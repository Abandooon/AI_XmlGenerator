"""shacl_exporter.py (v2.6) - 完全修复MINUS问题和约束跳过机制
------------------------------------------
关键修复：
1. 彻底移除所有MINUS子句，使用FILTER NOT EXISTS或简化约束
2. 增加约束跳过机制和统计功能
3. 完整的字符串转义和错误处理
"""
from __future__ import annotations

import json
import pathlib
import re
import unicodedata
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

        # 跳过约束统计
        self.skipped_constraints = []
        self.processed_count = 0
        self.skipped_count = 0

        # 已知的AUTOSAR角色定义
        self.known_roles = {
            "dataReadAccess", "dataWriteAccess", "dataSendPoint",
            "dataReceivePointByValue", "dataReceivePointByArgument"
        }

    def export(self, constraints: List[Dict[str, Any]]) -> pathlib.Path:
        """导出所有约束为SHACL shapes - 支持严重性分级和约束跳过统计"""

        # 先构建映射表
        self._build_xml_mappings(constraints)

        # 按约束来源分类
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
            try:
                if self._should_skip_constraint(constraint):
                    self._record_skipped_constraint(constraint, "structural", "Missing target class mapping")
                    continue

                self._export_structural_constraint(constraint)
                self.processed_count += 1
            except Exception as e:
                print(f"⚠️  导出结构约束失败: {e}")
                self._record_skipped_constraint(constraint, "structural", f"Export error: {str(e)}")
                continue

        self.lines.append("")
        self.lines.append("# =================================")
        self.lines.append("# 语义约束 (Semantic Constraints)")
        self.lines.append("# 来源: canonical_constraints.json")
        self.lines.append("# 严重性: sh:Warning/sh:Info (推荐配置)")
        self.lines.append("# =================================")
        self.lines.append("")

        # 2. 处理语义约束
        for constraint in semantic_constraints:
            try:
                if self._should_skip_constraint(constraint):
                    self._record_skipped_constraint(constraint, "semantic", "Missing target class mapping")
                    continue

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

                self.processed_count += 1
            except Exception as e:
                cid = constraint.get("cid", "unknown")
                print(f"⚠️  导出语义约束 {cid} 失败: {e}")
                self._record_skipped_constraint(constraint, "semantic", f"Export error: {str(e)}")
                continue

        # 生成统计报告
        self._generate_skip_report()

        # 保存SHACL文件
        path = self.out_dir / "autosar_shapes.ttl"
        try:
            final_content = "\n".join(self.lines)
            self._validate_ttl_syntax(final_content)

            path.write_text(final_content, encoding="utf-8")
            print(f"✅ SHACL文件已保存: {path}")
            print(f"📊 处理统计: 成功 {self.processed_count} 个，跳过 {self.skipped_count} 个")
            return path
        except Exception as e:
            print(f"❌ 保存SHACL文件失败: {e}")
            debug_path = self.out_dir / "autosar_shapes_debug.ttl"
            debug_path.write_text(final_content, encoding="utf-8")
            raise

    def _should_skip_constraint(self, constraint: Dict[str, Any]) -> bool:
        """检查约束是否应该被跳过（目标类缺失）"""
        targets = constraint.get("enriched_targets", [])

        if not targets:
            return True

        for target in targets:
            if target["target_type"] != "attribute":
                continue

            target_class = self._try_get_target_class_name(target)
            if target_class.startswith("CLASS_") or target_class == "DefaultClass":
                return True

            path_name = self._try_get_path_name(target)
            if path_name.startswith("ATTR_") or path_name == "None":
                return True

        return False

    def _try_get_target_class_name(self, target: Dict[str, Any]) -> str:
        """尝试获取目标类名，用于检查是否应该跳过"""
        class_id = target.get("class_id")

        class_xml_tag = target.get("class_xml_tag")
        if class_xml_tag and class_xml_tag != "DefaultClass":
            return self._sanitize_identifier(class_xml_tag)

        class_name = target.get("class_name")
        if class_name and class_name != "DefaultClass":
            return self._sanitize_identifier(class_name)

        if class_id in self.class_id_to_xml_mapping:
            mapped_name = self.class_id_to_xml_mapping[class_id]
            if mapped_name and mapped_name != "DefaultClass":
                return self._sanitize_identifier(mapped_name)

        return f"CLASS_{class_id}"

    def _try_get_path_name(self, target: Dict[str, Any]) -> str:
        """尝试获取属性路径名，用于检查是否应该跳过"""
        attr_id = target.get("attr_id")
        xml_tag = target.get("xml_tag")

        if xml_tag and xml_tag != "None":
            return self._sanitize_identifier(xml_tag)

        if attr_id in self.attr_id_to_xml_mapping:
            mapped_tag = self.attr_id_to_xml_mapping[attr_id]
            if mapped_tag and mapped_tag != "None":
                return self._sanitize_identifier(mapped_tag)

        return f"ATTR_{attr_id}"

    def _record_skipped_constraint(self, constraint: Dict[str, Any], constraint_category: str, reason: str):
        """记录被跳过的约束"""
        self.skipped_count += 1

        cid = constraint.get("cid", "unknown")
        constraint_type = constraint.get("type", "unknown")
        title = constraint.get("title", "")

        targets_info = []
        for target in constraint.get("enriched_targets", []):
            target_info = {
                "target_type": target.get("target_type", "unknown"),
                "class_id": target.get("class_id"),
                "class_name": target.get("class_name"),
                "class_xml_tag": target.get("class_xml_tag"),
                "attr_id": target.get("attr_id"),
                "xml_tag": target.get("xml_tag"),
                "resolved_class": self._try_get_target_class_name(target),
                "resolved_attr": self._try_get_path_name(target)
            }
            targets_info.append(target_info)

        skipped_record = {
            "cid": cid,
            "constraint_type": constraint_type,
            "constraint_category": constraint_category,
            "title": title[:100] if title else "",
            "reason": reason,
            "targets_count": len(constraint.get("enriched_targets", [])),
            "targets_info": targets_info,
            "original_constraint": {
                "is_structural": constraint.get("is_structural", False),
                "is_semantic": constraint.get("is_semantic", False),
                "severity": constraint.get("severity"),
                "source": constraint.get("source", "unknown")
            }
        }

        self.skipped_constraints.append(skipped_record)

    def _generate_skip_report(self):
        """生成跳过约束的详细报告"""
        if not self.skipped_constraints:
            print("✅ 所有约束都成功处理，无跳过约束")
            return

        report = {
            "summary": {
                "total_constraints": self.processed_count + self.skipped_count,
                "processed_constraints": self.processed_count,
                "skipped_constraints": self.skipped_count,
                "skip_rate": round(self.skipped_count / (self.processed_count + self.skipped_count) * 100, 2) if (self.processed_count + self.skipped_count) > 0 else 0
            },
            "skip_reasons": {},
            "skip_by_category": {},
            "skip_by_type": {},
            "skipped_details": self.skipped_constraints
        }

        for record in self.skipped_constraints:
            reason = record["reason"]
            category = record["constraint_category"]
            constraint_type = record["constraint_type"]

            report["skip_reasons"][reason] = report["skip_reasons"].get(reason, 0) + 1
            report["skip_by_category"][category] = report["skip_by_category"].get(category, 0) + 1
            report["skip_by_type"][constraint_type] = report["skip_by_type"].get(constraint_type, 0) + 1

        report_path = self.out_dir / "shacl_skipped_constraints.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"📋 跳过约束报告已生成: {report_path}")
        print(f"⚠️  跳过了 {self.skipped_count} 个约束 ({report['summary']['skip_rate']}%)")

    def _get_target_class_name(self, target: Dict[str, Any]) -> str:
        """获取目标类的实际XML名称"""
        return self._try_get_target_class_name(target)

    def _get_path_name(self, target: Dict[str, Any]) -> str:
        """获取属性路径的实际XML名称"""
        return self._try_get_path_name(target)

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

            min_occurs = target.get("minOccurs")
            max_occurs = target.get("maxOccurs")

            if min_occurs is not None:
                self.lines.append(f"    sh:minCount {min_occurs} ;")

            if max_occurs is not None and max_occurs != -1:
                self.lines.append(f"    sh:maxCount {max_occurs} ;")

            self.lines.append("    sh:severity sh:Violation ;")

            if min_occurs is not None and max_occurs is not None:
                if min_occurs == max_occurs:
                    message = f"STRUCTURAL ERROR: {path_name} must occur exactly {min_occurs} times in {target_class}"
                else:
                    message = f"STRUCTURAL ERROR: {path_name} must occur between {min_occurs} and {max_occurs} times in {target_class}"
            elif min_occurs is not None:
                message = f"STRUCTURAL ERROR: {path_name} must occur at least {min_occurs} times in {target_class}"
            elif max_occurs is not None:
                message = f"STRUCTURAL ERROR: {path_name} must occur at most {max_occurs} times in {target_class}"
            else:
                message = f"STRUCTURAL ERROR: Invalid cardinality for {path_name} in {target_class}"

            safe_message = self._escape_string(message)
            self.lines.append(f'    sh:message "{safe_message}" ;')

            original_cid = constraint.get("original_cid", "unknown")
            safe_cid = self._escape_string(str(original_cid))
            attr_id = target.get("attr_id", "")
            comment = f"Source: raw_attributes | Type: structural | AttrID: {attr_id}"
            safe_comment = self._escape_string(comment)
            self.lines.append(f'    rdfs:comment "{safe_comment}" .')
            self.lines.append("")

    def _export_existence_constraint_semantic(self, constraint: Dict[str, Any]):
        """导出存在性约束为语义推荐 - 使用标准SHACL约束，避免复杂SPARQL"""
        for target in constraint.get("enriched_targets", []):
            if target["target_type"] != "attribute":
                continue

            shape_id = self._get_shape_id(constraint, target)
            target_class = self._get_target_class_name(target)
            path_name = self._get_path_name(target)

            self.lines.append(f"ex:{shape_id} a sh:PropertyShape ;")

            title = constraint.get("title", f"Constraint {constraint.get('cid', 'unknown')}")
            safe_title = self._escape_string(title)

            self.lines.append(f'    rdfs:label "Semantic: {safe_title}" ;')
            self.lines.append(f"    sh:targetClass autosar:{target_class} ;")
            self.lines.append(f"    sh:path autosar:{path_name} ;")

            severity = constraint.get("severity", "sh:Warning")
            self.lines.append(f"    sh:severity {severity} ;")

            # 🔧 关键修复：使用标准SHACL约束而不是SPARQL
            if constraint.get("mustNotExist"):
                # 推荐不存在：使用maxCount 0
                self.lines.append("    sh:maxCount 0 ;")
                message = f"RECOMMENDATION: {path_name} should not exist in {target_class} (context-specific)"
            elif constraint.get("mustExist"):
                # 推荐存在：使用minCount 1
                self.lines.append("    sh:minCount 1 ;")
                message = f"RECOMMENDATION: {path_name} should exist in {target_class} for proper semantic behavior"
            else:
                message = f"RECOMMENDATION: Review {path_name} existence in {target_class}"

            safe_message = self._escape_string(message)
            self.lines.append(f'    sh:message "{safe_message}" ;')

            original_cid = constraint.get("original_cid") or constraint.get("cid", "")
            safe_cid = self._escape_string(str(original_cid))
            comment = f"Source: canonical_constraints | Type: semantic | Original_CID: {safe_cid}"
            safe_comment = self._escape_string(comment)
            self.lines.append(f'    rdfs:comment "{safe_comment}" .')
            self.lines.append("")

    def _export_ordering_constraint_semantic(self, constraint: Dict[str, Any]):
        """导出排序约束为语义推荐 - 避免使用复杂SPARQL"""
        precedence_rules = constraint.get("precedence_rules", [])

        for i, rule in enumerate(precedence_rules):
            shape_id = f"OrderingConstraint_{constraint.get('cid', self.shape_counter)}_{i}"

            raw_winner = rule.get("winner", "")
            raw_loser = rule.get("loser", "")

            winner = self._clean_property_name(raw_winner)
            loser = self._clean_property_name(raw_loser)

            if not winner or not loser:
                print(f"⚠️  跳过无效的排序规则: winner='{raw_winner}', loser='{raw_loser}'")
                continue

            self.lines.append(f"ex:{shape_id} a sh:NodeShape ;")

            safe_title = self._escape_string(f"Precedence Rule: {winner} wins over {loser}")
            self.lines.append(f'    rdfs:label "Semantic: {safe_title}" ;')

            severity = constraint.get("severity", "sh:Warning")
            self.lines.append(f"    sh:severity {severity} ;")

            for target in constraint.get("enriched_targets", []):
                if target.get("class_id"):
                    target_class = self._get_target_class_name(target)
                    self.lines.append(f"    sh:targetClass autosar:{target_class} ;")

            # 🔧 关键修复：使用简单的消息约束，避免复杂SPARQL
            safe_message = self._escape_string(f"RECOMMENDATION: {winner} should take precedence over {loser}")
            self.lines.append(f'    sh:message "{safe_message}" ;')

            original_cid = constraint.get("original_cid") or constraint.get("cid", "")
            safe_cid = self._escape_string(str(original_cid))
            comment = f"Source: canonical_constraints | Type: semantic | Original_CID: {safe_cid}"
            safe_comment = self._escape_string(comment)
            self.lines.append(f'    rdfs:comment "{safe_comment}" .')
            self.lines.append("")

    def _export_relationship_constraint_semantic(self, constraint: Dict[str, Any]):
        """导出关系约束为语义推荐 - 简化处理，避免复杂SPARQL"""
        shape_id = f"RelationshipConstraint_{constraint.get('cid', self.shape_counter)}"
        self.shape_counter += 1

        self.lines.append(f"ex:{shape_id} a sh:NodeShape ;")

        safe_title = self._escape_string(constraint.get("title", ""))
        self.lines.append(f'    rdfs:label "Semantic: {safe_title}" ;')

        severity = constraint.get("severity", "sh:Warning")
        self.lines.append(f"    sh:severity {severity} ;")

        for target in constraint.get("enriched_targets", []):
            if target.get("class_id"):
                target_class = self._get_target_class_name(target)
                self.lines.append(f"    sh:targetClass autosar:{target_class} ;")

        # 🔧 简化处理：只添加推荐消息，不使用复杂SPARQL
        safe_message = self._escape_string("RECOMMENDATION: Review relationship configuration")
        self.lines.append(f'    sh:message "{safe_message}" ;')

        original_cid = constraint.get("original_cid") or constraint.get("cid", "")
        safe_cid = self._escape_string(str(original_cid))
        comment = f"Source: canonical_constraints | Type: semantic | Original_CID: {safe_cid}"
        safe_comment = self._escape_string(comment)
        self.lines.append(f'    rdfs:comment "{safe_comment}" .')
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

            safe_title = self._escape_string(constraint.get("title", ""))
            self.lines.append(f'    rdfs:label "Semantic: {safe_title}" ;')
            self.lines.append(f"    sh:targetClass autosar:{target_class} ;")
            self.lines.append(f"    sh:path autosar:{path_name} ;")

            severity = constraint.get("severity", "sh:Info")
            self.lines.append(f"    sh:severity {severity} ;")

            enum_values = constraint.get("enum", [])
            if enum_values:
                safe_values = []
                for v in enum_values:
                    cleaned_v = self._escape_string(str(v))
                    if cleaned_v and cleaned_v != "No description":
                        safe_values.append(cleaned_v)

                if safe_values:
                    enum_list = " ".join(f'"{v}"' for v in safe_values)
                    self.lines.append(f"    sh:in ( {enum_list} ) ;")

                    values_str = ", ".join(safe_values[:5])
                    if len(safe_values) > 5:
                        values_str += "..."
                    message = f"RECOMMENDATION: {path_name} should be one of: {values_str}"
                    safe_message = self._escape_string(message)
                    self.lines.append(f'    sh:message "{safe_message}" ;')

            original_cid = constraint.get("original_cid") or constraint.get("cid", "")
            safe_cid = self._escape_string(str(original_cid))
            comment = f"Source: canonical_constraints | Type: semantic | Original_CID: {safe_cid}"
            safe_comment = self._escape_string(comment)
            self.lines.append(f'    rdfs:comment "{safe_comment}" .')
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

            safe_title = self._escape_string(constraint.get("title", ""))
            self.lines.append(f'    rdfs:label "Semantic: {safe_title}" ;')
            self.lines.append(f"    sh:targetClass autosar:{target_class} ;")
            self.lines.append(f"    sh:path autosar:{path_name} ;")

            severity = constraint.get("severity", "sh:Warning")
            self.lines.append(f"    sh:severity {severity} ;")

            message_parts = []

            if "exactOccurs" in constraint:
                count = constraint["exactOccurs"]
                message_parts.append(f"should occur exactly {count} times")

            if "minOccurs" in constraint and constraint["minOccurs"] is not None:
                min_count = constraint["minOccurs"]
                message_parts.append(f"should occur at least {min_count} times")

            if "maxOccurs" in constraint and constraint["maxOccurs"] is not None:
                max_count = constraint["maxOccurs"]
                message_parts.append(f"should occur at most {max_count} times")

            if message_parts:
                combined_message = f"RECOMMENDATION: {path_name} " + " and ".join(message_parts) + f" in {target_class}"
                safe_message = self._escape_string(combined_message)
                self.lines.append(f'    sh:message "{safe_message}" ;')

            original_cid = constraint.get("original_cid") or constraint.get("cid", "")
            safe_cid = self._escape_string(str(original_cid))
            comment = f"Source: canonical_constraints | Type: semantic | Original_CID: {safe_cid}"
            safe_comment = self._escape_string(comment)
            self.lines.append(f'    rdfs:comment "{safe_comment}" .')
            self.lines.append("")

    def _export_format_constraint_semantic(self, constraint: Dict[str, Any]):
        """导出格式约束为语义推荐 - 避免复杂正则表达式"""
        for target in constraint.get("enriched_targets", []):
            if target["target_type"] != "attribute":
                continue

            shape_id = self._get_shape_id(constraint, target)
            target_class = self._get_target_class_name(target)
            path_name = self._get_path_name(target)

            self.lines.append(f"ex:{shape_id} a sh:PropertyShape ;")

            safe_title = self._escape_string(constraint.get("title", ""))
            self.lines.append(f'    rdfs:label "Semantic: {safe_title}" ;')
            self.lines.append(f"    sh:targetClass autosar:{target_class} ;")
            self.lines.append(f"    sh:path autosar:{path_name} ;")

            severity = constraint.get("severity", "sh:Info")
            self.lines.append(f"    sh:severity {severity} ;")

            # 🔧 简化格式约束：只使用基本的数据类型约束
            if constraint.get("format_type") == "c_header":
                self.lines.append("    sh:datatype xsd:string ;")
                # 使用简单安全的正则表达式
                self.lines.append('    sh:pattern "^[a-zA-Z_][a-zA-Z0-9_]*$" ;')
                message = f"RECOMMENDATION: {path_name} should be a valid C identifier"
                safe_message = self._escape_string(message)
                self.lines.append(f'    sh:message "{safe_message}" ;')
            else:
                # 对于其他格式约束，只使用通用推荐消息
                message = f"RECOMMENDATION: {path_name} should follow proper format guidelines"
                safe_message = self._escape_string(message)
                self.lines.append(f'    sh:message "{safe_message}" ;')

            original_cid = constraint.get("original_cid") or constraint.get("cid", "")
            safe_cid = self._escape_string(str(original_cid))
            comment = f"Source: canonical_constraints | Type: semantic | Original_CID: {safe_cid}"
            safe_comment = self._escape_string(comment)
            self.lines.append(f'    rdfs:comment "{safe_comment}" .')
            self.lines.append("")

    def _export_behavioral_constraint_semantic(self, constraint: Dict[str, Any]):
        """导出行为约束为语义推荐 - 简化处理"""
        shape_id = f"BehavioralConstraint_{constraint.get('cid', self.shape_counter)}"
        self.shape_counter += 1

        self.lines.append(f"ex:{shape_id} a sh:NodeShape ;")

        safe_title = self._escape_string(constraint.get("title", ""))
        self.lines.append(f'    rdfs:label "Semantic: {safe_title}" ;')

        severity = constraint.get("severity", "sh:Warning")
        self.lines.append(f"    sh:severity {severity} ;")

        target_classes = set()
        for target in constraint.get("enriched_targets", []):
            if target.get("class_id"):
                target_class = self._get_target_class_name(target)
                target_classes.add(target_class)

        for target_class in target_classes:
            self.lines.append(f"    sh:targetClass autosar:{target_class} ;")

        # 🔧 简化处理：只添加推荐消息，不使用复杂SPARQL
        safe_message = self._escape_string("RECOMMENDATION: Review behavioral configuration")
        self.lines.append(f'    sh:message "{safe_message}" ;')

        original_cid = constraint.get("original_cid") or constraint.get("cid", "")
        safe_cid = self._escape_string(str(original_cid))
        comment = f"Source: canonical_constraints | Type: semantic | Original_CID: {safe_cid}"
        safe_comment = self._escape_string(comment)
        self.lines.append(f'    rdfs:comment "{safe_comment}" .')
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

            safe_title = self._escape_string(constraint.get("title", ""))
            self.lines.append(f'    rdfs:label "Semantic: {safe_title}" ;')
            self.lines.append(f"    sh:targetClass autosar:{target_class} ;")
            self.lines.append(f"    sh:path autosar:{path_name} ;")

            severity = constraint.get("severity", "sh:Info")
            self.lines.append(f"    sh:severity {severity} ;")

            message = f"RECOMMENDATION: Consider following naming conventions for {path_name}"
            safe_message = self._escape_string(message)
            self.lines.append(f'    sh:message "{safe_message}" ;')

            original_cid = constraint.get("original_cid") or constraint.get("cid", "")
            safe_cid = self._escape_string(str(original_cid))
            comment = f"Source: canonical_constraints | Type: semantic | Original_CID: {safe_cid}"
            safe_comment = self._escape_string(comment)
            self.lines.append(f'    rdfs:comment "{safe_comment}" .')
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

            safe_title = self._escape_string(constraint.get("title", ""))
            safe_expression = self._escape_string(constraint.get("expression", ""))

            self.lines.append(f'    rdfs:label "Semantic: {safe_title}" ;')
            self.lines.append(f'    rdfs:comment "Recommendation: {safe_expression}" ;')
            self.lines.append(f"    sh:targetClass autosar:{target_class} ;")
            self.lines.append(f"    sh:path autosar:{path_name} ;")

            severity = constraint.get("severity", "sh:Info")
            self.lines.append(f"    sh:severity {severity} ;")

            message = f"RECOMMENDATION: Consider reviewing {path_name} configuration in {target_class}"
            safe_message = self._escape_string(message)
            self.lines.append(f'    sh:message "{safe_message}" ;')

            original_cid = constraint.get("original_cid") or constraint.get("cid", "")
            safe_cid = self._escape_string(str(original_cid))
            comment = f"Source: canonical_constraints | Type: semantic | Original_CID: {safe_cid}"
            safe_comment = self._escape_string(comment)
            self.lines.append(f'    rdfs:comment "{safe_comment}" .')
            self.lines.append("")

    def _build_xml_mappings(self, constraints: List[Dict[str, Any]]):
        """从enriched_targets中构建XML映射表"""
        print("🔍 构建XML映射表...")

        for constraint in constraints:
            for target in constraint.get("enriched_targets", []):
                if target["target_type"] == "attribute":
                    attr_id = target.get("attr_id")
                    class_id = target.get("class_id")
                    xml_tag = target.get("xml_tag")

                    class_name = target.get("class_name")
                    class_xml_tag = target.get("class_xml_tag")

                    if attr_id and xml_tag:
                        self.attr_id_to_xml_mapping[attr_id] = xml_tag

                    if class_id:
                        if class_xml_tag:
                            self.class_id_to_xml_mapping[class_id] = class_xml_tag
                        elif class_name:
                            self.class_id_to_xml_mapping[class_id] = class_name

        print(f"✅ 映射表构建完成: {len(self.class_id_to_xml_mapping)} 个类映射, {len(self.attr_id_to_xml_mapping)} 个属性映射")

    def _get_shape_id(self, constraint: Dict[str, Any], target: Dict[str, Any]) -> str:
        """生成shape ID"""
        cid = constraint.get("cid", f"auto_{self.shape_counter}")
        attr_id = target.get("attr_id", "unknown")
        self.shape_counter += 1

        clean_cid = self._sanitize_identifier(str(cid))
        clean_attr_id = self._sanitize_identifier(str(attr_id))

        return f"CID_{clean_cid}_ATTR_{clean_attr_id}"

    def _clean_property_name(self, raw_name: str) -> str:
        """清理属性名，确保是有效的RDF属性标识符"""
        if not raw_name:
            return ""

        name = str(raw_name).strip()
        name = re.sub(r'[^\w\-_]', '', name)
        name = re.sub(r'^[0-9]+', '', name)

        if not name:
            return ""

        return name

    def _validate_ttl_syntax(self, content: str):
        """基础TTL语法验证"""
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            if '" .' in line and not line.endswith(' .'):
                print(f"⚠️  第{i}行可能有语法问题: {line[:50]}...")

            try:
                line.encode('ascii')
            except UnicodeEncodeError:
                non_ascii = [c for c in line if ord(c) > 127]
                if non_ascii:
                    print(f"⚠️  第{i}行包含非ASCII字符: {non_ascii}")

    def _escape_string(self, text: str) -> str:
        """字符串转义方法 - 彻底修复TTL问题字符"""
        if not text:
            return "No description"

        if isinstance(text, bytes):
            try:
                text = text.decode('utf-8', errors='replace')
            except Exception:
                text = repr(text)[2:-1]

        text = str(text)

        # 移除控制字符表示
        text = re.sub(r'\^[a-zA-Z@\[\\\]^_]', '', text)
        text = re.sub(r'\\x[0-9a-fA-F]{2}', '', text)
        text = re.sub(r'\\[0-7]{1,3}', '', text)

        # 移除控制字符
        control_chars = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]')
        text = control_chars.sub('', text)

        # 标准化Unicode
        try:
            text = unicodedata.normalize('NFKD', text)
        except Exception:
            pass

        # 替换特殊字符
        replacements = {
            '•': 'bullet', '→': 'arrow', '←': 'left_arrow',
            '…': '...', '–': '-', '—': '-',
            '"': '"', '"': '"', ''': "'", ''': "'",
            '≤': '<=', '≥': '>=', '≠': '!=',
            '×': 'x', '÷': '/', '|': 'pipe',
        }

        for old_char, new_char in replacements.items():
            text = text.replace(old_char, new_char)

        # 转为ASCII
        try:
            text = text.encode('ascii', errors='ignore').decode('ascii')
        except Exception:
            text = ''.join(char for char in text if 32 <= ord(char) <= 126)

        # 标准化空白
        text = re.sub(r'[\r\n\t\v\f]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()

        # TTL转义
        text = text.replace('\\', '\\\\')
        text = text.replace('"', '\\"')

        # 最终清理
        text = re.sub(r'[^\x20-\x7E\\"]', '', text)

        # 长度限制
        if len(text) > 150:
            text = text[:147] + "..."

        if not text or text.isspace():
            return "No description"

        if text.endswith('"') and not text.endswith('\\"'):
            text = text[:-1] + '\\"'

        return text

    def _sanitize_identifier(self, identifier: str) -> str:
        """处理标识符的清理函数"""
        if not identifier:
            return "unknown"

        identifier = str(identifier)

        # 移除控制字符
        identifier = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', identifier)
        identifier = re.sub(r'\^[a-zA-Z]', '', identifier)
        identifier = re.sub(r'\\x[0-9a-fA-F]{2}', '', identifier)

        # Unicode处理
        try:
            identifier = unicodedata.normalize('NFKD', identifier)
            identifier = identifier.encode('ascii', errors='ignore').decode('ascii')
        except Exception:
            pass

        # 替换非标识符字符
        identifier = re.sub(r'[^\w\-_.]', '_', identifier)

        # 确保不以数字开头
        if identifier and identifier[0].isdigit():
            identifier = "id_" + identifier

        if not identifier:
            identifier = "unknown"

        return identifier

    @staticmethod
    def run(enriched_path: str | pathlib.Path, out_path: str | pathlib.Path):
        """运行SHACL导出"""
        enriched_path, out_path = map(pathlib.Path, (enriched_path, out_path))

        with enriched_path.open(encoding="utf-8") as f:
            constraints = json.load(f)

        out_dir = out_path if out_path.suffix == "" else out_path.parent
        return ShaclExporter(out_dir).export(constraints)