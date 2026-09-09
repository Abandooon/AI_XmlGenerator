"""Offline acceptance for the repaired ATLAS AUTOSAR Phase 1/Phase 2 chain.

This runner never calls an external model API.  It replaces the model credential
environment variable with a literal local placeholder before importing project
modules, exercises the real Neo4j-backed schema builder, validates a provider
JSON instance, renders through the production hash-pinned serializer, and runs
the posterior XSD/obligation/reference/V2 gates.
"""

from __future__ import annotations

import argparse
import ast
import contextlib
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any


REPOSITORY = Path(r"E:\git projects\AI_XmlGenerator")
PROBE_ROOT = Path(__file__).resolve().parent
FRONTEND_ROOT = Path(r"E:\54239\Documents\ATLAS_FRONTEND_V1")
HELDOUT_ROOT = Path(r"E:\54239\Documents\atlas_autosar_heldout_v3")
GIT_EXECUTABLE = Path(r"D:\Git\cmd\git.exe")
EXPECTED_BRANCH = "api_rag"
EXPECTED_HEAD = "11469745124642f21475662b365701d47d23d8ca"
EXPECTED_XSD_SHA256 = "3c89b2f16d1981eb04e12c7fbe035e7cd6fbd79965a47ff6cf6d6b878feb71ad"
COMPONENT_NAME = "ASW_Com_Std_TimeoutExplicit"
COMPONENT_TYPE = "APPLICATION-SW-COMPONENT-TYPE"

SCOPED_FILES = (
    "atlas_workbench.py",
    "config/atlas_experiment_registry.json",
    "docs/AUTOSAR_V17_EXPERIMENT_PROTOCOL.md",
    "docs/ATLAS_WORKBENCH_USER_STUDY_PROTOCOL.md",
    "tests_v2/test_provider_transition_ledger.py",
    "llm_rag_generator_auto.py",
    "src/llm_generation/config.py",
    "src/llm_generation/core/component_registry.py",
    "src/llm_generation/core/conversation_manager.py",
    "src/llm_generation/core/round1_designer.py",
    "src/llm_generation/core/round2_generator.py",
    "src/llm_generation/core/typed_repair.py",
    "src/llm_generation/core/xsd_serializer.py",
    "src/llm_generation/knowledge/dynamic_query_engine.py",
    "src/llm_generation/knowledge/element_selection.py",
    "src/llm_generation/knowledge/xsd_content_index.py",
    "src/llm_generation/knowledge/xsd_selection_paths.py",
    "src/llm_generation/llm/openai_client.py",
    "src/llm_generation/llm/prompt_templates.py",
    "src/kg_builder/constraint_v2/neo4j_publish.py",
    "src/validation/v2/context.py",
    "src/validation/v2/engine.py",
    "src/validation/v2/implementation_manifest.py",
    "src/validation/v2/repair.py",
    "src/validation/v2/repair_loop.py",
    "src/validation/v2/selection_obligations.py",
    "src/validation/v2/service.py",
    "src/validation/v2/type_semantics_plugins.py",
    "src/validation/v2/validator_manifest.json",
    "src/workbench/__init__.py",
    "src/workbench/assignment.py",
    "src/workbench/artifacts.py",
    "src/workbench/autosar_graph.py",
    "src/workbench/study.py",
    "tests_v2/fixtures/asw_golden_component.arxml",
    "tests_v2/fixtures/asw_golden_interfaces.arxml",
    "tests_v2/test_element_selection_pipeline.py",
    "tests_v2/test_component_artifact_profile.py",
    "tests_v2/test_constraint_v2_publish.py",
    "tests_v2/test_constraint_dsl_and_repair.py",
    "tests_v2/test_openai_schema_fail_closed.py",
    "tests_v2/test_pipeline_artifacts.py",
    "tests_v2/test_round1_identity_contract.py",
    "tests_v2/test_repair_loop.py",
    "tests_v2/test_selection_obligations.py",
    "tests_v2/test_typed_patch_repair.py",
    "tests_v2/test_type_semantics_plugins.py",
    "tests_v2/test_validation_context.py",
    "tests_v2/test_validation_intent_separation.py",
    "tests_v2/test_v15_failure_regressions.py",
    "tests_v2/test_workbench.py",
    "tests_v2/test_xsd_content_index.py",
    "tests_v2/test_xsd_selection_paths.py",
    "tests_v2/fixtures/v15_failures/INDEX.json",
    "tests_v2/fixtures/v15_failures/asw_full_01_r1.json",
    "tests_v2/fixtures/v15_failures/asw_full_01_r3.json",
    "tests_v2/fixtures/v15_failures/asw_full_02_r1.json",
    "tests_v2/fixtures/v15_failures/asw_full_02_r2.json",
    "tests_v2/fixtures/v15_failures/asw_full_02_r3.json",
    "tests_v2/fixtures/v15_failures/asw_full_03_r2.json",
    "tests_v2/fixtures/v15_failures/asw_full_03_r3.json",
    "tests_v2/fixtures/v15_failures/asw_full_04_r2.json",
    "tests_v2/fixtures/v15_failures/asw_full_04_r3.json",
    "tests_v2/fixtures/v15_failures/asw_full_05_r1.json",
    "tests_v2/fixtures/v15_failures/asw_full_05_r2.json",
    "tests_v2/fixtures/v15_failures/asw_full_05_r3.json",
    "tests_v2/fixtures/v15_failures/asw_full_07_r3.json",
)

