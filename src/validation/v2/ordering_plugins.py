"""Executable precedence semantics for AUTOSAR properties and initial values.

These rules define interpretation rather than forbidding lower-priority values.
The validators therefore emit deterministic ``observations`` for the effective
source/value and fail closed when a reference or variation branch is ambiguous.
TPS_SWCT_01256 is the exception: it also has a concrete array-shape invariant.
"""

from __future__ import annotations

from lxml import etree

from .arxml_index import ArxmlIndex, local_name
from .plugins import PluginReport, plugin

DATA_PROTOTYPES = {
    "VARIABLE-DATA-PROTOTYPE", "PARAMETER-DATA-PROTOTYPE", "ARGUMENT-DATA-PROTOTYPE",
    "APPLICATION-ARRAY-ELEMENT", "APPLICATION-RECORD-ELEMENT",
}
APP_TYPES = {
    "APPLICATION-PRIMITIVE-DATA-TYPE", "APPLICATION-ARRAY-DATA-TYPE",
    "APPLICATION-RECORD-DATA-TYPE",
}
VALUE_SPECS = {
    "APPLICATION-VALUE-SPECIFICATION", "APPLICATION-RULE-BASED-VALUE-SPECIFICATION",
    "ARRAY-VALUE-SPECIFICATION", "NUMERICAL-RULE-BASED-VALUE-SPECIFICATION",
    "NUMERICAL-VALUE-SPECIFICATION", "RECORD-VALUE-SPECIFICATION",
    "REFERENCE-VALUE-SPECIFICATION", "TEXT-VALUE-SPECIFICATION", "CONSTANT-REFERENCE",
}
PROPERTY_TAGS = {
    "UNIT-REF", "COMPU-METHOD-REF", "DATA-CONSTR-REF", "SW-ADDR-METHOD-REF",
    "SW-CALIBRATION-ACCESS", "DISPLAY-FORMAT", "SW-IMPL-POLICY",
    "SW-RECORD-LAYOUT-REF", "INVALID-VALUE", "BASE-TYPE-REF",
}


def _text(element: etree._Element | None) -> str:
    return (element.text or "").strip() if element is not None else ""


def _direct(element: etree._Element, tag: str) -> etree._Element | None:
    return next((child for child in element if local_name(child.tag) == tag), None)


def _first(element: etree._Element, tags: set[str]) -> etree._Element | None:
    return next((item for item in element.iterdescendants() if local_name(item.tag) in tags), None)


def _resolve(index: ArxmlIndex, ref: etree._Element | None, report: PluginReport, label: str) -> etree._Element | None:
    if ref is None:
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


def _props(owner: etree._Element) -> etree._Element | None:
    return _first(owner, {"SW-DATA-DEF-PROPS"})


def _property_values(props: etree._Element | None, tag: str) -> list[etree._Element]:
    if props is None:
        return []
    values: list[etree._Element] = []
    for item in props.iterdescendants():
        if local_name(item.tag) != tag:
            continue
        nested_props = next(
            (ancestor for ancestor in item.iterancestors()
             if ancestor is not props and local_name(ancestor.tag) == "SW-DATA-DEF-PROPS"),
            None,
        )
        if nested_props is None:
            values.append(item)
    return values


def _token(index: ArxmlIndex, value: etree._Element, report: PluginReport) -> object | None:
    tag = local_name(value.tag)
    if tag.endswith(("-REF", "-TREF")):
        target = _resolve(index, value, report, tag)
        return index.path_of(target) if target is not None else None
    if tag == "INVALID-VALUE":
        spec = next((item for item in value.iterdescendants() if local_name(item.tag) in VALUE_SPECS), None)
        if spec is None:
            report.incomplete(f"INVALID-VALUE has no ValueSpecification at {index.location(value)}")
            return None
        return etree.tostring(spec, method="c14n", with_comments=False).decode("utf-8")
    return _text(value)


def _candidate(
    index: ArxmlIndex,
    report: PluginReport,
    owner: etree._Element | None,
    tag: str,
    source: str,
) -> tuple[str, object, dict] | None:
    if owner is None:
        return None
    props = owner if local_name(owner.tag) == "SW-DATA-DEF-PROPS" else _props(owner)
    values = _property_values(props, tag)
    if not values:
        return None
    tokens = [_token(index, item, report) for item in values]
    concrete = [item for item in tokens if item is not None]
    if not concrete:
        return None
    distinct = {repr(item) for item in concrete}
    if len(distinct) > 1:
        report.incomplete(
            f"variant-dependent {tag} has multiple values at {source} {index.location(owner)}"
        )
        return None
    return source, concrete[0], index.location(values[0])


