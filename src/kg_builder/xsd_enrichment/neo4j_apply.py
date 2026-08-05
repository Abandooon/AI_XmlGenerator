"""Strictly additive Neo4j application for XSD enrichment properties."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from typing import Any

from neo4j import GraphDatabase

from .content_model import canonical_json, semantic_hash
from .matcher import XSD_METADATA_FIELDS

_NON_ALNUM = re.compile(r"[^0-9A-Za-z]+")


def _slug(value: str) -> str:
    return re.sub(r"_+", "_", _NON_ALNUM.sub("_", value)).strip("_")


class KgUpdateConflict(ValueError):
    def __init__(self, conflicts: list[dict[str, Any]]) -> None:
        self.conflicts = conflicts
        super().__init__(
            "Conflicting metadata records resolve to the same KG entity ids: "
            f"{conflicts[:20]} (total={len(conflicts)})"
        )


def _decode_json(raw: str, *, field: str, expected: type) -> Any:
    try:
        value = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid {field} JSON") from exc
    if not isinstance(value, expected):
        raise ValueError(f"{field} must decode to {expected.__name__}")
    return value


def _merge_same_name_props(entries: list[dict[str, Any]]) -> dict[str, Any]:
    """Losslessly combine split legacy records for one logical KG name."""

    props_list = [entry["props"] for entry in entries]
    if all(props == props_list[0] for props in props_list[1:]):
        return props_list[0]

    merged: dict[str, Any] = {}
    for field in ("xsd_source_sha256", "xsd_model_version"):
        values = {props[field] for props in props_list if props.get(field) not in (None, "")}
        if len(values) != 1:
            raise ValueError(f"incompatible {field}")
        merged[field] = next(iter(values))

    models_by_owner: dict[str, dict[str, Any]] = {}
    for props in props_list:
        models = _decode_json(
            props.get("xsd_content_models_json", ""),
            field="xsd_content_models_json",
            expected=list,
        )
        declared_owner_ids = _decode_json(
            props.get("xsd_owner_ids_json", ""),
            field="xsd_owner_ids_json",
            expected=list,
        )
        actual_owner_ids: list[str] = []
        for model in models:
            if not isinstance(model, dict) or not model.get("owner_id"):
                raise ValueError("content model is missing owner_id")
            owner_id = str(model["owner_id"])
            actual_owner_ids.append(owner_id)
            previous = models_by_owner.get(owner_id)
            if previous is not None and canonical_json(previous) != canonical_json(model):
                raise ValueError(f"owner {owner_id} has incompatible models")
            models_by_owner[owner_id] = model
        if set(map(str, declared_owner_ids)) != set(actual_owner_ids):
            raise ValueError("xsd_owner_ids_json does not match content models")

    models = sorted(
        models_by_owner.values(),
        key=lambda item: (str(item.get("owner_kind")), str(item.get("owner_id"))),
    )
    merged["xsd_content_models_json"] = canonical_json(models)
    merged["xsd_owner_ids_json"] = canonical_json([item["owner_id"] for item in models])
    merged["xsd_model_sha256"] = semantic_hash(models)

    def unique_json_values(field: str) -> list[Any]:
        values: dict[str, Any] = {}
        for props in props_list:
            raw = props.get(field)
            if raw in (None, ""):
                continue
            value = _decode_json(raw, field=field, expected=dict)
            values[canonical_json(value)] = value
        return list(values.values())

    group_models = unique_json_values("xsd_group_model_json")
    if len(group_models) > 1:
        raise ValueError("multiple incompatible group models")
    if group_models:
        merged["xsd_group_model_json"] = canonical_json(group_models[0])

    complex_models = unique_json_values("xsd_complex_type_model_json")
    if len(complex_models) == 1:
        merged["xsd_complex_type_model_json"] = canonical_json(complex_models[0])

    effective_models: dict[str, dict[str, Any]] = {}
    for model in models:
        effective = model.get("effective_model")
        if isinstance(effective, dict):
            effective_models[canonical_json(effective)] = effective
    if len(effective_models) == 1:
        merged["xsd_effective_model_json"] = canonical_json(next(iter(effective_models.values())))

    return merged


def collect_updates(
    metadata: dict[str, Any],
    *,
    domain: str,
    version: str,
) -> list[dict[str, Any]]:
    """Collect Class updates, merging only lossless same-name legacy splits."""

    by_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for section in ("groups", "complexTypes", "extract_inner_class"):
        for key, record in (metadata.get(section) or {}).items():
            if not isinstance(record, dict):
                continue
            props = {
                field: record[field]
                for field in XSD_METADATA_FIELDS
                if record.get(field) not in (None, "")
            }
            if not props:
                continue
            name = str(record.get("name") or key)
            entity_id = str(record.get("iri") or f"{domain.lower()}:{version}/{_slug(name)}")
            by_id[entity_id].append(
                {"source": f"{section}.{key}", "name": name, "props": props}
            )

    rows: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    for entity_id, entries in sorted(by_id.items()):
        names = {entry["name"] for entry in entries}
        if len(names) != 1:
            conflicts.append(
                {
                    "entity_id": entity_id,
                    "sources": [entry["source"] for entry in entries],
                    "reason": "different names collapse to the same entity id",
                }
            )
            continue
        try:
            props = _merge_same_name_props(entries)
        except ValueError as exc:
            conflicts.append(
                {
                    "entity_id": entity_id,
                    "sources": [entry["source"] for entry in entries],
                    "reason": str(exc),
                }
            )
            continue
        rows.append({"id": entity_id, "props": props})

    if conflicts:
        raise KgUpdateConflict(conflicts)
    return rows


def apply_updates(
    *,
    uri: str,
    user: str,
    password: str,
    rows: list[dict[str, Any]],
    replace_existing: bool = False,
) -> dict[str, Any]:
    """Apply only ``xsd_*`` properties after an exact one-node-per-id audit."""

    if not rows:
        return {"requested": 0, "updated": 0, "noop": 0}

    driver = GraphDatabase.driver(uri, auth=(user, password))
    try:
        with driver.session() as session:
            counts = session.run(
                """
                UNWIND $ids AS entity_id
                OPTIONAL MATCH (n:Entity {id: entity_id})
                RETURN entity_id, count(n) AS matches
                """,
                ids=[row["id"] for row in rows],
            ).data()
            invalid = [item for item in counts if item["matches"] != 1]
            if invalid:
                raise RuntimeError(
                    "Neo4j enrichment aborted: every metadata entity id must match exactly one "
                    f"Entity node; invalid sample={invalid[:20]} (total={len(invalid)})"
                )

            existing_rows = session.run(
                """
                UNWIND $ids AS entity_id
                MATCH (n:Entity {id: entity_id})
                RETURN entity_id, properties(n) AS props
                """,
                ids=[row["id"] for row in rows],
            ).data()
            existing = {item["entity_id"]: item["props"] for item in existing_rows}

            to_write: list[dict[str, Any]] = []
            noop = 0
            conflicts: list[dict[str, str]] = []
            for row in rows:
                current = existing[row["id"]]
                changed: dict[str, Any] = {}
                for field, value in row["props"].items():
                    old = current.get(field)
                    if old in (None, "") or old == value or replace_existing:
                        if old != value:
                            changed[field] = value
                    else:
                        conflicts.append({"id": row["id"], "field": field})
                if changed:
                    to_write.append({"id": row["id"], "props": changed})
                else:
                    noop += 1

            if conflicts:
                raise RuntimeError(
                    "Neo4j enrichment aborted because existing xsd_* properties differ; "
                    f"conflict sample={conflicts[:20]} (total={len(conflicts)})"
                )

            if to_write:
                session.run(
                    """
                    UNWIND $rows AS row
                    MATCH (n:Entity {id: row.id})
                    SET n += row.props
                    """,
                    rows=to_write,
                ).consume()
            return {"requested": len(rows), "updated": len(to_write), "noop": noop}
    finally:
        driver.close()
