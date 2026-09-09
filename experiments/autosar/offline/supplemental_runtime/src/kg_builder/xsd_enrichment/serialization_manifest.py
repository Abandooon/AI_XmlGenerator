"""Compile and verify the deterministic XML serialization contract.

The provider-facing JSON Schema is intentionally not used as an XML ordering
contract.  This module compiles the parent-aware XSD model extracted by
``XsdContentModelExtractor`` into a compact, hash-pinned build artifact that is
required by generation and validation.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from lxml import etree

from .content_model import XSD_NS, XsdContentModelExtractor, canonical_json, sha256_file

SCHEMA_VERSION = "1.0"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
XS = f"{{{XSD_NS}}}"


class XsdSerializationManifestError(ValueError):
    """Raised when the deterministic XSD serialization contract is unusable."""


def _fingerprint(payload: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def _local_name(value: object) -> str:
    text = str(value or "")
    if text.startswith("{") and "}" in text:
        return text.split("}", 1)[1]
    return text.split(":", 1)[-1]


def _expand_qname(value: str | None, node: etree._Element) -> str | None:
    if not value:
        return None
    if value.startswith("{"):
        return value
    if ":" in value:
        prefix, local = value.split(":", 1)
        namespace = node.nsmap.get(prefix)
        return f"{{{namespace}}}{local}" if namespace else value
    namespace = node.nsmap.get(None)
    return f"{{{namespace}}}{value}" if namespace else value


def _unique_index(
    owners: list[dict[str, Any]], owner_kind: str
) -> dict[str, str]:
    index: dict[str, str] = {}
    for owner in owners:
        if owner.get("owner_kind") != owner_kind or not owner.get("name"):
            continue
        key = str(owner["name"]).strip().upper()
        owner_id = str(owner["owner_id"])
        previous = index.get(key)
        if previous and previous != owner_id:
            raise XsdSerializationManifestError(
                f"duplicate {owner_kind} local name {key!r}: {previous}, {owner_id}"
            )
        index[key] = owner_id
    return index


def _compact_particle(
    node: dict[str, Any] | None,
    *,
    group_index: dict[str, str],
    complex_type_index: dict[str, str],
) -> dict[str, Any] | None:
    if not isinstance(node, dict):
        return None
    keys = (
        "particle_id",
        "kind",
        "path",
        "position",
        "container_path",
        "source_line",
        "min_occurs",
        "max_occurs",
        "content_kind",
        "element_name",
        "name",
        "ref_qname",
        "type_qname",
        "anonymous_owner_id",
        "nillable",
        "namespace",
        "process_contents",
        "base_qname",
    )
    result = {key: node[key] for key in keys if key in node and node[key] is not None}
    kind = str(node.get("kind") or "")
    if kind == "group-ref":
        target = group_index.get(_local_name(node.get("ref_qname") or node.get("ref")).upper())
        if not target:
            raise XsdSerializationManifestError(
                f"unresolved group reference in particle {node.get('particle_id')}: {node.get('ref')}"
            )
        result["resolved_owner_id"] = target
    if kind in {"extension", "restriction"} and node.get("content_kind") == "complex-content":
        target = complex_type_index.get(
            _local_name(node.get("base_qname") or node.get("base")).upper()
        )
        if not target:
            raise XsdSerializationManifestError(
                f"unresolved complex base in particle {node.get('particle_id')}: {node.get('base')}"
            )
        result["resolved_base_owner_id"] = target
    children = [
        _compact_particle(
            child,
            group_index=group_index,
            complex_type_index=complex_type_index,
        )
        for child in node.get("children") or []
    ]
    children = [child for child in children if child is not None]
    if children:
        result["children"] = children
    return result


def _global_elements(xsd_path: Path) -> dict[str, dict[str, Any]]:
    parser = etree.XMLParser(remove_blank_text=False, resolve_entities=False, huge_tree=True)
    root = etree.parse(str(xsd_path), parser).getroot()
    result: dict[str, dict[str, Any]] = {}
    for node in root.findall(f"./{XS}element"):
        name = str(node.get("name") or "").strip()
        if not name:
            continue
        key = name.upper()
        record = {
            "element_name": name,
            "type_qname": _expand_qname(node.get("type"), node),
            "source_line": node.sourceline,
        }
        previous = result.get(key)
        if previous and previous != record:
            raise XsdSerializationManifestError(f"duplicate global element {name!r}")
        result[key] = record
    return result


def build_serialization_manifest(
    xsd_path: str | Path,
    *,
    content_document: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compile one deterministic, context-aware serialization manifest."""
    xsd_path = Path(xsd_path).resolve()
    document = content_document or XsdContentModelExtractor(xsd_path).extract()
    conflicts = document.get("conflicts") or []
    if conflicts:
        raise XsdSerializationManifestError(
            f"XSD content model has {len(conflicts)} unresolved conflicts"
        )
    source = document.get("source") or {}
    actual_xsd_sha256 = sha256_file(xsd_path)
    if str(source.get("sha256") or "") != actual_xsd_sha256:
        raise XsdSerializationManifestError("content-model XSD hash does not match the source file")

    raw_owners = [item for item in document.get("owners") or [] if isinstance(item, dict)]
    group_index = _unique_index(raw_owners, "group")
    complex_type_index = _unique_index(raw_owners, "complexType")
    owners: dict[str, dict[str, Any]] = {}
    for owner in sorted(raw_owners, key=lambda item: str(item.get("owner_id") or "")):
        owner_id = str(owner.get("owner_id") or "")
        if not owner_id or owner_id in owners:
            raise XsdSerializationManifestError(f"invalid or duplicate owner id {owner_id!r}")
        record = {
            key: owner.get(key)
            for key in (
                "owner_id",
                "owner_kind",
                "qname",
                "name",
                "element_name",
                "parent_owner_id",
                "parent_particle_path",
                "container_path",
                "source_line",
                "declared_model_sha256",
            )
            if owner.get(key) is not None
        }
        record["model"] = _compact_particle(
            owner.get("declared_model"),
            group_index=group_index,
            complex_type_index=complex_type_index,
        )
        owners[owner_id] = record

    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": "xsd_serialization_manifest",
        "xsd": {
            "sha256": actual_xsd_sha256,
            "target_namespace": str(source.get("target_namespace") or ""),
            "schema_version": str(source.get("schema_version") or ""),
        },
        "content_model_sha256": str(document.get("model_sha256") or ""),
        "owners": owners,
        "named_complex_types": dict(sorted(complex_type_index.items())),
        "global_elements": dict(sorted(_global_elements(xsd_path).items())),
        "stats": {
            "owners": len(owners),
            "named_complex_types": len(complex_type_index),
            "global_elements": len(_global_elements(xsd_path)),
        },
    }
    if not SHA256.fullmatch(manifest["content_model_sha256"]):
        raise XsdSerializationManifestError("content-model semantic SHA-256 is missing or invalid")
    manifest["manifest_sha256"] = _fingerprint(manifest)
    return manifest


