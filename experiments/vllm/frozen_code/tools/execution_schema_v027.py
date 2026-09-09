"""Build finite, assertion-only JSON Schemas for ATLAS constrained decoding."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any

EXECUTION_SCHEMA_VERSION = "atlas.vllm.uga.execution_schema.v1"
JSON_SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"

_ASSERTION_KEYS = {
    "$anchor",
    "$defs",
    "$dynamicAnchor",
    "$dynamicRef",
    "$id",
    "$ref",
    "$schema",
    "additionalItems",
    "additionalProperties",
    "allOf",
    "anyOf",
    "const",
    "contains",
    "dependentRequired",
    "dependentSchemas",
    "else",
    "enum",
    "exclusiveMaximum",
    "exclusiveMinimum",
    "format",
    "if",
    "items",
    "maxContains",
    "maxItems",
    "maxLength",
    "maxProperties",
    "maximum",
    "minContains",
    "minItems",
    "minLength",
    "minProperties",
    "minimum",
    "multipleOf",
    "not",
    "oneOf",
    "pattern",
    "patternProperties",
    "prefixItems",
    "properties",
    "propertyNames",
    "required",
    "then",
    "type",
    "unevaluatedItems",
    "unevaluatedProperties",
    "uniqueItems",
}
_NAMED_SCHEMA_MAPS = {"$defs", "definitions", "properties", "patternProperties"}
_OBLIGATION_PATTERN = re.compile(
    r"Exactly\s+(?P<p>\d+)\s+P ports,\s*"
    r"(?P<r>\d+)\s+R ports,\s*"
    r"(?P<runnables>\d+)\s+runnables,\s*"
    r"(?P<timing>\d+)\s+timing events,\s*and\s*"
    r"(?P<accesses>\d+)\s+variable accesses\."
)
_RUNNABLE_PATTERN = re.compile(r"^- RUNNABLE-ENTITY\s+(?P<name>\S+)\b")


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


def parse_requirement_cardinalities(requirement_text: str) -> dict[str, Any]:
    match = _OBLIGATION_PATTERN.search(requirement_text)
    if match is None:
        raise ValueError("deterministic_cardinality_obligation_missing")
    counts = {key: int(value) for key, value in match.groupdict().items()}
    runnable_accesses: list[dict[str, Any]] = []
    observed_p_ports = 0
    observed_r_ports = 0
    observed_timing_events = 0
    current: dict[str, Any] | None = None
    for raw_line in requirement_text.splitlines():
        line = raw_line.strip()
        if line.startswith("- P-PORT-PROTOTYPE "):
            observed_p_ports += 1
        elif line.startswith("- R-PORT-PROTOTYPE "):
            observed_r_ports += 1
        runnable_match = _RUNNABLE_PATTERN.match(line)
        if runnable_match is not None:
            if "TIMING-EVENT" in line:
                observed_timing_events += 1
            current = {
                "name": runnable_match.group("name"),
                "reads": 0,
                "writes": 0,
            }
            runnable_accesses.append(current)
            continue
        if line.startswith("Deterministic obligations:"):
            current = None
        elif current is not None and line.startswith("- Read "):
            current["reads"] += 1
        elif current is not None and line.startswith("- Write "):
            current["writes"] += 1

    if len(runnable_accesses) != counts["runnables"]:
        raise ValueError("runnable_count_disagrees_with_deterministic_obligation")
    if observed_p_ports != counts["p"]:
        raise ValueError("p_port_count_disagrees_with_deterministic_obligation")
    if observed_r_ports != counts["r"]:
        raise ValueError("r_port_count_disagrees_with_deterministic_obligation")
    if observed_timing_events != counts["timing"]:
        raise ValueError("timing_event_count_disagrees_with_obligation")
    observed_accesses = sum(
        item["reads"] + item["writes"] for item in runnable_accesses
    )
    if observed_accesses != counts["accesses"]:
        raise ValueError("variable_access_count_disagrees_with_obligation")
    counts["runnable_accesses"] = runnable_accesses
    return counts


def _strip_non_assertions(value: Any, path: tuple[str, ...], stats: dict[str, int]) -> Any:
    if isinstance(value, list):
        return [_strip_non_assertions(item, path, stats) for item in value]
    if not isinstance(value, dict):
        return copy.deepcopy(value)

    cleaned: dict[str, Any] = {}
    for key, item in value.items():
        if key not in _ASSERTION_KEYS and key not in _NAMED_SCHEMA_MAPS:
            stats["removed_keyword_count"] += 1
            continue
        if key in _NAMED_SCHEMA_MAPS and isinstance(item, dict):
            cleaned[key] = {
                name: _strip_non_assertions(schema, path + (key, name), stats)
                for name, schema in item.items()
            }
        else:
            cleaned[key] = _strip_non_assertions(item, path + (key,), stats)
    return cleaned


def _array_role(path: tuple[str, ...]) -> str | None:
    if path[-2:] == ("properties", "P-PORT-PROTOTYPE"):
        return "p_ports"
    if path[-2:] == ("properties", "R-PORT-PROTOTYPE"):
        return "r_ports"
    if path[-2:] == ("properties", "NONQUEUED-RECEIVER-COM-SPEC"):
        return "receiver_com_specs"
    if path[-2:] == ("properties", "TIMING-EVENT"):
        return "timing_events"
    if path[-2:] == ("properties", "RUNNABLE-ENTITY"):
        return "runnables"
    if path[-4:] == (
        "properties",
        "DATA-RECEIVE-POINT-BY-ARGUMENTS",
        "properties",
        "VARIABLE-ACCESS",
    ):
        return "reads_per_runnable"
    if path[-4:] == (
        "properties",
        "DATA-SEND-POINTS",
        "properties",
        "VARIABLE-ACCESS",
    ):
        return "writes_per_runnable"
    return None


def _bounds_for_role(role: str, cardinalities: Mapping[str, Any]) -> tuple[int, int]:
    exact_roles = {
        "p_ports": int(cardinalities["p"]),
        "r_ports": int(cardinalities["r"]),
        "receiver_com_specs": 1,
        "timing_events": int(cardinalities["timing"]),
        "runnables": int(cardinalities["runnables"]),
    }
    if role in exact_roles:
        value = exact_roles[role]
        return value, value
    field = "reads" if role == "reads_per_runnable" else "writes"
    values = [
        int(item[field]) for item in cardinalities["runnable_accesses"]
    ]
    if not values:
        raise ValueError(f"array_role_has_no_runnable_cardinality:{role}")
    return min(values), max(values)


def _apply_finite_array_bounds(
    schema: Any,
    cardinalities: Mapping[str, Any],
    path: tuple[str, ...],
    report: list[dict[str, Any]],
) -> None:
    if isinstance(schema, list):
        for index, item in enumerate(schema):
            _apply_finite_array_bounds(
                item, cardinalities, path + (str(index),), report
            )
        return
    if not isinstance(schema, dict):
        return
    if schema.get("type") == "array":
        role = _array_role(path)
        if role is None:
            raise ValueError(f"unclassified_array_schema:{'/'.join(path)}")
        minimum, maximum = _bounds_for_role(role, cardinalities)
        schema["minItems"] = minimum
        schema["maxItems"] = maximum
        report.append(
            {
                "schema_path": "/" + "/".join(path),
                "role": role,
                "minItems": minimum,
                "maxItems": maximum,
            }
        )
    for key, item in schema.items():
        _apply_finite_array_bounds(item, cardinalities, path + (key,), report)


def harden_execution_schema(
    source_schema: Mapping[str, Any],
    requirement_text: str,
    *,
    case_id: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Remove annotation bulk and make every generated array finite."""

    if not isinstance(source_schema, Mapping) or not source_schema:
        raise ValueError("source_schema_must_be_a_nonempty_object")
    cardinalities = parse_requirement_cardinalities(requirement_text)
    stats = {"removed_keyword_count": 0}
    execution_schema = _strip_non_assertions(dict(source_schema), (), stats)
    if not isinstance(execution_schema, dict):
        raise AssertionError("cleaned_schema_root_is_not_an_object")
    execution_schema["$schema"] = JSON_SCHEMA_DIALECT
    array_bounds: list[dict[str, Any]] = []
    _apply_finite_array_bounds(execution_schema, cardinalities, (), array_bounds)
    if not array_bounds:
        raise ValueError("execution_schema_contains_no_bounded_arrays")
    unbounded: list[str] = []

    def find_unbounded(value: Any, path: tuple[str, ...] = ()) -> None:
        if isinstance(value, dict):
            if value.get("type") == "array" and (
                "minItems" not in value or "maxItems" not in value
            ):
                unbounded.append("/" + "/".join(path))
            for key, item in value.items():
                find_unbounded(item, path + (key,))
        elif isinstance(value, list):
            for index, item in enumerate(value):
                find_unbounded(item, path + (str(index),))

    find_unbounded(execution_schema)
    if unbounded:
        raise ValueError(f"execution_schema_has_unbounded_arrays:{unbounded}")
    report = {
        "schema_version": EXECUTION_SCHEMA_VERSION,
        "case_id": case_id,
        "source_schema_sha256": canonical_sha256(source_schema),
        "execution_schema_sha256": canonical_sha256(execution_schema),
        "source_schema_character_count": len(
            canonical_json_bytes(source_schema).decode("utf-8")
        ),
        "execution_schema_character_count": len(
            canonical_json_bytes(execution_schema).decode("utf-8")
        ),
        "removed_keyword_count": stats["removed_keyword_count"],
        "cardinalities": cardinalities,
        "array_bounds": array_bounds,
    }
    return execution_schema, report


