"""Controlled bundle-wide LLM repair and deterministic revalidation loop.

Acceptance is fail-closed.  A candidate replaces the current best only when it
is provably better under the same hash-pinned validation context, checked in
this order:

1. it must not introduce any new finding fingerprint, because a net reduction in
   the finding count can still hide a regression;
2. no ``must`` rule may silently leave the evaluated set.  A rule that stops
   being evaluated is only permitted when the proposer supplies an auditable
   waiver: the rule belonged to a finding that the proposer deleted the reported
   element for, and that finding is in fact gone from the candidate report.
   Without such a waiver, losing coverage is treated as hiding evidence;
3. either at least one previously reported finding must disappear, or the
   candidate must complete missing evidence -- strictly fewer unevaluable
   ``must`` rules, with every newly evaluable rule passing.  A round that
   neither clears a violation nor makes a rule decidable is refused;
4. it must strictly improve the aggregate validation score;
5. it must preserve document identity, including the root element and the
   package-scoped entity set of every document.

The aggregate number of unevaluable rules is deliberately not a monotonic
guard.  Restoring a missing structure can make additional rule instances
applicable, so that total may rise even though no previously evaluated rule was
lost.  The per-rule coverage test above is the safe invariant.

Rules 3 and 4 exist because the two obvious ways to fake progress are opposites
of each other: deleting the content a rule reads, and adding content that lowers
the unevaluable count without fixing anything.  Neither is allowed, and neither
blocks the legitimate version of itself.

No step has a fallback, a tolerance window, or a "trust the proposer" bypass.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Callable

from lxml import etree

RepairCallback = Callable[[dict[str, Any], dict[str, Any], str, int], Any]
ReportEnricher = Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]


@dataclass(frozen=True)
class CoverageLossWaiver:
    """Auditable reason a ``must`` rule may leave the evaluated rule set.

    Removing the element a rule reports on is the correct repair for a
    forbidden-existence or mutual-exclusion violation, and it necessarily makes
    that rule ``NOT_APPLICABLE``.  The waiver names the finding whose enumerated
    ``remove_element`` candidate was applied; it is honoured only if that finding
    actually disappeared, so it cannot be used to excuse deleting evidence.
    """

    finding_fingerprint: str
    rule_ids: tuple[str, ...]
    removed_location: str

    def record(self) -> dict[str, Any]:
        return {
            "finding_fingerprint": self.finding_fingerprint,
            "rule_ids": list(self.rule_ids),
            "removed_location": self.removed_location,
        }


@dataclass(frozen=True)
class RepairProposal:
    """What a repair callback returns: a candidate plus its own audit trail."""

    bundle: dict[str, Any]
    token_usage: dict[str, int] = field(default_factory=dict)
    coverage_waivers: tuple[CoverageLossWaiver, ...] = ()
    identity_restorations: tuple["IdentityRestoration", ...] = ()


@dataclass(frozen=True)
class IdentityRestoration:
    """Exact document identity that a typed repair is allowed to restore.

    This is intentionally narrower than a general identity waiver: the input
    entity must have an empty SHORT-NAME, and the candidate may only replace it
    with the hash-bound target name for the same package and element tag.
    """

    kind: str
    document_name: str
    package_short_name: str
    element_tag: str
    short_name: str

    def record(self) -> dict[str, str]:
        return {
            "kind": self.kind,
            "document_name": self.document_name,
            "package_short_name": self.package_short_name,
            "element_tag": self.element_tag,
            "short_name": self.short_name,
        }


@dataclass(frozen=True)
class AcceptanceDecision:
    """Outcome of comparing one candidate against the current best."""

    accepted: bool
    reason: str
    details: tuple[str, ...] = ()
    basis: str = ""
    waiver_dispositions: tuple[dict[str, Any], ...] = ()


def bundle_fingerprint(bundle: dict[str, Any]) -> str:
    payload = json.dumps(bundle, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validation_score(report: dict[str, Any]) -> tuple[int, int, int, int, int]:
    summary = report.get("summary") or {}
    rank = {"PASS": 0, "INCOMPLETE": 1, "FAIL": 2, "ERROR": 3}.get(
        str(report.get("decision")), 4
    )
    return (
        rank,
        int(summary.get("ERROR") or 0),
        int(summary.get("FAIL") or 0),
        int(summary.get("finding_count") or 0),
        int(summary.get("must_not_evaluated") or 0),
    )


def must_not_evaluated_count(report: dict[str, Any]) -> int:
    """Number of ``must`` rules that remain undecidable for this artifact."""
    summary = report.get("summary")
    if not isinstance(summary, dict):
        raise ValueError("validation report summary must be an object")
    value = summary.get("must_not_evaluated")
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("validation report summary.must_not_evaluated must be an integer")
    if value < 0:
        raise ValueError("validation report summary.must_not_evaluated must not be negative")
    return value


def finding_fingerprints(report: dict[str, Any]) -> frozenset[str]:
    """Collect the finding fingerprints a report claims to have observed.

    A report without a well-formed ``findings`` array cannot be used to prove
    the absence of a regression, so it is rejected rather than treated as clean.
    """
    findings = report.get("findings")
    if not isinstance(findings, list):
        raise ValueError("validation report findings must be an array")
    result: set[str] = set()
    for position, item in enumerate(findings):
        if not isinstance(item, dict):
            raise ValueError(f"validation report findings[{position}] must be an object")
        fingerprint = item.get("fingerprint")
        if not isinstance(fingerprint, str) or not fingerprint:
            raise ValueError(
                f"validation report findings[{position}] has no usable fingerprint"
            )
        result.add(fingerprint)
    summary = report.get("summary") or {}
    reported_count = summary.get("finding_count")
    if (
        isinstance(reported_count, bool)
        or not isinstance(reported_count, int)
        or reported_count != len(findings)
    ):
        raise ValueError(
            "validation report summary.finding_count differs from the findings array"
        )
    return frozenset(result)


def must_rule_statuses(report: dict[str, Any]) -> dict[str, str]:
    """Status of every ``must`` rule, keyed by rule id."""
    rules = report.get("rules")
    if not isinstance(rules, list):
        raise ValueError("validation report rules must be an array")
    result: dict[str, str] = {}
    for position, item in enumerate(rules):
        if not isinstance(item, dict):
            raise ValueError(f"validation report rules[{position}] must be an object")
        if str(item.get("policy") or "") != "must":
            continue
        rule_id = item.get("rule_id")
        if not isinstance(rule_id, str) or not rule_id:
            raise ValueError(
                f"validation report rules[{position}] has no usable rule_id"
            )
        result[rule_id] = str(item.get("status") or "")
    return result


def evaluated_must_rule_ids(report: dict[str, Any]) -> frozenset[str]:
    """Must-rule coverage that a repair may not make disappear unaccounted for."""
    return frozenset(
        rule_id
        for rule_id, status in must_rule_statuses(report).items()
        if status in {"PASS", "FAIL"}
    )


def _waiver_dispositions(
    coverage_waivers: Any,
    candidate_fingerprints: frozenset[str],
    best_must: dict[str, str],
    candidate_must: dict[str, str],
) -> tuple[frozenset[str], list[dict[str, Any]]]:
    """Decide which waived rules may lose coverage, and record why.

    Three independent facts must hold, and the proposer supplies none of them:
    the finding it named is genuinely gone; the rule was actually ``FAIL``
    before; and the rule is explicitly ``NOT_APPLICABLE`` now.  The last one
    matters because a rule can also leave the evaluated set by becoming
    undecidable, which is evidence destruction wearing the same disguise.
    """
    if not isinstance(coverage_waivers, (list, tuple)):
        raise ValueError("repair coverage waivers must be a sequence")
    honoured: set[str] = set()
    dispositions: list[dict[str, Any]] = []
    for position, waiver in enumerate(coverage_waivers):
        if not isinstance(waiver, CoverageLossWaiver):
            raise ValueError(f"repair coverage waiver {position} has the wrong type")
        if not waiver.finding_fingerprint:
            raise ValueError(f"repair coverage waiver {position} names no finding")
        record = waiver.record()
        if waiver.finding_fingerprint in candidate_fingerprints:
            record["disposition"] = "void_finding_still_reported"
            dispositions.append(record)
            continue
        accepted: list[str] = []
        refused: list[dict[str, str]] = []
        for rule_id in waiver.rule_ids:
            rule_id = str(rule_id)
            before = best_must.get(rule_id, "")
            after = candidate_must.get(rule_id, "")
            if before != "FAIL":
                refused.append({"rule_id": rule_id, "reason": f"was_{before or 'absent'}"})
                continue
            if after != "NOT_APPLICABLE":
                refused.append({"rule_id": rule_id, "reason": f"became_{after or 'absent'}"})
                continue
            accepted.append(rule_id)
        record["accepted_rule_ids"] = accepted
        record["refused_rule_ids"] = refused
        record["disposition"] = "honoured" if accepted and not refused else (
            "partially_honoured" if accepted else "void_rule_transition"
        )
        honoured.update(accepted)
        dispositions.append(record)
    return frozenset(honoured), dispositions


def _documents(bundle: dict[str, Any]) -> dict[tuple[str, str], str]:
    result: dict[tuple[str, str], str] = {}
    for kind in ("components", "interfaces"):
        values = bundle.get(kind)
        if not isinstance(values, dict):
            raise ValueError(f"bundle.{kind} must be an object")
        for name, xml_text in values.items():
            if not isinstance(xml_text, str) or not xml_text.strip():
                raise ValueError(f"bundle document {kind}/{name} is empty or not text")
            result[(kind, str(name))] = xml_text
    return result


def _local_name(tag: object) -> str:
    text = str(tag or "")
    return text.rsplit("}", 1)[-1]


def _direct_children(node: etree._Element, name: str) -> list[etree._Element]:
    return [child for child in node if _local_name(child.tag) == name]


def _direct_short_name(node: etree._Element) -> str:
    names = _direct_children(node, "SHORT-NAME")
    if not names:
        return ""
    return (names[0].text or "").strip()


def _parse_document(kind: str, name: str, xml_text: str) -> etree._Element:
    parser = etree.XMLParser(
        resolve_entities=False, no_network=True, recover=False, huge_tree=True
    )
    try:
        return etree.fromstring(xml_text.encode("utf-8"), parser)
    except etree.XMLSyntaxError as error:
        raise ValueError(f"repair produced malformed XML for {kind}/{name}: {error}") from error


def document_identity(root: etree._Element) -> tuple[str, tuple[tuple[str, str, str], ...]]:
    """Identity a repair must preserve: root element and declared entities.

    The entity set is the ``(package short-name, element tag, element
    short-name)`` triple of every element directly under an ``ELEMENTS``
    container.  Nested short-names are deliberately excluded so that a
    legitimate repair may still add or remove inner structure, which remains
    governed by the selection obligations and the constraint rules.
    """
    entities: list[tuple[str, str, str]] = []
    for package in root.iter():
        if _local_name(package.tag) != "AR-PACKAGE":
            continue
        package_name = _direct_short_name(package)
        for container in _direct_children(package, "ELEMENTS"):
            for element in container:
                if not isinstance(element.tag, str):
                    continue
                entities.append(
                    (package_name, _local_name(element.tag), _direct_short_name(element))
                )
    return _local_name(root.tag), tuple(sorted(entities))


def validate_candidate_shape(
    original: dict[str, Any],
    candidate: dict[str, Any],
    *,
    identity_restorations: tuple[IdentityRestoration, ...] = (),
) -> None:
    original_documents = _documents(original)
    candidate_documents = _documents(candidate)
    if set(candidate_documents) != set(original_documents):
        missing = sorted(set(original_documents) - set(candidate_documents))
        extra = sorted(set(candidate_documents) - set(original_documents))
        raise ValueError(f"repair changed document identity; missing={missing}, extra={extra}")
    allowed: dict[tuple[str, str], IdentityRestoration] = {}
    for restoration in identity_restorations:
        key = (restoration.kind, restoration.document_name)
        if key in allowed:
            raise ValueError(f"duplicate document identity restoration for {key}")
        if restoration.short_name != restoration.document_name:
            raise ValueError(
                "document identity restoration must equal the hash-bound document name"
            )
        allowed[key] = restoration

    for (kind, name), candidate_xml in candidate_documents.items():
        candidate_root = _parse_document(kind, name, candidate_xml)
        original_root = _parse_document(kind, name, original_documents[(kind, name)])
        candidate_identity = document_identity(candidate_root)
        original_identity = document_identity(original_root)
        if candidate_identity == original_identity:
            continue
        restoration = allowed.get((kind, name))
        if restoration is not None:
            original_root_tag, original_entities = original_identity
            candidate_root_tag, candidate_entities = candidate_identity
            missing_identity = (
                restoration.package_short_name,
                restoration.element_tag,
                "",
            )
            restored_identity = (
                restoration.package_short_name,
                restoration.element_tag,
                restoration.short_name,
            )
            expected_entities = list(original_entities)
            if missing_identity in expected_entities:
                expected_entities.remove(missing_identity)
                expected_entities.append(restored_identity)
                if (
                    original_root_tag == candidate_root_tag
                    and tuple(sorted(expected_entities)) == candidate_entities
                ):
                    continue
        if candidate_identity != original_identity:
            raise ValueError(
                f"repair changed declared identity of {kind}/{name}: "
                f"expected {original_identity}, got {candidate_identity}"
            )


def acceptance_decision(
    best_report: dict[str, Any],
    candidate_report: dict[str, Any],
    *,
    coverage_waivers: Any = (),
) -> AcceptanceDecision:
    """Decide whether a revalidated candidate may replace the current best."""
    best_unevaluable = must_not_evaluated_count(best_report)
    candidate_unevaluable = must_not_evaluated_count(candidate_report)

    best_fingerprints = finding_fingerprints(best_report)
    candidate_fingerprints = finding_fingerprints(candidate_report)
    introduced = tuple(sorted(candidate_fingerprints - best_fingerprints))
    if introduced:
        return AcceptanceDecision(False, "regression", introduced)

    best_must = must_rule_statuses(best_report)
    candidate_must = must_rule_statuses(candidate_report)
    evaluated = {"PASS", "FAIL"}
    best_evaluated = {
        rule_id for rule_id, status in best_must.items() if status in evaluated
    }
    candidate_evaluated = {
        rule_id for rule_id, status in candidate_must.items() if status in evaluated
    }
    honoured, dispositions = _waiver_dispositions(
        coverage_waivers, candidate_fingerprints, best_must, candidate_must
    )
    unaccounted = tuple(sorted((best_evaluated - candidate_evaluated) - honoured))
    if unaccounted:
        return AcceptanceDecision(
            False, "lost_evaluated_must_rule_coverage", unaccounted,
            waiver_dispositions=tuple(dispositions),
        )

    resolved = tuple(sorted(best_fingerprints - candidate_fingerprints))
    basis = "finding_resolved"
    if not resolved and best_fingerprints:
        # Nothing reported was cleared.  The only other real progress is making
        # previously undecidable ``must`` rules decidable and passing, which is
        # the legitimate mirror image of the deletion trick rule 3 blocks.
        if candidate_unevaluable >= best_unevaluable:
            return AcceptanceDecision(
                False, "no_finding_resolved",
                waiver_dispositions=tuple(dispositions),
            )
        newly_evaluable = tuple(sorted(candidate_evaluated - best_evaluated))
        not_passing = tuple(
            rule_id
            for rule_id in newly_evaluable
            if candidate_must.get(rule_id) != "PASS"
        )
        if not newly_evaluable or not_passing:
            return AcceptanceDecision(
                False, "no_finding_resolved", not_passing,
                waiver_dispositions=tuple(dispositions),
            )
        basis = "evidence_completion"

    if validation_score(candidate_report) >= validation_score(best_report):
        return AcceptanceDecision(
            False, "no_strict_improvement", waiver_dispositions=tuple(dispositions)
        )
    return AcceptanceDecision(
        True, "", resolved, basis, waiver_dispositions=tuple(dispositions)
    )


class BundleRepairLoop:
    """Keep the best validated bundle; never accept an equal or worse proposal."""

    def __init__(
        self,
        validation_service: Any,
        repair_callback: RepairCallback,
        max_rounds: int = 2,
        report_enricher: ReportEnricher | None = None,
    ) -> None:
        if max_rounds < 0:
            raise ValueError("max_rounds must not be negative")
        self.validation_service = validation_service
        self.repair_callback = repair_callback
        self.max_rounds = max_rounds
        self.report_enricher = report_enricher

    def run(
        self,
        bundle: dict[str, Any],
        report: dict[str, Any],
        *,
        validation_context: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        # Fail fast when the caller supplies a report that cannot support a
        # regression comparison; this is a contract error, not a repair failure.
        must_not_evaluated_count(report)
        finding_fingerprints(report)
        evaluated_must_rule_ids(report)

        best_bundle = deepcopy(bundle)
        best_report = report
        best_score = validation_score(report)
        seen = {bundle_fingerprint(best_bundle)}
        history: list[dict[str, Any]] = []
        token_usage = {"input": 0, "output": 0, "total": 0}
        stop_reason = "not_required"

        for round_number in range(1, self.max_rounds + 1):
            actions = int((best_report.get("repair") or {}).get("action_count") or 0)
            if best_report.get("decision") not in {"FAIL", "ERROR"} or actions == 0:
                stop_reason = "no_repairable_findings"
                break
            prompt = str((best_report.get("repair") or {}).get("llm_prompt") or "").strip()
            try:
                callback_result = self.repair_callback(
                    deepcopy(best_bundle), deepcopy(best_report), prompt, round_number
                )
                usage: dict[str, Any] = {}
                waivers: tuple[CoverageLossWaiver, ...] = ()
                identity_restorations: tuple[IdentityRestoration, ...] = ()
                candidate = callback_result
                if isinstance(callback_result, RepairProposal):
                    candidate = callback_result.bundle
                    usage = callback_result.token_usage
                    waivers = tuple(callback_result.coverage_waivers)
                    identity_restorations = tuple(
                        callback_result.identity_restorations
                    )
                elif isinstance(callback_result, tuple) and len(callback_result) == 2:
                    candidate, usage = callback_result
                for key in token_usage:
                    token_usage[key] += int((usage or {}).get(key) or 0)
                if not isinstance(candidate, dict):
                    raise ValueError("repair callback did not return an ARXML bundle")
                validate_candidate_shape(
                    best_bundle,
                    candidate,
                    identity_restorations=identity_restorations,
                )
                fingerprint = bundle_fingerprint(candidate)
                if fingerprint in seen:
                    stop_reason = "repeated_candidate"
                    history.append({"round": round_number, "accepted": False, "reason": stop_reason})
                    break
                seen.add(fingerprint)
                candidate_report = self.validation_service.validate_bundle(
                    candidate, validation_context=validation_context
                )
                if self.report_enricher is not None:
                    candidate_report = self.report_enricher(
                        candidate, candidate_report
                    )
                candidate_score = validation_score(candidate_report)
                decision = acceptance_decision(
                    best_report, candidate_report, coverage_waivers=waivers
                )
                entry: dict[str, Any] = {
                    "round": round_number,
                    "accepted": decision.accepted,
                    "before_decision": best_report.get("decision"),
                    "after_decision": candidate_report.get("decision"),
                    "before_score": list(best_score),
                    "after_score": list(candidate_score),
                    "before_must_not_evaluated": must_not_evaluated_count(best_report),
                    "after_must_not_evaluated": must_not_evaluated_count(candidate_report),
                    "candidate_sha256": fingerprint,
                    "finding_count": (candidate_report.get("summary") or {}).get("finding_count", 0),
                    "introduced_finding_fingerprints": list(
                        decision.details if decision.reason == "regression" else ()
                    ),
                    "acceptance_basis": decision.basis,
                    "resolved_finding_fingerprints": list(
                        decision.details if decision.accepted else ()
                    ),
                    "coverage_loss_waivers": [
                        item
                        for item in decision.waiver_dispositions
                        if item.get("disposition") in {"honoured", "partially_honoured"}
                    ],
                    "void_coverage_loss_waivers": [
                        item
                        for item in decision.waiver_dispositions
                        if item.get("disposition")
                        not in {"honoured", "partially_honoured"}
                    ],
                    "identity_restorations": [
                        restoration.record()
                        for restoration in identity_restorations
                    ],
                }
                if not decision.accepted:
                    entry["reason"] = decision.reason
                    entry["reason_details"] = list(decision.details)
                history.append(entry)
                if not decision.accepted:
                    stop_reason = decision.reason
                    break
                best_bundle = deepcopy(candidate)
                best_report = candidate_report
                best_score = candidate_score
                stop_reason = "max_rounds_reached"
            except Exception as error:
                stop_reason = "repair_error"
                history.append({
                    "round": round_number,
                    "accepted": False,
                    "reason": stop_reason,
                    "error": f"{type(error).__name__}: {error}",
                })
                break

        audit = {
            "schema_version": "1.2",
            "enabled": True,
            "attempted_rounds": len(history),
            "accepted_rounds": sum(bool(item.get("accepted")) for item in history),
            "accepted_bases": sorted(
                {
                    str(item.get("acceptance_basis") or "")
                    for item in history
                    if item.get("accepted")
                }
            ),
            "waived_coverage_loss_count": sum(
                len(item.get("coverage_loss_waivers") or []) for item in history
            ),
            "stop_reason": stop_reason,
            "final_bundle_sha256": bundle_fingerprint(best_bundle),
            "final_validation_score": list(best_score),
            "final_must_not_evaluated": must_not_evaluated_count(best_report),
            "token_usage": token_usage,
            "history": history,
        }
        return best_bundle, best_report, audit
