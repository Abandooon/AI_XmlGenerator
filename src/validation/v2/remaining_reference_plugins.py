"""Reviewed cross-object reference and coverage validators."""

from __future__ import annotations

from collections import defaultdict

from lxml import etree

from .arxml_index import ArxmlIndex, local_name
from .plugins import COMPONENT_TAGS, CONNECTOR_TAGS, INTERFACE_REF_TAGS, PluginReport, plugin

ATOMIC_COMPONENT_TAGS = COMPONENT_TAGS - {"COMPOSITION-SW-COMPONENT-TYPE"}
DATA_PROTOTYPE_TAGS = {
    "VARIABLE-DATA-PROTOTYPE", "PARAMETER-DATA-PROTOTYPE", "ARGUMENT-DATA-PROTOTYPE",
    "APPLICATION-ARRAY-ELEMENT", "APPLICATION-RECORD-ELEMENT", "IMPLEMENTATION-DATA-TYPE-ELEMENT",
}


def _text(element: etree._Element | None) -> str:
    return (element.text or "").strip() if element is not None else ""


def _first(element: etree._Element, tags: set[str]) -> etree._Element | None:
    return next((item for item in element.iterdescendants() if local_name(item.tag) in tags), None)


def _direct(element: etree._Element, tag: str) -> etree._Element | None:
    return next((item for item in element if local_name(item.tag) == tag), None)


def _resolve(
    index: ArxmlIndex,
    reference: etree._Element | None,
    report: PluginReport,
    label: str,
) -> etree._Element | None:
    if reference is None:
        report.incomplete(f"missing {label}")
        return None
    resolution = index.resolve(reference)
    if resolution.status != "resolved" or resolution.element is None:
        report.incomplete(
            f"{resolution.status} {label} {resolution.reference} at {index.location(reference)}"
        )
        return None
    return resolution.element


def _repair(action: str, target: str, instruction: str, **values: object) -> dict:
    return {"action": action, "target": target, "instruction": instruction, **values}


def _short_name(element: etree._Element) -> str:
    return _text(_direct(element, "SHORT-NAME"))


def _owned(
    index: ArxmlIndex,
    owner: etree._Element,
    tag: str,
    owner_tags: set[str],
) -> list[etree._Element]:
    result: list[etree._Element] = []
    for item in index.descendants(owner, {tag}):
        current = index.parent.get(item)
        nearest = None
        while current is not None:
            if local_name(current.tag) in owner_tags:
                nearest = current
                break
            current = index.parent.get(current)
        if nearest is owner:
            result.append(item)
    return result


def _type_of(index: ArxmlIndex, prototype: etree._Element, report: PluginReport) -> etree._Element | None:
    return _resolve(index, _first(prototype, {"TYPE-TREF"}), report, f"{local_name(prototype.tag)} type")


def _port_interface(index: ArxmlIndex, port: etree._Element, report: PluginReport) -> etree._Element | None:
    return _resolve(index, _first(port, INTERFACE_REF_TAGS), report, "PortPrototype interface")


def _implementation_is_mode_eligible(
    index: ArxmlIndex, data_type: etree._Element, report: PluginReport
) -> bool | None:
    seen: set[int] = set()
    current = data_type
    while _text(_direct(current, "CATEGORY")) == "TYPE_REFERENCE":
        if id(current) in seen:
            report.incomplete(f"TYPE_REFERENCE cycle at {index.path_of(current)}")
            return None
        seen.add(id(current))
        current = _resolve(
            index, _first(current, {"IMPLEMENTATION-DATA-TYPE-REF"}), report,
            "TYPE_REFERENCE implementationDataType",
        )
        if current is None:
            return None
    category = _text(_direct(current, "CATEGORY"))
    base = _resolve(index, _first(current, {"BASE-TYPE-REF"}), report, "mode request SwBaseType")
    if base is None:
        return None
    return category == "VALUE" and _text(_first(base, {"BASE-TYPE-ENCODING"})) == "NONE"


