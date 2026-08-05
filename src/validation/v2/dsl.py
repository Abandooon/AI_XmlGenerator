"""Typed, closed-world DSL executor for deterministic ARXML checks.

The DSL is intentionally a small JSON AST.  It does not evaluate Python,
XPath, SPARQL, or arbitrary strings.  Unsupported operators and malformed
specifications are errors; they never become a successful validation result.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any

from lxml import etree

from .arxml_index import ArxmlIndex, local_name
from .plugins import PluginReport, plugin

SUPPORTED_OPERATORS = {
    "exists", "forbidden", "count", "count_matching", "value_domain", "numeric_range",
    "pattern", "mutually_exclusive", "unique", "ordered_before",
    "reference_resolves", "reference_dest_matches", "numeric_modulo",
}


def _segments(path: str | list[str]) -> list[str]:
    if isinstance(path, list):
        values = path
    else:
        values = str(path).split("/")
    return [str(item).strip() for item in values if str(item).strip()]


def _relative_matches(subject: etree._Element, path: str | list[str]) -> list[etree._Element]:
    if path in {".", "$self"}:
        return [subject]
    parts = _segments(path)
    if parts and parts[0] == local_name(subject.tag):
        parts = parts[1:]
    if not parts:
        return [subject]
    current = [subject]
    for part in parts:
        following: list[etree._Element] = []
        for parent in current:
            following.extend(
                child for child in parent
                if isinstance(child.tag, str) and local_name(child.tag) == part
            )
        current = following
        if not current:
            break
    return current


def _values(subject: etree._Element, check: dict[str, Any]) -> list[etree._Element]:
    paths = check.get("paths") or ([check["path"]] if check.get("path") else [])
    values: list[etree._Element] = []
    seen: set[int] = set()
    for path in paths:
        matches = _relative_matches(subject, path)
        if not matches and check.get("search") == "descendant":
            terminal = _segments(path)[-1] if _segments(path) else ""
            matches = [
                item for item in subject.iterdescendants()
                if isinstance(item.tag, str) and local_name(item.tag) == terminal
            ]
        for item in matches:
            if id(item) not in seen:
                seen.add(id(item))
                values.append(item)
    return values


def _text(element: etree._Element) -> str:
    return (element.text or "").strip()


def _ancestors(index: ArxmlIndex, subject: etree._Element) -> list[etree._Element]:
    result: list[etree._Element] = []
    current = index.parent.get(subject)
    while current is not None:
        result.append(current)
        current = index.parent.get(current)
    return result


def _condition_matches(index: ArxmlIndex, subject: etree._Element, condition: dict[str, Any]) -> bool:
    """Evaluate the small, typed antecedent language used by conditional rules."""
    if not condition:
        return True
    if "all" in condition:
        return all(_condition_matches(index, subject, item) for item in condition["all"])
    if "any" in condition:
        return any(_condition_matches(index, subject, item) for item in condition["any"])
    if "not" in condition:
        return not _condition_matches(index, subject, condition["not"])
    if "subject_tags" in condition:
        return local_name(subject.tag) in set(condition["subject_tags"])
    if "ancestor_tags" in condition:
        return any(
            local_name(item.tag) in set(condition["ancestor_tags"])
            for item in _ancestors(index, subject)
        )
    path = condition.get("path")
    if not path:
        raise ValueError(f"Malformed DSL condition: {condition!r}")
    values = _values(subject, condition)
    if "exists" in condition and bool(values) != bool(condition["exists"]):
        return False
    texts = [_text(item) for item in values]
    if not texts and any(key in condition for key in ("equals", "not_equals", "in", "not_in")):
        return False
    if "equals" in condition and str(condition["equals"]) not in texts:
        return False
    if "not_equals" in condition and any(text == str(condition["not_equals"]) for text in texts):
        return False
    if "in" in condition and not any(text in {str(item) for item in condition["in"]} for text in texts):
        return False
    if "not_in" in condition and any(text in {str(item) for item in condition["not_in"]} for text in texts):
        return False
    return True


def _repair(check: dict[str, Any], *, action: str, expected: Any, actual: Any) -> dict[str, Any]:
    configured = dict(check.get("repair") or {})
    return {
        "action": configured.pop("action", action),
        "target": configured.pop("target", check.get("path") or check.get("paths") or ""),
        "expected": configured.pop("expected", expected),
        "actual": configured.pop("actual", actual),
        "instruction": configured.pop(
            "instruction",
            check.get("message") or "Update the indicated ARXML element so that it satisfies the constraint.",
        ),
        **configured,
    }


def _fail(
    report: PluginReport,
    index: ArxmlIndex,
    element: etree._Element,
    check: dict[str, Any],
    message: str,
    *,
    action: str,
    expected: Any,
    actual: Any,
) -> None:
    report.fail(
        index,
        element,
        message,
        repair=_repair(check, action=action, expected=expected, actual=actual),
        dsl_operator=check["op"],
        expected=expected,
        actual=actual,
    )


def _execute_check(
    index: ArxmlIndex,
    subject: etree._Element,
    check: dict[str, Any],
    report: PluginReport,
) -> None:
    op = check.get("op")
    if op not in SUPPORTED_OPERATORS:
        raise ValueError(f"Unsupported Constraint DSL operator: {op!r}")
    if not _condition_matches(index, subject, check.get("when") or {}):
        return
    values = _values(subject, check)
    message = str(check.get("message") or "Constraint is not satisfied")

    if op == "exists":
        if not values:
            _fail(report, index, subject, check, message, action="insert", expected="at least one", actual=0)
        return
    if op == "forbidden":
        for value in values:
            _fail(report, index, value, check, message, action="remove", expected=0, actual=1)
        return
    if op in {"count", "count_matching"}:
        minimum = check.get("min")
        maximum = check.get("max")
        counted = values
        if op == "count_matching":
            allowed = {str(item) for item in check.get("allowed", [])}
            if not allowed:
                raise ValueError("count_matching requires a non-empty allowed set")
            counted = [item for item in values if _text(item) in allowed]
        count = len(counted)
        if (minimum is not None and count < int(minimum)) or (
            maximum is not None and count > int(maximum)
        ):
            _fail(
                report, index, subject, check, message, action="adjust_count",
                expected={"min": minimum, "max": maximum}, actual=count,
            )
        return
    if op == "mutually_exclusive":
        present = [path for path in check.get("paths", []) if _relative_matches(subject, path)]
        minimum = int(check.get("min_present", 0))
        maximum = int(check.get("max_present", 1))
        if len(present) < minimum or len(present) > maximum:
            _fail(
                report, index, subject, check, message, action="choose_alternative",
                expected={"min_present": minimum, "max_present": maximum}, actual=present,
            )
        return
    if op == "unique":
        key_path = check.get("key_path")
        groups: dict[str, list[etree._Element]] = {}
        for value in values:
            keys = _relative_matches(value, key_path) if key_path else [value]
            key = "|".join(_text(item) for item in keys)
            if key:
                groups.setdefault(key, []).append(value)
        for key, duplicates in groups.items():
            for duplicate in duplicates[1:]:
                _fail(
                    report, index, duplicate, check, message, action="make_unique",
                    expected="unique value", actual=key,
                )
        return
    if op == "ordered_before":
        before = _relative_matches(subject, check["before"])
        after = _relative_matches(subject, check["after"])
        children = [child for child in subject if isinstance(child.tag, str)]
        positions = {id(child): number for number, child in enumerate(children)}
        if before and after and max(positions.get(id(item), -1) for item in before) > min(
            positions.get(id(item), len(children)) for item in after
        ):
            _fail(
                report, index, subject, check, message, action="reorder",
                expected=f"{check['before']} before {check['after']}", actual="reversed",
            )
        return

    required = bool(check.get("required", False))
    if required and not values:
        _fail(report, index, subject, check, message, action="insert", expected="value present", actual="missing")
        return
    if not values:
        return

    if op == "value_domain":
        allowed = {str(item) for item in check.get("allowed", [])}
        forbidden = {str(item) for item in check.get("forbidden", [])}
        if not allowed and not forbidden:
            raise ValueError("value_domain requires allowed or forbidden values")
        for value in values:
            actual = _text(value)
            if (allowed and actual not in allowed) or actual in forbidden:
                _fail(
                    report, index, value, check, message, action="replace_value",
                    expected=sorted(allowed) if allowed else {"not": sorted(forbidden)}, actual=actual,
                )
        return
    if op == "numeric_modulo":
        modulus = Decimal(str(check["modulus"]))
        remainder = Decimal(str(check.get("remainder", 0)))
        if modulus == 0:
            raise ValueError("numeric_modulo modulus cannot be zero")
        for value in values:
            actual_text = _text(value)
            try:
                actual = Decimal(actual_text)
            except InvalidOperation:
                _fail(
                    report, index, value, check, message, action="replace_value",
                    expected="numeric value", actual=actual_text,
                )
                continue
            if actual % modulus != remainder:
                _fail(
                    report, index, value, check, message, action="replace_value",
                    expected={"modulus": str(modulus), "remainder": str(remainder)},
                    actual=actual_text,
                )
        return
    if op == "numeric_range":
        minimum = Decimal(str(check["min"])) if check.get("min") is not None else None
        maximum = Decimal(str(check["max"])) if check.get("max") is not None else None
        for value in values:
            actual_text = _text(value)
            try:
                actual = Decimal(actual_text)
            except InvalidOperation:
                _fail(
                    report, index, value, check, message, action="replace_value",
                    expected="numeric value", actual=actual_text,
                )
                continue
            below = minimum is not None and (
                actual <= minimum if check.get("min_exclusive") else actual < minimum
            )
            above = maximum is not None and (
                actual >= maximum if check.get("max_exclusive") else actual > maximum
            )
            if below or above:
                _fail(
                    report, index, value, check, message, action="replace_value",
                    expected={"min": str(minimum) if minimum is not None else None,
                              "max": str(maximum) if maximum is not None else None},
                    actual=actual_text,
                )
        return
    if op == "pattern":
        expression = re.compile(str(check["regex"]))
        for value in values:
            actual = _text(value)
            matched = expression.fullmatch(actual) is not None
            if matched == bool(check.get("forbid_match", False)):
                _fail(
                    report, index, value, check, message, action="replace_value",
                    expected={"regex": expression.pattern,
                              "forbid_match": bool(check.get("forbid_match", False))}, actual=actual,
                )
        return
    if op in {"reference_resolves", "reference_dest_matches"}:
        allowed_dest = {str(item) for item in check.get("allowed_dest", [])}
        for value in values:
            resolution = index.resolve(value)
            if resolution.status != "resolved":
                _fail(
                    report, index, value, check,
                    message or f"Reference {resolution.reference} is {resolution.status}",
                    action="repair_reference", expected="one resolvable target",
                    actual={"status": resolution.status, "reference": resolution.reference},
                )
                continue
            if op == "reference_dest_matches":
                actual_dest = str(value.get("DEST") or "")
                target_tag = local_name(resolution.element.tag) if resolution.element is not None else ""
                if (allowed_dest and actual_dest not in allowed_dest) or (
                    actual_dest and target_tag and actual_dest != target_tag
                ):
                    _fail(
                        report, index, value, check, message, action="replace_dest",
                        expected=sorted(allowed_dest) if allowed_dest else target_tag,
                        actual={"DEST": actual_dest, "resolved_tag": target_tag},
                    )
        return


def validate_spec(spec: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if spec.get("language") != "autosar-constraint-ir/1.0":
        errors.append("language must be autosar-constraint-ir/1.0")
    checks = spec.get("checks")
    if not isinstance(checks, list) or not checks:
        errors.append("checks must be a non-empty array")
        return errors
    for number, check in enumerate(checks, 1):
        if not isinstance(check, dict):
            errors.append(f"check {number} is not an object")
            continue
        if check.get("op") not in SUPPORTED_OPERATORS:
            errors.append(f"check {number} uses unsupported operator {check.get('op')!r}")
        if check.get("op") not in {"mutually_exclusive", "ordered_before"} and not (
            check.get("path") or check.get("paths")
        ):
            errors.append(f"check {number} has no path")
    return errors


@plugin("constraint_dsl")
def constraint_dsl(
    index: ArxmlIndex,
    rule: dict,
    selected: list[etree._Element],
) -> PluginReport:
    spec = rule.get("formal_spec") or {}
    errors = validate_spec(spec)
    if errors:
        raise ValueError("; ".join(errors))
    report = PluginReport(checked=len(selected))
    for subject in selected:
        for check in spec["checks"]:
            _execute_check(index, subject, check, report)
    return report
