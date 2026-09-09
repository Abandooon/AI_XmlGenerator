"""Fail-closed collector for XGrammar 0.2.3/0.2.4/0.2.5 probe results."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from execution_schema_v027 import canonical_sha256

EXPECTED_VERSIONS = ("0.2.3", "0.2.4", "0.2.5")


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


def collect(paths: list[Path]) -> dict[str, Any]:
    by_version: dict[str, tuple[Path, dict[str, Any]]] = {}
    errors: list[str] = []
    for path in paths:
        try:
            result = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"unreadable_probe:{path.name}:{type(exc).__name__}")
            continue
        claimed = result.get("content_sha256")
        body = {key: value for key, value in result.items() if key != "content_sha256"}
        if claimed != canonical_sha256(body):
            errors.append(f"probe_content_hash_mismatch:{path.name}")
            continue
        version = str(result.get("xgrammar_version") or "")
        if version in by_version:
            errors.append(f"duplicate_xgrammar_probe:{version}")
        else:
            by_version[version] = (path, result)
    missing = sorted(set(EXPECTED_VERSIONS) - set(by_version))
    unexpected = sorted(set(by_version) - set(EXPECTED_VERSIONS))
    errors.extend(f"missing_xgrammar_probe:{version}" for version in missing)
    errors.extend(f"unexpected_xgrammar_probe:{version}" for version in unexpected)
    for version in EXPECTED_VERSIONS:
        if version in by_version and by_version[version][1].get("decision") != "PASS":
            errors.append(f"xgrammar_probe_failed:{version}")
    asset_hashes = {
        str(result.get("compiled_assets_content_sha256") or "")
        for _, result in by_version.values()
    }
    if len(asset_hashes) != 1 or "" in asset_hashes:
        errors.append("xgrammar_probes_do_not_share_one_compiled_asset_identity")
    manifest: dict[str, Any] = {
        "schema_version": "atlas.vllm.uga.xgrammar_version_matrix.v1",
        "decision": "PASS" if not errors else "FAIL",
        "model_request_count": 0,
        "expected_versions": list(EXPECTED_VERSIONS),
        "missing_versions": missing,
        "unexpected_versions": unexpected,
        "errors": errors,
        "compiled_assets_content_sha256": (
            next(iter(asset_hashes)) if len(asset_hashes) == 1 else None
        ),
        "probes": [
            {
                "xgrammar_version": version,
                "path": by_version[version][0].name,
                "file_sha256": sha256_file(by_version[version][0]),
                "content_sha256": by_version[version][1]["content_sha256"],
                "decision": by_version[version][1]["decision"],
            }
            for version in EXPECTED_VERSIONS
            if version in by_version
        ],
    }
    manifest["content_sha256"] = canonical_sha256(manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = collect([path.resolve() for path in args.probe])
    atomic_write_json(args.output.resolve(), manifest)
    print(json.dumps({"decision": manifest["decision"], "errors": manifest["errors"]}, sort_keys=True))
    return 0 if manifest["decision"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
