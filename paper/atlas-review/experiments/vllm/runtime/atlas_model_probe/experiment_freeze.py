"""Fail-closed verification for the frozen ASW V3 formal experiment inputs.

This module only hashes public experiment artifacts. It never loads the runtime
environment, provider configuration, or credentials.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parent
REPOSITORY = Path(r"E:\git projects\AI_XmlGenerator")
REQUIREMENTS_ROOT = Path(r"E:\54239\Documents\atlas_autosar_requirements_v3")
HELDOUT_ROOT = Path(r"E:\54239\Documents\atlas_autosar_heldout_v3")
EXPECTED_HELDOUT_SOURCE_SHA256 = (
    "78dc6d65672d896af3c19b50a5efbf5ca18d8237de9f32f2b7234cd6ff226945"
)
FRONTEND_ROOT = Path(r"E:\54239\Documents\ATLAS_FRONTEND_V1")
DEFAULT_FREEZE_MANIFEST = ROOT / "PAPER_ARTIFACT_FREEZE_MANIFEST.json"
GIT_EXECUTABLE = Path(r"D:\Git\cmd\git.exe")


class ExperimentFreezeError(RuntimeError):
    """Raised when a formal experiment input differs from its frozen hash."""


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def public_runtime_configuration_fingerprint() -> dict[str, Any]:
    """Hash only settings used by the formal chain; never retain credentials."""

    config = yaml.safe_load(
        (REPOSITORY / "config/llm_api_config.yaml").read_text(encoding="utf-8")
    )
    llm = config.get("llm") or {}
    public_subset = {
        key: value
        for key, value in config.items()
        if key not in {"llm", "knowledge_graph"}
    }
    public_subset["llm_non_provider_settings"] = {
        key: llm.get(key)
        for key in (
            "temperature",
            "stage_temperatures",
            "max_output_tokens",
            "max_context_tokens",
            "reasoning_effort",
            "strict_json_schema",
            "enable_file_upload",
            "request_timeout_seconds",
            "max_retries",
            "stream_responses",
        )
    }
    public_subset["llm_non_provider_settings"]["transport_route_policy"] = str(
        llm.get(
            "transport_route_policy",
            "direct_no_environment_proxy",
        )
    )
    endpoint = str(llm.get("llm_api_url") or "").rstrip("/")
    knowledge_graph = config.get("knowledge_graph") or {}
    neo4j_endpoint = str(knowledge_graph.get("neo4j_uri") or "")
    neo4j_database = str(knowledge_graph.get("neo4j_database") or "")
    public_subset["knowledge_graph_non_secret_settings"] = {
        key: value
        for key, value in knowledge_graph.items()
        if key not in {
            "neo4j_password",
            "neo4j_uri",
            "neo4j_database",
            "neo4j_user",
        }
    }
    neo4j_user = str(knowledge_graph.get("neo4j_user") or "")
    return {
        "public_configuration_sha256": canonical_sha256(public_subset),
        "provider_endpoint_sha256": hashlib.sha256(
            endpoint.encode("utf-8")
        ).hexdigest(),
        "provider_transport_route_policy": "direct_no_environment_proxy",
        "neo4j_endpoint_sha256": hashlib.sha256(
            neo4j_endpoint.encode("utf-8")
        ).hexdigest(),
        "neo4j_database_sha256": hashlib.sha256(
            neo4j_database.encode("utf-8")
        ).hexdigest(),
        "neo4j_user_sha256": hashlib.sha256(
            neo4j_user.encode("utf-8")
        ).hexdigest(),
        "credential_fields_included": False,
    }


def public_runtime_environment_fingerprint() -> dict[str, Any]:
    """Record the interpreter and audit-relevant package versions."""

    package_names = (
        "jsonschema",
        "lxml",
        "neo4j",
        "openai",
        "psutil",
        "pydantic",
        "PyYAML",
        "xmlschema",
    )
    packages: dict[str, str] = {}
    for package_name in package_names:
        try:
            packages[package_name] = importlib.metadata.version(package_name)
        except importlib.metadata.PackageNotFoundError as error:
            raise ExperimentFreezeError(
                f"required runtime package is missing: {package_name}"
            ) from error
    body = {
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "python_executable_sha256": sha256_file(Path(sys.executable)),
        "platform": platform.platform(),
        "packages": packages,
        "credentials_included": False,
    }
    return {
        **body,
        "environment_sha256": canonical_sha256(body),
    }


def _git_value(*arguments: str) -> str:
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
        raise ExperimentFreezeError((process.stderr or process.stdout).strip())
    return process.stdout.strip()


def _verify_file_map(root: Path, records: dict[str, str], label: str) -> int:
    count = 0
    resolved_root = root.resolve()
    for relative, expected in sorted(records.items()):
        path = (root / relative).resolve()
        try:
            path.relative_to(resolved_root)
        except ValueError as error:
            raise ExperimentFreezeError(
                f"{label} path escapes its root: {relative}"
            ) from error
        if not path.is_file():
            raise ExperimentFreezeError(f"frozen {label} file is missing: {relative}")
        observed = sha256_file(path)
        if observed != expected:
            raise ExperimentFreezeError(
                f"frozen {label} hash mismatch: {relative}"
            )
        count += 1
    return count


def verify_freeze_manifest(
    manifest_path: Path = DEFAULT_FREEZE_MANIFEST,
    *,
    expected_file_sha256: str | None = None,
    expected_manifest_sha256: str | None = None,
) -> dict[str, Any]:
    """Verify manifest identity plus every frozen file before any provider call."""

    manifest_path = manifest_path.resolve()
    if not manifest_path.is_file():
        raise ExperimentFreezeError(f"freeze manifest is missing: {manifest_path}")
    file_sha256 = sha256_file(manifest_path)
    if expected_file_sha256 and file_sha256 != expected_file_sha256:
        raise ExperimentFreezeError("freeze manifest file hash mismatch")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ExperimentFreezeError("freeze manifest is not valid JSON") from error
    if manifest.get("schema_version") != "atlas.autosar.paper_artifact_freeze.v3":
        raise ExperimentFreezeError("unsupported freeze manifest schema version")
    claimed = manifest.get("manifest_sha256")
    unsigned = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    observed_manifest_sha256 = canonical_sha256(unsigned)
    if claimed != observed_manifest_sha256:
        raise ExperimentFreezeError("freeze manifest canonical hash mismatch")
    if expected_manifest_sha256 and claimed != expected_manifest_sha256:
        raise ExperimentFreezeError("freeze manifest identity mismatch")

    repository = manifest.get("repository") or {}
    branch = _git_value("branch", "--show-current")
    head = _git_value("rev-parse", "HEAD")
    status = _git_value("status", "--short")
    if branch != repository.get("branch") or head != repository.get("head"):
        raise ExperimentFreezeError("repository branch or HEAD differs from freeze")
    status_sha256 = hashlib.sha256(status.encode("utf-8")).hexdigest()
    if status_sha256 != repository.get("status_sha256"):
        raise ExperimentFreezeError("repository dirty-state fingerprint differs from freeze")

    frontend = manifest.get("unified_frontend") or {}
    frontend_gate = frontend.get("local_acceptance_gate") or {}
    frontend_files = frontend.get("files")
    if (
        frontend.get("root") != str(FRONTEND_ROOT)
        or frontend.get("formal_v16_result_source") is not False
        or frontend.get("provider_calls_enabled") is not False
        or frontend_gate.get("decision") != "PASS"
        or frontend_gate.get("external_model_api_calls") != 0
        or not isinstance(frontend_files, dict)
        or not frontend_files
    ):
        raise ExperimentFreezeError("unified frontend freeze identity is incomplete")

    heldout = manifest.get("prospective_internally_authored_heldout") or {}
    heldout_files = heldout.get("files")
    heldout_file_map = heldout_files if isinstance(heldout_files, dict) else {}
    admission_reviews = heldout.get("admission_reviews") or {}
    expected_review_files = {
        "claude": "claude_review.json",
        "human_autosar_reviewer": "human_autosar_review.json",
    }
    expected_heldout_cells = {
        f"{tier}:{role}": 2
        for tier in ("minimal", "standard", "full")
        for role in ("REPLICATION", "EXTENSION")
    }
    if (
        heldout.get("external_benchmark") is not False
        or heldout.get("package_schema_version")
        != "atlas.autosar.heldout.review_package.v3"
        or heldout.get("source_sha256") != EXPECTED_HELDOUT_SOURCE_SHA256
        or heldout.get("case_count") != 12
        or heldout.get("run_count") != 36
        or heldout.get("unit_of_analysis") != "case"
        or heldout.get("repetitions_per_case") != 3
        or heldout.get("structural_role_case_counts")
        != {"EXTENSION": 6, "REPLICATION": 6}
        or heldout.get("tier_by_structural_role_case_counts")
        != expected_heldout_cells
        or heldout.get("factorial_balance") != "PASS"
        or heldout.get("pooling_policy")
        != "stratified_primary_pooled_balanced_mixture_descriptive_only"
        or not isinstance(heldout.get("v15_structure_inventory_sha256"), str)
        or len(heldout.get("v15_structure_inventory_sha256")) != 64
        or heldout_file_map.get("v15_structure_inventory.json")
        != heldout.get("v15_structure_inventory_sha256")
        or not isinstance(
            heldout.get("v15_structure_inventory_content_sha256"), str
        )
        or len(heldout.get("v15_structure_inventory_content_sha256")) != 64
        or set(admission_reviews) != {"claude", "human_autosar_reviewer"}
        or any(
            (admission_reviews.get(role) or {}).get("reviewer") != role
            or (admission_reviews.get(role) or {}).get("review_decision") != "PASS"
            or (admission_reviews.get(role) or {}).get("source_sha256")
            != heldout.get("source_sha256")
            or (admission_reviews.get(role) or {}).get("file")
            != expected_review_files[role]
            or heldout_file_map.get(expected_review_files[role])
            != (admission_reviews.get(role) or {}).get("file_sha256")
            for role in expected_review_files
        )
        or not isinstance(heldout_files, dict)
        or not heldout_files
        or heldout_file_map.get("heldout_cases.yaml")
        != heldout.get("source_sha256")
    ):
        raise ExperimentFreezeError("held-out admission freeze identity is incomplete")

    heldout_inventory_path = HELDOUT_ROOT / "v15_structure_inventory.json"
    try:
        heldout_inventory = json.loads(
            heldout_inventory_path.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as error:
        raise ExperimentFreezeError(
            "held-out V15 structure inventory is not valid JSON"
        ) from error
    unsigned_inventory = {
        key: value
        for key, value in heldout_inventory.items()
        if key != "inventory_content_sha256"
    }
    inventory_provenance = heldout_inventory.get("provenance") or {}
    if (
        sha256_file(heldout_inventory_path)
        != heldout.get("v15_structure_inventory_sha256")
        or canonical_sha256(unsigned_inventory)
        != heldout.get("v15_structure_inventory_content_sha256")
        or heldout_inventory.get("inventory_content_sha256")
        != heldout.get("v15_structure_inventory_content_sha256")
        or heldout_inventory.get("scope")
        != "requirement_content_and_structure_no_model_outputs"
        or heldout_inventory.get("schema_version")
        != "atlas.autosar.v15_requirement_inventory.v2"
        or heldout_inventory.get("case_count") != 20
        or ((inventory_provenance.get("requirement_source") or {}).get("sha256"))
        != "3b61eb5926b5646a12f8767524192cd7ed65a39e27a37aa9672277058489e024"
        or ((inventory_provenance.get("formal_archive") or {}).get("manifest_sha256"))
        != "50d58236bbcd27b5b9f95c06f4e07deaec0096a88bf8625e679633e8a29a790c"
    ):
        raise ExperimentFreezeError(
            "held-out V15 structure inventory identity is incomplete"
        )

    counts = {
        "repository_files": _verify_file_map(
            REPOSITORY, manifest.get("repository_files") or {}, "repository"
        ),
        "experiment_files": _verify_file_map(
            ROOT, manifest.get("experiment_files") or {}, "experiment"
        ),
        "requirement_files": _verify_file_map(
            REQUIREMENTS_ROOT,
            (manifest.get("requirement_set") or {}).get("files") or {},
            "requirement",
        ),
        "runtime_assets": _verify_file_map(
            REPOSITORY, manifest.get("runtime_assets") or {}, "runtime asset"
        ),
        "unified_frontend_files": _verify_file_map(
            FRONTEND_ROOT, frontend_files, "unified frontend"
        ),
        "heldout_files": _verify_file_map(
            HELDOUT_ROOT, heldout_files, "held-out"
        ),
    }
    if manifest.get("runtime_configuration") != (
        public_runtime_configuration_fingerprint()
    ):
        raise ExperimentFreezeError("public runtime configuration differs from freeze")
    if manifest.get("runtime_environment") != public_runtime_environment_fingerprint():
        raise ExperimentFreezeError("runtime environment differs from freeze")
    contract = manifest.get("experiment_contract") or {}
    contract_path = ROOT / str(contract.get("path") or "")
    if not contract_path.is_file() or sha256_file(contract_path) != contract.get(
        "sha256"
    ):
        raise ExperimentFreezeError("formal experiment contract hash mismatch")
    contract_payload = json.loads(contract_path.read_text(encoding="utf-8"))
    if canonical_sha256(contract_payload) != contract.get("canonical_sha256"):
        raise ExperimentFreezeError("formal experiment contract canonical hash mismatch")
    neo4j_context = manifest.get("neo4j_context") or {}
    neo4j_context_path = ROOT / str(neo4j_context.get("path") or "")
    if not neo4j_context_path.is_file() or sha256_file(
        neo4j_context_path
    ) != neo4j_context.get("sha256"):
        raise ExperimentFreezeError("formal Neo4j context file hash mismatch")
    neo4j_payload = json.loads(neo4j_context_path.read_text(encoding="utf-8"))
    unsigned_neo4j = {
        key: value for key, value in neo4j_payload.items()
        if key != "context_sha256"
    }
    if (
        canonical_sha256(unsigned_neo4j) != neo4j_payload.get("context_sha256")
        or neo4j_payload.get("context_sha256") != neo4j_context.get("context_sha256")
    ):
        raise ExperimentFreezeError("formal Neo4j context canonical hash mismatch")

    return {
        "decision": "PASS",
        "manifest_path": str(manifest_path),
        "manifest_file_sha256": file_sha256,
        "manifest_sha256": claimed,
        "experiment_contract_sha256": contract["sha256"],
        "neo4j_context_sha256": neo4j_context["context_sha256"],
        "verified_file_counts": counts,
    }
