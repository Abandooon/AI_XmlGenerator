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


class LocalSemanticPluginTests(unittest.TestCase):
    def validate(self, xml: str, validation_rule: dict) -> dict:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.arxml"
            path.write_text(xml, encoding="utf-8")
            return ValidationEngine({"rules": [validation_rule]}).validate([path])

    def test_unconnected_rport_requires_init_for_each_element(self) -> None:
        xml = """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>P</SHORT-NAME><ELEMENTS>
        <SENDER-RECEIVER-INTERFACE><SHORT-NAME>I</SHORT-NAME><DATA-ELEMENTS><VARIABLE-DATA-PROTOTYPE><SHORT-NAME>D</SHORT-NAME></VARIABLE-DATA-PROTOTYPE></DATA-ELEMENTS></SENDER-RECEIVER-INTERFACE>
        <R-PORT-PROTOTYPE><SHORT-NAME>R</SHORT-NAME><REQUIRED-INTERFACE-TREF>/P/I</REQUIRED-INTERFACE-TREF></R-PORT-PROTOTYPE>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""
        result = self.validate(xml, rule("constr_1100", "unconnected_rport_init_values", ["R-PORT-PROTOTYPE"]))
        self.assertEqual("FAIL", result["decision"])

    def test_profile_range_is_profile_specific(self) -> None:
        xml = """<AUTOSAR><END-TO-END-PROTECTION><END-TO-END-PROFILE><CATEGORY>PROFILE_01</CATEGORY>
        <MAX-DELTA-COUNTER-INIT>15</MAX-DELTA-COUNTER-INIT></END-TO-END-PROFILE></END-TO-END-PROTECTION></AUTOSAR>"""
        result = self.validate(xml, rule("constr_1117", "e2e_profile_value_range", ["END-TO-END-PROTECTION"]))
        self.assertEqual("FAIL", result["decision"])
        self.assertEqual(14, result["findings"][0]["evidence"]["maximum"])

    def test_profile_fallback_required_without_receiver_override(self) -> None:
        xml = "<AUTOSAR><END-TO-END-PROTECTION><END-TO-END-PROFILE><CATEGORY>PROFILE_02</CATEGORY></END-TO-END-PROFILE></END-TO-END-PROTECTION></AUTOSAR>"
        result = self.validate(xml, rule("constr_1171", "e2e_profile_default_required", ["END-TO-END-PROTECTION"]))
        self.assertEqual("FAIL", result["decision"])

    def test_replace_with_is_bidirectional_condition(self) -> None:
        xml = """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>P</SHORT-NAME><ELEMENTS>
        <VARIABLE-DATA-PROTOTYPE><SHORT-NAME>D</SHORT-NAME></VARIABLE-DATA-PROTOTYPE>
        <NONQUEUED-RECEIVER-COM-SPEC><DATA-ELEMENT-REF>/P/D</DATA-ELEMENT-REF><HANDLE-OUT-OF-RANGE>EXTERNAL-REPLACEMENT</HANDLE-OUT-OF-RANGE></NONQUEUED-RECEIVER-COM-SPEC>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""
        result = self.validate(xml, rule("constr_1188", "receiver_replace_with_iff", ["NONQUEUED-RECEIVER-COM-SPEC"]))
        self.assertEqual("FAIL", result["decision"])

    def test_text_table_category_pair_is_closed(self) -> None:
        xml = """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>P</SHORT-NAME><ELEMENTS>
        <COMPU-METHOD><SHORT-NAME>C1</SHORT-NAME><CATEGORY>LINEAR</CATEGORY></COMPU-METHOD><COMPU-METHOD><SHORT-NAME>C2</SHORT-NAME><CATEGORY>TEXTTABLE</CATEGORY></COMPU-METHOD>
        <IMPLEMENTATION-DATA-TYPE><SHORT-NAME>T1</SHORT-NAME><SW-DATA-DEF-PROPS><COMPU-METHOD-REF>/P/C1</COMPU-METHOD-REF></SW-DATA-DEF-PROPS></IMPLEMENTATION-DATA-TYPE>
        <IMPLEMENTATION-DATA-TYPE><SHORT-NAME>T2</SHORT-NAME><SW-DATA-DEF-PROPS><COMPU-METHOD-REF>/P/C2</COMPU-METHOD-REF></SW-DATA-DEF-PROPS></IMPLEMENTATION-DATA-TYPE>
        <VARIABLE-DATA-PROTOTYPE><SHORT-NAME>A</SHORT-NAME><TYPE-TREF>/P/T1</TYPE-TREF></VARIABLE-DATA-PROTOTYPE><VARIABLE-DATA-PROTOTYPE><SHORT-NAME>B</SHORT-NAME><TYPE-TREF>/P/T2</TYPE-TREF></VARIABLE-DATA-PROTOTYPE>
        <DATA-PROTOTYPE-MAPPING><FIRST-DATA-PROTOTYPE-REF>/P/A</FIRST-DATA-PROTOTYPE-REF><SECOND-DATA-PROTOTYPE-REF>/P/B</SECOND-DATA-PROTOTYPE-REF><TEXT-TABLE-MAPPINGS><TEXT-TABLE-MAPPING/></TEXT-TABLE-MAPPINGS></DATA-PROTOTYPE-MAPPING>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""
        result = self.validate(xml, rule("constr_1303", "text_table_mapping_categories", ["DATA-PROTOTYPE-MAPPING"]))
        self.assertEqual("FAIL", result["decision"])

    def test_mask_rejects_bits_outside_domain(self) -> None:
        xml = """<AUTOSAR><TEXT-TABLE-MAPPING><BITFIELD-TEXT-TABLE-MASK-FIRST>3</BITFIELD-TEXT-TABLE-MASK-FIRST><VALUE-PAIRS>
        <TEXT-TABLE-VALUE-PAIR><FIRST-VALUE>4</FIRST-VALUE><SECOND-VALUE>0</SECOND-VALUE></TEXT-TABLE-VALUE-PAIR>
        </VALUE-PAIRS></TEXT-TABLE-MAPPING></AUTOSAR>"""
        result = self.validate(xml, rule("constr_1307", "text_table_mask_values", ["TEXT-TABLE-MAPPING"]))
        self.assertEqual("FAIL", result["decision"])

    def test_vsa_mapping_requires_structure(self) -> None:
        xml = """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>P</SHORT-NAME><ELEMENTS>
        <APPLICATION-ARRAY-DATA-TYPE><SHORT-NAME>A</SHORT-NAME><DYNAMIC-ARRAY-SIZE-PROFILE>VSA_LINEAR</DYNAMIC-ARRAY-SIZE-PROFILE></APPLICATION-ARRAY-DATA-TYPE>
        <IMPLEMENTATION-DATA-TYPE><SHORT-NAME>I</SHORT-NAME><CATEGORY>ARRAY</CATEGORY></IMPLEMENTATION-DATA-TYPE>
        <DATA-TYPE-MAP><APPLICATION-DATA-TYPE-REF>/P/A</APPLICATION-DATA-TYPE-REF><IMPLEMENTATION-DATA-TYPE-REF>/P/I</IMPLEMENTATION-DATA-TYPE-REF></DATA-TYPE-MAP>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""
        result = self.validate(xml, rule("constr_1322", "vsa_mapped_implementation_shape", ["DATA-TYPE-MAP"]))
        self.assertEqual("FAIL", result["decision"])

    def test_direct_nv_mapping_excludes_sub_element_mapping(self) -> None:
        xml = """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>P</SHORT-NAME><ELEMENTS>
        <VARIABLE-DATA-PROTOTYPE><SHORT-NAME>Root</SHORT-NAME></VARIABLE-DATA-PROTOTYPE><IMPLEMENTATION-DATA-TYPE-ELEMENT><SHORT-NAME>Leaf</SHORT-NAME></IMPLEMENTATION-DATA-TYPE-ELEMENT>
        <NV-BLOCK-DATA-MAPPING><SHORT-NAME>A</SHORT-NAME><READ-NV-DATA><ROOT-VARIABLE-DATA-PROTOTYPE-REF>/P/Root</ROOT-VARIABLE-DATA-PROTOTYPE-REF><TARGET-DATA-PROTOTYPE-REF>/P/Root</TARGET-DATA-PROTOTYPE-REF></READ-NV-DATA></NV-BLOCK-DATA-MAPPING>
        <NV-BLOCK-DATA-MAPPING><SHORT-NAME>B</SHORT-NAME><READ-NV-DATA><ROOT-VARIABLE-DATA-PROTOTYPE-REF>/P/Root</ROOT-VARIABLE-DATA-PROTOTYPE-REF><TARGET-IMPLEMENTATION-DATA-TYPE-ELEMENT-REF>/P/Leaf</TARGET-IMPLEMENTATION-DATA-TYPE-ELEMENT-REF></READ-NV-DATA></NV-BLOCK-DATA-MAPPING>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""
        result = self.validate(xml, rule("constr_1403", "nv_mapping_direct_or_subtree", ["NV-BLOCK-DATA-MAPPING"]))
        self.assertEqual("FAIL", result["decision"])

    def test_utf16_bom_is_rejected(self) -> None:
        xml = """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>P</SHORT-NAME><ELEMENTS>
        <SW-BASE-TYPE><SHORT-NAME>B</SHORT-NAME><BASE-TYPE-ENCODING>UTF-16</BASE-TYPE-ENCODING></SW-BASE-TYPE>
        <IMPLEMENTATION-DATA-TYPE><SHORT-NAME>T</SHORT-NAME><CATEGORY>VALUE</CATEGORY><SW-DATA-DEF-PROPS><BASE-TYPE-REF>/P/B</BASE-TYPE-REF></SW-DATA-DEF-PROPS></IMPLEMENTATION-DATA-TYPE>
        <VARIABLE-DATA-PROTOTYPE><SHORT-NAME>D</SHORT-NAME><TYPE-TREF>/P/T</TYPE-TREF><INIT-VALUE><TEXT-VALUE-SPECIFICATION><VALUE>FEFF0041</VALUE></TEXT-VALUE-SPECIFICATION></INIT-VALUE></VARIABLE-DATA-PROTOTYPE>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""
        result = self.validate(xml, rule("TPS_SWCT_01653", "utf16_value_no_bom", ["VARIABLE-DATA-PROTOTYPE"]))
        self.assertEqual("FAIL", result["decision"])


if __name__ == "__main__":
    unittest.main()
