"""One entry point for XSD enrichment, ConstraintV2 build, Neo4j, and audit."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the integrated AUTOSAR knowledge/constraint pipeline")
    parser.add_argument("--apply-neo4j", action="store_true")
    parser.add_argument("--skip-rebuild", action="store_true")
    parser.add_argument("--skip-xsd", action="store_true")
    return parser.parse_args(argv)


def _run(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        check=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
    )
    return {
        "command": command[1:],
        "stdout_tail": completed.stdout.splitlines()[-20:],
        "stderr_tail": completed.stderr.splitlines()[-20:],
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    steps: dict[str, Any] = {}
    if not args.skip_xsd:
        xsd_command = [
            sys.executable,
            "-B",
            "-m",
            "src.kg_builder.xsd_enrichment.cli",
            "--serialization-manifest",
            "src/llm_generation/knowledge/v2/xsd_serialization_manifest.json",
            "--replace-output",
        ]
        if args.apply_neo4j:
            xsd_command.append("--apply-neo4j")
        steps["xsd_enrichment"] = _run(xsd_command)
    if not args.skip_rebuild:
        # The validator manifest pins the compiled XSD serialization contract,
        # so XSD compilation must precede the constraint/validator build.
        steps["constraint_build"] = _run([
            sys.executable,
            "-B",
            "src/generate_formal_constraints/v2/run_pipeline.py",
        ])

    constraint_command = [
        sys.executable,
        "-B",
        "-m",
        "src.kg_builder.constraint_v2.cli",
    ]
    if args.apply_neo4j:
        constraint_command.append("--apply-neo4j")
    steps["constraint_neo4j"] = _run(constraint_command)
    if args.apply_neo4j:
        steps["constraint_neo4j_audit"] = _run([
            sys.executable,
            "-B",
            "-m",
            "src.kg_builder.constraint_v2.cli",
            "--audit-only",
        ])
    return {
        "schema_version": "2.0",
        "mode": "apply-neo4j" if args.apply_neo4j else "dry-run",
        "steps": steps,
    }


def main(argv: list[str] | None = None) -> int:
    report = run(parse_args(argv))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
