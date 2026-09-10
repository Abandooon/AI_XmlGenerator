"""Build a deterministic hash manifest for the paper-ready AUTOSAR artifacts."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

from local_pipeline_acceptance import (
    EXPECTED_BRANCH,
    EXPECTED_HEAD,
    FRONTEND_FILES,
    FRONTEND_ROOT,
    GIT_EXECUTABLE,
    REPOSITORY,
    SCOPED_FILES,
)
from experiment_freeze import (
    public_runtime_configuration_fingerprint,
    public_runtime_environment_fingerprint,
)
from replacement_policy import build_policy_artifact


ROOT = Path(__file__).resolve().parent
REQUIREMENTS_ROOT = Path(r"E:\54239\Documents\atlas_autosar_requirements_v3")
HELDOUT_ROOT = Path(r"E:\54239\Documents\atlas_autosar_heldout_v3")
EXPECTED_HELDOUT_SOURCE_SHA256 = (
    "78dc6d65672d896af3c19b50a5efbf5ca18d8237de9f32f2b7234cd6ff226945"
)
OUTPUT = ROOT / "PAPER_ARTIFACT_FREEZE_MANIFEST.json"

PROBE_FILES = (
    "LOCAL_PIPELINE_ACCEPTANCE_MANIFEST.json",
    "local_pipeline_acceptance.py",
    "ALL_REQUIREMENTS_OFFLINE_PRECHECK_MANIFEST.json",
    "precheck_all_asw_requirements.py",
    "test_precheck_all_asw_requirements.py",
    "CONTROLLED_REFERENCE_BASELINES_V16_MANIFEST.json",
    "controlled_repair_v16.py",
    "scripted_autosar_client.py",
    "delivery_classification.py",
    "replacement_policy.py",
    "REPLACEMENT_POLICY_V17.json",
    "run_observation.py",
    "heldout_v3_runtime.py",
    "offline_v17_e2e.py",
    "verify_workbench_browser.py",
    "verify_workbench_browser.cjs",
    "evidence_registry_gate.py",
    "test_controlled_repair_v16.py",
    "test_delivery_classification.py",
    "test_delivery_loop_e2e.py",
    "test_replacement_policy.py",
    "test_replacement_runner_e2e.py",
    "test_run_observation.py",
    "test_offline_v17_e2e.py",
    "test_heldout_v3_cli_e2e.py",
    "build_paper_artifact_manifest.py",
    "run_phase12_case.py",
    "experiment_runtime.py",
    "run_asw_v3_experiment.py",
    "run_asw_v3_full_experiment.py",
    "evaluate_asw_v3_run.py",
    "repair_asw_v3_run.py",
    "run_asw_v3_repair_experiment.py",
    "summarize_asw_v3_experiment.py",
    "summarize_asw_v3_repair.py",
    "summarize_heldout_v3.py",
    "test_summarize_heldout_v3.py",
    "test_run_phase12_case.py",
    "test_evaluate_asw_v3_run.py",
    "test_summarize_asw_v3_experiment.py",
    "test_build_paper_artifact_manifest.py",
    "test_asw_v3_repair_experiment.py",
    "build_requirement_contract_smoke_manifest.py",
    "test_build_requirement_contract_smoke_manifest.py",
    "REQUIREMENT_CONTRACT_SMOKE_MANIFEST.json",
    "FORMAL_EXPERIMENT_CONTRACT.json",
    "FORMAL_NEO4J_CONTEXT.json",
    "experiment_freeze.py",
    "neo4j_experiment_context.py",
    "freeze_formal_neo4j_context.py",
    "test_neo4j_experiment_context.py",
    "test_main_experiment_freeze.py",
    "test_run_asw_v3_full_experiment.py",
    "test_v17_pilot_archive.py",
)

REPOSITORY_PAPER_FILES: tuple[str, ...] = ()

RUNTIME_ASSETS = (
    "src/validation/data/AUTOSAR_4-2-2.xsd",
    "src/generate_formal_constraints/v2/validation_plan.json",
    "src/validation/v2/validator_manifest.json",
    "src/llm_generation/knowledge/v2/retrieval_cards.jsonl",
    "src/llm_generation/knowledge/v2/retrieval_manifest.json",
    "src/llm_generation/knowledge/v2/xsd_serialization_manifest.json",
)

HELDOUT_FILES = (
    "REVIEW_PACKAGE_MANIFEST.json",
    "CLAUDE_REVIEW_INSTRUCTIONS.md",
    "HUMAN_REVIEW_QUESTIONS.md",
    "README.md",
    "build_v15_structure_inventory.py",
    "heldout_cases.yaml",
    "review_response.schema.json",
    "test_validate_heldout.py",
    "v15_structure_inventory.json",
    "validate_heldout.py",
)
HELDOUT_REVIEW_FILES = {
    "claude": "claude_review.json",
    "human_autosar_reviewer": "human_autosar_review.json",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def file_records(root: Path, paths: Iterable[Path]) -> dict[str, str]:
    records: dict[str, str] = {}
    for path in sorted({item.resolve() for item in paths}):
        if not path.is_file():
            raise FileNotFoundError(path)
        records[path.relative_to(root.resolve()).as_posix()] = sha256_file(path)
    return records


def git_value(*arguments: str) -> str:
    process = subprocess.run(
        [
            str(GIT_EXECUTABLE),
            "-c",
            "safe.directory=E:/git projects/AI_XmlGenerator",
            *arguments,
        ],
        cwd=str(REPOSITORY),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    if process.returncode:
        raise RuntimeError((process.stderr or process.stdout).strip())
    return process.stdout.strip()


def verify_heldout_review(path: Path, *, expected_reviewer: str) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeError(
            f"held-out admission review is missing: {path.name}"
        )
    process = subprocess.run(
        [
            sys.executable,
            "-B",
            str(HELDOUT_ROOT / "validate_heldout.py"),
            "--review",
            str(path),
        ],
        cwd=str(HELDOUT_ROOT),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    if process.returncode:
        detail = (process.stderr or process.stdout).strip()
        raise RuntimeError(
            f"held-out admission review failed verification: {path.name}: {detail}"
        )
    try:
        result = json.loads(process.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"held-out admission verifier returned invalid JSON: {path.name}"
        ) from error
    if (
        result.get("decision") != "PASS"
        or result.get("reviewer") != expected_reviewer
        or result.get("review_decision") != "PASS"
        or result.get("source_sha256") != EXPECTED_HELDOUT_SOURCE_SHA256
    ):
        raise RuntimeError(
            f"held-out admission review is not an exact PASS: {path.name}"
        )
    return {
        "reviewer": expected_reviewer,
        "review_decision": "PASS",
        "source_sha256": result["source_sha256"],
        "file": path.name,
        "file_sha256": sha256_file(path),
    }


def build_manifest() -> dict[str, Any]:
    branch = git_value("branch", "--show-current")
    head = git_value("rev-parse", "HEAD")
    status = git_value("status", "--short")
    if branch != EXPECTED_BRANCH or head != EXPECTED_HEAD:
        raise RuntimeError(f"unexpected repository identity: {branch}@{head}")

    acceptance_path = ROOT / "LOCAL_PIPELINE_ACCEPTANCE_MANIFEST.json"
    acceptance = json.loads(acceptance_path.read_text(encoding="utf-8"))
    if acceptance.get("decision") != "LOCAL_CHAIN_ACCEPTED_FAIL_CLOSED":
        raise RuntimeError("local acceptance is not frozen PASS_FAIL_CLOSED")
    unsigned_acceptance = {
        key: value
        for key, value in acceptance.items()
        if key != "manifest_content_sha256"
    }
    if acceptance.get("manifest_content_sha256") != canonical_sha256(
        unsigned_acceptance
    ):
        raise RuntimeError("local acceptance manifest canonical hash mismatch")
    if acceptance.get("acceptance_fingerprint_sha256") != canonical_sha256(
        acceptance.get("evidence") or {}
    ):
        raise RuntimeError("local acceptance evidence fingerprint mismatch")
    acceptance_hashes = (acceptance.get("evidence") or {}).get("hashes") or {}
    scoped_hashes = acceptance_hashes.get("scoped_files") or {}
    expected_scoped = {
        relative: sha256_file(REPOSITORY / relative) for relative in SCOPED_FILES
    }
    if scoped_hashes != expected_scoped:
        raise RuntimeError("local acceptance is stale for the current scoped files")
    if acceptance_hashes.get("acceptance_runner_sha256") != sha256_file(
        ROOT / "local_pipeline_acceptance.py"
    ):
        raise RuntimeError("local acceptance runner changed after acceptance")
    frontend_gate = (acceptance.get("evidence") or {}).get("gates", {}).get(
        "unified_frontend_delivery"
    ) or {}
    expected_frontend_hashes = {
        relative: sha256_file(FRONTEND_ROOT / relative)
        for relative in FRONTEND_FILES
    }
    if (
        frontend_gate.get("decision") != "PASS"
        or frontend_gate.get("external_model_api_calls") != 0
        or frontend_gate.get("provider_calls_enabled") is not False
        or frontend_gate.get("file_sha256") != expected_frontend_hashes
    ):
        raise RuntimeError("local acceptance is stale for the unified frontend")
    heldout_acceptance = (acceptance.get("evidence") or {}).get("gates", {}).get(
        "prospective_heldout_v3"
    ) or {}
    expected_heldout_cells = {
        f"{tier}:{role}": 2
        for tier in ("minimal", "standard", "full")
        for role in ("REPLICATION", "EXTENSION")
    }
    if (
        heldout_acceptance.get("decision") != "PASS"
        or heldout_acceptance.get("source_sha256")
        != EXPECTED_HELDOUT_SOURCE_SHA256
        or heldout_acceptance.get("case_count") != 12
        or heldout_acceptance.get("run_count") != 36
        or heldout_acceptance.get("unit_of_analysis") != "case"
        or heldout_acceptance.get("repetitions_per_case") != 3
        or heldout_acceptance.get("structural_role_case_counts")
        != {"EXTENSION": 6, "REPLICATION": 6}
        or heldout_acceptance.get("tier_by_structural_role_case_counts")
        != expected_heldout_cells
        or heldout_acceptance.get("factorial_balance") != "PASS"
        or heldout_acceptance.get("case_exclusive_data_element_identities")
        != "PASS"
        or heldout_acceptance.get("v15_relation_ledger") != "PASS"
        or heldout_acceptance.get("v15_inventory_scope")
        != "requirement_content_and_structure_no_model_outputs"
        or heldout_acceptance.get("external_model_api_calls") != 0
        or heldout_acceptance.get("external_benchmark") is not False
        or heldout_acceptance.get("held_out_execution") is not False
    ):
        raise RuntimeError("local acceptance lacks the held-out V3 factorial gate")
    e2e_acceptance = (acceptance.get("evidence") or {}).get("gates", {}).get(
        "probe_fake_client_e2e"
    ) or {}
    if (
        e2e_acceptance.get("decision") != "PASS"
        or e2e_acceptance.get("external_model_api_calls") != 0
        or e2e_acceptance.get("full_context_failure_repair_interrupt_resume")
        is not True
        or e2e_acceptance.get("heldout_real_cli_exact_source_and_type_binding")
        is not True
        or e2e_acceptance.get("heldout_schedule_consumer_cohort_identity")
        is not True
        or e2e_acceptance.get("provider_call_transition_audit_exact_join")
        is not True
        or e2e_acceptance.get("sdk_retry_disabled_and_runtime_asserted")
        is not True
        or e2e_acceptance.get("replacement_provenance_tamper_gates")
        is not True
        or e2e_acceptance.get("replacement_schedule_consuming_runner")
        is not True
        or e2e_acceptance.get(
            "replacement_execution_external_model_api_calls"
        )
        != 0
        or e2e_acceptance.get("observer_reports_without_stop_authority")
        is not True
    ):
        raise RuntimeError("local acceptance lacks the fake-client E2E gates")

    precheck_path = ROOT / "CONTROLLED_REFERENCE_BASELINES_V16_MANIFEST.json"
    precheck = json.loads(precheck_path.read_text(encoding="utf-8"))
    unsigned_precheck = {
        key: value
        for key, value in precheck.items()
        if key not in {"content_sha256", "created_at_utc"}
    }
    if precheck.get("content_sha256") != canonical_sha256(unsigned_precheck):
        raise RuntimeError("all-requirements precheck canonical hash mismatch")
    coverage = precheck.get("coverage") or {}
    if (
        precheck.get("decision") != "PASS"
        or coverage.get("case_count") != 20
        or coverage.get("component_arxml_count") != 20
        or coverage.get("xsd_pass_count") != 85
        or coverage.get("selection_obligation_pass_count") != 20
        or coverage.get("controlled_mutation_injection_count") != 100
        or coverage.get("controlled_mutation_detection_count") != 100
        or coverage.get("controlled_core_fixed_operator_count") != 85
        or coverage.get("controlled_substitution_count") != 15
        or coverage.get("deterministic_reference_baseline_count") != 20
        or coverage.get("typed_repair_context_case_count") != 20
        or coverage.get("typed_repair_context_target_count") != 85
        or coverage.get("typed_mutation_injection_count") != 100
        or (precheck.get("execution_boundary") or {}).get(
            "external_model_api_calls"
        )
        != 0
    ):
        raise RuntimeError("all-requirements offline precheck is not complete PASS")
    reference_baselines = precheck.get("reference_baselines") or {}
    controlled_design = precheck.get("controlled_repair_design") or {}
    if (
        reference_baselines.get("materialized") is not True
        or reference_baselines.get("count") != 20
        or controlled_design.get("design_cell_count") != 100
        or controlled_design.get("scheduled_task_count") != 100
        or controlled_design.get("core_fixed_operator_task_count") != 85
        or controlled_design.get("substitution_task_count") != 15
        or len(precheck.get("records") or []) != 20
        or any(
            (record.get("interface_provider_boundary") or {}).get("reversible")
            is not True
            for record in precheck.get("records") or []
        )
    ):
        raise RuntimeError("controlled-reference/interface boundary is incomplete")

    heldout_manifest_path = HELDOUT_ROOT / "REVIEW_PACKAGE_MANIFEST.json"
    heldout_manifest = json.loads(
        heldout_manifest_path.read_text(encoding="utf-8")
    )
    heldout_reviews = {
        reviewer: verify_heldout_review(
            HELDOUT_ROOT / filename, expected_reviewer=reviewer
        )
        for reviewer, filename in HELDOUT_REVIEW_FILES.items()
    }
    heldout_declared = heldout_manifest.get("files") or {}
    expected_heldout_declared = {
        relative: sha256_file(HELDOUT_ROOT / relative)
        for relative in (*HELDOUT_FILES, *HELDOUT_REVIEW_FILES.values())
        if relative != "REVIEW_PACKAGE_MANIFEST.json"
    }
    if heldout_declared != expected_heldout_declared:
        raise RuntimeError("held-out review package manifest is stale")
    heldout_source_sha256 = sha256_file(HELDOUT_ROOT / "heldout_cases.yaml")
    heldout_inventory_path = HELDOUT_ROOT / "v15_structure_inventory.json"
    heldout_inventory = json.loads(
        heldout_inventory_path.read_text(encoding="utf-8")
    )
    unsigned_inventory = {
        key: value
        for key, value in heldout_inventory.items()
        if key != "inventory_content_sha256"
    }
    inventory_provenance = heldout_inventory.get("provenance") or {}
    if (
        heldout_source_sha256 != EXPECTED_HELDOUT_SOURCE_SHA256
        or heldout_manifest.get("schema_version")
        != "atlas.autosar.heldout.review_package.v3"
        or (heldout_manifest.get("claims") or {}).get("external_benchmark")
        is not False
        or heldout_inventory.get("scope")
        != "requirement_content_and_structure_no_model_outputs"
        or heldout_inventory.get("schema_version")
        != "atlas.autosar.v15_requirement_inventory.v2"
        or heldout_inventory.get("case_count") != 20
        or len(heldout_inventory.get("records") or []) != 20
        or heldout_inventory.get("inventory_content_sha256")
        != canonical_sha256(unsigned_inventory)
        or ((inventory_provenance.get("requirement_source") or {}).get("sha256"))
        != "3b61eb5926b5646a12f8767524192cd7ed65a39e27a37aa9672277058489e024"
        or ((inventory_provenance.get("formal_archive") or {}).get("manifest_sha256"))
        != "50d58236bbcd27b5b9f95c06f4e07deaec0096a88bf8625e679633e8a29a790c"
    ):
        raise RuntimeError("held-out source identity or evidence claim changed")

    rendered_path = REQUIREMENTS_ROOT / "rendered/run_manifest.json"
    rendered = json.loads(rendered_path.read_text(encoding="utf-8"))
    if rendered.get("validation", {}).get("status") != "PASS":
        raise RuntimeError("rendered requirement manifest is not valid")
    if len(rendered.get("runs") or []) != 60:
        raise RuntimeError("rendered requirement manifest does not contain 60 runs")

    prompt_paths = sorted((REQUIREMENTS_ROOT / "rendered/prompts").glob("ASW-*.txt"))
    requirement_paths = [
        REQUIREMENTS_ROOT / "asw_cases_v3.yaml",
        REQUIREMENTS_ROOT / "render_cases.py",
        REQUIREMENTS_ROOT / "test_render_cases.py",
        REQUIREMENTS_ROOT / "README.md",
        rendered_path,
        *prompt_paths,
    ]
    if len(prompt_paths) != 20:
        raise RuntimeError("expected exactly 20 rendered prompts")

    contract_path = ROOT / "FORMAL_EXPERIMENT_CONTRACT.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    generation_contract = contract.get("generation") or {}
    provider_registration = generation_contract.get("provider_registration") or {}
    orchestration_contract = generation_contract.get("orchestration") or {}
    retry_contract = generation_contract.get("retry_policy") or {}
    if provider_registration != {
        "requested_model": "gpt-5.6-luna",
        "provider_endpoint_sha256": (
            "f5a9a9ddfe1b4dac7276ccb59339acca10e9820aee221fc60ff1b349ad22d5b9"
        ),
        "request_timeout_seconds": 180.0,
        "max_attempts_per_call": 1,
        "transport_route_policy": "direct_no_environment_proxy",
    } or generation_contract.get("stream_responses") is not False:
        raise RuntimeError("formal provider registration is incomplete or changed")
    if (
        orchestration_contract.get("generation_child_hard_timeout_seconds")
        != 1800
        or orchestration_contract.get("repair_child_hard_timeout_seconds")
        != 1800
        or orchestration_contract.get("operator_stop_boundary")
        != "between_scheduled_runs_only"
        or orchestration_contract.get("operator_stop_sentinel")
        != "OPERATOR_STOP_REQUESTED"
        or orchestration_contract.get("operator_stop_sentinel_locations")
        != ["full_experiment_root", "generation_root"]
        or orchestration_contract.get("observer_may_stop_runner") is not False
        or generation_contract.get("transport_route_policy")
        != "direct_no_environment_proxy"
        or retry_contract
        != {
            "orchestrator_retry_on_timeout": "disabled",
            "orchestrator_retry_on_transport": "disabled",
            "provider_max_attempts_per_call": 1,
            "sdk_implicit_retry": "disabled",
        }
    ):
        raise RuntimeError("formal timeout, stop, observer, or retry policy changed")
    repair_contract = contract.get("repair_experiment") or {}
    if (
        repair_contract.get("controlled_design_cell_count") != 100
        or repair_contract.get("core_fixed_operator_task_count") != 85
        or repair_contract.get("substitution_task_count") != 15
        or repair_contract.get("core_operator_denominators")
        != controlled_design.get("core_repair_rate_denominators")
    ):
        raise RuntimeError("formal repair contract differs from controlled design")
    neo4j_context_path = ROOT / "FORMAL_NEO4J_CONTEXT.json"
    neo4j_context = json.loads(neo4j_context_path.read_text(encoding="utf-8"))
    unsigned_neo4j_context = {
        key: value
        for key, value in neo4j_context.items()
        if key != "context_sha256"
    }
    if neo4j_context.get("context_sha256") != canonical_sha256(
        unsigned_neo4j_context
    ):
        raise RuntimeError("formal Neo4j context canonical hash mismatch")
    replacement_policy_path = ROOT / "REPLACEMENT_POLICY_V17.json"
    replacement_policy = json.loads(
        replacement_policy_path.read_text(encoding="utf-8")
    )
    if replacement_policy != build_policy_artifact():
        raise RuntimeError(
            "replacement policy artifact is stale or not deterministically built"
        )

    validator_manifest = json.loads(
        (REPOSITORY / "src/validation/v2/validator_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    runtime_paths = [
        *(REPOSITORY / relative for relative in RUNTIME_ASSETS),
    ]
    runtime_paths.extend(
        REPOSITORY / item["path"] for item in validator_manifest["source_files"]
    )
    runtime_paths.extend(
        sorted((REPOSITORY / "src/llm_generation/knowledge/v2").glob("*.py"))
    )

    body: dict[str, Any] = {
        "schema_version": "atlas.autosar.paper_artifact_freeze.v3",
        "scope": "AUTOSAR Classic 4.2.2 component ARXML",
        "repository": {
            "path": str(REPOSITORY),
            "branch": branch,
            "head": head,
            "dirty_entry_count": len(status.splitlines()) if status else 0,
            "status_sha256": hashlib.sha256(status.encode("utf-8")).hexdigest(),
            "preexisting_dirty_files_preserved": True,
            "commit_or_push_performed": False,
        },
        "execution_boundary": {
            "constraint_corpus_recompiled": False,
            "historical_model_artifacts_modified": False,
            "v17_paid_experiment_started": False,
            "v17_paid_experiment_complete": False,
            "paid_provider_api_calls_in_this_build": 0,
            "v15_role": "immutable_archive_and_regression_provenance_only",
            "v15_result_admitted_to_current_tables": False,
            "paper_result_artifacts_included": False,
            "paper_result_reason": "V17 has not been executed or registered",
            "excluded_domains": ["PIL", "BESSER", "cross_domain"],
        },
        "requirement_set": {
            "case_count": 20,
            "repetitions_per_case": 3,
            "run_count_per_model": 60,
            "source_canonical_sha256": rendered["source_canonical_sha256"],
            "rendered_content_sha256": rendered["content_sha256"],
            "files": file_records(REQUIREMENTS_ROOT, requirement_paths),
        },
        "prospective_internally_authored_heldout": {
            "case_count": 12,
            "run_count": 36,
            "unit_of_analysis": "case",
            "repetitions_per_case": 3,
            "structural_role_case_counts": {
                "REPLICATION": 6,
                "EXTENSION": 6,
            },
            "tier_by_structural_role_case_counts": expected_heldout_cells,
            "factorial_balance": "PASS",
            "pooling_policy": "stratified_primary_pooled_balanced_mixture_descriptive_only",
            "external_benchmark": False,
            "package_schema_version": heldout_manifest["schema_version"],
            "source_sha256": heldout_source_sha256,
            "v15_structure_inventory_sha256": sha256_file(
                heldout_inventory_path
            ),
            "v15_structure_inventory_content_sha256": heldout_inventory[
                "inventory_content_sha256"
            ],
            "review_status": heldout_manifest.get("review_status") or {},
            "admission_reviews": heldout_reviews,
            "files": file_records(
                HELDOUT_ROOT,
                [
                    HELDOUT_ROOT / relative
                    for relative in (*HELDOUT_FILES, *HELDOUT_REVIEW_FILES.values())
                ],
            ),
        },
        "repository_files": file_records(
            REPOSITORY,
            [
                *(REPOSITORY / relative for relative in SCOPED_FILES),
                *(REPOSITORY / relative for relative in REPOSITORY_PAPER_FILES),
            ],
        ),
        "runtime_assets": file_records(REPOSITORY, runtime_paths),
        "runtime_configuration": public_runtime_configuration_fingerprint(),
        "runtime_environment": public_runtime_environment_fingerprint(),
        "experiment_files": file_records(
            ROOT, [ROOT / relative for relative in PROBE_FILES]
        ),
        "unified_frontend": {
            "root": str(FRONTEND_ROOT),
            "role": "frozen_supplemental_workbench_with_fake_autosar_adapter",
            "formal_v16_result_source": False,
            "provider_calls_enabled": False,
            "local_acceptance_gate": acceptance["evidence"]["gates"][
                "unified_frontend_delivery"
            ],
            "files": file_records(
                FRONTEND_ROOT,
                [FRONTEND_ROOT / relative for relative in FRONTEND_FILES],
            ),
        },
        "experiment_contract": {
            "path": contract_path.name,
            "sha256": sha256_file(contract_path),
            "canonical_sha256": canonical_sha256(contract),
            "provider_registration": provider_registration,
            "stream_responses": generation_contract["stream_responses"],
        },
        "replacement_policy": {
            "path": replacement_policy_path.name,
            "sha256": sha256_file(replacement_policy_path),
            "content_sha256": replacement_policy["content_sha256"],
            "schema_version": replacement_policy["schema_version"],
            "provider_no_execution_guarantee_frozen": replacement_policy[
                "provider_no_execution_guarantee_frozen"
            ],
            "currently_operational_eligibility_states": replacement_policy[
                "currently_operational_eligibility_states"
            ],
        },
        "neo4j_context": {
            "path": neo4j_context_path.name,
            "sha256": sha256_file(neo4j_context_path),
            "context_sha256": neo4j_context["context_sha256"],
            "credentials_included": False,
        },
        "local_acceptance": {
            "decision": acceptance["decision"],
            "acceptance_fingerprint_sha256": acceptance[
                "acceptance_fingerprint_sha256"
            ],
            "manifest_content_sha256": acceptance["manifest_content_sha256"],
            "test_count": acceptance["evidence"]["gates"][
                "offline_target_tests"
            ]["test_count"],
            "artifact_profile": acceptance["evidence"]["gates"][
                "atlas_v2_same_context"
            ]["artifact_profile"],
            "full_corpus_summary": acceptance["evidence"]["gates"][
                "atlas_v2_same_context"
            ]["summary"],
        },
        "all_requirements_offline_precheck": {
            "decision": precheck["decision"],
            "content_sha256": precheck["content_sha256"],
            "coverage": coverage,
            "controlled_repair_design_sha256": controlled_design[
                "content_sha256"
            ],
            "controlled_reference_root": reference_baselines["root"],
            "controlled_reference_count": reference_baselines["count"],
            "external_model_api_calls": precheck["execution_boundary"][
                "external_model_api_calls"
            ],
        },
    }
    body["manifest_sha256"] = canonical_sha256(body)
    return body


def main() -> int:
    manifest = build_manifest()
    OUTPUT.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {
                "manifest": str(OUTPUT),
                "manifest_sha256": manifest["manifest_sha256"],
                "repository_file_count": len(manifest["repository_files"]),
                "requirement_file_count": len(manifest["requirement_set"]["files"]),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
