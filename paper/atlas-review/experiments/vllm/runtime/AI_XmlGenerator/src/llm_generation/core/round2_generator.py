"""core/round2_generator.py - 修复版Round 2生成器

修复了参数调用不匹配问题和查询字段问题
专注于结构化输出，确保Schema生成流程正确
"""
import hashlib
import json
import time
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from jsonschema import Draft202012Validator

from src.validation.v2.repair_loop import (
    BundleRepairLoop,
    RepairProposal,
    bundle_fingerprint,
)
from src.validation.v2.selection_obligations import (
    merge_selection_obligations,
    validate_selection_obligations,
)
from src.validation.v2.service import GeneratedArxmlValidationService
from .typed_repair import (
    COMPONENT_PACKAGE,
    INTERFACE_PACKAGE,
    RepairTarget,
    TypedRepairSession,
    XsdGuard,
    deletion_repairable_rule_ids,
    render_document,
)
from .xsd_serializer import DeterministicXsdSerializer, apply_projection_map
from ..config import CONFIG
from ..knowledge.dynamic_query_engine import query_engine
from ..knowledge.element_selection import (
    apply_element_selections,
    augment_declared_value_selections,
    augment_required_existence_selections,
    compile_architecture_selection_paths,
    build_interface_instance_skeleton,
    build_provider_instance_skeleton,
    bind_projected_interface_data_types,
    constrain_interface_data_type_schema,
    materialize_deterministic_values,
    materialize_admitted_provider_payload,
    merge_provider_schema_payloads,
    normalize_component_reference_values,
    partition_provider_schema,
    project_provider_to_admitted_instances,
    project_element_design_for_schema,
    project_declared_value_design,
    remove_deterministic_value_properties,
)
from ..knowledge.xsd_selection_paths import PinnedXsdSelectionPathIndex
from ..knowledge.v2.generation_adapter import GenerationConstraintAdapterV2
from ..llm.openai_client import OpenAIClient as GeminiClient
# from ..llm.gemini_client import GeminiClient
from ..llm.prompt_templates import template_manager
from ..standard_types.standard_types import standard_type_manager  # 新增：导入标准类型管理器
from ..utils.serializers import ArchitectureDesign


