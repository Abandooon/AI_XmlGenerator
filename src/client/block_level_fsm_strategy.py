#!/usr/bin/env python3
# block_level_fsm_strategy.py - 分层块级FSM生成策略

import asyncio
import time
import json
import re
from typing import Dict, List, Optional, Tuple, Any, Set
from collections import defaultdict
import aiohttp
import xml.etree.ElementTree as ET


class BlockDefinition:
    """XML块定义"""

    def __init__(self, name: str, start_elements: List[str],
                 end_conditions: List[str], block_type: str = "container"):
        self.name = name
        self.start_elements = start_elements  # 块可以包含的起始元素
        self.end_conditions = end_conditions  # 块结束条件
        self.block_type = block_type  # container, content, mixed
        self.max_elements = 10  # 块内最大元素数
        self.required_elements = []  # 必需元素
        self.optional_elements = []  # 可选元素


class BlockLevelFSMStrategy:
    """分层块级FSM生成策略 - 逐块生成而非逐token"""

    def __init__(self, fsm_engine, config: Dict[str, Any] = None):
        self.fsm_engine = fsm_engine
        self.config = config or {}
        self.vllm_endpoint = None

        # 策略参数
        self.max_blocks = self.config.get('max_blocks', 10)
        self.temperature = self.config.get('temperature', 0.3)
        self.top_p = self.config.get('top_p', 0.9)
        self.block_validation = self.config.get('block_validation', True)

        # 定义块结构
        self._define_blocks()

        # 性能统计
        self.stats = {
            'total_requests': 0,
            'successful_generations': 0,
            'avg_blocks_per_generation': 0,
            'avg_llm_calls': 0,
            'avg_generation_time': 0
        }

        print("🎯 BlockLevelFSMStrategy initialized")
        print(f"   Max blocks: {self.max_blocks}")
        print(f"   Block definitions: {len(self.block_definitions)}")

    def _define_blocks(self):
        """定义XML生成块"""
        self.block_definitions = {
            # 头部块：组件基本信息
            'header_block': BlockDefinition(
                name='header_block',
                start_elements=['APPLICATION-SW-COMPONENT-TYPE', 'SHORT-NAME', 'ADMIN-DATA'],
                end_conditions=['PORTS', 'INTERNAL-BEHAVIORS'],
                block_type='mixed'
            ),

            # 端口块：所有端口定义
            'ports_block': BlockDefinition(
                name='ports_block',
                start_elements=['PORTS', 'P-PORT-PROTOTYPE', 'R-PORT-PROTOTYPE'],
                end_conditions=['INTERNAL-BEHAVIORS', '_COMPLETE_PORTS'],
                block_type='container'
            ),

            # 行为块：内部行为定义
            'behaviors_block': BlockDefinition(
                name='behaviors_block',
                start_elements=['INTERNAL-BEHAVIORS', 'SWC-INTERNAL-BEHAVIOR'],
                end_conditions=['_COMPLETE_APPLICATION-SW-COMPONENT-TYPE'],
                block_type='container'
            ),

            # P端口子块
            'p_port_block': BlockDefinition(
                name='p_port_block',
                start_elements=['P-PORT-PROTOTYPE'],
                end_conditions=['_COMPLETE_P-PORT-PROTOTYPE'],
                block_type='mixed'
            ),

            # R端口子块
            'r_port_block': BlockDefinition(
                name='r_port_block',
                start_elements=['R-PORT-PROTOTYPE'],
                end_conditions=['_COMPLETE_R-PORT-PROTOTYPE'],
                block_type='mixed'
            ),

            # 事件块
            'events_block': BlockDefinition(
                name='events_block',
                start_elements=['EVENTS', 'TIMING-EVENT'],
                end_conditions=['RUNNABLES', '_COMPLETE_EVENTS'],
                block_type='container'
            ),

            # 可运行实体块
            'runnables_block': BlockDefinition(
                name='runnables_block',
                start_elements=['RUNNABLES', 'RUNNABLE-ENTITY'],
                end_conditions=['_COMPLETE_RUNNABLES'],
                block_type='container'
            )
        }

        # 块的执行顺序
        self.block_sequence = [
            'header_block',
            'ports_block',
            'behaviors_block'
        ]

    async def generate(self, vllm_endpoint: str, request) -> Tuple[str, Dict]:
        """主生成方法 - 逐块生成XML"""
        start_time = time.time()
        self.stats['total_requests'] += 1
        self.vllm_endpoint = vllm_endpoint

        print(f"🎯 Using Block-Level FSM Strategy")
        print(f"📊 Generating XML in logical blocks")

        # 初始化
        xml_content = ""
        generation_path = []
        blocks_generated = []
        llm_calls = 0

        constraints_applied = {
            "fsm": True,
            "block_level": True,
            "strategy": "block_level_fsm"
        }

        # 重置FSM
        self.fsm_engine.reset()

        try:
            # 阶段1：结构规划
            structure_plan = await self._plan_structure(request.prompt)
            print(f"📋 Structure plan: {structure_plan}")

            # 阶段2：逐块生成
            for block_idx, block_name in enumerate(self.block_sequence):
                if block_idx >= self.max_blocks:
                    print(f"⚠️ Reached max blocks limit")
                    break

                print(f"\n--- 生成块 {block_idx + 1}: {block_name} ---")

                # 检查是否应该生成这个块
                if not self._should_generate_block(block_name, generation_path, structure_plan):
                    print(f"⏭️ Skipping block {block_name}")
                    continue

                # 获取块的FSM上下文
                block_context = self._get_block_context(block_name, generation_path)

                # 生成块内容
                block_xml, block_path = await self._generate_block(
                    block_name,
                    block_context,
                    xml_content,
                    request.prompt,
                    structure_plan
                )

                llm_calls += 1

                if block_xml:
                    # 验证块的有效性
                    if self.block_validation:
                        is_valid = self._validate_block(block_xml, block_name, generation_path)
                        if not is_valid:
                            print(f"❌ Block validation failed, retrying...")
                            # 重试一次
                            block_xml, block_path = await self._generate_block(
                                block_name, block_context, xml_content,
                                request.prompt, structure_plan, retry=True
                            )
                            llm_calls += 1

                    # 集成块到整体XML
                    xml_content = self._integrate_block(xml_content, block_xml, generation_path)
                    generation_path.extend(block_path)
                    blocks_generated.append({
                        'name': block_name,
                        'size': len(block_xml),
                        'elements': len(block_path)
                    })

                    print(f"✅ Block generated: {len(block_xml)} chars")
                else:
                    print(f"⚠️ Empty block generated")

                # 检查是否完成
                if self._is_generation_complete(generation_path, xml_content):
                    print(f"🏁 Generation complete")
                    break

            # 阶段3：完成和验证
            final_xml = self._finalize_xml(xml_content, generation_path)

            # 更新统计
            generation_time = time.time() - start_time
            self._update_stats(generation_time, len(blocks_generated), llm_calls, True)

            constraints_applied.update({
                'blocks_generated': len(blocks_generated),
                'llm_calls': llm_calls,
                'generation_time': generation_time,
                'block_details': blocks_generated
            })

            print(
                f"\n🏁 Generation completed: {len(blocks_generated)} blocks, {llm_calls} LLM calls, {generation_time:.2f}s")

            return final_xml, constraints_applied

        except Exception as e:
            print(f"❌ Block generation failed: {e}")
            import traceback
            traceback.print_exc()

            generation_time = time.time() - start_time
            self._update_stats(generation_time, 0, llm_calls, False)

            return xml_content, {
                **constraints_applied,
                'error': str(e),
                'generation_time': generation_time
            }

    async def _plan_structure(self, prompt: str) -> Dict[str, Any]:
        """阶段1：基于需求规划XML结构"""
        planning_prompt = f"""Based on the requirements, plan the XML structure for an AUTOSAR APPLICATION-SW-COMPONENT-TYPE.

Requirements: {prompt}

Analyze and determine:
1. Component name
2. Number and types of ports needed (P-PORTS for providing, R-PORTS for requiring)
3. Internal behaviors needed (events, runnables)
4. Any special requirements

Respond in JSON format:
{{
  "component_name": "...",
  "needs_admin_data": true/false,
  "ports": {{
    "p_ports_count": N,
    "r_ports_count": N,
    "port_descriptions": ["..."]
  }},
  "behaviors": {{
    "needs_timing_events": true/false,
    "runnable_count": N,
    "behavior_descriptions": ["..."]
  }},
  "special_requirements": ["..."]
}}"""

        try:
            vllm_request = {
                "model": "/model/HuggingFace/deepseek-ai/DeepSeek-R1-Distill-Qwen-14B",
                "prompt": planning_prompt,
                "max_tokens": 300,
                "temperature": 0.2,
                "stream": False,
                "response_format": {"type": "json_object"}
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                        f"{self.vllm_endpoint}/v1/completions",
                        json=vllm_request,
                        timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 200:
                        response = await resp.json()
                        plan_text = response["choices"][0]["text"].strip()
                        # 解析JSON
                        try:
                            plan = json.loads(plan_text)
                            return plan
                        except:
                            # 如果解析失败，返回默认结构
                            return self._get_default_structure_plan()
                    else:
                        return self._get_default_structure_plan()

        except Exception as e:
            print(f"⚠️ Structure planning failed: {e}")
            return self._get_default_structure_plan()

    def _get_default_structure_plan(self) -> Dict[str, Any]:
        """获取默认结构规划"""
        return {
            "component_name": "GeneratedComponent",
            "needs_admin_data": False,
            "ports": {
                "p_ports_count": 1,
                "r_ports_count": 1,
                "port_descriptions": ["Default ports"]
            },
            "behaviors": {
                "needs_timing_events": True,
                "runnable_count": 1,
                "behavior_descriptions": ["Default behavior"]
            },
            "special_requirements": []
        }

    def _should_generate_block(self, block_name: str, current_path: List[str],
                               structure_plan: Dict) -> bool:
        """判断是否应该生成某个块"""
        if block_name == 'header_block':
            return True  # 头部块总是需要

        elif block_name == 'ports_block':
            # 根据结构规划判断是否需要端口
            ports_info = structure_plan.get('ports', {})
            return (ports_info.get('p_ports_count', 0) > 0 or
                    ports_info.get('r_ports_count', 0) > 0)

        elif block_name == 'behaviors_block':
            # 根据结构规划判断是否需要行为
            behaviors_info = structure_plan.get('behaviors', {})
            return behaviors_info.get('runnable_count', 0) > 0

        return True

    def _get_block_context(self, block_name: str, current_path: List[str]) -> Dict:
        """获取块的FSM上下文信息"""
        block_def = self.block_definitions[block_name]
        context = {
            'block_name': block_name,
            'current_state': " ".join(current_path) if current_path else "",
            'allowed_elements': [],
            'required_elements': [],
            'content_guidance': {}
        }

        # 获取当前状态下允许的元素
        for start_element in block_def.start_elements:
            # 检查FSM中的可用转移
            test_path = current_path + [start_element]
            test_state = " ".join(test_path)

            # 尝试从当前状态
            current_state = " ".join(current_path) if current_path else ""
            if current_state in self.fsm_engine.transitions:
                allowed = self.fsm_engine.transitions[current_state]
                if start_element in allowed:
                    context['allowed_elements'].append(start_element)

            # 如果是起始状态
            if not current_path and "" in self.fsm_engine.transitions:
                allowed = self.fsm_engine.transitions[""]
                if start_element in allowed:
                    context['allowed_elements'].append(start_element)

        # 获取内容指导
        if hasattr(self.fsm_engine, 'fsm_data'):
            guidance = self.fsm_engine.fsm_data.get('content_guidance', {})
            context['content_guidance'] = guidance.get('content_elements', {})

        return context

    async def _generate_block(self, block_name: str, block_context: Dict,
                              current_xml: str, base_prompt: str,
                              structure_plan: Dict, retry: bool = False) -> Tuple[str, List[str]]:
        """生成一个完整的XML块"""
        block_def = self.block_definitions[block_name]

        # 构建块生成prompt
        generation_prompt = self._build_block_prompt(
            block_name, block_context, current_xml, base_prompt,
            structure_plan, retry
        )

        try:
            # 根据块类型设置生成参数
            max_tokens = 800 if block_name in ['ports_block', 'behaviors_block'] else 400

            vllm_request = {
                "model": "/model/HuggingFace/deepseek-ai/DeepSeek-R1-Distill-Qwen-14B",
                "prompt": generation_prompt,
                "max_tokens": max_tokens,
                "temperature": self.temperature,
                "top_p": self.top_p,
                "stream": False,
                "stop": ["</APPLICATION-SW-COMPONENT-TYPE>", "```"]
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                        f"{self.vllm_endpoint}/v1/completions",
                        json=vllm_request,
                        timeout=aiohttp.ClientTimeout(total=60)
                ) as resp:
                    if resp.status == 200:
                        response = await resp.json()
                        block_xml = response["choices"][0]["text"].strip()

                        # 清理输出
                        block_xml = self._clean_block_output(block_xml)

                        # 提取生成的路径
                        block_path = self._extract_block_path(block_xml)

                        return block_xml, block_path
                    else:
                        error_text = await resp.text()
                        print(f"❌ LLM request failed: {error_text}")
                        return "", []

        except Exception as e:
            print(f"❌ Block generation error: {e}")
            return "", []

    def _build_block_prompt(self, block_name: str, block_context: Dict,
                            current_xml: str, base_prompt: str,
                            structure_plan: Dict, retry: bool = False) -> str:
        """构建块生成的prompt"""

        # 基础prompt模板
        retry_note = "\nNOTE: Previous attempt failed validation. Ensure correct XML structure." if retry else ""

        if block_name == 'header_block':
            return f"""{base_prompt}

Generate the header section of an AUTOSAR APPLICATION-SW-COMPONENT-TYPE.
Component name: {structure_plan.get('component_name', 'GeneratedComponent')}

Current allowed elements: {', '.join(block_context['allowed_elements'])}

Generate a complete XML block starting with <APPLICATION-SW-COMPONENT-TYPE> including:
1. The opening tag
2. SHORT-NAME element with appropriate content
3. ADMIN-DATA section if needed ({structure_plan.get('needs_admin_data', False)})

Do NOT close the APPLICATION-SW-COMPONENT-TYPE tag yet.
{retry_note}

XML:"""

        elif block_name == 'ports_block':
            ports_info = structure_plan.get('ports', {})
            return f"""{base_prompt}

Continue the XML by adding the PORTS section.

Current XML so far:
```xml
{current_xml[-500:] if len(current_xml) > 500 else current_xml}
```

Requirements:
- P-PORTS needed: {ports_info.get('p_ports_count', 0)}
- R-PORTS needed: {ports_info.get('r_ports_count', 0)}
- Port descriptions: {', '.join(ports_info.get('port_descriptions', []))}

Generate the complete <PORTS> section with all port definitions.
Include appropriate SHORT-NAME, interface references, and specifications for each port.
Close the </PORTS> tag when done.
{retry_note}

XML:"""

        elif block_name == 'behaviors_block':
            behaviors_info = structure_plan.get('behaviors', {})
            return f"""{base_prompt}

Continue the XML by adding the INTERNAL-BEHAVIORS section.

Current XML so far:
```xml
{current_xml[-500:] if len(current_xml) > 500 else current_xml}
```

Requirements:
- Runnables needed: {behaviors_info.get('runnable_count', 0)}
- Timing events: {behaviors_info.get('needs_timing_events', True)}
- Behavior descriptions: {', '.join(behaviors_info.get('behavior_descriptions', []))}

Generate the complete <INTERNAL-BEHAVIORS> section including:
1. SWC-INTERNAL-BEHAVIOR with SHORT-NAME
2. EVENTS section with timing events if needed
3. RUNNABLES section with runnable entities
4. Proper data access points and symbols

Close all tags properly including </INTERNAL-BEHAVIORS> and </APPLICATION-SW-COMPONENT-TYPE>.
{retry_note}

XML:"""

        else:
            # 通用块prompt
            return f"""{base_prompt}

Generate XML block for: {block_name}

Current context:
```xml
{current_xml[-300:] if len(current_xml) > 300 else current_xml}
```

Allowed elements: {', '.join(block_context['allowed_elements'])}

Generate a complete, well-formed XML block for this section.
{retry_note}

XML:"""

    def _clean_block_output(self, block_xml: str) -> str:
        """清理块输出"""
        # 移除可能的markdown标记
        block_xml = re.sub(r'^```xml\s*\n?', '', block_xml)
        block_xml = re.sub(r'\n?```\s*$', '', block_xml)

        # 移除前后空白
        block_xml = block_xml.strip()

        # 确保有换行符
        if block_xml and not block_xml.endswith('\n'):
            block_xml += '\n'

        return block_xml

    def _extract_block_path(self, block_xml: str) -> List[str]:
        """从块XML中提取元素路径"""
        path = []
        try:
            # 简单的标签提取
            import re
            # 匹配开始标签（不包括自闭合标签）
            start_tags = re.findall(r'<([A-Z\-]+)(?:\s[^>]*)?>(?![^<]*/>)', block_xml)
            # 匹配结束标签
            end_tags = re.findall(r'</([A-Z\-]+)>', block_xml)

            # 构建路径（只包括未关闭的标签）
            tag_stack = []
            for tag in start_tags:
                if tag not in ['?xml']:  # 排除XML声明
                    tag_stack.append(tag)
                    # 检查是否立即关闭
                    if tag in end_tags:
                        end_tags.remove(tag)
                        tag_stack.pop()

            path = tag_stack

        except Exception as e:
            print(f"⚠️ Path extraction error: {e}")

        return path

    def _validate_block(self, block_xml: str, block_name: str,
                        current_path: List[str]) -> bool:
        """验证生成的块是否有效"""
        # 基本XML格式检查
        if not block_xml or len(block_xml.strip()) < 10:
            return False

        # 检查是否有平衡的标签
        open_tags = re.findall(r'<([A-Z\-]+)(?:\s[^>]*)?>(?![^<]*/>)', block_xml)
        close_tags = re.findall(r'</([A-Z\-]+)>', block_xml)

        # 不需要完全平衡（块可能有未关闭的标签）
        # 但是关闭标签不应该多于开启标签
        tag_count = defaultdict(int)
        for tag in open_tags:
            tag_count[tag] += 1
        for tag in close_tags:
            tag_count[tag] -= 1

        for tag, count in tag_count.items():
            if count < 0:  # 关闭标签多于开启标签
                print(f"⚠️ Validation failed: unbalanced tag {tag}")
                return False

        # 检查是否包含预期的元素
        block_def = self.block_definitions[block_name]
        has_expected_element = False
        for expected in block_def.start_elements:
            if f"<{expected}" in block_xml:
                has_expected_element = True
                break

        if not has_expected_element:
            print(f"⚠️ Validation failed: missing expected elements")
            return False

        return True

    def _integrate_block(self, current_xml: str, block_xml: str,
                         current_path: List[str]) -> str:
        """将块集成到整体XML中"""
        # 计算缩进
        indent_level = len(current_path)

        # 如果块已经有正确的缩进，直接添加
        if block_xml.startswith('  ' * indent_level):
            return current_xml + block_xml

        # 否则调整缩进
        lines = block_xml.split('\n')
        adjusted_lines = []

        for line in lines:
            if line.strip():  # 非空行
                # 检测当前行的缩进级别
                current_indent = len(line) - len(line.lstrip())
                current_indent_level = current_indent // 2

                # 调整缩进
                new_indent_level = indent_level + current_indent_level
                new_line = '  ' * new_indent_level + line.strip()
                adjusted_lines.append(new_line)
            else:
                adjusted_lines.append('')  # 保留空行

        adjusted_block = '\n'.join(adjusted_lines)
        if adjusted_block and not adjusted_block.endswith('\n'):
            adjusted_block += '\n'

        return current_xml + adjusted_block

    def _is_generation_complete(self, path: List[str], xml: str) -> bool:
        """检查生成是否完成"""
        # 检查是否回到根（路径为空）
        if not path and "</APPLICATION-SW-COMPONENT-TYPE>" in xml:
            return True

        # 检查是否在接受状态
        state = " ".join(path) if path else ""
        if hasattr(self.fsm_engine, 'accepting_states'):
            if state in self.fsm_engine.accepting_states:
                return True

        # 检查XML是否已经完整
        if xml.strip().endswith("</APPLICATION-SW-COMPONENT-TYPE>"):
            return True

        return False

    def _finalize_xml(self, xml_content: str, path: List[str]) -> str:
        """完成XML结构"""
        # 如果还有未关闭的标签，关闭它们
        if path:
            closing_tags = []
            for i in range(len(path) - 1, -1, -1):
                tag = path[i]
                indent = "  " * i
                closing_tags.append(f"{indent}</{tag}>")

            if closing_tags:
                xml_content += "\n".join(closing_tags) + "\n"

        # 确保根标签关闭
        if not xml_content.strip().endswith("</APPLICATION-SW-COMPONENT-TYPE>"):
            xml_content += "</APPLICATION-SW-COMPONENT-TYPE>\n"

        return xml_content.strip()

    def _update_stats(self, generation_time: float, blocks_count: int,
                      llm_calls: int, success: bool):
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

    def get_statistics(self) -> Dict[str, Any]:
        """获取策略统计信息"""
        return {
            **self.stats,
            'success_rate': (
                self.stats['successful_generations'] / self.stats['total_requests']
                if self.stats['total_requests'] > 0 else 0
            ),
            'efficiency_gain': {
                'vs_token_strategy': f"{40 / self.stats['avg_llm_calls']:.1f}x"
                if self.stats['avg_llm_calls'] > 0 else "N/A",
                'avg_chars_per_call': "~500-800"
            }
        }