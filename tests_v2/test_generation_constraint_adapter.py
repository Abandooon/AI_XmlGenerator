from __future__ import annotations

import unittest
from pathlib import Path

from src.llm_generation.knowledge.v2.constraint_retriever import ConstraintRetrieverV2
from src.llm_generation.knowledge.v2.generation_adapter import GenerationConstraintAdapterV2


class GenerationConstraintAdapterTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cards = Path(__file__).parents[1] / "src" / "llm_generation" / "knowledge" / "v2" / "retrieval_cards.jsonl"
        cls.adapter = GenerationConstraintAdapterV2(ConstraintRetrieverV2.from_jsonl(cards))

    def test_component_query_is_ranked_and_bounded(self) -> None:
        plan = {
            "name": "Controller",
            "type": "APPLICATION-SW-COMPONENT-TYPE",
            "element_design": {
                "ports": {"needed": True, "types": ["R-PORT-PROTOTYPE"]},
                "internal_behaviors": {
                    "needed": True,
                    "events": [{"type": "TIMING-EVENT"}],
                },
            },
        }
        schema = {
            "type": "object",
            "x-xml-tag": "APPLICATION-SW-COMPONENT-TYPE",
            "properties": {
                "PORTS": {
                    "type": "object",
                    "x-xml-wrapper-tag": "PORTS",
                    "properties": {
                        "R-PORT-PROTOTYPE": {
                            "type": "array",
                            "items": {"type": "object", "x-xml-tag": "R-PORT-PROTOTYPE"},
                        }
                    },
                },
                "TIMING-EVENT": {"type": "object", "x-xml-tag": "TIMING-EVENT"},
            },
        }
        cards = self.adapter.retrieve_for_component(
            component_plan=plan,
            component_schema=schema,
            max_constraints=12,
        )
        self.assertLessEqual(len(cards), 12)
        self.assertTrue(cards)
        self.assertTrue(any("TIMING-EVENT" in card["class_tags"] for card in cards))
        self.assertGreaterEqual(cards[0]["retrieval_score"], cards[-1]["retrieval_score"])
        rendered = self.adapter.render_prompt(cards)
        self.assertIn("Applicable AUTOSAR constraints", rendered)
        self.assertIn(cards[0]["constraint_id"], rendered)


if __name__ == "__main__":
    unittest.main()
