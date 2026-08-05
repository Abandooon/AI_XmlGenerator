from __future__ import annotations

import unittest
from pathlib import Path

from src.validation.v2.service import GeneratedArxmlValidationService


class ManualServiceLocationTests(unittest.TestCase):
    def test_manual_review_locations_do_not_leak_temporary_paths(self) -> None:
        root = Path(__file__).resolve().parents[1]
        service = GeneratedArxmlValidationService(
            plan_path=root / "src/generate_formal_constraints/v2/validation_plan.json",
            xsd_path=None,
            reference_scope="partial",
        )
        xml = """<AUTOSAR><APPLICATION-SW-COMPONENT-TYPE>
        <SHORT-NAME>A</SHORT-NAME></APPLICATION-SW-COMPONENT-TYPE></AUTOSAR>"""
        report = service.validate_bundle({"components": {"A": xml}, "interfaces": {}})
        review = next(
            item for item in report["manual_review"]
            if item["constraint_id"] == "TPS_SWCT_01000"
        )
        self.assertEqual({"components/A.arxml"}, {
            location["file"] for location in review["locations"]
        })


if __name__ == "__main__":
    unittest.main()
