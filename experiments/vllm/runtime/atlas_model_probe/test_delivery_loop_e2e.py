"""The whole delivery loop, not each end of it separately.

The previous suites verified module contracts and all passed while the loop was
broken in two places at once: the client wrote a transition ledger nothing read,
and the classifier read `exception_type`/`http_status` off a child summary that
never carries them. Every failure therefore fell through to the text fallback
that the evidence ordering exists to avoid, and no unit test could see it
because each end was correct on its own.

These tests drive the real client writer and the real classifier across a real
run directory.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(r"E:\git projects\AI_XmlGenerator")))

import delivery_classification as dc
from run_asw_v3_experiment import (
    _classify_failed_attempt,
    _last_call_evidence,
    _read_transition_ledger,
)
from src.llm_generation.llm.openai_client import OpenAIClient


class _Writer:
    """The real ledger writer, without constructing a network client."""

    def __init__(self, run_root: Path, phase: str):
        self.config = SimpleNamespace(
            model_name="gpt-5.6-luna", request_timeout_seconds=180.0
        )
        self.provider_endpoint_sha256 = "f5a9" + "0" * 60
        self.response_audit: list[dict] = []
        self.default_max_retries = 1
        self.pipeline_phase = phase
        os.environ["ATLAS_PROVIDER_TRANSITION_LEDGER_PATH"] = str(
            run_root / "provider_call_transitions.jsonl"
        )

    begin = OpenAIClient._begin_provider_call
    persist = OpenAIClient._persist_transition
    evidence = staticmethod(OpenAIClient._transport_evidence)


class DeliveryLoopTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.run_root = Path(self._tmp.name)
        self._previous = os.environ.get("ATLAS_PROVIDER_TRANSITION_LEDGER_PATH")
        self.addCleanup(self._restore)

    def _restore(self):
        if self._previous is None:
            os.environ.pop("ATLAS_PROVIDER_TRANSITION_LEDGER_PATH", None)
        else:
            os.environ["ATLAS_PROVIDER_TRANSITION_LEDGER_PATH"] = self._previous

    def test_a_crash_before_dispatch_reaches_the_classifier_as_transport(self):
        writer = _Writer(self.run_root, "round1")
        writer.begin()
        writer.persist("PRE_DISPATCH", dispatch_started=False)
        # process dies before the socket is used

        classified = _classify_failed_attempt(
            "", "", {"final_status": "failure"},
            timed_out=False, run_root=self.run_root,
        )
        self.assertEqual(
            dc.INFRASTRUCTURE_TRANSPORT_FAILURE, classified["completion_kind"]
        )
        self.assertEqual(
            dc.DEFINITELY_NOT_DISPATCHED, classified["delivery_state"]
        )
        self.assertTrue(classified["replacement_eligible"])

    def test_a_typed_exception_reaches_the_classifier_without_text(self):
        """The evidence path that was disconnected end to end."""
        writer = _Writer(self.run_root, "round2")
        writer.begin()
        writer.persist("PRE_DISPATCH", dispatch_started=False)
        writer.persist("DISPATCH_STARTED", dispatch_started=True,
                       request_acceptance_known=False)
        writer.persist("CALL_FAILED", dispatch_started=True,
                       **writer.evidence(TimeoutError("gone")))

        classified = _classify_failed_attempt(
            "", "", {"final_status": "failure"},
            timed_out=False, run_root=self.run_root,
        )
        self.assertEqual(
            dc.AMBIGUOUS_PROVIDER_DELIVERY, classified["completion_kind"]
        )
        self.assertEqual("UNKNOWN", classified["billing_state"])
        self.assertFalse(classified["replacement_eligible"])

    def test_the_stages_of_one_call_share_one_identity(self):
        writer = _Writer(self.run_root, "round1")
        call_id = writer.begin()
        for stage in ("PRE_DISPATCH", "DISPATCH_STARTED", "RESPONSE_RECEIVED"):
            writer.persist(stage)
        writer.response_audit.append({"call_index": 1})
        writer.persist("LOCAL_AUDIT_PERSISTED")

        rows = _read_transition_ledger(self.run_root)
        self.assertEqual(4, len(rows))
        self.assertEqual({call_id}, {row["provider_call_id"] for row in rows})
        # The old counter produced 1, 1, 1, 2 for exactly this sequence.
        self.assertEqual({1}, {row["logical_call_index"] for row in rows})

    def test_two_phases_sharing_a_ledger_stay_distinguishable(self):
        """Round 1 and Round 2 use separate clients and one ledger."""
        first = _Writer(self.run_root, "round1")
        first.begin()
        first.persist("PRE_DISPATCH")
        first.persist("RESPONSE_RECEIVED", response_id="resp_a")

        second = _Writer(self.run_root, "round2")
        second.begin()
        second.persist("PRE_DISPATCH")
        second.persist("CALL_FAILED", **second.evidence(TimeoutError("x")))

        rows = _read_transition_ledger(self.run_root)
        identities = {row["provider_call_id"] for row in rows}
        self.assertEqual(2, len(identities))
        self.assertEqual({"round1", "round2"},
                         {row["pipeline_phase"] for row in rows})
        # Delivery is decided from the call that ended the run.
        evidence = _last_call_evidence(rows)
        self.assertEqual("round2", evidence["pipeline_phase"])
        self.assertEqual("TimeoutError", evidence["exception_type"])

    def test_round1_audit_cannot_be_attached_to_round2_timeout(self):
        """A prior delivered call must not contaminate the model denominator."""
        first = _Writer(self.run_root, "round1")
        first_id = first.begin()
        first.persist("PRE_DISPATCH", dispatch_started=False)
        first.persist("DISPATCH_STARTED", dispatch_started=True)
        first.persist(
            "RESPONSE_RECEIVED", dispatch_started=True,
            request_acceptance_known=True, response_headers_received=True,
            response_id="resp_round1",
        )
        (self.run_root / "provider_calls.jsonl").write_text(
            json.dumps({
                "credentials_included": False,
                "provider_call_id": first_id,
                "pipeline_phase": "round1",
                "logical_call_index": 1,
                "response_id": "resp_round1",
                "usage": {"total_tokens": 10},
            }) + chr(10),
            encoding="utf-8",
        )

        second = _Writer(self.run_root, "round2.component")
        second.begin()
        second.persist("PRE_DISPATCH", dispatch_started=False)
        second.persist(
            "DISPATCH_STARTED", dispatch_started=True,
            request_acceptance_known=False,
        )
        second.persist(
            "CALL_FAILED", dispatch_started=True,
            **second.evidence(TimeoutError("Round 2 timed out")),
        )

        classified = _classify_failed_attempt(
            "", "", {"final_status": "failure"},
            timed_out=False, run_root=self.run_root,
        )
        self.assertEqual(
            dc.AMBIGUOUS_PROVIDER_DELIVERY, classified["completion_kind"]
        )
        self.assertEqual("round2.component", classified["pipeline_phase"])
        self.assertNotEqual("CONFIRMED", classified["billing_state"])

    def test_429_classifies_the_slot_then_halts_the_later_queue(self):
        writer = _Writer(self.run_root, "round2.component")
        writer.begin()
        writer.persist("PRE_DISPATCH", dispatch_started=False)
        writer.persist("DISPATCH_STARTED", dispatch_started=True)
        error = RuntimeError("rate limited")
        error.status_code = 429
        writer.persist("CALL_FAILED", dispatch_started=True,
                       **writer.evidence(error))

        classified = _classify_failed_attempt(
            "", "Error code: 429", {"final_status": "failure"},
            timed_out=False, run_root=self.run_root,
        )
        self.assertTrue(classified["terminal"])
        self.assertEqual(
            dc.AMBIGUOUS_PROVIDER_DELIVERY, classified["completion_kind"]
        )
        self.assertEqual("PROVIDER_RATE_LIMIT", classified["queue_halt_reason"])
        self.assertEqual("http_status", classified["evidence_basis"])

    def test_a_delivered_response_makes_the_failure_a_model_outcome(self):
        writer = _Writer(self.run_root, "round2")
        writer.begin()
        writer.persist("PRE_DISPATCH", dispatch_started=False)
        writer.persist("RESPONSE_RECEIVED", dispatch_started=True,
                       request_acceptance_known=True,
                       response_headers_received=True, response_id="resp_z")
        (self.run_root / "provider_calls.jsonl").write_text(
            json.dumps({
                "credentials_included": False,
                "response_id": "resp_z",
                "usage": {"input_tokens": 5, "output_tokens": 5,
                          "total_tokens": 10},
            }) + chr(10),
            encoding="utf-8",
        )

        classified = _classify_failed_attempt(
            "", "selection path conflict", {"final_status": "failure"},
            timed_out=False, run_root=self.run_root,
        )
        self.assertEqual(
            dc.MODEL_OR_SCHEMA_GENERATION_FAILURE, classified["completion_kind"]
        )

    def test_a_torn_final_line_does_not_lose_the_readable_stages(self):
        writer = _Writer(self.run_root, "round1")
        writer.begin()
        writer.persist("PRE_DISPATCH", dispatch_started=False)
        path = self.run_root / "provider_call_transitions.jsonl"
        with path.open("a", encoding="utf-8") as handle:
            handle.write('{"stage": "DISPATCH_ST')

        rows = _read_transition_ledger(self.run_root)
        self.assertEqual(1, len(rows))
        self.assertEqual("PRE_DISPATCH", rows[0]["stage"])

    def test_a_pipeline_timeout_is_ambiguous_and_not_retried(self):
        """The branch that still repeated a slot the provider may have served."""
        classified = _classify_failed_attempt(
            "", "", {}, timed_out=True, run_root=self.run_root,
        )
        self.assertEqual(
            dc.AMBIGUOUS_PROVIDER_DELIVERY, classified["completion_kind"]
        )
        self.assertTrue(classified["terminal"])
        self.assertFalse(classified["retryable"])
        self.assertFalse(classified["replacement_eligible"])


if __name__ == "__main__":
    unittest.main()
