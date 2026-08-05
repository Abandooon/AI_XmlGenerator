"""Remaining connector, component, mode, scale, and graph consistency rules."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal, InvalidOperation

from lxml import etree

from .arxml_index import ArxmlIndex, local_name
from .compatibility_kernel import (
    APP_TYPES, DATA_PROTOTYPES, DOC_TAGS, canonical, compu_method_unit, compu_scale_signature, data_types_compatible,
    direct, errors_compatible, first, interface, interface_members, mapping_pairs, physical_dimension_signature,
    mode_groups_compatible, operation_errors, operations_compatible, owned,
    prototypes_compatible, resolve, short_name, text, type_of, units_compatible, unwrap_impl,
)
from .plugins import COMPONENT_TAGS, CONNECTOR_TAGS, PORT_TAGS, PluginReport, plugin

ATOMIC_TAGS = COMPONENT_TAGS - {"COMPOSITION-SW-COMPONENT-TYPE", "PARAMETER-SW-COMPONENT-TYPE"}
DATA_INTERFACES = {"SENDER-RECEIVER-INTERFACE", "NV-DATA-INTERFACE", "PARAMETER-INTERFACE"}
ENDPOINT_REFS = {
    "TARGET-P-PORT-REF", "TARGET-R-PORT-REF", "OUTER-PORT-REF",
    "PROVIDED-OUTER-PORT-REF", "REQUIRED-OUTER-PORT-REF",
}
SAFE_DATA_REFERENCE_COMPONENTS = {
    "SERVICE-SW-COMPONENT-TYPE", "COMPLEX-DEVICE-DRIVER-SW-COMPONENT-TYPE",
    "PARAMETER-SW-COMPONENT-TYPE", "NV-BLOCK-SW-COMPONENT-TYPE", "ECU-ABSTRACTION-SW-COMPONENT-TYPE",
}


def _repair(action: str, target: str, instruction: str, **values: object) -> dict:
    return {"action": action, "target": target, "instruction": instruction, **values}


def _parameters(index: ArxmlIndex, rule: dict, target: etree._Element, report: PluginReport) -> dict | None:
    context = rule.get("_validation_context") or {}
    values = (((context.get("declared_parameters") or {}).get(rule["constraint_id"]) or {}).get(index.path_of(target)))
    if not isinstance(values, dict):
        report.incomplete(f"validation context has no declared parameters for {rule['constraint_id']} target {index.path_of(target)}")
        return None
    return values


def _connector_endpoints(index: ArxmlIndex, connector: etree._Element, report: PluginReport) -> list[tuple[etree._Element, etree._Element]]:
    result: list[tuple[etree._Element, etree._Element]] = []
    for ref in connector.iterdescendants():
        if local_name(ref.tag) not in ENDPOINT_REFS:
            continue
        port = resolve(index, ref, report, "connector port")
        if port is not None and local_name(port.tag) in PORT_TAGS and all(port is not item[1] for item in result):
            result.append((ref, port))
    if len(result) != 2:
        report.incomplete(f"connector resolves {len(result)} unique ports at {index.location(connector)}")
    return result


def _connector_mapping(index: ArxmlIndex, connector: etree._Element, report: PluginReport) -> tuple[set[tuple[int, int]], list[etree._Element]]:
    pairs: set[tuple[int, int]] = set()
    mappings: list[etree._Element] = []
    for ref in connector.iterdescendants():
        tag = local_name(ref.tag)
        if "MAPPING" not in tag or not tag.endswith("-REF"):
            continue
        mapping = resolve(index, ref, report, "connector PortInterfaceMapping")
        if mapping is not None:
            mappings.append(mapping)
            pairs.update(mapping_pairs(index, mapping, report))
    return pairs, mappings


def _is_service(interface_element: etree._Element) -> str:
    return text(first(interface_element, {"IS-SERVICE"})).lower() or "false"


def _mode_group(index: ArxmlIndex, prototype: etree._Element, report: PluginReport) -> etree._Element | None:
    return resolve(index, first(prototype, {"TYPE-TREF", "MODE-DECLARATION-GROUP-REF"}), report, "ModeDeclarationGroupPrototype type")


def _member_compatible(index: ArxmlIndex, left: etree._Element, right: etree._Element, report: PluginReport, explicit: set[tuple[int, int]]) -> bool | None:
    if explicit:
        return (id(left), id(right)) in explicit
    left_tag, right_tag = local_name(left.tag), local_name(right.tag)
    if left_tag in DATA_PROTOTYPES and right_tag in DATA_PROTOTYPES:
        return prototypes_compatible(index, left, right, report, require_name=True)
    if left_tag == right_tag == "MODE-DECLARATION-GROUP-PROTOTYPE":
        left_group = _mode_group(index, left, report)
        right_group = _mode_group(index, right, report)
        return None if left_group is None or right_group is None else mode_groups_compatible(index, left_group, right_group, report)
    if left_tag == right_tag == "CLIENT-SERVER-OPERATION":
        return operations_compatible(index, left, right, report)
    if left_tag == right_tag == "APPLICATION-ERROR":
        return errors_compatible(left, right)
    if left_tag == right_tag == "TRIGGER":
        return short_name(left) == short_name(right)
    return False


def _required_endpoint(endpoints: list[tuple[etree._Element, etree._Element]]) -> tuple[etree._Element, etree._Element] | None:
    return next((item for item in endpoints if local_name(item[0].tag) in {"TARGET-R-PORT-REF", "REQUIRED-OUTER-PORT-REF"} or local_name(item[1].tag) == "R-PORT-PROTOTYPE"), None)


@plugin("connector_interface_compatibility")
def connector_interface_compatibility(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    cid = rule["constraint_id"]
    for connector in selected:
        endpoints = _connector_endpoints(index, connector, report)
        if len(endpoints) != 2:
            continue
        first_ref, first_port = endpoints[0]
        second_ref, second_port = endpoints[1]
        first_if = interface(index, first_port, report)
        second_if = interface(index, second_port, report)
        if first_if is None or second_if is None:
            continue
        if _is_service(first_if) != _is_service(second_if):
            report.fail(index, connector, "Connected PortInterfaces have different isService values",
                        interfaces=[index.path_of(first_if), index.path_of(second_if)],
                        repair=_repair("repair_interface", "IS-SERVICE", "Use interfaces with identical isService values."))
        first_kind, second_kind = local_name(first_if.tag), local_name(second_if.tag)
        if first_kind != second_kind and not ({first_kind, second_kind} <= DATA_INTERFACES):
            report.fail(index, connector, "Connected PortInterfaces belong to incompatible interface families",
                        actual=[first_kind, second_kind],
                        repair=_repair("repair_reference", "INTERFACE-TREF", "Use compatible PortInterface kinds."))
            continue
        explicit, mappings = _connector_mapping(index, connector, report)
        required = _required_endpoint(endpoints)
        required_if = interface(index, required[1], report) if required is not None else first_if
        provided_if = second_if if required_if is first_if else first_if
        required_members = interface_members(index, required_if)
        provided_members = interface_members(index, provided_if)
        matched = 0
        for required_member in required_members:
            compatible_targets: list[etree._Element] = []
            for provided_member in provided_members:
                compatible = _member_compatible(index, required_member, provided_member, report, explicit)
                if compatible is True:
                    compatible_targets.append(provided_member)
            if compatible_targets:
                matched += 1
            elif cid not in {"constr_1085"}:
                report.fail(index, required_member, "Required PortInterface member has no compatible provided member",
                            connector=index.path_of(connector), interface=index.path_of(required_if),
                            explicit_mapping=bool(mappings),
                            repair=_repair("add_mapping_or_member", "PORT-INTERFACE-MAPPING", "Add a compatible provided member or an explicit complete mapping."))
        if cid == "constr_1085" and required_members and matched == 0:
            report.fail(index, connector, "Flat ECU connector has no compatible data prototype pair",
                        repair=_repair("add_mapping_or_member", "PORT-INTERFACE-MAPPING", "Provide at least one compatible data prototype pair."))
        report.observe(semantic="connector_interface_compatibility", constraint=cid, connector=index.path_of(connector),
                       required_member_count=len(required_members), matched_count=matched, mapping_override=bool(mappings))
    return report


@plugin("port_interface_mapping_applicable")
def port_interface_mapping_applicable(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for connector in index.select_any(sorted(CONNECTOR_TAGS)):
        endpoints = _connector_endpoints(index, connector, report)
        if len(endpoints) != 2:
            continue
        endpoint_interfaces = [interface(index, item[1], report) for item in endpoints]
        _, mappings = _connector_mapping(index, connector, report)
        for mapping in mappings:
            mapped_interfaces: list[etree._Element] = []
            for ref in mapping.iterdescendants():
                if "INTERFACE" not in local_name(ref.tag) or not local_name(ref.tag).endswith(("-REF", "-TREF")):
                    continue
                target = resolve(index, ref, report, "PortInterfaceMapping interface")
                if target is not None and "INTERFACE" in local_name(target.tag) and all(target is not item for item in mapped_interfaces):
                    mapped_interfaces.append(target)
            if len(mapped_interfaces) != 2 or {id(item) for item in mapped_interfaces} != {id(item) for item in endpoint_interfaces if item is not None}:
                report.fail(index, mapping, "PortInterfaceMapping does not map the same two interfaces as its SwConnector endpoints",
                            connector_interfaces=[index.path_of(item) for item in endpoint_interfaces if item is not None],
                            mapped_interfaces=[index.path_of(item) for item in mapped_interfaces],
                            repair=_repair("repair_reference", "PORT-INTERFACE-MAPPING-REF", "Reference a mapping whose two interfaces exactly match both connector ports."))
    return report


@plugin("mapped_prototype_policy")
def mapped_prototype_policy(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for mapping in selected:
        refs = index.descendants(mapping, {"FIRST-DATA-PROTOTYPE-REF", "SECOND-DATA-PROTOTYPE-REF"})
        targets = [resolve(index, ref, report, "DataPrototypeMapping endpoint") for ref in refs]
        targets = [item for item in targets if item is not None and local_name(item.tag) in DATA_PROTOTYPES]
        if len(targets) != 2:
            continue
        policies = [text(first(item, {"SW-IMPL-POLICY"})).upper() for item in targets]
        if "QUEUED" in policies and policies[0] != policies[1]:
            report.fail(index, mapping, "DataPrototypeMapping combines QUEUED with a different swImplPolicy",
                        actual=policies, repair=_repair("replace_value", "SW-IMPL-POLICY", "Use QUEUED on both mapped elements or on neither."))
    return report


@plugin("sender_receiver_conversion_available")
def sender_receiver_conversion_available(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for mapping in selected:
        refs = index.descendants(mapping, {"FIRST-DATA-PROTOTYPE-REF", "SECOND-DATA-PROTOTYPE-REF"})
        targets = [resolve(index, ref, report, "DataPrototypeMapping endpoint") for ref in refs]
        targets = [item for item in targets if item is not None and local_name(item.tag) in DATA_PROTOTYPES]
        if len(targets) != 2:
            continue
        left_type = type_of(index, targets[0], report)
        right_type = type_of(index, targets[1], report)
        compatible = data_types_compatible(index, left_type, right_type, report) if left_type is not None and right_type is not None else None
        conversion = first(mapping, {"FIRST-TO-SECOND-DATA-TRANSFORMATION-REF", "DATA-TRANSFORMATION-REF"})
        if compatible is False and conversion is None:
            report.fail(index, mapping, "Sender/receiver DataPrototypeMapping has incompatible types and no data conversion/transformation",
                        repair=_repair("add_element", "FIRST-TO-SECOND-DATA-TRANSFORMATION-REF", "Reference a valid DataTransformation or make both data types compatible."))
        if conversion is not None:
            resolve(index, conversion, report, "DataPrototypeMapping transformation")
    return report


@plugin("mode_interface_mapping_compatible")
def mode_interface_mapping_compatible(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for mapping in selected:
        pairs = mapping_pairs(index, mapping, report)
        prototypes = [
            item for item in index.file_by_element
            if local_name(item.tag) == "MODE-DECLARATION-GROUP-PROTOTYPE"
            and any(id(item) in pair for pair in pairs)
        ]
        if len(prototypes) < 2:
            report.incomplete(f"ModeInterfaceMapping has no resolved prototype pair at {index.location(mapping)}")
            continue
        for position, left in enumerate(prototypes):
            for right in prototypes[position + 1:]:
                if (id(left), id(right)) not in pairs:
                    continue
                left_group = _mode_group(index, left, report)
                right_group = _mode_group(index, right, report)
                if left_group is not None and right_group is not None and mode_groups_compatible(index, left_group, right_group, report) is False:
                    report.fail(index, mapping, "ModeInterfaceMapping relates prototypes typed by incompatible ModeDeclarationGroups",
                                repair=_repair("repair_reference", "MODE-DECLARATION-GROUP-PROTOTYPE-MAPPING", "Map prototypes whose ModeDeclarationGroups are compatible."))
    return report


def _type_compu(index: ArxmlIndex, prototype: etree._Element, report: PluginReport) -> etree._Element | None:
    data_type = type_of(index, prototype, report)
    return resolve(index, first(data_type, {"COMPU-METHOD-REF"}), report, "prototype CompuMethod", required=False) if data_type is not None else None


def _scale_set(index: ArxmlIndex, method: etree._Element, report: PluginReport) -> set[str] | None:
    signatures = [compu_scale_signature(item, report, index) for item in owned(index, method, "COMPU-SCALE", {"COMPU-METHOD"})]
    return None if any(item is None for item in signatures) else {repr(item) for item in signatures}


def _decimal_values(container: etree._Element | None, report: PluginReport, index: ArxmlIndex, label: str) -> tuple[Decimal, ...] | None:
    if container is None:
        report.incomplete(f"missing {label}")
        return None
    result: list[Decimal] = []
    for item in container.iterdescendants():
        if local_name(item.tag) not in {"V", "VF"}:
            continue
        try:
            result.append(Decimal(text(item)))
        except InvalidOperation:
            report.incomplete(f"non-numeric {label} coefficient {text(item)!r} at {index.location(item)}")
            return None
    if not result:
        report.incomplete(f"empty {label} at {index.location(container)}")
        return None
    return tuple(result)


def _rational_formula_kind(index: ArxmlIndex, scale: etree._Element, report: PluginReport, kind: str) -> bool | None:
    numerators = _decimal_values(first(scale, {"COMPU-NUMERATOR"}), report, index, "CompuScale numerator")
    denominators = _decimal_values(first(scale, {"COMPU-DENOMINATOR"}), report, index, "CompuScale denominator")
    if numerators is None or denominators is None:
        return None
    if kind == "linear":
        return (
            len(numerators) >= 2 and len(denominators) >= 1
            and numerators[1] != 0 and all(value == 0 for value in numerators[2:])
            and denominators[0] != 0 and all(value == 0 for value in denominators[1:])
        )
    return (
        len(numerators) >= 1 and len(denominators) >= 2
        and numerators[0] != 0 and all(value == 0 for value in numerators[1:])
        and denominators[1] != 0 and all(value == 0 for value in denominators[2:])
    )


def _unit_number(unit: etree._Element, tag: str, default: str, report: PluginReport, index: ArxmlIndex) -> Decimal | None:
    raw = text(first(unit, {tag})) or default
    try:
        return Decimal(raw)
    except InvalidOperation:
        report.incomplete(f"non-numeric Unit.{tag} {raw!r} at {index.location(unit)}")
        return None


def _scaling_units_compatible(
    index: ArxmlIndex,
    left: etree._Element | None,
    right: etree._Element | None,
    report: PluginReport,
) -> bool | None:
    # TPS_SWCT_01549/01550: a missing Unit is imaginary (factor=1, offset=0),
    # and a PhysicalDimension present on only one side is inherited by the other.
    if left is None and right is None:
        return True
    if left is None or right is None:
        actual = right if left is None else left
        factor = _unit_number(actual, "FACTOR-SI-TO-UNIT", "1", report, index)
        offset = _unit_number(actual, "OFFSET-SI-TO-UNIT", "0", report, index)
        return None if factor is None or offset is None else factor == 1 and offset == 0
    left_factor = _unit_number(left, "FACTOR-SI-TO-UNIT", "1", report, index)
    right_factor = _unit_number(right, "FACTOR-SI-TO-UNIT", "1", report, index)
    left_offset = _unit_number(left, "OFFSET-SI-TO-UNIT", "0", report, index)
    right_offset = _unit_number(right, "OFFSET-SI-TO-UNIT", "0", report, index)
    if None in {left_factor, right_factor, left_offset, right_offset}:
        return None
    if left_factor != right_factor or left_offset != right_offset:
        return False
    left_ref = first(left, {"PHYSICAL-DIMENSION-REF"})
    right_ref = first(right, {"PHYSICAL-DIMENSION-REF"})
    if left_ref is None or right_ref is None:
        return True
    left_dimension = resolve(index, left_ref, report, "left Unit PhysicalDimension")
    right_dimension = resolve(index, right_ref, report, "right Unit PhysicalDimension")
    if left_dimension is None or right_dimension is None:
        return None
    return physical_dimension_signature(left_dimension) == physical_dimension_signature(right_dimension)


def _scaling_definition(
    index: ArxmlIndex,
    method: etree._Element | None,
    report: PluginReport,
    kind: str,
) -> bool | None:
    if method is None:
        return kind == "linear"  # the normative default CompuMethod is IDENTICAL
    category = text(direct(method, "CATEGORY"))
    if kind == "linear" and category == "IDENTICAL":
        return True
    if category not in ({"LINEAR", "RAT_FUNC"} if kind == "linear" else {"RAT_FUNC"}):
        return False
    scales = owned(index, method, "COMPU-SCALE", {"COMPU-METHOD"})
    if not scales:
        report.incomplete(f"{category} CompuMethod has no CompuScale at {index.location(method)}")
        return None
    results = [_rational_formula_kind(index, scale, report, kind) for scale in scales]
    return None if any(result is None for result in results) else all(results)


@plugin("communication_compu_scale_compatibility")
def communication_compu_scale_compatibility(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    cid = rule["constraint_id"]
    enabled = {"SCALE_LINEAR_AND_TEXTTABLE", "SCALE_RATIONAL_AND_TEXTTABLE", "TEXTTABLE", "TAB_NOINTP", "BITFIELD_TEXTTABLE", "LINEAR", "RAT_FUNC", "IDENTICAL"}
    for connector in index.select_any(sorted(CONNECTOR_TAGS)):
        endpoints = _connector_endpoints(index, connector, report)
        if len(endpoints) != 2:
            continue
        interfaces = [interface(index, item[1], report) for item in endpoints]
        if any(item is None for item in interfaces):
            continue
        left_members = interface_members(index, interfaces[0], DATA_PROTOTYPES)
        right_members = interface_members(index, interfaces[1], DATA_PROTOTYPES)
        for left in left_members:
            right = next((item for item in right_members if short_name(item) == short_name(left)), None)
            if right is None:
                continue
            left_type = type_of(index, left, report)
            right_type = type_of(index, right, report)
            if left_type is None or right_type is None:
                continue
            left_ref = first(left_type, {"COMPU-METHOD-REF"})
            right_ref = first(right_type, {"COMPU-METHOD-REF"})
            left_method = resolve(index, left_ref, report, "left CompuMethod", required=False) if left_ref is not None else None
            right_method = resolve(index, right_ref, report, "right CompuMethod", required=False) if right_ref is not None else None
            if cid in {"TPS_SWCT_01549", "TPS_SWCT_01550"}:
                kind = "linear" if cid == "TPS_SWCT_01549" else "reciprocal_linear"
                left_formula = _scaling_definition(index, left_method, report, "linear" if kind == "linear" else "reciprocal")
                right_formula = _scaling_definition(index, right_method, report, "linear" if kind == "linear" else "reciprocal")
                left_unit = compu_method_unit(index, left_method, report) if left_method is not None else None
                right_unit = compu_method_unit(index, right_method, report) if right_method is not None else None
                unit_compatible = _scaling_units_compatible(index, left_unit, right_unit, report)
                qualifies = None if None in {left_formula, right_formula, unit_compatible} else bool(left_formula and right_formula and unit_compatible)
                report.observe(
                    semantic="autosar_scaling_definition", constraint=cid, kind=kind,
                    connector=index.path_of(connector), members=[index.path_of(left), index.path_of(right)],
                    left_formula=left_formula, right_formula=right_formula,
                    units_compatible=unit_compatible, qualifies=qualifies,
                )
                continue
            if left_method is None or right_method is None:
                continue
            if first(connector, {"TEXT-TABLE-MAPPING-REF"}) is not None and cid in {"constr_1154", "constr_1155", "constr_1156", "constr_1157"}:
                report.observe(semantic="text_table_mapping_override", connector=index.path_of(connector), constraint=cid)
                continue
            categories = {text(direct(left_method, "CATEGORY")), text(direct(right_method, "CATEGORY"))}
            if cid == "constr_1153":
                report.observe(semantic="compu_scale_compatibility_enabled", context=index.path_of(connector), enabled=categories <= enabled)
                continue
            left_set = _scale_set(index, left_method, report)
            right_set = _scale_set(index, right_method, report)
            if left_set is None or right_set is None:
                continue
            required = _required_endpoint(endpoints)
            provider_set, receiver_set = (right_set, left_set) if required is endpoints[0] else (left_set, right_set)
            if cid in {"constr_1154", "constr_1156", "constr_1157"} and not provider_set <= receiver_set:
                report.fail(index, connector, "Provider CompuScale set is not a subset of the requiring side",
                            repair=_repair("add_or_repair_scale", "COMPU-SCALE", "Add compatible requiring-side scales or repair the conversion mapping."))
            elif cid in {"constr_1176", "constr_1192", "constr_1163"}:
                if compu_methods_compatible(index, left_method, right_method, report) is False:
                    report.fail(index, connector, "Communication CompuMethods do not yield compatible conversions",
                                categories=sorted(categories),
                                repair=_repair("repair_compu_method", "COMPU-METHOD", "Align coefficients, units and applicable scale definitions."))
    return report


def _effective_unit_sources(index: ArxmlIndex, owner: etree._Element, report: PluginReport) -> list[etree._Element]:
    units: list[etree._Element] = []
    for ref in owner.iterdescendants():
        if local_name(ref.tag) != "UNIT-REF":
            continue
        unit = resolve(index, ref, report, "effective Unit")
        if unit is not None and all(unit is not item for item in units):
            units.append(unit)
    return units


@plugin("axis_and_props_units_consistent")
def axis_and_props_units_consistent(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for owner in selected:
        units = _effective_unit_sources(index, owner, report)
        for position, unit in enumerate(units):
            for other in units[position + 1:]:
                compatible = units_compatible(index, unit, other, report)
                if compatible is False:
                    report.fail(index, owner, "Units specified in the same axis/property context are incompatible despite precedence",
                                units=[index.path_of(unit), index.path_of(other)],
                                repair=_repair("repair_reference", "UNIT-REF", "Use compatible Units at every precedence level."))
    return report


@plugin("sw_addr_method_requests_consistent")
def sw_addr_method_requests_consistent(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for prototype in index.select_any(["VARIABLE-DATA-PROTOTYPE", "PARAMETER-DATA-PROTOTYPE"]):
        data_type = type_of(index, prototype, report)
        refs = []
        for owner in [data_type, prototype]:
            if owner is not None:
                refs.extend([item for item in owner.iterdescendants() if local_name(item.tag) == "SW-ADDR-METHOD-REF"])
        targets = [resolve(index, ref, report, "SwAddrMethod request") for ref in refs]
        unique = {id(item): item for item in targets if item is not None}
        if len(unique) > 1:
            report.fail(index, prototype, "Different component/type levels request conflicting SwAddrMethods for one object",
                        methods=[index.path_of(item) for item in unique.values()],
                        repair=_repair("repair_reference", "SW-ADDR-METHOD-REF", "Keep one effective SwAddrMethod request or remove lower-level conflicts."))
    return report


@plugin("constant_mapping_domains")
def constant_mapping_domains(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for mapping in selected:
        app = resolve(index, first(mapping, {"APPL-CONSTANT-REF", "APPLICATION-CONSTANT-REF"}), report, "application ConstantSpecification")
        impl = resolve(index, first(mapping, {"IMPL-CONSTANT-REF", "IMPLEMENTATION-CONSTANT-REF"}), report, "implementation ConstantSpecification")
        if app is None or impl is None:
            continue
        app_value = next((item for item in app.iterdescendants() if local_name(item.tag) in {"APPLICATION-VALUE-SPECIFICATION", "APPLICATION-RULE-BASED-VALUE-SPECIFICATION"}), None)
        impl_value = next((item for item in impl.iterdescendants() if local_name(item.tag) in {"NUMERICAL-VALUE-SPECIFICATION", "TEXT-VALUE-SPECIFICATION", "ARRAY-VALUE-SPECIFICATION", "RECORD-VALUE-SPECIFICATION"}), None)
        if app_value is None or impl_value is None:
            report.fail(index, mapping, "ConstantSpecificationMapping does not map application-domain to implementation-domain values",
                        repair=_repair("repair_reference", "CONSTANT-SPECIFICATION-REF", "Reference one application representation and one implementation representation."))
    return report


@plugin("sender_receiver_invalidation_uniform")
def sender_receiver_invalidation_uniform(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for interface_element in selected:
        policies: dict[str, list[etree._Element]] = defaultdict(list)
        for variable in interface_members(index, interface_element, {"VARIABLE-DATA-PROTOTYPE"}):
            policy = next((item for item in index.descendants(interface_element, {"INVALIDATION-POLICY"})
                           if resolve(index, first(item, {"DATA-ELEMENT-REF"}), report, "InvalidationPolicy data element") is variable), None)
            value = text(first(policy, {"HANDLE-INVALID"})) if policy is not None else ""
            policies[value].append(variable)
        if len(policies) > 1:
            report.fail(index, interface_element, "VariableDataPrototypes in one SenderReceiverInterface use different invalidation policies",
                        policies={key: [index.path_of(item) for item in values] for key, values in policies.items()},
                        repair=_repair("replace_value", "HANDLE-INVALID", "Use the same invalidationPolicy for every interface variable."))
    return report


def _transition_signature(index: ArxmlIndex, transition: etree._Element, report: PluginReport) -> tuple[str, str, str] | None:
    entered = resolve(index, first(transition, {"ENTERED-MODE-REF"}), report, "enteredMode")
    exited = resolve(index, first(transition, {"EXITED-MODE-REF"}), report, "exitedMode")
    return None if entered is None or exited is None else (short_name(transition), short_name(entered), short_name(exited))


@plugin("mode_group_and_transition_compatibility")
def mode_group_and_transition_compatibility(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    pairs: list[tuple[etree._Element, etree._Element, etree._Element]] = []
    for mapping in index.elements("MODE-INTERFACE-MAPPING") + index.elements("MODE-DECLARATION-MAPPING-SET"):
        groups: list[etree._Element] = []
        for ref in mapping.iterdescendants():
            target = resolve(index, ref, report, "mode mapping reference") if local_name(ref.tag).endswith("-REF") else None
            group = index.nearest(target, {"MODE-DECLARATION-GROUP"}) if target is not None else None
            if group is not None and all(group is not item for item in groups):
                groups.append(group)
        if len(groups) == 2:
            pairs.append((mapping, groups[0], groups[1]))
    for context, left, right in pairs:
        if mode_groups_compatible(index, left, right, report) is False:
            report.fail(index, context, "Mapped ModeDeclarationGroups are incompatible",
                        repair=_repair("repair_mode_group", "MODE-DECLARATION-GROUP", "Align mode names, initial/default modes, policies, ordering and values."))
        left_transitions = {_transition_signature(index, item, report) for item in owned(index, left, "MODE-TRANSITION", {"MODE-DECLARATION-GROUP"})}
        right_transitions = {_transition_signature(index, item, report) for item in owned(index, right, "MODE-TRANSITION", {"MODE-DECLARATION-GROUP"})}
        left_transitions.discard(None)
        right_transitions.discard(None)
        if left_transitions and right_transitions and left_transitions != right_transitions:
            report.fail(index, context, "ModeDeclarationGroups define non-identical ModeTransitions",
                        left=sorted(left_transitions), right=sorted(right_transitions),
                        repair=_repair("repair_mode_transition", "MODE-TRANSITION", "Align transition short names and entered/exited mode targets or provide an explicit mapping."))
    return report


def _event_port(index: ArxmlIndex, event: etree._Element, report: PluginReport) -> etree._Element | None:
    """Resolve the P/PR port from OperationInvokedEvent.operationIref."""
    return resolve(
        index,
        first(event, {"CONTEXT-P-PORT-REF", "TARGET-P-PORT-REF", "P-PORT-PROTOTYPE-REF", "PORT-PROTOTYPE-REF"}),
        report,
        "OperationInvokedEvent context provided port",
    )


def _event_mapping_sets(index: ArxmlIndex, event: etree._Element, report: PluginReport) -> list[etree._Element]:
    behavior = index.nearest(event, {"SWC-INTERNAL-BEHAVIOR"})
    if behavior is None:
        report.incomplete(f"OperationInvokedEvent has no containing SwcInternalBehavior at {index.location(event)}")
        return []
    result: list[etree._Element] = []
    for ref in behavior.iterdescendants():
        tag = local_name(ref.tag)
        if tag not in {"DATA-TYPE-MAPPING-REF", "DATA-TYPE-MAPPING-SET-REF"}:
            continue
        target = resolve(index, ref, report, "SwcInternalBehavior DataTypeMappingSet")
        if target is not None and local_name(target.tag) == "DATA-TYPE-MAPPING-SET" and all(target is not item for item in result):
            result.append(target)
    return result


def _effective_impl_type(
    index: ArxmlIndex,
    event: etree._Element,
    data_type: etree._Element,
    report: PluginReport,
) -> etree._Element | None:
    """Resolve the implementation type that determines the generated C signature."""
    if local_name(data_type.tag) == "IMPLEMENTATION-DATA-TYPE":
        return unwrap_impl(index, data_type, report)
    if local_name(data_type.tag) not in APP_TYPES:
        report.incomplete(f"unsupported runnable argument type {local_name(data_type.tag)} at {index.location(data_type)}")
        return None
    mapping_sets = _event_mapping_sets(index, event, report)
    if not mapping_sets:
        report.incomplete(f"no applicable DataTypeMappingSet for {index.path_of(data_type)} at {index.location(event)}")
        return None
    candidates: list[etree._Element] = []
    for mapping_set in mapping_sets:
        for mapping in owned(index, mapping_set, "DATA-TYPE-MAP", {"DATA-TYPE-MAPPING-SET"}):
            mapped_app = resolve(index, first(mapping, {"APPLICATION-DATA-TYPE-REF"}), report, "DataTypeMap application type")
            if mapped_app is not data_type:
                continue
            mapped_impl = resolve(index, first(mapping, {"IMPLEMENTATION-DATA-TYPE-REF"}), report, "DataTypeMap implementation type")
            if mapped_impl is not None and all(mapped_impl is not item for item in candidates):
                candidates.append(mapped_impl)
    if len(candidates) != 1:
        report.incomplete(
            f"expected one applicable implementation mapping for {index.path_of(data_type)} at "
            f"{index.location(event)}, found {len(candidates)}"
        )
        return None
    return unwrap_impl(index, candidates[0], report)


def _port_argument_values(
    index: ArxmlIndex,
    event: etree._Element,
    port: etree._Element,
    report: PluginReport,
) -> list[etree._Element] | None:
    matching: list[etree._Element] = []
    for option in index.elements("PORT-API-OPTION"):
        option_port = resolve(index, first(option, {"PORT-REF"}), report, "PortApiOption port")
        if option_port is port:
            matching.append(option)
    if len(matching) > 1:
        report.incomplete(
            f"multiple PortApiOptions apply to {index.path_of(port)} at {index.location(event)}; "
            "the active variant cannot be proven"
        )
        return None
    return owned(index, matching[0], "PORT-DEFINED-ARGUMENT-VALUE", {"PORT-API-OPTION"}) if matching else []


def _effective_arguments(
    index: ArxmlIndex,
    event: etree._Element,
    operation: etree._Element,
    report: PluginReport,
) -> list[dict[str, object]] | None:
    """Build the ordered RTE server signature: implicit port values, then formal arguments."""
    port = _event_port(index, event, report)
    if port is None:
        return None
    port_values = _port_argument_values(index, event, port, report)
    if port_values is None:
        return None
    result: list[dict[str, object]] = []
    for value in port_values:
        value_type = resolve(index, first(value, {"VALUE-TYPE-TREF"}), report, "PortDefinedArgumentValue valueType")
        final = unwrap_impl(index, value_type, report) if value_type is not None and local_name(value_type.tag) == "IMPLEMENTATION-DATA-TYPE" else None
        if final is None:
            if value_type is not None:
                report.incomplete(f"PortDefinedArgumentValue does not resolve to an ImplementationDataType at {index.location(value)}")
            return None
        result.append({"source": value, "kind": "port_value", "direction": "IN", "policy": "USE-ARGUMENT-TYPE", "type": final})
    for argument in owned(index, operation, "ARGUMENT-DATA-PROTOTYPE", {"CLIENT-SERVER-OPERATION"}):
        direction = text(first(argument, {"DIRECTION"})).upper()
        if not direction:
            report.incomplete(f"ArgumentDataPrototype direction is missing at {index.location(argument)}")
            return None
        policy = text(first(argument, {"SERVER-ARGUMENT-IMPL-POLICY"})).upper() or "USE-ARGUMENT-TYPE"
        if policy not in {"USE-ARGUMENT-TYPE", "USE-ARRAY-BASE-TYPE", "USE-VOID"}:
            report.incomplete(f"unsupported serverArgumentImplPolicy {policy!r} at {index.location(argument)}")
            return None
        declared = type_of(index, argument, report)
        if declared is None:
            return None
        final = _effective_impl_type(index, event, declared, report)
        if final is None:
            return None
        result.append({"source": argument, "kind": "formal", "direction": direction, "policy": policy, "type": final})
    return result


def _array_base_compatible(index: ArxmlIndex, left: etree._Element, right: etree._Element, report: PluginReport) -> bool | None:
    left = unwrap_impl(index, left, report)
    right = unwrap_impl(index, right, report)
    if left is None or right is None:
        return None
    if text(direct(left, "CATEGORY")) != "ARRAY" or text(direct(right, "CATEGORY")) != "ARRAY":
        return False
    left_elements = owned(index, left, "IMPLEMENTATION-DATA-TYPE-ELEMENT", {"IMPLEMENTATION-DATA-TYPE", "IMPLEMENTATION-DATA-TYPE-ELEMENT"})
    right_elements = owned(index, right, "IMPLEMENTATION-DATA-TYPE-ELEMENT", {"IMPLEMENTATION-DATA-TYPE", "IMPLEMENTATION-DATA-TYPE-ELEMENT"})
    if len(left_elements) != 1 or len(right_elements) != 1:
        report.incomplete(f"USE-ARRAY-BASE-TYPE requires exactly one array element at {index.location(left if len(left_elements) != 1 else right)}")
        return None
    ignored = DOC_TAGS | {"SHORT-NAME", "ARRAY-SIZE", "ARRAY-SIZE-SEMANTICS", "ARRAY-SIZE-HANDLING", "TYPE-TREF", "IMPLEMENTATION-DATA-TYPE-REF"}
    if canonical(left_elements[0], ignored=ignored) != canonical(right_elements[0], ignored=ignored):
        return False
    left_ref = first(left_elements[0], {"TYPE-TREF", "IMPLEMENTATION-DATA-TYPE-REF"})
    right_ref = first(right_elements[0], {"TYPE-TREF", "IMPLEMENTATION-DATA-TYPE-REF"})
    if left_ref is None or right_ref is None:
        return left_ref is None and right_ref is None
    left_type = resolve(index, left_ref, report, "left array base element type")
    right_type = resolve(index, right_ref, report, "right array base element type")
    return None if left_type is None or right_type is None else data_types_compatible(index, left_type, right_type, report)


def _effective_argument_compatible(index: ArxmlIndex, left: dict[str, object], right: dict[str, object], report: PluginReport) -> bool | None:
    if left["direction"] != right["direction"]:
        return False
    left_policy = str(left["policy"])
    right_policy = str(right["policy"])
    if left_policy == "USE-VOID" or right_policy == "USE-VOID":
        return left_policy == right_policy
    if left_policy == "USE-ARRAY-BASE-TYPE" or right_policy == "USE-ARRAY-BASE-TYPE":
        if left_policy != right_policy:
            return False
        return _array_base_compatible(index, left["type"], right["type"], report)
    return data_types_compatible(index, left["type"], right["type"], report)


def _error_signature(index: ArxmlIndex, operation: etree._Element, report: PluginReport) -> tuple[tuple[str, str], ...]:
    return tuple(sorted((short_name(error), text(first(error, {"ERROR-CODE"}))) for error in operation_errors(index, operation, report)))


@plugin("runnable_operation_signatures")
def runnable_operation_signatures(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    cid = rule["constraint_id"]
    by_runnable: dict[int, tuple[etree._Element, list[tuple[etree._Element, etree._Element]]]] = {}
    for event in index.elements("OPERATION-INVOKED-EVENT"):
        runnable = resolve(index, first(event, {"START-ON-EVENT-REF"}), report, "OperationInvokedEvent runnable")
        operation = resolve(index, first(event, {"TARGET-PROVIDED-OPERATION-REF", "OPERATION-REF"}), report, "OperationInvokedEvent operation")
        if runnable is not None and operation is not None:
            by_runnable.setdefault(id(runnable), (runnable, []))[1].append((event, operation))
    for runnable, entries in by_runnable.values():
        for position, (event, operation) in enumerate(entries):
            for other_event, other in entries[position + 1:]:
                operation_errors_for_event = operation_errors(index, operation, report)
                other_errors = operation_errors(index, other, report)
                if cid == "TPS_SWCT_01520":
                    if bool(operation_errors_for_event) == bool(other_errors):
                        continue
                    report.fail(index, event, "ClientServerOperations triggering the same RunnableEntity disagree on whether a return/error value exists",
                                runnable=index.path_of(runnable), operations=[index.path_of(operation), index.path_of(other)],
                                first_possible_error_count=len(operation_errors_for_event), second_possible_error_count=len(other_errors),
                                repair=_repair("repair_operation_signature", "POSSIBLE-ERROR-REF", "Make the Std_ReturnType/void behavior and possibleErrors identical for all triggering operations."))
                    continue
                left_args = _effective_arguments(index, event, operation, report)
                right_args = _effective_arguments(index, other_event, other, report)
                if left_args is None or right_args is None:
                    continue
                mismatch: str | None = None
                if len(left_args) != len(right_args):
                    mismatch = "effective argument counts differ"
                else:
                    for argument_position, (left_arg, right_arg) in enumerate(zip(left_args, right_args), start=1):
                        compatible = _effective_argument_compatible(index, left_arg, right_arg, report)
                        if compatible is None:
                            mismatch = None
                            break
                        if compatible is False:
                            mismatch = f"effective argument {argument_position} is incompatible"
                            break
                if mismatch is None and len(left_args) == len(right_args):
                    left_errors = _error_signature(index, operation, report)
                    right_errors = _error_signature(index, other, report)
                    if left_errors != right_errors:
                        mismatch = "possibleErrors or Std_ReturnType/void behavior differ"
                if mismatch is not None:
                    report.fail(
                        index, event,
                        "ClientServerOperations triggering the same RunnableEntity have incompatible generated signatures",
                        reason=mismatch, runnable=index.path_of(runnable),
                        operations=[index.path_of(operation), index.path_of(other)],
                        effective_argument_counts=[len(left_args), len(right_args)],
                        repair=_repair(
                            "repair_operation_signature", "CLIENT-SERVER-OPERATION",
                            "Align ordered PortDefinedArgumentValues and formal arguments, directions, serverArgumentImplPolicy effective implementation types, and possibleErrors.",
                        ),
                    )
    return report


def _component_for_port(index: ArxmlIndex, port: etree._Element) -> etree._Element | None:
    return index.nearest(port, COMPONENT_TAGS)


@plugin("service_component_graph_rules")
def service_component_graph_rules(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    cid = rule["constraint_id"]
    if cid == "TPS_SWCT_01044":
        for needs in selected:
            owner = index.nearest(needs, COMPONENT_TAGS)
            if owner is None or local_name(owner.tag) not in ATOMIC_TAGS | {"NV-BLOCK-SW-COMPONENT-TYPE"}:
                report.fail(index, needs, "ServiceNeeds is not owned by an eligible atomic/NvBlock software-component type",
                            repair=_repair("move_element", local_name(needs.tag), "Place ServiceNeeds under an eligible atomic software-component internal behavior."))
        return report
    if cid == "constr_2019":
        for component in selected:
            for port in index.descendants(component, PORT_TAGS):
                port_if = interface(index, port, report)
                if port_if is not None and _is_service(port_if) != "true":
                    report.fail(index, port, "ServiceSwComponentType port uses an interface with isService=false",
                                repair=_repair("repair_reference", "INTERFACE-TREF", "Reference a service PortInterface."))
        return report
    for connector in index.select_any(sorted(CONNECTOR_TAGS)):
        endpoints = _connector_endpoints(index, connector, report)
        if len(endpoints) != 2:
            continue
        owners = [_component_for_port(index, item[1]) for item in endpoints]
        owner_tags = [local_name(item.tag) if item is not None else "" for item in owners]
        port_tags = [local_name(item[1].tag) for item in endpoints]
        interfaces = [interface(index, item[1], report) for item in endpoints]
        if cid == "TPS_SWCT_02500" and ({"APPLICATION-SW-COMPONENT-TYPE", "SERVICE-SW-COMPONENT-TYPE"} <= set(owner_tags)):
            if not ({"R-PORT-PROTOTYPE", "P-PORT-PROTOTYPE"} <= set(port_tags)):
                report.fail(index, connector, "Application/service component connector does not pair required and provided port roles",
                            repair=_repair("repair_connector_endpoint", "SW-CONNECTOR", "Connect the application R port to the service P port."))
        elif cid == "constr_2011" and "NV-BLOCK-SW-COMPONENT-TYPE" in owner_tags:
            opposite = 1 - owner_tags.index("NV-BLOCK-SW-COMPONENT-TYPE")
            if owner_tags[opposite] not in ATOMIC_TAGS - {"NV-BLOCK-SW-COMPONENT-TYPE"} or interfaces[opposite] is None or local_name(interfaces[opposite].tag) not in {"NV-DATA-INTERFACE", "SENDER-RECEIVER-INTERFACE"}:
                report.fail(index, connector, "NvBlock component port is not connected to an eligible atomic component NvData/SenderReceiver port",
                            repair=_repair("repair_connector_endpoint", "SW-CONNECTOR", "Connect to another atomic component port typed by NvDataInterface or SenderReceiverInterface."))
    return report


@plugin("remote_service_proxy_port")
def remote_service_proxy_port(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for port in selected:
        owner = _component_for_port(index, port)
        if owner is None or local_name(owner.tag) != "SERVICE-PROXY-SW-COMPONENT-TYPE" or local_name(port.tag) != "R-PORT-PROTOTYPE":
            report.fail(index, port, "Manifest-declared remote service-proxy target is not an RPortPrototype of ServiceProxySwComponentType",
                        repair=_repair("repair_target_or_port", "R-PORT-PROTOTYPE", "Bind an R port owned by ServiceProxySwComponentType."))
            continue
        port_if = interface(index, port, report)
        if port_if is not None and local_name(port_if.tag) != "SENDER-RECEIVER-INTERFACE":
            report.fail(index, port, "Remote ServiceProxy R port is not typed by SenderReceiverInterface",
                        repair=_repair("repair_reference", "REQUIRED-INTERFACE-TREF", "Reference a SenderReceiverInterface."))
        connectors = [connector for connector in index.select_any(sorted(CONNECTOR_TAGS)) if any(target is port for _, target in _connector_endpoints(index, connector, report))]
        if not connectors:
            report.fail(index, port, "Remote ServiceProxy R port has no communication connector",
                        repair=_repair("add_connector", "ASSEMBLY-SW-CONNECTOR", "Connect the remote receive port in the intended 1:n scenario."))
    return report


def _is_data_reference(index: ArxmlIndex, data_type: etree._Element, report: PluginReport) -> bool | None:
    if local_name(data_type.tag) == "IMPLEMENTATION-DATA-TYPE":
        final = unwrap_impl(index, data_type, report)
        return None if final is None else text(direct(final, "CATEGORY")) == "DATA_REFERENCE"
    implementations = [impl for mapping in index.elements("DATA-TYPE-MAP")
                       if resolve(index, first(mapping, {"APPLICATION-DATA-TYPE-REF"}), report, "mapped app type") is data_type
                       for impl in [resolve(index, first(mapping, {"IMPLEMENTATION-DATA-TYPE-REF"}), report, "mapped impl type")]
                       if impl is not None]
    if not implementations:
        return False
    results = [_is_data_reference(index, item, report) for item in implementations]
    return None if any(item is None for item in results) else any(results)


@plugin("data_reference_usage_restrictions")
def data_reference_usage_restrictions(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    cid = rule["constraint_id"]
    if cid == "constr_1296":
        for variable in index.elements("VARIABLE-DATA-PROTOTYPE"):
            if index.nearest(variable, {"EXPLICIT-INTER-RUNNABLE-VARIABLES", "IMPLICIT-INTER-RUNNABLE-VARIABLES"}) is None:
                continue
            data_type = type_of(index, variable, report)
            if data_type is not None and _is_data_reference(index, data_type, report) is True:
                report.fail(index, variable, "Inter-runnable variable uses DATA_REFERENCE representation",
                            repair=_repair("repair_reference", "TYPE-TREF", "Use a non-DATA_REFERENCE data type for inter-runnable communication."))
        return report
    for interface_element in index.select_any(sorted(DATA_INTERFACES | {"CLIENT-SERVER-INTERFACE"})):
        affected = []
        for prototype in interface_members(index, interface_element, DATA_PROTOTYPES):
            data_type = type_of(index, prototype, report)
            if data_type is not None and _is_data_reference(index, data_type, report) is True:
                affected.append(prototype)
        if not affected:
            continue
        components = []
        for port in index.select_any(sorted(PORT_TAGS)):
            port_if = interface(index, port, report)
            if port_if is interface_element:
                owner = _component_for_port(index, port)
                if owner is not None:
                    components.append(owner)
        if components and not any(local_name(item.tag) in SAFE_DATA_REFERENCE_COMPONENTS for item in components):
            report.fail(index, affected[0], "DATA_REFERENCE interface is used only by application/sensor-actuator components",
                        components=[index.path_of(item) for item in components],
                        repair=_repair("repair_architecture", "PORT-PROTOTYPE", "Include an eligible service/CDD/parameter/NvBlock/ECU-abstraction provider or requester."))
    return report


@plugin("nv_block_data_type_compatibility")
def nv_block_data_type_compatibility(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    cid = rule["constraint_id"]
    if cid == "constr_2012":
        for descriptor in index.elements("NV-BLOCK-DESCRIPTOR"):
            ram = resolve(index, first(descriptor, {"RAM-BLOCK-REF"}), report, "NvBlockDescriptor ramBlock", required=False)
            rom = resolve(index, first(descriptor, {"ROM-BLOCK-REF"}), report, "NvBlockDescriptor romBlock", required=False)
            if ram is None or rom is None:
                continue
            ram_type = type_of(index, ram, report)
            rom_type = type_of(index, rom, report)
            if ram_type is not None and rom_type is not None and data_types_compatible(index, ram_type, rom_type, report) is False:
                report.fail(index, descriptor, "NvBlockDescriptor ramBlock and romBlock use incompatible ImplementationDataTypes",
                            repair=_repair("repair_reference", "ROM-BLOCK-REF", "Use a ROM block with an implementation type compatible with the RAM block."))
    else:
        for mapping in index.elements("NV-BLOCK-DATA-MAPPING"):
            ram = resolve(index, first(mapping, {"NV-RAM-BLOCK-ELEMENT-REF"}), report, "nvRamBlockElement")
            ram_type = type_of(index, ram, report) if ram is not None and local_name(ram.tag) in DATA_PROTOTYPES else (
                resolve(index, first(ram, {"IMPLEMENTATION-DATA-TYPE-REF"}), report, "nvRamBlockElement type") if ram is not None else None
            )
            for role in {"WRITTEN-NV-DATA", "WRITTEN-READ-NV-DATA", "READ-NV-DATA"}:
                prototype = resolve(index, first(mapping, {f"{role}-REF"}), report, role, required=False)
                other_type = type_of(index, prototype, report) if prototype is not None else None
                if ram_type is not None and other_type is not None and data_types_compatible(index, ram_type, other_type, report) is False:
                    report.fail(index, mapping, "NvBlockDataMapping references incompatible implementation types",
                                role=role, repair=_repair("repair_reference", f"{role}-REF", "Reference NvData with a type compatible with nvRamBlockElement."))
    return report


@plugin("manifest_reference_target_table")
def manifest_reference_target_table(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for owner in selected:
        params = _parameters(index, rule, owner, report)
        if params is None:
            continue
        allowed = set(params.get("allowed_target_tags") or [])
        if not allowed:
            report.incomplete(f"allowed_target_tags is missing for {index.path_of(owner)}")
            continue
        for ref in owner.iterdescendants():
            if local_name(ref.tag) not in {"BY-PASS-POINT-IREF", "RPT-AR-HOOK-IREF", "BY-PASS-POINT-REF", "RPT-HOOK-REF"} and not index.nearest(ref, {"BY-PASS-POINT-IREF", "RPT-AR-HOOK-IREF"}):
                continue
            if not local_name(ref.tag).endswith("-REF"):
                continue
            target = resolve(index, ref, report, "RPT table target")
            if target is not None and local_name(target.tag) not in allowed:
                report.fail(index, ref, "RPT reference target is forbidden by the manifest-bound Table 13.4 row",
                            actual=local_name(target.tag), allowed=sorted(allowed),
                            repair=_repair("repair_reference", local_name(ref.tag), "Reference a target kind allowed for the RptContainer category."))
    return report


@plugin("manifest_nv_blueprint_interface")
def manifest_nv_blueprint_interface(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for port in selected:
        params = _parameters(index, rule, port, report)
        if params is None:
            continue
        allowed = set(params.get("allowed_interface_paths") or [])
        if not allowed:
            report.incomplete(f"allowed_interface_paths is missing for {index.path_of(port)}")
            continue
        port_if = interface(index, port, report)
        if port_if is not None and index.path_of(port_if) not in allowed:
            report.fail(index, port, "NV-management ClientServer port is not typed by an allowed MOD_GeneralBlueprints-derived interface",
                        actual=index.path_of(port_if), allowed=sorted(allowed),
                        repair=_repair("repair_reference", "INTERFACE-TREF", "Reference one of the manifest-declared blueprint-compatible interfaces."))
    return report


@plugin("application_mode_manager_topology")
def application_mode_manager_topology(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for component in selected:
        rports = index.descendants(component, {"R-PORT-PROTOTYPE", "PR-PORT-PROTOTYPE"})
        service_request = [port for port in rports if (port_if := interface(index, port, report)) is not None and local_name(port_if.tag) == "SENDER-RECEIVER-INTERFACE" and _is_service(port_if) == "true"]
        app_request = [port for port in rports if (port_if := interface(index, port, report)) is not None and local_name(port_if.tag) == "SENDER-RECEIVER-INTERFACE" and _is_service(port_if) == "false"]
        if not service_request or not app_request:
            continue
        mode_ports = [port for port in index.descendants(component, {"P-PORT-PROTOTYPE", "PR-PORT-PROTOTYPE"})
                      if (port_if := interface(index, port, report)) is not None and local_name(port_if.tag) == "MODE-SWITCH-INTERFACE"]
        if len(mode_ports) != 1:
            report.fail(index, component, "Application Mode Manager interacting with BswM and applications must expose one mode-notification provided port",
                        actual=len(mode_ports), expected=1,
                        repair=_repair("set_cardinality", "P-PORT-PROTOTYPE", "Expose one provided ModeSwitchInterface port for all notifications.", expected=1))
        elif _is_service(interface(index, mode_ports[0], report)) != "false":
            report.fail(index, mode_ports[0], "Application Mode Manager notification ModeSwitchInterface has isService=true",
                        repair=_repair("replace_value", "IS-SERVICE", "Set isService=false for the shared notification interface."))
    return report


@plugin("nv_service_dependency_same_ram_block")
def nv_service_dependency_same_ram_block(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for dependency in selected:
        nv_ports: list[etree._Element] = []
        for assignment in owned(index, dependency, "ROLE-BASED-PORT-ASSIGNMENT", {"SWC-SERVICE-DEPENDENCY"}):
            if text(first(assignment, {"ROLE"})) != "NvDataPort":
                continue
            port = resolve(index, first(assignment, {"ASSIGNED-PORT-REF", "PORT-PROTOTYPE-REF"}), report, "NvDataPort assignment")
            if port is not None:
                nv_ports.append(port)
        ram_blocks: set[int] = set()
        ram_elements: list[etree._Element] = []
        for port in nv_ports:
            port_if = interface(index, port, report)
            if port_if is None:
                continue
            for data in interface_members(index, port_if, {"VARIABLE-DATA-PROTOTYPE"}):
                matched = False
                for mapping in index.elements("NV-BLOCK-DATA-MAPPING"):
                    targets = [resolve(index, ref, report, "NvBlockDataMapping target") for ref in mapping.iterdescendants() if local_name(ref.tag).endswith("-REF")]
                    if data not in targets:
                        continue
                    descriptor = index.nearest(mapping, {"NV-BLOCK-DESCRIPTOR"}) or resolve(index, first(mapping, {"NV-BLOCK-DESCRIPTOR-REF"}), report, "NvBlockDescriptor", required=False)
                    ram = resolve(index, first(descriptor, {"RAM-BLOCK-REF"}), report, "NvBlockDescriptor ramBlock") if descriptor is not None else None
                    if ram is not None:
                        matched = True
                        ram_blocks.add(id(ram))
                        ram_elements.append(ram)
                if not matched:
                    report.incomplete(f"NvDataPort data has no complete NvBlockDataMapping at {index.location(data)}")
        if len(ram_blocks) > 1:
            report.fail(index, dependency, "NvDataPort assignments of one SwcServiceDependency map to different NvBlockDescriptor RAM blocks",
                        ram_blocks=[index.path_of(item) for item in ram_elements],
                        repair=_repair("repair_nv_mapping", "NV-BLOCK-DATA-MAPPING", "Map all NvData of this dependency to one identical NvBlockDescriptor.ramBlock."))
    return report


def _table61_key(interface_element: etree._Element, member: etree._Element) -> tuple[str, str] | None:
    """Return the exact row/column key used by AUTOSAR Table 6.1."""
    interface_tag = local_name(interface_element.tag)
    member_tag = local_name(member.tag)
    policy = text(first(member, {"SW-IMPL-POLICY"})).lower() or "standard"
    if interface_tag == "PARAMETER-INTERFACE" and member_tag == "PARAMETER-DATA-PROTOTYPE" and policy in {"fixed", "const", "standard"}:
        return "Prm", policy
    if interface_tag == "SENDER-RECEIVER-INTERFACE" and member_tag == "VARIABLE-DATA-PROTOTYPE" and policy in {"standard", "queued"}:
        return "S/R", policy
    if interface_tag == "NV-DATA-INTERFACE" and member_tag == "VARIABLE-DATA-PROTOTYPE" and policy == "standard":
        return "NvD", policy
    return None


def _table61_orientation(
    connector: etree._Element,
    endpoints: list[tuple[etree._Element, etree._Element]],
) -> tuple[etree._Element, etree._Element] | None:
    """Orient endpoints as the row and column sides printed in Table 6.1."""
    connector_tag = local_name(connector.tag)
    if connector_tag == "ASSEMBLY-SW-CONNECTOR":
        row = next((port for ref, port in endpoints if local_name(ref.tag) == "TARGET-P-PORT-REF" or local_name(port.tag) == "P-PORT-PROTOTYPE"), None)
        column = next((port for ref, port in endpoints if local_name(ref.tag) == "TARGET-R-PORT-REF" or local_name(port.tag) == "R-PORT-PROTOTYPE"), None)
    elif connector_tag == "PASS-THROUGH-SW-CONNECTOR":
        row = next((port for ref, port in endpoints if local_name(ref.tag) == "REQUIRED-OUTER-PORT-REF" or local_name(port.tag) == "R-PORT-PROTOTYPE"), None)
        column = next((port for ref, port in endpoints if local_name(ref.tag) == "PROVIDED-OUTER-PORT-REF" or local_name(port.tag) == "P-PORT-PROTOTYPE"), None)
    elif connector_tag == "DELEGATION-SW-CONNECTOR":
        outer = next((port for ref, port in endpoints if "OUTER-PORT-REF" in local_name(ref.tag)), None)
        inner = next((port for ref, port in endpoints if port is not outer), None)
        if outer is None or inner is None:
            return None
        if local_name(outer.tag) == "R-PORT-PROTOTYPE":
            row, column = outer, inner
        elif local_name(outer.tag) == "P-PORT-PROTOTYPE":
            row, column = inner, outer
        else:
            return None
    else:
        return None
    return (row, column) if row is not None and column is not None and row is not column else None


@plugin("interface_member_compatibility_table")
def interface_member_compatibility_table(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_1071: execute the complete, directional Table 6.1 matrix."""
    report = PluginReport(checked=len(selected))
    columns = [
        ("Prm", "fixed"), ("Prm", "const"), ("Prm", "standard"),
        ("S/R", "standard"), ("S/R", "queued"), ("NvD", "standard"),
    ]
    yes_by_row = {
        ("Prm", "fixed"): {0, 1, 2, 3, 5},
        ("Prm", "const"): {1, 2, 3, 5},
        ("Prm", "standard"): {2, 3, 5},
        ("S/R", "standard"): {3, 5},
        ("S/R", "queued"): {4},
        ("NvD", "standard"): {3, 5},
    }
    allowed = {(row, columns[position]) for row, positions in yes_by_row.items() for position in positions}
    for connector in selected:
        endpoints = _connector_endpoints(index, connector, report)
        if len(endpoints) != 2:
            continue
        orientation = _table61_orientation(connector, endpoints)
        if orientation is None:
            report.incomplete(f"cannot orient connector endpoints for Table 6.1 at {index.location(connector)}")
            continue
        row_port, column_port = orientation
        row_interface = interface(index, row_port, report)
        column_interface = interface(index, column_port, report)
        if row_interface is None or column_interface is None:
            continue
        row_members = interface_members(index, row_interface, DATA_PROTOTYPES)
        column_members = interface_members(index, column_interface, DATA_PROTOTYPES)
        explicit, mappings = _connector_mapping(index, connector, report)
        pairs: list[tuple[etree._Element, etree._Element]] = []
        for row_member in row_members:
            for column_member in column_members:
                if (explicit and (id(row_member), id(column_member)) in explicit) or (
                    not explicit and short_name(row_member) == short_name(column_member)
                ):
                    pairs.append((row_member, column_member))
        for row_member, column_member in pairs:
            row_key = _table61_key(row_interface, row_member)
            column_key = _table61_key(column_interface, column_member)
            if row_key is None or column_key is None:
                report.incomplete(
                    f"Table 6.1 has no key for {local_name(row_interface.tag)}/{local_name(row_member.tag)} "
                    f"or {local_name(column_interface.tag)}/{local_name(column_member.tag)} at {index.location(connector)}"
                )
                continue
            if (row_key, column_key) not in allowed:
                report.fail(
                    index, connector,
                    "PortInterface member combination is forbidden by AUTOSAR Table 6.1",
                    row={"interface": row_key[0], "sw_impl_policy": row_key[1], "member": index.path_of(row_member)},
                    column={"interface": column_key[0], "sw_impl_policy": column_key[1], "member": index.path_of(column_member)},
                    explicit_mapping=bool(mappings),
                    repair=_repair("repair_interface_member", "SW-IMPL-POLICY", "Use a Table 6.1 'yes' combination or repair the correlated interface members."),
                )
            else:
                report.observe(semantic="autosar_table_6_1", connector=index.path_of(connector), row=row_key, column=column_key)
    return report


