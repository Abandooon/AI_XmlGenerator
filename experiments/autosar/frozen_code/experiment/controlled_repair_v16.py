"""Frozen applicability and mutation-task design for V16 controlled repair.

The design is derived only from the pinned requirement cases.  It retains the
five fixed-operator applicability ledger (including all NOT_APPLICABLE cells),
keeps the 85 applicable fixed-operator tasks as the core layer, and replaces
the 15 inapplicable cells with predeclared case-applicable mutations in a
separate substitution layer.  No generation result is inspected.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parent
REQUIREMENTS_PATH = Path(
    r"E:\54239\Documents\atlas_autosar_requirements_v3\asw_cases_v3.yaml"
)

CORE_OPERATORS = (
    "empty_init_value",
    "wrong_init_value",
    "missing_event_behavior_path",
    "missing_required_comspec",
    "wrong_xsd_order",
)

SUBSTITUTE_OPERATORS = (
    "empty_provided_interface_ref",
    "wrong_provided_interface_ref",
    "missing_provided_port",
    "missing_component_short_name",
    "missing_required_interface_ref",
)

EXPECTED_CORE_DENOMINATORS = {
    "empty_init_value": 17,
    "wrong_init_value": 17,
    "missing_event_behavior_path": 14,
    "missing_required_comspec": 17,
    "wrong_xsd_order": 20,
}


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _applicability(case: dict[str, Any], operator: str) -> tuple[bool, str]:
    has_required_port = bool(case.get("required_signals"))
    behavior = case.get("internal_behavior") or {}
    has_runnable = bool(behavior.get("runnables"))
    if operator in {
        "empty_init_value",
        "wrong_init_value",
        "missing_required_comspec",
    }:
        return (
            has_required_port,
            "requires at least one requirement-declared R port with a receiver com-spec",
        )
    if operator == "missing_event_behavior_path":
        return (
            has_runnable,
            "requires at least one requirement-declared runnable and event",
        )
    if operator == "wrong_xsd_order":
        return True, "component SHORT-NAME and PORTS are XSD-ordered in every case"
    raise ValueError(f"unknown core operator: {operator}")


def _substitute(case: dict[str, Any], operator: str) -> str:
    """Return the frozen substitute for one inapplicable core cell."""
    has_required_port = bool(case.get("required_signals"))
    has_provided_port = bool(case.get("provided_signals"))
    if operator == "empty_init_value" and has_provided_port:
        return "empty_provided_interface_ref"
    if operator == "wrong_init_value" and has_provided_port:
        return "wrong_provided_interface_ref"
    if operator == "missing_required_comspec" and has_provided_port:
        return "missing_provided_port"
    if operator == "missing_event_behavior_path":
        if has_required_port:
            return "missing_required_interface_ref"
        if has_provided_port:
            return "missing_component_short_name"
    raise ValueError(
        f"no deterministic substitute for {case.get('case_id')}:{operator}"
    )


def build_mutation_schedule(requirements: dict[str, Any]) -> dict[str, Any]:
    cases = list(requirements.get("cases") or [])
    if len(cases) != 20 or len({case["case_id"] for case in cases}) != 20:
        raise ValueError("V16 controlled repair requires exactly 20 unique cases")
    ledger: list[dict[str, Any]] = []
    tasks: list[dict[str, Any]] = []
    for case in sorted(cases, key=lambda item: item["case_id"]):
        case_id = str(case["case_id"])
        case_sha256 = canonical_sha256(case)
        for operator in CORE_OPERATORS:
            applicable, precondition = _applicability(case, operator)
            ledger.append(
                {
                    "case_id": case_id,
                    "case_sha256": case_sha256,
                    "operator": operator,
                    "applicability": "APPLICABLE" if applicable else "NOT_APPLICABLE",
                    "precondition": precondition,
                }
            )
            effective = operator if applicable else _substitute(case, operator)
            layer = "core_fixed_operator" if applicable else "substitution"
            tasks.append(
                {
                    "task_id": f"{case_id}__{operator}",
                    "case_id": case_id,
                    "case_sha256": case_sha256,
                    "base_operator": operator,
                    "applicability": "APPLICABLE" if applicable else "NOT_APPLICABLE",
                    "effective_mutation": effective,
                    "analysis_layer": layer,
                    "derivation": (
                        "fixed operator"
                        if applicable
                        else "predeclared requirement/XSD-derived substitute"
                    ),
                }
            )

    denominators = {
        operator: sum(
            item["operator"] == operator and item["applicability"] == "APPLICABLE"
            for item in ledger
        )
        for operator in CORE_OPERATORS
    }
    not_applicable = {
        operator: 20 - denominators[operator] for operator in CORE_OPERATORS
    }
    if denominators != EXPECTED_CORE_DENOMINATORS:
        raise ValueError(f"controlled-repair applicability drift: {denominators}")
    if len(ledger) != 100 or len(tasks) != 100:
        raise ValueError("controlled-repair design must contain 20 x 5 cells/tasks")
    if sum(denominators.values()) != 85 or sum(not_applicable.values()) != 15:
        raise ValueError("controlled-repair core/substitution split must be 85/15")
    if len({item["task_id"] for item in tasks}) != 100:
        raise ValueError("controlled-repair task IDs are not unique")

    body: dict[str, Any] = {
        "schema_version": "atlas.autosar.v16.controlled_repair_design.v1",
        "source_policy": "pinned requirements and XSD/contract only; no generation-result selection",
        "requirements_canonical_sha256": canonical_sha256(requirements),
        "case_count": 20,
        "design_cell_count": 100,
        "scheduled_task_count": 100,
        "core_fixed_operator_task_count": 85,
        "substitution_task_count": 15,
        "core_repair_rate_denominators": denominators,
        "not_applicable_counts": not_applicable,
        "denominator_policy": (
            "NOT_APPLICABLE cells remain in the applicability ledger but are "
            "excluded from that core operator's repair-rate denominator; "
            "substitution tasks are reported in a separate layer"
        ),
        "applicability_ledger": ledger,
        "tasks": tasks,
    }
    body["content_sha256"] = canonical_sha256(body)
    return body


def verify_mutation_schedule(
    schedule: dict[str, Any], requirements: dict[str, Any]
) -> dict[str, Any]:
    expected = build_mutation_schedule(requirements)
    if schedule != expected:
        raise ValueError("controlled-repair mutation schedule differs from requirements")
    unsigned = {key: value for key, value in schedule.items() if key != "content_sha256"}
    if canonical_sha256(unsigned) != schedule.get("content_sha256"):
        raise ValueError("controlled-repair mutation schedule hash mismatch")
    return schedule


def load_requirements(path: Path = REQUIREMENTS_PATH) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("requirements document must be an object")
    return value


if __name__ == "__main__":
    print(json.dumps(build_mutation_schedule(load_requirements()), ensure_ascii=False, indent=2))
