"""enricher.py  (v1.0)
---------------------
Inject *schema‑level metadata* (maxOccurs / enum literals) into canonical constraints
so exporters can rely solely on the constraint dict.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List
import pathlib


class ConstraintEnricher:
    """Augment canonical constraints with Attribute / Enum info."""

    def __init__(self, attr_idx: Dict[str, Dict[str, Any]], enum_idx: Dict[str, List[Dict[str, Any]]]):
        self.attr_idx = attr_idx  # key: "Class/attr" → {maxOccurs, minOccurs, type}
        self.enum_idx = enum_idx  # key: EnumName → list[lit_node]

    def enrich(self, cons: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        for c in cons:
            if not c.get("targets"):
                continue

            tgt = c["targets"][0]
            # enrich() 里解析 class / attr
             # --- 支持三种格式 --------------------------------

            if isinstance(tgt, int):  # ① 纯 ID
                key = self.aid2key.get(tgt)
                if not key:
                    continue
            elif tgt.isdigit():  # ② 字符串数字
                key = self.aid2key.get(int(tgt))
                if not key:
                    continue
            elif "." in tgt or "/" in tgt:  # ③ 已是 "Class.attr"
                cls, attr = re.split(r"[./]", tgt, 1)
                key = f"{cls}.{attr}"
            else:
                continue
            meta = self.attr_idx.get(key)

            if not meta:  # 找不到属性索引，同样补 None
                c.setdefault("maxOccurs", None)
                c.setdefault("minOccurs", None)
                continue

            # occurs
            c.setdefault("maxOccurs", meta.get("maxOccurs"))
            c.setdefault("minOccurs", meta.get("minOccurs"))

            # enum
            et = meta.get("type")
            if et and not c.get("enum") and et in self.enum_idx:
                c["enum"] = [lit["value"] for lit in self.enum_idx[et]]

        return cons

    @classmethod
    def run(
        cls,
        raw_attr_fp: str | pathlib.Path,
        raw_enum_fp: str | pathlib.Path,
        canonical_fp: str | pathlib.Path,
        out_fp: str | pathlib.Path,
    ):
        import json, pathlib
        raw_attr_fp, raw_enum_fp, canonical_fp, out_fp = map(pathlib.Path,
                                                            [raw_attr_fp, raw_enum_fp, canonical_fp, out_fp])

        # --- build indices -----------------------------------------
        with raw_attr_fp.open(encoding="utf-8") as f:
            attr_rows = [json.loads(l) for l in f]
        with raw_enum_fp.open(encoding="utf-8") as f:
            enum_rows = [json.loads(l) for l in f]
        attr_idx = {f"{r['classId']}.{r['xml_tag']}": {
                           "maxOccurs": r["maxOccurs"],
                           "minOccurs": r["minOccurs"],
                           "type": r["typeId"],
        } for r in attr_rows}
        # ⭐ 新增： attrId → "classId.xml_tag"
        aid2key = {r["attrId"]: f"{r['classId']}.{r['xml_tag']}" for r in attr_rows}
        enum_idx = {r["enumId"]: r["values"] for r in enum_rows}

        # --- enrich -------------------------------------------------
        with canonical_fp.open(encoding="utf-8") as f:
            canon = json.load(f)
        enricher = cls(attr_idx, enum_idx)
        enricher.aid2key = aid2key  # 动态挂给实例
        enriched = enricher.enrich(canon)
        out_fp.write_text(json.dumps(enriched, ensure_ascii=False, indent=2), encoding="utf-8")
        return out_fp