@plugin("client_server_compu_scale_compatibility")
def client_server_compu_scale_compatibility(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_1155: compare argument scale sets in the direction of data flow."""
    report = PluginReport(checked=len(selected))
    for connector in selected:
        endpoints = _connector_endpoints(index, connector, report)
        if len(endpoints) != 2:
            continue
        client_endpoint = next((item for item in endpoints if local_name(item[1].tag) in {"R-PORT-PROTOTYPE", "PR-PORT-PROTOTYPE"}), None)
        server_endpoint = next((item for item in endpoints if item is not client_endpoint), None)
        if client_endpoint is None or server_endpoint is None:
            report.incomplete(f"client/server endpoint roles are ambiguous at {index.location(connector)}")
            continue
        client_interface = interface(index, client_endpoint[1], report)
        server_interface = interface(index, server_endpoint[1], report)
        if client_interface is None or server_interface is None:
            continue
        if local_name(client_interface.tag) != "CLIENT-SERVER-INTERFACE" or local_name(server_interface.tag) != "CLIENT-SERVER-INTERFACE":
            continue
        explicit, mappings = _connector_mapping(index, connector, report)
        if first(connector, {"TEXT-TABLE-MAPPING-REF"}) is not None or any(first(item, {"TEXT-TABLE-MAPPING-REF"}) is not None for item in mappings):
            report.observe(semantic="text_table_mapping_override", connector=index.path_of(connector), constraint=rule["constraint_id"])
            continue
        client_operations = interface_members(index, client_interface, {"CLIENT-SERVER-OPERATION"})
        server_operations = interface_members(index, server_interface, {"CLIENT-SERVER-OPERATION"})
        for client_operation in client_operations:
            server_operation = next((item for item in server_operations if (
                (explicit and (id(client_operation), id(item)) in explicit) or
                (not explicit and short_name(client_operation) == short_name(item))
            )), None)
            if server_operation is None:
                continue
            client_arguments = owned(index, client_operation, "ARGUMENT-DATA-PROTOTYPE", {"CLIENT-SERVER-OPERATION"})
            server_arguments = owned(index, server_operation, "ARGUMENT-DATA-PROTOTYPE", {"CLIENT-SERVER-OPERATION"})
            if len(client_arguments) != len(server_arguments):
                report.incomplete(f"cannot align ClientServerOperation arguments at {index.location(client_operation)}")
                continue
            for client_argument, server_argument in zip(client_arguments, server_arguments):
                client_direction = text(first(client_argument, {"DIRECTION"})).upper()
                server_direction = text(first(server_argument, {"DIRECTION"})).upper()
                if client_direction not in {"IN", "OUT", "INOUT"} or client_direction != server_direction:
                    report.incomplete(f"argument direction is missing or inconsistent at {index.location(client_argument)}")
                    continue
                client_method = _type_compu(index, client_argument, report)
                server_method = _type_compu(index, server_argument, report)
                client_scales = set() if client_method is None else _scale_set(index, client_method, report)
                server_scales = set() if server_method is None else _scale_set(index, server_method, report)
                if client_scales is None or server_scales is None:
                    continue
                valid = (
                    client_scales <= server_scales if client_direction == "IN" else
                    server_scales <= client_scales if client_direction == "OUT" else
                    client_scales == server_scales
                )
                if not valid:
                    report.fail(
                        index, client_argument,
                        "Client/server argument CompuScale sets violate the IN/OUT/INOUT subset rule",
                        direction=client_direction, client_scale_count=len(client_scales), server_scale_count=len(server_scales),
                        client_operation=index.path_of(client_operation), server_operation=index.path_of(server_operation),
                        repair=_repair("repair_compu_scale", "COMPU-SCALE", "Align client/server scale sets according to argument direction, or declare an applicable TextTableMapping."),
                    )
    return report


@plugin("rpt_target_category_table")
def rpt_target_category_table(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_2055: execute the complete target-kind rows of AUTOSAR Table 13.4."""
    report = PluginReport(checked=len(selected))
    allowed_by_category = {
        "SW_COMPONENT_PROTOTYPE": {"SW-COMPONENT-PROTOTYPE"},
        "DATA_PROTOTYPE": set(DATA_PROTOTYPES),
        "RUNNABLE_ENTITY": {"RUNNABLE-ENTITY"},
        "ACCESS_POINTS": {
            "VARIABLE-ACCESS", "PARAMETER-ACCESS", "SERVER-CALL-POINT",
            "ASYNCHRONOUS-SERVER-CALL-RESULT-POINT", "INTERNAL-TRIGGERING-POINT",
            "MODE-SWITCH-POINT", "MODE-ACCESS-POINT", "MODE-ACCESS-POINT-IDENT",
            "EXTERNAL-TRIGGERING-POINT", "EXTERNAL-TRIGGERING-POINT-IDENT",
        },
    }
    for container in selected:
        category = text(direct(container, "CATEGORY"))
        allowed = allowed_by_category.get(category)
        if allowed is None:
            report.incomplete(f"RptContainer has a missing or unknown Table 13.4 category {category!r} at {index.location(container)}")
            continue
        target_refs = [item for item in container.iterdescendants() if local_name(item.tag) in {
            "TARGET-REF", "BY-PASS-POINT-REF", "RPT-AR-HOOK-REF", "RPT-HOOK-TARGET-REF",
        }]
        contexts = [item for item in container.iterdescendants() if local_name(item.tag) in {
            "BY-PASS-POINT-IREF", "RPT-AR-HOOK-IREF", "RPT-HOOK",
        }]
        if contexts and not target_refs:
            report.incomplete(f"RptContainer target references cannot be identified at {index.location(container)}")
            continue
        for ref in target_refs:
            target = resolve(index, ref, report, "RptContainer Table 13.4 target")
            if target is not None and local_name(target.tag) not in allowed:
                report.fail(
                    index, ref, "RptContainer reference target is forbidden by AUTOSAR Table 13.4",
                    category=category, actual=local_name(target.tag), allowed=sorted(allowed),
                    repair=_repair("repair_reference", local_name(ref.tag), "Reference a target kind allowed by the RptContainer category."),
                )
    return report
