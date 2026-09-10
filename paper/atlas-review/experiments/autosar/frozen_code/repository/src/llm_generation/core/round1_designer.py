"""core/round1_designer.py - Round 1架构设计器

执行第一轮对话：高层架构设计，确定组件类型、接口类型、连接关系
移除了冗余的函数调用，保留核心架构设计功能
"""
import json
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union

from jsonschema import Draft202012Validator

from ..config import CONFIG
from ..knowledge.element_selection import (
    augment_declared_value_selections,
    compile_architecture_selection_paths,
)
from ..knowledge.xsd_selection_paths import PinnedXsdSelectionPathIndex
from ..llm.openai_client import OpenAIClient as GeminiClient
# from ..llm.gemini_client import GeminiClient
from ..llm.prompt_templates import template_manager
from ..utils.exceptions import ArchitectureDesignError
from ..utils.serializers import ArchitectureDesign

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


def validate_architecture_identity_contract(architecture: object) -> None:
    """Reject ambiguous Phase 1 identities before any Phase 2 work.

    JSON Schema can constrain each array item but cannot express uniqueness by
    one of an object's fields.  Those cross-item and local-reference invariants
    are therefore an explicit posterior part of the Phase 1 contract.
    """
    if not isinstance(architecture, dict):
        raise ArchitectureDesignError("Round1 architecture must be an object")

    def rows(key: str) -> list[dict[str, Any]]:
        value = architecture.get(key)
        if not isinstance(value, list):
            raise ArchitectureDesignError(f"{key} must be an array")
        if any(not isinstance(item, dict) for item in value):
            raise ArchitectureDesignError(f"{key} entries must be objects")
        return value

    def unique_values(
        values: list[dict[str, Any]], field: str, label: str
    ) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for position, item in enumerate(values):
            value = str(item.get(field) or "").strip()
            if not value:
                raise ArchitectureDesignError(
                    f"{label}[{position}].{field} must be non-empty"
                )
            if value in seen:
                entity = label.removesuffix("_plan")
                identity_label = field if field.endswith("_id") else f"{entity} {field}"
                raise ArchitectureDesignError(
                    f"duplicate {identity_label}: {value!r}"
                )
            seen.add(value)
            result.append(value)
        return result

    components = rows("component_plan")
    interfaces = rows("interface_plan")
    component_ids = unique_values(components, "component_id", "component_plan")
    component_names = unique_values(components, "name", "component_plan")
    interface_ids = unique_values(interfaces, "interface_id", "interface_plan")
    interface_names = unique_values(interfaces, "name", "interface_plan")
    # Keep the variables explicit for audit/debuggers and guard accidental
    # future removal of one of the uniqueness passes.
    if not all((component_ids, component_names, interface_ids, interface_names)):
        raise ArchitectureDesignError("Phase 1 identity collections must be non-empty")

    order = architecture.get("component_generation_order")
    if not isinstance(order, list) or any(
        not isinstance(item, str) or not item.strip() for item in order
    ):
        raise ArchitectureDesignError(
            "component_generation_order must be an array of non-empty component names"
        )
    normalized_order = [item.strip() for item in order]
    if (
        len(normalized_order) != len(component_names)
        or len(set(normalized_order)) != len(normalized_order)
        or set(normalized_order) != set(component_names)
    ):
        raise ArchitectureDesignError(
            "component_generation_order must be an exact permutation of component names"
        )

    known_components = set(component_names)
    for interface_position, interface in enumerate(interfaces):
        connected = interface.get("connected_components")
        if not isinstance(connected, list) or not connected:
            raise ArchitectureDesignError(
                f"interface_plan[{interface_position}].connected_components must be non-empty"
            )
        normalized_connected = [str(item or "").strip() for item in connected]
        if any(not item for item in normalized_connected):
            raise ArchitectureDesignError(
                f"interface_plan[{interface_position}].connected_components contains an empty name"
            )
        if len(set(normalized_connected)) != len(normalized_connected):
            raise ArchitectureDesignError(
                f"interface_plan[{interface_position}].connected_components contains duplicates"
            )
        unknown = sorted(set(normalized_connected) - known_components)
        if unknown:
            raise ArchitectureDesignError(
                f"interface_plan[{interface_position}] references unknown component(s): "
                + ", ".join(unknown)
            )


