# src/client/constraint_sender.py - 支持配置化提示词
import uuid
from typing import Dict, List

from src.client.constraint_preparer import ConstraintPreparer
from src.client.constraint_models import ConstraintInfo, EnhancedGenerationRequest
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ConstraintSender:
    """约束信息发送器 - 支持配置化提示词"""

    def __init__(self, artifacts_dir: str, config: Dict = None):
        self.constraint_preparer = ConstraintPreparer(artifacts_dir)
        self.config = config or {}

        # 提取策略配置
        self.strategy_config = self.config.get("constraint_strategy", {})
        self.generation_config = self.config.get("generation", {})
        self.constraint_refs = self.config.get("constraint_references", {})

        # 🔥 提取提示词配置
        self.prompts_config = self.config.get("prompts", {})

        logger.info(f"ConstraintSender initialized with strategy: {self.strategy_config.get('mode', 'gbnf_priority')}")

    # 在 constraint_sender.py 中修改 build_enhanced_request 方法

    def build_enhanced_request(
            self,
            prompt: str,
            autosar_context: Dict = None,
            xml_context: List[str] = None,
            constraint_level: str = "mixed",
            prompt_type: str = "component_level",
            example_xml: str = None,
            **generation_params
    ) -> EnhancedGenerationRequest:
        """构建增强的生成请求 - 传递提示词配置"""
        request_id = str(uuid.uuid4())

        # 🔥 根据配置构建提示词
        enhanced_prompt = self._build_prompt_from_config(
            prompt, autosar_context, prompt_type, example_xml
        )

        # 根据配置构建约束信息
        constraint_info = self._build_constraint_info_from_config(constraint_level, xml_context)

        # 应用配置中的生成参数
        merged_params = self._merge_generation_params(generation_params)

        # 🔥 准备完整的autosar_context，包含提示词配置
        enhanced_autosar_context = autosar_context or {}

        # 🔥 添加提示词配置到上下文中
        enhanced_autosar_context['prompt_config'] = self.prompts_config
        enhanced_autosar_context['used_prompt_type'] = prompt_type

        # 如果有示例XML，也传递
        if example_xml:
            enhanced_autosar_context['example_xml'] = example_xml

        request = EnhancedGenerationRequest(
            request_id=request_id,
            prompt=enhanced_prompt,
            constraint_info=constraint_info,
            autosar_context=enhanced_autosar_context,  # 🔥 使用增强的上下文
            **merged_params
        )

        strategy_mode = self.strategy_config.get("mode", "gbnf_priority")
        logger.info(f"Built enhanced request {request_id} with strategy: {strategy_mode}")
        logger.info(f"Prompt type: {prompt_type}, length: {len(enhanced_prompt)}")
        logger.info(f"🎯 Prompt config included: {len(self.prompts_config)} templates")

        return request

    def _build_prompt_from_config(
            self,
            task: str,
            autosar_context: Dict,
            prompt_type: str,
            example_xml: str = None
    ) -> str:
        """🔥 修复：根据配置构建提示词 - 处理列表和字符串模板"""

        # 获取提示词模板
        prompt_template = self.prompts_config.get(prompt_type)

        # 🔥 修复：处理空值情况
        if not prompt_template or (isinstance(prompt_template, str) and not prompt_template.strip()):
            logger.warning(f"Prompt type '{prompt_type}' is empty or not found, using task directly")
            return task  # 直接使用原始task

        # 如果是列表格式（通常是YAML批量处理）
        if isinstance(prompt_template, list):
            logger.info(f"Found list format prompt with {len(prompt_template)} items")
            # 如果task就是列表中的一个，直接返回
            if task in prompt_template:
                logger.info("✅ Using exact match from prompt list")
                return task
            else:
                # 否则直接返回task
                logger.info("Using task as-is for list format")
                return task

        # 字符串模板处理
        if isinstance(prompt_template, str):
            # 检查是否包含格式占位符
            if '{task}' in prompt_template or '{context}' in prompt_template:
                # 构建上下文信息
                context = self._build_context_string(autosar_context)

                # 填充模板
                try:
                    if prompt_type == "with_example_xml" and example_xml:
                        enhanced_prompt = prompt_template.format(
                            task=task,
                            context=context,
                            example_xml=example_xml
                        )
                    else:
                        enhanced_prompt = prompt_template.format(
                            task=task,
                            context=context
                        )

                    logger.info(f"✅ Prompt built from string template: {prompt_type}")
                    return enhanced_prompt

                except KeyError as e:
                    logger.error(f"❌ Template formatting error: {e}")
                    return task  # 返回原始task
            else:
                # 如果是普通字符串且不包含占位符，直接返回
                logger.info("✅ Using string template as-is")
                return prompt_template

        # 兜底逻辑：直接返回task
        logger.warning("Unknown prompt template format, using task as-is")
        return task

    def _build_context_string(self, autosar_context: Dict) -> str:
        """构建上下文字符串"""
        if not autosar_context:
            return "Standard AUTOSAR component"

        parts = []
        if autosar_context.get('domain'):
            parts.append(f"Domain: {autosar_context['domain']}")
        if autosar_context.get('component_type'):
            parts.append(f"Type: {autosar_context['component_type']}")

        return ", ".join(parts) if parts else "Standard AUTOSAR component"

    def _get_default_prompt(self, task: str, autosar_context: Dict) -> str:
        """默认提示词"""
        context = self._build_context_string(autosar_context)

        return f"""Generate complete AUTOSAR APPLICATION-SW-COMPONENT-TYPE content.

            Context: {context}
            Task: {task}

            Requirements:
            - Start with <APPLICATION-SW-COMPONENT-TYPE> tag
            - Include SHORT-NAME element with descriptive name
            - Add PORTS section with both R-PORT-PROTOTYPE and P-PORT-PROTOTYPE
            - Include INTERNAL-BEHAVIOR with RUNNABLES and EVENTS
            - Use proper AUTOSAR R4.0 structure
            - End with </APPLICATION-SW-COMPONENT-TYPE>

            Generate complete component XML:"""

    def _build_constraint_info_from_config(self, constraint_level: str, xml_context: List[str]) -> ConstraintInfo:
        """根据配置构建约束信息"""
        constraint_info = ConstraintInfo()

        # 根据约束级别和策略模式设置引用
        strategy_mode = self.strategy_config.get("mode", "gbnf_priority")

        # 🔥 修复：专门处理 dynamic_gbnf 策略
        if strategy_mode == "dynamic_gbnf":
            # 动态GBNF策略需要GBNF引用
            constraint_info.gbnf_ref = self.constraint_refs.get("gbnf_ref", "autosar")
            constraint_info.gbnf_enabled = True
            logger.info(f"🎯 Setting GBNF ref for dynamic_gbnf: {constraint_info.gbnf_ref}")

        # 🔥 处理 block_level_fsm 策略
        elif strategy_mode == "block_level_fsm":
            constraint_info.fsm_ref = self.constraint_refs.get("fsm_ref", "autosar")
            constraint_info.fsm_enabled = True
            logger.info(f"🎯 Setting FSM ref for block_level_fsm: {constraint_info.fsm_ref}")

        # 原有的mixed/full逻辑
        elif constraint_level in ["mixed", "full"]:
            # 根据策略模式决定启用哪些约束
            if strategy_mode in ["gbnf_priority", "hybrid"]:
                constraint_info.gbnf_ref = self.constraint_refs.get("gbnf_ref", "autosar")
                constraint_info.gbnf_enabled = True

            if strategy_mode in ["iterative_fsm", "hybrid"]:
                constraint_info.fsm_ref = self.constraint_refs.get("fsm_ref", "autosar")
                constraint_info.fsm_enabled = True

        # 无约束模式
        if strategy_mode == "unconstrained":
            constraint_info.gbnf_ref = None
            constraint_info.fsm_ref = None
            constraint_info.fsm_enabled = False
            constraint_info.gbnf_enabled = False

        # 设置约束源信息
        constraint_info.constraint_version = "7.0.0"
        constraint_info.constraint_source = f"config_driven_{strategy_mode}"

        # 提取当前状态
        current_state = self._extract_current_state(xml_context)
        constraint_info.current_state = current_state

        logger.info(
            f"✅ Constraint info built for {strategy_mode}: fsm_ref={constraint_info.fsm_ref}, gbnf_ref={constraint_info.gbnf_ref}")
        logger.info(f"   fsm_enabled={constraint_info.fsm_enabled}, gbnf_enabled={constraint_info.gbnf_enabled}")

        return constraint_info

    def _merge_generation_params(self, generation_params: Dict) -> Dict:
        """合并生成参数 - 配置优先"""
        # 从配置获取默认值
        defaults = {
            "max_tokens": self.generation_config.get("default_max_tokens", 8000),
            "temperature": self.generation_config.get("default_temperature", 0.3),
            "top_p": self.generation_config.get("default_top_p", 0.9),
            "frequency_penalty": self.generation_config.get("default_frequency_penalty", 0.1),
            "presence_penalty": self.generation_config.get("default_presence_penalty", 0.1)
        }

        # 策略特定的参数覆盖
        strategy_mode = self.strategy_config.get("mode", "gbnf_priority")
        strategy_specific = self.strategy_config.get(strategy_mode, {})

        if strategy_specific:
            # 应用策略特定参数
            if "temperature" in strategy_specific:
                defaults["temperature"] = strategy_specific["temperature"]
            if "max_tokens" in strategy_specific:
                defaults["max_tokens"] = strategy_specific["max_tokens"]

        # 用户提供的参数具有最高优先级
        defaults.update(generation_params)

        logger.info(f"Generation params: {defaults}")
        return defaults

    def _extract_current_state(self, xml_context: List[str]) -> str:
        """从XML上下文提取当前状态"""
        if not xml_context:
            return "START"

        last_xml = xml_context[-1]
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(last_xml)
            return root.tag
        except:
            return "START"

    def get_constraint_summary(self) -> Dict:
        """获取约束制品摘要"""
        base_summary = self.constraint_preparer.get_constraint_summary()

        # 添加策略配置信息
        base_summary.update({
            "strategy_mode": self.strategy_config.get("mode", "gbnf_priority"),
            "strategy_config": self.strategy_config,
            "constraint_references": self.constraint_refs,
            "available_prompts": list(self.prompts_config.keys())
        })

        return base_summary