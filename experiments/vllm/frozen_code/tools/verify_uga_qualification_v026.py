"""Independently verify the non-paper ATLAS U/G/A qualification run."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Any

from token_evidence_v027 import decode_token_ids


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


def verify_run_ledger(path: Path, expected_requests: int) -> dict[str, Any]:
    """Recompute the run ledger's hash chain and its terminal invariants.

    This duplicates the formal summarizer's implementation on purpose: the
    deployment bundle has to be self-contained on the target host, and the
    summarizer stays on the analysis workstation. The two copies must agree,
    and a test asserts that they do on the same fixture.
    """

    records = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    previous = "0" * 64
    request_complete_count = 0
    for sequence, record in enumerate(records):
        if record.get("sequence") != sequence:
            raise RuntimeError("run_ledger_sequence_gap")
        if record.get("previous_chain_sha256") != previous:
            raise RuntimeError("run_ledger_previous_chain_mismatch")
        core = {
            key: record.get(key)
            for key in (
                "schema_version",
                "sequence",
                "previous_chain_sha256",
                "event",
            )
        }
        expected = hashlib.sha256(
            bytes.fromhex(previous) + canonical_json_bytes(core)
        ).hexdigest()
        if record.get("chain_sha256") != expected:
            raise RuntimeError("run_ledger_chain_mismatch")
        previous = expected
        if (record.get("event") or {}).get("event_type") == "request_complete":
            request_complete_count += 1
    event_types = [
        (record.get("event") or {}).get("event_type") for record in records
    ]
    if event_types[:1] != ["run_start"] or event_types[-1:] != ["run_complete"]:
        raise RuntimeError("run_ledger_boundary_mismatch")
    if request_complete_count != expected_requests:
        raise RuntimeError("run_ledger_request_complete_count_mismatch")
    if any(item == "infrastructure_failure" for item in event_types):
        raise RuntimeError("run_ledger_contains_infrastructure_failure")
    return {
        "record_count": len(records),
        "request_complete_count": request_complete_count,
        "final_chain_sha256": previous,
        "file_sha256": sha256_file(path),
    }


def load_verified(path: Path, label: str) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{label}_root_is_not_object")
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


def load_audit_verifier(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(
        "atlas_frozen_qualification_audit_verifier",
        path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("audit_verifier_module_cannot_be_loaded")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.verify_audit_records


def verify_qualification(
    *,
    contract_path: Path,
    schedule_path: Path,
    run_root: Path,
    audit_root: Path,
    postprocess_root: Path,
    audit_verifier_path: Path,
) -> dict[str, Any]:
    contract = load_verified(contract_path, "contract")
    schedule = load_verified(schedule_path, "schedule")
    run_manifest = load_verified(run_root / "RUN_MANIFEST.json", "run_manifest")
    if schedule.get("kind") != "qualification":
        raise RuntimeError("qualification_verifier_requires_qualification_schedule")

    # The contract's identity fields are copied into this verifier's output and
    # the formal contract builder then trusts them. They have to be checked
    # here rather than merely carried, or a qualification root produced under a
    # different contract or schedule could be laundered into a formal contract
    # without anything noticing.
    if contract.get("decision") != "READY_FOR_QUALIFICATION":
        raise RuntimeError("qualification_contract_is_not_ready_for_qualification")
    if contract.get("schedule_kind") != "qualification":
        raise RuntimeError("qualification_contract_schedule_kind_mismatch")
    if contract.get("schedule_content_sha256") != schedule.get("content_sha256"):
        raise RuntimeError("qualification_contract_schedule_content_mismatch")
    if contract.get("schedule_file_sha256") != sha256_file(schedule_path):
        raise RuntimeError("qualification_contract_schedule_file_mismatch")

    if run_manifest.get("decision") != "COMPLETE":
        raise RuntimeError("qualification_run_is_not_complete")
    if run_manifest.get("completed_request_count") != schedule.get("request_count"):
        raise RuntimeError("qualification_request_count_mismatch")
    if run_manifest.get("schedule_content_sha256") != schedule.get("content_sha256"):
        raise RuntimeError("qualification_run_schedule_mismatch")
    if run_manifest.get("contract_content_sha256") != contract.get(
        "content_sha256"
    ):
        raise RuntimeError("qualification_run_contract_mismatch")

    # A COMPLETE run manifest is a claim; the ledger is the evidence. Recompute
    # the chain rather than trusting the manifest's summary of it, and require
    # the manifest's own ledger identity to match what was recomputed.
    ledger = verify_run_ledger(
        run_root / "RUN_LEDGER.ndjson", int(schedule["request_count"])
    )
    if run_manifest.get("ledger_file_sha256") != ledger["file_sha256"]:
        raise RuntimeError("qualification_ledger_file_mismatch")
    if run_manifest.get("ledger_final_chain_sha256") != ledger[
        "final_chain_sha256"
    ]:
        raise RuntimeError("qualification_ledger_chain_mismatch")

    postprocess_manifest = load_verified(
        postprocess_root / "POSTPROCESS_MANIFEST.json",
        "postprocess_manifest",
    )
    if postprocess_manifest.get("decision") != "COMPLETE":
        raise RuntimeError("qualification_postprocess_is_not_complete")
    if postprocess_manifest.get("schedule_content_sha256") != schedule.get(
        "content_sha256"
    ):
        raise RuntimeError("qualification_postprocess_schedule_mismatch")
    if postprocess_manifest.get("run_manifest_content_sha256") != run_manifest.get(
        "content_sha256"
    ):
        raise RuntimeError("qualification_postprocess_run_mismatch")

    # Each result file is pinned by the run manifest. Reading whatever happens
    # to be on disk under a matching name would let an edited or substituted
    # result reach the formal contract, so the registry is the authority for
    # which files exist and what bytes they must contain.
    registered_results = {
        str(item["path"]): str(item["sha256"])
        for item in run_manifest.get("result_files") or []
    }
    if len(registered_results) != schedule["request_count"]:
        raise RuntimeError("qualification_run_manifest_result_count_mismatch")
    on_disk = {path.name for path in run_root.glob("[0-9][0-9][0-9].json")}
    if on_disk != set(registered_results):
        raise RuntimeError("qualification_result_files_differ_from_manifest")
    result_files = [
        run_root / name for name in sorted(registered_results)
    ]

    schedule_by_request = {
        str(record["request_id"]): record for record in schedule["records"]
    }
    result_by_request: dict[str, dict[str, Any]] = {}
    for name, expected_sha256 in sorted(registered_results.items()):
        path = run_root / name
        if sha256_file(path) != expected_sha256:
            raise RuntimeError(f"qualification_result_file_hash_mismatch:{name}")
        result = load_verified(path, f"result_{path.stem}")
        request_id = result["schedule"]["request_id"]
        if request_id in result_by_request:
            raise RuntimeError("duplicate_qualification_request_result")
        scheduled_record = schedule_by_request.get(request_id)
        if scheduled_record is None:
            raise RuntimeError(
                f"qualification_result_is_not_scheduled:{request_id}"
            )
        # The result carries its own copy of the schedule record; it must be
        # the frozen one, not a rewritten one.
        if result["schedule"] != scheduled_record:
            raise RuntimeError(
                f"qualification_result_schedule_record_mismatch:{request_id}"
            )
        try:
            output_token_ids = decode_token_ids(
                result.get("output_token_ids_evidence") or {}
            )
        except ValueError as exc:
            raise RuntimeError(
                f"qualification_output_token_evidence_invalid:{request_id}:{exc}"
            ) from exc
        if len(output_token_ids) != result.get("usage", {}).get(
            "completion_tokens"
        ):
            raise RuntimeError(
                f"qualification_output_token_count_mismatch:{request_id}"
            )
        if (result.get("output_token_ids_evidence") or {}).get(
            "token_ids_sha256"
        ) != result.get("output_token_ids_sha256"):
            raise RuntimeError(
                f"qualification_output_token_hash_mismatch:{request_id}"
            )
        result_by_request[request_id] = result
    if len(result_by_request) != schedule["request_count"]:
        raise RuntimeError("qualification_result_file_count_mismatch")

    # Same rule as the run results: the postprocess manifest's registry is the
    # authority for which reports exist and what bytes they contain. A report
    # rewritten with a recomputed self-hash would otherwise be accepted here
    # while disagreeing with the frozen manifest.
    registered_reports = {
        str(item["path"]): str(item["sha256"])
        for item in postprocess_manifest.get("report_files") or []
    }
    if len(registered_reports) != schedule["request_count"]:
        raise RuntimeError(
            "qualification_postprocess_manifest_report_count_mismatch"
        )
    reports_on_disk = {
        path.name for path in postprocess_root.glob("[0-9][0-9][0-9].json")
    }
    if reports_on_disk != set(registered_reports):
        raise RuntimeError("qualification_postprocess_files_differ_from_manifest")
    postprocess_files = [
        postprocess_root / name for name in sorted(registered_reports)
    ]

    postprocess_by_request: dict[str, dict[str, Any]] = {}
    for name, expected_sha256 in sorted(registered_reports.items()):
        path = postprocess_root / name
        if sha256_file(path) != expected_sha256:
            raise RuntimeError(
                f"qualification_postprocess_file_hash_mismatch:{name}"
            )
        report = load_verified(path, f"postprocess_{path.stem}")
        request_id = report["request_id"]
        if request_id in postprocess_by_request:
            raise RuntimeError("duplicate_qualification_postprocess_result")

        # The report must be bound to the frozen schedule record and to the
        # exact result bytes it was derived from, or a posterior verdict could
        # be carried over from a different run.
        scheduled_record = schedule_by_request.get(request_id)
        if scheduled_record is None:
            raise RuntimeError(
                f"qualification_postprocess_is_not_scheduled:{request_id}"
            )
        for field in ("case_id", "arm", "schedule_ordinal"):
            if report.get(field) != scheduled_record.get(field):
                raise RuntimeError(
                    f"qualification_postprocess_{field}_mismatch:{request_id}"
                )
        source_result = result_by_request.get(request_id)
        if source_result is None:
            raise RuntimeError(
                f"qualification_postprocess_has_no_result:{request_id}"
            )
        if report.get("source_result_content_sha256") != source_result.get(
            "content_sha256"
        ):
            raise RuntimeError(
                f"qualification_postprocess_source_result_mismatch:{request_id}"
            )
        postprocess_by_request[request_id] = report
    if len(postprocess_by_request) != schedule["request_count"]:
        raise RuntimeError("qualification_postprocess_result_count_mismatch")

    blocks: dict[int, dict[str, dict[str, Any]]] = {}
    for record in schedule["records"]:
        result = result_by_request.get(record["request_id"])
        if result is None:
            raise RuntimeError(f"missing_qualification_result:{record['request_id']}")
        blocks.setdefault(record["block_ordinal"], {})[record["arm"]] = result
    ga_checks = []
    for block_ordinal, arms in sorted(blocks.items()):
        if set(arms) != {"U", "G", "A"}:
            raise RuntimeError(f"qualification_block_is_incomplete:{block_ordinal}")
        for arm in ("G", "A"):
            if arms[arm]["parse_decision"] != "PASS":
                raise RuntimeError(f"qualification_{arm}_parse_failed:{block_ordinal}")
            if arms[arm].get("single_json_value_decision") != "PASS":
                raise RuntimeError(
                    f"qualification_{arm}_single_json_value_failed:{block_ordinal}"
                )
            if arms[arm]["schema_decision"] != "PASS":
                raise RuntimeError(f"qualification_{arm}_schema_failed:{block_ordinal}")
            if arms[arm]["termination_decision"] != "COMPLETE":
                raise RuntimeError(
                    f"qualification_{arm}_termination_failed:{block_ordinal}"
                )
        equal = arms["G"]["output_sha256"] == arms["A"]["output_sha256"]
        if not equal:
            raise RuntimeError(f"qualification_ga_output_mismatch:{block_ordinal}")
        posterior_g = postprocess_by_request[
            arms["G"]["schedule"]["request_id"]
        ]
        posterior_a = postprocess_by_request[
            arms["A"]["schedule"]["request_id"]
        ]
        posterior_fields = (
            "materialization_decision",
            "xsd_decision",
            "selection_obligation_decision",
            "artifact_profile_decision",
            "independent_decision",
            "end_to_end_structural_decision",
        )
        posterior_equal = all(
            posterior_g.get(field_name) == posterior_a.get(field_name)
            for field_name in posterior_fields
        )
        if not posterior_equal:
            raise RuntimeError(
                f"qualification_ga_posterior_mismatch:{block_ordinal}"
            )
        ga_checks.append(
            {
                "block_ordinal": block_ordinal,
                "case_id": arms["G"]["schedule"]["case_id"],
                "output_sha256_equal": equal,
                "parse_decision_equal": (
                    arms["G"]["parse_decision"] == arms["A"]["parse_decision"]
                ),
                "schema_decision_equal": (
                    arms["G"]["schema_decision"]
                    == arms["A"]["schema_decision"]
                ),
                "posterior_decisions_equal": posterior_equal,
            }
        )

    audit_files = sorted(audit_root.glob("structured-output-audit-*.ndjson"))
    if not audit_files:
        raise RuntimeError("qualification_audit_file_missing")
    audit_records = [
        json.loads(line)
        for path in audit_files
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    expected_audit_ids = [
        record["audit_request_id"]
        for record in schedule["records"]
        if record["arm"] == "A"
    ]
    audit_verification = load_audit_verifier(audit_verifier_path)(
        audit_records,
        expected_external_request_ids=expected_audit_ids,
    )
    if audit_verification.get("status") != "PASS":
        raise RuntimeError("qualification_audit_verification_failed")
    binding = audit_verification.get("binding") or {}
    if int(binding.get("steps_observed") or 0) <= 0:
        raise RuntimeError("qualification_binding_has_no_evaluable_steps")

    expected_context = {
        "experiment_id": contract["experiment_id"],
        "runtime_fingerprint_sha256": contract["runtime_fingerprint_sha256"],
        "protocol_sha256": contract["protocol_file_sha256"],
        "asset_manifest_sha256": contract["assets_manifest_content_sha256"],
    }
    start_metadata = {
        record["request_id"]: record["event"].get("metadata") or {}
        for record in audit_records
        if record.get("event", {}).get("event_type") == "request_start"
    }
    end_events = {
        record["request_id"]: record["event"]
        for record in audit_records
        if record.get("event", {}).get("event_type") == "request_end"
    }
    schedule_by_audit_id = {
        record["audit_request_id"]: record
        for record in schedule["records"]
        if record["arm"] == "A"
    }
    external_to_internal = audit_verification.get(
        "external_request_id_to_internal_request_id"
    ) or {}
    for request_id in expected_audit_ids:
        internal_request_id = external_to_internal.get(request_id)
        if not internal_request_id:
            raise RuntimeError(
                f"qualification_audit_external_identity_missing:{request_id}"
            )
        metadata = start_metadata.get(internal_request_id)
        if metadata is None:
            raise RuntimeError(f"qualification_audit_start_missing:{request_id}")
        for field_name, expected in expected_context.items():
            if metadata.get(field_name) != expected:
                raise RuntimeError(
                    f"qualification_audit_context_mismatch:{request_id}:{field_name}"
                )
        schedule_record = schedule_by_audit_id[request_id]
        if metadata.get("prompt_token_count") != schedule_record.get(
            "prompt_token_count"
        ):
            raise RuntimeError(
                f"qualification_audit_prompt_count_mismatch:{request_id}"
            )
        if metadata.get("prompt_token_ids_sha256") != schedule_record.get(
            "prompt_token_ids_sha256"
        ):
            raise RuntimeError(
                f"qualification_audit_prompt_hash_mismatch:{request_id}"
            )
        result = result_by_request[schedule_record["request_id"]]
        if end_events.get(internal_request_id, {}).get(
            "output_token_ids_sha256"
        ) != result.get("output_token_ids_sha256"):
            raise RuntimeError(
                f"qualification_audit_output_hash_mismatch:{request_id}"
            )
        if end_events.get(internal_request_id, {}).get(
            "finish_reason"
        ) != "FINISHED_STOPPED":
            raise RuntimeError(
                f"qualification_audit_finish_reason_mismatch:{request_id}"
            )
        if end_events.get(internal_request_id, {}).get(
            "grammar_terminated"
        ) is not True:
            raise RuntimeError(
                f"qualification_audit_grammar_not_terminated:{request_id}"
            )

    manifest: dict[str, Any] = {
        "schema_version": "atlas.vllm.uga.qualification_result.v2",
        "decision": "PASS",
        "external_model_request_count": schedule["request_count"],
        "paper_result_admissible": False,
        "contract_file_sha256": sha256_file(contract_path),
        "contract_content_sha256": contract["content_sha256"],
        "qualified_protocol_file_sha256": contract["protocol_file_sha256"],
        "qualified_runtime_fingerprint_sha256": contract[
            "runtime_fingerprint_sha256"
        ],
        "qualified_overlay_manifest_content_sha256": contract[
            "overlay_manifest_content_sha256"
        ],
        "qualified_assets_manifest_content_sha256": contract[
            "assets_manifest_content_sha256"
        ],
        "qualified_model_tree_content_sha256": contract[
            "model_tree_content_sha256"
        ],
        "qualified_model_path": contract["model_path"],
        "qualified_max_model_len": contract["max_model_len"],
        "qualified_max_output_tokens": contract["max_output_tokens"],
        "qualified_xgrammar_regression_content_sha256": contract[
            "xgrammar_regression_content_sha256"
        ],
        "qualified_detokenization_regression_content_sha256": contract[
            "detokenization_regression_content_sha256"
        ],
        "qualified_nccl_regression_content_sha256": contract[
            "nccl_regression_content_sha256"
        ],
        "schedule_file_sha256": sha256_file(schedule_path),
        "schedule_content_sha256": schedule["content_sha256"],
        "run_manifest_file_sha256": sha256_file(run_root / "RUN_MANIFEST.json"),
        "run_manifest_content_sha256": run_manifest["content_sha256"],
        "postprocess_manifest_file_sha256": sha256_file(
            postprocess_root / "POSTPROCESS_MANIFEST.json"
        ),
        "postprocess_manifest_content_sha256": postprocess_manifest[
            "content_sha256"
        ],
        "result_files": [
            {"path": path.name, "sha256": sha256_file(path)}
            for path in result_files
        ],
        "audit_files": [
            {"path": path.name, "sha256": sha256_file(path)}
            for path in audit_files
        ],
        "audit_verifier_file_sha256": sha256_file(audit_verifier_path),
        "qualification_verifier_file_sha256": sha256_file(Path(__file__)),
        "postprocess_files": [
            {"path": path.name, "sha256": sha256_file(path)}
            for path in postprocess_files
        ],
        "ga_equivalence": ga_checks,
        "audit_verification": audit_verification,
    }
    manifest["content_sha256"] = canonical_sha256(manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--schedule", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--audit-root", type=Path, required=True)
    parser.add_argument("--postprocess-root", type=Path, required=True)
    parser.add_argument("--audit-verifier", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output_path = args.output.resolve()
    exit_code = 0
    try:
        manifest = verify_qualification(
            contract_path=args.contract.resolve(),
            schedule_path=args.schedule.resolve(),
            run_root=args.run_root.resolve(),
            audit_root=args.audit_root.resolve(),
            postprocess_root=args.postprocess_root.resolve(),
            audit_verifier_path=args.audit_verifier.resolve(),
        )
    except Exception as exc:
        input_paths = {
            "contract": args.contract.resolve(),
            "schedule": args.schedule.resolve(),
            "audit_verifier": args.audit_verifier.resolve(),
        }
        manifest = {
            "schema_version": "atlas.vllm.uga.qualification_result.v2",
            "decision": "FAIL",
            "paper_result_admissible": False,
            "verification_completed": False,
            "error_type": type(exc).__name__,
            "error_code": str(exc),
            "input_file_sha256": {
                name: sha256_file(path) if path.is_file() else None
                for name, path in input_paths.items()
            },
            "run_root": str(args.run_root.resolve()),
            "audit_root": str(args.audit_root.resolve()),
            "postprocess_root": str(args.postprocess_root.resolve()),
        }
        manifest["content_sha256"] = canonical_sha256(manifest)
        exit_code = 2
    atomic_write_json(output_path, manifest)
    print(
        json.dumps(
            {
                "decision": manifest["decision"],
                "content_sha256": manifest["content_sha256"],
                "binding": (manifest.get("audit_verification") or {}).get(
                    "binding"
                ),
            },
            sort_keys=True,
        )
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
