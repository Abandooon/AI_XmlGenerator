"""Create a self-contained, hash-inventoried PIL V4 prepaid package."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pil_v4_contract as contract
import pil_v4_schedule


PIL_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PIL_ROOT.parent

REPO_FILES = (
    "Private_International_Law/PIL_V41_PREFLIGHT_READINESS.json",
    "Private_International_Law/PIL_V4_ADJUDICATION_RECORD.json",
    "Private_International_Law/PIL_D1_ACCEPTANCE.json",
    "Private_International_Law/PIL_V41_AUTOSAR_V20_PARAMETER_MATCH.json",
    "Private_International_Law/PIL_V4_SUPERSEDED_NO_CALL_AUTHORIZATION.json",
    "Private_International_Law/PIL_V4_DESIGN_AUDIT_ABORT_2026-09-04.json",
    "Private_International_Law/PIL_V41_ENGLISH_INPUT_MANIFEST.json",
    "Private_International_Law/PIL_V41_ENGLISH_LEGAL_SOURCE_AUDIT.json",
    "Private_International_Law/PIL_V41_TRANSLATION_PARITY_ACCEPTANCE.json",
    "Private_International_Law/PIL_V41_RENDERED_PROMPTS.jsonl",
    "Private_International_Law/PIL_V41_PREPAID_CODE_AUDIT.json",
    "Private_International_Law/data/inference_dataset_v4.jsonl",
    "Private_International_Law/data/inference_dataset_v41_en.jsonl",
    "Private_International_Law/data/consensus_gold_v4.jsonl",
    "Private_International_Law/kb/authoritative_provisions_v4.jsonl",
    "Private_International_Law/kb/authoritative_provisions_v41_en.jsonl",
    "Private_International_Law/schema/decision_schema_v4.json",
    "Private_International_Law/schema/consensus_gold_schema_v4.json",
    "Private_International_Law/rules/delivery_rules_v4.json",
    "Private_International_Law/review/PIL_C1_ACCEPTANCE_AND_INTERREVIEWER_REPORT_2026-09-03.md",
    "Private_International_Law/pil_v4_contract.py",
    "Private_International_Law/pil_v4_arms.py",
    "Private_International_Law/pil_v4_client.py",
    "Private_International_Law/pil_v4_provider.py",
    "Private_International_Law/pil_v4_schedule.py",
    "Private_International_Law/pil_v4_run.py",
    "Private_International_Law/pil_v4_rescore.py",
    "Private_International_Law/pil_v4_preflight.py",
    "Private_International_Law/pil_v4_authorize.py",
    "Private_International_Law/pil_v4_retained_diagnostic.py",
    "Private_International_Law/pil_v4_freeze_prepaid.py",
    "Private_International_Law/build_pil_v41_english_inputs.py",
    "Private_International_Law/pil_v41_render_prompts.py",
    "Private_International_Law/pil_v41_prepaid_audit.py",
    "docs/pil_v4_four_arm_replication_protocol.md",
    "docs/pil_v4_preflight_implementation_summary.md",
    "reports/pil_v4_retained_output_diagnostic.json",
    "reports/pil_v4_retained_output_diagnostic.md",
    "tests_v2/test_pil_v4.py",
    "tests_v2/test_workbench.py",
    "atlas_workbench.py",
    "src/workbench/artifacts.py",
    "config/atlas_experiment_registry.json",
    "reports/pil_v4_preflight_report.json",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _copy(source: Path, destination: Path) -> dict[str, Any]:
    if not source.is_file():
        raise FileNotFoundError(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    if _sha256(source) != _sha256(destination):
        raise ValueError(f"copy hash mismatch: {source}")
    return {"size_bytes": destination.stat().st_size, "sha256": _sha256(destination)}


def build(
    *, output: Path, builder: Path, c1_lock: Path, c2_lock: Path, d1_lock: Path,
    translation_review: Path,
) -> dict[str, Any]:
    if output.exists():
        raise FileExistsError(f"refusing to overwrite freeze directory: {output}")
    preflight = PIL_ROOT / "PIL_V41_PREFLIGHT_READINESS.json"
    blockers = pil_v4_schedule.readiness_blockers(
        preflight, require_execution_authorization=False,
    )
    if blockers:
        raise ValueError("preflight is not freezeable:\n- " + "\n- ".join(blockers))
    document = json.loads(preflight.read_text(encoding="utf-8"))
    if document.get("status") != "READY_FOR_PAID_AUTHORIZATION":
        raise ValueError("preflight does not have the expected zero-call ready status")
    translation_acceptance_path = PIL_ROOT / "PIL_V41_TRANSLATION_PARITY_ACCEPTANCE.json"
    translation_acceptance = json.loads(
        translation_acceptance_path.read_text(encoding="utf-8")
    )
    if translation_acceptance.get("accepted_workbook_sha256") != _sha256(translation_review):
        raise ValueError("completed translation-review workbook does not match its acceptance record")

    inventory: dict[str, dict[str, Any]] = {}
    for item in REPO_FILES:
        source = REPO_ROOT / item
        relative = Path(item).relative_to("Private_International_Law") if item.startswith("Private_International_Law/") else Path(item)
        inventory[relative.as_posix()] = _copy(source, output / relative)

    external = {
        "provenance/build_pil_v4_inputs.mjs": builder,
        "review_sources/C1/PIL_C1_ACCEPTANCE_RECORD.json": c1_lock / "PIL_C1_ACCEPTANCE_RECORD.json",
        "review_sources/C1/PIL_C1_INDEPENDENT_GOLD_REVIEW_YiRui_Wang_2026-09-02_RECHECKED_WITH_SOURCES.xlsx": c1_lock / "PIL_C1_INDEPENDENT_GOLD_REVIEW_YiRui_Wang_2026-09-02_RECHECKED_WITH_SOURCES.xlsx",
        "review_sources/C2/PIL_C2_ACCEPTANCE.json": c2_lock / "PIL_C2_ACCEPTANCE.json",
        "review_sources/C2/PIL_C2_ACCEPTANCE_SUMMARY.md": c2_lock / "PIL_C2_ACCEPTANCE_SUMMARY.md",
        "review_sources/C2/PIL_C2_DISAGREEMENT_CONSENSUS_REVIEW_v1_completed_xingyue_yang_yirui_wang.xlsx": c2_lock / "PIL_C2_DISAGREEMENT_CONSENSUS_REVIEW_v1_completed_xingyue_yang_yirui_wang.xlsx",
        "review_sources/D1/PIL_D1_ACCEPTANCE.json": d1_lock / "PIL_D1_ACCEPTANCE.json",
        "review_sources/D1/PIL_D1_INSPECTION.json": d1_lock / "PIL_D1_INSPECTION.json",
        "review_sources/D1/PIL_D1_AFFECTED_CASE_RECONFIRMATION_completed_2026-09-04.xlsx": d1_lock / "PIL_D1_AFFECTED_CASE_RECONFIRMATION_completed_2026-09-04.xlsx",
        "review_sources/translation/PIL_V41_ENGLISH_INPUT_PARITY_REVIEW_COMPLETED.xlsx": translation_review,
    }
    for relative, source in external.items():
        inventory[relative] = _copy(source, output / relative)

    packaged_preflight = output / "PIL_V41_PREFLIGHT_READINESS.json"
    packaged_blockers = pil_v4_schedule.readiness_blockers(
        packaged_preflight, require_execution_authorization=False,
    )
    if packaged_blockers:
        raise ValueError("packaged preflight verification failed:\n- " + "\n- ".join(packaged_blockers))

    body = {
        "schema_version": "atlas.pil.v4_prepaid_freeze.v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "FROZEN_READY_FOR_PAID_AUTHORIZATION",
        "formal_run_enabled": False,
        "external_calls_authorized": False,
        "provider_calls": 0,
        "paid_api_calls": 0,
        "preflight_raw_sha256": _sha256(packaged_preflight),
        "preflight_content_sha256": document["content_sha256"],
        "file_count": len(inventory),
        "files": dict(sorted(inventory.items())),
        "next_action": "Explicitly create a separate formal readiness manifest; do not edit this package or its preflight in place.",
    }
    stable = {key: value for key, value in body.items() if key != "created_at_utc"}
    manifest = {**body, "manifest_content_sha256": contract.canonical_sha256(stable)}
    manifest_path = output / "PIL_V41_PREPAID_FREEZE_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--builder", type=Path, required=True)
    parser.add_argument("--c1-lock", type=Path, required=True)
    parser.add_argument("--c2-lock", type=Path, required=True)
    parser.add_argument("--d1-lock", type=Path, required=True)
    parser.add_argument("--translation-review", type=Path, required=True)
    args = parser.parse_args(argv)
    manifest = build(
        output=args.output, builder=args.builder, c1_lock=args.c1_lock,
        c2_lock=args.c2_lock, d1_lock=args.d1_lock,
        translation_review=args.translation_review,
    )
    print(json.dumps({
        "output": str(args.output), "status": manifest["status"],
        "file_count": manifest["file_count"],
        "manifest_content_sha256": manifest["manifest_content_sha256"],
        "provider_calls": 0,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
