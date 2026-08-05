"""Intent-gated naming rules whose applicability is not inferable from ARXML alone."""

from __future__ import annotations

from lxml import etree

from .arxml_index import ArxmlIndex, local_name
from .plugins import INTERFACE_REF_TAGS, PluginReport, plugin

INTERFACE_NAME_RULES = {
    "TPS_SWCT_01544": {"RoutingActivation": None},
    "TPS_SWCT_01627": {"SecurityAccess": "SecurityAccess"},
    "TPS_SWCT_01628": {"DataServices": "DataServices"},
    "TPS_SWCT_01629": {"DataServices": "DataServices"},
    "TPS_SWCT_01630": {"DataServices": "DataServices"},
    "TPS_SWCT_01631": {"InfotypeServices": "InfotypeServices"},
    "TPS_SWCT_01632": {"RoutineServices": "RoutineServices"},
    "TPS_SWCT_01633": {"RequestControlServices": "RequestControlServices"},
    "TPS_SWCT_01634": {"DataServices": "DataServices"},
    "TPS_SWCT_01640": {"DataServices_DIDRange": "DataServices_DIDRange"},
    "TPS_SWCT_01656": {
        "IOControlRequest": "IOControlRequest",
        "IOControlResponse": "IOControlResponse",
    },
}

PORT_NAME_RULES = {
    "TPS_SWCT_01657": ("IOControlRequest", "R-PORT-PROTOTYPE", "IOControlRequest"),
    "TPS_SWCT_01658": ("IOControlResponse", "P-PORT-PROTOTYPE", "IOControlResponse"),
}


def _text(element: etree._Element | None) -> str:
    return (element.text or "").strip() if element is not None else ""


def _first(element: etree._Element, tags: set[str]) -> etree._Element | None:
    return next((item for item in element.iterdescendants() if local_name(item.tag) in tags), None)


def _short_name(element: etree._Element) -> tuple[str, etree._Element | None]:
    child = next((item for item in element if local_name(item.tag) == "SHORT-NAME"), None)
    return _text(child), child


def _resolve(index: ArxmlIndex, ref: etree._Element | None, report: PluginReport, label: str):
    if ref is None:
        report.incomplete(f"missing {label}")
        return None
    resolution = index.resolve(ref)
    if resolution.status != "resolved" or resolution.element is None:
        report.incomplete(f"{resolution.status} {label} {resolution.reference} at {index.location(ref)}")
        return None
    return resolution.element


def _assignment_port(index: ArxmlIndex, assignment: etree._Element, report: PluginReport):
    ref = _first(assignment, {"PORT-PROTOTYPE-REF", "ASSIGNED-PORT-REF"})
    return _resolve(index, ref, report, "RoleBasedPortAssignment assigned port")


def _interface(index: ArxmlIndex, port: etree._Element, report: PluginReport):
    return _resolve(index, _first(port, INTERFACE_REF_TAGS), report, "assigned port interface")


def _repair(expected: str) -> dict:
    return {
        "action": "rename_identifiable_and_references",
        "target": "SHORT-NAME",
        "instruction": f"Rename the element to {expected!r} and update every reference to it.",
        "expected": expected,
    }


@plugin("service_dependency_interface_name")
def service_dependency_interface_name(
    index: ArxmlIndex, rule: dict, selected: list[etree._Element]
) -> PluginReport:
    """TPS_SWCT_01544/01627..01656: interface name is derived from exact use-case target."""
    report = PluginReport(checked=len(selected))
    role_prefixes = INTERFACE_NAME_RULES[rule["constraint_id"]]
    for dependency in selected:
        dependency_name, _ = _short_name(dependency)
        if not dependency_name:
            report.incomplete(f"SwcServiceDependency lacks SHORT-NAME at {index.location(dependency)}")
            continue
        matched: set[str] = set()
        for assignment in index.descendants(dependency, {"ROLE-BASED-PORT-ASSIGNMENT"}):
            role = _text(_first(assignment, {"ROLE"}))
            if role not in role_prefixes:
                continue
            matched.add(role)
            port = _assignment_port(index, assignment, report)
            interface = _interface(index, port, report) if port is not None else None
            if interface is None:
                continue
            actual, name_element = _short_name(interface)
            prefix = role_prefixes[role]
            expected = f"{prefix}_{dependency_name}" if prefix is not None else None
            valid = actual == expected if expected is not None else actual.startswith(dependency_name + "_")
            if not valid:
                description = expected or f"a name beginning with {dependency_name}_"
                report.fail(index, name_element if name_element is not None else interface,
                            "PortInterface name does not follow the SwcServiceDependency naming rule",
                            role=role, actual=actual, expected=description,
                            repair=_repair(expected or f"{dependency_name}_<routing-activation-suffix>"))
        missing = sorted(set(role_prefixes) - matched)
        if missing:
            report.incomplete(
                f"Exact target {index.path_of(dependency)} has no assignment for naming role(s): {', '.join(missing)}"
            )
    return report


@plugin("service_dependency_port_name")
def service_dependency_port_name(
    index: ArxmlIndex, rule: dict, selected: list[etree._Element]
) -> PluginReport:
    """TPS_SWCT_01657/01658: assigned port name is role prefix plus dependency name."""
    report = PluginReport(checked=len(selected))
    role, expected_tag, prefix = PORT_NAME_RULES[rule["constraint_id"]]
    for dependency in selected:
        dependency_name, _ = _short_name(dependency)
        matched = False
        for assignment in index.descendants(dependency, {"ROLE-BASED-PORT-ASSIGNMENT"}):
            if _text(_first(assignment, {"ROLE"})) != role:
                continue
            matched = True
            port = _assignment_port(index, assignment, report)
            if port is None:
                continue
            actual, name_element = _short_name(port)
            expected = f"{prefix}_{dependency_name}"
            if local_name(port.tag) != expected_tag or actual != expected:
                report.fail(index, name_element if name_element is not None else port,
                            "RoleBasedPortAssignment port kind or name violates the naming rule",
                            role=role, actual={"tag": local_name(port.tag), "name": actual},
                            expected={"tag": expected_tag, "name": expected}, repair=_repair(expected))
        if not matched:
            report.incomplete(f"Exact target {index.path_of(dependency)} has no assignment with role {role}")
    return report
