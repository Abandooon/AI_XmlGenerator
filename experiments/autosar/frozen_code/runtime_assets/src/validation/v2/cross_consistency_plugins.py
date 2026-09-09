"""Reviewed cross-object consistency rules over the resolved ARXML graph."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from lxml import etree

from .arxml_index import ArxmlIndex, local_name, normalized_ref
from .plugins import COMPONENT_TAGS, INTERFACE_REF_TAGS, PORT_TAGS, PluginReport, plugin

DATA_TYPE_TAGS = {
    "APPLICATION-PRIMITIVE-DATA-TYPE", "APPLICATION-ARRAY-DATA-TYPE",
    "APPLICATION-RECORD-DATA-TYPE", "IMPLEMENTATION-DATA-TYPE",
}
TYPE_NODE_TAGS = DATA_TYPE_TAGS | {
    "APPLICATION-ARRAY-ELEMENT", "APPLICATION-RECORD-ELEMENT",
    "IMPLEMENTATION-DATA-TYPE-ELEMENT",
}


def _text(element: etree._Element | None) -> str:
    return (element.text or "").strip() if element is not None else ""


def _truth(element: etree._Element | None) -> bool:
    return _text(element).lower() in {"true", "1"}


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


def _value_key(element: etree._Element | None) -> tuple | None:
    if element is None:
        return None
    raw = _text(element)
    if raw:
        try:
            return ("number", Decimal(raw).normalize().to_eng_string())
        except InvalidOperation:
            return ("text", raw)
    return (
        "tree",
        tuple(
            (local_name(item.tag), _text(item), tuple(sorted(item.attrib.items())))
            for item in element.iter()
            if isinstance(item.tag, str)
        ),
    )


def _type_of(index: ArxmlIndex, prototype: etree._Element, report: PluginReport) -> etree._Element | None:
    ref = _first(prototype, {"TYPE-TREF"})
    if ref is None and local_name(prototype.tag) == "IMPLEMENTATION-DATA-TYPE-ELEMENT":
        ref = _first(prototype, {"IMPLEMENTATION-DATA-TYPE-REF"})
    return _resolve(index, ref, report, f"{local_name(prototype.tag)} type")


def _operation_of_call(index: ArxmlIndex, call: etree._Element, report: PluginReport) -> etree._Element | None:
    return _resolve(index, _first(call, {"TARGET-REQUIRED-OPERATION-REF"}), report, "server call operation")


@plugin("server_call_timeout_consistency")
def server_call_timeout_consistency(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """TPS_SWCT_01344/constr_2023: same operation call points use one timeout."""
    report = PluginReport(checked=len(selected))
    first_by_key: dict[tuple[int, ...], tuple[tuple | None, etree._Element]] = {}
    for call in selected:
        operation = _operation_of_call(index, call, report)
        if operation is None:
            continue
        if rule["constraint_id"] == "constr_2023":
            port = _resolve(index, _first(call, {"CONTEXT-R-PORT-REF"}), report, "server call RPortPrototype")
            if port is None:
                continue
            key = (id(port), id(operation))
        else:
            key = (id(operation),)
        timeout = _direct(call, "TIMEOUT")
        value = _value_key(timeout)
        prior = first_by_key.get(key)
        if prior is None:
            first_by_key[key] = (value, call)
        elif prior[0] != value:
            report.fail(
                index, timeout if timeout is not None else call,
                "ServerCallPoints for the same ClientServerOperation use inconsistent timeout values",
                operation=index.path_of(operation), first_timeout=prior[0], actual_timeout=value,
                first_call=index.location(prior[1]),
                repair=_repair("align_value", "TIMEOUT", "Use the same timeout for every call point of this operation."),
            )
    return report


@plugin("operation_event_queue_length")
def operation_event_queue_length(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_1128: operations sharing a runnable have identical server queue length."""
    report = PluginReport(checked=len(selected))
    operations_by_runnable: dict[int, tuple[etree._Element, set[int]]] = {}
    for event in index.elements("OPERATION-INVOKED-EVENT"):
        runnable = _resolve(index, _first(event, {"START-ON-EVENT-REF"}), report, "event runnable")
        operation = _resolve(index, _first(event, {"TARGET-PROVIDED-OPERATION-REF"}), report, "provided operation")
        if runnable is None or operation is None:
            continue
        entry = operations_by_runnable.setdefault(id(runnable), (runnable, set()))
        entry[1].add(id(operation))
    for runnable, operation_ids in operations_by_runnable.values():
        if len(operation_ids) < 2:
            continue
        component = index.nearest(runnable, COMPONENT_TAGS)
        if component is None:
            report.incomplete(f"RunnableEntity has no component owner at {index.location(runnable)}")
            continue
        queue_values: list[tuple[tuple | None, etree._Element, etree._Element]] = []
        for port in _owned(index, component, "P-PORT-PROTOTYPE", COMPONENT_TAGS):
            for comspec in index.descendants(port, {"SERVER-COM-SPEC"}):
                operation = _resolve(index, _first(comspec, {"OPERATION-REF"}), report, "ServerComSpec operation")
                if operation is not None and id(operation) in operation_ids:
                    queue_values.append((_value_key(_direct(comspec, "QUEUE-LENGTH")), comspec, operation))
        if len(queue_values) < len(operation_ids):
            report.incomplete(f"not every operation of {index.path_of(runnable)} has a resolved ServerComSpec")
            continue
        expected = queue_values[0][0]
        for value, comspec, operation in queue_values[1:]:
            if value != expected:
                report.fail(
                    index, comspec,
                    "ServerComSpecs for operations handled by one RunnableEntity use different queueLength values",
                    runnable=index.path_of(runnable), operation=index.path_of(operation),
                    expected=expected, actual=value,
                    repair=_repair("align_value", "QUEUE-LENGTH", "Use one queueLength for all operations handled by this runnable."),
                )
    return report


