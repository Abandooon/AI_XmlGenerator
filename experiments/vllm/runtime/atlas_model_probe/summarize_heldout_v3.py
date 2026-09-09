"""Fail-closed stratified summary for the prospective held-out V3 cohort.

The case is the independent unit. Three seed runs form one case stability
profile; run-level counts are diagnostics and never receive an independence-
based interval. The source design, not result labels, owns tier and V15 topology
relation.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import yaml


HELDOUT_SOURCE = Path(r"E:\54239\Documents\atlas_autosar_heldout_v3\heldout_cases.yaml")
EXPECTED_SOURCE_SHA256 = "78dc6d65672d896af3c19b50a5efbf5ca18d8237de9f32f2b7234cd6ff226945"
TERMINAL_STATUSES = {
    "COMPLETE",
    "RESUMED_COMPLETE",
    "TERMINAL_FAILURE",
    "RESUMED_TERMINAL_FAILURE",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def wilson(successes: int, total: int, z: float = 1.959963984540054) -> list[float]:
    if total <= 0:
        raise ValueError("case-level interval requires a positive denominator")
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


def source_cases(source: Path = HELDOUT_SOURCE) -> dict[str, dict[str, Any]]:
    if sha256_file(source) != EXPECTED_SOURCE_SHA256:
        raise ValueError("held-out V3 source identity changed")
    document = yaml.safe_load(source.read_text(encoding="utf-8"))
    if (
        document.get("schema_version") != "atlas.autosar.heldout.v3"
        or (document.get("experiment_design") or {}).get("independent_cases") != 12
        or (document.get("experiment_design") or {}).get("run_count") != 36
    ):
        raise ValueError("held-out V3 design identity is incomplete")
    cases = {str(case["case_id"]): case for case in document["cases"]}
    cells = Counter((case["tier"], case["structural_role"]) for case in cases.values())
    expected_cells = {
        (tier, role): 2
        for tier in ("minimal", "standard", "full")
        for role in ("REPLICATION", "EXTENSION")
    }
    if len(cases) != 12 or dict(cells) != expected_cells:
        raise ValueError("held-out V3 source is not factorially balanced")
    return cases


def summarize(results: dict[str, Any], *, source: Path = HELDOUT_SOURCE) -> dict[str, Any]:
    cases = source_cases(source)
    schedule = results.get("schedule") or {}
    if (
        schedule.get("cohort") != "prospective_internally_authored_heldout_v3"
        or schedule.get("heldout_source_sha256") != EXPECTED_SOURCE_SHA256
    ):
        raise ValueError("results are not bound to held-out V3")
    models = list(schedule.get("models") or [])
    scheduled = list(schedule.get("runs") or [])
    records = list(results.get("records") or [])
    if not models or len({str(item.get("run_id") or "") for item in scheduled}) != len(scheduled):
        raise ValueError("held-out schedule model/run identity is incomplete")
    record_by_run = {str(item.get("run_id") or ""): item for item in records}
    if len(record_by_run) != len(records) or set(record_by_run) != {
        str(item["run_id"]) for item in scheduled
    }:
        raise ValueError("held-out result records do not exactly cover the schedule")

    model_rows: dict[str, Any] = {}
    seeds = [104729, 130363, 155921]
    for model in models:
        model_schedule = [item for item in scheduled if item.get("model") == model]
        if len(model_schedule) != 36:
            raise ValueError(f"held-out model schedule is not 12 x 3: {model}")
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for item in model_schedule:
            case_id = str(item.get("case_id") or "")
            if case_id not in cases:
                raise ValueError(f"held-out schedule contains an unknown case: {case_id}")
            grouped[case_id].append(item)
        if set(grouped) != set(cases):
            raise ValueError(f"held-out schedule case coverage is incomplete: {model}")

        case_rows: dict[str, Any] = {}
        for case_id, case_schedule in grouped.items():
            ordered = sorted(case_schedule, key=lambda item: int(item["repetition"]))
            if (
                [int(item["repetition"]) for item in ordered] != [1, 2, 3]
                or [int(item["seed"]) for item in ordered] != seeds
            ):
                raise ValueError(f"held-out repetitions/seeds differ from preregistration: {case_id}")
            case_records = [record_by_run[str(item["run_id"])] for item in ordered]
            if any(record.get("status") not in TERMINAL_STATUSES for record in case_records):
                raise ValueError(f"held-out case is not terminal: {case_id}")
            outcomes = [record.get("independent_decision") == "PASS" for record in case_records]
            pass_count = sum(outcomes)
            source_case = cases[case_id]
            case_rows[case_id] = {
                "tier": source_case["tier"],
                "structural_role": source_case["structural_role"],
                "run_pass_count": pass_count,
                "repetitions": 3,
                "stability_score": pass_count / 3,
                "strict_case_pass": pass_count == 3,
            }

        def group_row(selected: list[dict[str, Any]], *, interval: bool) -> dict[str, Any]:
            strict = sum(bool(item["strict_case_pass"]) for item in selected)
            row = {
                "case_count": len(selected),
                "strict_3_of_3_pass_cases": strict,
                "strict_case_pass_rate": strict / len(selected),
                "mean_case_stability_score": sum(
                    float(item["stability_score"]) for item in selected
                ) / len(selected),
            }
            if interval:
                row["strict_case_pass_rate_wilson_95"] = wilson(strict, len(selected))
            return row

        strata = {
            role: group_row(
                [item for item in case_rows.values() if item["structural_role"] == role],
                interval=True,
            )
            for role in ("REPLICATION", "EXTENSION")
        }
        if any(row["case_count"] != 6 for row in strata.values()):
            raise ValueError("held-out structural strata are not six cases each")
        cells = {
            f"{tier}:{role}": group_row(
                [
                    item
                    for item in case_rows.values()
                    if item["tier"] == tier and item["structural_role"] == role
                ],
                interval=False,
            )
            for tier in ("minimal", "standard", "full")
            for role in ("REPLICATION", "EXTENSION")
        }
        if any(row["case_count"] != 2 for row in cells.values()):
            raise ValueError("held-out tier x structural-role cells are not two cases each")
        all_cases = list(case_rows.values())
        run_pass_count = sum(item["run_pass_count"] for item in all_cases)
        model_rows[model] = {
            "case_count": 12,
            "run_count": 36,
            "run_pass_count_diagnostic": run_pass_count,
            "run_pass_rate_diagnostic": run_pass_count / 36,
            "run_level_interval_prohibited": True,
            "structural_strata": strata,
            "tier_by_structural_role_cells": cells,
            "pooled_balanced_mixture_descriptive": group_row(all_cases, interval=False),
            "case_results": dict(sorted(case_rows.items())),
        }

    summary = {
        "schema_version": "atlas.autosar.heldout_v3.stratified_summary.v1",
        "source_results_content_sha256": results.get("content_sha256"),
        "heldout_source_sha256": EXPECTED_SOURCE_SHA256,
        "external_benchmark": False,
        "independent_unit": "case",
        "models": model_rows,
        "reporting_constraints": [
            "The two six-case structural strata are primary and are never replaced by the pooled summary.",
            "The six tier-by-structural-role cells are mandatory descriptive reports.",
            "The 12-case pooled value is descriptive only for the deliberately balanced mixture.",
            "The 36 seed runs are repeated stability observations and receive no independence-based interval.",
            "Extension means unseen requirement-determined topology for the whole pipeline, not provider synthesis of structure.",
            "This prospective internally-authored cohort is not an external benchmark.",
        ],
    }
    summary["content_sha256"] = canonical_sha256(summary)
    return summary
