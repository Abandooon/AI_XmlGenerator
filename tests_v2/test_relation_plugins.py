from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.validation.v2.engine import ValidationEngine


def rule(constraint_id: str, plugin: str, tags: list[str]) -> dict:
    return {
        "rule_id": f"{constraint_id}#r1",
        "constraint_id": constraint_id,
        "title": constraint_id,
        "severity": "error",
        "policy": "must",
        "implementation": {"status": "implemented", "plugin": plugin},
        "selector": {"tags": tags, "mode": "any"},
        "parameters": {},
        "completeness": {
            "requires": ["well_formed_xml", "complete_reference_scope"],
            "on_missing": "not_evaluated",
        },
        "dependencies": [],
        "bindings": [],
    }


class RelationPluginTests(unittest.TestCase):
    def validate(self, xml: str, rules: list[dict]) -> dict:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.arxml"
            path.write_text(xml, encoding="utf-8")
            return ValidationEngine({"rules": rules}).validate([path])

    def test_possible_error_must_share_interface_owner(self) -> None:
        xml = """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>Pkg</SHORT-NAME><ELEMENTS>
        <CLIENT-SERVER-INTERFACE><SHORT-NAME>I1</SHORT-NAME><POSSIBLE-ERRORS>
          <APPLICATION-ERROR><SHORT-NAME>E1</SHORT-NAME></APPLICATION-ERROR>
        </POSSIBLE-ERRORS></CLIENT-SERVER-INTERFACE>
        <CLIENT-SERVER-INTERFACE><SHORT-NAME>I2</SHORT-NAME><OPERATIONS>
          <CLIENT-SERVER-OPERATION><SHORT-NAME>Op</SHORT-NAME><POSSIBLE-ERROR-REFS>
            <POSSIBLE-ERROR-REF>/Pkg/I1/E1</POSSIBLE-ERROR-REF>
          </POSSIBLE-ERROR-REFS></CLIENT-SERVER-OPERATION>
        </OPERATIONS></CLIENT-SERVER-INTERFACE>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""
        result = self.validate(xml, [rule("constr_1038", "possible_error_same_interface", ["CLIENT-SERVER-OPERATION"])])
        self.assertEqual("FAIL", result["decision"])
        self.assertIn("same ClientServerInterface", result["findings"][0]["repair"]["instruction"])

    def test_unresolved_possible_error_is_incomplete(self) -> None:
        xml = """<AUTOSAR><CLIENT-SERVER-INTERFACE><SHORT-NAME>I</SHORT-NAME><OPERATIONS>
        <CLIENT-SERVER-OPERATION><SHORT-NAME>Op</SHORT-NAME>
          <POSSIBLE-ERROR-REF>/Missing</POSSIBLE-ERROR-REF>
        </CLIENT-SERVER-OPERATION></OPERATIONS></CLIENT-SERVER-INTERFACE></AUTOSAR>"""
        result = self.validate(xml, [rule("constr_1038", "possible_error_same_interface", ["CLIENT-SERVER-OPERATION"])])
        self.assertEqual("INCOMPLETE", result["decision"])
        self.assertEqual("NOT_EVALUATED", result["rules"][0]["status"])

    def test_mode_group_cannot_map_to_two_types(self) -> None:
        xml = """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>Pkg</SHORT-NAME><ELEMENTS>
        <MODE-DECLARATION-GROUP><SHORT-NAME>Modes</SHORT-NAME></MODE-DECLARATION-GROUP>
        <IMPLEMENTATION-DATA-TYPE><SHORT-NAME>T1</SHORT-NAME></IMPLEMENTATION-DATA-TYPE>
        <IMPLEMENTATION-DATA-TYPE><SHORT-NAME>T2</SHORT-NAME></IMPLEMENTATION-DATA-TYPE>
        <DATA-TYPE-MAPPING-SET><SHORT-NAME>Maps</SHORT-NAME><MODE-REQUEST-TYPE-MAPS>
          <MODE-REQUEST-TYPE-MAP><MODE-GROUP-REF>/Pkg/Modes</MODE-GROUP-REF><IMPLEMENTATION-DATA-TYPE-REF>/Pkg/T1</IMPLEMENTATION-DATA-TYPE-REF></MODE-REQUEST-TYPE-MAP>
          <MODE-REQUEST-TYPE-MAP><MODE-GROUP-REF>/Pkg/Modes</MODE-GROUP-REF><IMPLEMENTATION-DATA-TYPE-REF>/Pkg/T2</IMPLEMENTATION-DATA-TYPE-REF></MODE-REQUEST-TYPE-MAP>
        </MODE-REQUEST-TYPE-MAPS></DATA-TYPE-MAPPING-SET>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""
        result = self.validate(xml, [rule("constr_4002", "mode_request_mapping_unique", ["DATA-TYPE-MAPPING-SET"])])
        self.assertEqual("FAIL", result["decision"])
        self.assertEqual("/Pkg/T2", result["findings"][0]["evidence"]["second_type"])

    def test_async_call_point_requires_exactly_one_result(self) -> None:
        xml = """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>Pkg</SHORT-NAME><ELEMENTS>
        <RUNNABLE-ENTITY><SHORT-NAME>R</SHORT-NAME><SERVER-CALL-POINTS>
          <ASYNCHRONOUS-SERVER-CALL-POINT><SHORT-NAME>C</SHORT-NAME></ASYNCHRONOUS-SERVER-CALL-POINT>
        </SERVER-CALL-POINTS></RUNNABLE-ENTITY>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""
        result = self.validate(xml, [rule("constr_2006", "async_result_point_exactly_one", ["ASYNCHRONOUS-SERVER-CALL-POINT"])])
        self.assertEqual("FAIL", result["decision"])
        self.assertEqual(0, result["findings"][0]["evidence"]["actual"])

    def test_autosar_variable_iref_requires_root_for_composite_target(self) -> None:
        xml = """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>Pkg</SHORT-NAME><ELEMENTS>
        <APPLICATION-ARRAY-DATA-TYPE><SHORT-NAME>Array</SHORT-NAME></APPLICATION-ARRAY-DATA-TYPE>
        <VARIABLE-DATA-PROTOTYPE><SHORT-NAME>D</SHORT-NAME><TYPE-TREF>/Pkg/Array</TYPE-TREF></VARIABLE-DATA-PROTOTYPE>
        <VARIABLE-ACCESS><SHORT-NAME>A</SHORT-NAME><ACCESSED-VARIABLE><AUTOSAR-VARIABLE-REF>
          <AUTOSAR-VARIABLE-IREF><TARGET-DATA-PROTOTYPE-REF>/Pkg/D</TARGET-DATA-PROTOTYPE-REF></AUTOSAR-VARIABLE-IREF>
        </AUTOSAR-VARIABLE-REF></ACCESSED-VARIABLE></VARIABLE-ACCESS>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""
        result = self.validate(xml, [rule("TPS_SWCT_01375", "autosar_iref_composite_root", ["AUTOSAR-VARIABLE-REF"])])
        self.assertEqual("FAIL", result["decision"])
        self.assertTrue(result["findings"][0]["evidence"]["composite_type"])
        self.assertEqual("set_conditional_existence", result["findings"][0]["repair"]["action"])

    def test_variable_read_port_domain_is_resolved(self) -> None:
        xml = """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>Pkg</SHORT-NAME><ELEMENTS>
        <PARAMETER-INTERFACE><SHORT-NAME>Params</SHORT-NAME></PARAMETER-INTERFACE>
        <APPLICATION-SW-COMPONENT-TYPE><SHORT-NAME>Swc</SHORT-NAME><PORTS>
          <P-PORT-PROTOTYPE><SHORT-NAME>P</SHORT-NAME><PROVIDED-INTERFACE-TREF>/Pkg/Params</PROVIDED-INTERFACE-TREF></P-PORT-PROTOTYPE>
        </PORTS><INTERNAL-BEHAVIORS><SWC-INTERNAL-BEHAVIOR><SHORT-NAME>Ib</SHORT-NAME><RUNNABLES>
          <RUNNABLE-ENTITY><SHORT-NAME>R</SHORT-NAME><DATA-READ-ACCESSS><VARIABLE-ACCESS><SHORT-NAME>A</SHORT-NAME>
            <ACCESSED-VARIABLE><AUTOSAR-VARIABLE-REF><AUTOSAR-VARIABLE-IREF>
              <PORT-PROTOTYPE-REF>/Pkg/Swc/P</PORT-PROTOTYPE-REF>
            </AUTOSAR-VARIABLE-IREF></AUTOSAR-VARIABLE-REF></ACCESSED-VARIABLE>
          </VARIABLE-ACCESS></DATA-READ-ACCESSS></RUNNABLE-ENTITY>
        </RUNNABLES></SWC-INTERNAL-BEHAVIOR></INTERNAL-BEHAVIORS></APPLICATION-SW-COMPONENT-TYPE>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""
        result = self.validate(xml, [rule("constr_2002", "variable_access_port_domain", ["VARIABLE-ACCESS"])])
        self.assertEqual("FAIL", result["decision"])
        actual = result["findings"][0]["evidence"]["actual"]
        self.assertEqual("P-PORT-PROTOTYPE", actual["port"])
        self.assertEqual("PARAMETER-INTERFACE", actual["interface"])

    def test_event_waitpoint_restriction_collects_all_violations(self) -> None:
        xml = """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>Pkg</SHORT-NAME><ELEMENTS>
        <RUNNABLE-ENTITY><SHORT-NAME>R</SHORT-NAME><WAIT-POINTS><WAIT-POINT><SHORT-NAME>W</SHORT-NAME></WAIT-POINT></WAIT-POINTS></RUNNABLE-ENTITY>
        <SWC-MODE-SWITCH-EVENT><SHORT-NAME>E1</SHORT-NAME><START-ON-EVENT-REF>/Pkg/R</START-ON-EVENT-REF></SWC-MODE-SWITCH-EVENT>
        <SWC-MODE-SWITCH-EVENT><SHORT-NAME>E2</SHORT-NAME><START-ON-EVENT-REF>/Pkg/R</START-ON-EVENT-REF></SWC-MODE-SWITCH-EVENT>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""
        result = self.validate(xml, [rule("constr_1096", "event_runnable_waitpoint_restriction", ["SWC-MODE-SWITCH-EVENT"])])
        self.assertEqual("FAIL", result["decision"])
        self.assertEqual(2, result["summary"]["finding_count"])


if __name__ == "__main__":
    unittest.main()
