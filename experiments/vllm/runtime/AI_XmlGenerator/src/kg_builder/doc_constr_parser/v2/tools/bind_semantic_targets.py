"""Resolve curated semantic targets to metamodel declarations and XML paths."""

from __future__ import annotations

import argparse
import json
from collections import deque
from pathlib import Path
from typing import Iterable

SCHEMA_VERSION = "2.0"


def ordered_unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def occurs(value: object) -> int | None:
    if value is None or value == "":
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed


class MetamodelIndex:
    def __init__(self, metadata: dict) -> None:
        self.metadata = metadata
        self.classes: dict[str, tuple[str, dict]] = {}
        for bucket in ("groups", "complexTypes", "extract_inner_class"):
            for name, value in metadata.get(bucket, {}).items():
                self.classes.setdefault(name, (bucket, value))

    def class_data(self, name: str) -> dict | None:
        found = self.classes.get(name)
        return found[1] if found else None

    def direct_parents(self, name: str) -> list[str]:
        data = self.class_data(name) or {}
        parents = data.get("generalization", []) or []
        return [item for item in parents if isinstance(item, str) and item]

    def lineage(self, name: str) -> list[str]:
        queue: deque[str] = deque([name])
        seen: set[str] = set()
        result: list[str] = []
        while queue:
            current = queue.popleft()
            if current in seen:
                continue
            seen.add(current)
            result.append(current)
            queue.extend(self.direct_parents(current))
        return result

    def concrete_variants(self, name: str) -> list[str]:
        data = self.class_data(name) or {}
        if str(data.get("abstract", "false")).lower() != "true":
            return [name]
        variants = [item for item in data.get("subTags", []) or [] if item in self.classes]
        return variants or [name]

    def class_xml_tags(self, name: str) -> list[str]:
        tags: list[str] = []
        for variant in self.concrete_variants(name):
            data = self.class_data(variant) or {}
            tag = data.get("xml_tag") or data.get("annotation")
            if isinstance(tag, str) and tag and not tag.startswith("@"):
                tags.append(tag)
        if not tags:
            data = self.class_data(name) or {}
            tag = data.get("xml_tag") or data.get("annotation")
            if isinstance(tag, str) and tag and not tag.startswith("@"):
                tags.append(tag)
        return ordered_unique(tags)

    def declarations(self, class_name: str, property_name: str) -> list[dict]:
        normalized = property_name.casefold()
        found: list[dict] = []
        for owner in self.lineage(class_name):
            data = self.class_data(owner) or {}
            for collection in ("elements", "attributes"):
                for item in data.get(collection, []) or []:
                    if not isinstance(item, dict):
                        continue
                    names = {
                        str(item.get("name") or "").casefold(),
                        str(item.get("qualifiedName") or "").casefold(),
                        str(item.get("document_name") or "").rsplit(".", 1)[-1].casefold(),
                    }
                    if normalized in names:
                        candidate = dict(item)
                        candidate["declared_owner"] = owner
                        candidate["collection"] = collection
                        found.append(candidate)

            if data.get("latestBindingTime"):
                content_name = f"{owner}Content"
                content = self.class_data(content_name) or {}
                for item in content.get("elements", []) or []:
                    if not isinstance(item, dict):
                        continue
                    names = {
                        str(item.get("name") or "").casefold(),
                        str(item.get("qualifiedName") or "").casefold(),
                        str(item.get("document_name") or "").rsplit(".", 1)[-1].casefold(),
                    }
                    if normalized in names:
                        candidate = dict(item)
                        candidate["declared_owner"] = owner
                        candidate["collection"] = "content_elements"
                        found.append(candidate)

        unique: dict[tuple, dict] = {}
        for item in found:
            key = (
                item.get("declared_owner"),
                item.get("qualifiedName") or item.get("name"),
                item.get("xml_tag"),
                item.get("xml_wrapper_tag"),
            )
            unique[key] = item
        return list(unique.values())

    def enum_values(self, type_name: str | None) -> list[str]:
        if not type_name:
            return []
        values: list[str] = []
        for bucket in ("simpleTypes", "complexTypes"):
            data = self.metadata.get(bucket, {}).get(type_name, {})
            for key in ("enumerations", "enumeration"):
                for item in data.get(key, []) or []:
                    if isinstance(item, str):
                        values.append(item)
                    elif isinstance(item, dict) and item.get("value") is not None:
                        values.append(str(item["value"]))
        return ordered_unique(values)


