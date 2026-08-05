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
        "completeness": {
            "requires": ["well_formed_xml", "complete_reference_scope"],
            "on_missing": "not_evaluated",
        },
        "dependencies": [], "bindings": [],
    }


class TypeSemanticsPluginTests(unittest.TestCase):
    def validate(self, xml: str, validation_rule: dict) -> dict:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.arxml"
            path.write_text(xml, encoding="utf-8")
            return ValidationEngine({"rules": [validation_rule]}).validate([path])

    def test_application_category_matches_metamodel_kind(self) -> None:
        invalid = self.validate(
            "<AUTOSAR><APPLICATION-PRIMITIVE-DATA-TYPE><SHORT-NAME>T</SHORT-NAME>"
            "<CATEGORY>STRUCTURE</CATEGORY></APPLICATION-PRIMITIVE-DATA-TYPE></AUTOSAR>",
            rule("constr_1008", "application_category_kind", ["APPLICATION-PRIMITIVE-DATA-TYPE"]),
        )
        self.assertEqual("FAIL", invalid["decision"])
        self.assertEqual("CATEGORY", invalid["findings"][0]["location"]["tag"])

    def test_port_defined_type_reference_must_end_in_value(self) -> None:
        xml = """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>P</SHORT-NAME><ELEMENTS>
        <IMPLEMENTATION-DATA-TYPE><SHORT-NAME>A</SHORT-NAME><CATEGORY>ARRAY</CATEGORY></IMPLEMENTATION-DATA-TYPE>
        <IMPLEMENTATION-DATA-TYPE><SHORT-NAME>R</SHORT-NAME><CATEGORY>TYPE_REFERENCE</CATEGORY><SW-DATA-DEF-PROPS>
          <SW-DATA-DEF-PROPS-VARIANTS><SW-DATA-DEF-PROPS-CONDITIONAL><IMPLEMENTATION-DATA-TYPE-REF>/P/A</IMPLEMENTATION-DATA-TYPE-REF>
          </SW-DATA-DEF-PROPS-CONDITIONAL></SW-DATA-DEF-PROPS-VARIANTS></SW-DATA-DEF-PROPS></IMPLEMENTATION-DATA-TYPE>
        <PORT-DEFINED-ARGUMENT-VALUE><SHORT-NAME>V</SHORT-NAME><VALUE-TYPE-TREF>/P/R</VALUE-TYPE-TREF></PORT-DEFINED-ARGUMENT-VALUE>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""
        result = self.validate(xml, rule("constr_1150", "port_defined_argument_value_type", ["PORT-DEFINED-ARGUMENT-VALUE"]))
        self.assertEqual("FAIL", result["decision"])
        self.assertEqual("ARRAY", result["findings"][0]["evidence"]["actual"]["resolved"])

    def test_unresolved_type_reference_is_not_evaluated(self) -> None:
        xml = "<AUTOSAR><PORT-DEFINED-ARGUMENT-VALUE><VALUE-TYPE-TREF>/Missing</VALUE-TYPE-TREF></PORT-DEFINED-ARGUMENT-VALUE></AUTOSAR>"
        result = self.validate(xml, rule("constr_1150", "port_defined_argument_value_type", ["PORT-DEFINED-ARGUMENT-VALUE"]))
        self.assertEqual("INCOMPLETE", result["decision"])
        self.assertEqual("NOT_EVALUATED", result["rules"][0]["status"])

    def test_use_array_base_type_requires_mapped_array(self) -> None:
        xml = """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>P</SHORT-NAME><ELEMENTS>
        <APPLICATION-PRIMITIVE-DATA-TYPE><SHORT-NAME>App</SHORT-NAME><CATEGORY>VALUE</CATEGORY></APPLICATION-PRIMITIVE-DATA-TYPE>
        <IMPLEMENTATION-DATA-TYPE><SHORT-NAME>Impl</SHORT-NAME><CATEGORY>VALUE</CATEGORY></IMPLEMENTATION-DATA-TYPE>
        <DATA-TYPE-MAPPING-SET><SHORT-NAME>M</SHORT-NAME><DATA-TYPE-MAPS><DATA-TYPE-MAP>
          <APPLICATION-DATA-TYPE-REF>/P/App</APPLICATION-DATA-TYPE-REF><IMPLEMENTATION-DATA-TYPE-REF>/P/Impl</IMPLEMENTATION-DATA-TYPE-REF>
        </DATA-TYPE-MAP></DATA-TYPE-MAPS></DATA-TYPE-MAPPING-SET>
        <ARGUMENT-DATA-PROTOTYPE><SHORT-NAME>A</SHORT-NAME><TYPE-TREF>/P/App</TYPE-TREF><SERVER-ARGUMENT-IMPL-POLICY>useArrayBaseType</SERVER-ARGUMENT-IMPL-POLICY></ARGUMENT-DATA-PROTOTYPE>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""
        result = self.validate(xml, rule("constr_1297", "server_argument_policy_type", ["ARGUMENT-DATA-PROTOTYPE"]))
        self.assertEqual("FAIL", result["decision"])

    def test_mixed_data_transformation_roles_fail(self) -> None:
        xml = """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>P</SHORT-NAME><ELEMENTS>
        <DATA-TRANSFORMATION><SHORT-NAME>T</SHORT-NAME></DATA-TRANSFORMATION>
        <DATA-PROTOTYPE-MAPPING><FIRST-TO-SECOND-DATA-TRANSFORMATION-REF>/P/T</FIRST-TO-SECOND-DATA-TRANSFORMATION-REF></DATA-PROTOTYPE-MAPPING>
        <I-SIGNAL><SHORT-NAME>S</SHORT-NAME><DATA-TRANSFORMATIONS><DATA-TRANSFORMATION-REF-CONDITIONAL>
          <DATA-TRANSFORMATION-REF>/P/T</DATA-TRANSFORMATION-REF></DATA-TRANSFORMATION-REF-CONDITIONAL></DATA-TRANSFORMATIONS></I-SIGNAL>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""
        result = self.validate(xml, rule("constr_1400", "data_transformation_reference_role", ["DATA-PROTOTYPE-MAPPING", "I-SIGNAL"]))
        self.assertEqual("FAIL", result["decision"])
        self.assertEqual(["data_prototype_mapping", "i_signal"], result["findings"][0]["evidence"]["roles"])

    def test_runnable_component_must_populate_composition(self) -> None:
        xml = """<AUTOSAR><APPLICATION-SW-COMPONENT-TYPE><SHORT-NAME>A</SHORT-NAME><INTERNAL-BEHAVIORS>
        <SWC-INTERNAL-BEHAVIOR><RUNNABLES><RUNNABLE-ENTITY><SHORT-NAME>R</SHORT-NAME></RUNNABLE-ENTITY></RUNNABLES></SWC-INTERNAL-BEHAVIOR>
        </INTERNAL-BEHAVIORS></APPLICATION-SW-COMPONENT-TYPE></AUTOSAR>"""
        result = self.validate(xml, rule("TPS_SWCT_01098", "populated_atomic_runnable_context", ["APPLICATION-SW-COMPONENT-TYPE"]))
        self.assertEqual("FAIL", result["decision"])

    def test_simple_network_representation_rejects_composite_type(self) -> None:
        xml = """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>P</SHORT-NAME><ELEMENTS>
        <APPLICATION-RECORD-DATA-TYPE><SHORT-NAME>Rec</SHORT-NAME><CATEGORY>STRUCTURE</CATEGORY></APPLICATION-RECORD-DATA-TYPE>
        <VARIABLE-DATA-PROTOTYPE><SHORT-NAME>D</SHORT-NAME><TYPE-TREF>/P/Rec</TYPE-TREF></VARIABLE-DATA-PROTOTYPE>
        <NONQUEUED-RECEIVER-COM-SPEC><DATA-ELEMENT-REF>/P/D</DATA-ELEMENT-REF><NETWORK-REPRESENTATION/></NONQUEUED-RECEIVER-COM-SPEC>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""
        result = self.validate(xml, rule("TPS_SWCT_01452", "composite_network_representation", ["NONQUEUED-RECEIVER-COM-SPEC"]))
        self.assertEqual("FAIL", result["decision"])


if __name__ == "__main__":
    unittest.main()
