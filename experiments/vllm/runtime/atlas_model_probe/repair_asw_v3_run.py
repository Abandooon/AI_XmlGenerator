"""Repair a frozen ASW V3 baseline without regenerating Phase 1 or Phase 2."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from copy import deepcopy
from dataclasses import replace as dataclass_replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lxml import etree

from evaluate_asw_v3_run import evaluate
from experiment_runtime import atomic_write_json, atomic_write_text
from run_asw_v3_experiment import _locate_artifacts
from run_asw_v3_experiment import (
    _run_complete,
    verify_experiment_results,
    verify_schedule,
)
from run_phase12_case import (
    ATLAS_ROOT,
    MODELS,
    _load_runtime_environment,
)


CORE_MUTATIONS = (
    "none",
    "empty_init_value",
    "wrong_init_value",
    "missing_event_behavior_path",
    "missing_required_comspec",
    "wrong_xsd_order",
)

SUBSTITUTE_MUTATIONS = (
    "empty_provided_interface_ref",
    "wrong_provided_interface_ref",
    "missing_provided_port",
    "missing_component_short_name",
    "missing_required_interface_ref",
)

MUTATIONS = CORE_MUTATIONS + SUBSTITUTE_MUTATIONS


_REGRESSION_STOP_REASONS = frozenset({
    "regression",
    "increased_unevaluable_must_rules",
    "lost_evaluated_must_rule_coverage",
})
_NO_IMPROVEMENT_STOP_REASONS = frozenset({
    "no_finding_resolved",
    "no_strict_improvement",
    "repeated_candidate",
    "max_rounds_reached",
    "no_repairable_findings",
})


def classify_attempt_outcome(
    repair_audit: dict[str, Any], *, strict_restoration: bool
) -> str:
    """Map the repair execution to one mutually exclusive paper outcome."""
    attempted = int(repair_audit.get("attempted_rounds") or 0)
    if attempted == 0:
        return "not_attempted"
    if strict_restoration:
        return "resolved"
    stop_reason = str(repair_audit.get("stop_reason") or "")
    if stop_reason in _REGRESSION_STOP_REASONS:
        return "rejected_regression"
    if stop_reason in _NO_IMPROVEMENT_STOP_REASONS:
        return "rejected_no_improvement"
    return "rejected_malformed"


def automation_boundary_reasons(typed_trace: list[dict[str, Any]]) -> list[str]:
    """Collect typed-editor boundary reasons without conflating them with outcome."""
    reasons = {
        str(finding.get("automation_boundary_reason") or "")
        for attempt in typed_trace
        if isinstance(attempt, dict)
        for finding in (attempt.get("findings") or [])
        if isinstance(finding, dict)
    }
    reasons.discard("")
    reasons.discard("none")
    return sorted(reasons) or ["none"]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bundle_sha256(bundle: dict[str, Any]) -> str:
    text = json.dumps(
        bundle, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _parse(xml_text: str) -> etree._Element:
    parser = etree.XMLParser(
        resolve_entities=False, no_network=True, recover=False, huge_tree=True
    )
    return etree.fromstring(xml_text.encode("utf-8"), parser)


def _serialize(root: etree._Element) -> str:
    return etree.tostring(
        root, encoding="unicode", pretty_print=True, xml_declaration=False
    )


def apply_mutation(bundle: dict[str, Any], mutation: str) -> dict[str, Any]:
    if mutation not in MUTATIONS:
        raise ValueError(f"unsupported mutation {mutation!r}")
    result = json.loads(json.dumps(bundle, ensure_ascii=False))
    if mutation == "none":
        return result
    if len(result.get("components") or {}) != 1:
        raise ValueError("mutation requires exactly one component document")
    component_name, xml_text = next(iter(result["components"].items()))
    root = _parse(xml_text)

    def first(tag: str) -> etree._Element:
        matches = root.xpath(f"//*[local-name()='{tag}']")
        if not matches:
            raise ValueError(f"mutation target {tag} is absent")
        return matches[0]

    if mutation == "empty_init_value":
        first("INIT-VALUE").clear()
    elif mutation == "wrong_init_value":
        first("VALUE").text = "1"
    elif mutation == "missing_event_behavior_path":
        reference = first("START-ON-EVENT-REF")
        parts = [item for item in str(reference.text or "").split("/") if item]
        if len(parts) < 4:
            raise ValueError("event reference has no removable behavior segment")
        reference.text = "/" + "/".join([*parts[:2], *parts[3:]])
    elif mutation == "missing_required_comspec":
        comspecs = first("REQUIRED-COM-SPECS")
        parent = comspecs.getparent()
        if parent is None:
            raise ValueError("required comspec has no parent")
        parent.remove(comspecs)
    elif mutation == "wrong_xsd_order":
        components = root.xpath(
            "//*[local-name()='APPLICATION-SW-COMPONENT-TYPE']"
        )
        if len(components) != 1:
            raise ValueError("component root is missing or ambiguous")
        component = components[0]
        short_names = component.xpath("./*[local-name()='SHORT-NAME']")
        ports = component.xpath("./*[local-name()='PORTS']")
        if len(short_names) != 1 or len(ports) != 1:
            raise ValueError("universal XSD-order mutation targets are absent")
        component.remove(ports[0])
        component.insert(component.index(short_names[0]), ports[0])
    elif mutation == "empty_provided_interface_ref":
        reference = first("PROVIDED-INTERFACE-TREF")
        reference.text = ""
    elif mutation == "wrong_provided_interface_ref":
        reference = first("PROVIDED-INTERFACE-TREF")
        reference.text = "/Interfaces/DeterministicallyMissingProvidedInterface"
    elif mutation == "missing_provided_port":
        port = first("P-PORT-PROTOTYPE")
        if port.getparent() is None:
            raise ValueError("provided port has no parent")
        port.getparent().remove(port)
    elif mutation == "missing_component_short_name":
        components = root.xpath(
            "//*[local-name()='APPLICATION-SW-COMPONENT-TYPE']"
        )
        if len(components) != 1:
            raise ValueError("component root is missing or ambiguous")
        short_names = components[0].xpath("./*[local-name()='SHORT-NAME']")
        if len(short_names) != 1:
            raise ValueError("component SHORT-NAME is missing or ambiguous")
        components[0].remove(short_names[0])
    elif mutation == "missing_required_interface_ref":
        reference = first("REQUIRED-INTERFACE-TREF")
        if reference.getparent() is None:
            raise ValueError("required interface reference has no parent")
        reference.getparent().remove(reference)
    result["components"][component_name] = _serialize(root)
    return result


def _bundle_from_files(
    component: Path, interfaces: list[Path]
) -> dict[str, dict[str, str]]:
    bundle: dict[str, dict[str, str]] = {"components": {}, "interfaces": {}}
    component_root = _parse(component.read_text(encoding="utf-8"))
    component_names = component_root.xpath(
        "//*[local-name()='APPLICATION-SW-COMPONENT-TYPE']/*[local-name()='SHORT-NAME']/text()"
    )
    if len(component_names) != 1:
        raise ValueError("baseline component identity is missing or ambiguous")
    bundle["components"][str(component_names[0])] = component.read_text(encoding="utf-8")
    for path in interfaces:
        root = _parse(path.read_text(encoding="utf-8"))
        names = root.xpath(
            "//*[local-name()='SENDER-RECEIVER-INTERFACE']/*[local-name()='SHORT-NAME']/text()"
        )
        if len(names) != 1:
            raise ValueError(
                f"each baseline interface file must contain exactly one interface: {path}"
            )
        bundle["interfaces"][str(names[0])] = path.read_text(encoding="utf-8")
    return bundle


def _load_frozen_typed_repair_context(
    baseline_root: Path,
    baseline_summary: dict[str, Any],
    original_bundle: dict[str, Any],
) -> tuple[Path, dict[str, Any]]:
    """Locate the one context bound to this exact baseline artifact."""
    expected_bundle_sha256 = bundle_sha256(original_bundle)
    matches: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted((baseline_root / "atlas_output").glob(
        "typed_repair_context/*.json"
    )):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(f"cannot read typed-repair context {path}: {error}") from error
        if value.get("bundle_sha256") != expected_bundle_sha256:
            continue
        required = {
            "schema_version",
            "bundle_sha256",
            "xsd_sha256",
            "serialization_manifest_sha256",
            "targets",
            "content_sha256",
        }
        if set(value) != required:
            raise ValueError(f"typed-repair context contract differs: {path}")
        unsigned = {
            key: item for key, item in value.items() if key != "content_sha256"
        }
        if (
            value.get("schema_version") != "atlas.typed_repair_context.v1"
            or value.get("content_sha256")
            != hashlib.sha256(
                json.dumps(
                    unsigned,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest()
        ):
            raise ValueError(f"typed-repair context canonical identity differs: {path}")
        if not isinstance(value.get("targets"), list) or not value["targets"]:
            raise ValueError(f"typed-repair context has no structured targets: {path}")
        relative = path.relative_to(baseline_root).as_posix()
        expected_file_hash = (baseline_summary.get("artifact_hashes") or {}).get(relative)
        if not isinstance(expected_file_hash, str) or len(expected_file_hash) != 64:
            raise ValueError(
                f"typed-repair context is absent from baseline artifact hashes: {relative}"
            )
        if sha256_file(path) != expected_file_hash:
            raise ValueError(f"typed-repair context file hash differs: {relative}")
        matches.append((path, value))
    if len(matches) != 1:
        raise ValueError(
            "baseline must contain exactly one hash-qualified typed-repair context "
            f"for bundle {expected_bundle_sha256}; found {len(matches)}"
        )
    return matches[0]


def _mutate_typed_targets(
    targets: dict[tuple[str, str], Any], mutation: str
) -> dict[tuple[str, str], Any]:
    """Inject value/structure mutations before deterministic rendering.

    ``wrong_xsd_order`` is intentionally excluded because an XSD-driven
    renderer cannot emit that defect.  It is injected after rendering and then
    qualified by ``bind_order_normalization`` as an order-only difference.
    """
    if mutation in {"none", "wrong_xsd_order"}:
        return dict(targets)
    component_keys = [key for key in targets if key[0] == "components"]
    if len(component_keys) != 1:
        raise ValueError("typed mutation requires exactly one component target")
    key = component_keys[0]
    target = targets[key]
    locator = target.locator()

    def first(tag: str):
        matches = [node for node in locator.nodes if node.tag == tag]
        if not matches:
            raise ValueError(f"typed mutation target {tag} is absent")
        return matches[0]

    from src.llm_generation.core.xsd_serializer import canonical_path_to_source

    payload = deepcopy(target.payload)

    def source_path(node, *suffix: str) -> tuple[Any, ...]:
        return tuple(
            canonical_path_to_source(
                tuple(node.json_path) + tuple(suffix), target.projection_map
            )
        )

    def parent(path: tuple[Any, ...]) -> Any:
        value: Any = payload
        for segment in path[:-1]:
            try:
                value = value[segment]
            except (KeyError, IndexError, TypeError) as error:
                raise ValueError(
                    f"typed mutation source path does not resolve: {path!r}"
                ) from error
        return value

    def read(path: tuple[Any, ...]) -> Any:
        value: Any = payload
        for segment in path:
            try:
                value = value[segment]
            except (KeyError, IndexError, TypeError) as error:
                raise ValueError(
                    f"typed mutation source path does not resolve: {path!r}"
                ) from error
        return value

    def set_value(path: tuple[Any, ...], value: Any) -> None:
        holder = parent(path)
        holder[path[-1]] = value

    def delete(path: tuple[Any, ...]) -> None:
        holder = parent(path)
        last = path[-1]
        if isinstance(last, int):
            holder.pop(last)
        else:
            del holder[last]

    if mutation == "empty_init_value":
        set_value(source_path(first("INIT-VALUE")), {})
    elif mutation == "wrong_init_value":
        node = first("VALUE")
        suffix = ("#text",) if isinstance(node.value, dict) else ()
        set_value(source_path(node, *suffix), "1")
    elif mutation == "missing_event_behavior_path":
        node = first("START-ON-EVENT-REF")
        suffix = ("#text",) if isinstance(node.value, dict) else ()
        path = source_path(node, *suffix)
        value = read(path)
        parts = [item for item in str(value or "").split("/") if item]
        if len(parts) < 4:
            raise ValueError("event reference has no removable behavior segment")
        set_value(path, "/" + "/".join([*parts[:2], *parts[3:]]))
    elif mutation == "missing_required_comspec":
        delete(source_path(first("REQUIRED-COM-SPECS")))
    elif mutation == "empty_provided_interface_ref":
        node = first("PROVIDED-INTERFACE-TREF")
        suffix = ("#text",) if isinstance(node.value, dict) else ()
        set_value(source_path(node, *suffix), "")
    elif mutation == "wrong_provided_interface_ref":
        node = first("PROVIDED-INTERFACE-TREF")
        suffix = ("#text",) if isinstance(node.value, dict) else ()
        set_value(
            source_path(node, *suffix),
            "/Interfaces/DeterministicallyMissingProvidedInterface",
        )
    elif mutation == "missing_provided_port":
        delete(source_path(first("P-PORT-PROTOTYPE")))
    elif mutation == "missing_component_short_name":
        delete(source_path(first("SHORT-NAME")))
    elif mutation == "missing_required_interface_ref":
        delete(source_path(first("REQUIRED-INTERFACE-TREF")))
    else:
        raise ValueError(f"unsupported typed mutation {mutation!r}")

    updated = dict(targets)
    updated[key] = dataclass_replace(target, payload=payload)
    return updated


def _write_bundle(root: Path, bundle: dict[str, Any]) -> None:
    for kind in ("components", "interfaces"):
        directory = root / kind
        directory.mkdir(parents=True, exist_ok=True)
        for name, xml_text in sorted((bundle.get(kind) or {}).items()):
            atomic_write_text(directory / f"{name}.arxml", xml_text)


def _component_plans(baseline_root: Path) -> list[dict[str, Any]]:
    metrics = sorted((baseline_root / "metrics").rglob("*_metrics.json"))
    if len(metrics) != 1:
        raise ValueError(f"expected one baseline metrics file, found {len(metrics)}")
    value = json.loads(metrics[0].read_text(encoding="utf-8"))
    plans = ((value.get("phase1") or {}).get("blueprint") or {}).get(
        "component_plan"
    )
    if not isinstance(plans, list) or not plans:
        raise ValueError("baseline metrics do not contain Phase 1 component plans")
    if any(
        not isinstance((plan.get("element_design") or {}).get("selections"), list)
        for plan in plans
    ):
        raise ValueError("baseline Phase 1 plans lack parsed element selections")
    return plans


def repair_run(
    *,
    baseline_root: Path,
    output_root: Path,
    case_id: str,
    model: str,
    seed: int,
    mutation: str,
    max_rounds: int,
    repair_schedule_sha256: str,
    attempt_number: int,
    offline_scripted: bool = False,
) -> dict[str, Any]:
    baseline_root = baseline_root.resolve()
    output_root = output_root.resolve()
    if output_root.exists() and any(output_root.iterdir()):
        raise FileExistsError(f"repair output root is not empty: {output_root}")
    output_root.mkdir(parents=True, exist_ok=True)
    os.environ["ATLAS_PROVIDER_AUDIT_PATH"] = str(
        output_root / "provider_calls.jsonl"
    )
    summary = json.loads(
        (baseline_root / "run_summary.json").read_text(encoding="utf-8")
    )
    component, interfaces, validation_path = _locate_artifacts(
        baseline_root, str(summary["system_name"])
    )
    baseline_validation = json.loads(validation_path.read_text(encoding="utf-8"))
    validation_context = (baseline_validation.get("validation_context") or {}).get(
        "manifest"
    )
    if not isinstance(validation_context, dict):
        raise ValueError("baseline lacks a hash-pinned validation context")
    component_plans = _component_plans(baseline_root)
    original_bundle = _bundle_from_files(component, interfaces)

    if str(ATLAS_ROOT) not in sys.path:
        sys.path.insert(0, str(ATLAS_ROOT))
    from src.llm_generation.config import CONFIG
    from src.llm_generation.core.round2_generator import Round2Generator
    from src.llm_generation.core.typed_repair import render_documents
    from src.validation.v2.repair_loop import BundleRepairLoop

    CONFIG.llm.model_name = model
    contract = json.loads(
        (Path(__file__).resolve().parent / "FORMAL_EXPERIMENT_CONTRACT.json")
        .read_text(encoding="utf-8")
    )
    generation_contract = contract["generation"]
    repair_contract = contract["repair_experiment"]
    if max_rounds != int(repair_contract["max_rounds"]):
        raise ValueError("repair max rounds differs from formal contract")
    CONFIG.llm.max_output_tokens = int(generation_contract["max_completion_tokens"])
    CONFIG.llm.max_retries = int(
        generation_contract["provider_max_attempts_per_call"]
    )
    provider_registration = generation_contract["provider_registration"]
    if model != provider_registration["requested_model"]:
        raise ValueError("repair provider model differs from preregistration")
    if CONFIG.llm.max_retries != int(
        provider_registration["max_attempts_per_call"]
    ):
        raise ValueError("repair provider retry identity is internally inconsistent")
    CONFIG.llm.request_timeout_seconds = float(
        provider_registration["request_timeout_seconds"]
    )
    expected_route_policy = str(
        provider_registration.get("transport_route_policy") or ""
    )
    if (
        expected_route_policy != "direct_no_environment_proxy"
        or generation_contract.get("transport_route_policy")
        != expected_route_policy
    ):
        raise ValueError("repair provider route policy is incomplete or changed")
    CONFIG.llm.transport_route_policy = expected_route_policy
    CONFIG.llm.reasoning_effort = str(generation_contract["reasoning_effort"])
    CONFIG.llm.strict_json_schema = True
    CONFIG.validation.auto_repair_temperature = float(repair_contract["temperature"])
    CONFIG.llm.stream_responses = bool(contract["generation"]["stream_responses"])
    CONFIG.output_dir = output_root / "runtime"
    CONFIG.output_dir.mkdir(parents=True, exist_ok=True)
    generator = Round2Generator()
    if (
        getattr(generator.gemini_client, "transport_route_policy", None)
        != expected_route_policy
    ):
        raise RuntimeError("repair provider route policy invariant failed at startup")
    if offline_scripted:
        from scripted_autosar_client import ScriptedAutosarClient

        generator.gemini_client = ScriptedAutosarClient(
            case_id, requested_model=model
        )
    generator._generation_seed = seed
    if generator.validation_service is None:
        raise RuntimeError("hash-pinned validation service is disabled")
    typed_context_path, typed_context = _load_frozen_typed_repair_context(
        baseline_root, summary, original_bundle
    )
    baseline_targets = generator._typed_repair.restore_context(
        typed_context, original_bundle
    )
    if mutation == "wrong_xsd_order":
        input_bundle = apply_mutation(original_bundle, mutation)
        generator._typed_repair.bind_order_normalization(
            baseline_targets, input_bundle
        )
    elif mutation == "none":
        input_bundle = original_bundle
    else:
        mutated_targets = _mutate_typed_targets(baseline_targets, mutation)
        input_bundle = render_documents(
            mutated_targets, serializer=generator.xml_serializer
        )
        generator._typed_repair.bind(mutated_targets, input_bundle)
    _write_bundle(output_root / "input", input_bundle)

    def enrich(candidate: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
        return generator._merge_bundle_selection_obligations(
            candidate, report, component_plans
        )

    initial_validation = generator.validation_service.validate_bundle(
        input_bundle, validation_context=validation_context
    )
    initial_validation = enrich(input_bundle, initial_validation)
    if (initial_validation.get("validation_context") or {}).get("status") == "ERROR":
        raise ValueError("baseline validation context is incompatible with this validator")
    initial_validation_path = output_root / "initial_validation.json"
    atomic_write_json(initial_validation_path, initial_validation)
    initial_component = output_root / "input/components" / f"{summary['system_name']}.arxml"
    initial_interfaces = sorted((output_root / "input/interfaces").glob("*.arxml"))
    initial_independent = evaluate(
        case_id=case_id,
        component_path=initial_component,
        interface_paths=initial_interfaces,
        validation_path=initial_validation_path,
    )
    atomic_write_json(
        output_root / "initial_independent_evaluation.json", initial_independent
    )
    if mutation != "none" and initial_independent["decision"] == "PASS":
        raise ValueError(
            f"controlled mutation {mutation!r} was not detected by strict validation"
        )

    loop = BundleRepairLoop(
        generator.validation_service,
        generator._repair_bundle_candidate,
        max_rounds=max_rounds,
        report_enricher=enrich,
    )
    final_bundle, final_validation, repair_audit = loop.run(
        input_bundle,
        initial_validation,
        validation_context=validation_context,
    )
    _write_bundle(output_root / "final", final_bundle)
    final_validation_path = output_root / "final_validation.json"
    atomic_write_json(final_validation_path, final_validation)
    atomic_write_json(output_root / "repair_audit.json", repair_audit)
    typed_repair_trace = list(generator._typed_repair.trace)
    atomic_write_json(output_root / "typed_repair_trace.json", typed_repair_trace)
    final_component = output_root / "final/components" / f"{summary['system_name']}.arxml"
    final_interfaces = sorted((output_root / "final/interfaces").glob("*.arxml"))
    independent = evaluate(
        case_id=case_id,
        component_path=final_component,
        interface_paths=final_interfaces,
        validation_path=final_validation_path,
    )
    atomic_write_json(output_root / "independent_evaluation.json", independent)
    strict_restoration = (
        initial_independent["decision"] != "PASS"
        and independent["decision"] == "PASS"
    )
    attempt_outcome = classify_attempt_outcome(
        repair_audit, strict_restoration=strict_restoration
    )
    artifacts = {
        path.relative_to(output_root).as_posix(): sha256_file(path)
        for path in sorted(item for item in output_root.rglob("*") if item.is_file())
    }
    provider_responses = list(generator.gemini_client.response_audit)
    expected_audit_route = (
        "offline_scripted_no_network"
        if offline_scripted
        else expected_route_policy
    )
    if any(
        item.get("transport_route_policy") != expected_audit_route
        for item in provider_responses
    ):
        raise RuntimeError("repair provider audit route policy invariant failed")
    result = {
        "schema_version": "atlas.asw_v3.repair_experiment.v2",
        "case_id": case_id,
        "model": model,
        "seed": seed,
        "mutation": mutation,
        "max_rounds": max_rounds,
        "repair_schedule_sha256": repair_schedule_sha256,
        "offline_scripted": offline_scripted,
        "external_model_api_calls": 0 if offline_scripted else None,
        "attempt_number": attempt_number,
        "baseline_root": str(baseline_root),
        "baseline_run_summary_sha256": sha256_file(
            baseline_root / "run_summary.json"
        ),
        "typed_repair_context_path": str(typed_context_path),
        "typed_repair_context_file_sha256": sha256_file(typed_context_path),
        "typed_repair_context_content_sha256": typed_context["content_sha256"],
        "original_bundle_sha256": bundle_sha256(original_bundle),
        "input_bundle_sha256": bundle_sha256(input_bundle),
        "final_bundle_sha256": bundle_sha256(final_bundle),
        "initial_full_corpus_decision": initial_validation.get("decision"),
        "initial_artifact_profile_decision": (
            initial_validation.get("artifact_profile") or {}
        ).get("decision"),
        "initial_independent_decision": initial_independent["decision"],
        "initial_xsd_failure_count": sum(
            item.get("status") != "PASS" for item in initial_independent.get("xsd") or []
        ),
        "initial_structural_failure_count": initial_independent.get(
            "structural_failure_count"
        ),
        "initial_local_reference_failure_count": initial_independent.get(
            "local_reference_failure_count"
        ),
        "final_full_corpus_decision": final_validation.get("decision"),
        "final_artifact_profile_decision": (
            final_validation.get("artifact_profile") or {}
        ).get("decision"),
        "independent_decision": independent["decision"],
        "strict_restoration": strict_restoration,
        "input_differs_from_original": (
            bundle_sha256(input_bundle) != bundle_sha256(original_bundle)
        ),
        "exact_original_recovery": (
            bundle_sha256(final_bundle) == bundle_sha256(original_bundle)
        ),
        "repair_triggered": repair_audit["attempted_rounds"] > 0,
        "repair_attempted_rounds": repair_audit["attempted_rounds"],
        "repair_accepted_rounds": repair_audit["accepted_rounds"],
        "repair_stop_reason": repair_audit.get("stop_reason"),
        "attempt_outcome": attempt_outcome,
        "automation_boundary_reason": automation_boundary_reasons(
            typed_repair_trace
        ),
        "typed_repair_trace": typed_repair_trace,
        "repair_token_usage": repair_audit.get("token_usage") or {},
        "provider_responses": provider_responses,
        "provider_runtime_gate": {
            "decision": "PASS",
            "concrete_transport_route_policy": expected_route_policy,
            "observed_audit_transport_route_policies": sorted({
                str(item.get("transport_route_policy"))
                for item in provider_responses
            }),
        },
        "completed_at_utc": datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "artifact_hashes": artifacts,
    }
    result["manifest_sha256"] = hashlib.sha256(
        json.dumps(
            result, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()
    atomic_write_json(output_root / "repair_experiment_manifest.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--model", choices=MODELS, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--mutation", choices=MUTATIONS, default="none")
    parser.add_argument("--max-rounds", type=int, default=2)
    parser.add_argument("--generation-results", type=Path, required=True)
    parser.add_argument(
        "--controlled-reference-manifest", type=Path, required=True
    )
    parser.add_argument("--baseline-run-id", required=True)
    parser.add_argument("--repair-schedule-sha256", required=True)
    parser.add_argument("--attempt-number", type=int, required=True)
    parser.add_argument("--offline-scripted", action="store_true")
    args = parser.parse_args()
    generation_results = json.loads(
        args.generation_results.read_text(encoding="utf-8")
    )
    verify_experiment_results(generation_results)
    from run_asw_v3_repair_experiment import build_schedule as build_repair_schedule

    repair_schedule = build_repair_schedule(
        args.generation_results, args.controlled_reference_manifest
    )
    if repair_schedule["content_sha256"] != args.repair_schedule_sha256:
        raise ValueError("repair schedule identity differs from invocation")
    repair_items = [
        item for item in repair_schedule["runs"]
        if item["baseline_run_id"] == args.baseline_run_id
        and item["model"] == args.model
        and item["case_id"] == args.case_id
        and item["seed"] == args.seed
        and item["mutation"] == args.mutation
    ]
    if len(repair_items) != 1:
        raise ValueError("repair invocation is absent or ambiguous in frozen schedule")
    repair_item = repair_items[0]
    if Path(str(repair_item["baseline_root"])).resolve() != args.baseline_root.resolve():
        raise ValueError("repair baseline path differs from frozen repair schedule")
    if repair_item["cohort"] == "natural_failure":
        generation_schedule = verify_schedule(
            generation_results.get("schedule") or {}
        )
        scheduled = next(
            (
                item for item in generation_schedule["runs"]
                if item["run_id"] == args.baseline_run_id
            ),
            None,
        )
        record = next(
            (
                item for item in generation_results.get("records") or []
                if item.get("run_id") == args.baseline_run_id
            ),
            None,
        )
        if scheduled is None or record is None or not _run_complete(
            args.baseline_root.resolve(),
            scheduled,
            generation_schedule,
            int(record["attempt_number"]),
        ):
            raise ValueError("repair baseline does not match a completed frozen run")
        if (
            scheduled["model"] != args.model
            or scheduled["case_id"] != args.case_id
            or scheduled["seed"] != args.seed
            or Path(str(record["run_root"])).resolve()
            != args.baseline_root.resolve()
        ):
            raise ValueError("repair baseline identity differs from invocation")
    elif repair_item["cohort"] != "controlled_mutation":
        raise ValueError("repair cohort is unsupported")
    if args.offline_scripted:
        os.environ["LLM_API_KEY"] = "offline-local-placeholder"
    else:
        _load_runtime_environment()
    result = repair_run(
        baseline_root=args.baseline_root,
        output_root=args.output_root,
        case_id=args.case_id,
        model=args.model,
        seed=args.seed,
        mutation=args.mutation,
        max_rounds=args.max_rounds,
        repair_schedule_sha256=args.repair_schedule_sha256,
        attempt_number=args.attempt_number,
        offline_scripted=args.offline_scripted,
    )
    print(
        json.dumps(
            {
                "initial_artifact_profile_decision": result[
                    "initial_artifact_profile_decision"
                ],
                "final_artifact_profile_decision": result[
                    "final_artifact_profile_decision"
                ],
                "independent_decision": result["independent_decision"],
                "repair_accepted_rounds": result["repair_accepted_rounds"],
                "manifest_sha256": result["manifest_sha256"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if result["independent_decision"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
