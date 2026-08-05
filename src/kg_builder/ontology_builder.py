"""
Ontology Graph Builder – refactored (v1.1)
=========================================
✅ 补全 `parentClass` / `ownerClass` 字段，解决 CLI KeyError。

变更摘要
---------
1. **Attribute 节点** 现在包含：
   ```python
   {
       "parentClass": <物理宿主类名>,
       "ownerClass" : <逻辑拥有者类名>
   }
   ```
   逻辑：
   - `parentClass` = 创建 attribute 时传入的父节点名称（物理所在类 / AttrGroup）。
   - `ownerClass`  = `attr["ownerClass"]` 或 `qualifiedName` 前缀；若都缺省，则退化为 `parentClass`。
2. **_create_attribute** 函数改写，自动读取父节点 `name`。
3. 版本号 bump 至 1.1，并保留其余逻辑不变。
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from utils.logger import get_logger

logger = get_logger(__name__)

Node = Dict[str, Any]
Edge = Tuple[str, str, str]
_slug = re.compile(r"[^0-9A-Za-z]+")

def slug(txt: str) -> str:
    return _slug.sub("_", txt).strip("_")


def ensure_iter(x: Any) -> List[Any]:
    if x is None:
        return []
    if isinstance(x, (list, tuple, set)):
        return list(x)
    return [x]


class OntologyGraphBuilder:
    """Two-pass ontology builder with FULL label coverage (v1.1)."""

    def __init__(self) -> None:
        self._nodes: Dict[str, Node] = {}
        self._edges: List[Edge] = []
        self._class_idx: Dict[str, str] = {}
        self._attrgroup_idx: Dict[str, str] = {}
        self._package_idx: Dict[Tuple[str, ...], str] = {}
        self._enum_idx: Dict[str, str] = {}

    # ------------------------------------------------------------
    # public API
    # ------------------------------------------------------------
    def build(self, meta: Dict[str, Any]) -> Tuple[List[Node], List[Edge]]:
        logger.info("开始构建本体层图 (v1.1)")

        # pass-1  创建节点
        self._pass_class_nodes(meta.get("groups", {}), source="group", meta=meta)
        self._pass_class_nodes(meta.get("complexTypes", {}), source="ctype", meta=meta)
        self._pass_class_nodes(meta.get("extract_inner_class", {}), source="inner", meta=meta)
        self._handle_simple_types(meta.get("simpleTypes", {}))

        # pass-2  连接边
        self._wire_group_relationships(meta.get("groups", {}))
        self._wire_complex_relationships(meta.get("complexTypes", {}))
        self._wire_inline_expands(meta.get("groups", {}))

        self._wire_attr_type_edges()

        logger.info("本体层节点 %d，边 %d", len(self._nodes), len(self._edges))
        return list(self._nodes.values()), self._edges

    # ------------------------------------------------------------
    # helpers – nodes & edges
    # ------------------------------------------------------------
    def _add_node(self, iri: str, label: str, props: dict[str, Any]) -> None:
        self._nodes.setdefault(iri, {"id": iri, "label": label}).update(props)

    def _edge_exists(self, s: str, r: str, e: str) -> bool:
        return (s, r, e) in self._edges

    def _add_edge(self, s: str, r: str, e: str) -> None:
        if s == e:
            return  # 自环无意义
        if self._edge_exists(s, r, e):
            return
        self._edges.append((s, r, e))

    # ------------------------------------------------------------
    # pass-1  group / complex / inner classes -----> CLASS nodes
    # ------------------------------------------------------------
    def _pass_class_nodes(self, classes: Dict[str, Any], *, source: str, meta: Dict[str, Any]) -> None:
        for cls in classes.values():
            iri = cls["iri"]
            self._class_idx[cls["name"]] = iri
            abs_raw = cls.get("abstract", False)
            is_abs = (abs_raw is True) or (str(abs_raw).strip().lower() in {"true", "1", "yes"})
            class_props = {
                "name": cls["name"],
                "xml_tag": cls.get("xml_tag", ""),
                "description": cls.get("description", ""),
                "isComplexType": source == "ctype",
                "isInnerClassType": source == "inner",
                "isAttribute": cls.get("isAttribute", False),
                # 新增：抽象标记（保留两个键，便于查询兼容）
                "isAbstract": is_abs,
                "abstract": is_abs,
            }
            # Optional XSD models are canonical JSON strings because Neo4j
            # properties cannot contain nested maps/lists of maps.
            for xsd_field in (
                "xsd_group_model_json", "xsd_complex_type_model_json",
                "xsd_effective_model_json", "xsd_content_models_json",
                "xsd_owner_ids_json", "xsd_source_sha256",
                "xsd_model_sha256", "xsd_model_version",
            ):
                if cls.get(xsd_field) not in (None, ""):
                    class_props[xsd_field] = cls[xsd_field]
            self._add_node(iri, "Class", class_props)
            # self._add_node(iri, "Class", {
            #     "name": cls["name"],
            #     "xml_tag": cls.get("xml_tag", ""),
            #     "description": cls.get("description", ""),
            #     "isComplexType": source == "ctype",
            #     "isInnerClassType": source == "inner",
            #     "isAttribute": cls.get("isAttribute", False),
            # })

            # Package tree
            self._attach_package(cls.get("Package", []), iri)

            # Attribute & element nodes
            for key in ("attributes", "elements"):
                for attr in ensure_iter(cls.get(key)):
                    self._create_attribute(attr, iri)

            # AttributeGroup refs
            for ag in ensure_iter(cls.get("attributeGroups")):
                ag_iri = self._get_or_create_attrgroup(ag, meta)
                self._add_edge(iri, "HAS_ATTR_GROUP", ag_iri)

            # Content-Variant relation
            if cls["name"].endswith("Content"):
                base = cls["name"][:-7]
                if base in self._class_idx:
                    self._add_edge(iri, "VARIANT_OF", self._class_idx[base])

    # ------------------------------------------------------------
    # package helpers
    # ------------------------------------------------------------
    def _attach_package(self, pkg_path: List[str], cls_iri: str) -> None:
        if not pkg_path:
            return
        path, parent_iri = [], None
        for seg in pkg_path:
            path.append(seg)
            tup = tuple(path)
            if tup not in self._package_idx:
                iri = f"pkg:/{'/'.join(slug(p) for p in path)}"
                self._package_idx[tup] = iri
                self._add_node(iri, "Package", {"name": seg, "level": len(path)})
                if parent_iri:
                    self._add_edge(parent_iri, "HAS_CHILD", iri)
            parent_iri = self._package_idx[tup]
        self._add_edge(cls_iri, "IN_PACKAGE", parent_iri)

    # ------------------------------------------------------------
    # attribute group helpers
    # ------------------------------------------------------------
    def _get_or_create_attrgroup(self, name: str, meta: Dict[str, Any]) -> str:
        if not name:
            return ""  # ignore empty
        if name in self._attrgroup_idx:
            return self._attrgroup_idx[name]
        iri = f"attrgrp:{slug(name)}"
        self._attrgroup_idx[name] = iri
        self._add_node(iri, "AttrGroup", {"name": name})

        # materialize common attributes onto group node
        for attr in ensure_iter(meta.get("attributeGroups", {}).get(name)):
            self._create_attribute(attr, iri, edge_type="HAS_ATTRIBUTE")
        return iri

    def _get_or_create_stub_class(self, name: str) -> str:
        if name in self._class_idx:
            return self._class_idx[name]
        iri = f"stub:{slug(name)}"
        self._class_idx[name] = iri
        self._add_node(iri, "ClassStub", {"name": name})
        return iri

    # ------------------------------------------------------------
    # pass-2  relationships
    # ------------------------------------------------------------
    def _wire_group_relationships(self, groups: Dict[str, Any]) -> None:
        for g in groups.values():
            src = self._class_idx[g["name"]]
            # inheritance
            for parent in ensure_iter(g.get("generalization")):
                if parent in self._class_idx:
                    self._add_edge(src, "SUBCLASS_OF", self._class_idx[parent])
            # composition / aggregation
            for child in ensure_iter(g.get("childs")):
                if child in self._class_idx:
                    self._add_edge(src, "HAS_CHILD", self._class_idx[child])
            # association
            for ac_from in ensure_iter(g.get("ClassAssociatedFrom")):
                if ac_from in self._class_idx:
                    self._add_edge(self._class_idx[ac_from], "ASSOCIATED_FROM", src)
            for ac_to in ensure_iter(g.get("ClassAssociatedTo")):
                if ac_to in self._class_idx:
                    self._add_edge(self._class_idx[ac_to], "ASSOCIATED_TO", src)

    def _wire_inline_expands(self, groups: Dict[str, Any]) -> None:
        for g in groups.values():
            src = self._class_idx[g["name"]]
            for tgt in ensure_iter(g.get("xsdInlines")):
                tgt_iri = self._get_or_create_stub_class(tgt)
                self._add_edge(src, "INLINE_EXPANDS", tgt_iri)

    def _wire_complex_relationships(self, ctypes: Dict[str, Any]) -> None:
        for ct in ctypes.values():
            if (p := ct.get("extends")) and p in self._class_idx:
                self._add_edge(self._class_idx[ct["name"]], "SUBCLASS_OF", self._class_idx[p])

    # ------------------------------------------------------------
    # simpleTypes (Enum)
    # ------------------------------------------------------------
    def _handle_simple_types(self, stypes: Dict[str, Any]) -> None:
        for st in stypes.values():
            enum_iri = st["iri"]
            self._enum_idx[st["name"]] = enum_iri
            self._add_node(enum_iri, "Enum", {
                "name": st["name"],
                "baseType": st.get("base"),
                "isPrimitive": st.get("isPrimitiveType", False),
                "pattern": st.get("pattern", ""),
                "xml_tag": st.get("xml_tag", ""),
            })
            for lit in ensure_iter(st.get("enumerations")):
                lit_iri = lit["iri"]
                self._add_node(lit_iri, "EnumLiteral", {
                    "value": lit["value"],
                })
                self._add_edge(enum_iri, "HAS_LITERAL", lit_iri)

    # ------------------------------------------------------------
    # attribute nodes
    # ------------------------------------------------------------
    def _create_attribute(self, attr: Dict[str, Any], parent_iri: str, *, edge_type: str = "HAS_ATTRIBUTE") -> None:
        if not attr:
            return
        attr_iri = attr.get("iri") or f"attr:{slug(attr.get('qualifiedName', attr['name']))}"

        # 检查是否已存在该属性节点
        if attr_iri in self._nodes:
            # 如果已经存在，则不创建新节点，而是更新现有节点
            return

        local_name = attr.get("qualifiedName", attr["name"]).split(".")[-1]

        # ---- 取父节点名称供 parentClass ----
        parent_node = self._nodes.get(parent_iri, {})
        parent_name = parent_node.get("name", "")

        # ownerClass 推断：显式 > qualifiedName 前缀 > parent
        owner_cls = (
            attr.get("ownerClass")
            or (attr.get("qualifiedName", "").split(".", 1)[0] if attr.get("qualifiedName") else "")
            or parent_name
        )

        self._add_node(attr_iri, "Attribute", {
            "name": local_name,
            "qualifiedName": attr.get("qualifiedName"),
            "type": attr.get("type", ""),
            "isXmlAttr": attr.get("is_xml_attribute", False),
            "minOccurs": attr.get("pure_minOccurs"),
            "maxOccurs": attr.get("pure_maxOccurs"),
            "xml_tag": attr.get("xml_tag", ""),
            "xml_wrapper_tag": attr.get("xml_wrapper_tag", ""),
            "latestBindingTime": attr.get("latestBindingTime", ""),
            "description": attr.get("description", ""),
            "stereotypes": attr.get("stereotypes", []),
            "annotation": attr.get("annotation", ""),
            "isPrimitiveType": attr.get("isPrimitiveType", False),
            # ---- 新增的两个字段 ----
            "parentClass": parent_name,
            "ownerClass": owner_cls,
        })
        self._add_edge(parent_iri, edge_type, attr_iri)

        # link attr type to Enum (if any)
        typ = attr.get("type")
        # 如果类型是枚举类型，则建立类型与枚举的连接
        if typ in self._enum_idx:
            self._add_edge(attr_iri, "TYPE_OF", self._enum_idx[typ])
        # 如果类型是复杂类型（complex type），则建立类型与类的连接
        elif typ in self._class_idx:
            self._add_edge(attr_iri, "TYPE_OF", self._class_idx[typ])

    def _wire_attr_type_edges(self):
        for n in self._nodes.values():
            if n["label"] != "Attribute":
                continue
            typ = n.get("type")
            if not typ:
                continue
            src = n["id"]

            if typ in self._enum_idx and not self._edge_exists(src, "TYPE_OF", self._enum_idx[typ]):
                self._add_edge(src, "TYPE_OF", self._enum_idx[typ])

            if typ in self._class_idx and not self._edge_exists(src, "TYPE_OF", self._class_idx[typ]):
                self._add_edge(src, "TYPE_OF", self._class_idx[typ])

