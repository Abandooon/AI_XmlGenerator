# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright contributors to the vLLM project
"""Fail-closed research audit primitives for structured-output decoding.

The audit is disabled unless ``VLLM_STRUCTURED_OUTPUT_AUDIT_DIR`` is set. It
records hashes and aggregate counts, not prompt text, grammar text, or decoded
token text. Each EngineCore process writes a distinct NDJSON file.
"""

from __future__ import annotations

import hashlib
import json
import os
import queue
import re
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


AUDIT_SCHEMA_VERSION = "vllm.structured_output.audit.v3"
_CHAIN_ORIGIN = "0" * 64
_SENTINEL = object()
_EXPERIMENT_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}")
_EXTERNAL_REQUEST_ID_PATTERN = re.compile(
    r"[A-Za-z0-9][A-Za-z0-9._:-]{0,191}"
)
_AUDIT_CONTEXT_HASH_ENV = {
    "runtime_fingerprint_sha256": (
        "VLLM_STRUCTURED_OUTPUT_RUNTIME_FINGERPRINT_SHA256"
    ),
    "protocol_sha256": "VLLM_STRUCTURED_OUTPUT_PROTOCOL_SHA256",
    "asset_manifest_sha256": (
        "VLLM_STRUCTURED_OUTPUT_ASSET_MANIFEST_SHA256"
    ),
}


