"""Materialize and independently validate frozen U/G/A JSON results offline."""

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

ATLAS_ROOT = Path(r"E:\git projects\AI_XmlGenerator")
PROBE_ROOT = Path(r"E:\54239\Documents\atlas_model_probe")
REQUIREMENTS_ROOT = Path(r"E:\54239\Documents\atlas_autosar_requirements_v3")
XSD_PATH = ATLAS_ROOT / "src/validation/data/AUTOSAR_4-2-2.xsd"
SERIALIZATION_MANIFEST_PATH = (
    ATLAS_ROOT
    / "src/llm_generation/knowledge/v2/xsd_serialization_manifest.json"
)


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"json_root_must_be_object:{path.name}")
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


def verify_source_files(source_manifest: Mapping[str, Any]) -> None:
    for record in source_manifest.get("source_files") or []:
        path = Path(str(record.get("path") or ""))
        if not path.is_file():
            raise FileNotFoundError(f"source_identity_file_missing:{path}")
        if sha256_file(path) != record.get("sha256"):
            raise RuntimeError(f"source_identity_hash_mismatch:{path}")
    for tree in source_manifest.get("source_trees") or []:
        root = Path(str(tree.get("root") or ""))
        records = tree.get("records") or []
        if tree.get("file_count") != len(records):
            raise RuntimeError(f"source_tree_record_count_mismatch:{root}")
        suffixes = set(tree.get("suffixes") or [])
        excluded_prefixes = tuple(
            str(prefix).strip("/") + "/"
            for prefix in (tree.get("excluded_prefixes") or [])
        )
        candidates = root.rglob("*") if tree.get("recursive") else root.glob("*")
        current_paths = sorted(
            path.relative_to(root).as_posix()
            for path in candidates
            if path.is_file()
            and path.suffix.lower() in suffixes
            and "__pycache__" not in path.parts
            and not path.relative_to(root).as_posix().startswith(
                excluded_prefixes
            )
        )
        expected_paths = sorted(str(record["path"]) for record in records)
        if current_paths != expected_paths:
            raise RuntimeError(f"source_tree_file_set_mismatch:{root}")
        observed = []
        for record in records:
            path = root / str(record["path"])
            if not path.is_file():
                raise FileNotFoundError(f"source_tree_file_missing:{path}")
            current = {
                "path": record["path"],
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            if current != record:
                raise RuntimeError(f"source_tree_file_identity_mismatch:{path}")
            observed.append(current)
        if canonical_sha256(observed) != tree.get("tree_content_sha256"):
            raise RuntimeError(f"source_tree_content_hash_mismatch:{root}")


def verify_input_chain(
    *,
    contract_path: Path,
    schedule_path: Path,
    compiled_manifest_path: Path,
    source_root: Path,
    run_root: Path,
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
]:
    contract = load_verified(contract_path, "contract")
    schedule = load_verified(schedule_path, "schedule")
    compiled = load_verified(compiled_manifest_path, "compiled_assets")
    source_manifest_path = source_root / "SOURCE_ASSET_MANIFEST.json"
    source = load_verified(source_manifest_path, "source_assets")
    run_manifest = load_verified(run_root / "RUN_MANIFEST.json", "run_manifest")
    identities = {
        "schedule_file_sha256": sha256_file(schedule_path),
        "schedule_content_sha256": schedule["content_sha256"],
        "assets_manifest_file_sha256": sha256_file(compiled_manifest_path),
        "assets_manifest_content_sha256": compiled["content_sha256"],
    }
    for field_name, actual in identities.items():
        if contract.get(field_name) != actual:
            raise RuntimeError(f"contract_identity_mismatch:{field_name}")
    if compiled.get("source_manifest_file_sha256") != sha256_file(
        source_manifest_path
    ):
        raise RuntimeError("compiled_source_manifest_file_hash_mismatch")
    if compiled.get("source_manifest_content_sha256") != source.get(
        "content_sha256"
    ):
        raise RuntimeError("compiled_source_manifest_content_hash_mismatch")
    if run_manifest.get("contract_content_sha256") != contract.get(
        "content_sha256"
    ):
        raise RuntimeError("run_contract_content_hash_mismatch")
    if run_manifest.get("schedule_content_sha256") != schedule.get(
        "content_sha256"
    ):
        raise RuntimeError("run_schedule_content_hash_mismatch")
    if run_manifest.get("assets_manifest_content_sha256") != compiled.get(
        "content_sha256"
    ):
        raise RuntimeError("run_assets_content_hash_mismatch")
    if run_manifest.get("decision") != "COMPLETE":
        raise RuntimeError("run_manifest_is_not_complete")
    if run_manifest.get("completed_request_count") != schedule.get(
        "request_count"
    ):
        raise RuntimeError("run_request_count_mismatch")
    expected_result_hashes = {
        item["path"]: item["sha256"]
        for item in run_manifest.get("result_files") or []
    }
    if len(expected_result_hashes) != schedule.get("request_count"):
        raise RuntimeError("run_result_identity_count_mismatch")
    for relative, expected in expected_result_hashes.items():
        path = run_root / relative
        if not path.is_file() or sha256_file(path) != expected:
            raise RuntimeError(f"run_result_file_hash_mismatch:{relative}")
    verify_source_files(source)
    if source.get("xsd", {}).get("sha256") != sha256_file(XSD_PATH):
        raise RuntimeError("postprocess_xsd_hash_mismatch")
    if source.get("serialization_manifest", {}).get(
        "sha256"
    ) != sha256_file(SERIALIZATION_MANIFEST_PATH):
        raise RuntimeError("postprocess_serialization_manifest_hash_mismatch")
    return contract, schedule, compiled, source, run_manifest


def materialize_one(
    *,
    result: Mapping[str, Any],
    context: Mapping[str, Any],
    source_root: Path,
    output_root: Path,
    serializer: Any,
    validation_service: Any,
    evaluate: Any,
    apply_projection_map: Any,
    render_document: Any,
    merge_selection_obligations: Any,
    validate_selection_obligations: Any,
) -> dict[str, Any]:
    schedule_record = result["schedule"]
    report: dict[str, Any] = {
        "schema_version": "atlas.vllm.uga.postprocess_result.v1",
        "schedule_ordinal": schedule_record["schedule_ordinal"],
        "request_id": schedule_record["request_id"],
        "case_id": schedule_record["case_id"],
        "arm": schedule_record["arm"],
        "source_result_content_sha256": result["content_sha256"],
        "materialization_decision": "NOT_EVALUATED",
        "xsd_decision": "NOT_EVALUATED",
        "selection_obligation_decision": "NOT_EVALUATED",
        "artifact_profile_decision": "NOT_EVALUATED",
        "independent_decision": "NOT_EVALUATED",
        "end_to_end_structural_decision": "FAIL",
    }
    if result.get("parse_decision") != "PASS":
        report["terminal_reason"] = "JSON_PARSE_FAIL"
        return report
    if result.get("schema_decision") != "PASS":
        report["terminal_reason"] = "JSON_SCHEMA_FAIL"
        return report

    request_root = output_root / f"{int(schedule_record['schedule_ordinal']):03d}"
    request_root.mkdir()
    try:
        value = json.loads(str(result["output"]))
        element_type = str(context["component_element_type"])
        if not isinstance(value, dict) or set(value) != {element_type}:
            raise ValueError("final_ir_requires_one_registered_component_root")
        payload = value[element_type]
        if not isinstance(payload, dict):
            raise ValueError("final_ir_component_payload_must_be_object")
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
        component_path = request_root / f"{context['component']}.arxml"
        atomic_write_text(component_path, component_xml)
        interface_paths: list[Path] = []
        interfaces: dict[str, str] = {}
        for interface in context.get("interfaces") or []:
            source_path = source_root / str(interface["path"])
            if sha256_file(source_path) != interface["sha256"]:
                raise RuntimeError("frozen_interface_hash_mismatch")
            target_path = request_root / source_path.name
            shutil.copyfile(source_path, target_path)
            interface_paths.append(target_path)
            interfaces[str(interface["name"])] = target_path.read_text(
                encoding="utf-8"
            )
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
        validation_path = request_root / "validation.json"
        atomic_write_json(validation_path, validation)
        independent = evaluate(
            case_id=str(schedule_record["case_id"]),
            component_path=component_path,
            interface_paths=interface_paths,
            validation_path=validation_path,
        )
        independent_path = request_root / "independent_evaluation.json"
        atomic_write_json(independent_path, independent)
        xsd_pass = all(
            item.get("status") == "PASS"
            for item in independent.get("xsd") or []
        )
        complete = result.get("termination_decision") == "COMPLETE"
        end_to_end_pass = independent.get("decision") == "PASS" and complete
        report.update(
            {
                "materialization_decision": "PASS",
                "xsd_decision": "PASS" if xsd_pass else "FAIL",
                "selection_obligation_decision": obligations.get("decision"),
                "artifact_profile_decision": (
                    validation.get("artifact_profile") or {}
                ).get("decision"),
                "independent_decision": independent.get("decision"),
                "end_to_end_structural_decision": (
                    "PASS" if end_to_end_pass else "FAIL"
                ),
                "terminal_reason": (
                    "PASS"
                    if end_to_end_pass
                    else (
                        "LENGTH_TERMINATION"
                        if independent.get("decision") == "PASS"
                        else "POSTERIOR_VALIDATION_FAIL"
                    )
                ),
                "component_file_sha256": sha256_file(component_path),
                "interface_file_sha256": [
                    sha256_file(path) for path in interface_paths
                ],
                "validation_file_sha256": sha256_file(validation_path),
                "independent_evaluation_file_sha256": sha256_file(
                    independent_path
                ),
            }
        )
    except ValueError as exc:
        report.update(
            {
                "materialization_decision": "FAIL",
                "terminal_reason": "POSTPROCESS_EXCEPTION",
                "postprocess_error_type": type(exc).__name__,
            }
        )
    return report


def postprocess(
    *,
    contract_path: Path,
    schedule_path: Path,
    compiled_manifest_path: Path,
    source_root: Path,
    run_root: Path,
    output_root: Path,
) -> dict[str, Any]:
    if output_root.exists() and any(output_root.iterdir()):
        raise FileExistsError(f"output root is not empty: {output_root}")
    output_root.mkdir(parents=True, exist_ok=True)
    contract, schedule, compiled, source, run_manifest = verify_input_chain(
        contract_path=contract_path,
        schedule_path=schedule_path,
        compiled_manifest_path=compiled_manifest_path,
        source_root=source_root,
        run_root=run_root,
    )
    os.environ["LLM_API_KEY"] = "offline-local-placeholder"
    sys.path[:0] = [str(ATLAS_ROOT), str(PROBE_ROOT), str(REQUIREMENTS_ROOT)]
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
        SERIALIZATION_MANIFEST_PATH,
        xsd_path=XSD_PATH,
    )
    validation_service = GeneratedArxmlValidationService.from_config(CONFIG)
    if validation_service is None:
        raise RuntimeError("validation_service_is_disabled")

    source_by_case = {item["case_id"]: item for item in source["records"]}
    compiled_by_case = {item["case_id"]: item for item in compiled["records"]}
    reports: list[dict[str, Any]] = []
    report_files: list[dict[str, str]] = []
    for record in schedule["records"]:
        case_id = record["case_id"]
        source_record = source_by_case[case_id]
        compiled_record = compiled_by_case[case_id]
        # V4 deliberately transforms the large source schema into a finite
        # execution schema.  Comparing those two distinct identities made the
        # postprocessor fail before materialization.  Verify the two-link
        # chain instead: source -> compiled source identity, then compiled
        # manifest -> exact compiled asset/execution schema identity.
        if source_record["schema_sha256"] != compiled_record.get(
            "source_schema_sha256"
        ):
            raise RuntimeError(
                f"source_compiled_source_schema_hash_mismatch:{case_id}"
            )
        compiled_asset_path = (
            compiled_manifest_path.parent / str(compiled_record["path"])
        )
        if sha256_file(compiled_asset_path) != compiled_record.get("file_sha256"):
            raise RuntimeError(f"compiled_asset_file_hash_mismatch:{case_id}")
        compiled_asset = load_verified(
            compiled_asset_path, f"compiled_asset_{case_id}"
        )
        if compiled_asset.get("content_sha256") != compiled_record.get(
            "content_sha256"
        ):
            raise RuntimeError(f"compiled_asset_content_hash_mismatch:{case_id}")
        if compiled_asset.get("source_schema_sha256") != source_record[
            "schema_sha256"
        ]:
            raise RuntimeError(f"compiled_asset_source_schema_mismatch:{case_id}")
        if compiled_asset.get("schema_sha256") != compiled_record[
            "schema_sha256"
        ]:
            raise RuntimeError(f"compiled_asset_execution_schema_mismatch:{case_id}")
        context_path = source_root / source_record["postprocess_context_path"]
        if sha256_file(context_path) != source_record[
            "postprocess_context_file_sha256"
        ]:
            raise RuntimeError(f"postprocess_context_file_hash_mismatch:{case_id}")
        context = load_verified(context_path, f"postprocess_context_{case_id}")
        if context["content_sha256"] != source_record[
            "postprocess_context_content_sha256"
        ]:
            raise RuntimeError(
                f"postprocess_context_content_hash_mismatch:{case_id}"
            )
        result_path = run_root / f"{int(record['schedule_ordinal']):03d}.json"
        result = load_verified(
            result_path,
            f"run_result_{record['schedule_ordinal']}",
        )
        if result.get("schedule") != record:
            raise RuntimeError(
                f"run_result_schedule_mismatch:{record['schedule_ordinal']}"
            )
        report = materialize_one(
            result=result,
            context=context,
            source_root=source_root,
            output_root=output_root,
            serializer=serializer,
            validation_service=validation_service,
            evaluate=evaluate,
            apply_projection_map=apply_projection_map,
            render_document=render_document,
            merge_selection_obligations=merge_selection_obligations,
            validate_selection_obligations=validate_selection_obligations,
        )
        report["content_sha256"] = canonical_sha256(report)
        report_path = output_root / f"{int(record['schedule_ordinal']):03d}.json"
        atomic_write_json(report_path, report)
        reports.append(report)
        report_files.append(
            {"path": report_path.name, "sha256": sha256_file(report_path)}
        )

    manifest: dict[str, Any] = {
        "schema_version": "atlas.vllm.uga.postprocess_manifest.v1",
        "decision": "COMPLETE",
        "external_model_api_calls": 0,
        "experiment_id": contract["experiment_id"],
        "schedule_kind": schedule["kind"],
        "contract_content_sha256": contract["content_sha256"],
        "schedule_content_sha256": schedule["content_sha256"],
        "compiled_assets_content_sha256": compiled["content_sha256"],
        "source_assets_content_sha256": source["content_sha256"],
        "run_manifest_content_sha256": run_manifest["content_sha256"],
        "request_count": len(reports),
        "end_to_end_pass_count": sum(
            item["end_to_end_structural_decision"] == "PASS"
            for item in reports
        ),
        "report_files": report_files,
    }
    manifest["content_sha256"] = canonical_sha256(manifest)
    atomic_write_json(output_root / "POSTPROCESS_MANIFEST.json", manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--schedule", type=Path, required=True)
    parser.add_argument("--compiled-assets-manifest", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    manifest = postprocess(
        contract_path=args.contract.resolve(),
        schedule_path=args.schedule.resolve(),
        compiled_manifest_path=args.compiled_assets_manifest.resolve(),
        source_root=args.source_root.resolve(),
        run_root=args.run_root.resolve(),
        output_root=args.output_root.resolve(),
    )
    print(
        json.dumps(
            {
                "decision": manifest["decision"],
                "request_count": manifest["request_count"],
                "end_to_end_pass_count": manifest["end_to_end_pass_count"],
                "content_sha256": manifest["content_sha256"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
