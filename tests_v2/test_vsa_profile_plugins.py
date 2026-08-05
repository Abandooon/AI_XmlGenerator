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


class VsaProfilePluginTests(unittest.TestCase):
    def validate(self, xml: str, validation_rule: dict) -> dict:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.arxml"
            path.write_text(xml, encoding="utf-8")
            return ValidationEngine({"rules": [validation_rule]}).validate([path])

    def test_application_linear_requires_maximum(self) -> None:
        xml = """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>P</SHORT-NAME><ELEMENTS>
        <APPLICATION-PRIMITIVE-DATA-TYPE><SHORT-NAME>Leaf</SHORT-NAME><CATEGORY>VALUE</CATEGORY></APPLICATION-PRIMITIVE-DATA-TYPE>
        <APPLICATION-ARRAY-DATA-TYPE><SHORT-NAME>A</SHORT-NAME><DYNAMIC-ARRAY-SIZE-PROFILE>VSA_LINEAR</DYNAMIC-ARRAY-SIZE-PROFILE><ELEMENTS>
          <APPLICATION-ARRAY-ELEMENT><SHORT-NAME>E</SHORT-NAME><CATEGORY>VALUE</CATEGORY><ARRAY-SIZE-HANDLING>ALL-INDICES-SAME-ARRAY-SIZE</ARRAY-SIZE-HANDLING><ARRAY-SIZE-SEMANTICS>VARIABLE-SIZE</ARRAY-SIZE-SEMANTICS><TYPE-TREF>/P/Leaf</TYPE-TREF></APPLICATION-ARRAY-ELEMENT>
        </ELEMENTS></APPLICATION-ARRAY-DATA-TYPE></ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""
        result = self.validate(xml, rule("constr_1314", "application_vsa_profile", ["APPLICATION-ARRAY-DATA-TYPE"]))
        self.assertEqual("FAIL", result["decision"])

    def test_implementation_linear_payload_requires_inner_size(self) -> None:
        xml = """<AUTOSAR><IMPLEMENTATION-DATA-TYPE><SHORT-NAME>I</SHORT-NAME><DYNAMIC-ARRAY-SIZE-PROFILE>VSA_LINEAR</DYNAMIC-ARRAY-SIZE-PROFILE><SUB-ELEMENTS>
        <IMPLEMENTATION-DATA-TYPE-ELEMENT><SHORT-NAME>Size</SHORT-NAME><CATEGORY>VALUE</CATEGORY></IMPLEMENTATION-DATA-TYPE-ELEMENT>
        <IMPLEMENTATION-DATA-TYPE-ELEMENT><SHORT-NAME>Payload</SHORT-NAME><CATEGORY>ARRAY</CATEGORY><SUB-ELEMENTS>
          <IMPLEMENTATION-DATA-TYPE-ELEMENT><SHORT-NAME>D</SHORT-NAME><ARRAY-SIZE-SEMANTICS>VARIABLE-SIZE</ARRAY-SIZE-SEMANTICS><ARRAY-SIZE-HANDLING>ALL-INDICES-SAME-ARRAY-SIZE</ARRAY-SIZE-HANDLING></IMPLEMENTATION-DATA-TYPE-ELEMENT>
        </SUB-ELEMENTS></IMPLEMENTATION-DATA-TYPE-ELEMENT></SUB-ELEMENTS></IMPLEMENTATION-DATA-TYPE></AUTOSAR>"""
        result = self.validate(xml, rule("constr_1318", "implementation_vsa_profile", ["IMPLEMENTATION-DATA-TYPE"]))
        self.assertEqual("FAIL", result["decision"])

    def test_payload_is_second_array_element(self) -> None:
        xml = """<AUTOSAR><IMPLEMENTATION-DATA-TYPE><DYNAMIC-ARRAY-SIZE-PROFILE>VSA_LINEAR</DYNAMIC-ARRAY-SIZE-PROFILE><SUB-ELEMENTS>
        <IMPLEMENTATION-DATA-TYPE-ELEMENT><CATEGORY>VALUE</CATEGORY></IMPLEMENTATION-DATA-TYPE-ELEMENT>
        <IMPLEMENTATION-DATA-TYPE-ELEMENT><CATEGORY>STRUCTURE</CATEGORY></IMPLEMENTATION-DATA-TYPE-ELEMENT>
        </SUB-ELEMENTS></IMPLEMENTATION-DATA-TYPE></AUTOSAR>"""
        result = self.validate(xml, rule("TPS_SWCT_01649", "vsa_payload_and_indicator_shape", ["IMPLEMENTATION-DATA-TYPE"]))
        self.assertEqual("FAIL", result["decision"])

    def test_rectangular_indicator_size_equals_dimensions(self) -> None:
        xml = """<AUTOSAR><IMPLEMENTATION-DATA-TYPE><DYNAMIC-ARRAY-SIZE-PROFILE>VSA_RECTANGULAR</DYNAMIC-ARRAY-SIZE-PROFILE><SUB-ELEMENTS>
        <IMPLEMENTATION-DATA-TYPE-ELEMENT><CATEGORY>ARRAY</CATEGORY><ARRAY-SIZE>2</ARRAY-SIZE></IMPLEMENTATION-DATA-TYPE-ELEMENT>
        <IMPLEMENTATION-DATA-TYPE-ELEMENT><CATEGORY>ARRAY</CATEGORY><SUB-ELEMENTS><IMPLEMENTATION-DATA-TYPE-ELEMENT><CATEGORY>ARRAY</CATEGORY><ARRAY-SIZE>4</ARRAY-SIZE></IMPLEMENTATION-DATA-TYPE-ELEMENT></SUB-ELEMENTS></IMPLEMENTATION-DATA-TYPE-ELEMENT>
        </SUB-ELEMENTS></IMPLEMENTATION-DATA-TYPE></AUTOSAR>"""
        result = self.validate(xml, rule("TPS_SWCT_01648", "vsa_payload_and_indicator_shape", ["IMPLEMENTATION-DATA-TYPE"]))
        self.assertEqual("FAIL", result["decision"])
        self.assertEqual(1, result["findings"][0]["evidence"]["expected"])

    def test_indicator_capacity_uses_grounded_base_type(self) -> None:
        xml = """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>P</SHORT-NAME><ELEMENTS>
        <SW-BASE-TYPE><SHORT-NAME>u2</SHORT-NAME><BASE-TYPE-SIZE>2</BASE-TYPE-SIZE><BASE-TYPE-ENCODING>UNSIGNED</BASE-TYPE-ENCODING></SW-BASE-TYPE>
        <APPLICATION-PRIMITIVE-DATA-TYPE><SHORT-NAME>Leaf</SHORT-NAME><CATEGORY>VALUE</CATEGORY></APPLICATION-PRIMITIVE-DATA-TYPE>
        <APPLICATION-ARRAY-DATA-TYPE><SHORT-NAME>A</SHORT-NAME><DYNAMIC-ARRAY-SIZE-PROFILE>VSA_LINEAR</DYNAMIC-ARRAY-SIZE-PROFILE><ELEMENTS><APPLICATION-ARRAY-ELEMENT><SHORT-NAME>E</SHORT-NAME><MAX-NUMBER-OF-ELEMENTS>4</MAX-NUMBER-OF-ELEMENTS><TYPE-TREF>/P/Leaf</TYPE-TREF></APPLICATION-ARRAY-ELEMENT></ELEMENTS></APPLICATION-ARRAY-DATA-TYPE>
        <IMPLEMENTATION-DATA-TYPE><SHORT-NAME>I</SHORT-NAME><SUB-ELEMENTS><IMPLEMENTATION-DATA-TYPE-ELEMENT><SHORT-NAME>Size</SHORT-NAME><CATEGORY>VALUE</CATEGORY><SW-DATA-DEF-PROPS><BASE-TYPE-REF>/P/u2</BASE-TYPE-REF></SW-DATA-DEF-PROPS></IMPLEMENTATION-DATA-TYPE-ELEMENT><IMPLEMENTATION-DATA-TYPE-ELEMENT><SHORT-NAME>Payload</SHORT-NAME><CATEGORY>ARRAY</CATEGORY></IMPLEMENTATION-DATA-TYPE-ELEMENT></SUB-ELEMENTS></IMPLEMENTATION-DATA-TYPE>
        <DATA-TYPE-MAP><APPLICATION-DATA-TYPE-REF>/P/A</APPLICATION-DATA-TYPE-REF><IMPLEMENTATION-DATA-TYPE-REF>/P/I</IMPLEMENTATION-DATA-TYPE-REF></DATA-TYPE-MAP>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""
        result = self.validate(xml, rule("TPS_SWCT_01618", "vsa_indicator_capacity", ["DATA-TYPE-MAP"]))
        self.assertEqual("FAIL", result["decision"])
        self.assertEqual("3", result["findings"][0]["evidence"]["capacity"])


if __name__ == "__main__":
    unittest.main()
