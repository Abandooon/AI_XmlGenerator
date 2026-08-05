from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.validation.v2.context import ValidationContextError, build_validation_context
from src.validation.v2.engine import ValidationEngine

DATASET = "c" * 64
TRACE = {
    "C": {
        "backend": "neo4j", "dataset_sha256": DATASET,
        "result_count": 1, "fallback_reason": "", "constraint_ids": ["constr_1"],
    }
}


def rule() -> dict:
    return {
        "rule_id": "constr_1#r1", "constraint_id": "constr_1",
        "source_sha256": "0" * 64, "title": "declared intent rule",
        "severity": "error", "policy": "must", "backend": "dsl",
        "implementation": {"status": "implemented", "plugin": "constraint_dsl", "reason": "test"},
        "selector": {"tags": ["TARGET"], "mode": "any"},
        "completeness": {"requires": ["well_formed_xml", "generation_intent"], "on_missing": "not_evaluated"},
        "dependencies": [], "bindings": [],
        "formal_spec": {
            "language": "autosar-constraint-ir/1.0", "status": "reviewed", "coverage": "full",
            "activation": {"requires_declared_constraint": True, "requires_declared_targets": True},
            "checks": [{"op": "forbidden", "path": "BAD", "message": "BAD is forbidden"}],
        },
    }


class ValidationIntentSeparationTests(unittest.TestCase):
    def validate(self, context):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.arxml"
            path.write_text(
                "<AUTOSAR><TARGET><SHORT-NAME>A</SHORT-NAME><BAD/></TARGET>"
                "<TARGET><SHORT-NAME>B</SHORT-NAME></TARGET></AUTOSAR>",
                encoding="utf-8",
            )
            return ValidationEngine(
                {"rules": [rule()]}, expected_dataset_sha256=DATASET
            ).validate([path], validation_context=context)

    def test_retrieval_selection_is_not_generation_intent(self) -> None:
        context = build_validation_context(TRACE, expected_dataset_sha256=DATASET)
        result = self.validate(context)
        self.assertEqual("NOT_EVALUATED", result["rules"][0]["status"])
        self.assertIn("explicitly declared", result["rules"][0]["notes"][0])

    def test_explicit_constraint_intent_requires_real_retrieval_and_unlocks_capability(self) -> None:
        context = build_validation_context(
            TRACE, expected_dataset_sha256=DATASET, declared_constraint_ids=["constr_1"]
        )
        result = self.validate(context)
        self.assertIn("no exact ARXML", result["rules"][0]["notes"][0])

    def test_exact_declared_target_overrides_broad_selector(self) -> None:
        context = build_validation_context(
            TRACE, expected_dataset_sha256=DATASET,
            declared_constraint_ids=["constr_1"],
            declared_targets={"constr_1": ["/B"]},
        )
        result = self.validate(context)
        self.assertEqual("PASS", result["rules"][0]["status"])
        self.assertEqual(1, result["rules"][0]["checked_count"])

    def test_unresolved_declared_target_is_fail_closed(self) -> None:
        context = build_validation_context(
            TRACE, expected_dataset_sha256=DATASET,
            declared_constraint_ids=["constr_1"],
            declared_targets={"constr_1": ["/Missing"]},
        )
        result = self.validate(context)
        self.assertEqual("NOT_EVALUATED", result["rules"][0]["status"])
        self.assertIn("unresolved", result["rules"][0]["notes"][0])

    def test_explicit_constraint_missing_from_trace_is_rejected(self) -> None:
        with self.assertRaises(ValidationContextError):
            build_validation_context(
                TRACE, expected_dataset_sha256=DATASET, declared_constraint_ids=["constr_2"]
            )


if __name__ == "__main__":
    unittest.main()
