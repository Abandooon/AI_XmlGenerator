"""Build a semantic reading view without altering immutable raw source evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--overrides", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    overrides = json.loads(args.overrides.read_text(encoding="utf-8"))
    records = [
        json.loads(line)
        for line in args.input.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    seen: set[str] = set()
    for record in records:
        override = overrides.get(record["id"])
        if override is None:
            continue
        seen.add(record["id"])
        record["title"] = override["title"]
        record.setdefault("parse", {}).setdefault("issues", []).append(
            "semantic_title_override_applied"
        )

    missing = sorted(set(overrides) - seen)
    if missing:
        raise SystemExit(f"Unknown override ids: {missing}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(json.dumps({"record_count": len(records), "override_count": len(seen)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