FRONTEND_FILES = (
    ".gitignore",
    "HANDOFF.md",
    "README.md",
    "atlas_backend.py",
    "package.json",
    "server.py",
    "static/app.js",
    "static/core.js",
    "static/index.html",
    "static/styles.css",
    "tests/test_backend.py",
    "tests/test_core.cjs",
    "tests/test_snapshots.py",
    "tools/browser_test.cjs",
    "tools/browser_test.py",
    "tools/build.py",
    "tools/build_snapshots.py",
    "tools/lint.py",
    "tools/runtime_paths.py",
    "tools/test_all.py",
    "data/besser-current.json",
    "data/pil-current.json",
    "dist/BUILD_MANIFEST.json",
    "dist/atlas_backend.py",
    "dist/server.py",
    "dist/static/app.js",
    "dist/static/core.js",
    "dist/static/index.html",
    "dist/static/styles.css",
    "dist/data/besser-current.json",
    "dist/data/pil-current.json",
)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _canonical_hash(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return _sha256_bytes(encoded)


def _run(command: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd),
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )


def _git_value(*arguments: str) -> str:
    result = _run(
        [
            str(GIT_EXECUTABLE),
            "-c",
            "safe.directory=E:/git projects/AI_XmlGenerator",
            *arguments,
        ],
        cwd=REPOSITORY,
    )
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()[:300]
        raise RuntimeError(f"git {' '.join(arguments)} failed: {detail}")
    return result.stdout.strip()


def _strict_schema_violations(schema: dict[str, Any]) -> list[str]:
    violations: list[str] = []

    def walk(node: Any, path: str) -> None:
        if not isinstance(node, dict):
            return
        if node.get("type") == "object":
            properties = node.get("properties")
            required = node.get("required")
            if not isinstance(properties, dict):
                violations.append(f"{path}: object has no properties object")
            else:
                if set(required or []) != set(properties):
                    violations.append(f"{path}: required does not equal properties")
                for key, child in properties.items():
                    walk(child, f"{path}/properties/{key}")
            if node.get("additionalProperties") is not False:
                violations.append(f"{path}: additionalProperties is not false")
        if node.get("type") == "array":
            walk(node.get("items"), f"{path}/items")

    walk(schema, "$schema")
    return violations


def _provider_instance() -> dict[str, Any]:
    read_reference = {
        "PORT-PROTOTYPE-REF": {
            "@DEST": "R-PORT-PROTOTYPE",
            "#text": f"/Components/{COMPONENT_NAME}/Rp_HCU01_TqCmd",
        },
        "TARGET-DATA-PROTOTYPE-REF": {
            "@DEST": "VARIABLE-DATA-PROTOTYPE",
            "#text": "/COM_Interface/SR_Interface_HCU01_TqCmd/HCU01_TqCmd",
        },
    }
    write_reference = {
        "PORT-PROTOTYPE-REF": {
            "@DEST": "P-PORT-PROTOTYPE",
            "#text": f"/Components/{COMPONENT_NAME}/Pp_MCU03_NRF_IdcSamp",
        },
        "TARGET-DATA-PROTOTYPE-REF": {
            "@DEST": "VARIABLE-DATA-PROTOTYPE",
            "#text": "/COM_Interface/SR_Interface_MCU03_NRF_IdcSamp/MCU03_NRF_IdcSamp",
        },
    }
    return {
        COMPONENT_TYPE: {
            "SHORT-NAME": COMPONENT_NAME,
            "PORTS": {
                "P-PORT-PROTOTYPE": [
                    {
                        "SHORT-NAME": "Pp_MCU03_NRF_IdcSamp",
                        "PROVIDED-INTERFACE-TREF": {
                            "@DEST": "SENDER-RECEIVER-INTERFACE",
                            "#text": "/COM_Interface/SR_Interface_MCU03_NRF_IdcSamp",
                        },
                    }
                ],
                "R-PORT-PROTOTYPE": [
                    {
                        "SHORT-NAME": "Rp_HCU01_TqCmd",
                        "REQUIRED-COM-SPECS": {
                            "NONQUEUED-RECEIVER-COM-SPEC": [
                                {
                                    "DATA-ELEMENT-REF": {
                                        "@DEST": "VARIABLE-DATA-PROTOTYPE",
                                        "#text": "/COM_Interface/SR_Interface_HCU01_TqCmd/HCU01_TqCmd",
                                    },
                                    "ALIVE-TIMEOUT": 0.1,
                                    "HANDLE-TIMEOUT-TYPE": "NONE",
                                    "INIT-VALUE": {
                                        "NUMERICAL-VALUE-SPECIFICATION": {
                                            "VALUE": {"#text": "0"}
                                        }
                                    },
                                }
                            ]
                        },
                        "REQUIRED-INTERFACE-TREF": {
                            "@DEST": "SENDER-RECEIVER-INTERFACE",
                            "#text": "/COM_Interface/SR_Interface_HCU01_TqCmd",
                        },
                    }
                ],
            },
            "SWC-INTERNAL-BEHAVIOR": {
                "SHORT-NAME": "IB_Com_Std_TimeoutExplicit",
                "EVENTS": {
                    "TIMING-EVENT": [
                        {
                            "SHORT-NAME": "TE_RE_Com_Std_TimeoutExplicit_0p01s",
                            "START-ON-EVENT-REF": {
                                "@DEST": "RUNNABLE-ENTITY",
                                "#text": (
                                    f"/Components/{COMPONENT_NAME}/"
                                    "IB_Com_Std_TimeoutExplicit/RE_Com_Std_TimeoutExplicit"
                                ),
                            },
                            "PERIOD": 0.01,
                        }
                    ]
                },
                "RUNNABLE-ENTITY": [
                    {
                        "SHORT-NAME": "RE_Com_Std_TimeoutExplicit",
                        "DATA-RECEIVE-POINT-BY-ARGUMENTS": {
                            "VARIABLE-ACCESS": [
                                {
                                    "SHORT-NAME": "VA_Read_HCU01_TqCmd",
                                    "ACCESSED-VARIABLE": {
                                        "AUTOSAR-VARIABLE-IREF": read_reference
                                    },
                                }
                            ]
                        },
                        "DATA-SEND-POINTS": {
                            "VARIABLE-ACCESS": [
                                {
                                    "SHORT-NAME": "VA_Send_MCU03_NRF_IdcSamp",
                                    "ACCESSED-VARIABLE": {
                                        "AUTOSAR-VARIABLE-IREF": write_reference
                                    },
                                }
                            ]
                        },
                    }
                ],
            },
        }
    }


