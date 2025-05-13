import re
import spacy
from typing import Optional, Any, Union, List, Dict, Tuple

from models import ConstraintRaw, Entity

# 定义识别模式
CONDITIONAL_PATTERNS = [
    r'if\s+(.*?)\s+(?:is|are)\s+(.*?)[,\.]',
    r'when\s+(.*?)\s+(?:is|are)\s+(.*?)[,\.]',
    r'in case\s+(.*?)\s+(?:is|are)\s+(.*?)[,\.]',
    r'provided that\s+(.*?)\s+(?:is|are)\s+(.*?)[,\.]',
    r'(.*?)\s+(?:is|are) set to\s+(.*?)[,\.]',
    r'(.*?)\s+(?:equals|equal to)\s+(.*?)[,\.]'
]

PROHIBITION_PATTERNS = [
    r'shall not\s+(.*?)[,\.]',
    r'must not\s+(.*?)[,\.]',
    r'(.*?)\s+(?:shall|must) not be\s+(.*?)[,\.]',
    r'(.*?)\s+(?:shall|must) not overlap\s+(.*?)[,\.]',
    r'it is not allowed\s+(?:to|that)\s+(.*?)[,\.]',
    r'it is prohibited\s+(?:to|that)\s+(.*?)[,\.]'
]

SCOPE_PATTERNS = [
    r'within\s+(?:a|one)\s+(.*?)[,\.]',
    r'in\s+(?:a|one)\s+(.*?)[,\.]',
    r'for\s+(?:a|one)\s+(.*?)[,\.]',
    r'for\s+(?:any|each|all)\s+(.*?)[,\.]'
]

OVERLAP_PATTERNS = [
    r'shall not overlap\s+(.*?)[,\.]',
    r'must not overlap\s+(.*?)[,\.]',
    r'non-overlapping\s+(.*?)[,\.]',
    r'disjoint\s+(.*?)[,\.]',
    r'mutually exclusive\s+(.*?)[,\.]'
]

PERMISSION_PATTERNS = [
    r'(.*?)\s+can be\s+(.*?)[,\.]',
    r'(.*?)\s+(?:is|are) allowed\s+(.*?)[,\.]',
    r'(.*?)\s+(?:is|are) permitted\s+(.*?)[,\.]',
    r'it is allowed\s+(?:to|that)\s+(.*?)[,\.]',
    r'it is permitted\s+(?:to|that)\s+(.*?)[,\.]'
]


