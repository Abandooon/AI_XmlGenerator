"""Strict ATLAS client contract for the pinned vLLM v0.26.0 experiment."""

from __future__ import annotations

import hashlib
import inspect
import string
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Mapping


class VllmProtocolError(RuntimeError):
    """Raised when the server request or response is not scientifically usable."""


class PosteriorValidationError(VllmProtocolError):
    """Raised when deterministic posterior validation does not return PASS."""


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class VllmExperimentConfig:
    endpoint: str
    model: str
    max_tokens: int = 16_384
    temperature: float = 0.0
    top_p: float = 1.0
    timeout_seconds: float = 600.0
    max_model_len: int = 131_072

    def __post_init__(self) -> None:
        endpoint = self.endpoint.strip().rstrip("/")
        model = self.model.strip()
        if not endpoint.startswith(("http://", "https://")):
            raise ValueError("endpoint_must_be_http_url")
        if not model:
            raise ValueError("model_must_be_explicit")
        if self.max_tokens <= 0:
            raise ValueError("max_tokens_must_be_positive")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_must_be_positive")
        if self.max_model_len <= 0:
            raise ValueError("max_model_len_must_be_positive")
        if self.max_tokens > self.max_model_len:
            raise ValueError("max_tokens_exceed_max_model_len")
        object.__setattr__(self, "endpoint", endpoint)
        object.__setattr__(self, "model", model)


def build_completion_payload(
    config: VllmExperimentConfig,
    *,
    prompt: str,
    grammar: str,
) -> dict[str, Any]:
    if not prompt.strip():
        raise VllmProtocolError("prompt_is_empty")
    if not grammar.strip():
        raise VllmProtocolError("grammar_is_empty")
    return {
        "model": config.model,
        "prompt": prompt,
        "max_tokens": config.max_tokens,
        "temperature": config.temperature,
        "top_p": config.top_p,
        "stream": False,
        # vLLM v0.26.0 validates Lark/EBNF and converts supported Lark grammar
        # to XGrammar EBNF. Do not use the removed guided_grammar extension.
        "structured_outputs": {"grammar": grammar},
    }


def parse_completion_response(
    response: Mapping[str, Any],
    *,
    allowed_finish_reasons: tuple[str, ...] = ("stop",),
    allow_empty_text: bool = False,
) -> dict[str, Any]:
    choices = response.get("choices")
    if not isinstance(choices, list) or len(choices) != 1:
        raise VllmProtocolError("response_must_contain_exactly_one_choice")
    choice = choices[0]
    if not isinstance(choice, Mapping):
        raise VllmProtocolError("choice_must_be_object")
    text = choice.get("text")
    if not isinstance(text, str) or (not allow_empty_text and not text.strip()):
        raise VllmProtocolError("completion_text_is_empty")
    finish_reason = str(choice.get("finish_reason") or "")
    if finish_reason not in allowed_finish_reasons:
        detail = finish_reason or "missing"
        raise VllmProtocolError(f"incomplete_finish_reason:{detail}")

    usage = response.get("usage") or {}
    if not isinstance(usage, Mapping):
        raise VllmProtocolError("usage_must_be_object")
    raw_usage = (
        usage.get("prompt_tokens"),
        usage.get("completion_tokens"),
        usage.get("total_tokens"),
    )
    if any(
        not isinstance(value, int) or isinstance(value, bool)
        for value in raw_usage
    ):
        raise VllmProtocolError("usage_tokens_must_be_integers")
    prompt_tokens, completion_tokens, total_tokens = raw_usage
    if min(prompt_tokens, completion_tokens, total_tokens) < 0:
        raise VllmProtocolError("usage_tokens_must_be_nonnegative")
    if total_tokens and total_tokens != prompt_tokens + completion_tokens:
        raise VllmProtocolError("usage_total_token_mismatch")
    return {
        "text": text,
        "finish_reason": finish_reason,
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
        },
        "response_id": str(response.get("id") or ""),
    }


class StrictVllmClient:
    def __init__(self, config: VllmExperimentConfig) -> None:
        self.config = config

    async def generate(self, *, prompt: str, grammar: str) -> dict[str, Any]:
        import aiohttp

        payload = build_completion_payload(
            self.config,
            prompt=prompt,
            grammar=grammar,
        )
        timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{self.config.endpoint}/v1/completions",
                    json=payload,
                ) as response:
                    if response.status != 200:
                        # Do not echo provider/server bodies: they may contain
                        # prompts, grammar text, paths, or deployment details.
                        raise VllmProtocolError(
                            f"vllm_http_status:{response.status}"
                        )
                    value = await response.json()
        except VllmProtocolError:
            raise
        except Exception as exc:
            raise VllmProtocolError("vllm_request_failed") from exc
        if not isinstance(value, Mapping):
            raise VllmProtocolError("response_root_must_be_object")
        return parse_completion_response(value)

    async def generate_and_validate(
        self,
        *,
        prompt: str,
        grammar: str,
        validator: Callable[[str], Mapping[str, Any] | Awaitable[Mapping[str, Any]]],
        context_sha256: str,
    ) -> dict[str, Any]:
        if len(context_sha256) != 64 or any(
            character not in string.hexdigits for character in context_sha256
        ):
            raise ValueError("context_sha256_must_be_64_hex_characters")
        completion = await self.generate(prompt=prompt, grammar=grammar)
        validation = validator(completion["text"])
        if inspect.isawaitable(validation):
            validation = await validation
        if not isinstance(validation, Mapping):
            raise PosteriorValidationError("validator_result_must_be_object")
        decision = str(validation.get("decision") or "NOT_EVALUATED")
        if decision != "PASS":
            raise PosteriorValidationError(
                f"posterior_validation_not_pass:{decision}"
            )
        return {
            "status": "PASS",
            "model": self.config.model,
            "prompt_sha256": sha256_text(prompt),
            "grammar_sha256": sha256_text(grammar),
            "context_sha256": context_sha256,
            "output_sha256": sha256_text(completion["text"]),
            "finish_reason": completion["finish_reason"],
            "usage": completion["usage"],
            "response_id": completion["response_id"],
            "validation": dict(validation),
            "output": completion["text"],
        }
