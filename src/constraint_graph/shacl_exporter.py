"""shacl_exporter.py (v1.2)
--------------------------------
Emit SHACL for range / regex / existence / enum≤1 constraints.
"""
from __future__ import annotations

import json, pathlib
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
        # -------- 1) 解析属性 local-name -------------------------
        if isinstance(prop_full, int) or str(prop_full).isdigit():
            # enriched 里还有 xml_tag，可直接用；否则兜底 ATTR_<id>
            prop = c.get("xml_tag", f"ATTR_{prop_full}")
        else:  # str
            if "." in prop_full:
                prop = prop_full.split(".", 1)[-1]
            elif "/" in prop_full:
                prop = prop_full.split("/", 1)[-1]
            else:
                prop = prop_full
          # -------- 2) 生成合法 shape 名 --------------------------
        cid_raw = c["cid"]
        shape_id = f"CID_{cid_raw}" if isinstance(cid_raw, int) else str(cid_raw)

        return f"ex:{shape_id} a sh:PropertyShape ;\n    sh:path autosar:{prop} ;"

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

    @staticmethod
    def run(enriched_path: str | pathlib.Path,
            out_path: str | pathlib.Path):
        """读取 enriched_constraints.json → 写 autosar_shapes.ttl"""
        enriched_path, out_path = map(pathlib.Path, (enriched_path, out_path))
        cons = json.loads(enriched_path.read_text(encoding="utf-8"))
        out_dir = out_path if out_path.suffix == "" else out_path.parent
        return ShaclExporter(out_dir).export(cons)

