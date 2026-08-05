"""Reviewed structural rules remaining after the first qualification waves.

Each validator implements the complete normative predicate for its mapped
constraint.  Reference-dependent branches report incomplete evidence rather
than treating an unresolved reference as a successful check.
"""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal, InvalidOperation

from lxml import etree

from .arxml_index import ArxmlIndex, local_name
from .plugins import (
    CONNECTOR_TAGS,
    DATA_INTERFACE_TAGS,
    INTERFACE_REF_TAGS,
    PORT_TAGS,
    PluginReport,
    plugin,
)


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


def _truth(element: etree._Element | None) -> bool:
    return _text(element).casefold() in {"true", "1"}


@plugin("application_string_contract")
def application_string_contract(
    index: ArxmlIndex, rule: dict, selected: list[etree._Element]
) -> PluginReport:
    """TPS_SWCT_01128/01488/01570: STRING APDT layout, encoding, and mapping."""
    report = PluginReport(checked=len(selected))
    cid = rule["constraint_id"]
    mapped_types: set[int] = set()
    if cid == "TPS_SWCT_01570":
        for mapping in index.elements("DATA-TYPE-MAP"):
            target = _resolve(
                index, _first(mapping, {"APPLICATION-DATA-TYPE-REF"}), report,
                "DataTypeMap applicationDataType",
            )
            if target is not None:
                mapped_types.add(id(target))
    for data_type in selected:
        if local_name(data_type.tag) != "APPLICATION-PRIMITIVE-DATA-TYPE":
            continue
        if _text(_direct(data_type, "CATEGORY")) != "STRING":
            continue
        layout_ref = _first(data_type, {"SW-RECORD-LAYOUT-REF"})
        if cid == "TPS_SWCT_01128":
            if layout_ref is None or not _text(layout_ref):
                report.fail(
                    index, data_type,
                    "STRING ApplicationPrimitiveDataType lacks SW-RECORD-LAYOUT-REF",
                    repair=_repair(
                        "add_reference", "SW-RECORD-LAYOUT-REF",
                        "Reference the SwRecordLayout that defines the compound string representation.",
                    ),
                )
        elif cid == "TPS_SWCT_01488":
            base_ref = _first(data_type, {"BASE-TYPE-REF"})
            if base_ref is None:
                report.fail(
                    index, data_type,
                    "STRING ApplicationPrimitiveDataType lacks SW-TEXT-PROPS/BASE-TYPE-REF",
                    repair=_repair(
                        "add_reference", "BASE-TYPE-REF",
                        "Add SwTextProps.baseType and reference an encoded SwBaseType.",
                    ),
                )
                continue
            base_type = _resolve(index, base_ref, report, "STRING SwBaseType")
            if base_type is not None and not _text(_first(base_type, {"BASE-TYPE-ENCODING"})):
                report.fail(
                    index, base_type,
                    "SwBaseType used for STRING has no baseTypeEncoding",
                    repair=_repair(
                        "add_element", "BASE-TYPE-ENCODING",
                        "Specify the string character encoding on the referenced SwBaseType.",
                    ),
                )
        elif layout_ref is not None and _text(layout_ref) and id(data_type) not in mapped_types:
            report.fail(
                index, layout_ref,
                "ApplicationPrimitiveDataType with swRecordLayout has no DataTypeMap",
                repair=_repair(
                    "add_mapping", "DATA-TYPE-MAP",
                    "Add a DataTypeMap from this application type to the matching ImplementationDataType.",
                    application_type=index.path_of(data_type),
                ),
            )
    return report


def _decimal_values(element: etree._Element) -> list[Decimal] | None:
    values: list[Decimal] = []
    for value in element.iterdescendants():
        if local_name(value.tag) != "V" or not _text(value):
            continue
        try:
            values.append(Decimal(_text(value)))
        except InvalidOperation:
            return None
    return values


def _provably_invertible(direction: etree._Element, category: str) -> bool | None:
    if category == "IDENTICAL":
        return True
    if category != "LINEAR":
        return None
    scales = [item for item in direction.iterdescendants() if local_name(item.tag) == "COMPU-SCALE"]
    if len(scales) != 1:
        return None
    numerator = _first(scales[0], {"COMPU-NUMERATOR"})
    denominator = _first(scales[0], {"COMPU-DENOMINATOR"})
    if numerator is None:
        return None
    nums = _decimal_values(numerator)
    dens = _decimal_values(denominator) if denominator is not None else [Decimal(1)]
    if nums is None or dens is None or len(nums) < 2 or not dens:
        return None
    return nums[1] != 0 and all(value != 0 for value in dens)


