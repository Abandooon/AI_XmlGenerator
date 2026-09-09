"""Build finite, assertion-only JSON Schemas for ATLAS constrained decoding."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any

EXECUTION_SCHEMA_VERSION = "atlas.vllm.uga.execution_schema.v2"
JSON_SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"
INSTANCE_VALUE_CONSTRAINTS_KEY = "x-atlas-instance-value-constraints"

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


def _normalise_anchors(value: Any) -> tuple[tuple[int, str], ...]:
    if not isinstance(value, list):
        raise ValueError("instance_constraint_anchors_must_be_an_array")
    anchors: list[tuple[int, str]] = []
    for anchor in value:
        if not isinstance(anchor, Mapping):
            raise ValueError("instance_constraint_anchor_must_be_an_object")
        path_index = anchor.get("path_index")
        short_name = anchor.get("short_name")
        if not isinstance(path_index, int) or not isinstance(short_name, str):
            raise ValueError("instance_constraint_anchor_is_not_typed")
        anchors.append((path_index, short_name))
    return tuple(anchors)


def _coerce_exact_value(value: Any, schema: Mapping[str, Any]) -> Any:
    """Coerce exported string values to the scalar type asserted by the schema."""

    value_type = schema.get("type")
    if isinstance(value_type, list):
        non_null = [item for item in value_type if item != "null"]
        if len(non_null) != 1:
            raise ValueError(f"ambiguous_instance_constraint_type:{value_type}")
        value_type = non_null[0]
    if value_type == "string":
        coerced = str(value)
    elif value_type == "integer":
        if isinstance(value, bool):
            raise ValueError("boolean_is_not_an_integer_constraint")
        number = float(value)
        if not number.is_integer():
            raise ValueError(f"nonintegral_integer_constraint:{value}")
        coerced = int(number)
    elif value_type == "number":
        if isinstance(value, bool):
            raise ValueError("boolean_is_not_a_number_constraint")
        coerced = float(value)
    elif value_type == "boolean":
        if isinstance(value, bool):
            coerced = value
        elif str(value).lower() in {"true", "1"}:
            coerced = True
        elif str(value).lower() in {"false", "0"}:
            coerced = False
        else:
            raise ValueError(f"invalid_boolean_constraint:{value}")
    elif value_type == "null":
        if value is not None:
            raise ValueError(f"invalid_null_constraint:{value}")
        coerced = None
    else:
        raise ValueError(f"instance_constraint_requires_scalar_type:{value_type}")

    from jsonschema import Draft202012Validator

    assertion_schema = _strip_non_assertions(dict(schema), (), {"removed_keyword_count": 0})
    errors = list(Draft202012Validator(assertion_schema).iter_errors(coerced))
    if errors:
        raise ValueError(
            "instance_constraint_disagrees_with_source_assertions:"
            + errors[0].message
        )
    return coerced


def _source_constraint_keys(
    value: Any,
    *,
    path: tuple[str, ...] = (),
) -> set[tuple[tuple[str, ...], int]]:
    keys: set[tuple[tuple[str, ...], int]] = set()
    if isinstance(value, Mapping):
        constraints = value.get(INSTANCE_VALUE_CONSTRAINTS_KEY)
        if constraints is not None:
            if not isinstance(constraints, list) or not constraints:
                raise ValueError(
                    f"instance_constraints_must_be_nonempty:{'/'.join(path)}"
                )
            keys.update((path, index) for index in range(len(constraints)))
        for key, item in value.items():
            if key != INSTANCE_VALUE_CONSTRAINTS_KEY:
                keys.update(_source_constraint_keys(item, path=path + (key,)))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            keys.update(_source_constraint_keys(item, path=path + (str(index),)))
    return keys


def _exact_role_count(
    role: str,
    cardinalities: Mapping[str, Any],
    context: tuple[tuple[int, str], ...],
) -> int:
    if role == "p_ports":
        return int(cardinalities["p"])
    if role == "r_ports":
        return int(cardinalities["r"])
    if role == "receiver_com_specs":
        return 1
    if role == "timing_events":
        return int(cardinalities["timing"])
    if role == "runnables":
        return int(cardinalities["runnables"])
    if role not in {"reads_per_runnable", "writes_per_runnable"}:
        raise ValueError(f"unknown_array_role:{role}")
    runnable_names = {item["name"]: item for item in cardinalities["runnable_accesses"]}
    matching_names = [name for _, name in context if name in runnable_names]
    if len(matching_names) != 1:
        raise ValueError(f"runnable_context_is_not_unique:{role}:{context}")
    field = "reads" if role == "reads_per_runnable" else "writes"
    return int(runnable_names[matching_names[0]][field])


def _specialise_instance_contract(
    source: Mapping[str, Any],
    *,
    cardinalities: Mapping[str, Any],
    context: tuple[tuple[int, str], ...],
    path: tuple[str, ...],
    selected_constraints: set[tuple[tuple[str, ...], int]],
    report: dict[str, Any],
) -> tuple[dict[str, Any] | None, bool]:
    """Compile anchor-scoped metadata into ordinary Draft 2020-12 assertions."""

    source_type = source.get("type")
    if source_type == "object" or "properties" in source:
        properties = source.get("properties") or {}
        if not isinstance(properties, Mapping):
            raise ValueError(f"object_properties_must_be_a_map:{'/'.join(path)}")
        compiled_properties: dict[str, Any] = {}
        for name, child in properties.items():
            if not isinstance(child, Mapping):
                raise ValueError(f"property_schema_must_be_an_object:{name}")
            compiled_child, active = _specialise_instance_contract(
                child,
                cardinalities=cardinalities,
                context=context,
                path=path + ("properties", name),
                selected_constraints=selected_constraints,
                report=report,
            )
            if active:
                assert compiled_child is not None
                compiled_properties[name] = compiled_child
            else:
                report["pruned_inapplicable_property_count"] += 1
        if not compiled_properties:
            return None, False
        base = _strip_non_assertions(dict(source), path, report)
        base.pop("properties", None)
        base.pop("required", None)
        base["type"] = "object"
        base["properties"] = compiled_properties
        # Every surviving branch is backed by a frozen exact obligation or an
        # ordinary source const.  Requiring all of them closes the old
        # XSD-pass/task-obligation-fail gap without post-generation repair.
        base["required"] = list(compiled_properties)
        base["additionalProperties"] = False
        report["forced_required_property_count"] += len(compiled_properties)
        return base, True

    if source_type == "array":
        role = _array_role(path)
        if role is None:
            raise ValueError(f"unclassified_array_schema:{'/'.join(path)}")
        item_source = source.get("items")
        if not isinstance(item_source, Mapping):
            raise ValueError(f"array_items_must_be_an_object:{'/'.join(path)}")
        short_name_schema = (
            (item_source.get("properties") or {}).get("SHORT-NAME")
            if isinstance(item_source.get("properties"), Mapping)
            else None
        )
        identity_constraints = (
            short_name_schema.get(INSTANCE_VALUE_CONSTRAINTS_KEY)
            if isinstance(short_name_schema, Mapping)
            else None
        )
        prefix_items: list[dict[str, Any]] = []
        if identity_constraints is not None:
            if not isinstance(identity_constraints, list):
                raise ValueError(f"array_identity_constraints_not_list:{role}")
            identities: list[tuple[tuple[int, str], ...]] = []
            for constraint in identity_constraints:
                if not isinstance(constraint, Mapping):
                    raise ValueError(f"array_identity_constraint_not_object:{role}")
                anchors = _normalise_anchors(constraint.get("anchors"))
                if anchors[:-1] == context and len(anchors) == len(context) + 1:
                    if constraint.get("value") != anchors[-1][1]:
                        raise ValueError(f"array_identity_value_anchor_mismatch:{role}")
                    identities.append(anchors)
            if len(set(identities)) != len(identities):
                raise ValueError(f"duplicate_array_identity:{role}:{context}")
            for identity in identities:
                compiled_item, active = _specialise_instance_contract(
                    item_source,
                    cardinalities=cardinalities,
                    context=identity,
                    path=path + ("items",),
                    selected_constraints=selected_constraints,
                    report=report,
                )
                if not active or compiled_item is None:
                    raise ValueError(f"named_array_item_has_no_contract:{role}:{identity}")
                prefix_items.append(compiled_item)
        else:
            expected = _exact_role_count(role, cardinalities, context)
            if expected > 0:
                compiled_item, active = _specialise_instance_contract(
                    item_source,
                    cardinalities=cardinalities,
                    context=context,
                    path=path + ("items",),
                    selected_constraints=selected_constraints,
                    report=report,
                )
                if not active or compiled_item is None:
                    raise ValueError(f"unnamed_array_item_has_no_contract:{role}:{context}")
                prefix_items = [copy.deepcopy(compiled_item) for _ in range(expected)]

        expected_count = _exact_role_count(role, cardinalities, context)
        if len(prefix_items) != expected_count:
            raise ValueError(
                f"array_identity_cardinality_mismatch:{role}:"
                f"expected={expected_count}:observed={len(prefix_items)}:context={context}"
            )
        if not prefix_items:
            return None, False
        base = _strip_non_assertions(dict(source), path, report)
        base.pop("items", None)
        base["type"] = "array"
        base["prefixItems"] = prefix_items
        # maxItems is the portable closure assertion; items=false additionally
        # documents that no suffix item schema exists after the fixed slots.
        base["items"] = False
        base["minItems"] = expected_count
        base["maxItems"] = expected_count
        report["array_bounds"].append(
            {
                "schema_path": "/" + "/".join(path),
                "role": role,
                "context": [
                    {"path_index": index, "short_name": name}
                    for index, name in context
                ],
                "minItems": expected_count,
                "maxItems": expected_count,
                "prefixItemCount": expected_count,
            }
        )
        return base, True

    constraints = source.get(INSTANCE_VALUE_CONSTRAINTS_KEY)
    if constraints is not None:
        if not isinstance(constraints, list):
            raise ValueError(f"instance_constraints_not_list:{'/'.join(path)}")
        matches: list[tuple[int, Mapping[str, Any]]] = []
        for index, constraint in enumerate(constraints):
            if not isinstance(constraint, Mapping):
                raise ValueError(f"instance_constraint_not_object:{'/'.join(path)}")
            if _normalise_anchors(constraint.get("anchors")) == context:
                matches.append((index, constraint))
        if not matches:
            return None, False
        if len(matches) != 1:
            raise ValueError(f"ambiguous_instance_constraint:{'/'.join(path)}:{context}")
        index, constraint = matches[0]
        key = (path, index)
        if key in selected_constraints:
            raise ValueError(f"instance_constraint_selected_twice:{'/'.join(path)}:{index}")
        selected_constraints.add(key)
        base = _strip_non_assertions(dict(source), path, report)
        exact_value = _coerce_exact_value(constraint.get("value"), base)
        report["compiled_instance_exact_count"] += 1
        if base.get("type") in {"number", "integer"}:
            # XGrammar 0.2.6rc1 rejects the final digit of non-integral
            # numeric const/enum values (minimal reproduction: const 0.3),
            # but correctly implements equal inclusive bounds. The latter is
            # an equivalent standard JSON Schema exact-value assertion.
            base.pop("const", None)
            base["minimum"] = exact_value
            base["maximum"] = exact_value
            report["compiled_instance_numeric_bound_count"] += 1
        else:
            base["const"] = exact_value
            report["compiled_instance_const_count"] += 1
        return base, True

    if "const" in source:
        base = _strip_non_assertions(dict(source), path, report)
        report["retained_source_const_count"] += 1
        return base, True
    return None, False


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
    """Compile the frozen case contract into executable standard assertions."""

    if not isinstance(source_schema, Mapping) or not source_schema:
        raise ValueError("source_schema_must_be_a_nonempty_object")
    cardinalities = parse_requirement_cardinalities(requirement_text)
    all_constraints = _source_constraint_keys(source_schema)
    if not all_constraints:
        raise ValueError("source_schema_contains_no_instance_constraints")
    selected_constraints: set[tuple[tuple[str, ...], int]] = set()
    stats: dict[str, Any] = {
        "removed_keyword_count": 0,
        "compiled_instance_exact_count": 0,
        "compiled_instance_const_count": 0,
        "compiled_instance_numeric_bound_count": 0,
        "retained_source_const_count": 0,
        "pruned_inapplicable_property_count": 0,
        "forced_required_property_count": 0,
        "array_bounds": [],
    }
    execution_schema, active = _specialise_instance_contract(
        source_schema,
        cardinalities=cardinalities,
        context=(),
        path=(),
        selected_constraints=selected_constraints,
        report=stats,
    )
    if not active or not isinstance(execution_schema, dict):
        raise AssertionError("compiled_schema_root_is_not_active")
    missing = all_constraints - selected_constraints
    unexpected = selected_constraints - all_constraints
    if missing or unexpected:
        raise ValueError(
            "instance_constraint_coverage_mismatch:"
            f"missing={len(missing)}:unexpected={len(unexpected)}"
        )
    if stats["compiled_instance_exact_count"] != len(all_constraints):
        raise ValueError("compiled_instance_exact_count_mismatch")
    execution_schema["$schema"] = JSON_SCHEMA_DIALECT
    array_bounds = stats["array_bounds"]
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
        "source_instance_constraint_count": len(all_constraints),
        "compiled_instance_exact_count": stats[
            "compiled_instance_exact_count"
        ],
        "compiled_instance_const_count": stats[
            "compiled_instance_const_count"
        ],
        "compiled_instance_numeric_bound_count": stats[
            "compiled_instance_numeric_bound_count"
        ],
        "instance_constraint_coverage_decision": "PASS",
        "retained_source_const_count": stats["retained_source_const_count"],
        "pruned_inapplicable_property_count": stats[
            "pruned_inapplicable_property_count"
        ],
        "forced_required_property_count": stats[
            "forced_required_property_count"
        ],
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
        prefix_items = schema.get("prefixItems") or []
        if prefix_items:
            return [synthesize_witness(item) for item in prefix_items]
        count = int(schema.get("minItems", 0))
        item_schema = schema.get("items")
        if not isinstance(item_schema, Mapping):
            raise ValueError("array_witness_has_no_item_schema")
        return [synthesize_witness(item_schema) for _ in range(count)]
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
        prefix_items = schema.get("prefixItems") or []
        items = schema.get("items") or {}
        for index, item in enumerate(instance):
            item_schema = (
                prefix_items[index]
                if index < len(prefix_items)
                else items
            )
            if not isinstance(item_schema, Mapping):
                continue
            found = _first_array_location(
                item_schema,
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


def _iter_exact_locations(
    schema: Mapping[str, Any],
    instance: Any,
    *,
    path: tuple[Any, ...] = (),
) -> list[tuple[tuple[Any, ...], Any]]:
    locations: list[tuple[tuple[Any, ...], Any]] = []
    if "const" in schema:
        locations.append((path, schema["const"]))
        return locations
    if (
        schema.get("type") in {"number", "integer"}
        and "minimum" in schema
        and schema.get("minimum") == schema.get("maximum")
    ):
        locations.append((path, schema["minimum"]))
        return locations
    if isinstance(instance, dict):
        for name, child_schema in (schema.get("properties") or {}).items():
            if name in instance:
                locations.extend(
                    _iter_exact_locations(
                        child_schema,
                        instance[name],
                        path=path + (name,),
                    )
                )
    elif isinstance(instance, list):
        prefix_items = schema.get("prefixItems") or []
        item_schema = schema.get("items")
        for index, item in enumerate(instance):
            child_schema = (
                prefix_items[index]
                if index < len(prefix_items)
                else item_schema
            )
            if isinstance(child_schema, Mapping):
                locations.extend(
                    _iter_exact_locations(
                        child_schema,
                        item,
                        path=path + (index,),
                    )
                )
    return locations


def _mutated_scalar(value: Any) -> Any:
    if isinstance(value, bool):
        return not value
    if isinstance(value, str):
        return value + "__ATLAS_MUTATION__"
    if isinstance(value, int):
        return value + 1
    if isinstance(value, float):
        return value + 1.0
    if value is None:
        return "__ATLAS_MUTATION__"
    raise ValueError(f"unsupported_const_mutation_type:{type(value).__name__}")


def _iter_required_locations(
    schema: Mapping[str, Any],
    instance: Any,
    *,
    path: tuple[Any, ...] = (),
) -> list[tuple[Any, ...]]:
    locations: list[tuple[Any, ...]] = []
    if isinstance(instance, dict):
        properties = schema.get("properties") or {}
        for name in schema.get("required") or []:
            if name in instance:
                locations.append(path + (name,))
                child_schema = properties.get(name)
                if isinstance(child_schema, Mapping):
                    locations.extend(
                        _iter_required_locations(
                            child_schema,
                            instance[name],
                            path=path + (name,),
                        )
                    )
    elif isinstance(instance, list):
        prefix_items = schema.get("prefixItems") or []
        item_schema = schema.get("items")
        for index, item in enumerate(instance):
            child_schema = (
                prefix_items[index]
                if index < len(prefix_items)
                else item_schema
            )
            if isinstance(child_schema, Mapping):
                locations.extend(
                    _iter_required_locations(
                        child_schema,
                        item,
                        path=path + (index,),
                    )
                )
    return locations


def _delete_at_path(instance: Any, path: tuple[Any, ...]) -> None:
    parent = _at_path(instance, path[:-1])
    del parent[path[-1]]


def build_witness_matrix(schema: Mapping[str, Any]) -> dict[str, Any]:
    """Prove acceptance plus exhaustive exact-value/required-field rejection."""

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
    while len(above_array) <= int(above_schema["maxItems"]):
        above_array.append(
            copy.deepcopy(above_array[0]) if above_array else None
        )
    mutations.append(
        ("array_above_max_items", above, "/" + "/".join(map(str, above_path)))
    )

    exact_locations = _iter_exact_locations(schema, valid)
    if not exact_locations:
        raise ValueError("exact_value_witnesses_are_missing")
    for index, (const_path, exact_value) in enumerate(exact_locations, start=1):
        mutated = copy.deepcopy(valid)
        parent = _at_path(mutated, const_path[:-1])
        parent[const_path[-1]] = _mutated_scalar(exact_value)
        mutations.append(
            (
                f"exact_const_mutation_{index:04d}",
                mutated,
                "/" + "/".join(map(str, const_path)),
            )
        )

    required_locations = _iter_required_locations(schema, valid)
    if not required_locations:
        raise ValueError("required_property_witnesses_are_missing")
    for index, required_path in enumerate(required_locations, start=1):
        if required_path == (root_name,):
            continue
        mutated = copy.deepcopy(valid)
        _delete_at_path(mutated, required_path)
        mutations.append(
            (
                f"required_property_mutation_{index:04d}",
                mutated,
                "/" + "/".join(map(str, required_path)),
            )
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
        "schema_version": "atlas.vllm.uga.schema_witness_matrix.v3",
        "decision": "PASS",
        "schema_sha256": canonical_sha256(schema),
        "valid_witness": valid,
        "exact_value_mutation_count": len(exact_locations),
        "required_property_mutation_count": len(required_locations),
        "cases": cases,
    }
