# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright contributors to the vLLM project
import itertools
import multiprocessing
import time
from collections.abc import Iterable, Sequence
from concurrent.futures import Future, ThreadPoolExecutor
from typing import TYPE_CHECKING

from vllm.config import VllmConfig
from vllm.logger import init_logger
from vllm.reasoning import ReasoningParserManager
from vllm.tokenizers import cached_tokenizer_from_config
from vllm.utils.import_utils import LazyLoader
from vllm.v1.structured_output.audit import (
    BindingObservationTracker,
    StructuredOutputAuditError,
    StructuredOutputAuditSink,
    hash_packed_bitmask,
    hash_token_ids,
    packed_bitmask_allowed_token_count,
    sha256_json,
    structured_output_audit_context,
    structured_output_binding_required,
)
from vllm.v1.structured_output.backend_guidance import GuidanceBackend
from vllm.v1.structured_output.backend_types import (
    StructuredOutputBackend,
    StructuredOutputGrammar,
    StructuredOutputOptions,
)
from vllm.v1.structured_output.backend_xgrammar import XgrammarBackend

if TYPE_CHECKING:
    import numpy as np
    import numpy.typing as npt
    import torch

    from vllm.reasoning import ReasoningParser
    from vllm.v1.request import Request
else:
    torch = LazyLoader("torch", globals(), "torch")


logger = init_logger(__name__)

# EngineCoreOutput.stop_reason is the only stop-detail field transported from
# the scheduler process to the output processor.  A grammar-completing token is
# payload, not an EOS/stop token, so the output processor must not drop it when
# the scheduler terminates immediately at the root grammar boundary.
STRUCTURED_OUTPUT_TERMINATED_STOP_REASON = (
    "atlas_structured_output_grammar_terminated"
)


