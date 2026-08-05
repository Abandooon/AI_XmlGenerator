from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.validation.v2.engine import ValidationEngine


class ManualReviewDecisionTests(unittest.TestCase):
    def test_applicable_manual_obligation_prevents_false_pass(self) -> None:
        root = Path(__file__).resolve().parents[1]
        plan = json.loads(
            (root / "src/generate_formal_constraints/v2/validation_plan.json").read_text(
                encoding="utf-8"
            )
        )
        manual_only = {"rules": [], "manual_review": plan["manual_review"]}
        xml = "<AUTOSAR><APPLICATION-SW-COMPONENT-TYPE><SHORT-NAME>A</SHORT-NAME></APPLICATION-SW-COMPONENT-TYPE></AUTOSAR>"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.arxml"
            path.write_text(xml, encoding="utf-8")
            report = ValidationEngine(manual_only).validate([path])
        self.assertEqual("INCOMPLETE", report["decision"])
        self.assertFalse(report["valid"])
        self.assertGreater(report["summary"]["manual_review_applicable"], 0)


if __name__ == "__main__":
    unittest.main()
