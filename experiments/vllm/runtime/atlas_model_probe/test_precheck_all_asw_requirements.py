from __future__ import annotations

import json
import unittest

from precheck_all_asw_requirements import (
    ROOT,
    canonical_sha256,
    project_instance_to_schema,
    strict_schema_violations,
)


class AllRequirementsOfflinePrecheckTests(unittest.TestCase):
    def test_frozen_manifest_covers_every_case_and_xsd_document(self):
        path = ROOT / "CONTROLLED_REFERENCE_BASELINES_V16_MANIFEST.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        unsigned = {
            key: item
            for key, item in value.items()
            if key not in {"content_sha256", "created_at_utc"}
        }
        self.assertEqual(canonical_sha256(unsigned), value["content_sha256"])
        self.assertEqual("PASS", value["decision"])
        self.assertEqual(20, value["coverage"]["case_count"])
        self.assertEqual(85, value["coverage"]["xsd_pass_count"])
        self.assertEqual(
            100, value["coverage"]["controlled_mutation_injection_count"]
        )
        self.assertEqual(
            100, value["coverage"]["controlled_mutation_detection_count"]
        )
        self.assertEqual(
            20, value["coverage"]["typed_repair_context_case_count"]
        )
        self.assertEqual(
            85, value["coverage"]["typed_repair_context_target_count"]
        )
        self.assertEqual(100, value["coverage"]["typed_mutation_injection_count"])
        self.assertEqual(
            85, value["coverage"]["controlled_core_fixed_operator_count"]
        )
        self.assertEqual(
            15, value["coverage"]["controlled_substitution_count"]
        )
        self.assertEqual(
            20, value["coverage"]["deterministic_reference_baseline_count"]
        )
        self.assertEqual(20, value["reference_baselines"]["count"])
        self.assertTrue(value["reference_baselines"]["materialized"])
        design = value["controlled_repair_design"]
        self.assertEqual(100, design["design_cell_count"])
        self.assertEqual(100, design["scheduled_task_count"])
        self.assertEqual(85, design["core_fixed_operator_task_count"])
        self.assertEqual(15, design["substitution_task_count"])
        self.assertTrue(
            all(
                record["typed_repair_context"]["round_trip"] == "PASS"
                for record in value["records"]
            )
        )
        injection_modes = [
            result["injection_mode"]
            for record in value["records"]
            for result in record["controlled_mutation_detection"].values()
        ]
        self.assertEqual(80, injection_modes.count("structured_payload_then_renderer"))
        self.assertEqual(20, injection_modes.count("order_only_xml_identity"))
        self.assertTrue(
            all(
                record["interface_provider_boundary"]["reversible"] is True
                and record["interface_provider_boundary"][
                    "normalization_status"
                ]
                == "NOT_APPLICABLE"
                for record in value["records"]
            )
        )
        self.assertEqual(0, value["execution_boundary"]["external_model_api_calls"])
        self.assertEqual(20, len(value["records"]))

        records = {record["case_id"]: record for record in value["records"]}
        substituted = [
            task
            for task in design["tasks"]
            if task["analysis_layer"] == "substitution"
        ]
        self.assertEqual(15, len(substituted))
        observed_operators = set()
        for task in substituted:
            with self.subTest(task_id=task["task_id"]):
                detection = records[task["case_id"]][
                    "controlled_mutation_detection"
                ][task["effective_mutation"]]
                self.assertEqual(task["task_id"], detection["task_id"])
                self.assertEqual("substitution", detection["analysis_layer"])
                self.assertEqual("NOT_APPLICABLE", detection["applicability"])
                self.assertEqual("DETECTED", detection["decision"])
                self.assertEqual(
                    "structured_payload_then_renderer", detection["injection_mode"]
                )
                self.assertGreater(
                    int(detection["xsd_failure_count"])
                    + int(detection["reference_failure_count"])
                    + int(detection["selection_obligation_decision"] == "FAIL"),
                    0,
                )
                observed_operators.add(task["effective_mutation"])
        self.assertEqual(
            {
                "empty_provided_interface_ref",
                "wrong_provided_interface_ref",
                "missing_provided_port",
                "missing_component_short_name",
                "missing_required_interface_ref",
            },
            observed_operators,
        )

    def test_provider_projection_removes_only_absent_schema_properties(self):
        schema = {
            "type": "object",
            "additionalProperties": False,
            "properties": {"keep": {"type": "string"}},
            "required": ["keep"],
        }
        self.assertEqual(
            {"keep": "x"},
            project_instance_to_schema({"keep": "x", "materialize": "y"}, schema),
        )
        self.assertEqual([], strict_schema_violations(schema))


if __name__ == "__main__":
    unittest.main()
