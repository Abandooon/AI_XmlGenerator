"""smt_exporter.py (v1.2)
-----------------------
Add support for range, existence, mutuallyExclusive.
Regex skipped (Z3-str3 optional).
"""
from __future__ import annotations

import pathlib
from typing import Dict, List
import re


class SmtExporter:
    def __init__(self, out_dir: str | pathlib.Path):
        self.out_dir = pathlib.Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.lines: List[str] = []
        self.var_declared: set[str] = set()

    # ------------------------------------------------------------
    def export(self, cons: List[Dict[str, any]]) -> pathlib.Path:
        for c in cons:
            ty = c["type"]
            if ty == "cardinality" and c.get("maxOccurs") == 1 and c.get("enum"):
                self._enum_once(c)
            elif ty == "range":
                self._range(c)
            elif ty == "existence":
                self._existence(c)
            elif ty == "relationship" and c.get("mutuallyExclusive"):
                self._mutex(c)
        self.lines.append("(check-sat)")
        path = self.out_dir / "constraints.smt2"
        path.write_text("\n".join(self.lines), encoding="utf-8")
        return path

    # ------------------------------------------------------------
    def _declare(self, var: str):
        if var not in self.var_declared:
            self.lines.append(f"(declare-const {var} String)")
            self.var_declared.add(var)

    # _mangle()
    def _mangle(self, tgt) -> str:
        """
        Convert any target (attrId | "Class.attr" | "Class/attr")
        into a valid SMT variable name, e.g. 1234 → A_1234,
        "Pkg.Class.attr" → Pkg_Class_attr.
        """
        if isinstance(tgt, int) or str(tgt).isdigit():
            return f"A_{tgt}"  # ensure it starts with a letter
        else:
            return re.sub(r"[./]", "_", str(tgt))

    def _enum_once(self, c: Dict[str, any]):
        var = self._mangle(c["targets"][0])
        self._declare(var)
        ors = " ".join(f'(= {var} "{v}")' for v in c["enum"])
        self.lines += [f"; {c['cid']}", f"(assert (or {ors}))"]

    def _range(self, c: Dict[str, any]):
        var = self._mangle(c["targets"][0])
        self._declare(var)
        if "rangeMin" in c:
            self.lines.append(f"(assert (<= {c['rangeMin']} (str.to_int {var})))")
        if "rangeMax" in c:
            self.lines.append(f"(assert (<= (str.to_int {var}) {c['rangeMax']}))")

    def _existence(self, c: Dict[str, any]):
        var = self._mangle(c["targets"][0])
        self._declare(var)
        if c.get("mustNotExist"):
            self.lines.append(f"(assert (= {var} \"\"))")
        else:
            self.lines.append(f"(assert (distinct {var} \"\"))")

    def _mutex(self, c: Dict[str, any]):
        vars_ = [self._mangle(t) for t in c["mutuallyExclusive"]]
        for v in vars_:
            self._declare(v)
        if len(vars_) >= 2:
            self.lines.append("(assert (not (and {} {})))".format(vars_[0], vars_[1]))
    # -------- CLI-friendly wrapper ---------------------------------
    @staticmethod
    def run(enriched_path: str | pathlib.Path,
            out_dir: str | pathlib.Path) -> pathlib.Path:
        """
        Convenience wrapper so CLI can simply call
            SmtExporter.run("enriched_constraints.json", "smt")
        """
        import json, pathlib

        enriched_path, out_dir = map(pathlib.Path, (enriched_path, out_dir))
        cons = json.loads(enriched_path.read_text(encoding="utf-8"))
        return SmtExporter(out_dir).export(cons)