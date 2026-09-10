"""Zero-model regression for lossless structured-output termination text."""

from __future__ import annotations

import argparse
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import time
from typing import Any

from vllm.sampling_params import SamplingParams
from vllm.tokenizers import get_tokenizer
from vllm.v1.engine import EngineCoreRequest, FinishReason
from vllm.v1.engine.detokenizer import IncrementalDetokenizer
from vllm.v1.engine.output_processor import (
    should_exclude_stop_token_from_output,
)
from vllm.v1.structured_output import (
    STRUCTURED_OUTPUT_TERMINATED_STOP_REASON,
)


EXPECTED_FINAL_TOKENS = {
    92: "}",
    29958: '"}}',
}


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def atomic_write_json(path: Path, value: Any) -> None:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
        allow_nan=False,
    ).encode("utf-8") + b"\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(encoded)
    os.replace(temporary, path)


def make_detokenizer(tokenizer: Any, prompt_token_ids: list[int]) -> Any:
    request = EngineCoreRequest(
        request_id="atlas-v6-structured-stop-zero-model",
        prompt_token_ids=prompt_token_ids,
        mm_features=None,
        sampling_params=SamplingParams(
            temperature=0.0,
            max_tokens=8,
            include_stop_str_in_output=False,
        ),
        pooling_params=None,
        arrival_time=time.time(),
        lora_request=None,
        cache_salt=None,
        data_parallel_rank=None,
    )
    return IncrementalDetokenizer.from_new_request(tokenizer, request)


def probe(model_path: Path) -> dict[str, Any]:
    errors: list[str] = []
    cases: list[dict[str, Any]] = []
    grammar_excludes = should_exclude_stop_token_from_output(
        FinishReason.STOP,
        STRUCTURED_OUTPUT_TERMINATED_STOP_REASON,
    )
    eos_excludes = should_exclude_stop_token_from_output(FinishReason.STOP, None)
    stop_token_excludes = should_exclude_stop_token_from_output(
        FinishReason.STOP,
        248046,
    )
    length_excludes = should_exclude_stop_token_from_output(
        FinishReason.LENGTH,
        None,
    )
    if grammar_excludes:
        errors.append("grammar_completion_would_exclude_payload_token")
    if not eos_excludes:
        errors.append("eos_exclusion_behavior_changed")
    if not stop_token_excludes:
        errors.append("stop_token_exclusion_behavior_changed")
    if length_excludes:
        errors.append("length_completion_would_exclude_payload_token")

    tokenizer = get_tokenizer(str(model_path))
    prompt_token_ids = tokenizer.encode("x")
    for token_id, expected_text in EXPECTED_FINAL_TOKENS.items():
        decoded = tokenizer.decode([token_id], skip_special_tokens=True)
        keep = make_detokenizer(tokenizer, prompt_token_ids)
        keep.update(
            [token_id],
            should_exclude_stop_token_from_output(
                FinishReason.STOP,
                STRUCTURED_OUTPUT_TERMINATED_STOP_REASON,
            ),
        )
        grammar_text = keep.get_next_output_text(True, False)
        ordinary_stop = make_detokenizer(tokenizer, prompt_token_ids)
        ordinary_stop.update(
            [token_id],
            should_exclude_stop_token_from_output(FinishReason.STOP, None),
        )
        ordinary_stop_text = ordinary_stop.get_next_output_text(True, False)
        case_errors: list[str] = []
        if decoded != expected_text:
            case_errors.append("model_tokenizer_decode_mismatch")
        if grammar_text != expected_text:
            case_errors.append("grammar_completion_text_lost_final_token")
        if ordinary_stop_text != "":
            case_errors.append("ordinary_stop_no_longer_excludes_final_token")
        if keep.output_token_ids != [token_id]:
            case_errors.append("grammar_completion_token_evidence_mismatch")
        if ordinary_stop.output_token_ids != [token_id]:
            case_errors.append("ordinary_stop_token_evidence_mismatch")
        if case_errors:
            errors.extend(f"token_{token_id}:{item}" for item in case_errors)
        cases.append(
            {
                "token_id": token_id,
                "expected_text": expected_text,
                "decoded_text": decoded,
                "grammar_completion_text": grammar_text,
                "ordinary_stop_text": ordinary_stop_text,
                "grammar_output_token_ids": keep.output_token_ids,
                "ordinary_stop_output_token_ids": ordinary_stop.output_token_ids,
                "errors": case_errors,
                "decision": "PASS" if not case_errors else "FAIL",
            }
        )

    result: dict[str, Any] = {
        "schema_version": (
            "atlas.vllm.uga.structured_stop_detokenization_regression.v1"
        ),
        "decision": "PASS" if not errors else "FAIL",
        "model_request_count": 0,
        "model_path": str(model_path),
        "vllm_version": metadata.version("vllm"),
        "transformers_version": metadata.version("transformers"),
        "tokenizers_version": metadata.version("tokenizers"),
        "structured_output_stop_reason": (
            STRUCTURED_OUTPUT_TERMINATED_STOP_REASON
        ),
        "semantics": {
            "grammar_completion_excludes_final_token": grammar_excludes,
            "eos_excludes_final_token": eos_excludes,
            "stop_token_excludes_final_token": stop_token_excludes,
            "length_completion_excludes_final_token": length_excludes,
        },
        "cases": cases,
        "errors": errors,
    }
    result["content_sha256"] = canonical_sha256(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = probe(args.model_path.resolve())
    atomic_write_json(args.output.resolve(), result)
    print(
        json.dumps(
            {
                "decision": result["decision"],
                "model_request_count": result["model_request_count"],
                "case_count": len(result["cases"]),
                "content_sha256": result["content_sha256"],
            },
            sort_keys=True,
        )
    )
    return 0 if result["decision"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
