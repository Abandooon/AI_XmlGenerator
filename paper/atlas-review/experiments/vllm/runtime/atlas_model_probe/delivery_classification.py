"""Separate what the model did from what the network did, on evidence.

A V16 pilot batch recorded three slots as ``TERMINAL_GENERATION_FAILURE`` when
the actual event was a client-side ``Connection error.`` during Round 1.  The
old classifier matched ``connection reset``/``aborted``/``refused`` but not the
bare ``Connection error.`` the provider SDK raises, so a transport fault fell
through to the scientific-outcome branch and entered the model-quality
denominator.

The correction is not a longer marker list.  A failure has two independent
properties and the old scheme conflated them:

* **what failed** --- the model/schema, the transport, or the runner;
* **what the server may already have done** --- provably nothing, or something
  we cannot observe.

The second property decides whether a replacement run is even permissible.  A
request proven never to have left the client may be replaced once.  A request
that may have reached the server may not: replacing it would issue a second
paid execution for one scheduled slot.

**There is no default bucket.**  Neither "model failure" nor "ambiguous
delivery" may absorb an unrecognised failure: the first repeats the V16 defect,
the second quietly removes real model failures from the denominator.  Anything
without structured evidence is ``UNCLASSIFIED_FAILURE``, reported on its own.

Evidence is consulted in order of reliability: a structured provider response,
then the SDK's typed exception, then HTTP status and headers, then dispatch
telemetry, then the runner stage.  Free-text matching is a compatibility
fallback only, and is never applied to model-authored content --- a component
description containing the words "connection error" is not a network event.
"""

from __future__ import annotations

from typing import Any


# --- completion kinds ------------------------------------------------------

SUCCESSFUL_ARTIFACT = "SUCCESSFUL_ARTIFACT"
MODEL_OR_SCHEMA_GENERATION_FAILURE = "MODEL_OR_SCHEMA_GENERATION_FAILURE"
INFRASTRUCTURE_TRANSPORT_FAILURE = "INFRASTRUCTURE_TRANSPORT_FAILURE"
AMBIGUOUS_PROVIDER_DELIVERY = "AMBIGUOUS_PROVIDER_DELIVERY"
RUNNER_ORCHESTRATION_FAILURE = "RUNNER_ORCHESTRATION_FAILURE"
UNCLASSIFIED_FAILURE = "UNCLASSIFIED_FAILURE"

COMPLETION_KINDS = (
    SUCCESSFUL_ARTIFACT,
    MODEL_OR_SCHEMA_GENERATION_FAILURE,
    INFRASTRUCTURE_TRANSPORT_FAILURE,
    AMBIGUOUS_PROVIDER_DELIVERY,
    RUNNER_ORCHESTRATION_FAILURE,
    UNCLASSIFIED_FAILURE,
)

# Only these describe something the model or the schema did.
MODEL_QUALITY_KINDS = frozenset(
    {SUCCESSFUL_ARTIFACT, MODEL_OR_SCHEMA_GENERATION_FAILURE}
)

# Every scheduled slot, whatever happened to it, is operational evidence.
OPERATIONAL_KINDS = frozenset(COMPLETION_KINDS)

# Kinds that must be reported as their own line rather than folded anywhere.
SEPARATELY_REPORTED_KINDS = frozenset(
    {
        INFRASTRUCTURE_TRANSPORT_FAILURE,
        AMBIGUOUS_PROVIDER_DELIVERY,
        RUNNER_ORCHESTRATION_FAILURE,
        UNCLASSIFIED_FAILURE,
    }
)


# --- delivery and billing --------------------------------------------------

DEFINITELY_NOT_DISPATCHED = "DEFINITELY_NOT_DISPATCHED"
REJECTED_BEFORE_EXECUTION = "CONFIRMED_REJECTED_BEFORE_MODEL_EXECUTION"
DELIVERY_AMBIGUOUS = "AMBIGUOUS"
DELIVERY_CONFIRMED = "CONFIRMED_DELIVERED"
DELIVERY_UNKNOWN = "UNKNOWN"

