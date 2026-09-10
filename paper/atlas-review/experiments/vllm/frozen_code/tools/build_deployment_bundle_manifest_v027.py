"""Inventory and hash every file in an ATLAS U/G/A deployment bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any


MANIFEST_NAME = "DEPLOYMENT_BUNDLE_MANIFEST.json"


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


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


def role_for(relative: str) -> str:
    if relative.startswith("vllm_overlay/overlay/tests/"):
        return "overlay_test"
    if relative.startswith("vllm_overlay/overlay/"):
        return "overlay_runtime"
    if relative.startswith("source_assets/"):
        return "frozen_source_asset"
    if relative.startswith("tools/"):
        return "experiment_tool"
    if relative.endswith(".md"):
        return "protocol_or_operator_documentation"
    if relative.endswith(".sh"):
        return "deployment_entrypoint"
    if relative == "EXECUTION_SCHEMA_PREFLIGHT_V3.json":
        return "model_free_preflight_evidence"
    return "bundle_metadata"


def build(bundle_root: Path, protocol_path: Path) -> dict[str, Any]:
    bundle_root = bundle_root.resolve()
    protocol_path = protocol_path.resolve()
    if protocol_path.parent != bundle_root:
        raise RuntimeError("protocol_must_be_at_bundle_root")
    excluded = {MANIFEST_NAME}
    paths = sorted(
        (
            path
            for path in bundle_root.rglob("*")
            if path.is_file()
            and path.name not in excluded
            and "__pycache__" not in path.parts
            and path.suffix != ".pyc"
        ),
        key=lambda path: path.relative_to(bundle_root).as_posix(),
    )
    records = [
        {
            "path": path.relative_to(bundle_root).as_posix(),
            "role": role_for(path.relative_to(bundle_root).as_posix()),
            "sha256": sha256_file(path),
            "size": path.stat().st_size,
        }
        for path in paths
    ]
    overlay_manifest_path = bundle_root / "vllm_overlay" / "VLLM_OVERLAY_MANIFEST.json"
    overlay_manifest = json.loads(overlay_manifest_path.read_text(encoding="utf-8"))
    preflight_path = bundle_root / "EXECUTION_SCHEMA_PREFLIGHT_V3.json"
    preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    manifest: dict[str, Any] = {
        "schema_version": "atlas.vllm.uga.deployment_bundle.v2",
        "decision": "PASS",
        "docker_used": False,
        "protocol_path": protocol_path.name,
        "protocol_file_sha256": sha256_file(protocol_path),
        "overlay_manifest_content_sha256": overlay_manifest["content_sha256"],
        "execution_schema_preflight_content_sha256": preflight["content_sha256"],
        "record_count": len(records),
        "records": records,
    }
    manifest["content_sha256"] = canonical_sha256(manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle-root", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    args = parser.parse_args()
    bundle_root = args.bundle_root.resolve()
    manifest = build(bundle_root, args.protocol)
    atomic_write_json(bundle_root / MANIFEST_NAME, manifest)
    print(
        json.dumps(
            {
                "decision": manifest["decision"],
                "record_count": manifest["record_count"],
                "content_sha256": manifest["content_sha256"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
