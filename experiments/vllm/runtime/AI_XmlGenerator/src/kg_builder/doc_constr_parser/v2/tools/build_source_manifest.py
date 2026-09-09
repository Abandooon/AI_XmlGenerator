"""Build an immutable source-constraint manifest from annotated AUTOSAR Markdown.

This module performs deterministic document recovery only. It does not classify
semantics, invent constraints, or call an LLM API.
"""

from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

SCHEMA_VERSION = "2.0"
CHAPTER_ORDER = (
    "chapter2.md",
    "chapter3.md",
    "chapter4.md",
    "chapter5.md",
    "chapter6.md",
    "chapter7.md",
    "chapter8-10.md",
    "chapter11-13.md",
)

OFFICIAL_ID_RE = re.compile(r"\[((?:TPS_SWCT|constr)_[A-Za-z0-9_]+)\]")
ANY_REFERENCE_RE = re.compile(r"\[((?:TPS|SWS|RS|constr)_[A-Za-z0-9_]+)\]")
CID100_RE = re.compile(r"\(cid:100\)")
CID99_RE = re.compile(r"\(cid:99\)")
SECTION_RE = re.compile(r"^#@SECTION:[ \t]*(.*)$")
CLASS_RE = re.compile(r"^#@CLASS:[ \t]*([^\r\n]*)$")
ENUM_RE = re.compile(r"^#@ENUM:[ \t]*([^\r\n]*)$")


