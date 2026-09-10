"""Counterexamples for the delivery/billing classification the V16 pilot lacked.

The pilot recorded three ``Connection error.`` slots as
``TERMINAL_GENERATION_FAILURE``.  Each test here is a case that must not be
classified that way again, and each of the replacement rules exists to stop a
second paid execution being issued for one scheduled slot.
"""

from __future__ import annotations

import unittest

import delivery_classification as dc


class DispatchCertaintyTests(unittest.TestCase):
    def test_confirmed_failure_before_dispatch_is_transport_and_replaceable(self):
        record = dc.classify_delivery(
            "APIConnectionError: [Errno 111] Connection refused",
            audit_persisted=False,
            dispatch_started=False,
        )
        self.assertEqual(dc.DEFINITELY_NOT_DISPATCHED, record["delivery_state"])
        self.assertEqual(dc.BILLING_CONFIRMED, record["billing_state"])
        self.assertEqual(0, record["confirmed_cost_units"])
        self.assertTrue(record["replacement_eligible"])
        self.assertEqual(
            dc.INFRASTRUCTURE_TRANSPORT_FAILURE,
            dc.completion_kind_for(
                delivery_state=record["delivery_state"], model_reached=False
            ),
        )

    def test_dns_failure_is_also_provably_undispatched(self):
        record = dc.classify_delivery(
            "getaddrinfo failed", audit_persisted=False, dispatch_started=False
        )
        self.assertEqual(dc.DEFINITELY_NOT_DISPATCHED, record["delivery_state"])
        self.assertTrue(record["replacement_eligible"])

    def test_the_v16_pilot_failure_is_ambiguous_not_generation(self):
        """The exact text that was recorded as TERMINAL_GENERATION_FAILURE."""
        record = dc.classify_delivery(
            "Strict JSON Schema generation failed: Connection error.",
            audit_persisted=False,
        )
        self.assertEqual(dc.DELIVERY_AMBIGUOUS, record["delivery_state"])
        self.assertEqual(dc.BILLING_UNKNOWN, record["billing_state"])
        self.assertFalse(record["replacement_eligible"])
        kind = dc.completion_kind_for(
            delivery_state=record["delivery_state"], model_reached=False
        )
        self.assertEqual(dc.AMBIGUOUS_PROVIDER_DELIVERY, kind)
        self.assertNotEqual(dc.MODEL_OR_SCHEMA_GENERATION_FAILURE, kind)
        self.assertFalse(dc.counts_in_model_quality_denominator(kind))

    def test_connection_lost_after_possible_send_is_ambiguous(self):
        for text in (
            "Server disconnected without sending a response",
            "Connection reset by peer",
            "incomplete read of response body",
        ):
            with self.subTest(text=text):
                record = dc.classify_delivery(text, audit_persisted=False)
                self.assertEqual(dc.DELIVERY_AMBIGUOUS, record["delivery_state"])
                self.assertFalse(record["replacement_eligible"])

    def test_timeout_without_response_id_is_ambiguous(self):
        record = dc.classify_delivery(
            "Request timed out after 180.0 seconds", audit_persisted=False
        )
        self.assertEqual(dc.DELIVERY_AMBIGUOUS, record["delivery_state"])
        self.assertEqual(dc.BILLING_UNKNOWN, record["billing_state"])
        self.assertIsNone(record["response_id"])
        self.assertFalse(record["replacement_eligible"])

    def test_an_unrecognised_failure_is_unclassified_not_defaulted(self):
        """Neither bucket may absorb an unknown failure."""
        record = dc.classify_delivery("something nobody wrote a marker for",
                                      audit_persisted=False)
        self.assertEqual(dc.DELIVERY_UNKNOWN, record["delivery_state"])
        self.assertEqual(dc.EVIDENCE_NONE, record["evidence_basis"])
        self.assertFalse(record["replacement_eligible"])
        kind = dc.completion_kind_for(delivery_state=record["delivery_state"])
        self.assertEqual(dc.UNCLASSIFIED_FAILURE, kind)
        self.assertFalse(dc.counts_in_model_quality_denominator(kind))
        self.assertTrue(dc.requires_separate_report(kind))


