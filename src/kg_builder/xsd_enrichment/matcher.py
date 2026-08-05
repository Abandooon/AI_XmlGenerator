"""Match parent-aware XSD owners/particles to legacy ATLAS metadata."""

from __future__ import annotations

import re
from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from src.kg_builder.uml_metadata_parser.XsdParser.Utils import to_camel_case, to_pascal_case
from .content_model import XsdContentModelExtractor, canonical_json, semantic_hash

_TYPE_WRAPPER_RE = re.compile(r"^(?:ArrayList|List)<(.+)>$")
_NON_ALNUM = re.compile(r"[^0-9A-Za-z]+")
XSD_METADATA_FIELDS = (
    "xsd_group_model_json",
    "xsd_complex_type_model_json",
    "xsd_effective_model_json",
    "xsd_content_models_json",
    "xsd_owner_ids_json",
    "xsd_source_sha256",
    "xsd_model_sha256",
    "xsd_model_version",
)


def _slug(value: str) -> str:
    return re.sub(r"_+", "_", _NON_ALNUM.sub("_", value)).strip("_")


def _strip_collection(value: str | None) -> str:
    if not value:
        return ""
    result = str(value).strip()
    match = _TYPE_WRAPPER_RE.match(result)
    return match.group(1).strip() if match else result


def _qname_local(value: str | None) -> str:
    if not value:
        return ""
    if value.startswith("{") and "}" in value:
        return value.split("}", 1)[1]
    return value.split(":", 1)[-1]


@dataclass(frozen=True)
class MetadataTarget:
    section: str
    key: str
    record: dict[str, Any]
    entity_id: str

    def public(self) -> dict[str, Any]:
        return {
            "section": self.section,
            "key": self.key,
            "entity_id": self.entity_id,
            "name": self.record.get("name", self.key),
            "xml_tag": self.record.get("xml_tag") or self.record.get("annotation"),
        }


@dataclass(frozen=True)
class AttributeTarget:
    owner: MetadataTarget
    field: str
    index: int
    record: dict[str, Any]

    @property
    def target_id(self) -> str:
        return f"metadata:{self.owner.section}:{self.owner.key}:{self.field}[{self.index}]"

    def public(self) -> dict[str, Any]:
        return {
            "target_id": self.target_id,
            "owner_entity_id": self.owner.entity_id,
            "section": self.owner.section,
            "owner_key": self.owner.key,
            "field": self.field,
            "index": self.index,
            "name": self.record.get("name"),
            "xml_tag": self.record.get("xml_tag"),
            "xml_wrapper_tag": self.record.get("xml_wrapper_tag"),
            "type": self.record.get("type"),
            "document_name": self.record.get("document_name"),
        }


