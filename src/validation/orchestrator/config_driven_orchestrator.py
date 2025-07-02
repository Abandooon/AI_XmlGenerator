# src/validation/orchestrator/config_driven_orchestrator.py
"""
配置驱动的验证编排器 - 增强版（支持映射文件传递）
"""
from typing import Dict, Optional
import time
from pathlib import Path


class ConfigDrivenOrchestrator:
    """配置驱动的验证编排器 - 支持增强功能"""

    def __init__(self, config: Dict):
        """初始化验证编排器"""
        self.config = config
        self.validators = {}
        self._init_validators()

    def _init_validators(self):
        """根据配置初始化验证器"""
        print("\n🔧 初始化验证器...")
        validator_config = self.config.get("validators", {})
        file_paths = self.config.get("file_paths", {})

        # 修正：获取项目根目录
        project_root = Path(self.config.get("project_root", "."))

        # 获取映射文件路径 (可选)
        raw_attributes_file = file_paths.get("raw_attributes")
        enriched_constraints_file = file_paths.get("enriched_constraints")

        # 修正：解析映射文件的完整路径
        if raw_attributes_file:
            raw_attributes_path = project_root / raw_attributes_file if not Path(
                raw_attributes_file).is_absolute() else Path(raw_attributes_file)
            raw_attributes_file = str(raw_attributes_path) if raw_attributes_path.exists() else None

        if enriched_constraints_file:
            enriched_constraints_path = project_root / enriched_constraints_file if not Path(
                enriched_constraints_file).is_absolute() else Path(enriched_constraints_file)
            enriched_constraints_file = str(enriched_constraints_path) if enriched_constraints_path.exists() else None

        # 初始化结构验证器
        if validator_config.get("structure", {}).get("enabled", True):
            try:
                from ..structure.xsd_validator import XSDValidator
                xsd_path = file_paths.get("xsd_schema")
                if xsd_path:
                    # 修正：解析XSD文件的完整路径
                    xsd_full_path = project_root / xsd_path if not Path(xsd_path).is_absolute() else Path(xsd_path)
                    if xsd_full_path.exists():
                        print(f"📄 加载XSD Schema: {xsd_full_path}")
                        self.validators['structure'] = XSDValidator(str(xsd_full_path))
                        print("✅ XSD结构验证器初始化成功")
                    else:
                        print(f"⚠️  XSD文件未找到: {xsd_full_path}")
                else:
                    print("⚠️  配置中未指定XSD Schema路径")
            except Exception as e:
                print(f"⚠️  XSD验证器初始化失败: {e}")

        # 初始化语义验证器 (支持映射文件)
        if validator_config.get("semantic", {}).get("enabled", True):
            try:
                from ..semantic.shacl_validator import SHACLValidator
                shacl_path = file_paths.get("shacl_shapes")
                if shacl_path:
                    # 修正：解析SHACL文件的完整路径
                    shacl_full_path = project_root / shacl_path if not Path(shacl_path).is_absolute() else Path(
                        shacl_path)
                    if shacl_full_path.exists():
                        print(f"📄 加载SHACL Shapes: {shacl_full_path}")

                        # 检查是否有映射文件
                        if raw_attributes_file and Path(raw_attributes_file).exists():
                            print(f"📄 启用映射功能: {raw_attributes_file}")
                            self.validators['semantic'] = SHACLValidator(
                                str(shacl_full_path),
                                raw_attributes_file,
                                enriched_constraints_file
                            )
                            print("✅ SHACL语义验证器初始化成功 (增强模式)")
                        else:
                            print("📝 使用标准模式")
                            self.validators['semantic'] = SHACLValidator(str(shacl_full_path))
                            print("✅ SHACL语义验证器初始化成功 (标准模式)")
                    else:
                        print(f"⚠️  SHACL文件未找到: {shacl_full_path}")
                else:
                    print("⚠️  配置中未指定SHACL Shapes路径")
            except Exception as e:
                print(f"⚠️  SHACL验证器初始化失败: {e}")

        # 初始化约束验证器 (支持映射文件)
        if validator_config.get("constraint", {}).get("enabled", True):
            try:
                from ..constraints.smt_validator import SMTValidator
                smt_path = file_paths.get("smt_template")
                if smt_path:
                    # 修正：解析SMT文件的完整路径
                    smt_full_path = project_root / smt_path if not Path(smt_path).is_absolute() else Path(smt_path)
                    if smt_full_path.exists():
                        print(f"📄 加载SMT Template: {smt_full_path}")

                        # 检查是否有映射文件
                        if raw_attributes_file and Path(raw_attributes_file).exists():
                            print(f"📄 启用约束映射功能: {raw_attributes_file}")
                            self.validators['constraint'] = SMTValidator(
                                str(smt_full_path),
                                raw_attributes_file,
                                enriched_constraints_file
                            )
                            print("✅ SMT约束验证器初始化成功 (增强模式)")
                        else:
                            print("📝 使用标准模式")
                            self.validators['constraint'] = SMTValidator(str(smt_full_path))
                            print("✅ SMT约束验证器初始化成功 (标准模式)")
                    else:
                        print(f"⚠️  SMT文件未找到: {smt_full_path}")
                else:
                    print("⚠️  配置中未指定SMT Template路径")
            except Exception as e:
                print(f"⚠️  SMT验证器初始化失败: {e}")

    def execute_validation(self, xml_content: str, validation_stages: list = None) -> Dict:
        """执行指定阶段的验证"""

        if validation_stages is None:
            validation_stages = ["structure", "semantic", "constraint"]

        print(f"\n🎯 开始验证流程，包含 {len(validation_stages)} 个阶段: {', '.join(validation_stages)}")

        validation_results = {
            "overall_valid": False,
            "stages": {},
            "summary": {
                "total_stages": 0,
                "passed_stages": 0,
                "failed_stage": None,
                "execution_time": 0,
                "warnings": [],
                "xml_size": len(xml_content),
                "validation_stages": validation_stages
            }
        }

        start_time = time.time()

        try:
            # 分析XML基本信息
            self._analyze_xml_info(xml_content, validation_results)

            # 按顺序执行各个验证阶段
            for stage_num, stage in enumerate(validation_stages, 1):
                print(f"\n{'=' * 60}")
                print(f"🔍 第 {stage_num}/{len(validation_stages)} 阶段: {stage.upper()} 验证")
                print(f"{'=' * 60}")

                if stage not in self.validators:
                    warning_msg = f"{stage} 验证器不可用"
                    validation_results["summary"]["warnings"].append(warning_msg)
                    print(f"⚠️  {warning_msg}")
                    continue

                validation_results["summary"]["total_stages"] += 1
                stage_start_time = time.time()

                try:
                    # 执行对应的验证
                    result = self._execute_stage_validation(stage, xml_content)

                    stage_execution_time = time.time() - stage_start_time
                    result["execution_time"] = stage_execution_time

                    validation_results["stages"][stage] = {
                        "executed": True,
                        "result": result
                    }

                    if result.get("valid", False):
                        validation_results["summary"]["passed_stages"] += 1
                        print(f"✅ {stage.upper()} 验证通过 (耗时: {stage_execution_time:.3f}秒)")
                        self._print_stage_details(stage, result)
                    else:
                        validation_results["summary"]["failed_stage"] = stage
                        print(f"❌ {stage.upper()} 验证失败 (耗时: {stage_execution_time:.3f}秒)")
                        self._print_failure_details(stage, result)
                        # 验证失败时停止后续验证
                        break

                except Exception as e:
                    stage_execution_time = time.time() - stage_start_time
                    validation_results["stages"][stage] = {
                        "executed": True,
                        "result": {
                            "valid": False,
                            "error_info": f"{stage} 验证错误: {str(e)}",
                            "execution_time": stage_execution_time
                        }
                    }
                    validation_results["summary"]["failed_stage"] = stage
                    print(f"❌ {stage.upper()} 验证出错: {e} (耗时: {stage_execution_time:.3f}秒)")
                    break

            # 判断整体验证结果
            if (validation_results["summary"]["passed_stages"] ==
                    validation_results["summary"]["total_stages"] and
                    validation_results["summary"]["total_stages"] > 0):
                validation_results["overall_valid"] = True
                print(
                    f"\n🎉 所有验证阶段通过! ({validation_results['summary']['passed_stages']}/{validation_results['summary']['total_stages']})")
            else:
                failed_at = validation_results["summary"].get("failed_stage", "unknown")
                passed = validation_results["summary"]["passed_stages"]
                total = validation_results["summary"]["total_stages"]
                print(f"\n❌ 验证失败，停止于 {failed_at} 阶段 ({passed}/{total} 阶段通过)")

        except Exception as e:
            validation_results["summary"]["error"] = str(e)
            print(f"❌ 验证编排器错误: {e}")

        # 计算总执行时间
        validation_results["summary"]["execution_time"] = time.time() - start_time
        print(f"\n📊 总验证时间: {validation_results['summary']['execution_time']:.3f}秒")

        return validation_results

    def _analyze_xml_info(self, xml_content: str, validation_results: Dict):
        """分析XML基本信息"""
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_content)

            # 统计XML信息
            all_elements = list(root.iter())
            element_types = set(elem.tag for elem in all_elements)

            xml_info = {
                "root_element": root.tag,
                "total_elements": len(all_elements),
                "element_types": len(element_types),
                "xml_size_kb": len(xml_content) / 1024
            }

            validation_results["summary"]["xml_info"] = xml_info

            print(f"📋 XML文档信息:")
            print(f"   🏷️  根元素: {xml_info['root_element']}")
            print(f"   📊 总元素数: {xml_info['total_elements']}")
            print(f"   🔖 元素类型数: {xml_info['element_types']}")
            print(f"   📏 文档大小: {xml_info['xml_size_kb']:.2f} KB")

        except Exception as e:
            print(f"⚠️  分析XML信息时出错: {e}")

    def _execute_stage_validation(self, stage: str, xml_content: str) -> Dict:
        """执行单个阶段的验证"""
        validator = self.validators[stage]

        if stage == "structure":
            return validator.validate_structure(xml_content)
        elif stage == "semantic":
            return validator.validate_semantics(xml_content)
        elif stage == "constraint":
            return validator.validate_constraints(xml_content)
        else:
            return {"valid": False, "error_info": f"未知验证阶段: {stage}"}

    def _print_stage_details(self, stage: str, result: Dict):
        """打印验证阶段的详细信息 - 增强版"""

        if stage == "structure":
            validation_type = result.get("validation_type", "Unknown")
            print(f"   📄 验证类型: {validation_type}")

            if validation_type == "Basic XML":
                element_count = result.get("element_count", 0)
                root_element = result.get("root_element", "Unknown")
                print(f"   📊 XML元素数: {element_count}")
                print(f"   🏷️  根元素: {root_element}")

                if result.get("xsd_error"):
                    print(f"   ⚠️  XSD问题: Schema版本不兼容")
                    print(f"   ✅ 降级策略: 基础XML验证通过")

            elif validation_type == "XSD":
                schema_file = result.get("schema_file", "N/A")
                if schema_file != "N/A":
                    print(f"   📁 Schema: {Path(schema_file).name}")

        elif stage == "semantic":
            rdf_triples = result.get("rdf_triples", 0)
            shapes_applied = result.get("shapes_applied", 0)
            print(f"   🔗 RDF三元组: {rdf_triples}")
            print(f"   📐 SHACL形状: {shapes_applied}")

            # 显示映射功能状态
            mapping_stats = result.get("mapping_stats", {})
            if mapping_stats.get("mapping_enabled", False):
                print(f"   🔧 映射功能: 已启用")
                print(f"   📊 映射数量: {mapping_stats.get('xml_to_attr_mappings', 0)}")
            else:
                print(f"   📝 映射功能: 标准模式")

            violation_count = result.get("violation_count", 0)
            if violation_count == 0:
                print(f"   ✅ 语义约束: 全部满足")
            else:
                print(f"   ❌ 违规数量: {violation_count}")

        elif stage == "constraint":
            satisfied = result.get("satisfied_count", 0)
            total = result.get("constraint_count", 0)

            # 检查是否为增强模式
            if "constraint_breakdown" in result:
                print(f"   🔧 验证模式: 增强约束验证")
                breakdown = result.get("constraint_breakdown", {})
                print(f"   📊 约束分类:")
                for category, count in breakdown.items():
                    if count > 0:
                        print(f"      {category}: {count}")
            else:
                data_points = result.get("data_points", 0)
                print(f"   📝 验证模式: 标准约束验证")
                print(f"   📊 数据点: {data_points}")

            if total > 0:
                satisfaction_rate = result.get("satisfaction_rate", 0)
                print(f"   ✅ 约束满足: {satisfied}/{total} ({satisfaction_rate:.1%})")

                # 显示具体约束类型
                if satisfied == total:
                    print(f"   🎯 所有SMT约束验证通过")
                elif satisfaction_rate >= 0.8:
                    print(f"   🎯 大部分约束满足，验证通过")
                else:
                    print(f"   ❌ 约束满足率不足")
            else:
                print(f"   📝 无SMT约束需要验证")

    def _print_failure_details(self, stage: str, result: Dict):
        """打印验证失败的详细信息 - 增强版"""

        if stage == "structure":
            error_info = result.get("error_info")
            if error_info:
                print(f"   ❌ XSD错误: {error_info[:150]}...")

            validation_type = result.get("validation_type", "Unknown")
            if validation_type == "Basic XML":
                print(f"   📋 XML格式检查: 通过")
                print(f"   ⚠️  XSD Schema兼容性问题")

        elif stage == "semantic":
            violations = result.get("violations", [])
            violation_count = result.get("violation_count", 0)

            print(f"   📋 SHACL违规总数: {violation_count}")

            if violations:
                print(f"   📋 违规详情:")
                for i, violation in enumerate(violations[:3], 1):
                    severity = violation.get("severity", "Error")
                    message = violation.get("message", "Unknown")
                    focus_node = violation.get("focus_node", "N/A")

                    print(f"      {i}. [{severity}] {message}")
                    if focus_node != "N/A":
                        print(f"         🎯 节点: {focus_node}")

                    # 显示XML元素映射（如果可用）
                    xml_element = violation.get("xml_element")
                    if xml_element:
                        print(f"         🏷️  XML元素: {xml_element}")

                    # 显示约束类型
                    constraint_type = violation.get("constraint_component", "")
                    if constraint_type:
                        print(f"         📏 约束类型: {constraint_type}")

                if len(violations) > 3:
                    print(f"      ... 还有 {len(violations) - 3} 个违规")

        elif stage == "constraint":
            satisfied = result.get("satisfied_count", 0)
            total = result.get("constraint_count", 0)

            # 检查验证模式
            if "constraint_breakdown" in result:
                print(f"   🔧 增强约束验证失败")
                breakdown = result.get("constraint_breakdown", {})
                print(f"   📊 约束统计:")
                for category, count in breakdown.items():
                    print(f"      {category}: {count}")
            else:
                data_points = result.get("data_points", 0)
                print(f"   📝 标准约束验证失败")
                print(f"   📊 约束数据: {data_points} 个数据点")

            print(f"   📋 SMT约束: {satisfied}/{total} 满足")

            unsat_constraints = result.get("unsat_constraints", [])
            if unsat_constraints:
                print(f"   📋 未满足约束:")
                for i, unsat in enumerate(unsat_constraints[:3], 1):
                    status = unsat.get("status", "unknown")
                    error = unsat.get("error", "")
                    constraint_type = unsat.get("constraint_type", "unknown")

                    print(f"      {i}. 类型: {constraint_type}, 状态: {status}")
                    if error:
                        print(f"         原因: {error[:100]}...")

                if len(unsat_constraints) > 3:
                    print(f"      ... 还有 {len(unsat_constraints) - 3} 个")

            # 显示具体的约束违反原因
            satisfaction_rate = result.get("satisfaction_rate", 0)
            if satisfaction_rate < 1.0:
                print(f"   🎯 分析: 满足率 {satisfaction_rate:.1%}")
                if satisfaction_rate >= 0.8:
                    print(f"   💡 建议: 大部分约束满足，可能是边界条件问题")
                else:
                    print(f"   💡 建议: 检查时序参数和数值约束设置")

    def generate_validation_report(self, validation_results: Dict) -> str:
        """生成超详细的验证报告"""

        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("AUTOSAR XML 超详细验证报告")
        report_lines.append("=" * 80)

        # XML文档信息
        xml_info = validation_results['summary'].get('xml_info', {})
        if xml_info:
            report_lines.append(f"📋 XML文档信息:")
            report_lines.append(f"   根元素: {xml_info.get('root_element', 'Unknown')}")
            report_lines.append(f"   文档大小: {xml_info.get('xml_size_kb', 0):.2f} KB")
            report_lines.append(f"   元素总数: {xml_info.get('total_elements', 0)}")
            report_lines.append(f"   元素类型: {xml_info.get('element_types', 0)} 种")
            report_lines.append("")

        # 验证结果摘要
        overall_status = "✅ 通过" if validation_results["overall_valid"] else "❌ 失败"
        exec_time = validation_results['summary']['execution_time']

        report_lines.append(f"🎯 验证结果: {overall_status}")
        report_lines.append(f"⏱️  执行时间: {exec_time:.3f}秒")

        passed = validation_results['summary']['passed_stages']
        total = validation_results['summary']['total_stages']
        stages = validation_results['summary'].get('validation_stages', [])

        report_lines.append(f"📊 验证进度: {passed}/{total} 阶段通过")
        report_lines.append(f"🔄 验证流程: {' → '.join(stages)}")

        if validation_results['summary'].get('failed_stage'):
            failed_stage = validation_results['summary']['failed_stage']
            report_lines.append(f"🛑 失败阶段: {failed_stage}")

        report_lines.append("")

        # 各阶段超详细信息
        stage_names = {
            "structure": "🏗️  结构验证 (XSD Schema)",
            "semantic": "🧠 语义验证 (SHACL Shapes)",
            "constraint": "🔢 约束验证 (SMT Solver)"
        }

        for stage_key, stage_info in validation_results["stages"].items():
            if stage_info["executed"]:
                stage_name = stage_names.get(stage_key, stage_key.title())
                result = stage_info["result"]
                exec_time = result.get("execution_time", 0)

                status = "✅ 通过" if result.get("valid", False) else "❌ 失败"
                report_lines.append(f"{stage_name}: {status} ({exec_time:.3f}s)")

                # 结构验证详细信息
                if stage_key == "structure":
                    val_type = result.get("validation_type", "Unknown")
                    report_lines.append(f"   验证方式: {val_type}")

                    if val_type == "Basic XML":
                        element_count = result.get("element_count", 0)
                        report_lines.append(f"   XML元素: {element_count} 个")

                        if result.get("xsd_error"):
                            report_lines.append(f"   XSD兼容: Schema版本不匹配，已降级")
                            report_lines.append(f"   降级结果: 基础XML验证通过")

                    elif val_type == "XSD":
                        schema_file = result.get("schema_file", "")
                        if schema_file:
                            report_lines.append(f"   Schema: {Path(schema_file).name}")

                # 语义验证详细信息
                elif stage_key == "semantic":
                    rdf_triples = result.get("rdf_triples", 0)
                    shapes_applied = result.get("shapes_applied", 0)

                    report_lines.append(f"   RDF转换: {rdf_triples} 个三元组")
                    report_lines.append(f"   SHACL形状: {shapes_applied} 个")

                    # 映射功能状态
                    mapping_stats = result.get("mapping_stats", {})
                    if mapping_stats.get("mapping_enabled", False):
                        report_lines.append(
                            f"   映射功能: 已启用 ({mapping_stats.get('xml_to_attr_mappings', 0)} 个映射)")
                    else:
                        report_lines.append(f"   映射功能: 标准模式")

                    violation_count = result.get("violation_count", 0)
                    if violation_count == 0:
                        report_lines.append(f"   约束满足: 所有语义约束通过")
                    else:
                        report_lines.append(f"   违规发现: {violation_count} 个")

                        violations = result.get("violations", [])
                        for i, violation in enumerate(violations[:3], 1):
                            severity = violation.get("severity", "Error")
                            message = violation.get("message", "No message")
                            report_lines.append(f"     {i}. [{severity}] {message}")

                            # 显示XML元素信息（如果可用）
                            xml_element = violation.get("xml_element")
                            if xml_element:
                                report_lines.append(f"        XML元素: {xml_element}")

                # 约束验证详细信息
                elif stage_key == "constraint":
                    satisfied = result.get("satisfied_count", 0)
                    total_constraints = result.get("constraint_count", 0)

                    # 检查验证模式
                    if "constraint_breakdown" in result:
                        report_lines.append(f"   验证模式: 增强约束验证")
                        breakdown = result.get("constraint_breakdown", {})
                        report_lines.append(f"   约束分类:")
                        for category, count in breakdown.items():
                            if count > 0:
                                report_lines.append(f"     {category}: {count}")
                    else:
                        data_points = result.get("data_points", 0)
                        report_lines.append(f"   验证模式: 标准约束验证")
                        report_lines.append(f"   数据提取: {data_points} 个约束数据点")

                    if total_constraints > 0:
                        satisfaction_rate = result.get("satisfaction_rate", 0)
                        report_lines.append(
                            f"   约束求解: {satisfied}/{total_constraints} 满足 ({satisfaction_rate:.1%})")

                        if satisfaction_rate == 1.0:
                            report_lines.append(f"   验证结果: 所有SMT约束满足")
                        elif satisfaction_rate >= 0.8:
                            report_lines.append(f"   验证结果: 大部分约束满足，通过验证")
                        else:
                            report_lines.append(f"   验证结果: 约束违反，需要调整")
                    else:
                        report_lines.append(f"   验证结果: 无约束数据，跳过验证")

                # 错误信息
                if result.get("error_info") or result.get("error"):
                    error = result.get("error_info") or result.get("error")
                    report_lines.append(f"   错误详情: {error[:100]}...")

                report_lines.append("")

        # 验证建议
        if not validation_results["overall_valid"]:
            report_lines.append("💡 验证建议:")
            failed_stage = validation_results['summary'].get('failed_stage')

            if failed_stage == "structure":
                report_lines.append("   🔧 结构问题: 检查XML元素名称和属性")
                report_lines.append("   📚 参考: AUTOSAR 4.2.2 规范文档")

            elif failed_stage == "semantic":
                report_lines.append("   🧠 语义问题: 检查业务逻辑和数据关系")
                report_lines.append("   📐 参考: SHACL形状定义文件")

                # 检查是否有映射功能建议
                semantic_result = validation_results["stages"].get("semantic", {}).get("result", {})
                mapping_stats = semantic_result.get("mapping_stats", {})
                if not mapping_stats.get("mapping_enabled", False):
                    report_lines.append("   💡 建议: 启用映射功能以获得更精确的验证")

            elif failed_stage == "constraint":
                report_lines.append("   🔢 约束问题: 检查时序参数和数值设置")
                report_lines.append("   ⏰ 建议: 确保deadline < period，timeout > period")

                # 检查是否有增强功能建议
                constraint_result = validation_results["stages"].get("constraint", {}).get("result", {})
                if "constraint_breakdown" not in constraint_result:
                    report_lines.append("   💡 建议: 启用增强约束验证以获得详细分析")

            report_lines.append("")

        # 技术统计
        warnings = validation_results['summary'].get('warnings', [])
        if warnings:
            report_lines.append("⚠️  警告信息:")
            for warning in warnings:
                report_lines.append(f"   - {warning}")
            report_lines.append("")

        # 功能使用统计
        report_lines.append("🔧 功能使用统计:")

        semantic_result = validation_results["stages"].get("semantic", {}).get("result", {})
        constraint_result = validation_results["stages"].get("constraint", {}).get("result", {})

        # 语义验证功能
        mapping_stats = semantic_result.get("mapping_stats", {})
        if mapping_stats.get("mapping_enabled", False):
            report_lines.append(f"   ✅ SHACL映射功能: 已启用")
        else:
            report_lines.append(f"   📝 SHACL映射功能: 标准模式")

        # 约束验证功能
        if "constraint_breakdown" in constraint_result:
            report_lines.append(f"   ✅ SMT增强验证: 已启用")
        else:
            report_lines.append(f"   📝 SMT增强验证: 标准模式")

        return "\n".join(report_lines)

    def execute_full_validation(self, xml_content: str, validation_level: str = "full") -> Dict:
        """为兼容性提供的方法，调用execute_validation"""

        # 根据validation_level确定验证阶段
        if validation_level == "structure":
            validation_stages = ["structure"]
        elif validation_level == "semantic":
            validation_stages = ["structure", "semantic"]
        elif validation_level == "constraint":
            validation_stages = ["constraint"]
        else:  # full
            validation_stages = ["structure", "semantic", "constraint"]

        return self.execute_validation(xml_content, validation_stages)