"""Zero-network acceptance audit for the PIL V4.1 paid experiment.

The audit reconstructs every primary prompt, exercises the provider payload
with an in-memory transport, and exercises all four arm paths with synthetic
responses.  It never loads credentials and cannot call the configured API.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pil_v4_arms
import pil_v4_contract as contract
import pil_v4_provider
import pil_v4_schedule
import pil_v41_render_prompts
from pil_v4_client import COMMON_SYSTEM_INSTRUCTIONS, Generation, UnifiedV4Client


ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = ROOT / "PIL_V41_PREPAID_CODE_AUDIT.json"
AUDITED_IMPLEMENTATION = {
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
}


def _json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _valid_decision(*, forum_type: str = "exclusive", reasoning: str = "The provision controls.") -> dict[str, Any]:
    return {
        "conclusion": "Court_of_X_has_jurisdiction",
        "forum": "French courts",
        "forum_type": forum_type,
        "alternative_forum_types": [],
        "conditional_answer": False,
        "explicit_abstention": False,
        "legal_basis": [{"instrument": "BRUSSELS_I_BIS", "provision": "Art.24(1)"}],
        "reasoning": reasoning,
        "missing_facts": [],
    }


class _CapturedCompletions:
    def __init__(self, responses: list[Any]) -> None:
        self.responses = list(responses)
        self.requests: list[dict[str, Any]] = []

    def create(self, **request: Any) -> Any:
        self.requests.append(request)
        return self.responses.pop(0)


def _response(decision: dict[str, Any], response_id: str) -> Any:
    return SimpleNamespace(
        id=response_id,
        model=contract.PROVIDER_PROTOCOL["expected_response_model"],
        created=1788337678,
        system_fingerprint=None,
        service_tier="default",
        usage=SimpleNamespace(prompt_tokens=101, completion_tokens=23, total_tokens=124),
        choices=[SimpleNamespace(
            finish_reason="stop",
            message=SimpleNamespace(content=json.dumps(decision), refusal=None),
        )],
    )


class _SyntheticUnifiedClient:
    def __init__(self, decisions: list[dict[str, Any]]) -> None:
        self.decisions = list(decisions)
        self.prompts: list[str] = []
        self.schemas: list[dict[str, Any] | None] = []

    def generate(self, prompt: str, *, schema: dict[str, Any] | None, seed: int) -> Generation:
        self.prompts.append(prompt)
        self.schemas.append(schema)
        decision = self.decisions.pop(0)
        return Generation(
            raw_text=json.dumps(decision, ensure_ascii=False),
            parsed=decision if schema is not None else None,
            input_tokens=101,
            output_tokens=23,
            total_tokens=124,
            provider_schema_enforced=schema is not None,
            seed=seed,
            provider_response={
                "requested_model": contract.PROVIDER_PROTOCOL["model_name"],
                "response_model": contract.PROVIDER_PROTOCOL["expected_response_model"],
                "usage": {"input_tokens": 101, "output_tokens": 23, "total_tokens": 124},
            },
            transport_attempts=({
                "transport_attempt": 1,
                "status": "RESPONSE_RECEIVED",
                "request_sha256": "f" * 64,
            },),
        )


def _same_except(left: dict[str, Any], right: dict[str, Any], excluded: set[str]) -> bool:
    return (
        {key: value for key, value in left.items() if key not in excluded}
        == {key: value for key, value in right.items() if key not in excluded}
    )


def build(*, offline_tests_passed: bool) -> dict[str, Any]:
    checks: dict[str, bool] = {}
    details: dict[str, Any] = {}
    issues: list[str] = []

    cases = _jsonl(ROOT / "data" / "inference_dataset_v41_en.jsonl")
    knowledge_path = ROOT / "kb" / "authoritative_provisions_v41_en.jsonl"
    knowledge = _jsonl(knowledge_path)
    schema = contract.load_schema()
    context = pil_v4_arms.ArmContext.load(knowledge_base=knowledge_path)
    prompt_records = pil_v41_render_prompts.build()
    frozen_prompt_records = _jsonl(ROOT / "PIL_V41_RENDERED_PROMPTS.jsonl")

    checks["offline_test_suite_passed"] = offline_tests_passed
    checks["english_case_and_knowledge_counts"] = len(cases) == 60 and len(knowledge) == 58
    checks["rendered_prompt_count_and_freeze_match"] = (
        len(prompt_records) == 240 and prompt_records == frozen_prompt_records
    )
    checks["all_primary_model_messages_are_english"] = (
        not contract.contains_cjk(COMMON_SYSTEM_INSTRUCTIONS)
        and all(row.get("cjk_characters") == 0 for row in prompt_records)
    )
    checks["all_primary_prompts_include_complete_schema"] = all(
        json.dumps(schema, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        in str(row.get("prompt") or "")
        for row in prompt_records
    )

    by_case_arm = {
        (row["case_id"], row["arm"]): row
        for row in prompt_records
    }
    parity_failures: list[int] = []
    evidence_failures: list[int] = []
    for case in cases:
        rows = [by_case_arm[(case["id"], arm)] for arm in ("p1", "p2", "p3")]
        if len({row["prompt_sha256"] for row in rows}) != 1:
            parity_failures.append(case["id"])
        if len({tuple(row["evidence_ids"]) for row in rows}) != 1:
            evidence_failures.append(case["id"])
        if by_case_arm[(case["id"], "p0")]["evidence_ids"]:
            evidence_failures.append(case["id"])
    checks["p1_p2_p3_exact_prompt_parity"] = not parity_failures
    checks["retrieval_exposure_is_identical_for_grounded_arms"] = not evidence_failures
    details["prompt_parity_failure_case_ids"] = parity_failures
    details["evidence_exposure_failure_case_ids"] = sorted(set(evidence_failures))

    # Exercise soft and strict requests with an in-memory provider surface.
    capture = _CapturedCompletions([
        _response(_valid_decision(), "soft-fixture"),
        _response(_valid_decision(), "strict-fixture"),
    ])
    transport = pil_v4_provider.V4ChatCompletionsTransport(
        api_key="fixture-not-a-real-key",
        base_url="https://example.invalid/v1",
        transport=SimpleNamespace(chat=SimpleNamespace(completions=capture)),
    )
    unified = UnifiedV4Client(transport)
    sample_prompt = by_case_arm[(cases[0]["id"], "p1")]["prompt"]
    soft = unified.generate(sample_prompt, schema=None, seed=104729)
    strict = unified.generate(sample_prompt, schema=schema, seed=104729)
    soft_request, strict_request = capture.requests
    checks["p2_minus_p1_payload_diff_is_response_format_only"] = (
        _same_except(soft_request, strict_request, {"response_format"})
        and "response_format" not in soft_request
        and strict_request.get("response_format", {}).get("type") == "json_schema"
        and strict_request.get("response_format", {}).get("json_schema", {}).get("strict") is True
    )
    checks["provider_payload_matches_autosar_v20"] = (
        soft_request.get("model") == "gpt-5.6-luna"
        and soft_request.get("reasoning_effort") == "low"
        and soft_request.get("temperature") == 1.0
        and soft_request.get("max_completion_tokens") == 128000
        and soft_request.get("seed") == 104729
        and "tools" not in soft_request
        and contract.PROVIDER_PROTOCOL.get("api_mode") == "chat.completions"
        and contract.PROVIDER_PROTOCOL.get("stream_responses") is False
        and contract.PROVIDER_PROTOCOL.get("sdk_implicit_retries") == 0
    )
    checks["response_snapshot_and_usage_are_recorded"] = (
        soft.provider_response.get("response_model")
        == contract.PROVIDER_PROTOCOL["expected_response_model"]
        and soft.provider_response.get("usage")
        == {"input_tokens": 101, "output_tokens": 23, "total_tokens": 124}
        and soft.total_tokens == 124
        and strict.total_tokens == 124
    )

    # Exercise P0/P1/P2 and the P3 repair path without calling the provider.
    sample_case = cases[0]
    rows: dict[str, dict[str, Any]] = {}
    for arm in ("p0", "p1", "p2"):
        fake = _SyntheticUnifiedClient([_valid_decision()])
        rows[arm] = pil_v4_arms.run_unit(
            fake, context,
            {"unit_id": f"1|{arm}|1", "case_id": 1, "arm": arm, "replicate": 1},
            sample_case,
        )
    invalid = _valid_decision(forum_type="general", reasoning="法院有管辖权。")
    fake_p3 = _SyntheticUnifiedClient([invalid, _valid_decision()])
    rows["p3"] = pil_v4_arms.run_unit(
        fake_p3, context,
        {"unit_id": "1|p3|1", "case_id": 1, "arm": "p3", "replicate": 1},
        sample_case,
    )
    checks["arm_enforcement_flags_are_correct"] = (
        rows["p0"]["provider_schema_enforced"] is False
        and rows["p1"]["provider_schema_enforced"] is False
        and rows["p2"]["provider_schema_enforced"] is True
        and rows["p3"]["provider_schema_enforced"] is True
    )
    checks["p3_has_one_bounded_english_repair"] = (
        rows["p3"]["repair"]["attempted"] is True
        and rows["p3"]["logical_request_count"] == 2
        and rows["p3"]["transport_request_count"] == 2
        and rows["p3"]["repair"]["prompt_cjk_characters"] == 0
        and not contract.contains_cjk(rows["p3"]["repair"]["prompt"])
    )
    checks["per_unit_request_and_token_records_present"] = all(
        row.get("system_instructions_sha256")
        and row.get("prompt_sha256")
        and row.get("logical_request_count")
        and row.get("transport_request_count")
        and (row.get("usage") or {}).get("total_tokens")
        and all((response or {}).get("usage") for response in row.get("provider_responses") or [])
        for row in rows.values()
    )

    abort = _json(ROOT / "PIL_V4_DESIGN_AUDIT_ABORT_2026-09-04.json")
    checks["predecessor_batch_is_explicitly_excluded"] = (
        abort.get("status") == "ABORTED_DESIGN_CONFOUND_DETECTED_DURING_EXECUTION"
        and abort.get("completed_units") == 132
        and abort.get("logical_model_calls") == 136
        and abort.get("admissible_to_primary_analysis") is False
        and abort.get("admissible_to_paper_tables") is False
        and abort.get("resume_permitted") is False
        and abort.get("selective_reuse_permitted") is False
    )
    legal_source_audit = _json(ROOT / "PIL_V41_ENGLISH_LEGAL_SOURCE_AUDIT.json")
    checks["english_legal_source_audit_passed"] = (
        legal_source_audit.get("status") == "PASS"
        and legal_source_audit.get("knowledge_base", {}).get("sha256")
        == contract.sha256_file(knowledge_path)
        and legal_source_audit.get("provider_calls_during_audit") == 0
    )
    translation_acceptance = _json(ROOT / "PIL_V41_TRANSLATION_PARITY_ACCEPTANCE.json")
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
    checks["translation_parity_review_evidence_verified"] = (
        translation_acceptance.get("status") == "PASS"
        and translation_acceptance.get("case_rows_accepted") == 60
        and translation_acceptance.get("evidence_rows_accepted") == 58
        and translation_acceptance.get("unresolved_rows") == 0
        and translation_acceptance.get("provider_calls_before_acceptance") == 0
        and review_workbook_sha256
        == translation_acceptance.get("accepted_workbook_sha256")
        and (translation_acceptance.get("accepted_input_sha256s") or {}).get("english_cases")
        == contract.sha256_file(ROOT / "data" / "inference_dataset_v41_en.jsonl")
        and (translation_acceptance.get("accepted_input_sha256s") or {}).get("english_kb")
        == contract.sha256_file(knowledge_path)
    )
    details["translation_review_workbook_sha256"] = review_workbook_sha256
    checks["four_arm_design_is_exactly_720_units"] = (
        len(cases) * len(contract.ARMS) * pil_v4_schedule.REPLICATES == 720
    )

    parameter_match = _json(ROOT / "PIL_V41_AUTOSAR_V20_PARAMETER_MATCH.json")
    autosar_source = parameter_match.get("autosar_v20_source") or {}
    autosar_archive = Path(str(autosar_source.get("archive") or ""))
    autosar_entry = str(autosar_source.get("contract_entry") or "")
    autosar_contract: dict[str, Any] = {}
    autosar_entry_sha = ""
    if autosar_archive.is_file() and autosar_entry:
        with zipfile.ZipFile(autosar_archive) as archive:
            raw_contract = archive.read(autosar_entry)
        autosar_entry_sha = hashlib.sha256(raw_contract).hexdigest()
        autosar_contract = json.loads(raw_contract.decode("utf-8"))
    generation = autosar_contract.get("generation") or {}
    registration = generation.get("provider_registration") or {}
    checks["autosar_v20_source_contract_reverified"] = (
        autosar_archive.is_file()
        and contract.sha256_file(autosar_archive) == autosar_source.get("archive_sha256")
        and autosar_entry_sha == autosar_source.get("contract_entry_sha256")
        and registration.get("requested_model") == contract.PROVIDER_PROTOCOL["model_name"]
        and generation.get("reasoning_effort") == contract.PROVIDER_PROTOCOL["reasoning_effort"]
        and (generation.get("temperature") or {}).get("interface")
        == contract.PROVIDER_PROTOCOL["temperature"]
        and generation.get("max_completion_tokens")
        == contract.PROVIDER_PROTOCOL["max_completion_tokens"]
        and registration.get("request_timeout_seconds")
        == contract.PROVIDER_PROTOCOL["request_timeout_seconds"]
        and registration.get("max_attempts_per_call")
        == contract.PROVIDER_PROTOCOL["application_transport_max_attempts"]
        and registration.get("transport_retry_delays_seconds")
        == contract.PROVIDER_PROTOCOL["transport_retry_delays_seconds"]
        and registration.get("transport_route_policy")
        == contract.PROVIDER_PROTOCOL["transport_route_policy"]
        and generation.get("stream_responses")
        == contract.PROVIDER_PROTOCOL["stream_responses"]
        and (autosar_contract.get("requirement_set") or {}).get("seeds")
        == list(contract.PROVIDER_PROTOCOL["replicate_seeds"].values())
        and abort.get("returned_model_set")
        == [contract.PROVIDER_PROTOCOL["expected_response_model"]]
    )
    details["autosar_v20_archive_sha256"] = (
        contract.sha256_file(autosar_archive) if autosar_archive.is_file() else None
    )
    details["autosar_v20_contract_entry_sha256"] = autosar_entry_sha or None

    details["simulated_model_requests"] = 7
    details["real_provider_requests"] = 0
    details["primary_prompt_artifact_sha256"] = contract.sha256_file(
        ROOT / "PIL_V41_RENDERED_PROMPTS.jsonl"
    )
    details["english_case_sha256"] = contract.sha256_file(
        ROOT / "data" / "inference_dataset_v41_en.jsonl"
    )
    details["english_knowledge_sha256"] = contract.sha256_file(knowledge_path)
    details["audited_implementation_sha256s"] = {
        name: contract.sha256_file(path)
        for name, path in AUDITED_IMPLEMENTATION.items()
    }

    issues.extend(key for key, passed in checks.items() if not passed)
    status = "PASS" if not issues else "FAIL"
    body = {
        "schema_version": "atlas.pil.prepaid_code_audit.v4.1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "audit_mode": "zero_network_in_memory_provider_and_arm_simulation",
        "real_provider_requests": 0,
        "credentials_loaded": False,
        "checks": checks,
        "details": details,
        "failures": issues,
        "remaining_external_gate": (
            "The bilingual input-parity review is complete and hash-verified. The remaining gate is "
            "an explicit paid-run authorization bound to the frozen preflight."
        ),
    }
    stable = {key: value for key, value in body.items() if key != "created_at_utc"}
    return {**body, "content_sha256": contract.canonical_sha256(stable)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--offline-tests-passed", action="store_true")
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args(argv)
    report = build(offline_tests_passed=args.offline_tests_passed)
    if args.output.exists() and not args.replace:
        raise ValueError("refusing to overwrite existing prepaid audit without --replace")
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8", newline="\n",
    )
    print(json.dumps({
        "output": str(args.output),
        "status": report["status"],
        "real_provider_requests": report["real_provider_requests"],
        "failures": report["failures"],
        "content_sha256": report["content_sha256"],
    }, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
