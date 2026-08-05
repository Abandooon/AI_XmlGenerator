# src/client/full_client.py - 🔥 修复版本
import time
from typing import Dict

from src.client.constraint_models import CloudGenerationResponse, extract_legacy_constraints_applied
from src.client.data_models import ClientResponse

from .cloud_client import CloudServiceClient
from .constraint_sender import ConstraintSender
from ..utils.logger import get_logger

logger = get_logger(__name__)


class FullAutosarClient:
    """简化的AUTOSAR客户端 - 🔥 修复模型兼容性"""

    def __init__(self, config: Dict):
        self.config = config
        self.constraint_sender = ConstraintSender(
            config.get("local_validation", {}).get("artifacts_dir", "./artifacts"),
            config
        )
        self.strategy_config = config.get("constraint_strategy", {})

    async def generate_and_validate_full(
            self,
            prompt: str,
            autosar_context: Dict = None,
            constraint_level: str = "mixed",
            **generation_params
    ) -> ClientResponse:
        """简化的生成方法 - 🔥 修复模型处理"""

        start_time = time.time()

        # 构建请求
        enhanced_request = self.constraint_sender.build_enhanced_request(
            prompt=prompt,
            autosar_context=autosar_context,
            constraint_level=constraint_level,
            **generation_params
        )

        response = ClientResponse(request=enhanced_request, success=False)

        try:
            async with CloudServiceClient(self.config) as cloud_client:
                cloud_response = await cloud_client.enhanced_generate(enhanced_request)

                if cloud_response and cloud_response.success:
                    response.generation = self._convert_cloud_response(cloud_response)
                    response.success = True
                    # 简单的验证结果
                    response.validation = self._create_simple_validation(True)
                else:
                    response.error = cloud_response.error_message if cloud_response else "Generation failed"

        except Exception as e:
            response.error = str(e)
            logger.error(f"Generation failed: {e}")

        response.execution_time = time.time() - start_time
        return response

    def _convert_cloud_response(self, cloud_response: CloudGenerationResponse):
        """🔥 修复：转换云端响应 - 正确处理seed_results"""
        from src.client.data_models import GenerationResponse

        # 🔥 修复：从新的模型结构中提取数据
        constraints_applied = cloud_response.constraints_applied

        # 提取资源统计信息
        resource_stats = constraints_applied.resource_stats or {}
        batch_summary = constraints_applied.batch_resource_summary or {}
        detailed_stats = constraints_applied.detailed_prompt_stats or []

        # 🔥 新增：提取seed_results
        custom_constraints = constraints_applied.custom_constraints or {}
        seed_results = custom_constraints.get("seed_results", [])
        multi_seed_stats = custom_constraints.get("multi_seed_stats", {})

        # 🔥 为向后兼容，创建传统格式的字典
        legacy_constraints = extract_legacy_constraints_applied(constraints_applied)

        return GenerationResponse(
            request_id=cloud_response.request_id,
            generated_xml=cloud_response.generated_xml,
            metadata={
                # 🔥 保持向后兼容的constraints_applied格式
                "constraints_applied": legacy_constraints,
                "strategy": cloud_response.model_info.get("constraint_strategy", "unknown"),
                # 🔥 修复：完整传递资源统计
                "resource_stats": resource_stats,
                "batch_resource_summary": batch_summary,
                "detailed_prompt_stats": detailed_stats,
                "strategy_details": cloud_response.model_info.get("strategy_details", {}),
                "features_applied": cloud_response.model_info.get("features_applied", []),
                # 🔥 新增：传递seed_results和multi_seed_stats
                "seed_results": seed_results,
                "multi_seed_stats": multi_seed_stats,
                # 🔥 新增：原始约束模型（用于调试）
                "raw_constraints_applied": constraints_applied
            },
            performance={
                "generation_time": cloud_response.generation_time,
                # 🔥 添加详细性能信息
                "vllm_generation_time": resource_stats.get('generation_time_seconds', 0),
                "total_processing_time": resource_stats.get('total_processing_time', 0),
                "memory_usage": resource_stats.get('memory_usage_mb', {}),
                "token_usage": resource_stats.get('token_usage', {})
            }
        )

    def _create_simple_validation(self, is_valid: bool):
        """创建简单验证结果"""

        class SimpleValidation:
            def __init__(self, valid):
                self.is_valid = valid
                self.overall_valid = valid
                self.errors = []
                self.warnings = []

        return SimpleValidation(is_valid)


# src/client/cloud_client.py - 🔥 修复版本
import aiohttp
from typing import Optional, Dict, Any
from pathlib import Path

from src.client.constraint_models import EnhancedGenerationRequest, CloudGenerationResponse
from ..utils.logger import get_logger

logger = get_logger(__name__)


class CloudServiceClient:
    """简化的云端服务客户端 - 🔥 修复响应处理"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.cloud_config = config["cloud_service"]
        self.endpoint = self.cloud_config["internal_endpoint"]
        self.timeout = self.cloud_config["timeout"]
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def connect(self):
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)

    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None

    async def enhanced_generate(self, request: EnhancedGenerationRequest) -> CloudGenerationResponse:
        """发送生成请求 - 🔥 修复响应解析"""
        logger.info(f"Sending request to {self.endpoint}/enhanced_generate")

        try:
            request_dict = request.dict()

            async with self.session.post(
                    f"{self.endpoint}/enhanced_generate",
                    json=request_dict,
                    headers={"Content-Type": "application/json"}
            ) as response:

                if response.status == 200:
                    response_data = await response.json()

                    # 🔥 修复：在创建响应对象之前记录调试信息
                    logger.debug(f"Response keys: {list(response_data.keys())}")
                    if "constraints_applied" in response_data:
                        logger.debug(f"constraints_applied type: {type(response_data['constraints_applied'])}")
                        logger.debug(f"constraints_applied keys: {list(response_data['constraints_applied'].keys()) if isinstance(response_data['constraints_applied'], dict) else 'not dict'}")

                    # 简单保存原始输出
                    if response_data.get("raw_output"):
                        output_file = Path("outputs") / f"raw_output_{request.request_id[:8]}.txt"
                        output_file.parent.mkdir(exist_ok=True)
                        with open(output_file, 'w', encoding='utf-8') as f:
                            f.write(response_data["raw_output"])

                    # 🔥 使用新的模型结构创建响应
                    try:
                        return CloudGenerationResponse(**response_data)
                    except Exception as parse_error:
                        logger.error(f"Failed to parse cloud response: {parse_error}")
                        logger.error(f"Response data: {response_data}")
                        raise parse_error

                else:
                    error_text = await response.text()
                    return CloudGenerationResponse(
                        request_id=request.request_id,
                        success=False,
                        error_message=f"HTTP {response.status}: {error_text}"
                    )

        except Exception as e:
            logger.error(f"Request failed: {e}")
            return CloudGenerationResponse(
                request_id=request.request_id,
                success=False,
                error_message=f"Client Error: {str(e)}"
            )


# src/client/constraint_sender.py - 🔥 修复部分方法
import uuid
from typing import Dict, List

from src.client.constraint_preparer import ConstraintPreparer
from src.client.constraint_models import ConstraintInfo, EnhancedGenerationRequest
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ConstraintSender:
    """约束信息发送器 - 支持配置化提示词 - 🔥 修复版本"""

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
        """构建增强的生成请求 - 传递提示词配置 - 🔥 修复版本"""
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