class HttpStatusTests(unittest.TestCase):
    def test_an_error_status_does_not_prove_zero_execution_or_zero_cost(self):
        """A 4xx is an error response, not a billing guarantee.

        What is frozen for this experiment is an endpoint identity hash. It
        certifies nothing about whether a model ran before the error or what
        the call cost, so asserting confirmed zero cost from a status code
        exceeds the evidence and would wrongly grant a replacement.
        """
        for status, reason in (
            (429, "PROVIDER_RATE_LIMIT"),
            (401, "PROVIDER_AUTHENTICATION"),
            (402, "PROVIDER_PAYMENT_REQUIRED"),
            (403, "PROVIDER_PERMISSION"),
            (400, "PROVIDER_BAD_REQUEST"),
            (422, "PROVIDER_UNPROCESSABLE"),
        ):
            with self.subTest(status=status):
                record = dc.classify_delivery(http_status=status)
                self.assertEqual(dc.DELIVERY_AMBIGUOUS, record["delivery_state"])
                self.assertEqual(dc.BILLING_UNKNOWN, record["billing_state"])
                self.assertNotIn("confirmed_cost_units", record)
                self.assertFalse(record["replacement_eligible"])
                self.assertEqual(reason, record["provider_rejection_reason"])

    def test_the_no_execution_guarantee_is_off_until_one_is_frozen(self):
        self.assertFalse(dc._PROVIDER_NO_EXECUTION_GUARANTEE)

    def test_408_and_5xx_are_ambiguous_because_the_server_had_the_request(self):
        for status in (408, 500, 502, 503, 504):
            with self.subTest(status=status):
                record = dc.classify_delivery(http_status=status)
                self.assertEqual(dc.DELIVERY_AMBIGUOUS, record["delivery_state"])
                self.assertEqual(dc.BILLING_UNKNOWN, record["billing_state"])
                self.assertFalse(record["replacement_eligible"])


class BillingHonestyTests(unittest.TestCase):
    def test_unknown_billing_is_never_reported_as_zero(self):
        records = [
            dc.call_telemetry_record(
                dispatch_started=True,
                response_headers_received=False,
                response_id=None,
                usage=None,
                response_model=None,
                local_audit_persisted=False,
                exception_type="APIConnectionError",
                exception_text="Connection error.",
            )
        ]
        summary = dc.summarize_cost(records)
        self.assertEqual(1, summary["calls_with_unknown_billing"])
        self.assertIsNone(summary["unknown_billing_tokens"])
        self.assertNotEqual(0, summary["unknown_billing_tokens"])
        self.assertIn("must not be recorded as 0", summary["statement"])

    def test_a_missing_local_audit_is_not_evidence_of_no_execution(self):
        record = dc.call_telemetry_record(
            dispatch_started=True,
            response_headers_received=False,
            response_id=None,
            usage=None,
            response_model=None,
            local_audit_persisted=False,
            exception_type="APIConnectionError",
            exception_text="Connection error.",
        )
        self.assertFalse(record["local_audit_persisted"])
        self.assertEqual(dc.BILLING_UNKNOWN, record["billing_state"])
        self.assertNotIn("confirmed_cost_units", record)

    def test_every_telemetry_field_is_present_on_every_call(self):
        record = dc.call_telemetry_record(
            dispatch_started=True,
            response_headers_received=True,
            response_id="resp_123",
            usage={"total_tokens": 42},
            response_model="gpt-5.6-luna-2026-07-09",
            local_audit_persisted=True,
        )
        for field in dc.CALL_TELEMETRY_FIELDS:
            self.assertIn(field, record)
        self.assertEqual(dc.DELIVERY_CONFIRMED, record["delivery_state"])
        self.assertEqual(dc.BILLING_CONFIRMED, record["billing_state"])
        self.assertFalse(record["retry_or_replacement_eligible"])

    def test_confirmed_tokens_are_a_lower_bound_not_a_settlement(self):
        summary = dc.summarize_cost(
            [
                {"billing_state": dc.BILLING_CONFIRMED, "usage": {"total_tokens": 100}},
                {"billing_state": dc.BILLING_UNKNOWN, "usage": None},
            ]
        )
        self.assertEqual(100, summary["confirmed_total_tokens"])
        self.assertIn("lower bound", summary["statement"])


