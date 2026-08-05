"""Executable cardinality rules, including manifest-bound generation use cases."""

from __future__ import annotations

from collections import Counter

from lxml import etree

from .arxml_index import ArxmlIndex, local_name
from .plugins import INTERFACE_REF_TAGS, PluginReport, plugin

INTERFACE_MEMBER_TAGS = {
    "VARIABLE-DATA-PROTOTYPE", "PARAMETER-DATA-PROTOTYPE",
    "MODE-DECLARATION-GROUP-PROTOTYPE", "CLIENT-SERVER-OPERATION", "TRIGGER",
}
VALUE_SPECS = {
    "APPLICATION-VALUE-SPECIFICATION", "APPLICATION-RULE-BASED-VALUE-SPECIFICATION",
    "ARRAY-VALUE-SPECIFICATION", "NUMERICAL-RULE-BASED-VALUE-SPECIFICATION",
    "NUMERICAL-VALUE-SPECIFICATION", "RECORD-VALUE-SPECIFICATION",
    "REFERENCE-VALUE-SPECIFICATION", "TEXT-VALUE-SPECIFICATION", "CONSTANT-REFERENCE",
}
PORT_REF_TAGS = {
    "PORT-REF", "ASSIGNED-PORT-REF", "PORT-PROTOTYPE-REF", "P-PORT-PROTOTYPE-REF",
    "R-PORT-PROTOTYPE-REF", "PR-PORT-PROTOTYPE-REF", "CONTEXT-P-PORT-REF", "TARGET-P-PORT-REF",
}


def _text(element: etree._Element | None) -> str:
    return (element.text or "").strip() if element is not None else ""


def _direct(element: etree._Element, tag: str) -> etree._Element | None:
    return next((child for child in element if local_name(child.tag) == tag), None)


def _first(element: etree._Element, tags: set[str]) -> etree._Element | None:
    return next((item for item in element.iterdescendants() if local_name(item.tag) in tags), None)


def _short_name(element: etree._Element) -> str:
    return _text(_direct(element, "SHORT-NAME"))


def _resolve(index: ArxmlIndex, ref: etree._Element | None, report: PluginReport, label: str, *, required: bool = True) -> etree._Element | None:
    if ref is None:
        if required:
            report.incomplete(f"missing {label}")
        return None
    resolution = index.resolve(ref)
    if resolution.status != "resolved" or resolution.element is None:
        report.incomplete(f"{resolution.status} {label} {resolution.reference} at {index.location(ref)}")
        return None
    return resolution.element


def _repair(action: str, target: str, instruction: str, **values: object) -> dict:
    return {"action": action, "target": target, "instruction": instruction, **values}


def _owned(index: ArxmlIndex, owner: etree._Element, tag: str, owner_tags: set[str]) -> list[etree._Element]:
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


def _parameters(index: ArxmlIndex, rule: dict, target: etree._Element, report: PluginReport) -> dict | None:
    context = rule.get("_validation_context") or {}
    values = (((context.get("declared_parameters") or {}).get(rule["constraint_id"]) or {}).get(index.path_of(target)))
    if not isinstance(values, dict):
        report.incomplete(
            f"validation context has no declared parameters for {rule['constraint_id']} target {index.path_of(target)}"
        )
        return None
    return values


def _value_count(index: ArxmlIndex, target: etree._Element, report: PluginReport) -> int | None:
    value = next((item for item in target.iterdescendants() if local_name(item.tag) in VALUE_SPECS), None)
    if value is None:
        report.incomplete(f"target has no ValueSpecification at {index.location(target)}")
        return None
    if local_name(value.tag) not in {"ARRAY-VALUE-SPECIFICATION", "RECORD-VALUE-SPECIFICATION"}:
        return 1
    return len([
        item for item in value.iterdescendants()
        if local_name(item.tag) in VALUE_SPECS
        and index.nearest(index.parent.get(item), VALUE_SPECS) is value
    ])


