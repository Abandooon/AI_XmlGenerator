from __future__ import annotations

import unittest
from pathlib import Path

from src.kg_builder.constraint_v2.model import build_projection


class ConstraintNeo4jModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        root = Path(__file__).resolve().parents[1]
        cls.projection = build_projection(
            constraints_path=root / "src/kg_builder/doc_constr_parser/v2/constraints_v2.json",
            cards_path=root / "src/llm_generation/knowledge/v2/retrieval_cards.jsonl",
            retrieval_manifest_path=root / "src/llm_generation/knowledge/v2/retrieval_manifest.json",
            validation_plan_path=root / "src/generate_formal_constraints/v2/validation_plan.json",
            validator_manifest_path=root / "src/validation/v2/validator_manifest.json",
        )

    def test_projection_is_complete_and_hash_pinned(self) -> None:
        self.assertEqual(1085, len(self.projection["constraints"]))
        self.assertEqual(554, len(self.projection["validation_rules"]))
        dataset = self.projection["dataset"]["props"]
        self.assertEqual(64, len(dataset["dataset_sha256"]))
        self.assertEqual(64, len(dataset["validator_sha256"]))
        self.assertEqual("ready", dataset["status"])

    def test_structured_semantics_are_preserved_on_graph_nodes(self) -> None:
        record = next(
            item for item in self.projection["constraints"]
            if item["constraint_id"] == "TPS_SWCT_01447"
        )
        props = record["props"]
        self.assertEqual("major", props["importance"])
        self.assertTrue(props["must_validate"])
        self.assertIn("P-PORT-PROTOTYPE", props["class_tags"])
        self.assertTrue(props["card_json"])


if __name__ == "__main__":
    unittest.main()
