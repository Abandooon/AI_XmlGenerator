"""Pinned V4 Chat Completions transport matched to AUTOSAR V20 settings."""

from __future__ import annotations

import importlib.metadata
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from urllib.parse import urlsplit

import yaml
import httpx
from openai import (
    APIConnectionError, APITimeoutError, ConflictError, InternalServerError,
    OpenAI, RateLimitError,
)

import pil_v4_contract as contract


ROOT = Path(__file__).resolve().parent


def normalize_base_url(url: str) -> str:
    value = str(url or "").strip().rstrip("/")
    if not value:
        raise ValueError("PIL V4 API base URL is not configured")
    if not value.startswith(("http://", "https://")):
        value = "https://" + value
    parsed = urlsplit(value)
    if parsed.path.rstrip("/").lower() == "/google":
        raise ValueError("PIL V4 refuses the legacy Google route")
    if not value.endswith("/v1"):
        value += "/v1"
    return value


class V4ChatCompletionsTransport:
    """Expose only the three low-level operations used by ``UnifiedV4Client``."""

    def __init__(self, *, api_key: str, base_url: str, transport: Any | None = None) -> None:
        if not str(api_key or "").strip():
            raise ValueError("PIL V4 API key is not configured")
        normalized = normalize_base_url(base_url)
        self.config = SimpleNamespace(
            model_name=contract.PROVIDER_PROTOCOL["model_name"],
            llm_api_url=normalized,
            api_key=str(api_key),
        )
        self.http_client = None
        if transport is None:
            self.http_client = httpx.Client(
                trust_env=False,
                timeout=contract.PROVIDER_PROTOCOL["request_timeout_seconds"],
            )
            self.client = OpenAI(
                api_key=str(api_key), base_url=normalized,
                max_retries=contract.PROVIDER_PROTOCOL["sdk_implicit_retries"],
                timeout=contract.PROVIDER_PROTOCOL["request_timeout_seconds"],
                http_client=self.http_client,
            )
            if int(self.client.max_retries) != 0:
                raise RuntimeError("PIL V4 SDK implicit retries are not disabled")
        else:
            self.client = transport
        self.last_attempt_audit: list[dict[str, Any]] = []
        try:
            sdk = importlib.metadata.version("openai")
        except importlib.metadata.PackageNotFoundError:
            sdk = "UNKNOWN"
        self.runtime_metadata = {
            **contract.PROVIDER_PROTOCOL,
            "structured_output_mode": "strict_json_schema_no_fallback",
            "posterior_schema_validation": "draft_2020_12",
            "client_library": "openai",
            "client_library_version": sdk,
        }

    @staticmethod
    def _usage(response: Any) -> tuple[int, int, int]:
        usage = getattr(response, "usage", None)
        input_tokens = int(
            getattr(usage, "prompt_tokens", 0)
            or getattr(usage, "input_tokens", 0) or 0
        )
        output_tokens = int(
            getattr(usage, "completion_tokens", 0)
            or getattr(usage, "output_tokens", 0) or 0
        )
        total_tokens = int(getattr(usage, "total_tokens", input_tokens + output_tokens) or input_tokens + output_tokens)
        return input_tokens, output_tokens, total_tokens

    @classmethod
    def _usage_record(cls, response: Any) -> dict[str, int]:
        input_tokens, output_tokens, total_tokens = cls._usage(response)
        return {"input_tokens": input_tokens, "output_tokens": output_tokens, "total_tokens": total_tokens}

    @staticmethod
    def _any_text(response: Any) -> str:
        choices = list(getattr(response, "choices", None) or [])
        if choices:
            return str(getattr(getattr(choices[0], "message", None), "content", "") or "")
        parts: list[str] = []
        for item in list(getattr(response, "output", None) or []):
            for content in list(getattr(item, "content", None) or []):
                text = getattr(content, "text", None)
                if isinstance(text, str) and text:
                    parts.append(text)
        return "".join(parts) or str(getattr(response, "output_text", "") or "")

    @classmethod
    def _output_text(cls, response: Any) -> str:
        choices = list(getattr(response, "choices", None) or [])
        if not choices:
            raise contract.ModelResultError(
                "PIL V4 response contained no chat choice",
                raw_text=cls._any_text(response), stage="empty_output",
                response_status="no_choice", usage=cls._usage_record(response),
            )
        choice = choices[0]
        finish_reason = str(getattr(choice, "finish_reason", "") or "")
        message = getattr(choice, "message", None)
        refusal = str(getattr(message, "refusal", "") or "")
        if refusal:
            raise contract.ModelResultError(
                "PIL V4 model refused the request", raw_text=refusal,
                stage="refusal", response_status=finish_reason,
                usage=cls._usage_record(response),
            )
        text = str(getattr(message, "content", "") or "")
        if finish_reason != "stop":
            raise contract.ModelResultError(
                f"PIL V4 response did not finish normally ({finish_reason or 'unknown'})",
                raw_text=text, stage="incomplete", response_status=finish_reason,
                usage=cls._usage_record(response),
            )
        if not text:
            raise contract.ModelResultError(
                "PIL V4 response contained no output text", raw_text="",
                stage="empty_output", response_status=finish_reason,
                usage=cls._usage_record(response),
            )
        return text

    @staticmethod
    def _is_retryable(error: BaseException) -> bool:
        if isinstance(error, (
            APIConnectionError, APITimeoutError, ConflictError,
            InternalServerError, RateLimitError,
        )):
            return True
        status = getattr(error, "status_code", None)
        return status in {408, 409, 429} or isinstance(status, int) and status >= 500

    @classmethod
    def _response_metadata(cls, response: Any, *, seed: int) -> dict[str, Any]:
        choices = list(getattr(response, "choices", None) or [])
        return {
            "requested_model": contract.PROVIDER_PROTOCOL["model_name"],
            "response_model": getattr(response, "model", None),
            "response_id": getattr(response, "id", None),
            "created": getattr(response, "created", None),
            "system_fingerprint": getattr(response, "system_fingerprint", None),
            "service_tier": getattr(response, "service_tier", None),
            "finish_reason": getattr(choices[0], "finish_reason", None) if choices else None,
            "seed": seed,
            "temperature": contract.PROVIDER_PROTOCOL["temperature"],
            "reasoning_effort": contract.PROVIDER_PROTOCOL["reasoning_effort"],
            "max_completion_tokens": contract.PROVIDER_PROTOCOL["max_completion_tokens"],
            "usage": cls._usage_record(response),
        }

    def _create_response(
        self, *, prompt: str, instructions: str,
        text: dict[str, Any] | None = None, seed: int,
    ) -> Any:
        request: dict[str, Any] = {
            "model": contract.PROVIDER_PROTOCOL["model_name"],
            "messages": [
                {"role": "system", "content": instructions},
                {"role": "user", "content": prompt},
            ],
            "temperature": contract.PROVIDER_PROTOCOL["temperature"],
            "max_completion_tokens": contract.PROVIDER_PROTOCOL["max_completion_tokens"],
            "reasoning_effort": contract.PROVIDER_PROTOCOL["reasoning_effort"],
            "seed": int(seed),
        }
        if text is not None:
            request["response_format"] = {
                "type": "json_schema",
                "json_schema": dict(text["format"]),
            }
            request["response_format"]["json_schema"].pop("type", None)
        request_sha256 = contract.canonical_sha256(request)
        attempts = int(contract.PROVIDER_PROTOCOL["application_transport_max_attempts"])
        delays = list(contract.PROVIDER_PROTOCOL["transport_retry_delays_seconds"])
        self.last_attempt_audit = []
        for attempt in range(1, attempts + 1):
            try:
                response = self.client.chat.completions.create(**request)
            except Exception as error:
                retryable = self._is_retryable(error)
                self.last_attempt_audit.append({
                    "transport_attempt": attempt,
                    "at_utc": datetime.now(timezone.utc).isoformat(),
                    "status": "FAILED",
                    "error_type": type(error).__name__,
                    "retryable": retryable,
                    "request_sha256": request_sha256,
                })
                if not retryable or attempt >= attempts:
                    failure = contract.InfrastructureError(
                        "PIL V4 request failed before returning a response"
                    )
                    setattr(failure, "transport_attempts", list(self.last_attempt_audit))
                    raise failure from error
                time.sleep(float(delays[attempt - 1]))
                continue
            self.last_attempt_audit.append({
                "transport_attempt": attempt,
                "at_utc": datetime.now(timezone.utc).isoformat(),
                "status": "RESPONSE_RECEIVED",
                "response_id": getattr(response, "id", None),
                "response_model": getattr(response, "model", None),
                "request_sha256": request_sha256,
            })
            expected_model = str(contract.PROVIDER_PROTOCOL["expected_response_model"])
            actual_model = str(getattr(response, "model", "") or "")
            if actual_model != expected_model:
                self.last_attempt_audit[-1]["status"] = "RESPONSE_MODEL_MISMATCH"
                failure = contract.InfrastructureError(
                    f"PIL V4 response model mismatch: expected {expected_model}, got {actual_model or 'UNKNOWN'}"
                )
                setattr(failure, "transport_attempts", list(self.last_attempt_audit))
                setattr(failure, "provider_response", self._response_metadata(response, seed=seed))
                setattr(failure, "usage", self._usage_record(response))
                raise failure
            return response
        raise AssertionError("unreachable transport loop")


