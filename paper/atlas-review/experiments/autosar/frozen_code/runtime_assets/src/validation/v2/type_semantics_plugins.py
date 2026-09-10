"""Fail-closed AUTOSAR type/context validators for the remaining type rules.

The helpers deliberately return ``None`` when a semantic conclusion cannot be
proved from the loaded ARXML graph.  Callers turn that into NOT_EVALUATED via
``PluginReport.incomplete``; absence or ambiguity is never treated as success.
"""

from __future__ import annotations

from collections import defaultdict

from lxml import etree

from .arxml_index import ArxmlIndex, local_name
from .plugins import COMPONENT_TAGS, INTERFACE_REF_TAGS, PORT_TAGS, PluginReport, plugin

DATA_PROTOTYPE_TAGS = {
    "VARIABLE-DATA-PROTOTYPE", "PARAMETER-DATA-PROTOTYPE",
    "ARGUMENT-DATA-PROTOTYPE", "APPLICATION-ARRAY-ELEMENT",
    "APPLICATION-RECORD-ELEMENT", "IMPLEMENTATION-DATA-TYPE-ELEMENT",
}
APPLICATION_TYPE_TAGS = {
    "APPLICATION-PRIMITIVE-DATA-TYPE", "APPLICATION-ARRAY-DATA-TYPE",
    "APPLICATION-RECORD-DATA-TYPE",
}
AUTOSAR_TYPE_TAGS = APPLICATION_TYPE_TAGS | {"IMPLEMENTATION-DATA-TYPE"}
VALUE_SPEC_TAGS = {
    "APPLICATION-VALUE-SPECIFICATION", "APPLICATION-RULE-BASED-VALUE-SPECIFICATION",
    "ARRAY-VALUE-SPECIFICATION", "NUMERICAL-RULE-BASED-VALUE-SPECIFICATION",
    "NUMERICAL-VALUE-SPECIFICATION", "RECORD-VALUE-SPECIFICATION",
    "REFERENCE-VALUE-SPECIFICATION", "TEXT-VALUE-SPECIFICATION",
    "CONSTANT-REFERENCE",
}


def _text(element: etree._Element | None) -> str:
    return (element.text or "").strip() if element is not None else ""


def _direct(element: etree._Element, tag: str) -> etree._Element | None:
    return next((child for child in element if local_name(child.tag) == tag), None)


def _first(element: etree._Element, tags: set[str]) -> etree._Element | None:
    return next((item for item in element.iterdescendants() if local_name(item.tag) in tags), None)


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


def _type_of(
    index: ArxmlIndex, prototype: etree._Element, report: PluginReport
) -> etree._Element | None:
    return _resolve(index, _first(prototype, {"TYPE-TREF"}), report, f"{local_name(prototype.tag)} type")


def _final_impl_type(
    index: ArxmlIndex, data_type: etree._Element, report: PluginReport
) -> etree._Element | None:
    current = data_type
    seen: set[int] = set()
    while local_name(current.tag) == "IMPLEMENTATION-DATA-TYPE" and _text(_direct(current, "CATEGORY")) == "TYPE_REFERENCE":
        if id(current) in seen:
            report.incomplete(f"TYPE_REFERENCE cycle at {index.location(current)}")
            return None
        seen.add(id(current))
        current = _resolve(
            index,
            _first(current, {"IMPLEMENTATION-DATA-TYPE-REF"}),
            report,
            "TYPE_REFERENCE target",
        )
        if current is None:
            return None
        if local_name(current.tag) != "IMPLEMENTATION-DATA-TYPE":
            report.incomplete(
                f"TYPE_REFERENCE resolves to {local_name(current.tag)} at {index.location(current)}"
            )
            return None
    return current


def _mapped_impl_types(
    index: ArxmlIndex, application_type: etree._Element, report: PluginReport
) -> list[etree._Element] | None:
    found: list[etree._Element] = []
    for mapping in index.elements("DATA-TYPE-MAP"):
        app = _resolve(
            index, _first(mapping, {"APPLICATION-DATA-TYPE-REF"}), report,
            "DataTypeMap application type",
        )
        if app is not application_type:
            continue
        impl = _resolve(
            index, _first(mapping, {"IMPLEMENTATION-DATA-TYPE-REF"}), report,
            "DataTypeMap implementation type",
        )
        if impl is not None and all(impl is not item for item in found):
            found.append(impl)
    if not found:
        report.incomplete(
            f"no DataTypeMap proves an implementation type for {index.path_of(application_type)}"
        )
        return None
    return found


