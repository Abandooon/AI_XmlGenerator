"""Conditional, range and completeness validators with closed ARXML evidence."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal, InvalidOperation

from lxml import etree

from .arxml_index import ArxmlIndex, local_name
from .plugins import CONNECTOR_TAGS, INTERFACE_REF_TAGS, PORT_TAGS, PluginReport, plugin

DATA_PROTOTYPE_TAGS = {
    "VARIABLE-DATA-PROTOTYPE", "PARAMETER-DATA-PROTOTYPE", "ARGUMENT-DATA-PROTOTYPE",
    "APPLICATION-ARRAY-ELEMENT", "APPLICATION-RECORD-ELEMENT", "IMPLEMENTATION-DATA-TYPE-ELEMENT",
}
COMSPEC_TAGS = {"NONQUEUED-RECEIVER-COM-SPEC", "QUEUED-RECEIVER-COM-SPEC"}


def _text(element: etree._Element | None) -> str:
    return (element.text or "").strip() if element is not None else ""


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


def _type_of(index: ArxmlIndex, prototype: etree._Element, report: PluginReport) -> etree._Element | None:
    ref = _first(prototype, {"TYPE-TREF"})
    if ref is None and local_name(prototype.tag) == "IMPLEMENTATION-DATA-TYPE-ELEMENT":
        ref = _first(prototype, {"IMPLEMENTATION-DATA-TYPE-REF"})
    return _resolve(index, ref, report, f"{local_name(prototype.tag)} type")


def _final_impl(index: ArxmlIndex, data_type: etree._Element, report: PluginReport) -> etree._Element | None:
    current = data_type
    seen: set[int] = set()
    while local_name(current.tag) == "IMPLEMENTATION-DATA-TYPE" and _text(_direct(current, "CATEGORY")) == "TYPE_REFERENCE":
        if id(current) in seen:
            report.incomplete(f"TYPE_REFERENCE cycle at {index.location(current)}")
            return None
        seen.add(id(current))
        current = _resolve(index, _first(current, {"IMPLEMENTATION-DATA-TYPE-REF"}), report, "TYPE_REFERENCE target")
        if current is None:
            return None
    return current


def _numeric(element: etree._Element | None, report: PluginReport, index: ArxmlIndex, label: str) -> Decimal | None:
    if element is None:
        return None
    candidates = [_text(element)] if _text(element) else [
        _text(item) for item in element.iterdescendants()
        if local_name(item.tag) in {"VALUE", "V", "VT"} and _text(item)
    ]
    candidates = list(dict.fromkeys(candidates))
    if len(candidates) != 1:
        report.incomplete(f"{label} is variant or unbound at {index.location(element)}")
        return None
    try:
        return Decimal(candidates[0])
    except InvalidOperation:
        report.incomplete(f"{label} is non-numeric at {index.location(element)}")
        return None


def _port_interface(index: ArxmlIndex, port: etree._Element, report: PluginReport) -> etree._Element | None:
    return _resolve(index, _first(port, INTERFACE_REF_TAGS), report, "PortPrototype interface")


def _comspec_target(index: ArxmlIndex, comspec: etree._Element, report: PluginReport) -> etree._Element | None:
    return _resolve(index, _first(comspec, {"DATA-ELEMENT-REF", "PARAMETER-REF"}), report, "ReceiverComSpec element")


@plugin("unconnected_rport_init_values")
def unconnected_rport_init_values(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_1100: each data-interface element of an unconnected R port has an initValue."""
    report = PluginReport(checked=len(selected))
    connected: set[str] = set()
    for connector_tag in CONNECTOR_TAGS:
        for connector in index.elements(connector_tag):
            for ref in connector.iterdescendants():
                if "PORT" not in local_name(ref.tag) or not local_name(ref.tag).endswith(("-REF", "-TREF")):
                    continue
                port = _resolve(index, ref, report, "connector port")
                if port is not None and local_name(port.tag) in PORT_TAGS:
                    connected.add(index.path_of(port))
    for port in selected:
        if index.path_of(port) in connected:
            continue
        interface = _port_interface(index, port, report)
        if interface is None or local_name(interface.tag) not in {"SENDER-RECEIVER-INTERFACE", "NV-DATA-INTERFACE", "PARAMETER-INTERFACE"}:
            continue
        elements = [item for item in interface.iterdescendants() if local_name(item.tag) in {"VARIABLE-DATA-PROTOTYPE", "PARAMETER-DATA-PROTOTYPE"}]
        comspecs = [item for item in port.iterdescendants() if local_name(item.tag) in COMSPEC_TAGS | {"PARAMETER-REQUIRE-COM-SPEC"}]
        by_target: dict[str, list[etree._Element]] = defaultdict(list)
        for comspec in comspecs:
            target = _comspec_target(index, comspec, report)
            if target is not None:
                by_target[index.path_of(target)].append(comspec)
        for element in elements:
            candidates = by_target.get(index.path_of(element), [])
            if not candidates or not any(_first(item, {"INIT-VALUE"}) is not None for item in candidates):
                report.fail(index, port, "Unconnected data RPortPrototype element has no requiredComSpec initValue",
                            data_element=index.path_of(element),
                            repair=_repair("add_element", "INIT-VALUE", "Add a requiredComSpec with an initValue for this interface element."))
    return report


