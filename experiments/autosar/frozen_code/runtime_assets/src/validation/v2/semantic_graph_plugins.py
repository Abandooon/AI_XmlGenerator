"""Reusable resolved-graph validators for AUTOSAR type and context rules."""

from __future__ import annotations

from lxml import etree

from .arxml_index import ArxmlIndex, local_name
from .plugins import COMPONENT_TAGS, INTERFACE_REF_TAGS, PORT_TAGS, PluginReport, plugin


def _text(element: etree._Element | None) -> str:
    return (element.text or "").strip() if element is not None else ""


def _first(element: etree._Element, tags: set[str]) -> etree._Element | None:
    return next((item for item in element.iterdescendants()
                 if local_name(item.tag) in tags), None)


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


def _port_interface(index: ArxmlIndex, port: etree._Element, report: PluginReport):
    ref = _first(port, INTERFACE_REF_TAGS)
    if ref is None:
        report.incomplete(f"port interface reference is missing at {index.location(port)}")
        return None
    return _resolve(index, ref, report)


ANNOTATION_RULES = {
    "constr_4004": {"interface": "SENDER-RECEIVER-INTERFACE"},
    "constr_4005": {"interface": "CLIENT-SERVER-INTERFACE"},
    "constr_4006": {"port": "P-PORT-PROTOTYPE", "owner": "PARAMETER-SW-COMPONENT-TYPE"},
    "constr_4007": {"interface": "MODE-SWITCH-INTERFACE"},
    "constr_4008": {"interface": "TRIGGER-INTERFACE"},
    "constr_4009": {"interface": "NV-DATA-INTERFACE"},
    "constr_4010": {"owner": "COMPOSITION-SW-COMPONENT-TYPE"},
}


@plugin("port_annotation_context")
def port_annotation_context(
    index: ArxmlIndex, rule: dict, selected: list[etree._Element]
) -> PluginReport:
    """constr_4004..4010: annotation aggregation and port typing context."""
    report = PluginReport(checked=len(selected))
    expected = ANNOTATION_RULES[rule["constraint_id"]]
    for annotation in selected:
        port = index.nearest(annotation, PORT_TAGS)
        if port is None:
            report.fail(
                index, annotation, "Port annotation is not aggregated by a PortPrototype",
                repair=_repair("move_element", local_name(annotation.tag), "Aggregate the annotation below the required PortPrototype."),
            )
            continue
        expected_port = expected.get("port")
        if expected_port and local_name(port.tag) != expected_port:
            report.fail(index, annotation, f"Annotation requires {expected_port}", actual=local_name(port.tag))
        expected_owner = expected.get("owner")
        if expected_owner:
            owner = index.nearest(port, COMPONENT_TAGS)
            if owner is None:
                report.incomplete(f"annotated port has no component owner at {index.location(port)}")
            elif local_name(owner.tag) != expected_owner:
                report.fail(index, annotation, f"Annotation requires owner {expected_owner}", actual=local_name(owner.tag))
        expected_interface = expected.get("interface")
        if expected_interface:
            interface = _port_interface(index, port, report)
            if interface is not None and local_name(interface.tag) != expected_interface:
                report.fail(
                    index, annotation, f"Annotation requires a port typed by {expected_interface}",
                    actual=local_name(interface.tag),
                    repair=_repair("repair_reference", "INTERFACE-TREF", f"Reference a {expected_interface}."),
                )
    return report


COMSPEC_QUEUED = {
    "constr_1129": False,
    "constr_1130": True,
    "constr_1131": False,
    "constr_1132": True,
}


def _referenced_data_element(index: ArxmlIndex, subject: etree._Element, report: PluginReport):
    ref = next((item for item in subject.iterdescendants()
                if local_name(item.tag).endswith("DATA-ELEMENT-REF")), None)
    if ref is None:
        report.incomplete(f"data-element reference is missing at {index.location(subject)}")
        return None
    return _resolve(index, ref, report)


def _impl_policy(element: etree._Element) -> str:
    return _text(_first(element, {"SW-IMPL-POLICY"})) or "STANDARD"


@plugin("comspec_sw_impl_policy")
def comspec_sw_impl_policy(
    index: ArxmlIndex, rule: dict, selected: list[etree._Element]
) -> PluginReport:
    """constr_1129..1132: queued/nonqueued ComSpec agrees with data policy."""
    report = PluginReport(checked=len(selected))
    expect_queued = COMSPEC_QUEUED[rule["constraint_id"]]
    for comspec in selected:
        data_element = _referenced_data_element(index, comspec, report)
        if data_element is None:
            continue
        policy = _impl_policy(data_element)
        valid = policy == "QUEUED" if expect_queued else policy != "QUEUED"
        if not valid:
            report.fail(
                index, comspec, "ComSpec queue kind is incompatible with dataElement.swImplPolicy",
                expected="QUEUED" if expect_queued else "not QUEUED", actual=policy,
                data_element=index.path_of(data_element),
                repair=_repair("replace_value", "SW-IMPL-POLICY", "Align swImplPolicy with the queued/nonqueued ComSpec kind."),
            )
    return report