def _string_witness(schema: Mapping[str, Any]) -> str:
    if "const" in schema:
        return str(schema["const"])
    enum = schema.get("enum")
    if isinstance(enum, list) and enum:
        return str(enum[0])
    pattern = str(schema.get("pattern") or "")
    component_prefix = re.fullmatch(r"\^(/Components/[^*]+/)\.\*\$", pattern)
    if component_prefix is not None:
        return component_prefix.group(1) + "A"
    return "A"


def synthesize_witness(schema: Mapping[str, Any]) -> Any:
    if "const" in schema:
        return copy.deepcopy(schema["const"])
    enum = schema.get("enum")
    if isinstance(enum, list) and enum:
        return copy.deepcopy(enum[0])
    if "allOf" in schema:
        merged: dict[str, Any] = {}
        for branch in schema["allOf"]:
            value = synthesize_witness(branch)
            if isinstance(value, dict):
                merged.update(value)
        return merged
    for union_key in ("oneOf", "anyOf"):
        if union_key in schema:
            return synthesize_witness(schema[union_key][0])
    value_type = schema.get("type")
    if isinstance(value_type, list):
        value_type = next((item for item in value_type if item != "null"), "null")
    if value_type == "object" or "properties" in schema:
        properties = schema.get("properties") or {}
        return {
            name: synthesize_witness(properties[name])
            for name in schema.get("required") or []
        }
    if value_type == "array":
        count = int(schema.get("minItems", 0))
        return [synthesize_witness(schema.get("items") or {}) for _ in range(count)]
    if value_type == "string":
        return _string_witness(schema)
    if value_type == "integer":
        return int(schema.get("minimum", 0))
    if value_type == "number":
        return float(schema.get("minimum", 0))
    if value_type == "boolean":
        return False
    if value_type == "null":
        return None
    return None


