#!/usr/bin/env python3
# generic_gad_enhanced_fsm_strategy.py - 真正通用的实现

import time
import math
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Set
from collections import defaultdict, OrderedDict
import asyncio
import aiohttp
import re


# ===== EFG Cache Management (保持不变) =====
class EFGCache:
    """Expected Future Grammaticality缓存管理器"""

    def __init__(self, max_size: int = 10000, decay_factor: float = 0.95):
        self.max_size = max_size
        self.decay_factor = decay_factor
        self.cache = OrderedDict()
        self.hit_count = 0
        self.miss_count = 0
        self.update_count = 0

    def get(self, path_str: str) -> Optional[Dict[str, float]]:
        if path_str in self.cache:
            self.hit_count += 1
            self.cache.move_to_end(path_str)
            return self.cache[path_str]
        self.miss_count += 1
        return None

    def set(self, path_str: str, estimate: Dict[str, float]):
        if len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)
        self.cache[path_str] = estimate
        self.update_count += 1

    def update(self, path_str: str, was_successful: bool, confidence: float = 0.1):
        if path_str not in self.cache:
            return
        estimate = self.cache[path_str]
        old_score = estimate['efg_score']
        success_delta = 1.0 if was_successful else 0.0
        new_score = (1 - confidence) * old_score + confidence * success_delta
        estimate['efg_score'] = new_score
        estimate['sample_count'] = estimate.get('sample_count', 0) + 1
        estimate['success_count'] = estimate.get('success_count', 0) + (1 if was_successful else 0)
        estimate['confidence'] = min(1.0, estimate.get('confidence', 0.1) + 0.05)

    def decay_all(self):
        for path_str, estimate in self.cache.items():
            estimate['efg_score'] *= self.decay_factor
            estimate['confidence'] *= self.decay_factor

    def get_statistics(self) -> Dict[str, Any]:
        total_requests = self.hit_count + self.miss_count
        hit_rate = self.hit_count / total_requests if total_requests > 0 else 0
        return {
            "cache_size": len(self.cache),
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "hit_rate": hit_rate,
            "update_count": self.update_count,
            "avg_confidence": np.mean([e.get('confidence', 0) for e in self.cache.values()]) if self.cache else 0
        }