@plugin("invalidation_requires_nonqueued")
def invalidation_requires_nonqueued(
    index: ArxmlIndex, rule: dict, selected: list[etree._Element]
) -> PluginReport:
    """constr_1219: an invalidation policy cannot address queued data."""
    report = PluginReport(checked=len(selected))
    for policy_element in selected:
        data_element = _referenced_data_element(index, policy_element, report)
        if data_element is not None and _impl_policy(data_element) == "QUEUED":
            report.fail(index, policy_element, "Invalidation is not supported for QUEUED dataElements",
                        data_element=index.path_of(data_element),
                        repair=_repair("remove", "INVALIDATION-POLICY", "Remove invalidation or use a nonqueued data element."))
    return report


@plugin("data_read_access_nonqueued")
def data_read_access_nonqueued(
    index: ArxmlIndex, rule: dict, selected: list[etree._Element]
) -> PluginReport:
    """constr_2020: dataReadAccess cannot target queued data."""
    report = PluginReport(checked=len(selected))
    for access in selected:
        if index.nearest(access, {"DATA-READ-ACCESSS"}) is None:
            continue
        ref = next((item for item in access.iterdescendants()
                    if local_name(item.tag).endswith("TARGET-DATA-PROTOTYPE-REF")), None)
        target = _resolve(index, ref, report) if ref is not None else None
        if ref is None:
            report.incomplete(f"dataReadAccess target is missing at {index.location(access)}")
        elif target is not None and _impl_policy(target) == "QUEUED":
            report.fail(index, ref, "dataReadAccess cannot reference a QUEUED VariableDataPrototype",
                        repair=_repair("repair_reference", local_name(ref.tag), "Reference a nonqueued data element."))
    return report


@plugin("parameter_interface_port_kind")
def parameter_interface_port_kind(
    index: ArxmlIndex, rule: dict, selected: list[etree._Element]
) -> PluginReport:
    """constr_1312: ParameterInterface forbids PRPortPrototype."""
    report = PluginReport(checked=len(selected))
    for port in selected:
        interface = _port_interface(index, port, report)
        if interface is not None and local_name(interface.tag) == "PARAMETER-INTERFACE" and local_name(port.tag) == "PR-PORT-PROTOTYPE":
            report.fail(index, port, "PRPortPrototype typed by ParameterInterface is not supported",
                        repair=_repair("replace_port_kind", local_name(port.tag), "Use a PPortPrototype or RPortPrototype."))
    return report


def _final_impl_type(index: ArxmlIndex, data_type: etree._Element, report: PluginReport):
    seen: set[int] = set()
    current = data_type
    while local_name(current.tag) == "IMPLEMENTATION-DATA-TYPE" and _text(_first(current, {"CATEGORY"})) == "TYPE_REFERENCE":
        if id(current) in seen:
            report.incomplete(f"ImplementationDataType TYPE_REFERENCE cycle at {index.location(current)}")
            return None
        seen.add(id(current))
        ref = _first(current, {"IMPLEMENTATION-DATA-TYPE-REF"})
        target = _resolve(index, ref, report)
        if target is None:
            return None
        current = target
    return current


@plugin("implementation_compu_method_category")
def implementation_compu_method_category(
    index: ArxmlIndex, rule: dict, selected: list[etree._Element]
) -> PluginReport:
    """constr_1158: IDT compuMethod is TEXTTABLE or BITFIELD_TEXTTABLE."""
    report = PluginReport(checked=len(selected))
    for data_type in selected:
        for ref in (item for item in data_type.iterdescendants()
                    if local_name(item.tag) == "COMPU-METHOD-REF"):
            method = _resolve(index, ref, report)
            if method is None:
                continue
            category = _text(_first(method, {"CATEGORY"}))
            if category not in {"TEXTTABLE", "BITFIELD_TEXTTABLE"}:
                report.fail(index, ref, "ImplementationDataType compuMethod has an unsupported category",
                            actual=category, allowed=["BITFIELD_TEXTTABLE", "TEXTTABLE"],
                            repair=_repair("repair_reference", "COMPU-METHOD-REF", "Reference a TEXTTABLE or BITFIELD_TEXTTABLE CompuMethod."))
    return report


@plugin("mode_request_integral_type")
def mode_request_integral_type(
    index: ArxmlIndex, rule: dict, selected: list[etree._Element]
) -> PluginReport:
    """constr_1167: mode request type resolves to VALUE with NONE encoding."""
    report = PluginReport(checked=len(selected))
    for mapping in selected:
        ref = _first(mapping, {"IMPLEMENTATION-DATA-TYPE-REF"})
        data_type = _resolve(index, ref, report)
        if data_type is None:
            if ref is None:
                report.incomplete(f"ModeRequestTypeMap lacks type reference at {index.location(mapping)}")
            continue
        final = _final_impl_type(index, data_type, report)
        if final is None:
            continue
        category = _text(_first(final, {"CATEGORY"}))
        base_ref = _first(final, {"BASE-TYPE-REF"})
        base = _resolve(index, base_ref, report)
        encoding = _text(_first(base, {"BASE-TYPE-ENCODING"})) if base is not None else ""
        if category != "VALUE" or encoding != "NONE":
            report.fail(index, ref, "ModeRequestTypeMap type must resolve to VALUE with baseTypeEncoding NONE",
                        actual={"category": category, "encoding": encoding},
                        repair=_repair("repair_reference", "IMPLEMENTATION-DATA-TYPE-REF", "Reference an integral VALUE type encoded as NONE."))
    return report


