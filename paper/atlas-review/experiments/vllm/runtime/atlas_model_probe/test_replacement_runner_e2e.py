"""Zero-network execution gate for the replacement orchestrator and child."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from run_asw_v3_experiment import canonical_sha256, run_experiment


class ReplacementRunnerE2ETests(unittest.TestCase):
    def test_schedule_consuming_runner_executes_replacement_as_its_own_layer(self):
        source = {
            "run_id": "gpt-5.6-luna__ASW-MIN-01__R1__repair-off",
            "cohort": "primary",
            "case_id": "ASW-MIN-01",
            "tier": "minimal",
            "repetition": 1,
            "seed": 104729,
            "model": "gpt-5.6-luna",
            "prompt_sha256": "a" * 64,
            "case_sha256": "d287dc5f057f449be3d35f3f615f9cb1aec1debc24f305555f23b5812b564be6",
            "repair_mode": "off",
            "requirement_source_canonical_sha256": (
                "dc4847e125c04b82b3a26154f678d45619f8f7ae8a599aa4865386908ec79e83"
            ),
        }
        row = {
            **{key: value for key, value in source.items() if key != "cohort"},
            "run_id": source["run_id"] + "__replacement-1",
            "cohort": "replacement",
            "source_cohort": "primary",
            "replaces_run_id": source["run_id"],
            "replacement_index": 1,
            "original_completion_kind": "INFRASTRUCTURE_TRANSPORT_FAILURE",
            "original_delivery_state": "DEFINITELY_NOT_DISPATCHED",
            "original_failure_fingerprint": "f" * 64,
            "eligibility_reason": "scripted pre-dispatch loss",
        }
        unsigned = {
            "schema_version": "atlas.v17.replacement_schedule.v2",
            "cohort": "replacement",
            "analysis_layer": "replacement_sensitivity",
            "not_admissible_to_original_denominator": True,
            "freeze_manifest_path": "offline-gate-freeze.json",
            "freeze_manifest_file_sha256": "1" * 64,
            "freeze_manifest_sha256": "2" * 64,
            "experiment_contract_sha256": "3" * 64,
            "neo4j_context_sha256": "4" * 64,
            "models": ["gpt-5.6-luna"],
            "repair_mode": "off",
            "max_replacements_per_slot": 1,
            "pipeline_run_count": 1,
            "runs": [row],
        }
        schedule = {**unsigned, "content_sha256": canonical_sha256(unsigned)}
        freeze = {
            "manifest_sha256": schedule["freeze_manifest_sha256"],
            "experiment_contract_sha256": schedule["experiment_contract_sha256"],
            "neo4j_context_sha256": schedule["neo4j_context_sha256"],
        }

        with tempfile.TemporaryDirectory() as raw, patch(
            "run_asw_v3_experiment.verify_schedule", return_value=schedule
        ), patch(
            "run_asw_v3_experiment.verify_freeze_manifest", return_value=freeze
        ):
            try:
                result = run_experiment(
                    schedule, Path(raw), timeout_seconds=120, offline_scripted=True
                )
            except Exception as error:
                diagnostics = "\n".join(
                    path.read_text(encoding="utf-8", errors="replace")
                    for path in Path(raw).rglob("pipeline.stderr.log")
                )
                self.fail(f"{error}\n{diagnostics}")
            self.assertTrue(result["experiment_complete"])
            self.assertEqual(0, result["external_model_api_calls"])
            self.assertEqual(1, result["record_count"])
            record = result["records"][0]
            self.assertEqual("replacement", record["cohort"])
            self.assertEqual("primary", record["source_cohort"])
            self.assertEqual(source["run_id"], record["replaces_run_id"])
            self.assertEqual("PASS", record["independent_decision"])
            summary = json.loads(
                (Path(record["run_root"]) / "run_summary.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(
                [0, 0], summary["provider_runtime_gate"]["sdk_implicit_max_retries"]
            )
            self.assertTrue(
                summary["provider_runtime_gate"]["all_provider_calls_have_identity"]
            )
            audit_path = Path(record["run_root"]) / "provider_calls.jsonl"
            audit = [json.loads(line) for line in audit_path.read_text(
                encoding="utf-8"
            ).splitlines()]
            self.assertEqual(
                ["round1", "round2.interface", "round2.component"],
                [item["pipeline_phase"] for item in audit],
            )
            self.assertEqual([1, 2, 3], [item["logical_call_index"] for item in audit])
            self.assertTrue(all(item["actual_paid_provider_call"] is False for item in audit))


if __name__ == "__main__":
    unittest.main()