class Round2Generator:
    """Round 2详细生成器 - 修复版"""

    def __init__(self):
        """初始化Round 2生成器"""
        self.gemini_client = GeminiClient(pipeline_phase="round2.unassigned")
        self.query_engine = query_engine
        self.standard_type_manager = standard_type_manager  # 新增：标准类型管理器
        self.constraint_adapter_v2 = GenerationConstraintAdapterV2.try_default(CONFIG)
        if CONFIG.constraint_engine.enabled and self.constraint_adapter_v2 is None:
            raise RuntimeError(
                "ConstraintV2 is enabled, but retrieval cards/manifest could not be loaded"
            )
        self.validation_service = GeneratedArxmlValidationService.from_config(CONFIG)
        self._constraint_retrieval_trace: Dict[str, Any] = {}
        self._selection_path_compilation_trace: Dict[str, Any] = {}
        self._generation_obligation_trace: Dict[str, Any] = {}
        self._generation_seed: Optional[int] = None
        self._provider_payload_provenance: List[Dict[str, Any]] = []

        self._component_projection_maps: Dict[str, Dict[str, Any]] = {}
        # Per-document structured repair context.  These objects exist only as
        # locals inside the component loop, so without accumulating them the
        # repair stage would have no schema, no projection map and no
        # requirement-owned constant set to work against, and would have to
        # fall back to regenerating whole XML documents.
        self._repair_targets: Dict[Tuple[str, str], RepairTarget] = {}
        project_root = Path(__file__).resolve().parents[3]
        validation_config = getattr(CONFIG, "validation", None)
        xsd_value = str(getattr(validation_config, "xsd_path", "") or "")
        manifest_value = str(
            getattr(validation_config, "xsd_serialization_manifest_path", "") or ""
        )
        xsd_path = Path(xsd_value) if xsd_value else Path(
            "src/validation/data/AUTOSAR_4-2-2.xsd"
        )
        manifest_path = Path(manifest_value) if manifest_value else Path(
            "src/llm_generation/knowledge/v2/xsd_serialization_manifest.json"
        )
        if not xsd_path.is_absolute():
            xsd_path = project_root / xsd_path
        if not manifest_path.is_absolute():
            manifest_path = project_root / manifest_path
        self.xml_serializer = DeterministicXsdSerializer.from_files(
            manifest_path,
            xsd_path=xsd_path,
        )
        self.selection_path_index = PinnedXsdSelectionPathIndex.from_files(
            xsd_path,
            serialization_manifest_path=manifest_path,
        )
        self._typed_repair = TypedRepairSession(
            guard=XsdGuard(
                path_index=self.selection_path_index,
                serializer=self.xml_serializer,
            ),
            serializer=self.xml_serializer,
            fingerprint=bundle_fingerprint,
            # Which rules a deletion may legitimately take out of evaluation is
            # a property of the pinned rule corpus, not of the repair proposal.
            deletion_repairable_rule_ids=(
                deletion_repairable_rule_ids(self.validation_service.engine.plan)
                if self.validation_service is not None
                else frozenset()
            ),
        )

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
    ) -> Tuple[Dict[str, Dict[str, str]], Dict[str, Any]]:
        """Round2 逐组件生成：
        - 先基于 Round1 的接口计划与接口 Schema 生成“接口实例对象”
        - 再逐组件生成组件实例
        - 合并为最终 JSON，并转换为 ARXML
        """

        start_time = time.time()
        declarations = self._validation_declarations(custom_requirements)
        interface_package_ref = str(
            (custom_requirements or {}).get("interface_package_ref")
            or f"/{INTERFACE_PACKAGE}"
        ).strip()
        if (
            not interface_package_ref.startswith("/")
            or interface_package_ref == "/"
            or "/" in interface_package_ref[1:]
        ):
            raise ValueError(
                "interface_package_ref must be one absolute top-level AUTOSAR package"
            )
        self._interface_package_ref = interface_package_ref.rstrip("/")
        self._interface_package_name = self._interface_package_ref[1:]
        generation_value_obligations = (custom_requirements or {}).get(
            "generation_value_obligations", []
        )
        if not isinstance(generation_value_obligations, list):
            raise ValueError("generation_value_obligations must be an array")
        generation_requirement_contracts = (custom_requirements or {}).get(
            "generation_requirement_contracts", []
        )
        if not isinstance(generation_requirement_contracts, list):
            raise ValueError("generation_requirement_contracts must be an array")
        generation_seed = (custom_requirements or {}).get("generation_seed")
        if generation_seed is not None and (
            isinstance(generation_seed, bool) or not isinstance(generation_seed, int)
        ):
            raise ValueError("generation_seed must be an integer or null")
        self._generation_seed = generation_seed
        self._provider_payload_provenance.clear()
        self._component_projection_maps.clear()
        self._repair_targets.clear()
        self._typed_repair.reset()
        self._constraint_retrieval_trace = {}
        self._generation_obligation_trace = {}
        # Revalidate persisted or caller-supplied Phase 1 artifacts before the
        # interface schema/provider stage.  This is deliberately redundant with
        # Round1 acceptance so no alternate entry point can bypass the pinned
        # physical XSD path contract.
        compiled_architecture, self._selection_path_compilation_trace = (
            compile_architecture_selection_paths(
                {"component_plan": architecture_design.component_plan or []},
                xsd_path_index=self.selection_path_index,
            )
        )
        architecture_design.component_plan = compiled_architecture["component_plan"]
        for component_plan in architecture_design.component_plan or []:
            component_name = str(component_plan.get("name") or "").strip()
            component_plan["element_design"] = normalize_component_reference_values(
                component_plan.get("element_design") or {},
                component_name=component_name,
            )
        component_plans_map = {comp['name']: comp for comp in (architecture_design.component_plan or [])}
        interface_plans = deepcopy(architecture_design.interface_plan or [])
        raw_interface_type_bindings = (custom_requirements or {}).get(
            "interface_data_type_bindings", []
        )
        if not isinstance(raw_interface_type_bindings, list):
            raise ValueError("interface_data_type_bindings must be an array")
        plan_by_name = {
            str(plan.get("name") or ""): plan
            for plan in interface_plans
            if isinstance(plan, dict)
        }
        seen_interface_type_bindings: set[tuple[str, str]] = set()
        for position, binding in enumerate(raw_interface_type_bindings):
            if not isinstance(binding, dict):
                raise ValueError(
                    f"interface_data_type_bindings[{position}] must be an object"
                )
            interface_name = str(binding.get("interface_name") or "").strip()
            data_element = str(binding.get("data_element") or "").strip()
            type_ref = str(binding.get("type_ref") or "").strip()
            type_dest = str(binding.get("type_dest") or "").strip()
            identity = (interface_name, data_element)
            if (
                not all((interface_name, data_element, type_ref, type_dest))
                or identity in seen_interface_type_bindings
                or interface_name not in plan_by_name
                or data_element not in (plan_by_name[interface_name].get("data_elements") or [])
            ):
                raise ValueError(
                    "interface data-type binding is duplicate, incomplete, or outside "
                    f"the Phase-1-admitted interface plan at position {position}"
                )
            seen_interface_type_bindings.add(identity)
            plan_by_name[interface_name].setdefault(
                "data_element_type_refs", {}
            )[data_element] = {"value": type_ref, "dest": type_dest}


        # 1) 准备接口 Schema（用于接口实例的强校验）
        interface_schema = self.query_engine.generate_multi_interface_schema(interface_plans)
        interface_schema, interface_type_schema_plan = (
            constrain_interface_data_type_schema(interface_schema, interface_plans)
        )
        interface_skeleton: Dict[str, Any] = {}
        interface_skeleton_plan: Dict[str, Any] = {
            "decision": "NOT_APPLICABLE",
            "interface_count": 0,
            "data_element_count": 0,
        }
        interface_projection_plan: Dict[str, Any] = {
            "decision": "NOT_APPLICABLE",
            "named_array_count": 0,
            "admitted_instance_count": 0,
        }
        interface_provider_schema = interface_schema
        if interface_plans:
            interface_skeleton, interface_skeleton_plan = (
                build_interface_instance_skeleton(
                    interface_plans, interface_schema
                )
            )
            interface_provider_schema, interface_projection_plan = (
                project_provider_to_admitted_instances(
                    interface_schema, interface_skeleton
                )
            )
            interface_provider_schema, interface_type_binding_plan = (
                bind_projected_interface_data_types(
                    interface_provider_schema, interface_plans
                )
            )
            interface_skeleton_plan["data_type_schema"] = interface_type_schema_plan
            interface_skeleton_plan["data_type_bindings"] = (
                interface_type_binding_plan
            )
            self._save_component_schema_to_file(
                "interfaces_provider_admitted", interface_provider_schema
            )

        # ↓↓↓ 新增：提早准备标准类型，给接口 prompt 使用
        standard_types = self._prepare_standard_types()

        # 2) 先生成接口实例（独立于组件，严格按接口 Schema）
        merged_json: Dict[str, Any] = {}
        token_stats = {"input": 0, "output": 0, "total": 0}
        # Always define the downstream interface index. Architectures without
        # interfaces, and interface-generation failures, must still generate
        # their components and reach validation.
        iface_index_for_prompt: List[Dict[str, Any]] = []

        if interface_plans:
            interface_constraint_context_v2 = ""
            if self.constraint_adapter_v2 is not None:
                interface_cards_v2 = self.constraint_adapter_v2.retrieve_for_interfaces(
                    interface_plans=interface_plans,
                    interface_schema=interface_schema,
                    max_constraints=CONFIG.constraint_engine.max_constraints_interface,
                    per_family_limit=CONFIG.constraint_engine.per_family_limit,
                )
                interface_constraint_context_v2 = self.constraint_adapter_v2.render_prompt(interface_cards_v2)
                self._constraint_retrieval_trace["interfaces"] = (
                    self.constraint_adapter_v2.retrieval_trace()
                )
            try:
                interfaces_prompt = template_manager.get_round2_prompt_interfaces(
                    interface_plans=interface_plans,
                    interface_schema=interface_provider_schema,
                    architecture_design=architecture_design.__dict__,
                    memory_context=memory_context or "",
                    standard_types=standard_types
                )
                interfaces_prompt += interface_constraint_context_v2
                # 保存接口 Prompt 以便调试
                self._save_prompt_to_file(interfaces_prompt)

                try:
                    self.gemini_client.pipeline_phase = "round2.interface"
                    iface_resp, in_tok_i, out_tok_i, ttl_tok_i = (
                        self.gemini_client.generate_with_schema(
                            prompt=interfaces_prompt,
                            schema=interface_provider_schema,
                            seed=generation_seed,
                            temperature=CONFIG.llm.get_temperature('interface'),
                            max_retries=CONFIG.llm.max_retries,
                        )
                    )
                except Exception:
                    rejected_raw = getattr(
                        self.gemini_client, "last_raw_schema_payload", None
                    )
                    if isinstance(rejected_raw, dict):
                        raw_artifact = self._save_component_response_to_file(
                            "interfaces_provider_raw", rejected_raw
                        )
                        self._provider_payload_provenance.append(
                            {
                                "scope": "interfaces",
                                "component": None,
                                "raw_provider_payload": raw_artifact,
                                "raw_provider_schema_status": "RAW_FAIL",
                                "normalization_status": "NOT_APPLICABLE",
                                "final_atlas_status": "NOT_EVALUATED",
                                "identity_skeleton": interface_skeleton_plan,
                                "instance_projection": interface_projection_plan,
                            }
                        )
                    raise

                # This is intentionally the first operation on the returned
                # provider value.  Persist the exact admitted-space payload and
                # its SHA before deterministic identity materialization.
                raw_artifact = self._save_component_response_to_file(
                    "interfaces_provider_raw", iface_resp
                )
                raw_errors = sorted(
                    Draft202012Validator(interface_provider_schema).iter_errors(
                        iface_resp
                    ),
                    key=lambda error: list(error.absolute_path),
                )
                interface_provenance = {
                    "scope": "interfaces",
                    "component": None,
                    "raw_provider_payload": raw_artifact,
                    "raw_provider_schema_status": (
                        "PASS" if not raw_errors else "RAW_FAIL"
                    ),
                    "normalization_status": "NOT_APPLICABLE",
                    "final_atlas_status": "NOT_EVALUATED",
                    "identity_skeleton": interface_skeleton_plan,
                    "instance_projection": interface_projection_plan,
                }
                self._provider_payload_provenance.append(interface_provenance)
                if raw_errors:
                    first = raw_errors[0]
                    location = "/".join(
                        str(item) for item in first.absolute_path
                    ) or "<root>"
                    raise ValueError(
                        "raw interface provider payload violates admitted-only "
                        f"schema at {location}: {first.message}"
                    )
                interfaces_obj, interface_assembly_audit = (
                    materialize_admitted_provider_payload(
                        iface_resp,
                        interface_provider_schema,
                        interface_projection_plan,
                        interface_skeleton,
                    )
                )
                interface_provenance["normalization_status"] = (
                    interface_assembly_audit["normalization_status"]
                )
                assembled_errors = sorted(
                    Draft202012Validator(interface_schema).iter_errors(
                        interfaces_obj
                    ),
                    key=lambda error: list(error.absolute_path),
                )
                if assembled_errors:
                    interface_provenance["final_atlas_status"] = "FAIL"
                    first = assembled_errors[0]
                    location = "/".join(
                        str(item) for item in first.absolute_path
                    ) or "<root>"
                    raise ValueError(
                        "deterministically assembled interface payload violates "
                        f"the full ATLAS schema at {location}: {first.message}"
                    )
                interface_provenance["final_atlas_status"] = "PASS"
                self._save_component_response_to_file(
                    "interfaces_provider_admitted_assembled", interfaces_obj
                )

                token_stats["input"] += in_tok_i
                token_stats["output"] += out_tok_i
                token_stats["total"] += ttl_tok_i

                # 规范化：{ type: [ {SHORT-NAME,...}, ... ] } → { "<SHORT-NAME>": { _type: "<type>", ... } }
                normalized_ifaces = self._normalize_interfaces_object(interfaces_obj)
                expected_interface_names = {
                    str(plan.get("name") or "").strip()
                    for plan in interface_plans
                }
                if set(normalized_ifaces) != expected_interface_names:
                    interface_provenance["final_atlas_status"] = "FAIL"
                    raise ValueError(
                        "normalized interface identities differ from the "
                        "Phase-1-admitted identity set"
                    )
                # 可选：持久化接口实例，便于核对
                if normalized_ifaces:
                    try:
                        self._save_interfaces_instances(normalized_ifaces)
                    except Exception:
                        pass
                # 注入供后续 XML 转换
                merged_json["_interfaces"] = normalized_ifaces
                self._register_interface_repair_targets(
                    normalized_ifaces, interface_schema
                )

                # ↓↓↓ 新增：为组件 Prompt 构建只读“接口实例索引”
                iface_index_for_prompt = self._build_detailed_interface_index(normalized_ifaces)

                # 若接口阶段失败或为空，则退化为基于 Round1 计划的索引（不新增函数，局部就地处理）
                if not iface_index_for_prompt:
                    iface_index_for_prompt = [
                        {
                            "name": it.get("name", ""),
                            "type": it.get("type", ""),
                            "path": f"{self._interface_package_ref}/{it.get('name', '')}"
                        }
                        for it in (interface_plans or [])
                    ]

            except Exception as e:
                if CONFIG.debug_mode:
                    print(f"[ERROR] 接口实例生成失败，拒绝继续：{e}")
                raise



        # 4) 逐组件生成
        generation_order = architecture_design.component_generation_order
        if not generation_order or len(generation_order) != len(component_plans_map):
            if CONFIG.debug_mode:
                print("[WARNING] Round 1未提供有效生成顺序，将按默认顺序执行。")
            ordered_component_plans = architecture_design.component_plan or []
        else:
            ordered_component_plans = [component_plans_map[name] for name in generation_order if
                                       name in component_plans_map]

        if CONFIG.debug_mode:
            print(f"[DEBUG] 组件生成顺序: {[comp['name'] for comp in ordered_component_plans]}")

        standard_types = self._prepare_standard_types()

        # 4.b) 初始化用于累积实例路径的字典
        known_instance_paths: Dict[str, List[str]] = {}
        if iface_index_for_prompt:
            for item in iface_index_for_prompt:
                item_type = item.get("type")
                item_path = item.get("path")
                if item_type and item_path:
                    known_instance_paths.setdefault(item_type, []).append(item_path)

        if CONFIG.debug_mode and known_instance_paths:
            print(f"[DEBUG] 已预加载 {len(iface_index_for_prompt)} 条接口实例路径用于Schema注入。")
        # **********************************

        for comp in ordered_component_plans:
            comp_name = comp.get("name", "Component")
            value_obligation_audit = {
                "decision": "NOT_EVALUATED",
                "applied_count": 0,
                "ignored_other_component_indexes": [],
                "applied": [],
            }
            obligation_audit = {
                "decision": "NOT_EVALUATED",
                "derived_selection_count": 0,
                "promoted_selection_count": 0,
                "constraint_ids": [],
                "derived": [],
                "promoted": [],
            }
            augmented_comp = comp
            if generation_value_obligations or generation_requirement_contracts:
                augmented_comp, value_obligation_audit = augment_declared_value_selections(
                    augmented_comp,
                    generation_value_obligations,
                    xsd_path_index=self.selection_path_index,
                    requirement_contracts=generation_requirement_contracts,
                )
            if self.validation_service is not None:
                augmented_comp, obligation_audit = augment_required_existence_selections(
                    augmented_comp,
                    self.validation_service.engine.plan,
                    xsd_path_index=self.selection_path_index,
                )
            if (
                value_obligation_audit["applied_count"]
                or obligation_audit["derived_selection_count"]
                or obligation_audit["promoted_selection_count"]
            ):
                compiled, compilation_audit = compile_architecture_selection_paths(
                    {"component_plan": [augmented_comp]},
                    xsd_path_index=self.selection_path_index,
                )
                augmented_comp = compiled["component_plan"][0]
                augmented_comp["element_design"] = normalize_component_reference_values(
                    augmented_comp.get("element_design") or {},
                    component_name=str(comp_name),
                )
                comp.clear()
                comp.update(augmented_comp)
                obligation_audit["selection_path_compilation"] = compilation_audit
            obligation_audit["declared_values"] = value_obligation_audit
            self._generation_obligation_trace[str(comp_name)] = obligation_audit
            # 4.1 单组件 Schema
            comp_schema = self._build_single_component_schema(comp)
            projection_map = self.query_engine.component_xml_projection_map(comp)
            self._component_projection_maps[comp_name] = projection_map
            self._save_component_schema_to_file(comp_name, comp_schema)  # 保存原生Schema

            # 4.2 (新) 将已知的路径注入当前组件的Schema，生成增强版Schema
            enhanced_schema = self._inject_paths_into_schema(
                comp_schema,
                known_instance_paths,
                current_component_name=comp_name  # 传递当前组件名
            )
            declared_provider_design = project_declared_value_design(
                comp.get("element_design") or {},
                projection_map,
                value_obligation_audit,
            )
            provider_schema, provider_materialization_plan = (
                remove_deterministic_value_properties(
                    enhanced_schema, declared_provider_design
                )
            )
            # The requirement owns every named instance identity and count.
            # Project named arrays to fixed identity-keyed slots before the
            # provider call; the provider can fill semantic fields but cannot
            # emit an array, SHORT-NAME, extra identity, duplicate, or unnamed
            # instance at all.
            instance_provider_design = project_element_design_for_schema(
                comp.get("element_design") or {}, projection_map
            )
            instance_skeleton, instance_skeleton_plan = (
                build_provider_instance_skeleton(
                    enhanced_schema, instance_provider_design
                )
            )
            provider_schema, instance_projection_plan = (
                project_provider_to_admitted_instances(
                    provider_schema, instance_skeleton
                )
            )
            value_obligation_audit["provider_instance_skeleton"] = (
                instance_skeleton_plan
            )
            value_obligation_audit["provider_instance_projection"] = (
                instance_projection_plan
            )
            full_provider_schema = provider_schema
            provider_calls, provider_partition_plan = partition_provider_schema(
                full_provider_schema
            )
            if len(provider_calls) != 1:
                raise RuntimeError("component provider schema must use exactly one call")
            provider_schema = provider_calls[0]["schema"]
            value_obligation_audit["provider_materialization_plan"] = (
                provider_materialization_plan
            )
            value_obligation_audit["provider_schema_partition"] = (
                provider_partition_plan
            )
            if CONFIG.debug_mode and known_instance_paths:
                # 可以选择性保存增强后的Schema用于调试
                self._save_component_schema_to_file(f"{comp_name}_enhanced", enhanced_schema)
            if (
                provider_materialization_plan["unique_removed_path_count"]
                or provider_partition_plan["strategy"] != "single_strict_schema"
            ):
                self._save_component_schema_to_file(
                    f"{comp_name}_provider_full", full_provider_schema
                )
                self._save_component_schema_to_file(
                    f"{comp_name}_provider", provider_schema
                )

            constraint_context_v2 = ""
            if self.constraint_adapter_v2 is not None:
                component_cards_v2 = self.constraint_adapter_v2.retrieve_for_component(
                    component_plan=comp,
                    component_schema=enhanced_schema,
                    interface_plans=interface_plans,
                    max_constraints=CONFIG.constraint_engine.max_constraints_component,
                    per_family_limit=CONFIG.constraint_engine.per_family_limit,
                )
                closure_ids = set(obligation_audit.get("constraint_ids") or []) | set(
                    declarations["declared_constraint_ids"]
                )
                existing_card_ids = {
                    str(card.get("constraint_id") or "") for card in component_cards_v2
                }
                plan_rules = (
                    {
                        str(rule.get("constraint_id") or ""): rule
                        for rule in self.validation_service.engine.plan.get("rules", [])
                        if isinstance(rule, dict)
                        and str(rule.get("constraint_id") or "")
                    }
                    if self.validation_service is not None
                    else {}
                )
                for constraint_id in sorted(closure_ids - existing_card_ids):
                    rule = plan_rules.get(constraint_id)
                    if rule is None:
                        raise RuntimeError(
                            f"pinned V2 generation obligation {constraint_id} has no plan rule"
                        )
                    formal = rule.get("formal_spec") or {}
                    selector = rule.get("selector") or {}
                    component_cards_v2.append(
                        {
                            "constraint_id": constraint_id,
                            "source_sha256": str(rule.get("source_sha256") or ""),
                            "title": str(rule.get("title") or ""),
                            "summary": str(rule.get("title") or ""),
                            "class_tags": list(selector.get("tags") or []),
                            "property_tags": [],
                            "paths": [
                                "/".join(item.get("path") or [])
                                for item in obligation_audit.get("derived") or []
                                if item.get("constraint_id") == constraint_id
                            ],
                            "rule_family": str(
                                formal.get("rule_family") or "required_existence"
                            ),
                            "importance": "core",
                            "validation_policy": "must",
                            "usages": [
                                "generation_context",
                                "automatic_validation",
                            ],
                        }
                    )
                constraint_context_v2 = self.constraint_adapter_v2.render_prompt(component_cards_v2)
                retrieval_trace = dict(self.constraint_adapter_v2.retrieval_trace())
                if closure_ids:
                    combined_ids = sorted(
                        set(retrieval_trace.get("constraint_ids") or []) | closure_ids
                    )
                    retrieval_trace["constraint_ids"] = combined_ids
                    retrieval_trace["result_count"] = len(combined_ids)
                    retrieval_trace["backend"] = (
                        str(retrieval_trace.get("backend") or "unknown")
                        + "+pinned-plan-closure"
                    )
                    retrieval_trace["plan_closure_constraint_ids"] = sorted(
                        closure_ids
                    )
                self._constraint_retrieval_trace[comp_name] = retrieval_trace
            r1_component_design = comp

            # 4.3 单组件 Prompt（接口仅作为上下文参考；组件输出仍严格按组件 Schema）
            prompt = template_manager.get_round2_prompt_single(
                comp_plan=comp,
                interface_plans=interface_plans,
                component_schema=provider_schema,
                interface_index=iface_index_for_prompt,
                r1_component_design=r1_component_design,
                memory_context=memory_context or "",
                architecture_design=architecture_design.__dict__,
                # ****** 新增参数: 传递已知路径 ******
                known_paths=known_instance_paths
            )
            prompt += constraint_context_v2
            # 类型库与引用规范
            prompt += self._add_direct_reference_guidance(architecture_design)

            # 4.4 调用 LLM（严格约束该组件 Schema）
            try:
                self.gemini_client.pipeline_phase = "round2.component"
                resp, in_tok, out_tok, ttl_tok = self.gemini_client.generate_with_schema(
                    prompt=prompt,
                    schema=provider_schema,
                    seed=generation_seed,
                    temperature=CONFIG.llm.get_temperature('round2'),
                    max_retries=CONFIG.llm.max_retries
                )
            except Exception:
                # The concrete client exposes the parsed provider payload even
                # when its local schema gate refuses it.  Persist that evidence
                # before propagating the failure; scripted clients may omit it.
                rejected_raw = getattr(
                    self.gemini_client, "last_raw_schema_payload", None
                )
                if isinstance(rejected_raw, dict):
                    raw_artifact = self._save_component_response_to_file(
                        f"{comp_name}_provider_raw", rejected_raw
                    )
                    self._provider_payload_provenance.append(
                        {
                            "scope": "component",
                            "component": str(comp_name),
                            "raw_provider_payload": raw_artifact,
                            "raw_provider_schema_status": "RAW_FAIL",
                            "normalization_status": "NOT_APPLICABLE",
                            "final_atlas_status": "NOT_EVALUATED",
                        }
                    )
                raise

            # This is the first operation on the returned payload.  The bytes
            # and file SHA are durable before partition restoration,
            # deterministic identity assembly, or value materialization.
            raw_artifact = self._save_component_response_to_file(
                f"{comp_name}_provider_raw", resp
            )
            raw_errors = sorted(
                Draft202012Validator(provider_schema).iter_errors(resp),
                key=lambda error: list(error.absolute_path),
            )
            provider_provenance = {
                "scope": "component",
                "component": str(comp_name),
                "raw_provider_payload": raw_artifact,
                "raw_provider_schema_status": (
                    "PASS" if not raw_errors else "RAW_FAIL"
                ),
                "normalization_status": "NOT_APPLICABLE",
                "final_atlas_status": "NOT_EVALUATED",
            }
            self._provider_payload_provenance.append(provider_provenance)
            if raw_errors:
                first = raw_errors[0]
                location = "/".join(
                    str(item) for item in first.absolute_path
                ) or "<root>"
                raise ValueError(
                    f"raw provider payload violates admitted-only schema at "
                    f"{location}: {first.message}"
                )
            resp, provider_merge_audit = merge_provider_schema_payloads(
                {"full": resp}, full_provider_schema, provider_partition_plan
            )
            value_obligation_audit["provider_schema_merge"] = provider_merge_audit
            self._save_component_response_to_file(
                f"{comp_name}_provider_projection_restored", resp
            )
            resp, instance_assembly_audit = materialize_admitted_provider_payload(
                resp,
                full_provider_schema,
                instance_projection_plan,
                instance_skeleton,
            )
            value_obligation_audit["provider_instance_assembly"] = (
                instance_assembly_audit
            )
            provider_provenance["normalization_status"] = (
                instance_assembly_audit["normalization_status"]
            )
            self._save_component_response_to_file(
                f"{comp_name}_provider_admitted_assembled", resp
            )
            resp, value_materialization_audit = materialize_deterministic_values(
                resp,
                enhanced_schema,
                declared_provider_design,
            )
            value_obligation_audit["provider_materialization_result"] = (
                value_materialization_audit
            )
            provider_provenance["final_atlas_status"] = "PASS"
            self._save_component_prompt_to_file(comp_name, prompt)
            self._save_component_response_to_file(comp_name, resp)

            token_stats["input"] += in_tok
            token_stats["output"] += out_tok
            token_stats["total"] += ttl_tok

            new_paths = self._extract_instance_paths(resp, comp_name)
            if CONFIG.debug_mode:
                print(f"[DEBUG] 从 {comp_name} 提取到新路径: {new_paths}")

            # 4.6 (新) 将新路径合并到已知路径字典中
            for path_type, path_list in new_paths.items():
                known_instance_paths.setdefault(path_type, []).extend(path_list)

            # 4.5 合并当前组件结果（用实例名作为键）
            # The provider schema is a single-root component schema and
            # partition_provider_schema already asserts exactly one call, so any
            # other shape is a contract break.  It is refused here, naming the
            # component and the root count, rather than surfacing later as a
            # bundle/payload mismatch inside the typed-repair bind.
            if not isinstance(resp, dict) or len(resp) != 1:
                raise ValueError(
                    f"component {comp_name!r} returned "
                    f"{len(resp) if isinstance(resp, dict) else 0} payload roots; "
                    "the component provider schema declares exactly one"
                )
            comp_type_key = next(iter(resp.keys()))
            root = resp.get(comp_type_key) or {}
            if not isinstance(root, dict):
                raise ValueError(
                    f"component {comp_name!r} did not produce an object payload"
                )
            # Captured before projection: the repair stage edits the
            # provider-space payload and re-projects, so the XSD serializer
            # still decides tags and sibling order.
            self._register_component_repair_target(
                str(comp_name),
                comp_type_key,
                deepcopy(root),
                enhanced_schema=enhanced_schema,
                declared_provider_design=declared_provider_design,
                materialization_audit=value_materialization_audit,
            )
            root = apply_projection_map(
                root,
                self._component_projection_maps.get(comp_name),
            )
            merged_json[comp_name] = root
            merged_json[comp_name]["_type"] = comp_type_key

        # 5) 转为 ARXML（逐文件输出）并立即执行同一版本的验证计划。
        component_xml_map, interface_xml_map = self._convert_each_to_arxml(merged_json)
        arxml_bundle = {
            "components": component_xml_map,
            "interfaces": interface_xml_map,
        }
        # Bind and persist even when automatic repair is disabled.  The formal
        # experiment generates with repair off and evaluates a separately
        # scheduled repair cohort in a fresh process.
        self._typed_repair.bind(self._repair_targets, arxml_bundle)
        typed_repair_context = self._typed_repair.export_context(arxml_bundle)
        typed_repair_context_path = self._persist_typed_repair_context(
            typed_repair_context
        )
        validation_context = None
        validation = None
        repair_audit = {
            "schema_version": "1.0", "enabled": False,
            "attempted_rounds": 0, "accepted_rounds": 0,
            "stop_reason": "disabled",
            "token_usage": {"input": 0, "output": 0, "total": 0},
            "history": [],
        }
        if self.validation_service is not None:
            validation_context = self.validation_service.build_validation_context(
                self._constraint_retrieval_trace,
                declared_use_cases=declarations["declared_use_cases"],
                declared_constraint_ids=declarations["declared_constraint_ids"],
                declared_targets=declarations["declared_targets"],
                declared_parameters=declarations["declared_parameters"],
                intent_scope=declarations["intent_scope"],
                declared_capability_scopes=declarations["declared_capability_scopes"],
                manual_evidence_scope=declarations["manual_evidence_scope"],
            )
            validation = self.validation_service.validate_bundle(
                arxml_bundle, validation_context=validation_context
            )
            validation = self._merge_bundle_selection_obligations(
                arxml_bundle,
                validation,
                architecture_design.component_plan or [],
            )
            if CONFIG.validation.auto_repair_enabled:
                repair_loop = BundleRepairLoop(
                    self.validation_service,
                    self._repair_bundle_candidate,
                    max_rounds=CONFIG.validation.auto_repair_max_rounds,
                    report_enricher=lambda candidate, candidate_report: (
                        self._merge_bundle_selection_obligations(
                            candidate,
                            candidate_report,
                            architecture_design.component_plan or [],
                        )
                    ),
                )
                arxml_bundle, validation, repair_audit = repair_loop.run(
                    arxml_bundle, validation, validation_context=validation_context
                )
                repair_tokens = repair_audit.get("token_usage") or {}
                token_stats["input"] += int(repair_tokens.get("input") or 0)
                token_stats["output"] += int(repair_tokens.get("output") or 0)
                token_stats["total"] += int(repair_tokens.get("total") or 0)

        if validation is None:
            validation = self._merge_bundle_selection_obligations(
                arxml_bundle,
                None,
                architecture_design.component_plan or [],
            )
        selection_obligations = validation.get("selection_obligations") or {}

        # 6) 统计和可追溯运行信息
        generation_time = time.time() - start_time
        provider_status_counters: Dict[str, Dict[str, int]] = {
            "raw_provider_schema_status": {},
            "normalization_status": {},
            "final_atlas_status": {},
        }
        for item in self._provider_payload_provenance:
            for field, counts in provider_status_counters.items():
                status = str(item.get(field) or "NOT_EVALUATED")
                counts[status] = counts.get(status, 0) + 1
        final_atlas_status = (
            validation.get("decision") if validation else "NOT_EVALUATED"
        )
        stats = {
            "input_tokens": token_stats["input"],
            "output_tokens": token_stats["output"],
            "total_tokens": token_stats["total"],
            "generation_time": generation_time,
            "generation_seed": generation_seed,
            "selection_path_compilation": self._selection_path_compilation_trace,
            "generation_obligations": self._generation_obligation_trace,
            "constraint_retrieval": self._constraint_retrieval_trace,
            "validation_context": validation_context,
            "auto_repair": repair_audit,
            "typed_repair": list(self._typed_repair.trace),
            "typed_repair_context": {
                "path": str(typed_repair_context_path),
                "content_sha256": typed_repair_context["content_sha256"],
                "bundle_sha256": typed_repair_context["bundle_sha256"],
                "xsd_sha256": typed_repair_context["xsd_sha256"],
                "serialization_manifest_sha256": typed_repair_context[
                    "serialization_manifest_sha256"
                ],
                "target_count": len(typed_repair_context["targets"]),
            },
            "selection_obligations": selection_obligations,
            "validation": validation,
            "validation_decision": validation.get("decision") if validation else "DISABLED",
            "validation_summary": validation.get("summary", {}) if validation else {},
            "artifact_profile": validation.get("artifact_profile", {}) if validation else {},
            "artifact_profile_decision": (
                (validation.get("artifact_profile") or {}).get("decision")
                if validation else "DISABLED"
            ),
            "provider_responses": list(self.gemini_client.response_audit),
            "provider_payload_provenance": deepcopy(
                self._provider_payload_provenance
            ),
            "provider_payload_status_counters": provider_status_counters,
            "raw_provider_schema_status": (
                "RAW_FAIL"
                if provider_status_counters["raw_provider_schema_status"].get(
                    "RAW_FAIL", 0
                )
                else "PASS"
            ),
            "normalization_status": (
                "NORMALIZED"
                if provider_status_counters["normalization_status"].get(
                    "NORMALIZED", 0
                )
                else "NOT_APPLICABLE"
            ),
            "final_atlas_status": final_atlas_status,
            "provider_counters": {
                "calls": self.gemini_client.call_count,
                "successes": self.gemini_client.success_count,
                "errors": self.gemini_client.error_count,
            },
        }
        return arxml_bundle, stats

    @staticmethod
    def _merge_bundle_selection_obligations(
        bundle: Dict[str, Any],
        validation_report: Dict[str, Any] | None,
        component_plans: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        obligations = validate_selection_obligations(bundle, component_plans)
        return merge_selection_obligations(validation_report, obligations)

    @staticmethod
    def _validation_declarations(custom_requirements: Dict[str, Any] | None) -> Dict[str, Any]:
        """Read explicit intent without silently coercing malformed values.

        The ``validation_*`` names are retained only as compatibility aliases
        for callers predating the public ``declared_*`` validation-context
        contract.
        """
        source = custom_requirements or {}
        aliases = {
            "declared_use_cases": "validation_use_cases",
            "declared_constraint_ids": "validation_constraint_ids",
            "declared_targets": "validation_targets",
            "declared_parameters": "validation_parameters",
            "intent_scope": "validation_intent_scope",
            "declared_capability_scopes": "validation_capability_scopes",
            "manual_evidence_scope": "validation_manual_evidence_scope",
        }
        values: Dict[str, Any] = {}
        for public_name, legacy_name in aliases.items():
            value = source.get(public_name)
            if value is None:
                value = source.get(legacy_name)
            if value is None:
                if public_name in {"declared_use_cases", "declared_constraint_ids"}:
                    value = []
                elif public_name == "intent_scope":
                    value = "partial"
                elif public_name == "declared_capability_scopes":
                    value = []
                elif public_name == "manual_evidence_scope":
                    value = None
                else:
                    value = {}
            values[public_name] = value

        if not isinstance(values["declared_use_cases"], list):
            raise ValueError("declared_use_cases must be an array")
        if not isinstance(values["declared_constraint_ids"], list):
            raise ValueError("declared_constraint_ids must be an array")
        if not isinstance(values["declared_targets"], dict):
            raise ValueError("declared_targets must be an object")
        if not isinstance(values["declared_parameters"], dict):
            raise ValueError("declared_parameters must be an object")
        if values["intent_scope"] not in {"partial", "complete"}:
            raise ValueError("intent_scope must be 'partial' or 'complete'")
        if not isinstance(values["declared_capability_scopes"], list):
            raise ValueError("declared_capability_scopes must be an array")
        if values["manual_evidence_scope"] is not None and not isinstance(
            values["manual_evidence_scope"], dict
        ):
            raise ValueError("manual_evidence_scope must be an object or null")
        return values

    def _register_component_repair_target(
        self,
        comp_name: str,
        comp_type_key: str,
        provider_payload: Dict[str, Any],
        *,
        enhanced_schema: Dict[str, Any],
        declared_provider_design: Any,
        materialization_audit: Dict[str, Any],
    ) -> None:
        """Keep everything the typed repair stage needs for one component.

        ``enhanced_schema`` is the authoritative full schema, not the
        model-facing one: deterministic value properties are removed from the
        provider schema and re-materialized afterwards, so only the full schema
        accepts a finished payload.
        """
        root_schema = (enhanced_schema.get("properties") or {}).get(comp_type_key)
        if not isinstance(root_schema, dict):
            raise ValueError(
                f"component schema for {comp_name!r} has no {comp_type_key} root"
            )
        immutable = tuple(
            tuple(item.get("resolved_path") or ())
            for item in (materialization_audit.get("applied") or [])
            if item.get("resolved_path")
        )
        self._repair_targets[("components", comp_name)] = RepairTarget(
            kind="components",
            name=comp_name,
            element_type=comp_type_key,
            payload=provider_payload,
            root_schema=root_schema,
            document_schema=enhanced_schema,
            declared_value_design=declared_provider_design,
            projection_map=self._component_projection_maps.get(comp_name),
            immutable_paths=immutable,
        )

    def _register_interface_repair_targets(
        self,
        normalized_interfaces: Dict[str, Any],
        interface_schema: Dict[str, Any],
    ) -> None:
        """Interfaces share one schema, so only the per-type item schema differs."""
        properties = interface_schema.get("properties") or {}
        for key, payload in (normalized_interfaces or {}).items():
            if not isinstance(payload, dict):
                continue
            interface_type = str(payload.get("_type") or "")
            type_schema = properties.get(interface_type)
            if not isinstance(type_schema, dict):
                continue
            item_schema = type_schema.get("items")
            if not isinstance(item_schema, dict):
                continue
            name = str(payload.get("SHORT-NAME") or payload.get("SHORTNAME") or key)
            self._repair_targets[("interfaces", name)] = RepairTarget(
                kind="interfaces",
                name=name,
                package_name=getattr(
                    self, "_interface_package_name", INTERFACE_PACKAGE
                ),
                element_type=interface_type,
                payload={
                    field: value
                    for field, value in payload.items()
                    if field != "_type"
                },
                root_schema=item_schema,
            )

    def _repair_provider_call(
        self, prompt: str, schema: Dict[str, Any], seed: Optional[int]
    ) -> Tuple[Dict[str, Any], int, int, int]:
        self.gemini_client.pipeline_phase = "round2.repair"
        return self.gemini_client.generate_with_schema(
            prompt=prompt,
            schema=schema,
            seed=seed,
            temperature=CONFIG.validation.auto_repair_temperature,
            max_retries=CONFIG.llm.max_retries,
        )

    @staticmethod
    def _persist_typed_repair_context(context: Dict[str, Any]) -> Path:
        """Atomically persist the structured state required by later repair.

        Formal generation and repair run in different processes. Persisting
        this hash-qualified context prevents repair from parsing XML back into
        an approximate payload or rebuilding under a different schema state.
        """
        digest = str(context.get("content_sha256") or "")
        if len(digest) != 64:
            raise ValueError("typed-repair context has no canonical SHA-256")
        directory = Path(CONFIG.output_dir) / "typed_repair_context"
        directory.mkdir(parents=True, exist_ok=True)
        destination = directory / f"{digest}.json"
        text = json.dumps(context, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if destination.exists():
            if destination.read_text(encoding="utf-8") != text:
                raise RuntimeError("typed-repair context hash collision or stale artifact")
            return destination
        temporary = destination.with_suffix(".json.tmp")
        temporary.write_text(text, encoding="utf-8")
        temporary.replace(destination)
        return destination

    def _repair_bundle_candidate(
        self,
        bundle: Dict[str, Any],
        report: Dict[str, Any],
        repair_prompt: str,
        round_number: int,
    ) -> RepairProposal:
        """Propose one typed repair candidate at the structured value layer.

        The model receives enumerated edit locations that the program derived
        from the validation findings and returns index selections plus values.
        It never writes a path and never writes XML, so a repair cannot
        introduce a structure that generation could not have produced.
        """
        return self._typed_repair.propose(
            bundle,
            report,
            repair_prompt,
            round_number,
            provider=self._repair_provider_call,
            seed=(
                self._generation_seed + round_number
                if self._generation_seed is not None else None
            ),
            context_json=json.dumps(
                report.get("validation_context"), ensure_ascii=False, indent=2
            ),
        )

    def _build_single_component_schema(self, comp: Dict[str, Any]) -> Dict[str, Any]:
        """
        Round2 单组件 schema 构建入口：
        - 直接调用 query_engine 生成组件 Schema
        - 生成后执行“Round1 include -> required”增强，确保强一致
        """
        schema = self.query_engine.generate_component_schema_fixed(comp)
        # ✅ 强一致：把 Round1 include 的所有子键设为 required（仅对命中的 variant 节点）
        schema = self._enforce_includes_required(comp, schema)
        provider_element_design = project_element_design_for_schema(
            comp.get("element_design") or {},
            self.query_engine.component_xml_projection_map(comp),
        )
        schema = apply_element_selections(schema, provider_element_design)
        return schema

    def _extract_instance_paths(self, component_json: Dict[str, Any], component_name: str) -> Dict[str, List[str]]:
        """
        【修正版】从单个组件的生成结果中，递归提取所有带SHORT-NAME的实例路径。
        规则：只要一个JSON对象有SHORT-NAME，就认为它是一个可引用的实例。
        """
        paths = {}

        def recurse_children(parent_node: Dict[str, Any], parent_path: str):
            """
            【新逻辑】递归函数，只处理 parent_node 的子节点。
            """
            for key, value in parent_node.items():
                if key == "SHORT-NAME":
                    continue

                if isinstance(value, dict):
                    short_name = value.get("SHORT-NAME")
                    if short_name:
                        # 有名字的实例：记录路径并继续递归
                        child_path = f"{parent_path}/{short_name}"
                        child_type = key
                        paths.setdefault(child_type, []).append(child_path)
                        recurse_children(value, child_path)
                    else:
                        # ✅ 修复：容器对象（如 DATA-ELEMENTS）
                        # 没有 SHORT-NAME，但需要继续递归其内容
                        # 路径不变，继续用父路径
                        recurse_children(value, parent_path)

                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            short_name = item.get("SHORT-NAME")
                            if short_name:
                                child_path = f"{parent_path}/{short_name}"
                                child_type = key
                                paths.setdefault(child_type, []).append(child_path)
                                recurse_children(item, child_path)
                            else:
                                # ✅ 添加容器处理
                                recurse_children(item, parent_path)

        # 顶层组件处理
        if component_json and len(component_json) == 1:
            comp_type_key = next(iter(component_json))
            root_data = component_json[comp_type_key]
            # 1. 先正确添加组件自身
            base_path = f"/Components/{component_name}"
            paths.setdefault(comp_type_key, []).append(base_path)
            # 2. 然后调用递归函数处理其【子节点】
            recurse_children(root_data, base_path)

        return paths
    # ****** 修正后的辅助方法 2: 按@DEST精准注入路径到Schema ******
    def _inject_paths_into_schema(
            self,
            schema: Dict[str, Any],
            known_paths: Dict[str, List[str]],
            current_component_name: str = None  # 新增参数
    ) -> Dict[str, Any]:
        """
        【增强版】遍历Schema，根据引用的上下文约束，智能注入路径到#text字段的enum。

        关键改进：
        1. 识别引用所在的上下文（事件、端口访问、数据元素等）
        2. 根据AUTOSAR封装原则，只注入符合作用域规则的路径
        3. 支持组件内引用和全局类型引用的区分
        """
        if not known_paths:
            return schema

        schema_copy = deepcopy(schema)

        # 定义作用域过滤规则
        def get_scope_filter_rule(path_trace: List[str]) -> str:
            """
            根据schema路径追踪，判断当前引用的作用域类型。
            返回值：'component_local' | 'interface_element' | 'global_type'
            """
            path_upper = [p.upper() for p in path_trace]

            # 规则1：事件中的START-ON-EVENT-REF只能引用本组件的Runnable
            if any(event_type in path_upper for event_type in [
                'TIMING-EVENT', 'DATA-RECEIVED-EVENT', 'INIT-EVENT',
                'DATA-SEND-COMPLETED-EVENT', 'OPERATION-INVOKED-EVENT',
                'DATA-RECEIVE-ERROR-EVENT', 'EXTERNAL-TRIGGER-OCCURRED-EVENT'
            ]) and 'START-ON-EVENT-REF' in path_upper:
                return 'component_local'

            # 规则2：Runnable内部的数据访问点中的PORT-PROTOTYPE-REF必须是本组件端口
            if any(access_point in path_upper for access_point in [
                'DATA-SEND-POINTS', 'DATA-RECEIVE-POINT-BY-ARGUMENTS',
                'DATA-RECEIVE-POINT-BY-VALUES', 'DATA-READ-ACCESSS', 'DATA-WRITE-ACCESSS'
            ]):
                # 如果路径中包含AUTOSAR-VARIABLE-IREF和PORT-PROTOTYPE-REF
                if 'AUTOSAR-VARIABLE-IREF' in path_upper and 'PORT-PROTOTYPE-REF' in path_upper:
                    return 'component_local'
                # TARGET-DATA-PROTOTYPE-REF可以引用任何接口的数据元素
                if 'TARGET-DATA-PROTOTYPE-REF' in path_upper:
                    return 'interface_element'

            # 规则3：SERVER-CALL-POINTS中的CONTEXT-PORT-REF必须是本组件端口
            if 'SERVER-CALL-POINTS' in path_upper:
                if any(ctx in path_upper for ctx in ['CONTEXT-R-PORT-REF', 'CONTEXT-P-PORT-REF']):
                    return 'component_local'
                # OPERATION-IREF中的TARGET-REQUIRED-OPERATION-REF可以引用接口操作
                if 'TARGET-REQUIRED-OPERATION-REF' in path_upper or 'TARGET-PROVIDED-OPERATION-REF' in path_upper:
                    return 'interface_element'

            # 规则4：端口的接口引用（PROVIDED-INTERFACE-TREF/REQUIRED-INTERFACE-TREF）是全局类型
            if 'PORTS' in path_upper and any(tref in path_upper for tref in [
                'PROVIDED-INTERFACE-TREF', 'REQUIRED-INTERFACE-TREF',
                'PROVIDED-REQUIRED-INTERFACE-TREF'
            ]):
                return 'global_type'

            # 规则5：接口数据元素的TYPE-TREF是全局类型
            if 'TYPE-TREF' in path_upper:
                return 'global_type'

            # 默认：允许引用接口中的元素
            return 'interface_element'

        def filter_paths_by_scope(
                paths: List[str],
                scope: str,
                dest_types: List[str],
                component_name: str = None
        ) -> tuple[List[str], bool]:  # 返回路径列表和是否使用enum标志
            """
            返回值：(filtered_paths, use_enum)
            - use_enum=True: 正常注入enum
            - use_enum=False: 不注入enum，让LLM自由填写（但通过prompt约束格式）
            """

            if scope == 'component_local':
                # 对于组件内引用，不使用enum约束
                # 因为这些路径在生成时还不存在
                return [], False  # 返回空列表，标记不使用enum

            elif scope == 'interface_element':
                filtered = [
                    p
                    for p in paths
                    if p.startswith(f"{self._interface_package_ref}/")
                ]
                return filtered, True

            elif scope == 'global_type':
                return paths, True

            return paths, True



        def recurse(node: Any, path_trace: List[str] = None):
            """
            递归遍历schema，在引用节点处注入过滤后的路径。

            Args:
                node: 当前schema节点
                path_trace: 从根到当前节点的路径追踪（用于判断上下文）
            """
            if path_trace is None:
                path_trace = []

            if not isinstance(node, dict):
                return

            # 定位到引用对象的Schema定义 (特征: 包含@DEST和#text)
            props = node.get("properties", {})
            if node.get("type") == "object" and "@DEST" in props and "#text" in props:
                # 1. 读取@DEST允许的类型列表
                dest_prop_schema = props["@DEST"]
                allowed_dest_types = dest_prop_schema.get("enum", [])

                if not allowed_dest_types:
                    return

                # 2. 判断当前引用的作用域
                scope = get_scope_filter_rule(path_trace)

                # 3. 收集所有匹配@DEST类型的候选路径
                candidate_paths = []
                for dest_type in allowed_dest_types:
                    if dest_type in known_paths:
                        candidate_paths.extend(known_paths[dest_type])

                # 4. 根据作用域规则过滤路径
                filtered_paths, use_enum = filter_paths_by_scope(  # ✅ 正确解包元组
                    candidate_paths,
                    scope,
                    allowed_dest_types,
                    current_component_name
                )

                # 5. 根据use_enum标志决定注入策略
                text_prop_schema = props["#text"]

                if use_enum:
                    # 常规情况：注入enum约束
                    if filtered_paths:
                        text_prop_schema["enum"] = sorted(list(set(filtered_paths)))
                        text_prop_schema["examples"] = [filtered_paths[0]]

                        # 添加作用域说明（帮助调试）
                        if CONFIG.debug_mode:
                            text_prop_schema["x-scope"] = scope
                            text_prop_schema[
                                "x-filter-info"] = f"Filtered {len(candidate_paths)} candidate paths to {len(filtered_paths)}."
                    else:
                        # 过滤后没有可用路径，记录警告
                        if CONFIG.debug_mode:
                            print(
                                f"[WARNING] 引用位置 {'/'.join(path_trace[-3:])} 的作用域'{scope}'下没有可用路径")
                            print(
                                f"[WARNING] @DEST类型: {allowed_dest_types}, 候选路径数: {len(candidate_paths)}")
                else:
                    # component_local情况：不注入enum，添加格式约束
                    if current_component_name:
                        text_prop_schema["pattern"] = f"^/Components/{current_component_name}/.*$"
                        text_prop_schema["description"] = (
                            f"Must reference an instance owned by component {current_component_name}. "
                            f"Path format: /Components/{current_component_name}/{{ElementName}}"
                        )

                        if CONFIG.debug_mode:
                            text_prop_schema["x-scope"] = scope
                            text_prop_schema["x-constraint-type"] = "pattern (component_local)"
                            print(
                                f"[DEBUG] component_local引用: 添加pattern约束 ^/Components/{current_component_name}/.*$")
                    else:
                        if CONFIG.debug_mode:
                            print(f"[WARNING] component_local作用域但缺少组件名，无法添加pattern约束")

            # 递归遍历Schema的所有子节点
            for key, value in node.items():
                if isinstance(value, dict):
                    # 将当前key加入路径追踪
                    recurse(value, path_trace + [key])
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            recurse(item, path_trace + [key])

        recurse(schema_copy, [])
        return schema_copy

    # ****** 新增辅助方法: 构建包含深层实例的详细接口索引 ******
    # ****** CORRECTED FUNCTION: Replace the original in round2_generator.py ******
    def _build_detailed_interface_index(self, normalized_ifaces: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        【CORRECTED VERSION】Traverses the normalized interface instances to recursively
        extract all elements with a SHORT-NAME, building a detailed index of all
        referable instance paths, including deeply nested elements like data-prototypes
        and operations.

        This version correctly handles intermediate container objects (like DATA-ELEMENTS
        and OPERATIONS) that do not have a SHORT-NAME themselves, ensuring that the
        recursion continues until all nested elements are found.
        """
        if not normalized_ifaces:
            return []

        detailed_index = []

        def extract_paths_recursive(node: Any, parent_path: str, node_type_tag: str):
            """
            A robust recursive helper function to find all paths.

            Args:
                node: The current JSON node (can be a dict or a list).
                parent_path: The AUTOSAR path of the parent element.
                node_type_tag: The XML tag representing the type of the current node
                               (e.g., 'CLIENT-SERVER-OPERATION').
            """
            # Case 1: The node is a dictionary (JSON object)
            if isinstance(node, dict):
                short_name = node.get("SHORT-NAME")
                # Check if it's an instantiable element with a name
                if short_name:
                    # Construct the full path for this element
                    current_path = f"{parent_path}/{short_name}"
                    # Add it to our index
                    detailed_index.append({
                        "name": short_name,
                        "type": node_type_tag,
                        "path": current_path
                    })
                    # Continue searching for children within this element
                    parent_path_for_children = current_path
                else:
                    # It's a container without a name (e.g., DATA-ELEMENTS),
                    # so it doesn't get its own path segment.
                    parent_path_for_children = parent_path

                # **CRITICAL FIX**: Always recurse into children, regardless of
                # whether the current node had a SHORT-NAME or not.
                for key, value in node.items():
                    # Skip metadata fields to avoid infinite loops or incorrect typing
                    if key.startswith(("@", "#")) or key in ["SHORT-NAME", "_type"]:
                        continue
                    # The child's type is its key in the parent object
                    extract_paths_recursive(value, parent_path_for_children, key)

            # Case 2: The node is a list
            elif isinstance(node, list):
                # Process each item in the list. All items share the same type tag.
                for item in node:
                    extract_paths_recursive(item, parent_path, node_type_tag)

        # --- Main loop to start the process for each top-level interface ---
        for name, data in normalized_ifaces.items():
            interface_type = data.get("_type")
            interface_path = f"{self._interface_package_ref}/{name}"

            # 1. Add the top-level interface itself to the index
            detailed_index.append({
                "name": name,
                "type": interface_type,
                "path": interface_path
            })

            # 2. Start the deep recursive search for all its children
            # 创建一个副本，移除顶层SHORT-NAME，避免路径重复
            data_copy = {k: v for k, v in data.items() if k != "SHORT-NAME"}
            extract_paths_recursive(data_copy, interface_path, interface_type)

        return detailed_index

    def _enforce_includes_required(self, comp_plan: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        将 Round1 element_design 中 preselect.variant 对应的 include 子键，
        在 Schema 中提升为 required（仅当这些子键真实出现在该 variant 节点的 properties 时）。
        - 不修改 KG 查询逻辑，仅对返回的 Schema 做安全后处理
        - 以“父属性键 == variant 名称”作为定位依据；遍历时大小写不敏感
        """
        # 1) 收集 Round1 的 variant -> includes（均大写化便于匹配）
        variant_includes: Dict[str, set] = {}
        ed = (comp_plan.get("element_design") or {})
        ib = (ed.get("internal_behaviors") or {})
        for r in ib.get("runnables") or []:
            for elem in (r.get("elements") or []):
                if not isinstance(elem, dict):
                    continue
                for ps in (elem.get("preselect") or []):
                    variant = str(ps.get("variant") or "").strip().upper()
                    includes = [str(x).strip().upper() for x in (ps.get("include") or [])]
                    if variant and includes:
                        variant_includes.setdefault(variant, set()).update(includes)

        if not variant_includes:
            return schema  # 无需增强

        # 2) 深度遍历 schema：当当前对象节点的“父键”命中某个 variant 时，把 include 子键并入 required
        def _walk(node: Any, parent_key: Optional[str] = None):
            if not isinstance(node, dict):
                return
            ntype = node.get("type")

            if ntype == "object":
                props = node.get("properties") or {}
                # 命中 variant：把 includes -> required（仅对存在于 properties 的键）
                if parent_key and parent_key.upper() in variant_includes:
                    need = variant_includes[parent_key.upper()]
                    # 建立 “大写 -> 实际键名”的映射，安全对齐
                    upper2real = {str(k).strip().upper(): k for k in props.keys()}
                    req = node.setdefault("required", [])
                    for inc in need:
                        real = upper2real.get(inc)
                        if real and real not in req:
                            req.append(real)

                # 递归子属性
                for ck, cv in props.items():
                    _walk(cv, ck)

            elif ntype == "array" and isinstance(node.get("items"), dict):
                # 数组项沿用相同 parent_key 继续下潜（parent_key 决定是否命中 variant）
                _walk(node["items"], parent_key)

        _walk(schema, None)
        return schema


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

    def _format_standard_types(self, standard_types: Dict[str, Any]) -> str:
        """格式化标准类型引用 - 改进版，基于动态加载的类型"""

        prompt = "\n\n## Standard data-type reference rules\n"
        prompt += "Interface data elements must reference IMPLEMENTATION-DATA-TYPE, never SW-BASE-TYPE.\n\n"

        prompt += "### Available implementation data types for interfaces and ports\n"
        prompt += "Use one of these types for interface DATA-ELEMENT values:\n\n"

        for type_info in standard_types["implementation_types"][:15]:  # 显示前15个常用类型
            prompt += f"- `{type_info['path']}`  # {type_info['name']}"
            if type_info.get('description'):
                prompt += f" - {type_info['description'][:50]}"
            prompt += "\n"

        if len(standard_types["implementation_types"]) > 15:
            prompt += f"... plus {len(standard_types['implementation_types']) - 15} additional standard types\n"

        prompt += "\n### Valid type-reference example\n"
        prompt += "```xml\n"
        prompt += '<TYPE-TREF DEST="IMPLEMENTATION-DATA-TYPE">/AUTOSAR_Platform/ImplementationDataTypes/uint16</TYPE-TREF>\n'
        prompt += "```\n\n"

        # 添加ComputMethod信息
        if standard_types.get("compu_methods"):
            prompt += "### Available computation methods (CompuMethod)\n"
            for compu_info in standard_types["compu_methods"][:5]:
                prompt += f"- `{compu_info['path']}` ({compu_info['category']})\n"

        return prompt

    def _add_direct_reference_guidance(self, architecture_design: ArchitectureDesign) -> str:
        """
        精简版引用指导：
        - 不再展开具体组件/接口的示例清单，避免重复冗长
        - 只保留硬规则 + 最少必要的占位示例
        """
        # 只给一段非常短的规则，避免重复列举多个组件/接口示例
        return (
            "\n\n## Reference-path rules\n"
            "Every *-REF uses a complete absolute path, never a semantic description.\n"
            "- Component: /Components/<ComponentShortName>\n"
            "- Port: /Components/<ComponentShortName>/<PortName>\n"
            "- Runnable: /Components/<ComponentShortName>/<InternalBehaviorShortName>/<RunnableShortName>\n"
            f"- Interface: {self._interface_package_ref}/<InterfaceShortName>\n"
        )


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

    def _save_component_response_to_file(
        self, comp_name: str, resp: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Persist a component payload and return its non-secret file identity.

        Provider provenance is an admission artifact, so persistence failures
        are fatal instead of being reduced to debug warnings.
        """
        output_dir = Path(CONFIG.output_dir) / "debug"
        output_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        fp = output_dir / f"round2_response_{comp_name}_{ts}.json"
        payload = (
            json.dumps(resp, indent=2, ensure_ascii=False) + "\n"
        ).encode("utf-8")
        fp.write_bytes(payload)
        record = {
            "path": str(fp),
            "file_sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload),
        }
        if CONFIG.debug_mode:
            print(f"[DEBUG] 单组件Response已保存: {fp}")
        return record

    def _normalize_interfaces_object(self, iface_grouped: Dict[str, Any]) -> Dict[str, Any]:
        """
        将 LLM 按 interface_schema 产出的“类型分组对象”规范化为：
           { "<SHORT-NAME>": { "_type": "<TYPE>", ...其余字段... }, ... }
        这样可以直接被 _convert_each_to_arxml/render_document 消费。
        - 不做结构重写，不丢字段，只增加 _type，并以 SHORT-NAME 作为 key。
        - 若条目缺少 SHORT-NAME，则跳过该条（无法命名）。
        """
        if not isinstance(iface_grouped, dict):
            return {}
        out: Dict[str, Any] = {}
        for type_key, items in iface_grouped.items():
            if not isinstance(items, list):
                continue
            for item in items:
                if not isinstance(item, dict):
                    continue
                short = item.get("SHORT-NAME") or item.get("SHORTNAME")
                if not short:
                    continue
                normalized = dict(item)
                normalized["_type"] = type_key
                out[str(short)] = normalized
        return out

    def _save_interfaces_instances(self, data: Dict[str, Any], suffix: str = "interfaces.instances.json") -> None:
        """调试用：将接口实例保存到文件（可选）。"""
        try:
            out_path = Path(CONFIG.output_dir) / suffix
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            if CONFIG.debug_mode:
                print(f"[WARNING] 保存接口实例失败: {e}")

    def _convert_single_component_to_arxml(self, comp_name: str, comp_data: Dict[str, Any]) -> str:
        return render_document(
            self.xml_serializer,
            package=COMPONENT_PACKAGE,
            element_type=comp_data.get("_type", "APPLICATION-SW-COMPONENT-TYPE"),
            payload=comp_data,
        )

    def _convert_single_interface_to_arxml(self, intf_name: str, intf_data: Dict[str, Any]) -> str:
        return render_document(
            self.xml_serializer,
            package=getattr(self, "_interface_package_name", INTERFACE_PACKAGE),
            element_type=intf_data.get("_type", "SENDER-RECEIVER-INTERFACE"),
            payload=intf_data,
        )

    # === ADD: 批量分发为「名称 → XML文本」的映射（组件 & 接口分开）===
    def _convert_each_to_arxml(self, merged_json: Dict[str, Any]) -> Tuple[Dict[str, str], Dict[str, str]]:
        def _short_name(obj: Dict[str, Any], fallback: str) -> str:
            return str(obj.get("SHORT-NAME") or obj.get("SHORTNAME") or fallback)

        component_xml_map: Dict[str, str] = {}
        interface_xml_map: Dict[str, str] = {}

        # ✅ 改进：区分实例名键和类型名键
        for k, v in (merged_json or {}).items():
            if not isinstance(v, dict) or k.startswith("_"):
                continue

            # 判断：k是实例名 or 类型名？
            # 如果v有_type字段，说明k是实例名
            if "_type" in v:
                # k = "VehicleMotionController"（实例名）
                component_xml_map[k] = self._convert_single_component_to_arxml(k, v)
            else:
                # 兼容旧格式：k可能是类型名，从v提取SHORT-NAME
                name = _short_name(v, k)
                component_xml_map[name] = self._convert_single_component_to_arxml(name, v)

        # 接口：来自 _interfaces（逻辑不变）
        for k, v in (merged_json or {}).get("_interfaces", {}).items():
            if not isinstance(v, dict):
                continue
            name = _short_name(v, k)
            interface_xml_map[name] = self._convert_single_interface_to_arxml(name, v)

        return component_xml_map, interface_xml_map


# 全局Round2生成器实例
round2_generator = Round2Generator()
