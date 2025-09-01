"""core/round2_generator.py - 简化的Round 2生成器

移除了过度设计的函数调用，专注于结构化输出
在生成前一次性准备所有信息，让LLM专注于内容生成
"""
import json
import time
import uuid as uuid_module
from typing import Dict, List, Any, Optional, Tuple
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

from ..config import CONFIG
from ..llm.gemini_client import GeminiClient
from ..llm.prompt_templates import template_manager
from ..knowledge.dynamic_query_engine import query_engine
from ..knowledge.constraint_engine import constraint_engine
from ..utils.serializers import ArchitectureDesign, generate_uuid
from ..utils.exceptions import ValidationError


class Round2Generator:
    """Round 2详细生成器 - 简化版"""

    def __init__(self):
        """初始化Round 2生成器"""
        self.gemini_client = GeminiClient()
        self.query_engine = query_engine
        self.constraint_engine = constraint_engine

        if CONFIG.debug_mode:
            print("[DEBUG] Round2生成器初始化（简化版：无函数调用）")

    def generate_arxml(
        self,
        architecture_design: ArchitectureDesign,
        memory_context: str = "",
        custom_requirements: Dict[str, Any] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """生成详细的ARXML内容 - 简化版"""

        try:
            component_plans = architecture_design.component_plan
            if not component_plans:
                raise ValidationError("架构设计中没有组件计划")

            component_count = len(component_plans)

            if CONFIG.debug_mode:
                print(f"[DEBUG] 开始Round2生成: {component_count}个组件")
                print(f"[DEBUG] 单批阈值: {CONFIG.generation.single_batch_threshold}")

            # 优先尝试单批生成
            if component_count <= CONFIG.generation.single_batch_threshold:
                return self._generate_unified_batch(
                    architecture_design, memory_context, custom_requirements
                )
            else:
                # 仅在超大规模时才考虑分批（>25个组件）
                return self._generate_intelligent_batches(
                    architecture_design, memory_context, custom_requirements
                )

        except Exception as e:
            raise ValidationError(f"ARXML生成失败: {str(e)}")

    def _generate_unified_batch(
        self,
        architecture_design: ArchitectureDesign,
        memory_context: str = "",
        custom_requirements: Dict[str, Any] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """统一批次生成 - 简化版，无函数调用"""

        start_time = time.time()
        component_plans = architecture_design.component_plan
        interface_plans = architecture_design.interface_plan

        if CONFIG.debug_mode:
            print(f"[DEBUG] 统一批次生成: {len(component_plans)}个组件, {len(interface_plans)}个接口")
            print(f"[DEBUG] 使用纯结构化输出模式（无函数调用）")

        # ========== Phase 1: 准备阶段（所有动态信息一次性获取）==========

        # 1. 生成深度Schema
        schema_depth = CONFIG.generation.max_schema_injection_depth
        arxml_schema = self._generate_deep_schema(component_plans, schema_depth)

        # 2. 批量生成UUID（预生成所有需要的UUID）
        uuid_mapping = self._batch_generate_uuids(component_plans, interface_plans)

        # 3. 查询完整约束信息
        constraints = self._query_comprehensive_constraints(component_plans, interface_plans)

        # 4. 准备标准类型引用
        standard_types = self._prepare_standard_types()

        # ========== Phase 2: 生成阶段（纯LLM结构化输出）==========

        # 构建增强的提示词（包含所有预生成的信息）
        prompt = self._build_enhanced_prompt(
            architecture_design,
            constraints,
            memory_context,
            custom_requirements,
            schema_depth,
            uuid_mapping,
            standard_types
        )

        if CONFIG.debug_mode:
            print(f"[DEBUG] 提示词长度: {len(prompt)} 字符")
            print(f"[DEBUG] Schema深度: {schema_depth}")
            print(f"[DEBUG] 预生成UUID数: {len(uuid_mapping)}")
            print(f"[DEBUG] 约束规则数: {len(constraints)}")

        # 调用LLM生成（纯结构化输出，无函数调用）
        response_data, input_tokens, output_tokens, total_tokens = \
            self.gemini_client.generate_with_schema(
                prompt=prompt,
                schema=arxml_schema,
                temperature=0.7,
                max_retries=3
            )

        # ========== Phase 3: 后处理阶段 ==========

        # 1. 验证生成的内容
        validation_results = self._validate_generated_content(response_data, constraints)

        # 2. 确保所有引用都是直接路径（不需要解析语义占位符）
        processed_data = self._ensure_direct_references(response_data)

        # 3. 转换为ARXML
        arxml_content = self._convert_to_arxml(processed_data, architecture_design)

        generation_time = time.time() - start_time

        # 详细统计信息
        stats = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "component_count": len(component_plans),
            "interface_count": len(interface_plans),
            "generation_mode": "unified_batch",
            "schema_depth": schema_depth,
            "schema_properties": len(arxml_schema.get("properties", {})),
            "constraints_applied": len(constraints),
            "uuids_generated": len(uuid_mapping),
            "validation_passed": validation_results["passed"],
            "validation_errors": validation_results["errors"],
            "generation_time": generation_time,
            "tokens_per_component": total_tokens / max(len(component_plans), 1),
            "performance_metrics": {
                "time_per_component": generation_time / max(len(component_plans), 1),
                "schema_complexity": self._calculate_schema_complexity(arxml_schema),
                "output_efficiency": output_tokens / max(len(str(response_data)), 1)
            }
        }

        if CONFIG.debug_mode:
            print(f"[DEBUG] 生成完成: {generation_time:.2f}秒")
            print(f"[DEBUG] Token效率: {stats['tokens_per_component']:.0f} tokens/组件")
            print(f"[DEBUG] 验证结果: {'通过' if validation_results['passed'] else '有错误'}")

        return arxml_content, stats

    def _batch_generate_uuids(
        self,
        component_plans: List[Dict[str, Any]],
        interface_plans: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """批量预生成UUID"""

        uuid_mapping = {}

        # 为每个组件生成UUID
        for comp in component_plans:
            comp_name = comp.get("name", "")
            if comp_name:
                uuid_mapping[f"component_{comp_name}"] = str(uuid_module.uuid4())

                # 为组件的端口预生成UUID
                if comp.get("element_design", {}).get("ports", {}).get("needed"):
                    uuid_mapping[f"port_p_{comp_name}"] = str(uuid_module.uuid4())
                    uuid_mapping[f"port_r_{comp_name}"] = str(uuid_module.uuid4())

                # 为内部行为预生成UUID
                if comp.get("element_design", {}).get("internal_behaviors", {}).get("needed"):
                    uuid_mapping[f"behavior_{comp_name}"] = str(uuid_module.uuid4())
                    # 为runnables预生成
                    for runnable in comp.get("element_design", {}).get("internal_behaviors", {}).get("runnables", []):
                        uuid_mapping[f"runnable_{comp_name}_{runnable}"] = str(uuid_module.uuid4())

        # 为每个接口生成UUID
        for intf in interface_plans:
            intf_name = intf.get("name", "")
            if intf_name:
                uuid_mapping[f"interface_{intf_name}"] = str(uuid_module.uuid4())

        if CONFIG.debug_mode:
            print(f"[DEBUG] 预生成 {len(uuid_mapping)} 个UUID")

        return uuid_mapping

    def _prepare_standard_types(self) -> Dict[str, Any]:
        """准备标准类型引用信息"""

        # 从标准类型库获取常用类型
        standard_types = {
            "base_types": [
                "/AUTOSAR_Platform/ImplementationDataTypes/boolean",
                "/AUTOSAR_Platform/ImplementationDataTypes/uint8",
                "/AUTOSAR_Platform/ImplementationDataTypes/uint16",
                "/AUTOSAR_Platform/ImplementationDataTypes/uint32",
                "/AUTOSAR_Platform/ImplementationDataTypes/sint8",
                "/AUTOSAR_Platform/ImplementationDataTypes/sint16",
                "/AUTOSAR_Platform/ImplementationDataTypes/sint32",
                "/AUTOSAR_Platform/ImplementationDataTypes/float32",
                "/AUTOSAR_Platform/ImplementationDataTypes/float64"
            ],
            "physical_types": [
                "/AUTOSAR_Platform/CompuMethods/Temperature_degC",
                "/AUTOSAR_Platform/CompuMethods/Voltage_V",
                "/AUTOSAR_Platform/CompuMethods/Current_A",
                "/AUTOSAR_Platform/CompuMethods/Speed_kmh",
                "/AUTOSAR_Platform/CompuMethods/Pressure_kPa"
            ]
        }

        return standard_types

    def _build_enhanced_prompt(
        self,
        architecture_design: ArchitectureDesign,
        constraints: List[str],
        memory_context: str,
        custom_requirements: Dict[str, Any],
        schema_depth: int,
        uuid_mapping: Dict[str, str],
        standard_types: Dict[str, Any]
    ) -> str:
        """构建增强的提示词（包含所有预生成信息）"""

        # 使用模板生成基础提示词
        prompt = template_manager.get_round2_prompt(
            architecture_design=architecture_design.__dict__,
            constraints=constraints,
            schema_depth=schema_depth
        )

        # 添加记忆上下文
        if memory_context:
            prompt += f"\n\n## 对话上下文\n{memory_context}"

        # 添加自定义要求
        if custom_requirements:
            prompt += f"\n\n## 特殊要求\n"
            for key, value in custom_requirements.items():
                prompt += f"- {key}: {value}\n"

        # 添加预生成的UUID映射
        prompt += self._format_uuid_mapping(uuid_mapping)

        # 添加标准类型引用
        prompt += self._format_standard_types(standard_types)

        # 添加直接引用指导
        prompt += self._add_direct_reference_guidance(architecture_design)

        return prompt

    def _format_uuid_mapping(self, uuid_mapping: Dict[str, str]) -> str:
        """格式化UUID映射为提示词"""

        prompt = "\n\n## 预生成的UUID（必须使用这些UUID）\n"
        prompt += "以下是每个元素对应的UUID，请严格使用：\n\n"

        for key, uuid_val in uuid_mapping.items():
            if key.startswith("component_"):
                name = key.replace("component_", "")
                prompt += f"- 组件 {name}: {uuid_val}\n"
            elif key.startswith("interface_"):
                name = key.replace("interface_", "")
                prompt += f"- 接口 {name}: {uuid_val}\n"
            elif key.startswith("port_"):
                parts = key.split("_", 2)
                prompt += f"- 端口 {parts[2]}_{parts[1]}: {uuid_val}\n"
            elif key.startswith("behavior_"):
                name = key.replace("behavior_", "")
                prompt += f"- 内部行为 {name}: {uuid_val}\n"
            elif key.startswith("runnable_"):
                parts = key.replace("runnable_", "").split("_", 1)
                prompt += f"- Runnable {parts[1]} (组件{parts[0]}): {uuid_val}\n"

        return prompt

    def _format_standard_types(self, standard_types: Dict[str, Any]) -> str:
        """格式化标准类型引用"""

        prompt = "\n\n## 标准数据类型引用\n"
        prompt += "请使用以下标准类型，不要创建自定义类型：\n\n"

        prompt += "### 基础数据类型\n"
        for type_ref in standard_types["base_types"]:
            prompt += f"- {type_ref}\n"

        prompt += "\n### 物理量类型\n"
        for type_ref in standard_types["physical_types"]:
            prompt += f"- {type_ref}\n"

        return prompt

    def _add_direct_reference_guidance(self, architecture_design: ArchitectureDesign) -> str:
        """添加直接引用指导"""

        prompt = "\n\n## 引用路径规范\n"
        prompt += "所有引用必须使用完整的直接路径，格式如下：\n\n"

        # 基于实际架构生成具体示例
        if architecture_design.component_plan:
            prompt += "### 本系统的引用路径示例：\n"
            for comp in architecture_design.component_plan[:3]:  # 前3个组件作为示例
                comp_name = comp.get("name", "Component")
                prompt += f"- 组件: /Components/{comp_name}\n"
                prompt += f"- 端口: /Components/{comp_name}/Ports/PortName\n"
                prompt += f"- Runnable: /Components/{comp_name}/InternalBehavior/Runnables/RunnableName\n"
                prompt += f"- 事件: /Components/{comp_name}/InternalBehavior/Events/EventName\n\n"

        if architecture_design.interface_plan:
            prompt += "### 接口引用示例：\n"
            for intf in architecture_design.interface_plan[:3]:
                intf_name = intf.get("name", "Interface")
                prompt += f"- /Interfaces/{intf_name}\n"

        prompt += "\n**重要**：不要使用语义描述，必须使用完整路径！\n"

        return prompt

    def _validate_generated_content(
        self,
        response_data: Dict[str, Any],
        constraints: List[str]
    ) -> Dict[str, Any]:
        """验证生成的内容（后处理）"""

        validation_results = {
            "passed": True,
            "errors": [],
            "warnings": []
        }

        # 遍历所有组件进行验证
        for comp_name, comp_data in response_data.items():
            if isinstance(comp_data, dict) and not comp_name.startswith("_"):
                # 验证SHORT-NAME
                if "SHORT-NAME" not in comp_data:
                    validation_results["errors"].append(f"组件{comp_name}缺少SHORT-NAME")
                    validation_results["passed"] = False

                # 验证UUID格式
                if "@UUID" in comp_data:
                    uuid_val = comp_data["@UUID"]
                    import re
                    if not re.match(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$', uuid_val):
                        validation_results["errors"].append(f"组件{comp_name}的UUID格式无效")
                        validation_results["passed"] = False

                # 验证端口引用
                if "PORTS" in comp_data:
                    self._validate_port_references(comp_data["PORTS"], comp_name, validation_results)

                # 验证内部行为
                if "INTERNAL-BEHAVIORS" in comp_data:
                    self._validate_internal_behaviors(comp_data["INTERNAL-BEHAVIORS"], comp_name, validation_results)

        return validation_results

    def _validate_port_references(self, ports_data: Dict[str, Any], comp_name: str, results: Dict[str, Any]):
        """验证端口引用"""

        for port_type in ["P-PORT-PROTOTYPE", "R-PORT-PROTOTYPE"]:
            if port_type in ports_data:
                for port in ports_data[port_type]:
                    if isinstance(port, dict):
                        # 检查接口引用
                        ref_key = "PROVIDED-INTERFACE-TREF" if port_type == "P-PORT-PROTOTYPE" else "REQUIRED-INTERFACE-TREF"
                        if ref_key in port:
                            ref_val = port[ref_key]
                            if not ref_val.startswith("/"):
                                results["warnings"].append(f"{comp_name}的端口引用应以/开始: {ref_val}")

    def _validate_internal_behaviors(self, behaviors_data: Dict[str, Any], comp_name: str, results: Dict[str, Any]):
        """验证内部行为"""

        if "SWC-INTERNAL-BEHAVIOR" in behaviors_data:
            behavior = behaviors_data["SWC-INTERNAL-BEHAVIOR"]

            # 验证事件引用
            if "EVENTS" in behavior:
                for event_type, events in behavior["EVENTS"].items():
                    if isinstance(events, list):
                        for event in events:
                            if isinstance(event, dict) and "START-ON-EVENT-REF" in event:
                                ref = event["START-ON-EVENT-REF"]
                                if not ref.startswith("/"):
                                    results["warnings"].append(f"{comp_name}的事件引用应以/开始: {ref}")

    def _ensure_direct_references(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """确保所有引用都是直接路径格式"""

        processed_data = response_data.copy()

        def normalize_references(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if isinstance(value, str) and any(ref in key.upper() for ref in ["REF", "TREF"]):
                        # 确保引用以/开始
                        if value and not value.startswith("/"):
                            obj[key] = "/" + value
                    elif isinstance(value, (dict, list)):
                        normalize_references(value)
            elif isinstance(obj, list):
                for item in obj:
                    normalize_references(item)

        normalize_references(processed_data)

        return processed_data

    def _generate_deep_schema(
        self,
        component_plans: List[Dict[str, Any]],
        depth: int = 15
    ) -> Dict[str, Any]:
        """生成深度Schema - 保持原有实现"""

        if CONFIG.debug_mode:
            print(f"[DEBUG] 生成深度Schema: depth={depth}")
            self.query_engine.clear_cache("request")

        # 利用query_engine生成深度Schema
        schema = self.query_engine.generate_multi_component_schema(
            component_plans,
            max_depth=depth
        )

        if not schema or not schema.get("properties"):
            raise ValidationError(f"无法为组件类型生成有效Schema")

        # 增强Schema以支持直接引用
        schema = self._enhance_schema_for_direct_references(schema)

        if CONFIG.debug_mode:
            properties_count = len(schema.get("properties", {}))
            print(f"[DEBUG] Schema生成成功: {properties_count}个组件定义")

        return schema

    def _enhance_schema_for_direct_references(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """增强Schema以支持直接引用"""

        def enhance_properties(properties: Dict[str, Any]) -> Dict[str, Any]:
            enhanced = {}

            for key, value in properties.items():
                if isinstance(value, dict):
                    # 引用字段支持完整路径
                    if any(ref_key in key.upper() for ref_key in ["REF", "REFERENCE", "TREF", "IREF"]):
                        enhanced[key] = {
                            "type": "string",
                            "description": f"{value.get('description', '')} (完整路径格式: /Category/Element/SubElement)",
                            "pattern": "^(/[A-Za-z][A-Za-z0-9_-]*)+"  # 路径格式验证
                        }
                    elif value.get("type") == "object" and "properties" in value:
                        # 递归处理嵌套对象
                        enhanced[key] = {
                            **value,
                            "properties": enhance_properties(value["properties"])
                        }
                    else:
                        enhanced[key] = value
                else:
                    enhanced[key] = value

            return enhanced

        if schema.get("type") == "object" and "properties" in schema:
            schema["properties"] = enhance_properties(schema["properties"])

        return schema

    def _query_comprehensive_constraints(
        self,
        component_plans: List[Dict[str, Any]],
        interface_plans: List[Dict[str, Any]]
    ) -> List[str]:
        """查询完整的约束规则 - 保持原有实现"""

        constraints = []

        # 组件类型约束
        component_types = set(comp.get("type", "") for comp in component_plans)
        for comp_type in component_types:
            if comp_type:
                type_constraints = self.query_engine.query_constraints_for_elements([comp_type])
                constraints.extend(type_constraints)

        # 接口类型约束
        interface_types = set(intf.get("type", "") for intf in interface_plans)
        for intf_type in interface_types:
            if intf_type:
                intf_constraints = self.query_engine.query_constraints_for_elements([intf_type])
                constraints.extend(intf_constraints)

        # 通用AUTOSAR约束
        general_constraints = [
            "所有UUID必须全局唯一",
            "SHORT-NAME必须符合NCName规范",
            "端口名称在组件内必须唯一",
            "事件必须正确引用Runnable",
            "接口引用必须使用完整路径",
            "数据类型必须引用标准类型库"
        ]
        constraints.extend(general_constraints)

        # 去重
        constraints = list(set(constraints))

        if CONFIG.debug_mode:
            print(f"[DEBUG] 查询到{len(constraints)}条约束规则")

        return constraints

    def _convert_to_arxml(
        self,
        json_data: Dict[str, Any],
        architecture_design: ArchitectureDesign
    ) -> str:
        """转换JSON为ARXML格式 - 保持原有实现"""

        # 创建AUTOSAR根元素
        root = Element("AUTOSAR")
        root.set("xmlns", "http://autosar.org/schema/r4.0")
        root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        root.set("xsi:schemaLocation", "http://autosar.org/schema/r4.0 AUTOSAR_4-3-0.xsd")

        # AR-PACKAGES
        ar_packages = SubElement(root, "AR-PACKAGES")

        # Components包
        comp_package = SubElement(ar_packages, "AR-PACKAGE")
        SubElement(comp_package, "SHORT-NAME").text = "Components"
        comp_elements = SubElement(comp_package, "ELEMENTS")

        # Interfaces包
        intf_package = SubElement(ar_packages, "AR-PACKAGE")
        SubElement(intf_package, "SHORT-NAME").text = "Interfaces"
        intf_elements = SubElement(intf_package, "ELEMENTS")

        # 添加所有组件
        for comp_name, comp_data in json_data.items():
            if isinstance(comp_data, dict) and not comp_name.startswith("_"):
                self._add_component_to_xml(comp_elements, comp_name, comp_data)

        # 添加接口（如果在响应中定义）
        if "_interfaces" in json_data:
            for intf_name, intf_data in json_data["_interfaces"].items():
                self._add_interface_to_xml(intf_elements, intf_name, intf_data)

        # 格式化输出
        rough_string = tostring(root, encoding='unicode')
        reparsed = minidom.parseString(rough_string)

        # 优化格式化
        pretty_xml = reparsed.toprettyxml(indent="  ")

        # 移除多余的空行
        lines = [line for line in pretty_xml.split('\n') if line.strip()]
        return '\n'.join(lines)

    def _add_component_to_xml(self, parent: Element, comp_name: str, comp_data: Dict[str, Any]):
        """添加组件到XML"""

        comp_type = comp_data.get("_type", "APPLICATION-SW-COMPONENT-TYPE")
        comp_element = SubElement(parent, comp_type)

        self._dict_to_xml(comp_element, comp_data, skip_keys=["_type"])

    def _add_interface_to_xml(self, parent: Element, intf_name: str, intf_data: Dict[str, Any]):
        """添加接口到XML"""

        intf_type = intf_data.get("_type", "SENDER-RECEIVER-INTERFACE")
        intf_element = SubElement(parent, intf_type)

        self._dict_to_xml(intf_element, intf_data, skip_keys=["_type"])

    def _dict_to_xml(self, parent: Element, data: Dict[str, Any], skip_keys: List[str] = None):
        """递归转换字典到XML"""

        skip_keys = skip_keys or []

        for key, value in data.items():
            if key in skip_keys or key.startswith("_"):
                continue

            if key.startswith("@"):
                # 属性
                parent.set(key[1:], str(value))
            elif key == "#text":
                # 文本内容
                parent.text = str(value)
            elif isinstance(value, dict):
                # 嵌套元素
                child = SubElement(parent, key)
                self._dict_to_xml(child, value)
            elif isinstance(value, list):
                # 列表元素
                for item in value:
                    if isinstance(item, dict):
                        child = SubElement(parent, key)
                        self._dict_to_xml(child, item)
                    else:
                        SubElement(parent, key).text = str(item)
            else:
                # 简单元素
                SubElement(parent, key).text = str(value)

    def _calculate_schema_complexity(self, schema: Dict[str, Any]) -> int:
        """计算Schema复杂度"""

        def count_properties(obj):
            count = 0
            if isinstance(obj, dict):
                count += len(obj.keys())
                for value in obj.values():
                    count += count_properties(value)
            elif isinstance(obj, list):
                for item in obj:
                    count += count_properties(item)
            return count

        return count_properties(schema)

    def _generate_intelligent_batches(
        self,
        architecture_design: ArchitectureDesign,
        memory_context: str = "",
        custom_requirements: Dict[str, Any] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """智能分批生成 - 仅用于超大规模（>25组件）"""

        component_plans = architecture_design.component_plan

        if CONFIG.debug_mode:
            print(f"[DEBUG] 超大规模系统，智能分批: {len(component_plans)}个组件")

        # 基于复杂度智能分组
        batches = self._create_intelligent_batches(component_plans)

        all_components = {}
        total_stats = {
            "total_tokens": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "batch_count": len(batches),
            "component_count": len(component_plans),
            "generation_mode": "intelligent_batch",
            "batch_details": []
        }

        # 生成所有批次
        for batch_idx, batch in enumerate(batches):
            if CONFIG.debug_mode:
                print(f"[DEBUG] 生成批次 {batch_idx + 1}/{len(batches)}: {len(batch)}个组件")

            # 创建批次架构
            batch_architecture = ArchitectureDesign(
                system_analysis=architecture_design.system_analysis,
                component_plan=batch,
                interface_plan=architecture_design.interface_plan,  # 共享接口
                connection_topology=architecture_design.connection_topology,
                architecture_rationale=architecture_design.architecture_rationale
            )

            # 生成批次（使用统一批次方法）
            batch_arxml, batch_stats = self._generate_unified_batch(
                batch_architecture,
                memory_context,
                custom_requirements
            )

            # 解析并合并结果
            batch_components = self._parse_arxml_to_components(batch_arxml)
            all_components.update(batch_components)

            # 累计统计
            total_stats["total_tokens"] += batch_stats["total_tokens"]
            total_stats["input_tokens"] += batch_stats["input_tokens"]
            total_stats["output_tokens"] += batch_stats["output_tokens"]
            total_stats["batch_details"].append(batch_stats)

        # 组装最终ARXML
        final_arxml = self._assemble_components_to_arxml(all_components, architecture_design)

        return final_arxml, total_stats

    def _create_intelligent_batches(
        self,
        component_plans: List[Dict[str, Any]]
    ) -> List[List[Dict[str, Any]]]:
        """创建智能批次 - 基于复杂度"""

        # 计算每个组件的复杂度权重
        weighted_components = []
        for comp in component_plans:
            complexity = comp.get("estimated_complexity", "Medium")
            weight = {"Simple": 1, "Medium": 3, "Complex": 5}.get(complexity, 3)
            weighted_components.append((comp, weight))

        # 按复杂度排序
        weighted_components.sort(key=lambda x: x[1])

        # 智能分批
        batches = []
        current_batch = []
        current_weight = 0
        max_weight = 50  # 每批最大权重

        for comp, weight in weighted_components:
            if current_weight + weight <= max_weight:
                current_batch.append(comp)
                current_weight += weight
            else:
                if current_batch:
                    batches.append(current_batch)
                current_batch = [comp]
                current_weight = weight

        if current_batch:
            batches.append(current_batch)

        return batches

    def _parse_arxml_to_components(self, arxml_content: str) -> Dict[str, Any]:
        """解析ARXML内容为组件字典"""

        # 简化实现 - 实际应该使用XML解析
        components = {}
        # TODO: 实现XML到组件的解析
        return components

    def _assemble_components_to_arxml(
        self,
        components: Dict[str, Any],
        architecture_design: ArchitectureDesign
    ) -> str:
        """组装组件为最终ARXML"""

        return self._convert_to_arxml(components, architecture_design)


# 全局Round2生成器实例
round2_generator = Round2Generator()