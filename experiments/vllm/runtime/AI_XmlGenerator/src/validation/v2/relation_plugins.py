"""Qualified relationship and conditional AUTOSAR validators.

Every reference-dependent branch records incomplete evidence instead of
silently accepting an unresolved or ambiguous reference.
"""

from __future__ import annotations

from collections import defaultdict

from lxml import etree

from .arxml_index import ArxmlIndex, local_name
from .plugins import COMPONENT_TAGS, INTERFACE_REF_TAGS, PluginReport, plugin

DATA_INTERFACE_TAGS = {"SENDER-RECEIVER-INTERFACE", "NV-DATA-INTERFACE"}
EVENT_TAGS = {
    "ASYNCHRONOUS-SERVER-CALL-RETURNS-EVENT", "BACKGROUND-EVENT",
    "DATA-RECEIVE-ERROR-EVENT", "DATA-RECEIVED-EVENT", "DATA-SEND-COMPLETED-EVENT",
    "DATA-WRITE-COMPLETED-EVENT", "EXTERNAL-TRIGGER-OCCURRED-EVENT", "INIT-EVENT",
    "INTERNAL-TRIGGER-OCCURRED-EVENT", "MODE-SWITCHED-ACK-EVENT",
    "OPERATION-INVOKED-EVENT", "SWC-MODE-MANAGER-ERROR-EVENT",
    "SWC-MODE-SWITCH-EVENT", "TIMING-EVENT", "TRANSFORMER-HARD-ERROR-EVENT",
}


def _text(element: etree._Element | None) -> str:
    return (element.text or "").strip() if element is not None else ""


def _first(element: etree._Element, tags: set[str]) -> etree._Element | None:
    return next((item for item in element.iterdescendants() if local_name(item.tag) in tags), None)


def _direct(element: etree._Element, tag: str) -> list[etree._Element]:
    return [item for item in element if local_name(item.tag) == tag]


def _resolve(index: ArxmlIndex, ref: etree._Element | None, report: PluginReport, label: str):
    if ref is None:
        report.incomplete(f"missing {label}")
        return None
    resolution = index.resolve(ref)
    if resolution.status != "resolved" or resolution.element is None:
        report.incomplete(
            f"{resolution.status} {label} {resolution.reference} at {index.location(ref)}"
        )
        return None
    return resolution.element


def _repair(action: str, target: str, instruction: str, **values: object) -> dict:
    return {"action": action, "target": target, "instruction": instruction, **values}


def _interface_of_port(index: ArxmlIndex, port: etree._Element, report: PluginReport):
    ref = _first(port, INTERFACE_REF_TAGS)
    return _resolve(index, ref, report, f"interface reference for {index.path_of(port)}")


def _impl_policy(element: etree._Element) -> str:
    return _text(_first(element, {"SW-IMPL-POLICY"})) or "STANDARD"


def _referenced_data(index: ArxmlIndex, element: etree._Element, report: PluginReport):
    tags = {
        "TARGET-DATA-PROTOTYPE-REF", "TARGET-DATA-ELEMENT-REF", "DATA-ELEMENT-REF",
        "LOCAL-VARIABLE-REF",
    }
    ref = _first(element, tags)
    return _resolve(index, ref, report, f"data prototype reference for {index.path_of(element)}")


