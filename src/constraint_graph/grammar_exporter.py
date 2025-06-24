"""grammar_exporter.py
--------------------
Generate GBNF grammar and/or JSON Schema from canonical constraints.
"""
from __future__ import annotations


import json, pathlib
import re
from typing import Dict, List
from utils import normalize
from cli import BUILD_CFG

# 允许“展开成 GBNF 枚举”的最大元素数
MAX_ENUM = BUILD_CFG.get("limits", {}).get("max_enum", 64)


class GrammarExporter:

    def __init__(
        self,
        out_dir: str | pathlib.Path,
        *,
        roots: list[str] | None = None,
        raw_dir: str | pathlib.Path,
    ):
        self.out_dir = pathlib.Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.lines: List[str] = []
        # roots 来自 roots.json 或 CLI
        self.roots = roots or []
        self.raw_dir = pathlib.Path(raw_dir)
        self.value_rules: dict[str, set[str]] = {}  # 枚举规则池，延迟写入去重

    # -------------------------------------------------------------------------
    def _add_value_rule(self, slug: str, vals: list[str]) -> None:
        """去重并合并同名 <slug>_value> ::= … 规则."""
        if not vals or len(vals) > MAX_ENUM:
            return
        key = f"<{slug.lower()}_value>"
        pool = self.value_rules.setdefault(key, set())
        pool.update(vals)
        if len(pool) > MAX_ENUM:  # 联合集合过大就放弃前置
            self.value_rules.pop(key, None)


    # ------------------------------------------------------------
    def export(self) -> pathlib.Path:
        # ──初始化─────────────────────────────────────────────
        self.lines = ["; Auto-generated GBNF"]

        # ──根标签 → TOKEN + 规则──────────────────────────────
        root_rule_names = []
        for tag in self.roots:  # roots 为原串，如 "APPLICATION-SW-COMPONENT-TYPE"
            slug = normalize(tag)  # application_sw_component_type
            tok = slug.upper()  # APPLICATION_SW_COMPONENT_TYPE

            self.lines.append(f"{tok}: \"{tag}\"")  # TOKEN 行
            self.lines.append(f"<{slug}> ::= {tok}")  # 规则行
            root_rule_names.append(f"<{slug}>")

        # 写唯一的 start 行（始终第 1 行，保证不会重复）
        if root_rule_names:
            self.lines.insert(1, "start ::= " + " | ".join(root_rule_names))
        else:  # 没给 roots 就写占位
            self.lines.insert(1, "start ::= <dummy_root>")
            self.lines.insert(2, "<dummy_root> ::= \"DUMMY\"")

        # ──来自 raw_*.jsonl 的 TOKEN / 枚举──────────────────
        self._emit_from_raw()

        # ──落盘──────────────────────────────────────────────
        path = self.out_dir / "autosar.gbnf"
        path.write_text("\n".join(self.lines), encoding="utf-8")
        return path

    def _emit_from_raw(self) -> None:
        """raw_classes / raw_attributes / raw_enums → TOKEN + 枚举规则"""

        def _iter_jsonl(fp: pathlib.Path):
            if not fp.exists():
                return []
            for ln in fp.read_text(encoding="utf-8").splitlines():
                if ln.strip():
                    yield json.loads(ln)

        emitted: set[str] = {
            normalize(tag).upper() for tag in self.roots
        }

        # -- 1) enumId → literals (≤64) ---------------------
        enum_map: dict[int, list[str]] = {}
        for rec in _iter_jsonl(self.raw_dir / "raw_enums.jsonl"):
            vals = rec.get("values") or []
            if not (vals and len(vals) <= MAX_ENUM):
                continue
            # 兼容 enumId / enum_id 两种拼写
            eid_raw = rec.get("enumId", rec.get("enum_id"))
            try:
                eid = int(eid_raw)
            except (TypeError, ValueError):
                continue
            enum_map[eid] = vals

        # -- 2) Class & Attribute tags + 枚举值 --------------
        def _emit_tag(tag: str) -> str:
            slug = normalize(tag)
            tok = slug.upper()
            if tok not in emitted:
                self.lines.append(f'{tok}: "{tag}"')
                self.lines.append(f"<{slug}> ::= {tok}")
                emitted.add(tok)
            return slug

        # 2a. classes
        for rec in _iter_jsonl(self.raw_dir / "raw_classes.jsonl"):
            if tag := rec.get("xml_tag"):
                _emit_tag(tag)

        # 2b. attributes (& allowedValues / enum literals)
        for rec in _iter_jsonl(self.raw_dir / "raw_attributes.jsonl"):
            # ---------- A1: 先处理 wrapper -----------------------------
            if (wtag := rec.get("xml_wrapper_tag")):
                _emit_tag(wtag)

            tag = rec.get("xml_tag")
            if not tag or rec.get("isXmlAttr"):  # 真 @属性 跳过
                continue
            slug = _emit_tag(tag)

            # ---------- A2: 合法枚举判定：只看元素数量，不再检查 maxOccurs ----
            vals: list[str] = []
            if rec.get("allowedValues") and len(rec["allowedValues"]) <= MAX_ENUM:
                vals = rec["allowedValues"]
            else:
                try:
                    tid = int(rec.get("typeId", -1))
                except (TypeError, ValueError):
                    tid = -1
                if tid in enum_map:
                    vals = enum_map[tid]

            if vals:
                self._add_value_rule(slug, vals)

        # --- 枚举规则（已去重） ------------------------------------
        for rule_name, literals in self.value_rules.items():
            alts = " | ".join(f'"{v}"' for v in sorted(literals))
            self.lines.append(f"{rule_name} ::= {alts}")

    # ------------------------------------------------------------
    @staticmethod
    def run(
            raw_dir: str | pathlib.Path,
            out_path: str | pathlib.Path,
            *,
            roots: list[str] | None = None,
    ):
        """CLI 入口：raw_*.jsonl → autosar.gbnf"""
        raw_dir = pathlib.Path(raw_dir)
        out_dir = pathlib.Path(out_path) if out_path.suffix == "" else pathlib.Path(out_path).parent
        return GrammarExporter(out_dir, roots=roots, raw_dir=raw_dir).export()

