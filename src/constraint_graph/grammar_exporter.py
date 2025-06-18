"""grammar_exporter.py
--------------------
Generate GBNF grammar and/or JSON Schema from canonical constraints.
"""
from __future__ import annotations

import pathlib
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
            if c["type"] == "cardinality" and c["maxOccurs"] == 1 and c["enum"]:
                self._emit_once_enum_rule(c)
        path = self.out_dir / "autosar.gbnf"
        path.write_text("\n".join(self.lines), encoding="utf-8")
        return path

    # ------------------------------------------------------------
    def _emit_once_enum_rule(self, c: Dict[str, any]):
        rulename = f"{c['cid'].upper()}_LIST"
        enum_alts = " | ".join(f'"{v}"' for v in c["enum"])
        self.lines.append(f"<{rulename}> ::= {enum_alts}")
