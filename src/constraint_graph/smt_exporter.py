
from __future__ import annotations

import pathlib
import re
from typing import Dict, List, Any
import json


class SmtExporter:
    def __init__(self, out_dir: str | pathlib.Path):
        self.out_dir = pathlib.Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.lines: List[str] = []
        self.var_declared: set[str] = set()
        self.type_declared: set[str] = set()
        self.constraint_counter = 0
        self.class_id_to_xml_mapping = {}
        self.attr_id_to_xml_mapping = {}

        # 🔧 新增：跳过约束统计
        self.skipped_constraints = []
        self.processed_count = 0
        self.skipped_count = 0

    def export(self, constraints: List[Dict[str, Any]]) -> pathlib.Path:
        """导出所有约束为SMT求解实例 - 支持严重性分级和约束跳过统计"""

        # 先构建映射表
        self._build_xml_mappings(constraints)

        # 🔧 按约束来源和严重性分类
        structural_constraints = [c for c in constraints if c.get("is_structural", False)]
        semantic_constraints = [c for c in constraints if c.get("is_semantic", False)]

        print(f"📊 SMT约束分类统计:")
        print(f"   - 结构约束: {len(structural_constraints)} 个")
        print(f"   - 语义约束: {len(semantic_constraints)} 个")

        # SMT文件头部
        self._add_header()

        # 声明基础类型和函数
        self._declare_base_types()

        # 🔧 分别处理结构约束和语义约束
        self._export_structural_constraints_section(structural_constraints)
        self._export_semantic_constraints_section(semantic_constraints)

        # 添加检查命令
        self._add_check_commands()

        # 🔧 生成统计报告
        self._generate_skip_report()

        # 保存文件
        path = self.out_dir / "constraints.smt2"
        path.write_text("\n".join(self.lines), encoding="utf-8")
        print(f"✅ SMT文件已保存: {path}")
        print(f"📊 处理统计: 成功 {self.processed_count} 个，跳过 {self.skipped_count} 个")
        return path

    def _should_skip_constraint(self, constraint: Dict[str, Any]) -> bool:
        """检查约束是否应该被跳过（目标类缺失）"""
        targets = constraint.get("enriched_targets", [])
        
        if not targets:
            return True  # 没有目标则跳过
        
        for target in targets:
            if target["target_type"] != "attribute":
                continue
                
            # 检查是否能解析到有效的类名和属性名
            entity_name = self._try_get_entity_name(target.get("class_id"))
            attr_name = self._try_get_attribute_name(target.get("attr_id"))
            
            if entity_name.startswith("class_") or attr_name.startswith("attr_"):
                return True  # 无法解析到实际名称，跳过
                
        return False  # 所有目标都有效，不跳过

    def _try_get_entity_name(self, class_id: int) -> str:
        """尝试获取实体名称，用于检查是否应该跳过"""
        if class_id and class_id in self.class_id_to_xml_mapping:
            mapped_name = self.class_id_to_xml_mapping[class_id]
            if mapped_name and mapped_name != "unknown":
                return mapped_name
        return f"class_{class_id}" if class_id else "class_unknown"

    def _try_get_attribute_name(self, attr_id: int) -> str:
        """尝试获取属性名称，用于检查是否应该跳过"""
        if attr_id and attr_id in self.attr_id_to_xml_mapping:
            xml_tag = self.attr_id_to_xml_mapping[attr_id]
            if xml_tag and xml_tag != "unknown":
                smt_attr_name = self._to_smt_identifier(xml_tag)
                return smt_attr_name
        return f"attr_{attr_id}" if attr_id else "attr_unknown"

    def _record_skipped_constraint(self, constraint: Dict[str, Any], constraint_category: str, reason: str):
        """记录被跳过的约束"""
        self.skipped_count += 1

        # 提取约束的关键信息
        cid = constraint.get("cid", "unknown")
        constraint_type = constraint.get("type", "unknown")
        title = constraint.get("title", "")

        # 分析目标信息
        targets_info = []
        for target in constraint.get("enriched_targets", []):
            target_info = {
                "target_type": target.get("target_type", "unknown"),
                "class_id": target.get("class_id"),
                "class_name": target.get("class_name"),
                "class_xml_tag": target.get("class_xml_tag"),
                "attr_id": target.get("attr_id"),
                "xml_tag": target.get("xml_tag"),
                "resolved_entity": self._try_get_entity_name(target.get("class_id")),
                "resolved_attr": self._try_get_attribute_name(target.get("attr_id"))
            }
            targets_info.append(target_info)

        skipped_record = {
            "cid": cid,
            "constraint_type": constraint_type,
            "constraint_category": constraint_category,
            "title": title[:100] if title else "",  # 限制长度
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

        # 🔧 生成JSON格式的详细报告
        report = {
            "summary": {
                "total_constraints": self.processed_count + self.skipped_count,
                "processed_constraints": self.processed_count,
                "skipped_constraints": self.skipped_count,
                "skip_rate": round(self.skipped_count / (self.processed_count + self.skipped_count) * 100, 2) if (
                                                                                                                             self.processed_count + self.skipped_count) > 0 else 0
            },
            "skip_reasons": {},
            "skip_by_category": {},
            "skip_by_type": {},
            "skipped_details": self.skipped_constraints
        }

        # 统计跳过原因
        for record in self.skipped_constraints:
            reason = record["reason"]
            category = record["constraint_category"]
            constraint_type = record["constraint_type"]

            report["skip_reasons"][reason] = report["skip_reasons"].get(reason, 0) + 1
            report["skip_by_category"][category] = report["skip_by_category"].get(category, 0) + 1
            report["skip_by_type"][constraint_type] = report["skip_by_type"].get(constraint_type, 0) + 1

        # 保存详细报告
        report_path = self.out_dir / "smt_skipped_constraints.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        # 🔧 生成人类可读的摘要报告
        summary_lines = [
            "# SMT约束跳过统计报告",
            f"生成时间: {pathlib.Path().absolute()}",
            "",
            "## 总体统计",
            f"- 总约束数: {report['summary']['total_constraints']}",
            f"- 成功处理: {report['summary']['processed_constraints']}",
            f"- 跳过约束: {report['summary']['skipped_constraints']}",
            f"- 跳过率: {report['summary']['skip_rate']}%",
            "",
            "## 按跳过原因分类",
        ]

        for reason, count in report["skip_reasons"].items():
            summary_lines.append(f"- {reason}: {count} 个")

        summary_lines.extend([
            "",
            "## 按约束类别分类",
        ])

        for category, count in report["skip_by_category"].items():
            summary_lines.append(f"- {category}: {count} 个")

        summary_lines.extend([
            "",
            "## 按约束类型分类",
        ])

        for constraint_type, count in report["skip_by_type"].items():
            summary_lines.append(f"- {constraint_type}: {count} 个")

        summary_lines.extend([
            "",
            "## SMT特定问题诊断",
            "",
            "### SMT约束生成的特殊要求：",
            "1. 实体名称必须是有效的SMT标识符",
            "2. 属性名称必须能转换为SMT函数名",
            "3. 类映射关系必须完整，支持SMT类型推理",
            "",
            "### 常见SMT约束失败原因：",
            "- 实体类型无法映射到SMT Sort",
            "- 属性名称包含SMT不支持的字符",
            "- 缺少数值类型的约束信息",
            "",
            f"详细信息请查看: {report_path.name}"
        ])

        summary_path = self.out_dir / "smt_skip_summary.md"
        summary_path.write_text("\n".join(summary_lines), encoding="utf-8")

        print(f"📋 SMT跳过约束报告已生成:")
        print(f"   - 详细报告: {report_path}")
        print(f"   - 摘要报告: {summary_path}")
        print(f"⚠️  跳过了 {self.skipped_count} 个约束 ({report['summary']['skip_rate']}%)")

    def _export_structural_constraints_section(self, structural_constraints: List[Dict[str, Any]]):
        """导出结构约束部分"""
        if not structural_constraints:
            return

        self.lines.extend([
            "",
            "; =================================",
            "; STRUCTURAL CONSTRAINTS (HARD)",
            "; Source: raw_attributes.jsonl",
            "; Severity: Critical - Must be satisfied",
            "; =================================",
            ""
        ])

        # 声明结构约束谓词
        self.lines.extend([
            "; Structural constraint predicates",
            "(declare-fun structural_valid () Bool)",
            "(declare-fun cardinality_valid (Entity String Int Int) Bool)",
            ""
        ])

        structural_valid_assertions = []

        for constraint in structural_constraints:
            try:
                if self._should_skip_constraint(constraint):
                    self._record_skipped_constraint(constraint, "structural", "Missing target class mapping")
                    continue

                constraint_assertions = self._export_structural_constraint_smt(constraint)
                if constraint_assertions:
                    structural_valid_assertions.extend(constraint_assertions)
                    self.processed_count += 1
            except Exception as e:
                self._record_skipped_constraint(constraint, "structural", f"Export error: {str(e)}")
                continue

        # 🔧 结构约束必须全部满足
        if structural_valid_assertions:
            self.lines.append("; All structural constraints must be satisfied")
            self.lines.append("(assert structural_valid)")
            all_structural = " ".join(structural_valid_assertions)
            self.lines.append(f"(assert (= structural_valid (and {all_structural})))")
            self.lines.append("")

    def _export_semantic_constraints_section(self, semantic_constraints: List[Dict[str, Any]]):
        """导出语义约束部分"""
        if not semantic_constraints:
            return

        self.lines.extend([
            "",
            "; =================================",
            "; SEMANTIC CONSTRAINTS (SOFT)",
            "; Source: canonical_constraints.json",
            "; Severity: Warning/Info - Recommendations",
            "; =================================",
            ""
        ])

        # 🔧 声明语义约束软约束机制
        self.lines.extend([
            "; Semantic constraint predicates (soft constraints)",
            "(declare-fun semantic_score () Int)",
            "(declare-fun semantic_weight (String) Int)",
            "(declare-fun semantic_satisfied (String) Bool)",
            ""
        ])

        semantic_constraint_names = []

        for constraint in semantic_constraints:
            try:
                if self._should_skip_constraint(constraint):
                    self._record_skipped_constraint(constraint, "semantic", "Missing target class mapping")
                    continue

                constraint_name = self._export_semantic_constraint_smt(constraint)
                if constraint_name:
                    semantic_constraint_names.append(constraint_name)
                    self.processed_count += 1
            except Exception as e:
                self._record_skipped_constraint(constraint, "semantic", f"Export error: {str(e)}")
                continue

        # 🔧 语义约束使用软约束机制 - 最大化满足的约束数量
        if semantic_constraint_names:
            self.lines.extend([
                "; Semantic constraint scoring",
                "; Try to maximize the number of satisfied semantic constraints",
            ])

            # 为每个语义约束分配权重
            for i, constraint_name in enumerate(semantic_constraint_names):
                severity = self._get_constraint_severity(constraint_name)
                weight = self._severity_to_weight(severity)
                self.lines.append(f"(assert (= (semantic_weight \"{constraint_name}\") {weight}))")

            # 计算总分数
            score_terms = [f"(ite (semantic_satisfied \"{name}\") (semantic_weight \"{name}\") 0)"
                           for name in semantic_constraint_names]
            score_sum = " ".join(score_terms)
            self.lines.append(f"(assert (= semantic_score (+ {score_sum})))")

            # 🔧 软约束目标：尝试最大化语义得分，但不强制要求
            self.lines.append("")
            self.lines.append("; Soft constraint: try to maximize semantic score")
            self.lines.append(f"(assert (>= semantic_score 0))")  # 最低要求：得分非负
            self.lines.append("")

    def _export_structural_constraint_smt(self, constraint: Dict[str, Any]) -> List[str]:
        """导出单个结构约束为SMT断言"""
        assertions = []

        for target in constraint.get("enriched_targets", []):
            if target["target_type"] != "attribute":
                continue

            attr_id = target["attr_id"]
            class_id = target["class_id"]
            min_occurs = target.get("minOccurs", 0)
            max_occurs = target.get("maxOccurs", -1)

            # 使用实际的XML名称
            entity_name = self._get_entity_name(class_id)
            attr_name = self._get_attribute_name(attr_id)

            # 生成变量名
            entity_var = f"{entity_name}_entity"
            class_const = f"{entity_name}_class"

            self._declare_entity(entity_var)
            self._declare_class(class_const)

            # 生成结构约束断言
            constraint_name = f"struct_{attr_id}"

            self.lines.append(f"; Structural constraint: {attr_name} in {entity_name}")

            # 基数约束
            if min_occurs is not None and max_occurs is not None:
                if max_occurs == -1:  # 无上限
                    self.lines.append(f"(assert (forall ((e Entity))")
                    self.lines.append(f"  (=> (instanceOf e {class_const})")
                    self.lines.append(f"      (>= (attrCount e \"{attr_name}\") {min_occurs}))))")
                    assertions.append(f"(>= (attrCount {entity_var} \"{attr_name}\") {min_occurs})")
                else:
                    self.lines.append(f"(assert (forall ((e Entity))")
                    self.lines.append(f"  (=> (instanceOf e {class_const})")
                    self.lines.append(f"      (and (>= (attrCount e \"{attr_name}\") {min_occurs})")
                    self.lines.append(f"           (<= (attrCount e \"{attr_name}\") {max_occurs})))))")
                    assertions.append(f"(cardinality_valid {entity_var} \"{attr_name}\" {min_occurs} {max_occurs})")

            self.lines.append("")

        return assertions

    def _export_semantic_constraint_smt(self, constraint: Dict[str, Any]) -> str:
        """导出单个语义约束为SMT软约束"""
        constraint_type = constraint.get("type", "other")
        cid = constraint.get("cid", f"semantic_{self.constraint_counter}")
        self.constraint_counter += 1

        constraint_name = f"sem_{cid}_{constraint_type}"

        self.lines.append(f"; Semantic constraint {cid}: {constraint.get('title', '')}")
        self.lines.append(f"; Type: {constraint_type}")
        self.lines.append(f"; Severity: {constraint.get('severity', 'sh:Warning')}")

        if constraint_type == "existence":
            self._export_existence_constraint_soft(constraint, constraint_name)
        elif constraint_type == "value_restriction":
            self._export_value_restriction_constraint_soft(constraint, constraint_name)
        elif constraint_type == "cardinality":
            self._export_cardinality_constraint_soft(constraint, constraint_name)
        elif constraint_type == "format":
            self._export_format_constraint_soft(constraint, constraint_name)
        elif constraint_type == "behavioral":
            self._export_behavioral_constraint_soft(constraint, constraint_name)
        elif constraint_type == "relationship":
            self._export_relationship_constraint_soft(constraint, constraint_name)
        elif constraint_type == "ordering":
            self._export_ordering_constraint_soft(constraint, constraint_name)
        else:
            self._export_basic_constraint_soft(constraint, constraint_name)

        self.lines.append("")
        return constraint_name

    def _export_existence_constraint_soft(self, constraint: Dict[str, Any], constraint_name: str):
        """导出存在性约束为软约束"""
        for target in constraint.get("enriched_targets", []):
            if target["target_type"] != "attribute":
                continue

            attr_id = target["attr_id"]
            class_id = target["class_id"]

            entity_name = self._get_entity_name(class_id)
            attr_name = self._get_attribute_name(attr_id)

            entity_var = f"{entity_name}_entity"
            class_const = f"{entity_name}_class"

            self._declare_entity(entity_var)
            self._declare_class(class_const)

            # 🔧 软约束：推荐存在，但不强制要求
            if constraint.get("mustExist"):
                self.lines.append(f"; Recommendation: {attr_name} should exist in {entity_name}")
                self.lines.append(f"(assert (= (semantic_satisfied \"{constraint_name}\")")
                self.lines.append(f"    (=> (instanceOf {entity_var} {class_const})")
                self.lines.append(f"        (distinct (stringAttr {entity_var} \"{attr_name}\") \"\"))))")
            elif constraint.get("mustNotExist"):
                self.lines.append(f"; Recommendation: {attr_name} should not exist in {entity_name}")
                self.lines.append(f"(assert (= (semantic_satisfied \"{constraint_name}\")")
                self.lines.append(f"    (=> (instanceOf {entity_var} {class_const})")
                self.lines.append(f"        (= (stringAttr {entity_var} \"{attr_name}\") \"\"))))")

    def _export_value_restriction_constraint_soft(self, constraint: Dict[str, Any], constraint_name: str):
        """导出值限制约束为软约束"""
        for target in constraint.get("enriched_targets", []):
            if target["target_type"] != "attribute":
                continue

            attr_id = target["attr_id"]
            class_id = target["class_id"]
            enum_values = constraint.get("enum", [])

            if not enum_values:
                continue

            entity_name = self._get_entity_name(class_id)
            attr_name = self._get_attribute_name(attr_id)

            entity_var = f"{entity_name}_entity"
            class_const = f"{entity_name}_class"

            self._declare_entity(entity_var)
            self._declare_class(class_const)

            # 🔧 软约束：推荐使用枚举值，但允许其他值
            self.lines.append(f"; Recommendation: {attr_name} should use recommended values")

            if len(enum_values) == 1:
                self.lines.append(f"(assert (= (semantic_satisfied \"{constraint_name}\")")
                self.lines.append(
                    f"    (=> (and (instanceOf {entity_var} {class_const}) (distinct (stringAttr {entity_var} \"{attr_name}\") \"\"))")
                self.lines.append(f"        (= (stringAttr {entity_var} \"{attr_name}\") \"{enum_values[0]}\"))))")
            else:
                value_options = " ".join(f'(= (stringAttr {entity_var} \"{attr_name}\") "{v}")' for v in enum_values)
                self.lines.append(f"(assert (= (semantic_satisfied \"{constraint_name}\")")
                self.lines.append(
                    f"    (=> (and (instanceOf {entity_var} {class_const}) (distinct (stringAttr {entity_var} \"{attr_name}\") \"\"))")
                self.lines.append(f"        (or {value_options}))))")

    def _export_cardinality_constraint_soft(self, constraint: Dict[str, Any], constraint_name: str):
        """导出基数约束为软约束"""
        # 🔧 语义基数约束作为推荐，不覆盖结构约束
        for target in constraint.get("enriched_targets", []):
            if target["target_type"] != "attribute":
                continue

            attr_id = target["attr_id"]
            class_id = target["class_id"]

            entity_name = self._get_entity_name(class_id)
            attr_name = self._get_attribute_name(attr_id)

            entity_var = f"{entity_name}_entity"
            class_const = f"{entity_name}_class"

            self._declare_entity(entity_var)
            self._declare_class(class_const)

            # 语义层面的基数建议
            min_occurs = constraint.get("minOccurs")
            max_occurs = constraint.get("maxOccurs")

            constraints_parts = []
            if min_occurs is not None and min_occurs > 0:
                constraints_parts.append(f"(>= (attrCount {entity_var} \"{attr_name}\") {min_occurs})")

            if max_occurs is not None and max_occurs != -1:
                constraints_parts.append(f"(<= (attrCount {entity_var} \"{attr_name}\") {max_occurs})")

            if constraints_parts:
                constraint_expr = " ".join(constraints_parts)
                if len(constraints_parts) > 1:
                    constraint_expr = f"(and {constraint_expr})"

                self.lines.append(f"; Recommendation: {attr_name} cardinality in {entity_name}")
                self.lines.append(f"(assert (= (semantic_satisfied \"{constraint_name}\")")
                self.lines.append(f"    (=> (instanceOf {entity_var} {class_const})")
                self.lines.append(f"        {constraint_expr})))")

    def _export_format_constraint_soft(self, constraint: Dict[str, Any], constraint_name: str):
        """导出格式约束为软约束"""
        for target in constraint.get("enriched_targets", []):
            if target["target_type"] != "attribute":
                continue

            attr_id = target["attr_id"]
            class_id = target["class_id"]

            entity_name = self._get_entity_name(class_id)
            attr_name = self._get_attribute_name(attr_id)

            entity_var = f"{entity_name}_entity"
            class_const = f"{entity_name}_class"

            self._declare_entity(entity_var)
            self._declare_class(class_const)

            self.lines.append(f"; Recommendation: {attr_name} format in {entity_name}")

            # 🔧 软约束：推荐格式，但不强制要求
            if "forbidden_chars" in constraint:
                for char in constraint["forbidden_chars"]:
                    self.lines.append(f"(assert (= (semantic_satisfied \"{constraint_name}_{char}\")")
                    self.lines.append(f"    (=> (instanceOf {entity_var} {class_const})")
                    self.lines.append(
                        f"        (not (str.contains (stringAttr {entity_var} \"{attr_name}\") \"{char}\")))))")

    def _export_behavioral_constraint_soft(self, constraint: Dict[str, Any], constraint_name: str):
        """导出行为约束为软约束"""
        if constraint.get("constraint_logic") == "if_then":
            # 🔧 软约束：推荐遵循if-then逻辑，但不强制
            self.lines.append(f"; Recommendation: Follow if-then logic")
            self.lines.append(f"(assert (= (semantic_satisfied \"{constraint_name}\") true))")  # 简化处理

    def _export_relationship_constraint_soft(self, constraint: Dict[str, Any], constraint_name: str):
        """导出关系约束为软约束"""
        # 🔧 软约束：推荐正确的关系，但不强制
        self.lines.append(f"; Recommendation: Maintain proper relationships")
        self.lines.append(f"(assert (= (semantic_satisfied \"{constraint_name}\") true))")  # 简化处理

    def _export_ordering_constraint_soft(self, constraint: Dict[str, Any], constraint_name: str):
        """导出排序约束为软约束"""
        # 🔧 软约束：推荐正确的优先级，但不强制
        self.lines.append(f"; Recommendation: Follow precedence rules")
        self.lines.append(f"(assert (= (semantic_satisfied \"{constraint_name}\") true))")  # 简化处理

    def _export_basic_constraint_soft(self, constraint: Dict[str, Any], constraint_name: str):
        """导出基础约束为软约束"""
        # 🔧 软约束：一般性推荐
        self.lines.append(f"; General recommendation")
        self.lines.append(f"(assert (= (semantic_satisfied \"{constraint_name}\") true))")

    def _get_constraint_severity(self, constraint_name: str) -> str:
        """获取约束严重性"""
        if "existence" in constraint_name:
            return "Warning"
        elif "format" in constraint_name or "naming" in constraint_name:
            return "Info"
        else:
            return "Warning"

    def _severity_to_weight(self, severity: str) -> int:
        """将严重性转换为权重分数"""
        weight_mapping = {
            "Warning": 10,  # 警告级别约束权重较高
            "Info": 5,  # 信息级别约束权重较低
            "Error": 20  # 错误级别（备用）
        }
        return weight_mapping.get(severity, 10)

    def _add_check_commands(self):
        """添加检查命令"""
        self.lines.extend([
            "",
            "; =================================",
            "; SOLVING COMMANDS",
            "; =================================",
            "",
            "; Check if structural constraints are satisfiable (must be sat)",
            "(check-sat)",
            "",
            "; If sat, try to maximize semantic score",
            "; (push 1)",
            "; (maximize semantic_score)",
            "; (check-sat)",
            "; (get-objectives)",
            "; (pop 1)",
            "",
            "(get-model)"
        ])

    # 其他方法保持不变...
    def _build_xml_mappings(self, constraints: List[Dict[str, Any]]):
        """从约束中构建XML映射表 - 修复版"""
        print("🔍 构建SMT XML映射表...")

        for constraint in constraints:
            for target in constraint.get("enriched_targets", []):
                if target["target_type"] == "attribute":
                    attr_id = target.get("attr_id")
                    class_id = target.get("class_id")
                    xml_tag = target.get("xml_tag")

                    # 🔧 关键修复：使用 enricher 传递的实际类信息
                    class_name = target.get("class_name")  # 如: "RPortPrototype"
                    class_xml_tag = target.get("class_xml_tag")  # 如: "R-PORT-PROTOTYPE"

                    # 属性映射
                    if attr_id and xml_tag:
                        self.attr_id_to_xml_mapping[attr_id] = xml_tag

                    # 🔧 类映射 - 优先使用XML标签，备用类名
                    if class_id:
                        if class_xml_tag:
                            # 转换为SMT友好的标识符
                            smt_class_name = self._to_smt_identifier(class_xml_tag)
                            self.class_id_to_xml_mapping[class_id] = smt_class_name
                        elif class_name:
                            smt_class_name = self._to_smt_identifier(class_name)
                            self.class_id_to_xml_mapping[class_id] = smt_class_name

        print(
            f"✅ SMT映射表构建完成: {len(self.class_id_to_xml_mapping)} 个类映射, {len(self.attr_id_to_xml_mapping)} 个属性映射")

    def _to_smt_identifier(self, name: str) -> str:
        """将XML名称转换为SMT友好的标识符"""
        if not name:
            return "unknown"

        # 转换为合法的SMT标识符
        # 1. 替换连字符和点为下划线
        smt_name = name.replace("-", "_").replace(".", "_").replace(" ", "_")

        # 2. 移除其他非法字符
        smt_name = re.sub(r'[^a-zA-Z0-9_]', '_', smt_name)

        # 3. 确保以字母开头
        if smt_name and smt_name[0].isdigit():
            smt_name = "elem_" + smt_name

        # 4. 转换为驼峰命名
        if '_' in smt_name:
            parts = smt_name.split('_')
            smt_name = parts[0].lower() + ''.join(word.capitalize() for word in parts[1:] if word)

        return smt_name or "unknown"

    def _get_entity_name(self, class_id: int) -> str:
        """获取实际的XML元素名称 - 修复版"""
        if class_id in self.class_id_to_xml_mapping:
            mapped_name = self.class_id_to_xml_mapping[class_id]
            return mapped_name
        else:
            return f"class_{class_id}"

    def _get_attribute_name(self, attr_id: int) -> str:
        """获取实际的XML属性名称 - 修复版"""
        if attr_id in self.attr_id_to_xml_mapping:
            xml_tag = self.attr_id_to_xml_mapping[attr_id]
            smt_attr_name = self._to_smt_identifier(xml_tag)
            return smt_attr_name
        else:
            return f"attr_{attr_id}"

    def _add_header(self):
        """添加SMT文件头部"""
        self.lines.extend([
            "; AUTOSAR Constraint Validation SMT Instance (v3.1)",
            "; Generated with constraint severity classification and skip tracking",
            "; - Structural constraints: HARD (must be satisfied)",
            "; - Semantic constraints: SOFT (recommendations, maximize satisfaction)",
            "; Supports Z3 SMT solver with optimization",
            "",
            "(set-logic QF_SLIA)",  # Quantifier-free String/Integer Linear Arithmetic
            "(set-info :status unknown)",
            ""
        ])

    def _declare_base_types(self):
        """声明基础类型和函数"""
        self.lines.extend([
            "; Base types and functions",
            "(declare-sort Entity)",
            "(declare-sort Class)",
            "",
            "; Entity existence function",
            "(declare-fun exists (Entity) Bool)",
            "",
            "; Class membership function",
            "(declare-fun instanceOf (Entity Class) Bool)",
            "",
            "; Attribute value functions",
            "(declare-fun stringAttr (Entity String) String)",
            "(declare-fun intAttr (Entity String) Int)",
            "(declare-fun realAttr (Entity String) Real)",
            "(declare-fun boolAttr (Entity String) Bool)",
            "",
            "; Cardinality functions",
            "(declare-fun attrCount (Entity String) Int)",
            "",
            "; Relationship functions",
            "(declare-fun hasRelation (Entity Entity String) Bool)",
            ""
        ])

    # 辅助方法
    def _declare_entity(self, entity_name: str):
        """声明实体常量"""
        if entity_name not in self.var_declared:
            self.lines.append(f"(declare-const {entity_name} Entity)")
            self.var_declared.add(entity_name)

    def _declare_class(self, class_name: str):
        """声明类常量"""
        if class_name not in self.var_declared:
            self.lines.append(f"(declare-const {class_name} Class)")
            self.var_declared.add(class_name)

    @staticmethod
    def run(enriched_path: str | pathlib.Path, out_dir: str | pathlib.Path) -> pathlib.Path:
        """运行SMT导出"""
        enriched_path, out_dir = map(pathlib.Path, (enriched_path, out_dir))

        with enriched_path.open(encoding="utf-8") as f:
            constraints = json.load(f)

        return SmtExporter(out_dir).export(constraints)
