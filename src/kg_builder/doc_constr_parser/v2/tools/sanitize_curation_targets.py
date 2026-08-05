"""Remove lexical target hints that are not actual metamodel classes.

Triage expansion uses only explicit source mentions.  Some annotated documents
contain plural words or standardized instance names in CLASS annotations.  This
gate prevents those terms from becoming graph links while recording an audit
issue on the curation record.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    metadata = json.loads(args.metadata.read_text(encoding="utf-8"))
    classes: set[str] = set()
    for bucket in ("groups", "complexTypes", "extract_inner_class"):
        classes.update(metadata.get(bucket, {}))
    records = [json.loads(line) for line in args.input.read_text(encoding="utf-8").splitlines() if line.strip()]
    removed_count = 0
    for record in records:
        retained: list[dict] = []
        removed: list[str] = []
        for target in record["targets"]:
            class_name = target.get("class_name")
            if class_name is None or class_name in classes:
                retained.append(target)
            else:
                removed.append(class_name)
        if removed:
            removed_count += len(removed)
            issue = "discarded_non_metamodel_term"
            if issue not in record["curation"]["issues"]:
                record["curation"]["issues"].append(issue)
            audit = "Discarded non-metamodel lexical targets: " + ", ".join(dict.fromkeys(removed))
            record["curation"]["notes"] = (record["curation"]["notes"] + " " + audit).strip()
        if not retained:
            retained = [{
                "role": "context", "class_name": None, "property_name": None,
                "evidence": "No explicit source term resolved to a metamodel class.",
            }]
        record["targets"] = retained
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(json.dumps({"record_count": len(records), "discarded_target_count": removed_count}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