class MetadataMatcher:
    """Resolve XSD declarations only inside their physical parent context."""

    def __init__(
        self,
        metadata: dict[str, Any],
        *,
        domain: str = "AUTOSAR",
        version: str = "4-2-2",
    ) -> None:
        self.metadata = metadata
        self.domain = domain.lower()
        self.version = version
        self._targets: dict[str, list[MetadataTarget]] = defaultdict(list)
        self._target_by_identity: dict[tuple[str, str], MetadataTarget] = {}
        self._owner_targets: dict[str, MetadataTarget] = {}
        self._owner_modes: dict[str, str] = {}
        self._particle_matches: dict[tuple[str, str], dict[str, Any]] = {}
        self._attribute_objects: dict[str, AttributeTarget] = {}
        self._conflicts: list[dict[str, Any]] = []
        self._index_metadata()

    def match(self, content_document: dict[str, Any]) -> dict[str, Any]:
        document = deepcopy(content_document)
        self._owner_targets.clear()
        self._owner_modes.clear()
        self._particle_matches.clear()
        self._attribute_objects.clear()
        self._conflicts.clear()

        owners = document.get("owners") or []
        # Extractor order guarantees named owners first and anonymous parents
        # before nested anonymous children.
        for owner in owners:
            if owner.get("owner_kind") == "anonymousComplexType":
                self._match_anonymous_owner(owner)
            else:
                self._match_named_owner(owner)
            self._match_owner_particles(owner)

        document.setdefault("conflicts", []).extend(self._conflicts)
        stats = document.setdefault("stats", {})
        stats.update(
            {
                "owners_matched": sum(
                    (owner.get("match") or {}).get("status") == "matched" for owner in owners
                ),
                "owners_flattened_wrapper": sum(
                    (owner.get("match") or {}).get("status") == "flattened_wrapper" for owner in owners
                ),
                "owners_schema_only": sum(
                    (owner.get("match") or {}).get("status") == "schema_only" for owner in owners
                ),
                "owners_unmatched": sum(
                    (owner.get("match") or {}).get("status") not in {"matched", "flattened_wrapper", "schema_only"}
                    for owner in owners
                ),
                "particle_matches": sum(
                    match.get("status") == "matched" for match in self._particle_matches.values()
                ),
                "particle_conflicts": sum(
                    match.get("status") in {"ambiguous", "not_found"}
                    for match in self._particle_matches.values()
                ),
                "matching_conflicts": len(self._conflicts),
            }
        )
        return document

    def _index_metadata(self) -> None:
        for section in ("groups", "complexTypes", "extract_inner_class", "simpleTypes"):
            values = self.metadata.get(section) or {}
            if not isinstance(values, dict):
                continue
            for key, record in values.items():
                if not isinstance(record, dict):
                    continue
                name = str(record.get("name") or key)
                entity_id = str(record.get("iri") or f"{self.domain}:{self.version}/{_slug(name)}")
                target = MetadataTarget(section, str(key), record, entity_id)
                self._targets[section].append(target)
                self._target_by_identity[(section, str(key))] = target

    def _match_named_owner(self, owner: dict[str, Any]) -> None:
        raw_name = str(owner.get("name") or "")
        pascal_name = to_pascal_case(raw_name)
        kind = owner.get("owner_kind")
        sections = ("groups",) if kind == "group" else ("groups", "complexTypes")

        target: MetadataTarget | None = None
        candidates_public: list[dict[str, Any]] = []
        for section in sections:
            candidates = self._best_named_candidates(section, raw_name, pascal_name, owner)
            candidates_public.extend(item.public() for item in candidates)
            if len(candidates) == 1:
                target = candidates[0]
                break
            if len(candidates) > 1:
                break

        if target is None:
            if self._match_schema_only_simple_content(owner):
                return
            status = "ambiguous" if len(candidates_public) > 1 else "not_found"
            owner["match"] = {"status": status, "candidates": candidates_public}
            self._conflicts.append(
                {
                    "category": "owner_ambiguous" if status == "ambiguous" else "owner_not_found",
                    "owner_id": owner.get("owner_id"),
                    "owner_kind": kind,
                    "name": raw_name,
                    "candidates": candidates_public,
                }
            )
            return

        self._set_owner_target(owner, target, mode="direct")

    def _match_schema_only_simple_content(self, owner: dict[str, Any]) -> bool:
        """Recognize an XSD custom scalar wrapper that has no metamodel class.

        The legacy metadata intentionally materializes the underlying simple
        type, not the generated ``complexType`` wrapper used to attach XML
        attributes. This audited schema-only declaration must have a
        simple-content model and resolve its base to exactly one simpleType.
        It is not attached to a Class node or treated as a particle parent.
        """

        if owner.get("owner_kind") != "complexType":
            return False
        model = owner.get("declared_model") or {}
        if model.get("content_kind") != "simple-content":
            return False
        raw_base = _qname_local(model.get("base_qname") or model.get("base"))
        if not raw_base:
            return False
        candidates = self._best_named_candidates(
            "simpleTypes",
            raw_base,
            to_pascal_case(raw_base),
            {"qualified_name": ""},
        )
        if len(candidates) != 1:
            return False
        target = candidates[0]
        owner["mapped_target"] = target.public()
        owner["match"] = {
            "status": "schema_only",
            "mode": "simple_content_wrapper",
            "base_simple_type": raw_base,
            "candidates": [target.public()],
        }
        return True

    def _best_named_candidates(
        self,
        section: str,
        raw_name: str,
        pascal_name: str,
        owner: dict[str, Any],
    ) -> list[MetadataTarget]:
        scored: list[tuple[int, MetadataTarget]] = []
        qualified_name = str(owner.get("qualified_name") or "")
        for target in self._targets.get(section, []):
            record = target.record
            score = 0
            if target.key == pascal_name:
                score += 80
            if str(record.get("name") or "") == pascal_name:
                score += 80
            if str(record.get("xml_tag") or "") == raw_name:
                score += 100
            if str(record.get("annotation") or "") == raw_name:
                score += 100
            if qualified_name and qualified_name in {
                str(record.get("document_name") or ""),
                str(record.get("qualifiedName") or ""),
            }:
                score += 20
            if score:
                scored.append((score, target))
        if not scored:
            return []
        maximum = max(score for score, _ in scored)
        return [target for score, target in scored if score == maximum]

    def _match_anonymous_owner(self, owner: dict[str, Any]) -> None:
        parent_owner_id = str(owner.get("parent_owner_id") or "")
        parent_path = str(owner.get("parent_particle_path") or "")
        parent_target = self._owner_targets.get(parent_owner_id)
        parent_match = self._particle_matches.get((parent_owner_id, parent_path))

        if not parent_target:
            owner["match"] = {"status": "parent_not_found", "candidates": []}
            self._conflicts.append(
                {
                    "category": "inner_parent_not_found",
                    "owner_id": owner.get("owner_id"),
                    "parent_owner_id": parent_owner_id,
                }
            )
            return

        if parent_match and parent_match.get("status") == "flattened_wrapper":
            self._set_owner_target(owner, parent_target, mode="flattened_wrapper")
            owner["match"]["status"] = "flattened_wrapper"
            owner["match"]["wrapper_name"] = owner.get("element_name")
            return

        attribute: AttributeTarget | None = None
        if parent_match and parent_match.get("status") == "matched":
            attribute = self._attribute_objects.get(str(parent_match.get("target_id")))

        if attribute is None:
            # A wrapper element is intentionally flattened by the legacy parser.
            wrappers = [
                item
                for item in self._attributes_for(parent_target)
                if item.record.get("xml_wrapper_tag") == owner.get("element_name")
            ]
            if wrappers:
                self._set_owner_target(owner, parent_target, mode="flattened_wrapper")
                owner["match"]["status"] = "flattened_wrapper"
                owner["match"]["wrapper_name"] = owner.get("element_name")
                owner["match"]["wrapper_fields"] = [item.public() for item in wrappers]
                return

        declared_type = _strip_collection(attribute.record.get("type") if attribute else None)
        if not declared_type:
            owner["match"] = {"status": "not_found", "candidates": []}
            self._conflicts.append(
                {
                    "category": "inner_owner_not_materialized",
                    "owner_id": owner.get("owner_id"),
                    "parent_owner_id": parent_owner_id,
                    "parent_particle_path": parent_path,
                }
            )
            return

        candidates = [
            target
            for target in self._targets.get("extract_inner_class", [])
            if target.key == declared_type or str(target.record.get("name") or "") == declared_type
        ]
        if len(candidates) != 1:
            owner["match"] = {
                "status": "ambiguous" if candidates else "not_found",
                "declared_parent_type": declared_type,
                "candidates": [item.public() for item in candidates],
            }
            self._conflicts.append(
                {
                    "category": "inner_owner_ambiguous" if candidates else "inner_owner_not_found",
                    "owner_id": owner.get("owner_id"),
                    "parent_owner_id": parent_owner_id,
                    "declared_parent_type": declared_type,
                    "candidates": [item.public() for item in candidates],
                }
            )
            return

        self._set_owner_target(owner, candidates[0], mode="parent_declared_type")
        owner["match"]["parent_attribute"] = attribute.public() if attribute else None

    def _set_owner_target(self, owner: dict[str, Any], target: MetadataTarget, *, mode: str) -> None:
        owner_id = str(owner["owner_id"])
        owner["mapped_target"] = target.public()
        owner["match"] = {"status": "matched", "mode": mode, "candidates": [target.public()]}
        self._owner_targets[owner_id] = target
        self._owner_modes[owner_id] = mode

    def _match_owner_particles(self, owner: dict[str, Any]) -> None:
        owner_id = str(owner.get("owner_id") or "")
        target = self._owner_targets.get(owner_id)
        if target is None:
            return
        for particle in XsdContentModelExtractor.iter_particles(owner.get("declared_model")):
            kind = particle.get("kind")
            if kind == "element":
                match = self._match_element_particle(owner, target, particle)
            elif kind == "group-ref":
                match = self._match_group_ref(particle)
            else:
                continue
            particle["match"] = match
            self._particle_matches[(owner_id, str(particle.get("path") or ""))] = match

    def _match_element_particle(
        self,
        owner: dict[str, Any],
        target: MetadataTarget,
        particle: dict[str, Any],
    ) -> dict[str, Any]:
        element_name = str(particle.get("element_name") or "")
        attributes = self._attributes_for(target)
        owner_mode = self._owner_modes.get(str(owner.get("owner_id")), "direct")
        expected_wrapper = str(owner.get("element_name") or "") if owner_mode == "flattened_wrapper" else ""
        declared_type = to_pascal_case(_qname_local(particle.get("type_qname") or particle.get("type")))
        expected_field_name = to_camel_case(element_name)

        scored: list[tuple[int, AttributeTarget]] = []
        for attribute in attributes:
            record = attribute.record
            if record.get("is_xml_attribute") is True:
                continue
            xml_tag = str(record.get("xml_tag") or "")
            wrapper = str(record.get("xml_wrapper_tag") or "")
            if xml_tag != element_name:
                continue
            score = 100
            if expected_wrapper:
                if wrapper != expected_wrapper:
                    continue
                score += 80
            elif not wrapper:
                score += 10
            if declared_type and _strip_collection(record.get("type")) == declared_type:
                score += 30
            if str(record.get("name") or "") == expected_field_name:
                score += 10
            scored.append((score, attribute))

        if scored:
            maximum = max(score for score, _ in scored)
            best = [attribute for score, attribute in scored if score == maximum]
            if len(best) == 1:
                public = best[0].public()
                self._attribute_objects[best[0].target_id] = best[0]
                return {"status": "matched", **public}
            match = {"status": "ambiguous", "candidates": [item.public() for item in best]}
            self._conflicts.append(
                {
                    "category": "particle_ambiguous",
                    "owner_id": owner.get("owner_id"),
                    "particle_id": particle.get("particle_id"),
                    "element_name": element_name,
                    "candidates": match["candidates"],
                }
            )
            return match

        # An outer inline element may exist only as xml_wrapper_tag in the
        # flattened metadata. It is a container, not a unique Attribute.
        wrapper_fields = [
            attribute for attribute in attributes if attribute.record.get("xml_wrapper_tag") == element_name
        ]
        if particle.get("anonymous_owner_id") and wrapper_fields:
            return {
                "status": "flattened_wrapper",
                "wrapper_name": element_name,
                "candidates": [item.public() for item in wrapper_fields],
            }

        typed_model_match = self._match_typed_model_particle(particle)
        if typed_model_match is not None:
            if typed_model_match.get("status") == "ambiguous":
                self._conflicts.append({
                    "category": "particle_type_ambiguous",
                    "owner_id": owner.get("owner_id"),
                    "particle_id": particle.get("particle_id"),
                    "element_name": element_name,
                    "candidates": typed_model_match["candidates"],
                })
            return typed_model_match

        match = {"status": "not_found", "candidates": []}
        self._conflicts.append(
            {
                "category": "particle_not_found",
                "owner_id": owner.get("owner_id"),
                "particle_id": particle.get("particle_id"),
                "element_name": element_name,
                "container_path": particle.get("container_path"),
            }
        )
        return match

    def _match_typed_model_particle(self, particle: dict[str, Any]) -> dict[str, Any] | None:
        """Match a typed child omitted by the legacy flattened parent record.

        AUTOSAR uses typed elements inside choices (for example
        ``SW-AXIS-GROUPED``). The old parser materializes the child model as
        its own Entity but does not retain a synthetic field on the parent.
        Exact element/type equality and a unique model lookup make this safe.
        """

        element_name = str(particle.get("element_name") or "")
        raw_type = _qname_local(particle.get("type_qname") or particle.get("type"))
        if not element_name or raw_type != element_name:
            return None
        pascal_name = to_pascal_case(raw_type)
        for section in ("groups", "complexTypes"):
            candidates = self._best_named_candidates(
                section,
                raw_type,
                pascal_name,
                {"qualified_name": ""},
            )
            if len(candidates) == 1:
                return {
                    "status": "matched",
                    "mode": "typed_model_element",
                    "declared_type": raw_type,
                    "model_target": candidates[0].public(),
                }
            if len(candidates) > 1:
                return {
                    "status": "ambiguous",
                    "mode": "typed_model_element",
                    "declared_type": raw_type,
                    "candidates": [item.public() for item in candidates],
                }
        return None

    def _match_group_ref(self, particle: dict[str, Any]) -> dict[str, Any]:
        raw_name = _qname_local(particle.get("ref_qname") or particle.get("ref"))
        pascal_name = to_pascal_case(raw_name)
        candidates = self._best_named_candidates(
            "groups",
            raw_name,
            pascal_name,
            {"qualified_name": ""},
        )
        if len(candidates) == 1:
            return {"status": "matched", **candidates[0].public()}
        status = "ambiguous" if candidates else "not_found"
        result = {"status": status, "candidates": [item.public() for item in candidates]}
        self._conflicts.append(
            {
                "category": "group_ref_ambiguous" if candidates else "group_ref_not_found",
                "particle_id": particle.get("particle_id"),
                "ref": particle.get("ref"),
                "candidates": result["candidates"],
            }
        )
        return result

    @staticmethod
    def _attributes_for(target: MetadataTarget) -> list[AttributeTarget]:
        result: list[AttributeTarget] = []
        for field in ("attributes", "elements"):
            values = target.record.get(field) or []
            if not isinstance(values, list):
                continue
            for index, record in enumerate(values):
                if isinstance(record, dict):
                    result.append(AttributeTarget(target, field, index, record))
        return result


