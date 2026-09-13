#!/usr/bin/env python3
"""Check current reviewer navigation against the local ATLAS review tree.

Standard library only; no network or file writes. GitHub ATLAS paths and
api_rag/paper/atlas-review paths map to this tree. External websites are counted
without checking their availability. Relative navigation links require conversion
to GitHub URLs. Use --document repeatedly to inspect external Markdown copies.
"""

from __future__ import annotations

import argparse
from collections import Counter
import html
import json
from pathlib import Path
import re
import sys
import unicodedata
from urllib.parse import unquote, urlsplit

sys.dont_write_bytecode = True
REPOSITORY = ("abandooon", "ai_xmlgenerator")
FIXED_DOCUMENTS = (
    "README.md", "paper/README.md", "paper/current/README.md",
    "paper/current/english/README.md", "paper/current/english/LOCATIONS.md",
    "paper/current/latex/README.md", "paper/current/latex/LOCATIONS.md",
    "paper/REVIEW_RESPONSE_MATRIX.md", "paper/COMMENT_SOURCE_MAP.md",
    "paper/figure_sources/README.md",
    "inspection/examples/README.md",
    "supporting/bibliography_compatibility/README.md",
    "paper/current/english/TRANSLATION_REVIEW.md",
    "validation/publication_review/COMMAND_AUDIT.md",
)


def blank(match):
    return "".join("\n" if c == "\n" else " " for c in match.group())


def without_code_blocks(text):
    text = re.sub(r"<!--.*?-->", blank, text, flags=re.S)
    lines, fence = [], None
    for line in text.splitlines(keepends=True):
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if fence:
            lines.append("".join("\n" if c == "\n" else " " for c in line))
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence):
                fence = None
        elif marker:
            fence = marker[1]
            lines.append("".join("\n" if c == "\n" else " " for c in line))
        else:
            lines.append(line)
    return "".join(lines)


def label_key(label):
    return " ".join(label.split()).casefold()


def destination(value):
    value = value.strip()
    if value.startswith("<"):
        end = value.find(">")
        return value[1:end] if end >= 0 else value[1:]
    # Link titles follow whitespace; spaces in paths should be percent encoded.
    return re.split(r"\s+", value, maxsplit=1)[0]


def links(text):
    """Read inline, reference-definition, HTML and bare web destinations.

    Reference definitions are checked once even when a shorthand link is reused.
    Bare bracketed prose is not guessed to be an undefined shorthand reference.
    """
    text = without_code_blocks(text)
    text = re.sub(r"(`+)(.*?)\1", blank, text, flags=re.S)
    found, occupied, definitions, parser_issues = [], [], {}, []

    def add(start, end, target):
        found.append((text.count("\n", 0, start) + 1, html.unescape(target)))
        occupied.append((start, end))

    for match in re.finditer(r"^ {0,3}\[([^]\n]+)\]:[ \t]*(<[^>\n]*>|\S+)", text, re.M):
        definitions[label_key(match[1])] = destination(match[2])
        add(match.start(), match.end(), destination(match[2]))
    i = 0
    while i < len(text):
        if text[i] != "[" or (i and text[i - 1] == "\\"):
            i += 1
            continue
        if any(start <= i < end for start, end in occupied):
            i += 1
            continue
        end, depth = i + 1, 1
        while end < len(text) and depth:
            if text[end] == "\\":
                end += 2
                continue
            depth += (text[end] == "[") - (text[end] == "]")
            end += 1
        if depth or end >= len(text):
            i += 1
            continue
        if text[end] == "(":
            stop, level, angle = end + 1, 1, False
            while stop < len(text) and level:
                char = text[stop]
                if char == "\\":
                    stop += 2
                    continue
                if char == "<":
                    angle = True
                elif char == ">":
                    angle = False
                elif not angle:
                    level += (char == "(") - (char == ")")
                stop += 1
            if level == 0:
                add(i, stop, destination(text[end + 1:stop - 1]))
                i = stop
                continue
        elif text[end] == "[":
            stop = text.find("]", end + 1)
            if stop >= 0:
                label = text[end + 1:stop] or text[i + 1:end - 1]
                if label_key(label) not in definitions:
                    parser_issues.append((text.count("\n", 0, i) + 1,
                                          "undefined_reference", label))
                occupied.append((i, stop + 1))
                i = stop + 1
                continue
        i = end
    for match in re.finditer(r"<(?:a|img)\b[^>]*?\b(?:href|src)\s*=\s*(['\"])(.*?)\1[^>]*>", text, re.I):
        add(match.start(), match.end(), match[2])
    for match in re.finditer(r"(?:https?://|file:///)[^\s<>\"']+", text, re.I):
        if any(start <= match.start() < end for start, end in occupied):
            continue
        target = match.group().rstrip(".,;")
        while target.endswith(")") and target.count(")") > target.count("("):
            target = target[:-1]
        add(match.start(), match.end(), target)
    return sorted(set(found)), parser_issues


