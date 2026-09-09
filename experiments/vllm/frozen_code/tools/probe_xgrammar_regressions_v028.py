"""Fail-closed, zero-model XGrammar regression gate for ATLAS V6."""

from __future__ import annotations

import argparse
import copy
from hashlib import sha256
import importlib.metadata
import json
import os
from pathlib import Path
import time
from typing import Any, Mapping

from execution_schema_v029 import canonical_sha256, synthesize_witness
from probe_xgrammar_execution_schemas_v027 import resolve_model_vocab_size
from token_evidence_v027 import decode_token_ids

PINNED_XGRAMMAR_VERSION = "0.2.6rc1"
PINNED_TRANSFORMERS_VERSION = "5.16.1"
EXACT_V4_REJECTIONS = {
    "005.json": {
        "case_id": "ASW-STD-04",
        "schema_sha256": (
            "6056aea3af7902bca032c119580c588a43773ef871fcdbe31f6ab82f5f86efbe"
        ),
        "first_rejected_token_index": 599,
    },
    "007.json": {
        "case_id": "ASW-FULL-03",
        "schema_sha256": (
            "4ff91ec518bf61aa5aa15713aae1ad3aebd6610cb20ac1d03cfe6b5d95e810c7"
        ),
        "first_rejected_token_index": 1214,
    },
}


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


