from __future__ import annotations

import json
import unittest
from pathlib import Path

from src.generate_formal_constraints.v2.qualify_planned_rules import build_ledger, load_jsonl


class PlannedRuleQualificationTests(unittest.TestCase):
    def test_every_planned_rule_has_one_fail_closed_qualification(self) -> None:
        root = Path(__file__).parents[1]
        formal = root / "src/generate_formal_constraints/v2"
        work = root / "src/kg_builder/doc_constr_parser/v2/work"
        plan = json.loads((formal / "validation_plan.json").read_text(encoding="utf-8"))
        ledger, audit = build_ledger(
            plan,
            load_jsonl(work / "semantic_curation.jsonl"),
            load_jsonl(work / "binding_decisions.jsonl"),
        )
        self.assertTrue(audit["valid"])
        planned_rule_ids = {
            item["rule_id"]
            for item in plan["rules"]
            if item.get("implementation", {}).get("status") != "implemented"
        }
        self.assertEqual(len(planned_rule_ids), ledger["planned_rule_count"])
        self.assertEqual(planned_rule_ids, {item["rule_id"] for item in ledger["records"]})
        self.assertTrue(all(item["current_disposition"] == "remain_not_evaluated" for item in ledger["records"]))


if __name__ == "__main__":
    unittest.main()
