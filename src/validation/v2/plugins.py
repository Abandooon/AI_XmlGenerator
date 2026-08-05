"""Executable ARXML rules keyed by the validation-plan plugin name."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from lxml import etree

from .arxml_index import ArxmlIndex, local_name, normalized_ref

PORT_TAGS = {"P-PORT-PROTOTYPE", "R-PORT-PROTOTYPE", "PR-PORT-PROTOTYPE"}
COMPONENT_TAGS = {
    "APPLICATION-SW-COMPONENT-TYPE", "ATOMIC-SW-COMPONENT-TYPE",
    "COMPLEX-DEVICE-DRIVER-SW-COMPONENT-TYPE", "COMPOSITION-SW-COMPONENT-TYPE",
    "ECU-ABSTRACTION-SW-COMPONENT-TYPE", "NV-BLOCK-SW-COMPONENT-TYPE",
    "PARAMETER-SW-COMPONENT-TYPE", "SENSOR-ACTUATOR-SW-COMPONENT-TYPE",
    "SERVICE-PROXY-SW-COMPONENT-TYPE", "SERVICE-SW-COMPONENT-TYPE",
}
CONNECTOR_TAGS = {"ASSEMBLY-SW-CONNECTOR", "DELEGATION-SW-CONNECTOR", "PASS-THROUGH-SW-CONNECTOR"}
INTERFACE_REF_TAGS = {"PROVIDED-INTERFACE-TREF", "REQUIRED-INTERFACE-TREF", "PROVIDED-REQUIRED-INTERFACE-TREF"}
ENDPOINT_REF_TAGS = {
    "TARGET-P-PORT-REF", "TARGET-R-PORT-REF", "OUTER-PORT-REF",
    "PROVIDED-OUTER-PORT-REF", "REQUIRED-OUTER-PORT-REF",
}
DATA_INTERFACE_TAGS = {"SENDER-RECEIVER-INTERFACE", "NV-DATA-INTERFACE", "PARAMETER-INTERFACE"}


@dataclass
class PluginReport:
    violations: list[dict] = field(default_factory=list)
    incomplete_reasons: list[str] = field(default_factory=list)
    observations: list[dict] = field(default_factory=list)
    checked: int = 0

    def fail(
        self,
        index: ArxmlIndex,
        element: etree._Element,
        message: str,
        *,
        repair: dict | None = None,
        **evidence: object,
    ) -> None:
        item = {"message": message, "location": index.location(element)}
        if evidence:
            item["evidence"] = evidence
        if repair:
            item["repair"] = repair
        self.violations.append(item)

    def incomplete(self, reason: str) -> None:
        if reason not in self.incomplete_reasons:
            self.incomplete_reasons.append(reason)

    def observe(self, **evidence: object) -> None:
        """Attach deterministic semantic evidence without changing rule status."""
        self.observations.append(evidence)


Plugin = Callable[[ArxmlIndex, dict, list[etree._Element]], PluginReport]
REGISTRY: dict[str, Plugin] = {}


def plugin(name: str) -> Callable[[Plugin], Plugin]:
    def decorate(function: Plugin) -> Plugin:
        REGISTRY[name] = function
        return function
    return decorate


def _resolve(index: ArxmlIndex, ref: etree._Element, report: PluginReport) -> etree._Element | None:
    resolution = index.resolve(ref)
    if resolution.status != "resolved":
        report.incomplete(f"{resolution.status} reference {resolution.reference} at {index.location(ref)}")
        return None
    return resolution.element


def _port_interface(index: ArxmlIndex, port: etree._Element, report: PluginReport) -> etree._Element | None:
    ref = index.first_descendant(port, INTERFACE_REF_TAGS)
    if ref is None:
        report.incomplete(f"missing interface reference at {index.location(port)}")
        return None
    return _resolve(index, ref, report)


def _connector_endpoint_refs(index: ArxmlIndex, connector: etree._Element) -> list[etree._Element]:
    return index.descendants(connector, ENDPOINT_REF_TAGS)


@plugin("dynamic_array_profile_domain")
def dynamic_array_profile_domain(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    allowed = set(rule.get("parameters", {}).get("allowed", []))
    for element in selected:
        value = (element.text or "").strip()
        if value not in allowed:
            report.fail(index, element, f"dynamicArraySizeProfile value {value!r} is not allowed", actual=value, allowed=sorted(allowed))
    return report


@plugin("port_forbids_postbuild_variation")
def port_forbids_postbuild_variation(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for port in selected:
        postbuild = index.first_descendant(port, {"POST-BUILD-VARIANT-CONDITIONS", "POST-BUILD-VARIANT-CONDITION"})
        if postbuild is not None:
            report.fail(index, postbuild, "PortPrototype must not declare PostBuild variant conditions")
    return report


@plugin("port_interface_reference_required")
def port_interface_reference_required(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    expected = {
        "P-PORT-PROTOTYPE": "PROVIDED-INTERFACE-TREF",
        "R-PORT-PROTOTYPE": "REQUIRED-INTERFACE-TREF",
        "PR-PORT-PROTOTYPE": "PROVIDED-REQUIRED-INTERFACE-TREF",
    }
    report = PluginReport(checked=len(selected))
    for port in selected:
        required_tag = expected[local_name(port.tag)]
        ref = index.first_descendant(port, {required_tag})
        if ref is None or not (ref.text or "").strip():
            report.fail(index, port, f"{local_name(port.tag)} requires {required_tag}")
    return report


@plugin("parameter_component_restrictions")
def parameter_component_restrictions(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for component in selected:
        internal = index.first_descendant(component, {"INTERNAL-BEHAVIORS", "SWC-INTERNAL-BEHAVIOR"})
        if internal is not None:
            report.fail(index, internal, "ParameterSwComponentType must not aggregate an internal behavior")
        for port in index.descendants(component, PORT_TAGS):
            if local_name(port.tag) != "P-PORT-PROTOTYPE":
                report.fail(index, port, "ParameterSwComponentType may own only PPortPrototype ports")
                continue
            interface = _port_interface(index, port, report)
            if interface is not None and local_name(interface.tag) != "PARAMETER-INTERFACE":
                report.fail(index, port, "P port owned by ParameterSwComponentType must be typed by ParameterInterface", actual_interface=local_name(interface.tag))
    return report


@plugin("component_prototype_type_reference")
def component_prototype_type_reference(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for prototype in selected:
        ref = index.first_descendant(prototype, {"TYPE-TREF"})
        if ref is None or not (ref.text or "").strip():
            report.fail(index, prototype, "SwComponentPrototype requires TYPE-TREF")
            continue
        target = _resolve(index, ref, report)
        if target is not None and local_name(target.tag) not in COMPONENT_TAGS:
            report.fail(index, ref, "TYPE-TREF does not resolve to a SwComponentType", actual_target=local_name(target.tag))
    return report


def _cycle_path(graph: dict[etree._Element, set[etree._Element]]) -> list[etree._Element] | None:
    state: dict[etree._Element, int] = {}
    stack: list[etree._Element] = []
    positions: dict[etree._Element, int] = {}
    def visit(node: etree._Element) -> list[etree._Element] | None:
        state[node] = 1
        positions[node] = len(stack)
        stack.append(node)
        for target in graph.get(node, set()):
            if state.get(target, 0) == 0:
                found = visit(target)
                if found:
                    return found
            elif state.get(target) == 1:
                return stack[positions[target]:] + [target]
        stack.pop()
        positions.pop(node, None)
        state[node] = 2
        return None
    for node in graph:
        if state.get(node, 0) == 0:
            found = visit(node)
            if found:
                return found
    return None


@plugin("composition_type_acyclic")
def composition_type_acyclic(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    graph: dict[etree._Element, set[etree._Element]] = {item: set() for item in selected}
    selected_set = set(selected)
    for composition in selected:
        for prototype in index.descendants(composition, {"SW-COMPONENT-PROTOTYPE"}):
            ref = index.first_descendant(prototype, {"TYPE-TREF"})
            if ref is None:
                report.incomplete(f"prototype lacks TYPE-TREF at {index.location(prototype)}")
                continue
            target = _resolve(index, ref, report)
            if target in selected_set:
                graph[composition].add(target)
    cycle = _cycle_path(graph)
    if cycle:
        names = [index.path_of(item) for item in cycle]
        report.fail(index, cycle[0], "Composition type-reference graph contains a cycle", cycle=names)
    return report


def _port_capabilities(tag: str) -> set[str]:
    if tag == "P-PORT-PROTOTYPE":
        return {"provide"}
    if tag == "R-PORT-PROTOTYPE":
        return {"require"}
    if tag == "PR-PORT-PROTOTYPE":
        return {"provide", "require"}
    return set()


@plugin("delegation_port_kind_compatible")
def delegation_port_kind_compatible(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for connector in selected:
        inner_refs = index.descendants(connector, {"TARGET-P-PORT-REF", "TARGET-R-PORT-REF"})
        outer_refs = index.descendants(connector, {"OUTER-PORT-REF"})
        if len(inner_refs) != 1 or len(outer_refs) != 1:
            report.incomplete(f"delegation connector endpoints are incomplete at {index.location(connector)}")
            continue
        inner = _resolve(index, inner_refs[0], report)
        outer = _resolve(index, outer_refs[0], report)
        if inner is None or outer is None:
            continue
        role = "provide" if local_name(inner_refs[0].tag) == "TARGET-P-PORT-REF" else "require"
        if role not in _port_capabilities(local_name(inner.tag)) or role not in _port_capabilities(local_name(outer.tag)):
            report.fail(index, connector, "Delegation connector endpoints do not support the same port direction", role=role, inner=local_name(inner.tag), outer=local_name(outer.tag))
    return report


@plugin("connector_endpoint_pair_unique")
def connector_endpoint_pair_unique(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    first_by_pair: dict[tuple[str, str], etree._Element] = {}
    for connector in selected:
        refs = _connector_endpoint_refs(index, connector)
        values = [normalized_ref(ref.text) for ref in refs if normalized_ref(ref.text)]
        if len(values) != 2:
            report.incomplete(f"expected two port endpoints at {index.location(connector)}, found {len(values)}")
            continue
        pair = tuple(sorted(values))
        if pair in first_by_pair:
            report.fail(index, connector, "A pair of PortPrototypes is connected by more than one SwConnector", endpoints=list(pair), first_connector=index.location(first_by_pair[pair]))
        else:
            first_by_pair[pair] = connector
    return report


def _same_owner(index: ArxmlIndex, connector: etree._Element, refs: list[etree._Element], report: PluginReport, label: str) -> None:
    owner = index.nearest(connector, {"COMPOSITION-SW-COMPONENT-TYPE"})
    if owner is None:
        report.incomplete(f"{label} has no owning composition at {index.location(connector)}")
        return
    for ref in refs:
        target = _resolve(index, ref, report)
        if target is None:
            continue
        target_owner = index.nearest(target, {"COMPOSITION-SW-COMPONENT-TYPE"})
        if target_owner is not owner:
            report.fail(index, ref, f"{label} endpoint is not owned by the connector's composition", target=index.path_of(target), owner=index.path_of(owner))


@plugin("assembly_endpoints_same_composition")
def assembly_endpoints_same_composition(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for connector in selected:
        refs = index.descendants(connector, {"CONTEXT-COMPONENT-REF"})
        if len(refs) != 2:
            report.incomplete(f"assembly connector requires two context components at {index.location(connector)}")
        _same_owner(index, connector, refs, report, "AssemblySwConnector")
    return report


@plugin("delegation_endpoints_same_composition")
def delegation_endpoints_same_composition(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for connector in selected:
        refs = index.descendants(connector, {"CONTEXT-COMPONENT-REF", "OUTER-PORT-REF"})
        if len(refs) < 2:
            report.incomplete(f"delegation connector endpoints are incomplete at {index.location(connector)}")
        _same_owner(index, connector, refs, report, "DelegationSwConnector")
    return report


@plugin("inner_pr_port_uses_p_iref")
def inner_pr_port_uses_p_iref(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for connector in selected:
        refs = index.descendants(connector, {"TARGET-P-PORT-REF", "TARGET-R-PORT-REF"})
        for ref in refs:
            target = _resolve(index, ref, report)
            if target is not None and local_name(target.tag) == "PR-PORT-PROTOTYPE" and local_name(ref.tag) != "TARGET-P-PORT-REF":
                report.fail(index, ref, "An inner PRPortPrototype must be represented by PPortInCompositionInstanceRef/TARGET-P-PORT-REF")
    return report


@plugin("refined_event_is_timing_event")
def refined_event_is_timing_event(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for props in selected:
        refs = index.descendants(props, {"TARGET-EVENT-REF"})
        if len(refs) != 1:
            report.incomplete(f"expected one TARGET-EVENT-REF at {index.location(props)}")
            continue
        target = _resolve(index, refs[0], report)
        if target is not None and local_name(target.tag) != "TIMING-EVENT":
            report.fail(index, refs[0], "InstantiationTimingEventProps.refinedEvent must resolve to TimingEvent", actual_target=local_name(target.tag))
    return report


@plugin("connected_port_interface_kinds")
def connected_port_interface_kinds(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for connector in selected:
        port_refs = _connector_endpoint_refs(index, connector)
        if len(port_refs) != 2:
            report.incomplete(f"connector endpoint set is incomplete at {index.location(connector)}")
            continue
        ports = [_resolve(index, ref, report) for ref in port_refs]
        if any(port is None for port in ports):
            continue
        interfaces = [_port_interface(index, port, report) for port in ports if port is not None]
        if len(interfaces) != 2 or any(item is None for item in interfaces):
            continue
        kinds = [local_name(item.tag) for item in interfaces if item is not None]
        compatible = kinds[0] == kinds[1] or all(kind in DATA_INTERFACE_TAGS for kind in kinds)
        if not compatible:
            report.fail(index, connector, "Connected ports use incompatible PortInterface kinds", interface_kinds=kinds)
    return report


@plugin("parameter_interface_p_port_owner")
def parameter_interface_p_port_owner(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for port in selected:
        interface = _port_interface(index, port, report)
        if interface is None or local_name(interface.tag) != "PARAMETER-INTERFACE":
            continue
        owner = index.nearest(port, COMPONENT_TAGS)
        if owner is None:
            report.incomplete(f"P port has no owning SwComponentType at {index.location(port)}")
        elif local_name(owner.tag) != "PARAMETER-SW-COMPONENT-TYPE":
            report.fail(index, port, "P port typed by ParameterInterface must be owned by ParameterSwComponentType", actual_owner=local_name(owner.tag))
    return report


@plugin("composition_port_forbids_service_interface")
def composition_port_forbids_service_interface(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for composition in selected:
        for port in index.descendants(composition, PORT_TAGS):
            interface = _port_interface(index, port, report)
            if interface is None:
                continue
            value = index.first_descendant(interface, {"IS-SERVICE"})
            if value is not None and (value.text or "").strip().lower() in {"true", "1"}:
                report.fail(index, port, "CompositionSwComponentType must not own a port typed by an AUTOSAR service interface", interface=index.path_of(interface))
    return report
