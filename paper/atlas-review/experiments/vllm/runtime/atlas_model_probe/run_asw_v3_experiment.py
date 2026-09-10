"""Resumable paper experiment orchestrator for the ASW V3 Phase 1/2 chain.

The script never reads or prints credentials. The child pipeline process owns
its normal runtime credential loading. Existing non-complete run directories
are never overwritten.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from lxml import etree

from evaluate_asw_v3_run import evaluate
from experiment_runtime import (
    atomic_write_json,
    atomic_write_text,
    child_state_path,
    exclusive_experiment_lock,
    recover_orphaned_child,
    reserve_attempt,
    run_child_process,
    utc_now,
)
from experiment_freeze import (
    DEFAULT_FREEZE_MANIFEST,
    ExperimentFreezeError,
    verify_freeze_manifest,
)
from delivery_classification import (
    AMBIGUOUS_PROVIDER_DELIVERY,
    COMPLETION_KINDS,
    MODEL_OR_SCHEMA_GENERATION_FAILURE,
    classify_delivery,
    completion_kind_for,
)

# Every kind that is not a produced artifact.  Kept as a name so a future kind
# is admitted by the reader without another edit here.
NON_SUCCESS_COMPLETION_KINDS = frozenset(
    kind for kind in COMPLETION_KINDS if kind != "SUCCESSFUL_ARTIFACT"
)

ROOT = Path(__file__).resolve().parent
RENDERED_MANIFEST = (
    Path(r"E:\54239\Documents\atlas_autosar_requirements_v3")
    / "rendered/run_manifest.json"
)
FORMAL_CONTRACT = ROOT / "FORMAL_EXPERIMENT_CONTRACT.json"
RUNNER = ROOT / "run_phase12_case.py"
NS = {"ar": "http://autosar.org/schema/r4.0"}
SUCCESS_STATUSES = {"COMPLETE", "RESUMED_COMPLETE"}
# A terminated slot now carries the completion kind as its status, so the
# terminal set is derived from the frozen vocabulary rather than from one
# hard-coded name.  "TERMINAL_FAILURE" is retained only so an archived pilot
# ledger still parses; nothing writes it any more.
FAILURE_STATUSES = {
    "TERMINAL_FAILURE",
    "RESUMED_TERMINAL_FAILURE",
    *(kind for kind in COMPLETION_KINDS if kind != "SUCCESSFUL_ARTIFACT"),
}
TERMINAL_STATUSES = SUCCESS_STATUSES | FAILURE_STATUSES


def formal_models() -> list[str]:
    """Return the ordered model cohort from the only formal source of truth."""

    contract = json.loads(FORMAL_CONTRACT.read_text(encoding="utf-8"))
    models = list(contract.get("models") or [])
    if models != ["gpt-5.6-luna"]:
        raise ValueError("formal experiment contract must contain Luna only")
    return models


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json_object(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _read_provider_call_audit(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            return []
        if not isinstance(item, dict) or item.get("credentials_included") is not False:
            return []
        usage = item.get("usage") or {}
        if any(
            not isinstance(usage.get(key), int) or int(usage[key]) < 0
            for key in ("input_tokens", "output_tokens", "total_tokens")
        ):
            return []
        records.append(item)
    return records


def build_schedule(
    models: list[str],
    repair_mode: str,
    freeze_manifest: Path = DEFAULT_FREEZE_MANIFEST,
) -> dict[str, Any]:
    freeze = verify_freeze_manifest(freeze_manifest)
    contract = json.loads(FORMAL_CONTRACT.read_text(encoding="utf-8"))
    expected_models = list(contract["models"])
    expected_repair_mode = str(contract["generation"]["repair_mode"])
    if models != expected_models:
        raise ValueError(
            "formal schedule models must exactly match the frozen contract order"
        )
    if repair_mode != expected_repair_mode:
        raise ValueError("formal schedule repair mode must match the frozen contract")
    rendered = json.loads(RENDERED_MANIFEST.read_text(encoding="utf-8"))
    if rendered.get("validation", {}).get("status") != "PASS":
        raise ValueError("rendered requirement manifest is not valid")
    prompt_records = {
        item["case_id"]: item for item in rendered.get("prompts") or []
    }
    requirement_contract = contract["requirement_set"]
    expected_seeds = list(requirement_contract["seeds"])
    source_runs = list(rendered["runs"])
    observed_case_ids = {item["case_id"] for item in source_runs}
    if len(observed_case_ids) != int(requirement_contract["case_count"]):
        raise ValueError("rendered case count differs from the frozen contract")
    for case_id in sorted(observed_case_ids):
        case_runs = [item for item in source_runs if item["case_id"] == case_id]
        if len(case_runs) != int(requirement_contract["repetitions_per_case"]):
            raise ValueError(f"rendered repetition count differs for {case_id}")
        if [item["seed"] for item in case_runs] != expected_seeds:
            raise ValueError(f"rendered seed order differs for {case_id}")
    runs = []
    for model in models:
        for source_run in source_runs:
            prompt_record = prompt_records.get(source_run["case_id"])
            if prompt_record is None:
                raise ValueError(
                    f"missing rendered prompt identity for {source_run['case_id']}"
                )
            runs.append(
                {
                    "run_id": f"{model}__{source_run['run_id']}__repair-{repair_mode}",
                    "cohort": "primary",
                    "model": model,
                    "case_id": source_run["case_id"],
                    "tier": source_run["tier"],
                    "repetition": source_run["repetition"],
                    "seed": source_run["seed"],
                    "prompt_sha256": source_run["prompt_sha256"],
                    "case_sha256": prompt_record["case_sha256"],
                    "requirement_source_canonical_sha256": rendered[
                        "source_canonical_sha256"
                    ],
                    "repair_mode": repair_mode,
                }
            )
    schedule = {
        "schema_version": "atlas.asw_v3.experiment_schedule.v3",
        "cohort": "primary",
        "rendered_manifest": str(RENDERED_MANIFEST),
        "rendered_manifest_sha256": sha256_file(RENDERED_MANIFEST),
        "rendered_content_sha256": rendered["content_sha256"],
        "models": models,
        "repair_mode": repair_mode,
        "freeze_manifest_path": freeze["manifest_path"],
        "freeze_manifest_file_sha256": freeze["manifest_file_sha256"],
        "freeze_manifest_sha256": freeze["manifest_sha256"],
        "experiment_contract_sha256": freeze["experiment_contract_sha256"],
        "neo4j_context_sha256": freeze["neo4j_context_sha256"],
        "pipeline_run_count": len(runs),
        "runs": runs,
    }
    schedule["content_sha256"] = canonical_sha256(schedule)
    return schedule


def build_heldout_schedule(
    models: list[str],
    repair_mode: str,
    freeze_manifest: Path = DEFAULT_FREEZE_MANIFEST,
) -> dict[str, Any]:
    """Build the separate 36-run confirmatory schedule from the reviewed V3 source."""

    freeze = verify_freeze_manifest(freeze_manifest)
    contract = json.loads(FORMAL_CONTRACT.read_text(encoding="utf-8"))
    if models != list(contract["models"]):
        raise ValueError("held-out schedule models differ from the frozen contract")
    if repair_mode != str(contract["generation"]["repair_mode"]):
        raise ValueError("held-out schedule repair mode differs from the frozen contract")
    heldout_contract = contract.get("heldout_requirement_set") or {}
    from heldout_v3_runtime import (
        EXPECTED_SOURCE_SHA256,
        SOURCE,
        load_manifest,
        render_prompt,
        sha256_file as heldout_sha256_file,
        validate_manifest,
    )

    manifest = load_manifest()
    validation = validate_manifest(manifest)
    if validation.get("status") != "PASS":
        raise ValueError("held-out V3 runtime projection failed validation")
    if heldout_sha256_file(SOURCE) != EXPECTED_SOURCE_SHA256:
        raise ValueError("held-out V3 source differs from the frozen candidate")
    if len(manifest["cases"]) != int(heldout_contract.get("case_count") or -1):
        raise ValueError("held-out case count differs from the frozen contract")
    seeds = list(heldout_contract.get("seeds") or [])
    repetitions = int(heldout_contract.get("repetitions_per_case") or 0)
    if seeds != list(manifest["experiment_design"]["seeds"]):
        raise ValueError("held-out seeds differ from the reviewed source")
    if len(seeds) != repetitions:
        raise ValueError("held-out repetition count differs from its seed count")
    runs: list[dict[str, Any]] = []
    for model in models:
        for case in manifest["cases"]:
            prompt_sha256 = hashlib.sha256(
                render_prompt(manifest, case).encode("utf-8")
            ).hexdigest()
            for repetition, seed in enumerate(seeds, start=1):
                runs.append(
                    {
                        "run_id": (
                            f"{model}__heldout-v3__{case['case_id']}__R{repetition}__"
                            f"repair-{repair_mode}"
                        ),
                        "cohort": "heldout",
                        "model": model,
                        "case_id": case["case_id"],
                        "tier": case["tier"],
                        "structural_role": case["structural_role"],
                        "repetition": repetition,
                        "seed": int(seed),
                        "prompt_sha256": prompt_sha256,
                        "case_sha256": case["review_source_case_sha256"],
                        "requirement_source_canonical_sha256": manifest[
                            "review_source_canonical_sha256"
                        ],
                        "repair_mode": repair_mode,
                    }
                )
    schedule = {
        "schema_version": "atlas.autosar.heldout_v3.experiment_schedule.v1",
        "cohort": "prospective_internally_authored_heldout",
        "external_benchmark": False,
        "heldout_source": str(SOURCE),
        "heldout_source_sha256": EXPECTED_SOURCE_SHA256,
        "models": models,
        "repair_mode": repair_mode,
        "freeze_manifest_path": freeze["manifest_path"],
        "freeze_manifest_file_sha256": freeze["manifest_file_sha256"],
        "freeze_manifest_sha256": freeze["manifest_sha256"],
        "experiment_contract_sha256": freeze["experiment_contract_sha256"],
        "neo4j_context_sha256": freeze["neo4j_context_sha256"],
        "case_count": len(manifest["cases"]),
        "repetitions_per_case": repetitions,
        "pipeline_run_count": len(runs),
        "structural_role_case_counts": {"REPLICATION": 6, "EXTENSION": 6},
        "unit_of_analysis": "case",
        "runs": runs,
    }
    schedule["content_sha256"] = canonical_sha256(schedule)
    return schedule


REPLACEMENT_SCHEDULE_SCHEMA_VERSION = "atlas.v17.replacement_schedule.v2"


def _verify_replacement_schedule(schedule: dict[str, Any]) -> dict[str, Any]:
    """Accept a replacement schedule only for the cohort it was derived from."""
    from replacement_policy import (
        MAX_REPLACEMENTS_PER_SLOT,
        NEVER_REPLACED_KINDS,
        POLICY_VERSION,
        REPLACEMENT_ELIGIBLE_DELIVERY_STATES,
        build_replacement_schedule,
        failure_fingerprint,
        slot_is_replaceable,
    )

    for field in (
        "original_schedule_path",
        "original_schedule_file_sha256",
        "original_schedule_content_sha256",
        "original_results_path",
        "original_results_file_sha256",
        "original_results_content_sha256",
        "freeze_manifest_path",
        "freeze_manifest_file_sha256",
        "freeze_manifest_sha256",
    ):
        if not schedule.get(field):
            raise ValueError(f"replacement schedule does not bind {field}")
    if schedule.get("cohort") != "replacement":
        raise ValueError("replacement schedule must declare cohort=replacement")
    if schedule.get("policy_version") != POLICY_VERSION:
        raise ValueError("replacement schedule policy version mismatch")
    if schedule.get("analysis_layer") != "replacement_sensitivity":
        raise ValueError("replacement schedule analysis layer mismatch")
    if schedule.get("not_admissible_to_original_denominator") is not True:
        raise ValueError(
            "replacement schedule must declare that it is not admissible to the "
            "original denominator"
        )
    if int(schedule.get("max_replacements_per_slot") or 0) != MAX_REPLACEMENTS_PER_SLOT:
        raise ValueError("replacement schedule violates the frozen attempt cap")
    original_schedule_path = Path(schedule["original_schedule_path"]).resolve()
    original_results_path = Path(schedule["original_results_path"]).resolve()
    if (
        sha256_file(original_schedule_path)
        != schedule["original_schedule_file_sha256"]
        or sha256_file(original_results_path)
        != schedule["original_results_file_sha256"]
    ):
        raise ValueError("replacement source artifact file hash mismatch")
    original_schedule = _read_json_object(original_schedule_path)
    original_results = _read_json_object(original_results_path)
    if (
        original_schedule.get("content_sha256")
        != schedule["original_schedule_content_sha256"]
        or original_results.get("content_sha256")
        != schedule["original_results_content_sha256"]
    ):
        raise ValueError("replacement source artifact content identity mismatch")
    if original_schedule.get("schema_version") == REPLACEMENT_SCHEDULE_SCHEMA_VERSION:
        raise ValueError("a replacement schedule may not recursively source another replacement")
    verify_schedule(original_schedule)
    verify_experiment_results(original_results)
    if original_results.get("schedule") != original_schedule:
        raise ValueError("replacement results do not embed the bound original schedule")
    if schedule.get("created_at_utc") != original_results.get("completed_at_utc"):
        raise ValueError(
            "replacement schedule timestamp is not deterministically bound to "
            "the source cohort completion"
        )

    freeze = verify_freeze_manifest(
        Path(schedule["freeze_manifest_path"]),
        expected_file_sha256=schedule["freeze_manifest_file_sha256"],
        expected_manifest_sha256=schedule["freeze_manifest_sha256"],
    )
    if freeze["manifest_sha256"] != schedule["freeze_manifest_sha256"]:
        raise ValueError("replacement schedule binds a different freeze")
    if (
        original_schedule.get("freeze_manifest_sha256")
        != schedule["freeze_manifest_sha256"]
        or original_schedule.get("freeze_manifest_file_sha256")
        != schedule["freeze_manifest_file_sha256"]
    ):
        raise ValueError("replacement source schedule binds a different freeze")

    original_runs = {
        str(row["run_id"]): row for row in original_schedule.get("runs") or []
    }
    original_records = {
        str(row["run_id"]): row for row in original_results.get("records") or []
    }
    if len(original_runs) != len(original_schedule.get("runs") or []):
        raise ValueError("original schedule contains duplicate run IDs")
    if len(original_records) != len(original_results.get("records") or []):
        raise ValueError("original results contain duplicate run IDs")
    seen: set[str] = set()
    for row in schedule.get("runs") or []:
        replaced = str(row.get("replaces_run_id") or "")
        if not replaced:
            raise ValueError("replacement run does not name the slot it replaces")
        if replaced in seen:
            raise ValueError(f"more than one replacement for {replaced}")
        seen.add(replaced)
        if int(row.get("replacement_index") or 0) != 1:
            raise ValueError("only a first replacement is permitted")
        if str(row.get("original_completion_kind")) in NEVER_REPLACED_KINDS:
            raise ValueError(
                f"{replaced} is {row.get('original_completion_kind')} and may "
                "never be replaced"
            )
        if str(row.get("original_delivery_state")) not in (
            REPLACEMENT_ELIGIBLE_DELIVERY_STATES
        ):
            raise ValueError(
                f"{replaced} delivery state does not prove the request was "
                "never executed"
            )
        if not row.get("original_failure_fingerprint"):
            raise ValueError(f"{replaced} replacement lacks a failure fingerprint")
        source = original_runs.get(replaced)
        record = original_records.get(replaced)
        if source is None or record is None:
            raise ValueError(f"replacement source slot does not exist: {replaced}")
        eligible, _reason = slot_is_replaceable(record)
        if not eligible:
            raise ValueError(f"replacement source slot is not eligible: {replaced}")
        if row["original_failure_fingerprint"] != failure_fingerprint(record):
            raise ValueError(f"replacement failure fingerprint mismatch: {replaced}")
        expected_row = {
            key: source[key]
            for key in (
                "case_id", "tier", "repetition", "seed", "model",
                "prompt_sha256", "case_sha256", "repair_mode",
                "requirement_source_canonical_sha256",
            )
            if key in source
        }
        expected_row.update(
            {
                "run_id": f"{replaced}__replacement-1",
                "cohort": "replacement",
                "source_cohort": source.get("cohort", "primary"),
                "replaces_run_id": replaced,
                "replacement_index": 1,
                "original_completion_kind": record.get("completion_kind"),
                "original_delivery_state": record.get("delivery_state"),
                "original_failure_fingerprint": failure_fingerprint(record),
                "eligibility_reason": row.get("eligibility_reason"),
            }
        )
        if row != expected_row:
            raise ValueError(f"replacement run differs from its source slot: {replaced}")
    eligible_ids = {
        run_id for run_id, record in original_records.items()
        if slot_is_replaceable(record)[0]
    }
    if seen != eligible_ids:
        raise ValueError("replacement schedule drops or invents eligible source slots")
    if int(schedule.get("pipeline_run_count") or 0) != len(seen):
        raise ValueError("replacement schedule run count mismatch")
    expected_schedule = build_replacement_schedule(
        original_schedule,
        original_results,
        original_schedule_path=original_schedule_path,
        original_results_path=original_results_path,
    )
    if schedule != expected_schedule:
        raise ValueError(
            "replacement schedule differs from its deterministic source derivation"
        )
    return schedule


def verify_schedule(schedule: dict[str, Any]) -> dict[str, Any]:
    """Fail closed unless *schedule* is the one implied by frozen inputs."""

    unsigned_schedule = {
        key: value for key, value in schedule.items() if key != "content_sha256"
    }
    if canonical_sha256(unsigned_schedule) != schedule.get("content_sha256"):
        raise ValueError("schedule canonical hash mismatch")
    if schedule.get("schema_version") == REPLACEMENT_SCHEDULE_SCHEMA_VERSION:
        # A replacement schedule is not rebuildable from the frozen inputs
        # alone: it is a function of how the original cohort actually failed.
        # It is verified against the identities it binds instead, so it cannot
        # be pointed at a different cohort, freeze, or result set than the one
        # whose losses it answers.
        return _verify_replacement_schedule(schedule)
    if schedule.get("schema_version") == "atlas.autosar.heldout_v3.experiment_schedule.v1":
        expected = build_heldout_schedule(
            formal_models(),
            "off",
            Path(schedule["freeze_manifest_path"]),
        )
    else:
        expected = build_schedule(
            formal_models(),
            "off",
            Path(schedule["freeze_manifest_path"]),
        )
    if schedule != expected:
        raise ValueError("schedule differs from frozen formal experiment contract")
    return schedule


def _locate_artifacts(run_root: Path, component_name: str) -> tuple[Path, list[Path], Path]:
    arxml_files = sorted((run_root / "generated_arxml").rglob("*.arxml"))
    components: list[Path] = []
    interfaces: list[Path] = []
    parser = etree.XMLParser(resolve_entities=False, no_network=True, recover=False)
    for path in arxml_files:
        root = etree.parse(str(path), parser).getroot()
        component_names = root.xpath(
            "//ar:APPLICATION-SW-COMPONENT-TYPE/ar:SHORT-NAME/text()",
            namespaces=NS,
        )
        if component_name in component_names:
            components.append(path)
        elif root.xpath("//ar:SENDER-RECEIVER-INTERFACE", namespaces=NS):
            interfaces.append(path)
    validations = sorted(
        path
        for path in (run_root / "generated_arxml").rglob("*_validation_*.json")
        if "validation_context" not in path.name
    )
    if len(components) != 1 or len(validations) != 1:
        raise ValueError(
            f"expected one component and one validation report; "
            f"found components={len(components)}, validations={len(validations)}"
        )
    return components[0], interfaces, validations[0]


def _source_cohort(scheduled: dict[str, Any]) -> str:
    cohort = str(scheduled.get("cohort") or "primary")
    source = str(scheduled.get("source_cohort") or cohort)
    if source not in {"primary", "heldout"}:
        raise ValueError(f"invalid requirement source cohort: {source!r}")
    if cohort == "replacement" and not scheduled.get("source_cohort"):
        raise ValueError("replacement run does not bind its source cohort")
    return source


def _write_completion_manifest(
    run_root: Path,
    scheduled: dict[str, Any],
    schedule: dict[str, Any],
    attempt_number: int | None = None,
    *,
    completion_kind: str = "SUCCESSFUL_ARTIFACT",
) -> dict[str, Any]:
    if completion_kind not in COMPLETION_KINDS:
        raise ValueError(f"unsupported completion kind: {completion_kind}")
    artifacts = {
        path.relative_to(run_root).as_posix(): sha256_file(path)
        for path in sorted(item for item in run_root.rglob("*") if item.is_file())
        if path.name != "completion_manifest.json"
    }
    body = {
        "schema_version": "atlas.asw_v3.run_completion.v3",
        "run_id": scheduled["run_id"],
        "cohort": scheduled.get("cohort", "primary"),
        "source_cohort": _source_cohort(scheduled),
        "replaces_run_id": scheduled.get("replaces_run_id"),
        "model": scheduled["model"],
        "case_id": scheduled["case_id"],
        "repetition": scheduled["repetition"],
        "seed": scheduled["seed"],
        "repair_mode": scheduled["repair_mode"],
        "attempt_number": attempt_number,
        "completion_kind": completion_kind,
        "terminal": True,
        "retryable": False,
        "schedule_content_sha256": schedule["content_sha256"],
        "freeze_manifest_sha256": schedule["freeze_manifest_sha256"],
        "experiment_contract_sha256": schedule["experiment_contract_sha256"],
        "neo4j_context_sha256": schedule["neo4j_context_sha256"],
        "artifact_hashes": artifacts,
    }
    body["content_sha256"] = canonical_sha256(body)
    atomic_write_json(run_root / "completion_manifest.json", body)
    return body


def _run_complete(
    run_root: Path,
    scheduled: dict[str, Any],
    schedule: dict[str, Any],
    attempt_number: int | None = None,
) -> bool:
    """Return whether an attempt is an immutable terminal observation.

    The historical name is retained because repair scheduling imports it.  A
    terminal generation failure is complete as an experiment observation, but
    it is not a successful ARXML artifact.
    """

    completion_path = run_root / "completion_manifest.json"
    if not completion_path.is_file():
        return False
    try:
        completion = json.loads(completion_path.read_text(encoding="utf-8"))
        summary = json.loads((run_root / "run_summary.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    completion_kind = completion.get("completion_kind", "SUCCESSFUL_ARTIFACT")
    if completion_kind == "SUCCESSFUL_ARTIFACT":
        try:
            evaluation = json.loads(
                (run_root / "independent_evaluation.json").read_text(
                    encoding="utf-8"
                )
            )
        except (OSError, json.JSONDecodeError):
            return False
    elif completion_kind in NON_SUCCESS_COMPLETION_KINDS:
        if summary.get("final_status") != "failure":
            return False
        evaluation = None
    else:
        return False
    unsigned = {
        key: value for key, value in completion.items() if key != "content_sha256"
    }
    if canonical_sha256(unsigned) != completion.get("content_sha256"):
        return False
    identities = {
        "run_id": scheduled["run_id"],
        "cohort": scheduled.get("cohort", "primary"),
        "source_cohort": _source_cohort(scheduled),
        "replaces_run_id": scheduled.get("replaces_run_id"),
        "model": scheduled["model"],
        "case_id": scheduled["case_id"],
        "repetition": scheduled["repetition"],
        "seed": scheduled["seed"],
        "repair_mode": scheduled["repair_mode"],
        "schedule_content_sha256": schedule["content_sha256"],
        "freeze_manifest_sha256": schedule["freeze_manifest_sha256"],
        "experiment_contract_sha256": schedule["experiment_contract_sha256"],
        "neo4j_context_sha256": schedule["neo4j_context_sha256"],
        "attempt_number": attempt_number,
    }
    if any(completion.get(key) != value for key, value in identities.items()):
        return False
    summary_identities = {
        "cohort": scheduled.get("cohort", "primary"),
        "source_cohort": _source_cohort(scheduled),
        "model": scheduled["model"],
        "case_id": scheduled["case_id"],
        "repetition": scheduled["repetition"],
        "seed": scheduled["seed"],
        "repair_mode": scheduled["repair_mode"],
        "requirement_source_canonical_sha256": scheduled[
            "requirement_source_canonical_sha256"
        ],
        "case_sha256": scheduled["case_sha256"],
        "schedule_content_sha256": schedule["content_sha256"],
        "freeze_manifest_sha256": schedule["freeze_manifest_sha256"],
        "experiment_contract_sha256": schedule["experiment_contract_sha256"],
        "neo4j_context_sha256": schedule["neo4j_context_sha256"],
        "attempt_number": attempt_number,
    }
    if any(
        (
            summary.get(key, "primary")
            if key == "cohort"
            else (
                summary.get(key, _source_cohort(scheduled))
                if key == "source_cohort"
                else summary.get(key)
            )
        )
        != value
        for key, value in summary_identities.items()
    ):
        return False
    if evaluation is not None:
        if evaluation.get("case_id") != scheduled["case_id"]:
            return False
        if evaluation.get("cohort", "primary") != _source_cohort(scheduled):
            return False
    actual_files = {
        path.relative_to(run_root).as_posix()
        for path in run_root.rglob("*")
        if path.is_file() and path.name != "completion_manifest.json"
    }
    expected_hashes = completion.get("artifact_hashes") or {}
    if actual_files != set(expected_hashes):
        return False
    return all(
        sha256_file(run_root / relative) == expected
        for relative, expected in expected_hashes.items()
    )


def _record(
    run_root: Path,
    scheduled: dict[str, Any],
    status: str,
    *,
    attempt_number: int | None = None,
    attempt_roots: list[Path] | None = None,
) -> dict[str, Any]:
    hashes = {
        path.relative_to(run_root).as_posix(): sha256_file(path)
        for path in sorted(item for item in run_root.rglob("*") if item.is_file())
    }
    summary_path = run_root / "run_summary.json"
    evaluation_path = run_root / "independent_evaluation.json"
    summary = _read_json_object(summary_path) or None
    evaluation = _read_json_object(evaluation_path) or None
    phase1 = (summary or {}).get("phase1") or {}
    phase2 = (summary or {}).get("phase2") or {}
    provider_responses = [
        *(phase1.get("provider_responses") or []),
        *(phase2.get("provider_responses") or []),
    ]
    recorded_attempt_roots = attempt_roots or [run_root]
    provider_call_audit = [
        item
        for attempt_root in recorded_attempt_roots
        for item in _read_provider_call_audit(
            attempt_root / "provider_calls.jsonl"
        )
    ]
    audited_total_tokens = sum(
        int((item.get("usage") or {}).get("total_tokens") or 0)
        for item in provider_call_audit
    )
    completion = _read_json_object(run_root / "completion_manifest.json")
    attempt_records = []
    for path in recorded_attempt_roots:
        audit = _read_provider_call_audit(path / "provider_calls.jsonl")
        attempt_records.append(
            {
                "attempt_number": int(path.name.removeprefix("attempt-")),
                "run_root": str(path),
                "artifact_hashes": {
                    child.relative_to(path).as_posix(): sha256_file(child)
                    for child in sorted(
                        item for item in path.rglob("*") if item.is_file()
                    )
                },
                "provider_call_audit_count": len(audit),
                "provider_audited_total_tokens": sum(
                    int((item.get("usage") or {}).get("total_tokens") or 0)
                    for item in audit
                ),
            }
        )
    # The delivery evidence and the hashes of the files it came from travel with
    # the record, so a replacement schedule can bind the specific failure it
    # answers rather than a slot that merely failed similarly.
    classification = _read_json_object(run_root / "attempt_classification.json")
    transitions = _read_transition_ledger(run_root)
    return {
        **scheduled,
        "status": status,
        "terminal": status in TERMINAL_STATUSES,
        "completion_kind": completion.get("completion_kind"),
        "delivery_state": classification.get("delivery_state"),
        "billing_state": classification.get("billing_state"),
        "evidence_basis": classification.get("evidence_basis"),
        "delivery_evidence": _last_call_evidence(transitions) or None,
        "transition_ledger_sha256": (
            sha256_file(run_root / TRANSITION_LEDGER_NAME)
            if (run_root / TRANSITION_LEDGER_NAME).is_file() else None
        ),
        "provider_calls_sha256": (
            sha256_file(run_root / "provider_calls.jsonl")
            if (run_root / "provider_calls.jsonl").is_file() else None
        ),
        "run_root": str(run_root),
        "attempt_number": attempt_number,
        "attempts": attempt_records,
        "pipeline_final_status": (summary or {}).get("final_status"),
        "full_corpus_decision": ((summary or {}).get("phase2") or {}).get(
            "validation_decision"
        ),
        "artifact_profile_decision": ((summary or {}).get("phase2") or {}).get(
            "artifact_profile_decision"
        ),
        "independent_decision": (evaluation or {}).get("decision"),
        "xsd_all_pass": (
            None
            if evaluation is None
            else bool(evaluation.get("xsd"))
            and all(
                item.get("status") == "PASS"
                for item in evaluation.get("xsd") or []
            )
        ),
        "structural_failure_count": (evaluation or {}).get(
            "structural_failure_count"
        ),
        "local_reference_failure_count": (evaluation or {}).get(
            "local_reference_failure_count"
        ),
        "external_reference_not_evaluated_count": (evaluation or {}).get(
            "external_reference_not_evaluated_count"
        ),
        "phase1_tokens": phase1.get("tokens"),
        "phase2_tokens": phase2.get("tokens"),
        "total_tokens": (
            audited_total_tokens
            if provider_call_audit
            else (
                int(phase1.get("tokens") or 0) + int(phase2.get("tokens") or 0)
                if summary else None
            )
        ),
        "provider_call_audit_count": len(provider_call_audit),
        "provider_usage_complete": (
            status in TERMINAL_STATUSES
            and len(recorded_attempt_roots) == 1
            and bool(provider_call_audit)
        ),
        "phase1_duration_seconds": phase1.get("duration"),
        "phase2_duration_seconds": phase2.get("duration"),
        "total_duration_seconds": (
            float(phase1.get("duration") or 0)
            + float(phase2.get("duration") or 0)
            if summary else None
        ),
        "provider_response_models": sorted(
            {
                str(item["response_model"])
                for item in provider_responses
                if item.get("response_model")
            }
        ),
        "provider_system_fingerprints": sorted(
            {
                str(item["system_fingerprint"])
                for item in provider_responses
                if item.get("system_fingerprint")
            }
        ),
        "artifact_hashes": hashes,
    }


def _provider_queue_halt_reason(stdout: str, stderr: str) -> str | None:
    """Classify provider-wide blockers without retaining credential material."""

    text_value = f"{stdout}\n{stderr}".lower()
    markers = (
        ("insufficient_balance", "PROVIDER_INSUFFICIENT_BALANCE"),
        ("status code: 401", "PROVIDER_AUTHENTICATION"),
        ("error code: 401", "PROVIDER_AUTHENTICATION"),
        ("status code: 402", "PROVIDER_PAYMENT_REQUIRED"),
        ("error code: 402", "PROVIDER_PAYMENT_REQUIRED"),
        ("status code: 403", "PROVIDER_PERMISSION"),
        ("error code: 403", "PROVIDER_PERMISSION"),
        ("status code: 429", "PROVIDER_RATE_LIMIT"),
        ("error code: 429", "PROVIDER_RATE_LIMIT"),
        ("neo4j formal experiment context differs", "NEO4J_CONTEXT_MISMATCH"),
        ("frozen constraintv2 dataset is not ready", "NEO4J_CONTEXT_MISMATCH"),
    )
    reason = next((reason for marker, reason in markers if marker in text_value), None)
    if reason is not None:
        return reason
    strict_unavailable = (
        "strict json schema generation failed" in text_value
        and any(
            marker in text_value
            for marker in (
                "response_format is unsupported",
                "response_format not supported",
                "json_schema is unsupported",
                "json_schema not supported",
                "unsupported response_format",
            )
        )
    )
    return "PROVIDER_STRICT_SCHEMA_UNAVAILABLE" if strict_unavailable else None


TRANSITION_LEDGER_NAME = "provider_call_transitions.jsonl"


def _read_transition_ledger(run_root: Path | None) -> list[dict[str, Any]]:
    """Every provider-call stage this attempt durably recorded."""
    if run_root is None:
        return []
    path = run_root / TRANSITION_LEDGER_NAME
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            # A torn final line is the crash itself; keep what is readable.
            break
        if isinstance(item, dict) and item.get("credentials_included") is False:
            rows.append(item)
    return rows


def _last_call_evidence(transitions: list[dict[str, Any]]) -> dict[str, Any]:
    """Fold the stages of the most recent call into one evidence record.

    Delivery is decided from the last call the run attempted, because that is
    the one that ended it.  Stages are grouped by ``provider_call_id`` so a
    multi-call run cannot have its phases interleaved into a false picture.
    """
    if not transitions:
        return {}
    last_id = None
    for row in reversed(transitions):
        if row.get("provider_call_id"):
            last_id = row["provider_call_id"]
            break
    stages = [
        row for row in transitions
        if last_id is None or row.get("provider_call_id") == last_id
    ]
    evidence: dict[str, Any] = {
        "provider_call_id": last_id,
        "pipeline_phase": stages[-1].get("pipeline_phase"),
        "logical_call_index": stages[-1].get("logical_call_index"),
        "stages": [str(row.get("stage")) for row in stages],
        # Absent PRE_DISPATCH means nothing was recorded before the socket, so
        # dispatch is unknown rather than false.
        "dispatch_started": None,
    }
    for row in stages:
        stage = str(row.get("stage") or "")
        if stage == "PRE_DISPATCH" and evidence["dispatch_started"] is None:
            evidence["dispatch_started"] = False
        if row.get("dispatch_started") is True or stage in (
            "DISPATCH_STARTED", "RESPONSE_RECEIVED", "LOCAL_AUDIT_PERSISTED"
        ):
            evidence["dispatch_started"] = True
        for key in (
            "exception_type", "http_status", "response_id", "response_model",
            "response_headers_received", "request_acceptance_known",
        ):
            if row.get(key) is not None:
                evidence[key] = row[key]
    return evidence


OPERATOR_STOP_SENTINEL = "OPERATOR_STOP_REQUESTED"
OPERATOR_STOP_RECEIPT = "OPERATOR_STOP_RECEIPT.json"


def _operator_stop_receipt(
    experiment_root: Path,
    records: list[dict[str, Any]],
    schedule: dict[str, Any],
    *,
    additional_sentinel_roots: tuple[Path, ...] = (),
) -> dict[str, Any] | None:
    """Honour an operator stop request, at a run boundary and nowhere else.

    Stopping a paid experiment used to mean terminating the parent process and
    reasoning about the in-flight slot afterwards.  An operator can now create
    ``OPERATOR_STOP_REQUESTED`` in the experiment root; the queue finishes the
    slot it is on, records it, and stops before starting the next one.  The
    receipt states what was true at that moment so the boundary is auditable
    rather than reconstructed.

    A stop is never expressed as a fabricated provider error: that would write a
    false halt reason into the ledger.
    """
    sentinel_roots = [experiment_root.resolve()]
    for root in additional_sentinel_roots:
        resolved = root.resolve()
        if resolved not in sentinel_roots:
            sentinel_roots.append(resolved)
    sentinels = [root / OPERATOR_STOP_SENTINEL for root in sentinel_roots]
    sentinel = next((path for path in sentinels if path.is_file()), None)
    if sentinel is None:
        return None
    requested = ""
    try:
        requested = sentinel.read_text(encoding="utf-8").strip()[:2000]
    except OSError:
        requested = ""
    completed = [str(item.get("run_id")) for item in records]
    remaining = [
        str(item["run_id"])
        for item in schedule["runs"]
        if str(item["run_id"]) not in set(completed)
    ]
    receipt = {
        "schema_version": "atlas.asw_v3.operator_stop_receipt.v1",
        "stopped_at_utc": utc_now(),
        "reason": "operator stop sentinel observed at a run boundary",
        "operator_note": requested,
        "observed_sentinel_path": str(sentinel),
        "accepted_sentinel_paths": [str(path) for path in sentinels],
        "schedule_content_sha256": schedule["content_sha256"],
        "runs_completed": len(completed),
        "runs_scheduled": len(schedule["runs"]),
        "last_completed_run_id": completed[-1] if completed else None,
        "in_flight_run_id": None,
        "in_flight_state": "none; the stop was taken between runs",
        "not_started_run_ids": remaining,
        "provider_calls_interrupted": 0,
    }
    for root in sentinel_roots:
        atomic_write_json(root / OPERATOR_STOP_RECEIPT, receipt)
    return receipt


def _classify_failed_attempt(
    stdout: str,
    stderr: str,
    summary: dict[str, Any],
    *,
    timed_out: bool,
    run_root: Path | None = None,
) -> dict[str, Any]:
    """Separate scientific outcomes from retryable infrastructure failures."""

    if timed_out:
        # A hard pipeline timeout says the orchestrator stopped waiting.  It
        # does not say the provider stopped working, so re-running the slot can
        # issue a second paid execution for it.  This branch used to be
        # retryable, which contradicted the ambiguous-delivery rule applied
        # everywhere else; the slot is now terminal and its delivery is
        # unknown.  A provably undispatched slot is re-observed through the
        # replacement layer, never by silently repeating the attempt.
        return {
            "status": AMBIGUOUS_PROVIDER_DELIVERY,
            "completion_kind": AMBIGUOUS_PROVIDER_DELIVERY,
            "terminal": True,
            "retryable": False,
            "delivery_state": "AMBIGUOUS",
            "billing_state": "UNKNOWN",
            "replacement_eligible": False,
            "evidence_basis": "orchestrator_hard_timeout",
            "determination": (
                "the orchestrator hard timeout elapsed; server-side receipt, "
                "model execution and billing are unknown"
            ),
            "queue_halt_reason": None,
        }
    # Classify the current slot before deciding whether the provider-wide event
    # should halt later slots.  Queue control and scientific classification are
    # distinct: a 429 is an ambiguous terminal observation for this slot *and*
    # a reason not to dispatch the next one.
    queue_halt_reason = _provider_queue_halt_reason(stdout, stderr)
    text_value = f"{stdout}\n{stderr}\n{summary.get('error') or ''}".lower()
    # Delivery is decided before the outcome is named.  The previous version
    # matched "connection reset"/"aborted"/"refused" but not the bare
    # "Connection error." the provider SDK raises, so a transport fault fell
    # through to the scientific branch and three pilot slots were recorded as
    # generation failures.  It also marked every matched transport fault
    # retryable, which re-ran a whole slot whose request may already have been
    # executed -- a second paid execution for one scheduled slot.
    # Structured evidence first; the exception text is a compatibility fallback.
    # A run that produced a structured provider response and then failed on its
    # content is a model outcome; a run with no delivery evidence at all is
    # neither a model outcome nor a network one, and is reported as
    # unclassified rather than absorbed by either.
    audit_rows = (
        _read_provider_call_audit(run_root / "provider_calls.jsonl")
        if run_root is not None
        else []
    )
    # The transition ledger is the structured evidence.  It used to be written
    # and never read, while the classifier looked for exception_type and
    # http_status on the child summary -- fields the child never writes.  Both
    # ends were unconnected, so every failure fell through to the text
    # fallback the evidence order exists to avoid.
    transitions = _read_transition_ledger(run_root)
    evidence = _last_call_evidence(transitions)
    provider_call_id = str(evidence.get("provider_call_id") or "")
    matching_audit = next(
        (
            row for row in reversed(audit_rows)
            if provider_call_id
            and str(row.get("provider_call_id") or "") == provider_call_id
        ),
        {},
    )
    recorded_stages = set(evidence.get("stages") or [])
    delivery = classify_delivery(
        text_value,
        audit_persisted=bool(matching_audit),
        response_id=evidence.get("response_id") or matching_audit.get("response_id"),
        usage=matching_audit.get("usage"),
        exception_type=evidence.get("exception_type"),
        http_status=evidence.get("http_status"),
        response_headers_received=bool(evidence.get("response_headers_received")),
        structured_response_present="RESPONSE_RECEIVED" in recorded_stages,
        dispatch_started=evidence.get("dispatch_started"),
        acceptance_known=evidence.get("request_acceptance_known"),
        runner_stage=evidence.get("pipeline_phase"),
    )
    if delivery["delivery_state"] != "CONFIRMED_DELIVERED":
        kind = completion_kind_for(
            delivery_state=delivery["delivery_state"], model_reached=False
        )
        return {
            "status": kind,
            "completion_kind": kind,
            # Ambiguous delivery is terminal on purpose: it may not be retried,
            # because the provider may already have executed the request.
            "terminal": True,
            "retryable": False,
            "queue_halt_reason": queue_halt_reason,
            "delivery_state": delivery["delivery_state"],
            "billing_state": delivery["billing_state"],
            "replacement_eligible": delivery["replacement_eligible"],
            "evidence_basis": delivery["evidence_basis"],
            "provider_call_id": provider_call_id or None,
            "pipeline_phase": evidence.get("pipeline_phase"),
            "logical_call_index": evidence.get("logical_call_index"),
            "determination": delivery["determination"],
        }
    if summary.get("final_status") == "failure":
        return {
            "status": MODEL_OR_SCHEMA_GENERATION_FAILURE,
            "completion_kind": MODEL_OR_SCHEMA_GENERATION_FAILURE,
            "terminal": True,
            "retryable": False,
            "queue_halt_reason": queue_halt_reason,
            "delivery_state": "CONFIRMED_DELIVERED",
            "billing_state": "CONFIRMED",
            "replacement_eligible": False,
            "evidence_basis": delivery["evidence_basis"],
            "provider_call_id": provider_call_id or None,
            "pipeline_phase": evidence.get("pipeline_phase"),
            "logical_call_index": evidence.get("logical_call_index"),
            "determination": delivery["determination"],
        }
    return {
        "status": "RUNNER_ORCHESTRATION_FAILURE",
        "completion_kind": "RUNNER_ORCHESTRATION_FAILURE",
        "terminal": True,
        "retryable": False,
        "queue_halt_reason": (
            queue_halt_reason or "UNCLASSIFIED_PIPELINE_INFRASTRUCTURE_FAILURE"
        ),
        "delivery_state": delivery["delivery_state"],
        "billing_state": delivery["billing_state"],
        "replacement_eligible": False,
        "evidence_basis": delivery["evidence_basis"],
        "provider_call_id": provider_call_id or None,
        "pipeline_phase": evidence.get("pipeline_phase"),
        "logical_call_index": evidence.get("logical_call_index"),
        "determination": (
            "the child did not report a model failure after delivery; the "
            "orchestrator records a separate runner failure and halts the queue"
        ),
    }


def _required_completion_kind(classification: dict[str, Any]) -> str:
    """Reject a classifier that failed to emit one frozen terminal kind."""

    kind = classification.get("completion_kind")
    if kind not in COMPLETION_KINDS:
        raise ValueError("terminal classification lacks a valid completion_kind")
    return str(kind)


def _attempt_layout(run_base: Path) -> tuple[list[int], list[Path]]:
    run_base.mkdir(parents=True, exist_ok=True)
    invalid_entries = [
        path
        for path in run_base.iterdir()
        if not path.is_dir()
        or not path.name.startswith("attempt-")
        or not path.name.removeprefix("attempt-").isdigit()
    ]
    if invalid_entries:
        raise ValueError(f"run attempt layout contains unexpected entries: {run_base}")
    attempt_roots = sorted(
        run_base.iterdir(), key=lambda path: int(path.name.removeprefix("attempt-"))
    )
    observed_numbers = [
        int(path.name.removeprefix("attempt-")) for path in attempt_roots
    ]
    if observed_numbers != list(range(1, len(attempt_roots) + 1)):
        raise ValueError(f"run attempt numbers are not contiguous: {run_base}")
    return observed_numbers, attempt_roots


def _finish_existing_attempt_without_provider(
    run_root: Path,
    scheduled: dict[str, Any],
    schedule: dict[str, Any],
    attempt_number: int,
) -> str | None:
    """Finalize a child result left between summary and completion writes."""

    summary = _read_json_object(run_root / "run_summary.json")
    if not summary:
        return None
    if summary.get("final_status") == "failure":
        classification = _read_json_object(
            run_root / "attempt_classification.json"
        )
        if not classification:
            process = _read_json_object(run_root / "pipeline_process.json")
            classification = _classify_failed_attempt(
                (run_root / "pipeline.stdout.log").read_text(
                    encoding="utf-8", errors="replace"
                )
                if (run_root / "pipeline.stdout.log").is_file()
                else "",
                (run_root / "pipeline.stderr.log").read_text(
                    encoding="utf-8", errors="replace"
                )
                if (run_root / "pipeline.stderr.log").is_file()
                else "",
                summary,
                timed_out=bool(process.get("timed_out")),
                run_root=run_root,
            )
            atomic_write_json(
                run_root / "attempt_classification.json", classification
            )
        if not classification.get("terminal"):
            return None
        _write_completion_manifest(
            run_root,
            scheduled,
            schedule,
            attempt_number,
            completion_kind=_required_completion_kind(classification),
        )
        if not _run_complete(run_root, scheduled, schedule, attempt_number):
            raise ValueError(
                f"terminal failure summary identity is invalid: {scheduled['run_id']}"
            )
        return "RESUMED_TERMINAL_FAILURE"
    completed_statuses = {
        "success",
        "generated_with_validation_errors",
        "generated_with_incomplete_validation",
    }
    if summary.get("final_status") not in completed_statuses:
        return None
    evaluation_path = run_root / "independent_evaluation.json"
    if not evaluation_path.is_file():
        component, interfaces, validation = _locate_artifacts(
            run_root, str(summary["system_name"])
        )
        atomic_write_json(
            evaluation_path,
            evaluate(
                case_id=scheduled["case_id"],
                component_path=component,
                interface_paths=interfaces,
                validation_path=validation,
                cohort=_source_cohort(scheduled),
            ),
        )
    _write_completion_manifest(run_root, scheduled, schedule, attempt_number)
    if not _run_complete(run_root, scheduled, schedule, attempt_number):
        raise ValueError(
            f"successful child summary identity is invalid: {scheduled['run_id']}"
        )
    return "RESUMED_COMPLETE"


def _write_partial_results(
    experiment_root: Path,
    schedule: dict[str, Any],
    records: list[dict[str, Any]],
    queue_halt_reason: str | None,
) -> None:
    partial = {
        "schema_version": "atlas.asw_v3.experiment_results.v2",
        "schedule_content_sha256": schedule["content_sha256"],
        "record_count": len(records),
        "queue_halt_reason": queue_halt_reason,
        "records": records,
    }
    partial["content_sha256"] = canonical_sha256(partial)
    atomic_write_json(experiment_root / "experiment_results.partial.json", partial)


def run_experiment(
    schedule: dict[str, Any], experiment_root: Path, timeout_seconds: int,
    *,
    offline_scripted: bool = False,
    additional_operator_stop_roots: tuple[Path, ...] = (),
) -> dict[str, Any]:
    verify_schedule(schedule)
    freeze = verify_freeze_manifest(
        Path(schedule["freeze_manifest_path"]),
        expected_file_sha256=schedule["freeze_manifest_file_sha256"],
        expected_manifest_sha256=schedule["freeze_manifest_sha256"],
    )
    if freeze["experiment_contract_sha256"] != schedule[
        "experiment_contract_sha256"
    ]:
        raise ExperimentFreezeError("schedule experiment contract identity mismatch")
    if freeze["neo4j_context_sha256"] != schedule["neo4j_context_sha256"]:
        raise ExperimentFreezeError("schedule Neo4j context identity mismatch")
    experiment_root = experiment_root.resolve()
    contract = json.loads(FORMAL_CONTRACT.read_text(encoding="utf-8"))
    expected_timeout_seconds = int(
        contract["generation"]["orchestration"][
            "generation_child_hard_timeout_seconds"
        ]
    )
    if not offline_scripted and int(timeout_seconds) != expected_timeout_seconds:
        raise ValueError(
            "formal generation timeout differs from the frozen contract: "
            f"expected {expected_timeout_seconds}, got {timeout_seconds}"
        )
    max_attempts = int(contract["generation"]["max_pipeline_attempts_per_run"])
    with exclusive_experiment_lock(
        experiment_root, schedule_sha256=schedule["content_sha256"]
    ):
        schedule_path = experiment_root / "experiment_schedule.json"
        schedule_text = (
            json.dumps(schedule, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        )
        if (
            schedule_path.exists()
            and schedule_path.read_text(encoding="utf-8") != schedule_text
        ):
            raise FileExistsError(
                "experiment root is already bound to a different immutable schedule"
            )
        if not schedule_path.exists():
            atomic_write_text(schedule_path, schedule_text)

        records: list[dict[str, Any]] = []
        queue_halt_reason = None
        operator_stop = None
        for scheduled in schedule["runs"]:
            # The only place an operator stop is honoured.  Checking here and
            # nowhere else means a stop can never land inside a provider call:
            # the slot in flight always finishes and is recorded first.  The
            # V16 pilot had no such hook, so stopping it required terminating
            # the parent at a boundary observed from outside.
            operator_stop = _operator_stop_receipt(
                experiment_root,
                records,
                schedule,
                additional_sentinel_roots=additional_operator_stop_roots,
            )
            if operator_stop is not None:
                break
            run_base = (
                experiment_root
                / "runs"
                / scheduled["model"]
                / scheduled["case_id"]
                / f"R{scheduled['repetition']}"
                / f"repair-{scheduled['repair_mode']}"
            )
            observed_numbers, attempt_roots = _attempt_layout(run_base)
            for attempt_number, attempt_root in zip(observed_numbers, attempt_roots):
                recovered = recover_orphaned_child(
                    child_state_path(
                        experiment_root, scheduled["run_id"], attempt_number
                    )
                )
                if recovered and not (attempt_root / "run_summary.json").is_file():
                    atomic_write_json(
                        attempt_root / "attempt_classification.json",
                        {
                            "status": "TRANSIENT_ORPHANED_CHILD_RECOVERED",
                            "terminal": False,
                            "retryable": True,
                            "queue_halt_reason": None,
                            "recovery": recovered,
                        },
                    )
            if len(attempt_roots) > max_attempts:
                raise ValueError(f"attempt budget exceeded: {scheduled['run_id']}")

            complete_attempts = [
                (number, path)
                for number, path in zip(observed_numbers, attempt_roots)
                if _run_complete(path, scheduled, schedule, number)
            ]
            if len(complete_attempts) > 1:
                raise ValueError(
                    f"multiple terminal attempts exist for {scheduled['run_id']}"
                )
            if complete_attempts:
                attempt_number, run_root = complete_attempts[0]
                completion = _read_json_object(run_root / "completion_manifest.json")
                resumed_status = (
                    "RESUMED_TERMINAL_FAILURE"
                    if completion.get("completion_kind")
                    in NON_SUCCESS_COMPLETION_KINDS
                    else "RESUMED_COMPLETE"
                )
                records.append(
                    _record(
                        run_root,
                        scheduled,
                        resumed_status,
                        attempt_number=attempt_number,
                        attempt_roots=attempt_roots,
                    )
                )
                _write_partial_results(
                    experiment_root, schedule, records, queue_halt_reason
                )
                continue

            # A crash may occur after the child summary is durable but before
            # independent evaluation/completion.  Finish it locally first.
            finalized_existing = None
            if attempt_roots:
                finalized_existing = _finish_existing_attempt_without_provider(
                    attempt_roots[-1],
                    scheduled,
                    schedule,
                    observed_numbers[-1],
                )
            if finalized_existing is not None:
                records.append(
                    _record(
                        attempt_roots[-1],
                        scheduled,
                        finalized_existing,
                        attempt_number=observed_numbers[-1],
                        attempt_roots=attempt_roots,
                    )
                )
                _write_partial_results(
                    experiment_root, schedule, records, queue_halt_reason
                )
                continue

            prior_classification = (
                _read_json_object(attempt_roots[-1] / "attempt_classification.json")
                if attempt_roots
                else {}
            )
            if prior_classification and not prior_classification.get("retryable"):
                if prior_classification.get("terminal"):
                    raise ValueError(
                        f"terminal attempt lacks an auditable completion: "
                        f"{scheduled['run_id']}"
                    )
                queue_halt_reason = prior_classification.get("queue_halt_reason")
                records.append(
                    _record(
                        attempt_roots[-1],
                        scheduled,
                        str(prior_classification.get("status") or "NOT_EVALUATED"),
                        attempt_number=observed_numbers[-1],
                        attempt_roots=attempt_roots,
                    )
                )
                _write_partial_results(
                    experiment_root, schedule, records, queue_halt_reason
                )
                break

            status = "NOT_EVALUATED_ATTEMPTS_EXHAUSTED"
            run_root = attempt_roots[-1] if attempt_roots else run_base
            attempt_number = observed_numbers[-1] if observed_numbers else 0
            while len(attempt_roots) < max_attempts:
                attempt_number, run_root = reserve_attempt(run_base, max_attempts)
                command = [
                    sys.executable,
                    "-B",
                    str(RUNNER),
                    "--case-id",
                    scheduled["case_id"],
                    "--cohort",
                    scheduled.get("cohort", "primary"),
                    "--model",
                    scheduled["model"],
                    "--repetition",
                    str(scheduled["repetition"]),
                    "--repair-mode",
                    scheduled["repair_mode"],
                    "--run-root",
                    str(run_root),
                    "--expected-schedule-sha256",
                    schedule["content_sha256"],
                    "--attempt-number",
                    str(attempt_number),
                ]
                if scheduled.get("cohort") == "replacement":
                    command.extend(["--source-cohort", _source_cohort(scheduled)])
                if offline_scripted:
                    command.extend(
                        [
                            "--offline-scripted",
                            "--expected-freeze-sha256",
                            schedule["freeze_manifest_sha256"],
                            "--expected-freeze-file-sha256",
                            schedule["freeze_manifest_file_sha256"],
                            "--expected-contract-sha256",
                            schedule["experiment_contract_sha256"],
                            "--expected-neo4j-context-sha256",
                            schedule["neo4j_context_sha256"],
                        ]
                    )
                else:
                    command.extend(
                        [
                            "--freeze-manifest",
                            schedule["freeze_manifest_path"],
                            "--expected-freeze-sha256",
                            schedule["freeze_manifest_sha256"],
                        ]
                    )
                process = run_child_process(
                    command,
                    cwd=ROOT,
                    timeout_seconds=timeout_seconds,
                    # Outside the runs layout: the child requires this
                    # directory to be empty when it starts.
                    state_path=child_state_path(
                        experiment_root, scheduled["run_id"], attempt_number
                    ),
                    # Teed as the child writes them.  These used to be written
                    # only after the child exited, so a hung or stopped run left
                    # no readable log at all.
                    stdout_path=run_root / "pipeline.stdout.log",
                    stderr_path=run_root / "pipeline.stderr.log",
                )
                atomic_write_json(
                    run_root / "pipeline_process.json",
                    {
                        "returncode": process.returncode,
                        "timed_out": process.timed_out,
                        "termination": process.termination,
                    },
                )
                attempt_roots = [*attempt_roots, run_root]
                if process.returncode == 0 and not process.timed_out:
                    try:
                        finalized = _finish_existing_attempt_without_provider(
                            run_root, scheduled, schedule, attempt_number
                        )
                        if finalized != "RESUMED_COMPLETE":
                            raise ValueError(
                                "successful child did not produce a completed summary"
                            )
                        status = "COMPLETE"
                    except Exception as error:
                        atomic_write_json(
                            run_root / "orchestrator_error.json",
                            {"type": type(error).__name__, "message": str(error)},
                        )
                        status = "NOT_EVALUATED_ORCHESTRATOR_FAILURE"
                        queue_halt_reason = "ORCHESTRATOR_POSTPROCESSING_FAILURE"
                    break

                summary = _read_json_object(run_root / "run_summary.json")
                classification = _classify_failed_attempt(
                    process.stdout,
                    process.stderr,
                    summary,
                    timed_out=process.timed_out,
                    run_root=run_root,
                )
                status = str(classification["status"])
                queue_halt_reason = classification["queue_halt_reason"]
                atomic_write_json(
                    run_root / "attempt_classification.json", classification
                )
                if classification["terminal"]:
                    _write_completion_manifest(
                        run_root,
                        scheduled,
                        schedule,
                        attempt_number,
                        completion_kind=_required_completion_kind(classification),
                    )
                    if not _run_complete(
                        run_root, scheduled, schedule, attempt_number
                    ):
                        raise ValueError(
                            f"terminal failure failed audit: {scheduled['run_id']}"
                        )
                    break
                if not classification["retryable"]:
                    break
                if len(attempt_roots) >= max_attempts:
                    status = "NOT_EVALUATED_ATTEMPTS_EXHAUSTED"
                    queue_halt_reason = "TRANSIENT_ATTEMPTS_EXHAUSTED"
                    break

            if status == "NOT_EVALUATED_ATTEMPTS_EXHAUSTED":
                queue_halt_reason = "TRANSIENT_ATTEMPTS_EXHAUSTED"

            records.append(
                _record(
                    run_root,
                    scheduled,
                    status,
                    attempt_number=attempt_number,
                    attempt_roots=attempt_roots,
                )
            )
            _write_partial_results(
                experiment_root, schedule, records, queue_halt_reason
            )
            if queue_halt_reason is not None:
                break

        experiment_complete = (
            operator_stop is None
            and len(records) == len(schedule["runs"])
            and all(item["status"] in TERMINAL_STATUSES for item in records)
        )
        result = {
            "schema_version": "atlas.asw_v3.experiment_results.v2",
            "schedule": schedule,
            "completed_at_utc": utc_now() if experiment_complete else None,
            "snapshot_at_utc": utc_now(),
            "experiment_complete": experiment_complete,
            "record_count": len(records),
            "status_counts": dict(Counter(item["status"] for item in records)),
            "queue_halt_reason": queue_halt_reason,
            "operator_stop": operator_stop,
            "offline_scripted": offline_scripted,
            "external_model_api_calls": 0 if offline_scripted else None,
            "records": records,
        }
        result["content_sha256"] = canonical_sha256(result)
        _write_partial_results(experiment_root, schedule, records, queue_halt_reason)
        if experiment_complete:
            atomic_write_json(experiment_root / "experiment_results.json", result)
        return result


def verify_experiment_results(results: dict[str, Any]) -> dict[str, Any]:
    """Verify a generation result and every claimed complete run."""

    unsigned = {
        key: value for key, value in results.items() if key != "content_sha256"
    }
    if canonical_sha256(unsigned) != results.get("content_sha256"):
        raise ValueError("experiment results canonical hash mismatch")
    if results.get("offline_scripted") is True:
        raise ValueError("offline scripted results are not formal experiment results")
    schedule = verify_schedule(results.get("schedule") or {})
    if results.get("experiment_complete") is not True:
        raise ValueError("formal experiment results are not complete")
    records = list(results.get("records") or [])
    if len(records) != schedule["pipeline_run_count"]:
        raise ValueError("experiment result count differs from formal schedule")
    scheduled_by_id = {item["run_id"]: item for item in schedule["runs"]}
    if len(scheduled_by_id) != len(records):
        raise ValueError("experiment results contain duplicate or missing run IDs")
    observed_ids: set[str] = set()
    for record in records:
        run_id = str(record.get("run_id") or "")
        scheduled = scheduled_by_id.get(run_id)
        if scheduled is None or run_id in observed_ids:
            raise ValueError(f"experiment result run identity is invalid: {run_id}")
        observed_ids.add(run_id)
        for key in (
            "cohort", "source_cohort", "replaces_run_id", "model", "case_id",
            "tier", "repetition", "seed", "repair_mode",
            "case_sha256", "requirement_source_canonical_sha256",
        ):
            if key == "cohort":
                record_value = record.get(key, "primary")
            elif key == "source_cohort":
                record_value = record.get(key, _source_cohort(scheduled))
            else:
                record_value = record.get(key)
            scheduled_value = (
                scheduled.get(key, "primary")
                if key == "cohort"
                else (
                    _source_cohort(scheduled)
                    if key == "source_cohort"
                    else scheduled.get(key)
                )
            )
            if record_value != scheduled_value:
                raise ValueError(f"experiment result identity mismatch: {run_id}/{key}")
        if record.get("status") not in TERMINAL_STATUSES:
            raise ValueError(f"experiment observation is not terminal: {run_id}")
        if not _run_complete(
            Path(str(record["run_root"])),
            scheduled,
            schedule,
            int(record["attempt_number"]),
        ):
            raise ValueError(f"completed experiment run failed audit: {run_id}")
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-root", type=Path)
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    parser.add_argument(
        "--cohort",
        choices=("primary", "heldout", "replacement"),
        default="primary",
    )
    parser.add_argument(
        "--freeze-manifest", type=Path, default=DEFAULT_FREEZE_MANIFEST
    )
    parser.add_argument(
        "--schedule-path",
        type=Path,
        help="consume an already generated immutable formal schedule",
    )
    parser.add_argument(
        "--schedule-output",
        type=Path,
        help="write the deterministic schedule during --dry-run",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--offline-scripted",
        action="store_true",
        help=(
            "consume the real schedule/orchestrator/child chain with the "
            "deterministic zero-network client; never admissible as a formal result"
        ),
    )
    args = parser.parse_args()
    if args.schedule_path is not None and args.schedule_output is not None:
        parser.error("--schedule-path and --schedule-output are mutually exclusive")
    if args.schedule_output is not None and not args.dry_run:
        parser.error("--schedule-output is only valid with --dry-run")
    if args.offline_scripted and args.dry_run:
        parser.error("--offline-scripted requires an executing --experiment-root")
    if args.schedule_path is not None:
        schedule = json.loads(args.schedule_path.read_text(encoding="utf-8"))
        verify_schedule(schedule)
    else:
        if args.cohort == "replacement":
            # A replacement cohort is a function of how the original cohort
            # actually failed, so it cannot be built from the frozen inputs and
            # must be supplied as a derived schedule.
            parser.error(
                "--cohort replacement requires --schedule-path pointing at a "
                "schedule derived from a completed original cohort"
            )
        schedule = (
            build_schedule(formal_models(), "off", args.freeze_manifest)
            if args.cohort == "primary"
            else build_heldout_schedule(formal_models(), "off", args.freeze_manifest)
        )
    if args.schedule_output is not None:
        schedule_text = (
            json.dumps(schedule, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        )
        if (
            args.schedule_output.exists()
            and args.schedule_output.read_text(encoding="utf-8") != schedule_text
        ):
            raise FileExistsError(
                "schedule output exists with different immutable content"
            )
        args.schedule_output.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_text(args.schedule_output, schedule_text)
    if args.dry_run:
        print(
            json.dumps(
                {
                    "pipeline_run_count": schedule["pipeline_run_count"],
                    "models": schedule["models"],
                    "repair_mode": schedule["repair_mode"],
                    "freeze_manifest_sha256": schedule["freeze_manifest_sha256"],
                    "experiment_contract_sha256": schedule[
                        "experiment_contract_sha256"
                    ],
                    "neo4j_context_sha256": schedule["neo4j_context_sha256"],
                    "content_sha256": schedule["content_sha256"],
                    "schedule_output": (
                        str(args.schedule_output.resolve())
                        if args.schedule_output is not None else None
                    ),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    if args.experiment_root is None:
        parser.error("--experiment-root is required unless --dry-run is used")
    result = run_experiment(
        schedule,
        args.experiment_root,
        args.timeout_seconds,
        offline_scripted=args.offline_scripted,
    )
    print(
        json.dumps(
            {
                "record_count": result["record_count"],
                "status_counts": result["status_counts"],
                "content_sha256": result["content_sha256"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if result["experiment_complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