def load_serialization_manifest(
    manifest_path: str | Path,
    *,
    xsd_path: str | Path,
) -> dict[str, Any]:
    """Load the contract and fail closed on every missing or conflicting hash."""
    manifest_path = Path(manifest_path).resolve()
    xsd_path = Path(xsd_path).resolve()
    if not manifest_path.is_file():
        raise XsdSerializationManifestError(
            f"XSD serialization manifest not found: {manifest_path}"
        )
    if not xsd_path.is_file():
        raise XsdSerializationManifestError(f"XSD source not found: {xsd_path}")
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as error:
        raise XsdSerializationManifestError(
            f"cannot read XSD serialization manifest: {error}"
        ) from error
    if not isinstance(payload, dict) or payload.get("schema_version") != SCHEMA_VERSION:
        raise XsdSerializationManifestError("unsupported XSD serialization manifest schema_version")
    declared = str(payload.get("manifest_sha256") or "")
    body = dict(payload)
    body.pop("manifest_sha256", None)
    if not SHA256.fullmatch(declared) or declared != _fingerprint(body):
        raise XsdSerializationManifestError(
            "XSD serialization manifest fingerprint does not match its content"
        )
    expected_xsd_sha256 = str((payload.get("xsd") or {}).get("sha256") or "")
    if not SHA256.fullmatch(expected_xsd_sha256):
        raise XsdSerializationManifestError("manifest XSD SHA-256 is missing or invalid")
    if sha256_file(xsd_path) != expected_xsd_sha256:
        raise XsdSerializationManifestError(
            "runtime XSD hash does not match the serialization manifest"
        )
    if not isinstance(payload.get("owners"), dict) or not payload["owners"]:
        raise XsdSerializationManifestError("serialization manifest owner table is empty")
    if not isinstance(payload.get("named_complex_types"), dict):
        raise XsdSerializationManifestError("serialization manifest complex-type index is malformed")
    return payload
