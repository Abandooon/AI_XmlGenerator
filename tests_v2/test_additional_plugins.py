from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.validation.v2.engine import ValidationEngine


def make_rule(rule_id: str, plugin: str, tags: list[str], parameters: dict | None = None, requires: list[str] | None = None) -> dict:
    return {
        "rule_id": rule_id,
        "constraint_id": rule_id.split("#", 1)[0],
        "title": rule_id,
        "severity": "error",
        "policy": "must",
        "implementation": {"status": "implemented", "plugin": plugin},
        "selector": {"tags": tags, "mode": "any"},
        "parameters": parameters or {},
        "completeness": {"requires": requires or ["well_formed_xml"], "on_missing": "not_evaluated"},
        "dependencies": [],
        "bindings": [],
    }


class AdditionalPluginTest(unittest.TestCase):
    def validate(self, xml: str, rules: list[dict]) -> dict:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.arxml"
            path.write_text(xml, encoding="utf-8")
            return ValidationEngine({"rules": rules}).validate([path])

    def test_direct_value_rules_fail(self) -> None:
        xml = """<AUTOSAR>
        <RUNNABLE-ENTITY><SHORT-NAME>R</SHORT-NAME><REENTRANCY-LEVEL>1</REENTRANCY-LEVEL></RUNNABLE-ENTITY>
        <TIMING-EVENT><SHORT-NAME>T</SHORT-NAME><PERIOD>0</PERIOD></TIMING-EVENT>
        <EXECUTABLE-ENTITY-ACTIVATION-REASON><BIT-POSITION>32</BIT-POSITION></EXECUTABLE-ENTITY-ACTIVATION-REASON>
        </AUTOSAR>"""
        result = self.validate(xml, [
            make_rule("constr_4082#r1", "forbid_descendant_tags", ["RUNNABLE-ENTITY"], {"forbidden_tags": ["REENTRANCY-LEVEL"]}),
            make_rule("constr_2031#r1", "numeric_range", ["TIMING-EVENT"], {"value_tag": "PERIOD", "minimum": 0, "minimum_exclusive": True}),
            make_rule("constr_1226#r1", "numeric_range", ["EXECUTABLE-ENTITY-ACTIVATION-REASON"], {"value_tag": "BIT-POSITION", "minimum": 0, "maximum": 31}),
        ])
        self.assertEqual("FAIL", result["decision"])
        self.assertEqual(3, result["summary"]["FAIL"])

    def test_mode_ordering_rules(self) -> None:
        xml = """<AUTOSAR><MODE-DECLARATION-GROUP><SHORT-NAME>M</SHORT-NAME>
        <CATEGORY>EXPLICIT-ORDER</CATEGORY><ON-TRANSITION-VALUE>1</ON-TRANSITION-VALUE>
        <MODE-DECLARATIONS><MODE-DECLARATION><SHORT-NAME>A</SHORT-NAME><VALUE>1</VALUE></MODE-DECLARATION>
        <MODE-DECLARATION><SHORT-NAME>B</SHORT-NAME></MODE-DECLARATION></MODE-DECLARATIONS>
        </MODE-DECLARATION-GROUP></AUTOSAR>"""
        result = self.validate(xml, [
            make_rule("constr_1298#r1", "mode_declaration_group_ordering", ["MODE-DECLARATION-GROUP"], {"check": "explicit_requires_values"}),
            make_rule("constr_1181#r1", "mode_declaration_group_ordering", ["MODE-DECLARATION-GROUP"], {"check": "values_do_not_overlap"}),
        ])
        self.assertEqual("FAIL", result["decision"])
        self.assertEqual(2, result["summary"]["FAIL"])

    def test_init_event_resolves_runnable(self) -> None:
        xml = """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>Pkg</SHORT-NAME><ELEMENTS>
        <RUNNABLE-ENTITY><SHORT-NAME>R</SHORT-NAME><MINIMUM-START-INTERVAL>1</MINIMUM-START-INTERVAL><WAIT-POINT><SHORT-NAME>W</SHORT-NAME></WAIT-POINT></RUNNABLE-ENTITY>
        <INIT-EVENT><SHORT-NAME>I</SHORT-NAME><START-ON-EVENT-REF>/Pkg/R</START-ON-EVENT-REF></INIT-EVENT>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""
        result = self.validate(xml, [
            make_rule("constr_1257#r1", "init_event_runnable_shape", ["INIT-EVENT"], {"check": "no_wait_point"}, ["well_formed_xml", "complete_reference_scope"]),
            make_rule("constr_1258#r1", "init_event_runnable_shape", ["INIT-EVENT"], {"check": "minimum_start_interval_zero"}, ["well_formed_xml", "complete_reference_scope"]),
        ])
        self.assertEqual("FAIL", result["decision"])
        self.assertEqual(2, result["summary"]["FAIL"])

    def test_nv_cyclic_iff_rules(self) -> None:
        xml = """<AUTOSAR><NV-BLOCK-DESCRIPTOR><SHORT-NAME>D</SHORT-NAME><NV-BLOCK-NEEDS>
        <STORE-CYCLIC>true</STORE-CYCLIC><N-DATA-SETS>1</N-DATA-SETS><RELIABILITY>ERROR-CORRECTION</RELIABILITY>
        </NV-BLOCK-NEEDS></NV-BLOCK-DESCRIPTOR></AUTOSAR>"""
        result = self.validate(xml, [
            make_rule("constr_1095#r1", "nv_dataset_reliability", ["NV-BLOCK-NEEDS"]),
            make_rule("constr_1308#r1", "nv_cyclic_period_iff", ["NV-BLOCK-NEEDS"]),
            make_rule("constr_1309#r1", "nv_timing_event_iff", ["NV-BLOCK-DESCRIPTOR"]),
        ])
        self.assertEqual("FAIL", result["decision"])
        self.assertEqual(3, result["summary"]["FAIL"])

    def test_rpt_system_category(self) -> None:
        xml = """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>Pkg</SHORT-NAME><ELEMENTS>
        <SYSTEM><SHORT-NAME>S</SHORT-NAME><CATEGORY>NOT-RPT</CATEGORY></SYSTEM>
        <RAPID-PROTOTYPING-SCENARIO><SHORT-NAME>Scenario</SHORT-NAME><RPT-SYSTEM-REF>/Pkg/S</RPT-SYSTEM-REF></RAPID-PROTOTYPING-SCENARIO>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""
        result = self.validate(xml, [make_rule("constr_2054#r1", "rpt_system_category", ["RAPID-PROTOTYPING-SCENARIO"], {}, ["well_formed_xml", "complete_reference_scope"])])
        self.assertEqual("FAIL", result["decision"])


if __name__ == "__main__":
    unittest.main()