def compact_ws(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def ordered_unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def line_number(newlines: Sequence[int], position: int) -> int:
    return bisect.bisect_right(newlines, position) + 1


def section_level(title: str) -> int:
    match = re.match(r"\s*(\d+(?:\.\d+)*)\b", title)
    if not match:
        return 1
    return match.group(1).count(".") + 1


@dataclass
class SectionFrame:
    title: str
    level: int
    local_classes: list[str] = field(default_factory=list)
    local_enums: list[str] = field(default_factory=list)


@dataclass
class LineContext:
    section_path: list[str]
    local_classes: list[str]
    inherited_classes: list[str]
    local_enums: list[str]
    inherited_enums: list[str]
    in_hierarchical_block: bool
    in_multimodal_block: bool


@dataclass
class Marker:
    open_start: int
    open_end: int
    close_start: int | None
    close_end: int | None
    definition_id: str
    id_start: int
    id_end: int
    id_position: str
    issues: list[str]


def build_line_contexts(text: str) -> list[LineContext]:
    contexts: list[LineContext] = []
    stack: list[SectionFrame] = []
    hierarchical_depth = 0
    multimodal_depth = 0

    for line in text.splitlines():
        stripped = line.strip()
        section = SECTION_RE.match(line)
        if section:
            title = section.group(1).strip()
            level = section_level(title)
            while stack and stack[-1].level >= level:
                stack.pop()
            stack.append(SectionFrame(title=title, level=level))

        if stripped == "#@Hierarchical":
            hierarchical_depth += 1
        elif stripped == "/#@Hierarchical":
            hierarchical_depth = max(0, hierarchical_depth - 1)

        if "<-------------- multimodal context" in line:
            multimodal_depth += 1

        class_match = CLASS_RE.match(line)
        if class_match and stack:
            name = class_match.group(1).strip()
            if name and name not in stack[-1].local_classes:
                stack[-1].local_classes.append(name)

        enum_match = ENUM_RE.match(line)
        if enum_match and stack:
            name = enum_match.group(1).strip()
            if name and name not in stack[-1].local_enums:
                stack[-1].local_enums.append(name)

        local_classes = list(stack[-1].local_classes) if stack else []
        local_enums = list(stack[-1].local_enums) if stack else []
        inherited_classes = ordered_unique(
            value for frame in stack[:-1] for value in frame.local_classes
        )
        inherited_enums = ordered_unique(
            value for frame in stack[:-1] for value in frame.local_enums
        )
        contexts.append(
            LineContext(
                section_path=[frame.title for frame in stack],
                local_classes=local_classes,
                inherited_classes=inherited_classes,
                local_enums=local_enums,
                inherited_enums=inherited_enums,
                in_hierarchical_block=hierarchical_depth > 0,
                in_multimodal_block=multimodal_depth > 0,
            )
        )

        if multimodal_depth and "---------------------->" in line:
            multimodal_depth = max(0, multimodal_depth - 1)

    return contexts


def paragraph_start(text: str, position: int) -> int:
    candidates = [
        text.rfind("\n\n", 0, position),
        text.rfind("\r\n\r\n", 0, position),
    ]
    found = max(candidates)
    return 0 if found < 0 else found + (4 if text.startswith("\r\n\r\n", found) else 2)


def candidate_score(text: str, match: re.Match[str], open_start: int, window_start: int) -> tuple[int, int]:
    line_start = text.rfind("\n", window_start, match.start()) + 1
    prefix = text[line_start:match.start()].strip()
    score = 0
    if not prefix:
        score += 120
    elif prefix in {"•", "-", "*"}:
        score += 110
    elif prefix.endswith("|"):
        score += 80
    if match.start() == window_start or not text[window_start:match.start()].strip():
        score += 100
    distance = open_start - match.start()
    score -= min(distance // 40, 20)
    return score, -match.start()


def choose_definition_id(
    text: str,
    open_match: re.Match[str],
    previous_close_end: int,
    next_open_start: int | None,
) -> tuple[re.Match[str], str, list[str]]:
    issues: list[str] = []
    start = max(previous_close_end, paragraph_start(text, open_match.start()))
    before = list(OFFICIAL_ID_RE.finditer(text, start, open_match.start()))
    if not before:
        broad_start = max(previous_close_end, open_match.start() - 900)
        before = list(OFFICIAL_ID_RE.finditer(text, broad_start, open_match.start()))
        start = broad_start

    if before:
        chosen = max(before, key=lambda item: candidate_score(text, item, open_match.start(), start))
        if open_match.start() - chosen.end() > 500:
            issues.append("definition_id_far_from_cid100")
        if "\n" in text[chosen.end():open_match.start()]:
            issues.append("title_wraps_lines")
        return chosen, "before_cid100", issues

    lookahead_end = min(len(text), next_open_start or len(text), open_match.end() + 900)
    after = OFFICIAL_ID_RE.search(text, open_match.end(), lookahead_end)
    if after is None:
        raise ValueError(f"No official ID found near cid:100 at offset {open_match.start()}")
    issues.append("definition_id_after_cid100")
    return after, "after_cid100", issues


def pair_markers(text: str) -> list[Marker]:
    opens = list(CID100_RE.finditer(text))
    closes = list(CID99_RE.finditer(text))
    close_starts = [item.start() for item in closes]
    markers: list[Marker] = []
    previous_close_end = 0

    for index, open_match in enumerate(opens):
        next_open_start = opens[index + 1].start() if index + 1 < len(opens) else None
        close_index = bisect.bisect_left(close_starts, open_match.end())
        close_match = closes[close_index] if close_index < len(closes) else None
        issues: list[str] = []
        if close_match is None or (next_open_start is not None and close_match.start() > next_open_start):
            close_match = None
            issues.append("missing_cid99_before_next_constraint")

        id_match, id_position, id_issues = choose_definition_id(
            text, open_match, previous_close_end, next_open_start
        )
        issues.extend(id_issues)
        markers.append(
            Marker(
                open_start=open_match.start(),
                open_end=open_match.end(),
                close_start=close_match.start() if close_match else None,
                close_end=close_match.end() if close_match else None,
                definition_id=id_match.group(1),
                id_start=id_match.start(),
                id_end=id_match.end(),
                id_position=id_position,
                issues=issues,
            )
        )
        if close_match is not None:
            previous_close_end = close_match.end()

    return markers


def record_end(text: str, marker: Marker, next_marker: Marker | None) -> int:
    if marker.close_end is None:
        if next_marker is None:
            return len(text)
        return min(next_marker.id_start, next_marker.open_start)

    line_end = text.find("\n", marker.close_end)
    if line_end < 0:
        line_end = len(text)
    return line_end


def make_record(
    document: Path,
    text: str,
    newlines: Sequence[int],
    contexts: Sequence[LineContext],
    marker: Marker,
    next_marker: Marker | None,
) -> dict:
    start = min(marker.id_start, marker.open_start)
    end = record_end(text, marker, next_marker)
    raw = text[start:end].strip()
    start_line = line_number(newlines, start)
    end_line = line_number(newlines, max(start, end - 1))
    context = contexts[min(start_line - 1, len(contexts) - 1)]
    issues = list(marker.issues)

    if marker.id_position == "before_cid100":
        title = compact_ws(text[marker.id_end:marker.open_start])
        expression_end = marker.close_start if marker.close_start is not None else end
        expression = compact_ws(text[marker.open_end:expression_end])
    else:
        title = ""
        expression_end = marker.close_start if marker.close_start is not None else end
        expression = compact_ws(text[marker.id_end:expression_end])
        issues.append("title_requires_manual_recovery")

    if not title:
        issues.append("empty_title")
    if not expression:
        issues.append("empty_expression")

    references = ordered_unique(
        ref
        for ref in ANY_REFERENCE_RE.findall(raw)
        if ref != marker.definition_id
    )

    status = "exact"
    if issues:
        status = "malformed" if any(
            issue in {
                "missing_cid99_before_next_constraint",
                "definition_id_after_cid100",
                "empty_title",
                "empty_expression",
            }
            for issue in issues
        ) else "recovered"

    return {
        "schema_version": SCHEMA_VERSION,
        "id": marker.definition_id,
        "id_type": "TPS_SWCT" if marker.definition_id.startswith("TPS_SWCT_") else "constr",
        "title": title,
        "expression": expression,
        "references": references,
        "source": {
            "document": document.name,
            "section_path": context.section_path,
            "start_line": start_line,
            "end_line": end_line,
            "raw_text": raw,
            "sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
            "in_hierarchical_block": context.in_hierarchical_block,
            "in_multimodal_block": context.in_multimodal_block,
        },
        "terminology_context": {
            "local_classes": context.local_classes,
            "inherited_classes": context.inherited_classes,
            "local_enums": context.local_enums,
            "inherited_enums": context.inherited_enums,
        },
        "parse": {
            "status": status,
            "issues": ordered_unique(issues),
            "id_position": marker.id_position,
        },
    }


def extract_document(document: Path) -> tuple[list[dict], dict]:
    text = document.read_text(encoding="utf-8")
    newlines = [match.start() for match in re.finditer("\n", text)]
    contexts = build_line_contexts(text)
    markers = pair_markers(text)
    records = [
        make_record(
            document,
            text,
            newlines,
            contexts,
            marker,
            markers[index + 1] if index + 1 < len(markers) else None,
        )
        for index, marker in enumerate(markers)
    ]
    return records, {
        "document": document.name,
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "line_count": len(text.splitlines()),
        "cid100_count": len(CID100_RE.findall(text)),
        "cid99_count": len(CID99_RE.findall(text)),
        "record_count": len(records),
        "malformed_count": sum(item["parse"]["status"] == "malformed" for item in records),
        "recovered_count": sum(item["parse"]["status"] == "recovered" for item in records),
    }


def lint_terminology(input_dir: Path, metadata: dict) -> dict:
    class_names = set().union(
        set(metadata.get("groups", {})),
        set(metadata.get("complexTypes", {})),
        set(metadata.get("extract_inner_class", {})),
    )
    enum_names = set(metadata.get("simpleTypes", {})) | set(metadata.get("complexTypes", {}))
    unknown_classes: list[dict] = []
    unknown_enums: list[dict] = []
    blank_classes: list[dict] = []

    for name in CHAPTER_ORDER:
        path = input_dir / name
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            class_match = CLASS_RE.match(line)
            if class_match:
                value = class_match.group(1).strip()
                item = {"document": name, "line": number, "value": value}
                if not value:
                    blank_classes.append(item)
                elif value not in class_names:
                    unknown_classes.append(item)
            enum_match = ENUM_RE.match(line)
            if enum_match:
                value = enum_match.group(1).strip()
                if value and value not in enum_names:
                    unknown_enums.append({"document": name, "line": number, "value": value})

    return {
        "blank_class_annotations": blank_classes,
        "unknown_class_annotations": unknown_classes,
        "unknown_enum_annotations": unknown_enums,
    }


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, values: Sequence[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for value in values:
            handle.write(json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n")


def build(input_dir: Path, output_dir: Path, metadata_path: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    all_records: list[dict] = []
    documents: list[dict] = []
    for name in CHAPTER_ORDER:
        records, stats = extract_document(input_dir / name)
        all_records.extend(records)
        documents.append(stats)

    id_counts: dict[str, int] = {}
    for record in all_records:
        id_counts[record["id"]] = id_counts.get(record["id"], 0) + 1
    duplicate_ids = sorted(key for key, count in id_counts.items() if count > 1)

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    lint = lint_terminology(input_dir, metadata)
    lint.update(
        {
            "duplicate_source_ids": duplicate_ids,
            "malformed_records": [
                {
                    "id": item["id"],
                    "document": item["source"]["document"],
                    "line": item["source"]["start_line"],
                    "issues": item["parse"]["issues"],
                }
                for item in all_records
                if item["parse"]["status"] == "malformed"
            ],
        }
    )

    manifest_path = output_dir / "source_manifest.jsonl"
    lint_path = output_dir / "document_lint.json"
    write_jsonl(manifest_path, all_records)
    write_json(lint_path, lint)
    build_manifest = {
        "schema_version": SCHEMA_VERSION,
        "documents": documents,
        "record_count": len(all_records),
        "unique_id_count": len(id_counts),
        "duplicate_id_count": len(duplicate_ids),
        "exact_count": sum(item["parse"]["status"] == "exact" for item in all_records),
        "recovered_count": sum(item["parse"]["status"] == "recovered" for item in all_records),
        "malformed_count": sum(item["parse"]["status"] == "malformed" for item in all_records),
        "source_manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "document_lint_sha256": hashlib.sha256(lint_path.read_bytes()).hexdigest(),
    }
    write_json(output_dir / "build_manifest.json", build_manifest)
    return build_manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = build(args.input_dir, args.output_dir, args.metadata)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 1 if manifest["duplicate_id_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

