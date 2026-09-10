"""Parsed structural obligations derived from Phase 1 element selections."""

from __future__ import annotations

import hashlib
from dataclasses import replace as dataclass_replace
from typing import Any

from lxml import etree

from src.llm_generation.knowledge.element_selection import (
    ElementSelection,
    ElementSelectionError,
    parse_element_selections,
)
from src.validation.v2.repair import build_repair_payload


# These AUTOSAR elements are singleton grouping elements in the physical XML,
# while their sole repeated child carries the cardinality exposed to the
# provider schema.  ``apply_element_design_to_schema`` already projects a
# Round-1 count onto that child; the post-generation checker must mirror the
# same interpretation instead of demanding several invalid wrapper siblings.
_PROJECTED_OCCURRENCE_CHILD = {
    "DATA-RECEIVE-POINT-BY-ARGUMENTS": "VARIABLE-ACCESS",
    "DATA-SEND-POINTS": "VARIABLE-ACCESS",
}


def _physical_occurrence_selection(selection: ElementSelection) -> ElementSelection:
    if not selection.path or (
        selection.min_occurs <= 1 and selection.max_occurs <= 1
    ):
        return selection
    child = _PROJECTED_OCCURRENCE_CHILD.get(selection.path[-1].upper())
    if child is None:
        return selection
    return dataclass_replace(selection, path=(*selection.path, child))


def _local_name(node: etree._Element) -> str:
    return etree.QName(node).localname


def _direct_children(node: etree._Element, name: str) -> list[etree._Element]:
    return [child for child in node if _local_name(child).upper() == name.upper()]


def _short_name(node: etree._Element) -> str:
    values = _direct_children(node, "SHORT-NAME")
    return (values[0].text or "").strip() if values else ""


def _component_node(root: etree._Element, component_type: str, name: str) -> etree._Element | None:
    for node in root.iter():
        if _local_name(node).upper() != component_type.upper():
            continue
        if _short_name(node) == name:
            return node
    return None


def _selection_values(
    component: etree._Element, selection: ElementSelection
) -> tuple[list[Any], str]:
    nodes: list[etree._Element] = [component]
    anchors = {anchor.path_index: anchor.short_name for anchor in selection.anchors}
    xml_path = [f"{_local_name(component)}[SHORT-NAME={_short_name(component)}]"]
    for index, segment in enumerate(selection.path):
        if segment.startswith("@"):
            if index != len(selection.path) - 1:
                raise ElementSelectionError("attribute selection must be the final path segment")
            attribute = segment[1:]
            return [node.attrib[attribute] for node in nodes if attribute in node.attrib], "/".join(
                [*xml_path, segment]
            )
        if segment == "#TEXT":
            if index != len(selection.path) - 1:
                raise ElementSelectionError("#text selection must be the final path segment")
            return [str(node.text or "").strip() for node in nodes if node.text is not None], "/".join(
                [*xml_path, "#text"]
            )
        children = [child for node in nodes for child in _direct_children(node, segment)]
        if index in anchors:
            children = [child for child in children if _short_name(child) == anchors[index]]
        nodes = children
        anchor_suffix = f"[SHORT-NAME={anchors[index]}]" if index in anchors else ""
        xml_path.append(f"{segment}{anchor_suffix}")
    return nodes, "/".join(xml_path)


def _finding(
    *, component_name: str, selection: ElementSelection, xml_path: str, expected: Any, actual: Any, message: str
) -> dict[str, Any]:
    identity = (
        component_name,
        selection.path,
        tuple((anchor.path_index, anchor.short_name) for anchor in selection.anchors),
        expected,
        actual,
    )
    fingerprint = hashlib.sha256(repr(identity).encode("utf-8")).hexdigest()
    return {
        "fingerprint": fingerprint,
        "constraint_ids": ["ATLAS-PHASE1-ELEMENT-SELECTION"],
        "rule_ids": ["parsed-element-obligation"],
        "severity": "error",
        "message": message,
        "location": {
            "file": f"components/{component_name}.arxml",
            "xml_path": xml_path,
            "tag": selection.path[-1],
        },
        "evidence": {"expected": expected, "actual": actual},
    }


