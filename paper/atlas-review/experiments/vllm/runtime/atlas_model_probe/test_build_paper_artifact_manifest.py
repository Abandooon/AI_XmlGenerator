from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import yaml

from build_paper_artifact_manifest import build_manifest, verify_heldout_review


class PaperArtifactManifestTests(unittest.TestCase):
    @staticmethod
    def review(reviewer: str, *, overall: str = "PASS", findings: list[dict] | None = None) -> dict:
        root = Path(r"E:\54239\Documents\atlas_autosar_heldout_v3")
        source = root / "heldout_cases.yaml"
        document = yaml.safe_load(source.read_text(encoding="utf-8"))
        return {
            "schema_version": "atlas.autosar.heldout.review.v3",
            "reviewer": reviewer,
            "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "overall_decision": overall,
            "methodology": {
                "factorial_balance": "PASS",
                "estimand_alignment": "PASS",
                "reporting_and_independence": "PASS",
            },
            "cases": [
                {
                    "case_id": case["case_id"],
                    "terminology": "PASS",
                    "count_consistency": "PASS",
                    "xsd_realizability": "PASS",
                    "scope_consistency": "PASS",
                    "structural_role_consistency": "PASS",
                    "decision": "PASS",
                }
                for case in document["cases"]
            ],
            "findings": findings or [],
        }

    def test_missing_heldout_admission_record_blocks_manifest_build(self):
        with tempfile.TemporaryDirectory() as raw:
            missing = Path(raw) / "claude_review.json"
            with self.assertRaisesRegex(
                RuntimeError, "held-out admission review is missing"
            ):
                verify_heldout_review(missing, expected_reviewer="claude")

    def test_v3_exact_pass_review_is_accepted_by_the_hard_gate(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "claude_review.json"
            path.write_text(json.dumps(self.review("claude")), encoding="utf-8")
            result = verify_heldout_review(path, expected_reviewer="claude")
        self.assertEqual("PASS", result["review_decision"])
        self.assertEqual(
            "78dc6d65672d896af3c19b50a5efbf5ca18d8237de9f32f2b7234cd6ff226945",
            result["source_sha256"],
        )

    def test_verified_but_negative_v3_review_is_not_admitted(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "claude_review.json"
            path.write_text(
                json.dumps(
                    self.review(
                        "claude",
                        overall="CHANGES_REQUIRED",
                        findings=[
                            {"severity": "P1", "case_id": None, "message": "blocker"}
                        ],
                    )
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(RuntimeError, "not an exact PASS"):
                verify_heldout_review(path, expected_reviewer="claude")

    def test_manifest_is_deterministic_and_covers_frozen_inputs(self):
        first = build_manifest()
        second = build_manifest()
        self.assertEqual(first, second)
        self.assertEqual(64, len(first["manifest_sha256"]))
        self.assertEqual(20, first["requirement_set"]["case_count"])
        self.assertEqual(60, first["requirement_set"]["run_count_per_model"])
        self.assertEqual(
            "LOCAL_CHAIN_ACCEPTED_FAIL_CLOSED",
            first["local_acceptance"]["decision"],
        )
        self.assertEqual(
            "PASS", first["local_acceptance"]["artifact_profile"]["decision"]
        )
        self.assertEqual(
            "PASS", first["all_requirements_offline_precheck"]["decision"]
        )
        self.assertEqual(
            85,
            first["all_requirements_offline_precheck"]["coverage"][
                "xsd_pass_count"
            ],
        )
        self.assertEqual(
            100,
            first["all_requirements_offline_precheck"]["coverage"][
                "controlled_mutation_detection_count"
            ],
        )
        self.assertGreaterEqual(first["local_acceptance"]["test_count"], 247)
        self.assertEqual(
            "atlas.autosar.paper_artifact_freeze.v3", first["schema_version"]
        )
        self.assertIn(
            "src/llm_generation/knowledge/v2/retrieval_cards.jsonl",
            first["runtime_assets"],
        )
        self.assertFalse(
            first["runtime_configuration"]["credential_fields_included"]
        )
        self.assertFalse(first["runtime_environment"]["credentials_included"])
        self.assertEqual(64, len(first["runtime_environment"]["environment_sha256"]))
        self.assertIn("openai", first["runtime_environment"]["packages"])
        self.assertIn("psutil", first["runtime_environment"]["packages"])
        frontend = first["unified_frontend"]
        self.assertFalse(frontend["formal_v16_result_source"])
        self.assertFalse(frontend["provider_calls_enabled"])
        self.assertEqual("PASS", frontend["local_acceptance_gate"]["decision"])
        self.assertEqual(
            0, frontend["local_acceptance_gate"]["external_model_api_calls"]
        )
        self.assertGreaterEqual(len(frontend["files"]), 31)
        self.assertIn("dist/BUILD_MANIFEST.json", frontend["files"])
        self.assertFalse(
            first["execution_boundary"]["v17_paid_experiment_started"]
        )
        self.assertFalse(
            first["execution_boundary"]["v17_paid_experiment_complete"]
        )
        self.assertEqual(0, first["execution_boundary"]["paid_provider_api_calls_in_this_build"])
        self.assertFalse(
            first["execution_boundary"]["v15_result_admitted_to_current_tables"]
        )
        self.assertFalse(
            first["execution_boundary"]["paper_result_artifacts_included"]
        )
        self.assertEqual(
            "immutable_archive_and_regression_provenance_only",
            first["execution_boundary"]["v15_role"],
        )
        heldout = first["prospective_internally_authored_heldout"]
        self.assertEqual(12, heldout["case_count"])
        self.assertEqual(36, heldout["run_count"])
        self.assertEqual("case", heldout["unit_of_analysis"])
        self.assertEqual(
            {"REPLICATION": 6, "EXTENSION": 6},
            heldout["structural_role_case_counts"],
        )
        self.assertEqual(
            {f"{tier}:{role}": 2 for tier in ("minimal", "standard", "full") for role in ("REPLICATION", "EXTENSION")},
            heldout["tier_by_structural_role_case_counts"],
        )
        self.assertFalse(heldout["external_benchmark"])
        self.assertEqual(
            "atlas.autosar.heldout.review_package.v3",
            heldout["package_schema_version"],
        )
        self.assertEqual(
            "78dc6d65672d896af3c19b50a5efbf5ca18d8237de9f32f2b7234cd6ff226945",
            heldout["source_sha256"],
        )
        self.assertEqual(64, len(heldout["v15_structure_inventory_sha256"]))
        self.assertEqual(
            64, len(heldout["v15_structure_inventory_content_sha256"])
        )
        registration = first["experiment_contract"]["provider_registration"]
        self.assertEqual(
            "gpt-5.6-luna", registration["requested_model"]
        )
        policy = first["replacement_policy"]
        self.assertEqual("atlas.v17.replacement_policy.v2", policy["schema_version"])
        self.assertFalse(policy["provider_no_execution_guarantee_frozen"])
        self.assertEqual(
            ["DEFINITELY_NOT_DISPATCHED"],
            policy["currently_operational_eligibility_states"],
        )
        self.assertEqual(180.0, registration["request_timeout_seconds"])
        self.assertEqual(1, registration["max_attempts_per_call"])
        self.assertEqual(
            "direct_no_environment_proxy",
            registration["transport_route_policy"],
        )
        self.assertFalse(first["experiment_contract"]["stream_responses"])


if __name__ == "__main__":
    unittest.main()
