"""Merge implementation maps and reject accidental conflicting decisions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    merged: dict[str, list[dict]] = {}
    origins: dict[str, str] = {}
    for path in args.inputs:
        payload = json.loads(path.read_text(encoding="utf-8"))
        for constraint_id, specs in payload.items():
            if constraint_id in merged and merged[constraint_id] != specs:
                raise SystemExit(
                    f"Conflicting implementation for {constraint_id}: "
                    f"{origins[constraint_id]} vs {path}"
                )
            merged[constraint_id] = specs
            origins[constraint_id] = str(path)

    args.output.write_text(
        json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"implementation_count": len(merged)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
