from typing import Any, Optional

from models import (
    ConstraintRaw, ConstraintStructured, Entity,
    ConditionExpression, ProhibitionExpression,
    NonOverlapExpression, PermissionExpression
)


class ConstraintMapper:
    def __init__(self):
        pass

    def map_to_structured(self, constraint: ConstraintRaw, logic_analysis: dict[str, Any]) -> ConstraintStructured:
        """将原始约束映射为结构化约束"""
        constraint_type = logic_analysis.get("constraint_type", "Generic")

        # 创建基本结构化约束
        structured = ConstraintStructured(
            id=constraint.id,
            type=constraint_type,
            body=constraint.body,
            explanation=constraint.explanation,
            source_id=constraint.id,
            reference_id=constraint.reference_id
        )

        # 根据约束类型进行特定映射
        if constraint_type == "ConditionalProhibition":
            structured = self._map_conditional_prohibition(structured, logic_analysis)
        elif constraint_type == "NonOverlapConstraint":
            structured = self._map_non_overlap_constraint(structured, logic_analysis)
        elif constraint_type == "Permission":
            structured = self._map_permission(structured, logic_analysis)
        elif constraint_type == "Prohibition":
            structured = self._map_prohibition(structured, logic_analysis)
        elif constraint_type == "Requirement":
            structured = self._map_requirement(structured, logic_analysis)

        return structured

    def _map_conditional_prohibition(self, structured: ConstraintStructured,
                                     logic_analysis: dict[str, Any]) -> ConstraintStructured:
        """映射条件禁止约束"""
        # 处理条件
        conditions = logic_analysis.get("conditions", [])
        if conditions:
            if len(conditions) == 1:
                condition = conditions[0]
                structured.condition = ConditionExpression(
                    class_name=condition.get("parent_class", ""),
                    attribute=condition.get("entity", "").split(".")[-1] if "." in condition.get("entity",
                                                                                                 "") else condition.get(
                        "entity", ""),
                    operation=condition.get("operation", "=="),
                    value=condition.get("value", ""),
                    scope=condition.get("scope")
                )
            else:
                structured.condition = [
                    ConditionExpression(
                        class_name=cond.get("parent_class", ""),
                        attribute=cond.get("entity", "").split(".")[-1] if "." in cond.get("entity", "") else cond.get(
                            "entity", ""),
                        operation=cond.get("operation", "=="),
                        value=cond.get("value", ""),
                        scope=cond.get("scope")
                    )
                    for cond in conditions
                ]

        # 处理禁止
        prohibitions = logic_analysis.get("prohibitions", [])
        if prohibitions:
            structured.prohibition = [
                ProhibitionExpression(
                    class_name=prohib.get("parent_class", ""),
                    attribute=prohib.get("entity", "").split(".")[-1] if "." in prohib.get("entity",
                                                                                           "") else prohib.get("entity",
                                                                                                               ""),
                    operation=prohib.get("operation", "shall_not"),
                    scope=prohib.get("scope")
                )
                for prohib in prohibitions
            ]

        return structured

    def _map_non_overlap_constraint(self, structured: ConstraintStructured,
                                    logic_analysis: dict[str, Any]) -> ConstraintStructured:
        """映射非重叠约束"""
        non_overlapping = logic_analysis.get("non_overlapping")
        if non_overlapping:
            structured.non_overlapping = NonOverlapExpression(
                attributes=non_overlapping.get("attributes", []),
                scope=non_overlapping.get("scope", "")
            )

        return structured

    def _map_permission(self, structured: ConstraintStructured, logic_analysis: dict[str, Any]) -> ConstraintStructured:
        """映射许可约束"""
        permission = logic_analysis.get("permissions")
        if permission:
            structured.permission = PermissionExpression(
                attributes=permission.get("attributes", []),
                permission=permission.get("permission", "allowed"),
                conditions=permission.get("conditions", [])
            )

        return structured

    def _map_prohibition(self, structured: ConstraintStructured,
                         logic_analysis: dict[str, Any]) -> ConstraintStructured:
        """映射一般禁止约束"""
        # 处理禁止
        prohibitions = logic_analysis.get("prohibitions", [])
        if prohibitions:
            structured.prohibition = [
                ProhibitionExpression(
                    class_name=prohib.get("parent_class", ""),
                    attribute=prohib.get("entity", "").split(".")[-1] if "." in prohib.get("entity",
                                                                                           "") else prohib.get("entity",
                                                                                                               ""),
                    operation=prohib.get("operation", "shall_not"),
                    scope=prohib.get("scope")
                )
                for prohib in prohibitions
            ]

        return structured

    def _map_requirement(self, structured: ConstraintStructured,
                         logic_analysis: dict[str, Any]) -> ConstraintStructured:
        """映射要求约束"""
        # 要求约束可能没有明确的结构，保留原始数据
        structured.additional_data = {
            "conditions": logic_analysis.get("conditions", []),
            "scope": logic_analysis.get("scope")
        }

        return structured