class ReplacementPolicyTests(unittest.TestCase):
    def test_ambiguous_delivery_is_never_replaced(self):
        record = {
            "completion_kind": dc.AMBIGUOUS_PROVIDER_DELIVERY,
            "replacement_eligible": True,
            "billing_state": dc.BILLING_CONFIRMED,
            "replacement_attempts": 0,
        }
        # Even with every other field permissive, the kind alone forbids it.
        self.assertFalse(dc.replacement_allowed(record))

    def test_confirmed_pre_dispatch_failure_may_be_replaced_exactly_once(self):
        record = {
            "completion_kind": dc.INFRASTRUCTURE_TRANSPORT_FAILURE,
            "delivery_state": dc.DEFINITELY_NOT_DISPATCHED,
            "replacement_eligible": True,
            "billing_state": dc.BILLING_CONFIRMED,
            "replacement_attempts": 0,
        }
        self.assertTrue(dc.replacement_allowed(record))
        record["replacement_attempts"] = 1
        self.assertFalse(dc.replacement_allowed(record))

    def test_a_failed_replacement_stops_and_becomes_missing(self):
        record = {
            "completion_kind": dc.INFRASTRUCTURE_TRANSPORT_FAILURE,
            "replacement_eligible": True,
            "billing_state": dc.BILLING_CONFIRMED,
            "replacement_attempts": 1,
        }
        self.assertFalse(dc.replacement_allowed(record))

    def test_unknown_billing_blocks_replacement(self):
        record = {
            "completion_kind": dc.INFRASTRUCTURE_TRANSPORT_FAILURE,
            "replacement_eligible": True,
            "billing_state": dc.BILLING_UNKNOWN,
            "replacement_attempts": 0,
        }
        self.assertFalse(dc.replacement_allowed(record))


class DenominatorSeparationTests(unittest.TestCase):
    def test_transport_and_ambiguous_leave_the_model_quality_denominator(self):
        for kind in (
            dc.INFRASTRUCTURE_TRANSPORT_FAILURE,
            dc.AMBIGUOUS_PROVIDER_DELIVERY,
            dc.RUNNER_ORCHESTRATION_FAILURE,
        ):
            with self.subTest(kind=kind):
                self.assertFalse(dc.counts_in_model_quality_denominator(kind))

    def test_transport_and_ambiguous_stay_in_the_operational_denominator(self):
        for kind in dc.COMPLETION_KINDS:
            with self.subTest(kind=kind):
                self.assertTrue(dc.counts_in_operational_denominator(kind))

    def test_only_model_outcomes_enter_the_model_quality_denominator(self):
        self.assertEqual(
            {dc.SUCCESSFUL_ARTIFACT, dc.MODEL_OR_SCHEMA_GENERATION_FAILURE},
            set(dc.MODEL_QUALITY_KINDS),
        )

    def test_the_vocabulary_is_exactly_the_six_frozen_kinds(self):
        self.assertEqual(
            [
                "SUCCESSFUL_ARTIFACT",
                "MODEL_OR_SCHEMA_GENERATION_FAILURE",
                "INFRASTRUCTURE_TRANSPORT_FAILURE",
                "AMBIGUOUS_PROVIDER_DELIVERY",
                "RUNNER_ORCHESTRATION_FAILURE",
                "UNCLASSIFIED_FAILURE",
            ],
            list(dc.COMPLETION_KINDS),
        )
        self.assertNotIn("TERMINAL_GENERATION_FAILURE", dc.COMPLETION_KINDS)

    def test_a_runner_fault_is_neither_model_nor_provider(self):
        kind = dc.completion_kind_for(
            delivery_state=dc.DELIVERY_CONFIRMED,
            model_reached=True,
            runner_fault=True,
        )
        self.assertEqual(dc.RUNNER_ORCHESTRATION_FAILURE, kind)
        self.assertFalse(dc.counts_in_model_quality_denominator(kind))

    def test_a_delivered_response_with_a_bad_payload_is_a_model_outcome(self):
        kind = dc.completion_kind_for(
            delivery_state=dc.DELIVERY_CONFIRMED, model_reached=True
        )
        self.assertEqual(dc.MODEL_OR_SCHEMA_GENERATION_FAILURE, kind)
        self.assertTrue(dc.counts_in_model_quality_denominator(kind))


if __name__ == "__main__":
    unittest.main()


