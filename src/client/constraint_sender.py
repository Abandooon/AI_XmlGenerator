# src/client/constraint_sender.py - 更新版本，支持策略配置
import json
import uuid
from typing import Dict, List, Optional
from pathlib import Path

from src.client.constraint_preparer import ConstraintPreparer
from src.models.constraint_models import ConstraintInfo, EnhancedGenerationRequest
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ConstraintSender:
    """约束信息发送器 - 支持策略配置"""

    def __init__(self, artifacts_dir: str, config: Dict = None):
        # 使用ConstraintPreparer来加载约束制品
        self.constraint_preparer = ConstraintPreparer(artifacts_dir)
        self.config = config or {}

        # 🔥 提取策略配置
        self.strategy_config = self.config.get("constraint_strategy", {})
        self.generation_config = self.config.get("generation", {})
        self.constraint_refs = self.config.get("constraint_references", {})

        logger.info(f"ConstraintSender initialized with strategy: {self.strategy_config.get('mode', 'gbnf_priority')}")

    def build_enhanced_request(
            self,
            prompt: str,
            autosar_context: Dict = None,
            xml_context: List[str] = None,
            constraint_level: str = "mixed",
            **generation_params
    ) -> EnhancedGenerationRequest:
        """构建增强的生成请求 - 支持策略配置"""
        request_id = str(uuid.uuid4())

        # 🔥 根据配置构建约束信息
        constraint_info = self._build_constraint_info_from_config(constraint_level, xml_context)

        # 🔥 应用配置中的生成参数
        merged_params = self._merge_generation_params(generation_params)

        request = EnhancedGenerationRequest(
            request_id=request_id,
            prompt=prompt,
            constraint_info=constraint_info,
            autosar_context=autosar_context or {},
            **merged_params
        )

        strategy_mode = self.strategy_config.get("mode", "gbnf_priority")
        logger.info(f"Built enhanced request {request_id} with strategy: {strategy_mode}")
        return request

    def _build_constraint_info_from_config(self, constraint_level: str, xml_context: List[str]) -> ConstraintInfo:
        """根据配置构建约束信息"""
        constraint_info = ConstraintInfo()

        # 🔥 根据约束级别和策略模式设置引用
        strategy_mode = self.strategy_config.get("mode", "gbnf_priority")

        if constraint_level in ["mixed", "full"]:
            # 根据策略模式决定启用哪些约束
            if strategy_mode in ["gbnf_priority", "hybrid"]:
                constraint_info.gbnf_ref = self.constraint_refs.get("gbnf_ref", "autosar")

            if strategy_mode in ["iterative_fsm", "hybrid"]:
                constraint_info.fsm_ref = self.constraint_refs.get("fsm_ref", "autosar")

            if strategy_mode == "unconstrained":
                # 无约束模式
                constraint_info.gbnf_ref = None
                constraint_info.fsm_ref = None

        # 设置约束源信息
        constraint_info.constraint_version = "7.0.0"
        constraint_info.constraint_source = f"config_driven_{strategy_mode}"

        # 提取当前状态
        current_state = self._extract_current_state(xml_context)
        constraint_info.current_state = current_state

        logger.info(f"Constraint info built: fsm_ref={constraint_info.fsm_ref}, gbnf_ref={constraint_info.gbnf_ref}")
        return constraint_info

    def _merge_generation_params(self, generation_params: Dict) -> Dict:
        """合并生成参数 - 配置优先"""
        # 从配置获取默认值
        defaults = {
            "max_tokens": self.generation_config.get("default_max_tokens", 8000),  # 🔥 默认8000
            "temperature": self.generation_config.get("default_temperature", 0.3),
            "top_p": self.generation_config.get("default_top_p", 0.9),
            "frequency_penalty": self.generation_config.get("default_frequency_penalty", 0.1),
            "presence_penalty": self.generation_config.get("default_presence_penalty", 0.1)
        }

        # 🔥 策略特定的参数覆盖
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
            "constraint_references": self.constraint_refs
        })

        return base_summary


