from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.validation.v2.engine import ValidationEngine


def rule(cid: str, plugin: str, tags: list[str]) -> dict:
    return {
        "rule_id": f"{cid}#r1", "constraint_id": cid, "title": cid,
        "severity": "error", "policy": "must",
        "implementation": {"status": "implemented", "plugin": plugin},
        "selector": {"tags": tags, "mode": "any"}, "parameters": {},
        "completeness": {"requires": ["well_formed_xml", "complete_reference_scope"], "on_missing": "not_evaluated"},
        "dependencies": [], "bindings": [],
    }


class OrderingPluginTests(unittest.TestCase):
    def validate(self, xml: str, validation_rule: dict) -> dict:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.arxml"
            path.write_text(xml, encoding="utf-8")
            return ValidationEngine({"rules": [validation_rule]}).validate([path])

    def test_array_dimensions_are_compared_outer_to_inner(self) -> None:
        xml = """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>P</SHORT-NAME><ELEMENTS>
        <APPLICATION-PRIMITIVE-DATA-TYPE><SHORT-NAME>Leaf</SHORT-NAME><CATEGORY>VALUE</CATEGORY></APPLICATION-PRIMITIVE-DATA-TYPE>
        <APPLICATION-ARRAY-DATA-TYPE><SHORT-NAME>A</SHORT-NAME><ELEMENTS><APPLICATION-ARRAY-ELEMENT><SHORT-NAME>AE</SHORT-NAME><MAX-NUMBER-OF-ELEMENTS>2</MAX-NUMBER-OF-ELEMENTS><ARRAY-SIZE-SEMANTICS>FIXED-SIZE</ARRAY-SIZE-SEMANTICS><TYPE-TREF>/P/Leaf</TYPE-TREF></APPLICATION-ARRAY-ELEMENT></ELEMENTS></APPLICATION-ARRAY-DATA-TYPE>
        <IMPLEMENTATION-DATA-TYPE><SHORT-NAME>I</SHORT-NAME><CATEGORY>ARRAY</CATEGORY><SUB-ELEMENTS><IMPLEMENTATION-DATA-TYPE-ELEMENT><SHORT-NAME>IE</SHORT-NAME><ARRAY-SIZE>3</ARRAY-SIZE><ARRAY-SIZE-SEMANTICS>FIXED-SIZE</ARRAY-SIZE-SEMANTICS></IMPLEMENTATION-DATA-TYPE-ELEMENT></SUB-ELEMENTS></IMPLEMENTATION-DATA-TYPE>
        <DATA-TYPE-MAP><APPLICATION-DATA-TYPE-REF>/P/A</APPLICATION-DATA-TYPE-REF><IMPLEMENTATION-DATA-TYPE-REF>/P/I</IMPLEMENTATION-DATA-TYPE-REF></DATA-TYPE-MAP>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""
        result = self.validate(xml, rule("TPS_SWCT_01256", "array_dimension_mapping_order", ["DATA-TYPE-MAP"]))
        self.assertEqual("FAIL", result["decision"])
        self.assertEqual(1, result["findings"][0]["evidence"]["dimension"])

    def test_value_axis_precedence_records_effective_unit(self) -> None:
        xml = """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>P</SHORT-NAME><ELEMENTS>
        <UNIT><SHORT-NAME>Low</SHORT-NAME></UNIT><UNIT><SHORT-NAME>High</SHORT-NAME></UNIT>
        <APPLICATION-PRIMITIVE-DATA-TYPE><SHORT-NAME>V</SHORT-NAME><SW-DATA-DEF-PROPS><UNIT-REF>/P/High</UNIT-REF></SW-DATA-DEF-PROPS></APPLICATION-PRIMITIVE-DATA-TYPE>
        <SW-DATA-DEF-PROPS><SHORT-NAME>Props</SHORT-NAME><UNIT-REF>/P/Low</UNIT-REF><VALUE-AXIS-DATA-TYPE-REF>/P/V</VALUE-AXIS-DATA-TYPE-REF></SW-DATA-DEF-PROPS>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""
        result = self.validate(xml, rule("TPS_SWCT_01497", "value_axis_precedence", ["SW-DATA-DEF-PROPS"]))
        self.assertEqual("PASS", result["decision"])
        observations = result["rules"][0]["observations"]
        chosen = [item for item in observations if item["subject"].endswith("/Props")][0]
        self.assertEqual("valueAxisDataType.unit", chosen["effective_source"])
        self.assertEqual("/P/High", chosen["effective_value"])

    def test_unresolved_precedence_reference_is_not_evaluated(self) -> None:
        xml = "<AUTOSAR><SW-DATA-DEF-PROPS><VALUE-AXIS-DATA-TYPE-REF>/Missing</VALUE-AXIS-DATA-TYPE-REF></SW-DATA-DEF-PROPS></AUTOSAR>"
        result = self.validate(xml, rule("TPS_SWCT_01497", "value_axis_precedence", ["SW-DATA-DEF-PROPS"]))
        self.assertEqual("INCOMPLETE", result["decision"])
        self.assertEqual("NOT_EVALUATED", result["rules"][0]["status"])

    def test_comspec_initial_value_supersedes_prototype_value(self) -> None:
        xml = """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>P</SHORT-NAME><ELEMENTS>
        <VARIABLE-DATA-PROTOTYPE><SHORT-NAME>D</SHORT-NAME><INIT-VALUE><NUMERICAL-VALUE-SPECIFICATION><VALUE>1</VALUE></NUMERICAL-VALUE-SPECIFICATION></INIT-VALUE></VARIABLE-DATA-PROTOTYPE>
        <NONQUEUED-RECEIVER-COM-SPEC><SHORT-NAME>C</SHORT-NAME><DATA-ELEMENT-REF>/P/D</DATA-ELEMENT-REF><INIT-VALUE><NUMERICAL-VALUE-SPECIFICATION><VALUE>2</VALUE></NUMERICAL-VALUE-SPECIFICATION></INIT-VALUE></NONQUEUED-RECEIVER-COM-SPEC>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""
        result = self.validate(xml, rule("TPS_SWCT_01182", "initial_value_precedence", ["NONQUEUED-RECEIVER-COM-SPEC"]))
        self.assertEqual("PASS", result["decision"])
        self.assertEqual(2, result["rules"][0]["observations"][0]["effective_level"])


if __name__ == "__main__":
    unittest.main()
