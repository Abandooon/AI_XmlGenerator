"""Executable Variable-Size Array profile rules for AUTOSAR application/implementation types."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from lxml import etree

from .arxml_index import ArxmlIndex, local_name
from .plugins import PluginReport, plugin


def _text(element: etree._Element | None) -> str:
    return (element.text or "").strip() if element is not None else ""


def _token(element: etree._Element | None) -> str:
    return "".join(character for character in _text(element).upper() if character.isalnum())


def _direct(element: etree._Element, tag: str) -> etree._Element | None:
    return next((child for child in element if local_name(child.tag) == tag), None)


def _first(element: etree._Element, tags: set[str]) -> etree._Element | None:
    return next((item for item in element.iterdescendants() if local_name(item.tag) in tags), None)


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


def _resolve(index: ArxmlIndex, ref: etree._Element | None, report: PluginReport, label: str) -> etree._Element | None:
    if ref is None:
        report.incomplete(f"missing {label}")
        return None
    result = index.resolve(ref)
    if result.status != "resolved" or result.element is None:
        report.incomplete(f"{result.status} {label} {result.reference} at {index.location(ref)}")
        return None
    return result.element


def _repair(action: str, target: str, instruction: str, **values: object) -> dict:
    return {"action": action, "target": target, "instruction": instruction, **values}


def _decimal(element: etree._Element | None, report: PluginReport, index: ArxmlIndex, label: str) -> Decimal | None:
    if element is None:
        return None
    values = [_text(element)] if _text(element) else [
        _text(item) for item in element.iterdescendants()
        if local_name(item.tag) in {"VALUE", "V"} and _text(item)
    ]
    values = list(dict.fromkeys(values))
    if len(values) != 1:
        report.incomplete(f"{label} is variant or unbound at {index.location(element)}")
        return None
    try:
        return Decimal(values[0])
    except InvalidOperation:
        report.incomplete(f"{label} is non-numeric at {index.location(element)}")
        return None


def _app_elements(index: ArxmlIndex, data_type: etree._Element) -> list[etree._Element]:
    return _owned(index, data_type, "APPLICATION-ARRAY-ELEMENT", {"APPLICATION-ARRAY-DATA-TYPE"})


def _impl_elements(index: ArxmlIndex, owner: etree._Element) -> list[etree._Element]:
    return _owned(
        index, owner, "IMPLEMENTATION-DATA-TYPE-ELEMENT",
        {"IMPLEMENTATION-DATA-TYPE", "IMPLEMENTATION-DATA-TYPE-ELEMENT"},
    )


def _type_of(index: ArxmlIndex, element: etree._Element, report: PluginReport) -> etree._Element | None:
    ref = _first(element, {"TYPE-TREF"})
    if ref is None and local_name(element.tag) == "IMPLEMENTATION-DATA-TYPE-ELEMENT":
        ref = _first(element, {"IMPLEMENTATION-DATA-TYPE-REF"})
    return _resolve(index, ref, report, f"{local_name(element.tag)} type")


def _expect(
    index: ArxmlIndex,
    report: PluginReport,
    element: etree._Element,
    tag: str,
    expected: str | None,
    *,
    present: bool | None = None,
) -> bool:
    child = _direct(element, tag)
    valid = (child is not None) if present is True else (child is None) if present is False else _token(child) == _token_value(expected)
    if not valid:
        report.fail(
            index, child if child is not None else element,
            f"VSA profile requires {tag} {('present' if present else 'absent') if present is not None else expected}",
            actual=_text(child) if child is not None else None, expected=expected if present is None else {"present": present},
            repair=_repair("add_remove_or_replace", tag, "Align this property with the active VSA profile."),
        )
    return valid


def _token_value(value: str | None) -> str:
    return "".join(character for character in (value or "").upper() if character.isalnum())


def _application_chain(
    index: ArxmlIndex, root: etree._Element, report: PluginReport
) -> list[tuple[etree._Element, etree._Element, etree._Element]] | None:
    result: list[tuple[etree._Element, etree._Element, etree._Element]] = []
    current = root
    seen: set[int] = set()
    while local_name(current.tag) == "APPLICATION-ARRAY-DATA-TYPE":
        if id(current) in seen:
            report.incomplete(f"ApplicationArrayDataType cycle at {index.location(current)}")
            return None
        seen.add(id(current))
        elements = _app_elements(index, current)
        if len(elements) != 1:
            report.incomplete(f"expected exactly one ApplicationArrayElement at {index.location(current)}, found {len(elements)}")
            return None
        target = _type_of(index, elements[0], report)
        if target is None:
            return None
        result.append((current, elements[0], target))
        if local_name(target.tag) != "APPLICATION-ARRAY-DATA-TYPE":
            break
        current = target
    return result


@plugin("application_vsa_profile")
def application_vsa_profile(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_1314..1317: exact ApplicationArrayDataType profile chain shapes."""
    report = PluginReport(checked=len(selected))
    profiles = {
        "constr_1314": "VSA_LINEAR", "constr_1315": "VSA_SQUARE",
        "constr_1316": "VSA_RECTANGULAR", "constr_1317": "VSA_FULLY_FLEXIBLE",
    }
    expected_profile = profiles[rule["constraint_id"]]
    for root in selected:
        if _token(_direct(root, "DYNAMIC-ARRAY-SIZE-PROFILE")) != _token_value(expected_profile):
            continue
        chain = _application_chain(index, root, report)
        if not chain:
            continue
        if expected_profile == "VSA_LINEAR":
            if len(chain) != 1 or local_name(chain[0][2].tag) == "APPLICATION-ARRAY-DATA-TYPE" or _direct(chain[0][2], "DYNAMIC-ARRAY-SIZE-PROFILE") is not None:
                report.fail(index, chain[0][1], "VSA_LINEAR must terminate after one dimension in a non-profiled non-array type",
                            repair=_repair("repair_reference", "TYPE-TREF", "Reference a terminal non-profiled ApplicationDataType."))
            _expect(index, report, chain[0][1], "ARRAY-SIZE-SEMANTICS", "VARIABLE-SIZE")
            _expect(index, report, chain[0][1], "MAX-NUMBER-OF-ELEMENTS", None, present=True)
            _expect(index, report, chain[0][1], "ARRAY-SIZE-HANDLING", "ALL-INDICES-SAME-ARRAY-SIZE")
            continue
        if len(chain) < 2 or local_name(chain[0][2].tag) != "APPLICATION-ARRAY-DATA-TYPE":
            report.fail(index, chain[0][1], f"{expected_profile} requires a multidimensional ApplicationArrayDataType chain",
                        repair=_repair("repair_reference", "TYPE-TREF", "Reference a nested ApplicationArrayDataType."))
        for position, (_, element, target) in enumerate(chain):
            terminal = position == len(chain) - 1
            _expect(index, report, element, "ARRAY-SIZE-SEMANTICS", "VARIABLE-SIZE")
            if expected_profile == "VSA_SQUARE":
                _expect(index, report, element, "MAX-NUMBER-OF-ELEMENTS", None, present=terminal)
                _expect(index, report, element, "ARRAY-SIZE-HANDLING", "ALL-INDICES-SAME-ARRAY-SIZE" if terminal else "INHERITED-FROM-ARRAY-ELEMENT-TYPE-SIZE")
            elif expected_profile == "VSA_RECTANGULAR":
                _expect(index, report, element, "MAX-NUMBER-OF-ELEMENTS", None, present=True)
                _expect(index, report, element, "ARRAY-SIZE-HANDLING", "ALL-INDICES-SAME-ARRAY-SIZE")
            else:
                _expect(index, report, element, "MAX-NUMBER-OF-ELEMENTS", None, present=True)
                _expect(index, report, element, "ARRAY-SIZE-HANDLING", "ALL-INDICES-SAME-ARRAY-SIZE" if terminal else "ALL-INDICES-DIFFERENT-ARRAY-SIZE")
            if terminal and (local_name(target.tag) == "APPLICATION-ARRAY-DATA-TYPE" or _direct(target, "DYNAMIC-ARRAY-SIZE-PROFILE") is not None):
                report.fail(index, element, "VSA application chain does not terminate in a non-profiled non-array type",
                            repair=_repair("repair_reference", "TYPE-TREF", "Reference a terminal non-profiled ApplicationDataType."))
            if not terminal and local_name(target.tag) != "APPLICATION-ARRAY-DATA-TYPE":
                report.fail(index, element, "Intermediate VSA application dimension is not typed by ApplicationArrayDataType",
                            repair=_repair("repair_reference", "TYPE-TREF", "Reference the next ApplicationArrayDataType dimension."))
    return report