@plugin("compu_directions_determined")
def compu_directions_determined(
    index: ArxmlIndex, rule: dict, selected: list[etree._Element]
) -> PluginReport:
    """constr_1021: both directions exist or the single direction is provably invertible."""
    report = PluginReport(checked=len(selected))
    for method in selected:
        forward = _direct(method, "COMPU-INTERNAL-TO-PHYS")
        inverse = _direct(method, "COMPU-PHYS-TO-INTERNAL")
        if forward is not None and inverse is not None:
            continue
        category = _text(_direct(method, "CATEGORY"))
        existing = forward if forward is not None else inverse
        if existing is None:
            if category == "IDENTICAL":
                continue
            report.fail(
                index, method,
                "CompuMethod determines neither conversion direction",
                category=category,
                repair=_repair(
                    "add_element", "COMPU-INTERNAL-TO-PHYS/COMPU-PHYS-TO-INTERNAL",
                    "Specify both conversion directions, or use a provably invertible definition.",
                ),
            )
            continue
        invertible = _provably_invertible(existing, category)
        if invertible is True:
            continue
        if invertible is None:
            report.incomplete(
                f"automatic inversion is not provable for {category or 'unspecified'} CompuMethod "
                f"{index.path_of(method)}"
            )
        else:
            report.fail(
                index, existing,
                "The only specified CompuMethod direction is not invertible",
                category=category,
                repair=_repair(
                    "add_element",
                    "COMPU-PHYS-TO-INTERNAL" if forward is not None else "COMPU-INTERNAL-TO-PHYS",
                    "Specify the missing conversion direction explicitly.",
                ),
            )
    return report


@plugin("enable_update_not_data_read")
def enable_update_not_data_read(
    index: ArxmlIndex, rule: dict, selected: list[etree._Element]
) -> PluginReport:
    """constr_1103: enableUpdate=true target is not used by a dataReadAccess."""
    report = PluginReport(checked=len(selected))
    read_targets: dict[int, list[etree._Element]] = defaultdict(list)
    for access in index.elements("VARIABLE-ACCESS"):
        if index.nearest(access, {"DATA-READ-ACCESSS"}) is None:
            continue
        target = _resolve(index, _first(access, {"TARGET-DATA-PROTOTYPE-REF"}), report, "dataReadAccess target")
        if target is not None:
            read_targets[id(target)].append(access)
    for comspec in selected:
        if not _truth(_first(comspec, {"ENABLE-UPDATE"})):
            continue
        ref = _first(comspec, {"DATA-ELEMENT-REF"})
        target = _resolve(index, ref, report, "NonqueuedReceiverComSpec dataElement")
        if target is None:
            continue
        for access in read_targets.get(id(target), []):
            report.fail(
                index, ref if ref is not None else comspec,
                "enableUpdate=true dataElement is also used by a dataReadAccess",
                data_read_access=index.path_of(access),
                repair=_repair(
                    "replace_value", "ENABLE-UPDATE",
                    "Set enableUpdate to false or remove the conflicting dataReadAccess.",
                    expected="false",
                ),
            )
    return report


@plugin("invalid_value_category_forbidden")
def invalid_value_category_forbidden(
    index: ArxmlIndex, rule: dict, selected: list[etree._Element]
) -> PluginReport:
    """constr_1384: complex/axis/value-block application types forbid invalidValue."""
    report = PluginReport(checked=len(selected))
    forbidden = {"CURVE", "MAP", "CUBOID", "CUBE_4", "CUBE_5", "COM_AXIS", "RES_AXIS", "VAL_BLK"}
    for prototype in selected:
        type_ref = _first(prototype, {"TYPE-TREF"})
        data_type = _resolve(index, type_ref, report, "DataPrototype type")
        if data_type is None or local_name(data_type.tag) != "APPLICATION-PRIMITIVE-DATA-TYPE":
            continue
        category = _text(_direct(data_type, "CATEGORY"))
        if category not in forbidden:
            continue
        invalids = [
            item for owner in (prototype, data_type)
            for item in index.descendants(owner, {"INVALID-VALUE"})
        ]
        for invalid in dict.fromkeys(invalids):
            report.fail(
                index, invalid,
                "invalidValue is forbidden for this ApplicationPrimitiveDataType category",
                category=category, type=index.path_of(data_type),
                repair=_repair("remove", "INVALID-VALUE", "Remove the unsupported invalidValue."),
            )
    return report