def _e2e_profile_contexts(index: ArxmlIndex, protection: etree._Element, report: PluginReport):
    profile = _direct(protection, "END-TO-END-PROFILE")
    if profile is None:
        report.incomplete(f"EndToEndProtection has no profile at {index.location(protection)}")
        return None, "", set()
    category = _text(_direct(profile, "CATEGORY"))
    if not category:
        report.incomplete(f"EndToEndDescription category is missing at {index.location(profile)}")
    receivers: set[int] = set()
    for entry in _owned(index, protection, "END-TO-END-PROTECTION-VARIABLE-PROTOTYPE", {"END-TO-END-PROTECTION"}):
        wrapper = _direct(entry, "RECEIVER-IREFS")
        if wrapper is None:
            continue
        for ref in wrapper.iterdescendants():
            if local_name(ref.tag) not in {"TARGET-DATA-PROTOTYPE-REF", "TARGET-DATA-ELEMENT-REF"}:
                continue
            target = _resolve(index, ref, report, "E2E receiver data element")
            if target is not None:
                receivers.add(id(target))
    matching: set[int] = set()
    for tag in COMSPEC_TAGS:
        for comspec in index.elements(tag):
            target = _comspec_target(index, comspec, report)
            if target is not None and id(target) in receivers:
                matching.add(id(comspec))
    return profile, category, matching


E2E_DEFAULT_RULES = {
    "constr_1170": ("PROFILE_01", "MAX-DELTA-COUNTER-INIT"),
    "constr_1171": ("PROFILE_02", "MAX-DELTA-COUNTER-INIT"),
    "constr_1215": ("PROFILE_01", "MAX-NO-NEW-OR-REPEATED-DATA"),
    "constr_1216": ("PROFILE_01", "SYNC-COUNTER-INIT"),
    "constr_1217": ("PROFILE_02", "MAX-NO-NEW-OR-REPEATED-DATA"),
    "constr_1218": ("PROFILE_02", "SYNC-COUNTER-INIT"),
}


