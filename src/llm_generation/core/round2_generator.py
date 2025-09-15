"""core/round2_generator.py - 修复版Round 2生成器

修复了参数调用不匹配问题和查询字段问题
专注于结构化输出，确保Schema生成流程正确
"""
import json
import time
from datetime import datetime
from pathlib import Path
import uuid as uuid_module
from typing import Dict, List, Any, Optional, Tuple
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

from ..config import CONFIG
from ..llm.openai_client import OpenAIClient as GeminiClient
# from ..llm.gemini_client import GeminiClient
from ..llm.prompt_templates import template_manager
from ..knowledge.dynamic_query_engine import query_engine
from ..knowledge.constraint_engine import constraint_engine
from ..standard_types.standard_types import standard_type_manager # 新增：导入标准类型管理器
from ..utils.serializers import ArchitectureDesign, generate_uuid
from ..utils.exceptions import ValidationError


class Round2Generator:
    """Round 2详细生成器 - 修复版"""

    def __init__(self):
        """初始化Round 2生成器"""
        self.gemini_client = GeminiClient()
        self.query_engine = query_engine
        self.constraint_engine = constraint_engine
        self.standard_type_manager = standard_type_manager  # 新增：标准类型管理器

        if CONFIG.debug_mode:
            print("[DEBUG] Round2生成器初始化（修复版：无函数调用）")
            # 显示加载的标准类型统计
            type_stats = self.standard_type_manager.get_stats()
            print(f"[DEBUG] 已加载标准类型: {type_stats}")

    def generate_arxml(
            self,
            architecture_design: ArchitectureDesign,
            memory_context: str = "",
            custom_requirements: Dict[str, Any] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """Round2 逐组件生成：
        - 为所有接口先生成“只读参考 Schema”
        - 按组件逐一生成（每个组件独立 Schema + Prompt + 推理）
        - 校验并合并为最终 JSON，再转 ARXML
        """

        start_time = time.time()
        component_plans = architecture_design.component_plan or []
        interface_plans = architecture_design.interface_plan or []

        if CONFIG.debug_mode:
            print(f"[DEBUG] Round2逐组件模式：{len(component_plans)} 个组件，{len(interface_plans)} 个接口")

        # 1) 先准备接口 Schema（只读参考，不混入组件根）
        interface_schema = self.query_engine.generate_multi_interface_schema(interface_plans)

        # 2) 全局约束集合（随后按组件过滤）
        constraints_all = self._query_comprehensive_constraints(component_plans, interface_plans)
        standard_types = self._prepare_standard_types()

        merged_json: Dict[str, Any] = {}
        token_stats = {"input": 0, "output": 0, "total": 0}

        for comp in component_plans:
            comp_name = comp.get("name", "Component")
            # 2.1 生成“单组件 Schema”（只含当前类型 definitions + 顶层 comp_name）
            comp_schema = self._build_single_component_schema(comp)

            # 保存单组件 Schema 以便调试
            self._save_component_schema_to_file(comp_name, comp_schema)

            # 2.2 过滤与该组件相关的约束，减少无关噪声
            constraints = self._filter_constraints_for_component(comp, constraints_all)

            # 2.3 逐组件 Prompt（接口 Schema 以只读参考方式注入）
            prompt = template_manager.get_round2_prompt_single(
                comp_plan=comp,
                interface_plans=interface_plans,
                constraints=constraints,
                component_schema=comp_schema,
                interface_schema=interface_schema,
                memory_context=memory_context or ""
            )

            # 补充标准类型引用规则（用于 *-INTERFACE-TREF 的 DEST 指引等）
            prompt += self._format_standard_types(standard_types)
            prompt += self._add_direct_reference_guidance(architecture_design)

            # 2.4 调用 LLM（严格约束该组件 Schema）
            resp, in_tok, out_tok, ttl_tok = self.gemini_client.generate_with_schema(
                prompt=prompt,
                schema=comp_schema,
                temperature=0.7,
                max_retries=3
            )
            self._save_component_prompt_to_file(comp_name, prompt)
            self._save_component_response_to_file(comp_name, resp)

            token_stats["input"] += in_tok
            token_stats["output"] += out_tok
            token_stats["total"] += ttl_tok

            # 2.5 合并当前组件结果（顶层只会有一个键 = comp_name）
            if isinstance(resp, dict):
                merged_json.update(resp)

        # 3) 合并接口（如果你的后续 ARXML 转换需要放在同一 JSON 下）
        if interface_plans:
            merged_json["_interfaces"] = self._extract_interfaces_as_readonly(interface_plans)

        # 4) 转换为 ARXML
        arxml_content = self._convert_to_arxml(merged_json, architecture_design)

        # 5) 统计
        generation_time = time.time() - start_time
        stats = {
            "input_tokens": token_stats["input"],
            "output_tokens": token_stats["output"],
            "total_tokens": token_stats["total"],
            "generation_time": generation_time
        }
        return arxml_content, stats

    def _build_single_component_schema(self, comp: Dict[str, Any]) -> Dict[str, Any]:
        """
        Round2 单组件 schema 构建入口：
        - 不做任何 runnable elements 的合并或简化
        - 直接把 Round1 的 element_design 交给 query_engine
        """
        return self.query_engine.generate_component_schema_fixed(comp)

    # def _generate_unified_batch(
    #     self,
    #     architecture_design: ArchitectureDesign,
    #     memory_context: str = "",
    #     custom_requirements: Dict[str, Any] = None
    # ) -> Tuple[str, Dict[str, Any]]:
    #     """统一批次生成 - 修复版，无函数调用"""
    #
    #     start_time = time.time()
    #     component_plans = architecture_design.component_plan
    #     interface_plans = architecture_design.interface_plan
    #
    #     if CONFIG.debug_mode:
    #         print(f"[DEBUG] 统一批次生成: {len(component_plans)}个组件, {len(interface_plans)}个接口")
    #         print(f"[DEBUG] 使用纯结构化输出模式（无函数调用）")
    #
    #     # ========== Phase 1: 准备阶段（所有动态信息一次性获取）==========
    #
    #     # 1. 生成深度Schema
    #     # arxml_schema = self._generate_deep_schema(component_plans)
    #
    #     arxml_schema = self._generate_comprehensive_schema(component_plans, interface_plans)
    #
    #     # 输出schema到文件
    #     self._save_schema_to_file(arxml_schema)
    #
    #     # 2. 批量生成UUID（预生成所有需要的UUID）
    #     # uuid_mapping = self._batch_generate_uuids(component_plans, interface_plans)
    #
    #     # 3. 查询完整约束信息
    #     constraints = self._query_comprehensive_constraints(component_plans, interface_plans)
    #
    #     # 4. 准备标准类型引用（使用动态加载的类型）
    #     standard_types = self._prepare_standard_types()
    #
    #     # ========== Phase 2: 生成阶段（纯LLM结构化输出）==========
    #
    #     # 【修复】：构建增强的提示词（修复参数传递）
    #     prompt = self._build_enhanced_prompt(
    #         architecture_design,
    #         constraints,
    #         memory_context,
    #         custom_requirements,
    #         standard_types,
    #         arxml_schema
    #     )
    #     # 输出prompt到文件
    #     self._save_prompt_to_file(prompt)
    #
    #     if CONFIG.debug_mode:
    #         print(f"[DEBUG] 提示词长度: {len(prompt)} 字符")
    #         # print(f"[DEBUG] 预生成UUID数: {len(uuid_mapping)}")
    #         print(f"[DEBUG] 约束规则数: {len(constraints)}")
    #         print(f"[DEBUG] 标准类型数: {len(standard_types['implementation_types'])}")
    #
    #     # 调用LLM生成（纯结构化输出，无函数调用）
    #     response_data, input_tokens, output_tokens, total_tokens = \
    #         self.gemini_client.generate_with_schema(
    #             prompt=prompt,
    #             schema=arxml_schema,
    #             temperature=0.7,
    #             max_retries=3
    #         )
    #     self._save_response_to_file(response_data)
    #     # ========== Phase 3: 后处理阶段 ==========
    #
    #     # 1. 验证生成的内容
    #     # validation_results = self._validate_generated_content(response_data, constraints)
    #
    #     # 2. 确保所有引用都是直接路径（不需要解析语义占位符）
    #     # processed_data = self._ensure_direct_references(response_data)
    #
    #     # 3. 转换为ARXML
    #     arxml_content = self._convert_to_arxml(response_data, architecture_design)
    #
    #     generation_time = time.time() - start_time
    #
    #     # 详细统计信息
    #     stats = {
    #         "input_tokens": input_tokens,
    #         "output_tokens": output_tokens,
    #         "total_tokens": total_tokens,
    #         "component_count": len(component_plans),
    #         "interface_count": len(interface_plans),
    #         "generation_mode": "unified_batch",
    #         "schema_properties": len(arxml_schema.get("properties", {})),
    #         "constraints_applied": len(constraints),
    #         # "uuids_generated": len(uuid_mapping),
    #         "standard_types_available": len(standard_types['implementation_types']),
    #         # "validation_passed": validation_results["passed"],
    #         # "validation_errors": validation_results["errors"],
    #         "generation_time": generation_time,
    #         "tokens_per_component": total_tokens / max(len(component_plans), 1),
    #         "performance_metrics": {
    #             "time_per_component": generation_time / max(len(component_plans), 1),
    #             "schema_complexity": self._calculate_schema_complexity(arxml_schema),
    #             "output_efficiency": output_tokens / max(len(str(response_data)), 1)
    #         }
    #     }
    #
    #     if CONFIG.debug_mode:
    #         print(f"[DEBUG] 生成完成: {generation_time:.2f}秒")
    #         print(f"[DEBUG] Token效率: {stats['tokens_per_component']:.0f} tokens/组件")
    #         # print(f"[DEBUG] 验证结果: {'通过' if validation_results['passed'] else '有错误'}")
    #
    #     return arxml_content, stats

    # def _generate_comprehensive_schema(
    #         self,
    #         component_plans: List[Dict[str, Any]],
    #         interface_plans: List[Dict[str, Any]]
    # ) -> Dict[str, Any]:
    #     """生成包含组件和接口的完整Schema"""
    #
    #     # 生成组件Schema
    #     component_schema = self.query_engine.generate_multi_component_schema(component_plans)
    #
    #     # 生成接口Schema
    #     interface_schema = self.query_engine.generate_multi_interface_schema(interface_plans)
    #
    #     # 合并Schema
    #     comprehensive_schema = {
    #         "type": "object",
    #         "properties": {
    #             **component_schema.get("properties", {}),
    #             "_interfaces": {
    #                 "type": "object",
    #                 "properties": interface_schema.get("properties", {}),
    #                 "description": "接口定义集合"
    #             }
    #         },
    #         "definitions": {
    #             **component_schema.get("definitions", {}),
    #             **interface_schema.get("definitions", {})
    #         },
    #         "required": list(component_schema.get("properties", {}).keys())
    #     }
    #
    #     return comprehensive_schema

    def _filter_constraints_for_component(self, comp_plan: Dict[str, Any], constraints: List[str]) -> List[str]:
        """按组件特征（端口/内部行为/事件）过滤约束，减少 LLM 负担。"""
        ed = comp_plan.get("element_design", {}) or {}
        need_ports = bool(ed.get("ports", {}).get("needed"))
        need_ib = bool(ed.get("internal_behaviors", {}).get("needed"))
        event_types = set()
        for e in ed.get("internal_behaviors", {}).get("events", []) or []:
            if isinstance(e, dict) and e.get("type"):
                event_types.add(e["type"])

        filtered = []
        for c in constraints or []:
            cs = c or ""
            # 朴素启发：只保留与需要的部分相关的约束
            if ("端口" in cs or "PORT" in cs) and not need_ports:
                continue
            if ("RUNNABLE" in cs or "事件" in cs or "EVENT" in cs or "INTERNAL-BEHAVIOR" in cs) and not need_ib:
                continue
            # 如果指向特定事件类型，但该组件未声明此事件，则跳过
            if any(et in cs for et in ["TIMING-EVENT", "DATA-RECEIVED-EVENT", "OPERATION-INVOKED-EVENT"]):
                if not any(et in cs for et in event_types):
                    continue
            filtered.append(c)
        # 去重
        return sorted(set(filtered))


    def _prepare_standard_types(self) -> Dict[str, Any]:
        """准备标准类型引用信息 - 动态加载版本"""

        # 从标准类型管理器动态获取类型
        implementation_types = []
        base_types = []
        compu_methods = []

        # 获取所有IMPLEMENTATION-DATA-TYPE（接口应该引用这些）
        for impl_type_name, impl_type in self.standard_type_manager.implementation_types.items():
            # 只包含VALUE类型（基础数据类型）
            if impl_type.category == "VALUE":
                # 构建完整路径（基于实际ARXML中的路径）
                type_path = f"/AUTOSAR_Platform/ImplementationDataTypes/{impl_type.name}"
                implementation_types.append({
                    "path": type_path,
                    "name": impl_type.name,
                    "description": impl_type.description,
                    "base_type": impl_type.base_type_ref
                })

        # 添加标准类型库的其他类型（如Std_ReturnType）
        if "Std_ReturnType" in self.standard_type_manager.implementation_types:
            implementation_types.append({
                "path": "/AUTOSAR_Std/ImplementationDataTypes/Std_ReturnType",
                "name": "Std_ReturnType",
                "description": "Standard return type for APIs",
                "base_type": "/AUTOSAR_Platform/BaseTypes/uint8"
            })

        # 获取CompuMethods（计算方法）
        for compu_name, compu in self.standard_type_manager.compu_methods.items():
            if "RB" in compu_name or "RBA" in compu_name:
                # RB相关的CompuMethod
                compu_path = f"/RB/RBA/Common/CentralElements/CompuMethods/{compu.name}"
            elif "AUTOSAR" in compu_name or compu_name == "boolean":
                # AUTOSAR标准CompuMethod
                compu_path = f"/AUTOSAR_Platform/CompuMethods/{compu.name}"
            else:
                # 其他标准CompuMethod
                compu_path = f"/AUTOSAR_Std/CompuMethods/{compu.name}"

            compu_methods.append({
                "path": compu_path,
                "name": compu.name,
                "category": compu.category
            })

        # 注意：SW-BASE-TYPE不应直接被接口引用，仅供参考
        for base_type_name, base_type in self.standard_type_manager.base_types.items():
            base_types.append({
                "path": f"/AUTOSAR_Platform/BaseTypes/{base_type.name}",
                "name": base_type.name,
                "size": base_type.size,
                "encoding": base_type.encoding,
                "note": "仅供IMPLEMENTATION-DATA-TYPE内部引用，接口不应直接使用"
            })

        result = {
            "implementation_types": implementation_types,  # 接口数据元素应该引用这些
            "base_types": base_types,  # 仅供参考，不直接使用
            "compu_methods": compu_methods  # 计算方法
        }

        if CONFIG.debug_mode:
            print(f"[DEBUG] 动态加载标准类型:")
            print(f"  - 实现类型: {len(implementation_types)}")
            print(f"  - 基础类型: {len(base_types)} (仅供参考)")
            print(f"  - 计算方法: {len(compu_methods)}")

        return result

    def _build_enhanced_prompt(
        self,
        architecture_design: ArchitectureDesign,
        constraints: List[str],
        memory_context: str,
        custom_requirements: Dict[str, Any],
        standard_types: Dict[str, Any],
        arxml_schema: Dict[str, Any]
    ) -> str:
        """【修复】：构建增强的提示词（修复参数列表）"""

        # 获取schema深度配置
        if hasattr(CONFIG.generation, 'max_schema_injection_depth'):
            schema_depth = CONFIG.generation.max_schema_injection_depth
        else:
            schema_depth = CONFIG.knowledge_graph.max_safety_depth

        # 使用模板生成基础提示词
        prompt = template_manager.get_round2_prompt(
            architecture_design=architecture_design.__dict__,
            constraints=constraints,
            schema_depth=schema_depth,
            composite_schema=arxml_schema
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
        # prompt += self._format_uuid_mapping(uuid_mapping)

        # 添加标准类型引用（改进版）
        prompt += self._format_standard_types(standard_types)

        # 添加直接引用指导
        prompt += self._add_direct_reference_guidance(architecture_design)

        return prompt


    def _format_standard_types(self, standard_types: Dict[str, Any]) -> str:
        """格式化标准类型引用 - 改进版，基于动态加载的类型"""

        prompt = "\n\n## 标准数据类型引用规则\n"
        prompt += "**重要**：接口中的数据元素必须引用IMPLEMENTATION-DATA-TYPE，而不是SW-BASE-TYPE！\n\n"

        prompt += "### 可用的实现数据类型（用于接口和端口）\n"
        prompt += "以下是接口DATA-ELEMENT应该使用的类型：\n\n"

        for type_info in standard_types["implementation_types"][:15]:  # 显示前15个常用类型
            prompt += f"- `{type_info['path']}`  # {type_info['name']}类型"
            if type_info.get('description'):
                prompt += f" - {type_info['description'][:50]}"
            prompt += "\n"

        if len(standard_types["implementation_types"]) > 15:
            prompt += f"... 以及其他 {len(standard_types['implementation_types']) - 15} 个标准类型\n"

        prompt += "\n### 正确的类型引用示例\n"
        prompt += "```xml\n"
        prompt += '<TYPE-TREF DEST="IMPLEMENTATION-DATA-TYPE">/AUTOSAR_Platform/ImplementationDataTypes/uint16</TYPE-TREF>\n'
        prompt += "```\n\n"

        # 添加ComputMethod信息
        if standard_types.get("compu_methods"):
            prompt += "### 可用的计算方法（CompuMethod）\n"
            for compu_info in standard_types["compu_methods"][:5]:
                prompt += f"- `{compu_info['path']}` ({compu_info['category']})\n"

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


    def _query_comprehensive_constraints(
            self,
            component_plans: List[Dict[str, Any]],
            interface_plans: List[Dict[str, Any]]
    ) -> List[str]:
        """查询完整的约束规则 - 支持配置控制"""

        constraints = []

        # 检查约束引擎是否启用
        if hasattr(CONFIG, 'constraint_engine') and not CONFIG.constraint_engine.enabled:
            # 约束引擎被禁用，只返回最基础的约束
            if CONFIG.debug_mode:
                print("[DEBUG] 约束引擎已禁用，使用最小约束集")

            return [
                "所有UUID必须全局唯一",
                "SHORT-NAME必须符合NCName规范",
                "引用路径必须正确且一致"
            ]

        # 获取约束配置
        constraint_config = getattr(CONFIG, 'constraint_engine', None)
        max_constraints = constraint_config.max_constraints_per_type if constraint_config else 3
        exclude_standard = constraint_config.exclude_standard_constraints if constraint_config else False

        # 约束引擎启用时的逻辑
        try:
            # 组件类型约束
            component_types = set(comp.get("type", "") for comp in component_plans)
            for comp_type in component_types:
                if comp_type:
                    type_constraints = self.query_engine.query_constraints_for_elements([comp_type])
                    # 限制约束数量
                    constraints.extend(type_constraints[:max_constraints])

            # 接口类型约束
            interface_types = set(intf.get("type", "") for intf in interface_plans)
            for intf_type in interface_types:
                if intf_type:
                    intf_constraints = self.query_engine.query_constraints_for_elements([intf_type])
                    # 限制约束数量
                    constraints.extend(intf_constraints[:max_constraints])

        except Exception as e:
            if CONFIG.debug_mode:
                print(f"[DEBUG] 约束查询失败，使用基础约束: {e}")

        # 通用AUTOSAR约束（根据配置决定是否添加）
        if not exclude_standard:
            general_constraints = [
                "所有UUID必须全局唯一",
                "SHORT-NAME必须符合NCName规范",
                "端口名称在组件内必须唯一",
                "事件必须正确引用Runnable",
                "接口引用必须使用完整路径",
                "接口数据元素必须引用IMPLEMENTATION-DATA-TYPE，不能引用SW-BASE-TYPE",
                "类型引用格式：/AUTOSAR_Platform/ImplementationDataTypes/类型名"
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

    def _save_schema_to_file(self, schema: Dict[str, Any]):
        """保存Schema到文件"""
        try:
            output_dir = Path(CONFIG.output_dir) / "debug"
            output_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            schema_file = output_dir / f"round2_schema_{timestamp}.json"

            with open(schema_file, 'w', encoding='utf-8') as f:
                json.dump(schema, f, indent=2, ensure_ascii=False)

            if CONFIG.debug_mode:
                print(f"[DEBUG] Schema已保存到: {schema_file}")

        except Exception as e:
            if CONFIG.debug_mode:
                print(f"[WARNING] Schema保存失败: {e}")

    def _save_prompt_to_file(self, prompt: str):
        """保存Prompt到文件"""
        try:
            output_dir = Path(CONFIG.output_dir) / "debug"
            output_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            prompt_file = output_dir / f"round2_prompt_{timestamp}.txt"

            with open(prompt_file, 'w', encoding='utf-8') as f:
                f.write(prompt)

            if CONFIG.debug_mode:
                print(f"[DEBUG] Prompt已保存到: {prompt_file}")

        except Exception as e:
            if CONFIG.debug_mode:
                print(f"[WARNING] Prompt保存失败: {e}")

    def _save_response_to_file(self, response_data: Dict[str, Any]):
        """保存Response数据到文件"""
        try:
            output_dir = Path(CONFIG.output_dir) / "debug"
            output_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            response_file = output_dir / f"round2_response_{timestamp}.json"

            with open(response_file, 'w', encoding='utf-8') as f:
                json.dump(response_data, f, indent=2, ensure_ascii=False)

            if CONFIG.debug_mode:
                print(f"[DEBUG] Response已保存到: {response_file}")

        except Exception as e:
            if CONFIG.debug_mode:
                print(f"[WARNING] Response保存失败: {e}")

    def _extract_interfaces_as_readonly(self, interface_plans: List[Dict[str, Any]]) -> Dict[str, Any]:
        """把 Round1 的接口清单提炼成只读的索引（可选）。
        不做深结构生成，避免引导 LLM 回写接口对象。
        """
        out = {}
        for it in interface_plans or []:
            name = it.get("name")
            if not name:
                continue
            out[name] = {
                "type": it.get("type"),
                "purpose": it.get("purpose")
            }
        return out

    def _save_component_schema_to_file(self, comp_name: str, schema: Dict[str, Any]):
        try:
            output_dir = Path(CONFIG.output_dir) / "debug"
            output_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            fp = output_dir / f"round2_schema_{comp_name}_{ts}.json"
            with open(fp, "w", encoding="utf-8") as f:
                json.dump(schema, f, indent=2, ensure_ascii=False)
            if CONFIG.debug_mode:
                print(f"[DEBUG] 单组件Schema已保存: {fp}")
        except Exception as e:
            if CONFIG.debug_mode:
                print(f"[WARNING] 保存单组件Schema失败: {e}")

    def _save_component_prompt_to_file(self, comp_name: str, prompt: str):
        try:
            output_dir = Path(CONFIG.output_dir) / "debug"
            output_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            fp = output_dir / f"round2_prompt_{comp_name}_{ts}.txt"
            with open(fp, "w", encoding="utf-8") as f:
                f.write(prompt)
            if CONFIG.debug_mode:
                print(f"[DEBUG] 单组件Prompt已保存: {fp}")
        except Exception as e:
            if CONFIG.debug_mode:
                print(f"[WARNING] 保存单组件Prompt失败: {e}")

    def _save_component_response_to_file(self, comp_name: str, resp: Dict[str, Any]):
        try:
            output_dir = Path(CONFIG.output_dir) / "debug"
            output_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            fp = output_dir / f"round2_response_{comp_name}_{ts}.json"
            with open(fp, "w", encoding="utf-8") as f:
                json.dump(resp, f, indent=2, ensure_ascii=False)
            if CONFIG.debug_mode:
                print(f"[DEBUG] 单组件Response已保存: {fp}")
        except Exception as e:
            if CONFIG.debug_mode:
                print(f"[WARNING] 保存单组件Response失败: {e}")


# 全局Round2生成器实例
round2_generator = Round2Generator()