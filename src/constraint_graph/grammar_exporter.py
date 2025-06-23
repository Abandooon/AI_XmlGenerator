"""grammar_exporter.py
--------------------
Generate GBNF grammar and/or JSON Schema from canonical constraints.
"""
from __future__ import annotations


import json, pathlib
import re
from typing import Dict, List
from utils import normalize

# 允许“展开成 GBNF 枚举”的最大元素数
MAX_ENUM = 64


class GrammarExporter:

    def __init__(
        self,
        out_dir: str | pathlib.Path,
        roots: list[str] | None = None,  # ← 新参
    ):
        self.out_dir = pathlib.Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.lines: List[str] = []
        # 读取 roots.json（允许 None）
        self.roots = roots or []

    # ------------------------------------------------------------
    def export(self, constraints: List[Dict[str, any]]) -> pathlib.Path:
        self.lines = ["; Auto‑generated GBNF"]
        for c in constraints:
            #对 ≤1 的枚举硬约束生成 GBNF；不再依赖 type=="cardinality"
            # 仅当枚举元素 ≤ MAX_ENUM 才写 GBNF，否则留给 SMT 深验
            if (c.get("enum")
                and len(c["enum"]) <= MAX_ENUM
                and c.get("maxOccurs", 1) <= 1):
                self._emit_enum_rule(c)
        path = self.out_dir / "autosar.gbnf"
         # ---------- 补充根标签规则 + start ------------------
        if self.roots:
            root_rule_names = []
            for tag in self.roots:
                rname = normalize(tag)
                root_rule_names.append(f"<{rname}>")
                self.lines.append(f"<{rname}> ::= \"{tag}\"")
            self.lines.insert(1, "start ::= " + " | ".join(root_rule_names))
        else:
            # 若没提供 roots，仍写一个占位 start，防编译器报错
            self.lines.insert(1, "start ::= <dummy_root>")
            self.lines.insert(2, "<dummy_root> ::= \"DUMMY\"")
        path.write_text("\n".join(self.lines), encoding="utf-8")
        return path

    # ------------------------------------------------------------
    def _emit_enum_rule(self, c: Dict[str, any]):
        # ---------- rule name = sanitized xml_tag ---------------
        tag = c.get("xml_tag") or f"cid_{c['cid']}"
        # 统一用 normalize，小写 + 下划线
        rulename = f"{normalize(tag)}_list"
        enum_alts = " | ".join(f'"{v}"' for v in c["enum"])
        self.lines.append(f"<{rulename}> ::= {enum_alts}")

    @staticmethod
    def run(
        enriched_path: str | pathlib.Path,
        out_path: str | pathlib.Path,
        roots: str | pathlib.Path | None = None,
    ):
        """CLI-friendly批量入口：读取 enriched_constraints.json → 写 autosar.gbnf"""
        enriched_path, out_path = map(pathlib.Path, (enriched_path, out_path))
        cons = json.loads(enriched_path.read_text(encoding="utf-8"))

        # out_path 可能是目录，也可能是具体文件；统一转成目录
        out_dir = out_path if out_path.suffix == "" else out_path.parent
        return GrammarExporter(out_dir, roots).export(cons)

