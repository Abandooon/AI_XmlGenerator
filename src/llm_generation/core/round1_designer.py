"""core/round1_designer.py - Round 1架构设计器

执行第一轮对话：高层架构设计，确定组件类型、接口类型、连接关系
支持文档输入作为需求来源
"""
import json
from typing import Dict, List, Any, Optional, Tuple, Union
import google.generativeai as genai
from ..config import CONFIG
from ..llm.gemini_client import GeminiClient
from ..llm.prompt_templates import template_manager
from ..knowledge.terminology_builder import terminology_builder
from ..utils.serializers import ArchitectureDesign
from ..utils.exceptions import ArchitectureDesignError
from ..utils.document_processor import document_processor


class Round1Designer:
    """Round 1架构设计器"""

    def __init__(self):
        """初始化Round 1设计器"""
        self.gemini_client = GeminiClient()
        self.terminology = self._load_terminology_from_config()
        self.architecture_schema = self._build_architecture_schema()
        self.document_processor = document_processor

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
            document_files: Optional[Union[str, List[str]]] = None
    ) -> Tuple[ArchitectureDesign, Dict[str, Any]]:
        """执行架构设计，支持文档输入

        Args:
            user_requirements: 用户需求描述
            design_context: 设计上下文
            memory_context: 对话记忆上下文
            suggested_patterns: 建议的设计模式
            document_files: 文档文件路径（支持单个或列表）

        Returns:
            (架构设计对象, 统计信息)
        """

        try:
            # 处理文档上传
            uploaded_files = None
            document_content = ""

            if document_files:
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

            # 准备设计上下文，包含文档内容
            context = self._prepare_design_context(
                design_context,
                memory_context,
                suggested_patterns,
                document_content
            )

            # 获取术语库信息 - 修正访问方式
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

            # 调用LLM生成架构，包含文档
            response_data, input_tokens, output_tokens, total_tokens = \
                self.gemini_client.generate_with_schema(
                    prompt=prompt,
                    schema=self.architecture_schema,
                    document_files=uploaded_files
                )

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
                "documents_processed": len(uploaded_files) if uploaded_files else 0
            }

            if CONFIG.debug_mode:
                print(f"[DEBUG] Round1完成: {len(design.component_plan)}个组件, "
                      f"{len(design.interface_plan)}个接口, 验证{'通过' if is_valid else '有警告'}")

            return design, stats

        except Exception as e:
            raise ArchitectureDesignError(f"架构设计失败: {str(e)}")

    def _build_terminology_context(self) -> Dict[str, str]:
        """构建术语库上下文字符串"""

        context = {}

        # 组件类型上下文
        comp_context = []
        for comp_type in self.terminology["component_types"]:
            comp_context.append(f"""
    - {comp_type.name}: {comp_type.description}
      适用场景: {', '.join(comp_type.scenarios)}
      复杂度: {comp_type.complexity}""")
        context["component_types"] = "\n".join(comp_context)

        # 接口类型上下文
        intf_context = []
        for intf_type in self.terminology["interface_types"]:
            intf_context.append(f"""
    - {intf_type.name}: {intf_type.description}
      通信模式: {intf_type.communication_mode}
      适用场景: {', '.join(intf_type.scenarios)}""")
        context["interface_types"] = "\n".join(intf_context)

        # 设计模式上下文
        pattern_context = []
        for pattern in self.terminology["design_patterns"]:
            pattern_context.append(f"""
    - {pattern.name}: 
      组件: {', '.join(pattern.components)}
      接口: {', '.join(pattern.interfaces)}
      适用场景: {', '.join(pattern.scenarios)}""")
        context["design_patterns"] = "\n".join(pattern_context)

        return context

    def analyze_requirements(
        self,
        user_requirements: str,
        document_files: Optional[Union[str, List[str]]] = None
    ) -> Dict[str, Any]:
        """LLM驱动的需求分析，支持文档输入"""

        # 处理文档上传
        uploaded_files = None
        if document_files:
            if isinstance(document_files, str):
                document_files = [document_files]

            uploaded_files = []
            for file_path in document_files:
                try:
                    file_obj = self.document_processor.upload_file(file_path)
                    if file_obj:
                        uploaded_files.append(file_obj)
                except Exception as e:
                    if CONFIG.debug_mode:
                        print(f"[WARNING] 上传文档失败 {file_path}: {e}")

        # 构建术语库上下文
        terminology_context = self._build_terminology_context()

        analysis_prompt = f"""
    作为AUTOSAR系统分析专家，请分析以下用户需求并给出结构化的分析结果。

    ## 用户需求
    {user_requirements}

    ## 可用的AUTOSAR组件类型
    {terminology_context['component_types']}

    ## 可用的AUTOSAR接口类型  
    {terminology_context['interface_types']}

    ## 常见设计模式
    {terminology_context['design_patterns']}

    请根据需求分析（如有文档请优先参考文档内容），以JSON格式返回：
    {{
        "complexity_estimate": "Simple|Medium|Complex",
        "suggested_component_types": ["组件类型1", "组件类型2"],
        "suggested_interface_types": ["接口类型1", "接口类型2"],
        "suggested_patterns": ["模式1", "模式2"],
        "functional_analysis": "功能分析说明",
        "architectural_considerations": "架构考虑",
        "key_requirements": ["需求1", "需求2"],
        "document_insights": "从文档中提取的关键信息（如有）"
    }}
    """

        try:
            # 使用JSON模式确保结构化输出
            analysis_schema = {
                "type": "object",
                "properties": {
                    "complexity_estimate": {
                        "type": "string",
                        "enum": ["Simple", "Medium", "Complex"]
                    },
                    "suggested_component_types": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "suggested_interface_types": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "suggested_patterns": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "functional_analysis": {"type": "string"},
                    "architectural_considerations": {"type": "string"},
                    "key_requirements": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "document_insights": {"type": "string"}
                },
                "required": ["complexity_estimate", "suggested_component_types", "suggested_interface_types"]
            }

            response_data, _, _, _ = self.gemini_client.generate_with_schema(
                prompt=analysis_prompt,
                schema=analysis_schema,
                document_files=uploaded_files
            )

            return response_data

        except Exception as e:
            if CONFIG.debug_mode:
                print(f"[DEBUG] LLM需求分析失败: {e}")

            # 降级为基础分析
            return {
                "complexity_estimate": "Medium",
                "suggested_component_types": ["APPLICATION-SW-COMPONENT-TYPE"],
                "suggested_interface_types": ["SENDER-RECEIVER-INTERFACE"],
                "suggested_patterns": [],
                "functional_analysis": "需求分析失败，使用默认配置",
                "architectural_considerations": "基于通用AUTOSAR架构",
                "key_requirements": [user_requirements],
                "document_insights": "无文档分析结果"
            }


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
            "required": round1_config.system_analysis.required
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
                        "enum": round1_config.component_plan.allowed_types,
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
                "required": round1_config.component_plan.required_fields
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
                        "enum": round1_config.interface_plan.allowed_types
                    },
                    "communication_pattern": {"type": "string"},
                    "data_category": {"type": "string"},
                    "connected_components": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "performance_requirements": {"type": "string"}
                },
                "required": round1_config.interface_plan.required_fields
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

    def suggest_design_patterns(self, user_requirements: str) -> List[str]:
        """根据用户需求建议设计模式"""
        patterns = self.terminology.suggest_patterns_for_scenario(user_requirements)
        return [pattern.name for pattern in patterns]


# 全局Round1设计器实例
round1_designer = Round1Designer()