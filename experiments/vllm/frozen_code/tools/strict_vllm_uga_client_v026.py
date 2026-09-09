"""Strict request construction for the ATLAS vLLM U/G/A experiment."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Literal, Mapping

from strict_vllm_client_v026 import (
    VllmExperimentConfig,
    VllmProtocolError,
    parse_completion_response,
)

UgaArm = Literal["U", "G", "A"]
REQUEST_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}")


def canonical_schema_sha256(schema: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        schema,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_uga_completion_payload(
    config: VllmExperimentConfig,
    *,
    arm: UgaArm,
    prompt: str,
    schema: Mapping[str, Any],
    seed: int,
    request_id: str,
) -> dict[str, Any]:
    """Build one arm while holding all non-mechanism fields fixed."""
    if arm not in ("U", "G", "A"):
        raise VllmProtocolError("unknown_uga_arm")
    if not prompt.strip():
        raise VllmProtocolError("prompt_is_empty")
    if not schema:
        raise VllmProtocolError("schema_is_empty")
    if seed < 0:
        raise VllmProtocolError("seed_must_be_nonnegative")
    if REQUEST_ID_PATTERN.fullmatch(request_id) is None:
        raise VllmProtocolError("request_id_is_not_stable_ascii")
    if config.temperature != 0.0:
        raise VllmProtocolError("uga_requires_temperature_zero")
    if config.top_p != 1.0:
        raise VllmProtocolError("uga_requires_top_p_one")

    payload: dict[str, Any] = {
        "model": config.model,
        "prompt": prompt,
        "max_tokens": config.max_tokens,
        "temperature": config.temperature,
        "top_p": config.top_p,
        "seed": seed,
        "stream": False,
        "request_id": request_id,
        "return_token_ids": True,
        "add_special_tokens": False,
    }
    if arm in ("G", "A"):
        payload["structured_outputs"] = {
            "json": dict(schema),
            "atlas_audit_binding": arm == "A",
        }
        if arm == "A":
            payload["structured_outputs"]["atlas_audit_request_id"] = (
                f"cmpl-{request_id}-0"
            )
    return payload


def request_identity(
    *,
    arm: UgaArm,
    prompt: str,
    schema: Mapping[str, Any],
    seed: int,
    request_id: str,
    config: VllmExperimentConfig,
    prompt_token_count: int,
    prompt_token_ids_sha256: str,
) -> dict[str, Any]:
    """Return content identities without persisting prompt or schema text."""
    if arm not in ("U", "G", "A"):
        raise VllmProtocolError("unknown_uga_arm")
    if prompt_token_count <= 0:
        raise VllmProtocolError("prompt_token_count_must_be_positive")
    if not re.fullmatch(r"[0-9a-f]{64}", prompt_token_ids_sha256):
        raise VllmProtocolError("prompt_token_ids_sha256_must_be_64_hex")
    return {
        "arm": arm,
        "request_id": request_id,
        "audit_request_id": f"cmpl-{request_id}-0",
        "model": config.model,
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "prompt_token_count": prompt_token_count,
        "prompt_token_ids_sha256": prompt_token_ids_sha256,
        "schema_sha256": canonical_schema_sha256(schema),
        "seed": seed,
        "max_tokens": config.max_tokens,
        "max_model_len": config.max_model_len,
        "temperature": config.temperature,
        "top_p": config.top_p,
    }


def parse_uga_completion_response(
    response: Mapping[str, Any],
    *,
    request_id: str,
) -> dict[str, Any]:
    """Parse one response and verify its client-supplied identity."""
    parsed = parse_completion_response(
        response,
        allowed_finish_reasons=("stop", "length"),
        allow_empty_text=True,
    )
    expected_response_id = f"cmpl-{request_id}"
    if parsed["response_id"] != expected_response_id:
        raise VllmProtocolError("response_id_does_not_match_request_id")
    choice = response["choices"][0]
    prompt_token_ids = choice.get("prompt_token_ids")
    output_token_ids = choice.get("token_ids")
    if not isinstance(prompt_token_ids, list) or not prompt_token_ids:
        raise VllmProtocolError("prompt_token_ids_missing")
    if not isinstance(output_token_ids, list):
        raise VllmProtocolError("output_token_ids_missing")
    try:
        prompt_ids = [int(token_id) for token_id in prompt_token_ids]
        output_ids = [int(token_id) for token_id in output_token_ids]
    except (TypeError, ValueError) as exc:
        raise VllmProtocolError("response_token_ids_must_be_integers") from exc
    if any(token_id < 0 for token_id in (*prompt_ids, *output_ids)):
        raise VllmProtocolError("response_token_ids_must_be_nonnegative")
    parsed["prompt_token_ids"] = prompt_ids
    parsed["output_token_ids"] = output_ids
    return parsed


class StrictUgaVllmClient:
    """Fail-closed network client for a single pre-registered U/G/A request."""

    def __init__(self, config: VllmExperimentConfig) -> None:
        self.config = config

    async def generate(
        self,
        *,
        arm: UgaArm,
        prompt: str,
        schema: Mapping[str, Any],
        seed: int,
        request_id: str,
    ) -> dict[str, Any]:
        import aiohttp

        payload = build_uga_completion_payload(
            self.config,
            arm=arm,
            prompt=prompt,
            schema=schema,
            seed=seed,
            request_id=request_id,
        )
        timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)
        try:
            async with aiohttp.ClientSession(
                timeout=timeout,
                trust_env=False,
            ) as session:
                async with session.post(
                    f"{self.config.endpoint}/v1/completions",
                    json=payload,
                ) as response:
                    if response.status != 200:
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
        return parse_uga_completion_response(value, request_id=request_id)
