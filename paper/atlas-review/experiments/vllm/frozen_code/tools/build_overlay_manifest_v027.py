"""Rebuild the hash-pinned Python overlay manifest after audited repairs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any


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
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def rebuild(overlay_root: Path, template_path: Path) -> dict[str, Any]:
    overlay_root = overlay_root.resolve()
    template = json.loads(template_path.read_text(encoding="utf-8"))
    template_paths = {str(item["target_path"]) for item in template.get("records") or []}
    overlay_paths = {
        path.relative_to(overlay_root / "overlay").as_posix()
        for path in (overlay_root / "overlay").rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix != ".pyc"
    }
    if template_paths != overlay_paths:
        raise RuntimeError(
            "overlay_template_inventory_mismatch:"
            f"missing={sorted(overlay_paths - template_paths)}:"
            f"unexpected={sorted(template_paths - overlay_paths)}"
        )
    records: list[dict[str, Any]] = []
    for old in template.get("records") or []:
        target_path = str(old["target_path"])
        overlay_path = overlay_root / "overlay" / target_path
        if not overlay_path.is_file():
            raise RuntimeError(f"overlay_file_missing:{target_path}")
        records.append(
            {
                "target_path": target_path,
                "role": old["role"],
                "base_exists": bool(old["base_exists"]),
                "base_sha256": old.get("base_sha256"),
                "overlay_sha256": sha256_file(overlay_path),
                "size": overlay_path.stat().st_size,
            }
        )
    manifest: dict[str, Any] = {
        "schema_version": "atlas.vllm.python_overlay.v2",
        "decision": "PASS",
        "implementation_version": "atlas-vllm-uga-v6.1",
        "upstream_version": template["upstream_version"],
        "upstream_base_commit": template["upstream_base_commit"],
        "local_patch_head": None,
        "python_only": True,
        "uncommitted_overlay": True,
        "record_count": len(records),
        "runtime_file_count": sum(item["role"] == "runtime" for item in records),
        "test_file_count": sum(item["role"] == "test" for item in records),
        "records": records,
    }
    manifest["content_sha256"] = canonical_sha256(manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--overlay-root", type=Path, required=True)
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = rebuild(args.overlay_root, args.template)
    atomic_write_json(args.output.resolve(), manifest)
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
