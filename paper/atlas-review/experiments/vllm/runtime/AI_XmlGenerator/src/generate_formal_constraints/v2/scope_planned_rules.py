"""Make unimplemented rules fail closed only when their bound targets exist."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    plan = json.loads(args.input.read_text(encoding="utf-8"))
    scoped = 0
    errors: list[str] = []
    for rule in plan.get("rules", []):
        if rule["implementation"]["status"] != "planned" or rule["selector"]["tags"]:
            continue
        tags: set[str] = set()
        for binding in rule.get("bindings", []):
            for path in binding.get("path_variants", []):
                if path:
                    tags.add(path.split("/", 1)[0])
        if not tags:
            errors.append(f"{rule['rule_id']}: planned must-rule has no bound selector")
            continue
        rule["selector"] = {"tags": sorted(tags), "mode": "any"}
        rule["implementation"]["reason"] = (
            rule["implementation"].get("reason")
            or "Deep atomization is pending; applicable targets must return NOT_EVALUATED."
        )
        scoped += 1
    if errors:
        print("\n".join(errors))
        return 1
    plan["coverage"]["scoped_planned_rule_count"] = scoped
    args.output.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(plan["coverage"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
