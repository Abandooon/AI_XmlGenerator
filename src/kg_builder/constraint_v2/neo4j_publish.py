"""Idempotently publish the versioned ConstraintV2 projection to Neo4j."""

from __future__ import annotations

from typing import Any, Iterable

from neo4j import GraphDatabase


def _batches(values: list[dict], size: int = 500) -> Iterable[list[dict]]:
    for index in range(0, len(values), size):
        yield values[index:index + size]


def _session(driver, database: str | None):
    return driver.session(database=database or None)


def _create_schema(session) -> None:
    statements = [
        "CREATE CONSTRAINT constraint_v2_id IF NOT EXISTS FOR (n:ConstraintV2) REQUIRE n.constraint_id IS UNIQUE",
        "CREATE CONSTRAINT constraint_target_v2_id IF NOT EXISTS FOR (n:ConstraintTargetV2) REQUIRE n.id IS UNIQUE",
        "CREATE CONSTRAINT validation_rule_v2_id IF NOT EXISTS FOR (n:ValidationRuleV2) REQUIRE n.rule_id IS UNIQUE",
        "CREATE CONSTRAINT constraint_dataset_v2_hash IF NOT EXISTS FOR (n:ConstraintDatasetV2) REQUIRE n.dataset_sha256 IS UNIQUE",
        "CREATE CONSTRAINT document_section_v2_id IF NOT EXISTS FOR (n:DocumentSectionV2) REQUIRE n.id IS UNIQUE",
    ]
    for statement in statements:
        session.run(statement).consume()


def _clear_current_projection(session, constraint_ids: list[str]) -> None:
    for batch in _batches([{"constraint_id": item} for item in constraint_ids]):
        session.run(
            """
            UNWIND $rows AS row
            MATCH (c:ConstraintV2 {constraint_id: row.constraint_id})-[:HAS_TARGET]->(t:ConstraintTargetV2)
            DETACH DELETE t
            """,
            rows=batch,
        ).consume()
        session.run(
            """
            UNWIND $rows AS row
            MATCH (c:ConstraintV2 {constraint_id: row.constraint_id})-[:COMPILES_TO]->(r:ValidationRuleV2)
            DETACH DELETE r
            """,
            rows=batch,
        ).consume()
        for relationship in (
            "APPLIES_TO_CLASS",
            "APPLIES_TO_PROPERTY",
            "DERIVED_FROM",
            "IN_CONSTRAINT_DATASET",
        ):
            session.run(
                f"""
                UNWIND $rows AS row
                MATCH (c:ConstraintV2 {{constraint_id: row.constraint_id}})-[r:{relationship}]->()
                DELETE r
                """,
                rows=batch,
            ).consume()


def apply_projection(
    *,
    uri: str,
    user: str,
    password: str,
    database: str | None,
    projection: dict[str, Any],
) -> dict[str, Any]:
    if not password:
        raise ValueError("Neo4j password is not configured")
    dataset = projection["dataset"]
    constraints = list(projection["constraints"])
    targets = list(projection["targets"])
    sections = list(projection["sections"])
    rules = list(projection["validation_rules"])
    driver = GraphDatabase.driver(uri, auth=(user, password))
    try:
        with _session(driver, database) as session:
            _create_schema(session)
            publishing_props = dict(dataset["props"])
            publishing_props["status"] = "publishing"
            session.run(
                """
                MERGE (d:Entity {id: $id})
                SET d:ConstraintDatasetV2
                SET d += $props
                """,
                id=dataset["id"],
                props=publishing_props,
            ).consume()
            _clear_current_projection(
                session,
                [row["constraint_id"] for row in constraints],
            )

            for batch in _batches(sections):
                session.run(
                    """
                    UNWIND $rows AS row
                    MERGE (s:Entity {id: row.id})
                    SET s:DocumentSectionV2
                    SET s += row.props
                    """,
                    rows=batch,
                ).consume()
            for batch in _batches(constraints):
                session.run(
                    """
                    UNWIND $rows AS row
                    MERGE (c:Entity {id: row.id})
                    SET c:Constraint:ConstraintV2
                    SET c += row.props
                    WITH c, row
                    MATCH (d:ConstraintDatasetV2 {id: row.dataset_id})
                    MATCH (s:DocumentSectionV2 {id: row.section_id})
                    MERGE (c)-[:IN_CONSTRAINT_DATASET]->(d)
                    MERGE (c)-[:DERIVED_FROM]->(s)
                    """,
                    rows=batch,
                ).consume()
            for batch in _batches(targets):
                session.run(
                    """
                    UNWIND $rows AS row
                    MATCH (c:ConstraintV2 {constraint_id: row.constraint_id})
                    MERGE (t:Entity {id: row.id})
                    SET t:ConstraintTargetV2
                    SET t += row.props
                    MERGE (c)-[:HAS_TARGET]->(t)
                    """,
                    rows=batch,
                ).consume()
            for batch in _batches(rules):
                session.run(
                    """
                    UNWIND $rows AS row
                    MATCH (c:ConstraintV2 {constraint_id: row.constraint_id})
                    MERGE (r:Entity {id: row.id})
                    SET r:ValidationRuleV2
                    SET r += row.props
                    MERGE (c)-[:COMPILES_TO]->(r)
                    """,
                    rows=batch,
                ).consume()

            class_rows = [
                {
                    "constraint_id": target["constraint_id"],
                    "class_name": target["props"].get("class_name", ""),
                    "class_xml_tag": target["props"].get("class_xml_tag", ""),
                }
                for target in targets
                if target["props"].get("class_name")
                or target["props"].get("class_xml_tag")
            ]
            # Deduplicate before matching ontology nodes.
            class_rows = list({
                (item["constraint_id"], item["class_name"], item["class_xml_tag"]): item
                for item in class_rows
            }.values())
            for batch in _batches(class_rows):
                session.run(
                    """
                    UNWIND $rows AS row
                    MATCH (c:ConstraintV2 {constraint_id: row.constraint_id})
                    MATCH (target:Class)
                    WHERE (row.class_name <> '' AND target.name = row.class_name)
                       OR (row.class_xml_tag <> '' AND target.xml_tag = row.class_xml_tag)
                    MERGE (c)-[:APPLIES_TO_CLASS]->(target)
                    """,
                    rows=batch,
                ).consume()

            property_rows = [
                {
                    "constraint_id": target["constraint_id"],
                    "class_name": target["props"].get("class_name", ""),
                    "property_name": target["props"].get("property_name", ""),
                    "property_xml_tag": target["props"].get("property_xml_tag", ""),
                }
                for target in targets
                if target["props"].get("property_name")
                or target["props"].get("property_xml_tag")
            ]
            property_rows = list({
                (
                    item["constraint_id"], item["class_name"],
                    item["property_name"], item["property_xml_tag"],
                ): item
                for item in property_rows
            }.values())
            for batch in _batches(property_rows):
                session.run(
                    """
                    UNWIND $rows AS row
                    MATCH (c:ConstraintV2 {constraint_id: row.constraint_id})
                    MATCH (target:Attribute)
                    WHERE (
                      row.property_name <> ''
                      AND target.name = row.property_name
                      AND (
                        row.class_name = ''
                        OR target.ownerClass = row.class_name
                        OR target.parentClass = row.class_name
                      )
                    ) OR (
                      row.property_xml_tag <> ''
                      AND target.xml_tag = row.property_xml_tag
                      AND (
                        row.class_name = ''
                        OR target.ownerClass = row.class_name
                        OR target.parentClass = row.class_name
                      )
                    )
                    MERGE (c)-[:APPLIES_TO_PROPERTY]->(target)
                    """,
                    rows=batch,
                ).consume()

            ready_props = dict(dataset["props"])
            ready_props["status"] = "ready"
            session.run(
                """
                MATCH (d:ConstraintDatasetV2 {id: $id})
                SET d += $props
                """,
                id=dataset["id"],
                props=ready_props,
            ).consume()
        return audit_projection(
            uri=uri,
            user=user,
            password=password,
            database=database,
            dataset_sha256=dataset["props"]["dataset_sha256"],
            expected=dataset["props"],
        )
    finally:
        driver.close()


