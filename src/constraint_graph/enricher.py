"""enricher.py  (v1.0)
---------------------
Inject *schema‑level metadata* (maxOccurs / enum literals) into canonical constraints
so exporters can rely solely on the constraint dict.
"""
from __future__ import annotations

from typing import Any, Dict, List


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
            if "." in tgt:
                cls, attr = tgt.split(".", 1)
            elif "/" in tgt:
                cls, attr = tgt.split("/", 1)  # 容错分支
            else:
                continue
            # 构造查表 key – 统一用 '.'
            key = f"{cls}.{attr}"
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
