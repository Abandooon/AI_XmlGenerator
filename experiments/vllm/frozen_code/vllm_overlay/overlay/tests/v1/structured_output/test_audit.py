# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright contributors to the vLLM project

from __future__ import annotations

import json
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

try:
    from vllm.v1.structured_output.audit import (
        BindingObservationTracker,
        StructuredOutputAuditError,
        StructuredOutputAuditSink,
        binding_rate,
        binding_step,
        classify_binding_observations,
        hash_packed_bitmask,
        hash_token_ids,
        packed_bitmask_allowed_token_count,
        structured_output_audit_context,
        verify_audit_records,
    )
except ModuleNotFoundError as exc:
    # Keep the pure-standard-library audit tests runnable in lightweight source
    # checkouts where the vllm package cannot be imported because its runtime
    # dependencies or sibling modules are absent. Full vLLM CI takes the normal
    # import path above. Narrowing this to "torch" alone was not enough: on a
    # bare checkout the first failure is vllm.config, so the fallback never ran.
    missing = exc.name or ""
    if missing != "torch" and not missing.startswith("vllm"):
        raise
    audit_path = (
        Path(__file__).resolve().parents[3]
        / "vllm"
        / "v1"
        / "structured_output"
        / "audit.py"
    )
    spec = importlib.util.spec_from_file_location("vllm_audit_under_test", audit_path)
    assert spec is not None and spec.loader is not None
    audit_module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = audit_module
    spec.loader.exec_module(audit_module)
    StructuredOutputAuditError = audit_module.StructuredOutputAuditError
    StructuredOutputAuditSink = audit_module.StructuredOutputAuditSink
    BindingObservationTracker = audit_module.BindingObservationTracker
    binding_rate = audit_module.binding_rate
    binding_step = audit_module.binding_step
    classify_binding_observations = audit_module.classify_binding_observations
    hash_packed_bitmask = audit_module.hash_packed_bitmask
    hash_token_ids = audit_module.hash_token_ids
    packed_bitmask_allowed_token_count = audit_module.packed_bitmask_allowed_token_count
    structured_output_audit_context = audit_module.structured_output_audit_context
    verify_audit_records = audit_module.verify_audit_records


class PackedBitmaskTests(unittest.TestCase):
    def test_token_id_hash_uses_canonical_json_array_bytes(self) -> None:
        import hashlib

        self.assertEqual(
            hash_token_ids([1, 2, 300]),
            hashlib.sha256(b"[1,2,300]").hexdigest(),
        )

    def test_zero_mask(self) -> None:
        self.assertEqual(packed_bitmask_allowed_token_count([0, 0], 64), 0)

    def test_signed_full_words(self) -> None:
        self.assertEqual(packed_bitmask_allowed_token_count([-1, -1], 64), 64)

    def test_padding_bits_are_excluded(self) -> None:
        self.assertEqual(packed_bitmask_allowed_token_count([-1, -1], 33), 33)

    def test_sign_bit_is_one_token(self) -> None:
        self.assertEqual(packed_bitmask_allowed_token_count([-2147483648], 32), 1)

    def test_short_mask_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "shorter_than_vocab_size"):
            packed_bitmask_allowed_token_count([0], 33)

    def test_mask_hash_is_stable_across_signed_representation(self) -> None:
        self.assertEqual(
            hash_packed_bitmask([-1], 32),
            hash_packed_bitmask([0xFFFFFFFF], 32),
        )

    def test_binding_step_classifies_pre_mask_argmax(self) -> None:
        self.assertTrue(binding_step([0b10], 32, 0)["bound"])
        self.assertFalse(binding_step([0b10], 32, 1)["bound"])

    def test_binding_rate_excludes_non_evaluable_steps(self) -> None:
        self.assertEqual(
            {
                "steps_observed": 2,
                "steps_bound": 1,
                "binding_rate": 0.5,
            },
            binding_rate(
                [
                    {"bound": True},
                    {"bound": False},
                    {"bound": None, "evaluable": False},
                ]
            ),
        )

    def test_binding_observations_preserve_request_identity(self) -> None:
        self.assertEqual(
            {"req-a": True, "req-b": False},
            classify_binding_observations(
                ["req-a", "req-b"],
                [[0b10], [0b10]],
                32,
                [0, 1],
            ),
        )

    def test_binding_observations_reject_duplicate_request_rows(self) -> None:
        with self.assertRaisesRegex(
            StructuredOutputAuditError, "duplicate_binding_request_row"
        ):
            classify_binding_observations(
                ["req-a", "req-a"],
                [[0b10], [0b10]],
                32,
                [0, 1],
            )


