"""Command-line entry point for the V2 ARXML validator."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from .engine import ValidationEngine
except ImportError:
    from engine import ValidationEngine


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("arxml", nargs="+", type=Path)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--xsd", type=Path)
    parser.add_argument("--reference-scope", choices=["complete", "partial"], default="complete")
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = ValidationEngine.from_plan_file(args.plan, args.reference_scope).validate(args.arxml, args.xsd)
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(json.dumps({"decision": result["decision"], **result["summary"]}, ensure_ascii=False, indent=2))
    return {"PASS": 0, "FAIL": 1, "INCOMPLETE": 2, "ERROR": 3}[result["decision"]]


if __name__ == "__main__":
    raise SystemExit(main())
