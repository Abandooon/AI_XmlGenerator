"""core/round1_designer.py - Round 1架构设计器

执行第一轮对话：高层架构设计，确定组件类型、接口类型、连接关系
移除验证打分逻辑，专注于架构设计生成
"""
import json
from typing import Dict, List, Any, Optional, Tuple
from ..config import CONFIG
from ..llm.gemini_client import GeminiClient
from ..llm.prompt_templates import template_manager
from ..knowledge.terminology_builder import terminology_builder
from ..utils.serializers import ArchitectureDesign
from ..utils.exceptions import ArchitectureDesignError

class Round1Designer:
    """Round 1架构设计器"""

    def __init__(self):
        """初始化Round 1设计器"""
        self.gemini_client = GeminiClient()
        self.terminology = self._load_terminology_from_config()
        self.architecture_schema = self._build_architecture_schema()

    def design_architecture(
            self,
            user_requirements: str,
            design_context: str = "",
            memory_context: str = "",
            suggested_patterns: List[str] = None
    ) -> Tuple[ArchitectureDesign, Dict[str, Any]]:
        """执行架构设计"""

        try:
            # 准备设计上下文
            context = self._prepare_design_context(design_context, memory_context, suggested_patterns)

            # 获取术语库信息 - 修正访问方式
            component_types = [
                {
                    "name": ct.name,
                    "description": ct.description,
                    "scenarios": ct.scenarios,  # 修正：直接访问scenarios属性
                    "complexity": ct.complexity  # 修正：直接访问complexity属性
                }
                for ct in self.terminology["component_types"]
            ]

            interface_types = [
                {
                    "name": it.name,
                    "description": it.description,
                    "communication_mode": it.communication_mode,
                    "scenarios": it.scenarios  # 修正：直接访问scenarios属性
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

            # 调用LLM生成架构
            response_data, input_tokens, output_tokens, total_tokens = \
                self.gemini_client.generate_with_schema(
                    prompt=prompt,
                    schema=self.architecture_schema
                )

            # 解析响应并创建设计对象
            design = self._parse_response_to_design(response_data)

            # 生成统计信息
            stats = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "component_count": len(design.component_plan),
                "interface_count": len(design.interface_plan)
            }

            if CONFIG.debug_mode:
                print(f"[DEBUG] Round1完成: {len(design.component_plan)}个组件, {len(design.interface_plan)}个接口")

            return design, stats

        except Exception as e:
            raise ArchitectureDesignError(f"架构设计失败: {str(e)}")

    def _load_terminology_from_config(self) -> Dict[str, Any]:
        """从配置文件加载术语库"""
        return {
            "component_types": CONFIG.terminology.component_types,
            "interface_types": CONFIG.terminology.interface_types,
            "design_patterns": CONFIG.terminology.design_patterns
        }

    def analyze_requirements(self, user_requirements: str) -> Dict[str, Any]:
        """LLM驱动的需求分析，替换硬编码逻辑"""

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

    请根据需求分析，以JSON格式返回：
    {{
        "complexity_estimate": "Simple|Medium|Complex",
        "suggested_component_types": ["组件类型1", "组件类型2"],
        "suggested_interface_types": ["接口类型1", "接口类型2"],
        "suggested_patterns": ["模式1", "模式2"],
        "functional_analysis": "功能分析说明",
        "architectural_considerations": "架构考虑",
        "key_requirements": ["需求1", "需求2"]
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
                    }
                },
                "required": ["complexity_estimate", "suggested_component_types", "suggested_interface_types"]
            }

            response_data, _, _, _ = self.gemini_client.generate_with_schema(
                prompt=analysis_prompt,
                schema=analysis_schema
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
                "key_requirements": [user_requirements]
            }

    def _build_terminology_context(self) -> Dict[str, str]:
        """构建术语库上下文字符串"""

        context = {}

        # 组件类型上下文
        comp_context = []
        for comp_type in self.terminology["component_types"]:
            comp_context.append(f"""
    - {comp_type['name']}: {comp_type['description']}
      适用场景: {', '.join(comp_type['scenarios'])}
      复杂度: {comp_type['complexity']}""")
        context["component_types"] = "\n".join(comp_context)

        # 接口类型上下文
        intf_context = []
        for intf_type in self.terminology["interface_types"]:
            intf_context.append(f"""
    - {intf_type['name']}: {intf_type['description']}
      通信模式: {intf_type['communication_mode']}
      适用场景: {', '.join(intf_type['scenarios'])}""")
        context["interface_types"] = "\n".join(intf_context)

        # 设计模式上下文
        pattern_context = []
        for pattern in self.terminology["design_patterns"]:
            pattern_context.append(f"""
    - {pattern['name']}: 
      组件: {', '.join(pattern['components'])}
      接口: {', '.join(pattern['interfaces'])}
      适用场景: {', '.join(pattern['scenarios'])}""")
        context["design_patterns"] = "\n".join(pattern_context)

        return context

    def _build_architecture_schema(self) -> Dict[str, Any]:
        """构建架构设计的JSON Schema"""
        return {
            "type": "object",
            "properties": {
                "system_analysis": {
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
                        }
                    },
                    "required": ["functional_decomposition", "data_flow_analysis"]
                },
                "component_plan": {
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
                                "enum": ["APPLICATION-SW-COMPONENT-TYPE", "SENSOR-ACTUATOR-SW-COMPONENT-TYPE",
                                       "COMPOSITION-SW-COMPONENT-TYPE", "PARAMETER-SW-COMPONENT-TYPE"],
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
                                    "input_ports": {
                                        "type": "string",
                                        "description": "预估输入端口数量和类型"
                                    },
                                    "output_ports": {
                                        "type": "string",
                                        "description": "预估输出端口数量和类型"
                                    }
                                }
                            },
                            "behavioral_characteristics": {
                                "type": "string",
                                "description": "行为特征描述"
                            }
                        },
                        "required": ["component_id", "name", "type", "purpose"]
                    }
                },
                "interface_plan": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "interface_id": {
                                "type": "string",
                                "description": "接口唯一标识符"
                            },
                            "name": {
                                "type": "string",
                                "description": "接口名称"
                            },
                            "type": {
                                "type": "string",
                                "enum": ["SENDER-RECEIVER-INTERFACE", "CLIENT-SERVER-INTERFACE",
                                       "MODE-SWITCH-INTERFACE", "NV-DATA-INTERFACE"],
                                "description": "AUTOSAR接口类型"
                            },
                            "communication_pattern": {
                                "type": "string",
                                "description": "通信模式"
                            },
                            "data_category": {
                                "type": "string",
                                "description": "数据类别"
                            },
                            "connected_components": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "连接的组件ID列表"
                            },
                            "performance_requirements": {
                                "type": "string",
                                "description": "性能要求"
                            }
                        },
                        "required": ["interface_id", "name", "type", "communication_pattern"]
                    }
                },
                "connection_topology": {
                    "type": "object",
                    "properties": {
                        "component_connections": {
                            "type": "string",
                            "description": "组件间连接关系"
                        },
                        "data_flow_paths": {
                            "type": "string",
                            "description": "主要数据流路径"
                        },
                        "control_flow_paths": {
                            "type": "string",
                            "description": "控制流路径"
                        }
                    },
                    "required": ["component_connections", "data_flow_paths"]
                },
                "architecture_rationale": {
                    "type": "object",
                    "properties": {
                        "design_decisions": {
                            "type": "string",
                            "description": "关键设计决策及理由"
                        },
                        "tradeoff_analysis": {
                            "type": "string",
                            "description": "权衡分析"
                        },
                        "alternative_considerations": {
                            "type": "string",
                            "description": "考虑过的替代方案"
                        },
                        "risk_assessment": {
                            "type": "string",
                            "description": "潜在风险评估"
                        }
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
        suggested_patterns: List[str] = None
    ) -> str:
        """准备设计上下文"""
        context_parts = []

        if design_context:
            context_parts.append(f"设计背景: {design_context}")

        if memory_context:
            context_parts.append(f"对话历史: {memory_context}")

        if suggested_patterns:
            patterns_text = "\n".join([f"- {pattern}" for pattern in suggested_patterns])
            context_parts.append(f"建议的设计模式:\n{patterns_text}")

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