class AuditSinkTests(unittest.TestCase):
    def test_complete_trace_verifies(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            sink = StructuredOutputAuditSink(
                Path(temp_dir), required=True, queue_size=16
            )
            sink.start_request("req-1", {"grammar_sha256": "a" * 64})
            sink.record_event("req-1", "grammar_compile_start")
            sink.record_event("req-1", "grammar_compile_end", {"status": "PASS"})
            sink.end_request(
                "req-1", finish_reason="FINISHED_STOPPED", output_token_ids=[1, 2, 3]
            )
            sink.close()
            assert sink.output_path is not None
            records = [
                json.loads(line)
                for line in sink.output_path.read_text(encoding="utf-8").splitlines()
            ]
            result = verify_audit_records(records)
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["request_count"], 1)
            self.assertEqual([record["sequence"] for record in records], [0, 1, 2, 3])

    def test_event_without_start_fails_closed(self) -> None:
        sink = StructuredOutputAuditSink(None)
        sink.record_event("missing", "mask_ready")  # Disabled audit is a no-op.
        with tempfile.TemporaryDirectory() as temp_dir:
            enabled = StructuredOutputAuditSink(Path(temp_dir), required=True)
            with self.assertRaisesRegex(
                StructuredOutputAuditError, "without_request_start"
            ):
                enabled.record_event("missing", "mask_ready")
            enabled.close()

    def test_duplicate_start_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            sink = StructuredOutputAuditSink(Path(temp_dir), required=True)
            sink.start_request("req-1", {})
            sink.record_event("req-1", "grammar_compile_start")
            sink.record_event("req-1", "grammar_compile_end", {"status": "PASS"})
            with self.assertRaisesRegex(
                StructuredOutputAuditError, "duplicate_request_start"
            ):
                sink.start_request("req-1", {})
            sink.end_request("req-1", finish_reason="test", output_token_ids=[])
            sink.close()

    def test_tampered_trace_is_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            sink = StructuredOutputAuditSink(Path(temp_dir), required=True)
            sink.start_request("req-1", {})
            sink.record_event("req-1", "grammar_compile_start")
            sink.record_event("req-1", "grammar_compile_end", {"status": "PASS"})
            sink.end_request("req-1", finish_reason="test", output_token_ids=[])
            sink.close()
            assert sink.output_path is not None
            records = [
                json.loads(line)
                for line in sink.output_path.read_text(encoding="utf-8").splitlines()
            ]
            records[0]["event"]["metadata"] = {"tampered": True}
            result = verify_audit_records(records)
            self.assertEqual(result["status"], "INCOMPLETE")
            self.assertIn("req-1:chain_mismatch", result["errors"])

    def test_expected_request_without_trace_is_incomplete(self) -> None:
        result = verify_audit_records([], expected_request_ids=["req-missing"])
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertEqual(result["missing_request_ids"], ["req-missing"])

    def _external_identity_trace(
        self,
        directory: str,
        internal_request_id: str,
        external_request_id: str | None,
    ) -> list[dict[str, object]]:
        sink = StructuredOutputAuditSink(Path(directory), required=True)
        metadata: dict[str, object] = {"binding_required": True}
        if external_request_id is not None:
            metadata["external_request_id"] = external_request_id
        sink.start_request(internal_request_id, metadata)
        sink.record_event(internal_request_id, "grammar_compile_start")
        sink.record_event(
            internal_request_id, "grammar_compile_end", {"status": "PASS"}
        )
        sink.end_request(
            internal_request_id,
            finish_reason="FINISHED_STOPPED",
            output_token_ids=[],
            grammar_terminated=True,
        )
        sink.close()
        assert sink.output_path is not None
        return [
            json.loads(line)
            for line in sink.output_path.read_text(encoding="utf-8").splitlines()
        ]

    def test_random_internal_suffix_joins_by_external_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            records = self._external_identity_trace(
                temp_dir,
                "cmpl-exp-001-a-0-825e1022",
                "cmpl-exp-001-a-0",
            )
            result = verify_audit_records(
                records,
                expected_external_request_ids=["cmpl-exp-001-a-0"],
            )
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(
            result["external_request_id_to_internal_request_id"],
            {"cmpl-exp-001-a-0": "cmpl-exp-001-a-0-825e1022"},
        )

    def test_missing_external_identity_is_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            records = self._external_identity_trace(temp_dir, "internal-a", None)
            result = verify_audit_records(
                records,
                expected_external_request_ids=["external-a"],
            )
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertIn(
            "internal-a:external_request_id_missing", result["errors"]
        )

    def test_wrong_external_identity_is_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            records = self._external_identity_trace(
                temp_dir, "internal-a", "external-wrong"
            )
            result = verify_audit_records(
                records,
                expected_external_request_ids=["external-expected"],
            )
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertEqual(
            result["missing_external_request_ids"], ["external-expected"]
        )
        self.assertEqual(
            result["unexpected_external_request_ids"], ["external-wrong"]
        )

    def test_duplicate_external_identity_is_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            records = self._external_identity_trace(
                first, "internal-a-random", "external-a"
            )
            records += self._external_identity_trace(
                second, "internal-b-random", "external-a"
            )
            result = verify_audit_records(
                records,
                expected_external_request_ids=["external-a"],
            )
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertEqual(result["duplicate_external_request_ids"], ["external-a"])

    def test_unterminated_grammar_is_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            sink = StructuredOutputAuditSink(Path(temp_dir), required=True)
            sink.start_request(
                "internal-a",
                {"binding_required": True, "external_request_id": "external-a"},
            )
            sink.record_event("internal-a", "grammar_compile_start")
            sink.record_event(
                "internal-a", "grammar_compile_end", {"status": "PASS"}
            )
            sink.end_request(
                "internal-a",
                finish_reason="FINISHED_STOPPED",
                output_token_ids=[],
                grammar_terminated=False,
            )
            sink.close()
            assert sink.output_path is not None
            records = [
                json.loads(line)
                for line in sink.output_path.read_text(encoding="utf-8").splitlines()
            ]
            result = verify_audit_records(
                records,
                expected_external_request_ids=["external-a"],
            )
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertIn(
            "internal-a:grammar_not_terminated_at_request_end", result["errors"]
        )

    def test_length_capped_audit_trace_is_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            sink = StructuredOutputAuditSink(Path(temp_dir), required=True)
            sink.start_request(
                "internal-a",
                {"binding_required": True, "external_request_id": "external-a"},
            )
            sink.record_event("internal-a", "grammar_compile_start")
            sink.record_event(
                "internal-a", "grammar_compile_end", {"status": "PASS"}
            )
            sink.end_request(
                "internal-a",
                finish_reason="FINISHED_LENGTH_CAPPED",
                output_token_ids=[],
                grammar_terminated=False,
            )
            sink.close()
            assert sink.output_path is not None
            records = [
                json.loads(line)
                for line in sink.output_path.read_text(encoding="utf-8").splitlines()
            ]
            result = verify_audit_records(
                records,
                expected_external_request_ids=["external-a"],
            )
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertIn(
            "internal-a:request_did_not_finish_normally", result["errors"]
        )

    def test_complete_binding_trace_verifies_and_aggregates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            sink = StructuredOutputAuditSink(Path(temp_dir), required=True)
            sink.start_request(
                "req-1",
                {"binding_required": True, "external_request_id": "external-1"},
            )
            sink.record_event("req-1", "grammar_compile_start")
            sink.record_event("req-1", "grammar_compile_end", {"status": "PASS"})
            for ordinal, bound in enumerate((True, False)):
                sink.record_event(
                    "req-1",
                    "mask_ready",
                    {
                        "sample_ordinal": ordinal,
                        "mask_applied": True,
                    },
                )
                sink.record_event(
                    "req-1",
                    "binding_step",
                    {
                        "sample_ordinal": ordinal,
                        "mask_applied": True,
                        "evaluable": True,
                        "bound": bound,
                    },
                )
            sink.end_request(
                "req-1",
                finish_reason="FINISHED_STOPPED",
                output_token_ids=[1, 2],
                grammar_terminated=True,
            )
            sink.close()
            assert sink.output_path is not None
            records = [
                json.loads(line)
                for line in sink.output_path.read_text(encoding="utf-8").splitlines()
            ]
            result = verify_audit_records(records)
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["binding"]["steps_observed"], 2)
            self.assertEqual(result["binding"]["steps_bound"], 1)
            self.assertEqual(result["binding"]["binding_rate"], 0.5)

    def test_missing_binding_observation_is_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            sink = StructuredOutputAuditSink(Path(temp_dir), required=True)
            sink.start_request(
                "req-1",
                {"binding_required": True, "external_request_id": "external-1"},
            )
            sink.record_event("req-1", "grammar_compile_start")
            sink.record_event("req-1", "grammar_compile_end", {"status": "PASS"})
            sink.record_event(
                "req-1",
                "mask_ready",
                {"sample_ordinal": 0, "mask_applied": True},
            )
            sink.end_request(
                "req-1",
                finish_reason="FINISHED_STOPPED",
                output_token_ids=[],
                grammar_terminated=True,
            )
            sink.close()
            assert sink.output_path is not None
            records = [
                json.loads(line)
                for line in sink.output_path.read_text(encoding="utf-8").splitlines()
            ]
            result = verify_audit_records(records)
            self.assertEqual(result["status"], "INCOMPLETE")
            self.assertIn("req-1:binding_mask_step_mismatch", result["errors"])

    def test_malformed_binding_ordinal_is_incomplete_not_an_exception(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            sink = StructuredOutputAuditSink(Path(temp_dir), required=True)
            sink.start_request(
                "req-1",
                {"binding_required": True, "external_request_id": "external-1"},
            )
            sink.record_event("req-1", "grammar_compile_start")
            sink.record_event("req-1", "grammar_compile_end", {"status": "PASS"})
            sink.record_event(
                "req-1",
                "binding_step",
                {
                    "sample_ordinal": "not-an-integer",
                    "mask_applied": True,
                    "evaluable": True,
                    "bound": True,
                },
            )
            sink.end_request(
                "req-1",
                finish_reason="FINISHED_STOPPED",
                output_token_ids=[],
                grammar_terminated=True,
            )
            sink.close()
            assert sink.output_path is not None
            records = [
                json.loads(line)
                for line in sink.output_path.read_text(encoding="utf-8").splitlines()
            ]
            result = verify_audit_records(records)
            self.assertEqual(result["status"], "INCOMPLETE")
            self.assertIn(
                "req-1:invalid_binding_sample_ordinal", result["errors"]
            )


class BindingObservationTrackerTests(unittest.TestCase):
    def test_tracker_pairs_masks_in_request_order(self) -> None:
        tracker = BindingObservationTracker(True)
        tracker.start_request("req-1")
        self.assertEqual(tracker.register_mask("req-1", True), 0)
        self.assertEqual(tracker.register_mask("req-1", False), 1)
        self.assertEqual(tracker.consume_observation("req-1"), (0, True))
        self.assertEqual(tracker.consume_observation("req-1"), (1, False))
        self.assertEqual(tracker.finish_request("req-1"), 0)

    def test_tracker_reports_pending_masks_at_request_end(self) -> None:
        tracker = BindingObservationTracker(True)
        tracker.start_request("req-1")
        tracker.register_mask("req-1", True)
        self.assertEqual(tracker.finish_request("req-1"), 1)

    def test_tracker_rejects_an_observation_without_a_mask(self) -> None:
        tracker = BindingObservationTracker(True)
        tracker.start_request("req-1")
        with self.assertRaisesRegex(
            StructuredOutputAuditError,
            "binding_observation_without_pending_mask",
        ):
            tracker.consume_observation("req-1")


class AuditContextTests(unittest.TestCase):
    def valid_environment(self) -> dict[str, str]:
        return {
            "VLLM_STRUCTURED_OUTPUT_BINDING_REQUIRED": "true",
            "VLLM_STRUCTURED_OUTPUT_EXPERIMENT_ID": "atlas-uga-q1",
            "VLLM_STRUCTURED_OUTPUT_RUNTIME_FINGERPRINT_SHA256": "a" * 64,
            "VLLM_STRUCTURED_OUTPUT_PROTOCOL_SHA256": "b" * 64,
            "VLLM_STRUCTURED_OUTPUT_ASSET_MANIFEST_SHA256": "c" * 64,
        }

    def test_binding_context_is_complete(self) -> None:
        with patch.dict("os.environ", self.valid_environment(), clear=True):
            context = structured_output_audit_context()
        self.assertEqual(context["experiment_id"], "atlas-uga-q1")
        self.assertEqual(context["runtime_fingerprint_sha256"], "a" * 64)

    def test_binding_context_rejects_missing_hash(self) -> None:
        environment = self.valid_environment()
        environment.pop("VLLM_STRUCTURED_OUTPUT_PROTOCOL_SHA256")
        with patch.dict(
            "os.environ", environment, clear=True
        ), self.assertRaisesRegex(
            StructuredOutputAuditError,
            "invalid_audit_context_hash:protocol_sha256",
        ):
            structured_output_audit_context()


def _manager_importable() -> bool:
    try:
        from vllm.v1.structured_output import (  # noqa: F401
            StructuredOutputManager,
        )
    except Exception:
        return False
    return True


@unittest.skipUnless(
    _manager_importable(),
    "requires a full vllm import; runs on the deployment host",
)
class EngineSpeculativeGuardTests(unittest.TestCase):
    """The engine must refuse binding under speculative decoding, cheaply.

    The refusal has to happen before the audit sink is constructed. Building
    the sink creates the audit directory and starts a daemon writer thread, and
    the raise leaves no handle through which that thread could be closed, so a
    late refusal would leak one writer per rejected construction.
    """

    def environment(self, audit_dir: Path) -> dict[str, str]:
        return {
            "VLLM_STRUCTURED_OUTPUT_BINDING_REQUIRED": "true",
            "VLLM_STRUCTURED_OUTPUT_AUDIT_REQUIRED": "true",
            "VLLM_STRUCTURED_OUTPUT_AUDIT_DIR": str(audit_dir),
            "VLLM_STRUCTURED_OUTPUT_EXPERIMENT_ID": "atlas-uga-guard-test",
            "VLLM_STRUCTURED_OUTPUT_RUNTIME_FINGERPRINT_SHA256": "0" * 64,
            "VLLM_STRUCTURED_OUTPUT_PROTOCOL_SHA256": "0" * 64,
            "VLLM_STRUCTURED_OUTPUT_ASSET_MANIFEST_SHA256": "0" * 64,
        }

    def test_rejection_allocates_no_audit_resources(self) -> None:
        import threading

        from vllm.v1.structured_output import StructuredOutputManager

        class SpeculativeConfigStub:
            num_speculative_tokens = 1

        with tempfile.TemporaryDirectory() as parent:
            audit_dir = Path(parent) / "audit"
            threads_before = threading.active_count()
            with patch.dict(
                "os.environ", self.environment(audit_dir), clear=False
            ):
                with self.assertRaises(StructuredOutputAuditError) as caught:
                    StructuredOutputManager(SpeculativeConfigStub())
            self.assertEqual(
                str(caught.exception),
                "binding_requires_speculative_decoding_disabled",
            )
            self.assertFalse(
                audit_dir.exists(),
                "rejection path created an audit directory",
            )
            self.assertEqual(
                threading.active_count(),
                threads_before,
                "rejection path started a writer thread",
            )


def _sampling_params_importable() -> bool:
    try:
        import vllm.sampling_params  # noqa: F401
    except Exception:
        return False
    return True


@unittest.skipUnless(
    _sampling_params_importable(),
    "requires a full vllm import; runs on the deployment host",
)
class SpeculativeDecodeGuardTests(unittest.TestCase):
    """A binding request must be refused when a speculative config is present.

    Binding reads the pre-mask argmax of a decode step. Under speculative
    decoding that step may be a proposal that is later rejected, and this
    overlay establishes no proposed-to-accepted mapping, so the observation
    could not be attributed to an emitted token.
    """

    def build(self, *, binding: bool):
        from vllm.sampling_params import SamplingParams, StructuredOutputsParams

        return SamplingParams(
            temperature=0.0,
            structured_outputs=StructuredOutputsParams(
                json_object=True,
                atlas_audit_binding=binding,
                atlas_audit_request_id="external-1" if binding else None,
            ),
        )

    def test_binding_is_refused_under_speculative_decoding(self) -> None:
        params = self.build(binding=True)
        with self.assertRaisesRegex(
            ValueError, "atlas_audit_binding is not supported"
        ):
            params._validate_spec_decode(object())

    def test_binding_is_allowed_without_speculative_decoding(self) -> None:
        params = self.build(binding=True)
        self.assertIsNone(params._validate_spec_decode(None))

    def test_non_binding_request_is_unaffected(self) -> None:
        params = self.build(binding=False)
        self.assertIsNone(params._validate_spec_decode(object()))


@unittest.skipUnless(
    _sampling_params_importable(),
    "requires a full vllm import; runs on the deployment host",
)
class StructuredOutputTerminationDetokenizationTests(unittest.TestCase):
    def test_grammar_completion_keeps_the_final_payload_token(self) -> None:
        from vllm.v1.engine import FinishReason
        from vllm.v1.engine.output_processor import (
            should_exclude_stop_token_from_output,
        )
        from vllm.v1.structured_output import (
            STRUCTURED_OUTPUT_TERMINATED_STOP_REASON,
        )

        self.assertFalse(
            should_exclude_stop_token_from_output(
                FinishReason.STOP,
                STRUCTURED_OUTPUT_TERMINATED_STOP_REASON,
            )
        )

    def test_eos_and_stop_tokens_keep_upstream_exclusion_behavior(self) -> None:
        from vllm.v1.engine import FinishReason
        from vllm.v1.engine.output_processor import (
            should_exclude_stop_token_from_output,
        )

        self.assertTrue(
            should_exclude_stop_token_from_output(FinishReason.STOP, None)
        )
        self.assertTrue(
            should_exclude_stop_token_from_output(FinishReason.STOP, 248046)
        )
        self.assertFalse(
            should_exclude_stop_token_from_output(FinishReason.LENGTH, None)
        )


if __name__ == "__main__":
    unittest.main()