def heading_anchors(text):
    text = without_code_blocks(text)
    anchors = {html.unescape(m[2]) for m in re.finditer(
        r"<a\b[^>]*\b(?:id|name)\s*=\s*(['\"])(.*?)\1", text, re.I)}
    used = set()
    lines = text.splitlines()
    headings = []
    for index, line in enumerate(lines):
        match = re.match(r"^ {0,3}#{1,6}(?:\s+|$)(.*)$", line)
        if match:
            headings.append(re.sub(r"\s+#+\s*$", "", match[1]))
        elif (index and re.fullmatch(r" {0,3}(?:=+|-+)\s*", line)
              and lines[index - 1].strip() and "|" not in lines[index - 1]):
            headings.append(lines[index - 1].strip())
    for title in headings:
        title = re.sub(r"!?\[([^]]*)\]\([^)]*\)", r"\1", title)
        title = re.sub(r"<[^>]*>", "", title)
        title = html.unescape(title).lower().replace("`", "").replace("*", "")
        title = re.sub(r"\\([!\"#$%&'()*+,./:;<=>?@\[\]\\^_`{|}~-])", r"\1", title)
        slug = "".join(c for c in title if c in "-_" or not unicodedata.category(c).startswith(("P", "S")))
        slug = re.sub(r"\s", "-", slug.strip())
        candidate, suffix = slug, 0
        while candidate in used:
            suffix += 1
            candidate = f"{slug}-{suffix}"
        used.add(candidate)
        anchors.add(candidate)
    return anchors


def local_repository_path(url):
    """Return a mapped relative path/type, external classification, or error."""
    parsed = urlsplit(url)
    host = parsed.netloc.casefold().split(":", 1)[0]
    parts = unquote(parsed.path).strip("/").split("/") if parsed.path.strip("/") else []
    if host not in {"github.com", "www.github.com", "raw.githubusercontent.com", "codeload.github.com"}:
        return None, "external", None
    if len(parts) < 2 or tuple(p.casefold() for p in parts[:2]) != REPOSITORY:
        return None, "external", None
    rest = parts[2:]
    if not rest:
        return "", "repository_root", None
    if host == "codeload.github.com":
        return None, "repository_download_not_fetched", None
    if rest[0] == "archive":
        return None, "repository_download_not_fetched", None
    if host == "raw.githubusercontent.com":
        kind, ref, content = "blob", rest[0], rest[1:]
    elif len(rest) >= 2 and rest[0] in {"blob", "tree", "raw"}:
        kind, ref, content = rest[0], rest[1], rest[2:]
    elif rest[0] in {"issues", "pull", "pulls", "actions", "commits", "commit", "compare",
                      "releases", "discussions", "projects", "security", "network", "stargazers", "forks"}:
        return None, "repository_service_not_fetched", None
    else:
        return None, "repository", "unsupported_repository_url_route"
    if ref == "ATLAS":
        return "/".join(content), kind, None
    if ref == "api_rag" and content[:2] == ["paper", "atlas-review"]:
        return "/".join(content[2:]), kind, None
    return None, "repository", "repository_ref_outside_review_tree"


def navigation_documents(root):
    paths = {root / name for name in FIXED_DOCUMENTS}
    paths.update((root / "docs").glob("*.md"))
    paths.update((root / "experiments").glob("*/README.md"))
    return sorted(paths, key=lambda p: p.as_posix().casefold())


