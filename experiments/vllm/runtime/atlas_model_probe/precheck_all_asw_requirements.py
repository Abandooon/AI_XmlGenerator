"""Offline, model-free precheck for every frozen ASW V3 requirement.

The precheck exercises the production requirement-value compiler, pinned-XSD
path resolver, Neo4j-backed Phase 2 schema builder, provider-root projection,
deterministic value materialization, XML projection, deterministic serializer,
posterior AUTOSAR 4.2.2 XSD validation, parsed selection obligations, and
same-context reference resolution.  It never calls a model provider and sets a
literal placeholder credential before importing ATLAS modules.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parent
ATLAS_ROOT = Path(r"E:\git projects\AI_XmlGenerator")
REQUIREMENTS_ROOT = Path(r"E:\54239\Documents\atlas_autosar_requirements_v3")
REQUIREMENTS_PATH = REQUIREMENTS_ROOT / "asw_cases_v3.yaml"
XSD_PATH = ATLAS_ROOT / "src/validation/data/AUTOSAR_4-2-2.xsd"
EXPECTED_XSD_SHA256 = "3c89b2f16d1981eb04e12c7fbe035e7cd6fbd79965a47ff6cf6d6b878feb71ad"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_sha256(value: Any) -> str:
    return sha256_bytes(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )


def strict_schema_violations(schema: dict[str, Any]) -> list[str]:
    violations: list[str] = []

    def walk(node: Any, path: str) -> None:
        if not isinstance(node, dict):
            return
        if node.get("type") == "object":
            properties = node.get("properties")
            required = node.get("required")
            if not isinstance(properties, dict):
                violations.append(f"{path}: missing properties object")
            else:
                if set(required or []) != set(properties):
                    violations.append(f"{path}: required != properties")
                for key, child in properties.items():
                    walk(child, f"{path}/properties/{key}")
            if node.get("additionalProperties") is not False:
                violations.append(f"{path}: additionalProperties is not false")
        if node.get("type") == "array":
            walk(node.get("items"), f"{path}/items")

    walk(schema, "$schema")
    return violations


def project_instance_to_schema(value: Any, schema: dict[str, Any]) -> Any:
    """Remove deterministic properties exactly as the provider schema does."""
    if schema.get("type") == "object":
        properties = schema.get("properties") or {}
        if not isinstance(value, dict):
            return value
        return {
            key: project_instance_to_schema(value[key], child)
            for key, child in properties.items()
            if key in value
        }
    if schema.get("type") == "array" and isinstance(value, list):
        item_schema = schema.get("items") or {}
        return [project_instance_to_schema(item, item_schema) for item in value]
    return deepcopy(value)


def interface_plans(case: dict[str, Any], manifest: dict[str, Any]) -> list[dict[str, Any]]:
    catalog = manifest["authoritative_context"]["interface_catalog"]
    signals = [
        *(case.get("provided_signals") or []),
        *(item["signal"] for item in case.get("required_signals") or []),
    ]
    plans = []
    for signal in signals:
        entry = catalog[signal]
        plans.append(
            {
                "interface_id": f"IF-{signal.upper().replace('_', '-')}",
                "name": entry["interface_ref"].rsplit("/", 1)[-1],
                "type": "SENDER-RECEIVER-INTERFACE",
                "communication_pattern": "sender-receiver",
                "data_elements": [entry["data_element"]],
                "data_category": "scalar",
                "connected_components": [case["component"]],
                "performance_requirements": f"{case['case_id']} offline precheck",
                "direct_paths": "COM_Interface",
                **(
                    {
                        "data_element_type_refs": {
                            entry["data_element"]: {
                                "value": entry["type_ref"],
                                "dest": entry["type_dest"],
                            }
                        }
                    }
                    if entry.get("type_ref") and entry.get("type_dest")
                    else {}
                ),
            }
        )
    return plans


def canonical_component_plan(case: dict[str, Any]) -> dict[str, Any]:
    port_types = []
    if case.get("provided_signals"):
        port_types.append("P-PORT-PROTOTYPE")
    if case.get("required_signals"):
        port_types.append("R-PORT-PROTOTYPE")
    behavior = case.get("internal_behavior")
    return {
        "component_id": case["case_id"],
        "name": case["component"],
        "type": "APPLICATION-SW-COMPONENT-TYPE",
        "purpose": case["intent"],
        "estimated_complexity": str(case["tier"]).title(),
        "port_estimates": {
            "input_ports": str(len(case.get("required_signals") or [])),
            "output_ports": str(len(case.get("provided_signals") or [])),
        },
        "behavioral_characteristics": case["intent"],
        "element_design": {
            "ports": {
                "needed": bool(port_types),
                "types": port_types,
                "details": "Deterministic offline requirement precheck",
            },
            "internal_behaviors": {
                "needed": behavior is not None,
                "events": [],
                "runnables": [],
            },
            "selections": [],
            "unsupported": [],
        },
    }


def canonical_component_instance(
    case: dict[str, Any], manifest: dict[str, Any], *, event_short_name, variable_access_short_name
) -> dict[str, Any]:
    catalog = manifest["authoritative_context"]["interface_catalog"]
    component = case["component"]
    root: dict[str, Any] = {"SHORT-NAME": component}
    ports: dict[str, Any] = {}
    if case.get("provided_signals"):
        ports["P-PORT-PROTOTYPE"] = [
            {
                "SHORT-NAME": f"Pp_{signal}",
                "PROVIDED-INTERFACE-TREF": {
                    "@DEST": "SENDER-RECEIVER-INTERFACE",
                    "#text": catalog[signal]["interface_ref"],
                },
            }
            for signal in case["provided_signals"]
        ]
    if case.get("required_signals"):
        required_ports = []
        for specification in case["required_signals"]:
            signal = specification["signal"]
            entry = catalog[signal]
            required_ports.append(
                {
                    "SHORT-NAME": f"Rp_{signal}",
                    "REQUIRED-COM-SPECS": {
                        "NONQUEUED-RECEIVER-COM-SPEC": [
                            {
                                "DATA-ELEMENT-REF": {
                                    "@DEST": "VARIABLE-DATA-PROTOTYPE",
                                    "#text": (
                                        f"{entry['interface_ref']}/{entry['data_element']}"
                                    ),
                                },
                                "ALIVE-TIMEOUT": specification["alive_timeout_s"],
                                "HANDLE-TIMEOUT-TYPE": specification[
                                    "handle_timeout_type"
                                ],
                                "INIT-VALUE": {
                                    "NUMERICAL-VALUE-SPECIFICATION": {
                                        "VALUE": {"#text": "0"}
                                    }
                                },
                            }
                        ]
                    },
                    "REQUIRED-INTERFACE-TREF": {
                        "@DEST": "SENDER-RECEIVER-INTERFACE",
                        "#text": entry["interface_ref"],
                    },
                }
            )
        ports["R-PORT-PROTOTYPE"] = required_ports
    if ports:
        root["PORTS"] = ports

    behavior = case.get("internal_behavior")
    if behavior is not None:
        behavior_value: dict[str, Any] = {
            "SHORT-NAME": behavior["short_name"],
            "EVENTS": {"TIMING-EVENT": []},
            # Provider projection deliberately omits the physical RUNNABLES
            # wrapper. apply_projection_map restores it before serialization.
            "RUNNABLE-ENTITY": [],
        }
        for runnable in behavior["runnables"]:
            runnable_name = runnable["short_name"]
            behavior_value["EVENTS"]["TIMING-EVENT"].append(
                {
                    "SHORT-NAME": event_short_name(runnable_name),
                    "START-ON-EVENT-REF": {
                        "@DEST": "RUNNABLE-ENTITY",
                        "#text": (
                            f"/Components/{component}/{behavior['short_name']}/"
                            f"{runnable_name}"
                        ),
                    },
                    "PERIOD": runnable["period_s"],
                }
            )
            runnable_value: dict[str, Any] = {"SHORT-NAME": runnable_name}
            directions = (
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
            )
            for direction, signals, wrapper, port_prefix, port_dest in directions:
                accesses = []
                for signal in signals:
                    entry = catalog[signal]
                    accesses.append(
                        {
                            "SHORT-NAME": variable_access_short_name(
                                runnable_name, direction, signal
                            ),
                            "ACCESSED-VARIABLE": {
                                "AUTOSAR-VARIABLE-IREF": {
                                    "PORT-PROTOTYPE-REF": {
                                        "@DEST": port_dest,
                                        "#text": (
                                            f"/Components/{component}/"
                                            f"{port_prefix}_{signal}"
                                        ),
                                    },
                                    "TARGET-DATA-PROTOTYPE-REF": {
                                        "@DEST": "VARIABLE-DATA-PROTOTYPE",
                                        "#text": (
                                            f"{entry['interface_ref']}/"
                                            f"{entry['data_element']}"
                                        ),
                                    },
                                }
                            },
                        }
                    )
                if accesses:
                    runnable_value[wrapper] = {"VARIABLE-ACCESS": accesses}
            behavior_value["RUNNABLE-ENTITY"].append(runnable_value)
        root["SWC-INTERNAL-BEHAVIOR"] = behavior_value
    return {"APPLICATION-SW-COMPONENT-TYPE": root}


def canonical_interface_instance(plans: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "SENDER-RECEIVER-INTERFACE": [
            {
                "SHORT-NAME": plan["name"],
                "DATA-ELEMENTS": {
                    "VARIABLE-DATA-PROTOTYPE": [
                        {
                            "SHORT-NAME": name,
                            **(
                                {
                                    "TYPE-TREF": {
                                        "@DEST": plan["data_element_type_refs"][name][
                                            "dest"
                                        ],
                                        "#text": plan["data_element_type_refs"][name][
                                            "value"
                                        ],
                                    }
                                }
                                if name in (plan.get("data_element_type_refs") or {})
                                else {}
                            ),
                        }
                        for name in plan["data_elements"]
                    ]
                },
            }
            for plan in plans
        ]
    }


def fail_if_errors(errors: list[Any], label: str) -> None:
    if not errors:
        return
    first = errors[0]
    path = list(getattr(first, "absolute_path", []))
    message = str(getattr(first, "message", first))
    raise RuntimeError(f"{label} failed at {path}: {message}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "ALL_REQUIREMENTS_OFFLINE_PRECHECK_MANIFEST.json",
    )
    parser.add_argument(
        "--reference-root",
        type=Path,
        help="optionally materialize immutable deterministic controlled baselines",
    )
    args = parser.parse_args(argv)
    reference_root = args.reference_root.resolve() if args.reference_root else None
    if reference_root is not None and reference_root.exists() and any(reference_root.iterdir()):
        raise FileExistsError(f"reference root is not empty: {reference_root}")

    # Do not inherit, inspect, print, or persist any real provider credential.
    os.environ["LLM_API_KEY"] = "offline-local-placeholder"
    sys.path[:0] = [str(ATLAS_ROOT), str(ROOT), str(REQUIREMENTS_ROOT)]

    from jsonschema import Draft202012Validator
    from lxml import etree
    from render_cases import (
        event_short_name,
        load_manifest,
        validate_manifest,
        variable_access_short_name,
    )
    from evaluate_asw_v3_run import evaluate
    from experiment_runtime import atomic_write_json, atomic_write_text
    from run_phase12_case import _requirement
    from controlled_repair_v16 import build_mutation_schedule
    from repair_asw_v3_run import _mutate_typed_targets, apply_mutation
    from src.llm_generation.core.round1_designer import round1_designer
    from src.llm_generation.core.round2_generator import round2_generator
    from src.llm_generation.core.typed_repair import (
        RepairTarget,
        TypedRepairSession,
        render_documents,
    )
    from src.llm_generation.core.xsd_serializer import apply_projection_map
    from src.llm_generation.knowledge.element_selection import (
        augment_declared_value_selections,
        build_interface_instance_skeleton,
        build_provider_instance_skeleton,
        compile_architecture_selection_paths,
        materialize_admitted_provider_payload,
        materialize_deterministic_values,
        merge_provider_schema_payloads,
        partition_provider_schema,
        project_element_design_for_schema,
        project_payload_to_admitted_provider_schema,
        project_provider_to_admitted_instances,
        project_declared_value_design,
        remove_deterministic_value_properties,
    )
    from src.validation.v2.arxml_index import ArxmlIndex, local_name
    from src.validation.v2.selection_obligations import validate_selection_obligations

    if sha256_file(XSD_PATH) != EXPECTED_XSD_SHA256:
        raise RuntimeError("pinned AUTOSAR 4.2.2 XSD hash mismatch")
    manifest = load_manifest(REQUIREMENTS_PATH)
    requirement_validation = validate_manifest(manifest)
    if requirement_validation.get("status") != "PASS":
        raise RuntimeError("frozen ASW V3 requirement manifest is invalid")
    cases = list(manifest.get("cases") or [])
    if len(cases) != 20:
        raise RuntimeError(f"expected 20 requirements, found {len(cases)}")
    controlled_design = build_mutation_schedule(manifest)
    tasks_by_case = {
        case["case_id"]: [
            task
            for task in controlled_design["tasks"]
            if task["case_id"] == case["case_id"]
        ]
        for case in cases
    }

    xsd = etree.XMLSchema(etree.parse(str(XSD_PATH)))
    records: list[dict[str, Any]] = []
    aggregate = {
        "case_count": 0,
        "component_arxml_count": 0,
        "interface_arxml_count": 0,
        "xsd_pass_count": 0,
        "selection_obligation_pass_count": 0,
        "same_context_reference_pass_count": 0,
        "provider_schema_call_count": 0,
        "typed_repair_context_case_count": 0,
        "typed_repair_context_target_count": 0,
        "typed_mutation_injection_count": 0,
        "controlled_mutation_case_count": 0,
        "controlled_mutation_injection_count": 0,
        "controlled_mutation_detection_count": 0,
        "controlled_core_fixed_operator_count": 0,
        "controlled_substitution_count": 0,
        "controlled_mutation_detection_by_operator": {},
        "deterministic_reference_baseline_count": 0,
    }

    def reference_resolution_statuses(bundle: dict[str, Any]) -> list[str]:
        with tempfile.TemporaryDirectory(
            prefix="atlas-all-requirements-precheck-"
        ) as tmp:
            temp_root = Path(tmp)
            paths = []
            for kind in ("components", "interfaces"):
                for position, (name, xml_text) in enumerate(
                    sorted((bundle.get(kind) or {}).items())
                ):
                    path = temp_root / f"{kind}-{position}-{name}.arxml"
                    path.write_text(xml_text, encoding="utf-8")
                    paths.append(path)
            index = ArxmlIndex(paths)
            references = [
                element
                for root in index.roots
                for element in root.iter()
                if local_name(element.tag).endswith(("-REF", "-TREF", "-IREF"))
                and element.text
                and element.text.strip().startswith("/")
            ]
            return [index.resolve(item).status for item in references]

    for case in cases:
        requirement = _requirement(case["case_id"], 104729)
        interface_package_ref = str(
            requirement.get("interface_package_ref") or "/COM_Interface"
        ).rstrip("/")
        round2_generator._interface_package_ref = interface_package_ref
        round2_generator._interface_package_name = interface_package_ref[1:]
        plan = canonical_component_plan(case)
        plan, value_audit = augment_declared_value_selections(
            plan,
            requirement["generation_value_obligations"],
            xsd_path_index=round1_designer.selection_path_index,
            requirement_contracts=requirement[
                "generation_requirement_contracts"
            ],
        )
        architecture, path_audit = compile_architecture_selection_paths(
            {"component_plan": [plan]},
            xsd_path_index=round1_designer.selection_path_index,
        )
        plan = architecture["component_plan"][0]
        if (plan.get("element_design") or {}).get("unsupported"):
            raise RuntimeError(f"{case['case_id']}: unsupported intent remains")
        exact_paths = [
            item
            for component in path_audit.get("components") or []
            for item in component.get("selections") or []
        ]
        if not exact_paths or any(item.get("resolution") != "exact" for item in exact_paths):
            raise RuntimeError(f"{case['case_id']}: non-exact XSD selection path")

        plans = interface_plans(case, manifest)
        interface_schema = round2_generator.query_engine.generate_multi_interface_schema(
            plans
        )
        Draft202012Validator.check_schema(interface_schema)
        interface_strict = strict_schema_violations(interface_schema)
        if interface_strict:
            raise RuntimeError(
                f"{case['case_id']}: interface strict schema violations: "
                f"{interface_strict[:2]}"
            )
        interface_instance = canonical_interface_instance(plans)
        fail_if_errors(
            list(Draft202012Validator(interface_schema).iter_errors(interface_instance)),
            f"{case['case_id']} full interface schema",
        )
        interface_skeleton, interface_skeleton_audit = (
            build_interface_instance_skeleton(plans, interface_schema)
        )
        interface_provider_schema, interface_projection_plan = (
            project_provider_to_admitted_instances(
                interface_schema, interface_skeleton
            )
        )
        Draft202012Validator.check_schema(interface_provider_schema)
        interface_provider_strict = strict_schema_violations(
            interface_provider_schema
        )
        if interface_provider_strict:
            raise RuntimeError(
                f"{case['case_id']}: admitted interface strict schema "
                f"violations: {interface_provider_strict[:2]}"
            )
        interface_provider_input = project_payload_to_admitted_provider_schema(
            interface_instance, interface_projection_plan
        )
        fail_if_errors(
            list(
                Draft202012Validator(interface_provider_schema).iter_errors(
                    interface_provider_input
                )
            ),
            f"{case['case_id']} admitted-only interface provider schema",
        )
        interface_instance, interface_assembly_audit = (
            materialize_admitted_provider_payload(
                interface_provider_input,
                interface_provider_schema,
                interface_projection_plan,
                interface_skeleton,
            )
        )
        if interface_assembly_audit.get("normalization_status") != "NOT_APPLICABLE":
            raise RuntimeError(
                f"{case['case_id']}: interface reference builder normalized raw data"
            )
        if interface_instance != canonical_interface_instance(plans):
            raise RuntimeError(
                f"{case['case_id']}: interface provider projection/materialization "
                "is not reversible"
            )
        normalized_interfaces = round2_generator._normalize_interfaces_object(
            interface_instance
        )
        interface_xml: dict[str, str] = {}
        for name, value in sorted(normalized_interfaces.items()):
            xml_text = round2_generator._convert_single_interface_to_arxml(name, value)
            root = etree.fromstring(xml_text.encode("utf-8"))
            if not xsd.validate(root):
                raise RuntimeError(
                    f"{case['case_id']}/{name}: interface XSD failure: "
                    f"{xsd.error_log.last_error}"
                )
            interface_xml[name] = xml_text

        component_schema = round2_generator._build_single_component_schema(plan)
        projection_map = round2_generator.query_engine.component_xml_projection_map(plan)
        known_paths: dict[str, list[str]] = {}
        for item in round2_generator._build_detailed_interface_index(
            normalized_interfaces
        ):
            if item.get("type") and item.get("path"):
                known_paths.setdefault(str(item["type"]), []).append(str(item["path"]))
        enhanced_schema = round2_generator._inject_paths_into_schema(
            component_schema,
            known_paths,
            current_component_name=case["component"],
        )
        Draft202012Validator.check_schema(enhanced_schema)
        enhanced_strict = strict_schema_violations(enhanced_schema)
        if enhanced_strict:
            raise RuntimeError(
                f"{case['case_id']}: component strict schema violations: "
                f"{enhanced_strict[:2]}"
            )

        full_instance = canonical_component_instance(
            case,
            manifest,
            event_short_name=event_short_name,
            variable_access_short_name=variable_access_short_name,
        )
        fail_if_errors(
            list(Draft202012Validator(enhanced_schema).iter_errors(full_instance)),
            f"{case['case_id']} enhanced component schema",
        )
        declared_design = project_declared_value_design(
            plan.get("element_design") or {}, projection_map, value_audit
        )
        deterministic_provider_schema, materialization_plan = (
            remove_deterministic_value_properties(enhanced_schema, declared_design)
        )
        provider_input = project_instance_to_schema(
            full_instance, deterministic_provider_schema
        )
        fail_if_errors(
            list(
                Draft202012Validator(deterministic_provider_schema).iter_errors(
                    provider_input
                )
            ),
            f"{case['case_id']} deterministic provider schema",
        )
        instance_provider_design = project_element_design_for_schema(
            plan.get("element_design") or {}, projection_map
        )
        instance_skeleton, _instance_skeleton_plan = build_provider_instance_skeleton(
            enhanced_schema, instance_provider_design
        )
        full_provider_schema, instance_projection_plan = (
            project_provider_to_admitted_instances(
                deterministic_provider_schema, instance_skeleton
            )
        )
        admitted_provider_input = project_payload_to_admitted_provider_schema(
            provider_input, instance_projection_plan
        )
        fail_if_errors(
            list(
                Draft202012Validator(full_provider_schema).iter_errors(
                    admitted_provider_input
                )
            ),
            f"{case['case_id']} admitted-only provider schema",
        )
        provider_calls, partition_plan = partition_provider_schema(
            full_provider_schema
        )
        if len(provider_calls) != 1:
            raise RuntimeError(f"{case['case_id']}: provider call count is not one")
        projected_input = (
            admitted_provider_input[partition_plan["component_root"]]
            if partition_plan.get("component_root")
            else admitted_provider_input
        )
        fail_if_errors(
            list(
                Draft202012Validator(provider_calls[0]["schema"]).iter_errors(
                    projected_input
                )
            ),
            f"{case['case_id']} projected provider schema",
        )
        restored_provider, merge_audit = merge_provider_schema_payloads(
            {"full": projected_input}, full_provider_schema, partition_plan
        )
        admitted_materialized, instance_assembly_audit = (
            materialize_admitted_provider_payload(
                restored_provider,
                full_provider_schema,
                instance_projection_plan,
                instance_skeleton,
            )
        )
        if instance_assembly_audit.get("normalization_status") != "NOT_APPLICABLE":
            raise RuntimeError(f"{case['case_id']}: reference builder normalized raw data")
        materialized, materialization_audit = materialize_deterministic_values(
            admitted_materialized, enhanced_schema, declared_design
        )
        if materialized != full_instance:
            raise RuntimeError(
                f"{case['case_id']}: provider projection/materialization is not reversible"
            )

        root_payload = deepcopy(materialized["APPLICATION-SW-COMPONENT-TYPE"])
        # Keep the provider-space payload intact for the typed repair target,
        # exactly as Round2Generator registers it before XML projection.
        projected_payload = apply_projection_map(
            deepcopy(root_payload), projection_map
        )
        projected_payload["_type"] = "APPLICATION-SW-COMPONENT-TYPE"
        component_xml = round2_generator._convert_single_component_to_arxml(
            case["component"], projected_payload
        )
        component_xml_again = round2_generator._convert_single_component_to_arxml(
            case["component"], deepcopy(projected_payload)
        )
        if component_xml != component_xml_again:
            raise RuntimeError(f"{case['case_id']}: renderer is nondeterministic")
        component_root = etree.fromstring(component_xml.encode("utf-8"))
        if not xsd.validate(component_root):
            raise RuntimeError(
                f"{case['case_id']}: component XSD failure: {xsd.error_log.last_error}"
            )

        bundle = {
            "components": {case["component"]: component_xml},
            "interfaces": interface_xml,
        }
        repair_targets: dict[tuple[str, str], RepairTarget] = {
            ("components", case["component"]): RepairTarget(
                kind="components",
                name=case["component"],
                element_type="APPLICATION-SW-COMPONENT-TYPE",
                payload=deepcopy(root_payload),
                root_schema=deepcopy(
                    enhanced_schema["properties"][
                        "APPLICATION-SW-COMPONENT-TYPE"
                    ]
                ),
                document_schema=deepcopy(enhanced_schema),
                declared_value_design=deepcopy(declared_design),
                projection_map=deepcopy(projection_map),
                immutable_paths=tuple(
                    tuple(item.get("resolved_path") or ())
                    for item in materialization_audit.get("applied") or []
                    if item.get("resolved_path")
                ),
            )
        }
        for name, value in sorted(normalized_interfaces.items()):
            interface_type = str(value.get("_type") or "")
            item_schema = (
                (interface_schema.get("properties") or {})
                .get(interface_type, {})
                .get("items")
            )
            if not interface_type or not isinstance(item_schema, dict):
                raise RuntimeError(
                    f"{case['case_id']}/{name}: interface repair target has no item schema"
                )
            repair_targets[("interfaces", name)] = RepairTarget(
                kind="interfaces",
                name=name,
                element_type=interface_type,
                payload={
                    key: deepcopy(item)
                    for key, item in value.items()
                    if key != "_type"
                },
                root_schema=deepcopy(item_schema),
            )

        def repair_session() -> TypedRepairSession:
            production = round2_generator._typed_repair
            return TypedRepairSession(
                guard=production.guard,
                serializer=production.serializer,
                fingerprint=production.fingerprint,
                # Mirror production exactly: a clone that silently waived
                # nothing would make the precheck weaker than the real run.
                deletion_repairable_rule_ids=production.deletion_repairable_rule_ids,
            )

        context_session = repair_session()
        context_session.bind(repair_targets, bundle)
        typed_context = context_session.export_context(bundle)
        restored_session = repair_session()
        restored_targets = restored_session.restore_context(typed_context, bundle)
        if render_documents(
            restored_targets, serializer=restored_session.serializer
        ) != bundle:
            raise RuntimeError(
                f"{case['case_id']}: restored typed context did not reproduce bundle"
            )
        aggregate["typed_repair_context_case_count"] += 1
        aggregate["typed_repair_context_target_count"] += len(restored_targets)

        obligations = validate_selection_obligations(bundle, [plan])
        if obligations.get("decision") != "PASS":
            raise RuntimeError(
                f"{case['case_id']}: parsed selection obligations did not pass"
            )

        reference_statuses = reference_resolution_statuses(bundle)
        if any(status != "resolved" for status in reference_statuses):
            raise RuntimeError(f"{case['case_id']}: unresolved same-context reference")

        mutation_detection: dict[str, Any] = {}
        aggregate["controlled_mutation_case_count"] += 1
        for task in tasks_by_case[case["case_id"]]:
                mutation = task["effective_mutation"]
                if mutation == "wrong_xsd_order":
                    mutated = apply_mutation(bundle, mutation)
                    order_session = repair_session()
                    order_session.bind_order_normalization(
                        restored_targets, mutated
                    )
                    injection_mode = "order_only_xml_identity"
                else:
                    mutated_targets = _mutate_typed_targets(
                        restored_targets, mutation
                    )
                    mutated = render_documents(
                        mutated_targets, serializer=restored_session.serializer
                    )
                    injection_mode = "structured_payload_then_renderer"
                if mutated == bundle:
                    raise RuntimeError(
                        f"{case['case_id']}: controlled mutation {mutation} changed nothing"
                    )
                mutation_xsd_failures = 0
                for documents in mutated.values():
                    for xml_text in documents.values():
                        root = etree.fromstring(xml_text.encode("utf-8"))
                        mutation_xsd_failures += int(not xsd.validate(root))
                mutation_obligations = validate_selection_obligations(
                    mutated, [plan]
                )
                mutation_reference_statuses = reference_resolution_statuses(mutated)
                mutation_reference_failures = sum(
                    status != "resolved" for status in mutation_reference_statuses
                )
                detected = (
                    mutation_xsd_failures > 0
                    or mutation_obligations.get("decision") != "PASS"
                    or mutation_reference_failures > 0
                )
                if not detected:
                    raise RuntimeError(
                        f"{case['case_id']}: controlled mutation {mutation} escaped all gates"
                    )
                mutation_detection[mutation] = {
                    "decision": "DETECTED",
                    "task_id": task["task_id"],
                    "base_operator": task["base_operator"],
                    "applicability": task["applicability"],
                    "analysis_layer": task["analysis_layer"],
                    "injection_mode": injection_mode,
                    "xsd_failure_count": mutation_xsd_failures,
                    "selection_obligation_decision": mutation_obligations.get(
                        "decision"
                    ),
                    "reference_failure_count": mutation_reference_failures,
                }
                aggregate["controlled_mutation_injection_count"] += 1
                aggregate["typed_mutation_injection_count"] += 1
                aggregate["controlled_mutation_detection_count"] += 1
                if task["analysis_layer"] == "core_fixed_operator":
                    aggregate["controlled_core_fixed_operator_count"] += 1
                else:
                    aggregate["controlled_substitution_count"] += 1
                operator_counts = aggregate[
                    "controlled_mutation_detection_by_operator"
                ].setdefault(
                    task["base_operator"],
                    {"applicable": 0, "not_applicable": 0, "injected": 0, "detected": 0},
                )
                operator_counts[
                    "applicable" if task["applicability"] == "APPLICABLE" else "not_applicable"
                ] += 1
                operator_counts["injected"] += 1
                operator_counts["detected"] += 1

        reference_baseline: dict[str, Any] | None = None
        if reference_root is not None:
            if round2_generator.validation_service is None:
                raise RuntimeError("deterministic reference baseline needs validation service")
            baseline_root = reference_root / case["case_id"]
            generated = baseline_root / "generated_arxml" / "reference"
            component_path = generated / f"{case['component']}.arxml"
            atomic_write_text(component_path, component_xml)
            interface_paths: list[Path] = []
            for name, xml_text in sorted(interface_xml.items()):
                path = generated / f"{name}.arxml"
                atomic_write_text(path, xml_text)
                interface_paths.append(path)

            declarations = round2_generator._validation_declarations(requirement)
            declared_constraint_ids = declarations["declared_constraint_ids"]
            # A deterministic reference has no provider retrieval.  Its only
            # admissible validation selection is the explicit, frozen
            # requirement declaration.  Preserve that distinction in the
            # context while satisfying the same dataset/validator hash checks
            # used by the real runner.
            deterministic_selection_trace = {}
            if declared_constraint_ids:
                deterministic_selection_trace = {
                    "deterministic_requirement_declarations": {
                        "backend": "deterministic_requirement_xsd_reference_builder",
                        "dataset_sha256": (
                            round2_generator.validation_service.dataset_sha256
                        ),
                        "constraint_ids": sorted(set(declared_constraint_ids)),
                        "result_count": len(set(declared_constraint_ids)),
                        "fallback_reason": "not_a_provider_retrieval",
                    }
                }
            validation_context = (
                round2_generator.validation_service.build_validation_context(
                    deterministic_selection_trace,
                    declared_use_cases=declarations["declared_use_cases"],
                    declared_constraint_ids=declared_constraint_ids,
                    declared_targets=declarations["declared_targets"],
                    declared_parameters=declarations["declared_parameters"],
                    intent_scope=declarations["intent_scope"],
                    declared_capability_scopes=declarations[
                        "declared_capability_scopes"
                    ],
                    manual_evidence_scope=declarations["manual_evidence_scope"],
                )
            )
            validation = round2_generator.validation_service.validate_bundle(
                bundle, validation_context=validation_context
            )
            validation = round2_generator._merge_bundle_selection_obligations(
                bundle, validation, [plan]
            )
            validation_path = generated / f"{case['component']}_validation_reference.json"
            atomic_write_json(validation_path, validation)
            context_path = (
                baseline_root
                / "atlas_output"
                / "typed_repair_context"
                / f"{typed_context['content_sha256']}.json"
            )
            atomic_write_json(context_path, typed_context)
            metrics_path = (
                baseline_root
                / "metrics"
                / "reference"
                / f"{case['case_id']}_metrics.json"
            )
            atomic_write_json(
                metrics_path,
                {"phase1": {"blueprint": {"component_plan": [plan]}}},
            )
            independent = evaluate(
                case_id=case["case_id"],
                component_path=component_path,
                interface_paths=interface_paths,
                validation_path=validation_path,
            )
            atomic_write_json(
                baseline_root / "independent_evaluation.json", independent
            )
            if independent.get("decision") != "PASS":
                raise RuntimeError(
                    f"{case['case_id']}: deterministic reference baseline is not strict PASS"
                )
            artifact_hashes = {
                path.relative_to(baseline_root).as_posix(): sha256_file(path)
                for path in sorted(
                    item for item in baseline_root.rglob("*") if item.is_file()
                )
                if path.name != "run_summary.json"
            }
            run_summary = {
                "schema_version": "atlas.autosar.v16.reference_baseline.v1",
                "source": "deterministic_requirement_xsd_reference_builder",
                "case_id": case["case_id"],
                "system_name": case["component"],
                "requirement_case_sha256": canonical_sha256(case),
                "bundle_sha256": canonical_sha256(bundle),
                "typed_repair_context_content_sha256": typed_context[
                    "content_sha256"
                ],
                "validation_context_manifest_sha256": validation_context[
                    "manifest_sha256"
                ],
                "independent_decision": independent["decision"],
                "artifact_hashes": artifact_hashes,
            }
            atomic_write_json(baseline_root / "run_summary.json", run_summary)
            reference_baseline = {
                "root": str(baseline_root),
                "bundle_sha256": run_summary["bundle_sha256"],
                "run_summary_sha256": sha256_file(baseline_root / "run_summary.json"),
                "typed_repair_context_content_sha256": typed_context[
                    "content_sha256"
                ],
                "independent_decision": independent["decision"],
            }
            aggregate["deterministic_reference_baseline_count"] += 1

        record = {
            "case_id": case["case_id"],
            "tier": case["tier"],
            "component": case["component"],
            "requirement_obligation_count": len(
                requirement["generation_value_obligations"]
            ),
            "compiled_obligation_count": value_audit["applied_count"],
            "requirement_contract_count": value_audit[
                "requirement_contract_count"
            ],
            "exact_xsd_selection_path_count": len(exact_paths),
            "component_provider_call_count": len(provider_calls),
            "interface_provider_boundary": {
                "identity_skeleton_strategy": interface_skeleton_audit.get(
                    "strategy"
                ),
                "interface_count": interface_skeleton_audit.get(
                    "interface_count"
                ),
                "data_element_count": interface_skeleton_audit.get(
                    "data_element_count"
                ),
                "projection_strategy": interface_projection_plan.get(
                    "strategy"
                ),
                "named_array_count": interface_projection_plan.get(
                    "named_array_count"
                ),
                "admitted_instance_count": interface_projection_plan.get(
                    "admitted_instance_count"
                ),
                "normalization_status": interface_assembly_audit.get(
                    "normalization_status"
                ),
                "reversible": True,
            },
            "provider_projection_strategy": partition_plan.get("strategy"),
            "provider_schema_full_revalidated": merge_audit.get(
                "full_provider_schema_revalidated"
            ),
            "deterministic_removed_path_count": materialization_plan.get(
                "unique_removed_path_count"
            ),
            "deterministic_materialized_path_count": materialization_audit.get(
                "applied_count"
            ),
            "typed_repair_context": {
                "schema_version": typed_context["schema_version"],
                "content_sha256": typed_context["content_sha256"],
                "target_count": len(restored_targets),
                "round_trip": "PASS",
            },
            "component_arxml_sha256": sha256_bytes(component_xml.encode("utf-8")),
            "component_xsd": "PASS",
            "interface_arxml_count": len(interface_xml),
            "interface_xsd": "PASS",
            "parsed_selection_obligations": {
                "decision": obligations.get("decision"),
                "evaluated": obligations.get("evaluated"),
            },
            "same_context_references": {
                "decision": "PASS",
                "count": len(reference_statuses),
                "resolved": reference_statuses.count("resolved"),
            },
            "controlled_mutation_detection": mutation_detection,
            "deterministic_reference_baseline": reference_baseline,
        }
        records.append(record)
        aggregate["case_count"] += 1
        aggregate["component_arxml_count"] += 1
        aggregate["interface_arxml_count"] += len(interface_xml)
        aggregate["xsd_pass_count"] += 1 + len(interface_xml)
        aggregate["selection_obligation_pass_count"] += 1
        aggregate["same_context_reference_pass_count"] += len(reference_statuses)
        aggregate["provider_schema_call_count"] += len(provider_calls)
        print(
            f"PASS {case['case_id']} component=1 interfaces={len(interface_xml)} "
            f"obligations={obligations.get('evaluated')} refs={len(reference_statuses)}"
        )

    manifest_body: dict[str, Any] = {
        "schema_version": "atlas.asw_v3.all_requirements_offline_precheck.v2",
        "created_at_utc": datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "decision": "PASS",
        "execution_boundary": {
            "external_model_api_calls": 0,
            "credential_source": "literal offline placeholder assigned before imports",
            "neo4j_used": True,
            "constraint_corpus_recompiled": False,
        },
        "inputs": {
            "requirements_path": str(REQUIREMENTS_PATH),
            "requirements_sha256": sha256_file(REQUIREMENTS_PATH),
            "requirements_canonical_sha256": canonical_sha256(manifest),
            "xsd_path": str(XSD_PATH),
            "xsd_sha256": sha256_file(XSD_PATH),
        },
        "coverage": aggregate,
        "controlled_repair_design": controlled_design,
        "reference_baselines": {
            "materialized": reference_root is not None,
            "root": str(reference_root) if reference_root is not None else None,
            "count": aggregate["deterministic_reference_baseline_count"],
        },
        "records": records,
    }
    manifest_body["content_sha256"] = canonical_sha256(
        {key: value for key, value in manifest_body.items() if key != "created_at_utc"}
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(manifest_body, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps({"decision": "PASS", "output": str(args.output), **aggregate}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
