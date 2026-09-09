"""Summarize frozen ASW V3 natural-failure and controlled-mutation repairs."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from run_asw_v3_repair_experiment import (
    COMPLETE_STATUSES,
    canonical_sha256,
    verify_repair_results,
)
from experiment_runtime import atomic_write_json
from summarize_asw_v3_experiment import wilson


def summarize(results: dict[str, Any]) -> dict[str, Any]:
    complete = [
        item
        for item in results.get("records") or []
        if item.get("status") in COMPLETE_STATUSES
    ]
    cohorts: dict[str, Any] = {}
    for cohort in ("natural_failure",):
        records = [item for item in complete if item.get("cohort") == cohort]
        detected = sum(
            item.get("initial_independent_decision") != "PASS" for item in records
        )
        successes = sum(item.get("strict_restoration") is True for item in records)
        exact_recoveries = sum(
            item.get("exact_original_recovery") is True for item in records
        )
        triggered = sum(item.get("repair_triggered") is True for item in records)
        cohorts[cohort] = {
            "complete_runs": len(records),
            "detected_initial_failures": detected,
            "detection_rate": detected / len(records) if records else None,
            "repair_triggered_runs": triggered,
            "repair_trigger_rate": triggered / len(records) if records else None,
            "successful_repairs": successes,
            "success_rate": successes / detected if detected else None,
            "success_wilson_95": wilson(successes, detected),
            "exact_original_recoveries": exact_recoveries,
            "exact_original_recovery_rate": (
                exact_recoveries / detected if detected else None
            ),
            "estimability": (
                "ESTIMABLE"
                if detected
                else "NOT_ESTIMABLE_NO_OBSERVED_FAILURES"
            ),
            "accepted_round_counts": dict(
                Counter(item.get("repair_accepted_rounds") for item in records)
            ),
            "attempt_outcomes": dict(
                Counter(item.get("attempt_outcome") for item in records)
            ),
            "automation_boundary_reasons": dict(
                Counter(
                    reason
                    for item in records
                    for reason in (
                        item.get("automation_boundary_reason")
                        if isinstance(item.get("automation_boundary_reason"), list)
                        else [item.get("automation_boundary_reason") or "none"]
                    )
                )
            ),
        }
    schedule = results.get("schedule") or {}

    def mutation_row(records: list[dict[str, Any]], denominator: int) -> dict[str, Any]:
        detected = sum(
            item.get("initial_independent_decision") != "PASS" for item in records
        )
        successes = sum(item.get("strict_restoration") is True for item in records)
        return {
            "scheduled_denominator": denominator,
            "complete_runs": len(records),
            "detected_initial_failures": detected,
            "detection_rate": detected / denominator if denominator else None,
            "successful_repairs": successes,
            "repair_rate": successes / denominator if denominator else None,
            "wilson_95": wilson(successes, denominator),
            "exact_original_recovery_rate": (
                sum(item.get("exact_original_recovery") is True for item in records)
                / denominator
                if denominator
                else None
            ),
            "attempt_outcomes": dict(
                Counter(item.get("attempt_outcome") for item in records)
            ),
        }

    core_rows = {}
    core_denominators = schedule.get("core_operator_denominators") or {}
    for operator, denominator in sorted(core_denominators.items()):
        records = [
            item
            for item in complete
            if item.get("cohort") == "controlled_mutation"
            and item.get("analysis_layer") == "core_fixed_operator"
            and item.get("base_operator") == operator
        ]
        core_rows[operator] = mutation_row(records, int(denominator))

    substitution_rows = {}
    for mutation in schedule.get("controlled_substitute_mutations") or []:
        scheduled_substitutions = [
            item
            for item in schedule.get("runs") or []
            if item.get("cohort") == "controlled_mutation"
            and item.get("analysis_layer") == "substitution"
            and item.get("mutation") == mutation
        ]
        records = [
            item
            for item in complete
            if item.get("cohort") == "controlled_mutation"
            and item.get("analysis_layer") == "substitution"
            and item.get("mutation") == mutation
        ]
        substitution_rows[mutation] = mutation_row(
            records, len(scheduled_substitutions)
        )

    controlled_records = [
        item for item in complete if item.get("cohort") == "controlled_mutation"
    ]
    generation_count = int(schedule.get("source_generation_run_count") or 0)
    natural_failure_count = int(schedule.get("natural_failure_count") or 0)
    terminal_generation_failure_count = int(
        schedule.get("source_terminal_generation_failure_count") or 0
    )
    observed_generation_failures = (
        natural_failure_count + terminal_generation_failure_count
    )
    summary = {
        "schema_version": "atlas.asw_v3.repair_paper_summary.v3",
        "source_results_content_sha256": results.get("content_sha256"),
        "cohorts": cohorts,
        "controlled_repair_accounting": {
            "design_cells": int(schedule.get("controlled_design_cell_count") or 0),
            "core_fixed_operator_tasks": int(
                schedule.get("controlled_core_fixed_operator_task_count") or 0
            ),
            "substitution_tasks": int(
                schedule.get("controlled_substitution_task_count") or 0
            ),
            "complete_tasks": len(controlled_records),
            "combined_repair_rate": None,
            "combined_rate_policy": "PROHIBITED_SEPARATE_ANALYSIS_LAYERS",
        },
        "controlled_core_fixed_operators": core_rows,
        "controlled_substitutions": substitution_rows,
        "natural_failure_incidence": {
            "source_generation_runs": generation_count,
            "observed_generation_failures": observed_generation_failures,
            "repairable_natural_failure_outputs": natural_failure_count,
            "terminal_failures_without_repairable_arxml": (
                terminal_generation_failure_count
            ),
            "rate": (
                observed_generation_failures / generation_count
                if generation_count else None
            ),
            "wilson_95": wilson(observed_generation_failures, generation_count),
            "repair_effect_estimable": natural_failure_count > 0,
        },
        "interpretation_constraints": [
            "Natural failures and injected mutations are reported separately.",
            "Controlled mutations require an independently strict-PASS frozen baseline.",
            "The 85 applicable fixed-operator opportunities use operator-specific denominators; NOT_APPLICABLE cells stay in the applicability ledger and are excluded from that operator's repair-rate denominator.",
            "The 15 deterministic substitute tasks are reported as a separate analysis layer and are never pooled with the 85 core opportunities.",
            "Partial repair cohorts are descriptive and cannot establish fixed-pipeline repair effectiveness.",
            "Zero natural failures imply zero observed repair demand; natural-failure repair success is not estimable and is never reported as 100%.",
            "Controlled mutation success requires an independently detected failure followed by independent strict PASS.",
            "Exact byte-for-byte recovery is reported separately from semantically valid strict restoration.",
        ],
    }
    summary["content_sha256"] = canonical_sha256(summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    results = json.loads(args.results.read_text(encoding="utf-8"))
    verify_repair_results(results)
    summary = summarize(results)
    atomic_write_json(args.output, summary)
    print(json.dumps({"content_sha256": summary["content_sha256"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