class StructuredOutputManager:
    """Engine-level manager for structured output requests."""

    def __init__(self, vllm_config: VllmConfig):
        self.backend: StructuredOutputBackend | None = None
        # We only store the class of the reasoner in the manager.
        # The parser instance is request-scoped because some reasoning parsers
        # depend on per-request chat-template kwargs.
        self.reasoner_cls: type[ReasoningParser] | None = None
        self.vllm_config = vllm_config
        self.binding_required = structured_output_binding_required()
        # Checked before the audit sink is built. Constructing the sink creates
        # the audit directory and starts a daemon writer thread, and a
        # configuration that is going to be refused should not allocate either:
        # the raise leaves no handle through which the thread could be closed.
        if self.binding_required and vllm_config.num_speculative_tokens != 0:
            raise StructuredOutputAuditError(
                "binding_requires_speculative_decoding_disabled"
            )
        self.audit_sink = StructuredOutputAuditSink.from_env()
        self.audit_context = structured_output_audit_context()
        if self.binding_required and (
            not self.audit_sink.enabled or not self.audit_sink.required
        ):
            raise StructuredOutputAuditError(
                "binding_requires_fail_closed_audit_sink"
            )
        self.binding_tracker = BindingObservationTracker(self.binding_required)
        self._audited_request_ids: set[str] = set()

        # When in external_launcher mode, async grammar compilation causes deadlocks
        # due to external_launcher mode having a scheduler for each TP rank.
        # Async grammar compilation causes the
        # WAITING_FOR_STRUCTURED_OUTPUT_GRAMMAR → WAITING transition to
        # happen at different times on different TP ranks,
        # breaking the determinism assumption that external_launcher relies on.
        self._use_async_grammar_compilation = (
            vllm_config.parallel_config.distributed_executor_backend
            != "external_launcher"
        )

        self._grammar_bitmask: torch.Tensor | None = None
        self._full_mask = torch.tensor(-1, dtype=torch.int32)

        max_batch_size = self.vllm_config.scheduler_config.max_num_seqs
        self.fill_bitmask_parallel_threshold = 128
        if self.fill_bitmask_parallel_threshold < max_batch_size:
            self.fill_bitmask_parallel_batch_size = 16
            # Use:
            # - at least 1 CPU
            # - at most half the number of CPUs or 8, whichever is less
            max_workers = max(1, min(multiprocessing.cpu_count() // 2, 8))
            self.executor_for_fillmask = ThreadPoolExecutor(max_workers=max_workers)

        if not self.vllm_config.model_config.skip_tokenizer_init:
            # The default max_workers if not specified is the number of
            # CPUs * 5, which is way too high since these tasks are CPU-bound,
            # not I/O bound. We also know we would never dominate CPU usage
            # with just grammar compilation, so we set it to half the number
            # of CPUs.
            max_workers = max(1, (multiprocessing.cpu_count() + 1) // 2)
            self.executor = ThreadPoolExecutor(max_workers=max_workers)
            self.tokenizer = cached_tokenizer_from_config(
                model_config=self.vllm_config.model_config
            )
            reasoning_parser_plugin = (
                self.vllm_config.structured_outputs_config.reasoning_parser_plugin
            )
            if reasoning_parser_plugin and len(reasoning_parser_plugin) > 3:
                ReasoningParserManager.import_reasoning_parser(reasoning_parser_plugin)

            reasoning_parser = (
                self.vllm_config.structured_outputs_config.reasoning_parser
            )
            if reasoning_parser:
                self.reasoner_cls = ReasoningParserManager.get_reasoning_parser(
                    reasoning_parser
                )

        self.enable_in_reasoning = (
            self.vllm_config.structured_outputs_config.enable_in_reasoning
        )

    def _get_reasoner(self, request: "Request") -> "ReasoningParser | None":
        structured_req = request.structured_output_request
        if structured_req is None or self.reasoner_cls is None:
            return None

        if structured_req.reasoner is None:
            # Lazily build the request-local parser so the structured-output
            # gate observes the same template kwargs used by the frontend.
            parser_kwargs = structured_req.reasoning_parser_kwargs or {}
            structured_req.reasoner = self.reasoner_cls(
                tokenizer=self.tokenizer,
                **parser_kwargs,
            )
        return structured_req.reasoner

    def grammar_init(self, request: "Request") -> None:
        if request.structured_output_request is None:
            return

        request_type, grammar_spec = (
            request.structured_output_request.structured_output_key
        )
        assert request.sampling_params is not None
        structured_params = request.sampling_params.structured_outputs
        assert structured_params is not None
        if self.request_binding_required(request):
            if not self.binding_required:
                raise StructuredOutputAuditError(
                    "request_binding_requires_server_capability"
                )
            model_config = self.vllm_config.model_config
            self.audit_sink.start_request(
                request.request_id,
                {
                    "backend": structured_params._backend,
                    "structured_output_type": request_type.name,
                    "grammar_spec_sha256": sha256_json(grammar_spec),
                    "grammar_spec_character_count": len(grammar_spec),
                    "model": str(getattr(model_config, "model", "") or ""),
                    "model_revision": str(
                        getattr(model_config, "revision", "") or ""
                    ),
                    "prompt_token_count": len(request.prompt_token_ids or ()),
                    "prompt_token_ids_sha256": hash_token_ids(
                        request.prompt_token_ids
                    ),
                    "external_request_id": (
                        structured_params.atlas_audit_request_id
                    ),
                    "binding_required": True,
                    **self.audit_context,
                },
            )
            self._audited_request_ids.add(request.request_id)
            self.binding_tracker.start_request(request.request_id)

        if TYPE_CHECKING:
            assert (
                request.sampling_params is not None
                and request.sampling_params.structured_outputs is not None
            )

        # Initialize the backend the first time it is needed.
        #
        # NOTE: We only support a single backend. We do NOT support different
        # backends on a per-request basis in V1 (for now, anyway...).
        # _backend is set in Processor._validate_structured_output
        if self.backend is None:
            assert request.sampling_params is not None
            backend = request.sampling_params.structured_outputs._backend
            vocab_size = self.vllm_config.model_config.get_vocab_size()
            if backend == "xgrammar":
                self.backend = XgrammarBackend(
                    self.vllm_config,
                    tokenizer=self.tokenizer,
                    vocab_size=vocab_size,
                )
            elif backend == "guidance":
                self.backend = GuidanceBackend(
                    self.vllm_config,
                    tokenizer=self.tokenizer,
                    vocab_size=vocab_size,
                )
            elif backend == "outlines":
                from vllm.v1.structured_output.backend_outlines import OutlinesBackend

                self.backend = OutlinesBackend(
                    self.vllm_config,
                    tokenizer=self.tokenizer,
                    vocab_size=vocab_size,
                )
            elif backend == "lm-format-enforcer":
                from vllm.v1.structured_output.backend_lm_format_enforcer import (  # noqa: E501
                    LMFormatEnforcerBackend,
                )

                self.backend = LMFormatEnforcerBackend(
                    self.vllm_config,
                    tokenizer=self.tokenizer,
                    vocab_size=vocab_size,
                )
            else:
                raise ValueError(f"Unsupported structured output backend: {backend}")

        grammar: Future[StructuredOutputGrammar] | StructuredOutputGrammar
        if self._use_async_grammar_compilation:
            grammar = self.executor.submit(self._create_grammar, request)
        else:
            try:
                grammar = self._create_grammar(request)
            except Exception as e:
                grammar = Future()
                grammar.set_exception(e)
        request.structured_output_request.grammar = grammar

    @staticmethod
    def request_binding_required(request: "Request") -> bool:
        """Returns whether this request opted into ATLAS binding audit."""
        sampling_params = request.sampling_params
        structured_params = (
            sampling_params.structured_outputs
            if sampling_params is not None
            else None
        )
        return bool(
            structured_params is not None
            and structured_params.atlas_audit_binding
        )

    def _request_is_audited(self, request_id: str) -> bool:
        return request_id in self._audited_request_ids

    def _create_grammar(self, request: "Request") -> StructuredOutputGrammar:
        struct_request = request.structured_output_request
        assert struct_request is not None
        # Note that the request was validated in the engine core client,
        # so at this point we know it is a supported type of request. Grammar
        # compilation may still fail; the Future carries that error to the
        # scheduler so it can fail only this request.
        started = time.perf_counter()
        audited = self._request_is_audited(request.request_id)
        if audited:
            self.audit_sink.record_event(
                request.request_id,
                "grammar_compile_start",
            )
        try:
            request_type, grammar_spec = struct_request.structured_output_key
            assert self.backend is not None
            grammar = self.backend.compile_grammar(request_type, grammar_spec)
            if audited:
                self.audit_sink.record_event(
                    request.request_id,
                    "grammar_compile_end",
                    {
                        "status": "PASS",
                        "duration_seconds": time.perf_counter() - started,
                    },
                )
            return grammar
        except Exception as exc:
            if audited:
                self.audit_sink.record_event(
                    request.request_id,
                    "grammar_compile_end",
                    {
                        "status": "FAIL",
                        "duration_seconds": time.perf_counter() - started,
                        "error_type": type(exc).__name__,
                    },
                )
            logger.exception(
                "Failed to compile grammar for request %s", request.request_id
            )
            raise

    def _fill_bitmasks(
        self, batch: Iterable[tuple[StructuredOutputGrammar, int, bool, str]]
    ) -> None:
        assert self._grammar_bitmask is not None
        vocab_size = self.vllm_config.model_config.get_vocab_size()
        for grammar, index, apply_bitmask, request_id in batch:
            grammar_terminated = grammar.is_terminated()
            mask_applied = apply_bitmask and not grammar_terminated
            if mask_applied:
                grammar.fill_bitmask(self._grammar_bitmask, index)
            else:
                # Note that for thinking support, we will need to
                # reset the relevant part of the bitmask for consequent
                # requests here.
                self._grammar_bitmask[index].fill_(self._full_mask)
            if self._request_is_audited(request_id):
                packed_row = self._grammar_bitmask[index]
                sample_ordinal = self.binding_tracker.register_mask(
                    request_id, mask_applied
                )
                self.audit_sink.record_event(
                    request_id,
                    "mask_ready",
                    {
                        "row_index": index,
                        "mask_applied": mask_applied,
                        "grammar_terminated": grammar_terminated,
                        "vocab_size": vocab_size,
                        "packed_word_count": int(packed_row.numel()),
                        "allowed_token_count": packed_bitmask_allowed_token_count(
                            packed_row, vocab_size
                        ),
                        "packed_mask_sha256": hash_packed_bitmask(
                            packed_row, vocab_size
                        ),
                        "sample_ordinal": sample_ordinal,
                    },
                )

    def _async_submit_fill_bitmask(
        self, batch: list[tuple[StructuredOutputGrammar, int, bool, str]]
    ) -> Future:
        return self.executor_for_fillmask.submit(self._fill_bitmasks, batch)

    def grammar_bitmask(
        self,
        requests: dict[str, "Request"],
        structured_output_request_ids: list[str],
        scheduled_spec_decode_tokens: dict[str, list[int]],
    ) -> "npt.NDArray[np.int32] | None":
        # Prepare the structured output bitmask for this batch.
        if not structured_output_request_ids:
            return None

        # Covers both speculative decoding and diffusion LLMs (canvas_length).
        max_num_spec_tokens = self.vllm_config.num_speculative_tokens

        if self._grammar_bitmask is None:
            assert self.backend is not None
            max_batch_size = self.vllm_config.scheduler_config.max_num_seqs

            # Allocate a bitmask for each token needing to be checked:
            # one for each speculative position, and one more for the
            # bonus token / non-speculative token.
            self._grammar_bitmask = self.backend.allocate_token_bitmask(
                max_batch_size * (1 + max_num_spec_tokens)
            )

        # Generate a batched bitmask for all structured output requests.
        # When speculative decoding is enabled, we need to include multiple
        # masks for each request, one for each possible bonus token position.
        # These are stored inline in the tensor and unpacked by the gpu runner.
        cumulative_index = 0

        # Optimized parallel filling of bitmasks for
        # non-spec, large-batch-size cases
        if (
            len(structured_output_request_ids) > self.fill_bitmask_parallel_threshold
            and max_num_spec_tokens == 0
        ):
            promises = []
            batch = []
            for req_id in structured_output_request_ids:
                request = requests[req_id]
                structured_output_request = request.structured_output_request
                if TYPE_CHECKING:
                    assert structured_output_request is not None
                grammar = structured_output_request.grammar
                if TYPE_CHECKING:
                    assert isinstance(grammar, StructuredOutputGrammar)

                apply_bitmask = self.should_fill_bitmask(request)
                batch.append((grammar, cumulative_index, apply_bitmask, req_id))
                if len(batch) == self.fill_bitmask_parallel_batch_size:
                    promises.append(self._async_submit_fill_bitmask(batch))
                    batch = []

                cumulative_index += 1
            if batch:
                promises.append(self._async_submit_fill_bitmask(batch))

            # Wait for all bitmask filling tasks to complete.
            for promise in promises:
                promise.result()
        else:
            # Fallback to serial filling of bitmasks for small-batch-size cases
            for req_id in structured_output_request_ids:
                request = requests[req_id]
                structured_output_request = request.structured_output_request

                if TYPE_CHECKING:
                    assert structured_output_request is not None
                grammar = structured_output_request.grammar
                if TYPE_CHECKING:
                    assert isinstance(grammar, StructuredOutputGrammar)
                apply_bitmask = self.should_fill_bitmask(request)

                reasoner = self._get_reasoner(request)
                detect_reasoning_end = (
                    not apply_bitmask
                    and reasoner is not None
                    and not self.enable_in_reasoning
                )
                simulated_buf: list[int] | None = None
                history_len = 0

                state_advancements = 0
                post_reasoning_end_in_window = False
                req_tokens = scheduled_spec_decode_tokens.get(req_id, ())
                for i, token in enumerate(req_tokens):
                    self._fill_bitmasks(
                        ((grammar, cumulative_index, apply_bitmask, req_id),)
                    )
                    advance_grammar = apply_bitmask
                    if token == -1:
                        apply_bitmask = False
                        advance_grammar = False
                    elif (
                        detect_reasoning_end
                        and reasoner is not None
                        and not apply_bitmask
                    ):
                        if simulated_buf is None:
                            history = list(request.all_token_ids)
                            history_len = len(history)
                            simulated_buf = history + list(req_tokens)
                        simulated = simulated_buf[: history_len + i + 1]
                        if reasoner.is_reasoning_end_streaming(simulated, [token]):
                            # Reasoning ended mid-window. Constrain the rest
                            # of the window via bitmask. Skip grammar advance
                            # through the marker (it is reasoning content);
                            # try to advance through subsequent drafts so the
                            # next bitmask row reflects the post-advance state,
                            # but tolerate rejection since those drafts predate
                            # the bitmask and are not guaranteed valid.
                            apply_bitmask = True
                            advance_grammar = False
                            post_reasoning_end_in_window = True
                    if advance_grammar and not grammar.is_terminated():
                        accepted = grammar.accept_tokens(req_id, [token])
                        if accepted:
                            state_advancements += 1
                        elif not post_reasoning_end_in_window:
                            raise AssertionError(
                                (token, req_id, scheduled_spec_decode_tokens)
                            )
                    cumulative_index += 1
                # Diffusion LLMs don't sample a bonus token after the
                # scheduled positions, so skip its bitmask in that case.
                if not (self.vllm_config.model_config.is_diffusion and req_tokens):
                    # bonus_apply must be True when the bonus-row position
                    # should be grammar-constrained. Two triggers:
                    # - should_fill_bitmask(request): reasoning was already
                    #   over at step start (or no reasoner /
                    #   enable_in_reasoning).
                    # - apply_bitmask: reasoning ended mid-window in this
                    #   call and was flipped True after the marker;
                    #   should_fill_bitmask still returns False here because
                    #   reasoning_ended is only persisted later by
                    #   should_advance.
                    bonus_apply = self.should_fill_bitmask(request) or apply_bitmask
                    self._fill_bitmasks(
                        ((grammar, cumulative_index, bonus_apply, req_id),)
                    )
                    cumulative_index += 1
                if state_advancements > 0:
                    grammar.rollback(state_advancements)

        bitmask_tensor = self._grammar_bitmask
        if cumulative_index < bitmask_tensor.shape[0]:
            bitmask_tensor = bitmask_tensor[:cumulative_index]

        # After finishing with the xgrammar operations, we convert to
        # np.ndarray, because that is much more efficient for serialization
        # and deserialization when sending this to the GPU workers.
        return bitmask_tensor.numpy()

    def should_fill_bitmask(self, request: "Request") -> bool:
        # NOTE (Hanchen) if enable_in_reasoning is True, it means that
        # the model needs to be constrained in reasoning. So we should always
        # enable the bitmask filling.
        reasoner = self._get_reasoner(request)
        if reasoner is not None:
            if self.enable_in_reasoning:
                return True
            assert request.structured_output_request is not None
            if request.structured_output_request.reasoning_ended is None:
                # This should be removed here, but since `openai_gptoss`
                # is an independent code path, it is kept for now.
                # After unifying the `openai_gptoss` and non-`openai_gptoss` styles,
                # it can be removed.
                request.structured_output_request.reasoning_ended = (
                    reasoner.is_reasoning_end(request.prompt_token_ids or [])
                )
            return request.structured_output_request.reasoning_ended
        return True

    def should_advance(self, request: "Request") -> bool:
        if not request.use_structured_output:
            return False

        # To determine whether we can advance the FSM.
        # Supports thinking usage where we skip the reasoning components.
        if TYPE_CHECKING:
            assert request.structured_output_request is not None
            assert request.structured_output_request.grammar is not None
        # by default, we should always advance
        # for cases that don't use thinking mode.
        reasoner = self._get_reasoner(request)
        if reasoner is None:
            return True

        # if the model needs structured in reasoning, we should advance
        if self.enable_in_reasoning:
            return True

        structured_req = request.structured_output_request
        if structured_req.reasoning_ended:
            return True

        # Check if reasoning ends in *this* step
        delta_from = request.num_computed_tokens - request.num_output_placeholders
        all_token_ids = request.all_token_ids
        start = (
            delta_from if delta_from >= 0 else max(len(all_token_ids) + delta_from, 0)
        )
        if reasoner.is_reasoning_end_streaming(
            all_token_ids, itertools.islice(all_token_ids, start, None)
        ):
            structured_req.reasoning_ended = True

            # Reasoning just ended this step. Defer FSM advance until the next
            # pass (see reasoning_ended check above) for JSON/regex/choice/grammar:
            # advancing on the closing boundary token can accept tokens that still
            # belong to the reasoning stream. Structural tags are the only safe
            # same-step exception: they model phased output (e.g. thinking tag ->
            # answer tag), and speculative decoding must run grammar.validate_tokens
            # on draft tokens produced immediately after that transition.
            if (
                self.vllm_config.speculative_config is not None
                and structured_req.structured_output_key[0]
                == StructuredOutputOptions.STRUCTURAL_TAG
            ):
                # The scheduler will advance the grammar with this step's
                # tokens right away, but the step still contains reasoning
                # content up to and including the end marker. Record where
                # it ends so trim_reasoning_for_advance() can drop it.
                structured_req.reasoning_end_token_index = (
                    self._find_reasoning_end_index(reasoner, all_token_ids, start)
                )
                return True

        return False

    @staticmethod
    def _find_reasoning_end_index(
        reasoner: "ReasoningParser", all_token_ids: Sequence[int], start: int
    ) -> int:
        """Locates the last reasoning token within ``all_token_ids[start:]``.

        Returns:
            The absolute index of the token at which
            ``is_reasoning_end_streaming`` first fires. Falls back to the
            final index when no single token triggers the detection (e.g.
            a multi-token marker only recognized on the full delta), which
            conservatively treats the whole step as reasoning content.
        """
        prefix = list(itertools.islice(all_token_ids, start))
        for idx in range(start, len(all_token_ids)):
            token = all_token_ids[idx]
            prefix.append(token)
            if reasoner.is_reasoning_end_streaming(prefix, [token]):
                return idx
        return len(all_token_ids) - 1

    def trim_reasoning_for_advance(
        self, request: "Request", new_token_ids: list[int]
    ) -> list[int]:
        """Drops reasoning content from tokens about to advance the grammar.

        When reasoning ends mid-step (see should_advance), the step's output
        still contains reasoning tokens up to and including the end marker.
        Those are not grammar content: feeding them to accept_tokens makes
        the grammar reject the marker and kills the request (#44006).

        Returns:
            The suffix of ``new_token_ids`` that follows the reasoning-end
            marker. Steps fully after the boundary are returned unchanged.
        """
        structured_req = request.structured_output_request
        if structured_req is None:
            return new_token_ids
        end_idx = structured_req.reasoning_end_token_index
        if end_idx is None:
            return new_token_ids
        first_idx = len(request.all_token_ids) - len(new_token_ids)
        num_reasoning = end_idx + 1 - first_idx
        if num_reasoning <= 0:
            return new_token_ids
        return new_token_ids[num_reasoning:]

    def clear_backend(self) -> None:
        try:
            if self.backend is not None:
                self.backend.destroy()
        finally:
            self.audit_sink.close()

    def audit_token_advance(
        self,
        request: "Request",
        token_ids: Sequence[int],
        *,
        accepted: bool,
    ) -> None:
        if not self._request_is_audited(request.request_id):
            return
        structured_request = request.structured_output_request
        grammar = structured_request.grammar if structured_request is not None else None
        grammar_terminated = (
            grammar.is_terminated()
            if isinstance(grammar, StructuredOutputGrammar)
            else None
        )
        self.audit_sink.record_event(
            request.request_id,
            "token_advance",
            {
                "accepted": accepted,
                "token_count": len(token_ids),
                "token_ids_sha256": hash_token_ids(token_ids),
                "grammar_terminated": grammar_terminated,
            },
        )

    def audit_draft_validation(
        self,
        request_id: str,
        proposed_token_ids: Sequence[int],
        accepted_token_ids: Sequence[int],
    ) -> None:
        if not self._request_is_audited(request_id):
            return
        self.audit_sink.record_event(
            request_id,
            "draft_validation",
            {
                "proposed_token_count": len(proposed_token_ids),
                "accepted_token_count": len(accepted_token_ids),
                "proposed_token_ids_sha256": hash_token_ids(proposed_token_ids),
                "accepted_token_ids_sha256": hash_token_ids(accepted_token_ids),
            },
        )

    def audit_binding_steps(
        self,
        observations: dict[str, bool] | None,
    ) -> None:
        if not self.binding_required or observations is None:
            return
        for request_id, bound in observations.items():
            sample_ordinal, mask_applied = (
                self.binding_tracker.consume_observation(request_id)
            )
            self.audit_sink.record_event(
                request_id,
                "binding_step",
                {
                    "sample_ordinal": sample_ordinal,
                    "mask_applied": mask_applied,
                    "evaluable": mask_applied,
                    "bound": bool(bound) if mask_applied else None,
                },
            )

    def audit_request_end(self, request: "Request") -> None:
        request_id = request.request_id
        if not self._request_is_audited(request_id):
            return
        pending_count = self.binding_tracker.finish_request(request_id)
        if pending_count:
            self.audit_sink.record_event(
                request_id,
                "binding_incomplete",
                {"pending_mask_count": pending_count},
            )
        try:
            structured_request = request.structured_output_request
            grammar = (
                structured_request.grammar
                if structured_request is not None
                else None
            )
            grammar_terminated = (
                grammar.is_terminated()
                if isinstance(grammar, StructuredOutputGrammar)
                else None
            )
            self.audit_sink.end_request(
                request_id,
                finish_reason=str(request.status),
                output_token_ids=request.output_token_ids,
                grammar_terminated=grammar_terminated,
            )
        finally:
            self._audited_request_ids.discard(request_id)
