"""Typed patch IR and deterministic editor for validated ARXML repair.

Repair operates on the structured payload that precedes XML rendering, so a
repaired artifact inherits every guarantee the generation stage establishes:

* path realizability against the pinned XSD,
* provider-schema compliance,
* requirement-owned constants that cannot be rewritten,
* XSD-driven element tags and sibling order.

The model never writes a path and never writes XML.  The program derives the
candidate locations from the validation finding, the model selects an
enumerated candidate plus an operation, and values are always produced under a
sub-schema derived from the same XSD-backed component schema.  Every stage is
fail-closed: a patch set is applied in full or rejected in full.
"""

from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from dataclasses import dataclass, field, replace as dataclass_replace
from typing import Any, Iterable
from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement, fromstring, tostring

from jsonschema import Draft202012Validator

from ..knowledge.element_selection import (
    ElementSelectionError,
    materialize_deterministic_values,
    subschema_at_path,
)
from src.validation.v2.repair_loop import CoverageLossWaiver, RepairProposal

from ..knowledge.xsd_selection_paths import (
    PinnedXsdSelectionPathIndex,
    XsdSelectionPathError,
)
from .xsd_serializer import (
    DeterministicXsdSerializer,
    XsdSerializationError,
    apply_projection_map,
    canonical_path_to_source,
)

COMPONENT_PACKAGE = "Components"
INTERFACE_PACKAGE = "COM_Interface"
AUTOSAR_NAMESPACE = "http://autosar.org/schema/r4.0"
XSI_NAMESPACE = "http://www.w3.org/2001/XMLSchema-instance"
SCHEMA_LOCATION = f"{AUTOSAR_NAMESPACE} AUTOSAR_4-2-2.xsd"

SET_VALUE = "set_value"
INSERT_ELEMENT = "insert_element"
REMOVE_ELEMENT = "remove_element"
RESTORE_XSD_ORDER = "restore_xsd_order"
RESTORE_PINNED_VALUE = "restore_pinned_value"
OPERATIONS = (
    SET_VALUE,
    INSERT_ELEMENT,
    REMOVE_ELEMENT,
    RESTORE_XSD_ORDER,
    RESTORE_PINNED_VALUE,
)

REPAIR_CONTEXT_SCHEMA_VERSION = "atlas.typed_repair_context.v1"

# ``attempt_outcome`` values owned by the deterministic editor.  The repair loop
# owns the outcomes that depend on revalidation.
REJECTED_PATH_UNRESOLVABLE = "rejected_path_unresolvable"
REJECTED_IMMUTABLE_VALUE = "rejected_immutable_value"
REJECTED_OCCURRENCE_VIOLATION = "rejected_occurrence_violation"
REJECTED_SCHEMA_VIOLATION = "rejected_schema_violation"
REJECTED_RENDER_FAILURE = "rejected_render_failure"
REJECTED_CONFLICTING_PATCHES = "rejected_conflicting_patches"
REJECTED_MALFORMED_PATCH = "rejected_malformed_patch"

# ``automation_boundary_reason`` values (orthogonal to the outcome above).
BOUNDARY_NONE = "none"
BOUNDARY_NOT_LOCALIZABLE = "not_localizable"
BOUNDARY_NO_APPLICABLE_OPERATION = "no_applicable_operation"

_XML_PREFIX = ("AUTOSAR", "AR-PACKAGES", "AR-PACKAGE", "ELEMENTS")
_PREDICATE = re.compile(r"\[([^\]]*)\]")
_IDENTITY_TAGS = frozenset({"SHORT-NAME", "SHORTNAME"})


class TypedRepairError(ValueError):
    """Raised when a typed repair cannot be produced or applied."""

    def __init__(self, message: str, *, outcome: str = REJECTED_MALFORMED_PATCH) -> None:
        super().__init__(message)
        self.outcome = outcome


@dataclass(frozen=True)
class XsdGuard:
    """The two pinned XSD views a typed repair must satisfy.

    ``path_index`` answers "can this path exist at all"; ``serializer``
    answers "how many times may it exist here", using the same effective
    bounds it will later enforce while rendering.
    """

    path_index: PinnedXsdSelectionPathIndex
    serializer: DeterministicXsdSerializer

    def path_is_realizable(self, element_type: str, segments: list[str]) -> bool:
        if not segments:
            return False
        try:
            self.path_index.validate_path(element_type, segments)
        except XsdSelectionPathError:
            return False
        return True

    def require_realizable(self, element_type: str, segments: list[str]) -> None:
        if not segments:
            return
        try:
            self.path_index.validate_path(element_type, segments)
        except XsdSelectionPathError as error:
            raise TypedRepairError(
                f"repair path is not realizable in the pinned XSD: {error}",
                outcome=REJECTED_PATH_UNRESOLVABLE,
            ) from error

    def bounds(self, element_type: str, tag_path: tuple[str, ...]) -> tuple[int, int | None]:
        try:
            return self.serializer.element_bounds(element_type, list(tag_path))
        except XsdSerializationError as error:
            raise TypedRepairError(
                f"no XSD occurrence bounds for {'/'.join(tag_path)}: {error}",
                outcome=REJECTED_PATH_UNRESOLVABLE,
            ) from error

    def required_choice_groups(
        self, element_type: str, tag_path: tuple[str, ...]
    ) -> tuple[frozenset[str], ...]:
        try:
            return self.serializer.required_choice_groups(element_type, list(tag_path))
        except XsdSerializationError as error:
            raise TypedRepairError(
                f"no XSD choice model for {'/'.join(tag_path)}: {error}",
                outcome=REJECTED_PATH_UNRESOLVABLE,
            ) from error


def _short_name(value: Any) -> str:
    if not isinstance(value, dict):
        return ""
    raw = value.get("SHORT-NAME")
    if isinstance(raw, str):
        return raw.strip()
    if isinstance(raw, dict):
        text = raw.get("#text")
        if isinstance(text, str):
            return text.strip()
    return ""


def _is_scalar(value: Any) -> bool:
    return isinstance(value, (str, int, float, bool)) or value is None


def _element_items(value: Any) -> list[tuple[str, Any]]:
    """Return the element-bearing children of a payload node in payload order."""
    if not isinstance(value, dict):
        return []
    return [
        (key, child)
        for key, child in value.items()
        if not key.startswith("_") and not key.startswith("@") and key != "#text"
    ]


def _normalized_instance_path(*parts: str) -> str:
    segments = [
        segment
        for part in parts
        for segment in str(part or "").replace("\\", "/").split("/")
        if segment
    ]
    return "/" + "/".join(segments)


@dataclass(frozen=True)
class PayloadNode:
    """One XML element as it exists in the canonical (post-projection) payload."""

    json_path: tuple[Any, ...]
    tag_path: tuple[str, ...]
    tag: str
    short_name: str
    value: Any
    instance_path: str
    segment_short_names: tuple[str, ...]
    segment_positions: tuple[int, ...]


