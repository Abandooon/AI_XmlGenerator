"""Build fine-grained, hash-versioned retrieval cards."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from .dataset import build_retrieval_manifest
except ImportError:  # direct script execution from run_pipeline.py
    from dataset import build_retrieval_manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--constraints", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest-output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    constraints = json.loads(args.constraints.read_text(encoding="utf-8-sig"))
    cards: list[dict] = []
    for constraint in constraints:
        semantics = constraint["semantics"]
        verification = constraint["verification"]
        bound = [target for target in constraint["targets"] if target["binding_status"] == "resolved"]
        paths = sorted({target["path"] for target in bound if target.get("path")})
        class_tags = sorted({target["class_xml_tag"] for target in bound if target.get("class_xml_tag")})
        property_tags = sorted({target["property_xml_tag"] for target in bound if target.get("property_xml_tag")})
        cards.append({
            "schema_version": "2.0",
            "constraint_id": constraint["id"],
            "source_sha256": constraint["source"]["source"]["sha256"],
            "title": constraint["source"]["title"],
            "summary": semantics["summary"],
            "section_path": constraint["source"]["source"]["section_path"],
            "class_tags": class_tags,
            "property_tags": property_tags,
            "paths": paths,
            "rule_family": semantics["rule_family"],
            "scope": semantics["scope"],
            "normativity": semantics["normativity"],
            "importance": semantics["importance"],
            "is_core": semantics["is_core"],
            "usages": semantics["usages"],
            "validation_policy": verification["policy"],
            "must_validate": verification["must_validate"],
            "severity": verification["severity"],
            "backend": verification["preferred_backend"],
            "quality": constraint["quality"]["review_status"],
        })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as handle:
        for card in cards:
            handle.write(json.dumps(card, ensure_ascii=False, separators=(",", ":")) + "\n")
    manifest = build_retrieval_manifest(cards)
    args.manifest_output.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
