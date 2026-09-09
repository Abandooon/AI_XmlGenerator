"""Expand assistant-reviewed compact decisions into semantic curation records."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from jsonschema import Draft202012Validator

PROPERTY = re.compile(r"\b([A-Z][A-Za-z0-9]+)\.([a-z][A-Za-z0-9]+)\b")


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--decisions", type=Path, nargs="+", required=True)
    parser.add_argument("--profiles", type=Path, required=True)
    parser.add_argument("--decision-schema", type=Path, required=True)
    parser.add_argument("--curation-schema", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def lexical_targets(source: dict) -> list[dict]:
    text = source["title"] + " " + source["expression"]
    candidates = list(dict.fromkeys(
        source["terminology_context"].get("local_classes", [])
        + source["terminology_context"].get("inherited_classes", [])
    ))
    targets: list[dict] = []
    property_classes: set[str] = set()
    for class_name, property_name in PROPERTY.findall(text):
        property_classes.add(class_name)
        targets.append({"role":"property","class_name":class_name,"property_name":property_name,"evidence":f"explicit source mention {class_name}.{property_name}"})
    for class_name in candidates:
        if class_name in property_classes:
            continue
        if re.search(rf"(?<![A-Za-z0-9]){re.escape(class_name)}s?(?![A-Za-z0-9])", text):
            targets.append({"role":"context","class_name":class_name,"property_name":None,"evidence":f"explicit source mention {class_name}"})
        if len(targets) >= 8:
            break
    if not targets:
        targets.append({"role":"context","class_name":None,"property_name":None,"evidence":"No explicit metamodel target in this overview statement."})
    return targets


def main() -> int:
    args = parse_args()
    source = {item["id"]: item for item in load_jsonl(args.source)}
    profiles = json.loads(args.profiles.read_text(encoding="utf-8"))
    decision_validator = Draft202012Validator(json.loads(args.decision_schema.read_text(encoding="utf-8")))
    curation_validator = Draft202012Validator(json.loads(args.curation_schema.read_text(encoding="utf-8")))
    decisions: list[dict] = []
    errors: list[str] = []
    seen: set[str] = set()
    for path in args.decisions:
        for line_number, decision in enumerate(load_jsonl(path), 1):
            for error in decision_validator.iter_errors(decision):
                errors.append(f"{path.name}:{line_number}:{list(error.path)}:{error.message}")
            if decision.get("id") in seen:
                errors.append(f"{path.name}:{line_number}:duplicate id {decision.get('id')}")
            seen.add(decision.get("id"))
            decisions.append(decision)

    output: list[dict] = []
    for decision in decisions:
        constraint_id = decision["id"]
        record = source.get(constraint_id)
        profile = profiles.get(decision["profile"])
        if record is None:
            errors.append(f"unknown source id {constraint_id}")
            continue
        if profile is None:
            errors.append(f"unknown profile {decision['profile']} for {constraint_id}")
            continue
        values = dict(profile)
        for key in ("rule_family", "scope", "observability", "importance", "is_core", "must_validate"):
            if key in decision:
                values[key] = decision[key]
        issues = [] if values["status"] == "curated" else ["triage_only_requires_deep_curation"]
        if decision.get("note"):
            issues.append("curator_note_attached")
        curated = {
            "schema_version":"2.0",
            "id":constraint_id,
            "source_sha256":record["source"]["sha256"],
            "semantics":{
                "normativity":values["normativity"], "importance":values["importance"],
                "is_core":values["is_core"], "usages":values["usages"],
                "rule_family":values["rule_family"], "scope":values["scope"],
                "summary":record["title"], "rationale":values["rationale"]
            },
            "targets":lexical_targets(record),
            "verification":{
                "observability":values["observability"], "observability_reason":values["rationale"],
                "policy":values["policy"], "must_validate":values["must_validate"],
                "severity":values["severity"], "preferred_backend":values["preferred_backend"],
                "fallback_backend":values["fallback_backend"]
            },
            "curation":{"status":values["status"],"issues":issues,"notes":decision.get("note","")}
        }
        for error in curation_validator.iter_errors(curated):
            errors.append(f"{constraint_id}:{list(error.path)}:{error.message}")
        output.append(curated)
    if errors:
        print("\n".join(errors))
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as handle:
        for item in output:
            handle.write(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(json.dumps({"decision_count":len(decisions),"curation_count":len(output)},ensure_ascii=False,indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