@plugin("variation_proxy_value_type")
def variation_proxy_value_type(
    index: ArxmlIndex, rule: dict, selected: list[etree._Element]
) -> PluginReport:
    """constr_1389: VariationPointProxy type is VALUE or TYPE_REFERENCE->VALUE."""
    report = PluginReport(checked=len(selected))
    for proxy in selected:
        ref = _first(proxy, {"IMPLEMENTATION-DATA-TYPE-REF"})
        data_type = _resolve(index, ref, report)
        if data_type is None:
            if ref is None:
                report.incomplete(f"VariationPointProxy lacks implementation type at {index.location(proxy)}")
            continue
        initial = _text(_first(data_type, {"CATEGORY"}))
        final = _final_impl_type(index, data_type, report)
        final_category = _text(_first(final, {"CATEGORY"})) if final is not None else ""
        if initial not in {"VALUE", "TYPE_REFERENCE"} or final_category != "VALUE":
            report.fail(index, ref, "VariationPointProxy type must be VALUE or TYPE_REFERENCE resolving to VALUE",
                        actual={"initial": initial, "resolved": final_category},
                        repair=_repair("repair_reference", "IMPLEMENTATION-DATA-TYPE-REF", "Reference a VALUE ImplementationDataType."))
    return report


@plugin("implementation_init_value_kind")
def implementation_init_value_kind(
    index: ArxmlIndex, rule: dict, selected: list[etree._Element]
) -> PluginReport:
    """constr_1385: IDT-typed prototype cannot use ApplicationValueSpecification."""
    report = PluginReport(checked=len(selected))
    for prototype in selected:
        type_ref = _first(prototype, {"TYPE-TREF"})
        data_type = _resolve(index, type_ref, report) if type_ref is not None else None
        if type_ref is None or data_type is None or local_name(data_type.tag) != "IMPLEMENTATION-DATA-TYPE":
            continue
        invalid = _first(prototype, {"APPLICATION-VALUE-SPECIFICATION"})
        if invalid is not None:
            report.fail(index, invalid, "ImplementationDataType-typed DataPrototype cannot use ApplicationValueSpecification",
                        repair=_repair("replace_value_specification", "APPLICATION-VALUE-SPECIFICATION", "Use a value specification valid for the ImplementationDataType."))
    return report


@plugin("nv_block_port_domain")
def nv_block_port_domain(
    index: ArxmlIndex, rule: dict, selected: list[etree._Element]
) -> PluginReport:
    """constr_2009: external NvBlock ports have the exact supported domain."""
    report = PluginReport(checked=len(selected))
    for component in selected:
        for port in [item for item in component.iterdescendants() if local_name(item.tag) in PORT_TAGS]:
            interface = _port_interface(index, port, report)
            if interface is None:
                continue
            kind = local_name(interface.tag)
            valid = kind in {"NV-DATA-INTERFACE", "CLIENT-SERVER-INTERFACE"} or (
                kind == "MODE-SWITCH-INTERFACE" and local_name(port.tag) == "R-PORT-PROTOTYPE"
            )
            if not valid:
                report.fail(index, port, "NvBlockSwComponentType defines an unsupported external port kind",
                            port_kind=local_name(port.tag), interface_kind=kind,
                            repair=_repair("repair_reference", "INTERFACE-TREF", "Use NvDataInterface, ClientServerInterface, or an R port with ModeSwitchInterface."))
    return report


@plugin("service_proxy_port_domain")
def service_proxy_port_domain(
    index: ArxmlIndex, rule: dict, selected: list[etree._Element]
) -> PluginReport:
    """constr_2017: ServiceProxy ports either receive SR or use service interfaces."""
    report = PluginReport(checked=len(selected))
    for component in selected:
        for port in [item for item in component.iterdescendants() if local_name(item.tag) in PORT_TAGS]:
            interface = _port_interface(index, port, report)
            if interface is None:
                continue
            is_service = _text(_first(interface, {"IS-SERVICE"})).lower() in {"true", "1"}
            receive_sr = local_name(port.tag) == "R-PORT-PROTOTYPE" and local_name(interface.tag) == "SENDER-RECEIVER-INTERFACE"
            if not (receive_sr or is_service):
                report.fail(index, port, "ServiceProxySwComponentType port is neither receiving SR nor service-typed",
                            port_kind=local_name(port.tag), interface_kind=local_name(interface.tag),
                            repair=_repair("repair_reference", "INTERFACE-TREF", "Use an R/SenderReceiver port or an AUTOSAR service interface."))
    return report
