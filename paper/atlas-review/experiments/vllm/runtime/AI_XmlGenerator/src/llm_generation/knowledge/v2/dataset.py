"""Canonical identity for the published constraint-retrieval dataset."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def load_cards(path: str | Path) -> list[dict]:
    source = Path(path)
    cards = [
        json.loads(line)
        for line in source.read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]
    cards.sort(key=lambda item: str(item.get("constraint_id", "")))
    return cards


def retrieval_dataset_sha256(cards: list[dict]) -> str:
    ordered = sorted(cards, key=lambda item: str(item.get("constraint_id", "")))
    return hashlib.sha256(canonical_json(ordered).encode("utf-8")).hexdigest()


def build_retrieval_manifest(cards: list[dict]) -> dict:
    ids = [str(card.get("constraint_id", "")) for card in cards]
    return {
        "schema_version": "2.0",
        "dataset_sha256": retrieval_dataset_sha256(cards),
        "card_count": len(cards),
        "unique_constraint_count": len(set(ids)),
    }


def load_and_validate_manifest(cards_path: str | Path, manifest_path: str | Path) -> tuple[list[dict], dict]:
    cards = load_cards(cards_path)
    actual = build_retrieval_manifest(cards)
    declared = json.loads(Path(manifest_path).read_text(encoding="utf-8-sig"))
    for field in ("schema_version", "dataset_sha256", "card_count", "unique_constraint_count"):
        if declared.get(field) != actual.get(field):
            raise ValueError(
                f"Retrieval manifest mismatch for {field}: "
                f"declared={declared.get(field)!r}, actual={actual.get(field)!r}"
            )
    return cards, declared
