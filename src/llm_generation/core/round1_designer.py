"""core/round1_designer.py - Round 1架构设计器

执行第一轮对话：高层架构设计，确定组件类型、接口类型、连接关系
支持文档输入作为需求来源，集成函数调用功能
"""
import json
import uuid
from typing import Dict, List, Any, Optional, Tuple, Union
import google.generativeai as genai
from ..config import CONFIG
from ..llm.gemini_client import GeminiClient
from ..llm.prompt_templates import template_manager
from ..knowledge.terminology_builder import terminology_builder
from ..knowledge.dynamic_query_engine import query_engine
from ..knowledge.constraint_engine import constraint_engine
from ..utils.serializers import ArchitectureDesign
from ..utils.exceptions import ArchitectureDesignError
from ..utils.document_processor import document_processor

# 条件导入文档处理器 - 移到try块中避免导入错误
document_processor = None
if CONFIG.llm.enable_file_upload:
    try:
        from ..utils.document_processor import document_processor
        if CONFIG.debug_mode:
            print("[DEBUG] Document processor loaded successfully")
    except ImportError as e:
        if CONFIG.debug_mode:
            print(f"[WARNING] Document processor import failed: {e}")
        document_processor = None
else:
    if CONFIG.debug_mode:
        print("[DEBUG] Document upload disabled in config")

