from __future__ import annotations

import json
import unittest
from pathlib import Path


class QualificationFailClosedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        root = Path(__file__).parents[1]
        generated = root / "src/generate_formal_constraints/v2"
        cls.qualification = json.loads((generated / "planned_rule_qualification.json").read_text(encoding="utf-8"))
        cls.qualification_audit = json.loads((generated / "planned_rule_qualification_audit.json").read_text(encoding="utf-8"))
        cls.pipeline_audit = json.loads((generated / "pipeline_audit.json").read_text(encoding="utf-8"))
        plan = json.loads((generated / "validation_plan_dsl.json").read_text(encoding="utf-8"))
        cls.rules = {item["constraint_id"]: item for item in plan["rules"]}

    def test_no_unqualified_planned_rule_remains(self) -> None:
        self.assertEqual(0, self.qualification["planned_rule_count"])
        self.assertEqual([], self.qualification["records"])
        self.assertTrue(self.qualification_audit["valid"])
        self.assertEqual(0, self.qualification_audit["planned_rule_count"])

    def test_graph_rule_requires_complete_reference_scope(self) -> None:
        record = self.rules["constr_1295"]
        self.assertEqual("implemented", record["implementation"]["status"])
        self.assertEqual("data_reference_usage_restrictions", record["implementation"]["plugin"])
        self.assertIn("complete_reference_scope", record["completeness"]["requires"])

    def test_c_symbol_rule_has_a_reviewed_arxml_observable(self) -> None:
        record = self.rules["TPS_SWCT_01431"]
        self.assertEqual("implemented", record["implementation"]["status"])
        self.assertEqual("compu_scale_c_symbol", record["implementation"]["plugin"])
        self.assertEqual(["COMPU-SCALE"], record["selector"]["tags"])

    def test_pipeline_has_exact_full_must_coverage(self) -> None:
        counts = self.pipeline_audit["counts"]
        self.assertTrue(self.pipeline_audit["valid"])
        self.assertEqual(554, counts["must_validate"])
        self.assertEqual(554, counts["validation_rules"])
        self.assertEqual(554, counts["implemented_rules"])
        self.assertEqual(0, counts["planned_rules"])
        self.assertEqual(554, len(self.rules))
        self.assertTrue(all(item["implementation"]["status"] == "implemented" for item in self.rules.values()))


if __name__ == "__main__":
    unittest.main()
