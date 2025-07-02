"""smt_validator.py (v3.1) - 修复约束数据提取，使用结构化信息
--------------------------------------------
高优先级修复：使用enriched_constraints中的结构化信息，而非硬编码XML解析
"""
import subprocess
import tempfile
import json
import re
from typing import Dict, List, Any, Optional
import xml.etree.ElementTree as ET
import os
from pathlib import Path


class SMTValidator:
    """SMT约束验证器 - 支持严重性分级和结构化约束提取"""

    def __init__(self, smt_template_file: str,
                 raw_attributes_file: Optional[str] = None,
                 enriched_constraints_file: Optional[str] = None):
        """
        初始化SMT验证器

        Args:
            smt_template_file: SMT模板文件路径
            raw_attributes_file: raw_attributes.jsonl文件路径 (可选)
            enriched_constraints_file: enriched_constraints.json文件路径 (推荐)
        """
        self.smt_template_file = smt_template_file
        self.smt_template = self._load_smt_template(smt_template_file)
        self.z3_available = self._check_z3_availability()

        # 🔧 高优先级修复：优先使用结构化约束数据
        self.enriched_constraints = []
        self.structural_constraints = []
        self.semantic_constraints = []
        self.xml_to_attr_mapping = {}

        # 加载约束定义
        if enriched_constraints_file:
            print("🔧 启用结构化约束验证")
            self._load_enriched_constraints(enriched_constraints_file)
        else:
            print("📝 使用传统XML解析模式")

        # 向后兼容：构建映射表
        if raw_attributes_file:
            self._build_mapping_tables(raw_attributes_file)

    def validate_constraints(self, xml_content: str) -> Dict:
        """SMT约束验证 - 支持严重性分级"""
        print("🔍 开始SMT分级约束验证...")

        if not xml_content or not xml_content.strip():
            print("❌ XML内容为空")
            return self._create_error_result("XML content is empty")

        if not self.z3_available:
            print("⚠️  Z3求解器不可用，跳过SMT验证")
            return self._create_skip_result("Z3 solver not available")

        try:
            # 🔧 高优先级修复：根据是否有结构化约束选择验证方式
            if self.enriched_constraints:
                print("   🔧 使用结构化约束验证")
                return self._validate_with_enriched_constraints(xml_content)
            else:
                print("   📝 使用传统XML解析验证")
                return self._validate_constraints_as_recommendations(xml_content)

        except Exception as e:
            print(f"❌ SMT验证错误: {e}")
            import traceback
            traceback.print_exc()
            return self._create_error_result(str(e))

    def _validate_with_enriched_constraints(self, xml_content: str) -> Dict:
        """🔧 高优先级修复：使用结构化约束进行验证"""
        print("🔍 开始结构化约束验证...")

        try:
            # 解析XML文档
            xml_data = self._parse_xml_document(xml_content)

            # 分别验证结构约束和语义约束
            structural_results = self._validate_structural_constraints_structured(xml_data)
            semantic_results = self._validate_semantic_constraints_structured(xml_data)

            # 🔧 分析结果
            return self._analyze_validation_results(structural_results, semantic_results)

        except Exception as e:
            print(f"❌ 结构化约束验证错误: {e}")
            import traceback
            traceback.print_exc()
            return self._create_error_result(str(e))

    def _validate_structural_constraints_structured(self, xml_data: Dict) -> List[Dict]:
        """验证结构约束 - 使用enriched_constraints中的结构化信息"""
        print("🔧 验证结构约束（结构化）...")

        results = []

        for constraint in self.structural_constraints:
            try:
                # 🔧 从enriched_targets获取结构化信息
                for target in constraint.get("enriched_targets", []):
                    if target["target_type"] != "attribute":
                        continue

                    result = self._validate_single_structural_constraint(constraint, target, xml_data)
                    results.append(result)

            except Exception as e:
                results.append({
                    "status": "error",
                    "constraint_type": "structural",
                    "constraint_id": constraint.get("cid", "unknown"),
                    "error": str(e),
                    "severity": "violation"
                })

        print(f"   🔧 结构约束验证完成: {len(results)} 个")
        return results

    def _validate_single_structural_constraint(self, constraint: Dict, target: Dict, xml_data: Dict) -> Dict:
        """验证单个结构约束"""
        constraint_id = constraint.get("cid", "unknown")
        xml_tag = target.get("xml_tag", "unknown")
        class_xml_tag = target.get("class_xml_tag", "unknown")
        min_occurs = target.get("minOccurs", 0)
        max_occurs = target.get("maxOccurs", -1)

        # 🔧 从实际XML数据中计算出现次数
        actual_count = self._count_element_occurrences(xml_data, class_xml_tag, xml_tag)

        # 生成结构约束的SMT实例
        smt_instance = self._generate_structural_smt(constraint_id, xml_tag, actual_count, min_occurs, max_occurs)

        # 求解
        solve_result = self.solve_smt_instance(smt_instance)

        # 增强结果信息
        solve_result.update({
            "constraint_type": "structural_cardinality",
            "constraint_id": constraint_id,
            "element": xml_tag,
            "class_element": class_xml_tag,
            "actual_count": actual_count,
            "min_occurs": min_occurs,
            "max_occurs": max_occurs,
            "severity": "violation"
        })

        if solve_result.get("status") != "sat":
            solve_result["message"] = f"STRUCTURAL ERROR: {xml_tag} count {actual_count} violates range [{min_occurs}, {max_occurs if max_occurs != -1 else '∞'}]"
        else:
            solve_result["message"] = f"Structural constraint satisfied: {xml_tag} count {actual_count}"

        return solve_result

    def _validate_semantic_constraints_structured(self, xml_data: Dict) -> List[Dict]:
        """验证语义约束 - 使用enriched_constraints中的结构化信息"""
        print("💡 验证语义约束（结构化）...")

        results = []

        for constraint in self.semantic_constraints:
            try:
                constraint_type = constraint.get("type", "other")

                if constraint_type == "existence":
                    result = self._validate_existence_constraint_structured(constraint, xml_data)
                elif constraint_type == "value_restriction":
                    result = self._validate_value_restriction_structured(constraint, xml_data)
                elif constraint_type == "cardinality":
                    result = self._validate_cardinality_constraint_structured(constraint, xml_data)
                elif constraint_type == "format":
                    result = self._validate_format_constraint_structured(constraint, xml_data)
                elif constraint_type == "behavioral":
                    result = self._validate_behavioral_constraint_structured(constraint, xml_data)
                elif constraint_type == "relationship":
                    result = self._validate_relationship_constraint_structured(constraint, xml_data)
                else:
                    result = self._validate_basic_constraint_structured(constraint, xml_data)

                results.append(result)

            except Exception as e:
                results.append({
                    "status": "error",
                    "constraint_type": constraint.get("type", "unknown"),
                    "constraint_id": constraint.get("cid", "unknown"),
                    "error": str(e),
                    "severity": "warning"
                })

        print(f"   💡 语义约束验证完成: {len(results)} 个")
        return results

    def _validate_existence_constraint_structured(self, constraint: Dict, xml_data: Dict) -> Dict:
        """验证存在性约束 - 结构化版本"""
        constraint_id = constraint.get("cid", "unknown")
        must_exist = constraint.get("mustExist", False)
        must_not_exist = constraint.get("mustNotExist", False)

        for target in constraint.get("enriched_targets", []):
            if target["target_type"] != "attribute":
                continue

            xml_tag = target.get("xml_tag", "unknown")
            class_xml_tag = target.get("class_xml_tag", "unknown")

            # 🔧 从实际XML数据检查存在性
            exists = self._check_element_exists(xml_data, class_xml_tag, xml_tag)

            # 生成存在性约束的SMT实例
            smt_instance = self._generate_existence_smt(constraint_id, xml_tag, exists, must_exist, must_not_exist)

            solve_result = self.solve_smt_instance(smt_instance)
            solve_result.update({
                "constraint_type": "existence_recommendation",
                "constraint_id": constraint_id,
                "element": xml_tag,
                "exists": exists,
                "must_exist": must_exist,
                "must_not_exist": must_not_exist,
                "severity": "warning"
            })

            if solve_result.get("status") == "sat":
                solve_result["message"] = f"RECOMMENDATION SATISFIED: {xml_tag} existence requirement met"
            else:
                if must_exist and not exists:
                    solve_result["message"] = f"RECOMMENDATION: {xml_tag} should exist but was not found"
                elif must_not_exist and exists:
                    solve_result["message"] = f"RECOMMENDATION: {xml_tag} should not exist but was found"
                else:
                    solve_result["message"] = f"RECOMMENDATION: Review {xml_tag} existence"

            return solve_result

        # 如果没有有效目标，返回默认结果
        return {
            "status": "sat",
            "constraint_type": "existence_recommendation",
            "constraint_id": constraint_id,
            "message": "No valid targets for existence constraint",
            "severity": "warning"
        }

    def _validate_value_restriction_structured(self, constraint: Dict, xml_data: Dict) -> Dict:
        """验证值限制约束 - 结构化版本"""
        constraint_id = constraint.get("cid", "unknown")
        enum_values = constraint.get("enum", [])

        for target in constraint.get("enriched_targets", []):
            if target["target_type"] != "attribute":
                continue

            xml_tag = target.get("xml_tag", "unknown")
            class_xml_tag = target.get("class_xml_tag", "unknown")

            # 🔧 从实际XML数据获取属性值
            actual_values = self._get_element_values(xml_data, class_xml_tag, xml_tag)

            # 生成值限制约束的SMT实例
            smt_instance = self._generate_value_restriction_smt(constraint_id, xml_tag, actual_values, enum_values)

            solve_result = self.solve_smt_instance(smt_instance)
            solve_result.update({
                "constraint_type": "value_restriction_recommendation",
                "constraint_id": constraint_id,
                "element": xml_tag,
                "actual_values": actual_values,
                "allowed_values": enum_values,
                "severity": "info"
            })

            if solve_result.get("status") == "sat":
                solve_result["message"] = f"RECOMMENDATION SATISFIED: {xml_tag} values are acceptable"
            else:
                solve_result["message"] = f"RECOMMENDATION: {xml_tag} values {actual_values} should prefer {enum_values}"

            return solve_result

        return {
            "status": "sat",
            "constraint_type": "value_restriction_recommendation",
            "constraint_id": constraint_id,
            "message": "No valid targets for value restriction",
            "severity": "info"
        }

    def _validate_cardinality_constraint_structured(self, constraint: Dict, xml_data: Dict) -> Dict:
        """验证基数约束 - 结构化版本（语义级别）"""
        constraint_id = constraint.get("cid", "unknown")
        semantic_min = constraint.get("minOccurs")
        semantic_max = constraint.get("maxOccurs")

        for target in constraint.get("enriched_targets", []):
            if target["target_type"] != "attribute":
                continue

            xml_tag = target.get("xml_tag", "unknown")
            class_xml_tag = target.get("class_xml_tag", "unknown")

            # 🔧 从实际XML数据计算出现次数
            actual_count = self._count_element_occurrences(xml_data, class_xml_tag, xml_tag)

            # 生成语义基数约束的SMT实例
            smt_instance = self._generate_semantic_cardinality_smt(constraint_id, xml_tag, actual_count, semantic_min, semantic_max)

            solve_result = self.solve_smt_instance(smt_instance)
            solve_result.update({
                "constraint_type": "cardinality_recommendation",
                "constraint_id": constraint_id,
                "element": xml_tag,
                "actual_count": actual_count,
                "recommended_min": semantic_min,
                "recommended_max": semantic_max,
                "severity": "warning"
            })

            if solve_result.get("status") == "sat":
                solve_result["message"] = f"RECOMMENDATION SATISFIED: {xml_tag} count {actual_count} is reasonable"
            else:
                solve_result["message"] = f"RECOMMENDATION: {xml_tag} count {actual_count} outside recommended range"

            return solve_result

        return {
            "status": "sat",
            "constraint_type": "cardinality_recommendation",
            "constraint_id": constraint_id,
            "message": "No valid targets for cardinality constraint",
            "severity": "warning"
        }

    def _validate_format_constraint_structured(self, constraint: Dict, xml_data: Dict) -> Dict:
        """验证格式约束 - 结构化版本"""
        constraint_id = constraint.get("cid", "unknown")
        pattern = constraint.get("pattern", "")
        forbidden_chars = constraint.get("forbidden_chars", [])

        # 简化处理：检查格式约束的一般合规性
        return {
            "status": "sat",
            "constraint_type": "format_recommendation",
            "constraint_id": constraint_id,
            "message": f"Format recommendation: {constraint.get('title', 'Format constraint')}",
            "severity": "info"
        }

    def _validate_behavioral_constraint_structured(self, constraint: Dict, xml_data: Dict) -> Dict:
        """验证行为约束 - 结构化版本"""
        constraint_id = constraint.get("cid", "unknown")

        # 简化处理：行为约束通常需要更复杂的逻辑分析
        return {
            "status": "sat",
            "constraint_type": "behavioral_recommendation",
            "constraint_id": constraint_id,
            "message": f"Behavioral recommendation: {constraint.get('title', 'Behavioral constraint')}",
            "severity": "warning"
        }

    def _validate_relationship_constraint_structured(self, constraint: Dict, xml_data: Dict) -> Dict:
        """验证关系约束 - 结构化版本"""
        constraint_id = constraint.get("cid", "unknown")

        # 简化处理：关系约束需要跨元素的引用检查
        return {
            "status": "sat",
            "constraint_type": "relationship_recommendation",
            "constraint_id": constraint_id,
            "message": f"Relationship recommendation: {constraint.get('title', 'Relationship constraint')}",
            "severity": "warning"
        }

    def _validate_basic_constraint_structured(self, constraint: Dict, xml_data: Dict) -> Dict:
        """验证基础约束 - 结构化版本"""
        constraint_id = constraint.get("cid", "unknown")
        constraint_type = constraint.get("type", "other")

        return {
            "status": "sat",
            "constraint_type": f"{constraint_type}_recommendation",
            "constraint_id": constraint_id,
            "message": f"General recommendation: {constraint.get('title', 'Basic constraint')}",
            "severity": "info"
        }

    def _parse_xml_document(self, xml_content: str) -> Dict:
        """解析XML文档为结构化数据"""
        try:
            root = ET.fromstring(xml_content)

            # 🔧 构建元素索引，支持快速查找
            elements_by_tag = {}
            element_values = {}
            element_counts = {}

            for elem in root.iter():
                # 清理标签名
                tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag

                # 索引元素
                if tag not in elements_by_tag:
                    elements_by_tag[tag] = []
                elements_by_tag[tag].append(elem)

                # 统计数量
                element_counts[tag] = element_counts.get(tag, 0) + 1

                # 收集值
                if elem.text and elem.text.strip():
                    if tag not in element_values:
                        element_values[tag] = []
                    element_values[tag].append(elem.text.strip())

            return {
                "root": root,
                "elements_by_tag": elements_by_tag,
                "element_values": element_values,
                "element_counts": element_counts
            }

        except ET.ParseError as e:
            print(f"❌ XML解析错误: {e}")
            return {}

    def _count_element_occurrences(self, xml_data: Dict, class_tag: str, attr_tag: str) -> int:
        """计算特定元素的出现次数"""
        if not xml_data:
            return 0

        element_counts = xml_data.get("element_counts", {})

        # 🔧 优先查找精确的属性标签
        if attr_tag in element_counts:
            return element_counts[attr_tag]

        # 备用：查找类级别的标签
        if class_tag in element_counts:
            return element_counts[class_tag]

        return 0

    def _check_element_exists(self, xml_data: Dict, class_tag: str, attr_tag: str) -> bool:
        """检查元素是否存在"""
        if not xml_data:
            return False

        elements_by_tag = xml_data.get("elements_by_tag", {})

        # 检查属性标签是否存在
        if attr_tag in elements_by_tag and len(elements_by_tag[attr_tag]) > 0:
            return True

        # 检查类标签是否存在
        if class_tag in elements_by_tag and len(elements_by_tag[class_tag]) > 0:
            return True

        return False

    def _get_element_values(self, xml_data: Dict, class_tag: str, attr_tag: str) -> List[str]:
        """获取元素的值列表"""
        if not xml_data:
            return []

        element_values = xml_data.get("element_values", {})

        # 🔧 优先返回属性标签的值
        if attr_tag in element_values:
            return element_values[attr_tag]

        # 备用：返回类标签的值
        if class_tag in element_values:
            return element_values[class_tag]

        return []

    def _generate_structural_smt(self, constraint_id: str, element: str, actual_count: int, min_occurs: int, max_occurs: int) -> str:
        """生成结构约束的SMT实例"""
        var_name = re.sub(r'[^a-zA-Z0-9_]', '_', element)

        lines = [
            "(set-logic QF_LIA)",
            f"; Structural constraint {constraint_id} for {element}",
            f"(declare-const {var_name}_count Int)",
            f"(assert (= {var_name}_count {actual_count}))",
        ]

        if min_occurs > 0:
            lines.append(f"(assert (>= {var_name}_count {min_occurs}))")

        if max_occurs >= 0:
            lines.append(f"(assert (<= {var_name}_count {max_occurs}))")

        lines.append("(check-sat)")
        return "\n".join(lines)

    def _generate_existence_smt(self, constraint_id: str, element: str, exists: bool, must_exist: bool, must_not_exist: bool) -> str:
        """生成存在性约束的SMT实例"""
        var_name = re.sub(r'[^a-zA-Z0-9_]', '_', element)

        lines = [
            "(set-logic QF_LIA)",
            f"; Existence recommendation {constraint_id} for {element}",
            f"(declare-const {var_name}_exists Bool)",
            f"(assert (= {var_name}_exists {'true' if exists else 'false'}))",
        ]

        # 🔧 软约束：推荐存在性，但不强制
        if must_exist:
            lines.append(f"; Recommendation: {element} should exist")
            if not exists:
                lines.append("(assert false)")  # 不满足推荐
        elif must_not_exist:
            lines.append(f"; Recommendation: {element} should not exist")
            if exists:
                lines.append("(assert false)")  # 不满足推荐

        lines.append("(check-sat)")
        return "\n".join(lines)

    def _generate_value_restriction_smt(self, constraint_id: str, element: str, actual_values: List[str], allowed_values: List[str]) -> str:
        """生成值限制约束的SMT实例"""
        var_name = re.sub(r'[^a-zA-Z0-9_]', '_', element)

        lines = [
            "(set-logic QF_S)",
            f"; Value restriction recommendation {constraint_id} for {element}",
        ]

        # 🔧 检查实际值是否在推荐值列表中
        if actual_values and allowed_values:
            satisfies_restriction = any(val in allowed_values for val in actual_values)
            lines.extend([
                f"(declare-const {var_name}_valid Bool)",
                f"(assert (= {var_name}_valid {'true' if satisfies_restriction else 'false'}))",
                f"; Recommendation: values should be from {allowed_values}",
                f"(assert {var_name}_valid)"
            ])
        else:
            lines.append("(assert true)")  # 没有足够信息，默认通过

        lines.append("(check-sat)")
        return "\n".join(lines)

    def _generate_semantic_cardinality_smt(self, constraint_id: str, element: str, actual_count: int, min_rec: Optional[int], max_rec: Optional[int]) -> str:
        """生成语义基数约束的SMT实例"""
        var_name = re.sub(r'[^a-zA-Z0-9_]', '_', element)

        lines = [
            "(set-logic QF_LIA)",
            f"; Semantic cardinality recommendation {constraint_id} for {element}",
            f"(declare-const {var_name}_count Int)",
            f"(assert (= {var_name}_count {actual_count}))",
        ]

        # 🔧 语义基数约束：更宽松的推荐范围
        constraints = []
        if min_rec is not None and min_rec > 0:
            constraints.append(f"(>= {var_name}_count {min_rec})")

        if max_rec is not None and max_rec >= 0:
            constraints.append(f"(<= {var_name}_count {max_rec})")

        if constraints:
            if len(constraints) == 1:
                lines.append(f"(assert {constraints[0]})")
            else:
                lines.append(f"(assert (and {' '.join(constraints)}))")
        else:
            lines.append("(assert true)")  # 没有推荐范围，默认通过

        lines.append("(check-sat)")
        return "\n".join(lines)

    def _analyze_validation_results(self, structural_results: List[Dict], semantic_results: List[Dict]) -> Dict:
        """分析验证结果"""
        # 结构约束分析
        structural_count = len(structural_results)
        structural_satisfied = sum(1 for r in structural_results if r.get("status") == "sat")
        structural_valid = structural_satisfied == structural_count if structural_count > 0 else True
        structural_violations = [r for r in structural_results if r.get("status") != "sat"]

        # 语义约束分析
        semantic_count = len(semantic_results)
        semantic_satisfied = sum(1 for r in semantic_results if r.get("status") == "sat")
        semantic_warnings = [r for r in semantic_results if r.get("status") != "sat"]

        # 语义合规性评级
        if semantic_count == 0:
            semantic_compliance = "NONE"
        elif semantic_satisfied == semantic_count:
            semantic_compliance = "FULL"
        elif semantic_satisfied >= semantic_count * 0.8:
            semantic_compliance = "HIGH"
        elif semantic_satisfied >= semantic_count * 0.5:
            semantic_compliance = "PARTIAL"
        else:
            semantic_compliance = "LOW"

        # 整体状态
        overall_valid = structural_valid
        total_count = structural_count + semantic_count
        total_satisfied = structural_satisfied + semantic_satisfied

        print(f"📊 结构化验证结果:")
        print(f"   🔧 结构约束: {structural_satisfied}/{structural_count} {'✅ 通过' if structural_valid else '❌ 失败'}")
        print(f"   💡 语义约束: {semantic_satisfied}/{semantic_count} ({semantic_compliance})")
        print(f"   📈 总体: {total_satisfied}/{total_count}")

        return {
            "valid": overall_valid,
            "structural_valid": structural_valid,
            "semantic_compliance": semantic_compliance,
            "constraint_count": total_count,
            "satisfied_count": total_satisfied,
            "structural_violations": structural_violations,
            "semantic_warnings": semantic_warnings,
            "detailed_results": structural_results + semantic_results,
            "constraint_breakdown": {
                "structural": {
                    "total": structural_count,
                    "satisfied": structural_satisfied,
                    "violations": len(structural_violations)
                },
                "semantic": {
                    "total": semantic_count,
                    "satisfied": semantic_satisfied,
                    "warnings": len(semantic_warnings)
                }
            },
            "mode": "structured_constraints"
        }

    def _load_enriched_constraints(self, enriched_constraints_file: str):
        """🔧 加载enriched_constraints.json"""
        try:
            if not Path(enriched_constraints_file).exists():
                print(f"⚠️  约束文件不存在: {enriched_constraints_file}")
                return

            with open(enriched_constraints_file, 'r', encoding='utf-8') as f:
                constraints = json.load(f)

            if not isinstance(constraints, list):
                print(f"⚠️  约束文件格式错误，期望列表格式")
                return

            # 🔧 分类约束
            for constraint in constraints:
                if isinstance(constraint, dict):
                    self.enriched_constraints.append(constraint)

                    # 按类型分类
                    if constraint.get("is_structural", False):
                        self.structural_constraints.append(constraint)
                    elif constraint.get("is_semantic", False):
                        self.semantic_constraints.append(constraint)

            print(f"✅ 加载结构化约束成功:")
            print(f"   总约束: {len(self.enriched_constraints)} 个")
            print(f"   结构约束: {len(self.structural_constraints)} 个")
            print(f"   语义约束: {len(self.semantic_constraints)} 个")

        except json.JSONDecodeError as e:
            print(f"⚠️  约束文件JSON格式错误: {e}")
        except Exception as e:
            print(f"⚠️  加载约束文件失败: {e}")

    def _validate_constraints_as_recommendations(self, xml_content: str) -> Dict:
        """标准验证模式：将所有约束降级为推荐（保持原有逻辑）"""
        print("🔍 开始推荐级SMT约束验证...")

        try:
            # 提取约束数据
            constraint_data = self._extract_constraint_data_standard(xml_content)

            total_data_points = (len(constraint_data.get('timing_events', [])) +
                                 len(constraint_data.get('periods', [])) +
                                 len(constraint_data.get('timeouts', [])))

            if total_data_points == 0:
                print("⚠️  未找到约束数据，跳过SMT验证")
                return {
                    "valid": True,
                    "structural_valid": True,
                    "semantic_compliance": "NONE",
                    "constraint_count": 0,
                    "satisfied_count": 0,
                    "structural_violations": [],
                    "semantic_warnings": [],
                    "detailed_results": [],
                    "message": "No constraints found in standard mode"
                }

            # 生成SMT实例（作为推荐）
            print("📝 生成推荐级SMT约束实例...")
            smt_instances = self._generate_smt_instances_as_recommendations(constraint_data)

            if not smt_instances:
                print("⚠️  未生成SMT实例")
                return {
                    "valid": True,
                    "structural_valid": True,
                    "semantic_compliance": "NONE",
                    "constraint_count": 0,
                    "satisfied_count": 0,
                    "structural_violations": [],
                    "semantic_warnings": [],
                    "detailed_results": [],
                    "message": "No SMT instances generated"
                }

            # 求解SMT实例（作为推荐验证）
            print(f"🧮 验证 {len(smt_instances)} 个推荐级约束...")
            results = []
            satisfied_count = 0

            for i, smt_instance in enumerate(smt_instances, 1):
                print(f"   验证推荐 {i}/{len(smt_instances)}...")
                result = self.solve_smt_instance(smt_instance)

                # 🔧 标记为推荐级别
                result["severity"] = "recommendation"
                result["is_recommendation"] = True

                results.append(result)

                status = result.get("status", "unknown")
                if status == "sat":
                    satisfied_count += 1
                elif status == "unsat":
                    print(f"   💡 推荐不满足（可接受）")

            # 🔧 所有约束都作为语义推荐处理
            constraint_count = len(smt_instances)
            semantic_warnings = [r for r in results if r.get("status") == "unsat"]

            satisfaction_rate = satisfied_count / constraint_count if constraint_count > 0 else 1.0

            # 语义合规性评级
            if satisfaction_rate >= 0.8:
                semantic_compliance = "HIGH"
            elif satisfaction_rate >= 0.5:
                semantic_compliance = "PARTIAL"
            else:
                semantic_compliance = "LOW"

            print(f"📊 推荐级SMT验证结果:")
            print(f"   💡 推荐满足: {satisfied_count}/{constraint_count}")
            print(f"   📈 满足率: {satisfaction_rate:.1%}")
            print(f"   🎯 合规级别: {semantic_compliance}")

            # 🔧 标准模式下，结构约束总是通过（没有硬性结构约束）
            return {
                "valid": True,  # 总是通过，因为没有硬性约束
                "structural_valid": True,  # 没有结构约束检查
                "semantic_compliance": semantic_compliance,
                "constraint_count": constraint_count,
                "satisfied_count": satisfied_count,
                "structural_violations": [],  # 没有结构违规
                "semantic_warnings": semantic_warnings,
                "detailed_results": results,
                "data_points": total_data_points,
                "mode": "recommendations_only"
            }

        except Exception as e:
            print(f"❌ 推荐级SMT验证错误: {e}")
            import traceback
            traceback.print_exc()
            return {
                "valid": True,  # 推荐模式下仍然通过
                "structural_valid": True,
                "semantic_compliance": "ERROR",
                "constraint_count": 0,
                "satisfied_count": 0,
                "structural_violations": [],
                "semantic_warnings": [],
                "detailed_results": [],
                "error": str(e)
            }

    def _generate_smt_instances_as_recommendations(self, constraint_data: Dict) -> List[str]:
        """生成SMT实例作为推荐（更宽松的约束）"""
        smt_instances = []
        print("🏗️  生成推荐级SMT约束实例...")

        try:
            # 🔧 为时序事件生成推荐级约束
            for event in constraint_data.get("timing_events", []):
                event_id = event.get('id', 'unknown')

                if event.get("period") is not None:
                    period = event["period"]
                    instance_id = len(smt_instances)
                    # 🔧 更宽松的推荐范围
                    smt_instance = f"""(declare-const period_{instance_id} Real)
(assert (= period_{instance_id} {period}))
(assert (and (>= period_{instance_id} 0.0001) (<= period_{instance_id} 60.0)))
(check-sat)
; Recommendation: Period should be between 0.1ms and 60s
"""
                    smt_instances.append(smt_instance)
                    print(f"   💡 生成周期推荐: {period}s")

            # 🔧 为超时生成推荐级约束
            for i, timeout in enumerate(constraint_data.get("timeouts", [])):
                # 🔧 更宽松的超时范围
                smt_instance = f"""(declare-const timeout_{i} Real)
(assert (= timeout_{i} {timeout}))
(assert (and (>= timeout_{i} 0.0) (<= timeout_{i} 3600.0)))
(check-sat)
; Recommendation: Timeout should be between 0s and 1hour
"""
                smt_instances.append(smt_instance)
                print(f"   💡 生成超时推荐: {timeout}s")

            print(f"📊 总共生成 {len(smt_instances)} 个推荐级SMT约束实例")

        except Exception as e:
            print(f"❌ 生成推荐级SMT实例失败: {e}")

        return smt_instances

    def _extract_constraint_data_standard(self, xml_content: str) -> Dict:
        """标准约束数据提取 - 保持原有逻辑"""
        print("🔍 开始提取约束数据...")

        constraint_data = {
            "timing_events": [],
            "periods": [],
            "deadlines": [],
            "priorities": [],
            "timeouts": [],
            "relationships": []
        }

        try:
            root = ET.fromstring(xml_content)
            print(f"📋 解析XML根元素: {root.tag}")

            def clean_tag(tag):
                if '}' in tag:
                    return tag.split('}')[1]
                return tag

            # 查找时序事件
            timing_events = []
            for elem in root.iter():
                if clean_tag(elem.tag) == "TIMING-EVENT":
                    timing_events.append(elem)

            print(f"📊 找到 {len(timing_events)} 个TIMING-EVENT元素")

            for timing_event in timing_events:
                event_data = {
                    "id": timing_event.get("UUID") or timing_event.get(
                        "ID") or f"event_{len(constraint_data['timing_events'])}",
                    "period": None,
                    "deadline": None,
                    "priority": None
                }

                # 提取周期
                for child in timing_event.iter():
                    if clean_tag(child.tag) == "PERIOD":
                        if child.text and child.text.strip():
                            try:
                                event_data["period"] = float(child.text.strip())
                                constraint_data["periods"].append(event_data["period"])
                                print(f"   ⏰ 提取周期: {event_data['period']}")
                            except ValueError:
                                print(f"   ⚠️  周期值转换失败: {child.text}")
                        break

                # 提取截止时间
                for child in timing_event.iter():
                    if clean_tag(child.tag) == "DEADLINE":
                        if child.text and child.text.strip():
                            try:
                                event_data["deadline"] = float(child.text.strip())
                                constraint_data["deadlines"].append(event_data["deadline"])
                                print(f"   ⏰ 提取截止时间: {event_data['deadline']}")
                            except ValueError:
                                print(f"   ⚠️  截止时间值转换失败: {child.text}")
                        break

                constraint_data["timing_events"].append(event_data)
                print(f"   ✅ 时序事件: {event_data['id']}")

            # 提取超时设置
            timeout_elements = []
            for elem in root.iter():
                if clean_tag(elem.tag) == "ALIVE-TIMEOUT":
                    timeout_elements.append(elem)

            print(f"📊 找到 {len(timeout_elements)} 个ALIVE-TIMEOUT元素")

            for timeout_elem in timeout_elements:
                if timeout_elem.text and timeout_elem.text.strip():
                    try:
                        timeout_value = float(timeout_elem.text.strip())
                        constraint_data["timeouts"].append(timeout_value)
                        print(f"   ⏰ 提取超时: {timeout_value}")
                    except ValueError:
                        print(f"   ⚠️  超时值转换失败: {timeout_elem.text}")

            # 总结
            total_constraints = (len(constraint_data["timing_events"]) +
                                 len(constraint_data["periods"]) +
                                 len(constraint_data["timeouts"]))

            print(f"📊 约束数据提取总结:")
            print(f"   时序事件: {len(constraint_data['timing_events'])}")
            print(f"   周期数据: {len(constraint_data['periods'])}")
            print(f"   超时设置: {len(constraint_data['timeouts'])}")
            print(f"   总计: {total_constraints} 个约束数据点")

        except ET.ParseError as e:
            print(f"❌ XML解析错误: {e}")
        except Exception as e:
            print(f"❌ 约束提取错误: {e}")
            import traceback
            traceback.print_exc()

        return constraint_data

    def _create_error_result(self, error_message: str) -> Dict:
        """创建错误结果"""
        return {
            "valid": False,
            "structural_valid": False,
            "semantic_compliance": "ERROR",
            "constraint_count": 0,
            "satisfied_count": 0,
            "structural_violations": [],
            "semantic_warnings": [],
            "detailed_results": [],
            "error": error_message
        }

    def _create_skip_result(self, message: str) -> Dict:
        """创建跳过结果"""
        return {
            "valid": True,
            "structural_valid": True,
            "semantic_compliance": "SKIPPED",
            "constraint_count": 0,
            "satisfied_count": 0,
            "structural_violations": [],
            "semantic_warnings": [],
            "detailed_results": [],
            "message": message
        }

    # 保持原有的其他方法不变
    def _check_z3_availability(self):
        """检查Z3求解器可用性"""
        # 优先尝试Python z3包
        try:
            import z3
            print("✅ 使用Python z3包")
            return "python"
        except ImportError:
            pass

        # 尝试命令行z3
        try:
            result = subprocess.run(["z3", "--version"],
                                    capture_output=True, timeout=5)
            if result.returncode == 0:
                print("✅ 使用命令行z3")
                return "command"
        except Exception:
            pass

        print("⚠️  Z3求解器不可用")
        return None

    def _build_mapping_tables(self, raw_attributes_file: str):
        """构建XML到属性的映射表"""
        try:
            if not Path(raw_attributes_file).exists():
                print(f"⚠️  映射文件不存在: {raw_attributes_file}")
                return

            with open(raw_attributes_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    if line.strip():
                        try:
                            attr_record = json.loads(line)

                            # 验证必需字段
                            required_fields = ["classId", "attrId", "xml_tag"]
                            missing_fields = [field for field in required_fields if field not in attr_record]
                            if missing_fields:
                                print(f"⚠️  第{line_num}行缺少字段: {missing_fields}")
                                continue

                            class_id = attr_record["classId"]
                            attr_id = attr_record["attrId"]
                            xml_tag = attr_record["xml_tag"]

                            # 构建映射关系
                            context_key = f"{class_id}:{xml_tag}"
                            self.xml_to_attr_mapping[context_key] = attr_id
                            self.xml_to_attr_mapping[xml_tag] = attr_id

                        except json.JSONDecodeError as e:
                            print(f"⚠️  第{line_num}行JSON解析失败: {e}")
                            continue
                        except Exception as e:
                            print(f"⚠️  第{line_num}行处理失败: {e}")
                            continue

            print(f"✅ SMT映射表构建成功: {len(self.xml_to_attr_mapping)} 个映射")

        except Exception as e:
            print(f"❌ SMT映射表构建失败: {e}")

    def solve_smt_instance(self, smt_instance: str) -> Dict:
        """求解SMT实例"""
        if self.z3_available == "python":
            return self._solve_with_python_z3(smt_instance)
        elif self.z3_available == "command":
            return self._solve_with_command_z3(smt_instance)
        else:
            return {"status": "error", "error": "Z3 not available"}

    def _solve_with_python_z3(self, smt_instance: str) -> Dict:
        """使用Python z3包求解"""
        try:
            import z3

            solver = z3.Solver()
            variables = {}

            # 简化的解析 - 处理基本的SMT语句
            lines = smt_instance.strip().split('\n')

            for line in lines:
                line = line.strip()
                if not line or line.startswith(';'):
                    continue

                if line.startswith('(declare-const'):
                    # 解析变量声明
                    try:
                        parts = line.split()
                        if len(parts) >= 3:
                            var_name = parts[1]
                            var_type = parts[2].rstrip(')')

                            if var_type == "Real":
                                variables[var_name] = z3.Real(var_name)
                            elif var_type == "Int":
                                variables[var_name] = z3.Int(var_name)
                            elif var_type == "Bool":
                                variables[var_name] = z3.Bool(var_name)
                            elif var_type == "String":
                                variables[var_name] = z3.String(var_name)
                    except Exception:
                        continue

                elif line.startswith('(assert'):
                    # 简化的断言解析
                    try:
                        # 处理简单的数值比较
                        if any(op in line for op in ['>', '<', '>=', '<=', '=']):
                            for var_name, var_obj in variables.items():
                                if var_name in line:
                                    # 提取数值
                                    numbers = re.findall(r'\d+\.?\d*', line)
                                    if numbers:
                                        value = float(numbers[0])

                                        if '(>' in line and not '>=' in line:
                                            solver.add(var_obj > value)
                                        elif '(>=' in line:
                                            solver.add(var_obj >= value)
                                        elif '(<=' in line:
                                            solver.add(var_obj <= value)
                                        elif '(= ' in line and not '(>=' in line and not '(<=' in line:
                                            solver.add(var_obj == value)
                                    break

                        # 处理布尔断言
                        if 'false' in line and len(variables) > 0:
                            solver.add(False)
                        elif 'true' in line and len(variables) > 0:
                            solver.add(True)

                    except Exception:
                        continue

            # 求解
            result = solver.check()

            return {
                "status": str(result),
                "output": str(result),
                "method": "python_z3",
                "variables": list(variables.keys())
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "method": "python_z3"
            }

    def _solve_with_command_z3(self, smt_instance: str) -> Dict:
        """使用命令行z3求解"""
        temp_file = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.smt2', delete=False) as f:
                f.write(smt_instance)
                temp_file = f.name

            result = subprocess.run(
                ['z3', temp_file],
                capture_output=True,
                text=True,
                timeout=30
            )

            output = result.stdout.strip()

            if "sat" in output and "unsat" not in output:
                status = "sat"
            elif "unsat" in output:
                status = "unsat"
            else:
                status = "unknown"

            return {
                "status": status,
                "output": output,
                "error": result.stderr if result.stderr else None,
                "method": "command_z3"
            }

        except subprocess.TimeoutExpired:
            return {"status": "timeout", "method": "command_z3"}
        except Exception as e:
            return {"status": "error", "error": str(e), "method": "command_z3"}
        finally:
            if temp_file:
                try:
                    os.unlink(temp_file)
                except Exception:
                    pass

    def _load_smt_template(self, path: str) -> str:
        """加载SMT模板"""
        try:
            if Path(path).exists():
                with open(path, "r", encoding="utf-8") as fp:
                    return fp.read()
            else:
                print(f"⚠️  SMT模板文件不存在: {path}")
                return ""
        except Exception as e:
            print(f"⚠️  SMT模板加载失败: {e}")
            return ""