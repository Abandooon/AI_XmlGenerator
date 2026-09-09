#!/usr/bin/env python3
# cloud_vllm_service.py - 修复版本：解决FixedAutosarXMLBuilder和其他错误
import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

import aiohttp
import nest_asyncio
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict

from gad_enhanced_fsm_strategy import GADEnhancedFSMStrategy

nest_asyncio.apply()


# 数据模型定义
class ConstraintInfo(BaseModel):
    """约束信息模型 - 支持引用和传统模式"""
    model_config = ConfigDict(protected_namespaces=())

    # 新增：引用模式（优先使用）
    fsm_ref: Optional[str] = None  # "autosar" - 引用预加载的FSM
    gbnf_ref: Optional[str] = None  # "autosar" - 引用预加载的GBNF

    # 传统模式（兼容性保留）
    fsm_enabled: bool = False
    current_state: Optional[str] = None
    allowed_tokens: Optional[List[str]] = None
    gbnf_enabled: bool = False
    grammar_rules: Optional[str] = None

    # 其他字段
    domain_constraints: Dict[str, Any] = {}
    constraint_version: Optional[str] = None
    constraint_source: Optional[str] = None


class EnhancedGenerationRequest(BaseModel):
    """增强生成请求模型"""
    model_config = ConfigDict(protected_namespaces=())

    request_id: str
    timestamp: Optional[float] = None
    prompt: str
    temperature: float = 0.3
    max_tokens: int = 1024
    top_p: float = 0.9
    frequency_penalty: float = 0.1
    presence_penalty: float = 0.1
    constraint_info: ConstraintInfo
    autosar_context: Dict[str, Any] = {}
    client_version: Optional[str] = None
    client_id: Optional[str] = None


class CloudGenerationResponse(BaseModel):
    """云端生成响应模型"""
    model_config = ConfigDict(protected_namespaces=())

    request_id: str
    success: bool
    timestamp: Optional[float] = None
    generated_xml: Optional[str] = None
    raw_output: Optional[str] = None
    constraints_applied: Dict[str, bool] = {}
    constraint_violations: List[str] = []
    generation_time: float = 0.0
    model_info: Dict[str, Any] = {}
    error_message: Optional[str] = None
    error_details: Dict[str, Any] = {}

# GBNF约束引擎
class GBNFConstraintEngine:
    """GBNF约束引擎 - 修复换行符处理"""

    def __init__(self, gbnf_grammar: str):
        # 🔥 在初始化时就修复换行符
        self.grammar = self._fix_newlines(gbnf_grammar)
        self.is_valid = self._validate_grammar()

    def _fix_newlines(self, grammar: str) -> str:
        """修复换行符问题"""
        if not grammar:
            return grammar

        # 替换字面的换行符为真正的换行符
        fixed = grammar.replace('\\n', '\n')
        fixed = fixed.replace('\\r', '\r')
        fixed = fixed.replace('\\t', '\t')

        return fixed

    def _validate_grammar(self) -> bool:
        """验证GBNF语法有效性 - 增强版本"""
        try:
            if not self.grammar or len(self.grammar.strip()) < 10:
                print("⚠️ GBNF grammar too short or empty")
                return False

            # 检查是否包含基本的规则定义
            if "?start:" not in self.grammar and "start:" not in self.grammar:
                print("⚠️ GBNF grammar missing start rule")
                return False

            # 检查换行符是否正确
            if '\\n' in self.grammar:
                print("⚠️ GBNF grammar contains literal \\n (should be actual newlines)")
                return False

            # 检查基本语法结构
            lines = self.grammar.strip().split('\n')
            rule_count = sum(1 for line in lines if ':' in line and (
                        '?' in line or line.strip().startswith(('?', line.strip().split(':')[0]))))

            if rule_count < 1:
                print(f"⚠️ GBNF grammar has insufficient rules: {rule_count}")
                return False

            print(f"✅ GBNF grammar validation passed: {rule_count} rules, {len(lines)} lines")
            return True

        except Exception as e:
            print(f"❌ GBNF grammar validation failed: {e}")
            return False

# 🔥 策略1：GBNF优先约束引擎 - 使用原始GBNF文件
class GBNFPriorityStrategy:
    """GBNF优先约束策略 - 使用原始GBNF语法文件"""

    def __init__(self, gbnf_engine):
        self.gbnf_engine = gbnf_engine

    async def generate(self, vllm_endpoint: str, request: EnhancedGenerationRequest) -> tuple[str, dict]:
        """GBNF优先生成策略 - 修复换行符格式"""
        print(f"🎯 Using GBNF Priority Strategy - Fixed Format")

        vllm_request = {
            # "model": "/model/HuggingFace/deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
            "model": "/model/HuggingFace/deepseek-ai/DeepSeek-R1-Distill-Qwen-14B",
            "prompt": request.prompt,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "frequency_penalty": request.frequency_penalty,
            "presence_penalty": request.presence_penalty,
            "stream": False,
            "stop": ["</APPLICATION-SW-COMPONENT-TYPE>"]
        }

        constraints_applied = {"gbnf": False, "fsm": False, "strategy": "gbnf_priority"}

        # 🔥 修复：确保GBNF语法格式正确
        if self.gbnf_engine and self.gbnf_engine.is_valid:
            # 获取语法并确保换行符正确
            grammar = self.gbnf_engine.grammar

            # 再次确保没有字面的换行符
            grammar = grammar.replace('\\n', '\n')
            grammar = grammar.replace('\\r', '\r')

            vllm_request["guided_grammar"] = grammar
            constraints_applied["gbnf"] = True

            print(f"✅ Applied fixed GBNF constraint: {len(grammar)} chars")
            print(f"📋 Grammar preview (repr): {repr(grammar[:100])}...")
            print(f"📋 Grammar preview (visual):")
            for i, line in enumerate(grammar.split('\n')[:5]):
                print(f"   {i + 1}: {line}")
        else:
            print("⚠️ No valid GBNF engine available, using fallback")
            # 使用简单的fallback语法
            fallback_grammar = '''?start: autosar_component
    ?autosar_component: "<APPLICATION-SW-COMPONENT-TYPE>" component_content "</APPLICATION-SW-COMPONENT-TYPE>"
    ?component_content: short_name ports behaviors
    ?short_name: "<SHORT-NAME>" /[A-Za-z0-9_]+/ "</SHORT-NAME>"
    ?ports: "<PORTS>" port* "</PORTS>"
    ?port: "<P-PORT-PROTOTYPE>" port_content "</P-PORT-PROTOTYPE>" | "<R-PORT-PROTOTYPE>" port_content "</R-PORT-PROTOTYPE>"
    ?port_content: short_name
    ?behaviors: "<INTERNAL-BEHAVIORS>" behavior* "</INTERNAL-BEHAVIORS>"
    ?behavior: "<SWC-INTERNAL-BEHAVIOR>" behavior_content "</SWC-INTERNAL-BEHAVIOR>"
    ?behavior_content: short_name'''

            vllm_request["guided_grammar"] = fallback_grammar
            constraints_applied["gbnf"] = True
            constraints_applied["fallback_used"] = True
            print(f"✅ Applied fallback GBNF grammar")

        # 🔥 单次请求到vLLM
        async with aiohttp.ClientSession() as session:
            try:
                print(f"🚀 Sending request to vLLM...")
                async with session.post(
                        f"{vllm_endpoint}/v1/completions",
                        json=vllm_request,
                        timeout=aiohttp.ClientTimeout(total=10000)
                ) as resp:
                    if resp.status == 200:
                        response = await resp.json()
                        raw_output = response["choices"][0]["text"]
                        print(f"✅ GBNF generation successful: {len(raw_output)} chars")
                        return raw_output, constraints_applied
                    else:
                        error_text = await resp.text()
                        print(f"❌ GBNF generation failed: {resp.status}")
                        print(f"❌ Error details: {error_text}")
                        raise Exception(f"vLLM error: {error_text}")
            except Exception as e:
                print(f"❌ Request failed: {e}")
                raise

