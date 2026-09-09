"""Compile and replay ATLAS execution schemas in one pinned XGrammar env."""

from __future__ import annotations

import argparse
import copy
import importlib.metadata
import json
import os
from pathlib import Path
import time
from typing import Any

from execution_schema_v027 import canonical_sha256, synthesize_witness

ALLOWED_XGRAMMAR_VERSIONS = {"0.2.3", "0.2.4", "0.2.5"}


def resolve_model_vocab_size(config: Any) -> int:
    """Resolve the model output-head vocabulary from plain or composite configs.

    Qwen3.5 is represented by a composite Hugging Face config whose vocabulary
    lives under ``text_config``.  XGrammar must receive the model/logit
    vocabulary size, not ``len(tokenizer)``, which can include added tokens.
    """

    candidates: list[tuple[str, int]] = []
    for label, node in (
        ("config", config),
        ("config.text_config", getattr(config, "text_config", None)),
    ):
        raw_value = getattr(node, "vocab_size", None) if node is not None else None
        if raw_value is None:
            continue
        value = int(raw_value)
        if value <= 0:
            raise RuntimeError(f"model_vocab_size_is_not_positive:{label}:{value}")
        candidates.append((label, value))
    if not candidates:
        raise RuntimeError("model_vocab_size_missing")
    distinct = {value for _, value in candidates}
    if len(distinct) != 1:
        rendered = ",".join(f"{label}={value}" for label, value in candidates)
        raise RuntimeError(f"model_vocab_size_disagrees:{rendered}")
    return candidates[0][1]


def atomic_write_json(path: Path, value: Any) -> None:
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


def _first_invalid_instance(valid: Any) -> Any:
    if not isinstance(valid, dict) or not valid:
        raise ValueError("xgrammar_probe_requires_nonempty_object_witness")
    invalid = copy.deepcopy(valid)
    del invalid[next(iter(invalid))]
    return invalid


def _replay(matcher: Any, tokenizer: Any, text: str, eos_token_id: int) -> dict[str, Any]:
    token_ids = [
        int(token_id)
        for token_id in tokenizer.encode(text, add_special_tokens=False)
    ]
    accepted_count = 0
    for token_id in token_ids:
        if not matcher.accept_token(token_id):
            return {
                "accepted": False,
                "accepted_token_count": accepted_count,
                "token_count": len(token_ids),
                "terminated": bool(matcher.is_terminated()),
            }
        accepted_count += 1
    eos_accepted = bool(matcher.accept_token(eos_token_id))
    return {
        "accepted": eos_accepted,
        "accepted_token_count": accepted_count + int(eos_accepted),
        "token_count": len(token_ids) + 1,
        "terminated": bool(matcher.is_terminated()),
    }


def run_probe(compiled_assets_path: Path, model_path: Path) -> dict[str, Any]:
    import xgrammar as xgr
    from transformers import AutoConfig, AutoTokenizer

    version = importlib.metadata.version("xgrammar")
    if version not in ALLOWED_XGRAMMAR_VERSIONS:
        raise RuntimeError(f"xgrammar_version_not_in_matrix:{version}")
    assets_manifest = json.loads(compiled_assets_path.read_text(encoding="utf-8"))
    tokenizer = AutoTokenizer.from_pretrained(
        str(model_path), local_files_only=True, trust_remote_code=False
    )
    config = AutoConfig.from_pretrained(
        str(model_path), local_files_only=True, trust_remote_code=False
    )
    eos = tokenizer.eos_token_id
    if isinstance(eos, list):
        eos = eos[0] if eos else None
    if eos is None:
        raise RuntimeError("tokenizer_eos_token_id_missing")
    tokenizer_info = xgr.TokenizerInfo.from_huggingface(
        tokenizer,
        vocab_size=resolve_model_vocab_size(config),
        stop_token_ids=[int(eos)],
    )
    compiler = xgr.GrammarCompiler(tokenizer_info, cache_enabled=False)
    records: list[dict[str, Any]] = []
    for asset_record in assets_manifest.get("records") or []:
        asset_path = compiled_assets_path.parent / str(asset_record["path"])
        asset = json.loads(asset_path.read_text(encoding="utf-8"))
        schema = asset["schema"]
        schema_text = json.dumps(
            schema,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        started = time.perf_counter()
        compiled = compiler.compile_json_schema(schema_text)
        compile_seconds = time.perf_counter() - started
        valid = synthesize_witness(schema)
        valid_text = json.dumps(
            valid, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        valid_replay = _replay(
            xgr.GrammarMatcher(compiled), tokenizer, valid_text, int(eos)
        )
        invalid = _first_invalid_instance(valid)
        invalid_text = json.dumps(
            invalid, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        invalid_replay = _replay(
            xgr.GrammarMatcher(compiled), tokenizer, invalid_text, int(eos)
        )
        decision = (
            "PASS"
            if valid_replay["accepted"]
            and valid_replay["terminated"]
            and not invalid_replay["accepted"]
            else "FAIL"
        )
        records.append(
            {
                "case_id": asset_record["case_id"],
                "schema_sha256": canonical_sha256(schema),
                "compile_seconds": compile_seconds,
                "valid_replay": valid_replay,
                "invalid_replay": invalid_replay,
                "decision": decision,
            }
        )
    manifest: dict[str, Any] = {
        "schema_version": "atlas.vllm.uga.xgrammar_schema_probe.v1",
        "decision": (
            "PASS"
            if len(records) == 20 and all(item["decision"] == "PASS" for item in records)
            else "FAIL"
        ),
        "model_request_count": 0,
        "xgrammar_version": version,
        "model_path": str(model_path.resolve()),
        "compiled_assets_content_sha256": assets_manifest.get("content_sha256"),
        "case_count": len(records),
        "records": records,
    }
    manifest["content_sha256"] = canonical_sha256(manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiled-assets", type=Path, required=True)
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = run_probe(
        args.compiled_assets.resolve(), args.model_path.resolve()
    )
    atomic_write_json(args.output.resolve(), manifest)
    print(
        json.dumps(
            {
                "decision": manifest["decision"],
                "xgrammar_version": manifest["xgrammar_version"],
                "content_sha256": manifest["content_sha256"],
            },
            sort_keys=True,
        )
    )
    return 0 if manifest["decision"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
