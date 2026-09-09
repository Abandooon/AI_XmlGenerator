"""Build the credential-free audit manifest for the repaired Phase 1/2 rerun."""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROBE_ROOT = Path(__file__).resolve().parent
ATLAS_ROOT = Path(r"E:\git projects\AI_XmlGenerator")
CASES_ROOT = Path(r"E:\54239\Documents\atlas_autosar_requirements_v3")
FINAL_ROOT = PROBE_ROOT / "outputs" / "repaired-phase12-final-contract"
OUTPUT = PROBE_ROOT / "REPAIRED_MODEL_RERUN_MANIFEST.json"
MODELS = ("gpt-5.6-luna", "gpt-5.6-terra", "gpt-5.6-sol")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_hash(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return sha256_bytes(payload)


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={ATLAS_ROOT.as_posix()}", *args],
        cwd=ATLAS_ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=True,
    )
    return result.stdout.strip()


def all_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): sha256_file(path)
        for path in sorted(item for item in root.rglob("*") if item.is_file())
        if path.name not in {"run_summary.json"}
    }


def phase1_record(model_root: Path) -> tuple[Path, dict[str, Any]]:
    paths = sorted((model_root / "atlas_output" / "round1_data").glob("*.json"))
    if len(paths) != 1:
        raise RuntimeError(f"expected one Phase 1 artifact under {model_root}, found {len(paths)}")
    return paths[0], json.loads(paths[0].read_text(encoding="utf-8"))


def terra_audit(model_root: Path, round1: dict[str, Any]) -> dict[str, Any]:
    from audit_phase12_output import audit
    from src.llm_generation.knowledge.element_selection import (
        normalize_component_reference_values,
    )
    from src.validation.v2.selection_obligations import validate_selection_obligations

    arxml_root = model_root / "atlas_output" / "ARXML"
    component_paths = sorted((arxml_root / "Components").glob("*.arxml"))
    interface_paths = sorted((arxml_root / "Interfaces").glob("*.arxml"))
    validation_paths = sorted(
        path
        for path in arxml_root.glob("validation_*.json")
        if "validation_context_" not in path.name
    )
    if len(component_paths) != 1 or len(interface_paths) != 2 or len(validation_paths) != 1:
        raise RuntimeError("Terra final bundle does not have the expected 1+2 ARXML shape")
    parsed = audit(component_paths[0], interface_paths, validation_paths[0])

    plans = json.loads(json.dumps(round1["response_data"]["component_plan"]))
    for plan in plans:
        plan["element_design"] = normalize_component_reference_values(
            plan.get("element_design") or {}, component_name=plan["name"]
        )
    bundle = {
        "components": {
            plans[0]["name"]: component_paths[0].read_text(encoding="utf-8")
        },
        "interfaces": {
            path.stem: path.read_text(encoding="utf-8") for path in interface_paths
        },
    }
    selected = validate_selection_obligations(bundle, plans)
    return {
        "decision": parsed["decision"],
        "pinned_xsd": {
            "decision": "PASS"
            if all(item["status"] == "PASS" for item in parsed["xsd"])
            else "FAIL",
            "files_checked": len(parsed["xsd"]),
            "error_count": sum(len(item["errors"]) for item in parsed["xsd"]),
        },
        "curated_parsed_structural_obligations": {
            "decision": "PASS" if parsed["structural_failure_count"] == 0 else "FAIL",
            "evaluated": len(parsed["structural_obligations"]),
            "failure_count": parsed["structural_failure_count"],
        },
        "phase1_parsed_selection_obligations": {
            "decision": selected["decision"],
            "evaluated": selected["evaluated"],
            "finding_count": len(selected["findings"]),
        },
        "same_bundle_references": {
            "decision": "PASS"
            if parsed["local_reference_failure_count"] == 0
            else "FAIL",
            "resolved": sum(
                item["status"] == "PASS" for item in parsed["reference_integrity"]
            ),
            "failed": parsed["local_reference_failure_count"],
            "not_evaluated": parsed["external_reference_not_evaluated_count"],
        },
        "atlas_v2": parsed["v2"],
    }


def model_evidence(model: str) -> dict[str, Any]:
    model_root = FINAL_ROOT / model
    summary_path = model_root / "run_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    round1_path, round1 = phase1_record(model_root)
    response_data = round1["response_data"]
    selections = [
        selection
        for component in response_data.get("component_plan") or []
        for selection in (component.get("element_design") or {}).get("selections") or []
    ]
    debug_root = model_root / "atlas_output" / "debug"
    interface_responses = sorted(debug_root.glob("round2_response_20*.json"))
    component_responses = sorted(debug_root.glob("round2_response_*_20*.json"))
    completed_provider_outputs = 1 + len(interface_responses) + len(component_responses)
    evidence: dict[str, Any] = {
        "model": model,
        "run_summary_sha256": sha256_file(summary_path),
        "final_status": summary["final_status"],
        "phase1": summary["phase1"],
        "phase2": summary["phase2"],
        "error": summary["error"],
        "phase1_prompt_sha256": sha256_bytes(round1["prompt"].encode("utf-8")),
        "phase1_response_semantic_sha256": canonical_hash(response_data),
        "phase1_selection_count": len(selections),
        "phase1_unsupported_count": sum(
            len((component.get("element_design") or {}).get("unsupported") or [])
            for component in response_data.get("component_plan") or []
        ),
        "completed_provider_output_count": completed_provider_outputs,
        "interface_provider_output_completed": len(interface_responses) == 1,
        "component_provider_output_completed": len(component_responses) == 1,
        "artifact_hashes": all_hashes(model_root),
    }
    if model == "gpt-5.6-terra":
        evidence["gates"] = terra_audit(model_root, round1)
    else:
        evidence["gates"] = {
            "phase1_local_json_schema": "PASS",
            "interface_phase2_provider_json": "PASS",
            "component_phase2_schema_compilation": "FAIL",
            "component_phase2_provider_call": "NOT_PERFORMED",
            "pinned_xsd": "NOT_EVALUATED_NO_FINAL_ARXML",
            "parsed_obligations": "NOT_EVALUATED_NO_FINAL_ARXML",
            "reference_integrity": "NOT_EVALUATED_NO_FINAL_ARXML",
            "atlas_v2": "NOT_EVALUATED_NO_FINAL_ARXML",
        }
    return evidence


