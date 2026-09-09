# llm/openai_client.py
"""OpenAI-compatible client used by the AUTOSAR generation pipeline.

Formal runs require strict JSON Schema and fail closed. Legacy JSON-mode
recovery is reachable only when ``strict_json_schema`` is explicitly disabled.
"""

import hashlib
import json
import os
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List, Union

import httpx
from openai import OpenAI
from jsonschema import Draft202012Validator

from ..config import CONFIG
from ..utils.exceptions import LLMAPIError


class OpenAIClient:
    DIRECT_ROUTE_POLICY = "direct_no_environment_proxy"

    def __init__(self, *, pipeline_phase: str = "unassigned"):
        self.config = CONFIG.llm
        self.debug_mode = getattr(CONFIG, "debug_mode", False)
        self.default_max_retries = int(getattr(self.config, "max_retries", 3))
        self.rate_limit_sleep = 0.5
        raw_transport_delays = getattr(
            self.config,
            "transport_retry_delays_seconds",
            [1.0, 5.0, 15.0, 30.0, 60.0, 60.0, 60.0],
        )
        if not isinstance(raw_transport_delays, (list, tuple)):
            raise RuntimeError("transport retry delays must be an array")
        self.transport_retry_delays_seconds = tuple(
            float(value) for value in raw_transport_delays
        )
        if any(value < 0 for value in self.transport_retry_delays_seconds):
            raise RuntimeError("transport retry delays must be non-negative")
        if len(self.transport_retry_delays_seconds) < self.default_max_retries - 1:
            raise RuntimeError(
                "transport retry delay schedule is shorter than max attempts"
            )
        self.pipeline_phase = str(pipeline_phase or "unassigned")
        self.transport_route_policy = str(
            getattr(
                self.config,
                "transport_route_policy",
                self.DIRECT_ROUTE_POLICY,
            )
        )
        if self.transport_route_policy != self.DIRECT_ROUTE_POLICY:
            raise RuntimeError(
                "unsupported provider transport route policy: "
                f"{self.transport_route_policy}"
            )

        base = self._normalize_base(self.config.llm_api_url)
        self.provider_endpoint_sha256 = hashlib.sha256(
            base.encode("utf-8")
        ).hexdigest()
        # CloseAI 文档：Base URL 要带 /v1
        # 例如 https://api.openai-proxy.org/v1
        request_timeout = float(
            getattr(self.config, "request_timeout_seconds", 180)
        )
        # Formal AUTOSAR execution must not change route when a desktop VPN,
        # system proxy, shell-specific HTTP(S)_PROXY, or NO_PROXY value changes.
        # trust_env=False makes the application-level route deterministic.  The
        # policy name is frozen and emitted on every transition/audit record.
        self.http_client = httpx.Client(
            trust_env=False,
            timeout=request_timeout,
        )
        self.client = OpenAI(
            base_url=base,
            api_key=self.config.api_key,
            timeout=request_timeout,
            # The SDK retries connection errors, timeouts, 408/409/429 and 5xx
            # twice by default. Those hidden requests are invisible to the
            # experiment transition ledger and violate the frozen single-
            # execution contract. Pipeline attempts are governed separately.
            max_retries=0,
            http_client=self.http_client,
        )
        if int(self.client.max_retries) != 0:
            raise RuntimeError("provider SDK implicit retries are not disabled")

        self.call_count = 0
        self.total_tokens = 0
        self.success_count = 0
        self.error_count = 0
        self.response_audit: List[Dict[str, Any]] = []
        self.last_raw_schema_payload: Optional[Dict[str, Any]] = None
        self.last_raw_schema_status: str = "NOT_EVALUATED"

    # ---------- public APIs (与 GeminiClient 对齐) ----------

    def generate_with_schema(
        self,
        prompt: str,
        schema: Dict[str, Any],
        seed: Optional[int] = None,
        max_retries: Optional[int] = None,
        temperature: Optional[float] = None,
        document_files: Optional[Union[Any, List[Any]]] = None,  # 忽略，OpenAI 侧无需独立上传
        document_text: Optional[str] = None,
        context_info: Optional[str] = None
    ) -> Tuple[Dict[str, Any], int, int, int]:

        if not hasattr(self, "provider_endpoint_sha256"):
            config = getattr(self, "config", None)
            normalized = self._normalize_base(
                str(getattr(config, "llm_api_url", "") or "")
            )
            self.provider_endpoint_sha256 = hashlib.sha256(
                normalized.encode("utf-8")
            ).hexdigest()
        self.last_raw_schema_payload = None
        self.last_raw_schema_status = "NOT_EVALUATED"
        self._active_max_attempts = int(
            max_retries if max_retries is not None else self.default_max_retries
        )
        if self._active_max_attempts < 1:
            raise LLMAPIError("max_retries/max_attempts must be at least one")
        json_data, _, in_tok, out_tok, ttl = self._generate_with_schema_impl(
            prompt=prompt,
            schema=schema,
            seed=seed,
            max_retries=max_retries,
            temperature=temperature,
            document_text=document_text,
            context_info=context_info
        )
        self.last_raw_schema_payload = json.loads(
            json.dumps(json_data, ensure_ascii=False)
        )
        schema_errors = sorted(
            Draft202012Validator(schema).iter_errors(json_data),
            key=lambda error: list(error.absolute_path),
        )
        if schema_errors:
            self.last_raw_schema_status = "RAW_FAIL"
            first = schema_errors[0]
            location = "/".join(str(item) for item in first.absolute_path) or "<root>"
            raise LLMAPIError(
                f"provider JSON violates the requested schema at {location}: {first.message}"
            )
        self.last_raw_schema_status = "PASS"
        return json_data, in_tok, out_tok, ttl

    def generate_text(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        seed: Optional[int] = None,
        max_retries: Optional[int] = None,
        temperature: Optional[float] = None,
        document_files: Optional[Union[Any, List[Any]]] = None,
        document_text: Optional[str] = None
    ) -> Tuple[str, int, int, int]:

        max_retries = max_retries or self.default_max_retries
        full_prompt = prompt
        if system_message:
            full_prompt = f"<sys>{system_message}</sys>\n{full_prompt}"
        if document_text:
            full_prompt = f"参考文档：\n{document_text}\n\n{full_prompt}"

        for attempt in range(max_retries):
            try:
                if self.debug_mode and attempt > 0:
                    print(f"[DEBUG] Text retry {attempt+1}/{max_retries}")

                self.call_count += 1
                request = {
                    "model": self.config.model_name,
                    "temperature": (
                        self.config.temperature if temperature is None else temperature
                    ),
                    "max_completion_tokens": self.config.max_output_tokens,
                    "reasoning_effort": self.config.reasoning_effort,
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": full_prompt},
                    ],
                    "seed": seed,
                }
                if getattr(self.config, "stream_responses", False):
                    stream = self.client.chat.completions.create(
                        **request,
                        stream=True,
                        stream_options={"include_usage": True},
                    )
                    text, in_tok, out_tok, ttl_tok = self._consume_chat_stream(
                        stream,
                        response_format="text",
                        seed=seed,
                        temperature=request["temperature"],
                    )
                else:
                    resp = self.client.chat.completions.create(**request)
                    self._record_response_audit(
                        resp,
                        response_format="text",
                        seed=seed,
                        temperature=request["temperature"],
                    )
                    text = resp.choices[0].message.content or ""
                    in_tok, out_tok, ttl_tok = self._extract_usage(resp)
                self.total_tokens += ttl_tok
                self.success_count += 1
                return text, in_tok, out_tok, ttl_tok

            except Exception as e:
                self.error_count += 1
                if attempt < max_retries - 1:
                    time.sleep(self.rate_limit_sleep)
                else:
                    raise LLMAPIError(f"Text generation failed: {e}")

    # ---------- core implementation ----------

    def _generate_with_schema_impl(
        self,
        prompt: str,
        schema: Dict[str, Any],
        seed: Optional[int],
        max_retries: Optional[int],
        temperature: Optional[float],
        document_text: Optional[str],
        context_info: Optional[str],
        functions: Optional[List[str]] = None,  # 预留，当前不走函数调用
    ) -> Tuple[Dict[str, Any], Dict[str, Any], int, int, int]:
        """
        先尝试 Structured Outputs (json_schema) → 失败降级 JSON mode → 失败再走解析修复
        返回：(json_data, function_history, in_tok, out_tok, total_tok)
        """
        max_retries = max_retries or self.default_max_retries

        enhanced_prompt = prompt
        if document_text:
            enhanced_prompt = f"参考文档：\n{document_text}\n\n任务要求：\n{enhanced_prompt}"
        if context_info:
            enhanced_prompt = f"上下文信息：\n{context_info}\n\n{enhanced_prompt}"

        # 1) Structured Outputs（模型需支持，如 gpt-4o/4o-mini 2024-08-06+）
        # A logical schema-generation request may need more than one explicit
        # transport attempt.  Keep the logical identity stable across those
        # attempts while minting a fresh provider-call identity for every
        # dispatch.  This makes a transient network continuation auditable
        # without treating it as another experimental observation.  The SDK's
        # own implicit retry remains disabled (``max_retries=0`` above).
        logical_request_id = uuid.uuid4().hex
        for attempt in range(max_retries):
            try:
                if self.debug_mode and attempt > 0:
                    print(f"[DEBUG] SO retry {attempt+1}/{max_retries}")

                self.call_count += 1
                request = {
                    "model": self.config.model_name,
                    "temperature": (
                        self.config.temperature if temperature is None else temperature
                    ),
                    "max_completion_tokens": self.config.max_output_tokens,
                    "reasoning_effort": self.config.reasoning_effort,
                    "messages": [
                        {"role": "system", "content":
                         "You are an AUTOSAR assistant. Output ONLY JSON, strictly matching the schema."},
                        {"role": "user", "content": enhanced_prompt},
                    ],
                    "response_format": {
                        "type": "json_schema",
                        "json_schema": {
                            "name": "result",
                            "strict": True,
                            "schema": schema
                        }
                    },
                    "seed": seed,
                }
                # Recorded before the socket is touched, so a crash between here
                # and DISPATCH_STARTED is provably a request that never left.
                self._begin_provider_call(
                    logical_request_id=logical_request_id,
                    transport_attempt=attempt + 1,
                )
                self._persist_transition(
                    "PRE_DISPATCH",
                    response_format="json_schema",
                    seed=seed,
                    dispatch_started=False,
                )
                if getattr(self.config, "stream_responses", False):
                    self._persist_transition(
                        "DISPATCH_STARTED",
                        response_format="json_schema",
                        seed=seed,
                        dispatch_started=True,
                        request_acceptance_known=False,
                    )
                    stream = self.client.chat.completions.create(
                        **request,
                        stream=True,
                        stream_options={"include_usage": True},
                    )
                    text, in_tok, out_tok, ttl_tok = self._consume_chat_stream(
                        stream,
                        response_format="json_schema",
                        seed=seed,
                        temperature=request["temperature"],
                    )
                else:
                    self._persist_transition(
                        "DISPATCH_STARTED",
                        response_format="json_schema",
                        seed=seed,
                        dispatch_started=True,
                        request_acceptance_known=False,
                    )
                    resp = self.client.chat.completions.create(**request)
                    self._persist_transition(
                        "RESPONSE_RECEIVED",
                        response_format="json_schema",
                        seed=seed,
                        dispatch_started=True,
                        request_acceptance_known=True,
                        response_headers_received=True,
                        response_id=getattr(resp, "id", None),
                        response_model=getattr(resp, "model", None),
                    )
                    self._record_response_audit(
                        resp,
                        response_format="json_schema",
                        seed=seed,
                        temperature=request["temperature"],
                    )
                    text = resp.choices[0].message.content or ""
                    in_tok, out_tok, ttl_tok = self._extract_usage(resp)
                data = json.loads(text)

                self._persist_transition(
                    "LOCAL_AUDIT_PERSISTED",
                    response_format="json_schema",
                    seed=seed,
                    dispatch_started=True,
                    request_acceptance_known=True,
                    local_audit_persisted=True,
                )
                self.total_tokens += ttl_tok
                self.success_count += 1
                return data, {}, in_tok, out_tok, ttl_tok

            except Exception as e:
                self._persist_transition(
                    "CALL_FAILED",
                    response_format="json_schema",
                    seed=seed,
                    dispatch_started=True,
                    **self._transport_evidence(e),
                )
                self.error_count += 1
                # 常见：不支持 json_schema → 降级到 JSON mode
                last_error = e
                if self.debug_mode:
                    print(f"[DEBUG] Structured Outputs failed: {e}")
                if self._is_non_retryable_provider_error(e):
                    raise LLMAPIError(f"Generation failed: {e}") from e
                if getattr(self.config, "strict_json_schema", True):
                    if self._is_retryable_provider_error(e) and attempt < max_retries - 1:
                        delay_seconds = self._transport_retry_delay(attempt)
                        self._persist_transition(
                            "CONTINUATION_SCHEDULED",
                            response_format="json_schema",
                            seed=seed,
                            dispatch_started=False,
                            request_acceptance_known=False,
                            continuation_delay_seconds=delay_seconds,
                            continuation_reason=(
                                "typed_transient_transport_or_provider_status"
                            ),
                            next_transport_attempt=attempt + 2,
                        )
                        time.sleep(delay_seconds)
                        continue
                    raise LLMAPIError(
                        f"Strict JSON Schema generation failed: {e}"
                    ) from e
                break  # 直接降级（不少代理会报 400/参数不支持）

        # 2) JSON mode：只保证“返回 JSON 对象”，不保证 schema 严格一致
        text = ""
        resp = None
        for attempt in range(max_retries):
            try:
                if self.debug_mode and attempt > 0:
                    print(f"[DEBUG] JSON mode retry {attempt+1}/{max_retries}")

                self.call_count += 1
                resp = self.client.chat.completions.create(
                    model=self.config.model_name,
                    temperature=(
                        self.config.temperature if temperature is None else temperature
                    ),
                    max_completion_tokens=self.config.max_output_tokens,
                    reasoning_effort=self.config.reasoning_effort,
                    messages=[
                        {"role": "system", "content":
                         "You are an AUTOSAR assistant. Output ONLY a valid JSON object."},
                        {"role": "user", "content": enhanced_prompt},
                    ],
                    response_format={"type": "json_object"},
                    seed=seed
                )
                self._record_response_audit(
                    resp,
                    response_format="json_object",
                    seed=seed,
                    temperature=(
                        self.config.temperature if temperature is None else temperature
                    ),
                )
                text = resp.choices[0].message.content or ""

                try:
                    data = json.loads(text)
                except json.JSONDecodeError:
                    # 兜底修复 → 再解析
                    data = json.loads(self._repair_json_text(text))

                in_tok, out_tok, ttl_tok = self._extract_usage(resp)
                self.total_tokens += ttl_tok
                self.success_count += 1
                return data, {}, in_tok, out_tok, ttl_tok

            except Exception as e:
                self.error_count += 1
                last_error = e
                if self._is_non_retryable_provider_error(e):
                    raise LLMAPIError(f"Generation failed: {e}") from e
                if attempt < max_retries - 1:
                    time.sleep(self.rate_limit_sleep)
                else:
                    # 最后再做一遍“全文修复”尝试
                    try:
                        data = json.loads(self._repair_json_text(text))
                        if resp is None:
                            raise last_error
                        in_tok, out_tok, ttl_tok = self._extract_usage(resp)
                        self.total_tokens += ttl_tok
                        self.success_count += 1
                        return data, {}, in_tok, out_tok, ttl_tok
                    except Exception:
                        raise LLMAPIError(f"Generation failed: {last_error}")

    # ---------- helpers ----------

    @staticmethod
    def _is_non_retryable_provider_error(error: Exception) -> bool:
        """Reject authentication/payment/permission failures without fallback retries."""
        status_code = getattr(error, "status_code", None)
        return status_code in {401, 402, 403}

    @staticmethod
    def _is_retryable_provider_error(error: Exception) -> bool:
        """Retry transient failures without weakening structured output mode."""
        status_code = getattr(error, "status_code", None)
        if status_code in {408, 409, 429} or (
            isinstance(status_code, int) and status_code >= 500
        ):
            return True
        return type(error).__name__ in {
            "APIConnectionError",
            "APITimeoutError",
            "ConflictError",
            "InternalServerError",
            "RateLimitError",
        }

    def _transport_retry_delay(self, zero_based_attempt: int) -> float:
        """Return the preregistered delay before the next transport attempt.

        Tests and legacy callers that construct the client without ``__init__``
        retain the old ``rate_limit_sleep`` override.  Formal clients always
        carry the frozen delay schedule from configuration.
        """
        delays = getattr(self, "transport_retry_delays_seconds", None)
        if delays:
            position = min(max(int(zero_based_attempt), 0), len(delays) - 1)
            return float(delays[position])
        return float(getattr(self, "rate_limit_sleep", 0.5))

    def _normalize_base(self, url: str) -> str:
        if not url:
            return "https://api.openai-proxy.org/v1"
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        if not url.rstrip("/").endswith("/v1"):
            url = url.rstrip("/") + "/v1"
        return url

    def _record_response_audit(
        self,
        response: Any,
        *,
        response_format: str,
        seed: Optional[int],
        temperature: float,
    ) -> None:
        """Retain non-secret request/response identity for experiment audit."""

        response_audit = getattr(self, "response_audit", None)
        if response_audit is None:
            response_audit = []
            self.response_audit = response_audit
        input_tokens, output_tokens, total_tokens = self._extract_usage(response)
        record = {
            "call_index": len(self.response_audit) + 1,
            "provider_call_id": getattr(self, "_active_provider_call_id", None),
            "logical_request_id": getattr(self, "_active_logical_request_id", None),
            "pipeline_phase": getattr(self, "pipeline_phase", "unassigned"),
            "logical_call_index": int(getattr(self, "_logical_call_index", 0)),
            "transport_attempt": int(
                getattr(self, "_active_transport_attempt", 1)
            ),
            "sdk_attempt": 1,
            "requested_model": self.config.model_name,
            "response_model": getattr(response, "model", None),
            "response_id": getattr(response, "id", None),
            "created": getattr(response, "created", None),
            "system_fingerprint": getattr(response, "system_fingerprint", None),
            "service_tier": getattr(response, "service_tier", None),
            "finish_reason": (
                getattr(response.choices[0], "finish_reason", None)
                if getattr(response, "choices", None) else None
            ),
            "transport": "single_response",
            "response_format": response_format,
            "seed": seed,
            "temperature": temperature,
            "reasoning_effort": self.config.reasoning_effort,
            "max_completion_tokens": self.config.max_output_tokens,
            "request_timeout_seconds": float(
                getattr(self.config, "request_timeout_seconds", 180)
            ),
            "max_attempts": int(
                getattr(self, "_active_max_attempts", self.default_max_retries)
            ),
            "provider_endpoint_sha256": self.provider_endpoint_sha256,
            "transport_route_policy": getattr(
                self,
                "transport_route_policy",
                OpenAIClient.DIRECT_ROUTE_POLICY,
            ),
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
            },
            "credentials_included": False,
        }
        response_audit.append(record)
        self._persist_response_audit(record)

    def _consume_chat_stream(
        self,
        stream: Any,
        *,
        response_format: str,
        seed: Optional[int],
        temperature: float,
    ) -> Tuple[str, int, int, int]:
        """Collect one SSE chat completion without weakening schema enforcement."""

        parts: List[str] = []
        refusals: List[str] = []
        metadata: Dict[str, Any] = {
            "response_model": None,
            "response_id": None,
            "created": None,
            "system_fingerprint": None,
            "service_tier": None,
            "finish_reason": None,
        }
        usage = (0, 0, 0)
        for chunk in stream:
            for source, target in (
                ("model", "response_model"),
                ("id", "response_id"),
                ("created", "created"),
                ("system_fingerprint", "system_fingerprint"),
                ("service_tier", "service_tier"),
            ):
                value = getattr(chunk, source, None)
                if value is not None:
                    metadata[target] = value
            if getattr(chunk, "usage", None):
                usage = self._extract_usage(chunk)
            choices = getattr(chunk, "choices", None) or []
            if not choices:
                continue
            choice = choices[0]
            finish_reason = getattr(choice, "finish_reason", None)
            if finish_reason is not None:
                metadata["finish_reason"] = finish_reason
            delta = getattr(choice, "delta", None)
            content = getattr(delta, "content", None) if delta is not None else None
            if content:
                parts.append(content)
            refusal = getattr(delta, "refusal", None) if delta is not None else None
            if refusal:
                refusals.append(refusal)

        response_audit = getattr(self, "response_audit", None)
        if response_audit is None:
            response_audit = []
            self.response_audit = response_audit
        record = {
            "call_index": len(response_audit) + 1,
            "provider_call_id": getattr(self, "_active_provider_call_id", None),
            "logical_request_id": getattr(self, "_active_logical_request_id", None),
            "pipeline_phase": getattr(self, "pipeline_phase", "unassigned"),
            "logical_call_index": int(getattr(self, "_logical_call_index", 0)),
            "transport_attempt": int(
                getattr(self, "_active_transport_attempt", 1)
            ),
            "sdk_attempt": 1,
            "requested_model": self.config.model_name,
            **metadata,
            "response_format": response_format,
            "transport": "server_sent_events_stream",
            "seed": seed,
            "temperature": temperature,
            "reasoning_effort": self.config.reasoning_effort,
            "max_completion_tokens": self.config.max_output_tokens,
            "request_timeout_seconds": float(
                getattr(self.config, "request_timeout_seconds", 180)
            ),
            "max_attempts": int(
                getattr(self, "_active_max_attempts", self.default_max_retries)
            ),
            "provider_endpoint_sha256": self.provider_endpoint_sha256,
            "transport_route_policy": getattr(
                self,
                "transport_route_policy",
                OpenAIClient.DIRECT_ROUTE_POLICY,
            ),
            "usage": {
                "input_tokens": usage[0],
                "output_tokens": usage[1],
                "total_tokens": usage[2],
            },
            "credentials_included": False,
        }
        response_audit.append(record)
        self._persist_response_audit(record)
        if refusals:
            raise LLMAPIError("provider refused the streamed request")
        if metadata["finish_reason"] not in {None, "stop"}:
            raise LLMAPIError(
                f"streamed completion did not finish normally: {metadata['finish_reason']}"
            )
        text = "".join(parts)
        if not text:
            raise LLMAPIError("streamed completion returned no content")
        return text, *usage

    @staticmethod
    def _persist_response_audit(record: Dict[str, Any]) -> None:
        """Durably retain non-secret usage even if later local parsing fails."""

        raw_path = os.environ.get("ATLAS_PROVIDER_AUDIT_PATH")
        if not raw_path:
            return
        path = Path(raw_path).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())

    def _begin_provider_call(
        self,
        *,
        logical_request_id: Optional[str] = None,
        transport_attempt: int = 1,
    ) -> str:
        """Mint one dispatch identity inside a stable logical request.

        ``provider_call_id`` identifies one actual dispatch.  A transient
        application-level continuation receives a new provider-call identity,
        while ``logical_request_id`` and ``logical_call_index`` stay fixed.
        Consequently the evidence can distinguish network attempts from the
        single structured response that constitutes the experiment output.
        """
        if int(transport_attempt) < 1:
            raise ValueError("transport_attempt must be at least one")
        logical_request_id = str(logical_request_id or uuid.uuid4().hex)
        # Round 1 and Round 2 own separate client objects but append to one
        # run-scoped ledger. Derive the next logical index from that shared
        # ledger so the sequence cannot restart when the client instance
        # changes, and so retries of one logical request retain the same index.
        logical_index = 1
        raw_path = os.environ.get("ATLAS_PROVIDER_TRANSITION_LEDGER_PATH")
        if raw_path:
            path = Path(raw_path)
            if path.is_file():
                observed_logical_indexes: Dict[str, int] = {}
                for line in path.read_text(
                    encoding="utf-8", errors="replace"
                ).splitlines():
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    observed_logical_id = str(
                        row.get("logical_request_id")
                        or row.get("provider_call_id")
                        or ""
                    )
                    observed_index = int(row.get("logical_call_index") or 0)
                    if observed_logical_id and observed_index > 0:
                        observed_logical_indexes.setdefault(
                            observed_logical_id, observed_index
                        )
                if logical_request_id in observed_logical_indexes:
                    logical_index = observed_logical_indexes[logical_request_id]
                elif observed_logical_indexes:
                    logical_index = max(observed_logical_indexes.values()) + 1
        self._logical_call_index = logical_index
        self._active_logical_request_id = logical_request_id
        self._active_transport_attempt = int(transport_attempt)
        self._active_provider_call_id = uuid.uuid4().hex
        return self._active_provider_call_id

    def _persist_transition(self, stage: str, **fields: Any) -> None:
        """Append one provider-call stage to a crash-visible ledger.

        The response audit is only written once a response exists, so a call
        that fails in transport leaves no local trace at all.  A reader then
        cannot tell a request that never left the client from one the provider
        may have served -- which is how three V16 pilot slots were recorded as
        generation failures.

        This ledger records the stages themselves, so the last durable stage is
        readable after a crash.  It carries identity and outcome only: never a
        credential, never the request body, never anything a credential could be
        reconstructed from.  Emitting ``DISPATCH_STARTED`` is not a claim that
        the provider accepted the request; only a recorded response is.
        """
        raw_path = os.environ.get("ATLAS_PROVIDER_TRANSITION_LEDGER_PATH")
        if not raw_path:
            audit_path = os.environ.get("ATLAS_PROVIDER_AUDIT_PATH")
            if not audit_path:
                return
            raw_path = str(
                Path(audit_path).with_name("provider_call_transitions.jsonl")
            )
        record = {
            "schema_version": "atlas.provider_call_transition.v2",
            "stage": stage,
            "at_utc": datetime.now(timezone.utc).isoformat(),
            # A call is identified by an id minted before dispatch, not by a
            # count of already-recorded responses.  The counter advanced when
            # the response audit was appended, so one call's stages were
            # numbered 1, 1, 1, 2; and Round 1 and Round 2 use separate client
            # instances that share one ledger, so both restarted at 1.  Neither
            # the stages of a call nor the calls of a run could be reassembled.
            "provider_call_id": getattr(self, "_active_provider_call_id", None),
            "logical_request_id": getattr(self, "_active_logical_request_id", None),
            "pipeline_phase": getattr(self, "pipeline_phase", "unassigned"),
            "logical_call_index": int(
                getattr(self, "_logical_call_index", 0)
            ),
            "transport_attempt": int(
                getattr(self, "_active_transport_attempt", 1)
            ),
            "sdk_attempt": 1,
            "requested_model": self.config.model_name,
            "provider_endpoint_sha256": self.provider_endpoint_sha256,
            "transport_route_policy": getattr(
                self,
                "transport_route_policy",
                OpenAIClient.DIRECT_ROUTE_POLICY,
            ),
            "request_timeout_seconds": float(
                getattr(self.config, "request_timeout_seconds", 180)
            ),
            "max_attempts": int(
                getattr(self, "_active_max_attempts", self.default_max_retries)
            ),
            "credentials_included": False,
            "request_body_included": False,
            **fields,
        }
        path = Path(raw_path).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())

    @staticmethod
    def _transport_evidence(error: BaseException) -> Dict[str, Any]:
        """Structured evidence about a failed call, for the classifier.

        The exception's own class and HTTP status are recorded so that
        classification never has to guess from message text.
        """
        status = getattr(error, "status_code", None)
        if status is None:
            response = getattr(error, "response", None)
            status = getattr(response, "status_code", None)
        underlying = getattr(error, "__cause__", None)
        if underlying is None:
            underlying = getattr(error, "__context__", None)
        return {
            "exception_type": type(error).__name__,
            "underlying_exception_type": (
                type(underlying).__name__ if underlying is not None else None
            ),
            "http_status": int(status) if isinstance(status, int) else None,
            "response_headers_received": bool(
                getattr(getattr(error, "response", None), "headers", None)
            ),
            "provider_request_id": getattr(error, "request_id", None),
        }

    def _extract_usage(self, resp) -> Tuple[int, int, int]:
        """
        兼容 chat.completions / responses 两种结构
        """
        try:
            # chat.completions
            if hasattr(resp, "usage") and resp.usage:
                pt = getattr(resp.usage, "prompt_tokens", 0) or getattr(resp.usage, "input_tokens", 0) or 0
                ct = getattr(resp.usage, "completion_tokens", 0) or getattr(resp.usage, "output_tokens", 0) or 0
                tt = getattr(resp.usage, "total_tokens", pt + ct)
                return pt, ct, tt
        except Exception:
            pass
        return 0, 0, 0

    def _enhance_prompt_for_json(self, prompt: str) -> str:
        return f"""
Return ONLY JSON matching the schema. 
No prose, no markdown. Escape quotes, use \\n for line breaks.
{prompt}
""".strip()

    # —— 以下是“宽松修复”以提高健壮性（解决 Unterminated string 等）
    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        try:
            return json.loads(text)
        except Exception:
            pass
        for pattern in [r'```json\s*(.*?)\s*```', r'```\s*(.*?)\s*```', r'\{[\s\S]*\}']:
            for m in re.findall(pattern, text, re.DOTALL):
                c = m.strip()
                for cand in (c, self._repair_json_text(c)):
                    try:
                        return json.loads(cand)
                    except Exception:
                        continue
        repaired = self._repair_json_text(text)
        return json.loads(repaired)

    def _repair_json_text(self, text: str) -> str:
        import re
        t = re.sub(r"```json\s*([\s\S]*?)\s*```", r"\1", text)
        t = re.sub(r"```\s*([\s\S]*?)\s*```", r"\1", t)
        if "{" in t and "}" in t:
            t = t[t.find("{"): t.rfind("}") + 1]
        t = t.replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'")
        t = re.sub(r",(\s*[}\]])", r"\1", t)  # 尾逗号
        out, in_str, esc = [], False, False
        for ch in t:
            if in_str:
                if esc:
                    out.append(ch); esc = False
                else:
                    if ch == "\\":
                        out.append(ch); esc = True
                    elif ch in ("\n", "\r"):
                        out.append("\\n")
                    else:
                        out.append(ch)
                if not esc and ch == '"':
                    in_str = False
            else:
                out.append(ch)
                if ch == '"':
                    in_str, esc = True, False
        return "".join(out)
