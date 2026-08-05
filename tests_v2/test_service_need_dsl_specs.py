from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.validation.v2.engine import ValidationEngine


class ServiceNeedDslSpecsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        root = Path(__file__).resolve().parents[1]
        plan = json.loads(
            (root / "src/generate_formal_constraints/v2/validation_plan.json").read_text(
                encoding="utf-8"
            )
        )
        cls.rule = next(
            item for item in plan["rules"] if item["constraint_id"] == "TPS_SWCT_02505"
        )

    def validate(self, body: str) -> dict:
        xml = f"<AUTOSAR><SWC-SERVICE-DEPENDENCY><SHORT-NAME>D</SHORT-NAME>{body}</SWC-SERVICE-DEPENDENCY></AUTOSAR>"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.arxml"
            path.write_text(xml, encoding="utf-8")
            return ValidationEngine({"rules": [self.rule]}).validate([path])

    def test_missing_required_role_fails(self) -> None:
        report = self.validate(
            "<SERVICE-NEEDS><FUNCTION-INHIBITION-NEEDS/></SERVICE-NEEDS>"
        )
        self.assertEqual("FAIL", report["decision"])
        self.assertTrue(any(action["expected"] == {"min": 1, "max": 1} for action in report["repair"]["actions"]))

    def test_exact_role_passes_and_other_service_need_is_not_applicable(self) -> None:
        valid = self.validate(
            """<ASSIGNED-PORTS><ROLE-BASED-PORT-ASSIGNMENT><ROLE>FunctionInhibition</ROLE></ROLE-BASED-PORT-ASSIGNMENT></ASSIGNED-PORTS>
            <SERVICE-NEEDS><FUNCTION-INHIBITION-NEEDS/></SERVICE-NEEDS>"""
        )
        self.assertEqual("PASS", valid["decision"])
        other = self.validate(
            "<SERVICE-NEEDS><NV-BLOCK-NEEDS/></SERVICE-NEEDS>"
        )
        self.assertEqual("PASS", other["decision"])

    def test_wrong_role_reports_domain_and_missing_required_role(self) -> None:
        report = self.validate(
            """<ASSIGNED-PORTS><ROLE-BASED-PORT-ASSIGNMENT><ROLE>WrongRole</ROLE></ROLE-BASED-PORT-ASSIGNMENT></ASSIGNED-PORTS>
            <SERVICE-NEEDS><FUNCTION-INHIBITION-NEEDS/></SERVICE-NEEDS>"""
        )
        self.assertEqual("FAIL", report["decision"])
        self.assertEqual(2, report["summary"]["finding_count"])


if __name__ == "__main__":
    unittest.main()