def _owned_elements(index: ArxmlIndex, owner: etree._Element, tag: str, owner_tags: set[str]) -> list[etree._Element]:
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


@plugin("vsa_implementation_shape")
def vsa_implementation_shape(
    index: ArxmlIndex, rule: dict, selected: list[etree._Element]
) -> PluginReport:
    """TPS_SWCT_01650: an exact VSA type is STRUCTURE with size and payload elements."""
    report = PluginReport(checked=len(selected))
    for data_type in selected:
        elements = _owned_elements(
            index, data_type, "IMPLEMENTATION-DATA-TYPE-ELEMENT",
            {"IMPLEMENTATION-DATA-TYPE", "IMPLEMENTATION-DATA-TYPE-ELEMENT"},
        )
        category = _text(_direct(data_type, "CATEGORY"))
        if category != "STRUCTURE" or len(elements) != 2:
            report.fail(
                index, data_type,
                "VSA ImplementationDataType must be STRUCTURE with exactly two direct subElements",
                actual={"category": category, "sub_elements": len(elements)},
                expected={"category": "STRUCTURE", "sub_elements": 2},
                repair=_repair(
                    "set_structure", "IMPLEMENTATION-DATA-TYPE",
                    "Set category STRUCTURE and define the size-indicator and payload subElements.",
                ),
            )
    return report


@plugin("vsa_nonterminating_not_type_reference")
def vsa_nonterminating_not_type_reference(
    index: ArxmlIndex, rule: dict, selected: list[etree._Element]
) -> PluginReport:
    """constr_1396: a VSA aggregation-chain node may not be TYPE_REFERENCE."""
    report = PluginReport(checked=len(selected))
    for element in selected:
        owner = index.nearest(index.parent.get(element), {"IMPLEMENTATION-DATA-TYPE"})
        if owner is None or _direct(owner, "DYNAMIC-ARRAY-SIZE-PROFILE") is None:
            continue
        nested = _owned_elements(
            index, element, "IMPLEMENTATION-DATA-TYPE-ELEMENT",
            {"IMPLEMENTATION-DATA-TYPE-ELEMENT"},
        )
        if nested and _text(_direct(element, "CATEGORY")) == "TYPE_REFERENCE":
            category = _direct(element, "CATEGORY")
            report.fail(
                index, category if category is not None else element,
                "Non-terminating VSA ImplementationDataTypeElement may not use TYPE_REFERENCE",
                repair=_repair(
                    "replace_value", "CATEGORY",
                    "Use ARRAY or STRUCTURE for the non-terminating VSA aggregation node.",
                ),
            )
    return report


def _port_interface(index: ArxmlIndex, port: etree._Element, report: PluginReport) -> etree._Element | None:
    return _resolve(index, _first(port, INTERFACE_REF_TAGS), report, "PortPrototype interface")


def _connector_ports(index: ArxmlIndex, connector: etree._Element, report: PluginReport) -> list[etree._Element]:
    result: list[etree._Element] = []
    for ref in connector.iterdescendants():
        tag = local_name(ref.tag)
        if "PORT" not in tag or not tag.endswith(("-REF", "-TREF")) or not _text(ref):
            continue
        target = _resolve(index, ref, report, f"{tag} connector endpoint")
        if target is not None and local_name(target.tag) in PORT_TAGS and all(target is not item for item in result):
            result.append(target)
    return result


def _port_graph(index: ArxmlIndex, report: PluginReport) -> tuple[dict[int, etree._Element], dict[int, set[int]], dict[int, list[etree._Element]]]:
    ports = {id(item): item for tag in PORT_TAGS for item in index.elements(tag)}
    graph: dict[int, set[int]] = {marker: set() for marker in ports}
    connectors: dict[int, list[etree._Element]] = defaultdict(list)
    for tag in CONNECTOR_TAGS:
        for connector in index.elements(tag):
            endpoints = _connector_ports(index, connector, report)
            if len(endpoints) < 2:
                continue
            for left in endpoints:
                connectors[id(left)].append(connector)
                for right in endpoints:
                    if left is not right:
                        graph[id(left)].add(id(right))
    return ports, graph, connectors


