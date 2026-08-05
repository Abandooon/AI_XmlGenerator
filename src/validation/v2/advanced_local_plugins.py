"""Qualified validators for local assertions that still require ARXML links.

These rules are not expressible as plain XPath cardinalities: the counted or
compared objects live behind typed AUTOSAR references.  Every resolver failure
is therefore reported as incomplete instead of being treated as a pass.
"""

from __future__ import annotations

from collections import defaultdict
from math import prod

from lxml import etree

from .arxml_index import ArxmlIndex, local_name
from .plugins import PluginReport, plugin


def _text(element: etree._Element | None) -> str:
    return (element.text or "").strip() if element is not None else ""


def _first(element: etree._Element, tag: str) -> etree._Element | None:
    return next(
        (item for item in element.iterdescendants() if local_name(item.tag) == tag),
        None,
    )


def _desc(element: etree._Element, tags: set[str]) -> list[etree._Element]:
    return [item for item in element.iterdescendants() if local_name(item.tag) in tags]


def _resolve(index: ArxmlIndex, ref: etree._Element | None, report: PluginReport):
    if ref is None:
        return None
    resolution = index.resolve(ref)
    if resolution.status != "resolved" or resolution.element is None:
        report.incomplete(f"{resolution.status} reference {resolution.reference} at {index.location(ref)}")
        return None
    return resolution.element


def _repair(action: str, target: str, instruction: str, **values: object) -> dict:
    return {"action": action, "target": target, "instruction": instruction, **values}


@plugin("client_server_operation_single_owner")
def client_server_operation_single_owner(
    index: ArxmlIndex, rule: dict, selected: list[etree._Element]
) -> PluginReport:
    """TPS_SWCT_01118: operation aggregation has exactly one CS interface owner."""
    report = PluginReport(checked=len(selected))
    for operation in selected:
        owner = index.nearest(operation, {"CLIENT-SERVER-INTERFACE"})
        if owner is None:
            report.fail(
                index, operation,
                "ClientServerOperation is not aggregated by exactly one ClientServerInterface",
                repair=_repair("move_element", "CLIENT-SERVER-OPERATION", "Aggregate the operation in one ClientServerInterface."),
            )
    return report


@plugin("service_role_matches_interface_name")
def service_role_matches_interface_name(
    index: ArxmlIndex, rule: dict, selected: list[etree._Element]
) -> PluginReport:
    """TPS_SWCT_01129: a CS interface assignment role is its standardized name."""
    report = PluginReport(checked=len(selected))
    for assignment in selected:
        if index.nearest(assignment, {"SWC-SERVICE-DEPENDENCY"}) is None:
            continue
        role = _first(assignment, "ROLE")
        port_ref = next((item for item in assignment.iterdescendants()
                         if "PORT-PROTOTYPE-REF" in local_name(item.tag)), None)
        if role is None or port_ref is None:
            report.incomplete(f"role or assigned port is missing at {index.location(assignment)}")
            continue
        port = _resolve(index, port_ref, report)
        if port is None:
            continue
        interface_ref = next((item for item in port.iterdescendants()
                              if local_name(item.tag).endswith("INTERFACE-TREF")), None)
        interface = _resolve(index, interface_ref, report)
        if interface is None or local_name(interface.tag) != "CLIENT-SERVER-INTERFACE":
            continue
        expected = _text(_first(interface, "SHORT-NAME"))
        if not expected:
            report.incomplete(f"ClientServerInterface has no SHORT-NAME at {index.location(interface)}")
        elif _text(role) != expected:
            report.fail(
                index, role, "RoleBasedPortAssignment.role must equal the used ClientServerInterface shortName",
                expected=expected, actual=_text(role), interface=index.path_of(interface),
                repair=_repair("replace_value", "ROLE", f"Set ROLE to {expected}.", expected=expected),
            )
    return report


@plugin("role_assignment_exclusion")
def role_assignment_exclusion(
    index: ArxmlIndex, rule: dict, selected: list[etree._Element]
) -> PluginReport:
    """constr_1301: temporaryRamBlock and defaultValue cannot coexist."""
    report = PluginReport(checked=len(selected))
    for dependency in selected:
        data_roles = {
            _text(_first(item, "ROLE"))
            for item in _desc(dependency, {"ROLE-BASED-DATA-ASSIGNMENT"})
        }
        type_roles = {
            _text(_first(item, "ROLE"))
            for item in _desc(dependency, {"ROLE-BASED-DATA-TYPE-ASSIGNMENT"})
        }
        if "defaultValue" in data_roles and "temporaryRamBlock" in type_roles:
            offender = next(item for item in _desc(dependency, {"ROLE-BASED-DATA-TYPE-ASSIGNMENT"})
                            if _text(_first(item, "ROLE")) == "temporaryRamBlock")
            report.fail(
                index, offender,
                "temporaryRamBlock is allowed only when no defaultValue data assignment exists",
                repair=_repair("remove", "ROLE-BASED-DATA-TYPE-ASSIGNMENT", "Remove temporaryRamBlock or the conflicting defaultValue assignment."),
            )
    return report