def audit_projection(
    *,
    uri: str,
    user: str,
    password: str,
    database: str | None,
    dataset_sha256: str,
    expected: dict[str, Any] | None = None,
) -> dict[str, Any]:
    driver = GraphDatabase.driver(uri, auth=(user, password))
    try:
        with _session(driver, database) as session:
            marker = session.run(
                """
                MATCH (d:ConstraintDatasetV2 {dataset_sha256: $dataset_sha256})
                RETURN properties(d) AS props
                """,
                dataset_sha256=dataset_sha256,
            ).single()
            counts = session.run(
                """
                MATCH (c:ConstraintV2 {dataset_sha256: $dataset_sha256})
                OPTIONAL MATCH (c)-[:HAS_TARGET]->(t:ConstraintTargetV2)
                OPTIONAL MATCH (c)-[:COMPILES_TO]->(r:ValidationRuleV2)
                RETURN count(DISTINCT c) AS constraints,
                       count(DISTINCT t) AS targets,
                       count(DISTINCT r) AS validation_rules
                """,
                dataset_sha256=dataset_sha256,
            ).single()
            graph_counts = session.run(
                """
                MATCH (c:ConstraintV2 {dataset_sha256: $dataset_sha256})
                OPTIONAL MATCH (c)-[:APPLIES_TO_CLASS]->(class:Class)
                OPTIONAL MATCH (c)-[:APPLIES_TO_PROPERTY]->(attribute:Attribute)
                RETURN count(DISTINCT class) AS linked_classes,
                       count(DISTINCT attribute) AS linked_attributes,
                       count(DISTINCT CASE WHEN class IS NOT NULL OR attribute IS NOT NULL
                                           THEN c END) AS graph_linked_constraints
                """,
                dataset_sha256=dataset_sha256,
            ).single()
    finally:
        driver.close()

    marker_props = dict(marker["props"]) if marker else {}
    actual = {
        "constraint_count": int(counts["constraints"] if counts else 0),
        "target_count": int(counts["targets"] if counts else 0),
        "validation_rule_count": int(counts["validation_rules"] if counts else 0),
    }
    errors: list[str] = []
    if not marker:
        errors.append("dataset marker is missing")
    elif marker_props.get("status") != "ready":
        errors.append(f"dataset status is {marker_props.get('status')!r}")
    if expected:
        for field in ("constraint_count", "target_count", "validation_rule_count"):
            if int(expected.get(field) or 0) != actual[field]:
                errors.append(
                    f"{field} mismatch: expected={expected.get(field)}, actual={actual[field]}"
                )
    return {
        "schema_version": "2.0",
        "valid": not errors,
        "dataset_sha256": dataset_sha256,
        "marker": marker_props,
        "counts": actual,
        "graph": dict(graph_counts) if graph_counts else {},
        "errors": errors,
    }
