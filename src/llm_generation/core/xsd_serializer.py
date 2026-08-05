"""Deterministic, fail-closed XML projection and XSD-driven serialization."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from xml.etree.ElementTree import Element, SubElement

from src.kg_builder.xsd_enrichment.serialization_manifest import (
    load_serialization_manifest,
)


class XsdSerializationError(ValueError):
    """Raised when JSON cannot be mapped to one unambiguous XSD particle."""


def _normalized_tag(value: object) -> str:
    text = str(value or "").strip()
    if text.startswith("{") and "}" in text:
        text = text.split("}", 1)[1]
    return text.upper()


def _qname_local(value: object) -> str:
    text = str(value or "")
    if text.startswith("{") and "}" in text:
        return text.split("}", 1)[1]
    return text.split(":", 1)[-1]


def _path_value(root: dict[str, Any], path: tuple[str, ...]) -> tuple[bool, Any]:
    current: Any = root
    for part in path:
        if not isinstance(current, dict) or part not in current:
            return False, None
        current = current[part]
    return True, current


def _pop_path(root: dict[str, Any], path: tuple[str, ...]) -> Any:
    if not path:
        raise XsdSerializationError("projection source path cannot be empty")
    current: Any = root
    for part in path[:-1]:
        if not isinstance(current, dict) or part not in current:
            raise XsdSerializationError(f"projection source parent is missing: {'/'.join(path)}")
        current = current[part]
    if not isinstance(current, dict) or path[-1] not in current:
        raise XsdSerializationError(f"projection source is missing: {'/'.join(path)}")
    return current.pop(path[-1])


def _put_path(root: dict[str, Any], path: tuple[str, ...], value: Any) -> None:
    if not path:
        raise XsdSerializationError("projection target path cannot be empty")
    current: dict[str, Any] = root
    for part in path[:-1]:
        existing = current.get(part)
        if existing is None:
            existing = {}
            current[part] = existing
        if not isinstance(existing, dict):
            raise XsdSerializationError(
                f"projection target parent is not an object: {'/'.join(path)}"
            )
        current = existing
    if path[-1] in current:
        raise XsdSerializationError(f"projection target already exists: {'/'.join(path)}")
    current[path[-1]] = value


def apply_projection_map(
    payload: dict[str, Any], projection_map: dict[str, Any] | None
) -> dict[str, Any]:
    """Apply an explicit reversible JSON-to-XML projection in declared order."""
    if not projection_map:
        return payload
    if projection_map.get("schema_version") != "1.0":
        raise XsdSerializationError("unsupported XML projection map schema_version")
    rules = projection_map.get("rules")
    if not isinstance(rules, list):
        raise XsdSerializationError("XML projection map rules must be an array")
    for index, rule in enumerate(rules):
        if not isinstance(rule, dict):
            raise XsdSerializationError(f"XML projection rule {index} is not an object")
        source = tuple(str(item) for item in rule.get("source") or [])
        target = tuple(str(item) for item in rule.get("target") or [])
        if not source or not target or source == target:
            raise XsdSerializationError(f"XML projection rule {index} has invalid paths")
        source_exists, _ = _path_value(payload, source)
        target_exists, _ = _path_value(payload, target)
        if source_exists and target_exists:
            raise XsdSerializationError(
                f"both flattened and canonical XML paths exist: {'/'.join(source)}, {'/'.join(target)}"
            )
        if not source_exists:
            # Already-canonical payloads are accepted; absent optional sections
            # require no projection.  No alternative ordering strategy is used.
            continue
        value = _pop_path(payload, source)
        _put_path(payload, target, value)
    return payload


def _multiply_max(left: int | str, right: object) -> int | str:
    if left == "unbounded" or right == "unbounded":
        return "unbounded"
    try:
        return int(left) * int(right if right is not None else 1)
    except (TypeError, ValueError) as error:
        raise XsdSerializationError(f"invalid XSD maxOccurs value: {right!r}") from error


@dataclass(frozen=True)
class _ChoiceUse:
    particle_id: str
    branch: int
    effective_max: int | str


@dataclass(frozen=True)
class _ElementSlot:
    ordinal: int
    particle_id: str
    path: str
    element_name: str
    type_qname: str | None
    ref_qname: str | None
    anonymous_owner_id: str | None
    effective_max: int | str
    choices: tuple[_ChoiceUse, ...]


class DeterministicXsdSerializer:
    """Serialize unordered JSON by walking one exact XSD owner graph."""

    def __init__(self, manifest: dict[str, Any]) -> None:
        self.manifest = manifest
        self.manifest_sha256 = str(manifest.get("manifest_sha256") or "")
        self._owners: dict[str, dict[str, Any]] = dict(manifest.get("owners") or {})
        self._complex_types: dict[str, str] = {
            _normalized_tag(key): str(value)
            for key, value in (manifest.get("named_complex_types") or {}).items()
        }
        self._global_elements: dict[str, dict[str, Any]] = {
            _normalized_tag(key): value
            for key, value in (manifest.get("global_elements") or {}).items()
            if isinstance(value, dict)
        }
        self._slot_cache: dict[str, tuple[_ElementSlot, ...]] = {}

    @classmethod
    def from_files(
        cls, manifest_path: str | Path, *, xsd_path: str | Path
    ) -> "DeterministicXsdSerializer":
        return cls(load_serialization_manifest(manifest_path, xsd_path=xsd_path))

    def _owner(self, owner_id: str) -> dict[str, Any]:
        owner = self._owners.get(owner_id)
        if not isinstance(owner, dict):
            raise XsdSerializationError(f"XSD owner is missing from manifest: {owner_id}")
        return owner

    def _owner_for_type(self, type_qname: object) -> str | None:
        return self._complex_types.get(_normalized_tag(_qname_local(type_qname)))

    def owner_for_root(self, element_name: str) -> str:
        key = _normalized_tag(element_name)
        global_element = self._global_elements.get(key)
        if global_element:
            owner_id = self._owner_for_type(global_element.get("type_qname"))
            if owner_id:
                return owner_id
            raise XsdSerializationError(
                f"global element {element_name!r} has no resolvable complex type"
            )
        owner_id = self._complex_types.get(key)
        if owner_id:
            return owner_id
        raise XsdSerializationError(f"no XSD root owner for element {element_name!r}")

    def _slots_for_owner(self, owner_id: str) -> tuple[_ElementSlot, ...]:
        cached = self._slot_cache.get(owner_id)
        if cached is not None:
            return cached
        slots: list[_ElementSlot] = []

        def walk_owner(
            current_owner_id: str,
            *,
            owner_stack: tuple[str, ...],
            max_multiplier: int | str,
            choices: tuple[_ChoiceUse, ...],
        ) -> None:
            if current_owner_id in owner_stack:
                raise XsdSerializationError(
                    "cyclic XSD owner expansion: " + " -> ".join((*owner_stack, current_owner_id))
                )
            model = self._owner(current_owner_id).get("model")
            if isinstance(model, dict):
                walk(
                    model,
                    owner_stack=(*owner_stack, current_owner_id),
                    max_multiplier=max_multiplier,
                    choices=choices,
                )

        def walk(
            node: dict[str, Any],
            *,
            owner_stack: tuple[str, ...],
            max_multiplier: int | str,
            choices: tuple[_ChoiceUse, ...],
        ) -> None:
            kind = str(node.get("kind") or "")
            effective_max = _multiply_max(max_multiplier, node.get("max_occurs", 1))
            if kind == "element":
                element_name = str(node.get("element_name") or node.get("name") or "").strip()
                if not element_name:
                    raise XsdSerializationError(
                        f"unnamed XSD element particle {node.get('particle_id')}"
                    )
                slots.append(
                    _ElementSlot(
                        ordinal=len(slots),
                        particle_id=str(node.get("particle_id") or ""),
                        path=str(node.get("path") or ""),
                        element_name=element_name,
                        type_qname=(str(node["type_qname"]) if node.get("type_qname") else None),
                        ref_qname=(str(node["ref_qname"]) if node.get("ref_qname") else None),
                        anonymous_owner_id=(
                            str(node["anonymous_owner_id"])
                            if node.get("anonymous_owner_id")
                            else None
                        ),
                        effective_max=effective_max,
                        choices=choices,
                    )
                )
                return
            if kind == "group-ref":
                target = str(node.get("resolved_owner_id") or "")
                if not target:
                    raise XsdSerializationError(
                        f"unresolved group particle {node.get('particle_id')}"
                    )
                walk_owner(
                    target,
                    owner_stack=owner_stack,
                    max_multiplier=effective_max,
                    choices=choices,
                )
                return
            if kind in {"extension", "restriction"} and node.get("content_kind") == "complex-content":
                base = str(node.get("resolved_base_owner_id") or "")
                if not base:
                    raise XsdSerializationError(
                        f"unresolved base particle {node.get('particle_id')}"
                    )
                walk_owner(
                    base,
                    owner_stack=owner_stack,
                    max_multiplier=max_multiplier,
                    choices=choices,
                )
            children = [child for child in node.get("children") or [] if isinstance(child, dict)]
            if kind == "choice":
                choice_id = str(node.get("particle_id") or node.get("path") or "choice")
                for branch, child in enumerate(children):
                    walk(
                        child,
                        owner_stack=owner_stack,
                        max_multiplier=effective_max,
                        choices=(*choices, _ChoiceUse(choice_id, branch, effective_max)),
                    )
                return
            for child in children:
                walk(
                    child,
                    owner_stack=owner_stack,
                    max_multiplier=effective_max,
                    choices=choices,
                )

        walk_owner(owner_id, owner_stack=(), max_multiplier=1, choices=())
        result = tuple(slots)
        self._slot_cache[owner_id] = result
        return result

    @staticmethod
    def _normal_children(data: dict[str, Any], skip_keys: Iterable[str]) -> list[tuple[str, Any]]:
        skipped = set(skip_keys)
        return [
            (key, value)
            for key, value in data.items()
            if key not in skipped and not key.startswith("_") and not key.startswith("@") and key != "#text"
        ]

    def _ordered_children(
        self,
        data: dict[str, Any],
        owner_id: str,
        *,
        skip_keys: Iterable[str] = (),
    ) -> list[tuple[str, Any, _ElementSlot]]:
        by_tag: dict[str, list[_ElementSlot]] = {}
        for slot in self._slots_for_owner(owner_id):
            by_tag.setdefault(_normalized_tag(slot.element_name), []).append(slot)

        ordered: list[tuple[str, Any, _ElementSlot]] = []
        choice_branches: dict[str, tuple[int | str, set[int]]] = {}
        for key, value in self._normal_children(data, skip_keys):
            candidates = by_tag.get(_normalized_tag(key)) or []
            if not candidates:
                raise XsdSerializationError(
                    f"element {key!r} is not allowed by XSD owner {owner_id}"
                )
            unique = {candidate.particle_id: candidate for candidate in candidates}
            if len(unique) != 1:
                paths = ", ".join(sorted(candidate.path for candidate in unique.values()))
                raise XsdSerializationError(
                    f"element {key!r} maps to multiple XSD particles under {owner_id}: {paths}"
                )
            slot = next(iter(unique.values()))
            count = len(value) if isinstance(value, list) else 1
            if slot.effective_max != "unbounded" and count > int(slot.effective_max):
                raise XsdSerializationError(
                    f"element {key!r} occurs {count} times, exceeding XSD maxOccurs={slot.effective_max}"
                )
            for choice in slot.choices:
                maximum, branches = choice_branches.setdefault(
                    choice.particle_id, (choice.effective_max, set())
                )
                branches.add(choice.branch)
                choice_branches[choice.particle_id] = (maximum, branches)
            ordered.append((key, value, slot))

        for particle_id, (maximum, branches) in choice_branches.items():
            if maximum == 1 and len(branches) > 1:
                raise XsdSerializationError(
                    f"multiple branches selected for single-occurrence XSD choice {particle_id}"
                )
        return sorted(ordered, key=lambda item: item[2].ordinal)

    def _child_owner(self, slot: _ElementSlot) -> str | None:
        if slot.anonymous_owner_id:
            self._owner(slot.anonymous_owner_id)
            return slot.anonymous_owner_id
        if slot.type_qname:
            return self._owner_for_type(slot.type_qname)
        if slot.ref_qname:
            global_element = self._global_elements.get(_normalized_tag(_qname_local(slot.ref_qname)))
            if global_element:
                return self._owner_for_type(global_element.get("type_qname"))
        return None

    @staticmethod
    def _has_element_children(value: dict[str, Any]) -> bool:
        return any(
            not key.startswith("_") and not key.startswith("@") and key != "#text"
            for key in value
        )

    def _append_value(
        self,
        parent: Element,
        key: str,
        value: Any,
        slot: _ElementSlot,
    ) -> None:
        values = value if isinstance(value, list) else [value]
        child_owner_id = self._child_owner(slot)
        for item in values:
            child = SubElement(parent, key)
            if isinstance(item, dict):
                for attr_key, attr_value in item.items():
                    if attr_key.startswith("@"):
                        child.set(attr_key[1:], str(attr_value))
                if "#text" in item:
                    child.text = str(item["#text"])
                if self._has_element_children(item):
                    if not child_owner_id:
                        raise XsdSerializationError(
                            f"complex value for {key!r} has no exact XSD owner (particle {slot.particle_id})"
                        )
                    self.append_payload(child, item, owner_id=child_owner_id)
            elif item is not None:
                child.text = str(item)

    def append_payload(
        self,
        parent: Element,
        data: dict[str, Any],
        *,
        root_element: str | None = None,
        owner_id: str | None = None,
        skip_keys: Iterable[str] = (),
    ) -> None:
        if not isinstance(data, dict):
            raise XsdSerializationError("XML payload must be an object")
        resolved_owner = owner_id or self.owner_for_root(root_element or parent.tag)
        for key, value, slot in self._ordered_children(
            data, resolved_owner, skip_keys=skip_keys
        ):
            self._append_value(parent, key, value, slot)
