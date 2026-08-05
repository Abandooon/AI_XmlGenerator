from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.validation.v2.engine import ValidationEngine


def make_rule(constraint_id: str, plugin: str, tags: list[str]) -> dict:
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


class SemanticGraphPluginTests(unittest.TestCase):
    def validate(self, xml: str, rules: list[dict]) -> dict:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.arxml"
            path.write_text(xml, encoding="utf-8")
            return ValidationEngine({"rules": rules}).validate([path])

    def test_sender_receiver_annotation_uses_real_plural_container(self) -> None:
        xml = """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>Pkg</SHORT-NAME><ELEMENTS>
        <CLIENT-SERVER-INTERFACE><SHORT-NAME>Cs</SHORT-NAME></CLIENT-SERVER-INTERFACE>
        <APPLICATION-SW-COMPONENT-TYPE><SHORT-NAME>Swc</SHORT-NAME><PORTS>
          <R-PORT-PROTOTYPE><SHORT-NAME>P</SHORT-NAME>
            <REQUIRED-INTERFACE-TREF>/Pkg/Cs</REQUIRED-INTERFACE-TREF>
            <SENDER-RECEIVER-ANNOTATIONS/>
          </R-PORT-PROTOTYPE>
        </PORTS></APPLICATION-SW-COMPONENT-TYPE>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""
        result = self.validate(xml, [
            make_rule("constr_4004", "port_annotation_context", ["SENDER-RECEIVER-ANNOTATIONS"])
        ])
        self.assertEqual("FAIL", result["decision"])
        self.assertIn("SENDER-RECEIVER-INTERFACE", result["findings"][0]["message"])

    def test_queued_comspec_policy_mismatch_has_location_and_repair(self) -> None:
        xml = """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>Pkg</SHORT-NAME><ELEMENTS>
        <VARIABLE-DATA-PROTOTYPE><SHORT-NAME>D</SHORT-NAME>
          <SW-DATA-DEF-PROPS><SW-IMPL-POLICY>STANDARD</SW-IMPL-POLICY></SW-DATA-DEF-PROPS>
        </VARIABLE-DATA-PROTOTYPE>
        <R-PORT-PROTOTYPE><SHORT-NAME>P</SHORT-NAME><REQUIRED-COM-SPECS>
          <QUEUED-RECEIVER-COM-SPEC><DATA-ELEMENT-REF>/Pkg/D</DATA-ELEMENT-REF></QUEUED-RECEIVER-COM-SPEC>
        </REQUIRED-COM-SPECS></R-PORT-PROTOTYPE>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""
        result = self.validate(xml, [
            make_rule("constr_1130", "comspec_sw_impl_policy", ["QUEUED-RECEIVER-COM-SPEC"])
        ])
        self.assertEqual("FAIL", result["decision"])
        finding = result["findings"][0]
        self.assertGreater(finding["location"]["line"], 0)
        self.assertEqual("replace_value", finding["repair"]["action"])

    def test_unresolved_comspec_target_is_not_evaluated(self) -> None:
        xml = """<AUTOSAR><QUEUED-RECEIVER-COM-SPEC>
        <DATA-ELEMENT-REF>/Pkg/Missing</DATA-ELEMENT-REF>
        </QUEUED-RECEIVER-COM-SPEC></AUTOSAR>"""
        result = self.validate(xml, [
            make_rule("constr_1130", "comspec_sw_impl_policy", ["QUEUED-RECEIVER-COM-SPEC"])
        ])
        self.assertEqual("INCOMPLETE", result["decision"])
        self.assertEqual("NOT_EVALUATED", result["rules"][0]["status"])
        self.assertIn("unresolved reference", result["rules"][0]["notes"][0])

    def test_variation_proxy_type_reference_must_end_in_value(self) -> None:
        xml = """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>Pkg</SHORT-NAME><ELEMENTS>
        <IMPLEMENTATION-DATA-TYPE><SHORT-NAME>ArrayType</SHORT-NAME><CATEGORY>ARRAY</CATEGORY></IMPLEMENTATION-DATA-TYPE>
        <IMPLEMENTATION-DATA-TYPE><SHORT-NAME>Alias</SHORT-NAME><CATEGORY>TYPE_REFERENCE</CATEGORY>
          <SW-DATA-DEF-PROPS><IMPLEMENTATION-DATA-TYPE-REF>/Pkg/ArrayType</IMPLEMENTATION-DATA-TYPE-REF></SW-DATA-DEF-PROPS>
        </IMPLEMENTATION-DATA-TYPE>
        <VARIATION-POINT-PROXY><SHORT-NAME>Proxy</SHORT-NAME>
          <IMPLEMENTATION-DATA-TYPE-REF>/Pkg/Alias</IMPLEMENTATION-DATA-TYPE-REF>
        </VARIATION-POINT-PROXY>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""
        result = self.validate(xml, [
            make_rule("constr_1389", "variation_proxy_value_type", ["VARIATION-POINT-PROXY"])
        ])
        self.assertEqual("FAIL", result["decision"])
        self.assertEqual("ARRAY", result["findings"][0]["evidence"]["actual"]["resolved"])

    def test_service_proxy_collects_all_bad_ports(self) -> None:
        xml = """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>Pkg</SHORT-NAME><ELEMENTS>
        <PARAMETER-INTERFACE><SHORT-NAME>Params</SHORT-NAME><IS-SERVICE>false</IS-SERVICE></PARAMETER-INTERFACE>
        <SERVICE-PROXY-SW-COMPONENT-TYPE><SHORT-NAME>Proxy</SHORT-NAME><PORTS>
          <P-PORT-PROTOTYPE><SHORT-NAME>P1</SHORT-NAME><PROVIDED-INTERFACE-TREF>/Pkg/Params</PROVIDED-INTERFACE-TREF></P-PORT-PROTOTYPE>
          <R-PORT-PROTOTYPE><SHORT-NAME>P2</SHORT-NAME><REQUIRED-INTERFACE-TREF>/Pkg/Params</REQUIRED-INTERFACE-TREF></R-PORT-PROTOTYPE>
        </PORTS></SERVICE-PROXY-SW-COMPONENT-TYPE>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""
        result = self.validate(xml, [
            make_rule("constr_2017", "service_proxy_port_domain", ["SERVICE-PROXY-SW-COMPONENT-TYPE"])
        ])
        self.assertEqual("FAIL", result["decision"])
        self.assertEqual(2, result["summary"]["finding_count"])
        self.assertEqual({"P1", "P2"}, {
            finding["location"]["xml_path"].rsplit("/", 1)[-1] for finding in result["findings"]
        })


if __name__ == "__main__":
    unittest.main()
