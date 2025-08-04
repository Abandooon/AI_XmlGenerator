"""core/round2_generator.py - Round 2详细生成器

执行第二轮对话：根据确认的架构设计生成详细的ARXML JSON内容
支持多组件生成，动态Schema生成，确保实例引用唯一性
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

class Round2Generator:
    """Round 2详细生成器"""

    def __init__(self):
        """初始化Round 2生成器"""
        self.gemini_client = GeminiClient()
        self.query_engine = query_engine
        self.constraint_engine = constraint_engine

        # 实例引用管理
        self.reference_manager = ReferenceManager()

    def generate_arxml(
        self,
        architecture_design: ArchitectureDesign,
        memory_context: str = "",
        custom_requirements: Dict[str, Any] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """生成详细的ARXML内容"""

        try:
            # 分析要生成的组件
            component_plans = architecture_design.component_plan
            if not component_plans:
                raise ValidationError("架构设计中没有组件计划")

            # 动态生成JSON Schema
            arxml_schema = self._generate_dynamic_schema(component_plans)

            # 查询约束信息
            constraints = self._query_constraints(component_plans)

            # 初始化引用管理器
            self.reference_manager.initialize_from_plans(component_plans, architecture_design.interface_plan)

            # 生成提示词
            prompt = self._build_generation_prompt(
                architecture_design,
                constraints,
                memory_context,
                custom_requirements
            )

            if CONFIG.debug_mode:
                print(f"[DEBUG] Round2 提示词长度: {len(prompt)}")
                print(f"[DEBUG] 动态生成的Schema键: {list(arxml_schema.get('properties', {}).keys())}")

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
                "schema_properties": len(arxml_schema.get("properties", {})),
                "constraints_applied": len(constraints)
            }

            if CONFIG.debug_mode:
                print(f"[DEBUG] Round2完成: {len(arxml_content)}个顶级元素")

            return arxml_content, stats

        except Exception as e:
            raise ValidationError(f"ARXML生成失败: {str(e)}")

    def _convert_json_to_arxml(self, json_data: Dict[str, Any], architecture_design: ArchitectureDesign) -> str:
        """将JSON数据转换为标准ARXML格式"""

        from xml.etree.ElementTree import Element, SubElement, tostring
        from xml.dom import minidom

        # 创建AUTOSAR根元素
        root = Element("AUTOSAR")
        root.set("xmlns", "http://autosar.org/schema/r4.0")
        root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")

        # 创建AR-PACKAGES
        ar_packages = SubElement(root, "AR-PACKAGES")
        ar_package = SubElement(ar_packages, "AR-PACKAGE")

        # 设置包信息
        SubElement(ar_package, "SHORT-NAME").text = "Components"

        # 创建ELEMENTS
        elements = SubElement(ar_package, "ELEMENTS")

        # 递归转换JSON到XML
        for key, value in json_data.items():
            if isinstance(value, dict):
                self._json_dict_to_xml(elements, key, value)

        # 格式化输出
        rough_string = tostring(root, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

    def _json_dict_to_xml(self, parent: Element, tag_name: str, data: Dict[str, Any]) -> Element:
        """递归将JSON字典转换为XML元素"""

        # 处理特殊标签名转换
        xml_tag = self._normalize_xml_tag(tag_name)
        element = SubElement(parent, xml_tag)

        for key, value in data.items():
            if key.startswith('@'):
                # XML属性
                attr_name = key[1:]  # 去掉@前缀
                element.set(attr_name, str(value))
            elif key == '#text':
                # 文本内容
                element.text = str(value)
            elif isinstance(value, dict):
                # 嵌套对象
                self._json_dict_to_xml(element, key, value)
            elif isinstance(value, list):
                # 数组
                for item in value:
                    if isinstance(item, dict):
                        self._json_dict_to_xml(element, key, item)
                    else:
                        SubElement(element, key).text = str(item)
            else:
                # 简单值
                SubElement(element, key).text = str(value)

        return element

    def _normalize_xml_tag(self, tag_name: str) -> str:
        """标准化XML标签名"""
        # 移除非法字符，确保符合XML标签命名规范
        return tag_name.replace('_', '-').upper()

    def _generate_dynamic_schema(self, component_plans: List[Dict[str, Any]]) -> Dict[str, Any]:
        """动态生成JSON Schema"""

        try:
            # 使用查询引擎生成多组件Schema
            schema = self.query_engine.generate_multi_component_schema(component_plans)

            if CONFIG.debug_mode:
                print(f"[DEBUG] 动态生成Schema，包含{len(schema.get('properties', {}))}个属性")

            return schema

        except Exception as e:
            if CONFIG.debug_mode:
                print(f"[DEBUG] 动态Schema生成失败: {e}")

            # 动态Schema生成失败时直接抛出异常
            raise ValidationError(f"动态Schema生成失败: {e}")

    def _query_constraints(self, component_plans: List[Dict[str, Any]]) -> List[str]:
        """查询相关约束规则"""

        # 提取所有组件类型
        component_types = list(set([
            comp.get("type", "") for comp in component_plans
            if comp.get("type")
        ]))

        try:
            # 从KG查询约束
            constraints = self.query_engine.query_constraints_for_elements(component_types)

            if CONFIG.debug_mode:
                print(f"[DEBUG] 查询到{len(constraints)}条约束")

            return constraints

        except Exception as e:
            if CONFIG.debug_mode:
                print(f"[DEBUG] 约束查询失败: {e}")
            return ["确保XML结构完整性", "遵循AUTOSAR命名规范"]

    def _build_generation_prompt(
            self,
            architecture_design: ArchitectureDesign,
            constraints: List[str],
            memory_context: str = "",
            custom_requirements: Dict[str, Any] = None
    ) -> str:
        """构建生成提示词"""

        # 使用模板管理器生成基础提示词
        prompt = template_manager.get_round2_prompt(
            architecture_design=architecture_design.__dict__,
            component_details=[],
            interface_details=[],
            constraints=constraints
        )

        # 添加标准类型信息 - 新增
        from ..standard_types.standard_types import standard_type_manager
        type_context = standard_type_manager.get_type_context_for_llm(
            filter_categories=["VALUE", "TYPE_REFERENCE"]  # 只包含常用类型
        )
        prompt += f"\n\n{type_context}"

        # 添加类型使用指导 - 新增
        prompt += "\n\n## 数据类型使用指导\n"
        prompt += "- 对于接口中的数据元素，请从上述标准类型中选择合适的类型\n"
        prompt += "- 使用TYPE-REFERENCE引用标准类型，例如：/AUTOSAR_Platform/ImplementationDataTypes/uint16\n"
        prompt += "- 布尔值使用boolean类型，并配合TRUE/FALSE值\n"
        prompt += "- 数值类型根据范围选择：uint8(0-255), uint16(0-65535), uint32等\n"
        prompt += "- 浮点数使用float32或float64\n"

        # 添加记忆上下文
        if memory_context:
            prompt += f"\n\n## 对话上下文\n{memory_context}"

        # 添加多组件生成指导
        if len(architecture_design.component_plan) > 1:
            prompt += f"\n\n## 多组件生成要求\n"
            prompt += f"需要生成 {len(architecture_design.component_plan)} 个组件:\n"
            for i, comp in enumerate(architecture_design.component_plan, 1):
                prompt += f"{i}. {comp.get('name', f'Component{i}')} ({comp.get('type', 'APPLICATION-SW-COMPONENT-TYPE')})\n"
            prompt += "\n注意事项:\n"
            prompt += "- 每个组件使用独立的UUID\n"
            prompt += "- 确保组件间引用的一致性\n"
            prompt += "- 端口名称要体现组件特性\n"

        # 添加引用一致性要求
        prompt += f"\n\n## 引用一致性要求\n"
        prompt += "- 所有UUID必须是唯一的\n"
        prompt += "- 接口引用路径要正确\n"
        prompt += "- START-ON-EVENT-REF必须正确引用RUNNABLE-ENTITY\n"
        prompt += "- PORT-PROTOTYPE-REF必须正确引用端口\n"

        # 添加自定义要求
        if custom_requirements:
            prompt += f"\n\n## 特殊要求\n"
            for key, value in custom_requirements.items():
                prompt += f"- {key}: {value}\n"

        return prompt


    def _build_reference_map(self, arxml_data: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
        """构建引用映射表"""

        ref_map = {
            "runnables": {},      # runnable_name -> path
            "ports": {},          # port_name -> path
            "interfaces": {},     # interface_name -> path
            "components": {}      # component_name -> path
        }

        def collect_refs(obj, current_path=""):
            if isinstance(obj, dict):
                # 收集组件引用
                if "SHORT-NAME" in obj and current_path.endswith("APPLICATION-SW-COMPONENT-TYPE"):
                    comp_name = obj["SHORT-NAME"]
                    ref_map["components"][comp_name] = f"/{comp_name}"

                # 收集端口引用
                if "SHORT-NAME" in obj and ("P-PORT-PROTOTYPE" in current_path or "R-PORT-PROTOTYPE" in current_path):
                    port_name = obj["SHORT-NAME"]
                    ref_map["ports"][port_name] = f"/{port_name}"

                # 收集Runnable引用
                if "SHORT-NAME" in obj and "RUNNABLE-ENTITY" in current_path:
                    runnable_name = obj["SHORT-NAME"]
                    ref_map["runnables"][runnable_name] = f"/{runnable_name}"

                for key, value in obj.items():
                    collect_refs(value, f"{current_path}.{key}")
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    collect_refs(item, f"{current_path}[{i}]")

        collect_refs(arxml_data)
        return ref_map


class ReferenceManager:
    """引用管理器，确保实例引用的唯一性和一致性"""

    def __init__(self):
        self.component_refs = {}
        self.interface_refs = {}
        self.port_refs = {}
        self.runnable_refs = {}

    def initialize_from_plans(
        self,
        component_plans: List[Dict[str, Any]],
        interface_plans: List[Dict[str, Any]]
    ):
        """从设计计划初始化引用"""

        # 初始化组件引用
        for comp_plan in component_plans:
            comp_id = comp_plan.get("component_id", "")
            comp_name = comp_plan.get("name", "")
            if comp_id and comp_name:
                self.component_refs[comp_id] = f"/{comp_name}"

        # 初始化接口引用
        for intf_plan in interface_plans:
            intf_id = intf_plan.get("interface_id", "")
            intf_name = intf_plan.get("name", "")
            if intf_id and intf_name:
                self.interface_refs[intf_id] = f"/{intf_name}"

    def get_component_ref(self, component_id: str) -> str:
        """获取组件引用路径"""
        return self.component_refs.get(component_id, f"/UnknownComponent_{component_id}")

    def get_interface_ref(self, interface_id: str) -> str:
        """获取接口引用路径"""
        return self.interface_refs.get(interface_id, f"/UnknownInterface_{interface_id}")

    def register_port_ref(self, port_name: str, component_name: str) -> str:
        """注册端口引用"""
        ref_path = f"/{component_name}/{port_name}"
        self.port_refs[port_name] = ref_path
        return ref_path

    def register_runnable_ref(self, runnable_name: str, component_name: str) -> str:
        """注册Runnable引用"""
        ref_path = f"/{component_name}/InternalBehavior/{runnable_name}"
        self.runnable_refs[runnable_name] = ref_path
        return ref_path

# 全局Round2生成器实例
round2_generator = Round2Generator()