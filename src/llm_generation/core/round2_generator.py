"""core/round2_generator.py - 优化的Round 2生成器

利用Gemini长上下文能力，优先单批生成，减少复杂度
"""
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

from ..config import CONFIG
from ..llm.gemini_client import GeminiClient
from ..llm.prompt_templates import template_manager
from ..knowledge.dynamic_query_engine import query_engine
from ..utils.serializers import ArchitectureDesign, generate_uuid
from ..utils.exceptions import ValidationError


class Round2Generator:
    """Round 2详细生成器 - 长上下文优化版"""

    def __init__(self):
        """初始化Round 2生成器"""
        self.gemini_client = GeminiClient()
        self.query_engine = query_engine
        # 移除不必要的依赖
        # self.component_registry = component_registry  # 不再需要
        # self.reference_resolver = reference_resolver  # 简化处理
        # self.dependency_analyzer = dependency_analyzer  # 简化处理

    def generate_arxml(
        self,
        architecture_design: ArchitectureDesign,
        memory_context: str = "",
        custom_requirements: Dict[str, Any] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """生成详细的ARXML内容 - 优化版"""

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
                # 单批生成（现在支持到25个组件）
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
        """统一批次生成 - 核心优化"""

        start_time = time.time()
        component_plans = architecture_design.component_plan
        interface_plans = architecture_design.interface_plan

        if CONFIG.debug_mode:
            print(f"[DEBUG] 统一批次生成: {len(component_plans)}个组件, {len(interface_plans)}个接口")

        # 生成深度Schema（增强到depth=15）
        schema_depth = CONFIG.generation.max_schema_injection_depth
        arxml_schema = self._generate_deep_schema(component_plans, schema_depth)

        # 查询完整约束信息
        constraints = self._query_comprehensive_constraints(component_plans, interface_plans)

        # 构建完整上下文的提示词
        prompt = self._build_unified_prompt(
            architecture_design,
            constraints,
            memory_context,
            custom_requirements,
            schema_depth
        )

        if CONFIG.debug_mode:
            print(f"[DEBUG] 提示词长度: {len(prompt)} 字符")
            print(f"[DEBUG] Schema深度: {schema_depth}")
            print(f"[DEBUG] 约束规则数: {len(constraints)}")

        # 调用LLM生成（利用长上下文）
        response_data, input_tokens, output_tokens, total_tokens = \
            self.gemini_client.generate_with_schema(
                prompt=prompt,
                schema=arxml_schema,
                temperature=0.7,  # 保持创造性
                max_retries=3
            )

        # 后处理：直接引用展开（不需要语义占位符）
        processed_data = self._process_direct_references(response_data, architecture_design)

        # 转换为ARXML
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

        return arxml_content, stats

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

    def _generate_deep_schema(
        self,
        component_plans: List[Dict[str, Any]],
        depth: int = 15
    ) -> Dict[str, Any]:
        """生成深度Schema - 增强版"""

        if CONFIG.debug_mode:
            print(f"[DEBUG] 生成深度Schema: depth={depth}")
            # 清理请求级缓存
            self.query_engine.clear_cache("request")

        # 利用query_engine生成深度Schema
        schema = self.query_engine.generate_multi_component_schema(
            component_plans,
            max_depth=depth  # 使用配置的深度
        )

        if not schema or not schema.get("properties"):
            raise ValidationError(f"Schema生成失败：无法生成深度{depth}的Schema")

        # 增强Schema以支持直接引用
        schema = self._enhance_schema_for_direct_references(schema)

        if CONFIG.debug_mode:
            properties_count = len(schema.get("properties", {}))
            print(f"[DEBUG] Schema生成成功: {properties_count}个组件定义")
            # 计算Schema复杂度
            complexity = self._calculate_schema_complexity(schema)
            print(f"[DEBUG] Schema复杂度: {complexity}")

        return schema

    def _enhance_schema_for_direct_references(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """增强Schema以支持直接引用（替代语义占位符）"""

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
        """查询完整的约束规则"""

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

    def _build_unified_prompt(
        self,
        architecture_design: ArchitectureDesign,
        constraints: List[str],
        memory_context: str,
        custom_requirements: Dict[str, Any],
        schema_depth: int
    ) -> str:
        """构建统一生成的提示词 - 优化版"""

        # 使用优化的模板
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

        # 添加直接引用示例
        prompt += self._add_direct_reference_examples(architecture_design)

        return prompt

    def _add_direct_reference_examples(self, architecture_design: ArchitectureDesign) -> str:
        """添加直接引用示例"""

        examples = """

## 直接引用示例

### 正确的引用格式：
- PROVIDED-INTERFACE-TREF: "/Interfaces/SensorDataInterface"
- REQUIRED-INTERFACE-TREF: "/Interfaces/ControlCommandInterface"
- START-ON-EVENT-REF: "/Components/TempMonitor/InternalBehavior/Runnables/ProcessData"
- PORT-PROTOTYPE-REF: "/Components/DataProcessor/Ports/DataInput"

### 组件间引用规则：
1. 使用绝对路径，从根开始
2. 路径分隔符使用 /
3. 遵循 /Category/Parent/Element 格式
4. 确保引用的元素确实存在
"""

        # 基于实际架构添加具体示例
        if architecture_design.component_plan:
            examples += "\n### 本系统的具体引用路径：\n"
            for comp in architecture_design.component_plan[:3]:  # 前3个组件作为示例
                comp_name = comp.get("name", "Component")
                examples += f"- 组件路径: /Components/{comp_name}\n"
                examples += f"- 端口路径: /Components/{comp_name}/Ports/PortName\n"
                examples += f"- Runnable路径: /Components/{comp_name}/InternalBehavior/Runnables/RunnableName\n"

        return examples

    def _process_direct_references(
        self,
        response_data: Dict[str, Any],
        architecture_design: ArchitectureDesign
    ) -> Dict[str, Any]:
        """处理直接引用 - 简化版"""

        # 由于使用直接引用，只需要验证引用的有效性
        processed_data = response_data.copy()

        # 验证并规范化引用路径
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

    def _convert_to_arxml(
        self,
        json_data: Dict[str, Any],
        architecture_design: ArchitectureDesign
    ) -> str:
        """转换JSON为ARXML格式 - 优化版"""

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

        # 确定组件类型元素名
        comp_type = comp_data.get("_type", "APPLICATION-SW-COMPONENT-TYPE")
        comp_element = SubElement(parent, comp_type)

        # 递归添加属性
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
        max_weight = CONFIG.batch_optimization.max_complexity_per_batch

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