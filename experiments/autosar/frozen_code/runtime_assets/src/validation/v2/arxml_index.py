"""Namespace-agnostic ARXML document and reference index."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from lxml import etree


def local_name(tag: object) -> str:
    if not isinstance(tag, str):
        return ""
    return tag.rsplit("}", 1)[-1]


def normalized_ref(value: str | None) -> str:
    if not value:
        return ""
    parts = [part for part in value.strip().replace("\\", "/").split("/") if part]
    return "/" + "/".join(parts)


@dataclass(frozen=True)
class Resolution:
    status: str
    reference: str
    element: etree._Element | None
    candidates: tuple[etree._Element, ...] = ()


class ArxmlIndex:
    def __init__(self, paths: list[Path]) -> None:
        if not paths:
            raise ValueError("At least one ARXML file is required")
        self.paths = [path.resolve() for path in paths]
        self.trees: list[etree._ElementTree] = []
        self.roots: list[etree._Element] = []
        self.parent: dict[etree._Element, etree._Element] = {}
        self.file_by_element: dict[etree._Element, Path] = {}
        self.by_tag: dict[str, list[etree._Element]] = defaultdict(list)
        self.by_path: dict[str, list[etree._Element]] = defaultdict(list)
        self.by_short_name: dict[str, list[etree._Element]] = defaultdict(list)
        parser = etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=True)
        for path in self.paths:
            tree = etree.parse(str(path), parser)
            root = tree.getroot()
            self.trees.append(tree)
            self.roots.append(root)
            for element in root.iter():
                if not isinstance(element.tag, str):
                    continue
                self.file_by_element[element] = path
                self.by_tag[local_name(element.tag)].append(element)
                for child in element:
                    if isinstance(child.tag, str):
                        self.parent[child] = element
        self._build_reference_index()

    def _direct_short_name(self, element: etree._Element) -> str | None:
        for child in element:
            if local_name(child.tag) == "SHORT-NAME" and child.text and child.text.strip():
                return child.text.strip()
        return None

    def _build_reference_index(self) -> None:
        for element in self.file_by_element:
            name = self._direct_short_name(element)
            if not name:
                continue
            self.by_short_name[name].append(element)
            names: list[str] = []
            current: etree._Element | None = element
            while current is not None:
                current_name = self._direct_short_name(current)
                if current_name:
                    names.append(current_name)
                current = self.parent.get(current)
            path = normalized_ref("/".join(reversed(names)))
            self.by_path[path].append(element)

    def elements(self, tag: str) -> list[etree._Element]:
        return self.by_tag.get(tag, [])

    def select_any(self, tags: list[str]) -> list[etree._Element]:
        seen: set[int] = set()
        result: list[etree._Element] = []
        for tag in tags:
            for element in self.elements(tag):
                marker = id(element)
                if marker not in seen:
                    seen.add(marker)
                    result.append(element)
        return result

    def descendants(self, element: etree._Element, tags: set[str] | None = None) -> list[etree._Element]:
        values = [item for item in element.iterdescendants() if isinstance(item.tag, str)]
        return values if tags is None else [item for item in values if local_name(item.tag) in tags]

    def first_descendant(self, element: etree._Element, tags: set[str]) -> etree._Element | None:
        return next((item for item in element.iterdescendants() if local_name(item.tag) in tags), None)

    def nearest(self, element: etree._Element, tags: set[str]) -> etree._Element | None:
        current = element
        while current is not None:
            if local_name(current.tag) in tags:
                return current
            current = self.parent.get(current)
        return None

    def resolve(self, reference_or_element: str | etree._Element) -> Resolution:
        if isinstance(reference_or_element, str):
            raw = reference_or_element
        else:
            raw = reference_or_element.text or ""
        reference = normalized_ref(raw)
        if not reference:
            return Resolution("missing", reference, None)
        exact = tuple(self.by_path.get(reference, []))
        if len(exact) == 1:
            return Resolution("resolved", reference, exact[0], exact)
        if len(exact) > 1:
            return Resolution("ambiguous", reference, None, exact)
        short_name = reference.rsplit("/", 1)[-1]
        candidates = tuple(self.by_short_name.get(short_name, []))
        suffix = tuple(item for item in candidates if self.path_of(item).endswith(reference))
        if len(suffix) == 1:
            return Resolution("resolved", reference, suffix[0], suffix)
        if len(suffix) > 1:
            return Resolution("ambiguous", reference, None, suffix)
        return Resolution("unresolved", reference, None, candidates)

    def path_of(self, element: etree._Element) -> str:
        name = self._direct_short_name(element)
        if name:
            names: list[str] = []
            current: etree._Element | None = element
            while current is not None:
                current_name = self._direct_short_name(current)
                if current_name:
                    names.append(current_name)
                current = self.parent.get(current)
            return normalized_ref("/".join(reversed(names)))
        parent = self.parent.get(element)
        base = self.path_of(parent) if parent is not None else ""
        return f"{base}/{local_name(element.tag)}" or "/"

    def location(self, element: etree._Element) -> dict:
        path = self.file_by_element.get(element)
        return {
            "file": str(path) if path else None,
            "line": element.sourceline,
            "xml_path": self.path_of(element),
            "tag": local_name(element.tag),
        }