def _primitive_c_type(
    index: ArxmlIndex, data_type: etree._Element, report: PluginReport
) -> bool | None:
    tag = local_name(data_type.tag)
    category = _text(_direct(data_type, "CATEGORY"))
    if tag == "APPLICATION-PRIMITIVE-DATA-TYPE":
        return category in {"VALUE", "BOOLEAN"}
    if tag == "IMPLEMENTATION-DATA-TYPE":
        final = _final_impl_type(index, data_type, report)
        return None if final is None else _text(_direct(final, "CATEGORY")) == "VALUE"
    if tag in {"APPLICATION-ARRAY-DATA-TYPE", "APPLICATION-RECORD-DATA-TYPE"}:
        return False
    report.incomplete(f"unsupported AutosarDataType {tag} at {index.location(data_type)}")
    return None


def _compu_category_for_type(
    index: ArxmlIndex, data_type: etree._Element, report: PluginReport
) -> str | None:
    ref = _first(data_type, {"COMPU-METHOD-REF"})
    if ref is None:
        report.incomplete(f"missing CompuMethod for {index.path_of(data_type)}")
        return None
    method = _resolve(index, ref, report, "CompuMethod")
    if method is None:
        return None
    category = _text(_direct(method, "CATEGORY"))
    if not category:
        report.incomplete(f"CompuMethod category is missing at {index.location(method)}")
        return None
    return category


def _value_spec_in(container: etree._Element) -> etree._Element | None:
    return next(
        (item for item in container.iterdescendants() if local_name(item.tag) in VALUE_SPEC_TAGS),
        None,
    )


def _type_context_for_value(
    index: ArxmlIndex, value: etree._Element, report: PluginReport
) -> etree._Element | None:
    prototype = index.nearest(value, DATA_PROTOTYPE_TAGS)
    if prototype is not None:
        return _type_of(index, prototype, report)
    data_type = index.nearest(value, AUTOSAR_TYPE_TAGS)
    if data_type is not None:
        return data_type
    report.incomplete(f"cannot prove AutosarDataType context for {index.location(value)}")
    return None


def _unit_for_type(
    index: ArxmlIndex, data_type: etree._Element, report: PluginReport
) -> etree._Element | None:
    ref = _first(data_type, {"UNIT-REF"})
    if ref is None:
        return None
    return _resolve(index, ref, report, "AutosarDataType unit")


def _decimal_text(element: etree._Element, tag: str, default: str) -> str:
    value = _first(element, {tag})
    return _text(value) if value is not None else default


def _physical_dimension_signature(element: etree._Element) -> tuple[str, ...]:
    return tuple(
        _decimal_text(element, tag, "0")
        for tag in (
            "LENGTH-EXP", "MASS-EXP", "TIME-EXP", "CURRENT-EXP",
            "TEMPERATURE-EXP", "MOLAR-AMOUNT-EXP", "LUMINOUS-INTENSITY-EXP",
        )
    )


def _units_compatible(
    index: ArxmlIndex, first: etree._Element, second: etree._Element, report: PluginReport
) -> bool | None:
    if first is second:
        return True
    if (
        _decimal_text(first, "FACTOR-SI-TO-UNIT", "1")
        != _decimal_text(second, "FACTOR-SI-TO-UNIT", "1")
        or _decimal_text(first, "OFFSET-SI-TO-UNIT", "0")
        != _decimal_text(second, "OFFSET-SI-TO-UNIT", "0")
    ):
        return False
    first_ref = _first(first, {"PHYSICAL-DIMENSION-REF"})
    second_ref = _first(second, {"PHYSICAL-DIMENSION-REF"})
    if first_ref is None or second_ref is None:
        return first_ref is None and second_ref is None
    first_dim = _resolve(index, first_ref, report, "first Unit physical dimension")
    second_dim = _resolve(index, second_ref, report, "second Unit physical dimension")
    if first_dim is None or second_dim is None:
        return None
    return _physical_dimension_signature(first_dim) == _physical_dimension_signature(second_dim)