def inspect(root, documents):
    issues, classifications, checked_documents = [], Counter(), []
    text_cache, anchor_cache = {}, {}
    link_count = 0

    def display(path):
        return path.relative_to(root).as_posix() if path.is_relative_to(root) else path.name

    def problem(doc, line, target, code, **details):
        issues.append({"document": display(doc), "line": line, "target": target,
                       "error": code, **details})

    def text_of(path):
        if path not in text_cache:
            text_cache[path] = path.read_text(encoding="utf-8-sig")
        return text_cache[path]

    for doc in documents:
        doc = doc.resolve()
        if not doc.is_file():
            problem(doc, 0, "", "navigation_document_missing")
            continue
        checked_documents.append(display(doc))
        destinations, parse_issues = links(text_of(doc))
        for line, code, label in parse_issues:
            problem(doc, line, label, code)
        for line, target in destinations:
            link_count += 1
            # Only an anchored drive pattern is local. In particular, the tail
            # of 'https:/' must never be mistaken for a Windows 's:/' path.
            if re.match(r"^(?:file:|/?[A-Za-z]:[/\\]|\\\\)", target, re.I):
                classifications["forbidden_local_target"] += 1
                problem(doc, line, target, "local_filesystem_target")
                continue
            parsed = urlsplit(target)
            fragment = unquote(parsed.fragment)
            if parsed.scheme in {"http", "https"}:
                if not parsed.netloc:
                    problem(doc, line, target, "malformed_web_url")
                    continue
                relative, kind, error = local_repository_path(target)
                classifications[kind] += 1
                if error:
                    problem(doc, line, target, error)
                    continue
                if relative is None:
                    continue
                path = (root / relative).resolve()
            elif parsed.scheme:
                classifications["external_other_scheme"] += 1
                continue
            else:
                classifications["relative_requires_conversion"] += 1
                problem(doc, line, target, "relative_link_requires_github")
                relative = unquote(parsed.path)
                path = (doc.parent / relative).resolve() if relative else doc
                kind = "relative"
            if not path.is_relative_to(root):
                problem(doc, line, target, "target_escapes_review_tree")
                continue
            if not path.exists():
                problem(doc, line, target, "target_missing", resolved_path=display(path))
                continue
            if kind == "tree" and not path.is_dir():
                problem(doc, line, target, "tree_url_points_to_file")
                continue
            if kind in {"blob", "raw"} and not path.is_file():
                problem(doc, line, target, "file_url_points_to_directory")
                continue
            if not fragment:
                continue
            line_anchor = re.fullmatch(r"L([0-9]+)(?:-L([0-9]+))?", fragment)
            if line_anchor:
                if not path.is_file():
                    problem(doc, line, target, "line_anchor_on_directory")
                    continue
                try:
                    count = len(text_of(path).splitlines())
                except UnicodeError:
                    problem(doc, line, target, "line_anchor_on_non_text_file")
                    continue
                first, last = int(line_anchor[1]), int(line_anchor[2] or line_anchor[1])
                if not 1 <= first <= last <= count:
                    problem(doc, line, target, "line_anchor_out_of_bounds", target_lines=count)
                else:
                    classifications["checked_line_anchor"] += 1
            elif path.suffix.casefold() == ".md" or path.is_dir():
                heading_file = path / "README.md" if path.is_dir() else path
                if not heading_file.is_file():
                    problem(doc, line, target, "heading_readme_missing")
                    continue
                if heading_file not in anchor_cache:
                    anchor_cache[heading_file] = heading_anchors(text_of(heading_file))
                anchors = anchor_cache[heading_file]
                if fragment not in anchors and fragment.removeprefix("user-content-") not in anchors:
                    problem(doc, line, target, "markdown_anchor_missing")
                else:
                    classifications["checked_markdown_anchor"] += 1
            elif path.suffix.casefold() == ".pdf" and re.fullmatch(r"page=[1-9][0-9]*", fragment):
                classifications["pdf_page_fragment_syntax_only"] += 1
            else:
                problem(doc, line, target, "unsupported_or_invalid_fragment")
    return {"status": "PASS" if not issues else "FAIL", "mode": "read-only local navigation check",
            "repository": "Abandooon/AI_XmlGenerator", "documents_checked": checked_documents,
            "links_checked": link_count, "classifications": dict(sorted(classifications.items())),
            "errors": len(issues), "issues": issues,
            "scope": "Current reviewer navigation only. Local GitHub target paths, text line anchors and Markdown headings/explicit anchor IDs are checked. External websites and repository service/download URLs are classified without network access. PDF page fragments receive syntax checks only."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--document", type=Path, action="append", help="Inspect this Markdown file instead of the default navigation set; repeatable")
    args = parser.parse_args()
    root = args.release_root.resolve()
    try:
        report = inspect(root, args.document or navigation_documents(root))
    except (OSError, ValueError, TypeError) as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}, ensure_ascii=True, indent=2))
        return 1
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
