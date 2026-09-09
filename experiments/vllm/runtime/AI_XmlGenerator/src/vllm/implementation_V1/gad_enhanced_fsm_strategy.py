#!/usr/bin/env python3
# gad_enhanced_fsm_strategy_fixed_v3.py - 修复SHORT-NAME循环和内容生成

import re
import time
from collections import defaultdict, OrderedDict
from typing import Dict, List, Optional, Tuple, Any, Set

import aiohttp
import numpy as np


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


# ===== Dynamic EFG Estimator (改进版) =====
class DynamicEFGEstimator:
    """动态Expected Future Grammaticality估计器"""

    def __init__(self, fsm_engine, gbnf_engine, config: Dict[str, Any]):
        self.fsm_engine = fsm_engine
        self.gbnf_engine = gbnf_engine
        self.config = config

        # 🔥 调整权重分配
        self.efg_weights = config.get('efg_weights', {
            'gbnf': 0.3,  # 降低GBNF权重
            'complexity': 0.3,
            'structural': 0.4  # 提高结构权重
        })

        # 确保权重归一化
        total_weight = sum(self.efg_weights.values())
        if total_weight > 0:
            self.efg_weights = {k: v / total_weight for k, v in self.efg_weights.items()}

        # 从示例XML学习
        self.learned_patterns = self._extract_patterns_from_prompt(config.get('prompt_config'))
        self.learned_element_counts = self._extract_element_counts_from_example()
        self.learned_values = self._extract_values_from_example()  # 🔥 新增：学习具体值

    def _extract_values_from_example(self) -> Dict[str, List[str]]:
        """从示例中提取具体的值"""
        values = {
            'port_names': [],
            'interface_refs': [],
            'data_elements': [],
            'component_name': 'ASW_COM'
        }

        if not self.config.get('prompt_config'):
            return values

        prompt = self.config['prompt_config'].get('component_level', '')

        # 提取组件名
        comp_match = re.search(r'<SHORT-NAME>(\w+)</SHORT-NAME>.*?</APP', prompt, re.DOTALL)
        if comp_match:
            values['component_name'] = comp_match.group(1)

        # 提取所有端口名
        values['port_names'] = re.findall(r'<SHORT-NAME>([PR]Port_[^<]+)</SHORT-NAME>', prompt)

        # 提取接口引用
        values['interface_refs'] = re.findall(r'>(\/COM_Interface\/SR_Interface_[^<]+)<', prompt)

        # 提取数据元素
        values['data_elements'] = re.findall(r'>(\/COM_Interface\/[^/]+\/[^<]+)<', prompt)

        print(f"📚 学习到的值: 组件名={values['component_name']}, " +
              f"端口数={len(values['port_names'])}, " +
              f"接口数={len(values['interface_refs'])}")

        return values

    def estimate_efg(self, current_path: List[str], candidate_token: str,
                     efg_cache: EFGCache, current_xml: str = "",
                     generated_elements: Dict[str, Set[str]] = None,
                     element_counts: Dict[str, int] = None) -> float:
        """估计Expected Future Grammaticality"""
        full_path = current_path + [candidate_token]
        path_str = " ".join(full_path)

        # 缓存查询
        cached = efg_cache.get(path_str)
        if cached:
            return cached['efg_score']

        # 多维度评估
        gbnf_score = self._evaluate_gbnf_grammaticality(full_path, current_xml)
        complexity_score = self._evaluate_complexity_penalty(full_path, generated_elements, element_counts)
        structural_score = self._evaluate_structural_completeness(full_path, current_xml, generated_elements)

        # 🔥 改进的重复惩罚
        repetition_penalty = self._evaluate_repetition_penalty_v2(
            current_path, candidate_token, generated_elements, element_counts
        )

        # 示例一致性（降低权重）
        example_score = self._evaluate_example_consistency(current_path, candidate_token, element_counts)
        example_score = 0.8 + 0.2 * example_score  # 限制在0.8-1.0范围

        # 加权融合
        efg_score = (
                            self.efg_weights['gbnf'] * gbnf_score +
                            self.efg_weights['complexity'] * complexity_score +
                            self.efg_weights['structural'] * structural_score
                    ) * repetition_penalty * example_score

        # 缓存更新
        efg_cache.set(path_str, {
            'efg_score': efg_score,
            'gbnf_score': gbnf_score,
            'complexity_score': complexity_score,
            'structural_score': structural_score,
            'example_score': example_score,
            'repetition_penalty': repetition_penalty,
            'timestamp': time.time(),
            'confidence': 0.5
        })

        return efg_score

    def _evaluate_repetition_penalty_v2(self, current_path: List[str], candidate_token: str,
                                        generated_elements: Dict[str, Set[str]],
                                        element_counts: Dict[str, int]) -> float:
        """改进的重复惩罚 - 更严格"""
        if not generated_elements or not current_path:
            return 1.0

        parent = current_path[-1] if current_path else ""

        # 🔥 对于内容元素，检查是否已经在当前父元素下生成过
        unique_content_elements = {
            'SHORT-NAME', 'PROVIDED-INTERFACE-TREF', 'REQUIRED-INTERFACE-TREF',
            'SYMBOL', 'PERIOD', 'ALIVE-TIMEOUT', 'HANDLE-TIMEOUT-TYPE',
            'DATA-ELEMENT-REF', 'SD', 'GID'
        }

        if candidate_token in unique_content_elements:
            if parent in generated_elements and candidate_token in generated_elements[parent]:
                print(f"   ❌ {candidate_token}已在{parent}下生成，严重惩罚")
                return 0.01  # 几乎不可能被选中

        # 对于容器元素的唯一性检查
        unique_containers = {'PORTS', 'INTERNAL-BEHAVIORS', 'EVENTS', 'RUNNABLES',
                             'REQUIRED-COM-SPECS', 'ADMIN-DATA', 'SDGS'}

        if candidate_token in unique_containers:
            if parent in generated_elements and candidate_token in generated_elements[parent]:
                return 0.01

        # 可重复元素的处理
        if candidate_token in ['P-PORT-PROTOTYPE', 'R-PORT-PROTOTYPE', 'VARIABLE-ACCESS']:
            current_count = element_counts.get(candidate_token, 0) if element_counts else 0
            expected_count = self.learned_element_counts.get(candidate_token, 3)

            if current_count < expected_count:
                return 1.0  # 不惩罚
            else:
                # 超过期望数量后快速降低
                return 0.3 / (current_count - expected_count + 1)

        return 1.0

    def _evaluate_example_consistency(self, current_path: List[str], candidate_token: str,
                                      element_counts: Dict[str, int]) -> float:
        """评估与示例的一致性"""
        if not self.learned_element_counts:
            return 1.0

        score = 1.0

        if candidate_token in self.learned_element_counts:
            expected_count = self.learned_element_counts[candidate_token]
            current_count = element_counts.get(candidate_token, 0) if element_counts else 0

            if expected_count > 0:
                if current_count < expected_count:
                    score = 1.1  # 轻微鼓励
                elif current_count == expected_count:
                    score = 1.0
                else:
                    score = 0.7  # 轻微惩罚

        return score

    def _evaluate_gbnf_grammaticality(self, path: List[str], current_xml: str) -> float:
        """评估GBNF语法正确性"""
        if not self.gbnf_engine or not self.gbnf_engine.is_valid:
            return 0.5

        depth = len(path)
        if depth < 3:
            depth_score = 1.0
        elif depth < 8:
            depth_score = 0.9
        elif depth < 15:
            depth_score = 0.7
        else:
            depth_score = 0.5

        # 基于学习的模式评分
        pattern_score = 1.0
        if self.learned_patterns and path:
            current_element = path[-1]
            parent = path[-2] if len(path) > 1 else ""

            if parent in self.learned_patterns.get('parent_child_map', {}):
                expected_children = self.learned_patterns['parent_child_map'][parent]
                if current_element in expected_children:
                    pattern_score = 1.1  # 轻微奖励
                else:
                    pattern_score = 0.9

        return depth_score * pattern_score

    def _evaluate_complexity_penalty(self, path: List[str], generated_elements: Dict[str, Set[str]],
                                     element_counts: Dict[str, int]) -> float:
        """评估复杂度惩罚"""
        path_length = len(path)

        # 长度评分
        if path_length < 3:
            length_score = 1.0
        elif path_length < 10:
            length_score = 0.9
        elif path_length < 20:
            length_score = 0.7
        else:
            length_score = 0.5

        # 循环检测
        cycle_penalty = 1.0
        if path_length >= 4:
            recent_4 = path[-4:]
            unique_recent = len(set(recent_4))
            if unique_recent <= 2:
                cycle_penalty = 0.2
            elif unique_recent == 3:
                cycle_penalty = 0.6

        return length_score * cycle_penalty

    def _evaluate_structural_completeness(self, path: List[str], current_xml: str,
                                          generated_elements: Dict[str, Set[str]]) -> float:
        """评估结构完整性"""
        score = 1.0

        # 必需的结构元素
        required_elements = {
            'APPLICATION-SW-COMPONENT-TYPE': ['SHORT-NAME', 'PORTS', 'INTERNAL-BEHAVIORS'],
            'PORTS': ['P-PORT-PROTOTYPE', 'R-PORT-PROTOTYPE'],
            'P-PORT-PROTOTYPE': ['SHORT-NAME', 'PROVIDED-INTERFACE-TREF'],
            'R-PORT-PROTOTYPE': ['SHORT-NAME', 'REQUIRED-COM-SPECS', 'REQUIRED-INTERFACE-TREF'],
            'REQUIRED-COM-SPECS': ['NONQUEUED-RECEIVER-COM-SPEC'],
            'NONQUEUED-RECEIVER-COM-SPEC': ['DATA-ELEMENT-REF', 'ALIVE-TIMEOUT', 'HANDLE-TIMEOUT-TYPE'],
            'INTERNAL-BEHAVIORS': ['SWC-INTERNAL-BEHAVIOR'],
            'SWC-INTERNAL-BEHAVIOR': ['SHORT-NAME', 'EVENTS', 'RUNNABLES']
        }

        if path:
            current_element = path[-1]
            parent = path[-2] if len(path) > 1 else None

            if parent in required_elements:
                required_children = required_elements[parent]
                if generated_elements and parent in generated_elements:
                    already_generated = generated_elements[parent]
                    missing = [elem for elem in required_children if elem not in already_generated]

                    if current_element in missing:
                        score *= 1.3  # 奖励补全缺失的必需元素

        return min(1.0, score)

    def _extract_patterns_from_prompt(self, prompt_config) -> Dict[str, Any]:
        """从提示词中的示例XML提取模式"""
        if not prompt_config:
            return {}

        patterns = {
            'parent_child_map': {},
            'element_order': {},
            'unique_elements': set()
        }

        example_xml = prompt_config.get('example_xml', '')
        if not example_xml:
            component_prompt = prompt_config.get('component_level', '')
            import re
            xml_match = re.search(r'<[A-Z\-]+>.*?</[A-Z\-]+>', component_prompt, re.DOTALL)
            if xml_match:
                example_xml = xml_match.group(0)

        if example_xml:
            lines = example_xml.split('\n')
            parent_stack = []
            parent_children_order = defaultdict(list)

            for line in lines:
                line = line.strip()
                if line.startswith('<') and not line.startswith('</') and not '<!--' in line:
                    tag_match = re.match(r'<([A-Z][A-Z0-9\-_]*)', line)
                    if tag_match:
                        tag = tag_match.group(1)
                        tag = tag.replace('_', '-')
                        if tag == 'APP-SW-COMPONENT-TYPE':
                            tag = 'APPLICATION-SW-COMPONENT-TYPE'
                        elif tag == 'PORT':
                            tag = 'PORTS'

                        if parent_stack:
                            parent = parent_stack[-1]
                            if parent not in patterns['parent_child_map']:
                                patterns['parent_child_map'][parent] = set()
                            patterns['parent_child_map'][parent].add(tag)
                            parent_children_order[parent].append(tag)

                        if not line.endswith('/>') and '</' not in line:
                            parent_stack.append(tag)

                elif line.startswith('</'):
                    if parent_stack:
                        parent_stack.pop()

            # 处理元素顺序
            for parent, children in parent_children_order.items():
                seen = set()
                ordered = []
                for child in children:
                    if child not in seen:
                        seen.add(child)
                        ordered.append(child)
                patterns['element_order'][parent] = ordered

        return patterns

    def _extract_element_counts_from_example(self) -> Dict[str, int]:
        """从示例XML中提取元素数量"""
        if not self.config.get('prompt_config'):
            return {}

        prompt = self.config['prompt_config'].get('component_level', '')

        counts = {
            'P-PORT-PROTOTYPE': len(re.findall(r'<P[-_]PORT-PROTOTYPE', prompt, re.IGNORECASE)),
            'R-PORT-PROTOTYPE': len(re.findall(r'<R[-_]PORT-PROTOTYPE', prompt, re.IGNORECASE)),
            'TIMING-EVENT': len(re.findall(r'<TIMING-EVENT', prompt, re.IGNORECASE)),
            'RUNNABLE-ENTITY': len(re.findall(r'<RUNNABLE-ENTITY', prompt, re.IGNORECASE)),
            'VARIABLE-ACCESS': len(re.findall(r'<VARIABLE-ACCESS', prompt, re.IGNORECASE))
        }

        print(f"📊 从示例学习的元素数量: {counts}")
        return counts