def validate_selection_obligations(
    bundle: dict[str, Any], component_plans: list[dict[str, Any]] | None
) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    evaluated = 0
    incomplete_notes: list[str] = []
    parser = etree.XMLParser(resolve_entities=False, no_network=True, recover=False, huge_tree=True)
    component_documents = bundle.get("components") or {}
    if not isinstance(component_documents, dict):
        return {
            "schema_version": "1.0",
            "decision": "ERROR",
            "evaluated": 0,
            "findings": [],
            "notes": ["bundle.components is not an object"],
        }

    for plan in component_plans or []:
        name = str(plan.get("name") or "")
        component_type = str(plan.get("type") or "")
        element_design = plan.get("element_design")
        if (
            not isinstance(element_design, dict)
            or "selections" not in element_design
            or "unsupported" not in element_design
        ):
            incomplete_notes.append(
                f"component {name!r} has incomplete Phase 1 element selection context"
            )
            continue
        unsupported = element_design.get("unsupported")
        if not isinstance(unsupported, list):
            return {
                "schema_version": "1.0",
                "decision": "ERROR",
                "evaluated": evaluated,
                "findings": findings,
                "notes": [f"component {name!r} element_design.unsupported is not an array"],
            }
        for position, item in enumerate(unsupported):
            if not isinstance(item, dict):
                return {
                    "schema_version": "1.0",
                    "decision": "ERROR",
                    "evaluated": evaluated,
                    "findings": findings,
                    "notes": [
                        f"component {name!r} unsupported[{position}] is not an object"
                    ],
                }
            requirement_id = str(item.get("requirement_id") or "").strip()
            requirement = str(item.get("requirement") or "").strip()
            reason = str(item.get("reason") or "").strip()
            if not requirement_id or not requirement or not reason:
                return {
                    "schema_version": "1.0",
                    "decision": "ERROR",
                    "evaluated": evaluated,
                    "findings": findings,
                    "notes": [
                        f"component {name!r} unsupported[{position}] is incomplete"
                    ],
                }
            incomplete_notes.append(
                f"component {name!r} unsupported requirement {requirement_id}: "
                f"{requirement} ({reason})"
            )
        try:
            selections = parse_element_selections(element_design)
        except ElementSelectionError as error:
            return {
                "schema_version": "1.0",
                "decision": "ERROR",
                "evaluated": evaluated,
                "findings": findings,
                "notes": [str(error)],
            }
        if not selections:
            continue
        xml_text = component_documents.get(name)
        if not isinstance(xml_text, str) or not xml_text.strip():
            findings.append(
                _finding(
                    component_name=name,
                    selection=selections[0],
                    xml_path=component_type,
                    expected="component document",
                    actual="missing",
                    message=f"Selected element obligations cannot be evaluated: component {name!r} is missing.",
                )
            )
            continue
        try:
            root = etree.fromstring(xml_text.encode("utf-8"), parser)
        except etree.XMLSyntaxError as error:
            return {
                "schema_version": "1.0",
                "decision": "ERROR",
                "evaluated": evaluated,
                "findings": findings,
                "notes": [f"component {name!r} is not well-formed XML: {error}"],
            }
        component = _component_node(root, component_type, name)
        if component is None:
            findings.append(
                _finding(
                    component_name=name,
                    selection=selections[0],
                    xml_path=component_type,
                    expected=f"{component_type}/{name}",
                    actual="missing",
                    message=f"Component payload {component_type}/{name} is missing.",
                )
            )
            continue

        for selection in selections:
            evaluated += 1
            occurrence_selection = _physical_occurrence_selection(selection)
            try:
                values, xml_path = _selection_values(
                    component, occurrence_selection
                )
            except ElementSelectionError as error:
                return {
                    "schema_version": "1.0",
                    "decision": "ERROR",
                    "evaluated": evaluated,
                    "findings": findings,
                    "notes": [str(error)],
                }
            count = len(values)
            if (
                count < occurrence_selection.min_occurs
                or count > occurrence_selection.max_occurs
            ):
                findings.append(
                    _finding(
                        component_name=name,
                        selection=occurrence_selection,
                        xml_path=xml_path,
                        expected=(
                            "occurs "
                            f"{occurrence_selection.min_occurs}.."
                            f"{occurrence_selection.max_occurs}"
                        ),
                        actual=count,
                        message=(
                            "Selected AUTOSAR path "
                            f"{'/'.join(occurrence_selection.path)} has occurrence "
                            f"count {count}, expected {occurrence_selection.min_occurs}.."
                            f"{occurrence_selection.max_occurs}."
                        ),
                    )
                )
                continue
            if selection.value_present:
                actual_values = [
                    value if isinstance(value, str) else str(value.text or "").strip()
                    for value in values
                ]
                mismatches = [value for value in actual_values if value != selection.value]
                if mismatches:
                    findings.append(
                        _finding(
                            component_name=name,
                            selection=selection,
                            xml_path=xml_path,
                            expected=selection.value,
                            actual=actual_values,
                            message=(
                                f"Selected AUTOSAR path {'/'.join(selection.path)} has a value "
                                f"different from the exact Phase 1 requirement."
                            ),
                        )
                    )

    if findings:
        decision = "FAIL"
    elif incomplete_notes:
        decision = "NOT_EVALUATED"
    elif evaluated or component_plans:
        decision = "PASS"
    else:
        decision = "NOT_EVALUATED"
    return {
        "schema_version": "1.0",
        "decision": decision,
        "evaluated": evaluated,
        "summary": {"PASS": max(0, evaluated - len(findings)), "FAIL": len(findings)},
        "findings": findings,
        "notes": incomplete_notes,
    }


