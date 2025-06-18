"""smt_exporter.py
-----------------
Emit SMT‑LIB2 constraints from canonical constraints list.
"""
from __future__ import annotations

import pathlib
from typing import Dict, List


class SmtExporter:
    def __init__(self, out_dir: str | pathlib.Path):
        self.out_dir = pathlib.Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.lines: List[str] = []
        self.var_declared: set[str] = set()

    # ------------------------------------------------------------
    def export(self, constraints: List[Dict[str, any]]) -> pathlib.Path:
        for c in constraints:
            if c["type"] == "cardinality" and c["maxOccurs"] == 1 and c["enum"]:
                self._emit_enum_once(c)
        self.lines.append("(check-sat)")
        path = self.out_dir / "constraints.smt2"
        path.write_text("\n".join(self.lines), encoding="utf-8")
        return path

    # ------------------------------------------------------------
    def _emit_enum_once(self, c: Dict[str, any]):
        var = c["targets"][0].replace(".", "_")  # rough mangling
        if var not in self.var_declared:
            self.lines.append(f"(declare-const {var} String)")
            self.var_declared.add(var)
        ors = " ".join(f'(= {var} "{v}")' for v in c["enum"])
        self.lines.append(f"; {c['cid']}")
        self.lines.append(f"(assert (or {ors}))")
