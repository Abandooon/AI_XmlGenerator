"""Resumable zero-network E2E for the real AUTOSAR Phase1/2 and repair runners."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

from experiment_runtime import (
    atomic_write_json,
    atomic_write_text,
    child_state_path,
    run_child_process,
    utc_now,
)
from repair_asw_v3_run import repair_run
from run_asw_v3_repair_experiment import (
    canonical_sha256,
    sha256_file,
    verify_controlled_reference_manifest,
)


ROOT = Path(__file__).resolve().parent
ATLAS_ROOT = Path(r"E:\git projects\AI_XmlGenerator")
PHASE12_RUNNER = ROOT / "run_phase12_case.py"
FORMAL_CONTRACT = ROOT / "FORMAL_EXPERIMENT_CONTRACT.json"
DEFAULT_REFERENCE_MANIFEST = ROOT / "CONTROLLED_REFERENCE_BASELINES_V16_MANIFEST.json"
CASE_ID = "ASW-MIN-01"
MODEL = "gpt-5.6-luna"


def _load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _provider_audit(path: Path) -> list[dict[str, Any]]:
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    if any(
        item.get("credentials_included") is not False
        or item.get("actual_paid_provider_call") is not False
        for item in records
    ):
        raise ValueError("scripted provider audit crossed the zero-network boundary")
    return records


def _phase_command(run_root: Path, *, fail_stage: str | None) -> list[str]:
    command = [
        sys.executable,
        "-B",
        str(PHASE12_RUNNER),
        "--model",
        MODEL,
        "--case-id",
        CASE_ID,
        "--repetition",
        "1",
        "--repair-mode",
        "off",
        "--run-root",
        str(run_root),
        "--attempt-number",
        "1",
        "--offline-scripted",
    ]
    if fail_stage:
        command.extend(["--scripted-fail-stage", fail_stage])
    return command


def _run_phase(
    root: Path, name: str, *, fail_stage: str | None, expected_returncode: int
) -> dict[str, Any]:
    run_root = root / name
    result = run_child_process(
        _phase_command(run_root, fail_stage=fail_stage),
        cwd=ROOT,
        timeout_seconds=120,
        state_path=child_state_path(root, name, 1),
    )
    atomic_write_text(root / f"{name}.stdout.log", result.stdout)
    atomic_write_text(root / f"{name}.stderr.log", result.stderr)
    if result.returncode != expected_returncode or result.timed_out:
        raise RuntimeError(
            f"{name} returned {result.returncode}, expected {expected_returncode}"
        )
    summary_path = run_root / "run_summary.json"
    summary = _load_object(summary_path)
    return {
        "run_root": str(run_root),
        "run_summary_sha256": sha256_file(summary_path),
        "provider_audit_sha256": sha256_file(run_root / "provider_calls.jsonl"),
        "provider_call_count": len(_provider_audit(run_root / "provider_calls.jsonl")),
        "final_status": summary.get("final_status"),
        "error": summary.get("error"),
    }


def _verify_upstream_state(root: Path, state: dict[str, Any]) -> dict[str, Any]:
    repaired = state["upstream_repaired"]
    run_root = Path(repaired["run_root"])
    summary_path = run_root / "run_summary.json"
    audit_path = run_root / "provider_calls.jsonl"
    if (
        sha256_file(summary_path) != repaired["run_summary_sha256"]
        or sha256_file(audit_path) != repaired["provider_audit_sha256"]
    ):
        raise ValueError("durable upstream repair evidence changed before resume")
    summary = _load_object(summary_path)
    audit = _provider_audit(audit_path)
    if len(audit) != 3 or len(audit) != repaired["provider_call_count"]:
        raise ValueError("resume would duplicate or omit a scripted provider call")
    phase2 = summary.get("phase2") or {}
    runtime_gate = summary.get("provider_runtime_gate") or {}
    if (
        runtime_gate.get("decision") != "PASS"
        or runtime_gate.get("sdk_implicit_max_retries") != [0, 0]
        or runtime_gate.get("concrete_transport_route_policies")
        != ["direct_no_environment_proxy", "direct_no_environment_proxy"]
        or runtime_gate.get("observed_audit_transport_route_policies")
        != ["offline_scripted_no_network"]
        or runtime_gate.get("all_provider_calls_have_identity") is not True
        or set(runtime_gate.get("observed_pipeline_phases") or [])
        != {"round1", "round2.interface", "round2.component"}
    ):
        raise ValueError("provider runtime identity/retry/phase gate failed")
    provenance = list(phase2.get("provider_payload_provenance") or [])
    if len(provenance) != 2:
        raise ValueError("scripted Phase2 has ambiguous raw provider provenance")
    by_scope = {str(item.get("scope") or ""): item for item in provenance}
    if set(by_scope) != {"interfaces", "component"}:
        raise ValueError("scripted Phase2 provenance scopes are incomplete")
    raw_payload_sha256: dict[str, str] = {}
    for scope, item in sorted(by_scope.items()):
        raw = item.get("raw_provider_payload") or {}
        raw_path = Path(str(raw.get("path") or ""))
        if (
            "provider_raw" not in raw_path.name
            or sha256_file(raw_path) != raw.get("file_sha256")
            or item.get("raw_provider_schema_status") != "PASS"
            or item.get("normalization_status") != "NOT_APPLICABLE"
            or item.get("final_atlas_status") != "PASS"
        ):
            raise ValueError(
                f"raw/normalization/final Phase2 provenance is not admissible: {scope}"
            )
        raw_payload_sha256[scope] = str(raw["file_sha256"])
    counters = phase2.get("provider_payload_status_counters") or {}
    if (
        (counters.get("raw_provider_schema_status") or {}).get("PASS") != 2
        or (counters.get("normalization_status") or {}).get("NOT_APPLICABLE") != 2
        or (counters.get("final_atlas_status") or {}).get("PASS") != 2
        or phase2.get("artifact_profile_decision") != "PASS"
    ):
        raise ValueError("Phase2 provider status counters are incomplete")
    return {
        "summary": summary,
        "provider_audit": audit,
        "raw_provider_payload_sha256": raw_payload_sha256,
    }


def _temporary_registry_gate(root: Path, schedule_sha256: str) -> dict[str, Any]:
    if str(ATLAS_ROOT) not in sys.path:
        sys.path.insert(0, str(ATLAS_ROOT))
    from src.workbench.artifacts import (
        WorkbenchArtifactError,
        assert_latest_autosar_identity,
    )

    registry = {
        "schema_version": "atlas.experiment_registry.v1",
        "policy": {
            "legacy_results_allowed_in_primary_tables": False,
            "paper_and_promotion_require_active_identity": True,
            "predecessor_allowed_roles": ["archive", "regression"],
        },
        "experiments": {
            "autosar": {
                "predecessor_result": {
                    "id": "E1-V15-IMMUTABLE-PREDECESSOR",
                    "schedule_sha256": "f" * 64,
                },
                "active_result_status": "CURRENT_FORMAL_RESULT",
                "active_result_id": "V17-OFFLINE-E2E-NONPAPER",
                "active_schedule_sha256": schedule_sha256,
                "active_code_line": "V17-OFFLINE-E2E",
            }
        },
    }
    registry_path = root / "temporary_e2e_registry.json"
    atomic_write_json(registry_path, registry)
    accepted = assert_latest_autosar_identity(
        {"schedule_content_sha256": schedule_sha256},
        purpose="paper_primary",
        registry_path=registry_path,
    )
    stale_refused = False
    try:
        assert_latest_autosar_identity(
            {"schedule_content_sha256": "e" * 64},
            purpose="paper_primary",
            registry_path=registry_path,
        )
    except WorkbenchArtifactError:
        stale_refused = True
    if not stale_refused:
        raise ValueError("latest-only registry accepted a stale schedule")
    return {"accepted": accepted, "stale_schedule_refused": True}


def run(
    root: Path,
    reference_manifest_path: Path,
    *,
    stop_after_upstream: bool,
) -> tuple[dict[str, Any], int]:
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    state_path = root / "e2e_state.json"
    state = _load_object(state_path) if state_path.is_file() else {}
    if state:
        state_unsigned = {
            key: value for key, value in state.items() if key != "content_sha256"
        }
        if canonical_sha256(state_unsigned) != state.get("content_sha256"):
            raise ValueError("offline E2E resume state canonical hash mismatch")
    if not state:
        contract = _load_object(FORMAL_CONTRACT)
        registration = contract["generation"]["provider_registration"]
        if (
            registration.get("requested_model") != MODEL
            or float(registration.get("request_timeout_seconds") or 0) != 180.0
            or int(registration.get("max_attempts_per_call") or 0) != 1
            or len(str(registration.get("provider_endpoint_sha256") or "")) != 64
            or registration.get("transport_route_policy")
            != "direct_no_environment_proxy"
            or contract["generation"].get("stream_responses") is not False
            or contract["generation"].get("transport_route_policy")
            != "direct_no_environment_proxy"
        ):
            raise ValueError("formal provider registration is incomplete or unsafe")
        failure = _run_phase(
            root, "generation_failure", fail_stage="round1", expected_returncode=1
        )
        if failure["final_status"] != "failure" or "SCRIPTED_ROUND1_FAILURE" not in str(
            failure["error"]
        ):
            raise ValueError("scripted generation failure was not preserved")
        repaired = _run_phase(
            root, "upstream_repaired", fail_stage=None, expected_returncode=0
        )
        if repaired["provider_call_count"] != 3:
            raise ValueError("successful full-context run did not use exactly three calls")
        state = {
            "schema_version": "atlas.autosar.v17.offline_e2e_state.v1",
            "stage": "UPSTREAM_REPAIRED_DURABLE",
            "formal_contract_sha256": sha256_file(FORMAL_CONTRACT),
            "provider_registration": registration,
            "generation_failure": failure,
            "upstream_repaired": repaired,
            "simulated_interrupt_boundary": "after_durable_upstream_repair",
            "updated_at_utc": utc_now(),
        }
        state["content_sha256"] = canonical_sha256(state)
        atomic_write_json(state_path, state)

    verified = _verify_upstream_state(root, state)
    if stop_after_upstream and state.get("stage") == "UPSTREAM_REPAIRED_DURABLE":
        return state, 75

    reference_manifest = verify_controlled_reference_manifest(
        reference_manifest_path
    )
    reference_record = next(
        item
        for item in reference_manifest["records"]
        if item["case_id"] == CASE_ID
    )
    repair_root = root / "artifact_repair"
    if not (repair_root / "repair_experiment_manifest.json").is_file():
        os.environ["LLM_API_KEY"] = "offline-local-placeholder"
        repair = repair_run(
            baseline_root=Path(
                reference_record["deterministic_reference_baseline"]["root"]
            ),
            output_root=repair_root,
            case_id=CASE_ID,
            model=MODEL,
            seed=104729,
            mutation="wrong_xsd_order",
            max_rounds=2,
            repair_schedule_sha256=reference_manifest["content_sha256"],
            attempt_number=1,
            offline_scripted=True,
        )
    else:
        repair = _load_object(repair_root / "repair_experiment_manifest.json")
    if (
        repair.get("initial_independent_decision") != "FAIL"
        or repair.get("independent_decision") != "PASS"
        or repair.get("strict_restoration") is not True
        or int(repair.get("repair_accepted_rounds") or 0) != 1
        or repair.get("external_model_api_calls") != 0
    ):
        raise ValueError("scripted artifact repair did not strictly restore the baseline")

    schedule_identity = canonical_sha256(
        {
            "formal_contract_sha256": sha256_file(FORMAL_CONTRACT),
            "controlled_reference_content_sha256": reference_manifest[
                "content_sha256"
            ],
            "upstream_run_summary_sha256": state["upstream_repaired"][
                "run_summary_sha256"
            ],
            "repair_manifest_sha256": repair["manifest_sha256"],
        }
    )
    registry = _temporary_registry_gate(root, schedule_identity)
    upstream_audit_after = sha256_file(
        Path(state["upstream_repaired"]["run_root"]) / "provider_calls.jsonl"
    )
    if upstream_audit_after != state["upstream_repaired"]["provider_audit_sha256"]:
        raise ValueError("resume duplicated an upstream provider call")
    final = {
        "schema_version": "atlas.autosar.v17.offline_full_context_e2e.v1",
        "decision": "PASS",
        "external_model_api_calls": 0,
        "generation_failure_preserved": True,
        "upstream_repair_strict_pass": True,
        "artifact_repair_strict_pass": True,
        "interrupt_resume_verified": True,
        "duplicate_upstream_provider_calls": 0,
        "upstream_provider_call_count": 3,
        "raw_provider_payload_sha256_by_scope": verified[
            "raw_provider_payload_sha256"
        ],
        "raw_provider_payload_count": 2,
        "raw_provider_schema_status": "PASS",
        "normalization_status": "NOT_APPLICABLE",
        "payload_final_atlas_status": "PASS",
        "controlled_reference_content_sha256": reference_manifest[
            "content_sha256"
        ],
        "repair_manifest_sha256": repair["manifest_sha256"],
        "schedule_content_sha256": schedule_identity,
        "registry_gate": registry,
        "formal_provider_registration": state["provider_registration"],
    }
    final["content_sha256"] = canonical_sha256(final)
    atomic_write_json(root / "offline_v17_e2e_manifest.json", final)
    completed_state = {
        **state,
        "stage": "COMPLETE",
        "offline_v17_e2e_content_sha256": final["content_sha256"],
        "updated_at_utc": utc_now(),
    }
    completed_state.pop("content_sha256", None)
    completed_state["content_sha256"] = canonical_sha256(completed_state)
    atomic_write_json(state_path, completed_state)
    return final, 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument(
        "--controlled-reference-manifest",
        type=Path,
        default=DEFAULT_REFERENCE_MANIFEST,
    )
    parser.add_argument("--stop-after-upstream", action="store_true")
    args = parser.parse_args()
    result, code = run(
        args.root,
        args.controlled_reference_manifest,
        stop_after_upstream=args.stop_after_upstream,
    )
    print(
        json.dumps(
            {
                "stage": result.get("stage", "COMPLETE"),
                "decision": result.get("decision"),
                "content_sha256": result.get("content_sha256"),
                "external_model_api_calls": 0,
            },
            indent=2,
        )
    )
    return code


if __name__ == "__main__":
    raise SystemExit(main())