@plugin("manifest_variant_value_count")
def manifest_variant_value_count(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    key = "expected_max_value_count" if rule["constraint_id"] == "TPS_SWCT_01180" else "expected_variant_value_count"
    for target in selected:
        params = _parameters(index, rule, target, report)
        if params is None:
            continue
        expected = params.get(key)
        if not isinstance(expected, int) or isinstance(expected, bool) or expected < 0:
            report.incomplete(f"{key} must be a non-negative integer for {index.path_of(target)}")
            continue
        actual = _value_count(index, target, report)
        if actual is not None and actual != expected:
            report.fail(index, target, "Variant compound primitive initValue has the wrong number of values",
                        actual=actual, expected=expected, expectation_key=key,
                        repair=_repair("set_cardinality", "INIT-VALUE", "Generate exactly the manifest-declared maximum/variant value count.", expected=expected))
    return report


def _interface(index: ArxmlIndex, port: etree._Element, report: PluginReport) -> etree._Element | None:
    return _resolve(index, _first(port, INTERFACE_REF_TAGS), report, "PortPrototype interface")


def _members(index: ArxmlIndex, interface: etree._Element) -> list[etree._Element]:
    return [
        item for item in interface.iterdescendants()
        if local_name(item.tag) in INTERFACE_MEMBER_TAGS
        and index.nearest(index.parent.get(item), {local_name(interface.tag)}) is interface
    ]


def _mapping_pairs(index: ArxmlIndex, mapping: etree._Element, report: PluginReport) -> tuple[list[tuple[etree._Element, etree._Element]], set[int]]:
    pairs: list[tuple[etree._Element, etree._Element]] = []
    used: set[int] = set()
    pair_tags = {
        "DATA-ELEMENT-MAPPING", "VARIABLE-DATA-PROTOTYPE-MAPPING", "PARAMETER-DATA-PROTOTYPE-MAPPING",
        "MODE-DECLARATION-GROUP-PROTOTYPE-MAPPING", "CLIENT-SERVER-OPERATION-MAPPING", "TRIGGER-MAPPING",
        "SUB-ELEMENT-MAPPING",
    }
    for pair in [item for item in mapping.iterdescendants() if local_name(item.tag) in pair_tags]:
        refs = [item for item in pair.iterdescendants() if local_name(item.tag).endswith("-REF") and _text(item)]
        targets = [_resolve(index, ref, report, "PortInterfaceMapping member") for ref in refs]
        targets = [item for item in targets if item is not None and local_name(item.tag) in INTERFACE_MEMBER_TAGS]
        unique = []
        for target in targets:
            if all(target is not item for item in unique):
                unique.append(target)
        if len(unique) != 2:
            report.incomplete(f"mapping pair does not resolve exactly two interface members at {index.location(pair)}")
            continue
        pairs.append((unique[0], unique[1]))
        for target in unique:
            if id(target) in used:
                report.fail(index, pair, "PortInterfaceMapping maps an interface member more than once",
                            member=index.path_of(target),
                            repair=_repair("remove_or_repair_mapping", local_name(pair.tag), "Keep a one-to-one explicit member mapping."))
            used.add(id(target))
    return pairs, used


@plugin("strict_port_interface_mapping")
def strict_port_interface_mapping(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for mapping in selected:
        refs = [item for item in mapping.iterdescendants() if "INTERFACE" in local_name(item.tag) and local_name(item.tag).endswith(("-REF", "-TREF"))]
        interfaces: list[etree._Element] = []
        for ref in refs:
            target = _resolve(index, ref, report, "PortInterfaceMapping interface")
            if target is not None and "INTERFACE" in local_name(target.tag) and all(target is not item for item in interfaces):
                interfaces.append(target)
        if len(interfaces) != 2:
            report.incomplete(f"PortInterfaceMapping does not resolve exactly two interfaces at {index.location(mapping)}")
            continue
        pairs, used = _mapping_pairs(index, mapping, report)
        report.observe(
            semantic="strict_port_interface_mapping", mapping=index.path_of(mapping),
            interfaces=[index.path_of(item) for item in interfaces], explicit_pair_count=len(pairs),
            equal_short_name_fallback="disabled",
        )
        # Explicit mapping is strictly binding: a same-name pair not represented here
        # is deliberately not added. Connector compatibility plugins consume pairs only.
        for first, second in pairs:
            if index.nearest(first, {local_name(interfaces[0].tag)}) not in interfaces or index.nearest(second, {local_name(interfaces[1].tag)}) not in interfaces:
                report.fail(index, mapping, "PortInterfaceMapping pair escapes the two mapped interfaces",
                            pair=[index.path_of(first), index.path_of(second)],
                            repair=_repair("repair_reference", "PORT-INTERFACE-MAPPING", "Reference one member from each mapped interface."))
    return report


def _connected_other_ports(index: ArxmlIndex, outer: etree._Element, report: PluginReport) -> list[tuple[etree._Element, etree._Element]]:
    result: list[tuple[etree._Element, etree._Element]] = []
    for connector_tag in {"DELEGATION-SW-CONNECTOR", "PASS-THROUGH-SW-CONNECTOR"}:
        for connector in index.elements(connector_tag):
            refs = [item for item in connector.iterdescendants() if local_name(item.tag) in {
                "OUTER-PORT-REF", "PROVIDED-OUTER-PORT-REF", "REQUIRED-OUTER-PORT-REF", "TARGET-P-PORT-REF", "TARGET-R-PORT-REF"
            }]
            endpoints = [(ref, _resolve(index, ref, report, "hierarchical connector port")) for ref in refs]
            if not any(target is outer for _, target in endpoints):
                continue
            for _, target in endpoints:
                if target is not None and target is not outer:
                    result.append((connector, target))
    return result


def _explicit_pairs_for_connector(index: ArxmlIndex, connector: etree._Element, report: PluginReport) -> set[tuple[int, int]]:
    result: set[tuple[int, int]] = set()
    for ref in connector.iterdescendants():
        if "MAPPING" not in local_name(ref.tag) or not local_name(ref.tag).endswith("-REF"):
            continue
        mapping = _resolve(index, ref, report, "connector PortInterfaceMapping")
        if mapping is None:
            continue
        pairs, _ = _mapping_pairs(index, mapping, report)
        result.update((id(first), id(second)) for first, second in pairs)
        result.update((id(second), id(first)) for first, second in pairs)
    return result


@plugin("provided_outer_delegation_complete")
def provided_outer_delegation_complete(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for outer in selected:
        connections = _connected_other_ports(index, outer, report)
        if not connections:
            continue
        outer_if = _interface(index, outer, report)
        if outer_if is None:
            continue
        outer_members = _members(index, outer_if)
        matches: dict[int, list[tuple[etree._Element, etree._Element]]] = {id(item): [] for item in outer_members}
        for connector, other in connections:
            other_if = _interface(index, other, report)
            if other_if is None:
                continue
            explicit = _explicit_pairs_for_connector(index, connector, report)
            has_explicit_mapping = bool(explicit)
            for left in outer_members:
                for right in _members(index, other_if):
                    compatible = (id(left), id(right)) in explicit if has_explicit_mapping else (
                        local_name(left.tag) == local_name(right.tag) and _short_name(left) == _short_name(right)
                    )
                    if compatible:
                        matches[id(left)].append((connector, right))
        for member in outer_members:
            count = len(matches[id(member)])
            exact = local_name(member.tag) in {"MODE-DECLARATION-GROUP-PROTOTYPE", "CLIENT-SERVER-OPERATION", "TRIGGER"}
            valid = count == 1 if exact else count >= 1
            if not valid:
                report.fail(index, member, "Provided outer interface member has invalid hierarchical connection coverage",
                            actual=count, expected="exactly 1" if exact else "at least 1",
                            repair=_repair("add_or_remove_connector_mapping", "SW-CONNECTOR", "Provide the required compatible inner/outer member coverage."))
    return report


@plugin("runnable_argument_cardinality")
def runnable_argument_cardinality(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for event in index.elements("OPERATION-INVOKED-EVENT"):
        runnable = _resolve(index, _first(event, {"START-ON-EVENT-REF"}), report, "OperationInvokedEvent runnable")
        operation = _resolve(index, _first(event, {"TARGET-PROVIDED-OPERATION-REF", "OPERATION-REF"}), report, "invoked operation")
        if runnable is None or operation is None:
            continue
        runnable_args = _owned(index, runnable, "RUNNABLE-ENTITY-ARGUMENT", {"RUNNABLE-ENTITY"})
        if not runnable_args:
            continue
        operation_args = _owned(index, operation, "ARGUMENT-DATA-PROTOTYPE", {"CLIENT-SERVER-OPERATION"})
        port = _resolve(index, _first(event, {"CONTEXT-P-PORT-REF", "TARGET-P-PORT-REF", "PORT-PROTOTYPE-REF"}), report, "event port")
        port_values = 0
        if port is not None:
            for option in index.elements("PORT-API-OPTION"):
                option_port = _resolve(index, _first(option, PORT_REF_TAGS), report, "PortApiOption port", required=False)
                if option_port is port:
                    port_values += len(_owned(index, option, "PORT-DEFINED-ARGUMENT-VALUE", {"PORT-API-OPTION"}))
        expected = len(operation_args) + port_values
        if len(runnable_args) != expected:
            report.fail(index, runnable, "RunnableEntity argument count does not match operation plus PortApiOption arguments",
                        actual=len(runnable_args), operation_arguments=len(operation_args), port_argument_values=port_values, expected=expected,
                        repair=_repair("set_cardinality", "RUNNABLE-ENTITY-ARGUMENT", "Align runnable arguments with the invoked operation and applicable port API option.", expected=expected))
    return report


NVM_PORT_ROLES = {
    "TPS_SWCT_02501": {"NvmService": (0, 1), "NvMNotifyJobFinished": (0, 1), "NvMNotifyInitBlock": (0, 1), "NvMAdmin": (0, 1)},
    "TPS_SWCT_02502": {"NvmService": (1, 1), "NvMNotifyJobFinished": (0, 1), "NvMNotifyInitBlock": (0, 1), "NvMAdmin": (0, 1)},
    "TPS_SWCT_02503": {"NvMService": (0, 1), "NvMNotifyJobFinished": (0, 1), "NvMNotifyInitBlock": (0, 1), "NvMAdmin": (0, 1), "NvDataPort": (1, None)},
    "TPS_SWCT_02504": {"NvMService": (0, 1), "NvMNotifyJobFinished": (0, 1), "NvMNotifyInitBlock": (0, 1), "NvMAdmin": (0, 1), "NvMMirror": (1, 1)},
}
NVM_DATA_ROLES = {
    "TPS_SWCT_02501": {"ramBlock": (1, 1), "defaultValue": (0, 1)},
    "TPS_SWCT_02502": {"defaultValue": (0, 1)},
    "TPS_SWCT_02503": {},
    "TPS_SWCT_02504": {"defaultValue": (0, 1)},
}
NVM_TYPE_ROLES = {
    "TPS_SWCT_02501": {}, "TPS_SWCT_02502": {"temporaryRamBlock": (0, 1)},
    "TPS_SWCT_02503": {}, "TPS_SWCT_02504": {"temporaryRamBlock": (0, 1)},
}


def _role_counts(index: ArxmlIndex, owner: etree._Element, assignment_tag: str) -> tuple[Counter, dict[str, list[etree._Element]]]:
    items: dict[str, list[etree._Element]] = {}
    for assignment in _owned(index, owner, assignment_tag, {"SWC-SERVICE-DEPENDENCY"}):
        role = _text(_first(assignment, {"ROLE"}))
        items.setdefault(role, []).append(assignment)
    return Counter({role: len(values) for role, values in items.items()}), items


def _validate_role_table(index: ArxmlIndex, owner: etree._Element, report: PluginReport, assignment_tag: str, table: dict[str, tuple[int, int | None]]) -> dict[str, list[etree._Element]]:
    counts, items = _role_counts(index, owner, assignment_tag)
    for role, count in counts.items():
        if role not in table:
            for assignment in items[role]:
                report.fail(index, assignment, f"{assignment_tag} role is not allowed for the declared NvM use case",
                            actual=role, allowed=sorted(table),
                            repair=_repair("remove_or_replace_assignment", assignment_tag, "Use only roles allowed by the selected NvM use-case table."))
    for role, (minimum, maximum) in table.items():
        actual = counts.get(role, 0)
        if actual < minimum or (maximum is not None and actual > maximum):
            report.fail(index, owner, f"{assignment_tag} role multiplicity is invalid for the declared NvM use case",
                        role=role, actual=actual, minimum=minimum, maximum=maximum,
                        repair=_repair("set_cardinality", assignment_tag, "Add or remove assignments for this role.", role=role, minimum=minimum, maximum=maximum))
    return items


@plugin("nvm_use_case_role_table")
def nvm_use_case_role_table(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    cid = rule["constraint_id"]
    for dependency in selected:
        port_items = _validate_role_table(index, dependency, report, "ROLE-BASED-PORT-ASSIGNMENT", NVM_PORT_ROLES[cid])
        data_items = _validate_role_table(index, dependency, report, "ROLE-BASED-DATA-ASSIGNMENT", NVM_DATA_ROLES[cid])
        type_items = _validate_role_table(index, dependency, report, "ROLE-BASED-DATA-TYPE-ASSIGNMENT", NVM_TYPE_ROLES[cid])
        represented = _owned(index, dependency, "REPRESENTED-PORT-GROUP-REF", {"SWC-SERVICE-DEPENDENCY"})
        for item in represented:
            report.fail(index, item, "RepresentedPortGroup is not allowed for this NvM use case",
                        repair=_repair("remove", "REPRESENTED-PORT-GROUP-REF", "Remove the represented port group from this service dependency."))
        if cid in {"TPS_SWCT_02501", "TPS_SWCT_02504"}:
            for assignment in data_items.get("defaultValue", []):
                target = _resolve(index, _first(assignment, {"USED-PARAMETER-ELEMENT-REF", "PARAMETER-DATA-PROTOTYPE-REF"}), report, "defaultValue parameter", required=False)
                if target is None or local_name(target.tag) != "PARAMETER-DATA-PROTOTYPE":
                    report.fail(index, assignment, "defaultValue must reference a ParameterDataPrototype",
                                repair=_repair("repair_reference", "USED-PARAMETER-ELEMENT-REF", "Reference a per-instance or shared ParameterDataPrototype."))
        for assignment in type_items.get("temporaryRamBlock", []):
            target = _resolve(index, _first(assignment, {"IMPLEMENTATION-DATA-TYPE-REF", "ASSIGNED-DATA-TYPE-REF"}), report, "temporary RAM block type")
            if target is not None and local_name(target.tag) != "IMPLEMENTATION-DATA-TYPE":
                report.fail(index, assignment, "temporaryRamBlock must reference an ImplementationDataType",
                            repair=_repair("repair_reference", "IMPLEMENTATION-DATA-TYPE-REF", "Reference an ImplementationDataType."))
        for role, assignments in port_items.items():
            if role == "NvDataPort":
                for assignment in assignments:
                    port = _resolve(index, _first(assignment, PORT_REF_TAGS), report, "NvDataPort assignment")
                    interface = _interface(index, port, report) if port is not None else None
                    if interface is not None and local_name(interface.tag) != "NV-DATA-INTERFACE":
                        report.fail(index, assignment, "NvDataPort role does not reference an NvDataInterface port",
                                    repair=_repair("repair_reference", "ASSIGNED-PORT-REF", "Reference a PortPrototype typed by NvDataInterface."))
    return report


@plugin("roe_service_role_table")
def roe_service_role_table(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for dependency in selected:
        _validate_role_table(index, dependency, report, "ROLE-BASED-PORT-ASSIGNMENT", {"Dcm_Roe": (1, 1)})
        for tag in {"ROLE-BASED-DATA-ASSIGNMENT", "REPRESENTED-PORT-GROUP-REF"}:
            for item in _owned(index, dependency, tag, {"SWC-SERVICE-DEPENDENCY"}):
                report.fail(index, item, f"{tag} is not allowed for the ROE service use case",
                            repair=_repair("remove", tag, "Remove this assignment from the ROE service dependency."))
    return report


@plugin("manifest_variation_proxy_table")
def manifest_variation_proxy_table(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for proxy in selected:
        params = _parameters(index, rule, proxy, report)
        if params is None:
            continue
        expected_category = params.get("category")
        actual_category = _text(_direct(proxy, "CATEGORY"))
        if expected_category is not None and actual_category != expected_category:
            report.fail(index, _direct(proxy, "CATEGORY") or proxy, "VariationPointProxy category differs from the manifest-bound table row",
                        actual=actual_category, expected=expected_category,
                        repair=_repair("replace_value", "CATEGORY", "Use the category associated with the selected table row."))
        table = params.get("allowed_multiplicities")
        if not isinstance(table, dict) or not table:
            report.incomplete(f"allowed_multiplicities table row is missing for {index.path_of(proxy)}")
            continue
        direct_counts = Counter(local_name(child.tag) for child in proxy if isinstance(child.tag, str) and local_name(child.tag) not in {"SHORT-NAME", "CATEGORY"})
        for raw_tag, bounds in table.items():
            if not isinstance(bounds, dict):
                report.incomplete(f"invalid multiplicity bounds for {raw_tag} at {index.path_of(proxy)}")
                continue
            minimum = bounds.get("min", 0)
            maximum = bounds.get("max", 0)
            if not isinstance(minimum, int) or (maximum is not None and not isinstance(maximum, int)):
                report.incomplete(f"non-integer multiplicity bounds for {raw_tag} at {index.path_of(proxy)}")
                continue
            actual = direct_counts.pop(str(raw_tag), 0)
            if actual < minimum or (maximum is not None and actual > maximum):
                report.fail(index, proxy, "VariationPointProxy attribute multiplicity violates the manifest-bound Table 7.111 row",
                            attribute=raw_tag, actual=actual, minimum=minimum, maximum=maximum,
                            repair=_repair("set_cardinality", str(raw_tag), "Apply the exact multiplicity from AUTOSAR Table 7.111.", minimum=minimum, maximum=maximum))
        for tag, count in direct_counts.items():
            if count:
                report.fail(index, proxy, "VariationPointProxy attribute is not listed in the active Table 7.111 row and therefore has multiplicity zero",
                            attribute=tag, actual=count,
                            repair=_repair("remove", tag, "Remove attributes not permitted by the active binding-time/category row."))
    return report

