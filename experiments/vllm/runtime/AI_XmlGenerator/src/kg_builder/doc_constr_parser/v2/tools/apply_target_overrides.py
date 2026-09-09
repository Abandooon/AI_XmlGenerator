"""Apply explicit curator target corrections after deterministic hint expansion."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--overrides", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    records = [json.loads(line) for line in args.input.read_text(encoding="utf-8").splitlines() if line.strip()]
    overrides = json.loads(args.overrides.read_text(encoding="utf-8"))
    known = {item["id"] for item in records}
    unknown = sorted(set(overrides) - known)
    if unknown:
        print("Unknown override IDs: " + ", ".join(unknown))
        return 1
    for record in records:
        if record["id"] in overrides:
            record["targets"] = overrides[record["id"]]
            issue = "explicit_target_override"
            if issue not in record["curation"]["issues"]:
                record["curation"]["issues"].append(issue)
    with args.output.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(json.dumps({"record_count":len(records),"override_count":len(overrides)},ensure_ascii=False,indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
