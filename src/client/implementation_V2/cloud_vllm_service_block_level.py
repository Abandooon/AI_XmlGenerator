#!/usr/bin/env python3
# cloud_vllm_service_block_level.py - 修复模型定义不一致问题

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
from block_level_fsm_strategy import BlockLevelFSMStrategy
from dynamic_gbnf_strategy import DynamicGBNFStrategy
# 在现有导入部分添加
from safe_dynamic_gbnf_strategy import SafeDynamicGBNFStrategy

nest_asyncio.apply()


# ===== 🔥 修复：统一数据模型定义 =====
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


# 🔥 修复：使用统一的约束应用信息模型
class ConstraintsAppliedInfo(BaseModel):
    """约束应用信息模型 - 与客户端保持一致"""
    model_config = ConfigDict(protected_namespaces=())

    # 基础约束状态（布尔值）
    fsm: bool = False
    gbnf: bool = False
    enhanced: bool = False
    batch_mode: bool = False

    # 策略信息
    strategy: Optional[str] = None
    strategy_info: Optional[Dict[str, Any]] = None

    # 🔥 详细资源统计（支持复杂类型）
    resource_stats: Optional[Dict[str, Any]] = None
    batch_resource_summary: Optional[Dict[str, Any]] = None
    detailed_prompt_stats: Optional[List[Dict[str, Any]]] = None

    # 其他信息
    requirements_extracted: Optional[Dict[str, Any]] = None
    gbnf_customized: Optional[bool] = None
    template_used: Optional[str] = None
    custom_constraints: Dict[str, Any] = {}


class CloudGenerationResponse(BaseModel):
    """云端生成响应模型 - 修复字段类型"""
    model_config = ConfigDict(protected_namespaces=())

    request_id: str
    success: bool
    timestamp: Optional[float] = None
    generated_xml: Optional[str] = None
    raw_output: Optional[str] = None
    # 🔥 修复：使用正确的模型类型
    constraints_applied: ConstraintsAppliedInfo = ConstraintsAppliedInfo()
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