@plugin("e2e_profile_default_required")
def e2e_profile_default_required(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_1170/1171/1215..1218: profile fallback exists without a receiver override."""
    report = PluginReport(checked=len(selected))
    expected_profile, field = E2E_DEFAULT_RULES[rule["constraint_id"]]
    for protection in selected:
        profile, category, matching = _e2e_profile_contexts(index, protection, report)
        if profile is None or category != expected_profile:
            continue
        override = any(_direct(item, field) is not None for tag in COMSPEC_TAGS for item in index.elements(tag) if id(item) in matching)
        if not override and _direct(profile, field) is None:
            report.fail(index, profile, f"{expected_profile} EndToEndDescription requires fallback {field}",
                        repair=_repair("add_element", field, "Define the profile fallback because no matching ReceiverComSpec override exists."))
    return report


E2E_RANGE_RULES = {
    "constr_1117": ("PROFILE_01", "MAX-DELTA-COUNTER-INIT", 14),
    "constr_1121": ("PROFILE_02", "MAX-DELTA-COUNTER-INIT", 15),
    "constr_1211": ("PROFILE_01", "MAX-NO-NEW-OR-REPEATED-DATA", 14),
    "constr_1212": ("PROFILE_01", "SYNC-COUNTER-INIT", 14),
    "constr_1213": ("PROFILE_02", "MAX-NO-NEW-OR-REPEATED-DATA", 15),
    "constr_1214": ("PROFILE_02", "SYNC-COUNTER-INIT", 15),
}


@plugin("e2e_profile_value_range")
def e2e_profile_value_range(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """Profile-specific inclusive ranges for E2E description and receiver overrides."""
    report = PluginReport(checked=len(selected))
    expected_profile, field, maximum = E2E_RANGE_RULES[rule["constraint_id"]]
    for protection in selected:
        profile, category, matching = _e2e_profile_contexts(index, protection, report)
        if profile is None or category != expected_profile:
            continue
        subjects = [profile] + [item for tag in COMSPEC_TAGS for item in index.elements(tag) if id(item) in matching]
        for subject in subjects:
            value_element = _direct(subject, field)
            if value_element is None:
                continue
            value = _numeric(value_element, report, index, field)
            if value is not None and (value != value.to_integral_value() or value < 0 or value > maximum):
                report.fail(index, value_element, f"{field} is outside the {expected_profile} range",
                            actual=str(value), minimum=0, maximum=maximum,
                            repair=_repair("replace_value", field, f"Use an integer from 0 through {maximum}."))
    return report


@plugin("receiver_replace_with_iff")
def receiver_replace_with_iff(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_1188: replaceWith iff either replacement policy is externalReplacement."""
    report = PluginReport(checked=len(selected))
    for comspec in selected:
        target = _comspec_target(index, comspec, report)
        if target is None:
            continue
        own_external = _text(_direct(comspec, "HANDLE-OUT-OF-RANGE")).upper().replace("-", "_") == "EXTERNAL_REPLACEMENT"
        interface = index.nearest(target, {"SENDER-RECEIVER-INTERFACE"})
        policy_external = False
        if interface is not None:
            for policy in index.descendants(interface, {"INVALIDATION-POLICY"}):
                policy_target = _resolve(index, _first(policy, {"DATA-ELEMENT-REF"}), report, "invalidation policy data element")
                if policy_target is target and _text(_direct(policy, "HANDLE-INVALID")).upper().replace("-", "_") == "EXTERNAL_REPLACEMENT":
                    policy_external = True
        required = own_external or policy_external
        replace = _direct(comspec, "REPLACE-WITH")
        if (replace is not None) != required:
            report.fail(index, replace if replace is not None else comspec, "ReceiverComSpec.replaceWith existence does not match externalReplacement policy",
                        expected_present=required, actual_present=replace is not None,
                        repair=_repair("add_or_remove", "REPLACE-WITH", "Define replaceWith exactly when an applicable policy is externalReplacement."))
    return report


def _event_modes(index: ArxmlIndex, event: etree._Element, report: PluginReport) -> list[etree._Element]:
    result: list[etree._Element] = []
    for ref in event.iterdescendants():
        if local_name(ref.tag) not in {"TARGET-MODE-DECLARATION-REF", "MODE-DECLARATION-REF"}:
            continue
        mode = _resolve(index, ref, report, "event ModeDeclaration")
        if mode is not None and all(mode is not item for item in result):
            result.append(mode)
    return result


@plugin("mode_switch_transition_exists")
def mode_switch_transition_exists(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_1195: transition event direction is declared when the group uses transitions."""
    report = PluginReport(checked=len(selected))
    for event in selected:
        activation = _text(_direct(event, "ACTIVATION")).upper().replace("-", "_")
        if activation not in {"ON_TRANSITION", "ONTRANSITION"}:
            continue
        modes = _event_modes(index, event, report)
        if len(modes) != 2:
            report.incomplete(f"transition event does not resolve exactly two ordered modes at {index.location(event)}")
            continue
        group = index.nearest(modes[0], {"MODE-DECLARATION-GROUP"})
        if group is None or index.nearest(modes[1], {"MODE-DECLARATION-GROUP"}) is not group:
            report.incomplete(f"transition event modes do not establish one group at {index.location(event)}")
            continue
        transitions = _owned(index, group, "MODE-TRANSITION", {"MODE-DECLARATION-GROUP"})
        if not transitions:
            continue
        found = False
        for transition in transitions:
            exited = _resolve(index, _first(transition, {"EXITED-MODE-REF"}), report, "ModeTransition exitedMode")
            entered = _resolve(index, _first(transition, {"ENTERED-MODE-REF"}), report, "ModeTransition enteredMode")
            if exited is modes[0] and entered is modes[1]:
                found = True
        if not found:
            report.fail(index, event, "SwcModeSwitchEvent direction has no corresponding ModeTransition",
                        exited=index.path_of(modes[0]), entered=index.path_of(modes[1]),
                        repair=_repair("add_element", "MODE-TRANSITION", "Add a transition from the exited mode to the entered mode."))
    return report


def _prototype_compu_category(index: ArxmlIndex, prototype: etree._Element, report: PluginReport) -> str | None:
    data_type = _type_of(index, prototype, report)
    if data_type is None:
        return None
    method = _resolve(index, _first(data_type, {"COMPU-METHOD-REF"}), report, "prototype CompuMethod")
    if method is None:
        return None
    category = _text(_direct(method, "CATEGORY"))
    if not category:
        report.incomplete(f"CompuMethod category is missing at {index.location(method)}")
        return None
    return category


def _mapping_prototypes(index: ArxmlIndex, mapping: etree._Element, report: PluginReport):
    return (
        _resolve(index, _first(mapping, {"FIRST-DATA-PROTOTYPE-REF"}), report, "first mapped prototype"),
        _resolve(index, _first(mapping, {"SECOND-DATA-PROTOTYPE-REF"}), report, "second mapped prototype"),
    )


@plugin("text_table_mapping_categories")
def text_table_mapping_categories(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_1303: TextTableMapping is limited to six category pairs."""
    report = PluginReport(checked=len(selected))
    allowed = {
        ("TEXTTABLE", "TEXTTABLE"), ("SCALE_LINEAR_AND_TEXTTABLE", "TEXTTABLE"),
        ("TEXTTABLE", "SCALE_LINEAR_AND_TEXTTABLE"), ("BITFIELD_TEXTTABLE", "TEXTTABLE"),
        ("TEXTTABLE", "BITFIELD_TEXTTABLE"), ("BITFIELD_TEXTTABLE", "BITFIELD_TEXTTABLE"),
    }
    for mapping in selected:
        if not index.descendants(mapping, {"TEXT-TABLE-MAPPING"}):
            continue
        first, second = _mapping_prototypes(index, mapping, report)
        if first is None or second is None:
            continue
        categories = (_prototype_compu_category(index, first, report), _prototype_compu_category(index, second, report))
        if None not in categories and categories not in allowed:
            report.fail(index, mapping, "TextTableMapping uses an unsupported pair of CompuMethod categories",
                        actual=categories, allowed=sorted(allowed),
                        repair=_repair("repair_reference", "COMPU-METHOD-REF", "Use one of the supported textual category pairs."))
    return report


@plugin("text_table_mask_condition")
def text_table_mask_condition(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_1304/1305: each side mask is present only for BITFIELD_TEXTTABLE."""
    report = PluginReport(checked=len(selected))
    side = "FIRST" if rule["constraint_id"] == "constr_1304" else "SECOND"
    for mapping in selected:
        first, second = _mapping_prototypes(index, mapping, report)
        prototype = first if side == "FIRST" else second
        if prototype is None:
            continue
        category = _prototype_compu_category(index, prototype, report)
        for text_mapping in index.descendants(mapping, {"TEXT-TABLE-MAPPING"}):
            mask = _direct(text_mapping, f"BITFIELD-TEXT-TABLE-MASK-{side}")
            if mask is not None and category != "BITFIELD_TEXTTABLE":
                report.fail(index, mask, f"bitfieldTextTableMask{side.title()} exists for a non-BITFIELD_TEXTTABLE side",
                            actual_category=category,
                            repair=_repair("remove", local_name(mask.tag), "Remove the mask or reference a BITFIELD_TEXTTABLE CompuMethod."))
    return report


def _integer(element: etree._Element | None, report: PluginReport, index: ArxmlIndex, label: str) -> int | None:
    value = _numeric(element, report, index, label)
    if value is None:
        return None
    if value != value.to_integral_value():
        report.incomplete(f"{label} is not integral at {index.location(element)}")
        return None
    return int(value)


@plugin("text_table_mask_values")
def text_table_mask_values(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_1307: each value is representable by its side's bit mask."""
    report = PluginReport(checked=len(selected))
    for text_mapping in selected:
        for side in ("FIRST", "SECOND"):
            mask_element = _direct(text_mapping, f"BITFIELD-TEXT-TABLE-MASK-{side}")
            if mask_element is None:
                continue
            mask = _integer(mask_element, report, index, f"{side} bit mask")
            if mask is None:
                continue
            for pair in index.descendants(text_mapping, {"TEXT-TABLE-VALUE-PAIR"}):
                value_element = _direct(pair, f"{side}-VALUE")
                value = _integer(value_element, report, index, f"{side} value")
                if value is not None and (value < 0 or value & ~mask):
                    report.fail(index, value_element if value_element is not None else pair,
                                "TextTableValuePair value contains bits outside its bitfield mask",
                                side=side.lower(), value=value, mask=mask,
                                repair=_repair("replace_value", f"{side}-VALUE", "Use a nonnegative value whose set bits are contained in the mask."))
    return report


@plugin("bitfield_sender_values_complete")
def bitfield_sender_values_complete(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_1313: every possible sender-side submask occurs exactly once."""
    report = PluginReport(checked=len(selected))
    for mapping in selected:
        first, second = _mapping_prototypes(index, mapping, report)
        if first is None or second is None:
            continue
        categories = {
            "FIRST": _prototype_compu_category(index, first, report),
            "SECOND": _prototype_compu_category(index, second, report),
        }
        for text_mapping in index.descendants(mapping, {"TEXT-TABLE-MAPPING"}):
            direction = _text(_direct(text_mapping, "MAPPING-DIRECTION"))
            sender_sides = {"FIRST"} if direction == "FIRST-TO-SECOND" else {"SECOND"} if direction == "SECOND-TO-FIRST" else {"FIRST", "SECOND"} if direction == "BIDIRECTIONAL" else set()
            if not sender_sides:
                report.incomplete(f"unsupported or missing mappingDirection at {index.location(text_mapping)}")
                continue
            for side in sender_sides:
                if categories[side] != "BITFIELD_TEXTTABLE":
                    continue
                mask_element = _direct(text_mapping, f"BITFIELD-TEXT-TABLE-MASK-{side}")
                mask = _integer(mask_element, report, index, f"sender {side} mask")
                if mask is None:
                    continue
                values: list[int] = []
                for pair in index.descendants(text_mapping, {"TEXT-TABLE-VALUE-PAIR"}):
                    value = _integer(_direct(pair, f"{side}-VALUE"), report, index, f"sender {side} value")
                    if value is not None:
                        values.append(value)
                expected_count = 1 << mask.bit_count()
                valid = len(values) == expected_count and len(set(values)) == expected_count and all(value >= 0 and not (value & ~mask) for value in values)
                if not valid:
                    report.fail(index, text_mapping, "BITFIELD_TEXTTABLE sender values do not cover every possible bit-mask value exactly once",
                                side=side.lower(), mask=mask, expected_count=expected_count,
                                actual_count=len(values), unique_count=len(set(values)),
                                repair=_repair("replace_collection", "TEXT-TABLE-VALUE-PAIR", "Provide each possible submask value exactly once."))
    return report


def _type_children(index: ArxmlIndex, data_type: etree._Element) -> list[etree._Element]:
    tag = local_name(data_type.tag)
    if tag == "APPLICATION-ARRAY-DATA-TYPE":
        return _owned(index, data_type, "APPLICATION-ARRAY-ELEMENT", {"APPLICATION-ARRAY-DATA-TYPE"})
    if tag == "APPLICATION-RECORD-DATA-TYPE":
        return _owned(index, data_type, "APPLICATION-RECORD-ELEMENT", {"APPLICATION-RECORD-DATA-TYPE"})
    return []


def _application_leaves(index: ArxmlIndex, root_type: etree._Element, report: PluginReport) -> set[int]:
    leaves: set[int] = set()
    seen: set[int] = set()
    stack = [root_type]
    while stack:
        data_type = stack.pop()
        if id(data_type) in seen:
            report.incomplete(f"application data type recursion at {index.location(data_type)}")
            continue
        seen.add(id(data_type))
        children = _type_children(index, data_type)
        for child in children:
            child_type = _type_of(index, child, report)
            if child_type is None:
                continue
            nested = _type_children(index, child_type)
            if nested:
                stack.append(child_type)
            else:
                leaves.add(id(child))
    return leaves


@plugin("composite_network_representation_complete")
def composite_network_representation_complete(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_1197: once used, every composite leaf has exactly one representation."""
    report = PluginReport(checked=len(selected))
    for comspec in selected:
        representations = index.descendants(comspec, {"COMPOSITE-NETWORK-REPRESENTATION"})
        if not representations:
            continue
        root = _comspec_target(index, comspec, report)
        root_type = _type_of(index, root, report) if root is not None else None
        if root_type is None:
            continue
        leaves = _application_leaves(index, root_type, report)
        counts: dict[int, int] = defaultdict(int)
        for representation in representations:
            target = _resolve(index, _first(representation, {"TARGET-DATA-PROTOTYPE-REF"}), report, "composite network leaf")
            if target is not None:
                counts[id(target)] += 1
                if id(target) not in leaves:
                    report.fail(index, representation, "compositeNetworkRepresentation targets a non-leaf or foreign element",
                                target=index.path_of(target),
                                repair=_repair("repair_reference", "LEAF-ELEMENT-IREF", "Reference a leaf of the ComSpec data element's application type."))
        for marker in leaves:
            count = counts.get(marker, 0)
            if count != 1:
                leaf = next((item for item in index.file_by_element if id(item) == marker), root_type)
                report.fail(index, comspec, "Application composite leaf does not have exactly one compositeNetworkRepresentation",
                            leaf=index.path_of(leaf), actual=count, expected=1,
                            repair=_repair("set_reference_cardinality", "COMPOSITE-NETWORK-REPRESENTATION", "Create exactly one representation for this leaf.", expected=1))
    return report


def _nv_reference_target(index: ArxmlIndex, mapping: etree._Element, report: PluginReport):
    for role in ("READ-NV-DATA", "WRITTEN-NV-DATA", "WRITTEN-READ-NV-DATA"):
        wrapper = _direct(mapping, role)
        if wrapper is None:
            continue
        port_ref = _first(wrapper, {"PORT-PROTOTYPE-REF"})
        root_ref = _first(wrapper, {"ROOT-VARIABLE-DATA-PROTOTYPE-REF", "ROOT-DATA-PROTOTYPE-REF"})
        target_ref = _first(wrapper, {"TARGET-DATA-PROTOTYPE-REF", "TARGET-IMPLEMENTATION-DATA-TYPE-ELEMENT-REF"})
        port = _resolve(index, port_ref, report, "NvBlockDataMapping port") if port_ref is not None else None
        target = _resolve(index, target_ref, report, "NvBlockDataMapping target")
        root = _resolve(index, root_ref, report, "NvBlockDataMapping root") if root_ref is not None else None
        if root is None and target is not None and local_name(target.tag) == "VARIABLE-DATA-PROTOTYPE":
            root = target
        yield port, root, target, wrapper


@plugin("nv_mapping_direct_or_subtree")
def nv_mapping_direct_or_subtree(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_1403: a direct NV mapping excludes sub-element mappings for the same port/root."""
    report = PluginReport(checked=len(selected))
    grouped: dict[tuple[int, int], list[tuple[etree._Element, etree._Element, etree._Element]]] = defaultdict(list)
    for mapping in selected:
        for port, root, target, wrapper in _nv_reference_target(index, mapping, report):
            if root is not None and target is not None:
                grouped[(id(port) if port is not None else 0, id(root))].append((mapping, root, target))
    for entries in grouped.values():
        direct = [item for item in entries if item[2] is item[1]]
        sub = [item for item in entries if item[2] is not item[1]]
        if direct and sub:
            for mapping, root, target in sub:
                report.fail(index, mapping, "Direct complete NvBlockDataMapping coexists with a sub-element mapping for the same nvData and port",
                            nv_data=index.path_of(root), sub_element=index.path_of(target),
                            repair=_repair("remove", "NV-BLOCK-DATA-MAPPING", "Remove the redundant sub-element mapping or replace the direct mapping with complete sub-element mappings."))
    return report


@plugin("vsa_mapped_implementation_shape")
def vsa_mapped_implementation_shape(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """constr_1322: application VSA profile with no implementation profile implies STRUCTURE."""
    report = PluginReport(checked=len(selected))
    for mapping in selected:
        app = _resolve(index, _first(mapping, {"APPLICATION-DATA-TYPE-REF"}), report, "mapped application type")
        impl = _resolve(index, _first(mapping, {"IMPLEMENTATION-DATA-TYPE-REF"}), report, "mapped implementation type")
        if app is None or impl is None or local_name(app.tag) != "APPLICATION-ARRAY-DATA-TYPE":
            continue
        if _direct(app, "DYNAMIC-ARRAY-SIZE-PROFILE") is None or _direct(impl, "DYNAMIC-ARRAY-SIZE-PROFILE") is not None:
            continue
        category = _text(_direct(impl, "CATEGORY"))
        if category != "STRUCTURE":
            report.fail(index, impl, "Mapped VSA implementation type without its own profile must use category STRUCTURE",
                        actual=category, expected="STRUCTURE",
                        repair=_repair("replace_value", "CATEGORY", "Use STRUCTURE and define a size indicator plus payload.", expected="STRUCTURE"))
    return report


@plugin("utf16_value_no_bom")
def utf16_value_no_bom(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    """TPS_SWCT_01653: UTF-16 string values do not start with a BOM."""
    report = PluginReport(checked=len(selected))
    for prototype in selected:
        data_type = _type_of(index, prototype, report)
        if data_type is None or local_name(data_type.tag) != "IMPLEMENTATION-DATA-TYPE":
            continue
        final = _final_impl(index, data_type, report)
        base = _resolve(index, _first(final, {"BASE-TYPE-REF"}) if final is not None else None, report, "UTF-16 SwBaseType") if final is not None else None
        if base is None or _text(_first(base, {"BASE-TYPE-ENCODING"})) != "UTF-16":
            continue
        init = _first(prototype, {"INIT-VALUE"})
        if init is None:
            continue
        tokens = [_text(item) for item in init.iterdescendants() if local_name(item.tag) in {"VALUE", "V", "VT"} and _text(item)]
        starts_bom = False
        if tokens:
            first = tokens[0]
            compact = first.strip().upper().replace("0X", "").replace(" ", "").replace("-", "")
            starts_bom = first.startswith("\ufeff") or compact.startswith(("FEFF", "FFFE"))
            if not starts_bom and len(tokens) >= 2:
                try:
                    starts_bom = (int(tokens[0], 0), int(tokens[1], 0)) in {(0xFE, 0xFF), (0xFF, 0xFE)}
                except ValueError:
                    pass
        if starts_bom:
            report.fail(index, init, "UTF-16 encoded DataPrototype value starts with a byte order mark",
                        repair=_repair("remove_prefix", "INIT-VALUE", "Remove the UTF-16 BOM from the string value."))
    return report
