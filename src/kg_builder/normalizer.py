"""
名称标准化 & 域前缀管理
====================================================
• 统一 IRI 命名: <domain>:<version>/<entityName>
• 解决同名冲突、大小写不一致
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any

from utils.logger import get_logger

logger = get_logger(__name__)


class NameNormalizer:
    """
    提供 slug/驼峰/下划线互转，并支持 IRI 拼接
    """

    _non_alnum = re.compile(r"[^0-9a-zA-Z]+")

    def __init__(self, domain: str, version: str) -> None:
        self.domain = domain.lower()
        self.version = version

    # ---------- 内部辅助 ---------
    @staticmethod
    def _slug(text: str) -> str:
        text = unicodedata.normalize("NFKD", text)
        text = NameNormalizer._non_alnum.sub("_", text)
        return re.sub(r"_+", "_", text).strip("_")

    # ---------- 公共接口 ---------
    def iri(self, name: str) -> str:
        """
        生成统一 IRI: <domain>:<version>/<slug>
        """
        slug = self._slug(name)
        return f"{self.domain}:{self.version}/{slug}"

    def normalize_class(self, cls: dict[str, Any]) -> None:
        """在原 dict 内部增补 'iri' 字段"""
        cls["iri"] = self.iri(cls["name"])
        # stereotypes 列表统一小写
        if "stereotypes" in cls and isinstance(cls["stereotypes"], list):
            cls["stereotypes"] = [s.lower() for s in cls["stereotypes"]]

    def normalize_attribute(self, attr: dict[str, Any], parent_cls: str) -> None:
        attr_id = f"{parent_cls}/{attr['name']}"
        attr["iri"] = self.iri(attr_id)
        attr["is_xml_attribute"] = bool(attr.get("is_xml_attribute", False))


class PrefixManager:
    """
    管理多域前缀（AUTOSAR, opcua, dds…）
    """

    def __init__(self) -> None:
        self._prefix_map: dict[str, str] = {}

    def register(self, domain: str, base_iri: str) -> None:
        self._prefix_map[domain.lower()] = base_iri.rstrip("/")

    def get(self, domain: str) -> str:
        return self._prefix_map[domain.lower()]

    # For RDF serialization
    def to_turtle_prefixes(self) -> str:
        return "\n".join(f"@prefix {k}: <{v}/> ." for k, v in self._prefix_map.items())


# ----------------- 便捷批量工具 -----------------


def normalize_metadata(mdata: dict[str, Any], *, domain: str, version: str) -> dict[str, Any]:
    """
    遍历 metadata 所有 class/attribute/enum/literal
    添加 IRI、统一大小写，供后续构图
    """
    norm = NameNormalizer(domain=domain, version=version)

    # groups → Class
    for group in mdata.get("groups", {}).values():
        norm.normalize_class(group)
        for elem in group.get("elements", []):
            norm.normalize_attribute(elem, parent_cls=group["name"])

    # complexTypes 也视作 Class
    for ctype in mdata.get("complexTypes", {}).values():
        norm.normalize_class(ctype)
        for attr in ctype.get("attributes", []):
            norm.normalize_attribute(attr, parent_cls=ctype["name"])

    # simpleTypes → Enum + EnumLiteral
    for stype in mdata.get("simpleTypes", {}).values():
        stype["iri"] = norm.iri(stype["name"])
        enums = stype.get("enumerations", [])
        for idx, lit in enumerate(enums):
            if isinstance(lit, dict):
                value = lit.get("value") or f"ENUM_{idx}"
            else:
                value = lit
            enums[idx] = {"value": value, "iri": norm.iri(f"{stype['name']}/{value}")}

    logger.info("元数据规范化完成 (domain=%s, version=%s)", domain, version)
    return mdata
