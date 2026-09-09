"""Create a non-overwriting, hash-inventoried PIL V4.1 formal evidence archive."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pil_v4_contract as contract


ROOT = Path(__file__).resolve().parent
FORMAL_FILES = (
    "PIL_V41_FORMAL_READINESS.json",
    "PIL_V41_FORMAL_SCHEDULE.json",
    "PIL_V41_RUN_LEDGER.jsonl",
    "PIL_V41_RUN_MANIFEST.json",
    "PIL_V41_FORMAL_ANALYSIS.json",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _copy(source: Path, destination: Path) -> None:
    if not source.is_file():
        raise FileNotFoundError(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    if _sha256(source) != _sha256(destination):
        raise ValueError(f"copy hash mismatch: {source}")


def _inventory(root: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix()
        rows[relative] = {"size_bytes": path.stat().st_size, "sha256": _sha256(path)}
    return rows


def build(*, output: Path, prepaid_freeze: Path) -> dict[str, Any]:
    if output.exists():
        raise FileExistsError(f"refusing to overwrite formal archive: {output}")
    freeze_manifest_path = prepaid_freeze / "PIL_V41_PREPAID_FREEZE_MANIFEST.json"
    freeze_manifest = _json(freeze_manifest_path)
    if freeze_manifest.get("status") != "FROZEN_READY_FOR_PAID_AUTHORIZATION":
        raise ValueError("prepaid freeze does not have the required status")

    run_manifest = _json(ROOT / "PIL_V41_RUN_MANIFEST.json")
    analysis = _json(ROOT / "PIL_V41_FORMAL_ANALYSIS.json")
    schedule = _json(ROOT / "PIL_V41_FORMAL_SCHEDULE.json")
    if not (
        run_manifest.get("run_complete") is True
        and run_manifest.get("promotable") is True
        and run_manifest.get("ledger_line_count") == 720
        and run_manifest.get("units_pending") == 0
        and not run_manifest.get("unresolved_infrastructure_failed_units")
    ):
        raise ValueError("formal run manifest is incomplete or non-promotable")
    if analysis.get("unit_count") != 720 or analysis.get("case_count") != 60:
        raise ValueError("formal analysis has an unexpected analysis population")
    if analysis.get("inputs", {}).get("ledger_sha256") != _sha256(
        ROOT / "PIL_V41_RUN_LEDGER.jsonl"
    ):
        raise ValueError("analysis is not bound to the final ledger")
    if run_manifest.get("schedule_sha256") != schedule.get("content_sha256"):
        raise ValueError("run manifest is not bound to the formal schedule")

    output.mkdir(parents=True)
    shutil.copytree(prepaid_freeze, output / "prepaid_freeze")
    for name in FORMAL_FILES:
        _copy(ROOT / name, output / "formal" / name)
    _copy(Path(__file__).resolve(), output / "provenance" / Path(__file__).name)

    inventory = _inventory(output)
    body = {
        "schema_version": "atlas.pil.formal_archive.v4.1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "COMPLETE_PROMOTABLE_FORMAL_EVIDENCE",
        "experiment_identity": "PIL-V41-FOUR-ARM-ENGLISH",
        "formal_units": 720,
        "case_count": 60,
        "arm_counts": {"p0": 180, "p1": 180, "p2": 180, "p3": 180},
        "run_manifest_content_sha256": run_manifest.get("content_sha256"),
        "analysis_content_sha256": analysis.get("content_sha256"),
        "schedule_content_sha256": schedule.get("content_sha256"),
        "prepaid_freeze_manifest_raw_sha256": _sha256(freeze_manifest_path),
        "prepaid_freeze_manifest_content_sha256": freeze_manifest.get(
            "manifest_content_sha256"
        ),
        "file_count_before_archive_manifest": len(inventory),
        "files": inventory,
    }
    stable = {key: value for key, value in body.items() if key != "created_at_utc"}
    document = {**body, "content_sha256": contract.canonical_sha256(stable)}
    manifest_path = output / "PIL_V41_FORMAL_ARCHIVE_MANIFEST.json"
    manifest_path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return document


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--prepaid-freeze", type=Path, required=True)
    args = parser.parse_args(argv)
    document = build(output=args.output, prepaid_freeze=args.prepaid_freeze)
    manifest_path = args.output / "PIL_V41_FORMAL_ARCHIVE_MANIFEST.json"
    print(json.dumps({
        "output": str(args.output),
        "status": document["status"],
        "file_count_before_archive_manifest": document["file_count_before_archive_manifest"],
        "manifest_raw_sha256": _sha256(manifest_path),
        "manifest_content_sha256": document["content_sha256"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
