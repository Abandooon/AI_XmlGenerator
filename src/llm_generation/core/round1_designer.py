"""core/round1_designer.py - Round 1架构设计器

执行第一轮对话：高层架构设计，确定组件类型、接口类型、连接关系
移除了冗余的函数调用，保留核心架构设计功能
"""
import json
import uuid
from typing import Dict, List, Any, Optional, Tuple, Union
import google.generativeai as genai
from ..config import CONFIG
from ..llm.openai_client import OpenAIClient as GeminiClient
# from ..llm.gemini_client import GeminiClient
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
        """从配置构建 Round1 架构设计的 JSON Schema（strict & 无组合关键字）"""

        round1_config = CONFIG.round1_schema

        # --- 小助手：可能空的枚举 → 回退成普通 string，避免 enum:[]
        def _enum_or_string(values, desc: str = None):
            vals = sorted({v for v in (values or []) if v})
            if vals:
                return {"type": "string", "enum": vals}
            out = {"type": "string"}
            if desc:
                out["description"] = f"{desc}（未配置枚举，允许任意字符串）"
            return out

        # 端口/事件类型（可能为空）
        port_types = getattr(round1_config.round1_element_design, "port_types", None)
        event_types = getattr(round1_config.round1_element_design, "event_types", None)
        port_type_names = [pt.name for pt in port_types] if port_types else []
        event_type_names = [et.name for et in event_types] if event_types else []

        # Runnable 元素 key（可能为空）
        runnable_cfg = round1_config.runnable_entity_config
        if getattr(runnable_cfg, "elements", None):
            elem_keys = [e.key for e in runnable_cfg.elements]
        else:
            elem_keys = list(dict.fromkeys(
                (runnable_cfg.required_elements or []) + (runnable_cfg.optional_elements or [])
            ))

        # preselect unions（仅用于提示，不再把枚举强压进 schema）
        preselect_cfg = getattr(round1_config, "preselect", None)
        variant_children_map: Dict[str, List[str]] = {}
        if preselect_cfg and getattr(preselect_cfg, "unions", None):
            for u in preselect_cfg.unions:
                for b in (u.variants or []):
                    variant_children_map[b.name] = list(b.selectable_children or [])

        # ---------------- system_analysis ----------------
        system_analysis_schema = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "functional_decomposition": {"type": "string", "description": "功能分解和职责划分"},
                "data_flow_analysis": {"type": "string", "description": "数据流分析"},
                "timing_requirements": {"type": "string", "description": "时序要求分析"},
                "scalability_considerations": {"type": "string", "description": "可扩展性考虑"},
                "complexity_assessment": {
                    "type": "string",
                    "description": "复杂度评估",
                    "enum": ["Simple", "Medium", "Complex"]
                }
            },
            "required": [
                "functional_decomposition",
                "data_flow_analysis",
                "timing_requirements",
                "scalability_considerations",
                "complexity_assessment"
            ]
        }

        # ---------------- element_selection（元素选择，含 preselect） ----------------
        element_selection_schema = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                # 元素 key：可能为空 → 回退为 string；有枚举时给 enum
                "key": _enum_or_string(elem_keys, "元素键（如 SERVER-CALL-POINTS / DATA-RECEIVE-POINT-BY-ARGUMENTS）"),
                "wrapper": {"type": "string"},
                "preselect": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            # of/variant 直接用 string，避免“配置未加载好时的空枚举 400”
                            "of": {"type": "string"},
                            "variant": {"type": "string"},
                            "include": {
                                "type": "array",
                                "items": {"type": "string"},
                                "minItems": 1,
                                "description": "从配置的 selectable_children 中精确选择本次要生成 Schema 的子键（确定性选择）",
                                # 仅作提示，不参与校验
                                "x-allowed-children": variant_children_map
                            },
                            "notes": {"type": "string"}
                        },
                        "required": ["of", "variant", "include", "notes"]
                    },
                    "description": "在该元素内部的联合位置进行分支与子键的确定性选择"
                },
                "notes": {"type": "string"}
            },
            "required": ["key", "wrapper", "preselect", "notes"]
        }

        # ---------------- element_design（ports / internal_behaviors） ----------------
        element_design_schema = {
            "type": "object",
            "description": "LLM 决定需要哪些具体元素（含联合分支与子键的确定性选择）",
            "additionalProperties": False,
            "properties": {
                "ports": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "needed": {"type": "boolean"},
                        "types": {
                            "type": "array",
                            # 严格模式下不做条件：统一出现；needed=false 时等于 []
                            "minItems": 0,
                            "items": _enum_or_string(port_type_names, "端口类型"),
                            "description": "当 needed=false 时应为空数组；needed=true 时给出需要的端口类型集合"
                        },
                        "details": {"type": "string"}
                    },
                    "required": ["needed", "types", "details"]
                },
                "internal_behaviors": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "needed": {"type": "boolean"},
                        "events": {
                            "type": "array",
                            "minItems": 0,  # needed=false → []
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "type": _enum_or_string(event_type_names, "事件类型"),
                                    "name": {"type": "string"},
                                    "trigger": {"type": "string"}
                                },
                                "required": ["type", "name", "trigger"]
                            },
                            "description": "当 needed=false 时应为空数组"
                        },
                        "runnables": {
                            "type": "array",
                            "minItems": 0,  # needed=false → []
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "name": {"type": "string", "description": "Runnable 实体名"},
                                    "elements": {
                                        "type": "array",
                                        "minItems": 1,
                                        "items": element_selection_schema,
                                        "description": "该 Runnable 需要的深层元素（结构化 & 确定性 include）"
                                    },
                                    "notes": {"type": "string"}
                                },
                                "required": ["name", "elements", "notes"]
                            },
                            "description": "每个 runnable 选择所需的深层元素，并给出联合与子键的确定性选择"
                        }
                    },
                    "required": ["needed", "events", "runnables"]
                }
            },
            "required": ["ports", "internal_behaviors"]
        }

        # ---------------- component_plan ----------------
        component_type_enum = (
            round1_config.component_types.allowed_types
            if round1_config.component_types.allowed_types else [
                "APPLICATION-SW-COMPONENT-TYPE",
                "SENSOR-ACTUATOR-SW-COMPONENT-TYPE",
                "COMPLEX-DEVICE-DRIVER-SW-COMPONENT-TYPE",
                "ECU-ABSTRACTION-SW-COMPONENT-TYPE",
                "NV-BLOCK-SW-COMPONENT-TYPE",
                "SERVICE-PROXY-SW-COMPONENT-TYPE",
                "SERVICE-SW-COMPONENT-TYPE",
                "PARAMETER-SW-COMPONENT-TYPE"
            ]
        )

        component_plan_schema = {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "component_id": {"type": "string", "description": "组件唯一标识符"},
                    "name": {"type": "string", "description": "组件名称"},
                    "type": {"type": "string", "enum": component_type_enum, "description": "AUTOSAR组件类型"},
                    "purpose": {"type": "string", "description": "功能目的和职责"},
                    "estimated_complexity": {
                        "type": "string",
                        "enum": ["Simple", "Medium", "Complex"],
                        "description": "复杂度评估"
                    },
                    "port_estimates": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "input_ports": {"type": "string"},
                            "output_ports": {"type": "string"}
                        },
                        "required": ["input_ports", "output_ports"]
                    },
                    "behavioral_characteristics": {"type": "string", "description": "行为特征描述"},
                    "element_design": element_design_schema,
                    "direct_references": {"type": "array", "items": {"type": "string"}}
                },
                "required": [
                    "component_id",
                    "name",
                    "type",
                    "purpose",
                    "estimated_complexity",
                    "port_estimates",
                    "behavioral_characteristics",
                    "element_design",
                    "direct_references"
                ]
            }
        }

        # ---------------- interface_plan ----------------
        interface_type_enum = (
            round1_config.interface_types.allowed_types
            if round1_config.interface_types.allowed_types else [
                "SENDER-RECEIVER-INTERFACE",
                "CLIENT-SERVER-INTERFACE",
                "MODE-SWITCH-INTERFACE",
                "NV-DATA-INTERFACE",
                "PARAMETER-INTERFACE",
                "TRIGGER-INTERFACE"
            ]
        )

        interface_plan_schema = {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "interface_id": {"type": "string"},
                    "name": {"type": "string"},
                    "type": {"type": "string", "enum": interface_type_enum},
                    "communication_pattern": {"type": "string"},
                    "data_category": {"type": "string"},
                    "connected_components": {
                        "type": "array",
                        "minItems": 1,
                        "items": {"type": "string"}
                    },
                    "performance_requirements": {"type": "string"},
                    "data_elements": {"type": "array", "items": {"type": "string"}},
                    "direct_paths": {"type": "string"}
                },
                "required": [
                    "interface_id",
                    "name",
                    "type",
                    "communication_pattern",
                    "data_category",
                    "connected_components",
                    "performance_requirements",
                    "data_elements",
                    "direct_paths"
                ]
            }
        }

        # ---------------- root ----------------
        return {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "system_analysis": system_analysis_schema,
                "component_plan": component_plan_schema,
                "interface_plan": interface_plan_schema,
                "connection_topology": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "component_connections": {"type": "string"},
                        "data_flow_paths": {"type": "string"},
                        "control_flow_paths": {"type": "string"}
                    },
                    "required": ["component_connections", "data_flow_paths", "control_flow_paths"]
                },
                "architecture_rationale": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "design_decisions": {"type": "string"},
                        "tradeoff_analysis": {"type": "string"},
                        "alternative_considerations": {"type": "string"},
                        "risk_assessment": {"type": "string"}
                    },
                    "required": ["design_decisions", "tradeoff_analysis", "alternative_considerations",
                                 "risk_assessment"]
                }
            },
            "required": [
                "system_analysis",
                "component_plan",
                "interface_plan",
                "connection_topology",
                "architecture_rationale"
            ]
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