# FSM约束引擎
class FSMConstraintEngine:
    """FSM约束引擎 - 修复版本"""

    def __init__(self, fsm_data: Dict):
        self.fsm_data = fsm_data
        self.transitions = fsm_data.get("edges", {})
        self.accepting_states = set(fsm_data.get("accept", []))
        self.current_state = ""
        self.token_history = []

        print(f"🔧 FSM Engine initialized: {len(self.transitions)} states")

        # 🔥 调试信息：显示部分状态
        sample_states = list(self.transitions.keys())[:5]
        print(f"📋 Sample states: {sample_states}")

    def get_allowed_tokens(self, current_path: List[str] = None) -> List[str]:
        """根据当前状态获取允许的下一个token - 修复版本"""
        if current_path is None:
            current_path = self.token_history

        # 🔥 修复1：状态构建逻辑
        if not current_path:
            current_state = ""
        else:
            # 确保使用正确的状态格式：空格分隔，不是连字符
            current_state = " ".join(current_path)

        print(f"🎯 FSM查询状态: '{current_state}'")

        # 🔥 修复2：精确匹配
        if current_state in self.transitions:
            allowed = list(self.transitions[current_state].keys())
            print(f"✅ 精确匹配成功: {len(allowed)} tokens")
            print(f"📝 允许的tokens: {allowed[:10]}...")  # 只显示前10个
            return allowed

        # 🔥 修复3：改进的模糊匹配
        allowed = self._fuzzy_match_state(current_state)
        if allowed:
            print(f"🔍 模糊匹配成功: {len(allowed)} tokens")
            return allowed

        # 🔥 修复4：回退策略 - 逐步缩短状态
        if current_path:
            for i in range(len(current_path) - 1, 0, -1):
                shorter_state = " ".join(current_path[:i])
                if shorter_state in self.transitions:
                    allowed = list(self.transitions[shorter_state].keys())
                    print(f"🔄 回退匹配成功: '{shorter_state}' -> {len(allowed)} tokens")
                    return allowed

        print(f"❌ 状态匹配失败: '{current_state}'")
        print(f"📊 状态统计:")
        print(f"   总状态数: {len(self.transitions)}")
        print(f"   当前路径长度: {len(current_path)}")

        # 🔥 调试：显示相似状态
        self._debug_similar_states(current_state)

        return []

    def _fuzzy_match_state(self, target_state: str) -> List[str]:
        """改进的模糊匹配算法"""
        if not target_state:
            return list(self.transitions.get("", {}).keys())

        target_tokens = target_state.split()

        # 策略1：寻找包含所有目标token的状态
        for state in self.transitions.keys():
            if not state:
                continue
            state_tokens = state.split()
            if len(state_tokens) >= len(target_tokens):
                # 检查是否所有目标token都在状态中（顺序可能不同）
                if all(token in state_tokens for token in target_tokens):
                    return list(self.transitions[state].keys())

        # 策略2：寻找前缀匹配的状态
        for state in self.transitions.keys():
            if state.startswith(target_state):
                return list(self.transitions[state].keys())

        # 策略3：寻找部分匹配的状态
        target_suffix = target_tokens[-1] if target_tokens else ""
        for state in self.transitions.keys():
            if target_suffix and state.endswith(target_suffix):
                return list(self.transitions[state].keys())

        return []

    def _debug_similar_states(self, target_state: str, max_show: int = 5):
        """调试函数：显示相似的状态"""
        if not target_state:
            return

        target_tokens = set(target_state.split())
        similar_states = []

        for state in list(self.transitions.keys())[:100]:  # 只检查前100个状态
            if not state:
                continue
            state_tokens = set(state.split())

            # 计算交集比例
            intersection = target_tokens & state_tokens
            if intersection:
                similarity = len(intersection) / len(target_tokens | state_tokens)
                similar_states.append((state, similarity))

        # 按相似度排序并显示
        similar_states.sort(key=lambda x: x[1], reverse=True)
        if similar_states:
            print(f"🔍 最相似的状态:")
            for i, (state, sim) in enumerate(similar_states[:max_show]):
                print(f"   {i + 1}. '{state}' (相似度: {sim:.2f})")

    def reset(self):
        """重置状态机"""
        self.current_state = ""
        self.token_history = []
        print("🔄 FSM状态机已重置")

# 🔥 修复版本的 FixedAutosarXMLBuilder
class FixedAutosarXMLBuilder:
    """修复的AUTOSAR XML构建器 - 添加缺失属性"""

    def __init__(self):
        self.reset()

        # 🔥 修复1：添加缺失的simple_hierarchy属性
        self.simple_hierarchy = {
            "APPLICATION-SW-COMPONENT-TYPE": ["SHORT-NAME", "ADMIN-DATA", "PORTS", "INTERNAL-BEHAVIORS"],
            "ADMIN-DATA": ["SDGS"],
            "SDGS": ["SDG"],
            "SDG": ["SD"],
            "PORTS": ["P-PORT-PROTOTYPE", "R-PORT-PROTOTYPE"],
            "P-PORT-PROTOTYPE": ["SHORT-NAME", "PROVIDED-INTERFACE-TREF"],
            "R-PORT-PROTOTYPE": ["SHORT-NAME", "REQUIRED-COM-SPECS", "REQUIRED-INTERFACE-TREF"],
            "REQUIRED-COM-SPECS": ["NONQUEUED-RECEIVER-COM-SPEC"],
            "NONQUEUED-RECEIVER-COM-SPEC": ["DATA-ELEMENT-REF", "ALIVE-TIMEOUT", "HANDLE-TIMEOUT-TYPE"],
            "INTERNAL-BEHAVIORS": ["SWC-INTERNAL-BEHAVIOR"],
            "SWC-INTERNAL-BEHAVIOR": ["SHORT-NAME", "EVENTS", "RUNNABLES"],
            "EVENTS": ["TIMING-EVENT"],
            "TIMING-EVENT": ["SHORT-NAME", "START-ON-EVENT-REF", "PERIOD"],
            "RUNNABLES": ["RUNNABLE-ENTITY"],
            "RUNNABLE-ENTITY": ["SHORT-NAME", "SYMBOL", "DATA-RECEIVE-POINT-BY-ARGUMENTS", "DATA-SEND-POINTS"]
        }

        # 🔥 修复2：添加内容元素定义
        self.content_elements = {
            "SHORT-NAME", "SD", "PROVIDED-INTERFACE-TREF", "REQUIRED-INTERFACE-TREF",
            "PERIOD", "SYMBOL", "START-ON-EVENT-REF", "DATA-ELEMENT-REF",
            "ALIVE-TIMEOUT", "HANDLE-TIMEOUT-TYPE"
        }

    def reset(self):
        """重置构建器状态"""
        self.open_tags = []
        self.uuid_counter = 0
        self.element_count = 0

    def build_fixed_xml_fragment(self, token: str, current_path: list, step: int) -> str:
        """构建修复的XML片段"""
        fragment = ""

        # 🔥 修复: 智能标签关闭
        if self._needs_closing(token, current_path):
            fragment += self._close_tags_intelligently(token)

        # 🔥 修复: 正确的标签构建
        if token in self.content_elements:
            # 内容元素：开始标签，等待内容
            indent = "  " * len(self.open_tags)
            fragment += f"{indent}<{token}>"
            self.open_tags.append(token)
        else:
            # 容器元素：完整开始标签
            fragment += self._build_container_tag(token, step)
            self.open_tags.append(token)
            self.element_count += 1

        return fragment

    def _needs_closing(self, new_token: str, current_path: list) -> bool:
        """判断是否需要关闭标签"""
        if not self.open_tags:
            return False

        last_open = self.open_tags[-1]

        # 内容元素总是需要关闭
        if last_open in self.content_elements:
            return True

        # 容器元素：检查是否可以包含新token
        valid_children = self.simple_hierarchy.get(last_open, [])
        return new_token not in valid_children

    def _close_tags_intelligently(self, new_token: str) -> str:
        """智能关闭标签"""
        closing_fragment = ""

        while self.open_tags:
            last_tag = self.open_tags[-1]

            # 内容元素：直接关闭
            if last_tag in self.content_elements:
                self.open_tags.pop()
                closing_fragment += f"</{last_tag}>\n"
                continue

            # 容器元素：检查是否可以容纳新token
            valid_children = self.simple_hierarchy.get(last_tag, [])
            if new_token in valid_children:
                break

            # 关闭容器元素
            self.open_tags.pop()
            indent = "  " * len(self.open_tags)
            closing_fragment += f"{indent}</{last_tag}>\n"

        return closing_fragment

    def _build_container_tag(self, token: str, step: int) -> str:
        """构建容器标签"""
        indent = "  " * len(self.open_tags)

        # 需要UUID的元素
        uuid_elements = ["P-PORT-PROTOTYPE", "R-PORT-PROTOTYPE", "TIMING-EVENT", "RUNNABLE-ENTITY"]

        if token in uuid_elements:
            self.uuid_counter += 1
            uuid_val = self._generate_simple_uuid(step)
            return f'{indent}<{token} UUID="{uuid_val}">\n'
        else:
            return f"{indent}<{token}>\n"

    def _generate_simple_uuid(self, step: int) -> str:
        """生成简单的UUID"""
        return f"12345678-1234-5678-9abc-def{step:09d}"

    def finalize_fixed_xml(self, xml_content: str) -> str:
        """完成XML结构"""
        final_content = xml_content

        # 关闭所有开放的标签
        while self.open_tags:
            tag = self.open_tags.pop()

            if tag in self.content_elements:
                final_content += f"</{tag}>\n"
            else:
                indent = "  " * len(self.open_tags)
                final_content += f"{indent}</{tag}>\n"

        return final_content.strip()

    def get_element_count(self) -> int:
        """获取已构建的元素数量"""
        return self.element_count


class ImprovedXMLBuilder:
    """改进的XML构建器"""

    def __init__(self):
        self.reset()

    def reset(self):
        self.generated_content = ""
        self.current_depth = 0

    def add_content(self, content: str):
        """添加内容到构建器"""
        self.generated_content += content

    def get_content(self) -> str:
        """获取当前内容"""
        return self.generated_content


