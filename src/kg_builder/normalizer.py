"""
Metadata Normalizer
----------------------------------------------------
• 为每个实体统一生成 IRI
• Attribute: qualifiedName ← document_name 末段 │ name
"""

from __future__ import annotations
import re, unicodedata
from typing import Any
from utils.logger import get_logger

logger = get_logger(__name__)
_non_alnum = re.compile(r"[^0-9a-zA-Z]+")


def _slug(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = _non_alnum.sub("_", text)
    return re.sub(r"_+", "_", text).strip("_")


class _N:
    def __init__(self, domain: str, version: str):
        self.domain, self.version = domain.lower(), version

    def iri(self, name: str) -> str:
        return f"{self.domain}:{self.version}/{_slug(name)}"

    # ---------- helpers ----------
    def _norm_attr(self, attr: dict[str, Any], pcls: str) -> None:
        # 提取 local_attr 与 owner_cls
        local_attr = attr["name"]
        owner_cls = pcls
        if "document_name" in attr and "." in attr["document_name"]:
            owner_cls, local_attr = attr["document_name"].split(".", 1)

        # IRI & 回写字段
        attr["qualifiedName"] = f"{owner_cls}.{local_attr}"
        attr["parentClass"] = pcls
        attr["ownerClass"] = owner_cls  # ★ 逻辑所属类
        attr["iri"] = self.iri(f"{pcls}/{local_attr}")

    # ---------- public ----------
    def normalize(self, m: dict[str, Any]) -> None:
        # groups
        for grp in m.get("groups", {}).values():
            grp["iri"] = self.iri(grp["name"])
            for elem in grp.get("elements", []):
                self._norm_attr(elem, grp["name"])

        # complexTypes
        for ct in m.get("complexTypes", {}).values():
            ct["iri"] = self.iri(ct["name"])
            for lst in ("attributes", "elements"):
                for attr in ct.get(lst, []):
                    self._norm_attr(attr, ct["name"])

        # inner classes
        for ict in m.get("extract_inner_class", {}).values():
            ict["iri"] = self.iri(ict["name"])
            for lst in ("attributes", "elements"):
                for attr in ict.get(lst, []):
                    self._norm_attr(attr, ict["name"])

        # simpleTypes / EnumLiteral
        for st in m.get("simpleTypes", {}).values():
            st["iri"] = self.iri(st["name"])
            for i, lit in enumerate(st.get("enumerations", [])):
                val = lit.get("value") if isinstance(lit, dict) else lit
                st["enumerations"][i] = {
                    "value": val,
                    "iri": self.iri(f"{st['name']}/{val}")
                }


def normalize_metadata(meta: dict[str, Any], *, domain="AUTOSAR", version="UNSPECIFIED") -> dict[str, Any]:
    _N(domain, version).normalize(meta)
    logger.info("元数据规范化完成 (domain=%s, version=%s)", domain, version)
    return meta