# ===== 通用的EFG估计器 =====
class GenericEFGEstimator:
    """通用的Expected Future Grammaticality估计器 - 不依赖特定领域"""

    def __init__(self, fsm_engine, gbnf_engine, config: Dict[str, Any]):
        self.fsm_engine = fsm_engine
        self.gbnf_engine = gbnf_engine
        self.config = config

        # 权重配置 - 更平衡
        self.efg_weights = config.get('efg_weights', {
            'structural': 0.4,  # FSM结构合法性
            'grammatical': 0.4,  # GBNF语法合法性
            'contextual': 0.2  # 上下文连贯性
        })

        # 归一化权重
        total_weight = sum(self.efg_weights.values())
        if total_weight > 0:
            self.efg_weights = {k: v / total_weight for k, v in self.efg_weights.items()}

    def estimate_efg(self, current_path: List[str], candidate_token: str,
                     efg_cache: EFGCache, current_xml: str = "",
                     path_history: Dict = None) -> float:
        """估计Expected Future Grammaticality - 通用版本"""
        full_path = current_path + [candidate_token]
        path_str = " ".join(full_path)

        # 缓存查询
        cached = efg_cache.get(path_str)
        if cached:
            return cached['efg_score']

        # 计算各维度分数
        structural_score = self._evaluate_structural_validity(full_path, candidate_token)
        grammatical_score = self._evaluate_grammatical_validity(full_path)
        contextual_score = self._evaluate_contextual_coherence(current_path, candidate_token, path_history)

        # 加权融合
        efg_score = (
                self.efg_weights['structural'] * structural_score +
                self.efg_weights['grammatical'] * grammatical_score +
                self.efg_weights['contextual'] * contextual_score
        )

        # 缓存结果
        efg_cache.set(path_str, {
            'efg_score': efg_score,
            'structural_score': structural_score,
            'grammatical_score': grammatical_score,
            'contextual_score': contextual_score,
            'timestamp': time.time(),
            'confidence': 0.5
        })

        return efg_score

    def _evaluate_structural_validity(self, path: List[str], candidate: str) -> float:
        """评估结构有效性 - 基于FSM"""
        if not self.fsm_engine:
            return 0.5

        # 检查FSM中是否允许这个转移
        current_state = " ".join(path[:-1]) if len(path) > 1 else ""

        if current_state in self.fsm_engine.transitions:
            allowed = self.fsm_engine.transitions[current_state]
            if candidate in allowed:
                # 完全合法的转移
                return 1.0

        # 检查是否是完成标记
        if candidate.startswith('_COMPLETE_'):
            # 完成标记通常是合理的
            return 0.8

        # 默认给中等分数，让LLM有一定自由度
        return 0.5

    def _evaluate_grammatical_validity(self, path: List[str]) -> float:
        """评估语法有效性 - 基于路径深度和平衡性"""
        if not path:
            return 1.0

        depth = len(path)

        # 深度评分 - 避免过深的嵌套
        if depth < 5:
            depth_score = 1.0
        elif depth < 10:
            depth_score = 0.9
        elif depth < 15:
            depth_score = 0.7
        else:
            depth_score = 0.5

        # 平衡性评分 - 避免路径中重复元素过多
        unique_elements = len(set(path))
        balance_score = unique_elements / depth if depth > 0 else 1.0

        return 0.7 * depth_score + 0.3 * balance_score

    def _evaluate_contextual_coherence(self, current_path: List[str],
                                       candidate: str, path_history: Dict) -> float:
        """评估上下文连贯性 - 不依赖具体元素名称"""
        score = 1.0

        if not path_history:
            return score

        # 检查是否在当前上下文中已经存在
        parent_path = " ".join(current_path) if current_path else "ROOT"
        if parent_path in path_history:
            if candidate in path_history[parent_path]:
                # 重复元素，降低分数
                score *= 0.3

        # 检查是否是返回上级的完成标记
        if candidate.startswith('_COMPLETE_'):
            # 完成标记通常是合理的
            score *= 0.9

        return score