class EnhancedFSMStrategy:
    """基于FSM文件的增强迭代策略 - 修复版本 v5.0"""

    def __init__(self, fsm_engine, prompt_config=None):
        self.fsm_engine = fsm_engine
        self.max_iterations = 100  # 增加迭代次数
        self.max_tokens_per_step = 600
        self.temperature = 0.3  # 降低温度，更确定性
        self.top_p = 0.9
        self.choice_range = 30

        self.content_guidance = self._load_content_guidance()
        self.element_hierarchy = self._build_element_hierarchy_from_fsm()
        self.content_elements = self._extract_content_elements_from_fsm()
        self.priority_strategy = self._extract_priority_from_prompt(prompt_config)

        # 🔥 修复：确保标签名称一致性
        self.tag_mapping = self._extract_tag_mapping_from_prompt(prompt_config)

        self.sibling_elements = {
            "root_level": {"SHORT-NAME", "ADMIN-DATA", "PORTS", "INTERNAL-BEHAVIORS"},
            "port_types": {"P-PORT-PROTOTYPE", "R-PORT-PROTOTYPE"},
            "behavior_sections": {"EVENTS", "RUNNABLES"},
            "data_points": {"DATA-RECEIVE-POINT-BY-ARGUMENTS", "DATA-SEND-POINTS"},
            "admin_structure": {"SDGS", "SDG", "SD"}
        }

        # 🔥 新增：必需的最小结构
        self.required_structure = {
            "APPLICATION-SW-COMPONENT-TYPE": ["SHORT-NAME", "PORTS", "INTERNAL-BEHAVIORS"],
            "PORTS": ["P-PORT-PROTOTYPE", "R-PORT-PROTOTYPE"],  # 至少各一个
            "INTERNAL-BEHAVIORS": ["SWC-INTERNAL-BEHAVIOR"],
            "SWC-INTERNAL-BEHAVIOR": ["SHORT-NAME", "EVENTS", "RUNNABLES"]
        }

    def _extract_tag_mapping_from_prompt(self, prompt_config):
        """从提示词中提取标签映射关系"""
        if not prompt_config:
            return {}

        mapping = {}
        example_xml = self._extract_example_xml_from_prompt(
            prompt_config.get('component_level', '')
        )

        if example_xml:
            # 检测示例中使用的标签格式
            if "<APP-SW-COMPONENT-TYPE>" in example_xml:
                mapping["APPLICATION-SW-COMPONENT-TYPE"] = "APP-SW-COMPONENT-TYPE"
            if "<PORT>" in example_xml:
                mapping["PORTS"] = "PORT"
            if "<P_PORT-PROTOTYPE" in example_xml:
                mapping["P-PORT-PROTOTYPE"] = "P_PORT-PROTOTYPE"
                mapping["R-PORT-PROTOTYPE"] = "R_PORT-PROTOTYPE"

        return mapping

    async def generate(self, vllm_endpoint: str, request: EnhancedGenerationRequest) -> tuple[str, dict]:
        """修复版本的生成方法 - 改进vLLM交互"""
        print(f"🎯 Using Enhanced FSM Strategy - Fixed v5.0")

        # 初始化状态
        fsm_state = ""
        generation_path = []
        xml_content = ""
        constraints_applied = {"fsm": True, "gbnf": False, "strategy": "enhanced_fsm_fixed_v5"}
        iteration_log = []

        # 跟踪已生成的结构
        generated_structure = {
            "has_component": False,
            "has_name": False,
            "has_ports": False,
            "p_port_count": 0,
            "r_port_count": 0,
            "has_behaviors": False,
            "has_behavior": False,
            "has_events": False,
            "has_runnables": False
        }

        # 重置FSM引擎
        self.fsm_engine.reset()

        # 构建增强的基础提示词
        base_prompt = self._build_enhanced_base_prompt(request.prompt, request.autosar_context)

        for step in range(self.max_iterations):
            print(f"\n--- 步骤 {step + 1}/{self.max_iterations} ---")
            print(f"🎯 FSM状态: '{fsm_state}'")
            print(f"📍 生成路径: {' -> '.join(generation_path) if generation_path else '空'}")
            print(
                f"📊 结构状态: P-PORT={generated_structure['p_port_count']}, R-PORT={generated_structure['r_port_count']}")

            # 获取允许的tokens
            allowed_tokens = self._get_allowed_tokens_for_state(fsm_state)
            if not allowed_tokens:
                print(f"🛑 无可用tokens，结束生成")
                break

            # 🔥 智能过滤：基于当前需要什么
            filtered_tokens = self._smart_filter_tokens(
                allowed_tokens, generation_path, xml_content, generated_structure, step
            )

            if not filtered_tokens:
                print(f"⚠️ 过滤后无可用tokens，结束生成")
                break

            print(f"📝 准备调用vLLM，可选tokens: {len(filtered_tokens)}")
            print(f"   优先选项: {filtered_tokens[:5]}")

            # 🔥 调用vLLM获取下一个token
            try:
                selected_token, vllm_response = await self._call_vllm_with_context(
                    vllm_endpoint,
                    base_prompt,
                    xml_content,
                    generation_path,
                    filtered_tokens,
                    generated_structure,
                    step
                )

                if not selected_token:
                    print(f"❌ vLLM未返回有效token，结束生成")
                    break

                print(f"✅ vLLM选择token: {selected_token}")

            except Exception as e:
                print(f"❌ vLLM调用失败: {e}")
                # 🔥 降级策略：使用本地选择
                selected_token = self._fallback_token_selection(filtered_tokens, generation_path, generated_structure)
                if not selected_token:
                    break
                print(f"⚠️ 使用降级选择: {selected_token}")

            # 处理选择的token
            if selected_token.startswith("_COMPLETE_"):
                # 完成标记：只更新FSM状态
                fsm_state = self._handle_complete_token(fsm_state, selected_token)
                print(f"🔄 完成标记处理，新状态: '{fsm_state}'")
            else:
                # 普通元素：生成XML并更新状态
                xml_fragment, updated_path = self._generate_xml_with_validation(
                    selected_token, generation_path, fsm_state, step, xml_content
                )

                if xml_fragment:
                    xml_content += xml_fragment
                    generation_path = updated_path

                    # 更新生成结构跟踪
                    self._update_generated_structure(selected_token, generated_structure)

                    # 更新FSM状态
                    fsm_state = self._compute_new_fsm_state(fsm_state, selected_token, generation_path)

                    print(f"📝 生成片段: {xml_fragment.strip()[:100]}...")
                    print(f"🔄 新FSM状态: '{fsm_state}'")
                else:
                    print(f"⚠️ 无法生成有效的XML片段")

            # 记录迭代信息
            iteration_log.append({
                "step": step + 1,
                "selected_token": selected_token,
                "fsm_state": fsm_state,
                "path_depth": len(generation_path),
                "xml_length": len(xml_content),
                "structure": generated_structure.copy()
            })

            # 🔥 改进的完成条件
            if self._should_complete_with_validation(generation_path, xml_content, generated_structure, step):
                print(f"🏁 满足完成条件")
                break

        # 🔥 智能完成XML结构
        final_xml = self._smart_finalize_xml(xml_content, generation_path, generated_structure)

        constraints_applied.update({
            "steps": step + 1,
            "final_state": fsm_state,
            "final_path": generation_path,
            "iterations": iteration_log,
            "vllm_calls": step + 1,
            "final_structure": generated_structure
        })

        print(f"\n🏁 生成完成:")
        print(f"   步骤数: {step + 1}")
        print(
            f"   最终结构: P-PORT={generated_structure['p_port_count']}, R-PORT={generated_structure['r_port_count']}")
        print(f"   XML长度: {len(final_xml)} chars")

        return final_xml, constraints_applied

    def _build_enhanced_base_prompt(self, original_prompt: str, context: dict) -> str:
        """构建增强的基础提示词"""
        # 提取示例中的关键模式
        example_patterns = ""
        if context and 'example_xml' in context:
            example_patterns = """
Key patterns from example:
- Each PORT must have SHORT-NAME and interface reference
- R-PORT-PROTOTYPE needs REQUIRED-COM-SPECS with NONQUEUED-RECEIVER-COM-SPEC
- NONQUEUED-RECEIVER-COM-SPEC contains DATA-ELEMENT-REF, ALIVE-TIMEOUT, HANDLE-TIMEOUT-TYPE
- INTERNAL-BEHAVIORS contains SWC-INTERNAL-BEHAVIOR with EVENTS and RUNNABLES
"""

        return f"""{original_prompt}

You are generating AUTOSAR XML structure step by step using FSM constraints.
Each step, you will choose the next XML element to add based on the current context.

Important rules:
1. Generate valid AUTOSAR APPLICATION-SW-COMPONENT-TYPE structure
2. Each component needs: SHORT-NAME, PORTS (with both P-PORT and R-PORT), INTERNAL-BEHAVIORS
3. Follow the hierarchical structure strictly
4. Do not nest elements incorrectly
{example_patterns}

Focus on creating a complete, valid structure."""

    async def _call_vllm_with_context(self, vllm_endpoint: str, base_prompt: str,
                                      current_xml: str, generation_path: list,
                                      allowed_tokens: list, generated_structure: dict,
                                      step: int) -> tuple[str, dict]:
        """改进的vLLM调用，包含更好的上下文"""

        # 构建结构感知的提示词
        context_prompt = self._build_structure_aware_prompt(
            base_prompt, current_xml, generation_path, generated_structure, allowed_tokens
        )

        # 限制token数量
        choice_tokens = allowed_tokens[:self.choice_range]

        # 构建vLLM请求
        vllm_request = {
            "model": "/model/HuggingFace/deepseek-ai/DeepSeek-R1-Distill-Qwen-14B",
            "prompt": context_prompt,
            "max_tokens": 20,  # 减少到20，只需要选择
            "temperature": self.temperature,
            "top_p": self.top_p,
            "stream": False,
            "guided_choice": choice_tokens,
            "guided_decoding_backend": "outlines"
        }

        print(f"🚀 调用vLLM with {len(choice_tokens)} choices")

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                        f"{vllm_endpoint}/v1/completions",
                        json=vllm_request,
                        timeout=aiohttp.ClientTimeout(total=200)
                ) as resp:
                    if resp.status == 200:
                        response = await resp.json()
                        vllm_output = response["choices"][0]["text"].strip()

                        # 提取选择的token
                        selected_token = self._extract_token_from_output(vllm_output, choice_tokens)

                        print(f"📥 vLLM输出: '{vllm_output}'")

                        return selected_token, response
                    else:
                        error_text = await resp.text()
                        raise Exception(f"vLLM error {resp.status}: {error_text}")

            except Exception as e:
                print(f"❌ vLLM调用异常: {e}")
                raise

    def _build_structure_aware_prompt(self, base_prompt: str, current_xml: str,
                                      generation_path: list, generated_structure: dict,
                                      allowed_tokens: list) -> str:
        """构建结构感知的提示词"""

        # 分析当前需要什么
        needs = self._analyze_structure_needs(generated_structure, generation_path)

        # 构建XML预览（限制长度）
        xml_preview = current_xml[-500:] if len(current_xml) > 500 else current_xml
        if not xml_preview:
            xml_preview = "<APPLICATION-SW-COMPONENT-TYPE>"

        prompt = f"""{base_prompt}

Current XML structure:
```xml
{xml_preview}
```

Current position: {' -> '.join(generation_path[-3:]) if generation_path else 'Starting'}
Structure status: {needs}

Available choices: {', '.join(allowed_tokens[:10])}

Select the MOST APPROPRIATE next element to continue building a valid AUTOSAR structure.
Choose the element name that best fits the current context:"""

        return prompt

    def _analyze_structure_needs(self, generated_structure: dict, generation_path: list) -> str:
        """分析当前结构需要什么"""
        needs = []

        if not generated_structure['has_name']:
            needs.append("Component needs SHORT-NAME")

        if not generated_structure['has_ports']:
            needs.append("Component needs PORTS section")
        elif generation_path and "PORTS" in generation_path:
            if generated_structure['p_port_count'] == 0:
                needs.append("Need at least one P-PORT-PROTOTYPE")
            if generated_structure['r_port_count'] == 0:
                needs.append("Need at least one R-PORT-PROTOTYPE")

        if not generated_structure['has_behaviors']:
            needs.append("Component needs INTERNAL-BEHAVIORS")

        return " | ".join(needs) if needs else "Structure building in progress"

    def _smart_filter_tokens(self, allowed_tokens: list, generation_path: list,
                             xml_content: str, generated_structure: dict, step: int) -> list:
        """智能过滤tokens，基于当前需要"""

        # 分离token类型
        real_tokens = [t for t in allowed_tokens if not t.startswith('_COMPLETE_')]
        complete_tokens = [t for t in allowed_tokens if t.startswith('_COMPLETE_')]

        # 🔥 强制生成必需结构
        if generation_path:
            current = generation_path[-1]

            # 在PORTS中，确保生成足够的端口
            if current == "PORTS":
                if generated_structure['p_port_count'] == 0:
                    # 优先P-PORT
                    return self._prioritize_tokens(real_tokens, ["P-PORT-PROTOTYPE"])
                elif generated_structure['r_port_count'] == 0:
                    # 然后R-PORT
                    return self._prioritize_tokens(real_tokens, ["R-PORT-PROTOTYPE"])
                elif generated_structure['p_port_count'] >= 1 and generated_structure['r_port_count'] >= 1:
                    # 有足够端口后考虑完成或继续
                    if "INTERNAL-BEHAVIORS" in real_tokens:
                        return ["INTERNAL-BEHAVIORS"]
                    return complete_tokens if complete_tokens else real_tokens

            # 在组件根级别，确保有所有必需部分
            if current == "APPLICATION-SW-COMPONENT-TYPE":
                if not generated_structure['has_name'] and "SHORT-NAME" in real_tokens:
                    return ["SHORT-NAME"]
                elif not generated_structure['has_ports'] and "PORTS" in real_tokens:
                    return ["PORTS"]
                elif not generated_structure['has_behaviors'] and "INTERNAL-BEHAVIORS" in real_tokens:
                    return ["INTERNAL-BEHAVIORS"]

        # 过滤掉不需要的元素
        filtered = [t for t in real_tokens if t not in self.priority_strategy.get('skip_elements', set())]

        # 根据上下文优先级排序
        return self._sort_by_priority(filtered, generation_path)[:self.choice_range]

    def _prioritize_tokens(self, tokens: list, priorities: list) -> list:
        """将优先的tokens放在前面"""
        priority_tokens = [t for t in tokens if t in priorities]
        other_tokens = [t for t in tokens if t not in priorities]
        return priority_tokens + other_tokens

    def _sort_by_priority(self, tokens: list, generation_path: list) -> list:
        """根据优先级排序tokens"""
        if not generation_path:
            return tokens

        current = generation_path[-1] if generation_path else ""

        # 定义每个上下文的优先级
        context_priority = {
            "APPLICATION-SW-COMPONENT-TYPE": ["SHORT-NAME", "PORTS", "INTERNAL-BEHAVIORS"],
            "PORTS": ["P-PORT-PROTOTYPE", "R-PORT-PROTOTYPE"],
            "P-PORT-PROTOTYPE": ["SHORT-NAME", "PROVIDED-INTERFACE-TREF"],
            "R-PORT-PROTOTYPE": ["SHORT-NAME", "REQUIRED-COM-SPECS", "REQUIRED-INTERFACE-TREF"],
            "REQUIRED-COM-SPECS": ["NONQUEUED-RECEIVER-COM-SPEC"],
            "NONQUEUED-RECEIVER-COM-SPEC": ["DATA-ELEMENT-REF", "ALIVE-TIMEOUT", "HANDLE-TIMEOUT-TYPE"],
            "INTERNAL-BEHAVIORS": ["SWC-INTERNAL-BEHAVIOR"],
            "SWC-INTERNAL-BEHAVIOR": ["SHORT-NAME", "EVENTS", "RUNNABLES"],
            "EVENTS": ["TIMING-EVENT"],
            "RUNNABLES": ["RUNNABLE-ENTITY"]
        }

        priorities = context_priority.get(current, [])

        # 排序
        priority_tokens = [t for t in tokens if t in priorities]
        other_tokens = [t for t in tokens if t not in priorities]

        # 按照定义的优先级顺序排列
        sorted_priority = []
        for p in priorities:
            if p in priority_tokens:
                sorted_priority.append(p)

        return sorted_priority + other_tokens

    def _extract_token_from_output(self, vllm_output: str, allowed_tokens: list) -> str:
        """从vLLM输出中提取token"""
        cleaned = vllm_output.strip().upper()
        cleaned = cleaned.replace('<', '').replace('>', '').replace('/', '')

        # 直接匹配
        if cleaned in allowed_tokens:
            return cleaned

        # 查找最相似的
        for token in allowed_tokens:
            if token in cleaned or cleaned in token:
                return token

        # 分词匹配
        words = cleaned.split()
        for word in words:
            for token in allowed_tokens:
                if word in token or token in word:
                    return token

        # 返回第一个允许的token
        return allowed_tokens[0] if allowed_tokens else None

    def _fallback_token_selection(self, tokens: list, path: list, structure: dict) -> str:
        """降级token选择策略"""
        if not tokens:
            return None

        # 基于当前需要选择
        if path:
            current = path[-1]
            if current == "PORTS" and structure['p_port_count'] == 0:
                for t in tokens:
                    if "P-PORT" in t:
                        return t
            elif current == "PORTS" and structure['r_port_count'] == 0:
                for t in tokens:
                    if "R-PORT" in t:
                        return t

        # 返回第一个非完成标记
        for t in tokens:
            if not t.startswith("_COMPLETE_"):
                return t

        return tokens[0] if tokens else None

    def _generate_xml_with_validation(self, token: str, current_path: list,
                                      fsm_state: str, step: int, current_xml: str) -> tuple[str, list]:
        """生成XML片段并验证"""
        xml_fragment = ""
        new_path = current_path.copy()

        # 确定需要关闭的标签
        tags_to_close = self._determine_tags_to_close(current_path, token, fsm_state)

        # 生成关闭标签
        for tag in reversed(tags_to_close):
            if tag in new_path:
                depth = new_path.index(tag)
                indent = "  " * depth
                xml_fragment += f"{indent}</{tag}>\n"
                new_path.remove(tag)

        # 生成新元素
        indent = "  " * len(new_path)

        if token in self.content_elements:
            # 内容元素
            content = self._generate_smart_content(token, new_path, step, current_xml)
            xml_fragment += f"{indent}<{token}>{content}</{token}>\n"
        else:
            # 容器元素
            if self._element_needs_uuid(token):
                uuid_val = self._generate_uuid(step)
                xml_fragment += f'{indent}<{token} UUID="{uuid_val}">\n'
            else:
                xml_fragment += f"{indent}<{token}>\n"
            new_path.append(token)

        return xml_fragment, new_path

    def _generate_smart_content(self, element: str, current_path: list, step: int, current_xml: str) -> str:
        """生成智能内容，基于示例和上下文"""

        # 基于元素类型生成适当的内容
        if element == "SHORT-NAME":
            return self._generate_context_aware_name(current_path, step)

        elif element == "PROVIDED-INTERFACE-TREF":
            return ' DEST="SENDER-RECEIVER-INTERFACE">/COM_Interface/SR_Interface_Provider'

        elif element == "REQUIRED-INTERFACE-TREF":
            return ' DEST="SENDER-RECEIVER-INTERFACE">/COM_Interface/SR_Interface_Receiver'

        elif element == "DATA-ELEMENT-REF":
            # 从上下文中提取接口名称
            interface_name = "SR_Interface_Data"
            if current_xml:
                # 尝试从最近的R-PORT名称推断
                import re
                rport_match = re.findall(r'<SHORT-NAME>RPort_(\w+)</SHORT-NAME>', current_xml)
                if rport_match:
                    interface_name = f"SR_Interface_{rport_match[-1]}"
            return f' DEST="VARIABLE-DATA-PROTOTYPE">/COM_Interface/{interface_name}/DataElement'

        elif element == "PORT-PROTOTYPE-REF":
            port_type = "R-PORT-PROTOTYPE" if "RECEIVE" in str(current_path) else "P-PORT-PROTOTYPE"
            return f' DEST="{port_type}">/Components/Component/Port_{step:02d}'

        elif element == "TARGET-DATA-PROTOTYPE-REF":
            return ' DEST="VARIABLE-DATA-PROTOTYPE">/COM_Interface/SR_Interface_Data/Element'

        elif element == "START-ON-EVENT-REF":
            return ' DEST="RUNNABLE-ENTITY">/Components/Component/InternalBehavior/Runnable_Main'

        elif element == "PERIOD":
            return "0.01"

        elif element == "ALIVE-TIMEOUT":
            return "0.3"

        elif element == "HANDLE-TIMEOUT-TYPE":
            return "NONE"

        elif element == "SYMBOL":
            return "Runnable_Main_func"

        else:
            return f"Generated_{element}_{step:02d}"

    def _generate_context_aware_name(self, current_path: list, step: int) -> str:
        """基于上下文生成合适的名称"""
        if not current_path:
            return f"Element_{step:02d}"

        parent = current_path[-1] if current_path else ""

        name_map = {
            "APPLICATION-SW-COMPONENT-TYPE": "MyComponent",
            "P-PORT-PROTOTYPE": f"PPort_Provider_{step:02d}",
            "R-PORT-PROTOTYPE": f"RPort_Receiver_{step:02d}",
            "SWC-INTERNAL-BEHAVIOR": "InternalBehavior",
            "TIMING-EVENT": f"TE_10ms",
            "RUNNABLE-ENTITY": f"RE_Main",
            "VARIABLE-ACCESS": f"DataAccess_{step:02d}"
        }

        return name_map.get(parent, f"Element_{step:02d}")

    def _update_generated_structure(self, token: str, structure: dict):
        """更新已生成结构的跟踪"""
        if token == "APPLICATION-SW-COMPONENT-TYPE":
            structure["has_component"] = True
        elif token == "SHORT-NAME":
            structure["has_name"] = True
        elif token == "PORTS":
            structure["has_ports"] = True
        elif token == "P-PORT-PROTOTYPE":
            structure["p_port_count"] += 1
        elif token == "R-PORT-PROTOTYPE":
            structure["r_port_count"] += 1
        elif token == "INTERNAL-BEHAVIORS":
            structure["has_behaviors"] = True
        elif token == "SWC-INTERNAL-BEHAVIOR":
            structure["has_behavior"] = True
        elif token == "EVENTS":
            structure["has_events"] = True
        elif token == "RUNNABLES":
            structure["has_runnables"] = True

    def _should_complete_with_validation(self, path: list, xml: str, structure: dict, step: int) -> bool:
        """改进的完成条件，确保生成完整结构"""

        # 必须有基本组件结构
        if not structure["has_component"] or not structure["has_name"]:
            return False

        # 必须有PORTS且包含至少一个P-PORT和一个R-PORT
        if not structure["has_ports"] or structure["p_port_count"] < 1 or structure["r_port_count"] < 1:
            return False

        # 必须有INTERNAL-BEHAVIORS
        if not structure["has_behaviors"] or not structure["has_behavior"]:
            return False

        # 检查PORTS和INTERNAL-BEHAVIORS是否已关闭
        if "<PORTS>" in xml and "</PORTS>" not in xml:
            return False
        if "<INTERNAL-BEHAVIORS>" in xml and "</INTERNAL-BEHAVIORS>" not in xml:
            return False

        # 如果有EVENTS或RUNNABLES开始标签，确保它们被关闭
        if "<EVENTS>" in xml and "</EVENTS>" not in xml:
            return False
        if "<RUNNABLES>" in xml and "</RUNNABLES>" not in xml:
            return False

        # 步数限制
        if step >= self.max_iterations - 1:
            return True

        # 如果所有主要结构都已完成
        if structure["has_events"] or structure["has_runnables"]:
            return True

        return False

    def _smart_finalize_xml(self, xml_content: str, path: list, structure: dict) -> str:
        """智能完成XML，确保所有必需元素都存在"""

        # 如果缺少必需的结构，添加它们
        if not structure["has_behaviors"] and "</PORTS>" in xml_content:
            # 在PORTS后添加INTERNAL-BEHAVIORS
            insert_pos = xml_content.rfind("</PORTS>") + len("</PORTS>")
            behaviors_xml = """
  <INTERNAL-BEHAVIORS>
    <SWC-INTERNAL-BEHAVIOR>
      <SHORT-NAME>DefaultBehavior</SHORT-NAME>
      <EVENTS>
        <TIMING-EVENT UUID="00000000-0000-0000-0000-000000000001">
          <SHORT-NAME>TE_Default</SHORT-NAME>
          <START-ON-EVENT-REF DEST="RUNNABLE-ENTITY">/Components/Component/DefaultBehavior/RE_Default</START-ON-EVENT-REF>
          <PERIOD>0.01</PERIOD>
        </TIMING-EVENT>
      </EVENTS>
      <RUNNABLES>
        <RUNNABLE-ENTITY UUID="00000000-0000-0000-0000-000000000002">
          <SHORT-NAME>RE_Default</SHORT-NAME>
          <SYMBOL>RE_Default_func</SYMBOL>
        </RUNNABLE-ENTITY>
      </RUNNABLES>
    </SWC-INTERNAL-BEHAVIOR>
  </INTERNAL-BEHAVIORS>"""
            xml_content = xml_content[:insert_pos] + behaviors_xml + xml_content[insert_pos:]

        # 关闭所有开放的标签
        closing_xml = ""
        for i in range(len(path) - 1, -1, -1):
            tag = path[i]
            if tag not in self.content_elements:
                indent = "  " * i
                closing_xml += f"{indent}</{tag}>\n"

        return xml_content + closing_xml

    # 保持其他辅助方法不变...
    def _get_allowed_tokens_for_state(self, fsm_state: str) -> list:
        """获取当前状态允许的tokens"""
        if fsm_state in self.fsm_engine.transitions:
            return list(self.fsm_engine.transitions[fsm_state].keys())
        return []

    def _handle_complete_token(self, fsm_state: str, complete_token: str) -> str:
        """处理完成标记，返回新状态"""
        if fsm_state in self.fsm_engine.transitions:
            transitions = self.fsm_engine.transitions[fsm_state]
            if complete_token in transitions:
                return transitions[complete_token]
        return fsm_state

    def _determine_tags_to_close(self, current_path: list, new_token: str,
                                 fsm_state: str) -> list:
        """确定需要关闭的标签"""
        if not current_path:
            return []

        tags_to_close = []

        # 检查FSM状态
        if fsm_state in self.fsm_engine.transitions:
            allowed = self.fsm_engine.transitions[fsm_state]
            if new_token in allowed:
                return []

        # 查找可以容纳新token的祖先
        for i in range(len(current_path) - 1, -1, -1):
            ancestor_path = current_path[:i]
            ancestor_state = " ".join(ancestor_path) if ancestor_path else ""

            if ancestor_state in self.fsm_engine.transitions:
                allowed = self.fsm_engine.transitions[ancestor_state]
                if new_token in allowed:
                    tags_to_close = current_path[i:]
                    break

        # 基于平级元素关系
        if not tags_to_close and current_path:
            current_element = current_path[-1]
            if self._are_siblings(current_element, new_token):
                tags_to_close = [current_element]

        return tags_to_close

    def _are_siblings(self, elem1: str, elem2: str) -> bool:
        """判断两个元素是否为平级关系"""
        for group_name, group_elements in self.sibling_elements.items():
            if elem1 in group_elements and elem2 in group_elements:
                return True
        return False

    def _compute_new_fsm_state(self, current_state: str, token: str,
                               generation_path: list) -> str:
        """计算新的FSM状态"""
        if current_state in self.fsm_engine.transitions:
            transitions = self.fsm_engine.transitions[current_state]
            if token in transitions:
                return transitions[token]

        state_path = [elem for elem in generation_path if elem not in self.content_elements]
        return " ".join(state_path) if state_path else ""

    def _element_needs_uuid(self, element: str) -> bool:
        """检查元素是否需要UUID"""
        uuid_elements = {'P-PORT-PROTOTYPE', 'R-PORT-PROTOTYPE', 'TIMING-EVENT',
                         'RUNNABLE-ENTITY', 'VARIABLE-ACCESS'}
        return element in uuid_elements

    def _generate_uuid(self, step: int) -> str:
        """生成UUID"""
        import uuid
        return str(uuid.uuid4())

    # 保留原有的其他辅助方法...
    def _extract_priority_from_prompt(self, prompt_config):
        if not prompt_config:
            return self._get_default_priority_strategy()

        component_prompt = prompt_config.get('component_level', '')
        example_xml = self._extract_example_xml_from_prompt(component_prompt)

        if example_xml:
            return self._analyze_xml_priority(example_xml)
        else:
            return self._get_default_priority_strategy()

    def _extract_example_xml_from_prompt(self, prompt_content):
        import re
        # 修改正则表达式以匹配示例中的格式
        xml_pattern = r'<APP[LICATION]*-SW-COMPONENT-TYPE>.*?</APP[LICATION]*-SW-COMPONENT-TYPE>'
        match = re.search(xml_pattern, prompt_content, re.DOTALL)
        if match:
            return match.group(0)
        return None

    def _analyze_xml_priority(self, xml_content):
        import re

        lines = xml_content.split('\n')
        structure = []
        element_counts = {}

        for line in lines:
            trimmed = line.strip()
            if trimmed.startswith('<') and not trimmed.startswith('</') and not '<!--' in trimmed:
                # 修改正则以匹配下划线
                match = re.match(r'<([A-Z][A-Z0-9_-]*)', trimmed)
                if match:
                    element = match[1]
                    # 标准化元素名称
                    element = element.replace('_', '-')
                    if element == 'APP-SW-COMPONENT-TYPE':
                        element = 'APPLICATION-SW-COMPONENT-TYPE'
                    elif element == 'PORT':
                        element = 'PORTS'

                    depth = (len(line) - len(line.lstrip())) // 2
                    structure.append({
                        'element': element,
                        'depth': depth,
                        'order': len(structure)
                    })
                    element_counts[element] = element_counts.get(element, 0) + 1

        priority_strategy = {
            'core_structures': [],
            'main_containers': [],
            'detail_elements': [],
            'avoid_elements': [],
            'generation_order': [],
            'skip_elements': set()
        }

        for item in structure:
            if item['depth'] <= 2 and element_counts[item['element']] == 1:
                priority_strategy['core_structures'].append(item['element'])

        main_containers = [item['element'] for item in structure if item['depth'] <= 3]
        priority_strategy['main_containers'] = list(dict.fromkeys(main_containers))

        detail_elements = [item['element'] for item in structure if item['depth'] > 4]
        priority_strategy['detail_elements'] = list(set(detail_elements))

        xml_elements = set(element_counts.keys())
        admin_elements = {'ADMIN-DATA', 'SDGS', 'SDG', 'SD'}
        if not (admin_elements & xml_elements):
            priority_strategy['avoid_elements'] = list(admin_elements)
            priority_strategy['skip_elements'] = admin_elements

        generation_order = []
        seen = set()
        for item in structure:
            if item['element'] not in seen and item['element'] not in priority_strategy['avoid_elements']:
                generation_order.append(item['element'])
                seen.add(item['element'])

        priority_strategy['generation_order'] = generation_order

        return priority_strategy

    def _get_default_priority_strategy(self):
        return {
            'core_structures': ['APPLICATION-SW-COMPONENT-TYPE', 'PORTS', 'INTERNAL-BEHAVIORS'],
            'main_containers': ['SHORT-NAME', 'P-PORT-PROTOTYPE', 'R-PORT-PROTOTYPE', 'SWC-INTERNAL-BEHAVIOR'],
            'detail_elements': ['VARIABLE-ACCESS', 'AUTOSAR-VARIABLE-IREF'],
            'avoid_elements': ['ADMIN-DATA', 'SDGS', 'SDG', 'SD'],
            'generation_order': ['APPLICATION-SW-COMPONENT-TYPE', 'SHORT-NAME', 'PORTS', 'INTERNAL-BEHAVIORS'],
            'skip_elements': {'ADMIN-DATA', 'SDGS', 'SDG', 'SD'}
        }

    def _load_content_guidance(self):
        if hasattr(self.fsm_engine, 'fsm_data') and 'content_guidance' in self.fsm_engine.fsm_data:
            return self.fsm_engine.fsm_data['content_guidance']
        return {}

    def _build_element_hierarchy_from_fsm(self):
        hierarchy = {}
        if not hasattr(self.fsm_engine, 'transitions'):
            return hierarchy

        for state, transitions in self.fsm_engine.transitions.items():
            if not state:
                continue

            state_parts = state.split()
            if state_parts:
                current_element = state_parts[-1]
                child_elements = []
                for next_token in transitions.keys():
                    if not next_token.startswith('_COMPLETE'):
                        child_elements.append(next_token)

                if child_elements:
                    hierarchy[current_element] = child_elements

        return hierarchy

    def _extract_content_elements_from_fsm(self):
        content_elements = set()

        if self.content_guidance:
            guidance_elements = self.content_guidance.get('content_elements', {})
            content_elements.update(guidance_elements.keys())

        common_content_elements = {
            'SHORT-NAME', 'PROVIDED-INTERFACE-TREF', 'REQUIRED-INTERFACE-TREF',
            'DATA-ELEMENT-REF', 'PORT-PROTOTYPE-REF', 'TARGET-DATA-PROTOTYPE-REF',
            'START-ON-EVENT-REF', 'PERIOD', 'ALIVE-TIMEOUT', 'HANDLE-TIMEOUT-TYPE',
            'SYMBOL', 'SD'
        }
        content_elements.update(common_content_elements)

        return content_elements

