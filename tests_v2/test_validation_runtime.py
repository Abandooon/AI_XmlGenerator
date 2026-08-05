from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.validation.v2.engine import ValidationEngine


def rule(rule_id: str, plugin: str | None, tags: list[str], requires: list[str] | None = None, parameters: dict | None = None) -> dict:
    constraint_id = rule_id.split("#", 1)[0]
    return {
        "rule_id": rule_id,
        "constraint_id": constraint_id,
        "source_sha256": "0" * 64,
        "title": rule_id,
        "severity": "error",
        "policy": "must",
        "backend": "python",
        "implementation": {"status": "implemented" if plugin else "planned", "plugin": plugin, "reason": "planned" if not plugin else ""},
        "selector": {"tags": tags, "mode": "any"},
        "parameters": parameters or {},
        "completeness": {"requires": requires or ["well_formed_xml"], "on_missing": "not_evaluated"},
        "dependencies": [],
        "bindings": [],
    }


class ValidationRuntimeTest(unittest.TestCase):
    def run_xml(self, xml: str, rules: list[dict], reference_scope: str = "complete") -> dict:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.arxml"
            path.write_text(xml, encoding="utf-8")
            return ValidationEngine({"rules": rules}, reference_scope).validate([path])

    def test_observable_violations_fail(self) -> None:
        xml = """<AUTOSAR><CATEGORY>BAD</CATEGORY><P-PORT-PROTOTYPE><SHORT-NAME>P</SHORT-NAME><VARIATION-POINT><POST-BUILD-VARIANT-CONDITIONS/></VARIATION-POINT></P-PORT-PROTOTYPE></AUTOSAR>"""
        result = self.run_xml(xml, [
            rule("test_value_domain#r1", "value_domain", ["CATEGORY"], parameters={"value_tag": "CATEGORY", "allowed": ["GOOD"]}),
            rule("TPS_SWCT_01447#r1", "port_forbids_postbuild_variation", ["P-PORT-PROTOTYPE"]),
        ])
        self.assertEqual("FAIL", result["decision"])
        self.assertEqual(2, result["summary"]["FAIL"])

    def test_missing_complete_scope_is_not_evaluated(self) -> None:
        xml = """<AUTOSAR><SW-COMPONENT-PROTOTYPE><SHORT-NAME>C</SHORT-NAME><TYPE-TREF>/Pkg/Type</TYPE-TREF></SW-COMPONENT-PROTOTYPE></AUTOSAR>"""
        result = self.run_xml(xml, [rule("TPS_SWCT_01035#r1", "component_prototype_type_reference", ["SW-COMPONENT-PROTOTYPE"], ["well_formed_xml", "complete_reference_scope"])], "partial")
        self.assertEqual("INCOMPLETE", result["decision"])
        self.assertEqual("NOT_EVALUATED", result["rules"][0]["status"])

    def test_planned_applicable_rule_is_not_evaluated(self) -> None:
        xml = "<AUTOSAR><PASS-THROUGH-SW-CONNECTOR><SHORT-NAME>C</SHORT-NAME></PASS-THROUGH-SW-CONNECTOR></AUTOSAR>"
        result = self.run_xml(xml, [rule("constr_1252#r1", None, ["PASS-THROUGH-SW-CONNECTOR"])])
        self.assertEqual("INCOMPLETE", result["decision"])

    def test_planned_non_applicable_rule_passes(self) -> None:
        result = self.run_xml("<AUTOSAR/>", [rule("constr_1252#r1", None, ["PASS-THROUGH-SW-CONNECTOR"])])
        self.assertEqual("PASS", result["decision"])

    def test_composition_cycle_fails(self) -> None:
        xml = """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>Pkg</SHORT-NAME><ELEMENTS>
        <COMPOSITION-SW-COMPONENT-TYPE><SHORT-NAME>A</SHORT-NAME><COMPONENTS><SW-COMPONENT-PROTOTYPE><SHORT-NAME>BRole</SHORT-NAME><TYPE-TREF>/Pkg/B</TYPE-TREF></SW-COMPONENT-PROTOTYPE></COMPONENTS></COMPOSITION-SW-COMPONENT-TYPE>
        <COMPOSITION-SW-COMPONENT-TYPE><SHORT-NAME>B</SHORT-NAME><COMPONENTS><SW-COMPONENT-PROTOTYPE><SHORT-NAME>ARole</SHORT-NAME><TYPE-TREF>/Pkg/A</TYPE-TREF></SW-COMPONENT-PROTOTYPE></COMPONENTS></COMPOSITION-SW-COMPONENT-TYPE>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""
        result = self.run_xml(xml, [rule("constr_1035#r1", "composition_type_acyclic", ["COMPOSITION-SW-COMPONENT-TYPE"], ["well_formed_xml", "complete_reference_scope"])])
        self.assertEqual("FAIL", result["decision"])
        self.assertIn("cycle", result["findings"][0]["message"].lower())


if __name__ == "__main__":
    unittest.main()
