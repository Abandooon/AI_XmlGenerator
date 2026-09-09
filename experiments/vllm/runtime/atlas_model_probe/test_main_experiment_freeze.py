from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import experiment_freeze
from build_paper_artifact_manifest import build_manifest
from experiment_freeze import (
    ExperimentFreezeError,
    canonical_sha256,
    verify_freeze_manifest,
)
from run_asw_v3_experiment import (
    _classify_failed_attempt,
    _read_provider_call_audit,
    _read_json_object,
    _run_complete,
    _write_completion_manifest,
    run_experiment,
)
from run_asw_v3_experiment import _provider_queue_halt_reason
from experiment_runtime import (
    ChildProcessResult,
    atomic_write_json,
    exclusive_experiment_lock,
    recover_orphaned_child,
    reserve_attempt,
    run_child_process,
)


class MainExperimentFreezeTests(unittest.TestCase):
    def test_built_manifest_verifies_every_frozen_input(self):
        manifest = build_manifest()
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "freeze.json"
            path.write_text(
                json.dumps(manifest, ensure_ascii=False, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            verification = verify_freeze_manifest(path)
        self.assertEqual("PASS", verification["decision"])
        self.assertGreater(verification["verified_file_counts"]["runtime_assets"], 30)

    def test_tampered_manifest_fails_closed(self):
        manifest = build_manifest()
        manifest["requirement_set"]["case_count"] = 19
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "tampered.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(
                ExperimentFreezeError, "canonical hash mismatch"
            ):
                verify_freeze_manifest(path)

    def test_completion_resume_requires_identity_and_all_artifact_hashes(self):
        scheduled = {
            "run_id": "gpt-5.6-luna__ASW-MIN-01-R1__repair-off",
            "model": "gpt-5.6-luna",
            "case_id": "ASW-MIN-01",
            "repetition": 1,
            "seed": 104729,
            "repair_mode": "off",
            "requirement_source_canonical_sha256": "a" * 64,
            "case_sha256": "b" * 64,
        }
        schedule = {
            "freeze_manifest_sha256": "c" * 64,
            "experiment_contract_sha256": "d" * 64,
            "neo4j_context_sha256": "f" * 64,
            "content_sha256": "e" * 64,
        }
        summary = {
            **{key: scheduled[key] for key in (
                "model", "case_id", "repetition", "seed", "repair_mode",
                "requirement_source_canonical_sha256", "case_sha256",
            )},
            "schedule_content_sha256": schedule["content_sha256"],
            "freeze_manifest_sha256": schedule["freeze_manifest_sha256"],
            "experiment_contract_sha256": schedule["experiment_contract_sha256"],
            "neo4j_context_sha256": schedule["neo4j_context_sha256"],
        }
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "run_summary.json").write_text(
                json.dumps(summary), encoding="utf-8"
            )
            (root / "independent_evaluation.json").write_text(
                json.dumps({"case_id": scheduled["case_id"], "decision": "PASS"}),
                encoding="utf-8",
            )
            artifact = root / "component.arxml"
            artifact.write_text("<AUTOSAR/>", encoding="utf-8")
            completion = _write_completion_manifest(root, scheduled, schedule)
            unsigned = {
                key: value for key, value in completion.items()
                if key != "content_sha256"
            }
            self.assertEqual(
                completion["content_sha256"], canonical_sha256(unsigned)
            )
            self.assertTrue(_run_complete(root, scheduled, schedule))
            artifact.write_text("<AUTOSAR><TAMPER/></AUTOSAR>", encoding="utf-8")
            self.assertFalse(_run_complete(root, scheduled, schedule))

    def test_completion_resume_rejects_schedule_identity_change(self):
        scheduled = {
            "run_id": "run",
            "model": "gpt-5.6-sol",
            "case_id": "ASW-MIN-01",
            "repetition": 1,
            "seed": 104729,
            "repair_mode": "off",
            "requirement_source_canonical_sha256": "a" * 64,
            "case_sha256": "b" * 64,
        }
        schedule = {
            "freeze_manifest_sha256": "c" * 64,
            "experiment_contract_sha256": "d" * 64,
            "neo4j_context_sha256": "f" * 64,
            "content_sha256": "e" * 64,
        }
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            summary = {
                **scheduled,
                "schedule_content_sha256": schedule["content_sha256"],
                "freeze_manifest_sha256": schedule["freeze_manifest_sha256"],
                "experiment_contract_sha256": schedule[
                    "experiment_contract_sha256"
                ],
                "neo4j_context_sha256": schedule["neo4j_context_sha256"],
            }
            (root / "run_summary.json").write_text(
                json.dumps(summary), encoding="utf-8"
            )
            (root / "independent_evaluation.json").write_text(
                json.dumps({"case_id": scheduled["case_id"]}), encoding="utf-8"
            )
            _write_completion_manifest(root, scheduled, schedule)
            changed = {**schedule, "content_sha256": "f" * 64}
            self.assertFalse(_run_complete(root, scheduled, changed))

    def test_completion_attempt_identity_is_bound(self):
        scheduled = {
            "run_id": "run",
            "model": "gpt-5.6-luna",
            "case_id": "ASW-MIN-01",
            "repetition": 1,
            "seed": 104729,
            "repair_mode": "off",
            "requirement_source_canonical_sha256": "a" * 64,
            "case_sha256": "b" * 64,
        }
        schedule = {
            "freeze_manifest_sha256": "c" * 64,
            "experiment_contract_sha256": "d" * 64,
            "neo4j_context_sha256": "f" * 64,
            "content_sha256": "e" * 64,
        }
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            summary = {
                **scheduled,
                "schedule_content_sha256": schedule["content_sha256"],
                "freeze_manifest_sha256": schedule["freeze_manifest_sha256"],
                "experiment_contract_sha256": schedule[
                    "experiment_contract_sha256"
                ],
                "neo4j_context_sha256": schedule["neo4j_context_sha256"],
                "attempt_number": 1,
            }
            (root / "run_summary.json").write_text(
                json.dumps(summary), encoding="utf-8"
            )
            (root / "independent_evaluation.json").write_text(
                json.dumps({"case_id": scheduled["case_id"]}), encoding="utf-8"
            )
            _write_completion_manifest(root, scheduled, schedule, 1)
            self.assertTrue(_run_complete(root, scheduled, schedule, 1))
            self.assertFalse(_run_complete(root, scheduled, schedule, 2))

    def test_provider_wide_blockers_halt_queue(self):
        self.assertEqual(
            "PROVIDER_INSUFFICIENT_BALANCE",
            _provider_queue_halt_reason("", "403 insufficient_balance"),
        )
        self.assertEqual(
            "PROVIDER_STRICT_SCHEMA_UNAVAILABLE",
            _provider_queue_halt_reason(
                "",
                "Strict JSON Schema generation failed: response_format is unsupported",
            ),
        )
        self.assertIsNone(
            _provider_queue_halt_reason(
                "", "Strict JSON Schema generation failed: request timed out"
            )
        )
        self.assertIsNone(_provider_queue_halt_reason("case failed XSD", ""))

    def test_failure_classifier_never_retries_a_model_or_selection_failure(self):
        """A model failure must be evidenced by a delivered provider response.

        Without that evidence the failure is unclassified, not attributed to
        the model: an unmatched failure may not fall into the model bucket by
        default, which is how the V16 pilot mislabelled three transport faults.
        """
        with tempfile.TemporaryDirectory() as raw:
            run_root = Path(raw)
            call_id = "call_selection"
            (run_root / "provider_calls.jsonl").write_text(
                json.dumps(
                    {
                        "credentials_included": False,
                        "provider_call_id": call_id,
                        "response_id": "resp_selection",
                        "usage": {
                            "input_tokens": 10,
                            "output_tokens": 5,
                            "total_tokens": 15,
                        },
                    }
                )
                + chr(10),
                encoding="utf-8",
            )
            (run_root / "provider_call_transitions.jsonl").write_text(
                chr(10).join(
                    json.dumps({
                        "credentials_included": False,
                        "provider_call_id": call_id,
                        "pipeline_phase": "round2.component",
                        "logical_call_index": 2,
                        "stage": stage,
                        "dispatch_started": True,
                        "request_acceptance_known": True,
                        "response_headers_received": True,
                        "response_id": "resp_selection",
                    })
                    for stage in (
                        "PRE_DISPATCH", "DISPATCH_STARTED", "RESPONSE_RECEIVED",
                        "LOCAL_AUDIT_PERSISTED",
                    )
                ) + chr(10),
                encoding="utf-8",
            )
            classified = _classify_failed_attempt(
                "", "selection path conflict", {"final_status": "failure"},
                timed_out=False,
                run_root=run_root,
            )
            self.assertEqual(
                "MODEL_OR_SCHEMA_GENERATION_FAILURE",
                classified["completion_kind"],
            )
            self.assertTrue(classified["terminal"])
            self.assertFalse(classified["retryable"])
            self.assertEqual("CONFIRMED_DELIVERED", classified["delivery_state"])
            self.assertFalse(classified["replacement_eligible"])

    def test_a_failure_with_no_delivery_evidence_is_unclassified(self):
        classified = _classify_failed_attempt(
            "", "selection path conflict", {"final_status": "failure"},
            timed_out=False,
        )
        self.assertEqual("UNCLASSIFIED_FAILURE", classified["completion_kind"])
        self.assertNotEqual(
            "MODEL_OR_SCHEMA_GENERATION_FAILURE", classified["completion_kind"]
        )
        self.assertFalse(classified["replacement_eligible"])

    def test_a_transport_timeout_is_not_retried_and_is_not_a_generation_failure(self):
        """A timed-out request may already have been executed.

        The classifier previously called this transient and retryable, which
        re-ran a whole slot whose request the provider may already have served:
        a second paid execution for one scheduled slot.  It is now terminal,
        ambiguous, and outside the model-quality denominator.
        """
        classified = _classify_failed_attempt(
            "",
            "Strict JSON Schema generation failed: request timed out",
            {"final_status": "failure"},
            timed_out=False,
        )
        self.assertEqual(
            "AMBIGUOUS_PROVIDER_DELIVERY", classified["completion_kind"]
        )
        self.assertTrue(classified["terminal"])
        self.assertFalse(classified["retryable"])
        self.assertEqual("UNKNOWN", classified["billing_state"])
        self.assertFalse(classified["replacement_eligible"])
        self.assertIsNone(classified["queue_halt_reason"])

    def test_the_v16_pilot_connection_error_is_no_longer_a_generation_failure(self):
        """The exact text that cost three pilot slots."""
        classified = _classify_failed_attempt(
            "",
            "Round1: Strict JSON Schema generation failed: Connection error.",
            {"final_status": "failure"},
            timed_out=False,
        )
        self.assertEqual(
            "AMBIGUOUS_PROVIDER_DELIVERY", classified["completion_kind"]
        )
        self.assertNotEqual(
            "MODEL_OR_SCHEMA_GENERATION_FAILURE", classified["completion_kind"]
        )
        self.assertEqual("UNKNOWN", classified["billing_state"])
        self.assertFalse(classified["replacement_eligible"])

    def test_partial_json_is_not_treated_as_a_valid_record(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "partial.json"
            path.write_text('{"unfinished":', encoding="utf-8")
            self.assertEqual({}, _read_json_object(path))

    def test_provider_usage_audit_fails_closed_without_required_fields(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "provider_calls.jsonl"
            path.write_text(
                json.dumps(
                    {
                        "credentials_included": False,
                        "usage": {
                            "input_tokens": 10,
                            "output_tokens": 4,
                            "total_tokens": 14,
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            self.assertEqual(1, len(_read_provider_call_audit(path)))
            path.write_text(
                json.dumps({"credentials_included": False, "usage": {}}),
                encoding="utf-8",
            )
            self.assertEqual([], _read_provider_call_audit(path))

    def test_runtime_lock_rejects_a_second_orchestrator(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            with exclusive_experiment_lock(root, schedule_sha256="a" * 64):
                with self.assertRaisesRegex(RuntimeError, "another experiment"):
                    with exclusive_experiment_lock(
                        root, schedule_sha256="a" * 64
                    ):
                        pass

    def test_runtime_lock_retains_and_recovers_a_stale_lock(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / ".atlas-experiment.lock").write_text(
                json.dumps({"pid": 2147483647, "token": "old"}),
                encoding="utf-8",
            )
            with exclusive_experiment_lock(root, schedule_sha256="a" * 64):
                self.assertTrue((root / ".atlas-experiment.lock").is_file())
            stale = list(root.glob(".atlas-experiment.lock.stale.*.json"))
            self.assertEqual(1, len(stale))

    def test_atomic_json_and_attempt_reservation_are_consistent(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            path = root / "state.json"
            atomic_write_json(path, {"value": 1})
            self.assertEqual({"value": 1}, json.loads(path.read_text("utf-8")))
            first_number, first = reserve_attempt(root / "attempts", 2)
            second_number, second = reserve_attempt(root / "attempts", 2)
            self.assertEqual((1, 2), (first_number, second_number))
            self.assertNotEqual(first, second)
            with self.assertRaisesRegex(RuntimeError, "budget exhausted"):
                reserve_attempt(root / "attempts", 2)

    def test_child_timeout_terminates_the_process(self):
        with tempfile.TemporaryDirectory() as raw:
            state_path = Path(raw) / "child_process_state.json"
            result = run_child_process(
                [sys.executable, "-c", "import time; time.sleep(10)"],
                cwd=Path.cwd(),
                timeout_seconds=1,
                state_path=state_path,
            )
            state = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertTrue(result.timed_out)
        self.assertIsNotNone(result.termination)
        self.assertEqual("TIMED_OUT", state["status"])

    def test_orphan_state_for_an_exited_pid_is_recovered_without_kill(self):
        with tempfile.TemporaryDirectory() as raw:
            state_path = Path(raw) / "child_process_state.json"
            state_path.write_text(
                json.dumps(
                    {
                        "status": "RUNNING",
                        "pid": 2147483647,
                        "process_create_time": 0,
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual(
                "ORPHAN_ALREADY_EXITED", recover_orphaned_child(state_path)
            )
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual("ORPHAN_ALREADY_EXITED", state["status"])

    def test_heldout_schedule_consumer_forwards_cohort_and_records_terminal_failure(self):
        scheduled = {
            "run_id": "gpt-5.6-luna__heldout-v3__ASW-HO-MIN-01__R1__repair-off",
            "cohort": "heldout",
            "model": "gpt-5.6-luna",
            "case_id": "ASW-HO-MIN-01",
            "tier": "MIN",
            "repetition": 1,
            "seed": 104729,
            "repair_mode": "off",
            "requirement_source_canonical_sha256": "a" * 64,
            "case_sha256": "b" * 64,
        }
        schedule = {
            "content_sha256": "c" * 64,
            "freeze_manifest_path": "offline-freeze.json",
            "freeze_manifest_file_sha256": "d" * 64,
            "freeze_manifest_sha256": "e" * 64,
            "experiment_contract_sha256": "f" * 64,
            "neo4j_context_sha256": "1" * 64,
            "runs": [scheduled],
        }
        calls = []

        def fake_child(
            command, *, cwd, timeout_seconds, state_path,
            stdout_path=None, stderr_path=None,
        ):
            calls.append(list(command))
            run_root = Path(command[command.index("--run-root") + 1])
            attempt = int(command[command.index("--attempt-number") + 1])
            summary = {
                **{
                    key: scheduled[key]
                    for key in (
                        "cohort",
                        "model",
                        "case_id",
                        "repetition",
                        "seed",
                        "repair_mode",
                        "requirement_source_canonical_sha256",
                        "case_sha256",
                    )
                },
                "schedule_content_sha256": schedule["content_sha256"],
                "freeze_manifest_sha256": schedule["freeze_manifest_sha256"],
                "experiment_contract_sha256": schedule[
                    "experiment_contract_sha256"
                ],
                "neo4j_context_sha256": schedule["neo4j_context_sha256"],
                "attempt_number": attempt,
                "final_status": "failure",
                "error": "selection path conflict",
            }
            (run_root / "run_summary.json").write_text(
                json.dumps(summary), encoding="utf-8"
            )
            # A model/selection failure happens after the provider answered, so
            # the run carries a delivered-response audit row.  Without it the
            # failure would correctly be unclassified rather than attributed to
            # the model.
            (run_root / "provider_calls.jsonl").write_text(
                json.dumps(
                    {
                        "credentials_included": False,
                        "provider_call_id": "call_heldout",
                        "response_id": "resp_heldout",
                        "usage": {
                            "input_tokens": 8,
                            "output_tokens": 4,
                            "total_tokens": 12,
                        },
                    }
                )
                + chr(10),
                encoding="utf-8",
            )
            (run_root / "provider_call_transitions.jsonl").write_text(
                chr(10).join(
                    json.dumps({
                        "credentials_included": False,
                        "provider_call_id": "call_heldout",
                        "pipeline_phase": "round2.component",
                        "logical_call_index": 2,
                        "stage": stage,
                        "dispatch_started": True,
                        "request_acceptance_known": True,
                        "response_headers_received": True,
                        "response_id": "resp_heldout",
                    })
                    for stage in (
                        "PRE_DISPATCH", "DISPATCH_STARTED", "RESPONSE_RECEIVED",
                        "LOCAL_AUDIT_PERSISTED",
                    )
                ) + chr(10),
                encoding="utf-8",
            )
            return ChildProcessResult(1, "", "selection path conflict", False)

        freeze = {
            "experiment_contract_sha256": schedule["experiment_contract_sha256"],
            "neo4j_context_sha256": schedule["neo4j_context_sha256"],
        }
        with tempfile.TemporaryDirectory() as raw, patch(
            "run_asw_v3_experiment.verify_schedule", return_value=schedule
        ), patch(
            "run_asw_v3_experiment.verify_freeze_manifest", return_value=freeze
        ), patch(
            "run_asw_v3_experiment.run_child_process", side_effect=fake_child
        ):
            result = run_experiment(schedule, Path(raw), timeout_seconds=1800)
        self.assertEqual(1, len(calls))
        cohort_position = calls[0].index("--cohort")
        self.assertEqual("heldout", calls[0][cohort_position + 1])
        self.assertTrue(result["experiment_complete"])
        self.assertEqual(
            {"MODEL_OR_SCHEMA_GENERATION_FAILURE": 1}, result["status_counts"]
        )
        self.assertEqual("heldout", result["records"][0]["cohort"])
        self.assertIsNone(result["records"][0]["xsd_all_pass"])


class RepositoryFingerprintGateTests(unittest.TestCase):
    """The freeze pins the working tree, so something has to exercise that.

    Three schedule-semantics tests used to reach this gate incidentally and
    error on it while the tree was intentionally dirty.  They now mock
    ``verify_freeze_manifest`` away -- correctly, since they are about schedule
    construction -- which left the branch/HEAD/dirty-state comparison itself
    with no coverage at all, immediately before the one permitted rebuild of
    the freeze chain.  These tests run the real verifier.
    """

    @staticmethod
    def git(*arguments: str) -> str:
        return experiment_freeze._git_value(*arguments)

    def signed(self, **repository: str) -> Path:
        """A manifest that is valid up to the repository comparison."""
        frontend_relative = "README.md"
        frontend_path = experiment_freeze.FRONTEND_ROOT / frontend_relative
        heldout_source = self.heldout_root / "heldout_cases.yaml"
        heldout_review_files = {
            "claude": "claude_review.json",
            "human_autosar_reviewer": "human_autosar_review.json",
        }
        heldout_file_map = {
            path.name: experiment_freeze.sha256_file(path)
            for path in self.heldout_root.iterdir()
            if path.is_file()
        }
        heldout_inventory = json.loads(
            (self.heldout_root / "v15_structure_inventory.json").read_text(
                encoding="utf-8"
            )
        )
        manifest = {
            "schema_version": "atlas.autosar.paper_artifact_freeze.v3",
            "repository": {
                "branch": self.git("branch", "--show-current"),
                "head": self.git("rev-parse", "HEAD"),
                "status_sha256": hashlib.sha256(
                    self.git("status", "--short").encode("utf-8")
                ).hexdigest(),
                **repository,
            },
            "unified_frontend": {
                "root": str(experiment_freeze.FRONTEND_ROOT),
                "formal_v16_result_source": False,
                "provider_calls_enabled": False,
                "local_acceptance_gate": {
                    "decision": "PASS",
                    "external_model_api_calls": 0,
                },
                "files": {
                    frontend_relative: experiment_freeze.sha256_file(frontend_path)
                },
            },
            "prospective_internally_authored_heldout": {
                "case_count": 12,
                "run_count": 36,
                "unit_of_analysis": "case",
                "repetitions_per_case": 3,
                "structural_role_case_counts": {
                    "REPLICATION": 6,
                    "EXTENSION": 6,
                },
                "tier_by_structural_role_case_counts": {
                    f"{tier}:{role}": 2
                    for tier in ("minimal", "standard", "full")
                    for role in ("REPLICATION", "EXTENSION")
                },
                "factorial_balance": "PASS",
                "pooling_policy": "stratified_primary_pooled_balanced_mixture_descriptive_only",
                "external_benchmark": False,
                "package_schema_version": "atlas.autosar.heldout.review_package.v3",
                "source_sha256": experiment_freeze.sha256_file(heldout_source),
                "v15_structure_inventory_sha256": heldout_file_map[
                    "v15_structure_inventory.json"
                ],
                "v15_structure_inventory_content_sha256": heldout_inventory[
                    "inventory_content_sha256"
                ],
                "admission_reviews": {
                    role: {
                        "reviewer": role,
                        "review_decision": "PASS",
                        "source_sha256": experiment_freeze.sha256_file(
                            heldout_source
                        ),
                        "file": filename,
                        "file_sha256": heldout_file_map[filename],
                    }
                    for role, filename in heldout_review_files.items()
                },
                "files": heldout_file_map,
            },
        }
        manifest["manifest_sha256"] = canonical_sha256(manifest)
        path = Path(self.directory) / "freeze.json"
        path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return path

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.directory = self.temporary.name
        self.addCleanup(self.temporary.cleanup)
        original_heldout_root = experiment_freeze.HELDOUT_ROOT
        self.heldout_root = Path(self.directory) / "heldout"
        self.heldout_root.mkdir()
        (self.heldout_root / "heldout_cases.yaml").write_bytes(
            (original_heldout_root / "heldout_cases.yaml").read_bytes()
        )
        (self.heldout_root / "v15_structure_inventory.json").write_bytes(
            (original_heldout_root / "v15_structure_inventory.json").read_bytes()
        )
        for filename in ("claude_review.json", "human_autosar_review.json"):
            (self.heldout_root / filename).write_text(
                json.dumps({"test_fixture": filename}), encoding="utf-8"
            )
        experiment_freeze.HELDOUT_ROOT = self.heldout_root
        self.addCleanup(
            setattr, experiment_freeze, "HELDOUT_ROOT", original_heldout_root
        )

    def test_a_changed_dirty_state_is_refused(self) -> None:
        path = self.signed(status_sha256="0" * 64)
        with self.assertRaisesRegex(
            ExperimentFreezeError, "dirty-state fingerprint differs from freeze"
        ):
            verify_freeze_manifest(path)

    def test_a_changed_head_is_refused(self) -> None:
        path = self.signed(head="0" * 40)
        with self.assertRaisesRegex(
            ExperimentFreezeError, "branch or HEAD differs from freeze"
        ):
            verify_freeze_manifest(path)

    def test_a_changed_branch_is_refused(self) -> None:
        path = self.signed(branch="not-the-frozen-branch")
        with self.assertRaisesRegex(
            ExperimentFreezeError, "branch or HEAD differs from freeze"
        ):
            verify_freeze_manifest(path)

    def test_the_current_tree_passes_the_repository_comparison(self) -> None:
        """Without this the three refusals above could pass for a wrong reason.

        A manifest carrying the current branch, HEAD, and status hash must get
        *past* the repository comparison.  It still fails afterwards, on the
        frozen file maps this stub does not carry, which is what distinguishes
        a working gate from one that refuses everything.
        """
        with self.assertRaises(ExperimentFreezeError) as caught:
            verify_freeze_manifest(self.signed())
        message = str(caught.exception)
        self.assertNotIn("dirty-state fingerprint", message)
        self.assertNotIn("branch or HEAD", message)
        self.assertEqual("public runtime configuration differs from freeze", message)

    def test_a_changed_unified_frontend_file_is_refused(self) -> None:
        path = self.signed()
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["unified_frontend"]["files"]["README.md"] = "0" * 64
        manifest["manifest_sha256"] = canonical_sha256(
            {key: value for key, value in manifest.items() if key != "manifest_sha256"}
        )
        path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(
            ExperimentFreezeError, "unified frontend hash mismatch"
        ):
            verify_freeze_manifest(path)

    def test_a_missing_unified_frontend_identity_is_refused(self) -> None:
        path = self.signed()
        manifest = json.loads(path.read_text(encoding="utf-8"))
        del manifest["unified_frontend"]
        manifest["manifest_sha256"] = canonical_sha256(
            {key: value for key, value in manifest.items() if key != "manifest_sha256"}
        )
        path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(
            ExperimentFreezeError, "frontend freeze identity is incomplete"
        ):
            verify_freeze_manifest(path)

    def test_a_changed_heldout_review_file_is_refused(self) -> None:
        path = self.signed()
        (self.heldout_root / "claude_review.json").write_text(
            "tampered", encoding="utf-8"
        )
        with self.assertRaisesRegex(
            ExperimentFreezeError, "held-out hash mismatch"
        ):
            verify_freeze_manifest(path)

    def test_a_rehashed_but_tampered_v15_structure_inventory_is_refused(self) -> None:
        path = self.signed()
        inventory_path = self.heldout_root / "v15_structure_inventory.json"
        inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
        inventory["records"][0]["tier"] = "tampered"
        inventory_path.write_text(json.dumps(inventory), encoding="utf-8")
        observed = experiment_freeze.sha256_file(inventory_path)
        manifest = json.loads(path.read_text(encoding="utf-8"))
        heldout = manifest["prospective_internally_authored_heldout"]
        heldout["files"]["v15_structure_inventory.json"] = observed
        heldout["v15_structure_inventory_sha256"] = observed
        manifest["manifest_sha256"] = canonical_sha256(
            {key: value for key, value in manifest.items() if key != "manifest_sha256"}
        )
        path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(
            ExperimentFreezeError, "V15 structure inventory identity is incomplete"
        ):
            verify_freeze_manifest(path)

    def test_a_missing_heldout_admission_identity_is_refused(self) -> None:
        path = self.signed()
        manifest = json.loads(path.read_text(encoding="utf-8"))
        del manifest["prospective_internally_authored_heldout"]
        manifest["manifest_sha256"] = canonical_sha256(
            {key: value for key, value in manifest.items() if key != "manifest_sha256"}
        )
        path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(
            ExperimentFreezeError, "held-out admission freeze identity is incomplete"
        ):
            verify_freeze_manifest(path)

    def test_an_unbalanced_heldout_cell_ledger_is_refused(self) -> None:
        path = self.signed()
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["prospective_internally_authored_heldout"][
            "tier_by_structural_role_case_counts"
        ]["full:EXTENSION"] = 1
        manifest["manifest_sha256"] = canonical_sha256(
            {key: value for key, value in manifest.items() if key != "manifest_sha256"}
        )
        path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(
            ExperimentFreezeError, "held-out admission freeze identity is incomplete"
        ):
            verify_freeze_manifest(path)

    def test_a_pooled_only_heldout_policy_is_refused(self) -> None:
        path = self.signed()
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["prospective_internally_authored_heldout"][
            "pooling_policy"
        ] = "pooled_only"
        manifest["manifest_sha256"] = canonical_sha256(
            {key: value for key, value in manifest.items() if key != "manifest_sha256"}
        )
        path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(
            ExperimentFreezeError, "held-out admission freeze identity is incomplete"
        ):
            verify_freeze_manifest(path)

    def test_the_canonical_hash_is_checked_before_the_repository(self) -> None:
        path = Path(self.directory) / "unsigned.json"
        path.write_text(
            json.dumps(
                {
                    "schema_version": "atlas.autosar.paper_artifact_freeze.v3",
                    "manifest_sha256": "0" * 64,
                    "repository": {},
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(
            ExperimentFreezeError, "canonical hash mismatch"
        ):
            verify_freeze_manifest(path)


if __name__ == "__main__":
    unittest.main()
