"""Value, range, conditional, naming, and graph-local AUTOSAR validators."""

from __future__ import annotations

import re
from collections import defaultdict, deque
from decimal import Decimal, InvalidOperation

from lxml import etree

from .arxml_index import ArxmlIndex, local_name
from .plugins import COMPONENT_TAGS, CONNECTOR_TAGS, INTERFACE_REF_TAGS, PORT_TAGS, PluginReport, plugin

DATA_PROTOTYPES = {
    "VARIABLE-DATA-PROTOTYPE", "PARAMETER-DATA-PROTOTYPE", "ARGUMENT-DATA-PROTOTYPE",
    "APPLICATION-ARRAY-ELEMENT", "APPLICATION-RECORD-ELEMENT", "IMPLEMENTATION-DATA-TYPE-ELEMENT",
}
APP_TYPES = {
    "APPLICATION-PRIMITIVE-DATA-TYPE", "APPLICATION-ARRAY-DATA-TYPE", "APPLICATION-RECORD-DATA-TYPE",
}
VALUE_SPECS = {
    "APPLICATION-VALUE-SPECIFICATION", "APPLICATION-RULE-BASED-VALUE-SPECIFICATION",
    "ARRAY-VALUE-SPECIFICATION", "NUMERICAL-RULE-BASED-VALUE-SPECIFICATION",
    "NUMERICAL-VALUE-SPECIFICATION", "RECORD-VALUE-SPECIFICATION",
    "REFERENCE-VALUE-SPECIFICATION", "TEXT-VALUE-SPECIFICATION", "CONSTANT-REFERENCE",
}
C_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _text(element: etree._Element | None) -> str:
    return (element.text or "").strip() if element is not None else ""


def _direct(element: etree._Element, tag: str) -> etree._Element | None:
    return next((child for child in element if local_name(child.tag) == tag), None)


def _first(element: etree._Element, tags: set[str]) -> etree._Element | None:
    return next((item for item in element.iterdescendants() if local_name(item.tag) in tags), None)


def _short_name(element: etree._Element) -> str:
    return _text(_direct(element, "SHORT-NAME"))


def _resolve(index: ArxmlIndex, ref: etree._Element | None, report: PluginReport, label: str, *, required: bool = True) -> etree._Element | None:
    if ref is None:
        if required:
            report.incomplete(f"missing {label}")
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


def _decimal(element: etree._Element | None, report: PluginReport, index: ArxmlIndex, label: str) -> Decimal | None:
    raw = _text(element)
    try:
        return Decimal(raw)
    except (InvalidOperation, ValueError):
        report.incomplete(f"non-numeric {label} {raw!r} at {index.location(element) if element is not None else None}")
        return None


def _type_of(index: ArxmlIndex, prototype: etree._Element, report: PluginReport) -> etree._Element | None:
    return _resolve(index, _first(prototype, {"TYPE-TREF"}), report, f"{local_name(prototype.tag)} type")


def _unwrap_impl(index: ArxmlIndex, data_type: etree._Element, report: PluginReport) -> etree._Element | None:
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


def _props(owner: etree._Element) -> etree._Element | None:
    return _first(owner, {"SW-DATA-DEF-PROPS"})


def _data_constr(index: ArxmlIndex, owner: etree._Element, report: PluginReport) -> etree._Element | None:
    ref = _first(owner, {"DATA-CONSTR-REF"})
    return _resolve(index, ref, report, "DataConstr", required=False)


def _intervals(index: ArxmlIndex, constr: etree._Element, report: PluginReport, physical: bool | None = None) -> list[tuple[Decimal, Decimal, bool, bool]] | None:
    containers: list[etree._Element] = []
    for item in constr.iterdescendants():
        tag = local_name(item.tag)
        if tag not in {"INTERNAL-CONSTRS", "PHYS-CONSTRS"}:
            continue
        if physical is True and tag != "PHYS-CONSTRS":
            continue
        if physical is False and tag != "INTERNAL-CONSTRS":
            continue
        containers.append(item)
    if not containers:
        report.incomplete(f"DataConstr has no applicable limit container at {index.location(constr)}")
        return None
    result: list[tuple[Decimal, Decimal, bool, bool]] = []
    for container in containers:
        lower_el = _first(container, {"LOWER-LIMIT"})
        upper_el = _first(container, {"UPPER-LIMIT"})
        if lower_el is None or upper_el is None:
            report.incomplete(f"incomplete limits at {index.location(container)}")
            return None
        lower = _decimal(lower_el, report, index, "lowerLimit")
        upper = _decimal(upper_el, report, index, "upperLimit")
        if lower is None or upper is None:
            return None
        lower_open = any(local_name(key) == "INTERVAL-TYPE" and str(value).upper() == "OPEN" for key, value in lower_el.attrib.items())
        upper_open = any(local_name(key) == "INTERVAL-TYPE" and str(value).upper() == "OPEN" for key, value in upper_el.attrib.items())
        if lower > upper or (lower == upper and (lower_open or upper_open)):
            report.incomplete(f"empty or inverted interval at {index.location(container)}")
            return None
        result.append((lower, upper, lower_open, upper_open))
    return result


