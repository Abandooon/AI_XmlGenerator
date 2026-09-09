"""Verify every byte in an ATLAS vLLM U/G/A deployment bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


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
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def verify_bundle(bundle_root: Path) -> dict[str, Any]:
    bundle_root = bundle_root.resolve()
    manifest_path = bundle_root / "DEPLOYMENT_BUNDLE_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise RuntimeError("deployment_manifest_root_is_not_object")
    body = {key: item for key, item in manifest.items() if key != "content_sha256"}
    if manifest.get("content_sha256") != canonical_sha256(body):
        raise RuntimeError("deployment_manifest_content_hash_mismatch")
    expected = {item["path"]: item for item in manifest.get("records") or []}
    observed = {
        path.relative_to(bundle_root).as_posix(): path
        for path in bundle_root.rglob("*")
        if path.is_file() and path != manifest_path
    }
    missing = sorted(set(expected) - set(observed))
    unexpected = sorted(set(observed) - set(expected))
    if missing or unexpected:
        raise RuntimeError(
            f"deployment_bundle_file_set_mismatch:{missing}:{unexpected}"
        )
    for relative, record in expected.items():
        path = observed[relative]
        if path.stat().st_size != record.get("size"):
            raise RuntimeError(f"deployment_bundle_size_mismatch:{relative}")
        if sha256_file(path) != record.get("sha256"):
            raise RuntimeError(f"deployment_bundle_hash_mismatch:{relative}")
    return {
        "decision": "PASS",
        "file_count": len(observed),
        "manifest_file_sha256": sha256_file(manifest_path),
        "manifest_content_sha256": manifest["content_sha256"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle-root", type=Path, required=True)
    args = parser.parse_args()
    result = verify_bundle(args.bundle_root)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