def _payload(index: ArxmlIndex, data_type: etree._Element, report: PluginReport) -> etree._Element | None:
    elements = _impl_elements(index, data_type)
    if len(elements) < 2:
        report.fail(index, data_type, "VSA ImplementationDataType requires a second payload subElement",
                    actual=len(elements), expected_at_least=2,
                    repair=_repair("add_element", "IMPLEMENTATION-DATA-TYPE-ELEMENT", "Add size-indicator and payload subElements."))
        return None
    return elements[1]


def _single_child(index: ArxmlIndex, element: etree._Element, report: PluginReport, label: str) -> etree._Element | None:
    children = _impl_elements(index, element)
    if len(children) != 1:
        report.fail(index, element, f"{label} requires exactly one nested ImplementationDataTypeElement",
                    actual=len(children), expected=1,
                    repair=_repair("set_child_cardinality", "IMPLEMENTATION-DATA-TYPE-ELEMENT", "Keep exactly one nested VSA dimension.", expected=1))
        return None
    return children[0]


def _outer_payload_shape(index: ArxmlIndex, report: PluginReport, payload: etree._Element) -> None:
    _expect(index, report, payload, "CATEGORY", "ARRAY")
    _expect(index, report, payload, "ARRAY-SIZE-SEMANTICS", None, present=False)
    _expect(index, report, payload, "ARRAY-SIZE", None, present=False)
    _expect(index, report, payload, "ARRAY-SIZE-HANDLING", None, present=False)


