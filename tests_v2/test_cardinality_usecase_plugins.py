from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.validation.v2.context import ValidationContextError, build_validation_context, normalize_validation_context
from src.validation.v2.engine import ValidationEngine

DATASET = "a" * 64


def rule(cid: str, plugin: str, tags: list[str]) -> dict:
    return {
        "rule_id": f"{cid}#r1", "constraint_id": cid, "title": cid,
        "severity": "error", "policy": "must",
        "implementation": {"status": "implemented", "plugin": plugin},
        "selector": {"tags": tags, "mode": "any"}, "parameters": {},
        "completeness": {"requires": ["well_formed_xml", "complete_reference_scope"], "on_missing": "not_evaluated"},
        "dependencies": [], "bindings": [],
    }


class CardinalityUsecasePluginTests(unittest.TestCase):
    def validate(self, xml: str, validation_rule: dict, context: dict | None = None) -> dict:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.arxml"
            path.write_text(xml, encoding="utf-8")
            return ValidationEngine({"rules": [validation_rule]}, expected_dataset_sha256=DATASET).validate([path], validation_context=context)

    def context(self, cid: str, target: str, values: dict) -> dict:
        return build_validation_context(
            {"generation": {"dataset_sha256": DATASET, "constraint_ids": [cid], "result_count": 1}},
            expected_dataset_sha256=DATASET,
            reference_scope="complete",
            declared_constraint_ids=[cid],
            declared_targets={cid: [target]},
            declared_parameters={cid: {target: values}},
        )

    def test_manifest_target_parameters_are_integrity_protected(self) -> None:
        manifest = self.context("constr_1160", "/P/D", {"expected_variant_value_count": 2})
        manifest["declared_parameters"]["constr_1160"]["/P/D"]["expected_variant_value_count"] = 3
        with self.assertRaises(ValidationContextError):
            normalize_validation_context(manifest, expected_dataset_sha256=DATASET)

    def test_variant_value_count_uses_exact_target_parameter(self) -> None:
        xml = """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>P</SHORT-NAME><ELEMENTS>
        <VARIABLE-DATA-PROTOTYPE><SHORT-NAME>D</SHORT-NAME><INIT-VALUE><ARRAY-VALUE-SPECIFICATION><ELEMENTS>
        <NUMERICAL-VALUE-SPECIFICATION><VALUE>1</VALUE></NUMERICAL-VALUE-SPECIFICATION>
        </ELEMENTS></ARRAY-VALUE-SPECIFICATION></INIT-VALUE></VARIABLE-DATA-PROTOTYPE>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""
        context = self.context("constr_1160", "/P/D", {"expected_variant_value_count": 2})
        result = self.validate(xml, rule("constr_1160", "manifest_variant_value_count", ["VARIABLE-DATA-PROTOTYPE"]), context)
        self.assertEqual("FAIL", result["decision"])
        self.assertEqual(2, result["findings"][0]["evidence"]["expected"])

    def test_missing_variant_parameter_is_not_evaluated(self) -> None:
        xml = "<AUTOSAR><VARIABLE-DATA-PROTOTYPE><SHORT-NAME>D</SHORT-NAME><INIT-VALUE><NUMERICAL-VALUE-SPECIFICATION><VALUE>1</VALUE></NUMERICAL-VALUE-SPECIFICATION></INIT-VALUE></VARIABLE-DATA-PROTOTYPE></AUTOSAR>"
        result = self.validate(xml, rule("constr_1160", "manifest_variant_value_count", ["VARIABLE-DATA-PROTOTYPE"]))
        self.assertEqual("INCOMPLETE", result["decision"])

    def test_nvm_permanent_ram_requires_ram_block_assignment(self) -> None:
        xml = "<AUTOSAR><SWC-SERVICE-DEPENDENCY><SHORT-NAME>N</SHORT-NAME></SWC-SERVICE-DEPENDENCY></AUTOSAR>"
        result = self.validate(xml, rule("TPS_SWCT_02501", "nvm_use_case_role_table", ["SWC-SERVICE-DEPENDENCY"]))
        self.assertEqual("FAIL", result["decision"])
        self.assertEqual("ramBlock", result["findings"][0]["evidence"]["role"])

    def test_variation_proxy_unlisted_attribute_has_zero_multiplicity(self) -> None:
        xml = """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>P</SHORT-NAME><ELEMENTS>
        <VARIATION-POINT-PROXY><SHORT-NAME>V</SHORT-NAME><CATEGORY>VALUE</CATEGORY><VALUE-ACCESS>1</VALUE-ACCESS><POST-BUILD-VALUE-ACCESS>2</POST-BUILD-VALUE-ACCESS></VARIATION-POINT-PROXY>
        </ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""
        context = self.context("constr_1253", "/P/V", {"category": "VALUE", "allowed_multiplicities": {"VALUE-ACCESS": {"min": 1, "max": 1}}})
        result = self.validate(xml, rule("constr_1253", "manifest_variation_proxy_table", ["VARIATION-POINT-PROXY"]), context)
        self.assertEqual("FAIL", result["decision"])
        self.assertEqual("POST-BUILD-VALUE-ACCESS", result["findings"][0]["evidence"]["attribute"])


if __name__ == "__main__":
    unittest.main()
