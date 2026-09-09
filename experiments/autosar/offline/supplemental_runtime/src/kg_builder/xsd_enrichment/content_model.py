"""Extract an XSD content model without flattening compositor structure.

The legacy AUTOSAR parser turns ``sequence``/``choice``/``group`` particles
into flat attribute lists.  This module deliberately runs beside that parser:
it keeps occurrence identity, the complete parent-container path, and stable
particle paths that can be matched back to the existing metadata.
"""

from __future__ import annotations

import json
import re
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from typing import Any, Iterable

from lxml import etree

XSD_NS = "http://www.w3.org/2001/XMLSchema"
XS = f"{{{XSD_NS}}}"
PARTICLE_KINDS = {"sequence", "choice", "all", "element", "group", "any"}
COMPOSITOR_KINDS = {"sequence", "choice", "all"}
_QUALIFIED_NAME_RE = re.compile(r'mmt\.qualifiedName\s*=\s*"([^"]+)"')


def canonical_json(value: Any) -> str:
    """Return the canonical JSON representation used for hashes/idempotency."""

    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def semantic_hash(value: Any) -> str:
    """Hash semantic model data while ignoring source-line diagnostics."""

    def clean(item: Any) -> Any:
        if isinstance(item, dict):
            return {
                key: clean(val)
                for key, val in item.items()
                if key not in {"source_line", "mapped_target", "match"}
            }
        if isinstance(item, list):
            return [clean(val) for val in item]
        return item

    return sha256(canonical_json(clean(value)).encode("utf-8")).hexdigest()


def _local_name(node: etree._Element) -> str:
    # Comments and processing instructions can appear between declarations.
    if not isinstance(node.tag, str):
        return ""
    return etree.QName(node).localname


def _occurs(node: etree._Element) -> tuple[int, int | str]:
    min_raw = node.get("minOccurs", "1")
    max_raw = node.get("maxOccurs", "1")
    try:
        min_value = int(min_raw)
    except (TypeError, ValueError):
        min_value = 1
    if max_raw == "unbounded":
        max_value: int | str = "unbounded"
    else:
        try:
            max_value = int(max_raw)
        except (TypeError, ValueError):
            max_value = 1
    return min_value, max_value