class PayloadLocator:
    """Resolve a validation finding's ``xml_path`` to concrete payload nodes.

    Three producers spell locations differently and all three are honoured
    exactly rather than approximately:

    ``ArxmlIndex.path_of``
        instance path built from SHORT-NAME chains, container tags collapsed;
    libxml2 ``xmlGetNodePath`` (XSD findings)
        full tag path with a positional predicate only where siblings repeat;
    ``selection_obligations``
        component-rooted tag path with ``[SHORT-NAME=...]`` on anchored steps.

    A path that does not resolve is reported as ``not_localizable`` and never
    guessed at.
    """

    def __init__(self, payload: dict[str, Any], *, element_type: str, package: str) -> None:
        self.element_type = str(element_type)
        self.package = str(package)
        self.nodes: list[PayloadNode] = []
        self._by_instance: dict[str, list[PayloadNode]] = {}
        self._by_tag_path: dict[tuple[str, ...], list[PayloadNode]] = {}
        self._index(payload)

    def _record(self, node: PayloadNode) -> None:
        self.nodes.append(node)
        self._by_instance.setdefault(node.instance_path, []).append(node)
        self._by_tag_path.setdefault(node.tag_path, []).append(node)

    def _index(self, payload: dict[str, Any]) -> None:
        root_short = _short_name(payload)
        if root_short:
            named_path = _normalized_instance_path(self.package, root_short)
            instance_path = named_path
        else:
            named_path = _normalized_instance_path(self.package)
            instance_path = f"{named_path}/ELEMENTS/{self.element_type}"
        root = PayloadNode(
            json_path=(),
            tag_path=(self.element_type,),
            tag=self.element_type,
            short_name=root_short,
            value=payload,
            instance_path=instance_path,
            segment_short_names=(root_short,),
            segment_positions=(1,),
        )
        self._record(root)
        self._index_children(root, named_path)

    def _index_children(self, parent: PayloadNode, parent_named_path: str) -> None:
        for key, value in _element_items(parent.value):
            occurrences = value if isinstance(value, list) else [value]
            for position, item in enumerate(occurrences):
                json_path = (
                    parent.json_path + (key, position)
                    if isinstance(value, list)
                    else parent.json_path + (key,)
                )
                short = _short_name(item)
                if short:
                    named_path = _normalized_instance_path(parent_named_path, short)
                    instance_path = named_path
                else:
                    named_path = parent_named_path
                    instance_path = f"{parent.instance_path}/{key}"
                node = PayloadNode(
                    json_path=json_path,
                    tag_path=parent.tag_path + (key,),
                    tag=key,
                    short_name=short,
                    value=item,
                    instance_path=instance_path,
                    segment_short_names=parent.segment_short_names + (short,),
                    segment_positions=parent.segment_positions + (position + 1,),
                )
                self._record(node)
                if isinstance(item, dict):
                    self._index_children(node, named_path)

    @staticmethod
    def _parse(path_text: str) -> tuple[list[tuple[str, str, int | None]], str | None]:
        """Split a spelled XML path into steps plus an optional value leaf."""
        raw = str(path_text or "").replace("\\", "/").strip()
        parts = [part for part in raw.split("/") if part]
        if not parts:
            return [], None
        leaf: str | None = None
        last = parts[-1]
        if last == "#text" or last == "#TEXT":
            leaf = "#text"
            parts = parts[:-1]
        elif last.startswith("@"):
            leaf = last
            parts = parts[:-1]
        steps: list[tuple[str, str, int | None]] = []
        for part in parts:
            predicates = _PREDICATE.findall(part)
            name = _PREDICATE.sub("", part).strip()
            short = ""
            position: int | None = None
            for predicate in predicates:
                text = predicate.strip()
                if text.upper().startswith("SHORT-NAME="):
                    short = text.split("=", 1)[1].strip()
                elif text.isdigit():
                    position = int(text)
                else:
                    return [], None
            if not name:
                return [], None
            steps.append((name, short, position))
        return steps, leaf

    def resolve(self, xml_path: str) -> tuple[list[PayloadNode], str | None]:
        """Return the nodes a spelled path denotes, plus its value-leaf hint."""
        steps, leaf = self._parse(xml_path)
        if not steps:
            return [], leaf
        names = [step[0] for step in steps]
        if tuple(names[: len(_XML_PREFIX)]) == _XML_PREFIX:
            steps = steps[len(_XML_PREFIX):]
            names = names[len(_XML_PREFIX):]
        if not steps:
            return [], leaf
        if names[0].upper() == self.element_type.upper():
            tag_path = (self.element_type, *names[1:])
            matches = list(self._by_tag_path.get(tag_path, []))
            for index, (_name, short, position) in enumerate(steps):
                if short:
                    matches = [
                        node for node in matches if node.segment_short_names[index] == short
                    ]
                if position is not None:
                    matches = [
                        node for node in matches if node.segment_positions[index] == position
                    ]
            return matches, leaf
        if any(short or position is not None for _name, short, position in steps):
            return [], leaf
        return list(self._by_instance.get(_normalized_instance_path(*names), [])), leaf


@dataclass(frozen=True)
class RepairCandidate:
    """One enumerated, XSD-legal edit location offered to the model."""

    op: str
    json_path: tuple[Any, ...]
    source_path: tuple[Any, ...]
    tag_path: tuple[str, ...]
    label: str
    leaf: str | None = None
    child_tag: str | None = None
    parent_json_path: tuple[Any, ...] = ()
    parent_source_path: tuple[Any, ...] = ()
    is_array_member: bool = False


