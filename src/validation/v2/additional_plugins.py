"""Reusable and high-value ARXML validators for the V2 migration plan.

These validators deliberately implement only predicates that can be evaluated from
serialized ARXML.  Missing references or missing values needed by a predicate are
reported as incomplete, never as a successful check.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from lxml import etree

from .arxml_index import ArxmlIndex, local_name, normalized_ref
from .plugins import PluginReport, plugin

TRUE_VALUES = {"true", "1"}


def _children(element: etree._Element, tag: str) -> list[etree._Element]:
    return [child for child in element if local_name(child.tag) == tag]


def _descendants(element: etree._Element, tag: str) -> list[etree._Element]:
    return [child for child in element.iterdescendants() if local_name(child.tag) == tag]


def _first(element: etree._Element, tag: str) -> etree._Element | None:
    return next((child for child in element.iterdescendants() if local_name(child.tag) == tag), None)


def _text(element: etree._Element | None) -> str:
    return (element.text or "").strip() if element is not None else ""


def _resolve(index: ArxmlIndex, ref: etree._Element, report: PluginReport) -> etree._Element | None:
    resolution = index.resolve(ref)
    if resolution.status != "resolved":
        report.incomplete(
            f"{resolution.status} reference {resolution.reference} at {index.location(ref)}"
        )
        return None
    return resolution.element


@plugin("forbid_descendant_tags")
def forbid_descendant_tags(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    forbidden = set(rule.get("parameters", {}).get("forbidden_tags", []))
    for subject in selected:
        for element in subject.iterdescendants():
            if local_name(element.tag) in forbidden:
                report.fail(index, element, f"{local_name(element.tag)} is forbidden in {local_name(subject.tag)}")
    return report


@plugin("numeric_range")
def numeric_range(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    params = rule.get("parameters", {})
    value_tag = params.get("value_tag")
    minimum = Decimal(str(params["minimum"])) if "minimum" in params else None
    maximum = Decimal(str(params["maximum"])) if "maximum" in params else None
    min_exclusive = bool(params.get("minimum_exclusive", False))
    max_exclusive = bool(params.get("maximum_exclusive", False))
    report = PluginReport(checked=len(selected))
    for subject in selected:
        values = [subject] if local_name(subject.tag) == value_tag else _descendants(subject, value_tag)
        if not values:
            report.incomplete(f"missing {value_tag} at {index.location(subject)}")
            continue
        for element in values:
            try:
                value = Decimal(_text(element))
            except InvalidOperation:
                report.fail(index, element, f"{value_tag} is not numeric", actual=_text(element))
                continue
            below = minimum is not None and (value <= minimum if min_exclusive else value < minimum)
            above = maximum is not None and (value >= maximum if max_exclusive else value > maximum)
            if below or above:
                report.fail(
                    index,
                    element,
                    f"{value_tag} is outside the permitted range",
                    actual=str(value),
                    minimum=str(minimum) if minimum is not None else None,
                    maximum=str(maximum) if maximum is not None else None,
                    minimum_exclusive=min_exclusive,
                    maximum_exclusive=max_exclusive,
                )
    return report


@plugin("value_domain")
def value_domain(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    params = rule.get("parameters", {})
    value_tag = params.get("value_tag")
    allowed = {str(value).upper() for value in params.get("allowed", [])}
    report = PluginReport(checked=len(selected))
    for subject in selected:
        values = [subject] if local_name(subject.tag) == value_tag else _descendants(subject, value_tag)
        if not values:
            report.incomplete(f"missing {value_tag} at {index.location(subject)}")
            continue
        for element in values:
            actual = _text(element)
            if actual.upper() not in allowed:
                report.fail(index, element, f"{value_tag} has an unsupported value", actual=actual, allowed=sorted(allowed))
    return report


@plugin("at_least_one_descendant")
def at_least_one_descendant(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    tags = set(rule.get("parameters", {}).get("tags", []))
    report = PluginReport(checked=len(selected))
    for subject in selected:
        found = {local_name(item.tag) for item in subject.iterdescendants()} & tags
        if not found:
            report.fail(index, subject, "At least one required alternative is missing", alternatives=sorted(tags))
    return report


@plugin("unique_descendant_values")
def unique_descendant_values(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    tags = rule.get("parameters", {}).get("value_tags", [])
    report = PluginReport(checked=len(selected))
    for subject in selected:
        for tag in tags:
            first_by_value: dict[str, etree._Element] = {}
            for element in _descendants(subject, tag):
                value = _text(element)
                if not value:
                    report.incomplete(f"empty {tag} at {index.location(element)}")
                    continue
                if value in first_by_value:
                    report.fail(index, element, f"{tag} shall be unique within {local_name(subject.tag)}", actual=value, first=index.location(first_by_value[value]))
                else:
                    first_by_value[value] = element
    return report


def _init_runnable(index: ArxmlIndex, event: etree._Element, report: PluginReport) -> etree._Element | None:
    ref = _first(event, "START-ON-EVENT-REF")
    if ref is None:
        report.incomplete(f"INIT-EVENT lacks START-ON-EVENT-REF at {index.location(event)}")
        return None
    target = _resolve(index, ref, report)
    if target is not None and local_name(target.tag) != "RUNNABLE-ENTITY":
        report.fail(index, ref, "InitEvent.startOnEvent does not resolve to RunnableEntity", actual=local_name(target.tag))
        return None
    return target


@plugin("init_event_runnable_shape")
def init_event_runnable_shape(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    check = rule.get("parameters", {}).get("check")
    report = PluginReport(checked=len(selected))
    for event in selected:
        runnable = _init_runnable(index, event, report)
        if runnable is None:
            continue
        if check == "no_wait_point":
            for item in _descendants(runnable, "WAIT-POINT"):
                report.fail(index, item, "RunnableEntity triggered by InitEvent shall not aggregate WaitPoint")
        elif check == "minimum_start_interval_zero":
            value = _first(runnable, "MINIMUM-START-INTERVAL")
            if value is None:
                report.incomplete(f"missing MINIMUM-START-INTERVAL at {index.location(runnable)}")
            else:
                try:
                    is_zero = Decimal(_text(value)) == 0
                except InvalidOperation:
                    is_zero = False
                if not is_zero:
                    report.fail(index, value, "RunnableEntity triggered by InitEvent requires minimumStartInterval = 0", actual=_text(value))
        elif check == "no_async_result_point":
            for item in _descendants(runnable, "ASYNCHRONOUS-SERVER-CALL-RESULT-POINT"):
                report.fail(index, item, "RunnableEntity triggered by InitEvent shall not aggregate AsynchronousServerCallResultPoint")
        else:
            report.incomplete(f"unknown init-event check {check!r}")
    return report


@plugin("wait_point_trigger_event_domain")
def wait_point_trigger_event_domain(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    allowed = set(rule.get("parameters", {}).get("allowed_event_tags", []))
    report = PluginReport(checked=len(selected))
    for wait_point in selected:
        ref = _first(wait_point, "TRIGGER-REF")
        if ref is None:
            report.incomplete(f"WAIT-POINT lacks TRIGGER-REF at {index.location(wait_point)}")
            continue
        target = _resolve(index, ref, report)
        if target is not None and local_name(target.tag) not in allowed:
            report.fail(index, ref, "WaitPoint trigger resolves to an unsupported RTEEvent", actual=local_name(target.tag), allowed=sorted(allowed))
    return report


@plugin("mode_declaration_group_ordering")
def mode_declaration_group_ordering(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    check = rule.get("parameters", {}).get("check")
    report = PluginReport(checked=len(selected))
    for group in selected:
        category = _text(_first(group, "CATEGORY")).upper()
        on_transition = _children(group, "ON-TRANSITION-VALUE")
        modes = _descendants(group, "MODE-DECLARATION")
        mode_values = [(mode, _children(mode, "VALUE")) for mode in modes]
        if check == "explicit_requires_values" and category == "EXPLICIT-ORDER":
            if not on_transition:
                report.fail(index, group, "EXPLICIT_ORDER ModeDeclarationGroup requires ON-TRANSITION-VALUE")
            for mode, values in mode_values:
                if not values:
                    report.fail(index, mode, "Every ModeDeclaration in EXPLICIT_ORDER requires VALUE")
        elif check == "non_explicit_forbids_values" and category != "EXPLICIT-ORDER":
            for element in on_transition + [v for _, values in mode_values for v in values]:
                report.fail(index, element, "Mode values are forbidden unless category is EXPLICIT_ORDER", category=category or None)
        elif check == "values_do_not_overlap":
            first_by_value: dict[str, etree._Element] = {}
            for element in on_transition + [v for _, values in mode_values for v in values]:
                value = _text(element)
                if value in first_by_value:
                    report.fail(index, element, "ModeDeclaration.value and onTransitionValue shall not overlap", actual=value, first=index.location(first_by_value[value]))
                else:
                    first_by_value[value] = element
        elif check not in {"explicit_requires_values", "non_explicit_forbids_values", "values_do_not_overlap"}:
            report.incomplete(f"unknown mode-ordering check {check!r}")
    return report


@plugin("conditional_required_descendant")
def conditional_required_descendant(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    params = rule.get("parameters", {})
    if_tag = params.get("if_tag")
    if_value = str(params.get("if_value", "")).upper()
    required_tag = params.get("required_tag")
    report = PluginReport(checked=len(selected))
    for subject in selected:
        antecedent = _first(subject, if_tag)
        if antecedent is not None and _text(antecedent).upper() == if_value and _first(subject, required_tag) is None:
            report.fail(index, subject, f"{required_tag} is required when {if_tag} is {if_value}")
    return report


@plugin("mode_and_disabled_mode_distinct")
def mode_and_disabled_mode_distinct(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for event in selected:
        mode_refs: set[str] = set()
        disabled_refs: set[str] = set()
        for container in _descendants(event, "MODE-IREF"):
            mode_refs.update(normalized_ref(ref.text) for ref in container.iterdescendants() if local_name(ref.tag).endswith("MODE-DECLARATION-REF") and normalized_ref(ref.text))
        for container in _descendants(event, "DISABLED-MODE-IREF"):
            disabled_refs.update(normalized_ref(ref.text) for ref in container.iterdescendants() if local_name(ref.tag).endswith("MODE-DECLARATION-REF") and normalized_ref(ref.text))
        overlap = sorted(mode_refs & disabled_refs)
        if overlap:
            report.fail(index, event, "SwcModeSwitchEvent references the same ModeDeclaration as mode and disabledMode", references=overlap)
    return report


@plugin("port_api_take_address_single_instance")
def port_api_take_address_single_instance(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for option in selected:
        enabled = _first(option, "ENABLE-TAKE-ADDRESS")
        if enabled is None or _text(enabled).lower() not in TRUE_VALUES:
            continue
        behavior = index.nearest(option, {"SWC-INTERNAL-BEHAVIOR"})
        if behavior is None:
            report.incomplete(f"PORT-API-OPTION has no owning SWC-INTERNAL-BEHAVIOR at {index.location(option)}")
            continue
        multiple = _first(behavior, "SUPPORTS-MULTIPLE-INSTANTIATION")
        if multiple is None:
            report.incomplete(f"missing SUPPORTS-MULTIPLE-INSTANTIATION at {index.location(behavior)}")
        elif _text(multiple).lower() in TRUE_VALUES:
            report.fail(index, option, "enableTakeAddress=true is permitted only for single-instantiation software components")
    return report


@plugin("static_memory_single_instance")
def static_memory_single_instance(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for behavior in selected:
        static_wrapper = _first(behavior, "STATIC-MEMORYS")
        if static_wrapper is None:
            static_wrapper = _first(behavior, "STATIC-MEMORIES")
        if static_wrapper is None:
            continue
        multiple = _first(behavior, "SUPPORTS-MULTIPLE-INSTANTIATION")
        if multiple is None:
            report.incomplete(f"missing SUPPORTS-MULTIPLE-INSTANTIATION at {index.location(behavior)}")
        elif _text(multiple).lower() in TRUE_VALUES:
            report.fail(index, static_wrapper, "staticMemory is supported only when supportsMultipleInstantiation=false")
    return report


@plugin("nv_dataset_reliability")
def nv_dataset_reliability(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for needs in selected:
        count_element = _first(needs, "N-DATA-SETS")
        reliability = _first(needs, "RELIABILITY")
        if count_element is None or reliability is None:
            continue
        try:
            positive = Decimal(_text(count_element)) > 0
        except InvalidOperation:
            report.incomplete(f"invalid N-DATA-SETS at {index.location(count_element)}")
            continue
        if positive and _text(reliability).upper() == "ERROR-CORRECTION":
            report.fail(index, reliability, "reliability=errorCorrection is forbidden when nDataSets > 0")
    return report


def _store_cyclic_enabled(needs: etree._Element) -> bool:
    value = _first(needs, "STORE-CYCLIC")
    return value is not None and _text(value).lower() in TRUE_VALUES


@plugin("nv_cyclic_period_iff")
def nv_cyclic_period_iff(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for needs in selected:
        enabled = _store_cyclic_enabled(needs)
        period = _first(needs, "CYCLIC-WRITING-PERIOD")
        if enabled != (period is not None):
            report.fail(index, period if period is not None else needs, "cyclicWritingPeriod shall exist iff storeCyclic=true", store_cyclic=enabled, period_exists=period is not None)
    return report


@plugin("nv_timing_event_iff")
def nv_timing_event_iff(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for descriptor in selected:
        needs = _first(descriptor, "NV-BLOCK-NEEDS")
        if needs is None:
            report.incomplete(f"NV-BLOCK-DESCRIPTOR lacks NV-BLOCK-NEEDS at {index.location(descriptor)}")
            continue
        enabled = _store_cyclic_enabled(needs)
        timing = _first(descriptor, "TIMING-EVENT-REF")
        if enabled != (timing is not None):
            report.fail(index, timing if timing is not None else descriptor, "timingEvent shall exist iff storeCyclic=true", store_cyclic=enabled, timing_event_exists=timing is not None)
    return report


@plugin("rpt_system_category")
def rpt_system_category(index: ArxmlIndex, rule: dict, selected: list[etree._Element]) -> PluginReport:
    report = PluginReport(checked=len(selected))
    for scenario in selected:
        ref = _first(scenario, "RPT-SYSTEM-REF")
        if ref is None:
            report.incomplete(f"missing RPT-SYSTEM-REF at {index.location(scenario)}")
            continue
        system = _resolve(index, ref, report)
        if system is None:
            continue
        category = _first(system, "CATEGORY")
        if category is None:
            report.incomplete(f"referenced SYSTEM lacks CATEGORY at {index.location(system)}")
        elif _text(category).upper() != "RPT-SYSTEM":
            report.fail(index, category, "rptSystem must reference a System of category RPT_SYSTEM", actual=_text(category))
    return report
