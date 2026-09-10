"""Readiness-gated, resumable runner for the 720-unit PIL V4 replication."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pil_v4_arms
import pil_v4_contract as contract
import pil_v4_provider
import pil_v4_schedule as schedule_module

ROOT = Path(__file__).resolve().parent
RUN_VERSION = "atlas.pil.formal_run.v4.1"
PAID_CONFIRMATION = contract.PAID_CONFIRMATION


def _resolve(manifest_path: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else manifest_path.parent / path


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _load_cases(path: Path) -> dict[Any, dict[str, Any]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return {row["id"]: row for row in rows}


def _assert_provider_identity(client: Any, readiness: dict[str, Any]) -> dict[str, Any]:
    expected = dict(readiness.get("provider_contract") or {})
    actual_metadata = dict(getattr(client, "runtime_metadata", {}) or {})
    actual = {key: actual_metadata.get(key) for key in expected}
    if not expected or actual != expected:
        raise ValueError("configured provider protocol differs from formal readiness")
    endpoint = str(getattr(getattr(client, "config", None), "llm_api_url", "") or "")
    expected_endpoint_hash = str(
        (readiness.get("authorization") or {}).get("api_base_sha256") or ""
    )
    if not endpoint or _sha256_text(endpoint) != expected_endpoint_hash:
        raise ValueError("configured API base differs from formal authorization")
    return actual_metadata


def _read_prior(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    document = json.loads(path.read_text(encoding="utf-8"))
    declared = document.get("content_sha256")
    body = {k: v for k, v in document.items() if k not in {"content_sha256", "created_at_utc"}}
    if declared != contract.canonical_sha256(body):
        raise ValueError("prior run manifest content hash mismatch")
    return document


def _write_json_atomic(path: Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    payload = json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _sum_usage(usages: list[dict[str, Any]]) -> dict[str, int]:
    totals = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    for usage in usages:
        for key in totals:
            totals[key] += int(usage.get(key) or 0)
    return totals


def _manifest(
    schedule: dict[str, Any],
    ledger: schedule_module.RunLedger,
    *,
    readiness_path: Path,
    output: Path,
) -> dict[str, Any]:
    pending = ledger.pending(schedule)
    attempt_count = ledger.attempt_count
    complete = not pending and ledger.line_count == int(schedule["unit_count"])
    completed_logical_requests = sum(
        int((entry.get("row") or {}).get("logical_request_count") or 0)
        for entry in ledger.completed.values()
    )
    completed_transport_requests = sum(
        int((entry.get("row") or {}).get("transport_request_count") or 0)
        for entry in ledger.completed.values()
    )
    failed_logical_requests = sum(
        int(entry.get("logical_requests_observed") or 0)
        for entry in ledger.attempt_records
    )
    failed_transport_requests = sum(
        int(entry.get("transport_requests_observed") or 0)
        for entry in ledger.attempt_records
    )
    completed_usage = _sum_usage([
        (entry.get("row") or {}).get("usage") or {}
        for entry in ledger.completed.values()
    ])
    failed_usage_records: list[dict[str, Any]] = []
    for entry in ledger.attempt_records:
        failed_usage_records.extend(
            (stage.get("usage") or {})
            for stage in (entry.get("completed_stages") or [])
        )
        failed_usage_records.append(entry.get("usage") or {})
    failed_usage = _sum_usage(failed_usage_records)
    total_usage = {
        key: completed_usage[key] + failed_usage[key]
        for key in completed_usage
    }
    body = {
        "schema_version": RUN_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "schedule_sha256": schedule["content_sha256"],
        "readiness_manifest_sha256": contract.sha256_file(readiness_path),
        "contract_version": contract.CONTRACT_VERSION,
        "contract_sha256": contract.contract_sha256(),
        "ledger_file": str(ledger.path),
        "ledger_line_count": ledger.line_count,
        "ledger_chain_head_sha256": ledger.chain_head,
        "attempt_journal_file": str(ledger.attempt_path),
        "attempt_journal_count": attempt_count,
        "attempt_journal_head_sha256": ledger.attempt_head,
        "request_accounting": {
            "logical_completed_units": completed_logical_requests,
            "logical_infrastructure_failed_attempts": failed_logical_requests,
            "logical_requests_observed_total": completed_logical_requests + failed_logical_requests,
            "transport_completed_units": completed_transport_requests,
            "transport_infrastructure_failed_attempts": failed_transport_requests,
            "transport_requests_observed_total": completed_transport_requests + failed_transport_requests,
            "external_call_count_field_semantics": "logical model requests, not transport retries",
        },
        "token_accounting": {
            "completed_units": completed_usage,
            "infrastructure_failed_attempts": failed_usage,
            "observed_total": total_usage,
            "source": "provider response usage fields; transport failures without a response contribute zero tokens",
        },
        "unresolved_infrastructure_failed_units": ledger.failed_unit_ids(),
        "units_total": schedule["unit_count"],
        "units_pending": len(pending),
        "run_complete": complete,
        "promotable": complete,
        "provenance": dict(ledger.provenance),
        "external_result_selection": "none; every completed unit retained",
        "output_path": str(output),
    }
    return {**body, "content_sha256": contract.canonical_sha256({k: v for k, v in body.items() if k != "created_at_utc"})}


@contextlib.contextmanager
def exclusive_lock(schedule: dict[str, Any], ledger_path: Path):
    lock = ROOT / f"{schedule['content_sha256']}.pil-v41-run.lock"
    try:
        handle = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise ValueError(f"another PIL V4.1 runner holds {lock}") from None
    os.write(handle, json.dumps({
        "pid": os.getpid(), "ledger": str(ledger_path),
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
    }).encode("utf-8"))
    os.close(handle)
    try:
        yield
    finally:
        try:
            lock.unlink()
        except FileNotFoundError:
            pass


def plan(readiness: Path, schedule_path: Path, ledger_path: Path) -> dict[str, Any]:
    blockers = schedule_module.readiness_blockers(readiness)
    result: dict[str, Any] = {
        "readiness": str(readiness),
        "readiness_status": "BLOCKED" if blockers else "READY",
        "blockers": blockers,
        "external_calls_made": 0,
    }
    if blockers:
        return result
    if not schedule_path.is_file():
        return {**result, "readiness_status": "READY_NO_SCHEDULE", "blockers": ["formal schedule has not been generated"]}
    schedule = json.loads(schedule_path.read_text(encoding="utf-8"))
    schedule_module.verify_schedule(schedule, readiness)
    ledger = schedule_module.RunLedger(ledger_path, schedule)
    return {
        **result,
        "schedule": str(schedule_path),
        "schedule_sha256": schedule["content_sha256"],
        "units_total": schedule["unit_count"],
        "units_completed": ledger.line_count,
        "units_pending": len(ledger.pending(schedule)),
        "unresolved_infrastructure_failed_units": ledger.failed_unit_ids(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--readiness", type=Path, default=ROOT / "PIL_V41_FORMAL_READINESS.json")
    parser.add_argument("--schedule", type=Path, default=ROOT / "PIL_V41_FORMAL_SCHEDULE.json")
    parser.add_argument("--ledger", type=Path, default=ROOT / "PIL_V41_RUN_LEDGER.jsonl")
    parser.add_argument("--output", type=Path, default=ROOT / "PIL_V41_RUN_MANIFEST.json")
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--confirm-paid-run", default="")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument(
        "--retry-failed-unit", action="append", default=[], metavar="UNIT_ID",
        help=(
            "Explicitly permit retrying one previously failed unit. Repeat the option "
            "for more than one unit; no failed unit is retried by default."
        ),
    )
    args = parser.parse_args(argv)

    if args.plan_only:
        print(json.dumps(plan(args.readiness, args.schedule, args.ledger), ensure_ascii=False, indent=2))
        return 0
    if not args.execute:
        raise SystemExit("No calls are made by default. Use --plan-only or explicitly pass --execute.")
    if args.confirm_paid_run != PAID_CONFIRMATION:
        raise SystemExit(f"Paid execution requires --confirm-paid-run {PAID_CONFIRMATION}")

    readiness = schedule_module.verify_readiness(args.readiness)
    schedule = json.loads(args.schedule.read_text(encoding="utf-8"))
    schedule_module.verify_schedule(schedule, args.readiness)
    dataset = _resolve(args.readiness, readiness["inputs"]["inference_dataset"]["path"])
    knowledge = _resolve(args.readiness, readiness["inputs"]["knowledge_base"]["path"])
    cases = _load_cases(dataset)

    # Credentials are read and the transport is created only after every no-call gate.
    from pil_v4_client import UnifiedV4Client

    with exclusive_lock(schedule, args.ledger):
        base_client = pil_v4_provider.create_experiment_client()
        client = UnifiedV4Client(base_client)
        runtime_metadata = _assert_provider_identity(client, readiness)
        endpoint = str(getattr(getattr(base_client, "config", None), "llm_api_url", ""))
        provenance = {
            "model_name": str(getattr(getattr(base_client, "config", None), "model_name", "UNKNOWN")),
            "api_base_sha256": _sha256_text(endpoint) if endpoint else None,
            "client_runtime_sha256": contract.canonical_sha256(runtime_metadata),
        }
        prior = _read_prior(args.output)
        ledger = schedule_module.RunLedger(args.ledger, schedule, provenance=provenance, prior_manifest=prior)
        context = pil_v4_arms.ArmContext.load(knowledge_base=knowledge)
        unit_runner = pil_v4_arms.make_run_unit(client, context)
        executed = 0
        retry_authorizations = set(args.retry_failed_unit)
        previously_failed_units = set(ledger.failed_unit_ids())
        try:
            for unit in ledger.pending(schedule):
                if args.limit is not None and executed >= args.limit:
                    break
                unit_id = str(unit["unit_id"])
                if unit_id in previously_failed_units and unit_id not in retry_authorizations:
                    raise RuntimeError(
                        f"unit {unit_id} already incurred an infrastructure-failed request; "
                        f"retry is blocked unless --retry-failed-unit {unit_id} is supplied"
                    )
                try:
                    row = unit_runner(unit, cases[unit["case_id"]])
                except Exception as error:
                    # Only failures that returned no usable model result escape
                    # the arm; they stay pending and are journalled for billing.
                    ledger.record_attempt(unit, error)
                    _write_json_atomic(args.output, _manifest(schedule, ledger, readiness_path=args.readiness, output=args.output))
                    raise
                ledger.record(unit, row)
                executed += 1
                _write_json_atomic(args.output, _manifest(schedule, ledger, readiness_path=args.readiness, output=args.output))
        finally:
            manifest = _manifest(schedule, ledger, readiness_path=args.readiness, output=args.output)
            _write_json_atomic(args.output, manifest)

    print(json.dumps({
        "output": str(args.output),
        "ledger": str(args.ledger),
        "executed_now": executed,
        "completed": ledger.line_count,
        "pending": len(ledger.pending(schedule)),
        "promotable": manifest["promotable"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
