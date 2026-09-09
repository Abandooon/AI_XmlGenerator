"""Create paper-table JSON and Markdown from a frozen ASW V3 experiment."""

from __future__ import annotations

import argparse
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from experiment_runtime import atomic_write_json, atomic_write_text
from run_asw_v3_experiment import (
    SUCCESS_STATUSES,
    TERMINAL_STATUSES,
    verify_experiment_results,
)


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    import hashlib

    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def wilson(successes: int, total: int, z: float = 1.959963984540054) -> list[float] | None:
    if total <= 0:
        return None
    proportion = successes / total
    denominator = 1 + z * z / total
    center = (proportion + z * z / (2 * total)) / denominator
    margin = (
        z
        * math.sqrt(
            proportion * (1 - proportion) / total + z * z / (4 * total * total)
        )
        / denominator
    )
    return [max(0.0, center - margin), min(1.0, center + margin)]


def _mean(values: list[Any]) -> float | None:
    numbers = [float(item) for item in values if item is not None]
    return statistics.fmean(numbers) if numbers else None


def summarize(results: dict[str, Any]) -> dict[str, Any]:
    records = list(results.get("records") or [])
    models = list((results.get("schedule") or {}).get("models") or [])
    model_rows: dict[str, Any] = {}
    case_outcomes: dict[str, dict[str, bool]] = defaultdict(dict)
    for model in models:
        selected = [item for item in records if item.get("model") == model]
        terminal = [item for item in selected if item.get("status") in TERMINAL_STATUSES]
        artifact_runs = [
            item for item in terminal if item.get("status") in SUCCESS_STATUSES
        ]
        pass_count = sum(
            item.get("independent_decision") == "PASS" for item in terminal
        )
        tier_rows = {}
        for tier in ("minimal", "standard", "full"):
            tier_records = [item for item in terminal if item.get("tier") == tier]
            tier_pass = sum(
                item.get("independent_decision") == "PASS" for item in tier_records
            )
            tier_rows[tier] = {
                "runs": len(tier_records),
                "passes": tier_pass,
                "pass_rate": tier_pass / len(tier_records) if tier_records else None,
                "wilson_95": wilson(tier_pass, len(tier_records)),
            }
        grouped_cases: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for item in terminal:
            grouped_cases[str(item["case_id"])].append(item)
        scheduled_cases = sorted({str(item["case_id"]) for item in selected})
        stable_pass = 0
        any_pass = 0
        for case_id in scheduled_cases:
            case_records = grouped_cases.get(case_id, [])
            outcomes = [item.get("independent_decision") == "PASS" for item in case_records]
            all_pass = len(case_records) == 3 and all(outcomes)
            case_outcomes[model][case_id] = all_pass
            stable_pass += all_pass
            any_pass += any(outcomes)
        stable_rate = stable_pass / len(scheduled_cases) if scheduled_cases else None
        for tier in ("minimal", "standard", "full"):
            tier_case_ids = sorted(
                {
                    str(item["case_id"])
                    for item in selected
                    if item.get("tier") == tier
                }
            )
            tier_stable_pass = sum(
                case_outcomes[model].get(case_id, False)
                for case_id in tier_case_ids
            )
            tier_rows[tier].update(
                {
                    "case_count": len(tier_case_ids),
                    "stable_pass_cases": tier_stable_pass,
                    "stable_pass_rate": (
                        tier_stable_pass / len(tier_case_ids)
                        if tier_case_ids else None
                    ),
                    "stable_pass_rate_wilson_95": wilson(
                        tier_stable_pass, len(tier_case_ids)
                    ),
                }
            )
        cohort_complete = bool(selected) and len(terminal) == len(selected)
        xsd_status_counts = {
            "PASS": sum(item.get("xsd_all_pass") is True for item in terminal),
            "FAIL": sum(item.get("xsd_all_pass") is False for item in terminal),
            "NOT_EVALUATED": sum(
                item.get("xsd_all_pass") is None for item in terminal
            ),
        }
        if sum(xsd_status_counts.values()) != len(terminal):
            raise ValueError("PASS/FAIL/NOT_EVALUATED XSD counters are not exhaustive")
        model_rows[model] = {
            "scheduled_runs": len(selected),
            "complete_runs": len(terminal),
            "terminal_observations": len(terminal),
            "artifact_evaluated_runs": len(artifact_runs),
            "terminal_generation_failures": len(terminal) - len(artifact_runs),
            "status_counts": dict(Counter(item.get("status") for item in selected)),
            "independent_passes": pass_count,
            "run_pass_rate": pass_count / len(terminal) if terminal else None,
            "run_pass_rate_wilson_95": wilson(pass_count, len(terminal)),
            "case_all_repetitions_pass_count": stable_pass,
            "case_all_repetitions_pass_rate": stable_rate,
            "case_all_repetitions_pass_rate_wilson_95": wilson(
                stable_pass, len(scheduled_cases)
            ),
            "case_any_pass_count": any_pass,
            "case_count": len(scheduled_cases),
            "cohort_complete": cohort_complete,
            "tier": tier_rows,
            # ``is True``, not ``bool(...)``: a run that produced no artifact
            # records None because the XSD gate never executed, and bool(None)
            # would count that as a failure -- the exact conflation this field
            # was changed to remove.
            "xsd_status_counts": xsd_status_counts,
            "xsd_all_pass_runs": xsd_status_counts["PASS"],
            "xsd_fail_runs": xsd_status_counts["FAIL"],
            # Stated rather than left to a subtraction, so "not evaluated" is
            # never read as "evaluated and failed".
            "xsd_not_evaluated_runs": xsd_status_counts["NOT_EVALUATED"],
            "artifact_profile_decisions": dict(
                Counter(item.get("artifact_profile_decision") for item in artifact_runs)
            ),
            "full_corpus_decisions": dict(
                Counter(item.get("full_corpus_decision") for item in artifact_runs)
            ),
            "mean_total_tokens": _mean([item.get("total_tokens") for item in terminal]),
            "mean_total_duration_seconds": _mean(
                [item.get("total_duration_seconds") for item in terminal]
            ),
            "provider_response_models": sorted(
                {
                    response_model
                    for item in terminal
                    for response_model in item.get("provider_response_models") or []
                }
            ),
            "provider_system_fingerprints": sorted(
                {
                    fingerprint
                    for item in terminal
                    for fingerprint in item.get("provider_system_fingerprints") or []
                }
            ),
        }

    summary = {
        "schema_version": "atlas.asw_v3.paper_summary.v3",
        "source_results_content_sha256": results.get("content_sha256"),
        "models": model_rows,
        "study_design": {
            "objective": "qualify_the_fixed_generation_pipeline_not_rank_models",
            "formal_model_count": len(models),
            "cross_model_comparison_performed": False,
            "stability_unit": "case_all_three_repetitions_pass",
        },
        "interpretation_constraints": [
            "The independent case is the primary unit; three runs measure stability.",
            "Terminal generation failures remain in the strict-pass denominator and are never retried until success.",
            "Token counts are reported without monetary conversion unless a separately hash-pinned price table is supplied.",
            "Artifact-profile PASS is not a full 554-rule AUTOSAR conformance claim.",
            "The formal protocol qualifies one fixed model and does not perform cross-model ranking.",
        ],
    }
    summary["content_sha256"] = canonical_sha256(summary)
    return summary


def markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# ASW V3 Luna qualification summary",
        "",
        "| Model | Complete runs | Run PASS | Stable cases (3/3) | Stable rate | Mean tokens | Mean seconds |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for model, row in summary["models"].items():
        rate = row["run_pass_rate"]
        if rate is None:
            lines.append(
                f"| {model} | {row['complete_runs']} | N/A | "
                f"0/{row['case_count']} | N/A | N/A | N/A |"
            )
            continue
        mean_tokens = row["mean_total_tokens"]
        mean_seconds = row["mean_total_duration_seconds"]
        lines.append(
            f"| {model} | {row['complete_runs']} | {rate:.3f} | "
            f"{row['case_all_repetitions_pass_count']}/{row['case_count']} | "
            f"{row['case_all_repetitions_pass_rate']:.3f} | "
            f"{mean_tokens:.1f} | {mean_seconds:.3f} |"
            if mean_tokens is not None and mean_seconds is not None
            else f"| {model} | {row['complete_runs']} | {rate:.3f} | "
            f"{row['case_all_repetitions_pass_count']}/{row['case_count']} | "
            f"{row['case_all_repetitions_pass_rate']:.3f} | N/A | N/A |"
        )
    lines.extend(
        [
            "",
            "This formal protocol reports Luna qualification and three-run stability; it does not rank models.",
            "The full-corpus coverage decision is reported separately from the component-artifact profile.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-markdown", type=Path, required=True)
    args = parser.parse_args()
    results = json.loads(args.results.read_text(encoding="utf-8"))
    verify_experiment_results(results)
    from evidence_registry_gate import assert_current_autosar_results

    assert_current_autosar_results(results, purpose="paper_primary")
    summary = summarize(results)
    atomic_write_json(args.output_json, summary)
    atomic_write_text(args.output_markdown, markdown(summary))
    print(json.dumps({"models": list(summary["models"]), "cross_model_comparison_performed": False}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
