"""Normalize validation findings into deterministic LLM repair instructions."""

from __future__ import annotations

from typing import Any


def repair_action(finding: dict[str, Any]) -> dict[str, Any]:
    location = finding.get("location") or {}
    configured = finding.get("repair") or {}
    evidence = finding.get("evidence") or {}
    instruction = configured.get("instruction") or finding.get("message") or "Repair this constraint violation."
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
    }


def build_repair_payload(findings: list[dict[str, Any]]) -> dict[str, Any]:
    actions = [repair_action(item) for item in findings]
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
        "schema_version": "1.0",
        "action_count": len(actions),
        "actions": actions,
        "by_file": grouped,
        "llm_prompt": "\n".join(lines),
    }
