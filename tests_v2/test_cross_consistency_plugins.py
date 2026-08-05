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


class CrossConsistencyPluginTests(unittest.TestCase):
    def validate(self, xml: str, validation_rule: dict) -> dict:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.arxml"
            path.write_text(xml, encoding="utf-8")
            return ValidationEngine({"rules": [validation_rule]}).validate([path])

    def test_server_call_timeouts_compare_semantic_numbers(self) -> None:
        xml = """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>P</SHORT-NAME><ELEMENTS>
        <CLIENT-SERVER-OPERATION><SHORT-NAME>Op</SHORT-NAME></CLIENT-SERVER-OPERATION>
        <SYNCHRONOUS-SERVER-CALL-POINT><SHORT-NAME>A</SHORT-NAME><TIMEOUT>1.0</TIMEOUT><OPERATION-IREF><TARGET-REQUIRED-OPERATION-REF>/P/Op</TARGET-REQUIRED-OPERATION-REF></OPERATION-IREF></SYNCHRONOUS-SERVER-CALL-POINT>
        <ASYNCHRONOUS-SERVER-CALL-POINT><SHORT-NAME>B</SHORT-NAME><TIMEOUT>1.00</TIMEOUT><OPERATION-IREF><TARGET-REQUIRED-OPERATION-REF>/P/Op</TARGET-REQUIRED-OPERATION-REF></OPERATION-IREF></ASYNCHRONOUS-SERVER-CALL-POINT>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""
        result = self.validate(xml, rule("TPS_SWCT_01344", "server_call_timeout_consistency", ["SYNCHRONOUS-SERVER-CALL-POINT", "ASYNCHRONOUS-SERVER-CALL-POINT"]))
        self.assertEqual("PASS", result["decision"])

    def test_array_element_category_mismatch_fails(self) -> None:
        xml = """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>P</SHORT-NAME><ELEMENTS>
        <APPLICATION-PRIMITIVE-DATA-TYPE><SHORT-NAME>T</SHORT-NAME><CATEGORY>VALUE</CATEGORY></APPLICATION-PRIMITIVE-DATA-TYPE>
        <APPLICATION-ARRAY-ELEMENT><SHORT-NAME>E</SHORT-NAME><CATEGORY>BOOLEAN</CATEGORY><TYPE-TREF>/P/T</TYPE-TREF></APPLICATION-ARRAY-ELEMENT>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""
        result = self.validate(xml, rule("constr_1152", "application_array_element_category", ["APPLICATION-ARRAY-ELEMENT"]))
        self.assertEqual("FAIL", result["decision"])
        self.assertEqual("VALUE", result["findings"][0]["evidence"]["expected"])

    def test_e2e_entries_require_identical_sender(self) -> None:
        xml = """<AUTOSAR><END-TO-END-PROTECTION><END-TO-END-PROTECTION-VARIABLE-PROTOTYPES>
        <END-TO-END-PROTECTION-VARIABLE-PROTOTYPE><SENDER-IREF><CONTEXT-PORT-REF>/P/A</CONTEXT-PORT-REF></SENDER-IREF></END-TO-END-PROTECTION-VARIABLE-PROTOTYPE>
        <END-TO-END-PROTECTION-VARIABLE-PROTOTYPE><SENDER-IREF><CONTEXT-PORT-REF>/P/B</CONTEXT-PORT-REF></SENDER-IREF></END-TO-END-PROTECTION-VARIABLE-PROTOTYPE>
        </END-TO-END-PROTECTION-VARIABLE-PROTOTYPES></END-TO-END-PROTECTION></AUTOSAR>"""
        result = self.validate(xml, rule("constr_1183", "e2e_identical_sender", ["END-TO-END-PROTECTION"]))
        self.assertEqual("FAIL", result["decision"])

    def test_mapping_sides_must_have_distinct_interface_owners(self) -> None:
        xml = """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>P</SHORT-NAME><ELEMENTS>
        <SENDER-RECEIVER-INTERFACE><SHORT-NAME>I</SHORT-NAME><DATA-ELEMENTS>
          <VARIABLE-DATA-PROTOTYPE><SHORT-NAME>A</SHORT-NAME></VARIABLE-DATA-PROTOTYPE>
          <VARIABLE-DATA-PROTOTYPE><SHORT-NAME>B</SHORT-NAME></VARIABLE-DATA-PROTOTYPE>
        </DATA-ELEMENTS></SENDER-RECEIVER-INTERFACE>
        <VARIABLE-AND-PARAMETER-INTERFACE-MAPPING><SHORT-NAME>M</SHORT-NAME><DATA-MAPPINGS><DATA-PROTOTYPE-MAPPING>
          <FIRST-DATA-PROTOTYPE-REF>/P/I/A</FIRST-DATA-PROTOTYPE-REF><SECOND-DATA-PROTOTYPE-REF>/P/I/B</SECOND-DATA-PROTOTYPE-REF>
        </DATA-PROTOTYPE-MAPPING></DATA-MAPPINGS></VARIABLE-AND-PARAMETER-INTERFACE-MAPPING>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""
        result = self.validate(xml, rule("constr_1159", "interface_mapping_side_scope", ["VARIABLE-AND-PARAMETER-INTERFACE-MAPPING"]))
        self.assertEqual("FAIL", result["decision"])

    def test_pim_typedef_mismatch_is_located(self) -> None:
        xml = """<AUTOSAR><SWC-INTERNAL-BEHAVIOR><SHORT-NAME>IB</SHORT-NAME><PER-INSTANCE-MEMORIES>
        <PER-INSTANCE-MEMORY><SHORT-NAME>A</SHORT-NAME><TYPE>T</TYPE><TYPE-DEFINITION>typedef int T;</TYPE-DEFINITION></PER-INSTANCE-MEMORY>
        <PER-INSTANCE-MEMORY><SHORT-NAME>B</SHORT-NAME><TYPE>T</TYPE><TYPE-DEFINITION>typedef long T;</TYPE-DEFINITION></PER-INSTANCE-MEMORY>
        </PER-INSTANCE-MEMORIES></SWC-INTERNAL-BEHAVIOR></AUTOSAR>"""
        result = self.validate(xml, rule("constr_2007", "pim_type_definition_consistency", ["SWC-INTERNAL-BEHAVIOR"]))
        self.assertEqual("FAIL", result["decision"])
        self.assertEqual("PER-INSTANCE-MEMORY", result["findings"][0]["location"]["tag"])

    def test_wait_point_timeout_matches_ack_request(self) -> None:
        xml = """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>P</SHORT-NAME><ELEMENTS>
        <VARIABLE-ACCESS><SHORT-NAME>Send</SHORT-NAME><TRANSMISSION-ACKNOWLEDGE><TIMEOUT>2</TIMEOUT></TRANSMISSION-ACKNOWLEDGE></VARIABLE-ACCESS>
        <DATA-SEND-COMPLETED-EVENT><SHORT-NAME>Ev</SHORT-NAME><EVENT-SOURCE-REF>/P/Send</EVENT-SOURCE-REF></DATA-SEND-COMPLETED-EVENT>
        <WAIT-POINT><SHORT-NAME>W</SHORT-NAME><TIMEOUT>3</TIMEOUT><TRIGGER-REF>/P/Ev</TRIGGER-REF></WAIT-POINT>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""
        result = self.validate(xml, rule("constr_2033", "event_request_timeout_consistency", ["WAIT-POINT"]))
        self.assertEqual("FAIL", result["decision"])

    def test_transition_event_requires_two_distinct_modes(self) -> None:
        xml = """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>P</SHORT-NAME><ELEMENTS>
        <MODE-DECLARATION-GROUP><SHORT-NAME>G</SHORT-NAME><MODE-DECLARATIONS><MODE-DECLARATION><SHORT-NAME>A</SHORT-NAME></MODE-DECLARATION></MODE-DECLARATIONS></MODE-DECLARATION-GROUP>
        <SWC-MODE-SWITCH-EVENT><SHORT-NAME>E</SHORT-NAME><ACTIVATION>ON-TRANSITION</ACTIVATION><MODE-IREFS><MODE-IREF><TARGET-MODE-DECLARATION-REF>/P/G/A</TARGET-MODE-DECLARATION-REF></MODE-IREF></MODE-IREFS></SWC-MODE-SWITCH-EVENT>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""
        result = self.validate(xml, rule("constr_4003", "mode_switch_event_mode_cardinality", ["SWC-MODE-SWITCH-EVENT"]))
        self.assertEqual("FAIL", result["decision"])


if __name__ == "__main__":
    unittest.main()
