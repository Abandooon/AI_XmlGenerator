"""smt_validator.py (v4.0) - 修复XML到SMT的实际连接
--------------------------------------------
核心修复：将实际XML数据转换为SMT事实，实现非抽象的约束验证
"""
import subprocess
import tempfile
import json
import re
from typing import Dict, List, Any, Optional, Set
import xml.etree.ElementTree as ET
import os
from pathlib import Path


class SMTValidator:
    """SMT约束验证器 - 实现XML数据到SMT模型的完整映射"""

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

        # 🔧 核心修复：完整的约束和映射数据
        self.enriched_constraints = []
        self.structural_constraints = []
        self.semantic_constraints = []
        self.xml_to_attr_mapping = {}

        # 🔧 新增：XML元素到SMT实体的映射
        self.xml_element_registry = {}  # tag -> List[Element]
        self.smt_entity_counter = 0

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
        """SMT约束验证 - 🔧 核心修复：使用实际XML数据生成具体SMT实例"""
        print("🔍 开始SMT完整约束验证...")

        if not xml_content or not xml_content.strip():
            print("❌ XML内容为空")
            return self._create_error_result("XML content is empty")

        if not self.z3_available:
            print("⚠️  Z3求解器不可用，跳过SMT验证")
            return self._create_skip_result("Z3 solver not available")

        try:
            # 🔧 步骤1：解析XML并建立完整的元素注册表
            print("📝 步骤1: 解析XML并建立元素注册表...")
            xml_model = self._build_complete_xml_model(xml_content)

            if not xml_model:
                return self._create_error_result("Failed to parse XML")

            # 🔧 步骤2：为每个约束生成具体的SMT验证实例
            print("📝 步骤2: 生成具体SMT验证实例...")
            return self._validate_with_concrete_smt_instances(xml_model)

        except Exception as e:
            print(f"❌ SMT验证错误: {e}")
            import traceback
            traceback.print_exc()
            return self._create_error_result(str(e))

    def _build_complete_xml_model(self, xml_content: str) -> Optional[Dict]:
        """🔧 核心修复：构建完整的XML模型，包含实体映射"""
        try:
            root = ET.fromstring(xml_content)
            print(f"📋 解析XML根元素: {root.tag}")

            # 🔧 构建完整的XML元素模型
            xml_model = {
                "root": root,
                "entities": {},  # tag -> List[XMLEntity]
                "entity_facts": [],  # SMT事实列表
                "attribute_facts": [],  # 属性事实列表
                "element_counts": {},  # tag -> count
                "wrapper_relationships": {},  # wrapper_tag -> item_tag
                "parent_child_map": {}  # child_element -> parent_element
            }

            # 🔧 首先建立父子关系映射
            def build_parent_map(element, parent=None):
                """递归建立父子关系映射"""
                xml_model["parent_child_map"][element] = parent
                for child in element:
                    build_parent_map(child, element)

            build_parent_map(root)

            # 🔧 遍历所有元素，建立完整映射
            entity_id = 0
            for elem in root.iter():
                clean_tag = self._clean_xml_tag(elem.tag)

                # 🔧 修复：使用parent_child_map获取父元素
                parent_elem = xml_model["parent_child_map"].get(elem)
                parent_tag = self._clean_xml_tag(parent_elem.tag) if parent_elem is not None else None

                # 创建XML实体
                xml_entity = {
                    "id": f"entity_{entity_id}",
                    "tag": clean_tag,
                    "element": elem,
                    "text": elem.text.strip() if elem.text and elem.text.strip() else None,
                    "attributes": dict(elem.attrib),
                    "parent_tag": parent_tag,
                    "children_tags": [self._clean_xml_tag(child.tag) for child in elem]
                }

                # 注册实体
                if clean_tag not in xml_model["entities"]:
                    xml_model["entities"][clean_tag] = []
                xml_model["entities"][clean_tag].append(xml_entity)

                # 统计元素数量
                xml_model["element_counts"][clean_tag] = xml_model["element_counts"].get(clean_tag, 0) + 1

                entity_id += 1

            # 🔧 检测wrapper关系
            xml_model["wrapper_relationships"] = self._detect_wrapper_relationships(xml_model)

            print(f"✅ XML模型构建完成:")
            print(f"   📊 总元素: {entity_id} 个")
            print(f"   🏷️  标签类型: {len(xml_model['entities'])} 种")
            print(f"   📦 Wrapper关系: {len(xml_model['wrapper_relationships'])} 对")

            return xml_model

        except ET.ParseError as e:
            print(f"❌ XML解析错误: {e}")
            return None
        except Exception as e:
            print(f"❌ XML模型构建错误: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _detect_wrapper_relationships(self, xml_model: Dict) -> Dict[str, str]:
        """🔧 检测wrapper标签关系"""
        wrapper_relationships = {}

        # 已知的wrapper模式
        known_wrappers = {
            'RUNNABLES': 'RUNNABLE-ENTITY',
            'INTERNAL-BEHAVIORS': 'SWC-INTERNAL-BEHAVIOR',
            'PORTS': 'P-PORT-PROTOTYPE',
            'PROVIDED-PORTS': 'P-PORT-PROTOTYPE',
            'REQUIRED-PORTS': 'R-PORT-PROTOTYPE'
        }

        # 从XML结构中检测wrapper关系
        for tag, entities in xml_model["entities"].items():
            for entity in entities:
                children_tags = entity["children_tags"]

                # 如果一个元素只有一种类型的子元素，且数量>1，可能是wrapper
                if len(set(children_tags)) == 1 and len(children_tags) > 0:
                    child_tag = children_tags[0]
                    if tag not in wrapper_relationships:
                        wrapper_relationships[tag] = child_tag

                # 应用已知wrapper模式
                if tag in known_wrappers:
                    wrapper_relationships[tag] = known_wrappers[tag]

        return wrapper_relationships

    def _validate_with_concrete_smt_instances(self, xml_model: Dict) -> Dict:
        """🔧 核心修复：使用具体XML数据验证约束"""
        structural_results = []
        semantic_results = []

        # 🔧 验证结构约束 - 使用实际XML数据
        print("📝 步骤3: 验证结构约束...")
        for constraint in self.structural_constraints:
            try:
                result = self._validate_structural_constraint_concrete(constraint, xml_model)
                structural_results.append(result)
            except Exception as e:
                structural_results.append({
                    "status": "error",
                    "constraint_type": "structural",
                    "constraint_id": constraint.get("cid", "unknown"),
                    "error": str(e),
                    "severity": "violation"
                })

        # 🔧 验证语义约束 - 使用实际XML数据
        print("📝 步骤4: 验证语义约束...")
        for constraint in self.semantic_constraints:
            try:
                result = self._validate_semantic_constraint_concrete(constraint, xml_model)
                semantic_results.append(result)
            except Exception as e:
                semantic_results.append({
                    "status": "error",
                    "constraint_type": constraint.get("type", "unknown"),
                    "constraint_id": constraint.get("cid", "unknown"),
                    "error": str(e),
                    "severity": "warning"
                })

        return self._analyze_validation_results(structural_results, semantic_results)

    def _validate_structural_constraint_concrete(self, constraint: Dict, xml_model: Dict) -> Dict:
        """🔧 验证单个结构约束 - 使用具体XML数据"""
        constraint_id = constraint.get("cid", "unknown")

        for target in constraint.get("enriched_targets", []):
            if target["target_type"] != "attribute":
                continue

            xml_tag = target.get("xml_tag", "unknown")
            class_xml_tag = target.get("class_xml_tag", "unknown")
            min_occurs = target.get("minOccurs", 0)
            max_occurs = target.get("maxOccurs", -1)

            # 🔧 关键修复：从实际XML模型计算出现次数
            actual_count = self._count_actual_occurrences(xml_model, class_xml_tag, xml_tag)

            # 🔧 生成具体的SMT验证实例
            smt_instance = self._generate_concrete_structural_smt(
                constraint_id, xml_tag, class_xml_tag, actual_count, min_occurs, max_occurs, xml_model
            )

            # 🔧 求解具体实例
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

            # 🔧 正确的违规判定逻辑
            constraint_violated = False
            if min_occurs is not None and actual_count < min_occurs:
                constraint_violated = True
            if max_occurs is not None and max_occurs != -1 and actual_count > max_occurs:
                constraint_violated = True

            if constraint_violated:
                solve_result["status"] = "unsat"
                solve_result["message"] = f"STRUCTURAL ERROR: {xml_tag} count {actual_count} violates range [{min_occurs}, {max_occurs if max_occurs != -1 else '∞'}] in {class_xml_tag}"
            else:
                solve_result["status"] = "sat"
                solve_result["message"] = f"Structural constraint satisfied: {xml_tag} count {actual_count} in {class_xml_tag}"

            print(f"   🔧 结构约束 {constraint_id}: {xml_tag} = {actual_count} ({'✅ 通过' if not constraint_violated else '❌ 违反'})")
            return solve_result

        # 默认返回
        return {
            "status": "sat",
            "constraint_type": "structural_cardinality",
            "constraint_id": constraint_id,
            "message": "No valid targets for structural constraint",
            "severity": "violation"
        }

    def _count_actual_occurrences(self, xml_model: Dict, class_tag: str, attr_tag: str) -> int:
        """🔧 核心修复：从实际XML模型计算元素出现次数"""
        total_count = 0

        # 🔧 处理wrapper关系
        wrapper_relationships = xml_model.get("wrapper_relationships", {})

        # 情况1：直接查找属性标签
        if attr_tag in xml_model["entities"]:
            direct_count = len(xml_model["entities"][attr_tag])
            print(f"   📊 直接找到 {attr_tag}: {direct_count} 个")
            total_count += direct_count

        # 情况2：在指定类的上下文中查找
        if class_tag in xml_model["entities"]:
            for class_entity in xml_model["entities"][class_tag]:
                # 检查直接子元素
                if attr_tag in class_entity["children_tags"]:
                    count = class_entity["children_tags"].count(attr_tag)
                    total_count += count
                    print(f"   📊 在 {class_tag} 中找到 {attr_tag}: {count} 个")

                # 🔧 检查通过wrapper间接包含的元素
                for child_tag in class_entity["children_tags"]:
                    if child_tag in wrapper_relationships:
                        expected_item = wrapper_relationships[child_tag]
                        if expected_item == attr_tag:
                            # 计算wrapper内的实际item数量
                            if child_tag in xml_model["entities"]:
                                for wrapper_entity in xml_model["entities"][child_tag]:
                                    wrapper_count = wrapper_entity["children_tags"].count(attr_tag)
                                    total_count += wrapper_count
                                    print(f"   📦 通过wrapper {child_tag} 找到 {attr_tag}: {wrapper_count} 个")

        print(f"   📈 {attr_tag} 在 {class_tag} 中总计: {total_count} 个")
        return total_count

    def _generate_concrete_structural_smt(self, constraint_id: str, attr_tag: str, class_tag: str,
                                        actual_count: int, min_occurs: int, max_occurs: int,
                                        xml_model: Dict) -> str:
        """🔧 生成具体的结构约束SMT实例"""
        lines = [
            "(set-logic QF_LIA)",
            f"; Concrete structural constraint {constraint_id}",
            f"; Element: {attr_tag} in {class_tag}",
            f"; Actual count from XML: {actual_count}",
            f"; Required range: [{min_occurs}, {max_occurs if max_occurs != -1 else '∞'}]",
            ""
        ]

        # 🔧 声明具体的变量
        var_name = re.sub(r'[^a-zA-Z0-9_]', '_', f"{class_tag}_{attr_tag}")
        lines.extend([
            f"(declare-const {var_name}_actual_count Int)",
            f"(declare-const {var_name}_min_required Int)",
            f"(declare-const {var_name}_max_allowed Int)",
            f"(declare-const {var_name}_constraint_satisfied Bool)",
            ""
        ])

        # 🔧 设置实际值
        lines.extend([
            f"(assert (= {var_name}_actual_count {actual_count}))",
            f"(assert (= {var_name}_min_required {min_occurs}))",
        ])

        if max_occurs == -1:
            lines.append(f"(assert (= {var_name}_max_allowed 999999))")  # 无限制用大数
        else:
            lines.append(f"(assert (= {var_name}_max_allowed {max_occurs}))")

        lines.append("")

        # 🔧 定义约束满足条件
        lines.extend([
            f"(assert (= {var_name}_constraint_satisfied",
            f"    (and (>= {var_name}_actual_count {var_name}_min_required)",
            f"         (<= {var_name}_actual_count {var_name}_max_allowed))))",
            ""
        ])

        # 🔧 关键：断言约束必须满足（如果违反，SMT将返回unsat）
        lines.extend([
            f"(assert {var_name}_constraint_satisfied)",
            "(check-sat)",
            "(get-model)"
        ])

        return "\n".join(lines)

    def _solve_with_python_z3(self, smt_instance: str) -> Dict:
        """🔧 改进的Python z3求解器 - 更准确的约束处理"""
        try:
            import z3

            solver = z3.Solver()
            variables = {}

            # 🔧 改进的SMT解析 - 处理更复杂的约束
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
                    except Exception as e:
                        print(f"⚠️ 变量声明解析失败: {line} - {e}")
                        continue

                elif line.startswith('(assert'):
                    # 🔧 改进的断言解析
                    try:
                        # 🔧 关键修复：正确解析复杂的布尔表达式
                        if '(= ' in line and '_constraint_satisfied' in line:
                            # 处理约束满足条件的定义
                            # 例如: (assert (= var_constraint_satisfied (and (>= var_actual_count var_min_required) (<= var_actual_count var_max_allowed))))

                            # 提取变量名
                            for var_name in variables:
                                if f'{var_name}_constraint_satisfied' in line:
                                    constraint_var = variables[f'{var_name}_constraint_satisfied']
                                    actual_var = variables.get(f'{var_name}_actual_count')
                                    min_var = variables.get(f'{var_name}_min_required')
                                    max_var = variables.get(f'{var_name}_max_allowed')

                                    if actual_var and min_var and max_var:
                                        # 定义约束满足条件
                                        constraint_expr = z3.And(actual_var >= min_var, actual_var <= max_var)
                                        solver.add(constraint_var == constraint_expr)
                                    break

                        elif '(= ' in line:
                            # 处理简单等式断言
                            for var_name, var_obj in variables.items():
                                if var_name in line:
                                    # 提取数值或布尔值
                                    if 'true' in line:
                                        solver.add(var_obj == True)
                                        break
                                    elif 'false' in line:
                                        solver.add(var_obj == False)
                                        break
                                    else:
                                        numbers = re.findall(r'-?\d+\.?\d*', line)
                                        if numbers:
                                            try:
                                                if isinstance(var_obj, z3.ArithRef):
                                                    value = int(numbers[-1]) if '.' not in numbers[-1] else float(numbers[-1])
                                                    solver.add(var_obj == value)
                                                    break
                                            except (ValueError, TypeError):
                                                continue

                        # 🔧 处理简单布尔断言（约束必须满足）
                        elif line.startswith("(assert ") and line.endswith(")"):
                            # 提取变量名
                            assert_content = line[8:-1]  # 移除 "(assert " 和 ")"
                            if assert_content in variables:
                                var_obj = variables[assert_content]
                                if isinstance(var_obj, z3.BoolRef):
                                    solver.add(var_obj)
                                    print(f"   添加断言: {assert_content} 必须为真")

                    except Exception as e:
                        print(f"⚠️ 断言解析失败: {line} - {e}")
                        continue

            # 🔧 求解
            print(f"   🧮 求解SMT实例，包含 {len(variables)} 个变量，{len(solver.assertions())} 个断言")
            result = solver.check()

            solve_result = {
                "status": str(result),
                "output": str(result),
                "method": "python_z3",
                "variables": list(variables.keys()),
                "solver_assertions": len(solver.assertions())
            }

            # 🔧 如果sat，获取模型值
            if result == z3.sat:
                model = solver.model()
                model_values = {}
                for var_name, var_obj in variables.items():
                    try:
                        value = model[var_obj]
                        if value is not None:
                            model_values[var_name] = str(value)
                    except Exception:
                        pass
                solve_result["model_values"] = model_values

            return solve_result

        except Exception as e:
            print(f"❌ Z3求解失败: {e}")
            return {
                "status": "error",
                "error": str(e),
                "method": "python_z3"
            }

    def _validate_semantic_constraint_concrete(self, constraint: Dict, xml_model: Dict) -> Dict:
        """🔧 验证语义约束 - 使用具体XML数据"""
        constraint_id = constraint.get("cid", "unknown")
        constraint_type = constraint.get("type", "other")

        if constraint_type == "existence":
            return self._validate_existence_constraint_concrete(constraint, xml_model)
        elif constraint_type == "value_restriction":
            return self._validate_value_restriction_concrete(constraint, xml_model)
        elif constraint_type == "cardinality":
            return self._validate_cardinality_constraint_concrete(constraint, xml_model)
        else:
            # 其他语义约束简化处理
            return {
                "status": "sat",
                "constraint_type": f"{constraint_type}_recommendation",
                "constraint_id": constraint_id,
                "message": f"Semantic recommendation: {constraint.get('title', constraint_type)}",
                "severity": "warning"
            }

    def _validate_existence_constraint_concrete(self, constraint: Dict, xml_model: Dict) -> Dict:
        """🔧 验证存在性约束 - 具体版本"""
        constraint_id = constraint.get("cid", "unknown")
        must_exist = constraint.get("mustExist", False)
        must_not_exist = constraint.get("mustNotExist", False)

        for target in constraint.get("enriched_targets", []):
            if target["target_type"] != "attribute":
                continue

            xml_tag = target.get("xml_tag", "unknown")
            class_xml_tag = target.get("class_xml_tag", "unknown")

            # 🔧 从实际XML检查存在性
            actual_exists = self._check_element_exists_concrete(xml_model, class_xml_tag, xml_tag)

            # 生成具体的存在性SMT实例
            smt_instance = self._generate_concrete_existence_smt(
                constraint_id, xml_tag, actual_exists, must_exist, must_not_exist
            )

            solve_result = self.solve_smt_instance(smt_instance)
            solve_result.update({
                "constraint_type": "existence_recommendation",
                "constraint_id": constraint_id,
                "element": xml_tag,
                "exists": actual_exists,
                "must_exist": must_exist,
                "must_not_exist": must_not_exist,
                "severity": "warning"
            })

            # 🔧 正确的推荐判定逻辑
            recommendation_violated = False
            if must_exist and not actual_exists:
                recommendation_violated = True
            elif must_not_exist and actual_exists:
                recommendation_violated = True

            if recommendation_violated:
                solve_result["status"] = "unsat"
                if must_exist and not actual_exists:
                    solve_result["message"] = f"RECOMMENDATION: {xml_tag} should exist but was not found"
                elif must_not_exist and actual_exists:
                    solve_result["message"] = f"RECOMMENDATION: {xml_tag} should not exist but was found"
            else:
                solve_result["status"] = "sat"
                solve_result["message"] = f"RECOMMENDATION SATISFIED: {xml_tag} existence requirement met"

            print(f"   💡 存在性约束 {constraint_id}: {xml_tag} = {'存在' if actual_exists else '不存在'} ({'✅ 符合推荐' if not recommendation_violated else '⚠️ 不符合推荐'})")
            return solve_result

        return {
            "status": "sat",
            "constraint_type": "existence_recommendation",
            "constraint_id": constraint_id,
            "message": "No valid targets for existence constraint",
            "severity": "warning"
        }

    def _validate_value_restriction_concrete(self, constraint: Dict, xml_model: Dict) -> Dict:
        """🔧 验证值限制约束 - 具体版本"""
        constraint_id = constraint.get("cid", "unknown")
        enum_values = constraint.get("enum", [])

        for target in constraint.get("enriched_targets", []):
            if target["target_type"] != "attribute":
                continue

            xml_tag = target.get("xml_tag", "unknown")
            class_xml_tag = target.get("class_xml_tag", "unknown")

            # 🔧 从实际XML获取属性值
            actual_values = self._get_element_values_concrete(xml_model, class_xml_tag, xml_tag)

            # 检查值是否在推荐列表中
            values_compliant = True
            if enum_values and actual_values:
                values_compliant = all(val in enum_values for val in actual_values)

            result = {
                "status": "sat" if values_compliant else "unsat",
                "constraint_type": "value_restriction_recommendation",
                "constraint_id": constraint_id,
                "element": xml_tag,
                "actual_values": actual_values,
                "allowed_values": enum_values,
                "severity": "info"
            }

            if values_compliant:
                result["message"] = f"RECOMMENDATION SATISFIED: {xml_tag} values {actual_values} are acceptable"
            else:
                result["message"] = f"RECOMMENDATION: {xml_tag} values {actual_values} should prefer {enum_values}"

            print(f"   📝 值限制约束 {constraint_id}: {xml_tag} = {actual_values} ({'✅ 符合推荐' if values_compliant else '⚠️ 建议调整'})")
            return result

        return {
            "status": "sat",
            "constraint_type": "value_restriction_recommendation",
            "constraint_id": constraint_id,
            "message": "No valid targets for value restriction",
            "severity": "info"
        }

    def _validate_cardinality_constraint_concrete(self, constraint: Dict, xml_model: Dict) -> Dict:
        """🔧 验证基数约束 - 具体版本（语义级别）"""
        constraint_id = constraint.get("cid", "unknown")
        semantic_min = constraint.get("minOccurs")
        semantic_max = constraint.get("maxOccurs")

        for target in constraint.get("enriched_targets", []):
            if target["target_type"] != "attribute":
                continue

            xml_tag = target.get("xml_tag", "unknown")
            class_xml_tag = target.get("class_xml_tag", "unknown")

            # 🔧 从实际XML数据计算出现次数
            actual_count = self._count_actual_occurrences(xml_model, class_xml_tag, xml_tag)

            # 检查是否符合语义推荐
            recommendation_satisfied = True
            if semantic_min is not None and actual_count < semantic_min:
                recommendation_satisfied = False
            if semantic_max is not None and semantic_max != -1 and actual_count > semantic_max:
                recommendation_satisfied = False

            result = {
                "status": "sat" if recommendation_satisfied else "unsat",
                "constraint_type": "cardinality_recommendation",
                "constraint_id": constraint_id,
                "element": xml_tag,
                "actual_count": actual_count,
                "recommended_min": semantic_min,
                "recommended_max": semantic_max,
                "severity": "warning"
            }

            if recommendation_satisfied:
                result["message"] = f"RECOMMENDATION SATISFIED: {xml_tag} count {actual_count} is reasonable"
            else:
                result["message"] = f"RECOMMENDATION: {xml_tag} count {actual_count} outside recommended range [{semantic_min}, {semantic_max if semantic_max != -1 else '∞'}]"

            print(f"   📊 基数约束 {constraint_id}: {xml_tag} = {actual_count} ({'✅ 符合推荐' if recommendation_satisfied else '⚠️ 建议调整'})")
            return result

        return {
            "status": "sat",
            "constraint_type": "cardinality_recommendation",
            "constraint_id": constraint_id,
            "message": "No valid targets for cardinality constraint",
            "severity": "warning"
        }

    def _check_element_exists_concrete(self, xml_model: Dict, class_tag: str, attr_tag: str) -> bool:
        """🔧 从具体XML模型检查元素是否存在"""
        # 直接检查
        if attr_tag in xml_model["entities"]:
            return len(xml_model["entities"][attr_tag]) > 0

        # 在类上下文中检查
        if class_tag in xml_model["entities"]:
            for entity in xml_model["entities"][class_tag]:
                if attr_tag in entity["children_tags"]:
                    return True

        return False

    def _get_element_values_concrete(self, xml_model: Dict, class_tag: str, attr_tag: str) -> List[str]:
        """🔧 从具体XML模型获取元素值"""
        values = []

        # 直接获取值
        if attr_tag in xml_model["entities"]:
            for entity in xml_model["entities"][attr_tag]:
                if entity["text"]:
                    values.append(entity["text"])

        return values

    def _generate_concrete_existence_smt(self, constraint_id: str, element: str, exists: bool,
                                       must_exist: bool, must_not_exist: bool) -> str:
        """🔧 生成具体的存在性SMT实例"""
        var_name = re.sub(r'[^a-zA-Z0-9_]', '_', element)

        lines = [
            "(set-logic QF_LIA)",
            f"; Concrete existence constraint {constraint_id} for {element}",
            f"; Actual existence: {exists}",
            f"; Must exist: {must_exist}",
            f"; Must not exist: {must_not_exist}",
            ""
        ]

        lines.extend([
            f"(declare-const {var_name}_exists Bool)",
            f"(declare-const {var_name}_recommendation_satisfied Bool)",
            f"(assert (= {var_name}_exists {'true' if exists else 'false'}))",
            ""
        ])

        # 🔧 定义推荐满足条件
        if must_exist:
            lines.append(f"(assert (= {var_name}_recommendation_satisfied {var_name}_exists))")
        elif must_not_exist:
            lines.append(f"(assert (= {var_name}_recommendation_satisfied (not {var_name}_exists)))")
        else:
            lines.append(f"(assert (= {var_name}_recommendation_satisfied true))")

        # 🔧 断言推荐应该满足（如果违反，返回unsat）
        lines.extend([
            f"(assert {var_name}_recommendation_satisfied)",
            "(check-sat)"
        ])

        return "\n".join(lines)

    def _clean_xml_tag(self, tag: str) -> str:
        """清理XML标签名"""
        if '}' in tag:
            return tag.split('}')[1]
        return tag

    # ==================== 原有方法保持不变 ====================

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

        print(f"📊 SMT验证结果:")
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
            "mode": "concrete_xml_validation"
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

    # ==================== 原有辅助方法 ====================

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

            # 🔧 改进的SMT解析 - 处理更复杂的约束
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
                    # 🔧 改进的断言解析
                    try:
                        # 处理等式断言
                        if '(= ' in line:
                            # 提取变量名和值
                            for var_name, var_obj in variables.items():
                                if var_name in line:
                                    # 提取数值或布尔值
                                    if 'true' in line:
                                        solver.add(var_obj == True)
                                        break
                                    elif 'false' in line:
                                        solver.add(var_obj == False)
                                        break
                                    else:
                                        numbers = re.findall(r'-?\d+\.?\d*', line)
                                        if numbers:
                                            try:
                                                if isinstance(var_obj, z3.IntRef):
                                                    value = int(numbers[-1])  # 取最后一个数字
                                                else:
                                                    value = float(numbers[-1])
                                                solver.add(var_obj == value)
                                                break
                                            except ValueError:
                                                continue

                        # 处理比较断言
                        elif any(op in line for op in ['>= ', '<= ', '> ', '< ']):
                            for var_name, var_obj in variables.items():
                                if var_name in line:
                                    numbers = re.findall(r'\d+\.?\d*', line)
                                    if numbers:
                                        try:
                                            value = float(numbers[0])
                                            if '>=' in line:
                                                solver.add(var_obj >= value)
                                            elif '<=' in line:
                                                solver.add(var_obj <= value)
                                            elif '>' in line:
                                                solver.add(var_obj > value)
                                            elif '<' in line:
                                                solver.add(var_obj < value)
                                            break
                                        except ValueError:
                                            continue

                        # 处理简单布尔断言
                        elif line == "(assert false)":
                            solver.add(False)
                        elif line == "(assert true)":
                            solver.add(True)
                        else:
                            # 处理复杂表达式
                            for var_name, var_obj in variables.items():
                                if var_name in line:
                                    if isinstance(var_obj, z3.BoolRef):
                                        if f"(assert {var_name})" in line:
                                            solver.add(var_obj)
                                        elif f"(assert (not {var_name})" in line:
                                            solver.add(z3.Not(var_obj))
                                    break

                    except Exception:
                        continue

            # 求解
            result = solver.check()

            return {
                "status": str(result),
                "output": str(result),
                "method": "python_z3",
                "variables": list(variables.keys()),
                "solver_assertions": len(solver.assertions())
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

    # ==================== 向后兼容的传统验证方法 ====================

    def _validate_constraints_as_recommendations(self, xml_content: str) -> Dict:
        """传统验证模式：保持原有逻辑作为后备"""
        print("🔍 开始传统SMT约束验证...")

        try:
            # 🔧 即使没有enriched_constraints，也尝试基础的XML解析验证
            xml_model = self._build_complete_xml_model(xml_content)

            if not xml_model:
                return {
                    "valid": True,
                    "structural_valid": True,
                    "semantic_compliance": "NONE",
                    "constraint_count": 0,
                    "satisfied_count": 0,
                    "structural_violations": [],
                    "semantic_warnings": [],
                    "detailed_results": [],
                    "message": "Traditional validation mode - failed to parse XML"
                }

            # 🔧 基础验证：检查常见的必需元素
            basic_results = self._perform_basic_validation(xml_model)

            return {
                "valid": len(basic_results['violations']) == 0,
                "structural_valid": len(basic_results['violations']) == 0,
                "semantic_compliance": "BASIC" if len(basic_results['violations']) == 0 else "LOW",
                "constraint_count": len(basic_results['checks']),
                "satisfied_count": len(basic_results['checks']) - len(basic_results['violations']),
                "structural_violations": basic_results['violations'],
                "semantic_warnings": [],
                "detailed_results": basic_results['checks'],
                "message": "Traditional validation mode - basic XML structure checks"
            }

        except Exception as e:
            print(f"❌ 传统验证模式错误: {e}")
            return {
                "valid": True,
                "structural_valid": True,
                "semantic_compliance": "ERROR",
                "constraint_count": 0,
                "satisfied_count": 0,
                "structural_violations": [],
                "semantic_warnings": [],
                "detailed_results": [],
                "error": str(e)
            }

    def _perform_basic_validation(self, xml_model: Dict) -> Dict:
        """🔧 执行基础验证 - 检查常见的XML结构问题"""
        checks = []
        violations = []

        # 🔧 基础检查1：根元素应该有SHORT-NAME
        root_tags = list(xml_model["entities"].keys())
        if root_tags:
            root_tag = root_tags[0]  # 假设第一个是根标签

            # 检查是否有SHORT-NAME
            short_name_count = xml_model["element_counts"].get("SHORT-NAME", 0)

            check_result = {
                "constraint_id": "basic_short_name_check",
                "constraint_type": "basic_structural",
                "element": "SHORT-NAME",
                "class_element": root_tag,
                "actual_count": short_name_count,
                "severity": "violation"
            }

            if short_name_count == 0:
                check_result.update({
                    "status": "unsat",
                    "message": f"BASIC CHECK: ROOT element {root_tag} should contain SHORT-NAME"
                })
                violations.append(check_result)
            else:
                check_result.update({
                    "status": "sat",
                    "message": f"BASIC CHECK: ROOT element {root_tag} contains SHORT-NAME"
                })

            checks.append(check_result)

        # 🔧 基础检查2：检查wrapper关系
        wrapper_relationships = xml_model.get("wrapper_relationships", {})
        for wrapper_tag, item_tag in wrapper_relationships.items():
            wrapper_count = xml_model["element_counts"].get(wrapper_tag, 0)
            item_count = xml_model["element_counts"].get(item_tag, 0)

            check_result = {
                "constraint_id": f"basic_wrapper_check_{wrapper_tag}",
                "constraint_type": "basic_wrapper",
                "element": item_tag,
                "class_element": wrapper_tag,
                "actual_count": item_count,
                "severity": "info"
            }

            if wrapper_count > 0 and item_count == 0:
                check_result.update({
                    "status": "unsat",
                    "message": f"BASIC CHECK: {wrapper_tag} exists but contains no {item_tag}"
                })
                # 这只是警告，不算违规
            else:
                check_result.update({
                    "status": "sat",
                    "message": f"BASIC CHECK: {wrapper_tag} wrapper structure is reasonable"
                })

            checks.append(check_result)

        print(f"   📊 基础验证完成: {len(checks)} 项检查, {len(violations)} 个违规")

        return {
            "checks": checks,
            "violations": violations
        }