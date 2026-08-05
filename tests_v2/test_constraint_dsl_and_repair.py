from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.validation.v2.engine import ValidationEngine


def dsl_rule(rule_id: str, tags: list[str], checks: list[dict]) -> dict:
    return {
        "rule_id": rule_id,
        "constraint_id": rule_id.split("#", 1)[0],
        "source_sha256": "0" * 64,
        "title": "Reviewed DSL rule",
        "severity": "error",
        "policy": "must",
        "backend": "dsl",
        "implementation": {
            "status": "implemented",
            "plugin": "constraint_dsl",
            "reason": "reviewed test rule",
        },
        "selector": {"tags": tags, "mode": "any"},
        "parameters": {},
        "completeness": {
            "requires": ["well_formed_xml"],
            "on_missing": "not_evaluated",
        },
        "dependencies": [],
        "bindings": [],
        "formal_spec": {
            "language": "autosar-constraint-ir/1.0",
            "status": "reviewed",
            "coverage": "full",
            "rule_family": "value_domain",
            "checks": checks,
        },
    }


class ConstraintDslAndRepairTests(unittest.TestCase):
    def validate(self, documents: dict[str, str], rules: list[dict]) -> dict:
        with tempfile.TemporaryDirectory() as directory:
            paths = []
            for name, xml in documents.items():
                path = Path(directory) / name
                path.write_text(xml, encoding="utf-8")
                paths.append(path)
            return ValidationEngine({"rules": rules}).validate(paths)

    def test_reports_every_dsl_violation_and_builds_llm_repair_payload(self) -> None:
        xml = """<AUTOSAR><SW-BASE-TYPE><SHORT-NAME>T</SHORT-NAME>
        <CATEGORY>BAD</CATEGORY><CATEGORY>ALSO_BAD</CATEGORY>
        </SW-BASE-TYPE></AUTOSAR>"""
        report = self.validate({"input.arxml": xml}, [dsl_rule(
            "constr_1011#r1",
            ["SW-BASE-TYPE"],
            [{
                "op": "value_domain",
                "path": "CATEGORY",
                "allowed": ["FIXED_LENGTH", "VARIABLE_LENGTH"],
                "message": "Unsupported SwBaseType category.",
            }],
        )])
        self.assertEqual("FAIL", report["decision"])
        self.assertEqual(2, report["summary"]["finding_count"])
        self.assertEqual(2, report["repair"]["action_count"])
        self.assertTrue(all(item["location"]["line"] for item in report["findings"]))
        self.assertIn("Apply all non-conflicting actions", report["repair"]["llm_prompt"])

    def test_collects_xml_syntax_errors_from_every_document(self) -> None:
        report = self.validate({
            "a.arxml": "<AUTOSAR><A></AUTOSAR>",
            "b.arxml": "<AUTOSAR><B></AUTOSAR>",
        }, [])
        self.assertEqual("ERROR", report["decision"])
        self.assertGreaterEqual(report["summary"]["finding_count"], 2)
        files = {Path(item["location"]["file"]).name for item in report["findings"]}
        self.assertEqual({"a.arxml", "b.arxml"}, files)
        self.assertEqual(report["summary"]["finding_count"], report["repair"]["action_count"])

    def test_exactly_one_alternative_is_enforced(self) -> None:
        xml = "<AUTOSAR><VALUE-GROUP><SHORT-NAME>V</SHORT-NAME></VALUE-GROUP></AUTOSAR>"
        report = self.validate({"input.arxml": xml}, [dsl_rule(
            "constr_1243#r1",
            ["VALUE-GROUP"],
            [{
                "op": "mutually_exclusive",
                "paths": ["VF", "VT"],
                "min_present": 1,
                "max_present": 1,
                "message": "Exactly one of VF and VT is required.",
            }],
        )])
        self.assertEqual("FAIL", report["decision"])
        self.assertEqual("choose_alternative", report["repair"]["actions"][0]["action"])


if __name__ == "__main__":
    unittest.main()