# ===== GAD Enhanced FSM Strategy (修复版v3) =====
class GADEnhancedFSMStrategy:
    """Grammar-Aligned Decoding增强的FSM策略 - 修复循环和内容生成"""

    def __init__(self, fsm_engine, gbnf_engine, config: Dict[str, Any]):
        self.fsm_engine = fsm_engine
        self.gbnf_engine = gbnf_engine
        self.config = config

        # 策略参数
        self.efg_threshold = config.get('efg_threshold', 0.3)
        self.max_candidates = config.get('max_candidates', 20)
        self.adaptive_threshold = config.get('adaptive_threshold', True)
        self.temperature_scaling = config.get('temperature_scaling', 0.8)
        self.fusion_strategy = config.get('fusion_strategy', 'multiplicative')
        self.max_iterations = config.get('max_iterations', 30)

        # 初始化组件
        cache_size = config.get('cache_size', 10000)
        cache_decay = config.get('cache_decay', 0.95)
        self.efg_cache = EFGCache(max_size=cache_size, decay_factor=cache_decay)
        self.efg_estimator = DynamicEFGEstimator(fsm_engine, gbnf_engine, config)

        # 性能监控
        self.performance_stats = {
            'total_requests': 0,
            'successful_generations': 0,
            'avg_generation_time': 0,
            'avg_steps': 0,
            'efg_cache_stats': {}
        }

        # 内容元素定义
        self.content_elements = {
            'SHORT-NAME', 'PROVIDED-INTERFACE-TREF', 'REQUIRED-INTERFACE-TREF',
            'DATA-ELEMENT-REF', 'PORT-PROTOTYPE-REF', 'TARGET-DATA-PROTOTYPE-REF',
            'START-ON-EVENT-REF', 'PERIOD', 'ALIVE-TIMEOUT', 'HANDLE-TIMEOUT-TYPE',
            'SYMBOL', 'SD', 'GID'
        }

        # 🔥 修复：使用更精确的跟踪结构
        self.generated_elements = {}  # parent_path -> set of children
        self.element_counts = defaultdict(int)

        # 🔥 新增：端口索引跟踪
        self.port_index = {
            'P-PORT-PROTOTYPE': 0,
            'R-PORT-PROTOTYPE': 0,
            'VARIABLE-ACCESS': 0
        }

        # 从示例学习
        self.learned_structure = self._learn_from_example()

    def _learn_from_example(self) -> Dict[str, Any]:
        """从示例XML学习预期结构和值"""
        learned = {
            'component_name': 'ASW_COM',
            'port_data': {},  # 端口名 -> 相关数据
            'expected_counts': {},
            'element_values': defaultdict(list)
        }

        if self.config.get('prompt_config'):
            prompt = self.config['prompt_config'].get('component_level', '')

            # 提取组件名
            comp_match = re.search(r'<SHORT-NAME>(\w+)</SHORT-NAME>', prompt)
            if comp_match:
                learned['component_name'] = comp_match.group(1)

            # 提取端口数据（端口名和对应的接口）
            port_pattern = r'<([PR][-_]PORT-PROTOTYPE)[^>]*>.*?<SHORT-NAME>([^<]+)</SHORT-NAME>.*?<(?:PROVIDED|REQUIRED)-INTERFACE-TREF[^>]*>([^<]+)</(?:PROVIDED|REQUIRED)-INTERFACE-TREF>.*?</\1>'

            for match in re.finditer(port_pattern, prompt, re.DOTALL):
                port_type = match.group(1).replace('_', '-')
                port_name = match.group(2)
                interface_ref = match.group(3)

                learned['port_data'][port_name] = {
                    'type': port_type,
                    'interface': interface_ref
                }

                # 收集所有端口名
                key = 'p_ports' if 'P-PORT' in port_type else 'r_ports'
                if key not in learned['element_values']:
                    learned['element_values'][key] = []
                learned['element_values'][key].append(port_name)

            # 提取其他值
            learned['element_values']['timing_events'] = re.findall(
                r'<TIMING-EVENT[^>]*>.*?<SHORT-NAME>([^<]+)</SHORT-NAME>', prompt, re.DOTALL)
            learned['element_values']['runnables'] = re.findall(
                r'<RUNNABLE-ENTITY[^>]*>.*?<SHORT-NAME>([^<]+)</SHORT-NAME>', prompt, re.DOTALL)
            learned['element_values']['variable_accesses'] = re.findall(
                r'<VARIABLE-ACCESS[^>]*>.*?<SHORT-NAME>([^<]+)</SHORT-NAME>', prompt, re.DOTALL)

            print(f"📚 学习到的结构: 组件名={learned['component_name']}, " +
                  f"端口数据={len(learned['port_data'])}个")

        return learned

    async def generate(self, vllm_endpoint: str, request) -> Tuple[str, Dict]:
        """GAD增强的生成方法"""
        start_time = time.time()
        self.performance_stats['total_requests'] += 1

        print(f"🎯 Using GAD Enhanced FSM Strategy (Fixed v3)")
        print(f"📊 Config: EFG threshold={self.efg_threshold}, Fusion={self.fusion_strategy}")

        # 初始化
        generation_path = []
        xml_content = ""
        constraints_applied = {
            "fsm": True,
            "gbnf": True,
            "gad": True,
            "strategy": "gad_enhanced_fsm_fixed_v3"
        }
        iteration_log = []

        # 重置跟踪器
        self.generated_elements = {}
        self.element_counts = defaultdict(int)
        self.port_index = {'P-PORT-PROTOTYPE': 0, 'R-PORT-PROTOTYPE': 0, 'VARIABLE-ACCESS': 0}

        # 重置FSM引擎
        self.fsm_engine.reset()

        # 提取提示词配置
        prompt_config = self._extract_prompt_config(request)
        if prompt_config:
            self.config['prompt_config'] = prompt_config
            self.efg_estimator = DynamicEFGEstimator(self.fsm_engine, self.gbnf_engine, self.config)
            self.learned_structure = self._learn_from_example()

        for step in range(self.max_iterations):
            print(f"\n--- GAD步骤 {step + 1}/{self.max_iterations} ---")
            print(f"📍 当前路径: {' -> '.join(generation_path[-3:]) if generation_path else '开始'}")
            print(f"📊 元素统计: P-PORT={self.element_counts.get('P-PORT-PROTOTYPE', 0)}, " +
                  f"R-PORT={self.element_counts.get('R-PORT-PROTOTYPE', 0)}")

            # 1. 获取FSM允许的tokens
            fsm_state = " ".join(generation_path)
            fsm_tokens = self._get_fsm_allowed_tokens(fsm_state)

            if not fsm_tokens:
                print(f"🛑 FSM无可用tokens，结束生成")
                break

            # 2. 智能过滤和排序
            filtered_tokens = self._smart_filter_and_sort_tokens_v2(
                fsm_tokens, generation_path, xml_content
            )

            if not filtered_tokens:
                print(f"⚠️ 所有tokens都被过滤，尝试完成")
                break

            # 3. 计算GAD权重
            token_weights = {}
            efg_scores = {}

            candidate_tokens = filtered_tokens[:self.max_candidates]

            for token in candidate_tokens:
                # 🔥 使用路径字符串作为父元素标识
                parent_path = " ".join(generation_path) if generation_path else "ROOT"

                efg_score = self.efg_estimator.estimate_efg(
                    generation_path, token, self.efg_cache, xml_content,
                    self.generated_elements, self.element_counts
                )
                efg_scores[token] = efg_score

                # 应用EFG阈值
                if self.adaptive_threshold:
                    current_threshold = self.efg_threshold * (1 - step / self.max_iterations * 0.5)
                else:
                    current_threshold = self.efg_threshold

                if efg_score >= current_threshold:
                    token_weights[token] = efg_score

            if not token_weights:
                best_token = max(efg_scores.items(), key=lambda x: x[1])[0]
                token_weights = {best_token: efg_scores[best_token]}
                print(f"⚠️ 无token通过EFG阈值，选择最佳: {best_token} (EFG={efg_scores[best_token]:.3f})")

            print(f"📊 候选tokens: {len(candidate_tokens)}, 通过EFG: {len(token_weights)}")
            print(f"🎯 Top candidates: {list(token_weights.keys())[:5]}")

            # 4. 使用vLLM进行选择
            try:
                selected_token = await self._vllm_guided_selection(
                    vllm_endpoint, request, xml_content, generation_path,
                    list(token_weights.keys()), token_weights, step
                )

                if not selected_token:
                    print(f"❌ vLLM未返回有效token")
                    break

                print(f"✅ GAD选择: {selected_token} (EFG={efg_scores.get(selected_token, 0):.3f})")

            except Exception as e:
                print(f"❌ vLLM调用失败: {e}")
                selected_token = max(token_weights.items(), key=lambda x: x[1])[0]
                print(f"⚠️ 降级选择: {selected_token}")

            # 5. 处理选择的token
            if selected_token.startswith("_COMPLETE_"):
                print(f"🔄 处理完成标记: {selected_token}")
                generation_path = self._handle_complete_token(generation_path, selected_token)
            else:
                # 生成XML片段
                xml_fragment, path_updated = self._generate_xml_fragment_v2(
                    selected_token, generation_path, step, xml_content
                )

                if xml_fragment:
                    xml_content += xml_fragment
                    generation_path = path_updated

                    # 更新元素计数
                    if selected_token not in self.content_elements:
                        self.element_counts[selected_token] += 1

                    print(f"📝 生成片段: {xml_fragment.strip()[:80]}...")
                else:
                    print(f"⚠️ 未生成XML片段")

            # 6. 记录迭代信息
            iteration_log.append({
                "step": step + 1,
                "selected_token": selected_token,
                "efg_score": efg_scores.get(selected_token, 0),
                "candidates": len(candidate_tokens),
                "passed_threshold": len(token_weights),
                "current_path": generation_path.copy(),
                "element_counts": dict(self.element_counts)
            })

            # 7. 检查完成条件
            if self._should_complete(generation_path, xml_content, step):
                print(f"🏁 满足完成条件")
                break

        # 8. 完成XML结构
        final_xml = self._finalize_xml(xml_content, generation_path)

        # 9. 更新统计
        generation_time = time.time() - start_time
        self._update_performance_stats(generation_time, step + 1, True)

        constraints_applied.update({
            "steps": step + 1,
            "final_path": generation_path,
            "iterations": iteration_log,
            "generation_time": generation_time,
            "efg_cache_stats": self.efg_cache.get_statistics(),
            "generated_elements": {k: list(v) for k, v in self.generated_elements.items()},
            "element_counts": dict(self.element_counts)
        })

        print(f"\n🏁 GAD生成完成:")
        print(f"   步骤数: {step + 1}")
        print(f"   生成时间: {generation_time:.2f}s")

        return final_xml, constraints_applied

    def _smart_filter_and_sort_tokens_v2(self, tokens: List[str], path: List[str], xml: str) -> List[str]:
        """智能过滤和排序 - 修复版"""
        filtered = []

        # 🔥 构建父路径字符串
        parent_path = " ".join(path) if path else "ROOT"

        for token in tokens:
            # 完成标记
            if token.startswith('_COMPLETE_'):
                if self._can_complete_element(token, path, xml):
                    filtered.append(token)
                continue

            # 🔥 检查是否已经生成过（使用路径字符串）
            if token in self.content_elements:
                if parent_path in self.generated_elements and token in self.generated_elements[parent_path]:
                    print(f"   ❌ {token}已在当前位置生成，跳过")
                    continue

            # 检查唯一容器元素
            unique_containers = {'PORTS', 'INTERNAL-BEHAVIORS', 'EVENTS', 'RUNNABLES',
                                 'REQUIRED-COM-SPECS', 'ADMIN-DATA', 'SDGS'}
            if token in unique_containers:
                if parent_path in self.generated_elements and token in self.generated_elements[parent_path]:
                    continue

            filtered.append(token)

        # 🔥 基于当前状态的智能排序
        if not path:
            return self._prioritize_tokens(filtered, ['SHORT-NAME', 'APPLICATION-SW-COMPONENT-TYPE'])

        current = path[-1] if path else ""

        # 组件级排序
        if current == 'APPLICATION-SW-COMPONENT-TYPE':
            generated = self.generated_elements.get(parent_path, set())
            if 'SHORT-NAME' not in generated:
                return self._prioritize_tokens(filtered, ['SHORT-NAME'])
            elif 'PORTS' not in generated:
                return self._prioritize_tokens(filtered, ['PORTS'])
            elif 'INTERNAL-BEHAVIORS' not in generated:
                return self._prioritize_tokens(filtered, ['INTERNAL-BEHAVIORS'])

        # PORTS内排序
        elif current == 'PORTS':
            p_count = self.element_counts.get('P-PORT-PROTOTYPE', 0)
            r_count = self.element_counts.get('R-PORT-PROTOTYPE', 0)

            # 基于示例的预期数量
            expected_p = len(self.learned_structure.get('element_values', {}).get('p_ports', []))
            expected_r = len(self.learned_structure.get('element_values', {}).get('r_ports', []))

            if expected_p == 0:
                expected_p = 3
            if expected_r == 0:
                expected_r = 3

            # 平衡生成
            if p_count == 0:
                return self._prioritize_tokens(filtered, ['P-PORT-PROTOTYPE'])
            elif r_count == 0:
                return self._prioritize_tokens(filtered, ['R-PORT-PROTOTYPE'])
            elif p_count < expected_p and p_count <= r_count:
                return self._prioritize_tokens(filtered, ['P-PORT-PROTOTYPE'])
            elif r_count < expected_r:
                return self._prioritize_tokens(filtered, ['R-PORT-PROTOTYPE'])
            else:
                return self._prioritize_tokens(filtered, ['_COMPLETE_PORTS', 'INTERNAL-BEHAVIORS'])

        # 端口内部排序
        elif current in ['P-PORT-PROTOTYPE', 'R-PORT-PROTOTYPE']:
            generated = self.generated_elements.get(parent_path, set())
            if 'SHORT-NAME' not in generated:
                return self._prioritize_tokens(filtered, ['SHORT-NAME'])
            elif current == 'P-PORT-PROTOTYPE' and 'PROVIDED-INTERFACE-TREF' not in generated:
                return self._prioritize_tokens(filtered, ['PROVIDED-INTERFACE-TREF'])
            elif current == 'R-PORT-PROTOTYPE':
                if 'REQUIRED-COM-SPECS' not in generated:
                    return self._prioritize_tokens(filtered, ['REQUIRED-COM-SPECS'])
                elif 'REQUIRED-INTERFACE-TREF' not in generated:
                    return self._prioritize_tokens(filtered, ['REQUIRED-INTERFACE-TREF'])

        # NONQUEUED-RECEIVER-COM-SPEC内部排序
        elif current == 'NONQUEUED-RECEIVER-COM-SPEC':
            generated = self.generated_elements.get(parent_path, set())
            order = ['DATA-ELEMENT-REF', 'ALIVE-TIMEOUT', 'HANDLE-TIMEOUT-TYPE']
            for elem in order:
                if elem not in generated and elem in filtered:
                    return self._prioritize_tokens(filtered, [elem])

        return filtered

    def _generate_xml_fragment_v2(self, token: str, path: List[str], step: int,
                                  current_xml: str) -> Tuple[str, List[str]]:
        """生成XML片段 - 修复版"""
        indent = "  " * len(path)
        new_path = path.copy()

        # 🔥 记录生成的元素（使用路径字符串）
        parent_path = " ".join(path) if path else "ROOT"
        if parent_path not in self.generated_elements:
            self.generated_elements[parent_path] = set()
        self.generated_elements[parent_path].add(token)

        # 确定需要关闭的标签
        tags_to_close = self._determine_tags_to_close(path, token)
        closing_xml = ""

        for tag in reversed(tags_to_close):
            if tag in new_path:
                depth = new_path.index(tag)
                closing_xml += "  " * depth + f"</{tag}>\n"
                new_path = new_path[:depth]

        xml_fragment = closing_xml

        # 生成新元素
        indent = "  " * len(new_path)

        if token in self.content_elements:
            # 🔥 内容元素 - 使用示例中的实际值
            content = self._generate_content_from_example(token, new_path, step, current_xml)
            xml_fragment += f"{indent}<{token}>{content}</{token}>\n"
            # 内容元素不改变路径
        else:
            # 容器元素
            attrs = self._generate_attributes(token, step)
            if attrs:
                xml_fragment += f'{indent}<{token}{attrs}>\n'
            else:
                xml_fragment += f"{indent}<{token}>\n"
            new_path.append(token)

        return xml_fragment, new_path

    def _generate_content_from_example(self, element: str, path: List[str], step: int,
                                       current_xml: str) -> str:
        """从示例生成内容 - 使用实际值"""
        parent = path[-1] if path else ""

        if element == "SHORT-NAME":
            # 根据上下文生成合适的名称
            if parent == "APPLICATION-SW-COMPONENT-TYPE":
                return self.learned_structure.get('component_name', 'ASW_COM')

            elif parent == "P-PORT-PROTOTYPE":
                p_ports = self.learned_structure.get('element_values', {}).get('p_ports', [])
                idx = self.port_index['P-PORT-PROTOTYPE']
                if idx < len(p_ports):
                    self.port_index['P-PORT-PROTOTYPE'] += 1
                    return p_ports[idx]
                else:
                    return f"PPort_Provider_{idx + 1:02d}"

            elif parent == "R-PORT-PROTOTYPE":
                r_ports = self.learned_structure.get('element_values', {}).get('r_ports', [])
                idx = self.port_index['R-PORT-PROTOTYPE']
                if idx < len(r_ports):
                    self.port_index['R-PORT-PROTOTYPE'] += 1
                    return r_ports[idx]
                else:
                    return f"RPort_Receiver_{idx + 1:02d}"

            elif parent == "SWC-INTERNAL-BEHAVIOR":
                return "SwcInternalBehavior"

            elif parent == "TIMING-EVENT":
                events = self.learned_structure.get('element_values', {}).get('timing_events', [])
                return events[0] if events else "TE_SWC_COM_10ms"

            elif parent == "RUNNABLE-ENTITY":
                runnables = self.learned_structure.get('element_values', {}).get('runnables', [])
                return runnables[0] if runnables else "RE_COM_SWC"

            elif parent == "VARIABLE-ACCESS":
                va_list = self.learned_structure.get('element_values', {}).get('variable_accesses', [])
                idx = self.port_index['VARIABLE-ACCESS']
                if idx < len(va_list):
                    self.port_index['VARIABLE-ACCESS'] += 1
                    return va_list[idx]
                else:
                    if "DATA-RECEIVE-POINT-BY-ARGUMENTS" in path:
                        return f"DRPA_Data_{idx:02d}"
                    else:
                        return f"DSP_Data_{idx:02d}"

        elif element == "PROVIDED-INTERFACE-TREF":
            # 从当前端口名获取对应的接口
            port_name = self._get_current_port_name(current_xml)
            port_data = self.learned_structure.get('port_data', {}).get(port_name)
            if port_data and 'interface' in port_data:
                return port_data['interface']
            else:
                # 基于端口名生成
                suffix = self._extract_interface_suffix(port_name)
                return f' DEST="SENDER-RECEIVER-INTERFACE">/COM_Interface/SR_Interface_{suffix}'

        elif element == "REQUIRED-INTERFACE-TREF":
            # 从当前端口名获取对应的接口
            port_name = self._get_current_port_name(current_xml)
            port_data = self.learned_structure.get('port_data', {}).get(port_name)
            if port_data and 'interface' in port_data:
                return port_data['interface']
            else:
                suffix = self._extract_interface_suffix(port_name)
                return f' DEST="SENDER-RECEIVER-INTERFACE">/COM_Interface/SR_Interface_{suffix}'

        elif element == "DATA-ELEMENT-REF":
            # 基于R-PORT的接口生成
            interface_match = re.search(r'/COM_Interface/(SR_Interface_[^<"]+)', current_xml)
            if interface_match:
                interface_name = interface_match.group(1)
                # 从接口名提取数据元素名
                data_element = self._extract_data_element_from_interface(interface_name)
                return f' DEST="VARIABLE-DATA-PROTOTYPE">/COM_Interface/{interface_name}/{data_element}'
            else:
                return ' DEST="VARIABLE-DATA-PROTOTYPE">/COM_Interface/SR_Interface_Data/DataElement'

        elif element == "PERIOD":
            return "0.01"
        elif element == "ALIVE-TIMEOUT":
            return "0.3"
        elif element == "HANDLE-TIMEOUT-TYPE":
            return "NONE"
        elif element == "SYMBOL":
            runnable_match = re.search(r'<RUNNABLE-ENTITY[^>]*>.*?<SHORT-NAME>([^<]+)</SHORT-NAME>',
                                       current_xml, re.DOTALL)
            if runnable_match:
                return f"{runnable_match.group(1)}_func"
            return "RE_Main_func"
        elif element == "GID":
            return "Master"
        elif element == "SD":
            return "true"
        elif element == "PORT-PROTOTYPE-REF":
            # 基于上下文确定端口类型和引用
            if "DATA-RECEIVE" in " ".join(path):
                # 找到合适的R-PORT引用
                port_match = re.search(r'<R-PORT-PROTOTYPE[^>]*>.*?<SHORT-NAME>([^<]+)</SHORT-NAME>',
                                       current_xml, re.DOTALL)
                if port_match:
                    port_name = port_match.group(1)
                    return f' DEST="R-PORT-PROTOTYPE">/COM_SWC/{self.learned_structure.get("component_name", "ASW_COM")}/{port_name}'
            else:
                # P-PORT引用
                port_match = re.search(r'<P-PORT-PROTOTYPE[^>]*>.*?<SHORT-NAME>([^<]+)</SHORT-NAME>',
                                       current_xml, re.DOTALL)
                if port_match:
                    port_name = port_match.group(1)
                    return f' DEST="P-PORT-PROTOTYPE">/COM_SWC/{self.learned_structure.get("component_name", "ASW_COM")}/{port_name}'
            return ' DEST="PORT-PROTOTYPE">/Components/Component/Port'

        elif element == "TARGET-DATA-PROTOTYPE-REF":
            # 使用与PORT-PROTOTYPE-REF相同的接口
            interface_match = re.search(r'<PORT-PROTOTYPE-REF[^>]*>/[^/]+/[^/]+/(RPort_[^<]+)</PORT-PROTOTYPE-REF>',
                                        current_xml)
            if interface_match:
                port_name = interface_match.group(1)
                # 从端口名推断接口和数据元素
                suffix = self._extract_interface_suffix(port_name)
                data_element = self._extract_data_element_from_interface(f"SR_Interface_{suffix}")
                return f' DEST="VARIABLE-DATA-PROTOTYPE">/COM_Interface/SR_Interface_{suffix}/{data_element}'
            return ' DEST="VARIABLE-DATA-PROTOTYPE">/Interfaces/Data'

        elif element == "START-ON-EVENT-REF":
            runnable_match = re.search(r'<RUNNABLE-ENTITY[^>]*>.*?<SHORT-NAME>([^<]+)</SHORT-NAME>',
                                       current_xml, re.DOTALL)
            if runnable_match:
                runnable_name = runnable_match.group(1)
                return f' DEST="RUNNABLE-ENTITY">/COM_SWC/{self.learned_structure.get("component_name", "ASW_COM")}/SwcInternalBehavior/{runnable_name}'
            return ' DEST="RUNNABLE-ENTITY">/Components/Component/Behavior/Runnable'

        else:
            return f"Generated_{element}_{step:02d}"

    def _get_current_port_name(self, xml: str) -> str:
        """获取当前端口名称"""
        # 查找最近的未关闭的端口
        p_port_match = re.findall(
            r'<P-PORT-PROTOTYPE[^>]*>(?:(?!</P-PORT-PROTOTYPE>).)*?<SHORT-NAME>([^<]+)</SHORT-NAME>',
            xml, re.DOTALL)
        r_port_match = re.findall(
            r'<R-PORT-PROTOTYPE[^>]*>(?:(?!</R-PORT-PROTOTYPE>).)*?<SHORT-NAME>([^<]+)</SHORT-NAME>',
            xml, re.DOTALL)

        all_ports = p_port_match + r_port_match
        return all_ports[-1] if all_ports else "Port_Default"

    def _extract_interface_suffix(self, port_name: str) -> str:
        """从端口名称提取接口后缀"""
        # PPort_MCU01_EmergShutDown -> MCU01_EmergShutDown
        parts = port_name.split('_', 1)
        return parts[1] if len(parts) > 1 else "Default"

    def _extract_data_element_from_interface(self, interface_name: str) -> str:
        """从接口名称推断数据元素名称"""
        # SR_Interface_HCU01_TqCmd -> HCU01_Tq_Cmd
        suffix = interface_name.replace('SR_Interface_', '')

        # 在驼峰命名中插入下划线
        # HCU01TqCmd -> HCU01_Tq_Cmd
        result = re.sub(r'([0-9])([A-Z])', r'\1_\2', suffix)
        result = re.sub(r'([a-z])([A-Z])', r'\1_\2', result)

        return result

    def _prioritize_tokens(self, tokens: List[str], priorities: List[str]) -> List[str]:
        """将优先的tokens放在前面"""
        priority_tokens = [t for t in priorities if t in tokens]
        other_tokens = [t for t in tokens if t not in priorities]
        return priority_tokens + other_tokens

    def _can_complete_element(self, complete_token: str, path: List[str], xml: str) -> bool:
        """检查是否可以完成某个元素"""
        element = complete_token.replace('_COMPLETE_', '')

        if element == 'PORTS':
            p_count = self.element_counts.get('P-PORT-PROTOTYPE', 0)
            r_count = self.element_counts.get('R-PORT-PROTOTYPE', 0)
            return p_count >= 1 and r_count >= 1

        return True

    def _handle_complete_token(self, path: List[str], complete_token: str) -> List[str]:
        """处理完成标记"""
        element_to_complete = complete_token.replace('_COMPLETE_', '')

        if element_to_complete in path:
            idx = path.index(element_to_complete)
            return path[:idx]

        return path

    def _determine_tags_to_close(self, current_path: List[str], new_token: str) -> List[str]:
        """确定需要关闭的标签"""
        if not current_path or new_token.startswith('_COMPLETE_'):
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

    def _generate_attributes(self, token: str, step: int) -> str:
        """生成元素属性"""
        if token in ['P-PORT-PROTOTYPE', 'R-PORT-PROTOTYPE', 'TIMING-EVENT',
                     'RUNNABLE-ENTITY', 'VARIABLE-ACCESS']:
            import uuid
            return f' UUID="{str(uuid.uuid4())}"'
        elif token == 'SDG':
            return ' GID="Master"'
        return ""

    def _should_complete(self, path: List[str], xml: str, step: int) -> bool:
        """判断是否应该完成生成"""
        if step >= self.max_iterations - 1:
            return True

        # 检查基本结构
        has_component = "<APPLICATION-SW-COMPONENT-TYPE" in xml
        has_name = "<SHORT-NAME>" in xml and "</SHORT-NAME>" in xml
        has_ports = "<PORTS>" in xml and "</PORTS>" in xml
        has_behaviors = "<INTERNAL-BEHAVIORS>" in xml

        if has_component and has_name and has_ports:
            p_count = self.element_counts.get('P-PORT-PROTOTYPE', 0)
            r_count = self.element_counts.get('R-PORT-PROTOTYPE', 0)

            # 使用学习的预期数量
            expected_p = len(self.learned_structure.get('element_values', {}).get('p_ports', []))
            expected_r = len(self.learned_structure.get('element_values', {}).get('r_ports', []))

            if expected_p == 0:
                expected_p = 3
            if expected_r == 0:
                expected_r = 3

            # 如果端口数量接近预期
            if p_count >= min(expected_p, 3) and r_count >= min(expected_r, 3):
                if has_behaviors and "</INTERNAL-BEHAVIORS>" in xml:
                    return True

        # 如果路径为空且有完整结构
        if not path and has_component and has_name and has_ports and has_behaviors:
            return True

        return False

    def _finalize_xml(self, xml_content: str, path: List[str]) -> str:
        """完成XML结构"""
        closing_tags = []

        for i in range(len(path) - 1, -1, -1):
            tag = path[i]
            if tag not in self.content_elements:
                indent = "  " * i
                closing_tags.append(f"{indent}</{tag}>")

        if closing_tags:
            xml_content += "\n".join(closing_tags) + "\n"

        if "<APPLICATION-SW-COMPONENT-TYPE" in xml_content and \
                "</APPLICATION-SW-COMPONENT-TYPE>" not in xml_content:
            xml_content += "</APPLICATION-SW-COMPONENT-TYPE>\n"

        return xml_content.strip()

    # ===== 辅助方法 =====

    async def _vllm_guided_selection(self, vllm_endpoint: str, request,
                                     current_xml: str, generation_path: List[str],
                                     candidate_tokens: List[str], token_weights: Dict[str, float],
                                     step: int) -> str:
        """使用vLLM进行GAD引导的选择"""
        prompt = self._build_gad_prompt(request.prompt, current_xml, generation_path,
                                        candidate_tokens, token_weights)

        vllm_request = {
            "model": "/model/HuggingFace/deepseek-ai/DeepSeek-R1-Distill-Qwen-14B",
            "prompt": prompt,
            "max_tokens": 20,
            "temperature": request.temperature * self.temperature_scaling,
            "top_p": request.top_p,
            "stream": False,
            "guided_choice": candidate_tokens,
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
                    vllm_output = response["choices"][0]["text"].strip()
                    selected = self._extract_token_from_output(vllm_output, candidate_tokens)

                    if self.fusion_strategy == "multiplicative":
                        if token_weights.get(selected, 0) < 0.3:
                            best_efg_token = max(token_weights.items(), key=lambda x: x[1])[0]
                            if token_weights[best_efg_token] > token_weights.get(selected, 0) * 2:
                                print(f"🔄 GAD override: {selected} -> {best_efg_token}")
                                selected = best_efg_token

                    return selected
                else:
                    raise Exception(f"vLLM error: {resp.status}")

    def _build_gad_prompt(self, base_prompt: str, current_xml: str,
                          generation_path: List[str], candidates: List[str],
                          token_weights: Dict[str, float]) -> str:
        """构建GAD感知的提示词"""
        efg_info = []
        for token in candidates[:10]:
            efg = token_weights.get(token, 0)
            efg_info.append(f"{token} (EFG={efg:.2f})")

        needs = []
        if generation_path:
            parent = generation_path[-1]
            parent_path = " ".join(generation_path)

            if parent_path in self.generated_elements:
                generated = self.generated_elements[parent_path]

                if parent == "APPLICATION-SW-COMPONENT-TYPE":
                    if "SHORT-NAME" not in generated:
                        needs.append("Component needs SHORT-NAME first")
                    elif "PORTS" not in generated:
                        needs.append("Component needs PORTS section")
                    elif "INTERNAL-BEHAVIORS" not in generated:
                        needs.append("Component needs INTERNAL-BEHAVIORS")

                elif parent == "PORTS":
                    p_count = self.element_counts.get('P-PORT-PROTOTYPE', 0)
                    r_count = self.element_counts.get('R-PORT-PROTOTYPE', 0)
                    if p_count == 0:
                        needs.append("Need P-PORT-PROTOTYPE")
                    elif r_count == 0:
                        needs.append("Need R-PORT-PROTOTYPE")

        needs_str = " | ".join(needs) if needs else "Continue building structure"

        prompt = f"""{base_prompt}

Current XML structure:
```xml
{current_xml if current_xml else "<APPLICATION-SW-COMPONENT-TYPE>"}
```

Current position: {' -> '.join(generation_path[-3:]) if generation_path else 'Starting'}
Current needs: {needs_str}

Available choices with scores:
{', '.join(efg_info)}

Select the element that best follows the example structure and avoids repetition.
Select ONE element name:"""

        return prompt

    def _extract_token_from_output(self, output: str, candidates: List[str]) -> str:
        """从vLLM输出中提取token"""
        cleaned = output.strip().upper().replace('<', '').replace('>', '').replace('/', '')

        if cleaned in candidates:
            return cleaned

        for token in candidates:
            if token in cleaned or cleaned in token:
                return token

        return candidates[0] if candidates else None

    def _get_fsm_allowed_tokens(self, fsm_state: str) -> List[str]:
        """从FSM获取允许的tokens"""
        if fsm_state in self.fsm_engine.transitions:
            return list(self.fsm_engine.transitions[fsm_state].keys())

        tokens = self.fsm_engine.get_allowed_tokens(fsm_state.split() if fsm_state else [])
        return tokens if tokens else []

    def _extract_prompt_config(self, request) -> Optional[Dict[str, Any]]:
        """从请求中提取提示词配置"""
        if hasattr(request, 'autosar_context') and request.autosar_context:
            return request.autosar_context.get('prompt_config')

        if hasattr(request, 'prompt') and len(request.prompt) > 1000:
            return {'component_level': request.prompt}

        return None

    def _update_performance_stats(self, generation_time: float, steps: int, success: bool):
        """更新性能统计"""
        if success:
            self.performance_stats['successful_generations'] += 1

        n = self.performance_stats['total_requests']
        old_avg_time = self.performance_stats['avg_generation_time']
        old_avg_steps = self.performance_stats['avg_steps']

        self.performance_stats['avg_generation_time'] = (old_avg_time * (n - 1) + generation_time) / n
        self.performance_stats['avg_steps'] = (old_avg_steps * (n - 1) + steps) / n
        self.performance_stats['efg_cache_stats'] = self.efg_cache.get_statistics()

    def get_statistics(self) -> Dict[str, Any]:
        """获取策略统计信息"""
        return {
            **self.performance_stats,
            "success_rate": self.performance_stats['successful_generations'] / \
                            self.performance_stats['total_requests']
            if self.performance_stats['total_requests'] > 0 else 0
        }

    def export_efg_cache(self, filepath: str):
        """导出EFG缓存供分析"""
        import json
        cache_data = {
            "metadata": {
                "export_time": time.time(),
                "cache_size": len(self.efg_cache.cache),
                "statistics": self.efg_cache.get_statistics()
            },
            "cache_entries": dict(self.efg_cache.cache)
        }

        with open(filepath, 'w') as f:
            json.dump(cache_data, f, indent=2)

        print(f"📁 EFG cache exported to {filepath}")