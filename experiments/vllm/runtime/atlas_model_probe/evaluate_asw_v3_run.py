"""Independent, parsed evaluator for one curated ASW V3 pipeline run."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from lxml import etree


ATLAS_ROOT = Path(r"E:\git projects\AI_XmlGenerator")
CASES_ROOT = Path(r"E:\54239\Documents\atlas_autosar_requirements_v3")
XSD = ATLAS_ROOT / "src/validation/data/AUTOSAR_4-2-2.xsd"
NS = "http://autosar.org/schema/r4.0"
N = {"ar": NS}
SHA256_LENGTH = 64


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _local(node: etree._Element) -> str:
    return etree.QName(node).localname


def _children(node: etree._Element, tag: str) -> list[etree._Element]:
    return [child for child in node if _local(child) == tag]


def _one_text(node: etree._Element, xpath: str) -> list[str]:
    return [str(item).strip() for item in node.xpath(xpath, namespaces=N)]


def _short_name(node: etree._Element) -> str:
    values = _children(node, "SHORT-NAME")
    return str(values[0].text or "").strip() if len(values) == 1 else ""


def _decimal_equal(actual: object, expected: object) -> bool:
    try:
        return Decimal(str(actual)) == Decimal(str(expected))
    except InvalidOperation:
        return False


def _obligation(
    code: str,
    expected: Any,
    actual: Any,
    passed: bool,
    *,
    subject: str | None = None,
) -> dict[str, Any]:
    return {
        "code": code,
        "subject": subject,
        "status": "PASS" if passed else "FAIL",
        "expected": expected,
        "actual": actual,
    }


def _identity_paths(roots: list[etree._Element]) -> Counter[str]:
    paths: Counter[str] = Counter()

    def visit(node: etree._Element, parent_path: str) -> None:
        name = _short_name(node)
        current = parent_path
        if name:
            current = f"{parent_path}/{name}"
            paths[current] += 1
        for child in node:
            if _local(child) != "SHORT-NAME":
                visit(child, current)

    for root in roots:
        for package in root.xpath(
            "/ar:AUTOSAR/ar:AR-PACKAGES/ar:AR-PACKAGE", namespaces=N
        ):
            package_name = _short_name(package)
            if not package_name:
                continue
            package_path = f"/{package_name}"
            paths[package_path] += 1
            for element in package.xpath("./ar:ELEMENTS/*", namespaces=N):
                visit(element, package_path)
    return paths


def _load_case(
    case_id: str, cohort: str = "primary"
) -> tuple[dict[str, Any], dict[str, Any], str, str, str]:
    if cohort == "primary":
        if str(CASES_ROOT) not in sys.path:
            sys.path.insert(0, str(CASES_ROOT))
        from render_cases import canonical_sha256, load_manifest, validate_manifest

        source = CASES_ROOT / "asw_cases_v3.yaml"
        manifest = load_manifest(source)
        source_canonical_sha256 = canonical_sha256(manifest)
    elif cohort == "heldout":
        from heldout_v3_runtime import SOURCE, load_manifest, validate_manifest

        source = SOURCE
        manifest = load_manifest()
        source_canonical_sha256 = manifest["review_source_canonical_sha256"]
    else:
        raise ValueError(f"unsupported AUTOSAR cohort: {cohort!r}")
    if validate_manifest(manifest).get("status") != "PASS":
        raise ValueError(f"AUTOSAR {cohort} manifest failed validation")
    matches = [case for case in manifest["cases"] if case["case_id"] == case_id]
    if len(matches) != 1:
        raise ValueError(f"expected one case named {case_id!r}")
    case = matches[0]
    case_sha256 = str(case.get("review_source_case_sha256") or "")
    if not case_sha256:
        from render_cases import canonical_sha256

        case_sha256 = canonical_sha256(case)
    return manifest, case, sha256_file(source), source_canonical_sha256, case_sha256


def _parse(path: Path) -> etree._Element:
    parser = etree.XMLParser(
        resolve_entities=False, no_network=True, recover=False, huge_tree=True
    )
    return etree.parse(str(path), parser).getroot()


def _component_obligations(
    root: etree._Element,
    interface_roots: list[etree._Element],
    manifest: dict[str, Any],
    case: dict[str, Any],
) -> list[dict[str, Any]]:
    obligations: list[dict[str, Any]] = []
    catalog = manifest["authoritative_context"]["interface_catalog"]
    init_value = manifest["authoritative_context"][
        "unconnected_required_port_init_value"
    ]
    components = [
        node
        for node in root.xpath("//ar:APPLICATION-SW-COMPONENT-TYPE", namespaces=N)
        if _short_name(node) == case["component"]
    ]
    obligations.append(
        _obligation(
            "component_identity",
            [case["component"]],
            [_short_name(node) for node in components],
            len(components) == 1,
        )
    )
    if len(components) != 1:
        return obligations
    component = components[0]
    expected_counts = case["expected_counts"]
    for code, tag, expected in (
        ("p_port_count", "P-PORT-PROTOTYPE", expected_counts["p_ports"]),
        ("r_port_count", "R-PORT-PROTOTYPE", expected_counts["r_ports"]),
        ("runnable_count", "RUNNABLE-ENTITY", expected_counts["runnables"]),
        ("timing_event_count_global", "TIMING-EVENT", expected_counts["timing_events"]),
        ("variable_access_count", "VARIABLE-ACCESS", expected_counts["variable_accesses"]),
    ):
        actual = int(component.xpath(f"count(.//ar:{tag})", namespaces=N))
        obligations.append(_obligation(code, expected, actual, actual == expected))
    p_ports = component.xpath("./ar:PORTS/ar:P-PORT-PROTOTYPE", namespaces=N)
    r_ports = component.xpath("./ar:PORTS/ar:R-PORT-PROTOTYPE", namespaces=N)
    expected_p = [f"Pp_{signal}" for signal in case.get("provided_signals") or []]
    expected_r = [
        f"Rp_{spec['signal']}" for spec in case.get("required_signals") or []
    ]
    obligations.extend(
        [
            _obligation(
                "p_port_names",
                sorted(expected_p),
                sorted(_short_name(node) for node in p_ports),
                Counter(expected_p) == Counter(_short_name(node) for node in p_ports),
            ),
            _obligation(
                "r_port_names",
                sorted(expected_r),
                sorted(_short_name(node) for node in r_ports),
                Counter(expected_r) == Counter(_short_name(node) for node in r_ports),
            ),
        ]
    )
    p_by_name = {_short_name(node): node for node in p_ports}
    r_by_name = {_short_name(node): node for node in r_ports}
    for signal in case.get("provided_signals") or []:
        name = f"Pp_{signal}"
        port = p_by_name.get(name)
        expected_ref = catalog[signal]["interface_ref"]
        actual = [] if port is None else _one_text(
            port, "./ar:PROVIDED-INTERFACE-TREF/text()"
        )
        dest = [] if port is None else _one_text(
            port, "./ar:PROVIDED-INTERFACE-TREF/@DEST"
        )
        obligations.append(
            _obligation("provided_interface_ref", [expected_ref], actual, actual == [expected_ref], subject=name)
        )
        obligations.append(
            _obligation(
                "provided_interface_dest",
                ["SENDER-RECEIVER-INTERFACE"],
                dest,
                dest == ["SENDER-RECEIVER-INTERFACE"],
                subject=name,
            )
        )

    for spec in case.get("required_signals") or []:
        signal = spec["signal"]
        name = f"Rp_{signal}"
        port = r_by_name.get(name)
        expected_ref = catalog[signal]["interface_ref"]
        interface_ref = [] if port is None else _one_text(
            port, "./ar:REQUIRED-INTERFACE-TREF/text()"
        )
        interface_dest = [] if port is None else _one_text(
            port, "./ar:REQUIRED-INTERFACE-TREF/@DEST"
        )
        comspecs = [] if port is None else port.xpath(
            "./ar:REQUIRED-COM-SPECS/ar:NONQUEUED-RECEIVER-COM-SPEC",
            namespaces=N,
        )
        obligations.extend(
            [
                _obligation("required_interface_ref", [expected_ref], interface_ref, interface_ref == [expected_ref], subject=name),
                _obligation(
                    "required_interface_dest",
                    ["SENDER-RECEIVER-INTERFACE"],
                    interface_dest,
                    interface_dest == ["SENDER-RECEIVER-INTERFACE"],
                    subject=name,
                ),
                _obligation("nonqueued_comspec_count", 1, len(comspecs), len(comspecs) == 1, subject=name),
            ]
        )
        if len(comspecs) != 1:
            continue
        comspec = comspecs[0]
        expected_data_ref = f"{expected_ref}/{catalog[signal]['data_element']}"
        data_ref = _one_text(comspec, "./ar:DATA-ELEMENT-REF/text()")
        data_dest = _one_text(comspec, "./ar:DATA-ELEMENT-REF/@DEST")
        timeout = _one_text(comspec, "./ar:ALIVE-TIMEOUT/text()")
        handle = _one_text(comspec, "./ar:HANDLE-TIMEOUT-TYPE/text()")
        numeric_init = _one_text(
            comspec,
            "./ar:INIT-VALUE/ar:NUMERICAL-VALUE-SPECIFICATION/ar:VALUE/text()",
        )
        obligations.extend(
            [
                _obligation("comspec_data_element_ref", [expected_data_ref], data_ref, data_ref == [expected_data_ref], subject=name),
                _obligation("comspec_data_element_dest", ["VARIABLE-DATA-PROTOTYPE"], data_dest, data_dest == ["VARIABLE-DATA-PROTOTYPE"], subject=name),
                _obligation("alive_timeout", spec["alive_timeout_s"], timeout, len(timeout) == 1 and _decimal_equal(timeout[0], spec["alive_timeout_s"]), subject=name),
                _obligation("handle_timeout_type", [spec["handle_timeout_type"]], handle, handle == [spec["handle_timeout_type"]], subject=name),
                _obligation("unconnected_numeric_init_value", init_value, numeric_init, len(numeric_init) == 1 and _decimal_equal(numeric_init[0], init_value), subject=name),
            ]
        )

    all_interface_nodes = [
        node
        for interface_root in interface_roots
        for node in interface_root.xpath("//ar:SENDER-RECEIVER-INTERFACE", namespaces=N)
    ]
    interface_by_name: dict[str, list[etree._Element]] = {}
    for node in all_interface_nodes:
        interface_by_name.setdefault(_short_name(node), []).append(node)
    involved = [
        *case.get("provided_signals", []),
        *(spec["signal"] for spec in case.get("required_signals") or []),
    ]
    for signal in involved:
        interface_name = catalog[signal]["interface_ref"].rsplit("/", 1)[-1]
        matches = interface_by_name.get(interface_name, [])
        obligations.append(
            _obligation("interface_definition_count", 1, len(matches), len(matches) == 1, subject=interface_name)
        )
        data_names = [] if len(matches) != 1 else _one_text(
            matches[0], "./ar:DATA-ELEMENTS/ar:VARIABLE-DATA-PROTOTYPE/ar:SHORT-NAME/text()"
        )
        obligations.append(
            _obligation("interface_data_element", [catalog[signal]["data_element"]], data_names, data_names == [catalog[signal]["data_element"]], subject=interface_name)
        )
        if len(matches) == 1 and catalog[signal].get("type_ref"):
            type_refs = _one_text(
                matches[0],
                "./ar:DATA-ELEMENTS/ar:VARIABLE-DATA-PROTOTYPE/ar:TYPE-TREF/text()",
            )
            type_dests = _one_text(
                matches[0],
                "./ar:DATA-ELEMENTS/ar:VARIABLE-DATA-PROTOTYPE/ar:TYPE-TREF/@DEST",
            )
            obligations.extend(
                [
                    _obligation(
                        "interface_data_type_ref",
                        [catalog[signal]["type_ref"]],
                        type_refs,
                        type_refs == [catalog[signal]["type_ref"]],
                        subject=interface_name,
                    ),
                    _obligation(
                        "interface_data_type_dest",
                        [catalog[signal]["type_dest"]],
                        type_dests,
                        type_dests == [catalog[signal]["type_dest"]],
                        subject=interface_name,
                    ),
                ]
            )

    behavior_spec = case.get("internal_behavior")
    behaviors = component.xpath(
        "./ar:INTERNAL-BEHAVIORS/ar:SWC-INTERNAL-BEHAVIOR", namespaces=N
    )
    if behavior_spec is None:
        obligations.append(_obligation("internal_behavior_absent", 0, len(behaviors), len(behaviors) == 0))
    else:
        matching_behaviors = [
            node for node in behaviors if _short_name(node) == behavior_spec["short_name"]
        ]
        obligations.append(
            _obligation("internal_behavior_identity", [behavior_spec["short_name"]], [_short_name(node) for node in behaviors], len(behaviors) == 1 and len(matching_behaviors) == 1)
        )
        if len(matching_behaviors) == 1:
            behavior = matching_behaviors[0]
            runnable_nodes = behavior.xpath("./ar:RUNNABLES/ar:RUNNABLE-ENTITY", namespaces=N)
            expected_runnables = [item["short_name"] for item in behavior_spec["runnables"]]
            obligations.append(
                _obligation("runnable_names", sorted(expected_runnables), sorted(_short_name(node) for node in runnable_nodes), Counter(expected_runnables) == Counter(_short_name(node) for node in runnable_nodes))
            )
            runnable_by_name = {_short_name(node): node for node in runnable_nodes}
            events = behavior.xpath("./ar:EVENTS/ar:TIMING-EVENT", namespaces=N)
            obligations.append(_obligation("timing_event_count", len(expected_runnables), len(events), len(events) == len(expected_runnables)))
            for runnable_spec in behavior_spec["runnables"]:
                runnable_name = runnable_spec["short_name"]
                runnable_path = (
                    f"/Components/{case['component']}/{behavior_spec['short_name']}/"
                    f"{runnable_name}"
                )
                matching_events = [
                    event
                    for event in events
                    if _one_text(event, "./ar:START-ON-EVENT-REF/text()") == [runnable_path]
                ]
                periods = [
                    value
                    for event in matching_events
                    for value in _one_text(event, "./ar:PERIOD/text()")
                ]
                dests = [
                    value
                    for event in matching_events
                    for value in _one_text(event, "./ar:START-ON-EVENT-REF/@DEST")
                ]
                obligations.extend(
                    [
                        _obligation("runnable_timing_event", 1, len(matching_events), len(matching_events) == 1, subject=runnable_name),
                        _obligation("runnable_period", runnable_spec["period_s"], periods, len(periods) == 1 and _decimal_equal(periods[0], runnable_spec["period_s"]), subject=runnable_name),
                        _obligation("runnable_event_dest", ["RUNNABLE-ENTITY"], dests, dests == ["RUNNABLE-ENTITY"], subject=runnable_name),
                    ]
                )
                runnable = runnable_by_name.get(runnable_name)
                for direction, signals, container, expected_dest in (
                    ("read", runnable_spec["reads"], "DATA-RECEIVE-POINT-BY-ARGUMENTS", "R-PORT-PROTOTYPE"),
                    ("write", runnable_spec["writes"], "DATA-SEND-POINTS", "P-PORT-PROTOTYPE"),
                ):
                    accesses = [] if runnable is None else runnable.xpath(
                        f"./ar:{container}/ar:VARIABLE-ACCESS", namespaces=N
                    )
                    actual_pairs = []
                    actual_dests = []
                    for access in accesses:
                        port_refs = _one_text(access, ".//ar:PORT-PROTOTYPE-REF/text()")
                        data_refs = _one_text(access, ".//ar:TARGET-DATA-PROTOTYPE-REF/text()")
                        port_dests = _one_text(access, ".//ar:PORT-PROTOTYPE-REF/@DEST")
                        data_dests = _one_text(access, ".//ar:TARGET-DATA-PROTOTYPE-REF/@DEST")
                        if len(port_refs) == len(data_refs) == 1:
                            actual_pairs.append([port_refs[0], data_refs[0]])
                        actual_dests.extend([*port_dests, *data_dests])
                    expected_pairs = []
                    for signal in signals:
                        port_prefix = "Rp" if direction == "read" else "Pp"
                        expected_pairs.append(
                            [
                                f"/Components/{case['component']}/{port_prefix}_{signal}",
                                f"{catalog[signal]['interface_ref']}/{catalog[signal]['data_element']}",
                            ]
                        )
                    obligations.extend(
                        [
                            _obligation(f"{direction}_access_pairs", sorted(expected_pairs), sorted(actual_pairs), Counter(map(tuple, expected_pairs)) == Counter(map(tuple, actual_pairs)), subject=runnable_name),
                            _obligation(f"{direction}_access_dest_values", sorted([expected_dest, "VARIABLE-DATA-PROTOTYPE"] * len(signals)), sorted(actual_dests), Counter([expected_dest, "VARIABLE-DATA-PROTOTYPE"] * len(signals)) == Counter(actual_dests), subject=runnable_name),
                        ]
                    )

    forbidden_tags = {
        "CAN-CLUSTER",
        "CLIENT-SERVER-INTERFACE",
        "ECU-INSTANCE",
        "ETHERNET-CLUSTER",
        "MODE-SWITCH-INTERFACE",
        "PARAMETER-INTERFACE",
        "ROOT-SW-COMPOSITION-PROTOTYPE",
        "SW-COMPONENT-PROTOTYPE",
        "SYNCHRONOUS-SERVER-CALL-POINT",
        "SYSTEM",
    }
    observed_forbidden = sorted(
        {_local(node) for node in root.iter()} & forbidden_tags
    )
    obligations.append(
        _obligation("excluded_constructs_absent", [], observed_forbidden, not observed_forbidden)
    )
    return obligations


def evaluate(
    *,
    case_id: str,
    component_path: Path,
    interface_paths: list[Path],
    validation_path: Path | None,
    cohort: str = "primary",
) -> dict[str, Any]:
    (
        manifest,
        case,
        source_sha256,
        source_canonical_sha256,
        case_sha256,
    ) = _load_case(case_id, cohort)
    component_root = _parse(component_path)
    interface_roots = [_parse(path) for path in interface_paths]
    roots = [component_root, *interface_roots]
    parser = etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=True)
    schema = etree.XMLSchema(etree.parse(str(XSD), parser))
    xsd_results = []
    for path in [component_path, *interface_paths]:
        document = etree.parse(str(path), parser)
        valid = schema.validate(document)
        xsd_results.append(
            {
                "file": str(path.resolve()),
                "sha256": sha256_file(path),
                "status": "PASS" if valid else "FAIL",
                "errors": [str(item) for item in schema.error_log],
            }
        )
    obligations = _component_obligations(
        component_root, interface_roots, manifest, case
    )
    identities = _identity_paths(roots)
    authoritative_context = manifest["authoritative_context"]
    declared_context_targets = {
        str(entry["type_ref"])
        for entry in authoritative_context.get("interface_catalog", {}).values()
        if isinstance(entry, dict) and entry.get("type_ref")
    }
    declared_context_targets.update(
        str(entry["base_type_ref"])
        for entry in authoritative_context.get("implementation_data_types", {}).values()
        if isinstance(entry, dict) and entry.get("base_type_ref")
    )
    interface_package_prefixes = {
        f"{str(entry['interface_ref']).rsplit('/', 1)[0]}/"
        for entry in authoritative_context.get("interface_catalog", {}).values()
        if isinstance(entry, dict)
        and str(entry.get("interface_ref") or "").startswith("/")
        and "/" in str(entry["interface_ref"])[1:]
    }
    local_reference_prefixes = {"/Components/", *interface_package_prefixes}
    references: list[dict[str, Any]] = []
    for root, source in zip(roots, [component_path, *interface_paths]):
        for ref in root.iter():
            tag = _local(ref)
            if not tag.endswith(("-REF", "-TREF", "-IREF")):
                continue
            if len(ref):
                # AUTOSAR also uses *-IREF names for structured instance-ref
                # containers. Only leaf reference values participate here.
                continue
            target = str(ref.text or "").strip()
            if not target.startswith("/"):
                status, reason = "FAIL", "reference is not an absolute path"
            elif identities[target]:
                count = identities[target]
                status = "PASS" if count == 1 else "FAIL"
                reason = f"same-context target count is {count}"
            elif target in declared_context_targets:
                status = "PASS"
                reason = (
                    "exact target is declared by the hash-pinned held-out "
                    "authoritative type context"
                )
            elif any(target.startswith(prefix) for prefix in local_reference_prefixes):
                status = "FAIL"
                reason = "declared same-bundle target is absent"
            else:
                status, reason = "NOT_EVALUATED", "external catalog is not in the supplied bundle"
            references.append(
                {
                    "source_file": str(source.resolve()),
                    "tag": tag,
                    "dest": ref.get("DEST"),
                    "target": target,
                    "status": status,
                    "reason": reason,
                }
            )

    validation: dict[str, Any] | None = None
    validation_status = "NOT_EVALUATED"
    if validation_path is not None:
        validation = json.loads(validation_path.read_text(encoding="utf-8"))
        artifact = validation.get("artifact_profile") or {}
        validator_sha256 = str(validation.get("validator_sha256") or "")
        context_hash = str(
            ((validation.get("validation_context") or {}).get("manifest") or {}).get(
                "manifest_sha256"
            )
            or ""
        )
        selection_decision = str(
            (validation.get("selection_obligations") or {}).get("decision") or ""
        )
        if (
            artifact.get("decision") == "PASS"
            and selection_decision == "PASS"
            and len(validator_sha256) == SHA256_LENGTH
            and len(context_hash) == SHA256_LENGTH
        ):
            validation_status = "PASS"
        elif artifact.get("decision") in {"FAIL", "ERROR"}:
            validation_status = str(artifact["decision"])
        else:
            validation_status = "INCOMPLETE"

    structural_failures = [item for item in obligations if item["status"] == "FAIL"]
    reference_failures = [item for item in references if item["status"] == "FAIL"]
    external_references = [
        item for item in references if item["status"] == "NOT_EVALUATED"
    ]
    if (
        structural_failures
        or reference_failures
        or any(item["status"] != "PASS" for item in xsd_results)
        or validation_status in {"FAIL", "ERROR"}
    ):
        decision = "FAIL" if validation_status != "ERROR" else "ERROR"
    elif external_references or validation_status != "PASS":
        decision = "INCOMPLETE"
    else:
        decision = "PASS"
    result = {
        "schema_version": "atlas.asw_v3.independent_evaluation.v1",
        "case_id": case_id,
        "cohort": cohort,
        "tier": case["tier"],
        "decision": decision,
        "promotable": decision == "PASS",
        "requirement_source_sha256": source_sha256,
        "requirement_source_canonical_sha256": source_canonical_sha256,
        "case_sha256": case_sha256,
        "evaluator_sha256": sha256_file(Path(__file__)),
        "xsd_path": str(XSD),
        "xsd_sha256": sha256_file(XSD),
        "xsd": xsd_results,
        "structural_obligations": obligations,
        "structural_failure_count": len(structural_failures),
        "reference_integrity": references,
        "local_reference_failure_count": len(reference_failures),
        "external_reference_not_evaluated_count": len(external_references),
        "validation_status": validation_status,
        "validation_file": str(validation_path.resolve()) if validation_path else None,
        "validation_sha256": sha256_file(validation_path) if validation_path else None,
        "full_corpus_decision": (validation or {}).get("decision"),
        "artifact_profile": (validation or {}).get("artifact_profile"),
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--cohort", choices=("primary", "heldout"), default="primary")
    parser.add_argument("--component", type=Path, required=True)
    parser.add_argument("--interface", type=Path, action="append", default=[])
    parser.add_argument("--validation", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = evaluate(
        case_id=args.case_id,
        component_path=args.component,
        interface_paths=args.interface,
        validation_path=args.validation,
        cohort=args.cohort,
    )
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8", newline="\n")
    print(text, end="")
    return 0 if result["decision"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
