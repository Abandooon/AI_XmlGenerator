"""Qualified AUTOSAR reference-integrity validators."""

from __future__ import annotations

from lxml import etree

from .arxml_index import ArxmlIndex, local_name
from .plugins import INTERFACE_REF_TAGS, PluginReport, plugin

LOCAL_ACCESS_CONTAINERS = {"READ-LOCAL-VARIABLES", "WRITTEN-LOCAL-VARIABLES"}
INTER_RUNNABLE_CONTAINERS = {
    "EXPLICIT-INTER-RUNNABLE-VARIABLES", "IMPLICIT-INTER-RUNNABLE-VARIABLES",
}
APP_COMPOSITE_ELEMENTS = {"APPLICATION-ARRAY-ELEMENT", "APPLICATION-RECORD-ELEMENT"}


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
    return _resolve(index, _first(port, INTERFACE_REF_TAGS), report, "PortPrototype interface")


@plugin("local_variable_access_reference")
def local_variable_access_reference(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """TPS_SWCT_01053/01521 and constr_2026: local accesses resolve within the same behavior role."""
    report = PluginReport(checked=len(selected))
    for access in selected:
        if index.nearest(access, LOCAL_ACCESS_CONTAINERS) is None:
            continue
        local_ref = _first(access, {"LOCAL-VARIABLE-REF"})
        if local_ref is None:
            report.fail(index, access, "Local VariableAccess does not use AutosarVariableRef.localVariable",
                        repair=_repair("add_reference", "LOCAL-VARIABLE-REF", "Reference the inter-runnable VariableDataPrototype through localVariable."))
            continue
        target = _resolve(index, local_ref, report, "localVariable reference")
        if target is None:
            continue
        if local_name(target.tag) != "VARIABLE-DATA-PROTOTYPE":
            report.fail(index, local_ref, "localVariable does not resolve to VariableDataPrototype",
                        actual=local_name(target.tag),
                        repair=_repair("repair_reference", "LOCAL-VARIABLE-REF", "Reference an inter-runnable VariableDataPrototype."))
            continue
        if rule["constraint_id"] != "constr_2026":
            continue
        source_behavior = index.nearest(access, {"SWC-INTERNAL-BEHAVIOR"})
        target_behavior = index.nearest(target, {"SWC-INTERNAL-BEHAVIOR"})
        role = index.nearest(target, INTER_RUNNABLE_CONTAINERS)
        if source_behavior is None or target_behavior is None:
            report.incomplete(f"local variable ownership is missing at {index.location(local_ref)}")
        elif source_behavior is not target_behavior or role is None:
            report.fail(index, local_ref, "localVariable target is not an explicit/implicit inter-runnable variable of the same SwcInternalBehavior",
                        source_behavior=index.path_of(source_behavior),
                        target_behavior=index.path_of(target_behavior),
                        target_role=local_name(role.tag) if role is not None else None,
                        repair=_repair("repair_reference", "LOCAL-VARIABLE-REF", "Reference an inter-runnable variable owned by the runnable's SwcInternalBehavior."))
    return report


def _concrete_service_needs(dependency: etree._Element) -> list[etree._Element]:
    result = []
    for item in dependency.iterdescendants():
        tag = local_name(item.tag)
        if tag.endswith("-NEEDS") and tag not in {"SERVICE-NEEDS", "SERVICE-DEPENDENCYS"}:
            result.append(item)
    return result


@plugin("standard_service_dependency_chain")
def standard_service_dependency_chain(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """TPS_SWCT_01400: assigned standardized interfaces are service-marked and backed by ServiceNeeds."""
    report = PluginReport(checked=len(selected))
    for dependency in selected:
        assignments = index.descendants(dependency, {"ROLE-BASED-PORT-ASSIGNMENT"})
        if not assignments:
            continue
        if not _concrete_service_needs(dependency):
            report.fail(index, dependency, "SwcServiceDependency assigns service ports but has no concrete ServiceNeeds",
                        repair=_repair("add_element", "SERVICE-NEEDS", "Add the standardized ServiceNeeds for this dependency."))
        for assignment in assignments:
            port = _resolve(index, _first(assignment, {"PORT-PROTOTYPE-REF", "ASSIGNED-PORT-REF"}), report, "assigned service port")
            interface = _interface(index, port, report) if port is not None else None
            if interface is not None and _text(_first(interface, {"IS-SERVICE"})).lower() not in {"true", "1"}:
                report.fail(index, assignment, "Assigned standardized service PortInterface does not set IS-SERVICE=true",
                            interface=index.path_of(interface),
                            repair=_repair("replace_value", "IS-SERVICE", "Set IS-SERVICE to true on the standardized PortInterface.", expected="true"))
    return report


def _owned_modes(index: ArxmlIndex, group: etree._Element) -> list[etree._Element]:
    modes = []
    for mode in index.descendants(group, {"MODE-DECLARATION"}):
        if index.nearest(index.parent.get(mode), {"MODE-DECLARATION-GROUP"}) is group:
            modes.append(mode)
    return modes


@plugin("mode_entered_transition_coverage")
def mode_entered_transition_coverage(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_1193: every non-initial mode is entered when transitions exist."""
    report = PluginReport(checked=len(selected))
    for group in selected:
        transitions = index.descendants(group, {"MODE-TRANSITION"})
        if not transitions:
            continue
        initial = _resolve(index, _first(group, {"INITIAL-MODE-REF"}), report, "initialMode reference")
        entered: set[int] = set()
        for transition in transitions:
            target = _resolve(index, _first(transition, {"ENTERED-MODE-REF"}), report, "enteredMode reference")
            if target is not None:
                entered.add(id(target))
        for mode in _owned_modes(index, group):
            if mode is not initial and id(mode) not in entered:
                report.fail(index, mode, "ModeDeclaration is never referenced as enteredMode",
                            repair=_repair("add_transition_reference", "ENTERED-MODE-REF", "Add a ModeTransition entering this non-initial mode."))
    return report


@plugin("port_api_option_provided_cs")
def port_api_option_provided_cs(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_1386: PortDefinedArgumentValue is only used for provided ClientServer ports."""
    report = PluginReport(checked=len(selected))
    for option in selected:
        if _first(option, {"PORT-DEFINED-ARGUMENT-VALUE"}) is None:
            continue
        ref = _first(option, {"PORT-REF"})
        port = _resolve(index, ref, report, "PortAPIOption port")
        if port is None:
            continue
        interface = _interface(index, port, report)
        valid = local_name(port.tag) in {"P-PORT-PROTOTYPE", "PR-PORT-PROTOTYPE"}
        valid = valid and interface is not None and local_name(interface.tag) == "CLIENT-SERVER-INTERFACE"
        if not valid:
            report.fail(index, ref if ref is not None else option,
                        "PortDefinedArgumentValue requires an abstract provided port typed by ClientServerInterface",
                        actual={"port": local_name(port.tag), "interface": local_name(interface.tag) if interface is not None else None},
                        repair=_repair("repair_reference", "PORT-REF", "Reference a P or PR port typed by ClientServerInterface."))
    return report


@plugin("diagnostic_io_current_value_reference")
def diagnostic_io_current_value_reference(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """TPS_SWCT_01655: exact DiagnosticIoControlNeeds target references current DiagnosticValueNeeds."""
    report = PluginReport(checked=len(selected))
    for needs in selected:
        ref = _first(needs, {"CURRENT-VALUE-REF"})
        target = _resolve(index, ref, report, "DiagnosticIoControlNeeds currentValue")
        if target is not None and local_name(target.tag) != "DIAGNOSTIC-VALUE-NEEDS":
            report.fail(index, ref if ref is not None else needs, "CURRENT-VALUE-REF does not reference DiagnosticValueNeeds",
                        actual=local_name(target.tag),
                        repair=_repair("repair_reference", "CURRENT-VALUE-REF", "Reference the DiagnosticValueNeeds for current-value access."))
    return report


@plugin("diag_debounce_assignment")
def diag_debounce_assignment(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_1139: internal debounce dependency assigns the standardized role to an R port."""
    report = PluginReport(checked=len(selected))
    for dependency in selected:
        if _first(dependency, {"DIAG-EVENT-DEBOUNCE-MONITOR-INTERNAL"}) is None:
            continue
        matched = False
        for assignment in index.descendants(dependency, {"ROLE-BASED-PORT-ASSIGNMENT"}):
            role = _text(_first(assignment, {"ROLE"}))
            if role != "DiagFaultDetectionCounterPort":
                continue
            matched = True
            port = _resolve(index, _first(assignment, {"PORT-PROTOTYPE-REF", "ASSIGNED-PORT-REF"}), report, "debounce assignedPort")
            if port is not None and local_name(port.tag) != "R-PORT-PROTOTYPE":
                report.fail(index, assignment, "DiagFaultDetectionCounterPort role does not reference RPortPrototype",
                            actual=local_name(port.tag),
                            repair=_repair("repair_reference", "PORT-PROTOTYPE-REF", "Reference an RPortPrototype."))
        if not matched:
            report.fail(index, dependency, "DiagEventDebounceMonitorInternal lacks DiagFaultDetectionCounterPort assignment",
                        repair=_repair("add_role_assignment", "ROLE-BASED-PORT-ASSIGNMENT", "Add role DiagFaultDetectionCounterPort referencing an R port."))
    return report


@plugin("composite_iref_root_matches_base")
def composite_iref_root_matches_base(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_1184: rootDataPrototype kind and owner match the base DataInterface."""
    report = PluginReport(checked=len(selected))
    for iref in selected:
        base = _resolve(index, _first(iref, {"BASE-REF"}), report, "ApplicationCompositeElement iref base")
        root = _resolve(index, _first(iref, {"ROOT-DATA-PROTOTYPE-REF"}), report, "ApplicationCompositeElement iref rootDataPrototype")
        if base is None or root is None:
            continue
        expected = "PARAMETER-DATA-PROTOTYPE" if local_name(base.tag) == "PARAMETER-INTERFACE" else "VARIABLE-DATA-PROTOTYPE"
        owner = index.nearest(root, {"PARAMETER-INTERFACE", "SENDER-RECEIVER-INTERFACE", "NV-DATA-INTERFACE"})
        if owner is not base or local_name(root.tag) != expected:
            report.fail(index, iref, "rootDataPrototype kind/owner is inconsistent with the base DataInterface",
                        base=index.path_of(base), root=index.path_of(root), expected_root_tag=expected,
                        repair=_repair("repair_reference", "ROOT-DATA-PROTOTYPE-REF", "Reference a root prototype owned by the base interface with the required kind."))
    return report


@plugin("async_returns_same_runnable")
def async_returns_same_runnable(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_2030: WaitPoint and result point connected by returns event share a RunnableEntity."""
    report = PluginReport(checked=len(selected))
    waits_by_event: dict[int, list[etree._Element]] = {}
    for waitpoint in index.elements("WAIT-POINT"):
        event = _resolve(index, _first(waitpoint, {"TRIGGER-REF"}), report, "WaitPoint trigger")
        if event is not None:
            waits_by_event.setdefault(id(event), []).append(waitpoint)
    for event in selected:
        waits = waits_by_event.get(id(event), [])
        if not waits:
            continue
        result_point = _resolve(index, _first(event, {"EVENT-SOURCE-REF"}), report, "AsynchronousServerCallReturnsEvent eventSource")
        if result_point is None:
            continue
        result_runnable = index.nearest(result_point, {"RUNNABLE-ENTITY"})
        if result_runnable is None:
            report.incomplete(f"result point has no RunnableEntity owner at {index.location(result_point)}")
            continue
        for waitpoint in waits:
            wait_runnable = index.nearest(waitpoint, {"RUNNABLE-ENTITY"})
            if wait_runnable is None:
                report.incomplete(f"WaitPoint has no RunnableEntity owner at {index.location(waitpoint)}")
            elif wait_runnable is not result_runnable:
                report.fail(index, waitpoint, "WaitPoint and AsynchronousServerCallResultPoint belong to different RunnableEntities",
                            wait_runnable=index.path_of(wait_runnable), result_runnable=index.path_of(result_runnable),
                            repair=_repair("move_or_retarget", "WAIT-POINT", "Aggregate the WaitPoint and result point in the same RunnableEntity."))
    return report


def _reachable_application_elements(index: ArxmlIndex, root: etree._Element, report: PluginReport) -> set[int]:
    reachable: set[int] = set()
    seen_types: set[int] = set()
    type_ref = _first(root, {"TYPE-TREF"})
    first_type = _resolve(index, type_ref, report, "root DataPrototype type")
    stack = [first_type] if first_type is not None else []
    while stack:
        data_type = stack.pop()
        if id(data_type) in seen_types:
            continue
        seen_types.add(id(data_type))
        for element in index.descendants(data_type, APP_COMPOSITE_ELEMENTS):
            if index.nearest(index.parent.get(element), {"APPLICATION-ARRAY-DATA-TYPE", "APPLICATION-RECORD-DATA-TYPE"}) is not data_type:
                continue
            reachable.add(id(element))
            nested = _resolve(index, _first(element, {"TYPE-TREF"}), report, "ApplicationCompositeElement type")
            if nested is not None:
                stack.append(nested)
    return reachable


IREF_TARGET_RULES = {
    "constr_2535": ("AUTOSAR-PARAMETER-IREF", "PARAMETER-DATA-PROTOTYPE", "ROOT-PARAMETER-DATA-PROTOTYPE-REF"),
    "constr_2536": ("AUTOSAR-VARIABLE-IREF", "VARIABLE-DATA-PROTOTYPE", "ROOT-VARIABLE-DATA-PROTOTYPE-REF"),
}


@plugin("autosar_iref_target_domain")
def autosar_iref_target_domain(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_2535/2536: iref target is the correct root prototype or a nested composite element."""
    report = PluginReport(checked=len(selected))
    iref_tag, root_tag, root_ref_tag = IREF_TARGET_RULES[rule["constraint_id"]]
    for wrapper in selected:
        iref = _first(wrapper, {iref_tag})
        if iref is None:
            continue
        target_ref = _first(iref, {"TARGET-DATA-PROTOTYPE-REF"})
        target = _resolve(index, target_ref, report, "Autosar iref targetDataPrototype")
        if target is None:
            continue
        if local_name(target.tag) == root_tag:
            continue
        root = _resolve(index, _first(iref, {root_ref_tag}), report, root_ref_tag)
        valid = root is not None and local_name(root.tag) == root_tag and id(target) in _reachable_application_elements(index, root, report)
        if not valid:
            report.fail(index, target_ref if target_ref is not None else iref,
                        "Autosar iref target is neither the required DataPrototype nor a nested composite element",
                        actual=local_name(target.tag), required_root=root_tag,
                        repair=_repair("repair_reference", "TARGET-DATA-PROTOTYPE-REF", f"Reference a {root_tag} or an element reachable from its application data type."))
    return report


@plugin("rpt_scenario_system_partition")
def rpt_scenario_system_partition(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_2056: RPT algorithm and hook instances belong to the two declared systems."""
    report = PluginReport(checked=len(selected))
    for scenario in selected:
        rpt_system = _resolve(index, _first(scenario, {"RPT-SYSTEM-REF"}), report, "rptSystem")
        host_system = _resolve(index, _first(scenario, {"HOST-SYSTEM-REF"}), report, "hostSystem")
        if rpt_system is None or host_system is None:
            continue
        if rpt_system is host_system:
            report.fail(index, scenario, "rptSystem and hostSystem must be two different System instances",
                        repair=_repair("repair_reference", "RPT-SYSTEM-REF", "Reference the distinct rapid-prototyping algorithm System."))
        for hook in index.descendants(scenario, {"RPT-HOOK"}):
            iref = _first(hook, {"RPT-AR-HOOK-IREF"})
            if iref is None:
                continue
            refs = [item for item in iref.iterdescendants() if local_name(item.tag).endswith("-REF") and _text(item)]
            if not refs:
                report.incomplete(f"RPT-AR-HOOK-IREF has no target reference at {index.location(iref)}")
                continue
            target = _resolve(index, refs[-1], report, "rptArHook target")
            target_system = index.nearest(target, {"SYSTEM"}) if target is not None else None
            if target is not None and target_system is None:
                report.incomplete(f"rptArHook target has no System owner at {index.location(target)}")
            elif target_system is not host_system:
                report.fail(index, iref, "rptArHook target is not owned by the host System",
                            expected_system=index.path_of(host_system),
                            actual_system=index.path_of(target_system) if target_system is not None else None,
                            repair=_repair("repair_reference", local_name(refs[-1].tag), "Reference an instance in the host System."))
    return report
