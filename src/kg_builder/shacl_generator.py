"""
SHACL Shapes 生成器
====================================================
• 将 ModelOCL / DataType 相关约束节点转换为 SHACL Shape
• 支持 cardinality、value_restriction、format 等常见规则
• 产出 Turtle 格式，后续可用 pyshacl 验证
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from rdflib import Graph, Namespace, RDF, RDFS, URIRef, Literal

from utils.logger import get_logger

logger = get_logger(__name__)

SH = Namespace("http://www.w3.org/ns/shacl#")
KG = Namespace("kg:")


class ShapeEmitter:
    """
    调用示例：
    >>> emitter = ShapeEmitter(domain="autosar", version="4.3.1")
    >>> emitter.build(constraint_nodes).serialize("out/shapes.ttl")
    """

    def __init__(self, domain: str, version: str):
        self.domain = domain
        self.version = version
        self.g = Graph()
        self.g.bind("sh", SH)
        self.g.bind("kg", KG)

    # -------- 主入口 --------
    def build(self, constraints: List[Dict[str, Any]]) -> Graph:
        for c in constraints:
            layer = c["label"]
            if "ModelOCL" not in layer and "DataType" not in layer:
                continue  # 仅对这两层生成 SHACL

            self._create_shape(c)

        logger.info("SHACL 生成完成，总计 %d triples", len(self.g))
        return self.g

    # -------- 私有 --------
    def _create_shape(self, c: Dict[str, Any]) -> None:
        shape_uri = URIRef(f"{c['id']}_Shape")
        self.g.add((shape_uri, RDF.type, SH.NodeShape))
        self.g.add((shape_uri, RDFS.label, Literal(c["title"])))

        targets = c.get("targets", [])
        if not targets:
            return

        for tgt in c["targets"]:
            target_cls = tgt["targetEntityName"]
            target_attrs = tgt["targetAttributes"]
            if target_attrs == ["_classLevel"]:
                # 针对类级别约束
                self._add_class_level_rule(shape_uri, target_cls, c)
            else:
                for attr in target_attrs:
                    self._add_attr_level_rule(shape_uri, target_cls, attr, c)

    def _add_class_level_rule(self, shape_uri: URIRef, cls_name: str, c: Dict[str, Any]) -> None:
        self.g.add((shape_uri, SH.targetClass, URIRef(f"kg:{cls_name}")))
        # 示例：仅处理 cardinality=1 的简单场景
        if c["constraint_type"] == "cardinality" and c["value"] == "1":
            self.g.add((shape_uri, SH["qualifiedMinCount"], Literal(1)))

    def _add_attr_level_rule(
        self, shape_uri: URIRef, cls_name: str, attr_name: str, c: Dict[str, Any]
    ) -> None:
        prop_shape = URIRef(f"{shape_uri}_{attr_name}")
        self.g.add((shape_uri, SH.property, prop_shape))
        self.g.add((prop_shape, SH.path, URIRef(f"kg:{cls_name}/{attr_name}")))

        if c["constraint_type"] == "cardinality":
            min_val = c.get("value") or "1"
            self.g.add((prop_shape, SH.minCount, Literal(int(min_val))))
        elif c["constraint_type"] == "value_restriction":
            self.g.add((prop_shape, SH["in"], Literal(c["value"])))
        elif c["constraint_type"] == "format":
            self.g.add((prop_shape, SH.pattern, Literal(c["value"])))
