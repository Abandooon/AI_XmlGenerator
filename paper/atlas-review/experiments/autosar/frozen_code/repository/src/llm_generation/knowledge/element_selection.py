"""Compile Phase 1 element intent into deterministic Phase 2 schema constraints.

The AUTOSAR metamodel remains authoritative.  Phase 1 only selects paths and
values; it never defines XML structure or ordering.  Phase 2 first uses the
adjacent path pairs to expand optional nodes from Neo4j, then applies the same
selections to the generated JSON Schema.  Missing or ambiguous paths fail
closed instead of being reduced to prompt-only guidance.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import re
from typing import Any, Iterable

from jsonschema import Draft202012Validator


class ElementSelectionError(ValueError):
    """A Phase 1 selection cannot be represented by the Phase 2 schema."""


PATH_SEGMENT = re.compile(r"^(?:[A-Z][A-Z0-9-]*|@[A-Z][A-Z0-9-]*|#TEXT)$")


def _tag(value: object) -> str:
    return str(value or "").strip().upper()


def _single_edit_apart(left: str, right: str) -> bool:
    """Return true only for one insertion, deletion, or substitution.

    This deliberately narrow predicate is used only to recognize a malformed
    provider path that is already superseded by one exact structured
    requirement fact.  It is not a general fuzzy XSD path resolver.
    """
    if left == right or abs(len(left) - len(right)) > 1:
        return False
    if len(left) == len(right):
        return sum(a != b for a, b in zip(left, right)) == 1
    shorter, longer = (left, right) if len(left) < len(right) else (right, left)
    short_index = 0
    long_index = 0
    edits = 0
    while short_index < len(shorter) and long_index < len(longer):
        if shorter[short_index] == longer[long_index]:
            short_index += 1
            long_index += 1
            continue
        edits += 1
        long_index += 1
        if edits > 1:
            return False
    return True


@dataclass(frozen=True)
class ElementAnchor:
    path_index: int
    short_name: str


@dataclass(frozen=True)
class ElementSelection:
    path: tuple[str, ...]
    min_occurs: int
    max_occurs: int
    value_present: bool
    value: str
    notes: str
    anchors: tuple[ElementAnchor, ...]

    @classmethod
    def from_mapping(
        cls,
        raw: object,
        *,
        position: int,
        minimum_path_segments: int = 2,
    ) -> "ElementSelection":
        if not isinstance(raw, dict):
            raise ElementSelectionError(f"selection[{position}] must be an object")
        path_value = raw.get("path")
        if not isinstance(path_value, list):
            raise ElementSelectionError(f"selection[{position}].path must be an array")
        path = tuple(_tag(item) for item in path_value if _tag(item))
        if len(path) < minimum_path_segments:
            raise ElementSelectionError(
                f"selection[{position}].path must contain at least "
                f"{minimum_path_segments} non-empty segment(s)"
            )
        invalid_segments = [segment for segment in path if not PATH_SEGMENT.fullmatch(segment)]
        if invalid_segments:
            raise ElementSelectionError(
                f"selection[{position}].path contains non-AUTOSAR segments: "
                + ", ".join(invalid_segments)
            )
        try:
            minimum = int(raw.get("min_occurs"))
            maximum = int(raw.get("max_occurs"))
        except (TypeError, ValueError) as exc:
            raise ElementSelectionError(
                f"selection[{position}] occurrence bounds must be integers"
            ) from exc
        if minimum < 0 or maximum < 1 or minimum > maximum:
            raise ElementSelectionError(
                f"selection[{position}] has invalid occurrence range {minimum}..{maximum}"
            )
        value_present = raw.get("value_present")
        if not isinstance(value_present, bool):
            raise ElementSelectionError(
                f"selection[{position}].value_present must be boolean"
            )
        value = raw.get("value")
        if not isinstance(value, str):
            raise ElementSelectionError(f"selection[{position}].value must be a string")
        if not value_present and value:
            raise ElementSelectionError(
                f"selection[{position}].value must be empty when value_present is false"
            )
        notes = raw.get("notes")
        if not isinstance(notes, str):
            raise ElementSelectionError(f"selection[{position}].notes must be a string")
        raw_anchors = raw.get("anchors") or []
        if not isinstance(raw_anchors, list):
            raise ElementSelectionError(f"selection[{position}].anchors must be an array")
        anchors: list[ElementAnchor] = []
        for anchor_position, raw_anchor in enumerate(raw_anchors):
            if not isinstance(raw_anchor, dict):
                raise ElementSelectionError(
                    f"selection[{position}].anchors[{anchor_position}] must be an object"
                )
            try:
                path_index = int(raw_anchor.get("path_index"))
            except (TypeError, ValueError) as exc:
                raise ElementSelectionError(
                    f"selection[{position}].anchors[{anchor_position}].path_index must be integer"
                ) from exc
            short_name = str(raw_anchor.get("short_name") or "").strip()
            if path_index < 0 or path_index >= len(path) or not short_name:
                raise ElementSelectionError(
                    f"selection[{position}].anchors[{anchor_position}] is out of range or unnamed"
                )
            anchors.append(ElementAnchor(path_index, short_name))
        if len({anchor.path_index for anchor in anchors}) != len(anchors):
            raise ElementSelectionError(
                f"selection[{position}] has multiple anchors for the same path index"
            )
        return cls(path, minimum, maximum, value_present, value, notes, tuple(anchors))


def parse_element_selections(
    element_design: object, *, minimum_path_segments: int = 2
) -> tuple[ElementSelection, ...]:
    if not isinstance(element_design, dict):
        return ()
    raw_selections = element_design.get("selections") or []
    if not isinstance(raw_selections, list):
        raise ElementSelectionError("element_design.selections must be an array")
    if minimum_path_segments < 1:
        raise ElementSelectionError("minimum_path_segments must be at least one")
    selections = tuple(
        ElementSelection.from_mapping(
            raw,
            position=position,
            minimum_path_segments=minimum_path_segments,
        )
        for position, raw in enumerate(raw_selections)
    )
    identities: dict[tuple[tuple[str, ...], tuple[ElementAnchor, ...]], ElementSelection] = {}
    for selection in selections:
        identity = (selection.path, selection.anchors)
        previous = identities.get(identity)
        semantic_signature = (
            selection.min_occurs,
            selection.max_occurs,
            selection.value_present,
            selection.value,
        )
        previous_signature = (
            previous.min_occurs,
            previous.max_occurs,
            previous.value_present,
            previous.value,
        ) if previous is not None else None
        if previous is not None and previous_signature != semantic_signature:
            raise ElementSelectionError(
                "conflicting selections for path " + "/".join(selection.path)
            )
        identities[identity] = selection
    return tuple(identities.values())


def _anchor_index_translation(
    original: tuple[str, ...], canonical: tuple[str, ...]
) -> dict[int, int]:
    """Map retained path segments after an XSD-proven wrapper insertion."""
    result: dict[int, int] = {}
    cursor = 0
    for original_index, segment in enumerate(original):
        while cursor < len(canonical) and canonical[cursor] != segment:
            cursor += 1
        if cursor >= len(canonical):
            break
        result[original_index] = cursor
        cursor += 1
    return result


def _canonicalize_anchor_indices(
    raw_selections: list[object],
    declared_anchor_names: dict[tuple[str, ...], set[str]] | None = None,
) -> dict[int, list[dict[str, Any]]]:
    """Derive anchor indexes from selected SHORT-NAME definitions.

    ``path_index`` is a projection detail, not semantic intent.  The anchor's
    ``short_name`` and the sibling SHORT-NAME selection identify the named XSD
    element deterministically.  When that definition is a unique prefix of the
    anchored selection, replace even an in-range model-supplied index.  Missing
    or ambiguous definitions remain fail-closed in the normal parser.
    """
    definitions: dict[str, set[tuple[str, ...]]] = {}
    definition_rows: list[tuple[int, dict[str, Any], tuple[str, ...], str]] = []
    pending_splits: dict[int, dict[int, list[str]]] = {}
    for selection_index, raw in enumerate(raw_selections):
        if not isinstance(raw, dict):
            continue
        path = tuple(_tag(item) for item in (raw.get("path") or []) if _tag(item))
        named_prefix: tuple[str, ...] | None = None
        if path and path[-1] == "SHORT-NAME":
            named_prefix = path[:-1]
        elif len(path) >= 2 and path[-2:] == ("SHORT-NAME", "#TEXT"):
            named_prefix = path[:-2]
        value = raw.get("value")
        if (
            named_prefix
            and raw.get("value_present") is True
            and isinstance(value, str)
            and value.strip()
        ):
            definitions.setdefault(value.strip(), set()).add(named_prefix)
            definition_rows.append(
                (selection_index, raw, named_prefix, value.strip())
            )

    repairs: dict[int, list[dict[str, Any]]] = {}
    # The value of a selected SHORT-NAME is itself the deterministic identity
    # of the repeated parent element.  Providers often omit the redundant
    # self-anchor for these definition rows.  Add it locally so three ports
    # may select the same physical SHORT-NAME path without being collapsed
    # into a conflict.  Existing contradictory anchors remain an error.
    for selection_index, raw, named_prefix, short_name in definition_rows:
        anchors = raw.get("anchors")
        if not isinstance(anchors, list):
            continue
        parent_index = len(named_prefix) - 1
        existing = [
            anchor
            for anchor in anchors
            if isinstance(anchor, dict)
            and anchor.get("path_index") == parent_index
        ]
        if existing and any(
            str(anchor.get("short_name") or "").strip() != short_name
            for anchor in existing
        ):
            raise ElementSelectionError(
                f"selection[{selection_index}] SHORT-NAME conflicts with its parent anchor"
            )
        same_identity = [
            anchor
            for anchor in anchors
            if isinstance(anchor, dict)
            and str(anchor.get("short_name") or "").strip() == short_name
        ]
        if not existing and not same_identity:
            anchors.append({"path_index": parent_index, "short_name": short_name})
            repairs.setdefault(selection_index, []).append(
                {
                    "anchor_index": len(anchors) - 1,
                    "short_name": short_name,
                    "original_path_index": None,
                    "canonical_path_index": parent_index,
                    "inferred_from_short_name": True,
                }
            )
        if (raw.get("min_occurs"), raw.get("max_occurs")) != (1, 1):
            original_min = raw.get("min_occurs")
            original_max = raw.get("max_occurs")
            raw["min_occurs"] = 1
            raw["max_occurs"] = 1
            repairs.setdefault(selection_index, []).append(
                {
                    "anchor_index": None,
                    "short_name": short_name,
                    "original_path_index": None,
                    "canonical_path_index": len(named_prefix) - 1,
                    "normalized_named_identity_occurrence": True,
                    "original_min_occurs": original_min,
                    "original_max_occurs": original_max,
                }
            )

    for selection_index, raw in enumerate(raw_selections):
        if not isinstance(raw, dict):
            continue
        path = tuple(_tag(item) for item in (raw.get("path") or []) if _tag(item))
        anchors = raw.get("anchors") or []
        if not isinstance(anchors, list):
            continue
        for anchor_index, anchor in enumerate(anchors):
            if not isinstance(anchor, dict):
                continue
            short_name = str(anchor.get("short_name") or "").strip()
            matching_indexes = {
                len(prefix) - 1
                for prefix in definitions.get(short_name, set())
                if len(prefix) <= len(path) and path[: len(prefix)] == prefix
            }
            if len(matching_indexes) > 1:
                raise ElementSelectionError(
                    f"selection[{selection_index}].anchors[{anchor_index}] has "
                    f"ambiguous SHORT-NAME definition {short_name!r}"
                )
            if len(matching_indexes) != 1:
                continue
            canonical_index = next(iter(matching_indexes))
            original_index = anchor.get("path_index")
            if original_index != canonical_index:
                anchor["path_index"] = canonical_index
                repairs.setdefault(selection_index, []).append(
                    {
                        "anchor_index": anchor_index,
                        "short_name": short_name,
                        "original_path_index": original_index,
                        "canonical_path_index": canonical_index,
                    }
                )
        deduplicated: list[object] = []
        seen_anchors: set[tuple[int, str]] = set()
        instance_names: dict[int, list[str]] = {}
        for anchor in anchors:
            if not isinstance(anchor, dict):
                deduplicated.append(anchor)
                continue
            path_index = anchor.get("path_index")
            short_name = str(anchor.get("short_name") or "").strip()
            if not isinstance(path_index, int):
                deduplicated.append(anchor)
                continue
            if (path_index, short_name) in seen_anchors:
                repairs.setdefault(selection_index, []).append(
                    {
                        "anchor_index": None,
                        "short_name": short_name,
                        "original_path_index": path_index,
                        "canonical_path_index": path_index,
                        "deduplicated": True,
                    }
                )
                continue
            seen_anchors.add((path_index, short_name))
            # Two different names at one path index are two named instances,
            # not a contradiction.  Record the split point and keep both.
            instance_names.setdefault(path_index, []).append(short_name)
            deduplicated.append(anchor)
        anchors[:] = deduplicated
        split_points: dict[int, list[str]] = {}
        for index, names in sorted(instance_names.items()):
            if len(names) <= 1:
                continue
            if not _is_corroborated_instance_split(
                path, index, names, declared_anchor_names
            ):
                raise ElementSelectionError(
                    f"selection[{selection_index}] has conflicting anchors at "
                    f"path index {index}"
                )
            split_points[index] = names
        if split_points:
            pending_splits[selection_index] = split_points
    if pending_splits:
        _split_named_instance_selections(raw_selections, pending_splits, repairs)
    return repairs


def _is_corroborated_instance_split(
    path: tuple[str, ...],
    path_index: int,
    names: list[str],
    declared_anchor_names: dict[tuple[str, ...], set[str]] | None,
) -> bool:
    """Whether several names at one path index are instances the requirement declares.

    Splitting an uncorroborated selection would invent named elements: a design
    naming ``Rp_Declared`` and ``Rp_Invented`` where the requirement declares
    only the first must still fail closed, and on a SHORT-NAME leaf the names
    are the selected values rather than anchors, so broadcasting them across
    instances is the ambiguity this refuses rather than a normalization.
    """
    if declared_anchor_names is None:
        return False
    if path[-1:] == ("SHORT-NAME",) or path[-2:] == ("SHORT-NAME", "#TEXT"):
        return False
    if path_index >= len(path):
        return False
    declared = declared_anchor_names.get(path[: path_index + 1])
    return bool(declared) and set(names) <= declared


def _split_named_instance_selections(
    raw_selections: list[object],
    pending_splits: dict[int, dict[int, list[str]]],
    repairs: dict[int, list[dict[str, Any]]],
) -> None:
    """Give every named instance its own selection.

    Phase 1 expressed "this element exists under Rp_A and under Rp_B" as two
    anchors sharing one path index.  That is not a selection of anything --- a
    path index identifies one repeated instance --- so the design was rejected
    even though the requirement it described was correct and realizable.  One
    selection per name states the same thing in the form the rest of the
    pipeline can bind to.
    """
    rebuilt: list[object] = []
    remapped: dict[int, list[dict[str, Any]]] = {}
    for selection_index, raw in enumerate(raw_selections):
        carried = repairs.get(selection_index, [])
        split_points = pending_splits.get(selection_index)
        if not split_points:
            if carried:
                remapped[len(rebuilt)] = list(carried)
            rebuilt.append(raw)
            continue
        if len(split_points) > 1:
            # A cross product of instances is not implied by the design, and
            # guessing which combinations were meant is not a normalization.
            raise ElementSelectionError(
                f"selection[{selection_index}] names several instances at more "
                f"than one path index: {sorted(split_points)}"
            )
        ((path_index, names),) = split_points.items()
        minimum = raw.get("min_occurs") if isinstance(raw, dict) else None
        maximum = raw.get("max_occurs") if isinstance(raw, dict) else None
        # An anchored path identifies one element under one named instance, so
        # any occurrence above one counted the instances of the repeated
        # ancestor rather than this element within one of them.  Phase 1 often
        # reports that total while naming only some of the instances, which is
        # a partial list, not a contradiction.  A range says nothing exact and
        # still fails.  An exact total below the number of names is normalized
        # only because this function is reached after the frozen structured
        # requirement has corroborated every name at this path.
        if minimum != maximum:
            raise ElementSelectionError(
                f"selection[{selection_index}] names {len(names)} instances at "
                f"path index {path_index} with an inexact occurrence "
                f"{minimum}..{maximum}"
            )
        if not isinstance(maximum, int):
            raise ElementSelectionError(
                f"selection[{selection_index}] has no exact integer occurrence"
            )
        normalized_occurrence = len(names) > 1 or (minimum, maximum) != (1, 1)
        for name in names:
            clone = deepcopy(raw)
            clone["anchors"] = [
                anchor
                for anchor in (clone.get("anchors") or [])
                if not (
                    isinstance(anchor, dict)
                    and anchor.get("path_index") == path_index
                    and str(anchor.get("short_name") or "").strip() != name
                )
            ]
            clone["min_occurs"] = 1
            clone["max_occurs"] = 1
            remapped[len(rebuilt)] = [
                *carried,
                {
                    "anchor_index": None,
                    "short_name": name,
                    "original_path_index": path_index,
                    "canonical_path_index": path_index,
                    "split_named_instance": True,
                    "named_instances": list(names),
                    "normalized_named_instance_occurrence": normalized_occurrence,
                },
            ]
            rebuilt.append(clone)
    raw_selections[:] = rebuilt
    repairs.clear()
    repairs.update(remapped)


def _normalize_absent_value_fields(
    raw_selections: list[object],
) -> dict[int, list[dict[str, Any]]]:
    """Clear a semantically unused provider companion field, with audit."""
    repairs: dict[int, list[dict[str, Any]]] = {}
    for position, raw in enumerate(raw_selections):
        if not isinstance(raw, dict):
            continue
        value = raw.get("value")
        if raw.get("value_present") is False and isinstance(value, str) and value:
            raw["value"] = ""
            repairs[position] = [
                {
                    "normalized_absent_value": True,
                    "original_value": value,
                    "canonical_value": "",
                }
            ]
    return repairs


def compile_element_design_paths(
    element_design: object,
    *,
    component_type: str,
    xsd_path_index: object,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Compile Phase 1 paths against the pinned physical XSD graph.

    Exact paths are retained.  A missing wrapper may be inserted only when the
    XSD index proves one unique descendant path.  Model-invented or ambiguous
    containment is rejected before Neo4j expansion or any Phase 2 provider
    call.
    """
    if not isinstance(element_design, dict):
        return {}, []
    result = deepcopy(element_design)
    raw_selections = result.get("selections") or []
    if not isinstance(raw_selections, list):
        raise ElementSelectionError("element_design.selections must be an array")
    # ``value_present`` is the authoritative semantic flag.  Providers
    # occasionally leave explanatory text in the companion string even though
    # the flag explicitly declares an existence-only selection.
    contract_repairs = _normalize_absent_value_fields(raw_selections)
    anchor_repairs = _canonicalize_anchor_indices(raw_selections)
    selections = tuple(
        ElementSelection.from_mapping(raw, position=position)
        for position, raw in enumerate(raw_selections)
    )
    audit: list[dict[str, Any]] = []
    for position, (raw, selection) in enumerate(zip(raw_selections, selections)):
        try:
            resolution = xsd_path_index.resolve_path(component_type, selection.path)
        except Exception as error:
            # Keep the public pipeline exception stable while preserving the
            # exact XSD diagnostic as its cause/message.
            raise ElementSelectionError(
                f"selection[{position}] is not a physical AUTOSAR XSD path for "
                f"{component_type}: {'/'.join(selection.path)}: {error}"
            ) from error
        canonical = tuple(resolution.canonical_path)
        value_leaf_resolution = None
        direct_text_check = getattr(
            xsd_path_index, "requires_direct_text_leaf", None
        )
        if (
            selection.value_present
            and canonical
            and canonical[-1] != "#TEXT"
            and not canonical[-1].startswith("@")
            and callable(direct_text_check)
            and direct_text_check(component_type, canonical)
        ):
            canonical = (*canonical, "#TEXT")
            value_leaf_resolution = "xsd-direct-text-leaf"
        if canonical != selection.path:
            translation = _anchor_index_translation(selection.path, canonical)
            for anchor_position, raw_anchor in enumerate(raw.get("anchors") or []):
                original_index = int(raw_anchor["path_index"])
                if original_index not in translation:
                    raise ElementSelectionError(
                        f"selection[{position}].anchors[{anchor_position}] cannot be "
                        "translated through the XSD path repair"
                    )
                raw_anchor["path_index"] = translation[original_index]
            raw["path"] = list(canonical)
        audit.append(
            {
                "selection_index": position,
                "resolution": value_leaf_resolution or str(resolution.resolution),
                "original_path": list(selection.path),
                "canonical_path": list(canonical),
                "value_leaf_resolution": value_leaf_resolution,
                "anchor_repairs": anchor_repairs.get(position, []),
                "contract_repairs": contract_repairs.get(position, []),
            }
        )

    # A provider can describe a simple-content element twice: once as an empty
    # container placeholder and once as its explicit ``#TEXT`` leaf.  After the
    # XSD-proven direct-text projection above, those two rows have the same
    # identity.  Prefer the explicit leaf only for this narrow, lossless case.
    # Different non-empty values or occurrence bounds remain hard conflicts.
    canonical_rows: list[object] = []
    canonical_positions: dict[
        tuple[tuple[str, ...], tuple[ElementAnchor, ...]], tuple[int, int]
    ] = {}
    for position, raw in enumerate(raw_selections):
        current = ElementSelection.from_mapping(raw, position=position)
        identity = (current.path, current.anchors)
        previous_location = canonical_positions.get(identity)
        if previous_location is None:
            canonical_positions[identity] = (len(canonical_rows), position)
            canonical_rows.append(raw)
            continue
        row_index, previous_position = previous_location
        previous = ElementSelection.from_mapping(
            canonical_rows[row_index], position=previous_position
        )
        previous_implicit = (
            audit[previous_position]["value_leaf_resolution"]
            == "xsd-direct-text-leaf"
        )
        current_implicit = (
            audit[position]["value_leaf_resolution"] == "xsd-direct-text-leaf"
        )
        same_occurrence = (
            previous.min_occurs == current.min_occurs
            and previous.max_occurs == current.max_occurs
        )
        if (
            same_occurrence
            and previous_implicit != current_implicit
            and previous.value_present
            and current.value_present
        ):
            implicit = previous if previous_implicit else current
            explicit = current if previous_implicit else previous
            if implicit.value == "" or implicit.value == explicit.value:
                explicit_position = position if previous_implicit else previous_position
                implicit_position = previous_position if previous_implicit else position
                if previous_implicit:
                    canonical_rows[row_index] = raw
                    canonical_positions[identity] = (row_index, position)
                audit[implicit_position]["canonical_merge"] = (
                    "dropped-empty-implicit-direct-text-placeholder"
                    if implicit.value == ""
                    else "dropped-redundant-implicit-direct-text-selection"
                )
                audit[explicit_position]["canonical_merge"] = (
                    "kept-explicit-direct-text-leaf"
                )
                continue
        # Preserve every other duplicate so the existing parser below can
        # reject mismatched values, bounds, notes, or unsupported merge cases.
        canonical_rows.append(raw)
    result["selections"] = canonical_rows

    # Reparse after translation so duplicate/conflicting canonical selections
    # and anchor ranges fail closed as well.
    parse_element_selections(result)
    return result, audit