@plugin("populated_atomic_runnable_context")
def populated_atomic_runnable_context(
    index: ArxmlIndex, rule: dict, selected: list[etree._Element]
) -> PluginReport:
    """TPS_SWCT_01098: runnable-owning atomic types populate a composition."""
    report = PluginReport(checked=len(selected))
    populated: set[int] = set()
    for prototype in index.elements("SW-COMPONENT-PROTOTYPE"):
        if index.nearest(prototype, {"COMPOSITION-SW-COMPONENT-TYPE"}) is None:
            continue
        target = _resolve(index, _first(prototype, {"TYPE-TREF"}), report, "component prototype type")
        if target is not None:
            populated.add(id(target))
    for component in selected:
        runnables = _owned(index, component, "RUNNABLE-ENTITY", COMPONENT_TAGS)
        if runnables and id(component) not in populated:
            # A component-fragment bundle cannot prove that no composition in
            # the surrounding project instantiates this atomic type.  Treating
            # absence from the partial bundle as a violation turns missing
            # external antecedent evidence into a false model failure.  A
            # resolved prototype is positive evidence; the negative direction
            # remains explicitly unevaluated until a complete composition
            # context is supplied.
            report.incomplete(
                "composition population context is absent or incomplete for "
                f"runnable-owning component {index.location(component)}"
            )
    return report


@plugin("nv_mapping_port_interface")
def nv_mapping_port_interface(
    index: ArxmlIndex, rule: dict, selected: list[etree._Element]
) -> PluginReport:
    """TPS_SWCT_01142: ports actually used for NV data are NvDataInterface ports."""
    report = PluginReport(checked=len(selected))
    for mapping in selected:
        for ref in mapping.iterdescendants():
            tag = local_name(ref.tag)
            if "PORT" not in tag or not tag.endswith(("-REF", "-TREF")) or not _text(ref):
                continue
            port = _resolve(index, ref, report, "NvBlockDataMapping port")
            if port is None or local_name(port.tag) not in PORT_TAGS:
                continue
            interface = _resolve(index, _first(port, INTERFACE_REF_TAGS), report, "NV data port interface")
            if interface is not None and local_name(interface.tag) != "NV-DATA-INTERFACE":
                report.fail(
                    index, ref,
                    "Port used by NvBlockDataMapping is not typed by NvDataInterface",
                    actual_interface=local_name(interface.tag),
                    repair=_repair(
                        "repair_reference", local_name(ref.tag),
                        "Reference an NvBlockSwComponentType port typed by NvDataInterface.",
                    ),
                )
    return report


@plugin("e2e_sender_receiver_only")
def e2e_sender_receiver_only(
    index: ArxmlIndex, rule: dict, selected: list[etree._Element]
) -> PluginReport:
    """constr_1000: E2E variable endpoints belong to SenderReceiverInterface."""
    report = PluginReport(checked=len(selected))
    for protection in selected:
        for ref in protection.iterdescendants():
            tag = local_name(ref.tag)
            if tag not in {"TARGET-DATA-PROTOTYPE-REF", "TARGET-DATA-ELEMENT-REF"}:
                continue
            target = _resolve(index, ref, report, "end-to-end protected variable")
            if target is None:
                continue
            interface = index.nearest(target, {"SENDER-RECEIVER-INTERFACE", "NV-DATA-INTERFACE", "PARAMETER-INTERFACE", "CLIENT-SERVER-INTERFACE"})
            if interface is None:
                report.incomplete(f"cannot prove interface context for {index.location(target)}")
            elif local_name(interface.tag) != "SENDER-RECEIVER-INTERFACE":
                report.fail(
                    index, ref,
                    "End-to-end protection endpoint is outside sender/receiver communication",
                    actual_interface=local_name(interface.tag),
                    repair=_repair(
                        "repair_reference", tag,
                        "Reference a VariableDataPrototype owned by a SenderReceiverInterface.",
                    ),
                )
    return report


