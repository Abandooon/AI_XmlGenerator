"""core/round2_generator.py - Round 2详细生成器

支持分批生成、语义占位符处理、引用展开
"""
import json
import uuid
from typing import Dict, List, Any, Optional, Tuple

from lxml.etree import Element, SubElement

from ..config import CONFIG
from ..llm.gemini_client import GeminiClient
from ..llm.prompt_templates import template_manager
from ..knowledge.dynamic_query_engine import query_engine
from ..knowledge.constraint_engine import constraint_engine
from ..utils.serializers import ArchitectureDesign, generate_uuid
from ..utils.exceptions import ValidationError
from .component_registry import component_registry
from .reference_resolver import reference_resolver
from .dependency_analyzer import dependency_analyzer

class Round2Generator:
    """Round 2详细生成器 - 支持分批生成"""

    def __init__(self):
        """初始化Round 2生成器"""
        self.gemini_client = GeminiClient()
        self.query_engine = query_engine
        self.constraint_engine = constraint_engine
        self.component_registry = component_registry
        self.reference_resolver = reference_resolver
        self.dependency_analyzer = dependency_analyzer

    def generate_arxml(
        self,
        architecture_design: ArchitectureDesign,
        memory_context: str = "",
        custom_requirements: Dict[str, Any] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """生成详细的ARXML内容 - 支持分批生成"""

        try:
            # 分析要生成的组件
            component_plans = architecture_design.component_plan
            if not component_plans:
                raise ValidationError("架构设计中没有组件计划")

            # 判断生成策略
            component_count = len(component_plans)
            if component_count <= CONFIG.generation.single_batch_threshold:
                # 单批生成
                return self._generate_single_batch(
                    architecture_design, memory_context, custom_requirements
                )
            else:
                # 分批生成
                return self._generate_multi_batch(
                    architecture_design, memory_context, custom_requirements
                )

        except Exception as e:
            raise ValidationError(f"ARXML生成失败: {str(e)}")

    def _generate_single_batch(
        self,
        architecture_design: ArchitectureDesign,
        memory_context: str = "",
        custom_requirements: Dict[str, Any] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """单批生成 - 原有逻辑"""

        component_plans = architecture_design.component_plan

        # 动态生成JSON Schema
        arxml_schema = self._generate_dynamic_schema(component_plans)

        # 查询约束信息
        constraints = self._query_constraints(component_plans)

        # 生成提示词
        prompt = self._build_generation_prompt(
            architecture_design,
            constraints,
            memory_context,
            custom_requirements
        )

        if CONFIG.debug_mode:
            print(f"[DEBUG] 单批生成 - 组件数量: {len(component_plans)}")

        # 调用LLM生成ARXML
        response_data, input_tokens, output_tokens, total_tokens = \
            self.gemini_client.generate_with_schema(
                prompt=prompt,
                schema=arxml_schema,
            )

        # 将JSON转换为ARXML格式
        arxml_content = self._convert_json_to_arxml(response_data, architecture_design)

        # 生成统计信息
        stats = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "component_count": len(component_plans),
            "generation_mode": "single_batch",
            "schema_properties": len(arxml_schema.get("properties", {})),
            "constraints_applied": len(constraints)
        }

        return arxml_content, stats

    def _generate_multi_batch(
        self,
        architecture_design: ArchitectureDesign,
        memory_context: str = "",
        custom_requirements: Dict[str, Any] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """分批生成 - 新增逻辑"""

        # 1. 分析依赖关系并制定分批策略
        batches = self.dependency_analyzer.analyze_and_batch(
            architecture_design.component_plan,
            architecture_design.interface_plan
        )

        if CONFIG.debug_mode:
            print(f"[DEBUG] 分批策略: {len(batches)}批，组件分布: {[len(batch['components']) for batch in batches]}")

        # 2. 初始化注册表
        self.component_registry.initialize_session(
            architecture_design.component_plan,
            architecture_design.interface_plan
        )

        all_generated_components = {}
        total_stats = {
            "total_tokens": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "batch_count": len(batches),
            "component_count": len(architecture_design.component_plan),
            "generation_mode": "multi_batch",
            "batch_details": []
        }

        # 3. 逐批生成
        for batch_idx, batch_info in enumerate(batches):
            batch_components, batch_stats = self._generate_batch(
                batch_info,
                architecture_design,
                memory_context,
                custom_requirements,
                batch_idx
            )

            # 更新注册表
            for comp_data in batch_components.values():
                self.component_registry.register_generated_component(comp_data)

            # 合并结果
            all_generated_components.update(batch_components)

            # 累计统计
            total_stats["total_tokens"] += batch_stats["total_tokens"]
            total_stats["input_tokens"] += batch_stats["input_tokens"]
            total_stats["output_tokens"] += batch_stats["output_tokens"]
            total_stats["batch_details"].append(batch_stats)

        # 4. 展开语义占位符
        resolved_components = self.reference_resolver.resolve_all_references(
            all_generated_components,
            self.component_registry.get_interface_registry()
        )

        # 5. 组装最终ARXML
        final_arxml = self._assemble_final_arxml(resolved_components, architecture_design)

        return final_arxml, total_stats

    def _generate_batch(
        self,
        batch_info: Dict[str, Any],
        architecture_design: ArchitectureDesign,
        memory_context: str,
        custom_requirements: Dict[str, Any],
        batch_idx: int
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """生成单个批次"""

        batch_components = batch_info["components"]
        batch_type = batch_info["batch_type"]

        if CONFIG.debug_mode:
            print(f"[DEBUG] 生成第{batch_idx + 1}批: {batch_type}, {len(batch_components)}个组件")

        # 动态生成Schema（只包含当前批次组件）
        batch_schema = self.query_engine.generate_batch_schema(batch_components)

        # 查询约束
        constraints = self._query_constraints(batch_components)

        # 构建批次上下文
        batch_context = self._build_batch_context(
            batch_info,
            architecture_design,
            memory_context
        )

        # 生成批次特定提示词
        prompt = template_manager.get_batch_generation_prompt(
            batch_info=batch_info,
            architecture_design=architecture_design.__dict__,
            constraints=constraints,
            batch_context=batch_context,
            registered_interfaces=self.component_registry.get_interface_summaries()
        )

        # 调用LLM生成
        response_data, input_tokens, output_tokens, total_tokens = \
            self.gemini_client.generate_with_schema(
                prompt=prompt,
                schema=batch_schema
            )

        # 生成统计
        batch_stats = {
            "batch_idx": batch_idx,
            "batch_type": batch_type,
            "component_count": len(batch_components),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "constraints_applied": len(constraints)
        }

        return response_data, batch_stats

    def _build_batch_context(
        self,
        batch_info: Dict[str, Any],
        architecture_design: ArchitectureDesign,
        memory_context: str
    ) -> str:
        """构建批次上下文"""

        context_parts = []

        # 架构设计摘要
        context_parts.append("## 架构设计摘要")
        context_parts.append(f"系统功能: {architecture_design.system_analysis.get('functional_decomposition', '')}")
        context_parts.append(f"数据流分析: {architecture_design.system_analysis.get('data_flow_analysis', '')}")

        # 当前批次信息
        context_parts.append(f"\n## 当前批次信息")
        context_parts.append(f"批次类型: {batch_info['batch_type']}")
        context_parts.append(f"批次目标: {batch_info['description']}")

        # 已生成组件摘要
        registered_components = self.component_registry.get_component_summaries()
        if registered_components:
            context_parts.append(f"\n## 已生成组件摘要")
            for comp_summary in registered_components:
                context_parts.append(f"- {comp_summary['name']}: {comp_summary['interfaces']}")

        # 语义占位符指导
        context_parts.append(f"\n## 语义占位符使用指导")
        context_parts.append("对于组件间引用，请使用语义占位符，例如:")
        context_parts.append("- '引用温度传感器的输出端口'")
        context_parts.append("- '连接到数据处理器的控制接口'")
        context_parts.append("- '订阅系统状态管理器的模式切换'")

        # 记忆上下文
        if memory_context:
            context_parts.append(f"\n## 对话上下文")
            context_parts.append(memory_context)

        return "\n".join(context_parts)

    def _assemble_final_arxml(
        self,
        resolved_components: Dict[str, Any],
        architecture_design: ArchitectureDesign
    ) -> str:
        """组装最终ARXML"""

        from xml.etree.ElementTree import Element, SubElement, tostring
        from xml.dom import minidom

        # 创建AUTOSAR根元素
        root = Element("AUTOSAR")
        root.set("xmlns", "http://autosar.org/schema/r4.0")
        root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")

        # 创建AR-PACKAGES
        ar_packages = SubElement(root, "AR-PACKAGES")
        ar_package = SubElement(ar_packages, "AR-PACKAGE")
        SubElement(ar_package, "SHORT-NAME").text = "Components"

        # 创建ELEMENTS
        elements = SubElement(ar_package, "ELEMENTS")

        # 添加所有组件
        for comp_name, comp_data in resolved_components.items():
            if isinstance(comp_data, dict):
                self._json_dict_to_xml(elements, comp_name, comp_data)

        # 格式化输出
        rough_string = tostring(root, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

    # 保留原有的其他方法
    def _convert_json_to_arxml(self, json_data: Dict[str, Any], architecture_design: ArchitectureDesign) -> str:
        """将JSON数据转换为标准ARXML格式"""
        # 原有实现保持不变
        from xml.etree.ElementTree import Element, SubElement, tostring
        from xml.dom import minidom

        root = Element("AUTOSAR")
        root.set("xmlns", "http://autosar.org/schema/r4.0")
        root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")

        ar_packages = SubElement(root, "AR-PACKAGES")
        ar_package = SubElement(ar_packages, "AR-PACKAGE")
        SubElement(ar_package, "SHORT-NAME").text = "Components"
        elements = SubElement(ar_package, "ELEMENTS")

        for key, value in json_data.items():
            if isinstance(value, dict):
                self._json_dict_to_xml(elements, key, value)

        rough_string = tostring(root, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

    def _json_dict_to_xml(self, parent: Element, tag_name: str, data: Dict[str, Any]) -> Element:
        """递归将JSON字典转换为XML元素"""
        # 原有实现保持不变
        xml_tag = self._normalize_xml_tag(tag_name)
        element = SubElement(parent, xml_tag)

        for key, value in data.items():
            if key.startswith('@'):
                attr_name = key[1:]
                element.set(attr_name, str(value))
            elif key == '#text':
                element.text = str(value)
            elif isinstance(value, dict):
                self._json_dict_to_xml(element, key, value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        self._json_dict_to_xml(element, key, item)
                    else:
                        SubElement(element, key).text = str(item)
            else:
                SubElement(element, key).text = str(value)

        return element

    def _normalize_xml_tag(self, tag_name: str) -> str:
        """标准化XML标签名"""
        return tag_name.replace('_', '-').upper()

    def _generate_dynamic_schema(self, component_plans: List[Dict[str, Any]]) -> Dict[str, Any]:
        """动态生成JSON Schema - 无降级，失败直接报错"""

        # 必须成功生成，否则报错
        schema = self.query_engine.generate_multi_component_schema(component_plans)

        if not schema or not schema.get("properties"):
            raise ValidationError(f"Schema生成失败：无法为{len(component_plans)}个组件生成有效Schema")

        # 基于LLM的element_design增强schema
        for comp_plan in component_plans:
            comp_name = comp_plan.get("name")
            if comp_name in schema["properties"]:
                schema["properties"][comp_name] = self._enhance_schema_with_element_design(
                    schema["properties"][comp_name],
                    comp_plan.get("element_design", {})
                )

        if CONFIG.debug_mode:
            print(f"[DEBUG] 成功生成Schema，包含{len(schema.get('properties', {}))}个组件定义")

        return schema

    def _enhance_schema_with_element_design(
            self,
            base_schema: Dict[str, Any],
            element_design: Dict[str, Any]
    ) -> Dict[str, Any]:
        """基于LLM的元素设计增强Schema"""

        if not element_design:
            return base_schema

        # 如果LLM设计了ports，确保schema包含PORTS
        if element_design.get("ports", {}).get("needed"):
            if "properties" not in base_schema:
                base_schema["properties"] = {}

            if "PORTS" not in base_schema["properties"]:
                # 查询PORTS的完整结构
                from ..knowledge.terminology_builder import terminology_builder
                ports_context = terminology_builder.build_element_context_for_round2(
                    "PORTS", depth=2
                )

                base_schema["properties"]["PORTS"] = {
                    "type": "object",
                    "description": ports_context.get("element_descriptions", {}).get("PORTS", {}).get("description",
                                                                                                      "端口定义"),
                    "properties": {
                        "P-PORT-PROTOTYPE": {"type": "object"},
                        "R-PORT-PROTOTYPE": {"type": "object"}
                    }
                }

        # 如果LLM设计了internal_behaviors，确保schema包含
        if element_design.get("internal_behaviors", {}).get("needed"):
            if "properties" not in base_schema:
                base_schema["properties"] = {}

            if "INTERNAL-BEHAVIORS" not in base_schema["properties"]:
                base_schema["properties"]["INTERNAL-BEHAVIORS"] = {
                    "type": "object",
                    "description": "内部行为定义",
                    "properties": {
                        "SWC-INTERNAL-BEHAVIOR": {
                            "type": "object",
                            "properties": {
                                "SHORT-NAME": {"type": "string"},
                                "EVENTS": {"type": "object"},
                                "RUNNABLES": {"type": "object"}
                            }
                        }
                    }
                }

        return base_schema

    def _query_constraints(self, component_plans: List[Dict[str, Any]]) -> List[str]:
        """查询相关约束规则 - 无降级"""

        component_types = list(set([
            comp.get("type", "") for comp in component_plans
            if comp.get("type")
        ]))

        # 必须成功查询，否则报错
        constraints = self.query_engine.query_constraints_for_elements(component_types)

        if CONFIG.debug_mode:
            print(f"[DEBUG] 成功查询到{len(constraints)}条约束")

        return constraints

    def _build_generation_prompt(
        self,
        architecture_design: ArchitectureDesign,
        constraints: List[str],
        memory_context: str = "",
        custom_requirements: Dict[str, Any] = None
    ) -> str:
        """构建生成提示词"""
        # 原有实现保持不变
        prompt = template_manager.get_round2_prompt(
            architecture_design=architecture_design.__dict__,
            component_details=[],
            interface_details=[],
            constraints=constraints
        )

        from ..standard_types.standard_types import standard_type_manager
        type_context = standard_type_manager.get_type_context_for_llm(
            filter_categories=["VALUE", "TYPE_REFERENCE"]
        )
        prompt += f"\n\n{type_context}"

        prompt += "\n\n## 数据类型使用指导\n"
        prompt += "- 对于接口中的数据元素，请从上述标准类型中选择合适的类型\n"
        prompt += "- 使用TYPE-REFERENCE引用标准类型，例如：/AUTOSAR_Platform/ImplementationDataTypes/uint16\n"
        prompt += "- 布尔值使用boolean类型，并配合TRUE/FALSE值\n"
        prompt += "- 数值类型根据范围选择：uint8(0-255), uint16(0-65535), uint32等\n"
        prompt += "- 浮点数使用float32或float64\n"

        if memory_context:
            prompt += f"\n\n## 对话上下文\n{memory_context}"

        if len(architecture_design.component_plan) > 1:
            prompt += f"\n\n## 多组件生成要求\n"
            prompt += f"需要生成 {len(architecture_design.component_plan)} 个组件:\n"
            for i, comp in enumerate(architecture_design.component_plan, 1):
                prompt += f"{i}. {comp.get('name', f'Component{i}')} ({comp.get('type', 'APPLICATION-SW-COMPONENT-TYPE')})\n"
            prompt += "\n注意事项:\n"
            prompt += "- 每个组件使用独立的UUID\n"
            prompt += "- 确保组件间引用的一致性\n"
            prompt += "- 端口名称要体现组件特性\n"

        prompt += f"\n\n## 引用一致性要求\n"
        prompt += "- 所有UUID必须是唯一的\n"
        prompt += "- 接口引用路径要正确\n"
        prompt += "- START-ON-EVENT-REF必须正确引用RUNNABLE-ENTITY\n"
        prompt += "- PORT-PROTOTYPE-REF必须正确引用端口\n"

        if custom_requirements:
            prompt += f"\n\n## 特殊要求\n"
            for key, value in custom_requirements.items():
                prompt += f"- {key}: {value}\n"

        return prompt


# 保持原有的ReferenceManager但标记为deprecated
class ReferenceManager:
    """引用管理器（已弃用，使用ComponentRegistry替代）"""

    def __init__(self):
        self.component_refs = {}
        self.interface_refs = {}
        self.port_refs = {}
        self.runnable_refs = {}

    def initialize_from_plans(self, component_plans: List[Dict[str, Any]], interface_plans: List[Dict[str, Any]]):
        for comp_plan in component_plans:
            comp_id = comp_plan.get("component_id", "")
            comp_name = comp_plan.get("name", "")
            if comp_id and comp_name:
                self.component_refs[comp_id] = f"/{comp_name}"

        for intf_plan in interface_plans:
            intf_id = intf_plan.get("interface_id", "")
            intf_name = intf_plan.get("name", "")
            if intf_id and intf_name:
                self.interface_refs[intf_id] = f"/{intf_name}"

    def get_component_ref(self, component_id: str) -> str:
        return self.component_refs.get(component_id, f"/UnknownComponent_{component_id}")

    def get_interface_ref(self, interface_id: str) -> str:
        return self.interface_refs.get(interface_id, f"/UnknownInterface_{interface_id}")

    def register_port_ref(self, port_name: str, component_name: str) -> str:
        ref_path = f"/{component_name}/{port_name}"
        self.port_refs[port_name] = ref_path
        return ref_path

    def register_runnable_ref(self, runnable_name: str, component_name: str) -> str:
        ref_path = f"/{component_name}/InternalBehavior/{runnable_name}"
        self.runnable_refs[runnable_name] = ref_path
        return ref_path

# 全局Round2生成器实例
round2_generator = Round2Generator()