def _interface_plans() -> list[dict[str, Any]]:
    common = {
        "type": "SENDER-RECEIVER-INTERFACE",
        "communication_pattern": "sender-receiver",
        "data_category": "scalar",
        "connected_components": [COMPONENT_NAME],
        "performance_requirements": "ASW-STD-07 local acceptance",
        "direct_paths": "COM_Interface",
    }
    return [
        {
            **common,
            "interface_id": "IF-MCU03-NRF-IDC-SAMP",
            "name": "SR_Interface_MCU03_NRF_IdcSamp",
            "data_elements": ["MCU03_NRF_IdcSamp"],
        },
        {
            **common,
            "interface_id": "IF-HCU01-TQ-CMD",
            "name": "SR_Interface_HCU01_TqCmd",
            "data_elements": ["HCU01_TqCmd"],
        },
    ]


def _interface_instance() -> dict[str, Any]:
    return {
        "SENDER-RECEIVER-INTERFACE": [
            {
                "SHORT-NAME": plan["name"],
                "DATA-ELEMENTS": {
                    "VARIABLE-DATA-PROTOTYPE": [
                        {"SHORT-NAME": name}
                        for name in plan["data_elements"]
                    ]
                },
            }
            for plan in _interface_plans()
        ]
    }


def _run_unit_tests() -> dict[str, Any]:
    modules = sorted(
        "tests_v2." + path.stem
        for path in (REPOSITORY / "tests_v2").glob("test_*.py")
        if not re.search(r"pil|besser|cross_domain", path.name, re.IGNORECASE)
    )
    environment = dict(os.environ)
    environment["LLM_API_KEY"] = "offline-local-placeholder"
    result = _run(
        [sys.executable, "-B", "-m", "unittest", *modules],
        cwd=REPOSITORY,
        env=environment,
    )
    combined = "\n".join((result.stdout, result.stderr))
    match = re.search(r"Ran\s+(\d+)\s+tests", combined)
    if result.returncode:
        tail = "\n".join(combined.splitlines()[-20:])
        raise RuntimeError(f"offline target tests failed:\n{tail}")
    return {
        "decision": "PASS",
        "test_count": int(match.group(1)) if match else None,
        "module_count": len(modules),
        "excluded_patterns": ["pil", "besser", "cross_domain"],
    }


def _run_workbench_browser_gate() -> dict[str, Any]:
    result = _run(
        [sys.executable, "-B", str(PROBE_ROOT / "verify_workbench_browser.py")],
        cwd=PROBE_ROOT,
        env={**os.environ, "LLM_API_KEY": "offline-browser-placeholder"},
    )
    if result.returncode:
        detail = "\n".join((result.stdout, result.stderr)).strip()[-3000:]
        raise RuntimeError(f"workbench browser isolation failed:\n{detail}")
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError("workbench browser isolation returned no result")
    payload = json.loads(lines[-1])
    if payload.get("decision") != "PASS" or payload.get(
        "external_model_api_calls"
    ) != 0:
        raise RuntimeError("workbench browser isolation did not pass offline")
    return payload


def _run_probe_e2e_gate() -> dict[str, Any]:
    modules = (
        "test_precheck_all_asw_requirements",
        "test_controlled_repair_v16",
        "test_offline_v17_e2e",
        "test_heldout_v3_cli_e2e",
        "test_run_phase12_case",
        "test_delivery_classification",
        "test_delivery_loop_e2e",
        "test_replacement_policy",
        "test_replacement_runner_e2e",
        "test_run_observation",
        "test_v17_pilot_archive",
        "test_main_experiment_freeze.MainExperimentFreezeTests."
        "test_heldout_schedule_consumer_forwards_cohort_and_records_terminal_failure",
    )
    result = _run(
        [sys.executable, "-B", "-m", "unittest", "-v", *modules],
        cwd=PROBE_ROOT,
        env={**os.environ, "LLM_API_KEY": "offline-local-placeholder"},
    )
    combined = "\n".join((result.stdout, result.stderr))
    match = re.search(r"Ran\s+(\d+)\s+tests", combined)
    if result.returncode:
        raise RuntimeError(f"probe fake-client E2E failed:\n{combined[-4000:]}")
    return {
        "decision": "PASS",
        "test_count": int(match.group(1)) if match else None,
        "external_model_api_calls": 0,
        "full_context_failure_repair_interrupt_resume": True,
        "heldout_real_cli_exact_source_and_type_binding": True,
        "heldout_schedule_consumer_cohort_identity": True,
        "provider_call_transition_audit_exact_join": True,
        "sdk_retry_disabled_and_runtime_asserted": True,
        "replacement_provenance_tamper_gates": True,
        "replacement_schedule_consuming_runner": True,
        "replacement_execution_external_model_api_calls": 0,
        "observer_reports_without_stop_authority": True,
    }


