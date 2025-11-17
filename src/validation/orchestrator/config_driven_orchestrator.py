# src/validation/orchestrator/config_driven_orchestrator.py
"""
配置驱动的验证编排器 - 增强版（支持映射文件传递）
"""
from typing import Dict, Optional, List
import time
from pathlib import Path


class ConfigDrivenOrchestrator:
    """配置驱动的验证编排器 - 支持增强功能"""

    def __init__(self, config: Dict):
        """初始化验证编排器"""
        self.config = config
        self.validators = {}
        self._init_validators()


    def _print_stage_details(self, stage: str, result: Dict):
        """打印验证阶段的详细信息 - 增强SHACL详细违规显示"""

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
            validation_mode = result.get("validation_mode", "hybrid")

            print(f"   🔧 验证模式: {validation_mode}")
            print(f"   🔗 RDF三元组: {rdf_triples}")
            print(f"   📐 SHACL形状: {shapes_applied}")

            # 🔧 增强：显示详细的SHACL违规分解
            violation_breakdown = result.get("violation_breakdown", {})
            if violation_breakdown and isinstance(violation_breakdown, dict):
                # 显示总体配置
                config = violation_breakdown.get("configuration", {})
                if config:
                    struct_enabled = config.get("structural_enabled", True)
                    semantic_enabled = config.get("semantic_enabled", True)
                    print(f"   📋 验证范围: 结构{'✅' if struct_enabled else '❌'} 语义{'✅' if semantic_enabled else '❌'}")

                    # 显示严重性过滤配置
                    severity_filter = config.get("severity_filter", {})
                    if severity_filter:
                        print(f"   🔍 严重性过滤:")
                        for category, levels in severity_filter.items():
                            print(f"      {category}: {', '.join(levels)}")

                # 显示结构验证详情
                structural = violation_breakdown.get("structural", {})
                if structural:
                    print(f"   🔧 结构验证详情:")
                    for constraint_type, stats in structural.items():
                        if isinstance(stats, dict) and stats.get("total", 0) > 0:
                            total_count = stats.get("total", 0)
                            violations = stats.get("violations", 0)
                            status = "✅" if violations == 0 else f"❌({violations})"
                            print(f"      {constraint_type}: {total_count} 个 {status}")

                # 🔧 显示语义验证详情 - 按类型细分
                semantic = violation_breakdown.get("semantic", {})
                if semantic:
                    print(f"   💡 语义验证详情:")

                    # 按约束类型分组显示
                    constraint_types = {
                        "existence": "存在性约束",
                        "value_restriction": "值限制约束",
                        "cardinality": "基数约束",
                        "dependency": "依赖关系约束",
                        "mutual_exclusion": "互斥约束",
                        "format": "格式约束",
                        "range": "范围约束",
                        "behavioral": "行为约束",
                        "other": "其他约束"
                    }

                    for constraint_type, type_name in constraint_types.items():
                        if constraint_type in semantic:
                            stats = semantic[constraint_type]
                            if isinstance(stats, dict) and stats.get("total", 0) > 0:
                                total_count = stats.get("total", 0)
                                violations = stats.get("violations", 0)
                                warnings = stats.get("warnings", 0)
                                info = stats.get("info", 0)
                                enabled = stats.get("enabled", True)

                                # 状态显示
                                if violations > 0:
                                    status = f"❌({violations})"
                                elif warnings > 0:
                                    status = f"⚠️({warnings})"
                                elif info > 0:
                                    status = f"ℹ️({info})"
                                else:
                                    status = "✅"

                                enable_status = "" if enabled else " [禁用]"
                                print(f"      {type_name}: {total_count} 个 {status}{enable_status}")

            # 显示映射功能状态
            mapping_stats = result.get("mapping_stats", {})
            if mapping_stats.get("mapping_enabled", False):
                print(f"   🔧 映射功能: 已启用")
                print(f"   📊 映射统计:")
                print(f"      XML->属性映射: {mapping_stats.get('xml_to_attr_mappings', 0)}")
                print(f"      Wrapper映射: {mapping_stats.get('wrapper_mappings', 0)}")
                print(f"      文本内容映射: {mapping_stats.get('text_content_mappings', 0)}")
            else:
                print(f"   📝 映射功能: 标准模式")

            # 🔧 关键增强：显示所有SHACL违规的详细信息
            violation_count = result.get("violation_count", 0)
            if violation_count == 0:
                print(f"   ✅ SHACL约束: 全部满足")
            else:
                print(f"   📊 违规发现: {violation_count} 个")

                # 🔧 新增：显示完整的违规统计
                violation_stats = result.get("violation_stats", {})
                violations = violation_stats.get("violations", 0)
                warnings = violation_stats.get("warnings", 0)
                info = violation_stats.get("info", 0)

                print(f"   📈 违规统计分解:")
                if violations > 0:
                    print(f"      ❌ 结构错误: {violations} 个")
                if warnings > 0:
                    print(f"      ⚠️  语义警告: {warnings} 个")
                if info > 0:
                    print(f"      ℹ️  格式建议: {info} 个")

                # 🔧 新增：显示所有违规的详细信息
                self._print_all_shacl_violations(result)

            # 显示验证配置
            validation_config = result.get("validation_config", {})
            if validation_config:
                print(f"   ⚙️  验证配置:")
                print(f"      模式: {validation_config.get('mode', 'hybrid')}")
                semantic_types_config = validation_config.get('semantic_types_config', {})
                if semantic_types_config:
                    enabled_count = sum(1 for v in semantic_types_config.values() if v)
                    total_count = len(semantic_types_config)
                    print(f"      启用类型: {enabled_count}/{total_count}")

        elif stage == "constraint":
            # ... 保持原有的约束验证显示逻辑 ...
            satisfied = result.get("satisfied_count", 0)
            total = result.get("constraint_count", 0)
            validation_mode = result.get("validation_mode", "hybrid")

            print(f"   🔧 验证模式: {validation_mode}")

            # 显示详细的约束类型分解
            breakdown = result.get("constraint_breakdown", {})
            if breakdown and isinstance(breakdown, dict):
                # 显示总体配置
                config = breakdown.get("configuration", {})
                if config:
                    struct_enabled = config.get("structural_enabled", True)
                    semantic_enabled = config.get("semantic_enabled", True)
                    print(f"   📋 约束范围: 结构{'✅' if struct_enabled else '❌'} 语义{'✅' if semantic_enabled else '❌'}")

                    if config.get("fail_fast", True):
                        print(f"   ⚡ 失败策略: 快速失败")

                # 显示结构约束详情
                structural = breakdown.get("structural", {})
                if structural:
                    print(f"   🔧 结构约束详情:")
                    for constraint_type, stats in structural.items():
                        if isinstance(stats, dict):
                            total_count = stats.get("total", 0)
                            satisfied_count = stats.get("satisfied", 0)
                            violations = stats.get("violations", 0)
                            status = "✅" if violations == 0 else "❌"
                            print(f"      {constraint_type}: {satisfied_count}/{total_count} {status}")

                # 显示语义约束详情 - 按类型细分
                semantic = breakdown.get("semantic", {})
                if semantic:
                    print(f"   💡 语义约束详情:")

                    constraint_types = {
                        "existence": "存在性约束",
                        "value_restriction": "值限制约束",
                        "cardinality": "基数约束",
                        "dependency": "依赖关系约束",
                        "mutual_exclusion": "互斥约束",
                        "format": "格式约束",
                        "range": "范围约束",
                        "behavioral": "行为约束",
                        "other": "其他约束"
                    }

                    for constraint_type, type_name in constraint_types.items():
                        if constraint_type in semantic:
                            stats = semantic[constraint_type]
                            if isinstance(stats, dict):
                                total_count = stats.get("total", 0)
                                satisfied_count = stats.get("satisfied", 0)
                                warnings = stats.get("warnings", 0)
                                enabled = stats.get("enabled", True)

                                if total_count > 0:
                                    status = "✅" if warnings == 0 else "⚠️"
                                    enable_status = "启用" if enabled else "禁用"
                                    print(
                                        f"      {type_name}: {satisfied_count}/{total_count} {status} ({enable_status})")

            # 显示总体统计
            if total > 0:
                satisfaction_rate = result.get("satisfaction_rate", 0)
                print(f"   📈 总体满足率: {satisfied}/{total} ({satisfaction_rate:.1%})")

                if satisfied == total:
                    print(f"   🎯 验证结果: 所有约束验证通过")
                elif satisfaction_rate >= 0.8:
                    print(f"   🎯 验证结果: 大部分约束满足")
                else:
                    print(f"   ❌ 验证结果: 需要关注约束违规")
            else:
                print(f"   📝 验证结果: 无约束需要验证")

    def _print_all_shacl_violations(self, result: Dict):
        """🔧 新增：打印所有SHACL违规的详细信息"""
        violations = result.get("violations", [])

        if not violations:
            return

        print(f"   📋 详细违规信息:")

        # 按严重性分组
        violations_by_severity = {}
        for violation in violations:
            severity = violation.get('severity', 'Unknown').lower()
            if severity not in violations_by_severity:
                violations_by_severity[severity] = []
            violations_by_severity[severity].append(violation)

        # 定义严重性显示顺序和图标
        severity_display = {
            'violation': {'icon': '❌', 'name': '结构错误'},
            'error': {'icon': '❌', 'name': '结构错误'},
            'warning': {'icon': '⚠️', 'name': '语义警告'},
            'info': {'icon': 'ℹ️', 'name': '格式建议'}
        }

        violation_index = 1

        for severity in ['violation', 'error', 'warning', 'info']:
            if severity in violations_by_severity:
                severity_violations = violations_by_severity[severity]
                severity_info = severity_display.get(severity, {'icon': '❓', 'name': severity})

                print(f"      {severity_info['icon']} {severity_info['name']} ({len(severity_violations)} 个):")

                for violation in severity_violations:
                    # 提取详细信息
                    message = violation.get('message', 'No message available')
                    focus_node = violation.get('focus_node', 'Unknown')
                    result_path = violation.get('result_path', 'Unknown')
                    constraint_component = violation.get('constraint_component', 'Unknown')
                    source_constraint = violation.get('source_constraint', 'Unknown')
                    xml_element = violation.get('xml_element', '')
                    semantic_type = violation.get('semantic_type', '')

                    # 显示基本信息
                    print(f"        {violation_index}. {message}")

                    # 显示详细的上下文信息
                    if focus_node and focus_node != 'Unknown':
                        print(f"           🎯 焦点节点: {focus_node}")

                    if result_path and result_path != 'Unknown':
                        print(f"           📍 结果路径: {result_path}")

                    if xml_element:
                        print(f"           🏷️  XML元素: {xml_element}")

                    if constraint_component and constraint_component != 'Unknown':
                        print(f"           📏 约束组件: {constraint_component}")

                    if source_constraint and source_constraint != 'Unknown':
                        print(f"           📐 源约束: {source_constraint}")

                    if semantic_type:
                        print(f"           💡 语义类型: {semantic_type}")

                    # 添加分隔线（除了最后一个）
                    if violation_index < len(violations):
                        print(f"           {'-' * 50}")

                    violation_index += 1

        # 显示违规模式统计
        print(f"   📊 违规模式分析:")
        constraint_components = {}
        xml_elements = {}

        for violation in violations:
            # 统计约束组件
            comp = violation.get('constraint_component', 'Unknown')
            constraint_components[comp] = constraint_components.get(comp, 0) + 1

            # 统计XML元素
            elem = violation.get('xml_element', violation.get('focus_node', 'Unknown'))
            if elem and elem != 'Unknown':
                xml_elements[elem] = xml_elements.get(elem, 0) + 1

        # 显示最常见的约束组件
        if constraint_components:
            print(f"      🔧 最常见约束组件:")
            sorted_components = sorted(constraint_components.items(), key=lambda x: x[1], reverse=True)
            for comp, count in sorted_components[:5]:  # 显示前5个
                print(f"         {comp}: {count} 次")

        # 显示最常违规的XML元素
        if xml_elements:
            print(f"      🏷️  最常违规元素:")
            sorted_elements = sorted(xml_elements.items(), key=lambda x: x[1], reverse=True)
            for elem, count in sorted_elements[:5]:  # 显示前5个
                print(f"         {elem}: {count} 次")

    def generate_validation_report(self, validation_results: Dict) -> str:
        """生成超详细的验证报告 - 增强SHACL违规详情"""

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

                # 🔧 增强语义验证报告 - 显示所有违规详情
                if stage_key == "semantic":
                    rdf_triples = result.get("rdf_triples", 0)
                    shapes_applied = result.get("shapes_applied", 0)
                    validation_mode = result.get("validation_mode", "hybrid")

                    report_lines.append(f"   🔧 验证模式: {validation_mode}")
                    report_lines.append(f"   🔗 RDF三元组: {rdf_triples}")
                    report_lines.append(f"   📐 SHACL形状: {shapes_applied}")

                    # 映射功能状态
                    mapping_stats = result.get("mapping_stats", {})
                    if mapping_stats.get("mapping_enabled", False):
                        report_lines.append(
                            f"   🔧 映射功能: 已启用 ({mapping_stats.get('xml_to_attr_mappings', 0)} 个映射)")
                    else:
                        report_lines.append(f"   📝 映射功能: 标准模式")

                    violation_count = result.get("violation_count", 0)
                    if violation_count == 0:
                        report_lines.append(f"   ✅ SHACL约束: 全部满足")
                    else:
                        report_lines.append(f"   📊 违规发现: {violation_count} 个")

                        # 🔧 新增：添加完整的违规详情到报告
                        report_lines.extend(self._generate_detailed_shacl_violation_report(result))

                # 其他阶段的处理保持原样...
                elif stage_key == "structure":
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

                elif stage_key == "constraint":
                    satisfied = result.get("satisfied_count", 0)
                    total_constraints = result.get("constraint_count", 0)

                    breakdown = result.get("constraint_breakdown", {})
                    if breakdown and isinstance(breakdown, dict):
                        report_lines.append(f"   验证模式: 增强约束验证")
                        report_lines.append(f"   约束分类:")

                        for category, count_data in breakdown.items():
                            try:
                                if isinstance(count_data, dict):
                                    total_count = self._safe_int_conversion(count_data.get("total", 0), 0)
                                    satisfied_count = self._safe_int_conversion(count_data.get("satisfied", 0), 0)
                                    violations_count = self._safe_int_conversion(count_data.get("violations", 0), 0)

                                    if total_count > 0:
                                        report_lines.append(f"     {category}: {satisfied_count}/{total_count} 满足")
                                        if violations_count > 0:
                                            report_lines.append(f"       违规: {violations_count} 个")
                                else:
                                    count = self._safe_int_conversion(count_data, 0)
                                    if count > 0:
                                        report_lines.append(f"     {category}: {count}")
                            except Exception as breakdown_error:
                                report_lines.append(f"     {category}: 数据解析错误")
                                continue
                    else:
                        data_points = result.get("data_points", 0)
                        report_lines.append(f"   验证模式: 标准约束验证")
                        report_lines.append(f"   数据提取: {data_points} 个约束数据点")

                    if total_constraints > 0:
                        satisfaction_rate = result.get("satisfaction_rate", 0)
                        try:
                            if isinstance(satisfaction_rate, (int, float)):
                                rate_percent = satisfaction_rate * 100 if satisfaction_rate <= 1 else satisfaction_rate
                                report_lines.append(
                                    f"   约束求解: {satisfied}/{total_constraints} 满足 ({rate_percent:.1f}%)")
                            else:
                                report_lines.append(f"   约束求解: {satisfied}/{total_constraints} 满足")
                        except Exception:
                            report_lines.append(f"   约束求解: {satisfied}/{total_constraints} 满足")

                        if satisfied == total_constraints:
                            report_lines.append(f"   验证结果: 所有SMT约束满足")
                        elif satisfaction_rate >= 0.8:
                            report_lines.append(f"   验证结果: 大部分约束满足，通过验证")
                        else:
                            report_lines.append(f"   验证结果: 约束违反，需要调整")
                    else:
                        report_lines.append(f"   验证结果: 无约束数据，跳过验证")

                # 错误信息
                error_info = result.get("error_info") or result.get("error")
                if error_info:
                    try:
                        error_str = str(error_info)
                        if len(error_str) > 100:
                            error_str = error_str[:100] + "..."
                        report_lines.append(f"   错误详情: {error_str}")
                    except Exception:
                        report_lines.append(f"   错误详情: [错误信息解析失败]")

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

    def _generate_detailed_shacl_violation_report(self, result: Dict) -> List[str]:
        """🔧 新增：生成详细的SHACL违规报告行"""

        violations = result.get("violations", [])
        if not violations:
            return ["     ✅ 无违规发现"]

        report_lines = []

        # 按严重性分组
        violations_by_severity = {}
        for violation in violations:
            severity = violation.get('severity', 'Unknown').lower()
            if severity not in violations_by_severity:
                violations_by_severity[severity] = []
            violations_by_severity[severity].append(violation)

        # 定义严重性显示顺序
        severity_display = {
            'violation': {'icon': '❌', 'name': '结构错误'},
            'error': {'icon': '❌', 'name': '结构错误'},
            'warning': {'icon': '⚠️', 'name': '语义警告'},
            'info': {'icon': 'ℹ️', 'name': '格式建议'}
        }

        violation_index = 1

        for severity in ['violation', 'error', 'warning', 'info']:
            if severity in violations_by_severity:
                severity_violations = violations_by_severity[severity]
                severity_info = severity_display.get(severity, {'icon': '❓', 'name': severity})

                report_lines.append(
                    f"     {severity_info['icon']} {severity_info['name']} ({len(severity_violations)} 个):")

                for violation in severity_violations:
                    # 提取详细信息
                    message = violation.get('message', 'No message available')
                    focus_node = violation.get('focus_node', '')
                    result_path = violation.get('result_path', '')
                    constraint_component = violation.get('constraint_component', '')
                    source_constraint = violation.get('source_constraint', '')
                    xml_element = violation.get('xml_element', '')
                    semantic_type = violation.get('semantic_type', '')

                    # 显示基本信息
                    report_lines.append(f"       {violation_index}. {message}")

                    # 显示详细的上下文信息
                    detail_lines = []
                    if focus_node and focus_node != 'Unknown':
                        detail_lines.append(f"焦点节点: {focus_node}")

                    if result_path and result_path != 'Unknown':
                        detail_lines.append(f"结果路径: {result_path}")

                    if xml_element:
                        detail_lines.append(f"XML元素: {xml_element}")

                    if constraint_component and constraint_component != 'Unknown':
                        detail_lines.append(f"约束组件: {constraint_component}")

                    if source_constraint and source_constraint != 'Unknown':
                        detail_lines.append(f"源约束: {source_constraint}")

                    if semantic_type:
                        detail_lines.append(f"语义类型: {semantic_type}")

                    # 将详细信息添加到报告中
                    if detail_lines:
                        report_lines.append(f"          详情: {' | '.join(detail_lines)}")

                    violation_index += 1

        # 添加违规模式统计
        report_lines.append(f"     📊 违规模式分析:")
        constraint_components = {}
        xml_elements = {}
        semantic_types = {}

        for violation in violations:
            # 统计约束组件
            comp = violation.get('constraint_component', 'Unknown')
            if comp and comp != 'Unknown':
                constraint_components[comp] = constraint_components.get(comp, 0) + 1

            # 统计XML元素
            elem = violation.get('xml_element', violation.get('focus_node', ''))
            if elem and elem != 'Unknown':
                xml_elements[elem] = xml_elements.get(elem, 0) + 1

            # 统计语义类型
            sem_type = violation.get('semantic_type', '')
            if sem_type:
                semantic_types[sem_type] = semantic_types.get(sem_type, 0) + 1

        # 显示最常见的约束组件
        if constraint_components:
            report_lines.append(f"       🔧 约束组件分布:")
            sorted_components = sorted(constraint_components.items(), key=lambda x: x[1], reverse=True)
            for comp, count in sorted_components[:3]:  # 显示前3个
                percentage = (count / len(violations)) * 100
                report_lines.append(f"         {comp}: {count} 次 ({percentage:.1f}%)")

        # 显示最常违规的XML元素
        if xml_elements:
            report_lines.append(f"       🏷️  元素违规分布:")
            sorted_elements = sorted(xml_elements.items(), key=lambda x: x[1], reverse=True)
            for elem, count in sorted_elements[:3]:  # 显示前3个
                percentage = (count / len(violations)) * 100
                report_lines.append(f"         {elem}: {count} 次 ({percentage:.1f}%)")

        # 显示语义类型分布
        if semantic_types:
            report_lines.append(f"       💡 语义类型分布:")
            sorted_types = sorted(semantic_types.items(), key=lambda x: x[1], reverse=True)
            for sem_type, count in sorted_types[:3]:  # 显示前3个
                percentage = (count / len(violations)) * 100
                report_lines.append(f"         {sem_type}: {count} 次 ({percentage:.1f}%)")

        return report_lines

    def generate_shacl_violation_summary_report(self, validation_results: Dict) -> str:
        """🔧 新增：生成专门的SHACL违规摘要报告"""

        semantic_result = validation_results["stages"].get("semantic", {}).get("result", {})
        if not semantic_result:
            return "SHACL语义验证未执行或失败"

        lines = []
        lines.append("📊 SHACL违规详细分析报告")
        lines.append("=" * 60)

        violation_count = semantic_result.get("violation_count", 0)
        validation_mode = semantic_result.get("validation_mode", "hybrid")

        lines.append(f"验证模式: {validation_mode}")
        lines.append(f"违规总数: {violation_count}")
        lines.append("")

        if violation_count == 0:
            lines.append("✅ 未发现任何SHACL违规")
            return "\n".join(lines)

        violations = semantic_result.get("violations", [])

        # 按严重性统计
        violation_stats = semantic_result.get("violation_stats", {})
        violations_count = violation_stats.get("violations", 0)
        warnings_count = violation_stats.get("warnings", 0)
        info_count = violation_stats.get("info", 0)

        lines.append("📈 严重性分布:")
        if violations_count > 0:
            lines.append(f"  ❌ 结构错误: {violations_count} 个 ({violations_count / violation_count * 100:.1f}%)")
        if warnings_count > 0:
            lines.append(f"  ⚠️  语义警告: {warnings_count} 个 ({warnings_count / violation_count * 100:.1f}%)")
        if info_count > 0:
            lines.append(f"  ℹ️  格式建议: {info_count} 个 ({info_count / violation_count * 100:.1f}%)")
        lines.append("")

        # 详细违规列表
        lines.append("📋 详细违规列表:")
        lines.extend(self._generate_detailed_shacl_violation_report(semantic_result))
        lines.append("")

        # 修复建议
        lines.append("💡 修复建议:")
        if violations_count > 0:
            lines.append("  1. 优先修复结构错误，这些会影响XML的基本合规性")
            lines.append("  2. 检查元素的必需属性和基数约束")
        if warnings_count > 0:
            lines.append("  3. 关注语义警告，这些涉及业务逻辑的正确性")
            lines.append("  4. 验证跨元素的关系和依赖约束")
        if info_count > 0:
            lines.append("  5. 考虑格式建议，提升文档的规范性")

        return "\n".join(lines)

    def _print_failure_details(self, stage: str, result: Dict):
        """打印验证失败的详细信息 - 增强SHACL失败详情显示"""

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
            validation_mode = result.get("validation_mode", "hybrid")

            print(f"   🔧 SHACL验证模式: {validation_mode}")
            print(f"   📋 违规总数: {violation_count}")

            # 🔧 增强：按类型显示SHACL违规详情
            violation_breakdown = result.get("violation_breakdown", {})
            if violation_breakdown and isinstance(violation_breakdown, dict):

                # 显示结构验证失败
                structural = violation_breakdown.get("structural", {})
                if structural:
                    print(f"   🔧 结构验证失败:")
                    for constraint_type, stats in structural.items():
                        if isinstance(stats, dict):
                            violations_count = stats.get("violations", 0)
                            total_count = stats.get("total", 0)
                            if violations_count > 0:
                                print(f"      {constraint_type}: {violations_count}/{total_count} 失败")

                # 显示语义验证警告
                semantic = violation_breakdown.get("semantic", {})
                if semantic:
                    print(f"   💡 语义验证问题:")

                    constraint_types = {
                        "existence": "存在性",
                        "value_restriction": "值限制",
                        "cardinality": "基数",
                        "dependency": "依赖关系",
                        "mutual_exclusion": "互斥",
                        "format": "格式",
                        "range": "范围",
                        "behavioral": "行为"
                    }

                    for constraint_type, type_name in constraint_types.items():
                        if constraint_type in semantic:
                            stats = semantic[constraint_type]
                            if isinstance(stats, dict):
                                violations_count = stats.get("violations", 0)
                                warnings_count = stats.get("warnings", 0)
                                total_count = stats.get("total", 0)
                                enabled = stats.get("enabled", True)

                                issues = violations_count + warnings_count
                                if issues > 0:
                                    status = "禁用" if not enabled else "问题"
                                    print(f"      {type_name}约束: {issues}/{total_count} {status}")

            # 🔧 增强：显示所有违规的详细信息（失败时）
            if violations:
                print(f"   📋 完整违规详情:")
                self._print_all_shacl_violations(result)

            # 显示建议
            validation_config = result.get("validation_config", {})
            mode = validation_config.get('mode', 'hybrid')
            if mode == "semantic_only":
                print(f"   💡 建议: 检查语义约束配置，考虑调整约束类型启用状态")
            elif mode == "structural_only":
                print(f"   💡 建议: 检查SHACL结构约束，确保必需属性和基数要求")
            else:
                semantic_compliance = result.get('semantic_compliance', 'UNKNOWN')
                if semantic_compliance in ['HIGH', 'PARTIAL']:
                    print(f"   💡 建议: 主要约束已满足，关注剩余的语义警告")
                else:
                    print(f"   💡 建议: 检查SHACL形状定义和XML数据的匹配度")

        elif stage == "constraint":
            # 保持原有的约束验证失败显示逻辑
            satisfied = result.get("satisfied_count", 0)
            total = result.get("constraint_count", 0)
            validation_mode = result.get("validation_mode", "hybrid")

            print(f"   🔧 约束验证模式: {validation_mode}")

            # 显示失败的约束类型统计
            breakdown = result.get("constraint_breakdown", {})
            if breakdown and isinstance(breakdown, dict):

                # 显示结构约束失败
                structural = breakdown.get("structural", {})
                if structural:
                    print(f"   🔧 结构约束失败:")
                    for constraint_type, stats in structural.items():
                        if isinstance(stats, dict):
                            violations = stats.get("violations", 0)
                            total_count = stats.get("total", 0)
                            if violations > 0:
                                print(f"      {constraint_type}: {violations}/{total_count} 失败")

                # 显示语义约束警告
                semantic = breakdown.get("semantic", {})
                if semantic:
                    print(f"   💡 语义约束警告:")

                    constraint_types = {
                        "existence": "存在性",
                        "value_restriction": "值限制",
                        "cardinality": "基数",
                        "dependency": "依赖关系",
                        "mutual_exclusion": "互斥",
                        "format": "格式",
                        "range": "范围",
                        "behavioral": "行为"
                    }

                    for constraint_type, type_name in constraint_types.items():
                        if constraint_type in semantic:
                            stats = semantic[constraint_type]
                            if isinstance(stats, dict):
                                warnings = stats.get("warnings", 0)
                                total_count = stats.get("total", 0)
                                if warnings > 0:
                                    print(f"      {type_name}约束: {warnings}/{total_count} 不符合推荐")

            # 显示具体违规
            structural_violations = result.get("structural_violations", [])
            semantic_warnings = result.get("semantic_warnings", [])

            max_display = 5  # 增加显示数量

            if structural_violations:
                print(f"   📋 结构违规详情:")
                for i, violation in enumerate(structural_violations[:max_display], 1):
                    constraint_id = violation.get("constraint_id", "unknown")
                    message = violation.get("message", "No message")
                    print(f"      {i}. [{constraint_id}] {message[:100]}...")

            if semantic_warnings:
                print(f"   📋 语义警告详情:")
                for i, warning in enumerate(semantic_warnings[:max_display], 1):
                    constraint_id = warning.get("constraint_id", "unknown")
                    constraint_type = warning.get("constraint_type", "unknown")
                    message = warning.get("message", "No message")
                    print(f"      {i}. [{constraint_type}] {message[:100]}...")

            # 显示建议
            satisfaction_rate = result.get("satisfaction_rate", 0)
            if validation_mode == "semantic_only":
                print(f"   💡 建议: 检查语义约束配置，考虑调整约束类型启用状态")
            elif validation_mode == "structural_only":
                print(f"   💡 建议: 检查XML结构合规性，确保必需元素存在")
            else:
                if satisfaction_rate >= 0.8:
                    print(f"   💡 建议: 主要约束已满足，关注剩余的边界条件")
                else:
                    print(f"   💡 建议: 检查约束配置和XML数据的匹配度")

    def _init_validators(self):
        """根据配置初始化验证器 - 支持SHACL和SMT细粒度控制"""
        print("\n🔧 初始化验证器...")
        validator_config = self.config.get("validators", {})
        file_paths = self.config.get("file_paths", {})

        # 获取项目根目录
        project_root = Path(self.config.get("project_root", "."))

        # 🔧 获取语义和约束验证配置
        semantic_config = validator_config.get("semantic", {})
        constraint_config = validator_config.get("constraint", {})

        # 安全地解析映射文件路径
        raw_attributes_file = None
        enriched_constraints_file = None

        try:
            raw_attr_config = file_paths.get("raw_attributes")
            enriched_constraints_config = file_paths.get("enriched_constraints")

            if raw_attr_config:
                raw_attributes_path = project_root / raw_attr_config if not Path(
                    raw_attr_config).is_absolute() else Path(raw_attr_config)
                if raw_attributes_path.exists():
                    raw_attributes_file = str(raw_attributes_path)
                    print(f"✅ 找到原始属性映射文件: {raw_attributes_path}")
                else:
                    print(f"⚠️  原始属性映射文件未找到: {raw_attributes_path}")

            if enriched_constraints_config:
                enriched_constraints_path = project_root / enriched_constraints_config if not Path(
                    enriched_constraints_config).is_absolute() else Path(enriched_constraints_config)
                if enriched_constraints_path.exists():
                    enriched_constraints_file = str(enriched_constraints_path)
                    print(f"✅ 找到增强约束文件: {enriched_constraints_path}")
                else:
                    print(f"⚠️  增强约束文件未找到: {enriched_constraints_path}")

        except Exception as e:
            print(f"⚠️  映射文件路径解析错误: {e}")

        # 初始化结构验证器
        if validator_config.get("structure", {}).get("enabled", True):
            try:
                from ..structure.xsd_validator import XSDValidator
                xsd_path = file_paths.get("xsd_schema")
                if xsd_path:
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

        # 🔧 增强的语义验证器初始化 - 支持细粒度控制
        if semantic_config.get("enabled", True):
            try:
                from ..semantic.shacl_validator import SHACLValidator
                shacl_path = file_paths.get("shacl_shapes")
                if shacl_path:
                    shacl_full_path = project_root / shacl_path if not Path(shacl_path).is_absolute() else Path(
                        shacl_path)
                    if shacl_full_path.exists():
                        print(f"📄 加载SHACL Shapes: {shacl_full_path}")

                        # 🔧 显示语义验证配置信息
                        validation_scope = semantic_config.get('validation_scope', {})
                        print(f"🔧 SHACL验证配置:")

                        # 检查验证范围
                        struct_validation = validation_scope.get('structural_validation', True)
                        semantic_validation = validation_scope.get('semantic_validation', True)
                        print(f"   结构验证: {'启用' if struct_validation else '禁用'}")
                        print(f"   语义验证: {'启用' if semantic_validation else '禁用'}")

                        # 显示语义约束类型配置
                        semantic_types = validation_scope.get('semantic_types', {})
                        if semantic_types:
                            enabled_types = [k for k, v in semantic_types.items() if v]
                            disabled_types = [k for k, v in semantic_types.items() if not v]
                            if enabled_types:
                                print(f"   启用类型: {', '.join(enabled_types)}")
                            if disabled_types:
                                print(f"   禁用类型: {', '.join(disabled_types)}")

                        # 显示验证策略
                        strategy = semantic_config.get('validation_strategy', {})
                        validation_mode = strategy.get('mode', 'hybrid')
                        print(f"   验证模式: {validation_mode}")

                        # 显示严重性过滤
                        severity_filter = strategy.get('severity_filter', {})
                        if severity_filter:
                            print(f"   严重性过滤:")
                            for category, levels in severity_filter.items():
                                print(f"     {category}: {', '.join(levels)}")

                        # 安全地初始化SHACL验证器
                        if raw_attributes_file and Path(raw_attributes_file).exists():
                            print(f"📄 启用SHACL映射功能: {raw_attributes_file}")
                            try:
                                self.validators['semantic'] = SHACLValidator(
                                    str(shacl_full_path),
                                    raw_attributes_file,
                                    enriched_constraints_file,
                                    semantic_config  # 🔧 传递语义配置
                                )
                                print("✅ SHACL语义验证器初始化成功 (增强模式)")
                            except Exception as init_error:
                                print(f"⚠️  增强模式初始化失败: {init_error}")
                                print("🔄 回退到标准模式...")
                                try:
                                    self.validators['semantic'] = SHACLValidator(
                                        str(shacl_full_path),
                                        None, None,
                                        semantic_config  # 🔧 仍然传递语义配置
                                    )
                                    print("✅ SHACL语义验证器初始化成功 (标准模式)")
                                except Exception as fallback_error:
                                    print(f"❌ 标准模式也失败: {fallback_error}")
                                    raise
                        else:
                            print("📝 使用标准模式")
                            self.validators['semantic'] = SHACLValidator(
                                str(shacl_full_path),
                                None, None,
                                semantic_config  # 🔧 传递语义配置
                            )
                            print("✅ SHACL语义验证器初始化成功 (标准模式)")
                    else:
                        print(f"⚠️  SHACL文件未找到: {shacl_full_path}")
                else:
                    print("⚠️  配置中未指定SHACL Shapes路径")
            except Exception as e:
                print(f"⚠️  SHACL验证器初始化失败: {e}")
                import traceback
                traceback.print_exc()

        # ⬇️ =================== SMT 验证器修复 =================== ⬇️
        # 🔧 增强的约束验证器初始化 - 支持细粒度控制
        if constraint_config.get("enabled", True):
            try:
                from ..constraints.smt_validator import SMTValidator
                smt_path = file_paths.get("smt_template")

                # ⬇️ 关键修复：从配置中读取 smt_mapping 路径
                mapping_path = file_paths.get("smt_mapping")

                # ⬇️ 关键修复：初始化路径变量
                smt_full_path = None
                mapping_full_path = None

                if smt_path:
                    smt_full_path = project_root / smt_path if not Path(smt_path).is_absolute() else Path(smt_path)

                # ⬇️ 关键修复：解析映射的完整路径
                if mapping_path:
                    mapping_full_path = project_root / mapping_path if not Path(mapping_path).is_absolute() else Path(
                        mapping_path)

                if smt_full_path and smt_full_path.exists():
                    print(f"📄 加载SMT Template: {smt_full_path}")

                    # ⬇️ 关键修复：检查映射路径并准备传递
                    mapping_to_pass = None
                    if mapping_full_path and mapping_full_path.exists():
                        print(f"📄 启用SMT约束映射: {mapping_full_path}")
                        mapping_to_pass = str(mapping_full_path)
                    elif mapping_full_path:
                        # 路径在配置中但文件不存在
                        print(f"⚠️  SMT 映射文件未找到: {mapping_full_path}")
                        print(f"     请检查 'main_config.yaml' 中的 'smt_mapping' 路径。")
                    else:
                        # 路径未在配置中
                        print(f"⚠️  配置中未指定 SMT 映射 (smt_mapping)")
                        print(f"     将不加载 SMT 映射，这*将*导致 '0 data points' 错误。")

                    # 🔧 显示约束验证配置信息
                    validation_scope = constraint_config.get('validation_scope', {})
                    print(f"🔧 SMT约束验证配置:")

                    # 检查验证范围
                    struct_enabled = validation_scope.get('structural_constraints', True)
                    semantic_enabled = validation_scope.get('semantic_constraints', True)
                    print(f"   结构约束: {'启用' if struct_enabled else '禁用'}")
                    print(f"   语义约束: {'启用' if semantic_enabled else '禁用'}")

                    # 显示语义约束类型配置
                    semantic_types = validation_scope.get('semantic_types', {})
                    if semantic_types:
                        enabled_types = [k for k, v in semantic_types.items() if v]
                        disabled_types = [k for k, v in semantic_types.items() if not v]
                        if enabled_types:
                            print(f"   启用类型: {', '.join(enabled_types)}")
                        if disabled_types:
                            print(f"   禁用类型: {', '.join(disabled_types)}")

                    # 显示验证策略
                    strategy = constraint_config.get('validation_strategy', {})
                    validation_mode = strategy.get('mode', 'hybrid')
                    print(f"   验证模式: {validation_mode}")

                    if strategy.get('fail_fast', True):
                        print(f"   失败策略: 快速失败")
                    if strategy.get('continue_on_semantic_fail', True):
                        print(f"   语义失败: 继续验证")

                    # 安全地初始化SMT验证器
                    # (我们不再区分“增强模式”和“标准模式”的初始化，
                    # 而是统一将解析后的 mapping_to_pass 传递下去)

                    print("📝 使用标准模式 (已配置映射)")
                    try:
                        self.validators['constraint'] = SMTValidator(
                            str(smt_full_path),
                            # ⬇️ 关键修复：将解析后的路径传递给构造函数
                            mapping_file=mapping_to_pass
                            # constraint_config  # 🔧 传递约束配置
                        )
                        print("✅ SMT约束验证器初始化成功")
                    except Exception as fallback_error:
                        print(f"❌ SMT约束验证器初始化失败: {fallback_error}")
                        raise

                else:
                    if smt_path:
                        print(f"⚠️  SMT文件未找到: {smt_full_path}")
                    else:
                        print("⚠️  配置中未指定SMT Template路径")
            except Exception as e:
                print(f"⚠️  SMT验证器初始化失败: {e}")
                import traceback
                traceback.print_exc()


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


    def generate_semantic_summary_report(self, validation_results: Dict) -> str:
        """🔧 新增：生成语义验证专用摘要报告"""

        semantic_result = validation_results["stages"].get("semantic", {}).get("result", {})
        if not semantic_result:
            return "语义验证未执行或失败"

        lines = []
        lines.append("📊 SHACL语义验证摘要报告")
        lines.append("=" * 50)

        validation_mode = semantic_result.get("validation_mode", "hybrid")
        lines.append(f"验证模式: {validation_mode}")

        structural_valid = semantic_result.get("structural_valid", False)
        semantic_compliance = semantic_result.get("semantic_compliance", "UNKNOWN")
        violation_count = semantic_result.get("violation_count", 0)

        lines.append(f"结构有效性: {'✅ 通过' if structural_valid else '❌ 失败'}")
        lines.append(f"语义合规性: {semantic_compliance}")
        lines.append(f"违规总数: {violation_count}")
        lines.append("")

        # 详细的违规类型分解
        violation_breakdown = semantic_result.get("violation_breakdown", {})
        if violation_breakdown:

            # 结构验证摘要
            structural = violation_breakdown.get("structural", {})
            if structural:
                lines.append("🔧 结构验证:")
                for constraint_type, stats in structural.items():
                    if isinstance(stats, dict) and stats.get("total", 0) > 0:
                        total_count = stats.get("total", 0)
                        violations = stats.get("violations", 0)
                        status = "✅" if violations == 0 else f"❌({violations})"
                        lines.append(f"  {constraint_type}: {total_count} 个 {status}")
                lines.append("")

            # 语义验证摘要
            semantic = violation_breakdown.get("semantic", {})
            if semantic:
                lines.append("💡 语义验证:")

                constraint_type_names = {
                    "existence": "存在性",
                    "value_restriction": "值限制",
                    "cardinality": "基数",
                    "dependency": "依赖",
                    "mutual_exclusion": "互斥",
                    "format": "格式",
                    "range": "范围",
                    "behavioral": "行为",
                    "other": "其他"
                }

                for constraint_type, stats in semantic.items():
                    if isinstance(stats, dict) and stats.get("total", 0) > 0:
                        type_name = constraint_type_names.get(constraint_type, constraint_type)
                        total_count = stats.get("total", 0)
                        violations = stats.get("violations", 0)
                        warnings = stats.get("warnings", 0)
                        info = stats.get("info", 0)
                        enabled = stats.get("enabled", True)

                        # 状态显示
                        if violations > 0:
                            status = f"❌({violations})"
                        elif warnings > 0:
                            status = f"⚠️({warnings})"
                        elif info > 0:
                            status = f"ℹ️({info})"
                        else:
                            status = "✅"

                        enable_status = "" if enabled else " [禁用]"
                        lines.append(f"  {type_name}: {total_count} 个 {status}{enable_status}")
                lines.append("")

        # 配置信息
        validation_config = semantic_result.get("validation_config", {})
        if validation_config:
            lines.append("⚙️  验证配置:")
            lines.append(f"  结构验证: {'启用' if validation_config.get('structural_enabled', True) else '禁用'}")
            lines.append(f"  语义验证: {'启用' if validation_config.get('semantic_enabled', True) else '禁用'}")
            lines.append(f"  验证模式: {validation_config.get('mode', 'hybrid')}")

            semantic_types_config = validation_config.get('semantic_types_config', {})
            if semantic_types_config:
                enabled_count = sum(1 for v in semantic_types_config.values() if v)
                total_count = len(semantic_types_config)
                lines.append(f"  启用类型: {enabled_count}/{total_count}")

            severity_filter = validation_config.get('severity_filter', {})
            if severity_filter:
                lines.append("  严重性过滤:")
                for category, levels in severity_filter.items():
                    lines.append(f"    {category}: {', '.join(levels)}")

        # 映射统计
        mapping_stats = semantic_result.get("mapping_stats", {})
        if mapping_stats.get("mapping_enabled", False):
            lines.append("")
            lines.append("🔧 映射功能统计:")
            lines.append(f"  XML->属性映射: {mapping_stats.get('xml_to_attr_mappings', 0)}")
            lines.append(f"  Wrapper映射: {mapping_stats.get('wrapper_mappings', 0)}")
            lines.append(f"  文本内容映射: {mapping_stats.get('text_content_mappings', 0)}")

        return "\n".join(lines)

    def generate_validation_comparison_report(self, validation_results: Dict) -> str:
        """🔧 新增：生成SHACL与SMT验证对比报告"""

        semantic_result = validation_results["stages"].get("semantic", {}).get("result", {})
        constraint_result = validation_results["stages"].get("constraint", {}).get("result", {})

        lines = []
        lines.append("📊 语义验证对比报告 (SHACL vs SMT)")
        lines.append("=" * 60)

        # 总体对比
        if semantic_result and constraint_result:
            semantic_valid = semantic_result.get("valid", False)
            constraint_valid = constraint_result.get("valid", False)

            lines.append("📋 总体对比:")
            lines.append(f"  SHACL验证: {'✅ 通过' if semantic_valid else '❌ 失败'}")
            lines.append(f"  SMT验证:  {'✅ 通过' if constraint_valid else '❌ 失败'}")
            lines.append("")

            # 约束类型对比
            semantic_breakdown = semantic_result.get("violation_breakdown", {}).get("semantic", {})
            constraint_breakdown = constraint_result.get("constraint_breakdown", {}).get("semantic", {})

            if semantic_breakdown or constraint_breakdown:
                lines.append("💡 语义约束类型对比:")

                all_types = set(semantic_breakdown.keys()) | set(constraint_breakdown.keys())
                for constraint_type in sorted(all_types):
                    shacl_stats = semantic_breakdown.get(constraint_type, {})
                    smt_stats = constraint_breakdown.get(constraint_type, {})

                    shacl_total = shacl_stats.get("total", 0)
                    smt_total = smt_stats.get("total", 0)

                    if shacl_total > 0 or smt_total > 0:
                        shacl_issues = shacl_stats.get("violations", 0) + shacl_stats.get("warnings", 0)
                        smt_issues = smt_stats.get("violations", 0) + smt_stats.get("warnings", 0)

                        lines.append(f"  {constraint_type}:")
                        lines.append(f"    SHACL: {shacl_total} 个约束, {shacl_issues} 个问题")
                        lines.append(f"    SMT:   {smt_total} 个约束, {smt_issues} 个问题")
                lines.append("")

            # 配置对比
            semantic_config = semantic_result.get("validation_config", {})
            constraint_config = constraint_result.get("constraint_breakdown", {}).get("configuration", {})

            lines.append("⚙️  配置对比:")
            lines.append(f"  SHACL模式: {semantic_config.get('mode', 'unknown')}")
            lines.append(f"  SMT模式:  {constraint_result.get('validation_mode', 'unknown')}")

            # 性能对比
            semantic_time = semantic_result.get("execution_time", 0)
            constraint_time = constraint_result.get("execution_time", 0)

            if semantic_time > 0 or constraint_time > 0:
                lines.append("")
                lines.append("⏱️  性能对比:")
                lines.append(f"  SHACL执行时间: {semantic_time:.3f}s")
                lines.append(f"  SMT执行时间:  {constraint_time:.3f}s")

        elif semantic_result:
            lines.append("📋 仅执行了SHACL验证")
            lines.append(f"  结果: {'✅ 通过' if semantic_result.get('valid', False) else '❌ 失败'}")

        elif constraint_result:
            lines.append("📋 仅执行了SMT验证")
            lines.append(f"  结果: {'✅ 通过' if constraint_result.get('valid', False) else '❌ 失败'}")

        else:
            lines.append("❌ 未执行语义验证或约束验证")

        return "\n".join(lines)

    def generate_constraint_summary_report(self, validation_results: Dict) -> str:
        """🔧 新增：生成约束验证专用摘要报告"""

        constraint_result = validation_results["stages"].get("constraint", {}).get("result", {})
        if not constraint_result:
            return "约束验证未执行或失败"

        lines = []
        lines.append("📊 约束验证摘要报告")
        lines.append("=" * 50)

        validation_mode = constraint_result.get("validation_mode", "hybrid")
        lines.append(f"验证模式: {validation_mode}")

        satisfied = constraint_result.get("satisfied_count", 0)
        total = constraint_result.get("constraint_count", 0)
        satisfaction_rate = constraint_result.get("satisfaction_rate", 0)

        lines.append(f"约束满足: {satisfied}/{total} ({satisfaction_rate:.1%})")
        lines.append("")

        # 详细的约束类型分解
        breakdown = constraint_result.get("constraint_breakdown", {})
        if breakdown:

            # 结构约束摘要
            structural = breakdown.get("structural", {})
            if structural:
                lines.append("🔧 结构约束:")
                for constraint_type, stats in structural.items():
                    if isinstance(stats, dict) and stats.get("total", 0) > 0:
                        total_count = stats.get("total", 0)
                        satisfied_count = stats.get("satisfied", 0)
                        violations = stats.get("violations", 0)
                        status = "✅" if violations == 0 else f"❌({violations})"
                        lines.append(f"  {constraint_type}: {satisfied_count}/{total_count} {status}")
                lines.append("")

            # 语义约束摘要
            semantic = breakdown.get("semantic", {})
            if semantic:
                lines.append("💡 语义约束:")

                constraint_type_names = {
                    "existence": "存在性",
                    "value_restriction": "值限制",
                    "cardinality": "基数",
                    "dependency": "依赖",
                    "mutual_exclusion": "互斥",
                    "format": "格式",
                    "range": "范围",
                    "behavioral": "行为",
                    "other": "其他"
                }

                for constraint_type, stats in semantic.items():
                    if isinstance(stats, dict) and stats.get("total", 0) > 0:
                        type_name = constraint_type_names.get(constraint_type, constraint_type)
                        total_count = stats.get("total", 0)
                        satisfied_count = stats.get("satisfied", 0)
                        warnings = stats.get("warnings", 0)
                        enabled = stats.get("enabled", True)

                        status = "✅" if warnings == 0 else f"⚠️({warnings})"
                        enable_status = "" if enabled else " [禁用]"
                        lines.append(f"  {type_name}: {satisfied_count}/{total_count} {status}{enable_status}")
                lines.append("")

        # 配置信息
        config = breakdown.get("configuration", {}) if breakdown else {}
        if config:
            lines.append("⚙️  配置状态:")
            lines.append(f"  结构约束: {'启用' if config.get('structural_enabled', True) else '禁用'}")
            lines.append(f"  语义约束: {'启用' if config.get('semantic_enabled', True) else '禁用'}")
            lines.append(f"  快速失败: {'是' if config.get('fail_fast', True) else '否'}")

        return "\n".join(lines)



    def _safe_int_conversion(self, value: any, default: int = 0) -> int:
        """🔧 安全的整数转换方法"""
        try:
            if value is None:
                return default

            # 如果是字典或其他复杂类型，返回默认值
            if isinstance(value, (dict, list, tuple)):
                return default

            # 字符串转换
            if isinstance(value, str):
                # 提取数字
                import re
                numbers = re.findall(r'-?\d+', value)
                if numbers:
                    return int(numbers[0])
                return default

            # 直接转换
            return int(value)

        except (ValueError, TypeError, AttributeError):
            return default

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