def build_enriched_metadata(
    metadata: dict[str, Any],
    matched_document: dict[str, Any],
    *,
    replace_existing: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return an enriched copy; never mutate or delete legacy metadata fields."""

    enriched = deepcopy(metadata)
    bundles: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    conflicts: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    source_hash = str((matched_document.get("source") or {}).get("sha256") or "")

    for owner in matched_document.get("owners") or []:
        match = owner.get("match") or {}
        target = owner.get("mapped_target") or {}
        if match.get("status") != "matched" or match.get("mode") == "flattened_wrapper":
            continue
        section, key = target.get("section"), target.get("key")
        if not section or not key:
            continue
        bundles[(str(section), str(key))].append(
            {
                "owner_id": owner.get("owner_id"),
                "owner_kind": owner.get("owner_kind"),
                "container_path": owner.get("container_path"),
                "declared_model": owner.get("declared_model"),
                "effective_model": owner.get("effective_model"),
                "declared_model_sha256": owner.get("declared_model_sha256"),
                "effective_model_sha256": owner.get("effective_model_sha256"),
            }
        )

    records_changed = 0
    fields_changed = 0
    records_noop = 0
    for (section, key), models in sorted(bundles.items()):
        record = (enriched.get(section) or {}).get(key)
        if not isinstance(record, dict):
            conflicts.append(
                {"category": "metadata_target_missing", "section": section, "key": key}
            )
            continue

        models.sort(key=lambda item: (str(item.get("owner_kind")), str(item.get("owner_id"))))
        groups = [item for item in models if item.get("owner_kind") == "group"]
        named_complex = [item for item in models if item.get("owner_kind") == "complexType"]
        anonymous = [item for item in models if item.get("owner_kind") == "anonymousComplexType"]

        # A named complex type is the outer declaration and therefore the
        # preferred effective model. Otherwise use a unique group/anonymous
        # model. Multiple anonymous contexts remain an explicit model list.
        preferred: dict[str, Any] | None = None
        if len(named_complex) == 1:
            preferred = named_complex[0]
        elif len(groups) == 1:
            preferred = groups[0]
        elif len(anonymous) == 1:
            preferred = anonymous[0]

        updates: dict[str, Any] = {
            "xsd_content_models_json": canonical_json(models),
            "xsd_owner_ids_json": canonical_json([item["owner_id"] for item in models]),
            "xsd_source_sha256": source_hash,
            "xsd_model_sha256": semantic_hash(models),
            "xsd_model_version": str(matched_document.get("format_version", 1)),
        }
        if len(groups) == 1:
            updates["xsd_group_model_json"] = canonical_json(groups[0]["declared_model"])
        if len(named_complex) == 1:
            updates["xsd_complex_type_model_json"] = canonical_json(named_complex[0]["declared_model"])
        elif len(anonymous) == 1:
            updates["xsd_complex_type_model_json"] = canonical_json(anonymous[0]["declared_model"])
        if preferred is not None:
            updates["xsd_effective_model_json"] = canonical_json(preferred["effective_model"])
        elif len(anonymous) > 1:
            warnings.append(
                {
                    "category": "class_multiple_context_models",
                    "section": section,
                    "key": key,
                    "owner_ids": [item["owner_id"] for item in anonymous],
                }
            )

        changed_here = 0
        for field, value in updates.items():
            existing = record.get(field)
            if existing in (None, ""):
                record[field] = value
                changed_here += 1
            elif existing == value:
                continue
            elif replace_existing:
                record[field] = value
                changed_here += 1
            else:
                conflicts.append(
                    {
                        "category": "existing_xsd_field_conflict",
                        "section": section,
                        "key": key,
                        "field": field,
                    }
                )
        if changed_here:
            records_changed += 1
            fields_changed += changed_here
        else:
            records_noop += 1

    report = {
        "targets_with_models": len(bundles),
        "records_changed": records_changed,
        "fields_changed": fields_changed,
        "records_noop": records_noop,
        "conflicts": conflicts,
        "conflict_count": len(conflicts),
        "warnings": warnings,
        "warning_count": len(warnings),
    }
    return enriched, report


def metadata_sha256(metadata: dict[str, Any]) -> str:
    return sha256(canonical_json(metadata).encode("utf-8")).hexdigest()

