"""Run paper repair cohorts from a frozen ASW V3 generation experiment.

Natural failures and controlled mutations are scheduled separately. The script
does not inspect credentials; the single-run repair child owns its runtime.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from experiment_runtime import (
    atomic_write_json,
    atomic_write_text,
    child_state_path,
    exclusive_experiment_lock,
    recover_orphaned_child,
    reserve_attempt,
    run_child_process,
)
from repair_asw_v3_run import (
    CORE_MUTATIONS,
    MUTATIONS,
    SUBSTITUTE_MUTATIONS,
    _bundle_from_files,
    _load_frozen_typed_repair_context,
    apply_mutation,
)
from run_asw_v3_experiment import (
    SUCCESS_STATUSES as GENERATION_SUCCESS_STATUSES,
    TERMINAL_STATUSES as GENERATION_TERMINAL_STATUSES,
    _classify_failed_attempt,
    _locate_artifacts,
    _read_provider_call_audit,
    _read_json_object,
    _run_complete,
    verify_experiment_results,
    verify_schedule,
)


ROOT = Path(__file__).resolve().parent
REPAIR_RUNNER = ROOT / "repair_asw_v3_run.py"
COMPLETE_STATUSES = {"COMPLETE", "RESUMED_COMPLETE"}
TERMINAL_STATUSES = COMPLETE_STATUSES
CONTROLLED_CASE_IDS = (
    "ASW-MIN-01",
    "ASW-MIN-02",
    "ASW-MIN-03",
    "ASW-MIN-04",
    "ASW-MIN-05",
    "ASW-MIN-06",
    "ASW-STD-01",
    "ASW-STD-02",
    "ASW-STD-03",
    "ASW-STD-04",
    "ASW-STD-05",
    "ASW-STD-06",
    "ASW-STD-07",
    "ASW-FULL-01",
    "ASW-FULL-02",
    "ASW-FULL-03",
    "ASW-FULL-04",
    "ASW-FULL-05",
    "ASW-FULL-06",
    "ASW-FULL-07",
)
CONTROLLED_REPETITION = 1
CONTROLLED_MUTATIONS = tuple(item for item in CORE_MUTATIONS if item != "none")
CONTROLLED_SUBSTITUTE_MUTATIONS = tuple(SUBSTITUTE_MUTATIONS)
FORMAL_CONTRACT = ROOT / "FORMAL_EXPERIMENT_CONTRACT.json"
DEFAULT_CONTROLLED_REFERENCE_MANIFEST = (
    ROOT / "CONTROLLED_REFERENCE_BASELINES_V16_MANIFEST.json"
)


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_repair_baseline(
    record: dict[str, Any], *, controlled_mutations: tuple[str, ...] = ()
) -> dict[str, Any]:
    """Prove a scheduled baseline has exact typed state and mutation targets."""
    baseline_root = Path(str(record["run_root"])).resolve()
    summary_path = baseline_root / "run_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    system_name = str(summary.get("system_name") or "")
    if not system_name:
        raise ValueError("repair baseline has no system identity")
    component, interfaces, _validation = _locate_artifacts(
        baseline_root, system_name
    )
    bundle = _bundle_from_files(component, interfaces)
    context_path, context = _load_frozen_typed_repair_context(
        baseline_root, summary, bundle
    )
    checked_mutations: list[str] = []
    if controlled_mutations:
        for mutation in controlled_mutations:
            apply_mutation(bundle, mutation)
            checked_mutations.append(mutation)
    return {
        "baseline_run_summary_sha256": sha256_file(summary_path),
        "typed_repair_context_content_sha256": context["content_sha256"],
        "typed_repair_context_file_sha256": sha256_file(context_path),
        "controlled_mutation_targets_verified": checked_mutations,
    }


def verify_controlled_reference_manifest(path: Path) -> dict[str, Any]:
    path = path.resolve()
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != "atlas.asw_v3.all_requirements_offline_precheck.v2":
        raise ValueError("unsupported controlled reference manifest schema")
    unsigned = {
        key: value
        for key, value in manifest.items()
        if key not in {"content_sha256", "created_at_utc"}
    }
    if canonical_sha256(unsigned) != manifest.get("content_sha256"):
        raise ValueError("controlled reference manifest canonical hash mismatch")
    if manifest.get("decision") != "PASS":
        raise ValueError("controlled reference manifest is not PASS")
    references = manifest.get("reference_baselines") or {}
    if references.get("materialized") is not True or int(references.get("count") or 0) != 20:
        raise ValueError("controlled reference manifest lacks 20 materialized baselines")
    design = manifest.get("controlled_repair_design") or {}
    design_unsigned = {
        key: value for key, value in design.items() if key != "content_sha256"
    }
    if canonical_sha256(design_unsigned) != design.get("content_sha256"):
        raise ValueError("controlled repair design canonical hash mismatch")
    tasks = list(design.get("tasks") or [])
    if (
        int(design.get("scheduled_task_count") or 0) != 100
        or int(design.get("core_fixed_operator_task_count") or 0) != 85
        or int(design.get("substitution_task_count") or 0) != 15
        or len(tasks) != 100
    ):
        raise ValueError("controlled repair design is not the frozen 100/85/15 design")
    records = list(manifest.get("records") or [])
    if len(records) != 20 or len({item.get("case_id") for item in records}) != 20:
        raise ValueError("controlled reference records are incomplete or duplicated")
    for record in records:
        reference = record.get("deterministic_reference_baseline") or {}
        baseline_root = Path(str(reference.get("root") or "")).resolve()
        summary_path = baseline_root / "run_summary.json"
        independent_path = baseline_root / "independent_evaluation.json"
        if (
            reference.get("independent_decision") != "PASS"
            or not summary_path.is_file()
            or not independent_path.is_file()
            or sha256_file(summary_path) != reference.get("run_summary_sha256")
        ):
            raise ValueError(
                f"controlled reference baseline identity failed: {record.get('case_id')}"
            )
        independent = json.loads(independent_path.read_text(encoding="utf-8"))
        if independent.get("decision") != "PASS":
            raise ValueError(
                f"controlled reference is not independent PASS: {record.get('case_id')}"
            )
    return manifest


def build_schedule(
    results_path: Path,
    controlled_reference_manifest_path: Path = DEFAULT_CONTROLLED_REFERENCE_MANIFEST,
) -> dict[str, Any]:
    results_path = results_path.resolve()
    results = json.loads(results_path.read_text(encoding="utf-8"))
    verify_experiment_results(results)
    generation_schedule = verify_schedule(results.get("schedule") or {})
    records = list(results.get("records") or [])
    if len(records) != generation_schedule["pipeline_run_count"]:
        raise ValueError("repair requires the complete frozen generation cohort")
    scheduled_by_id = {
        item["run_id"]: item for item in generation_schedule["runs"]
    }
    if len(scheduled_by_id) != len(records):
        raise ValueError("generation result/run schedule cardinality mismatch")
    for record in records:
        scheduled_run = scheduled_by_id.get(record.get("run_id"))
        if (
            scheduled_run is None
            or record.get("status") not in GENERATION_TERMINAL_STATUSES
        ):
            raise ValueError("repair requires every frozen generation run to complete")
        if not _run_complete(
            Path(str(record["run_root"])),
            scheduled_run,
            generation_schedule,
            int(record["attempt_number"]),
        ):
            raise ValueError(
                f"generation baseline failed completion audit: {record.get('run_id')}"
            )
    contract = json.loads(FORMAL_CONTRACT.read_text(encoding="utf-8"))
    repair_contract = contract["repair_experiment"]
    if (
        tuple(repair_contract["controlled_case_ids"]) != CONTROLLED_CASE_IDS
        or int(repair_contract["controlled_repetition"])
        != CONTROLLED_REPETITION
        or tuple(repair_contract["controlled_mutations"])
        != CONTROLLED_MUTATIONS
        or tuple(repair_contract["controlled_substitute_mutations"])
        != CONTROLLED_SUBSTITUTE_MUTATIONS
        or int(repair_contract["controlled_design_cell_count"]) != 100
        or int(repair_contract["core_fixed_operator_task_count"]) != 85
        or int(repair_contract["substitution_task_count"]) != 15
    ):
        raise ValueError("repair implementation differs from formal contract")
    reference_path = controlled_reference_manifest_path.resolve()
    reference_manifest = verify_controlled_reference_manifest(reference_path)
    reference_design = reference_manifest["controlled_repair_design"]
    reference_records = {
        item["case_id"]: item for item in reference_manifest["records"]
    }
    design_case_ids = tuple(sorted({item["case_id"] for item in reference_design["tasks"]}))
    if design_case_ids != tuple(sorted(CONTROLLED_CASE_IDS)):
        raise ValueError("controlled reference cases differ from formal contract")
    scheduled: list[dict[str, Any]] = []
    ineligible: list[dict[str, Any]] = []

    for record in records:
        common = {
            "baseline_run_id": str(record["run_id"]),
            "model": str(record["model"]),
            "case_id": str(record["case_id"]),
            "repetition": int(record["repetition"]),
            "seed": int(record["seed"]),
            "baseline_root": str(Path(str(record["run_root"])).resolve()),
            "baseline_independent_decision": record.get("independent_decision"),
            "baseline_generation_status": record.get("status"),
        }
        if record.get("status") not in GENERATION_SUCCESS_STATUSES:
            ineligible.append(
                {
                    **common,
                    "cohort": "natural_failure",
                    "reason": "generation ended before a repairable ARXML artifact existed",
                }
            )
            continue
        if record.get("independent_decision") != "PASS":
            common.update(verify_repair_baseline(record))
            item = {**common, "cohort": "natural_failure", "mutation": "none"}
            item["run_id"] = (
                f"natural__{item['model']}__{item['case_id']}__R{item['repetition']}"
            )
            scheduled.append(item)

    provider_model = str(contract["generation"]["provider_registration"]["requested_model"])
    tasks_by_case: dict[str, list[dict[str, Any]]] = {}
    for task in reference_design["tasks"]:
        tasks_by_case.setdefault(str(task["case_id"]), []).append(task)
    for case_id in CONTROLLED_CASE_IDS:
        reference_record = reference_records[case_id]
        reference = reference_record["deterministic_reference_baseline"]
        effective_mutations = tuple(
            str(task["effective_mutation"])
            for task in sorted(tasks_by_case[case_id], key=lambda item: item["task_id"])
        )
        baseline_record = {"run_root": reference["root"]}
        baseline_audit = verify_repair_baseline(
            baseline_record, controlled_mutations=effective_mutations
        )
        if tuple(baseline_audit["controlled_mutation_targets_verified"]) != effective_mutations:
            raise ValueError(f"controlled reference mutation audit failed: {case_id}")
        common = {
            "baseline_run_id": f"reference__{case_id}",
            "model": provider_model,
            "case_id": case_id,
            "repetition": CONTROLLED_REPETITION,
            "seed": 104729,
            "baseline_root": str(Path(str(reference["root"])).resolve()),
            "baseline_independent_decision": "PASS",
            "baseline_generation_status": "DETERMINISTIC_REFERENCE_PASS",
            "reference_bundle_sha256": reference["bundle_sha256"],
            "reference_manifest_content_sha256": reference_manifest["content_sha256"],
            **baseline_audit,
        }
        for task in sorted(tasks_by_case[case_id], key=lambda item: item["task_id"]):
            mutation = str(task["effective_mutation"])
            item = {
                **common,
                "cohort": "controlled_mutation",
                "mutation": mutation,
                "design_task_id": task["task_id"],
                "base_operator": task["base_operator"],
                "applicability": task["applicability"],
                "analysis_layer": task["analysis_layer"],
                "case_sha256": task["case_sha256"],
            }
            item["run_id"] = (
                f"controlled__{provider_model}__{task['task_id']}__{mutation}"
            )
            scheduled.append(item)

    if len({item["run_id"] for item in scheduled}) != len(scheduled):
        raise ValueError("repair schedule contains duplicate run IDs")
    schedule: dict[str, Any] = {
        "schema_version": "atlas.asw_v3.repair_schedule.v3",
        "source_results": str(results_path),
        "source_results_file_sha256": sha256_file(results_path),
        "source_results_content_sha256": results.get("content_sha256"),
        "source_generation_schedule_sha256": generation_schedule["content_sha256"],
        "freeze_manifest_sha256": generation_schedule["freeze_manifest_sha256"],
        "experiment_contract_sha256": generation_schedule[
            "experiment_contract_sha256"
        ],
        "neo4j_context_sha256": generation_schedule["neo4j_context_sha256"],
        "controlled_case_ids": list(CONTROLLED_CASE_IDS),
        "controlled_repetition": CONTROLLED_REPETITION,
        "controlled_mutations": list(CONTROLLED_MUTATIONS),
        "controlled_substitute_mutations": list(CONTROLLED_SUBSTITUTE_MUTATIONS),
        "controlled_reference_manifest": str(reference_path),
        "controlled_reference_manifest_file_sha256": sha256_file(reference_path),
        "controlled_reference_manifest_content_sha256": reference_manifest[
            "content_sha256"
        ],
        "controlled_repair_design_sha256": reference_design["content_sha256"],
        "controlled_design_cell_count": 100,
        "controlled_core_fixed_operator_task_count": 85,
        "controlled_substitution_task_count": 15,
        "core_operator_denominators": reference_design[
            "core_repair_rate_denominators"
        ],
        "source_generation_run_count": len(records),
        "source_terminal_generation_failure_count": sum(
            item.get("status") not in GENERATION_SUCCESS_STATUSES
            for item in records
        ),
        "source_artifact_nonpass_count": sum(
            item.get("status") in GENERATION_SUCCESS_STATUSES
            and item.get("independent_decision") != "PASS"
            for item in records
        ),
        "natural_failure_count": sum(
            item["cohort"] == "natural_failure" for item in scheduled
        ),
        "controlled_baseline_count": len(
            {
                item["baseline_run_id"]
                for item in scheduled
                if item["cohort"] == "controlled_mutation"
            }
        ),
        "scheduled_count": len(scheduled),
        "ineligible_count": len(ineligible),
        "runs": sorted(scheduled, key=lambda item: item["run_id"]),
        "ineligible": sorted(
            ineligible,
            key=lambda item: (item["model"], item["case_id"], item["repetition"]),
        ),
    }
    schedule["content_sha256"] = canonical_sha256(schedule)
    return schedule


def verify_repair_schedule(schedule: dict[str, Any]) -> dict[str, Any]:
    unsigned = {
        key: value for key, value in schedule.items() if key != "content_sha256"
    }
    if canonical_sha256(unsigned) != schedule.get("content_sha256"):
        raise ValueError("repair schedule canonical hash mismatch")
    expected = build_schedule(
        Path(schedule["source_results"]),
        Path(schedule["controlled_reference_manifest"]),
    )
    if schedule != expected:
        raise ValueError("repair schedule differs from the frozen generation results")
    return schedule


def _write_completion_manifest(
    output_root: Path,
    item: dict[str, Any],
    schedule: dict[str, Any],
    attempt_number: int,
) -> dict[str, Any]:
    artifacts = {
        path.relative_to(output_root).as_posix(): sha256_file(path)
        for path in sorted(child for child in output_root.rglob("*") if child.is_file())
        if path.name != "repair_completion_manifest.json"
    }
    body = {
        "schema_version": "atlas.asw_v3.repair_completion.v2",
        "run_id": item["run_id"],
        "baseline_run_id": item["baseline_run_id"],
        "model": item["model"],
        "case_id": item["case_id"],
        "repetition": item["repetition"],
        "seed": item["seed"],
        "cohort": item["cohort"],
        "mutation": item["mutation"],
        "attempt_number": attempt_number,
        "completion_kind": "COMPLETED_REPAIR_EVALUATION",
        "terminal": True,
        "retryable": False,
        "repair_schedule_sha256": schedule["content_sha256"],
        "source_results_content_sha256": schedule[
            "source_results_content_sha256"
        ],
        "freeze_manifest_sha256": schedule["freeze_manifest_sha256"],
        "experiment_contract_sha256": schedule["experiment_contract_sha256"],
        "neo4j_context_sha256": schedule["neo4j_context_sha256"],
        "artifact_hashes": artifacts,
    }
    body["content_sha256"] = canonical_sha256(body)
    atomic_write_json(output_root / "repair_completion_manifest.json", body)
    return body


def _complete(
    output_root: Path,
    item: dict[str, Any],
    schedule: dict[str, Any],
    attempt_number: int,
) -> bool:
    completion_path = output_root / "repair_completion_manifest.json"
    if not completion_path.is_file():
        return False
    try:
        completion = json.loads(completion_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    unsigned = {
        key: value for key, value in completion.items() if key != "content_sha256"
    }
    if canonical_sha256(unsigned) != completion.get("content_sha256"):
        return False
    identities = {
        "run_id": item["run_id"],
        "baseline_run_id": item["baseline_run_id"],
        "model": item["model"],
        "case_id": item["case_id"],
        "repetition": item["repetition"],
        "seed": item["seed"],
        "cohort": item["cohort"],
        "mutation": item["mutation"],
        "attempt_number": attempt_number,
        "repair_schedule_sha256": schedule["content_sha256"],
        "source_results_content_sha256": schedule[
            "source_results_content_sha256"
        ],
        "freeze_manifest_sha256": schedule["freeze_manifest_sha256"],
        "experiment_contract_sha256": schedule["experiment_contract_sha256"],
        "neo4j_context_sha256": schedule["neo4j_context_sha256"],
    }
    if any(completion.get(key) != value for key, value in identities.items()):
        return False
    if completion.get("completion_kind", "COMPLETED_REPAIR_EVALUATION") != (
        "COMPLETED_REPAIR_EVALUATION"
    ):
        return False
    paths = (
        output_root / "repair_experiment_manifest.json",
        output_root / "independent_evaluation.json",
        output_root / "final_validation.json",
    )
    if not all(path.is_file() for path in paths):
        return False
    try:
        manifest = json.loads(paths[0].read_text(encoding="utf-8"))
        evaluation = json.loads(paths[1].read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    unsigned_manifest = {
        key: value for key, value in manifest.items() if key != "manifest_sha256"
    }
    if canonical_sha256(unsigned_manifest) != manifest.get("manifest_sha256"):
        return False
    outcome_values = {
        "resolved",
        "rejected_no_improvement",
        "rejected_regression",
        "rejected_malformed",
        "not_attempted",
    }
    boundary_reasons = manifest.get("automation_boundary_reason")
    if (
        manifest.get("schema_version") != "atlas.asw_v3.repair_experiment.v2"
        or manifest.get("case_id") != item["case_id"]
        or manifest.get("model") != item["model"]
        or manifest.get("seed") != item["seed"]
        or manifest.get("mutation") != item["mutation"]
        or manifest.get("repair_schedule_sha256") != schedule["content_sha256"]
        or manifest.get("attempt_number") != attempt_number
        or evaluation.get("case_id") != item["case_id"]
        or evaluation.get("decision") != manifest.get("independent_decision")
        or manifest.get("typed_repair_context_content_sha256")
        != item.get("typed_repair_context_content_sha256")
        or manifest.get("typed_repair_context_file_sha256")
        != item.get("typed_repair_context_file_sha256")
        or manifest.get("attempt_outcome") not in outcome_values
        or not isinstance(boundary_reasons, list)
        or not boundary_reasons
        or not isinstance(manifest.get("typed_repair_trace"), list)
        or (manifest.get("attempt_outcome") == "resolved")
        != (manifest.get("strict_restoration") is True)
        or (int(manifest.get("repair_attempted_rounds") or 0) > 0)
        != (manifest.get("repair_triggered") is True)
    ):
        return False
    expected_hashes = completion.get("artifact_hashes") or {}
    actual_files = {
        path.relative_to(output_root).as_posix()
        for path in output_root.rglob("*")
        if path.is_file() and path.name != "repair_completion_manifest.json"
    }
    if actual_files != set(expected_hashes):
        return False
    return all(
        sha256_file(output_root / relative) == expected
        for relative, expected in expected_hashes.items()
    )


def _record(
    output_root: Path,
    item: dict[str, Any],
    status: str,
    *,
    attempt_number: int,
    attempt_roots: list[Path],
) -> dict[str, Any]:
    manifest_path = output_root / "repair_experiment_manifest.json"
    manifest = _read_json_object(manifest_path)
    process_path = output_root / "repair_process.json"
    process = _read_json_object(process_path)
    completion = _read_json_object(output_root / "repair_completion_manifest.json")
    recorded_attempt_roots = attempt_roots or [output_root]
    provider_call_audit = [
        audit_item
        for attempt_root in recorded_attempt_roots
        for audit_item in _read_provider_call_audit(
            attempt_root / "provider_calls.jsonl"
        )
    ]
    return {
        **item,
        "status": status,
        "terminal": status in TERMINAL_STATUSES,
        "completion_kind": completion.get("completion_kind"),
        "output_root": str(output_root),
        "attempt_number": attempt_number,
        "attempts": [
            {
                "attempt_number": int(path.name.removeprefix("attempt-")),
                "output_root": str(path),
                "artifact_hashes": {
                    child.relative_to(path).as_posix(): sha256_file(child)
                    for child in sorted(
                        item for item in path.rglob("*") if item.is_file()
                    )
                },
            }
            for path in attempt_roots
        ],
        "initial_artifact_profile_decision": manifest.get(
            "initial_artifact_profile_decision"
        ),
        "initial_independent_decision": manifest.get(
            "initial_independent_decision"
        ),
        "final_artifact_profile_decision": manifest.get(
            "final_artifact_profile_decision"
        ),
        "independent_decision": manifest.get("independent_decision"),
        "strict_restoration": manifest.get("strict_restoration"),
        "exact_original_recovery": manifest.get("exact_original_recovery"),
        "repair_triggered": manifest.get("repair_triggered"),
        "repair_attempted_rounds": manifest.get("repair_attempted_rounds"),
        "repair_accepted_rounds": manifest.get("repair_accepted_rounds"),
        "repair_stop_reason": manifest.get("repair_stop_reason"),
        "attempt_outcome": manifest.get("attempt_outcome"),
        "automation_boundary_reason": manifest.get(
            "automation_boundary_reason"
        ),
        "repair_token_usage": manifest.get("repair_token_usage"),
        "provider_call_audit_count": len(provider_call_audit),
        "provider_audited_total_tokens": sum(
            int((audit_item.get("usage") or {}).get("total_tokens") or 0)
            for audit_item in provider_call_audit
        ),
        "provider_usage_complete": (
            status in TERMINAL_STATUSES
            and len(recorded_attempt_roots) == 1
            and (
                bool(provider_call_audit)
                or manifest.get("repair_triggered") is False
            )
        ),
        "repair_manifest_sha256": manifest.get("manifest_sha256"),
        "child_returncode": process.get("returncode"),
        "artifact_hashes": {
            path.relative_to(output_root).as_posix(): sha256_file(path)
            for path in sorted(
                child for child in output_root.rglob("*") if child.is_file()
            )
        },
    }


def _attempt_layout(output_base: Path) -> tuple[list[int], list[Path]]:
    output_base.mkdir(parents=True, exist_ok=True)
    invalid_entries = [
        path
        for path in output_base.iterdir()
        if not path.is_dir()
        or not path.name.startswith("attempt-")
        or not path.name.removeprefix("attempt-").isdigit()
    ]
    if invalid_entries:
        raise ValueError(
            f"repair attempt layout contains unexpected entries: {output_base}"
        )
    roots = sorted(
        output_base.iterdir(),
        key=lambda path: int(path.name.removeprefix("attempt-")),
    )
    numbers = [int(path.name.removeprefix("attempt-")) for path in roots]
    if numbers != list(range(1, len(roots) + 1)):
        raise ValueError(f"repair attempt numbers are not contiguous: {output_base}")
    return numbers, roots


def _required_repair_outputs(output_root: Path) -> bool:
    return all(
        (output_root / name).is_file()
        for name in (
            "repair_experiment_manifest.json",
            "independent_evaluation.json",
            "final_validation.json",
        )
    )


def _write_partial(
    experiment_root: Path,
    schedule: dict[str, Any],
    records: list[dict[str, Any]],
    queue_halt_reason: str | None,
) -> None:
    partial = {
        "schema_version": "atlas.asw_v3.repair_results.v2",
        "schedule_content_sha256": schedule["content_sha256"],
        "record_count": len(records),
        "queue_halt_reason": queue_halt_reason,
        "records": records,
    }
    partial["content_sha256"] = canonical_sha256(partial)
    atomic_write_json(experiment_root / "repair_results.partial.json", partial)


def run_schedule(
    schedule: dict[str, Any], experiment_root: Path, max_rounds: int, timeout_seconds: int
) -> dict[str, Any]:
    verify_repair_schedule(schedule)
    contract = json.loads(FORMAL_CONTRACT.read_text(encoding="utf-8"))
    expected_max_rounds = int(contract["repair_experiment"]["max_rounds"])
    if max_rounds != expected_max_rounds:
        raise ValueError("repair max rounds differs from formal experiment contract")
    max_attempts = int(
        contract["repair_experiment"]["max_pipeline_attempts_per_repair"]
    )
    experiment_root = experiment_root.resolve()
    with exclusive_experiment_lock(
        experiment_root, schedule_sha256=schedule["content_sha256"]
    ):
        schedule_path = experiment_root / "repair_schedule.json"
        schedule_text = (
            json.dumps(schedule, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        )
        if (
            schedule_path.exists()
            and schedule_path.read_text(encoding="utf-8") != schedule_text
        ):
            raise FileExistsError(
                "repair root is bound to a different immutable schedule"
            )
        if not schedule_path.exists():
            atomic_write_text(schedule_path, schedule_text)

        records: list[dict[str, Any]] = []
        queue_halt_reason = None
        for item in schedule["runs"]:
            output_base = (
                experiment_root
                / "runs"
                / item["cohort"]
                / item["model"]
                / item["case_id"]
                / f"R{item['repetition']}"
                / item["mutation"]
            )
            observed_numbers, attempt_roots = _attempt_layout(output_base)
            for attempt_number, attempt_root in zip(observed_numbers, attempt_roots):
                recovered = recover_orphaned_child(
                    child_state_path(
                        experiment_root, item["run_id"], attempt_number
                    )
                )
                if recovered and not _required_repair_outputs(attempt_root):
                    atomic_write_json(
                        attempt_root / "attempt_classification.json",
                        {
                            "status": "TRANSIENT_ORPHANED_CHILD_RECOVERED",
                            "terminal": False,
                            "retryable": True,
                            "queue_halt_reason": None,
                            "recovery": recovered,
                        },
                    )
            if len(attempt_roots) > max_attempts:
                raise ValueError(f"repair attempt budget exceeded: {item['run_id']}")
            complete_attempts = [
                (number, path)
                for number, path in zip(observed_numbers, attempt_roots)
                if _complete(path, item, schedule, number)
            ]
            if len(complete_attempts) > 1:
                raise ValueError(f"multiple terminal repair attempts: {item['run_id']}")
            if complete_attempts:
                attempt_number, output_root = complete_attempts[0]
                records.append(
                    _record(
                        output_root,
                        item,
                        "RESUMED_COMPLETE",
                        attempt_number=attempt_number,
                        attempt_roots=attempt_roots,
                    )
                )
                _write_partial(experiment_root, schedule, records, queue_halt_reason)
                continue

            # Complete an interrupted local post-processing step without a new call.
            if attempt_roots and _required_repair_outputs(attempt_roots[-1]):
                _write_completion_manifest(
                    attempt_roots[-1], item, schedule, observed_numbers[-1]
                )
                if not _complete(
                    attempt_roots[-1], item, schedule, observed_numbers[-1]
                ):
                    raise ValueError(
                        f"interrupted repair output failed audit: {item['run_id']}"
                    )
                records.append(
                    _record(
                        attempt_roots[-1],
                        item,
                        "RESUMED_COMPLETE",
                        attempt_number=observed_numbers[-1],
                        attempt_roots=attempt_roots,
                    )
                )
                _write_partial(experiment_root, schedule, records, queue_halt_reason)
                continue

            prior_classification = (
                _read_json_object(attempt_roots[-1] / "attempt_classification.json")
                if attempt_roots
                else {}
            )
            if prior_classification and not prior_classification.get("retryable"):
                queue_halt_reason = prior_classification.get("queue_halt_reason")
                records.append(
                    _record(
                        attempt_roots[-1],
                        item,
                        str(prior_classification.get("status") or "NOT_EVALUATED"),
                        attempt_number=observed_numbers[-1],
                        attempt_roots=attempt_roots,
                    )
                )
                _write_partial(experiment_root, schedule, records, queue_halt_reason)
                break

            status = "NOT_EVALUATED_ATTEMPTS_EXHAUSTED"
            output_root = attempt_roots[-1] if attempt_roots else output_base
            attempt_number = observed_numbers[-1] if observed_numbers else 0
            while len(attempt_roots) < max_attempts:
                attempt_number, output_root = reserve_attempt(
                    output_base, max_attempts
                )
                command = [
                    sys.executable,
                    "-B",
                    str(REPAIR_RUNNER),
                    "--baseline-root",
                    item["baseline_root"],
                    "--output-root",
                    str(output_root),
                    "--case-id",
                    item["case_id"],
                    "--model",
                    item["model"],
                    "--seed",
                    str(item["seed"]),
                    "--mutation",
                    item["mutation"],
                    "--max-rounds",
                    str(max_rounds),
                    "--generation-results",
                    schedule["source_results"],
                    "--controlled-reference-manifest",
                    schedule["controlled_reference_manifest"],
                    "--baseline-run-id",
                    item["baseline_run_id"],
                    "--repair-schedule-sha256",
                    schedule["content_sha256"],
                    "--attempt-number",
                    str(attempt_number),
                ]
                process = run_child_process(
                    command,
                    cwd=ROOT,
                    timeout_seconds=timeout_seconds,
                    # Outside the runs layout, as in the generation runner: the
                    # repair child also requires an empty output root.
                    state_path=child_state_path(
                        experiment_root, item["run_id"], attempt_number
                    ),
                )
                atomic_write_text(output_root / "repair.stdout.log", process.stdout)
                atomic_write_text(output_root / "repair.stderr.log", process.stderr)
                atomic_write_json(
                    output_root / "repair_process.json",
                    {
                        "returncode": process.returncode,
                        "timed_out": process.timed_out,
                        "termination": process.termination,
                    },
                )
                attempt_roots = [*attempt_roots, output_root]
                if _required_repair_outputs(output_root):
                    _write_completion_manifest(
                        output_root, item, schedule, attempt_number
                    )
                    if not _complete(output_root, item, schedule, attempt_number):
                        raise ValueError(
                            f"repair output failed completion audit: {item['run_id']}"
                        )
                    status = "COMPLETE"
                    break

                classification = _classify_failed_attempt(
                    process.stdout,
                    process.stderr,
                    {},
                    timed_out=process.timed_out,
                )
                atomic_write_json(
                    output_root / "attempt_classification.json", classification
                )
                queue_halt_reason = classification["queue_halt_reason"]
                if classification["retryable"]:
                    status = "TRANSIENT_REPAIR_INFRASTRUCTURE_FAILURE"
                    if len(attempt_roots) < max_attempts:
                        continue
                    status = "NOT_EVALUATED_ATTEMPTS_EXHAUSTED"
                    queue_halt_reason = "TRANSIENT_ATTEMPTS_EXHAUSTED"
                    break
                if queue_halt_reason is not None:
                    status = str(classification["status"])
                    break
                raise RuntimeError("repair failure classification is incomplete")

            if status == "NOT_EVALUATED_ATTEMPTS_EXHAUSTED":
                queue_halt_reason = "TRANSIENT_ATTEMPTS_EXHAUSTED"
            records.append(
                _record(
                    output_root,
                    item,
                    status,
                    attempt_number=attempt_number,
                    attempt_roots=attempt_roots,
                )
            )
            _write_partial(experiment_root, schedule, records, queue_halt_reason)
            if queue_halt_reason is not None:
                break

        experiment_complete = (
            len(records) == schedule["scheduled_count"]
            and all(item["status"] in TERMINAL_STATUSES for item in records)
        )
        result = {
            "schema_version": "atlas.asw_v3.repair_results.v2",
            "schedule": schedule,
            "experiment_complete": experiment_complete,
            "record_count": len(records),
            "status_counts": dict(Counter(item["status"] for item in records)),
            "queue_halt_reason": queue_halt_reason,
            "records": records,
        }
        result["content_sha256"] = canonical_sha256(result)
        _write_partial(experiment_root, schedule, records, queue_halt_reason)
        if experiment_complete:
            atomic_write_json(experiment_root / "repair_results.json", result)
        return result


def verify_repair_results(results: dict[str, Any]) -> dict[str, Any]:
    """Verify repair result identity and every claimed complete repair."""

    unsigned = {
        key: value for key, value in results.items() if key != "content_sha256"
    }
    if canonical_sha256(unsigned) != results.get("content_sha256"):
        raise ValueError("repair results canonical hash mismatch")
    schedule = verify_repair_schedule(results.get("schedule") or {})
    if results.get("experiment_complete") is not True:
        raise ValueError("formal repair results are not complete")
    records = list(results.get("records") or [])
    if len(records) != schedule["scheduled_count"]:
        raise ValueError("repair result count differs from repair schedule")
    scheduled_by_id = {item["run_id"]: item for item in schedule["runs"]}
    if len(scheduled_by_id) != len(records):
        raise ValueError("repair results contain duplicate or missing run IDs")
    observed_ids: set[str] = set()
    for record in records:
        run_id = str(record.get("run_id") or "")
        scheduled = scheduled_by_id.get(run_id)
        if scheduled is None or run_id in observed_ids:
            raise ValueError(f"repair result run identity is invalid: {run_id}")
        observed_ids.add(run_id)
        for key in (
            "baseline_run_id", "model", "case_id", "repetition", "seed",
            "cohort", "mutation",
        ):
            if record.get(key) != scheduled.get(key):
                raise ValueError(f"repair result identity mismatch: {run_id}/{key}")
        if record.get("status") not in TERMINAL_STATUSES:
            raise ValueError(f"repair observation is not terminal: {run_id}")
        if not _complete(
            Path(str(record["output_root"])),
            scheduled,
            schedule,
            int(record["attempt_number"]),
        ):
            raise ValueError(f"completed repair run failed audit: {run_id}")
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generation-results", type=Path, required=True)
    parser.add_argument(
        "--controlled-reference-manifest",
        type=Path,
        default=DEFAULT_CONTROLLED_REFERENCE_MANIFEST,
    )
    parser.add_argument("--experiment-root", type=Path)
    parser.add_argument("--max-rounds", type=int, default=2)
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    schedule = build_schedule(
        args.generation_results, args.controlled_reference_manifest
    )
    if args.dry_run:
        print(
            json.dumps(
                {
                    "scheduled_count": schedule["scheduled_count"],
                    "ineligible_count": schedule["ineligible_count"],
                    "cohort_counts": dict(
                        Counter(item["cohort"] for item in schedule["runs"])
                    ),
                    "content_sha256": schedule["content_sha256"],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    if args.experiment_root is None:
        parser.error("--experiment-root is required unless --dry-run is used")
    result = run_schedule(
        schedule, args.experiment_root, args.max_rounds, args.timeout_seconds
    )
    print(
        json.dumps(
            {
                "record_count": result["record_count"],
                "status_counts": result["status_counts"],
                "content_sha256": result["content_sha256"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if result["experiment_complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
