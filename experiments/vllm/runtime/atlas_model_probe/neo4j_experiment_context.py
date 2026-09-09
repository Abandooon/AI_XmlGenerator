"""Canonical, credential-free evidence for the Neo4j inputs used by Phase 2."""

from __future__ import annotations

import hashlib
import heapq
import json
from pathlib import Path
import tempfile
from typing import Any


SCHEMA_LABELS = ("Class", "Attribute", "Enum", "EnumLiteral")
SCHEMA_RELATIONSHIPS = (
    "HAS_ATTRIBUTE",
    "TYPE_OF",
    "SUBCLASS_OF",
    "HAS_LITERAL",
)
CONSTRAINT_RELATIONSHIPS = ("APPLIES_TO_CLASS", "APPLIES_TO_PROPERTY")


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(item) for item in value]
    return str(value)


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        _jsonable(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _canonical_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = [_jsonable(dict(row)) for row in rows]
    return sorted(
        normalized,
        key=lambda row: json.dumps(
            row, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ),
    )


def _canonical_row_json(row: dict[str, Any]) -> str:
    return json.dumps(
        _jsonable(dict(row)),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


DEFAULT_CONTEXT_BATCH_SIZE = 25


def _streaming_canonical_query_hash(
    session,
    query: str,
    *,
    parameters: dict[str, Any],
    batch_size: int = DEFAULT_CONTEXT_BATCH_SIZE,
) -> tuple[int, str]:
    """Hash canonically sorted query rows without retaining the graph in RAM.

    The digest is byte-identical to ``canonical_sha256(_canonical_rows(rows))``.
    Neo4j rows are paged by ``elementId``; each page is sorted into a temporary
    chunk and the chunks are merged lexicographically while hashing the JSON
    array representation.  The internal ``_atlas_row_id`` cursor is excluded
    from the canonical row.  The deliberately small default page bounds each
    Bolt response because relationship rows include the complete properties of
    both endpoints.  Changing the page size does not change the canonical hash.
    """
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    row_count = 0
    after_id: str | None = None
    with tempfile.TemporaryDirectory(prefix="atlas-neo4j-context-") as raw:
        directory = Path(raw)
        chunks: list[Path] = []
        while True:
            result = session.run(
                query,
                **parameters,
                after_id=after_id,
                batch_size=batch_size,
            )
            rows = result.data()
            if not rows:
                break
            next_after = rows[-1].get("_atlas_row_id")
            row_strings = []
            for row in rows:
                canonical_row = dict(row)
                canonical_row.pop("_atlas_row_id", None)
                row_strings.append(_canonical_row_json(canonical_row))
            row_strings.sort()
            chunk = directory / f"chunk-{len(chunks):06d}.jsonl"
            chunk.write_text(
                "\n".join(row_strings) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            chunks.append(chunk)
            row_count += len(row_strings)
            # Test doubles and legacy providers may omit the pagination field.
            # Treat that response as one complete page rather than looping.
            if not next_after:
                break
            if next_after == after_id:
                raise RuntimeError("Neo4j context pagination cursor did not advance")
            after_id = str(next_after)
            if len(rows) < batch_size:
                break

        digest = hashlib.sha256()
        digest.update(b"[")
        handles = [path.open("r", encoding="utf-8") for path in chunks]
        try:
            first = True
            for line in heapq.merge(*handles):
                value = line.rstrip("\n")
                if not first:
                    digest.update(b",")
                digest.update(value.encode("utf-8"))
                first = False
        finally:
            for handle in handles:
                handle.close()
        digest.update(b"]")
        return row_count, digest.hexdigest()


def collect_neo4j_context(
    driver,
    *,
    database: str | None,
    dataset_sha256: str,
    expected_card_count: int,
) -> dict[str, Any]:
    """Collect only hashes/counts from the read-only Phase 2 graph projection."""

    with driver.session(database=database or None) as session:
        session.run("RETURN 1 AS ok").consume()
        server_components = _canonical_rows(
            session.run(
                """
                CALL dbms.components()
                YIELD name, versions, edition
                RETURN name, versions, edition
                """
            ).data()
        )
        if not server_components:
            raise RuntimeError("Neo4j server component identity is unavailable")
        marker = session.run(
            """
            MATCH (d:ConstraintDatasetV2 {dataset_sha256: $dataset_sha256})
            RETURN d.status AS status, d.card_count AS card_count
            """,
            dataset_sha256=dataset_sha256,
        ).single()
        if (
            marker is None
            or marker.get("status") != "ready"
            or int(marker.get("card_count") or -1) != expected_card_count
        ):
            raise RuntimeError("frozen ConstraintV2 dataset is not ready in Neo4j")

        schema_node_count, schema_nodes_sha256 = _streaming_canonical_query_hash(
            session,
            """
            MATCH (n)
            WHERE any(label IN labels(n) WHERE label IN $labels)
            WITH n, elementId(n) AS row_id
            WHERE $after_id IS NULL OR row_id > $after_id
            ORDER BY row_id
            LIMIT $batch_size
            RETURN row_id AS _atlas_row_id,
                   labels(n) AS labels,
                   properties(n) AS properties
            """,
            parameters={"labels": list(SCHEMA_LABELS)},
        )
        (
            schema_relationship_count,
            schema_relationships_sha256,
        ) = _streaming_canonical_query_hash(
            session,
            """
            MATCH (source)-[relationship]->(target)
            WHERE type(relationship) IN $relationship_types
              AND any(label IN labels(source) WHERE label IN $labels)
              AND any(label IN labels(target) WHERE label IN $labels)
            WITH source, relationship, target,
                 elementId(relationship) AS row_id
            WHERE $after_id IS NULL OR row_id > $after_id
            ORDER BY row_id
            LIMIT $batch_size
            RETURN row_id AS _atlas_row_id,
                   labels(source) AS source_labels,
                   properties(source) AS source_properties,
                   type(relationship) AS relationship_type,
                   properties(relationship) AS relationship_properties,
                   labels(target) AS target_labels,
                   properties(target) AS target_properties
            """,
            parameters={
                "labels": list(SCHEMA_LABELS),
                "relationship_types": list(SCHEMA_RELATIONSHIPS),
            },
        )
        constraint_link_count, constraint_links_sha256 = (
            _streaming_canonical_query_hash(
                session,
                """
                MATCH (constraint:ConstraintV2 {dataset_sha256: $dataset_sha256})
                      -[relationship]->(target)
                WHERE type(relationship) IN $relationship_types
                WITH constraint, relationship, target,
                     elementId(relationship) AS row_id
                WHERE $after_id IS NULL OR row_id > $after_id
                ORDER BY row_id
                LIMIT $batch_size
                RETURN row_id AS _atlas_row_id,
                       constraint.constraint_id AS constraint_id,
                       type(relationship) AS relationship_type,
                       properties(relationship) AS relationship_properties,
                       labels(target) AS target_labels,
                       properties(target) AS target_properties
                """,
                parameters={
                    "dataset_sha256": dataset_sha256,
                    "relationship_types": list(CONSTRAINT_RELATIONSHIPS),
                },
            )
        )
        required_types = [
            "APPLICATION-SW-COMPONENT-TYPE",
            "SENDER-RECEIVER-INTERFACE",
        ]
        row = session.run(
            """
            UNWIND $xml_tags AS xml_tag
            OPTIONAL MATCH (class:Class {xml_tag: xml_tag})
            RETURN collect(DISTINCT class.xml_tag) AS found
            """,
            xml_tags=required_types,
        ).single()
        found = sorted(set((row or {}).get("found") or []))
        missing = sorted(set(required_types) - set(found))
        if missing:
            raise RuntimeError(
                "formal AUTOSAR schema graph lacks required types: "
                + ", ".join(missing)
            )

    body = {
        "schema_version": "atlas.asw_v3.neo4j_context.v1",
        "dataset_sha256": dataset_sha256,
        "constraint_card_count": expected_card_count,
        "server_components": server_components,
        "required_schema_types": required_types,
        "schema_node_count": schema_node_count,
        "schema_relationship_count": schema_relationship_count,
        "constraint_link_count": constraint_link_count,
        "schema_nodes_sha256": schema_nodes_sha256,
        "schema_relationships_sha256": schema_relationships_sha256,
        "constraint_links_sha256": constraint_links_sha256,
        "read_only": True,
        "credentials_included": False,
    }
    body["context_sha256"] = canonical_sha256(body)
    return body


def verify_neo4j_context(observed: dict[str, Any], expected: dict[str, Any]) -> None:
    if observed != expected:
        differing = sorted(
            key for key in set(observed) | set(expected)
            if observed.get(key) != expected.get(key)
        )
        raise RuntimeError(
            "Neo4j formal experiment context differs from freeze: "
            + ", ".join(differing)
        )