@plugin("implementation_vsa_profile")
def implementation_vsa_profile(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_1318..1321: exact payload aggregation chain per VSA profile."""
    report = PluginReport(checked=len(selected))
    profiles = {
        "constr_1318": "VSA_LINEAR", "constr_1319": "VSA_SQUARE",
        "constr_1320": "VSA_RECTANGULAR", "constr_1321": "VSA_FULLY_FLEXIBLE",
    }
    expected_profile = profiles[rule["constraint_id"]]
    for data_type in selected:
        if _token(_direct(data_type, "DYNAMIC-ARRAY-SIZE-PROFILE")) != _token_value(expected_profile):
            continue
        payload = _payload(index, data_type, report)
        if payload is None:
            continue
        _outer_payload_shape(index, report, payload)
        current = _single_child(index, payload, report, "VSA payload")
        seen: set[int] = set()
        depth = 0
        while current is not None:
            if id(current) in seen:
                report.incomplete(f"ImplementationDataTypeElement cycle at {index.location(current)}")
                break
            seen.add(id(current))
            depth += 1
            children = _impl_elements(index, current)
            terminal = not children
            if expected_profile == "VSA_LINEAR":
                _expect(index, report, current, "ARRAY-SIZE-SEMANTICS", "VARIABLE-SIZE")
                _expect(index, report, current, "ARRAY-SIZE", None, present=True)
                _expect(index, report, current, "ARRAY-SIZE-HANDLING", "ALL-INDICES-SAME-ARRAY-SIZE")
                if not terminal:
                    report.fail(index, current, "VSA_LINEAR payload must terminate after its first dimension",
                                repair=_repair("remove", "SUB-ELEMENTS", "Remove additional payload dimensions."))
                break
            if expected_profile == "VSA_SQUARE":
                _expect(index, report, current, "ARRAY-SIZE-SEMANTICS", "VARIABLE-SIZE")
                _expect(index, report, current, "ARRAY-SIZE", None, present=terminal)
                _expect(index, report, current, "ARRAY-SIZE-HANDLING", "ALL-INDICES-SAME-ARRAY-SIZE" if terminal else "INHERITED-FROM-ARRAY-ELEMENT-TYPE-SIZE")
                if not terminal:
                    _expect(index, report, current, "CATEGORY", "ARRAY")
            elif expected_profile == "VSA_RECTANGULAR":
                _expect(index, report, current, "ARRAY-SIZE-SEMANTICS", "VARIABLE-SIZE")
                _expect(index, report, current, "ARRAY-SIZE", None, present=True)
                _expect(index, report, current, "ARRAY-SIZE-HANDLING", "ALL-INDICES-SAME-ARRAY-SIZE")
                if not terminal:
                    _expect(index, report, current, "CATEGORY", "ARRAY")
            else:
                if depth % 2 == 1:
                    _expect(index, report, current, "ARRAY-SIZE-SEMANTICS", "VARIABLE-SIZE")
                    _expect(index, report, current, "CATEGORY", "STRUCTURE")
                    _expect(index, report, current, "ARRAY-SIZE", None, present=True)
                    _expect(index, report, current, "ARRAY-SIZE-HANDLING", "ALL-INDICES-DIFFERENT-ARRAY-SIZE")
                elif terminal:
                    _expect(index, report, current, "ARRAY-SIZE-SEMANTICS", "VARIABLE-SIZE")
                    _expect(index, report, current, "ARRAY-SIZE", None, present=True)
                    _expect(index, report, current, "ARRAY-SIZE-HANDLING", "ALL-INDICES-SAME-ARRAY-SIZE")
                else:
                    _expect(index, report, current, "CATEGORY", "ARRAY")
                    _expect(index, report, current, "ARRAY-SIZE-SEMANTICS", None, present=False)
                    _expect(index, report, current, "ARRAY-SIZE", None, present=False)
                    _expect(index, report, current, "ARRAY-SIZE-HANDLING", None, present=False)
            if terminal:
                break
            current = _single_child(index, current, report, "VSA dimension")
    return report


def _app_maxima(index: ArxmlIndex, app_type: etree._Element, report: PluginReport) -> list[Decimal] | None:
    chain = _application_chain(index, app_type, report)
    if not chain:
        return None
    result: list[Decimal] = []
    for _, element, _ in chain:
        value = _decimal(_direct(element, "MAX-NUMBER-OF-ELEMENTS"), report, index, "maxNumberOfElements")
        if value is None:
            return None
        result.append(value)
    return result


def _impl_dimension_nodes(index: ArxmlIndex, data_type: etree._Element, report: PluginReport) -> list[etree._Element] | None:
    payload = _payload(index, data_type, report)
    if payload is None:
        return None
    result: list[etree._Element] = []
    current = _single_child(index, payload, report, "VSA payload")
    seen: set[int] = set()
    while current is not None:
        if id(current) in seen:
            report.incomplete(f"ImplementationDataTypeElement cycle at {index.location(current)}")
            return None
        seen.add(id(current))
        size = _direct(current, "ARRAY-SIZE")
        if size is not None:
            result.append(current)
        children = _impl_elements(index, current)
        if not children:
            break
        if len(children) != 1:
            report.incomplete(f"ambiguous VSA payload branching at {index.location(current)}")
            return None
        current = children[0]
    return result


@plugin("vsa_payload_and_indicator_shape")
def vsa_payload_and_indicator_shape(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """TPS_SWCT_01619/01621/01648/01649: indicator/payload dimensions and sizes."""
    report = PluginReport(checked=len(selected))
    cid = rule["constraint_id"]
    pairs: list[tuple[etree._Element | None, etree._Element]] = []
    if cid in {"TPS_SWCT_01619", "TPS_SWCT_01621"}:
        for mapping in selected:
            app = _resolve(index, _first(mapping, {"APPLICATION-DATA-TYPE-REF"}), report, "mapped ApplicationArrayDataType")
            impl = _resolve(index, _first(mapping, {"IMPLEMENTATION-DATA-TYPE-REF"}), report, "mapped VSA ImplementationDataType")
            if app is not None and impl is not None and _direct(app, "DYNAMIC-ARRAY-SIZE-PROFILE") is not None:
                pairs.append((app, impl))
    else:
        pairs = [(None, item) for item in selected if _direct(item, "DYNAMIC-ARRAY-SIZE-PROFILE") is not None]
    for app, impl in pairs:
        elements = _impl_elements(index, impl)
        if len(elements) < 2:
            report.fail(index, impl, "VSA implementation type requires size indicator and payload",
                        actual=len(elements), expected_at_least=2,
                        repair=_repair("add_element", "IMPLEMENTATION-DATA-TYPE-ELEMENT", "Add the missing VSA subElement."))
            continue
        indicator, payload = elements[0], elements[1]
        if cid == "TPS_SWCT_01649":
            _expect(index, report, payload, "CATEGORY", "ARRAY")
            continue
        impl_dims = _impl_dimension_nodes(index, impl, report)
        if impl_dims is None:
            continue
        if cid == "TPS_SWCT_01648":
            if _token(_direct(impl, "DYNAMIC-ARRAY-SIZE-PROFILE")) != _token_value("VSA_RECTANGULAR"):
                continue
            _expect(index, report, indicator, "CATEGORY", "ARRAY")
            size = _decimal(_direct(indicator, "ARRAY-SIZE"), report, index, "indicator arraySize")
            if size is not None and size != len(impl_dims):
                report.fail(index, indicator, "Rectangular VSA indicator arraySize differs from payload dimension count",
                            actual=str(size), expected=len(impl_dims),
                            repair=_repair("replace_value", "ARRAY-SIZE", "Use the number of payload dimensions.", expected=len(impl_dims)))
            continue
        maxima = _app_maxima(index, app, report) if app is not None else None
        if maxima is None:
            continue
        if cid == "TPS_SWCT_01619":
            if _token(_direct(app, "DYNAMIC-ARRAY-SIZE-PROFILE")) != _token_value("VSA_RECTANGULAR"):
                continue
            _expect(index, report, indicator, "CATEGORY", "ARRAY")
            size = _decimal(_direct(indicator, "ARRAY-SIZE"), report, index, "indicator arraySize")
            if size is not None and size != len(maxima):
                report.fail(index, indicator, "Rectangular VSA indicator arraySize differs from application dimension count",
                            actual=str(size), expected=len(maxima),
                            repair=_repair("replace_value", "ARRAY-SIZE", "Use the application array dimension count.", expected=len(maxima)))
        else:
            _expect(index, report, payload, "CATEGORY", "ARRAY")
            sizes = [_decimal(_direct(item, "ARRAY-SIZE"), report, index, "payload arraySize") for item in impl_dims]
            grounded = [item for item in sizes if item is not None]
            if len(grounded) == len(sizes) and grounded != maxima:
                report.fail(index, payload, "VSA payload arraySize sequence differs from application maxArraySize sequence",
                            actual=[str(item) for item in grounded], expected=[str(item) for item in maxima],
                            repair=_repair("align_structure", "ARRAY-SIZE", "Match each payload dimension to maxNumberOfElements of the application type."))
    return report


def _indicator_capacity(index: ArxmlIndex, indicator: etree._Element, report: PluginReport) -> Decimal | None:
    ref = _first(indicator, {"TYPE-TREF", "IMPLEMENTATION-DATA-TYPE-REF"})
    data_type = _resolve(index, ref, report, "size indicator type") if ref is not None else None
    subject = data_type if data_type is not None else indicator
    category = _text(_direct(subject, "CATEGORY")) or _text(_direct(indicator, "CATEGORY"))
    if category == "TYPE_REFERENCE" and data_type is not None:
        target = _resolve(index, _first(data_type, {"IMPLEMENTATION-DATA-TYPE-REF"}), report, "indicator TYPE_REFERENCE target")
        if target is None:
            return None
        subject = target
        category = _text(_direct(subject, "CATEGORY"))
    if category != "VALUE":
        report.fail(index, indicator, "VSA size indicator is not an integer VALUE type",
                    actual_category=category,
                    repair=_repair("repair_reference", "IMPLEMENTATION-DATA-TYPE-REF", "Use an integer VALUE implementation type."))
        return None
    upper = _first(subject, {"UPPER-LIMIT"})
    if upper is not None:
        return _decimal(upper, report, index, "indicator upper limit")
    base = _resolve(index, _first(subject, {"BASE-TYPE-REF"}), report, "indicator SwBaseType")
    if base is None:
        return None
    bits = _decimal(_first(base, {"BASE-TYPE-SIZE", "MAX-BASE-TYPE-SIZE"}), report, index, "indicator base type size")
    encoding = _token(_first(base, {"BASE-TYPE-ENCODING"}))
    if bits is None or bits != bits.to_integral_value() or bits <= 0:
        return None
    if encoding in {_token_value("2C"), _token_value("SIGNED")}:
        return Decimal(2) ** (int(bits) - 1) - 1
    if encoding in {_token_value("UNSIGNED"), _token_value("BCD")}:
        return Decimal(2) ** int(bits) - 1
    report.incomplete(f"cannot prove signedness/capacity for baseTypeEncoding {_text(_first(base, {'BASE-TYPE-ENCODING'}))!r} at {index.location(base)}")
    return None


@plugin("vsa_indicator_capacity")
def vsa_indicator_capacity(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """TPS_SWCT_01618/01620/01647: grounded size indicator capacity covers maxima."""
    report = PluginReport(checked=len(selected))
    cid = rule["constraint_id"]
    pairs: list[tuple[etree._Element | None, etree._Element]] = []
    if cid in {"TPS_SWCT_01618", "TPS_SWCT_01620"}:
        for mapping in selected:
            app = _resolve(index, _first(mapping, {"APPLICATION-DATA-TYPE-REF"}), report, "mapped ApplicationArrayDataType")
            impl = _resolve(index, _first(mapping, {"IMPLEMENTATION-DATA-TYPE-REF"}), report, "mapped VSA ImplementationDataType")
            if app is not None and impl is not None:
                pairs.append((app, impl))
    else:
        pairs = [(None, item) for item in selected]
    for app, impl in pairs:
        profile = _token(_direct(app if app is not None else impl, "DYNAMIC-ARRAY-SIZE-PROFILE"))
        scalar_profiles = {_token_value("VSA_LINEAR"), _token_value("VSA_SQUARE"), _token_value("VSA_FULLY_FLEXIBLE")}
        if cid in {"TPS_SWCT_01618", "TPS_SWCT_01647"} and profile not in scalar_profiles:
            continue
        if cid == "TPS_SWCT_01620" and profile != _token_value("VSA_RECTANGULAR"):
            continue
        elements = _impl_elements(index, impl)
        if not elements:
            report.fail(index, impl, "VSA implementation type has no size indicator",
                        repair=_repair("add_element", "IMPLEMENTATION-DATA-TYPE-ELEMENT", "Add the size indicator as first subElement."))
            continue
        maxima = _app_maxima(index, app, report) if app is not None else None
        if maxima is None:
            dims = _impl_dimension_nodes(index, impl, report)
            maxima = [_decimal(_direct(item, "ARRAY-SIZE"), report, index, "payload arraySize") for item in dims or []]
            if not maxima or any(item is None for item in maxima):
                continue
            maxima = [item for item in maxima if item is not None]
        indicators = _impl_elements(index, elements[0]) if cid == "TPS_SWCT_01620" else [elements[0]]
        required = maxima if cid == "TPS_SWCT_01620" else [max(maxima)]
        if len(indicators) != len(required):
            report.fail(index, elements[0], "VSA size-indicator cardinality differs from dimension count",
                        actual=len(indicators), expected=len(required),
                        repair=_repair("set_child_cardinality", "IMPLEMENTATION-DATA-TYPE-ELEMENT", "Provide one integer indicator per rectangular dimension.", expected=len(required)))
            continue
        for indicator, maximum in zip(indicators, required):
            capacity = _indicator_capacity(index, indicator, report)
            if capacity is not None and capacity < maximum:
                report.fail(index, indicator, "VSA size indicator cannot represent the maximum valid element count",
                            capacity=str(capacity), required=str(maximum),
                            repair=_repair("repair_reference", "BASE-TYPE-REF", "Use an integer type with sufficient upper range."))
    return report
