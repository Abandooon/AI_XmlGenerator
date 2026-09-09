"""Recover infrastructure losses without inventing model results.

A scheduled slot that died in transport is a real loss of observation, but it is
not a model outcome.  Dropping it inflates the model-quality rate; keeping it in
that rate blames the model for the network.  Neither is acceptable, so the slot
stays in the operational denominator, leaves the model-quality denominator, and
may be re-observed only under conditions that cannot produce a second paid
execution for one slot.

The eligibility rule is deliberately narrow.  A replacement is permitted only
where the evidence shows the provider cannot have executed the request:

* ``DEFINITELY_NOT_DISPATCHED`` --- the transition ledger recorded PRE_DISPATCH
  and never DISPATCH_STARTED, so nothing left the client;
* ``CONFIRMED_REJECTED_BEFORE_MODEL_EXECUTION`` --- the provider answered with a
  status that declines before any model runs.

``AMBIGUOUS_PROVIDER_DELIVERY`` and ``UNCLASSIFIED_FAILURE`` are never replaced.
Their whole content is that we do not know what the server did; re-issuing them
is precisely the duplicate-call condition the experiment forbids.  They remain
as ``missing``, which is an honest gap rather than a fabricated observation.

Replacements never overwrite the original ledger.  They are a separate schedule,
a separate result set, and a separate reported layer, so a reader can always see
the original cohort as it actually ran.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from delivery_classification import (
    AMBIGUOUS_PROVIDER_DELIVERY,
    COMPLETION_KINDS,
    DEFINITELY_NOT_DISPATCHED,
    INFRASTRUCTURE_TRANSPORT_FAILURE,
    MODEL_QUALITY_KINDS,
    OPERATIONAL_KINDS,
    PROVIDER_NO_EXECUTION_GUARANTEE,
    REJECTED_BEFORE_EXECUTION,
    SEPARATELY_REPORTED_KINDS,
    SUCCESSFUL_ARTIFACT,
    UNCLASSIFIED_FAILURE,
)


POLICY_VERSION = "atlas.v17.replacement_policy.v2"
SCHEDULE_SCHEMA_VERSION = "atlas.v17.replacement_schedule.v2"

REPLACEMENT_ELIGIBLE_DELIVERY_STATES = frozenset(
    {DEFINITELY_NOT_DISPATCHED, REJECTED_BEFORE_EXECUTION}
)
NEVER_REPLACED_KINDS = frozenset(
    {AMBIGUOUS_PROVIDER_DELIVERY, UNCLASSIFIED_FAILURE}
)
MAX_REPLACEMENTS_PER_SLOT = 1


class ReplacementPolicyError(ValueError):
    """Raised when a replacement would violate the frozen policy."""


def build_policy_artifact() -> dict[str, Any]:
    """Build the timeless policy document included inside the paper freeze.

    The policy cannot bind the freeze or schedules by hash because those
    objects bind this policy through the freeze.  Keeping identity links in
    both directions would create a circular hash chain.  Instead the policy is
    frozen as an experiment file, and every runnable schedule binds that freeze.
    """

    policy: dict[str, Any] = {
        "schema_version": POLICY_VERSION,
        "replacement_schedule_schema_version": SCHEDULE_SCHEMA_VERSION,
        "policy_document_role": "method_input_included_in_paper_artifact_freeze",
        "identity_binding": (
            "this exact file is hashed inside the paper artifact freeze; each "
            "primary, held-out, and later derived replacement schedule binds "
            "that freeze"
        ),
        "completion_kinds": list(COMPLETION_KINDS),
        "operational_denominator_kinds": [
            kind for kind in COMPLETION_KINDS if kind in OPERATIONAL_KINDS
        ],
        "model_quality_denominator_kinds": [
            kind for kind in COMPLETION_KINDS if kind in MODEL_QUALITY_KINDS
        ],
        "separately_reported_kinds": [
            kind for kind in COMPLETION_KINDS if kind in SEPARATELY_REPORTED_KINDS
        ],
        "never_replaced_kinds": [
            kind for kind in COMPLETION_KINDS if kind in NEVER_REPLACED_KINDS
        ],
        "provider_no_execution_guarantee_frozen": (
            PROVIDER_NO_EXECUTION_GUARANTEE
        ),
        "replacement_eligible_delivery_states": [
            DEFINITELY_NOT_DISPATCHED,
            REJECTED_BEFORE_EXECUTION,
        ],
        "currently_operational_eligibility_states": (
            [DEFINITELY_NOT_DISPATCHED, REJECTED_BEFORE_EXECUTION]
            if PROVIDER_NO_EXECUTION_GUARANTEE
            else [DEFINITELY_NOT_DISPATCHED]
        ),
        "max_replacements_per_slot": MAX_REPLACEMENTS_PER_SLOT,
        "numerator_rule": (
            "an independent evaluator PASS; a produced artifact with validation "
            "errors or incomplete validation is not a pass"
        ),
        "derivation": (
            "derive deterministically only after experiment_complete; reopen and "
            "fully verify the immutable original schedule, original results, and "
            "freeze; bind both source file hashes, both canonical content hashes, "
            "the source completion time, and every eligible failure fingerprint"
        ),
        "failure_fingerprint_binds": [
            "slot coordinates and attempt number",
            "completion kind, delivery state, billing state, evidence basis",
            "provider_call_id, pipeline_phase, logical_call_index",
            "exception_type, http_status, response_id, recorded stages",
            "transition_ledger_sha256 and provider_calls_sha256",
        ],
        "retry_policy": {
            "sdk_implicit_retry": "disabled_and_runtime_asserted",
            "provider_max_attempts_per_call": 1,
            "orchestrator_retry_on_transport": "disabled",
            "orchestrator_retry_on_timeout": "disabled",
            "recursive_replacement": "disabled",
        },
        "reporting_layers": [
            "primary: operational success, intention-to-treat over all scheduled slots",
            "secondary: conditional model quality, available-case on delivered responses",
            "sensitivity: replacement-recovered result, never pooled",
        ],
        "forbidden": [
            "replacing AMBIGUOUS_PROVIDER_DELIVERY or UNCLASSIFIED_FAILURE",
            "more than one replacement per slot or recursive replacement",
            "writing replacement results into the original ledger or denominator",
            "pooling the three reporting layers into one rate",
            "SDK-implicit or orchestrator transport/timeout retry",
            "reporting UNKNOWN billing as zero cost or zero provider calls",
            "asserting zero model execution from a status without a frozen provider guarantee",
            "counting a produced artifact as a pass without an independent PASS",
            "treating the 60 seed-level runs as independent units",
            "comparing any layer with the V15 46/60",
        ],
    }
    policy["content_sha256"] = _canonical_sha256(policy)
    return policy


def _canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _verified_source_document(
    value: dict[str, Any], path: Path, *, label: str
) -> tuple[Path, str]:
    """Bind one in-memory source to the exact immutable JSON file it came from."""

    resolved = path.resolve()
    if not resolved.is_file():
        raise ReplacementPolicyError(f"{label} source file is missing: {resolved}")
    try:
        observed = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ReplacementPolicyError(f"{label} source is not valid JSON") from error
    if observed != value:
        raise ReplacementPolicyError(
            f"{label} in memory differs from the source artifact"
        )
    unsigned = {key: item for key, item in value.items() if key != "content_sha256"}
    if _canonical_sha256(unsigned) != value.get("content_sha256"):
        raise ReplacementPolicyError(f"{label} canonical hash mismatch")
    return resolved, _file_sha256(resolved)


def failure_fingerprint(record: dict[str, Any]) -> str:
    """Identity of the specific failure a replacement is answering.

    The slot coordinates and classification are not enough: the same slot can
    fail the same way twice for different reasons, and a schedule bound only to
    those could be replayed against a later cohort that merely looks alike. The
    fingerprint therefore also binds the evidence the classification rests on --
    the provider call identity, the exception and status observed, the recorded
    stages, and the hashes of the evidence files themselves.
    """
    evidence = record.get("delivery_evidence") or {}
    return _canonical_sha256(
        {
            "run_id": record.get("run_id"),
            "case_id": record.get("case_id"),
            "repetition": record.get("repetition"),
            "seed": record.get("seed"),
            "attempt_number": record.get("attempt_number"),
            "completion_kind": record.get("completion_kind"),
            "delivery_state": record.get("delivery_state"),
            "billing_state": record.get("billing_state"),
            "evidence_basis": record.get("evidence_basis"),
            "provider_call_id": evidence.get("provider_call_id"),
            "pipeline_phase": evidence.get("pipeline_phase"),
            "logical_call_index": evidence.get("logical_call_index"),
            "exception_type": evidence.get("exception_type"),
            "http_status": evidence.get("http_status"),
            "response_id": evidence.get("response_id"),
            "recorded_stages": list(evidence.get("stages") or []),
            "transition_ledger_sha256": record.get("transition_ledger_sha256"),
            "provider_calls_sha256": record.get("provider_calls_sha256"),
        }
    )


def slot_is_replaceable(record: dict[str, Any]) -> tuple[bool, str]:
    """Whether one original slot may be re-observed, and why."""
    kind = str(record.get("completion_kind") or "")
    delivery = str(record.get("delivery_state") or "")
    if kind in NEVER_REPLACED_KINDS:
        return False, (
            f"{kind} cannot be replaced: the provider may already have executed "
            "the request, so a replacement risks a second paid execution for one "
            "scheduled slot; the slot stays missing"
        )
    if kind in MODEL_QUALITY_KINDS:
        return False, (
            f"{kind} is a model result and is never replaced"
        )
    if kind != INFRASTRUCTURE_TRANSPORT_FAILURE:
        return False, f"{kind} is not an infrastructure loss"
    if delivery not in REPLACEMENT_ELIGIBLE_DELIVERY_STATES:
        return False, (
            f"delivery state {delivery!r} does not prove the provider could not "
            "have executed the request"
        )
    if int(record.get("replacement_attempts") or 0) >= MAX_REPLACEMENTS_PER_SLOT:
        return False, (
            "the slot already had its one replacement; a further attempt would "
            "be a recursive retry and the slot is recorded as missing"
        )
    return True, (
        f"delivery state {delivery!r} proves no model execution was possible; "
        "one replacement is permitted"
    )


def build_replacement_schedule(
    original_schedule: dict[str, Any],
    original_results: dict[str, Any],
    *,
    original_schedule_path: Path,
    original_results_path: Path,
) -> dict[str, Any]:
    """Derive the replacement schedule deterministically from a finished cohort.

    This may only run after the original cohort is complete: a replacement built
    while the original is still executing would be conditional on a partial
    result, and the cohort it answers would not be a fixed object.
    """
    schedule_path, schedule_file_sha256 = _verified_source_document(
        original_schedule, original_schedule_path, label="original schedule"
    )
    results_path, results_file_sha256 = _verified_source_document(
        original_results, original_results_path, label="original results"
    )
    if original_results.get("experiment_complete") is not True:
        raise ReplacementPolicyError(
            "a replacement schedule may only be derived from a completed "
            "original cohort"
        )
    completed_at_utc = original_results.get("completed_at_utc")
    if not isinstance(completed_at_utc, str) or not completed_at_utc.strip():
        raise ReplacementPolicyError(
            "completed original results must carry completed_at_utc so the "
            "derived replacement schedule has a deterministic timestamp"
        )
    if original_results.get("schedule") != original_schedule:
        raise ReplacementPolicyError(
            "original results do not embed the bound original schedule"
        )
    freeze_path = Path(str(original_schedule.get("freeze_manifest_path") or ""))
    if not freeze_path.is_file():
        raise ReplacementPolicyError("original schedule freeze manifest is missing")
    freeze_file_sha256 = _file_sha256(freeze_path)
    if freeze_file_sha256 != original_schedule.get("freeze_manifest_file_sha256"):
        raise ReplacementPolicyError("original schedule freeze file hash mismatch")
    original_runs = {
        str(item["run_id"]): item for item in original_schedule["runs"]
    }
    rows: list[dict[str, Any]] = []
    refused: list[dict[str, Any]] = []
    for record in original_results.get("records") or []:
        replaceable, reason = slot_is_replaceable(record)
        run_id = str(record.get("run_id"))
        if not replaceable:
            if str(record.get("completion_kind")) not in MODEL_QUALITY_KINDS:
                refused.append(
                    {"run_id": run_id, "completion_kind":
                     record.get("completion_kind"), "reason": reason}
                )
            continue
        source = original_runs.get(run_id)
        if source is None:
            raise ReplacementPolicyError(
                f"result {run_id} is not in the original schedule"
            )
        # Identical case, seed, prompt, model, and freeze: a replacement
        # re-observes the same slot, it does not create a new condition.
        rows.append(
            {
                **{
                    key: source[key]
                    for key in (
                        "case_id", "tier", "repetition", "seed", "model",
                        "prompt_sha256", "case_sha256", "repair_mode",
                        "requirement_source_canonical_sha256",
                    )
                    if key in source
                },
                "run_id": f"{run_id}__replacement-1",
                "cohort": "replacement",
                "source_cohort": source.get("cohort", "primary"),
                "replaces_run_id": run_id,
                "replacement_index": 1,
                "original_completion_kind": record.get("completion_kind"),
                "original_delivery_state": record.get("delivery_state"),
                "original_failure_fingerprint": failure_fingerprint(record),
                "eligibility_reason": reason,
            }
        )
    schedule = {
        "schema_version": SCHEDULE_SCHEMA_VERSION,
        "policy_version": POLICY_VERSION,
        "cohort": "replacement",
        "analysis_layer": "replacement_sensitivity",
        "not_admissible_to_original_denominator": True,
        "original_schedule_path": str(schedule_path),
        "original_schedule_file_sha256": schedule_file_sha256,
        "original_schedule_content_sha256": original_schedule["content_sha256"],
        "original_results_path": str(results_path),
        "original_results_file_sha256": results_file_sha256,
        "original_results_content_sha256": original_results["content_sha256"],
        "freeze_manifest_path": str(freeze_path.resolve()),
        "freeze_manifest_file_sha256": freeze_file_sha256,
        "freeze_manifest_sha256": original_schedule["freeze_manifest_sha256"],
        "experiment_contract_sha256": original_schedule.get(
            "experiment_contract_sha256"
        ),
        "neo4j_context_sha256": original_schedule.get("neo4j_context_sha256"),
        "models": original_schedule["models"],
        "repair_mode": original_schedule["repair_mode"],
        "max_replacements_per_slot": MAX_REPLACEMENTS_PER_SLOT,
        "pipeline_run_count": len(rows),
        "runs": rows,
        "refused_slots": refused,
        # A wall-clock timestamp here made identical immutable inputs produce
        # different schedule hashes.  The source cohort's frozen completion
        # time is the earliest possible derivation time and is fully bound by
        # original_results_content_sha256, so it is both meaningful and
        # deterministic.
        "created_at_utc": completed_at_utc,
    }
    schedule["content_sha256"] = _canonical_sha256(schedule)
    return schedule


def summarize_layers(
    original_results: dict[str, Any],
    replacement_results: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """The three layers a report must carry, never collapsed into one rate."""
    records = list(original_results.get("records") or [])
    scheduled = len(records)
    kinds: dict[str, int] = {}
    for record in records:
        kind = str(record.get("completion_kind") or "UNRECORDED")
        kinds[kind] = kinds.get(kind, 0) + 1

    model_quality = [
        item for item in records
        if str(item.get("completion_kind")) in MODEL_QUALITY_KINDS
    ]
    # "Produced an artifact" is not "passed".  A run whose final status is
    # generated_with_validation_errors or generated_with_incomplete_validation
    # still carries completion_kind SUCCESSFUL_ARTIFACT, so counting the kind
    # alone put failed artifacts in the numerator and overstated the rate.  The
    # numerator is the independent evaluator's PASS.
    successes = [
        item for item in model_quality
        if str(item.get("completion_kind")) == SUCCESSFUL_ARTIFACT
        and str(item.get("independent_decision")) == "PASS"
    ]
    produced_but_not_passing = [
        item for item in model_quality
        if str(item.get("completion_kind")) == SUCCESSFUL_ARTIFACT
        and str(item.get("independent_decision")) != "PASS"
    ]

    replacement_layer: dict[str, Any] | None = None
    if replacement_results is not None:
        replaced = list(replacement_results.get("records") or [])
        recovered = [
            item for item in replaced
            if str(item.get("completion_kind")) == SUCCESSFUL_ARTIFACT
            and str(item.get("independent_decision")) == "PASS"
        ]
        replacement_layer = {
            "attempted": len(replaced),
            "recovered": len(recovered),
            "still_failed": len(replaced) - len(recovered),
            "recursive_retries": 0,
            "interpretation": (
                "sensitivity only; these observations are not filled back into "
                "the original slots and never change the original rate"
            ),
        }

    return {
        "schema_version": "atlas.v17.layered_result_summary.v1",
        "operational_reliability": {
            "scheduled_slots": scheduled,
            "completion_kind_counts": kinds,
            "denominator": scheduled,
            "note": (
                "every scheduled slot counts here, including transport, "
                "ambiguous and unclassified losses"
            ),
        },
        "operational_success": {
            "denominator": scheduled,
            "passing": len(successes),
            "note": (
                "intention-to-treat: strict end-to-end success over every "
                "scheduled slot, keeping all missingness in the denominator. "
                "This endpoint needs no assumption about why slots were lost "
                "and is the primary result."
            ),
        },
        "conditional_model_quality": {
            "denominator": len(model_quality),
            "passing": len(successes),
            "artifacts_produced_but_not_passing": len(produced_but_not_passing),
            "excluded_from_denominator": scheduled - len(model_quality),
            "note": (
                "available-case analysis conditioned on a delivered provider "
                "response. At most the scheduled count, and smaller whenever an "
                "unanalyzable loss occurs. Missingness here is not necessarily "
                "random, so this is a secondary, explicitly conditional result "
                "and is never published without the operational denominator."
            ),
        },
        "replacement_sensitivity": replacement_layer,
        "forbidden": [
            "pooling the replacement layer into the original denominator",
            "reporting conditional model quality without the operational result",
            "counting a produced artifact as a pass without an independent PASS",
            "treating the 60 seed-level runs as independent units; the 20 cases "
            "are the units for confirmatory inference",
            "comparing any layer with the V15 46/60",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "build the frozen replacement policy or derive one immutable "
            "replacement schedule from formal results"
        )
    )
    parser.add_argument("--policy-output", type=Path)
    parser.add_argument("--original-schedule", type=Path)
    parser.add_argument("--original-results", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--replace-existing-policy",
        action="store_true",
        help="replace a stale generated policy artifact during a new freeze build",
    )
    args = parser.parse_args()
    if args.policy_output is not None:
        if any((args.original_schedule, args.original_results, args.output)):
            parser.error(
                "--policy-output cannot be combined with replacement schedule inputs"
            )
        document = build_policy_artifact()
        text = json.dumps(
            document, ensure_ascii=False, indent=2, sort_keys=True
        ) + "\n"
        output = args.policy_output.resolve()
        if output.exists() and output.read_text(encoding="utf-8") != text:
            if not args.replace_existing_policy:
                raise FileExistsError(
                    "policy output already has different content; use "
                    "--replace-existing-policy only as part of an intentional "
                    "new freeze build"
                )
        output.parent.mkdir(parents=True, exist_ok=True)
        from experiment_runtime import atomic_write_text

        atomic_write_text(output, text)
        print(json.dumps({
            "decision": "PASS",
            "schema_version": document["schema_version"],
            "content_sha256": document["content_sha256"],
            "output": str(output),
            "external_model_api_calls": 0,
        }, indent=2))
        return 0
    if not all((args.original_schedule, args.original_results, args.output)):
        parser.error(
            "schedule derivation requires --original-schedule, "
            "--original-results, and --output"
        )
    original_schedule = json.loads(
        args.original_schedule.read_text(encoding="utf-8")
    )
    original_results = json.loads(args.original_results.read_text(encoding="utf-8"))
    derived = build_replacement_schedule(
        original_schedule,
        original_results,
        original_schedule_path=args.original_schedule,
        original_results_path=args.original_results,
    )
    # Re-open and verify every bound artifact, result record, freeze identity and
    # failure fingerprint before exposing a runnable schedule.
    from run_asw_v3_experiment import verify_schedule

    verify_schedule(derived)
    text = json.dumps(derived, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    output = args.output.resolve()
    if output.exists() and output.read_text(encoding="utf-8") != text:
        raise FileExistsError("replacement schedule output already has different content")
    output.parent.mkdir(parents=True, exist_ok=True)
    if not output.exists():
        from experiment_runtime import atomic_write_text

        atomic_write_text(output, text)
    print(json.dumps({
        "decision": "PASS",
        "pipeline_run_count": derived["pipeline_run_count"],
        "content_sha256": derived["content_sha256"],
        "output": str(output),
        "external_model_api_calls": 0,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