class LogicAnalyzer:
    def __init__(self):
        # 加载spaCy模型
        self.nlp = spacy.load("en_core_web_sm")

        # 编译正则表达式
        self.conditional_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in CONDITIONAL_PATTERNS]
        self.prohibition_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in PROHIBITION_PATTERNS]
        self.scope_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in SCOPE_PATTERNS]
        self.overlap_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in OVERLAP_PATTERNS]
        self.permission_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in PERMISSION_PATTERNS]

    def analyze_constraint_logic(self, constraint: ConstraintRaw, entities: List[Entity]) -> Dict[str, Any]:
        """分析约束的逻辑结构"""
        # 预处理文本，保留列表结构
        processed_text, list_items = self._preprocess_text(constraint.body)

        # 确定约束类型
        constraint_type = self._determine_constraint_type(processed_text, list_items)

        # 分析结果
        result = {
            "constraint_type": constraint_type
        }

        # 提取逻辑元素
        conditions = self._extract_conditions(processed_text, list_items, entities)
        if conditions:
            result["conditions"] = conditions

        prohibitions = self._extract_prohibitions(processed_text, entities)
        if prohibitions:
            result["prohibitions"] = prohibitions

        non_overlapping = self._extract_non_overlapping(processed_text, entities)
        if non_overlapping:
            result["non_overlapping"] = non_overlapping

        permissions = self._extract_permissions(processed_text, entities, constraint)
        if permissions:
            result["permissions"] = permissions

        scope = self._extract_scope(processed_text, entities)
        if scope:
            result["scope"] = scope

        # 处理列表结构中的条件（步骤列表等）
        if list_items and not conditions:
            list_conditions = self._process_list_conditions(list_items, entities)
            if list_conditions:
                result["conditions"] = list_conditions

        return result

    def _preprocess_text(self, text: str) -> Tuple[str, List[str]]:
        """预处理文本，提取列表结构"""
        # 提取列表项
        list_pattern = r'(\d+\.\s+.+?)(?=\d+\.\s+|$)'
        list_items = re.findall(list_pattern, text, re.DOTALL)
        list_items = [item.strip() for item in list_items]

        # 保留处理后的文本
        processed_text = text

        return processed_text, list_items

    def _determine_constraint_type(self, text: str, list_items: List[str]) -> str:
        """确定约束类型"""
        # 检查是否是步骤清单或程序
        if list_items and len(list_items) >= 3:
            # 三个或更多编号项可能是程序
            return "Procedure"

        # 检查条件禁止模式
        has_condition = any(pattern.search(text) for pattern in self.conditional_patterns)
        has_prohibition = any(pattern.search(text) for pattern in self.prohibition_patterns)

        if has_condition and has_prohibition:
            return "ConditionalProhibition"

        # 检查非重叠约束
        if any(pattern.search(text) for pattern in self.overlap_patterns):
            return "NonOverlapConstraint"

        # 检查许可约束
        if any(pattern.search(text) for pattern in self.permission_patterns):
            return "Permission"

        # 检查禁止约束
        if has_prohibition:
            return "Prohibition"

        # 检查一般要求
        if "shall" in text.lower() or "must" in text.lower():
            return "Requirement"

        # 默认类型
        return "Generic"

    def _extract_conditions(self, text: str, list_items: List[str], entities: List[Entity]) -> List[Dict[str, Any]]:
        """提取条件表达式"""
        conditions = []

        # 从正文提取条件
        for pattern in self.conditional_patterns:
            matches = pattern.finditer(text)
            for match in matches:
                condition_text = match.group(1) if len(match.groups()) >= 1 else ""
                value_text = match.group(2) if len(match.groups()) >= 2 else None

                # 解析条件中的实体和值
                condition_entity = self._find_entity_in_text(condition_text, entities)
                value_entity = self._find_entity_in_text(value_text, entities) if value_text else None

                if condition_entity:
                    condition = {
                        "text": condition_text,
                        "entity": condition_entity.text,
                        "entity_type": condition_entity.type,
                        "parent_class": condition_entity.parent
                    }

                    # 添加值信息
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
                        condition["operation"] = "=="

                    conditions.append(condition)

        return conditions

    def _process_list_conditions(self, list_items: List[str], entities: List[Entity]) -> List[Dict[str, Any]]:
        """处理列表中的条件项"""
        conditions = []

        for item in list_items:
            # 移除编号前缀
            item_text = re.sub(r'^\d+\.\s+', '', item).strip()

            # 查找项中的实体
            item_entities = []
            for entity in entities:
                if entity.text in item_text:
                    item_entities.append(entity)

            # 构建条件对象
            if item_entities:
                # 使用最可能的实体（例如，优先选择ATTRIBUTE_PATH类型）
                primary_entity = None
                for e in item_entities:
                    if e.type == "ATTRIBUTE_PATH":
                        primary_entity = e
                        break

                if not primary_entity and item_entities:
                    primary_entity = item_entities[0]

                if primary_entity:
                    condition = {
                        "text": item_text,
                        "entity": primary_entity.text,
                        "entity_type": primary_entity.type,
                        "parent_class": primary_entity.parent,
                        "list_item": True  # 标记为列表项
                    }

                    # 尝试确定操作
                    if "take" in item_text.lower() or "use" in item_text.lower():
                        condition["operation"] = "use"
                    elif "set" in item_text.lower():
                        condition["operation"] = "=="
                    else:
                        condition["operation"] = "apply"  # 一般应用

                    conditions.append(condition)
            else:
                # 没有找到实体，但仍保留列表项
                condition = {
                    "text": item_text,
                    "list_item": True
                }
                conditions.append(condition)

        return conditions

    def _extract_prohibitions(self, text: str, entities: List[Entity]) -> List[Dict[str, Any]]:
        """提取禁止表达式"""
        prohibitions = []

        for pattern in self.prohibition_patterns:
            matches = pattern.finditer(text)
            for match in matches:
                prohibition_text = match.group(1) if len(match.groups()) >= 1 else ""

                # 在禁止文本中查找实体
                prohibition_entity = self._find_entity_in_text(prohibition_text, entities)

                if prohibition_entity:
                    prohibition = {
                        "text": prohibition_text,
                        "entity": prohibition_entity.text,
                        "entity_type": prohibition_entity.type,
                        "parent_class": prohibition_entity.parent
                    }

                    # 确定操作类型
                    if "shall not be set" in match.group(0) or "must not be set" in match.group(0):
                        prohibition["operation"] = "shall_not_be_set"
                    elif "shall not overlap" in match.group(0) or "must not overlap" in match.group(0):
                        prohibition["operation"] = "shall_not_overlap"
                    else:
                        prohibition["operation"] = "shall_not"

                    # 提取作用域
                    for scope_pattern in self.scope_patterns:
                        scope_match = scope_pattern.search(text)
                        if scope_match:
                            scope_text = scope_match.group(1)
                            scope_entity = self._find_entity_in_text(scope_text, entities)
                            if scope_entity:
                                prohibition["scope"] = scope_entity.text

                    prohibitions.append(prohibition)

        return prohibitions

    def _extract_non_overlapping(self, text: str, entities: List[Entity]) -> Optional[Dict[str, Any]]:
        """提取非重叠约束"""
        for pattern in self.overlap_patterns:
            match = pattern.search(text)
            if match:
                overlap_text = match.group(1) if len(match.groups()) >= 1 else ""

                # 查找涉及的实体
                related_entities = []
                for entity in entities:
                    if entity.text in overlap_text or entity.text in text:
                        related_entities.append(entity)

                if related_entities:
                    non_overlapping = {
                        "text": overlap_text,
                        "attributes": []
                    }

                    # 添加相关属性
                    for entity in related_entities:
                        if entity.type in ["ATTRIBUTE", "ATTRIBUTE_PATH"]:
                            attr_name = entity.text.split(".")[-1] if "." in entity.text else entity.text
                            non_overlapping["attributes"].append({
                                "class": entity.parent,
                                "attribute": attr_name
                            })

                    # 提取作用域
                    for scope_pattern in self.scope_patterns:
                        scope_match = scope_pattern.search(text)
                        if scope_match:
                            scope_text = scope_match.group(1)
                            scope_entity = self._find_entity_in_text(scope_text, entities)
                            if scope_entity and scope_entity.type == "CLASS":
                                non_overlapping["scope"] = f"within_one_{scope_entity.text}"

                    return non_overlapping

        return None

    def _extract_permissions(self, text: str, entities: List[Entity], constraint: ConstraintRaw) -> Optional[
        Dict[str, Any]]:
        """提取许可表达式"""
        for pattern in self.permission_patterns:
            match = pattern.search(text)
            if match:
                permission_text = match.group(1) if len(match.groups()) >= 1 else ""

                # 查找涉及的实体
                permission_entities = []
                for entity in entities:
                    if entity.text in permission_text or entity.text in text:
                        permission_entities.append(entity)

                if permission_entities:
                    permission = {
                        "attributes": [],
                        "permission": "arbitrary_values" if "arbitrary" in text else "allowed"
                    }

                    # 添加相关属性
                    for entity in permission_entities:
                        if entity.type in ["ATTRIBUTE", "ATTRIBUTE_PATH"]:
                            attr_name = entity.text.split(".")[-1] if "." in entity.text else entity.text
                            permission["attributes"].append({
                                "class": entity.parent,
                                "attribute": attr_name
                            })

                    # 提取引用的约束条件
                    reference_ids = []

                    # 使用约束中已识别的引用ID
                    if hasattr(constraint, 'reference_ids') and constraint.reference_ids:
                        reference_ids.extend(constraint.reference_ids)

                    # 也在文本中查找可能的引用
                    ref_matches = re.findall(r"\[(constr|TPS|req)_[^\]]+\]", text)
                    if ref_matches:
                        for ref in ref_matches:
                            if ref not in reference_ids:
                                reference_ids.append(ref)

                    if reference_ids:
                        permission["conditions"] = reference_ids

                    return permission

        return None

    def _extract_scope(self, text: str, entities: List[Entity]) -> Optional[str]:
        """提取约束的作用范围"""
        for pattern in self.scope_patterns:
            match = pattern.search(text)
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

        # 精确匹配
        for entity in entities:
            if entity.text.lower() == text.lower():
                return entity

        # 部分匹配，优先选择最长匹配
        matched_entities = []
        for entity in entities:
            if entity.text.lower() in text.lower():
                matched_entities.append((entity, len(entity.text)))

        if matched_entities:
            # 按匹配长度降序排序
            matched_entities.sort(key=lambda x: x[1], reverse=True)
            return matched_entities[0][0]

        return None