@plugin("mode_request_map_required")
def mode_request_map_required(
    index: ArxmlIndex, rule: dict, selected: list[etree._Element]
) -> PluginReport:
    """constr_1166: every application mode port has an eligible local ModeRequestTypeMap."""
    report = PluginReport(checked=len(selected))
    for component in [item for item in selected if local_name(item.tag) == "APPLICATION-SW-COMPONENT-TYPE"]:
        mapping_sets: list[etree._Element] = []
        behaviors = _owned(index, component, "SWC-INTERNAL-BEHAVIOR", COMPONENT_TAGS)
        if not behaviors:
            report.incomplete(f"ApplicationSwComponentType has no SwcInternalBehavior at {index.path_of(component)}")
        for behavior in behaviors:
            for ref in index.descendants(behavior, {"DATA-TYPE-MAPPING-REF"}):
                target = _resolve(index, ref, report, "SwcInternalBehavior DataTypeMappingSet")
                if target is not None and local_name(target.tag) == "DATA-TYPE-MAPPING-SET":
                    mapping_sets.append(target)
        port_groups: list[tuple[etree._Element, etree._Element]] = []
        for port in _owned(index, component, "P-PORT-PROTOTYPE", COMPONENT_TAGS) + _owned(index, component, "R-PORT-PROTOTYPE", COMPONENT_TAGS) + _owned(index, component, "PR-PORT-PROTOTYPE", COMPONENT_TAGS):
            interface = _port_interface(index, port, report)
            if interface is None or local_name(interface.tag) != "MODE-SWITCH-INTERFACE":
                continue
            prototype = _first(interface, {"MODE-GROUP"})
            group = _resolve(index, _first(prototype, {"TYPE-TREF", "MODE-DECLARATION-GROUP-REF"}) if prototype is not None else None, report, "ModeDeclarationGroupPrototype type")
            if group is not None:
                port_groups.append((port, group))
        for port, group in port_groups:
            candidates: list[tuple[etree._Element, etree._Element]] = []
            for mapping_set in mapping_sets:
                for mapping in index.descendants(mapping_set, {"MODE-REQUEST-TYPE-MAP"}):
                    mapped_group = _resolve(index, _first(mapping, {"MODE-GROUP-REF"}), report, "ModeRequestTypeMap modeGroup")
                    if mapped_group is not group:
                        continue
                    impl = _resolve(index, _first(mapping, {"IMPLEMENTATION-DATA-TYPE-REF"}), report, "ModeRequestTypeMap type")
                    if impl is not None:
                        candidates.append((mapping, impl))
            eligible = [pair for pair in candidates if _implementation_is_mode_eligible(index, pair[1], report) is True]
            if not eligible:
                report.fail(
                    index, port,
                    "Mode port has no eligible ModeRequestTypeMap in its owning internal behavior",
                    mode_group=index.path_of(group),
                    repair=_repair(
                        "add_mapping", "MODE-REQUEST-TYPE-MAP",
                        "Reference the ModeDeclarationGroup and an integral VALUE ImplementationDataType from a DataTypeMappingSet used by this component's SwcInternalBehavior.",
                    ),
                )
    return report


@plugin("mode_declaration_mapping_complete")
def mode_declaration_mapping_complete(
    index: ArxmlIndex, rule: dict, selected: list[etree._Element]
) -> PluginReport:
    """constr_1210: once a manager group is mapped, all of its modes are mapped."""
    report = PluginReport(checked=len(selected))
    mapping_sets = {index.nearest(item, {"MODE-DECLARATION-MAPPING-SET"}) for item in selected}
    for mapping_set in [item for item in mapping_sets if item is not None]:
        mapped_by_group: dict[int, tuple[etree._Element, set[int]]] = {}
        for mapping in index.descendants(mapping_set, {"MODE-DECLARATION-MAPPING"}):
            second = _resolve(index, _first(mapping, {"SECOND-MODE-REF"}), report, "mode-user ModeDeclaration")
            if second is None:
                continue
            for ref in index.descendants(mapping, {"FIRST-MODE-REF"}):
                manager_mode = _resolve(index, ref, report, "mode-manager ModeDeclaration")
                if manager_mode is None:
                    continue
                group = index.nearest(manager_mode, {"MODE-DECLARATION-GROUP"})
                if group is None:
                    report.incomplete(f"manager mode has no ModeDeclarationGroup owner at {index.location(manager_mode)}")
                    continue
                entry = mapped_by_group.setdefault(id(group), (group, set()))
                entry[1].add(id(manager_mode))
        for group, mapped in mapped_by_group.values():
            modes = _owned(index, group, "MODE-DECLARATION", {"MODE-DECLARATION-GROUP"})
            missing = [mode for mode in modes if id(mode) not in mapped]
            for mode in missing:
                report.fail(
                    index, mapping_set,
                    "ModeDeclarationMappingSet does not map every mode of the mode manager",
                    manager_group=index.path_of(group), missing_mode=index.path_of(mode),
                    repair=_repair(
                        "add_mapping", "MODE-DECLARATION-MAPPING",
                        "Add a mapping from the missing manager mode to an applicable mode-user mode.",
                    ),
                )
    return report


