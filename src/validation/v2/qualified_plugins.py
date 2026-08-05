"""Rule-level validators qualified from complete AUTOSAR source assertions.

The functions in this module intentionally use closed operations over parsed
ARXML.  The rational-formula rule is the narrow case where SMT is appropriate:
the denominator is a finite, grounded polynomial over an explicit interval.
Missing bounds, values, or reference context never become a successful check.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from lxml import etree
from z3 import Q, Real, Solver, sat, unknown

from .arxml_index import ArxmlIndex, local_name
from .plugins import PluginReport, plugin


def _children(element: etree._Element, tag: str) -> list[etree._Element]:
    return [child for child in element if isinstance(child.tag, str) and local_name(child.tag) == tag]


def _first(element: etree._Element, tag: str) -> etree._Element | None:
    return next(
        (child for child in element.iterdescendants() if local_name(child.tag) == tag),
        None,
    )


def _text(element: etree._Element | None) -> str:
    return (element.text or "").strip() if element is not None else ""


def _repair(action: str, target: str, instruction: str, **values: object) -> dict:
    return {"action": action, "target": target, "instruction": instruction, **values}


@plugin("application_error_code_range")
def application_error_code_range(
    index: ArxmlIndex,
    rule: dict,
    selected: list[etree._Element],
) -> PluginReport:
    """constr_1108: 1..63, plus zero only for the E_OK ApplicationError."""

    report = PluginReport(checked=len(selected))
    for error in selected:
        code_element = _first(error, "ERROR-CODE")
        if code_element is None:
            report.incomplete(f"missing ERROR-CODE at {index.location(error)}")
            continue
        raw = _text(code_element)
        try:
            code = int(raw, 10)
        except ValueError:
            report.fail(
                index,
                code_element,
                "ApplicationError.errorCode must be an integer in its permitted range",
                actual=raw,
                repair=_repair("replace_value", "ERROR-CODE", "Use an integer from 1 through 63, or 0 only for E_OK."),
            )
            continue
        short_name = _text(_first(error, "SHORT-NAME"))
        allowed = 1 <= code <= 63 or (code == 0 and short_name == "E_OK")
        if not allowed:
            report.fail(
                index,
                code_element,
                "ApplicationError.errorCode is outside 1..63; zero is reserved for E_OK",
                actual=code,
                application_error=short_name or None,
                expected={"range": [1, 63], "zero_allowed_for": "E_OK"},
                repair=_repair("replace_value", "ERROR-CODE", "Choose 1..63, unless this ApplicationError is E_OK."),
            )
    return report


def _decimal_q(value: str):
    decimal = Decimal(value)
    numerator, denominator = decimal.as_integer_ratio()
    return Q(numerator, denominator)


def _interval_bound(
    scale: etree._Element,
    tag: str,
    report: PluginReport,
    index: ArxmlIndex,
):
    element = _first(scale, tag)
    if element is None:
        return None
    raw = _text(element)
    if raw in {"INF", "+INF", "-INF"}:
        return None
    try:
        value = _decimal_q(raw)
    except (InvalidOperation, ValueError):
        report.incomplete(f"unbound or non-numeric {tag} at {index.location(element)}")
        return "invalid"
    interval_type = str(element.get("INTERVAL-TYPE") or "CLOSED").upper()
    if interval_type not in {"OPEN", "CLOSED"}:
        report.incomplete(f"unsupported INTERVAL-TYPE {interval_type!r} at {index.location(element)}")
        return "invalid"
    return value, interval_type


@plugin("rational_formula_denominator_nonzero")
def rational_formula_denominator_nonzero(
    index: ArxmlIndex,
    rule: dict,
    selected: list[etree._Element],
) -> PluginReport:
    """constr_1025: prove the grounded denominator has no root in its scale."""

    report = PluginReport(checked=len(selected))
    for number, coeffs in enumerate(selected):
        denominator = _first(coeffs, "COMPU-DENOMINATOR")
        if denominator is None:
            report.incomplete(f"missing COMPU-DENOMINATOR at {index.location(coeffs)}")
            continue
        values = _children(denominator, "V")
        if not values:
            report.incomplete(f"missing denominator coefficients at {index.location(denominator)}")
            continue
        try:
            coefficients = [_decimal_q(_text(item)) for item in values]
        except (InvalidOperation, ValueError):
            report.incomplete(f"unbound denominator coefficient at {index.location(denominator)}")
            continue
        scale = index.nearest(coeffs, {"COMPU-SCALE"})
        if scale is None:
            report.incomplete(f"COMPU-RATIONAL-COEFFS has no owning COMPU-SCALE at {index.location(coeffs)}")
            continue
        lower = _interval_bound(scale, "LOWER-LIMIT", report, index)
        upper = _interval_bound(scale, "UPPER-LIMIT", report, index)
        if lower == "invalid" or upper == "invalid":
            continue
        variable = Real(f"compu_x_{number}")
        # Build powers by multiplication. Z3's real ``x ** 0`` remains an
        # uninterpreted power term and can make the constant case spuriously
        # satisfiable; an explicit Horner-style power sequence is exact.
        polynomial, power = Q(0, 1), Q(1, 1)
        for coefficient in coefficients:
            polynomial, power = polynomial + coefficient * power, power * variable
        solver = Solver()
        solver.add(polynomial == 0)
        if lower is not None:
            bound, interval_type = lower
            solver.add(variable > bound if interval_type == "OPEN" else variable >= bound)
        if upper is not None:
            bound, interval_type = upper
            solver.add(variable < bound if interval_type == "OPEN" else variable <= bound)
        outcome = solver.check()
        if outcome == unknown:
            report.incomplete(f"SMT solver returned unknown for {index.location(denominator)}")
        elif outcome == sat:
            root = str(solver.model().eval(variable, model_completion=True))
            report.fail(
                index,
                denominator,
                "Compu rational denominator can evaluate to zero within the applicable interval",
                coefficients=[_text(item) for item in values],
                counterexample=root,
                repair=_repair(
                    "replace_formula_coefficients",
                    "COMPU-DENOMINATOR",
                    "Change the denominator coefficients or interval so no permitted input makes it zero.",
                ),
            )
    return report


@plugin("compu_symbol_ranges_consistent")
def compu_symbol_ranges_consistent(
    index: ArxmlIndex,
    rule: dict,
    selected: list[etree._Element],
) -> PluginReport:
    """constr_1133: equal CompuScale symbols imply equal closed/open ranges."""

    report = PluginReport(checked=len(selected))
    for method in selected:
        first_by_symbol: dict[str, tuple[tuple[str | None, str, str | None, str], etree._Element]] = {}
        for scale in (item for item in method.iterdescendants() if local_name(item.tag) == "COMPU-SCALE"):
            symbol = _text(_first(scale, "SYMBOL"))
            if not symbol:
                continue
            lower = _first(scale, "LOWER-LIMIT")
            upper = _first(scale, "UPPER-LIMIT")
            range_key = (
                _text(lower) if lower is not None else None,
                str(lower.get("INTERVAL-TYPE") or "CLOSED") if lower is not None else "MISSING",
                _text(upper) if upper is not None else None,
                str(upper.get("INTERVAL-TYPE") or "CLOSED") if upper is not None else "MISSING",
            )
            previous = first_by_symbol.get(symbol)
            if previous is None:
                first_by_symbol[symbol] = (range_key, scale)
            elif previous[0] != range_key:
                report.fail(
                    index,
                    scale,
                    "CompuScales with the same SYMBOL must define the same range",
                    symbol=symbol,
                    expected_range=previous[0],
                    actual_range=range_key,
                    first=index.location(previous[1]),
                    repair=_repair("align_range", "LOWER-LIMIT/UPPER-LIMIT", f"Make the range for symbol {symbol} identical in every CompuScale."),
                )
    return report


ALLOWED_INDEX_CONTEXTS = {
    "AUTOSAR-PARAMETER-REF",
    "AUTOSAR-VARIABLE-REF",
    "ANY-INSTANCE-REF",
    "FLAT-INSTANCE-DESCRIPTOR",
    "INSTANCE-IN-MEMORY",
}


@plugin("reference_index_context")
def reference_index_context(
    index: ArxmlIndex,
    rule: dict,
    selected: list[etree._Element],
) -> PluginReport:
    """constr_1161: INDEX on Ref is restricted to the enumerated use cases."""

    report = PluginReport(checked=0)
    for root in index.roots:
        for element in root.iter():
            if not isinstance(element.tag, str) or element.get("INDEX") is None:
                continue
            report.checked += 1
            current: etree._Element | None = element
            context: list[str] = []
            while current is not None:
                context.append(local_name(current.tag))
                current = index.parent.get(current)
            if not ALLOWED_INDEX_CONTEXTS.intersection(context):
                report.fail(
                    index,
                    element,
                    "Ref.INDEX is used outside its permitted AUTOSAR reference contexts",
                    actual_context=context[:8],
                    allowed_contexts=sorted(ALLOWED_INDEX_CONTEXTS),
                    repair=_repair("remove_attribute", "@INDEX", "Remove INDEX or use it only in an allowed reference use case."),
                )
    return report


FUNCTION_POINTER = re.compile(
    r"\(\s*\*[^()]*\)\s*\(",
    re.DOTALL,
)


@plugin("per_instance_memory_no_function_pointer")
def per_instance_memory_no_function_pointer(
    index: ArxmlIndex,
    rule: dict,
    selected: list[etree._Element],
) -> PluginReport:
    """TPS_SWCT_01574: reject C function-pointer declarators."""

    report = PluginReport(checked=len(selected))
    for memory in selected:
        definition = _first(memory, "TYPE-DEFINITION")
        if definition is None:
            report.incomplete(f"missing TYPE-DEFINITION at {index.location(memory)}")
        elif FUNCTION_POINTER.search(_text(definition)):
            report.fail(
                index,
                definition,
                "PerInstanceMemory.typeDefinition must not contain a function pointer",
                actual=_text(definition),
                repair=_repair("replace_value", "TYPE-DEFINITION", "Replace the function-pointer typedef with a supported object type."),
            )
    return report


@plugin("pointer_to_pointer_forbidden")
def pointer_to_pointer_forbidden(
    index: ArxmlIndex,
    rule: dict,
    selected: list[etree._Element],
) -> PluginReport:
    """constr_1254: reject nested DATA_REFERENCE pointer target properties."""

    report = PluginReport(checked=len(selected))
    for data_type in selected:
        if _text(_first(data_type, "CATEGORY")) != "DATA_REFERENCE":
            continue
        pointers = [
            item for item in data_type.iterdescendants()
            if local_name(item.tag) == "SW-POINTER-TARGET-PROPS"
        ]
        for outer in pointers:
            if _text(_first(outer, "TARGET-CATEGORY")) != "DATA_REFERENCE":
                continue
            nested = next(
                (item for item in outer.iterdescendants() if local_name(item.tag) == "SW-POINTER-TARGET-PROPS"),
                None,
            )
            if nested is not None:
                report.fail(
                    index,
                    nested,
                    "AUTOSAR does not support an ImplementationDataType pointer to a pointer",
                    outer=index.location(outer),
                    repair=_repair("remove_nested_pointer", "SW-POINTER-TARGET-PROPS", "Replace the nested pointer target with a non-DATA_REFERENCE target type."),
                )
    return report


@plugin("compu_both_domains_have_limits")
def compu_both_domains_have_limits(
    index: ArxmlIndex,
    rule: dict,
    selected: list[etree._Element],
) -> PluginReport:
    """constr_1022: both serialized conversion domains require explicit limits."""

    report = PluginReport(checked=len(selected))
    for method in selected:
        directions = {
            tag: _first(method, tag)
            for tag in ("COMPU-INTERNAL-TO-PHYS", "COMPU-PHYS-TO-INTERNAL")
        }
        if any(value is None for value in directions.values()):
            continue
        for tag, direction in directions.items():
            scales = [
                item for item in direction.iterdescendants()
                if local_name(item.tag) == "COMPU-SCALE"
            ]
            if not scales:
                report.fail(
                    index,
                    direction,
                    f"{tag} must define explicitly bounded CompuScales when both domains exist",
                    repair=_repair("insert", f"{tag}/COMPU-SCALES/COMPU-SCALE", "Add an explicitly bounded CompuScale."),
                )
            for scale in scales:
                missing = [name for name in ("LOWER-LIMIT", "UPPER-LIMIT") if _first(scale, name) is None]
                if missing:
                    report.fail(
                        index,
                        scale,
                        f"{tag} CompuScale is missing explicit limits",
                        missing=missing,
                        repair=_repair("insert", missing[0], "Define both LOWER-LIMIT and UPPER-LIMIT."),
                    )
    return report


VARIABLE_ACCESS_SCOPE_WRAPPERS = {
    "DATA-READ-ACCESSS",
    "DATA-WRITE-ACCESSS",
    "DATA-SEND-POINTS",
    "DATA-RECEIVE-POINT-BY-VALUES",
    "DATA-RECEIVE-POINT-BY-ARGUMENTS",
}


@plugin("variable_access_scope_context")
def variable_access_scope_context(
    index: ArxmlIndex,
    rule: dict,
    selected: list[etree._Element],
) -> PluginReport:
    """constr_1141: SCOPE is legal only in the five named aggregation roles."""

    report = PluginReport(checked=len(selected))
    for access in selected:
        scope = _first(access, "SCOPE")
        if scope is None:
            continue
        current = index.parent.get(access)
        ancestors: list[str] = []
        while current is not None:
            ancestors.append(local_name(current.tag))
            current = index.parent.get(current)
        if not VARIABLE_ACCESS_SCOPE_WRAPPERS.intersection(ancestors):
            report.fail(
                index,
                scope,
                "VariableAccess.scope is used outside an allowed aggregation role",
                actual_context=ancestors[:8],
                allowed_contexts=sorted(VARIABLE_ACCESS_SCOPE_WRAPPERS),
                repair=_repair("remove", "SCOPE", "Remove SCOPE or move the VariableAccess to an allowed role."),
            )
    return report


def _resolve(index: ArxmlIndex, ref: etree._Element, report: PluginReport) -> etree._Element | None:
    resolution = index.resolve(ref)
    if resolution.status != "resolved":
        report.incomplete(f"{resolution.status} reference {resolution.reference} at {index.location(ref)}")
        return None
    return resolution.element


@plugin("autosar_parameter_variable_context")
def autosar_parameter_variable_context(
    index: ArxmlIndex,
    rule: dict,
    selected: list[etree._Element],
) -> PluginReport:
    """constr_1173: a variable target is legal only below SwAxisGrouped."""

    report = PluginReport(checked=len(selected))
    for parameter_ref in selected:
        target_ref = _first(parameter_ref, "TARGET-DATA-PROTOTYPE-REF")
        if target_ref is None:
            continue
        target = _resolve(index, target_ref, report)
        if target is None or local_name(target.tag) != "VARIABLE-DATA-PROTOTYPE":
            continue
        if index.nearest(parameter_ref, {"SW-AXIS-GROUPED"}) is None:
            report.fail(
                index,
                target_ref,
                "AutosarParameterRef may target VariableDataPrototype only in SwAxisGrouped",
                resolved_target=index.location(target),
                repair=_repair("repair_reference", "TARGET-DATA-PROTOTYPE-REF", "Reference a ParameterDataPrototype or move this reference into SwAxisGrouped."),
            )
    return report


NV_MAPPING_PORT_KIND = {
    "WRITTEN-NV-DATA": "R-PORT-PROTOTYPE",
    "WRITTEN-READ-NV-DATA": "PR-PORT-PROTOTYPE",
    "READ-NV-DATA": "P-PORT-PROTOTYPE",
}


@plugin("nv_mapping_port_role")
def nv_mapping_port_role(
    index: ArxmlIndex,
    rule: dict,
    selected: list[etree._Element],
) -> PluginReport:
    """constr_1285: each NvBlockDataMapping role fixes the port kind."""

    report = PluginReport(checked=len(selected))
    for mapping in selected:
        for role_tag, expected_tag in NV_MAPPING_PORT_KIND.items():
            for role in _children(mapping, role_tag):
                port_ref = next(
                    (item for item in role.iterdescendants() if "PORT-PROTOTYPE-REF" in local_name(item.tag)),
                    None,
                )
                if port_ref is None:
                    report.incomplete(f"{role_tag} lacks PORT-PROTOTYPE-REF at {index.location(role)}")
                    continue
                port = _resolve(index, port_ref, report)
                if port is not None and local_name(port.tag) != expected_tag:
                    report.fail(
                        index,
                        port_ref,
                        f"{role_tag} requires a {expected_tag}",
                        actual=local_name(port.tag),
                        expected=expected_tag,
                        repair=_repair("repair_reference", local_name(port_ref.tag), f"Reference a {expected_tag}."),
                    )
    return report


@plugin("core_local_init_policy")
def core_local_init_policy(
    index: ArxmlIndex,
    rule: dict,
    selected: list[etree._Element],
) -> PluginReport:
    """constr_1402: coreLocal memory requires INIT or CLEARED policy."""

    report = PluginReport(checked=len(selected))
    for subject in selected:
        options = [_text(item) for item in subject.iterdescendants() if local_name(item.tag) == "OPTION"]
        if "coreLocal" not in options:
            continue
        method = subject
        if local_name(subject.tag) == "MEMORY-SECTION":
            ref = _first(subject, "SW-ADDR-METHOD-REF")
            if ref is None:
                report.incomplete(f"coreLocal MEMORY-SECTION lacks SW-ADDR-METHOD-REF at {index.location(subject)}")
                continue
            method = _resolve(index, ref, report)
            if method is None:
                continue
        policy = _first(method, "SECTION-INITIALIZATION-POLICY")
        actual = _text(policy)
        if actual not in {"INIT", "CLEARED"}:
            report.fail(
                index,
                policy if policy is not None else method,
                "coreLocal requires sectionInitializationPolicy INIT or CLEARED",
                actual=actual or None,
                allowed=["CLEARED", "INIT"],
                repair=_repair("replace_value", "SECTION-INITIALIZATION-POLICY", "Set the policy to INIT or CLEARED."),
            )
    return report
