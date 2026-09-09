#!/usr/bin/env python3
# generic_gad_enhanced_fsm_strategy.py - 完整修复版本

import time
from collections import OrderedDict
from typing import Dict, List, Optional, Tuple, Any

import aiohttp
import numpy as np


# ===== EFG Cache Management =====
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
    """通用的Expected Future Grammaticality估计器"""

    def __init__(self, fsm_engine, gbnf_engine, config: Dict[str, Any]):
        self.fsm_engine = fsm_engine
        self.gbnf_engine = gbnf_engine
        self.config = config

        # 权重配置
        self.efg_weights = config.get('efg_weights', {
            'structural': 0.4,
            'grammatical': 0.4,
            'contextual': 0.2
        })

        # 归一化权重
        total_weight = sum(self.efg_weights.values())
        if total_weight > 0:
            self.efg_weights = {k: v / total_weight for k, v in self.efg_weights.items()}

    def estimate_efg(self, current_path: List[str], candidate_token: str,
                     efg_cache: EFGCache, current_xml: str = "",
                     path_history: Dict = None) -> float:
        """估计Expected Future Grammaticality"""
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
        """评估结构有效性"""
        if not self.fsm_engine:
            return 0.5

        current_state = " ".join(path[:-1]) if len(path) > 1 else ""

        if current_state in self.fsm_engine.transitions:
            allowed = self.fsm_engine.transitions[current_state]
            if candidate in allowed:
                return 1.0

        if candidate.startswith('_COMPLETE_'):
            return 0.8

        return 0.5

    def _evaluate_grammatical_validity(self, path: List[str]) -> float:
        """评估语法有效性"""
        if not path:
            return 1.0

        depth = len(path)

        if depth < 5:
            depth_score = 1.0
        elif depth < 10:
            depth_score = 0.9
        elif depth < 15:
            depth_score = 0.7
        else:
            depth_score = 0.5

        unique_elements = len(set(path))
        balance_score = unique_elements / depth if depth > 0 else 1.0

        return 0.7 * depth_score + 0.3 * balance_score

    def _evaluate_contextual_coherence(self, current_path: List[str],
                                       candidate: str, path_history: Dict) -> float:
        """评估上下文连贯性"""
        score = 1.0

        if not path_history:
            return score

        parent_path = " ".join(current_path) if current_path else "ROOT"
        if parent_path in path_history:
            if candidate in path_history[parent_path]:
                score *= 0.3

        if candidate.startswith('_COMPLETE_'):
            score *= 0.9

        return score