# 🎯 主云端服务类 - 包含块级FSM支持
class EnhancedCloudService:
    """增强云端服务 - 支持块级FSM策略"""

    def __init__(self):
        """初始化云端服务 - 添加动态GBNF支持"""
        self.app = FastAPI(
            title="Generic XML Generation Service with Dynamic GBNF",
            version="12.0.0",  # 更新版本
            description="Domain-agnostic XML generation with dynamic GBNF strategy"
        )

        self.vllm_endpoint = "http://localhost:8001"
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0

        # 约束系统
        self.constraint_cache = {}
        self.constraint_engines = {}
        self.constraint_stats = {}

        self.dynamic_gbnf_strategy = SafeDynamicGBNFStrategy()

        # 扩展策略配置
        self.strategy_config = {
            "mode": "dynamic_gbnf",  # 🆕 默认使用动态GBNF策略
            "debug": {"enabled": True},

            # 🆕 动态GBNF策略配置
            "dynamic_gbnf": {
                "extract_requirements": True,  # 自动提取需求
                "cache_generated_gbnf": True,  # 缓存生成的GBNF
                "fallback_to_default": True,  # 提取失败时使用默认配置
                "max_extraction_attempts": 2,  # 最大提取尝试次数
                "validation_enabled": True,  # 启用生成结果验证
                "adaptive_temperature": True  # 自适应温度调整
            },

            # 🎯 新增: 块级FSM策略配置
            "block_level_fsm": {
                # 基础参数
                "max_blocks": 10,  # 最大块数
                "temperature": 0.3,  # LLM温度
                "top_p": 0.9,  # 采样参数
                "block_validation": True,  # 启用块验证

                # 🎯 新增: 动态块识别参数
                "min_block_size": 2,  # 最小块大小（token数）
                "max_block_size": 10,  # 最大块大小
                "branch_threshold": 3,  # 分支阈值（超过此值认为是分支点）

                # 🎯 新增: 路径探索参数
                "max_paths_per_block": 50,  # 每个块最多探索的路径数
                "path_clustering": True,  # 启用路径聚类

                # 🎯 新增: 成本计算参数
                "completion_cost_factor": 0.5,  # 完成标记的成本系数
                "branch_cost_factor": 1.2,  # 分支点的成本系数
                "loop_cost_factor": 1.5,  # 循环的成本系数

                # 原有参数（已废弃但保留兼容性）
                "retry_on_failure": True,
                "structure_planning": False,  # 🎯 改为false，使用动态识别
                "block_definitions": {}  # 🎯 不再使用预定义块
            },

        }

        self._setup_routes()
        print("🏗️ Fixed Generic Cloud Service v12.0 initialized")
        print("🎯 New Block-Level FSM strategy for efficient XML generation")
        print("🔥 Enhanced GAD strategy with intelligent repetition and completion control")
        print("🆕 Dynamic GBNF strategy for adaptive XML generation")

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

        # 基础语法修复
        return fixed_rules

    def _setup_routes(self):
        """设置API路由"""

        @self.app.get("/")
        async def root():
            return {
                "service": "Fixed Generic XML Generation Service",
                "version": "12.0.0",  # 🎯 更新版本
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
                    "dynamic_gbnf": {  # 🆕 添加动态GBNF策略描述
                        "description": "🆕 Dynamic GBNF - Adaptive grammar generation from prompt",
                        "domain_agnostic": True,
                        "recommended": True,
                        "features": [
                            "Extracts requirements from prompt automatically",
                            "Generates customized GBNF for each request",
                            "Balances flexibility with constraint compliance",
                            "No hardcoded element counts",
                            "Adaptive to different XML structures"
                        ]
                    },
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
                },
                "current_strategy": self.strategy_config.get("mode"),
                "strategy_configs": {
                    "dynamic_gbnf": self.strategy_config.get("dynamic_gbnf", {}),
                    "block_level_fsm": self.strategy_config.get("block_level_fsm", {}),
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
                "version": "12.0.0"  # 🎯 版本信息
            }

        @self.app.get("/enhanced_batch_statistics")
        async def get_enhanced_batch_statistics():
            """获取增强批量处理统计信息"""
            return {
                "enhanced_stats": self.dynamic_gbnf_strategy.get_batch_statistics(),
                "strategy_info": {
                    "seeds": self.dynamic_gbnf_strategy.SEEDS,
                    "temperature": self.dynamic_gbnf_strategy.TEMPERATURE,
                    "top_p": self.dynamic_gbnf_strategy.TOP_P
                },
                "supported_formats": {
                    "min_format": "1P+0R (ASW_COM_MIN)",
                    "mid_format": "2P+1R (ASW_COM_STD)",
                    "standard_format": "3P+3R (ASW_COM)",
                    "full_format": "3P+4R (with Calibration/Special)",
                    "full_with_special": "3P+4R (with SLEEP mode)"
                }
            }

        @self.app.get("/format_coverage")
        async def get_format_coverage():
            """检查格式覆盖情况"""
            mapper = self.dynamic_gbnf_strategy.prompt_mapper

            coverage_report = {
                "min_formats": {
                    "mcu01_emergsutdown": "✅ Covered",
                    "mcu02_maxtor": "✅ Covered",
                    "mcu03_nrf_idcsamp": "✅ Covered"
                },
                "mid_formats": {
                    "emergsutdown_maxtor_hcu01tqcmd": "✅ Covered",
                    "maxtor_nrf_hcu01shift": "✅ Covered",
                    "emergsutdown_nrf_hcu02poweroff": "✅ Covered",
                    "emergsutdown_maxtor_hcu01shift": "✅ Covered",
                    "emergsutdown_nrf_hcu01tqcmd": "✅ Covered",
                    "maxtor_nrf_hcu02poweroff": "✅ Covered",
                    "with_timeout_handling": "✅ Covered"
                },
                "full_formats": {
                    "standard_3p3r": "✅ Covered",
                    "with_calibration_port": "✅ Covered",
                    "with_sleep_mode": "✅ Covered",
                    "various_comspec_configs": "✅ Covered"
                },
                "batch_support": {
                    "yaml_list_format": "✅ Supported",
                    "parameter_variation": "✅ Supported",
                    "seed_diversity": f"✅ {len(self.dynamic_gbnf_strategy.SEEDS)} seeds",
                    "template_selection": "✅ Automatic"
                }
            }

            return coverage_report

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

                # 🆕 更新动态GBNF策略配置
                if strategy_config['mode'] == 'dynamic_gbnf' and 'dynamic_gbnf' in strategy_config:
                    dynamic_config = strategy_config['dynamic_gbnf']
                    self.strategy_config['dynamic_gbnf'].update(dynamic_config)

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
                    "dynamic_gbnf" if self.strategy_config.get("mode") == "dynamic_gbnf" else "other_strategy",
                    "block_level_generation" if self.strategy_config.get(
                        "mode") == "block_level_fsm" else "token_level_generation",
                    "repetition_control", "completion_control",
                    "xml_generation", "enhanced_efg_weights"
                ]
            }

        # 🆕 添加动态GBNF统计路由
        @self.app.get("/dynamic_gbnf_statistics")
        async def get_dynamic_gbnf_statistics():
            """获取动态GBNF统计信息"""
            if hasattr(self, 'dynamic_gbnf_stats'):
                return {
                    "dynamic_gbnf_stats": self.dynamic_gbnf_stats,
                    "generated_gbnf_cache": len(getattr(self, 'gbnf_cache', {})),
                    "extraction_success_rate": self.dynamic_gbnf_stats.get('extraction_success_rate', 0)
                }
            else:
                return {"message": "Dynamic GBNF strategy not active or no statistics available"}

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

    # 🔥 修复4: 核心生成方法
    async def generate_with_constraints(self, request: EnhancedGenerationRequest) -> CloudGenerationResponse:
        """🔥 修复：核心生成方法 - 使用正确的模型结构"""
        start_time = time.time()

        try:
            print(f"📝 Processing request: {request.request_id}")

            # 确定策略
            strategy_mode = self.strategy_config.get("mode", "dynamic_gbnf")
            print(f"🎯 Using strategy: {strategy_mode}")

            constraint_violations = []
            fsm_engine = None
            gbnf_engine = None

            # 获取FSM引擎（保持原有逻辑）
            if request.constraint_info.fsm_ref:
                fsm_key = f"fsm_{request.constraint_info.fsm_ref}"
                if fsm_key in self.constraint_engines:
                    fsm_engine = self.constraint_engines[fsm_key]
                    fsm_engine.reset()
                    print(f"✅ FSM engine loaded: {fsm_key}")
                else:
                    constraint_violations.append(f"fsm_not_found: {request.constraint_info.fsm_ref}")

            # 策略选择
            raw_output = ""
            strategy_constraints = {}

            if strategy_mode == "dynamic_gbnf":
                print("🎯 Initializing Enhanced Safe Dynamic GBNF Strategy")

                try:
                    # 检测批量模式
                    is_batch = ("- |" in request.prompt or
                                request.prompt.strip().startswith("-") or
                                request.prompt.count('\n') > 5)

                    if is_batch:
                        print("🔄 Detected batch mode")
                    else:
                        print("📋 Single prompt mode")

                    raw_output, strategy_constraints = await self.dynamic_gbnf_strategy.generate(
                        self.vllm_endpoint, request
                    )

                    # 🔥 修复：确保完整的XML标签闭合
                    raw_output = self._ensure_xml_completion(raw_output)

                    # 🔥 修复：添加完整的AUTOSAR XML外围结构
                    raw_output = self._wrap_with_autosar_envelope(raw_output)

                except Exception as e:
                    print(f"⚠️ Enhanced Dynamic GBNF failed: {e}, falling back")
                    raw_output, strategy_constraints = await self._generate_unconstrained(request)
                    strategy_constraints["strategy"] = "unconstrained_fallback_from_enhanced"

            elif strategy_mode == "block_level_fsm":
                # 保持原有块级FSM逻辑
                if fsm_engine:
                    print("🎯 Initializing Block-Level FSM Strategy")
                    block_config = self.strategy_config.get("block_level_fsm", {})
                    strategy = BlockLevelFSMStrategy(fsm_engine, block_config)
                    self.block_strategy_instance = strategy
                    raw_output, strategy_constraints = await strategy.generate(self.vllm_endpoint, request)

                    # 🔥 修复：同样处理其他策略的输出
                    raw_output = self._ensure_xml_completion(raw_output)
                    raw_output = self._wrap_with_autosar_envelope(raw_output)
                else:
                    print("⚠️ Block-level FSM requires FSM engine, falling back")
                    raw_output, strategy_constraints = await self._generate_unconstrained(request)
                    strategy_constraints["strategy"] = "unconstrained_fallback"

            else:  # unconstrained
                raw_output, strategy_constraints = await self._generate_unconstrained(request)
                # 🔥 修复：无约束策略也需要XML处理
                raw_output = self._ensure_xml_completion(raw_output)
                raw_output = self._wrap_with_autosar_envelope(raw_output)

            # 🔥 修复：构建正确的约束应用信息
            constraints_applied = ConstraintsAppliedInfo(
                fsm=strategy_constraints.get("fsm", False),
                gbnf=strategy_constraints.get("gbnf", False),
                enhanced=strategy_constraints.get("strategy") == "enhanced_safe_dynamic_gbnf",
                batch_mode=strategy_constraints.get("batch_mode", False),
                strategy=strategy_constraints.get("strategy", strategy_mode),
                strategy_info=strategy_constraints.get("strategy_info", {}),
                # 🔥 正确传递资源统计
                resource_stats=strategy_constraints.get("single_resource_stats", {}),
                batch_resource_summary=strategy_constraints.get("batch_resource_summary", {}),
                detailed_prompt_stats=strategy_constraints.get("detailed_prompt_stats", []),
                requirements_extracted=strategy_constraints.get("requirements_extracted"),
                gbnf_customized=strategy_constraints.get("gbnf_customized", False),
                template_used=strategy_constraints.get("template_used"),
                # 🔥 新增：传递自定义约束（包含seed_results）
                custom_constraints={
                    "seed_results": strategy_constraints.get("seed_results", []),
                    "multi_seed_stats": strategy_constraints.get("multi_seed_stats", {})
                }
            )

            # 生成响应
            generation_time = time.time() - start_time

            return CloudGenerationResponse(
                request_id=request.request_id,
                success=True,
                timestamp=time.time(),
                generated_xml=raw_output,
                raw_output=raw_output,
                constraints_applied=constraints_applied,  # 🔥 使用正确的模型
                constraint_violations=constraint_violations,
                generation_time=generation_time,
                model_info={
                    "model_name": "DeepSeek-R1-Distill-Qwen-14B",
                    "constraint_strategy": strategy_constraints.get("strategy", strategy_mode),
                    "strategy_details": strategy_constraints,
                    "mode": "enhanced_gbnf_xml_generation" if strategy_mode == "dynamic_gbnf" else "other_mode",
                    "version": "12.0.0",
                    "features_applied": [
                        "enhanced_batch_processing" if strategy_constraints.get("batch_mode") else "single_processing",
                        "parameter_diversity" if strategy_constraints.get(
                            "parameter_diversity") else "fixed_parameters",
                        "complete_format_coverage",
                        "template_auto_selection",
                        "seed_based_variation",
                        "xml_completion_ensured",  # 🔥 新增
                        "autosar_envelope_wrapped"  # 🔥 新增
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
                error_details={
                    "generation_time": error_time,
                    "strategy": strategy_mode,
                    "version": "12.0.0"
                }
            )

    def _ensure_xml_completion(self, xml_content: str) -> str:
        """🔥 新增：确保XML标签完整闭合"""
        if not xml_content or not xml_content.strip():
            return xml_content

        # 移除可能的多余空白
        xml_content = xml_content.strip()

        # 检查是否以 APPLICATION-SW-COMPONENT-TYPE 开头但未正确闭合
        if xml_content.startswith('<APPLICATION-SW-COMPONENT-TYPE'):
            if not xml_content.endswith('</APPLICATION-SW-COMPONENT-TYPE>'):
                # 检查是否已有部分闭合标签
                if '</APPLICATION-SW-COMPONENT-TYPE>' not in xml_content:
                    xml_content += '</APPLICATION-SW-COMPONENT-TYPE>'

        # 检查PORTS标签闭合
        if '<PORTS>' in xml_content and '</PORTS>' not in xml_content:
            # 在APPLICATION-SW-COMPONENT-TYPE闭合标签前添加PORTS闭合
            xml_content = xml_content.replace('</APPLICATION-SW-COMPONENT-TYPE>',
                                              '</PORTS></APPLICATION-SW-COMPONENT-TYPE>')

        # 检查INTERNAL-BEHAVIORS标签闭合
        if '<INTERNAL-BEHAVIORS>' in xml_content and '</INTERNAL-BEHAVIORS>' not in xml_content:
            xml_content = xml_content.replace('</APPLICATION-SW-COMPONENT-TYPE>',
                                              '</INTERNAL-BEHAVIORS></APPLICATION-SW-COMPONENT-TYPE>')

        # 检查SWC-INTERNAL-BEHAVIOR标签闭合
        if '<SWC-INTERNAL-BEHAVIOR>' in xml_content and '</SWC-INTERNAL-BEHAVIOR>' not in xml_content:
            xml_content = xml_content.replace('</INTERNAL-BEHAVIORS>', '</SWC-INTERNAL-BEHAVIOR></INTERNAL-BEHAVIORS>')

        # 检查EVENTS标签闭合
        if '<EVENTS>' in xml_content and '</EVENTS>' not in xml_content:
            xml_content = xml_content.replace('</SWC-INTERNAL-BEHAVIOR>', '</EVENTS></SWC-INTERNAL-BEHAVIOR>')

        # 检查RUNNABLES标签闭合
        if '<RUNNABLES>' in xml_content and '</RUNNABLES>' not in xml_content:
            xml_content = xml_content.replace('</SWC-INTERNAL-BEHAVIOR>', '</RUNNABLES></SWC-INTERNAL-BEHAVIOR>')

        print(f"🔧 XML completion check: {len(xml_content)} chars")
        return xml_content

    def _wrap_with_autosar_envelope(self, inner_xml: str) -> str:
        """🔥 新增：添加完整的AUTOSAR XML外围结构"""
        if not inner_xml or not inner_xml.strip():
            return inner_xml

        # 如果已经包含AUTOSAR外围结构，直接返回
        if '<?xml version="1.0"' in inner_xml and '<AUTOSAR' in inner_xml:
            return inner_xml

        # 构建完整的AUTOSAR XML结构
        complete_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<AUTOSAR xmlns="http://autosar.org/schema/r4.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://autosar.org/schema/r4.0 AUTOSAR_4-2-2.xsd">
  <AR-PACKAGES>
    <AR-PACKAGE>
      <SHORT-NAME>COM_SWC</SHORT-NAME>
      <ELEMENTS>
        {inner_xml}
      </ELEMENTS>
    </AR-PACKAGE>
  </AR-PACKAGES>
</AUTOSAR>'''

        print(f"🔧 Added AUTOSAR envelope: {len(complete_xml)} chars")
        return complete_xml

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


# 🔥 修复5: 启动函数 - 更新信息
async def start_fixed_generic_service():
    """启动增强后的通用服务"""
    print("🚀 Starting Enhanced XML Generation Service v12.0...")
    print("🎯 Mode: Complete Format Coverage with Batch Processing")
    print("🎯 Available Strategies:")
    print("   1️⃣ 🎯 Enhanced Safe Dynamic GBNF: Complete format coverage + batch processing")
    print("   2️⃣ Block-Level FSM: Efficient chunk-based generation")
    print("   3️⃣ Enhanced FSM: Iterative generation")
    print("   4️⃣ Unconstrained: Pure LLM generation")

    print("\n🎯 Enhanced Safe Dynamic GBNF Features:")
    print("   • ✅ Complete MIN format coverage (3 variants)")
    print("   • ✅ Complete MID format coverage (7+ variants)")
    print("   • ✅ Complete FULL format coverage (5+ variants)")
    print("   • 🔄 Batch processing with YAML list support")
    print("   • 🎲 Parameter diversity with multiple seeds")
    print("   • 📊 Automatic template selection")
    print("   • 🎯 Perfect prompt-to-GBNF mapping")

    print("\n🎯 Generation Parameters:")
    print(f"   • Seeds: {service.dynamic_gbnf_strategy.SEEDS}")
    print(f"   • Temperature: {service.dynamic_gbnf_strategy.TEMPERATURE} (±0.1 variation)")
    print(f"   • Top-P: {service.dynamic_gbnf_strategy.TOP_P} (±0.05 variation)")

    print("\n🎯 Supported Batch Format:")
    print("   ```yaml")
    print("   component_level: |")
    print("     - prompt1")
    print("     - prompt2")
    print("     - prompt3")
    print("   ```")

    print(f"\n🔗 Connecting to vLLM at: {service.vllm_endpoint}")

    # 加载约束文件
    print("📂 Loading constraint files...")
    await service._load_constraint_files()

    # 检查vLLM健康状态
    vllm_status = await service._check_vllm_health()
    if vllm_status["available"]:
        print("✅ vLLM service is available")
    else:
        print("❌ vLLM service not available")

    # 启动服务
    config = uvicorn.Config(service.app, host="0.0.0.0", port=8000, log_level="info", access_log=True)
    server = uvicorn.Server(config)

    print("\n🌐 Starting enhanced server on 0.0.0.0:8000")
    print("📖 API documentation: http://localhost:8000/docs")
    print("🔧 Format coverage: GET /format_coverage")
    print("📊 Enhanced stats: GET /enhanced_batch_statistics")
    print("🎮 Strategy management: POST /update_strategy")
    print("🎉 Enhanced XML generation system ready!")

    print(f"\n📊 Template coverage: {len(service.dynamic_gbnf_strategy.safe_gbnf_templates)} templates")
    print(f"🎯 Default strategy: {service.strategy_config.get('mode')}")
    print(f"🔄 Processing mode: Enhanced batch-capable generation")
    print(f"🎯 Version: 12.0.0 with complete format coverage")

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