@dataclass
class RepairTarget:
    """Everything needed to repair one generated document at the value layer."""

    kind: str
    name: str
    element_type: str
    payload: dict[str, Any]
    root_schema: dict[str, Any]
    document_schema: dict[str, Any] | None = None
    declared_value_design: Any = None
    projection_map: dict[str, Any] | None = None
    immutable_paths: tuple[tuple[Any, ...], ...] = ()
    package_name: str | None = None

    @property
    def package(self) -> str:
        return self.package_name or (
            COMPONENT_PACKAGE if self.kind == "components" else INTERFACE_PACKAGE
        )

    def canonical_payload(self) -> dict[str, Any]:
        return apply_projection_map(deepcopy(self.payload), self.projection_map)

    def locator(self) -> PayloadLocator:
        return PayloadLocator(
            self.canonical_payload(),
            element_type=self.element_type,
            package=self.package,
        )

    def revalidate(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Re-run the generation-stage value contract over a patched payload.

        Components re-run deterministic materialization, which both re-asserts
        every requirement-owned constant and revalidates the authoritative full
        schema.  Interfaces have no materialization stage, so their schema is
        validated directly.
        """
        if self.kind == "components":
            if self.document_schema is None:
                raise TypedRepairError(
                    f"component {self.name} has no authoritative schema",
                    outcome=REJECTED_SCHEMA_VIOLATION,
                )
            try:
                materialized, _audit = materialize_deterministic_values(
                    {self.element_type: payload},
                    self.document_schema,
                    self.declared_value_design,
                )
            except ElementSelectionError as error:
                raise TypedRepairError(
                    f"patched {self.kind}/{self.name} violates the value contract: {error}",
                    outcome=REJECTED_SCHEMA_VIOLATION,
                ) from error
            return materialized[self.element_type]
        errors = sorted(
            Draft202012Validator(self.root_schema).iter_errors(payload),
            key=lambda error: list(error.absolute_path),
        )
        if errors:
            location = "/".join(str(item) for item in errors[0].absolute_path) or "<root>"
            raise TypedRepairError(
                f"patched {self.kind}/{self.name} violates its schema at {location}: "
                f"{errors[0].message}",
                outcome=REJECTED_SCHEMA_VIOLATION,
            )
        return payload


def _canonical_sha256(value: Any) -> str:
    text = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _target_record(target: RepairTarget) -> dict[str, Any]:
    return {
        "kind": target.kind,
        "name": target.name,
        "element_type": target.element_type,
        "payload": deepcopy(target.payload),
        "root_schema": deepcopy(target.root_schema),
        "document_schema": deepcopy(target.document_schema),
        "declared_value_design": deepcopy(target.declared_value_design),
        "projection_map": deepcopy(target.projection_map),
        "immutable_paths": [list(path) for path in target.immutable_paths],
        "package_name": target.package_name,
    }


def _target_from_record(record: Any, *, position: int) -> RepairTarget:
    if not isinstance(record, dict):
        raise TypedRepairError(f"repair context target {position} must be an object")
    legacy_required = {
        "kind",
        "name",
        "element_type",
        "payload",
        "root_schema",
        "document_schema",
        "declared_value_design",
        "projection_map",
        "immutable_paths",
    }
    required = {*legacy_required, "package_name"}
    if frozenset(record) not in {frozenset(legacy_required), frozenset(required)}:
        raise TypedRepairError(
            f"repair context target {position} fields differ from the contract"
        )
    kind = record.get("kind")
    name = record.get("name")
    element_type = record.get("element_type")
    payload = record.get("payload")
    root_schema = record.get("root_schema")
    document_schema = record.get("document_schema")
    projection_map = record.get("projection_map")
    immutable_paths = record.get("immutable_paths")
    if kind not in {"components", "interfaces"}:
        raise TypedRepairError(f"repair context target {position} has invalid kind")
    if not isinstance(name, str) or not name:
        raise TypedRepairError(f"repair context target {position} has no name")
    if not isinstance(element_type, str) or not element_type:
        raise TypedRepairError(f"repair context target {position} has no element type")
    if not isinstance(payload, dict) or not isinstance(root_schema, dict):
        raise TypedRepairError(
            f"repair context target {position} payload/schema must be objects"
        )
    if document_schema is not None and not isinstance(document_schema, dict):
        raise TypedRepairError(
            f"repair context target {position} document schema must be an object or null"
        )
    if projection_map is not None and not isinstance(projection_map, dict):
        raise TypedRepairError(
            f"repair context target {position} projection map must be an object or null"
        )
    if not isinstance(immutable_paths, list) or any(
        not isinstance(path, list) for path in immutable_paths
    ):
        raise TypedRepairError(
            f"repair context target {position} immutable paths must be arrays"
        )
    return RepairTarget(
        kind=kind,
        name=name,
        element_type=element_type,
        payload=deepcopy(payload),
        root_schema=deepcopy(root_schema),
        document_schema=deepcopy(document_schema),
        declared_value_design=deepcopy(record.get("declared_value_design")),
        projection_map=deepcopy(projection_map),
        immutable_paths=tuple(tuple(path) for path in immutable_paths),
        package_name=(
            str(record["package_name"])
            if record.get("package_name") is not None
            else None
        ),
    )


def _get_path(payload: Any, path: Iterable[Any]) -> tuple[bool, Any]:
    current = payload
    for segment in path:
        if isinstance(segment, int):
            if not isinstance(current, list) or segment >= len(current):
                return False, None
            current = current[segment]
            continue
        if not isinstance(current, dict) or segment not in current:
            return False, None
        current = current[segment]
    return True, current


def _parent_of(payload: Any, path: tuple[Any, ...]) -> Any:
    found, parent = _get_path(payload, path[:-1])
    if not found:
        raise TypedRepairError(
            f"patch parent does not exist: {_format_path(path)}",
            outcome=REJECTED_PATH_UNRESOLVABLE,
        )
    return parent


def _format_path(path: Iterable[Any]) -> str:
    return "/".join(str(segment) for segment in path) or "<root>"


def _set_path(payload: Any, path: tuple[Any, ...], value: Any) -> None:
    parent = _parent_of(payload, path)
    last = path[-1]
    if isinstance(last, int):
        if not isinstance(parent, list) or last >= len(parent):
            raise TypedRepairError(
                f"patch target index does not exist: {_format_path(path)}",
                outcome=REJECTED_PATH_UNRESOLVABLE,
            )
        parent[last] = value
        return
    if not isinstance(parent, dict) or last not in parent:
        raise TypedRepairError(
            f"patch target does not exist: {_format_path(path)}",
            outcome=REJECTED_PATH_UNRESOLVABLE,
        )
    parent[last] = value


def _delete_path(payload: Any, path: tuple[Any, ...]) -> None:
    parent = _parent_of(payload, path)
    last = path[-1]
    if isinstance(last, int):
        if not isinstance(parent, list) or last >= len(parent):
            raise TypedRepairError(
                f"patch target index does not exist: {_format_path(path)}",
                outcome=REJECTED_PATH_UNRESOLVABLE,
            )
        del parent[last]
        return
    if not isinstance(parent, dict) or last not in parent:
        raise TypedRepairError(
            f"patch target does not exist: {_format_path(path)}",
            outcome=REJECTED_PATH_UNRESOLVABLE,
        )
    del parent[last]


def _empties_a_required_choice(
    guard: "XsdGuard",
    element_type: str,
    canonical: dict[str, Any],
    json_path: tuple[Any, ...],
    tag_path: tuple[str, ...],
) -> bool:
    """True when removing this element would leave a required choice empty."""
    groups = guard.required_choice_groups(element_type, tag_path[1:])
    if not groups:
        return False
    parent_path = json_path[: -2 if isinstance(json_path[-1], int) else -1]
    for group in groups:
        remaining = 0
        for tag in group:
            count = _canonical_count(canonical, parent_path, tag)
            if tag == tag_path[-1]:
                count -= 1
            remaining += count
        if remaining < 1:
            return True
    return False


def _canonical_count(canonical: dict[str, Any], parent_path: tuple[Any, ...], tag: str) -> int:
    found, parent = _get_path(canonical, parent_path)
    if not found or not isinstance(parent, dict) or tag not in parent:
        return 0
    value = parent[tag]
    return len(value) if isinstance(value, list) else 1


def derive_candidates(
    target: RepairTarget,
    finding: dict[str, Any],
    *,
    guard: XsdGuard,
) -> tuple[list[RepairCandidate], bool]:
    """Enumerate every XSD-legal edit the finding's location admits.

    Enumeration is the whole point: because the program produces the paths, a
    path cannot be misspelled, and the strict provider schema can be reduced to
    integer selections with no free-form string anywhere.
    """
    location = finding.get("location") or {}
    xml_path = location.get("xml_path")
    if not isinstance(xml_path, str) or not xml_path.strip():
        return [], False
    canonical = target.canonical_payload()
    locator = PayloadLocator(
        canonical, element_type=target.element_type, package=target.package
    )
    nodes, leaf = locator.resolve(xml_path)
    if not nodes:
        return [], False

    candidates: list[RepairCandidate] = []
    seen: set[tuple[str, tuple[Any, ...], str | None]] = set()

    def add(candidate: RepairCandidate) -> None:
        key = (candidate.op, candidate.json_path, candidate.leaf or candidate.child_tag)
        if key in seen:
            return
        if candidate.op != RESTORE_PINNED_VALUE:
            try:
                # Requirement-owned values cannot be rewritten by a model.
                # They have a separate deterministic restore operation.
                _check_immutable(target, candidate.source_path)
            except TypedRepairError:
                return
        seen.add(key)
        candidates.append(candidate)

    def to_source(path: tuple[Any, ...]) -> tuple[Any, ...] | None:
        source = canonical_path_to_source(path, target.projection_map)
        found, _value = _get_path(target.payload, source)
        return source if found else None

    def legal(tag_path: tuple[str, ...], leaf_segment: str | None) -> bool:
        segments = list(tag_path[1:])
        if leaf_segment:
            segments.append("#TEXT" if leaf_segment == "#text" else leaf_segment.upper())
        return guard.path_is_realizable(target.element_type, segments)

    def within_bounds(candidate_tag_path: tuple[str, ...], delta: int, count: int) -> bool:
        try:
            minimum, maximum = guard.bounds(target.element_type, candidate_tag_path[1:])
        except TypedRepairError:
            return False
        updated = count + delta
        return updated >= minimum and (maximum is None or updated <= maximum)

    def add_set_value(node: PayloadNode, leaf_segment: str | None) -> None:
        if leaf_segment is None and node.tag.upper() in _IDENTITY_TAGS:
            return
        path = node.json_path if leaf_segment is None else node.json_path + (leaf_segment,)
        found, value = _get_path(canonical, path)
        if not found or not _is_scalar(value):
            return
        if not legal(node.tag_path, leaf_segment):
            return
        source = to_source(path)
        if source is None:
            return
        try:
            _check_immutable(target, source)
        except TypedRepairError:
            add(
                RepairCandidate(
                    op=RESTORE_PINNED_VALUE,
                    json_path=path,
                    source_path=source,
                    tag_path=node.tag_path,
                    leaf=leaf_segment,
                    label=f"{RESTORE_PINNED_VALUE} {node.instance_path}"
                    + (f"/{leaf_segment}" if leaf_segment else ""),
                )
            )
            return
        add(
            RepairCandidate(
                op=SET_VALUE,
                json_path=path,
                source_path=source,
                tag_path=node.tag_path,
                leaf=leaf_segment,
                label=f"{SET_VALUE} {node.instance_path}"
                + (f"/{leaf_segment}" if leaf_segment else ""),
            )
        )

    def add_descendant_pinned_restore(node: PayloadNode) -> None:
        """Offer deterministic materialization when a pinned leaf is absent.

        A finding may stop at an existing ancestor such as ``INIT-VALUE`` after
        the value-specification subtree has been deleted.  The missing leaf
        cannot be selected as a normal edit site, but its provider-space path
        remains part of the frozen generation context.
        """
        source_root = canonical_path_to_source(node.json_path, target.projection_map)
        for pinned in target.immutable_paths:
            pinned_path = tuple(pinned)
            if pinned_path[: len(source_root)] != tuple(source_root):
                continue
            add(
                RepairCandidate(
                    op=RESTORE_PINNED_VALUE,
                    json_path=node.json_path,
                    source_path=pinned_path,
                    tag_path=node.tag_path,
                    label=(
                        f"{RESTORE_PINNED_VALUE} requirement-owned descendant "
                        f"under {node.instance_path}"
                    ),
                )
            )
            return

    for node in nodes:
        if leaf is not None:
            add_set_value(node, leaf)
            continue
        add_descendant_pinned_restore(node)
        add_set_value(node, None)
        if isinstance(node.value, dict):
            if "#text" in node.value:
                add_set_value(node, "#text")
            for key in node.value:
                if key.startswith("@"):
                    add_set_value(node, key)
            for key, child in _element_items(node.value):
                if key.upper() in _IDENTITY_TAGS or not _is_scalar(child):
                    continue
                child_node = next(
                    (
                        item
                        for item in locator.nodes
                        if item.json_path == node.json_path + (key,)
                    ),
                    None,
                )
                if child_node is not None:
                    add_set_value(child_node, None)

    if leaf is not None:
        return candidates, True

    for node in nodes:
        source_root = to_source(node.json_path)
        if source_root is None:
            continue
        try:
            node_schema = subschema_at_path(target.root_schema, source_root)
        except ElementSelectionError:
            continue
        properties = node_schema.get("properties")
        if isinstance(properties, dict):
            for key, child_schema in properties.items():
                if key.startswith("@") or key == "#text" or key.upper() in _IDENTITY_TAGS:
                    continue
                if not isinstance(child_schema, dict):
                    continue
                tag_path = node.tag_path + (key,)
                if not legal(tag_path, None):
                    continue
                is_array = child_schema.get("type") == "array"
                present = isinstance(node.value, dict) and key in node.value
                if present and not is_array:
                    continue
                if not within_bounds(
                    tag_path, 1, _canonical_count(canonical, node.json_path, key)
                ):
                    continue
                add(
                    RepairCandidate(
                        op=INSERT_ELEMENT,
                        json_path=node.json_path + (key,),
                        source_path=source_root + (key,),
                        tag_path=tag_path,
                        child_tag=key,
                        parent_json_path=node.json_path,
                        parent_source_path=source_root,
                        is_array_member=is_array,
                        label=f"{INSERT_ELEMENT} {key} under {node.instance_path}",
                    )
                )

    for node in nodes:
        removable: list[PayloadNode] = [node] if node.json_path else []
        removable.extend(
            item
            for item in locator.nodes
            if len(item.json_path) > len(node.json_path)
            and item.json_path[: len(node.json_path)] == node.json_path
            and len(item.json_path) <= len(node.json_path) + 2
            and item.tag_path == node.tag_path + (item.tag,)
        )
        for item in removable:
            if item.tag.upper() in _IDENTITY_TAGS:
                continue
            if not legal(item.tag_path, None):
                continue
            parent_path = item.json_path[: -2 if isinstance(item.json_path[-1], int) else -1]
            if not within_bounds(
                item.tag_path, -1, _canonical_count(canonical, parent_path, item.tag)
            ):
                continue
            try:
                if _empties_a_required_choice(
                    guard,
                    target.element_type,
                    canonical,
                    item.json_path,
                    item.tag_path,
                ):
                    continue
            except TypedRepairError:
                continue
            source = to_source(item.json_path)
            if source is None:
                continue
            add(
                RepairCandidate(
                    op=REMOVE_ELEMENT,
                    json_path=item.json_path,
                    source_path=source,
                    tag_path=item.tag_path,
                    parent_json_path=item.json_path[:-1],
                    is_array_member=isinstance(item.json_path[-1], int),
                    label=f"{REMOVE_ELEMENT} {item.instance_path}",
                )
            )
    return candidates, True


@dataclass
class FindingPlan:
    """A finding together with the enumerated edits the program will accept."""

    index: int
    finding: dict[str, Any]
    target_key: tuple[str, str] | None
    located: bool = False
    candidates: list[RepairCandidate] = field(default_factory=list)

    @property
    def automation_boundary_reason(self) -> str:
        """Why this finding cannot enter the automatic queue, if it cannot.

        This is orthogonal to the attempt outcome: a finding may be perfectly
        localizable and still be rejected by revalidation.
        """
        if self.target_key is None or not self.located:
            return BOUNDARY_NOT_LOCALIZABLE
        if not self.candidates:
            return BOUNDARY_NO_APPLICABLE_OPERATION
        return BOUNDARY_NONE

    def record(self) -> dict[str, Any]:
        location = self.finding.get("location") or {}
        return {
            "finding_index": self.index,
            "finding_fingerprint": str(self.finding.get("fingerprint") or ""),
            "constraint_ids": list(self.finding.get("constraint_ids") or []),
            "file": location.get("file"),
            "xml_path": location.get("xml_path"),
            "candidate_count": len(self.candidates),
            "operations": sorted({item.op for item in self.candidates}),
            "automation_boundary_reason": self.automation_boundary_reason,
        }


def plan_findings(
    findings: list[dict[str, Any]],
    targets: dict[tuple[str, str], RepairTarget],
    *,
    guard: XsdGuard,
    order_normalization_keys: frozenset[tuple[str, str]] = frozenset(),
) -> list[FindingPlan]:
    plans: list[FindingPlan] = []
    for index, finding in enumerate(findings):
        location = finding.get("location") or {}
        raw_file = str(location.get("file") or "")
        key: tuple[str, str] | None = None
        if "/" in raw_file:
            kind, name = raw_file.split("/", 1)
            candidate_key = (kind, name.removesuffix(".arxml"))
            if candidate_key in targets:
                key = candidate_key
        plan = FindingPlan(index=index, finding=finding, target_key=key)
        if key is not None:
            constraint_ids = {
                str(item).upper() for item in finding.get("constraint_ids") or []
            }
            if key in order_normalization_keys and "XSD" in constraint_ids:
                plan.located = True
                plan.candidates = [
                    RepairCandidate(
                        op=RESTORE_XSD_ORDER,
                        json_path=(),
                        source_path=(),
                        tag_path=(targets[key].element_type,),
                        label=f"{RESTORE_XSD_ORDER} {key[0]}/{key[1]}",
                    )
                ]
            else:
                plan.candidates, plan.located = derive_candidates(
                    targets[key], finding, guard=guard
                )
        plans.append(plan)
    return plans


def build_selection_schema(plans: list[FindingPlan]) -> dict[str, Any]:
    """Strict, fully enumerated schema for the first provider call.

    There is no free-form string in this schema: the model chooses which
    finding to address, which enumerated location to edit, and which operation
    to use.  Scalar values are the only free content, and they are re-checked
    against the component schema before anything is rendered.
    """
    actionable = [plan for plan in plans if plan.candidates]
    if not actionable:
        raise TypedRepairError(
            "no validation finding could be localized to an editable payload path",
            outcome=REJECTED_PATH_UNRESOLVABLE,
        )
    finding_indexes = [plan.index for plan in actionable]
    max_candidates = max(len(plan.candidates) for plan in actionable)
    operations = sorted({item.op for plan in actionable for item in plan.candidates})
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["patches"],
        "properties": {
            "patches": {
                "type": "array",
                "minItems": 1,
                "maxItems": len(actionable),
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["finding_index", "candidate_index", "op", "scalar_value"],
                    "properties": {
                        "finding_index": {"type": "integer", "enum": finding_indexes},
                        "candidate_index": {
                            "type": "integer",
                            "enum": list(range(max_candidates)),
                        },
                        "op": {"type": "string", "enum": operations},
                        "scalar_value": {
                            "type": ["string", "number", "boolean", "null"],
                            "description": (
                                "New scalar value; required for set_value and "
                                "must be null for every other operation."
                            ),
                        },
                    },
                },
            }
        },
    }


def build_insert_schema(
    inserts: list[tuple[int, RepairCandidate]], targets_by_patch: dict[int, RepairTarget]
) -> dict[str, Any]:
    """Strict schema for the second call: XSD-derived structure, model values.

    The sub-schema is taken from the component's authoritative schema at the
    exact insertion point, so the inserted subtree's element names, cardinality
    and value domains are decided by the XSD, never by the model.
    """
    properties: dict[str, Any] = {}
    for position, candidate in inserts:
        target = targets_by_patch[position]
        try:
            parent_schema = subschema_at_path(
                target.root_schema, candidate.parent_source_path
            )
            child_schema = subschema_at_path(
                parent_schema, (candidate.child_tag,)
            )
        except ElementSelectionError as error:
            raise TypedRepairError(
                f"no schema for inserted element {candidate.child_tag}: {error}",
                outcome=REJECTED_SCHEMA_VIOLATION,
            ) from error
        if child_schema.get("type") == "array":
            items = child_schema.get("items")
            if not isinstance(items, dict):
                raise TypedRepairError(
                    f"array schema for {candidate.child_tag} has no item schema",
                    outcome=REJECTED_SCHEMA_VIOLATION,
                )
            child_schema = items
        properties[f"insert_{position}"] = deepcopy(child_schema)
    return {
        "type": "object",
        "additionalProperties": False,
        "required": sorted(properties),
        "properties": properties,
    }


@dataclass(frozen=True)
class ResolvedPatch:
    position: int
    plan: FindingPlan
    candidate: RepairCandidate
    target_key: tuple[str, str]
    scalar_value: Any = None
    inserted_value: Any = None


def resolve_patches(
    patches: list[dict[str, Any]],
    plans: list[FindingPlan],
    targets: dict[tuple[str, str], RepairTarget],
) -> list[ResolvedPatch]:
    """Turn provider selections into concrete edits, rejecting anything unclear."""
    by_index = {plan.index: plan for plan in plans}
    resolved: list[ResolvedPatch] = []
    used: set[tuple[int, int]] = set()
    used_findings: set[int] = set()
    for position, patch in enumerate(patches):
        if not isinstance(patch, dict):
            raise TypedRepairError(
                f"patch {position} is not an object", outcome=REJECTED_MALFORMED_PATCH
            )
        finding_index = patch.get("finding_index")
        candidate_index = patch.get("candidate_index")
        op = patch.get("op")
        if not isinstance(finding_index, int) or isinstance(finding_index, bool):
            raise TypedRepairError(
                f"patch {position} has no integer finding_index",
                outcome=REJECTED_MALFORMED_PATCH,
            )
        if not isinstance(candidate_index, int) or isinstance(candidate_index, bool):
            raise TypedRepairError(
                f"patch {position} has no integer candidate_index",
                outcome=REJECTED_MALFORMED_PATCH,
            )
        plan = by_index.get(finding_index)
        if plan is None or plan.target_key is None:
            raise TypedRepairError(
                f"patch {position} references unknown finding {finding_index}",
                outcome=REJECTED_PATH_UNRESOLVABLE,
            )
        if not 0 <= candidate_index < len(plan.candidates):
            raise TypedRepairError(
                f"patch {position} selects candidate {candidate_index} outside "
                f"the {len(plan.candidates)} enumerated for finding {finding_index}",
                outcome=REJECTED_PATH_UNRESOLVABLE,
            )
        if (finding_index, candidate_index) in used:
            raise TypedRepairError(
                f"patch {position} repeats an already selected edit",
                outcome=REJECTED_CONFLICTING_PATCHES,
            )
        used.add((finding_index, candidate_index))
        if finding_index in used_findings:
            raise TypedRepairError(
                f"patch {position} repeats finding {finding_index}",
                outcome=REJECTED_CONFLICTING_PATCHES,
            )
        used_findings.add(finding_index)
        candidate = plan.candidates[candidate_index]
        if op != candidate.op:
            raise TypedRepairError(
                f"patch {position} requests {op!r} for a {candidate.op!r} candidate",
                outcome=REJECTED_MALFORMED_PATCH,
            )
        scalar = patch.get("scalar_value")
        if candidate.op == SET_VALUE:
            if scalar is None:
                raise TypedRepairError(
                    f"patch {position} is a set_value without a scalar_value",
                    outcome=REJECTED_MALFORMED_PATCH,
                )
        elif scalar is not None:
            raise TypedRepairError(
                f"patch {position} supplies a scalar_value for {candidate.op}",
                outcome=REJECTED_MALFORMED_PATCH,
            )
        if plan.target_key not in targets:
            raise TypedRepairError(
                f"patch {position} targets an unknown document",
                outcome=REJECTED_PATH_UNRESOLVABLE,
            )
        resolved.append(
            ResolvedPatch(
                position=position,
                plan=plan,
                candidate=candidate,
                target_key=plan.target_key,
                scalar_value=scalar,
            )
        )
    return resolved


def _reject_overlaps(patches: list[ResolvedPatch]) -> None:
    by_target: dict[tuple[str, str], list[tuple[Any, ...]]] = {}
    for patch in patches:
        path = patch.candidate.source_path
        for existing in by_target.setdefault(patch.target_key, []):
            shorter, longer = sorted((existing, path), key=len)
            if longer[: len(shorter)] == shorter:
                raise TypedRepairError(
                    "patches overlap at "
                    f"{_format_path(shorter)} and {_format_path(longer)}",
                    outcome=REJECTED_CONFLICTING_PATCHES,
                )
        by_target[patch.target_key].append(path)


def _check_immutable(target: RepairTarget, path: tuple[Any, ...]) -> None:
    for pinned in target.immutable_paths:
        shorter, longer = sorted((tuple(pinned), path), key=len)
        if longer[: len(shorter)] == shorter:
            raise TypedRepairError(
                "patch would rewrite the requirement-owned value at "
                f"{_format_path(pinned)}",
                outcome=REJECTED_IMMUTABLE_VALUE,
            )


def _check_occurrence(
    target: RepairTarget,
    canonical: dict[str, Any],
    candidate: RepairCandidate,
    *,
    delta: int,
    guard: XsdGuard,
) -> None:
    tag_segments = candidate.tag_path[1:]
    if not tag_segments:
        raise TypedRepairError(
            "the document root element cannot be inserted or removed",
            outcome=REJECTED_OCCURRENCE_VIOLATION,
        )
    minimum, maximum = guard.bounds(target.element_type, tag_segments)
    if delta < 0 and _empties_a_required_choice(
        guard,
        target.element_type,
        canonical,
        candidate.json_path,
        candidate.tag_path,
    ):
        raise TypedRepairError(
            f"removing {candidate.tag_path[-1]} would leave a required XSD choice "
            "with no selected branch",
            outcome=REJECTED_OCCURRENCE_VIOLATION,
        )
    parent_path = (
        candidate.parent_json_path
        if candidate.op == INSERT_ELEMENT
        else candidate.json_path[: -2 if candidate.is_array_member else -1]
    )
    current = _canonical_count(canonical, parent_path, candidate.tag_path[-1])
    updated = current + delta
    if updated < minimum or (maximum is not None and updated > maximum):
        raise TypedRepairError(
            f"{candidate.op} would leave {updated} occurrences of "
            f"{candidate.tag_path[-1]}, outside XSD bounds "
            f"[{minimum}, {'unbounded' if maximum is None else maximum}]",
            outcome=REJECTED_OCCURRENCE_VIOLATION,
        )


def apply_patches(
    patches: list[ResolvedPatch],
    targets: dict[tuple[str, str], RepairTarget],
    *,
    guard: XsdGuard,
) -> dict[tuple[str, str], RepairTarget]:
    """Apply a whole patch set or reject it whole.

    Ordering is fixed so that one patch can never invalidate another's already
    validated path: values first, then insertions (appends never shift existing
    indices), then removals from the deepest path upward.
    """
    _reject_overlaps(patches)
    canonical_by_target = {
        key: target.canonical_payload() for key, target in targets.items()
    }
    working = {key: deepcopy(target.payload) for key, target in targets.items()}
    touched: set[tuple[str, str]] = set()

    def order(patch: ResolvedPatch) -> tuple[int, Any]:
        rank = {
            SET_VALUE: 0,
            INSERT_ELEMENT: 1,
            REMOVE_ELEMENT: 2,
            RESTORE_XSD_ORDER: 3,
            RESTORE_PINNED_VALUE: 0,
        }[patch.candidate.op]
        depth = len(patch.candidate.source_path)
        return (rank, -depth if rank == 2 else depth)

    for patch in sorted(patches, key=order):
        target = targets[patch.target_key]
        candidate = patch.candidate
        canonical = canonical_by_target[patch.target_key]
        payload = working[patch.target_key]
        touched.add(patch.target_key)

        if candidate.op == RESTORE_XSD_ORDER:
            # The payload already represents the same document content; the
            # only repair is to let the pinned XSD serializer decide sibling
            # order again.  ``bind_order_normalization`` proves this premise.
            continue

        if candidate.op == RESTORE_PINNED_VALUE:
            # ``RepairTarget.revalidate`` reapplies the hash-pinned declared
            # value design.  Remove the corrupted source leaf first so that
            # deterministic materialization can reinsert the declared value;
            # it deliberately refuses to overwrite conflicting input.  No
            # provider-supplied scalar reaches this path.
            found, _existing = _get_path(payload, candidate.source_path)
            if found:
                _delete_path(payload, candidate.source_path)
            continue

        segments = list(candidate.tag_path[1:])
        if candidate.leaf:
            segments.append("#TEXT" if candidate.leaf == "#text" else candidate.leaf.upper())
        guard.require_realizable(target.element_type, segments)

        _check_immutable(target, candidate.source_path)

        if candidate.op == SET_VALUE:
            found, existing = _get_path(payload, candidate.source_path)
            if not found or not _is_scalar(existing):
                raise TypedRepairError(
                    f"set_value target is not a scalar leaf: "
                    f"{_format_path(candidate.source_path)}",
                    outcome=REJECTED_PATH_UNRESOLVABLE,
                )
            _set_path(payload, candidate.source_path, patch.scalar_value)
            continue

        if candidate.op == INSERT_ELEMENT:
            if patch.inserted_value is None:
                raise TypedRepairError(
                    f"insert_element patch {patch.position} has no value subtree",
                    outcome=REJECTED_MALFORMED_PATCH,
                )
            _check_occurrence(target, canonical, candidate, delta=1, guard=guard)
            parent = None
            found, parent = _get_path(payload, candidate.parent_source_path)
            if not found or not isinstance(parent, dict):
                raise TypedRepairError(
                    f"insert parent does not exist: "
                    f"{_format_path(candidate.parent_source_path)}",
                    outcome=REJECTED_PATH_UNRESOLVABLE,
                )
            tag = str(candidate.child_tag)
            if candidate.is_array_member:
                existing = parent.setdefault(tag, [])
                if not isinstance(existing, list):
                    raise TypedRepairError(
                        f"insert target {tag} is not an array",
                        outcome=REJECTED_SCHEMA_VIOLATION,
                    )
                existing.append(deepcopy(patch.inserted_value))
            else:
                if tag in parent:
                    raise TypedRepairError(
                        f"insert target {tag} already exists",
                        outcome=REJECTED_OCCURRENCE_VIOLATION,
                    )
                parent[tag] = deepcopy(patch.inserted_value)
            continue

        _check_occurrence(target, canonical, candidate, delta=-1, guard=guard)
        _delete_path(payload, candidate.source_path)

    updated: dict[tuple[str, str], RepairTarget] = {}
    for key, target in targets.items():
        if key not in touched:
            updated[key] = target
            continue
        revalidated = target.revalidate(working[key])
        updated[key] = RepairTarget(
            kind=target.kind,
            name=target.name,
            element_type=target.element_type,
            payload=revalidated,
            root_schema=target.root_schema,
            document_schema=target.document_schema,
            declared_value_design=target.declared_value_design,
            projection_map=target.projection_map,
            immutable_paths=target.immutable_paths,
            package_name=target.package_name,
        )
    return updated


def render_document(
    serializer: DeterministicXsdSerializer,
    *,
    package: str,
    element_type: str,
    payload: dict[str, Any],
) -> str:
    """Render one single-element ARXML document through the XSD serializer.

    Element tags and sibling order come from the XSD content model, so neither
    generation nor repair can decide them.
    """
    root = Element("AUTOSAR")
    root.set("xmlns", AUTOSAR_NAMESPACE)
    root.set("xmlns:xsi", XSI_NAMESPACE)
    root.set("xsi:schemaLocation", SCHEMA_LOCATION)
    ar_packages = SubElement(root, "AR-PACKAGES")
    package_element = SubElement(ar_packages, "AR-PACKAGE")
    SubElement(package_element, "SHORT-NAME").text = package
    elements = SubElement(package_element, "ELEMENTS")
    element = SubElement(elements, element_type)
    serializer.append_payload(
        element, payload, root_element=element_type, skip_keys=("_type",)
    )
    rough = tostring(root, encoding="unicode")
    pretty = minidom.parseString(rough).toprettyxml(indent="  ")
    return "\n".join(line for line in pretty.split("\n") if line.strip())


def render_documents(
    targets: dict[tuple[str, str], RepairTarget],
    *,
    serializer: DeterministicXsdSerializer,
) -> dict[str, dict[str, str]]:
    """Re-render every document from its structured payload."""
    bundle: dict[str, dict[str, str]] = {"components": {}, "interfaces": {}}
    for (kind, name), target in targets.items():
        try:
            bundle[kind][name] = render_document(
                serializer,
                package=target.package,
                element_type=target.element_type,
                payload=target.canonical_payload(),
            )
        except (XsdSerializationError, ValueError) as error:
            raise TypedRepairError(
                f"repaired {kind}/{name} could not be serialized: {error}",
                outcome=REJECTED_RENDER_FAILURE,
            ) from error
    return bundle


def describe_plans(plans: list[FindingPlan]) -> str:
    """Render the enumerated choices for the provider prompt."""
    lines: list[str] = []
    for plan in plans:
        if not plan.candidates:
            continue
        location = plan.finding.get("location") or {}
        lines.append(
            f"FINDING {plan.index} "
            f"[{','.join(str(item) for item in plan.finding.get('constraint_ids') or []) or 'XSD'}] "
            f"{location.get('file') or '<bundle>'} {location.get('xml_path') or ''}"
        )
        lines.append(f"  message: {plan.finding.get('message') or ''}")
        evidence = plan.finding.get("evidence") or {}
        if evidence:
            lines.append(
                f"  expected={evidence.get('expected')!r} actual={evidence.get('actual')!r}"
            )
        for index, candidate in enumerate(plan.candidates):
            lines.append(f"  [{index}] {candidate.label}")
    return "\n".join(lines)


def _unordered_xml_identity(xml_text: str) -> tuple[Any, ...]:
    """Represent XML content while deliberately ignoring sibling order.

    This is used only to qualify an XSD-order repair.  Tags, attributes, text,
    descendants and multiplicity must remain identical; only the ordering of a
    node's direct children may differ.
    """
    try:
        root = fromstring(xml_text)
    except Exception as error:
        raise TypedRepairError(
            f"order-normalization input is not well-formed XML: {error}",
            outcome=REJECTED_MALFORMED_PATCH,
        ) from error

    def visit(node: Element) -> tuple[Any, ...]:
        children = sorted((visit(child) for child in list(node)), key=repr)
        attributes = tuple(sorted((str(key), str(value)) for key, value in node.attrib.items()))
        return (
            str(node.tag),
            attributes,
            str(node.text or "").strip(),
            tuple(children),
        )

    return visit(root)


ProviderCall = Any
FingerprintCall = Any

# Constraint families for which deleting the reported element is a defensible
# repair rather than a way of disposing of the rule.  Everything else -- value
# ranges, formats, references, cardinality minima -- reports that a value or a
# relationship is wrong, and deleting the carrier destroys evidence instead of
# fixing anything.  The set is deliberately narrow: the rule corpus records no
# repair-operation metadata, so nothing wider is derivable from the data.
DELETION_REPAIRABLE_FAMILIES = frozenset({"forbidden_existence", "mutual_exclusion"})


def deletion_repairable_rule_ids(plan: Any) -> frozenset[str]:
    """Rule ids whose family makes ``remove_element`` a legitimate repair.

    Only 185 of the 554 compiled rules declare a ``rule_family`` at all, so a
    rule without one never qualifies.  That is fail-closed by construction: an
    unclassified rule cannot justify a deletion.
    """
    if not isinstance(plan, dict):
        return frozenset()
    rules = plan.get("rules")
    if not isinstance(rules, list):
        return frozenset()
    result: set[str] = set()
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        family = str((rule.get("formal_spec") or {}).get("rule_family") or "")
        if family not in DELETION_REPAIRABLE_FAMILIES:
            continue
        rule_id = str(rule.get("rule_id") or "")
        if rule_id:
            result.add(rule_id)
    return frozenset(result)


def _coverage_loss_waivers(
    patches: list[ResolvedPatch],
    deletion_repairable_rule_ids: frozenset[str],
) -> tuple[tuple[CoverageLossWaiver, ...], list[dict[str, Any]]]:
    """Account for the rules a removal may legitimately take out of evaluation.

    A waiver is emitted only for rules whose constraint family makes deletion a
    defensible repair.  Removing an element is *not* a repair for a value-range,
    format or reference violation -- the value is wrong, not the element -- and
    waiving those would let a model turn any inconvenient rule into
    ``NOT_APPLICABLE`` by deleting the optional element that carries it.

    A removal with no eligible rule is still proposed: the acceptance policy
    then rejects it as an unaccounted coverage loss, which is exactly the
    automation-boundary datum the evaluation needs to report.  Suppressing the
    proposal instead would hide that the model wanted to delete.
    """
    waivers: list[CoverageLossWaiver] = []
    unwaived: list[dict[str, Any]] = []
    for patch in patches:
        if patch.candidate.op != REMOVE_ELEMENT:
            continue
        finding = patch.plan.finding
        fingerprint = str(finding.get("fingerprint") or "")
        rule_ids = tuple(
            str(rule_id) for rule_id in finding.get("rule_ids") or [] if str(rule_id)
        )
        eligible = tuple(
            rule_id for rule_id in rule_ids if rule_id in deletion_repairable_rule_ids
        )
        if not fingerprint or not eligible:
            unwaived.append(
                {
                    "finding_fingerprint": fingerprint,
                    "rule_ids": list(rule_ids),
                    "removed_location": patch.candidate.label,
                    "reason": (
                        "finding_has_no_fingerprint"
                        if not fingerprint
                        else "no_rule_of_a_deletion_repairable_family"
                    ),
                }
            )
            continue
        waivers.append(
            CoverageLossWaiver(
                finding_fingerprint=fingerprint,
                rule_ids=eligible,
                removed_location=patch.candidate.label,
            )
        )
    return tuple(waivers), unwaived


class TypedRepairSession:
    """Drive one artifact's typed repair rounds against a structured payload state.

    The repair loop hands back whichever bundle it currently considers best, so
    the structured payloads are keyed by the hash of the bundle they render to.
    A bundle that no stored payload reproduces is refused rather than repaired
    from a payload that does not match it.
    """

    def __init__(
        self,
        *,
        guard: XsdGuard,
        serializer: DeterministicXsdSerializer,
        fingerprint: FingerprintCall,
        deletion_repairable_rule_ids: frozenset[str] = frozenset(),
    ) -> None:
        self.guard = guard
        self.serializer = serializer
        self.fingerprint = fingerprint
        # Empty by default: a session that was not told which rules deletion can
        # repair waives nothing, so every removal that costs coverage is refused.
        self.deletion_repairable_rule_ids = frozenset(deletion_repairable_rule_ids)
        self.states: dict[str, dict[tuple[str, str], RepairTarget]] = {}
        self.order_normalization: dict[str, frozenset[tuple[str, str]]] = {}
        self.trace: list[dict[str, Any]] = []

    def reset(self) -> None:
        self.states = {}
        self.order_normalization = {}
        self.trace = []

    def bind(
        self, targets: dict[tuple[str, str], RepairTarget], bundle: dict[str, Any]
    ) -> None:
        """Prove the payloads reproduce the generated bundle, then bind them."""
        rendered = render_documents(targets, serializer=self.serializer)
        if rendered != bundle:
            expected = {
                f"{kind}/{name}"
                for kind in ("components", "interfaces")
                for name in (bundle.get(kind) or {})
            }
            produced = {
                f"{kind}/{name}"
                for kind in ("components", "interfaces")
                for name in rendered[kind]
            }
            raise TypedRepairError(
                "structured repair payloads do not reproduce the generated bundle; "
                f"documents without a payload={sorted(expected - produced)}, "
                f"unexpected documents={sorted(produced - expected)}"
            )
        self.states = {self.fingerprint(bundle): dict(targets)}
        self.order_normalization = {}

    def bind_order_normalization(
        self, targets: dict[tuple[str, str], RepairTarget], bundle: dict[str, Any]
    ) -> None:
        """Bind a bundle that differs from the structured state only by order.

        The comparison is content-complete and order-insensitive.  It is not a
        permissive XML parser or a fallback reconstruction path: any changed
        tag, value, attribute, multiplicity or document identity is rejected.
        """
        rendered = render_documents(targets, serializer=self.serializer)
        rendered_keys = {
            (kind, name)
            for kind in ("components", "interfaces")
            for name in rendered[kind]
        }
        bundle_keys = {
            (kind, name)
            for kind in ("components", "interfaces")
            for name in (bundle.get(kind) or {})
        }
        if rendered_keys != bundle_keys:
            raise TypedRepairError("order-normalization bundle changed document identity")
        changed: set[tuple[str, str]] = set()
        for kind, name in sorted(rendered_keys):
            expected = rendered[kind][name]
            actual = str((bundle.get(kind) or {}).get(name) or "")
            if expected == actual:
                continue
            if _unordered_xml_identity(expected) != _unordered_xml_identity(actual):
                raise TypedRepairError(
                    f"order-normalization bundle changed content in {kind}/{name}"
                )
            changed.add((kind, name))
        if not changed:
            raise TypedRepairError("order-normalization bundle has no ordering difference")
        bundle_hash = self.fingerprint(bundle)
        self.states = {bundle_hash: dict(targets)}
        self.order_normalization = {bundle_hash: frozenset(changed)}

    def export_context(self, bundle: dict[str, Any]) -> dict[str, Any]:
        """Serialize the exact structured state needed by a later repair run."""
        bundle_hash = self.fingerprint(bundle)
        targets = self.states.get(bundle_hash)
        if targets is None:
            raise TypedRepairError("cannot export an unbound typed-repair bundle")
        unsigned: dict[str, Any] = {
            "schema_version": REPAIR_CONTEXT_SCHEMA_VERSION,
            "bundle_sha256": bundle_hash,
            "xsd_sha256": self.guard.path_index.xsd_sha256,
            "serialization_manifest_sha256": self.serializer.manifest_sha256,
            "targets": [
                _target_record(targets[key]) for key in sorted(targets)
            ],
        }
        return {**unsigned, "content_sha256": _canonical_sha256(unsigned)}

    def restore_context(
        self, context: Any, bundle: dict[str, Any]
    ) -> dict[tuple[str, str], RepairTarget]:
        """Verify and restore a persisted context, then reproduce its bundle."""
        if not isinstance(context, dict):
            raise TypedRepairError("typed-repair context must be an object")
        required = {
            "schema_version",
            "bundle_sha256",
            "xsd_sha256",
            "serialization_manifest_sha256",
            "targets",
            "content_sha256",
        }
        if set(context) != required:
            raise TypedRepairError("typed-repair context fields differ from the contract")
        unsigned = {key: context[key] for key in context if key != "content_sha256"}
        if context.get("schema_version") != REPAIR_CONTEXT_SCHEMA_VERSION:
            raise TypedRepairError("typed-repair context schema version is unsupported")
        if context.get("content_sha256") != _canonical_sha256(unsigned):
            raise TypedRepairError("typed-repair context canonical hash mismatch")
        if context.get("xsd_sha256") != self.guard.path_index.xsd_sha256:
            raise TypedRepairError("typed-repair context XSD hash mismatch")
        if (
            context.get("serialization_manifest_sha256")
            != self.serializer.manifest_sha256
        ):
            raise TypedRepairError("typed-repair serialization manifest hash mismatch")
        bundle_hash = self.fingerprint(bundle)
        if context.get("bundle_sha256") != bundle_hash:
            raise TypedRepairError("typed-repair context bundle hash mismatch")
        raw_targets = context.get("targets")
        if not isinstance(raw_targets, list) or not raw_targets:
            raise TypedRepairError("typed-repair context has no targets")
        targets: dict[tuple[str, str], RepairTarget] = {}
        for position, record in enumerate(raw_targets):
            target = _target_from_record(record, position=position)
            key = (target.kind, target.name)
            if key in targets:
                raise TypedRepairError(f"typed-repair context repeats {key[0]}/{key[1]}")
            targets[key] = target
        self.bind(targets, bundle)
        return targets

    def propose(
        self,
        bundle: dict[str, Any],
        report: dict[str, Any],
        repair_prompt: str,
        round_number: int,
        *,
        provider: ProviderCall,
        seed: int | None = None,
        context_json: str = "",
    ) -> RepairProposal:
        """Produce one typed repair candidate, or raise with a typed outcome.

        The proposal carries its own coverage-loss waivers.  Deleting the
        element a rule reports on is the correct repair for a forbidden-existence
        or mutual-exclusion violation and necessarily makes that rule
        ``NOT_APPLICABLE``; without an auditable waiver the acceptance policy
        cannot tell that apart from deleting evidence, and would refuse every
        removal.
        """
        record: dict[str, Any] = {"round": round_number}
        tokens = {"input": 0, "output": 0, "total": 0}
        try:
            bundle_hash = self.fingerprint(bundle)
            targets = self.states.get(bundle_hash)
            if targets is None:
                raise TypedRepairError(
                    "no structured payload state matches the bundle offered for repair",
                    outcome=REJECTED_PATH_UNRESOLVABLE,
                )
            findings = report.get("findings")
            if not isinstance(findings, list):
                raise TypedRepairError("validation report has no findings array")
            plans = plan_findings(
                findings,
                targets,
                guard=self.guard,
                order_normalization_keys=self.order_normalization.get(
                    bundle_hash, frozenset()
                ),
            )
            record["findings"] = [plan.record() for plan in plans]
            schema = build_selection_schema(plans)
            response = self._call(
                provider,
                self._selection_prompt(
                    plans, repair_prompt, round_number, bundle, context_json
                ),
                schema,
                seed,
                tokens,
            )
            patches = resolve_patches(
                (response or {}).get("patches") or [], plans, targets
            )
            record["patches"] = [
                {
                    "finding_index": patch.plan.index,
                    "op": patch.candidate.op,
                    "location": patch.candidate.label,
                }
                for patch in patches
            ]
            patches = self._fill_inserted_subtrees(
                patches,
                targets,
                repair_prompt,
                round_number,
                provider=provider,
                seed=seed,
                tokens=tokens,
            )
            updated = apply_patches(patches, targets, guard=self.guard)
            candidate = render_documents(updated, serializer=self.serializer)
            self.states[self.fingerprint(candidate)] = updated
            waivers, unwaived = _coverage_loss_waivers(
                patches, self.deletion_repairable_rule_ids
            )
            record["coverage_loss_waivers"] = [waiver.record() for waiver in waivers]
            record["unwaived_removals"] = unwaived
            record["attempt_outcome"] = "proposed"
            return RepairProposal(
                bundle=candidate,
                token_usage=dict(tokens),
                coverage_waivers=waivers,
            )
        except TypedRepairError as error:
            record["attempt_outcome"] = error.outcome
            record["error"] = str(error)
            raise
        except Exception as error:
            record["attempt_outcome"] = "repair_error"
            record["error"] = f"{type(error).__name__}: {error}"
            raise
        finally:
            record["token_usage"] = dict(tokens)
            self.trace.append(record)

    @staticmethod
    def _call(
        provider: ProviderCall,
        prompt: str,
        schema: dict[str, Any],
        seed: int | None,
        tokens: dict[str, int],
    ) -> dict[str, Any]:
        response, in_tokens, out_tokens, total_tokens = provider(prompt, schema, seed)
        tokens["input"] += int(in_tokens or 0)
        tokens["output"] += int(out_tokens or 0)
        tokens["total"] += int(total_tokens or 0)
        return response

    @staticmethod
    def _selection_prompt(
        plans: list[FindingPlan],
        repair_prompt: str,
        round_number: int,
        bundle: dict[str, Any],
        context_json: str,
    ) -> str:
        documents = [
            f"--- {kind}/{name} ---\n{xml_text}"
            for kind in ("components", "interfaces")
            for name, xml_text in sorted((bundle.get(kind) or {}).items())
        ]
        return (
            f"Typed AUTOSAR repair round {round_number}.\n"
            "Select repairs from the enumerated locations below. Every location was "
            "derived from the validation finding by the tool chain and is already "
            "known to be realizable in the pinned AUTOSAR XSD.\n"
            "Rules: identify a location only by its finding index and candidate "
            "index; supply scalar_value for set_value and null for every other "
            "operation; propose at most one edit per finding; propose nothing the "
            "finding itself does not justify.\n\n"
            f"VALIDATION ACTIONS:\n{repair_prompt}\n\n"
            f"ENUMERATED REPAIR LOCATIONS:\n{describe_plans(plans)}\n\n"
            f"HASH-PINNED VALIDATION CONTEXT:\n{context_json}\n\n"
            "CURRENT ARXML DOCUMENTS:\n" + "\n".join(documents)
        )

    def _fill_inserted_subtrees(
        self,
        patches: list[ResolvedPatch],
        targets: dict[tuple[str, str], RepairTarget],
        repair_prompt: str,
        round_number: int,
        *,
        provider: ProviderCall,
        seed: int | None,
        tokens: dict[str, int],
    ) -> list[ResolvedPatch]:
        """Ask for the values of inserted elements under an XSD-derived schema.

        The structure of an inserted subtree comes from the component schema at
        the exact insertion point; the model supplies only the values inside it.
        Structure and values are never decided by the same party.
        """
        inserts = [
            (patch.position, patch.candidate)
            for patch in patches
            if patch.candidate.op == INSERT_ELEMENT
        ]
        if not inserts:
            return patches
        schema = build_insert_schema(
            inserts,
            {
                patch.position: targets[patch.target_key]
                for patch in patches
                if patch.candidate.op == INSERT_ELEMENT
            },
        )
        described = "\n".join(
            f"insert_{position}: {candidate.label}" for position, candidate in inserts
        )
        prompt = (
            f"Typed AUTOSAR repair round {round_number}, value stage.\n"
            "Each property below is one element you chose to insert. Its schema is "
            "derived from the pinned AUTOSAR XSD at the exact insertion point, so "
            "supply values only; the element names and their order are already "
            "fixed.\n\n"
            f"INSERTIONS:\n{described}\n\n"
            f"VALIDATION ACTIONS:\n{repair_prompt}"
        )
        response = self._call(provider, prompt, schema, seed, tokens)
        values = response or {}
        filled: list[ResolvedPatch] = []
        for patch in patches:
            if patch.candidate.op != INSERT_ELEMENT:
                filled.append(patch)
                continue
            key = f"insert_{patch.position}"
            if key not in values:
                raise TypedRepairError(
                    f"value stage did not return a subtree for {key}"
                )
            filled.append(dataclass_replace(patch, inserted_value=values[key]))
        return filled
