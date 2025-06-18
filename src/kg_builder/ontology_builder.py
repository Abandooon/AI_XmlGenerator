"""
Ontology Graph Builder (two-pass) + AttrGroup & Package
----------------------------------------------------
• pass-1:  创建 Class / Attribute / Enum / AttrGroup / Package 节点
• pass-2:  连接 SUBCLASS_OF / HAS_CHILD / ASSOCIATED_* /
           HAS_ATTR_GROUP / IN_PACKAGE / VARIANT_OF
"""

from __future__ import annotations
from typing import Any, Dict, List, Tuple
import re
from utils.logger import get_logger

logger = get_logger(__name__)
Node = Dict[str, Any]
Edge = Tuple[str, str, str]
_slug = re.compile(r"[^0-9A-Za-z]+")


def slug(txt: str) -> str:
    return _slug.sub("_", txt).strip("_")


class OntologyGraphBuilder:
    def __init__(self) -> None:
        self._nodes: Dict[str, Node] = {}
        self._edges: List[Edge] = []
        self._class_idx: Dict[str, str] = {}
        self._attrgroup_idx: Dict[str, str] = {}      # group → iri
        self._package_idx: Dict[Tuple[str, ...], str] = {}  # pkg path → iri

    # ------------ public ------------
    def build(self, meta: dict[str, Any]) -> Tuple[List[Node], List[Edge]]:
        logger.info("开始构建本体层图")

        self._pass_class_nodes(meta.get("groups", {}), source="group")
        self._pass_class_nodes(meta.get("complexTypes", {}), source="ctype")
        self._pass_class_nodes(meta.get("extract_inner_class", {}), source="inner")
        self._handle_simple_types(meta.get("simpleTypes", {}))

        self._wire_group_relationships(meta.get("groups", {}))
        self._wire_complex_relationships(meta.get("complexTypes", {}))
        self._wire_inline_expands(meta.get("groups", {}))

        logger.info("本体层节点 %d，边 %d", len(self._nodes), len(self._edges))
        return list(self._nodes.values()), self._edges

    # ------------ utilities ------------
    def _add_node(self, iri: str, label: str, props: dict[str, Any]) -> None:
        self._nodes.setdefault(iri, {"id": iri, "label": label}).update(props)

    def _add_edge(self, s: str, r: str, e: str) -> None:
        self._edges.append((s, r, e))

    # ------------ pass-1 ------------
    def _pass_class_nodes(self, classes: dict[str, Any], *, source: str) -> None:
        for cls in classes.values():
            iri = cls["iri"]
            self._class_idx[cls["name"]] = iri
            self._add_node(iri, "Class", {"name": cls["name"]})

            # VARIANT_OF  (Content ↔ Base)
            if cls["name"].endswith("Content"):
                base = cls["name"][:-7]
                if base in self._class_idx:
                    self._add_edge(iri, "VARIANT_OF", self._class_idx[base])

            # ---------- Package ----------
            self._attach_package(cls.get("Package", []), iri)

            # ---------- Attributes ----------
            for lst in ("attributes", "elements"):
                for attr in cls.get(lst, []):
                    self._create_attribute(attr, iri)

            # ---------- attributeGroups ----------
            ag_raw = cls.get("attributeGroups", [])
            if isinstance(ag_raw, str):
                ag_names = [n.strip() for n in ag_raw.split(",") if n.strip()]
            else:
                ag_names = ag_raw
            for ag in ag_names:
                ag_iri = self._get_or_create_attrgroup(ag, cls, meta=classes)  # 传 meta 以便拿属性
                self._add_edge(iri, "HAS_ATTR_GROUP", ag_iri)

    # ------------ Package helpers ------------
    def _attach_package(self, pkg_list: list[str], cls_iri: str) -> None:
        if not pkg_list:
            return
        path, parent_iri = [], None
        for seg in pkg_list:
            path.append(seg)
            tup = tuple(path)
            if tup not in self._package_idx:
                pkg_iri = f"pkg:/{'/'.join(slug(p) for p in path)}"
                self._package_idx[tup] = pkg_iri
                self._add_node(pkg_iri, "Package", {"name": seg, "level": len(path)})
                if parent_iri:
                    self._add_edge(parent_iri, "HAS_CHILD", pkg_iri)
            parent_iri = self._package_idx[tup]
        self._add_edge(cls_iri, "IN_PACKAGE", parent_iri)

    # ------------ AttrGroup helpers ------------
    def _get_or_create_attrgroup(self, name: str, cls: dict[str, Any], meta: dict[str, Any]) -> str:
        if name in self._attrgroup_idx:
            return self._attrgroup_idx[name]
        iri = f"attrgrp:{slug(name)}"
        self._attrgroup_idx[name] = iri
        self._add_node(iri, "AttrGroup", {"name": name})

        # 将公共属性落到组节点，仅一次
        grp_attrs = meta.get("attributeGroups", {}).get(name, [])
        for a in grp_attrs:
            self._create_attribute(a, iri, edge_type="HAS_ATTRIBUTE")
        return iri

    def _get_or_create_stub_class(self, name: str) -> str:
        """若类尚未建节点，则创建一个 ClassStub；返回其 iri"""
        if name in self._class_idx:
            return self._class_idx[name]
        iri = f"stub:{slug(name)}"
        if iri not in self._nodes:
            self._add_node(iri, "ClassStub", {"name": name})
        self._class_idx[name] = iri
        return iri

    # ------------ pass-2 relationships ------------
    def _wire_group_relationships(self, groups: dict[str, Any]) -> None:
        for g in groups.values():
            src = self._class_idx[g["name"]]
            for parent in g.get("generalization", []):
                if parent in self._class_idx:
                    self._add_edge(src, "SUBCLASS_OF", self._class_idx[parent])
            for child in g.get("childs", []):
                if child in self._class_idx:
                    self._add_edge(src, "HAS_CHILD", self._class_idx[child])
            # for ac_from in g.get("ClassAssociatedFrom", []):
            #     if ac_from in self._class_idx:
            #         self._add_edge(self._class_idx[ac_from], "ASSOCIATED_FROM", src)
            for ac_to in g.get("ClassAssociatedTo", []):
                if ac_to in self._class_idx:
                    self._add_edge(self._class_idx[ac_to], "ASSOCIATED_TO", src)

    def _wire_inline_expands(self, groups: dict[str, Any]) -> None:
        """
        把 groups[*].xsdInlines 转成 (:Class)-[:INLINE_EXPANDS]->(:Class)
        """
        for g in groups.values():
            src_iri = self._class_idx[g["name"]]
            for tgt in g.get("xsdInlines", []):
                tgt_iri = self._get_or_create_stub_class(tgt)
                # 避免自环 & 重复
                if src_iri != tgt_iri and (src_iri, "INLINE_EXPANDS", tgt_iri) not in self._edges:
                    self._add_edge(src_iri, "INLINE_EXPANDS", tgt_iri)

    def _wire_complex_relationships(self, ctypes: dict[str, Any]) -> None:
        for ct in ctypes.values():
            if (p := ct.get("extends")) and p in self._class_idx:
                self._add_edge(self._class_idx[ct["name"]], "SUBCLASS_OF", self._class_idx[p])

    # ------------ simpleTypes ------------
    def _handle_simple_types(self, stypes: dict[str, Any]) -> None:
        for st in stypes.values():
            self._add_node(st["iri"], "Enum", {"name": st["name"]})
            for lit in st.get("enumerations", []):
                self._add_node(lit["iri"], "EnumLiteral", {"value": lit["value"]})
                self._add_edge(st["iri"], "HAS_LITERAL", lit["iri"])

    # ------------ attribute ------------
    def _create_attribute(self, attr: dict[str, Any], parent_iri: str, *, edge_type="HAS_ATTRIBUTE") -> None:
        if "iri" not in attr:
            attr["iri"] = f"stub:{attr.get('qualifiedName', attr['name'])}"
        local = attr.get("qualifiedName", "").split(".", 1)[-1] or attr["name"]
        self._add_node(
            attr["iri"],
            "Attribute",
            {
                "name": local,
                "qualifiedName": attr.get("qualifiedName"),
                "parentClass": attr.get("parentClass"),
                "ownerClass":  attr.get("ownerClass"),

            },
        )
        self._add_edge(parent_iri, edge_type, attr["iri"])