@plugin("application_category_kind")
def application_category_kind(
    index: ArxmlIndex, rule: dict, selected: list[etree._Element]
) -> PluginReport:
    """constr_1008: ARRAY/STRUCTURE are composite; all other categories primitive."""
    report = PluginReport(checked=len(selected))
    for data_type in selected:
        category_element = _direct(data_type, "CATEGORY")
        category = _text(category_element)
        if not category:
            report.incomplete(f"missing CATEGORY at {index.location(data_type)}")
            continue
        composite = local_name(data_type.tag) in {"APPLICATION-ARRAY-DATA-TYPE", "APPLICATION-RECORD-DATA-TYPE"}
        expected = {"ARRAY", "STRUCTURE"} if composite else None
        valid = category in expected if composite else category not in {"ARRAY", "STRUCTURE"}
        if not valid:
            report.fail(
                index, category_element if category_element is not None else data_type,
                "ApplicationDataType category does not match primitive/composite metaclass",
                actual=category, metaclass=local_name(data_type.tag),
                repair=_repair(
                    "replace_value", "CATEGORY",
                    "Use ARRAY/STRUCTURE only for application composite types and other categories only for ApplicationPrimitiveDataType.",
                ),
            )
    return report


@plugin("composite_network_representation")
def composite_network_representation(
    index: ArxmlIndex, rule: dict, selected: list[etree._Element]
) -> PluginReport:
    """TPS_SWCT_01452: simple networkRepresentation is primitive-only."""
    report = PluginReport(checked=len(selected))
    for comspec in selected:
        simple = _first(comspec, {"NETWORK-REPRESENTATION"})
        if simple is None:
            continue
        data = _resolve(index, _first(comspec, {"DATA-ELEMENT-REF"}), report, "ComSpec data element")
        if data is None:
            continue
        data_type = _type_of(index, data, report)
        if data_type is not None and local_name(data_type.tag) != "APPLICATION-PRIMITIVE-DATA-TYPE":
            report.fail(
                index, simple,
                "networkRepresentation is only valid for an ApplicationPrimitiveDataType data element",
                actual_type=local_name(data_type.tag),
                repair=_repair(
                    "replace_element", "NETWORK-REPRESENTATION",
                    "Use compositeNetworkRepresentation for the leaf elements of the composite data type.",
                ),
            )
    return report


@plugin("port_defined_argument_value_type")
def port_defined_argument_value_type(
    index: ArxmlIndex, rule: dict, selected: list[etree._Element]
) -> PluginReport:
    """constr_1150: valueType is VALUE or TYPE_REFERENCE resolving to VALUE."""
    report = PluginReport(checked=len(selected))
    for value in selected:
        ref = _first(value, {"VALUE-TYPE-TREF"})
        data_type = _resolve(index, ref, report, "PortDefinedArgumentValue valueType")
        if data_type is None:
            continue
        initial = _text(_direct(data_type, "CATEGORY"))
        final = _final_impl_type(index, data_type, report) if local_name(data_type.tag) == "IMPLEMENTATION-DATA-TYPE" else data_type
        final_category = _text(_direct(final, "CATEGORY")) if final is not None else ""
        if initial not in {"VALUE", "TYPE_REFERENCE"} or final_category != "VALUE":
            report.fail(
                index, ref if ref is not None else value,
                "PortDefinedArgumentValue.valueType must resolve to category VALUE",
                actual={"initial": initial, "resolved": final_category},
                repair=_repair(
                    "repair_reference", "VALUE-TYPE-TREF",
                    "Reference a VALUE ImplementationDataType or a TYPE_REFERENCE chain ending in VALUE.",
                ),
            )
    return report


@plugin("application_invalid_value_kind")
def application_invalid_value_kind(
    index: ArxmlIndex, rule: dict, selected: list[etree._Element]
) -> PluginReport:
    """constr_1282: unsupported rule/reference value kinds are forbidden."""
    report = PluginReport(checked=len(selected))
    forbidden = {"APPLICATION-RULE-BASED-VALUE-SPECIFICATION", "NUMERICAL-RULE-BASED-VALUE-SPECIFICATION", "REFERENCE-VALUE-SPECIFICATION"}
    for data_type in selected:
        if local_name(data_type.tag) != "APPLICATION-PRIMITIVE-DATA-TYPE":
            continue
        for invalid in index.descendants(data_type, {"INVALID-VALUE"}):
            spec = _value_spec_in(invalid)
            if spec is None:
                report.incomplete(f"invalidValue has no ValueSpecification at {index.location(invalid)}")
            elif local_name(spec.tag) in forbidden:
                report.fail(
                    index, spec,
                    "ApplicationPrimitiveDataType.invalidValue uses an unsupported value specification kind",
                    actual=local_name(spec.tag), allowed=["APPLICATION-VALUE-SPECIFICATION", "CONSTANT-REFERENCE"],
                    repair=_repair(
                        "replace_value_specification", local_name(spec.tag),
                        "Use an ApplicationValueSpecification or a ConstantReference to one.",
                    ),
                )
    return report


