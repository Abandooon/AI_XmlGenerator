"""Freeze the ASW-FULL-06 machine-contract smoke evidence without ranking models."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
RUN_ROOT = ROOT / "outputs" / "paper-v3-complex-smoke-20260811"
OUTPUT = ROOT / "REQUIREMENT_CONTRACT_SMOKE_MANIFEST.json"
LOCAL_ACCEPTANCE = ROOT / "LOCAL_PIPELINE_ACCEPTANCE_MANIFEST.json"
TERRA_ROOT = RUN_ROOT / "terra" / "ASW-FULL-06" / "R1-contract1"
SOL_ROOT = RUN_ROOT / "sol" / "ASW-FULL-06" / "R1-contract1"
EXPECTED_COMPONENT_SHA256 = (
    "5b56b938d3871b659512abfd97ced4490eb9938fd2343f06d84a9bf406c585e3"
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def one(paths: list[Path], label: str) -> Path:
    if len(paths) != 1:
        raise RuntimeError(f"expected exactly one {label}, found {len(paths)}")
    return paths[0]


def phase1_contract_record(run_root: Path) -> dict[str, Any]:
    phase1_path = one(
        sorted((run_root / "atlas_output" / "round1_data").glob("*.json")),
        "Phase 1 artifact",
    )
    payload = json.loads(phase1_path.read_text(encoding="utf-8"))
    plans = (payload.get("response_data") or {}).get("component_plan") or []
    audits = (payload.get("stats") or {}).get("declared_value_reconciliation") or []
    if len(plans) != 1 or len(audits) != 1:
        raise RuntimeError("Phase 1 artifact has an unexpected component/audit cardinality")
    plan = plans[0]
    audit = audits[0]
    contracts = audit.get("requirement_contracts") or []
    if (
        audit.get("applied_count") != 61
        or audit.get("requirement_contract_count") != 5
        or any(item.get("decision") != "PASS" for item in contracts)
        or (plan.get("element_design") or {}).get("unsupported") != []
    ):
        raise RuntimeError("Phase 1 machine requirement contracts are not fully resolved")
    return {
        "path": str(phase1_path),
        "sha256": sha256_file(phase1_path),
        "selection_count": len((plan.get("element_design") or {}).get("selections") or []),
        "unsupported_count": 0,
        "applied_obligation_count": 61,
        "requirement_contract_count": 5,
        "resolved_unsupported_count": int(audit.get("resolved_unsupported_count") or 0),
        "resolved_unsupported_requirement_ids": [
            str(item.get("requirement_id"))
            for item in audit.get("resolved_unsupported") or []
        ],
        "contracts": contracts,
    }


def terra_record() -> dict[str, Any]:
    summary_path = TERRA_ROOT / "run_summary.json"
    revalidation_path = TERRA_ROOT / "offline_revalidation.json"
    evaluation_path = TERRA_ROOT / "requirement_evaluation.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    revalidation = json.loads(revalidation_path.read_text(encoding="utf-8"))
    evaluation = json.loads(evaluation_path.read_text(encoding="utf-8"))
    component = one(
        sorted((TERRA_ROOT / "atlas_output" / "ARXML" / "Components").glob("*.arxml")),
        "Terra component",
    )
    if (
        summary.get("model") != "gpt-5.6-terra"
        or summary.get("error")
        or summary.get("phase2", {}).get("artifact_profile_decision") != "PASS"
        or revalidation.get("selection_obligations", {}).get("decision") != "PASS"
        or revalidation.get("artifact_profile", {}).get("decision") != "PASS"
        or evaluation.get("decision") != "PASS"
        or evaluation.get("promotable") is not True
        or evaluation.get("structural_failure_count") != 0
        or evaluation.get("local_reference_failure_count") != 0
        or evaluation.get("external_reference_not_evaluated_count") != 0
        or sha256_file(component) != EXPECTED_COMPONENT_SHA256
    ):
        raise RuntimeError("Terra full smoke evidence does not satisfy the frozen gates")
    return {
        "execution_status": "COMPLETE",
        "model_quality_decision": "PASS",
        "rank_eligible": False,
        "reason_not_rank_eligible": "single diagnostic case and repetition",
        "run_summary": {
            "path": str(summary_path),
            "sha256": sha256_file(summary_path),
            "phase1": summary.get("phase1"),
            "phase2": summary.get("phase2"),
        },
        "phase1_machine_contract": phase1_contract_record(TERRA_ROOT),
        "component": {"path": str(component), "sha256": sha256_file(component)},
        "offline_revalidation": {
            "path": str(revalidation_path),
            "sha256": sha256_file(revalidation_path),
            "fingerprint_sha256": revalidation.get("revalidation_fingerprint_sha256"),
            "validation_decision": revalidation.get("validation", {}).get("decision"),
            "selection_obligation_decision": revalidation.get(
                "selection_obligations", {}
            ).get("decision"),
            "artifact_profile_decision": revalidation.get("artifact_profile", {}).get(
                "decision"
            ),
        },
        "independent_requirement_evaluation": {
            "path": str(evaluation_path),
            "sha256": sha256_file(evaluation_path),
            "decision": evaluation.get("decision"),
            "promotable": evaluation.get("promotable"),
            "structural_failure_count": evaluation.get("structural_failure_count"),
            "local_reference_failure_count": evaluation.get(
                "local_reference_failure_count"
            ),
        },
    }


def sol_record() -> dict[str, Any]:
    summary_path = SOL_ROOT / "run_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    error = str(summary.get("error") or "")
    if (
        summary.get("model") != "gpt-5.6-sol"
        or summary.get("final_status") != "failure"
        or "insufficient_balance" not in error
        or summary.get("phase1", {}).get("component_count") != 1
    ):
        raise RuntimeError("Sol diagnostic is not the expected external-balance failure")
    return {
        "execution_status": "BLOCKED_EXTERNAL_BALANCE",
        "model_quality_decision": "NOT_EVALUATED",
        "rank_eligible": False,
        "failure_stage": "PHASE2_PROVIDER_CALL",
        "provider_error_code": "insufficient_balance",
        "run_summary": {
            "path": str(summary_path),
            "sha256": sha256_file(summary_path),
            "phase1": summary.get("phase1"),
        },
        "phase1_machine_contract": phase1_contract_record(SOL_ROOT),
    }


def build_manifest() -> dict[str, Any]:
    acceptance = json.loads(LOCAL_ACCEPTANCE.read_text(encoding="utf-8"))
    if acceptance.get("decision") != "LOCAL_CHAIN_ACCEPTED_FAIL_CLOSED":
        raise RuntimeError("local acceptance is not green")
    body: dict[str, Any] = {
        "schema_version": "atlas.autosar.requirement_contract_smoke.v1",
        "case_id": "ASW-FULL-06",
        "seed": 104729,
        "decision": "TERRA_FULL_PASS_SOL_EXTERNAL_BALANCE_BLOCKED_LUNA_NOT_ATTEMPTED",
        "ranking": {"permitted": False, "winner": None},
        "machine_contract": {
            "requirement_contract_count": 5,
            "value_obligation_count": 61,
            "unsupported_resolution_rule": (
                "an authorized requirement_id is removed only after all expected "
                "hash-pinned XSD obligations compile and apply"
            ),
        },
        "local_acceptance": {
            "path": str(LOCAL_ACCEPTANCE),
            "sha256": sha256_file(LOCAL_ACCEPTANCE),
            "decision": acceptance["decision"],
            "acceptance_fingerprint_sha256": acceptance["acceptance_fingerprint_sha256"],
            "test_count": acceptance["evidence"]["gates"]["offline_target_tests"][
                "test_count"
            ],
        },
        "models": {
            "gpt-5.6-terra": terra_record(),
            "gpt-5.6-sol": sol_record(),
            "gpt-5.6-luna": {
                "execution_status": "NOT_ATTEMPTED_AFTER_EXTERNAL_BALANCE_BLOCK",
                "model_quality_decision": "NOT_EVALUATED",
                "rank_eligible": False,
            },
        },
        "constraints_recompiled": False,
        "historical_artifacts_modified": False,
    }
    body["manifest_sha256"] = canonical_sha256(body)
    return body


def main() -> int:
    manifest = build_manifest()
    OUTPUT.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {"manifest": str(OUTPUT), "manifest_sha256": manifest["manifest_sha256"]},
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
