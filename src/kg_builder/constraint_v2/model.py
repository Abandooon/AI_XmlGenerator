"""Build a deterministic, Neo4j-safe projection from the V2 artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from src.llm_generation.knowledge.v2.dataset import (
    canonical_json,
    load_and_validate_manifest,
)


def _semantic_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _section_id(path: list[str]) -> str:
    digest = hashlib.sha256(canonical_json(path).encode("utf-8")).hexdigest()[:24]
    return f"doc:section:v2/{digest}"


def _constraint_entity_id(constraint_id: str) -> str:
    return f"autosar:4-2-2/constr/{constraint_id}"


def _target_entity_id(constraint_id: str, index: int) -> str:
    return f"autosar:4-2-2/constr-target-v2/{constraint_id}/{index}"


def _rule_entity_id(rule_id: str) -> str:
    return f"autosar:4-2-2/validation-rule-v2/{rule_id}"


def _load_constraints(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    records = payload if isinstance(payload, list) else payload.get("constraints", [])
    if not isinstance(records, list):
        raise ValueError("constraints_v2 must contain a JSON array")
    return records


def build_projection(
    *,
    constraints_path: str | Path,
    cards_path: str | Path,
    retrieval_manifest_path: str | Path,
    validation_plan_path: str | Path,
    validator_manifest_path: str | Path | None = None,
) -> dict[str, Any]:
    constraints = _load_constraints(Path(constraints_path))
    cards, retrieval_manifest = load_and_validate_manifest(cards_path, retrieval_manifest_path)
    plan = json.loads(Path(validation_plan_path).read_text(encoding="utf-8-sig"))
    rules = list(plan.get("rules") or [])
    manual_reviews = list((plan.get("manual_review") or {}).get("reviews") or [])
    validator_sha256 = ""
    if validator_manifest_path is not None:
        from src.validation.v2.implementation_manifest import validate_manifest
        validator_manifest = validate_manifest(
            Path(validator_manifest_path),
            plan_path=Path(validation_plan_path),
            dataset_manifest_path=Path(retrieval_manifest_path),
        )
        validator_sha256 = str(validator_manifest["validator_sha256"])
    manual_by_id = {str(item["constraint_id"]): item for item in manual_reviews}
    if len(manual_by_id) != len(manual_reviews):
        raise ValueError("manual review plan contains duplicate constraint ids")

    constraint_by_id = {str(item["id"]): item for item in constraints}
    card_by_id = {str(item["constraint_id"]): item for item in cards}
    if len(constraint_by_id) != len(constraints):
        raise ValueError("constraints_v2 contains duplicate ids")
    if len(card_by_id) != len(cards):
        raise ValueError("retrieval cards contain duplicate constraint ids")
    if set(constraint_by_id) != set(card_by_id):
        raise ValueError("structured constraints and retrieval cards have different id sets")

    rules_by_constraint: dict[str, list[dict]] = {}
    for rule in rules:
        rules_by_constraint.setdefault(str(rule["constraint_id"]), []).append(rule)
    unknown_rule_ids = set(rules_by_constraint) - set(constraint_by_id)
    if unknown_rule_ids:
        raise ValueError(f"validation plan contains unknown constraints: {sorted(unknown_rule_ids)[:20]}")
    unknown_manual_ids = set(manual_by_id) - set(constraint_by_id)
    if unknown_manual_ids:
        raise ValueError(f"manual review plan contains unknown constraints: {sorted(unknown_manual_ids)[:20]}")

    retrieval_sha = str(retrieval_manifest["dataset_sha256"])
    publication_sha = _semantic_sha256({
        "constraints": constraints,
        "validation_rules": rules,
        "manual_reviews": manual_reviews,
        "validator_sha256": validator_sha256,
    })
    dataset_id = f"constraint-dataset:v2/{retrieval_sha}"

    projection_constraints: list[dict] = []
    targets: list[dict] = []
    sections: dict[str, dict] = {}
    projection_rules: list[dict] = []

    for constraint_id in sorted(constraint_by_id):
        record = constraint_by_id[constraint_id]
        card = card_by_id[constraint_id]
        source = record["source"]
        source_location = source["source"]
        semantics = record["semantics"]
        verification = record["verification"]
        quality = record["quality"]
        manual_review = manual_by_id.get(constraint_id) or {}
        section_path = list(source_location.get("section_path") or [])
        section_id = _section_id(section_path)
        sections.setdefault(section_id, {
            "id": section_id,
            "props": {
                "path": section_path,
                "path_text": " / ".join(section_path),
                "document": source_location.get("document", ""),
                "schema_version": "2.0",
            },
        })

        target_records = list(record.get("targets") or [])
        constraint_entity_id = _constraint_entity_id(constraint_id)
        constraint_props = {
            "constraint_id": constraint_id,
            "cid": constraint_id,
            "schema_version": "2.0",
            "dataset_sha256": retrieval_sha,
            "publication_sha256": publication_sha,
            "validator_sha256": validator_sha256,
            "title": source.get("title", ""),
            "expression": source.get("expression", ""),
            "summary": semantics.get("summary", ""),
            "rationale": semantics.get("rationale", ""),
            "source_sha256": source_location.get("sha256", ""),
            "source_document": source_location.get("document", ""),
            "source_start_line": int(source_location.get("start_line") or 0),
            "source_end_line": int(source_location.get("end_line") or 0),
            "section_path": section_path,
            "normativity": semantics.get("normativity", ""),
            "importance": semantics.get("importance", ""),
            "is_core": bool(semantics.get("is_core")),
            "usages": list(semantics.get("usages") or []),
            "rule_family": semantics.get("rule_family", ""),
            "scope": semantics.get("scope", ""),
            "validation_policy": verification.get("policy", ""),
            "must_validate": bool(verification.get("must_validate")),
            "severity": verification.get("severity", ""),
            "preferred_backend": verification.get("preferred_backend", ""),
            "fallback_backend": verification.get("fallback_backend", ""),
            "observability": verification.get("observability", ""),
            "observability_reason": verification.get("observability_reason", ""),
            "manual_review_decision": manual_review.get("decision", ""),
            "manual_required_capability": manual_review.get("required_capability", ""),
            "manual_review_reason": manual_review.get("reason", ""),
            "manual_review_instruction": manual_review.get("review_instruction", ""),
            "partial_arxml_guard": bool(manual_review.get("partial_arxml_guard", False)),
            "review_status": quality.get("review_status", ""),
            "semantic_status": quality.get("semantic_status", ""),
            "binding_status": quality.get("binding_status", ""),
            "quality_issues": list(quality.get("issues") or []),
            "class_tags": list(card.get("class_tags") or []),
            "property_tags": list(card.get("property_tags") or []),
            "paths": list(card.get("paths") or []),
            "card_json": canonical_json(card),
            "targets_json": canonical_json(target_records),
            "is_active": True,
        }
        projection_constraints.append({
            "id": constraint_entity_id,
            "constraint_id": constraint_id,
            "section_id": section_id,
            "dataset_id": dataset_id,
            "props": constraint_props,
        })

        for index, target in enumerate(target_records):
            targets.append({
                "id": _target_entity_id(constraint_id, index),
                "constraint_id": constraint_id,
                "constraint_entity_id": constraint_entity_id,
                "props": {
                    "constraint_id": constraint_id,
                    "target_index": index,
                    "role": target.get("role", ""),
                    "class_name": target.get("class_name", ""),
                    "class_xml_tag": target.get("class_xml_tag", ""),
                    "property_name": target.get("property_name", ""),
                    "property_xml_tag": target.get("property_xml_tag", ""),
                    "path": target.get("path", ""),
                    "binding_status": target.get("binding_status", ""),
                    "evidence": target.get("evidence", ""),
                    "candidates": list(target.get("candidates") or []),
                    "dataset_sha256": retrieval_sha,
                    "schema_version": "2.0",
                },
            })

        for rule in sorted(rules_by_constraint.get(constraint_id, []), key=lambda item: item["rule_id"]):
            implementation = rule.get("implementation") or {}
            projection_rules.append({
                "id": _rule_entity_id(str(rule["rule_id"])),
                "rule_id": str(rule["rule_id"]),
                "constraint_id": constraint_id,
                "constraint_entity_id": constraint_entity_id,
                "props": {
                    "rule_id": str(rule["rule_id"]),
                    "constraint_id": constraint_id,
                    "dataset_sha256": retrieval_sha,
                    "validator_sha256": validator_sha256,
                    "source_sha256": rule.get("source_sha256", ""),
                    "severity": rule.get("severity", ""),
                    "policy": rule.get("policy", ""),
                    "backend": rule.get("backend", ""),
                    "implementation_status": implementation.get("status", ""),
                    "plugin": implementation.get("plugin") or "",
                    "selector_tags": list((rule.get("selector") or {}).get("tags") or []),
                    "selector_mode": (rule.get("selector") or {}).get("mode", ""),
                    "rule_json": canonical_json(rule),
                    "schema_version": "2.0",
                },
            })

    dataset = {
        "id": dataset_id,
        "props": {
            "schema_version": "2.0",
            "dataset_sha256": retrieval_sha,
            "publication_sha256": publication_sha,
            "validator_sha256": validator_sha256,
            "card_count": len(cards),
            "constraint_count": len(constraints),
            "target_count": len(targets),
            "validation_rule_count": len(projection_rules),
            "manual_review_count": len(manual_reviews),
            "status": "ready",
        },
    }
    return {
        "schema_version": "2.0",
        "dataset": dataset,
        "constraints": projection_constraints,
        "targets": targets,
        "sections": sorted(sections.values(), key=lambda item: item["id"]),
        "validation_rules": projection_rules,
    }


def projection_summary(projection: dict[str, Any]) -> dict[str, Any]:
    dataset = projection["dataset"]["props"]
    return {
        "schema_version": "2.0",
        "dataset_sha256": dataset["dataset_sha256"],
        "publication_sha256": dataset["publication_sha256"],
        "validator_sha256": dataset.get("validator_sha256", ""),
        "constraint_count": len(projection["constraints"]),
        "target_count": len(projection["targets"]),
        "section_count": len(projection["sections"]),
        "validation_rule_count": len(projection["validation_rules"]),
    }
