"""Infer missing target hints from curated local terminology and metamodel properties.

This is a deterministic binding aid, not a semantic classifier.  It runs only
when direct lexical extraction produced no metamodel target.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

WORD = re.compile(r"[A-Z]+(?=[A-Z][a-z]|$)|[A-Z]?[a-z]+|[0-9]+")


def words(value: str) -> list[str]:
    return [item.casefold() for item in WORD.findall(value) if len(item) > 1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    records = [json.loads(line) for line in args.input.read_text(encoding="utf-8").splitlines() if line.strip()]
    source = {item["id"]: item for item in (json.loads(line) for line in args.source.read_text(encoding="utf-8").splitlines() if line.strip())}
    metadata = json.loads(args.metadata.read_text(encoding="utf-8"))
    classes: dict[str, dict] = {}
    for bucket in ("groups", "complexTypes", "extract_inner_class"):
        classes.update(metadata.get(bucket, {}))
    enriched = 0
    for record in records:
        if any(target.get("class_name") for target in record["targets"]):
            continue
        source_record = source[record["id"]]
        text = (source_record["title"] + " " + source_record["expression"]).casefold()
        text_words = set(re.findall(r"[a-z0-9]+", text))
        local = list(dict.fromkeys(
            source_record["terminology_context"].get("local_classes", [])
            + source_record["terminology_context"].get("inherited_classes", [])
        ))
        scored: list[tuple[int, str, list[str]]] = []
        for class_name in local:
            data = classes.get(class_name)
            if data is None:
                continue
            score = 0
            class_words = words(class_name)
            if class_name.casefold() in text:
                score += 100
            overlap = set(class_words).intersection(text_words)
            score += 8 * len(overlap)
            if class_words and set(class_words).issubset(text_words):
                score += 45
            properties: list[str] = []
            for item in list(data.get("elements", []) or []) + list(data.get("attributes", []) or []):
                name = str(item.get("name") or "")
                if name and re.search(rf"(?<![a-z0-9]){re.escape(name.casefold())}(?![a-z0-9])", text):
                    properties.append(name)
                    score += 30
            if score:
                scored.append((score, class_name, properties))
        scored.sort(key=lambda item: (-item[0], item[1]))
        if not scored:
            continue
        best = scored[0][0]
        selected = [item for item in scored if item[0] >= max(20, int(best * 0.7))][:3]
        targets: list[dict] = []
        for score, class_name, properties in selected:
            if properties:
                for property_name in properties[:4]:
                    targets.append({
                        "role":"property", "class_name":class_name, "property_name":property_name,
                        "evidence":f"metamodel property {property_name} explicitly occurs in source (binding score {score})",
                    })
            else:
                targets.append({
                    "role":"context", "class_name":class_name, "property_name":None,
                    "evidence":f"local terminology matches source wording (binding score {score})",
                })
        if targets:
            record["targets"] = targets
            issue = "target_hint_inferred_from_local_metamodel_context"
            if issue not in record["curation"]["issues"]:
                record["curation"]["issues"].append(issue)
            enriched += 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(json.dumps({"record_count":len(records),"enriched_record_count":enriched},ensure_ascii=False,indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
