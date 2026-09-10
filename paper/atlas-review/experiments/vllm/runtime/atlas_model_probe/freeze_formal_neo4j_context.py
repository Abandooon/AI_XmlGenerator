"""Create the read-only Neo4j context hash used by the formal experiment."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv
from neo4j import GraphDatabase

from neo4j_experiment_context import collect_neo4j_context, verify_neo4j_context


ROOT = Path(__file__).resolve().parent
REPOSITORY = Path(r"E:\git projects\AI_XmlGenerator")
OUTPUT = ROOT / "FORMAL_NEO4J_CONTEXT.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--verify",
        action="store_true",
        help="verify live read-only context against the frozen file without writing",
    )
    args = parser.parse_args()
    expected = (
        json.loads(OUTPUT.read_text(encoding="utf-8"))
        if args.verify else None
    )
    load_dotenv(REPOSITORY / ".env", override=False)
    config = yaml.safe_load(
        (REPOSITORY / "config/llm_api_config.yaml").read_text(encoding="utf-8")
    )
    knowledge_graph = config["knowledge_graph"]
    password = (
        os.environ.get("NEO4J_PASSWORD")
        or os.environ.get("NEO4J_PWD")
        or knowledge_graph.get("neo4j_password")
        or ""
    )
    if not password:
        raise RuntimeError("Neo4j credentials are unavailable")
    uri = os.environ.get("NEO4J_URI") or knowledge_graph["neo4j_uri"]
    user = os.environ.get("NEO4J_USER") or knowledge_graph.get("neo4j_user", "neo4j")
    database = os.environ.get("NEO4J_DATABASE") or knowledge_graph.get(
        "neo4j_database"
    )
    retrieval = json.loads(
        (REPOSITORY / "src/llm_generation/knowledge/v2/retrieval_manifest.json")
        .read_text(encoding="utf-8")
    )
    driver = GraphDatabase.driver(uri, auth=(user, password))
    try:
        context = collect_neo4j_context(
            driver,
            database=database,
            dataset_sha256=retrieval["dataset_sha256"],
            expected_card_count=int(retrieval["card_count"]),
        )
    finally:
        driver.close()
    if args.verify:
        verify_neo4j_context(context, expected)
    else:
        OUTPUT.write_text(
            json.dumps(context, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    print(
        json.dumps(
            {
                "decision": "PASS",
                "mode": "verify" if args.verify else "freeze",
                "output": str(OUTPUT),
                "context_sha256": context["context_sha256"],
                "credentials_included": False,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
