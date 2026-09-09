"""Publish immutable source, curation, and binding layers as constraints_v2.json."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator, RefResolver


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--curation", type=Path, required=True)
    parser.add_argument("--bindings", type=Path, required=True)
    parser.add_argument("--structured-schema", type=Path, required=True)
    parser.add_argument("--source-schema", type=Path, required=True)
    parser.add_argument("--validation-plan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest-output", type=Path, required=True)
    return parser.parse_args()


def published_targets(binding: dict) -> list[dict]:
    result: list[dict] = []
    for target in binding["targets"]:
        paths = target["path_variants"] or [None]
        tags = target["class_xml_tags"] or [None]
        for number, path in enumerate(paths):
            result.append({
                "role": target["role"],
                "class_name": target["class_name"],
                "class_xml_tag": tags[number] if number < len(tags) else (tags[0] if tags else None),
                "property_name": target["property_name"],
                "property_xml_tag": target["property_xml_tag"],
                "path": path,
                "binding_status": target["binding_status"],
                "evidence": target["evidence"],
                "candidates": target["candidates"],
            })
    return result


def main() -> int:
    args = parse_args()
    source = {item["id"]: item for item in load_jsonl(args.source)}
    curation = load_jsonl(args.curation)
    bindings = {item["id"]: item for item in load_jsonl(args.bindings)}
    plan = json.loads(args.validation_plan.read_text(encoding="utf-8"))
    plan_by_constraint: dict[str, list[dict]] = {}
    for rule in plan.get("rules", []):
        plan_by_constraint.setdefault(rule["constraint_id"], []).append(rule)

    source_schema = json.loads(args.source_schema.read_text(encoding="utf-8"))
    structured_schema = json.loads(args.structured_schema.read_text(encoding="utf-8"))
    resolver = RefResolver.from_schema(
        structured_schema,
        store={"source_constraint.schema.json": source_schema},
    )
    validator = Draft202012Validator(structured_schema, resolver=resolver)
    output: list[dict] = []
    errors: list[str] = []

    for curated in curation:
        constraint_id = curated["id"]
        source_record = source[constraint_id]
        binding = bindings[constraint_id]
        formal = plan_by_constraint.get(constraint_id, [])
        issues = list(dict.fromkeys(
            curated["curation"]["issues"]
            + binding["issues"]
            + (["formal_rule_planned"] if any(item["implementation"]["status"] != "implemented" for item in formal) else [])
        ))
        approved = curated["curation"]["status"] == "curated" and binding["binding_status"] in {"complete", "not_applicable"} and "formal_rule_planned" not in issues
        record = {
            "schema_version": "2.0",
            "id": constraint_id,
            "source": source_record,
            "semantics": curated["semantics"],
            "targets": published_targets(binding),
            "verification": curated["verification"],
            "quality": {
                "semantic_status": curated["curation"]["status"],
                "binding_status": binding["binding_status"],
                "review_status": "approved" if approved else "needs_review",
                "issues": issues,
            },
        }
        for error in validator.iter_errors(record):
            errors.append(f"{constraint_id}:{list(error.path)}:{error.message}")
        output.append(record)

    if errors:
        print("\n".join(errors))
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "schema_version": "2.0",
        "source_count": len(source),
        "published_count": len(output),
        "coverage_percent": round(100 * len(output) / len(source), 2) if source else 0,
        "approved_count": sum(item["quality"]["review_status"] == "approved" for item in output),
        "needs_review_count": sum(item["quality"]["review_status"] == "needs_review" for item in output),
        "must_validate_count": sum(item["verification"]["must_validate"] for item in output),
        "must_validate_implemented_count": len({
            item["constraint_id"] for item in plan.get("rules", [])
            if item["implementation"]["status"] == "implemented"
        }),
    }
    args.manifest_output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
