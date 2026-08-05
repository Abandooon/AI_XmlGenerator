from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.validation.v2.engine import ValidationEngine


def rule(constraint_id: str, plugin: str, tags: list[str]) -> dict:
    return {
        "rule_id": f"{constraint_id}#r1",
        "constraint_id": constraint_id,
        "source_sha256": "0" * 64,
        "title": constraint_id,
        "severity": "error",
        "policy": "must",
        "backend": "python",
        "implementation": {"status": "implemented", "plugin": plugin, "reason": "reviewed"},
        "selector": {"tags": tags, "mode": "any" if tags else "global"},
        "parameters": {},
        "completeness": {"requires": ["well_formed_xml"], "on_missing": "not_evaluated"},
        "dependencies": [],
        "bindings": [],
    }


class QualifiedPluginTests(unittest.TestCase):
    def validate(self, xml: str, validation_rule: dict) -> dict:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.arxml"
            path.write_text(xml, encoding="utf-8")
            return ValidationEngine({"rules": [validation_rule]}).validate([path])

    def test_application_error_code_exception_and_boundaries(self) -> None:
        validation_rule = rule("constr_1108", "application_error_code_range", ["APPLICATION-ERROR"])
        valid = self.validate(
            "<AUTOSAR><APPLICATION-ERROR><SHORT-NAME>E_OK</SHORT-NAME><ERROR-CODE>0</ERROR-CODE></APPLICATION-ERROR>"
            "<APPLICATION-ERROR><SHORT-NAME>E_X</SHORT-NAME><ERROR-CODE>63</ERROR-CODE></APPLICATION-ERROR></AUTOSAR>",
            validation_rule,
        )
        self.assertEqual("PASS", valid["decision"])
        invalid = self.validate(
            "<AUTOSAR><APPLICATION-ERROR><SHORT-NAME>E_X</SHORT-NAME><ERROR-CODE>0</ERROR-CODE></APPLICATION-ERROR>"
            "<APPLICATION-ERROR><SHORT-NAME>E_Y</SHORT-NAME><ERROR-CODE>64</ERROR-CODE></APPLICATION-ERROR></AUTOSAR>",
            validation_rule,
        )
        self.assertEqual("FAIL", invalid["decision"])
        self.assertEqual(2, invalid["summary"]["finding_count"])

    def test_rational_denominator_uses_grounded_smt_interval(self) -> None:
        validation_rule = rule("constr_1025", "rational_formula_denominator_nonzero", ["COMPU-RATIONAL-COEFFS"])
        invalid = self.validate(
            "<AUTOSAR><COMPU-SCALE><LOWER-LIMIT>-1</LOWER-LIMIT><UPPER-LIMIT>1</UPPER-LIMIT>"
            "<COMPU-RATIONAL-COEFFS><COMPU-DENOMINATOR><V>0</V><V>1</V></COMPU-DENOMINATOR>"
            "</COMPU-RATIONAL-COEFFS></COMPU-SCALE></AUTOSAR>",
            validation_rule,
        )
        self.assertEqual("FAIL", invalid["decision"])
        self.assertEqual("0", invalid["findings"][0]["evidence"]["counterexample"])
        valid = self.validate(
            "<AUTOSAR><COMPU-SCALE><LOWER-LIMIT>-1</LOWER-LIMIT><UPPER-LIMIT>1</UPPER-LIMIT>"
            "<COMPU-RATIONAL-COEFFS><COMPU-DENOMINATOR><V>1</V></COMPU-DENOMINATOR>"
            "</COMPU-RATIONAL-COEFFS></COMPU-SCALE></AUTOSAR>",
            validation_rule,
        )
        self.assertEqual("PASS", valid["decision"])

    def test_equal_compu_symbols_require_equal_ranges(self) -> None:
        validation_rule = rule("constr_1133", "compu_symbol_ranges_consistent", ["COMPU-METHOD"])
        invalid = self.validate(
            "<AUTOSAR><COMPU-METHOD><COMPU-INTERNAL-TO-PHYS><COMPU-SCALES>"
            "<COMPU-SCALE><SYMBOL>S</SYMBOL><LOWER-LIMIT>0</LOWER-LIMIT><UPPER-LIMIT>1</UPPER-LIMIT></COMPU-SCALE>"
            "<COMPU-SCALE><SYMBOL>S</SYMBOL><LOWER-LIMIT>0</LOWER-LIMIT><UPPER-LIMIT>2</UPPER-LIMIT></COMPU-SCALE>"
            "</COMPU-SCALES></COMPU-INTERNAL-TO-PHYS></COMPU-METHOD></AUTOSAR>",
            validation_rule,
        )
        self.assertEqual("FAIL", invalid["decision"])

    def test_reference_index_is_limited_to_enumerated_contexts(self) -> None:
        validation_rule = rule("constr_1161", "reference_index_context", [])
        valid = self.validate(
            '<AUTOSAR><AUTOSAR-VARIABLE-REF><TARGET-DATA-PROTOTYPE-REF INDEX="1">/P/V</TARGET-DATA-PROTOTYPE-REF></AUTOSAR-VARIABLE-REF></AUTOSAR>',
            validation_rule,
        )
        self.assertEqual("PASS", valid["decision"])
        invalid = self.validate(
            '<AUTOSAR><UNRELATED><TARGET-DATA-PROTOTYPE-REF INDEX="1">/P/V</TARGET-DATA-PROTOTYPE-REF></UNRELATED></AUTOSAR>',
            validation_rule,
        )
        self.assertEqual("FAIL", invalid["decision"])
        self.assertEqual("remove_attribute", invalid["repair"]["actions"][0]["action"])

    def test_function_pointer_and_nested_pointer_are_rejected(self) -> None:
        function_rule = rule("TPS_SWCT_01574", "per_instance_memory_no_function_pointer", ["PER-INSTANCE-MEMORY"])
        invalid_function = self.validate(
            "<AUTOSAR><PER-INSTANCE-MEMORY><TYPE-DEFINITION>typedef void (*Handler)(int);</TYPE-DEFINITION></PER-INSTANCE-MEMORY></AUTOSAR>",
            function_rule,
        )
        self.assertEqual("FAIL", invalid_function["decision"])
        valid_object = self.validate(
            "<AUTOSAR><PER-INSTANCE-MEMORY><TYPE-DEFINITION>typedef struct { int value; } State;</TYPE-DEFINITION></PER-INSTANCE-MEMORY></AUTOSAR>",
            function_rule,
        )
        self.assertEqual("PASS", valid_object["decision"])

        pointer_rule = rule("constr_1254", "pointer_to_pointer_forbidden", ["IMPLEMENTATION-DATA-TYPE"])
        invalid_pointer = self.validate(
            "<AUTOSAR><IMPLEMENTATION-DATA-TYPE><CATEGORY>DATA_REFERENCE</CATEGORY>"
            "<SW-POINTER-TARGET-PROPS><TARGET-CATEGORY>DATA_REFERENCE</TARGET-CATEGORY><SW-DATA-DEF-PROPS>"
            "<SW-POINTER-TARGET-PROPS><TARGET-CATEGORY>VALUE</TARGET-CATEGORY></SW-POINTER-TARGET-PROPS>"
            "</SW-DATA-DEF-PROPS></SW-POINTER-TARGET-PROPS></IMPLEMENTATION-DATA-TYPE></AUTOSAR>",
            pointer_rule,
        )
        self.assertEqual("FAIL", invalid_pointer["decision"])

    def test_variable_scope_and_compu_domain_limits(self) -> None:
        scope_rule = rule("constr_1141", "variable_access_scope_context", ["VARIABLE-ACCESS"])
        invalid_scope = self.validate(
            "<AUTOSAR><OTHER-ROLE><VARIABLE-ACCESS><SCOPE>LOCAL</SCOPE></VARIABLE-ACCESS></OTHER-ROLE></AUTOSAR>",
            scope_rule,
        )
        self.assertEqual("FAIL", invalid_scope["decision"])
        valid_scope = self.validate(
            "<AUTOSAR><DATA-READ-ACCESSS><VARIABLE-ACCESS><SCOPE>LOCAL</SCOPE></VARIABLE-ACCESS></DATA-READ-ACCESSS></AUTOSAR>",
            scope_rule,
        )
        self.assertEqual("PASS", valid_scope["decision"])

        limits_rule = rule("constr_1022", "compu_both_domains_have_limits", ["COMPU-METHOD"])
        invalid_limits = self.validate(
            "<AUTOSAR><COMPU-METHOD><COMPU-INTERNAL-TO-PHYS><COMPU-SCALE><LOWER-LIMIT>0</LOWER-LIMIT></COMPU-SCALE></COMPU-INTERNAL-TO-PHYS>"
            "<COMPU-PHYS-TO-INTERNAL><COMPU-SCALE><LOWER-LIMIT>0</LOWER-LIMIT><UPPER-LIMIT>1</UPPER-LIMIT></COMPU-SCALE></COMPU-PHYS-TO-INTERNAL>"
            "</COMPU-METHOD></AUTOSAR>",
            limits_rule,
        )
        self.assertEqual("FAIL", invalid_limits["decision"])

    def test_core_local_policy_resolves_memory_section_reference(self) -> None:
        validation_rule = rule("constr_1402", "core_local_init_policy", ["SW-ADDR-METHOD", "MEMORY-SECTION"])
        xml = """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>P</SHORT-NAME><ELEMENTS>
        <SW-ADDR-METHOD><SHORT-NAME>A</SHORT-NAME><SECTION-INITIALIZATION-POLICY>NO-INIT</SECTION-INITIALIZATION-POLICY></SW-ADDR-METHOD>
        <MEMORY-SECTION><SHORT-NAME>M</SHORT-NAME><OPTIONS><OPTION>coreLocal</OPTION></OPTIONS><SW-ADDR-METHOD-REF>/P/A</SW-ADDR-METHOD-REF></MEMORY-SECTION>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""
        report = self.validate(xml, validation_rule)
        self.assertEqual("FAIL", report["decision"])
        self.assertEqual(1, report["summary"]["finding_count"])

    def test_nv_mapping_role_checks_resolved_port_kind(self) -> None:
        validation_rule = rule("constr_1285", "nv_mapping_port_role", ["NV-BLOCK-DATA-MAPPING"])
        xml = """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>P</SHORT-NAME><ELEMENTS>
        <P-PORT-PROTOTYPE><SHORT-NAME>Provided</SHORT-NAME></P-PORT-PROTOTYPE>
        <NV-BLOCK-DATA-MAPPING><WRITTEN-NV-DATA><AUTOSAR-VARIABLE-IREF><PORT-PROTOTYPE-REF>/P/Provided</PORT-PROTOTYPE-REF></AUTOSAR-VARIABLE-IREF></WRITTEN-NV-DATA></NV-BLOCK-DATA-MAPPING>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""
        report = self.validate(xml, validation_rule)
        self.assertEqual("FAIL", report["decision"])
        self.assertEqual("R-PORT-PROTOTYPE", report["findings"][0]["evidence"]["expected"])

    def test_autosar_parameter_variable_target_requires_grouped_axis(self) -> None:
        validation_rule = rule("constr_1173", "autosar_parameter_variable_context", ["AUTOSAR-PARAMETER-REF"])
        xml = """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>P</SHORT-NAME><ELEMENTS>
        <VARIABLE-DATA-PROTOTYPE><SHORT-NAME>V</SHORT-NAME></VARIABLE-DATA-PROTOTYPE>
        <AUTOSAR-PARAMETER-REF><TARGET-DATA-PROTOTYPE-REF>/P/V</TARGET-DATA-PROTOTYPE-REF></AUTOSAR-PARAMETER-REF>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""
        report = self.validate(xml, validation_rule)
        self.assertEqual("FAIL", report["decision"])


if __name__ == "__main__":
    unittest.main()