# ===== 通用的GAD增强FSM策略 =====
class GenericGADEnhancedFSMStrategy:
    """通用的Grammar-Aligned Decoding增强FSM策略"""

    def __init__(self, fsm_engine, gbnf_engine, config: Dict[str, Any]):
        self.fsm_engine = fsm_engine
        self.gbnf_engine = gbnf_engine
        self.config = config
        self.vllm_endpoint = None  # 将在generate时设置

        # 策略参数
        self.efg_threshold = config.get('efg_threshold', 0.3)
        self.max_candidates = config.get('max_candidates', 20)
        self.adaptive_threshold = config.get('adaptive_threshold', True)
        self.temperature_scaling = config.get('temperature_scaling', 0.8)
        self.max_iterations = config.get('max_iterations', 50)

        # 初始化组件
        self.efg_cache = EFGCache(
            max_size=config.get('cache_size', 10000),
            decay_factor=config.get('cache_decay', 0.95)
        )
        self.efg_estimator = GenericEFGEstimator(fsm_engine, gbnf_engine, config)

        # 路径历史记录
        self.path_history = {}  # parent_path -> set of children

        # 性能统计
        self.performance_stats = {
            'total_requests': 0,
            'successful_generations': 0,
            'avg_generation_time': 0,
            'avg_steps': 0
        }

    async def generate(self, vllm_endpoint: str, request) -> Tuple[str, Dict]:
        """通用的GAD增强生成方法"""
        start_time = time.time()
        self.performance_stats['total_requests'] += 1
        self.vllm_endpoint = vllm_endpoint

        print(f"🎯 Using Generic GAD Enhanced FSM Strategy")
        print(f"📊 Config: EFG threshold={self.efg_threshold}")

        # 初始化
        generation_path = []
        xml_content = ""
        constraints_applied = {
            "fsm": True,
            "gbnf": True,
            "gad": True,
            "strategy": "generic_gad_enhanced_fsm"
        }
        iteration_log = []

        # 重置状态
        self.path_history = {}
        self.fsm_engine.reset()

        for step in range(self.max_iterations):
            print(f"\n--- GAD步骤 {step + 1}/{self.max_iterations} ---")
            print(f"📍 当前路径: {' -> '.join(generation_path[-3:]) if generation_path else '开始'}")

            # 1. 获取FSM允许的tokens
            fsm_tokens = self._get_fsm_allowed_tokens(generation_path)

            if not fsm_tokens:
                print(f"🛑 FSM无可用tokens，结束生成")
                break

            # 2. 过滤重复（简单规则）
            parent_path = " ".join(generation_path) if generation_path else "ROOT"
            filtered_tokens = []

            for token in fsm_tokens:
                # 完成标记总是允许
                if token.startswith('_COMPLETE_'):
                    filtered_tokens.append(token)
                    continue

                # 检查是否已经在当前位置生成过
                if parent_path in self.path_history and token in self.path_history[parent_path]:
                    # 让LLM决定是否真的需要重复
                    if await self._should_allow_repetition(token, generation_path, xml_content):
                        filtered_tokens.append(token)
                else:
                    filtered_tokens.append(token)

            if not filtered_tokens:
                print(f"⚠️ 所有tokens都被过滤")
                break

            # 3. 计算EFG分数
            token_scores = {}
            candidate_tokens = filtered_tokens[:self.max_candidates]

            for token in candidate_tokens:
                efg_score = self.efg_estimator.estimate_efg(
                    generation_path, token, self.efg_cache,
                    xml_content, self.path_history
                )
                token_scores[token] = efg_score

            # 4. 应用阈值（自适应）
            if self.adaptive_threshold:
                current_threshold = self.efg_threshold * (1 - step / self.max_iterations * 0.5)
            else:
                current_threshold = self.efg_threshold

            qualified_tokens = {k: v for k, v in token_scores.items() if v >= current_threshold}

            if not qualified_tokens:
                # 如果没有通过阈值的，选择得分最高的
                best_token = max(token_scores.items(), key=lambda x: x[1])[0]
                qualified_tokens = {best_token: token_scores[best_token]}

            print(f"📊 候选tokens: {len(candidate_tokens)}, 通过阈值: {len(qualified_tokens)}")

            # 5. 让LLM选择最合适的token
            try:
                selected_token = await self._llm_select_token(
                    list(qualified_tokens.keys()),
                    generation_path,
                    xml_content,
                    request.prompt
                )

                if not selected_token:
                    print(f"❌ LLM未返回有效token")
                    break

                print(f"✅ LLM选择: {selected_token} (EFG={token_scores.get(selected_token, 0):.3f})")

            except Exception as e:
                print(f"❌ LLM调用失败: {e}")
                # 降级：选择EFG最高的
                selected_token = max(qualified_tokens.items(), key=lambda x: x[1])[0]
                print(f"⚠️ 降级选择: {selected_token}")

            # 6. 处理选择的token
            if selected_token.startswith("_COMPLETE_"):
                # 处理完成标记
                element_to_close = selected_token.replace('_COMPLETE_', '')
                if element_to_close in generation_path:
                    idx = generation_path.index(element_to_close)
                    generation_path = generation_path[:idx]
                print(f"🔄 完成元素: {element_to_close}")
            else:
                # 生成XML片段
                xml_fragment = await self._generate_xml_fragment(
                    selected_token, generation_path, xml_content, request.prompt
                )

                if xml_fragment:
                    xml_content += xml_fragment

                    # 更新路径历史
                    if parent_path not in self.path_history:
                        self.path_history[parent_path] = set()
                    self.path_history[parent_path].add(selected_token)

                    # 更新生成路径
                    if not xml_fragment.strip().endswith('/>'):
                        # 非自闭合标签，添加到路径
                        generation_path.append(selected_token)

                    print(f"📝 生成: {xml_fragment.strip()[:80]}...")

            # 7. 记录迭代
            iteration_log.append({
                "step": step + 1,
                "selected_token": selected_token,
                "efg_score": token_scores.get(selected_token, 0),
                "candidates": len(candidate_tokens),
                "current_path": generation_path.copy()
            })

            # 8. 检查完成条件
            if self._should_complete(generation_path, xml_content, step):
                print(f"🏁 满足完成条件")
                break

        # 9. 完成XML结构
        final_xml = self._finalize_xml(xml_content, generation_path)

        # 10. 更新统计
        generation_time = time.time() - start_time
        self._update_performance_stats(generation_time, step + 1, True)

        constraints_applied.update({
            "steps": step + 1,
            "iterations": iteration_log,
            "generation_time": generation_time,
            "efg_cache_stats": self.efg_cache.get_statistics()
        })

        print(f"\n🏁 生成完成: {step + 1}步, {generation_time:.2f}秒")

        return final_xml, constraints_applied

    async def _should_allow_repetition(self, token: str, path: List[str],
                                       xml_content: str) -> bool:
        """让LLM决定是否允许重复元素"""
        prompt = f"""Given the current XML structure, should we allow adding another <{token}> element?

Current path: {' -> '.join(path[-3:]) if path else 'Root'}

Current XML (last 300 chars):
{xml_content[-300:] if len(xml_content) > 300 else xml_content}

Answer with just YES or NO:"""

        try:
            vllm_request = {
                "model": "/model/HuggingFace/deepseek-ai/DeepSeek-R1-Distill-Llama-70B",
                "prompt": prompt,
                "max_tokens": 10,
                "temperature": 0.1,
                "stream": False
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                        f"{self.vllm_endpoint}/v1/completions",
                        json=vllm_request,
                        timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        response = await resp.json()
                        answer = response["choices"][0]["text"].strip().upper()
                        return "YES" in answer
        except:
            # 默认不允许重复
            return False

        return False

    async def _llm_select_token(self, candidates: List[str], path: List[str],
                                xml_content: str, base_prompt: str) -> str:
        """让LLM从候选中选择最合适的token"""
        # 构建选择prompt
        prompt = f"""{base_prompt}

You are building an XML structure step by step. Based on the current context, select the most appropriate next element.

Current XML structure:
```xml
{xml_content[-500:] if len(xml_content) > 500 else xml_content}
```

Current position: {' -> '.join(path[-3:]) if path else 'Starting'}

Available choices: {', '.join(candidates)}

Select the ONE element name that best continues the structure:"""

        vllm_request = {
            "model": "/model/HuggingFace/deepseek-ai/DeepSeek-R1-Distill-Llama-70B",
            "prompt": prompt,
            "max_tokens": 50,
            "temperature": self.config.get('temperature', 0.3),
            "top_p": self.config.get('top_p', 0.9),
            "stream": False,
            "guided_choice": candidates,
            "guided_decoding_backend": "outlines"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                    f"{self.vllm_endpoint}/v1/completions",
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

                    # 如果没找到，返回第一个
                    return candidates[0] if candidates else None
                else:
                    raise Exception(f"vLLM error: {resp.status}")

    async def _generate_xml_fragment(self, token: str, path: List[str],
                                     current_xml: str, base_prompt: str) -> str:
        """生成XML片段 - 完全由LLM决定内容"""
        indent = "  " * len(path)

        # 先确定需要关闭哪些标签
        closing_tags = self._determine_tags_to_close(path, token)
        closing_xml = ""

        for tag in closing_tags:
            tag_indent = "  " * (path.index(tag) if tag in path else 0)
            closing_xml += f"{tag_indent}</{tag}>\n"

        # 询问LLM这个元素是否需要内容
        needs_content = await self._element_needs_content(token, path, current_xml, base_prompt)

        if needs_content:
            # 让LLM生成内容
            content = await self._generate_element_content(token, path, current_xml, base_prompt)

            if content and not content.startswith('<'):
                # 简单内容元素
                return closing_xml + f"{indent}<{token}>{content}</{token}>\n"
            else:
                # 复杂内容或属性
                return closing_xml + f"{indent}<{token}{content}>\n"
        else:
            # 容器元素
            attributes = await self._generate_attributes(token, path, current_xml, base_prompt)
            return closing_xml + f"{indent}<{token}{attributes}>\n"

    async def _element_needs_content(self, element: str, path: List[str],
                                     current_xml: str, base_prompt: str) -> bool:
        """让LLM判断元素是否需要内容"""
        prompt = f"""Based on the context, does the XML element <{element}> need text content or is it a container element?

Context:
- Parent elements: {' -> '.join(path[-2:]) if path else 'Root'}
- Recent XML: 
{current_xml[-200:] if len(current_xml) > 200 else current_xml}

Original requirement: {base_prompt[:200]}...

Answer with: CONTENT (if it needs text content) or CONTAINER (if it contains other elements):"""

        try:
            vllm_request = {
                "model": "/model/HuggingFace/deepseek-ai/DeepSeek-R1-Distill-Llama-70B",
                "prompt": prompt,
                "max_tokens": 20,
                "temperature": 0.1,
                "stream": False
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                        f"{self.vllm_endpoint}/v1/completions",
                        json=vllm_request,
                        timeout=aiohttp.ClientTimeout(total=15)
                ) as resp:
                    if resp.status == 200:
                        response = await resp.json()
                        answer = response["choices"][0]["text"].strip().upper()
                        return "CONTENT" in answer
        except:
            # 默认作为容器
            return False

        return False

    async def _generate_element_content(self, element: str, path: List[str],
                                        current_xml: str, base_prompt: str) -> str:
        """让LLM生成元素内容"""
        prompt = f"""Generate appropriate content for the XML element <{element}>.

Context:
- Parent elements: {' -> '.join(path[-2:]) if path else 'Root'}
- Current XML structure:
{current_xml[-300:] if len(current_xml) > 300 else current_xml}

Requirements from original prompt: {base_prompt[:300]}...

Generate ONLY the content text (no XML tags). If the element needs attributes, include them.
Content:"""

        vllm_request = {
            "model": "/model/HuggingFace/deepseek-ai/DeepSeek-R1-Distill-Llama-70B",
            "prompt": prompt,
            "max_tokens": 100,
            "temperature": 0.3,
            "stream": False,
            "stop": ["<", "\n\n"]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                    f"{self.vllm_endpoint}/v1/completions",
                    json=vllm_request,
                    timeout=aiohttp.ClientTimeout(total=20)
            ) as resp:
                if resp.status == 200:
                    response = await resp.json()
                    content = response["choices"][0]["text"].strip()
                    return content
                else:
                    return f"Generated_{element}"

    async def _generate_attributes(self, element: str, path: List[str],
                                   current_xml: str, base_prompt: str) -> str:
        """让LLM决定元素是否需要属性"""
        prompt = f"""Does the XML element <{element}> need any attributes? If yes, generate them.

Context:
- Parent elements: {' -> '.join(path[-2:]) if path else 'Root'}
- Requirements: {base_prompt[:200]}...

Reply with ONLY the attributes (including the leading space) or empty string if no attributes needed.
Example responses: ' id="123"' or ' type="example"' or ''

Attributes:"""

        vllm_request = {
            "model": "/model/HuggingFace/deepseek-ai/DeepSeek-R1-Distill-Llama-70B",
            "prompt": prompt,
            "max_tokens": 50,
            "temperature": 0.2,
            "stream": False,
            "stop": [">", "\n"]
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                        f"{self.vllm_endpoint}/v1/completions",
                        json=vllm_request,
                        timeout=aiohttp.ClientTimeout(total=15)
                ) as resp:
                    if resp.status == 200:
                        response = await resp.json()
                        attributes = response["choices"][0]["text"].strip()
                        # 确保属性格式正确
                        if attributes and not attributes.startswith(' '):
                            attributes = ' ' + attributes
                        return attributes
        except:
            pass

        return ""

    def _determine_tags_to_close(self, current_path: List[str], new_token: str) -> List[str]:
        """确定需要关闭的标签"""
        if not current_path:
            return []

        # 基于FSM状态判断
        current_state = " ".join(current_path)

        if current_state in self.fsm_engine.transitions:
            allowed = self.fsm_engine.transitions[current_state]
            if new_token in allowed:
                return []  # 可以直接添加

        # 需要关闭一些标签
        tags_to_close = []

        # 从当前路径向上查找可以容纳new_token的位置
        for i in range(len(current_path) - 1, -1, -1):
            ancestor_path = current_path[:i]
            ancestor_state = " ".join(ancestor_path) if ancestor_path else ""

            if ancestor_state in self.fsm_engine.transitions:
                allowed = self.fsm_engine.transitions[ancestor_state]
                if new_token in allowed:
                    # 找到了可以容纳的位置
                    tags_to_close = current_path[i:]
                    break

        return tags_to_close

    def _get_fsm_allowed_tokens(self, path: List[str]) -> List[str]:
        """获取FSM允许的tokens"""
        state = " ".join(path) if path else ""

        if state in self.fsm_engine.transitions:
            return list(self.fsm_engine.transitions[state].keys())

        # 尝试模糊匹配
        return self.fsm_engine.get_allowed_tokens(path)

    def _should_complete(self, path: List[str], xml: str, step: int) -> bool:
        """判断是否应该完成生成"""
        # 步数限制
        if step >= self.max_iterations - 1:
            return True

        # 路径为空（回到根）且有内容
        if not path and len(xml) > 100:
            return True

        # 让FSM判断是否在接受状态
        state = " ".join(path) if path else ""
        if state in self.fsm_engine.accepting_states:
            return True

        return False

    def _finalize_xml(self, xml_content: str, path: List[str]) -> str:
        """完成XML结构"""
        # 关闭所有未关闭的标签
        closing_tags = []

        for i in range(len(path) - 1, -1, -1):
            tag = path[i]
            indent = "  " * i
            closing_tags.append(f"{indent}</{tag}>")

        if closing_tags:
            xml_content += "\n".join(closing_tags) + "\n"

        return xml_content.strip()

    def _update_performance_stats(self, generation_time: float, steps: int, success: bool):
        """更新性能统计"""
        if success:
            self.performance_stats['successful_generations'] += 1

        n = self.performance_stats['total_requests']
        old_avg_time = self.performance_stats['avg_generation_time']
        old_avg_steps = self.performance_stats['avg_steps']

        self.performance_stats['avg_generation_time'] = (old_avg_time * (n - 1) + generation_time) / n
        self.performance_stats['avg_steps'] = (old_avg_steps * (n - 1) + steps) / n

    def get_statistics(self) -> Dict[str, Any]:
        """获取策略统计信息"""
        return {
            **self.performance_stats,
            "efg_cache_stats": self.efg_cache.get_statistics(),
            "success_rate": self.performance_stats['successful_generations'] /
                            self.performance_stats['total_requests']
            if self.performance_stats['total_requests'] > 0 else 0
        }