def main() -> int:
    # Never inspect or inherit a provider secret while building evidence.
    os.environ["LLM_API_KEY"] = "manifest-offline-placeholder"
    if str(ATLAS_ROOT) not in sys.path:
        sys.path.insert(0, str(ATLAS_ROOT))
    acceptance = json.loads(
        (PROBE_ROOT / "LOCAL_PIPELINE_ACCEPTANCE_MANIFEST.json").read_text(encoding="utf-8")
    )
    noise = io.StringIO()
    with contextlib.redirect_stdout(noise), contextlib.redirect_stderr(noise):
        from src.llm_generation.core.round1_designer import Round1Designer

        phase1_schema = Round1Designer.__new__(Round1Designer)._build_architecture_schema()
        models = [model_evidence(model) for model in MODELS]

    prompt_hashes = sorted({item["phase1_prompt_sha256"] for item in models})
    status = git("status", "--short")
    excluded = []
    for relative, reason in (
        ("outputs/repaired-phase12/gpt-5.6-luna", "instance name used as XML path segment"),
        ("outputs/repaired-phase12-final/gpt-5.6-luna", "primitive text projection was unresolved"),
        ("outputs/repaired-phase12-final-pinned/gpt-5.6-luna", "component-local reference prefix and interface element selection were not yet compiled"),
    ):
        root = PROBE_ROOT / relative
        summary = root / "run_summary.json"
        if summary.exists():
            excluded.append(
                {
                    "path": relative,
                    "reason": reason,
                    "run_summary_sha256": sha256_file(summary),
                }
            )

    manifest: dict[str, Any] = {
        "schema_version": "atlas.autosar.repaired-model-rerun.v1",
        "created_at_utc": datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "case_id": "ASW-STD-07",
        "contract": "existing-atlas-phase1-phase2-neo4j-xsd-renderer-v2",
        "decision": "SINGLE_CASE_EVIDENCE_NO_MODEL_RANKING",
        "promotable_comparison": False,
        "credential_value_recorded": False,
        "constraint_corpus_recompiled": False,
        "repository": {
            "path": str(ATLAS_ROOT),
            "branch": git("branch", "--show-current"),
            "head": git("rev-parse", "HEAD"),
            "dirty_entry_count": len(status.splitlines()) if status else 0,
            "status_sha256": sha256_bytes(status.encode("utf-8")),
            "reset_clean_checkout_commit_push_performed": False,
        },
        "controlled_contract": {
            "phase1_prompt_byte_identical": len(prompt_hashes) == 1,
            "phase1_prompt_sha256": prompt_hashes[0] if len(prompt_hashes) == 1 else prompt_hashes,
            "phase1_json_schema_semantic_sha256": canonical_hash(phase1_schema),
            "local_acceptance_decision": acceptance["decision"],
            "local_acceptance_fingerprint_sha256": acceptance[
                "acceptance_fingerprint_sha256"
            ],
            "local_acceptance_manifest_content_sha256": acceptance[
                "manifest_content_sha256"
            ],
        },
        "input_and_implementation_hashes": {
            "asw_cases_v3_yaml_sha256": sha256_file(CASES_ROOT / "asw_cases_v3.yaml"),
            "render_cases_sha256": sha256_file(CASES_ROOT / "render_cases.py"),
            "runner_sha256": sha256_file(PROBE_ROOT / "run_phase12_case.py"),
            "manifest_builder_sha256": sha256_file(
                PROBE_ROOT / "build_repaired_rerun_manifest.py"
            ),
            "parsed_auditor_sha256": sha256_file(
                PROBE_ROOT / "audit_phase12_output.py"
            ),
            "acceptance_runner_sha256": sha256_file(
                PROBE_ROOT / "local_pipeline_acceptance.py"
            ),
            "handoff_sha256": sha256_file(PROBE_ROOT / "XSD_PIPELINE_REPAIR_HANDOFF.md"),
            "autosar_4_2_2_xsd_sha256": sha256_file(
                ATLAS_ROOT / "src/validation/data/AUTOSAR_4-2-2.xsd"
            ),
            "validator_manifest_sha256": sha256_file(
                ATLAS_ROOT / "src/validation/v2/validator_manifest.json"
            ),
            "scoped_files": acceptance["evidence"]["hashes"]["scoped_files"],
        },
        "models": models,
        "excluded_chain_repair_diagnostics": excluded,
        "interpretation": {
            "gpt-5.6-luna": "FAIL_CLOSED_INVALID_PHASE1_AUTOSAR_PATH",
            "gpt-5.6-terra": "GENERATED_XSD_VALID_AND_OBLIGATION_VALID_BUT_V2_INCOMPLETE",
            "gpt-5.6-sol": "FAIL_CLOSED_INVALID_PHASE1_AUTOSAR_PATH",
            "ranking": "NOT_ESTABLISHED_FROM_ONE_CASE_ONE_SAMPLE",
        },
    }
    manifest["manifest_content_sha256"] = canonical_hash(manifest)
    OUTPUT.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "decision": manifest["decision"],
                "manifest": str(OUTPUT),
                "manifest_content_sha256": manifest["manifest_content_sha256"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
