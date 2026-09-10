"""Build and verify the hash-pinned executable validator manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from src.kg_builder.xsd_enrichment.serialization_manifest import (
    load_serialization_manifest,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SOURCE_ROOT = Path(__file__).resolve().parent
DEFAULT_PLAN = PROJECT_ROOT / "src/generate_formal_constraints/v2/validation_plan.json"
DEFAULT_XSD = PROJECT_ROOT / "src/validation/data/AUTOSAR_4-2-2.xsd"
DEFAULT_DATASET = PROJECT_ROOT / "src/llm_generation/knowledge/v2/retrieval_manifest.json"
DEFAULT_XSD_SERIALIZATION_MANIFEST = (
    PROJECT_ROOT / "src/llm_generation/knowledge/v2/xsd_serialization_manifest.json"
)
DEFAULT_OUTPUT = SOURCE_ROOT / "validator_manifest.json"


class ValidatorManifestError(ValueError):
    """Raised when executable validator files do not match their manifest."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _fingerprint(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _source_files(source_root: Path = SOURCE_ROOT) -> list[Path]:
    return sorted(path.resolve() for path in source_root.rglob("*.py") if path.is_file())


def build_manifest(
    *,
    plan_path: Path = DEFAULT_PLAN,
    xsd_path: Path = DEFAULT_XSD,
    dataset_manifest_path: Path = DEFAULT_DATASET,
    xsd_serialization_manifest_path: Path = DEFAULT_XSD_SERIALIZATION_MANIFEST,
    source_root: Path = SOURCE_ROOT,
) -> dict[str, Any]:
    plan_path = plan_path.resolve()
    xsd_path = xsd_path.resolve()
    dataset_manifest_path = dataset_manifest_path.resolve()
    xsd_serialization_manifest_path = xsd_serialization_manifest_path.resolve()
    for label, path in (
        ("validation plan", plan_path),
        ("XSD", xsd_path),
        ("retrieval manifest", dataset_manifest_path),
        ("XSD serialization manifest", xsd_serialization_manifest_path),
    ):
        if not path.is_file():
            raise ValidatorManifestError(f"{label} not found: {path}")
    serialization_manifest = load_serialization_manifest(
        xsd_serialization_manifest_path,
        xsd_path=xsd_path,
    )
    dataset = json.loads(dataset_manifest_path.read_text(encoding="utf-8-sig"))
    dataset_sha256 = str(dataset.get("dataset_sha256") or "")
    files = [
        {
            "path": path.relative_to(PROJECT_ROOT).as_posix(),
            "sha256": _sha256(path),
        }
        for path in _source_files(source_root)
    ]
    body: dict[str, Any] = {
        "schema_version": "1.0",
        "dataset_sha256": dataset_sha256,
        "validation_plan": {
            "path": plan_path.relative_to(PROJECT_ROOT).as_posix(),
            "sha256": _sha256(plan_path),
        },
        "xsd": {
            "path": xsd_path.relative_to(PROJECT_ROOT).as_posix(),
            "sha256": _sha256(xsd_path),
        },
        "xsd_serialization_manifest": {
            "path": xsd_serialization_manifest_path.relative_to(PROJECT_ROOT).as_posix(),
            "sha256": _sha256(xsd_serialization_manifest_path),
            "manifest_sha256": serialization_manifest["manifest_sha256"],
        },
        "source_files": files,
    }
    body["validator_sha256"] = _fingerprint(body)
    return body


