"""Deterministic execution adapter for the admitted AUTOSAR held-out V3 source.

The review package deliberately uses paper-facing terminology and records the
V15 comparison design.  The Phase 1/2 runner uses the older internal
``provided_signals``/``required_signals`` vocabulary.  This module is the only
translation boundary between those representations.  It validates the exact
review source before translating it and never reads model outputs.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import yaml


HELDOUT_ROOT = Path(r"E:\54239\Documents\atlas_autosar_heldout_v3")
SOURCE = HELDOUT_ROOT / "heldout_cases.yaml"
EXPECTED_SOURCE_SHA256 = (
    "78dc6d65672d896af3c19b50a5efbf5ca18d8237de9f32f2b7234cd6ff226945"
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def event_short_name(runnable_short_name: str) -> str:
    stem = str(runnable_short_name).strip()
    return f"TE_{stem[3:] if stem.startswith('RE_') else stem}"


def variable_access_short_name(
    runnable_short_name: str, direction: str, data_element: str
) -> str:
    stem = str(runnable_short_name).strip()
    if stem.startswith("RE_"):
        stem = stem[3:]
    operation = {"read": "Read", "write": "Write"}.get(str(direction).lower())
    if operation is None:
        raise ValueError(f"unsupported variable-access direction: {direction}")
    return f"VA_{stem}_{operation}_{str(data_element).strip()}"


def _load_review_source() -> dict[str, Any]:
    if sha256_file(SOURCE) != EXPECTED_SOURCE_SHA256:
        raise ValueError("held-out V3 source file hash differs from the admitted candidate")
    value = yaml.safe_load(SOURCE.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("held-out V3 source must be an object")
    if str(HELDOUT_ROOT) not in sys.path:
        sys.path.insert(0, str(HELDOUT_ROOT))
    from validate_heldout import validate

    result = validate(value, source=SOURCE)
    if result.get("decision") != "PASS":
        raise ValueError("held-out V3 source failed its local admission validator")
    return value


def _runtime_context(source: dict[str, Any]) -> dict[str, Any]:
    original = source["authoritative_context"]
    init = original["unconnected_required_port_init_value"]
    return {
        **original,
        "unconnected_required_port_init_value": init["value"],
        "init_value_policy": (
            "Every unconnected required sender-receiver port uses the source-owned "
            f"{init['value_specification']} value {init['value']}."
        ),
        "component_output_policy": (
            "Generate the requested component and sender-receiver interfaces; exact "
            "implementation-data-type references are source-owned obligations."
        ),
        "validation_evidence_profile": {
            "profile_id": "autosar_component_arxml_only_v1",
            "manual_evidence_scope_complete": True,
            "manual_capabilities_out_of_scope": [
                "external_antecedent",
                "external_design_evidence",
                "generated_artifact",
                "runtime_evidence",
            ],
        },
    }


def _runtime_case(case: dict[str, Any]) -> dict[str, Any]:
    behavior = case.get("internal_behavior")
    normalized_behavior = None
    if behavior is not None:
        normalized_behavior = {
            "short_name": behavior["short_name"],
            "runnables": [
                {
                    "short_name": runnable["short_name"],
                    "period_s": runnable["period_s"],
                    "reads": list(
                        runnable.get("data_receive_point_by_arguments") or []
                    ),
                    "writes": list(runnable.get("data_send_points") or []),
                }
                for runnable in behavior["runnables"]
            ],
        }
    return {
        "case_id": case["case_id"],
        "tier": case["tier"],
        "structural_role": case["structural_role"],
        "v15_relation": case["v15_relation"],
        "component": case["component"],
        "intent": case["intent"],
        "provided_signals": list(case.get("provided_data_elements") or []),
        "required_signals": [
            {
                "signal": item["data_element"],
                "alive_timeout_s": item["alive_timeout_s"],
                "handle_timeout_type": item["handle_timeout_type"],
            }
            for item in case.get("required_data_elements") or []
        ],
        "internal_behavior": normalized_behavior,
        "expected_counts": dict(case["expected_counts"]),
        "review_source_case_sha256": canonical_sha256(case),
    }


def load_manifest() -> dict[str, Any]:
    """Return the validated source projected into the Phase 1/2 runtime shape."""

    source = _load_review_source()
    return {
        "schema_version": "atlas.autosar.heldout.runtime_projection.v1",
        "metadata": dict(source["metadata"]),
        "experiment_design": dict(source["experiment_design"]),
        "authoritative_context": _runtime_context(source),
        "cases": [_runtime_case(case) for case in source["cases"]],
        "review_source_file_sha256": sha256_file(SOURCE),
        "review_source_canonical_sha256": canonical_sha256(source),
    }


def validate_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    expected = load_manifest()
    if manifest != expected:
        raise ValueError("held-out runtime projection differs from the validated source")
    return {
        "status": "PASS",
        "case_count": len(manifest["cases"]),
        "run_count": manifest["experiment_design"]["run_count"],
        "source_sha256": manifest["review_source_file_sha256"],
        "external_model_api_calls": 0,
    }


def render_prompt(manifest: dict[str, Any], case: dict[str, Any]) -> str:
    """Render every held-out obligation, including exact data-type references."""

    validate_manifest(manifest)
    context = manifest["authoritative_context"]
    catalog = context["interface_catalog"]
    lines = [
        "Generate one AUTOSAR Classic Platform 4.2.2 ARXML document for the "
        "prospective internally-authored component requirement below.",
        "This is a component-level evaluation, not an ECU or network configuration.",
        "The named interface, data-element, port, runnable, and event identities are "
        "requirement-owned. Do not add, omit, duplicate, or rename them.",
        "",
        f"Case ID: {case['case_id']}",
        f"Component: APPLICATION-SW-COMPONENT-TYPE {case['component']}",
        f"Factorial cell: tier={case['tier']}; V15 topology relation={case['structural_role']}",
        f"Intent: {case['intent']}",
        "",
        "Ports, interfaces, data elements, and exact implementation data types:",
    ]
    for signal in case.get("provided_signals") or []:
        item = catalog[signal]
        lines.append(
            f"- P-PORT-PROTOTYPE Pp_{signal}: {item['interface_ref']}/"
            f"{item['data_element']}; TYPE-TREF {item['type_ref']} "
            f"(DEST={item['type_dest']})."
        )
    for spec in case.get("required_signals") or []:
        signal = spec["signal"]
        item = catalog[signal]
        lines.append(
            f"- R-PORT-PROTOTYPE Rp_{signal}: {item['interface_ref']}/"
            f"{item['data_element']}; TYPE-TREF {item['type_ref']} "
            f"(DEST={item['type_dest']}); NONQUEUED-RECEIVER-COM-SPEC "
            f"ALIVE-TIMEOUT={spec['alive_timeout_s']}, HANDLE-TIMEOUT-TYPE="
            f"{spec['handle_timeout_type']}, INIT-VALUE/NUMERICAL-VALUE-"
            "SPECIFICATION/VALUE=0."
        )
    behavior = case.get("internal_behavior")
    if behavior is None:
        lines.extend(
            [
                "",
                "Do not create an SWC-INTERNAL-BEHAVIOR, RUNNABLE-ENTITY, or event.",
            ]
        )
    else:
        lines.extend(
            [
                "",
                f"SWC-INTERNAL-BEHAVIOR {behavior['short_name']}:",
            ]
        )
        for runnable in behavior["runnables"]:
            lines.append(
                f"- RUNNABLE-ENTITY {runnable['short_name']} with exactly one TIMING-"
                f"EVENT {event_short_name(runnable['short_name'])} at "
                f"{runnable['period_s']} seconds."
            )
            for signal in runnable["reads"]:
                lines.append(
                    f"  - DATA-RECEIVE-POINT-BY-ARGUMENTS VARIABLE-ACCESS "
                    f"{variable_access_short_name(runnable['short_name'], 'read', signal)} "
                    f"reads Rp_{signal}/{catalog[signal]['data_element']}."
                )
            for signal in runnable["writes"]:
                lines.append(
                    f"  - DATA-SEND-POINTS VARIABLE-ACCESS "
                    f"{variable_access_short_name(runnable['short_name'], 'write', signal)} "
                    f"writes Pp_{signal}/{catalog[signal]['data_element']}."
                )
    expected = case["expected_counts"]
    lines.extend(
        [
            "",
            "Deterministic counts:",
            f"- P ports={expected['p_ports']}; R ports={expected['r_ports']}; "
            f"runnables={expected['runnables']}; timing events="
            f"{expected['timing_events']}; variable accesses="
            f"{expected['variable_accesses']}.",
            "- Use the AUTOSAR 4.2.2 namespace, valid DEST values and XSD order.",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def case_record(case_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest = load_manifest()
    matches = [case for case in manifest["cases"] if case["case_id"] == case_id]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one held-out V3 case named {case_id!r}")
    return manifest, matches[0]
