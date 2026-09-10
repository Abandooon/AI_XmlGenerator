"""Build the deterministic final manifest for the repaired ATLAS Phase1/2 cohort."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from audit_phase12_output import audit


PROBE_ROOT = Path(__file__).resolve().parent
ATLAS_ROOT = Path(r"E:\git projects\AI_XmlGenerator")
COHORT_ROOT = PROBE_ROOT / "outputs" / "repaired-phase12-xsd-path-contract-v7"
OUTPUT = PROBE_ROOT / "XSD_PATH_CONTRACT_MODEL_RERUN_MANIFEST.json"
AUDIT_ROOT = PROBE_ROOT / "audits" / "xsd-path-contract-v7"
LOCAL_ACCEPTANCE = PROBE_ROOT / "LOCAL_PIPELINE_ACCEPTANCE_MANIFEST.json"
MODELS = ("gpt-5.6-luna", "gpt-5.6-terra", "gpt-5.6-sol")
XSD = ATLAS_ROOT / "src" / "validation" / "data" / "AUTOSAR_4-2-2.xsd"

SCOPED_CODE = (
    "llm_rag_generator_auto.py",
    "src/llm_generation/core/round1_designer.py",
    "src/llm_generation/core/round2_generator.py",
    "src/llm_generation/core/xsd_serializer.py",
    "src/llm_generation/knowledge/dynamic_query_engine.py",
    "src/llm_generation/knowledge/element_selection.py",
    "src/llm_generation/knowledge/xsd_content_index.py",
    "src/llm_generation/knowledge/xsd_selection_paths.py",
    "src/llm_generation/knowledge/v2/generation_adapter.py",
    "src/llm_generation/knowledge/v2/retrieval_cards.jsonl",
    "src/llm_generation/knowledge/v2/retrieval_manifest.json",
    "src/validation/v2/selection_obligations.py",
    "src/validation/v2/validator_manifest.json",
    "tests_v2/test_element_selection_pipeline.py",
    "tests_v2/test_generation_constraint_adapter.py",
    "tests_v2/test_xsd_selection_paths.py",
)

EXCLUDED_DIAGNOSTICS = (
    (
        "outputs/repaired-phase12-xsd-path-contract/gpt-5.6-luna",
        "anchor index projection rejected before Phase2; chain-repair diagnostic",
    ),
    (
        "outputs/repaired-phase12-xsd-path-contract-v2/gpt-5.6-sol",
        "physical RUNNABLES wrapper was incorrectly exposed as a provider path",
    ),
    (
        "outputs/repaired-phase12-xsd-path-contract-v3/gpt-5.6-luna",
        "V2 required-existence and local reference normalization diagnostic",
    ),
    (
        "outputs/repaired-phase12-xsd-path-contract-v4/gpt-5.6-sol",
        "component-local /ASW path alias normalization diagnostic",
    ),
    (
        "outputs/repaired-phase12-xsd-path-contract-v5/gpt-5.6-luna",
        "single-segment provider projection diagnostic",
    ),
    (
        "outputs/repaired-phase12-xsd-path-contract-v6",
        "successful pre-final cohort excluded because free-form Phase1 prose still affected constraint ranking",
    ),
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return sha256_bytes(encoded)


def one(paths: list[Path], label: str) -> Path:
    if len(paths) != 1:
        raise RuntimeError(f"expected one {label}, found {len(paths)}")
    return paths[0]


def git_value(*args: str) -> str:
    return subprocess.check_output(
        ["git", "-c", f"safe.directory={ATLAS_ROOT.as_posix()}", *args],
        cwd=ATLAS_ROOT,
        text=True,
        encoding="utf-8",
    ).strip()


def final_model_record(model: str) -> tuple[dict[str, Any], dict[str, Any], str]:
    root = COHORT_ROOT / model
    summary_path = root / "run_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if summary.get("model") != model or summary.get("error"):
        raise RuntimeError(f"invalid final run summary for {model}")
    if summary.get("final_status") != "generated_with_incomplete_validation":
        raise RuntimeError(f"unexpected final status for {model}: {summary.get('final_status')}")

    for relative, declared_hash in (summary.get("artifact_hashes") or {}).items():
        path = root / relative
        actual_hash = sha256_file(path)
        if actual_hash != declared_hash:
            raise RuntimeError(
                f"artifact hash mismatch for {model}/{relative}: "
                f"{declared_hash} != {actual_hash}"
            )

    arxml_root = root / "atlas_output" / "ARXML"
    component = one(list((arxml_root / "Components").glob("*.arxml")), "component")
    interfaces = sorted((arxml_root / "Interfaces").glob("*.arxml"))
    if len(interfaces) != 2:
        raise RuntimeError(f"expected two interfaces for {model}")
    validation = one(
        [
            path
            for path in arxml_root.glob("validation_*.json")
            if "validation_context_" not in path.name
        ],
        "validation report",
    )
    validation_context = one(
        list(arxml_root.glob("validation_context_*.json")), "validation context"
    )
    phase1 = one(
        list((root / "atlas_output" / "round1_data").glob("*.json")),
        "Phase1 artifact",
    )

    parsed_audit = audit(component, interfaces, validation)
    if (
        parsed_audit.get("decision") != "INCOMPLETE"
        or parsed_audit.get("structural_failure_count") != 0
        or parsed_audit.get("local_reference_failure_count") != 0
        or any(item.get("status") != "PASS" for item in parsed_audit.get("xsd") or [])
    ):
        raise RuntimeError(f"final parsed audit failed for {model}")
    v2_summary = (parsed_audit.get("v2") or {}).get("summary") or {}
    if int(v2_summary.get("FAIL") or 0) or int(v2_summary.get("ERROR") or 0):
        raise RuntimeError(f"final V2 audit has failures for {model}")

    AUDIT_ROOT.mkdir(parents=True, exist_ok=True)
    audit_path = AUDIT_ROOT / f"{model}.json"
    audit_path.write_text(
        json.dumps(parsed_audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    phase1_payload = json.loads(phase1.read_text(encoding="utf-8"))
    prompt_hash = sha256_bytes(str(phase1_payload.get("prompt") or "").encode("utf-8"))
    validation_payload = json.loads(validation.read_text(encoding="utf-8"))
    selection_report = validation_payload.get("selection_obligations") or {}

    record = {
        "run_root": str(root),
        "run_summary": {
            "path": str(summary_path),
            "sha256": sha256_file(summary_path),
            "final_status": summary["final_status"],
            "completed_at_utc": summary["completed_at_utc"],
        },
        "phase1": summary.get("phase1"),
        "phase2": summary.get("phase2"),
        "phase1_prompt_sha256": prompt_hash,
        "artifacts": {
            "component": {"path": str(component), "sha256": sha256_file(component)},
            "interfaces": [
                {"path": str(path), "sha256": sha256_file(path)}
                for path in interfaces
            ],
            "validation": {
                "path": str(validation),
                "sha256": sha256_file(validation),
            },
            "validation_context": {
                "path": str(validation_context),
                "sha256": sha256_file(validation_context),
            },
            "phase1_raw": {"path": str(phase1), "sha256": sha256_file(phase1)},
            "parsed_audit": {"path": str(audit_path), "sha256": sha256_file(audit_path)},
        },
        "acceptance": {
            "xsd_document_count": len(parsed_audit["xsd"]),
            "all_xsd_pass": all(item["status"] == "PASS" for item in parsed_audit["xsd"]),
            "structural_failure_count": parsed_audit["structural_failure_count"],
            "local_reference_failure_count": parsed_audit["local_reference_failure_count"],
            "v2_decision": parsed_audit["v2"]["decision"],
            "v2_summary": parsed_audit["v2"]["summary"],
            "selection_obligation_decision": selection_report.get("decision"),
            "selection_obligation_finding_count": len(selection_report.get("findings") or []),
            "overall": "XSD_VALID_ZERO_FINDINGS_INCOMPLETE_CONTEXT",
        },
    }
    return record, parsed_audit, sha256_file(validation_context)


def diagnostic_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for relative, reason in EXCLUDED_DIAGNOSTICS:
        path = PROBE_ROOT / relative
        summaries = sorted(path.rglob("run_summary.json")) if path.exists() else []
        records.append(
            {
                "path": str(path),
                "reason": reason,
                "promotable": False,
                "run_summaries": [
                    {"path": str(item), "sha256": sha256_file(item)} for item in summaries
                ],
            }
        )
    return records


def main() -> int:
    local = json.loads(LOCAL_ACCEPTANCE.read_text(encoding="utf-8"))
    if local.get("decision") != "LOCAL_CHAIN_ACCEPTED_FAIL_CLOSED":
        raise RuntimeError("local pipeline acceptance is not green")

    models: dict[str, Any] = {}
    prompt_hashes: set[str] = set()
    context_hashes: set[str] = set()
    completion_times: list[str] = []
    for model in MODELS:
        record, _parsed_audit, context_hash = final_model_record(model)
        models[model] = record
        prompt_hashes.add(record["phase1_prompt_sha256"])
        context_hashes.add(context_hash)
        completion_times.append(record["run_summary"]["completed_at_utc"])
    if len(prompt_hashes) != 1:
        raise RuntimeError("final Phase1 prompts are not byte-identical")
    if len(context_hashes) != 1:
        raise RuntimeError("final validation contexts are not byte-identical")

    manifest: dict[str, Any] = {
        "schema_version": "atlas.xsd-path-contract-rerun.v1",
        "evidence_cutoff_utc": max(completion_times),
        "case_id": "ASW-STD-07",
        "cohort": {
            "path": str(COHORT_ROOT),
            "model_count": len(MODELS),
            "models": list(MODELS),
            "external_model_api_calls": 3,
            "same_final_code": True,
            "phase1_prompts_byte_identical": True,
            "phase1_prompt_sha256": next(iter(prompt_hashes)),
            "validation_contexts_byte_identical": True,
            "validation_context_sha256": next(iter(context_hashes)),
        },
        "decision": "THREE_MODEL_CHAIN_RERUN_COMPLETE_XSD_VALID_INCOMPLETE",
        "ranking": {
            "permitted": False,
            "result": "NO_MODEL_WINNER",
            "reason": (
                "One curated case with partial validation context cannot establish a model ranking; "
                "all three results are INCOMPLETE despite zero findings."
            ),
        },
        "local_acceptance": {
            "path": str(LOCAL_ACCEPTANCE),
            "file_sha256": sha256_file(LOCAL_ACCEPTANCE),
            "acceptance_fingerprint_sha256": local["acceptance_fingerprint_sha256"],
            "manifest_content_sha256": local["manifest_content_sha256"],
            "decision": local["decision"],
            "test_count": local["evidence"]["gates"]["offline_target_tests"]["test_count"],
            "constraint_corpus_recompiled": local["evidence"]["execution_boundary"][
                "constraint_corpus_recompiled"
            ],
        },
        "repository": {
            "path": str(ATLAS_ROOT),
            "branch": git_value("branch", "--show-current"),
            "head": git_value("rev-parse", "HEAD"),
            "commit_or_push_performed": False,
            "preexisting_dirty_files_preserved": True,
        },
        "hashes": {
            "autosar_4_2_2_xsd_sha256": sha256_file(XSD),
            "runner_sha256": sha256_file(PROBE_ROOT / "run_phase12_case.py"),
            "audit_sha256": sha256_file(PROBE_ROOT / "audit_phase12_output.py"),
            "builder_sha256": sha256_file(Path(__file__)),
            "scoped_code": {
                relative: sha256_file(ATLAS_ROOT / relative) for relative in SCOPED_CODE
            },
        },
        "models": models,
        "excluded_diagnostics": diagnostic_records(),
        "execution_boundary": {
            "credentials_read_or_persisted_by_manifest_builder": False,
            "paper_experiments_performed": False,
            "excluded_domains": ["PIL", "BESSER", "cross_domain", "paper experiments"],
            "constraint_corpus_recompiled": False,
        },
    }
    manifest["manifest_content_sha256"] = canonical_sha256(manifest)
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
                "validation_context_sha256": manifest["cohort"][
                    "validation_context_sha256"
                ],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
