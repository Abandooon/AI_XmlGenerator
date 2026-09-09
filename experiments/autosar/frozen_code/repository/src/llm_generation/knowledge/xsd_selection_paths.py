"""Hash-pinned AUTOSAR XSD validation for Phase 1 selection paths.

Phase 1 expresses element intent, but it is not allowed to invent XML
containment.  This module resolves every path against the physical XSD type
graph before Phase 2 performs a Neo4j query or calls a provider.  Named base
groups and anonymous wrapper types are expanded by ``xmlschema``; no tag-only
or post-serialization ordering heuristic is used.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Iterable
import warnings

import xmlschema


AUTOSAR_NAMESPACE = "http://autosar.org/schema/r4.0"


class XsdSelectionPathError(ValueError):
    """A selection path is absent, ambiguous, or unsupported by the pinned XSD."""


@dataclass(frozen=True)
class XsdPathResolution:
    original_path: tuple[str, ...]
    canonical_path: tuple[str, ...]
    resolution: str


def _local_name(value: object) -> str:
    local = getattr(value, "local_name", None)
    if local:
        return str(local).upper()
    text = str(getattr(value, "name", value) or "")
    if text.startswith("{") and "}" in text:
        text = text.split("}", 1)[1]
    return text.split(":", 1)[-1].upper()


def _direct_elements(xsd_type: object) -> tuple[object, ...]:
    """Flatten model groups while stopping at direct element particles."""
    content = getattr(xsd_type, "content", None)
    if content is None:
        return ()
    result: list[object] = []

    def walk(particle: object) -> None:
        if particle.__class__.__name__ == "XsdElement":
            result.append(particle)
            return
        try:
            members = list(particle)  # XsdGroup, including inherited groups.
        except (TypeError, AttributeError):
            return
        for member in members:
            walk(member)

    walk(content)
    return tuple(result)


def _has_text(xsd_type: object) -> bool:
    if bool(getattr(xsd_type, "mixed", False)) or str(
        getattr(xsd_type, "content_type_label", "") or ""
    ).lower() == "mixed":
        return True
    method = getattr(xsd_type, "has_simple_content", None)
    if callable(method):
        try:
            return bool(method())
        except (AttributeError, TypeError):
            return False
    is_simple = getattr(xsd_type, "is_simple", None)
    return bool(is_simple()) if callable(is_simple) else False


def _attribute_names(xsd_type: object) -> frozenset[str]:
    attributes = getattr(xsd_type, "attributes", {})
    try:
        return frozenset(_local_name(name) for name in attributes)
    except TypeError:
        return frozenset()


@lru_cache(maxsize=4)
def _compiled_schema(path_text: str, pinned_sha256: str) -> object:
    # xmlschema warns about recursive AUTOSAR model groups while constructing a
    # correct finite component graph.  The path walker itself has explicit
    # cycle and expansion bounds.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return xmlschema.XMLSchema(path_text)


class PinnedXsdSelectionPathIndex:
    """Validate and uniquely canonicalize paths against one pinned XSD."""

    def __init__(self, xsd_path: str | Path, *, expected_sha256: str) -> None:
        path = Path(xsd_path).resolve()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        expected = str(expected_sha256 or "").lower()
        if len(expected) != 64 or digest != expected:
            raise XsdSelectionPathError(
                f"XSD hash mismatch: expected {expected or '<missing>'}, got {digest}"
            )
        self.xsd_path = path
        self.xsd_sha256 = digest
        self.schema = _compiled_schema(str(path), digest)
        self.namespace = str(
            getattr(self.schema, "target_namespace", "") or AUTOSAR_NAMESPACE
        )

    @classmethod
    def from_files(
        cls,
        xsd_path: str | Path,
        *,
        serialization_manifest_path: str | Path,
    ) -> "PinnedXsdSelectionPathIndex":
        manifest_path = Path(serialization_manifest_path)
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise XsdSelectionPathError(
                f"cannot read XSD serialization manifest {manifest_path}: {error}"
            ) from error
        expected = str((manifest.get("xsd") or {}).get("sha256") or "")
        return cls(xsd_path, expected_sha256=expected)

    def _root_type(self, component_type: str) -> object:
        name = str(component_type or "").strip().upper()
        qname = f"{{{self.namespace}}}{name}"
        root = getattr(self.schema, "maps").types.get(qname)
        if root is None:
            raise XsdSelectionPathError(
                f"component type is absent from pinned XSD: {name or '<missing>'}"
            )
        return root

    @staticmethod
    def _deduplicate_states(states: Iterable[object]) -> tuple[object, ...]:
        result: list[object] = []
        seen: set[int] = set()
        for state in states:
            identity = id(state)
            if identity not in seen:
                seen.add(identity)
                result.append(state)
        return tuple(result)

    def _element_states(
        self, states: Iterable[object], segment: str
    ) -> tuple[object, ...]:
        matches = (
            getattr(element, "type", None)
            for state in states
            for element in _direct_elements(state)
            if _local_name(element) == segment
        )
        return self._deduplicate_states(state for state in matches if state is not None)

    def _states_after_elements(
        self, component_type: str, segments: Iterable[str]
    ) -> tuple[object, ...]:
        states: tuple[object, ...] = (self._root_type(component_type),)
        for segment in segments:
            if segment.startswith("@") or segment == "#TEXT":
                return ()
            states = self._element_states(states, segment)
            if not states:
                return ()
        return states

    def _reachable_element_names(
        self, component_type: str, *, max_depth: int
    ) -> frozenset[str]:
        root = self._root_type(component_type)
        names: set[str] = set()
        frontier: list[tuple[object, int]] = [(root, 0)]
        best_depth: dict[int, int] = {id(root): 0}
        while frontier:
            xsd_type, depth = frontier.pop(0)
            if depth >= max_depth:
                continue
            for element in _direct_elements(xsd_type):
                names.add(_local_name(element))
                child = getattr(element, "type", None)
                if child is None:
                    continue
                child_depth = depth + 1
                previous = best_depth.get(id(child))
                if previous is None or child_depth < previous:
                    best_depth[id(child)] = child_depth
                    frontier.append((child, child_depth))
        return frozenset(names)

    def requirement_candidate_paths(
        self,
        component_type: str,
        requirements: str,
        *,
        max_depth: int = 12,
        max_paths: int = 240,
    ) -> tuple[tuple[str, ...], ...]:
        """Return focused physical paths for tags explicitly named by a request.

        This catalog is prompt guidance, not the authority: every returned or
        provider-generated path is still checked by :meth:`validate_path`.
        Ubiquitous ``SHORT-NAME`` paths are derived only below request-named
        identifiable elements, avoiding an impractically large whole-XSD enum.
        """
        mentioned = frozenset(
            re.findall(r"\b[A-Z][A-Z0-9-]{2,}\b", str(requirements or "").upper())
        )
        reachable = self._reachable_element_names(component_type, max_depth=max_depth)
        targets = sorted(
            (mentioned & reachable)
            - {"BEHAVIOR", "ELEMENT", "ELEMENTS", "SHORT-NAME", "TIMEOUT"}
        )
        if not targets:
            return ()
        root_states = (self._root_type(component_type),)
        scored: dict[tuple[str, ...], int] = {}

        def add(candidate: tuple[str, ...], score: int) -> None:
            previous = scored.get(candidate)
            if previous is None or score > previous:
                scored[candidate] = score

        for terminal in targets:
            candidates, exhausted = self._descendant_candidates(
                root_states,
                terminal=terminal,
                pseudo_suffix=None,
                max_depth=max_depth,
                expansion_limit=200000,
                candidate_limit=512,
            )
            if exhausted:
                # A truncated list must never masquerade as a complete
                # candidate constraint.
                continue
            ranked_candidates = [
                (len(set(candidate) & mentioned), candidate)
                for candidate in candidates
            ]
            best_score = max((score for score, _candidate in ranked_candidates), default=0)
            if best_score < 2:
                continue
            for score, candidate in ranked_candidates:
                if score != best_score:
                    continue
                add(candidate, score)
                terminal_states = self._states_after_elements(component_type, candidate)
                if any(_has_text(state) for state in terminal_states):
                    add(candidate + ("#TEXT",), score)
                if any("DEST" in _attribute_names(state) for state in terminal_states):
                    add(candidate + ("@DEST",), score)
                if any(
                    any(_local_name(element) == "SHORT-NAME" for element in _direct_elements(state))
                    for state in terminal_states
                ):
                    short_name = candidate + ("SHORT-NAME",)
                    add(short_name, score)
                    short_name_states = self._states_after_elements(
                        component_type, short_name
                    )
                    if any(_has_text(state) for state in short_name_states):
                        add(short_name + ("#TEXT",), score)
                # Semantic containers named by the request often own the
                # actual reference leaf (for example AUTOSAR-VARIABLE-IREF).
                # Expose only their direct scalar/ref children, never invented
                # deeper tag chains.
                for state in terminal_states:
                    for element in _direct_elements(state):
                        child_name = _local_name(element)
                        if not (
                            child_name == "SHORT-NAME"
                            or child_name.endswith(("-REF", "-TREF"))
                        ):
                            continue
                        child_type = getattr(element, "type", None)
                        if child_type is None or not _has_text(child_type):
                            continue
                        child_path = candidate + (child_name,)
                        add(child_path, score)
                        add(child_path + ("#TEXT",), score)
                        if "DEST" in _attribute_names(child_type):
                            add(child_path + ("@DEST",), score)

        ordered = sorted(
            scored,
            key=lambda candidate: (-scored[candidate], len(candidate), candidate),
        )
        return tuple(ordered[:max_paths])

    def validate_path(self, component_type: str, path: Iterable[str]) -> None:
        segments = tuple(str(item or "").strip().upper() for item in path)
        if not segments:
            raise XsdSelectionPathError("selection path is empty")
        states: tuple[object, ...] = (self._root_type(component_type),)
        for index, segment in enumerate(segments):
            final = index == len(segments) - 1
            if segment.startswith("@"):
                if not final:
                    raise XsdSelectionPathError(
                        f"attribute segment must be terminal at {'/'.join(segments[: index + 1])}"
                    )
                wanted = segment[1:]
                if any(wanted in _attribute_names(state) for state in states):
                    return
                available = sorted({name for state in states for name in _attribute_names(state)})
                raise XsdSelectionPathError(
                    f"XSD attribute @{wanted} is absent after {'/'.join(segments[:index])}; "
                    f"available attributes: {', '.join(available) or '<none>'}"
                )
            if segment == "#TEXT":
                if not final:
                    raise XsdSelectionPathError(
                        f"#TEXT must be terminal at {'/'.join(segments[: index + 1])}"
                    )
                if any(_has_text(state) for state in states):
                    return
                raise XsdSelectionPathError(
                    f"XSD type has no direct text after {'/'.join(segments[:index])}"
                )

            next_states = self._element_states(states, segment)
            if not next_states:
                available = sorted(
                    {_local_name(element) for state in states for element in _direct_elements(state)}
                )
                raise XsdSelectionPathError(
                    f"XSD child {segment} is absent after "
                    f"{'/'.join(segments[:index]) or '<component-root>'}; "
                    f"available children: {', '.join(available) or '<none>'}"
                )
            states = next_states

    def has_direct_text(self, component_type: str, path: Iterable[str]) -> bool:
        """Return true only when every XSD state at an exact element path has text.

        This deliberately performs no descendant repair.  It is used to turn a
        model's exact value on a simple-content element (for example a TREF)
        into the canonical ``#TEXT`` leaf, while leaving complex containers
        such as ``INIT-VALUE`` unsupported and fail-closed.
        """
        segments = tuple(str(item or "").strip().upper() for item in path)
        if not segments or any(
            segment == "#TEXT" or segment.startswith("@") for segment in segments
        ):
            return False
        self.validate_path(component_type, segments)
        states = self._states_after_elements(component_type, segments)
        return bool(states) and all(_has_text(state) for state in states)

    def requires_direct_text_leaf(
        self, component_type: str, path: Iterable[str]
    ) -> bool:
        """Return true when the JSON projection must represent text as ``#TEXT``.

        Plain AUTOSAR simple-content value types (for example ``SHORT-NAME``
        or ``PERIOD``) are scalar JSON leaves even though their XSD base type
        exposes generic serialization attributes.  A direct-text reference
        type with an XSD ``DEST`` attribute is the Phase 2 ``{@DEST,#text}``
        object, so its lexical value needs the explicit ``#TEXT`` leaf.
        """
        segments = tuple(str(item or "").strip().upper() for item in path)
        if not self.has_direct_text(component_type, segments):
            return False
        states = self._states_after_elements(component_type, segments)
        return bool(states) and all(
            "DEST" in _attribute_names(state) for state in states
        )

    def element_occurrence_bounds(
        self, component_type: str, path: Iterable[str]
    ) -> tuple[int, int | None]:
        """Return the terminal element particle's XSD occurrence bounds.

        This is intentionally limited to physical element paths.  Multiple
        particles with different bounds are ambiguous for a tag-only semantic
        selection and therefore fail closed.
        """
        segments = tuple(str(item or "").strip().upper() for item in path)
        if not segments or any(
            segment == "#TEXT" or segment.startswith("@") for segment in segments
        ):
            raise XsdSelectionPathError(
                "occurrence bounds require a non-empty physical element path"
            )
        states: tuple[object, ...] = (self._root_type(component_type),)
        for index, segment in enumerate(segments):
            matches = [
                element
                for state in states
                for element in _direct_elements(state)
                if _local_name(element) == segment
            ]
            if not matches:
                raise XsdSelectionPathError(
                    f"XSD child {segment} is absent after "
                    f"{'/'.join(segments[:index]) or '<component-root>'}"
                )
            if index == len(segments) - 1:
                bounds: set[tuple[int, int | None]] = set()
                for element in matches:
                    minimum = int(getattr(element, "min_occurs", 1))
                    raw_maximum = getattr(element, "max_occurs", 1)
                    maximum = None if raw_maximum is None else int(raw_maximum)
                    bounds.add((minimum, maximum))
                if len(bounds) != 1:
                    raise XsdSelectionPathError(
                        "ambiguous XSD occurrence bounds for " + "/".join(segments)
                    )
                return next(iter(bounds))
            states = self._deduplicate_states(
                getattr(element, "type", None)
                for element in matches
                if getattr(element, "type", None) is not None
            )
        raise XsdSelectionPathError(
            "could not resolve XSD occurrence bounds for " + "/".join(segments)
        )

    @staticmethod
    def _is_subsequence(needle: tuple[str, ...], haystack: tuple[str, ...]) -> bool:
        cursor = 0
        for segment in haystack:
            if cursor < len(needle) and needle[cursor] == segment:
                cursor += 1
        return cursor == len(needle)

    def _descendant_candidates(
        self,
        states: tuple[object, ...],
        *,
        terminal: str,
        pseudo_suffix: str | None,
        max_depth: int,
        expansion_limit: int,
        candidate_limit: int = 256,
    ) -> tuple[tuple[tuple[str, ...], ...], bool]:
        candidates: set[tuple[str, ...]] = set()
        expansions = 0
        exhausted = False
        memo: dict[tuple[int, int], tuple[tuple[str, ...], ...]] = {}

        def supports_suffix(xsd_type: object) -> bool:
            if pseudo_suffix is None:
                return True
            if pseudo_suffix == "#TEXT":
                return _has_text(xsd_type)
            return pseudo_suffix[1:] in _attribute_names(xsd_type)

        def paths_from(
            xsd_type: object,
            remaining: int,
        ) -> tuple[tuple[str, ...], ...]:
            nonlocal expansions, exhausted
            if exhausted or remaining <= 0:
                return ()
            cache_key = (id(xsd_type), remaining)
            cached = memo.get(cache_key)
            if cached is not None:
                return cached
            result: set[tuple[str, ...]] = set()
            for element in _direct_elements(xsd_type):
                expansions += 1
                if expansions > expansion_limit:
                    exhausted = True
                    return ()
                name = _local_name(element)
                child_type = getattr(element, "type", None)
                if child_type is None:
                    continue
                if name == terminal and supports_suffix(child_type):
                    result.add(
                        (name,) + ((pseudo_suffix,) if pseudo_suffix is not None else ())
                    )
                if remaining > 1:
                    for suffix in paths_from(child_type, remaining - 1):
                        result.add((name,) + suffix)
                        if len(result) > candidate_limit:
                            exhausted = True
                            return ()
            ordered = tuple(sorted(result))
            memo[cache_key] = ordered
            return ordered

        for state in states:
            candidates.update(paths_from(state, max_depth))
            if len(candidates) > candidate_limit:
                exhausted = True
                break
        return tuple(sorted(candidates)), exhausted

    def resolve_path(
        self,
        component_type: str,
        path: Iterable[str],
        *,
        max_descendant_depth: int = 6,
        expansion_limit: int = 100000,
    ) -> XsdPathResolution:
        """Return an exact path or one uniquely provable missing-wrapper repair.

        A repair is allowed only below the deepest valid ancestor.  The
        proposed remaining element tags must be an ordered subsequence of one
        and only one XSD candidate.  If the proposal has no usable intermediate
        tag, the terminal itself must have exactly one candidate.  Ambiguity or
        a search bound is fail-closed.
        """
        original = tuple(str(item or "").strip().upper() for item in path)
        validation_error: XsdSelectionPathError | None = None
        try:
            self.validate_path(component_type, original)
            return XsdPathResolution(original, original, "exact")
        except XsdSelectionPathError as error:
            validation_error = error
        assert validation_error is not None

        pseudo_suffix = original[-1] if original and (
            original[-1] == "#TEXT" or original[-1].startswith("@")
        ) else None
        elements = original[:-1] if pseudo_suffix is not None else original
        if len(elements) < 2:
            raise validation_error
        terminal = elements[-1]

        longest_prefix = 0
        for length in range(1, len(elements)):
            if self._states_after_elements(component_type, elements[:length]):
                longest_prefix = length
            else:
                break
        if longest_prefix == 0:
            raise validation_error

        for prefix_length in range(longest_prefix, 0, -1):
            prefix = elements[:prefix_length]
            states = self._states_after_elements(component_type, prefix)
            candidates, exhausted = self._descendant_candidates(
                states,
                terminal=terminal,
                pseudo_suffix=pseudo_suffix,
                max_depth=max_descendant_depth,
                expansion_limit=expansion_limit,
            )
            if exhausted:
                raise XsdSelectionPathError(
                    f"XSD repair search exceeded {expansion_limit} particles for "
                    f"{'/'.join(original)}; original error: {validation_error}"
                ) from validation_error
            if not candidates:
                continue
            proposed_tail = elements[prefix_length:]
            specific = tuple(
                candidate
                for candidate in candidates
                if self._is_subsequence(proposed_tail, candidate)
            )
            eligible = specific if specific else candidates
            if len(eligible) != 1:
                rendered = ["/".join(prefix + candidate) for candidate in eligible[:8]]
                raise XsdSelectionPathError(
                    f"XSD path is invalid and has {len(eligible)} candidate repairs: "
                    f"{'/'.join(original)}; candidates: {', '.join(rendered)}"
                ) from validation_error
            canonical = prefix + eligible[0]
            self.validate_path(component_type, canonical)
            return XsdPathResolution(original, canonical, "unique-xsd-descendant")

        raise validation_error