def _components(graph: dict[int, set[int]]) -> list[set[int]]:
    result: list[set[int]] = []
    unseen = set(graph)
    while unseen:
        start = unseen.pop()
        group = {start}
        stack = [start]
        while stack:
            current = stack.pop()
            for neighbor in graph.get(current, set()):
                if neighbor not in group:
                    group.add(neighbor)
                    unseen.discard(neighbor)
                    stack.append(neighbor)
        result.append(group)
    return result


def _capabilities(port: etree._Element) -> set[str]:
    return {
        "P-PORT-PROTOTYPE": {"provide"},
        "R-PORT-PROTOTYPE": {"require"},
        "PR-PORT-PROTOTYPE": {"provide", "require"},
    }.get(local_name(port.tag), set())


@plugin("communication_topology_cardinality")
def communication_topology_cardinality(
    index: ArxmlIndex, rule: dict, selected: list[etree._Element]
) -> PluginReport:
    """TPS_SWCT_01581/constr_1033/1037/1101: forbidden connector fan-in/out shapes."""
    report = PluginReport(checked=len(selected))
    ports, graph, connectors = _port_graph(index, report)
    cid = rule["constraint_id"]
    interfaces: dict[int, etree._Element | None] = {}
    for marker, port in ports.items():
        interfaces[marker] = _port_interface(index, port, report)
    if cid == "constr_1101":
        for marker, port in ports.items():
            interface = interfaces[marker]
            if local_name(port.tag) != "R-PORT-PROTOTYPE" or interface is None or local_name(interface.tag) != "MODE-SWITCH-INTERFACE":
                continue
            distinct = list(dict.fromkeys(connectors.get(marker, [])))
            if len(distinct) > 1:
                report.fail(
                    index, port,
                    "ModeSwitchInterface RPortPrototype is referenced by more than one SwConnector",
                    connector_count=len(distinct),
                    repair=_repair("remove_connector", "SW-CONNECTOR", "Keep at most one connector for this mode R port."),
                )
        return report
    for group in _components(graph):
        typed = [marker for marker in group if interfaces.get(marker) is not None]
        if cid == "TPS_SWCT_01581":
            typed = [marker for marker in typed if local_name(interfaces[marker].tag) == "MODE-SWITCH-INTERFACE"]
            providers = [marker for marker in typed if "provide" in _capabilities(ports[marker])]
            requesters = [marker for marker in typed if "require" in _capabilities(ports[marker])]
            invalid = len(providers) > 1 and bool(requesters)
            message = "Mode communication topology is n:1; only 1:1 or 1:n is allowed"
        elif cid == "constr_1033":
            typed = [marker for marker in typed if local_name(interfaces[marker].tag) in DATA_INTERFACE_TAGS]
            providers = [marker for marker in typed if "provide" in _capabilities(ports[marker])]
            requesters = [marker for marker in typed if "require" in _capabilities(ports[marker])]
            invalid = len(providers) > 1 and len(requesters) > 1
            message = "Sender/receiver topology has both multiple senders and multiple receivers"
        else:
            typed = [marker for marker in typed if local_name(interfaces[marker].tag) == "CLIENT-SERVER-INTERFACE"]
            requesters = [marker for marker in typed if "require" in _capabilities(ports[marker])]
            invalid = False
            for requester in requesters:
                reachable = [
                    marker for marker in group
                    if marker != requester and marker in typed and "provide" in _capabilities(ports[marker])
                ]
                if len(reachable) > 1:
                    invalid = True
                    break
            providers = [marker for marker in typed if "provide" in _capabilities(ports[marker])]
            message = "Client port is connected to multiple server ports"
        if invalid and typed:
            report.fail(
                index, ports[typed[0]], message,
                providers=[index.path_of(ports[item]) for item in providers],
                requesters=[index.path_of(ports[item]) for item in requesters],
                repair=_repair("remove_connector", "SW-CONNECTOR", "Split the topology so the forbidden fan-in/fan-out no longer exists."),
            )
    return report


