"""
构建本体层 (Ontology Layer)
====================================================
• 读取由 normalizer 处理后的 metadata dict
• 生成节点 (:Class / :Attribute / :Enum / :EnumLiteral)
  及结构边 (:HAS_ATTRIBUTE, :HAS_LITERAL, :SUBCLASS_OF, :HAS_STEREOTYPE)
• 输出以 Python list / dict 形式暂存，供 EdgeBuilder 批量写 Neo4j
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Tuple

from utils.logger import get_logger

logger = get_logger(__name__)


# ---------- 内部类型别名 ----------
Node = Dict[str, Any]
Edge = Tuple[str, str, str]  # (start_id, edge_type, end_id)


class OntologyGraphBuilder:
    """核心 API: build() 返回 (nodes, edges)"""

    def __init__(self) -> None:
        self._nodes: dict[str, Node] = {}
        self._edges: list[Edge] = []
        # 辅助：class name → iri
        self._class_index: dict[str, str] = {}

    # ------------------ 外部主入口 ------------------
    def build(self, metadata: dict[str, Any]) -> tuple[list[Node], list[Edge]]:
        logger.info("开始构建本体层图")
        self._handle_groups(metadata.get("groups", {}))
        self._handle_complex_types(metadata.get("complexTypes", {}))
        self._handle_simple_types(metadata.get("simpleTypes", {}))

        logger.info("本体层节点 %d，边 %d", len(self._nodes), len(self._edges))
        return list(self._nodes.values()), self._edges

    # ------------------ 私有方法 ------------------
    def _add_node(self, iri: str, label: str, props: dict[str, Any]) -> None:
        if iri in self._nodes:  # 已存在则 merge
            self._nodes[iri].update(props)
        else:
            self._nodes[iri] = {"id": iri, "label": label, **props}

    def _add_edge(self, start: str, rel: str, end: str) -> None:
        self._edges.append((start, rel, end))

    # ---- groups -> Class + Attribute ----
    def _handle_groups(self, groups: dict[str, Any]) -> None:
        for group in groups.values():
            cls_iri = group["iri"]
            self._class_index[group["name"]] = cls_iri

            self._add_node(
                cls_iri,
                label="Class",
                props={
                    "name": group["name"],
                    "abstract": group.get("abstract", "false") == "true",
                    "annotation": group.get("annotation", ""),
                },
            )

            # stereotype 可多值，拆节点或存列表；这里采用列表属性
            if group.get("stereotypes"):
                self._nodes[cls_iri]["stereotypes"] = group["stereotypes"]

            for attr in group.get("elements", []):
                self._create_attribute(attr, cls_iri)

            # 继承
            for super_cls in group.get("generalization", []):
                if super_cls in self._class_index:
                    self._add_edge(cls_iri, "SUBCLASS_OF", self._class_index[super_cls])

    # ---- complexTypes -> 亦视为 Class ----
    def _handle_complex_types(self, ctypes: dict[str, Any]) -> None:
        for ctype in ctypes.values():
            cls_iri = ctype["iri"]
            self._class_index[ctype["name"]] = cls_iri
            # 改到这里了，核对和修改complexTypes的属性

            self._add_node(
                cls_iri,
                label="Class",
                props={
                    "name": ctype["name"],
                    "isComplexType": True,
                    "annotation": ctype.get("annotation", ""),
                },
            )

            for attr in ctype.get("attributes", []):
                self._create_attribute(attr, cls_iri)

            # 继承
            parent = ctype.get("extends")
            if parent and parent in self._class_index:
                self._add_edge(cls_iri, "SUBCLASS_OF", self._class_index[parent])

    # ---- simpleTypes -> Enum + EnumLiteral ----
    def _handle_simple_types(self, stypes: dict[str, Any]) -> None:
        for stype in stypes.values():
            enum_iri = stype["iri"]
            self._add_node(
                enum_iri,
                label="Enum",
                props={
                    "name": stype["name"],
                    "baseType": stype.get("base"),
                    "isPrimitive": stype.get("isPrimitiveType", False),
                    "annotation": stype.get("annotation", ""),
                    "pattern": stype.get("pattern", ""),
                },
            )

            literals: list[dict[str, str]] = stype.get("enumerations", [])
            for lit in literals:
                lit_iri = lit["iri"]
                self._add_node(
                    lit_iri,
                    label="EnumLiteral",
                    props={"value": lit["value"]},
                )
                self._add_edge(enum_iri, "HAS_LITERAL", lit_iri)

    # ---- 公共: 创建 Attribute 节点并连边 ----
    def _create_attribute(self, attr: dict[str, Any], parent_iri: str) -> None:
        attr_iri = attr["iri"]
        self._add_node(
            attr_iri,
            label="Attribute",
            props={
                "name": attr.get("qualifiedName", attr["name"]).split(".")[-1],
                "qualifiedName": attr.get("qualifiedName"),
                "type": attr.get("type", ""),
                "isXmlAttr": attr.get("is_xml_attribute", False),
                "minOccurs": attr.get("pure_minOccurs"),
                "maxOccurs": attr.get("pure_maxOccurs"),
                "xml_tag": attr.get("xml_tag", ""),
                "xml_wrapper_tag": attr.get("xml_wrapper_tag", ""),
                "is_xml_attribute": attr.get("is_xml_attribute", False),
                "latestBindingTime" : attr.get("latestBindingTime", ""),
                "description" : attr.get("description", ""),
                "stereotypes": attr.get("stereotypes", []),
            },
        )
        self._add_edge(parent_iri, "HAS_ATTRIBUTE", attr_iri)
