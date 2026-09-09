"""One request surface for both soft-JSON and strict-schema PIL V4 arms."""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

from jsonschema import Draft202012Validator

import pil_v4_contract as contract

COMMON_SYSTEM_INSTRUCTIONS = (
    "Use only the supplied case facts. When retrieved legal evidence is supplied, cite "
    "only that evidence. When no legal evidence is supplied, you may rely on your legal "
    "knowledge but must not invent facts or authorities. Return one JSON object matching "
    "the requested semantic fields, and write every natural-language string value in "
    "English. When facts are insufficient, explicitly abstain."
)


def provider_schema(schema: Mapping[str, Any]) -> dict[str, Any]:
    """Project metadata/unsupported posterior keywords without changing semantics."""
    def project(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: project(item)
                for key, item in value.items()
                if key not in {"$id", "$schema", "uniqueItems"}
            }
        if isinstance(value, list):
            return [project(item) for item in value]
        return copy.deepcopy(value)

    return project(dict(schema))


@dataclass(frozen=True)
class Generation:
    raw_text: str
    parsed: dict[str, Any] | None
    input_tokens: int
    output_tokens: int
    total_tokens: int
    provider_schema_enforced: bool
    seed: int
    provider_response: dict[str, Any]
    transport_attempts: tuple[dict[str, Any], ...]


class UnifiedV4Client:
    """Use identical system instructions; vary only provider schema enforcement."""

    def __init__(self, base_client: Any) -> None:
        for attr in ("_create_response", "_output_text", "_usage"):
            if not callable(getattr(base_client, attr, None)):
                raise TypeError(f"base client does not expose required method {attr}")
        self.base = base_client
        self.config = getattr(base_client, "config", None)
        self.runtime_metadata = {
            **dict(getattr(base_client, "runtime_metadata", {}) or {}),
            "v4_common_system_instructions_sha256": hashlib.sha256(
                COMMON_SYSTEM_INSTRUCTIONS.encode("utf-8")
            ).hexdigest(),
            "v4_soft_json_policy": "exact_json_object_no_fence_repair",
        }

    def generate(
        self, prompt: str, *, schema: Mapping[str, Any] | None, seed: int,
    ) -> Generation:
        text_config: dict[str, Any] | None = None
        if schema is not None:
            Draft202012Validator.check_schema(dict(schema))
            projected = provider_schema(schema)
            name = "pil_v4_" + hashlib.sha256(
                json.dumps(projected, sort_keys=True).encode("utf-8")
            ).hexdigest()[:16]
            text_config = {
                "format": {
                    "type": "json_schema",
                    "name": name,
                    "strict": True,
                    "schema": projected,
                }
            }
        response = self.base._create_response(
            prompt=prompt,
            instructions=COMMON_SYSTEM_INSTRUCTIONS,
            text=text_config,
            seed=int(seed),
        )
        try:
            raw = self.base._output_text(response)
        except contract.ModelResultError as error:
            setattr(
                error, "transport_attempts",
                list(getattr(self.base, "last_attempt_audit", []) or []),
            )
            setattr(
                error, "provider_response",
                self._response_metadata(response, seed=int(seed)),
            )
            raise
        input_tokens, output_tokens, total_tokens = self.base._usage(response)
        provider_response = self._response_metadata(response, seed=int(seed))
        transport_attempts = list(getattr(self.base, "last_attempt_audit", []) or [])
        parsed: dict[str, Any] | None = None
        if schema is not None:
            try:
                candidate = json.loads(raw)
            except json.JSONDecodeError as error:
                self._raise_response_error(
                    "Strict structured output was not JSON.", raw, "json_decode",
                    input_tokens, output_tokens, total_tokens, error,
                    provider_response=provider_response,
                    transport_attempts=transport_attempts,
                )
            if not isinstance(candidate, dict):
                self._raise_response_error(
                    "Strict structured output root was not an object.", raw, "posterior_schema",
                    input_tokens, output_tokens, total_tokens,
                    provider_response=provider_response,
                    transport_attempts=transport_attempts,
                )
            errors = sorted(
                Draft202012Validator(dict(schema)).iter_errors(candidate),
                key=lambda item: list(item.absolute_path),
            )
            if errors:
                self._raise_response_error(
                    "Strict output failed authoritative posterior schema validation.",
                    raw, "posterior_schema", input_tokens, output_tokens, total_tokens,
                    schema_errors=[item.message[:200] for item in errors], parsed=candidate,
                    provider_response=provider_response,
                    transport_attempts=transport_attempts,
                )
            parsed = candidate
        return Generation(
            raw, parsed, input_tokens, output_tokens, total_tokens,
            schema is not None, int(seed),
            provider_response, tuple(transport_attempts),
        )

    def _response_metadata(self, response: Any, *, seed: int) -> dict[str, Any]:
        getter = getattr(self.base, "_response_metadata", None)
        if callable(getter):
            return dict(getter(response, seed=seed))
        return {
            "requested_model": getattr(self.config, "model_name", None),
            "response_model": getattr(response, "model", None),
            "seed": seed,
        }

    @staticmethod
    def _raise_response_error(
        message: str,
        raw: str,
        stage: str,
        input_tokens: int,
        output_tokens: int,
        total_tokens: int,
        cause: BaseException | None = None,
        *,
        schema_errors: list[str] | None = None,
        parsed: Any = None,
        provider_response: Mapping[str, Any] | None = None,
        transport_attempts: list[dict[str, Any]] | None = None,
    ) -> None:
        error = contract.ModelResultError(
            message,
            raw_text=raw,
            parsed=parsed,
            schema_errors=schema_errors or (),
            stage=stage,
            response_status="completed",
            usage={
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
            },
        )
        setattr(error, "provider_response", dict(provider_response or {}))
        setattr(error, "transport_attempts", list(transport_attempts or []))
        if cause is not None:
            raise error from cause
        raise error