# src/client/cloud_client.py - 更新版本，支持策略配置
import aiohttp
import asyncio
import time
import json
from typing import Optional, Dict, Any, List

from ..models.constraint_models import EnhancedGenerationRequest, CloudGenerationResponse
from ..utils.logger import get_logger

logger = get_logger(__name__)


class CloudServiceClient:
    """云端服务客户端 - 支持策略配置"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.cloud_config = config["cloud_service"]
        self.endpoint = self.cloud_config["internal_endpoint"]
        self.timeout = self.cloud_config["timeout"]
        self.api_type = self.cloud_config.get("api_type", "enhanced")
        self.model_name = self.cloud_config.get("model_name", "")
        self.session: Optional[aiohttp.ClientSession] = None

        # 🔥 策略配置
        self.strategy_config = config.get("constraint_strategy", {})

        logger.info(
            f"CloudServiceClient initialized with strategy: {self.strategy_config.get('mode', 'gbnf_priority')}")

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def connect(self):
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)

            # 🔥 发送策略配置到云端服务
            await self._configure_cloud_strategy()

            logger.info(f"Connected to cloud service at {self.endpoint}")

    async def _configure_cloud_strategy(self):
        """配置云端服务的策略"""
        try:
            strategy_payload = {
                "mode": self.strategy_config.get("mode", "gbnf_priority"),
                "debug": {"enabled": False},  # 🔥 确保调试关闭
                **self.strategy_config
            }

            async with self.session.post(
                    f"{self.endpoint}/update_strategy",
                    json=strategy_payload,
                    timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    logger.info(f"Cloud strategy configured: {strategy_payload['mode']}")
                else:
                    logger.warning(f"Failed to configure cloud strategy: {response.status}")
        except Exception as e:
            logger.warning(f"Strategy configuration failed: {e}")

    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None

    async def enhanced_generate(self, request: EnhancedGenerationRequest) -> CloudGenerationResponse:
        """调用增强生成接口"""
        try:
            logger.info(f"Sending enhanced generation request: {request.request_id}")

            # 转换为字典
            request_dict = request.dict()

            async with self.session.post(
                    f"{self.endpoint}/enhanced_generate",
                    json=request_dict,
                    headers={"Content-Type": "application/json"}
            ) as response:

                if response.status == 200:
                    response_data = await response.json()
                    logger.info(f"Generation successful: {request.request_id}")
                    return CloudGenerationResponse(**response_data)
                else:
                    error_text = await response.text()
                    logger.error(f"Generation failed: {response.status} - {error_text}")
                    return CloudGenerationResponse(
                        request_id=request.request_id,
                        success=False,
                        error_message=f"HTTP {response.status}: {error_text}"
                    )

        except Exception as e:
            logger.error(f"Enhanced generation error: {e}")
            return CloudGenerationResponse(
                request_id=request.request_id,
                success=False,
                error_message=f"Client error: {str(e)}"
            )

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            async with self.session.get(f"{self.endpoint}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    return {"status": "unhealthy", "http_status": response.status}
        except Exception as e:
            return {"status": "error", "error": str(e)}


# src/client/full_client.py - 更新版本，支持策略配置
import asyncio
import time
from typing import Dict, List, Optional

from .constraint_sender import ConstraintSender
from .cloud_client import CloudServiceClient
from ..validation.local_validator import LocalValidator
from ..models.constraint_models import EnhancedGenerationRequest, CloudGenerationResponse
from ..models.data_models import ClientResponse, ValidationResult
from ..utils.logger import get_logger

logger = get_logger(__name__)


class FullAutosarClient:
    """完整的AUTOSAR客户端 - 支持策略配置"""

    def __init__(self, config: Dict):
        """
        初始化完整客户端

        Args:
            config: 客户端配置
        """
        self.config = config

        # 🔥 传递完整配置到约束发送器
        self.constraint_sender = ConstraintSender(
            config["local_validation"]["artifacts_dir"],
            config  # 传递完整配置
        )

        self.local_validator = LocalValidator(
            config["local_validation"]["artifacts_dir"]
        )

        # 🔥 提取策略配置
        self.strategy_config = config.get("constraint_strategy", {})

        logger.info(f"FullAutosarClient initialized with strategy: {self.strategy_config.get('mode', 'gbnf_priority')}")

    async def generate_and_validate_full(
            self,
            prompt: str,
            autosar_context: Dict = None,
            xml_context: List[str] = None,
            constraint_level: str = "mixed",
            **generation_params
    ) -> ClientResponse:
        """完整的生成和验证流程 - 支持策略配置"""
        start_time = time.time()

        # 🔥 构建增强请求（会自动应用策略配置）
        enhanced_request = self.constraint_sender.build_enhanced_request(
            prompt=prompt,
            autosar_context=autosar_context,
            xml_context=xml_context,
            constraint_level=constraint_level,
            **generation_params
        )

        response = ClientResponse(
            request=enhanced_request,
            success=False
        )

        try:
            # 使用云端服务生成
            async with CloudServiceClient(self.config) as cloud_client:
                cloud_response = await cloud_client.enhanced_generate(enhanced_request)

                if cloud_response and cloud_response.success:
                    logger.info(f"Generation successful: {len(cloud_response.generated_xml)} chars")
                    logger.info(f"Strategy used: {cloud_response.model_info.get('constraint_strategy', 'unknown')}")

                    response.generation = self._convert_cloud_response(cloud_response)

                    # 本地验证
                    if self.config["local_validation"]["enabled"]:
                        validation_result = self.local_validator.validate_xml(
                            cloud_response.generated_xml,
                            self.config["local_validation"]["validation_level"]
                        )
                        response.validation = validation_result

                    response.success = True
                else:
                    response.error = cloud_response.error_message if cloud_response else "Cloud generation failed"

        except Exception as e:
            response.error = str(e)
            logger.error(f"Full generation process failed: {e}")

        response.execution_time = time.time() - start_time
        return response

    def _convert_cloud_response(self, cloud_response: CloudGenerationResponse):
        """将云端响应转换为标准生成响应格式"""
        from ..models.data_models import GenerationResponse

        return GenerationResponse(
            request_id=cloud_response.request_id,
            generated_xml=cloud_response.generated_xml,
            metadata={
                "constraints_applied": cloud_response.constraints_applied,
                "constraint_violations": cloud_response.constraint_violations,
                "constraint_strategy": cloud_response.model_info.get("constraint_strategy", "unknown"),
                "strategy_details": cloud_response.model_info.get("strategy_details", {}),
                "raw_output_length": len(cloud_response.raw_output) if cloud_response.raw_output else 0
            },
            performance={
                "generation_time": cloud_response.generation_time,
                "model_info": cloud_response.model_info
            }
        )

    def analyze_constraint_effectiveness(self, response: ClientResponse) -> Dict:
        """分析约束效果 - 增强版本"""
        analysis = {
            "constraints_sent": False,
            "constraints_applied": {},
            "constraint_violations": [],
            "validation_passed": False,
            "effectiveness_score": 0.0,
            "strategy_used": "unknown"
        }

        if response.generation and response.generation.metadata:
            metadata = response.generation.metadata

            analysis["constraints_sent"] = True
            analysis["constraints_applied"] = metadata.get("constraints_applied", {})
            analysis["constraint_violations"] = metadata.get("constraint_violations", [])
            analysis["strategy_used"] = metadata.get("constraint_strategy", "unknown")

        if response.validation:
            analysis["validation_passed"] = response.validation.overall_valid

        # 🔥 改进的效果评分
        applied_count = sum(1 for applied in analysis["constraints_applied"].values() if applied)
        total_constraints = len(analysis["constraints_applied"])
        violation_count = len(analysis["constraint_violations"])

        if total_constraints > 0:
            constraint_score = applied_count / total_constraints
            violation_penalty = min(violation_count * 0.1, 0.5)

            # 策略加权
            strategy_bonus = 0.1 if analysis["strategy_used"] in ["gbnf_priority", "hybrid"] else 0.0

            analysis["effectiveness_score"] = max(0.0, constraint_score - violation_penalty + strategy_bonus)

        return analysis