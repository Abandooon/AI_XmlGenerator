"""Publish the reviewed disposition of constraints that need external evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

PARTIAL_GUARD_IDS = {
    "TPS_SWCT_01040", "TPS_SWCT_01000", "TPS_SWCT_01001",
    "TPS_SWCT_01511", "TPS_SWCT_01512", "TPS_SWCT_01513",
}


def disposition(record: dict) -> tuple[str, str, str]:
    family = record["semantics"]["rule_family"]
    summary = record["semantics"]["summary"]
    if family == "generation_procedure":
        return (
            "generated_artifact",
            "retain_manual",
            "The claim constrains generated RTE/A2L/ECU artifacts or a generation procedure; input ARXML alone cannot prove it.",
        )
    if family == "runtime_behavior":
        return (
            "runtime_evidence",
            "retain_manual",
            "The claim constrains runtime behavior or implementation code; a static ARXML model cannot prove absence or execution behavior.",
        )
    if record["verification"]["observability"] == "partial":
        return (
            "external_antecedent",
            "retain_manual",
            "ARXML can check a structural consequence only after an external design-intent antecedent is established.",
        )
    return (
        "external_design_evidence",
        "retain_manual",
        f"The requirement depends on project intent, external configuration, or semantic correspondence not encoded in ARXML: {summary}",
    )


def compile_plan(constraints: list[dict]) -> dict:
    reviews: list[dict] = []
    for record in sorted(constraints, key=lambda item: item["id"]):
        if record["verification"]["policy"] != "manual":
            continue
        capability, decision, reason = disposition(record)
        tags = sorted({
            value
            for target in record.get("targets", [])
            for value in (target.get("class_xml_tag"), target.get("property_xml_tag"))
            if value
        })
        reviews.append({
            "constraint_id": record["id"],
            "title": record["source"].get("title") or record["semantics"]["summary"],
            "summary": record["semantics"]["summary"],
            "importance": record["semantics"]["importance"],
            "decision": decision,
            "required_capability": capability,
            "reason": reason,
            "selector_tags": tags,
            "partial_arxml_guard": record["id"] in PARTIAL_GUARD_IDS,
            "review_instruction": (
                "Obtain and inspect the required external evidence; do not repair ARXML solely to silence this review item."
            ),
            "source": record["source"]["source"],
        })
    if len(reviews) != 51:
        raise ValueError(f"Expected 51 reviewed manual constraints, found {len(reviews)}")
    return {
        "schema_version": "1.0",
        "reviewer": "Codex delegated domain review",
        "decision_policy": "retain manual when the full normative claim is not provable from the submitted ARXML bundle",
        "count": len(reviews),
        "reviews": reviews,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--curation", required=True, type=Path)
    parser.add_argument("--bindings", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    load_jsonl = lambda path: [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    sources = {item["id"]: item for item in load_jsonl(args.source)}
    bindings = {item["id"]: item for item in load_jsonl(args.bindings)}
    constraints = []
    for curated in load_jsonl(args.curation):
        cid = curated["id"]
        targets = []
        for target in bindings[cid]["targets"]:
            for class_tag in target.get("class_xml_tags") or [None]:
                targets.append({
                    "class_xml_tag": class_tag,
                    "property_xml_tag": target.get("property_xml_tag"),
                })
        constraints.append({
            "id": cid, "source": sources[cid],
            "semantics": curated["semantics"],
            "verification": curated["verification"], "targets": targets,
        })
    plan = compile_plan(constraints)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"manual_review_count": plan["count"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
