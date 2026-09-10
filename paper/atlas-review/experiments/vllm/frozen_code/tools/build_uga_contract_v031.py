"""Build a fail-closed qualification or formal U/G/A experiment contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any


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


def load_verified(path: Path, label: str) -> dict[str, Any]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise RuntimeError(f"{label}_root_is_not_object")
    claimed = document.get("content_sha256")
    body = {key: value for key, value in document.items() if key != "content_sha256"}
    if claimed != canonical_sha256(body):
        raise RuntimeError(f"{label}_content_hash_mismatch")
    return document


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


def build_contract(
    *,
    protocol_path: Path,
    schedule_path: Path,
    assets_manifest_path: Path,
    runtime_fingerprint_path: Path,
    overlay_manifest_path: Path,
    execution_schema_preflight_path: Path,
    materialized_witness_preflight_path: Path,
    xgrammar_schema_probe_path: Path,
    xgrammar_regression_path: Path,
    detokenization_regression_path: Path,
    nccl_regression_path: Path,
    qualification_manifest_path: Path | None,
) -> dict[str, Any]:
    schedule = load_verified(schedule_path, "schedule")
    assets = load_verified(assets_manifest_path, "assets")
    runtime = load_verified(runtime_fingerprint_path, "runtime")
    overlay = load_verified(overlay_manifest_path, "overlay")
    execution_schema_preflight = load_verified(
        execution_schema_preflight_path, "execution_schema_preflight"
    )
    materialized_witness_preflight = load_verified(
        materialized_witness_preflight_path, "materialized_witness_preflight"
    )
    xgrammar_schema_probe = load_verified(
        xgrammar_schema_probe_path, "xgrammar_schema_probe"
    )
    xgrammar_regression = load_verified(
        xgrammar_regression_path, "xgrammar_regression"
    )
    detokenization_regression = load_verified(
        detokenization_regression_path,
        "detokenization_regression",
    )
    nccl_regression = load_verified(nccl_regression_path, "nccl_regression")
    if schedule.get("schema_version") != "atlas.vllm.uga.schedule.v1":
        raise RuntimeError("schedule_schema_version_mismatch")
    if schedule.get("kind") not in {"qualification", "formal"}:
        raise RuntimeError("schedule_kind_is_invalid")
    if runtime.get("decision") != "PASS":
        raise RuntimeError("runtime_fingerprint_not_pass")
    if runtime.get("schema_version") != "atlas.vllm.uga.runtime_fingerprint.v1":
        raise RuntimeError("runtime_fingerprint_schema_version_mismatch")
    topology_probe = runtime.get("gpu", {}).get("topology_probe", {})
    if topology_probe.get("decision") != "PASS":
        raise RuntimeError("runtime_topology_probe_not_pass")
    topology_mode = topology_probe.get("mode")
    if topology_mode not in {"matrix", "known_hwloc_cpuset_degradation"}:
        raise RuntimeError("runtime_topology_probe_mode_invalid")
    if topology_mode == "known_hwloc_cpuset_degradation":
        topology_output = str(topology_probe.get("output") or "")
        if (
            topology_probe.get("returncode") == 0
            or topology_probe.get("requires_nccl_tp2_gate") is not True
            or topology_probe.get("degraded_errors") != []
            or "Topology does not contain any PU" not in topology_output
            or "Failed to run topology matrix" not in topology_output
            or len(set(topology_probe.get("gpu_uuids") or [])) != 2
            or not topology_probe.get("proc_self_status_affinity")
            or not topology_probe.get("cgroup_cpuset_effective")
            or not topology_probe.get("kernel_online_cpus")
        ):
            raise RuntimeError("runtime_degraded_topology_evidence_invalid")
    elif topology_probe.get("returncode") != 0:
        raise RuntimeError("runtime_topology_matrix_returncode_invalid")
    if assets.get("decision") != "PASS":
        raise RuntimeError("assets_manifest_not_pass")
    if assets.get("schema_version") != "atlas.vllm.uga.compiled_assets.v3":
        raise RuntimeError("compiled_assets_schema_version_mismatch")
    if assets.get("max_output_tokens") != 16_384:
        raise RuntimeError("v3_protocol_requires_16384_output_tokens")
    if execution_schema_preflight.get("decision") != "PASS":
        raise RuntimeError("execution_schema_preflight_not_pass")
    if execution_schema_preflight.get("case_count") != 20:
        raise RuntimeError("execution_schema_preflight_case_count_mismatch")
    if execution_schema_preflight.get("source_instance_constraint_count") != 720:
        raise RuntimeError("execution_schema_preflight_source_constraint_mismatch")
    if execution_schema_preflight.get("compiled_instance_exact_count") != 720:
        raise RuntimeError("execution_schema_preflight_compiled_constraint_mismatch")
    if execution_schema_preflight.get("compiled_instance_const_count") != 670:
        raise RuntimeError("execution_schema_preflight_const_count_mismatch")
    if execution_schema_preflight.get(
        "compiled_instance_numeric_bound_count"
    ) != 50:
        raise RuntimeError("execution_schema_preflight_numeric_bound_count_mismatch")
    if execution_schema_preflight.get("exact_value_mutation_count") != 754:
        raise RuntimeError("execution_schema_preflight_exact_mutation_mismatch")
    if execution_schema_preflight.get("required_property_mutation_count") != 1451:
        raise RuntimeError("execution_schema_preflight_required_mutation_mismatch")
    if execution_schema_preflight.get("source_manifest_content_sha256") != assets.get(
        "source_manifest_content_sha256"
    ):
        raise RuntimeError("execution_schema_preflight_source_mismatch")
    preflight_schemas = {
        str(item["case_id"]): str(item["execution_schema_sha256"])
        for item in execution_schema_preflight.get("records") or []
    }
    asset_schemas = {
        str(item["case_id"]): str(item["schema_sha256"])
        for item in assets.get("records") or []
    }
    if preflight_schemas != asset_schemas:
        raise RuntimeError("execution_schema_preflight_assets_mismatch")
    if materialized_witness_preflight.get("decision") != "PASS":
        raise RuntimeError("materialized_witness_preflight_not_pass")
    materialized_requirements = {
        "case_count": 20,
        "xsd_pass_count": 20,
        "selection_obligation_pass_count": 20,
        "independent_pass_count": 20,
        "source_instance_constraint_count": 720,
        "compiled_instance_exact_count": 720,
        "compiled_instance_const_count": 670,
        "compiled_instance_numeric_bound_count": 50,
        "exact_value_mutation_count": 754,
        "required_property_mutation_count": 1451,
    }
    for field_name, expected in materialized_requirements.items():
        if materialized_witness_preflight.get(field_name) != expected:
            raise RuntimeError(
                f"materialized_witness_preflight_mismatch:{field_name}"
            )
    if materialized_witness_preflight.get(
        "source_manifest_content_sha256"
    ) != assets.get("source_manifest_content_sha256"):
        raise RuntimeError("materialized_witness_preflight_source_mismatch")
    if xgrammar_schema_probe.get("decision") != "PASS":
        raise RuntimeError("xgrammar_schema_probe_not_pass")
    if xgrammar_schema_probe.get("schema_version") != (
        "atlas.vllm.uga.xgrammar_schema_probe.v2"
    ):
        raise RuntimeError("xgrammar_schema_probe_schema_version_mismatch")
    if xgrammar_schema_probe.get("xgrammar_version") != "0.2.6rc1":
        raise RuntimeError("xgrammar_schema_probe_version_mismatch")
    if xgrammar_schema_probe.get("model_request_count") != 0:
        raise RuntimeError("xgrammar_schema_probe_made_model_requests")
    if xgrammar_schema_probe.get("model_path") != assets.get("model_path"):
        raise RuntimeError("xgrammar_schema_probe_model_path_mismatch")
    if xgrammar_schema_probe.get("compiled_assets_content_sha256") != assets.get(
        "content_sha256"
    ):
        raise RuntimeError("xgrammar_schema_probe_assets_mismatch")
    if xgrammar_schema_probe.get("case_count") != assets.get("case_count"):
        raise RuntimeError("xgrammar_schema_probe_case_count_mismatch")
    probed_schemas = {
        str(item["case_id"]): str(item["schema_sha256"])
        for item in xgrammar_schema_probe.get("records") or []
        if item.get("decision") == "PASS"
        and item.get("valid_replay", {}).get("accepted") is True
        and item.get("valid_replay", {}).get("terminated") is True
        and item.get("invalid_replay", {}).get("accepted") is False
    }
    if probed_schemas != asset_schemas:
        raise RuntimeError("xgrammar_schema_probe_schema_identity_mismatch")
    if xgrammar_regression.get("decision") != "PASS":
        raise RuntimeError("xgrammar_regression_not_pass")
    if xgrammar_regression.get("schema_version") != (
        "atlas.vllm.uga.xgrammar_regression.v2"
    ):
        raise RuntimeError("xgrammar_regression_schema_version_mismatch")
    if xgrammar_regression.get("xgrammar_version") != "0.2.6rc1":
        raise RuntimeError("xgrammar_regression_version_mismatch")
    if xgrammar_regression.get("model_request_count") != 0:
        raise RuntimeError("xgrammar_regression_made_model_requests")
    if runtime.get("software", {}).get("xgrammar") != xgrammar_regression.get(
        "xgrammar_version"
    ):
        raise RuntimeError("runtime_xgrammar_regression_version_mismatch")
    if runtime.get("software", {}).get("distributions", {}).get(
        "transformers"
    ) != xgrammar_regression.get("transformers_version"):
        raise RuntimeError("runtime_xgrammar_regression_transformers_mismatch")
    if xgrammar_regression.get("model_path") != assets.get("model_path"):
        raise RuntimeError("xgrammar_regression_model_path_mismatch")
    if xgrammar_regression.get("compiled_assets_content_sha256") != assets.get(
        "content_sha256"
    ):
        raise RuntimeError("xgrammar_regression_assets_mismatch")
    if xgrammar_regression.get("errors") != []:
        raise RuntimeError("xgrammar_regression_contains_errors")
    if detokenization_regression.get("decision") != "PASS":
        raise RuntimeError("detokenization_regression_not_pass")
    if detokenization_regression.get("schema_version") != (
        "atlas.vllm.uga.structured_stop_detokenization_regression.v1"
    ):
        raise RuntimeError("detokenization_regression_schema_version_mismatch")
    if detokenization_regression.get("model_request_count") != 0:
        raise RuntimeError("detokenization_regression_made_model_requests")
    if detokenization_regression.get("model_path") != assets.get("model_path"):
        raise RuntimeError("detokenization_regression_model_path_mismatch")
    if detokenization_regression.get("vllm_version") != runtime.get(
        "software", {}
    ).get("vllm"):
        raise RuntimeError("detokenization_regression_vllm_version_mismatch")
    if detokenization_regression.get("transformers_version") != runtime.get(
        "software", {}
    ).get("distributions", {}).get("transformers"):
        raise RuntimeError("detokenization_regression_transformers_mismatch")
    if detokenization_regression.get("errors") != []:
        raise RuntimeError("detokenization_regression_contains_errors")
    if detokenization_regression.get("semantics") != {
        "grammar_completion_excludes_final_token": False,
        "eos_excludes_final_token": True,
        "stop_token_excludes_final_token": True,
        "length_completion_excludes_final_token": False,
    }:
        raise RuntimeError("detokenization_regression_semantics_mismatch")
    expected_final_tokens = {92: "}", 29958: '"}}'}
    observed_final_tokens = {
        int(item["token_id"]): str(item["grammar_completion_text"])
        for item in detokenization_regression.get("cases") or []
        if item.get("decision") == "PASS"
        and item.get("errors") == []
        and item.get("ordinary_stop_text") == ""
        and item.get("grammar_output_token_ids") == [item.get("token_id")]
        and item.get("ordinary_stop_output_token_ids") == [item.get("token_id")]
    }
    if observed_final_tokens != expected_final_tokens:
        raise RuntimeError("detokenization_regression_exact_cases_mismatch")
    required_launch_environment = {"NCCL_CUMEM_HOST_ENABLE": "0"}
    if runtime.get("required_launch_environment") != required_launch_environment:
        raise RuntimeError("runtime_required_launch_environment_mismatch")
    if nccl_regression.get("decision") != "PASS":
        raise RuntimeError("nccl_regression_not_pass")
    if nccl_regression.get("schema_version") != (
        "atlas.vllm.uga.nccl_tp2_regression.v1"
    ):
        raise RuntimeError("nccl_regression_schema_version_mismatch")
    if nccl_regression.get("model_request_count") != 0:
        raise RuntimeError("nccl_regression_made_model_requests")
    if nccl_regression.get("world_size") != 2:
        raise RuntimeError("nccl_regression_world_size_mismatch")
    if nccl_regression.get("required_launch_environment") != (
        required_launch_environment
    ):
        raise RuntimeError("nccl_regression_launch_environment_mismatch")
    if nccl_regression.get("p2p_override_used") is not False:
        raise RuntimeError("nccl_regression_used_p2p_override")
    if nccl_regression.get("errors") != []:
        raise RuntimeError("nccl_regression_contains_errors")
    nccl_ranks = {
        int(item["rank"]): item
        for item in nccl_regression.get("records") or []
        if item.get("decision") == "PASS"
    }
    if set(nccl_ranks) != {0, 1} or any(
        item.get("world_size") != 2
        or item.get("mean") != 2.0
        or item.get("nccl_cumem_host_enable") != "0"
        or item.get("nccl_p2p_disable") is not None
        for item in nccl_ranks.values()
    ):
        raise RuntimeError("nccl_regression_rank_evidence_mismatch")
    expected_schemas = {
        str(item["case_id"]): str(item["schema_sha256"])
        for item in assets.get("records") or []
    }
    witness_records = xgrammar_regression.get("witness_records") or []
    witnessed_schemas = {
        str(item["case_id"]): str(item["schema_sha256"])
        for item in witness_records
        if item.get("decision") == "PASS"
    }
    if (
        len(witness_records) != assets.get("case_count")
        or xgrammar_regression.get("witness_case_count") != assets.get("case_count")
        or witnessed_schemas != expected_schemas
    ):
        raise RuntimeError("xgrammar_regression_witness_identity_mismatch")
    expected_exact_rejections = {
        "005.json": {
            "first_rejected_token_index": 599,
            "case_id": "ASW-STD-04",
            "legacy_asset_file": "005.asset.json",
            "legacy_schema_sha256": (
                "6056aea3af7902bca032c119580c588a43773ef871fcdbe31f6ab82f5f86efbe"
            ),
        },
        "007.json": {
            "first_rejected_token_index": 1214,
            "case_id": "ASW-FULL-03",
            "legacy_asset_file": "007.asset.json",
            "legacy_schema_sha256": (
                "4ff91ec518bf61aa5aa15713aae1ad3aebd6610cb20ac1d03cfe6b5d95e810c7"
            ),
        },
    }
    exact_rejections = {
        str(item["fixture"]): {
            "first_rejected_token_index": item.get("replay", {}).get(
                "first_rejected_token_index"
            ),
            "case_id": item.get("case_id"),
            "legacy_asset_file": item.get("legacy_asset_file"),
            "legacy_schema_sha256": item.get("legacy_schema_sha256"),
        }
        for item in xgrammar_regression.get("exact_v4_failure_replays") or []
        if item.get("decision") == "PASS"
        and item.get("replay", {}).get("accepted_all") is False
    }
    if exact_rejections != expected_exact_rejections:
        raise RuntimeError("xgrammar_regression_exact_replay_mismatch")
    if schedule.get("assets_manifest_file_sha256") != sha256_file(
        assets_manifest_path
    ):
        raise RuntimeError("schedule_assets_file_hash_mismatch")
    if runtime.get("overlay_manifest_file_sha256") != sha256_file(
        overlay_manifest_path
    ):
        raise RuntimeError("runtime_overlay_file_hash_mismatch")
    if overlay.get("decision") != "PASS" or not overlay.get("python_only"):
        raise RuntimeError("overlay_manifest_not_admitted")
    for field_name in ("model_path", "max_model_len", "max_output_tokens"):
        if schedule.get(field_name) != assets.get(field_name):
            raise RuntimeError(f"schedule_assets_field_mismatch:{field_name}")
    if runtime.get("model", {}).get("path") != assets.get("model_path"):
        raise RuntimeError("runtime_assets_model_path_mismatch")
    qualification_identity = None
    if schedule["kind"] == "formal":
        if qualification_manifest_path is None:
            raise RuntimeError("formal_contract_requires_qualification_manifest")
        qualification = load_verified(
            qualification_manifest_path,
            "qualification_manifest",
        )
        if qualification.get("decision") != "PASS":
            raise RuntimeError("qualification_manifest_not_pass")
        qualification_requirements = {
            "qualified_protocol_file_sha256": sha256_file(protocol_path),
            "qualified_runtime_fingerprint_sha256": runtime["content_sha256"],
            "qualified_overlay_manifest_content_sha256": overlay[
                "content_sha256"
            ],
            "qualified_assets_manifest_content_sha256": assets[
                "content_sha256"
            ],
            "qualified_model_tree_content_sha256": runtime["model"][
                "tree_content_sha256"
            ],
            "qualified_model_path": assets["model_path"],
            "qualified_max_model_len": assets["max_model_len"],
            "qualified_max_output_tokens": assets["max_output_tokens"],
            "qualified_xgrammar_regression_content_sha256": xgrammar_regression[
                "content_sha256"
            ],
            "qualified_execution_schema_preflight_content_sha256": (
                execution_schema_preflight["content_sha256"]
            ),
            "qualified_materialized_witness_preflight_content_sha256": (
                materialized_witness_preflight["content_sha256"]
            ),
            "qualified_xgrammar_schema_probe_content_sha256": (
                xgrammar_schema_probe["content_sha256"]
            ),
            "qualified_detokenization_regression_content_sha256": (
                detokenization_regression["content_sha256"]
            ),
            "qualified_nccl_regression_content_sha256": nccl_regression[
                "content_sha256"
            ],
        }
        for field_name, expected in qualification_requirements.items():
            if qualification.get(field_name) != expected:
                raise RuntimeError(
                    f"qualification_identity_mismatch:{field_name}"
                )
        qualification_identity = {
            "file_sha256": sha256_file(qualification_manifest_path),
            "content_sha256": qualification["content_sha256"],
        }
    elif qualification_manifest_path is not None:
        raise RuntimeError("qualification_contract_must_not_claim_prior_qualification")

    contract: dict[str, Any] = {
        "schema_version": "atlas.vllm.uga.experiment_contract.v2",
        "decision": "READY_FOR_QUALIFICATION",
        "experiment_id": schedule["experiment_id"],
        "schedule_kind": schedule["kind"],
        "protocol_file_sha256": sha256_file(protocol_path),
        "schedule_file_sha256": sha256_file(schedule_path),
        "schedule_content_sha256": schedule["content_sha256"],
        "assets_manifest_file_sha256": sha256_file(assets_manifest_path),
        "assets_manifest_content_sha256": assets["content_sha256"],
        "runtime_fingerprint_file_sha256": sha256_file(
            runtime_fingerprint_path
        ),
        "runtime_fingerprint_sha256": runtime["content_sha256"],
        "overlay_manifest_file_sha256": sha256_file(overlay_manifest_path),
        "overlay_manifest_content_sha256": overlay["content_sha256"],
        "execution_schema_preflight_file_sha256": sha256_file(
            execution_schema_preflight_path
        ),
        "execution_schema_preflight_content_sha256": (
            execution_schema_preflight["content_sha256"]
        ),
        "materialized_witness_preflight_file_sha256": sha256_file(
            materialized_witness_preflight_path
        ),
        "materialized_witness_preflight_content_sha256": (
            materialized_witness_preflight["content_sha256"]
        ),
        "xgrammar_schema_probe_file_sha256": sha256_file(
            xgrammar_schema_probe_path
        ),
        "xgrammar_schema_probe_content_sha256": xgrammar_schema_probe[
            "content_sha256"
        ],
        "xgrammar_regression_file_sha256": sha256_file(
            xgrammar_regression_path
        ),
        "xgrammar_regression_content_sha256": xgrammar_regression[
            "content_sha256"
        ],
        "detokenization_regression_file_sha256": sha256_file(
            detokenization_regression_path
        ),
        "detokenization_regression_content_sha256": (
            detokenization_regression["content_sha256"]
        ),
        "nccl_regression_file_sha256": sha256_file(nccl_regression_path),
        "nccl_regression_content_sha256": nccl_regression["content_sha256"],
        "qualification_identity": qualification_identity,
        "served_model_name": "Qwen3.5-9B",
        "model_path": assets["model_path"],
        "model_tree_content_sha256": runtime["model"]["tree_content_sha256"],
        "max_model_len": assets["max_model_len"],
        "max_output_tokens": assets["max_output_tokens"],
        "request_timeout_seconds": 1800,
        "sampling": {
            "temperature": 0.0,
            "top_p": 1.0,
            "seeds": [104729, 130363, 155921],
            "speculative_decoding": False,
            "thinking": False,
        },
        "runtime_policy": {
            "endpoint": "http://127.0.0.1:8000",
            "tensor_parallel_size": 2,
            "dtype": "bfloat16",
            "prefix_caching": False,
            "max_num_seqs": 1,
            "request_logging": False,
            "retries": 0,
            "structured_outputs_backend": "xgrammar",
            "disable_any_whitespace": True,
            "terminate_without_stop_token": True,
            "stop_on_grammar_termination": True,
            "preserve_grammar_completion_payload_token": True,
            "required_environment": required_launch_environment,
        },
    }
    if schedule["kind"] == "formal":
        contract["decision"] = "READY_FOR_FORMAL_AFTER_EXPLICIT_AUTHORIZATION"
    contract["content_sha256"] = canonical_sha256(contract)
    return contract


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--schedule", type=Path, required=True)
    parser.add_argument("--assets-manifest", type=Path, required=True)
    parser.add_argument("--runtime-fingerprint", type=Path, required=True)
    parser.add_argument("--overlay-manifest", type=Path, required=True)
    parser.add_argument("--execution-schema-preflight", type=Path, required=True)
    parser.add_argument(
        "--materialized-witness-preflight", type=Path, required=True
    )
    parser.add_argument("--xgrammar-schema-probe", type=Path, required=True)
    parser.add_argument("--xgrammar-regression", type=Path, required=True)
    parser.add_argument(
        "--detokenization-regression",
        type=Path,
        required=True,
    )
    parser.add_argument("--nccl-regression", type=Path, required=True)
    parser.add_argument("--qualification-manifest", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    contract = build_contract(
        protocol_path=args.protocol.resolve(),
        schedule_path=args.schedule.resolve(),
        assets_manifest_path=args.assets_manifest.resolve(),
        runtime_fingerprint_path=args.runtime_fingerprint.resolve(),
        overlay_manifest_path=args.overlay_manifest.resolve(),
        execution_schema_preflight_path=(
            args.execution_schema_preflight.resolve()
        ),
        materialized_witness_preflight_path=(
            args.materialized_witness_preflight.resolve()
        ),
        xgrammar_schema_probe_path=args.xgrammar_schema_probe.resolve(),
        xgrammar_regression_path=args.xgrammar_regression.resolve(),
        detokenization_regression_path=(
            args.detokenization_regression.resolve()
        ),
        nccl_regression_path=args.nccl_regression.resolve(),
        qualification_manifest_path=(
            args.qualification_manifest.resolve()
            if args.qualification_manifest
            else None
        ),
    )
    atomic_write_json(args.output.resolve(), contract)
    print(
        json.dumps(
            {
                "decision": contract["decision"],
                "content_sha256": contract["content_sha256"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
