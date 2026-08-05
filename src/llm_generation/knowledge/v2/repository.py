"""Unified constraint repository with Neo4j-first and local fallback modes."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .constraint_retriever import ConstraintRetrieverV2
from .dataset import load_and_validate_manifest

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RetrievalBatch:
    cards: list[dict]
    backend: str
    dataset_sha256: str
    fallback_reason: str = ""

    def trace(self) -> dict[str, Any]:
        return {
            "backend": self.backend,
            "dataset_sha256": self.dataset_sha256,
            "result_count": len(self.cards),
            "fallback_reason": self.fallback_reason,
            "constraint_ids": [card["constraint_id"] for card in self.cards],
        }


class LocalConstraintRepository:
    def __init__(self, cards: list[dict], dataset_sha256: str) -> None:
        self.cards = cards
        self.dataset_sha256 = dataset_sha256
        self.retriever = ConstraintRetrieverV2(cards)

    @classmethod
    def from_files(cls, cards_path: str | Path, manifest_path: str | Path) -> "LocalConstraintRepository":
        cards, manifest = load_and_validate_manifest(cards_path, manifest_path)
        return cls(cards, str(manifest["dataset_sha256"]))

    def retrieve(self, **query: Any) -> RetrievalBatch:
        return RetrievalBatch(
            cards=self.retriever.retrieve(**query),
            backend="local",
            dataset_sha256=self.dataset_sha256,
        )


class Neo4jConstraintRepository:
    """Read one immutable, hash-pinned ConstraintV2 dataset from Neo4j."""

    def __init__(
        self,
        *,
        uri: str,
        user: str,
        password: str,
        database: str | None,
        dataset_sha256: str,
        expected_count: int,
    ) -> None:
        self.uri = uri
        self.user = user
        self.password = password
        self.database = database or None
        self.dataset_sha256 = dataset_sha256
        self.expected_count = expected_count
        self._driver = None
        self._cards: list[dict] | None = None

    def _session(self):
        if not self.password:
            raise RuntimeError("Neo4j password is not configured")
        if self._driver is None:
            from neo4j import GraphDatabase

            self._driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
            )
        return self._driver.session(database=self.database)

    def close(self) -> None:
        if self._driver is not None:
            self._driver.close()
            self._driver = None

    def _load_cards(self) -> list[dict]:
        if self._cards is not None:
            return self._cards
        with self._session() as session:
            marker = session.run(
                """
                MATCH (d:ConstraintDatasetV2 {dataset_sha256: $dataset_sha256})
                RETURN d.card_count AS card_count, d.status AS status
                """,
                dataset_sha256=self.dataset_sha256,
            ).single()
            if marker is None or marker.get("status") != "ready":
                raise RuntimeError("The expected ConstraintV2 dataset is not published and ready")
            if int(marker.get("card_count") or -1) != self.expected_count:
                raise RuntimeError("ConstraintV2 dataset marker count does not match the local manifest")
            rows = session.run(
                """
                MATCH (c:ConstraintV2 {dataset_sha256: $dataset_sha256})
                RETURN c.card_json AS card_json
                ORDER BY c.constraint_id
                """,
                dataset_sha256=self.dataset_sha256,
            ).data()
        cards = [json.loads(row["card_json"]) for row in rows if row.get("card_json")]
        if len(cards) != self.expected_count:
            raise RuntimeError(
                "ConstraintV2 dataset is incomplete in Neo4j: "
                f"expected={self.expected_count}, actual={len(cards)}"
            )
        self._cards = cards
        return cards

    def _graph_matches(self, class_tags: list[str], property_tags: list[str]) -> set[str]:
        if not class_tags and not property_tags:
            return set()
        with self._session() as session:
            class_rows = session.run(
                """
                UNWIND $class_tags AS class_tag
                MATCH (actual:Class {xml_tag: class_tag})
                MATCH (actual)-[:SUBCLASS_OF*0..]->(target:Class)
                MATCH (c:ConstraintV2 {dataset_sha256: $dataset_sha256})
                      -[:APPLIES_TO_CLASS]->(target)
                RETURN DISTINCT c.constraint_id AS constraint_id
                """,
                class_tags=class_tags,
                dataset_sha256=self.dataset_sha256,
            ).data() if class_tags else []
            property_rows = session.run(
                """
                UNWIND $property_tags AS property_tag
                MATCH (attribute:Attribute {xml_tag: property_tag})
                      <-[:APPLIES_TO_PROPERTY]-(c:ConstraintV2 {
                        dataset_sha256: $dataset_sha256
                      })
                RETURN DISTINCT c.constraint_id AS constraint_id
                """,
                property_tags=property_tags,
                dataset_sha256=self.dataset_sha256,
            ).data() if property_tags else []
        return {
            str(row["constraint_id"])
            for row in [*class_rows, *property_rows]
            if row.get("constraint_id")
        }

    def retrieve(self, **query: Any) -> RetrievalBatch:
        cards = self._load_cards()
        graph_matches = self._graph_matches(
            list(query.get("class_tags") or []),
            list(query.get("property_tags") or []),
        )
        ranked = ConstraintRetrieverV2(cards).retrieve(
            **query,
            graph_constraint_ids=graph_matches,
        )
        return RetrievalBatch(
            cards=ranked,
            backend="neo4j",
            dataset_sha256=self.dataset_sha256,
        )


class HybridConstraintRepository:
    def __init__(
        self,
        *,
        local: LocalConstraintRepository,
        neo4j: Neo4jConstraintRepository | None,
        mode: str = "hybrid",
    ) -> None:
        if mode not in {"hybrid", "neo4j", "local"}:
            raise ValueError("constraint repository mode must be hybrid, neo4j, or local")
        self.local = local
        self.neo4j = neo4j
        self.mode = mode

    def retrieve(self, **query: Any) -> RetrievalBatch:
        if self.mode == "local":
            return self.local.retrieve(**query)
        if self.neo4j is None:
            if self.mode == "neo4j":
                raise RuntimeError("Neo4j constraint repository is not configured")
            batch = self.local.retrieve(**query)
            return RetrievalBatch(
                cards=batch.cards,
                backend="local-fallback",
                dataset_sha256=batch.dataset_sha256,
                fallback_reason="Neo4j constraint repository is not configured",
            )
        try:
            return self.neo4j.retrieve(**query)
        except Exception as error:
            if self.mode == "neo4j":
                raise
            logger.warning("Neo4j constraint retrieval failed; using hash-matched local cards: %s", error)
            batch = self.local.retrieve(**query)
            return RetrievalBatch(
                cards=batch.cards,
                backend="local-fallback",
                dataset_sha256=batch.dataset_sha256,
                fallback_reason=f"{type(error).__name__}: {error}",
            )


def build_repository(
    *,
    cards_path: str | Path,
    manifest_path: str | Path,
    mode: str,
    neo4j_uri: str,
    neo4j_user: str,
    neo4j_password: str,
    neo4j_database: str | None = None,
) -> HybridConstraintRepository:
    local = LocalConstraintRepository.from_files(cards_path, manifest_path)
    neo4j = None
    if mode in {"hybrid", "neo4j"} and neo4j_password:
        neo4j = Neo4jConstraintRepository(
            uri=neo4j_uri,
            user=neo4j_user,
            password=neo4j_password,
            database=neo4j_database,
            dataset_sha256=local.dataset_sha256,
            expected_count=len(local.cards),
        )
    return HybridConstraintRepository(local=local, neo4j=neo4j, mode=mode)
