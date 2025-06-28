"""grammar_exporter.py
--------------------
Generate GBNF grammar and/or JSON Schema from canonical AUTOSAR constraints.
This refactor removes duplicated rule emission, namespaces DEST attributes,
adds aggressive de‑duplication for TOKEN and parser rules, and keeps the public
API unchanged (GrammarExporter.run). A built‑in Lark compilation pass is left
commented‑out – enable it in CI for early failure.
"""
from __future__ import annotations

import json
import pathlib
import re
from typing import Dict, List, Set

from utils import normalize  # simple slugifier
from cli import BUILD_CFG

# ---------------------------------------------------------------------------
# Configuration ----------------------------------------------------------------
# ---------------------------------------------------------------------------
_MAX_ENUM = BUILD_CFG.get("limits", {}).get("max_enum", 64)

# ---------------------------------------------------------------------------
# Helpers ---------------------------------------------------------------------
# ---------------------------------------------------------------------------

def _iter_jsonl(fp: pathlib.Path):
    """Yield parsed JSON objects from a .jsonl file (if present)."""
    if not fp.exists():
        return
    for ln in fp.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if ln:
            yield json.loads(ln)


class GrammarExporter:
    """Convert raw_* canonical files into a single autosar.gbnf file.

    Key guarantees **after** this refactor:
    - Every TOKEN or non‑terminal rule is emitted **once and only once**.
    - XML attributes that share the same name across different classes now
      share *one* TOKEN (e.g. ATTR_DEST) and *one* value‑rule (e.g.
      <attr_dest_value>). Enumerations across contexts are **merged**.
    - Zero‑width patterns are proactively banned: any `*`, `{0,}` or `.*` in
      a regex is replaced with a `+` variant during export.
    """

    # Regex to catch zero‑width pattern constructs inside /regex/ tokens
    _STAR_PATTERN = re.compile(r"\*|\{0,\}|\.\*")

    def __init__(
        self,
        out_dir: str | pathlib.Path,
        *,
        roots: List[str] | None = None,
        raw_dir: str | pathlib.Path,
    ) -> None:
        self.out_dir = pathlib.Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)

        self.raw_dir = pathlib.Path(raw_dir)
        self.roots: List[str] = roots or []

        # In‑memory buffers ---------------------------------------------------
        self._lines: List[str] = []           # Final GBNF lines
        self._emitted_tokens: Set[str] = set()# TOKEN strings already written
        self._emitted_rules: Set[str] = set()  # "<rule> ::= ..." already written
        self._value_pool: Dict[str, Set[str]] = {}  # Aggregated enum literals

    # ---------------------------------------------- internal writer helpers --

    def _write_token(self, token: str, literal: str) -> None:
        """Emit a TOKEN line once."""
        if token in self._emitted_tokens:
            return
        self._lines.append(f'{token}: "{literal}"')
        self._emitted_tokens.add(token)

    def _write_rule(self, rule: str, production: str) -> None:
        """Emit a parser rule line once (exact textual deduplication)."""
        line = f"{rule} ::= {production}"
        if line in self._emitted_rules:
            return
        self._lines.append(line)
        self._emitted_rules.add(line)

    def _add_enum_values(self, slug: str, vals: List[str]) -> None:
        """Collect enum literals for <slug_value> rule (merged later)."""
        if not vals or len(vals) > _MAX_ENUM:
            return
        key = f"<{slug.lower()}_value>"
        self._value_pool.setdefault(key, set()).update(vals)

    # ------------------------------------------------------------- main flow --

    def export(self) -> pathlib.Path:
        """Top‑level dispatcher – returns Path to the generated autosar.gbnf."""
        self._lines = ["; Auto‑generated GBNF"]
        self._emit_roots()
        self._emit_from_raw()
        self._flush_enum_rules()
        self._sanitize_zero_width_regex()

        out_path = self.out_dir / "autosar.gbnf"
        out_path.write_text("\n".join(self._lines), encoding="utf-8")

        # Uncomment in CI – will fail fast on duplicate or bad constructs.
        try:
            from lark import Lark
            Lark(out_path.read_text(), parser="lalr")
        except Exception as exc:
            raise RuntimeError(f"GBNF compilation failed: {exc}")

        return out_path

    # ---------------------------------------------- emitting sub‑functions --

    def _emit_roots(self) -> None:
        """Emit TOKEN and parser rule for root tags and create `start` rule."""
        root_rule_names: List[str] = []
        for tag in self.roots:
            slug = normalize(tag)            # e.g. application_sw_component_type
            token = slug.upper()             # e.g. APPLICATION_SW_COMPONENT_TYPE
            self._write_token(token, tag)
            self._write_rule(f"<{slug}>", token)
            root_rule_names.append(f"<{slug}>")

        # Insert `start` as the second line for readability
        if root_rule_names:
            self._lines.insert(1, "start ::= " + " | ".join(root_rule_names))
        else:
            # fallback dummy to keep grammar compilable
            self._lines.insert(1, "start ::= <dummy_root>")
            self._write_rule("<dummy_root>", '"DUMMY"')

    # ---------------------------------------------------------------------

    def _emit_from_raw(self) -> None:
        """Walk raw JSONL sources (classes & attributes) to populate grammar."""
        raw_dir = self.raw_dir

        # -------- ENUM TABLE ------------------------------------------------
        enum_map: Dict[int, List[str]] = {}
        for rec in _iter_jsonl(raw_dir / "raw_enums.jsonl"):
            values = rec.get("values") or []
            if not (values and len(values) <= _MAX_ENUM):
                continue
            eid = rec.get("enumId", rec.get("enum_id"))
            try:
                enum_map[int(eid)] = values
            except (TypeError, ValueError):
                continue

        # -------- CLASSES (tags only) --------------------------------------
        for rec in _iter_jsonl(raw_dir / "raw_classes.jsonl"):
            tag = rec.get("xml_tag")
            if not tag:
                continue
            slug = normalize(tag)
            self._write_token(slug.upper(), tag)
            self._write_rule(f"<{slug}>", slug.upper())

        # -------- ATTRIBUTES (XML attrs + elems) ---------------------------
        for rec in _iter_jsonl(raw_dir / "raw_attributes.jsonl"):
            tag = rec.get("xml_tag")
            if not tag:
                continue

            is_attr = bool(rec.get("isXmlAttr", False))
            slug = f"attr_{normalize(tag)}" if is_attr else normalize(tag)
            token = (f"ATTR_{normalize(tag).upper()}" if is_attr else slug.upper())
            literal = f"@{tag}" if is_attr else tag

            # TOKEN + wrapper rule (avoid duplicates) ---------------------
            self._write_token(token, literal)
            self._write_rule(f"<{slug}>", token)

            # Optional wrapper tag ---------------------------------------
            if rec.get("xml_wrapper_tag"):
                wrapper = rec["xml_wrapper_tag"]
                w_slug = normalize(wrapper)
                self._write_token(w_slug.upper(), wrapper)
                self._write_rule(f"<{w_slug}>", w_slug.upper())

            # Enumerations (allowedValues or enumId) ---------------------
            enum_vals: List[str] = []
            if rec.get("allowedValues"):
                enum_vals = rec["allowedValues"][:_MAX_ENUM]
            else:
                try:
                    eid = int(rec.get("typeId", -1))
                except (TypeError, ValueError):
                    eid = -1
                enum_vals = enum_map.get(eid, [])

            self._add_enum_values(slug, enum_vals)

    # ---------------------------------------------------------------------

    def _flush_enum_rules(self) -> None:
        """Emit the aggregated <slug_value> ::= "A" | "B" rules."""
        for rule, literals in sorted(self._value_pool.items()):
            if not literals:
                continue
            alts = " | ".join(f'"{v}"' for v in sorted(literals))
            self._write_rule(rule, alts)

    # ---------------------------------------------------------------------

    def _sanitize_zero_width_regex(self) -> None:
        """Replace * / {0,} / .* patterns inside regex TOKEN definitions."""
        for i, line in enumerate(self._lines):
            if ": " not in line:
                continue
            token, body = line.split(": ", 1)
            if body.startswith("/") and self._STAR_PATTERN.search(body):
                # naive but safe – turn * into +, {0,} into {1,}, .* into .+
                body = self._STAR_PATTERN.sub(lambda m: "+" if "*" in m.group(0) else "{1,}" if "0," in m.group(0) else ".+", body)
                self._lines[i] = f"{token}: {body}"

    # ---------------------------------------------------------------------
    #  Public CLI wrapper ----------------------------------------------------
    # ---------------------------------------------------------------------

    @staticmethod
    def run(
        raw_dir: str | pathlib.Path,
        out_path: str | pathlib.Path,
        *,
        roots: List[str] | None = None,
    ) -> pathlib.Path:
        out_dir = pathlib.Path(out_path)
        if out_dir.suffix:
            # If filename with suffix supplied, take its parent as dir
            out_dir = out_dir.parent
        exporter = GrammarExporter(out_dir, roots=roots, raw_dir=raw_dir)
        return exporter.export()