class Round1Designer:
    """Round 1架构设计器"""

    def __init__(self):
        """初始化Round 1设计器"""
        self.gemini_client = GeminiClient(pipeline_phase="round1")
        self.terminology = self._load_terminology_from_config()
        self.architecture_schema = self._build_architecture_schema()
        project_root = Path(__file__).resolve().parents[3]
        xsd_path = Path(str(CONFIG.validation.xsd_path))
        manifest_path = Path(str(CONFIG.validation.xsd_serialization_manifest_path))
        if not xsd_path.is_absolute():
            xsd_path = project_root / xsd_path
        if not manifest_path.is_absolute():
            manifest_path = project_root / manifest_path
        self.selection_path_index = PinnedXsdSelectionPathIndex.from_files(
            xsd_path,
            serialization_manifest_path=manifest_path,
        )

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
        use_functions: bool = False,  # 默认不使用函数调用
        generation_seed: Optional[int] = None,
        generation_value_obligations: Optional[List[Dict[str, Any]]] = None,
        generation_requirement_contracts: Optional[List[Dict[str, Any]]] = None,
    ) -> Tuple[ArchitectureDesign, Dict[str, Any]]:
        """执行架构设计"""

        prompt = ""
        response_data: Dict[str, Any] | None = None
        try:
            if generation_requirement_contracts is None:
                generation_requirement_contracts = []
            if not isinstance(generation_requirement_contracts, list):
                raise ArchitectureDesignError(
                    "generation_requirement_contracts must be an array"
                )
            request_schema = deepcopy(self.architecture_schema)
            contract_ids: set[str] = set()
            contract_keys: set[tuple[str, str]] = set()
            for position, contract in enumerate(generation_requirement_contracts):
                if not isinstance(contract, dict):
                    raise ArchitectureDesignError(
                        f"generation_requirement_contracts[{position}] must be an object"
                    )
                requirement_id = str(contract.get("requirement_id") or "").strip()
                component = str(contract.get("component") or "").strip()
                requirement = str(contract.get("requirement") or "").strip()
                expected_count = contract.get("expected_obligation_count")
                if (
                    not requirement_id
                    or not component
                    or not requirement
                    or isinstance(expected_count, bool)
                    or not isinstance(expected_count, int)
                    or expected_count < 1
                ):
                    raise ArchitectureDesignError(
                        f"generation_requirement_contracts[{position}] is incomplete"
                    )
                key = (component, requirement_id)
                if key in contract_keys:
                    raise ArchitectureDesignError(
                        "generation requirement contracts require unique "
                        "(component, requirement_id) pairs"
                    )
                contract_keys.add(key)
                contract_ids.add(requirement_id)
            if contract_ids:
                unsupported_id_schema = (
                    request_schema["properties"]["component_plan"]["items"]
                    ["properties"]["element_design"]["properties"]["unsupported"]
                    ["items"]["properties"]["requirement_id"]
                )
                unsupported_id_schema["enum"] = sorted(contract_ids)
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
                architecture_schema=request_schema  # ← 明确内嵌 JSON Schema
            )
            selection_candidate_catalog_audit = {
                "contract": "focused-pinned-xsd-candidates-v1",
                "xsd_sha256": self.selection_path_index.xsd_sha256,
                "component_types": {},
            }
            mentioned_component_types = [
                str(component_type).strip().upper()
                for component_type in ct_allowed
                if str(component_type).strip().upper() in user_requirements.upper()
            ]
            catalog_sections: list[str] = []
            for component_type in mentioned_component_types:
                candidate_paths = self.selection_path_index.requirement_candidate_paths(
                    component_type,
                    user_requirements,
                    max_paths=120,
                )
                if not candidate_paths:
                    continue
                selection_candidate_catalog_audit["component_types"][component_type] = {
                    "candidate_count": len(candidate_paths),
                }
                rendered = "\n".join(f"- {'/'.join(path)}" for path in candidate_paths)
                catalog_sections.append(f"[{component_type}]\n{rendered}")
            if catalog_sections:
                prompt += (
                    "\n\n## Hash-pinned AUTOSAR XSD path candidates\n"
                    f"XSD SHA-256: {self.selection_path_index.xsd_sha256}\n"
                    "For requirement elements covered by this focused catalog, copy one exact "
                    "physical path; never splice parent/child tags from different entries. "
                    "The catalog is derived locally from request-named XSD elements and is not "
                    "a license to invent uncatalogued containment. If no path represents the "
                    "intended requirement, record it in element_design.unsupported. Every "
                    "selection is revalidated against this pinned XSD before Phase 1 is "
                    "accepted.\n\n"
                    + "\n\n".join(catalog_sections)
                )
            if generation_requirement_contracts:
                prompt += (
                    "\n\n## Authorized structured requirement contracts\n"
                    "The local requirement adapter has already compiled these contracts into "
                    "exact scalar obligations. If you defer one in element_design.unsupported, "
                    "copy its requirement_id exactly from this list. Do not invent IDs. The "
                    "free-text requirement and reason are explanatory; requirement_id is the "
                    "machine binding.\n"
                    + json.dumps(
                        generation_requirement_contracts,
                        ensure_ascii=False,
                        sort_keys=True,
                    )
                )

            if CONFIG.debug_mode:
                print(f"[DEBUG] Round1 提示词长度: {len(prompt)}")
                if uploaded_files:
                    print(f"[DEBUG] 包含 {len(uploaded_files)} 个文档文件")

            # Round1使用纯结构化输出（不使用函数调用）
            # 因为所需信息都已经在prompt中提供了
            self.gemini_client.pipeline_phase = "round1"
            response_data, input_tokens, output_tokens, total_tokens = \
                self.gemini_client.generate_with_schema(
                    prompt=prompt,
                    schema=request_schema,
                    seed=generation_seed,
                    temperature=CONFIG.llm.get_temperature('round1'),
                    document_files=uploaded_files
                )

            schema_errors = sorted(
                Draft202012Validator(request_schema).iter_errors(response_data),
                key=lambda error: list(error.absolute_path),
            )
            if schema_errors:
                first_error = schema_errors[0]
                location = "/".join(str(part) for part in first_error.absolute_path)
                raise ArchitectureDesignError(
                    "Round1 response failed local JSON Schema validation at "
                    f"{location or '<root>'}: {first_error.message}"
                )

            # Structured requirement values are authoritative over alternative
            # Phase 1 branches below the same named element.  Reconcile them
            # before validating every model-selected path against the XSD, so
            # an invalid competing INIT-VALUE branch cannot reject the design
            # before the deterministic requirement compiler gets a chance to
            # remove it.  Unrelated invalid paths still fail closed below.
            if generation_value_obligations is None:
                generation_value_obligations = []
            if not isinstance(generation_value_obligations, list):
                raise ArchitectureDesignError(
                    "generation_value_obligations must be an array"
                )
            value_obligation_audit = []
            if generation_value_obligations or generation_requirement_contracts:
                augmented_components = []
                for component_plan in response_data.get("component_plan") or []:
                    augmented, audit = augment_declared_value_selections(
                        component_plan,
                        generation_value_obligations,
                        xsd_path_index=self.selection_path_index,
                        requirement_contracts=generation_requirement_contracts,
                    )
                    augmented_components.append(augmented)
                    value_obligation_audit.append(audit)
                response_data = dict(response_data)
                response_data["component_plan"] = augmented_components

            # The provider schema validates the semantic IR shape, but JSON
            # Schema cannot express the AUTOSAR parent/child type graph without
            # enumerating an unbounded set of whole paths.  Resolve that second
            # contract locally against the pinned XSD before accepting Phase 1.
            response_data, selection_path_audit = compile_architecture_selection_paths(
                response_data,
                xsd_path_index=self.selection_path_index,
            )

            validate_architecture_identity_contract(response_data)

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
                "selection_candidate_catalog": selection_candidate_catalog_audit,
                "declared_value_reconciliation": value_obligation_audit,
                "selection_path_compilation": selection_path_audit,
                "provider_responses": list(self.gemini_client.response_audit),
                "provider_counters": {
                    "calls": self.gemini_client.call_count,
                    "successes": self.gemini_client.success_count,
                    "errors": self.gemini_client.error_count,
                },
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
            if isinstance(response_data, dict):
                try:
                    self.save_rejected_round1_data(
                        prompt=prompt,
                        response_data=response_data,
                        error=e,
                        user_requirements=user_requirements,
                    )
                except Exception as save_error:
                    if CONFIG.debug_mode:
                        print(f"[WARNING] rejected Round1 audit save failed: {save_error}")
            raise ArchitectureDesignError(f"架构设计失败: {str(e)}")

    def _build_architecture_schema(self) -> Dict[str, Any]:
        """Build the strict, combination-free Round 1 JSON Schema."""

        round1_config = CONFIG.round1_schema

        # --- 小助手：可能空的枚举 → 回退成普通 string，避免 enum:[]
        def _enum_or_string(values, desc: str = None):
            vals = sorted({v for v in (values or []) if v})
            if vals:
                return {"type": "string", "enum": vals}
            out = {"type": "string"}
            if desc:
                out["description"] = f"{desc}; no enum is configured, so any string is allowed."
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
                "functional_decomposition": {"type": "string", "description": "Functional decomposition and responsibility boundaries."},
                "data_flow_analysis": {"type": "string", "description": "Data-flow analysis."},
                "timing_requirements": {"type": "string", "description": "Timing-requirement analysis."},
                "scalability_considerations": {"type": "string", "description": "Scalability considerations."},
                "complexity_assessment": {
                    "type": "string",
                    "description": "Complexity assessment.",
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
                "key": _enum_or_string(elem_keys, "Element key such as SERVER-CALL-POINTS or DATA-RECEIVE-POINT-BY-ARGUMENTS"),
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
                                "description": "Select exactly the required child keys from configured selectable_children.",
                                # 仅作提示，不参与校验
                                "x-allowed-children": variant_children_map
                            },
                            "notes": {"type": "string"}
                        },
                        "required": ["of", "variant", "include", "notes"]
                    },
                    "description": "Deterministic union-branch and child-key selections inside this element."
                },
                "notes": {"type": "string"}
            },
            "required": ["key", "wrapper", "preselect", "notes"]
        }

        element_requirement_schema = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "path": {
                    "type": "array",
                    "minItems": 2,
                    "items": {
                        "type": "string",
                        "pattern": "^(?:[A-Z][A-Z0-9-]*|@[A-Z][A-Z0-9-]*|#TEXT)$",
                    },
                    "description": (
                        "Semantic selection of one physical AUTOSAR XSD path relative to the "
                        "component payload. Every adjacent parent/child pair is checked locally "
                        "against the hash-pinned XSD before Phase 1 is accepted; never compose "
                        "a path from merely familiar tag names. Example: "
                        "PORTS/R-PORT-PROTOTYPE/REQUIRED-COM-SPECS/"
                        "NONQUEUED-RECEIVER-COM-SPEC/ALIVE-TIMEOUT"
                    ),
                },
                "min_occurs": {"type": "integer", "minimum": 0},
                "max_occurs": {"type": "integer", "minimum": 1},
                "value_present": {
                    "type": "boolean",
                    "description": "True only when the selected leaf has an exact lexical value.",
                },
                "value": {
                    "type": "string",
                    "description": (
                        "Exact lexical value for a scalar XSD leaf, or an empty string "
                        "when value_present=false. Complex containers cannot carry values."
                    ),
                },
                "anchors": {
                    "type": "array",
                    "minItems": 0,
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "path_index": {"type": "integer", "minimum": 0},
                            "short_name": {"type": "string", "minLength": 1},
                        },
                        "required": ["path_index", "short_name"],
                    },
                    "description": (
                        "Optional instance anchors for repeated structures. path_index identifies "
                        "the path segment whose direct SHORT-NAME must match."
                    ),
                },
                "notes": {"type": "string"},
            },
            "required": [
                "path", "min_occurs", "max_occurs", "value_present", "value", "anchors", "notes"
            ],
        }

        unsupported_requirement_schema = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "requirement_id": {"type": "string", "minLength": 1},
                "requirement": {"type": "string", "minLength": 1},
                "reason": {"type": "string", "minLength": 1},
            },
            "required": ["requirement_id", "requirement", "reason"],
        }

        # ---------------- element_design（ports / internal_behaviors） ----------------
        element_design_schema = {
            "type": "object",
            "description": "Required concrete elements with deterministic union-branch and child-key selections.",
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
                            "items": _enum_or_string(port_type_names, "Port type"),
                            "description": "Use an empty array when needed=false; otherwise list every required port type."
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
                                    "type": _enum_or_string(event_type_names, "Event type"),
                                    "name": {"type": "string"},
                                    "trigger": {"type": "string"}
                                },
                                "required": ["type", "name", "trigger"]
                            },
                            "description": "Use an empty array when needed=false."
                        },
                        "runnables": {
                            "type": "array",
                            "minItems": 0,  # needed=false → []
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "name": {"type": "string", "description": "Runnable entity name."},
                                    "elements": {
                                        "type": "array",
                                        "minItems": 1,
                                        "items": element_selection_schema,
                                        "description": "Deep elements required by this runnable, including deterministic child selections."
                                    },
                                    "notes": {"type": "string"}
                                },
                                "required": ["name", "elements", "notes"]
                            },
                            "description": "For each runnable, select every required deep element and its deterministic union/child choices."
                        }
                    },
                    "required": ["needed", "events", "runnables"]
                },
                "selections": {
                    "type": "array",
                    "minItems": 0,
                    "items": element_requirement_schema,
                    "description": (
                        "All requirement-driven AUTOSAR paths outside or in addition to the legacy "
                        "runnable preselect structure. Selected optional XSD elements must be listed "
                        "here so Phase 2 can expand them from Neo4j and promote them to required."
                    ),
                },
                "unsupported": {
                    "type": "array",
                    "minItems": 0,
                    "items": unsupported_requirement_schema,
                    "description": (
                        "Requirement items that cannot be mapped to a known supported AUTOSAR path. "
                        "A non-empty list makes Phase 2 validation incomplete and prevents promotion."
                    ),
                },
            },
            "required": ["ports", "internal_behaviors", "selections", "unsupported"]
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
                    "component_id": {"type": "string", "description": "Unique component identifier."},
                    "name": {"type": "string", "description": "Component name."},
                    "type": {"type": "string", "enum": component_type_enum, "description": "AUTOSAR component type."},
                    "purpose": {"type": "string", "description": "Functional purpose and responsibility."},
                    "estimated_complexity": {
                        "type": "string",
                        "enum": ["Simple", "Medium", "Complex"],
                        "description": "Complexity assessment."
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
                    "behavioral_characteristics": {"type": "string", "description": "Behavioral characteristics."},
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
                "component_generation_order": {
                    "type": "array",
                    "description": "Component generation order. Place dependencies before dependants; every item must exactly match a component_plan name.",
                    "items": {
                        "type": "string"
                    }
                },
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
                "component_generation_order",
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
            context_parts.append(f"Design background: {design_context}")

        if memory_context:
            context_parts.append(f"Conversation history: {memory_context}")

        if suggested_patterns:
            patterns_text = "\n".join([f"- {pattern}" for pattern in suggested_patterns])
            context_parts.append(f"Suggested design patterns:\n{patterns_text}")

        if document_content:
            context_parts.append(f"Document analysis:\n{document_content}")

        return "\n\n".join(context_parts)

    def _parse_response_to_design(self, response_data: Dict[str, Any]) -> ArchitectureDesign:
        """解析LLM响应并创建设计对象"""

        # 创建ArchitectureDesign对象
        design = ArchitectureDesign(
            system_analysis=response_data.get("system_analysis", {}),
            component_plan=response_data.get("component_plan", []),
            interface_plan=response_data.get("interface_plan", []),
            component_generation_order=response_data.get("component_generation_order", []),
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

    def save_rejected_round1_data(
        self,
        *,
        prompt: str,
        response_data: Dict[str, Any],
        error: Exception,
        user_requirements: str = "",
    ) -> Path:
        """Quarantine a locally rejected provider response for audit only."""
        save_dir = CONFIG.output_dir / "round1_rejected"
        save_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        output_file = save_dir / f"round1_rejected_{timestamp}.json"
        payload = {
            "artifact_kind": "rejected_phase1_response",
            "promotable": False,
            "timestamp": timestamp,
            "model": CONFIG.llm.model_name,
            "xsd_sha256": self.selection_path_index.xsd_sha256,
            "error": {"type": type(error).__name__, "message": str(error)},
            "user_requirements": user_requirements,
            "prompt": prompt,
            "response_data": response_data,
        }
        output_file.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return output_file

# 全局Round1设计器实例
round1_designer = Round1Designer()
