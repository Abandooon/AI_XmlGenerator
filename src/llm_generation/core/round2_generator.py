"""core/round2_generator.py - 修复版Round 2生成器

修复了参数调用不匹配问题和查询字段问题
专注于结构化输出，确保Schema生成流程正确
"""
import json
import time
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement, tostring

from src.validation.v2.repair_loop import BundleRepairLoop
from src.validation.v2.service import GeneratedArxmlValidationService
from .xsd_serializer import DeterministicXsdSerializer, apply_projection_map
from ..config import CONFIG
from ..knowledge.dynamic_query_engine import query_engine
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
        self.gemini_client = GeminiClient()
        self.query_engine = query_engine
        self.standard_type_manager = standard_type_manager  # 新增：标准类型管理器
        self.constraint_adapter_v2 = GenerationConstraintAdapterV2.try_default(CONFIG)
        if CONFIG.constraint_engine.enabled and self.constraint_adapter_v2 is None:
            raise RuntimeError(
                "ConstraintV2 is enabled, but retrieval cards/manifest could not be loaded"
            )
        self.validation_service = GeneratedArxmlValidationService.from_config(CONFIG)
        self._constraint_retrieval_trace: Dict[str, Any] = {}

        self._component_projection_maps: Dict[str, Dict[str, Any]] = {}
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
        self._component_projection_maps.clear()
        self._constraint_retrieval_trace = {}
        component_plans_map = {comp['name']: comp for comp in (architecture_design.component_plan or [])}
        interface_plans = architecture_design.interface_plan or []


        # 1) 准备接口 Schema（用于接口实例的强校验）
        interface_schema = self.query_engine.generate_multi_interface_schema(interface_plans)

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
                    interface_schema=interface_schema,
                    architecture_design=architecture_design.__dict__,
                    memory_context=memory_context or "",
                    standard_types=standard_types
                )
                interfaces_prompt += interface_constraint_context_v2
                # 保存接口 Prompt 以便调试
                self._save_prompt_to_file(interfaces_prompt)

                iface_resp, in_tok_i, out_tok_i, ttl_tok_i = self.gemini_client.generate_with_schema(
                    prompt=interfaces_prompt,
                    schema=interface_schema,  # 直接用接口 Schema 做强校验
                    temperature=CONFIG.llm.get_temperature('interface'),
                    max_retries=3
                )
                # 保存接口响应
                self._save_response_to_file(iface_resp)

                token_stats["input"] += in_tok_i
                token_stats["output"] += out_tok_i
                token_stats["total"] += ttl_tok_i

                # 规范化：{ type: [ {SHORT-NAME,...}, ... ] } → { "<SHORT-NAME>": { _type: "<type>", ... } }
                interfaces_obj = iface_resp if isinstance(iface_resp, dict) else {}
                normalized_ifaces = self._normalize_interfaces_object(interfaces_obj)
                # 可选：持久化接口实例，便于核对
                if normalized_ifaces:
                    try:
                        self._save_interfaces_instances(normalized_ifaces)
                    except Exception:
                        pass
                # 注入供后续 XML 转换
                merged_json["_interfaces"] = normalized_ifaces

                # ↓↓↓ 新增：为组件 Prompt 构建只读“接口实例索引”
                iface_index_for_prompt = self._build_detailed_interface_index(normalized_ifaces)

                # 若接口阶段失败或为空，则退化为基于 Round1 计划的索引（不新增函数，局部就地处理）
                if not iface_index_for_prompt:
                    iface_index_for_prompt = [
                        {
                            "name": it.get("name", ""),
                            "type": it.get("type", ""),
                            "path": f"/Interfaces/{it.get('name', '')}"
                        }
                        for it in (interface_plans or [])
                    ]

            except Exception as e:
                if CONFIG.debug_mode:
                    print(f"[WARNING] 接口实例生成失败，将跳过接口：{e}")



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
            # 4.1 单组件 Schema
            comp_schema = self._build_single_component_schema(comp)
            self._component_projection_maps[comp_name] = (
                self.query_engine.component_xml_projection_map(comp)
            )
            self._save_component_schema_to_file(comp_name, comp_schema)  # 保存原生Schema

            # 4.2 (新) 将已知的路径注入当前组件的Schema，生成增强版Schema
            enhanced_schema = self._inject_paths_into_schema(
                comp_schema,
                known_instance_paths,
                current_component_name=comp_name  # 传递当前组件名
            )
            if CONFIG.debug_mode and known_instance_paths:
                # 可以选择性保存增强后的Schema用于调试
                self._save_component_schema_to_file(f"{comp_name}_enhanced", enhanced_schema)

            constraint_context_v2 = ""
            if self.constraint_adapter_v2 is not None:
                component_cards_v2 = self.constraint_adapter_v2.retrieve_for_component(
                    component_plan=comp,
                    component_schema=enhanced_schema,
                    interface_plans=interface_plans,
                    max_constraints=CONFIG.constraint_engine.max_constraints_component,
                    per_family_limit=CONFIG.constraint_engine.per_family_limit,
                )
                constraint_context_v2 = self.constraint_adapter_v2.render_prompt(component_cards_v2)
                self._constraint_retrieval_trace[comp_name] = (
                    self.constraint_adapter_v2.retrieval_trace()
                )
            r1_component_design = comp

            # 4.3 单组件 Prompt（接口仅作为上下文参考；组件输出仍严格按组件 Schema）
            prompt = template_manager.get_round2_prompt_single(
                comp_plan=comp,
                interface_plans=interface_plans,
                component_schema=enhanced_schema,
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
            resp, in_tok, out_tok, ttl_tok = self.gemini_client.generate_with_schema(
                prompt=prompt,
                schema=enhanced_schema,
                temperature=CONFIG.llm.get_temperature('round2'),
                max_retries=3
            )
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

            # # 4.7 合并当前组件结果
            # if isinstance(resp, dict):
            #     merged_json.update(resp)

            # 4.5 合并当前组件结果（用实例名作为键）
            if isinstance(resp, dict):
                # --- 提取组件类型和数据 ---
                if len(resp) == 1:
                    comp_type_key = next(iter(resp.keys()))
                    root = resp.get(comp_type_key) or {}

                    # --- 恢复折叠的容器标签（保持原有逻辑）---
                    if not isinstance(root, dict):
                        raise ValueError(
                            f"component {comp_name!r} did not produce an object payload"
                        )
                    root = apply_projection_map(
                        root,
                        self._component_projection_maps.get(comp_name),
                    )
                    # ✅ 核心改动：用实例名作为键
                    merged_json[comp_name] = root
                    # 保存类型信息（供后续转换使用）
                    merged_json[comp_name]["_type"] = comp_type_key
                else:
                    # 兼容异常情况：直接合并
                    merged_json.update(resp)

        # 5) 转为 ARXML（逐文件输出）并立即执行同一版本的验证计划。
        component_xml_map, interface_xml_map = self._convert_each_to_arxml(merged_json)
        arxml_bundle = {
            "components": component_xml_map,
            "interfaces": interface_xml_map,
        }
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
            declarations = self._validation_declarations(custom_requirements)
            validation_context = self.validation_service.build_validation_context(
                self._constraint_retrieval_trace,
                declared_use_cases=declarations["declared_use_cases"],
                declared_constraint_ids=declarations["declared_constraint_ids"],
                declared_targets=declarations["declared_targets"],
                declared_parameters=declarations["declared_parameters"],
            )
            validation = self.validation_service.validate_bundle(
                arxml_bundle, validation_context=validation_context
            )
            if CONFIG.validation.auto_repair_enabled:
                repair_loop = BundleRepairLoop(
                    self.validation_service,
                    self._repair_bundle_candidate,
                    max_rounds=CONFIG.validation.auto_repair_max_rounds,
                )
                arxml_bundle, validation, repair_audit = repair_loop.run(
                    arxml_bundle, validation, validation_context=validation_context
                )
                repair_tokens = repair_audit.get("token_usage") or {}
                token_stats["input"] += int(repair_tokens.get("input") or 0)
                token_stats["output"] += int(repair_tokens.get("output") or 0)
                token_stats["total"] += int(repair_tokens.get("total") or 0)

        # 6) 统计和可追溯运行信息
        generation_time = time.time() - start_time
        stats = {
            "input_tokens": token_stats["input"],
            "output_tokens": token_stats["output"],
            "total_tokens": token_stats["total"],
            "generation_time": generation_time,
            "constraint_retrieval": self._constraint_retrieval_trace,
            "validation_context": validation_context,
            "auto_repair": repair_audit,
            "validation": validation,
            "validation_decision": validation.get("decision") if validation else "DISABLED",
            "validation_summary": validation.get("summary", {}) if validation else {},
        }
        return arxml_bundle, stats

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
        }
        values: Dict[str, Any] = {}
        for public_name, legacy_name in aliases.items():
            value = source.get(public_name)
            if value is None:
                value = source.get(legacy_name)
            if value is None:
                value = [] if public_name in {"declared_use_cases", "declared_constraint_ids"} else {}
            values[public_name] = value

        if not isinstance(values["declared_use_cases"], list):
            raise ValueError("declared_use_cases must be an array")
        if not isinstance(values["declared_constraint_ids"], list):
            raise ValueError("declared_constraint_ids must be an array")
        if not isinstance(values["declared_targets"], dict):
            raise ValueError("declared_targets must be an object")
        if not isinstance(values["declared_parameters"], dict):
            raise ValueError("declared_parameters must be an object")
        return values

    def _repair_bundle_candidate(
        self,
        bundle: Dict[str, Any],
        report: Dict[str, Any],
        repair_prompt: str,
        round_number: int,
    ) -> Tuple[Dict[str, Dict[str, str]], Dict[str, int]]:
        documents = [
            {"kind": kind, "name": name, "xml": xml_text}
            for kind in ("components", "interfaces")
            for name, xml_text in sorted((bundle.get(kind) or {}).items())
        ]
        schema = {
            "type": "object",
            "additionalProperties": False,
            "required": ["documents"],
            "properties": {
                "documents": {
                    "type": "array",
                    "minItems": len(documents),
                    "maxItems": len(documents),
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["kind", "name", "xml"],
                        "properties": {
                            "kind": {"type": "string", "enum": ["components", "interfaces"]},
                            "name": {"type": "string"},
                            "xml": {"type": "string", "minLength": 1},
                        },
                    },
                }
            },
        }
        prompt = (
            f"Controlled AUTOSAR repair round {round_number}.\n"
            "Return every input document exactly once with the same kind and name. "
            "Edit only what is needed to address the findings; never delete unrelated content. "
            "Preserve namespaces, SHORT-NAME identity, cross-file references, and XSD element order.\n\n"
            f"VALIDATION ACTIONS:\n{repair_prompt}\n\n"
            "HASH-PINNED VALIDATION CONTEXT:\n"
            f"{json.dumps(report.get('validation_context'), ensure_ascii=False, indent=2)}\n\n"
            "CURRENT ARXML DOCUMENTS:\n"
            f"{json.dumps(documents, ensure_ascii=False, indent=2)}"
        )
        response, in_tokens, out_tokens, total_tokens = self.gemini_client.generate_with_schema(
            prompt=prompt,
            schema=schema,
            temperature=CONFIG.validation.auto_repair_temperature,
            max_retries=2,
        )
        candidate: Dict[str, Dict[str, str]] = {"components": {}, "interfaces": {}}
        for item in (response or {}).get("documents") or []:
            kind = str(item.get("kind") or "")
            name = str(item.get("name") or "")
            if kind not in candidate or not name or name in candidate[kind]:
                raise ValueError(f"invalid or duplicate repaired document identity: {kind}/{name}")
            candidate[kind][name] = str(item.get("xml") or "")
        return candidate, {"input": in_tokens, "output": out_tokens, "total": total_tokens}

    def _build_single_component_schema(self, comp: Dict[str, Any]) -> Dict[str, Any]:
        """
        Round2 单组件 schema 构建入口：
        - 直接调用 query_engine 生成组件 Schema
        - 生成后执行“Round1 include -> required”增强，确保强一致
        """
        schema = self.query_engine.generate_component_schema_fixed(comp)
        # ✅ 强一致：把 Round1 include 的所有子键设为 required（仅对命中的 variant 节点）
        schema = self._enforce_includes_required(comp, schema)
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
                filtered = [p for p in paths if p.startswith("/Interfaces/")]
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
                                "x-filter-info"] = f"从{len(candidate_paths)}个候选路径过滤到{len(filtered_paths)}个"
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
                            f"必须引用本组件({current_component_name})的实例。"
                            f"路径格式：/Components/{current_component_name}/{{元素名称}}"
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
            interface_path = f"/Interfaces/{name}"

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
        """
        精简版引用指导：
        - 不再展开具体组件/接口的示例清单，避免重复冗长
        - 只保留硬规则 + 最少必要的占位示例
        """
        # 只给一段非常短的规则，避免重复列举多个组件/接口示例
        return (
            "\n\n## 引用路径规范\n"
            "所有 *-REF 必须使用完整的绝对路径，不允许语义化描述。\n"
            "- 组件路径示例：/Components/<ComponentShortName>\n"
            "- 端口路径示例：/Components/<ComponentShortName>/Ports/<PortName>\n"
            "- 接口路径示例：/Interfaces/<InterfaceShortName>\n"
        )


    def _add_component_to_xml(self, parent: Element, comp_name: str, comp_data: Dict[str, Any]):
        """Add a component through the hash-pinned XSD serialization plan."""
        comp_type = comp_data.get("_type", "APPLICATION-SW-COMPONENT-TYPE")
        comp_element = SubElement(parent, comp_type)
        self.xml_serializer.append_payload(
            comp_element,
            comp_data,
            root_element=comp_type,
            skip_keys=("_type",),
        )

    def _add_interface_to_xml(self, parent: Element, intf_name: str, intf_data: Dict[str, Any]):
        """Add an interface through the hash-pinned XSD serialization plan."""
        intf_type = intf_data.get("_type", "SENDER-RECEIVER-INTERFACE")
        intf_element = SubElement(parent, intf_type)
        self.xml_serializer.append_payload(
            intf_element,
            intf_data,
            root_element=intf_type,
            skip_keys=("_type",),
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

    def _normalize_interfaces_object(self, iface_grouped: Dict[str, Any]) -> Dict[str, Any]:
        """
        将 LLM 按 interface_schema 产出的“类型分组对象”规范化为：
           { "<SHORT-NAME>": { "_type": "<TYPE>", ...其余字段... }, ... }
        这样可以直接被 _convert_to_arxml/_add_interface_to_xml 消费。
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
        root = Element("AUTOSAR")
        root.set("xmlns", "http://autosar.org/schema/r4.0")
        root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        root.set("xsi:schemaLocation", "http://autosar.org/schema/r4.0 AUTOSAR_4-2-2.xsd")

        ar_packages = SubElement(root, "AR-PACKAGES")
        comp_package = SubElement(ar_packages, "AR-PACKAGE")
        SubElement(comp_package, "SHORT-NAME").text = "Components"
        comp_elements = SubElement(comp_package, "ELEMENTS")
        self._add_component_to_xml(comp_elements, comp_name, comp_data)

        rough = tostring(root, encoding="unicode")
        pretty = minidom.parseString(rough).toprettyxml(indent="  ")
        return "\n".join(ln for ln in pretty.split("\n") if ln.strip())

    def _convert_single_interface_to_arxml(self, intf_name: str, intf_data: Dict[str, Any]) -> str:
        root = Element("AUTOSAR")
        root.set("xmlns", "http://autosar.org/schema/r4.0")
        root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        root.set("xsi:schemaLocation", "http://autosar.org/schema/r4.0 AUTOSAR_4-2-2.xsd")

        ar_packages = SubElement(root, "AR-PACKAGES")
        intf_package = SubElement(ar_packages, "AR-PACKAGE")
        SubElement(intf_package, "SHORT-NAME").text = "Interfaces"
        intf_elements = SubElement(intf_package, "ELEMENTS")
        self._add_interface_to_xml(intf_elements, intf_name, intf_data)

        rough = tostring(root, encoding="unicode")
        pretty = minidom.parseString(rough).toprettyxml(indent="  ")
        return "\n".join(ln for ln in pretty.split("\n") if ln.strip())

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