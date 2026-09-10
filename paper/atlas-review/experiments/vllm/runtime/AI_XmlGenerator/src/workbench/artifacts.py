"""Fail-closed, read-only loaders for the three ATLAS evidence domains."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


REPOSITORY = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY = REPOSITORY / "config" / "atlas_experiment_registry.json"


class WorkbenchArtifactError(ValueError):
    """Raised when an evidence artifact is missing or structurally unusable."""


def _object(path: str | Path) -> dict[str, Any]:
    target = Path(path).expanduser().resolve()
    if not target.is_file():
        raise WorkbenchArtifactError(f"artifact is missing: {target}")
    try:
        value = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise WorkbenchArtifactError(f"artifact is not valid JSON: {target}") from error
    if not isinstance(value, dict):
        raise WorkbenchArtifactError(f"artifact root must be an object: {target}")
    return value


def load_registry(path: str | Path = DEFAULT_REGISTRY) -> dict[str, Any]:
    registry = _object(path)
    if registry.get("schema_version") != "atlas.experiment_registry.v1":
        raise WorkbenchArtifactError("unsupported experiment registry schema")
    policy = registry.get("policy") or {}
    if policy.get("legacy_results_allowed_in_primary_tables") is not False:
        raise WorkbenchArtifactError("registry must fail closed against legacy primary results")
    if policy.get("paper_and_promotion_require_active_identity") is not True:
        raise WorkbenchArtifactError("registry must gate paper and promotion identities")
    predecessor_roles = set(policy.get("predecessor_allowed_roles") or [])
    if predecessor_roles != {"archive", "regression"}:
        raise WorkbenchArtifactError(
            "registry must limit predecessor evidence to archive/regression"
        )
    return registry


def assert_latest_autosar_identity(
    manifest: dict[str, Any],
    *,
    purpose: str,
    registry_path: str | Path = DEFAULT_REGISTRY,
) -> dict[str, Any]:
    """Enforce the registry at every paper/promotion AUTOSAR load boundary."""
    registry = load_registry(registry_path)
    autosar = (registry.get("experiments") or {}).get("autosar") or {}
    predecessor = autosar.get("predecessor_result") or {}
    schedule_sha256 = str(manifest.get("schedule_content_sha256") or "")
    if not schedule_sha256:
        raise WorkbenchArtifactError("AUTOSAR manifest has no schedule identity")
    if schedule_sha256 == predecessor.get("schedule_sha256"):
        if purpose not in set(registry["policy"]["predecessor_allowed_roles"]):
            raise WorkbenchArtifactError(
                "E1-V15 is an immutable predecessor usable only for archive/regression"
            )
        return {
            "registry_role": purpose,
            "registry_identity": predecessor.get("id"),
            "registry_decision": "PASS",
        }
    if purpose in {"paper_primary", "promotion", "latest_dashboard"}:
        if autosar.get("active_result_status") != "CURRENT_FORMAL_RESULT":
            raise WorkbenchArtifactError(
                "no current V17 formal result is registered for paper/promotion"
            )
        if schedule_sha256 != autosar.get("active_schedule_sha256"):
            raise WorkbenchArtifactError(
                "AUTOSAR artifact is not the registry's active V17 identity"
            )
        if not str(autosar.get("active_code_line") or "").startswith("V17"):
            raise WorkbenchArtifactError("active AUTOSAR code line is not V17")
        return {
            "registry_role": purpose,
            "registry_identity": autosar.get("active_result_id"),
            "registry_decision": "PASS",
        }
    raise WorkbenchArtifactError(f"unsupported AUTOSAR registry purpose: {purpose}")


def summarize_autosar_experiment(
    root: str | Path,
    *,
    purpose: str = "latest_dashboard",
    registry_path: str | Path = DEFAULT_REGISTRY,
) -> dict[str, Any]:
    experiment_root = Path(root).expanduser().resolve()
    manifest = _object(experiment_root / "full_experiment_manifest.json")
    registry_gate = assert_latest_autosar_identity(
        manifest, purpose=purpose, registry_path=registry_path
    )
    generation = _object(experiment_root / "generation" / "experiment_results.json")
    repair = _object(experiment_root / "repair" / "repair_results.json")
    records = generation.get("records")
    repair_records = repair.get("records")
    if not isinstance(records, list) or not isinstance(repair_records, list):
        raise WorkbenchArtifactError("AUTOSAR results are missing record arrays")

    status_counts = Counter(str(item.get("status")) for item in records)
    completed = [item for item in records if item.get("status") == "COMPLETE"]
    strict_pass = [item for item in records if item.get("independent_decision") == "PASS"]
    xsd_status_counts = {"PASS": 0, "FAIL": 0, "NOT_EVALUATED": 0}
    for item in records:
        value = item.get("xsd_all_pass")
        if value is True:
            xsd_status_counts["PASS"] += 1
        elif value is False:
            xsd_status_counts["FAIL"] += 1
        else:
            xsd_status_counts["NOT_EVALUATED"] += 1
    if sum(xsd_status_counts.values()) != len(records):
        raise WorkbenchArtifactError("XSD status counters do not cover every run")
    repair_cohorts = Counter(str(item.get("cohort")) for item in repair_records)
    repair_success = Counter(
        str(item.get("cohort"))
        for item in repair_records
        if item.get("strict_restoration") is True
        or item.get("strict_success") is True
        or item.get("attempt_outcome") in {
            "accepted_strict_improvement",
            "resolved",
        }
    )
    return {
        "domain": "AUTOSAR",
        "experiment_complete": manifest.get("experiment_complete") is True,
        "manifest_sha256": manifest.get("content_sha256"),
        "schedule_sha256": manifest.get("schedule_content_sha256"),
        **registry_gate,
        "scheduled_runs": len(records),
        "status_counts": dict(sorted(status_counts.items())),
        "completed_artifact_runs": len(completed),
        "strict_pass_runs": len(strict_pass),
        "xsd_status_counts": xsd_status_counts,
        "xsd_evaluated_runs": xsd_status_counts["PASS"] + xsd_status_counts["FAIL"],
        "xsd_pass_runs": xsd_status_counts["PASS"],
        "xsd_fail_runs": xsd_status_counts["FAIL"],
        "xsd_not_evaluated_runs": xsd_status_counts["NOT_EVALUATED"],
        "repair_records": len(repair_records),
        "repair_cohorts": dict(sorted(repair_cohorts.items())),
        "repair_strict_success": dict(sorted(repair_success.items())),
    }


def summarize_pil_manifest(path: str | Path) -> dict[str, Any]:
    manifest = _object(path)
    progress = manifest.get("progress") or {}
    arms = ((manifest.get("summary") or {}).get("arms") or {})
    arm_rows: dict[str, Any] = {}
    for arm, value in sorted(arms.items()):
        if not isinstance(value, dict):
            continue
        arm_rows[arm] = {
            "report_name": value.get("arm_report_name") or arm,
            "cases": value.get("cases"),
            "final_output_accuracy": value.get("final_output_accuracy"),
            "promotion_coverage": value.get("promotion_coverage"),
            "selective_accuracy": value.get("selective_accuracy"),
        }
    return {
        "domain": "Private International Law",
        "promotable": manifest.get("promotable") is True,
        "schedule_sha256": manifest.get("schedule_sha256"),
        "contract_sha256": manifest.get("contract_sha256"),
        "units_total": progress.get("units_total"),
        "units_completed": progress.get("units_completed_after"),
        "units_missing": len(manifest.get("units_missing") or []),
        "arms": arm_rows,
    }


def summarize_pil_provenance(path: str | Path) -> dict[str, Any]:
    document = _object(path)
    if document.get("schema_version") != "atlas.pil.dataset_provenance.v1":
        raise ValueError("artifact is not a PIL V2 dataset provenance addendum")
    characterization = document.get("dataset_characterization") or {}
    strengthening = document.get("required_strengthening_before_strong_gold_validity_claim") or {}
    return {
        "domain": "Private International Law",
        "experiment_id": document.get("experiment_id"),
        "status": document.get("status"),
        "dataset_sha256": (document.get("frozen_links") or {}).get("dataset_sha256"),
        "case_count": (document.get("frozen_links") or {}).get("dataset_case_count"),
        "case_type": characterization.get("case_type"),
        "author_role": characterization.get("author_role"),
        "real_case_records": characterization.get("real_case_records") is True,
        "representative_sample_claimed": characterization.get("representative_sample_claimed") is True,
        "independent_review": strengthening.get("independent_review"),
        "created_after_formal_run": document.get("created_after_formal_run") is True,
        "part_of_original_freeze": document.get("part_of_original_freeze") is True,
        "mutates_frozen_experiment": document.get("mutates_frozen_experiment") is True,
        "claim_boundary": document.get("claim_boundary") or {},
    }


def summarize_besser_report(path: str | Path) -> dict[str, Any]:
    report = _object(path)
    summary = report.get("summary") or {}
    return {
        "domain": "BESSER",
        "role": "cross-domain evidence adapter case",
        "decision": report.get("decision"),
        "valid": report.get("valid") is True,
        "finding_count": summary.get("finding_count"),
        "status_counts": {
            key: summary.get(key)
            for key in ("PASS", "FAIL", "NOT_EVALUATED", "ERROR")
        },
        "repair_enabled": (report.get("repair_audit") or {}).get("enabled") is True,
        "pooled_with_other_domains": False,
    }


def summarize_train_benchmark_report(path: str | Path) -> dict[str, Any]:
    """Normalize the Train/BESSER/ATLAS preflight without pooling metrics."""
    report = _object(path)
    if report.get("adapter") != "TrainBenchmarkS2Adapter":
        raise ValueError("artifact is not a TrainBenchmarkS2Adapter report")
    summary = report.get("summary") or {}
    source = report.get("source") or {}
    authority = source.get("authority") or {}
    return {
        "domain": "Train Benchmark via BESSER",
        "experiment_id": (report.get("validation_context") or {}).get("experiment_id"),
        "role": "cross-domain layered-constraint qualification",
        "decision": report.get("decision"),
        "evidence_valid": report.get("evidence_valid") is True,
        "formal_run_allowed": report.get("formal_run_allowed") is True,
        "promotion_allowed": report.get("promotion_allowed") is True,
        "authority": {
            "repository": "https://github.com/FTSRG/trainbenchmark",
            "commit": authority.get("commit"),
            "verified": authority.get("verified") is True,
        },
        "design": {
            "rules": 6,
            "sizes": 3,
            "states": 3,
            "formal_units": summary.get("formal_units"),
            "repair_pairs": summary.get("repair_pairs"),
        },
        "metrics": {
            "oracle_exact_units": summary.get("oracle_exact_units"),
            "true_positive_tokens": summary.get("true_positive_tokens"),
            "false_positive_tokens": summary.get("false_positive_tokens"),
            "false_negative_tokens": summary.get("false_negative_tokens"),
            "precision": summary.get("precision"),
            "recall": summary.get("recall"),
            "f1": summary.get("f1"),
            "posterior_repair_passes": summary.get("posterior_repair_passes"),
            "unexpected_promotions": summary.get("unexpected_promotions"),
        },
        "gates": report.get("gates") or {},
        "scope": {
            "llm_calls": summary.get("llm_calls"),
            "paid_api_calls": summary.get("paid_api_calls"),
            "pooled_with_other_domains": False,
            "paper_result_frozen": False,
        },
    }