def _first_array_location(
    schema: Mapping[str, Any],
    instance: Any,
    *,
    require_positive_minimum: bool,
    path: tuple[Any, ...] = (),
) -> tuple[tuple[Any, ...], Mapping[str, Any]] | None:
    if schema.get("type") == "array" and isinstance(instance, list):
        if not require_positive_minimum or int(schema.get("minItems", 0)) > 0:
            return path, schema
        items = schema.get("items") or {}
        for index, item in enumerate(instance):
            found = _first_array_location(
                items,
                item,
                require_positive_minimum=require_positive_minimum,
                path=path + (index,),
            )
            if found is not None:
                return found
    properties = schema.get("properties") or {}
    if isinstance(instance, dict):
        for name, child_schema in properties.items():
            if name in instance:
                found = _first_array_location(
                    child_schema,
                    instance[name],
                    require_positive_minimum=require_positive_minimum,
                    path=path + (name,),
                )
                if found is not None:
                    return found
    return None


def _at_path(instance: Any, path: tuple[Any, ...]) -> Any:
    current = instance
    for part in path:
        current = current[part]
    return current


def build_witness_matrix(schema: Mapping[str, Any]) -> dict[str, Any]:
    """Prove valid acceptance and representative assertion rejections."""

    from jsonschema import Draft202012Validator

    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    valid = synthesize_witness(schema)
    valid_errors = list(validator.iter_errors(valid))
    if valid_errors:
        raise ValueError(f"synthesized_witness_is_invalid:{valid_errors[0].message}")

    required = list(schema.get("required") or [])
    if not required or not isinstance(valid, dict):
        raise ValueError("root_required_witness_cannot_be_constructed")
    root_name = required[0]
    mutations: list[tuple[str, Any, str]] = []

    missing = copy.deepcopy(valid)
    del missing[root_name]
    mutations.append(("missing_required", missing, "/" + root_name))

    wrong_type = copy.deepcopy(valid)
    wrong_type[root_name] = []
    mutations.append(("wrong_type", wrong_type, "/" + root_name))

    additional = copy.deepcopy(valid)
    additional["__ATLAS_UNEXPECTED__"] = True
    mutations.append(("additional_property", additional, "/__ATLAS_UNEXPECTED__"))

    below_location = _first_array_location(
        schema, valid, require_positive_minimum=True
    )
    if below_location is None:
        raise ValueError("positive_minimum_array_witness_missing")
    below_path, _ = below_location
    below = copy.deepcopy(valid)
    _at_path(below, below_path).clear()
    mutations.append(
        ("array_below_min_items", below, "/" + "/".join(map(str, below_path)))
    )

    above_location = _first_array_location(
        schema, valid, require_positive_minimum=False
    )
    if above_location is None:
        raise ValueError("maximum_array_witness_missing")
    above_path, above_schema = above_location
    above = copy.deepcopy(valid)
    above_array = _at_path(above, above_path)
    item_schema = above_schema.get("items") or {}
    while len(above_array) <= int(above_schema["maxItems"]):
        above_array.append(synthesize_witness(item_schema))
    mutations.append(
        ("array_above_max_items", above, "/" + "/".join(map(str, above_path)))
    )

    cases: list[dict[str, Any]] = [
        {
            "name": "valid",
            "expected": "ACCEPT",
            "observed": "ACCEPT",
            "instance_sha256": canonical_sha256(valid),
        }
    ]
    for name, instance, mutation_path in mutations:
        errors = list(validator.iter_errors(instance))
        if not errors:
            raise ValueError(f"invalid_witness_was_accepted:{name}")
        cases.append(
            {
                "name": name,
                "expected": "REJECT",
                "observed": "REJECT",
                "mutation_path": mutation_path,
                "instance_sha256": canonical_sha256(instance),
                "validator": errors[0].validator,
            }
        )
    return {
        "schema_version": "atlas.vllm.uga.schema_witness_matrix.v1",
        "decision": "PASS",
        "schema_sha256": canonical_sha256(schema),
        "cases": cases,
    }