def _contains(interval: tuple[Decimal, Decimal, bool, bool], value: Decimal) -> bool:
    low, high, low_open, high_open = interval
    return (value > low if low_open else value >= low) and (value < high if high_open else value <= high)


def _domain_contains(intervals: list[tuple[Decimal, Decimal, bool, bool]], value: Decimal) -> bool:
    return any(_contains(interval, value) for interval in intervals)


def _interval_subset(inner: list[tuple[Decimal, Decimal, bool, bool]], outer: list[tuple[Decimal, Decimal, bool, bool]]) -> bool:
    for low, high, low_open, high_open in inner:
        covered = False
        for outer_low, outer_high, outer_low_open, outer_high_open in outer:
            low_ok = low > outer_low or (low == outer_low and (low_open or not outer_low_open))
            high_ok = high < outer_high or (high == outer_high and (high_open or not outer_high_open))
            if low_ok and high_ok:
                covered = True
                break
        if not covered:
            return False
    return True


def _value_spec(container: etree._Element) -> etree._Element | None:
    return next((item for item in container.iterdescendants() if local_name(item.tag) in VALUE_SPECS), None)


def _constant_value(index: ArxmlIndex, value: etree._Element, report: PluginReport) -> etree._Element | None:
    if local_name(value.tag) != "CONSTANT-REFERENCE":
        return value
    constant = _resolve(index, _first(value, {"CONSTANT-REF"}), report, "ConstantReference")
    if constant is None:
        return None
    resolved = _value_spec(constant)
    if resolved is None:
        report.incomplete(f"ConstantSpecification has no ValueSpecification at {index.location(constant)}")
    return resolved


def _scalar(value: etree._Element, report: PluginReport, index: ArxmlIndex) -> tuple[str, str] | None:
    resolved = _constant_value(index, value, report)
    if resolved is None:
        return None
    tag = local_name(resolved.tag)
    field = _first(resolved, {"VALUE", "VT"})
    if field is None:
        report.incomplete(f"scalar ValueSpecification lacks VALUE/VT at {index.location(resolved)}")
        return None
    return tag, _text(field)


def _value_key(index: ArxmlIndex, value: etree._Element, report: PluginReport) -> object | None:
    resolved = _constant_value(index, value, report)
    if resolved is None:
        return None
    tag = local_name(resolved.tag)
    if tag in {"ARRAY-VALUE-SPECIFICATION", "RECORD-VALUE-SPECIFICATION"}:
        children = [
            item for item in resolved.iterdescendants()
            if local_name(item.tag) in VALUE_SPECS
            and index.nearest(index.parent.get(item), VALUE_SPECS) is resolved
        ]
        values = [_value_key(index, child, report) for child in children]
        return (tag, tuple(values))
    scalar = _scalar(resolved, report, index)
    return scalar


def _base_range(index: ArxmlIndex, data_type: etree._Element, report: PluginReport) -> list[tuple[Decimal, Decimal, bool, bool]] | None:
    base = _resolve(index, _first(data_type, {"BASE-TYPE-REF"}), report, "SwBaseType", required=False)
    if base is None:
        return None
    size = _decimal(_first(base, {"BASE-TYPE-SIZE"}), report, index, "baseTypeSize")
    if size is None or size != int(size) or size <= 0:
        return None
    bits = int(size)
    encoding = _text(_first(base, {"BASE-TYPE-ENCODING"})).upper()
    if "UNSIGNED" in encoding or encoding in {"BOOLEAN", "NONE"}:
        return [(Decimal(0), Decimal((1 << bits) - 1), False, False)]
    if "SIGNED" in encoding or "2C" in encoding:
        return [(Decimal(-(1 << (bits - 1))), Decimal((1 << (bits - 1)) - 1), False, False)]
    report.incomplete(f"unsupported base type encoding {encoding!r} at {index.location(base)}")
    return None


def _type_domain(index: ArxmlIndex, data_type: etree._Element, report: PluginReport, *, physical: bool | None = None) -> list[tuple[Decimal, Decimal, bool, bool]] | None:
    constr = _data_constr(index, data_type, report)
    if constr is not None:
        return _intervals(index, constr, report, physical)
    if local_name(data_type.tag) == "IMPLEMENTATION-DATA-TYPE":
        final = _unwrap_impl(index, data_type, report)
        if final is not None:
            return _base_range(index, final, report)
    return None


def _children(index: ArxmlIndex, owner: etree._Element, tags: set[str], owner_tags: set[str]) -> list[etree._Element]:
    result: list[etree._Element] = []
    for tag in tags:
        result.extend(_owned(index, owner, tag, owner_tags))
    return result


def _value_children(index: ArxmlIndex, value: etree._Element) -> list[etree._Element]:
    return [
        item for item in value.iterdescendants()
        if local_name(item.tag) in VALUE_SPECS
        and index.nearest(index.parent.get(item), VALUE_SPECS) is value
    ]