def compile_architecture_selection_paths(
    architecture: object, *, xsd_path_index: object
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Apply XSD path compilation to every component in a Phase 1 mapping."""
    if not isinstance(architecture, dict):
        raise ElementSelectionError("architecture design must be an object")
    result = deepcopy(architecture)
    component_plans = result.get("component_plan") or []
    if not isinstance(component_plans, list):
        raise ElementSelectionError("component_plan must be an array")
    components_audit: list[dict[str, Any]] = []
    for position, component_plan in enumerate(component_plans):
        if not isinstance(component_plan, dict):
            raise ElementSelectionError(f"component_plan[{position}] must be an object")
        component_type = str(component_plan.get("type") or "").strip().upper()
        compiled, selections_audit = compile_element_design_paths(
            component_plan.get("element_design") or {},
            component_type=component_type,
            xsd_path_index=xsd_path_index,
        )
        component_plan["element_design"] = compiled
        components_audit.append(
            {
                "component_index": position,
                "component_name": str(component_plan.get("name") or ""),
                "component_type": component_type,
                "selections": selections_audit,
            }
        )
    audit = {
        "contract": "pinned-autosar-xsd-selection-paths-v1",
        "xsd_sha256": str(getattr(xsd_path_index, "xsd_sha256", "")),
        "components": components_audit,
    }
    return result, audit


def normalize_component_reference_values(
    element_design: object, *, component_name: str
) -> dict[str, Any]:
    """Canonicalize component-local reference values to renderer package paths.

    Phase 1 selects semantic references.  The deterministic renderer owns the
    package prefix, so a local semantic path containing the current component
    segment is compiled to ``/Components/<component>/...`` before
    provider-schema enforcement and parsed-obligation validation.  External
    package paths remain untouched.
    """
    if not isinstance(element_design, dict):
        return {}
    result = deepcopy(element_design)
    selections = parse_element_selections(result)
    raw_selections = result.get("selections") or []
    local_reference_tags = {"PORT-PROTOTYPE-REF", "START-ON-EVENT-REF"}

    def selected_text_tag(selection: ElementSelection) -> str | None:
        if not selection.path or selection.path[-1].startswith("@"):
            return None
        if selection.path[-1] == "#TEXT":
            return selection.path[-2] if len(selection.path) >= 2 else None
        return selection.path[-1]

    def anchored_port(selection: ElementSelection) -> tuple[str, str] | None:
        if (
            len(selection.path) < 2
            or selection.path[0] != "PORTS"
            or selection.path[1] not in {"P-PORT-PROTOTYPE", "R-PORT-PROTOTYPE"}
        ):
            return None
        anchors = {
            anchor.short_name
            for anchor in selection.anchors
            if anchor.path_index == 1
        }
        if len(anchors) != 1:
            return None
        return selection.path[1], next(iter(anchors))

    # A ComSpec DATA-ELEMENT-REF is serialized as an absolute AUTOSAR
    # reference, while Phase 1 may legitimately express the requested data
    # element by its SHORT-NAME.  Resolve that semantic short name through the
    # exact interface reference selected for the same named port.  This keeps
    # the comparison strict without accepting an arbitrary matching suffix.
    port_interface_refs: dict[tuple[str, str], set[str]] = {}
    for selection in selections:
        if not (
            selection.value_present
            and selected_text_tag(selection)
            in {"PROVIDED-INTERFACE-TREF", "REQUIRED-INTERFACE-TREF"}
            and selection.value.startswith("/")
        ):
            continue
        port = anchored_port(selection)
        if port is not None:
            port_interface_refs.setdefault(port, set()).add(
                selection.value.rstrip("/")
            )

    for position, raw in enumerate(raw_selections):
        selection = ElementSelection.from_mapping(raw, position=position)
        if (
            selection.value_present
            and selected_text_tag(selection) == "DATA-ELEMENT-REF"
            and selection.value
            and "/" not in selection.value
        ):
            port = anchored_port(selection)
            candidates = port_interface_refs.get(port, set()) if port else set()
            if len(candidates) != 1:
                reason = "missing" if not candidates else "ambiguous"
                raise ElementSelectionError(
                    f"{reason} exact interface reference for anchored "
                    f"DATA-ELEMENT-REF {selection.value!r}"
                )
            raw["value"] = f"{next(iter(candidates))}/{selection.value}"
        elif (
            selection.value_present
            and selected_text_tag(selection) in local_reference_tags
            and selection.value.startswith("/")
        ):
            segments = [item for item in selection.value.split("/") if item]
            component_indexes = [
                index for index, item in enumerate(segments) if item == component_name
            ]
            if len(component_indexes) == 1:
                suffix = segments[component_indexes[0] + 1 :]
                raw["value"] = "/" + "/".join(
                    ["Components", component_name, *suffix]
                )
        elif (
            selection.value_present
            and selected_text_tag(selection) == "PORT-PROTOTYPE-REF"
            and selection.value
            and "/" not in selection.value
        ):
            # A bare port SHORT-NAME is an unambiguous component-local
            # semantic reference.  The renderer owns the physical package
            # prefix, so compile it before both provider-schema enforcement
            # and parsed-obligation validation.
            raw["value"] = f"/Components/{component_name}/{selection.value}"
    return result


def augment_declared_value_selections(
    component_plan: object,
    obligations: object,
    *,
    xsd_path_index: object,
    requirement_contracts: object = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Compile requirement-declared scalar values into Phase 2 selections.

    These obligations are authored by the structured requirement adapter, not
    inferred from free-form prompt text.  Each obligation is bound to one
    named repeated AUTOSAR element and checked against the pinned physical XSD
    before it may affect Neo4j schema expansion or provider decoding.
    """
    if not isinstance(component_plan, dict):
        raise ElementSelectionError("component plan must be an object")
    if obligations is None:
        obligations = []
    if not isinstance(obligations, list):
        raise ElementSelectionError("generation_value_obligations must be an array")
    if requirement_contracts is None:
        requirement_contracts = []
    if not isinstance(requirement_contracts, list):
        raise ElementSelectionError("generation_requirement_contracts must be an array")

    result = deepcopy(component_plan)
    component_name = str(result.get("name") or "").strip()
    component_type = _tag(result.get("type"))
    element_design = result.get("element_design")
    if not component_name or not component_type or not isinstance(element_design, dict):
        raise ElementSelectionError(
            "component name, type, and element_design are required for value obligations"
        )
    raw_selections = element_design.get("selections")
    if not isinstance(raw_selections, list):
        raise ElementSelectionError("component element_design.selections must be an array")
    absent_value_repairs = _normalize_absent_value_fields(raw_selections)
    suppressed_phase1_selections: list[dict[str, Any]] = []
    applied_authoritative_subtrees: set[tuple[str, ...]] = set()
    declared_anchor_names: dict[tuple[str, ...], set[str]] = {}
    declared_anchor_chains: set[
        tuple[tuple[tuple[str, ...], str], ...]
    ] = set()
    authoritative_subtree_coverages: dict[
        tuple[tuple[str, ...], tuple[str, ...]], set[str]
    ] = {}
    declared_exact_value_chains: dict[
        tuple[tuple[str, ...], str],
        set[tuple[tuple[tuple[str, ...], str], ...]],
    ] = {}
    for obligation_position, raw_obligation in enumerate(obligations):
        if not isinstance(raw_obligation, dict):
            raise ElementSelectionError(
                f"generation_value_obligations[{obligation_position}] must be an object"
            )
        if str(raw_obligation.get("component") or "").strip() != component_name:
            continue
        raw_anchors = raw_obligation.get("anchors")
        if raw_anchors is None:
            continue
        if not isinstance(raw_anchors, list) or not raw_anchors:
            raise ElementSelectionError(
                f"generation_value_obligations[{obligation_position}].anchors "
                "must be a non-empty array"
            )
        declared_chain: list[tuple[tuple[str, ...], str]] = []
        for anchor_position, raw_anchor in enumerate(raw_anchors):
            if not isinstance(raw_anchor, dict):
                raise ElementSelectionError(
                    f"generation_value_obligations[{obligation_position}]."
                    f"anchors[{anchor_position}] must be an object"
                )
            short_name = str(raw_anchor.get("short_name") or "").strip()
            raw_anchor_path = raw_anchor.get("path")
            if not short_name or not isinstance(raw_anchor_path, list):
                raise ElementSelectionError(
                    f"generation_value_obligations[{obligation_position}]."
                    f"anchors[{anchor_position}] requires short_name and path"
                )
            try:
                anchor_resolution = xsd_path_index.resolve_path(
                    component_type,
                    tuple(_tag(item) for item in raw_anchor_path if _tag(item)),
                )
            except Exception as error:
                raise ElementSelectionError(
                    "generation value obligation anchor is not a physical AUTOSAR "
                    f"XSD path: {'/'.join(str(item) for item in raw_anchor_path)}: {error}"
                ) from error
            canonical_anchor_path = tuple(anchor_resolution.canonical_path)
            declared_anchor_names.setdefault(canonical_anchor_path, set()).add(
                short_name
            )
            declared_chain.append((canonical_anchor_path, short_name))
        canonical_declared_chain = tuple(
            sorted(
                declared_chain,
                key=lambda item: (len(item[0]), item[0], item[1]),
            )
        )
        declared_anchor_chains.add(canonical_declared_chain)
        # Every named anchor also declares its physical SHORT-NAME value and
        # the complete ancestor chain required to address that identity.  This
        # gives later normalization an independent, structured source for
        # repairing a model row with a missing parent or an invented extra
        # anchor, without guessing from the provider payload.
        for chain_index, (anchor_path, short_name) in enumerate(
            canonical_declared_chain
        ):
            identity_path = (*anchor_path, "SHORT-NAME", "#TEXT")
            try:
                identity_resolution = xsd_path_index.resolve_path(
                    component_type, identity_path
                )
            except Exception:
                continue
            declared_exact_value_chains.setdefault(
                (tuple(identity_resolution.canonical_path), short_name), set()
            ).add(canonical_declared_chain[: chain_index + 1])
        raw_value_path = raw_obligation.get("path")
        raw_value = raw_obligation.get("value")
        if (
            isinstance(raw_value_path, list)
            and not isinstance(raw_value, bool)
            and isinstance(raw_value, (str, int, float))
        ):
            try:
                value_resolution = xsd_path_index.resolve_path(
                    component_type,
                    tuple(_tag(item) for item in raw_value_path if _tag(item)),
                )
            except Exception:
                value_resolution = None
            if value_resolution is not None:
                declared_exact_value_chains.setdefault(
                    (tuple(value_resolution.canonical_path), str(raw_value)), set()
                ).add(canonical_declared_chain)
        raw_authoritative_subtree = raw_obligation.get(
            "authoritative_subtree_path"
        )
        if raw_authoritative_subtree is not None:
            if not isinstance(raw_authoritative_subtree, list):
                raise ElementSelectionError(
                    f"generation_value_obligations[{obligation_position}]."
                    "authoritative_subtree_path must be an array"
                )
            try:
                subtree_resolution = xsd_path_index.resolve_path(
                    component_type,
                    tuple(
                        _tag(item)
                        for item in raw_authoritative_subtree
                        if _tag(item)
                    ),
                )
            except Exception as error:
                raise ElementSelectionError(
                    "authoritative value subtree is not a physical AUTOSAR XSD path: "
                    + "/".join(str(item) for item in raw_authoritative_subtree)
                ) from error
            canonical_subtree = tuple(subtree_resolution.canonical_path)
            anchor_candidates = [
                (anchor_path, short_name)
                for anchor_path, short_name in declared_chain
                if len(anchor_path) < len(canonical_subtree)
                and canonical_subtree[: len(anchor_path)] == anchor_path
            ]
            if not anchor_candidates:
                raise ElementSelectionError(
                    "authoritative value subtree must be a descendant of a "
                    "structured requirement anchor"
                )
            deepest_length = max(len(anchor_path) for anchor_path, _ in anchor_candidates)
            deepest_candidates = [
                candidate
                for candidate in anchor_candidates
                if len(candidate[0]) == deepest_length
            ]
            if len(deepest_candidates) != 1:
                raise ElementSelectionError(
                    "authoritative value subtree has an ambiguous deepest anchor"
                )
            deepest_path, deepest_name = deepest_candidates[0]
            authoritative_subtree_coverages.setdefault(
                (canonical_subtree, deepest_path), set()
            ).add(deepest_name)

    # A malformed model path must normally fail closed.  The only exception
    # here is a duplicate of one exact, structured requirement value: same
    # scalar, same complete anchor chain, same path length, and exactly one
    # character edit in exactly one segment.  In that case the malformed row
    # adds no information and is discarded; the requirement compiler below
    # emits the pinned physical path.  This is intentionally stricter than a
    # fuzzy path repair and cannot turn an uncorroborated model choice into a
    # valid selection.
    retained_after_malformed_duplicates: list[object] = []
    for selection_position, raw_selection in enumerate(raw_selections):
        if not isinstance(raw_selection, dict):
            retained_after_malformed_duplicates.append(raw_selection)
            continue
        raw_path = tuple(
            _tag(item) for item in (raw_selection.get("path") or []) if _tag(item)
        )
        raw_anchors = raw_selection.get("anchors") or []
        raw_value = str(raw_selection.get("value") or "")
        if (
            not raw_path
            or raw_selection.get("value_present") is not True
            or raw_selection.get("min_occurs") != 1
            or raw_selection.get("max_occurs") != 1
            or not isinstance(raw_anchors, list)
            or not raw_anchors
        ):
            retained_after_malformed_duplicates.append(raw_selection)
            continue
        try:
            xsd_path_index.resolve_path(component_type, raw_path)
        except Exception:
            pass
        else:
            retained_after_malformed_duplicates.append(raw_selection)
            continue

        matching_requirement_facts: set[
            tuple[tuple[str, ...], tuple[tuple[tuple[str, ...], str], ...]]
        ] = set()
        for (declared_path, declared_value), declared_chains in (
            declared_exact_value_chains.items()
        ):
            if declared_value != raw_value or len(declared_path) != len(raw_path):
                continue
            differing = [
                index
                for index, (raw_segment, declared_segment) in enumerate(
                    zip(raw_path, declared_path)
                )
                if raw_segment != declared_segment
            ]
            if (
                len(differing) != 1
                or not _single_edit_apart(
                    raw_path[differing[0]], declared_path[differing[0]]
                )
            ):
                continue
            raw_anchor_pairs: set[tuple[int, str]] = set()
            valid_raw_anchors = True
            for raw_anchor in raw_anchors:
                if not isinstance(raw_anchor, dict):
                    valid_raw_anchors = False
                    break
                try:
                    path_index = int(raw_anchor.get("path_index"))
                except (TypeError, ValueError):
                    valid_raw_anchors = False
                    break
                short_name = str(raw_anchor.get("short_name") or "").strip()
                if not short_name:
                    valid_raw_anchors = False
                    break
                raw_anchor_pairs.add((path_index, short_name))
            if not valid_raw_anchors:
                continue
            for declared_chain in declared_chains:
                expected_anchor_pairs = {
                    (len(anchor_path) - 1, short_name)
                    for anchor_path, short_name in declared_chain
                    if raw_path[: len(anchor_path)] == anchor_path
                }
                if raw_anchor_pairs == expected_anchor_pairs and len(
                    expected_anchor_pairs
                ) == len(declared_chain):
                    matching_requirement_facts.add((declared_path, declared_chain))
        if len(matching_requirement_facts) != 1:
            retained_after_malformed_duplicates.append(raw_selection)
            continue
        declared_path, declared_chain = next(iter(matching_requirement_facts))
        suppressed_phase1_selections.append(
            {
                "obligation_index": None,
                "component": component_name,
                "anchor_short_name": declared_chain[-1][1],
                "authoritative_subtree_path": None,
                "suppressed_path": list(raw_path),
                "suppressed_value_present": True,
                "suppressed_value": raw_value,
                "replacement_path": list(declared_path),
                "reason": (
                    "invalid_near_path_superseded_by_exact_structured_"
                    "requirement_value"
                ),
            }
        )
    raw_selections[:] = retained_after_malformed_duplicates

    # The semantic IR schema permits an anchor array, but JSON Schema cannot
    # express that one path index may identify only one instance.  A provider
    # may therefore use one selection as a broadcast over several named
    # instances.  Expand that representation only when the structured
    # requirement compiler proves the exact complete name set and every
    # resulting parent/child anchor chain.  Unknown, partial, or multi-level
    # broadcasts remain invalid and fail in _canonicalize_anchor_indices.
    multi_anchor_expansions: list[dict[str, Any]] = []
    structured_anchor_index_repairs: list[dict[str, Any]] = []
    expanded_selections: list[object] = []
    aggregate_counts: dict[
        tuple[tuple[str, ...], tuple[tuple[int, str], ...]], int
    ] = {}
    for selection_position, raw_selection in enumerate(raw_selections):
        if not isinstance(raw_selection, dict):
            expanded_selections.append(raw_selection)
            continue
        raw_anchors = raw_selection.get("anchors") or []
        if not isinstance(raw_anchors, list):
            expanded_selections.append(raw_selection)
            continue
        anchors_by_index: dict[int, list[str]] = {}
        valid_anchor_shape = True
        for raw_anchor in raw_anchors:
            if not isinstance(raw_anchor, dict):
                valid_anchor_shape = False
                break
            try:
                path_index = int(raw_anchor.get("path_index"))
            except (TypeError, ValueError):
                valid_anchor_shape = False
                break
            short_name = str(raw_anchor.get("short_name") or "").strip()
            if not short_name:
                valid_anchor_shape = False
                break
            names = anchors_by_index.setdefault(path_index, [])
            if short_name not in names:
                names.append(short_name)
        duplicate_levels = [
            (path_index, names)
            for path_index, names in anchors_by_index.items()
            if len(names) > 1
        ]
        raw_path = tuple(
            _tag(item) for item in (raw_selection.get("path") or []) if _tag(item)
        )
        if (
            not valid_anchor_shape
            or len(duplicate_levels) != 1
            or not raw_path
        ):
            expanded_selections.append(raw_selection)
            continue
        duplicate_index, duplicate_names = duplicate_levels[0]
        if duplicate_index < 0 or duplicate_index >= len(raw_path):
            expanded_selections.append(raw_selection)
            continue
        try:
            resolved_raw_prefixes: dict[tuple[str, ...], list[int]] = {}
            for raw_index in range(len(raw_path)):
                resolution = xsd_path_index.resolve_path(
                    component_type, raw_path[: raw_index + 1]
                )
                resolved_raw_prefixes.setdefault(
                    tuple(resolution.canonical_path), []
                ).append(raw_index)

            canonical_fixed_anchors: list[tuple[tuple[str, ...], str]] = []
            for path_index, names in anchors_by_index.items():
                if path_index == duplicate_index:
                    continue
                if len(names) != 1 or path_index < 0 or path_index >= len(raw_path):
                    raise ElementSelectionError("ambiguous fixed broadcast anchor")
                fixed_resolution = xsd_path_index.resolve_path(
                    component_type, raw_path[: path_index + 1]
                )
                canonical_fixed_anchors.append(
                    (tuple(fixed_resolution.canonical_path), names[0])
                )
        except Exception:
            expanded_selections.append(raw_selection)
            continue

        # Providers sometimes attach a multi-instance identity broadcast to
        # the SHORT-NAME leaf (or its #TEXT projection) instead of the named
        # repeated element.  Normalize only that exact identity-leaf shape,
        # and only when one structured-requirement prefix proves the complete
        # name set.  Arbitrary descendant-anchor relocation remains invalid.
        prefix_candidates: list[tuple[tuple[str, ...], int, set[str]]] = []
        duplicate_name_set = set(duplicate_names)
        for declared_prefix, expected_names in declared_anchor_names.items():
            raw_indexes = resolved_raw_prefixes.get(declared_prefix, [])
            if expected_names != duplicate_name_set or len(raw_indexes) != 1:
                continue
            declared_raw_index = raw_indexes[0]
            identity_suffix = raw_path[declared_raw_index + 1 :]
            direct_anchor = duplicate_index == declared_raw_index
            identity_leaf_anchor = (
                identity_suffix in (("SHORT-NAME",), ("SHORT-NAME", "#TEXT"))
                and duplicate_index > declared_raw_index
            )
            if direct_anchor or identity_leaf_anchor:
                prefix_candidates.append(
                    (declared_prefix, declared_raw_index, expected_names)
                )
        if len(prefix_candidates) != 1:
            expanded_selections.append(raw_selection)
            continue

        canonical_prefix, normalized_duplicate_index, expected_names = (
            prefix_candidates[0]
        )
        selected_declared_chains: list[
            tuple[tuple[tuple[str, ...], str], ...]
        ] = []
        for short_name in sorted(duplicate_names):
            matches = [
                declared_chain
                for declared_chain in declared_anchor_chains
                if (canonical_prefix, short_name) in declared_chain
                and all(
                    fixed_anchor in declared_chain
                    for fixed_anchor in canonical_fixed_anchors
                )
            ]
            if len(matches) != 1:
                selected_declared_chains = []
                break
            selected_declared_chains.append(matches[0])
        if len(selected_declared_chains) != len(duplicate_names):
            expanded_selections.append(raw_selection)
            continue

        shared_declared_anchors = set(selected_declared_chains[0])
        for declared_chain in selected_declared_chains[1:]:
            shared_declared_anchors.intersection_update(declared_chain)
        shared_declared_anchors = {
            anchor
            for anchor in shared_declared_anchors
            if anchor[0] != canonical_prefix
            and len(anchor[0]) < len(canonical_prefix)
            and canonical_prefix[: len(anchor[0])] == anchor[0]
        }

        fixed_raw_anchor_map: dict[int, str] = {}
        proof_failed = False
        for raw_anchor in raw_anchors:
            raw_index = int(raw_anchor["path_index"])
            if raw_index == duplicate_index:
                continue
            short_name = str(raw_anchor["short_name"]).strip()
            previous = fixed_raw_anchor_map.get(raw_index)
            if previous is not None and previous != short_name:
                proof_failed = True
                break
            fixed_raw_anchor_map[raw_index] = short_name
        if not proof_failed:
            for anchor_path, short_name in sorted(
                shared_declared_anchors,
                key=lambda item: (len(item[0]), item[0], item[1]),
            ):
                raw_indexes = resolved_raw_prefixes.get(anchor_path, [])
                if len(raw_indexes) != 1:
                    proof_failed = True
                    break
                raw_index = raw_indexes[0]
                previous = fixed_raw_anchor_map.get(raw_index)
                if previous is not None and previous != short_name:
                    proof_failed = True
                    break
                fixed_raw_anchor_map[raw_index] = short_name
        if proof_failed:
            expanded_selections.append(raw_selection)
            continue

        fixed_raw_anchors = [
            {"path_index": path_index, "short_name": short_name}
            for path_index, short_name in sorted(fixed_raw_anchor_map.items())
        ]
        aggregate_path = raw_path[: normalized_duplicate_index + 1]
        aggregate_anchor_key = tuple(
            (anchor["path_index"], anchor["short_name"])
            for anchor in fixed_raw_anchors
        )

        aggregate_counts[(aggregate_path, aggregate_anchor_key)] = len(expected_names)
        for short_name in sorted(expected_names):
            expanded = deepcopy(raw_selection)
            expanded["anchors"] = sorted(
                [
                    *deepcopy(fixed_raw_anchors),
                    {
                        "path_index": normalized_duplicate_index,
                        "short_name": short_name,
                    },
                ],
                key=lambda anchor: int(anchor["path_index"]),
            )
            expanded["min_occurs"] = 1
            expanded["max_occurs"] = 1
            expanded["notes"] = (
                "Deterministically expanded from a requirement-proven "
                "multi-instance anchor broadcast."
            )
            expanded_selections.append(expanded)
        multi_anchor_expansions.append(
            {
                "selection_index": selection_position,
                "path": list(raw_path),
                "anchor_path": list(canonical_prefix),
                "anchor_names": sorted(expected_names),
                "expanded_selection_count": len(expected_names),
                "original_anchor_path_index": duplicate_index,
                "canonical_anchor_path_index": normalized_duplicate_index,
                "synthesized_parent_anchors": deepcopy(fixed_raw_anchors),
            }
        )

    def _raw_anchor_key(candidate: dict[str, Any]) -> tuple[tuple[int, str], ...] | None:
        raw_candidate_anchors = candidate.get("anchors") or []
        if not isinstance(raw_candidate_anchors, list):
            return None
        normalized: list[tuple[int, str]] = []
        for raw_anchor in raw_candidate_anchors:
            if not isinstance(raw_anchor, dict):
                return None
            try:
                path_index = int(raw_anchor.get("path_index"))
            except (TypeError, ValueError):
                return None
            short_name = str(raw_anchor.get("short_name") or "").strip()
            if not short_name:
                return None
            normalized.append((path_index, short_name))
        return tuple(sorted(normalized))

    for (aggregate_path, aggregate_anchor_key), exact_count in sorted(
        aggregate_counts.items()
    ):
        matching_indexes = [
            position
            for position, candidate in enumerate(expanded_selections)
            if isinstance(candidate, dict)
            and tuple(
                _tag(item) for item in (candidate.get("path") or []) if _tag(item)
            )
            == aggregate_path
            and _raw_anchor_key(candidate) == aggregate_anchor_key
            and candidate.get("value_present") is False
        ]
        aggregate = {
            "path": list(aggregate_path),
            "min_occurs": exact_count,
            "max_occurs": exact_count,
            "value_present": False,
            "value": "",
            "anchors": [
                {"path_index": path_index, "short_name": short_name}
                for path_index, short_name in aggregate_anchor_key
            ],
            "notes": (
                "System-derived exact collection count from the complete "
                "structured requirement anchor set."
            ),
        }
        if matching_indexes:
            keep = matching_indexes[0]
            expanded_selections[keep] = aggregate
            for position in reversed(matching_indexes[1:]):
                expanded_selections.pop(position)
        else:
            expanded_selections.append(aggregate)
    raw_selections[:] = expanded_selections

    # Explicit structured anchors define a complete named instance set for
    # their collection.  Remove model-invented identities in that same set and
    # every branch bound to them before parsing/compiling the Phase 1 IR.
    extraneous_anchor_names: set[str] = set()
    for raw_selection in raw_selections:
        if not isinstance(raw_selection, dict):
            continue
        selection_path = tuple(
            _tag(item) for item in (raw_selection.get("path") or []) if _tag(item)
        )
        if selection_path[-1:] == ("SHORT-NAME",):
            prefix = selection_path[:-1]
        elif selection_path[-2:] == ("SHORT-NAME", "#TEXT"):
            prefix = selection_path[:-2]
        else:
            continue
        value = str(raw_selection.get("value") or "").strip()
        expected_names = declared_anchor_names.get(prefix)
        if (
            expected_names is not None
            and raw_selection.get("value_present") is True
            and value
            and value not in expected_names
        ):
            extraneous_anchor_names.add(value)
    if extraneous_anchor_names:
        retained_phase1: list[object] = []
        for selection_position, raw_selection in enumerate(raw_selections):
            if not isinstance(raw_selection, dict):
                retained_phase1.append(raw_selection)
                continue
            value = str(raw_selection.get("value") or "").strip()
            anchor_names = {
                str(anchor.get("short_name") or "").strip()
                for anchor in (raw_selection.get("anchors") or [])
                if isinstance(anchor, dict)
            }
            conflicts = sorted(
                ({value} if value in extraneous_anchor_names else set())
                | (anchor_names & extraneous_anchor_names)
            )
            if not conflicts:
                retained_phase1.append(raw_selection)
                continue
            suppressed_phase1_selections.append(
                {
                    "obligation_index": None,
                    "component": component_name,
                    "anchor_short_name": conflicts[0],
                    "authoritative_subtree_path": None,
                    "suppressed_path": list(raw_selection.get("path") or []),
                    "suppressed_value_present": bool(
                        raw_selection.get("value_present")
                    ),
                    "suppressed_value": raw_selection.get("value"),
                    "reason": (
                        "conflicts_with_structured_requirement_instance_identity"
                    ),
                }
            )
        raw_selections[:] = retained_phase1

    # Providers sometimes serialize a repeated scalar collection as one
    # semicolon-delimited value.  Such a value is not a legal scalar and must
    # never reach deterministic materialization.  Discard it only when the
    # structured requirement supplies the complete, instance-bound value
    # multiset for the exact same physical path and the declared instance
    # count matches the fixed aggregate occurrence.  Otherwise retain it so
    # the ordinary compiler/materializer fails closed.
    retained_after_delimited_aggregates: list[object] = []
    for selection_position, raw_selection in enumerate(raw_selections):
        if not isinstance(raw_selection, dict):
            retained_after_delimited_aggregates.append(raw_selection)
            continue
        raw_value = raw_selection.get("value")
        raw_anchors = raw_selection.get("anchors") or []
        minimum = raw_selection.get("min_occurs")
        maximum = raw_selection.get("max_occurs")
        if (
            raw_selection.get("value_present") is not True
            or raw_anchors
            or not isinstance(raw_value, str)
            or ";" not in raw_value
            or isinstance(minimum, bool)
            or not isinstance(minimum, int)
            or minimum < 2
            or maximum != minimum
        ):
            retained_after_delimited_aggregates.append(raw_selection)
            continue
        raw_path = tuple(
            _tag(item) for item in (raw_selection.get("path") or []) if _tag(item)
        )
        try:
            canonical_path = tuple(
                xsd_path_index.resolve_path(component_type, raw_path).canonical_path
            )
        except Exception:
            retained_after_delimited_aggregates.append(raw_selection)
            continue
        declared_by_chain: dict[
            tuple[tuple[tuple[str, ...], str], ...], str
        ] = {}
        conflicting_chain = False
        for (declared_path, declared_value), declared_chains in (
            declared_exact_value_chains.items()
        ):
            if declared_path != canonical_path:
                continue
            for declared_chain in declared_chains:
                previous = declared_by_chain.get(declared_chain)
                if previous is not None and previous != declared_value:
                    conflicting_chain = True
                    break
                declared_by_chain[declared_chain] = declared_value
            if conflicting_chain:
                break
        aggregate_values = [item.strip() for item in raw_value.split(";")]
        complete_structured_replacement = (
            not conflicting_chain
            and len(aggregate_values) == minimum
            and all(aggregate_values)
            and len(declared_by_chain) == minimum
            and all(declared_by_chain)
            and sorted(aggregate_values) == sorted(declared_by_chain.values())
        )
        if not complete_structured_replacement:
            retained_after_delimited_aggregates.append(raw_selection)
            continue
        suppressed_phase1_selections.append(
            {
                "obligation_index": None,
                "component": component_name,
                "anchor_short_name": None,
                "authoritative_subtree_path": None,
                "suppressed_path": list(canonical_path),
                "suppressed_value_present": True,
                "suppressed_value": raw_value,
                "reason": (
                    "delimiter_aggregate_superseded_by_instance_bound_"
                    "structured_values"
                ),
                "aggregate_count": minimum,
                "declared_instance_count": len(declared_by_chain),
            }
        )
    raw_selections[:] = retained_after_delimited_aggregates
    # Bind an otherwise unanchored exact value to structured requirement
    # instances only when path, value, XSD prefixes, and instance coverage make
    # the mapping deterministic.  A unique value identity binds directly.  A
    # shared value may broadcast only across the complete declared name set.
    # A multi-parent broadcast is also deterministic when the selection's
    # exact multiplicity equals the complete set of distinct requirement-owned
    # chains.  This covers uniform constants such as @DEST that legitimately
    # repeat under several runnable/access parents without treating a partial
    # or default-minimum row as an instruction to fill every instance.
    structured_value_anchor_bindings: list[dict[str, Any]] = []
    value_bound_selections: list[object] = []
    for selection_position, raw_selection in enumerate(raw_selections):
        if not isinstance(raw_selection, dict):
            value_bound_selections.append(raw_selection)
            continue
        raw_anchors = raw_selection.get("anchors") or []
        raw_path = tuple(
            _tag(item) for item in (raw_selection.get("path") or []) if _tag(item)
        )
        value = str(raw_selection.get("value") or "")
        if (
            raw_anchors
            or not raw_path
            or raw_selection.get("value_present") is not True
        ):
            value_bound_selections.append(raw_selection)
            continue
        try:
            resolved_raw_prefixes: dict[tuple[str, ...], list[int]] = {}
            for raw_index in range(len(raw_path)):
                resolution = xsd_path_index.resolve_path(
                    component_type, raw_path[: raw_index + 1]
                )
                resolved_raw_prefixes.setdefault(
                    tuple(resolution.canonical_path), []
                ).append(raw_index)
            canonical_path = tuple(
                xsd_path_index.resolve_path(component_type, raw_path).canonical_path
            )
            direct_text_check = getattr(
                xsd_path_index, "requires_direct_text_leaf", None
            )
            if (
                canonical_path
                and canonical_path[-1] != "#TEXT"
                and not canonical_path[-1].startswith("@")
                and callable(direct_text_check)
                and direct_text_check(component_type, canonical_path)
            ):
                canonical_path = (*canonical_path, "#TEXT")
        except Exception:
            value_bound_selections.append(raw_selection)
            continue
        candidate_chains = sorted(
            declared_exact_value_chains.get((canonical_path, value), set()),
            key=lambda chain: tuple(
                (len(path), path, short_name) for path, short_name in chain
            ),
        )
        if not candidate_chains and canonical_path[-1:] != ("#TEXT",):
            text_path = (*canonical_path, "#TEXT")
            try:
                text_resolution = xsd_path_index.resolve_path(
                    component_type, text_path
                )
            except Exception:
                text_resolution = None
            if text_resolution is not None:
                resolved_text_path = tuple(text_resolution.canonical_path)
                candidate_chains = sorted(
                    declared_exact_value_chains.get(
                        (resolved_text_path, value), set()
                    ),
                    key=lambda chain: tuple(
                        (len(path), path, short_name)
                        for path, short_name in chain
                    ),
                )
                if candidate_chains:
                    canonical_path = resolved_text_path
        if not candidate_chains:
            value_bound_selections.append(raw_selection)
            continue

        normalized_chains: list[tuple[tuple[int, str], ...]] = []
        for declared_chain in candidate_chains:
            normalized_chain: list[tuple[int, str]] = []
            for anchor_path, short_name in declared_chain:
                raw_indexes = resolved_raw_prefixes.get(anchor_path, [])
                if len(raw_indexes) != 1:
                    raise ElementSelectionError(
                        f"selection[{selection_position}] exact structured value "
                        f"anchor {short_name!r} is not a unique path prefix"
                    )
                normalized_chain.append((raw_indexes[0], short_name))
            if len({index for index, _ in normalized_chain}) != len(normalized_chain):
                raise ElementSelectionError(
                    f"selection[{selection_position}] exact structured value has "
                    "duplicate anchor path indexes"
                )
            normalized_chains.append(tuple(normalized_chain))

        if len(candidate_chains) > 1:
            deepest_entries = [declared_chain[-1] for declared_chain in candidate_chains]
            deepest_paths = {path for path, _ in deepest_entries}
            deepest_names = [short_name for _, short_name in deepest_entries]
            minimum = raw_selection.get("min_occurs")
            maximum = raw_selection.get("max_occurs")
            exact_complete_multiplicity = (
                not isinstance(minimum, bool)
                and isinstance(minimum, int)
                and minimum == maximum == len(candidate_chains)
            )
            complete_broadcast = (
                len(deepest_paths) == 1
                and len(deepest_names) == len(set(deepest_names))
                and declared_anchor_names.get(next(iter(deepest_paths)))
                == set(deepest_names)
                and (
                    len({declared_chain[:-1] for declared_chain in candidate_chains})
                    == 1
                    or exact_complete_multiplicity
                )
            )
            if not complete_broadcast:
                raise ElementSelectionError(
                    f"selection[{selection_position}] unanchored exact value has "
                    "ambiguous structured requirement instances"
                )

        for normalized_chain in normalized_chains:
            bound = deepcopy(raw_selection)
            bound["anchors"] = [
                {"path_index": path_index, "short_name": short_name}
                for path_index, short_name in normalized_chain
            ]
            bound["min_occurs"] = 1
            bound["max_occurs"] = 1
            bound["notes"] = (
                "Deterministically bound to an exact structured requirement value."
            )
            value_bound_selections.append(bound)
        structured_value_anchor_bindings.append(
            {
                "selection_index": selection_position,
                "path": list(canonical_path),
                "value": value,
                "bound_instance_count": len(normalized_chains),
                "anchors": [
                    [
                        {"path_index": path_index, "short_name": short_name}
                        for path_index, short_name in normalized_chain
                    ]
                    for normalized_chain in normalized_chains
                ],
            }
        )
    raw_selections[:] = value_bound_selections

    # Correct anchored exact-value rows only when the frozen requirement gives
    # one unique complete anchor chain.  Recognized anchors must agree with the
    # candidate chain; unknown extras may be discarded because path+value have
    # already selected one requirement-owned fact.  Ambiguous exact values are
    # left to the ordinary fail-closed parser.
    structured_anchor_chain_repairs: list[dict[str, Any]] = []
    for selection_position, raw_selection in enumerate(raw_selections):
        if not isinstance(raw_selection, dict):
            continue
        raw_anchors = raw_selection.get("anchors") or []
        raw_path = tuple(
            _tag(item) for item in (raw_selection.get("path") or []) if _tag(item)
        )
        if (
            not raw_anchors
            or not isinstance(raw_anchors, list)
            or not raw_path
            or raw_selection.get("value_present") is not True
        ):
            continue
        try:
            canonical_path = tuple(
                xsd_path_index.resolve_path(component_type, raw_path).canonical_path
            )
            resolved_raw_prefixes: dict[tuple[str, ...], list[int]] = {}
            for raw_index in range(len(raw_path)):
                resolution = xsd_path_index.resolve_path(
                    component_type, raw_path[: raw_index + 1]
                )
                resolved_raw_prefixes.setdefault(
                    tuple(resolution.canonical_path), []
                ).append(raw_index)
        except Exception:
            continue
        value = str(raw_selection.get("value") or "")
        candidate_chains = set(
            declared_exact_value_chains.get((canonical_path, value), set())
        )
        if not candidate_chains:
            continue
        recognized: list[tuple[tuple[str, ...], str]] = []
        unknown_anchor_names: list[str] = []
        ambiguous_anchor = False
        for raw_anchor in raw_anchors:
            if not isinstance(raw_anchor, dict):
                ambiguous_anchor = True
                break
            short_name = str(raw_anchor.get("short_name") or "").strip()
            matching_paths = {
                declared_path
                for declared_path, names in declared_anchor_names.items()
                if short_name in names
                and declared_path in resolved_raw_prefixes
            }
            if len(matching_paths) == 1:
                recognized.append((next(iter(matching_paths)), short_name))
            elif not matching_paths:
                unknown_anchor_names.append(short_name)
            else:
                ambiguous_anchor = True
                break
        if ambiguous_anchor:
            continue
        compatible_chains = {
            chain
            for chain in candidate_chains
            if all(anchor in chain for anchor in recognized)
        }
        if len(compatible_chains) != 1:
            continue
        selected_chain = next(iter(compatible_chains))
        normalized_anchors: list[dict[str, Any]] = []
        for anchor_path, short_name in selected_chain:
            raw_indexes = resolved_raw_prefixes.get(anchor_path, [])
            if len(raw_indexes) != 1:
                normalized_anchors = []
                break
            normalized_anchors.append(
                {"path_index": raw_indexes[0], "short_name": short_name}
            )
        if not normalized_anchors:
            continue
        original_anchors = deepcopy(raw_anchors)
        if original_anchors == normalized_anchors and (
            raw_selection.get("min_occurs"), raw_selection.get("max_occurs")
        ) == (1, 1):
            continue
        raw_selection["anchors"] = normalized_anchors
        raw_selection["min_occurs"] = 1
        raw_selection["max_occurs"] = 1
        raw_selection["notes"] = (
            "Deterministically normalized to the unique frozen requirement "
            "anchor chain for this exact value."
        )
        structured_anchor_chain_repairs.append(
            {
                "selection_index": selection_position,
                "path": list(canonical_path),
                "value": value,
                "original_anchors": original_anchors,
                "canonical_anchors": deepcopy(normalized_anchors),
                "discarded_unknown_anchor_names": sorted(
                    name for name in unknown_anchor_names if name
                ),
            }
        )

    # ``path_index`` is a projection coordinate, not AUTOSAR semantic intent.
    # Normalize it from the structured requirement only when one declared,
    # hash-pinned XSD prefix uniquely binds the anchor name on this selection
    # path.  Unknown or multiply-declared names remain untouched/ambiguous and
    # therefore fail in the ordinary parser below.
    for selection_position, raw_selection in enumerate(raw_selections):
        if not isinstance(raw_selection, dict):
            continue
        raw_path = tuple(
            _tag(item) for item in (raw_selection.get("path") or []) if _tag(item)
        )
        raw_anchors = raw_selection.get("anchors") or []
        if not raw_path or not isinstance(raw_anchors, list):
            continue
        resolved_raw_prefixes: dict[tuple[str, ...], list[int]] = {}
        for raw_index in range(len(raw_path)):
            try:
                resolution = xsd_path_index.resolve_path(
                    component_type, raw_path[: raw_index + 1]
                )
            except Exception:
                continue
            resolved_raw_prefixes.setdefault(
                tuple(resolution.canonical_path), []
            ).append(raw_index)
        for anchor_position, raw_anchor in enumerate(raw_anchors):
            if not isinstance(raw_anchor, dict):
                continue
            short_name = str(raw_anchor.get("short_name") or "").strip()
            if not short_name:
                continue
            candidate_indexes = {
                raw_index
                for declared_path, expected_names in declared_anchor_names.items()
                if short_name in expected_names
                for raw_index in resolved_raw_prefixes.get(declared_path, [])
            }
            if len(candidate_indexes) > 1:
                raise ElementSelectionError(
                    f"selection[{selection_position}].anchors[{anchor_position}] has "
                    f"ambiguous structured requirement definition {short_name!r}"
                )
            if len(candidate_indexes) != 1:
                continue
            canonical_index = next(iter(candidate_indexes))
            original_index = raw_anchor.get("path_index")
            if original_index == canonical_index:
                continue
            raw_anchor["path_index"] = canonical_index
            structured_anchor_index_repairs.append(
                {
                    "selection_index": selection_position,
                    "anchor_index": anchor_position,
                    "short_name": short_name,
                    "original_path_index": original_index,
                    "canonical_path_index": canonical_index,
                }
            )
    # The structured requirement is what makes several names at one path index
    # readable as separate instances rather than as a contradiction, so the
    # declared anchors travel with the design here and nowhere else.
    _canonicalize_anchor_indices(raw_selections, declared_anchor_names)
    selections = parse_element_selections(element_design)

    named_prefixes: dict[str, set[tuple[str, ...]]] = {}
    for selection in selections:
        for anchor in selection.anchors:
            named_prefixes.setdefault(anchor.short_name, set()).add(
                selection.path[: anchor.path_index + 1]
            )
        if not selection.value_present or not selection.value.strip():
            continue
        if selection.path[-1:] == ("SHORT-NAME",):
            prefix = selection.path[:-1]
        elif selection.path[-2:] == ("SHORT-NAME", "#TEXT"):
            prefix = selection.path[:-2]
        else:
            continue
        named_prefixes.setdefault(selection.value.strip(), set()).add(prefix)

    existing: dict[
        tuple[tuple[str, ...], tuple[tuple[int, str], ...]],
        tuple[ElementSelection, dict[str, Any]],
    ] = {}
    for selection_position, raw_selection in enumerate(raw_selections):
        selection = ElementSelection.from_mapping(
            raw_selection, position=selection_position
        )
        anchor_key = tuple(
            (anchor.path_index, anchor.short_name) for anchor in selection.anchors
        )
        existing[(selection.path, anchor_key)] = (selection, raw_selection)

    applied: list[dict[str, Any]] = []
    derived_anchor_identities: list[dict[str, Any]] = []
    ignored_other_components: list[int] = []
    for position, raw in enumerate(obligations):
        if not isinstance(raw, dict):
            raise ElementSelectionError(
                f"generation_value_obligations[{position}] must be an object"
            )
        target_component = str(raw.get("component") or "").strip()
        if not target_component:
            raise ElementSelectionError(
                f"generation_value_obligations[{position}].component is required"
            )
        if target_component != component_name:
            ignored_other_components.append(position)
            continue
        requirement_id = str(raw.get("requirement_id") or "").strip()
        if requirement_contracts and not requirement_id:
            raise ElementSelectionError(
                f"generation_value_obligations[{position}].requirement_id is required "
                "when generation requirement contracts are present"
            )
        raw_path = raw.get("path")
        if not isinstance(raw_path, list):
            raise ElementSelectionError(
                f"generation_value_obligations[{position}].path must be an array"
            )
        path = tuple(_tag(item) for item in raw_path if _tag(item))
        raw_value = raw.get("value")
        if isinstance(raw_value, bool) or not isinstance(raw_value, (str, int, float)):
            raise ElementSelectionError(
                f"generation_value_obligations[{position}].value must be a scalar"
            )
        value = str(raw_value)
        try:
            resolution = xsd_path_index.resolve_path(component_type, path)
        except Exception as error:
            raise ElementSelectionError(
                f"generation value obligation is not a physical AUTOSAR XSD path for "
                f"{component_type}: {'/'.join(path)}: {error}"
            ) from error
        canonical_path = tuple(resolution.canonical_path)
        explicit_anchors = raw.get("anchors")
        resolved_anchors: list[tuple[int, str]] = []
        if explicit_anchors is not None:
            if not isinstance(explicit_anchors, list) or not explicit_anchors:
                raise ElementSelectionError(
                    f"generation_value_obligations[{position}].anchors must be a non-empty array"
                )
            for anchor_position, raw_anchor in enumerate(explicit_anchors):
                if not isinstance(raw_anchor, dict):
                    raise ElementSelectionError(
                        f"generation_value_obligations[{position}].anchors[{anchor_position}] "
                        "must be an object"
                    )
                anchor_short_name = str(
                    raw_anchor.get("short_name") or ""
                ).strip()
                raw_anchor_path = raw_anchor.get("path")
                if not anchor_short_name or not isinstance(raw_anchor_path, list):
                    raise ElementSelectionError(
                        f"generation_value_obligations[{position}].anchors[{anchor_position}] "
                        "requires short_name and path"
                    )
                anchor_path = tuple(
                    _tag(item) for item in raw_anchor_path if _tag(item)
                )
                try:
                    anchor_resolution = xsd_path_index.resolve_path(
                        component_type, anchor_path
                    )
                except Exception as error:
                    raise ElementSelectionError(
                        "generation value obligation anchor is not a physical AUTOSAR "
                        f"XSD path: {'/'.join(anchor_path)}: {error}"
                    ) from error
                canonical_anchor_path = tuple(anchor_resolution.canonical_path)
                if (
                    not canonical_anchor_path
                    or canonical_path[: len(canonical_anchor_path)]
                    != canonical_anchor_path
                ):
                    raise ElementSelectionError(
                        "generation value obligation anchor path is not a prefix of its value path"
                    )
                anchor_index = len(canonical_anchor_path) - 1
                current_anchor = (anchor_index, anchor_short_name)
                if canonical_anchor_path not in named_prefixes.get(
                    anchor_short_name, set()
                ):
                    identity_path = (*canonical_anchor_path, "SHORT-NAME", "#TEXT")
                    try:
                        identity_resolution = xsd_path_index.resolve_path(
                            component_type, identity_path
                        )
                    except Exception as error:
                        raise ElementSelectionError(
                            "structured requirement anchor has no physical SHORT-NAME "
                            f"identity path: {'/'.join(identity_path)}: {error}"
                        ) from error
                    canonical_identity_path = tuple(
                        identity_resolution.canonical_path
                    )
                    if canonical_identity_path != identity_path:
                        raise ElementSelectionError(
                            "structured requirement anchor identity required an "
                            "unexpected XSD path repair"
                        )
                    identity_anchors = [*resolved_anchors, current_anchor]
                    generated_identity = {
                        "path": list(canonical_identity_path),
                        "min_occurs": 1,
                        "max_occurs": 1,
                        "value_present": True,
                        "value": anchor_short_name,
                        "anchors": [
                            {"path_index": index, "short_name": short_name}
                            for index, short_name in identity_anchors
                        ],
                        "notes": (
                            "System-derived named instance from a complete structured "
                            "requirement anchor set."
                        ),
                    }
                    obligation_is_identity = (
                        canonical_identity_path == canonical_path
                        and value == anchor_short_name
                    )
                    if not obligation_is_identity:
                        raw_selections.append(generated_identity)
                    named_prefixes.setdefault(anchor_short_name, set()).add(
                        canonical_anchor_path
                    )
                    if not obligation_is_identity:
                        derived_anchor_identities.append(
                            {
                                "obligation_index": position,
                                "path": list(canonical_identity_path),
                                "short_name": anchor_short_name,
                                "anchors": list(generated_identity["anchors"]),
                            }
                        )
                resolved_anchors.append(current_anchor)
        else:
            anchor_short_name = str(raw.get("anchor_short_name") or "").strip()
            if not anchor_short_name:
                raise ElementSelectionError(
                    f"generation_value_obligations[{position}].anchor_short_name is required"
                )
            candidate_prefixes = {
                prefix
                for prefix in named_prefixes.get(anchor_short_name, set())
                if len(prefix) <= len(canonical_path)
                and canonical_path[: len(prefix)] == prefix
            }
            if len(candidate_prefixes) != 1:
                reason = "missing" if not candidate_prefixes else "ambiguous"
                raise ElementSelectionError(
                    f"generation value obligation anchor {anchor_short_name!r} is {reason} "
                    f"in Phase 1 selections for component {component_name!r}"
                )
            anchor_prefix = next(iter(candidate_prefixes))
            resolved_anchors.append((len(anchor_prefix) - 1, anchor_short_name))
        if len({index for index, _name in resolved_anchors}) != len(resolved_anchors):
            raise ElementSelectionError(
                f"generation_value_obligations[{position}] has duplicate anchor path indexes"
            )
        resolved_anchors.sort(key=lambda item: item[0])
        anchor_key = tuple(resolved_anchors)
        deepest_anchor_index, deepest_anchor_name = anchor_key[-1]
        raw_subtree_path = raw.get("authoritative_subtree_path")
        authoritative_subtree: tuple[str, ...] | None = None
        if raw_subtree_path is not None:
            if not isinstance(raw_subtree_path, list):
                raise ElementSelectionError(
                    f"generation_value_obligations[{position}]."
                    "authoritative_subtree_path must be an array"
                )
            authoritative_subtree = tuple(
                _tag(item) for item in raw_subtree_path if _tag(item)
            )
            if (
                len(authoritative_subtree) <= deepest_anchor_index
                or canonical_path[: len(authoritative_subtree)]
                != authoritative_subtree
            ):
                raise ElementSelectionError(
                    "authoritative value subtree must be a descendant of the "
                    "named anchor and a prefix of the exact value path"
                )
            try:
                xsd_path_index.resolve_path(component_type, authoritative_subtree)
            except Exception as error:
                raise ElementSelectionError(
                    "authoritative value subtree is not a physical AUTOSAR XSD path: "
                    + "/".join(authoritative_subtree)
                ) from error

            applied_authoritative_subtrees.add(authoritative_subtree)
            retained_raw: list[object] = []
            for selection_position, raw_selection in enumerate(raw_selections):
                candidate = ElementSelection.from_mapping(
                    raw_selection, position=selection_position
                )
                if candidate.path[: len(authoritative_subtree)] != authoritative_subtree:
                    retained_raw.append(raw_selection)
                    continue
                candidate_anchor_names = {
                    anchor.short_name for anchor in candidate.anchors
                }
                if not candidate_anchor_names:
                    # The requirement owns this subtree.  An unanchored Phase 1
                    # selection inside it is bound to no named instance, so it
                    # is not evidence about any of them; the compiler emits one
                    # exact selection per declared instance either way.  This
                    # used to be accepted only when the model's aggregate
                    # occurrence happened to equal the number of declared
                    # instances, which made a correct requirement unbuildable
                    # whenever the model miscounted a subtree it was not
                    # responsible for.
                    declared_instances = sorted(
                        {
                            name
                            for (subtree_path, _anchor_path), names
                            in authoritative_subtree_coverages.items()
                            if subtree_path == authoritative_subtree
                            for name in names
                        }
                    )
                    suppressed_phase1_selections.append(
                        {
                            "obligation_index": position,
                            "component": component_name,
                            "anchor_short_name": deepest_anchor_name,
                            "authoritative_subtree_path": list(authoritative_subtree),
                            "suppressed_path": list(candidate.path),
                            "suppressed_value_present": candidate.value_present,
                            "suppressed_value": candidate.value,
                            "suppressed_min_occurs": candidate.min_occurs,
                            "suppressed_max_occurs": candidate.max_occurs,
                            "declared_instances": declared_instances,
                            "reason": (
                                "redundant_unanchored_aggregate_superseded_by_"
                                "requirement_owned_subtree"
                                if candidate.path == authoritative_subtree
                                else "unanchored_candidate_superseded_by_"
                                "requirement_owned_subtree"
                            ),
                        }
                    )
                    continue
                if deepest_anchor_name not in candidate_anchor_names:
                    retained_raw.append(raw_selection)
                    continue
                compatible = (
                    len(candidate.path) <= len(canonical_path)
                    and canonical_path[: len(candidate.path)] == candidate.path
                )
                if compatible:
                    retained_raw.append(raw_selection)
                    continue
                suppressed_phase1_selections.append(
                    {
                        "obligation_index": position,
                        "component": component_name,
                        "anchor_short_name": deepest_anchor_name,
                        "authoritative_subtree_path": list(authoritative_subtree),
                        "suppressed_path": list(candidate.path),
                        "suppressed_value_present": candidate.value_present,
                        "suppressed_value": candidate.value,
                        "reason": "conflicts_with_structured_requirement_value_branch",
                    }
                )
            raw_selections[:] = retained_raw
            selections = parse_element_selections(element_design)
            existing = {}
            for selection_position, raw_selection in enumerate(raw_selections):
                selection = ElementSelection.from_mapping(
                    raw_selection, position=selection_position
                )
                selection_anchor_key = tuple(
                    (anchor.path_index, anchor.short_name)
                    for anchor in selection.anchors
                )
                existing[(selection.path, selection_anchor_key)] = (
                    selection,
                    raw_selection,
                )

        identity = (canonical_path, anchor_key)
        previous_entry = existing.get(identity)
        if previous_entry is not None:
            previous, previous_raw = previous_entry
            if not previous.value_present:
                previous_raw["value_present"] = True
                previous_raw["value"] = value
                previous_raw["min_occurs"] = 1
                previous_raw["max_occurs"] = 1
                previous_raw["notes"] = (
                    "Deterministically materialized from a structured "
                    "requirement value obligation."
                )
                normalized = ElementSelection.from_mapping(
                    previous_raw, position=-1
                )
                existing[identity] = (normalized, previous_raw)
                outcome = "materialized_exact_value"
            elif previous.value != value:
                raise ElementSelectionError(
                    "generation value obligation conflicts with Phase 1 selection at "
                    + "/".join(canonical_path)
                )
            elif (previous.min_occurs, previous.max_occurs) != (1, 1):
                previous_raw["min_occurs"] = 1
                previous_raw["max_occurs"] = 1
                normalized = ElementSelection.from_mapping(
                    previous_raw, position=-1
                )
                existing[identity] = (normalized, previous_raw)
                outcome = "normalized_exact_value_occurrence"
            else:
                outcome = "already_selected"
        else:
            generated = {
                "path": list(canonical_path),
                "min_occurs": 1,
                "max_occurs": 1,
                "value_present": True,
                "value": value,
                "anchors": [
                    {"path_index": index, "short_name": short_name}
                    for index, short_name in anchor_key
                ],
                "notes": "System-derived from a structured requirement value obligation.",
            }
            raw_selections.append(generated)
            existing[identity] = (
                ElementSelection.from_mapping(
                    generated, position=len(raw_selections) - 1
                ),
                generated,
            )
            outcome = "derived"
        applied.append(
            {
                "obligation_index": position,
                "requirement_id": requirement_id,
                "component": component_name,
                "path": list(canonical_path),
                "anchor_short_name": deepest_anchor_name,
                "anchors": [
                    {"path_index": index, "short_name": short_name}
                    for index, short_name in anchor_key
                ],
                "value": value,
                "authoritative_subtree_path": list(authoritative_subtree)
                if authoritative_subtree is not None
                else None,
                "xsd_resolution": str(resolution.resolution),
                "outcome": outcome,
            }
        )

    # Suppressing the model's view of a requirement-owned subtree is only safe
    # while the compiler's own bound selections are the sole survivors inside
    # it.  An unanchored selection reaching this point would mean the subtree
    # was emptied without being rebuilt.
    for selection_position, raw_selection in enumerate(raw_selections):
        candidate = ElementSelection.from_mapping(
            raw_selection, position=selection_position
        )
        if candidate.anchors:
            continue
        for subtree in applied_authoritative_subtrees:
            if candidate.path[: len(subtree)] == subtree:
                raise ElementSelectionError(
                    "an unbound selection survived inside requirement-owned value "
                    "subtree " + "/".join(subtree) + " at " + "/".join(candidate.path)
                )

    # Phase 1 sometimes reports a total count beneath repeated named parents
    # as though it were the XSD occurrence of each parent-local child.  That
    # would turn three runnables with one access each into three accesses per
    # runnable.  Remove such an unanchored aggregate only when structured
    # obligations prove every exact child instance and its distinct parent.
    retained_raw: list[object] = []
    for selection_position, raw_selection in enumerate(raw_selections):
        candidate = ElementSelection.from_mapping(
            raw_selection, position=selection_position
        )
        if (
            candidate.anchors
            or candidate.value_present
            or candidate.min_occurs < 1
            or candidate.min_occurs != candidate.max_occurs
        ):
            retained_raw.append(raw_selection)
            continue
        if (
            candidate.path[-1:] == ("SHORT-NAME",)
            or candidate.path[-2:] == ("SHORT-NAME", "#TEXT")
        ):
            named_parent = (
                candidate.path[:-1]
                if candidate.path[-1:] == ("SHORT-NAME",)
                else candidate.path[:-2]
            )
            declared_names = declared_anchor_names.get(named_parent, set())
            if (
                len(declared_names) >= 2
                and len(declared_names) == candidate.min_occurs
            ):
                suppressed_phase1_selections.append(
                    {
                        "obligation_index": None,
                        "component": component_name,
                        "anchor_short_name": None,
                        "authoritative_subtree_path": None,
                        "suppressed_path": list(candidate.path),
                        "suppressed_value_present": False,
                        "suppressed_value": "",
                        "reason": (
                            "aggregate_occurrence_replaced_by_frozen_named_"
                            "instance_identities"
                        ),
                        "aggregate_count": candidate.min_occurs,
                        "declared_names": sorted(declared_names),
                    }
                )
                continue
        target_index = len(candidate.path) - 1
        instance_keys: set[tuple[tuple[int, str], ...]] = set()
        parent_keys: set[tuple[tuple[int, str], ...]] = set()
        scalar_instance_keys: set[tuple[tuple[int, str], ...]] = set()
        ancestor_scoped_instance_keys: set[tuple[tuple[int, str], ...]] = set()
        descendant_named_instance_keys: set[tuple[tuple[int, str], ...]] = set()
        for obligation in applied:
            obligation_path = tuple(obligation.get("path") or [])
            obligation_anchors = tuple(
                (
                    int(anchor.get("path_index", -1)),
                    str(anchor.get("short_name") or ""),
                )
                for anchor in (obligation.get("anchors") or [])
                if isinstance(anchor, dict)
            )
            if obligation_path[: len(candidate.path)] != candidate.path:
                continue
            if any(index > target_index for index, _name in obligation_anchors):
                descendant_named_instance_keys.add(obligation_anchors)
            if not any(index >= target_index for index, _name in obligation_anchors):
                # The selected element can be an anonymous, one-per-named-parent
                # child (for example NONQUEUED-RECEIVER-COM-SPEC below each
                # R-PORT).  Exact structured values below it prove the child in
                # every distinct parent even though the child has no SHORT-NAME
                # anchor of its own.
                if obligation_anchors:
                    ancestor_scoped_instance_keys.add(obligation_anchors)
                # A primitive leaf has no named instance of its own.  Distinct
                # exact values bound to distinct named repeated ancestors are
                # the complete instance set for that leaf (for example three
                # Timing Events, each with one PERIOD).  The model's aggregate
                # min/max belongs to the parent collection, not to PERIOD.
                if (
                    obligation_path == candidate.path
                    and candidate.path[-1] in {"#TEXT"}
                    and obligation_anchors
                ):
                    scalar_instance_keys.add(obligation_anchors)
                continue
            parent_key = tuple(
                (index, name)
                for index, name in obligation_anchors
                if index < target_index
            )
            if not parent_key:
                continue
            instance_keys.add(obligation_anchors)
            parent_keys.add(parent_key)
        nested_instances_proven = (
            len(parent_keys) >= 2
            and len(instance_keys) == candidate.min_occurs
        )
        # An anonymous, max-one wrapper is often reported once per named
        # parent (for example one receive-point container per runnable), while
        # the exact structured facts below it may contain a different total
        # number of named children.  Distinct parent contexts, rather than the
        # descendant child total, are therefore the relevant proof for the
        # model's aggregate wrapper count.
        parent_scoped_wrappers_proven = (
            len(parent_keys) >= 2
            and len(parent_keys) == candidate.min_occurs
            and bool(descendant_named_instance_keys)
        )
        scalar_instances_proven = (
            len(scalar_instance_keys) >= 2
            and len(scalar_instance_keys) == candidate.min_occurs
        )
        ancestor_scoped_instances_proven = (
            len(ancestor_scoped_instance_keys) >= 2
            and len(ancestor_scoped_instance_keys) == candidate.min_occurs
        )
        per_parent_singleton_proven = (
            candidate.min_occurs == 1
            and bool(ancestor_scoped_instance_keys)
        )
        descendant_named_children_proven = (
            len(descendant_named_instance_keys) >= 2
            and len(descendant_named_instance_keys) == candidate.min_occurs
        )
        if (
            nested_instances_proven
            or parent_scoped_wrappers_proven
            or scalar_instances_proven
            or ancestor_scoped_instances_proven
            or per_parent_singleton_proven
            or descendant_named_children_proven
        ):
            suppressed_phase1_selections.append(
                {
                    "obligation_index": None,
                    "component": component_name,
                    "anchor_short_name": None,
                    "authoritative_subtree_path": None,
                    "suppressed_path": list(candidate.path),
                    "suppressed_value_present": False,
                    "suppressed_value": "",
                    "reason": (
                        "aggregate_occurrence_replaced_by_instance_bound_"
                        "structured_obligations"
                    ),
                    "aggregate_count": candidate.min_occurs,
                    "distinct_parent_count": len(parent_keys),
                    "distinct_instance_count": (
                        len(instance_keys)
                        if nested_instances_proven
                        else (
                            len(parent_keys)
                            if parent_scoped_wrappers_proven
                            else (
                                len(scalar_instance_keys)
                                if scalar_instances_proven
                                else (
                                    len(descendant_named_instance_keys)
                                    if descendant_named_children_proven
                                    else len(ancestor_scoped_instance_keys)
                                )
                            )
                        )
                    ),
                    "instance_evidence": (
                        "nested_named_children"
                        if nested_instances_proven
                        else (
                            "one_wrapper_per_distinct_named_parent"
                            if parent_scoped_wrappers_proven
                            else (
                                "distinct_named_ancestors_for_scalar_leaf"
                                if scalar_instances_proven
                                else (
                                    "named_children_below_anonymous_wrapper"
                                    if descendant_named_children_proven
                                    else "one_anonymous_child_per_named_parent"
                                )
                            )
                        )
                    ),
                }
            )
            continue
        retained_raw.append(raw_selection)
    raw_selections[:] = retained_raw

    contract_by_id: dict[str, dict[str, Any]] = {}
    for position, raw_contract in enumerate(requirement_contracts):
        if not isinstance(raw_contract, dict):
            raise ElementSelectionError(
                f"generation_requirement_contracts[{position}] must be an object"
            )
        target_component = str(raw_contract.get("component") or "").strip()
        if target_component != component_name:
            continue
        requirement_id = str(raw_contract.get("requirement_id") or "").strip()
        requirement = str(raw_contract.get("requirement") or "").strip()
        expected_count = raw_contract.get("expected_obligation_count")
        if (
            not requirement_id
            or not requirement
            or isinstance(expected_count, bool)
            or not isinstance(expected_count, int)
            or expected_count < 1
        ):
            raise ElementSelectionError(
                f"generation_requirement_contracts[{position}] requires a non-empty "
                "requirement_id, component, requirement, and positive "
                "expected_obligation_count"
            )
        if requirement_id in contract_by_id:
            raise ElementSelectionError(
                f"duplicate generation requirement contract {requirement_id!r} "
                f"for component {component_name!r}"
            )
        contract_by_id[requirement_id] = raw_contract

    obligation_counts: dict[str, int] = {}
    for position, raw in enumerate(obligations):
        if not isinstance(raw, dict) or str(raw.get("component") or "").strip() != component_name:
            continue
        requirement_id = str(raw.get("requirement_id") or "").strip()
        if not contract_by_id:
            continue
        if requirement_id not in contract_by_id:
            raise ElementSelectionError(
                f"generation_value_obligations[{position}].requirement_id "
                f"{requirement_id!r} has no contract for component {component_name!r}"
            )
        obligation_counts[requirement_id] = obligation_counts.get(requirement_id, 0) + 1

    applied_counts: dict[str, int] = {}
    for item in applied:
        requirement_id = str(item.get("requirement_id") or "").strip()
        if requirement_id:
            applied_counts[requirement_id] = applied_counts.get(requirement_id, 0) + 1

    resolved_requirement_ids: set[str] = set()
    contract_audit: list[dict[str, Any]] = []
    for requirement_id, contract in contract_by_id.items():
        expected_count = int(contract["expected_obligation_count"])
        declared_count = obligation_counts.get(requirement_id, 0)
        applied_count = applied_counts.get(requirement_id, 0)
        if declared_count != expected_count:
            raise ElementSelectionError(
                f"generation requirement contract {requirement_id!r} expected "
                f"{expected_count} obligations but received {declared_count}"
            )
        if applied_count != expected_count:
            raise ElementSelectionError(
                f"generation requirement contract {requirement_id!r} compiled "
                f"{applied_count} of {expected_count} obligations"
            )
        resolved_requirement_ids.add(requirement_id)
        contract_audit.append(
            {
                "requirement_id": requirement_id,
                "requirement": str(contract["requirement"]),
                "expected_obligation_count": expected_count,
                "applied_obligation_count": applied_count,
                "decision": "PASS",
            }
        )

    resolved_unsupported: list[dict[str, Any]] = []
    retained_unsupported: list[object] = []
    raw_unsupported = element_design.get("unsupported")
    if raw_unsupported is None and not contract_by_id:
        raw_unsupported = []
    if not isinstance(raw_unsupported, list):
        raise ElementSelectionError("component element_design.unsupported must be an array")
    for unsupported_position, item in enumerate(raw_unsupported):
        if not isinstance(item, dict):
            retained_unsupported.append(item)
            continue
        requirement_id = str(item.get("requirement_id") or "").strip()
        if requirement_id and requirement_id in resolved_requirement_ids:
            resolved_unsupported.append(
                {
                    "unsupported_index": unsupported_position,
                    "requirement_id": requirement_id,
                    "resolution": "all_contract_obligations_compiled",
                }
            )
            continue
        retained_unsupported.append(item)
    element_design["unsupported"] = retained_unsupported

    parse_element_selections(element_design)
    return result, {
        "decision": "PASS",
        "applied_count": len(applied),
        "suppressed_phase1_selection_count": len(suppressed_phase1_selections),
        "suppressed_phase1_selections": suppressed_phase1_selections,
        "multi_anchor_expansion_count": len(multi_anchor_expansions),
        "multi_anchor_expansions": multi_anchor_expansions,
        "structured_anchor_index_repair_count": len(
            structured_anchor_index_repairs
        ),
        "structured_anchor_index_repairs": structured_anchor_index_repairs,
        "structured_anchor_chain_repair_count": len(
            structured_anchor_chain_repairs
        ),
        "structured_anchor_chain_repairs": structured_anchor_chain_repairs,
        "absent_value_repair_count": len(absent_value_repairs),
        "absent_value_repairs": [
            {
                "selection_index": selection_index,
                **repair,
            }
            for selection_index, repairs in sorted(absent_value_repairs.items())
            for repair in repairs
        ],
        "structured_value_anchor_binding_count": len(
            structured_value_anchor_bindings
        ),
        "structured_value_anchor_bindings": structured_value_anchor_bindings,
        "derived_anchor_identity_count": len(derived_anchor_identities),
        "derived_anchor_identities": derived_anchor_identities,
        "ignored_other_component_indexes": ignored_other_components,
        "requirement_contract_count": len(contract_audit),
        "requirement_contracts": contract_audit,
        "resolved_unsupported_count": len(resolved_unsupported),
        "resolved_unsupported": resolved_unsupported,
        "applied": applied,
    }


def augment_required_existence_selections(
    component_plan: object,
    validation_plan: object,
    *,
    xsd_path_index: object,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Compile applicable pinned V2 ``exists`` rules into Phase 2 selections.

    The validation plan is already hash-checked by the V2 service.  Only
    reviewed, fully implemented, unconditional MUST rules in the
    ``required_existence`` family are eligible.  A rule becomes applicable
    only when a required Phase 1 selection proves the selector/ancestor
    antecedent exists.  Every derived path is then checked against the pinned
    physical XSD before it can influence Neo4j schema assembly.
    """
    if not isinstance(component_plan, dict):
        raise ElementSelectionError("component plan must be an object")
    if not isinstance(validation_plan, dict):
        raise ElementSelectionError("V2 validation plan must be an object")
    rules = validation_plan.get("rules") or []
    if not isinstance(rules, list):
        raise ElementSelectionError("V2 validation plan rules must be an array")
    result = deepcopy(component_plan)
    component_type = _tag(result.get("type"))
    if not component_type:
        raise ElementSelectionError("component type is required for V2 obligation closure")
    element_design = result.get("element_design")
    if not isinstance(element_design, dict):
        raise ElementSelectionError("component element_design must be an object")
    raw_selections = element_design.get("selections")
    if not isinstance(raw_selections, list):
        raise ElementSelectionError("component element_design.selections must be an array")
    selections = parse_element_selections(element_design)

    existing: dict[
        tuple[tuple[str, ...], tuple[tuple[int, str], ...]], tuple[int, dict[str, Any]]
    ] = {}
    for position, raw in enumerate(raw_selections):
        selection = ElementSelection.from_mapping(raw, position=position)
        anchor_key = tuple(
            (anchor.path_index, anchor.short_name) for anchor in selection.anchors
        )
        existing[(selection.path, anchor_key)] = (position, raw)

    derived: list[dict[str, Any]] = []
    promoted: list[dict[str, Any]] = []
    selected_constraint_ids: set[str] = set()
    candidate_keys: set[
        tuple[str, tuple[str, ...], tuple[tuple[int, str], ...], str]
    ] = set()

    for rule in rules:
        if not isinstance(rule, dict):
            continue
        formal = rule.get("formal_spec") or {}
        implementation = rule.get("implementation") or {}
        activation = rule.get("activation") or {}
        if (
            str(rule.get("policy") or "").lower() != "must"
            or str(implementation.get("status") or "").lower() != "implemented"
            or str(formal.get("language") or "") != "autosar-constraint-ir/1.0"
            or str(formal.get("status") or "").lower() != "reviewed"
            or str(formal.get("coverage") or "").lower() != "full"
            or str(formal.get("rule_family") or "").lower() != "required_existence"
            or bool(rule.get("dependencies"))
            or bool(activation)
        ):
            continue
        selector = rule.get("selector") or {}
        if str(selector.get("mode") or "any").lower() != "any":
            continue
        selector_tags = {
            _tag(item) for item in (selector.get("tags") or []) if _tag(item)
        }
        if not selector_tags:
            continue
        checks = formal.get("checks") or []
        if not isinstance(checks, list):
            raise ElementSelectionError(
                f"V2 rule {rule.get('rule_id') or '<unknown>'} checks must be an array"
            )
        for check in checks:
            if not isinstance(check, dict) or str(check.get("op") or "") != "exists":
                continue
            when = check.get("when") or {}
            if not isinstance(when, dict) or set(when) - {"ancestor_tags"}:
                continue
            ancestor_tags = {
                _tag(item) for item in (when.get("ancestor_tags") or []) if _tag(item)
            }
            relative_path = tuple(
                _tag(item)
                for item in str(check.get("path") or "").split("/")
                if _tag(item)
            )
            if not relative_path or any(
                item == "#TEXT" or item.startswith("@") for item in relative_path
            ):
                continue
            for selection in selections:
                if selection.min_occurs < 1:
                    continue
                for selector_index, segment in enumerate(selection.path):
                    if segment not in selector_tags:
                        continue
                    prefix = selection.path[: selector_index + 1]
                    if not ancestor_tags.issubset(set(prefix[:-1])):
                        continue
                    anchors = tuple(
                        (anchor.path_index, anchor.short_name)
                        for anchor in selection.anchors
                        if anchor.path_index <= selector_index
                    )
                    if not anchors and any(
                        peer.path[: selector_index + 1] == prefix
                        and any(
                            anchor.path_index <= selector_index
                            for anchor in peer.anchors
                        )
                        for peer in selections
                    ):
                        # A generic selector row and concrete named-instance
                        # rows may coexist in Phase 1.  Deriving one global
                        # existence obligation in addition to the concrete
                        # instance obligations would mis-state a per-instance
                        # XSD cardinality as a document-global cardinality.
                        continue
                    path = prefix + relative_path
                    constraint_id = str(rule.get("constraint_id") or "").strip()
                    candidate_key = (constraint_id, path, anchors, str(check.get("message") or ""))
                    if candidate_key in candidate_keys:
                        continue
                    candidate_keys.add(candidate_key)
                    try:
                        resolution = xsd_path_index.resolve_path(component_type, path)
                        _minimum, maximum = xsd_path_index.element_occurrence_bounds(
                            component_type, resolution.canonical_path
                        )
                    except Exception as error:
                        raise ElementSelectionError(
                            f"V2 required-existence path is absent from the pinned XSD: "
                            f"{constraint_id or '<unknown>'} {'/'.join(path)}: {error}"
                        ) from error
                    canonical_path = tuple(resolution.canonical_path)
                    existing_key = (canonical_path, anchors)
                    existing_entry = existing.get(existing_key)
                    if existing_entry is not None:
                        position, raw = existing_entry
                        if int(raw.get("min_occurs") or 0) < 1:
                            raw["min_occurs"] = 1
                            promoted.append(
                                {
                                    "constraint_id": constraint_id,
                                    "selection_index": position,
                                    "path": list(canonical_path),
                                }
                            )
                        selected_constraint_ids.add(constraint_id)
                        continue
                    maximum_value = maximum if maximum is not None else 2_147_483_647
                    raw = {
                        "path": list(canonical_path),
                        "min_occurs": 1,
                        "max_occurs": max(1, int(maximum_value)),
                        "value_present": False,
                        "value": "",
                        "anchors": [
                            {"path_index": index, "short_name": short_name}
                            for index, short_name in anchors
                        ],
                        "notes": (
                            "System-derived from pinned V2 required-existence rule "
                            f"{rule.get('rule_id') or constraint_id}."
                        ),
                    }
                    raw_selections.append(raw)
                    existing[existing_key] = (len(raw_selections) - 1, raw)
                    selected_constraint_ids.add(constraint_id)
                    derived.append(
                        {
                            "constraint_id": constraint_id,
                            "rule_id": str(rule.get("rule_id") or ""),
                            "source_sha256": str(rule.get("source_sha256") or ""),
                            "title": str(rule.get("title") or ""),
                            "path": list(canonical_path),
                            "anchors": list(raw["anchors"]),
                            "xsd_resolution": str(resolution.resolution),
                        }
                    )

    return result, {
        "decision": "PASS",
        "derived_selection_count": len(derived),
        "promoted_selection_count": len(promoted),
        "constraint_ids": sorted(item for item in selected_constraint_ids if item),
        "derived": derived,
        "promoted": promoted,
    }


def selection_design_index(element_design: object) -> dict[str, set[str]]:
    """Return parent-tag -> requested-child-tag pairs for Neo4j expansion."""
    index: dict[str, set[str]] = {}
    for selection in parse_element_selections(element_design):
        for parent, child in zip(selection.path, selection.path[1:]):
            # Attributes are projections, not metamodel child elements.
            # Keep #TEXT in the index: the XSD-driven schema builder uses it
            # to activate complex simple-content shapes when appropriate.
            if child.startswith("@"):
                continue
            index.setdefault(parent, set()).add(child)
    return index


def interface_design_index(
    interface_type: str, interface_plans: list[dict[str, Any]]
) -> dict[str, set[str]]:
    """Compile requested interface payloads into Neo4j expansion edges."""
    requested = [
        str(name).strip()
        for plan in interface_plans
        for name in (plan.get("data_elements") or [])
        if str(name).strip()
    ]
    if not requested:
        return {}
    mapping = {
        "SENDER-RECEIVER-INTERFACE": ("DATA-ELEMENTS", "VARIABLE-DATA-PROTOTYPE"),
    }
    edge = mapping.get(str(interface_type or "").strip().upper())
    if edge is None:
        raise ElementSelectionError(
            f"interface data_elements are unsupported for {interface_type or '<missing type>'}"
        )
    container, child = edge
    return {
        str(interface_type).strip().upper(): {container},
        container: {child},
    }


def project_element_design_for_schema(
    element_design: object, projection_map: object
) -> dict[str, Any]:
    """Translate canonical XML selections to a provider-facing schema projection.

    Projection rules are declared as provider ``source`` -> canonical XML
    ``target`` paths.  Phase 1 always speaks in canonical XML paths, so schema
    enforcement applies the inverse mapping.  Anchor indexes are translated
    with their selected named element; an anchor on a removed container fails
    closed.
    """
    if not isinstance(element_design, dict):
        return {}
    result = deepcopy(element_design)
    selections = parse_element_selections(element_design)
    if not selections:
        result["selections"] = []
        return result
    if not isinstance(projection_map, dict):
        raise ElementSelectionError("component projection map must be an object")
    if projection_map.get("schema_version") != "1.0":
        raise ElementSelectionError("unsupported component projection map schema_version")
    raw_rules = projection_map.get("rules") or []
    if not isinstance(raw_rules, list):
        raise ElementSelectionError("component projection rules must be an array")
    rules: list[tuple[tuple[str, ...], tuple[str, ...]]] = []
    removed_wrapper_prefixes: set[tuple[str, ...]] = set()
    for position, raw_rule in enumerate(raw_rules):
        if not isinstance(raw_rule, dict):
            raise ElementSelectionError(f"component projection rule {position} must be an object")
        source = tuple(_tag(item) for item in (raw_rule.get("source") or []))
        target = tuple(_tag(item) for item in (raw_rule.get("target") or []))
        if not source or not target or source == target:
            raise ElementSelectionError(f"component projection rule {position} has an empty path")
        cursor = 0
        retained_indexes: set[int] = set()
        for source_segment in source:
            while cursor < len(target) and target[cursor] != source_segment:
                cursor += 1
            if cursor >= len(target):
                raise ElementSelectionError(
                    "projection source is not an ordered subset of target: "
                    + "/".join(source)
                )
            retained_indexes.add(cursor)
            cursor += 1
        for target_index in set(range(len(target))) - retained_indexes:
            removed_wrapper_prefixes.add(target[: target_index + 1])
        rules.append((target, source))
    rules.sort(key=lambda item: len(item[0]), reverse=True)

    redundant_wrapper_indexes: set[int] = set()
    for position, selection in enumerate(selections):
        if (
            selection.path not in removed_wrapper_prefixes
            or selection.value_present
            or (selection.min_occurs, selection.max_occurs) != (1, 1)
        ):
            continue
        anchor_identity = {
            (anchor.path_index, anchor.short_name) for anchor in selection.anchors
        }
        for other_position, descendant in enumerate(selections):
            if position == other_position or len(descendant.path) <= len(selection.path):
                continue
            if descendant.path[: len(selection.path)] != selection.path:
                continue
            descendant_anchors = {
                (anchor.path_index, anchor.short_name) for anchor in descendant.anchors
            }
            if (
                descendant.min_occurs >= 1
                and anchor_identity.issubset(descendant_anchors)
            ):
                redundant_wrapper_indexes.add(position)
                break

    projected: list[dict[str, Any]] = []
    for selection_position, selection in enumerate(selections):
        if selection_position in redundant_wrapper_indexes:
            # The provider projection intentionally flattens this physical XSD
            # wrapper.  A required anchored descendant both activates the same
            # Neo4j edge and forces the renderer to materialize the wrapper;
            # the canonical selection remains in Phase 1 for parsed XML
            # obligation validation.
            continue
        # Each current segment retains the original canonical path indexes it
        # represents.  This makes anchor translation explicit and auditable.
        segments: list[tuple[str, tuple[int, ...]]] = [
            (segment, (index,)) for index, segment in enumerate(selection.path)
        ]
        while True:
            applied = False
            for target, source in rules:
                if tuple(segment for segment, _ in segments[: len(target)]) != target:
                    continue
                matched: list[tuple[str, tuple[int, ...]]] = []
                target_segments = segments[: len(target)]
                cursor = 0
                for source_segment in source:
                    while (
                        cursor < len(target_segments)
                        and target_segments[cursor][0] != source_segment
                    ):
                        cursor += 1
                    if cursor >= len(target_segments):
                        raise ElementSelectionError(
                            "projection source is not an ordered subset of target: "
                            + "/".join(source)
                        )
                    matched.append((source_segment, target_segments[cursor][1]))
                    cursor += 1
                segments = [*matched, *segments[len(target) :]]
                applied = True
                break
            if not applied:
                break

        origin_to_projected: dict[int, int] = {}
        for projected_index, (_segment, origins) in enumerate(segments):
            for origin in origins:
                origin_to_projected[origin] = projected_index
        anchors = []
        for anchor in selection.anchors:
            if anchor.path_index not in origin_to_projected:
                raise ElementSelectionError(
                    "selection anchor was removed by component projection at "
                    + "/".join(selection.path)
                )
            anchors.append(
                {
                    "path_index": origin_to_projected[anchor.path_index],
                    "short_name": anchor.short_name,
                }
            )
        projected.append(
            {
                "path": [segment for segment, _ in segments],
                "min_occurs": selection.min_occurs,
                "max_occurs": selection.max_occurs,
                "value_present": selection.value_present,
                "value": selection.value,
                "anchors": anchors,
                "notes": selection.notes,
            }
        )
    result["selections"] = projected
    return result


def project_declared_value_design(
    element_design: object,
    projection_map: object,
    value_obligation_audit: object,
) -> dict[str, Any]:
    """Project only structured-requirement values to provider schema paths.

    The augmentation audit is authoritative because a value may already have
    been selected by Phase 1 and therefore cannot be identified from notes.
    Every audit entry must bind back to one exact canonical selection.
    """
    if not isinstance(element_design, dict):
        raise ElementSelectionError("element_design must be an object")
    if not isinstance(value_obligation_audit, dict):
        raise ElementSelectionError("declared value obligation audit must be an object")
    applied = value_obligation_audit.get("applied") or []
    if not isinstance(applied, list):
        raise ElementSelectionError("declared value obligation audit applied must be an array")
    raw_selections = element_design.get("selections") or []
    if not isinstance(raw_selections, list):
        raise ElementSelectionError("element_design.selections must be an array")
    parsed = [
        (raw, ElementSelection.from_mapping(raw, position=position))
        for position, raw in enumerate(raw_selections)
    ]
    selected: list[dict[str, Any]] = []
    authoritative_subtrees: list[tuple[str, ...] | None] = []
    for position, obligation in enumerate(applied):
        if not isinstance(obligation, dict):
            raise ElementSelectionError(
                f"declared value obligation audit applied[{position}] must be an object"
            )
        path = tuple(_tag(item) for item in obligation.get("path") or [])
        value = str(obligation.get("value"))
        obligation_anchors = obligation.get("anchors")
        if obligation_anchors is not None:
            if not isinstance(obligation_anchors, list) or not obligation_anchors:
                raise ElementSelectionError(
                    "declared value obligation audit anchors must be a non-empty array"
                )
            anchor_key = tuple(
                (
                    int(anchor.get("path_index", -1)),
                    str(anchor.get("short_name") or "").strip(),
                )
                for anchor in obligation_anchors
                if isinstance(anchor, dict)
            )
            if len(anchor_key) != len(obligation_anchors):
                raise ElementSelectionError(
                    "declared value obligation audit contains an invalid anchor"
                )
        else:
            anchor_name = str(obligation.get("anchor_short_name") or "").strip()
            anchor_key = ()
        matches = [
            raw
            for raw, selection in parsed
            if selection.path == path
            and selection.value_present
            and selection.value == value
            and (
                tuple(
                    (anchor.path_index, anchor.short_name)
                    for anchor in selection.anchors
                )
                == anchor_key
                if obligation_anchors is not None
                else any(
                    anchor.short_name == anchor_name for anchor in selection.anchors
                )
            )
        ]
        if len(matches) != 1:
            reason = "missing" if not matches else "ambiguous"
            raise ElementSelectionError(
                f"declared value obligation audit is {reason} in canonical selections: "
                + "/".join(path)
            )
        selected.append(deepcopy(matches[0]))
        raw_subtree = obligation.get("authoritative_subtree_path")
        if raw_subtree is None:
            authoritative_subtrees.append(None)
        elif not isinstance(raw_subtree, list):
            raise ElementSelectionError(
                "declared value obligation authoritative_subtree_path must be an array"
            )
        else:
            subtree = tuple(_tag(item) for item in raw_subtree if _tag(item))
            if not subtree or path[: len(subtree)] != subtree:
                raise ElementSelectionError(
                    "declared value authoritative subtree is not a prefix of its value path"
                )
            authoritative_subtrees.append(subtree)
    projected = project_element_design_for_schema(
        {"selections": selected}, projection_map
    )
    if len(projected.get("selections") or []) != len(applied):
        raise ElementSelectionError("declared value projection changed obligation count")
    for position, subtree in enumerate(authoritative_subtrees):
        if subtree is None:
            continue
        source = deepcopy(selected[position])
        source["path"] = list(subtree)
        source["min_occurs"] = 1
        source["max_occurs"] = 1
        source["value_present"] = False
        source["value"] = ""
        source["anchors"] = [
            anchor
            for anchor in (source.get("anchors") or [])
            if int(anchor.get("path_index", -1)) < len(subtree)
        ]
        projected_subtree = project_element_design_for_schema(
            {"selections": [source]}, projection_map
        ).get("selections") or []
        if len(projected_subtree) != 1:
            raise ElementSelectionError(
                "declared value authoritative subtree projection is ambiguous"
            )
        projected["selections"][position]["authoritative_subtree_path"] = list(
            projected_subtree[0]["path"]
        )
    return projected


def _object_node(node: dict[str, Any]) -> dict[str, Any]:
    current = node
    while current.get("type") == "array" and isinstance(current.get("items"), dict):
        current = current["items"]
    return current


def _sole_repeated_child(node: dict[str, Any]) -> dict[str, Any] | None:
    """The repeated element a single-property wrapper stands for, if any.

    AUTOSAR wraps repeated particles in a container element that carries no
    occurrence of its own, so a count declared on the wrapper is a count of
    the element inside it.
    """
    if node.get("type") != "object":
        return None
    properties = node.get("properties")
    if not isinstance(properties, dict) or len(properties) != 1:
        return None
    (child,) = properties.values()
    if isinstance(child, dict) and child.get("type") == "array":
        return child
    return None


def _property(node: dict[str, Any], wanted: str) -> tuple[str, dict[str, Any]] | None:
    obj = _object_node(node)
    properties = obj.get("properties")
    if not isinstance(properties, dict):
        return None
    by_tag = {_tag(key): (key, child) for key, child in properties.items() if isinstance(child, dict)}
    return by_tag.get(_tag(wanted))


def _match_from(
    node: dict[str, Any], path: tuple[str, ...]
) -> list[tuple[list[tuple[dict[str, Any], str, dict[str, Any]]], dict[str, Any]]]:
    if not path:
        return []
    found = _property(node, path[0])
    if found is None:
        return []
    key, child = found
    parent = _object_node(node)
    trail = [(parent, key, child)]
    current = child
    for segment in path[1:]:
        nested = _property(current, segment)
        if nested is None:
            return []
        key, child = nested
        trail.append((_object_node(current), key, child))
        current = child
    return [(trail, current)]


def _search_matches(
    node: dict[str, Any], path: tuple[str, ...]
) -> list[tuple[list[tuple[dict[str, Any], str, dict[str, Any]]], dict[str, Any]]]:
    matches = _match_from(node, path)
    obj = _object_node(node)
    properties = obj.get("properties")
    if isinstance(properties, dict):
        for child in properties.values():
            if isinstance(child, dict):
                matches.extend(_search_matches(child, path))
    return matches


def subschema_at_path(schema: dict[str, Any], path: Iterable[Any]) -> dict[str, Any]:
    """Return the sub-schema governing one absolute payload path.

    Array occurrences must be entered through an integer index so a repair can
    never silently address "some" element of a repeated particle.  A path the
    schema does not describe raises rather than degrading to a permissive node.
    """
    if not isinstance(schema, dict):
        raise ElementSelectionError("schema must be an object")
    current = schema
    walked: list[str] = []
    for segment in path:
        walked.append(str(segment))
        if isinstance(segment, bool) or not isinstance(segment, (str, int)):
            raise ElementSelectionError(
                f"unsupported schema path segment at {'/'.join(walked)}"
            )
        if isinstance(segment, int):
            if current.get("type") != "array" or not isinstance(current.get("items"), dict):
                raise ElementSelectionError(
                    f"schema path enters a non-array at {'/'.join(walked)}"
                )
            current = current["items"]
            continue
        if current.get("type") == "array":
            raise ElementSelectionError(
                f"schema path must index the repeated particle at {'/'.join(walked)}"
            )
        found = _property(current, segment)
        if found is None:
            raise ElementSelectionError(
                f"schema has no property for {'/'.join(walked)}"
            )
        current = found[1]
    return current


def _coerce_const(value: str, schema: dict[str, Any]) -> Any:
    target = _object_node(schema) if schema.get("type") == "array" else schema
    schema_type = target.get("type")
    if schema_type == "boolean":
        lowered = value.strip().lower()
        if lowered not in {"true", "false"}:
            raise ElementSelectionError(f"cannot coerce {value!r} to boolean")
        return lowered == "true"
    if schema_type == "integer":
        try:
            return int(value)
        except ValueError as exc:
            raise ElementSelectionError(f"cannot coerce {value!r} to integer") from exc
    if schema_type == "number":
        try:
            return float(value)
        except ValueError as exc:
            raise ElementSelectionError(f"cannot coerce {value!r} to number") from exc
    return value


def _merge_const(node: dict[str, Any], value: Any, path: Iterable[str]) -> None:
    existing = node.get("const")
    if "const" in node and existing != value:
        raise ElementSelectionError(
            f"conflicting constant at {'/'.join(path)}: {existing!r} versus {value!r}"
        )
    enum_values = node.get("enum")
    if isinstance(enum_values, list) and value not in enum_values:
        raise ElementSelectionError(
            f"constant {value!r} is outside enum at {'/'.join(path)}"
        )
    validation_errors = list(Draft202012Validator(node).iter_errors(value))
    if validation_errors:
        raise ElementSelectionError(
            f"constant {value!r} violates provider schema at {'/'.join(path)}: "
            + validation_errors[0].message
        )
    node["const"] = value


def remove_deterministic_value_properties(
    schema: dict[str, Any], element_design: object
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Remove exact requirement-owned subtrees from the model-facing schema.

    The original schema remains authoritative after materialization. Starting
    at the exact value leaf, the cut moves upward only through single-property
    wrapper objects and stops before a model-owned sibling. This removes the
    physical value wrapper without removing communication-spec siblings.
    """
    result = deepcopy(schema)
    removed: list[dict[str, Any]] = []
    removed_paths: set[tuple[str, ...]] = set()
    removed_prefixes: dict[tuple[str, ...], tuple[str, ...]] = {}
    parse_element_selections(element_design, minimum_path_segments=1)
    raw_selections = (
        element_design.get("selections") or []
        if isinstance(element_design, dict)
        else []
    )
    for position, raw_selection in enumerate(raw_selections):
        selection = ElementSelection.from_mapping(
            raw_selection, position=position, minimum_path_segments=1
        )
        if not selection.value_present or not selection.anchors:
            raise ElementSelectionError(
                "deterministic provider values must be exact and anchor-bound"
            )
        if selection.path not in removed_paths:
            matches = _search_matches(result, selection.path)
            if not matches and selection.path[-1] == "#TEXT":
                matches = _search_matches(result, selection.path[:-1])
            if len(matches) != 1:
                reason = "missing" if not matches else f"ambiguous ({len(matches)} matches)"
                raise ElementSelectionError(
                    f"deterministic provider value path is {reason}: "
                    + "/".join(selection.path)
                )
            trail, _target = matches[0]
            deepest_anchor = max(anchor.path_index for anchor in selection.anchors)
            raw_subtree = raw_selection.get("authoritative_subtree_path")
            if raw_subtree is not None:
                if not isinstance(raw_subtree, list):
                    raise ElementSelectionError(
                        "deterministic authoritative_subtree_path must be an array"
                    )
                subtree = tuple(_tag(item) for item in raw_subtree if _tag(item))
                if (
                    len(subtree) <= deepest_anchor
                    or selection.path[: len(subtree)] != subtree
                    or len(subtree) > len(trail)
                ):
                    raise ElementSelectionError(
                        "deterministic authoritative subtree is outside the anchored value path"
                    )
                cut_index = len(subtree) - 1
            else:
                cut_index = len(trail) - 1
                while cut_index > deepest_anchor + 1:
                    parent, key, _child = trail[cut_index]
                    properties = parent.get("properties")
                    if not isinstance(properties, dict) or set(properties) != {key}:
                        break
                    cut_index -= 1
            parent, key, _child = trail[cut_index]
            properties = parent.get("properties")
            if not isinstance(properties, dict) or key not in properties:
                raise ElementSelectionError(
                    "deterministic provider value leaf has no removable property: "
                    + "/".join(selection.path)
                )
            properties.pop(key)
            required = parent.get("required")
            if isinstance(required, list):
                parent["required"] = [item for item in required if item != key]
            removed_paths.add(selection.path)
            removed_prefixes[selection.path] = selection.path[: cut_index + 1]
        removed.append(
            {
                "path": list(selection.path),
                "provider_removed_prefix": list(removed_prefixes[selection.path]),
                "authoritative_subtree": bool(
                    raw_selection.get("authoritative_subtree_path")
                ),
                "value": selection.value,
                "anchors": [
                    {
                        "path_index": anchor.path_index,
                        "short_name": anchor.short_name,
                    }
                    for anchor in selection.anchors
                ],
            }
        )
    Draft202012Validator.check_schema(result)
    return result, {
        "decision": "PASS",
        "strategy": "remove_exact_wrapper_subtree_then_materialize_from_requirement_ir",
        "unique_removed_path_count": len(removed_paths),
        "obligation_count": len(removed),
        "obligations": removed,
    }


def build_provider_instance_skeleton(
    full_schema: dict[str, Any], element_design: object
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Construct the named instances the requirement owns, before the model runs.

    Phase 2 used to learn the component's whole structure from the provider and
    was rejected outright when the model returned one RUNNABLE-ENTITY where the
    requirement declared two, or left out an ACCESSED-VARIABLE.  Those counts
    and identities are not the model's to decide, so they are built here and
    the provider is left with the values it is actually being asked for.

    Only anchored instances are created.  An unanchored repeated element has no
    declared identity, so inventing one would be a guess rather than a
    construction, and a single occurrence is created for it exactly where
    materialization would otherwise demand one.
    """
    parsed_selections = parse_element_selections(
        element_design, minimum_path_segments=1
    )
    declared_names_by_path: dict[tuple[str, ...], set[str]] = {}
    for parsed in parsed_selections:
        for anchor in parsed.anchors:
            declared_names_by_path.setdefault(
                parsed.path[: anchor.path_index + 1], set()
            ).add(anchor.short_name)

    skeleton: dict[str, Any] = {}
    instances: list[dict[str, Any]] = []
    cardinality_paths: list[list[str]] = []
    inferred_parent_instances: list[dict[str, Any]] = []
    for selection in parsed_selections:
        if not selection.anchors:
            continue
        matches = _search_matches(full_schema, selection.path)
        if not matches and selection.path[-1] == "#TEXT":
            matches = _search_matches(full_schema, selection.path[:-1])
        if len(matches) != 1:
            # Ambiguity is resolved by the existing full-schema gates, not here.
            continue
        trail, _target = matches[0]
        anchors = {anchor.path_index: anchor.short_name for anchor in selection.anchors}
        deepest_anchor = max(anchors)
        current: Any = skeleton
        walked: list[str] = []
        for path_index, (_parent_schema, key, child_schema) in enumerate(trail):
            if path_index > deepest_anchor:
                break
            walked.append(key)
            schema_type = child_schema.get("type")
            if schema_type == "array":
                entries = current.setdefault(key, [])
                if not isinstance(entries, list):
                    raise ElementSelectionError(
                        f"skeleton property {key!r} is not an array"
                    )
                anchor_name = anchors.get(path_index)
                if anchor_name is None:
                    item_schema = child_schema.get("items")
                    item_properties = (
                        item_schema.get("properties")
                        if isinstance(item_schema, dict)
                        else None
                    )
                    named_array = (
                        isinstance(item_properties, dict)
                        and "SHORT-NAME" in item_properties
                    )
                    if not named_array:
                        if not entries:
                            entries.append({})
                        current = entries[0]
                        continue

                    current_path = tuple(walked)
                    inferred_names: set[str] = set()
                    direct_names = declared_names_by_path.get(current_path, set())
                    if len(direct_names) == 1:
                        inferred_names.update(direct_names)
                    else:
                        deeper_identities = [
                            (
                                selection.path[: anchor_index + 1],
                                anchor_name_value,
                            )
                            for anchor_index, anchor_name_value in anchors.items()
                            if anchor_index > path_index
                        ]
                        for peer in parsed_selections:
                            peer_anchors = {
                                anchor.path_index: anchor.short_name
                                for anchor in peer.anchors
                            }
                            if not all(
                                peer.path[: len(identity_path)] == identity_path
                                and peer_anchors.get(len(identity_path) - 1)
                                == identity_name
                                for identity_path, identity_name in deeper_identities
                            ):
                                continue
                            peer_parent = peer_anchors.get(path_index)
                            if peer_parent:
                                inferred_names.add(peer_parent)
                    if len(inferred_names) != 1:
                        raise ElementSelectionError(
                            "named provider skeleton array has no unique frozen "
                            "parent identity at " + "/".join(walked)
                        )
                    anchor_name = next(iter(inferred_names))
                    inferred_parent_instances.append(
                        {
                            "path": list(walked),
                            "short_name": anchor_name,
                            "selection_path": list(selection.path),
                        }
                    )
                cardinality_paths.append(list(walked))
                existing = [
                    item
                    for item in entries
                    if isinstance(item, dict)
                    and str(item.get("SHORT-NAME") or "") == anchor_name
                ]
                if existing:
                    current = existing[0]
                    continue
                created = {"SHORT-NAME": anchor_name}
                entries.append(created)
                instances.append(
                    {"path": list(walked), "short_name": anchor_name}
                )
                current = created
                continue
            if schema_type == "object":
                current = current.setdefault(key, {})
                if not isinstance(current, dict):
                    raise ElementSelectionError(
                        f"skeleton property {key!r} is not an object"
                    )
                continue
            break
    unique_cardinality = sorted({tuple(item) for item in cardinality_paths})
    return skeleton, {
        "decision": "PASS" if instances else "NOT_APPLICABLE",
        "instance_count": len(instances),
        "instances": instances,
        "inferred_parent_instance_count": len(inferred_parent_instances),
        "inferred_parent_instances": inferred_parent_instances,
        "requirement_owned_array_paths": [list(item) for item in unique_cardinality],
    }


def build_interface_instance_skeleton(
    interface_plans: object,
    interface_schema: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build the complete Phase-1-owned interface identity skeleton.

    ``interface_plan`` owns every interface name and every declared data
    element name.  The physical interface schema supplies the canonical root
    type spelling; matching ignores punctuation only to accommodate the
    Round-1 aliases already accepted by the schema generator.  No identity is
    inferred from a provider payload.
    """

    if not isinstance(interface_plans, list):
        raise ElementSelectionError("interface_plan must be an array")
    properties = interface_schema.get("properties")
    if not isinstance(properties, dict):
        raise ElementSelectionError("interface schema properties are required")

    def identity_key(value: object) -> str:
        return "".join(character for character in str(value).upper() if character.isalnum())

    schema_types: dict[str, list[str]] = {}
    for schema_type in properties:
        schema_types.setdefault(identity_key(schema_type), []).append(str(schema_type))

    skeleton: dict[str, Any] = {}
    seen_interface_names: set[str] = set()
    interface_records: list[dict[str, Any]] = []
    data_element_records: list[dict[str, Any]] = []
    for position, raw_plan in enumerate(interface_plans):
        if not isinstance(raw_plan, dict):
            raise ElementSelectionError(
                f"interface_plan[{position}] must be an object"
            )
        raw_type = str(raw_plan.get("type") or "").strip()
        name = str(raw_plan.get("name") or "").strip()
        if not raw_type or not name:
            raise ElementSelectionError(
                f"interface_plan[{position}] requires non-empty type and name"
            )
        matches = schema_types.get(identity_key(raw_type), [])
        if len(matches) != 1:
            raise ElementSelectionError(
                f"interface_plan[{position}] type {raw_type!r} does not resolve "
                "to exactly one interface schema root"
            )
        schema_type = matches[0]
        if name in seen_interface_names:
            raise ElementSelectionError(
                f"duplicate requirement-owned interface identity: {name!r}"
            )
        seen_interface_names.add(name)

        raw_data_elements = raw_plan.get("data_elements") or []
        if not isinstance(raw_data_elements, list):
            raise ElementSelectionError(
                f"interface_plan[{position}].data_elements must be an array"
            )
        data_names: list[str] = []
        seen_data_names: set[str] = set()
        for data_position, raw_name in enumerate(raw_data_elements):
            data_name = str(raw_name or "").strip()
            if not data_name:
                raise ElementSelectionError(
                    f"interface_plan[{position}].data_elements[{data_position}] "
                    "must be non-empty"
                )
            if data_name in seen_data_names:
                raise ElementSelectionError(
                    f"duplicate requirement-owned data element identity in "
                    f"interface {name!r}: {data_name!r}"
                )
            seen_data_names.add(data_name)
            data_names.append(data_name)

        interface_item: dict[str, Any] = {"SHORT-NAME": name}
        if data_names:
            interface_item["DATA-ELEMENTS"] = {
                "VARIABLE-DATA-PROTOTYPE": [
                    {"SHORT-NAME": data_name} for data_name in data_names
                ]
            }
        skeleton.setdefault(schema_type, []).append(interface_item)
        interface_records.append(
            {"schema_type": schema_type, "short_name": name}
        )
        data_element_records.extend(
            {
                "interface_short_name": name,
                "short_name": data_name,
            }
            for data_name in data_names
        )

    return skeleton, {
        "decision": "PASS",
        "strategy": "phase1_interface_and_data_element_identity_skeleton",
        "interface_count": len(interface_records),
        "data_element_count": len(data_element_records),
        "interfaces": interface_records,
        "data_elements": data_element_records,
    }


def constrain_interface_data_type_schema(
    interface_schema: dict[str, Any],
    interface_plans: object,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Admit exact source-owned data-element type references into an interface schema.

    The XSD/KG interface schema is shared by all instances of one interface
    type.  It can therefore constrain the allowed type-reference vocabulary but
    cannot bind one value to one named data element until identity projection.
    This first step adds (or narrows) the physical ``TYPE-TREF`` shape and fails
    closed when the selected interface shape is ambiguous.
    """

    if not isinstance(interface_plans, list):
        raise ElementSelectionError("interface_plan must be an array")
    bindings = [
        (str(name), str(spec.get("value") or ""), str(spec.get("dest") or ""))
        for plan in interface_plans
        if isinstance(plan, dict)
        for name, spec in (plan.get("data_element_type_refs") or {}).items()
        if isinstance(spec, dict)
    ]
    if not bindings:
        return deepcopy(interface_schema), {
            "decision": "NOT_APPLICABLE",
            "binding_count": 0,
        }
    if any(not name or not value or not dest for name, value, dest in bindings):
        raise ElementSelectionError("interface data-type binding fields must be non-empty")
    names = [name for name, _value, _dest in bindings]
    if len(names) != len(set(names)):
        raise ElementSelectionError("duplicate source-owned interface data-element type binding")

    result = deepcopy(interface_schema)
    data_nodes: list[dict[str, Any]] = []

    def collect(node: Any) -> None:
        if not isinstance(node, dict):
            return
        properties = node.get("properties")
        if isinstance(properties, dict):
            for key, child in properties.items():
                if _tag(key) == "VARIABLE-DATA-PROTOTYPE" and isinstance(child, dict):
                    data_nodes.append(child)
                collect(child)
        items = node.get("items")
        if isinstance(items, dict):
            collect(items)

    collect(result)
    if len(data_nodes) != 1:
        raise ElementSelectionError(
            "source-owned interface TYPE-TREF bindings require exactly one "
            f"VARIABLE-DATA-PROTOTYPE schema, found {len(data_nodes)}"
        )
    data_node = data_nodes[0]
    item_schema = data_node.get("items") if data_node.get("type") == "array" else data_node
    if not isinstance(item_schema, dict) or item_schema.get("type") != "object":
        raise ElementSelectionError("VARIABLE-DATA-PROTOTYPE item schema must be an object")
    properties = item_schema.setdefault("properties", {})
    if not isinstance(properties, dict):
        raise ElementSelectionError("VARIABLE-DATA-PROTOTYPE properties must be an object")
    values = sorted({value for _name, value, _dest in bindings})
    destinations = sorted({dest for _name, _value, dest in bindings})
    type_schema = properties.get("TYPE-TREF")
    if type_schema is None:
        type_schema = {
            "type": "object",
            "properties": {
                "@DEST": {"type": "string", "enum": destinations},
                "#text": {"type": "string", "enum": values},
            },
            "required": ["@DEST", "#text"],
            "additionalProperties": False,
        }
        properties["TYPE-TREF"] = type_schema
    elif isinstance(type_schema, dict) and type_schema.get("type") == "string":
        type_schema = {
            "type": "object",
            "properties": {
                "@DEST": {"type": "string", "enum": destinations},
                "#text": {"type": "string", "enum": values},
            },
            "required": ["@DEST", "#text"],
            "additionalProperties": False,
        }
        properties["TYPE-TREF"] = type_schema
    elif isinstance(type_schema, dict):
        type_properties = type_schema.get("properties") or {}
        if not isinstance(type_properties, dict):
            raise ElementSelectionError("TYPE-TREF properties must be an object")
        text_key = next(
            (key for key in type_properties if _tag(key) == "#TEXT"), None
        )
        dest_key = next(
            (key for key in type_properties if _tag(key) == "@DEST"), None
        )
        if text_key is None or dest_key is None:
            raise ElementSelectionError("TYPE-TREF schema lacks #text or @DEST")
        type_properties[text_key]["enum"] = values
        type_properties[dest_key]["enum"] = destinations
        required = list(type_schema.get("required") or [])
        for key in (dest_key, text_key):
            if key not in required:
                required.append(key)
        type_schema["required"] = required
    else:
        raise ElementSelectionError("TYPE-TREF schema must be an object")
    required = list(item_schema.get("required") or [])
    if "TYPE-TREF" not in required:
        required.append("TYPE-TREF")
    item_schema["required"] = required
    Draft202012Validator.check_schema(result)
    return result, {
        "decision": "PASS",
        "binding_count": len(bindings),
        "allowed_type_refs": values,
        "allowed_destinations": destinations,
    }


def bind_projected_interface_data_types(
    provider_schema: dict[str, Any],
    interface_plans: object,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Bind each admitted data-element slot to its exact TYPE-TREF constants."""

    if not isinstance(interface_plans, list):
        raise ElementSelectionError("interface_plan must be an array")
    expected: dict[str, tuple[str, str]] = {}
    for plan in interface_plans:
        if not isinstance(plan, dict):
            continue
        for name, spec in (plan.get("data_element_type_refs") or {}).items():
            if not isinstance(spec, dict):
                raise ElementSelectionError("interface data-type binding must be an object")
            key = str(name)
            value = str(spec.get("value") or "")
            dest = str(spec.get("dest") or "")
            if not key or not value or not dest or key in expected:
                raise ElementSelectionError(
                    "interface data-type binding identity/value/destination is invalid"
                )
            expected[key] = (value, dest)
    if not expected:
        return deepcopy(provider_schema), {
            "decision": "NOT_APPLICABLE",
            "binding_count": 0,
        }

    result = deepcopy(provider_schema)
    bound: list[str] = []

    def visit(node: Any) -> None:
        if not isinstance(node, dict):
            return
        properties = node.get("properties")
        if isinstance(properties, dict):
            for key, child in properties.items():
                if key in expected and isinstance(child, dict):
                    matches: list[dict[str, Any]] = []

                    def find_type(candidate: Any) -> None:
                        if not isinstance(candidate, dict):
                            return
                        candidate_properties = candidate.get("properties")
                        if isinstance(candidate_properties, dict):
                            for candidate_key, candidate_child in candidate_properties.items():
                                if _tag(candidate_key) == "TYPE-TREF" and isinstance(
                                    candidate_child, dict
                                ):
                                    matches.append(candidate_child)
                                find_type(candidate_child)
                        candidate_items = candidate.get("items")
                        if isinstance(candidate_items, dict):
                            find_type(candidate_items)

                    find_type(child)
                    if len(matches) != 1:
                        raise ElementSelectionError(
                            f"admitted data element {key!r} resolves to {len(matches)} TYPE-TREF schemas"
                        )
                    type_properties = matches[0].get("properties") or {}
                    text_key = next(
                        (item for item in type_properties if _tag(item) == "#TEXT"), None
                    )
                    dest_key = next(
                        (item for item in type_properties if _tag(item) == "@DEST"), None
                    )
                    if text_key is None or dest_key is None:
                        raise ElementSelectionError(
                            f"admitted data element {key!r} TYPE-TREF lacks #text or @DEST"
                        )
                    value, dest = expected[key]
                    type_properties[text_key].pop("enum", None)
                    type_properties[text_key]["const"] = value
                    type_properties[dest_key].pop("enum", None)
                    type_properties[dest_key]["const"] = dest
                    bound.append(key)
                visit(child)
        items = node.get("items")
        if isinstance(items, dict):
            visit(items)

    visit(result)
    counts = {name: bound.count(name) for name in expected}
    if any(count != 1 for count in counts.values()):
        raise ElementSelectionError(
            "source-owned interface TYPE-TREF bindings did not resolve exactly once: "
            + repr(counts)
        )
    Draft202012Validator.check_schema(result)
    return result, {
        "decision": "PASS",
        "binding_count": len(bound),
        "bound_data_elements": sorted(bound),
    }


def project_provider_to_admitted_instances(
    provider_schema: dict[str, Any],
    skeleton: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Project named arrays to fixed, requirement-admitted identity slots.

    A named array is an array whose item schema exposes ``SHORT-NAME``.  Such
    arrays are not model-owned: the deterministic skeleton supplies their
    identities and cardinality.  In provider space the array therefore becomes
    an object whose only legal keys are the admitted identities, while each
    value schema contains semantic fields but no ``SHORT-NAME``.  An empty
    admitted set becomes a closed empty object, so the provider cannot create
    an instance merely because the full XSD schema permits one.

    The returned plan is the reversible mapping used by
    :func:`materialize_admitted_provider_payload`; no invalid provider entry is
    dropped or renamed.
    """

    records: list[dict[str, Any]] = []
    effective_skeleton: dict[str, Any] = skeleton
    skeleton_root_key: str | None = None
    root_properties = provider_schema.get("properties") or {}
    if (
        isinstance(root_properties, dict)
        and len(root_properties) == 1
        and isinstance(skeleton, dict)
    ):
        sole_root = next(iter(root_properties))
        if sole_root not in skeleton:
            effective_skeleton = {sole_root: skeleton}
            skeleton_root_key = sole_root

    def skeleton_lists_for_key(value: Any, key: str) -> list[list[Any]]:
        found: list[list[Any]] = []
        if isinstance(value, dict):
            for child_key, child in value.items():
                if str(child_key) == key and isinstance(child, list):
                    found.append(child)
                found.extend(skeleton_lists_for_key(child, key))
        elif isinstance(value, list):
            for child in value:
                found.extend(skeleton_lists_for_key(child, key))
        return found

    def project(
        schema_node: Any,
        skeleton_node: Any,
        path: tuple[str, ...],
    ) -> tuple[Any, dict[str, Any]]:
        if not isinstance(schema_node, dict):
            return deepcopy(schema_node), {"kind": "scalar"}
        node_type = schema_node.get("type")
        if node_type == "object":
            result = deepcopy(schema_node)
            properties = result.get("properties") or {}
            source_properties = schema_node.get("properties") or {}
            projected_properties: dict[str, Any] = {}
            children: dict[str, Any] = {}
            for key, child_schema in source_properties.items():
                child_skeleton = (
                    skeleton_node.get(key)
                    if isinstance(skeleton_node, dict) and key in skeleton_node
                    else None
                )
                child_projected, child_plan = project(
                    child_schema, child_skeleton, (*path, str(key))
                )
                projected_properties[key] = child_projected
                children[key] = child_plan
            result["properties"] = projected_properties
            if "required" in result:
                result["required"] = [
                    key for key in result.get("required") or []
                    if key in projected_properties
                ]
            return result, {"kind": "object", "children": children}
        if node_type == "array":
            item_schema = schema_node.get("items") or {}
            item_properties = (
                item_schema.get("properties") or {}
                if isinstance(item_schema, dict)
                else {}
            )
            if "SHORT-NAME" in item_properties:
                skeleton_resolution = "direct"
                if isinstance(skeleton_node, list):
                    admitted = skeleton_node
                else:
                    candidates = skeleton_lists_for_key(
                        effective_skeleton, str(path[-1]) if path else ""
                    )
                    if len(candidates) > 1:
                        raise ElementSelectionError(
                            "named-array skeleton projection is ambiguous at "
                            + "/".join(path)
                        )
                    admitted = candidates[0] if candidates else []
                    skeleton_resolution = (
                        "unique_terminal_key" if candidates else "absent_closed_empty"
                    )
                names: list[str] = []
                slots: dict[str, Any] = {}
                slot_plans: dict[str, Any] = {}
                for position, item in enumerate(admitted):
                    if not isinstance(item, dict):
                        raise ElementSelectionError(
                            "requirement-owned named-array skeleton item is not an object at "
                            + "/".join(path)
                        )
                    name = str(item.get("SHORT-NAME") or "").strip()
                    if not name:
                        raise ElementSelectionError(
                            "requirement-owned named-array skeleton item is unnamed at "
                            + "/".join((*path, str(position)))
                        )
                    if name in slots:
                        raise ElementSelectionError(
                            "duplicate requirement-owned identity at "
                            + "/".join(path)
                            + f": {name!r}"
                        )
                    semantic_schema = deepcopy(item_schema)
                    semantic_properties = dict(
                        semantic_schema.get("properties") or {}
                    )
                    semantic_properties.pop("SHORT-NAME", None)
                    semantic_schema["properties"] = semantic_properties
                    semantic_schema["required"] = [
                        key for key in semantic_schema.get("required") or []
                        if key != "SHORT-NAME"
                    ]
                    projected_item, item_plan = project(
                        semantic_schema, item, (*path, name)
                    )
                    names.append(name)
                    slots[name] = projected_item
                    slot_plans[name] = item_plan
                projected = {
                    "type": "object",
                    "properties": slots,
                    "required": list(names),
                    "additionalProperties": False,
                }
                records.append(
                    {
                        "path": list(path),
                        "admitted_identities": list(names),
                        "admitted_count": len(names),
                        "skeleton_resolution": skeleton_resolution,
                    }
                )
                return projected, {
                    "kind": "admitted_named_array",
                    "identities": list(names),
                    "slots": slot_plans,
                }
            projected_items, item_plan = project(item_schema, None, (*path, "*"))
            result = deepcopy(schema_node)
            result["items"] = projected_items
            return result, {"kind": "array", "item": item_plan}
        return deepcopy(schema_node), {"kind": "scalar"}

    projected, tree = project(provider_schema, effective_skeleton, ())
    Draft202012Validator.check_schema(projected)
    return projected, {
        "decision": "PASS",
        "strategy": "fixed_identity_slots_from_requirement_skeleton",
        "named_array_count": len(records),
        "admitted_instance_count": sum(item["admitted_count"] for item in records),
        "named_arrays": records,
        "skeleton_root_key": skeleton_root_key,
        "tree": tree,
    }


def materialize_admitted_provider_payload(
    payload: dict[str, Any],
    projected_schema: dict[str, Any],
    projection_plan: dict[str, Any],
    skeleton: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Reconstruct requirement-owned arrays without normalizing provider errors.

    The raw payload must conform to the admitted-only schema before this
    function runs.  Reconstruction is a reversible contract mapping, not a
    repair step: it never drops an entry, guesses an identity, resolves a
    duplicate, or overwrites an identity supplied by the provider (the latter
    is absent from provider space by construction).
    """

    errors = sorted(
        Draft202012Validator(projected_schema).iter_errors(payload),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        first = errors[0]
        location = "/".join(str(item) for item in first.absolute_path) or "<root>"
        raise ElementSelectionError(
            f"raw provider payload violates admitted-only schema at {location}: "
            f"{first.message}"
        )

    def materialize(
        value: Any,
        plan: dict[str, Any],
        skeleton_value: Any,
        path: tuple[str, ...],
    ) -> Any:
        kind = plan.get("kind")
        if kind == "object":
            if not isinstance(value, dict):
                raise ElementSelectionError(
                    "admitted provider object changed type at " + "/".join(path)
                )
            # The projection plan already carries every admitted identity.  Do
            # not copy the differently wrapped skeleton object into provider
            # space: that would reintroduce wrapper fields absent from this
            # schema and turn deterministic restoration into normalization.
            result: dict[str, Any] = {}
            if isinstance(skeleton_value, dict) and skeleton_value.get("SHORT-NAME"):
                result["SHORT-NAME"] = str(skeleton_value["SHORT-NAME"])
            for key, child in (plan.get("children") or {}).items():
                if key not in value:
                    continue
                result[key] = materialize(
                    value[key], child, None, (*path, str(key))
                )
            return result
        if kind == "admitted_named_array":
            identities = list(plan.get("identities") or [])
            if not isinstance(value, dict) or set(value) != set(identities):
                raise ElementSelectionError(
                    "admitted provider identities changed at " + "/".join(path)
                )
            result = []
            for name in identities:
                base = {"SHORT-NAME": name}
                semantic = materialize(
                    value[name],
                    (plan.get("slots") or {})[name],
                    base,
                    (*path, name),
                )
                if not isinstance(semantic, dict):
                    raise ElementSelectionError(
                        "admitted provider slot is not an object at "
                        + "/".join((*path, name))
                    )
                if semantic.get("SHORT-NAME") != name:
                    raise ElementSelectionError(
                        "admitted provider slot conflicts with expected identity at "
                        + "/".join((*path, name))
                    )
                result.append(semantic)
            return result
        if kind == "array":
            if not isinstance(value, list):
                raise ElementSelectionError(
                    "admitted provider array changed type at " + "/".join(path)
                )
            return [
                materialize(item, plan.get("item") or {}, None, (*path, str(index)))
                for index, item in enumerate(value)
            ]
        return deepcopy(value)

    effective_skeleton: dict[str, Any] = skeleton
    skeleton_root_key = projection_plan.get("skeleton_root_key")
    if skeleton_root_key:
        effective_skeleton = {str(skeleton_root_key): skeleton}
    result = materialize(payload, projection_plan["tree"], effective_skeleton, ())
    return result, {
        "decision": "PASS",
        "strategy": "reversible_admitted_identity_materialization",
        "normalization_status": "NOT_APPLICABLE",
        "named_array_count": int(projection_plan.get("named_array_count") or 0),
        "admitted_instance_count": int(
            projection_plan.get("admitted_instance_count") or 0
        ),
        "dropped_instance_count": 0,
        "renamed_instance_count": 0,
    }


def project_payload_to_admitted_provider_schema(
    payload: dict[str, Any], projection_plan: dict[str, Any]
) -> dict[str, Any]:
    """Encode a known-valid full provider payload into admitted provider space.

    This is used by deterministic reference/precheck tooling only.  It is the
    inverse of :func:`materialize_admitted_provider_payload` and refuses source
    arrays whose identities differ from the frozen admitted set.
    """

    def encode(value: Any, plan: dict[str, Any], path: tuple[str, ...]) -> Any:
        kind = plan.get("kind")
        if kind == "object":
            if not isinstance(value, dict):
                raise ElementSelectionError(
                    "reference payload object changed type at " + "/".join(path)
                )
            return {
                key: encode(value[key], child, (*path, str(key)))
                for key, child in (plan.get("children") or {}).items()
                if key in value
            }
        if kind == "admitted_named_array":
            if not isinstance(value, list):
                raise ElementSelectionError(
                    "reference payload named array changed type at "
                    + "/".join(path)
                )
            identities = list(plan.get("identities") or [])
            by_name: dict[str, Any] = {}
            for position, item in enumerate(value):
                if not isinstance(item, dict):
                    raise ElementSelectionError(
                        "reference payload named-array item is not an object at "
                        + "/".join((*path, str(position)))
                    )
                name = str(item.get("SHORT-NAME") or "").strip()
                if not name:
                    raise ElementSelectionError(
                        "reference payload named-array item is unnamed at "
                        + "/".join((*path, str(position)))
                    )
                if name in by_name:
                    raise ElementSelectionError(
                        "reference payload has duplicate identity at "
                        + "/".join(path)
                        + f": {name!r}"
                    )
                by_name[name] = item
            if set(by_name) != set(identities):
                raise ElementSelectionError(
                    "reference payload identities differ from admitted set at "
                    + "/".join(path)
                    + f": observed={sorted(by_name)!r}, admitted={sorted(identities)!r}"
                )
            return {
                name: encode(
                    {
                        key: item
                        for key, item in by_name[name].items()
                        if key != "SHORT-NAME"
                    },
                    (plan.get("slots") or {})[name],
                    (*path, name),
                )
                for name in identities
            }
        if kind == "array":
            if not isinstance(value, list):
                raise ElementSelectionError(
                    "reference payload array changed type at " + "/".join(path)
                )
            return [
                encode(item, plan.get("item") or {}, (*path, str(index)))
                for index, item in enumerate(value)
            ]
        return deepcopy(value)

    encoded = encode(payload, projection_plan["tree"], ())
    if not isinstance(encoded, dict):
        raise ElementSelectionError("admitted provider payload root must be an object")
    return encoded


def materialize_deterministic_values(
    payload: dict[str, Any],
    full_schema: dict[str, Any],
    element_design: object,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Materialize exact anchored values and revalidate the full schema.

    Named repeated ancestors must already exist in provider output. Only
    descendants below the deepest declared anchor may be created, so this
    cannot silently invent a missing port or other named semantic entity.
    """
    if not isinstance(payload, dict):
        raise ElementSelectionError("provider payload must be an object")
    result = deepcopy(payload)
    roots = [value for value in result.values() if isinstance(value, dict)]
    data_root: Any = roots[0] if len(result) == 1 and len(roots) == 1 else result
    applied: list[dict[str, Any]] = []
    for selection in parse_element_selections(
        element_design, minimum_path_segments=1
    ):
        if not selection.value_present or not selection.anchors:
            raise ElementSelectionError(
                "deterministic materialization requires exact anchor-bound values"
            )
        matches = _search_matches(full_schema, selection.path)
        if not matches and selection.path[-1] == "#TEXT":
            matches = _search_matches(full_schema, selection.path[:-1])
        if len(matches) != 1:
            reason = "missing" if not matches else f"ambiguous ({len(matches)} matches)"
            raise ElementSelectionError(
                f"full schema deterministic value path is {reason}: "
                + "/".join(selection.path)
            )
        trail, target = matches[0]
        if target.get("type") in {"object", "array"}:
            raise ElementSelectionError(
                "deterministic materialization requires a scalar XSD leaf, not container "
                + "/".join(selection.path)
            )
        anchors = {anchor.path_index: anchor.short_name for anchor in selection.anchors}
        deepest_anchor = max(anchors)
        current: Any = data_root
        # Absolute payload location of this requirement-owned value, relative to
        # the component root.  Downstream repair uses it as the immutable set;
        # ``selection.path`` alone is a schema-relative fragment and cannot
        # identify which array occurrence the constant was written into.
        resolved_path: list[Any] = []
        for path_index, (_parent_schema, key, child_schema) in enumerate(trail):
            if not isinstance(current, dict):
                raise ElementSelectionError(
                    "provider payload has a non-object before "
                    + "/".join(selection.path[: path_index + 1])
                )
            schema_type = child_schema.get("type")
            if schema_type == "array":
                value = current.get(key)
                if value is None:
                    if path_index <= deepest_anchor:
                        raise ElementSelectionError(
                            f"provider omitted anchor-owning array {key!r}"
                        )
                    value = []
                    current[key] = value
                if not isinstance(value, list):
                    raise ElementSelectionError(f"provider property {key!r} is not an array")
                anchor_name = anchors.get(path_index)
                if anchor_name:
                    candidates = [
                        (position, item)
                        for position, item in enumerate(value)
                        if isinstance(item, dict)
                        and str(item.get("SHORT-NAME") or "") == anchor_name
                    ]
                    if len(candidates) != 1:
                        reason = "missing" if not candidates else "ambiguous"
                        raise ElementSelectionError(
                            f"provider anchor {anchor_name!r} is {reason} at {key!r}"
                        )
                    position, current = candidates[0]
                    resolved_path.extend([key, position])
                else:
                    if not value:
                        value.append({})
                    if len(value) != 1 or not isinstance(value[0], dict):
                        raise ElementSelectionError(
                            f"deterministic value path is ambiguous at array {key!r}"
                        )
                    current = value[0]
                    resolved_path.extend([key, 0])
                continue
            if schema_type == "object":
                value = current.get(key)
                if value is None:
                    if path_index <= deepest_anchor:
                        raise ElementSelectionError(
                            f"provider omitted anchor-owning object {key!r}"
                        )
                    value = {}
                    current[key] = value
                if not isinstance(value, dict):
                    raise ElementSelectionError(f"provider property {key!r} is not an object")
                current = value
                resolved_path.append(key)
                continue

            expected = _coerce_const(selection.value, target)
            if key in current and current[key] != expected:
                raise ElementSelectionError(
                    f"provider supplied a conflicting deterministic value at {key!r}"
                )
            current[key] = expected
            current = expected
            resolved_path.append(key)

        applied.append(
            {
                "path": list(selection.path),
                "resolved_path": list(resolved_path),
                "value": selection.value,
                "anchors": [
                    {
                        "path_index": anchor.path_index,
                        "short_name": anchor.short_name,
                    }
                    for anchor in selection.anchors
                ],
            }
        )

    errors = sorted(
        Draft202012Validator(full_schema).iter_errors(result),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        first = errors[0]
        location = "/".join(str(item) for item in first.absolute_path) or "<root>"
        raise ElementSelectionError(
            f"materialized provider JSON violates the full schema at {location}: "
            f"{first.message}"
        )
    return result, {
        "decision": "PASS",
        "applied_count": len(applied),
        "applied": applied,
        "full_schema_revalidated": True,
    }


def provider_schema_container_depth(schema: dict[str, Any]) -> int:
    """Return maximum nested object/array containers for Structured Outputs."""
    if not isinstance(schema, dict):
        raise ElementSelectionError("provider schema must be an object")

    def walk(node: object) -> int:
        if not isinstance(node, dict):
            return 0
        if "$ref" in node:
            raise ElementSelectionError(
                "provider schema depth audit does not support unresolved $ref"
            )
        raw_type = node.get("type")
        types = set(raw_type) if isinstance(raw_type, list) else {raw_type}
        own_depth = 1 if types & {"object", "array"} else 0
        children: list[int] = []
        properties = node.get("properties")
        if isinstance(properties, dict):
            children.extend(walk(child) for child in properties.values())
        items = node.get("items")
        if isinstance(items, dict):
            children.append(walk(items))
        return own_depth + (max(children) if children else 0)

    return walk(schema)


def partition_provider_schema(
    schema: dict[str, Any], *, maximum_depth: int = 10
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Build strict mergeable calls without weakening a deep component schema."""
    if (
        isinstance(maximum_depth, bool)
        or not isinstance(maximum_depth, int)
        or maximum_depth < 1
    ):
        raise ElementSelectionError("provider maximum depth must be a positive integer")
    Draft202012Validator.check_schema(schema)
    full_depth = provider_schema_container_depth(schema)
    if full_depth > maximum_depth:
        return _partition_deep_provider_schema(
            schema, full_depth=full_depth, maximum_depth=maximum_depth
        )
    call = {
        "call_id": "full", "root_property": None, "merge_path": [],
        "nesting_depth": full_depth, "schema": deepcopy(schema),
    }
    return [call], {
        "decision": "PASS", "strategy": "single_strict_schema",
        "maximum_depth": maximum_depth, "full_schema_depth": full_depth,
        "component_root": None, "call_count": 1,
        "calls": [{key: value for key, value in call.items() if key != "schema"}],
    }


def _partition_deep_provider_schema(
    schema: dict[str, Any], *, full_depth: int, maximum_depth: int
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    root_properties = schema.get("properties")
    root_required = schema.get("required")
    if (
        schema.get("type") != "object"
        or not isinstance(root_properties, dict)
        or len(root_properties) != 1
        or not isinstance(root_required, list)
    ):
        raise ElementSelectionError(
            "deep provider schema must contain exactly one required component root"
        )
    component_root, component_schema = next(iter(root_properties.items()))
    if root_required != [component_root] or not isinstance(component_schema, dict):
        raise ElementSelectionError(
            "deep provider schema component root is missing or ambiguous"
        )
    if component_schema.get("type") != "object":
        raise ElementSelectionError("deep provider component root must be an object")
    return _project_required_component_root(
        component_root,
        component_schema,
        full_depth=full_depth,
        maximum_depth=maximum_depth,
    )


def _project_required_component_root(
    component_root: str, component_schema: dict[str, Any],
    *, full_depth: int, maximum_depth: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    projected_depth = provider_schema_container_depth(component_schema)
    if projected_depth > maximum_depth:
        raise ElementSelectionError(
            f"provider schema remains depth {projected_depth} after removing the "
            f"required component transport root; maximum is {maximum_depth}"
        )
    call = {
        "call_id": "full", "root_property": None,
        "merge_path": [component_root], "nesting_depth": projected_depth,
        "schema": deepcopy(component_schema),
    }
    return [call], {
        "decision": "PASS", "strategy": "required_component_root_projection",
        "maximum_depth": maximum_depth, "full_schema_depth": full_depth,
        "component_root": component_root, "call_count": 1,
        "calls": [{key: value for key, value in call.items() if key != "schema"}],
    }


def merge_provider_schema_payloads(
    payloads: dict[str, Any],
    full_schema: dict[str, Any],
    partition_plan: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Merge provider partitions and revalidate the original provider schema."""
    if not isinstance(payloads, dict) or not isinstance(partition_plan, dict):
        raise ElementSelectionError("provider partition inputs must be objects")
    calls = partition_plan.get("calls")
    if not isinstance(calls, list) or not calls:
        raise ElementSelectionError("provider partition plan has no calls")
    expected_ids = [str(call.get("call_id") or "") for call in calls]
    if not all(expected_ids) or set(payloads) != set(expected_ids):
        raise ElementSelectionError("provider partition payload identities do not match plan")
    strategy = str(partition_plan.get("strategy") or "")
    if strategy == "single_strict_schema":
        result = deepcopy(payloads[expected_ids[0]])
    elif strategy == "required_component_root_projection":
        component_root = str(partition_plan.get("component_root") or "")
        if not component_root:
            raise ElementSelectionError("provider projection component root is missing")
        result = {component_root: deepcopy(payloads[expected_ids[0]])}
    else:
        raise ElementSelectionError(
            f"unsupported provider partition strategy {strategy!r}"
        )
    _validate_merged_provider_payload(result, full_schema)
    return result, {
        "decision": "PASS", "strategy": strategy,
        "merged_call_count": len(calls),
        "full_provider_schema_revalidated": True,
    }


def _validate_merged_provider_payload(
    payload: dict[str, Any], full_schema: dict[str, Any]
) -> None:
    errors = sorted(
        Draft202012Validator(full_schema).iter_errors(payload),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        first = errors[0]
        location = "/".join(str(item) for item in first.absolute_path) or "<root>"
        raise ElementSelectionError(
            "merged provider partitions violate the full provider schema at "
            f"{location}: {first.message}"
        )


def apply_element_selections(
    schema: dict[str, Any], element_design: object
) -> dict[str, Any]:
    """Promote selected paths in a generated provider JSON Schema.

    Every ancestor of a min-occurs selection becomes required.  Occurrence
    constraints apply to the selected final node.  Constant values are applied
    only after the target schema type and enum have been checked.
    """
    result = deepcopy(schema)
    for selection in parse_element_selections(
        element_design, minimum_path_segments=1
    ):
        matches = _search_matches(result, selection.path)
        # Canonical XML IR may explicitly select an element's direct text.
        # Provider JSON represents complex simple-content as a #text property,
        # but represents primitive XSD elements as the scalar property itself.
        # Resolve that projection from the generated schema instead of asking
        # the model to predict the provider representation.
        if not matches and selection.path[-1] == "#TEXT":
            scalar_matches = _search_matches(result, selection.path[:-1])
            if len(scalar_matches) == 1:
                scalar_target = scalar_matches[0][1]
                if scalar_target.get("type") in {"string", "number", "integer", "boolean"}:
                    matches = scalar_matches
        if len(matches) != 1:
            reason = "missing" if not matches else f"ambiguous ({len(matches)} matches)"
            raise ElementSelectionError(
                f"selected AUTOSAR path is {reason}: {'/'.join(selection.path)}"
            )
        trail, target = matches[0]
        if selection.value_present and target.get("type") in {"object", "array"}:
            raise ElementSelectionError(
                "exact selection value must target a scalar XSD leaf "
                "(#TEXT, an attribute, or a primitive element), not container "
                + "/".join(selection.path)
            )
        if any(anchor.path_index >= len(trail) for anchor in selection.anchors):
            raise ElementSelectionError(
                "selection anchor targets a non-element projection at "
                + "/".join(selection.path)
            )
        if selection.min_occurs >= 1:
            for parent, key, _child in trail:
                required = parent.setdefault("required", [])
                if key not in required:
                    required.append(key)

        occurrence_target = target
        if (
            target.get("type") != "array"
            and (selection.min_occurs > 1 or selection.max_occurs > 1)
        ):
            # A count declared on a wrapper belongs to the repeated element the
            # wrapper contains, not to the repeated element above it.  Lifting
            # "three DATA-SEND-POINTS" past the wrapper onto RUNNABLE-ENTITY
            # asked the provider for at least three runnables and at most one,
            # and no response could satisfy that.
            repeated_child = _sole_repeated_child(target)
            if repeated_child is not None:
                occurrence_target = repeated_child
            else:
                # Phase 1 describes XML path occurrences, while the provider
                # schema represents repeated XSD elements as arrays of
                # containing objects.  A count such as two
                # VARIABLE-ACCESS/SHORT-NAME values therefore belongs to the
                # deepest repeated ancestor, not to the scalar SHORT-NAME
                # property.  Only an array already proven by the Phase 2 schema
                # may receive the lifted bound; otherwise fail closed below.
                repeated_ancestors = [
                    child
                    for _parent, _key, child in trail
                    if child.get("type") == "array"
                ]
                if repeated_ancestors:
                    occurrence_target = repeated_ancestors[-1]

        if occurrence_target.get("type") == "array":
            occurrence_target["minItems"] = max(
                selection.min_occurs,
                int(occurrence_target.get("minItems") or 0),
            )
            if selection.anchors:
                occurrence_metadata = occurrence_target.setdefault(
                    "x-atlas-instance-occurrence-constraints", []
                )
                occurrence_entry = {
                    "anchors": [
                        {"path_index": anchor.path_index, "short_name": anchor.short_name}
                        for anchor in selection.anchors
                    ],
                    "min_occurs": selection.min_occurs,
                    "max_occurs": selection.max_occurs,
                }
                if occurrence_entry not in occurrence_metadata:
                    occurrence_metadata.append(occurrence_entry)
            else:
                existing_max = occurrence_target.get("maxItems")
                occurrence_target["maxItems"] = (
                    min(selection.max_occurs, int(existing_max))
                    if existing_max is not None
                    else selection.max_occurs
                )
            # An anchored selection raised minItems without this check, so a
            # bound of at least three and at most one could reach the provider.
            # No response satisfies that, and the run was then recorded as a
            # model failure.  It is a local contradiction and stops here.
            bound = occurrence_target.get("maxItems")
            if bound is not None and occurrence_target["minItems"] > int(bound):
                raise ElementSelectionError(
                    "selection occurrence range conflicts with XSD at "
                    + "/".join(selection.path)
                    + f" (minItems {occurrence_target['minItems']} > maxItems {int(bound)})"
                )
        elif selection.min_occurs > 1 or selection.max_occurs > 1:
            raise ElementSelectionError(
                "non-array selection cannot occur more than once: "
                + "/".join(selection.path)
            )

        anchored_to_repeated_schema = any(
            trail[anchor.path_index][2].get("type") == "array"
            for anchor in selection.anchors
        )
        if selection.value_present and selection.anchors and anchored_to_repeated_schema:
            metadata = target.setdefault("x-atlas-instance-value-constraints", [])
            entry = {
                "anchors": [
                    {"path_index": anchor.path_index, "short_name": anchor.short_name}
                    for anchor in selection.anchors
                ],
                "value": selection.value,
            }
            if entry not in metadata:
                metadata.append(entry)
        elif selection.value_present:
            value = _coerce_const(selection.value, target)
            const_target = _object_node(target) if target.get("type") == "array" else target
            _merge_const(const_target, value, selection.path)
    return result