class XsdContentModelExtractor:
    """Build a deterministic, parent-aware content model from one XSD file."""

    format_version = 1

    def __init__(self, xsd_path: str | Path) -> None:
        self.xsd_path = Path(xsd_path).resolve()
        self._owners: list[dict[str, Any]] = []
        self._owners_by_id: dict[str, dict[str, Any]] = {}
        self._group_by_local_name: dict[str, str] = {}
        self._complex_by_local_name: dict[str, str] = {}
        self._conflicts: list[dict[str, Any]] = []
        self._target_namespace = ""

    def extract(self) -> dict[str, Any]:
        if not self.xsd_path.is_file():
            raise FileNotFoundError(f"XSD file does not exist: {self.xsd_path}")

        parser = etree.XMLParser(remove_blank_text=False, resolve_entities=False, huge_tree=True)
        root = etree.parse(str(self.xsd_path), parser).getroot()
        if _local_name(root) != "schema":
            raise ValueError(f"Expected an XML Schema root, got {_local_name(root)!r}")
        self._target_namespace = root.get("targetNamespace", "")

        # Register named declarations first so forward group/base references resolve.
        named_nodes: list[tuple[str, etree._Element, dict[str, Any]]] = []
        for node in root:
            kind = _local_name(node)
            if kind not in {"group", "complexType"} or not node.get("name"):
                continue
            owner = self._new_named_owner(kind, node)
            named_nodes.append((kind, node, owner))

        # Parse models in document order. Anonymous complex types are registered
        # recursively and retain the path of the element that owns them.
        for _, node, owner in named_nodes:
            owner["declared_model"] = self._extract_container_model(
                node,
                owner=owner,
                base_path="",
                container_path=list(owner["container_path"]),
            )

        for owner in self._owners:
            owner["effective_model"] = self._resolve_model(
                owner.get("declared_model"),
                resolving=(owner["owner_id"],),
            )
            owner["declared_model_sha256"] = semantic_hash(owner.get("declared_model"))
            owner["effective_model_sha256"] = semantic_hash(owner.get("effective_model"))

        stats = self._stats()
        source_hash = sha256_file(self.xsd_path)
        document: dict[str, Any] = {
            "format_version": self.format_version,
            "source": {
                "path": str(self.xsd_path),
                "sha256": source_hash,
                "target_namespace": self._target_namespace,
                "schema_version": root.get("version", ""),
            },
            "owners": self._owners,
            "conflicts": self._conflicts,
            "stats": stats,
        }
        document["model_sha256"] = semantic_hash(
            [{"owner_id": item["owner_id"], "model": item["declared_model"]} for item in self._owners]
        )
        return document

    def _new_named_owner(self, kind: str, node: etree._Element) -> dict[str, Any]:
        name = node.get("name", "")
        owner_kind = "group" if kind == "group" else "complexType"
        qname = self._expanded_target_name(name)
        owner_id = f"xsd:{self._target_namespace}:{owner_kind}:{name}"
        owner = {
            "owner_id": owner_id,
            "owner_kind": owner_kind,
            "qname": qname,
            "name": name,
            "qualified_name": self._annotation_qualified_name(node),
            "parent_owner_id": None,
            "parent_particle_path": None,
            "container_path": [f"{owner_kind}:{qname}"],
            "source_line": node.sourceline,
            "declared_model": None,
            "effective_model": None,
        }
        self._register_owner(owner)
        if owner_kind == "group":
            self._group_by_local_name[name] = owner_id
        else:
            self._complex_by_local_name[name] = owner_id
        return owner

    def _new_anonymous_owner(
        self,
        complex_type: etree._Element,
        *,
        parent_owner: dict[str, Any],
        parent_particle_path: str,
        element_name: str,
        container_path: list[str],
    ) -> dict[str, Any]:
        identity = f"{parent_owner['owner_id']}|{parent_particle_path}|anonymous-complex-type"
        suffix = sha256(identity.encode("utf-8")).hexdigest()[:24]
        owner_id = f"xsd:{self._target_namespace}:anonymousComplexType:{suffix}"
        owner = {
            "owner_id": owner_id,
            "owner_kind": "anonymousComplexType",
            "qname": None,
            "name": None,
            "element_name": element_name,
            "class_name_hint": self._pascal_case(element_name),
            "qualified_name": self._annotation_qualified_name(complex_type),
            "parent_owner_id": parent_owner["owner_id"],
            "parent_particle_path": parent_particle_path,
            "container_path": container_path,
            "source_line": complex_type.sourceline,
            "declared_model": None,
            "effective_model": None,
        }
        self._register_owner(owner)
        owner["declared_model"] = self._extract_container_model(
            complex_type,
            owner=owner,
            base_path="",
            container_path=container_path,
        )
        return owner

    def _register_owner(self, owner: dict[str, Any]) -> None:
        owner_id = owner["owner_id"]
        if owner_id in self._owners_by_id:
            raise ValueError(f"Duplicate XSD owner identity: {owner_id}")
        self._owners.append(owner)
        self._owners_by_id[owner_id] = owner

    def _extract_container_model(
        self,
        container: etree._Element,
        *,
        owner: dict[str, Any],
        base_path: str,
        container_path: list[str],
    ) -> dict[str, Any] | None:
        for child in container:
            if _local_name(child) in COMPOSITOR_KINDS:
                return self._parse_particle(
                    child,
                    owner=owner,
                    path=self._join_path(base_path, f"{_local_name(child)}[0]"),
                    position=0,
                    container_path=container_path,
                )

        complex_content = container.find(f"./{XS}complexContent")
        if complex_content is not None:
            extension = complex_content.find(f"./{XS}extension")
            if extension is None:
                extension = complex_content.find(f"./{XS}restriction")
            if extension is not None:
                return self._parse_derivation(
                    extension,
                    owner=owner,
                    base_path=base_path,
                    container_path=container_path,
                    content_kind="complex-content",
                )

        simple_content = container.find(f"./{XS}simpleContent")
        if simple_content is not None:
            extension = simple_content.find(f"./{XS}extension")
            if extension is None:
                extension = simple_content.find(f"./{XS}restriction")
            if extension is not None:
                return self._parse_derivation(
                    extension,
                    owner=owner,
                    base_path=base_path,
                    container_path=container_path,
                    content_kind="simple-content",
                )
        return None

    def _parse_derivation(
        self,
        node: etree._Element,
        *,
        owner: dict[str, Any],
        base_path: str,
        container_path: list[str],
        content_kind: str,
    ) -> dict[str, Any]:
        derivation_kind = _local_name(node)
        path = self._join_path(base_path, f"{content_kind}[0]/{derivation_kind}[0]")
        result: dict[str, Any] = {
            "particle_id": self._particle_id(owner["owner_id"], path),
            "kind": derivation_kind,
            "content_kind": content_kind,
            "path": path,
            "position": 0,
            "container_path": container_path,
            "source_line": node.sourceline,
            "base": node.get("base"),
            "base_qname": self._expand_qname(node.get("base"), node),
            "children": [],
        }
        for child in node:
            if _local_name(child) in COMPOSITOR_KINDS:
                result["children"].append(
                    self._parse_particle(
                        child,
                        owner=owner,
                        path=self._join_path(path, f"{_local_name(child)}[0]"),
                        position=0,
                        container_path=container_path,
                    )
                )
        return result

    def _parse_particle(
        self,
        node: etree._Element,
        *,
        owner: dict[str, Any],
        path: str,
        position: int,
        container_path: list[str],
    ) -> dict[str, Any]:
        raw_kind = _local_name(node)
        kind = "group-ref" if raw_kind == "group" else raw_kind
        min_occurs, max_occurs = _occurs(node)
        particle: dict[str, Any] = {
            "particle_id": self._particle_id(owner["owner_id"], path),
            "kind": kind,
            "path": path,
            "position": position,
            "container_path": list(container_path),
            "min_occurs": min_occurs,
            "max_occurs": max_occurs,
            "source_line": node.sourceline,
        }

        if raw_kind in COMPOSITOR_KINDS:
            particle["children"] = []
            child_position = 0
            for child in node:
                child_kind = _local_name(child)
                if child_kind not in PARTICLE_KINDS:
                    continue
                child_path = self._join_path(path, f"{child_kind}[{child_position}]")
                particle["children"].append(
                    self._parse_particle(
                        child,
                        owner=owner,
                        path=child_path,
                        position=child_position,
                        container_path=container_path,
                    )
                )
                child_position += 1
            return particle

        if raw_kind == "element":
            raw_name = node.get("name")
            raw_ref = node.get("ref")
            element_name = raw_name or self._qname_local(raw_ref) or ""
            particle.update(
                {
                    "name": raw_name,
                    "ref": raw_ref,
                    "ref_qname": self._expand_qname(raw_ref, node),
                    "element_name": element_name,
                    "type": node.get("type"),
                    "type_qname": self._expand_qname(node.get("type"), node),
                    "nillable": node.get("nillable", "false").lower() == "true",
                }
            )
            inline_complex = node.find(f"./{XS}complexType")
            if inline_complex is not None:
                element_segment = f"element:{element_name}@{path}"
                anonymous = self._new_anonymous_owner(
                    inline_complex,
                    parent_owner=owner,
                    parent_particle_path=path,
                    element_name=element_name,
                    container_path=[*container_path, element_segment],
                )
                particle["anonymous_owner_id"] = anonymous["owner_id"]
            return particle

        if raw_kind == "group":
            ref = node.get("ref")
            particle.update({"ref": ref, "ref_qname": self._expand_qname(ref, node)})
            return particle

        if raw_kind == "any":
            particle.update(
                {
                    "namespace": node.get("namespace", "##any"),
                    "process_contents": node.get("processContents", "strict"),
                }
            )
        return particle

    def _resolve_model(
        self,
        model: dict[str, Any] | None,
        *,
        resolving: tuple[str, ...],
    ) -> dict[str, Any] | None:
        if model is None:
            return None
        result = deepcopy(model)
        kind = result.get("kind")

        if kind == "group-ref":
            local = self._qname_local(result.get("ref"))
            target_id = self._group_by_local_name.get(local or "")
            if not target_id:
                self._conflicts.append(
                    {
                        "category": "group_target_not_found",
                        "particle_id": result.get("particle_id"),
                        "ref": result.get("ref"),
                    }
                )
                return result
            result["resolved_owner_id"] = target_id
            if target_id in resolving:
                self._conflicts.append(
                    {
                        "category": "group_cycle",
                        "particle_id": result.get("particle_id"),
                        "cycle": [*resolving, target_id],
                    }
                )
                return result
            target = self._owners_by_id[target_id]
            expanded = self._resolve_model(
                target.get("declared_model"),
                resolving=(*resolving, target_id),
            )
            if expanded is not None:
                result["children"] = [expanded]
            return result

        if kind in {"extension", "restriction"} and result.get("content_kind") == "complex-content":
            local = self._qname_local(result.get("base"))
            target_id = self._complex_by_local_name.get(local or "")
            if target_id:
                result["resolved_base_owner_id"] = target_id
                if target_id in resolving:
                    self._conflicts.append(
                        {
                            "category": "base_type_cycle",
                            "particle_id": result.get("particle_id"),
                            "cycle": [*resolving, target_id],
                        }
                    )
                else:
                    target = self._owners_by_id[target_id]
                    expanded = self._resolve_model(
                        target.get("declared_model"),
                        resolving=(*resolving, target_id),
                    )
                    if expanded is not None:
                        result["base_model"] = expanded

        if isinstance(result.get("children"), list):
            result["children"] = [
                self._resolve_model(child, resolving=resolving)
                for child in result["children"]
            ]
        return result

    def _stats(self) -> dict[str, int]:
        particle_counts: dict[str, int] = {}
        for owner in self._owners:
            for particle in self.iter_particles(owner.get("declared_model")):
                kind = str(particle.get("kind"))
                particle_counts[kind] = particle_counts.get(kind, 0) + 1
        return {
            "owners": len(self._owners),
            "groups": sum(owner["owner_kind"] == "group" for owner in self._owners),
            "complex_types": sum(owner["owner_kind"] == "complexType" for owner in self._owners),
            "anonymous_complex_types": sum(
                owner["owner_kind"] == "anonymousComplexType" for owner in self._owners
            ),
            "particles": sum(particle_counts.values()),
            **{f"particles_{key.replace('-', '_')}": value for key, value in sorted(particle_counts.items())},
        }

    @staticmethod
    def iter_particles(model: dict[str, Any] | None) -> Iterable[dict[str, Any]]:
        if not isinstance(model, dict):
            return
        yield model
        for child in model.get("children") or []:
            yield from XsdContentModelExtractor.iter_particles(child)
        base_model = model.get("base_model")
        if isinstance(base_model, dict):
            yield from XsdContentModelExtractor.iter_particles(base_model)

    def _expanded_target_name(self, local: str) -> str:
        return f"{{{self._target_namespace}}}{local}" if self._target_namespace else local

    @staticmethod
    def _annotation_qualified_name(node: etree._Element) -> str:
        for appinfo in node.findall(f"./{XS}annotation/{XS}appinfo"):
            if appinfo.get("source") != "tags" or not appinfo.text:
                continue
            match = _QUALIFIED_NAME_RE.search(appinfo.text)
            if match:
                return match.group(1)
        return ""

    @staticmethod
    def _pascal_case(value: str) -> str:
        return "".join(part.capitalize() for part in re.split(r"[-_]", value))

    @staticmethod
    def _qname_local(value: str | None) -> str | None:
        if not value:
            return None
        if value.startswith("{") and "}" in value:
            return value.split("}", 1)[1]
        return value.split(":", 1)[-1]

    @staticmethod
    def _expand_qname(value: str | None, node: etree._Element) -> str | None:
        if not value:
            return None
        if value.startswith("{"):
            return value
        if ":" in value:
            prefix, local = value.split(":", 1)
            namespace = node.nsmap.get(prefix)
            return f"{{{namespace}}}{local}" if namespace else value
        default_namespace = node.nsmap.get(None)
        return f"{{{default_namespace}}}{value}" if default_namespace else value

    @staticmethod
    def _join_path(parent: str, child: str) -> str:
        return f"{parent}/{child}" if parent else child

    @staticmethod
    def _particle_id(owner_id: str, path: str) -> str:
        suffix = sha256(f"{owner_id}|{path}".encode("utf-8")).hexdigest()[:24]
        return f"xsd-particle:{suffix}"

