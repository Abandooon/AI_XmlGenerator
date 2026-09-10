"""Readiness-gated 720-unit schedule and append-only ledger for PIL V4."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pil_v4_contract as contract
import pil_v4_arms
from pil_v4_client import COMMON_SYSTEM_INSTRUCTIONS
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent
SCHEDULE_VERSION = "atlas.pil.formal_schedule.v4.1"
LEDGER_VERSION = "atlas.pil.run_ledger.v4.1"
ATTEMPT_VERSION = "atlas.pil.attempt_journal.v4.1"
REPLICATES = 3
INTERLEAVE_SEED = "atlas.pil.v4.1.interleave.2026-09"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _resolve(manifest_path: Path, value: str | None) -> Path:
    if not value:
        raise ValueError("readiness input path is not set")
    path = Path(value)
    return path if path.is_absolute() else manifest_path.parent / path


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def readiness_blockers(path: Path, *, require_execution_authorization: bool = True) -> list[str]:
    if not path.is_file():
        return [f"readiness manifest missing: {path}"]
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"readiness manifest unreadable: {type(error).__name__}"]
    blockers: list[str] = []
    expected_schema_version = (
        "atlas.pil.formal_readiness.v4.1"
        if require_execution_authorization
        else "atlas.pil.prepaid_readiness.v4.1"
    )
    if manifest.get("schema_version") != expected_schema_version:
        blockers.append(f"schema_version is not {expected_schema_version}")
    declared_content_sha256 = manifest.get("content_sha256")
    stable_content = {
        key: value
        for key, value in manifest.items()
        if key not in {"created_at_utc", "content_sha256"}
    }
    if declared_content_sha256 != contract.canonical_sha256(stable_content):
        blockers.append("readiness manifest content hash mismatch")
    allowed_statuses = {"READY_FOR_FORMAL_RUN"} if require_execution_authorization else {
        "READY_FOR_PAID_AUTHORIZATION", "READY_FOR_FORMAL_RUN",
    }
    if manifest.get("status") not in allowed_statuses:
        blockers.append("status is not an accepted readiness state")
    if require_execution_authorization:
        if manifest.get("formal_run_enabled") is not True:
            blockers.append("formal_run_enabled is not true")
        if manifest.get("external_calls_authorized") is not True:
            blockers.append("external_calls_authorized is not true")
    review = manifest.get("review") or {}
    for key in (
        "reviewer_1_locked", "reviewer_2_locked", "consensus_complete",
        "affected_cases_reconfirmed_after_fact_edits",
    ):
        if review.get(key) is not True:
            blockers.append(f"review.{key} is not true")
    for key in (
        "agreement_report_sha256", "adjudication_record_sha256",
        "d1_acceptance_sha256",
    ):
        if not review.get(key):
            blockers.append(f"review.{key} is missing")
    checks = manifest.get("required_checks") or {}
    for key in (
        "inference_dataset_contains_no_gold", "knowledge_base_checked_against_eur_lex",
        "article_29_30_31_distinguished", "case_count_is_60",
        "gold_case_ids_match_dataset", "four_arm_schedule_is_720_units",
        "instrument_qualified_evidence_ids", "consensus_gold_schema_valid",
        "retrieval_required_evidence_coverage_complete", "dependency_clusters_declared",
        "implementation_files_hashed", "provider_contract_frozen",
        "autosar_v20_provider_parameters_matched", "runtime_environment_complete",
        "english_model_inputs_verified", "all_240_primary_prompts_are_english",
        "english_legal_source_audit_passed", "translation_parity_review_complete",
        "translation_review_workbook_hash_verified",
        "prepaid_code_audit_passed",
        "p1_p2_p3_prompt_text_is_identical",
        "rendered_prompt_artifact_matches_implementation",
        "offline_tests_pass",
    ):
        if checks.get(key) is not True:
            blockers.append(f"required_checks.{key} is not true")

    inputs = manifest.get("inputs") or {}
    resolved: dict[str, Path] = {}
    for key in (
        "inference_dataset", "consensus_gold", "knowledge_base", "decision_schema",
        "gold_schema", "delivery_rules",
        "autosar_v20_parameter_match",
        "english_input_manifest",
        "english_legal_source_audit",
        "translation_parity_acceptance",
        "rendered_prompts",
        "prepaid_code_audit",
    ):
        item = inputs.get(key) or {}
        try:
            resolved[key] = _resolve(path, item.get("path"))
        except ValueError:
            blockers.append(f"inputs.{key}.path is missing")
            continue
        if not resolved[key].is_file():
            blockers.append(f"inputs.{key} file is missing")
        elif item.get("sha256") != _sha256(resolved[key]):
            blockers.append(f"inputs.{key} hash does not match")

    implementation = manifest.get("implementation") or {}
    for key in (
        "preflight", "contract", "arms", "client", "provider", "schedule", "runner", "rescore",
        "authorizer", "prepaid_freezer", "prompt_renderer", "english_input_builder",
        "prepaid_audit",
    ):
        item = implementation.get(key) or {}
        try:
            file = _resolve(path, item.get("path"))
        except ValueError:
            blockers.append(f"implementation.{key}.path is missing")
            continue
        if not file.is_file():
            blockers.append(f"implementation.{key} file is missing")
        elif item.get("sha256") != _sha256(file):
            blockers.append(f"implementation.{key} hash does not match")

    if manifest.get("provider_contract") != contract.PROVIDER_PROTOCOL:
        blockers.append("provider contract does not match the frozen V4 protocol")
    if manifest.get("runtime_environment") != contract.runtime_environment():
        blockers.append("runtime environment differs from the frozen V4 environment")
    if require_execution_authorization:
        authorization = manifest.get("authorization") or {}
        if not authorization.get("api_base_sha256"):
            blockers.append("authorization.api_base_sha256 is missing")
        if authorization.get("authorized_unit_count") != 720:
            blockers.append("authorization.authorized_unit_count is not 720")
        if authorization.get("confirmation_token_sha256") != contract.canonical_sha256(
            contract.PAID_CONFIRMATION
        ):
            blockers.append("authorization confirmation token hash does not match V4.1")
        if manifest.get("provider_calls_before_authorization") != 0:
            blockers.append("provider_calls_before_authorization is not zero")
        if manifest.get("paid_api_calls_before_authorization") != 0:
            blockers.append("paid_api_calls_before_authorization is not zero")
        try:
            preflight_path = _resolve(path, authorization.get("preflight_path"))
        except ValueError:
            blockers.append("authorization.preflight_path is missing")
        else:
            if not preflight_path.is_file():
                blockers.append("authorization preflight file is missing")
            else:
                if authorization.get("preflight_file_sha256") != _sha256(preflight_path):
                    blockers.append("authorization preflight file hash does not match")
                try:
                    preflight_document = json.loads(preflight_path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    blockers.append("authorization preflight file is unreadable")
                else:
                    if authorization.get("preflight_content_sha256") != preflight_document.get(
                        "content_sha256"
                    ):
                        blockers.append("authorization preflight content hash does not match")

    if "inference_dataset" in resolved and resolved["inference_dataset"].is_file():
        try:
            cases = _jsonl(resolved["inference_dataset"])
        except Exception as error:
            blockers.append(f"inference dataset unreadable: {type(error).__name__}")
            cases = []
        if len(cases) != 60:
            blockers.append(f"inference dataset has {len(cases)} cases, expected 60")
        ids = [row.get("id") for row in cases]
        if len(set(ids)) != len(ids):
            blockers.append("inference dataset repeats case ids")
        forbidden = {"expected_output", "gold", "connecting_factors", "accepted_conclusions", "accepted_forum_types"}
        leaked = sorted({key for row in cases for key in forbidden if key in row})
        if leaked:
            blockers.append("inference dataset leaks evaluation fields: " + ",".join(leaked))
        if any(set(row) - {"id", "cluster_id", "facts_text", "source_class"} for row in cases):
            blockers.append("inference dataset contains fields outside its declared inference-only surface")
        if any(not row.get("cluster_id") for row in cases):
            blockers.append("inference dataset has a case without a dependence cluster")
    else:
        cases = []

    gold: list[dict[str, Any]] = []
    if "consensus_gold" in resolved and resolved["consensus_gold"].is_file():
        try:
            gold = _jsonl(resolved["consensus_gold"])
        except Exception as error:
            blockers.append(f"consensus gold unreadable: {type(error).__name__}")
            gold = []
        if len(gold) != 60:
            blockers.append(f"consensus gold has {len(gold)} cases, expected 60")
        if cases and {row.get("id") for row in gold} != {row.get("id") for row in cases}:
            blockers.append("consensus gold case ids do not match inference dataset")
        if len({row.get("id") for row in gold}) != len(gold):
            blockers.append("consensus gold repeats case ids")

        if "gold_schema" in resolved and resolved["gold_schema"].is_file():
            try:
                gold_schema = json.loads(resolved["gold_schema"].read_text(encoding="utf-8"))
                Draft202012Validator.check_schema(gold_schema)
                validator = Draft202012Validator(gold_schema)
                invalid = [row.get("id") for row in gold if not validator.is_valid(row)]
                if invalid:
                    blockers.append("consensus gold schema failures: " + ",".join(map(str, invalid)))
            except Exception as error:
                blockers.append(f"gold schema unreadable: {type(error).__name__}")

    if "knowledge_base" in resolved and resolved["knowledge_base"].is_file():
        try:
            kb = _jsonl(resolved["knowledge_base"])
            evidence_ids = [str(row.get("evidence_id") or "") for row in kb]
            if len(set(evidence_ids)) != len(evidence_ids) or any(":" not in item for item in evidence_ids):
                blockers.append("knowledge base evidence ids are not unique instrument-qualified identities")
            for evidence_id in (
                "BRUSSELS_I_BIS:Art.29(1)",
                "BRUSSELS_I_BIS:Art.30(1)",
                "BRUSSELS_I_BIS:Art.31(2)",
                "EU_TRADE_MARK_REGULATION:Art.63(1)",
            ):
                if evidence_id not in evidence_ids:
                    blockers.append(f"knowledge base lacks required distinct evidence {evidence_id}")
            if gold:
                known = set(evidence_ids)
                outside = sorted({
                    evidence
                    for row in gold
                    for evidence in (row.get("accepted_evidence") or [])
                    if evidence not in known
                })
                if outside:
                    blockers.append("gold cites evidence absent from knowledge base: " + ",".join(outside))
        except Exception as error:
            blockers.append(f"knowledge base unreadable: {type(error).__name__}")
    return blockers


def verify_readiness(path: Path) -> dict[str, Any]:
    blockers = readiness_blockers(path)
    if blockers:
        raise ValueError("PIL V4 formal run is blocked:\n- " + "\n- ".join(blockers))
    return json.loads(path.read_text(encoding="utf-8"))


def build_schedule(readiness_path: Path) -> dict[str, Any]:
    readiness = verify_readiness(readiness_path)
    dataset_path = _resolve(readiness_path, readiness["inputs"]["inference_dataset"]["path"])
    cases = _jsonl(dataset_path)
    knowledge_path = _resolve(readiness_path, readiness["inputs"]["knowledge_base"]["path"])
    context = pil_v4_arms.ArmContext.load(knowledge_base=knowledge_path)
    units = [
        {
            "unit_id": f"{case['id']}|{arm}|{replicate}",
            "case_id": case["id"],
            "cluster_id": case.get("cluster_id"),
            "arm": arm,
            "arm_name": contract.ARM_NAMES[arm],
            "replicate": replicate,
            "seed": contract.seed_for_replicate(replicate),
            "prompt_sha256": hashlib.sha256(
                pil_v4_arms.render_primary_prompt(
                    context, arm=arm, facts=str(case["facts_text"]),
                )[0].encode("utf-8")
            ).hexdigest(),
            "system_instructions_sha256": hashlib.sha256(
                COMMON_SYSTEM_INSTRUCTIONS.encode("utf-8")
            ).hexdigest(),
        }
        for case in cases
        for arm in contract.ARMS
        for replicate in range(1, REPLICATES + 1)
    ]
    units.sort(key=lambda unit: hashlib.sha256(
        f"{INTERLEAVE_SEED}|{unit['unit_id']}".encode("utf-8")
    ).hexdigest())
    body = {
        "schema_version": SCHEDULE_VERSION,
        "created_before_external_calls": True,
        "case_count": 60,
        "arms": list(contract.ARMS),
        "replicates": REPLICATES,
        "unit_count": len(units),
        "unit_order_policy": "sha256_interleave_fixed_seed",
        "interleave_seed_sha256": hashlib.sha256(INTERLEAVE_SEED.encode("utf-8")).hexdigest(),
        "selection_policy": "execute every unit once; never replace or repeat a completed unit",
        "inputs": {
            "readiness_manifest_sha256": _sha256(readiness_path),
            "inference_dataset_sha256": readiness["inputs"]["inference_dataset"]["sha256"],
            "consensus_gold_sha256": readiness["inputs"]["consensus_gold"]["sha256"],
            "knowledge_base_sha256": readiness["inputs"]["knowledge_base"]["sha256"],
            "decision_schema_sha256": readiness["inputs"]["decision_schema"]["sha256"],
            "gold_schema_sha256": readiness["inputs"]["gold_schema"]["sha256"],
            "delivery_rules_sha256": readiness["inputs"]["delivery_rules"]["sha256"],
            "autosar_v20_parameter_match_sha256": readiness["inputs"]["autosar_v20_parameter_match"]["sha256"],
            "english_input_manifest_sha256": readiness["inputs"]["english_input_manifest"]["sha256"],
            "english_legal_source_audit_sha256": readiness["inputs"]["english_legal_source_audit"]["sha256"],
            "translation_parity_acceptance_sha256": readiness["inputs"]["translation_parity_acceptance"]["sha256"],
            "rendered_prompts_sha256": readiness["inputs"]["rendered_prompts"]["sha256"],
            "prepaid_code_audit_sha256": readiness["inputs"]["prepaid_code_audit"]["sha256"],
            "contract_version": contract.CONTRACT_VERSION,
            "contract_sha256": contract.contract_sha256(),
        },
        "units": units,
    }
    if len(units) != 720:
        raise ValueError(f"formal schedule must contain 720 units, found {len(units)}")
    return {**body, "content_sha256": contract.canonical_sha256(body)}


def verify_schedule(schedule: dict[str, Any], readiness_path: Path) -> None:
    if schedule.get("schema_version") != SCHEDULE_VERSION:
        raise ValueError("unsupported PIL V4 schedule version")
    body = {key: value for key, value in schedule.items() if key != "content_sha256"}
    if schedule.get("content_sha256") != contract.canonical_sha256(body):
        raise ValueError("schedule content hash mismatch")
    expected = build_schedule(readiness_path)
    if schedule != expected:
        raise ValueError("schedule is not the exact 720-unit schedule implied by locked readiness inputs")


class LedgerIntegrityError(ValueError):
    pass


class RunLedger:
    def __init__(
        self,
        path: Path,
        schedule: dict[str, Any],
        *,
        provenance: dict[str, Any] | None = None,
        prior_manifest: dict[str, Any] | None = None,
    ) -> None:
        self.path = path
        self.attempt_path = path.with_name(path.name + ".attempts.jsonl")
        self.schedule_hash = str(schedule["content_sha256"])
        self.units = {str(unit["unit_id"]): unit for unit in schedule["units"]}
        self.provenance = dict(provenance or {})
        self.completed: dict[str, dict[str, Any]] = {}
        self.chain_head = self.schedule_hash
        self.line_count = 0
        self.attempt_head = self.schedule_hash
        self.attempt_count = 0
        self.attempt_records: list[dict[str, Any]] = []
        self.byte_size = path.stat().st_size if path.is_file() else 0
        if path.is_file():
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    self._admit(json.loads(line))
        self._load_attempts()
        if prior_manifest and prior_manifest.get("schedule_sha256") == self.schedule_hash:
            prior_count = int(prior_manifest.get("ledger_line_count") or 0)
            if self.line_count < prior_count:
                raise LedgerIntegrityError("ledger is shorter than the prior run manifest")
            if self.line_count == prior_count and prior_count and prior_manifest.get("ledger_chain_head_sha256") != self.chain_head:
                raise LedgerIntegrityError("ledger head differs from prior run manifest")
            prior_attempt_count = int(prior_manifest.get("attempt_journal_count") or 0)
            if self.attempt_count < prior_attempt_count:
                raise LedgerIntegrityError("attempt journal is shorter than the prior run manifest")
            if (
                self.attempt_count == prior_attempt_count
                and prior_attempt_count
                and prior_manifest.get("attempt_journal_head_sha256") != self.attempt_head
            ):
                raise LedgerIntegrityError("attempt journal head differs from prior run manifest")

    def _admit(self, entry: dict[str, Any]) -> None:
        key = str(entry.get("unit_id"))
        unit = self.units.get(key)
        if unit is None or key in self.completed:
            raise LedgerIntegrityError(f"unknown or repeated ledger unit {key}")
        if entry.get("schedule_sha256") != self.schedule_hash:
            raise LedgerIntegrityError("ledger belongs to another schedule")
        if entry.get("sequence") != self.line_count or entry.get("prev_sha256") != self.chain_head:
            raise LedgerIntegrityError("ledger sequence/hash chain is broken")
        digest = contract.canonical_sha256({k: v for k, v in entry.items() if k != "entry_sha256"})
        if entry.get("entry_sha256") != digest:
            raise LedgerIntegrityError("ledger entry content hash mismatch")
        for field in (
            "case_id", "arm", "replicate", "seed", "prompt_sha256",
            "system_instructions_sha256",
        ):
            if entry.get(field) != unit[field]:
                raise LedgerIntegrityError(f"ledger unit disagrees with schedule on {field}")
        row = entry.get("row")
        if not isinstance(row, dict):
            raise LedgerIntegrityError("ledger entry carries no result row")
        for field, expected in (
            ("unit_id", key), ("id", unit["case_id"]),
            ("mode", unit["arm"]), ("replicate", unit["replicate"]),
            ("seed", unit["seed"]),
            ("prompt_sha256", unit["prompt_sha256"]),
            ("system_instructions_sha256", unit["system_instructions_sha256"]),
        ):
            if row.get(field) != expected:
                raise LedgerIntegrityError(f"ledger result row disagrees on {field}")
        for key_name, value in (entry.get("provenance") or {}).items():
            self.provenance.setdefault(key_name, value)
        for key_name, value in self.provenance.items():
            if (entry.get("provenance") or {}).get(key_name) != value:
                raise LedgerIntegrityError(f"ledger mixes provenance value {key_name}")
        self.completed[key] = entry
        self.chain_head = digest
        self.line_count += 1

    def pending(self, schedule: dict[str, Any]) -> list[dict[str, Any]]:
        return [unit for unit in schedule["units"] if str(unit["unit_id"]) not in self.completed]

    def failed_unit_ids(self) -> list[str]:
        """Return unresolved units that have already incurred a failed request."""
        return sorted({
            str(record["unit_id"])
            for record in self.attempt_records
            if str(record["unit_id"]) not in self.completed
        })

    def record(self, unit: dict[str, Any], row: dict[str, Any]) -> None:
        key = str(unit["unit_id"])
        if key in self.completed:
            raise LedgerIntegrityError(f"completed unit {key} cannot be rerun")
        observed = self.path.stat().st_size if self.path.is_file() else 0
        if observed != self.byte_size:
            raise LedgerIntegrityError("ledger changed underneath this runner")
        stamped = {
            **row,
            "unit_id": key,
            "id": unit["case_id"],
            "mode": unit["arm"],
            "replicate": unit["replicate"],
            "seed": unit["seed"],
            "prompt_sha256": unit["prompt_sha256"],
            "system_instructions_sha256": unit["system_instructions_sha256"],
        }
        body = {
            "schema_version": LEDGER_VERSION,
            "schedule_sha256": self.schedule_hash,
            "sequence": self.line_count,
            "prev_sha256": self.chain_head,
            "unit_id": key,
            "case_id": unit["case_id"],
            "arm": unit["arm"],
            "replicate": unit["replicate"],
            "seed": unit["seed"],
            "prompt_sha256": unit["prompt_sha256"],
            "system_instructions_sha256": unit["system_instructions_sha256"],
            "completed_at_utc": datetime.now(timezone.utc).isoformat(),
            "provenance": dict(self.provenance),
            "row": stamped,
        }
        entry = {**body, "entry_sha256": contract.canonical_sha256(body)}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        self.completed[key] = entry
        self.chain_head = entry["entry_sha256"]
        self.line_count += 1
        self.byte_size = self.path.stat().st_size

    def _load_attempts(self) -> None:
        prior = self.schedule_hash
        count = 0
        if self.attempt_path.is_file():
            for line in self.attempt_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                record = json.loads(line)
                if record.get("prev_sha256") != prior:
                    raise LedgerIntegrityError("attempt journal chain is broken")
                digest = contract.canonical_sha256({k: v for k, v in record.items() if k != "attempt_sha256"})
                if record.get("attempt_sha256") != digest:
                    raise LedgerIntegrityError("attempt journal entry was edited")
                unit = self.units.get(str(record.get("unit_id")))
                if unit is None or record.get("schedule_sha256") != self.schedule_hash:
                    raise LedgerIntegrityError("attempt journal belongs to another schedule or unit")
                for field in (
                    "case_id", "arm", "replicate", "seed", "prompt_sha256",
                    "system_instructions_sha256",
                ):
                    if record.get(field) != unit[field]:
                        raise LedgerIntegrityError(f"attempt journal disagrees with schedule on {field}")
                prior = digest
                count += 1
                self.attempt_records.append(record)
        self.attempt_head = prior
        self.attempt_count = count
        self.attempt_byte_size = self.attempt_path.stat().st_size if self.attempt_path.is_file() else 0

    def record_attempt(self, unit: dict[str, Any], error: BaseException) -> None:
        observed = self.attempt_path.stat().st_size if self.attempt_path.is_file() else 0
        if observed != self.attempt_byte_size:
            raise LedgerIntegrityError("attempt journal changed underneath this runner")
        body = {
            "schema_version": ATTEMPT_VERSION,
            "schedule_sha256": self.schedule_hash,
            "sequence": self.attempt_count,
            "prev_sha256": self.attempt_head,
            "unit_id": unit["unit_id"],
            "case_id": unit["case_id"],
            "arm": unit["arm"],
            "replicate": unit["replicate"],
            "seed": unit["seed"],
            "prompt_sha256": unit["prompt_sha256"],
            "system_instructions_sha256": unit["system_instructions_sha256"],
            "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
            "failure_class": "infrastructure",
            "error_type": type(error).__name__,
            "message": str(error),
            "failed_stage": getattr(error, "failed_stage", None),
            "completed_stages": list(getattr(error, "completed_stages", []) or []),
            "failed_prompt": getattr(error, "failed_prompt", None),
            "failed_prompt_sha256": getattr(error, "failed_prompt_sha256", None),
            "transport_attempts": list(getattr(error, "transport_attempts", []) or []),
            "provider_response": dict(getattr(error, "provider_response", {}) or {}),
            "usage": dict(getattr(error, "usage", {}) or {}),
            "logical_requests_observed": int(
                getattr(error, "logical_requests_observed", 1) or 1
            ),
            "transport_requests_observed": sum(
                len(list(stage.get("transport_attempts") or []))
                for stage in list(getattr(error, "completed_stages", []) or [])
            ) + len(list(getattr(error, "transport_attempts", []) or [])),
            "unit_recorded": False,
        }
        record = {**body, "attempt_sha256": contract.canonical_sha256(body)}
        self.attempt_path.parent.mkdir(parents=True, exist_ok=True)
        with self.attempt_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        self.attempt_head = record["attempt_sha256"]
        self.attempt_count += 1
        self.attempt_records.append(record)
        self.attempt_byte_size = self.attempt_path.stat().st_size


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--readiness", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    schedule = build_schedule(args.readiness)
    if args.output.exists():
        raise ValueError(f"refusing to overwrite existing formal schedule: {args.output}")
    args.output.write_text(json.dumps(schedule, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "units": schedule["unit_count"], "sha256": schedule["content_sha256"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