@plugin("operation_argument_mapping_complete")
def operation_argument_mapping_complete(
    index: ArxmlIndex, rule: dict, selected: list[etree._Element]
) -> PluginReport:
    """constr_1240: every argument of both mapped operations is represented."""
    report = PluginReport(checked=len(selected))
    for mapping in [item for item in selected if local_name(item.tag) == "CLIENT-SERVER-OPERATION-MAPPING"]:
        first_op = _resolve(index, _first(mapping, {"FIRST-OPERATION-REF"}), report, "first operation")
        second_op = _resolve(index, _first(mapping, {"SECOND-OPERATION-REF"}), report, "second operation")
        if first_op is None or second_op is None:
            continue
        mapped_first: set[int] = set()
        mapped_second: set[int] = set()
        for argument_mapping in index.descendants(mapping, {"DATA-PROTOTYPE-MAPPING"}):
            first = _resolve(index, _first(argument_mapping, {"FIRST-DATA-PROTOTYPE-REF"}), report, "first argument mapping reference")
            second = _resolve(index, _first(argument_mapping, {"SECOND-DATA-PROTOTYPE-REF"}), report, "second argument mapping reference")
            if first is not None:
                mapped_first.add(id(first))
            if second is not None:
                mapped_second.add(id(second))
        for operation, mapped, side in ((first_op, mapped_first, "first"), (second_op, mapped_second, "second")):
            arguments = _owned(index, operation, "ARGUMENT-DATA-PROTOTYPE", {"CLIENT-SERVER-OPERATION"})
            for argument in arguments:
                if id(argument) not in mapped:
                    report.fail(
                        index, mapping,
                        f"{side} operation argument is absent from argumentMappings",
                        operation=index.path_of(operation), argument=index.path_of(argument),
                        repair=_repair(
                            "add_mapping", "DATA-PROTOTYPE-MAPPING",
                            f"Add a {side}DataPrototype reference for the missing operation argument.",
                        ),
                    )
    return report


def _type_children(index: ArxmlIndex, data_type: etree._Element) -> list[etree._Element]:
    tag = local_name(data_type.tag)
    if tag == "APPLICATION-ARRAY-DATA-TYPE":
        return _owned(index, data_type, "APPLICATION-ARRAY-ELEMENT", {"APPLICATION-ARRAY-DATA-TYPE"})
    if tag == "APPLICATION-RECORD-DATA-TYPE":
        return _owned(index, data_type, "APPLICATION-RECORD-ELEMENT", {"APPLICATION-RECORD-DATA-TYPE"})
    if tag == "IMPLEMENTATION-DATA-TYPE" and _text(_direct(data_type, "CATEGORY")) in {"STRUCTURE", "ARRAY"}:
        return _owned(index, data_type, "IMPLEMENTATION-DATA-TYPE-ELEMENT", {"IMPLEMENTATION-DATA-TYPE", "IMPLEMENTATION-DATA-TYPE-ELEMENT"})
    return []


def _prototype_nodes(
    index: ArxmlIndex, prototype: etree._Element, report: PluginReport
) -> tuple[set[int], set[int]] | None:
    """Return all reachable composite nodes and leaves, including the root prototype."""
    root_type = _type_of(index, prototype, report)
    if root_type is None:
        return None
    nodes = {id(prototype)}
    leaves: set[int] = set()
    seen_types: set[int] = set()
    stack: list[etree._Element] = [root_type]
    while stack:
        data_type = stack.pop()
        if id(data_type) in seen_types:
            continue
        seen_types.add(id(data_type))
        children = _type_children(index, data_type)
        if not children:
            continue
        for child in children:
            nodes.add(id(child))
            child_type = _type_of(index, child, report)
            if child_type is None:
                return None
            nested = _type_children(index, child_type)
            if nested:
                stack.append(child_type)
            else:
                leaves.add(id(child))
    if not leaves:
        leaves.add(id(prototype))
    return nodes, leaves