BILLING_CONFIRMED = "CONFIRMED"
BILLING_UNKNOWN = "UNKNOWN"

EVIDENCE_STRUCTURED_RESPONSE = "structured_provider_response"
EVIDENCE_TYPED_EXCEPTION = "sdk_typed_exception"
EVIDENCE_HTTP_STATUS = "http_status"
EVIDENCE_DISPATCH_TELEMETRY = "dispatch_telemetry"
EVIDENCE_TEXT_FALLBACK = "text_marker_fallback"
EVIDENCE_NONE = "none"


# SDK exception classes, by what their occurrence proves.  A connection or
# timeout error proves only that *we* stopped observing; it says nothing about
# whether the server received or served the request.
_TYPED_EXCEPTIONS = {
    "APIConnectionError": DELIVERY_AMBIGUOUS,
    "APITimeoutError": DELIVERY_AMBIGUOUS,
    "InternalServerError": DELIVERY_AMBIGUOUS,
    "APIResponseValidationError": DELIVERY_CONFIRMED,
    "RateLimitError": REJECTED_BEFORE_EXECUTION,
    "AuthenticationError": REJECTED_BEFORE_EXECUTION,
    "PermissionDeniedError": REJECTED_BEFORE_EXECUTION,
    "BadRequestError": REJECTED_BEFORE_EXECUTION,
    "NotFoundError": REJECTED_BEFORE_EXECUTION,
    "UnprocessableEntityError": REJECTED_BEFORE_EXECUTION,
}

# No provider execution/billing contract is frozen for this experiment.  What is
# frozen is an endpoint identity hash, which says nothing about whether a 4xx
# was produced before or after any model work, or about what it cost.  Until a
# provider guarantee is frozen and verified, an error response is treated as
# ambiguous delivery with unknown billing and grants no replacement.  Flipping
# this constant without also freezing that guarantee would reintroduce a
# zero-cost claim the evidence does not support.
PROVIDER_NO_EXECUTION_GUARANTEE = False
# Backward-compatible internal spelling retained for the classifier; the
# public constant is what the frozen policy artifact records and tests.
_PROVIDER_NO_EXECUTION_GUARANTEE = PROVIDER_NO_EXECUTION_GUARANTEE

# Statuses that a frozen provider guarantee could, in principle, certify as
# pre-execution rejections.  Retained for the reason code only.
_REJECTED_STATUSES = {400: "PROVIDER_BAD_REQUEST", 401: "PROVIDER_AUTHENTICATION",
                      402: "PROVIDER_PAYMENT_REQUIRED", 403: "PROVIDER_PERMISSION",
                      404: "PROVIDER_NOT_FOUND", 422: "PROVIDER_UNPROCESSABLE",
                      429: "PROVIDER_RATE_LIMIT"}

# A server that answers with these had the request; execution is unobservable.
_AMBIGUOUS_STATUSES = {408, 409, 425, 500, 502, 503, 504}

# Compatibility only, and only ever applied to exception text.
_TEXT_AMBIGUOUS_MARKERS = (
    "connection error",
    "connection reset",
    "connection aborted",
    "server disconnected",
    "remote end closed connection",
    "incomplete read",
    "request timed out",
    "read timeout",
    "connect timeout",
)


