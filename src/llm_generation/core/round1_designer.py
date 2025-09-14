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
from datetime import datetime
from pathlib import Path

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

            # 获取术语库信息（可选说明用）
            # component_types_termino = [
            #     {
            #         "name": ct.name,
            #         "description": ct.description,
            #         "scenarios": ct.scenarios,
            #         "complexity": ct.complexity
            #     }
            #     for ct in self.terminology["component_types"]
            # ]
            #
            # interface_types_termino = [
            #     {
            #         "name": it.name,
            #         "description": it.description,
            #         "communication_mode": it.communication_mode,
            #         "scenarios": it.scenarios
            #     }
            #     for it in self.terminology["interface_types"]
            # ]

            # —— 来自 config.round1_schema 的“允许枚举”（主信息源，用于提示&对齐 schema）
            ct_allowed = (CONFIG.round1_schema.component_types.allowed_types
                          if CONFIG.round1_schema.component_types.allowed_types else [
                "APPLICATION-SW-COMPONENT-TYPE",
                "SENSOR-ACTUATOR-SW-COMPONENT-TYPE",
                "COMPLEX-DEVICE-DRIVER-SW-COMPONENT-TYPE",
                "ECU-ABSTRACTION-SW-COMPONENT-TYPE",
                "NV-BLOCK-SW-COMPONENT-TYPE",
                "SERVICE-PROXY-SW-COMPONENT-TYPE",
                "SERVICE-SW-COMPONENT-TYPE",
                "COMPOSITION-SW-COMPONENT-TYPE",
                "PARAMETER-SW-COMPONENT-TYPE"
            ])

            it_allowed = (CONFIG.round1_schema.interface_types.allowed_types
                          if CONFIG.round1_schema.interface_types.allowed_types else [
                "SENDER-RECEIVER-INTERFACE",
                "CLIENT-SERVER-INTERFACE",
                "MODE-SWITCH-INTERFACE",
                "NV-DATA-INTERFACE",
                "PARAMETER-INTERFACE",
                "TRIGGER-INTERFACE"
            ])

            # 生成提示词（把 schema 也放进提示）
            prompt = template_manager.get_round1_prompt(
                user_requirements=user_requirements,
                design_context=context,
                component_types_allowed=ct_allowed,  # ← 主信息源：来自 config
                interface_types_allowed=it_allowed,  # ← 主信息源：来自 config
                architecture_schema=self.architecture_schema  # ← 明确内嵌 JSON Schema
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
            saved_file = self.save_round1_data(
                prompt=prompt,
                response_data=response_data,
                design=design,
                stats=stats,
                user_requirements=user_requirements
            )
            stats["saved_file"] = str(saved_file)

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
        # ---------- 元素目录 & “联合预选”枚举 ----------
        runnable_config = round1_config.runnable_entity_config
        if getattr(runnable_config, "elements", None):
            elem_keys = [e.key for e in runnable_config.elements]
        else:
            elem_keys = list(dict.fromkeys(
                (runnable_config.required_elements or []) + (runnable_config.optional_elements or [])
            ))

        # 从配置编译 union → variants / variant → selectable_children
        preselect_cfg = getattr(round1_config, "preselect", None)
        union_variants_map: Dict[str, List[str]] = {}
        variant_children_map: Dict[str, List[str]] = {}
        union_card_map: Dict[str, Dict[str, int]] = {}
        if preselect_cfg and getattr(preselect_cfg, "unions", None):
            for u in preselect_cfg.unions:
                union_variants_map[u.of] = [b.name for b in u.variants]
                union_card_map[u.of] = {"min": u.min_select, "max": u.max_select}
                for b in u.variants:
                    variant_children_map[b.name] = b.selectable_children or []

        # 统一枚举列表（Gemini 不支持跨字段动态枚举，就给出全集合，靠提示词与后处理校验）
        all_union_names = sorted(list(union_variants_map.keys()))
        all_variant_names = sorted({v for vs in union_variants_map.values() for v in vs})

        # ---------- 元素选择对象（关键：在 Round1 确定性选择 include） ----------
        element_selection_schema = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "key": {"type": "string", "enum": elem_keys},  # 例如 "VariableAccess" / "ServerCallPoints" ...
                "wrapper": {"type": "string"},  # 可选：若位于某 wrapper（如 SERVER-CALL-POINTS / DATA-SEND-POINTS）
                "preselect": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "of": {"type": "string", "enum": all_union_names},  # 比如 "ACCESSED-VARIABLE"
                            "variant": {"type": "string", "enum": all_variant_names},  # 比如 "AUTOSAR-VARIABLE-IREF"
                            # Round1 在这里“确定性选择”schema 需要生成的子键，而不是仅提示
                            "include": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "从配置的 selectable_children 中精确选择这次要生成 Schema 的子键（确定性选择）",
                                # 给 LLM 的提示性信息（非校验）
                                "x-allowed-children": variant_children_map
                            },
                            "notes": {"type": "string"}
                        },
                        "required": ["of", "variant", "include"]
                    },
                    "description": "在该元素内部的联合位置进行分支与子键的确定性选择"
                },
                "notes": {"type": "string"}
            },
            "required": ["key"]
        }

        # ---------- element_design_schema ----------
        element_design_schema = {
            "type": "object",
            "description": "LLM决定需要哪些具体元素（含联合分支与子键的确定性选择）",
            "additionalProperties": False,
            "properties": {
                "ports": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "needed": {"type": "boolean"},
                        "types": {
                            "type": "array",
                            "items": {"type": "string", "enum": [pt.name for pt in port_types]},
                            "description": "需要的具体端口类型"
                        },
                        "details": {"type": "string"}
                    },
                    "allOf": [
                        {"if": {"properties": {"needed": {"const": True}}}, "then": {"required": ["types"]}}
                    ]
                },
                "internal_behaviors": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "needed": {"type": "boolean"},
                        "events": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "type": {"type": "string", "enum": [et.name for et in event_types]},
                                    "name": {"type": "string"},
                                    "trigger": {"type": "string"}
                                },
                                "required": ["type", "name"]
                            },
                            "description": "需要的具体事件类型和配置"
                        },
                        "runnables": {
                            "type": "array",
                            "minItems": 1,
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "name": {"type": "string", "description": "Runnable 实体名"},
                                    "elements": {
                                        "type": "array",
                                        "items": element_selection_schema,
                                        "description": "该 Runnable 需要的深层元素（结构化 & 确定性 include）"
                                    },
                                    "notes": {"type": "string"}
                                },
                                "required": ["name"]
                            },
                            "description": "每个 runnable 选择所需的深层元素，并给出联合与子键的确定性选择"
                        }
                    },
                    "allOf": [
                        {"if": {"properties": {"needed": {"const": True}}},
                         "then": {"required": ["runnables"]}}
                    ]
                }
            }
        }

        # 构建component_plan的schema
        component_plan_schema = {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
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
                    "element_design": element_design_schema,
                    "direct_references": {"type": "array", "items": {"type": "string"}}
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
                "additionalProperties": False,
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
                    "performance_requirements": {"type": "string"},
                    "data_elements": {"type": "array", "items": {"type": "string"}},
                    "direct_paths": {"type": "string"}
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

    def save_round1_data(self,
                         prompt: str,
                         response_data: Dict[str, Any],
                         design: ArchitectureDesign,
                         stats: Dict[str, Any],
                         user_requirements: str = "",
                         save_dir: Optional[Path] = None) -> Path:
        """保存Round1的prompt和输出数据"""

        # 确定保存目录
        if save_dir is None:
            save_dir = CONFIG.output_dir / "round1_data"
        save_dir.mkdir(parents=True, exist_ok=True)

        # 生成时间戳文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = f"round1_{timestamp}"

        # 准备保存数据
        round1_data = {
            "session_id": session_id,
            "timestamp": timestamp,
            "user_requirements": user_requirements,
            "prompt": prompt,
            "response_data": response_data,
            "design": {
                "system_analysis": design.system_analysis,
                "component_plan": design.component_plan,
                "interface_plan": design.interface_plan,
                "connection_topology": design.connection_topology,
                "architecture_rationale": design.architecture_rationale
            },
            "stats": stats,
            "config": {
                "model": CONFIG.llm.model_name,
                "temperature": CONFIG.llm.temperature,
                "max_output_tokens": CONFIG.llm.max_output_tokens
            }
        }

        # 保存JSON文件
        output_file = save_dir / f"{session_id}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(round1_data, f, indent=2, ensure_ascii=False)

        if CONFIG.debug_mode:
            print(f"[DEBUG] Round1数据已保存到: {output_file}")

        return output_file


# 全局Round1设计器实例
round1_designer = Round1Designer()