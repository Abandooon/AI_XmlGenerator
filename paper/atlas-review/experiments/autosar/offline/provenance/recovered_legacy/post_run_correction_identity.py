"""Cryptographic identity gates for a post-run AUTOSAR correction study.

The original execution is verified from the immutable receipt created before
source edits.  The correction implementation is verified independently from a
new file-map freeze.  This deliberately does not pretend that old model output
was produced by the corrected source tree.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
REPOSITORY = Path(r"E:\git projects\AI_XmlGenerator")
REQUIREMENTS_ROOT = Path(r"E:\54239\Documents\atlas_autosar_requirements_v3")
HELDOUT_ROOT = Path(r"E:\54239\Documents\atlas_autosar_heldout_v3")


class CorrectionIdentityError(ValueError):
    """Raised when either side of the correction provenance chain changes."""


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _object(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise CorrectionIdentityError(f"identity artifact is missing: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CorrectionIdentityError(f"identity artifact is not an object: {path}")
    return value


def _verify_canonical(
    value: dict[str, Any], *, hash_field: str, excluded: tuple[str, ...] = ()
) -> None:
    unsigned = {
        key: item
        for key, item in value.items()
        if key != hash_field and key not in excluded
    }
    if canonical_sha256(unsigned) != value.get(hash_field):
        raise CorrectionIdentityError(f"canonical identity mismatch: {hash_field}")


def _verify_file_map(root: Path, records: dict[str, Any], label: str) -> int:
    if not isinstance(records, dict) or not records:
        raise CorrectionIdentityError(f"{label} file map is empty")
    for relative, expected in sorted(records.items()):
        path = root / relative
        if not path.is_file() or sha256_file(path) != expected:
            raise CorrectionIdentityError(f"{label} file identity mismatch: {path}")
    return len(records)


def verify_as_executed_source(
    results_path: Path, receipt_path: Path
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Verify the old result without evaluating it against corrected source."""

    results_path = results_path.resolve()
    receipt_path = receipt_path.resolve()
    results = _object(results_path)
    receipt = _object(receipt_path)
    _verify_canonical(receipt, hash_field="content_sha256")
    _verify_canonical(results, hash_field="content_sha256")
    schedule = results.get("schedule") or {}
    if not isinstance(schedule, dict):
        raise CorrectionIdentityError("source generation schedule is absent")
    _verify_canonical(schedule, hash_field="content_sha256")
    if (
        receipt.get("schema_version") != "atlas.asw_v3.as_executed_evidence.v1"
        or receipt.get("decision") != "PASS"
        or receipt.get("model_outputs_rewritten") is not False
        or receipt.get("generation_results_content_sha256")
        != results.get("content_sha256")
        or receipt.get("schedule_content_sha256") != schedule.get("content_sha256")
        or int(receipt.get("generation_record_count") or 0)
        != int(results.get("record_count") or 0)
    ):
        raise CorrectionIdentityError("source result differs from as-executed receipt")
    if results.get("experiment_complete") is not True:
        raise CorrectionIdentityError("source generation experiment is incomplete")
    records = list(results.get("records") or [])
    if len(records) != int(results.get("record_count") or 0):
        raise CorrectionIdentityError("source generation record count mismatch")
    run_ids = [str(item.get("run_id") or "") for item in records]
    if not all(run_ids) or len(set(run_ids)) != len(run_ids):
        raise CorrectionIdentityError("source generation run identities are invalid")
    frozen_manifest_path = receipt_path.parent / "PAPER_ARTIFACT_FREEZE_MANIFEST.json"
    frozen_manifest = _object(frozen_manifest_path)
    _verify_canonical(frozen_manifest, hash_field="manifest_sha256")
    freeze = receipt.get("freeze_verification") or {}
    if (
        sha256_file(frozen_manifest_path) != freeze.get("manifest_file_sha256")
        or frozen_manifest.get("manifest_sha256") != freeze.get("manifest_sha256")
        or schedule.get("freeze_manifest_sha256") != freeze.get("manifest_sha256")
    ):
        raise CorrectionIdentityError("preserved execution freeze identity mismatch")
    evidence_root = receipt_path.parent
    copied = {
        "repository_files": ("repository_files", frozen_manifest.get("repository_files")),
        "experiment_files": ("experiment_files", frozen_manifest.get("experiment_files")),
        "requirement_files": (
            "requirement_files",
            (frozen_manifest.get("requirement_set") or {}).get("files"),
        ),
        "runtime_assets": ("runtime_assets", frozen_manifest.get("runtime_assets")),
        "unified_frontend_files": (
            "unified_frontend_files",
            (frozen_manifest.get("unified_frontend") or {}).get("files"),
        ),
        "heldout_files": (
            "heldout_files",
            (frozen_manifest.get("prospective_internally_authored_heldout") or {}).get("files"),
        ),
    }
    for count_key, (directory, file_map) in copied.items():
        observed = _verify_file_map(evidence_root / directory, file_map or {}, count_key)
        if observed != int((receipt.get("copied_file_counts") or {}).get(count_key) or 0):
            raise CorrectionIdentityError(f"preserved {count_key} count mismatch")
    return results, receipt


def verify_correction_freeze(path: Path) -> dict[str, Any]:
    path = path.resolve()
    manifest = _object(path)
    if manifest.get("schema_version") != "atlas.autosar.post_run_correction_freeze.v1":
        raise CorrectionIdentityError("unsupported correction freeze schema")
    _verify_canonical(manifest, hash_field="content_sha256", excluded=("created_at_utc",))
    roots = {
        "repository_files": REPOSITORY,
        "experiment_files": ROOT,
        "requirement_files": REQUIREMENTS_ROOT,
        "heldout_files": HELDOUT_ROOT,
    }
    counts: dict[str, int] = {}
    for key, root in roots.items():
        counts[key] = _verify_file_map(root, manifest.get(key) or {}, key)
    evidence = manifest.get("evidence_files") or {}
    if not isinstance(evidence, dict) or not evidence:
        raise CorrectionIdentityError("correction evidence file map is empty")
    for absolute, expected in sorted(evidence.items()):
        target = Path(absolute).resolve()
        if not target.is_file() or sha256_file(target) != expected:
            raise CorrectionIdentityError(
                f"correction evidence identity mismatch: {target}"
            )
    expected_counts = manifest.get("file_counts") or {}
    if any(counts[key] != int(expected_counts.get(key) or 0) for key in counts):
        raise CorrectionIdentityError("correction freeze file count mismatch")
    return manifest
