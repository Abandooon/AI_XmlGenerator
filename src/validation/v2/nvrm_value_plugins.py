"""NvBlock behavior and typed value-shape validators."""

from __future__ import annotations

from lxml import etree

from .arxml_index import ArxmlIndex, local_name
from .plugins import INTERFACE_REF_TAGS, PORT_TAGS, PluginReport, plugin

DATA_PROTOTYPE_TAGS = {
    "VARIABLE-DATA-PROTOTYPE", "PARAMETER-DATA-PROTOTYPE", "ARGUMENT-DATA-PROTOTYPE",
    "APPLICATION-ARRAY-ELEMENT", "APPLICATION-RECORD-ELEMENT",
}
ALLOWED_NV_EVENTS = {
    "OPERATION-INVOKED-EVENT", "TIMING-EVENT", "DATA-RECEIVED-EVENT", "SWC-MODE-SWITCH-EVENT",
}
RUNNABLE_FORBIDDEN_FEATURES = {
    "ASYNCHRONOUS-SERVER-CALL-RESULT-POINT", "DATA-READ-ACCESSS", "DATA-RECEIVE-POINT-BY-ARGUMENTS",
    "DATA-RECEIVE-POINT-BY-VALUES", "DATA-SEND-POINTS", "DATA-WRITE-ACCESSS",
    "EXCLUSIVE-AREA-REF", "EXTERNAL-TRIGGERING-POINT", "INTERNAL-TRIGGERING-POINT",
    "MODE-ACCESS-POINT", "MODE-SWITCH-POINT", "PARAMETER-ACCESS", "PER-INSTANCE-MEMORY-ACCESS",
    "READ-LOCAL-VARIABLES", "SERVER-CALL-POINTS", "WAIT-POINT", "WRITTEN-LOCAL-VARIABLES",
}
BEHAVIOR_FORBIDDEN_FEATURES = {
    "AR-TYPED-PER-INSTANCE-MEMORY", "EXCLUSIVE-AREA", "EXPLICIT-INTER-RUNNABLE-VARIABLES",
    "IMPLICIT-INTER-RUNNABLE-VARIABLES", "INCLUDED-DATA-TYPE-SET", "PER-INSTANCE-MEMORY",
    "SHARED-PARAMETERS", "STATIC-MEMORY",
}


def _text(element: etree._Element | None) -> str:
    return (element.text or "").strip() if element is not None else ""


def _first(element: etree._Element, tags: set[str]) -> etree._Element | None:
    return next((item for item in element.iterdescendants() if local_name(item.tag) in tags), None)


def _short_name(element: etree._Element) -> str:
    return _text(next((item for item in element if local_name(item.tag) == "SHORT-NAME"), None))


def _resolve(index: ArxmlIndex, ref: etree._Element | None, report: PluginReport, label: str):
    if ref is None:
        report.incomplete(f"missing {label}")
        return None
    resolution = index.resolve(ref)
    if resolution.status != "resolved" or resolution.element is None:
        report.incomplete(f"{resolution.status} {label} {resolution.reference} at {index.location(ref)}")
        return None
    return resolution.element


def _repair(action: str, target: str, instruction: str, **values: object) -> dict:
    return {"action": action, "target": target, "instruction": instruction, **values}


def _interface(index: ArxmlIndex, port: etree._Element, report: PluginReport):
    return _resolve(index, _first(port, INTERFACE_REF_TAGS), report, "PortPrototype interface reference")