def merge_selection_obligations(
    validation_report: dict[str, Any] | None, obligation_report: dict[str, Any]
) -> dict[str, Any]:
    report = dict(validation_report or {})
    report["selection_obligations"] = obligation_report
    obligation_decision = obligation_report.get("decision")
    artifact_profile = dict(report.get("artifact_profile") or {})
    if artifact_profile:
        # Preserve the independent validator result before adding the
        # model-plan self-consistency diagnostic.  External promotion gates can
        # then use XSD/TPS/constraint evidence without circularly treating the
        # model-authored selection plan as its own requirement oracle.
        artifact_profile.setdefault(
            "independent_decision", artifact_profile.get("decision")
        )
        artifact_profile.setdefault(
            "independent_valid", artifact_profile.get("valid")
        )
        artifact_profile["selection_obligation_decision"] = obligation_decision
        profile_decision = str(
            artifact_profile.get("decision") or "NOT_EVALUATED"
        ).upper()
        if obligation_decision == "ERROR" or profile_decision == "ERROR":
            artifact_profile["decision"] = "ERROR"
            artifact_profile["valid"] = False
        elif obligation_decision == "FAIL" or profile_decision == "FAIL":
            artifact_profile["decision"] = "FAIL"
            artifact_profile["valid"] = False
        elif obligation_decision != "PASS" or profile_decision != "PASS":
            artifact_profile["decision"] = "INCOMPLETE"
            artifact_profile["valid"] = False
        else:
            artifact_profile["decision"] = "PASS"
            artifact_profile["valid"] = True
        report["artifact_profile"] = artifact_profile
    if validation_report:
        report.setdefault("independent_decision", report.get("decision"))
        report.setdefault("independent_valid", report.get("valid"))
    if not validation_report:
        notes = ["V2 validation report is unavailable"]
        notes.extend(obligation_report.get("notes") or [])
        report.update(
            {
                "decision": "INCOMPLETE",
                "valid": None,
                "summary": dict(obligation_report.get("summary") or {}),
                "findings": [],
                "notes": notes,
            }
        )
    elif obligation_decision == "NOT_EVALUATED":
        existing_decision = str(report.get("decision") or "NOT_EVALUATED").upper()
        if existing_decision not in {"ERROR", "FAIL"}:
            report["decision"] = "INCOMPLETE"
            report["valid"] = None
        notes = list(report.get("notes") or [])
        notes.extend(obligation_report.get("notes") or [])
        report["notes"] = notes
    if obligation_decision in {"FAIL", "ERROR"}:
        existing_decision = str(report.get("decision") or "NOT_EVALUATED").upper()
        report["decision"] = (
            "ERROR"
            if "ERROR" in {existing_decision, obligation_decision}
            else "FAIL"
        )
        report["valid"] = False
        findings = list(report.get("findings") or [])
        findings.extend(obligation_report.get("findings") or [])
        report["findings"] = findings
        summary = dict(report.get("summary") or {})
        if obligation_decision == "FAIL":
            summary["FAIL"] = int(summary.get("FAIL") or 0) + int(
                (obligation_report.get("summary") or {}).get("FAIL") or 0
            )
        else:
            summary["ERROR"] = int(summary.get("ERROR") or 0) + 1
        summary["finding_count"] = len(findings)
        report["summary"] = summary
        report["repair"] = build_repair_payload(findings, report.get("rules"))
    return report


def generation_status_from_validation(decision: object) -> str:
    """Map validation decisions without turning incomplete work into success."""
    normalized = str(decision or "NOT_EVALUATED").strip().upper()
    if normalized == "PASS":
        return "success"
    if normalized in {"FAIL", "ERROR"}:
        return "generated_with_validation_errors"
    return "generated_with_incomplete_validation"