def _reference_target(
    index: ArxmlIndex, wrapper: etree._Element, report: PluginReport
) -> tuple[etree._Element | None, etree._Element | None, etree._Element | None]:
    port = _resolve(index, _first(wrapper, {"PORT-PROTOTYPE-REF"}), report, "AutosarVariableRef port") if _first(wrapper, {"PORT-PROTOTYPE-REF"}) is not None else None
    target_ref = _first(wrapper, {"TARGET-DATA-PROTOTYPE-REF", "TARGET-IMPLEMENTATION-DATA-TYPE-ELEMENT-REF"})
    target = _resolve(index, target_ref, report, "AutosarVariableRef target")
    root_ref = _first(wrapper, {"ROOT-VARIABLE-DATA-PROTOTYPE-REF", "ROOT-DATA-PROTOTYPE-REF"})
    root = _resolve(index, root_ref, report, "AutosarVariableRef root") if root_ref is not None else None
    if root is None and target is not None and local_name(target.tag) == "VARIABLE-DATA-PROTOTYPE":
        root = target
    return port, root, target


@plugin("nv_data_mapping_complete")
def nv_data_mapping_complete(
    index: ArxmlIndex, rule: dict, selected: list[etree._Element]
) -> PluginReport:
    """TPS_SWCT_01659/constr_1395: direct, complete-leaf, or complete-subtree NvData mapping."""
    report = PluginReport(checked=len(selected))
    coverage: dict[tuple[int, int], tuple[etree._Element | None, etree._Element, set[int], list[etree._Element]]] = {}
    for mapping in index.elements("NV-BLOCK-DATA-MAPPING"):
        for role in {"READ-NV-DATA", "WRITTEN-NV-DATA", "WRITTEN-READ-NV-DATA"}:
            wrapper = _direct(mapping, role)
            if wrapper is None:
                continue
            port, root, target = _reference_target(index, wrapper, report)
            if target is None or root is None:
                report.incomplete(f"{role} does not establish a root and target at {index.location(wrapper)}")
                continue
            shape = _prototype_nodes(index, root, report)
            if shape is None:
                continue
            nodes, _ = shape
            if id(target) not in nodes:
                report.fail(
                    index, wrapper,
                    "NvBlockDataMapping target is outside the referenced nvData tree",
                    root=index.path_of(root), target=index.path_of(target),
                    repair=_repair("repair_reference", "TARGET-DATA-PROTOTYPE-REF", "Reference the nvData root or one of its reachable sub-elements."),
                )
                continue
            key = (id(port) if port is not None else 0, id(root))
            entry = coverage.setdefault(key, (port, root, set(), []))
            entry[2].add(id(target))
            entry[3].append(mapping)
    for port, root, covered, mappings in coverage.values():
        shape = _prototype_nodes(index, root, report)
        if shape is None:
            continue
        nodes, leaves = shape
        if id(root) in covered:
            continue
        effective: set[int] = set(covered)
        for marker in list(covered):
            element = next((item for item in index.file_by_element if id(item) == marker), None)
            if element is None:
                continue
            target_type = _type_of(index, element, report)
            if target_type is None:
                continue
            descendants = _type_children(index, target_type)
            if descendants:
                stack = list(descendants)
                while stack:
                    child = stack.pop()
                    effective.add(id(child))
                    child_type = _type_of(index, child, report)
                    if child_type is not None:
                        stack.extend(_type_children(index, child_type))
        missing = leaves - effective
        for marker in missing:
            leaf = next((item for item in index.file_by_element if id(item) == marker), root)
            report.fail(
                index, mappings[0],
                "NvBlockDataMapping leaves part of nvData unmapped",
                port=index.path_of(port) if port is not None else None,
                nv_data=index.path_of(root), missing_leaf=index.path_of(leaf),
                repair=_repair(
                    "add_mapping", "NV-BLOCK-DATA-MAPPING",
                    "Map the missing leaf, an enclosing subtree, or the complete nvData root.",
                ),
            )
    return report


