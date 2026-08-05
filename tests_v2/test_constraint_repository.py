from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.llm_generation.knowledge.v2.dataset import build_retrieval_manifest
from src.llm_generation.knowledge.v2.repository import (
    HybridConstraintRepository,
    LocalConstraintRepository,
)


def card(constraint_id: str, tag: str, *, family: str = "test") -> dict:
    return {
        "schema_version": "2.0",
        "constraint_id": constraint_id,
        "source_sha256": "0" * 64,
        "title": constraint_id,
        "summary": f"Rule for {tag}",
        "section_path": ["test"],
        "class_tags": [tag],
        "property_tags": [],
        "paths": [],
        "rule_family": family,
        "scope": "local",
        "normativity": "mandatory",
        "importance": "major",
        "is_core": False,
        "usages": ["generation_context"],
        "validation_policy": "must",
        "must_validate": True,
        "severity": "error",
        "backend": "python",
        "quality": "approved",
    }


class FailingNeo4j:
    def retrieve(self, **query):
        raise RuntimeError("database unavailable")


class ConstraintRepositoryTests(unittest.TestCase):
    def test_manifest_is_verified_and_local_ranking_is_deterministic(self) -> None:
        cards = [card("B", "B-TAG"), card("A", "A-TAG")]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cards_path = root / "cards.jsonl"
            manifest_path = root / "manifest.json"
            cards_path.write_text(
                "".join(json.dumps(item) + "\n" for item in cards),
                encoding="utf-8",
            )
            manifest_path.write_text(
                json.dumps(build_retrieval_manifest(cards)),
                encoding="utf-8",
            )
            repository = LocalConstraintRepository.from_files(cards_path, manifest_path)
            batch = repository.retrieve(class_tags=["A-TAG"], max_constraints=5)
        self.assertEqual("local", batch.backend)
        self.assertEqual(["A"], [item["constraint_id"] for item in batch.cards])

    def test_hybrid_fallback_is_explicit(self) -> None:
        cards = [card("A", "A-TAG")]
        local = LocalConstraintRepository(cards, build_retrieval_manifest(cards)["dataset_sha256"])
        repository = HybridConstraintRepository(local=local, neo4j=FailingNeo4j(), mode="hybrid")
        batch = repository.retrieve(class_tags=["A-TAG"], max_constraints=5)
        self.assertEqual("local-fallback", batch.backend)
        self.assertIn("database unavailable", batch.fallback_reason)


if __name__ == "__main__":
    unittest.main()
