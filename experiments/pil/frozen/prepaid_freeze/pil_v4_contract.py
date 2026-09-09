"""Common semantic contract and deterministic L2 audit for PIL V4.

The four arms share one output schema.  P0/P1 are asked for that JSON in the
prompt and are parsed only with ``json.loads``; P2/P3 use provider-enforced
strict schema decoding.  No keyword parser is part of the primary endpoint.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent
CONTRACT_VERSION = "atlas.pil.evaluation_contract.v4.1"
PAID_CONFIRMATION = "PIL_V41_720_LOCKED"
ARMS = ("p0", "p1", "p2", "p3")
ARM_NAMES = {
    "p0": "Prompt-only JSON",
    "p1": "RAG + prompt-only JSON",
    "p2": "RAG + strict schema (L1)",
    "p3": "RAG + strict schema + audit/one repair (L2/AGR)",
}
ABSTAIN = "Abstain_Insufficient_Info"
ATOMIC_FORUM_TYPES = {
    "exclusive", "agreement", "special", "general",
    "lis_pendens", "related_actions", "appearance", "none",
}
INSTRUMENTS = {"BRUSSELS_I_BIS", "EU_TRADE_MARK_REGULATION"}
MODEL_RESULT_STAGES = {
    "incomplete", "refusal", "empty_output", "json_decode", "posterior_schema",
}
PROVIDER_PROTOCOL = {
    "model_name": "gpt-5.6-luna",
    "expected_response_model": "gpt-5.6-luna-2026-07-09",
    "provider_family": "openai-compatible",
    "api_mode": "chat.completions",
    "reasoning_effort": "low",
    "temperature": 1.0,
    "tools_enabled": False,
    "max_completion_tokens": 128000,
    "sdk_implicit_retries": 0,
    "application_transport_max_attempts": 8,
    "transport_retry_delays_seconds": [1.0, 5.0, 15.0, 30.0, 60.0, 60.0, 60.0],
    "request_timeout_seconds": 180.0,
    "stream_responses": False,
    "transport_route_policy": "direct_no_environment_proxy",
    "seed_control": "provider_best_effort_fixed_replicate_seeds",
    "replicate_seeds": {"1": 104729, "2": 130363, "3": 155921},
}


def contains_cjk(value: Any) -> bool:
    """Return whether a model-visible/output value contains a CJK character."""
    if isinstance(value, Mapping):
        return any(contains_cjk(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(contains_cjk(item) for item in value)
    return isinstance(value, str) and any("\u3400" <= char <= "\u9fff" for char in value)


class InfrastructureError(RuntimeError):
    """A request failed before a model result was returned."""


class ModelResultError(RuntimeError):
    """A completed/refused/incomplete model response retained as an outcome."""

    def __init__(
        self,
        message: str,
        *,
        raw_text: str | None = None,
        parsed: Any = None,
        schema_errors: Iterable[str] = (),
        stage: str | None = None,
        response_status: str | None = None,
        usage: Mapping[str, int] | None = None,
    ) -> None:
        super().__init__(message)
        self.raw_text = raw_text
        self.parsed = parsed
        self.schema_errors = tuple(schema_errors)
        self.stage = stage
        self.response_status = response_status
        self.usage = dict(usage or {})


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def runtime_environment() -> dict[str, Any]:
    packages: dict[str, str] = {}
    for distribution in ("openai", "httpx", "jsonschema", "PyYAML"):
        try:
            packages[distribution] = importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError:
            packages[distribution] = "MISSING"
    return {
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform_system": platform.system(),
        "platform_machine": platform.machine(),
        "packages": packages,
        "byteorder": sys.byteorder,
    }


def seed_for_replicate(replicate: int) -> int:
    try:
        return int(PROVIDER_PROTOCOL["replicate_seeds"][str(int(replicate))])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"unsupported PIL V4 replicate {replicate!r}") from error


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_schema(path: Path | None = None) -> dict[str, Any]:
    path = path or ROOT / "schema" / "decision_schema_v4.json"
    schema = load_json(path)
    Draft202012Validator.check_schema(schema)
    return schema


def load_rules(path: Path | None = None) -> dict[str, Any]:
    return load_json(path or ROOT / "rules" / "delivery_rules_v4.json")


def strict_json_parse(raw_text: str) -> tuple[dict[str, Any] | None, str | None]:
    """Accept exactly one JSON object; never repair fences or prose."""
    try:
        parsed = json.loads(raw_text)
    except (TypeError, json.JSONDecodeError) as error:
        return None, f"json_decode:{type(error).__name__}"
    if not isinstance(parsed, dict):
        return None, "json_root_not_object"
    return parsed, None


def provision_set(decision: Mapping[str, Any]) -> set[str]:
    result: set[str] = set()
    for item in decision.get("legal_basis") or []:
        if isinstance(item, Mapping) and isinstance(item.get("provision"), str):
            result.add(str(item["provision"]).strip())
    return result


def evidence_set(decision: Mapping[str, Any]) -> set[str]:
    """Return instrument-qualified citation identities.

    Article numbers are not globally unique.  In particular, Article 63 of
    Brussels I bis concerns company domicile while Article 63 of the EU trade
    mark regulation concerns applications to EUIPO.
    """
    result: set[str] = set()
    for item in decision.get("legal_basis") or []:
        if not isinstance(item, Mapping):
            continue
        instrument = item.get("instrument")
        provision = item.get("provision")
        if isinstance(instrument, str) and isinstance(provision, str):
            result.add(f"{instrument.strip()}:{provision.strip()}")
    return result


def schema_findings(decision: Mapping[str, Any], schema: Mapping[str, Any]) -> list[dict[str, str]]:
    errors = sorted(
        Draft202012Validator(dict(schema)).iter_errors(dict(decision)),
        key=lambda item: list(item.absolute_path),
    )
    return [
        {
            "code": "schema_invalid",
            "stage": "schema",
            "message": error.message[:240],
        }
        for error in errors
    ]


def _has_prefix(basis: set[str], prefix: str) -> bool:
    return any(item == prefix or item.startswith(prefix + "(") for item in basis)


def audit_decision(
    decision: Mapping[str, Any],
    *,
    schema: Mapping[str, Any],
    rules: Mapping[str, Any],
    allowed_evidence: Iterable[str] | None,
    require_english_natural_language: bool = True,
) -> dict[str, Any]:
    """Deterministic structural/cross-field/evidence audit, not a legal oracle."""
    findings = schema_findings(decision, schema)
    if findings:
        return {"status": "FAIL", "findings": findings}

    conclusion = str(decision.get("conclusion"))
    forum = str(decision.get("forum") or "").strip()
    forum_type = str(decision.get("forum_type") or "")
    alternatives = list(decision.get("alternative_forum_types") or [])
    explicit_abstention = bool(decision.get("explicit_abstention"))
    conditional_answer = bool(decision.get("conditional_answer"))
    missing_facts = list(decision.get("missing_facts") or [])
    basis = evidence_set(decision)

    def add(code: str, message: str, stage: str = "cross_field") -> None:
        findings.append({"code": code, "stage": stage, "message": message})

    natural_language_surface = {
        "forum": decision.get("forum"),
        "reasoning": decision.get("reasoning"),
        "missing_facts": decision.get("missing_facts"),
    }
    if require_english_natural_language and contains_cjk(natural_language_surface):
        add(
            "non_english_natural_language",
            "Natural-language output fields must be written in English.",
            "language",
        )

    if forum_type not in ATOMIC_FORUM_TYPES:
        add("forum_type_not_atomic", "forum_type must be one declared atomic label.")
    if forum_type in alternatives:
        add("primary_repeated_as_alternative", "forum_type is duplicated in alternative_forum_types.")

    abstained = conclusion == ABSTAIN
    national_law = conclusion == "No_EU_jurisdiction_use_member_state_law"
    if explicit_abstention != abstained:
        add("abstention_flag_mismatch", "explicit_abstention must agree with conclusion.")
    if conditional_answer != bool(missing_facts):
        add(
            "conditional_missing_facts_mismatch",
            "conditional_answer must be true exactly when missing_facts is non-empty.",
        )
    if abstained and not conditional_answer:
        add("abstention_not_conditional", "An abstention must set conditional_answer=true.")
    if abstained:
        if forum.lower() != "none" or forum_type != "none":
            add("abstention_forum_mismatch", "An abstention must use forum='none' and forum_type='none'.")
        if not missing_facts:
            add("abstention_without_missing_fact", "An abstention must name at least one missing fact.")
    elif national_law:
        if not forum or forum.lower() == "none" or forum_type != "none":
            add(
                "national_law_forum_mismatch",
                "A national-law referral requires a named Member State forum and forum_type=none.",
            )
        if not basis:
            add("decision_without_basis", "A national-law referral requires at least one legal provision.")
    else:
        if not forum or forum.lower() == "none" or forum_type == "none":
            add("decision_without_forum", "A non-abstaining decision requires a forum and atomic forum type.")
        if not basis:
            add("decision_without_basis", "A non-abstaining decision requires at least one legal provision.")

    cross = rules.get("cross_field_rules") or {}
    if conclusion == "Stay_for_first_seised" and forum_type != cross.get("stay_forum_type"):
        add("stay_type_mismatch", "Stay_for_first_seised requires forum_type=lis_pendens.")
    if (
        conclusion == "May_stay_or_decline_for_related_actions"
        and forum_type != cross.get("related_actions_forum_type")
    ):
        add(
            "related_actions_type_mismatch",
            "May_stay_or_decline_for_related_actions requires forum_type=related_actions.",
        )
    if conclusion == "Decline_in_favor_of_chosen_court" and forum_type != cross.get("chosen_court_forum_type"):
        add("chosen_court_type_mismatch", "Chosen-court decline requires forum_type=agreement.")
    if conclusion == "Authority_of_X_has_jurisdiction":
        if forum_type != cross.get("authority_forum_type"):
            add("authority_type_mismatch", "Authority jurisdiction requires the declared authority forum type.")
        required_instrument = cross.get("authority_required_instrument")
        if required_instrument and not any(item.startswith(f"{required_instrument}:") for item in basis):
            add(
                "authority_instrument_mismatch",
                "Authority jurisdiction requires a citation to the declared authority instrument.",
                "precedence",
            )
    if national_law:
        national_law_prefix = cross.get("national_law_required_basis_prefix")
        if national_law_prefix and not _has_prefix(basis, national_law_prefix):
            add(
                "national_law_basis_mismatch",
                "A national-law referral requires the declared Article 6 evidence.",
                "precedence",
            )

    required = (rules.get("forum_type_required_basis_prefixes") or {}).get(forum_type, [])
    if not abstained and required and not any(_has_prefix(basis, prefix) for prefix in required):
        add(
            "forum_type_basis_mismatch",
            f"forum_type={forum_type} requires one of the declared basis prefixes: {required}.",
            "precedence",
        )
    if allowed_evidence is not None:
        allowed = set(allowed_evidence)
        outside = sorted(basis - allowed)
        if outside:
            add(
                "citation_outside_retrieved_evidence",
                "Cited provisions were not in the frozen retrieved evidence: " + ", ".join(outside),
                "evidence_scope",
            )

    return {"status": "PASS" if not findings else "FAIL", "findings": findings}


def fail_closed_decision(reason_codes: Iterable[str]) -> dict[str, Any]:
    reasons = list(dict.fromkeys(str(item) for item in reason_codes if item)) or ["l2_audit_failed"]
    return {
        "conclusion": ABSTAIN,
        "forum": "none",
        "forum_type": "none",
        "alternative_forum_types": [],
        "conditional_answer": True,
        "explicit_abstention": True,
        "legal_basis": [],
        "reasoning": "The result was withheld because the frozen validation contract failed.",
        "missing_facts": ["fail_closed:" + code for code in reasons],
    }


@dataclass(frozen=True)
class GoldCompatibility:
    conclusion: bool
    forum_type: bool
    evidence: bool
    conditional_answer: bool

    @property
    def correct(self) -> bool:
        return (
            self.conclusion and self.forum_type
            and self.evidence and self.conditional_answer
        )


def score_against_gold(decision: Mapping[str, Any] | None, gold: Mapping[str, Any]) -> GoldCompatibility:
    """Score atomic primary fields against a consensus acceptance-set gold."""
    if not decision:
        return GoldCompatibility(False, False, False, False)
    accepted_conclusions = set(gold.get("accepted_conclusions") or [gold.get("conclusion")])
    accepted_types = set(gold.get("accepted_forum_types") or [gold.get("forum_type")])
    required_evidence = set(gold.get("required_evidence") or [])
    conclusion_ok = decision.get("conclusion") in accepted_conclusions
    type_ok = decision.get("forum_type") in accepted_types
    basis = evidence_set(decision)
    evidence_ok = not required_evidence or bool(basis & required_evidence)
    conditional_ok = decision.get("conditional_answer") is gold.get("conditional_answer")
    return GoldCompatibility(conclusion_ok, type_ok, evidence_ok, conditional_ok)


def contract_declaration() -> dict[str, Any]:
    schema_path = ROOT / "schema" / "decision_schema_v4.json"
    rules_path = ROOT / "rules" / "delivery_rules_v4.json"
    return {
        "version": CONTRACT_VERSION,
        "arms": list(ARMS),
        "arm_names": dict(ARM_NAMES),
        "schema_sha256": sha256_file(schema_path),
        "delivery_rules_sha256": sha256_file(rules_path),
        "soft_json_parser": "json.loads_exact_object_no_repair",
        "output_contract_prompt_visibility": "identical_complete_schema_all_arms",
        "p2_minus_p1_treatment_difference": "provider_strict_schema_enforcement_only",
        "model_visible_language": "English",
        "p0_knowledge_policy": "model_prior_legal_knowledge_allowed_when_no_evidence_is_supplied",
        "grounded_arms_evidence_policy": "citations_restricted_to_frozen_retrieved_evidence",
        "p3_maximum_repair_attempts": 1,
        "citation_identity": "instrument:provision",
        "primary_gold_fields": [
            "conclusion", "forum_type", "required_evidence", "conditional_answer",
        ],
        "provider_protocol": dict(PROVIDER_PROTOCOL),
        "paid_confirmation_token_sha256": canonical_sha256(PAID_CONFIRMATION),
    }


def contract_sha256() -> str:
    return canonical_sha256(contract_declaration())
