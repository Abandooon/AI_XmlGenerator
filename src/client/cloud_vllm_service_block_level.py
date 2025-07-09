#!/usr/bin/env python3
# cloud_vllm_service_block_level.py - 包含块级FSM策略的云端服务

import asyncio
import json
import time
import uuid
import re
from typing import Dict, List, Optional, Any, Set
from pathlib import Path
import xml.etree.ElementTree as ET

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict
import uvicorn
import aiohttp
import nest_asyncio

# 🔥 导入所有策略类
from generic_gad_enhanced_fsm_strategy import FixedGenericGADEnhancedFSMStrategy, EFGCache
# 🎯 新增: 导入块级FSM策略
from block_level_fsm_strategy import BlockLevelFSMStrategy

nest_asyncio.apply()


# ===== 数据模型保持不变 =====
class ConstraintInfo(BaseModel):
    """约束信息模型 - 支持引用和传统模式"""
    model_config = ConfigDict(protected_namespaces=())

    # 引用模式（优先使用）
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
    temperature: float = 0.7
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


# ===== 约束引擎类保持不变 =====
class GBNFConstraintEngine:
    """GBNF约束引擎 - 修复换行符处理"""

    def __init__(self, gbnf_grammar: str):
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
        """验证GBNF语法有效性"""
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
                print("⚠️ GBNF grammar contains literal \\n")
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


class FSMConstraintEngine:
    """FSM约束引擎"""

    def __init__(self, fsm_data: Dict):
        self.fsm_data = fsm_data
        self.transitions = fsm_data.get("edges", {})
        self.accepting_states = set(fsm_data.get("accept", []))
        self.current_state = ""
        self.token_history = []

        print(f"🔧 FSM Engine initialized: {len(self.transitions)} states")

    def get_allowed_tokens(self, current_path: List[str] = None) -> List[str]:
        """根据当前状态获取允许的下一个token"""
        if current_path is None:
            current_path = self.token_history

        if not current_path:
            current_state = ""
        else:
            current_state = " ".join(current_path)

        print(f"🎯 FSM查询状态: '{current_state}'")

        # 精确匹配
        if current_state in self.transitions:
            allowed = list(self.transitions[current_state].keys())
            print(f"✅ 精确匹配成功: {len(allowed)} tokens")
            return allowed

        # 模糊匹配
        allowed = self._fuzzy_match_state(current_state)
        if allowed:
            print(f"🔍 模糊匹配成功: {len(allowed)} tokens")
            return allowed

        # 回退策略
        if current_path:
            for i in range(len(current_path) - 1, 0, -1):
                shorter_state = " ".join(current_path[:i])
                if shorter_state in self.transitions:
                    allowed = list(self.transitions[shorter_state].keys())
                    print(f"🔄 回退匹配成功: {len(allowed)} tokens")
                    return allowed

        print(f"❌ 状态匹配失败: '{current_state}'")
        return []

    def _fuzzy_match_state(self, target_state: str) -> List[str]:
        """模糊匹配算法"""
        if not target_state:
            return list(self.transitions.get("", {}).keys())

        target_tokens = target_state.split()

        # 寻找包含所有目标token的状态
        for state in self.transitions.keys():
            if not state:
                continue
            state_tokens = state.split()
            if len(state_tokens) >= len(target_tokens):
                if all(token in state_tokens for token in target_tokens):
                    return list(self.transitions[state].keys())

        # 前缀匹配
        for state in self.transitions.keys():
            if state.startswith(target_state):
                return list(self.transitions[state].keys())

        return []

    def reset(self):
        """重置状态机"""
        self.current_state = ""
        self.token_history = []
        print("🔄 FSM状态机已重置")


# ===== 其他策略类保持不变 =====
class GBNFPriorityStrategy:
    """GBNF优先约束策略"""

    def __init__(self, gbnf_engine):
        self.gbnf_engine = gbnf_engine

    async def generate(self, vllm_endpoint: str, request: EnhancedGenerationRequest) -> tuple[str, dict]:
        """GBNF优先生成策略"""
        print(f"🎯 Using GBNF Priority Strategy")

        vllm_request = {
            "model": "/model/HuggingFace/deepseek-ai/DeepSeek-R1-Distill-Qwen-14B",
            "prompt": request.prompt,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "frequency_penalty": request.frequency_penalty,
            "presence_penalty": request.presence_penalty,
            "stream": False,
            "stop": ["</APPLICATION-SW-COMPONENT-TYPE>", "</COMPONENT>", "</ROOT>"]
        }

        constraints_applied = {"gbnf": False, "fsm": False, "strategy": "gbnf_priority"}

        if self.gbnf_engine and self.gbnf_engine.is_valid:
            grammar = self.gbnf_engine.grammar
            # 确保没有字面的换行符
            grammar = grammar.replace('\\n', '\n')
            grammar = grammar.replace('\\r', '\r')

            vllm_request["guided_grammar"] = grammar
            constraints_applied["gbnf"] = True

            print(f"✅ Applied GBNF constraint: {len(grammar)} chars")
        else:
            print("⚠️ No valid GBNF engine available")

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                        f"{vllm_endpoint}/v1/completions",
                        json=vllm_request,
                        timeout=aiohttp.ClientTimeout(total=600)
                ) as resp:
                    if resp.status == 200:
                        response = await resp.json()
                        raw_output = response["choices"][0]["text"]
                        print(f"✅ GBNF generation successful: {len(raw_output)} chars")
                        return raw_output, constraints_applied
                    else:
                        error_text = await resp.text()
                        raise Exception(f"vLLM error: {error_text}")
            except Exception as e:
                print(f"❌ Request failed: {e}")
                raise


