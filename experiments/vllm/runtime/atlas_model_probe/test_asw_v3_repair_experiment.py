from __future__ import annotations

import json
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from run_asw_v3_repair_experiment import build_schedule, canonical_sha256
from repair_asw_v3_run import (
    _load_frozen_typed_repair_context,
    _mutate_typed_targets,
    automation_boundary_reasons,
    bundle_sha256,
    classify_attempt_outcome,
    sha256_file,
)
from summarize_asw_v3_repair import summarize
from controlled_repair_v16 import build_mutation_schedule, load_requirements


class AswV3RepairExperimentTests(unittest.TestCase):
    def controlled_reference(self, directory: Path) -> tuple[Path, dict]:
        design = build_mutation_schedule(load_requirements())
        records = []
        for case_id in sorted({item["case_id"] for item in design["tasks"]}):
            records.append(
                {
                    "case_id": case_id,
                    "deterministic_reference_baseline": {
                        "root": str(directory / "reference" / case_id),
                        "bundle_sha256": "4" * 64,
                        "run_summary_sha256": "5" * 64,
                        "typed_repair_context_content_sha256": "2" * 64,
                        "independent_decision": "PASS",
                    },
                }
            )
        manifest = {
            "schema_version": "atlas.asw_v3.all_requirements_offline_precheck.v2",
            "decision": "PASS",
            "content_sha256": "6" * 64,
            "controlled_repair_design": design,
            "records": records,
            "reference_baselines": {"materialized": True, "count": 20},
        }
        path = directory / "controlled_reference.json"
        path.write_text("{}", encoding="utf-8")
        return path, manifest

    @staticmethod
    def baseline_audit(_record, *, controlled_mutations=()):
        return {
            "baseline_run_summary_sha256": "1" * 64,
            "typed_repair_context_content_sha256": "2" * 64,
            "typed_repair_context_file_sha256": "3" * 64,
            "controlled_mutation_targets_verified": list(controlled_mutations),
        }

    def generation_results(self, directory: Path) -> Path:
        records = []
        for model, standard_pass in (("luna", True), ("terra", False)):
            records.extend(
                [
                    {
                        "run_id": f"{model}__std",
                        "model": model,
                        "case_id": "ASW-STD-07",
                        "repetition": 1,
                        "seed": 104729,
                        "run_root": str(directory / model / "std"),
                        "attempt_number": 1,
                        "status": "COMPLETE",
                        "independent_decision": "PASS" if standard_pass else "FAIL",
                    },
                    {
                        "run_id": f"{model}__full",
                        "model": model,
                        "case_id": "ASW-FULL-01",
                        "repetition": 1 if model == "luna" else 2,
                        "seed": 104729 if model == "luna" else 130363,
                        "run_root": str(directory / model / "full"),
                        "attempt_number": 1,
                        "status": "COMPLETE",
                        "independent_decision": "PASS" if model == "luna" else "FAIL",
                    },
                ]
            )
        generation_schedule = {
            "pipeline_run_count": len(records),
            "content_sha256": "b" * 64,
            "freeze_manifest_sha256": "c" * 64,
            "experiment_contract_sha256": "d" * 64,
            "neo4j_context_sha256": "e" * 64,
            "runs": [
                {
                    "run_id": item["run_id"],
                    "model": item["model"],
                    "case_id": item["case_id"],
                    "repetition": item["repetition"],
                    "seed": item["seed"],
                }
                for item in records
            ],
        }
        value = {
            "schedule": generation_schedule,
            "records": records,
        }
        value["content_sha256"] = canonical_sha256(value)
        path = directory / "generation_results.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def test_schedule_separates_natural_and_controlled_cohorts(self):
        with tempfile.TemporaryDirectory() as raw:
            results_path = self.generation_results(Path(raw))
            reference_path, reference = self.controlled_reference(Path(raw))
            results = json.loads(results_path.read_text(encoding="utf-8"))
            with patch(
                "run_asw_v3_repair_experiment.verify_experiment_results",
                return_value=results,
            ), patch(
                "run_asw_v3_repair_experiment.verify_schedule",
                return_value=results["schedule"],
            ), patch(
                "run_asw_v3_repair_experiment._run_complete", return_value=True
            ), patch(
                "run_asw_v3_repair_experiment.verify_repair_baseline",
                side_effect=self.baseline_audit,
            ), patch(
                "run_asw_v3_repair_experiment.verify_controlled_reference_manifest",
                return_value=reference,
            ):
                schedule = build_schedule(results_path, reference_path)
        cohorts = [item["cohort"] for item in schedule["runs"]]
        self.assertEqual(2, cohorts.count("natural_failure"))
        self.assertEqual(100, cohorts.count("controlled_mutation"))
        self.assertEqual(0, schedule["ineligible_count"])
        self.assertEqual(20, schedule["controlled_baseline_count"])
        self.assertEqual(85, schedule["controlled_core_fixed_operator_task_count"])
        self.assertEqual(15, schedule["controlled_substitution_task_count"])
        self.assertEqual(len(schedule["runs"]), len({item["run_id"] for item in schedule["runs"]}))

    def test_repair_summary_keeps_fault_injection_separate(self):
        results = {
            "content_sha256": "b" * 64,
            "schedule": {
                "controlled_design_cell_count": 1,
                "controlled_core_fixed_operator_task_count": 1,
                "controlled_substitution_task_count": 0,
                "core_operator_denominators": {"wrong_init_value": 1},
                "controlled_substitute_mutations": [],
                "runs": [
                    {
                        "cohort": "controlled_mutation",
                        "analysis_layer": "core_fixed_operator",
                        "base_operator": "wrong_init_value",
                        "mutation": "wrong_init_value",
                    }
                ],
            },
            "records": [
                {
                    "status": "COMPLETE",
                    "cohort": "natural_failure",
                    "initial_independent_decision": "FAIL",
                    "independent_decision": "PASS",
                    "strict_restoration": True,
                    "exact_original_recovery": False,
                    "repair_triggered": True,
                    "repair_accepted_rounds": 1,
                },
                {
                    "status": "COMPLETE",
                    "cohort": "controlled_mutation",
                    "mutation": "wrong_init_value",
                    "base_operator": "wrong_init_value",
                    "analysis_layer": "core_fixed_operator",
                    "initial_independent_decision": "FAIL",
                    "independent_decision": "FAIL",
                    "strict_restoration": False,
                    "exact_original_recovery": False,
                    "repair_triggered": True,
                    "repair_accepted_rounds": 0,
                },
            ],
        }
        summary = summarize(results)
        self.assertEqual(1.0, summary["cohorts"]["natural_failure"]["success_rate"])
        self.assertEqual(
            0.0,
            summary["controlled_core_fixed_operators"]["wrong_init_value"][
                "repair_rate"
            ],
        )
        self.assertIsNone(
            summary["controlled_repair_accounting"]["combined_repair_rate"]
        )
        self.assertEqual(64, len(summary["content_sha256"]))

    def test_terminal_generation_failure_is_counted_but_not_repaired(self):
        with tempfile.TemporaryDirectory() as raw:
            results_path = self.generation_results(Path(raw))
            reference_path, reference = self.controlled_reference(Path(raw))
            results = json.loads(results_path.read_text(encoding="utf-8"))
            failed = results["records"][0]
            failed["status"] = "TERMINAL_FAILURE"
            failed["independent_decision"] = None
            results["content_sha256"] = canonical_sha256(
                {key: value for key, value in results.items() if key != "content_sha256"}
            )
            results_path.write_text(json.dumps(results), encoding="utf-8")
            with patch(
                "run_asw_v3_repair_experiment.verify_experiment_results",
                return_value=results,
            ), patch(
                "run_asw_v3_repair_experiment.verify_schedule",
                return_value=results["schedule"],
            ), patch(
                "run_asw_v3_repair_experiment._run_complete", return_value=True
            ), patch(
                "run_asw_v3_repair_experiment.verify_repair_baseline",
                side_effect=self.baseline_audit,
            ), patch(
                "run_asw_v3_repair_experiment.verify_controlled_reference_manifest",
                return_value=reference,
            ):
                schedule = build_schedule(results_path, reference_path)
        self.assertEqual(1, schedule["source_terminal_generation_failure_count"])
        self.assertTrue(
            any(
                "repairable ARXML" in item["reason"]
                for item in schedule["ineligible"]
            )
        )
        self.assertFalse(
            any(
                item["baseline_run_id"] == failed["run_id"]
                for item in schedule["runs"]
            )
        )

    def test_zero_natural_failures_are_not_reported_as_perfect_repair(self):
        results = {
            "content_sha256": "b" * 64,
            "schedule": {
                "controlled_mutations": [],
                "source_generation_run_count": 60,
                "natural_failure_count": 0,
            },
            "records": [],
        }
        summary = summarize(results)
        natural = summary["cohorts"]["natural_failure"]
        self.assertIsNone(natural["success_rate"])
        self.assertEqual(
            "NOT_ESTIMABLE_NO_OBSERVED_FAILURES", natural["estimability"]
        )
        self.assertEqual(0.0, summary["natural_failure_incidence"]["rate"])

    def test_attempt_outcomes_are_mutually_exclusive(self):
        self.assertEqual(
            "not_attempted",
            classify_attempt_outcome({"attempted_rounds": 0}, strict_restoration=False),
        )
        self.assertEqual(
            "resolved",
            classify_attempt_outcome(
                {"attempted_rounds": 1, "stop_reason": "no_repairable_findings"},
                strict_restoration=True,
            ),
        )
        self.assertEqual(
            "rejected_regression",
            classify_attempt_outcome(
                {"attempted_rounds": 1, "stop_reason": "regression"},
                strict_restoration=False,
            ),
        )
        self.assertEqual(
            "rejected_no_improvement",
            classify_attempt_outcome(
                {"attempted_rounds": 1, "stop_reason": "no_finding_resolved"},
                strict_restoration=False,
            ),
        )
        self.assertEqual(
            "rejected_malformed",
            classify_attempt_outcome(
                {"attempted_rounds": 1, "stop_reason": "repair_error"},
                strict_restoration=False,
            ),
        )

    def test_automation_boundary_is_orthogonal_and_deduplicated(self):
        trace = [
            {
                "attempt_outcome": "proposed",
                "findings": [
                    {"automation_boundary_reason": "not_localizable"},
                    {"automation_boundary_reason": "none"},
                    {"automation_boundary_reason": "not_localizable"},
                ],
            }
        ]
        self.assertEqual(["not_localizable"], automation_boundary_reasons(trace))
        self.assertEqual(["none"], automation_boundary_reasons([]))

    def test_frozen_typed_context_must_be_present_in_baseline_hashes(self):
        bundle = {
            "components": {"C": "<AUTOSAR><C/></AUTOSAR>"},
            "interfaces": {},
        }
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            directory = root / "atlas_output/typed_repair_context"
            directory.mkdir(parents=True)
            path = directory / "context.json"
            context = {
                "schema_version": "atlas.typed_repair_context.v1",
                "bundle_sha256": bundle_sha256(bundle),
                "xsd_sha256": "b" * 64,
                "serialization_manifest_sha256": "c" * 64,
                "targets": [{"kind": "components", "name": "C"}],
            }
            context["content_sha256"] = hashlib.sha256(
                json.dumps(
                    context,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest()
            path.write_text(json.dumps(context), encoding="utf-8")
            relative = path.relative_to(root).as_posix()
            summary = {"artifact_hashes": {relative: sha256_file(path)}}
            restored_path, restored = _load_frozen_typed_repair_context(
                root, summary, bundle
            )
            self.assertEqual(path, restored_path)
            self.assertEqual(context, restored)

            summary["artifact_hashes"][relative] = "0" * 64
            with self.assertRaisesRegex(ValueError, "hash differs"):
                _load_frozen_typed_repair_context(root, summary, bundle)

    def test_controlled_value_mutations_are_applied_before_xsd_rendering(self):
        import sys
        from run_phase12_case import ATLAS_ROOT

        if str(ATLAS_ROOT) not in sys.path:
            sys.path.insert(0, str(ATLAS_ROOT))
        from tests_v2.test_typed_patch_repair import (
            COMPONENT_NAME,
            PINNED_INIT_VALUE_DESIGN,
            RepairFixture,
        )
        from src.llm_generation.core.typed_repair import render_documents

        RepairFixture.setUpClass()
        fixture = RepairFixture(methodName="runTest")
        target = fixture.target(
            declared_value_design=PINNED_INIT_VALUE_DESIGN
        )
        targets = fixture.targets(target)
        baseline = render_documents(targets, serializer=fixture.serializer)
        for mutation in (
            "empty_init_value",
            "wrong_init_value",
            "missing_event_behavior_path",
        ):
            mutated_targets = _mutate_typed_targets(targets, mutation)
            mutated = render_documents(
                mutated_targets, serializer=fixture.serializer
            )
            self.assertNotEqual(
                baseline["components"][COMPONENT_NAME],
                mutated["components"][COMPONENT_NAME],
                mutation,
            )


if __name__ == "__main__":
    unittest.main()
