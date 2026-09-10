"""PIL V4 four-arm treatment implementation with a common JSON contract."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import pil_v4_contract as contract
from pil_v4_client import COMMON_SYSTEM_INSTRUCTIONS, UnifiedV4Client

ROOT = Path(__file__).resolve().parent
ARMS_VERSION = "atlas.pil.four_arm_treatments.v4.1"
# Twelve entries keep the English deterministic lexical retriever
# recall-complete despite provision-level sibling entries, while still
# supplying only a bounded subset of the 58-entry knowledge base.  The value
# is frozen before any paid V4.1 generation.
TOP_K = 12

COMMON_PROMPT = """You are deciding jurisdiction under the supplied PIL task.

CASE FACTS:
{facts}

RETRIEVED LEGAL EVIDENCE:
{evidence}

AUTHORITATIVE OUTPUT CONTRACT (the identical complete JSON Schema is shown to
all four arms; only P2/P3 additionally enable provider-side enforcement):
{schema}

Return exactly one JSON object with these semantic fields:
conclusion, forum, forum_type, alternative_forum_types, conditional_answer,
explicit_abstention, legal_basis, reasoning, missing_facts.

Use only atomic forum_type labels. Put concurrent or alternative bases in
alternative_forum_types.

Allowed conclusion labels:
Court_of_X_has_jurisdiction, Authority_of_X_has_jurisdiction,
Stay_for_first_seised, May_stay_or_decline_for_related_actions,
Decline_in_favor_of_chosen_court,
No_EU_jurisdiction_use_member_state_law, Abstain_Insufficient_Info.

Allowed forum_type labels:
exclusive, agreement, special, general, lis_pendens, related_actions,
appearance, none.

legal_basis is an array of objects containing an instrument and provision,
for example {{"instrument":"BRUSSELS_I_BIS","provision":"Art.29(1)"}}.
The allowed instrument labels are BRUSSELS_I_BIS and
EU_TRADE_MARK_REGULATION. If the facts do not
support a reliable answer, use conclusion=Abstain_Insufficient_Info,
forum="none", forum_type="none", explicit_abstention=true, and name the
missing facts. Write every natural-language string value in English. Do not
wrap the JSON in Markdown fences."""

REPAIR_PROMPT = """The prior decision failed the frozen deterministic audit.

CASE FACTS:
{facts}

RETRIEVED LEGAL EVIDENCE:
{evidence}

AUTHORITATIVE OUTPUT CONTRACT:
{schema}

PRIOR DECISION:
{prior}

AUDIT FINDINGS:
{findings}