@plugin("port_interface_mapping_two_interfaces")
def port_interface_mapping_two_interfaces(
    index: ArxmlIndex, rule: dict, selected: list[etree._Element]
) -> PluginReport:
    """TPS_SWCT_01099: mapped element references must identify two interfaces."""
    report = PluginReport(checked=len(selected))
    interface_tags = {
        "CLIENT-SERVER-INTERFACE", "MODE-SWITCH-INTERFACE", "NV-DATA-INTERFACE",
        "PARAMETER-INTERFACE", "SENDER-RECEIVER-INTERFACE", "TRIGGER-INTERFACE",
    }
    for mapping in selected:
        owners: set[etree._Element] = set()
        refs = [item for item in mapping.iterdescendants()
                if local_name(item.tag).endswith(("-REF", "-TREF"))]
        if not refs:
            report.incomplete(f"mapping has no mapped element references at {index.location(mapping)}")
            continue
        for ref in refs:
            target = _resolve(index, ref, report)
            if target is None:
                continue
            owner = index.nearest(target, interface_tags)
            if owner is None:
                report.incomplete(f"mapped target has no PortInterface owner at {index.location(target)}")
            else:
                owners.add(owner)
        if len(owners) != 2:
            report.fail(
                index, mapping, "PortInterfaceMapping must describe elements of exactly two PortInterfaces",
                actual=[index.path_of(item) for item in owners], expected=2,
                repair=_repair("repair_reference", "mapped element references", "Reference elements owned by exactly two PortInterfaces."),
            )
    return report


@plugin("operation_mapping_argument_count")
def operation_mapping_argument_count(
    index: ArxmlIndex, rule: dict, selected: list[etree._Element]
) -> PluginReport:
    """constr_1269: mapped ClientServerOperations preserve argument count."""
    report = PluginReport(checked=len(selected))
    for mapping in selected:
        refs = [_first(mapping, tag) for tag in ("FIRST-OPERATION-REF", "SECOND-OPERATION-REF")]
        if any(ref is None for ref in refs):
            report.incomplete(f"operation mapping references are incomplete at {index.location(mapping)}")
            continue
        operations = [_resolve(index, ref, report) for ref in refs]
        if any(item is None for item in operations):
            continue
        counts = [len(_desc(item, {"ARGUMENT-DATA-PROTOTYPE"})) for item in operations]
        if counts[0] != counts[1]:
            report.fail(
                index, mapping, "Mapped ClientServerOperations must have the same number of arguments",
                first_count=counts[0], second_count=counts[1],
                repair=_repair("align_structure", "ARGUMENTS", "Add or remove mapped arguments so both operations have equal cardinality."),
            )
    return report


@plugin("mode_mapping_injective")
def mode_mapping_injective(
    index: ArxmlIndex, rule: dict, selected: list[etree._Element]
) -> PluginReport:
    """constr_1209: within one set, manager mode has at most one user mode."""
    report = PluginReport(checked=len(selected))
    grouped: dict[tuple[int, str], list[tuple[str, etree._Element]]] = defaultdict(list)
    for mapping in selected:
        owner = index.nearest(mapping, {"MODE-DECLARATION-MAPPING-SET"})
        if owner is None:
            report.incomplete(f"ModeDeclarationMapping has no mapping-set owner at {index.location(mapping)}")
            continue
        user_ref = _first(mapping, "MODE-USER-MODE")
        manager_ref = _first(mapping, "MODE-MANAGER-MODE")
        user_leaf = next((item for item in user_ref.iterdescendants()
                          if local_name(item.tag) == "MODE-DECLARATION-REF"), None) if user_ref is not None else None
        manager_leaf = next((item for item in manager_ref.iterdescendants()
                             if local_name(item.tag) == "MODE-DECLARATION-REF"), None) if manager_ref is not None else None
        if user_leaf is None or manager_leaf is None:
            report.incomplete(f"mode mapping pair is incomplete at {index.location(mapping)}")
            continue
        user = index.resolve(user_leaf)
        manager = index.resolve(manager_leaf)
        if user.status != "resolved" or manager.status != "resolved":
            report.incomplete(f"mode mapping reference is unresolved at {index.location(mapping)}")
            continue
        grouped[(id(owner), manager.reference)].append((user.reference, mapping))
    for values in grouped.values():
        users = {item[0] for item in values}
        if len(users) > 1:
            for user, mapping in values[1:]:
                report.fail(
                    index, mapping, "Several mode-user declarations map to the same mode-manager declaration",
                    user_mode=user, all_user_modes=sorted(users),
                    repair=_repair("repair_reference", "MODE-MANAGER-MODE", "Map each manager mode from at most one user mode."),
                )
    return report


def _value_count(container: etree._Element) -> int:
    count = 0
    for item in container.iterdescendants():
        tag = local_name(item.tag)
        if tag not in {"V", "VF", "VT", "VTF"}:
            continue
        parent = item.getparent()
        if parent is not None and local_name(parent.tag) == "VTF":
            continue
        count += 1
    return count


@plugin("sw_values_array_size_product")
def sw_values_array_size_product(
    index: ArxmlIndex, rule: dict, selected: list[etree._Element]
) -> PluginReport:
    """constr_2052: product(swArraySize) equals serialized physical values."""
    report = PluginReport(checked=len(selected))
    for content in selected:
        array_size = _first(content, "SW-ARRAYSIZE")
        values = _first(content, "SW-VALUES-PHYS")
        if array_size is None or values is None:
            continue
        raw_dimensions = [_text(item) for item in _desc(array_size, {"V"})]
        try:
            dimensions = [int(item, 10) for item in raw_dimensions]
        except ValueError:
            report.incomplete(f"unbound SW-ARRAYSIZE at {index.location(array_size)}")
            continue
        if not dimensions or any(item < 0 for item in dimensions):
            report.incomplete(f"invalid SW-ARRAYSIZE at {index.location(array_size)}")
            continue
        expected, actual = prod(dimensions), _value_count(values)
        if actual != expected:
            report.fail(
                index, values, "SW-VALUES-PHYS cardinality must equal the product of SW-ARRAYSIZE dimensions",
                dimensions=dimensions, expected=expected, actual=actual,
                repair=_repair("adjust_count", "SW-VALUES-PHYS", f"Provide exactly {expected} physical values."),
            )
    return report