@plugin("texttable_compu_structure")
def texttable_compu_structure(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_1134: TEXTTABLE has internal-to-physical bounded scales and no physConstr."""
    report = PluginReport(checked=len(selected))
    for method in selected:
        if _text(_direct(method, "CATEGORY")) != "TEXTTABLE":
            continue
        phys = _first(method, {"PHYS-CONSTRS"})
        if phys is not None:
            report.fail(index, phys, "TEXTTABLE CompuMethod must not define physConstrs",
                        repair=_repair("remove", "PHYS-CONSTRS", "Remove physConstrs from the TEXTTABLE definition."))
        direction = _direct(method, "COMPU-INTERNAL-TO-PHYS")
        if direction is None:
            report.fail(index, method, "TEXTTABLE CompuMethod requires compuInternalToPhys",
                        repair=_repair("add_element", "COMPU-INTERNAL-TO-PHYS", "Define bounded CompuScales."))
            continue
        scales = [item for item in direction.iterdescendants() if local_name(item.tag) == "COMPU-SCALE"]
        if not scales:
            report.fail(index, direction, "TEXTTABLE compuInternalToPhys requires at least one CompuScale",
                        repair=_repair("add_element", "COMPU-SCALE", "Add a bounded text-table scale."))
        for scale in scales:
            if _first(scale, {"LOWER-LIMIT"}) is None or _first(scale, {"UPPER-LIMIT"}) is None:
                report.fail(index, scale, "TEXTTABLE CompuScale requires lowerLimit and upperLimit",
                            repair=_repair("add_element", "LOWER-LIMIT/UPPER-LIMIT", "Define both limits for this scale."))
    return report


@plugin("application_array_element_category")
def application_array_element_category(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_1152: array-element category equals referenced type category."""
    report = PluginReport(checked=len(selected))
    for element in selected:
        own_category = _direct(element, "CATEGORY")
        data_type = _type_of(index, element, report)
        if data_type is None:
            continue
        target_category = _direct(data_type, "CATEGORY")
        if own_category is None or target_category is None:
            report.incomplete(f"missing category for {index.path_of(element)} or its type")
        elif _text(own_category) != _text(target_category):
            report.fail(index, own_category, "ApplicationArrayElement category differs from its AutosarDataType",
                        actual=_text(own_category), expected=_text(target_category), type=index.path_of(data_type),
                        repair=_repair("replace_value", "CATEGORY", "Copy the category of the referenced AutosarDataType.", expected=_text(target_category)))
    return report


@plugin("interface_mapping_side_scope")
def interface_mapping_side_scope(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_1159/1237/1238: each mapping side belongs to one distinct interface."""
    report = PluginReport(checked=len(selected))
    cid = rule["constraint_id"]
    if cid == "constr_1159":
        roots = selected
        mapping_tag = "DATA-PROTOTYPE-MAPPING"
        pairs = (("FIRST-DATA-PROTOTYPE-REF", "first"), ("SECOND-DATA-PROTOTYPE-REF", "second"))
        owner_tag = {"SENDER-RECEIVER-INTERFACE", "NV-DATA-INTERFACE", "PARAMETER-INTERFACE"}
    elif cid == "constr_1237":
        roots = list({index.nearest(item, {"CLIENT-SERVER-INTERFACE-MAPPING"}) or item for item in selected})
        mapping_tag = "CLIENT-SERVER-OPERATION-MAPPING"
        pairs = (("FIRST-OPERATION-REF", "first"), ("SECOND-OPERATION-REF", "second"))
        owner_tag = {"CLIENT-SERVER-INTERFACE"}
    else:
        roots = list({index.nearest(item, {"CLIENT-SERVER-INTERFACE-MAPPING"}) or item for item in selected})
        mapping_tag = "CLIENT-SERVER-APPLICATION-ERROR-MAPPING"
        pairs = (("FIRST-APPLICATION-ERROR-REF", "first"), ("SECOND-APPLICATION-ERROR-REF", "second"))
        owner_tag = {"CLIENT-SERVER-INTERFACE"}
    for root in roots:
        owners: dict[str, set[etree._Element]] = {"first": set(), "second": set()}
        mappings = [root] if local_name(root.tag) == mapping_tag else index.descendants(root, {mapping_tag})
        for mapping in mappings:
            for ref_tag, side in pairs:
                for ref in index.descendants(mapping, {ref_tag}):
                    target = _resolve(index, ref, report, f"{side} mapped element")
                    owner = index.nearest(target, owner_tag) if target is not None else None
                    if target is not None and owner is None:
                        report.incomplete(f"mapped {side} target has no PortInterface owner at {index.location(target)}")
                    elif owner is not None:
                        owners[side].add(owner)
        invalid = any(len(values) != 1 for values in owners.values()) or owners["first"] == owners["second"]
        if mappings and invalid:
            report.fail(index, root, "Mapping sides do not each belong to one distinct PortInterface",
                        first_interfaces=[index.path_of(item) for item in owners["first"]],
                        second_interfaces=[index.path_of(item) for item in owners["second"]],
                        repair=_repair("repair_reference", "FIRST/SECOND references", "Keep each side within one interface and use different interfaces for the two sides."))
    return report


@plugin("e2e_identical_sender")
def e2e_identical_sender(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_1183: all protected variable groups use the same sender IREF."""
    report = PluginReport(checked=len(selected))
    for protection in selected:
        entries = _owned(index, protection, "END-TO-END-PROTECTION-VARIABLE-PROTOTYPE", {"END-TO-END-PROTECTION"})
        sender_keys: list[tuple[str, ...]] = []
        sender_nodes: list[etree._Element] = []
        for entry in entries:
            sender = _direct(entry, "SENDER-IREF")
            refs = tuple(normalized_ref(_text(item)) for item in sender.iterdescendants()
                         if local_name(item.tag).endswith("REF") and _text(item)) if sender is not None else ()
            if not refs:
                report.incomplete(f"missing sender IREF at {index.location(entry)}")
                continue
            sender_keys.append(refs)
            sender_nodes.append(sender)
        if sender_keys and any(key != sender_keys[0] for key in sender_keys[1:]):
            report.fail(index, sender_nodes[1], "EndToEndProtectionVariablePrototypes do not reference the identical sender",
                        senders=sender_keys,
                        repair=_repair("repair_reference", "SENDER-IREF", "Use the same sender instance reference in every entry."))
    return report


def _direct_type_children(index: ArxmlIndex, data_type: etree._Element) -> list[etree._Element]:
    tag = local_name(data_type.tag)
    if tag == "APPLICATION-ARRAY-DATA-TYPE":
        return _owned(index, data_type, "APPLICATION-ARRAY-ELEMENT", {"APPLICATION-ARRAY-DATA-TYPE"})
    if tag == "APPLICATION-RECORD-DATA-TYPE":
        return _owned(index, data_type, "APPLICATION-RECORD-ELEMENT", {"APPLICATION-RECORD-DATA-TYPE"})
    if tag == "IMPLEMENTATION-DATA-TYPE":
        return _owned(index, data_type, "IMPLEMENTATION-DATA-TYPE-ELEMENT", {"IMPLEMENTATION-DATA-TYPE", "IMPLEMENTATION-DATA-TYPE-ELEMENT"})
    return []


def _reachable_type_nodes(index: ArxmlIndex, root_type: etree._Element, report: PluginReport) -> set[int]:
    result: set[int] = set()
    seen_types: set[int] = set()
    stack = [root_type]
    while stack:
        data_type = stack.pop()
        if id(data_type) in seen_types:
            continue
        seen_types.add(id(data_type))
        for child in _direct_type_children(index, data_type):
            result.add(id(child))
            child_type = _type_of(index, child, report)
            if child_type is not None:
                stack.append(child_type)
    return result


@plugin("instance_ref_type_enclosure")
def instance_ref_type_enclosure(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_1185/1186: context and target nodes are enclosed by the root type."""
    report = PluginReport(checked=len(selected))
    for iref in selected:
        root_tags = {"ROOT-DATA-PROTOTYPE-REF"} if rule["constraint_id"] == "constr_1185" else {"ROOT-VARIABLE-DATA-PROTOTYPE-REF"}
        root = _resolve(index, _first(iref, root_tags), report, "instance-ref root prototype")
        if root is None:
            continue
        root_type = _type_of(index, root, report)
        if root_type is None:
            continue
        reachable = _reachable_type_nodes(index, root_type, report)
        refs = index.descendants(iref, {"CONTEXT-DATA-PROTOTYPE-REF", "TARGET-DATA-PROTOTYPE-REF"})
        if not any(local_name(item.tag) == "TARGET-DATA-PROTOTYPE-REF" for item in refs):
            report.incomplete(f"instance reference has no target at {index.location(iref)}")
        for ref in refs:
            target = _resolve(index, ref, report, "instance-ref context/target")
            if target is not None and id(target) not in reachable:
                report.fail(index, ref, "Instance-reference node is outside the type graph of rootDataPrototype",
                            root_type=index.path_of(root_type), target=index.path_of(target),
                            repair=_repair("repair_reference", local_name(ref.tag), "Reference an element enclosed by the root prototype's data type."))
    return report


@plugin("mode_mapping_scope")
def mode_mapping_scope(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_1246/1247: mapping sides match exactly one declared mode group."""
    report = PluginReport(checked=len(selected))
    if rule["constraint_id"] == "constr_1246":
        sets = selected
        declared: dict[int, tuple[etree._Element | None, etree._Element | None]] = {}
    else:
        sets = []
        declared = {}
        for prototype_mapping in selected:
            mapping_set = _resolve(index, _first(prototype_mapping, {"MODE-DECLARATION-MAPPING-SET-REF"}), report, "ModeDeclarationMappingSet")
            first_proto = _resolve(index, _first(prototype_mapping, {"FIRST-MODE-GROUP-REF"}), report, "first ModeDeclarationGroupPrototype")
            second_proto = _resolve(index, _first(prototype_mapping, {"SECOND-MODE-GROUP-REF"}), report, "second ModeDeclarationGroupPrototype")
            if mapping_set is None or first_proto is None or second_proto is None:
                continue
            first_group = _resolve(index, _first(first_proto, {"TYPE-TREF", "MODE-DECLARATION-GROUP-REF"}), report, "first mode-group type")
            second_group = _resolve(index, _first(second_proto, {"TYPE-TREF", "MODE-DECLARATION-GROUP-REF"}), report, "second mode-group type")
            sets.append(mapping_set)
            declared[id(mapping_set)] = (first_group, second_group)
    for mapping_set in sets:
        owners: dict[str, set[etree._Element]] = {"first": set(), "second": set()}
        for mapping in index.descendants(mapping_set, {"MODE-DECLARATION-MAPPING"}):
            for tag, side in (("FIRST-MODE-REF", "first"), ("SECOND-MODE-REF", "second")):
                for ref in index.descendants(mapping, {tag}):
                    mode = _resolve(index, ref, report, f"{side} ModeDeclaration")
                    group = index.nearest(mode, {"MODE-DECLARATION-GROUP"}) if mode is not None else None
                    if mode is not None and group is None:
                        report.incomplete(f"ModeDeclaration has no group owner at {index.location(mode)}")
                    elif group is not None:
                        owners[side].add(group)
        invalid = any(len(values) != 1 for values in owners.values()) or owners["first"] == owners["second"]
        expected = declared.get(id(mapping_set))
        if expected is not None:
            invalid = invalid or owners["first"] != ({expected[0]} if expected[0] is not None else set()) or owners["second"] != ({expected[1]} if expected[1] is not None else set())
        if invalid:
            report.fail(index, mapping_set, "Mode mapping sides do not match one distinct ModeDeclarationGroup each",
                        first_groups=[index.path_of(item) for item in owners["first"]],
                        second_groups=[index.path_of(item) for item in owners["second"]],
                        repair=_repair("repair_reference", "FIRST/SECOND-MODE-REF", "Keep each side in its single declared ModeDeclarationGroup."))
    return report


@plugin("boolean_string_unit_dimensionless")
def boolean_string_unit_dimensionless(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_1255: BOOLEAN/STRING units have a zero physical dimension."""
    report = PluginReport(checked=len(selected))
    exponent_tags = {"LENGTH-EXP", "MASS-EXP", "TIME-EXP", "CURRENT-EXP", "TEMPERATURE-EXP", "MOLAR-AMOUNT-EXP", "LUMINOUS-INTENSITY-EXP"}
    for data_type in selected:
        if _text(_direct(data_type, "CATEGORY")) not in {"BOOLEAN", "STRING"}:
            continue
        for ref in index.descendants(data_type, {"UNIT-REF"}):
            unit = _resolve(index, ref, report, "BOOLEAN/STRING Unit")
            dim_ref = _first(unit, {"PHYSICAL-DIMENSION-REF"}) if unit is not None else None
            if unit is None:
                continue
            if dim_ref is None:
                continue
            dimension = _resolve(index, dim_ref, report, "Unit physical dimension")
            if dimension is None:
                continue
            nonzero = [item for item in index.descendants(dimension, exponent_tags) if _text(item) not in {"", "0", "0.0"}]
            if nonzero:
                report.fail(index, ref, "BOOLEAN/STRING ApplicationPrimitiveDataType uses a dimensional Unit",
                            physical_dimension=index.path_of(dimension), nonzero_exponents={local_name(item.tag): _text(item) for item in nonzero},
                            repair=_repair("repair_reference", "UNIT-REF", "Use a meaningless Unit whose PhysicalDimension exponents are all zero."))
    return report


@plugin("mapped_argument_direction")
def mapped_argument_direction(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_1268: mapped operation arguments preserve direction."""
    report = PluginReport(checked=len(selected))
    for operation_mapping in selected:
        for mapping in index.descendants(operation_mapping, {"DATA-PROTOTYPE-MAPPING"}):
            first = _resolve(index, _first(mapping, {"FIRST-DATA-PROTOTYPE-REF"}), report, "first mapped argument")
            second = _resolve(index, _first(mapping, {"SECOND-DATA-PROTOTYPE-REF"}), report, "second mapped argument")
            if first is None or second is None:
                continue
            first_direction = _text(_direct(first, "DIRECTION"))
            second_direction = _text(_direct(second, "DIRECTION"))
            if not first_direction or not second_direction:
                report.incomplete(f"mapped argument direction is missing at {index.location(mapping)}")
            elif first_direction != second_direction:
                report.fail(index, mapping, "Mapped ArgumentDataPrototypes have different directions",
                            first=first_direction, second=second_direction,
                            repair=_repair("replace_value", "DIRECTION", "Use the same direction on both mapped arguments."))
    return report


@plugin("receive_by_value_nonqueued")
def receive_by_value_nonqueued(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_1277: dataReceivePointByValue may not target queued data."""
    report = PluginReport(checked=len(selected))
    for access in selected:
        if index.nearest(access, {"DATA-RECEIVE-POINT-BY-VALUES"}) is None:
            continue
        target = _resolve(index, _first(access, {"TARGET-DATA-PROTOTYPE-REF"}), report, "receive-by-value target")
        if target is None:
            continue
        policy = _text(_first(target, {"SW-IMPL-POLICY"})) or "STANDARD"
        if policy == "QUEUED":
            report.fail(index, access, "dataReceivePointByValue targets a QUEUED VariableDataPrototype",
                        target=index.path_of(target),
                        repair=_repair("repair_reference", "TARGET-DATA-PROTOTYPE-REF", "Reference a nonqueued data prototype."))
    return report


def _compu_category_for_prototype(index: ArxmlIndex, prototype: etree._Element, report: PluginReport) -> str | None:
    data_type = _type_of(index, prototype, report)
    if data_type is None:
        return None
    method = _resolve(index, _first(data_type, {"COMPU-METHOD-REF"}), report, "prototype CompuMethod")
    return _text(_direct(method, "CATEGORY")) if method is not None else None


@plugin("bitfield_text_mapping_not_identical")
def bitfield_text_mapping_not_identical(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_1306: mapped BITFIELD_TEXTTABLE value pairs require identicalMapping=false."""
    report = PluginReport(checked=len(selected))
    for text_mapping in selected:
        if not index.descendants(text_mapping, {"TEXT-TABLE-VALUE-PAIR"}):
            continue
        data_mapping = index.nearest(text_mapping, {"DATA-PROTOTYPE-MAPPING"})
        if data_mapping is None:
            report.incomplete(f"TextTableMapping has no DataPrototypeMapping owner at {index.location(text_mapping)}")
            continue
        first = _resolve(index, _first(data_mapping, {"FIRST-DATA-PROTOTYPE-REF"}), report, "first mapped prototype")
        second = _resolve(index, _first(data_mapping, {"SECOND-DATA-PROTOTYPE-REF"}), report, "second mapped prototype")
        if first is None or second is None:
            continue
        categories = [_compu_category_for_prototype(index, item, report) for item in (first, second)]
        identical = _direct(text_mapping, "IDENTICAL-MAPPING")
        if categories == ["BITFIELD_TEXTTABLE", "BITFIELD_TEXTTABLE"] and _truth(identical):
            report.fail(index, identical if identical is not None else text_mapping,
                        "BITFIELD_TEXTTABLE value-pair mapping must set identicalMapping=false",
                        repair=_repair("replace_value", "IDENTICAL-MAPPING", "Set identicalMapping to false.", expected="false"))
    return report


@plugin("e2e_comspec_uses_flag")
def e2e_comspec_uses_flag(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_1323: E2E transformation ComSpec props require usesE2E=false."""
    report = PluginReport(checked=len(selected))
    for comspec in selected:
        if _first(comspec, {"END-TO-END-TRANSFORMATION-COM-SPEC-PROPS"}) is None:
            continue
        flag = _direct(comspec, "USES-END-TO-END-PROTECTION")
        if flag is None:
            report.incomplete(f"usesEndToEndProtection is missing at {index.location(comspec)}")
        elif _truth(flag):
            report.fail(index, flag, "ReceiverComSpec with E2E transformation props must set usesEndToEndProtection=false",
                        repair=_repair("replace_value", "USES-END-TO-END-PROTECTION", "Set the value to false.", expected="false"))
    return report


@plugin("pim_type_definition_consistency")
def pim_type_definition_consistency(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_2007: same PIM C type in one behavior has one typedef text."""
    report = PluginReport(checked=len(selected))
    for behavior in selected:
        first_by_type: dict[str, tuple[str, etree._Element]] = {}
        for memory in _owned(index, behavior, "PER-INSTANCE-MEMORY", {"SWC-INTERNAL-BEHAVIOR"}):
            c_type = _text(_direct(memory, "TYPE"))
            definition = _text(_direct(memory, "TYPE-DEFINITION"))
            if not c_type or not definition:
                report.incomplete(f"PerInstanceMemory TYPE/TYPE-DEFINITION is missing at {index.location(memory)}")
                continue
            prior = first_by_type.get(c_type)
            if prior is None:
                first_by_type[c_type] = (definition, memory)
            elif prior[0] != definition:
                report.fail(index, memory, "PerInstanceMemorys with identical TYPE have different TYPE-DEFINITION text",
                            c_type=c_type, first_definition=prior[0], actual_definition=definition,
                            first=index.location(prior[1]),
                            repair=_repair("replace_value", "TYPE-DEFINITION", "Use the same typedef text for this TYPE."))
    return report


@plugin("event_request_timeout_consistency")
def event_request_timeout_consistency(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_2033/4012: WaitPoint timeout equals the request that raises its event."""
    report = PluginReport(checked=len(selected))
    expected_event = "DATA-SEND-COMPLETED-EVENT" if rule["constraint_id"] == "constr_2033" else "MODE-SWITCHED-ACK-EVENT"
    request_tag = "TRANSMISSION-ACKNOWLEDGE" if rule["constraint_id"] == "constr_2033" else "MODE-SWITCHED-ACK"
    for wait in selected:
        event = _resolve(index, _direct(wait, "TRIGGER-REF"), report, "WaitPoint trigger event")
        if event is None or local_name(event.tag) != expected_event:
            continue
        source = _resolve(index, _direct(event, "EVENT-SOURCE-REF"), report, "event source")
        request = _first(source, {request_tag}) if source is not None else None
        if source is not None and request is None:
            report.incomplete(f"event source has no {request_tag} at {index.location(source)}")
            continue
        wait_timeout = _direct(wait, "TIMEOUT")
        request_timeout = _direct(request, "TIMEOUT") if request is not None else None
        if wait_timeout is None or request_timeout is None:
            report.incomplete(f"timeout pair is incomplete at {index.location(wait)}")
        elif _value_key(wait_timeout) != _value_key(request_timeout):
            report.fail(index, wait_timeout, "WaitPoint timeout differs from the corresponding acknowledgement request timeout",
                        wait_timeout=_value_key(wait_timeout), request_timeout=_value_key(request_timeout),
                        request=index.location(request),
                        repair=_repair("replace_value", "TIMEOUT", "Use the timeout of the corresponding acknowledgement request."))
    return report


def _mode_group_of_port(index: ArxmlIndex, port: etree._Element, report: PluginReport) -> etree._Element | None:
    interface = _resolve(index, _first(port, INTERFACE_REF_TAGS), report, "mode port interface")
    if interface is None or local_name(interface.tag) != "MODE-SWITCH-INTERFACE":
        return None
    prototype = _first(interface, {"MODE-GROUP"})
    return _resolve(index, _first(prototype, {"TYPE-TREF", "MODE-DECLARATION-GROUP-REF"}) if prototype is not None else None, report, "ModeDeclarationGroupPrototype type")


@plugin("component_mode_group_name_consistency")
def component_mode_group_name_consistency(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_2049: same group shortName in a component means identical modes."""
    report = PluginReport(checked=len(selected))
    for component in selected:
        by_name: dict[str, tuple[tuple[str, ...], etree._Element]] = {}
        ports = sum((_owned(index, component, tag, COMPONENT_TAGS) for tag in PORT_TAGS), [])
        for port in ports:
            group = _mode_group_of_port(index, port, report)
            if group is None:
                continue
            name = _text(_direct(group, "SHORT-NAME"))
            modes = tuple(sorted(_text(_direct(item, "SHORT-NAME")) for item in _owned(index, group, "MODE-DECLARATION", {"MODE-DECLARATION-GROUP"})))
            prior = by_name.get(name)
            if prior is None:
                by_name[name] = (modes, group)
            elif prior[0] != modes:
                report.fail(index, port, "Mode ports use same-named ModeDeclarationGroups with different declarations",
                            group_name=name, first_modes=prior[0], actual_modes=modes,
                            first_group=index.path_of(prior[1]), actual_group=index.path_of(group),
                            repair=_repair("rename_or_align", "MODE-DECLARATION-GROUP", "Use different shortNames or make the mode declarations identical."))
    return report


@plugin("mode_switch_event_mode_cardinality")
def mode_switch_event_mode_cardinality(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_4003: transition activation has two ordered modes; others one."""
    report = PluginReport(checked=len(selected))
    for event in selected:
        activation = _text(_direct(event, "ACTIVATION")).upper().replace("-", "_")
        modes: list[etree._Element] = []
        for ref in event.iterdescendants():
            if local_name(ref.tag) not in {"TARGET-MODE-DECLARATION-REF", "MODE-DECLARATION-REF"}:
                continue
            mode = _resolve(index, ref, report, "SwcModeSwitchEvent ModeDeclaration")
            if mode is not None and all(mode is not item for item in modes):
                modes.append(mode)
        expected = 2 if activation in {"ON_TRANSITION", "ONTRANSITION"} else 1
        groups = {index.nearest(mode, {"MODE-DECLARATION-GROUP"}) for mode in modes}
        valid = len(modes) == expected and (expected == 1 or (len(groups) == 1 and len({id(item) for item in modes}) == 2))
        if not valid:
            report.fail(index, event, "SwcModeSwitchEvent mode cardinality/group is inconsistent with activation",
                        activation=activation, expected_count=expected, actual_count=len(modes),
                        groups=[index.path_of(item) for item in groups if item is not None],
                        repair=_repair("repair_reference_cardinality", "MODE-IREF", "Use two distinct modes from one group for onTransition, otherwise exactly one mode."))
    return report
