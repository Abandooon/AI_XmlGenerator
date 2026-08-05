"""Shared, fail-closed AUTOSAR compatibility semantics.

No helper converts absent evidence into compatibility.  ``None`` means that the
loaded ARXML graph cannot prove the relation and callers must return
NOT_EVALUATED.  Explicit mappings are passed separately and take precedence over
short-name matching.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from lxml import etree

from .arxml_index import ArxmlIndex, local_name
from .plugins import INTERFACE_REF_TAGS, PluginReport

APP_TYPES = {
    "APPLICATION-PRIMITIVE-DATA-TYPE", "APPLICATION-ARRAY-DATA-TYPE", "APPLICATION-RECORD-DATA-TYPE",
}
DATA_PROTOTYPES = {
    "VARIABLE-DATA-PROTOTYPE", "PARAMETER-DATA-PROTOTYPE", "ARGUMENT-DATA-PROTOTYPE",
    "APPLICATION-ARRAY-ELEMENT", "APPLICATION-RECORD-ELEMENT", "IMPLEMENTATION-DATA-TYPE-ELEMENT",
}
INTERFACE_MEMBERS = DATA_PROTOTYPES | {
    "CLIENT-SERVER-OPERATION", "APPLICATION-ERROR", "MODE-DECLARATION-GROUP-PROTOTYPE", "TRIGGER",
}
DOC_TAGS = {
    "SHORT-NAME", "DESC", "INTRODUCTION", "LONG-NAME", "ADMIN-DATA", "ANNOTATION", "ANNOTATIONS",
}
PROPS_AFFECTING_COMPATIBILITY = {
    "UNIT-REF", "COMPU-METHOD-REF", "INVALID-VALUE", "DATA-CONSTR-REF", "SW-RECORD-LAYOUT-REF",
}


def text(element: etree._Element | None) -> str:
    return (element.text or "").strip() if element is not None else ""


def direct(element: etree._Element, tag: str) -> etree._Element | None:
    return next((child for child in element if local_name(child.tag) == tag), None)


def first(element: etree._Element, tags: set[str]) -> etree._Element | None:
    return next((item for item in element.iterdescendants() if local_name(item.tag) in tags), None)


def short_name(element: etree._Element) -> str:
    return text(direct(element, "SHORT-NAME"))


def resolve(index: ArxmlIndex, ref: etree._Element | None, report: PluginReport, label: str, *, required: bool = True) -> etree._Element | None:
    if ref is None:
        if required:
            report.incomplete(f"missing {label}")
        return None
    resolution = index.resolve(ref)
    if resolution.status != "resolved" or resolution.element is None:
        report.incomplete(f"{resolution.status} {label} {resolution.reference} at {index.location(ref)}")
        return None
    return resolution.element


def owned(index: ArxmlIndex, owner: etree._Element, tag: str, owner_tags: set[str]) -> list[etree._Element]:
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


def canonical(element: etree._Element | None, *, ignored: set[str] | None = None) -> object:
    if element is None:
        return None
    ignored = ignored or set()
    tag = local_name(element.tag)
    if tag in ignored:
        return None
    attrs = tuple(sorted((local_name(key), str(value)) for key, value in element.attrib.items()))
    children = tuple(
        item for item in (canonical(child, ignored=ignored) for child in element if isinstance(child.tag, str))
        if item is not None
    )
    return tag, attrs, text(element), children


def _decimal(element: etree._Element | None, report: PluginReport, index: ArxmlIndex, label: str, default: str | None = None) -> Decimal | None:
    raw = text(element) if element is not None else (default or "")
    try:
        return Decimal(raw)
    except (InvalidOperation, ValueError):
        report.incomplete(f"non-numeric {label} {raw!r} at {index.location(element) if element is not None else None}")
        return None


def physical_dimension_signature(element: etree._Element) -> tuple[str, ...]:
    return tuple(
        text(first(element, {tag})) or "0"
        for tag in (
            "LENGTH-EXP", "MASS-EXP", "TIME-EXP", "CURRENT-EXP",
            "TEMPERATURE-EXP", "MOLAR-AMOUNT-EXP", "LUMINOUS-INTENSITY-EXP",
        )
    )


def physical_dimensions_compatible(index: ArxmlIndex, left: etree._Element, right: etree._Element, report: PluginReport) -> bool:
    if physical_dimension_signature(left) != physical_dimension_signature(right):
        return False
    if short_name(left) == short_name(right):
        return True
    for mapping in index.elements("PHYSICAL-DIMENSION-MAPPING"):
        refs = [item for item in mapping.iterdescendants() if local_name(item.tag).endswith("-REF")]
        targets = [resolve(index, ref, report, "PhysicalDimensionMapping endpoint") for ref in refs]
        markers = {id(item) for item in targets if item is not None}
        if {id(left), id(right)} <= markers:
            return True
    return False


def units_compatible(index: ArxmlIndex, left: etree._Element, right: etree._Element, report: PluginReport) -> bool | None:
    left_factor = _decimal(first(left, {"FACTOR-SI-TO-UNIT"}), report, index, "factorSiToUnit", "1")
    right_factor = _decimal(first(right, {"FACTOR-SI-TO-UNIT"}), report, index, "factorSiToUnit", "1")
    left_offset = _decimal(first(left, {"OFFSET-SI-TO-UNIT"}), report, index, "offsetSiToUnit", "0")
    right_offset = _decimal(first(right, {"OFFSET-SI-TO-UNIT"}), report, index, "offsetSiToUnit", "0")
    if None in {left_factor, right_factor, left_offset, right_offset}:
        return None
    if left_factor != right_factor or left_offset != right_offset:
        return False
    left_ref = first(left, {"PHYSICAL-DIMENSION-REF"})
    right_ref = first(right, {"PHYSICAL-DIMENSION-REF"})
    if left_ref is None or right_ref is None:
        return left_ref is None and right_ref is None
    left_dim = resolve(index, left_ref, report, "left Unit physical dimension")
    right_dim = resolve(index, right_ref, report, "right Unit physical dimension")
    return None if left_dim is None or right_dim is None else physical_dimensions_compatible(index, left_dim, right_dim, report)


def reference_pair_compatible(index: ArxmlIndex, left_ref: etree._Element | None, right_ref: etree._Element | None, report: PluginReport, label: str, comparator) -> bool | None:
    if left_ref is None or right_ref is None:
        return left_ref is None and right_ref is None
    left = resolve(index, left_ref, report, f"left {label}")
    right = resolve(index, right_ref, report, f"right {label}")
    if left is None or right is None:
        return None
    return comparator(index, left, right, report)


def _scale_coefficients(scale: etree._Element, report: PluginReport, index: ArxmlIndex) -> tuple[tuple[Decimal, ...], tuple[Decimal, ...]] | None:
    numerator_container = first(scale, {"COMPU-NUMERATOR"})
    denominator_container = first(scale, {"COMPU-DENOMINATOR"})
    numerators = [
        _decimal(item, report, index, "CompuScale numerator")
        for item in (numerator_container.iterdescendants() if numerator_container is not None else [])
        if local_name(item.tag) in {"V", "VF"}
    ]
    denominators = [
        _decimal(item, report, index, "CompuScale denominator")
        for item in (denominator_container.iterdescendants() if denominator_container is not None else [])
        if local_name(item.tag) in {"V", "VF"}
    ]
    if any(item is None for item in numerators + denominators):
        return None
    return tuple(numerators), tuple(denominators)


def compu_scale_signature(scale: etree._Element, report: PluginReport, index: ArxmlIndex, *, names: bool = True) -> object | None:
    coefficients = _scale_coefficients(scale, report, index)
    if coefficients is None:
        return None
    lower = text(first(scale, {"LOWER-LIMIT"}))
    upper = text(first(scale, {"UPPER-LIMIT"}))
    const = first(scale, {"COMPU-CONST"})
    name_part: object = None
    if names and const is not None:
        name_part = (
            text(direct(scale, "SHORT-LABEL")), text(first(scale, {"SYMBOL"})),
            canonical(const, ignored=DOC_TAGS),
        )
    return lower, upper, coefficients, name_part


def compu_method_unit(index: ArxmlIndex, method: etree._Element, report: PluginReport) -> etree._Element | None:
    return resolve(index, first(method, {"UNIT-REF"}), report, "CompuMethod Unit", required=False)


def compu_methods_compatible(index: ArxmlIndex, left: etree._Element, right: etree._Element, report: PluginReport) -> bool | None:
    ignored = DOC_TAGS | {"DISPLAY-FORMAT", "COMPU-SCALES", "UNIT-REF"}
    if canonical(left, ignored=ignored) != canonical(right, ignored=ignored):
        return False
    left_unit = compu_method_unit(index, left, report)
    right_unit = compu_method_unit(index, right, report)
    if left_unit is None or right_unit is None:
        if report.incomplete_reasons:
            return None
        if left_unit is not right_unit:
            return False
    elif units_compatible(index, left_unit, right_unit, report) is not True:
        return False
    left_scales = owned(index, left, "COMPU-SCALE", {"COMPU-METHOD"})
    right_scales = owned(index, right, "COMPU-SCALE", {"COMPU-METHOD"})
    left_signatures = [compu_scale_signature(item, report, index) for item in left_scales]
    right_signatures = [compu_scale_signature(item, report, index) for item in right_scales]
    if any(item is None for item in left_signatures + right_signatures):
        return None
    return sorted(map(repr, left_signatures)) == sorted(map(repr, right_signatures))


def data_constr_intervals(index: ArxmlIndex, constr: etree._Element, report: PluginReport) -> tuple[tuple[str, str, str], ...] | None:
    result: list[tuple[str, str, str]] = []
    for container in constr.iterdescendants():
        tag = local_name(container.tag)
        if tag not in {"INTERNAL-CONSTRS", "PHYS-CONSTRS"}:
            continue
        low = first(container, {"LOWER-LIMIT"})
        high = first(container, {"UPPER-LIMIT"})
        if low is None or high is None:
            report.incomplete(f"DataConstr limit pair is incomplete at {index.location(container)}")
            return None
        result.append((tag, text(low), text(high)))
    if not result:
        report.incomplete(f"DataConstr has no limits at {index.location(constr)}")
        return None
    return tuple(sorted(result))


def data_constrs_compatible(index: ArxmlIndex, left: etree._Element, right: etree._Element, report: PluginReport) -> bool | None:
    left_ranges = data_constr_intervals(index, left, report)
    right_ranges = data_constr_intervals(index, right, report)
    if left_ranges is None or right_ranges is None:
        return None
    if left_ranges != right_ranges:
        return False
    return reference_pair_compatible(
        index, first(left, {"UNIT-REF"}), first(right, {"UNIT-REF"}), report,
        "PhysConstrs Unit", units_compatible,
    )


def sw_record_layouts_compatible(index: ArxmlIndex, left: etree._Element, right: etree._Element, report: PluginReport) -> bool:
    return canonical(left, ignored=DOC_TAGS) == canonical(right, ignored=DOC_TAGS)


def _value_canonical(index: ArxmlIndex, value: etree._Element | None, report: PluginReport) -> object | None:
    if value is None:
        return None
    spec = next((item for item in value.iterdescendants() if local_name(item.tag).endswith("VALUE-SPECIFICATION") or local_name(item.tag) == "CONSTANT-REFERENCE"), None)
    if spec is None:
        report.incomplete(f"invalidValue has no ValueSpecification at {index.location(value)}")
        return None
    if local_name(spec.tag) == "CONSTANT-REFERENCE":
        constant = resolve(index, first(spec, {"CONSTANT-REF"}), report, "invalid ConstantReference")
        if constant is None:
            return None
        spec = next((item for item in constant.iterdescendants() if local_name(item.tag).endswith("VALUE-SPECIFICATION")), None)
        if spec is None:
            report.incomplete(f"ConstantSpecification has no value at {index.location(constant)}")
            return None
    return canonical(spec, ignored=DOC_TAGS)


def props(owner: etree._Element) -> etree._Element | None:
    return first(owner, {"SW-DATA-DEF-PROPS"})


def sw_data_def_props_compatible(index: ArxmlIndex, left: etree._Element | None, right: etree._Element | None, report: PluginReport) -> bool | None:
    if left is None or right is None:
        return left is None and right is None
    comparators = {
        "UNIT-REF": units_compatible,
        "COMPU-METHOD-REF": compu_methods_compatible,
        "DATA-CONSTR-REF": data_constrs_compatible,
        "SW-RECORD-LAYOUT-REF": sw_record_layouts_compatible,
    }
    for tag, comparator in comparators.items():
        compatible = reference_pair_compatible(index, first(left, {tag}), first(right, {tag}), report, tag, comparator)
        if compatible is not True:
            return compatible
    left_invalid = first(left, {"INVALID-VALUE"})
    right_invalid = first(right, {"INVALID-VALUE"})
    if left_invalid is None or right_invalid is None:
        return left_invalid is None and right_invalid is None
    return _value_canonical(index, left_invalid, report) == _value_canonical(index, right_invalid, report)


def unwrap_impl(index: ArxmlIndex, data_type: etree._Element, report: PluginReport) -> etree._Element | None:
    current = data_type
    seen: set[int] = set()
    while local_name(current.tag) == "IMPLEMENTATION-DATA-TYPE" and text(direct(current, "CATEGORY")) == "TYPE_REFERENCE":
        if id(current) in seen:
            report.incomplete(f"ImplementationDataType TYPE_REFERENCE cycle at {index.location(current)}")
            return None
        seen.add(id(current))
        current = resolve(index, first(current, {"IMPLEMENTATION-DATA-TYPE-REF"}), report, "TYPE_REFERENCE target")
        if current is None:
            return None
    return current


def type_of(index: ArxmlIndex, prototype: etree._Element, report: PluginReport) -> etree._Element | None:
    return resolve(index, first(prototype, {"TYPE-TREF"}), report, f"{local_name(prototype.tag)} type")


def _type_children(index: ArxmlIndex, data_type: etree._Element) -> list[etree._Element]:
    tag = local_name(data_type.tag)
    if tag == "APPLICATION-ARRAY-DATA-TYPE":
        return owned(index, data_type, "APPLICATION-ARRAY-ELEMENT", {tag})
    if tag == "APPLICATION-RECORD-DATA-TYPE":
        return owned(index, data_type, "APPLICATION-RECORD-ELEMENT", {tag})
    if tag == "IMPLEMENTATION-DATA-TYPE":
        return owned(index, data_type, "IMPLEMENTATION-DATA-TYPE-ELEMENT", {tag, "IMPLEMENTATION-DATA-TYPE-ELEMENT"})
    return []


def _element_type(index: ArxmlIndex, element: etree._Element, report: PluginReport) -> etree._Element | None:
    return resolve(index, first(element, {"TYPE-TREF", "IMPLEMENTATION-DATA-TYPE-REF"}), report, "data type element type", required=False)


def impl_types_compatible(index: ArxmlIndex, left: etree._Element, right: etree._Element, report: PluginReport, seen: set[tuple[int, int]]) -> bool | None:
    left = unwrap_impl(index, left, report)
    right = unwrap_impl(index, right, report)
    if left is None or right is None:
        return None
    marker = (id(left), id(right))
    if marker in seen:
        return True
    seen.add(marker)
    left_category = text(direct(left, "CATEGORY"))
    right_category = text(direct(right, "CATEGORY"))
    if left_category != right_category:
        return False
    if sw_data_def_props_compatible(index, props(left), props(right), report) is not True:
        return False
    left_children = _type_children(index, left)
    right_children = _type_children(index, right)
    if len(left_children) != len(right_children):
        return False
    for left_element, right_element in zip(left_children, right_children):
        ignored_element_type = DOC_TAGS | {"TYPE-TREF", "IMPLEMENTATION-DATA-TYPE-REF"}
        if canonical(left_element, ignored=ignored_element_type) != canonical(right_element, ignored=ignored_element_type):
            return False
        for tag in {"ARRAY-SIZE", "ARRAY-SIZE-SEMANTICS", "ARRAY-SIZE-HANDLING", "CATEGORY"}:
            if text(first(left_element, {tag})) != text(first(right_element, {tag})):
                return False
        left_type = _element_type(index, left_element, report)
        right_type = _element_type(index, right_element, report)
        if left_type is None or right_type is None:
            # Inline implementation elements are compared structurally below.
            if canonical(left_element, ignored=DOC_TAGS | {"SHORT-NAME"}) != canonical(right_element, ignored=DOC_TAGS | {"SHORT-NAME"}):
                return False
            continue
        if data_types_compatible(index, left_type, right_type, report, seen) is not True:
            return False
    return True


def app_types_compatible(index: ArxmlIndex, left: etree._Element, right: etree._Element, report: PluginReport, seen: set[tuple[int, int]]) -> bool | None:
    marker = (id(left), id(right))
    if marker in seen:
        return True
    seen.add(marker)
    if local_name(left.tag) != local_name(right.tag) or text(direct(left, "CATEGORY")) != text(direct(right, "CATEGORY")):
        return False
    if sw_data_def_props_compatible(index, props(left), props(right), report) is not True:
        return False
    left_children = _type_children(index, left)
    right_children = _type_children(index, right)
    if len(left_children) != len(right_children):
        return False
    for left_element, right_element in zip(left_children, right_children):
        if local_name(left.tag) == "APPLICATION-ARRAY-DATA-TYPE":
            for tag in {"MAX-NUMBER-OF-ELEMENTS", "ARRAY-SIZE-SEMANTICS"}:
                if text(first(left_element, {tag})) != text(first(right_element, {tag})):
                    return False
        # Application composite compatibility is positional and type-based; element
        # short names and descriptive metadata do not participate in constr_1048/1049.
        left_type = _element_type(index, left_element, report)
        right_type = _element_type(index, right_element, report)
        if left_type is None or right_type is None:
            report.incomplete(f"application data type element lacks a resolvable TYPE-TREF at {index.location(left_element if left_type is None else right_element)}")
            return None
        if data_types_compatible(index, left_type, right_type, report, seen) is not True:
            return False
    return True


def app_impl_compatible(index: ArxmlIndex, app: etree._Element, impl: etree._Element, report: PluginReport, seen: set[tuple[int, int]]) -> bool | None:
    impl = unwrap_impl(index, impl, report)
    if impl is None:
        return None
    app_category = text(direct(app, "CATEGORY"))
    impl_category = text(direct(impl, "CATEGORY"))
    allowed = {
        "VALUE": {"VALUE"}, "BOOLEAN": {"VALUE"}, "STRING": {"VALUE", "ARRAY"},
        "ARRAY": {"ARRAY"}, "VAL_BLK": {"ARRAY"}, "STRUCTURE": {"STRUCTURE"},
        "COM_AXIS": {"STRUCTURE", "ARRAY"}, "RES_AXIS": {"STRUCTURE", "ARRAY"},
        "CURVE": {"STRUCTURE", "ARRAY"}, "MAP": {"STRUCTURE", "ARRAY"},
        "CUBOID": {"STRUCTURE", "ARRAY"}, "CUBE_4": {"STRUCTURE", "ARRAY"}, "CUBE_5": {"STRUCTURE", "ARRAY"},
    }
    if impl_category in {"UNION", "DATA_REFERENCE", "FUNCTION_REFERENCE"}:
        return False
    if app_category not in allowed or impl_category not in allowed[app_category]:
        return False
    app_children = _type_children(index, app)
    impl_children = _type_children(index, impl)
    if app_category == "ARRAY" and app_children:
        if len(impl_children) != 1:
            return False
        app_element_type = _element_type(index, app_children[0], report)
        impl_element_type = _element_type(index, impl_children[0], report)
        if app_element_type is None or impl_element_type is None:
            report.incomplete(f"array element type is not resolvable at {index.location(app_children[0] if app_element_type is None else impl_children[0])}")
            return None
        if text(first(app_children[0], {"MAX-NUMBER-OF-ELEMENTS"})) != text(first(impl_children[0], {"ARRAY-SIZE"})):
            return False
        return data_types_compatible(index, app_element_type, impl_element_type, report, seen)
    if app_category == "STRUCTURE" and app_children:
        if len(app_children) != len(impl_children):
            return False
        for app_element, impl_element in zip(app_children, impl_children):
            app_element_type = _element_type(index, app_element, report)
            impl_element_type = _element_type(index, impl_element, report)
            if app_element_type is None or impl_element_type is None:
                report.incomplete(f"record element type is not resolvable at {index.location(app_element if app_element_type is None else impl_element)}")
                return None
            if data_types_compatible(index, app_element_type, impl_element_type, report, seen) is not True:
                return False
    return True


def data_types_compatible(index: ArxmlIndex, left: etree._Element, right: etree._Element, report: PluginReport, seen: set[tuple[int, int]] | None = None) -> bool | None:
    seen = seen or set()
    left_tag = local_name(left.tag)
    right_tag = local_name(right.tag)
    if left_tag in APP_TYPES and right_tag in APP_TYPES:
        return app_types_compatible(index, left, right, report, seen)
    if left_tag == "IMPLEMENTATION-DATA-TYPE" and right_tag == "IMPLEMENTATION-DATA-TYPE":
        return impl_types_compatible(index, left, right, report, seen)
    if left_tag in APP_TYPES and right_tag == "IMPLEMENTATION-DATA-TYPE":
        return app_impl_compatible(index, left, right, report, seen)
    if right_tag in APP_TYPES and left_tag == "IMPLEMENTATION-DATA-TYPE":
        return app_impl_compatible(index, right, left, report, seen)
    report.incomplete(f"unsupported data type compatibility pair {left_tag}/{right_tag}")
    return None


def prototypes_compatible(index: ArxmlIndex, left: etree._Element, right: etree._Element, report: PluginReport, *, require_name: bool = True) -> bool | None:
    if require_name and short_name(left) != short_name(right):
        return False
    left_policy = text(first(left, {"SW-IMPL-POLICY"}))
    right_policy = text(first(right, {"SW-IMPL-POLICY"}))
    if "QUEUED" in {left_policy.upper(), right_policy.upper()} and left_policy != right_policy:
        return False
    left_type = type_of(index, left, report)
    right_type = type_of(index, right, report)
    if left_type is None or right_type is None:
        return None
    return data_types_compatible(index, left_type, right_type, report)


def interface(index: ArxmlIndex, port: etree._Element, report: PluginReport) -> etree._Element | None:
    return resolve(index, first(port, INTERFACE_REF_TAGS), report, "PortPrototype interface")


def interface_members(index: ArxmlIndex, interface_element: etree._Element, tags: set[str] | None = None) -> list[etree._Element]:
    tags = tags or INTERFACE_MEMBERS
    return [
        item for item in interface_element.iterdescendants()
        if local_name(item.tag) in tags
        and index.nearest(index.parent.get(item), {local_name(interface_element.tag)}) is interface_element
    ]


def mapping_pairs(index: ArxmlIndex, mapping: etree._Element, report: PluginReport) -> set[tuple[int, int]]:
    result: set[tuple[int, int]] = set()
    pair_tags = {
        "DATA-ELEMENT-MAPPING", "VARIABLE-DATA-PROTOTYPE-MAPPING", "PARAMETER-DATA-PROTOTYPE-MAPPING",
        "MODE-DECLARATION-GROUP-PROTOTYPE-MAPPING", "CLIENT-SERVER-OPERATION-MAPPING",
        "CLIENT-SERVER-APPLICATION-ERROR-MAPPING", "TRIGGER-MAPPING", "SUB-ELEMENT-MAPPING",
    }
    for pair in [item for item in mapping.iterdescendants() if local_name(item.tag) in pair_tags]:
        targets: list[etree._Element] = []
        for ref in pair.iterdescendants():
            if not local_name(ref.tag).endswith("-REF") or not text(ref):
                continue
            target = resolve(index, ref, report, "PortInterfaceMapping member")
            if target is not None and local_name(target.tag) in INTERFACE_MEMBERS and all(target is not item for item in targets):
                targets.append(target)
        if len(targets) == 2:
            result.add((id(targets[0]), id(targets[1])))
            result.add((id(targets[1]), id(targets[0])))
    return result


def mode_group_signature(index: ArxmlIndex, group: etree._Element, report: PluginReport) -> object | None:
    modes = owned(index, group, "MODE-DECLARATION", {"MODE-DECLARATION-GROUP"})
    mode_values = []
    for mode in modes:
        mode_values.append((short_name(mode), text(direct(mode, "VALUE"))))
    initial = resolve(index, first(group, {"INITIAL-MODE-REF"}), report, "initial mode", required=False)
    defaults: list[str | None] = []
    policies: list[str] = []
    for behavior_tag in {"MODE-USER-ERROR-BEHAVIOR", "MODE-MANAGER-ERROR-BEHAVIOR"}:
        behavior = first(group, {behavior_tag})
        policies.append(text(first(behavior, {"ERROR-REACTION-POLICY"})) if behavior is not None else "")
        default = resolve(index, first(behavior, {"DEFAULT-MODE-REF"}), report, f"{behavior_tag} default mode", required=False) if behavior is not None else None
        defaults.append(short_name(default) if default is not None else None)
    category = text(direct(group, "CATEGORY"))
    on_transition = text(first(group, {"ON-TRANSITION-VALUE"}))
    return (
        tuple(sorted(mode_values if category == "EXPLICIT_ORDER" else [(name, "") for name, _ in mode_values])),
        short_name(initial) if initial is not None else None,
        tuple(policies), tuple(defaults), category, on_transition if category == "EXPLICIT_ORDER" else "",
    )


def mode_groups_compatible(index: ArxmlIndex, left: etree._Element, right: etree._Element, report: PluginReport) -> bool | None:
    if mode_group_signature(index, left, report) == mode_group_signature(index, right, report):
        return True
    for mapping in index.elements("MODE-DECLARATION-MAPPING"):
        targets = [resolve(index, ref, report, "ModeDeclarationMapping endpoint") for ref in mapping.iterdescendants() if local_name(ref.tag).endswith("-REF")]
        owners = {id(index.nearest(item, {"MODE-DECLARATION-GROUP"})) for item in targets if item is not None}
        if {id(left), id(right)} <= owners:
            return True
    return False


def arguments_compatible(index: ArxmlIndex, left: etree._Element, right: etree._Element, report: PluginReport) -> bool | None:
    if text(first(left, {"DIRECTION"})) != text(first(right, {"DIRECTION"})):
        return False
    return prototypes_compatible(index, left, right, report, require_name=False)


def errors_compatible(left: etree._Element, right: etree._Element) -> bool:
    return short_name(left) == short_name(right) and text(first(left, {"ERROR-CODE"})) == text(first(right, {"ERROR-CODE"}))


def operation_errors(index: ArxmlIndex, operation: etree._Element, report: PluginReport) -> list[etree._Element]:
    result: list[etree._Element] = []
    for ref in operation.iterdescendants():
        if local_name(ref.tag) not in {"POSSIBLE-ERROR-REF", "APPLICATION-ERROR-REF"}:
            continue
        target = resolve(index, ref, report, "ClientServerOperation possibleError")
        if target is not None and local_name(target.tag) == "APPLICATION-ERROR" and all(target is not item for item in result):
            result.append(target)
    # Some schema variants inline error declarations below the operation.
    for item in owned(index, operation, "APPLICATION-ERROR", {"CLIENT-SERVER-OPERATION"}):
        if all(item is not target for target in result):
            result.append(item)
    return result


def operations_compatible(index: ArxmlIndex, required: etree._Element, provided: etree._Element, report: PluginReport) -> bool | None:
    if short_name(required) != short_name(provided):
        return False
    required_args = owned(index, required, "ARGUMENT-DATA-PROTOTYPE", {"CLIENT-SERVER-OPERATION"})
    provided_args = owned(index, provided, "ARGUMENT-DATA-PROTOTYPE", {"CLIENT-SERVER-OPERATION"})
    if len(required_args) != len(provided_args):
        return False
    for left, right in zip(required_args, provided_args):
        if arguments_compatible(index, left, right, report) is not True:
            return False
    required_errors = operation_errors(index, required, report)
    provided_errors = operation_errors(index, provided, report)
    return all(any(errors_compatible(provider_error, required_error) for required_error in required_errors) for provider_error in provided_errors)

