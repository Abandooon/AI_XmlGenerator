"""Execute one frozen ATLAS vLLM U/G/A schedule without retries."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import time
from typing import Any, Mapping
from urllib.parse import urlparse

from qwen35_prompt_v026 import hash_token_ids, sha256_text
from strict_vllm_client_v026 import VllmExperimentConfig, VllmProtocolError
from strict_vllm_uga_client_v026 import (
    StrictUgaVllmClient,
    request_identity,
)
from token_evidence_v027 import encode_token_ids


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


def verify_content_hash(document: dict[str, Any], label: str) -> str:
    claimed = document.get("content_sha256")
    body = {key: value for key, value in document.items() if key != "content_sha256"}
    actual = canonical_sha256(body)
    if claimed != actual:
        raise RuntimeError(f"{label}_content_hash_mismatch")
    return actual


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


class HashChainLedger:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.previous_sha256 = "0" * 64
        self.sequence = 0

    def append(self, event: Mapping[str, Any]) -> str:
        core = {
            "schema_version": "atlas.vllm.uga.run_ledger.v1",
            "sequence": self.sequence,
            "previous_chain_sha256": self.previous_sha256,
            "event": dict(event),
        }
        chain_sha256 = hashlib.sha256(
            bytes.fromhex(self.previous_sha256) + canonical_json_bytes(core)
        ).hexdigest()
        record = {**core, "chain_sha256": chain_sha256}
        with self.path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(canonical_json_bytes(record).decode("utf-8") + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        self.previous_sha256 = chain_sha256
        self.sequence += 1
        return chain_sha256


def verify_loopback_endpoint(endpoint: str) -> None:
    parsed = urlparse(endpoint)
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost"}:
        raise RuntimeError("formal_runner_requires_plain_http_loopback_endpoint")


def verify_frozen_inputs(
    *,
    contract_path: Path,
    schedule_path: Path,
    assets_manifest_path: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    contract = load_json(contract_path)
    schedule = load_json(schedule_path)
    assets = load_json(assets_manifest_path)
    verify_content_hash(contract, "contract")
    verify_content_hash(schedule, "schedule")
    verify_content_hash(assets, "assets")
    allowed_decisions = {
        "READY_FOR_QUALIFICATION",
        "READY_FOR_FORMAL_AFTER_EXPLICIT_AUTHORIZATION",
    }
    if contract.get("decision") not in allowed_decisions:
        raise RuntimeError("contract_not_ready_for_execution")
    if schedule.get("schema_version") != "atlas.vllm.uga.schedule.v1":
        raise RuntimeError("schedule_schema_version_mismatch")
    if assets.get("schema_version") != "atlas.vllm.uga.compiled_assets.v2":
        raise RuntimeError("assets_schema_version_mismatch")
    if contract.get("schedule_kind") != schedule.get("kind"):
        raise RuntimeError("contract_schedule_kind_mismatch")
    expected_decision = {
        "qualification": "READY_FOR_QUALIFICATION",
        "formal": "READY_FOR_FORMAL_AFTER_EXPLICIT_AUTHORIZATION",
    }.get(schedule.get("kind"))
    if contract.get("decision") != expected_decision:
        raise RuntimeError("contract_decision_does_not_match_schedule_kind")
    identities = {
        "schedule_file_sha256": sha256_file(schedule_path),
        "schedule_content_sha256": schedule["content_sha256"],
        "assets_manifest_file_sha256": sha256_file(assets_manifest_path),
        "assets_manifest_content_sha256": assets["content_sha256"],
    }
    for field_name, actual in identities.items():
        if contract.get(field_name) != actual:
            raise RuntimeError(f"contract_identity_mismatch:{field_name}")
    if contract.get("experiment_id") != schedule.get("experiment_id"):
        raise RuntimeError("contract_schedule_experiment_id_mismatch")
    if schedule.get("assets_manifest_file_sha256") != identities[
        "assets_manifest_file_sha256"
    ]:
        raise RuntimeError("schedule_assets_file_hash_mismatch")
    if schedule.get("assets_manifest_content_sha256") != assets.get(
        "content_sha256"
    ):
        raise RuntimeError("schedule_assets_content_hash_mismatch")
    shared_fields = (
        "model_path",
        "max_model_len",
        "max_output_tokens",
    )
    for field_name in shared_fields:
        if schedule.get(field_name) != assets.get(field_name):
            raise RuntimeError(f"schedule_assets_field_mismatch:{field_name}")
        if contract.get(field_name) != assets.get(field_name):
            raise RuntimeError(f"contract_assets_field_mismatch:{field_name}")
    if schedule.get("enable_thinking") is not False:
        raise RuntimeError("schedule_thinking_must_be_disabled")
    if assets.get("enable_thinking") is not False:
        raise RuntimeError("assets_thinking_must_be_disabled")
    if schedule.get("request_count") != len(schedule.get("records") or []):
        raise RuntimeError("schedule_request_count_mismatch")
    asset_by_case = {item["case_id"]: item for item in assets["records"]}
    if len(asset_by_case) != assets.get("case_count"):
        raise RuntimeError("asset_case_identity_not_unique")
    asset_root = assets_manifest_path.parent
    for record in schedule["records"]:
        asset_record = asset_by_case.get(record["case_id"])
        if asset_record is None:
            raise RuntimeError(f"schedule_case_without_asset:{record['case_id']}")
        asset_path = asset_root / asset_record["path"]
        if sha256_file(asset_path) != record["asset_file_sha256"]:
            raise RuntimeError(f"schedule_asset_hash_mismatch:{record['case_id']}")
        if record.get("asset_content_sha256") != asset_record.get(
            "content_sha256"
        ):
            raise RuntimeError(
                f"schedule_asset_content_hash_mismatch:{record['case_id']}"
            )
        for field_name in (
            "prompt_sha256",
            "prompt_token_count",
            "prompt_token_ids_sha256",
            "schema_sha256",
        ):
            if record.get(field_name) != asset_record.get(field_name):
                raise RuntimeError(
                    f"schedule_asset_field_mismatch:{record['case_id']}:{field_name}"
                )
    return contract, schedule, assets


def classify_output(text: str, schema: Mapping[str, Any]) -> dict[str, Any]:
    try:
        value, end_index = json.JSONDecoder().raw_decode(text.lstrip())
    except (json.JSONDecodeError, TypeError):
        return {
            "parse_decision": "FAIL",
            "single_json_value_decision": "FAIL",
            "schema_decision": "NOT_EVALUATED",
            "schema_error_count": None,
        }
    trailing = text.lstrip()[end_index:]
    if trailing.strip():
        return {
            "parse_decision": "FAIL",
            "single_json_value_decision": "FAIL",
            "schema_decision": "NOT_EVALUATED",
            "schema_error_count": None,
        }
    from jsonschema import Draft202012Validator

    errors = list(Draft202012Validator(schema).iter_errors(value))
    return {
        "parse_decision": "PASS",
        "single_json_value_decision": "PASS",
        "schema_decision": "PASS" if not errors else "FAIL",
        "schema_error_count": len(errors),
    }


def load_asset(
    *,
    assets_manifest_path: Path,
    asset_record: Mapping[str, Any],
) -> dict[str, Any]:
    asset_path = assets_manifest_path.parent / str(asset_record["path"])
    asset = load_json(asset_path)
    if sha256_file(asset_path) != asset_record["file_sha256"]:
        raise RuntimeError(f"asset_file_hash_mismatch:{asset_record['case_id']}")
    if verify_content_hash(asset, "case_asset") != asset_record["content_sha256"]:
        raise RuntimeError(f"asset_content_hash_mismatch:{asset_record['case_id']}")
    return asset


# Two sentinel spellings are in use across this project's runners: this one and
# OPERATOR_STOP_REQUESTED, used by the AUTOSAR runner. Both are honoured, in
# both roots, so that an operator stop cannot be missed because of which name
# was written.
OPERATOR_STOP_SENTINEL_NAMES = ("OPERATOR_STOP", "OPERATOR_STOP_REQUESTED")


def operator_stop_requested(output_root: Path, control_root: Path | None) -> bool:
    roots = [output_root]
    if control_root is not None:
        roots.append(control_root)
    return any(
        (root / name).exists()
        for root in roots
        for name in OPERATOR_STOP_SENTINEL_NAMES
    )


async def execute_schedule(
    *,
    contract: dict[str, Any],
    schedule: dict[str, Any],
    assets: dict[str, Any],
    assets_manifest_path: Path,
    output_root: Path,
    endpoint: str,
    control_root: Path | None,
) -> dict[str, Any]:
    config = VllmExperimentConfig(
        endpoint=endpoint,
        model=contract["served_model_name"],
        max_tokens=int(contract["max_output_tokens"]),
        temperature=0.0,
        top_p=1.0,
        timeout_seconds=float(contract["request_timeout_seconds"]),
        max_model_len=int(contract["max_model_len"]),
    )
    client = StrictUgaVllmClient(config)
    ledger = HashChainLedger(output_root / "RUN_LEDGER.ndjson")
    asset_by_case = {item["case_id"]: item for item in assets["records"]}
    completed = 0

    def halt_for_infrastructure(record: Mapping[str, Any], error_code: str) -> None:
        ledger.append(
            {
                "event_type": "infrastructure_failure",
                "schedule_ordinal": record["schedule_ordinal"],
                "request_id": record["request_id"],
                "error_code": error_code,
            }
        )
        raise RuntimeError(error_code)

    ledger.append(
        {
            "event_type": "run_start",
            "experiment_id": contract["experiment_id"],
            "schedule_content_sha256": schedule["content_sha256"],
            "contract_content_sha256": contract["content_sha256"],
        }
    )
    for record in schedule["records"]:
        if operator_stop_requested(output_root, control_root):
            ledger.append(
                {
                    "event_type": "operator_stop",
                    "next_schedule_ordinal": record["schedule_ordinal"],
                }
            )
            raise RuntimeError("operator_stop_requested")
        asset = load_asset(
            assets_manifest_path=assets_manifest_path,
            asset_record=asset_by_case[record["case_id"]],
        )
        if asset["prompt_sha256"] != record["prompt_sha256"]:
            raise RuntimeError("scheduled_prompt_identity_mismatch")
        if asset["schema_sha256"] != record["schema_sha256"]:
            raise RuntimeError("scheduled_schema_identity_mismatch")
        identity = request_identity(
            arm=record["arm"],
            prompt=asset["prompt"],
            schema=asset["schema"],
            seed=int(record["seed"]),
            request_id=record["request_id"],
            config=config,
            prompt_token_count=int(asset["prompt_token_count"]),
            prompt_token_ids_sha256=asset["prompt_token_ids_sha256"],
        )
        started_at_unix_ns = time.time_ns()
        started = time.perf_counter()
        try:
            response = await client.generate(
                arm=record["arm"],
                prompt=asset["prompt"],
                schema=asset["schema"],
                seed=int(record["seed"]),
                request_id=record["request_id"],
            )
        except VllmProtocolError as exc:
            ledger.append(
                {
                    "event_type": "infrastructure_failure",
                    "schedule_ordinal": record["schedule_ordinal"],
                    "request_id": record["request_id"],
                    "error_type": type(exc).__name__,
                    "error_code": str(exc),
                }
            )
            raise
        elapsed_seconds = time.perf_counter() - started
        ended_at_unix_ns = time.time_ns()
        observed_prompt_hash = hash_token_ids(response["prompt_token_ids"])
        if observed_prompt_hash != asset["prompt_token_ids_sha256"]:
            halt_for_infrastructure(
                record,
                "server_prompt_token_ids_hash_mismatch",
            )
        if len(response["prompt_token_ids"]) != int(asset["prompt_token_count"]):
            halt_for_infrastructure(record, "server_prompt_token_count_mismatch")
        if response["usage"]["prompt_tokens"] != len(
            response["prompt_token_ids"]
        ):
            halt_for_infrastructure(record, "server_prompt_usage_count_mismatch")
        if response["usage"]["completion_tokens"] != len(
            response["output_token_ids"]
        ):
            halt_for_infrastructure(record, "server_output_usage_count_mismatch")
        outcome = classify_output(response["text"], asset["schema"])
        token_evidence = encode_token_ids(response["output_token_ids"])
        result: dict[str, Any] = {
            "schema_version": "atlas.vllm.uga.request_result.v2",
            "schedule": record,
            "request_identity": identity,
            "response_id": response["response_id"],
            "audit_request_id": record["audit_request_id"],
            "finish_reason": response["finish_reason"],
            "termination_decision": (
                "COMPLETE" if response["finish_reason"] == "stop" else "LENGTH"
            ),
            "usage": response["usage"],
            "elapsed_seconds": elapsed_seconds,
            "started_at_unix_ns": started_at_unix_ns,
            "ended_at_unix_ns": ended_at_unix_ns,
            "output_sha256": sha256_text(response["text"]),
            "output_token_ids_sha256": hash_token_ids(
                response["output_token_ids"]
            ),
            "output_token_ids_evidence": token_evidence,
            "output": response["text"],
            **outcome,
        }
        result["content_sha256"] = canonical_sha256(result)
        result_path = output_root / f"{record['schedule_ordinal']:03d}.json"
        atomic_write_json(result_path, result)
        completed += 1
        ledger.append(
            {
                "event_type": "request_complete",
                "schedule_ordinal": record["schedule_ordinal"],
                "request_id": record["request_id"],
                "arm": record["arm"],
                "result_file_sha256": sha256_file(result_path),
                "result_content_sha256": result["content_sha256"],
                "parse_decision": outcome["parse_decision"],
                "schema_decision": outcome["schema_decision"],
            }
        )

    ledger.append(
        {
            "event_type": "run_complete",
            "completed_request_count": completed,
        }
    )
    manifest: dict[str, Any] = {
        "schema_version": "atlas.vllm.uga.run_manifest.v2",
        "decision": "COMPLETE",
        "experiment_id": contract["experiment_id"],
        "schedule_kind": schedule["kind"],
        "scheduled_request_count": schedule["request_count"],
        "completed_request_count": completed,
        "ledger_file_sha256": sha256_file(output_root / "RUN_LEDGER.ndjson"),
        "ledger_final_chain_sha256": ledger.previous_sha256,
        "result_file_count": completed,
        "contract_content_sha256": contract["content_sha256"],
        "schedule_content_sha256": schedule["content_sha256"],
        "assets_manifest_content_sha256": assets["content_sha256"],
        "result_files": [
            {
                "path": f"{record['schedule_ordinal']:03d}.json",
                "sha256": sha256_file(
                    output_root / f"{record['schedule_ordinal']:03d}.json"
                ),
            }
            for record in schedule["records"]
        ],
        "offline_postprocess_decision": "NOT_EVALUATED",
    }
    manifest["content_sha256"] = canonical_sha256(manifest)
    atomic_write_json(output_root / "RUN_MANIFEST.json", manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--schedule", type=Path, required=True)
    parser.add_argument("--assets-manifest", type=Path, required=True)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--control-root", type=Path)
    parser.add_argument("--endpoint", default="http://127.0.0.1:8000")
    parser.add_argument("--metrics-stop-file", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--authorize-formal", action="store_true")
    args = parser.parse_args()
    contract_path = args.contract.resolve()
    schedule_path = args.schedule.resolve()
    assets_manifest_path = args.assets_manifest.resolve()
    contract, schedule, assets = verify_frozen_inputs(
        contract_path=contract_path,
        schedule_path=schedule_path,
        assets_manifest_path=assets_manifest_path,
    )
    verify_loopback_endpoint(args.endpoint)
    if args.endpoint.rstrip("/") != str(
        contract.get("runtime_policy", {}).get("endpoint") or ""
    ).rstrip("/"):
        raise RuntimeError("endpoint_does_not_match_contract")
    if schedule["kind"] == "formal" and not args.authorize_formal:
        raise RuntimeError("formal_schedule_requires_explicit_cli_authorization")
    if args.dry_run:
        print(
            json.dumps(
                {
                    "decision": "PASS",
                    "external_model_calls": 0,
                    "schedule_kind": schedule["kind"],
                    "request_count": schedule["request_count"],
                },
                sort_keys=True,
            )
        )
        return 0
    if args.output_root is None:
        raise RuntimeError("output_root_is_required_without_dry_run")
    output_root = args.output_root.resolve()
    if output_root.exists() and any(output_root.iterdir()):
        raise FileExistsError(f"output root is not empty: {output_root}")
    output_root.mkdir(parents=True, exist_ok=True)
    control_root = args.control_root.resolve() if args.control_root else None
    metrics_stop_file = (
        args.metrics_stop_file.resolve() if args.metrics_stop_file else None
    )
    if metrics_stop_file is not None and metrics_stop_file.exists():
        raise FileExistsError(
            f"metrics stop file already exists: {metrics_stop_file}"
        )
    exit_code = 0
    try:
        manifest = asyncio.run(
            execute_schedule(
                contract=contract,
                schedule=schedule,
                assets=assets,
                assets_manifest_path=assets_manifest_path,
                output_root=output_root,
                endpoint=args.endpoint,
                control_root=control_root,
            )
        )
    except Exception as exc:
        result_paths = sorted(output_root.glob("[0-9][0-9][0-9].json"))
        failure_manifest: dict[str, Any] = {
            "schema_version": "atlas.vllm.uga.run_failure.v1",
            "decision": "FAIL",
            "paper_result_admissible": False,
            "error_type": type(exc).__name__,
            "error_code": str(exc),
            "experiment_id": contract.get("experiment_id"),
            "schedule_kind": schedule.get("kind"),
            "scheduled_request_count": schedule.get("request_count"),
            "completed_result_count": len(result_paths),
            "contract_content_sha256": contract.get("content_sha256"),
            "schedule_content_sha256": schedule.get("content_sha256"),
            "assets_manifest_content_sha256": assets.get("content_sha256"),
            "ledger_file_sha256": (
                sha256_file(output_root / "RUN_LEDGER.ndjson")
                if (output_root / "RUN_LEDGER.ndjson").is_file()
                else None
            ),
            "result_files": [
                {"path": path.name, "sha256": sha256_file(path)}
                for path in result_paths
            ],
        }
        failure_manifest["content_sha256"] = canonical_sha256(failure_manifest)
        atomic_write_json(
            output_root / "RUN_FAILURE_MANIFEST.json", failure_manifest
        )
        manifest = failure_manifest
        exit_code = 2
    finally:
        if metrics_stop_file is not None:
            metrics_stop_file.parent.mkdir(parents=True, exist_ok=True)
            metrics_stop_file.write_text(
                "uga_runner_finished\n",
                encoding="utf-8",
                newline="\n",
            )
    print(
        json.dumps(
            {
                "decision": manifest["decision"],
                "completed_request_count": manifest.get(
                    "completed_request_count",
                    manifest.get("completed_result_count", 0),
                ),
                "content_sha256": manifest["content_sha256"],
            },
            sort_keys=True,
        )
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
