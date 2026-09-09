"""Re-score only unchanged V2 cases against V4 consensus gold as a diagnostic.

This is intentionally not the V4 experiment: five cases whose facts changed are
excluded, baseline/RAG use the locked human transcription of their retained
free text, and no citation or delivery-validity endpoint is estimated.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
CHANGED_CASES = {19, 34, 44, 53, 55}
ARMS = ("baseline", "rag", "prism")
CONTRASTS = (("prism", "baseline"), ("prism", "rag"), ("rag", "baseline"))
BOOTSTRAP_DRAWS = 20_000
BOOTSTRAP_SEED = 20260904


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * p
    low, high = math.floor(position), math.ceil(position)
    return ordered[low] if low == high else ordered[low] * (high - position) + ordered[high] * (position - low)


def _bootstrap(differences: list[float], clusters: list[str] | None = None) -> dict[str, Any]:
    if clusters is None:
        population = differences
    else:
        grouped: dict[str, list[float]] = defaultdict(list)
        for cluster, value in zip(clusters, differences):
            grouped[cluster].append(value)
        population = [sum(values) / len(values) for _, values in sorted(grouped.items())]
    rng = random.Random(BOOTSTRAP_SEED)
    draws = [
        sum(population[rng.randrange(len(population))] for _ in population) / len(population)
        for _ in range(BOOTSTRAP_DRAWS)
    ]
    return {
        "estimate": sum(population) / len(population),
        "ci95": [_percentile(draws, 0.025), _percentile(draws, 0.975)],
        "clusters": len(population), "draws": BOOTSTRAP_DRAWS, "seed": BOOTSTRAP_SEED,
    }


def _prediction_for(row: dict[str, str] | dict[str, Any], *, arm: str) -> tuple[str, str]:
    if arm in {"baseline", "rag"}:
        return str(row.get("human_conclusion") or ""), str(row.get("human_forum_type") or "")
    pred = row.get("pred") or {}
    return str(pred.get("conclusion") or ""), str(pred.get("forum_type") or "")


def _correct(conclusion: str, forum_type: str, gold: dict[str, Any], *, compatible: bool) -> bool:
    conclusion_ok = conclusion in set(gold.get("accepted_conclusions") or [gold.get("conclusion")])
    accepted = set(gold.get("accepted_forum_types") or [gold.get("forum_type")])
    if compatible and forum_type == "special_or_general":
        forum_ok = bool(accepted & {"special", "general"})
    else:
        forum_ok = forum_type in accepted
    return conclusion_ok and forum_ok


def build(*, ledger_path: Path, audit_csv: Path, gold_path: Path) -> dict[str, Any]:
    gold_rows = _jsonl(gold_path)
    gold = {int(row["id"]): row for row in gold_rows}
    retained = {
        str(row["unit_id"]): row
        for row in _jsonl(ledger_path)
        if str(row.get("arm")) == "prism" and int(row.get("case_id")) not in CHANGED_CASES
    }
    with audit_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        audited = {
            str(row["unit_id"]): row
            for row in csv.DictReader(handle)
            if int(row["case_id"]) not in CHANGED_CASES
        }
    records: list[dict[str, Any]] = []
    for arm in ARMS:
        for case_id in sorted(set(gold) - CHANGED_CASES):
            for replicate in range(1, 4):
                unit_id = f"{case_id}|{arm}|{replicate}"
                source = retained[unit_id]["row"] if arm == "prism" else audited[unit_id]
                conclusion, forum_type = _prediction_for(source, arm=arm)
                records.append({
                    "unit_id": unit_id, "case_id": case_id,
                    "cluster_id": gold[case_id]["cluster_id"], "arm": arm,
                    "replicate": replicate, "conclusion": conclusion,
                    "forum_type": forum_type,
                    "strict_correct": _correct(conclusion, forum_type, gold[case_id], compatible=False),
                    "compatible_correct": _correct(conclusion, forum_type, gold[case_id], compatible=True),
                })
    expected = 55 * 3 * 3
    if len(records) != expected or len({row["unit_id"] for row in records}) != expected:
        raise ValueError(f"expected {expected} unique retained diagnostic units, found {len(records)}")

    by_arm: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_case_arm: dict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)
    for row in records:
        by_arm[row["arm"]].append(row)
        by_case_arm[(row["case_id"], row["arm"])].append(row)
    arm_summary = {
        arm: {
            "units": len(rows),
            "strict_correct": sum(row["strict_correct"] for row in rows),
            "strict_rate": sum(row["strict_correct"] for row in rows) / len(rows),
            "compatible_correct": sum(row["compatible_correct"] for row in rows),
            "compatible_rate": sum(row["compatible_correct"] for row in rows) / len(rows),
        }
        for arm, rows in sorted(by_arm.items())
    }
    contrasts: dict[str, Any] = {}
    case_ids = sorted(set(gold) - CHANGED_CASES)
    for metric in ("strict_correct", "compatible_correct"):
        contrasts[metric] = {}
        for treatment, control in CONTRASTS:
            differences = []
            clusters = []
            for case_id in case_ids:
                t = sum(row[metric] for row in by_case_arm[(case_id, treatment)]) / 3
                c = sum(row[metric] for row in by_case_arm[(case_id, control)]) / 3
                differences.append(t - c)
                clusters.append(str(gold[case_id]["cluster_id"]))
            contrasts[metric][f"{treatment}-{control}"] = {
                "case_bootstrap": _bootstrap(differences),
                "dependence_cluster_sensitivity": _bootstrap(differences, clusters),
            }
    return {
        "schema_version": "atlas.pil.v4_retained_output_diagnostic.v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "POST_HOC_DIAGNOSTIC_ONLY",
        "provider_calls": 0,
        "paid_api_calls": 0,
        "inputs": {
            "v2_ledger": {"path": str(ledger_path), "sha256": _sha256(ledger_path)},
            "locked_human_parse_audit_csv": {"path": str(audit_csv), "sha256": _sha256(audit_csv)},
            "v4_consensus_gold": {"path": str(gold_path), "sha256": _sha256(gold_path)},
        },
        "exclusions": {
            "facts_changed_after_v2": sorted(CHANGED_CASES),
            "reason": "The retained V2 outputs answer different facts and cannot be scored against V4 gold.",
        },
        "design": {
            "cases": 55, "arms": list(ARMS), "replicates": 3, "units": expected,
            "baseline_rag_projection": "locked blinded human transcription",
            "prism_projection": "retained structured V2 decision",
            "citation_endpoint": "NOT_EVALUATED",
            "delivery_validity_endpoint": "NOT_EVALUATED",
        },
        "arms": arm_summary,
        "contrasts": contrasts,
        "claim_boundary": {
            "confirmatory": False,
            "is_v4_four_arm_result": False,
            "supports_v4_power_or_effect_assumption": False,
            "permitted_use": "measurement-threat and continuity diagnostic only",
        },
    }


def _markdown(document: dict[str, Any]) -> str:
    lines = [
        "# PIL V4 retained-output diagnostic", "",
        "Status: `POST_HOC_DIAGNOSTIC_ONLY`; provider/paid calls: 0/0.", "",
        "Five fact-edited cases (19, 34, 44, 53, 55) are excluded. The remaining 55 cases reuse locked V2 outputs; this is not the V4 four-arm experiment and cannot support a confirmatory claim.", "",
        "| Arm | Strict | Compatible | Units |", "|---|---:|---:|---:|",
    ]
    for arm in ARMS:
        item = document["arms"][arm]
        lines.append(f"| {arm} | {item['strict_rate']:.1%} | {item['compatible_rate']:.1%} | {item['units']} |")
    strict = document["contrasts"]["strict_correct"]["prism-baseline"]["case_bootstrap"]
    compatible = document["contrasts"]["compatible_correct"]["prism-baseline"]["case_bootstrap"]
    lines.extend([
        "",
        f"Old prism − baseline is {strict['estimate']:+.1%} under the strict view (95% case-bootstrap CI {strict['ci95'][0]:+.1%} to {strict['ci95'][1]:+.1%}) and {compatible['estimate']:+.1%} under the compatible view (95% CI {compatible['ci95'][0]:+.1%} to {compatible['ci95'][1]:+.1%}).",
        "",
        "The two rows preserve the earlier lower/upper treatment of `special_or_general`. Citation and delivery-validity outcomes are not evaluated because the retained arms did not share the V4 evidence identity and contract.",
        "",
    ])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--audit-csv", type=Path, required=True)
    parser.add_argument("--gold", type=Path, default=ROOT / "data" / "consensus_gold_v4.jsonl")
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args(argv)
    document = build(ledger_path=args.ledger, audit_csv=args.audit_csv, gold_path=args.gold)
    args.output_json.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.output_md.write_text(_markdown(document), encoding="utf-8")
    print(json.dumps({"status": document["status"], "arms": document["arms"], "provider_calls": 0}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