Return one corrected JSON object under the same schema. Use the same facts and
evidence only. Do not add an authority outside the retrieved evidence. This is
the only permitted repair attempt."""


def _norm(text: str) -> str:
    return " ".join(str(text).lower().split())


def _terms(provision: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for key in ("keywords",):
        values.extend(str(item) for item in provision.get(key) or [])
    values.extend([
        str(provision.get("instrument") or ""),
        str(provision.get("provision") or ""),
        str(provision.get("title") or ""),
    ])
    return [item for item in values if item]


def _affirmative_match(haystack: str, term: str) -> bool:
    """Ignore keywords that occur only inside an explicit exclusion clause."""
    needle = _norm(term)
    if not needle:
        return False
    start = 0
    while True:
        index = haystack.find(needle, start)
        if index < 0:
            return False
        clause_start = max(
            haystack.rfind(mark, 0, index)
            for mark in ("。", "；", ";", "！", "？", ".", "!", "?", "\n")
        ) + 1
        prefix = haystack[clause_start:index]
        tail = prefix[-160:]
        if not any(marker in tail for marker in (
            "不涉及", "不包括", "不存在", "排除",
            "does not involve", "does not include", "does not concern",
            "do not involve", "do not include", "do not concern",
            "there is no", "contains no", "without a", "no written",
            "no choice-of-court", "no jurisdiction",
        )):
            return True
        start = index + len(needle)


class FrozenRetriever:
    """Small deterministic retriever whose output is identical for P1/P2/P3."""

    def __init__(self, provisions: Iterable[dict[str, Any]], *, top_k: int = TOP_K) -> None:
        self.provisions = [dict(item) for item in provisions]
        self.top_k = top_k

    def retrieve(self, facts: str) -> list[dict[str, Any]]:
        haystack = _norm(facts)
        scored: list[tuple[int, str, dict[str, Any]]] = []
        for item in self.provisions:
            score = sum(1 for term in _terms(item) if _affirmative_match(haystack, term))
            scored.append((score, str(item.get("evidence_id") or ""), item))
        scored.sort(key=lambda row: (-row[0], row[1]))
        positive = [item for score, _, item in scored if score > 0]
        return positive[: self.top_k]


@dataclass(frozen=True)
class ArmContext:
    schema: dict[str, Any]
    rules: dict[str, Any]
    provisions: list[dict[str, Any]]
    retriever: FrozenRetriever

    @classmethod
    def load(cls, *, knowledge_base: Path) -> "ArmContext":
        provisions = [
            json.loads(line)
            for line in knowledge_base.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        return cls(
            schema=contract.load_schema(),
            rules=contract.load_rules(),
            provisions=provisions,
            retriever=FrozenRetriever(provisions),
        )


def _evidence_text(items: list[dict[str, Any]]) -> str:
    if not items:
        return "NONE SUPPLIED. This arm has no retrieved legal evidence."
    return "\n\n".join(
        f"[{item.get('evidence_id')}] {item.get('title', '')}\n{item.get('text_en') or item.get('text') or ''}"
        for item in items
    )


def render_primary_prompt(
    context: ArmContext, *, arm: str, facts: str,
) -> tuple[str, list[dict[str, Any]]]:
    if arm not in contract.ARMS:
        raise ValueError(f"unknown PIL V4 arm {arm!r}")
    grounded = arm in {"p1", "p2", "p3"}
    evidence_items = context.retriever.retrieve(facts) if grounded else []
    schema_text = json.dumps(
        context.schema, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    )
    prompt = COMMON_PROMPT.format(
        facts=facts, evidence=_evidence_text(evidence_items), schema=schema_text,
    )
    return prompt, evidence_items


def _usage(generation: Any) -> dict[str, int]:
    return {
        "input_tokens": int(generation.input_tokens),
        "output_tokens": int(generation.output_tokens),
        "total_tokens": int(generation.total_tokens),
    }


def _stage_attempts(attempts: Iterable[dict[str, Any]], stage: str) -> list[dict[str, Any]]:
    return [{**dict(item), "logical_request_stage": stage} for item in attempts]


def _redact_cjk_for_prompt(value: Any) -> Any:
    """Keep a repair request English even if a prior model output was not."""
    if isinstance(value, dict):
        return {str(key): _redact_cjk_for_prompt(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact_cjk_for_prompt(item) for item in value]
    if isinstance(value, str) and contract.contains_cjk(value):
        return "[NON-ENGLISH VALUE REDACTED]"
    return value


def _row_request_metadata(*, strict: bool, transport_attempts: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "provider_schema_enforced": strict,
        "system_instructions_sha256": hashlib.sha256(
            COMMON_SYSTEM_INSTRUCTIONS.encode("utf-8")
        ).hexdigest(),
        "primary_prompt_language": "en",
        "logical_request_count": 1,
        "transport_request_count": len(transport_attempts),
    }


def _model_failure(error: BaseException) -> dict[str, Any]:
    return {
        "stage": getattr(error, "stage", None),
        "error_type": type(error).__name__,
        "raw_text": getattr(error, "raw_text", None),
        "parsed": getattr(error, "parsed", None),
        "schema_errors": list(getattr(error, "schema_errors", ()) or ()),
        "usage": dict(getattr(error, "usage", {}) or {}),
        "provider_response": dict(getattr(error, "provider_response", {}) or {}),
        "transport_attempts": list(getattr(error, "transport_attempts", []) or []),
    }


def _is_model_result_failure(error: BaseException) -> bool:
    return getattr(error, "stage", None) in contract.MODEL_RESULT_STAGES


def run_unit(
    client: UnifiedV4Client,
    context: ArmContext,
    unit: dict[str, Any],
    case: dict[str, Any],
) -> dict[str, Any]:
    arm = str(unit["arm"])
    if arm not in contract.ARMS:
        raise ValueError(f"unknown PIL V4 arm {arm!r}")
    facts = str(case["facts_text"])
    strict = arm in {"p2", "p3"}
    prompt, evidence_items = render_primary_prompt(context, arm=arm, facts=facts)
    evidence_ids = [str(item.get("evidence_id")) for item in evidence_items]
    seed = contract.seed_for_replicate(int(unit["replicate"]))
    schema_text = json.dumps(
        context.schema, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    )
    prompt_sha256 = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    expected_prompt_sha256 = unit.get("prompt_sha256")
    if expected_prompt_sha256 and expected_prompt_sha256 != prompt_sha256:
        raise ValueError("rendered prompt differs from the frozen schedule")
    first: Any | None = None
    try:
        first = client.generate(
            prompt, schema=context.schema if strict else None, seed=seed,
        )
    except Exception as error:
        if not _is_model_result_failure(error):
            setattr(error, "failed_stage", "initial")
            setattr(error, "failed_prompt", prompt)
            setattr(error, "failed_prompt_sha256", prompt_sha256)
            setattr(error, "logical_requests_observed", 1)
            setattr(error, "completed_stages", [])
            raise
        failure = _model_failure(error)
        attempts = _stage_attempts(failure.get("transport_attempts") or [], "initial")
        final = contract.fail_closed_decision(["model_response_" + str(failure.get("stage") or "failed")]) if arm == "p3" else None
        return {
            "arm": arm,
            "arm_name": contract.ARM_NAMES[arm],
            "seed": seed,
            "facts_sha256": hashlib.sha256(facts.encode("utf-8")).hexdigest(),
            "prompt_sha256": prompt_sha256,
            "retrieved_evidence": evidence_ids,
            "raw_text": failure.get("raw_text"),
            "parsed_decision": failure.get("parsed"),
            "final_decision": final,
            "schema_status": "FAIL",
            "internal_audit": {"status": "FAIL", "findings": [failure]},
            "repair": {"attempted": False, "reason": "no_complete_parsed_decision"},
            "system_release": False,
            "model_result_failure": failure,
            "usage": failure.get("usage") or {},
            "external_call_count": 1,
            **_row_request_metadata(strict=strict, transport_attempts=attempts),
            "provider_responses": [failure.get("provider_response") or {}],
            "transport_attempts": attempts,
        }

    usage = _usage(first)
    parsed = first.parsed
    parse_error: str | None = None
    if not strict:
        parsed, parse_error = contract.strict_json_parse(first.raw_text)
    schema_issues = contract.schema_findings(parsed, context.schema) if parsed else []
    schema_status = "PASS" if parsed is not None and not schema_issues else "FAIL"

    if arm != "p3":
        attempts = _stage_attempts(first.transport_attempts, "initial")
        return {
            "arm": arm,
            "arm_name": contract.ARM_NAMES[arm],
            "seed": seed,
            "facts_sha256": hashlib.sha256(facts.encode("utf-8")).hexdigest(),
            "prompt_sha256": prompt_sha256,
            "retrieved_evidence": evidence_ids,
            "raw_text": first.raw_text,
            "parsed_decision": parsed,
            "final_decision": parsed,
            "parse_error": parse_error,
            "schema_status": schema_status,
            "schema_findings": schema_issues,
            "internal_audit": {"status": "NOT_APPLICABLE", "findings": []},
            "repair": {"attempted": False, "reason": "arm_has_no_l2_or_agr"},
            "system_release": schema_status == "PASS",
            "usage": usage,
            "external_call_count": 1,
            **_row_request_metadata(strict=strict, transport_attempts=attempts),
            "provider_responses": [first.provider_response],
            "transport_attempts": attempts,
        }

    assert parsed is not None
    initial_audit = contract.audit_decision(
        parsed, schema=context.schema, rules=context.rules, allowed_evidence=evidence_ids,
    )
    if initial_audit["status"] == "PASS":
        attempts = _stage_attempts(first.transport_attempts, "initial")
        return {
            "arm": arm,
            "arm_name": contract.ARM_NAMES[arm],
            "seed": seed,
            "facts_sha256": hashlib.sha256(facts.encode("utf-8")).hexdigest(),
            "prompt_sha256": prompt_sha256,
            "retrieved_evidence": evidence_ids,
            "raw_text": first.raw_text,
            "parsed_decision": parsed,
            "final_decision": parsed,
            "schema_status": "PASS",
            "internal_audit": initial_audit,
            "repair": {"attempted": False, "reason": "initial_audit_passed"},
            "system_release": True,
            "usage": usage,
            "external_call_count": 1,
            **_row_request_metadata(strict=True, transport_attempts=attempts),
            "provider_responses": [first.provider_response],
            "transport_attempts": attempts,
        }

    repair_prompt = REPAIR_PROMPT.format(
        facts=facts,
        evidence=_evidence_text(evidence_items),
        schema=schema_text,
        prior=json.dumps(_redact_cjk_for_prompt(parsed), ensure_ascii=False, sort_keys=True),
        findings=json.dumps(
            _redact_cjk_for_prompt(initial_audit["findings"]),
            ensure_ascii=False, sort_keys=True,
        ),
    )
    if contract.contains_cjk(repair_prompt):
        raise ValueError("repair prompt contains non-English CJK text")
    repair_prompt_sha256 = hashlib.sha256(repair_prompt.encode("utf-8")).hexdigest()
    try:
        repaired = client.generate(repair_prompt, schema=context.schema, seed=seed)
    except Exception as error:
        if not _is_model_result_failure(error):
            # One unit is atomic. An infrastructure failure after the first paid
            # call must be journalled by the runner and the unit stays pending.
            setattr(error, "failed_stage", "repair")
            setattr(error, "failed_prompt", repair_prompt)
            setattr(error, "failed_prompt_sha256", repair_prompt_sha256)
            setattr(error, "logical_requests_observed", 2)
            setattr(
                error, "transport_attempts",
                _stage_attempts(getattr(error, "transport_attempts", []) or [], "repair"),
            )
            setattr(error, "completed_stages", [{
                "stage": "initial_decision",
                "raw_text": first.raw_text,
                "parsed_decision": parsed,
                "usage": usage,
                "provider_response": first.provider_response,
                "transport_attempts": _stage_attempts(first.transport_attempts, "initial"),
            }])
            raise
        failure = _model_failure(error)
        attempts = [
            *_stage_attempts(first.transport_attempts, "initial"),
            *_stage_attempts(failure.get("transport_attempts") or [], "repair"),
        ]
        total_usage = dict(usage)
        for key, value in (failure.get("usage") or {}).items():
            total_usage[key] = total_usage.get(key, 0) + int(value or 0)
        closed = contract.fail_closed_decision(item["code"] for item in initial_audit["findings"])
        return {
            "arm": arm,
            "arm_name": contract.ARM_NAMES[arm],
            "seed": seed,
            "facts_sha256": hashlib.sha256(facts.encode("utf-8")).hexdigest(),
            "prompt_sha256": prompt_sha256,
            "retrieved_evidence": evidence_ids,
            "raw_text": first.raw_text,
            "parsed_decision": parsed,
            "final_decision": closed,
            "schema_status": "PASS",
            "internal_audit": initial_audit,
            "repair": {
                "attempted": True, "status": "FAIL",
                "prompt": repair_prompt, "prompt_sha256": repair_prompt_sha256,
                "prompt_language": "en", "prompt_cjk_characters": 0,
                "model_result_failure": failure,
            },
            "system_release": False,
            "usage": total_usage,
            "external_call_count": 2,
            **{
                **_row_request_metadata(strict=True, transport_attempts=attempts),
                "logical_request_count": 2,
            },
            "provider_responses": [
                first.provider_response,
                failure.get("provider_response") or {},
            ],
            "transport_attempts": attempts,
        }

    repair_audit = contract.audit_decision(
        repaired.parsed or {}, schema=context.schema, rules=context.rules, allowed_evidence=evidence_ids,
    )
    total_usage = {
        key: usage.get(key, 0) + _usage(repaired).get(key, 0)
        for key in {"input_tokens", "output_tokens", "total_tokens"}
    }
    passed = repair_audit["status"] == "PASS"
    final = repaired.parsed if passed else contract.fail_closed_decision(
        item["code"] for item in repair_audit["findings"]
    )
    attempts = [
        *_stage_attempts(first.transport_attempts, "initial"),
        *_stage_attempts(repaired.transport_attempts, "repair"),
    ]
    return {
        "arm": arm,
        "arm_name": contract.ARM_NAMES[arm],
        "seed": seed,
        "facts_sha256": hashlib.sha256(facts.encode("utf-8")).hexdigest(),
        "prompt_sha256": prompt_sha256,
        "retrieved_evidence": evidence_ids,
        "raw_text": first.raw_text,
        "parsed_decision": parsed,
        "final_decision": final,
        "schema_status": "PASS",
        "internal_audit": initial_audit,
        "repair": {
            "attempted": True,
            "status": "PASS" if passed else "FAIL",
            "prompt": repair_prompt,
            "prompt_sha256": repair_prompt_sha256,
            "prompt_language": "en",
            "prompt_cjk_characters": 0,
            "raw_text": repaired.raw_text,
            "decision": repaired.parsed,
            "audit": repair_audit,
        },
        "system_release": passed,
        "usage": total_usage,
        "external_call_count": 2,
        **{
            **_row_request_metadata(strict=True, transport_attempts=attempts),
            "logical_request_count": 2,
        },
        "provider_responses": [first.provider_response, repaired.provider_response],
        "transport_attempts": attempts,
    }


def make_run_unit(client: Any, context: ArmContext) -> Any:
    unified = client if isinstance(client, UnifiedV4Client) else UnifiedV4Client(client)
    return lambda unit, case: run_unit(unified, context, unit, case)
