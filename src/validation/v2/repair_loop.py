"""Controlled bundle-wide LLM repair and deterministic revalidation loop."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any, Callable

from lxml import etree

RepairCallback = Callable[[dict[str, Any], dict[str, Any], str, int], Any]


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


def validate_candidate_shape(original: dict[str, Any], candidate: dict[str, Any]) -> None:
    original_documents = _documents(original)
    candidate_documents = _documents(candidate)
    if set(candidate_documents) != set(original_documents):
        missing = sorted(set(original_documents) - set(candidate_documents))
        extra = sorted(set(candidate_documents) - set(original_documents))
        raise ValueError(f"repair changed document identity; missing={missing}, extra={extra}")
    parser = etree.XMLParser(resolve_entities=False, no_network=True, recover=False, huge_tree=True)
    for (kind, name), xml_text in candidate_documents.items():
        try:
            etree.fromstring(xml_text.encode("utf-8"), parser)
        except etree.XMLSyntaxError as error:
            raise ValueError(f"repair produced malformed XML for {kind}/{name}: {error}") from error


class BundleRepairLoop:
    """Keep the best validated bundle; never accept an equal or worse proposal."""

    def __init__(self, validation_service: Any, repair_callback: RepairCallback, max_rounds: int = 2) -> None:
        if max_rounds < 0:
            raise ValueError("max_rounds must not be negative")
        self.validation_service = validation_service
        self.repair_callback = repair_callback
        self.max_rounds = max_rounds

    def run(
        self,
        bundle: dict[str, Any],
        report: dict[str, Any],
        *,
        validation_context: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
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
                candidate = callback_result
                if isinstance(callback_result, tuple) and len(callback_result) == 2:
                    candidate, usage = callback_result
                for key in token_usage:
                    token_usage[key] += int((usage or {}).get(key) or 0)
                if not isinstance(candidate, dict):
                    raise ValueError("repair callback did not return an ARXML bundle")
                validate_candidate_shape(best_bundle, candidate)
                fingerprint = bundle_fingerprint(candidate)
                if fingerprint in seen:
                    stop_reason = "repeated_candidate"
                    history.append({"round": round_number, "accepted": False, "reason": stop_reason})
                    break
                seen.add(fingerprint)
                candidate_report = self.validation_service.validate_bundle(
                    candidate, validation_context=validation_context
                )
                candidate_score = validation_score(candidate_report)
                accepted = candidate_score < best_score
                history.append({
                    "round": round_number,
                    "accepted": accepted,
                    "before_decision": best_report.get("decision"),
                    "after_decision": candidate_report.get("decision"),
                    "before_score": list(best_score),
                    "after_score": list(candidate_score),
                    "candidate_sha256": fingerprint,
                    "finding_count": (candidate_report.get("summary") or {}).get("finding_count", 0),
                })
                if not accepted:
                    stop_reason = "no_strict_improvement"
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
            "schema_version": "1.0",
            "enabled": True,
            "attempted_rounds": len(history),
            "accepted_rounds": sum(bool(item.get("accepted")) for item in history),
            "stop_reason": stop_reason,
            "final_bundle_sha256": bundle_fingerprint(best_bundle),
            "final_validation_score": list(best_score),
            "token_usage": token_usage,
            "history": history,
        }
        return best_bundle, best_report, audit