@plugin("runnable_single_wait_point")
def runnable_single_wait_point(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_1090: a non-concurrently invokable runnable has at most one wait point."""
    report = PluginReport(checked=len(selected))
    for runnable in selected:
        concurrent = _text(_first(runnable, {"CAN-BE-INVOKED-CONCURRENTLY"})).lower() in {"true", "1"}
        wait_points = index.descendants(runnable, {"WAIT-POINT"})
        if not concurrent and len(wait_points) > 1:
            report.fail(
                index, runnable, "RunnableEntity that is scheduled as one instance has more than one WaitPoint",
                actual=len(wait_points), maximum=1,
                repair=_repair("remove_extra", "WAIT-POINT", "Retain at most one WaitPoint or model concurrent invocation explicitly."),
            )
    return report


@plugin("sub_element_mapping_at_most_one")
def sub_element_mapping_at_most_one(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_1190: composite-to-primitive mapping has at most one subElementMapping."""
    report = PluginReport(checked=len(selected))
    for mapping in selected:
        values = index.descendants(mapping, {"SUB-ELEMENT-MAPPING"})
        if len(values) > 1:
            report.fail(index, mapping, "DataPrototypeMapping has more than one SubElementMapping",
                        actual=len(values), maximum=1,
                        repair=_repair("remove_extra", "SUB-ELEMENT-MAPPING", "Retain exactly the single composite-to-primitive mapping."))
    return report


@plugin("axis_cont_mandatory_fields")
def axis_cont_mandatory_fields(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_2050/constr_2057: axis content has one index and one array size."""
    report = PluginReport(checked=len(selected))
    for axis in selected:
        for tag in ("SW-AXIS-INDEX", "SW-ARRAYSIZE"):
            count = len(index.descendants(axis, {tag}))
            if count != 1:
                report.fail(index, axis, f"{local_name(axis.tag)} must define exactly one {tag}",
                            actual=count, expected=1,
                            repair=_repair("set_cardinality", tag, f"Define exactly one {tag}.", expected=1))
    return report


@plugin("possible_error_same_interface")
def possible_error_same_interface(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_1038: possible errors and operations have the same interface owner."""
    report = PluginReport(checked=len(selected))
    for operation in selected:
        owner = index.nearest(operation, {"CLIENT-SERVER-INTERFACE"})
        if owner is None:
            report.incomplete(f"ClientServerOperation has no interface owner at {index.location(operation)}")
            continue
        for ref in index.descendants(operation, {"POSSIBLE-ERROR-REF"}):
            error = _resolve(index, ref, report, "possibleError reference")
            if error is not None and index.nearest(error, {"CLIENT-SERVER-INTERFACE"}) is not owner:
                report.fail(index, ref, "ApplicationError is not owned by the ClientServerInterface that owns the operation",
                            operation_interface=index.path_of(owner), error=index.path_of(error),
                            repair=_repair("repair_reference", "POSSIBLE-ERROR-REF", "Reference an ApplicationError owned by the same ClientServerInterface."))
    return report


@plugin("hardware_reference_targets_hw_type")
def hardware_reference_targets_hw_type(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_1144: hardwareElement and sensorActuator references target HwType."""
    report = PluginReport(checked=len(selected))
    for component in selected:
        refs = index.descendants(component, {"HARDWARE-ELEMENT-REF", "SENSOR-ACTUATOR-REF"})
        for ref in refs:
            target = _resolve(index, ref, report, local_name(ref.tag))
            if target is not None and local_name(target.tag) != "HW-TYPE":
                report.fail(index, ref, f"{local_name(ref.tag)} must resolve to HW-TYPE",
                            actual=local_name(target.tag),
                            repair=_repair("repair_reference", local_name(ref.tag), "Reference an HwType."))
    return report


@plugin("sw_pointer_target_category")
def sw_pointer_target_category(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_1177: pointer target category domain with the native void exception."""
    report = PluginReport(checked=len(selected))
    for props in selected:
        category_element = _first(props, {"TARGET-CATEGORY"})
        category = _text(category_element)
        valid = category in {"TYPE_REFERENCE", "FUNCTION_REFERENCE"}
        if category == "VALUE":
            base_ref = _first(props, {"BASE-TYPE-REF"})
            base = _resolve(index, base_ref, report, "SwPointerTargetProps base type reference")
            if base is None:
                continue
            valid = _text(_first(base, {"NATIVE-DECLARATION"})).strip().lower() == "void"
        if category and not valid:
            report.fail(index, category_element if category_element is not None else props, "SwPointerTargetProps has an unsupported targetCategory",
                        actual=category, allowed=["FUNCTION_REFERENCE", "TYPE_REFERENCE", "VALUE with native void base type"],
                        repair=_repair("replace_value", "TARGET-CATEGORY", "Use TYPE_REFERENCE, FUNCTION_REFERENCE, or the qualified VALUE/native-void exception."))
    return report


@plugin("event_runnable_waitpoint_restriction")
def event_runnable_waitpoint_restriction(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_1096/constr_1097: prohibited event references to waiting runnables."""
    report = PluginReport(checked=len(selected))
    constraint_id = rule["constraint_id"]
    for event in selected:
        if constraint_id == "constr_1097" and _first(event, {"DISABLED-MODE-IREF"}) is None:
            continue
        start_ref = _first(event, {"START-ON-EVENT-REF"})
        if start_ref is None:
            continue
        runnable = _resolve(index, start_ref, report, "startOnEvent reference")
        if runnable is not None and _first(runnable, {"WAIT-POINT"}) is not None:
            report.fail(index, start_ref, "Event references a RunnableEntity that has a WaitPoint",
                        runnable=index.path_of(runnable),
                        repair=_repair("repair_reference", "START-ON-EVENT-REF", "Reference a RunnableEntity without WaitPoints."))
    return report


@plugin("waitpoint_event_forbids_activation_reason")
def waitpoint_event_forbids_activation_reason(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_1228: a WaitPoint trigger event has no activationReasonRepresentation."""
    report = PluginReport(checked=len(selected))
    for waitpoint in selected:
        trigger_ref = _first(waitpoint, {"TRIGGER-REF"})
        event = _resolve(index, trigger_ref, report, "WaitPoint trigger reference")
        if event is not None:
            activation = _first(event, {"ACTIVATION-REASON-REPRESENTATION-REF"})
            if activation is not None:
                report.fail(index, activation, "RTEEvent used as a WaitPoint trigger references an activation reason",
                            event=index.path_of(event),
                            repair=_repair("remove", "ACTIVATION-REASON-REPRESENTATION-REF", "Remove the activation reason from the WaitPoint trigger event."))
    return report


@plugin("entity_addr_method_policy")
def entity_addr_method_policy(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_2034: executable entities forbid addrMethodShortNameAndAlignment."""
    report = PluginReport(checked=len(selected))
    for entity in selected:
        ref = _first(entity, {"SW-ADDR-METHOD-REF"})
        if ref is None:
            continue
        method = _resolve(index, ref, report, "SwAddrMethod reference")
        if method is not None and _text(_first(method, {"MEMORY-ALLOCATION-KEYWORD-POLICY"})) == "ADDR-METHOD-SHORT-NAME-AND-ALIGNMENT":
            report.fail(index, ref, "Executable entity references a forbidden SwAddrMethod keyword policy",
                        repair=_repair("repair_reference", "SW-ADDR-METHOD-REF", "Reference a SwAddrMethod with a different memoryAllocationKeywordPolicy."))
    return report


@plugin("mode_request_mapping_unique")
def mode_request_mapping_unique(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_4002: one mode group maps to one implementation type per set."""
    report = PluginReport(checked=len(selected))
    for mapping_set in selected:
        mapped: dict[int, tuple[etree._Element, etree._Element]] = {}
        for mapping in index.descendants(mapping_set, {"MODE-REQUEST-TYPE-MAP"}):
            group = _resolve(index, _first(mapping, {"MODE-GROUP-REF"}), report, "ModeRequestTypeMap modeGroup")
            impl = _resolve(index, _first(mapping, {"IMPLEMENTATION-DATA-TYPE-REF"}), report, "ModeRequestTypeMap implementationDataType")
            if group is None or impl is None:
                continue
            prior = mapped.get(id(group))
            if prior is not None and prior[1] is not impl:
                report.fail(index, mapping, "ModeDeclarationGroup is mapped to different ImplementationDataTypes in one DataTypeMappingSet",
                            mode_group=index.path_of(group), first_type=index.path_of(prior[1]), second_type=index.path_of(impl),
                            repair=_repair("repair_reference", "IMPLEMENTATION-DATA-TYPE-REF", "Use one implementation type for this mode group."))
            else:
                mapped[id(group)] = (mapping, impl)
    return report


@plugin("async_result_point_exactly_one")
def async_result_point_exactly_one(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_2006: each asynchronous call point has exactly one result point."""
    report = PluginReport(checked=len(selected))
    counts: dict[int, int] = defaultdict(int)
    for result in index.elements("ASYNCHRONOUS-SERVER-CALL-RESULT-POINT"):
        target = _resolve(index, _first(result, {"ASYNCHRONOUS-SERVER-CALL-POINT-REF"}), report, "asynchronous call point reference")
        if target is not None:
            counts[id(target)] += 1
    for call in selected:
        count = counts[id(call)]
        if count != 1:
            report.fail(index, call, "AsynchronousServerCallPoint must be referenced by exactly one result point",
                        actual=count, expected=1,
                        repair=_repair("set_reference_cardinality", "ASYNCHRONOUS-SERVER-CALL-POINT-REF", "Create or retain exactly one result-point reference.", expected=1))
    return report


@plugin("server_call_kind_exclusive")
def server_call_kind_exclusive(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_2022: one (R port, operation) pair uses one call style."""
    report = PluginReport(checked=len(selected))
    styles: dict[tuple[int, int], tuple[str, etree._Element]] = {}
    for point in selected:
        port = _resolve(index, _first(point, {"CONTEXT-R-PORT-REF"}), report, "server call RPort reference")
        operation = _resolve(index, _first(point, {"TARGET-REQUIRED-OPERATION-REF"}), report, "server call operation reference")
        if port is None or operation is None:
            continue
        style = "async" if local_name(point.tag) == "ASYNCHRONOUS-SERVER-CALL-POINT" else "sync"
        key = (id(port), id(operation))
        prior = styles.get(key)
        if prior is not None and prior[0] != style:
            report.fail(index, point, "RPortPrototype/ClientServerOperation pair is used by synchronous and asynchronous call points",
                        port=index.path_of(port), operation=index.path_of(operation),
                        repair=_repair("remove_conflicting_call_point", local_name(point.tag), "Use only one server-call style for this port/operation pair."))
        else:
            styles[key] = (style, point)
    return report


FORBIDDEN_CONNECTED_TYPES = {
    "constr_2010": "NV-BLOCK-SW-COMPONENT-TYPE",
    "constr_2016": "SERVICE-PROXY-SW-COMPONENT-TYPE",
}


@plugin("same_component_type_connection_forbidden")
def same_component_type_connection_forbidden(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_2010/constr_2016: connectors do not join two prohibited component kinds."""
    report = PluginReport(checked=len(selected))
    forbidden = FORBIDDEN_CONNECTED_TYPES[rule["constraint_id"]]
    for connector in selected:
        context_refs = index.descendants(connector, {"CONTEXT-COMPONENT-REF"})
        if len(context_refs) < 2:
            continue
        prototypes = [_resolve(index, ref, report, "connector context component") for ref in context_refs]
        if any(item is None for item in prototypes):
            continue
        types = []
        for prototype in prototypes:
            types.append(_resolve(index, _first(prototype, {"TYPE-TREF"}), report, "component prototype type"))
        if len(types) >= 2 and all(item is not None and local_name(item.tag) == forbidden for item in types):
            report.fail(index, connector, f"SwConnector connects two component prototypes typed by {forbidden}",
                        component_types=[index.path_of(item) for item in types if item is not None],
                        repair=_repair("remove_connector", local_name(connector.tag), f"Do not connect two {forbidden} instances."))
    return report


ACCESS_ROLES = {
    "constr_2002": ("DATA-READ-ACCESSS", {"R-PORT-PROTOTYPE", "PR-PORT-PROTOTYPE"}),
    "constr_2003": ("DATA-WRITE-ACCESSS", {"P-PORT-PROTOTYPE", "PR-PORT-PROTOTYPE"}),
    "constr_2004": ("DATA-SEND-POINTS", {"P-PORT-PROTOTYPE", "PR-PORT-PROTOTYPE"}),
    "constr_2005": ("DATA-RECEIVE-POINT-BY-ARGUMENTS", {"R-PORT-PROTOTYPE", "PR-PORT-PROTOTYPE"}),
}


@plugin("variable_access_port_domain")
def variable_access_port_domain(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_2002..2005: VariableAccess role determines port direction and interface kind."""
    report = PluginReport(checked=len(selected))
    container, allowed_ports = ACCESS_ROLES[rule["constraint_id"]]
    containers = {container}
    if rule["constraint_id"] == "constr_2005":
        containers.add("DATA-RECEIVE-POINT-BY-VALUES")
    for access in selected:
        if index.nearest(access, containers) is None:
            continue
        iref = _first(access, {"AUTOSAR-VARIABLE-IREF"})
        if iref is None:
            continue
        port_ref = _first(iref, {"CONTEXT-R-PORT-REF", "CONTEXT-P-PORT-REF", "CONTEXT-PORT-PROTOTYPE-REF", "PORT-PROTOTYPE-REF"})
        port = _resolve(index, port_ref, report, "AutosarVariableRef port prototype")
        if port is None:
            continue
        interface = _interface_of_port(index, port, report)
        if local_name(port.tag) not in allowed_ports or (interface is not None and local_name(interface.tag) not in DATA_INTERFACE_TAGS):
            report.fail(index, port_ref if port_ref is not None else access, "VariableAccess uses an incompatible port direction or interface",
                        actual={"port": local_name(port.tag), "interface": local_name(interface.tag) if interface is not None else None},
                        allowed={"ports": sorted(allowed_ports), "interfaces": sorted(DATA_INTERFACE_TAGS)},
                        repair=_repair("repair_reference", local_name(port_ref.tag) if port_ref is not None else "PORT-PROTOTYPE-REF", "Reference a port with the required direction and a SenderReceiverInterface or NvDataInterface."))
    return report


@plugin("data_read_access_policy")
def data_read_access_policy(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_1018: dataReadAccess does not target measurementPoint data."""
    report = PluginReport(checked=len(selected))
    for access in selected:
        if index.nearest(access, {"DATA-READ-ACCESSS"}) is None:
            continue
        data = _referenced_data(index, access, report)
        if data is not None and _impl_policy(data) == "MEASUREMENT-POINT":
            report.fail(index, access, "dataReadAccess references a measurementPoint VariableDataPrototype",
                        data=index.path_of(data),
                        repair=_repair("repair_reference", "ACCESSED-VARIABLE", "Reference data whose swImplPolicy is not measurementPoint."))
    return report


@plugin("service_dependency_service_port")
def service_dependency_service_port(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_2027: assigned ports are service ports, except NvM roles."""
    report = PluginReport(checked=len(selected))
    for dependency in selected:
        owner = index.nearest(dependency, COMPONENT_TAGS)
        for assignment in index.descendants(dependency, {"ROLE-BASED-PORT-ASSIGNMENT"}):
            role = _text(_first(assignment, {"ROLE"}))
            nvm_exception = (owner is not None and local_name(owner.tag) == "NV-BLOCK-SW-COMPONENT-TYPE") or role.upper().startswith("NVM")
            if nvm_exception:
                continue
            port_ref = _first(assignment, {"PORT-PROTOTYPE-REF", "ASSIGNED-PORT-REF"})
            port = _resolve(index, port_ref, report, "assigned PortPrototype reference")
            if port is None:
                continue
            interface = _interface_of_port(index, port, report)
            if interface is not None and _text(_first(interface, {"IS-SERVICE"})).lower() not in {"true", "1"}:
                report.fail(index, port_ref if port_ref is not None else assignment, "SwcServiceDependency assignedPort is not typed by a service PortInterface",
                            role=role, interface=index.path_of(interface),
                            repair=_repair("repair_reference", local_name(port_ref.tag) if port_ref is not None else "PORT-PROTOTYPE-REF", "Reference a port typed by an interface with IS-SERVICE=true."))
    return report


@plugin("rpt_hook_reference_or_code_label")
def rpt_hook_reference_or_code_label(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """TPS_SWCT_02047: an RptHook without an AR hook iref has a code label."""
    report = PluginReport(checked=len(selected))
    for hook in selected:
        if _first(hook, {"RPT-AR-HOOK-IREF"}) is None and not _text(_first(hook, {"CODE-LABEL"})):
            report.fail(index, hook, "RptHook defines neither rptArHookIref nor codeLabel",
                        repair=_repair("add_element", "CODE-LABEL", "Provide CODE-LABEL when RPT-AR-HOOK-IREF is absent."))
    return report


@plugin("runnable_argument_requires_operation_event")
def runnable_argument_requires_operation_event(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_1165: RunnableEntityArgument is used only by operation-triggered runnables."""
    report = PluginReport(checked=len(selected))
    triggered: set[int] = set()
    for event in index.elements("OPERATION-INVOKED-EVENT"):
        runnable = _resolve(index, _first(event, {"START-ON-EVENT-REF"}), report, "OperationInvokedEvent startOnEvent")
        if runnable is not None:
            triggered.add(id(runnable))
    for runnable in selected:
        if _first(runnable, {"RUNNABLE-ENTITY-ARGUMENT"}) is not None and id(runnable) not in triggered:
            report.fail(index, runnable, "RunnableEntity has RunnableEntityArguments but is not triggered by a ClientServerOperation",
                        repair=_repair("add_operation_event", "OPERATION-INVOKED-EVENT", "Add an OperationInvokedEvent or remove RunnableEntityArguments."))
    return report


IREF_RULES = {
    "TPS_SWCT_01374": ("AUTOSAR-PARAMETER-IREF", "ROOT-PARAMETER-DATA-PROTOTYPE-REF", "TARGET-DATA-PROTOTYPE-REF"),
    "TPS_SWCT_01375": ("AUTOSAR-VARIABLE-IREF", "ROOT-VARIABLE-DATA-PROTOTYPE-REF", "TARGET-DATA-PROTOTYPE-REF"),
}


def _is_composite_type(data_type: etree._Element) -> bool:
    tag = local_name(data_type.tag)
    if tag in {"APPLICATION-ARRAY-DATA-TYPE", "APPLICATION-RECORD-DATA-TYPE"}:
        return True
    if tag == "APPLICATION-PRIMITIVE-DATA-TYPE":
        return False
    return _text(_first(data_type, {"CATEGORY"})) in {"ARRAY", "STRUCTURE", "UNION"}


@plugin("autosar_iref_composite_root")
def autosar_iref_composite_root(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """TPS_SWCT_01374/01375: root prototype reference exists iff target data is composite."""
    report = PluginReport(checked=len(selected))
    iref_tag, root_tag, target_tag = IREF_RULES[rule["constraint_id"]]
    for wrapper in selected:
        iref = _first(wrapper, {iref_tag})
        if iref is None:
            continue
        target_ref = _first(iref, {target_tag})
        target = _resolve(index, target_ref, report, target_tag)
        if target is None:
            continue
        type_ref = _first(target, {"TYPE-TREF"})
        data_type = _resolve(index, type_ref, report, "DataPrototype type reference")
        if data_type is None:
            continue
        composite = _is_composite_type(data_type)
        has_root = _first(iref, {root_tag}) is not None
        if composite != has_root:
            report.fail(index, iref, f"{root_tag} existence does not match the target AutosarDataType shape",
                        composite_type=composite, root_reference_present=has_root,
                        repair=_repair("set_conditional_existence", root_tag, f"{'Add' if composite else 'Remove'} {root_tag}.", expected=composite))
    return report


def _final_impl_type(index: ArxmlIndex, data_type: etree._Element, report: PluginReport):
    seen: set[int] = set()
    current = data_type
    while local_name(current.tag) == "IMPLEMENTATION-DATA-TYPE" and _text(_first(current, {"CATEGORY"})) == "TYPE_REFERENCE":
        if id(current) in seen:
            report.incomplete(f"ImplementationDataType TYPE_REFERENCE cycle at {index.location(current)}")
            return None
        seen.add(id(current))
        current = _resolve(index, _first(current, {"IMPLEMENTATION-DATA-TYPE-REF"}), report, "ImplementationDataType reference")
        if current is None:
            return None
    return current


@plugin("type_reference_props_require_value")
def type_reference_props_require_value(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_1383: TYPE_REFERENCE with local compu/data constraints ends in VALUE."""
    report = PluginReport(checked=len(selected))
    for data_type in selected:
        if _text(_first(data_type, {"CATEGORY"})) != "TYPE_REFERENCE":
            continue
        if _first(data_type, {"COMPU-METHOD-REF", "DATA-CONSTR-REF"}) is None:
            continue
        final = _final_impl_type(index, data_type, report)
        category = _text(_first(final, {"CATEGORY"})) if final is not None else ""
        if final is not None and category != "VALUE":
            report.fail(index, data_type, "TYPE_REFERENCE with compuMethod/dataConstr does not resolve to a VALUE type",
                        resolved_category=category,
                        repair=_repair("repair_reference", "IMPLEMENTATION-DATA-TYPE-REF", "Reference a chain ending in a VALUE ImplementationDataType."))
    return report


@plugin("data_receive_event_policy")
def data_receive_event_policy(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """TPS_SWCT_01340/constr_2021: receive event policy matches error/wait semantics."""
    report = PluginReport(checked=len(selected))
    for subject in selected:
        event = subject
        expected = "not QUEUED"
        if rule["constraint_id"] == "constr_2021":
            event = _resolve(index, _first(subject, {"TRIGGER-REF"}), report, "WaitPoint trigger")
            if event is None:
                continue
            if local_name(event.tag) != "DATA-RECEIVED-EVENT":
                continue
            expected = "QUEUED"
        data = _referenced_data(index, event, report)
        if data is None:
            continue
        policy = _impl_policy(data)
        valid = policy == "QUEUED" if expected == "QUEUED" else policy != "QUEUED"
        if not valid:
            report.fail(index, subject, f"{local_name(subject.tag)} requires data swImplPolicy {expected}",
                        actual=policy, data=index.path_of(data),
                        repair=_repair("repair_reference", "DATA-IREF", f"Reference data with swImplPolicy {expected}."))
    return report
