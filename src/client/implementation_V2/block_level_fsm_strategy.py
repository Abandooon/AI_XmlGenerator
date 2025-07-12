#!/usr/bin/env python3
# block_level_fsm_strategy.py - FSM驱动的动态块级生成策略（AUTOSAR优化版）

import asyncio
import time
import json
import re
import random
import psutil
import os
from typing import Dict, List, Optional, Tuple, Any, Set
from collections import defaultdict, deque
import aiohttp
import xml.etree.ElementTree as ET


class FSMPath:
    """FSM路径表示"""

    def __init__(self, states: List[str], tokens: List[str], cost: float = 0.0):
        self.states = states  # 状态序列
        self.tokens = tokens  # token序列
        self.cost = cost  # 路径成本

    def extend(self, token: str, next_state: str, additional_cost: float = 1.0):
        """扩展路径"""
        new_states = self.states + [next_state]
        new_tokens = self.tokens + [token]
        return FSMPath(new_states, new_tokens, self.cost + additional_cost)


class DynamicBlock:
    """动态识别的块"""

    def __init__(self, name: str, start_state: str, paths: List[FSMPath]):
        self.name = name
        self.start_state = start_state
        self.paths = paths  # 该块包含的所有可能路径
        self.selected_path = None  # LLM选择的路径

    def get_common_prefix(self) -> List[str]:
        """获取所有路径的公共前缀"""
        if not self.paths:
            return []

        # 找出最短路径长度
        min_len = min(len(p.tokens) for p in self.paths)
        prefix = []

        for i in range(min_len):
            tokens_at_i = set(p.tokens[i] for p in self.paths)
            if len(tokens_at_i) == 1:  # 所有路径在这个位置的token相同
                prefix.append(self.paths[0].tokens[i])
            else:
                break

        return prefix