def _mapped_nodes_for_prototype(
    index: ArxmlIndex, prototype: etree._Element, report: PluginReport
) -> tuple[set[int], bool]:
    mapped: set[int] = set()
    whole = False
    for mapping in index.elements("DATA-PROTOTYPE-MAPPING"):
        refs = index.descendants(mapping, {"FIRST-DATA-PROTOTYPE-REF", "SECOND-DATA-PROTOTYPE-REF"})
        roots = [_resolve(index, ref, report, "DataPrototypeMapping prototype") for ref in refs]
        if all(root is not prototype for root in roots):
            continue
        submappings = index.descendants(mapping, {"SUB-ELEMENT-MAPPING"})
        if not submappings:
            whole = True
            continue
        for submapping in submappings:
            for ref in submapping.iterdescendants():
                if not local_name(ref.tag).endswith("-REF") or not _text(ref):
                    continue
                target = _resolve(index, ref, report, "SubElementMapping element")
                if target is not None and local_name(target.tag) in DATA_PROTOTYPE_TAGS:
                    mapped.add(id(target))
    return mapped, whole


@plugin("receiver_composite_mapping_policy")
def receiver_composite_mapping_policy(
    index: ArxmlIndex, rule: dict, selected: list[etree._Element]
) -> PluginReport:
    """constr_1279/1280: unmapped receiver leaves require allowed policy/init value."""
    report = PluginReport(checked=len(selected))
    for comspec in index.elements("NONQUEUED-RECEIVER-COM-SPEC") + index.elements("QUEUED-RECEIVER-COM-SPEC"):
        port = index.nearest(comspec, {"R-PORT-PROTOTYPE", "PR-PORT-PROTOTYPE"})
        if port is None:
            continue
        prototype = _resolve(index, _first(comspec, {"DATA-ELEMENT-REF"}), report, "ReceiverComSpec dataElement")
        if prototype is None:
            continue
        shape = _prototype_nodes(index, prototype, report)
        if shape is None:
            continue
        _, leaves = shape
        if leaves == {id(prototype)}:
            continue
        mapped, whole = _mapped_nodes_for_prototype(index, prototype, report)
        unmapped = set() if whole else leaves - mapped
        if not unmapped:
            continue
        if rule["constraint_id"] == "constr_1280":
            if _first(comspec, {"INIT-VALUE"}) is None:
                report.fail(
                    index, comspec,
                    "Receiver ComSpec with unmapped composite leaves lacks initValue",
                    missing_leaf_count=len(unmapped),
                    repair=_repair("add_element", "INIT-VALUE", "Add an initValue covering the unmapped receiver-side elements."),
                )
        else:
            policy = _text(_first(prototype, {"SW-IMPL-POLICY"})).upper()
            if policy == "QUEUED":
                report.fail(
                    index, comspec,
                    "QUEUED receiver data prototype has unmapped composite elements",
                    missing_leaf_count=len(unmapped),
                    repair=_repair("add_mapping", "SUB-ELEMENT-MAPPING", "Map every receiver-side leaf or use a supported non-queued policy."),
                )
    return report


def _component_ecus(index: ArxmlIndex, report: PluginReport) -> dict[int, set[int]]:
    result: dict[int, set[int]] = defaultdict(set)
    for mapping in index.elements("SWC-TO-ECU-MAPPING"):
        ecu = _resolve(index, _first(mapping, {"ECU-INSTANCE-REF"}), report, "SwcToEcuMapping ECU")
        if ecu is None:
            continue
        for iref in index.descendants(mapping, {"COMPONENT-IREF"}):
            targets = index.descendants(iref, {"TARGET-COMPONENT-REF", "CONTEXT-COMPONENT-REF"})
            if not targets:
                report.incomplete(f"ComponentIref has no component reference at {index.location(iref)}")
                continue
            prototype = _resolve(index, targets[-1], report, "SwcToEcuMapping component")
            if prototype is not None:
                result[id(prototype)].add(id(ecu))
    return result


def _connector_component_prototypes(
    index: ArxmlIndex, connector: etree._Element, report: PluginReport
) -> list[etree._Element]:
    result: list[etree._Element] = []
    for ref in connector.iterdescendants():
        if local_name(ref.tag) not in {"CONTEXT-COMPONENT-REF", "TARGET-COMPONENT-REF"}:
            continue
        target = _resolve(index, ref, report, "connector component context")
        if target is not None and local_name(target.tag) == "SW-COMPONENT-PROTOTYPE" and all(target is not item for item in result):
            result.append(target)
    return result