def validate_manifest(
    manifest_path: Path = DEFAULT_OUTPUT,
    *,
    plan_path: Path | None = None,
    xsd_path: Path | None = None,
    dataset_manifest_path: Path | None = None,
    xsd_serialization_manifest_path: Path | None = None,
) -> dict[str, Any]:
    manifest_path = manifest_path.resolve()
    if not manifest_path.is_file():
        raise ValidatorManifestError(f"validator manifest not found: {manifest_path}")
    payload = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    if payload.get("schema_version") != "1.0":
        raise ValidatorManifestError("unsupported validator manifest schema_version")
    declared_hash = str(payload.get("validator_sha256") or "")
    body = dict(payload)
    body.pop("validator_sha256", None)
    if declared_hash != _fingerprint(body):
        raise ValidatorManifestError("validator manifest fingerprint does not match its content")
    declared_files = payload.get("source_files")
    if not isinstance(declared_files, list) or not declared_files:
        raise ValidatorManifestError("validator manifest source_files is empty or malformed")
    declared_paths = {str(item.get("path") or "") for item in declared_files if isinstance(item, dict)}
    actual_paths = {path.relative_to(PROJECT_ROOT).as_posix() for path in _source_files()}
    if declared_paths != actual_paths:
        raise ValidatorManifestError("validator source file set differs from the hash-pinned manifest")
    for item in declared_files:
        relative = Path(str(item.get("path") or ""))
        target = (PROJECT_ROOT / relative).resolve()
        if PROJECT_ROOT.resolve() not in target.parents or not target.is_file():
            raise ValidatorManifestError(f"invalid validator source path: {relative}")
        if _sha256(target) != str(item.get("sha256") or ""):
            raise ValidatorManifestError(f"validator source hash mismatch: {relative.as_posix()}")
    checks = (
        ("validation_plan", plan_path),
        ("xsd", xsd_path),
        ("xsd_serialization_manifest", xsd_serialization_manifest_path),
    )
    for key, expected_path in checks:
        record = payload.get(key) or {}
        declared_path = (PROJECT_ROOT / str(record.get("path") or "")).resolve()
        if expected_path is not None and declared_path != expected_path.resolve():
            raise ValidatorManifestError(f"validator manifest {key} path does not match runtime configuration")
        if not declared_path.is_file() or _sha256(declared_path) != str(record.get("sha256") or ""):
            raise ValidatorManifestError(f"validator manifest {key} hash mismatch")
    serialization_record = payload.get("xsd_serialization_manifest") or {}
    serialization_path = (
        PROJECT_ROOT / str(serialization_record.get("path") or "")
    ).resolve()
    validated_serialization = load_serialization_manifest(
        serialization_path,
        xsd_path=(PROJECT_ROOT / str((payload.get("xsd") or {}).get("path") or "")).resolve(),
    )
    if validated_serialization["manifest_sha256"] != str(
        serialization_record.get("manifest_sha256") or ""
    ):
        raise ValidatorManifestError(
            "validator manifest XSD serialization semantic hash mismatch"
        )
    if dataset_manifest_path is not None:
        dataset = json.loads(dataset_manifest_path.read_text(encoding="utf-8-sig"))
        if str(dataset.get("dataset_sha256") or "") != str(payload.get("dataset_sha256") or ""):
            raise ValidatorManifestError("validator manifest dataset hash does not match retrieval manifest")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the executable validator hash manifest")
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--xsd", type=Path, default=DEFAULT_XSD)
    parser.add_argument("--dataset-manifest", type=Path, default=DEFAULT_DATASET)
    parser.add_argument(
        "--xsd-serialization-manifest",
        type=Path,
        default=DEFAULT_XSD_SERIALIZATION_MANIFEST,
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    manifest = build_manifest(
        plan_path=args.plan,
        xsd_path=args.xsd,
        dataset_manifest_path=args.dataset_manifest,
        xsd_serialization_manifest_path=args.xsd_serialization_manifest,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    validate_manifest(
        args.output,
        plan_path=args.plan,
        xsd_path=args.xsd,
        dataset_manifest_path=args.dataset_manifest,
        xsd_serialization_manifest_path=args.xsd_serialization_manifest,
    )
    print(json.dumps({"valid": True, "validator_sha256": manifest["validator_sha256"], "source_file_count": len(manifest["source_files"])}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
