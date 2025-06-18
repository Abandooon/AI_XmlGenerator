"""shacl_exporter.py
--------------------
Generate SHACL shapes file (Turtle) from canonical constraints.
"""
from __future__ import annotations

import pathlib
from typing import Dict, List


class ShaclExporter:
    def __init__(self, out_dir: str | pathlib.Path):
        self.out_dir = pathlib.Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.lines: List[str] = ["@prefix sh: <http://www.w3.org/ns/shacl#> ."]

    # ------------------------------------------------------------
    def export(self, constraints: List[Dict[str, any]]) -> pathlib.Path:
        for c in constraints:
            if c["type"] == "cardinality" and c["maxOccurs"] == 1 and c["enum"]:
                self._emit_enum_max1(c)
        path = self.out_dir / "autosar_shapes.ttl"
        path.write_text("\n".join(self.lines), encoding="utf-8")
        return path

    # ------------------------------------------------------------
    def _emit_enum_max1(self, c: Dict[str, any]):
        shape = c["cid"]
        path_prop = c["targets"][0].split(".")[-1]
        in_list = " ".join(f'"{v}"' for v in c["enum"])
        self.lines.append(
            f"""
            ex:{shape} a sh:PropertyShape ;
                sh:path autosar:{path_prop} ;
                sh:in ( {in_list} ) ;
                sh:maxCount 1 .
            """.strip()
        )