@plugin("trigger_rport_source_unique")
def trigger_rport_source_unique(
    index: ArxmlIndex, rule: dict, selected: list[etree._Element]
) -> PluginReport:
    """constr_1104: one R trigger port has at most one source per Trigger shortName."""
    report = PluginReport(checked=len(selected))
    ports, graph, _ = _port_graph(index, report)
    for r_port in selected:
        interface = _port_interface(index, r_port, report)
        if interface is None or local_name(interface.tag) != "TRIGGER-INTERFACE":
            continue
        by_name: dict[str, set[int]] = defaultdict(set)
        for neighbor in graph.get(id(r_port), set()):
            p_port = ports.get(neighbor)
            if p_port is None or "provide" not in _capabilities(p_port):
                continue
            p_interface = _port_interface(index, p_port, report)
            if p_interface is None or local_name(p_interface.tag) != "TRIGGER-INTERFACE":
                continue
            for trigger in index.descendants(p_interface, {"TRIGGER"}):
                name = _text(_direct(trigger, "SHORT-NAME"))
                if name:
                    by_name[name].add(neighbor)
        for name, providers in by_name.items():
            if len(providers) > 1:
                report.fail(
                    index, r_port,
                    "Trigger R port has multiple sources defining the same Trigger shortName",
                    trigger=name,
                    providers=[index.path_of(ports[item]) for item in providers],
                    repair=_repair("remove_connector", "SW-CONNECTOR", "Keep at most one source for this Trigger shortName."),
                )
    return report


@plugin("service_port_not_represented")
def service_port_not_represented(
    index: ArxmlIndex, rule: dict, selected: list[etree._Element]
) -> PluginReport:
    """TPS_SWCT_01173/01174: control/status assignment is outside represented PortGroup."""
    report = PluginReport(checked=len(selected))
    role = "control" if rule["constraint_id"] == "TPS_SWCT_01173" else "status"
    for dependency in selected:
        group_ref = _first(dependency, {"REPRESENTED-PORT-GROUP-REF"})
        assignments = [
            item for item in index.descendants(dependency, {"ROLE-BASED-PORT-ASSIGNMENT"})
            if _text(_first(item, {"ROLE"})).casefold() == role
        ]
        if not assignments or group_ref is None:
            continue
        group = _resolve(index, group_ref, report, "represented PortGroup")
        if group is None:
            continue
        members: set[int] = set()
        for ref in group.iterdescendants():
            tag = local_name(ref.tag)
            if "PORT" not in tag or not tag.endswith(("-REF", "-TREF")) or not _text(ref):
                continue
            target = _resolve(index, ref, report, f"PortGroup {tag}")
            if target is not None:
                members.add(id(target))
        for assignment in assignments:
            port = _resolve(index, _first(assignment, {"PORT-PROTOTYPE-REF", "ASSIGNED-PORT-REF"}), report, f"{role} assigned port")
            if port is not None and id(port) in members:
                report.fail(
                    index, assignment,
                    f"{role} port is also a member of the represented PortGroup",
                    port=index.path_of(port), group=index.path_of(group),
                    repair=_repair("remove_group_member", "PORT-GROUP", f"Remove the {role} port from the represented PortGroup."),
                )
    return report


@plugin("vendor_service_dependency_no_standard_needs")
def vendor_service_dependency_no_standard_needs(
    index: ArxmlIndex, rule: dict, selected: list[etree._Element]
) -> PluginReport:
    """TPS_SWCT_01005: exact vendor-specific dependency contains no AUTOSAR ServiceNeeds subtype."""
    report = PluginReport(checked=len(selected))
    for dependency in selected:
        dependency_ns = dependency.tag.rsplit("}", 1)[0][1:] if "}" in dependency.tag else ""
        wrapper = _first(dependency, {"SERVICE-NEEDS"})
        if wrapper is None:
            continue
        for need in wrapper:
            if not isinstance(need.tag, str):
                continue
            need_ns = need.tag.rsplit("}", 1)[0][1:] if "}" in need.tag else ""
            if need_ns != dependency_ns:
                continue
            report.fail(
                index, need,
                "Vendor-specific SwcServiceDependency contains a standardized AUTOSAR ServiceNeeds subtype",
                actual=local_name(need.tag),
                repair=_repair("remove", local_name(need.tag), "Remove the standardized ServiceNeeds from this vendor-specific dependency."),
            )
    return report
