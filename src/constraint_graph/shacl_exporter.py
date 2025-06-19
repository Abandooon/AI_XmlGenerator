"""shacl_exporter.py (v1.2)
--------------------------------
Emit SHACL for range / regex / existence / enum≤1 constraints.
"""
from __future__ import annotations

import pathlib
from typing import Dict, List


class ShaclExporter:
    def __init__(self, out_dir: str | pathlib.Path):
        self.out_dir = pathlib.Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.lines: List[str] = [
            "@prefix sh: <http://www.w3.org/ns/shacl#> .",
            "@prefix ex: <http://example.com/> .",
            "@prefix autosar: <http://autosar.org/> .",
        ]

    # ------------------------------------------------------------
    def export(self, constraints: List[Dict[str, any]]) -> pathlib.Path:
        for c in constraints:
            ty = c["type"]
            if ty == "cardinality" and c.get("maxOccurs") == 1 and c.get("enum"):
                self._emit_enum_max1(c)
            elif ty == "range":
                self._emit_range(c)
            elif ty == "format" and c.get("regex"):
                self._emit_regex(c)
            elif ty == "existence":
                self._emit_existence(c)
        path = self.out_dir / "autosar_shapes.ttl"
        path.write_text("\n".join(self.lines), encoding="utf-8")
        return path

    # ------------------------------------------------------------
    def _shape_header(self, c):
        prop_full = c["targets"][0]
        prop = prop_full.split(".", 1)[-1] if "." in prop_full else prop_full.split("/", 1)[-1]
        return f"ex:{c['cid']} a sh:PropertyShape ;\n    sh:path autosar:{prop} ;"

    def _emit_enum_max1(self, c: Dict[str, any]):
        in_list = " ".join(f'"{v}"' for v in c["enum"])
        self.lines.append(
            f"{self._shape_header(c)}\n    sh:in ( {in_list} ) ;\n    sh:maxCount 1 .\n" )

    def _emit_range(self, c: Dict[str, any]):
        hdr = self._shape_header(c)
        extra = []
        if "rangeMin" in c:
            extra.append(f"    sh:minInclusive {c['rangeMin']} ;")
        if "rangeMax" in c:
            extra.append(f"    sh:maxInclusive {c['rangeMax']} ;")
        self.lines.append("\n".join([hdr, *extra, "    .\n"]))

    def _emit_regex(self, c: Dict[str, any]):
        pattern = c["regex"].replace("\\", "\\\\")
        self.lines.append(
            f"{self._shape_header(c)}\n    sh:pattern \"{pattern}\" .\n")

    def _emit_existence(self, c: Dict[str, any]):
        hdr = self._shape_header(c)
        if c.get("mustNotExist"):
            self.lines.append(f"{hdr}\n    sh:maxCount 0 .\n")
        else:
            self.lines.append(f"{hdr}\n    sh:minCount 1 .\n")