def _observe_effective(
    index: ArxmlIndex,
    report: PluginReport,
    subject: etree._Element,
    property_name: str,
    candidates_low_to_high: list[tuple[str, object, dict] | None],
) -> None:
    candidates = [item for item in candidates_low_to_high if item is not None]
    if not candidates:
        return
    source, value, location = candidates[-1]
    report.observe(
        semantic="effective_property",
        constraint_property=property_name,
        subject=index.path_of(subject),
        effective_source=source,
        effective_value=value,
        source_location=location,
        shadowed_sources=[item[0] for item in candidates[:-1]],
    )


def _type_of(index: ArxmlIndex, prototype: etree._Element, report: PluginReport) -> etree._Element | None:
    ref = _first(prototype, {"TYPE-TREF"})
    if ref is None:
        report.incomplete(f"missing TYPE-TREF at {index.location(prototype)}")
        return None
    return _resolve(index, ref, report, "DataPrototype type")


def _mapped_impl(index: ArxmlIndex, app_type: etree._Element, report: PluginReport) -> etree._Element | None:
    results: list[etree._Element] = []
    for mapping in index.elements("DATA-TYPE-MAP"):
        app_ref = _first(mapping, {"APPLICATION-DATA-TYPE-REF"})
        resolution = index.resolve(app_ref) if app_ref is not None else None
        if resolution is None or resolution.status != "resolved" or resolution.element is not app_type:
            continue
        impl = _resolve(index, _first(mapping, {"IMPLEMENTATION-DATA-TYPE-REF"}), report, "mapped ImplementationDataType")
        if impl is not None and all(impl is not item for item in results):
            results.append(impl)
    if len(results) > 1:
        report.incomplete(f"multiple ImplementationDataTypes mapped to {index.path_of(app_type)}")
        return None
    return results[0] if results else None