@plugin("application_service_same_ecu")
def application_service_same_ecu(
    index: ArxmlIndex, rule: dict, selected: list[etree._Element]
) -> PluginReport:
    """TPS_SWCT_01413: application-to-service communication is ECU-local."""
    report = PluginReport(checked=len(selected))
    ecus = _component_ecus(index, report)
    for tag in CONNECTOR_TAGS:
        for connector in index.elements(tag):
            prototypes = _connector_component_prototypes(index, connector, report)
            typed: list[tuple[etree._Element, etree._Element]] = []
            for prototype in prototypes:
                component_type = _type_of(index, prototype, report)
                if component_type is not None:
                    typed.append((prototype, component_type))
            applications = [pair for pair in typed if local_name(pair[1].tag) == "APPLICATION-SW-COMPONENT-TYPE"]
            services = [pair for pair in typed if local_name(pair[1].tag) == "SERVICE-SW-COMPONENT-TYPE"]
            for app, _ in applications:
                for service, _ in services:
                    app_ecus = ecus.get(id(app), set())
                    service_ecus = ecus.get(id(service), set())
                    if not app_ecus or not service_ecus:
                        report.incomplete(
                            f"ECU deployment is missing for application/service connector {index.path_of(connector)}"
                        )
                    elif app_ecus.isdisjoint(service_ecus):
                        report.fail(
                            index, connector,
                            "ApplicationSwComponent and ServiceSwComponent communicate across different ECUs",
                            application=index.path_of(app), service=index.path_of(service),
                            repair=_repair("repair_mapping", "SWC-TO-ECU-MAPPING", "Deploy both communicating instances on the same ECU."),
                        )
    return report


@plugin("service_proxy_network_receive_only")
def service_proxy_network_receive_only(
    index: ArxmlIndex, rule: dict, selected: list[etree._Element]
) -> PluginReport:
    """TPS_SWCT_01416: signal mappings for service-proxy instances use receive-capable ports only."""
    report = PluginReport(checked=len(selected))
    mapping_tags = {
        "SENDER-RECEIVER-TO-SIGNAL-MAPPING",
        "SENDER-RECEIVER-TO-SIGNAL-GROUP-MAPPING",
        "SENDER-RECEIVER-COMPOSITE-ELEMENT-TO-SIGNAL-MAPPING",
    }
    for tag in mapping_tags:
        for mapping in index.elements(tag):
            iref = _first(mapping, {"DATA-ELEMENT-IREF"})
            if iref is None:
                continue
            context_refs = index.descendants(iref, {"CONTEXT-COMPONENT-REF", "TARGET-COMPONENT-REF"})
            if not context_refs:
                report.incomplete(f"network dataElement iref has no component context at {index.location(iref)}")
                continue
            prototype = _resolve(index, context_refs[-1], report, "network-mapped component")
            if prototype is None:
                continue
            component_type = _type_of(index, prototype, report)
            if component_type is None or local_name(component_type.tag) != "SERVICE-PROXY-SW-COMPONENT-TYPE":
                continue
            port = _resolve(index, _first(iref, {"PORT-PROTOTYPE-REF"}), report, "network dataElement port")
            if port is not None and local_name(port.tag) != "R-PORT-PROTOTYPE":
                report.fail(
                    index, mapping,
                    "ServiceProxySwComponentType sends a signal over the network",
                    port=index.path_of(port), port_kind=local_name(port.tag),
                    repair=_repair("repair_reference", "PORT-PROTOTYPE-REF", "Use an RPortPrototype for service-proxy network reception; do not map a provided port to a network signal."),
                )
    return report


