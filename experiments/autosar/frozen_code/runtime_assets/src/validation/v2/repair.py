"""Normalize validation findings into deterministic LLM repair instructions."""

from __future__ import annotations

from typing import Any


def _dependency_ids(value: Any) -> tuple[str, ...]:
    """Normalize dependency records without inventing rule-family ordering."""
    result: list[str] = []
    for item in value if isinstance(value, list) else []:
        if isinstance(item, str) and item:
            result.append(item)
            continue
        if isinstance(item, dict):
            dependency = str(
                item.get("rule_id") or item.get("constraint_id") or ""
            ).strip()
            if dependency:
                result.append(dependency)
    return tuple(dict.fromkeys(result))


def _rule_index(rule_results: Any) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in rule_results if isinstance(rule_results, list) else []:
        if not isinstance(item, dict):
            continue
        rule_id = str(item.get("rule_id") or "").strip()
        if rule_id:
            result[rule_id] = item
    return result


def repair_action(
    finding: dict[str, Any], rule_index: dict[str, dict[str, Any]] | None = None
) -> dict[str, Any]:
    location = finding.get("location") or {}
    configured = finding.get("repair") or {}
    evidence = finding.get("evidence") or {}
    instruction = configured.get("instruction") or finding.get("message") or "Repair this constraint violation."
    matched_rules = [
        (rule_index or {}).get(str(rule_id))
        for rule_id in (finding.get("rule_ids") or [])
    ]
    matched_rules = [item for item in matched_rules if isinstance(item, dict)]
    dependencies = tuple(dict.fromkeys(
        dependency
        for rule in matched_rules
        for dependency in _dependency_ids(rule.get("dependencies"))
    ))
    required_capabilities = tuple(dict.fromkeys(
        str(capability)
        for rule in matched_rules
        for capability in (rule.get("completeness_requires") or [])
        if str(capability)
    ))
    return {
        "finding_fingerprint": finding.get("fingerprint", ""),
        "constraint_ids": list(finding.get("constraint_ids") or []),
        "rule_ids": list(finding.get("rule_ids") or []),
        "severity": finding.get("severity", "error"),
        "file": location.get("file"),
        "line": location.get("line"),
        "xml_path": location.get("xml_path"),
        "tag": location.get("tag"),
        "action": configured.get("action", "edit"),
        "target": configured.get("target") or location.get("xml_path"),
        "expected": configured.get("expected", evidence.get("expected")),
        "actual": configured.get("actual", evidence.get("actual")),
        "instruction": instruction,
        "message": finding.get("message", ""),
        "depends_on_rule_ids": list(dependencies),
        "required_capabilities": list(required_capabilities),
    }


def _dependency_order(
    actions: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Stable topological order over the ordering constraints the data supports.

    Two edge sources are used and no others.  Rule-to-rule ``dependencies`` are
    honoured when a rule declares them; a rule whose completeness requires
    ``well_formed_xml`` is ordered after the XML/XSD findings that would make the
    document parseable.  No rule-family ordering is assumed: the family chain in
    the review plan is not derivable from the current rule set, and inventing it
    would misreport the basis of the repair order.  The returned audit states how
    many edges each source actually contributed.
    """
    rule_positions: dict[str, set[int]] = {}
    for position, action in enumerate(actions):
        for rule_id in action.get("rule_ids") or []:
            rule_positions.setdefault(str(rule_id), set()).add(position)
        for constraint_id in action.get("constraint_ids") or []:
            rule_positions.setdefault(str(constraint_id), set()).add(position)

    prerequisites: dict[int, set[int]] = {
        position: set() for position in range(len(actions))
    }
    xml_positions = {
        position
        for position, action in enumerate(actions)
        if {str(item).upper() for item in action.get("constraint_ids") or []}
        & {"XML", "XSD"}
    }
    declared_edges = 0
    well_formedness_edges = 0
    for position, action in enumerate(actions):
        for dependency in action.get("depends_on_rule_ids") or []:
            matched = rule_positions.get(str(dependency), set()) - {position}
            declared_edges += len(matched)
            prerequisites[position].update(matched)
        if "well_formed_xml" in set(action.get("required_capabilities") or []):
            matched = xml_positions - {position}
            well_formedness_edges += len(matched)
            prerequisites[position].update(matched)
        prerequisites[position].discard(position)

    audit: dict[str, Any] = {
        "strategy": "declared_rule_dependency_and_well_formedness_topological_sort",
        "declared_rule_dependency_edges": declared_edges,
        "well_formedness_prerequisite_edges": well_formedness_edges,
        "rule_family_ordering_assumed": False,
        "dependency_cycle_detected": False,
    }
    ordered_positions: list[int] = []
    remaining = set(range(len(actions)))
    while remaining:
        ready = sorted(
            position
            for position in remaining
            if not (prerequisites[position] & remaining)
        )
        if not ready:
            ordered_positions.extend(sorted(remaining))
            audit["dependency_cycle_detected"] = True
            return [actions[position] for position in ordered_positions], audit
        ordered_positions.extend(ready)
        remaining.difference_update(ready)
    return [actions[position] for position in ordered_positions], audit


def build_repair_payload(
    findings: list[dict[str, Any]], rule_results: Any = None
) -> dict[str, Any]:
    rules = _rule_index(rule_results)
    actions, ordering_audit = _dependency_order(
        [repair_action(item, rules) for item in findings]
    )
    grouped: dict[str, list[dict[str, Any]]] = {}
    for action in actions:
        grouped.setdefault(str(action.get("file") or "<bundle>"), []).append(action)
    lines = [
        "Repair every ARXML validation finding listed below.",
        "Preserve unrelated content, AUTOSAR namespaces, SHORT-NAME identity, references, and XSD element order.",
        "Do not stop after the first edit. Apply all non-conflicting actions, then run validation again.",
    ]
    for file_name, file_actions in grouped.items():
        lines.append(f"\nFILE: {file_name}")
        for number, action in enumerate(file_actions, 1):
            where = action.get("xml_path") or action.get("tag") or "unknown XML location"
            line = action.get("line")
            lines.append(
                f"{number}. [{','.join(action['constraint_ids']) or 'XSD'}] "
                f"{where}{f' line {line}' if line else ''}: {action['instruction']} "
                f"Expected={action.get('expected')!r}; actual={action.get('actual')!r}."
            )
    return {
        "schema_version": "1.1",
        "action_count": len(actions),
        "actions": actions,
        "by_file": grouped,
        "llm_prompt": "\n".join(lines),
        "ordering": ordering_audit,
    }