# 🔥 主要的云端服务类
class EnhancedCloudService:
    """增强云端服务 - 修复版本，解决所有错误"""

    def __init__(self):
        self.app = FastAPI(
            title="Enhanced AUTOSAR Cloud vLLM Service with GAD",
            version="8.0.0",
            description="Fixed Version with GBNF, FSM, and GAD Strategies"
        )

        self.vllm_endpoint = "http://localhost:8001"
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0

        # 约束系统
        self.constraint_cache = {}
        self.constraint_engines = {}
        self.constraint_stats = {}

        # 🔥 策略配置（添加GAD支持）
        self.strategy_config = {
            "mode": "gbnf_priority",  # 可选: "gbnf_priority", "enhanced_fsm", "gad_enhanced_fsm"
            "debug": {"enabled": False},

            # GAD策略配置
            "gad_config": {
                "efg_threshold": 0.35,
                "max_candidates": 15,
                "adaptive_threshold": True,
                "temperature_scaling": 0.6,
                "efg_weights": {
                    "gbnf": 0.3,
                    "complexity": 0.3,
                    "structural": 0.4
                },
                "fusion_strategy": "multiplicative",
                "cache_size": 10000,
                "cache_decay": 0.95,
                "max_iterations": 25
            }
        }

        self._setup_routes()
        print("🏗️ Enhanced CloudService v8.0 initialized - With GAD Strategy")
        print("🔥 Available strategies: GBNF Priority, Enhanced FSM, GAD Enhanced FSM")

    def update_strategy_config(self, config: Dict[str, Any]):
        """更新策略配置"""
        self.strategy_config.update(config)
        print(f"🔧 Strategy config updated: {self.strategy_config}")

    async def _load_constraint_files(self):
        """预加载约束文件到内存并初始化约束引擎"""
        start_time = time.time()
        constraint_dir = Path("../")

        print("📂 Loading original constraint files...")

        # 加载FSM文件并创建引擎
        fsm_files = list(constraint_dir.glob("*.fsm"))
        print(f"🔍 Found {len(fsm_files)} FSM files: {[f.name for f in fsm_files]}")

        for fsm_file in fsm_files:
            try:
                name = fsm_file.stem
                print(f"📥 Loading FSM: {fsm_file.name}")

                with open(fsm_file, 'r', encoding='utf-8') as f:
                    fsm_data = json.load(f)

                fsm_engine = FSMConstraintEngine(fsm_data)

                self.constraint_cache[f"fsm_{name}"] = {
                    "type": "fsm",
                    "data": fsm_data,
                    "file_size": fsm_file.stat().st_size,
                    "loaded_at": time.time()
                }

                self.constraint_engines[f"fsm_{name}"] = fsm_engine
                print(f"✅ FSM '{name}' engine created")

            except Exception as e:
                print(f"❌ Failed to load FSM {fsm_file.name}: {e}")

        # 🔥 加载GBNF文件并创建引擎（最小修复）
        gbnf_files = list(constraint_dir.glob("*.gbnf"))
        print(f"🔍 Found {len(gbnf_files)} GBNF files: {[f.name for f in gbnf_files]}")

        for gbnf_file in gbnf_files:
            try:
                name = gbnf_file.stem
                print(f"📥 Loading GBNF: {gbnf_file.name}")

                with open(gbnf_file, 'r', encoding='utf-8') as f:
                    gbnf_content = f.read()

                # 🔥 最小修复，保持原始语法
                fixed_grammar = self._minimal_gbnf_fix(gbnf_content)
                gbnf_engine = GBNFConstraintEngine(fixed_grammar)

                self.constraint_cache[f"gbnf_{name}"] = {
                    "type": "gbnf",
                    "data": fixed_grammar,
                    "original_size": gbnf_file.stat().st_size,
                    "loaded_at": time.time()
                }

                self.constraint_engines[f"gbnf_{name}"] = gbnf_engine
                print(f"✅ GBNF '{name}' engine created: valid={gbnf_engine.is_valid}")
                print(f"📋 Original file size: {gbnf_file.stat().st_size} bytes")

            except Exception as e:
                print(f"❌ Failed to load GBNF {gbnf_file.name}: {e}")

        load_time = time.time() - start_time
        print(f"🎉 Constraint loading completed in {load_time:.2f}s")
        print(f"📊 Total engines: {len(self.constraint_engines)}")

    def _minimal_gbnf_fix(self, grammar_rules: str) -> str:
        """🔥 修复GBNF语法 - 处理换行符问题"""
        if not grammar_rules or len(grammar_rules.strip()) < 20:
            print("⚠️ GBNF grammar too short or empty, using fallback")
            # 提供一个简单的fallback语法
            return '''?start: element
?element: "<TEST>" "content" "</TEST>"'''

        print(f"🔧 Fixing GBNF grammar ({len(grammar_rules)} chars)")

        # 🔥 关键修复：确保使用真正的换行符
        fixed_rules = grammar_rules.strip()

        # 修复可能的转义换行符问题
        fixed_rules = fixed_rules.replace('\\n', '\n')  # 将字面的\n转为真正的换行符
        fixed_rules = fixed_rules.replace('\\r', '\r')  # 处理回车符
        fixed_rules = fixed_rules.replace('\\t', '\t')  # 处理制表符

        # 确保规则之间有正确的换行
        import re
        # 在规则定义之间添加换行（如果缺失）
        fixed_rules = re.sub(r'(\?[a-zA-Z_][a-zA-Z0-9_]*\s*:.*?)(\?[a-zA-Z_][a-zA-Z0-9_]*\s*:)',
                             r'\1\n\2', fixed_rules)

        # 基本的语法修复（保守）
        fixed_rules = re.sub(r'\*\s*,', '*,', fixed_rules, flags=re.MULTILINE)  # 保留 *
        fixed_rules = re.sub(r'\{0,\}', '*', fixed_rules)                      # {0,} → *

        print(f"✅ GBNF fixes applied")
        print(f"📋 First 200 chars: {repr(fixed_rules[:200])}")

        return fixed_rules

    def _setup_routes(self):
        """设置API路由"""

        @self.app.get("/")
        async def root():
            return {
                "service": "Enhanced AUTOSAR Cloud vLLM Service with GAD",
                "version": "8.0.0",
                "status": "running",
                "strategies": ["gbnf_priority", "enhanced_fsm", "gad_enhanced_fsm", "unconstrained"],
                "current_strategy": self.strategy_config.get("mode", "enhanced_fsm"),
                "vllm_endpoint": self.vllm_endpoint,
                "constraint_engines": len(self.constraint_engines),
                "features": ["GBNF constraints", "FSM state control", "GAD with EFG estimation"]
            }

        @self.app.get("/strategies")
        async def list_strategies():
            """列出所有可用策略及其配置"""
            return {
                "available_strategies": {
                    "gbnf_priority": {
                        "description": "GBNF grammar-based generation in single pass",
                        "pros": "Fast, structure-aware",
                        "cons": "Less flexible"
                    },
                    "enhanced_fsm": {
                        "description": "Iterative FSM with vLLM guided choice",
                        "pros": "Precise control, step-by-step",
                        "cons": "Slower, may lose global view"
                    },
                    "gad_enhanced_fsm": {
                        "description": "Grammar-Aligned Decoding with EFG estimation",
                        "pros": "Theoretically optimal, balances LLM and grammar",
                        "cons": "More complex, requires tuning"
                    },
                    "unconstrained": {
                        "description": "No constraints, pure LLM generation",
                        "pros": "Most flexible",
                        "cons": "May generate invalid structure"
                    }
                },
                "current_strategy": self.strategy_config.get("mode"),
                "gad_config": self.strategy_config.get("gad_config", {})
            }

        @self.app.get("/health")
        async def health_check():
            """健康检查接口"""
            vllm_status = await self._check_vllm_health()
            return {
                "status": "healthy" if vllm_status["available"] else "unhealthy",
                "vllm_available": vllm_status["available"],
                "constraint_engines": len(self.constraint_engines),
                "current_strategy": self.strategy_config.get("mode"),
                "debug_enabled": self.strategy_config.get("debug", {}).get("enabled", False),
                "mode": "fixed_constraints_raw_output",
                "statistics": {
                    "total_requests": self.request_count,
                    "successful_requests": self.success_count,
                    "failed_requests": self.error_count
                }
            }

        @self.app.post("/update_strategy")
        async def update_strategy(config: Dict[str, Any]):
            """更新约束策略配置 - 支持GAD配置"""
            self.update_strategy_config(config)

            # 如果切换到GAD策略，确保有合适的配置
            if config.get("mode") == "gad_enhanced_fsm":
                if "gad_config" in config:
                    self.strategy_config["gad_config"].update(config["gad_config"])

            return {"message": "Strategy config updated", "current_config": self.strategy_config}

        @self.app.get("/gad_statistics")
        async def get_gad_statistics():
            """获取GAD策略的统计信息"""
            if hasattr(self, 'gad_strategy_instance') and self.gad_strategy_instance:
                return {
                    "gad_stats": self.gad_strategy_instance.get_statistics(),
                    "efg_cache_stats": self.gad_strategy_instance.efg_cache.get_statistics()
                }
            else:
                return {"message": "GAD strategy not active"}

        @self.app.get("/constraints")
        async def list_constraints():
            """列出可用的约束引擎"""
            constraint_summary = {}

            for key, cache_item in self.constraint_cache.items():
                engine = self.constraint_engines.get(key)
                constraint_summary[key] = {
                    "type": cache_item["type"],
                    "size_kb": cache_item.get("file_size", cache_item.get("original_size", 0)) / 1024,
                    "has_engine": engine is not None,
                    "stats": self.constraint_stats.get(key, {})
                }

                if cache_item["type"] == "fsm" and engine:
                    constraint_summary[key]["state_count"] = len(engine.transitions)
                elif cache_item["type"] == "gbnf" and engine:
                    constraint_summary[key]["valid_grammar"] = engine.is_valid
                    constraint_summary[key]["grammar_preview"] = engine.grammar[:200] + "..." if len(
                        engine.grammar) > 200 else engine.grammar

            return {
                "available_constraints": constraint_summary,
                "total_engines": len(self.constraint_engines),
                "supported_strategies": ["gbnf_priority", "iterative_fsm", "hybrid", "unconstrained"],
                "constraint_source": "original_files"
            }

        @self.app.post("/enhanced_generate", response_model=CloudGenerationResponse)
        async def enhanced_generate(request: EnhancedGenerationRequest):
            """🔥 主要生成接口 - 修复版本"""
            self.request_count += 1
            vllm_status = await self._check_vllm_health()
            if not vllm_status["available"]:
                self.error_count += 1
                raise HTTPException(status_code=503, detail="vLLM service unavailable")

            try:
                response = await self.generate_with_original_constraints(request)
                if response.success:
                    self.success_count += 1
                else:
                    self.error_count += 1
                return response
            except Exception as e:
                self.error_count += 1
                print(f"❌ Enhanced generate error: {e}")
                import traceback
                traceback.print_exc()
                raise HTTPException(status_code=500, detail=str(e))

    async def _check_vllm_health(self) -> Dict[str, Any]:
        """检查vLLM服务健康状态"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.vllm_endpoint}/v1/models",
                                       timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    return {"available": resp.status == 200}
        except Exception:
            return {"available": False}

    async def generate_with_original_constraints(self, request: EnhancedGenerationRequest) -> CloudGenerationResponse:
        """🔥 核心生成方法 - 修复FSM引擎获取逻辑"""
        start_time = time.time()

        try:
            print(f"📝 Processing request: {request.request_id}")

            # 确定使用的策略
            strategy_mode = self.strategy_config.get("mode", "enhanced_fsm")
            print(f"🎯 Using strategy: {strategy_mode}")

            # 🔥 提取提示词配置
            prompt_config = self._extract_prompt_config(request)

            constraint_violations = []
            fsm_engine = None
            gbnf_engine = None

            # FSM引擎获取逻辑（保持原有代码）
            if request.constraint_info.fsm_ref:
                fsm_key = f"fsm_{request.constraint_info.fsm_ref}"
                if fsm_key in self.constraint_engines:
                    fsm_engine = self.constraint_engines[fsm_key]
                    fsm_engine.reset()
                    print(f"✅ User-specified FSM engine loaded: {fsm_key}")
                else:
                    constraint_violations.append(f"fsm_engine_not_found: {request.constraint_info.fsm_ref}")
            else:
                fsm_engines = {k: v for k, v in self.constraint_engines.items() if k.startswith("fsm_")}
                if fsm_engines:
                    fsm_key = list(fsm_engines.keys())[0]
                    fsm_engine = fsm_engines[fsm_key]
                    fsm_engine.reset()
                    print(f"✅ Auto-selected FSM engine: {fsm_key}")
                    request.constraint_info.fsm_ref = fsm_key.replace("fsm_", "")

            # GBNF引擎获取逻辑（保持原有代码）
            if request.constraint_info.gbnf_ref:
                gbnf_key = f"gbnf_{request.constraint_info.gbnf_ref}"
                if gbnf_key in self.constraint_engines:
                    gbnf_engine = self.constraint_engines[gbnf_key]
                    print(f"✅ User-specified GBNF engine loaded: {gbnf_key}")
                else:
                    constraint_violations.append(f"gbnf_engine_not_found: {request.constraint_info.gbnf_ref}")
            else:
                gbnf_engines = {k: v for k, v in self.constraint_engines.items() if k.startswith("gbnf_")}
                if gbnf_engines:
                    gbnf_key = list(gbnf_engines.keys())[0]
                    gbnf_engine = gbnf_engines[gbnf_key]
                    print(f"✅ Auto-selected GBNF engine: {gbnf_key}")
                    request.constraint_info.gbnf_ref = gbnf_key.replace("gbnf_", "")

            # 🔥 策略选择逻辑（添加GAD分支）
            raw_output = ""
            constraints_applied = {}

            if strategy_mode == "gad_enhanced_fsm":
                # 🔥 新增：GAD增强FSM策略
                if fsm_engine and gbnf_engine:
                    print("🎯 Initializing GAD Enhanced FSM Strategy")

                    # 创建GAD策略实例
                    gad_config = self.strategy_config.get("gad_config", {})
                    strategy = GADEnhancedFSMStrategy(fsm_engine, gbnf_engine, gad_config)

                    # 保存实例供统计使用
                    self.gad_strategy_instance = strategy

                    # 执行生成
                    raw_output, constraints_applied = await strategy.generate(self.vllm_endpoint, request)

                    # 添加GAD特定的信息
                    constraints_applied["gad_info"] = {
                        "efg_threshold": gad_config.get("efg_threshold", 0.2),
                        "fusion_strategy": gad_config.get("fusion_strategy", "multiplicative"),
                        "cache_hits": strategy.efg_cache.get_statistics()["hit_rate"]
                    }
                else:
                    print("⚠️ GAD requires both FSM and GBNF engines, falling back to enhanced FSM")
                    if fsm_engine:
                        strategy = EnhancedFSMStrategy(fsm_engine, prompt_config)
                        raw_output, constraints_applied = await strategy.generate(self.vllm_endpoint, request)
                    else:
                        raw_output, constraints_applied = await self._generate_unconstrained(request)
                    constraints_applied["strategy"] = "fallback_from_gad"

            elif strategy_mode == "enhanced_fsm":
                if fsm_engine:
                    strategy = EnhancedFSMStrategy(fsm_engine, prompt_config)
                    raw_output, constraints_applied = await strategy.generate(self.vllm_endpoint, request)
                else:
                    print("⚠️ FSM engine not available, falling back to unconstrained")
                    raw_output, constraints_applied = await self._generate_unconstrained(request)
                    constraints_applied["strategy"] = "unconstrained_fallback"

            elif strategy_mode == "gbnf_priority":
                if gbnf_engine:
                    strategy = GBNFPriorityStrategy(gbnf_engine)
                    raw_output, constraints_applied = await strategy.generate(self.vllm_endpoint, request)
                else:
                    print("⚠️ GBNF engine not available, falling back to unconstrained")
                    raw_output, constraints_applied = await self._generate_unconstrained(request)
                    constraints_applied["strategy"] = "unconstrained_fallback"

            else:  # unconstrained
                raw_output, constraints_applied = await self._generate_unconstrained(request)

            # 生成响应
            generation_time = time.time() - start_time

            return CloudGenerationResponse(
                request_id=request.request_id,
                success=True,
                timestamp=time.time(),
                generated_xml=raw_output,
                raw_output=raw_output,
                constraints_applied={
                    "fsm": constraints_applied.get("fsm", False),
                    "gbnf": constraints_applied.get("gbnf", False),
                    "gad": constraints_applied.get("gad", False)
                },
                constraint_violations=constraint_violations,
                generation_time=generation_time,
                model_info={
                    "model_name": "DeepSeek-R1-Distill-Qwen-14B",
                    "constraint_strategy": constraints_applied.get("strategy", strategy_mode),
                    "strategy_details": constraints_applied,
                    "mode": "multi_strategy_with_gad",
                    "prompt_config_used": bool(prompt_config),
                    "engines_used": {
                        "fsm": request.constraint_info.fsm_ref if fsm_engine else None,
                        "gbnf": request.constraint_info.gbnf_ref if gbnf_engine else None
                    }
                }
            )

        except Exception as e:
            error_time = time.time() - start_time
            print(f"❌ Generation failed: {e}")
            import traceback
            traceback.print_exc()

            return CloudGenerationResponse(
                request_id=request.request_id,
                success=False,
                timestamp=time.time(),
                error_message=str(e),
                error_details={"generation_time": error_time, "strategy": strategy_mode}
            )

    def _extract_prompt_config(self, request: EnhancedGenerationRequest) -> dict:
        """🔥 从请求中提取提示词配置"""

        # 方法1：从请求的上下文中提取
        if hasattr(request, 'autosar_context') and request.autosar_context:
            prompt_config = request.autosar_context.get('prompt_config')
            if prompt_config:
                return prompt_config

        # 方法2：从请求的prompt中分析（如果包含完整的component_level内容）
        if request.prompt and len(request.prompt) > 1000:  # 长提示词可能包含示例XML
            return {
                'component_level': request.prompt
            }

        # 方法3：使用服务端的默认配置（如果有的话）
        if hasattr(self, 'default_prompt_config'):
            return self.default_prompt_config

        # 方法4：返回None，让策略使用默认优先级
        return None

    async def _generate_unconstrained(self, request: EnhancedGenerationRequest) -> tuple[str, dict]:
        """无约束生成策略 - 单次请求"""
        print(f"🎯 Using Unconstrained Strategy")

        vllm_request = {
            # "model": "/model/HuggingFace/deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
            "model": "/model/HuggingFace/deepseek-ai/DeepSeek-R1-Distill-Qwen-14B",
            "prompt": request.prompt,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "frequency_penalty": request.frequency_penalty,
            "presence_penalty": request.presence_penalty,
            "stream": False,
            "stop": ["</APPLICATION-SW-COMPONENT-TYPE>"]
        }

        constraints_applied = {"fsm": False, "gbnf": False, "strategy": "unconstrained"}

        async with aiohttp.ClientSession() as session:
            async with session.post(
                    f"{self.vllm_endpoint}/v1/completions",
                    json=vllm_request,
                    timeout=aiohttp.ClientTimeout(total=10000)
            ) as resp:
                if resp.status == 200:
                    response = await resp.json()
                    raw_output = response["choices"][0]["text"]
                    print(f"✅ Unconstrained generation successful: {len(raw_output)} chars")
                    return raw_output, constraints_applied
                else:
                    error_text = await resp.text()
                    raise Exception(f"Unconstrained generation failed: {error_text}")

    # 在服务初始化时添加默认提示词配置加载
    async def _load_default_prompt_config(self):
        """加载默认的提示词配置"""
        try:
            # 尝试从配置文件加载
            import yaml
            config_path = Path("config/main_config.yaml")
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    self.default_prompt_config = config.get('prompts', {})
                    print(f"📋 Loaded default prompt config with {len(self.default_prompt_config)} templates")
            else:
                self.default_prompt_config = {}
        except Exception as e:
            print(f"⚠️ Failed to load prompt config: {e}")
            self.default_prompt_config = {}


async def start_enhanced_service():
    """启动增强服务 - 包含GAD策略"""
    print("🚀 Starting Enhanced AUTOSAR Cloud vLLM Service v8.0...")
    print("🔥 Mode: Multi-Strategy with GAD Support")
    print("🔥 Available Strategies:")
    print("   1️⃣ GBNF Priority: Fast single-pass generation with grammar constraints")
    print("   2️⃣ Enhanced FSM: Iterative generation with state machine control")
    print("   3️⃣ GAD Enhanced FSM: Grammar-Aligned Decoding with EFG estimation")
    print("   4️⃣ Unconstrained: Pure LLM generation without constraints")

    print("\n🔥 GAD Strategy Features:")
    print("   • Expected Future Grammaticality (EFG) estimation")
    print("   • Dynamic threshold adaptation")
    print("   • Multi-dimensional constraint evaluation")
    print("   • Incremental learning with cache")
    print("   • Fusion of LLM probabilities and grammar constraints")

    print(f"\n🔗 Connecting to vLLM at: {service.vllm_endpoint}")

    # 加载配置和约束文件
    print("📋 Loading default prompt configuration...")
    await service._load_default_prompt_config()

    print("📂 Loading original constraint files and initializing engines...")
    await service._load_constraint_files()

    # 检查vLLM健康状态
    vllm_status = await service._check_vllm_health()
    if vllm_status["available"]:
        print("✅ vLLM service is available")
    else:
        print("❌ vLLM service not available")
        print("💡 Service will start but requests will fail until vLLM is ready")

    # 启动服务
    config = uvicorn.Config(service.app, host="0.0.0.0", port=8000, log_level="info", access_log=True)
    server = uvicorn.Server(config)

    print("\n🌐 Starting enhanced server on 0.0.0.0:8000")
    print("📖 API documentation: http://localhost:8000/docs")
    print("🔧 Constraint status: http://localhost:8000/constraints")
    print("🎮 Strategy management: POST /update_strategy")
    print("📊 GAD statistics: GET /gad_statistics")
    print("🎉 Multi-strategy constraint system with GAD ready!")

    print(f"\n📊 Constraint engines: {len(service.constraint_engines)}")
    print(f"🎯 Default strategy: {service.strategy_config.get('mode', 'enhanced_fsm')}")
    print(f"⚡ GAD EFG threshold: {service.strategy_config['gad_config']['efg_threshold']}")
    print(f"🔄 Processing mode: Multi-strategy with Grammar-Aligned Decoding")

    await server.serve()


# 全局服务实例
service = EnhancedCloudService()

if __name__ == "__main__":
    try:
        asyncio.run(start_enhanced_service())
    except KeyboardInterrupt:
        print("\n🛑 Service stopped by user")
    except Exception as e:
        print(f"❌ Service failed to start: {e}")
        import traceback

        traceback.print_exc()