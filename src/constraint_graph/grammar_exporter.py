"""grammar_exporter.py
--------------------
Generate GBNF grammar and/or JSON Schema from canonical constraints.
"""
from __future__ import annotations


import json, pathlib
import re
from typing import Dict, List


class GrammarExporter:
    def __init__(self, out_dir: str | pathlib.Path):
        self.out_dir = pathlib.Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.lines: List[str] = []

    # ------------------------------------------------------------
    def export(self, constraints: List[Dict[str, any]]) -> pathlib.Path:
        self.lines = ["; Auto‑generated GBNF"]
        for c in constraints:
            #对 ≤1 的枚举硬约束生成 GBNF；不再依赖 type=="cardinality"
            if c.get("enum") and c.get("maxOccurs", 1) <= 1:
                self._emit_enum_rule(c)
        path = self.out_dir / "autosar.gbnf"
        path.write_text("\n".join(self.lines), encoding="utf-8")
        return path

    # ------------------------------------------------------------
    def _emit_enum_rule(self, c: Dict[str, any]):
        # ---------- rule name = sanitized xml_tag ---------------
        tag = c.get("xml_tag") or f"CID_{c['cid']}"
        # keep A-Z, a-z, 0-9, replace others with '_', upper-case
        slug = re.sub(r"[^A-Za-z0-9]", "_", str(tag)).upper()
        # GBNF rule must start with a letter
        if slug[0].isdigit():
                    slug = "X_" + slug
        rulename = f"{slug}_LIST"
        enum_alts = " | ".join(f'"{v}"' for v in c["enum"])
        self.lines.append(f"<{rulename}> ::= {enum_alts}")

    @staticmethod
    def run(enriched_path: str | pathlib.Path,
            out_path: str | pathlib.Path):
        """CLI-friendly批量入口：读取 enriched_constraints.json → 写 autosar.gbnf"""
        enriched_path, out_path = map(pathlib.Path, (enriched_path, out_path))
        cons = json.loads(enriched_path.read_text(encoding="utf-8"))

        # out_path 可能是目录，也可能是具体文件；统一转成目录
        out_dir = out_path if out_path.suffix == "" else out_path.parent
        return GrammarExporter(out_dir).export(cons)

