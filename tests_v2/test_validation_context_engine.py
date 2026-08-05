from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.validation.v2.context import build_validation_context
from src.validation.v2.engine import ValidationEngine

DATASET = "a" * 64


def planned_rule() -> dict:
    return {
        "rule_id": "constr_1#r1", "constraint_id": "constr_1",
        "source_sha256": "0" * 64, "title": "intent gated rule",
        "severity": "error", "policy": "must", "backend": "dsl",
        "implementation": {"status": "planned", "plugin": None, "reason": "test"},
        "selector": {"tags": ["TARGET"], "mode": "any"},
        "completeness": {"requires": ["well_formed_xml"], "on_missing": "not_evaluated"},
        "dependencies": [], "bindings": [],
        "formal_spec": {
            "activation": {"requires_validation_context": True, "requires_selected_constraint": True}
        },
    }


class ValidationContextEngineTests(unittest.TestCase):
    def validate(self, context):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.arxml"
            path.write_text("<AUTOSAR><TARGET/></AUTOSAR>", encoding="utf-8")
            return ValidationEngine(
                {"rules": [planned_rule()]}, expected_dataset_sha256=DATASET
            ).validate([path], validation_context=context)

    def test_missing_context_keeps_intent_gated_rule_not_evaluated(self) -> None:
        result = self.validate(None)
        self.assertEqual("INCOMPLETE", result["decision"])
        self.assertIn("requires", result["rules"][0]["notes"][0])

    def test_selected_constraint_reaches_normal_implementation_gate(self) -> None:
        context = build_validation_context({
            "C": {
                "backend": "neo4j", "dataset_sha256": DATASET,
                "result_count": 1, "fallback_reason": "", "constraint_ids": ["constr_1"],
            }
        }, expected_dataset_sha256=DATASET)
        result = self.validate(context)
        self.assertEqual("VERIFIED", result["validation_context"]["status"])
        self.assertEqual("NOT_EVALUATED", result["rules"][0]["status"])
        self.assertEqual(["test"], result["rules"][0]["notes"])

    def test_wrong_dataset_hash_returns_error_report(self) -> None:
        context = build_validation_context({}, expected_dataset_sha256="b" * 64)
        result = self.validate(context)
        self.assertEqual("ERROR", result["decision"])
        self.assertEqual("ERROR", result["validation_context"]["status"])
        self.assertEqual("CONTEXT#integrity", result["rules"][0]["rule_id"])


if __name__ == "__main__":
    unittest.main()
