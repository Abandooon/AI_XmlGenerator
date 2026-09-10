"""Finalize a completed V17 run through an append-only post-run registry.

The paid runner froze the repository registry while it still said NOT_RUN, but
its paper gate required CURRENT_FORMAL_RESULT after the provider and repair
phases had completed.  Mutating the frozen registry in place would destroy the
as-executed identity.  This corrigendum therefore preserves that file byte for
byte, verifies the completed results against the original freeze, and creates a
result-root registry that activates only the exact verified result identity.

This module has no provider client and performs no external model calls.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import uuid
from collections import Counter
from pathlib import Path
from typing import Any

from evidence_registry_gate import ATLAS_ROOT
from experiment_freeze import canonical_sha256, verify_freeze_manifest
from experiment_runtime import atomic_write_json, atomic_write_text, utc_now
from run_asw_v3_experiment import verify_experiment_results, verify_schedule
from run_asw_v3_full_experiment import _write_state
from run_asw_v3_repair_experiment import verify_repair_results
from summarize_asw_v3_experiment import markdown as generation_markdown
from summarize_asw_v3_experiment import summarize as summarize_generation
from summarize_asw_v3_repair import summarize as summarize_repair


ROOT = Path(__file__).resolve().parent
PRE_RUN_REGISTRY = ATLAS_ROOT / "config" / "atlas_experiment_registry.json"
IDENTITY_SOURCES = {
    "LOCAL_PIPELINE_ACCEPTANCE_MANIFEST.json": ROOT
    / "LOCAL_PIPELINE_ACCEPTANCE_MANIFEST.json",
    "PAPER_ARTIFACT_FREEZE_MANIFEST.json": ROOT
    / "PAPER_ARTIFACT_FREEZE_MANIFEST.json",
    "FORMAL_EXPERIMENT_SCHEDULE_V17.json": ROOT
    / "FORMAL_EXPERIMENT_SCHEDULE_V17.json",
    "FORMAL_HELDOUT_V3_EXPERIMENT_SCHEDULE_V17.json": ROOT
    / "FORMAL_HELDOUT_V3_EXPERIMENT_SCHEDULE_V17.json",
    "FORMAL_EXPERIMENT_CONTRACT.json": ROOT / "FORMAL_EXPERIMENT_CONTRACT.json",
    "FORMAL_NEO4J_CONTEXT.json": ROOT / "FORMAL_NEO4J_CONTEXT.json",
    "PRE_RUN_REGISTRY_SNAPSHOT.json": PRE_RUN_REGISTRY,
}
EXPECTED_PRIMARY_SCHEDULE = (
    "203da038bcda33529dc813342bb63ca3b3deac7233c66d85cbe61cd80944345f"
)
RESULT_ID = "E1-V17-PRIMARY-203da038"
CORRECTION_SCHEMA = "atlas.autosar.v17.post_run_registry_corrigendum.v1"
REGISTRY_SCHEMA = "atlas.experiment_registry.post_run_activation.v1"


class CorrigendumError(RuntimeError):
    """Raised when post-run activation cannot be proven safe."""


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CorrigendumError(f"invalid JSON object: {path}") from error
    if not isinstance(value, dict):
        raise CorrigendumError(f"JSON root is not an object: {path}")
    return value


def _verify_content_hash(value: dict[str, Any], field: str) -> None:
    claimed = value.get(field)
    unsigned = {key: item for key, item in value.items() if key != field}
    if canonical_sha256(unsigned) != claimed:
        raise CorrigendumError(f"canonical hash mismatch: {field}")


def _atomic_copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{uuid.uuid4().hex}.tmp")
    try:
        shutil.copyfile(source, temporary)
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def _assert_quiescent(experiment_root: Path) -> None:
    forbidden = [
        experiment_root / ".atlas-full-experiment.lock",
        experiment_root / "generation" / ".atlas-experiment.lock",
        experiment_root / "repair" / ".atlas-experiment.lock",
        experiment_root / "OPERATOR_STOP_REQUESTED",
        experiment_root / "generation" / "OPERATOR_STOP_REQUESTED",
    ]
    present = [str(path) for path in forbidden if path.exists()]
    if present:
        raise CorrigendumError("run is not quiescent: " + ", ".join(present))


def _verify_pre_run_identity() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    acceptance = _load_object(ROOT / "LOCAL_PIPELINE_ACCEPTANCE_MANIFEST.json")
    _verify_content_hash(acceptance, "manifest_content_sha256")
    if canonical_sha256(acceptance.get("evidence") or {}) != acceptance.get(
        "acceptance_fingerprint_sha256"
    ):
        raise CorrigendumError("acceptance fingerprint mismatch")
    if acceptance.get("decision") != "LOCAL_CHAIN_ACCEPTED_FAIL_CLOSED":
        raise CorrigendumError("local acceptance is not fail-closed PASS")
    freeze = verify_freeze_manifest(ROOT / "PAPER_ARTIFACT_FREEZE_MANIFEST.json")
    schedule = verify_schedule(
        _load_object(ROOT / "FORMAL_EXPERIMENT_SCHEDULE_V17.json")
    )
    if schedule.get("content_sha256") != EXPECTED_PRIMARY_SCHEDULE:
        raise CorrigendumError("unexpected primary schedule identity")
    registry = _load_object(PRE_RUN_REGISTRY)
    autosar = ((registry.get("experiments") or {}).get("autosar") or {})
    if (
        autosar.get("active_result_status") != "NOT_RUN"
        or autosar.get("active_schedule_sha256") is not None
    ):
        raise CorrigendumError("pre-run registry is not the frozen NOT_RUN state")
    return acceptance, freeze, schedule


def _verify_paid_results(
    experiment_root: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    state = _load_object(experiment_root / "full_experiment_state.json")
    if state.get("stage") not in {"SUMMARIZING", "COMPLETE"}:
        raise CorrigendumError("paid runner did not reach the post-result boundary")
    generation_path = experiment_root / "generation" / "experiment_results.json"
    repair_path = experiment_root / "repair" / "repair_results.json"
    generation = _load_object(generation_path)
    repair = _load_object(repair_path)
    verify_experiment_results(generation)
    verify_repair_results(repair)
    if generation.get("record_count") != 60 or not generation.get(
        "experiment_complete"
    ):
        raise CorrigendumError("generation result is not a complete 60-slot cohort")
    if repair.get("record_count") != 102 or not repair.get("experiment_complete"):
        raise CorrigendumError("repair result is not the complete 102-record cohort")
    generation_summary = summarize_generation(generation)
    repair_summary = summarize_repair(repair)
    return generation, repair, generation_summary, repair_summary


def _activation_registry(
    experiment_root: Path,
    generation: dict[str, Any],
    repair: dict[str, Any],
    freeze: dict[str, Any],
    pre_run_registry_file_sha256: str,
) -> dict[str, Any]:
    source = _load_object(PRE_RUN_REGISTRY)
    registry = json.loads(json.dumps(source, ensure_ascii=False))
    registry["activation_schema_version"] = REGISTRY_SCHEMA
    policy = registry["policy"]
    policy["notes"] = (
        str(policy.get("notes") or "")
        + " Post-run activation is append-only and root-scoped because the frozen "
        "pre-run registry had to remain NOT_RUN while the paper gate required "
        "CURRENT_FORMAL_RESULT after execution."
    )
    autosar = registry["experiments"]["autosar"]
    autosar.update(
        {
            "active_code_line": "V17-formal",
            "active_result_status": "CURRENT_FORMAL_RESULT",
            "active_result_id": RESULT_ID,
            "active_schedule_sha256": generation["schedule"]["content_sha256"],
            "active_result_root": str(experiment_root),
            "active_freeze_manifest_sha256": freeze["manifest_sha256"],
            "active_generation_results_content_sha256": generation[
                "content_sha256"
            ],
            "active_generation_results_file_sha256": sha256_file(
                experiment_root / "generation" / "experiment_results.json"
            ),
            "active_repair_results_content_sha256": repair["content_sha256"],
            "active_repair_results_file_sha256": sha256_file(
                experiment_root / "repair" / "repair_results.json"
            ),
            "activation_model": "append_only_post_run_corrigendum_v1",
            "pre_run_registry_file_sha256": pre_run_registry_file_sha256,
            "provider_calls_by_activation": 0,
            "ui_default": True,
        }
    )
    registry["registry_content_sha256"] = canonical_sha256(registry)
    return registry


def _corrigendum_markdown(receipt: dict[str, Any]) -> str:
    generation = receipt["generation"]
    repair = receipt["repair"]
    return "\n".join(
        [
            "# ATLAS V17 post-run registry activation corrigendum",
            "",
            "The paid generation and repair phases completed before the original",
            "runner reached its paper-summary gate. The frozen repository registry",
            "correctly still said `NOT_RUN`, while that gate required",
            "`CURRENT_FORMAL_RESULT`. The gate ordering therefore blocked only",
            "post-processing; it did not interrupt or alter a provider call.",
            "",
            "This corrigendum preserves the complete pre-run registry byte for byte",
            "and activates only the exact result identities recorded below. It does",
            "not alter the model, prompts, schemas, cohort, estimand, scoring, or any",
            "provider output.",
            "",
            f"- Result ID: `{receipt['result_id']}`",
            f"- Schedule: `{receipt['schedule_content_sha256']}`",
            f"- Freeze: `{receipt['freeze_manifest_sha256']}`",
            f"- Generation: `{generation['content_sha256']}` ({generation['records']} records)",
            f"- Repair: `{repair['content_sha256']}` ({repair['records']} records)",
            f"- Calls made by corrigendum: `{receipt['external_model_api_calls']}`",
            "",
        ]
    )


def finalize(experiment_root: Path) -> dict[str, Any]:
    experiment_root = experiment_root.resolve()
    _assert_quiescent(experiment_root)
    if (experiment_root / "full_experiment_manifest.json").exists():
        return verify_finalization(experiment_root)
    acceptance, freeze, schedule = _verify_pre_run_identity()
    generation, repair, generation_summary, repair_summary = _verify_paid_results(
        experiment_root
    )
    correction_root = experiment_root / "post_run_correction"
    identity_root = correction_root / "as_executed_identity"
    for name, source in IDENTITY_SOURCES.items():
        _atomic_copy(source, identity_root / name)
    identity_hashes = {
        path.relative_to(correction_root).as_posix(): sha256_file(path)
        for path in sorted(identity_root.iterdir())
        if path.is_file()
    }
    pre_registry_hash = identity_hashes[
        "as_executed_identity/PRE_RUN_REGISTRY_SNAPSHOT.json"
    ]
    if pre_registry_hash != sha256_file(PRE_RUN_REGISTRY):
        raise CorrigendumError("pre-run registry snapshot is not byte-identical")
    registry = _activation_registry(
        experiment_root, generation, repair, freeze, pre_registry_hash
    )
    registry_path = correction_root / "POST_RUN_RESULT_REGISTRY.json"
    atomic_write_json(registry_path, registry)

    if str(ATLAS_ROOT) not in sys.path:
        sys.path.insert(0, str(ATLAS_ROOT))
    from src.workbench.artifacts import assert_latest_autosar_identity

    registry_gate = assert_latest_autosar_identity(
        {"schedule_content_sha256": schedule["content_sha256"]},
        purpose="paper_primary",
        registry_path=registry_path,
    )
    generation_records = list(generation.get("records") or [])
    repair_records = list(repair.get("records") or [])
    activation_at = utc_now()
    receipt = {
        "schema_version": CORRECTION_SCHEMA,
        "activation_at_utc": activation_at,
        "activation_decision": "CURRENT_FORMAL_RESULT",
        "result_id": RESULT_ID,
        "result_root": str(experiment_root),
        "registry_gate": registry_gate,
        "acceptance_content_sha256": acceptance["manifest_content_sha256"],
        "acceptance_fingerprint_sha256": acceptance[
            "acceptance_fingerprint_sha256"
        ],
        "freeze_manifest_file_sha256": freeze["manifest_file_sha256"],
        "freeze_manifest_sha256": freeze["manifest_sha256"],
        "schedule_content_sha256": schedule["content_sha256"],
        "experiment_contract_file_sha256": freeze["experiment_contract_sha256"],
        "neo4j_context_sha256": freeze["neo4j_context_sha256"],
        "pre_run_registry_file_sha256": pre_registry_hash,
        "post_run_registry_file_sha256": sha256_file(registry_path),
        "post_run_registry_content_sha256": registry[
            "registry_content_sha256"
        ],
        "generation": {
            "file_sha256": sha256_file(
                experiment_root / "generation" / "experiment_results.json"
            ),
            "content_sha256": generation["content_sha256"],
            "records": len(generation_records),
            "status_counts": dict(
                sorted(Counter(item.get("status") for item in generation_records).items())
            ),
            "independent_passes": sum(
                item.get("independent_decision") == "PASS"
                for item in generation_records
            ),
            "summary_content_sha256": generation_summary["content_sha256"],
        },
        "repair": {
            "file_sha256": sha256_file(
                experiment_root / "repair" / "repair_results.json"
            ),
            "content_sha256": repair["content_sha256"],
            "records": len(repair_records),
            "cohort_counts": dict(
                sorted(Counter(item.get("cohort") for item in repair_records).items())
            ),
            "summary_content_sha256": repair_summary["content_sha256"],
        },
        "as_executed_identity_file_hashes": identity_hashes,
        "gate_defect": {
            "blocked_stage": "SUMMARIZING",
            "exception_type": "WorkbenchArtifactError",
            "message": "no current V17 formal result is registered for paper/promotion",
            "cause": (
                "the pre-run registry was freeze-bound as NOT_RUN while the post-run "
                "paper gate required CURRENT_FORMAL_RESULT"
            ),
            "provider_phase_affected": False,
        },
        "methodology_changes": [],
        "external_model_api_calls": 0,
        "heldout_execution": False,
    }
    receipt["content_sha256"] = canonical_sha256(receipt)
    receipt_path = correction_root / "POST_RUN_ACTIVATION_RECEIPT.json"
    atomic_write_json(receipt_path, receipt)
    report_path = correction_root / "POST_RUN_REGISTRY_ACTIVATION_CORRIGENDUM.md"
    atomic_write_text(report_path, _corrigendum_markdown(receipt))

    paper_root = experiment_root / "paper"
    generation_summary_path = paper_root / "generation_summary.json"
    generation_markdown_path = paper_root / "generation_summary.md"
    repair_summary_path = paper_root / "repair_summary.json"
    atomic_write_json(generation_summary_path, generation_summary)
    atomic_write_text(generation_markdown_path, generation_markdown(generation_summary))
    atomic_write_json(repair_summary_path, repair_summary)

    artifact_paths = {
        "formal_experiment_schedule.json": experiment_root
        / "formal_experiment_schedule.json",
        "generation/experiment_results.json": experiment_root
        / "generation"
        / "experiment_results.json",
        "repair/repair_results.json": experiment_root
        / "repair"
        / "repair_results.json",
        "paper/generation_summary.json": generation_summary_path,
        "paper/generation_summary.md": generation_markdown_path,
        "paper/repair_summary.json": repair_summary_path,
        "post_run_correction/POST_RUN_RESULT_REGISTRY.json": registry_path,
        "post_run_correction/POST_RUN_ACTIVATION_RECEIPT.json": receipt_path,
        "post_run_correction/POST_RUN_REGISTRY_ACTIVATION_CORRIGENDUM.md": report_path,
    }
    for relative in identity_hashes:
        artifact_paths[f"post_run_correction/{relative}"] = correction_root / relative
    artifacts = {
        relative: sha256_file(path) for relative, path in sorted(artifact_paths.items())
    }
    result = {
        "schema_version": "atlas.asw_v3.full_experiment.v1",
        "experiment_complete": True,
        "completion_mode": "post_run_registry_activation_corrigendum_v1",
        "schedule_content_sha256": schedule["content_sha256"],
        "generation_results_content_sha256": generation["content_sha256"],
        "repair_results_content_sha256": repair["content_sha256"],
        "generation_summary_content_sha256": generation_summary["content_sha256"],
        "repair_summary_content_sha256": repair_summary["content_sha256"],
        "post_run_activation_receipt_content_sha256": receipt["content_sha256"],
        "post_run_registry_content_sha256": registry["registry_content_sha256"],
        "registry_gate": registry_gate,
        "completed_at_utc": activation_at,
        "artifact_hashes": artifacts,
    }
    result["content_sha256"] = canonical_sha256(result)
    atomic_write_json(experiment_root / "full_experiment_manifest.json", result)
    _write_state(
        experiment_root,
        schedule,
        "COMPLETE",
        full_experiment_content_sha256=result["content_sha256"],
        completion_mode=result["completion_mode"],
        post_run_activation_receipt_content_sha256=receipt["content_sha256"],
    )
    return verify_finalization(experiment_root)


def verify_finalization(experiment_root: Path) -> dict[str, Any]:
    experiment_root = experiment_root.resolve()
    _assert_quiescent(experiment_root)
    acceptance, freeze, schedule = _verify_pre_run_identity()
    generation, repair, expected_generation_summary, expected_repair_summary = (
        _verify_paid_results(experiment_root)
    )
    correction_root = experiment_root / "post_run_correction"
    registry_path = correction_root / "POST_RUN_RESULT_REGISTRY.json"
    receipt_path = correction_root / "POST_RUN_ACTIVATION_RECEIPT.json"
    registry = _load_object(registry_path)
    _verify_content_hash(registry, "registry_content_sha256")
    receipt = _load_object(receipt_path)
    _verify_content_hash(receipt, "content_sha256")
    if receipt.get("external_model_api_calls") != 0:
        raise CorrigendumError("corrigendum claims external model calls")
    if receipt.get("schedule_content_sha256") != schedule["content_sha256"]:
        raise CorrigendumError("activation receipt schedule mismatch")
    if receipt.get("freeze_manifest_sha256") != freeze["manifest_sha256"]:
        raise CorrigendumError("activation receipt freeze mismatch")
    if receipt.get("acceptance_content_sha256") != acceptance[
        "manifest_content_sha256"
    ]:
        raise CorrigendumError("activation receipt acceptance mismatch")
    if receipt["generation"]["content_sha256"] != generation["content_sha256"]:
        raise CorrigendumError("activation receipt generation mismatch")
    if receipt["repair"]["content_sha256"] != repair["content_sha256"]:
        raise CorrigendumError("activation receipt repair mismatch")
    if sha256_file(PRE_RUN_REGISTRY) != receipt.get(
        "pre_run_registry_file_sha256"
    ):
        raise CorrigendumError("live pre-run registry no longer matches its snapshot")
    if str(ATLAS_ROOT) not in sys.path:
        sys.path.insert(0, str(ATLAS_ROOT))
    from src.workbench.artifacts import assert_latest_autosar_identity

    gate = assert_latest_autosar_identity(
        {"schedule_content_sha256": schedule["content_sha256"]},
        purpose="paper_primary",
        registry_path=registry_path,
    )
    if gate != receipt.get("registry_gate"):
        raise CorrigendumError("activation registry gate receipt mismatch")
    generation_summary = _load_object(
        experiment_root / "paper" / "generation_summary.json"
    )
    repair_summary = _load_object(experiment_root / "paper" / "repair_summary.json")
    _verify_content_hash(generation_summary, "content_sha256")
    _verify_content_hash(repair_summary, "content_sha256")
    if generation_summary.get("content_sha256") != expected_generation_summary.get(
        "content_sha256"
    ):
        raise CorrigendumError("generation summary is not deterministic")
    if repair_summary.get("content_sha256") != expected_repair_summary.get(
        "content_sha256"
    ):
        raise CorrigendumError("repair summary is not deterministic")
    manifest = _load_object(experiment_root / "full_experiment_manifest.json")
    _verify_content_hash(manifest, "content_sha256")
    if (
        manifest.get("experiment_complete") is not True
        or manifest.get("completion_mode")
        != "post_run_registry_activation_corrigendum_v1"
        or manifest.get("schedule_content_sha256") != schedule["content_sha256"]
        or manifest.get("generation_results_content_sha256")
        != generation["content_sha256"]
        or manifest.get("repair_results_content_sha256") != repair["content_sha256"]
        or manifest.get("post_run_activation_receipt_content_sha256")
        != receipt["content_sha256"]
    ):
        raise CorrigendumError("full manifest identity is incomplete")
    for relative, expected in (manifest.get("artifact_hashes") or {}).items():
        path = (experiment_root / relative).resolve()
        try:
            path.relative_to(experiment_root)
        except ValueError as error:
            raise CorrigendumError(f"manifest path escapes root: {relative}") from error
        if not path.is_file() or sha256_file(path) != expected:
            raise CorrigendumError(f"full manifest artifact mismatch: {relative}")
    state = _load_object(experiment_root / "full_experiment_state.json")
    if (
        state.get("stage") != "COMPLETE"
        or state.get("full_experiment_content_sha256") != manifest["content_sha256"]
    ):
        raise CorrigendumError("full experiment state is not COMPLETE")
    model = generation_summary["models"]["gpt-5.6-luna"]
    return {
        "decision": "PASS",
        "result_id": RESULT_ID,
        "result_root": str(experiment_root),
        "schedule_content_sha256": schedule["content_sha256"],
        "generation_results_content_sha256": generation["content_sha256"],
        "repair_results_content_sha256": repair["content_sha256"],
        "generation_summary_content_sha256": generation_summary["content_sha256"],
        "repair_summary_content_sha256": repair_summary["content_sha256"],
        "activation_receipt_content_sha256": receipt["content_sha256"],
        "post_run_registry_content_sha256": registry["registry_content_sha256"],
        "full_experiment_content_sha256": manifest["content_sha256"],
        "scheduled_runs": model["scheduled_runs"],
        "independent_passes": model["independent_passes"],
        "repair_records": repair["record_count"],
        "external_model_api_calls_by_corrigendum": 0,
        "heldout_execution": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment-root", type=Path, required=True)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    result = (
        verify_finalization(args.experiment_root)
        if args.verify_only
        else finalize(args.experiment_root)
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