class Round1Designer:
    """Round 1架构设计器"""

    def __init__(self):
        """初始化Round 1设计器"""
        self.gemini_client = GeminiClient()
        self.terminology = self._load_terminology_from_config()
        self.architecture_schema = self._build_architecture_schema()

        # 只在启用文件上传时初始化文档处理器
        self.document_processor = document_processor
        self.file_upload_enabled = CONFIG.llm.enable_file_upload and document_processor is not None

        # 注册Round1函数
        self._register_round1_functions()

        if CONFIG.debug_mode:
            if self.file_upload_enabled:
                print("[DEBUG] 文档上传功能已启用")
            else:
                print("[DEBUG] 运行在纯对话模式（文档上传已禁用）")

    def _register_round1_functions(self):
        """注册Round1阶段的函数"""

        # 1. 查询已有组件函数
        self.gemini_client.register_function(
            name="query_existing_components",
            description="Query existing component types and patterns from knowledge base",
            parameters={
                "type": "object",
                "properties": {
                    "component_category": {
                        "type": "string",
                        "description": "Component category to query (e.g., APPLICATION, SENSOR, SERVICE)",
                        "enum": ["APPLICATION", "SENSOR", "SERVICE", "PARAMETER", "COMPOSITION", "ALL"]
                    },
                    "keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Keywords to filter components"
                    }
                },
                "required": ["component_category"]
            },
            implementation=self._query_existing_components_impl
        )

        # 2. 检查接口兼容性函数
        self.gemini_client.register_function(
            name="check_interface_compatibility",
            description="Check if two interface types are compatible for connection",
            parameters={
                "type": "object",
                "properties": {
                    "provider_interface": {
                        "type": "string",
                        "description": "Provider interface type"
                    },
                    "consumer_interface": {
                        "type": "string",
                        "description": "Consumer interface type"
                    },
                    "communication_pattern": {
                        "type": "string",
                        "description": "Expected communication pattern",
                        "enum": ["SENDER_RECEIVER", "CLIENT_SERVER", "MODE_SWITCH", "NV_DATA"]
                    }
                },
                "required": ["provider_interface", "consumer_interface"]
            },
            implementation=self._check_interface_compatibility_impl
        )

        # 3. 计算复杂度函数
        self.gemini_client.register_function(
            name="calculate_complexity",
            description="Calculate system complexity based on component and interface counts",
            parameters={
                "type": "object",
                "properties": {
                    "component_count": {
                        "type": "integer",
                        "description": "Number of components"
                    },
                    "interface_count": {
                        "type": "integer",
                        "description": "Number of interfaces"
                    },
                    "has_state_machine": {
                        "type": "boolean",
                        "description": "Whether system has state machines"
                    },
                    "has_real_time_constraints": {
                        "type": "boolean",
                        "description": "Whether system has real-time constraints"
                    }
                },
                "required": ["component_count", "interface_count"]
            },
            implementation=self._calculate_complexity_impl
        )

    def _query_existing_components_impl(
        self,
        component_category: str,
        keywords: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """查询已有组件的实现"""

        try:
            # 从知识图谱查询组件类型
            if query_engine.driver:
                with query_engine.driver.session() as session:
                    # 构建查询
                    if component_category == "ALL":
                        base_query = """
                        MATCH (c:Class)
                        WHERE c.xml_tag ENDS WITH '-SW-COMPONENT-TYPE'
                        """
                    else:
                        base_query = f"""
                        MATCH (c:Class)
                        WHERE c.xml_tag CONTAINS '{component_category}' 
                        AND c.xml_tag ENDS WITH '-SW-COMPONENT-TYPE'
                        """

                    # 添加关键词过滤
                    if keywords:
                        keyword_filter = " OR ".join([f"c.annotation CONTAINS '{kw}'" for kw in keywords])
                        base_query += f" AND ({keyword_filter})"

                    base_query += """
                    RETURN c.xml_tag as type, 
                           c.annotation as description,
                           c.isComplexType as is_complex
                    LIMIT 10
                    """

                    result = session.run(base_query)
                    components = []
                    for record in result:
                        components.append({
                            "type": record["type"],
                            "description": record.get("description", ""),
                            "is_complex": record.get("is_complex", False)
                        })

                    return {
                        "found": len(components),
                        "components": components,
                        "category": component_category
                    }

            # 降级到配置的组件类型
            filtered = []
            for comp_type in self.terminology["component_types"]:
                if component_category == "ALL" or component_category.upper() in comp_type.name.upper():
                    if not keywords or any(kw.lower() in comp_type.description.lower() for kw in keywords):
                        filtered.append({
                            "type": comp_type.name,
                            "description": comp_type.description,
                            "scenarios": comp_type.scenarios
                        })

            return {
                "found": len(filtered),
                "components": filtered[:10],
                "category": component_category,
                "source": "configuration"
            }

        except Exception as e:
            if CONFIG.debug_mode:
                print(f"[DEBUG] Component query failed: {e}")
            return {
                "found": 0,
                "components": [],
                "error": str(e)
            }

    def _check_interface_compatibility_impl(
        self,
        provider_interface: str,
        consumer_interface: str,
        communication_pattern: Optional[str] = None
    ) -> Dict[str, Any]:
        """检查接口兼容性的实现"""

        # 基本兼容性规则
        compatibility_rules = {
            "SENDER_RECEIVER": {
                "compatible_patterns": ["async", "broadcast", "multicast"],
                "incompatible_with": ["CLIENT_SERVER"]
            },
            "CLIENT_SERVER": {
                "compatible_patterns": ["sync", "request_response"],
                "incompatible_with": ["SENDER_RECEIVER"]
            },
            "MODE_SWITCH": {
                "compatible_patterns": ["state", "mode"],
                "incompatible_with": []
            },
            "NV_DATA": {
                "compatible_patterns": ["persistent", "storage"],
                "incompatible_with": []
            }
        }

        # 检查接口类型匹配
        is_compatible = True
        compatibility_notes = []

        # 相同接口类型通常兼容
        if provider_interface == consumer_interface:
            is_compatible = True
            compatibility_notes.append("Same interface type - generally compatible")

        # 检查通信模式
        if communication_pattern:
            pattern_rules = compatibility_rules.get(communication_pattern, {})

            # 检查不兼容的模式
            for incompatible in pattern_rules.get("incompatible_with", []):
                if incompatible in provider_interface or incompatible in consumer_interface:
                    is_compatible = False
                    compatibility_notes.append(f"Incompatible with {incompatible} pattern")

        # 特定接口类型检查
        if "SENDER" in provider_interface and "CLIENT" in consumer_interface:
            is_compatible = False
            compatibility_notes.append("Cannot connect sender-receiver to client-server")

        return {
            "compatible": is_compatible,
            "provider": provider_interface,
            "consumer": consumer_interface,
            "pattern": communication_pattern,
            "notes": compatibility_notes,
            "recommendation": "Consider using adapter component" if not is_compatible else "Direct connection possible"
        }

    def _calculate_complexity_impl(
        self,
        component_count: int,
        interface_count: int,
        has_state_machine: bool = False,
        has_real_time_constraints: bool = False
    ) -> Dict[str, Any]:
        """计算系统复杂度的实现"""

        # 基础复杂度评分
        base_score = component_count * 2 + interface_count

        # 状态机增加复杂度
        if has_state_machine:
            base_score += 5

        # 实时约束增加复杂度
        if has_real_time_constraints:
            base_score += 3

        # 确定复杂度级别
        if base_score <= 10:
            complexity_level = "Simple"
            batch_recommendation = "single_batch"
        elif base_score <= 30:
            complexity_level = "Medium"
            batch_recommendation = "type_based_batching"
        else:
            complexity_level = "Complex"
            batch_recommendation = "dependency_based_batching"

        # 生成建议
        recommendations = []
        if component_count > 15:
            recommendations.append("Consider decomposing into multiple subsystems")
        if interface_count > component_count * 3:
            recommendations.append("High interface density - review for potential simplification")
        if has_state_machine:
            recommendations.append("Include state machine documentation and transition rules")
        if has_real_time_constraints:
            recommendations.append("Define timing requirements and worst-case execution times")

        return {
            "complexity_score": base_score,
            "complexity_level": complexity_level,
            "component_count": component_count,
            "interface_count": interface_count,
            "batch_strategy": batch_recommendation,
            "recommendations": recommendations,
            "estimated_generation_time": f"{base_score * 2}-{base_score * 3} seconds"
        }

    def _load_terminology_from_config(self) -> Dict[str, Any]:
        """从配置文件加载术语库"""
        return {
            "component_types": CONFIG.terminology.component_types,
            "interface_types": CONFIG.terminology.interface_types,
            "design_patterns": CONFIG.terminology.design_patterns
        }

    def design_architecture(
            self,
            user_requirements: str,
            design_context: str = "",
            memory_context: str = "",
            suggested_patterns: List[str] = None,
            document_files: Optional[Union[str, List[str]]] = None,
            use_functions: bool = True
    ) -> Tuple[ArchitectureDesign, Dict[str, Any]]:
        """执行架构设计 - 完整版本"""

        try:
            # 处理文档上传（只在启用且有文档时）
            uploaded_files = None
            document_content = ""

            if document_files and self.file_upload_enabled:
                if CONFIG.debug_mode:
                    print(f"[DEBUG] 处理上传的文档...")

                # 确保是列表
                if isinstance(document_files, str):
                    document_files = [document_files]

                # 上传文档
                uploaded_files = []
                for file_path in document_files:
                    try:
                        file_obj = self.document_processor.upload_file(file_path)
                        if file_obj:
                            uploaded_files.append(file_obj)
                            # 提取文档内容摘要
                            content = self.document_processor.extract_document_content(file_obj)
                            document_content += f"\n\n文档 {file_obj.display_name} 内容摘要:\n{content}"
                    except Exception as e:
                        if CONFIG.debug_mode:
                            print(f"[WARNING] 上传文档失败 {file_path}: {e}")
                        continue

                if CONFIG.debug_mode:
                    print(f"[DEBUG] 成功上传 {len(uploaded_files)} 个文档")

            elif document_files and not self.file_upload_enabled:
                if CONFIG.debug_mode:
                    print("[WARNING] 文档上传功能未启用，忽略文档输入")

            # 准备设计上下文，包含文档内容
            context = self._prepare_design_context(
                design_context,
                memory_context,
                suggested_patterns,
                document_content
            )

            # 获取术语库信息
            component_types = [
                {
                    "name": ct.name,
                    "description": ct.description,
                    "scenarios": ct.scenarios,
                    "complexity": ct.complexity
                }
                for ct in self.terminology["component_types"]
            ]

            interface_types = [
                {
                    "name": it.name,
                    "description": it.description,
                    "communication_mode": it.communication_mode,
                    "scenarios": it.scenarios
                }
                for it in self.terminology["interface_types"]
            ]

            # 生成提示词
            prompt = template_manager.get_round1_prompt(
                user_requirements=user_requirements,
                design_context=context,
                component_types=component_types,
                interface_types=interface_types
            )

            if CONFIG.debug_mode:
                print(f"[DEBUG] Round1 提示词长度: {len(prompt)}")
                if uploaded_files:
                    print(f"[DEBUG] 包含 {len(uploaded_files)} 个文档文件")
                print(f"[DEBUG] 函数调用: {'启用' if use_functions else '禁用'}")

            # 调用LLM生成架构
            if use_functions:
                # 使用函数调用增强的生成
                response_data, function_calls, input_tokens, output_tokens, total_tokens = \
                    self.gemini_client.generate_with_schema_and_functions(
                        prompt=prompt,
                        schema=self.architecture_schema,
                        functions=["query_existing_components", "check_interface_compatibility", "calculate_complexity"],
                        document_files=uploaded_files
                    )
            else:
                # 普通生成（向后兼容）
                response_data, input_tokens, output_tokens, total_tokens = \
                    self.gemini_client.generate_with_schema(
                        prompt=prompt,
                        schema=self.architecture_schema,
                        document_files=uploaded_files
                    )
                function_calls = {}

            # 验证响应格式
            from ..utils.validators import validate_architecture_design
            is_valid, errors = validate_architecture_design(response_data)
            if not is_valid and CONFIG.debug_mode:
                print(f"[DEBUG] 架构设计验证警告: {errors[:3]}")

            # 解析响应并创建设计对象
            design = self._parse_response_to_design(response_data)

            # 生成统计信息
            stats = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "component_count": len(design.component_plan),
                "interface_count": len(design.interface_plan),
                "validation_passed": is_valid,
                "validation_errors": len(errors) if not is_valid else 0,
                "documents_processed": len(uploaded_files) if uploaded_files else 0,
                "functions_called": len(function_calls),
                "function_details": function_calls
            }

            if CONFIG.debug_mode:
                print(f"[DEBUG] Round1完成: {len(design.component_plan)}个组件, "
                      f"{len(design.interface_plan)}个接口, 验证{'通过' if is_valid else '有警告'}")
                if function_calls:
                    print(f"[DEBUG] 调用了 {len(function_calls)} 个函数")

            return design, stats

        except Exception as e:
            raise ArchitectureDesignError(f"架构设计失败: {str(e)}")

    # 保留原有的其他方法...（省略未修改的方法）

    def _build_architecture_schema(self) -> Dict[str, Any]:
        """从配置构建架构设计的JSON Schema"""

        # 从配置加载schema定义
        round1_config = CONFIG.round1_schema

        # 构建system_analysis的schema
        system_analysis_schema = {
            "type": "object",
            "properties": {
                "functional_decomposition": {
                    "type": "string",
                    "description": "功能分解和职责划分"
                },
                "data_flow_analysis": {
                    "type": "string",
                    "description": "数据流分析"
                },
                "timing_requirements": {
                    "type": "string",
                    "description": "时序要求分析"
                },
                "scalability_considerations": {
                    "type": "string",
                    "description": "可扩展性考虑"
                },
                "document_based_requirements": {
                    "type": "string",
                    "description": "基于文档的需求分析"
                }
            },
            # 使用正确的访问路径
            "required": round1_config.output_schema.system_analysis.required_fields if round1_config.output_schema.system_analysis.required_fields else [
                "functional_decomposition", "data_flow_analysis"]
        }

        # 构建component_plan的schema
        component_plan_schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "component_id": {
                        "type": "string",
                        "description": "组件唯一标识符"
                    },
                    "name": {
                        "type": "string",
                        "description": "组件名称"
                    },
                    "type": {
                        "type": "string",
                        # 使用组件类型配置中的allowed_types
                        "enum": round1_config.component_types.allowed_types if round1_config.component_types.allowed_types else [
                            "APPLICATION-SW-COMPONENT-TYPE",
                            "SENSOR-ACTUATOR-SW-COMPONENT-TYPE",
                            "COMPLEX-DEVICE-DRIVER-SW-COMPONENT-TYPE",
                            "ECU-ABSTRACTION-SW-COMPONENT-TYPE",
                            "NV-BLOCK-SW-COMPONENT-TYPE",
                            "SERVICE-PROXY-SW-COMPONENT-TYPE",
                            "SERVICE-SW-COMPONENT-TYPE",
                            "COMPOSITION-SW-COMPONENT-TYPE",
                            "PARAMETER-SW-COMPONENT-TYPE"
                        ],
                        "description": "AUTOSAR组件类型"
                    },
                    "purpose": {
                        "type": "string",
                        "description": "功能目的和职责"
                    },
                    "estimated_complexity": {
                        "type": "string",
                        "enum": ["Simple", "Medium", "Complex"],
                        "description": "复杂度评估"
                    },
                    "port_estimates": {
                        "type": "object",
                        "properties": {
                            "input_ports": {"type": "string"},
                            "output_ports": {"type": "string"}
                        }
                    },
                    "behavioral_characteristics": {
                        "type": "string",
                        "description": "行为特征描述"
                    },
                    # 新增：元素设计规划
                    "element_design": {
                        "type": "object",
                        "description": "LLM规划的元素使用",
                        "properties": {
                            "ports": {
                                "type": "object",
                                "properties": {
                                    "needed": {"type": "boolean"},
                                    "details": {"type": "string"}
                                }
                            },
                            "internal_behaviors": {
                                "type": "object",
                                "properties": {
                                    "needed": {"type": "boolean"},
                                    "runnables": {"type": "array", "items": {"type": "string"}},
                                    "events": {"type": "array", "items": {"type": "string"}}
                                }
                            }
                        }
                    }
                },
                # 使用输出schema配置中的required_fields
                "required": round1_config.output_schema.component_plan.required_fields if round1_config.output_schema.component_plan.required_fields else [
                    "component_id", "name", "type", "purpose"
                ]
            }
        }

        # 构建interface_plan的schema
        interface_plan_schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "interface_id": {"type": "string"},
                    "name": {"type": "string"},
                    "type": {
                        "type": "string",
                        # 使用接口类型配置中的allowed_types
                        "enum": round1_config.interface_types.allowed_types if round1_config.interface_types.allowed_types else [
                            "SENDER-RECEIVER-INTERFACE",
                            "CLIENT-SERVER-INTERFACE",
                            "MODE-SWITCH-INTERFACE",
                            "NV-DATA-INTERFACE",
                            "PARAMETER-INTERFACE",
                            "TRIGGER-INTERFACE"
                        ]
                    },
                    "communication_pattern": {"type": "string"},
                    "data_category": {"type": "string"},
                    "connected_components": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "performance_requirements": {"type": "string"}
                },
                # 使用输出schema配置中的required_fields
                "required": round1_config.output_schema.interface_plan.required_fields if round1_config.output_schema.interface_plan.required_fields else [
                    "interface_id", "name", "type", "communication_pattern"
                ]
            }
        }

        # 组装完整schema
        return {
            "type": "object",
            "properties": {
                "system_analysis": system_analysis_schema,
                "component_plan": component_plan_schema,
                "interface_plan": interface_plan_schema,
                "connection_topology": {
                    "type": "object",
                    "properties": {
                        "component_connections": {"type": "string"},
                        "data_flow_paths": {"type": "string"},
                        "control_flow_paths": {"type": "string"}
                    },
                    "required": ["component_connections", "data_flow_paths"]
                },
                "architecture_rationale": {
                    "type": "object",
                    "properties": {
                        "design_decisions": {"type": "string"},
                        "tradeoff_analysis": {"type": "string"},
                        "alternative_considerations": {"type": "string"},
                        "risk_assessment": {"type": "string"}
                    },
                    "required": ["design_decisions"]
                }
            },
            "required": ["system_analysis", "component_plan", "interface_plan",
                         "connection_topology", "architecture_rationale"]
        }

    def _prepare_design_context(
        self,
        design_context: str,
        memory_context: str,
        suggested_patterns: List[str] = None,
        document_content: str = ""
    ) -> str:
        """准备设计上下文，包含文档内容"""
        context_parts = []

        if design_context:
            context_parts.append(f"设计背景: {design_context}")

        if memory_context:
            context_parts.append(f"对话历史: {memory_context}")

        if suggested_patterns:
            patterns_text = "\n".join([f"- {pattern}" for pattern in suggested_patterns])
            context_parts.append(f"建议的设计模式:\n{patterns_text}")

        if document_content:
            context_parts.append(f"文档分析结果:\n{document_content}")

        # 添加AUTOSAR设计原则
        context_parts.append("""
AUTOSAR设计原则:
- 分层架构: 应用层、RTE层、基础软件层
- 组件化设计: 功能封装在独立组件中
- 标准化接口: 使用标准AUTOSAR接口类型
- 可配置性: 支持不同ECU配置
- 可重用性: 组件可在不同项目中复用
""")

        return "\n\n".join(context_parts)

    def _parse_response_to_design(self, response_data: Dict[str, Any]) -> ArchitectureDesign:
        """解析LLM响应并创建设计对象"""

        # 创建ArchitectureDesign对象
        design = ArchitectureDesign(
            system_analysis=response_data.get("system_analysis", {}),
            component_plan=response_data.get("component_plan", []),
            interface_plan=response_data.get("interface_plan", []),
            connection_topology=response_data.get("connection_topology", {}),
            architecture_rationale=response_data.get("architecture_rationale", {})
        )

        return design


# 全局Round1设计器实例
round1_designer = Round1Designer()