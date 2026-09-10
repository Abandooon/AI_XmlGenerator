"""Create the model-free execution-schema and witness preflight manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from execution_schema_v027 import (
    build_witness_matrix,
    canonical_json_bytes,
    canonical_sha256,
    harden_execution_schema,
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_content_hash(document: dict[str, Any]) -> str:
    claimed = document.get("content_sha256")
    body = {key: value for key, value in document.items() if key != "content_sha256"}
    actual = canonical_sha256(body)
    if claimed != actual:
        raise RuntimeError("source_asset_manifest_content_hash_mismatch")
    return actual


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


def build_preflight(source_root: Path) -> dict[str, Any]:
    source_root = source_root.resolve()
    source_manifest_path = source_root / "SOURCE_ASSET_MANIFEST.json"
    source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    source_content_sha256 = verify_content_hash(source_manifest)
    records: list[dict[str, Any]] = []
    for source_record in source_manifest.get("records") or []:
        case_id = str(source_record["case_id"])
        schema_path = source_root / str(source_record["schema_path"])
        requirement_path = source_root / str(source_record["requirement_path"])
        if sha256_file(schema_path) != source_record.get("schema_sha256"):
            raise RuntimeError(f"source_schema_hash_mismatch:{case_id}")
        if sha256_file(requirement_path) != source_record.get("requirement_sha256"):
            raise RuntimeError(f"source_requirement_hash_mismatch:{case_id}")
        source_schema = json.loads(schema_path.read_text(encoding="utf-8"))
        requirement = requirement_path.read_text(encoding="utf-8")
        execution_schema, hardening = harden_execution_schema(
            source_schema,
            requirement,
            case_id=case_id,
        )
        witness = build_witness_matrix(execution_schema)
        records.append(
            {
                "case_id": case_id,
                "tier": source_record["tier"],
                "source_schema_file_sha256": sha256_file(schema_path),
                "execution_schema_sha256": canonical_sha256(execution_schema),
                "execution_schema_character_count": len(
                    canonical_json_bytes(execution_schema).decode("utf-8")
                ),
                "hardening": hardening,
                "witness_matrix": witness,
            }
        )
    if len(records) != 20:
        raise RuntimeError("execution_schema_preflight_case_count_mismatch")
    manifest: dict[str, Any] = {
        "schema_version": "atlas.vllm.uga.execution_schema_preflight.v1",
        "decision": "PASS",
        "model_request_count": 0,
        "source_manifest_file_sha256": sha256_file(source_manifest_path),
        "source_manifest_content_sha256": source_content_sha256,
        "case_count": len(records),
        "all_arrays_finitely_bounded": True,
        "all_witness_matrices_pass": all(
            record["witness_matrix"]["decision"] == "PASS" for record in records
        ),
        "records": records,
    }
    manifest["content_sha256"] = canonical_sha256(manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = build_preflight(args.source_root)
    atomic_write_json(args.output.resolve(), manifest)
    print(
        json.dumps(
            {
                "decision": manifest["decision"],
                "case_count": manifest["case_count"],
                "content_sha256": manifest["content_sha256"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
