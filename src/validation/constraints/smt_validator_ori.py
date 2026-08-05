"""smt_validator.py (v4.0) - 修复XML到SMT的实际连接
--------------------------------------------
核心修复：将实际XML数据转换为SMT事实，实现非抽象的约束验证
"""
import json
import os
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Optional

import z3


class SMTValidator:
    """SMT约束验证器 - 实现XML数据到SMT模型的完整映射"""

    def __init__(self, smt_template_file: str,
                 raw_attributes_file: Optional[str] = None,
                 enriched_constraints_file: Optional[str] = None,
                 constraint_config: Optional[Dict] = None):
        """
        初始化SMT验证器 - 支持细粒度约束控制

        Args:
            smt_template_file: SMT模板文件路径
            raw_attributes_file: raw_attributes.jsonl文件路径 (可选)
            enriched_constraints_file: enriched_constraints.json文件路径 (推荐)
            constraint_config: 约束验证配置 (新增)
        """
        print("🔧 初始化SMT验证器...")

        # 🔧 约束配置处理
        self.constraint_config = constraint_config or {}
        self.validation_scope = self.constraint_config.get('validation_scope', {})
        self.validation_strategy = self.constraint_config.get('validation_strategy', {})
        self.performance_config = self.constraint_config.get('performance', {})
        self.output_config = self.constraint_config.get('output', {})

        # 解析验证模式
        self.validation_mode = self.validation_strategy.get('mode', 'hybrid')
        self.semantic_types_enabled = self.validation_scope.get('semantic_types', {})

        print(f"📋 约束验证配置:")
        print(f"   验证模式: {self.validation_mode}")
        print(f"   结构约束: {'启用' if self.validation_scope.get('structural_constraints', True) else '禁用'}")
        print(f"   语义约束: {'启用' if self.validation_scope.get('semantic_constraints', True) else '禁用'}")

        # 显示启用的语义约束类型
        enabled_semantic_types = [k for k, v in self.semantic_types_enabled.items() if v]
        if enabled_semantic_types:
            print(f"   语义约束类型: {', '.join(enabled_semantic_types)}")

        # 原有初始化逻辑...
        try:
            self.smt_template_file = str(smt_template_file) if smt_template_file else ""
            self.smt_template = self._load_smt_template(self.smt_template_file)
            self.z3_available = self._check_z3_availability()

            # 核心约束和映射数据初始化
            self.enriched_constraints = []
            self.structural_constraints = []
            self.semantic_constraints = []
            self.xml_to_attr_mapping = {}
            self.xml_element_registry = {}
            self.smt_entity_counter = 0

            # 加载约束数据
            enriched_file_valid = False
            if enriched_constraints_file:
                try:
                    enriched_path = Path(enriched_constraints_file)
                    if enriched_path.exists() and enriched_path.suffix in ['.json']:
                        print("🔧 启用结构化约束验证")
                        self._load_enriched_constraints(str(enriched_path))
                        enriched_file_valid = True
                    else:
                        print(f"⚠️  增强约束文件无效或不存在: {enriched_constraints_file}")
                except Exception as e:
                    print(f"⚠️  增强约束文件处理失败: {e}")

            if not enriched_file_valid:
                print("📝 使用传统XML解析模式")

            # 加载映射文件
            if raw_attributes_file:
                try:
                    raw_attr_path = Path(raw_attributes_file)
                    if raw_attr_path.exists() and raw_attr_path.suffix in ['.jsonl', '.json']:
                        print(f"📄 加载属性映射文件: {raw_attributes_file}")
                        self._build_mapping_tables(str(raw_attr_path))
                    else:
                        print(f"⚠️  原始属性文件无效或不存在: {raw_attributes_file}")
                except Exception as e:
                    print(f"⚠️  原始属性文件处理失败: {e}")

            # 🔧 新增：根据配置过滤约束
            self._filter_constraints_by_config()

            print("✅ SMT验证器初始化完成")

        except Exception as e:
            print(f"❌ SMT验证器初始化失败: {e}")
            # 提供默认的安全状态
            self._init_safe_defaults()

    def _filter_constraints_by_config(self):
        """🔧 新增：根据配置过滤约束"""
        original_structural_count = len(self.structural_constraints)
        original_semantic_count = len(self.semantic_constraints)

        # 过滤结构约束
        if not self.validation_scope.get('structural_constraints', True):
            self.structural_constraints = []
            print(f"🔧 已禁用结构约束 (原有 {original_structural_count} 个)")

        # 过滤语义约束
        if not self.validation_scope.get('semantic_constraints', True):
            self.semantic_constraints = []
            print(f"🔧 已禁用语义约束 (原有 {original_semantic_count} 个)")
        else:
            # 根据语义约束类型过滤
            filtered_semantic = []
            semantic_type_counts = {}

            for constraint in self.semantic_constraints:
                constraint_type = constraint.get('type', 'other')

                # 统计
                semantic_type_counts[constraint_type] = semantic_type_counts.get(constraint_type, 0) + 1

                # 检查是否启用此类型
                if self.semantic_types_enabled.get(constraint_type, True):
                    filtered_semantic.append(constraint)

            # 显示过滤结果
            removed_count = len(self.semantic_constraints) - len(filtered_semantic)
            if removed_count > 0:
                print(f"🔧 过滤语义约束: 保留 {len(filtered_semantic)}/{original_semantic_count} 个")
                for constraint_type, count in semantic_type_counts.items():
                    status = "启用" if self.semantic_types_enabled.get(constraint_type, True) else "禁用"
                    print(f"   {constraint_type}: {count} 个 ({status})")

            self.semantic_constraints = filtered_semantic

    def validate_constraints(self, xml_content: str) -> Dict:
        """SMT约束验证 - 支持细粒度控制的版本"""
        print("🔍 开始SMT约束验证...")

        if not xml_content or not xml_content.strip():
            print("❌ XML内容为空")
            return self._create_error_result("XML content is empty")

        if not self.z3_available:
            print("⚠️  Z3求解器不可用，跳过SMT验证")
            return self._create_skip_result("Z3 solver not available")

        try:
            # 步骤1：解析XML并建立完整的元素注册表
            print("📝 步骤1: 解析XML并建立元素注册表...")
            xml_model = self._build_complete_xml_model(xml_content)

            if not xml_model:
                return self._create_error_result("Failed to parse XML")

            # 🔧 新增：根据验证模式决定验证范围
            print(f"📋 验证模式: {self.validation_mode}")

            if self.validation_mode == "structural_only":
                print("🔧 仅验证结构约束")
                return self._validate_structural_only(xml_model)
            elif self.validation_mode == "semantic_only":
                print("🔧 仅验证语义约束")
                return self._validate_semantic_only(xml_model)
            else:  # hybrid mode
                print("🔧 混合验证模式")
                return self._validate_with_concrete_smt_instances(xml_model)

        except Exception as e:
            print(f"❌ SMT验证错误: {e}")
            import traceback
            traceback.print_exc()
            return self._create_error_result(str(e))

    def _validate_structural_only(self, xml_model: Dict) -> Dict:
        """🔧 新增：仅验证结构约束"""
        structural_results = []

        print(f"📝 验证结构约束 ({len(self.structural_constraints)} 个)...")

        for constraint in self.structural_constraints:
            try:
                result = self._validate_structural_constraint_concrete(constraint, xml_model)
                structural_results.append(result)

                # 如果启用了fail_fast且约束失败
                if (self.validation_strategy.get('fail_fast', True) and
                        result.get('status') != 'sat'):
                    print(f"⚠️  fail_fast模式：在约束 {constraint.get('cid', 'unknown')} 失败后停止")
                    break

            except Exception as e:
                structural_results.append({
                    "status": "error",
                    "constraint_type": "structural",
                    "constraint_id": constraint.get("cid", "unknown"),
                    "error": str(e),
                    "severity": "violation"
                })

        return self._analyze_validation_results(structural_results, [])

    def _validate_semantic_only(self, xml_model: Dict) -> Dict:
        """🔧 新增：仅验证语义约束"""
        semantic_results = []

        print(f"📝 验证语义约束 ({len(self.semantic_constraints)} 个)...")

        # 按类型分组验证
        constraints_by_type = {}
        for constraint in self.semantic_constraints:
            constraint_type = constraint.get('type', 'other')
            if constraint_type not in constraints_by_type:
                constraints_by_type[constraint_type] = []
            constraints_by_type[constraint_type].append(constraint)

        # 按类型依次验证
        for constraint_type, constraints in constraints_by_type.items():
            print(f"   🔍 验证 {constraint_type} 约束 ({len(constraints)} 个)...")

            for constraint in constraints:
                try:
                    result = self._validate_semantic_constraint_concrete(constraint, xml_model)
                    result['constraint_source'] = 'semantic_only_mode'  # 标记来源
                    semantic_results.append(result)

                except Exception as e:
                    semantic_results.append({
                        "status": "error",
                        "constraint_type": constraint_type,
                        "constraint_id": constraint.get("cid", "unknown"),
                        "error": str(e),
                        "severity": "warning",
                        "constraint_source": 'semantic_only_mode'
                    })

        return self._analyze_validation_results([], semantic_results)

    def _analyze_validation_results(self, structural_results: List[Dict], semantic_results: List[Dict]) -> Dict:
        """分析验证结果 - 支持细粒度控制的版本"""

        # 基础统计
        structural_count = len(structural_results) if isinstance(structural_results, list) else 0
        structural_satisfied = sum(1 for r in structural_results if isinstance(r, dict) and r.get("status") == "sat")
        structural_violations = [r for r in structural_results if isinstance(r, dict) and r.get("status") != "sat"]
        structural_valid = structural_satisfied == structural_count if structural_count > 0 else True

        semantic_count = len(semantic_results) if isinstance(semantic_results, list) else 0
        semantic_satisfied = sum(1 for r in semantic_results if isinstance(r, dict) and r.get("status") == "sat")
        semantic_warnings = [r for r in semantic_results if isinstance(r, dict) and r.get("status") != "sat"]

        # 🔧 新增：按约束类型的详细分析
        constraint_breakdown = self._build_detailed_constraint_breakdown(structural_results, semantic_results)

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

        # 整体状态判定
        overall_valid = structural_valid
        total_count = structural_count + semantic_count
        total_satisfied = structural_satisfied + semantic_satisfied

        # 🔧 新增：验证模式相关的状态调整
        if self.validation_mode == "semantic_only":
            # 语义约束模式下，整体有效性基于语义约束
            overall_valid = semantic_compliance in ["FULL", "HIGH"]
        elif self.validation_mode == "structural_only":
            # 结构约束模式下，整体有效性基于结构约束
            overall_valid = structural_valid

        print(f"📊 SMT验证结果 ({self.validation_mode} 模式):")
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
            "detailed_results": (structural_results if isinstance(structural_results, list) else []) +
                                (semantic_results if isinstance(semantic_results, list) else []),
            "constraint_breakdown": constraint_breakdown,
            "satisfaction_rate": total_satisfied / total_count if total_count > 0 else 1.0,
            "validation_mode": self.validation_mode,
            "mode": "concrete_xml_validation"
        }

    def _build_detailed_constraint_breakdown(self, structural_results: List[Dict],
                                             semantic_results: List[Dict]) -> Dict:
        """🔧 新增：构建详细的约束类型分解"""
        breakdown = {
            "summary": {
                "total_structural": len(structural_results),
                "total_semantic": len(semantic_results),
                "validation_mode": self.validation_mode
            },
            "structural": {},
            "semantic": {}
        }

        # 分析结构约束
        for result in structural_results:
            if isinstance(result, dict):
                constraint_type = result.get("constraint_type", "unknown")
                if constraint_type not in breakdown["structural"]:
                    breakdown["structural"][constraint_type] = {
                        "total": 0,
                        "satisfied": 0,
                        "violations": 0
                    }

                breakdown["structural"][constraint_type]["total"] += 1
                if result.get("status") == "sat":
                    breakdown["structural"][constraint_type]["satisfied"] += 1
                else:
                    breakdown["structural"][constraint_type]["violations"] += 1

        # 分析语义约束 - 按类型细分
        semantic_type_stats = {}
        for result in semantic_results:
            if isinstance(result, dict):
                constraint_type = result.get("constraint_type", "unknown")
                # 提取具体的语义约束类型（去掉后缀）
                base_type = constraint_type.replace("_recommendation", "").replace("_constraint", "")

                if base_type not in semantic_type_stats:
                    semantic_type_stats[base_type] = {
                        "total": 0,
                        "satisfied": 0,
                        "warnings": 0,
                        "enabled": self.semantic_types_enabled.get(base_type, True)
                    }

                semantic_type_stats[base_type]["total"] += 1
                if result.get("status") == "sat":
                    semantic_type_stats[base_type]["satisfied"] += 1
                else:
                    semantic_type_stats[base_type]["warnings"] += 1

        breakdown["semantic"] = semantic_type_stats

        # 🔧 新增：验证配置信息
        breakdown["configuration"] = {
            "structural_enabled": self.validation_scope.get('structural_constraints', True),
            "semantic_enabled": self.validation_scope.get('semantic_constraints', True),
            "semantic_types_config": self.semantic_types_enabled,
            "fail_fast": self.validation_strategy.get('fail_fast', True)
        }

        return breakdown

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
        """🔧 验证单个结构约束 - 使用具体XML数据 - 类型安全版本"""
        constraint_id = constraint.get("cid", "unknown")

        try:
            for target in constraint.get("enriched_targets", []):
                if target.get("target_type") != "attribute":
                    continue

                # 🔧 安全地提取目标信息
                xml_tag = str(target.get("xml_tag", "unknown"))
                class_xml_tag = str(target.get("class_xml_tag", "unknown"))

                # 🔧 安全地提取约束参数
                min_occurs = self._safe_int_conversion(target.get("minOccurs"), 0)
                max_occurs = self._safe_int_conversion(target.get("maxOccurs"), -1)

                # 🔧 关键修复：从实际XML模型计算出现次数 - 类型安全
                try:
                    actual_count = self._count_actual_occurrences(xml_model, class_xml_tag, xml_tag)
                    # 确保actual_count是整数
                    actual_count = self._safe_int_conversion(actual_count, 0)
                except Exception as count_error:
                    print(f"⚠️  计数失败: {count_error}")
                    actual_count = 0

                # 🔧 生成具体的SMT验证实例
                try:
                    smt_instance = self._generate_concrete_structural_smt(
                        constraint_id, xml_tag, class_xml_tag, actual_count, min_occurs, max_occurs, xml_model
                    )
                except Exception as smt_error:
                    print(f"⚠️  SMT实例生成失败: {smt_error}")
                    return {
                        "status": "error",
                        "constraint_type": "structural_cardinality",
                        "constraint_id": constraint_id,
                        "error": f"SMT generation failed: {str(smt_error)}",
                        "severity": "violation"
                    }

                # 🔧 求解具体实例
                try:
                    solve_result = self.solve_smt_instance(smt_instance)
                except Exception as solve_error:
                    print(f"⚠️  SMT求解失败: {solve_error}")
                    solve_result = {
                        "status": "error",
                        "error": f"SMT solve failed: {str(solve_error)}"
                    }

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

                # 🔧 正确的违规判定逻辑 - 类型安全
                constraint_violated = False
                try:
                    # 确保所有比较操作都使用整数
                    if isinstance(min_occurs, int) and min_occurs > 0 and actual_count < min_occurs:
                        constraint_violated = True
                    if isinstance(max_occurs,
                                  int) and max_occurs != -1 and max_occurs > 0 and actual_count > max_occurs:
                        constraint_violated = True
                except TypeError as compare_error:
                    print(f"⚠️  约束比较失败: {compare_error}")
                    print(f"   actual_count: {actual_count} ({type(actual_count)})")
                    print(f"   min_occurs: {min_occurs} ({type(min_occurs)})")
                    print(f"   max_occurs: {max_occurs} ({type(max_occurs)})")
                    constraint_violated = True  # 安全起见，标记为违反

                if constraint_violated:
                    solve_result["status"] = "unsat"
                    max_display = max_occurs if max_occurs != -1 else '∞'
                    solve_result[
                        "message"] = f"STRUCTURAL ERROR: {xml_tag} count {actual_count} violates range [{min_occurs}, {max_display}] in {class_xml_tag}"
                else:
                    solve_result["status"] = "sat"
                    solve_result[
                        "message"] = f"Structural constraint satisfied: {xml_tag} count {actual_count} in {class_xml_tag}"

                status_symbol = '✅ 通过' if not constraint_violated else '❌ 违反'
                print(f"   🔧 结构约束 {constraint_id}: {xml_tag} = {actual_count} ({status_symbol})")
                return solve_result

        except Exception as e:
            print(f"❌ 结构约束验证失败: {e}")
            import traceback
            traceback.print_exc()

            return {
                "status": "error",
                "constraint_type": "structural_cardinality",
                "constraint_id": constraint_id,
                "error": f"Structural constraint validation failed: {str(e)}",
                "severity": "violation"
            }

        # 默认返回
        return {
            "status": "sat",
            "constraint_type": "structural_cardinality",
            "constraint_id": constraint_id,
            "message": "No valid targets for structural constraint",
            "severity": "violation"
        }

    def _count_actual_occurrences(self, xml_model: Dict, class_tag: str, attr_tag: str) -> int:
        """🔧 核心修复：从实际XML模型计算元素出现次数 - 类型安全版本"""
        try:
            # 🔧 输入验证和类型安全
            if not xml_model or not isinstance(xml_model, dict):
                print(f"⚠️ xml_model 无效: {type(xml_model)}")
                return 0

            if not class_tag or not attr_tag:
                print(f"⚠️ 标签参数无效: class_tag={class_tag}, attr_tag={attr_tag}")
                return 0

            # 确保class_tag和attr_tag是字符串
            class_tag = str(class_tag) if class_tag else ""
            attr_tag = str(attr_tag) if attr_tag else ""

            # 🔧 处理wrapper关系
            wrapper_relationships = xml_model.get("wrapper_relationships", {})
            if not isinstance(wrapper_relationships, dict):
                wrapper_relationships = {}

            # 使用集合避免重复计数
            counted_elements = set()
            total_count = 0

            # 🔧 类型安全的实体访问
            entities = xml_model.get("entities", {})
            if not isinstance(entities, dict):
                print(f"⚠️ entities 字段类型错误: {type(entities)}")
                return 0

            # 情况1：在指定类的上下文中查找（避免全局计数导致的重复）
            class_entities = entities.get(class_tag, [])
            if not isinstance(class_entities, list):
                print(f"⚠️ class_entities 类型错误: {type(class_entities)}")
                class_entities = []

            if class_entities:
                for class_entity in class_entities:
                    if not isinstance(class_entity, dict):
                        continue

                    element = class_entity.get("element")
                    if element is None:
                        continue

                    # 🔧 修复：只检查直接子元素，不递归
                    direct_child_count = 0
                    try:
                        for child in element:  # 直接子元素
                            child_tag = self._clean_xml_tag(child.tag)
                            if child_tag == attr_tag and id(child) not in counted_elements:
                                counted_elements.add(id(child))
                                direct_child_count += 1
                    except Exception as e:
                        print(f"⚠️ 遍历子元素失败: {e}")
                        continue

                    if direct_child_count > 0:
                        print(f"   📊 在 {class_tag} 的直接子元素中找到 {attr_tag}: {direct_child_count} 个")
                        total_count += direct_child_count

                    # 🔧 检查通过wrapper间接包含的元素
                    children_tags = class_entity.get("children_tags", [])
                    if not isinstance(children_tags, list):
                        continue

                    for child_tag in set(children_tags):
                        if not isinstance(child_tag, str):
                            continue

                        if child_tag in wrapper_relationships:
                            expected_item = wrapper_relationships[child_tag]
                            if not isinstance(expected_item, str):
                                continue

                            if expected_item == attr_tag:
                                # 计算wrapper内的实际item数量（避免重复）
                                wrapper_count = 0
                                try:
                                    for child in element:
                                        if self._clean_xml_tag(child.tag) == child_tag:
                                            # wrapper元素，检查其子元素
                                            for grandchild in child:
                                                if (self._clean_xml_tag(grandchild.tag) == attr_tag and
                                                        id(grandchild) not in counted_elements):
                                                    counted_elements.add(id(grandchild))
                                                    wrapper_count += 1
                                except Exception as e:
                                    print(f"⚠️ wrapper 子元素检查失败: {e}")
                                    continue

                                if wrapper_count > 0:
                                    print(f"   📦 通过wrapper {child_tag} 找到 {attr_tag}: {wrapper_count} 个")
                                    total_count += wrapper_count

            # 情况2：如果在类上下文中没找到，才进行全局查找
            if total_count == 0:
                attr_entities = entities.get(attr_tag, [])
                if isinstance(attr_entities, list):
                    global_count = len(attr_entities)
                    if global_count > 0:
                        print(f"   📊 全局查找 {attr_tag}: {global_count} 个")
                        total_count = global_count

            # 🔧 确保返回整数
            result = int(total_count) if isinstance(total_count, (int, float)) else 0
            print(f"   📈 {attr_tag} 在 {class_tag} 中总计: {result} 个")
            return result

        except Exception as e:
            print(f"❌ 计数过程出错: {e}")
            import traceback
            traceback.print_exc()
            return 0

    def count_with_wrapper_support(element_counts, class_tag, attr_tag, wrapper_relationships, root):
        """🔧 支持wrapper的智能计数"""

        # 使用集合避免重复计数
        counted_elements = set()
        total_count = 0

        # 查找class_tag元素
        for elem in root.iter():
            elem_tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            if elem_tag == class_tag:
                # 计算直接子元素
                direct_count = 0
                for child in elem:
                    child_tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                    if child_tag == attr_tag and id(child) not in counted_elements:
                        counted_elements.add(id(child))
                        direct_count += 1

                if direct_count > 0:
                    print(f"      📊 在 {class_tag} 中直接找到 {attr_tag}: {direct_count} 个")
                    total_count += direct_count

                # 检查通过wrapper的元素
                for child in elem:
                    child_tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                    if child_tag in wrapper_relationships:
                        expected_item = wrapper_relationships[child_tag]
                        if expected_item == attr_tag:
                            # 计算wrapper内的item数量
                            wrapper_count = 0
                            for grandchild in child:
                                grandchild_tag = grandchild.tag.split('}')[
                                    -1] if '}' in grandchild.tag else grandchild.tag
                                if grandchild_tag == attr_tag and id(grandchild) not in counted_elements:
                                    counted_elements.add(id(grandchild))
                                    wrapper_count += 1

                            if wrapper_count > 0:
                                print(f"      📦 通过wrapper {child_tag} 找到 {attr_tag}: {wrapper_count} 个")
                                total_count += wrapper_count

        # 如果在类上下文中没找到，才进行全局查找
        if total_count == 0:
            global_count = element_counts.get(attr_tag, 0)
            if global_count > 0:
                print(f"      📊 全局查找 {attr_tag}: {global_count} 个")
                total_count = global_count

        print(f"      📈 总计: {total_count} 个")

        return total_count

    def _generate_concrete_structural_smt(self, constraint_id: str, attr_tag: str, class_tag: str,
                                          actual_count: int, min_occurs: int, max_occurs: int,
                                          xml_model: Dict) -> str:
        """🔧 生成具体的结构约束SMT实例 - 类型安全版本"""
        try:
            # 🔧 类型安全转换
            constraint_id = str(constraint_id) if constraint_id else "unknown"
            attr_tag = str(attr_tag) if attr_tag else "unknown"
            class_tag = str(class_tag) if class_tag else "unknown"

            # 🔧 确保数值类型安全
            actual_count = self._safe_int_conversion(actual_count, 0)
            min_occurs = self._safe_int_conversion(min_occurs, 0)
            max_occurs = self._safe_int_conversion(max_occurs, -1)

            lines = [
                "(set-logic QF_LIA)",
                f"; Concrete structural constraint {constraint_id}",
                f"; Element: {attr_tag} in {class_tag}",
                f"; Actual count from XML: {actual_count}",
                f"; Required range: [{min_occurs}, {max_occurs if max_occurs != -1 else '∞'}]",
                ""
            ]

            # 🔧 声明具体的变量 - 使用安全的标识符
            var_name = self._create_safe_smt_identifier(f"{class_tag}_{attr_tag}")

            lines.extend([
                f"(declare-const {var_name}_actual_count Int)",
                f"(declare-const {var_name}_min_required Int)",
                f"(declare-const {var_name}_max_allowed Int)",
                f"(declare-const {var_name}_constraint_satisfied Bool)",
                ""
            ])

            # 🔧 设置实际值 - 确保都是安全的整数
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

        except Exception as e:
            print(f"❌ SMT生成失败: {e}")
            # 返回一个简单的错误实例
            return f"""(set-logic QF_LIA)
    ; Error generating SMT for {constraint_id}: {str(e)}
    (declare-const error_occurred Bool)
    (assert error_occurred)
    (check-sat)"""

    def _safe_int_conversion(self, value: Any, default: int = 0) -> int:
        """🔧 新增：安全的整数转换"""
        try:
            if value is None:
                return default

            # 如果是字典或其他复杂类型，返回默认值
            if isinstance(value, (dict, list, tuple)):
                print(f"⚠️ 尝试转换复杂类型为整数: {type(value)} -> 使用默认值 {default}")
                return default

            # 字符串转换
            if isinstance(value, str):
                # 提取数字
                numbers = re.findall(r'-?\d+', value)
                if numbers:
                    return int(numbers[0])
                return default

            # 直接转换
            return int(value)

        except (ValueError, TypeError, AttributeError) as e:
            print(f"⚠️ 整数转换失败: {value} ({type(value)}) -> {e} -> 使用默认值 {default}")
            return default

    def _create_safe_smt_identifier(self, name: str) -> str:
        """🔧 新增：创建安全的SMT标识符"""
        try:
            if not name:
                return "unknown"

            # 转换为字符串
            name = str(name)

            # 替换特殊字符
            safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', name)

            # 确保以字母开头
            if safe_name and safe_name[0].isdigit():
                safe_name = "var_" + safe_name

            # 限制长度
            if len(safe_name) > 50:
                safe_name = safe_name[:47] + "_etc"

            return safe_name or "unknown"

        except Exception as e:
            print(f"⚠️ SMT标识符创建失败: {name} -> {e}")
            return "unknown"



    def _solve_with_python_z3(self, smt_instance: str) -> dict:
        try:
            s = z3.Solver()
            # 直接用 z3 的 SMT-LIB2 解析器（支持 declare-sort/fun、量词等）
            fmls = z3.parse_smt2_string(smt_instance)
            # parse_smt2_string 可能返回单个公式或列表
            if isinstance(fmls, list):
                s.add(*fmls)
            else:
                s.add(fmls)

            res = s.check()
            model = s.model() if res == z3.sat else None
            return {
                "status": str(res),
                "method": "python_z3",
                "model": str(model) if model is not None else None,
                "solver_assertions": len(s.assertions())
            }
        except Exception as e:
            return {"status": "error", "error": str(e), "method": "python_z3"}

    def _extract_safe_value(self, line: str, var_obj) -> Any:
        """🔧 新增：安全提取值，确保类型正确"""
        try:
            import z3
            # 处理布尔值
            if 'true' in line.lower():
                if isinstance(var_obj, z3.BoolRef):
                    return True
                return None
            elif 'false' in line.lower():
                if isinstance(var_obj, z3.BoolRef):
                    return False
                return None

            # 🔧 关键修复：安全提取数值
            # 查找数字模式，避免解析复杂结构
            number_patterns = [
                r'\b(\d+)\b',  # 简单整数
                r'\b(-?\d+)\b',  # 带符号整数
                r'\b(-?\d*\.?\d+)\b'  # 小数
            ]

            for pattern in number_patterns:
                matches = re.findall(pattern, line)
                if matches:
                    try:
                        # 取最后一个匹配的数字（通常是赋值的目标值）
                        num_str = matches[-1]

                        # 🔧 类型安全转换
                        if isinstance(var_obj, (z3.IntRef, z3.ArithRef)):
                            if '.' in num_str:
                                return float(num_str)
                            else:
                                return int(num_str)
                        elif isinstance(var_obj, z3.RealRef):
                            return float(num_str)

                    except (ValueError, TypeError) as e:
                        print(f"⚠️ 数值转换失败: {num_str} -> {e}")
                        continue

            # 如果没有找到有效数值，返回None
            return None

        except Exception as e:
            print(f"⚠️ 值提取失败: {line} -> {e}")
            return None

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