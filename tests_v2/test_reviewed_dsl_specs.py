from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.validation.v2.engine import ValidationEngine


class ReviewedDslSpecsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        root = Path(__file__).resolve().parents[1]
        cls.plan = json.loads(
            (root / "src/generate_formal_constraints/v2/validation_plan.json").read_text(
                encoding="utf-8"
            )
        )
        cls.rules = {rule["constraint_id"]: rule for rule in cls.plan["rules"]}

    def validate(self, xml: str, *constraint_ids: str) -> dict:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.arxml"
            path.write_text(xml, encoding="utf-8")
            rules = [self.rules[item] for item in constraint_ids]
            return ValidationEngine({"rules": rules}).validate([path])

    def test_profile_rule_reports_range_and_modulo_without_stopping(self) -> None:
        report = self.validate(
            """<AUTOSAR><END-TO-END-DESCRIPTION><SHORT-NAME>E</SHORT-NAME>
            <CATEGORY>PROFILE_01</CATEGORY><CRC-OFFSET>65537</CRC-OFFSET>
            </END-TO-END-DESCRIPTION></AUTOSAR>""",
            "constr_1114",
        )
        self.assertEqual("FAIL", report["decision"])
        self.assertEqual(2, report["summary"]["finding_count"])
        self.assertEqual({"numeric_range", "numeric_modulo"}, {
            finding["evidence"]["dsl_operator"] for finding in report["findings"]
        })

    def test_role_specific_rule_does_not_fire_outside_role_wrapper(self) -> None:
        outside = self.validate(
            """<AUTOSAR><VARIABLE-DATA-PROTOTYPE><SHORT-NAME>V</SHORT-NAME>
            <SW-DATA-DEF-PROPS><SW-DATA-DEF-PROPS-VARIANTS><SW-DATA-DEF-PROPS-CONDITIONAL>
            <SW-IMPL-POLICY>QUEUED</SW-IMPL-POLICY>
            </SW-DATA-DEF-PROPS-CONDITIONAL></SW-DATA-DEF-PROPS-VARIANTS></SW-DATA-DEF-PROPS>
            </VARIABLE-DATA-PROTOTYPE></AUTOSAR>""",
            "constr_2038",
        )
        self.assertEqual("PASS", outside["decision"])
        inside = self.validate(
            """<AUTOSAR><IMPLICIT-INTER-RUNNABLE-VARIABLES>
            <VARIABLE-DATA-PROTOTYPE><SHORT-NAME>V</SHORT-NAME>
            <SW-DATA-DEF-PROPS><SW-DATA-DEF-PROPS-VARIANTS><SW-DATA-DEF-PROPS-CONDITIONAL>
            <SW-IMPL-POLICY>QUEUED</SW-IMPL-POLICY>
            </SW-DATA-DEF-PROPS-CONDITIONAL></SW-DATA-DEF-PROPS-VARIANTS></SW-DATA-DEF-PROPS>
            </VARIABLE-DATA-PROTOTYPE></IMPLICIT-INTER-RUNNABLE-VARIABLES></AUTOSAR>""",
            "constr_2038",
        )
        self.assertEqual("FAIL", inside["decision"])

    def test_missing_conditional_antecedent_is_not_treated_as_other_value(self) -> None:
        report = self.validate(
            """<AUTOSAR><APPLICATION-PRIMITIVE-DATA-TYPE><SHORT-NAME>T</SHORT-NAME>
            <SW-DATA-DEF-PROPS><INVALID-VALUE><NUMERICAL-VALUE-SPECIFICATION/></INVALID-VALUE></SW-DATA-DEF-PROPS>
            </APPLICATION-PRIMITIVE-DATA-TYPE></AUTOSAR>""",
            "constr_1241",
        )
        self.assertEqual("PASS", report["decision"])


if __name__ == "__main__":
    unittest.main()
