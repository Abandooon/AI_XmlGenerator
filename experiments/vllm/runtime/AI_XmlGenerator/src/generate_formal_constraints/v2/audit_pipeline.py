"""Audit source, semantic, binding, publication, retrieval, and validation-plan consistency."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def unique_map(records: list[dict], key: str, label: str, errors: list[str]) -> dict[str, dict]:
    counts = Counter(str(record.get(key)) for record in records)
    duplicates = sorted(item for item, count in counts.items() if count > 1)
    if duplicates:
        errors.append(f"{label} contains duplicate ids: {duplicates}")
    return {str(record[key]): record for record in records}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--curation", type=Path, required=True)
    parser.add_argument("--bindings", type=Path, required=True)
    parser.add_argument("--constraints", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--cards", type=Path, required=True)
    parser.add_argument("--retrieval-manifest", type=Path, required=True)
    parser.add_argument("--qualification-ledger", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    errors: list[str] = []
    source = unique_map(load_jsonl(args.source), "id", "source", errors)
    curation = unique_map(load_jsonl(args.curation), "id", "curation", errors)
    bindings = unique_map(load_jsonl(args.bindings), "id", "bindings", errors)
    constraints_payload = json.loads(args.constraints.read_text(encoding="utf-8"))
    constraint_records = (
        constraints_payload
        if isinstance(constraints_payload, list)
        else constraints_payload.get("constraints", [])
    )
    constraints = unique_map(constraint_records, "id", "constraints", errors)
    cards = unique_map(load_jsonl(args.cards), "constraint_id", "cards", errors)
    declared_retrieval_manifest = json.loads(
        args.retrieval_manifest.read_text(encoding="utf-8-sig")
    )
    ordered_cards = sorted(cards.values(), key=lambda item: str(item.get("constraint_id", "")))
    payload = json.dumps(
        ordered_cards, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    actual_retrieval_manifest = {
        "schema_version": "2.0",
        "dataset_sha256": hashlib.sha256(payload.encode("utf-8")).hexdigest(),
        "card_count": len(ordered_cards),
        "unique_constraint_count": len(cards),
    }
    if declared_retrieval_manifest != actual_retrieval_manifest:
        errors.append("retrieval manifest does not match retrieval_cards.jsonl")
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    rules = plan.get("rules", [])
    qualification = json.loads(args.qualification_ledger.read_text(encoding="utf-8-sig"))
    qualification_records = qualification.get("records", [])

    expected_ids = set(source)
    for label, records in (("curation", curation), ("bindings", bindings), ("constraints", constraints), ("cards", cards)):
        missing = sorted(expected_ids - set(records))
        extra = sorted(set(records) - expected_ids)
        if missing:
            errors.append(f"{label} is missing {len(missing)} source ids: {missing[:20]}")
        if extra:
            errors.append(f"{label} has {len(extra)} unknown ids: {extra[:20]}")

    for constraint_id in sorted(expected_ids & set(curation) & set(bindings)):
        source_sha = source[constraint_id]["source"]["sha256"]
        if curation[constraint_id].get("source_sha256") != source_sha:
            errors.append(f"{constraint_id}: curation source hash mismatch")
        if bindings[constraint_id].get("source_sha256") != source_sha:
            errors.append(f"{constraint_id}: binding source hash mismatch")

    must_ids = {
        constraint_id
        for constraint_id, record in curation.items()
        if record["verification"]["must_validate"]
    }
    plan_ids = {str(rule.get("constraint_id")) for rule in rules}
    if must_ids != plan_ids:
        errors.append(
            f"must/plan id mismatch: missing={sorted(must_ids-plan_ids)[:20]}, "
            f"extra={sorted(plan_ids-must_ids)[:20]}"
        )

    rule_counts = Counter(str(rule.get("constraint_id")) for rule in rules)
    for constraint_id in sorted(must_ids):
        if rule_counts[constraint_id] < 1:
            errors.append(f"{constraint_id}: no validation rule")
        binding_status = bindings.get(constraint_id, {}).get("binding_status")
        if binding_status != "complete":
            errors.append(f"{constraint_id}: must-validate binding is {binding_status}")

    for rule in rules:
        constraint_id = str(rule.get("constraint_id"))
        semantic = curation.get(constraint_id)
        if semantic and rule.get("source_sha256") != semantic.get("source_sha256"):
            errors.append(f"{rule.get('rule_id')}: source hash mismatch")
        implementation = rule.get("implementation", {})
        status = implementation.get("status")
        plugin = implementation.get("plugin")
        if status == "implemented" and not plugin:
            errors.append(f"{rule.get('rule_id')}: implemented rule has no plugin")
        if status == "planned" and plugin:
            errors.append(f"{rule.get('rule_id')}: planned rule unexpectedly has a plugin")

    implemented = sum(rule.get("implementation", {}).get("status") == "implemented" for rule in rules)
    planned = sum(rule.get("implementation", {}).get("status") == "planned" for rule in rules)
    planned_ids = {rule["rule_id"] for rule in rules if rule.get("implementation", {}).get("status") == "planned"}
    qualification_ids = [str(item.get("rule_id")) for item in qualification_records]
    if len(set(qualification_ids)) != len(qualification_ids):
        errors.append("qualification ledger contains duplicate rule ids")
    if planned_ids != set(qualification_ids):
        errors.append(
            f"qualification/planned mismatch: missing={sorted(planned_ids-set(qualification_ids))[:20]}, "
            f"extra={sorted(set(qualification_ids)-planned_ids)[:20]}"
        )
    if any(item.get("current_disposition") != "remain_not_evaluated" for item in qualification_records):
        errors.append("qualification ledger falsely promotes an unimplemented rule")
    rule_by_id = {rule["rule_id"]: rule for rule in rules}
    for item in qualification_records:
        rule = rule_by_id.get(str(item.get("rule_id")))
        if rule and item.get("source_sha256") != rule.get("source_sha256"):
            errors.append(f"{item.get('rule_id')}: qualification source hash mismatch")

    report = {
        "schema_version": "2.0",
        "valid": not errors,
        "retrieval_dataset_sha256": actual_retrieval_manifest["dataset_sha256"],
        "counts": {
            "source": len(source),
            "curation": len(curation),
            "bindings": len(bindings),
            "constraints": len(constraints),
            "retrieval_cards": len(cards),
            "must_validate": len(must_ids),
            "validation_rules": len(rules),
            "implemented_rules": implemented,
            "planned_rules": planned,
            "qualified_planned_rules": len(qualification_records),
            "must_binding_failures": sum(
                bindings.get(item, {}).get("binding_status") != "complete" for item in must_ids
            ),
        },
        "errors": errors,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
