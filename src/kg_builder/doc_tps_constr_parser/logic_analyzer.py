import re
import spacy
from typing import List, Dict, Any, Optional, Tuple, Union

from models import (
    ConstraintRaw, Entity, ConditionExpression,
    ProhibitionExpression, NonOverlapExpression,
    PermissionExpression
)
from utils import (
    CONDITIONAL_PATTERNS, PROHIBITION_PATTERNS,
    SCOPE_PATTERNS, OVERLAP_PATTERNS
)


class LogicAnalyzer:
    def __init__(self):
        # 加载spaCy模型
        self.nlp = spacy.load("en_core_web_sm")

        # 编译正则表达式
        self.conditional_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in CONDITIONAL_PATTERNS]
        self.prohibition_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in PROHIBITION_PATTERNS]
        self.scope_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in SCOPE_PATTERNS]
        self.overlap_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in OVERLAP_PATTERNS]

    def analyze_constraint_logic(self, constraint: ConstraintRaw, entities: List[Entity]) -> Dict[str, Any]:
        """分析约束的逻辑结构"""
        result = {
            "constraint_type": self._determine_constraint_type(constraint, entities),
            "conditions": self._extract_conditions(constraint, entities),
            "prohibitions": self._extract_prohibitions(constraint, entities),
            "non_overlapping": self._extract_non_overlapping(constraint, entities),
            "permissions": self._extract_permissions(constraint, entities),
            "scope": self._extract_scope(constraint, entities),
        }

        # 移除空值
        return {k: v for k, v in result.items() if v}

    def _determine_constraint_type(self, constraint: ConstraintRaw, entities: List[Entity]) -> str:
        """确定约束类型"""
        body = constraint.body.lower()

        # 检查是否为条件禁止
        if any(re.search(pattern, body) for pattern in self.conditional_patterns) and \
                any(re.search(pattern, body) for pattern in self.prohibition_patterns):
            return "ConditionalProhibition"

        # 检查是否为非重叠约束
        if any(re.search(pattern, body) for pattern in self.overlap_patterns):
            return "NonOverlapConstraint"

        # 检查是否为许可约束
        if "can be" in body or "are allowed" in body or "is allowed" in body:
            return "Permission"

        # 检查是否为一般禁止
        if "shall not" in body or "must not" in body:
            return "Prohibition"

        # 检查是否为强制要求
        if "shall" in body or "must" in body:
            return "Requirement"

        return "Generic"  # 默认类型

    def _extract_conditions(self, constraint: ConstraintRaw, entities: List[Entity]) -> List[Dict[str, Any]]:
        """提取条件表达式"""
        conditions = []
        body = constraint.body

        # 使用正则表达式查找条件模式
        for pattern in self.conditional_patterns:
            matches = pattern.finditer(body)
            for match in matches:
                condition_text = match.group(1)
                value_text = match.group(2) if len(match.groups()) > 1 else None

                # 在条件文本中查找实体
                condition_entity = self._find_entity_in_text(condition_text, entities)
                value_entity = self._find_entity_in_text(value_text, entities) if value_text else None

                if condition_entity:
                    # 构建条件表达式
                    condition = {
                        "text": condition_text,
                        "entity": condition_entity.text,
                        "entity_type": condition_entity.type,
                        "parent_class": condition_entity.parent,
                    }

                    # 如果有值实体，添加到条件中
                    if value_entity:
                        condition["value"] = value_entity.text
                        condition["value_type"] = value_entity.type
                    elif value_text:
                        condition["value"] = value_text

                    # 确定操作符
                    if "is set to" in match.group(0) or "are set to" in match.group(0):
                        condition["operation"] = "=="
                    elif "is not" in match.group(0) or "are not" in match.group(0):
                        condition["operation"] = "!="
                    elif "other than" in match.group(0):
                        condition["operation"] = "!="
                    else:
                        condition["operation"] = "=="  # 默认等于

                    conditions.append(condition)

        return conditions

    def _extract_prohibitions(self, constraint: ConstraintRaw, entities: List[Entity]) -> List[Dict[str, Any]]:
        """提取禁止表达式"""
        prohibitions = []
        body = constraint.body

        # 使用正则表达式查找禁止模式
        for pattern in self.prohibition_patterns:
            matches = pattern.finditer(body)
            for match in matches:
                prohibition_text = match.group(1)

                # 在禁止文本中查找实体
                prohibition_entity = self._find_entity_in_text(prohibition_text, entities)

                if prohibition_entity:
                    # 构建禁止表达式
                    prohibition = {
                        "text": prohibition_text,
                        "entity": prohibition_entity.text,
                        "entity_type": prohibition_entity.type,
                        "parent_class": prohibition_entity.parent,
                    }

                    # 确定操作
                    if "shall not be set" in match.group(0):
                        prohibition["operation"] = "shall_not_be_set"
                    elif "shall not overlap" in match.group(0):
                        prohibition["operation"] = "shall_not_overlap"
                    else:
                        prohibition["operation"] = "shall_not"  # 默认禁止

                    # 检查范围词汇
                    if "for any" in match.group(0) or "for all" in match.group(0):
                        prohibition["scope"] = "any"
                    elif "within one" in match.group(0) or "within a" in match.group(0):
                        prohibition["scope"] = "one"

                    prohibitions.append(prohibition)

        return prohibitions

    def _extract_non_overlapping(self, constraint: ConstraintRaw, entities: List[Entity]) -> Optional[Dict[str, Any]]:
        """提取不重叠约束"""
        body = constraint.body

        # 检查是否为不重叠约束
        for pattern in self.overlap_patterns:
            match = pattern.search(body)
            if match:
                overlap_text = match.group(1)

                # 查找涉及的实体
                related_entities = [e for e in entities if e.text in overlap_text]

                if related_entities:
                    # 构建不重叠表达式
                    non_overlapping = {
                        "text": overlap_text,
                        "attributes": []
                    }

                    for entity in related_entities:
                        if entity.type in ["ATTRIBUTE", "ATTRIBUTE_PATH"]:
                            non_overlapping["attributes"].append({
                                "class": entity.parent,
                                "attribute": entity.text.split(".")[-1] if "." in entity.text else entity.text
                            })

                    # 确定范围
                    for scope_pattern in self.scope_patterns:
                        scope_match = scope_pattern.search(body)
                        if scope_match:
                            scope_text = scope_match.group(1)
                            scope_entity = self._find_entity_in_text(scope_text, entities)
                            if scope_entity and scope_entity.type == "CLASS":
                                non_overlapping["scope"] = f"within_one_{scope_entity.text}"

                    return non_overlapping

        return None

    def _extract_permissions(self, constraint: ConstraintRaw, entities: List[Entity]) -> Optional[Dict[str, Any]]:
        """提取许可表达式"""
        body = constraint.body

        # 检查是否为许可约束
        if "can be" in body or "are allowed" in body or "is allowed" in body:
            # 查找涉及的属性实体
            permission_entities = [e for e in entities if e.type in ["ATTRIBUTE", "ATTRIBUTE_PATH"]]

            if permission_entities:
                # 构建许可表达式
                permission = {
                    "attributes": [],
                    "permission": "arbitrary_values" if "arbitrary" in body else "allowed"
                }

                for entity in permission_entities:
                    permission["attributes"].append({
                        "class": entity.parent,
                        "attribute": entity.text.split(".")[-1] if "." in entity.text else entity.text
                    })

                # 提取条件约束引用
                constraint_refs = re.findall(r"\[(constr|TPS)_(\d+)\]", body)
                if constraint_refs:
                    permission["conditions"] = [f"{ref[0]}_{ref[1]}" for ref in constraint_refs]

                return permission

        return None

    def _extract_scope(self, constraint: ConstraintRaw, entities: List[Entity]) -> Optional[str]:
        """提取约束的作用范围"""
        body = constraint.body

        for pattern in self.scope_patterns:
            match = pattern.search(body)
            if match:
                scope_text = match.group(1)
                scope_entity = self._find_entity_in_text(scope_text, entities)
                if scope_entity and scope_entity.type == "CLASS":
                    return f"within_one_{scope_entity.text}"

        return None

    def _find_entity_in_text(self, text: str, entities: List[Entity]) -> Optional[Entity]:
        """在文本片段中查找实体"""
        if not text:
            return None

        # 首先尝试精确匹配
        for entity in entities:
            if entity.text.lower() == text.lower():
                return entity

        # 然后尝试部分匹配
        for entity in entities:
            if entity.text.lower() in text.lower():
                return entity

        return None