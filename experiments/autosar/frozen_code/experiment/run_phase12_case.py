"""Run one curated ASW V3 requirement through the existing ATLAS Phase 1/2 chain.

This adapter deliberately does not define or modify a provider JSON Schema.
Phase 2 remains authoritative for Neo4j constraint retrieval, schema assembly,
XSD-driven serialization, and V2 validation. Credentials are loaded only into
the current process and are never printed or persisted by this adapter.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from experiment_freeze import verify_freeze_manifest
from neo4j_experiment_context import (
    collect_neo4j_context,
    verify_neo4j_context,
)


ATLAS_ROOT = Path(r"E:\git projects\AI_XmlGenerator")
CASES_ROOT = Path(r"E:\54239\Documents\atlas_autosar_requirements_v3")
DEFAULT_CASE_ID = "ASW-STD-07"
MODELS = ("gpt-5.6-luna", "gpt-5.6-terra", "gpt-5.6-sol")
DEFAULT_RUNS_ROOT = Path(__file__).resolve().parent / "outputs" / "repaired-phase12"


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _transport_continuation_audit(
    path: Path,
    *,
    max_attempts: int,
) -> dict[str, Any]:
    """Verify explicit transport attempts without turning them into trials."""

    if not path.is_file():
        return {
            "decision": "NOT_APPLICABLE_NO_NETWORK_LEDGER",
            "logical_request_count": 0,
            "provider_dispatch_count": 0,
            "continued_logical_request_count": 0,
            "max_observed_transport_attempt": 0,
        }
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        if not isinstance(item, dict) or item.get("credentials_included") is not False:
            raise RuntimeError("provider transition ledger is malformed")
        rows.append(item)
    logical: dict[str, dict[int, set[str]]] = {}
    response_attempts: dict[str, set[int]] = {}
    for row in rows:
        logical_id = str(row.get("logical_request_id") or "")
        provider_call_id = str(row.get("provider_call_id") or "")
        attempt = int(row.get("transport_attempt") or 0)
        if not logical_id or not provider_call_id or not 1 <= attempt <= max_attempts:
            raise RuntimeError("provider transition identity/attempt is invalid")
        logical.setdefault(logical_id, {}).setdefault(attempt, set()).add(
            provider_call_id
        )
        if row.get("stage") == "RESPONSE_RECEIVED":
            response_attempts.setdefault(logical_id, set()).add(attempt)
    for logical_id, attempts in logical.items():
        observed = sorted(attempts)
        if observed != list(range(1, max(observed) + 1)):
            raise RuntimeError("transport attempts are not contiguous")
        if any(len(call_ids) != 1 for call_ids in attempts.values()):
            raise RuntimeError("one transport attempt has multiple provider identities")
        if len(response_attempts.get(logical_id, set())) > 1:
            raise RuntimeError("one logical request has multiple received responses")
    maximum = max((max(attempts) for attempts in logical.values()), default=0)
    return {
        "decision": "PASS",
        "logical_request_count": len(logical),
        "provider_dispatch_count": sum(len(attempts) for attempts in logical.values()),
        "continued_logical_request_count": sum(
            1 for attempts in logical.values() if max(attempts) > 1
        ),
        "max_observed_transport_attempt": maximum,
        "failed_transport_attempts_are_experimental_observations": False,
    }


def _load_runtime_environment() -> None:
    load_dotenv(ATLAS_ROOT / ".env", override=False)
    if not os.environ.get("LLM_API_KEY"):
        for name in (
            "ATLAS_LLM_API_KEY",
            "API_KEY",
        ):
            value = os.environ.get(name)
            if value:
                os.environ["LLM_API_KEY"] = value
                break


def _preflight_formal_neo4j(
    config,
    expected_dataset_sha256: str,
    expected_card_count: int,
    expected_context: dict,
) -> dict:
    """Read-only proof that both formal Phase 2 Neo4j inputs are available."""

    if not config.knowledge_graph.neo4j_password:
        raise RuntimeError("formal Neo4j preflight requires configured credentials")
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver(
        config.knowledge_graph.neo4j_uri,
        auth=(
            config.knowledge_graph.neo4j_user,
            config.knowledge_graph.neo4j_password,
        ),
    )
    try:
        observed = collect_neo4j_context(
            driver,
            database=config.knowledge_graph.neo4j_database or None,
            dataset_sha256=expected_dataset_sha256,
            expected_card_count=expected_card_count,
        )
    finally:
        driver.close()
    verify_neo4j_context(observed, expected_context)
    return {
        "decision": "PASS",
        "constraint_dataset_sha256": expected_dataset_sha256,
        "constraint_card_count": expected_card_count,
        "context_sha256": observed["context_sha256"],
        "schema_node_count": observed["schema_node_count"],
        "schema_relationship_count": observed["schema_relationship_count"],
        "constraint_link_count": observed["constraint_link_count"],
        "required_schema_types": observed["required_schema_types"],
        "read_only": True,
    }


def _runtime_source(cohort: str, source_cohort: str | None = None):
    effective_cohort = source_cohort if cohort == "replacement" else cohort
    if cohort == "replacement" and effective_cohort not in {"primary", "heldout"}:
        raise ValueError("replacement cohort requires a primary or heldout source cohort")
    if effective_cohort == "primary":
        if str(CASES_ROOT) not in sys.path:
            sys.path.insert(0, str(CASES_ROOT))
        from render_cases import (
            canonical_sha256,
            event_short_name,
            load_manifest,
            render_prompt,
            validate_manifest,
            variable_access_short_name,
        )

        manifest = load_manifest(CASES_ROOT / "asw_cases_v3.yaml")
        source_canonical_sha256 = canonical_sha256(manifest)
        case_sha256 = canonical_sha256
    elif effective_cohort == "heldout":
        from heldout_v3_runtime import (
            canonical_sha256,
            event_short_name,
            load_manifest,
            render_prompt,
            validate_manifest,
            variable_access_short_name,
        )

        manifest = load_manifest()
        source_canonical_sha256 = manifest["review_source_canonical_sha256"]
        case_sha256 = lambda case: case["review_source_case_sha256"]
    else:
        raise ValueError(f"unsupported AUTOSAR cohort: {effective_cohort!r}")
    return {
        "manifest": manifest,
        "validate_manifest": validate_manifest,
        "render_prompt": render_prompt,
        "event_short_name": event_short_name,
        "variable_access_short_name": variable_access_short_name,
        "source_canonical_sha256": source_canonical_sha256,
        "case_sha256": case_sha256,
        "canonical_sha256": canonical_sha256,
    }


def _case_run_definition(
    case_id: str, repetition: int, cohort: str = "primary",
    source_cohort: str | None = None,
) -> dict:
    runtime = _runtime_source(cohort, source_cohort)
    manifest = runtime["manifest"]
    validate_manifest = runtime["validate_manifest"]
    validation = validate_manifest(manifest)
    if validation.get("status") != "PASS":
        raise RuntimeError(f"AUTOSAR {cohort} requirement manifest failed local validation")
    cases = manifest["cases"]
    matches = [
        (position, case)
        for position, case in enumerate(cases, start=1)
        if case["case_id"] == case_id
    ]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one ASW V3 case named {case_id!r}")
    seeds = manifest["experiment_design"]["seeds"]
    if repetition < 1 or repetition > len(seeds):
        raise ValueError(f"repetition must be between 1 and {len(seeds)}")
    position, case = matches[0]
    return {
        "manifest": manifest,
        "case": case,
        "case_index": position,
        "repetition": repetition,
        "seed": int(seeds[repetition - 1]),
        "source_canonical_sha256": runtime["source_canonical_sha256"],
        "case_sha256": runtime["case_sha256"](case),
        "cohort": cohort,
    }


def _requirement(
    case_id: str,
    generation_seed: int | None = None,
    cohort: str = "primary",
) -> dict:
    runtime = _runtime_source(cohort)
    canonical_sha256 = runtime["canonical_sha256"]
    event_short_name = runtime["event_short_name"]
    variable_access_short_name = runtime["variable_access_short_name"]
    manifest = runtime["manifest"]
    validate_manifest = runtime["validate_manifest"]
    validation = validate_manifest(manifest)
    if validation.get("status") != "PASS":
        raise RuntimeError(f"AUTOSAR {cohort} requirement manifest failed local validation")
    matches = [case for case in manifest["cases"] if case["case_id"] == case_id]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one ASW V3 case named {case_id!r}")
    case = matches[0]
    prompt = runtime["render_prompt"](manifest, case)
    component = case["component"]
    behavior = case.get("internal_behavior")
    declared_use_cases = ["sender_receiver_communication"]
    declared_constraint_ids: list[str] = []
    declared_targets: dict[str, list[str]] = {}
    if behavior is not None:
        declared_use_cases.append("periodic_sensor_processing")
        declared_constraint_ids.append("TPS_SWCT_01519")
        declared_targets["TPS_SWCT_01519"] = [
            f"/Components/{component}/{behavior['short_name']}/{runnable['short_name']}"
            for runnable in behavior["runnables"]
        ]
    required_port_targets = [
        f"/Components/{component}/Rp_{spec['signal']}"
        for spec in case.get("required_signals") or []
    ]
    if required_port_targets:
        declared_constraint_ids.append("constr_1100")
        declared_targets["constr_1100"] = required_port_targets
    authoritative_context = manifest["authoritative_context"]
    interface_catalog = authoritative_context["interface_catalog"]
    interface_data_type_bindings = []
    for signal in [
        *case.get("provided_signals", []),
        *(spec["signal"] for spec in case.get("required_signals") or []),
    ]:
        entry = interface_catalog[signal]
        if entry.get("type_ref") or entry.get("type_dest"):
            if not entry.get("type_ref") or not entry.get("type_dest"):
                raise ValueError(
                    f"incomplete source-owned interface type binding for {signal}"
                )
            interface_data_type_bindings.append(
                {
                    "interface_name": entry["interface_ref"].rsplit("/", 1)[-1],
                    "data_element": entry["data_element"],
                    "type_ref": entry["type_ref"],
                    "type_dest": entry["type_dest"],
                }
            )
    init_value = authoritative_context[
        "unconnected_required_port_init_value"
    ]
    init_value_path = [
        "PORTS",
        "R-PORT-PROTOTYPE",
        "REQUIRED-COM-SPECS",
        "NONQUEUED-RECEIVER-COM-SPEC",
        "INIT-VALUE",
        "NUMERICAL-VALUE-SPECIFICATION",
        "VALUE",
        "#TEXT",
    ]
    generation_value_obligations: list[dict] = []
    requirement_descriptions = {
        "asw.component.provided_ports": (
            "Materialize every declared provided port and its exact sender-receiver interface reference."
        ),
        "asw.component.required_ports": (
            "Materialize every declared required port, receiver ComSpec, timeout policy, init value, and exact interface/data references."
        ),
        "asw.component.internal_behavior": (
            "Materialize the declared SWC internal behavior identity."
        ),
        "asw.component.timing_events": (
            "Materialize one named timing event per runnable with its exact runnable reference and period."
        ),
        "asw.component.variable_accesses": (
            "Materialize every named runnable variable access with its exact port and target data references."
        ),
    }
    for signal in case.get("provided_signals") or []:
        catalog_entry = interface_catalog[signal]
        anchor = f"Pp_{signal}"
        port_anchors = [
            {"path": ["PORTS", "P-PORT-PROTOTYPE"], "short_name": anchor}
        ]
        reference_path = [
            "PORTS",
            "P-PORT-PROTOTYPE",
            "PROVIDED-INTERFACE-TREF",
        ]
        generation_value_obligations.extend(
            [
                {
                    "requirement_id": "asw.component.provided_ports",
                    "component": component,
                    "path": [*reference_path, "#TEXT"],
                    "anchors": port_anchors,
                    "value": catalog_entry["interface_ref"],
                },
                {
                    "requirement_id": "asw.component.provided_ports",
                    "component": component,
                    "path": [*reference_path, "@DEST"],
                    "anchors": port_anchors,
                    "value": "SENDER-RECEIVER-INTERFACE",
                },
            ]
        )
    for spec in case.get("required_signals") or []:
        signal = spec["signal"]
        catalog_entry = interface_catalog[signal]
        anchor = f"Rp_{signal}"
        port_anchors = [
            {"path": ["PORTS", "R-PORT-PROTOTYPE"], "short_name": anchor}
        ]
        comspec_path = [
            "PORTS",
            "R-PORT-PROTOTYPE",
            "REQUIRED-COM-SPECS",
            "NONQUEUED-RECEIVER-COM-SPEC",
        ]
        data_reference_path = [*comspec_path, "DATA-ELEMENT-REF"]
        interface_reference_path = [
            "PORTS",
            "R-PORT-PROTOTYPE",
            "REQUIRED-INTERFACE-TREF",
        ]
        generation_value_obligations.extend(
            [
                {
                    "requirement_id": "asw.component.required_ports",
                    "component": component,
                    "path": init_value_path,
                    "authoritative_subtree_path": init_value_path[:5],
                    "anchors": port_anchors,
                    "value": init_value,
                },
                {
                    "requirement_id": "asw.component.required_ports",
                    "component": component,
                    "path": [*data_reference_path, "#TEXT"],
                    "anchors": port_anchors,
                    "value": (
                        f"{catalog_entry['interface_ref']}/"
                        f"{catalog_entry['data_element']}"
                    ),
                },
                {
                    "requirement_id": "asw.component.required_ports",
                    "component": component,
                    "path": [*data_reference_path, "@DEST"],
                    "anchors": port_anchors,
                    "value": "VARIABLE-DATA-PROTOTYPE",
                },
                {
                    "requirement_id": "asw.component.required_ports",
                    "component": component,
                    "path": [*comspec_path, "ALIVE-TIMEOUT", "#TEXT"],
                    "anchors": port_anchors,
                    "value": spec["alive_timeout_s"],
                },
                {
                    "requirement_id": "asw.component.required_ports",
                    "component": component,
                    "path": [*comspec_path, "HANDLE-TIMEOUT-TYPE", "#TEXT"],
                    "anchors": port_anchors,
                    "value": spec["handle_timeout_type"],
                },
                {
                    "requirement_id": "asw.component.required_ports",
                    "component": component,
                    "path": [*interface_reference_path, "#TEXT"],
                    "anchors": port_anchors,
                    "value": catalog_entry["interface_ref"],
                },
                {
                    "requirement_id": "asw.component.required_ports",
                    "component": component,
                    "path": [*interface_reference_path, "@DEST"],
                    "anchors": port_anchors,
                    "value": "SENDER-RECEIVER-INTERFACE",
                },
            ]
        )
    if behavior is not None:
        behavior_prefix = [
            "INTERNAL-BEHAVIORS",
            "SWC-INTERNAL-BEHAVIOR",
        ]
        generation_value_obligations.append(
            {
                "requirement_id": "asw.component.internal_behavior",
                "component": component,
                "path": [*behavior_prefix, "SHORT-NAME", "#TEXT"],
                "anchors": [
                    {"path": behavior_prefix, "short_name": behavior["short_name"]}
                ],
                "value": behavior["short_name"],
            }
        )
        event_prefix = [*behavior_prefix, "EVENTS", "TIMING-EVENT"]
        runnable_prefix = [*behavior_prefix, "RUNNABLES", "RUNNABLE-ENTITY"]
        for runnable in behavior["runnables"]:
            runnable_name = runnable["short_name"]
            event_name = event_short_name(runnable_name)
            event_anchor = [{"path": event_prefix, "short_name": event_name}]
            generation_value_obligations.extend(
                [
                    {
                        "requirement_id": "asw.component.timing_events",
                        "component": component,
                        "path": [*event_prefix, "START-ON-EVENT-REF", "#TEXT"],
                        "anchors": event_anchor,
                        "value": (
                            f"/Components/{component}/{behavior['short_name']}/"
                            f"{runnable_name}"
                        ),
                    },
                    {
                        "requirement_id": "asw.component.timing_events",
                        "component": component,
                        "path": [*event_prefix, "START-ON-EVENT-REF", "@DEST"],
                        "anchors": event_anchor,
                        "value": "RUNNABLE-ENTITY",
                    },
                    {
                        "requirement_id": "asw.component.timing_events",
                        "component": component,
                        "path": [*event_prefix, "PERIOD", "#TEXT"],
                        "anchors": event_anchor,
                        "value": runnable["period_s"],
                    },
                ]
            )
            for direction, signals, wrapper, port_prefix, port_dest in (
                (
                    "read",
                    runnable["reads"],
                    "DATA-RECEIVE-POINT-BY-ARGUMENTS",
                    "Rp",
                    "R-PORT-PROTOTYPE",
                ),
                (
                    "write",
                    runnable["writes"],
                    "DATA-SEND-POINTS",
                    "Pp",
                    "P-PORT-PROTOTYPE",
                ),
            ):
                for signal in signals:
                    catalog_entry = interface_catalog[signal]
                    access_name = variable_access_short_name(
                        runnable_name, direction, signal
                    )
                    access_prefix = [*runnable_prefix, wrapper, "VARIABLE-ACCESS"]
                    access_anchors = [
                        {"path": runnable_prefix, "short_name": runnable_name},
                        {"path": access_prefix, "short_name": access_name},
                    ]
                    iref_prefix = [
                        *access_prefix,
                        "ACCESSED-VARIABLE",
                        "AUTOSAR-VARIABLE-IREF",
                    ]
                    generation_value_obligations.extend(
                        [
                            {
                                "requirement_id": "asw.component.variable_accesses",
                                "component": component,
                                "path": [*iref_prefix, "PORT-PROTOTYPE-REF", "#TEXT"],
                                "anchors": access_anchors,
                                "value": (
                                    f"/Components/{component}/{port_prefix}_{signal}"
                                ),
                            },
                            {
                                "requirement_id": "asw.component.variable_accesses",
                                "component": component,
                                "path": [*iref_prefix, "PORT-PROTOTYPE-REF", "@DEST"],
                                "anchors": access_anchors,
                                "value": port_dest,
                            },
                            {
                                "requirement_id": "asw.component.variable_accesses",
                                "component": component,
                                "path": [
                                    *iref_prefix,
                                    "TARGET-DATA-PROTOTYPE-REF",
                                    "#TEXT",
                                ],
                                "anchors": access_anchors,
                                "value": (
                                    f"{catalog_entry['interface_ref']}/"
                                    f"{catalog_entry['data_element']}"
                                ),
                            },
                            {
                                "requirement_id": "asw.component.variable_accesses",
                                "component": component,
                                "path": [
                                    *iref_prefix,
                                    "TARGET-DATA-PROTOTYPE-REF",
                                    "@DEST",
                                ],
                                "anchors": access_anchors,
                                "value": "VARIABLE-DATA-PROTOTYPE",
                            },
                        ]
                    )
    obligation_counts: dict[str, int] = {}
    for obligation in generation_value_obligations:
        requirement_id = obligation["requirement_id"]
        obligation_counts[requirement_id] = obligation_counts.get(requirement_id, 0) + 1
    generation_requirement_contracts = [
        {
            "requirement_id": requirement_id,
            "component": component,
            "requirement": requirement_descriptions[requirement_id],
            "expected_obligation_count": obligation_counts[requirement_id],
        }
        for requirement_id in requirement_descriptions
        if requirement_id in obligation_counts
    ]
    evidence_sha256 = canonical_sha256(authoritative_context)
    referenced_signals = [
        *case.get("provided_signals", []),
        *(spec["signal"] for spec in case.get("required_signals") or []),
    ]
    capability_scope_paths = [
        f"/Components/{component}",
        *(
            authoritative_context["interface_catalog"][signal]["interface_ref"]
            for signal in referenced_signals
        ),
        *(
            authoritative_context["interface_catalog"][signal]["type_ref"]
            for signal in referenced_signals
            if authoritative_context["interface_catalog"][signal].get("type_ref")
        ),
    ]
    declared_capability_scopes = [
        {
            "scope_path": path,
            "constraint_ids": declared_constraint_ids,
            "capabilities": ["complete_reference_scope"],
            "evidence_sha256": evidence_sha256,
            "evidence_kind": "hash_pinned_component_benchmark_context",
        }
        for path in sorted(set(capability_scope_paths))
    ] if declared_constraint_ids else []
    evidence_profile = authoritative_context["validation_evidence_profile"]
    return {
        "system_name": component,
        "description": prompt,
        "components_count": 1,
        "component_types": ["APPLICATION-SW-COMPONENT-TYPE"],
        "key_requirements": [
            f"Preserve the exact curated obligations for {case_id}.",
            "Use Phase 2 Neo4j retrieval and the hash-pinned XSD serialization contract.",
            "Fail closed rather than substituting an unrelated or raw-XML-only contract.",
        ],
        "declared_use_cases": declared_use_cases,
        "declared_constraint_ids": declared_constraint_ids,
        "declared_targets": declared_targets,
        "declared_parameters": {},
        "intent_scope": "complete",
        "generation_value_obligations": generation_value_obligations,
        "generation_requirement_contracts": generation_requirement_contracts,
        "interface_data_type_bindings": interface_data_type_bindings,
        "interface_package_ref": authoritative_context.get(
            "interface_package_ref", "/COM_Interface"
        ),
        "declared_capability_scopes": declared_capability_scopes,
        "manual_evidence_scope": {
            "profile_id": evidence_profile["profile_id"],
            "complete": evidence_profile["manual_evidence_scope_complete"],
            "excluded_capabilities": evidence_profile[
                "manual_capabilities_out_of_scope"
            ],
            "evidence_sha256": evidence_sha256,
        },
        "generation_seed": generation_seed,
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-id", default=DEFAULT_CASE_ID)
    parser.add_argument(
        "--cohort", choices=("primary", "heldout", "replacement"), default="primary"
    )
    parser.add_argument("--source-cohort", choices=("primary", "heldout"))
    parser.add_argument("--model", choices=MODELS, required=True)
    parser.add_argument("--repetition", type=int, default=1)
    parser.add_argument("--run-root", type=Path)
    parser.add_argument("--repair-mode", choices=("off", "on"), default="off")
    parser.add_argument("--freeze-manifest", type=Path)
    parser.add_argument("--expected-freeze-sha256")
    parser.add_argument("--expected-freeze-file-sha256")
    parser.add_argument("--expected-contract-sha256")
    parser.add_argument("--expected-neo4j-context-sha256")
    parser.add_argument("--expected-schedule-sha256")
    parser.add_argument("--attempt-number", type=int)
    parser.add_argument(
        "--offline-scripted",
        action="store_true",
        help="run the real Phase1/2 chain with a deterministic zero-network schema client",
    )
    parser.add_argument(
        "--scripted-fail-stage",
        choices=("round1", "interface", "component", "repair", "repair_value"),
    )
    args = parser.parse_args()

    if args.scripted_fail_stage and not args.offline_scripted:
        raise ValueError("--scripted-fail-stage requires --offline-scripted")
    if args.cohort == "replacement" and args.source_cohort is None:
        raise ValueError("replacement runs require --source-cohort")
    if args.cohort != "replacement" and args.source_cohort is not None:
        raise ValueError("--source-cohort is only valid for replacement runs")
    if args.offline_scripted and args.expected_schedule_sha256:
        required_offline_identities = {
            "expected_freeze_sha256": args.expected_freeze_sha256,
            "expected_freeze_file_sha256": args.expected_freeze_file_sha256,
            "expected_contract_sha256": args.expected_contract_sha256,
            "expected_neo4j_context_sha256": args.expected_neo4j_context_sha256,
        }
        missing = [key for key, value in required_offline_identities.items() if not value]
        if missing:
            raise ValueError(
                "schedule-consuming offline run lacks identities: " + ", ".join(missing)
            )

    freeze_verification = None
    formal_contract = None
    source_cohort = args.source_cohort or args.cohort
    run_definition = _case_run_definition(
        args.case_id, args.repetition, args.cohort, args.source_cohort
    )
    if args.freeze_manifest is not None:
        if not args.expected_freeze_sha256 or not args.expected_schedule_sha256:
            raise ValueError(
                "formal runs require expected freeze and schedule identities"
            )
        freeze_verification = verify_freeze_manifest(
            args.freeze_manifest,
            expected_manifest_sha256=args.expected_freeze_sha256,
        )
        formal_contract = json.loads(
            (Path(__file__).resolve().parent / "FORMAL_EXPERIMENT_CONTRACT.json")
            .read_text(encoding="utf-8")
        )
        if args.model not in formal_contract["models"]:
            raise ValueError("model is outside the frozen formal experiment contract")
        if args.repair_mode != formal_contract["generation"]["repair_mode"]:
            raise ValueError("repair mode differs from the frozen formal contract")
        requirement_contract_key = (
            "requirement_set" if source_cohort == "primary" else "heldout_requirement_set"
        )
        if requirement_contract_key not in formal_contract:
            raise ValueError(f"formal contract has no {args.cohort} requirement cohort")
        expected_seeds = formal_contract[requirement_contract_key]["seeds"]
        if run_definition["seed"] != expected_seeds[args.repetition - 1]:
            raise ValueError("run seed differs from the frozen formal contract")

    if args.offline_scripted:
        # Never inherit, inspect, print, or persist a real credential in the
        # scripted E2E path.  Concrete provider construction sees only this
        # non-secret placeholder before its client is replaced.
        os.environ["LLM_API_KEY"] = "offline-local-placeholder"
    else:
        _load_runtime_environment()
    if not os.environ.get("LLM_API_KEY"):
        raise RuntimeError("Phase 1/2 credentials are unavailable to the existing runtime")
    if str(ATLAS_ROOT) not in sys.path:
        sys.path.insert(0, str(ATLAS_ROOT))

    from src.llm_generation.config import CONFIG

    run_root = (
        args.run_root
        or (
            DEFAULT_RUNS_ROOT
            / args.model
            / args.case_id
            / f"R{args.repetition}"
            / args.repair_mode
        )
    ).resolve()
    # The orchestrator tees live stdout/stderr into the attempt directory before
    # the child starts.  Those two append-only logs are the only admissible
    # pre-existing entries; accepting anything else would risk overwriting an
    # earlier attempt.  The previous blanket emptiness check made the real
    # orchestrator and real child mutually incompatible.
    allowed_live_logs = {"pipeline.stdout.log", "pipeline.stderr.log"}
    unexpected = (
        [path for path in run_root.iterdir() if path.name not in allowed_live_logs]
        if run_root.exists()
        else []
    )
    if unexpected:
        raise FileExistsError(
            "run root contains non-log artifacts; choose a new immutable run "
            f"directory: {run_root}"
        )
    run_root.mkdir(parents=True, exist_ok=True)
    os.environ["ATLAS_PROVIDER_AUDIT_PATH"] = str(
        run_root / "provider_calls.jsonl"
    )
    # Written beside the response audit and read back by the orchestrator's
    # failure classifier.  Without this the ledger exists but nothing consumes
    # it, and delivery has to be guessed from exception text.
    os.environ["ATLAS_PROVIDER_TRANSITION_LEDGER_PATH"] = str(
        run_root / "provider_call_transitions.jsonl"
    )
    CONFIG.llm.model_name = args.model
    CONFIG.validation.auto_repair_enabled = args.repair_mode == "on"
    if formal_contract is not None:
        generation = formal_contract["generation"]
        provider_registration = generation["provider_registration"]
        if args.model != provider_registration["requested_model"]:
            raise ValueError("requested provider model differs from preregistration")
        expected_route_policy = str(
            provider_registration.get("transport_route_policy") or ""
        )
        if (
            expected_route_policy != "direct_no_environment_proxy"
            or generation.get("transport_route_policy") != expected_route_policy
        ):
            raise ValueError("formal provider route policy is incomplete or changed")
        if generation.get("stream_responses") is not False:
            raise ValueError("formal AUTOSAR runs require non-streaming provider calls")
        retry_policy = generation.get("retry_policy") or {}
        configured_attempts = int(
            generation.get("provider_max_attempts_per_call") or 0
        )
        if (
            configured_attempts < 1
            or retry_policy.get("sdk_implicit_retry") != "disabled"
            or retry_policy.get("application_transport_continuation")
            != (
                "up_to_8_attempts_within_one_logical_request_for_typed_"
                "transient_transport_errors_only"
            )
            or retry_policy.get("transport_retry_delays_seconds")
            != [1.0, 5.0, 15.0, 30.0, 60.0, 60.0, 60.0]
            or retry_policy.get(
                "failed_transport_attempts_are_experimental_observations"
            )
            is not False
        ):
            raise ValueError("formal provider retry policy is not fail-closed")
        endpoint = str(CONFIG.llm.llm_api_url or "").rstrip("/")
        endpoint_sha256 = hashlib.sha256(endpoint.encode("utf-8")).hexdigest()
        if endpoint_sha256 != provider_registration["provider_endpoint_sha256"]:
            raise ValueError("provider endpoint identity differs from preregistration")
        if int(generation["provider_max_attempts_per_call"]) != int(
            provider_registration["max_attempts_per_call"]
        ):
            raise ValueError("provider retry identity is internally inconsistent")
        CONFIG.llm.stage_temperatures = dict(generation["temperature"])
        CONFIG.llm.temperature = float(generation["temperature"]["interface"])
        CONFIG.llm.max_output_tokens = int(generation["max_completion_tokens"])
        CONFIG.llm.reasoning_effort = str(generation["reasoning_effort"])
        CONFIG.llm.stream_responses = bool(generation["stream_responses"])
        CONFIG.llm.transport_route_policy = expected_route_policy
        CONFIG.llm.max_retries = int(generation["provider_max_attempts_per_call"])
        CONFIG.llm.transport_retry_delays_seconds = list(
            provider_registration["transport_retry_delays_seconds"]
        )
        CONFIG.llm.request_timeout_seconds = float(
            provider_registration["request_timeout_seconds"]
        )
        CONFIG.llm.strict_json_schema = True
        CONFIG.constraint_engine.backend = "neo4j"
        CONFIG.constraint_engine.enabled = True
        retrieval_contract = generation["constraint_retrieval"]
        CONFIG.constraint_engine.max_constraints_interface = int(
            retrieval_contract["max_constraints_interface"]
        )
        CONFIG.constraint_engine.max_constraints_component = int(
            retrieval_contract["max_constraints_component"]
        )
        CONFIG.constraint_engine.per_family_limit = int(
            retrieval_contract["per_family_limit"]
        )
        CONFIG.validation.auto_repair_enabled = False
        CONFIG.validation.enabled = True
        CONFIG.validation.xsd_enabled = True
        CONFIG.validation.reference_scope = str(
            formal_contract["validation"]["reference_scope"]
        )
        CONFIG.validation.plan_path = (
            "src/generate_formal_constraints/v2/validation_plan.json"
        )
        CONFIG.validation.xsd_path = "src/validation/data/AUTOSAR_4-2-2.xsd"
        CONFIG.validation.xsd_serialization_manifest_path = (
            "src/llm_generation/knowledge/v2/xsd_serialization_manifest.json"
        )
        retrieval_manifest = json.loads(
            (ATLAS_ROOT / "src/llm_generation/knowledge/v2/retrieval_manifest.json")
            .read_text(encoding="utf-8")
        )
        expected_neo4j_context = json.loads(
            (Path(__file__).resolve().parent / "FORMAL_NEO4J_CONTEXT.json")
            .read_text(encoding="utf-8")
        )
        neo4j_preflight = (
            None
            if args.offline_scripted
            else _preflight_formal_neo4j(
                CONFIG,
                retrieval_manifest["dataset_sha256"],
                int(retrieval_manifest["card_count"]),
                expected_neo4j_context,
            )
        )
        if args.offline_scripted:
            # The offline path exercises the real runner, schema projection and
            # serializer with a deterministic client. It verifies the frozen
            # Neo4j identity through the freeze manifest but performs no live
            # external-system access of any kind.
            CONFIG.constraint_engine.enabled = False
    else:
        neo4j_preflight = None
        if args.offline_scripted:
            CONFIG.llm.max_retries = 1
            CONFIG.llm.request_timeout_seconds = 180.0
            CONFIG.llm.stream_responses = False
            CONFIG.llm.strict_json_schema = True
            CONFIG.validation.enabled = True
            CONFIG.validation.xsd_enabled = True
            CONFIG.validation.reference_scope = "complete"
    CONFIG.output_dir = run_root / "atlas_output"
    CONFIG.output_dir.mkdir(parents=True, exist_ok=True)

    from llm_rag_generator_auto import LLMRAGGenerator

    if formal_contract is not None and not args.offline_scripted:
        from src.llm_generation.knowledge.dynamic_query_engine import query_engine

        if query_engine.driver is None:
            raise RuntimeError(
                "formal Phase 2 schema assembly requires a live Neo4j driver"
            )

    generator = LLMRAGGenerator()
    concrete_clients = (
        generator.conversation_manager.round1_designer.gemini_client,
        generator.conversation_manager.round2_generator.gemini_client,
    )
    if any(int(client.client.max_retries) != 0 for client in concrete_clients):
        raise RuntimeError("provider SDK implicit retry invariant failed at startup")
    expected_route_policy = (
        str(formal_contract["generation"]["transport_route_policy"])
        if formal_contract is not None
        else "direct_no_environment_proxy"
    )
    if any(
        getattr(client, "transport_route_policy", None) != expected_route_policy
        for client in concrete_clients
    ):
        raise RuntimeError("provider route policy invariant failed at startup")
    scripted_client = None
    if args.offline_scripted:
        from scripted_autosar_client import ScriptedAutosarClient

        scripted_client = ScriptedAutosarClient(
            args.case_id,
            cohort=source_cohort,
            requested_model=args.model,
            fail_stage=args.scripted_fail_stage,
            max_attempts=(
                int(formal_contract["generation"]["provider_max_attempts_per_call"])
                if formal_contract is not None
                else 1
            ),
        )
        generator.conversation_manager.round1_designer.gemini_client = scripted_client
        generator.conversation_manager.round2_generator.gemini_client = scripted_client
    generator.generated_arxml_dir = run_root / "generated_arxml"
    generator.metrics_dir = run_root / "metrics"
    generator.generated_arxml_dir.mkdir(parents=True, exist_ok=True)
    generator.metrics_dir.mkdir(parents=True, exist_ok=True)
    result = generator._process_single_requirement(
        requirement=_requirement(
            args.case_id, run_definition["seed"], source_cohort
        ),
        complexity=(
            f"asw_v3_{args.cohort}_{run_definition['case']['tier']}_r{args.repetition}_"
            f"repair_{args.repair_mode}"
        ),
        index=run_definition["case_index"],
    )
    provider_audits = [
        *((result.get("phase1") or {}).get("provider_responses") or []),
        *((result.get("phase2") or {}).get("provider_responses") or []),
    ]
    allowed_phases = {
        "round1", "round2.interface", "round2.component", "round2.repair"
    }
    provider_max_attempts = (
        int(formal_contract["generation"]["provider_max_attempts_per_call"])
        if formal_contract is not None
        else 1
    )
    if formal_contract is not None and any(
        not item.get("provider_call_id")
        or not item.get("logical_request_id")
        or item.get("pipeline_phase") not in allowed_phases
        or int(item.get("logical_call_index") or 0) < 1
        or not 1 <= int(item.get("transport_attempt") or 0) <= provider_max_attempts
        or int(item.get("sdk_attempt") or 0) != 1
        or int(item.get("max_attempts") or 0) != provider_max_attempts
        or (
            item.get("transport_route_policy")
            != (
                "offline_scripted_no_network"
                if args.offline_scripted
                else expected_route_policy
            )
        )
        for item in provider_audits
    ):
        raise RuntimeError("formal provider audit identity/phase invariant failed")
    transport_continuation = _transport_continuation_audit(
        run_root / "provider_call_transitions.jsonl",
        max_attempts=provider_max_attempts,
    )
    if (
        formal_contract is not None
        and not args.offline_scripted
        and transport_continuation.get("decision") != "PASS"
    ):
        raise RuntimeError("formal transport-continuation audit did not pass")
    provider_runtime_gate = {
        "decision": "PASS",
        "sdk_implicit_max_retries": [
            int(client.client.max_retries) for client in concrete_clients
        ],
        "concrete_transport_route_policies": [
            str(client.transport_route_policy) for client in concrete_clients
        ],
        "observed_audit_transport_route_policies": sorted({
            str(item.get("transport_route_policy")) for item in provider_audits
        }),
        "allowed_pipeline_phases": sorted(allowed_phases),
        "observed_pipeline_phases": sorted({
            str(item.get("pipeline_phase")) for item in provider_audits
        }),
        "all_provider_calls_have_identity": all(
            bool(item.get("provider_call_id")) for item in provider_audits
        ),
        "all_provider_calls_have_logical_request_identity": all(
            bool(item.get("logical_request_id")) for item in provider_audits
        ),
        "transport_continuation": transport_continuation,
    }
    if formal_contract is not None and not args.offline_scripted:
        neo4j_postflight = _preflight_formal_neo4j(
            CONFIG,
            retrieval_manifest["dataset_sha256"],
            int(retrieval_manifest["card_count"]),
            expected_neo4j_context,
        )
        if neo4j_postflight != neo4j_preflight:
            raise RuntimeError(
                "formal Neo4j context changed between Phase 1/2 preflight and postflight"
            )
    else:
        neo4j_postflight = None
    summary = {
        "case_id": args.case_id,
        "cohort": args.cohort,
        "source_cohort": source_cohort,
        "structural_role": run_definition["case"].get("structural_role"),
        "model": args.model,
        "case_index": run_definition["case_index"],
        "tier": run_definition["case"]["tier"],
        "repetition": args.repetition,
        "seed": run_definition["seed"],
        "repair_mode": args.repair_mode,
        "requirement_source_canonical_sha256": run_definition[
            "source_canonical_sha256"
        ],
        "case_sha256": run_definition["case_sha256"],
        "freeze_manifest_sha256": (
            freeze_verification["manifest_sha256"]
            if freeze_verification is not None else args.expected_freeze_sha256
        ),
        "freeze_manifest_file_sha256": (
            freeze_verification["manifest_file_sha256"]
            if freeze_verification is not None else args.expected_freeze_file_sha256
        ),
        "experiment_contract_sha256": (
            freeze_verification["experiment_contract_sha256"]
            if freeze_verification is not None else args.expected_contract_sha256
        ),
        "neo4j_context_sha256": (
            freeze_verification["neo4j_context_sha256"]
            if freeze_verification is not None else args.expected_neo4j_context_sha256
        ),
        "schedule_content_sha256": args.expected_schedule_sha256,
        "attempt_number": args.attempt_number,
        "offline_scripted": args.offline_scripted,
        "scripted_fail_stage": args.scripted_fail_stage,
        "offline_scripted_provider_call_count": (
            scripted_client.call_count if scripted_client is not None else None
        ),
        "external_model_api_calls": 0 if args.offline_scripted else None,
        "provider_runtime_gate": provider_runtime_gate,
        "formal_neo4j_preflight": neo4j_preflight,
        "formal_neo4j_postflight": neo4j_postflight,
        "system_name": result.get("system_name"),
        "final_status": result.get("final_status"),
        "phase1": {
            key: (result.get("phase1") or {}).get(key)
            for key in (
                "duration", "tokens", "component_count", "interface_count",
                "provider_responses",
                "provider_counters",
            )
        },
        "phase2": {
            key: (result.get("phase2") or {}).get(key)
            for key in (
                "duration", "tokens", "output_files", "status",
                "validation_decision", "validation_summary",
                "artifact_profile_decision", "artifact_profile",
                "provider_responses",
                "provider_counters",
                "provider_payload_provenance",
                "provider_payload_status_counters",
                "raw_provider_schema_status",
                "normalization_status",
                "final_atlas_status",
                "typed_repair_context",
            )
        },
        "error": result.get("error"),
        "completed_at_utc": datetime.now(timezone.utc).replace(
            microsecond=0
        ).isoformat().replace("+00:00", "Z"),
    }
    artifact_hashes = {}
    for path in sorted(item for item in run_root.rglob("*") if item.is_file()):
        if path.name == "run_summary.json":
            continue
        artifact_hashes[path.relative_to(run_root).as_posix()] = _sha256_file(path)
    summary["artifact_hashes"] = artifact_hashes
    summary_path = run_root / "run_summary.json"
    from experiment_runtime import atomic_write_json

    atomic_write_json(summary_path, summary)
    summary["run_summary_path"] = str(summary_path)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    completed_statuses = {
        "success",
        "generated_with_validation_errors",
        "generated_with_incomplete_validation",
    }
    return 0 if result.get("final_status") in completed_statuses and not result.get("error") else 1


if __name__ == "__main__":
    raise SystemExit(main())
