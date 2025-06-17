"""
根据 Ontology + Constraint 构建语义关系边
====================================================
• 目标：补全
  - :CONSTRAINS
  - :REFERS_TO
  - :IN_SECTION
  - :PARENT_OF (由 scope_path 推断章节层级)
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Tuple

from utils.exceptions import MissingTargetError
from utils.logger import get_logger

logger = get_logger(__name__)

Edge = Tuple[str, str, str]  # (startIRI, relType, endIRI)


class EdgeAssembler:
    """根据已解析实体，生成边"""

    def __init__(
        self,
        *,
        class_index: dict[str, str],
        attr_index: dict[str, str],
        enum_index: dict[str, str],
        literal_index: dict[str, str],
    ) -> None:
        self.cls_idx = class_index
        self.attr_idx = attr_index
        self.enum_idx = enum_index
        self.lit_idx = literal_index

    # ---------------- 对外主接口 ----------------
    def build_edges(
        self,
        constraint_nodes: list[dict[str, Any]],
    ) -> list[Edge]:
        edges: list[Edge] = []
        section_cache: dict[tuple[str, ...], str] = {}

        for node in constraint_nodes:
            c_iri = node["id"]
            # ---- 1) CONSTRAINS ----
            edges += self._build_constrains_edges(node, c_iri)

            # ---- 2) REFERS_TO ----
            for ref in node.get("references", []):
                ref_iri = f"{c_iri.rsplit('/', 1)[0]}/{ref}"
                edges.append((c_iri, "REFERS_TO", ref_iri))

            # ---- 3) IN_SECTION & PARENT_OF ----
            scope_path: list[str] = node.get("scope_path", [])
            if scope_path:
                sec_iri = self._get_or_create_section(scope_path, section_cache)
                edges.append((c_iri, "IN_SECTION", sec_iri))

        logger.info("EdgeAssembler 生成边 %d 条", len(edges))
        return edges

    # ---------------- 私有 ----------------
    def _build_constrains_edges(self, node: dict[str, Any], c_iri: str) -> list[Edge]:
        edges: list[Edge] = []

        for target in node.get("targets", []):
            t_name = target["targetEntityName"]
            attrs = target.get("targetAttributes", [])
            etype = target["entityType"]

            # 获取实体 iri
            if etype == "class":
                base_iri = self.cls_idx.get(t_name)
                if not base_iri:
                    raise MissingTargetError(f"找不到目标类 {t_name}")
                # _classLevel
                if attrs == ["_classLevel"]:
                    edges.append((c_iri, "CONSTRAINS", base_iri))
                else:
                    for a in attrs:
                        a_iri = self.attr_idx.get(f"{t_name}/{a}")
                        if not a_iri:
                            raise MissingTargetError(f"{t_name}.{a} 不存在")
                        edges.append((c_iri, "CONSTRAINS", a_iri))

            elif etype == "enum":
                enum_iri = self.enum_idx.get(t_name)
                if not enum_iri:
                    raise MissingTargetError(f"找不到枚举 {t_name}")
                if attrs == ["_enumLevel"]:
                    edges.append((c_iri, "CONSTRAINS", enum_iri))
                else:
                    for lit in attrs:
                        lit_iri = self.lit_idx.get(f"{t_name}/{lit}")
                        if not lit_iri:
                            raise MissingTargetError(f"{t_name}.{lit} 不存在")
                        edges.append((c_iri, "CONSTRAINS", lit_iri))

            else:  # abstract
                edges.append((c_iri, "CONSTRAINS", f"abstract:{t_name}"))

        return edges

    # ---------------- Section 节点生成 ----------------
    @staticmethod
    def _get_or_create_section(
        path: list[str],
        cache: dict[tuple[str, ...], str],
    ) -> str:
        key = tuple(path)
        if key in cache:
            return cache[key]
        # 构造 iri: doc:sec/Chapter_1/Section_1_1
        slug = "/".join(p.replace(" ", "_") for p in path)
        iri = f"doc:sec/{slug}"
        cache[key] = iri
        return iri
