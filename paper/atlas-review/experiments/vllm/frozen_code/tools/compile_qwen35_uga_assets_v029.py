"""Compile frozen non-thinking Qwen3.5 prompts from exported AUTOSAR schemas."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from qwen35_prompt_v026 import (
    DEFAULT_MAX_OUTPUT_TOKENS,
    MAX_MODEL_LEN,
    compile_non_thinking_prompt,
    sha256_text,
)
from execution_schema_v029 import (
    build_witness_matrix,
    harden_execution_schema,
)


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_write_json(path: Path, value: Any, *, compact: bool = False) -> None:
    if compact:
        encoded = canonical_json_bytes(value)
    else:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            allow_nan=False,
        ).encode("utf-8") + b"\n"
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(encoded)
    os.replace(temporary, path)


def verify_content_hash(document: dict[str, Any]) -> str:
    claimed = document.get("content_sha256")
    body = {key: value for key, value in document.items() if key != "content_sha256"}
    actual = canonical_sha256(body)
    if claimed != actual:
        raise RuntimeError("source_asset_manifest_content_hash_mismatch")
    return actual


def compile_assets(
    *,
    source_root: Path,
    output_root: Path,
    model_path: Path,
    max_model_len: int,
    max_output_tokens: int,
) -> dict[str, Any]:
    source_root = source_root.resolve()
    output_root = output_root.resolve()
    model_path = model_path.resolve()
    if output_root.exists() and any(output_root.iterdir()):
        raise FileExistsError(f"output root is not empty: {output_root}")
    if not model_path.is_dir():
        raise FileNotFoundError(f"model path does not exist: {model_path}")
    output_root.mkdir(parents=True, exist_ok=True)
    asset_root = output_root / "cases"
    asset_root.mkdir()

    source_manifest_path = source_root / "SOURCE_ASSET_MANIFEST.json"
    source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    source_content_sha256 = verify_content_hash(source_manifest)
    if source_manifest.get("decision") != "PASS":
        raise RuntimeError("source_asset_manifest_not_pass")
    if source_manifest.get("case_count") != 20:
        raise RuntimeError("source_asset_manifest_case_count_mismatch")

    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        str(model_path),
        local_files_only=True,
        trust_remote_code=False,
    )
    chat_template = str(getattr(tokenizer, "chat_template", "") or "")
    if not chat_template:
        raise RuntimeError("tokenizer_chat_template_is_missing")

    records: list[dict[str, Any]] = []
    for source_record in source_manifest["records"]:
        case_id = source_record["case_id"]
        schema_path = source_root / source_record["schema_path"]
        requirement_path = source_root / source_record["requirement_path"]
        if sha256_file(schema_path) != source_record["schema_sha256"]:
            raise RuntimeError(f"source_schema_hash_mismatch:{case_id}")
        if sha256_file(requirement_path) != source_record["requirement_sha256"]:
            raise RuntimeError(f"source_requirement_hash_mismatch:{case_id}")
        source_schema = json.loads(schema_path.read_text(encoding="utf-8"))
        requirement = requirement_path.read_text(encoding="utf-8")
        schema, hardening_report = harden_execution_schema(
            source_schema,
            requirement,
            case_id=case_id,
        )
        witness_matrix = build_witness_matrix(schema)
        compiled = compile_non_thinking_prompt(
            tokenizer,
            requirement_text=requirement,
            schema=schema,
            max_model_len=max_model_len,
            max_output_tokens=max_output_tokens,
        )
        if compiled.schema_sha256 != hardening_report["execution_schema_sha256"]:
            raise RuntimeError(f"compiled_execution_schema_hash_mismatch:{case_id}")
        asset = {
            "schema_version": "atlas.vllm.uga.compiled_case.v3",
            "case_id": case_id,
            "tier": source_record["tier"],
            "component": source_record["component"],
            "case_sha256": source_record["case_sha256"],
            "source_requirement_sha256": source_record["requirement_sha256"],
            "source_schema_sha256": source_record["schema_sha256"],
            "schema": schema,
            "schema_sha256": compiled.schema_sha256,
            "execution_schema_hardening": hardening_report,
            "execution_schema_witness_matrix": witness_matrix,
            "prompt": compiled.prompt,
            "prompt_sha256": compiled.prompt_sha256,
            "prompt_token_count": compiled.prompt_token_count,
            "prompt_token_ids_sha256": compiled.prompt_token_ids_sha256,
            "enable_thinking": compiled.enable_thinking,
            "max_model_len": max_model_len,
            "max_output_tokens": max_output_tokens,
        }
        asset["content_sha256"] = canonical_sha256(asset)
        asset_path = asset_root / f"{case_id}.json"
        atomic_write_json(asset_path, asset, compact=True)
        records.append(
            {
                "case_id": case_id,
                "tier": source_record["tier"],
                "path": asset_path.relative_to(output_root).as_posix(),
                "file_sha256": sha256_file(asset_path),
                "content_sha256": asset["content_sha256"],
                "schema_sha256": compiled.schema_sha256,
                "source_schema_sha256": source_record["schema_sha256"],
                "execution_schema_character_count": hardening_report[
                    "execution_schema_character_count"
                ],
                "source_schema_character_count": hardening_report[
                    "source_schema_character_count"
                ],
                "bounded_array_count": len(hardening_report["array_bounds"]),
                "schema_witness_decision": witness_matrix["decision"],
                "prompt_sha256": compiled.prompt_sha256,
                "prompt_token_count": compiled.prompt_token_count,
                "prompt_token_ids_sha256": compiled.prompt_token_ids_sha256,
            }
        )

    manifest: dict[str, Any] = {
        "schema_version": "atlas.vllm.uga.compiled_assets.v3",
        "decision": "PASS",
        "model_path": str(model_path),
        "model_revision": None,
        "tokenizer_class": type(tokenizer).__name__,
        "tokenizer_name_or_path": str(tokenizer.name_or_path),
        "tokenizer_vocab_size": int(tokenizer.vocab_size),
        "chat_template_sha256": sha256_text(chat_template),
        "enable_thinking": False,
        "raw_completion_endpoint": "/v1/completions",
        "max_model_len": max_model_len,
        "max_output_tokens": max_output_tokens,
        "source_manifest_file_sha256": sha256_file(source_manifest_path),
        "source_manifest_content_sha256": source_content_sha256,
        "case_count": len(records),
        "records": records,
    }
    manifest["content_sha256"] = canonical_sha256(manifest)
    atomic_write_json(output_root / "COMPILED_ASSET_MANIFEST.json", manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--max-model-len", type=int, default=MAX_MODEL_LEN)
    parser.add_argument(
        "--max-output-tokens",
        type=int,
        default=DEFAULT_MAX_OUTPUT_TOKENS,
    )
    args = parser.parse_args()
    manifest = compile_assets(
        source_root=args.source_root,
        output_root=args.output_root,
        model_path=args.model_path,
        max_model_len=args.max_model_len,
        max_output_tokens=args.max_output_tokens,
    )
    print(
        json.dumps(
            {
                "decision": manifest["decision"],
                "case_count": manifest["case_count"],
                "content_sha256": manifest["content_sha256"],
                "max_prompt_tokens": max(
                    item["prompt_token_count"] for item in manifest["records"]
                ),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