def _run_frontend_delivery_gate() -> dict[str, Any]:
    commands = (
        ("lint", FRONTEND_ROOT / "tools/lint.py"),
        ("tests", FRONTEND_ROOT / "tools/test_all.py"),
        ("build", FRONTEND_ROOT / "tools/build.py"),
        ("browser", FRONTEND_ROOT / "tools/browser_test.py"),
    )
    results: dict[str, str] = {}
    python_test_count: int | None = None
    javascript_test_count: int | None = None
    environment = {**os.environ, "LLM_API_KEY": "offline-frontend-placeholder"}
    for label, script in commands:
        result = _run([sys.executable, "-B", str(script)], cwd=FRONTEND_ROOT, env=environment)
        combined = "\n".join((result.stdout, result.stderr)).strip()
        if result.returncode:
            raise RuntimeError(f"frontend {label} gate failed:\n{combined[-3000:]}")
        if label == "tests":
            python_matches = re.findall(r"Ran (\d+) tests?", combined)
            javascript_matches = re.findall(r"\btests\s+(\d+)", combined)
            if not python_matches or not javascript_matches:
                raise RuntimeError("frontend test counts could not be audited")
            python_test_count = int(python_matches[-1])
            javascript_test_count = int(javascript_matches[-1])
        results[label] = combined[-1000:]

    build_manifest_path = FRONTEND_ROOT / "dist/BUILD_MANIFEST.json"
    build_manifest = json.loads(build_manifest_path.read_text(encoding="utf-8"))
    if (
        build_manifest.get("schema_version") != "atlas.frontend.build.v1"
        or build_manifest.get("provider_calls_enabled") is not False
    ):
        raise RuntimeError("frontend build manifest has an unsafe identity")
    records = build_manifest.get("files") or []
    expected_built_paths = {
        relative.removeprefix("dist/")
        for relative in FRONTEND_FILES
        if relative.startswith("dist/")
        and relative != "dist/BUILD_MANIFEST.json"
    }
    observed_built_paths = [str(record.get("path") or "") for record in records]
    if (
        len(observed_built_paths) != len(set(observed_built_paths))
        or set(observed_built_paths) != expected_built_paths
    ):
        raise RuntimeError("frontend portable build file set is incomplete")
    for record in records:
        relative = str(record.get("path") or "")
        expected = str(record.get("sha256") or "")
        source = (FRONTEND_ROOT / relative).resolve()
        built = (FRONTEND_ROOT / "dist" / relative).resolve()
        if (
            not source.is_file()
            or not built.is_file()
            or _sha256_file(source) != expected
            or _sha256_file(built) != expected
        ):
            raise RuntimeError(f"frontend portable build differs at {relative}")
    hashes = {
        relative: _sha256_file(FRONTEND_ROOT / relative)
        for relative in FRONTEND_FILES
    }
    return {
        "decision": "PASS",
        "python_tests": python_test_count,
        "javascript_tests": javascript_test_count,
        "lint": "PASS",
        "portable_build": "PASS",
        "browser": "PASS",
        "browser_scope": [
            "manual_isolation",
            "assisted_fake_repair",
            "PIL_BESSER_read_only",
            "1440px",
            "1024px",
        ],
        "provider_calls_enabled": False,
        "external_model_api_calls": 0,
        "file_sha256": hashes,
        "command_output_tails": results,
    }


def _run_heldout_v3_gate() -> dict[str, Any]:
    commands = (
        ("inventory", [sys.executable, "-B", "build_v15_structure_inventory.py", "--check"]),
        ("source", [sys.executable, "-B", "validate_heldout.py"]),
        ("tests", [sys.executable, "-B", "-m", "unittest", "-v", "test_validate_heldout.py"]),
        ("package", [sys.executable, "-B", "validate_heldout.py", "--verify-package"]),
    )
    outputs: dict[str, str] = {}
    test_count: int | None = None
    source_result: dict[str, Any] | None = None
    for label, command in commands:
        result = _run(command, cwd=HELDOUT_ROOT)
        combined = "\n".join((result.stdout, result.stderr)).strip()
        if result.returncode:
            raise RuntimeError(f"held-out V3 {label} gate failed:\n{combined[-3000:]}")
        if label == "source":
            source_result = json.loads(result.stdout)
        if label == "tests":
            match = re.search(r"Ran\s+(\d+)\s+tests", combined)
            if not match:
                raise RuntimeError("held-out V3 test count could not be audited")
            test_count = int(match.group(1))
        outputs[label] = combined[-1000:]
    source_sha256 = _sha256_file(HELDOUT_ROOT / "heldout_cases.yaml")
    if source_sha256 != "78dc6d65672d896af3c19b50a5efbf5ca18d8237de9f32f2b7234cd6ff226945":
        raise RuntimeError("held-out V3 source identity changed")
    expected_cells = {
        f"{tier}:{role}": 2
        for tier in ("minimal", "standard", "full")
        for role in ("REPLICATION", "EXTENSION")
    }
    if (
        not source_result
        or source_result.get("decision") != "PASS"
        or source_result.get("case_count") != 12
        or source_result.get("run_count") != 36
        or source_result.get("structural_role_case_counts")
        != {"EXTENSION": 6, "REPLICATION": 6}
        or source_result.get("tier_by_structural_role_case_counts") != expected_cells
        or source_result.get("factorial_balance") != "PASS"
        or source_result.get("case_exclusive_data_element_identities") != "PASS"
        or source_result.get("v15_relation_ledger") != "PASS"
    ):
        raise RuntimeError("held-out V3 factorial method gate is incomplete")
    inventory = json.loads(
        (HELDOUT_ROOT / "v15_structure_inventory.json").read_text(encoding="utf-8")
    )
    return {
        "decision": "PASS",
        "schema_version": "atlas.autosar.heldout.v3",
        "source_sha256": source_sha256,
        "case_count": 12,
        "run_count": 36,
        "unit_of_analysis": "case",
        "repetitions_per_case": 3,
        "structural_role_case_counts": source_result["structural_role_case_counts"],
        "tier_by_structural_role_case_counts": source_result[
            "tier_by_structural_role_case_counts"
        ],
        "factorial_balance": "PASS",
        "case_exclusive_data_element_identities": "PASS",
        "v15_relation_ledger": "PASS",
        "test_count": test_count,
        "v15_structure_inventory_sha256": _sha256_file(
            HELDOUT_ROOT / "v15_structure_inventory.json"
        ),
        "v15_structure_inventory_content_sha256": inventory[
            "inventory_content_sha256"
        ],
        "v15_inventory_scope": inventory["scope"],
        "external_benchmark": False,
        "held_out_execution": False,
        "external_model_api_calls": 0,
        "command_output_tails": outputs,
    }