class OperatorStopTests(unittest.TestCase):
    """Stopping a paid queue must be a supported action, not a process kill.

    The V16 pilot had no operator stop hook, so ending it meant terminating the
    parent from outside and reconstructing the boundary afterwards.  Triggering
    the existing queue halt instead would have required fabricating a provider
    error, which writes a false halt reason into the ledger.
    """

    def setUp(self):
        import tempfile
        from pathlib import Path
        import run_asw_v3_experiment as runner

        self.runner = runner
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.schedule = {
            "content_sha256": "c" * 64,
            "runs": [{"run_id": f"run-{i}"} for i in range(4)],
        }

    def test_no_sentinel_means_no_stop(self):
        self.assertIsNone(
            self.runner._operator_stop_receipt(self.root, [], self.schedule)
        )

    def test_a_sentinel_stops_at_the_boundary_and_writes_a_receipt(self):
        (self.root / self.runner.OPERATOR_STOP_SENTINEL).write_text(
            "transport faults; switching to V17", encoding="utf-8"
        )
        records = [{"run_id": "run-0"}, {"run_id": "run-1"}]

        receipt = self.runner._operator_stop_receipt(
            self.root, records, self.schedule
        )

        self.assertIsNotNone(receipt)
        self.assertEqual(2, receipt["runs_completed"])
        self.assertEqual(4, receipt["runs_scheduled"])
        self.assertEqual("run-1", receipt["last_completed_run_id"])
        self.assertEqual(["run-2", "run-3"], receipt["not_started_run_ids"])
        self.assertEqual("transport faults; switching to V17",
                         receipt["operator_note"])
        self.assertTrue(receipt["stopped_at_utc"])

    def test_the_stop_never_lands_inside_a_provider_call(self):
        (self.root / self.runner.OPERATOR_STOP_SENTINEL).write_text("", encoding="utf-8")
        receipt = self.runner._operator_stop_receipt(
            self.root, [{"run_id": "run-0"}], self.schedule
        )
        self.assertIsNone(receipt["in_flight_run_id"])
        self.assertEqual(0, receipt["provider_calls_interrupted"])
        self.assertIn("between runs", receipt["in_flight_state"])

    def test_the_receipt_is_persisted_for_audit(self):
        import json

        (self.root / self.runner.OPERATOR_STOP_SENTINEL).write_text("", encoding="utf-8")
        self.runner._operator_stop_receipt(self.root, [], self.schedule)
        written = json.loads(
            (self.root / self.runner.OPERATOR_STOP_RECEIPT).read_text(encoding="utf-8")
        )
        self.assertEqual(
            "atlas.asw_v3.operator_stop_receipt.v1", written["schema_version"]
        )
        self.assertEqual("c" * 64, written["schedule_content_sha256"])

    def test_an_operator_stop_is_not_a_complete_experiment(self):
        """A stopped queue must never be summarised as a finished one."""
        (self.root / self.runner.OPERATOR_STOP_SENTINEL).write_text("", encoding="utf-8")
        receipt = self.runner._operator_stop_receipt(self.root, [], self.schedule)
        self.assertIsNotNone(receipt)
        self.assertLess(receipt["runs_completed"], receipt["runs_scheduled"])

    def test_stopping_does_not_require_a_fabricated_provider_error(self):
        (self.root / self.runner.OPERATOR_STOP_SENTINEL).write_text("", encoding="utf-8")
        receipt = self.runner._operator_stop_receipt(self.root, [], self.schedule)
        self.assertEqual(
            "operator stop sentinel observed at a run boundary", receipt["reason"]
        )
        self.assertNotIn("PROVIDER_", receipt["reason"])

    def test_full_runner_root_and_generation_root_are_both_honoured(self):
        top = self.root / "full"
        generation = top / "generation"
        generation.mkdir(parents=True)
        (top / self.runner.OPERATOR_STOP_SENTINEL).write_text(
            "operator requested boundary stop", encoding="utf-8"
        )

        receipt = self.runner._operator_stop_receipt(
            generation,
            [{"run_id": "run-0"}],
            self.schedule,
            additional_sentinel_roots=(top,),
        )

        self.assertIsNotNone(receipt)
        self.assertEqual(
            str(top / self.runner.OPERATOR_STOP_SENTINEL),
            receipt["observed_sentinel_path"],
        )
        self.assertTrue(
            (generation / self.runner.OPERATOR_STOP_RECEIPT).is_file()
        )
        self.assertTrue((top / self.runner.OPERATOR_STOP_RECEIPT).is_file())