def canonical_schema_text(schema: Mapping[str, Any]) -> str:
    return json.dumps(
        schema,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def xgrammar_instance_text(instance: Any) -> str:
    # XGrammar 0.2.6rc1's any_whitespace=False grammar uses the canonical
    # object separators emitted by the runtime path (": " and ", "). The
    # schema and instance keys are both sorted, so their declared order agrees.
    return json.dumps(
        instance,
        ensure_ascii=False,
        sort_keys=True,
        allow_nan=False,
    )


def encode(tokenizer: Any, text: str) -> list[int]:
    return [
        int(token_id)
        for token_id in tokenizer.encode(text, add_special_tokens=False)
    ]


def replay(matcher: Any, token_ids: list[int]) -> dict[str, Any]:
    accepted_count = 0
    rejected_token_id: int | None = None
    for token_id in token_ids:
        if not matcher.accept_token(token_id):
            rejected_token_id = token_id
            break
        accepted_count += 1
    return {
        "token_count": len(token_ids),
        "accepted_token_count": accepted_count,
        "accepted_all": accepted_count == len(token_ids),
        "first_rejected_token_index": (
            None if accepted_count == len(token_ids) else accepted_count
        ),
        "first_rejected_token_id": rejected_token_id,
        "completed": bool(matcher.is_completed()),
        "terminated": bool(matcher.is_terminated()),
    }


def _walk(
    schema: Mapping[str, Any],
    instance: Any,
    *,
    depth: int = 0,
) -> list[tuple[Mapping[str, Any], Any, int]]:
    nodes = [(schema, instance, depth)]
    if schema.get("type") == "object" and isinstance(instance, dict):
        properties = schema.get("properties") or {}
        for key, child_schema in properties.items():
            if key in instance and isinstance(child_schema, dict):
                nodes.extend(
                    _walk(child_schema, instance[key], depth=depth + 1)
                )
    elif schema.get("type") == "array" and isinstance(instance, list):
        prefix_items = schema.get("prefixItems")
        fallback_item_schema = schema.get("items")
        for index, item in enumerate(instance):
            item_schema: Any = None
            if isinstance(prefix_items, list) and index < len(prefix_items):
                item_schema = prefix_items[index]
            elif isinstance(fallback_item_schema, dict):
                item_schema = fallback_item_schema
            if isinstance(item_schema, dict):
                nodes.extend(_walk(item_schema, item, depth=depth + 1))
    return nodes


def adversarial_instances(
    schema: Mapping[str, Any], valid: Any
) -> dict[str, Any]:
    nodes = _walk(schema, valid)
    object_node = next(
        (
            (node_schema, node_instance)
            for node_schema, node_instance, depth in nodes
            if depth >= 2
            and node_schema.get("type") == "object"
            and isinstance(node_instance, dict)
            and node_schema.get("required")
        ),
        None,
    )
    array_node = next(
        (
            (node_schema, node_instance)
            for node_schema, node_instance, _ in nodes
            if node_schema.get("type") == "array"
            and isinstance(node_instance, list)
            and int(node_schema.get("minItems", 0)) > 0
            and isinstance(node_schema.get("maxItems"), int)
        ),
        None,
    )
    if object_node is None or array_node is None:
        raise RuntimeError("schema_lacks_adversarial_probe_nodes")

    def mutate_target(
        original_schema: Mapping[str, Any],
        original_instance: Any,
        target_schema: Mapping[str, Any],
        mutation: Any,
    ) -> Any:
        if original_schema is target_schema:
            return mutation(copy.deepcopy(original_instance))
        if original_schema.get("type") == "object":
            result = copy.deepcopy(original_instance)
            for key, child_schema in (original_schema.get("properties") or {}).items():
                if key in result and isinstance(child_schema, dict):
                    result[key] = mutate_target(
                        child_schema, result[key], target_schema, mutation
                    )
            return result
        if original_schema.get("type") == "array":
            result = copy.deepcopy(original_instance)
            prefix_items = original_schema.get("prefixItems")
            fallback_item_schema = original_schema.get("items")
            for index, item in enumerate(result):
                item_schema: Any = None
                if isinstance(prefix_items, list) and index < len(prefix_items):
                    item_schema = prefix_items[index]
                elif isinstance(fallback_item_schema, dict):
                    item_schema = fallback_item_schema
                if isinstance(item_schema, dict):
                    result[index] = mutate_target(
                        item_schema, item, target_schema, mutation
                    )
            return result
        return copy.deepcopy(original_instance)

    target_object_schema, target_object = object_node
    required_key = str(target_object_schema["required"][-1])
    first_property = str(next(iter(target_object_schema["properties"])))
    target_array_schema, _ = array_node
    max_items = int(target_array_schema["maxItems"])

    def missing_required(value: dict[str, Any]) -> dict[str, Any]:
        value.pop(required_key, None)
        return value

    def additional_property(value: dict[str, Any]) -> dict[str, Any]:
        value["__ATLAS_UNEXPECTED__"] = "forbidden"
        return value

    def wrong_type(value: dict[str, Any]) -> dict[str, Any]:
        value[first_property] = None
        return value

    def below_min(_: list[Any]) -> list[Any]:
        return []

    def above_max(value: list[Any]) -> list[Any]:
        if not value:
            raise RuntimeError("array_witness_is_empty")
        if len(value) != max_items:
            raise RuntimeError("array_witness_does_not_match_exact_max")
        return copy.deepcopy(value) + [copy.deepcopy(value[-1])]

    return {
        "nested_missing_required": mutate_target(
            schema, valid, target_object_schema, missing_required
        ),
        "nested_additional_property": mutate_target(
            schema, valid, target_object_schema, additional_property
        ),
        "nested_wrong_type": mutate_target(
            schema, valid, target_object_schema, wrong_type
        ),
        "array_below_min_items": mutate_target(
            schema, valid, target_array_schema, below_min
        ),
        "array_above_max_items": mutate_target(
            schema, valid, target_array_schema, above_max
        ),
    }


def run_probe(
    *,
    compiled_assets_path: Path,
    model_path: Path,
    fixture_root: Path,
) -> dict[str, Any]:
    import xgrammar as xgr
    from transformers import AutoConfig, AutoTokenizer

    xgrammar_version = importlib.metadata.version("xgrammar")
    transformers_version = importlib.metadata.version("transformers")
    if xgrammar_version != PINNED_XGRAMMAR_VERSION:
        raise RuntimeError(
            f"xgrammar_version_mismatch:{xgrammar_version}:"
            f"{PINNED_XGRAMMAR_VERSION}"
        )
    if transformers_version != PINNED_TRANSFORMERS_VERSION:
        raise RuntimeError(
            f"transformers_version_mismatch:{transformers_version}:"
            f"{PINNED_TRANSFORMERS_VERSION}"
        )

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
    model_vocab_size = resolve_model_vocab_size(config)
    tokenizer_info = xgr.TokenizerInfo.from_huggingface(
        tokenizer,
        vocab_size=model_vocab_size,
        stop_token_ids=[int(eos)],
    )
    compiler = xgr.GrammarCompiler(tokenizer_info, cache_enabled=False)

    witness_records: list[dict[str, Any]] = []
    for asset_record in assets_manifest.get("records") or []:
        asset_path = compiled_assets_path.parent / str(asset_record["path"])
        asset = json.loads(asset_path.read_text(encoding="utf-8"))
        case_id = str(asset_record["case_id"])
        schema = asset["schema"]
        schema_text = canonical_schema_text(schema)
        started = time.perf_counter()
        compiled = compiler.compile_json_schema(
            schema_text,
            any_whitespace=False,
        )
        compile_seconds = time.perf_counter() - started
        valid = synthesize_witness(schema)
        valid_text = xgrammar_instance_text(valid)
        valid_replay = replay(
            xgr.GrammarMatcher(compiled, terminate_without_stop_token=True),
            encode(tokenizer, valid_text),
        )
        invalid_replays: dict[str, dict[str, Any]] = {}
        for name, invalid in adversarial_instances(schema, valid).items():
            invalid_text = xgrammar_instance_text(invalid)
            invalid_replays[name] = replay(
                xgr.GrammarMatcher(compiled, terminate_without_stop_token=True),
                encode(tokenizer, invalid_text),
            )
        suffix_matcher = xgr.GrammarMatcher(
            compiled, terminate_without_stop_token=True
        )
        replay(suffix_matcher, encode(tokenizer, valid_text))
        suffix_tokens = encode(tokenizer, "Wait")
        suffix_rejected = bool(suffix_tokens) and not suffix_matcher.accept_token(
            suffix_tokens[0]
        )
        decision = (
            "PASS"
            if valid_replay["accepted_all"]
            and valid_replay["completed"]
            and valid_replay["terminated"]
            and suffix_rejected
            and all(
                not item["accepted_all"]
                and not item["completed"]
                and not item["terminated"]
                for item in invalid_replays.values()
            )
            else "FAIL"
        )
        witness_records.append(
            {
                "case_id": case_id,
                "schema_sha256": canonical_sha256(schema),
                "compile_seconds": compile_seconds,
                "valid_without_eos": valid_replay,
                "first_trailing_token_rejected": suffix_rejected,
                "invalid_replays": invalid_replays,
                "decision": decision,
            }
        )

    exact_records: list[dict[str, Any]] = []
    for fixture_name, expectation in EXACT_V4_REJECTIONS.items():
        result_path = fixture_root / fixture_name
        legacy_asset_path = fixture_root / (
            f"{Path(fixture_name).stem}.asset.json"
        )
        result = json.loads(result_path.read_text(encoding="utf-8"))
        legacy_asset_bytes = legacy_asset_path.read_bytes()
        legacy_asset = json.loads(legacy_asset_bytes.decode("utf-8"))
        case_id = str(expectation["case_id"])
        expected_schema_sha256 = str(expectation["schema_sha256"])
        legacy_asset_body = dict(legacy_asset)
        legacy_asset_content_sha256 = legacy_asset_body.pop(
            "content_sha256", None
        )
        if legacy_asset_content_sha256 != canonical_sha256(legacy_asset_body):
            raise RuntimeError(
                f"legacy_asset_content_hash_mismatch:{legacy_asset_path.name}"
            )
        legacy_schema_sha256 = canonical_sha256(legacy_asset["schema"])
        identity_claims = {
            "expectation_case_id": case_id,
            "legacy_asset_case_id": str(legacy_asset.get("case_id")),
            "result_schedule_case_id": str(
                result.get("schedule", {}).get("case_id")
            ),
            "result_request_case_id": str(
                result.get("request_identity", {}).get("case_id", case_id)
            ),
        }
        if set(identity_claims.values()) != {case_id}:
            raise RuntimeError(
                f"legacy_fixture_case_identity_mismatch:{fixture_name}:"
                f"{identity_claims}"
            )
        schema_claims = {
            "expected": expected_schema_sha256,
            "legacy_asset_schema": legacy_schema_sha256,
            "legacy_asset_hardening": str(
                legacy_asset.get("execution_schema_hardening", {}).get(
                    "execution_schema_sha256"
                )
            ),
            "result_schedule": str(
                result.get("schedule", {}).get("schema_sha256")
            ),
            "result_request": str(
                result.get("request_identity", {}).get("schema_sha256")
            ),
        }
        if set(schema_claims.values()) != {expected_schema_sha256}:
            raise RuntimeError(
                f"legacy_fixture_schema_identity_mismatch:{fixture_name}:"
                f"{schema_claims}"
            )
        compiled = compiler.compile_json_schema(
            canonical_schema_text(legacy_asset["schema"]),
            any_whitespace=True,
        )
        token_ids = decode_token_ids(result["output_token_ids_evidence"])
        exact_replay = replay(xgr.GrammarMatcher(compiled), token_ids)
        expected_index = int(expectation["first_rejected_token_index"])
        decision = (
            "PASS"
            if exact_replay["first_rejected_token_index"] == expected_index
            and not exact_replay["accepted_all"]
            else "FAIL"
        )
        exact_records.append(
            {
                "fixture": fixture_name,
                "case_id": case_id,
                "legacy_asset_file": legacy_asset_path.name,
                "legacy_asset_file_sha256": sha256(
                    legacy_asset_bytes
                ).hexdigest(),
                "legacy_asset_content_sha256": legacy_asset_content_sha256,
                "legacy_schema_sha256": legacy_schema_sha256,
                "expected_first_rejected_token_index": expected_index,
                "replay": exact_replay,
                "decision": decision,
            }
        )

    errors: list[str] = []
    if len(witness_records) != 20:
        errors.append("witness_case_count_mismatch")
    errors.extend(
        f"witness_probe_failed:{item['case_id']}"
        for item in witness_records
        if item["decision"] != "PASS"
    )
    errors.extend(
        f"exact_v4_replay_failed:{item['fixture']}"
        for item in exact_records
        if item["decision"] != "PASS"
    )
    report: dict[str, Any] = {
        "schema_version": "atlas.vllm.uga.xgrammar_regression.v2",
        "decision": "PASS" if not errors else "FAIL",
        "model_request_count": 0,
        "xgrammar_version": xgrammar_version,
        "transformers_version": transformers_version,
        "model_path": str(model_path.resolve()),
        "model_vocab_size": model_vocab_size,
        "tokenizer_length": len(tokenizer),
        "tokenizer_eos_token_id": int(eos),
        "compiled_assets_content_sha256": assets_manifest.get("content_sha256"),
        "witness_case_count": len(witness_records),
        "witness_records": witness_records,
        "exact_v4_failure_replays": exact_records,
        "errors": errors,
    }
    report["content_sha256"] = canonical_sha256(report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiled-assets", type=Path, required=True)
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--fixture-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run_probe(
        compiled_assets_path=args.compiled_assets.resolve(),
        model_path=args.model_path.resolve(),
        fixture_root=args.fixture_root.resolve(),
    )
    atomic_write_json(args.output.resolve(), report)
    print(
        json.dumps(
            {
                "decision": report["decision"],
                "model_request_count": report["model_request_count"],
                "content_sha256": report["content_sha256"],
            },
            sort_keys=True,
        )
    )
    return 0 if report["decision"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