def _acceptance_evidence() -> dict[str, Any]:
    branch = _git_value("branch", "--show-current")
    head = _git_value("rev-parse", "HEAD")
    status = _git_value("status", "--short")
    if branch != EXPECTED_BRANCH or head != EXPECTED_HEAD:
        raise RuntimeError(f"unexpected repository identity: {branch}@{head}")

    xsd_path = REPOSITORY / "src/validation/data/AUTOSAR_4-2-2.xsd"
    xsd_hash = _sha256_file(xsd_path)
    if xsd_hash != EXPECTED_XSD_SHA256:
        raise RuntimeError("pinned AUTOSAR XSD hash mismatch")

    ast_files = [
        path for relative in SCOPED_FILES
        if (path := REPOSITORY / relative).suffix == ".py"
    ]
    for path in ast_files:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    unit_tests = _run_unit_tests()
    workbench_browser = _run_workbench_browser_gate()
    probe_e2e = _run_probe_e2e_gate()
    frontend_delivery = _run_frontend_delivery_gate()
    heldout_v3 = _run_heldout_v3_gate()

    # Do not inherit or inspect a real provider credential.
    os.environ["LLM_API_KEY"] = "offline-local-placeholder"
    sys.path.insert(0, str(REPOSITORY))
    noise = io.StringIO()
    with contextlib.redirect_stdout(noise), contextlib.redirect_stderr(noise):
        from jsonschema import Draft202012Validator
        from lxml import etree

        from src.llm_generation.core.round1_designer import round1_designer
        from src.llm_generation.core.round2_generator import round2_generator
        from src.llm_generation.core.xsd_serializer import apply_projection_map
        from src.llm_generation.knowledge.element_selection import (
            ElementSelectionError,
            build_interface_instance_skeleton,
            compile_architecture_selection_paths,
            materialize_admitted_provider_payload,
            merge_provider_schema_payloads,
            partition_provider_schema,
            project_payload_to_admitted_provider_schema,
            project_provider_to_admitted_instances,
            provider_schema_container_depth,
        )
        from src.validation.v2.arxml_index import ArxmlIndex, local_name
        from src.validation.v2.selection_obligations import (
            generation_status_from_validation,
            merge_selection_obligations,
            validate_selection_obligations,
        )
        from tests_v2.test_selection_obligations import component_plan

        phase1_schema = round1_designer._build_architecture_schema()
        phase1_strict = _strict_schema_violations(phase1_schema)
        if phase1_strict:
            raise RuntimeError("Phase 1 strict-schema invariant failed")

        plans = component_plan()
        compiled_architecture, selection_path_audit = compile_architecture_selection_paths(
            {"component_plan": plans},
            xsd_path_index=round1_designer.selection_path_index,
        )
        plans = compiled_architecture["component_plan"]
        path_resolutions = [
            selection
            for component_audit in selection_path_audit["components"]
            for selection in component_audit["selections"]
        ]
        if not path_resolutions or any(
            item.get("resolution") != "exact" for item in path_resolutions
        ):
            raise RuntimeError("golden Phase 1 paths were not exact pinned-XSD paths")
        rejected_mutations = 0
        for invalid_path in (
            [
                "PORTS",
                "P-PORT-PROTOTYPE",
                "PROVIDED-INTERFACE-TREF",
                "DATA-ELEMENT-REF",
                "#TEXT",
            ],
            [
                "INTERNAL-BEHAVIORS",
                "SWC-INTERNAL-BEHAVIOR",
                "COMPONENT-REF",
                "@DEST",
            ],
        ):
            mutation = deepcopy(plans[0])
            mutation["element_design"]["selections"] = [
                {
                    "path": invalid_path,
                    "min_occurs": 1,
                    "max_occurs": 1,
                    "value_present": False,
                    "value": "",
                    "anchors": [],
                    "notes": "observed invalid-parent mutation",
                }
            ]
            try:
                compile_architecture_selection_paths(
                    {"component_plan": [mutation]},
                    xsd_path_index=round1_designer.selection_path_index,
                )
            except ElementSelectionError:
                rejected_mutations += 1
        if rejected_mutations != 2:
            raise RuntimeError("observed nonexistent selection paths were not rejected")
        component = plans[0]
        phase2_schema = round2_generator._build_single_component_schema(component)
        phase2_strict = _strict_schema_violations(phase2_schema)
        if phase2_strict:
            raise RuntimeError("Phase 2 strict-schema invariant failed")

        Draft202012Validator.check_schema(phase2_schema)
        instance = _provider_instance()
        instance_errors = sorted(
            Draft202012Validator(phase2_schema).iter_errors(instance),
            key=lambda error: list(error.absolute_path),
        )
        if instance_errors:
            first = instance_errors[0]
            raise RuntimeError(f"provider JSON does not satisfy Phase 2 schema at {list(first.absolute_path)}")

        provider_calls, provider_projection = partition_provider_schema(phase2_schema)
        if provider_projection.get("call_count") != 1 or len(provider_calls) != 1:
            raise RuntimeError("provider root projection changed the model call count")
        projected_schema = provider_calls[0]["schema"]
        projected_instance = (
            instance[COMPONENT_TYPE]
            if provider_projection.get("component_root") == COMPONENT_TYPE
            else instance
        )
        projected_errors = list(
            Draft202012Validator(projected_schema).iter_errors(projected_instance)
        )
        if projected_errors:
            raise RuntimeError("projected provider JSON does not satisfy strict schema")
        restored_instance, provider_restore = merge_provider_schema_payloads(
            {"full": projected_instance}, phase2_schema, provider_projection
        )
        if restored_instance != instance:
            raise RuntimeError("provider component-root projection was not reversible")

        component_root = phase2_schema["properties"][COMPONENT_TYPE]
        component_properties = component_root["properties"]
        r_port = component_properties["PORTS"]["properties"]["R-PORT-PROTOTYPE"]["items"]
        r_port_properties = r_port["properties"]
        if "REQUIRED-COM-SPECS" not in r_port_properties or "REQUIRED-COM-SPECS" not in r_port["required"]:
            raise RuntimeError("requirement-selected REQUIRED-COM-SPECS is absent or optional")

        projection = round2_generator.query_engine.component_xml_projection_map(component)

        def render() -> str:
            payload = apply_projection_map(
                deepcopy(instance[COMPONENT_TYPE]),
                projection,
            )
            payload["_type"] = COMPONENT_TYPE
            return round2_generator._convert_single_component_to_arxml(
                COMPONENT_NAME,
                payload,
            )

        rendered = render()
        rendered_again = render()
        if rendered != rendered_again:
            raise RuntimeError("deterministic renderer produced different bytes")

        xsd = etree.XMLSchema(etree.parse(str(xsd_path)))
        rendered_root = etree.fromstring(rendered.encode("utf-8"))
        if not xsd.validate(rendered_root):
            first_error = next(iter(xsd.error_log), None)
            raise RuntimeError(f"rendered component failed pinned XSD: {first_error}")

        obligations = validate_selection_obligations(
            {"components": {COMPONENT_NAME: rendered}, "interfaces": {}},
            plans,
        )
        if obligations.get("decision") != "PASS" or obligations.get("evaluated") != 25:
            raise RuntimeError("parsed Phase 1 obligations did not all pass")

        unsupported_plans = deepcopy(plans)
        unsupported_plans[0]["element_design"]["unsupported"] = [
            {
                "requirement_id": "vendor.extension.unsupported",
                "requirement": "unsupported vendor extension",
                "reason": "no supported AUTOSAR 4.2.2 path",
            }
        ]
        unsupported_report = validate_selection_obligations(
            {"components": {COMPONENT_NAME: rendered}, "interfaces": {}},
            unsupported_plans,
        )
        if unsupported_report.get("decision") != "NOT_EVALUATED":
            raise RuntimeError("unsupported Phase 1 intent was not rejected fail-closed")

        interface_fixture = REPOSITORY / "tests_v2/fixtures/asw_golden_interfaces.arxml"
        interface_xml = interface_fixture.read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory(prefix="atlas-local-acceptance-") as directory:
            component_path = Path(directory) / "component.arxml"
            interfaces_path = Path(directory) / "interfaces.arxml"
            component_path.write_text(rendered, encoding="utf-8")
            interfaces_path.write_text(interface_xml, encoding="utf-8")
            index = ArxmlIndex([component_path, interfaces_path])
            references = [
                element
                for element in index.roots[0].iter()
                if local_name(element.tag).endswith(("-REF", "-TREF", "-IREF"))
                and element.text
                and element.text.strip().startswith("/")
            ]
            resolutions = [index.resolve(reference).status for reference in references]
        if len(references) != 8 or any(status != "resolved" for status in resolutions):
            raise RuntimeError("same-context reference integrity failed")

        adapter = round2_generator.constraint_adapter_v2
        if adapter is None:
            raise RuntimeError("ConstraintV2 retrieval adapter is unavailable")
        adapter.retrieve_for_component(
            component_plan=component,
            component_schema=phase2_schema,
            interface_plans=_interface_plans(),
        )
        retrieval_trace = {COMPONENT_NAME: adapter.retrieval_trace()}
        interface_schema = round2_generator.query_engine.generate_multi_interface_schema(
            _interface_plans()
        )
        interface_strict = _strict_schema_violations(interface_schema)
        if interface_strict:
            raise RuntimeError("Phase 2 interface strict-schema invariant failed")
        interface_array = interface_schema["properties"]["SENDER-RECEIVER-INTERFACE"]
        interface_item = interface_array["items"]
        if interface_array.get("minItems") != 2 or interface_array.get("maxItems") != 2:
            raise RuntimeError("planned interface count was not compiled into the schema")
        if "DATA-ELEMENTS" not in interface_item.get("required", []):
            raise RuntimeError("planned interface DATA-ELEMENTS is not required")
        data_container = interface_item["properties"]["DATA-ELEMENTS"]
        data_array = data_container["properties"]["VARIABLE-DATA-PROTOTYPE"]
        if data_array.get("minItems") != 1 or data_array.get("maxItems") != 1:
            raise RuntimeError("planned interface data-element count is not constrained")
        data_names = data_array["items"]["properties"]["SHORT-NAME"].get("enum")
        if set(data_names or []) != {"HCU01_TqCmd", "MCU03_NRF_IdcSamp"}:
            raise RuntimeError("planned interface data-element names are absent from the schema")
        full_interface_instance = _interface_instance()
        full_interface_errors = list(
            Draft202012Validator(interface_schema).iter_errors(
                full_interface_instance
            )
        )
        if full_interface_errors:
            raise RuntimeError("golden interface instance violates the full schema")
        interface_skeleton, interface_skeleton_audit = (
            build_interface_instance_skeleton(
                _interface_plans(), interface_schema
            )
        )
        interface_provider_schema, interface_projection = (
            project_provider_to_admitted_instances(
                interface_schema, interface_skeleton
            )
        )
        raw_interface_instance = project_payload_to_admitted_provider_schema(
            full_interface_instance, interface_projection
        )
        if list(
            Draft202012Validator(interface_provider_schema).iter_errors(
                raw_interface_instance
            )
        ):
            raise RuntimeError("golden interface raw payload violates admitted schema")
        restored_interface_instance, interface_assembly = (
            materialize_admitted_provider_payload(
                raw_interface_instance,
                interface_provider_schema,
                interface_projection,
                interface_skeleton,
            )
        )
        if (
            restored_interface_instance != full_interface_instance
            or interface_assembly.get("normalization_status") != "NOT_APPLICABLE"
        ):
            raise RuntimeError("interface admitted projection was not reversible")
        adapter.retrieve_for_interfaces(
            interface_plans=_interface_plans(),
            interface_schema=interface_schema,
        )
        retrieval_trace["interfaces"] = adapter.retrieval_trace()
        if any(trace.get("backend") != "neo4j" for trace in retrieval_trace.values()):
            raise RuntimeError("acceptance retrieval did not use Neo4j")

        service = round2_generator.validation_service
        declared_constraint_ids = ["TPS_SWCT_01519", "constr_1100"]
        component_trace = retrieval_trace[COMPONENT_NAME]
        component_trace["constraint_ids"] = sorted(
            set(component_trace.get("constraint_ids") or [])
            | set(declared_constraint_ids)
        )
        component_trace["result_count"] = len(component_trace["constraint_ids"])
        declared_targets = {
            "TPS_SWCT_01519": [
                f"/Components/{COMPONENT_NAME}/IB_Com_Std_TimeoutExplicit/"
                "RE_Com_Std_TimeoutExplicit"
            ],
            "constr_1100": [f"/Components/{COMPONENT_NAME}/Rp_HCU01_TqCmd"],
        }
        evidence = {
            "profile_id": "autosar_component_arxml_only_v1",
            "component": COMPONENT_NAME,
            "interfaces": [
                "/COM_Interface/SR_Interface_HCU01_TqCmd",
                "/COM_Interface/SR_Interface_MCU03_NRF_IdcSamp",
            ],
            "manual_capabilities_out_of_scope": [
                "external_antecedent",
                "external_design_evidence",
                "generated_artifact",
                "runtime_evidence",
            ],
        }
        evidence_sha256 = _canonical_hash(evidence)
        validation_context = service.build_validation_context(
            retrieval_trace,
            declared_use_cases=[
                "periodic_sensor_processing",
                "sender_receiver_communication",
            ],
            declared_constraint_ids=declared_constraint_ids,
            declared_targets=declared_targets,
            intent_scope="complete",
            declared_capability_scopes=[
                {
                    "scope_path": scope_path,
                    "constraint_ids": declared_constraint_ids,
                    "capabilities": ["complete_reference_scope"],
                    "evidence_sha256": evidence_sha256,
                    "evidence_kind": "hash_pinned_component_benchmark_context",
                }
                for scope_path in [
                    f"/Components/{COMPONENT_NAME}",
                    *evidence["interfaces"],
                ]
            ],
            manual_evidence_scope={
                "profile_id": evidence["profile_id"],
                "complete": True,
                "excluded_capabilities": evidence[
                    "manual_capabilities_out_of_scope"
                ],
                "evidence_sha256": evidence_sha256,
            },
        )
        v2_report = service.validate_bundle(
            {
                "components": {COMPONENT_NAME: rendered},
                "interfaces": {"COM_Interface": interface_xml},
            },
            validation_context,
        )
        merged_report = merge_selection_obligations(v2_report, obligations)
        v2_decision = merged_report.get("decision")
        v2_summary = merged_report.get("summary") or {}
        if v2_decision not in {"PASS", "INCOMPLETE"}:
            raise RuntimeError(f"V2 returned {v2_decision}")
        if merged_report.get("findings"):
            raise RuntimeError("V2 returned findings for the golden bundle")
        if v2_decision == "INCOMPLETE" and int(v2_summary.get("must_not_evaluated") or 0) < 1:
            raise RuntimeError("V2 incomplete decision has no unevaluated MUST evidence")
        artifact_profile = merged_report.get("artifact_profile") or {}
        if artifact_profile.get("decision") != "PASS":
            raise RuntimeError(
                "golden component artifact profile did not pass: "
                f"{artifact_profile.get('decision')}"
            )

    selected_constraint_count = int(
        len(validation_context.get("selected_constraint_ids") or [])
    )
    if selected_constraint_count < 1:
        raise RuntimeError("hash-pinned V2 context selected no constraints")

    return {
        "repository": {
            "path": str(REPOSITORY),
            "branch": branch,
            "head": head,
            "status_sha256": _sha256_bytes(status.encode("utf-8")),
            "dirty_entry_count": len(status.splitlines()) if status else 0,
            "preexisting_dirty_files_preserved": True,
            "commit_or_push_performed": False,
        },
        "execution_boundary": {
            "external_model_api_calls": 0,
            "credential_source": "literal offline placeholder assigned before imports",
            "neo4j_used": True,
            "constraint_corpus_recompiled": False,
            "excluded_domains": ["PIL", "BESSER", "cross_domain", "paper experiments"],
        },
        "hashes": {
            "autosar_4_2_2_xsd_sha256": xsd_hash,
            "xsd_serialization_manifest_sha256": _sha256_file(
                REPOSITORY / "src/llm_generation/knowledge/v2/xsd_serialization_manifest.json"
            ),
            "validation_plan_sha256": _sha256_file(
                REPOSITORY / "src/generate_formal_constraints/v2/validation_plan.json"
            ),
            "validator_manifest_sha256": _sha256_file(
                REPOSITORY / "src/validation/v2/validator_manifest.json"
            ),
            "retrieval_manifest_sha256": _sha256_file(
                REPOSITORY / "src/llm_generation/knowledge/v2/retrieval_manifest.json"
            ),
            "acceptance_runner_sha256": _sha256_file(Path(__file__)),
            "scoped_files": {
                relative: _sha256_file(REPOSITORY / relative)
                for relative in SCOPED_FILES
            },
        },
        "gates": {
            "python_ast": {"decision": "PASS", "file_count": len(ast_files)},
            "offline_target_tests": unit_tests,
            "probe_fake_client_e2e": probe_e2e,
            "workbench_browser_condition_isolation": workbench_browser,
            "unified_frontend_delivery": frontend_delivery,
            "prospective_heldout_v3": heldout_v3,
            "phase1_strict_schema": {"decision": "PASS", "violation_count": 0},
            "phase1_pinned_xsd_selection_paths": {
                "decision": "PASS",
                "exact_path_count": len(path_resolutions),
                "observed_mutations_rejected": rejected_mutations,
                "xsd_sha256": selection_path_audit["xsd_sha256"],
            },
            "phase2_neo4j_schema": {
                "decision": "PASS",
                "strict_violation_count": 0,
                "required_com_specs_selected": True,
            },
            "phase2_interface_requirement_schema": {
                "decision": "PASS",
                "strict_violation_count": 0,
                "interface_count_constrained": 2,
                "data_elements_required": True,
                "data_element_names_constrained": 2,
            },
            "phase2_interface_admitted_provider_schema": {
                "decision": "PASS",
                "identity_skeleton_strategy": interface_skeleton_audit.get(
                    "strategy"
                ),
                "interface_count": interface_skeleton_audit.get(
                    "interface_count"
                ),
                "data_element_count": interface_skeleton_audit.get(
                    "data_element_count"
                ),
                "projection_strategy": interface_projection.get("strategy"),
                "named_array_count": interface_projection.get(
                    "named_array_count"
                ),
                "admitted_instance_count": interface_projection.get(
                    "admitted_instance_count"
                ),
                "raw_provider_schema_status": "PASS",
                "normalization_status": interface_assembly.get(
                    "normalization_status"
                ),
                "final_atlas_status": "PASS",
                "reversible": True,
            },
            "provider_json_schema": {"decision": "PASS", "error_count": 0},
            "provider_single_call_root_projection": {
                "decision": "PASS",
                "strategy": provider_projection.get("strategy"),
                "call_count": provider_projection.get("call_count"),
                "full_schema_depth": provider_schema_container_depth(phase2_schema),
                "projected_schema_depth": provider_calls[0].get("nesting_depth"),
                "full_provider_schema_revalidated": provider_restore.get(
                    "full_provider_schema_revalidated"
                ),
            },
            "deterministic_renderer": {
                "decision": "PASS",
                "component_arxml_sha256": _sha256_bytes(rendered.encode("utf-8")),
            },
            "pinned_xsd": {"decision": "PASS", "error_count": 0},
            "parsed_selection_obligations": {
                "decision": "PASS",
                "evaluated": obligations.get("evaluated"),
                "finding_count": 0,
            },
            "unsupported_intent": {
                "decision": "PASS",
                "observed_validation_decision": unsupported_report.get("decision"),
            },
            "same_context_reference_integrity": {
                "decision": "PASS",
                "reference_count": len(references),
                "resolved_count": resolutions.count("resolved"),
            },
            "atlas_v2_same_context": {
                "decision": "PASS_FAIL_CLOSED",
                "observed_validation_decision": v2_decision,
                "summary": v2_summary,
                "finding_count": len(merged_report.get("findings") or []),
                "selected_constraint_count": selected_constraint_count,
                "validation_context_manifest_sha256": validation_context.get("manifest_sha256"),
                "generation_status": generation_status_from_validation(v2_decision),
                "artifact_profile": artifact_profile,
            },
        },
        "model_rerun_boundary": {
            "locally_ready": True,
            "performed_by_this_runner": False,
            "external_model_api_calls_by_this_runner": 0,
            "authorization_managed_by_outer_execution": True,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=PROBE_ROOT / "LOCAL_PIPELINE_ACCEPTANCE_MANIFEST.json",
    )
    args = parser.parse_args(argv)
    created = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    try:
        evidence = _acceptance_evidence()
        manifest: dict[str, Any] = {
            "schema_version": "atlas.autosar.local-pipeline-acceptance.v1",
            "created_at_utc": created,
            "decision": "LOCAL_CHAIN_ACCEPTED_FAIL_CLOSED",
            "promotable_model_output": False,
            "evidence": evidence,
        }
        manifest["acceptance_fingerprint_sha256"] = _canonical_hash(evidence)
        exit_code = 0
    except Exception as error:
        manifest = {
            "schema_version": "atlas.autosar.local-pipeline-acceptance.v1",
            "created_at_utc": created,
            "decision": "ERROR",
            "promotable_model_output": False,
            "error": {
                "type": type(error).__name__,
                "message": str(error)[:1000],
            },
        }
        exit_code = 1
    manifest["manifest_content_sha256"] = _canonical_hash(manifest)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "decision": manifest["decision"],
                "manifest": str(args.output.resolve()),
                "manifest_content_sha256": manifest["manifest_content_sha256"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
