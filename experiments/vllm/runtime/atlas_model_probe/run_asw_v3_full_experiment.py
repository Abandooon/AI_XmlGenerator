"""Run the frozen AUTOSAR generation, repair, and summary stages once.

The command is resumable.  A rerun first verifies and reuses durable terminal
observations; it never treats a partial result snapshot as a final cohort.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from experiment_runtime import (
    atomic_write_json,
    atomic_write_text,
    exclusive_experiment_lock,
    utc_now,
)
from run_asw_v3_experiment import (
    build_schedule,
    canonical_sha256,
    formal_models,
    run_experiment,
    sha256_file,
    verify_experiment_results,
    verify_schedule,
)
from experiment_freeze import DEFAULT_FREEZE_MANIFEST
from run_asw_v3_repair_experiment import (
    DEFAULT_CONTROLLED_REFERENCE_MANIFEST,
    build_schedule as build_repair_schedule,
    run_schedule as run_repair_schedule,
    verify_controlled_reference_manifest,
    verify_repair_results,
)
from summarize_asw_v3_experiment import markdown as generation_markdown
from summarize_asw_v3_experiment import summarize as summarize_generation
from summarize_asw_v3_repair import summarize as summarize_repair


FORMAL_CONTRACT = Path(__file__).resolve().parent / "FORMAL_EXPERIMENT_CONTRACT.json"


def _write_state(
    experiment_root: Path,
    schedule: dict[str, Any],
    stage: str,
    **details: Any,
) -> None:
    state = {
        "schema_version": "atlas.asw_v3.full_experiment_state.v1",
        "schedule_content_sha256": schedule["content_sha256"],
        "stage": stage,
        "updated_at_utc": utc_now(),
        **details,
    }
    state["content_sha256"] = canonical_sha256(state)
    atomic_write_json(experiment_root / "full_experiment_state.json", state)


def run_full_experiment(
    schedule: dict[str, Any],
    experiment_root: Path,
    *,
    generation_timeout_seconds: int,
    repair_timeout_seconds: int,
    repair_max_rounds: int,
    controlled_reference_manifest: Path = DEFAULT_CONTROLLED_REFERENCE_MANIFEST,
) -> dict[str, Any]:
    verify_schedule(schedule)
    contract = json.loads(FORMAL_CONTRACT.read_text(encoding="utf-8"))
    generation_contract = contract["generation"]
    orchestration = generation_contract["orchestration"]
    expected_generation_timeout = int(
        orchestration["generation_child_hard_timeout_seconds"]
    )
    expected_repair_timeout = int(
        orchestration["repair_child_hard_timeout_seconds"]
    )
    expected_repair_rounds = int(
        contract["repair_experiment"]["max_rounds"]
    )
    if int(generation_timeout_seconds) != expected_generation_timeout:
        raise ValueError("generation timeout differs from the frozen contract")
    if int(repair_timeout_seconds) != expected_repair_timeout:
        raise ValueError("repair timeout differs from the frozen contract")
    if int(repair_max_rounds) != expected_repair_rounds:
        raise ValueError("repair round count differs from the frozen contract")
    experiment_root = experiment_root.resolve()
    with exclusive_experiment_lock(
        experiment_root,
        schedule_sha256=schedule["content_sha256"],
        lock_name=".atlas-full-experiment.lock",
    ):
        top_schedule_path = experiment_root / "formal_experiment_schedule.json"
        schedule_text = (
            json.dumps(schedule, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        )
        if (
            top_schedule_path.exists()
            and top_schedule_path.read_text(encoding="utf-8") != schedule_text
        ):
            raise FileExistsError(
                "full experiment root is bound to a different schedule"
            )
        if not top_schedule_path.exists():
            atomic_write_text(top_schedule_path, schedule_text)
        _write_state(experiment_root, schedule, "GENERATION_RUNNING")
        generation_root = experiment_root / "generation"
        generation = run_experiment(
            schedule,
            generation_root,
            generation_timeout_seconds,
            additional_operator_stop_roots=(experiment_root,),
        )
        if not generation.get("experiment_complete"):
            stopped_by_operator = generation.get("operator_stop") is not None
            _write_state(
                experiment_root,
                schedule,
                (
                    "GENERATION_STOPPED_BY_OPERATOR"
                    if stopped_by_operator
                    else "GENERATION_BLOCKED"
                ),
                record_count=generation.get("record_count"),
                queue_halt_reason=generation.get("queue_halt_reason"),
            )
            return {
                "experiment_complete": False,
                "stage": (
                    "GENERATION_STOPPED_BY_OPERATOR"
                    if stopped_by_operator
                    else "GENERATION_BLOCKED"
                ),
                "generation": generation,
            }
        generation_results_path = generation_root / "experiment_results.json"
        verify_experiment_results(
            json.loads(generation_results_path.read_text(encoding="utf-8"))
        )

        _write_state(experiment_root, schedule, "REPAIR_RUNNING")
        repair_schedule = build_repair_schedule(
            generation_results_path, controlled_reference_manifest
        )
        repair_root = experiment_root / "repair"
        repair = run_repair_schedule(
            repair_schedule,
            repair_root,
            repair_max_rounds,
            repair_timeout_seconds,
        )
        if not repair.get("experiment_complete"):
            _write_state(
                experiment_root,
                schedule,
                "REPAIR_BLOCKED",
                record_count=repair.get("record_count"),
                queue_halt_reason=repair.get("queue_halt_reason"),
            )
            return {
                "experiment_complete": False,
                "stage": "REPAIR_BLOCKED",
                "generation": generation,
                "repair": repair,
            }
        repair_results_path = repair_root / "repair_results.json"
        verify_repair_results(
            json.loads(repair_results_path.read_text(encoding="utf-8"))
        )

        _write_state(experiment_root, schedule, "SUMMARIZING")
        from evidence_registry_gate import assert_current_autosar_results

        assert_current_autosar_results(generation, purpose="paper_primary")
        paper_root = experiment_root / "paper"
        generation_summary = summarize_generation(generation)
        repair_summary = summarize_repair(repair)
        generation_summary_path = paper_root / "generation_summary.json"
        generation_markdown_path = paper_root / "generation_summary.md"
        repair_summary_path = paper_root / "repair_summary.json"
        atomic_write_json(generation_summary_path, generation_summary)
        atomic_write_text(
            generation_markdown_path, generation_markdown(generation_summary)
        )
        atomic_write_json(repair_summary_path, repair_summary)

        artifacts = {
            "formal_experiment_schedule.json": sha256_file(top_schedule_path),
            "generation_results.json": sha256_file(generation_results_path),
            "repair_results.json": sha256_file(repair_results_path),
            "paper/generation_summary.json": sha256_file(generation_summary_path),
            "paper/generation_summary.md": sha256_file(generation_markdown_path),
            "paper/repair_summary.json": sha256_file(repair_summary_path),
        }
        result = {
            "schema_version": "atlas.asw_v3.full_experiment.v1",
            "experiment_complete": True,
            "schedule_content_sha256": schedule["content_sha256"],
            "generation_results_content_sha256": generation["content_sha256"],
            "repair_results_content_sha256": repair["content_sha256"],
            "generation_summary_content_sha256": generation_summary[
                "content_sha256"
            ],
            "repair_summary_content_sha256": repair_summary["content_sha256"],
            "completed_at_utc": utc_now(),
            "artifact_hashes": artifacts,
        }
        result["content_sha256"] = canonical_sha256(result)
        atomic_write_json(experiment_root / "full_experiment_manifest.json", result)
        _write_state(
            experiment_root,
            schedule,
            "COMPLETE",
            full_experiment_content_sha256=result["content_sha256"],
        )
        return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schedule-path", type=Path)
    parser.add_argument(
        "--freeze-manifest", type=Path, default=DEFAULT_FREEZE_MANIFEST
    )
    parser.add_argument("--experiment-root", type=Path)
    parser.add_argument("--generation-timeout-seconds", type=int, default=1800)
    parser.add_argument("--repair-timeout-seconds", type=int, default=1800)
    parser.add_argument("--repair-max-rounds", type=int, default=2)
    parser.add_argument(
        "--controlled-reference-manifest",
        type=Path,
        default=DEFAULT_CONTROLLED_REFERENCE_MANIFEST,
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    schedule = (
        json.loads(args.schedule_path.read_text(encoding="utf-8"))
        if args.schedule_path is not None
        else build_schedule(formal_models(), "off", args.freeze_manifest)
    )
    verify_schedule(schedule)
    if args.dry_run:
        controlled_reference = verify_controlled_reference_manifest(
            args.controlled_reference_manifest
        )
        print(
            json.dumps(
                {
                    "pipeline_run_count": schedule["pipeline_run_count"],
                    "models": schedule["models"],
                    "schedule_content_sha256": schedule["content_sha256"],
                    "controlled_reference_content_sha256": controlled_reference[
                        "content_sha256"
                    ],
                    "controlled_task_count": len(
                        controlled_reference["controlled_repair_design"]["tasks"]
                    ),
                    "external_model_api_calls": 0,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    if args.experiment_root is None:
        parser.error("--experiment-root is required unless --dry-run is used")
    result = run_full_experiment(
        schedule,
        args.experiment_root,
        generation_timeout_seconds=args.generation_timeout_seconds,
        repair_timeout_seconds=args.repair_timeout_seconds,
        repair_max_rounds=args.repair_max_rounds,
        controlled_reference_manifest=args.controlled_reference_manifest,
    )
    print(
        json.dumps(
            {
                "experiment_complete": result["experiment_complete"],
                "stage": result.get("stage", "COMPLETE"),
                "content_sha256": result.get("content_sha256"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if result["experiment_complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
