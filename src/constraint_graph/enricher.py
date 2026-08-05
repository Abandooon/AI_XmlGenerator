"""enricher.py (v1.3) - 高优先级修复：目标解析标准化
---------------------
修复：统一处理多种目标格式 (targets, targetRefs, targets_json)
"""
from __future__ import annotations

import json
import pathlib
import re
from typing import Any, Dict, List


class ConstraintEnricher:
    """增强的约束enricher，支持完整的映射和约束类型处理"""

    def __init__(self, attr_idx: Dict[str, Dict[str, Any]], enum_idx: Dict[str, List[str]],
                 class_idx: Dict[int, Dict[str, Any]]):
        self.attr_idx = attr_idx  # "classId.xml_tag" → {maxOccurs, minOccurs, type, attrId}
        self.enum_idx = enum_idx  # enumId → list[values]
        self.class_idx = class_idx  # classId → {className, xml_tag}
        self.aid2key = {}  # attrId → "classId.xml_tag"
        self.target_refs_map = {}  # "ClassName.attrName" → attrId映射

    def enrich(self, cons: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """增强约束信息 - 修改为同时生成结构约束和语义约束"""
        enriched_constraints = []

        # 1. 处理语义约束（从canonical_constraints）
        print("📋 处理语义约束...")
        for c in cons:
            enriched_constraint = self._enrich_single_constraint(c)
            if enriched_constraint:
                enriched_constraints.append(enriched_constraint)

        # 2. 生成结构约束（从raw_attributes）
        print("📋 生成结构约束...")
        structural_constraints = self.generate_structural_constraints()
        enriched_constraints.extend(structural_constraints)

        print(f"✅ 总计生成 {len(enriched_constraints)} 个约束")
        print(f"   - 语义约束: {len(cons)} 个")
        print(f"   - 结构约束: {len(structural_constraints)} 个")

        return enriched_constraints

    def _enrich_single_constraint(self, c: Dict[str, Any]) -> Dict[str, Any] | None:
        """增强单个约束 - 添加约束来源和严重性分类"""
        constraint_type = c.get("type") or c.get("constraint_type", "other")

        # 🔧 关键修复：保持原始CID
        original_cid = c.get("original_cid") or c.get("cid") or c.get("id")

        # 基础约束信息
        enriched = {
            "cid": original_cid,  # 🔧 使用原始CID
            "original_cid": original_cid,  # 🔧 明确记录原始CID
            "type": constraint_type,
            "expression": c.get("expression", ""),
            "title": c.get("title", f"Constraint {original_cid}"),
            "confidence": c.get("confidence", 1.0),
            "targets": [],
            "enriched_targets": [],
            "xml_mapping": {},
            # 🔧 约束来源和严重性分类
            "constraint_source": "canonical_constraints",
            "severity": self._determine_constraint_severity(constraint_type),
            "is_structural": False,
            "is_semantic": True,
            # 🔧 溯源信息
            "kg_source": c.get("kg_source", False),
            "original_expression": c.get("original_expression", ""),
            "original_title": c.get("original_title", ""),
            "original_value": c.get("original_value", "")
        }

        # 确保title和expression不为空
        if not enriched["title"]:
            enriched["title"] = f"Constraint {enriched['cid']}"
        if not enriched["expression"]:
            enriched["expression"] = f"Auto-generated constraint of type {constraint_type}"

        # 🔧 高优先级修复：统一处理所有目标格式
        self._process_all_target_formats(c, enriched)

        # 根据约束类型添加特定信息
        self._enrich_by_constraint_type(c, enriched, constraint_type)

        return enriched

    def _process_all_target_formats(self, c: Dict[str, Any], enriched: Dict[str, Any]):
        """🔧 高优先级修复：统一处理所有目标格式"""
        normalized_targets = []

        # 方法1：处理 targetRefs（最直接和可靠的格式）
        target_refs = c.get("targetRefs", [])
        if target_refs:
            print(f"🔍 处理targetRefs: {len(target_refs)} 个")
            for ref in target_refs:
                target = self._parse_target_ref(ref)
                if target:
                    normalized_targets.append(target)

        # 方法2：处理 targets_json（新格式）
        targets_json = c.get("targets_json")
        if targets_json:
            print("🔍 处理targets_json格式")
            json_targets = self._parse_targets_json(targets_json)
            normalized_targets.extend(json_targets)

        # 方法3：处理传统 targets 格式
        targets = c.get("targets", [])
        if targets:
            print(f"🔍 处理传统targets: {len(targets)} 个")
            legacy_targets = self._parse_legacy_targets(targets)
            normalized_targets.extend(legacy_targets)

        # 如果没有找到任何目标，创建默认目标（向后兼容）
        if not normalized_targets:
            print("⚠️  未找到有效目标，创建默认目标")
            normalized_targets = [self._create_default_target()]

        # 转换为enriched格式并填充
        for target in normalized_targets:
            self._populate_target_details(target, enriched)

        print(f"✅ 目标解析完成: {len(enriched['enriched_targets'])} 个enriched_targets")

    def _parse_target_ref(self, target_ref: str) -> Dict[str, Any] | None:
        """解析 targetRef 格式 (如 'CompuMethod.category')"""
        if "." not in target_ref:
            return None

        class_name, attr_name = target_ref.split(".", 1)

        # 处理特殊的类级别目标
        if attr_name == "_classLevel":
            return {
                "target_type": "class",
                "class_name": class_name,
                "attr_name": None,
                "xml_tag": None
            }
        else:
            return {
                "target_type": "attribute",
                "class_name": class_name,
                "attr_name": attr_name,
                "xml_tag": attr_name  # 假设attr_name就是xml_tag
            }

    def _parse_targets_json(self, targets_json) -> List[Dict[str, Any]]:
        """解析 targets_json 格式"""
        try:
            if isinstance(targets_json, str):
                targets_data = json.loads(targets_json)
            else:
                targets_data = targets_json

            if not isinstance(targets_data, list):
                targets_data = [targets_data]

            normalized_targets = []
            for target in targets_data:
                entity_name = target.get("targetEntityName")
                target_attrs = target.get("targetAttributes", [])
                entity_type = target.get("entityType", "class")

                for attr_name in target_attrs:
                    if attr_name == "_classLevel" or attr_name == "_abstractLevel":
                        normalized_targets.append({
                            "target_type": "class",
                            "class_name": entity_name,
                            "attr_name": None,
                            "xml_tag": None
                        })
                    else:
                        normalized_targets.append({
                            "target_type": "attribute",
                            "class_name": entity_name,
                            "attr_name": attr_name,
                            "xml_tag": attr_name
                        })

            return normalized_targets

        except (json.JSONDecodeError, TypeError, AttributeError) as e:
            print(f"⚠️  targets_json解析失败: {e}")
            return []

    def _parse_legacy_targets(self, targets: List) -> List[Dict[str, Any]]:
        """解析传统 targets 格式"""
        normalized_targets = []

        for target in targets:
            if isinstance(target, (int, str)) and str(target).isdigit():
                # 简单的属性ID格式
                attr_id = int(target)
                key = self.aid2key.get(attr_id)
                if key:
                    class_id_str, xml_tag = key.split(".", 1)
                    class_id = int(class_id_str)
                    class_info = self.class_idx.get(class_id)

                    normalized_targets.append({
                        "target_type": "attribute",
                        "attr_id": attr_id,
                        "class_id": class_id,
                        "class_name": class_info.get("className") if class_info else None,
                        "xml_tag": xml_tag
                    })

            elif isinstance(target, dict):
                # 复杂target结构
                entity_name = target.get("targetEntityName")
                target_attrs = target.get("targetAttributes", [])

                for attr_name in target_attrs:
                    if attr_name == "_classLevel":
                        normalized_targets.append({
                            "target_type": "class",
                            "class_name": entity_name,
                            "attr_name": None,
                            "xml_tag": None
                        })
                    else:
                        normalized_targets.append({
                            "target_type": "attribute",
                            "class_name": entity_name,
                            "attr_name": attr_name,
                            "xml_tag": attr_name
                        })

        return normalized_targets

    def _create_default_target(self) -> Dict[str, Any]:
        """创建默认目标（向后兼容）"""
        return {
            "target_type": "attribute",
            "attr_id": 0,
            "class_id": 1,
            "class_name": "DefaultClass",
            "xml_tag": "default"
        }

    def _populate_target_details(self, target: Dict[str, Any], enriched: Dict[str, Any]):
        """填充目标的详细信息并添加到enriched中"""

        # 如果已有attr_id和class_id，直接使用
        if target.get("attr_id") and target.get("class_id"):
            self._add_target_to_enriched(target, enriched)
            return

        # 否则需要通过名称查找ID
        class_name = target.get("class_name")
        attr_name = target.get("attr_name")

        if target["target_type"] == "class":
            # 类级别目标
            class_id = self._find_class_id_by_name(class_name)
            if class_id:
                target["class_id"] = class_id
                self._add_target_to_enriched(target, enriched)

        elif target["target_type"] == "attribute":
            # 属性级别目标
            attr_id = self._find_attr_id_by_name(class_name, attr_name)
            class_id = self._find_class_id_by_name(class_name)

            if attr_id and class_id:
                target["attr_id"] = attr_id
                target["class_id"] = class_id
                self._add_target_to_enriched(target, enriched)
            else:
                print(f"⚠️  无法解析目标: {class_name}.{attr_name}")

    def _add_target_to_enriched(self, target: Dict[str, Any], enriched: Dict[str, Any]):
        """将解析好的目标添加到enriched约束中"""

        if target["target_type"] == "attribute":
            attr_id = target["attr_id"]
            class_id = target["class_id"]

            # 获取类信息
            class_info = self.class_idx.get(class_id, {})

            # 获取属性元数据
            key = self.aid2key.get(attr_id)
            attr_meta = self.attr_idx.get(key, {}) if key else {}

            enriched_target = {
                "attr_id": attr_id,
                "class_id": class_id,
                "xml_tag": target.get("xml_tag", f"attr_{attr_id}"),
                "target_type": "attribute",
                "class_name": class_info.get("className"),
                "class_xml_tag": class_info.get("xml_tag"),
                "maxOccurs": attr_meta.get("maxOccurs"),
                "minOccurs": attr_meta.get("minOccurs"),
                "typeId": attr_meta.get("type")
            }

            enriched["targets"].append(attr_id)
            enriched["enriched_targets"].append(enriched_target)

            print(f"✅ 添加属性目标: {class_info.get('className', 'Unknown')}.{target.get('xml_tag')}")

        elif target["target_type"] == "class":
            class_id = target["class_id"]
            class_info = self.class_idx.get(class_id, {})

            enriched_target = {
                "class_id": class_id,
                "class_name": class_info.get("className"),
                "class_xml_tag": class_info.get("xml_tag"),
                "target_type": "class"
            }

            enriched["targets"].append(f"class_{class_id}")
            enriched["enriched_targets"].append(enriched_target)

            print(f"✅ 添加类目标: {class_info.get('className', 'Unknown')}")

    def _determine_constraint_severity(self, constraint_type: str) -> str:
        """根据约束类型确定SHACL严重性级别"""
        # 🔧 语义约束的严重性映射
        severity_mapping = {
            "existence": "sh:Warning",  # 存在性约束 → 推荐
            "behavioral": "sh:Warning",  # 行为约束 → 推荐
            "relationship": "sh:Warning",  # 关系约束 → 推荐
            "value_restriction": "sh:Info",  # 值限制 → 信息（除非是硬性枚举）
            "format": "sh:Info",  # 格式约束 → 信息
            "naming_convention": "sh:Info",  # 命名约定 → 信息
            "ordering": "sh:Warning",  # 排序约束 → 推荐
            "cardinality": "sh:Warning",  # 基数约束 → 推荐（语义层面）
            "definition": "sh:Info"  # 定义约束 → 信息
        }

        return severity_mapping.get(constraint_type, "sh:Warning")

    # 🔧 新增：生成结构约束的方法
    def generate_structural_constraints(self) -> List[Dict[str, Any]]:
        """从raw_attributes生成结构约束 - 使用明确的结构CID"""
        structural_constraints = []

        for key, attr_meta in self.attr_idx.items():
            class_id_str, xml_tag = key.split(".", 1)
            class_id = int(class_id_str)
            attr_id = attr_meta["attrId"]

            # 获取类信息
            class_info = self.class_idx.get(class_id, {})

            # 🔧 创建明确的结构约束CID，与语义约束区分
            struct_cid = f"STRUCT_{attr_id}"

            # 创建结构约束
            structural_constraint = {
                "cid": struct_cid,
                "original_cid": struct_cid,  # 结构约束的原始CID就是自己
                "type": "structural_cardinality",
                "expression": f"Structural constraint for {xml_tag} in {class_info.get('className', f'Class_{class_id}')}",
                "title": f"Structural Constraint: {xml_tag}",
                "confidence": 1.0,
                "targets": [attr_id],
                "enriched_targets": [{
                    "attr_id": attr_id,
                    "class_id": class_id,
                    "xml_tag": xml_tag,
                    "target_type": "attribute",
                    "class_name": class_info.get("className", f"Class_{class_id}"),
                    "class_xml_tag": class_info.get("xml_tag", f"CLASS-{class_id}"),
                    "maxOccurs": attr_meta.get("maxOccurs"),
                    "minOccurs": attr_meta.get("minOccurs"),
                    "typeId": attr_meta.get("type")
                }],
                "xml_mapping": {
                    f"ATTR_{attr_id}": {
                        "xml_tag": xml_tag,
                        "class_id": class_id,
                        "class_name": class_info.get("className", ""),
                        "class_xml_tag": class_info.get("xml_tag", ""),
                        "context_path": f"{class_id}:{xml_tag}"
                    }
                },
                # 🔧 结构约束标记
                "constraint_source": "raw_attributes",
                "severity": "sh:Violation",  # 硬性约束
                "is_structural": True,
                "is_semantic": False,
                "kg_source": False,  # 标记为非KG来源
                # 结构约束特有字段
                "minOccurs": attr_meta.get("minOccurs"),
                "maxOccurs": attr_meta.get("maxOccurs")
            }

            structural_constraints.append(structural_constraint)

        return structural_constraints

    def _enrich_by_constraint_type(self, c: Dict[str, Any], enriched: Dict[str, Any],
                                 constraint_type: str):
        """根据约束类型添加特定的增强信息"""

        if constraint_type == "existence":
            self._enrich_existence_constraint(c, enriched)
        elif constraint_type == "value_restriction":
            self._enrich_value_restriction_constraint(c, enriched)
        elif constraint_type == "cardinality":
            self._enrich_cardinality_constraint(c, enriched)
        elif constraint_type == "format":
            self._enrich_format_constraint(c, enriched)
        elif constraint_type == "behavioral":
            self._enrich_behavioral_constraint(c, enriched)
        elif constraint_type == "relationship":
            self._enrich_relationship_constraint(c, enriched)
        elif constraint_type == "ordering":
            self._enrich_ordering_constraint(c, enriched)
        elif constraint_type == "naming_convention":
            self._enrich_naming_constraint(c, enriched)
        elif constraint_type == "definition":
            self._enrich_definition_constraint(c, enriched)

        # 添加通用的属性元数据
        self._add_attribute_metadata(enriched)

    def _enrich_existence_constraint(self, c: Dict[str, Any], enriched: Dict[str, Any]):
        """增强存在性约束"""
        expression = c.get("expression", "").lower()
        value = c.get("value", "")

        # 分析表达式确定存在性要求
        if any(phrase in expression for phrase in ["shall only be provided", "only applies", "shall not exist"]):
            enriched["mustNotExist"] = True
            enriched["conditional"] = True
        elif any(phrase in expression for phrase in ["shall exist", "must be present", "required"]):
            enriched["mustExist"] = True
        else:
            enriched["mustExist"] = True  # 默认为必须存在

        # 提取条件信息
        if "where" in expression or "if" in expression:
            enriched["has_condition"] = True
            enriched["condition_expression"] = expression

    def _enrich_value_restriction_constraint(self, c: Dict[str, Any], enriched: Dict[str, Any]):
        """增强值限制约束"""
        value = c.get("value", "")

        if value:
            # 解析枚举值
            enum_values = self._parse_enum_values(value)
            enriched["enum"] = enum_values
            enriched["enum_type"] = "explicit"

        # 从表达式中提取推荐值
        expression = c.get("expression", "")
        if "recommended" in expression.lower():
            enriched["recommendation_type"] = "recommended"
        elif "mutually agreed" in expression.lower():
            enriched["extensible"] = True

    def _enrich_cardinality_constraint(self, c: Dict[str, Any], enriched: Dict[str, Any]):
        """增强基数约束"""
        expression = c.get("expression", "")
        value = c.get("value", "")

        # 提取基数信息
        if "exactly one" in expression:
            enriched["minOccurs"] = 1
            enriched["maxOccurs"] = 1
        elif value and value.isdigit():
            enriched["exactOccurs"] = int(value)

        # 从表达式中提取更多基数信息
        numbers = re.findall(r'\b(\d+)\b', expression)
        if numbers:
            enriched["cardinality_constraint"] = int(numbers[0])

    def _enrich_format_constraint(self, c: Dict[str, Any], enriched: Dict[str, Any]):
        """增强格式约束"""
        expression = c.get("expression", "")
        value = c.get("value", "")

        if value:
            if value == "|":
                enriched["forbidden_chars"] = ["|"]
            else:
                enriched["pattern"] = value

        # 从表达式中提取格式要求
        if "C header file" in expression:
            enriched["format_type"] = "c_header"
            enriched["pattern"] = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
        elif "forbidden" in expression:
            forbidden_chars = re.findall(r'"([^"]+)"', expression)
            if forbidden_chars:
                enriched["forbidden_chars"] = forbidden_chars

    def _enrich_behavioral_constraint(self, c: Dict[str, Any], enriched: Dict[str, Any]):
        """增强行为约束"""
        expression = c.get("expression", "")

        # 提取if-then逻辑
        if "if" in expression.lower() and "then" in expression.lower():
            parts = re.split(r'\bif\b|\bthen\b', expression, flags=re.IGNORECASE)
            if len(parts) >= 3:
                enriched["if_condition"] = parts[1].strip()
                enriched["then_action"] = parts[2].strip()
                enriched["constraint_logic"] = "if_then"

    def _enrich_relationship_constraint(self, c: Dict[str, Any], enriched: Dict[str, Any]):
        """增强关系约束"""
        expression = c.get("expression", "")

        # 检测约束类型
        if "shall only be applied" in expression:
            enriched["application_constraint"] = True

        # 提取相关实体
        entities = self._extract_entities_from_expression(expression)
        enriched["related_entities"] = entities

    def _enrich_ordering_constraint(self, c: Dict[str, Any], enriched: Dict[str, Any]):
        """增强排序约束"""
        expression = c.get("expression", "")

        # 提取优先级规则
        if "wins over" in expression:
            precedence_rules = self._extract_precedence_rules(expression)
            enriched["precedence_rules"] = precedence_rules

    def _enrich_naming_constraint(self, c: Dict[str, Any], enriched: Dict[str, Any]):
        """增强命名约束"""
        expression = c.get("expression", "")

        if "naming conventions" in expression.lower():
            enriched["naming_type"] = "convention"
        if "shortNamePattern" in expression:
            enriched["pattern_based"] = True

    def _enrich_definition_constraint(self, c: Dict[str, Any], enriched: Dict[str, Any]):
        """增强定义约束"""
        # 定义约束主要是描述性的，添加分类标记
        enriched["constraint_nature"] = "descriptive"

    def _add_attribute_metadata(self, enriched: Dict[str, Any]):
        """为约束添加属性元数据 - 修复版：正确传递类名信息"""
        xml_mapping = {}

        for target in enriched["enriched_targets"]:
            if target["target_type"] == "attribute":
                attr_id = target["attr_id"]
                key = self.aid2key.get(attr_id)

                if key:
                    class_id_str, xml_tag = key.split(".", 1)
                    class_id = int(class_id_str)

                    # 🔧 关键修复：从 class_idx 获取实际的类信息
                    class_info = self.class_idx.get(class_id)
                    if class_info:
                        # ✅ 正确传递类信息到target中，供SHACL导出器使用
                        target["class_name"] = class_info.get("className")  # 如: "TimingEvent"
                        target["class_xml_tag"] = class_info.get("xml_tag")  # 如: "TIMING-EVENT"

                        print(
                            f"📋 类映射传递: classId {class_id} → XML:{class_info.get('xml_tag')} / 类名:{class_info.get('className')}")
                    else:
                        print(f"⚠️  未找到classId {class_id}的类信息")
                        # 提供默认值避免None
                        target["class_name"] = f"UnknownClass_{class_id}"
                        target["class_xml_tag"] = f"UNKNOWN-CLASS-{class_id}"

                    # 添加属性元数据
                    meta = self.attr_idx.get(key)
                    if meta:
                        target["maxOccurs"] = meta.get("maxOccurs")
                        target["minOccurs"] = meta.get("minOccurs")
                        target["typeId"] = meta.get("type")

                    # 构建XML映射 - 使用实际的类信息
                    xml_mapping[f"ATTR_{attr_id}"] = {
                        "xml_tag": xml_tag,
                        "class_id": class_id,
                        "class_name": class_info.get("className", "") if class_info else "",
                        "class_xml_tag": class_info.get("xml_tag", "") if class_info else "",
                        "context_path": f"{class_id}:{xml_tag}"
                    }

        enriched["xml_mapping"] = xml_mapping

    # 辅助方法
    def _find_attr_id_by_name(self, class_name: str, attr_name: str) -> int | None:
        """根据类名和属性名查找属性ID"""
        # 这里需要实现名称到ID的映射逻辑
        # 实际实现中需要构建反向索引
        for attr_id, key in self.aid2key.items():
            class_id_str, xml_tag = key.split(".", 1)
            class_id = int(class_id_str)
            class_info = self.class_idx.get(class_id)
            if class_info and class_info.get("className") == class_name and xml_tag == attr_name:
                return attr_id
        return None

    def _find_class_id_by_name(self, class_name: str) -> int | None:
        """根据类名查找类ID"""
        for class_id, class_info in self.class_idx.items():
            if class_info.get("className") == class_name:
                return class_id
        return None

    def _parse_enum_values(self, value_str: str) -> List[str]:
        """解析枚举值字符串"""
        # 支持多种分隔符
        separators = [",", "，", "、", ";", "；"]
        for sep in separators:
            if sep in value_str:
                return [v.strip() for v in value_str.split(sep) if v.strip()]
        return [value_str.strip()] if value_str.strip() else []

    def _extract_entities_from_expression(self, expression: str) -> List[str]:
        """从表达式中提取实体名称"""
        # 提取大写开头的实体名称
        entities = re.findall(r'\b[A-Z][a-zA-Z]+\b', expression)
        return list(set(entities))

    def _extract_precedence_rules(self, expression: str) -> List[Dict[str, str]]:
        """提取优先级规则"""
        rules = []
        lines = expression.split('\n')
        for line in lines:
            if "wins over" in line:
                parts = line.split("wins over")
                if len(parts) == 2:
                    rules.append({
                        "winner": parts[0].strip(),
                        "loser": parts[1].strip()
                    })
        return rules

    @classmethod
    def run(
            cls,
            raw_attr_fp: str | pathlib.Path,
            raw_enum_fp: str | pathlib.Path,
            canonical_fp: str | pathlib.Path,
            out_fp: str | pathlib.Path,
            raw_classes_fp: str | pathlib.Path = None,  # 🔧 修改：改为必需参数
    ):
        """运行增强处理 - 修复版：确保 raw_classes.jsonl 被正确加载"""
        raw_attr_fp, raw_enum_fp, canonical_fp, out_fp = map(
            pathlib.Path, [raw_attr_fp, raw_enum_fp, canonical_fp, out_fp]
        )

        # 🔧 修复：确保 raw_classes_fp 存在
        if raw_classes_fp:
            raw_classes_fp = pathlib.Path(raw_classes_fp)
        else:
            # 🔧 新增：如果没有显式传入，尝试从 raw_attr_fp 的目录中找到
            raw_classes_fp = raw_attr_fp.parent / "raw_classes.jsonl"
            print(f"🔍 自动推断 raw_classes.jsonl 路径: {raw_classes_fp}")

        if not raw_classes_fp.exists():
            print(f"❌ 错误: raw_classes.jsonl 文件不存在: {raw_classes_fp}")
            print(f"   请确保已经运行了 TokenExtractor.dump() 生成所有 raw_*.jsonl 文件")
            raise FileNotFoundError(f"raw_classes.jsonl not found: {raw_classes_fp}")

        # 构建索引
        with raw_attr_fp.open(encoding="utf-8") as f:
            attr_rows = [json.loads(l) for l in f]

        with raw_enum_fp.open(encoding="utf-8") as f:
            enum_rows = [json.loads(l) for l in f]

        # 🔧 修复：确保加载类索引
        print(f"📋 加载类索引从: {raw_classes_fp}")
        with raw_classes_fp.open(encoding="utf-8") as f:
            class_rows = [json.loads(l) for l in f]
            class_idx = {
                r["classId"]: {
                    "className": r["className"],
                    "xml_tag": r["xml_tag"]
                } for r in class_rows
            }

        print(f"✅ 加载了 {len(class_idx)} 个类定义")

        # 调试：显示加载的类信息
        for class_id, class_info in list(class_idx.items())[:5]:  # 显示前5个
            print(f"   classId {class_id}: {class_info['xml_tag']} ({class_info['className']})")
        if len(class_idx) > 5:
            print(f"   ... 还有 {len(class_idx) - 5} 个类")

        # 构建属性索引
        attr_idx = {}
        aid2key = {}
        for r in attr_rows:
            key = f"{r['classId']}.{r['xml_tag']}"
            attr_idx[key] = {
                "maxOccurs": r["maxOccurs"],
                "minOccurs": r["minOccurs"],
                "type": r["typeId"],
                "attrId": r["attrId"]
            }
            aid2key[r["attrId"]] = key

        # 构建枚举索引
        enum_idx = {r["enumId"]: r["values"] for r in enum_rows}

        # 加载约束并增强
        with canonical_fp.open(encoding="utf-8") as f:
            canon = json.load(f)

        enricher = cls(attr_idx, enum_idx, class_idx)
        enricher.aid2key = aid2key

        enriched = enricher.enrich(canon)

        # 保存结果
        out_fp.write_text(
            json.dumps(enriched, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        return out_fp