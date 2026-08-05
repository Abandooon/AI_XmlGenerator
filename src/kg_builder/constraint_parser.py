"""
解析结构化约束，生成 :Constraint 节点及内部层标签
====================================================
• 按 constraint_type / id_type → layer label
• 输出节点列表，边 (:PARENT_OF, :REFERS_TO) 由 EdgeBuilder 追加
"""

from __future__ import annotations

from typing import Any, Dict

from utils.logger import get_logger

logger = get_logger(__name__)


ConstraintNode = Dict[str, Any]


# ---------- 约束层标签映射 ----------
_LAYER_MAP: dict[str, str] = {
    # constraint_type → 图层标签
    "cardinality": "ModelOCL",
    "relationship": "ModelOCL",
    "existence": "ModelOCL",
    "value_restriction": "DataType",
    "format": "DataType",
    "definition": "Documentation",
    "naming_convention": "Documentation",
    "xml_instantiation_example": "Documentation",
    "behavioral": "Production",
    "ordering": "Production",
    # 其余默认根据 id_type 决定
}


class ConstraintGraphBuilder:
    """把 extracted_constraints 列表转 :Constraint 节点列表"""

    def __init__(self, domain: str, version: str) -> None:
        self.domain = domain.lower()
        self.version = version

    # ---- 主入口 ----
    def build(self, constraints: list[dict[str, Any]]) -> list[ConstraintNode]:
        logger.info("开始解析约束 (%d 条)", len(constraints))
        nodes: list[ConstraintNode] = []
        for item in constraints:
            node = self._create_constraint_node(item)
            nodes.append(node)
        logger.info("约束节点构建完成")
        return nodes

    # ---- 内部方法 ----
    def _create_constraint_node(self, raw: dict[str, Any]) -> ConstraintNode:
        cid = raw["id"]
        iri = f"{self.domain}:{self.version}/constr/{cid}"

        layer_label = self._decide_layer(raw)

        node: ConstraintNode = {
            "id": iri,
            "label": f"Constraint;{layer_label}",  # 多标签使用分号分隔
            "cid": cid,
            "title": raw.get("title", ""),
            "id_type": raw["id_type"],
            "constraint_type": raw["constraint_type"],
            "is_active": raw.get("is_active", True),
            "expression": raw.get("expression", ""),
            "value": raw.get("value"),
            "scope_path": raw.get("scope_path", []),
            "targets": raw.get("targets", []),
            "references": raw.get("references", []),
        }
        return node

    def _decide_layer(self, raw: dict[str, Any]) -> str:
        """根据 constraint_type / id_type 决定层标签"""
        ctype = raw["constraint_type"]
        if ctype in _LAYER_MAP:
            return _LAYER_MAP[ctype]
        # Fallback by id_type
        id_type = raw["id_type"]
        if id_type.startswith("additional"):
            return "Documentation"
        if id_type == "example":
            return "Documentation"
        # 默认放 ModelOCL，保守不影响验证
        return "ModelOCL"