@plugin("text_value_compu_category")
def text_value_compu_category(
    index: ArxmlIndex, rule: dict, selected: list[etree._Element]
) -> PluginReport:
    """constr_1284: TextValueSpecification requires a textual CompuMethod."""
    report = PluginReport(checked=len(selected))
    allowed = {
        "TEXTTABLE", "BITFIELD_TEXTTABLE", "SCALE_LINEAR_AND_TEXTTABLE",
        "SCALE_RATIONAL_AND_TEXTTABLE",
    }
    for value in selected:
        data_type = _type_context_for_value(index, value, report)
        if data_type is None:
            continue
        category = _compu_category_for_type(index, data_type, report)
        if category is not None and category not in allowed:
            report.fail(
                index, value,
                "TextValueSpecification is used with a non-textual CompuMethod",
                actual=category, allowed=sorted(allowed), data_type=index.path_of(data_type),
                repair=_repair(
                    "repair_reference", "COMPU-METHOD-REF",
                    "Use one of the textual CompuMethod categories or replace the TextValueSpecification.",
                ),
            )
    return report


@plugin("server_argument_policy_type")
def server_argument_policy_type(
    index: ArxmlIndex, rule: dict, selected: list[etree._Element]
) -> PluginReport:
    """constr_1286/1297: server argument implementation policy matches type shape."""
    report = PluginReport(checked=len(selected))
    for argument in selected:
        policy_element = _direct(argument, "SERVER-ARGUMENT-IMPL-POLICY")
        policy = _text(policy_element)
        if policy not in {"USE-VOID", "USE-ARRAY-BASE-TYPE", "useVoid", "useArrayBaseType"}:
            continue
        data_type = _type_of(index, argument, report)
        if data_type is None:
            continue
        if rule["constraint_id"] == "constr_1286":
            direction = _text(_direct(argument, "DIRECTION")).upper()
            primitive = _primitive_c_type(index, data_type, report)
            if direction == "IN" and primitive is True and policy.upper().replace("-", "_") in {"USE_VOID", "USEVOID"}:
                report.fail(
                    index, policy_element if policy_element is not None else argument,
                    "useVoid is forbidden for an IN argument with a primitive C data type",
                    data_type=index.path_of(data_type),
                    repair=_repair(
                        "replace_value", "SERVER-ARGUMENT-IMPL-POLICY",
                        "Use useArgumentType for this primitive IN argument.",
                    ),
                )
        else:
            if policy.upper().replace("-", "_") not in {"USE_ARRAY_BASE_TYPE", "USEARRAYBASETYPE"}:
                continue
            candidates: list[etree._Element]
            if local_name(data_type.tag) == "IMPLEMENTATION-DATA-TYPE":
                candidates = [data_type]
            elif local_name(data_type.tag) in APPLICATION_TYPE_TAGS:
                mapped = _mapped_impl_types(index, data_type, report)
                if mapped is None:
                    continue
                candidates = mapped
            else:
                report.incomplete(f"unsupported argument type at {index.location(data_type)}")
                continue
            resolved_categories: list[str] = []
            for candidate in candidates:
                final = _final_impl_type(index, candidate, report)
                if final is not None:
                    resolved_categories.append(_text(_direct(final, "CATEGORY")))
            if resolved_categories and "ARRAY" not in resolved_categories:
                report.fail(
                    index, policy_element if policy_element is not None else argument,
                    "useArrayBaseType requires an ImplementationDataType resolving to ARRAY",
                    resolved_categories=resolved_categories,
                    repair=_repair(
                        "replace_value", "SERVER-ARGUMENT-IMPL-POLICY",
                        "Use useArrayBaseType only with an ARRAY implementation type.",
                    ),
                )
    return report