@plugin("sw_data_def_props_precedence")
def sw_data_def_props_precedence(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """TPS_SWCT_01273: resolve application -> implementation -> prototype -> instance/access layers."""
    report = PluginReport(checked=len(selected))
    for prototype in index.select_any(sorted(DATA_PROTOTYPES)):
        if _props(prototype) is None and _first(prototype, {"INIT-VALUE"}) is None:
            continue
        data_type = _type_of(index, prototype, report)
        if data_type is None:
            continue
        app_type = data_type if local_name(data_type.tag) in APP_TYPES else None
        impl_type = data_type if local_name(data_type.tag) == "IMPLEMENTATION-DATA-TYPE" else (
            _mapped_impl(index, app_type, report) if app_type is not None else None
        )
        for tag in sorted(PROPERTY_TAGS):
            _observe_effective(index, report, prototype, tag, [
                _candidate(index, report, app_type, tag, "ApplicationDataType"),
                _candidate(index, report, impl_type, tag, "ImplementationDataType"),
                _candidate(index, report, prototype, tag, "DataPrototype"),
            ])
    # Higher instantiation/access layers are self-contained in the ARXML model.
    levels = [
        ("INSTANTIATION-DATA-DEF-PROPS", "InstantiationDataDefProps"),
        ("PARAMETER-ACCESS", "ParameterAccess/Argument"),
        ("FLAT-INSTANCE-DESCRIPTOR", "FlatInstanceDescriptor"),
        ("MC-DATA-INSTANCE", "McDataInstance"),
    ]
    for tag_name, label in levels:
        for owner in index.elements(tag_name):
            for tag in sorted(PROPERTY_TAGS):
                value = _candidate(index, report, owner, tag, label)
                if value is not None:
                    _observe_effective(index, report, owner, tag, [value])
    return report


def _referenced_props(index: ArxmlIndex, owner: etree._Element, ref_tags: set[str], report: PluginReport, label: str) -> etree._Element | None:
    target = _resolve(index, _first(owner, ref_tags), report, label)
    return _props(target) if target is not None else None


def _compu(index: ArxmlIndex, props: etree._Element | None, report: PluginReport, label: str) -> etree._Element | None:
    if props is None:
        return None
    return _resolve(index, _first(props, {"COMPU-METHOD-REF"}), report, label)


def _value_axis_sources(index: ArxmlIndex, props: etree._Element, report: PluginReport, property_tag: str) -> list[tuple[str, object, dict] | None]:
    value_type_props = _referenced_props(
        index, props, {"VALUE-AXIS-DATA-TYPE-REF", "VALUE-AXIS-DATA-TYPE-TREF"}, report,
        "valueAxisDataType",
    )
    value_compu = _compu(index, value_type_props, report, "valueAxisDataType CompuMethod")
    direct_compu = _compu(index, props, report, "SwDataDefProps CompuMethod")
    if property_tag == "UNIT-REF":
        return [
            _candidate(index, report, direct_compu, property_tag, "SwDataDefProps.compuMethod.unit"),
            _candidate(index, report, props, property_tag, "SwDataDefProps.unit"),
            _candidate(index, report, value_compu, property_tag, "valueAxisDataType.compuMethod.unit"),
            _candidate(index, report, value_type_props, property_tag, "valueAxisDataType.unit"),
        ]
    if property_tag == "DATA-CONSTR-REF":
        return [
            _candidate(index, report, value_type_props, property_tag, "valueAxisDataType.dataConstr"),
            _candidate(index, report, props, property_tag, "SwDataDefProps.dataConstr"),
        ]
    if property_tag == "COMPU-METHOD-REF":
        return [
            _candidate(index, report, props, property_tag, "SwDataDefProps.compuMethod"),
            _candidate(index, report, value_type_props, property_tag, "valueAxisDataType.compuMethod"),
        ]
    if property_tag == "DISPLAY-FORMAT":
        return [
            _candidate(index, report, direct_compu, property_tag, "SwDataDefProps.compuMethod.displayFormat"),
            _candidate(index, report, value_compu, property_tag, "valueAxisDataType.compuMethod.displayFormat"),
            _candidate(index, report, value_type_props, property_tag, "valueAxisDataType.displayFormat"),
            _candidate(index, report, props, property_tag, "SwDataDefProps.displayFormat"),
        ]
    return [
        _candidate(index, report, value_type_props, property_tag, f"valueAxisDataType.{property_tag}"),
        _candidate(index, report, props, property_tag, f"SwDataDefProps.{property_tag}"),
    ]


@plugin("value_axis_precedence")
def value_axis_precedence(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    property_by_rule = {
        "TPS_SWCT_01497": "UNIT-REF", "TPS_SWCT_01498": "DATA-CONSTR-REF",
        "TPS_SWCT_01499": "COMPU-METHOD-REF", "TPS_SWCT_01500": "DISPLAY-FORMAT",
        "TPS_SWCT_01501": "SW-CALIBRATION-ACCESS",
    }
    report = PluginReport(checked=len(selected))
    tag = property_by_rule[rule["constraint_id"]]
    for props in index.elements("SW-DATA-DEF-PROPS"):
        _observe_effective(index, report, props, tag, _value_axis_sources(index, props, report, tag))
    return report


def _axis_type_props(index: ArxmlIndex, axis: etree._Element, report: PluginReport) -> etree._Element | None:
    return _referenced_props(index, axis, {"INPUT-VARIABLE-TYPE-REF", "INPUT-VARIABLE-TYPE-TREF"}, report, "inputVariableType")


def _axis_variable_props(index: ArxmlIndex, axis: etree._Element, report: PluginReport) -> etree._Element | None:
    variable = _resolve(index, _first(axis, {"AUTOSAR-VARIABLE-REF", "TARGET-DATA-PROTOTYPE-REF"}), report, "axis variable")
    if variable is None:
        return None
    data_type = _type_of(index, variable, report)
    return _props(data_type) if data_type is not None else None


def _input_axis_sources(index: ArxmlIndex, axis: etree._Element, report: PluginReport, property_tag: str) -> list[tuple[str, object, dict] | None]:
    type_props = _axis_type_props(index, axis, report)
    variable_props = _axis_variable_props(index, axis, report)
    type_compu = _compu(index, type_props, report, "inputVariableType CompuMethod")
    variable_compu = _compu(index, variable_props, report, "axis variable CompuMethod")
    axis_compu = _resolve(index, _first(axis, {"COMPU-METHOD-REF"}), report, "axis CompuMethod")
    if property_tag == "UNIT-REF":
        return [
            _candidate(index, report, variable_props, property_tag, "swVariableRef.type.unit"),
            _candidate(index, report, variable_compu, property_tag, "swVariableRef.type.compuMethod.unit"),
            _candidate(index, report, type_props, property_tag, "inputVariableType.unit"),
            _candidate(index, report, axis_compu, property_tag, "axis.compuMethod.unit"),
            _candidate(index, report, axis, property_tag, "axis.unit"),
        ]
    if property_tag == "DATA-CONSTR-REF":
        return [
            _candidate(index, report, variable_props, property_tag, "swVariableRef.type.dataConstr"),
            _candidate(index, report, type_props, property_tag, "inputVariableType.dataConstr"),
            _candidate(index, report, axis, property_tag, "axis.dataConstr"),
        ]
    if property_tag == "DISPLAY-FORMAT":
        return [
            _candidate(index, report, variable_compu, property_tag, "swVariableRef.type.compuMethod.displayFormat"),
            _candidate(index, report, variable_props, property_tag, "swVariableRef.type.displayFormat"),
            _candidate(index, report, type_compu, property_tag, "inputVariableType.compuMethod.displayFormat"),
            _candidate(index, report, type_props, property_tag, "inputVariableType.displayFormat"),
            _candidate(index, report, axis_compu, property_tag, "axis.compuMethod.displayFormat"),
            _candidate(index, report, axis, property_tag, "axis.displayFormat"),
        ]
    return []


@plugin("input_axis_precedence")
def input_axis_precedence(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    tag_by_rule = {
        "TPS_SWCT_01502": "UNIT-REF", "TPS_SWCT_01503": "DATA-CONSTR-REF",
        "TPS_SWCT_01504": "DISPLAY-FORMAT",
    }
    report = PluginReport(checked=len(selected))
    tag = tag_by_rule[rule["constraint_id"]]
    axes = index.elements("SW-AXIS-INDIVIDUAL") if tag != "DISPLAY-FORMAT" else (
        index.elements("SW-CALPRM-AXIS") + index.elements("SW-AXIS-INDIVIDUAL")
    )
    for axis in axes:
        _observe_effective(index, report, axis, tag, _input_axis_sources(index, axis, report, tag))
    return report


@plugin("calibration_access_precedence")
def calibration_access_precedence(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for axis in index.elements("SW-CALPRM-AXIS"):
        owner_props = index.nearest(axis, {"SW-DATA-DEF-PROPS"})
        _observe_effective(index, report, axis, "SW-CALIBRATION-ACCESS", [
            _candidate(index, report, axis, "SW-CALIBRATION-ACCESS", "SwCalprmAxis.swCalibrationAccess"),
            _candidate(index, report, owner_props, "SW-CALIBRATION-ACCESS", "SwDataDefProps.swCalibrationAccess"),
        ])
    return report


@plugin("general_axis_precedence")
def general_axis_precedence(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """TPS_SWCT_01496: exercise each property-specific resolver on every applicable axis context."""
    report = PluginReport(checked=len(selected))
    for props in index.elements("SW-DATA-DEF-PROPS"):
        for tag in ("UNIT-REF", "DATA-CONSTR-REF", "COMPU-METHOD-REF", "DISPLAY-FORMAT", "SW-CALIBRATION-ACCESS"):
            _observe_effective(index, report, props, tag, _value_axis_sources(index, props, report, tag))
    for axis in index.elements("SW-AXIS-INDIVIDUAL"):
        for tag in ("UNIT-REF", "DATA-CONSTR-REF", "DISPLAY-FORMAT"):
            _observe_effective(index, report, axis, tag, _input_axis_sources(index, axis, report, tag))
    return report


def _array_chain(index: ArxmlIndex, data_type: etree._Element, report: PluginReport, application: bool) -> list[tuple[etree._Element, str, str]] | None:
    chain: list[tuple[etree._Element, str, str]] = []
    seen: set[int] = set()
    current = data_type
    while True:
        if id(current) in seen:
            report.incomplete(f"array type cycle at {index.location(current)}")
            return None
        seen.add(id(current))
        element_tag = "APPLICATION-ARRAY-ELEMENT" if application else "IMPLEMENTATION-DATA-TYPE-ELEMENT"
        children = _owned(index, current, element_tag, {local_name(current.tag), element_tag})
        if len(children) != 1:
            report.incomplete(f"array dimension requires exactly one {element_tag} at {index.location(current)}")
            return None
        element = children[0]
        size = _text(_first(element, {"MAX-NUMBER-OF-ELEMENTS" if application else "ARRAY-SIZE"}))
        semantics = _text(_first(element, {"ARRAY-SIZE-SEMANTICS"}))
        if not size:
            report.incomplete(f"array dimension size is missing at {index.location(element)}")
            return None
        chain.append((element, size, semantics))
        ref_tags = {"TYPE-TREF"} if application else {"IMPLEMENTATION-DATA-TYPE-REF"}
        ref = _first(element, ref_tags)
        if ref is None:
            break
        target = _resolve(index, ref, report, "nested array element type")
        if target is None:
            return None
        expected = "APPLICATION-ARRAY-DATA-TYPE" if application else "IMPLEMENTATION-DATA-TYPE"
        if local_name(target.tag) != expected or (not application and _text(_direct(target, "CATEGORY")) != "ARRAY"):
            break
        current = target
    return chain


@plugin("array_dimension_mapping_order")
def array_dimension_mapping_order(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for mapping in index.elements("DATA-TYPE-MAP"):
        app = _resolve(index, _first(mapping, {"APPLICATION-DATA-TYPE-REF"}), report, "mapped ApplicationDataType")
        impl = _resolve(index, _first(mapping, {"IMPLEMENTATION-DATA-TYPE-REF"}), report, "mapped ImplementationDataType")
        if app is None or impl is None or local_name(app.tag) != "APPLICATION-ARRAY-DATA-TYPE":
            continue
        if local_name(impl.tag) != "IMPLEMENTATION-DATA-TYPE" or _text(_direct(impl, "CATEGORY")) != "ARRAY":
            report.fail(index, mapping, "Application array is not mapped to an ImplementationDataType of category ARRAY",
                        repair=_repair("repair_reference", "IMPLEMENTATION-DATA-TYPE-REF", "Reference the corresponding ARRAY ImplementationDataType."))
            continue
        app_chain = _array_chain(index, app, report, True)
        impl_chain = _array_chain(index, impl, report, False)
        if app_chain is None or impl_chain is None:
            continue
        if len(app_chain) != len(impl_chain):
            report.fail(index, mapping, "Application and implementation array dimension counts differ",
                        application_dimensions=len(app_chain), implementation_dimensions=len(impl_chain),
                        repair=_repair("repair_array_shape", "DATA-TYPE-MAP", "Align the nested array dimension chains in outer-to-inner order."))
            continue
        for position, (app_dim, impl_dim) in enumerate(zip(app_chain, impl_chain), 1):
            if app_dim[1:] != impl_dim[1:]:
                report.fail(index, impl_dim[0], "Mapped array dimension does not correspond in outer-to-inner order",
                            dimension=position, application={"size": app_dim[1], "semantics": app_dim[2]},
                            implementation={"size": impl_dim[1], "semantics": impl_dim[2]},
                            repair=_repair("replace_value", "ARRAY-SIZE", "Match size and semantics to the corresponding ApplicationArrayElement dimension."))
    return report


def _init_spec(container: etree._Element) -> etree._Element | None:
    init = _first(container, {"INIT-VALUE", "APP-INIT-VALUE", "IMPL-INIT-VALUE"})
    if init is None:
        return None
    return next((item for item in init.iterdescendants() if local_name(item.tag) in VALUE_SPECS), None)


@plugin("initial_value_precedence")
def initial_value_precedence(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    comspec_tags = {
        "NONQUEUED-SENDER-COM-SPEC", "NONQUEUED-RECEIVER-COM-SPEC",
        "PARAMETER-PROVIDE-COM-SPEC", "PARAMETER-REQUIRE-COM-SPEC", "NV-REQUIRE-COM-SPEC",
    }
    for comspec in index.select_any(sorted(comspec_tags)):
        level2 = _init_spec(comspec)
        if level2 is None:
            continue
        prototype = _resolve(index, _first(comspec, {"DATA-ELEMENT-REF", "PARAMETER-REF", "VARIABLE-REF"}), report, "ComSpec data prototype")
        level1 = _init_spec(prototype) if prototype is not None else None
        report.observe(
            semantic="effective_initial_value", subject=index.path_of(prototype) if prototype is not None else index.path_of(comspec),
            effective_level=2, effective_source=index.location(level2),
            ignored_lower_level=index.location(level1) if level1 is not None else None,
        )
    for prototype in index.select_any(["VARIABLE-DATA-PROTOTYPE", "PARAMETER-DATA-PROTOTYPE"]):
        level1 = _init_spec(prototype)
        if level1 is not None:
            report.observe(semantic="effective_initial_value", subject=index.path_of(prototype), effective_level=1,
                           effective_source=index.location(level1))
    for calibration in index.elements("CALIBRATION-PARAMETER-VALUE"):
        app_value = _first(calibration, {"APP-INIT-VALUE"})
        impl_value = _first(calibration, {"IMPL-INIT-VALUE"})
        if app_value is not None or impl_value is not None:
            report.observe(
                semantic="calibration_initial_values", subject=index.path_of(calibration), conceptual_level=3,
                application_value=index.location(app_value) if app_value is not None else None,
                implementation_value=index.location(impl_value) if impl_value is not None else None,
                note="Level 3 application and implementation values are separate representations.",
            )
    return report

