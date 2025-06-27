# src/client/full_client.py
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
    """完整的AUTOSAR客户端 - 支持约束传输和本地验证"""

    def __init__(self, config: Dict):
        """
        初始化完整客户端

        Args:
            config: 客户端配置
        """
        self.config = config

        # 初始化组件
        self.constraint_sender = ConstraintSender(
            config["local_validation"]["artifacts_dir"]
        )
        self.local_validator = LocalValidator(
            config["local_validation"]["artifacts_dir"]
        )

    # src/client/full_client.py - 关键部分修改
    async def generate_and_validate_full(
            self,
            prompt: str,
            autosar_context: Dict = None,
            xml_context: List[str] = None,
            constraint_level: str = "mixed",
            **generation_params
    ) -> ClientResponse:
        """完整的生成和验证流程"""
        start_time = time.time()

        # 构建增强请求
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
            # 简化：直接使用CloudServiceClient的enhanced_generate方法
            async with CloudServiceClient(self.config) as cloud_client:
                cloud_response = await cloud_client.enhanced_generate(enhanced_request)

                if cloud_response and cloud_response.success:
                    logger.info(f"Received generation result: {len(cloud_response.generated_xml)} chars")

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

    # 删除 _call_enhanced_generation 方法，因为CloudServiceClient已经有了


    def _convert_cloud_response(self, cloud_response: CloudGenerationResponse):
        """将云端响应转换为标准生成响应格式"""
        from ..models.data_models import GenerationResponse

        return GenerationResponse(
            request_id=cloud_response.request_id,
            generated_xml=cloud_response.generated_xml,
            metadata={
                "constraints_applied": cloud_response.constraints_applied,
                "constraint_violations": cloud_response.constraint_violations,
                "raw_output_length": len(cloud_response.raw_output) if cloud_response.raw_output else 0
            },
            performance={
                "generation_time": cloud_response.generation_time,
                "model_info": cloud_response.model_info
            }
        )

    def analyze_constraint_effectiveness(self, response: ClientResponse) -> Dict:
        """分析约束效果"""

        analysis = {
            "constraints_sent": False,
            "constraints_applied": {},
            "constraint_violations": [],
            "validation_passed": False,
            "effectiveness_score": 0.0
        }

        if response.generation and response.generation.metadata:
            metadata = response.generation.metadata

            analysis["constraints_sent"] = True
            analysis["constraints_applied"] = metadata.get("constraints_applied", {})
            analysis["constraint_violations"] = metadata.get("constraint_violations", [])

        if response.validation:
            analysis["validation_passed"] = response.validation.overall_valid

        # 计算效果评分
        applied_count = sum(1 for applied in analysis["constraints_applied"].values() if applied)
        total_constraints = len(analysis["constraints_applied"])
        violation_count = len(analysis["constraint_violations"])

        if total_constraints > 0:
            constraint_score = applied_count / total_constraints
            violation_penalty = min(violation_count * 0.1, 0.5)  # 最多扣0.5分
            analysis["effectiveness_score"] = max(0.0, constraint_score - violation_penalty)

        return analysis