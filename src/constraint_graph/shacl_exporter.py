"""shacl_exporter.py (v2.3) - 修复角色提取和目标解析
------------------------------------------
高优先级修复：
1. 从结构化数据提取角色，而非正则表达式
2. 统一处理多种目标格式
"""
from __future__ import annotations

import json
import pathlib
import re
from typing import Dict, List, Any


class ShaclExporter:
    def __init__(self, out_dir: str | pathlib.Path):
        self.out_dir = pathlib.Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.lines: List[str] = [
            "@prefix sh: <http://www.w3.org/ns/shacl#> .",
            "@prefix ex: <http://example.com/> .",
            "@prefix autosar: <http://autosar.org/> .",
            "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .",
            "@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .",
            "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
            ""
        ]
        self.shape_counter = 0
        self.class_id_to_xml_mapping = {}
        self.attr_id_to_xml_mapping = {}

        # 🔧 新增：已知的AUTOSAR角色定义（从样本数据中提取）
        self.known_roles = {
            "dataReadAccess", "dataWriteAccess", "dataSendPoint",
            "dataReceivePointByValue", "dataReceivePointByArgument"
        }

    def export(self, constraints: List[Dict[str, Any]]) -> pathlib.Path:
        """导出所有约束为SHACL shapes - 支持严重性分级"""

        # 先构建映射表
        self._build_xml_mappings(constraints)

        # 🔧 按约束来源分类
        structural_constraints = [c for c in constraints if c.get("is_structural", False)]
        semantic_constraints = [c for c in constraints if c.get("is_semantic", False)]

        print(f"📊 SHACL约束分类统计:")
        print(f"   - 结构约束: {len(structural_constraints)} 个")
        print(f"   - 语义约束: {len(semantic_constraints)} 个")

        # 添加分组注释
        self.lines.append("# =================================")
        self.lines.append("# 结构约束 (Structural Constraints)")
        self.lines.append("# 来源: raw_attributes.jsonl")
        self.lines.append("# 严重性: sh:Violation (硬性约束)")
        self.lines.append("# =================================")
        self.lines.append("")

        # 1. 处理结构约束
        for constraint in structural_constraints:
            self._export_structural_constraint(constraint)

        self.lines.append("")
        self.lines.append("# =================================")
        self.lines.append("# 语义约束 (Semantic Constraints)")
        self.lines.append("# 来源: canonical_constraints.json")
        self.lines.append("# 严重性: sh:Warning/sh:Info (推荐配置)")
        self.lines.append("# =================================")
        self.lines.append("")

        # 2. 处理语义约束 - 使用语义版本的导出方法
        for constraint in semantic_constraints:
            constraint_type = constraint.get("type", "other")

            if constraint_type == "existence":
                self._export_existence_constraint_semantic(constraint)
            elif constraint_type == "value_restriction":
                self._export_value_restriction_constraint_semantic(constraint)
            elif constraint_type == "cardinality":
                self._export_cardinality_constraint_semantic(constraint)
            elif constraint_type == "format":
                self._export_format_constraint_semantic(constraint)
            elif constraint_type == "behavioral":
                self._export_behavioral_constraint_semantic(constraint)
            elif constraint_type == "relationship":
                self._export_relationship_constraint_semantic(constraint)
            elif constraint_type == "ordering":
                self._export_ordering_constraint_semantic(constraint)
            elif constraint_type == "naming_convention":
                self._export_naming_constraint_semantic(constraint)
            else:
                self._export_basic_constraint_semantic(constraint)

        # 保存文件
        path = self.out_dir / "autosar_shapes.ttl"
        path.write_text("\n".join(self.lines), encoding="utf-8")
        return path

    def _export_structural_constraint(self, constraint: Dict[str, Any]):
        """导出结构约束 - 硬性约束，使用sh:Violation"""
        for target in constraint.get("enriched_targets", []):
            if target["target_type"] != "attribute":
                continue

            shape_id = f"Structural_{target.get('attr_id', 'unknown')}"
            target_class = self._get_target_class_name(target)
            path_name = self._get_path_name(target)

            self.lines.append(f"ex:{shape_id} a sh:PropertyShape ;")
            self.lines.append(f'    rdfs:label "Structural: {path_name}" ;')
            self.lines.append(f'    rdfs:comment "Hard constraint from XML Schema definition" ;')
            self.lines.append(f"    sh:targetClass autosar:{target_class} ;")
            self.lines.append(f"    sh:path autosar:{path_name} ;")

            # 🔧 硬性约束：严格使用raw_attributes中的基数
            min_occurs = target.get("minOccurs")
            max_occurs = target.get("maxOccurs")

            if min_occurs is not None:
                self.lines.append(f"    sh:minCount {min_occurs} ;")

            if max_occurs is not None and max_occurs != -1:
                self.lines.append(f"    sh:maxCount {max_occurs} ;")

            # 🔧 硬性约束标记
            self.lines.append("    sh:severity sh:Violation ;")

            # 结构约束的错误消息
            if min_occurs is not None and max_occurs is not None:
                if min_occurs == max_occurs:
                    self.lines.append(
                        f'    sh:message "STRUCTURAL ERROR: {path_name} must occur exactly {min_occurs} times in {target_class}" ;')
                else:
                    self.lines.append(
                        f'    sh:message "STRUCTURAL ERROR: {path_name} must occur between {min_occurs} and {max_occurs} times in {target_class}" ;')
            elif min_occurs is not None:
                self.lines.append(
                    f'    sh:message "STRUCTURAL ERROR: {path_name} must occur at least {min_occurs} times in {target_class}" ;')
            elif max_occurs is not None:
                self.lines.append(
                    f'    sh:message "STRUCTURAL ERROR: {path_name} must occur at most {max_occurs} times in {target_class}" ;')

            # 🔧 溯源信息
            original_cid = constraint.get("original_cid", "unknown")
            self.lines.append(
                f'    rdfs:comment "Source: raw_attributes | Type: structural | AttrID: {target.get("attr_id", "")}" ;')

            self.lines.append("    .")
            self.lines.append("")

    def _export_existence_constraint_semantic(self, constraint: Dict[str, Any]):
        """导出存在性约束为语义推荐 - 修复严重性问题"""
        for target in constraint.get("enriched_targets", []):
            if target["target_type"] != "attribute":
                continue

            shape_id = self._get_shape_id(constraint, target)
            target_class = self._get_target_class_name(target)
            path_name = self._get_path_name(target)

            self.lines.append(f"ex:{shape_id} a sh:PropertyShape ;")

            title = constraint.get("title", f"Constraint {constraint.get('cid', 'unknown')}")
            expression = constraint.get("expression", "Auto-generated constraint")

            self.lines.append(f'    rdfs:label "Semantic: {self._escape_string(title)}" ;')
            self.lines.append(f'    rdfs:comment "Recommendation: {self._escape_string(expression[:100])}" ;')
            self.lines.append(f"    sh:targetClass autosar:{target_class} ;")
            self.lines.append(f"    sh:path autosar:{path_name} ;")

            # 🔧 关键修复：语义约束使用Warning级别
            severity = constraint.get("severity", "sh:Warning")
            self.lines.append(f"    sh:severity {severity} ;")

            # 🔧 存在性约束逻辑：使用SPARQL而不是minCount，避免与结构约束冲突
            if constraint.get("mustNotExist"):
                self.lines.append("    sh:sparql [")
                self.lines.append("        a sh:SPARQLConstraint ;")
                self.lines.append(
                    f'        sh:message "RECOMMENDATION: {path_name} should not exist in {target_class} (context-specific)" ;')
                self.lines.append("        sh:select \"\"\"")
                self.lines.append("            SELECT $this WHERE {")
                self.lines.append(f"                $this a autosar:{target_class} .")
                self.lines.append(f"                $this autosar:{path_name} ?value .")
                self.lines.append("            }")
                self.lines.append("        \"\"\" ;")
                self.lines.append("    ] ;")
            elif constraint.get("mustExist"):
                # 🔧 关键修改：使用SPARQL约束表达推荐，不使用硬性minCount
                self.lines.append("    sh:sparql [")
                self.lines.append("        a sh:SPARQLConstraint ;")
                self.lines.append(
                    f'        sh:message "RECOMMENDATION: {path_name} should exist in {target_class} for proper semantic behavior" ;')
                self.lines.append("        sh:select \"\"\"")
                self.lines.append("            SELECT $this WHERE {")
                self.lines.append(f"                $this a autosar:{target_class} .")
                self.lines.append(f"                FILTER NOT EXISTS {{ $this autosar:{path_name} ?value }}")
                self.lines.append("            }")
                self.lines.append("        \"\"\" ;")
                self.lines.append("    ] ;")

            # 🔧 溯源信息
            original_cid = constraint.get("original_cid") or constraint.get("cid", "")
            self.lines.append(
                f'    rdfs:comment "Source: canonical_constraints | Type: semantic | Original_CID: {original_cid}" ;')

            self.lines.append("    .")
            self.lines.append("")

    def _export_value_restriction_constraint_semantic(self, constraint: Dict[str, Any]):
        """导出值限制约束为语义推荐"""
        for target in constraint.get("enriched_targets", []):
            if target["target_type"] != "attribute":
                continue

            shape_id = self._get_shape_id(constraint, target)
            target_class = self._get_target_class_name(target)
            path_name = self._get_path_name(target)

            self.lines.append(f"ex:{shape_id} a sh:PropertyShape ;")
            self.lines.append(f'    rdfs:label "Semantic: {constraint.get("title", "")}" ;')
            self.lines.append(f"    sh:targetClass autosar:{target_class} ;")
            self.lines.append(f"    sh:path autosar:{path_name} ;")

            # 🔧 语义约束严重性
            severity = constraint.get("severity", "sh:Info")
            self.lines.append(f"    sh:severity {severity} ;")

            # 枚举值约束 - 作为推荐
            enum_values = constraint.get("enum", [])
            if enum_values:
                enum_list = " ".join(f'"{v}"' for v in enum_values)
                self.lines.append(f"    sh:in ( {enum_list} ) ;")
                self.lines.append(
                    f'    sh:message "RECOMMENDATION: {path_name} should be one of: {", ".join(enum_values)}" ;')

            # 推荐值处理
            if constraint.get("recommendation_type") == "recommended":
                self.lines.append(
                    f'    sh:message "RECOMMENDATION: Consider using recommended values for {path_name}" ;')

            # 可扩展性处理
            if constraint.get("extensible"):
                self.lines.append(
                    f'    sh:message "INFO: Additional values for {path_name} may be agreed between stakeholders" ;')

            # 溯源信息
            original_cid = constraint.get("original_cid") or constraint.get("cid", "")
            self.lines.append(
                f'    rdfs:comment "Source: canonical_constraints | Type: semantic | Original_CID: {original_cid}" ;')

            self.lines.append("    .")
            self.lines.append("")

    def _export_cardinality_constraint_semantic(self, constraint: Dict[str, Any]):
        """导出基数约束为语义推荐"""
        for target in constraint.get("enriched_targets", []):
            if target["target_type"] != "attribute":
                continue

            shape_id = self._get_shape_id(constraint, target)
            target_class = self._get_target_class_name(target)
            path_name = self._get_path_name(target)

            self.lines.append(f"ex:{shape_id} a sh:PropertyShape ;")
            self.lines.append(f'    rdfs:label "Semantic: {constraint.get("title", "")}" ;')
            self.lines.append(f"    sh:targetClass autosar:{target_class} ;")
            self.lines.append(f"    sh:path autosar:{path_name} ;")

            # 🔧 语义约束严重性
            severity = constraint.get("severity", "sh:Warning")
            self.lines.append(f"    sh:severity {severity} ;")

            # 🔧 语义基数约束：使用SPARQL而不是直接的minCount/maxCount（避免与结构约束冲突）
            message_parts = []

            # 精确基数
            if "exactOccurs" in constraint:
                count = constraint["exactOccurs"]
                message_parts.append(f"should occur exactly {count} times")

            # 最小/最大基数
            if "minOccurs" in constraint and constraint["minOccurs"] is not None:
                min_count = constraint["minOccurs"]
                message_parts.append(f"should occur at least {min_count} times")

            if "maxOccurs" in constraint and constraint["maxOccurs"] is not None:
                max_count = constraint["maxOccurs"]
                message_parts.append(f"should occur at most {max_count} times")

            # 组合消息
            if message_parts:
                combined_message = f"RECOMMENDATION: {path_name} " + " and ".join(message_parts) + f" in {target_class}"
                self.lines.append(f'    sh:message "{combined_message}" ;')

            # 溯源信息
            original_cid = constraint.get("original_cid") or constraint.get("cid", "")
            self.lines.append(
                f'    rdfs:comment "Source: canonical_constraints | Type: semantic | Original_CID: {original_cid}" ;')

            self.lines.append("    .")
            self.lines.append("")

    def _export_format_constraint_semantic(self, constraint: Dict[str, Any]):
        """导出格式约束为语义推荐"""
        for target in constraint.get("enriched_targets", []):
            if target["target_type"] != "attribute":
                continue

            shape_id = self._get_shape_id(constraint, target)
            target_class = self._get_target_class_name(target)
            path_name = self._get_path_name(target)

            self.lines.append(f"ex:{shape_id} a sh:PropertyShape ;")
            self.lines.append(f'    rdfs:label "Semantic: {constraint.get("title", "")}" ;')
            self.lines.append(f"    sh:targetClass autosar:{target_class} ;")
            self.lines.append(f"    sh:path autosar:{path_name} ;")

            # 🔧 语义约束严重性
            severity = constraint.get("severity", "sh:Info")
            self.lines.append(f"    sh:severity {severity} ;")

            # 正则表达式约束 - 作为推荐
            if "pattern" in constraint:
                pattern = constraint["pattern"].replace("\\", "\\\\")
                self.lines.append(f'    sh:pattern "{pattern}" ;')
                self.lines.append(f'    sh:message "RECOMMENDATION: {path_name} should match pattern: {pattern}" ;')

            # 禁用字符约束 - 作为推荐
            if "forbidden_chars" in constraint:
                for char in constraint["forbidden_chars"]:
                    escaped_char = char.replace("\\", "\\\\").replace('"', '\\"')
                    self.lines.append(f'    sh:not [')
                    self.lines.append(f'        sh:pattern ".*{re.escape(escaped_char)}.*" ;')
                    self.lines.append(f'    ] ;')
                    self.lines.append(
                        f'    sh:message "RECOMMENDATION: {path_name} should not contain character: {char}" ;')

            # 数据类型约束 - 作为推荐
            if constraint.get("format_type") == "c_header":
                self.lines.append("    sh:datatype xsd:string ;")
                self.lines.append('    sh:pattern "^[a-zA-Z_][a-zA-Z0-9_]*$" ;')
                self.lines.append(f'    sh:message "RECOMMENDATION: {path_name} should be a valid C identifier" ;')

            # 溯源信息
            original_cid = constraint.get("original_cid") or constraint.get("cid", "")
            self.lines.append(
                f'    rdfs:comment "Source: canonical_constraints | Type: semantic | Original_CID: {original_cid}" ;')

            self.lines.append("    .")
            self.lines.append("")

    def _export_behavioral_constraint_semantic(self, constraint: Dict[str, Any]):
        """导出行为约束为语义推荐"""
        shape_id = f"BehavioralConstraint_{constraint.get('cid', self.shape_counter)}"
        self.shape_counter += 1

        self.lines.append(f"ex:{shape_id} a sh:NodeShape ;")
        self.lines.append(f'    rdfs:label "Semantic: {constraint.get("title", "")}" ;')

        # 🔧 语义约束严重性
        severity = constraint.get("severity", "sh:Warning")
        self.lines.append(f"    sh:severity {severity} ;")

        # 为所有相关的类添加目标
        target_classes = set()
        for target in constraint.get("enriched_targets", []):
            if target.get("class_id"):
                target_class = self._get_target_class_name(target)
                target_classes.add(target_class)

        for target_class in target_classes:
            self.lines.append(f"    sh:targetClass autosar:{target_class} ;")

        # if-then逻辑约束 - 作为推荐
        if constraint.get("constraint_logic") == "if_then":
            if_condition = constraint.get("if_condition", "")
            then_action = constraint.get("then_action", "")

            # 生成SPARQL查询来验证if-then逻辑
            sparql_query = self._generate_if_then_sparql(constraint, if_condition, then_action)
            if sparql_query:
                self.lines.append("    sh:sparql [")
                self.lines.append("        a sh:SPARQLConstraint ;")
                self.lines.append(f'        sh:message "RECOMMENDATION: {constraint.get("title", "")}" ;')
                self.lines.append("        sh:select \"\"\"")
                self.lines.append(f"            {sparql_query}")
                self.lines.append("        \"\"\" ;")
                self.lines.append("    ] ;")

        # 溯源信息
        original_cid = constraint.get("original_cid") or constraint.get("cid", "")
        self.lines.append(
            f'    rdfs:comment "Source: canonical_constraints | Type: semantic | Original_CID: {original_cid}" ;')

        self.lines.append("    .")
        self.lines.append("")

    def _export_relationship_constraint_semantic(self, constraint: Dict[str, Any]):
        """导出关系约束为语义推荐 - 🔧 修复角色提取逻辑"""
        shape_id = f"RelationshipConstraint_{constraint.get('cid', self.shape_counter)}"
        self.shape_counter += 1

        self.lines.append(f"ex:{shape_id} a sh:NodeShape ;")
        self.lines.append(f'    rdfs:label "Semantic: {constraint.get("title", "")}" ;')

        # 🔧 语义约束严重性
        severity = constraint.get("severity", "sh:Warning")
        self.lines.append(f"    sh:severity {severity} ;")

        # 添加所有相关类为目标
        for target in constraint.get("enriched_targets", []):
            if target.get("class_id"):
                target_class = self._get_target_class_name(target)
                self.lines.append(f"    sh:targetClass autosar:{target_class} ;")

        # 应用约束 - 作为推荐
        if constraint.get("application_constraint"):
            self._add_application_constraint_semantic(constraint)

        # 相关实体约束
        related_entities = constraint.get("related_entities", [])
        if related_entities:
            for entity in related_entities:
                self.lines.append(f"    # Related entity: {entity}")

        # 溯源信息
        original_cid = constraint.get("original_cid") or constraint.get("cid", "")
        self.lines.append(
            f'    rdfs:comment "Source: canonical_constraints | Type: semantic | Original_CID: {original_cid}" ;')

        self.lines.append("    .")
        self.lines.append("")

    def _export_ordering_constraint_semantic(self, constraint: Dict[str, Any]):
        """导出排序约束为语义推荐"""
        precedence_rules = constraint.get("precedence_rules", [])

        for i, rule in enumerate(precedence_rules):
            shape_id = f"OrderingConstraint_{constraint.get('cid', self.shape_counter)}_{i}"

            self.lines.append(f"ex:{shape_id} a sh:NodeShape ;")
            self.lines.append(
                f'    rdfs:label "Semantic: Precedence Rule: {rule.get("winner", "")} wins over {rule.get("loser", "")}" ;')

            # 🔧 语义约束严重性
            severity = constraint.get("severity", "sh:Warning")
            self.lines.append(f"    sh:severity {severity} ;")

            # 为包含这些属性的类添加约束
            for target in constraint.get("enriched_targets", []):
                if target.get("class_id"):
                    target_class = self._get_target_class_name(target)
                    self.lines.append(f"    sh:targetClass autosar:{target_class} ;")

            # 优先级逻辑约束 - 作为推荐
            winner = rule.get("winner", "")
            loser = rule.get("loser", "")

            if winner and loser:
                self.lines.append("    sh:sparql [")
                self.lines.append("        a sh:SPARQLConstraint ;")
                self.lines.append(
                    f'        sh:message "RECOMMENDATION: {winner} should take precedence over {loser}" ;')
                self.lines.append("        sh:select \"\"\"")
                self.lines.append("            SELECT $this WHERE {")
                self.lines.append(f"                $this autosar:{winner} ?winnerValue .")
                self.lines.append(f"                $this autosar:{loser} ?loserValue .")
                self.lines.append("                FILTER(?loserValue != \"\") .")
                self.lines.append("                FILTER(?winnerValue = \"\") .")
                self.lines.append("            }")
                self.lines.append("        \"\"\" ;")
                self.lines.append("    ] ;")

            # 溯源信息
            original_cid = constraint.get("original_cid") or constraint.get("cid", "")
            self.lines.append(
                f'    rdfs:comment "Source: canonical_constraints | Type: semantic | Original_CID: {original_cid}" ;')

            self.lines.append("    .")
            self.lines.append("")

    def _export_naming_constraint_semantic(self, constraint: Dict[str, Any]):
        """导出命名约束为语义推荐"""
        for target in constraint.get("enriched_targets", []):
            if target["target_type"] != "attribute":
                continue

            shape_id = self._get_shape_id(constraint, target)
            target_class = self._get_target_class_name(target)
            path_name = self._get_path_name(target)

            self.lines.append(f"ex:{shape_id} a sh:PropertyShape ;")
            self.lines.append(f'    rdfs:label "Semantic: {constraint.get("title", "")}" ;')
            self.lines.append(f"    sh:targetClass autosar:{target_class} ;")
            self.lines.append(f"    sh:path autosar:{path_name} ;")

            # 🔧 语义约束严重性
            severity = constraint.get("severity", "sh:Info")
            self.lines.append(f"    sh:severity {severity} ;")

            # 模式约束 - 作为推荐
            if constraint.get("pattern_based"):
                self.lines.append("    sh:node ex:ShortNamePatternShape ;")

            # 命名约定约束 - 作为推荐
            if constraint.get("naming_type") == "convention":
                self.lines.append(
                    f'    sh:message "RECOMMENDATION: Consider following naming conventions for {path_name}" ;')

            # 溯源信息
            original_cid = constraint.get("original_cid") or constraint.get("cid", "")
            self.lines.append(
                f'    rdfs:comment "Source: canonical_constraints | Type: semantic | Original_CID: {original_cid}" ;')

            self.lines.append("    .")
            self.lines.append("")

    def _export_basic_constraint_semantic(self, constraint: Dict[str, Any]):
        """导出基础约束为语义推荐"""
        for target in constraint.get("enriched_targets", []):
            if target["target_type"] != "attribute":
                continue

            shape_id = self._get_shape_id(constraint, target)
            target_class = self._get_target_class_name(target)
            path_name = self._get_path_name(target)

            self.lines.append(f"ex:{shape_id} a sh:PropertyShape ;")
            self.lines.append(f'    rdfs:label "Semantic: {constraint.get("title", "")}" ;')
            self.lines.append(f'    rdfs:comment "Recommendation: {constraint.get("expression", "")}" ;')
            self.lines.append(f"    sh:targetClass autosar:{target_class} ;")
            self.lines.append(f"    sh:path autosar:{path_name} ;")

            # 🔧 语义约束严重性
            severity = constraint.get("severity", "sh:Info")
            self.lines.append(f"    sh:severity {severity} ;")

            # 🔧 对于基础约束，只添加通用的推荐消息，不添加具体的基数约束
            self.lines.append(
                f'    sh:message "RECOMMENDATION: Consider reviewing {path_name} configuration in {target_class}" ;')

            # 溯源信息
            original_cid = constraint.get("original_cid") or constraint.get("cid", "")
            self.lines.append(
                f'    rdfs:comment "Source: canonical_constraints | Type: semantic | Original_CID: {original_cid}" ;')

            self.lines.append("    .")
            self.lines.append("")

    def _add_application_constraint_semantic(self, constraint: Dict[str, Any]):
        """🔧 修复版：从结构化数据提取角色，而非正则表达式"""

        # 🔧 高优先级修复1：从结构化数据提取角色
        roles = self._extract_roles_from_constraint(constraint)

        if roles:
            self.lines.append("    sh:sparql [")
            self.lines.append("        a sh:SPARQLConstraint ;")
            self.lines.append(
                f'        sh:message "RECOMMENDATION: Scope attribute should be applied in specific roles: {", ".join(roles)}" ;')
            self.lines.append("        sh:select \"\"\"")
            self.lines.append("            SELECT $this WHERE {")
            self.lines.append("                $this autosar:scope ?scope .")
            self.lines.append("                FILTER(?scope != \"\") .")

            # 检查是否在允许的角色中
            role_conditions = []
            for role in roles:
                role_conditions.append(f"                MINUS {{ ?parent autosar:{role} $this }}")

            for condition in role_conditions:
                self.lines.append(condition)

            self.lines.append("            }")
            self.lines.append("        \"\"\" ;")
            self.lines.append("    ] ;")

    def _extract_roles_from_constraint(self, constraint: Dict[str, Any]) -> List[str]:
        """🔧 高优先级修复：从结构化数据提取角色，而非文本解析"""
        roles = []

        # 方法1：从enriched_targets中提取（最可靠）
        for target in constraint.get("enriched_targets", []):
            if target.get("target_type") == "attribute":
                xml_tag = target.get("xml_tag", "")
                if xml_tag in self.known_roles:
                    roles.append(xml_tag)

        # 方法2：从原始约束的targetRefs提取（KG结构化数据）
        target_refs = constraint.get("targetRefs", [])
        for ref in target_refs:
            if "." in ref:
                entity, attr = ref.split(".", 1)
                if entity == "RunnableEntity" and attr in self.known_roles:
                    roles.append(attr)

        # 方法3：从targets_json提取（新格式）
        targets_json = constraint.get("targets_json")
        if targets_json:
            try:
                if isinstance(targets_json, str):
                    targets_data = json.loads(targets_json)
                else:
                    targets_data = targets_json

                if isinstance(targets_data, list):
                    for target in targets_data:
                        target_attrs = target.get("targetAttributes", [])
                        for attr in target_attrs:
                            if attr in self.known_roles:
                                roles.append(attr)
            except (json.JSONDecodeError, TypeError):
                pass

        # 方法4：从原始targets提取（传统格式）
        targets = constraint.get("targets", [])
        for target in targets:
            if isinstance(target, dict):
                target_attrs = target.get("targetAttributes", [])
                target_entity = target.get("targetEntityName", "")
                if target_entity == "RunnableEntity":
                    for attr in target_attrs:
                        if attr in self.known_roles:
                            roles.append(attr)

        # 方法5：最后后备 - 从表达式文本提取（保留作为fallback）
        if not roles:
            expression = constraint.get("expression", "")
            roles = [role for role in self.known_roles if role in expression]

        return list(set(roles))  # 去重

    def _build_xml_mappings(self, constraints: List[Dict[str, Any]]):
        """从enriched_targets中构建XML映射表 - 修复版"""
        print("🔍 构建XML映射表...")

        for constraint in constraints:
            for target in constraint.get("enriched_targets", []):
                if target["target_type"] == "attribute":
                    attr_id = target.get("attr_id")
                    class_id = target.get("class_id")
                    xml_tag = target.get("xml_tag")

                    # 🔧 关键修复：正确使用enricher传递的类信息
                    class_name = target.get("class_name")        # 来自 raw_classes.jsonl 的 className
                    class_xml_tag = target.get("class_xml_tag")  # 来自 raw_classes.jsonl 的 xml_tag

                    # 属性映射
                    if attr_id and xml_tag:
                        self.attr_id_to_xml_mapping[attr_id] = xml_tag
                        print(f"📋 属性映射: attrId {attr_id} → {xml_tag}")

                    # 🔧 关键修复：类映射 - 优先使用 xml_tag，备用 className
                    if class_id:
                        if class_xml_tag:  # 优先使用实际的XML标签
                            self.class_id_to_xml_mapping[class_id] = class_xml_tag
                            print(f"📋 类映射: classId {class_id} → {class_xml_tag} (XML标签)")
                        elif class_name:  # 备用使用类名
                            self.class_id_to_xml_mapping[class_id] = class_name
                            print(f"📋 类映射(备用): classId {class_id} → {class_name} (类名)")
                        else:
                            print(f"⚠️  classId {class_id} 无法获取类名信息")

        print(f"✅ 映射表构建完成: {len(self.class_id_to_xml_mapping)} 个类映射, {len(self.attr_id_to_xml_mapping)} 个属性映射")

    def _get_target_class_name(self, target: Dict[str, Any]) -> str:
        """获取目标类的实际XML名称 - 修复版"""
        class_id = target.get("class_id")

        # 🔧 第一优先级：直接从target中获取实际XML标签
        class_xml_tag = target.get("class_xml_tag")
        if class_xml_tag:
            print(f"✅ 使用class_xml_tag: {class_xml_tag}")
            return class_xml_tag

        # 🔧 第二优先级：从target中获取类名
        class_name = target.get("class_name")
        if class_name:
            print(f"✅ 使用class_name: {class_name}")
            return class_name

        # 🔧 第三优先级：从构建的映射表中查找
        if class_id in self.class_id_to_xml_mapping:
            mapped_name = self.class_id_to_xml_mapping[class_id]
            print(f"✅ 使用映射: classId {class_id} → {mapped_name}")
            return mapped_name

        # 🔧 最后后备：使用抽象名称（应该避免这种情况）
        print(f"❌ 无法解析classId {class_id}，使用抽象名称")
        return f"CLASS_{class_id}"

    def _get_path_name(self, target: Dict[str, Any]) -> str:
        """获取属性路径的实际XML名称"""
        attr_id = target.get("attr_id")
        xml_tag = target.get("xml_tag")

        # 优先使用直接提供的xml_tag
        if xml_tag:
            return xml_tag

        # 从映射表中查找
        if attr_id in self.attr_id_to_xml_mapping:
            return self.attr_id_to_xml_mapping[attr_id]

        # 默认使用抽象名称（应该避免）
        return f"ATTR_{attr_id}"

    def _export_attribute_cardinality_constraint(self, constraint: Dict[str, Any], target: Dict[str, Any]):
        """导出属性基数约束 - 使用实际XML名称"""
        shape_id = self._get_shape_id(constraint, target)
        target_class = self._get_target_class_name(target)
        path_name = self._get_path_name(target)

        self.lines.append(f"ex:{shape_id} a sh:PropertyShape ;")
        self.lines.append(f'    rdfs:label "{constraint.get("title", "")}" ;')
        self.lines.append(f"    sh:targetClass autosar:{target_class} ;")
        self.lines.append(f"    sh:path autosar:{path_name} ;")

        # 精确基数
        if "exactOccurs" in constraint:
            count = constraint["exactOccurs"]
            self.lines.append(f"    sh:minCount {count} ;")
            self.lines.append(f"    sh:maxCount {count} ;")
            self.lines.append(f'    sh:message "{path_name} must occur exactly {count} times in {target_class}" ;')

        # 最小/最大基数
        if "minOccurs" in constraint and constraint["minOccurs"] is not None:
            min_count = constraint["minOccurs"]
            self.lines.append(f"    sh:minCount {min_count} ;")
            if "maxOccurs" not in constraint:
                self.lines.append(f'    sh:message "{path_name} must occur at least {min_count} times in {target_class}" ;')

        if "maxOccurs" in constraint and constraint["maxOccurs"] is not None:
            max_count = constraint["maxOccurs"]
            self.lines.append(f"    sh:maxCount {max_count} ;")

        # 组合消息
        if "minOccurs" in constraint and "maxOccurs" in constraint:
            min_c = constraint["minOccurs"]
            max_c = constraint["maxOccurs"]
            self.lines.append(f'    sh:message "{path_name} must occur between {min_c} and {max_c} times in {target_class}" ;')

        self.lines.append("    .")
        self.lines.append("")

    def _export_class_cardinality_constraint(self, constraint: Dict[str, Any], target: Dict[str, Any]):
        """导出类级别基数约束 - 使用实际XML名称"""
        shape_id = self._get_shape_id(constraint, target)
        target_class = self._get_target_class_name(target)

        self.lines.append(f"ex:{shape_id} a sh:NodeShape ;")
        self.lines.append(f'    rdfs:label "{constraint.get("title", "")}" ;')
        self.lines.append(f"    sh:targetClass autosar:{target_class} ;")

        # 类存在基数约束
        if "cardinality_constraint" in constraint:
            count = constraint["cardinality_constraint"]
            self.lines.append(f"    sh:property [")
            self.lines.append(f"        sh:path rdf:type ;")
            self.lines.append(f"        sh:hasValue autosar:{target_class} ;")
            self.lines.append(f"        sh:minCount {count} ;")
            self.lines.append(f"        sh:maxCount {count} ;")
            self.lines.append(f'        sh:message "Must have exactly {count} instances of {target_class}" ;')
            self.lines.append(f"    ] ;")

        self.lines.append("    .")
        self.lines.append("")

    # 辅助方法
    def _get_shape_id(self, constraint: Dict[str, Any], target: Dict[str, Any]) -> str:
        """生成shape ID"""
        cid = constraint.get("cid", f"auto_{self.shape_counter}")
        attr_id = target.get("attr_id", "unknown")
        self.shape_counter += 1
        return f"CID_{cid}_ATTR_{attr_id}"

    def _generate_if_then_sparql(self, constraint: Dict[str, Any], if_condition: str, then_action: str) -> str:
        """生成if-then逻辑的SPARQL查询"""
        # 简化的SPARQL生成 - 实际实现需要更复杂的解析
        sparql_lines = [
            "SELECT $this WHERE {",
            "    # If condition check",
        ]

        # 解析if条件
        if "unit has to be converted" in if_condition:
            sparql_lines.extend([
                "    $this autosar:physicalDimension ?dim1 .",
                "    ?other autosar:physicalDimension ?dim2 .",
                "    FILTER(?dim1 != ?dim2) .",
            ])

        # 解析then动作
        if "physicalDimension" in then_action and "shall be the same" in then_action:
            sparql_lines.extend([
                "    # Then condition violation",
                "    FILTER(?dim1 != ?dim2) .",
            ])

        sparql_lines.append("}")
        return "\n            ".join(sparql_lines)

    def _escape_string(self, text: str) -> str:
        """转义字符串中的特殊字符"""
        if not text:
            return ""
        return text.replace('"', '\\"').replace('\n', ' ').replace('\r', ' ')

    @staticmethod
    def run(enriched_path: str | pathlib.Path, out_path: str | pathlib.Path):
        """运行SHACL导出"""
        enriched_path, out_path = map(pathlib.Path, (enriched_path, out_path))

        with enriched_path.open(encoding="utf-8") as f:
            constraints = json.load(f)

        out_dir = out_path if out_path.suffix == "" else out_path.parent
        return ShaclExporter(out_dir).export(constraints)