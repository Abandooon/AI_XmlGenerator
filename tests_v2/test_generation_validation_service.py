from __future__ import annotations

import json
import unittest
from pathlib import Path

from src.llm_generation.config import ValidationConfig
from src.validation.v2.service import GeneratedArxmlValidationService


class GeneratedValidationServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        root = Path(__file__).resolve().parents[1]
        cls.service = GeneratedArxmlValidationService(
            plan_path=root / "src/generate_formal_constraints/v2/validation_plan.json",
            xsd_path=None,
            reference_scope="partial",
        )

    def test_bundle_is_validated_and_temp_paths_are_replaced(self) -> None:
        xml = """<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>Components</SHORT-NAME><ELEMENTS>
        <APPLICATION-SW-COMPONENT-TYPE><SHORT-NAME>A</SHORT-NAME><PORTS>
        <P-PORT-PROTOTYPE><SHORT-NAME>P</SHORT-NAME><VARIATION-POINT>
        <POST-BUILD-VARIANT-CONDITIONS/></VARIATION-POINT></P-PORT-PROTOTYPE>
        </PORTS></APPLICATION-SW-COMPONENT-TYPE></ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>"""
        report = self.service.validate_bundle({"components": {"A": xml}, "interfaces": {}})
        self.assertEqual("FAIL", report["decision"])
        self.assertEqual(["components/A.arxml"], report["inputs"])
        self.assertTrue(any(
            "TPS_SWCT_01447" in finding["constraint_ids"]
            for finding in report["findings"]
        ))
        self.assertEqual(554, len(report["rules"]))
        self.assertEqual(len(report["findings"]), report["repair"]["action_count"])
        self.assertTrue(all(item["location"]["file"] == "components/A.arxml" for item in report["findings"]))
        self.assertTrue(all(item["location"]["xml_path"] for item in report["findings"]))
        self.assertTrue(all(action["instruction"] for action in report["repair"]["actions"]))
        self.assertIn("Do not stop after the first edit", report["repair"]["llm_prompt"])
        self.assertIn("components/A.arxml", report["repair"]["by_file"])

    def test_configured_service_is_validator_hash_pinned(self) -> None:
        root = Path(__file__).resolve().parents[1]
        manifest = json.loads(
            (root / "src/validation/v2/validator_manifest.json").read_text(encoding="utf-8")
        )
        config = type("Config", (), {"validation": ValidationConfig()})()
        service = GeneratedArxmlValidationService.from_config(config)
        self.assertEqual(manifest["validator_sha256"], service.validator_sha256)

    def test_runtime_defaults_to_fully_compiled_plan_and_fail_closed_scope(self) -> None:
        config = ValidationConfig()
        self.assertTrue(config.plan_path.endswith("validation_plan.json"))
        self.assertEqual("partial", config.reference_scope)

    def test_service_context_preserves_exact_target_parameters(self) -> None:
        dataset = "a" * 64
        root = Path(__file__).resolve().parents[1]
        service = GeneratedArxmlValidationService(
            plan_path=root / "src/generate_formal_constraints/v2/validation_plan.json",
            xsd_path=None,
            reference_scope="complete",
            dataset_sha256=dataset,
        )
        context = service.build_validation_context(
            {"generation": {"dataset_sha256": dataset, "constraint_ids": ["constr_1160"], "result_count": 1}},
            declared_constraint_ids=["constr_1160"],
            declared_targets={"constr_1160": ["/P/D"]},
            declared_parameters={"constr_1160": {"/P/D": {"expected_variant_value_count": 2}}},
        )
        self.assertEqual(
            2,
            context["declared_parameters"]["constr_1160"]["/P/D"]["expected_variant_value_count"],
        )


if __name__ == "__main__":
    unittest.main()
