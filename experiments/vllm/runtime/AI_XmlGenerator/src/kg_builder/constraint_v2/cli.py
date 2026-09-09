"""Build, publish, and audit the ConstraintV2 Neo4j projection."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from .model import build_projection, projection_summary
from .neo4j_publish import apply_projection, audit_projection

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONSTRAINTS = PROJECT_ROOT / "src/kg_builder/doc_constr_parser/v2/constraints_v2.json"
DEFAULT_CARDS = PROJECT_ROOT / "src/llm_generation/knowledge/v2/retrieval_cards.jsonl"
DEFAULT_MANIFEST = PROJECT_ROOT / "src/llm_generation/knowledge/v2/retrieval_manifest.json"
DEFAULT_PLAN = PROJECT_ROOT / "src/generate_formal_constraints/v2/validation_plan.json"
DEFAULT_VALIDATOR_MANIFEST = PROJECT_ROOT / "src/validation/v2/validator_manifest.json"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Publish the versioned ConstraintV2 model")
    parser.add_argument("--constraints", type=Path, default=DEFAULT_CONSTRAINTS)
    parser.add_argument("--cards", type=Path, default=DEFAULT_CARDS)
    parser.add_argument("--retrieval-manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--validation-plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--validator-manifest", type=Path, default=DEFAULT_VALIDATOR_MANIFEST)
    parser.add_argument("--apply-neo4j", action="store_true")
    parser.add_argument("--audit-only", action="store_true")
    parser.add_argument("--neo4j-uri")
    parser.add_argument("--neo4j-user")
    parser.add_argument("--neo4j-password")
    parser.add_argument("--neo4j-database")
    return parser.parse_args(argv)


def _connection(args: argparse.Namespace) -> dict[str, str | None]:
    load_dotenv(PROJECT_ROOT / ".env")
    return {
        "uri": args.neo4j_uri or os.getenv("NEO4J_URI") or "neo4j://127.0.0.1:7687",
        "user": args.neo4j_user or os.getenv("NEO4J_USER") or "neo4j",
        "password": args.neo4j_password or os.getenv("NEO4J_PASSWORD") or os.getenv("NEO4J_PWD"),
        "database": args.neo4j_database or os.getenv("NEO4J_DATABASE") or None,
    }


def run(args: argparse.Namespace) -> dict:
    projection = build_projection(
        constraints_path=args.constraints,
        cards_path=args.cards,
        retrieval_manifest_path=args.retrieval_manifest,
        validation_plan_path=args.validation_plan,
        validator_manifest_path=args.validator_manifest,
    )
    summary = projection_summary(projection)
    if not args.apply_neo4j and not args.audit_only:
        return {**summary, "mode": "dry-run", "valid": True}

    connection = _connection(args)
    if not connection["password"]:
        raise ValueError("Neo4j password is not configured")
    if args.audit_only:
        result = audit_projection(
            **connection,
            dataset_sha256=summary["dataset_sha256"],
            expected=projection["dataset"]["props"],
        )
    else:
        result = apply_projection(**connection, projection=projection)
    return {**summary, "mode": "audit" if args.audit_only else "apply-neo4j", "neo4j": result}


def main(argv: list[str] | None = None) -> int:
    result = run(parse_args(argv))
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    valid = result.get("valid", result.get("neo4j", {}).get("valid", True))
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
