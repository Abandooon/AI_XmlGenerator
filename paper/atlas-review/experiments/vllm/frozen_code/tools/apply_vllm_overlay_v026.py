"""Apply or verify the hash-pinned ATLAS overlay in a vLLM wheel install."""

from __future__ import annotations

import argparse
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import shutil
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
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_manifest(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    body = {key: item for key, item in value.items() if key != "content_sha256"}
    if value.get("content_sha256") != canonical_sha256(body):
        raise RuntimeError("overlay_manifest_content_hash_mismatch")
    if value.get("decision") != "PASS" or not value.get("python_only"):
        raise RuntimeError("overlay_manifest_not_admitted")
    return value


def installed_package_root() -> Path:
    import vllm

    return Path(vllm.__file__).resolve().parent.parent


def apply_overlay(
    *,
    bundle_root: Path,
    verify_only: bool,
) -> dict[str, Any]:
    bundle_root = bundle_root.resolve()
    manifest_path = bundle_root / "VLLM_OVERLAY_MANIFEST.json"
    manifest = load_manifest(manifest_path)
    if metadata.version("vllm") != manifest["upstream_version"]:
        raise RuntimeError("installed_vllm_version_mismatch")
    package_root = installed_package_root()
    records = [item for item in manifest["records"] if item["role"] == "runtime"]
    applied = 0
    verified = 0
    for record in records:
        source = bundle_root / "overlay" / record["target_path"]
        target = package_root / record["target_path"]
        if sha256_file(source) != record["overlay_sha256"]:
            raise RuntimeError(f"overlay_source_hash_mismatch:{record['target_path']}")
        target_exists = target.is_file()
        current_sha256 = sha256_file(target) if target_exists else None
        if current_sha256 == record["overlay_sha256"]:
            verified += 1
            continue
        if verify_only:
            raise RuntimeError(f"overlay_not_applied:{record['target_path']}")
        base_exists = record.get("base_exists", True)
        if base_exists:
            if current_sha256 != record["base_sha256"]:
                raise RuntimeError(
                    f"installed_base_hash_mismatch:{record['target_path']}"
                )
        elif target_exists:
            raise RuntimeError(
                f"unexpected_added_target_exists:{record['target_path']}"
            )
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".atlas-tmp")
        shutil.copyfile(source, temporary)
        os.replace(temporary, target)
        if sha256_file(target) != record["overlay_sha256"]:
            raise RuntimeError(f"overlay_apply_hash_mismatch:{record['target_path']}")
        applied += 1
    return {
        "decision": "PASS",
        "package_root": str(package_root),
        "applied_count": applied,
        "verified_count": verified,
        "runtime_file_count": len(records),
        "overlay_manifest_file_sha256": sha256_file(manifest_path),
        "overlay_manifest_content_sha256": manifest["content_sha256"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle-root", type=Path, required=True)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    result = apply_overlay(
        bundle_root=args.bundle_root,
        verify_only=args.verify_only,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
