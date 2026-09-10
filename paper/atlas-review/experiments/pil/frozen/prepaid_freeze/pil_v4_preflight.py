"""Validate and freeze every PIL V4 input before paid execution is authorized.

This command performs no provider call.  A successful run creates a
``READY_FOR_PAID_AUTHORIZATION`` manifest; it does not enable the 720-unit
formal runner.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

import pil_v4_arms
import pil_v4_contract as contract
import pil_v4_schedule
import pil_v41_render_prompts


ROOT = Path(__file__).resolve().parent
INPUTS = {
    "inference_dataset": ROOT / "data" / "inference_dataset_v41_en.jsonl",
    "consensus_gold": ROOT / "data" / "consensus_gold_v4.jsonl",
    "knowledge_base": ROOT / "kb" / "authoritative_provisions_v41_en.jsonl",
    "decision_schema": ROOT / "schema" / "decision_schema_v4.json",
    "gold_schema": ROOT / "schema" / "consensus_gold_schema_v4.json",
    "delivery_rules": ROOT / "rules" / "delivery_rules_v4.json",
    "autosar_v20_parameter_match": ROOT / "PIL_V41_AUTOSAR_V20_PARAMETER_MATCH.json",
    "english_input_manifest": ROOT / "PIL_V41_ENGLISH_INPUT_MANIFEST.json",
    "english_legal_source_audit": ROOT / "PIL_V41_ENGLISH_LEGAL_SOURCE_AUDIT.json",
    "translation_parity_acceptance": ROOT / "PIL_V41_TRANSLATION_PARITY_ACCEPTANCE.json",
    "rendered_prompts": ROOT / "PIL_V41_RENDERED_PROMPTS.jsonl",
    "prepaid_code_audit": ROOT / "PIL_V41_PREPAID_CODE_AUDIT.json",
}
IMPLEMENTATION_FILES = {
    "preflight": ROOT / "pil_v4_preflight.py",
    "contract": ROOT / "pil_v4_contract.py",
    "arms": ROOT / "pil_v4_arms.py",
    "client": ROOT / "pil_v4_client.py",
    "provider": ROOT / "pil_v4_provider.py",
    "schedule": ROOT / "pil_v4_schedule.py",
    "runner": ROOT / "pil_v4_run.py",
    "rescore": ROOT / "pil_v4_rescore.py",
    "authorizer": ROOT / "pil_v4_authorize.py",
    "prepaid_freezer": ROOT / "pil_v4_freeze_prepaid.py",
    "prompt_renderer": ROOT / "pil_v41_render_prompts.py",
    "english_input_builder": ROOT / "build_pil_v41_english_inputs.py",
    "prepaid_audit": ROOT / "pil_v41_prepaid_audit.py",
}
AGREEMENT_REPORT = (
    ROOT / "review" / "PIL_C1_ACCEPTANCE_AND_INTERREVIEWER_REPORT_2026-09-03.md"
)
ADJUDICATION_RECORD = ROOT / "PIL_V4_ADJUDICATION_RECORD.json"
D1_ACCEPTANCE = ROOT / "PIL_D1_ACCEPTANCE.json"


def _json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def build(*, offline_tests_passed: bool) -> dict[str, Any]:
    issues: list[str] = []
    for name, file in {**INPUTS, **IMPLEMENTATION_FILES}.items():
        if not file.is_file():
            issues.append(f"missing input {name}: {file}")
    for file in (AGREEMENT_REPORT, ADJUDICATION_RECORD, D1_ACCEPTANCE):
        if not file.is_file():
            issues.append(f"missing review artifact: {file}")
    if issues:
        return {
            "schema_version": "atlas.pil.prepaid_readiness.v4.1",
            "status": "BLOCKED",
            "formal_run_enabled": False,
            "external_calls_authorized": False,
            "provider_calls": 0,
            "prepaid_blockers": issues,
        }

    inference = _jsonl(INPUTS["inference_dataset"])
    gold = _jsonl(INPUTS["consensus_gold"])
    knowledge = _jsonl(INPUTS["knowledge_base"])
    decision_schema = _json(INPUTS["decision_schema"])
    gold_schema = _json(INPUTS["gold_schema"])
    rules = _json(INPUTS["delivery_rules"])
    parameter_match = _json(INPUTS["autosar_v20_parameter_match"])
    english_manifest = _json(INPUTS["english_input_manifest"])
    legal_source_audit = _json(INPUTS["english_legal_source_audit"])
    translation_acceptance = _json(INPUTS["translation_parity_acceptance"])
    frozen_rendered_prompts = _jsonl(INPUTS["rendered_prompts"])
    prepaid_code_audit = _json(INPUTS["prepaid_code_audit"])
    adjudication = _json(ADJUDICATION_RECORD)
    d1 = _json(D1_ACCEPTANCE)
    provider_contract = dict(contract.PROVIDER_PROTOCOL)
    runtime_environment = contract.runtime_environment()
    review_workbook_value = str(
        (translation_acceptance.get("review_workbook") or {}).get("accepted_path") or ""
    )
    review_workbook_path = Path(review_workbook_value) if review_workbook_value else None
    if review_workbook_path is not None and not review_workbook_path.is_absolute():
        review_workbook_path = ROOT / review_workbook_path
    review_workbook_sha256 = (
        contract.sha256_file(review_workbook_path)
        if review_workbook_path is not None and review_workbook_path.is_file()
        else None
    )

    matched = parameter_match.get("matched_provider_parameters") or {}
    autosar_parameters_matched = (
        parameter_match.get("status") == "MATCHED_BEFORE_ANY_PIL_V41_PROVIDER_CALL"
        and parameter_match.get("pil_v41_provider_calls_before_match") == 0
        and (parameter_match.get("treatment_isolation_correction") or {}).get("status") == "PASS"
        and matched.get("requested_model") == provider_contract.get("model_name")
        and matched.get("observed_response_model")
        == provider_contract.get("expected_response_model")
        and matched.get("api_mode") == provider_contract.get("api_mode")
        and matched.get("stream_responses") == provider_contract.get("stream_responses")
        and matched.get("reasoning_effort") == provider_contract.get("reasoning_effort")
        and matched.get("temperature") == provider_contract.get("temperature")
        and matched.get("max_completion_tokens") == provider_contract.get("max_completion_tokens")
        and matched.get("request_timeout_seconds") == provider_contract.get("request_timeout_seconds")
        and matched.get("sdk_implicit_retries") == provider_contract.get("sdk_implicit_retries")
        and matched.get("application_transport_max_attempts")
        == provider_contract.get("application_transport_max_attempts")
        and matched.get("transport_retry_delays_seconds")
        == provider_contract.get("transport_retry_delays_seconds")
        and matched.get("transport_route_policy") == provider_contract.get("transport_route_policy")
        and matched.get("replicate_seeds") == provider_contract.get("replicate_seeds")
        and matched.get("structured_output_for_constrained_arms")
        == "strict_json_schema_no_fallback"
    )

    try:
        Draft202012Validator.check_schema(decision_schema)
        Draft202012Validator.check_schema(gold_schema)
    except Exception as error:
        issues.append(f"invalid schema: {type(error).__name__}: {error}")

    gold_validator = Draft202012Validator(gold_schema)
    invalid_gold: list[dict[str, Any]] = []
    for row in gold:
        row_errors = sorted(gold_validator.iter_errors(row), key=lambda item: list(item.absolute_path))
        if row_errors:
            invalid_gold.append({
                "id": row.get("id"),
                "errors": [error.message for error in row_errors[:5]],
            })
        decision = {
            key: row[key]
            for key in (
                "conclusion", "forum", "forum_type", "alternative_forum_types",
                "conditional_answer", "explicit_abstention", "legal_basis",
                "reasoning", "missing_facts",
            )
        }
        audit = contract.audit_decision(
            decision,
            schema=decision_schema,
            rules=rules,
            allowed_evidence=row.get("accepted_evidence") or [],
            require_english_natural_language=False,
        )
        if audit["status"] != "PASS":
            issues.append(f"gold case {row.get('id')} fails common contract: {audit['findings']}")

    if invalid_gold:
        issues.append(f"gold schema failures: {invalid_gold}")

    ids = [row.get("id") for row in inference]
    gold_ids = [row.get("id") for row in gold]
    inference_surface = {"id", "cluster_id", "facts_text", "source_class"}
    forbidden = {
        "expected_output", "gold", "connecting_factors",
        "accepted_conclusions", "accepted_forum_types",
    }
    leaks = sorted({key for row in inference for key in row if key in forbidden})
    excess = sorted({key for row in inference for key in set(row) - inference_surface})
    if leaks:
        issues.append("inference dataset leaks evaluation fields: " + ",".join(leaks))
    if excess:
        issues.append("inference dataset has undeclared fields: " + ",".join(excess))

    evidence_ids = [str(row.get("evidence_id") or "") for row in knowledge]
    evidence_set = set(evidence_ids)
    evidence_identity_ok = (
        len(evidence_ids) == len(evidence_set)
        and all(item.startswith(("BRUSSELS_I_BIS:", "EU_TRADE_MARK_REGULATION:")) for item in evidence_ids)
    )
    official_sources_ok = all(
        str(row.get("official_url") or "").startswith("https://eur-lex.europa.eu/")
        and row.get("text_status") == "concise_english_paraphrase_checked_against_official_source"
        for row in knowledge
    ) and (
        legal_source_audit.get("status") == "PASS"
        and (legal_source_audit.get("knowledge_base") or {}).get("sha256")
        == contract.sha256_file(INPUTS["knowledge_base"])
        and legal_source_audit.get("provider_calls_during_audit") == 0
    )
    article_distinction_ok = (
        set(rules["forum_type_required_basis_prefixes"]["lis_pendens"])
        == {"BRUSSELS_I_BIS:Art.29"}
        and set(rules["forum_type_required_basis_prefixes"]["related_actions"])
        == {"BRUSSELS_I_BIS:Art.30"}
        and "BRUSSELS_I_BIS:Art.31(2)" in rules["forum_type_required_basis_prefixes"]["agreement"]
        and {
            "BRUSSELS_I_BIS:Art.29(1)",
            "BRUSSELS_I_BIS:Art.30(1)",
            "BRUSSELS_I_BIS:Art.31(2)",
        }.issubset(evidence_set)
    )

    context = pil_v4_arms.ArmContext.load(knowledge_base=INPUTS["knowledge_base"])
    rendered_prompts = [
        pil_v4_arms.render_primary_prompt(context, arm=arm, facts=str(case["facts_text"]))[0]
        for case in inference for arm in contract.ARMS
    ]
    expected_rendered_records = pil_v41_render_prompts.build()
    model_visible_cjk = sum(
        1 for prompt in rendered_prompts for char in prompt
        if "\u3400" <= char <= "\u9fff"
    )
    p123_prompt_parity = all(
        pil_v4_arms.render_primary_prompt(context, arm="p1", facts=str(case["facts_text"]))[0]
        == pil_v4_arms.render_primary_prompt(context, arm="p2", facts=str(case["facts_text"]))[0]
        == pil_v4_arms.render_primary_prompt(context, arm="p3", facts=str(case["facts_text"]))[0]
        for case in inference
    )
    retrieval_misses: list[dict[str, Any]] = []
    gold_by_id = {row["id"]: row for row in gold}
    for case in inference:
        retrieved = {str(row.get("evidence_id")) for row in context.retriever.retrieve(case["facts_text"])}
        required = set(gold_by_id[case["id"]].get("required_evidence") or [])
        if required and not (required & retrieved):
            retrieval_misses.append({
                "id": case["id"],
                "required": sorted(required),
                "retrieved": sorted(retrieved),
            })

    checks = {
        "inference_dataset_contains_no_gold": not leaks and not excess,
        "knowledge_base_checked_against_eur_lex": official_sources_ok,
        "article_29_30_31_distinguished": article_distinction_ok,
        "case_count_is_60": len(inference) == 60 and len(set(ids)) == 60,
        "gold_case_ids_match_dataset": len(gold) == 60 and set(gold_ids) == set(ids),
        "four_arm_schedule_is_720_units": len(inference) * len(contract.ARMS) * pil_v4_schedule.REPLICATES == 720,
        "instrument_qualified_evidence_ids": evidence_identity_ok,
        "consensus_gold_schema_valid": not invalid_gold,
        "retrieval_required_evidence_coverage_complete": not retrieval_misses,
        "dependency_clusters_declared": all(row.get("cluster_id") for row in inference)
        and {row.get("cluster_id") for row in inference} == {row.get("cluster_id") for row in gold},
        "implementation_files_hashed": all(file.is_file() for file in IMPLEMENTATION_FILES.values()),
        "provider_contract_frozen": (
            provider_contract.get("model_name") == "gpt-5.6-luna"
            and provider_contract.get("expected_response_model")
            == "gpt-5.6-luna-2026-07-09"
            and provider_contract.get("api_mode") == "chat.completions"
            and provider_contract.get("reasoning_effort") == "low"
            and provider_contract.get("temperature") == 1.0
            and provider_contract.get("tools_enabled") is False
            and provider_contract.get("max_completion_tokens") == 128000
            and provider_contract.get("sdk_implicit_retries") == 0
            and provider_contract.get("application_transport_max_attempts") == 8
            and provider_contract.get("request_timeout_seconds") == 180.0
            and provider_contract.get("stream_responses") is False
            and provider_contract.get("transport_route_policy")
            == "direct_no_environment_proxy"
            and provider_contract.get("seed_control")
            == "provider_best_effort_fixed_replicate_seeds"
            and provider_contract.get("replicate_seeds")
            == {"1": 104729, "2": 130363, "3": 155921}
        ),
        "autosar_v20_provider_parameters_matched": autosar_parameters_matched,
        "english_model_inputs_verified": (
            english_manifest.get("status") == "PASS"
            and english_manifest.get("model_visible_cjk_characters") == 0
            and english_manifest.get("case_ids_preserved") is True
            and english_manifest.get("cluster_ids_preserved") is True
            and english_manifest.get("evidence_ids_preserved") is True
            and english_manifest.get("official_urls_preserved") is True
            and (english_manifest.get("english_cases") or {}).get("sha256")
            == contract.sha256_file(INPUTS["inference_dataset"])
            and (english_manifest.get("english_kb") or {}).get("sha256")
            == contract.sha256_file(INPUTS["knowledge_base"])
        ),
        "english_legal_source_audit_passed": official_sources_ok,
        "translation_parity_review_complete": (
            translation_acceptance.get("status") == "PASS"
            and translation_acceptance.get("case_rows_accepted") == 60
            and translation_acceptance.get("evidence_rows_accepted") == 58
            and translation_acceptance.get("unresolved_rows") == 0
            and bool(translation_acceptance.get("accepted_workbook_sha256"))
            and bool(translation_acceptance.get("reviewer"))
            and bool(translation_acceptance.get("review_date"))
            and translation_acceptance.get("provider_calls_before_acceptance") == 0
            and (translation_acceptance.get("accepted_input_sha256s") or {}).get("english_cases")
            == contract.sha256_file(INPUTS["inference_dataset"])
            and (translation_acceptance.get("accepted_input_sha256s") or {}).get("english_kb")
            == contract.sha256_file(INPUTS["knowledge_base"])
        ),
        "translation_review_workbook_hash_verified": (
            review_workbook_sha256 is not None
            and review_workbook_sha256
            == translation_acceptance.get("accepted_workbook_sha256")
        ),
        "all_240_primary_prompts_are_english": len(rendered_prompts) == 240 and model_visible_cjk == 0,
        "p1_p2_p3_prompt_text_is_identical": p123_prompt_parity,
        "rendered_prompt_artifact_matches_implementation": frozen_rendered_prompts == expected_rendered_records,
        "prepaid_code_audit_passed": (
            prepaid_code_audit.get("status") == "PASS"
            and prepaid_code_audit.get("real_provider_requests") == 0
            and prepaid_code_audit.get("credentials_loaded") is False
            and (prepaid_code_audit.get("details") or {}).get("primary_prompt_artifact_sha256")
            == contract.sha256_file(INPUTS["rendered_prompts"])
            and (prepaid_code_audit.get("details") or {}).get("audited_implementation_sha256s")
            == {
                name: contract.sha256_file(file)
                for name, file in IMPLEMENTATION_FILES.items()
                if name != "prepaid_audit"
            }
        ),
        "runtime_environment_complete": all(
            value != "MISSING"
            for value in runtime_environment["packages"].values()
        ),
        "offline_tests_pass": offline_tests_passed,
    }
    issues.extend(f"required check failed: {key}" for key, passed in checks.items() if not passed)

    review_ok = (
        adjudication.get("status") == "CONSENSUS_COMPLETE"
        and d1.get("status") == "PASS"
        and d1.get("checks", {}).get("two_reviewer_confirmation") is True
    )
    if not review_ok:
        issues.append("review chain is not complete")

    input_manifest = {
        name: {"path": _relative(file), "sha256": contract.sha256_file(file)}
        for name, file in INPUTS.items()
    }
    status = "READY_FOR_PAID_AUTHORIZATION" if not issues else "BLOCKED"
    body = {
        "schema_version": "atlas.pil.prepaid_readiness.v4.1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "formal_run_enabled": False,
        "external_calls_authorized": False,
        "provider_calls": 0,
        "paid_api_calls": 0,
        "review": {
            "reviewer_1_locked": True,
            "reviewer_2_locked": True,
            "consensus_complete": review_ok,
            "affected_cases_reconfirmed_after_fact_edits": d1.get("status") == "PASS",
            "agreement_report_sha256": contract.sha256_file(AGREEMENT_REPORT),
            "adjudication_record_sha256": contract.sha256_file(ADJUDICATION_RECORD),
            "d1_acceptance_sha256": contract.sha256_file(D1_ACCEPTANCE),
        },
        "inputs": input_manifest,
        "implementation": {
            name: {"path": _relative(file), "sha256": contract.sha256_file(file)}
            for name, file in IMPLEMENTATION_FILES.items()
        },
        "provider_contract": provider_contract,
        "runtime_environment": runtime_environment,
        "required_checks": checks,
        "summary": {
            "case_count": len(inference),
            "gold_count": len(gold),
            "knowledge_entries": len(knowledge),
            "dependence_clusters": len({row.get("cluster_id") for row in inference}),
            "facts_changed_after_v2": adjudication.get("facts_changed_case_ids") or [],
            "retrieval_miss_count": len(retrieval_misses),
            "four_arm_units": len(inference) * len(contract.ARMS) * pil_v4_schedule.REPLICATES,
        },
        "retrieval_misses": retrieval_misses,
        "prepaid_blockers": issues,
        "execution_blocker": (
            "Explicit paid-run authorization has not been recorded. Create a separate formal readiness manifest; "
            "do not edit this frozen preflight manifest."
        ),
        "scope_limits": [
            "The 60 cases are synthetic, two-reviewer-adjudicated scenarios, not a probability sample of legal disputes.",
            "Five facts were changed after V2, so the frozen V2 outputs for those cases cannot be rescored against V4 gold.",
            "V4 estimates the four-arm mechanism within this PIL case set; it does not establish statistical generalization across domains.",
        ],
    }
    content = {key: value for key, value in body.items() if key != "created_at_utc"}
    return {**body, "content_sha256": contract.canonical_sha256(content)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "PIL_V41_PREFLIGHT_READINESS.json")
    parser.add_argument("--offline-tests-passed", action="store_true")
    parser.add_argument(
        "--replace-blocked", action="store_true",
        help="Explicitly replace an existing zero-call BLOCKED preflight after its blockers changed.",
    )
    args = parser.parse_args(argv)
    document = build(offline_tests_passed=args.offline_tests_passed)
    if args.output.exists():
        prior = _json(args.output)
        replaceable = (
            args.replace_blocked
            and prior.get("status") == "BLOCKED"
            and prior.get("provider_calls") == 0
            and prior.get("paid_api_calls") == 0
        )
        if not replaceable:
            raise ValueError(
                "refusing to overwrite an existing preflight; only an explicit "
                "--replace-blocked may replace a zero-call BLOCKED artifact"
            )
    args.output.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(args.output),
        "status": document["status"],
        "provider_calls": document["provider_calls"],
        "blockers": document.get("prepaid_blockers"),
        "summary": document.get("summary"),
        "content_sha256": document.get("content_sha256"),
    }, ensure_ascii=False, indent=2))
    return 0 if document["status"] == "READY_FOR_PAID_AUTHORIZATION" else 1


if __name__ == "__main__":
    raise SystemExit(main())
