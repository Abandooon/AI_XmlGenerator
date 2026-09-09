from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from lxml import etree

from evaluate_asw_v3_run import evaluate
from repair_asw_v3_run import apply_mutation


ROOT = Path(r"E:\git projects\AI_XmlGenerator")
COMPONENT = ROOT / "tests_v2/fixtures/asw_golden_component.arxml"
INTERFACES = ROOT / "tests_v2/fixtures/asw_golden_interfaces.arxml"


class AswV3IndependentEvaluatorTests(unittest.TestCase):
    @staticmethod
    def validation_file(directory: Path) -> Path:
        path = directory / "validation.json"
        path.write_text(
            json.dumps(
                {
                    "decision": "INCOMPLETE",
                    "validator_sha256": "a" * 64,
                    "validation_context": {
                        "manifest": {"manifest_sha256": "b" * 64}
                    },
                    "selection_obligations": {"decision": "PASS"},
                    "artifact_profile": {
                        "profile_id": "autosar_component_arxml_only_v1",
                        "decision": "PASS",
                    },
                }
            ),
            encoding="utf-8",
        )
        return path

    def evaluate_component(self, xml_text: str, *, include_interfaces: bool = True):
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            component = directory / "component.arxml"
            component.write_text(xml_text, encoding="utf-8")
            validation = self.validation_file(directory)
            return evaluate(
                case_id="ASW-STD-07",
                component_path=component,
                interface_paths=[INTERFACES] if include_interfaces else [],
                validation_path=validation,
            )

    def test_golden_fixture_is_promotable_even_when_full_corpus_is_incomplete(self):
        report = self.evaluate_component(COMPONENT.read_text(encoding="utf-8"))
        self.assertEqual("PASS", report["decision"])
        self.assertTrue(report["promotable"])
        self.assertEqual("INCOMPLETE", report["full_corpus_decision"])
        self.assertEqual(0, report["structural_failure_count"])
        self.assertEqual(0, report["local_reference_failure_count"])

    def test_empty_or_wrong_init_value_fails_parsed_requirement(self):
        for mutation in ("empty", "wrong"):
            with self.subTest(mutation=mutation):
                document = etree.fromstring(COMPONENT.read_bytes())
                if mutation == "empty":
                    document.xpath("//*[local-name()='INIT-VALUE']")[0].clear()
                else:
                    document.xpath("//*[local-name()='VALUE']")[0].text = "1"
                report = self.evaluate_component(
                    etree.tostring(document, encoding="unicode")
                )
                self.assertEqual("FAIL", report["decision"])
                failed_codes = {
                    item["code"]
                    for item in report["structural_obligations"]
                    if item["status"] == "FAIL"
                }
                self.assertIn("unconnected_numeric_init_value", failed_codes)

    def test_missing_interface_context_is_not_a_model_structure_pass(self):
        report = self.evaluate_component(
            COMPONENT.read_text(encoding="utf-8"), include_interfaces=False
        )
        self.assertEqual("FAIL", report["decision"])
        self.assertGreater(report["local_reference_failure_count"], 0)

    def test_nonexistent_runnable_path_fails_event_and_reference_obligations(self):
        document = etree.fromstring(COMPONENT.read_bytes())
        document.xpath("//*[local-name()='START-ON-EVENT-REF']")[0].text = (
            "/Components/ASW_Com_Std_TimeoutExplicit/RE_Missing"
        )
        report = self.evaluate_component(etree.tostring(document, encoding="unicode"))
        self.assertEqual("FAIL", report["decision"])
        self.assertGreater(report["local_reference_failure_count"], 0)
        failed_codes = {
            item["code"]
            for item in report["structural_obligations"]
            if item["status"] == "FAIL"
        }
        self.assertIn("runnable_timing_event", failed_codes)

    def test_repair_experiment_mutations_are_deterministic_and_well_formed(self):
        source_bundle = {
            "components": {
                "ASW_Com_Std_TimeoutExplicit": COMPONENT.read_text(encoding="utf-8")
            },
            "interfaces": {},
        }
        for mutation in (
            "empty_init_value",
            "wrong_init_value",
            "missing_event_behavior_path",
            "missing_required_comspec",
            "wrong_xsd_order",
        ):
            with self.subTest(mutation=mutation):
                first = apply_mutation(source_bundle, mutation)
                second = apply_mutation(source_bundle, mutation)
                self.assertEqual(first, second)
                self.assertNotEqual(source_bundle, first)
                etree.fromstring(
                    first["components"]["ASW_Com_Std_TimeoutExplicit"].encode(
                        "utf-8"
                    )
                )


if __name__ == "__main__":
    unittest.main()
