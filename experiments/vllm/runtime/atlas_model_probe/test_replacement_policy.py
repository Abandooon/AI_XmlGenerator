"""The replacement layer must recover losses without inventing observations."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import delivery_classification as dc
import replacement_policy as rp
import run_asw_v3_experiment as runner


def record(run_id, kind, delivery=None, attempts=0, decision="PASS", **extra):
    return {
        "independent_decision": decision,
        "run_id": run_id,
        "case_id": run_id.split("__")[1] if "__" in run_id else run_id,
        "repetition": 1,
        "seed": 104729,
        "completion_kind": kind,
        "delivery_state": delivery,
        "billing_state": dc.BILLING_CONFIRMED,
        "replacement_attempts": attempts,
        **extra,
    }


def canonical(value):
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":")
    ).encode()).hexdigest()


def file_sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def schedule(run_ids, freeze_path=None):
    body = {
        "schema_version": "atlas.autosar.asw_v3.experiment_schedule.v1",
        "freeze_manifest_sha256": "b" * 64,
        "freeze_manifest_path": str(freeze_path) if freeze_path else "unused.json",
        "freeze_manifest_file_sha256": (
            file_sha(freeze_path) if freeze_path else "1" * 64
        ),
        "experiment_contract_sha256": "c" * 64,
        "neo4j_context_sha256": "d" * 64,
        "models": ["gpt-5.6-luna"],
        "repair_mode": "off",
        "runs": [
            {
                "run_id": r,
                "case_id": "ASW-MIN-01",
                "tier": "minimal",
                "repetition": 1,
                "seed": 104729,
                "model": "gpt-5.6-luna",
                "prompt_sha256": "e" * 64,
                "case_sha256": "f" * 64,
                "repair_mode": "off",
                "requirement_source_canonical_sha256": "0" * 64,
            }
            for r in run_ids
        ],
    }
    return {**body, "content_sha256": canonical(body)}


def results(records, complete=True, embedded_schedule=None):
    body = {
        "experiment_complete": complete,
        "completed_at_utc": "2026-08-25T00:00:00+00:00",
        "records": records,
    }
    if embedded_schedule is not None:
        body["schedule"] = embedded_schedule
    return {**body, "content_sha256": canonical(body)}


class PolicyArtifactTests(unittest.TestCase):
    def test_policy_artifact_is_deterministic_and_timeless(self):
        first = rp.build_policy_artifact()
        second = rp.build_policy_artifact()
        self.assertEqual(first, second)
        self.assertEqual(rp.POLICY_VERSION, first["schema_version"])
        self.assertEqual(
            rp.SCHEDULE_SCHEMA_VERSION,
            first["replacement_schedule_schema_version"],
        )
        self.assertNotIn("created_at_utc", first)
        self.assertNotIn("bound_to", first)
        unsigned = {
            key: value for key, value in first.items()
            if key != "content_sha256"
        }
        self.assertEqual(canonical(unsigned), first["content_sha256"])

    def test_no_provider_guarantee_leaves_only_predispatch_eligibility(self):
        policy = rp.build_policy_artifact()
        self.assertFalse(policy["provider_no_execution_guarantee_frozen"])
        self.assertEqual(
            [dc.DEFINITELY_NOT_DISPATCHED],
            policy["currently_operational_eligibility_states"],
        )
        self.assertIn(
            "paper_artifact_freeze", policy["policy_document_role"]
        )


class EligibilityTests(unittest.TestCase):
    def test_definitely_not_dispatched_is_replaceable(self):
        ok, reason = rp.slot_is_replaceable(
            record("r1", dc.INFRASTRUCTURE_TRANSPORT_FAILURE,
                   dc.DEFINITELY_NOT_DISPATCHED)
        )
        self.assertTrue(ok)
        self.assertIn("no model execution was possible", reason)

    def test_a_rejection_before_execution_is_replaceable(self):
        ok, _ = rp.slot_is_replaceable(
            record("r1", dc.INFRASTRUCTURE_TRANSPORT_FAILURE,
                   dc.REJECTED_BEFORE_EXECUTION)
        )
        self.assertTrue(ok)

    def test_ambiguous_delivery_is_never_replaced(self):
        ok, reason = rp.slot_is_replaceable(
            record("r1", dc.AMBIGUOUS_PROVIDER_DELIVERY, dc.DELIVERY_AMBIGUOUS)
        )
        self.assertFalse(ok)
        self.assertIn("second paid execution", reason)
        self.assertIn("stays missing", reason)

    def test_unclassified_failure_is_never_replaced(self):
        ok, reason = rp.slot_is_replaceable(
            record("r1", dc.UNCLASSIFIED_FAILURE, dc.DELIVERY_UNKNOWN)
        )
        self.assertFalse(ok)
        self.assertIn("stays missing", reason)

    def test_a_model_result_is_never_replaced(self):
        for kind in (dc.SUCCESSFUL_ARTIFACT, dc.MODEL_OR_SCHEMA_GENERATION_FAILURE):
            with self.subTest(kind=kind):
                ok, reason = rp.slot_is_replaceable(
                    record("r1", kind, dc.DELIVERY_CONFIRMED)
                )
                self.assertFalse(ok)
                self.assertIn("model result", reason)

    def test_one_replacement_only_then_missing(self):
        ok, reason = rp.slot_is_replaceable(
            record("r1", dc.INFRASTRUCTURE_TRANSPORT_FAILURE,
                   dc.DEFINITELY_NOT_DISPATCHED, attempts=1)
        )
        self.assertFalse(ok)
        self.assertIn("recursive retry", reason)
        self.assertIn("missing", reason)


class ScheduleDerivationTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.freeze = self.root / "freeze.json"
        self.freeze.write_text("{}\n", encoding="utf-8")

    def build(self, original, observed):
        schedule_path = self.root / "original_schedule.json"
        results_path = self.root / "original_results.json"
        schedule_path.write_text(json.dumps(original, sort_keys=True), encoding="utf-8")
        results_path.write_text(json.dumps(observed, sort_keys=True), encoding="utf-8")
        return rp.build_replacement_schedule(
            original,
            observed,
            original_schedule_path=schedule_path,
            original_results_path=results_path,
        )

    def test_a_replacement_may_not_be_derived_from_an_incomplete_cohort(self):
        original = schedule(["r1"], self.freeze)
        with self.assertRaisesRegex(rp.ReplacementPolicyError, "completed"):
            self.build(
                original,
                results([record("r1", dc.INFRASTRUCTURE_TRANSPORT_FAILURE,
                                dc.DEFINITELY_NOT_DISPATCHED)], complete=False,
                        embedded_schedule=original),
            )

    def test_the_schedule_binds_every_required_identity(self):
        original = schedule(["r1"], self.freeze)
        observed = results([record(
            "r1", dc.INFRASTRUCTURE_TRANSPORT_FAILURE,
            dc.DEFINITELY_NOT_DISPATCHED,
        )], embedded_schedule=original)
        built = self.build(
            original,
            observed,
        )
        self.assertEqual(original["content_sha256"], built["original_schedule_content_sha256"])
        self.assertEqual(observed["content_sha256"], built["original_results_content_sha256"])
        self.assertEqual("b" * 64, built["freeze_manifest_sha256"])
        self.assertEqual(file_sha(self.freeze), built["freeze_manifest_file_sha256"])
        self.assertEqual(1, built["pipeline_run_count"])
        row = built["runs"][0]
        self.assertEqual("r1", row["replaces_run_id"])
        self.assertEqual(104729, row["seed"])
        self.assertEqual("e" * 64, row["prompt_sha256"])
        self.assertEqual("gpt-5.6-luna", row["model"])
        self.assertTrue(row["original_failure_fingerprint"])

    def test_identical_source_artifacts_produce_an_identical_schedule(self):
        original = schedule(["r1"], self.freeze)
        observed = results([record(
            "r1", dc.INFRASTRUCTURE_TRANSPORT_FAILURE,
            dc.DEFINITELY_NOT_DISPATCHED,
        )], embedded_schedule=original)
        first = self.build(original, observed)
        second = self.build(original, observed)
        self.assertEqual(observed["completed_at_utc"], first["created_at_utc"])
        self.assertEqual(first, second)
        self.assertEqual(first["content_sha256"], second["content_sha256"])

    def test_completed_results_without_a_completion_time_fail_closed(self):
        original = schedule(["r1"], self.freeze)
        observed = results([record(
            "r1", dc.INFRASTRUCTURE_TRANSPORT_FAILURE,
            dc.DEFINITELY_NOT_DISPATCHED,
        )], embedded_schedule=original)
        observed.pop("completed_at_utc")
        observed["content_sha256"] = canonical({
            key: value for key, value in observed.items()
            if key != "content_sha256"
        })
        with self.assertRaisesRegex(
            rp.ReplacementPolicyError, "deterministic timestamp"
        ):
            self.build(original, observed)

    def test_the_replacement_is_its_own_cohort_and_layer(self):
        original = schedule(["r1"], self.freeze)
        built = self.build(
            original,
            results([record("r1", dc.INFRASTRUCTURE_TRANSPORT_FAILURE,
                            dc.DEFINITELY_NOT_DISPATCHED)],
                    embedded_schedule=original),
        )
        self.assertEqual("replacement", built["cohort"])
        self.assertEqual("replacement_sensitivity", built["analysis_layer"])
        self.assertTrue(built["not_admissible_to_original_denominator"])
        self.assertNotEqual("r1", built["runs"][0]["run_id"])

    def test_ineligible_losses_are_recorded_as_refused_not_dropped(self):
        original = schedule(["r1", "r2"], self.freeze)
        built = self.build(
            original,
            results([
                record("r1", dc.AMBIGUOUS_PROVIDER_DELIVERY, dc.DELIVERY_AMBIGUOUS),
                record("r2", dc.UNCLASSIFIED_FAILURE, dc.DELIVERY_UNKNOWN),
            ], embedded_schedule=original),
        )
        self.assertEqual(0, built["pipeline_run_count"])
        self.assertEqual(2, len(built["refused_slots"]))
        self.assertEqual(
            {dc.AMBIGUOUS_PROVIDER_DELIVERY, dc.UNCLASSIFIED_FAILURE},
            {item["completion_kind"] for item in built["refused_slots"]},
        )

    def test_the_failure_fingerprint_changes_with_the_failure(self):
        first = rp.failure_fingerprint(
            record("r1", dc.INFRASTRUCTURE_TRANSPORT_FAILURE,
                   dc.DEFINITELY_NOT_DISPATCHED)
        )
        second = rp.failure_fingerprint(
            record("r1", dc.AMBIGUOUS_PROVIDER_DELIVERY, dc.DELIVERY_AMBIGUOUS)
        )
        self.assertNotEqual(first, second)

    def verified_schedule(self):
        original = schedule(["r1"], self.freeze)
        observed = results([record(
            "r1", dc.INFRASTRUCTURE_TRANSPORT_FAILURE,
            dc.DEFINITELY_NOT_DISPATCHED,
        )], embedded_schedule=original)
        built = self.build(original, observed)
        freeze = {
            "manifest_sha256": built["freeze_manifest_sha256"],
            "experiment_contract_sha256": built["experiment_contract_sha256"],
            "neo4j_context_sha256": built["neo4j_context_sha256"],
        }
        return original, observed, built, freeze

    def test_verifier_recomputes_the_bound_failure_fingerprint(self):
        original, observed, built, freeze = self.verified_schedule()
        tampered = json.loads(json.dumps(built))
        tampered["runs"][0]["original_failure_fingerprint"] = "0" * 64
        unsigned = {key: value for key, value in tampered.items()
                    if key != "content_sha256"}
        tampered["content_sha256"] = canonical(unsigned)
        with patch.object(runner, "verify_schedule", return_value=original), patch.object(
            runner, "verify_experiment_results", return_value=observed
        ), patch.object(runner, "verify_freeze_manifest", return_value=freeze):
            with self.assertRaisesRegex(ValueError, "fingerprint mismatch"):
                runner._verify_replacement_schedule(tampered)

    def test_verifier_rejects_source_result_file_tampering(self):
        original, observed, built, freeze = self.verified_schedule()
        Path(built["original_results_path"]).write_text("{}\n", encoding="utf-8")
        with patch.object(runner, "verify_schedule", return_value=original), patch.object(
            runner, "verify_experiment_results", return_value=observed
        ), patch.object(runner, "verify_freeze_manifest", return_value=freeze):
            with self.assertRaisesRegex(ValueError, "file hash mismatch"):
                runner._verify_replacement_schedule(built)

    def test_verifier_rejects_a_dropped_eligible_slot(self):
        original, observed, built, freeze = self.verified_schedule()
        tampered = json.loads(json.dumps(built))
        tampered["runs"] = []
        tampered["pipeline_run_count"] = 0
        unsigned = {key: value for key, value in tampered.items()
                    if key != "content_sha256"}
        tampered["content_sha256"] = canonical(unsigned)
        with patch.object(runner, "verify_schedule", return_value=original), patch.object(
            runner, "verify_experiment_results", return_value=observed
        ), patch.object(runner, "verify_freeze_manifest", return_value=freeze):
            with self.assertRaisesRegex(ValueError, "drops or invents"):
                runner._verify_replacement_schedule(tampered)

    def test_verifier_rejects_a_wall_clock_timestamp(self):
        original, observed, built, freeze = self.verified_schedule()
        tampered = json.loads(json.dumps(built))
        tampered["created_at_utc"] = "2099-01-01T00:00:00+00:00"
        unsigned = {key: value for key, value in tampered.items()
                    if key != "content_sha256"}
        tampered["content_sha256"] = canonical(unsigned)
        with patch.object(runner, "verify_schedule", return_value=original), patch.object(
            runner, "verify_experiment_results", return_value=observed
        ), patch.object(runner, "verify_freeze_manifest", return_value=freeze):
            with self.assertRaisesRegex(ValueError, "deterministically bound"):
                runner._verify_replacement_schedule(tampered)

    def test_verifier_rejects_tampered_refused_slot_reporting(self):
        original = schedule(["r1"], self.freeze)
        observed = results([record(
            "r1", dc.AMBIGUOUS_PROVIDER_DELIVERY, dc.DELIVERY_AMBIGUOUS,
        )], embedded_schedule=original)
        built = self.build(original, observed)
        freeze = {
            "manifest_sha256": built["freeze_manifest_sha256"],
            "experiment_contract_sha256": built["experiment_contract_sha256"],
            "neo4j_context_sha256": built["neo4j_context_sha256"],
        }
        tampered = json.loads(json.dumps(built))
        tampered["refused_slots"] = []
        unsigned = {key: value for key, value in tampered.items()
                    if key != "content_sha256"}
        tampered["content_sha256"] = canonical(unsigned)
        with patch.object(runner, "verify_schedule", return_value=original), patch.object(
            runner, "verify_experiment_results", return_value=observed
        ), patch.object(runner, "verify_freeze_manifest", return_value=freeze):
            with self.assertRaisesRegex(ValueError, "deterministic source derivation"):
                runner._verify_replacement_schedule(tampered)


class LayeredReportingTests(unittest.TestCase):
    def setUp(self):
        self.original = results([
            record("r1", dc.SUCCESSFUL_ARTIFACT, dc.DELIVERY_CONFIRMED),
            record("r2", dc.SUCCESSFUL_ARTIFACT, dc.DELIVERY_CONFIRMED),
            record("r3", dc.MODEL_OR_SCHEMA_GENERATION_FAILURE,
                   dc.DELIVERY_CONFIRMED),
            record("r4", dc.AMBIGUOUS_PROVIDER_DELIVERY, dc.DELIVERY_AMBIGUOUS),
            record("r5", dc.INFRASTRUCTURE_TRANSPORT_FAILURE,
                   dc.DEFINITELY_NOT_DISPATCHED),
            record("r6", dc.UNCLASSIFIED_FAILURE, dc.DELIVERY_UNKNOWN),
        ])

    def test_the_operational_denominator_keeps_every_slot(self):
        summary = rp.summarize_layers(self.original)
        self.assertEqual(6, summary["operational_reliability"]["denominator"])
        self.assertEqual(
            6, summary["operational_reliability"]["scheduled_slots"]
        )

    def test_the_model_quality_denominator_excludes_infrastructure(self):
        summary = rp.summarize_layers(self.original)
        quality = summary["conditional_model_quality"]
        self.assertEqual(3, quality["denominator"])
        self.assertEqual(2, quality["passing"])
        self.assertEqual(3, quality["excluded_from_denominator"])

    def test_the_two_denominators_are_never_the_same_number_by_accident(self):
        summary = rp.summarize_layers(self.original)
        self.assertNotEqual(
            summary["operational_reliability"]["denominator"],
            summary["conditional_model_quality"]["denominator"],
        )
        self.assertIn(
            "never published without the operational denominator",
            summary["conditional_model_quality"]["note"],
        )

    def test_a_produced_artifact_is_not_a_pass_without_an_independent_pass(self):
        """The numerator defect GPT found: artifact produced, evaluation FAIL."""
        original = results([
            record("r1", dc.SUCCESSFUL_ARTIFACT, dc.DELIVERY_CONFIRMED,
                   decision="PASS"),
            record("r2", dc.SUCCESSFUL_ARTIFACT, dc.DELIVERY_CONFIRMED,
                   decision="FAIL"),
        ])
        summary = rp.summarize_layers(original)
        self.assertEqual(1, summary["conditional_model_quality"]["passing"])
        self.assertEqual(
            1,
            summary["conditional_model_quality"][
                "artifacts_produced_but_not_passing"
            ],
        )
        self.assertEqual(2, summary["conditional_model_quality"]["denominator"])
        self.assertEqual(1, summary["operational_success"]["passing"])
        self.assertEqual(2, summary["operational_success"]["denominator"])

    def test_the_primary_endpoint_keeps_every_scheduled_slot(self):
        summary = rp.summarize_layers(self.original)
        self.assertEqual(6, summary["operational_success"]["denominator"])
        self.assertEqual(2, summary["operational_success"]["passing"])
        self.assertIn(
            "intention-to-treat", summary["operational_success"]["note"]
        )

    def test_the_replacement_layer_is_reported_separately(self):
        replacement = results([
            record("r5__replacement-1", dc.SUCCESSFUL_ARTIFACT,
                   dc.DELIVERY_CONFIRMED),
        ])
        summary = rp.summarize_layers(self.original, replacement)
        layer = summary["replacement_sensitivity"]
        self.assertEqual(1, layer["attempted"])
        self.assertEqual(1, layer["recovered"])
        self.assertEqual(0, layer["recursive_retries"])
        self.assertIn("not filled back", layer["interpretation"])
        # The original rate is untouched by the recovery.
        self.assertEqual(
            2, summary["conditional_model_quality"]["passing"]
        )
        self.assertEqual(3, summary["conditional_model_quality"]["denominator"])

    def test_a_failed_replacement_does_not_recurse(self):
        replacement = results([
            record("r5__replacement-1", dc.AMBIGUOUS_PROVIDER_DELIVERY,
                   dc.DELIVERY_AMBIGUOUS),
        ])
        summary = rp.summarize_layers(self.original, replacement)
        self.assertEqual(1, summary["replacement_sensitivity"]["still_failed"])
        self.assertEqual(0, summary["replacement_sensitivity"]["recovered"])

    def test_forbidden_reporting_is_stated_in_the_summary(self):
        summary = rp.summarize_layers(self.original)
        joined = " ".join(summary["forbidden"])
        self.assertIn("pooling the replacement layer", joined)
        self.assertIn("46/60", joined)


if __name__ == "__main__":
    unittest.main()
