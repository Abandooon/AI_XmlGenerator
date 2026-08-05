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

from typing import Any, Tuple

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
        parent_index: dict[str, list[str]]
    ) -> None:
        self.cls_idx = class_index
        self.attr_idx = attr_index
        self.enum_idx = enum_index
        self.lit_idx = literal_index
        self.parent_idx = parent_index

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

    # ---------- 构造 CONSTRAINS / APPLIES_TO_CLASS ----------
    def _build_constrains_edges(self, node: dict[str, Any], c_iri: str) -> list[Edge]:
        edges: list[Edge] = []
        for tgt in node.get("targets", []):
            cls_name = tgt["targetEntityName"]
            attrs = tgt.get("targetAttributes", [])
            etype = tgt["entityType"]
            if etype != "class":
                continue  # 其他实体类型此处略
            cls_iri = self.cls_idx.get(cls_name)
            if not cls_iri:
                raise MissingTargetError(f"找不到目标类 {cls_name}")
            # _classLevel 直接连类节点
            if attrs == ["_classLevel"]:
                edges.append((c_iri, "CONSTRAINS", cls_iri))
                continue
            for a in attrs:
                if a == "_classLevel":  # ← ② 双保险，遇到也跳过
                    continue
                key = f"{cls_name}/{a}"
                a_iri = self.attr_idx.get(key)
                # ① 本类未声明 → 回溯祖先
                if not a_iri:
                    anc = self._find_ancestor_with_attr(cls_name, a)
                    if not anc:
                        raise MissingTargetError(f"{cls_name}.{a} 不存在")
                    a_iri = self.attr_idx[f"{anc}/{a}"]
                    edges.append((c_iri, "CONSTRAINS", a_iri))
                    edges.append((c_iri, "APPLIES_TO_CLASS", cls_iri))
                    continue
                # ② 本类命中
                edges.append((c_iri, "CONSTRAINS", a_iri))
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


    # ------- 多继承回溯 -------
    def _find_ancestor_with_attr(self, cls: str, attr: str) -> str | None:
        visited: set[str] = set()
        stack: list[str] = [cls]  # DFS；广度同理

        while stack:
            cur = stack.pop()
            if cur in visited:
                continue
            visited.add(cur)

            if f"{cur}/{attr}" in self.attr_idx:
                return cur  # 命中

            stack.extend(self.parent_idx.get(cur, []))
        return None
