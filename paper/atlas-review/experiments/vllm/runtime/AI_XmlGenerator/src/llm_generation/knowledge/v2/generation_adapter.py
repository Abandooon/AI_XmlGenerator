"""Purpose- and path-aware constraint context for Round2 generation."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .repository import HybridConstraintRepository, RetrievalBatch, build_repository

XML_TAG = re.compile(r"^[A-Z][A-Z0-9-]{2,}$")


class GenerationConstraintAdapterV2:
    def __init__(self, repository: HybridConstraintRepository) -> None:
        self.repository = repository
        self.last_batch: RetrievalBatch | None = None

    @classmethod
    def try_default(cls, config: Any | None = None) -> "GenerationConstraintAdapterV2 | None":
        cards = Path(__file__).with_name("retrieval_cards.jsonl")
        manifest = Path(__file__).with_name("retrieval_manifest.json")
        if not cards.is_file() or not manifest.is_file():
            return None
        engine = getattr(config, "constraint_engine", None)
        if engine is not None and not bool(getattr(engine, "enabled", True)):
            return None
        mode = str(getattr(engine, "backend", "hybrid") or "hybrid").lower()
        knowledge_graph = getattr(config, "knowledge_graph", None)
        try:
            repository = build_repository(
                cards_path=cards,
                manifest_path=manifest,
                mode=mode,
                neo4j_uri=str(getattr(knowledge_graph, "neo4j_uri", "neo4j://127.0.0.1:7687")),
                neo4j_user=str(getattr(knowledge_graph, "neo4j_user", "neo4j")),
                neo4j_password=str(getattr(knowledge_graph, "neo4j_password", "") or ""),
                neo4j_database=str(getattr(knowledge_graph, "neo4j_database", "") or "") or None,
            )
            return cls(repository)
        except (OSError, ValueError, json.JSONDecodeError):
            return None

    @staticmethod
    def _plan_tags(value: Any) -> set[str]:
        tags: set[str] = set()

        def walk(item: Any) -> None:
            if isinstance(item, dict):
                for key, child in item.items():
                    if XML_TAG.fullmatch(str(key).strip()):
                        tags.add(str(key).strip())
                    walk(child)
            elif isinstance(item, list):
                for child in item:
                    walk(child)
            elif isinstance(item, str):
                candidate = item.strip()
                if XML_TAG.fullmatch(candidate):
                    tags.add(candidate)

        walk(value)
        return tags

    @staticmethod
    def _schema_context(schema: dict[str, Any] | None) -> tuple[set[str], set[str]]:
        tags: set[str] = set()
        paths: set[str] = set()

        def walk(node: Any, parent_path: str = "") -> None:
            if not isinstance(node, dict):
                return
            tag = str(node.get("x-xml-tag") or "").strip().upper()
            wrapper = str(node.get("x-xml-wrapper-tag") or "").strip().upper()
            segment = wrapper or tag
            current = "/".join(part for part in (parent_path, segment) if part)
            if tag:
                tags.add(tag)
            if wrapper:
                tags.add(wrapper)
            if current:
                paths.add(current)
                if wrapper and tag and wrapper != tag:
                    paths.add("/".join(part for part in (parent_path, wrapper, tag) if part))
            properties = node.get("properties")
            if isinstance(properties, dict):
                for key, child in properties.items():
                    key_tag = str(key).strip().upper()
                    if XML_TAG.fullmatch(key_tag):
                        tags.add(key_tag)
                    walk(child, current)
            items = node.get("items")
            if isinstance(items, dict):
                walk(items, parent_path)

        walk(schema or {})
        return tags, paths

    @staticmethod
    def _query_text(*values: Any) -> str:
        return " ".join(
            json.dumps(value, ensure_ascii=False, separators=(",", ":"))
            for value in values
            if value
        )[:12000]

    def _retrieve(self, **query: Any) -> list[dict]:
        result = self.repository.retrieve(**query)
        if isinstance(result, RetrievalBatch):
            self.last_batch = result
        else:
            # Compatibility for callers that inject the deterministic ranker
            # directly (the production path always supplies a repository).
            self.last_batch = RetrievalBatch(
                cards=list(result),
                backend="in-memory",
                dataset_sha256="",
            )
        return self.last_batch.cards

    def retrieval_trace(self) -> dict[str, Any]:
        return self.last_batch.trace() if self.last_batch is not None else {}

    def retrieve_for_component(
        self,
        *,
        component_plan: dict[str, Any],
        component_schema: dict[str, Any] | None,
        interface_plans: list[dict[str, Any]] | None = None,
        max_constraints: int = 24,
        per_family_limit: int = 5,
    ) -> list[dict]:
        schema_tags, paths = self._schema_context(component_schema)
        component_type = str(component_plan.get("type") or "").strip().upper()
        class_tags = set(schema_tags)
        if component_type:
            class_tags.add(component_type)
        semantic_query = {
            "component_type": component_type,
            "class_tags": sorted(class_tags),
            "property_tags": sorted(schema_tags),
            "schema_paths": sorted(paths),
            "interface_types": sorted(
                {
                    str(plan.get("type") or "").strip().upper()
                    for plan in interface_plans or []
                    if str(plan.get("type") or "").strip()
                }
            ),
        }
        return self._retrieve(
            class_tags=sorted(class_tags),
            property_tags=sorted(schema_tags),
            paths=sorted(paths),
            purpose="generation_context",
            query=self._query_text(semantic_query),
            max_constraints=max_constraints,
            per_family_limit=per_family_limit,
        )

    def retrieve_for_interfaces(
        self,
        *,
        interface_plans: list[dict[str, Any]],
        interface_schema: dict[str, Any] | None,
        max_constraints: int = 20,
        per_family_limit: int = 5,
    ) -> list[dict]:
        schema_tags, paths = self._schema_context(interface_schema)
        interface_types = sorted(
            {
                str(plan.get("type") or "").strip().upper()
                for plan in interface_plans
                if str(plan.get("type") or "").strip()
            }
        )
        semantic_query = {
            "interface_types": interface_types,
            "class_tags": sorted(schema_tags),
            "property_tags": sorted(schema_tags),
            "schema_paths": sorted(paths),
        }
        return self._retrieve(
            class_tags=sorted(schema_tags),
            property_tags=sorted(schema_tags),
            paths=sorted(paths),
            purpose="generation_context",
            query=self._query_text(semantic_query),
            max_constraints=max_constraints,
            per_family_limit=per_family_limit,
        )

    @staticmethod
    def render_prompt(cards: list[dict]) -> str:
        if not cards:
            return ""
        lines = [
            "\n\n## Applicable AUTOSAR constraints (ranked V2 context)",
            "Apply these rules when their antecedent exists in the requested model. "
            "MUST/core rules take precedence. Do not create optional structures solely to make a rule applicable.",
        ]
        for card in cards:
            level = card.get("validation_policy", "not_applicable").upper()
            importance = card.get("importance", "supporting").upper()
            family = card.get("rule_family", "other")
            target_text = ", ".join((card.get("paths") or card.get("class_tags") or [])[:3])
            summary = " ".join(str(card.get("summary") or card.get("title") or "").split())
            lines.append(
                f"- [{card['constraint_id']}][{level}][{importance}][{family}] "
                f"{summary} Targets: {target_text or 'global'}."
            )
        return "\n".join(lines)