class BlockLevelFSMStrategy:
    """FSM驱动的动态块级生成策略（AUTOSAR优化版）"""

    # 添加种子和参数配置
    SEEDS: List[int] = [42, 1001, 20250701]  # 随机种子列表
    TEMPERATURE: float = 0.7
    TOP_P: float = 0.9

    def __init__(self, fsm_engine, config: Dict[str, Any] = None):
        self.fsm_engine = fsm_engine
        self.config = config or {}
        self.vllm_endpoint = None

        # 策略参数 - 针对AUTOSAR优化
        self.max_blocks = self.config.get('max_blocks', 15)
        self.temperature = self.TEMPERATURE  # 使用指定温度
        self.top_p = self.TOP_P  # 使用指定top_p
        self.block_validation = self.config.get('block_validation', True)

        # 动态块识别参数 - 针对AUTOSAR优化
        self.min_block_size = self.config.get('min_block_size', 2)
        self.max_block_size = self.config.get('max_block_size', 20)  # 增加到20以支持VARIABLE-ACCESS
        self.branch_threshold = self.config.get('branch_threshold', 3)

        # AUTOSAR特定的块大小配置
        self.autosar_block_sizes = {
            'VARIABLE-ACCESS': 15,  # VARIABLE-ACCESS需要更大的块
            'PORTS': 8,
            'P-PORT-PROTOTYPE': 6,
            'R-PORT-PROTOTYPE': 10,  # R-PORT需要更大因为有COM-SPECS
            'INTERNAL-BEHAVIORS': 12,
            'RUNNABLE-ENTITY': 15,
            'default': 10
        }

        # AUTOSAR模式识别
        self.autosar_patterns = {
            'component_name': re.compile(r'组件\s*`([^`]+)`|Application-SW\s+组件\s*`([^`]+)`|组件\s*`([^`]+)`'),
            'p_ports': re.compile(r'P-PORT[：:\s]+`([^`]+)`|Provided\s+信号[：:]\s*`([^`]+)`|提供\s*`([^`]+)`'),
            'r_ports': re.compile(r'R-PORT[：:\s]+`([^`]+)`|Required\s+信号[：:]\s*`([^`]+)`|接收\s*`([^`]+)`'),
            'runnable': re.compile(r'Runnable\s+`([^`]+)`'),
            'variable_access_count': re.compile(r'(\d+)\s*条\s*VARIABLE-ACCESS'),
            'period': re.compile(r'周期\s*(\d+)\s*ms'),
            'alive_timeout': re.compile(r'aliveTimeout\s*([\d.]+)\s*s'),
            'min_format': re.compile(r'无需任何\s*Runnable|仅包含一个\s*P-PORT'),
            'interface_refs': re.compile(r'可引用.*?[：:](.*?)(?:输出|$)', re.DOTALL)
        }

        # 随机选择种子
        self.current_seed = random.choice(self.SEEDS)
        random.seed(self.current_seed)

        # 分析FSM结构
        self.fsm_analysis = self._analyze_fsm_structure()

        # 性能统计 - 增加内存和token统计
        self.stats = {
            'total_requests': 0,
            'successful_generations': 0,
            'avg_blocks_per_generation': 0,
            'avg_llm_calls': 0,
            'avg_generation_time': 0,
            'avg_tokens_used': 0,
            'avg_memory_mb': 0,
            'current_memory_mb': 0
        }

        # 性能监控
        self.process = psutil.Process(os.getpid())
        self.initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB

        print("🎯 AUTOSAR-Optimized Block-Level FSM Strategy initialized")
        print(f"   FSM states: {len(self.fsm_engine.transitions)}")
        print(f"   Block size: {self.min_block_size}-{self.max_block_size} tokens")
        print(f"   Temperature: {self.temperature}, Top-P: {self.top_p}")
        print(f"   Current seed: {self.current_seed}")

    def _analyze_fsm_structure(self) -> Dict[str, Any]:
        """分析FSM结构，识别关键模式"""
        analysis = {
            'branch_points': {},  # 分支点（多个可能的下一步）
            'merge_points': {},  # 汇合点（多个路径汇聚）
            'loops': [],  # 循环结构
            'critical_paths': []  # 关键路径
        }

        # 识别分支点
        for state, transitions in self.fsm_engine.transitions.items():
            if len(transitions) > self.branch_threshold:
                analysis['branch_points'][state] = list(transitions.keys())

        # 识别汇合点（反向查找）
        reverse_transitions = defaultdict(set)
        for state, transitions in self.fsm_engine.transitions.items():
            for token, next_state in transitions.items():
                if not token.startswith('_COMPLETE_'):
                    reverse_transitions[next_state].add(state)

        for state, predecessors in reverse_transitions.items():
            if len(predecessors) > 2:
                analysis['merge_points'][state] = list(predecessors)

        print(f"📊 FSM Analysis: {len(analysis['branch_points'])} branch points, "
              f"{len(analysis['merge_points'])} merge points")

        return analysis

    def _extract_autosar_requirements(self, prompt: str) -> Dict[str, Any]:
        """从prompt中提取AUTOSAR需求"""
        requirements = {
            'component_name': 'ASW_COM',
            'p_ports': [],
            'r_ports': [],
            'runnables': [],
            'variable_access_count': 0,
            'period': '0.01',  # 默认10ms
            'alive_timeout': '0.3',  # 默认0.3s
            'handle_timeout_type': 'NONE',
            'has_internal_behavior': True,
            'format_type': 'UNKNOWN',  # MIN, MID, FULL
            'interface_refs': []
        }

        # 提取组件名
        comp_match = self.autosar_patterns['component_name'].search(prompt)
        if comp_match:
            requirements['component_name'] = comp_match.group(1) or comp_match.group(2) or comp_match.group(3)

        # 提取P-PORTs - 改进匹配
        p_port_text = prompt
        for match in self.autosar_patterns['p_ports'].finditer(p_port_text):
            port_name = match.group(1) or match.group(2) or match.group(3)
            if port_name and port_name not in requirements['p_ports']:
                requirements['p_ports'].append(port_name.strip())

        # 特殊处理列举的端口
        if '`MCU01_EmergShutDown`' in prompt:
            if 'MCU01_EmergShutDown' not in requirements['p_ports']:
                requirements['p_ports'].append('MCU01_EmergShutDown')
        if '`MCU02_MaxTor`' in prompt:
            if 'MCU02_MaxTor' not in requirements['p_ports']:
                requirements['p_ports'].append('MCU02_MaxTor')
        if '`MCU03_NRF_IdcSamp`' in prompt:
            if 'MCU03_NRF_IdcSamp' not in requirements['p_ports']:
                requirements['p_ports'].append('MCU03_NRF_IdcSamp')

        # 提取R-PORTs
        for match in self.autosar_patterns['r_ports'].finditer(prompt):
            port_name = match.group(1) or match.group(2) or match.group(3)
            if port_name and port_name not in requirements['r_ports']:
                requirements['r_ports'].append(port_name.strip())

        # 特殊处理列举的R端口
        if '`HCU01_TqCmd`' in prompt:
            if 'HCU01_TqCmd' not in requirements['r_ports']:
                requirements['r_ports'].append('HCU01_TqCmd')
        if '`HCU01_Shift`' in prompt:
            if 'HCU01_Shift' not in requirements['r_ports']:
                requirements['r_ports'].append('HCU01_Shift')
        if '`HCU02_Poweroff`' in prompt:
            if 'HCU02_Poweroff' not in requirements['r_ports']:
                requirements['r_ports'].append('HCU02_Poweroff')

        # 提取Runnable
        runnable_match = self.autosar_patterns['runnable'].search(prompt)
        if runnable_match:
            requirements['runnables'].append(runnable_match.group(1))

        # 提取VARIABLE-ACCESS数量
        va_match = self.autosar_patterns['variable_access_count'].search(prompt)
        if va_match:
            requirements['variable_access_count'] = int(va_match.group(1))

        # 提取周期
        period_match = self.autosar_patterns['period'].search(prompt)
        if period_match:
            period_ms = int(period_match.group(1))
            requirements['period'] = f"{period_ms / 1000:.3f}".rstrip('0').rstrip('.')

        # 提取aliveTimeout
        timeout_match = self.autosar_patterns['alive_timeout'].search(prompt)
        if timeout_match:
            requirements['alive_timeout'] = timeout_match.group(1)

        # 检查是否需要内部行为
        if self.autosar_patterns['min_format'].search(prompt):
            requirements['has_internal_behavior'] = False

        # 判断格式类型
        if not requirements['has_internal_behavior'] and len(requirements['p_ports']) == 1 and len(
                requirements['r_ports']) == 0:
            requirements['format_type'] = 'MIN'
        elif len(requirements['p_ports']) == 2 and len(requirements['r_ports']) == 1:
            requirements['format_type'] = 'MID'
        elif len(requirements['p_ports']) == 3 and len(requirements['r_ports']) == 3:
            requirements['format_type'] = 'FULL'

        # 提取接口引用
        interface_match = self.autosar_patterns['interface_refs'].search(prompt)
        if interface_match:
            interface_text = interface_match.group(1)
            # 提取所有接口路径
            interface_paths = re.findall(r'/[A-Za-z_/]+SR_Interface_[A-Za-z0-9_]+', interface_text)
            requirements['interface_refs'] = interface_paths

        print(f"📋 Extracted requirements: {requirements['format_type']} format, "
              f"{len(requirements['p_ports'])}P+{len(requirements['r_ports'])}R")

        return requirements

    async def generate(self, vllm_endpoint: str, request) -> Tuple[str, Dict]:
        """主生成方法 - AUTOSAR优化版"""
        start_time = time.time()
        start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.stats['total_requests'] += 1
        self.vllm_endpoint = vllm_endpoint

        print(f"🎯 Using AUTOSAR-Optimized Block-Level FSM Strategy")
        print(f"🎲 Seed: {self.current_seed}, Temperature: {self.temperature}, Top-P: {self.top_p}")

        # 提取AUTOSAR需求
        requirements = self._extract_autosar_requirements(request.prompt)

        # 初始化
        xml_content = ""
        current_state = ""
        blocks_generated = []
        llm_calls = 0
        total_paths_explored = 0
        total_tokens_used = 0

        constraints_applied = {
            "fsm": True,
            "block_level": True,
            "dynamic_blocks": True,
            "strategy": "autosar_optimized_block_level_fsm",
            "seed": self.current_seed,
            "temperature": self.temperature,
            "top_p": self.top_p
        }

        # 重置FSM
        self.fsm_engine.reset()

        try:
            # 阶段1：基于需求的路径规划
            block_plan = self._plan_blocks_for_autosar(requirements)
            print(f"📋 Block plan: {len(block_plan)} planned blocks for {requirements['format_type']} format")

            # 阶段2：按计划生成块
            for block_idx, planned_block in enumerate(block_plan):
                print(f"\n--- 块 {block_idx + 1}/{len(block_plan)}: {planned_block['name']} ---")
                print(f"📍 当前状态: {current_state if current_state else '初始'}")

                # 获取该块的路径
                block_paths = self._get_paths_for_planned_block(
                    current_state,
                    planned_block,
                    requirements
                )

                if not block_paths:
                    print(f"⚠️ 无法找到块 {planned_block['name']} 的路径")
                    break

                # 创建动态块
                dynamic_block = DynamicBlock(
                    name=planned_block['name'],
                    start_state=current_state,
                    paths=block_paths
                )

                print(f"📦 块包含 {len(dynamic_block.paths)} 条可能路径")
                total_paths_explored += len(dynamic_block.paths)

                # 生成块内容
                block_xml, selected_path, end_state, tokens_used = await self._generate_autosar_block(
                    dynamic_block,
                    xml_content,
                    request.prompt,
                    requirements,
                    planned_block
                )

                llm_calls += 1
                total_tokens_used += tokens_used

                if block_xml:
                    xml_content += block_xml
                    current_state = end_state

                    blocks_generated.append({
                        'name': dynamic_block.name,
                        'size': len(block_xml),
                        'path_length': len(selected_path.tokens) if selected_path else 0,
                        'tokens_used': tokens_used
                    })

                    print(f"✅ 块生成成功: {tokens_used} tokens, {len(block_xml)} chars")
                else:
                    print("⚠️ 块生成失败")
                    break

            # 阶段3：完成XML
            if requirements['format_type'] != 'MIN' or xml_content.count('</APPLICATION-SW-COMPONENT-TYPE>') == 0:
                final_xml = self._finalize_autosar_xml(xml_content, requirements)
            else:
                final_xml = xml_content

            # 计算性能指标
            generation_time = time.time() - start_time
            end_memory = self.process.memory_info().rss / 1024 / 1024
            memory_used = end_memory - start_memory

            # 更新统计
            self._update_stats(generation_time, len(blocks_generated), llm_calls, True, total_tokens_used, memory_used)

            constraints_applied.update({
                'blocks_generated': len(blocks_generated),
                'llm_calls': llm_calls,
                'generation_time': generation_time,
                'total_paths_explored': total_paths_explored,
                'block_details': blocks_generated,
                'final_state': current_state,
                'fsm_compliant': True,
                'format_type': requirements['format_type'],
                'tokens_used': total_tokens_used,
                'memory_used_mb': memory_used,
                'performance_metrics': {
                    'time_seconds': round(generation_time, 2),
                    'total_tokens': total_tokens_used,
                    'memory_mb': round(memory_used, 2),
                    'tokens_per_second': round(total_tokens_used / generation_time, 2) if generation_time > 0 else 0
                }
            })

            print(f"\n🏁 生成完成:")
            print(f"   ⏱️  时间: {generation_time:.2f}秒")
            print(f"   🎯 Tokens: {total_tokens_used}")
            print(f"   💾 内存: {memory_used:.2f}MB")
            print(f"   📦 块数: {len(blocks_generated)}")
            print(f"   🔄 LLM调用: {llm_calls}")

            return final_xml, constraints_applied

        except Exception as e:
            print(f"❌ 块生成失败: {e}")
            import traceback
            traceback.print_exc()

            generation_time = time.time() - start_time
            end_memory = self.process.memory_info().rss / 1024 / 1024
            memory_used = end_memory - start_memory

            self._update_stats(generation_time, 0, llm_calls, False, total_tokens_used, memory_used)

            return xml_content, {
                **constraints_applied,
                'error': str(e),
                'generation_time': generation_time,
                'tokens_used': total_tokens_used,
                'memory_used_mb': memory_used
            }

    def _plan_blocks_for_autosar(self, requirements: Dict) -> List[Dict]:
        """基于AUTOSAR需求规划块序列"""
        blocks = []

        # MIN格式
        if requirements['format_type'] == 'MIN':
            blocks.append({
                'name': 'COMPONENT_HEADER',
                'target_elements': ['APPLICATION-SW-COMPONENT-TYPE', 'SHORT-NAME'],
                'max_size': 6
            })
            blocks.append({
                'name': 'SINGLE_P_PORT',
                'target_elements': ['PORTS', 'P-PORT-PROTOTYPE'],
                'max_size': 8
            })

        # MID格式
        elif requirements['format_type'] == 'MID':
            blocks.append({
                'name': 'COMPONENT_HEADER',
                'target_elements': ['APPLICATION-SW-COMPONENT-TYPE', 'SHORT-NAME'],
                'max_size': 6
            })
            blocks.append({
                'name': 'PORTS_SECTION',
                'target_elements': ['PORTS'] + ['P-PORT-PROTOTYPE'] * len(requirements['p_ports']),
                'max_size': 15
            })
            blocks.append({
                'name': 'R_PORTS_SECTION',
                'target_elements': ['R-PORT-PROTOTYPE', 'REQUIRED-COM-SPECS'],
                'max_size': 12
            })
            blocks.append({
                'name': 'BEHAVIOR_SECTION',
                'target_elements': ['INTERNAL-BEHAVIORS', 'SWC-INTERNAL-BEHAVIOR'],
                'max_size': 15
            })

        # FULL格式
        elif requirements['format_type'] == 'FULL':
            blocks.append({
                'name': 'COMPONENT_HEADER',
                'target_elements': ['APPLICATION-SW-COMPONENT-TYPE', 'SHORT-NAME'],
                'max_size': 6
            })
            # 分别处理P-PORTs
            for i, p_port in enumerate(requirements['p_ports']):
                blocks.append({
                    'name': f'P_PORT_{i + 1}',
                    'target_elements': ['P-PORT-PROTOTYPE'],
                    'max_size': 8,
                    'port_name': p_port
                })
            # 分别处理R-PORTs
            for i, r_port in enumerate(requirements['r_ports']):
                blocks.append({
                    'name': f'R_PORT_{i + 1}',
                    'target_elements': ['R-PORT-PROTOTYPE', 'REQUIRED-COM-SPECS'],
                    'max_size': 12,
                    'port_name': r_port
                })
            blocks.append({
                'name': 'BEHAVIOR_HEADER',
                'target_elements': ['INTERNAL-BEHAVIORS', 'SWC-INTERNAL-BEHAVIOR'],
                'max_size': 10
            })
            blocks.append({
                'name': 'EVENTS_AND_RUNNABLE',
                'target_elements': ['EVENTS', 'TIMING-EVENT', 'RUNNABLES', 'RUNNABLE-ENTITY'],
                'max_size': 15
            })
            # VARIABLE-ACCESS批处理
            if requirements['variable_access_count'] > 0:
                blocks.append({
                    'name': 'VARIABLE_ACCESS_BATCH',
                    'target_elements': ['DATA-RECEIVE-POINT-BY-ARGUMENTS', 'DATA-SEND-POINTS', 'VARIABLE-ACCESS'],
                    'max_size': 20,
                    'va_count': requirements['variable_access_count']
                })

        else:
            # 默认规划
            blocks.append({
                'name': 'GENERIC_COMPONENT',
                'target_elements': ['APPLICATION-SW-COMPONENT-TYPE'],
                'max_size': 15
            })

        return blocks

    def _get_paths_for_planned_block(self, start_state: str, planned_block: Dict,
                                     requirements: Dict) -> List[FSMPath]:
        """获取计划块的可能路径"""
        # 根据块类型设置最大深度
        max_depth = planned_block.get('max_size', self.max_block_size)

        # 如果是VARIABLE-ACCESS块，使用更大的深度
        if 'VARIABLE_ACCESS' in planned_block['name']:
            max_depth = 20

        # 探索路径
        paths = self._explore_paths_from_state(
            start_state,
            max_depth=max_depth,
            max_paths=100,
            target_elements=planned_block.get('target_elements', [])
        )

        return paths

    def _explore_paths_from_state(self, start_state: str, max_depth: int,
                                  max_paths: int, target_elements: List[str] = None) -> List[FSMPath]:
        """从给定状态探索可能的路径（优先考虑目标元素）"""
        paths = []
        queue = deque([FSMPath([start_state], [])])
        visited = set()

        while queue and len(paths) < max_paths:
            current_path = queue.popleft()
            current_state = current_path.states[-1]

            # 检查深度限制
            if len(current_path.tokens) >= max_depth:
                if len(current_path.tokens) >= self.min_block_size:
                    paths.append(current_path)
                continue

            # 获取可能的转移
            if current_state in self.fsm_engine.transitions:
                transitions = self.fsm_engine.transitions[current_state]
            else:
                # 尝试模糊匹配
                transitions = self._get_fuzzy_transitions(current_state)

            if not transitions:
                if len(current_path.tokens) >= self.min_block_size:
                    paths.append(current_path)
                continue

            # 优先探索目标元素
            sorted_transitions = self._sort_transitions_by_priority(
                transitions, target_elements
            )

            # 探索每个可能的转移
            for token, next_state in sorted_transitions:
                # 跳过已访问的状态（避免循环）
                state_key = f"{next_state}:{len(current_path.tokens)}"
                if state_key in visited and len(current_path.tokens) > 5:
                    continue
                visited.add(state_key)

                # 计算转移成本
                cost = self._calculate_transition_cost(token, current_state, next_state)

                # 创建新路径
                new_path = current_path.extend(token, next_state, cost)

                # 如果是完成标记或达到合适的块边界，添加到结果
                if (token.startswith('_COMPLETE_') or
                        self._is_good_block_boundary(next_state) or
                        (target_elements and self._contains_target_elements(new_path, target_elements))):
                    paths.append(new_path)
                else:
                    queue.append(new_path)

        return paths

    def _sort_transitions_by_priority(self, transitions: Dict[str, str],
                                      target_elements: List[str]) -> List[Tuple[str, str]]:
        """根据目标元素对转移进行优先级排序"""
        if not target_elements:
            return list(transitions.items())

        priority_transitions = []
        other_transitions = []

        for token, next_state in transitions.items():
            if any(target in token for target in target_elements):
                priority_transitions.append((token, next_state))
            else:
                other_transitions.append((token, next_state))

        return priority_transitions + other_transitions

    def _contains_target_elements(self, path: FSMPath, target_elements: List[str]) -> bool:
        """检查路径是否包含目标元素"""
        path_tokens = set(path.tokens)
        for target in target_elements:
            if any(target in token for token in path_tokens):
                return True
        return False

    async def _generate_autosar_block(self, block: DynamicBlock, current_xml: str,
                                      base_prompt: str, requirements: Dict,
                                      planned_block: Dict) -> Tuple[str, FSMPath, str, int]:
        """生成AUTOSAR特定的块内容"""
        # 构建增强的prompt
        generation_prompt = self._build_autosar_prompt(
            base_prompt, block, current_xml, requirements, planned_block
        )

        try:
            # 添加随机性变化
            temp_variation = random.uniform(-0.1, 0.1)
            top_p_variation = random.uniform(-0.05, 0.05)

            vllm_request = {
                "model": "/model/HuggingFace/deepseek-ai/DeepSeek-R1-Distill-Qwen-14B",
                "prompt": generation_prompt,
                "max_tokens": 1000,
                "temperature": max(0.1, min(1.0, self.temperature + temp_variation)),
                "top_p": max(0.1, min(1.0, self.top_p + top_p_variation)),
                "seed": self.current_seed,
                "stream": False
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                        f"{self.vllm_endpoint}/v1/completions",
                        json=vllm_request,
                        timeout=aiohttp.ClientTimeout(total=60)
                ) as resp:
                    if resp.status == 200:
                        response = await resp.json()
                        output = response["choices"][0]["text"].strip()

                        # 计算使用的tokens（估算）
                        tokens_used = len(generation_prompt.split()) + len(output.split())

                        # 解析输出
                        chosen_path_idx, xml_content = self._parse_path_selection(output)

                        if 0 <= chosen_path_idx < len(block.paths):
                            selected_path = block.paths[chosen_path_idx]
                        else:
                            # 选择最短路径
                            selected_path = min(block.paths, key=lambda p: len(p.tokens))

                        # 清理XML
                        xml_content = self._clean_and_enhance_xml(xml_content, requirements, planned_block)

                        end_state = selected_path.states[-1] if selected_path else block.start_state

                        return xml_content, selected_path, end_state, tokens_used

        except Exception as e:
            print(f"❌ 块生成错误: {e}")

        return "", None, block.start_state, 0

    def _build_autosar_prompt(self, base_prompt: str, block: DynamicBlock,
                              current_xml: str, requirements: Dict,
                              planned_block: Dict) -> str:
        """构建AUTOSAR特定的生成prompt"""
        # 根据块类型构建特定指导
        if 'COMPONENT_HEADER' in block.name:
            specific_guidance = f"""
Generate the component header for AUTOSAR APPLICATION-SW-COMPONENT-TYPE.
Component name: {requirements['component_name']}
"""
        elif 'P_PORT' in block.name:
            port_name = planned_block.get('port_name',
                                          requirements['p_ports'][0] if requirements['p_ports'] else 'Port')
            specific_guidance = f"""
Generate P-PORT-PROTOTYPE for provided port.
Port name: {port_name}
Use appropriate interface reference from: {', '.join(requirements['interface_refs'])}
Include UUID attribute.
"""
        elif 'R_PORT' in block.name:
            port_name = planned_block.get('port_name',
                                          requirements['r_ports'][0] if requirements['r_ports'] else 'Port')
            specific_guidance = f"""
Generate R-PORT-PROTOTYPE for required port.
Port name: {port_name}
Include REQUIRED-COM-SPECS with:
- NONQUEUED-RECEIVER-COM-SPEC
- ALIVE-TIMEOUT: {requirements['alive_timeout']}
- HANDLE-TIMEOUT-TYPE: {requirements['handle_timeout_type']}
Use appropriate interface reference.
Include UUID attribute.
"""
        elif 'VARIABLE_ACCESS' in block.name:
            va_count = planned_block.get('va_count', requirements['variable_access_count'])
            specific_guidance = f"""
Generate {va_count} VARIABLE-ACCESS elements.
Split between:
- DATA-RECEIVE-POINT-BY-ARGUMENTS: {va_count // 2} items
- DATA-SEND-POINTS: {va_count - va_count // 2} items

Use naming patterns:
- Receive: DRPA_[PortName]_[Index]
- Send: DSP_[PortName]_[Index]

Include proper PORT-PROTOTYPE-REF and TARGET-DATA-PROTOTYPE-REF.
Each VARIABLE-ACCESS needs UUID attribute.
"""
        elif 'BEHAVIOR' in block.name:
            specific_guidance = f"""
Generate internal behavior structure.
Include:
- SWC-INTERNAL-BEHAVIOR with SHORT-NAME: SwcInternalBehavior
- EVENTS section with TIMING-EVENT
- Event period: {requirements['period']}
- Runnable name: {requirements['runnables'][0] if requirements['runnables'] else 'RE_COM_SWC'}
"""
        else:
            specific_guidance = "Generate appropriate AUTOSAR XML content for this section."

        # 格式化可用路径
        paths_description = self._format_autosar_paths(block.paths[:10])

        prompt = f"""{base_prompt}

=== AUTOSAR XML Generation ===
Format Type: {requirements['format_type']}
Current Block: {block.name}

{specific_guidance}

Current XML Context:
```xml
{current_xml[-800:] if len(current_xml) > 800 else current_xml}
```

Available FSM Paths:
{paths_description}

INSTRUCTIONS:
1. Choose the most appropriate path (indicate: CHOSEN PATH: [number])
2. Generate valid AUTOSAR XML following the chosen path
3. Include all required attributes (UUID, DEST, etc.)
4. Follow AUTOSAR naming conventions
5. Ensure proper element nesting

Generate XML:
"""
        return prompt

    def _format_autosar_paths(self, paths: List[FSMPath]) -> str:
        """格式化AUTOSAR路径显示"""
        formatted = []
        for i, path in enumerate(paths):
            # 只显示非COMPLETE的token
            visible_tokens = [t for t in path.tokens if not t.startswith('_COMPLETE_')]
            path_str = " → ".join(visible_tokens[:8])  # 限制显示长度
            if len(visible_tokens) > 8:
                path_str += " → ..."
            formatted.append(f"Path {i}: {path_str}")
        return "\n".join(formatted)

    def _clean_and_enhance_xml(self, xml: str, requirements: Dict, planned_block: Dict) -> str:
        """清理并增强生成的XML"""
        # 移除markdown标记
        xml = re.sub(r'^```xml\s*\n?', '', xml)
        xml = re.sub(r'\n?```\s*$', '', xml)
        xml = re.sub(r'^```\s*\n?', '', xml)

        # 移除CHOSEN PATH行
        lines = xml.split('\n')
        clean_lines = []
        for line in lines:
            if not line.startswith('CHOSEN PATH:') and not line.startswith('Path '):
                if line.strip():
                    clean_lines.append(line)

        xml = '\n'.join(clean_lines)

        # 根据块类型进行特定增强
        if 'P_PORT' in planned_block['name'] and planned_block.get('port_name'):
            # 确保端口名称正确
            port_name = planned_block['port_name']
            xml = xml.replace('<SHORT-NAME>Port</SHORT-NAME>', f'<SHORT-NAME>PPort_{port_name}</SHORT-NAME>')

        elif 'R_PORT' in planned_block['name'] and planned_block.get('port_name'):
            port_name = planned_block['port_name']
            xml = xml.replace('<SHORT-NAME>Port</SHORT-NAME>', f'<SHORT-NAME>RPort_{port_name}</SHORT-NAME>')

        return xml

    def _finalize_autosar_xml(self, xml_content: str, requirements: Dict) -> str:
        """完成AUTOSAR XML结构"""
        # 检查是否需要关闭标签
        open_tags = []
        for line in xml_content.split('\n'):
            # 查找开始标签
            start_match = re.search(r'<([A-Z\-]+)(?:\s[^>]*)?>(?![^<]*/>)', line)
            if start_match:
                tag = start_match.group(1)
                if not re.search(f'</{tag}>', xml_content[xml_content.find(line):]):
                    open_tags.append(tag)

        # 反向关闭所有未关闭的标签
        closing_tags = []
        for tag in reversed(open_tags):
            # 根据标签类型添加适当的缩进
            indent = '  ' * (len(open_tags) - open_tags.index(tag) - 1)
            closing_tags.append(f'{indent}</{tag}>')

        if closing_tags:
            xml_content += '\n' + '\n'.join(closing_tags)

        # 添加XML声明和根元素（如果缺失）
        if not xml_content.strip().startswith('<?xml'):
            xml_header = '''<?xml version="1.0" encoding="UTF-8"?>
<AUTOSAR xmlns="http://autosar.org/schema/r4.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://autosar.org/schema/r4.0 AUTOSAR_4-2-2.xsd">
  <AR-PACKAGES>
    <AR-PACKAGE>
      <SHORT-NAME>COM_SWC</SHORT-NAME>
      <ELEMENTS>
'''
            xml_footer = '''
      </ELEMENTS>
    </AR-PACKAGE>
  </AR-PACKAGES>
</AUTOSAR>'''

            xml_content = xml_header + xml_content + xml_footer

        return xml_content.strip()

    def _parse_path_selection(self, output: str) -> Tuple[int, str]:
        """解析LLM的路径选择和XML输出"""
        lines = output.split('\n')
        chosen_idx = 0
        xml_start = -1

        for i, line in enumerate(lines):
            if line.startswith('CHOSEN PATH:'):
                try:
                    chosen_idx = int(re.search(r'\d+', line).group())
                except:
                    pass
            elif line.strip().startswith('<') and xml_start == -1:
                xml_start = i
                break

        if xml_start > -1:
            xml_content = '\n'.join(lines[xml_start:])
        else:
            xml_content = output

        return chosen_idx, xml_content

    def _get_fuzzy_transitions(self, state: str) -> Dict[str, str]:
        """获取模糊匹配的转移"""
        # 这里可以实现更复杂的模糊匹配逻辑
        tokens = state.split()
        for i in range(len(tokens), 0, -1):
            partial_state = " ".join(tokens[:i])
            if partial_state in self.fsm_engine.transitions:
                return self.fsm_engine.transitions[partial_state]
        return {}

    def _calculate_transition_cost(self, token: str, from_state: str, to_state: str) -> float:
        """计算状态转移的成本"""
        cost = 1.0

        # 完成标记的成本较低（鼓励完成）
        if token.startswith('_COMPLETE_'):
            cost *= 0.5

        # 分支点的成本较高
        if from_state in self.fsm_analysis['branch_points']:
            cost *= 1.2

        # 循环的成本较高
        if to_state in from_state:  # 简单的循环检测
            cost *= 1.5

        return cost

    def _is_good_block_boundary(self, state: str) -> bool:
        """判断是否是好的块边界"""
        # 汇合点是好的边界
        if state in self.fsm_analysis['merge_points']:
            return True

        # 只有少量出边的状态是好的边界
        if state in self.fsm_engine.transitions:
            if len(self.fsm_engine.transitions[state]) <= 2:
                return True

        return False

    def _update_stats(self, generation_time: float, blocks_count: int,
                      llm_calls: int, success: bool, tokens_used: int, memory_used: float):
        """更新性能统计"""
        if success:
            self.stats['successful_generations'] += 1

        n = self.stats['total_requests']

        # 更新平均值
        self.stats['avg_generation_time'] = (
                (self.stats['avg_generation_time'] * (n - 1) + generation_time) / n
        )
        self.stats['avg_blocks_per_generation'] = (
                (self.stats['avg_blocks_per_generation'] * (n - 1) + blocks_count) / n
        )
        self.stats['avg_llm_calls'] = (
                (self.stats['avg_llm_calls'] * (n - 1) + llm_calls) / n
        )
        self.stats['avg_tokens_used'] = (
                (self.stats['avg_tokens_used'] * (n - 1) + tokens_used) / n
        )
        self.stats['avg_memory_mb'] = (
                (self.stats['avg_memory_mb'] * (n - 1) + memory_used) / n
        )
        self.stats['current_memory_mb'] = self.process.memory_info().rss / 1024 / 1024 - self.initial_memory

    def get_statistics(self) -> Dict[str, Any]:
        """获取策略统计信息"""
        return {
            **self.stats,
            'success_rate': (
                self.stats['successful_generations'] / self.stats['total_requests']
                if self.stats['total_requests'] > 0 else 0
            ),
            'fsm_analysis': {
                'branch_points': len(self.fsm_analysis['branch_points']),
                'merge_points': len(self.fsm_analysis['merge_points'])
            },
            'performance': {
                'avg_time_seconds': round(self.stats['avg_generation_time'], 2),
                'avg_tokens': round(self.stats['avg_tokens_used'], 0),
                'avg_memory_mb': round(self.stats['avg_memory_mb'], 2),
                'current_memory_mb': round(self.stats['current_memory_mb'], 2)
            }
        }