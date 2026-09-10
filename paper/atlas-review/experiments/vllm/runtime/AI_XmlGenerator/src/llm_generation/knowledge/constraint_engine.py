"""Compatibility facade over the unified ConstraintV2 repository.

New generation code uses :class:`GenerationConstraintAdapterV2` directly. The
facade remains for callers that still request constraints by XML element type;
it no longer contains a second Neo4j query model or mock rules.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .v2.generation_adapter import GenerationConstraintAdapterV2
from ..config import CONFIG


class ConstraintType(Enum):
    MODEL_OCL = "ModelOCL"
    DATA_TYPE = "DataType"
    PRODUCTION = "Production"
    DOCUMENTATION = "Documentation"


@dataclass(frozen=True)
class ConstraintInfo:
    constraint_id: str
    constraint_type: ConstraintType
    expression: str
    title: str
    description: str
    target_elements: list[str]
    is_active: bool
    metadata: dict[str, Any]


class ConstraintEngine:
    def __init__(self) -> None:
        self.adapter = GenerationConstraintAdapterV2.try_default(CONFIG)

    def query_constraints_for_elements(self, element_types: list[str]) -> list[ConstraintInfo]:
        if not element_types or self.adapter is None:
            return []
        batch = self.adapter.repository.retrieve(
            class_tags=sorted(set(element_types)),
            property_tags=[],
            paths=[],
            purpose="generation_context",
            query=" ".join(element_types),
            max_constraints=max(1, int(CONFIG.constraint_engine.max_constraints_component)),
            per_family_limit=max(1, int(CONFIG.constraint_engine.per_family_limit)),
        )
        return [
            ConstraintInfo(
                constraint_id=card["constraint_id"],
                constraint_type=ConstraintType.DOCUMENTATION,
                expression=card.get("summary", ""),
                title=card.get("title", ""),
                description=card.get("summary", ""),
                target_elements=list(card.get("class_tags") or []),
                is_active=True,
                metadata=card,
            )
            for card in batch.cards
        ]

    def generate_constraint_prompt(self, element_types: list[str]) -> str:
        records = self.query_constraints_for_elements(element_types)
        return GenerationConstraintAdapterV2.render_prompt([record.metadata for record in records])

    def clear_cache(self) -> None:
        return None

    def close(self) -> None:
        if self.adapter is None:
            return
        neo4j = getattr(self.adapter.repository, "neo4j", None)
        if neo4j is not None:
            neo4j.close()

    def get_stats(self) -> dict[str, Any]:
        trace = self.adapter.retrieval_trace() if self.adapter is not None else {}
        return {
            "enabled": self.adapter is not None,
            "backend": trace.get("backend", "not-used"),
            "dataset_sha256": trace.get("dataset_sha256", ""),
        }


constraint_engine = ConstraintEngine()