def _fits(index: ArxmlIndex, value: etree._Element, data_type: etree._Element, report: PluginReport) -> bool | None:
    value = _constant_value(index, value, report)
    if value is None:
        return None
    tag = local_name(data_type.tag)
    category = _text(_direct(data_type, "CATEGORY"))
    if tag == "IMPLEMENTATION-DATA-TYPE":
        final = _unwrap_impl(index, data_type, report)
        if final is None:
            return None
        data_type = final
        category = _text(_direct(final, "CATEGORY"))
    value_tag = local_name(value.tag)
    if tag == "APPLICATION-PRIMITIVE-DATA-TYPE" or category == "VALUE":
        scalar = _scalar(value, report, index)
        if scalar is None:
            return None
        if category == "STRING":
            return scalar[0] in {"APPLICATION-VALUE-SPECIFICATION", "TEXT-VALUE-SPECIFICATION"}
        if category == "BOOLEAN":
            return scalar[1].lower() in {"0", "1", "true", "false"}
        try:
            number = Decimal(scalar[1])
        except InvalidOperation:
            # Enumeration labels are admitted only when present in the CompuMethod.
            method = _resolve(index, _first(data_type, {"COMPU-METHOD-REF"}), report, "CompuMethod", required=False)
            if method is None:
                return False
            labels = {_text(item) for item in method.iterdescendants() if local_name(item.tag) in {"VT", "SHORT-LABEL", "SYMBOL"}}
            return scalar[1] in labels
        domain = _type_domain(index, data_type, report)
        return True if domain is None and not report.incomplete_reasons else (None if domain is None else _domain_contains(domain, number))
    if tag == "APPLICATION-ARRAY-DATA-TYPE" or category == "ARRAY":
        if value_tag not in {"ARRAY-VALUE-SPECIFICATION", "APPLICATION-RULE-BASED-VALUE-SPECIFICATION", "NUMERICAL-RULE-BASED-VALUE-SPECIFICATION"}:
            return False
        element_tag = "APPLICATION-ARRAY-ELEMENT" if tag == "APPLICATION-ARRAY-DATA-TYPE" else "IMPLEMENTATION-DATA-TYPE-ELEMENT"
        elements = _children(index, data_type, {element_tag}, {tag, element_tag})
        if len(elements) != 1:
            report.incomplete(f"array type has {len(elements)} element definitions at {index.location(data_type)}")
            return None
        element = elements[0]
        child_type = _resolve(index, _first(element, {"TYPE-TREF", "IMPLEMENTATION-DATA-TYPE-REF"}), report, "array element type")
        if child_type is None:
            return None
        values = _value_children(index, value)
        size_el = _first(element, {"MAX-NUMBER-OF-ELEMENTS", "ARRAY-SIZE"})
        size = int(_decimal(size_el, report, index, "array size") or -1)
        semantics = _text(_first(element, {"ARRAY-SIZE-SEMANTICS"}))
        if semantics == "FIXED-SIZE" and len(values) != size:
            return False
        if size >= 0 and len(values) > size:
            return False
        nested = [_fits(index, item, child_type, report) for item in values]
        return None if any(item is None for item in nested) else all(nested)
    if tag == "APPLICATION-RECORD-DATA-TYPE" or category == "STRUCTURE":
        if value_tag != "RECORD-VALUE-SPECIFICATION":
            return False
        element_tags = {"APPLICATION-RECORD-ELEMENT"} if tag == "APPLICATION-RECORD-DATA-TYPE" else {"IMPLEMENTATION-DATA-TYPE-ELEMENT"}
        elements = _children(index, data_type, element_tags, {tag, *element_tags})
        values = _value_children(index, value)
        if len(elements) != len(values):
            return False
        checks: list[bool | None] = []
        for element, child_value in zip(elements, values):
            child_type = _resolve(index, _first(element, {"TYPE-TREF", "IMPLEMENTATION-DATA-TYPE-REF"}), report, "record element type")
            checks.append(None if child_type is None else _fits(index, child_value, child_type, report))
        return None if any(item is None for item in checks) else all(checks)
    report.incomplete(f"unsupported value-fitting category {category!r} at {index.location(data_type)}")
    return None


