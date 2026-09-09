"""Rank the complete candidate set before applying a result limit."""

from __future__ import annotations

import json
import re
from pathlib import Path

TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9_-]{2,}")


def _tokens(value: str) -> set[str]:
    return {item.casefold() for item in TOKEN.findall(value)}


class ConstraintRetrieverV2:
    def __init__(self, cards: list[dict]) -> None:
        self.cards = cards

    @classmethod
    def from_jsonl(cls, path: str | Path) -> "ConstraintRetrieverV2":
        path = Path(path)
        return cls([json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()])

    def retrieve(
        self,
        *,
        class_tags: list[str] | None = None,
        property_tags: list[str] | None = None,
        paths: list[str] | None = None,
        purpose: str = "generation_context",
        query: str = "",
        max_constraints: int = 20,
        per_family_limit: int = 6,
        graph_constraint_ids: set[str] | None = None,
    ) -> list[dict]:
        wanted_classes = set(class_tags or [])
        wanted_properties = set(property_tags or [])
        wanted_paths = set(paths or [])
        query_tokens = _tokens(query)
        graph_matches = graph_constraint_ids or set()
        ranked: list[tuple[int, str, dict, list[str]]] = []

        for card in self.cards:
            score = 0
            reasons: list[str] = []
            exact_paths = wanted_paths.intersection(card["paths"])
            if exact_paths:
                score += 120 + 10 * len(exact_paths)
                reasons.append("exact_path")
            if card["constraint_id"] in graph_matches:
                score += 45
                reasons.append("graph_class_or_property")
            properties = wanted_properties.intersection(card["property_tags"])
            if properties:
                score += 70 + 5 * len(properties)
                reasons.append("property_tag")
            classes = wanted_classes.intersection(card["class_tags"])
            if classes:
                score += 40 + 3 * len(classes)
                reasons.append("class_tag")
            if purpose in card["usages"]:
                score += 25
                reasons.append("purpose")
            if card["validation_policy"] == "must":
                score += 24
                reasons.append("must_validate")
            elif card["validation_policy"] == "should":
                score += 12
            if card["importance"] == "core":
                score += 22
                reasons.append("core")
            elif card["importance"] == "major":
                score += 10
            if card["quality"] == "approved":
                score += 5
            text_tokens = _tokens(card["title"] + " " + card["summary"])
            overlap = query_tokens.intersection(text_tokens)
            if overlap:
                score += min(30, 3 * len(overlap))
                reasons.append("query_terms")
            if score and (
                classes
                or properties
                or exact_paths
                or overlap
                or card["constraint_id"] in graph_matches
            ):
                ranked.append((score, card["constraint_id"], card, reasons))

        ranked.sort(key=lambda item: (-item[0], item[1]))
        selected: list[dict] = []
        family_counts: dict[str, int] = {}
        for score, _, card, reasons in ranked:
            family = card["rule_family"]
            if family_counts.get(family, 0) >= per_family_limit:
                continue
            family_counts[family] = family_counts.get(family, 0) + 1
            selected.append({**card, "retrieval_score": score, "retrieval_reasons": reasons})
            if len(selected) >= max_constraints:
                break
        return selected
