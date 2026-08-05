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


CONNECTORS = ["ASSEMBLY-SW-CONNECTOR", "DELEGATION-SW-CONNECTOR", "PASS-THROUGH-SW-CONNECTOR"]


class RemainingCompiledPluginTests(unittest.TestCase):
    def validate(self, xml: str, validation_rule: dict) -> dict:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.arxml"
            path.write_text(xml, encoding="utf-8")
            return ValidationEngine({"rules": [validation_rule]}).validate([path])

    @staticmethod
    def table61_xml(required_policy: str) -> str:
        return f"""<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>P</SHORT-NAME><ELEMENTS>
        <PARAMETER-INTERFACE><SHORT-NAME>Prm</SHORT-NAME><PARAMETERS><PARAMETER-DATA-PROTOTYPE>
          <SHORT-NAME>D</SHORT-NAME><SW-IMPL-POLICY>fixed</SW-IMPL-POLICY>
        </PARAMETER-DATA-PROTOTYPE></PARAMETERS></PARAMETER-INTERFACE>
        <SENDER-RECEIVER-INTERFACE><SHORT-NAME>Sr</SHORT-NAME><DATA-ELEMENTS><VARIABLE-DATA-PROTOTYPE>
          <SHORT-NAME>D</SHORT-NAME><SW-IMPL-POLICY>{required_policy}</SW-IMPL-POLICY>
        </VARIABLE-DATA-PROTOTYPE></DATA-ELEMENTS></SENDER-RECEIVER-INTERFACE>
        <P-PORT-PROTOTYPE><SHORT-NAME>PP</SHORT-NAME><PROVIDED-INTERFACE-TREF>/P/Prm</PROVIDED-INTERFACE-TREF></P-PORT-PROTOTYPE>
        <R-PORT-PROTOTYPE><SHORT-NAME>RP</SHORT-NAME><REQUIRED-INTERFACE-TREF>/P/Sr</REQUIRED-INTERFACE-TREF></R-PORT-PROTOTYPE>
        <ASSEMBLY-SW-CONNECTOR><SHORT-NAME>C</SHORT-NAME><PROVIDER-IREF><TARGET-P-PORT-REF>/P/PP</TARGET-P-PORT-REF></PROVIDER-IREF>
          <REQUESTER-IREF><TARGET-R-PORT-REF>/P/RP</TARGET-R-PORT-REF></REQUESTER-IREF></ASSEMBLY-SW-CONNECTOR>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""

    def test_table_61_forbidden_pair_fails(self) -> None:
        result = self.validate(
            self.table61_xml("queued"),
            rule("constr_1071", "interface_member_compatibility_table", CONNECTORS),
        )
        self.assertEqual("FAIL", result["decision"])
        self.assertIn("Table 6.1", result["findings"][0]["message"])

    def test_table_61_yes_pair_passes_with_observation(self) -> None:
        result = self.validate(
            self.table61_xml("standard"),
            rule("constr_1071", "interface_member_compatibility_table", CONNECTORS),
        )
        self.assertEqual("PASS", result["decision"])
        self.assertEqual("autosar_table_6_1", result["rules"][0]["observations"][0]["semantic"])

    @staticmethod
    def client_server_scale_xml() -> str:
        return """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>P</SHORT-NAME><ELEMENTS>
        <COMPU-METHOD><SHORT-NAME>ClientCm</SHORT-NAME><CATEGORY>TEXTTABLE</CATEGORY><COMPU-INTERNAL-TO-PHYS><COMPU-SCALES>
          <COMPU-SCALE><LOWER-LIMIT>0</LOWER-LIMIT><UPPER-LIMIT>0</UPPER-LIMIT></COMPU-SCALE>
          <COMPU-SCALE><LOWER-LIMIT>1</LOWER-LIMIT><UPPER-LIMIT>1</UPPER-LIMIT></COMPU-SCALE>
        </COMPU-SCALES></COMPU-INTERNAL-TO-PHYS></COMPU-METHOD>
        <COMPU-METHOD><SHORT-NAME>ServerCm</SHORT-NAME><CATEGORY>TEXTTABLE</CATEGORY><COMPU-INTERNAL-TO-PHYS><COMPU-SCALES>
          <COMPU-SCALE><LOWER-LIMIT>0</LOWER-LIMIT><UPPER-LIMIT>0</UPPER-LIMIT></COMPU-SCALE>
        </COMPU-SCALES></COMPU-INTERNAL-TO-PHYS></COMPU-METHOD>
        <APPLICATION-PRIMITIVE-DATA-TYPE><SHORT-NAME>ClientType</SHORT-NAME><CATEGORY>VALUE</CATEGORY><SW-DATA-DEF-PROPS><COMPU-METHOD-REF>/P/ClientCm</COMPU-METHOD-REF></SW-DATA-DEF-PROPS></APPLICATION-PRIMITIVE-DATA-TYPE>
        <APPLICATION-PRIMITIVE-DATA-TYPE><SHORT-NAME>ServerType</SHORT-NAME><CATEGORY>VALUE</CATEGORY><SW-DATA-DEF-PROPS><COMPU-METHOD-REF>/P/ServerCm</COMPU-METHOD-REF></SW-DATA-DEF-PROPS></APPLICATION-PRIMITIVE-DATA-TYPE>
        <CLIENT-SERVER-INTERFACE><SHORT-NAME>ClientIf</SHORT-NAME><OPERATIONS><CLIENT-SERVER-OPERATION><SHORT-NAME>Op</SHORT-NAME><ARGUMENTS>
          <ARGUMENT-DATA-PROTOTYPE><SHORT-NAME>A</SHORT-NAME><TYPE-TREF>/P/ClientType</TYPE-TREF><DIRECTION>IN</DIRECTION></ARGUMENT-DATA-PROTOTYPE>
        </ARGUMENTS></CLIENT-SERVER-OPERATION></OPERATIONS></CLIENT-SERVER-INTERFACE>
        <CLIENT-SERVER-INTERFACE><SHORT-NAME>ServerIf</SHORT-NAME><OPERATIONS><CLIENT-SERVER-OPERATION><SHORT-NAME>Op</SHORT-NAME><ARGUMENTS>
          <ARGUMENT-DATA-PROTOTYPE><SHORT-NAME>A</SHORT-NAME><TYPE-TREF>/P/ServerType</TYPE-TREF><DIRECTION>IN</DIRECTION></ARGUMENT-DATA-PROTOTYPE>
        </ARGUMENTS></CLIENT-SERVER-OPERATION></OPERATIONS></CLIENT-SERVER-INTERFACE>
        <R-PORT-PROTOTYPE><SHORT-NAME>Client</SHORT-NAME><REQUIRED-INTERFACE-TREF>/P/ClientIf</REQUIRED-INTERFACE-TREF></R-PORT-PROTOTYPE>
        <P-PORT-PROTOTYPE><SHORT-NAME>Server</SHORT-NAME><PROVIDED-INTERFACE-TREF>/P/ServerIf</PROVIDED-INTERFACE-TREF></P-PORT-PROTOTYPE>
        <ASSEMBLY-SW-CONNECTOR><SHORT-NAME>C</SHORT-NAME><REQUESTER-IREF><TARGET-R-PORT-REF>/P/Client</TARGET-R-PORT-REF></REQUESTER-IREF>
          <PROVIDER-IREF><TARGET-P-PORT-REF>/P/Server</TARGET-P-PORT-REF></PROVIDER-IREF></ASSEMBLY-SW-CONNECTOR>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""

    def test_client_server_in_scale_direction_fails(self) -> None:
        result = self.validate(
            self.client_server_scale_xml(),
            rule("constr_1155", "client_server_compu_scale_compatibility", CONNECTORS),
        )
        self.assertEqual("FAIL", result["decision"])
        self.assertEqual("IN", result["findings"][0]["evidence"]["direction"])

    def test_mode_request_value_outside_type_range_fails(self) -> None:
        xml = """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>P</SHORT-NAME><ELEMENTS>
        <DATA-CONSTR><SHORT-NAME>C</SHORT-NAME><DATA-CONSTR-RULES><DATA-CONSTR-RULE><INTERNAL-CONSTRS>
          <LOWER-LIMIT>0</LOWER-LIMIT><UPPER-LIMIT>1</UPPER-LIMIT>
        </INTERNAL-CONSTRS></DATA-CONSTR-RULE></DATA-CONSTR-RULES></DATA-CONSTR>
        <IMPLEMENTATION-DATA-TYPE><SHORT-NAME>I</SHORT-NAME><CATEGORY>VALUE</CATEGORY><SW-DATA-DEF-PROPS><DATA-CONSTR-REF>/P/C</DATA-CONSTR-REF></SW-DATA-DEF-PROPS></IMPLEMENTATION-DATA-TYPE>
        <MODE-DECLARATION-GROUP><SHORT-NAME>G</SHORT-NAME><MODE-DECLARATIONS>
          <MODE-DECLARATION><SHORT-NAME>M0</SHORT-NAME><VALUE>0</VALUE></MODE-DECLARATION>
          <MODE-DECLARATION><SHORT-NAME>M2</SHORT-NAME><VALUE>2</VALUE></MODE-DECLARATION>
        </MODE-DECLARATIONS></MODE-DECLARATION-GROUP>
        <MODE-REQUEST-TYPE-MAP><MODE-GROUP-REF>/P/G</MODE-GROUP-REF><IMPLEMENTATION-DATA-TYPE-REF>/P/I</IMPLEMENTATION-DATA-TYPE-REF></MODE-REQUEST-TYPE-MAP>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""
        result = self.validate(xml, rule("constr_1168", "mode_request_type_map_compatible", ["MODE-REQUEST-TYPE-MAP"]))
        self.assertEqual("FAIL", result["decision"])
        self.assertEqual("2", result["findings"][0]["evidence"]["value"])

    def test_mode_request_missing_range_is_not_evaluated(self) -> None:
        xml = """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>P</SHORT-NAME><ELEMENTS>
        <IMPLEMENTATION-DATA-TYPE><SHORT-NAME>I</SHORT-NAME><CATEGORY>VALUE</CATEGORY></IMPLEMENTATION-DATA-TYPE>
        <MODE-DECLARATION-GROUP><SHORT-NAME>G</SHORT-NAME><MODE-DECLARATIONS><MODE-DECLARATION><SHORT-NAME>M</SHORT-NAME><VALUE>0</VALUE></MODE-DECLARATION></MODE-DECLARATIONS></MODE-DECLARATION-GROUP>
        <MODE-REQUEST-TYPE-MAP><MODE-GROUP-REF>/P/G</MODE-GROUP-REF><IMPLEMENTATION-DATA-TYPE-REF>/P/I</IMPLEMENTATION-DATA-TYPE-REF></MODE-REQUEST-TYPE-MAP>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""
        result = self.validate(xml, rule("constr_1168", "mode_request_type_map_compatible", ["MODE-REQUEST-TYPE-MAP"]))
        self.assertEqual("INCOMPLETE", result["decision"])
        self.assertEqual("NOT_EVALUATED", result["rules"][0]["status"])

    def test_rpt_table_13_4_wrong_target_fails(self) -> None:
        xml = """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>P</SHORT-NAME><ELEMENTS>
        <SW-COMPONENT-PROTOTYPE><SHORT-NAME>C</SHORT-NAME></SW-COMPONENT-PROTOTYPE>
        <RPT-CONTAINER><SHORT-NAME>R</SHORT-NAME><CATEGORY>RUNNABLE_ENTITY</CATEGORY><BY-PASS-POINT-IREFS>
          <BY-PASS-POINT-IREF><TARGET-REF>/P/C</TARGET-REF></BY-PASS-POINT-IREF>
        </BY-PASS-POINT-IREFS></RPT-CONTAINER>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""
        result = self.validate(xml, rule("constr_2055", "rpt_target_category_table", ["RPT-CONTAINER"]))
        self.assertEqual("FAIL", result["decision"])
        self.assertEqual("SW-COMPONENT-PROTOTYPE", result["findings"][0]["evidence"]["actual"])

    def test_incompatible_data_type_map_fails(self) -> None:
        xml = """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>P</SHORT-NAME><ELEMENTS>
        <APPLICATION-PRIMITIVE-DATA-TYPE><SHORT-NAME>A</SHORT-NAME><CATEGORY>VALUE</CATEGORY></APPLICATION-PRIMITIVE-DATA-TYPE>
        <IMPLEMENTATION-DATA-TYPE><SHORT-NAME>I</SHORT-NAME><CATEGORY>STRUCTURE</CATEGORY></IMPLEMENTATION-DATA-TYPE>
        <DATA-TYPE-MAP><APPLICATION-DATA-TYPE-REF>/P/A</APPLICATION-DATA-TYPE-REF><IMPLEMENTATION-DATA-TYPE-REF>/P/I</IMPLEMENTATION-DATA-TYPE-REF></DATA-TYPE-MAP>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""
        result = self.validate(xml, rule("TPS_SWCT_01191", "mapped_data_type_compatibility", ["DATA-TYPE-MAP"]))
        self.assertEqual("FAIL", result["decision"])

    def test_unresolved_data_type_map_is_not_evaluated(self) -> None:
        xml = """<AUTOSAR><DATA-TYPE-MAP><APPLICATION-DATA-TYPE-REF>/Missing/A</APPLICATION-DATA-TYPE-REF>
        <IMPLEMENTATION-DATA-TYPE-REF>/Missing/I</IMPLEMENTATION-DATA-TYPE-REF></DATA-TYPE-MAP></AUTOSAR>"""
        result = self.validate(xml, rule("TPS_SWCT_01191", "mapped_data_type_compatibility", ["DATA-TYPE-MAP"]))
        self.assertEqual("INCOMPLETE", result["decision"])

    def test_runnable_possible_error_presence_must_match(self) -> None:
        xml = """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>P</SHORT-NAME><ELEMENTS>
        <RUNNABLE-ENTITY><SHORT-NAME>R</SHORT-NAME></RUNNABLE-ENTITY>
        <APPLICATION-ERROR><SHORT-NAME>E</SHORT-NAME><ERROR-CODE>1</ERROR-CODE></APPLICATION-ERROR>
        <CLIENT-SERVER-OPERATION><SHORT-NAME>O1</SHORT-NAME><POSSIBLE-ERROR-REFS><POSSIBLE-ERROR-REF>/P/E</POSSIBLE-ERROR-REF></POSSIBLE-ERROR-REFS></CLIENT-SERVER-OPERATION>
        <CLIENT-SERVER-OPERATION><SHORT-NAME>O2</SHORT-NAME></CLIENT-SERVER-OPERATION>
        <OPERATION-INVOKED-EVENT><SHORT-NAME>E1</SHORT-NAME><START-ON-EVENT-REF>/P/R</START-ON-EVENT-REF><TARGET-PROVIDED-OPERATION-REF>/P/O1</TARGET-PROVIDED-OPERATION-REF></OPERATION-INVOKED-EVENT>
        <OPERATION-INVOKED-EVENT><SHORT-NAME>E2</SHORT-NAME><START-ON-EVENT-REF>/P/R</START-ON-EVENT-REF><TARGET-PROVIDED-OPERATION-REF>/P/O2</TARGET-PROVIDED-OPERATION-REF></OPERATION-INVOKED-EVENT>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""
        result = self.validate(xml, rule("TPS_SWCT_01520", "runnable_operation_signatures", ["OPERATION-INVOKED-EVENT"]))
        self.assertEqual("FAIL", result["decision"])
        self.assertIn("return/error", result["findings"][0]["message"])

    @staticmethod
    def runnable_signature_xml(*, second_type: str = "T", policy: str = "USE-ARGUMENT-TYPE", runnable_arg_count: int = 1, include_port_value: bool = True) -> str:
        runnable_args = "".join("<RUNNABLE-ENTITY-ARGUMENT><SYMBOL>A</SYMBOL></RUNNABLE-ENTITY-ARGUMENT>" for _ in range(runnable_arg_count))
        port_option = """<PORT-API-OPTIONS><PORT-API-OPTION><PORT-REF>/P/S/P1</PORT-REF><PORT-ARG-VALUES><PORT-DEFINED-ARGUMENT-VALUE>
            <VALUE-TYPE-TREF>/P/T</VALUE-TYPE-TREF><VALUE><NUMERICAL-VALUE-SPECIFICATION><VALUE>1</VALUE></NUMERICAL-VALUE-SPECIFICATION></VALUE>
          </PORT-DEFINED-ARGUMENT-VALUE></PORT-ARG-VALUES></PORT-API-OPTION></PORT-API-OPTIONS>""" if include_port_value else ""
        return f"""<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>P</SHORT-NAME><ELEMENTS>
        <IMPLEMENTATION-DATA-TYPE><SHORT-NAME>T</SHORT-NAME><CATEGORY>VALUE</CATEGORY></IMPLEMENTATION-DATA-TYPE>
        <IMPLEMENTATION-DATA-TYPE><SHORT-NAME>U</SHORT-NAME><CATEGORY>STRUCTURE</CATEGORY></IMPLEMENTATION-DATA-TYPE>
        <CLIENT-SERVER-INTERFACE><SHORT-NAME>I1</SHORT-NAME><OPERATIONS><CLIENT-SERVER-OPERATION><SHORT-NAME>O1</SHORT-NAME></CLIENT-SERVER-OPERATION></OPERATIONS></CLIENT-SERVER-INTERFACE>
        <CLIENT-SERVER-INTERFACE><SHORT-NAME>I2</SHORT-NAME><OPERATIONS><CLIENT-SERVER-OPERATION><SHORT-NAME>O2</SHORT-NAME><ARGUMENTS>
          <ARGUMENT-DATA-PROTOTYPE><SHORT-NAME>A</SHORT-NAME><TYPE-TREF>/P/{second_type}</TYPE-TREF><DIRECTION>IN</DIRECTION><SERVER-ARGUMENT-IMPL-POLICY>{policy}</SERVER-ARGUMENT-IMPL-POLICY></ARGUMENT-DATA-PROTOTYPE>
        </ARGUMENTS></CLIENT-SERVER-OPERATION></OPERATIONS></CLIENT-SERVER-INTERFACE>
        <APPLICATION-SW-COMPONENT-TYPE><SHORT-NAME>S</SHORT-NAME><PORTS>
          <P-PORT-PROTOTYPE><SHORT-NAME>P1</SHORT-NAME><PROVIDED-INTERFACE-TREF>/P/I1</PROVIDED-INTERFACE-TREF></P-PORT-PROTOTYPE>
          <P-PORT-PROTOTYPE><SHORT-NAME>P2</SHORT-NAME><PROVIDED-INTERFACE-TREF>/P/I2</PROVIDED-INTERFACE-TREF></P-PORT-PROTOTYPE>
        </PORTS><INTERNAL-BEHAVIORS><SWC-INTERNAL-BEHAVIOR><SHORT-NAME>IB</SHORT-NAME>
          <RUNNABLES><RUNNABLE-ENTITY><SHORT-NAME>R</SHORT-NAME><ARGUMENTS>{runnable_args}</ARGUMENTS></RUNNABLE-ENTITY></RUNNABLES>
          {port_option}
          <EVENTS>
            <OPERATION-INVOKED-EVENT><SHORT-NAME>E1</SHORT-NAME><START-ON-EVENT-REF>/P/S/IB/R</START-ON-EVENT-REF><OPERATION-IREF><CONTEXT-P-PORT-REF>/P/S/P1</CONTEXT-P-PORT-REF><TARGET-PROVIDED-OPERATION-REF>/P/I1/O1</TARGET-PROVIDED-OPERATION-REF></OPERATION-IREF></OPERATION-INVOKED-EVENT>
            <OPERATION-INVOKED-EVENT><SHORT-NAME>E2</SHORT-NAME><START-ON-EVENT-REF>/P/S/IB/R</START-ON-EVENT-REF><OPERATION-IREF><CONTEXT-P-PORT-REF>/P/S/P2</CONTEXT-P-PORT-REF><TARGET-PROVIDED-OPERATION-REF>/P/I2/O2</TARGET-PROVIDED-OPERATION-REF></OPERATION-IREF></OPERATION-INVOKED-EVENT>
          </EVENTS>
        </SWC-INTERNAL-BEHAVIOR></INTERNAL-BEHAVIORS></APPLICATION-SW-COMPONENT-TYPE>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""

    def test_runnable_signature_compares_port_value_with_formal_argument(self) -> None:
        result = self.validate(
            self.runnable_signature_xml(),
            rule("constr_2000", "runnable_operation_signatures", ["OPERATION-INVOKED-EVENT"]),
        )
        self.assertEqual("PASS", result["decision"])

    def test_runnable_signature_rejects_incompatible_port_value_and_formal_argument(self) -> None:
        result = self.validate(
            self.runnable_signature_xml(second_type="U"),
            rule("constr_2000", "runnable_operation_signatures", ["OPERATION-INVOKED-EVENT"]),
        )
        self.assertEqual("FAIL", result["decision"])
        self.assertIn("effective argument 1", result["findings"][0]["evidence"]["reason"])

    def test_runnable_argument_cardinality_counts_context_port_values(self) -> None:
        result = self.validate(
            self.runnable_signature_xml(runnable_arg_count=1),
            rule("constr_1164", "runnable_argument_cardinality", ["OPERATION-INVOKED-EVENT"]),
        )
        # Both events independently require one generated argument: one implicit on P1, one formal on P2.
        self.assertEqual("PASS", result["decision"])

    def test_runnable_signature_missing_context_port_is_not_evaluated(self) -> None:
        xml = """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>P</SHORT-NAME><ELEMENTS>
        <RUNNABLE-ENTITY><SHORT-NAME>R</SHORT-NAME></RUNNABLE-ENTITY>
        <CLIENT-SERVER-OPERATION><SHORT-NAME>O1</SHORT-NAME></CLIENT-SERVER-OPERATION>
        <CLIENT-SERVER-OPERATION><SHORT-NAME>O2</SHORT-NAME></CLIENT-SERVER-OPERATION>
        <OPERATION-INVOKED-EVENT><SHORT-NAME>E1</SHORT-NAME><START-ON-EVENT-REF>/P/R</START-ON-EVENT-REF><TARGET-PROVIDED-OPERATION-REF>/P/O1</TARGET-PROVIDED-OPERATION-REF></OPERATION-INVOKED-EVENT>
        <OPERATION-INVOKED-EVENT><SHORT-NAME>E2</SHORT-NAME><START-ON-EVENT-REF>/P/R</START-ON-EVENT-REF><TARGET-PROVIDED-OPERATION-REF>/P/O2</TARGET-PROVIDED-OPERATION-REF></OPERATION-INVOKED-EVENT>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""
        result = self.validate(xml, rule("constr_2000", "runnable_operation_signatures", ["OPERATION-INVOKED-EVENT"]))
        self.assertEqual("INCOMPLETE", result["decision"])

    def test_use_void_allows_arbitrary_implementation_types(self) -> None:
        xml = self.runnable_signature_xml(second_type="U", policy="USE-VOID", include_port_value=False).replace(
            "<CLIENT-SERVER-OPERATION><SHORT-NAME>O1</SHORT-NAME></CLIENT-SERVER-OPERATION>",
            "<CLIENT-SERVER-OPERATION><SHORT-NAME>O1</SHORT-NAME><ARGUMENTS><ARGUMENT-DATA-PROTOTYPE><SHORT-NAME>A</SHORT-NAME><TYPE-TREF>/P/T</TYPE-TREF><DIRECTION>IN</DIRECTION><SERVER-ARGUMENT-IMPL-POLICY>USE-VOID</SERVER-ARGUMENT-IMPL-POLICY></ARGUMENT-DATA-PROTOTYPE></ARGUMENTS></CLIENT-SERVER-OPERATION>",
        )
        result = self.validate(xml, rule("constr_2000", "runnable_operation_signatures", ["OPERATION-INVOKED-EVENT"]))
        self.assertEqual("PASS", result["decision"])

    @staticmethod
    def scaling_definition_xml(category: str, coefficients: str) -> str:
        method = lambda name: f"""<COMPU-METHOD><SHORT-NAME>{name}</SHORT-NAME><CATEGORY>{category}</CATEGORY>{coefficients}</COMPU-METHOD>"""
        return f"""<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>P</SHORT-NAME><ELEMENTS>
        {method('C1')}{method('C2')}
        <APPLICATION-PRIMITIVE-DATA-TYPE><SHORT-NAME>T1</SHORT-NAME><CATEGORY>VALUE</CATEGORY><SW-DATA-DEF-PROPS><COMPU-METHOD-REF>/P/C1</COMPU-METHOD-REF></SW-DATA-DEF-PROPS></APPLICATION-PRIMITIVE-DATA-TYPE>
        <APPLICATION-PRIMITIVE-DATA-TYPE><SHORT-NAME>T2</SHORT-NAME><CATEGORY>VALUE</CATEGORY><SW-DATA-DEF-PROPS><COMPU-METHOD-REF>/P/C2</COMPU-METHOD-REF></SW-DATA-DEF-PROPS></APPLICATION-PRIMITIVE-DATA-TYPE>
        <SENDER-RECEIVER-INTERFACE><SHORT-NAME>I1</SHORT-NAME><DATA-ELEMENTS><VARIABLE-DATA-PROTOTYPE><SHORT-NAME>D</SHORT-NAME><TYPE-TREF>/P/T1</TYPE-TREF></VARIABLE-DATA-PROTOTYPE></DATA-ELEMENTS></SENDER-RECEIVER-INTERFACE>
        <SENDER-RECEIVER-INTERFACE><SHORT-NAME>I2</SHORT-NAME><DATA-ELEMENTS><VARIABLE-DATA-PROTOTYPE><SHORT-NAME>D</SHORT-NAME><TYPE-TREF>/P/T2</TYPE-TREF></VARIABLE-DATA-PROTOTYPE></DATA-ELEMENTS></SENDER-RECEIVER-INTERFACE>
        <P-PORT-PROTOTYPE><SHORT-NAME>PP</SHORT-NAME><PROVIDED-INTERFACE-TREF>/P/I1</PROVIDED-INTERFACE-TREF></P-PORT-PROTOTYPE>
        <R-PORT-PROTOTYPE><SHORT-NAME>RP</SHORT-NAME><REQUIRED-INTERFACE-TREF>/P/I2</REQUIRED-INTERFACE-TREF></R-PORT-PROTOTYPE>
        <ASSEMBLY-SW-CONNECTOR><SHORT-NAME>C</SHORT-NAME><PROVIDER-IREF><TARGET-P-PORT-REF>/P/PP</TARGET-P-PORT-REF></PROVIDER-IREF><REQUESTER-IREF><TARGET-R-PORT-REF>/P/RP</TARGET-R-PORT-REF></REQUESTER-IREF></ASSEMBLY-SW-CONNECTOR>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""

    def test_linear_scaling_definition_checks_exact_coefficients(self) -> None:
        coefficients = """<COMPU-INTERNAL-TO-PHYS><COMPU-SCALES><COMPU-SCALE><COMPU-RATIONAL-COEFFS>
          <COMPU-NUMERATOR><V>5</V><V>2</V><V>0</V></COMPU-NUMERATOR>
          <COMPU-DENOMINATOR><V>3</V><V>0</V></COMPU-DENOMINATOR>
        </COMPU-RATIONAL-COEFFS></COMPU-SCALE></COMPU-SCALES></COMPU-INTERNAL-TO-PHYS>"""
        result = self.validate(
            self.scaling_definition_xml("LINEAR", coefficients),
            rule("TPS_SWCT_01549", "communication_compu_scale_compatibility", CONNECTORS),
        )
        self.assertEqual("PASS", result["decision"])
        observation = result["rules"][0]["observations"][0]
        self.assertTrue(observation["qualifies"])
        self.assertEqual("linear", observation["kind"])

    def test_reciprocal_linear_definition_classifies_nonmatching_formula(self) -> None:
        coefficients = """<COMPU-INTERNAL-TO-PHYS><COMPU-SCALES><COMPU-SCALE><COMPU-RATIONAL-COEFFS>
          <COMPU-NUMERATOR><V>1</V><V>1</V></COMPU-NUMERATOR>
          <COMPU-DENOMINATOR><V>0</V><V>1</V></COMPU-DENOMINATOR>
        </COMPU-RATIONAL-COEFFS></COMPU-SCALE></COMPU-SCALES></COMPU-INTERNAL-TO-PHYS>"""
        result = self.validate(
            self.scaling_definition_xml("RAT_FUNC", coefficients),
            rule("TPS_SWCT_01550", "communication_compu_scale_compatibility", CONNECTORS),
        )
        self.assertEqual("PASS", result["decision"])
        self.assertFalse(result["rules"][0]["observations"][0]["qualifies"])

    def test_linear_scaling_missing_formula_is_not_evaluated(self) -> None:
        result = self.validate(
            self.scaling_definition_xml("LINEAR", ""),
            rule("TPS_SWCT_01549", "communication_compu_scale_compatibility", CONNECTORS),
        )
        self.assertEqual("INCOMPLETE", result["decision"])

    @staticmethod
    def prototype_mapping_xml(*, second_category: str, submapping: str = "", first_name: str = "A", second_name: str = "B") -> str:
        return f"""<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>P</SHORT-NAME><ELEMENTS>
        <APPLICATION-PRIMITIVE-DATA-TYPE><SHORT-NAME>T1</SHORT-NAME><CATEGORY>VALUE</CATEGORY></APPLICATION-PRIMITIVE-DATA-TYPE>
        <APPLICATION-PRIMITIVE-DATA-TYPE><SHORT-NAME>T2</SHORT-NAME><CATEGORY>{second_category}</CATEGORY></APPLICATION-PRIMITIVE-DATA-TYPE>
        <APPLICATION-RECORD-DATA-TYPE><SHORT-NAME>R1</SHORT-NAME><CATEGORY>STRUCTURE</CATEGORY><ELEMENTS><APPLICATION-RECORD-ELEMENT><SHORT-NAME>{first_name}</SHORT-NAME><TYPE-TREF>/P/T1</TYPE-TREF></APPLICATION-RECORD-ELEMENT></ELEMENTS></APPLICATION-RECORD-DATA-TYPE>
        <APPLICATION-RECORD-DATA-TYPE><SHORT-NAME>R2</SHORT-NAME><CATEGORY>STRUCTURE</CATEGORY><ELEMENTS><APPLICATION-RECORD-ELEMENT><SHORT-NAME>{second_name}</SHORT-NAME><TYPE-TREF>/P/T2</TYPE-TREF></APPLICATION-RECORD-ELEMENT></ELEMENTS></APPLICATION-RECORD-DATA-TYPE>
        <VARIABLE-DATA-PROTOTYPE><SHORT-NAME>V1</SHORT-NAME><TYPE-TREF>/P/R1</TYPE-TREF></VARIABLE-DATA-PROTOTYPE>
        <VARIABLE-DATA-PROTOTYPE><SHORT-NAME>V2</SHORT-NAME><TYPE-TREF>/P/R2</TYPE-TREF></VARIABLE-DATA-PROTOTYPE>
        <DATA-PROTOTYPE-MAPPING><FIRST-DATA-PROTOTYPE-REF>/P/V1</FIRST-DATA-PROTOTYPE-REF><SECOND-DATA-PROTOTYPE-REF>/P/V2</SECOND-DATA-PROTOTYPE-REF>{submapping}</DATA-PROTOTYPE-MAPPING>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""

    def test_primitive_mapping_is_normative_compatibility_override(self) -> None:
        xml = """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>P</SHORT-NAME><ELEMENTS>
        <APPLICATION-PRIMITIVE-DATA-TYPE><SHORT-NAME>T1</SHORT-NAME><CATEGORY>VALUE</CATEGORY></APPLICATION-PRIMITIVE-DATA-TYPE>
        <APPLICATION-PRIMITIVE-DATA-TYPE><SHORT-NAME>T2</SHORT-NAME><CATEGORY>STRING</CATEGORY></APPLICATION-PRIMITIVE-DATA-TYPE>
        <VARIABLE-DATA-PROTOTYPE><SHORT-NAME>V1</SHORT-NAME><TYPE-TREF>/P/T1</TYPE-TREF></VARIABLE-DATA-PROTOTYPE>
        <VARIABLE-DATA-PROTOTYPE><SHORT-NAME>V2</SHORT-NAME><TYPE-TREF>/P/T2</TYPE-TREF></VARIABLE-DATA-PROTOTYPE>
        <DATA-PROTOTYPE-MAPPING><FIRST-DATA-PROTOTYPE-REF>/P/V1</FIRST-DATA-PROTOTYPE-REF><SECOND-DATA-PROTOTYPE-REF>/P/V2</SECOND-DATA-PROTOTYPE-REF></DATA-PROTOTYPE-MAPPING>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""
        result = self.validate(xml, rule("constr_1047", "compatibility_kernel_context_audit", ["APPLICATION-PRIMITIVE-DATA-TYPE"]))
        self.assertEqual("PASS", result["decision"])
        observation = result["rules"][0]["observations"][0]
        self.assertFalse(observation["direct_compatible"])
        self.assertTrue(observation["mapping_override"])

    def test_record_mapping_without_complete_submapping_fails(self) -> None:
        result = self.validate(
            self.prototype_mapping_xml(second_category="STRING"),
            rule("constr_1048", "compatibility_kernel_context_audit", ["APPLICATION-RECORD-DATA-TYPE"]),
        )
        self.assertEqual("FAIL", result["decision"])
        self.assertIn("complete normative mapping override", result["findings"][0]["message"])

    def test_record_mapping_complete_required_side_override_passes(self) -> None:
        submapping = """<SUB-ELEMENT-MAPPINGS><SUB-ELEMENT-MAPPING>
          <FIRST-ELEMENTS><FIRST-ELEMENT-REF>/P/R1/A</FIRST-ELEMENT-REF></FIRST-ELEMENTS>
          <SECOND-ELEMENTS><SECOND-ELEMENT-REF>/P/R2/B</SECOND-ELEMENT-REF></SECOND-ELEMENTS>
        </SUB-ELEMENT-MAPPING></SUB-ELEMENT-MAPPINGS>"""
        result = self.validate(
            self.prototype_mapping_xml(second_category="STRING", submapping=submapping),
            rule("constr_1048", "compatibility_kernel_context_audit", ["APPLICATION-RECORD-DATA-TYPE"]),
        )
        self.assertEqual("PASS", result["decision"])
        self.assertTrue(result["rules"][0]["observations"][0]["mapping_override"])

    def test_record_direct_compatibility_does_not_require_equal_element_names(self) -> None:
        result = self.validate(
            self.prototype_mapping_xml(second_category="VALUE", first_name="First", second_name="Second"),
            rule("constr_1048", "compatibility_kernel_context_audit", ["APPLICATION-RECORD-DATA-TYPE"]),
        )
        self.assertEqual("PASS", result["decision"])
        self.assertTrue(result["rules"][0]["observations"][0]["direct_compatible"])


if __name__ == "__main__":
    unittest.main()
