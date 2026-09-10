"""Prove all compiled execution-schema witnesses survive the full offline chain."""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
from typing import Any, Mapping

from execution_schema_v029 import (
    build_witness_matrix,
    canonical_sha256,
    harden_execution_schema,
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"json_root_must_be_object:{path}")
    return value


def load_verified(path: Path, label: str) -> dict[str, Any]:
    value = load_json(path)
    claimed = value.get("content_sha256")
    body = {key: item for key, item in value.items() if key != "content_sha256"}
    if claimed != canonical_sha256(body):
        raise RuntimeError(f"{label}_content_hash_mismatch")
    return value


def atomic_write_json(path: Path, value: Any) -> None:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
        allow_nan=False,
    ).encode("utf-8") + b"\n"
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(encoded)
    os.replace(temporary, path)


def atomic_write_text(path: Path, value: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(value, encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def run_preflight(
    *,
    source_root: Path,
    output_root: Path,
    atlas_root: Path,
    probe_root: Path,
    requirements_root: Path,
) -> dict[str, Any]:
    if output_root.exists() and any(output_root.iterdir()):
        raise FileExistsError(f"output root is not empty: {output_root}")
    output_root.mkdir(parents=True, exist_ok=True)
    source_manifest_path = source_root / "SOURCE_ASSET_MANIFEST.json"
    source_manifest = load_verified(source_manifest_path, "source_manifest")
    if source_manifest.get("decision") != "PASS":
        raise RuntimeError("source_manifest_not_pass")

    xsd_path = atlas_root / "src/validation/data/AUTOSAR_4-2-2.xsd"
    serialization_manifest_path = (
        atlas_root
        / "src/llm_generation/knowledge/v2/xsd_serialization_manifest.json"
    )
    if source_manifest.get("xsd", {}).get("sha256") != sha256_file(xsd_path):
        raise RuntimeError("source_xsd_identity_mismatch")
    if source_manifest.get("serialization_manifest", {}).get(
        "sha256"
    ) != sha256_file(serialization_manifest_path):
        raise RuntimeError("source_serialization_manifest_identity_mismatch")

    os.environ["LLM_API_KEY"] = "offline-local-placeholder"
    sys.path[:0] = [str(atlas_root), str(probe_root), str(requirements_root)]
    from evaluate_asw_v3_run import evaluate
    from src.llm_generation.config import CONFIG
    from src.llm_generation.core.typed_repair import render_document
    from src.llm_generation.core.xsd_serializer import (
        DeterministicXsdSerializer,
        apply_projection_map,
    )
    from src.validation.v2.selection_obligations import (
        merge_selection_obligations,
        validate_selection_obligations,
    )
    from src.validation.v2.service import GeneratedArxmlValidationService

    serializer = DeterministicXsdSerializer.from_files(
        serialization_manifest_path,
        xsd_path=xsd_path,
    )
    validation_service = GeneratedArxmlValidationService.from_config(CONFIG)
    if validation_service is None:
        raise RuntimeError("validation_service_is_disabled")

    reports: list[dict[str, Any]] = []
    for record in source_manifest["records"]:
        case_id = str(record["case_id"])
        schema_path = source_root / str(record["schema_path"])
        requirement_path = source_root / str(record["requirement_path"])
        context_path = source_root / str(record["postprocess_context_path"])
        if sha256_file(schema_path) != record["schema_sha256"]:
            raise RuntimeError(f"source_schema_hash_mismatch:{case_id}")
        if sha256_file(requirement_path) != record["requirement_sha256"]:
            raise RuntimeError(f"source_requirement_hash_mismatch:{case_id}")
        if sha256_file(context_path) != record["postprocess_context_file_sha256"]:
            raise RuntimeError(f"postprocess_context_hash_mismatch:{case_id}")
        context = load_verified(context_path, f"context_{case_id}")
        source_schema = load_json(schema_path)
        requirement = requirement_path.read_text(encoding="utf-8")
        execution_schema, hardening = harden_execution_schema(
            source_schema,
            requirement,
            case_id=case_id,
        )
        witness_matrix = build_witness_matrix(execution_schema)
        witness = witness_matrix["valid_witness"]
        element_type = str(context["component_element_type"])
        if not isinstance(witness, dict) or set(witness) != {element_type}:
            raise RuntimeError(f"witness_root_contract_mismatch:{case_id}")
        payload = witness[element_type]
        if not isinstance(payload, dict):
            raise RuntimeError(f"witness_payload_not_object:{case_id}")

        case_root = output_root / case_id
        case_root.mkdir()
        projected = apply_projection_map(
            deepcopy(payload),
            context.get("projection_map"),
        )
        projected["_type"] = element_type
        component_xml = render_document(
            serializer,
            package=str(context["component_package"]),
            element_type=element_type,
            payload=projected,
        )
        component_path = case_root / f"{context['component']}.arxml"
        atomic_write_text(component_path, component_xml)

        interfaces: dict[str, str] = {}
        interface_paths: list[Path] = []
        for interface in context.get("interfaces") or []:
            source_path = source_root / str(interface["path"])
            if sha256_file(source_path) != interface["sha256"]:
                raise RuntimeError(f"frozen_interface_hash_mismatch:{case_id}")
            target_path = case_root / source_path.name
            shutil.copyfile(source_path, target_path)
            interfaces[str(interface["name"])] = target_path.read_text(
                encoding="utf-8"
            )
            interface_paths.append(target_path)

        bundle = {
            "components": {str(context["component"]): component_xml},
            "interfaces": interfaces,
        }
        validation = validation_service.validate_bundle(
            bundle,
            validation_context=dict(context["validation_context"]),
        )
        obligations = validate_selection_obligations(
            bundle,
            [dict(context["component_plan"])],
        )
        validation = merge_selection_obligations(validation, obligations)
        validation_path = case_root / "validation.json"
        atomic_write_json(validation_path, validation)
        independent = evaluate(
            case_id=case_id,
            component_path=component_path,
            interface_paths=interface_paths,
            validation_path=validation_path,
        )
        independent_path = case_root / "independent_evaluation.json"
        atomic_write_json(independent_path, independent)

        xsd_pass = all(
            item.get("status") == "PASS" for item in independent.get("xsd") or []
        )
        selection_pass = obligations.get("decision") == "PASS"
        artifact_profile_pass = (
            (validation.get("artifact_profile") or {}).get("decision") == "PASS"
        )
        independent_pass = independent.get("decision") == "PASS"
        decision = (
            "PASS"
            if xsd_pass
            and selection_pass
            and artifact_profile_pass
            and independent_pass
            else "FAIL"
        )
        report: dict[str, Any] = {
            "schema_version": "atlas.vllm.uga.materialized_witness_result.v1",
            "case_id": case_id,
            "tier": record["tier"],
            "decision": decision,
            "xsd_decision": "PASS" if xsd_pass else "FAIL",
            "selection_obligation_decision": obligations.get("decision"),
            "artifact_profile_decision": (
                validation.get("artifact_profile") or {}
            ).get("decision"),
            "independent_decision": independent.get("decision"),
            "execution_schema_sha256": hardening["execution_schema_sha256"],
            "valid_witness_sha256": canonical_sha256(witness),
            "source_instance_constraint_count": hardening[
                "source_instance_constraint_count"
            ],
            "compiled_instance_exact_count": hardening[
                "compiled_instance_exact_count"
            ],
            "compiled_instance_const_count": hardening[
                "compiled_instance_const_count"
            ],
            "compiled_instance_numeric_bound_count": hardening[
                "compiled_instance_numeric_bound_count"
            ],
            "exact_value_mutation_count": witness_matrix[
                "exact_value_mutation_count"
            ],
            "required_property_mutation_count": witness_matrix[
                "required_property_mutation_count"
            ],
            "component_file_sha256": sha256_file(component_path),
            "validation_file_sha256": sha256_file(validation_path),
            "independent_evaluation_file_sha256": sha256_file(independent_path),
        }
        report["content_sha256"] = canonical_sha256(report)
        atomic_write_json(case_root / "witness_report.json", report)
        reports.append(report)
        if decision != "PASS":
            raise RuntimeError(f"materialized_witness_failed:{case_id}")

    manifest: dict[str, Any] = {
        "schema_version": "atlas.vllm.uga.materialized_witness_manifest.v1",
        "decision": "PASS",
        "external_model_api_calls": 0,
        "source_manifest_file_sha256": sha256_file(source_manifest_path),
        "source_manifest_content_sha256": source_manifest["content_sha256"],
        "case_count": len(reports),
        "xsd_pass_count": sum(item["xsd_decision"] == "PASS" for item in reports),
        "selection_obligation_pass_count": sum(
            item["selection_obligation_decision"] == "PASS" for item in reports
        ),
        "independent_pass_count": sum(
            item["independent_decision"] == "PASS" for item in reports
        ),
        "source_instance_constraint_count": sum(
            int(item["source_instance_constraint_count"]) for item in reports
        ),
        "compiled_instance_exact_count": sum(
            int(item["compiled_instance_exact_count"]) for item in reports
        ),
        "compiled_instance_const_count": sum(
            int(item["compiled_instance_const_count"]) for item in reports
        ),
        "compiled_instance_numeric_bound_count": sum(
            int(item["compiled_instance_numeric_bound_count"]) for item in reports
        ),
        "exact_value_mutation_count": sum(
            int(item["exact_value_mutation_count"]) for item in reports
        ),
        "required_property_mutation_count": sum(
            int(item["required_property_mutation_count"]) for item in reports
        ),
        "records": reports,
    }
    manifest["content_sha256"] = canonical_sha256(manifest)
    atomic_write_json(output_root / "MATERIALIZED_WITNESS_PREFLIGHT.json", manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--atlas-root", type=Path, required=True)
    parser.add_argument("--probe-root", type=Path, required=True)
    parser.add_argument("--requirements-root", type=Path, required=True)
    args = parser.parse_args()
    manifest = run_preflight(
        source_root=args.source_root.resolve(),
        output_root=args.output_root.resolve(),
        atlas_root=args.atlas_root.resolve(),
        probe_root=args.probe_root.resolve(),
        requirements_root=args.requirements_root.resolve(),
    )
    print(
        json.dumps(
            {
                "decision": manifest["decision"],
                "case_count": manifest["case_count"],
                "xsd_pass_count": manifest["xsd_pass_count"],
                "selection_obligation_pass_count": manifest[
                    "selection_obligation_pass_count"
                ],
                "compiled_instance_exact_count": manifest[
                    "compiled_instance_exact_count"
                ],
                "compiled_instance_const_count": manifest[
                    "compiled_instance_const_count"
                ],
                "content_sha256": manifest["content_sha256"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