@plugin("constant_mapping_reference_target")
def constant_mapping_reference_target(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_1030/constr_1031: existing constant mapping references have the exact target kind."""
    report = PluginReport(checked=len(selected))
    tags = {"CONSTANT-MAPPING-REF"} if rule["constraint_id"] == "constr_1030" else {"CONSTANT-VALUE-MAPPING-REF"}
    for subject in selected:
        for ref in index.descendants(subject, tags):
            target = _resolve(index, ref, report, local_name(ref.tag))
            if target is not None and local_name(target.tag) != "CONSTANT-SPECIFICATION-MAPPING-SET":
                report.fail(index, ref, f"{local_name(ref.tag)} does not reference a ConstantSpecificationMappingSet",
                            actual=local_name(target.tag),
                            repair=_repair("repair_reference", local_name(ref.tag), "Reference a ConstantSpecificationMappingSet."))
    return report


@plugin("nv_block_interface_not_service")
def nv_block_interface_not_service(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_1148: every interface used by an NvBlock component has IS-SERVICE=false."""
    report = PluginReport(checked=len(selected))
    for component in selected:
        for port in index.descendants(component, PORT_TAGS):
            interface = _interface(index, port, report)
            if interface is not None and _text(_first(interface, {"IS-SERVICE"})).lower() in {"true", "1"}:
                report.fail(index, port, "NvBlockSwComponentType port uses a PortInterface with IS-SERVICE=true",
                            interface=index.path_of(interface),
                            repair=_repair("repair_reference", "INTERFACE-TREF", "Reference an interface with IS-SERVICE=false."))
    return report


PORT_REF_TAGS = {
    "ASSIGNED-PORT-REF", "CLIENT-SERVER-PORT-REF", "P-PORT-PROTOTYPE-REF",
    "PORT-PROTOTYPE-REF", "PR-PORT-PROTOTYPE-REF", "R-PORT-PROTOTYPE-REF",
}


@plugin("nv_block_role_matches_interface")
def nv_block_role_matches_interface(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_2014: NvBlockDescriptor role names identify standardized NvM interfaces."""
    report = PluginReport(checked=len(selected))
    for descriptor in selected:
        for assignment in index.descendants(descriptor, {"ROLE-BASED-PORT-ASSIGNMENT"}):
            role_element = _first(assignment, {"ROLE"})
            role = _text(role_element)
            port = _resolve(index, _first(assignment, PORT_REF_TAGS), report, "NvBlock role assigned port")
            interface = _interface(index, port, report) if port is not None else None
            if interface is None:
                continue
            interface_name = _short_name(interface)
            if not interface_name:
                report.incomplete(f"assigned interface lacks SHORT-NAME at {index.location(interface)}")
            elif role != interface_name:
                report.fail(index, role_element if role_element is not None else assignment,
                            "NvBlockDescriptor role does not name the standardized NvM PortInterface",
                            actual=role, expected=interface_name,
                            repair=_repair("replace_value", "ROLE", "Use the exact standardized NvM interface name.", expected=interface_name))
    return report


def _nv_events(component: etree._Element, index: ArxmlIndex, tag: str) -> list[etree._Element]:
    return index.descendants(component, {tag})


def _valid_event_targets(index: ArxmlIndex, events: list[etree._Element], report: PluginReport) -> set[int]:
    targets: set[int] = set()
    for event in events:
        runnable = _resolve(index, _first(event, {"START-ON-EVENT-REF"}), report, f"{local_name(event.tag)} startOnEvent")
        if runnable is not None:
            targets.add(id(runnable))
    return targets


@plugin("nv_block_api_behavior_required")
def nv_block_api_behavior_required(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """TPS_SWCT_01150: a ClientServer NvM API port has the required server behavior elements."""
    report = PluginReport(checked=len(selected))
    for component in selected:
        has_cs_port = False
        for port in index.descendants(component, {"P-PORT-PROTOTYPE"}):
            interface = _interface(index, port, report)
            has_cs_port = has_cs_port or (interface is not None and local_name(interface.tag) == "CLIENT-SERVER-INTERFACE")
        if not has_cs_port:
            continue
        behavior = _first(component, {"SWC-INTERNAL-BEHAVIOR"})
        if behavior is None:
            report.fail(index, component, "NvBlockSwComponentType with ClientServer P port lacks SwcInternalBehavior",
                        repair=_repair("add_element", "SWC-INTERNAL-BEHAVIOR", "Add the NvM server internal behavior."))
            continue
        required = {
            "OPERATION-INVOKED-EVENT": bool(index.descendants(behavior, {"OPERATION-INVOKED-EVENT"})),
            "RUNNABLE-ENTITY": bool(index.descendants(behavior, {"RUNNABLE-ENTITY"})),
            "PORT-DEFINED-ARGUMENT-VALUE": bool(index.descendants(behavior, {"PORT-DEFINED-ARGUMENT-VALUE"})),
        }
        for tag, present in required.items():
            if not present:
                report.fail(index, behavior, f"NvM server internal behavior lacks {tag}",
                            repair=_repair("add_element", tag, f"Add the required {tag}."))
    return report


@plugin("nv_block_internal_behavior_shape")
def nv_block_internal_behavior_shape(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """TPS_SWCT_01151/constr_2015: NvBlock behavior uses only the explicitly permitted runtime model."""
    report = PluginReport(checked=len(selected))
    for component in selected:
        behavior = _first(component, {"SWC-INTERNAL-BEHAVIOR"})
        if behavior is None:
            continue
        operation_events = index.descendants(behavior, {"OPERATION-INVOKED-EVENT"})
        server_runnables = _valid_event_targets(index, operation_events, report)
        for runnable in index.descendants(behavior, {"RUNNABLE-ENTITY"}):
            if rule["constraint_id"] == "TPS_SWCT_01151" and id(runnable) not in server_runnables:
                continue
            for forbidden in index.descendants(runnable, RUNNABLE_FORBIDDEN_FEATURES):
                report.fail(index, forbidden, "NvBlock RunnableEntity defines a forbidden additional behavior feature",
                            feature=local_name(forbidden.tag),
                            repair=_repair("remove", local_name(forbidden.tag), "Remove this feature from the NvBlock runnable."))
        if rule["constraint_id"] != "constr_2015":
            continue
        for event in index.descendants(behavior):
            tag = local_name(event.tag)
            if tag.endswith("-EVENT") and tag not in ALLOWED_NV_EVENTS:
                report.fail(index, event, "NvBlock SwcInternalBehavior aggregates an unsupported RTEEvent kind",
                            actual=tag, allowed=sorted(ALLOWED_NV_EVENTS),
                            repair=_repair("remove", tag, "Remove or replace the unsupported event."))
        for forbidden in index.descendants(behavior, BEHAVIOR_FORBIDDEN_FEATURES):
            report.fail(index, forbidden, "NvBlock SwcInternalBehavior defines a forbidden aggregation",
                        feature=local_name(forbidden.tag),
                        repair=_repair("remove", local_name(forbidden.tag), "Remove the unsupported NvBlock behavior aggregation."))
    return report


@plugin("nv_block_runnable_symbol")
def nv_block_runnable_symbol(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_1234: NvM operation-triggered runnable symbols use the corresponding NvM API name."""
    report = PluginReport(checked=len(selected))
    for component in selected:
        for event in _nv_events(component, index, "OPERATION-INVOKED-EVENT"):
            runnable = _resolve(index, _first(event, {"START-ON-EVENT-REF"}), report, "OperationInvokedEvent runnable")
            operation = _resolve(index, _first(event, {"TARGET-PROVIDED-OPERATION-REF"}), report, "OperationInvokedEvent provided operation")
            if runnable is None or operation is None:
                continue
            interface = index.nearest(operation, {"CLIENT-SERVER-INTERFACE"})
            interface_name = _short_name(interface) if interface is not None else ""
            if "NVM" not in interface_name.upper():
                report.incomplete(f"cannot establish standardized NvM API interface for {index.path_of(operation)}")
                continue
            operation_name = _short_name(operation)
            symbol_element = _first(runnable, {"SYMBOL"})
            symbol = _text(symbol_element)
            allowed = {operation_name}
            if not operation_name.startswith("NvM_"):
                allowed.add("NvM_" + operation_name)
            if symbol not in allowed:
                expected = sorted(allowed)
                report.fail(index, symbol_element if symbol_element is not None else runnable,
                            "NvBlock operation-triggered RunnableEntity uses a non-NvM API symbol",
                            actual=symbol, allowed=expected,
                            repair=_repair("replace_value", "SYMBOL", "Use the NvM API name associated with the triggering operation.", allowed=expected))
    return report


@plugin("nv_block_store_strategy_event")
def nv_block_store_strategy_event(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """TPS_SWCT_01587/01588: configured storage strategy has a runnable-targeting event."""
    report = PluginReport(checked=len(selected))
    if rule["constraint_id"] == "TPS_SWCT_01587":
        flag_tag, event_tag = "STORE-CYCLIC", "TIMING-EVENT"
    else:
        flag_tag, event_tag = "STORE-IMMEDIATE", "DATA-RECEIVED-EVENT"
    for component in selected:
        enabled = any(_text(_first(needs, {flag_tag})).lower() in {"true", "1"}
                      for needs in index.descendants(component, {"NV-BLOCK-NEEDS"}))
        if not enabled:
            continue
        events = index.descendants(component, {event_tag})
        if not events:
            report.fail(index, component, f"{flag_tag}=true requires {event_tag}",
                        repair=_repair("add_element", event_tag, f"Add a {event_tag} that starts the storage runnable."))
        else:
            _valid_event_targets(index, events, report)
    return report


VALUE_SPEC_CONTAINER = {
    "RECORD-VALUE-SPECIFICATION": "FIELDS",
    "ARRAY-VALUE-SPECIFICATION": "ELEMENTS",
}


def _value_count(value_spec: etree._Element) -> int:
    container = next((item for item in value_spec if local_name(item.tag) == VALUE_SPEC_CONTAINER[local_name(value_spec.tag)]), None)
    if container is None:
        return 0
    return len([item for item in container if isinstance(item.tag, str)])


def _owned_count(index: ArxmlIndex, owner: etree._Element, tag: str, owner_tags: set[str]) -> int:
    count = 0
    for item in index.descendants(owner, {tag}):
        current = index.parent.get(item)
        nearest_owner = None
        while current is not None:
            if local_name(current.tag) in owner_tags:
                nearest_owner = current
                break
            current = index.parent.get(current)
        if nearest_owner is owner:
            count += 1
    return count


def _integer(element: etree._Element | None, report: PluginReport, index: ArxmlIndex, label: str) -> int | None:
    try:
        return int(_text(element))
    except ValueError:
        report.incomplete(f"non-integer {label} at {index.location(element) if element is not None else None}")
        return None


@plugin("typed_value_shape_cardinality")
def typed_value_shape_cardinality(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_1271..1274: record/array value arity equals the resolved data type shape."""
    report = PluginReport(checked=len(selected))
    constraint_id = rule["constraint_id"]
    expected_spec_tag = "RECORD-VALUE-SPECIFICATION" if constraint_id in {"constr_1271", "constr_1272"} else "ARRAY-VALUE-SPECIFICATION"
    for value_spec in selected:
        if local_name(value_spec.tag) != expected_spec_tag:
            continue
        owner = index.nearest(value_spec, DATA_PROTOTYPE_TAGS)
        if owner is None:
            continue
        data_type = _resolve(index, _first(owner, {"TYPE-TREF"}), report, "DataPrototype type")
        if data_type is None:
            continue
        type_tag = local_name(data_type.tag)
        expected: int | None = None
        if constraint_id == "constr_1271" and type_tag == "APPLICATION-RECORD-DATA-TYPE":
            expected = _owned_count(index, data_type, "APPLICATION-RECORD-ELEMENT", {"APPLICATION-RECORD-DATA-TYPE"})
        elif constraint_id == "constr_1272" and type_tag == "IMPLEMENTATION-DATA-TYPE" and _text(_first(data_type, {"CATEGORY"})) == "STRUCTURE":
            expected = _owned_count(index, data_type, "IMPLEMENTATION-DATA-TYPE-ELEMENT", {"IMPLEMENTATION-DATA-TYPE", "IMPLEMENTATION-DATA-TYPE-ELEMENT"})
        elif constraint_id == "constr_1273" and type_tag == "APPLICATION-ARRAY-DATA-TYPE":
            element = _first(data_type, {"APPLICATION-ARRAY-ELEMENT"})
            expected = _integer(_first(element, {"MAX-NUMBER-OF-ELEMENTS"}) if element is not None else None, report, index, "maxNumberOfElements")
        elif constraint_id == "constr_1274" and type_tag == "IMPLEMENTATION-DATA-TYPE" and _text(_first(data_type, {"CATEGORY"})) == "ARRAY":
            element = _first(data_type, {"IMPLEMENTATION-DATA-TYPE-ELEMENT"})
            expected = _integer(_first(element, {"ARRAY-SIZE"}) if element is not None else None, report, index, "arraySize")
        if expected is None:
            continue
        actual = _value_count(value_spec)
        if actual != expected:
            report.fail(index, value_spec, "ValueSpecification element count does not match its resolved data type",
                        actual=actual, expected=expected, type=index.path_of(data_type),
                        repair=_repair("set_cardinality", VALUE_SPEC_CONTAINER[expected_spec_tag], "Add or remove value entries to match the data type.", expected=expected))
    return report
