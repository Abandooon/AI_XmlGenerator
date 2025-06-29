# src/client/full_client.py - 简化版本，支持配置化提示词
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
    """完整的AUTOSAR客户端 - 简化版本，支持配置化提示词"""

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

        # 本地验证器（可选）
        if config["local_validation"]["enabled"]:
            self.local_validator = LocalValidator(
                config["local_validation"]["artifacts_dir"]
            )
        else:
            self.local_validator = None

        # 提取策略配置
        self.strategy_config = config.get("constraint_strategy", {})

        # 🔥 后处理配置
        self.post_processing_config = config.get("post_processing", {})

        logger.info(f"FullAutosarClient initialized with strategy: {self.strategy_config.get('mode', 'gbnf_priority')}")
        logger.info(
            f"Post-processing: {'enabled' if self.post_processing_config.get('enabled', False) else 'disabled'}")

    async def generate_and_validate_full(
            self,
            prompt: str,
            autosar_context: Dict = None,
            xml_context: List[str] = None,
            constraint_level: str = "mixed",
            prompt_type: str = "component_level",  # 🔥 新增：提示词类型参数
            example_xml: str = None,  # 🔥 新增：示例XML参数
            **generation_params
    ) -> ClientResponse:
        """完整的生成和验证流程 - 简化版本"""
        start_time = time.time()

        # 🔥 构建增强请求（支持配置化提示词）
        enhanced_request = self.constraint_sender.build_enhanced_request(
            prompt=prompt,
            autosar_context=autosar_context,
            xml_context=xml_context,
            constraint_level=constraint_level,
            prompt_type=prompt_type,  # 🔥 传递提示词类型
            example_xml=example_xml,  # 🔥 传递示例XML
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

                    # 🔥 可选的本地验证
                    if self.local_validator and self.config["local_validation"]["enabled"]:
                        validation_result = self.local_validator.validate_xml(
                            cloud_response.generated_xml,
                            self.config["local_validation"]["validation_level"]
                        )
                        response.validation = validation_result
                        logger.info(
                            f"Validation completed: {'passed' if validation_result.overall_valid else 'failed'}")

                    response.success = True
                else:
                    response.error = cloud_response.error_message if cloud_response else "Cloud generation failed"

        except Exception as e:
            response.error = str(e)
            logger.error(f"Full generation process failed: {e}")

        response.execution_time = time.time() - start_time
        return response

    def _convert_cloud_response(self, cloud_response: CloudGenerationResponse):
        """将云端响应转换为标准生成响应格式 - 简化版本"""
        from ..models.data_models import GenerationResponse

        return GenerationResponse(
            request_id=cloud_response.request_id,
            generated_xml=cloud_response.generated_xml,  # 🔥 直接使用原始输出
            metadata={
                "constraints_applied": cloud_response.constraints_applied,
                "constraint_violations": cloud_response.constraint_violations,
                "constraint_strategy": cloud_response.model_info.get("constraint_strategy", "unknown"),
                "strategy_details": cloud_response.model_info.get("strategy_details", {}),
                "raw_output_length": len(cloud_response.raw_output) if cloud_response.raw_output else 0,
                "processing_mode": cloud_response.model_info.get("mode", "standard"),
                "post_processing": cloud_response.model_info.get("post_processing", "enabled")
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
            "strategy_used": "unknown",
            "processing_mode": "unknown"
        }

        if response.generation and response.generation.metadata:
            metadata = response.generation.metadata

            analysis["constraints_sent"] = True
            analysis["constraints_applied"] = metadata.get("constraints_applied", {})
            analysis["constraint_violations"] = metadata.get("constraint_violations", [])
            analysis["strategy_used"] = metadata.get("constraint_strategy", "unknown")
            analysis["processing_mode"] = metadata.get("processing_mode", "standard")

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

            # 处理模式加权
            mode_bonus = 0.05 if analysis["processing_mode"] == "raw_output_only" else 0.0

            analysis["effectiveness_score"] = max(0.0,
                                                  constraint_score - violation_penalty + strategy_bonus + mode_bonus)

        return analysis

    def get_available_prompt_types(self) -> List[str]:
        """获取可用的提示词类型"""
        prompts_config = self.config.get("prompts", {})
        return list(prompts_config.keys())

    def preview_prompt(self,
                       prompt: str,
                       prompt_type: str = "component_level",
                       autosar_context: Dict = None,
                       example_xml: str = None) -> str:
        """预览生成的提示词（调试用）"""
        try:
            # 创建临时请求来获取提示词
            enhanced_request = self.constraint_sender.build_enhanced_request(
                prompt=prompt,
                autosar_context=autosar_context,
                prompt_type=prompt_type,
                example_xml=example_xml,
                constraint_level="simple"  # 使用simple级别避免约束影响
            )
            return enhanced_request.prompt
        except Exception as e:
            logger.error(f"Failed to preview prompt: {e}")
            return f"Error generating prompt: {str(e)}"