def _result(
    delivery_state: str,
    billing_state: str,
    *,
    evidence: str,
    determination: str,
    replacement_eligible: bool,
    response_id: str | None = None,
    usage: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    record = {
        "delivery_state": delivery_state,
        "billing_state": billing_state,
        "evidence_basis": evidence,
        "replacement_eligible": replacement_eligible,
        "response_id": response_id,
        "usage": usage,
        "determination": determination,
    }
    if extra:
        record.update(extra)
    return record


def classify_delivery(
    exception_text: str = "",
    *,
    audit_persisted: bool = False,
    response_id: str | None = None,
    usage: dict[str, Any] | None = None,
    exception_type: str | None = None,
    http_status: int | None = None,
    response_headers_received: bool = False,
    structured_response_present: bool = False,
    dispatch_started: bool | None = None,
    acceptance_known: bool | None = None,
    runner_stage: str | None = None,
) -> dict[str, Any]:
    """Decide what the server may already have done, from the best evidence.

    ``exception_text`` is the transport exception's own text.  Model-authored
    content must never be passed here: the text fallback would then classify a
    component description mentioning a connection error as a network event.
    """
    # 1. A structured provider response settles it.
    if structured_response_present or (audit_persisted and response_id):
        return _result(
            DELIVERY_CONFIRMED, BILLING_CONFIRMED,
            evidence=EVIDENCE_STRUCTURED_RESPONSE,
            determination="a structured provider response was received and recorded",
            replacement_eligible=False,
            response_id=response_id, usage=usage,
        )

    # 2. The SDK's own exception class.
    if exception_type:
        state = _TYPED_EXCEPTIONS.get(str(exception_type).split(".")[-1])
        if state == REJECTED_BEFORE_EXECUTION:
            # An error response proves an error response was received.  It does
            # not prove the provider ran no model and charged nothing: that is
            # a provider execution/billing contract, and what is frozen here is
            # an endpoint identity hash, not such a guarantee.  Without one,
            # billing stays UNKNOWN and no replacement is granted.
            return _result(
                DELIVERY_AMBIGUOUS
                if not _PROVIDER_NO_EXECUTION_GUARANTEE
                else REJECTED_BEFORE_EXECUTION,
                BILLING_CONFIRMED
                if _PROVIDER_NO_EXECUTION_GUARANTEE
                else BILLING_UNKNOWN,
                evidence=EVIDENCE_TYPED_EXCEPTION,
                determination=(
                    f"{exception_type} indicates the provider returned an error. "
                    "No frozen provider guarantee establishes that no model ran "
                    "or that nothing was billed, so delivery stays ambiguous and "
                    "no replacement is granted"
                ),
                replacement_eligible=bool(_PROVIDER_NO_EXECUTION_GUARANTEE),
                extra={"provider_error_class": exception_type},
            )
        if state == DELIVERY_AMBIGUOUS:
            return _result(
                DELIVERY_AMBIGUOUS, BILLING_UNKNOWN,
                evidence=EVIDENCE_TYPED_EXCEPTION,
                determination=(
                    f"{exception_type} proves only that the client stopped "
                    "observing; server-side receipt, model execution and billing "
                    "are unknown"
                ),
                replacement_eligible=False,
            )
        if state == DELIVERY_CONFIRMED:
            return _result(
                DELIVERY_CONFIRMED, BILLING_CONFIRMED,
                evidence=EVIDENCE_TYPED_EXCEPTION,
                determination=(
                    f"{exception_type} is raised after a response was received"
                ),
                replacement_eligible=False,
            )

    # 3. HTTP status, then headers.
    if http_status is not None:
        status = int(http_status)
        if status in _REJECTED_STATUSES:
            return _result(
                REJECTED_BEFORE_EXECUTION
                if _PROVIDER_NO_EXECUTION_GUARANTEE
                else DELIVERY_AMBIGUOUS,
                BILLING_CONFIRMED
                if _PROVIDER_NO_EXECUTION_GUARANTEE
                else BILLING_UNKNOWN,
                evidence=EVIDENCE_HTTP_STATUS,
                determination=(
                    f"HTTP {status} is an error response. A status code alone "
                    "does not establish that no model ran or that nothing was "
                    "billed; that requires a frozen provider guarantee, and the "
                    "frozen artifact here is an endpoint identity hash"
                ),
                replacement_eligible=bool(_PROVIDER_NO_EXECUTION_GUARANTEE),
                extra={"provider_rejection_reason": _REJECTED_STATUSES[status]},
            )
        if status in _AMBIGUOUS_STATUSES:
            return _result(
                DELIVERY_AMBIGUOUS, BILLING_UNKNOWN,
                evidence=EVIDENCE_HTTP_STATUS,
                determination=(
                    f"HTTP {status} means the server held the request; whether a "
                    "model ran is not observable from the client"
                ),
                replacement_eligible=False,
            )
    if response_headers_received:
        return _result(
            DELIVERY_AMBIGUOUS, BILLING_UNKNOWN,
            evidence=EVIDENCE_HTTP_STATUS,
            determination=(
                "response headers were received without a usable response body "
                "or identity"
            ),
            replacement_eligible=False,
        )

    # 4. Dispatch telemetry.  Only a persisted PRE_DISPATCH with no
    #    DISPATCH_STARTED proves the request never left the client.
    if dispatch_started is False:
        return _result(
            DEFINITELY_NOT_DISPATCHED, BILLING_CONFIRMED,
            evidence=EVIDENCE_DISPATCH_TELEMETRY,
            determination=(
                "the transition ledger records PRE_DISPATCH without "
                "DISPATCH_STARTED, so no request left the client"
            ),
            replacement_eligible=True,
            extra={"confirmed_cost_units": 0, "runner_stage": runner_stage},
        )
    if dispatch_started and acceptance_known is False:
        return _result(
            DELIVERY_AMBIGUOUS, BILLING_UNKNOWN,
            evidence=EVIDENCE_DISPATCH_TELEMETRY,
            determination=(
                "dispatch started but acceptance was never established; "
                "dispatch_started does not mean the provider accepted"
            ),
            replacement_eligible=False,
        )

    # 5. Compatibility fallback on exception text only.
    lowered = str(exception_text or "").lower()
    if lowered:
        for marker in _TEXT_AMBIGUOUS_MARKERS:
            if marker in lowered:
                return _result(
                    DELIVERY_AMBIGUOUS, BILLING_UNKNOWN,
                    evidence=EVIDENCE_TEXT_FALLBACK,
                    determination=(
                        f"no structured evidence; the exception text matched "
                        f"{marker!r}, which is treated as ambiguous delivery"
                    ),
                    replacement_eligible=False,
                )

    # 6. No evidence.  This is its own outcome, not anyone else's default.
    return _result(
        DELIVERY_UNKNOWN, BILLING_UNKNOWN,
        evidence=EVIDENCE_NONE,
        determination=(
            "no structured evidence identified this failure; it is reported as "
            "unclassified rather than attributed to the model or to the network"
        ),
        replacement_eligible=False,
        extra={"runner_stage": runner_stage},
    )


def completion_kind_for(
    *,
    delivery_state: str,
    model_reached: bool = False,
    runner_fault: bool = False,
) -> str:
    """Map one failure onto the frozen completion vocabulary."""
    if runner_fault:
        return RUNNER_ORCHESTRATION_FAILURE
    if delivery_state == DELIVERY_UNKNOWN:
        return UNCLASSIFIED_FAILURE
    if delivery_state == DELIVERY_AMBIGUOUS:
        return AMBIGUOUS_PROVIDER_DELIVERY
    if delivery_state in (DEFINITELY_NOT_DISPATCHED, REJECTED_BEFORE_EXECUTION):
        return INFRASTRUCTURE_TRANSPORT_FAILURE
    if delivery_state == DELIVERY_CONFIRMED and model_reached:
        return MODEL_OR_SCHEMA_GENERATION_FAILURE
    # A confirmed delivery whose failure is not attributable to model output is
    # still not automatically a model result.
    return UNCLASSIFIED_FAILURE


def counts_in_model_quality_denominator(completion_kind: str) -> bool:
    return completion_kind in MODEL_QUALITY_KINDS


def counts_in_operational_denominator(completion_kind: str) -> bool:
    return completion_kind in OPERATIONAL_KINDS


def requires_separate_report(completion_kind: str) -> bool:
    return completion_kind in SEPARATELY_REPORTED_KINDS


CALL_TELEMETRY_FIELDS = (
    "dispatch_started",
    "request_acceptance_known",
    "response_headers_received",
    "response_id",
    "usage",
    "response_model",
    "local_audit_persisted",
    "delivery_state",
    "billing_state",
    "retry_or_replacement_eligible",
    "evidence_basis",
    "determination",
)


def call_telemetry_record(
    *,
    dispatch_started: bool,
    response_headers_received: bool,
    response_id: str | None,
    usage: dict[str, Any] | None,
    response_model: str | None,
    local_audit_persisted: bool,
    exception_type: str | None = None,
    http_status: int | None = None,
    exception_text: str = "",
    acceptance_known: bool | None = None,
    runner_stage: str | None = None,
) -> dict[str, Any]:
    """The frozen per-call delivery record, written for every call.

    An absent local audit is a fact about this machine.  It is not evidence that
    the provider did nothing, and must never be summarised as
    ``provider_calls=0`` or ``cost=0``.
    """
    decision = classify_delivery(
        exception_text,
        audit_persisted=local_audit_persisted,
        response_id=response_id,
        usage=usage,
        exception_type=exception_type,
        http_status=http_status,
        response_headers_received=response_headers_received,
        structured_response_present=bool(response_id and local_audit_persisted),
        dispatch_started=dispatch_started,
        acceptance_known=acceptance_known,
        runner_stage=runner_stage,
    )
    if acceptance_known is None:
        acceptance_known = bool(
            response_headers_received
            or response_id
            or decision["delivery_state"]
            in (REJECTED_BEFORE_EXECUTION, DEFINITELY_NOT_DISPATCHED)
        )
    record = {
        "dispatch_started": bool(dispatch_started),
        "request_acceptance_known": bool(acceptance_known),
        "response_headers_received": bool(response_headers_received),
        "response_id": response_id,
        "usage": usage,
        "response_model": response_model,
        "local_audit_persisted": bool(local_audit_persisted),
        "delivery_state": decision["delivery_state"],
        "billing_state": decision["billing_state"],
        "retry_or_replacement_eligible": bool(decision["replacement_eligible"]),
        "evidence_basis": decision["evidence_basis"],
        "determination": decision["determination"],
    }
    for optional in ("confirmed_cost_units", "provider_rejection_reason"):
        if optional in decision:
            record[optional] = decision[optional]
    missing = [name for name in CALL_TELEMETRY_FIELDS if name not in record]
    if missing:
        raise ValueError(f"call telemetry is incomplete: {missing}")
    return record


def summarize_cost(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Report cost in two layers, and never collapse UNKNOWN to zero."""
    confirmed_tokens = 0
    unknown_calls = 0
    for item in records:
        if item.get("billing_state") == BILLING_CONFIRMED and item.get("usage"):
            confirmed_tokens += int(item["usage"].get("total_tokens") or 0)
        elif item.get("billing_state") == BILLING_UNKNOWN:
            unknown_calls += 1
    return {
        "confirmed_total_tokens": confirmed_tokens,
        "calls_with_unknown_billing": unknown_calls,
        "unknown_billing_tokens": None if unknown_calls else 0,
        "statement": (
            "Confirmed tokens are a lower bound from persisted audit rows. "
            f"{unknown_calls} call(s) have UNKNOWN billing: server-side receipt "
            "and cost cannot be determined locally and must not be recorded as 0."
        ),
    }


def replacement_allowed(record: dict[str, Any]) -> bool:
    """One replacement, only for a request proven never to have been executed."""
    kind = record.get("completion_kind")
    if kind in (AMBIGUOUS_PROVIDER_DELIVERY, UNCLASSIFIED_FAILURE):
        return False
    if record.get("delivery_state") not in (
        DEFINITELY_NOT_DISPATCHED,
        REJECTED_BEFORE_EXECUTION,
    ):
        return False
    if not record.get("replacement_eligible"):
        return False
    if record.get("billing_state") != BILLING_CONFIRMED:
        return False
    return int(record.get("replacement_attempts") or 0) < 1