class StructuredOutputAuditError(RuntimeError):
    """Raised when required audit evidence cannot be recorded completely."""


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_json(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def hash_token_ids(token_ids: Iterable[int] | None) -> str | None:
    if token_ids is None:
        return None
    return sha256_json([int(token_id) for token_id in token_ids])


def _as_unsigned_word(word: Any) -> int:
    return int(word) & 0xFFFFFFFF


def packed_bitmask_allowed_token_count(
    packed_words: Sequence[int] | Any,
    vocab_size: int,
) -> int:
    """Count allowed tokens in an XGrammar packed int32 bitmask row.

    Each bit corresponds to one vocabulary token; a set bit means allowed. The
    final word may contain padding bits beyond ``vocab_size`` and those bits are
    excluded.
    """

    if vocab_size < 0:
        raise ValueError("vocab_size_must_be_nonnegative")
    if hasattr(packed_words, "tolist"):
        packed_words = packed_words.tolist()
    words = list(packed_words)
    required_words = (vocab_size + 31) // 32
    if len(words) < required_words:
        raise ValueError("packed_bitmask_shorter_than_vocab_size")
    if required_words == 0:
        return 0

    count = sum(_as_unsigned_word(word).bit_count() for word in words[:required_words])
    remainder = vocab_size % 32
    if remainder:
        final_word = _as_unsigned_word(words[required_words - 1])
        count -= final_word.bit_count()
        count += (final_word & ((1 << remainder) - 1)).bit_count()
    return count


def hash_packed_bitmask(packed_words: Sequence[int] | Any, vocab_size: int) -> str:
    if hasattr(packed_words, "tolist"):
        packed_words = packed_words.tolist()
    words = list(packed_words)
    required_words = (vocab_size + 31) // 32
    if len(words) < required_words:
        raise ValueError("packed_bitmask_shorter_than_vocab_size")
    digest = hashlib.sha256()
    digest.update(int(vocab_size).to_bytes(8, "little", signed=False))
    for word in words[:required_words]:
        digest.update(_as_unsigned_word(word).to_bytes(4, "little", signed=False))
    return digest.hexdigest()


def token_is_allowed(
    packed_words: Sequence[int] | Any,
    vocab_size: int,
    token_id: int,
) -> bool:
    """Whether one token id is permitted by an XGrammar packed int32 bitmask."""
    if not 0 <= token_id < vocab_size:
        raise ValueError("token_id_outside_vocab")
    if hasattr(packed_words, "tolist"):
        packed_words = packed_words.tolist()
    words = list(packed_words)
    required_words = (vocab_size + 31) // 32
    if len(words) < required_words:
        raise ValueError("packed_bitmask_shorter_than_vocab_size")
    word = _as_unsigned_word(words[token_id // 32])
    return bool(word >> (token_id % 32) & 1)


def binding_step(
    packed_words: Sequence[int] | Any,
    vocab_size: int,
    unconstrained_argmax: int,
) -> dict[str, Any]:
    """Classify one decoding step as bound or unbound by the grammar.

    This replaces the withdrawn allowed-token statistic with a directly
    interpretable intervention measure: whether the model's own preferred token
    was one the grammar forbids. That is a per-step boolean and aggregates into
    a rate with a stable denominator.
    """
    allowed = token_is_allowed(packed_words, vocab_size, unconstrained_argmax)
    return {
        "unconstrained_argmax": int(unconstrained_argmax),
        "argmax_allowed": allowed,
        # A step is "bound" when the grammar removed the model's first choice.
        "bound": not allowed,
        "allowed_token_count": packed_bitmask_allowed_token_count(
            packed_words, vocab_size
        ),
    }


def binding_rate(steps: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Aggregate binding steps.

    ``None`` rather than zero when no step was observed: an unmeasured rate and
    a measured rate of zero are different claims, and the discarded metric was
    reported as though they were the same.
    """
    observed = [step for step in steps if isinstance(step.get("bound"), bool)]
    bound = sum(1 for step in observed if step["bound"])
    return {
        "steps_observed": len(observed),
        "steps_bound": bound,
        "binding_rate": (bound / len(observed)) if observed else None,
    }


def classify_binding_observations(
    request_ids: Sequence[str],
    packed_rows: Sequence[Sequence[int]] | Any,
    vocab_size: int,
    unconstrained_argmax_ids: Sequence[int],
) -> dict[str, bool]:
    """Classify aligned non-speculative request rows without retaining token ids."""
    if hasattr(packed_rows, "tolist"):
        packed_rows = packed_rows.tolist()
    rows = list(packed_rows)
    if not (
        len(request_ids) == len(rows) == len(unconstrained_argmax_ids)
    ):
        raise StructuredOutputAuditError("binding_request_row_mismatch")
    observations: dict[str, bool] = {}
    for request_id, packed_row, argmax_id in zip(
        request_ids, rows, unconstrained_argmax_ids, strict=True
    ):
        if request_id in observations:
            raise StructuredOutputAuditError("duplicate_binding_request_row")
        observations[request_id] = bool(
            binding_step(packed_row, vocab_size, int(argmax_id))["bound"]
        )
    return observations


def structured_output_binding_required() -> bool:
    """Whether fail-closed binding observation is enabled for this process."""
    return os.environ.get(
        "VLLM_STRUCTURED_OUTPUT_BINDING_REQUIRED", "false"
    ).lower() == "true"


def structured_output_audit_context() -> dict[str, str]:
    """Read the frozen experiment identity required by binding audit."""
    experiment_id = os.environ.get(
        "VLLM_STRUCTURED_OUTPUT_EXPERIMENT_ID", ""
    ).strip()
    context = {"experiment_id": experiment_id}
    for field_name, environment_name in _AUDIT_CONTEXT_HASH_ENV.items():
        context[field_name] = os.environ.get(environment_name, "").strip().lower()
    if not structured_output_binding_required():
        return context
    if _EXPERIMENT_ID_PATTERN.fullmatch(experiment_id) is None:
        raise StructuredOutputAuditError("invalid_audit_experiment_id")
    for field_name in _AUDIT_CONTEXT_HASH_ENV:
        value = context[field_name]
        invalid_character = any(
            character not in "0123456789abcdef" for character in value
        )
        if len(value) != 64 or invalid_character:
            raise StructuredOutputAuditError(
                f"invalid_audit_context_hash:{field_name}"
            )
    return context


class BindingObservationTracker:
    """Pair scheduler mask rows with worker observations by request and ordinal."""

    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled
        self._lock = threading.Lock()
        self._mask_counts: dict[str, int] = {}
        self._pending_masks: dict[str, list[tuple[int, bool]]] = {}

    def start_request(self, request_id: str) -> None:
        if not self.enabled:
            return
        with self._lock:
            if request_id in self._pending_masks:
                raise StructuredOutputAuditError("duplicate_binding_request_start")
            self._mask_counts[request_id] = 0
            self._pending_masks[request_id] = []

    def register_mask(self, request_id: str, mask_applied: bool) -> int | None:
        if not self.enabled:
            return None
        with self._lock:
            if request_id not in self._pending_masks:
                raise StructuredOutputAuditError(
                    "binding_mask_without_request_start"
                )
            sample_ordinal = self._mask_counts[request_id]
            self._mask_counts[request_id] += 1
            self._pending_masks[request_id].append(
                (sample_ordinal, mask_applied)
            )
            return sample_ordinal

    def consume_observation(self, request_id: str) -> tuple[int, bool]:
        if not self.enabled:
            raise StructuredOutputAuditError("binding_tracker_not_enabled")
        with self._lock:
            pending = self._pending_masks.get(request_id)
            if not pending:
                raise StructuredOutputAuditError(
                    "binding_observation_without_pending_mask"
                )
            return pending.pop(0)

    def finish_request(self, request_id: str) -> int:
        if not self.enabled:
            return 0
        with self._lock:
            pending_count = len(self._pending_masks.get(request_id, ()))
            self._mask_counts.pop(request_id, None)
            self._pending_masks.pop(request_id, None)
            return pending_count


@dataclass
class _RequestState:
    next_sequence: int = 0
    chain_sha256: str = _CHAIN_ORIGIN
    dropped_event_count: int = 0
    ended: bool = False


class StructuredOutputAuditSink:
    """Bounded asynchronous NDJSON audit sink with per-request hash chains."""

    def __init__(
        self,
        audit_dir: Path | None,
        *,
        required: bool = False,
        queue_size: int = 8192,
    ) -> None:
        if queue_size <= 0:
            raise ValueError("queue_size_must_be_positive")
        self.audit_dir = audit_dir
        self.required = required
        self.enabled = audit_dir is not None
        self.queue_size = queue_size
        self._states: dict[str, _RequestState] = {}
        self._state_lock = threading.Lock()
        self._queue: queue.Queue[dict[str, Any] | object] | None = None
        self._writer: threading.Thread | None = None
        self._writer_error: BaseException | None = None
        self._closed = False
        self.output_path: Path | None = None

        if self.enabled:
            assert audit_dir is not None
            audit_dir.mkdir(parents=True, exist_ok=True)
            self.output_path = (
                audit_dir / f"structured-output-audit-{os.getpid()}.ndjson"
            )
            self._queue = queue.Queue(maxsize=queue_size)
            self._writer = threading.Thread(
                target=self._writer_loop,
                name="vllm-structured-output-audit",
                daemon=True,
            )
            self._writer.start()

    @classmethod
    def from_env(cls) -> "StructuredOutputAuditSink":
        raw_dir = os.environ.get("VLLM_STRUCTURED_OUTPUT_AUDIT_DIR", "").strip()
        required = os.environ.get(
            "VLLM_STRUCTURED_OUTPUT_AUDIT_REQUIRED", "false"
        ).lower() == "true"
        raw_queue_size = os.environ.get(
            "VLLM_STRUCTURED_OUTPUT_AUDIT_QUEUE_SIZE", "8192"
        )
        try:
            queue_size = int(raw_queue_size)
        except ValueError as exc:
            raise StructuredOutputAuditError("invalid_audit_queue_size") from exc
        return cls(
            Path(raw_dir) if raw_dir else None,
            required=required,
            queue_size=queue_size,
        )

    def _writer_loop(self) -> None:
        assert self.output_path is not None
        assert self._queue is not None
        try:
            stream = self.output_path.open(
                "a", encoding="utf-8", buffering=1, newline="\n"
            )
        except BaseException as exc:
            self._writer_error = exc
            stream = None
        try:
            while True:
                item = self._queue.get()
                try:
                    if item is _SENTINEL:
                        return
                    if stream is not None and self._writer_error is None:
                        try:
                            stream.write(_canonical_json(item) + "\n")
                        except BaseException as exc:
                            # Keep draining queued items so close() cannot deadlock.
                            # The missing records make verification INCOMPLETE.
                            self._writer_error = exc
                finally:
                    self._queue.task_done()
        finally:
            if stream is not None:
                stream.close()

    def _raise_if_writer_failed(self) -> None:
        if self._writer_error is not None and self.required:
            raise StructuredOutputAuditError(
                "audit_writer_failed"
            ) from self._writer_error

    def _enqueue(self, record: dict[str, Any], state: _RequestState) -> bool:
        if not self.enabled:
            return False
        self._raise_if_writer_failed()
        assert self._queue is not None
        try:
            self._queue.put_nowait(record)
            return True
        except queue.Full as exc:
            state.dropped_event_count += 1
            if self.required:
                raise StructuredOutputAuditError("audit_queue_full") from exc
            return False

    @staticmethod
    def _record_core(
        request_id: str,
        sequence: int,
        timestamp_ns: int,
        event: Mapping[str, Any],
    ) -> dict[str, Any]:
        return {
            "schema_version": AUDIT_SCHEMA_VERSION,
            "record_type": "structured_output_audit_event",
            "timestamp_ns": timestamp_ns,
            "request_id": request_id,
            "sequence": sequence,
            "event": dict(event),
        }

    def _append_locked(
        self,
        request_id: str,
        state: _RequestState,
        event: Mapping[str, Any],
    ) -> dict[str, Any]:
        timestamp_ns = time.time_ns()
        core = self._record_core(
            request_id, state.next_sequence, timestamp_ns, event
        )
        chain = hashlib.sha256(
            bytes.fromhex(state.chain_sha256) + _canonical_json(core).encode("utf-8")
        ).hexdigest()
        record = {
            **core,
            "previous_chain_sha256": state.chain_sha256,
            "chain_sha256": chain,
        }
        state.next_sequence += 1
        state.chain_sha256 = chain
        self._enqueue(record, state)
        return record

    def start_request(self, request_id: str, metadata: Mapping[str, Any]) -> None:
        if not self.enabled:
            return
        with self._state_lock:
            if request_id in self._states:
                if self.required:
                    raise StructuredOutputAuditError("duplicate_request_start")
                return
            state = _RequestState()
            self._states[request_id] = state
            self._append_locked(
                request_id,
                state,
                {"event_type": "request_start", "metadata": dict(metadata)},
            )

    def record_event(
        self,
        request_id: str,
        event_type: str,
        payload: Mapping[str, Any] | None = None,
    ) -> None:
        if not self.enabled:
            return
        with self._state_lock:
            state = self._states.get(request_id)
            if state is None:
                if self.required:
                    raise StructuredOutputAuditError("event_without_request_start")
                return
            if state.ended:
                if self.required:
                    raise StructuredOutputAuditError("event_after_request_end")
                return
            self._append_locked(
                request_id,
                state,
                {"event_type": event_type, "payload": dict(payload or {})},
            )

    def end_request(
        self,
        request_id: str,
        *,
        finish_reason: str,
        output_token_ids: Iterable[int] | None,
        grammar_terminated: bool | None = None,
    ) -> None:
        if not self.enabled:
            return
        with self._state_lock:
            state = self._states.get(request_id)
            if state is None:
                if self.required:
                    raise StructuredOutputAuditError("end_without_request_start")
                return
            if state.ended:
                if self.required:
                    raise StructuredOutputAuditError("duplicate_request_end")
                return
            writer_failed = self._writer_error is not None
            trace_complete = state.dropped_event_count == 0 and not writer_failed
            self._append_locked(
                request_id,
                state,
                {
                    "event_type": "request_end",
                    "finish_reason": finish_reason,
                    "output_token_ids_sha256": hash_token_ids(output_token_ids),
                    "grammar_terminated": grammar_terminated,
                    "event_count_before_end": state.next_sequence,
                    "dropped_event_count": state.dropped_event_count,
                    "writer_failed": writer_failed,
                    "trace_complete": trace_complete,
                },
            )
            state.ended = True
            del self._states[request_id]

    def close(self) -> None:
        if not self.enabled or self._queue is None or self._writer is None:
            return
        if self._closed:
            return
        self._closed = True
        self._queue.put(_SENTINEL)
        self._queue.join()
        self._writer.join(timeout=10)
        if self._writer.is_alive() and self.required:
            raise StructuredOutputAuditError("audit_writer_shutdown_timeout")
        self._raise_if_writer_failed()


def verify_audit_records(
    records: Iterable[Mapping[str, Any]],
    *,
    expected_request_ids: Iterable[str] | None = None,
    expected_external_request_ids: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Verify traces and join them through experiment-owned external ids."""

    grouped: dict[str, list[Mapping[str, Any]]] = {}
    errors: list[str] = []
    all_binding_steps: list[Mapping[str, Any]] = []
    for record in records:
        request_id = str(record.get("request_id") or "")
        if not request_id:
            errors.append("record_missing_request_id")
            continue
        grouped.setdefault(request_id, []).append(record)

    requests: dict[str, dict[str, Any]] = {}
    external_to_internals: dict[str, list[str]] = {}
    for request_id, request_records in grouped.items():
        ordered = sorted(
            request_records, key=lambda item: int(item.get("sequence", -1))
        )
        previous_chain = _CHAIN_ORIGIN
        event_types: list[str] = []
        request_errors: list[str] = []
        for expected_sequence, record in enumerate(ordered):
            if record.get("schema_version") != AUDIT_SCHEMA_VERSION:
                request_errors.append("schema_version_mismatch")
            if record.get("sequence") != expected_sequence:
                request_errors.append("sequence_gap")
            if record.get("previous_chain_sha256") != previous_chain:
                request_errors.append("previous_chain_mismatch")
            core = {
                key: record.get(key)
                for key in (
                    "schema_version",
                    "record_type",
                    "timestamp_ns",
                    "request_id",
                    "sequence",
                    "event",
                )
            }
            expected_chain = hashlib.sha256(
                bytes.fromhex(previous_chain) + _canonical_json(core).encode("utf-8")
            ).hexdigest()
            if record.get("chain_sha256") != expected_chain:
                request_errors.append("chain_mismatch")
            previous_chain = expected_chain
            event = record.get("event") or {}
            event_types.append(str(event.get("event_type") or ""))

        if event_types.count("request_start") != 1 or event_types[:1] != [
            "request_start"
        ]:
            request_errors.append("invalid_request_start_boundary")
        if event_types.count("request_end") != 1 or event_types[-1:] != ["request_end"]:
            request_errors.append("invalid_request_end_boundary")
        if event_types.count("grammar_compile_start") != 1:
            request_errors.append("invalid_grammar_compile_start_count")
        if event_types.count("grammar_compile_end") != 1:
            request_errors.append("invalid_grammar_compile_end_count")
        if ordered and event_types[-1:] == ["request_end"]:
            end_event = ordered[-1].get("event") or {}
            if not end_event.get("trace_complete"):
                request_errors.append("trace_marked_incomplete")
            if end_event.get("event_count_before_end") != len(ordered) - 1:
                request_errors.append("end_event_count_mismatch")

        start_event = ordered[0].get("event") if ordered else {}
        start_metadata = (start_event or {}).get("metadata") or {}
        binding_required = bool(start_metadata.get("binding_required"))
        raw_external_request_id = start_metadata.get("external_request_id")
        external_request_id: str | None = None
        if binding_required:
            if raw_external_request_id is None:
                request_errors.append("external_request_id_missing")
            elif (
                not isinstance(raw_external_request_id, str)
                or _EXTERNAL_REQUEST_ID_PATTERN.fullmatch(raw_external_request_id)
                is None
            ):
                request_errors.append("external_request_id_invalid")
            else:
                external_request_id = raw_external_request_id
                external_to_internals.setdefault(external_request_id, []).append(
                    request_id
                )
        mask_steps: dict[int, Mapping[str, Any]] = {}
        binding_steps: dict[int, Mapping[str, Any]] = {}
        for record in ordered:
            event = record.get("event") or {}
            event_type = event.get("event_type")
            payload = event.get("payload") or {}
            if (
                event_type == "mask_ready"
                and payload.get("sample_ordinal") is not None
            ):
                try:
                    ordinal = int(payload["sample_ordinal"])
                except (TypeError, ValueError):
                    request_errors.append("invalid_mask_sample_ordinal")
                    continue
                if ordinal in mask_steps:
                    request_errors.append("duplicate_mask_sample_ordinal")
                mask_steps[ordinal] = payload
            elif event_type == "binding_step":
                try:
                    ordinal = int(payload.get("sample_ordinal", -1))
                except (TypeError, ValueError):
                    request_errors.append("invalid_binding_sample_ordinal")
                    continue
                if ordinal < 0:
                    request_errors.append("invalid_binding_sample_ordinal")
                elif ordinal in binding_steps:
                    request_errors.append("duplicate_binding_sample_ordinal")
                else:
                    binding_steps[ordinal] = payload
                    if payload.get("evaluable"):
                        all_binding_steps.append(payload)

        if binding_required:
            end_event = ordered[-1].get("event") if ordered else {}
            if (end_event or {}).get("finish_reason") != "FINISHED_STOPPED":
                request_errors.append("request_did_not_finish_normally")
            if (end_event or {}).get("grammar_terminated") is not True:
                request_errors.append("grammar_not_terminated_at_request_end")
            if "binding_incomplete" in event_types:
                request_errors.append("binding_marked_incomplete")
            if set(mask_steps) != set(binding_steps):
                request_errors.append("binding_mask_step_mismatch")
            for ordinal in sorted(set(mask_steps) & set(binding_steps)):
                mask_payload = mask_steps[ordinal]
                binding_payload = binding_steps[ordinal]
                mask_applied = bool(mask_payload.get("mask_applied"))
                if binding_payload.get("mask_applied") is not mask_applied:
                    request_errors.append("binding_mask_application_mismatch")
                if bool(binding_payload.get("evaluable")) is not mask_applied:
                    request_errors.append("binding_evaluable_mismatch")
                bound = binding_payload.get("bound")
                if mask_applied and not isinstance(bound, bool):
                    request_errors.append("binding_bound_value_missing")
                if not mask_applied and bound is not None:
                    request_errors.append("binding_bound_value_not_null")

        request_binding = binding_rate(binding_steps.values())

        requests[request_id] = {
            "status": "PASS" if not request_errors else "INCOMPLETE",
            "record_count": len(ordered),
            "event_types": event_types,
            "errors": sorted(set(request_errors)),
            "final_chain_sha256": previous_chain,
            "binding": request_binding,
            "external_request_id": external_request_id,
        }
        errors.extend(f"{request_id}:{error}" for error in request_errors)

    duplicate_external_request_ids = sorted(
        external_id
        for external_id, internal_ids in external_to_internals.items()
        if len(internal_ids) != 1
    )
    for external_id in duplicate_external_request_ids:
        for internal_id in external_to_internals[external_id]:
            requests[internal_id]["status"] = "INCOMPLETE"
            if "duplicate_external_request_id" not in requests[internal_id]["errors"]:
                requests[internal_id]["errors"].append(
                    "duplicate_external_request_id"
                )
                requests[internal_id]["errors"].sort()
            errors.append(f"{internal_id}:duplicate_external_request_id")

    external_to_internal = {
        external_id: internal_ids[0]
        for external_id, internal_ids in external_to_internals.items()
        if len(internal_ids) == 1
    }
    expected = set(expected_request_ids or ())
    missing_request_ids = sorted(expected - set(grouped))
    unexpected_request_ids = (
        sorted(set(grouped) - expected)
        if expected_request_ids is not None
        else []
    )
    errors.extend(f"{request_id}:missing_trace" for request_id in missing_request_ids)
    errors.extend(
        f"{request_id}:unexpected_trace" for request_id in unexpected_request_ids
    )

    expected_external = set(expected_external_request_ids or ())
    missing_external_request_ids = sorted(
        expected_external - set(external_to_internal)
    )
    unexpected_external_request_ids = (
        sorted(set(external_to_internals) - expected_external)
        if expected_external_request_ids is not None
        else []
    )
    errors.extend(
        f"{request_id}:missing_external_trace"
        for request_id in missing_external_request_ids
    )
    errors.extend(
        f"{request_id}:unexpected_external_trace"
        for request_id in unexpected_external_request_ids
    )
    return {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "status": "PASS" if grouped and not errors else "INCOMPLETE",
        "request_count": len(grouped),
        "requests": requests,
        "missing_request_ids": missing_request_ids,
        "unexpected_request_ids": unexpected_request_ids,
        "missing_external_request_ids": missing_external_request_ids,
        "unexpected_external_request_ids": unexpected_external_request_ids,
        "duplicate_external_request_ids": duplicate_external_request_ids,
        "external_request_id_to_internal_request_id": external_to_internal,
        "errors": errors,
        "binding": binding_rate(all_binding_steps),
    }
