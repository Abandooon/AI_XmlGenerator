"""Post-run common scoring and case-level paired statistics for PIL V4."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable

import pil_v4_contract as contract

BOOTSTRAP_DRAWS = 20_000
BOOTSTRAP_SEED = 20260902
CONTRASTS = (("p1", "p0"), ("p2", "p1"), ("p3", "p2"), ("p3", "p0"))


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] * (upper - position) + ordered[upper] * (position - lower)


def _bootstrap_difference(differences: list[float], *, cluster_ids: list[Any] | None = None) -> dict[str, Any]:
    rng = random.Random(BOOTSTRAP_SEED)
    if cluster_ids is None:
        draws = [
            sum(differences[rng.randrange(len(differences))] for _ in differences) / len(differences)
            for _ in range(BOOTSTRAP_DRAWS)
        ]
        estimate = sum(differences) / len(differences)
        clusters = len(differences)
    else:
        grouped: dict[Any, list[float]] = defaultdict(list)
        for cluster, value in zip(cluster_ids, differences):
            grouped[cluster].append(value)
        populations = [items for _, items in sorted(grouped.items(), key=lambda kv: str(kv[0]))]
        draws = []
        for _ in range(BOOTSTRAP_DRAWS):
            sampled = [populations[rng.randrange(len(populations))] for _ in populations]
            values = [value for cluster in sampled for value in cluster]
            draws.append(sum(values) / len(values))
        estimate = sum(differences) / len(differences)
        clusters = len(populations)
    return {
        "estimate": estimate,
        "ci95": [_percentile(draws, 0.025), _percentile(draws, 0.975)],
        "clusters": clusters,
        "draws": BOOTSTRAP_DRAWS,
        "seed": BOOTSTRAP_SEED,
    }


def _sign_test(differences: list[float]) -> dict[str, Any]:
    positive = sum(value > 0 for value in differences)
    negative = sum(value < 0 for value in differences)
    n = positive + negative
    if n == 0:
        return {"positive": positive, "negative": negative, "ties": len(differences), "two_sided_p": 1.0}
    k = min(positive, negative)
    tail = sum(math.comb(n, index) for index in range(k + 1)) / (2 ** n)
    return {
        "positive": positive,
        "negative": negative,
        "ties": len(differences) - n,
        "two_sided_p": min(1.0, 2 * tail),
    }


def _validate_balanced_entries(entries: list[dict[str, Any]], gold_ids: set[Any]) -> None:
    expected = {
        (case_id, arm, replicate)
        for case_id in gold_ids
        for arm in contract.ARMS
        for replicate in (1, 2, 3)
    }
    observed: list[tuple[Any, Any, Any]] = []
    unit_ids: list[str] = []
    for entry in entries:
        row = entry.get("row") or {}
        observed.append((entry.get("case_id"), row.get("mode"), row.get("replicate")))
        unit_ids.append(str(row.get("unit_id") or ""))
        replicate = int(row.get("replicate") or 0)
        if row.get("seed") != contract.seed_for_replicate(replicate):
            raise ValueError(f"ledger seed mismatch for {row.get('unit_id')}")
        if not row.get("prompt_sha256"):
            raise ValueError(f"ledger prompt hash missing for {row.get('unit_id')}")
    if len(unit_ids) != len(set(unit_ids)):
        raise ValueError("formal ledger contains duplicate unit ids")
    if set(observed) != expected or len(observed) != len(expected):
        raise ValueError("formal ledger is not the exact balanced 60 x 4 x 3 design")


def _citation_metrics(decision: dict[str, Any] | None, gold: dict[str, Any]) -> tuple[float, float, float]:
    predicted = contract.evidence_set(decision or {})
    accepted = set(gold.get("accepted_evidence") or gold.get("required_evidence") or [])
    if not predicted and not accepted:
        return 1.0, 1.0, 1.0
    overlap = len(predicted & accepted)
    precision = overlap / len(predicted) if predicted else 0.0
    recall = overlap / len(accepted) if accepted else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1


def score_row(entry: dict[str, Any], gold: dict[str, Any], schema: dict[str, Any], rules: dict[str, Any]) -> dict[str, Any]:
    row = entry["row"]
    arm = row["mode"]
    decision = row.get("final_decision")
    allowed = None if arm == "p0" else row.get("retrieved_evidence") or []
    audit = (
        contract.audit_decision(decision, schema=schema, rules=rules, allowed_evidence=allowed)
        if isinstance(decision, dict)
        else {"status": "FAIL", "findings": [{"code": "no_decision", "stage": "structure", "message": "No JSON decision was available."}]}
    )
    compatibility = contract.score_against_gold(decision, gold)
    structure_valid = row.get("schema_status") == "PASS" and isinstance(decision, dict)
    delivery_valid = structure_valid and audit["status"] == "PASS"
    system_release = bool(row.get("system_release"))
    correct = compatibility.correct
    endpoint_success = delivery_valid and correct and system_release
    precision, recall, f1 = _citation_metrics(decision, gold)
    unsafe_release = system_release and (not correct or not delivery_valid)
    result = {
        "unit_id": row["unit_id"], "case_id": row["id"], "cluster_id": gold.get("cluster_id"),
        "arm": arm, "replicate": row["replicate"],
        "structure_valid": structure_valid, "common_delivery_valid": delivery_valid,
        "gold_correct": correct, "endpoint_success": endpoint_success,
        "system_release": system_release,
        "error_release": unsafe_release,
        "semantic_error_release": system_release and not correct,
        "invalid_artifact_release": system_release and not delivery_valid,
        "conclusion_correct": compatibility.conclusion,
        "forum_type_compatible": compatibility.forum_type,
        "evidence_requirement_met": compatibility.evidence,
        "conditional_answer_correct": compatibility.conditional_answer,
        "citation_precision": precision, "citation_recall": recall, "citation_f1": f1,
        "common_audit": audit,
        "repair_attempted": bool((row.get("repair") or {}).get("attempted")),
        "repair_status": (row.get("repair") or {}).get("status"),
        "external_call_count": int(row.get("external_call_count") or 0),
        "logical_request_count": int(
            row.get("logical_request_count") or row.get("external_call_count") or 0
        ),
        "transport_request_count": int(
            row.get("transport_request_count") or len(row.get("transport_attempts") or [])
        ),
        "tokens_total": int((row.get("usage") or {}).get("total_tokens") or 0),
        "tokens_input": int((row.get("usage") or {}).get("input_tokens") or 0),
        "tokens_output": int((row.get("usage") or {}).get("output_tokens") or 0),
    }
    if arm == "p3" and result["repair_attempted"]:
        before = contract.score_against_gold(row.get("parsed_decision"), gold).correct
        result["pre_repair_gold_correct"] = before
        result["repair_recovered_correctness"] = (not before) and correct and system_release
        result["repair_induced_error"] = before and not correct
    return result


def _mean(rows: list[dict[str, Any]], key: str) -> float:
    return sum(float(bool(row[key])) if isinstance(row[key], bool) else float(row[key]) for row in rows) / len(rows)


def summarize(scored: list[dict[str, Any]]) -> dict[str, Any]:
    by_arm: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_case_arm: dict[tuple[Any, str], list[dict[str, Any]]] = defaultdict(list)
    cluster_by_case: dict[Any, Any] = {}
    for row in scored:
        by_arm[row["arm"]].append(row)
        by_case_arm[(row["case_id"], row["arm"])].append(row)
        cluster_by_case[row["case_id"]] = row.get("cluster_id") or row["case_id"]
    metric_keys = [
        "endpoint_success", "error_release", "semantic_error_release", "invalid_artifact_release",
        "structure_valid", "common_delivery_valid",
        "system_release", "gold_correct", "conclusion_correct", "forum_type_compatible",
        "conditional_answer_correct", "citation_precision", "citation_recall", "citation_f1",
        "tokens_input", "tokens_output", "tokens_total", "external_call_count",
        "logical_request_count", "transport_request_count",
    ]
    arm_summary = {
        arm: {"units": len(rows), **{key: _mean(rows, key) for key in metric_keys}}
        for arm, rows in sorted(by_arm.items())
    }
    case_ids = sorted({row["case_id"] for row in scored}, key=str)
    contrasts: dict[str, Any] = {}
    for treatment, control in CONTRASTS:
        differences = [
            _mean(by_case_arm[(case_id, treatment)], "endpoint_success")
            - _mean(by_case_arm[(case_id, control)], "endpoint_success")
            for case_id in case_ids
        ]
        contrasts[f"{treatment}-{control}"] = {
            "case_clustered_bootstrap": _bootstrap_difference(differences),
            "dependence_cluster_bootstrap_sensitivity": _bootstrap_difference(
                differences, cluster_ids=[cluster_by_case[case_id] for case_id in case_ids]
            ),
            "paired_sign_test": _sign_test(differences),
        }
    ordered = sorted(
        ((name, value["paired_sign_test"]["two_sided_p"]) for name, value in contrasts.items()),
        key=lambda item: item[1],
    )
    running = 0.0
    total = len(ordered)
    for rank, (name, raw_p) in enumerate(ordered):
        running = max(running, min(1.0, raw_p * (total - rank)))
        contrasts[name]["paired_sign_test"]["holm_adjusted_p"] = running
    p3 = by_arm.get("p3", [])
    repairs = [row for row in p3 if row["repair_attempted"]]
    repair_summary = {
        "triggered": len(repairs),
        "trigger_rate": len(repairs) / len(p3) if p3 else None,
        "successful_release": sum(row["system_release"] for row in repairs),
        "recovered_correctness": sum(row.get("repair_recovered_correctness", False) for row in repairs),
        "induced_errors": sum(row.get("repair_induced_error", False) for row in repairs),
    }
    return {"arms": arm_summary, "contrasts": contrasts, "p3_repair": repair_summary}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    entries = _jsonl(args.ledger)
    gold_rows = _jsonl(args.gold)
    gold = {row["id"]: row for row in gold_rows}
    if len(entries) != 720:
        raise ValueError(f"formal scoring requires 720 ledger entries, found {len(entries)}")
    if len(gold) != 60:
        raise ValueError(f"formal scoring requires 60 gold cases, found {len(gold)}")
    _validate_balanced_entries(entries, set(gold))
    schema = contract.load_schema()
    rules = contract.load_rules()
    scored = [score_row(entry, gold[entry["case_id"]], schema, rules) for entry in entries]
    body = {
        "schema_version": "atlas.pil.formal_analysis.v4.1",
        "analysis_unit": "case",
        "replicate_policy": "average three fixed-seed repetitions within each case and arm before paired case-level inference",
        "multiplicity_policy": "Holm adjustment across the four predeclared paired sign tests",
        "unit_count": len(scored),
        "case_count": len(gold),
        "bootstrap_draws": BOOTSTRAP_DRAWS,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "inputs": {
            "ledger_sha256": hashlib.sha256(args.ledger.read_bytes()).hexdigest(),
            "gold_sha256": hashlib.sha256(args.gold.read_bytes()).hexdigest(),
            "contract_sha256": contract.contract_sha256(),
            "decision_schema_sha256": contract.sha256_file(contract.ROOT / "schema" / "decision_schema_v4.json"),
            "delivery_rules_sha256": contract.sha256_file(contract.ROOT / "rules" / "delivery_rules_v4.json"),
        },
        "summary": summarize(scored),
        "scored_units": scored,
    }
    document = {**body, "content_sha256": contract.canonical_sha256(body)}
    args.output.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "sha256": document["content_sha256"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