def path_variants(class_tags: list[str], declaration: dict | None) -> list[str]:
    if declaration is None:
        return class_tags
    property_tag = declaration.get("xml_tag")
    wrapper = declaration.get("xml_wrapper_tag")
    paths: list[str] = []
    for class_tag in class_tags:
        parts = [class_tag]
        if wrapper:
            parts.append(str(wrapper))
        if property_tag:
            parts.append(str(property_tag))
        paths.append("/".join(parts))
    return ordered_unique(paths)


def bind_target(index: MetamodelIndex, target_index: int, target: dict) -> dict:
    class_name = target.get("class_name")
    property_name = target.get("property_name")
    base = {
        "target_index": target_index,
        "role": target["role"],
        "class_name": class_name,
        "property_name": property_name,
        "evidence": target["evidence"],
        "binding_status": "unresolved",
        "declared_owner": None,
        "class_is_abstract": False,
        "class_xml_tags": [],
        "property_xml_tag": None,
        "xml_wrapper_tag": None,
        "path_variants": [],
        "type_name": None,
        "min_occurs": None,
        "max_occurs": None,
        "enum_values": [],
        "candidates": [],
        "issues": [],
    }
    if class_name is None:
        base["binding_status"] = "not_applicable"
        return base

    class_data = index.class_data(class_name)
    if class_data is None:
        base["issues"].append("class_not_found")
        return base

    base["class_is_abstract"] = str(class_data.get("abstract", "false")).lower() == "true"
    base["class_xml_tags"] = index.class_xml_tags(class_name)
    if not base["class_xml_tags"]:
        base["issues"].append("class_xml_tag_not_found")

    if property_name is None:
        base["binding_status"] = "resolved" if base["class_xml_tags"] else "unresolved"
        base["path_variants"] = base["class_xml_tags"]
        return base

    declarations = index.declarations(class_name, property_name)
    base["candidates"] = ordered_unique(
        f"{item['declared_owner']}.{item.get('qualifiedName') or item.get('name')}"
        for item in declarations
    )
    if not declarations:
        base["issues"].append("property_not_found_in_class_lineage")
        return base
    if len(declarations) > 1:
        signatures = {
            (item.get("xml_tag"), item.get("xml_wrapper_tag"), item.get("type"))
            for item in declarations
        }
        if len(signatures) > 1:
            base["binding_status"] = "ambiguous"
            base["issues"].append("multiple_property_declarations")
            return base

    declaration = declarations[0]
    base["declared_owner"] = declaration.get("declared_owner")
    base["property_xml_tag"] = declaration.get("xml_tag")
    base["xml_wrapper_tag"] = declaration.get("xml_wrapper_tag")
    base["type_name"] = declaration.get("type")
    base["min_occurs"] = occurs(declaration.get("pure_minOccurs", declaration.get("minOccurs")))
    base["max_occurs"] = occurs(declaration.get("pure_maxOccurs", declaration.get("maxOccurs")))
    base["enum_values"] = index.enum_values(base["type_name"])
    base["path_variants"] = path_variants(base["class_xml_tags"], declaration)
    if not base["property_xml_tag"]:
        base["issues"].append("property_xml_tag_not_found")
    base["binding_status"] = (
        "resolved"
        if base["class_xml_tags"] and base["property_xml_tag"]
        else "unresolved"
    )
    return base


def bind_record(index: MetamodelIndex, record: dict) -> dict:
    targets = [bind_target(index, number, target) for number, target in enumerate(record["targets"])]
    unresolved = [item for item in targets if item["binding_status"] in {"unresolved", "ambiguous"}]
    applicable = [item for item in targets if item["binding_status"] != "not_applicable"]
    if not targets or not applicable:
        status = "not_applicable"
    elif not unresolved:
        status = "complete"
    elif len(unresolved) == len(applicable):
        status = "unresolved"
    else:
        status = "partial"
    return {
        "schema_version": SCHEMA_VERSION,
        "id": record["id"],
        "source_sha256": record["source_sha256"],
        "binding_status": status,
        "targets": targets,
        "issues": ordered_unique(
            f"target[{item['target_index']}]:{issue}"
            for item in targets
            for issue in item["issues"]
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--curation", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    metadata = json.loads(args.metadata.read_text(encoding="utf-8"))
    index = MetamodelIndex(metadata)
    records: list[dict] = []
    for path in args.curation:
        records.extend(
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    bound = [bind_record(index, record) for record in records]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as handle:
        for record in bound:
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
    summary = {
        "record_count": len(bound),
        "complete": sum(item["binding_status"] == "complete" for item in bound),
        "partial": sum(item["binding_status"] == "partial" for item in bound),
        "unresolved": sum(item["binding_status"] == "unresolved" for item in bound),
        "not_applicable": sum(item["binding_status"] == "not_applicable" for item in bound),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