@plugin("assigned_value_unit_compatible")
def assigned_value_unit_compatible(
    index: ArxmlIndex, rule: dict, selected: list[etree._Element]
) -> PluginReport:
    """constr_1391/1392: assigned application value and target type units agree."""
    report = PluginReport(checked=len(selected))
    for value in selected:
        prototype = index.nearest(value, DATA_PROTOTYPE_TAGS)
        if prototype is None:
            report.incomplete(f"cannot prove assigned DataPrototype for {index.location(value)}")
            continue
        data_type = _type_of(index, prototype, report)
        if data_type is None:
            continue
        value_ref = _first(value, {"UNIT-REF"})
        type_ref = _first(data_type, {"UNIT-REF"})
        if value_ref is None and type_ref is None:
            continue
        if value_ref is None or type_ref is None:
            report.fail(
                index, value,
                "Assigned value and AutosarDataType do not both define a Unit",
                value_has_unit=value_ref is not None, type_has_unit=type_ref is not None,
                repair=_repair(
                    "align_unit", "UNIT-REF",
                    "Define compatible units on both the assigned value and the target data type, or on neither.",
                ),
            )
            continue
        value_unit = _resolve(index, value_ref, report, "assigned value Unit")
        type_unit = _resolve(index, type_ref, report, "AutosarDataType Unit")
        if value_unit is None or type_unit is None:
            continue
        compatible = _units_compatible(index, value_unit, type_unit, report)
        if compatible is False:
            report.fail(
                index, value_ref,
                "Assigned value Unit is incompatible with the AutosarDataType Unit",
                assigned_unit=index.path_of(value_unit), type_unit=index.path_of(type_unit),
                repair=_repair(
                    "repair_reference", "UNIT-REF",
                    "Reference a Unit with identical conversion and physical dimension semantics.",
                ),
            )
    return report


@plugin("data_transformation_reference_role")
def data_transformation_reference_role(
    index: ArxmlIndex, rule: dict, selected: list[etree._Element]
) -> PluginReport:
    """constr_1400: one transformation is used in exactly one permitted role class."""
    report = PluginReport(checked=len(selected))
    roles_by_target: dict[int, set[str]] = defaultdict(set)
    target_by_id: dict[int, etree._Element] = {}
    refs_by_target: dict[int, list[etree._Element]] = defaultdict(list)
    for root in index.roots:
        for ref in root.iter():
            if not isinstance(ref.tag, str) or not local_name(ref.tag).endswith("REF"):
                continue
            if "DATA-TRANSFORMATION" not in local_name(ref.tag) or not _text(ref):
                continue
            target = _resolve(index, ref, report, "DataTransformation")
            if target is None or local_name(target.tag) != "DATA-TRANSFORMATION":
                continue
            tag = local_name(ref.tag)
            if tag == "FIRST-TO-SECOND-DATA-TRANSFORMATION-REF" and index.nearest(ref, {"DATA-PROTOTYPE-MAPPING"}) is not None:
                role = "data_prototype_mapping"
            elif index.nearest(ref, {"I-SIGNAL"}) is not None:
                role = "i_signal"
            elif index.nearest(ref, {"I-SIGNAL-GROUP"}) is not None and index.nearest(ref, {"COM-BASED-SIGNAL-GROUP-TRANSFORMATIONS"}) is not None:
                role = "i_signal_group"
            else:
                role = "forbidden"
            marker = id(target)
            target_by_id[marker] = target
            roles_by_target[marker].add(role)
            refs_by_target[marker].append(ref)
    for marker, roles in roles_by_target.items():
        if "forbidden" in roles or len(roles) > 1:
            target = target_by_id[marker]
            report.fail(
                index, refs_by_target[marker][0],
                "DataTransformation is referenced from a forbidden or mixed semantic role",
                transformation=index.path_of(target), roles=sorted(roles),
                references=[index.location(item) for item in refs_by_target[marker]],
                repair=_repair(
                    "remove_reference", "DATA-TRANSFORMATION-REF",
                    "Keep references to this DataTransformation in only one allowed role class.",
                ),
            )
    return report