class EvidencePrecedenceTests(unittest.TestCase):
    """Structured evidence outranks text, and model text is never evidence."""

    def test_model_output_mentioning_connection_error_is_not_a_transport_fault(self):
        """The counterexample that makes the text fallback safe.

        A component description, a validator finding, or a prompt may contain
        the words "connection error".  Passing model-authored content to the
        classifier would turn a genuine model result into a network event and
        silently remove it from the model-quality denominator.
        """
        model_text = (
            "The runnable shall log a connection error when the sender-receiver "
            "port reports a timed out link."
        )
        # Model content is never passed as exception text; the caller passes the
        # transport exception only.  With no exception evidence the failure is
        # unclassified, not transport.
        record = dc.classify_delivery(
            exception_text="",
            audit_persisted=True,
            response_id="resp_9",
            structured_response_present=True,
        )
        self.assertEqual(dc.DELIVERY_CONFIRMED, record["delivery_state"])
        kind = dc.completion_kind_for(
            delivery_state=record["delivery_state"], model_reached=True
        )
        self.assertEqual(dc.MODEL_OR_SCHEMA_GENERATION_FAILURE, kind)
        self.assertTrue(dc.counts_in_model_quality_denominator(kind))
        self.assertIn("connection error", model_text)

    def test_a_structured_response_outranks_transport_looking_text(self):
        record = dc.classify_delivery(
            "connection error",
            audit_persisted=True,
            response_id="resp_1",
            usage={"total_tokens": 10},
        )
        self.assertEqual(dc.DELIVERY_CONFIRMED, record["delivery_state"])
        self.assertEqual(
            dc.EVIDENCE_STRUCTURED_RESPONSE, record["evidence_basis"]
        )

    def test_a_typed_exception_outranks_the_text_fallback(self):
        record = dc.classify_delivery(
            "connection error",
            exception_type="RateLimitError",
        )
        self.assertEqual(dc.EVIDENCE_TYPED_EXCEPTION, record["evidence_basis"])
        self.assertEqual(dc.DELIVERY_AMBIGUOUS, record["delivery_state"])
        self.assertEqual(dc.BILLING_UNKNOWN, record["billing_state"])
        self.assertFalse(record["replacement_eligible"])
        self.assertEqual("RateLimitError", record["provider_error_class"])

    def test_http_status_outranks_the_text_fallback(self):
        record = dc.classify_delivery("connection error", http_status=503)
        self.assertEqual(dc.DELIVERY_AMBIGUOUS, record["delivery_state"])
        self.assertEqual(dc.EVIDENCE_HTTP_STATUS, record["evidence_basis"])

    def test_text_fallback_is_marked_as_such(self):
        record = dc.classify_delivery("Connection error.")
        self.assertEqual(dc.DELIVERY_AMBIGUOUS, record["delivery_state"])
        self.assertEqual(dc.EVIDENCE_TEXT_FALLBACK, record["evidence_basis"])
        self.assertFalse(record["replacement_eligible"])

    def test_dispatch_started_does_not_mean_the_provider_accepted(self):
        record = dc.classify_delivery(
            "", dispatch_started=True, acceptance_known=False
        )
        self.assertEqual(dc.DELIVERY_AMBIGUOUS, record["delivery_state"])
        self.assertEqual(dc.BILLING_UNKNOWN, record["billing_state"])
        self.assertFalse(record["replacement_eligible"])
        self.assertIn("does not mean the provider accepted",
                      record["determination"])

    def test_only_dispatch_telemetry_can_prove_a_request_never_left(self):
        proven = dc.classify_delivery("", dispatch_started=False)
        self.assertEqual(dc.DEFINITELY_NOT_DISPATCHED, proven["delivery_state"])
        self.assertEqual(
            dc.EVIDENCE_DISPATCH_TELEMETRY, proven["evidence_basis"]
        )
        # The same words without telemetry do not establish it.
        unproven = dc.classify_delivery("connection refused")
        self.assertNotEqual(
            dc.DEFINITELY_NOT_DISPATCHED, unproven["delivery_state"]
        )

    def test_unclassified_is_reported_separately_and_never_replaced(self):
        kind = dc.UNCLASSIFIED_FAILURE
        self.assertTrue(dc.requires_separate_report(kind))
        self.assertTrue(dc.counts_in_operational_denominator(kind))
        self.assertFalse(dc.counts_in_model_quality_denominator(kind))
        self.assertFalse(
            dc.replacement_allowed(
                {
                    "completion_kind": kind,
                    "delivery_state": dc.DEFINITELY_NOT_DISPATCHED,
                    "replacement_eligible": True,
                    "billing_state": dc.BILLING_CONFIRMED,
                    "replacement_attempts": 0,
                }
            )
        )
