"""core/round1_designer.py - Round 1架构设计器

执行第一轮对话：高层架构设计，确定组件类型、接口类型、连接关系
移除了冗余的函数调用，保留核心架构设计功能
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

# 条件导入文档处理器
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

        # 文档处理器
        self.document_processor = document_processor
        self.file_upload_enabled = CONFIG.llm.enable_file_upload and document_processor is not None

        # Round1不需要函数调用，但保留框架供未来扩展
        if CONFIG.debug_mode:
            if self.file_upload_enabled:
                print("[DEBUG] 文档上传功能已启用")
            else:
                print("[DEBUG] 运行在纯对话模式（文档上传已禁用）")
            print("[DEBUG] Round1使用纯结构化输出（无函数调用）")

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
        use_functions: bool = False  # 默认不使用函数调用
    ) -> Tuple[ArchitectureDesign, Dict[str, Any]]:
        """执行架构设计"""

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

            # Round1使用纯结构化输出（不使用函数调用）
            # 因为所需信息都已经在prompt中提供了
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
                },
                "complexity_assessment": {
                    "type": "string",
                    "description": "复杂度评估",
                    "enum": ["Simple", "Medium", "Complex"]
                }
            },
            "required": round1_config.output_schema.system_analysis.required_fields if round1_config.output_schema.system_analysis.required_fields else [
                "functional_decomposition", "data_flow_analysis"]
        }

        # 加载端口和事件类型配置 - 修正：使用属性访问而非字典访问
        port_types = round1_config.round1_element_design.port_types
        event_types = round1_config.round1_element_design.event_types
        # 加载RunnableEntity详细配置
        runnable_config = round1_config.runnable_entity_config

        # 构建element_design的schema - 更精细的结构
        element_design_schema = {
            "type": "object",
            "description": "LLM决定需要哪些具体元素",
            "properties": {
                "ports": {
                    "type": "object",
                    "properties": {
                        "needed": {"type": "boolean"},
                        "types": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": [pt.name for pt in port_types]  # 修正：使用.name属性访问
                            },
                            "description": "需要的具体端口类型"
                        },
                        "details": {"type": "string"}
                    }
                },
                "internal_behaviors": {
                    "type": "object",
                    "properties": {
                        "needed": {"type": "boolean"},
                        "events": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "type": {
                                        "type": "string",
                                        "enum": [et.name for et in event_types]  # 修正：使用.name属性访问
                                    },
                                    "name": {"type": "string"},
                                    "trigger": {"type": "string"}
                                }
                            },
                            "description": "需要的具体事件类型和配置"
                        },
                        "runnables": {
                        "type": "object",
                        "properties": {
                            "names": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Runnable实体名称列表"
                            },
                            "required_elements": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": runnable_config.required_elements
                                },
                                "description": "每个RunnableEntity必需的元素"
                            },
                            "optional_elements": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": runnable_config.optional_elements
                                },
                                "description": "每个RunnableEntity可选的元素"
                                }
                            }
                        }
                    }
                }
            }
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
                    "element_design": element_design_schema
                },
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

        # 添加AUTOSAR设计原则和规则（替代函数调用）
        context_parts.append("""
AUTOSAR设计原则:
- 分层架构: 应用层、RTE层、基础软件层
- 组件化设计: 功能封装在独立组件中
- 标准化接口: 使用标准AUTOSAR接口类型
- 可配置性: 支持不同ECU配置
- 可重用性: 组件可在不同项目中复用

接口兼容性规则:
- SENDER-RECEIVER接口: 用于异步数据传输，不能与CLIENT-SERVER直接连接
- CLIENT-SERVER接口: 用于同步服务调用，不能与SENDER-RECEIVER直接连接
- MODE-SWITCH接口: 用于模式切换和状态同步
- NV-DATA接口: 用于非易失性数据存储
- 相同类型的接口通常可以连接
- 不同类型的接口需要适配器组件

复杂度评估指南:
- Simple (简单): 1-5个组件，基础功能，少量接口
- Medium (中等): 6-15个组件，中等业务逻辑，适度的接口复杂度
- Complex (复杂): 16+个组件，复杂交互，状态机，实时约束
- 复杂度影响生成策略选择
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