@plugin("sensor_actuator_mapping_matches_hardware")
def sensor_actuator_mapping_matches_hardware(
    index: ArxmlIndex, rule: dict, selected: list[etree._Element]
) -> PluginReport:
    """constr_1109: exact IO-HAL prototype maps to the ECU/hardware matching its type."""
    report = PluginReport(checked=len(selected))
    for prototype in selected:
        component_type = _type_of(index, prototype, report)
        if component_type is None or local_name(component_type.tag) != "SENSOR-ACTUATOR-SW-COMPONENT-TYPE":
            report.fail(
                index, prototype,
                "Declared IO-HAL target is not typed by SensorActuatorSwComponentType",
                repair=_repair("repair_reference", "TYPE-TREF", "Reference a SensorActuatorSwComponentType."),
            )
            continue
        expected_hw = _resolve(index, _first(component_type, {"SENSOR-ACTUATOR-REF"}), report, "sensorActuator hardware")
        if expected_hw is None:
            continue
        mappings: list[tuple[etree._Element, etree._Element | None]] = []
        for mapping in index.elements("SWC-TO-ECU-MAPPING"):
            targets: list[etree._Element] = []
            for iref in index.descendants(mapping, {"COMPONENT-IREF"}):
                refs = index.descendants(iref, {"TARGET-COMPONENT-REF", "CONTEXT-COMPONENT-REF"})
                if refs:
                    target = _resolve(index, refs[-1], report, "SwcToEcuMapping component")
                    if target is not None:
                        targets.append(target)
            if any(target is prototype for target in targets):
                controlled = _resolve(index, _first(mapping, {"CONTROLLED-HW-ELEMENT-REF"}), report, "controlledHwElement")
                mappings.append((mapping, controlled))
        if len(mappings) != 1:
            report.fail(
                index, prototype,
                "Sensor/actuator prototype must have exactly one applicable SwcToEcuMapping",
                actual=len(mappings),
                repair=_repair("add_or_remove_mapping", "SWC-TO-ECU-MAPPING", "Create exactly one mapping for the declared IO-HAL prototype."),
            )
            continue
        mapping, controlled = mappings[0]
        if controlled is None:
            continue
        expected_type_ref = _first(expected_hw, {"HW-TYPE-REF"})
        actual_type_ref = _first(controlled, {"HW-TYPE-REF"})
        expected_type = _resolve(index, expected_type_ref, report, "sensor hardware type") if expected_type_ref is not None else expected_hw
        actual_type = _resolve(index, actual_type_ref, report, "controlled hardware type") if actual_type_ref is not None else controlled
        if actual_type is not expected_type:
            report.fail(
                index, mapping,
                "SwcToEcuMapping controlled hardware does not correspond to the SensorActuatorSwComponentType hardware",
                expected=index.path_of(expected_hw), actual=index.path_of(controlled),
                repair=_repair("repair_reference", "CONTROLLED-HW-ELEMENT-REF", "Reference a HwElement with the corresponding HwType on the mapped ECU."),
            )
    return report


def _allowed_instance_scope(
    index: ArxmlIndex, owner: etree._Element, report: PluginReport
) -> set[int]:
    allowed = {id(owner), *(id(item) for item in owner.iterdescendants())}
    if local_name(owner.tag) != "COMPOSITION-SW-COMPONENT-TYPE":
        return allowed
    for prototype in _owned(index, owner, "SW-COMPONENT-PROTOTYPE", COMPONENT_TAGS):
        component_type = _type_of(index, prototype, report)
        if component_type is not None:
            allowed.add(id(component_type))
            allowed.update(id(item) for item in component_type.iterdescendants())
    return allowed


@plugin("consistency_needs_instance_scope")
def consistency_needs_instance_scope(
    index: ArxmlIndex, rule: dict, selected: list[etree._Element]
) -> PluginReport:
    """constr_1231/1232: all instance-ref context/targets stay inside the owning component context."""
    report = PluginReport(checked=len(selected))
    expected_owners = {"COMPOSITION-SW-COMPONENT-TYPE"} if rule["constraint_id"] == "constr_1231" else ATOMIC_COMPONENT_TAGS
    for needs in [item for item in selected if local_name(item.tag) == "CONSISTENCY-NEEDS"]:
        owner = index.nearest(needs, expected_owners)
        if owner is None:
            continue
        allowed = _allowed_instance_scope(index, owner, report)
        for iref in [item for item in needs.iterdescendants() if local_name(item.tag).endswith("-IREF")]:
            refs = [item for item in iref.iterdescendants() if local_name(item.tag).endswith("-REF") and _text(item)]
            if not refs:
                report.incomplete(f"instanceRef has no reference at {index.location(iref)}")
                continue
            for ref in refs:
                target = _resolve(index, ref, report, "ConsistencyNeeds instanceRef")
                if target is not None and id(target) not in allowed:
                    report.fail(
                        index, ref,
                        "ConsistencyNeeds instanceRef escapes the owning component context",
                        owner=index.path_of(owner), target=index.path_of(target),
                        repair=_repair("repair_reference", local_name(ref.tag), "Reference a context or target reachable within the owning component type."),
                    )
    return report