def configured_base_url() -> str:
    config_path = ROOT.parent / "config" / "llm_api_config.yaml"
    configured: dict[str, Any] = {}
    if config_path.is_file():
        configured = dict((yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}).get("llm") or {})
    return normalize_base_url(
        os.getenv("PIL_LLM_API_BASE", "").strip()
        or os.getenv("OPENAI_BASE_URL", "").strip()
        or str(configured.get("llm_api_url") or "").strip()
    )


def create_experiment_client() -> V4ChatCompletionsTransport:
    override = os.getenv("PIL_LLM_MODEL_NAME", "").strip()
    if override and override != contract.PROVIDER_PROTOCOL["model_name"]:
        raise RuntimeError("PIL V4 model override was rejected")
    provider = os.getenv("PIL_LLM_PROVIDER", "openai-compatible").strip().lower()
    if provider not in {"openai", "openai-compatible"}:
        raise RuntimeError("PIL V4 provider override was rejected")
    config_path = ROOT.parent / "config" / "llm_api_config.yaml"
    configured: dict[str, Any] = {}
    if config_path.is_file():
        configured = dict((yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}).get("llm") or {})
    api_key = (
        os.getenv("PIL_LLM_API_KEY", "").strip()
        or os.getenv("OPENAI_API_KEY", "").strip()
        or os.getenv("LLM_API_KEY", "").strip()
        or str(configured.get("api_key") or "").strip()
    )
    return V4ChatCompletionsTransport(api_key=api_key, base_url=configured_base_url())


# Compatibility name for frozen pre-run tests; the implementation is Chat Completions.
V4ResponsesTransport = V4ChatCompletionsTransport
