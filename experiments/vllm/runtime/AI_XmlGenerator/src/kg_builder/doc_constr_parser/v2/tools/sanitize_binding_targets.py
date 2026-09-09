"""Downgrade invalid lexical property hints to valid class-context hints."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from bind_semantic_targets import MetamodelIndex


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    records = [json.loads(line) for line in args.input.read_text(encoding="utf-8").splitlines() if line.strip()]
    index = MetamodelIndex(json.loads(args.metadata.read_text(encoding="utf-8")))
    changed = 0
    for record in records:
        result: list[dict] = []
        seen: set[tuple] = set()
        for target in record["targets"]:
            class_name = target.get("class_name")
            property_name = target.get("property_name")
            if class_name and property_name:
                declarations = index.declarations(class_name, property_name)
                if not declarations or not any(item.get("xml_tag") for item in declarations):
                    target = dict(target)
                    target["role"] = "context"
                    target["property_name"] = None
                    target["evidence"] += f"; lexical property {property_name} is not a direct XML-bound metamodel property"
                    changed += 1
                    issue = "lexical_property_downgraded_to_class_context"
                    if issue not in record["curation"]["issues"]:
                        record["curation"]["issues"].append(issue)
            key = (target.get("role"), target.get("class_name"), target.get("property_name"))
            if key not in seen:
                seen.add(key)
                result.append(target)
        record["targets"] = result
    with args.output.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(json.dumps({"record_count":len(records),"downgraded_property_count":changed},ensure_ascii=False,indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