# ===== 修复后的GAD增强FSM策略 =====
class FixedGenericGADEnhancedFSMStrategy:
    """修复后的通用GAD增强FSM策略"""

    def __init__(self, fsm_engine, gbnf_engine, config: Dict[str, Any]):
        """🔥 修复: 添加完整的初始化方法"""
        self.fsm_engine = fsm_engine
        self.gbnf_engine = gbnf_engine
        self.config = config
        self.vllm_endpoint = None

        # 策略参数
        self.efg_threshold = config.get('efg_threshold', 0.25)
        self.max_candidates = config.get('max_candidates', 25)
        self.adaptive_threshold = config.get('adaptive_threshold', True)
        self.temperature_scaling = config.get('temperature_scaling', 0.7)
        self.max_iterations = config.get('max_iterations', 40)

        # 🔥 新增配置支持
        self.repetition_control = config.get('repetition_control', {
            'enabled': True,
            'semantic_analysis': True,
            'default_allow_repetition': True,
            'llm_decision_timeout': 10
        })

        self.completion_control = config.get('completion_control', {
            'min_xml_length': 200,
            'min_depth_reached': 3,
            'require_multiple_elements': True,
            'strict_accepting_states': True
        })

        self.xml_generation = config.get('xml_generation', {
            'element_analysis_enabled': True,
            'content_generation_timeout': 20,
            'attribute_generation_timeout': 15,
            'semantic_content_decision': True
        })

        # 初始化组件
        self.efg_cache = EFGCache(
            max_size=config.get('cache_size', 15000),
            decay_factor=config.get('cache_decay', 0.97)
        )
        self.efg_estimator = GenericEFGEstimator(fsm_engine, gbnf_engine, config)

        # 路径历史记录
        self.path_history = {}

        # 性能统计
        self.performance_stats = {
            'total_requests': 0,
            'successful_generations': 0,
            'avg_generation_time': 0,
            'avg_steps': 0
        }

        print("🔥 FixedGenericGADEnhancedFSMStrategy initialized")
        print(f"   EFG threshold: {self.efg_threshold}")
        print(f"   Max candidates: {self.max_candidates}")
        print(f"   Max iterations: {self.max_iterations}")
        print(f"   Repetition control: {self.repetition_control['enabled']}")
        print(f"   Completion control: {self.completion_control}")

    async def generate(self, vllm_endpoint: str, request) -> Tuple[str, Dict]:
        """修复后的GAD增强生成方法"""
        start_time = time.time()
        self.performance_stats['total_requests'] += 1
        self.vllm_endpoint = vllm_endpoint

        print(f"🎯 Using Fixed Generic GAD Enhanced FSM Strategy")
        print(f"📊 Config: EFG threshold={self.efg_threshold}")

        # 初始化
        generation_path = []
        xml_content = ""
        constraints_applied = {
            "fsm": True,
            "gbnf": True,
            "gad": True,
            "strategy": "fixed_generic_gad_enhanced_fsm"
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

            # 2. 修复：基于prompt的智能重复检测
            if self.repetition_control['enabled']:
                filtered_tokens = await self._intelligent_repetition_filter(
                    fsm_tokens, generation_path, xml_content, request.prompt
                )
            else:
                filtered_tokens = fsm_tokens

            if not filtered_tokens:
                print(f"⚠️ 智能过滤后无可用tokens，使用原始列表")
                filtered_tokens = fsm_tokens

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
                selected_token = max(qualified_tokens.items(), key=lambda x: x[1])[0]
                print(f"⚠️ 降级选择: {selected_token}")

            # 6. 处理选择的token
            if selected_token.startswith("_COMPLETE_"):
                element_to_close = selected_token.replace('_COMPLETE_', '')
                if element_to_close in generation_path:
                    idx = generation_path.index(element_to_close)
                    generation_path = generation_path[:idx]
                print(f"🔄 完成元素: {element_to_close}")
            else:
                # 修复：正确生成XML片段
                xml_fragment = await self._generate_correct_xml_fragment(
                    selected_token, generation_path, xml_content, request.prompt
                )

                if xml_fragment:
                    xml_content += xml_fragment

                    # 更新路径历史
                    parent_path = " ".join(generation_path) if generation_path else "ROOT"
                    if parent_path not in self.path_history:
                        self.path_history[parent_path] = set()
                    self.path_history[parent_path].add(selected_token)

                    # 更新生成路径
                    if not xml_fragment.strip().endswith('/>'):
                        generation_path.append(selected_token)

                    print(f"📝 生成: {xml_fragment.strip()}")

            # 7. 记录迭代
            iteration_log.append({
                "step": step + 1,
                "selected_token": selected_token,
                "efg_score": token_scores.get(selected_token, 0),
                "candidates": len(candidate_tokens),
                "current_path": generation_path.copy()
            })

            # 8. 修复：更严格的完成条件检查
            if self._should_complete_fixed(generation_path, xml_content, step):
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

    async def _intelligent_repetition_filter(self, tokens: List[str], path: List[str],
                                             xml_content: str, base_prompt: str) -> List[str]:
        """修复：基于prompt的智能重复检测"""

        # 🚨 应急修复：检查过度重复
        from collections import Counter
        repetition_counts = Counter(path)
        max_repetition = max(repetition_counts.values()) if repetition_counts else 0

        print(f"🔍 重复检查: 最大重复={max_repetition}, 详情={dict(repetition_counts)}")

        # 🚨 如果任何元素重复超过3次，强制优先选择完成标记
        if max_repetition >= 3:
            print("🚨 检测到过度重复，优先选择完成选项")
            complete_tokens = [t for t in tokens if t.startswith('_COMPLETE_')]
            if complete_tokens:
                print(f"🏁 强制返回完成选项: {complete_tokens}")
                return complete_tokens[:1]  # 只返回一个完成选项

        parent_path = " ".join(path) if path else "ROOT"
        filtered_tokens = []

        for token in tokens:
            # 完成标记总是允许
            if token.startswith('_COMPLETE_'):
                filtered_tokens.append(token)
                continue

            # 🚨 硬限制：任何元素重复不超过2次
            current_count = repetition_counts.get(token, 0)
            if current_count >= 2:
                print(f"🚫 硬限制：{token} 已重复 {current_count} 次，跳过")
                continue

            # 🚨 防止连续重复
            if len(path) >= 1 and path[-1] == token:
                print(f"🚫 防止连续重复: {token}")
                continue

            # 检查是否已经在当前位置生成过
            if parent_path in self.path_history and token in self.path_history[parent_path]:
                if self.repetition_control.get('semantic_analysis', True):
                    should_repeat = await self._should_allow_repetition_semantic(
                        token, path, xml_content, base_prompt
                    )
                    if should_repeat and current_count < 2:  # 🚨 额外检查重复次数
                        filtered_tokens.append(token)
                        print(f"✅ 允许重复元素: {token}")
                    else:
                        print(f"🚫 拒绝重复元素: {token}")
                else:
                    if self.repetition_control.get('default_allow_repetition', True) and current_count < 2:
                        filtered_tokens.append(token)
            else:
                filtered_tokens.append(token)

        # 🚨 如果过滤后没有选项，至少保留完成选项
        if not filtered_tokens:
            complete_tokens = [t for t in tokens if t.startswith('_COMPLETE_')]
            if complete_tokens:
                print("🚨 无可用token，返回完成选项")
                return complete_tokens[:1]

        return filtered_tokens

    async def _should_allow_repetition_semantic(self, token: str, path: List[str],
                                                xml_content: str, base_prompt: str) -> bool:
        """基于XML语义的重复判断"""
        prompt = f"""Based on the XML structure and requirements, should we add another <{token}> element?

Original requirements: {base_prompt[:200]}...

Current XML structure:
{xml_content[-400:] if len(xml_content) > 400 else xml_content}

Current path: {' -> '.join(path[-3:]) if path else 'Root'}

Consider:
1. XML semantics - does this element naturally allow multiple instances?
2. Requirements context - do the requirements suggest multiple elements?
3. Current structure - would another element make sense here?

Answer with YES (allow repetition) or NO (avoid repetition):"""

        try:
            vllm_request = {
                "model": "/model/HuggingFace/deepseek-ai/DeepSeek-R1-Distill-Qwen-14B",
                "prompt": prompt,
                "max_tokens": 10,
                "temperature": 0.1,
                "stream": False
            }

            timeout = self.repetition_control.get('llm_decision_timeout', 10)
            async with aiohttp.ClientSession() as session:
                async with session.post(
                        f"{self.vllm_endpoint}/v1/completions",
                        json=vllm_request,
                        timeout=aiohttp.ClientTimeout(total=timeout)
                ) as resp:
                    if resp.status == 200:
                        response = await resp.json()
                        answer = response["choices"][0]["text"].strip().upper()
                        return "YES" in answer
        except Exception as e:
            print(f"⚠️ 语义重复判断失败: {e}")
            return self.repetition_control.get('default_allow_repetition', True)

        return True

    async def _generate_correct_xml_fragment(self, token: str, path: List[str],
                                             current_xml: str, base_prompt: str) -> str:
        """修复：正确生成XML片段"""
        indent = "  " * len(path)

        # 先确定需要关闭哪些标签
        closing_tags = self._determine_tags_to_close(path, token)
        closing_xml = ""

        for tag in closing_tags:
            tag_indent = "  " * (path.index(tag) if tag in path else 0)
            closing_xml += f"{tag_indent}</{tag}>\n"

        # 询问LLM这个元素的类型和内容
        if self.xml_generation['element_analysis_enabled']:
            element_info = await self._analyze_element_requirements(
                token, path, current_xml, base_prompt
            )
        else:
            # 简化模式
            element_info = self._simple_element_decision(token)

        if element_info['type'] == 'content':
            content = element_info['content']
            attributes = element_info.get('attributes', '')
            return closing_xml + f"{indent}<{token}{attributes}>{content}</{token}>\n"
        elif element_info['type'] == 'self_closing':
            attributes = element_info.get('attributes', '')
            return closing_xml + f"{indent}<{token}{attributes}/>\n"
        else:
            attributes = element_info.get('attributes', '')
            return closing_xml + f"{indent}<{token}{attributes}>\n"

    async def _analyze_element_requirements(self, element: str, path: List[str],
                                            current_xml: str, base_prompt: str) -> Dict:
        """分析元素类型和内容需求"""
        prompt = f"""Analyze the XML element <{element}> in the current context:

Requirements: {base_prompt[:300]}...

Current XML structure:
{current_xml[-300:] if len(current_xml) > 300 else current_xml}

Current position: {' -> '.join(path[-2:]) if path else 'Root'}

Determine:
1. Element type: CONTENT (needs text content), CONTAINER (contains other elements), or SELF_CLOSING (standalone)
2. If CONTENT type, what should the content be?
3. What attributes (if any) should this element have?

Respond in this format:
TYPE: [CONTENT|CONTAINER|SELF_CLOSING]
CONTENT: [content text if TYPE is CONTENT]
ATTRIBUTES: [attributes if any, starting with space]

Response:"""

        try:
            timeout = self.xml_generation.get('content_generation_timeout', 20)
            vllm_request = {
                "model": "/model/HuggingFace/deepseek-ai/DeepSeek-R1-Distill-Qwen-14B",
                "prompt": prompt,
                "max_tokens": 150,
                "temperature": 0.2,
                "stream": False
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                        f"{self.vllm_endpoint}/v1/completions",
                        json=vllm_request,
                        timeout=aiohttp.ClientTimeout(total=timeout)
                ) as resp:
                    if resp.status == 200:
                        response = await resp.json()
                        analysis = response["choices"][0]["text"].strip()
                        return self._parse_element_analysis(analysis, element)

        except Exception as e:
            print(f"⚠️ 元素分析失败: {e}")

        return self._simple_element_decision(element)

    def _simple_element_decision(self, element: str) -> Dict:
        """简化的元素决策"""
        if element in ['SHORT-NAME', 'PERIOD', 'ALIVE-TIMEOUT']:
            return {'type': 'content', 'content': f'Generated_{element}', 'attributes': ''}
        else:
            return {'type': 'container', 'attributes': ''}

    def _parse_element_analysis(self, analysis: str, element: str) -> Dict:
        """解析LLM的元素分析响应"""
        result = {'type': 'container', 'content': '', 'attributes': ''}

        lines = analysis.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('TYPE:'):
                type_value = line.replace('TYPE:', '').strip().upper()
                if type_value in ['CONTENT', 'CONTAINER', 'SELF_CLOSING']:
                    result['type'] = type_value.lower()
            elif line.startswith('CONTENT:'):
                content = line.replace('CONTENT:', '').strip()
                if content:
                    result['content'] = content
            elif line.startswith('ATTRIBUTES:'):
                attrs = line.replace('ATTRIBUTES:', '').strip()
                if attrs and not attrs.startswith(' '):
                    attrs = ' ' + attrs
                result['attributes'] = attrs

        if result['type'] == 'content' and not result['content']:
            result['content'] = f'Generated_{element}'

        return result

    def _should_complete_fixed(self, path: List[str], xml: str, step: int) -> bool:
        """修复：更严格的完成条件判断"""

        # 🚨 应急检查：路径异常长度
        if len(path) > 10:
            print(f"🚨 路径过长 ({len(path)})，强制完成")
            return True

        # 🚨 应急检查：过度重复
        from collections import Counter
        repetition_counts = Counter(path)
        max_repetition = max(repetition_counts.values()) if repetition_counts else 0
        if max_repetition >= 3:
            print(f"🚨 检测到过度重复 (最大: {max_repetition})，强制完成")
            return True

        # 步数限制
        if step >= self.max_iterations - 1:
            print(f"⚠️ 达到最大迭代次数限制")
            return True

        # 只有路径为空且有足够内容时才考虑完成
        if not path and len(xml) > 200:
            print(f"✅ 路径为空且内容充足: {len(xml)} chars")
            return True

        # 检查是否在真正的接受状态（只有根级完成状态）
        state = " ".join(path) if path else ""

        # 修复：只接受真正的完成状态
        accepting_patterns = [
            "_COMPLETE_APPLICATION-SW-COMPONENT-TYPE",
            "APPLICATION-SW-COMPONENT-TYPE _COMPLETE_APPLICATION-SW-COMPONENT-TYPE"
        ]

        if any(pattern in state for pattern in accepting_patterns):
            print(f"✅ 到达接受状态: {state}")
            return True

        # 如果XML内容太少，不应该完成
        if len(xml) < 100:
            return False

        return False

    def _determine_tags_to_close(self, current_path: List[str], new_token: str) -> List[str]:
        """确定需要关闭的标签"""
        if not current_path:
            return []

        current_state = " ".join(current_path)

        if current_state in self.fsm_engine.transitions:
            allowed = self.fsm_engine.transitions[current_state]
            if new_token in allowed:
                return []

        tags_to_close = []
        for i in range(len(current_path) - 1, -1, -1):
            ancestor_path = current_path[:i]
            ancestor_state = " ".join(ancestor_path) if ancestor_path else ""

            if ancestor_state in self.fsm_engine.transitions:
                allowed = self.fsm_engine.transitions[ancestor_state]
                if new_token in allowed:
                    tags_to_close = current_path[i:]
                    break

        return tags_to_close

    def _get_fsm_allowed_tokens(self, path: List[str]) -> List[str]:
        """获取FSM允许的tokens"""
        state = " ".join(path) if path else ""

        if state in self.fsm_engine.transitions:
            return list(self.fsm_engine.transitions[state].keys())

        return self.fsm_engine.get_allowed_tokens(path)

    async def _llm_select_token(self, candidates: List[str], path: List[str],
                                xml_content: str, base_prompt: str) -> str:
        """让LLM从候选中选择最合适的token"""
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
            "model": "/model/HuggingFace/deepseek-ai/DeepSeek-R1-Distill-Qwen-14B",
            "prompt": prompt,
            "max_tokens": 50,
            "temperature": self.config.get('temperature', 0.4),
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

                    for candidate in candidates:
                        if candidate in output.upper():
                            return candidate

                    return candidates[0] if candidates else None
                else:
                    raise Exception(f"vLLM error: {resp.status}")

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

    # !/usr/bin/env python3
    # 防止无限循环的关键修复方法

    # 🔥 修复1: 增强的重复检测 - 添加到 FixedGenericGADEnhancedFSMStrategy 类中

    async def _intelligent_repetition_filter_enhanced(self, tokens: List[str], path: List[str],
                                                      xml_content: str, base_prompt: str) -> List[str]:
        """🔥 增强版智能重复检测 - 防止无限循环"""
        parent_path = " ".join(path) if path else "ROOT"
        filtered_tokens = []

        # 🔥 新增：检测路径中的重复模式
        repetition_counts = self._count_path_repetitions(path)
        max_same_element = max(repetition_counts.values()) if repetition_counts else 0

        print(f"🔍 路径重复分析: 最大重复次数={max_same_element}, 详情={repetition_counts}")

        for token in tokens:
            if token.startswith('_COMPLETE_'):
                # 🔥 完成标记优先级提升 - 如果检测到过度重复，强制优先考虑完成
                if max_same_element >= 3:  # 如果任何元素重复超过3次
                    print(f"🚨 检测到过度重复，优先选择完成标记: {token}")
                    filtered_tokens.insert(0, token)  # 插入到最前面
                else:
                    filtered_tokens.append(token)
                continue

            # 🔥 新增：严格重复限制
            current_repetitions = repetition_counts.get(token, 0)

            # 设置不同元素的重复限制
            max_allowed = self._get_max_repetition_limit(token, path)

            if current_repetitions >= max_allowed:
                print(f"🚫 元素 {token} 重复次数 {current_repetitions} 超过限制 {max_allowed}")
                continue

            # 检查连续重复（防止 A->A->A 模式）
            if len(path) >= 2 and path[-1] == token and path[-2] == token:
                print(f"🚫 阻止连续重复: {token}")
                continue

            # 检查是否已经在当前位置生成过
            if parent_path in self.path_history and token in self.path_history[parent_path]:
                if self.repetition_control['semantic_analysis']:
                    # 🔥 更严格的语义判断
                    should_repeat = await self._should_allow_repetition_semantic_enhanced(
                        token, path, xml_content, base_prompt, current_repetitions
                    )
                    if should_repeat:
                        filtered_tokens.append(token)
                        print(f"✅ 语义允许重复元素: {token} (第{current_repetitions + 1}次)")
                    else:
                        print(f"🚫 语义拒绝重复元素: {token}")
                else:
                    if self.repetition_control['default_allow_repetition'] and current_repetitions < max_allowed:
                        filtered_tokens.append(token)
            else:
                filtered_tokens.append(token)

        # 🔥 新增：如果过度重复且没有完成选项，强制添加完成选项
        if max_same_element >= 5 and not any(t.startswith('_COMPLETE_') for t in filtered_tokens):
            print("🚨 检测到严重重复，强制添加完成选项")
            # 尝试添加当前最深层的完成标记
            if path:
                complete_token = f"_COMPLETE_{path[-1]}"
                filtered_tokens.insert(0, complete_token)

        return filtered_tokens

    def _count_path_repetitions(self, path: List[str]) -> Dict[str, int]:
        """🔥 新增：统计路径中每个元素的重复次数"""
        from collections import Counter
        return Counter(path)

    def _get_max_repetition_limit(self, token: str, path: List[str]) -> int:
        """🔥 新增：获取不同元素的最大重复限制"""
        # 基于元素类型设置不同的重复限制
        if token in ['P-PORT-PROTOTYPE', 'R-PORT-PROTOTYPE']:
            return 5  # 端口可以有多个，但不超过5个
        elif token in ['PORTS', 'INTERNAL-BEHAVIORS']:
            return 1  # 这些容器元素通常只有一个
        elif token in ['SHORT-NAME', 'PERIOD', 'ALIVE-TIMEOUT']:
            return 1  # 这些内容元素通常只有一个
        elif token.startswith('_COMPLETE_'):
            return 1  # 完成标记只能用一次
        else:
            return 3  # 其他元素默认最多3个

    async def _should_allow_repetition_semantic_enhanced(self, token: str, path: List[str],
                                                         xml_content: str, base_prompt: str,
                                                         current_count: int) -> bool:
        """🔥 增强版语义重复判断"""

        # 🔥 硬限制：超过一定次数直接拒绝
        if current_count >= 10:
            print(f"🚨 硬限制：{token} 重复次数 {current_count} 超过绝对限制")
            return False

        # 🔥 特殊检查：如果是容器元素且已经重复多次，很可能有问题
        if token in ['PORTS', 'INTERNAL-BEHAVIORS'] and current_count >= 1:
            print(f"🚫 容器元素 {token} 不应重复")
            return False

        # 构建更明确的prompt
        prompt = f"""CRITICAL: Avoid infinite loops! 

    The element <{token}> has already appeared {current_count} times in the current XML.

    Current XML structure:
    {xml_content[-400:] if len(xml_content) > 400 else xml_content}

    Current path shows: {' -> '.join(path[-5:]) if path else 'Root'}

    Question: Should we add ANOTHER <{token}> element?

    Consider:
    1. Does <{token}> naturally allow multiple instances?
    2. Have we already generated enough <{token}> elements?
    3. Would adding another <{token}> create meaningless repetition?
    4. Should we complete the current structure instead?

    Answer ONLY: YES (allow one more) or NO (stop repetition):"""

        try:
            vllm_request = {
                "model": "/model/HuggingFace/deepseek-ai/DeepSeek-R1-Distill-Qwen-14B",
                "prompt": prompt,
                "max_tokens": 10,
                "temperature": 0.05,  # 🔥 降低温度，更确定的回答
                "stream": False
            }

            timeout = self.repetition_control.get('llm_decision_timeout', 10)
            async with aiohttp.ClientSession() as session:
                async with session.post(
                        f"{self.vllm_endpoint}/v1/completions",
                        json=vllm_request,
                        timeout=aiohttp.ClientTimeout(total=timeout)
                ) as resp:
                    if resp.status == 200:
                        response = await resp.json()
                        answer = response["choices"][0]["text"].strip().upper()
                        result = "YES" in answer
                        print(f"🤖 LLM重复判断: {answer} -> {'允许' if result else '拒绝'}")
                        return result
        except Exception as e:
            print(f"⚠️ 语义重复判断失败: {e}")

        # 🔥 默认策略：如果重复次数过多，倾向于拒绝
        if current_count >= 3:
            print(f"🚫 默认拒绝：{token} 重复次数过多 ({current_count})")
            return False

        return self.repetition_control.get('default_allow_repetition', True)

    # 🔥 修复2: 增强的完成条件检查
    def _should_complete_fixed_enhanced(self, path: List[str], xml: str, step: int) -> bool:
        """🔥 增强版完成条件判断 - 检测异常模式"""

        # 🔥 新增：异常模式检测
        if self._detect_abnormal_patterns(path, xml, step):
            print("🚨 检测到异常模式，强制完成")
            return True

        # 步数限制
        if step >= self.max_iterations - 1:
            print(f"⚠️ 达到最大迭代次数限制")
            return True

        # 检查最小长度
        min_length = self.completion_control.get('min_xml_length', 200)
        if len(xml) < min_length:
            return False

        # 只有路径为空且有足够内容时才考虑完成
        if not path and len(xml) > min_length:
            print(f"✅ 路径为空且内容充足: {len(xml)} chars")
            return True

        # 🔥 新增：如果路径过深，考虑完成
        if len(path) > 10:
            print(f"⚠️ 路径过深 ({len(path)})，考虑完成")
            return True

        # 检查最小深度
        min_depth = self.completion_control.get('min_depth_reached', 3)
        if len(path) < min_depth:
            return False

        # 检查是否在真正的接受状态
        if self.completion_control.get('strict_accepting_states', True):
            state = " ".join(path) if path else ""
            accepting_patterns = [
                "_COMPLETE_APPLICATION-SW-COMPONENT-TYPE",
                "APPLICATION-SW-COMPONENT-TYPE _COMPLETE_APPLICATION-SW-COMPONENT-TYPE"
            ]

            if any(pattern in state for pattern in accepting_patterns):
                print(f"✅ 到达接受状态: {state}")
                return True

        return False

    def _detect_abnormal_patterns(self, path: List[str], xml: str, step: int) -> bool:
        """🔥 新增：检测异常模式"""

        # 检测过度重复
        repetition_counts = self._count_path_repetitions(path)
        max_repetition = max(repetition_counts.values()) if repetition_counts else 0

        if max_repetition >= 5:
            print(f"🚨 异常模式：元素重复次数过多 (最大: {max_repetition})")
            return True

        # 检测路径长度异常
        if len(path) > 20:
            print(f"🚨 异常模式：路径过长 ({len(path)})")
            return True

        # 检测连续重复模式
        if len(path) >= 3:
            last_three = path[-3:]
            if len(set(last_three)) == 1:  # 最后三个元素都相同
                print(f"🚨 异常模式：连续重复 {last_three}")
                return True

        # 检测XML增长停滞
        if step > 10 and len(xml) < step * 50:  # 平均每步应该生成至少50字符
            print(f"🚨 异常模式：XML增长停滞 (步数: {step}, 长度: {len(xml)})")
            return True

        return False

    # 🔥 修复3: 改进的LLM token选择
    async def _llm_select_token_enhanced(self, candidates: List[str], path: List[str],
                                         xml_content: str, base_prompt: str) -> str:
        """🔥 改进的LLM token选择 - 优先考虑完成和避免重复"""

        # 🔥 分析当前状态
        repetition_counts = self._count_path_repetitions(path)
        max_repetition = max(repetition_counts.values()) if repetition_counts else 0

        # 🔥 如果有过度重复，调整候选优先级
        if max_repetition >= 3:
            # 将完成标记移到前面
            complete_tokens = [t for t in candidates if t.startswith('_COMPLETE_')]
            other_tokens = [t for t in candidates if not t.startswith('_COMPLETE_')]
            candidates = complete_tokens + other_tokens
            print(f"🔄 检测到重复，调整候选优先级: {candidates}")

        prompt = f"""{base_prompt}

    IMPORTANT: You are building an XML structure step by step. Avoid infinite loops and meaningless repetition!

    Current XML structure:
    ```xml
    {xml_content[-500:] if len(xml_content) > 500 else xml_content}
    ```

    Current position: {' -> '.join(path[-3:]) if path else 'Starting'}
    Path depth: {len(path)}

    Available choices: {', '.join(candidates)}

    Guidelines:
    1. If you see repeated elements, prefer COMPLETION options
    2. Avoid creating infinite loops
    3. Build meaningful, complete structures
    4. Prefer _COMPLETE_ tokens when appropriate

    Select the ONE element name that best continues the structure:"""

        vllm_request = {
            "model": "/model/HuggingFace/deepseek-ai/DeepSeek-R1-Distill-Qwen-14B",
            "prompt": prompt,
            "max_tokens": 50,
            "temperature": 0.3,  # 🔥 稍微降低温度
            "top_p": 0.8,  # 🔥 降低采样范围
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

                    # 优先匹配完成标记
                    for candidate in candidates:
                        if candidate.startswith('_COMPLETE_') and candidate in output.upper():
                            print(f"🏁 LLM选择了完成标记: {candidate}")
                            return candidate

                    # 然后匹配其他token
                    for candidate in candidates:
                        if candidate in output.upper():
                            return candidate

                    # 如果有过度重复且有完成选项，强制选择完成
                    if max_repetition >= 3:
                        complete_options = [t for t in candidates if t.startswith('_COMPLETE_')]
                        if complete_options:
                            print(f"🚨 强制选择完成选项避免重复: {complete_options[0]}")
                            return complete_options[0]

                    return candidates[0] if candidates else None
                else:
                    raise Exception(f"vLLM error: {resp.status}")


# ===== 原始通用GAD增强FSM策略（保持兼容性） =====
class GenericGADEnhancedFSMStrategy:
    """原始通用GAD增强FSM策略 - 保持向后兼容"""

    def __init__(self, fsm_engine, gbnf_engine, config: Dict[str, Any]):
        self.fsm_engine = fsm_engine
        self.gbnf_engine = gbnf_engine
        self.config = config
        self.vllm_endpoint = None

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
        self.path_history = {}

        # 性能统计
        self.performance_stats = {
            'total_requests': 0,
            'successful_generations': 0,
            'avg_generation_time': 0,
            'avg_steps': 0
        }

    async def generate(self, vllm_endpoint: str, request) -> Tuple[str, Dict]:
        """原始GAD增强生成方法"""
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

    async def _should_allow_repetition(self, token: str, path: List[str], xml_content: str) -> bool:
        """让LLM决定是否允许重复元素"""
        prompt = f"""Given the current XML structure, should we allow adding another <{token}> element?

Current path: {' -> '.join(path[-3:]) if path else 'Root'}

Current XML (last 300 chars):
{xml_content[-300:] if len(xml_content) > 300 else xml_content}

Answer with just YES or NO:"""

        try:
            vllm_request = {
                "model": "/model/HuggingFace/deepseek-ai/DeepSeek-R1-Distill-Qwen-14B",
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
            "model": "/model/HuggingFace/deepseek-ai/DeepSeek-R1-Distill-Qwen-14B",
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
                "model": "/model/HuggingFace/deepseek-ai/DeepSeek-R1-Distill-Qwen-14B",
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
            "model": "/model/HuggingFace/deepseek-ai/DeepSeek-R1-Distill-Qwen-14B",
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
            "model": "/model/HuggingFace/deepseek-ai/DeepSeek-R1-Distill-Qwen-14B",
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