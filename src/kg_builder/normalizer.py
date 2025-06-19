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
import os

logger = get_logger(__name__)
_non_alnum = re.compile(r"[^0-9a-zA-Z]+")


def _slug(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = _non_alnum.sub("_", text)
    return re.sub(r"_+", "_", text).strip("_")


class _N:
    def __init__(self, domain: str, version: str):
        self.domain, self.version = domain.lower(), version
        self.output_dir = "output"  # 输出目录
        os.makedirs(self.output_dir, exist_ok=True)  # 创建文件夹（如果不存在）

    def iri(self, name: str) -> str:
        return f"{self.domain}:{self.version}/{_slug(name)}"

    def _write_to_file(self, name: str, iri: str) -> None:
        # 将元素名和iri写入文件
        with open(os.path.join(self.output_dir, "elements_iri.txt"), "a") as f:
            f.write(f"{name}-{iri}\n")

    # ---------- helpers ----------
    def _norm_attr(self, attr: dict[str, Any], pcls: str) -> None:
        local_attr = attr.get("qualifiedname") or attr["name"]
        owner_cls = pcls

        if "document_name" in attr and "." in attr["document_name"]:
            owner_cls, doc_attr = attr["document_name"].split(".", 1)
            if not attr.get("qualifiedname"):
                local_attr = doc_attr

        # 生成iri
        attr["qualifiedName"] = f"{owner_cls}.{local_attr}"
        attr["parentClass"] = pcls
        attr["ownerClass"] = owner_cls
        attr["iri"] = self.iri(f"{pcls}/{local_attr}")

        # 写入到文件
        self._write_to_file(attr["qualifiedName"], attr["iri"])

    # ---------- public ----------
    def normalize(self, m: dict[str, Any]) -> None:
        # groups
        for grp in m.get("groups", {}).values():
            grp["iri"] = self.iri(grp["name"])
            self._write_to_file(grp["name"], grp["iri"])
            for elem in grp.get("elements", []):
                self._norm_attr(elem, grp["name"])

        # complexTypes
        for ct in m.get("complexTypes", {}).values():
            ct["iri"] = self.iri(ct["name"])
            self._write_to_file(ct["name"], ct["iri"])
            for lst in ("attributes", "elements"):
                for attr in ct.get(lst, []):
                    self._norm_attr(attr, ct["name"])

        # inner classes
        for ict in m.get("extract_inner_class", {}).values():
            ict["iri"] = self.iri(ict["name"])
            self._write_to_file(ict["name"], ict["iri"])
            for lst in ("attributes", "elements"):
                for attr in ict.get(lst, []):
                    self._norm_attr(attr, ict["name"])

        # simpleTypes / EnumLiteral
        for st in m.get("simpleTypes", {}).values():
            st["iri"] = self.iri(st["name"])
            self._write_to_file(st["name"], st["iri"])
            for i, lit in enumerate(st.get("enumerations", [])):
                val = lit.get("value") if isinstance(lit, dict) else lit
                st["enumerations"][i] = {
                    "value": val,
                    "iri": self.iri(f"{st['name']}/{val}")
                }
                self._write_to_file(f"{st['name']}/{val}", st["enumerations"][i]["iri"])

def normalize_metadata(meta: dict[str, Any], *, domain="AUTOSAR", version="UNSPECIFIED") -> dict[str, Any]:
    _N(domain, version).normalize(meta)
    logger.info("元数据规范化完成 (domain=%s, version=%s)", domain, version)
    return meta
