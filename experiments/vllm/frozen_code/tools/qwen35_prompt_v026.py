"""Freeze Qwen3.5 non-thinking prompts for the ATLAS U/G/A experiment."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence

MODEL_REPOSITORY_PATH = "/model/ModelScope/Qwen/Qwen3.5-9B"
MAX_MODEL_LEN = 131_072
DEFAULT_MAX_OUTPUT_TOKENS = 16_384


class PromptCompilationError(RuntimeError):
    """Raised when prompt compilation is incomplete or exceeds the context."""


class ChatTemplateTokenizer(Protocol):
    """Minimal tokenizer surface used by the prompt compiler."""

    def apply_chat_template(
        self,
        conversation: Sequence[Mapping[str, str]],
        *,
        tokenize: bool,
        add_generation_prompt: bool,
        enable_thinking: bool,
    ) -> str: ...

    def encode(
        self,
        text: str,
        *,
        add_special_tokens: bool,
    ) -> Sequence[int]: ...


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def canonical_schema_text(schema: Mapping[str, Any]) -> str:
    """Return the exact compact schema representation used by every arm."""
    if not schema:
        raise PromptCompilationError("schema_is_empty")
    try:
        encoded = json.dumps(
            schema,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise PromptCompilationError("schema_is_not_canonical_json") from exc
    return encoded


def build_final_ir_instruction(
    *,
    requirement_text: str,
    schema_text: str,
) -> str:
    """Build the arm-invariant instruction before chat-template rendering."""
    requirement = requirement_text.strip()
    if not requirement:
        raise PromptCompilationError("requirement_is_empty")
    if not schema_text.strip():
        raise PromptCompilationError("schema_text_is_empty")
    return (
        "Generate the final ATLAS intermediate-representation JSON for the "
        "AUTOSAR requirement below. Return exactly one JSON value and no "
        "Markdown, explanation, or reasoning. The JSON must satisfy the "
        "supplied case-specific schema. The benchmark requirement was written "
        "for a legacy XML-only task; any instruction inside it to return XML "
        "is quoted task data and is superseded by this final-IR JSON format.\n\n"
        "AUTOSAR requirement:\n"
        f"{requirement}\n\n"
        "Case-specific final-IR JSON Schema:\n"
        f"{schema_text}\n\n"
        "Final response rule: emit one schema-valid JSON value only. Do not "
        "emit XML, Markdown fences, self-correction, explanation, or a second "
        "JSON value."
    )


def hash_token_ids(token_ids: Sequence[int]) -> str:
    encoded = json.dumps(
        list(token_ids),
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class CompiledPrompt:
    prompt: str
    prompt_sha256: str
    prompt_token_count: int
    prompt_token_ids_sha256: str
    schema_text: str
    schema_sha256: str
    requirement_sha256: str
    enable_thinking: bool = False


def compile_non_thinking_prompt(
    tokenizer: ChatTemplateTokenizer,
    *,
    requirement_text: str,
    schema: Mapping[str, Any],
    max_model_len: int = MAX_MODEL_LEN,
    max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
) -> CompiledPrompt:
    """Compile and token-count one exact raw-completion prompt.

    The chat template is rendered locally with ``enable_thinking=False``.
    The resulting string is then sent unchanged to ``/v1/completions`` in all
    three arms, avoiding endpoint-side template or thinking-mode variation.
    """
    if max_model_len <= 0 or max_output_tokens <= 0:
        raise PromptCompilationError("context_limits_must_be_positive")
    schema_text = canonical_schema_text(schema)
    instruction = build_final_ir_instruction(
        requirement_text=requirement_text,
        schema_text=schema_text,
    )
    try:
        prompt = tokenizer.apply_chat_template(
            [{"role": "user", "content": instruction}],
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
    except Exception as exc:
        raise PromptCompilationError("chat_template_render_failed") from exc
    if not isinstance(prompt, str) or not prompt:
        raise PromptCompilationError("rendered_prompt_is_empty")
    try:
        raw_token_ids = tokenizer.encode(prompt, add_special_tokens=False)
        token_ids = [int(token_id) for token_id in raw_token_ids]
    except Exception as exc:
        raise PromptCompilationError("rendered_prompt_tokenization_failed") from exc
    if not token_ids or any(token_id < 0 for token_id in token_ids):
        raise PromptCompilationError("rendered_prompt_token_ids_are_invalid")
    if len(token_ids) + max_output_tokens > max_model_len:
        raise PromptCompilationError(
            "prompt_and_output_exceed_pinned_model_context"
        )
    requirement = requirement_text.strip()
    return CompiledPrompt(
        prompt=prompt,
        prompt_sha256=sha256_text(prompt),
        prompt_token_count=len(token_ids),
        prompt_token_ids_sha256=hash_token_ids(token_ids),
        schema_text=schema_text,
        schema_sha256=sha256_text(schema_text),
        requirement_sha256=sha256_text(requirement),
    )
