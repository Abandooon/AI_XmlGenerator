"""Remaining executable AUTOSAR data-type and value compatibility rules."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from lxml import etree

from .arxml_index import ArxmlIndex, local_name
from .compatibility_kernel import (
    APP_TYPES, DATA_PROTOTYPES, DOC_TAGS, canonical, data_types_compatible,
    direct, first, owned,
    physical_dimension_signature, props, resolve,
    sw_data_def_props_compatible, text, type_of, units_compatible,
    unwrap_impl,
)
from .plugins import COMPONENT_TAGS, PluginReport, plugin

VALUE_SPECS = {
    "APPLICATION-VALUE-SPECIFICATION", "APPLICATION-RULE-BASED-VALUE-SPECIFICATION",
    "ARRAY-VALUE-SPECIFICATION", "NUMERICAL-RULE-BASED-VALUE-SPECIFICATION",
    "NUMERICAL-VALUE-SPECIFICATION", "RECORD-VALUE-SPECIFICATION",
    "REFERENCE-VALUE-SPECIFICATION", "TEXT-VALUE-SPECIFICATION", "CONSTANT-REFERENCE",
}


def _repair(action: str, target: str, instruction: str, **values: object) -> dict:
    return {"action": action, "target": target, "instruction": instruction, **values}


def _mapped_pair(index: ArxmlIndex, mapping: etree._Element, report: PluginReport) -> tuple[etree._Element | None, etree._Element | None]:
    return (
        resolve(index, first(mapping, {"APPLICATION-DATA-TYPE-REF"}), report, "mapped ApplicationDataType"),
        resolve(index, first(mapping, {"IMPLEMENTATION-DATA-TYPE-REF"}), report, "mapped ImplementationDataType"),
    )


def _data_type_maps(index: ArxmlIndex, report: PluginReport) -> list[tuple[etree._Element, etree._Element, etree._Element]]:
    result: list[tuple[etree._Element, etree._Element, etree._Element]] = []
    for mapping in index.elements("DATA-TYPE-MAP"):
        app, impl = _mapped_pair(index, mapping, report)
        if app is not None and impl is not None:
            result.append((mapping, app, impl))
    return result


@plugin("mapped_data_type_compatibility")
def mapped_data_type_compatibility(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    cid = rule["constraint_id"]
    for mapping, app, impl in _data_type_maps(index, report):
        final = unwrap_impl(index, impl, report)
        if final is None:
            continue
        app_category = text(direct(app, "CATEGORY"))
        impl_category = text(direct(final, "CATEGORY"))
        compatible = data_types_compatible(index, app, impl, report)
        if compatible is False:
            report.fail(index, mapping, "DataTypeMap references incompatible application and implementation data types",
                        application=index.path_of(app), implementation=index.path_of(impl),
                        application_category=app_category, implementation_category=impl_category,
                        repair=_repair("repair_reference", "IMPLEMENTATION-DATA-TYPE-REF", "Reference or generate an ImplementationDataType compatible with the ApplicationDataType."))
        elif compatible is None:
            continue
        report.observe(semantic="data_type_map_compatibility", constraint=cid,
                       mapping=index.path_of(mapping), application_category=app_category, implementation_category=impl_category)
    return report


@plugin("same_application_mapped_impl_compatible")
def same_application_mapped_impl_compatible(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    by_app: dict[int, tuple[etree._Element, list[tuple[etree._Element, etree._Element]]]] = {}
    for mapping, app, impl in _data_type_maps(index, report):
        entry = by_app.setdefault(id(app), (app, []))
        entry[1].append((mapping, impl))
    for app, entries in by_app.values():
        for position, (mapping, impl) in enumerate(entries):
            for _, other in entries[position + 1:]:
                compatible = data_types_compatible(index, impl, other, report)
                if compatible is False:
                    report.fail(index, mapping, "ImplementationDataTypes mapped to the same ApplicationDataType are incompatible",
                                application=index.path_of(app), implementations=[index.path_of(impl), index.path_of(other)],
                                repair=_repair("repair_data_type", "IMPLEMENTATION-DATA-TYPE", "Align both implementation representations or split their application mapping scope."))
    return report


@plugin("atomic_mapping_scope_unique")
def atomic_mapping_scope_unique(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    atomic_tags = COMPONENT_TAGS - {"COMPOSITION-SW-COMPONENT-TYPE"}
    for component in index.select_any(sorted(atomic_tags)):
        mapping_sets: list[etree._Element] = []
        for ref in index.descendants(component, {"DATA-TYPE-MAPPING-SET-REF"}):
            target = resolve(index, ref, report, "component DataTypeMappingSet")
            if target is not None:
                mapping_sets.append(target)
        if not mapping_sets:
            continue
        by_app: dict[int, tuple[etree._Element, set[int], list[etree._Element]]] = {}
        for mapping_set in mapping_sets:
            for mapping in index.descendants(mapping_set, {"DATA-TYPE-MAP"}):
                app, impl = _mapped_pair(index, mapping, report)
                if app is None or impl is None:
                    continue
                entry = by_app.setdefault(id(app), (app, set(), []))
                entry[1].add(id(impl))
                entry[2].append(mapping)
        for app, impls, mappings in by_app.values():
            if len(impls) > 1:
                report.fail(index, mappings[-1], "One atomic component mapping scope maps an ApplicationDataType to multiple ImplementationDataTypes",
                            component=index.path_of(component), application=index.path_of(app), implementation_count=len(impls),
                            repair=_repair("remove_or_split_mapping", "DATA-TYPE-MAP", "Use exactly one implementation mapping per ApplicationDataType in an atomic component scope."))
    return report


def _prototype_pairs(index: ArxmlIndex, report: PluginReport) -> list[tuple[etree._Element, etree._Element, etree._Element, bool]]:
    result: list[tuple[etree._Element, etree._Element, etree._Element, bool]] = []
    for mapping in index.elements("DATA-PROTOTYPE-MAPPING"):
        refs = index.descendants(mapping, {"FIRST-DATA-PROTOTYPE-REF", "SECOND-DATA-PROTOTYPE-REF"})
        targets = [resolve(index, ref, report, "DataPrototypeMapping endpoint") for ref in refs]
        targets = [item for item in targets if item is not None and local_name(item.tag) in DATA_PROTOTYPES]
        if len(targets) == 2:
            result.append((mapping, targets[0], targets[1], bool(index.descendants(mapping, {"SUB-ELEMENT-MAPPING"}))))
    return result


def _root_type_elements(index: ArxmlIndex, data_type: etree._Element) -> list[etree._Element]:
    tag = local_name(data_type.tag)
    child_tag = {
        "APPLICATION-ARRAY-DATA-TYPE": "APPLICATION-ARRAY-ELEMENT",
        "APPLICATION-RECORD-DATA-TYPE": "APPLICATION-RECORD-ELEMENT",
        "IMPLEMENTATION-DATA-TYPE": "IMPLEMENTATION-DATA-TYPE-ELEMENT",
    }.get(tag)
    return owned(index, data_type, child_tag, {tag, child_tag}) if child_tag is not None else []


def _root_element(index: ArxmlIndex, element: etree._Element, data_type: etree._Element) -> etree._Element | None:
    roots = _root_type_elements(index, data_type)
    current: etree._Element | None = element
    while current is not None and current is not data_type:
        if any(current is root for root in roots):
            return current
        current = index.parent.get(current)
    return None


def _mapped_sub_elements(
    index: ArxmlIndex,
    mapping: etree._Element,
    left_type: etree._Element,
    right_type: etree._Element,
    report: PluginReport,
) -> tuple[set[int], set[int], bool]:
    left_covered: set[int] = set()
    right_covered: set[int] = set()
    paired = True
    for submapping in index.descendants(mapping, {"SUB-ELEMENT-MAPPING"}):
        left_found: set[int] = set()
        right_found: set[int] = set()
        for ref in submapping.iterdescendants():
            if not local_name(ref.tag).endswith("-REF") or not text(ref):
                continue
            target = resolve(index, ref, report, "SubElementMapping target")
            if target is None:
                continue
            left_root = _root_element(index, target, left_type)
            right_root = _root_element(index, target, right_type)
            if left_root is not None:
                left_found.add(id(left_root))
            if right_root is not None:
                right_found.add(id(right_root))
        left_covered.update(left_found)
        right_covered.update(right_found)
        paired = paired and bool(left_found) and bool(right_found)
    return left_covered, right_covered, paired


def _mapping_override_complete(
    index: ArxmlIndex,
    mapping: etree._Element,
    left_type: etree._Element,
    right_type: etree._Element,
    report: PluginReport,
    cid: str,
) -> bool:
    left_tag = local_name(left_type.tag)
    right_tag = local_name(right_type.tag)
    submappings = index.descendants(mapping, {"SUB-ELEMENT-MAPPING"})
    if cid == "constr_1047":
        if left_tag == right_tag == "APPLICATION-PRIMITIVE-DATA-TYPE":
            return True
        composite_tags = {"APPLICATION-ARRAY-DATA-TYPE", "APPLICATION-RECORD-DATA-TYPE"}
        if {left_tag, right_tag} & composite_tags and "APPLICATION-PRIMITIVE-DATA-TYPE" in {left_tag, right_tag}:
            composite = left_type if left_tag in composite_tags else right_type
            for submapping in submappings:
                for ref in submapping.iterdescendants():
                    if not local_name(ref.tag).endswith("-REF") or not text(ref):
                        continue
                    target = resolve(index, ref, report, "composite-to-primitive SubElementMapping target")
                    if target is not None and _root_element(index, target, composite) is not None:
                        return True
        return False
    if cid == "constr_1050":
        return left_tag == right_tag == "IMPLEMENTATION-DATA-TYPE"
    expected_tag = "APPLICATION-RECORD-DATA-TYPE" if cid == "constr_1048" else "APPLICATION-ARRAY-DATA-TYPE"
    if left_tag != expected_tag or right_tag != expected_tag or not submappings:
        return False
    left_roots = {id(item) for item in _root_type_elements(index, left_type)}
    right_roots = {id(item) for item in _root_type_elements(index, right_type)}
    left_covered, right_covered, paired = _mapped_sub_elements(index, mapping, left_type, right_type, report)
    # The source requires every element of the required side. Direction is supplied
    # by the connector context, so either complete side is sufficient here; each
    # SubElementMapping must still resolve a counterpart on the other side.
    return paired and bool(left_roots) and bool(right_roots) and (
        left_roots <= left_covered or right_roots <= right_covered
    )


@plugin("compatibility_kernel_context_audit")
def compatibility_kernel_context_audit(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """Execute predicate-definition rules on every concrete mapping context."""
    report = PluginReport(checked=len(selected))
    cid = rule["constraint_id"]
    if cid == "constr_1053":
        for mapping in index.elements("PHYSICAL-DIMENSION-MAPPING"):
            targets = [resolve(index, ref, report, "PhysicalDimensionMapping endpoint") for ref in mapping.iterdescendants() if local_name(ref.tag).endswith("-REF")]
            targets = [item for item in targets if item is not None and local_name(item.tag) == "PHYSICAL-DIMENSION"]
            if len(targets) == 2 and physical_dimension_signature(targets[0]) != physical_dimension_signature(targets[1]):
                report.fail(index, mapping, "PhysicalDimensionMapping relates dimensions with different exponents",
                            repair=_repair("repair_reference", "PHYSICAL-DIMENSION-MAPPING", "Map only PhysicalDimensions with identical exponent vectors."))
        return report
    for mapping, left, right, has_submapping in _prototype_pairs(index, report):
        left_type = type_of(index, left, report)
        right_type = type_of(index, right, report)
        if left_type is None or right_type is None:
            continue
        compatible = data_types_compatible(index, left_type, right_type, report)
        override: bool | None = None
        if cid in {"constr_1047", "constr_1048", "constr_1049", "constr_1050"}:
            override = _mapping_override_complete(index, mapping, left_type, right_type, report, cid)
            if compatible is False and not override:
                report.fail(
                    index, mapping,
                    "DataPrototypeMapping neither has directly compatible types nor a complete normative mapping override",
                    left_type=index.path_of(left_type), right_type=index.path_of(right_type),
                    predicate_rule=cid, has_submapping=has_submapping,
                    repair=_repair(
                        "add_mapping_or_repair_type", "SUB-ELEMENT-MAPPING",
                        "Make the data types directly compatible or add complete paired SubElementMappings for every required composite element.",
                    ),
                )
        # constr_1220/1051/1052/1278/1162 define nested predicates. Their
        # direct value is evidence consumed by the outer type predicate; an
        # explicit DataPrototypeMapping may legally override outer incompatibility.
        report.observe(
            semantic="compatibility_predicate_evaluated", constraint=cid,
            context=index.path_of(mapping), direct_compatible=compatible,
            mapping_override=override, effective_compatible=bool(compatible or override),
        )
    return report


def _all_refs(owner: etree._Element, tags: set[str]) -> list[etree._Element]:
    return [item for item in owner.iterdescendants() if local_name(item.tag) in tags and text(item)]


@plugin("implementation_category_semantics")
def implementation_category_semantics(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    cid = rule["constraint_id"]
    for data_type in selected:
        category = text(direct(data_type, "CATEGORY"))
        if cid == "constr_1055" and category == "VALUE":
            bases = [resolve(index, ref, report, "VALUE SwBaseType") for ref in _all_refs(data_type, {"BASE-TYPE-REF"})]
            signatures = {repr(canonical(item, ignored=DOC_TAGS)) for item in bases if item is not None}
            if len(signatures) > 1:
                report.fail(index, data_type, "VALUE ImplementationDataType variants reference incompatible SwBaseTypes",
                            repair=_repair("repair_reference", "BASE-TYPE-REF", "Use compatible SwBaseTypes in every active variant."))
        elif cid == "constr_1056" and category == "TYPE_REFERENCE":
            targets = [resolve(index, ref, report, "TYPE_REFERENCE ImplementationDataType") for ref in _all_refs(data_type, {"IMPLEMENTATION-DATA-TYPE-REF"})]
            targets = [item for item in targets if item is not None]
            for position, target in enumerate(targets):
                for other in targets[position + 1:]:
                    if data_types_compatible(index, target, other, report) is False:
                        report.fail(index, data_type, "TYPE_REFERENCE variants resolve to incompatible ImplementationDataTypes",
                                    repair=_repair("repair_reference", "IMPLEMENTATION-DATA-TYPE-REF", "Use compatible referenced implementation types."))
        elif cid == "constr_1057" and category == "DATA_REFERENCE":
            pointers = index.descendants(data_type, {"SW-POINTER-TARGET-PROPS"})
            signatures = {repr(canonical(item, ignored=DOC_TAGS)) for item in pointers}
            if len(signatures) > 1:
                report.fail(index, data_type, "DATA_REFERENCE pointer target properties differ between variants",
                            repair=_repair("repair_properties", "SW-POINTER-TARGET-PROPS", "Use identical targetCategory and target SwDataDefProps."))
        elif cid == "constr_1058" and category == "FUNCTION_REFERENCE":
            entries = [resolve(index, ref, report, "functionPointerSignature") for ref in _all_refs(data_type, {"FUNCTION-POINTER-SIGNATURE-REF"})]
            signatures = {repr(canonical(item, ignored=DOC_TAGS)) for item in entries if item is not None}
            if len(signatures) > 1:
                report.fail(index, data_type, "FUNCTION_REFERENCE variants resolve to different function signatures",
                            repair=_repair("repair_reference", "FUNCTION-POINTER-SIGNATURE-REF", "Reference BswModuleEntrys with the same function signature."))
        elif cid == "constr_1229":
            final = unwrap_impl(index, data_type, report)
            qualifies = final is not None and text(direct(final, "CATEGORY")) == "VALUE"
            if not qualifies and category == "ARRAY":
                elements = owned(index, data_type, "IMPLEMENTATION-DATA-TYPE-ELEMENT", {"IMPLEMENTATION-DATA-TYPE", "IMPLEMENTATION-DATA-TYPE-ELEMENT"})
                if len(elements) == 1:
                    element = elements[0]
                    base = resolve(index, first(element, {"BASE-TYPE-REF"}), report, "integral array SwBaseType", required=False)
                    qualifies = base is not None and text(first(base, {"BASE-TYPE-SIZE", "MAX-BASE-TYPE-SIZE"})) == "8" and text(first(base, {"BASE-TYPE-ENCODING"})) == "NONE"
            report.observe(semantic="integral_primitive_type", subject=index.path_of(data_type), qualifies=qualifies)
    return report


def _invalid_spec(owner: etree._Element) -> etree._Element | None:
    invalid = first(owner, {"INVALID-VALUE"})
    return next((item for item in invalid.iterdescendants() if local_name(item.tag) in VALUE_SPECS), None) if invalid is not None else None


def _dereference_constant(index: ArxmlIndex, value: etree._Element, report: PluginReport) -> etree._Element | None:
    if local_name(value.tag) != "CONSTANT-REFERENCE":
        return value
    constant = resolve(index, first(value, {"CONSTANT-REF"}), report, "ConstantReference")
    return next((item for item in constant.iterdescendants() if local_name(item.tag) in VALUE_SPECS - {"CONSTANT-REFERENCE"}), None) if constant is not None else None


@plugin("invalid_value_representation")
def invalid_value_representation(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    cid = rule["constraint_id"]
    for owner in selected:
        if cid == "constr_1242" and text(direct(owner, "CATEGORY")) != "STRING":
            continue
        spec = _invalid_spec(owner)
        if spec is None:
            continue
        resolved = _dereference_constant(index, spec, report)
        if resolved is None:
            report.incomplete(f"invalid ConstantReference has no value at {index.location(spec)}")
            continue
        allowed = {"APPLICATION-VALUE-SPECIFICATION"} if cid == "constr_1242" else {"NUMERICAL-VALUE-SPECIFICATION", "TEXT-VALUE-SPECIFICATION"}
        if local_name(resolved.tag) not in allowed:
            report.fail(index, resolved, "invalidValue uses an unsupported ValueSpecification kind",
                        actual=local_name(resolved.tag), allowed=sorted(allowed),
                        repair=_repair("replace_value_specification", local_name(resolved.tag), "Use a permitted compatible invalid-value representation."))
    return report


def _compu_labels(index: ArxmlIndex, data_type: etree._Element, report: PluginReport) -> tuple[str | None, set[str]]:
    method = resolve(index, first(data_type, {"COMPU-METHOD-REF"}), report, "enumeration CompuMethod", required=False)
    if method is None:
        return None, set()
    category = text(direct(method, "CATEGORY"))
    labels = {text(item) for item in method.iterdescendants() if local_name(item.tag) in {"VT", "SYMBOL", "SHORT-LABEL"} and text(item)}
    return category, labels


def _init_spec(prototype: etree._Element) -> etree._Element | None:
    init = first(prototype, {"INIT-VALUE", "APP-INIT-VALUE", "IMPL-INIT-VALUE"})
    return next((item for item in init.iterdescendants() if local_name(item.tag) in VALUE_SPECS), None) if init is not None else None


def _scalar_label(value: etree._Element) -> str:
    return text(first(value, {"VALUE", "VT"}))


@plugin("enumeration_value_semantics")
def enumeration_value_semantics(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    cid = rule["constraint_id"]
    for prototype in index.select_any(sorted(DATA_PROTOTYPES)):
        value = _init_spec(prototype)
        if value is None:
            continue
        data_type = type_of(index, prototype, report)
        if data_type is None:
            continue
        category, labels = _compu_labels(index, data_type, report)
        if category not in {"TEXTTABLE", "BITFIELD_TEXTTABLE", "SCALE_LINEAR_AND_TEXTTABLE", "SCALE_RATIONAL_AND_TEXTTABLE"}:
            continue
        expected_kind = "TEXT-VALUE-SPECIFICATION" if local_name(data_type.tag) == "IMPLEMENTATION-DATA-TYPE" else "APPLICATION-VALUE-SPECIFICATION"
        if cid == "constr_1225" and local_name(data_type.tag) != "IMPLEMENTATION-DATA-TYPE":
            continue
        if local_name(value.tag) != expected_kind:
            report.fail(index, value, "Enumeration initValue uses the wrong representation for its AutosarDataType domain",
                        actual=local_name(value.tag), expected=expected_kind,
                        repair=_repair("replace_value_specification", local_name(value.tag), f"Use {expected_kind}."))
        elif labels and _scalar_label(value) not in labels:
            report.fail(index, value, "Enumeration value does not match vt, shortLabel, or symbol of an applicable CompuScale",
                        actual=_scalar_label(value), allowed=sorted(labels),
                        repair=_repair("replace_value", "VALUE", "Use an applicable CompuScale label."))
    return report


@plugin("prototype_init_value_kind")
def prototype_init_value_kind(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    cid = rule["constraint_id"]
    for prototype in index.select_any(sorted(DATA_PROTOTYPES)):
        value = _init_spec(prototype)
        if value is None:
            continue
        data_type = type_of(index, prototype, report)
        if data_type is None:
            continue
        type_tag = local_name(data_type.tag)
        category = text(direct(data_type, "CATEGORY"))
        allowed: set[str] | None = None
        if cid in {"TPS_SWCT_01183", "constr_1221"} and type_tag == "APPLICATION-PRIMITIVE-DATA-TYPE":
            allowed = {"APPLICATION-VALUE-SPECIFICATION"}
        elif cid == "TPS_SWCT_01183" and type_tag == "IMPLEMENTATION-DATA-TYPE":
            allowed = {"NUMERICAL-VALUE-SPECIFICATION", "TEXT-VALUE-SPECIFICATION", "ARRAY-VALUE-SPECIFICATION", "RECORD-VALUE-SPECIFICATION", "NUMERICAL-RULE-BASED-VALUE-SPECIFICATION"}
        elif cid == "TPS_SWCT_01185" and type_tag == "IMPLEMENTATION-DATA-TYPE" and category in {"ARRAY", "STRUCTURE"}:
            allowed = {"ARRAY-VALUE-SPECIFICATION", "RECORD-VALUE-SPECIFICATION", "NUMERICAL-RULE-BASED-VALUE-SPECIFICATION"}
        elif cid == "constr_1222" and category == "STRING":
            allowed = {"APPLICATION-VALUE-SPECIFICATION"}
            app_category = text(first(value, {"CATEGORY"}))
            if app_category and app_category != "STRING":
                report.fail(index, value, "STRING type ApplicationValueSpecification does not have category STRING",
                            actual=app_category, repair=_repair("replace_value", "CATEGORY", "Set ApplicationValueSpecification category to STRING."))
        elif cid == "constr_1223" and type_tag == "APPLICATION-RECORD-DATA-TYPE":
            allowed = {"RECORD-VALUE-SPECIFICATION"}
        elif cid == "constr_1224" and type_tag == "APPLICATION-ARRAY-DATA-TYPE":
            allowed = {"ARRAY-VALUE-SPECIFICATION", "APPLICATION-RULE-BASED-VALUE-SPECIFICATION"}
        if allowed is not None and local_name(value.tag) not in allowed:
            report.fail(index, value, "initValue representation does not match the AutosarDataType",
                        actual=local_name(value.tag), allowed=sorted(allowed), type=index.path_of(data_type),
                        repair=_repair("replace_value_specification", local_name(value.tag), "Use the value representation required by the resolved AutosarDataType."))
    return report


def _integer_impl(index: ArxmlIndex, data_type: etree._Element, report: PluginReport) -> bool | None:
    final = unwrap_impl(index, data_type, report)
    if final is None:
        return None
    if text(direct(final, "CATEGORY")) != "VALUE":
        return False
    base = resolve(index, first(final, {"BASE-TYPE-REF"}), report, "integer SwBaseType", required=False)
    if base is None:
        return None
    encoding = text(first(base, {"BASE-TYPE-ENCODING"})).upper()
    return any(token in encoding for token in {"SIGNED", "UNSIGNED", "2C", "BOOLEAN"}) or encoding == "NONE"


@plugin("data_filter_integer_domain")
def data_filter_integer_domain(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for data_filter in selected:
        prototype = index.nearest(data_filter, DATA_PROTOTYPES)
        data_type = type_of(index, prototype, report) if prototype is not None else resolve(index, first(data_filter, {"TYPE-TREF"}), report, "DataFilter type", required=False)
        if data_type is None:
            report.incomplete(f"cannot establish DataFilter data type at {index.location(data_filter)}")
            continue
        impl_types: list[etree._Element] = []
        if local_name(data_type.tag) == "IMPLEMENTATION-DATA-TYPE":
            impl_types = [data_type]
        else:
            for _, app, impl in _data_type_maps(index, report):
                if app is data_type:
                    impl_types.append(impl)
        if not impl_types:
            report.incomplete(f"DataFilter type has no implementation representation at {index.location(data_filter)}")
        elif not all(_integer_impl(index, item, report) is True for item in impl_types):
            report.fail(index, data_filter, "DataFilter is applied to a non-integer implementation base type",
                        repair=_repair("repair_reference", "TYPE-TREF", "Use an AutosarDataType with an integer SwBaseType."))
    return report


@plugin("application_integral_primitive")
def application_integral_primitive(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    allowed_categories = {"BOOLEAN", "VALUE", "STRING", "ARRAY"}
    for app in selected:
        if local_name(app.tag) not in APP_TYPES:
            continue
        maps = [impl for _, mapped_app, impl in _data_type_maps(index, report) if mapped_app is app]
        qualifies = text(direct(app, "CATEGORY")) in allowed_categories and bool(maps) and all(_integer_impl(index, item, report) is True for item in maps)
        report.observe(semantic="application_integral_primitive", subject=index.path_of(app), qualifies=qualifies,
                       mapped_implementation_count=len(maps))
    return report


@plugin("axis_type_properties_compatible")
def axis_type_properties_compatible(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    cid = rule["constraint_id"]
    if cid == "constr_1019":
        for axis in index.elements("SW-AXIS-INDIVIDUAL"):
            variable = resolve(index, first(axis, {"AUTOSAR-VARIABLE-REF", "TARGET-DATA-PROTOTYPE-REF"}), report, "axis input variable", required=False)
            variable_type = type_of(index, variable, report) if variable is not None else None
            axis_type = resolve(index, first(axis, {"INPUT-VARIABLE-TYPE-REF", "INPUT-VARIABLE-TYPE-TREF"}), report, "axis inputVariableType", required=False)
            if variable_type is not None and axis_type is not None and data_types_compatible(index, variable_type, axis_type, report) is False:
                report.fail(index, axis, "Input variable type is incompatible with SwAxisIndividual.inputVariableType",
                            repair=_repair("repair_reference", "INPUT-VARIABLE-TYPE-REF", "Reference a compatible axis input type."))
            if variable_type is not None and sw_data_def_props_compatible(index, props(variable_type), props(axis), report) is False:
                report.fail(index, axis, "Input variable SwDataDefProps are incompatible with axis properties",
                            repair=_repair("repair_properties", "SW-DATA-DEF-PROPS", "Align axis unit, CompuMethod, DataConstr and record layout."))
    else:
        for parameter in selected:
            shared = resolve(index, first(parameter, {"SHARED-AXIS-TYPE-REF"}), report, "sharedAxisType", required=False)
            if shared is None:
                continue
            data_type = type_of(index, parameter, report)
            if data_type is not None and data_types_compatible(index, data_type, shared, report) is False:
                report.fail(index, parameter, "ParameterDataPrototype type is incompatible with sharedAxisType",
                            repair=_repair("repair_reference", "TYPE-TREF", "Reference a data type compatible with sharedAxisType."))
    return report


@plugin("compu_method_stepwise")
def compu_method_stepwise(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    forbidden = {"COMPU-RATIONAL-COEFFS"}  # Allowed only inside individual CompuScales.
    for method in selected:
        scales = owned(index, method, "COMPU-SCALE", {"COMPU-METHOD"})
        if not scales and text(direct(method, "CATEGORY")) != "IDENTICAL":
            report.fail(index, method, "Non-IDENTICAL CompuMethod has no stepwise CompuScale definition",
                        repair=_repair("add_element", "COMPU-SCALE", "Define the conversion as one or more CompuScales."))
        for child in method:
            if local_name(child.tag) in forbidden:
                report.fail(index, child, "CompuMethod defines a non-stepwise top-level conversion formula",
                            repair=_repair("move_element", local_name(child.tag), "Place coefficients inside the applicable CompuScale."))
    return report


@plugin("unit_group_conversion_compatibility")
def unit_group_conversion_compatibility(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for group in selected:
        refs = [item for item in group.iterdescendants() if local_name(item.tag) == "UNIT-REF"]
        units = [resolve(index, ref, report, "UnitGroup member") for ref in refs]
        units = [item for item in units if item is not None]
        if text(direct(group, "CATEGORY")) == "EQUIV_UNITS":
            for position, unit in enumerate(units):
                for other in units[position + 1:]:
                    if units_compatible(index, unit, other, report) is False:
                        report.fail(index, group, "EQUIV_UNITS UnitGroup contains physically incompatible Units",
                                    units=[index.path_of(unit), index.path_of(other)],
                                    repair=_repair("remove_or_repair_reference", "UNIT-REF", "Keep only Units with compatible SI conversion and PhysicalDimension."))
    return report


def _primitive(data_type: etree._Element, index: ArxmlIndex, report: PluginReport) -> bool | None:
    tag = local_name(data_type.tag)
    if tag == "APPLICATION-PRIMITIVE-DATA-TYPE":
        return text(direct(data_type, "CATEGORY")) == "VALUE"
    if tag == "IMPLEMENTATION-DATA-TYPE":
        final = unwrap_impl(index, data_type, report)
        return None if final is None else text(direct(final, "CATEGORY")) == "VALUE"
    return False


@plugin("primitive_provider_submapping_forbidden")
def primitive_provider_submapping_forbidden(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for mapping, provider, requester, has_submapping in _prototype_pairs(index, report):
        if not has_submapping:
            continue
        provider_type = type_of(index, provider, report)
        if provider_type is None or _primitive(provider_type, index, report) is not True:
            continue
        for submapping in index.descendants(mapping, {"SUB-ELEMENT-MAPPING"}):
            targets = [resolve(index, ref, report, "SubElementMapping target") for ref in submapping.iterdescendants() if local_name(ref.tag).endswith("-REF")]
            if any(target is not None and local_name(target.tag) in {"IMPLEMENTATION-DATA-TYPE-ELEMENT", "APPLICATION-ARRAY-ELEMENT", "APPLICATION-RECORD-ELEMENT"} for target in targets):
                report.fail(index, submapping, "Primitive provider DataPrototype is mapped to a requester composite sub-element",
                            repair=_repair("remove", "SUB-ELEMENT-MAPPING", "Map primitive prototypes directly; do not target a composite requester element."))
    return report


def _has_invalid_leaf(index: ArxmlIndex, data_type: etree._Element, report: PluginReport, *, all_required: bool, seen: set[int] | None = None) -> bool | None:
    seen = seen or set()
    if id(data_type) in seen:
        report.incomplete(f"data type cycle while checking invalidation at {index.location(data_type)}")
        return None
    seen.add(id(data_type))
    tag = local_name(data_type.tag)
    final = unwrap_impl(index, data_type, report) if tag == "IMPLEMENTATION-DATA-TYPE" else data_type
    if final is None:
        return None
    category = text(direct(final, "CATEGORY"))
    if tag == "APPLICATION-PRIMITIVE-DATA-TYPE" or category == "VALUE":
        return first(final, {"INVALID-VALUE"}) is not None
    children = []
    for child_tag in {"APPLICATION-ARRAY-ELEMENT", "APPLICATION-RECORD-ELEMENT", "IMPLEMENTATION-DATA-TYPE-ELEMENT"}:
        children.extend(owned(index, final, child_tag, {local_name(final.tag), child_tag}))
    results: list[bool | None] = []
    for child in children:
        child_type = resolve(index, first(child, {"TYPE-TREF", "IMPLEMENTATION-DATA-TYPE-REF"}), report, "invalidation leaf type")
        results.append(None if child_type is None else _has_invalid_leaf(index, child_type, report, all_required=all_required, seen=seen))
    if any(item is None for item in results) or not results:
        return None
    return all(results) if category == "UNION" or all_required else any(results)


@plugin("data_invalidation_type_eligible")
def data_invalidation_type_eligible(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for policy in index.elements("INVALIDATION-POLICY"):
        data = resolve(index, first(policy, {"DATA-ELEMENT-REF"}), report, "InvalidationPolicy data element")
        data_type = type_of(index, data, report) if data is not None else None
        eligible = _has_invalid_leaf(index, data_type, report, all_required=False) if data_type is not None else None
        if eligible is False:
            report.fail(index, policy, "Data invalidation is applied to a type without the required primitive invalidValue coverage",
                        repair=_repair("add_invalid_value_or_remove_policy", "INVALIDATION-POLICY", "Define invalidValue on eligible primitive leaves or remove invalidation."))
    return report


@plugin("parameter_type_properties_match")
def parameter_type_properties_match(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for parameter in selected:
        prototype_props = props(parameter)
        if prototype_props is None:
            continue
        data_type = type_of(index, parameter, report)
        type_props = props(data_type) if data_type is not None else None
        if type_props is None:
            report.incomplete(f"ParameterDataPrototype type has no SwDataDefProps at {index.location(parameter)}")
            continue
        compatible = sw_data_def_props_compatible(index, prototype_props, type_props, report)
        if compatible is False:
            report.fail(index, parameter, "ParameterDataPrototype SwDataDefProps do not match its data type record-layout properties",
                        type=index.path_of(data_type),
                        repair=_repair("repair_properties", "SW-DATA-DEF-PROPS", "Align unit, CompuMethod, invalidValue, DataConstr and SwRecordLayout with the referenced type."))
    return report

def _mode_value_in_internal_range(data_constr: etree._Element, value: Decimal, index: ArxmlIndex, report: PluginReport) -> bool | None:
    intervals = [item for item in data_constr.iterdescendants() if local_name(item.tag) == "INTERNAL-CONSTRS"]
    if not intervals:
        report.incomplete(f"ModeRequestTypeMap DataConstr has no INTERNAL-CONSTRS at {index.location(data_constr)}")
        return None
    for interval in intervals:
        lower_element = first(interval, {"LOWER-LIMIT"})
        upper_element = first(interval, {"UPPER-LIMIT"})
        try:
            lower = Decimal(text(lower_element))
            upper = Decimal(text(upper_element))
        except (InvalidOperation, ValueError):
            report.incomplete(f"ModeRequestTypeMap has a non-numeric DataConstr interval at {index.location(interval)}")
            return None
        lower_ok = value > lower if (lower_element is not None and lower_element.get("INTERVAL-TYPE") == "OPEN") else value >= lower
        upper_ok = value < upper if (upper_element is not None and upper_element.get("INTERVAL-TYPE") == "OPEN") else value <= upper
        if lower_ok and upper_ok:
            return True
    return False




@plugin("mode_request_type_map_compatible")
def mode_request_type_map_compatible(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for mapping in selected:
        group = resolve(index, first(mapping, {"MODE-GROUP-REF"}), report, "ModeRequestTypeMap ModeDeclarationGroup")
        implementation = resolve(index, first(mapping, {"IMPLEMENTATION-DATA-TYPE-REF"}), report, "ModeRequestTypeMap ImplementationDataType")
        if group is None or implementation is None:
            continue
        final = unwrap_impl(index, implementation, report)
        if final is None:
            continue
        data_constr_refs = [item for item in final.iterdescendants() if local_name(item.tag) == "DATA-CONSTR-REF"]
        data_constrs = [resolve(index, ref, report, "ModeRequestTypeMap DataConstr") for ref in data_constr_refs]
        data_constrs = [item for item in data_constrs if item is not None]
        if not data_constrs:
            report.incomplete(f"ModeRequestTypeMap type has no resolvable DataConstr range at {index.location(mapping)}")
            continue
        declarations = owned(index, group, "MODE-DECLARATION", {"MODE-DECLARATION-GROUP"})
        if not declarations:
            report.incomplete(f"ModeRequestTypeMap group has no ModeDeclarations at {index.location(group)}")
            continue
        for declaration in declarations:
            raw_value = text(direct(declaration, "VALUE"))
            try:
                value = Decimal(raw_value)
            except InvalidOperation:
                report.incomplete(f"ModeDeclaration has no explicit numeric value at {index.location(declaration)}")
                continue
            supported = [_mode_value_in_internal_range(item, value, index, report) for item in data_constrs]
            if supported and all(item is False for item in supported):
                report.fail(
                    index, declaration,
                    "ModeDeclaration value is outside the supported range of its ModeRequestTypeMap implementation type",
                    value=raw_value, implementation_type=index.path_of(implementation),
                    repair=_repair("repair_range_or_value", "DATA-CONSTR-REF", "Expand the user-side implementation range or use a supported ModeDeclaration value."),
                )
    return report
