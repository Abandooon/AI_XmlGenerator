"""Fail-closed indexes over enriched AUTOSAR XSD content models."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from xml.etree import ElementTree


class XsdContentIndexError(ValueError):
    """An XSD content model cannot be reduced to an unambiguous tag index."""


@dataclass(frozen=True)
class XsdOccurrence:
    min_occurs: int
    max_occurs: int | None


def _bound(value: object, *, maximum: bool) -> int | None:
    if maximum and str(value).strip().lower() in {"unbounded", "inf", "infinite", "-1"}:
        return None
    try:
        result = int(value)
    except (TypeError, ValueError) as error:
        raise XsdContentIndexError(f"invalid XSD occurrence bound: {value!r}") from error
    if result < 0:
        raise XsdContentIndexError(f"negative XSD occurrence bound: {value!r}")
    return result


def _multiply_max(left: int | None, right: int | None) -> int | None:
    if left is None or right is None:
        return None
    return left * right


def content_occurrence_index(model: object) -> dict[str, XsdOccurrence]:
    """Return effective XSD occurrences keyed by exact XML element tag.

    Inherited groups are already expanded in the enriched model and are walked
    recursively.  A branch-specific element under a multi-branch choice has a
    lower bound of zero.  Duplicate tag particles are rejected because a
    tag-only Phase 2 schema cannot represent their positional distinction.
    """
    if not isinstance(model, dict):
        raise XsdContentIndexError("XSD content model must be an object")
    occurrences: dict[str, XsdOccurrence] = {}

    def walk(node: object, parent_min: int, parent_max: int | None) -> None:
        if not isinstance(node, dict):
            raise XsdContentIndexError("XSD content-model particle must be an object")
        minimum = _bound(node.get("min_occurs", 1), maximum=False)
        maximum = _bound(node.get("max_occurs", 1), maximum=True)
        assert minimum is not None
        effective_min = parent_min * minimum
        effective_max = _multiply_max(parent_max, maximum)
        kind = str(node.get("kind") or "")
        if kind == "element":
            tag = str(node.get("element_name") or node.get("name") or "").strip().upper()
            if not tag:
                raise XsdContentIndexError("XSD element particle is unnamed")
            if tag in occurrences:
                raise XsdContentIndexError(f"duplicate XSD element particle for tag {tag}")
            occurrences[tag] = XsdOccurrence(effective_min, effective_max)
            return

        base_model = node.get("base_model")
        if base_model is not None:
            walk(base_model, effective_min, effective_max)
        children = node.get("children") or []
        if not isinstance(children, list):
            raise XsdContentIndexError("XSD content-model children must be an array")
        branch_min = 0 if kind == "choice" and len(children) > 1 else effective_min
        for child in children:
            walk(child, branch_min, effective_max)

    walk(model, 1, 1)
    return occurrences


def load_text_content_type_index(
    xsd_path: str | Path, *, expected_sha256: str
) -> frozenset[str]:
    """Load hash-pinned complex types that can carry direct text content."""
    path = Path(xsd_path)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != expected_sha256:
        raise XsdContentIndexError(
            f"XSD hash mismatch: expected {expected_sha256}, got {digest}"
        )
    root = ElementTree.parse(path).getroot()
    namespace = "{http://www.w3.org/2001/XMLSchema}"
    result: set[str] = set()
    for complex_type in root.findall(f"{namespace}complexType"):
        name = str(complex_type.get("name") or "").strip().upper()
        if not name:
            continue
        if str(complex_type.get("mixed") or "").lower() == "true":
            result.add(name)
            continue
        if complex_type.find(f"{namespace}simpleContent") is not None:
            result.add(name)
    return frozenset(result)