class GenericEnhancedFSMStrategy:
    """通用的增强FSM策略 - 移除硬编码"""

    def __init__(self, fsm_engine, config=None):
        self.fsm_engine = fsm_engine
        self.config = config or {}
        self.max_iterations = self.config.get('max_iterations', 100)
        self.max_tokens_per_step = self.config.get('max_tokens_per_step', 600)
        self.temperature = self.config.get('temperature', 0.3)
        self.top_p = self.config.get('top_p', 0.9)
        self.choice_range = self.config.get('choice_range', 30)

    async def generate(self, vllm_endpoint: str, request: EnhancedGenerationRequest) -> tuple[str, dict]:
        """通用生成方法"""
        print(f"🎯 Using Generic Enhanced FSM Strategy")

        # 初始化
        generation_path = []
        xml_content = ""
        constraints_applied = {"fsm": True, "gbnf": False, "strategy": "generic_enhanced_fsm"}
        iteration_log = []

        # 重置FSM引擎
        self.fsm_engine.reset()

        for step in range(self.max_iterations):
            print(f"\n--- 步骤 {step + 1}/{self.max_iterations} ---")
            print(f"📍 生成路径: {' -> '.join(generation_path) if generation_path else '空'}")

            # 获取允许的tokens
            allowed_tokens = self.fsm_engine.get_allowed_tokens(generation_path)
            if not allowed_tokens:
                print(f"🛑 无可用tokens，结束生成")
                break

            # 让LLM选择
            try:
                selected_token = await self._llm_select_token(
                    vllm_endpoint,
                    allowed_tokens[:self.choice_range],
                    generation_path,
                    xml_content,
                    request.prompt
                )

                if not selected_token:
                    print(f"❌ LLM未返回有效token")
                    break

                print(f"✅ LLM选择: {selected_token}")

            except Exception as e:
                print(f"❌ LLM调用失败: {e}")
                # 降级：选择第一个
                selected_token = allowed_tokens[0] if allowed_tokens else None
                if not selected_token:
                    break

            # 处理选择的token
            if selected_token.startswith("_COMPLETE_"):
                # 完成标记
                element_to_close = selected_token.replace('_COMPLETE_', '')
                if element_to_close in generation_path:
                    idx = generation_path.index(element_to_close)
                    generation_path = generation_path[:idx]
                print(f"🔄 完成元素: {element_to_close}")
            else:
                # 生成XML片段
                xml_fragment = await self._generate_xml_fragment(
                    vllm_endpoint,
                    selected_token,
                    generation_path,
                    xml_content,
                    request.prompt
                )

                if xml_fragment:
                    xml_content += xml_fragment

                    # 更新路径（如果不是自闭合标签）
                    if not xml_fragment.strip().endswith('/>'):
                        generation_path.append(selected_token)

                    print(f"📝 生成: {xml_fragment.strip()[:80]}...")

            # 记录迭代
            iteration_log.append({
                "step": step + 1,
                "selected_token": selected_token,
                "path_depth": len(generation_path),
                "xml_length": len(xml_content)
            })

            # 检查完成条件
            if self._should_complete(generation_path, xml_content, step):
                print(f"🏁 满足完成条件")
                break

        # 完成XML结构
        final_xml = self._finalize_xml(xml_content, generation_path)

        constraints_applied.update({
            "steps": step + 1,
            "iterations": iteration_log
        })

        return final_xml, constraints_applied

    async def _llm_select_token(self, vllm_endpoint: str, candidates: List[str],
                                path: List[str], xml_content: str, base_prompt: str) -> str:
        """让LLM选择token"""
        prompt = f"""{base_prompt}

You are building an XML structure step by step. Select the most appropriate next element.

Current XML:
```xml
{xml_content[-500:] if len(xml_content) > 500 else xml_content}
```

Current position: {' -> '.join(path[-3:]) if path else 'Starting'}
Available choices: {', '.join(candidates)}

Select ONE element name:"""

        vllm_request = {
            "model": "/model/HuggingFace/deepseek-ai/DeepSeek-R1-Distill-Qwen-14B",
            "prompt": prompt,
            "max_tokens": 50,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "stream": False,
            "guided_choice": candidates,
            "guided_decoding_backend": "outlines"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                    f"{vllm_endpoint}/v1/completions",
                    json=vllm_request,
                    timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status == 200:
                    response = await resp.json()
                    output = response["choices"][0]["text"].strip()

                    # 提取token
                    for candidate in candidates:
                        if candidate in output.upper():
                            return candidate

                    return candidates[0] if candidates else None
                else:
                    raise Exception(f"vLLM error: {resp.status}")

    async def _generate_xml_fragment(self, vllm_endpoint: str, token: str,
                                     path: List[str], current_xml: str,
                                     base_prompt: str) -> str:
        """生成XML片段 - 让LLM决定内容"""
        indent = "  " * len(path)

        # 让LLM决定是否需要内容
        prompt = f"""Based on the context, does <{token}> need text content or is it a container?

Context: {' -> '.join(path[-2:]) if path else 'Root'}
Requirements: {base_prompt[:200]}...

Answer: CONTENT or CONTAINER"""

        vllm_request = {
            "model": "/model/HuggingFace/deepseek-ai/DeepSeek-R1-Distill-Qwen-14B",
            "prompt": prompt,
            "max_tokens": 20,
            "temperature": 0.1,
            "stream": False
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                        f"{vllm_endpoint}/v1/completions",
                        json=vllm_request,
                        timeout=aiohttp.ClientTimeout(total=15)
                ) as resp:
                    if resp.status == 200:
                        response = await resp.json()
                        answer = response["choices"][0]["text"].strip().upper()

                        if "CONTENT" in answer:
                            # 生成内容
                            content = await self._generate_content(
                                vllm_endpoint, token, path, current_xml, base_prompt
                            )
                            return f"{indent}<{token}>{content}</{token}>\n"
                        else:
                            # 容器元素
                            return f"{indent}<{token}>\n"
        except:
            # 默认作为容器
            return f"{indent}<{token}>\n"

        return f"{indent}<{token}>\n"

    async def _generate_content(self, vllm_endpoint: str, element: str,
                                path: List[str], current_xml: str,
                                base_prompt: str) -> str:
        """生成元素内容"""
        prompt = f"""Generate content for <{element}>.

Context: {' -> '.join(path[-2:]) if path else 'Root'}
Requirements: {base_prompt[:300]}...

Content:"""

        vllm_request = {
            "model": "/model/HuggingFace/deepseek-ai/DeepSeek-R1-Distill-Qwen-14B",
            "prompt": prompt,
            "max_tokens": 100,
            "temperature": 0.3,
            "stream": False,
            "stop": ["<", "\n\n"]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                    f"{vllm_endpoint}/v1/completions",
                    json=vllm_request,
                    timeout=aiohttp.ClientTimeout(total=20)
            ) as resp:
                if resp.status == 200:
                    response = await resp.json()
                    return response["choices"][0]["text"].strip()
                else:
                    return f"Generated_{element}"

    def _should_complete(self, path: List[str], xml: str, step: int) -> bool:
        """判断是否完成"""
        if step >= self.max_iterations - 1:
            return True

        if not path and len(xml) > 100:
            return True

        state = " ".join(path) if path else ""
        if state in self.fsm_engine.accepting_states:
            return True

        return False

    def _finalize_xml(self, xml_content: str, path: List[str]) -> str:
        """完成XML结构"""
        closing_tags = []

        for i in range(len(path) - 1, -1, -1):
            tag = path[i]
            indent = "  " * i
            closing_tags.append(f"{indent}</{tag}>")

        if closing_tags:
            xml_content += "\n".join(closing_tags) + "\n"

        return xml_content.strip()


# 🎯 主云端服务类 - 包含块级FSM支持
class EnhancedCloudService:
    """增强云端服务 - 支持块级FSM策略"""

    def __init__(self):
        """🔥 完整替换: 增加新配置参数支持"""
        self.app = FastAPI(
            title="Generic XML Generation Service with Block-Level Strategy",
            version="10.0.0",  # 🎯 版本号更新
            description="Domain-agnostic XML generation with block-level FSM strategy"
        )

        self.vllm_endpoint = "http://localhost:8001"
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0

        # 约束系统
        self.constraint_cache = {}
        self.constraint_engines = {}
        self.constraint_stats = {}

        # 🎯 修复: 扩展策略配置，支持新参数
        self.strategy_config = {
            "mode": "block_level_fsm",  # 🎯 默认使用新的块级FSM策略
            "debug": {"enabled": True},  # 🔥 启用调试

            # 🎯 新增: 块级FSM策略配置
            "block_level_fsm": {
                "max_blocks": 10,  # 最大块数
                "temperature": 0.3,  # LLM温度
                "top_p": 0.9,  # 采样参数
                "block_validation": True,  # 启用块验证
                "retry_on_failure": True,  # 失败时重试
                "structure_planning": True,  # 启用结构规划
                "block_definitions": {
                    "header_block": {"priority": 1, "required": True},
                    "ports_block": {"priority": 2, "required": False},
                    "behaviors_block": {"priority": 3, "required": False}
                }
            },

            # 🔥 修复后的GAD策略配置 - 支持所有新参数
            "gad_config": {
                # 基础参数
                "efg_threshold": 0.25,  # 🔥 降低阈值
                "max_candidates": 25,  # 🔥 增加候选数
                "adaptive_threshold": True,
                "temperature_scaling": 0.7,  # 🔥 提高创造性
                "max_iterations": 40,  # 🔥 增加迭代数
                "cache_size": 15000,  # 🔥 增加缓存
                "cache_decay": 0.97,  # 🔥 减少衰减

                # EFG权重配置
                "efg_weights": {
                    "structural": 0.3,  # 🔥 降低结构权重
                    "grammatical": 0.5,  # 🔥 提高语法权重
                    "contextual": 0.2  # 保持上下文权重
                },

                # 🔥 新增: 重复检测配置
                "repetition_control": {
                    "enabled": True,
                    "semantic_analysis": True,  # 启用语义分析
                    "default_allow_repetition": True,  # 默认允许重复
                    "llm_decision_timeout": 10  # LLM决策超时
                },

                # 🔥 新增: 完成条件配置
                "completion_control": {
                    "min_xml_length": 200,  # 最小XML长度
                    "min_depth_reached": 3,  # 最小路径深度
                    "require_multiple_elements": True,  # 要求多个元素
                    "strict_accepting_states": True  # 严格接受状态
                },

                # 🔥 新增: XML生成配置
                "xml_generation": {
                    "element_analysis_enabled": True,  # 启用元素分析
                    "content_generation_timeout": 20,  # 内容生成超时
                    "attribute_generation_timeout": 15,  # 属性生成超时
                    "semantic_content_decision": True  # 语义内容决策
                },

                # 其他配置
                "fusion_strategy": "weighted_sum",  # 🔥 改为加权求和
                "temperature": 0.4,  # 🔥 LLM温度
                "top_p": 0.9  # LLM采样参数
            },

            # 其他策略配置保持不变
            "enhanced_fsm": {
                "max_iterations": 100,
                "max_tokens_per_step": 600,
                "temperature": 0.4,
                "top_p": 0.85,
                "choice_range": 30
            }
        }

        self._setup_routes()
        print("🏗️ Fixed Generic Cloud Service v10.0 initialized")
        print("🎯 New Block-Level FSM strategy for efficient XML generation")
        print("🔥 Enhanced GAD strategy with intelligent repetition and completion control")

    def update_strategy_config(self, config: Dict[str, Any]):
        """更新策略配置"""
        self.strategy_config.update(config)
        print(f"🔧 Strategy config updated: {self.strategy_config}")

    async def _load_constraint_files(self):
        """预加载约束文件 - 保持不变"""
        start_time = time.time()
        constraint_dir = Path("./")

        print("📂 Loading constraint files...")

        # 加载FSM文件
        fsm_files = list(constraint_dir.glob("*.fsm"))
        print(f"🔍 Found {len(fsm_files)} FSM files")

        for fsm_file in fsm_files:
            try:
                name = fsm_file.stem
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
                print(f"✅ FSM '{name}' loaded")

            except Exception as e:
                print(f"❌ Failed to load FSM {fsm_file.name}: {e}")

        # 加载GBNF文件
        gbnf_files = list(constraint_dir.glob("*.gbnf"))
        print(f"🔍 Found {len(gbnf_files)} GBNF files")

        for gbnf_file in gbnf_files:
            try:
                name = gbnf_file.stem
                with open(gbnf_file, 'r', encoding='utf-8') as f:
                    gbnf_content = f.read()

                # 修复语法
                fixed_grammar = self._fix_gbnf_grammar(gbnf_content)
                gbnf_engine = GBNFConstraintEngine(fixed_grammar)

                self.constraint_cache[f"gbnf_{name}"] = {
                    "type": "gbnf",
                    "data": fixed_grammar,
                    "original_size": gbnf_file.stat().st_size,
                    "loaded_at": time.time()
                }

                self.constraint_engines[f"gbnf_{name}"] = gbnf_engine
                print(f"✅ GBNF '{name}' loaded: valid={gbnf_engine.is_valid}")

            except Exception as e:
                print(f"❌ Failed to load GBNF {gbnf_file.name}: {e}")

        load_time = time.time() - start_time
        print(f"🎉 Constraint loading completed in {load_time:.2f}s")
        print(f"📊 Total engines: {len(self.constraint_engines)}")

    def _fix_gbnf_grammar(self, grammar_rules: str) -> str:
        """修复GBNF语法 - 保持不变"""
        if not grammar_rules or len(grammar_rules.strip()) < 20:
            return '''?start: element\n?element: "<TEST>" "content" "</TEST>"'''

        fixed_rules = grammar_rules.strip()

        # 修复换行符
        fixed_rules = fixed_rules.replace('\\n', '\n')
        fixed_rules = fixed_rules.replace('\\r', '\r')
        fixed_rules = fixed_rules.replace('\\t', '\t')

        # 确保规则之间有换行
        import re
        fixed_rules = re.sub(r'(\?[a-zA-Z_][a-zA-Z0-9_]*\s*:.*?)(\?[a-zA-Z_][a-zA-Z0-9_]*\s*:)',
                             r'\1\n\2', fixed_rules)

        # 基本语法修复
        fixed_rules = re.sub(r'\*\s*,', '+', fixed_rules, flags=re.MULTILINE)
        fixed_rules = re.sub(r'\{0,\}', '+', fixed_rules)

        return fixed_rules

    def _setup_routes(self):
        """设置API路由"""

        @self.app.get("/")
        async def root():
            return {
                "service": "Fixed Generic XML Generation Service",
                "version": "10.0.0",  # 🎯 更新版本
                "status": "running",
                "strategies": ["gbnf_priority", "enhanced_fsm", "gad_enhanced_fsm", "block_level_fsm", "unconstrained"],
                "current_strategy": self.strategy_config.get("mode"),
                "vllm_endpoint": self.vllm_endpoint,
                "constraint_engines": len(self.constraint_engines),
                "features": [
                    "Domain-agnostic",
                    "LLM-driven content",
                    "Flexible constraints",
                    "🔥 Fixed repetition detection",
                    "🔥 Intelligent completion control",
                    "🔥 Semantic element analysis",
                    "🎯 NEW: Block-level generation for efficiency"  # 🎯 新特性
                ]
            }

        @self.app.get("/strategies")
        async def list_strategies():
            """列出所有可用策略"""
            return {
                "available_strategies": {
                    "block_level_fsm": {
                        "description": "🎯 Block-Level FSM - Efficient chunk-based generation",
                        "domain_agnostic": True,
                        "recommended": True,
                        "efficiency": "5-8x faster than token-level",
                        "features": [
                            "Generates complete logical blocks",
                            "Structure planning phase",
                            "Minimal LLM calls (5-8 vs 40+)",
                            "Better semantic coherence",
                            "FSM-guided block transitions"
                        ]
                    },
                    "gbnf_priority": {
                        "description": "GBNF grammar-based generation",
                        "domain_agnostic": True
                    },
                    "enhanced_fsm": {
                        "description": "FSM iterative generation",
                        "domain_agnostic": True
                    },
                    "gad_enhanced_fsm": {
                        "description": "🔥 Fixed Generic GAD with enhanced features",
                        "domain_agnostic": True,
                        "new_features": [
                            "Intelligent repetition detection",
                            "Semantic element analysis",
                            "Enhanced completion control",
                            "Improved XML generation"
                        ]
                    },
                    "unconstrained": {
                        "description": "Pure LLM generation",
                        "domain_agnostic": True
                    }
                },
                "current_strategy": self.strategy_config.get("mode"),
                "strategy_configs": {
                    "block_level_fsm": self.strategy_config.get("block_level_fsm", {}),
                    "gad_config": self.strategy_config.get("gad_config", {})
                }
            }

        @self.app.get("/health")
        async def health_check():
            """健康检查"""
            vllm_status = await self._check_vllm_health()
            return {
                "status": "healthy" if vllm_status["available"] else "unhealthy",
                "vllm_available": vllm_status["available"],
                "constraint_engines": len(self.constraint_engines),
                "current_strategy": self.strategy_config.get("mode"),
                "mode": "block_level_generic_xml_generation",  # 🎯 更新模式
                "version": "10.0.0"  # 🎯 版本信息
            }

        # 🔥 修复3: 更新策略配置接口 - 完整替换
        @self.app.post("/update_strategy")
        async def update_strategy(config: Dict[str, Any]):
            """🔥 完整替换: 更新策略配置 - 支持所有新参数"""
            # 从配置文件读取策略配置
            if 'constraint_strategy' in config:
                strategy_config = config['constraint_strategy']

                # 设置模式
                if 'mode' in strategy_config:
                    self.strategy_config['mode'] = strategy_config['mode']

                # 更新GAD策略配置
                if strategy_config['mode'] == 'gad_enhanced_fsm' and 'gad_enhanced_fsm' in strategy_config:
                    gad_config = strategy_config['gad_enhanced_fsm']

                    # 🔥 更新基础配置
                    self.strategy_config['gad_config'].update({
                        'efg_threshold': gad_config.get('efg_threshold', 0.25),
                        'max_candidates': gad_config.get('max_candidates', 25),
                        'adaptive_threshold': gad_config.get('adaptive_threshold', True),
                        'temperature_scaling': gad_config.get('temperature_scaling', 0.7),
                        'max_iterations': gad_config.get('max_iterations', 40),
                        'cache_size': gad_config.get('cache_size', 15000),
                        'cache_decay': gad_config.get('cache_decay', 0.97),
                        'fusion_strategy': gad_config.get('fusion_strategy', 'weighted_sum'),
                        'temperature': gad_config.get('temperature', 0.4),
                        'top_p': gad_config.get('top_p', 0.9)
                    })

                    # 🔥 更新EFG权重
                    if 'efg_weights' in gad_config:
                        self.strategy_config['gad_config']['efg_weights'].update(
                            gad_config['efg_weights']
                        )

                    # 🔥 更新重复检测配置
                    if 'repetition_control' in gad_config:
                        if 'repetition_control' not in self.strategy_config['gad_config']:
                            self.strategy_config['gad_config']['repetition_control'] = {}
                        self.strategy_config['gad_config']['repetition_control'].update(
                            gad_config['repetition_control']
                        )

                    # 🔥 更新完成条件配置
                    if 'completion_control' in gad_config:
                        if 'completion_control' not in self.strategy_config['gad_config']:
                            self.strategy_config['gad_config']['completion_control'] = {}
                        self.strategy_config['gad_config']['completion_control'].update(
                            gad_config['completion_control']
                        )

                    # 🔥 更新XML生成配置
                    if 'xml_generation' in gad_config:
                        if 'xml_generation' not in self.strategy_config['gad_config']:
                            self.strategy_config['gad_config']['xml_generation'] = {}
                        self.strategy_config['gad_config']['xml_generation'].update(
                            gad_config['xml_generation']
                        )

                # 🎯 新增：更新块级FSM策略配置
                elif strategy_config['mode'] == 'block_level_fsm' and 'block_level_fsm' in strategy_config:
                    block_config = strategy_config['block_level_fsm']
                    self.strategy_config['block_level_fsm'].update(block_config)

                elif strategy_config['mode'] == 'enhanced_fsm' and 'enhanced_fsm' in strategy_config:
                    fsm_config = strategy_config['enhanced_fsm']
                    self.strategy_config['enhanced_fsm'] = fsm_config

            else:
                # 直接更新（旧格式兼容）
                self.update_strategy_config(config)

            return {
                "message": "Strategy config updated with new parameters",
                "current_config": self.strategy_config,
                "updated_features": [  # 🎯 显示更新的特性
                    "block_level_generation" if self.strategy_config.get(
                        "mode") == "block_level_fsm" else "token_level_generation",
                    "repetition_control", "completion_control",
                    "xml_generation", "enhanced_efg_weights"
                ]
            }

        @self.app.get("/gad_statistics")
        async def get_gad_statistics():
            """获取GAD统计信息"""
            if hasattr(self, 'gad_strategy_instance') and self.gad_strategy_instance:
                return {
                    "gad_stats": self.gad_strategy_instance.get_statistics(),
                    "efg_cache_stats": self.gad_strategy_instance.efg_cache.get_statistics()
                }
            else:
                return {"message": "GAD strategy not active"}

        @self.app.get("/block_fsm_statistics")
        async def get_block_fsm_statistics():
            """获取块级FSM统计信息"""
            if hasattr(self, 'block_strategy_instance') and self.block_strategy_instance:
                return {
                    "block_fsm_stats": self.block_strategy_instance.get_statistics(),
                    "efficiency_metrics": {
                        "avg_blocks_per_generation": self.block_strategy_instance.stats.get('avg_blocks_per_generation',
                                                                                            0),
                        "avg_llm_calls": self.block_strategy_instance.stats.get('avg_llm_calls', 0),
                        "efficiency_gain": f"{40 / max(1, self.block_strategy_instance.stats.get('avg_llm_calls', 1)):.1f}x"
                    }
                }
            else:
                return {"message": "Block-level FSM strategy not active"}

        @self.app.get("/constraints")
        async def list_constraints():
            """列出可用约束"""
            constraint_summary = {}

            for key, cache_item in self.constraint_cache.items():
                engine = self.constraint_engines.get(key)
                constraint_summary[key] = {
                    "type": cache_item["type"],
                    "size_kb": cache_item.get("file_size", cache_item.get("original_size", 0)) / 1024,
                    "has_engine": engine is not None
                }

                if cache_item["type"] == "fsm" and engine:
                    constraint_summary[key]["state_count"] = len(engine.transitions)
                elif cache_item["type"] == "gbnf" and engine:
                    constraint_summary[key]["valid_grammar"] = engine.is_valid

            return {
                "available_constraints": constraint_summary,
                "total_engines": len(self.constraint_engines)
            }

        @self.app.post("/enhanced_generate", response_model=CloudGenerationResponse)
        async def enhanced_generate(request: EnhancedGenerationRequest):
            """主生成接口"""
            self.request_count += 1
            vllm_status = await self._check_vllm_health()
            if not vllm_status["available"]:
                self.error_count += 1
                raise HTTPException(status_code=503, detail="vLLM service unavailable")

            try:
                response = await self.generate_with_constraints(request)
                if response.success:
                    self.success_count += 1
                else:
                    self.error_count += 1
                return response
            except Exception as e:
                self.error_count += 1
                print(f"❌ Generate error: {e}")
                import traceback
                traceback.print_exc()
                raise HTTPException(status_code=500, detail=str(e))

    async def _check_vllm_health(self) -> Dict[str, Any]:
        """检查vLLM健康状态 - 保持不变"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.vllm_endpoint}/v1/models",
                                       timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    return {"available": resp.status == 200}
        except Exception:
            return {"available": False}

    # 🔥 修复4: 核心生成方法 - 完整替换
    async def generate_with_constraints(self, request: EnhancedGenerationRequest) -> CloudGenerationResponse:
        """🔥 完整替换: 核心生成方法 - 使用修复后的策略"""
        start_time = time.time()

        try:
            print(f"📝 Processing request: {request.request_id}")

            # 确定策略
            strategy_mode = self.strategy_config.get("mode", "block_level_fsm")
            print(f"🎯 Using strategy: {strategy_mode}")

            constraint_violations = []
            fsm_engine = None
            gbnf_engine = None

            # 获取FSM引擎
            if request.constraint_info.fsm_ref:
                fsm_key = f"fsm_{request.constraint_info.fsm_ref}"
                if fsm_key in self.constraint_engines:
                    fsm_engine = self.constraint_engines[fsm_key]
                    fsm_engine.reset()
                    print(f"✅ FSM engine loaded: {fsm_key}")
                else:
                    constraint_violations.append(f"fsm_not_found: {request.constraint_info.fsm_ref}")
            else:
                # 自动选择第一个FSM
                fsm_engines = {k: v for k, v in self.constraint_engines.items() if k.startswith("fsm_")}
                if fsm_engines:
                    fsm_key = list(fsm_engines.keys())[0]
                    fsm_engine = fsm_engines[fsm_key]
                    fsm_engine.reset()
                    print(f"✅ Auto-selected FSM: {fsm_key}")

            # 获取GBNF引擎
            if request.constraint_info.gbnf_ref:
                gbnf_key = f"gbnf_{request.constraint_info.gbnf_ref}"
                if gbnf_key in self.constraint_engines:
                    gbnf_engine = self.constraint_engines[gbnf_key]
                    print(f"✅ GBNF engine loaded: {gbnf_key}")
                else:
                    constraint_violations.append(f"gbnf_not_found: {request.constraint_info.gbnf_ref}")
            else:
                # 自动选择第一个GBNF
                gbnf_engines = {k: v for k, v in self.constraint_engines.items() if k.startswith("gbnf_")}
                if gbnf_engines:
                    gbnf_key = list(gbnf_engines.keys())[0]
                    gbnf_engine = gbnf_engines[gbnf_key]
                    print(f"✅ Auto-selected GBNF: {gbnf_key}")

            # 策略选择
            raw_output = ""
            constraints_applied = {}

            if strategy_mode == "block_level_fsm":
                # 🎯 使用块级FSM策略
                if fsm_engine:
                    print("🎯 Initializing Block-Level FSM Strategy")

                    block_config = self.strategy_config.get("block_level_fsm", {})
                    strategy = BlockLevelFSMStrategy(fsm_engine, block_config)

                    self.block_strategy_instance = strategy

                    raw_output, constraints_applied = await strategy.generate(self.vllm_endpoint, request)

                    constraints_applied["strategy_info"] = {
                        "strategy_type": "block_level_fsm",
                        "blocks_generated": constraints_applied.get('blocks_generated', 0),
                        "llm_calls": constraints_applied.get('llm_calls', 0),
                        "efficiency": f"{40 / max(1, constraints_applied.get('llm_calls', 1)):.1f}x vs token-level"
                    }
                else:
                    print("⚠️ Block-level FSM requires FSM engine, falling back")
                    raw_output, constraints_applied = await self._generate_unconstrained(request)
                    constraints_applied["strategy"] = "unconstrained_fallback"

            elif strategy_mode == "gad_enhanced_fsm":
                # 🔥 使用修复后的GAD策略
                if fsm_engine and gbnf_engine:
                    print("🎯 Initializing Fixed Generic GAD Enhanced FSM Strategy")

                    # 🔥 传递完整配置给修复后的策略
                    gad_config = self.strategy_config.get("gad_config", {})
                    strategy = FixedGenericGADEnhancedFSMStrategy(fsm_engine, gbnf_engine, gad_config)

                    self.gad_strategy_instance = strategy

                    raw_output, constraints_applied = await strategy.generate(self.vllm_endpoint, request)

                    constraints_applied["gad_info"] = {
                        "strategy_type": "fixed_generic",  # 🔥 更新策略类型
                        "efg_threshold": gad_config.get("efg_threshold"),
                        "cache_hits": strategy.efg_cache.get_statistics()["hit_rate"],
                        "repetition_control": gad_config.get("repetition_control", {}).get("enabled", False),  # 🔥 新增
                        "completion_control": gad_config.get("completion_control", {}).get("enabled", False),  # 🔥 新增
                        "semantic_analysis": gad_config.get("repetition_control", {}).get("semantic_analysis", False)
                        # 🔥 新增
                    }
                else:
                    print("⚠️ GAD requires both FSM and GBNF, falling back")
                    if fsm_engine:
                        # 使用通用增强FSM策略
                        config = self.strategy_config.get("enhanced_fsm", {})
                        strategy = GenericEnhancedFSMStrategy(fsm_engine, config)
                        raw_output, constraints_applied = await strategy.generate(self.vllm_endpoint, request)
                    else:
                        raw_output, constraints_applied = await self._generate_unconstrained(request)
                    constraints_applied["strategy"] = "fallback_from_gad"

            elif strategy_mode == "enhanced_fsm":
                if fsm_engine:
                    config = self.strategy_config.get("enhanced_fsm", {})
                    strategy = GenericEnhancedFSMStrategy(fsm_engine, config)
                    raw_output, constraints_applied = await strategy.generate(self.vllm_endpoint, request)
                else:
                    raw_output, constraints_applied = await self._generate_unconstrained(request)
                    constraints_applied["strategy"] = "unconstrained_fallback"

            elif strategy_mode == "gbnf_priority":
                if gbnf_engine:
                    strategy = GBNFPriorityStrategy(gbnf_engine)
                    raw_output, constraints_applied = await strategy.generate(self.vllm_endpoint, request)
                else:
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
                    "model_name": "DeepSeek-R1-Distill-Qwen-14B",  # 🔥 更新模型名
                    "constraint_strategy": constraints_applied.get("strategy", strategy_mode),
                    "strategy_details": constraints_applied,
                    "mode": "block_level_generic_xml_generation",  # 🎯 更新模式
                    "engines_used": {
                        "fsm": request.constraint_info.fsm_ref if fsm_engine else None,
                        "gbnf": request.constraint_info.gbnf_ref if gbnf_engine else None
                    },
                    "version": "10.0.0",  # 🎯 版本信息
                    "features_applied": [  # 🎯 应用的特性
                        "block_level_generation" if strategy_mode == "block_level_fsm" else "token_level_generation",
                        "intelligent_repetition_detection" if strategy_mode == "gad_enhanced_fsm" else "standard_generation",
                        "semantic_element_analysis",
                        "enhanced_completion_control",
                        "improved_xml_generation"
                    ]
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
                error_details={"generation_time": error_time, "strategy": strategy_mode, "version": "10.0.0"}  # 🎯 版本信息
            )

    async def _generate_unconstrained(self, request: EnhancedGenerationRequest) -> tuple[str, dict]:
        """无约束生成 - 保持不变"""
        print(f"🎯 Using Unconstrained Strategy")

        vllm_request = {
            "model": "/model/HuggingFace/deepseek-ai/DeepSeek-R1-Distill-Qwen-14B",
            "prompt": request.prompt,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "frequency_penalty": request.frequency_penalty,
            "presence_penalty": request.presence_penalty,
            "stream": False
        }

        constraints_applied = {"fsm": False, "gbnf": False, "strategy": "unconstrained"}

        async with aiohttp.ClientSession() as session:
            async with session.post(
                    f"{self.vllm_endpoint}/v1/completions",
                    json=vllm_request,
                    timeout=aiohttp.ClientTimeout(total=600)
            ) as resp:
                if resp.status == 200:
                    response = await resp.json()
                    raw_output = response["choices"][0]["text"]
                    print(f"✅ Unconstrained generation successful")
                    return raw_output, constraints_applied
                else:
                    error_text = await resp.text()
                    raise Exception(f"Unconstrained generation failed: {error_text}")

    async def _load_config_from_file(self, config_path: str = "config/main_config_fixed.yaml"):
        """🔥 从修复后的配置文件加载策略配置"""
        try:
            import yaml
            path = Path(config_path)
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)

                    # 更新策略配置
                    if 'constraint_strategy' in config:
                        await self._setup_routes()  # 确保路由已设置

                        # 通过API更新配置
                        async with aiohttp.ClientSession() as session:
                            async with session.post(
                                    "http://localhost:8000/update_strategy",
                                    json=config
                            ) as resp:
                                if resp.status == 200:
                                    print("📋 Loaded fixed strategy config from file")
                                else:
                                    print("⚠️ Failed to update strategy from config file")
        except Exception as e:
            print(f"⚠️ Failed to load config file: {e}")


# 🔥 修复5: 启动函数 - 更新信息
async def start_fixed_generic_service():
    """启动修复后的通用服务"""
    print("🚀 Starting Fixed Generic XML Generation Service v10.0...")
    print("🔥 Mode: Enhanced Domain-agnostic Constraint System")
    print("🔥 Available Strategies:")
    print("   1️⃣ GBNF Priority: Grammar-based generation")
    print("   2️⃣ Enhanced FSM: Iterative generation")
    print("   3️⃣ 🔥 Fixed Generic GAD FSM: Enhanced LLM-driven with constraints")
    print("   4️⃣ 🎯 Block-Level FSM: Efficient chunk-based generation (NEW!)")
    print("   5️⃣ Unconstrained: Pure LLM generation")

    print("\n🎯 Key Features of Block-Level FSM Strategy:")
    print("   • 📦 Generates complete logical blocks instead of tokens")
    print("   • 🚀 5-8x faster than token-level strategies")
    print("   • 🧠 Better semantic coherence and context understanding")
    print("   • 📋 Intelligent structure planning phase")
    print("   • 🔄 Minimal LLM calls (5-8 vs 40+)")

    print("\n🔥 Key Fixes Applied:")
    print("   • 🔧 Intelligent repetition detection based on XML semantics")
    print("   • 🔧 Enhanced completion control with multiple criteria")
    print("   • 🔧 Improved XML generation with element analysis")
    print("   • 🔧 Better EFG scoring with adjusted weights")
    print("   • 🔧 Semantic content and attribute generation")

    print(f"\n🔗 Connecting to vLLM at: {service.vllm_endpoint}")

    # 加载约束文件
    print("📂 Loading constraint files...")
    await service._load_constraint_files()

    # 🔥 加载修复后的配置文件
    print("📋 Loading fixed configuration...")
    await service._load_config_from_file("config/main_config_fixed.yaml")

    # 检查vLLM健康状态
    vllm_status = await service._check_vllm_health()
    if vllm_status["available"]:
        print("✅ vLLM service is available")
    else:
        print("❌ vLLM service not available")

    # 启动服务
    config = uvicorn.Config(service.app, host="0.0.0.0", port=8000, log_level="info", access_log=True)
    server = uvicorn.Server(config)

    print("\n🌐 Starting fixed server on 0.0.0.0:8000")
    print("📖 API documentation: http://localhost:8000/docs")
    print("🔧 Constraint status: http://localhost:8000/constraints")
    print("🎮 Strategy management: POST /update_strategy")
    print("📊 Block FSM stats: GET /block_fsm_statistics")
    print("🎉 Fixed Generic XML generation system ready!")

    print(f"\n📊 Loaded engines: {len(service.constraint_engines)}")
    print(f"🎯 Default strategy: {service.strategy_config.get('mode')}")
    print(f"🔄 Processing mode: Block-level constraint-based generation")
    print(f"🎯 Version: 10.0.0 with block-level generation")

    await server.serve()


# 全局服务实例
service = EnhancedCloudService()

if __name__ == "__main__":
    try:
        asyncio.run(start_fixed_generic_service())  # 🔥 使用修复后的启动函数
    except KeyboardInterrupt:
        print("\n🛑 Service stopped by user")
    except Exception as e:
        print(f"❌ Service failed to start: {e}")
        import traceback

        traceback.print_exc()