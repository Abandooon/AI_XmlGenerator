"""core/round2_generator.py - 修复版Round 2生成器

修复了参数调用不匹配问题和查询字段问题
专注于结构化输出，确保Schema生成流程正确
"""
import json
import time
from datetime import datetime
from pathlib import Path
import uuid as uuid_module
from typing import Dict, List, Any, Optional, Tuple
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
from copy import deepcopy
from ..config import CONFIG
from ..llm.openai_client import OpenAIClient as GeminiClient
# from ..llm.gemini_client import GeminiClient
from ..llm.prompt_templates import template_manager
from ..knowledge.dynamic_query_engine import query_engine
from ..knowledge.constraint_engine import constraint_engine
from ..standard_types.standard_types import standard_type_manager # 新增：导入标准类型管理器
from ..utils.serializers import ArchitectureDesign, generate_uuid
from ..utils.exceptions import ValidationError


class Round2Generator:
    """Round 2详细生成器 - 修复版"""

    def __init__(self):
        """初始化Round 2生成器"""
        self.gemini_client = GeminiClient()
        self.query_engine = query_engine
        self.constraint_engine = constraint_engine
        self.standard_type_manager = standard_type_manager  # 新增：标准类型管理器

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
        component_plans_map = {comp['name']: comp for comp in (architecture_design.component_plan or [])}
        interface_plans = architecture_design.interface_plan or []


        # 1) 准备接口 Schema（用于接口实例的强校验）
        interface_schema = self.query_engine.generate_multi_interface_schema(interface_plans)

        # ↓↓↓ 新增：提早准备标准类型，给接口 prompt 使用
        standard_types = self._prepare_standard_types()

        # 2) 先生成接口实例（独立于组件，严格按接口 Schema）
        merged_json: Dict[str, Any] = {}
        token_stats = {"input": 0, "output": 0, "total": 0}

        if interface_plans:
            try:
                interfaces_prompt = template_manager.get_round2_prompt_interfaces(
                    interface_plans=interface_plans,
                    interface_schema=interface_schema,
                    architecture_design=architecture_design.__dict__,
                    memory_context=memory_context or "",
                    standard_types=standard_types
                )
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

        # 3) 查询全局约束集合（随后按组件过滤）
        constraints_all = self._query_comprehensive_constraints(ordered_component_plans, interface_plans)
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
            self._save_component_schema_to_file(comp_name, comp_schema)  # 保存原生Schema

            # 4.2 (新) 将已知的路径注入当前组件的Schema，生成增强版Schema
            enhanced_schema = self._inject_paths_into_schema(comp_schema, known_instance_paths)
            if CONFIG.debug_mode and known_instance_paths:
                # 可以选择性保存增强后的Schema用于调试
                self._save_component_schema_to_file(f"{comp_name}_enhanced", enhanced_schema)

            # 4.2 过滤与该组件相关的约束
            constraints = self._filter_constraints_for_component(comp, constraints_all)
            r1_component_design = comp

            # 4.3 单组件 Prompt（接口仅作为上下文参考；组件输出仍严格按组件 Schema）
            prompt = template_manager.get_round2_prompt_single(
                comp_plan=comp,
                interface_plans=interface_plans,
                constraints=constraints,
                component_schema=enhanced_schema,
                interface_index=iface_index_for_prompt,
                r1_component_design=r1_component_design,
                memory_context=memory_context or "",
                architecture_design=architecture_design.__dict__,
                # ****** 新增参数: 传递已知路径 ******
                known_paths=known_instance_paths
            )
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

            # 4.5 合并当前组件结果（顶层只会有一个键 = comp_name）
            if isinstance(resp, dict):
                # --- 恢复折叠的容器标签（就地处理，不改变 LLM 输出的其它字段） ---
                try:
                    if len(resp) == 1:
                        comp_type = next(iter(resp.keys()))
                        root = resp.get(comp_type) or {}
                        if isinstance(root, dict) and "SWC-INTERNAL-BEHAVIOR" in root:
                            sib = root.get("SWC-INTERNAL-BEHAVIOR") or {}
                            if isinstance(sib, dict):
                                # A) 先恢复 RUNNABLES：若有 RUNNABLE-ENTITY 且没有 RUNNABLES，就包一层
                                if "RUNNABLE-ENTITY" in sib and "RUNNABLES" not in sib:
                                    sib["RUNNABLES"] = {"RUNNABLE-ENTITY": sib.pop("RUNNABLE-ENTITY")}
                                # B) 再恢复 INTERNAL-BEHAVIORS：若不存在则包一层
                                if "INTERNAL-BEHAVIORS" not in root:
                                    root["INTERNAL-BEHAVIORS"] = {"SWC-INTERNAL-BEHAVIOR": sib}
                                    # 移除扁平时暴露出来的 SWC-INTERNAL-BEHAVIOR
                                    root.pop("SWC-INTERNAL-BEHAVIOR", None)
                            resp[comp_type] = root
                except Exception:
                    # 出错时忽略恢复，继续走原逻辑
                    pass

                merged_json.update(resp)

        # 5) 转为 ARXML（新逻辑：逐条输出，不合并）
        component_xml_map, interface_xml_map = self._convert_each_to_arxml(merged_json)

        # 6) 统计
        generation_time = time.time() - start_time
        stats = {
            "input_tokens": token_stats["input"],
            "output_tokens": token_stats["output"],
            "total_tokens": token_stats["total"],
            "generation_time": generation_time
        }
        return {
            "components": component_xml_map,  # Dict[str, str]  ->  {组件名: 组件XML文本}
            "interfaces": interface_xml_map  # Dict[str, str]  ->  {接口名: 接口XML文本}
        }, stats

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

    # ****** 泛化后的辅助方法: 提取所有带SHORT-NAME的实例路径 ******
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
                        child_path = f"{parent_path}/{short_name}"
                        child_type = key
                        paths.setdefault(child_type, []).append(child_path)
                        recurse_children(value, child_path)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            short_name = item.get("SHORT-NAME")
                            if short_name:
                                child_path = f"{parent_path}/{short_name}"
                                child_type = key
                                paths.setdefault(child_type, []).append(child_path)
                                recurse_children(item, child_path)
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
    def _inject_paths_into_schema(self, schema: Dict[str, Any], known_paths: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        【核心逻辑】遍历Schema，找到*-REF字段，并根据其@DEST属性的约束，
        从known_paths中筛选出类型匹配的路径，注入为#text字段的enum。
        """
        if not known_paths:
            return schema
        schema_copy = deepcopy(schema)
        def recurse(node):
            if not isinstance(node, dict):
                return
            # 定位到引用对象的Schema定义 (特征: 包含@DEST和#text)
            props = node.get("properties", {})
            if node.get("type") == "object" and "@DEST" in props and "#text" in props:
                # 1. 读取@DEST允许的类型列表
                dest_prop_schema = props["@DEST"]
                # @DEST允许的类型通常在其enum字段中定义
                allowed_dest_types = dest_prop_schema.get("enum", [])
                # 如果没有enum定义，我们无法进行安全注入，直接返回
                if not allowed_dest_types:
                    return
                # 2. 根据@DEST允许的类型，从全局路径池(known_paths)中筛选
                valid_paths_for_this_ref = []
                for dest_type in allowed_dest_types:
                    # 如果我们已经提取到了这种类型的实例路径
                    if dest_type in known_paths:
                        # 就将这些路径加入到此引用的有效路径列表中
                        valid_paths_for_this_ref.extend(known_paths[dest_type])
                # 3. 如果找到了匹配的路径，则注入到#text字段的enum中
                if valid_paths_for_this_ref:
                    text_prop_schema = props["#text"]
                    # 使用set去重并排序，然后注入enum约束
                    text_prop_schema["enum"] = sorted(list(set(valid_paths_for_this_ref)))
                    # 还可以加上一个示例，帮助LLM理解
                    text_prop_schema["examples"] = [valid_paths_for_this_ref[0]]
            # 递归遍历Schema的所有子节点
            for key, value in node.items():
                if isinstance(value, dict):
                    recurse(value)
                elif isinstance(value, list):
                    for item in value:
                        recurse(item)
        recurse(schema_copy)
        return schema_copy

    # ****** 新增辅助方法: 构建包含深层实例的详细接口索引 ******
    def _build_detailed_interface_index(self, normalized_ifaces: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        【修正版】遍历规范化后的接口实例，递归提取所有带SHORT-NAME的子元素，
        构建一个详细的、可供引用的实例索引。
        """
        if not normalized_ifaces:
            return []
        detailed_index = []
        def recurse_children(parent_node: Dict[str, Any], parent_path: str):
            """
            【新逻辑】递归函数，只处理 parent_node 的子节点。
            """
            # 遍历父节点的所有子元素（由key和value代表）
            for key, value in parent_node.items():
                # 跳过非结构化的元数据
                if key in ["SHORT-NAME", "_type"]:
                    continue
                # 处理作为字典的单个子元素
                if isinstance(value, dict):
                    short_name = value.get("SHORT-NAME")
                    if short_name:
                        # 子元素的路径 = 父路径 / 子元素的名字
                        child_path = f"{parent_path}/{short_name}"
                        # 子元素的类型 = 它在父节点中的key
                        child_type = key
                        detailed_index.append({
                            "name": short_name,
                            "type": child_type,
                            "path": child_path
                        })
                        # 继续向下递归，处理这个子元素的子节点
                        recurse_children(value, child_path)
                # 处理作为列表的多个子元素
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            short_name = item.get("SHORT-NAME")
                            if short_name:
                                child_path = f"{parent_path}/{short_name}"
                                # 列表中所有元素的类型都由列表的key决定
                                child_type = key
                                detailed_index.append({
                                    "name": short_name,
                                    "type": child_type,
                                    "path": child_path
                                })
                                recurse_children(item, child_path)
        # 从每个顶层接口开始遍历
        for name, data in normalized_ifaces.items():
            interface_type = data.get("_type")
            interface_path = f"/Interfaces/{name}"
            # 1. 先正确添加顶层接口自身
            detailed_index.append({
                "name": name,
                "type": interface_type,
                "path": interface_path
            })
            # 2. 然后调用递归函数来处理它的【子节点】
            recurse_children(data, interface_path)
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

    def _filter_constraints_for_component(self, comp_plan: Dict[str, Any], constraints: List[str]) -> List[str]:
        """按组件特征（端口/内部行为/事件）过滤约束，减少 LLM 负担。"""
        ed = comp_plan.get("element_design", {}) or {}
        need_ports = bool(ed.get("ports", {}).get("needed"))
        need_ib = bool(ed.get("internal_behaviors", {}).get("needed"))
        event_types = set()
        for e in ed.get("internal_behaviors", {}).get("events", []) or []:
            if isinstance(e, dict) and e.get("type"):
                event_types.add(e["type"])

        filtered = []
        for c in constraints or []:
            cs = c or ""
            # 朴素启发：只保留与需要的部分相关的约束
            if ("端口" in cs or "PORT" in cs) and not need_ports:
                continue
            if ("RUNNABLE" in cs or "事件" in cs or "EVENT" in cs or "INTERNAL-BEHAVIOR" in cs) and not need_ib:
                continue
            # 如果指向特定事件类型，但该组件未声明此事件，则跳过
            if any(et in cs for et in ["TIMING-EVENT", "DATA-RECEIVED-EVENT", "OPERATION-INVOKED-EVENT"]):
                if not any(et in cs for et in event_types):
                    continue
            filtered.append(c)
        # 去重
        return sorted(set(filtered))

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

    def _query_comprehensive_constraints(
            self,
            component_plans: List[Dict[str, Any]],
            interface_plans: List[Dict[str, Any]]
    ) -> List[str]:
        """查询完整的约束规则 - 支持配置控制"""

        constraints = []

        # 检查约束引擎是否启用
        if hasattr(CONFIG, 'constraint_engine') and not CONFIG.constraint_engine.enabled:
            # 约束引擎被禁用，只返回最基础的约束
            if CONFIG.debug_mode:
                print("[DEBUG] 约束引擎已禁用，使用最小约束集")

            return [
                "所有UUID必须全局唯一",
                "SHORT-NAME必须符合NCName规范",
                "引用路径必须正确且一致"
            ]

        # 获取约束配置
        constraint_config = getattr(CONFIG, 'constraint_engine', None)
        max_constraints = constraint_config.max_constraints_per_type if constraint_config else 3
        exclude_standard = constraint_config.exclude_standard_constraints if constraint_config else False

        # 约束引擎启用时的逻辑
        try:
            # 组件类型约束
            component_types = set(comp.get("type", "") for comp in component_plans)
            for comp_type in component_types:
                if comp_type:
                    type_constraints = self.query_engine.query_constraints_for_elements([comp_type])
                    # 限制约束数量
                    constraints.extend(type_constraints[:max_constraints])

            # 接口类型约束
            interface_types = set(intf.get("type", "") for intf in interface_plans)
            for intf_type in interface_types:
                if intf_type:
                    intf_constraints = self.query_engine.query_constraints_for_elements([intf_type])
                    # 限制约束数量
                    constraints.extend(intf_constraints[:max_constraints])

        except Exception as e:
            if CONFIG.debug_mode:
                print(f"[DEBUG] 约束查询失败，使用基础约束: {e}")

        # 通用AUTOSAR约束（根据配置决定是否添加）
        if not exclude_standard:
            general_constraints = [
                "所有UUID必须全局唯一",
                "SHORT-NAME必须符合NCName规范",
                "端口名称在组件内必须唯一",
                "事件必须正确引用Runnable",
                "接口引用必须使用完整路径",
                "接口数据元素必须引用IMPLEMENTATION-DATA-TYPE，不能引用SW-BASE-TYPE",
                "类型引用格式：/AUTOSAR_Platform/ImplementationDataTypes/类型名"
            ]
            constraints.extend(general_constraints)

        # 去重
        constraints = list(set(constraints))

        if CONFIG.debug_mode:
            print(f"[DEBUG] 查询到{len(constraints)}条约束规则")

        return constraints

    def _add_component_to_xml(self, parent: Element, comp_name: str, comp_data: Dict[str, Any]):
        """添加组件到XML"""

        comp_type = comp_data.get("_type", "APPLICATION-SW-COMPONENT-TYPE")
        comp_element = SubElement(parent, comp_type)

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

        # 组件：跳过内部键（如 _interfaces）
        for k, v in (merged_json or {}).items():
            if not isinstance(v, dict) or k.startswith("_"):
                continue
            name = _short_name(v, k)
            component_xml_map[name] = self._convert_single_component_to_arxml(name, v)

        # 接口：来自 _interfaces
        for k, v in (merged_json or {}).get("_interfaces", {}).items():
            if not isinstance(v, dict):
                continue
            name = _short_name(v, k)
            interface_xml_map[name] = self._convert_single_interface_to_arxml(name, v)

        return component_xml_map, interface_xml_map


# 全局Round2生成器实例
round2_generator = Round2Generator()