@plugin("declared_invalid_value_scope")
def declared_invalid_value_scope(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    expected = "APPLICATION-VALUE-SPECIFICATION" if rule["constraint_id"] == "constr_1281" else "NUMERICAL-VALUE-SPECIFICATION"
    for data_type in selected:
        if _text(_direct(data_type, "CATEGORY")) != "VALUE":
            report.fail(index, data_type, "Declared invalid-value scope target is not category VALUE",
                        repair=_repair("replace_value", "CATEGORY", "Bind this rule only to a VALUE ApplicationPrimitiveDataType."))
            continue
        invalid = _first(data_type, {"INVALID-VALUE"})
        spec = _value_spec(invalid) if invalid is not None else None
        if spec is None:
            report.incomplete(f"declared invalid-value scope target has no invalidValue at {index.location(data_type)}")
        elif local_name(spec.tag) != expected:
            report.fail(index, spec, "invalidValue representation does not match its explicitly declared CompuMethod scope",
                        actual=local_name(spec.tag), expected=expected,
                        repair=_repair("replace_value_specification", local_name(spec.tag), f"Use {expected} for the declared invalid-value scope."))
    return report


@plugin("periodic_runnable_event")
def periodic_runnable_event(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for runnable in selected:
        matches: list[etree._Element] = []
        for event in index.elements("TIMING-EVENT"):
            target = _resolve(index, _first(event, {"START-ON-EVENT-REF"}), report, "TimingEvent runnable")
            if target is runnable:
                matches.append(event)
        if not matches:
            report.fail(index, runnable, "RunnableEntity declared for periodic execution has no TimingEvent",
                        repair=_repair("add_element", "TIMING-EVENT", "Add a TimingEvent with PERIOD and START-ON-EVENT-REF targeting this RunnableEntity."))
        for event in matches:
            period = _first(event, {"PERIOD"})
            if period is None or _decimal(period, report, index, "TimingEvent period") is None:
                report.fail(index, event, "Periodic TimingEvent lacks a numeric PERIOD",
                            repair=_repair("add_element", "PERIOD", "Set the explicitly required execution period."))
    return report


@plugin("asynchronous_blocking_wait")
def asynchronous_blocking_wait(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for point in selected:
        return_events: list[etree._Element] = []
        for event in index.elements("ASYNCHRONOUS-SERVER-CALL-RETURNS-EVENT"):
            refs = index.descendants(event, {"ASYNCHRONOUS-SERVER-CALL-RESULT-POINT-REF", "RESULT-POINT-REF"})
            targets = [_resolve(index, ref, report, "returns-event result point") for ref in refs]
            if any(target is point for target in targets):
                return_events.append(event)
        waits: list[etree._Element] = []
        for wait in index.elements("WAIT-POINT"):
            for ref in index.descendants(wait, {"TRIGGER-REF", "EVENT-REF", "ASYNCHRONOUS-SERVER-CALL-RETURNS-EVENT-REF"}):
                target = _resolve(index, ref, report, "WaitPoint trigger")
                if any(target is event for event in return_events):
                    waits.append(wait)
        if not waits:
            continue
        if not return_events:
            report.incomplete(f"blocking WaitPoint has no associated returns event for {index.location(point)}")
        for event in return_events:
            start = _first(event, {"START-ON-EVENT-REF"})
            if start is not None:
                report.fail(index, start, "Blocking asynchronous returns event must not start a RunnableEntity",
                            repair=_repair("remove", "START-ON-EVENT-REF", "Remove the runnable start reference from the blocking returns event."))
    return report


@plugin("sender_mode_management_points")
def sender_mode_management_points(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for runnable in selected:
        points = _owned(index, runnable, "MODE-SWITCH-POINT", {"RUNNABLE-ENTITY"})
        if not points:
            report.fail(index, runnable, "RunnableEntity declared as a mode sender has no ModeSwitchPoint",
                        repair=_repair("add_element", "MODE-SWITCH-POINT", "Add ModeSwitchPoints for every managed ModeDeclarationGroup."))
            continue
        for point in points:
            ref = _first(point, {"MODE-GROUP-REF", "TARGET-MODE-GROUP-REF"})
            if ref is None:
                report.incomplete(f"ModeSwitchPoint has no ModeDeclarationGroup reference at {index.location(point)}")
            else:
                _resolve(index, ref, report, "ModeSwitchPoint mode group")
    return report


@plugin("replace_invalid_not_init")
def replace_invalid_not_init(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for policy in index.elements("INVALIDATION-POLICY"):
        if _text(_first(policy, {"HANDLE-INVALID"})).lower() != "replace":
            continue
        data = _resolve(index, _first(policy, {"DATA-ELEMENT-REF"}), report, "InvalidationPolicy data element")
        if data is None:
            continue
        data_type = _type_of(index, data, report)
        invalid_container = _first(data_type, {"INVALID-VALUE"}) if data_type is not None else None
        invalid = _value_spec(invalid_container) if invalid_container is not None else None
        if invalid is None:
            report.incomplete(f"replace policy data element has no invalidValue at {index.location(data)}")
            continue
        for comspec in index.elements("NONQUEUED-RECEIVER-COM-SPEC"):
            target = _resolve(index, _first(comspec, {"DATA-ELEMENT-REF"}), report, "ReceiverComSpec data element")
            if target is not data:
                continue
            init_container = _first(comspec, {"INIT-VALUE"})
            init = _value_spec(init_container) if init_container is not None else None
            if init is not None and _value_key(index, init, report) == _value_key(index, invalid, report):
                report.fail(index, init, "Receiver initValue equals invalidValue while handleInvalid=replace",
                            repair=_repair("replace_value_specification", "INIT-VALUE", "Choose an initial value different from invalidValue."))
    return report


@plugin("memory_short_name_c_identifier")
def memory_short_name_c_identifier(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    roles = {"VARIABLE-DATA-PROTOTYPE": "STATIC-MEMORY", "PARAMETER-DATA-PROTOTYPE": "CONSTANT-MEMORY"}
    for prototype in selected:
        role = roles.get(local_name(prototype.tag))
        if role is None or index.nearest(prototype, {role}) is None:
            continue
        short = _short_name(prototype)
        symbol = _text(_direct(prototype, "SYMBOL"))
        if not short or not C_IDENTIFIER.fullmatch(short):
            report.fail(index, _direct(prototype, "SHORT-NAME") or prototype, "Memory prototype SHORT-NAME is not a valid C identifier",
                        actual=short, repair=_repair("replace_value", "SHORT-NAME", "Use the exact valid C identifier of the variable or constant."))
        elif symbol and symbol != short:
            report.fail(index, _direct(prototype, "SYMBOL") or prototype, "Memory prototype SHORT-NAME differs from its explicit C symbol",
                        short_name=short, symbol=symbol,
                        repair=_repair("replace_value", "SHORT-NAME", "Make SHORT-NAME identical to SYMBOL.", expected=symbol))
    return report


@plugin("compu_scale_c_symbol")
def compu_scale_c_symbol(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for scale in selected:
        lower = _text(_first(scale, {"LOWER-LIMIT"}))
        upper = _text(_first(scale, {"UPPER-LIMIT"}))
        if not lower or lower != upper:
            continue
        symbol = _text(_first(scale, {"SYMBOL"}))
        vt = _text(_first(scale, {"VT"}))
        label = _text(_direct(scale, "SHORT-LABEL"))
        if symbol:
            chosen_source, chosen = "symbol", symbol
        elif C_IDENTIFIER.fullmatch(vt or ""):
            chosen_source, chosen = "vt", vt
        elif label:
            chosen_source, chosen = "shortLabel", label
        else:
            report.fail(index, scale, "Point-range CompuScale has no usable C symbol source",
                        repair=_repair("add_element", "SYMBOL", "Add SYMBOL, a C-identifier VT, or SHORT-LABEL."))
            continue
        report.observe(semantic="compu_scale_c_symbol", subject=index.path_of(scale), source=chosen_source, symbol=chosen)
    return report


def _interface(index: ArxmlIndex, port: etree._Element, report: PluginReport) -> etree._Element | None:
    return _resolve(index, _first(port, INTERFACE_REF_TAGS), report, "PortPrototype interface")


def _writer_target(index: ArxmlIndex, access: etree._Element, report: PluginReport) -> tuple[etree._Element | None, etree._Element | None]:
    candidate = _first(access, {"ACCESSED-VARIABLE", "AUTOSAR-VARIABLE"})
    wrapper = candidate if candidate is not None else access
    target = _resolve(index, _first(wrapper, {"TARGET-DATA-PROTOTYPE-REF", "TARGET-VARIABLE-DATA-PROTOTYPE-REF"}), report, "written data prototype")
    port = _resolve(index, _first(wrapper, {"PORT-PROTOTYPE-REF"}), report, "writer port", required=False)
    return target, port


def _acknowledged(index: ArxmlIndex, port: etree._Element | None, target: etree._Element, report: PluginReport) -> bool:
    if port is None:
        return False
    for comspec in index.descendants(port, {"NONQUEUED-SENDER-COM-SPEC", "QUEUED-SENDER-COM-SPEC"}):
        data = _resolve(index, _first(comspec, {"DATA-ELEMENT-REF"}), report, "SenderComSpec data element")
        if data is target and _text(_first(comspec, {"TRANSMISSION-ACKNOWLEDGE"})).lower() in {"true", "1"}:
            return True
    return False


@plugin("acknowledged_writer_unique")
def acknowledged_writer_unique(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    access_tags = {"VARIABLE-ACCESS", "DATA-SEND-POINT", "DATA-WRITE-ACCESS"}
    for behavior in index.elements("SWC-INTERNAL-BEHAVIOR"):
        writers: dict[int, list[tuple[etree._Element, etree._Element]]] = defaultdict(list)
        for runnable in _owned(index, behavior, "RUNNABLE-ENTITY", {"SWC-INTERNAL-BEHAVIOR"}):
            seen: set[int] = set()
            for access in [item for item in runnable.iterdescendants() if local_name(item.tag) in access_tags]:
                target, port = _writer_target(index, access, report)
                if target is not None and id(target) not in seen and _acknowledged(index, port, target, report):
                    writers[id(target)].append((runnable, access))
                    seen.add(id(target))
        for entries in writers.values():
            if len(entries) > 1:
                target, _ = _writer_target(index, entries[0][1], report)
                for runnable, access in entries[1:]:
                    report.fail(index, access, "More than one RunnableEntity writes acknowledged sender data",
                                target=index.path_of(target) if target is not None else None,
                                writers=[index.path_of(item[0]) for item in entries],
                                repair=_repair("remove_or_reassign_access", local_name(access.tag), "Keep exactly one writer or disable transmission acknowledgement."))
    return report


@plugin("conversion_compu_category")
def conversion_compu_category(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    allowed = {"LINEAR", "IDENTICAL", "SCALE_LINEAR_AND_TEXTTABLE", "TEXTTABLE", "BITFIELD_TEXTTABLE"}
    for data_type in [item for item in selected if local_name(item.tag) in APP_TYPES | {"IMPLEMENTATION-DATA-TYPE"}]:
        ref = _first(data_type, {"COMPU-METHOD-REF"})
        if ref is None:
            continue
        method = _resolve(index, ref, report, "AutosarDataType CompuMethod")
        if method is None:
            continue
        category = _text(_direct(method, "CATEGORY"))
        if category not in allowed:
            report.fail(index, _direct(method, "CATEGORY") or method, "CompuMethod category is unsupported for data conversion",
                        actual=category, allowed=sorted(allowed), data_type=index.path_of(data_type),
                        repair=_repair("replace_value", "CATEGORY", "Use a supported conversion category or remove the conversion requirement."))
    return report


@plugin("implementation_invalid_value_range")
def implementation_invalid_value_range(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for data_type in selected:
        invalid_container = _first(data_type, {"INVALID-VALUE"})
        if invalid_container is None:
            continue
        value = _value_spec(invalid_container)
        if value is None:
            report.incomplete(f"invalidValue has no ValueSpecification at {index.location(invalid_container)}")
            continue
        scalar = _scalar(value, report, index)
        domain = _type_domain(index, data_type, report, physical=False)
        if scalar is None or domain is None:
            continue
        try:
            number = Decimal(scalar[1])
        except InvalidOperation:
            report.fail(index, value, "ImplementationDataType invalidValue is not numerical",
                        repair=_repair("replace_value_specification", local_name(value.tag), "Use a numerical invalid value fitting the implementation range."))
            continue
        if not _domain_contains(domain, number):
            report.fail(index, value, "invalidValue is outside the ImplementationDataType range",
                        actual=str(number), allowed=[tuple(map(str, item[:2])) for item in domain],
                        repair=_repair("replace_value", "VALUE", "Choose a value inside internalConstrs/base-type range."))
    return report


@plugin("value_specification_fits_type")
def value_specification_fits_type(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    roots = [item for item in selected if local_name(item.tag) in VALUE_SPECS]
    for value in roots:
        if index.nearest(index.parent.get(value), VALUE_SPECS) is not None:
            continue
        prototype = index.nearest(value, DATA_PROTOTYPES)
        data_type = _type_of(index, prototype, report) if prototype is not None else index.nearest(value, APP_TYPES | {"IMPLEMENTATION-DATA-TYPE"})
        if data_type is None:
            report.incomplete(f"cannot establish type context for {index.location(value)}")
            continue
        fits = _fits(index, value, data_type, report)
        if fits is False:
            report.fail(index, value, "ValueSpecification does not fit its resolved AutosarDataType without information loss",
                        data_type=index.path_of(data_type),
                        repair=_repair("replace_value_specification", local_name(value.tag), "Match value kind, shape, cardinality and range to the resolved AutosarDataType."))
    return report


@plugin("value_axis_constraint_subset")
def value_axis_constraint_subset(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for props in selected:
        direct = _resolve(index, _first(props, {"DATA-CONSTR-REF"}), report, "SwDataDefProps DataConstr", required=False)
        value_type = _resolve(index, _first(props, {"VALUE-AXIS-DATA-TYPE-REF", "VALUE-AXIS-DATA-TYPE-TREF"}), report, "valueAxisDataType", required=False)
        inherited = _data_constr(index, value_type, report) if value_type is not None else None
        if direct is None or inherited is None:
            continue
        inner = _intervals(index, direct, report)
        outer = _intervals(index, inherited, report)
        if inner is not None and outer is not None and not _interval_subset(inner, outer):
            report.fail(index, _first(props, {"DATA-CONSTR-REF"}) or props, "SwDataDefProps.dataConstr relaxes the value-axis DataConstr",
                        repair=_repair("repair_reference", "DATA-CONSTR-REF", "Reference a DataConstr whose domain is a subset of the value-axis domain."))
    return report


def _compu_intervals(index: ArxmlIndex, data_type: etree._Element, report: PluginReport) -> list[tuple[Decimal, Decimal, bool, bool]] | None:
    method = _resolve(index, _first(data_type, {"COMPU-METHOD-REF"}), report, "CompuMethod", required=False)
    if method is None:
        return None
    result: list[tuple[Decimal, Decimal, bool, bool]] = []
    for scale in index.descendants(method, {"COMPU-SCALE"}):
        lower_el = _first(scale, {"LOWER-LIMIT"})
        upper_el = _first(scale, {"UPPER-LIMIT"})
        if lower_el is None or upper_el is None:
            continue
        lower = _decimal(lower_el, report, index, "CompuScale lowerLimit")
        upper = _decimal(upper_el, report, index, "CompuScale upperLimit")
        if lower is not None and upper is not None:
            result.append((lower, upper, False, False))
    if not result:
        report.incomplete(f"CompuMethod has no numeric definition range at {index.location(method)}")
        return None
    return result


@plugin("invalidation_outside_compu_interval")
def invalidation_outside_compu_interval(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for interface in selected:
        for policy in index.descendants(interface, {"INVALIDATION-POLICY"}):
            if _text(_first(policy, {"HANDLE-INVALID"})).lower() in {"", "dontinvalidate", "dont_invalidate"}:
                continue
            data = _resolve(index, _first(policy, {"DATA-ELEMENT-REF"}), report, "InvalidationPolicy data element")
            data_type = _type_of(index, data, report) if data is not None else None
            invalid = _value_spec(_first(data_type, {"INVALID-VALUE"})) if data_type is not None and _first(data_type, {"INVALID-VALUE"}) is not None else None
            intervals = _compu_intervals(index, data_type, report) if data_type is not None else None
            scalar = _scalar(invalid, report, index) if invalid is not None else None
            if invalid is None:
                report.incomplete(f"invalidation policy target lacks invalidValue at {index.location(data) if data is not None else index.location(policy)}")
                continue
            if scalar is None or intervals is None:
                continue
            try:
                number = Decimal(scalar[1])
            except InvalidOperation:
                continue
            if _domain_contains(intervals, number):
                report.fail(index, invalid, "invalidValue lies inside the CompuMethod interval while invalidation is enabled",
                            actual=str(number), repair=_repair("replace_value", "VALUE", "Choose an invalid value outside every CompuScale interval or use dontInvalidate."))
    return report


def _mapped_pair(index: ArxmlIndex, mapping: etree._Element, report: PluginReport) -> tuple[etree._Element | None, etree._Element | None]:
    return (
        _resolve(index, _first(mapping, {"APPLICATION-DATA-TYPE-REF"}), report, "mapped ApplicationDataType"),
        _resolve(index, _first(mapping, {"IMPLEMENTATION-DATA-TYPE-REF"}), report, "mapped ImplementationDataType"),
    )


@plugin("mapped_limit_consistency")
def mapped_limit_consistency(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for mapping in index.elements("DATA-TYPE-MAP"):
        app, impl = _mapped_pair(index, mapping, report)
        if app is None or impl is None:
            continue
        app_domain = _type_domain(index, app, report, physical=True)
        compu_domain = _compu_intervals(index, app, report) if _first(app, {"COMPU-METHOD-REF"}) is not None else None
        if app_domain is not None and compu_domain is not None and not _interval_subset(app_domain, compu_domain):
            report.fail(index, mapping, "ApplicationDataType limits exceed the CompuMethod definition range",
                        repair=_repair("repair_data_constr", "DATA-CONSTR-REF", "Restrict application limits to the applicable CompuMethod range."))
        impl_domain = _type_domain(index, impl, report, physical=False)
        if app_domain is not None and impl_domain is not None and not _interval_subset(app_domain, impl_domain):
            report.fail(index, mapping, "ApplicationDataType limits exceed mapped implementation internal constraints",
                        repair=_repair("repair_data_constr", "DATA-TYPE-MAP", "Align mapped application and implementation constraint domains."))
        base_domain = _base_range(index, _unwrap_impl(index, impl, report) or impl, report)
        if impl_domain is not None and base_domain is not None and not _interval_subset(impl_domain, base_domain):
            report.fail(index, impl, "ImplementationDataType constraints exceed the SwBaseType representable range",
                        repair=_repair("repair_data_constr", "DATA-CONSTR-REF", "Restrict internal constraints or select a wider SwBaseType."))
    return report


def _prototype_domain(index: ArxmlIndex, prototype: etree._Element, report: PluginReport) -> list[tuple[Decimal, Decimal, bool, bool]] | None:
    data_type = _type_of(index, prototype, report)
    return _type_domain(index, data_type, report) if data_type is not None else None


def _interface_members(index: ArxmlIndex, interface: etree._Element) -> list[etree._Element]:
    return [item for item in interface.iterdescendants() if local_name(item.tag) in {"VARIABLE-DATA-PROTOTYPE", "PARAMETER-DATA-PROTOTYPE"} and index.nearest(item, {local_name(interface.tag)}) is interface]


@plugin("provider_data_constr_subset")
def provider_data_constr_subset(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for connector in index.select_any(sorted(CONNECTOR_TAGS)):
        provider = _resolve(index, _first(connector, {"TARGET-P-PORT-REF", "PROVIDED-OUTER-PORT-REF"}), report, "provider port")
        requester = _resolve(index, _first(connector, {"TARGET-R-PORT-REF", "REQUIRED-OUTER-PORT-REF"}), report, "requester port")
        if provider is None or requester is None:
            continue
        provider_if = _interface(index, provider, report)
        requester_if = _interface(index, requester, report)
        if provider_if is None or requester_if is None:
            continue
        requesting = {_short_name(item): item for item in _interface_members(index, requester_if)}
        for sent in _interface_members(index, provider_if):
            received = requesting.get(_short_name(sent))
            if received is None:
                continue
            sent_domain = _prototype_domain(index, sent, report)
            received_domain = _prototype_domain(index, received, report)
            if sent_domain is None and received_domain is None:
                continue
            if sent_domain is None or received_domain is None:
                report.fail(index, sent, "Provider/receiver DataConstr presence is incompatible",
                            repair=_repair("repair_data_constr", "DATA-CONSTR-REF", "Define compatible constraints on both sides or on neither side."))
            elif not _interval_subset(sent_domain, received_domain):
                report.fail(index, sent, "Provider DataConstr is not contained in the requiring DataConstr",
                            provider=index.path_of(sent), requiring=index.path_of(received),
                            repair=_repair("repair_data_constr", "DATA-CONSTR-REF", "Restrict provider values or widen the requiring domain."))
    return report


@plugin("pass_through_requires_atomic_path")
def pass_through_requires_atomic_path(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    # Build a conservative connector graph. Atomic component instances add the only
    # permitted intra-instance edge; missing endpoint context prevents a PASS.
    graph: dict[int, list[tuple[int, bool]]] = defaultdict(list)
    elements: dict[int, etree._Element] = {}
    for connector in index.select_any(sorted(CONNECTOR_TAGS)):
        endpoints: list[etree._Element] = []
        for ref in connector.iterdescendants():
            if local_name(ref.tag) not in {"TARGET-P-PORT-REF", "TARGET-R-PORT-REF", "OUTER-PORT-REF", "PROVIDED-OUTER-PORT-REF", "REQUIRED-OUTER-PORT-REF"}:
                continue
            target = _resolve(index, ref, report, "connector port")
            if target is not None and all(target is not item for item in endpoints):
                endpoints.append(target)
        for first in endpoints:
            elements[id(first)] = first
            for second in endpoints:
                if first is not second:
                    graph[id(first)].append((id(second), False))
    atomic_tags = COMPONENT_TAGS - {"COMPOSITION-SW-COMPONENT-TYPE", "PARAMETER-SW-COMPONENT-TYPE"}
    for prototype in index.elements("SW-COMPONENT-PROTOTYPE"):
        component_type = _resolve(index, _first(prototype, {"TYPE-TREF"}), report, "component prototype type")
        if component_type is None or local_name(component_type.tag) not in atomic_tags:
            continue
        ports = index.descendants(component_type, PORT_TAGS)
        for first in ports:
            elements[id(first)] = first
            for second in ports:
                if first is not second:
                    graph[id(first)].append((id(second), True))
    for connector in selected:
        required = _resolve(index, _first(connector, {"REQUIRED-OUTER-PORT-REF"}), report, "pass-through required outer port")
        provided = _resolve(index, _first(connector, {"PROVIDED-OUTER-PORT-REF"}), report, "pass-through provided outer port")
        if required is None or provided is None:
            continue
        queue = deque([(id(required), False)])
        visited = {(id(required), False)}
        forbidden_path = False
        while queue:
            node, atomic_seen = queue.popleft()
            if node == id(provided) and not atomic_seen:
                forbidden_path = True
                break
            for target, atomic_edge in graph.get(node, []):
                state = (target, atomic_seen or atomic_edge)
                if state not in visited:
                    visited.add(state)
                    queue.append(state)
        if forbidden_path:
            report.fail(index, connector, "PassThroughSwConnector participates in an outer-port loop without an atomic component instance",
                        repair=_repair("remove_or_rewire_connector", "PASS-THROUGH-SW-CONNECTOR", "Break the loop or route it through an AtomicSwComponentType instance."))
    return report


@plugin("transformed_prototype_signal_exclusive")
def transformed_prototype_signal_exclusive(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    prototype_transformed: set[int] = set()
    for mapping in index.elements("DATA-PROTOTYPE-MAPPING"):
        if _first(mapping, {"DATA-TRANSFORMATION-REF", "FIRST-TO-SECOND-DATA-TRANSFORMATION-REF", "SECOND-TO-FIRST-DATA-TRANSFORMATION-REF"}) is None:
            continue
        for ref in index.descendants(mapping, {"FIRST-DATA-PROTOTYPE-REF", "SECOND-DATA-PROTOTYPE-REF", "TARGET-DATA-PROTOTYPE-REF"}):
            target = _resolve(index, ref, report, "transformed DataPrototypeMapping prototype")
            if target is not None:
                prototype_transformed.add(id(target))
    for mapping_tag in {"SENDER-RECEIVER-TO-SIGNAL-MAPPING", "SENDER-RECEIVER-TO-SIGNAL-GROUP-MAPPING", "SENDER-RECEIVER-COMPOSITE-ELEMENT-TO-SIGNAL-MAPPING"}:
        for mapping in index.elements(mapping_tag):
            refs = [item for item in mapping.iterdescendants() if local_name(item.tag).endswith("-REF")]
            targets = [_resolve(index, ref, report, "system data mapping reference") for ref in refs]
            prototypes = [item for item in targets if item is not None and local_name(item.tag) == "VARIABLE-DATA-PROTOTYPE"]
            signals = [item for item in targets if item is not None and local_name(item.tag) in {"I-SIGNAL", "I-SIGNAL-GROUP"}]
            if not any(id(item) in prototype_transformed for item in prototypes):
                continue
            for signal in signals:
                if _first(signal, {"DATA-TRANSFORMATION-REF"}) is not None:
                    report.fail(index, mapping, "VariableDataPrototype and its ISignal path both reference a DataTransformation",
                                prototype=[index.path_of(item) for item in prototypes], signal=index.path_of(signal),
                                repair=_repair("remove", "DATA-TRANSFORMATION-REF", "Keep transformation on either DataPrototypeMapping or ISignal path, not both."))
    return report

