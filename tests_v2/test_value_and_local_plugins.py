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


class ValueAndLocalPluginTests(unittest.TestCase):
    def validate(self, xml: str, validation_rule: dict) -> dict:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.arxml"
            path.write_text(xml, encoding="utf-8")
            return ValidationEngine({"rules": [validation_rule]}).validate([path])

    def test_declared_outside_scope_requires_numerical_value(self) -> None:
        xml = """<AUTOSAR><APPLICATION-PRIMITIVE-DATA-TYPE><SHORT-NAME>T</SHORT-NAME><CATEGORY>VALUE</CATEGORY>
        <SW-DATA-DEF-PROPS><INVALID-VALUE><APPLICATION-VALUE-SPECIFICATION><VALUE>1</VALUE></APPLICATION-VALUE-SPECIFICATION></INVALID-VALUE></SW-DATA-DEF-PROPS>
        </APPLICATION-PRIMITIVE-DATA-TYPE></AUTOSAR>"""
        result = self.validate(xml, rule("constr_1283", "declared_invalid_value_scope", ["APPLICATION-PRIMITIVE-DATA-TYPE"]))
        self.assertEqual("FAIL", result["decision"])
        self.assertEqual("NUMERICAL-VALUE-SPECIFICATION", result["findings"][0]["evidence"]["expected"])

    def test_blocking_returns_event_must_not_start_runnable(self) -> None:
        xml = """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>P</SHORT-NAME><ELEMENTS>
        <ASYNCHRONOUS-SERVER-CALL-RESULT-POINT><SHORT-NAME>RP</SHORT-NAME></ASYNCHRONOUS-SERVER-CALL-RESULT-POINT>
        <RUNNABLE-ENTITY><SHORT-NAME>R</SHORT-NAME></RUNNABLE-ENTITY>
        <ASYNCHRONOUS-SERVER-CALL-RETURNS-EVENT><SHORT-NAME>E</SHORT-NAME><RESULT-POINT-REF>/P/RP</RESULT-POINT-REF><START-ON-EVENT-REF>/P/R</START-ON-EVENT-REF></ASYNCHRONOUS-SERVER-CALL-RETURNS-EVENT>
        <WAIT-POINT><SHORT-NAME>W</SHORT-NAME><EVENT-REF>/P/E</EVENT-REF></WAIT-POINT>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""
        result = self.validate(xml, rule("TPS_SWCT_01347", "asynchronous_blocking_wait", ["ASYNCHRONOUS-SERVER-CALL-RESULT-POINT"]))
        self.assertEqual("FAIL", result["decision"])
        self.assertEqual("START-ON-EVENT-REF", result["findings"][0]["location"]["tag"])

    def test_point_scale_without_symbol_source_fails(self) -> None:
        xml = "<AUTOSAR><COMPU-SCALE><LOWER-LIMIT>1</LOWER-LIMIT><UPPER-LIMIT>1</UPPER-LIMIT><VT>not valid</VT></COMPU-SCALE></AUTOSAR>"
        result = self.validate(xml, rule("TPS_SWCT_01431", "compu_scale_c_symbol", ["COMPU-SCALE"]))
        self.assertEqual("FAIL", result["decision"])

    def test_implementation_invalid_value_must_fit_range(self) -> None:
        xml = """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>P</SHORT-NAME><ELEMENTS>
        <DATA-CONSTR><SHORT-NAME>C</SHORT-NAME><DATA-CONSTR-RULES><DATA-CONSTR-RULE><INTERNAL-CONSTRS><LOWER-LIMIT>0</LOWER-LIMIT><UPPER-LIMIT>10</UPPER-LIMIT></INTERNAL-CONSTRS></DATA-CONSTR-RULE></DATA-CONSTR-RULES></DATA-CONSTR>
        <IMPLEMENTATION-DATA-TYPE><SHORT-NAME>I</SHORT-NAME><CATEGORY>VALUE</CATEGORY><SW-DATA-DEF-PROPS><DATA-CONSTR-REF>/P/C</DATA-CONSTR-REF><INVALID-VALUE><NUMERICAL-VALUE-SPECIFICATION><VALUE>11</VALUE></NUMERICAL-VALUE-SPECIFICATION></INVALID-VALUE></SW-DATA-DEF-PROPS></IMPLEMENTATION-DATA-TYPE>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""
        result = self.validate(xml, rule("constr_2545", "implementation_invalid_value_range", ["IMPLEMENTATION-DATA-TYPE"]))
        self.assertEqual("FAIL", result["decision"])
        self.assertEqual("11", result["findings"][0]["evidence"]["actual"])

    def test_value_specification_array_shape_is_checked(self) -> None:
        xml = """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>P</SHORT-NAME><ELEMENTS>
        <APPLICATION-PRIMITIVE-DATA-TYPE><SHORT-NAME>Leaf</SHORT-NAME><CATEGORY>BOOLEAN</CATEGORY></APPLICATION-PRIMITIVE-DATA-TYPE>
        <APPLICATION-ARRAY-DATA-TYPE><SHORT-NAME>A</SHORT-NAME><CATEGORY>ARRAY</CATEGORY><ELEMENTS><APPLICATION-ARRAY-ELEMENT><SHORT-NAME>E</SHORT-NAME><MAX-NUMBER-OF-ELEMENTS>2</MAX-NUMBER-OF-ELEMENTS><ARRAY-SIZE-SEMANTICS>FIXED-SIZE</ARRAY-SIZE-SEMANTICS><TYPE-TREF>/P/Leaf</TYPE-TREF></APPLICATION-ARRAY-ELEMENT></ELEMENTS></APPLICATION-ARRAY-DATA-TYPE>
        <VARIABLE-DATA-PROTOTYPE><SHORT-NAME>D</SHORT-NAME><TYPE-TREF>/P/A</TYPE-TREF><INIT-VALUE><ARRAY-VALUE-SPECIFICATION><ELEMENTS><NUMERICAL-VALUE-SPECIFICATION><VALUE>1</VALUE></NUMERICAL-VALUE-SPECIFICATION></ELEMENTS></ARRAY-VALUE-SPECIFICATION></INIT-VALUE></VARIABLE-DATA-PROTOTYPE>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""
        result = self.validate(xml, rule("constr_4035", "value_specification_fits_type", ["ARRAY-VALUE-SPECIFICATION", "NUMERICAL-VALUE-SPECIFICATION"]))
        self.assertEqual("FAIL", result["decision"])
        self.assertIn("does not fit", result["findings"][0]["message"])

    def test_unresolved_value_type_is_not_evaluated(self) -> None:
        xml = "<AUTOSAR><VARIABLE-DATA-PROTOTYPE><TYPE-TREF>/Missing</TYPE-TREF><INIT-VALUE><NUMERICAL-VALUE-SPECIFICATION><VALUE>1</VALUE></NUMERICAL-VALUE-SPECIFICATION></INIT-VALUE></VARIABLE-DATA-PROTOTYPE></AUTOSAR>"
        result = self.validate(xml, rule("constr_4035", "value_specification_fits_type", ["NUMERICAL-VALUE-SPECIFICATION"]))
        self.assertEqual("INCOMPLETE", result["decision"])
        self.assertEqual("NOT_EVALUATED", result["rules"][0]["status"])


if __name__ == "__main__":
    unittest.main()
