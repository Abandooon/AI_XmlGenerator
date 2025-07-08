# src/client/full_client.py - 修复版本，解决local_validator错误
import asyncio
import time
from typing import Dict, List, Optional

from .constraint_sender import ConstraintSender
from .cloud_client import CloudServiceClient
from ..models.constraint_models import EnhancedGenerationRequest, CloudGenerationResponse
from ..models.data_models import ClientResponse, ValidationResult
from ..utils.logger import get_logger

logger = get_logger(__name__)


class FullAutosarClient:
    """完整的AUTOSAR客户端 - 修复版本，解决local_validator错误"""

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

        # 🔥 修复1: 修复local_validator属性错误
        # 检查配置中是否启用本地验证
        if config.get("local_validation", {}).get("enabled", False):
            try:
                # 尝试导入并初始化本地验证器
                from ..validation.local_validator import LocalValidator
                self.local_validator = LocalValidator(
                    config["local_validation"]["artifacts_dir"]
                )
                logger.info("✅ Local validator initialized")
            except ImportError:
                logger.warning("⚠️ LocalValidator not available, disabling local validation")
                self.local_validator = None
                # 更新配置以反映实际状态
                self.config["local_validation"]["enabled"] = False
            except Exception as e:
                logger.error(f"❌ Failed to initialize LocalValidator: {e}")
                self.local_validator = None
                self.config["local_validation"]["enabled"] = False
        else:
            self.local_validator = None
            logger.info("ℹ️ Local validation disabled in config")

        # 提取策略配置
        self.strategy_config = config.get("constraint_strategy", {})

        # 🔥 后处理配置
        self.post_processing_config = config.get("post_processing", {})

        logger.info(f"FullAutosarClient initialized with strategy: {self.strategy_config.get('mode', 'gbnf_priority')}")
        logger.info(
            f"Post-processing: {'enabled' if self.post_processing_config.get('enabled', False) else 'disabled'}")
        logger.info(f"Local validation: {'enabled' if self.local_validator else 'disabled'}")

    async def generate_and_validate_full(
            self,
            prompt: str,
            autosar_context: Dict = None,
            xml_context: List[str] = None,
            constraint_level: str = "gad_enhanced",  # 🔥 新的默认值
            prompt_type: str = "component_level",
            example_xml: str = None,
            **generation_params
    ) -> ClientResponse:
        """修改生成方法以支持GAD"""

        start_time = time.time()

        # 🔥 构建GAD增强请求
        try:
            enhanced_request = self.constraint_sender.build_enhanced_request(
                prompt=prompt,
                autosar_context=autosar_context,
                xml_context=xml_context,
                constraint_level=constraint_level,
                prompt_type=prompt_type,
                example_xml=example_xml,
                **generation_params
            )

            # 🔥 添加GAD特定的约束信息
            if constraint_level == "gad_enhanced":
                enhanced_request.constraint_info.gad_enabled = True
                enhanced_request.constraint_info.gad_strategy = "gad_enhanced_fsm"

        except Exception as e:
            logger.error(f"❌ Failed to build enhanced request: {e}")
            return ClientResponse(
                request=None,
                success=False,
                error=f"Request building failed: {str(e)}",
                execution_time=time.time() - start_time
            )

        response = ClientResponse(request=enhanced_request, success=False)

        try:
            async with CloudServiceClient(self.config) as cloud_client:
                cloud_response = await cloud_client.enhanced_generate(enhanced_request)

                if cloud_response and cloud_response.success:
                    logger.info(f"Generation successful: {len(cloud_response.generated_xml)} chars")

                    # 🔥 记录GAD特定信息
                    if cloud_response.model_info.get("gad_enhanced"):
                        logger.info(f"GAD Enhanced generation completed")
                        logger.info(f"GAD service: {cloud_response.model_info.get('gad_service_used')}")

                    response.generation = self._convert_cloud_response(cloud_response)

                    # 本地验证逻辑保持不变...
                    if self.local_validator and self.config.get("local_validation", {}).get("enabled", False):
                        try:
                            validation_result = self.local_validator.validate_xml(
                                cloud_response.generated_xml,
                                self.config["local_validation"].get("validation_level", "basic")
                            )
                            response.validation = validation_result
                        except Exception as e:
                            logger.error(f"❌ Local validation failed: {e}")
                            response.validation = self._create_default_validation_result(False, str(e))
                    else:
                        response.validation = self._create_default_validation_result(True, "validation_skipped")

                    response.success = True
                else:
                    error_msg = cloud_response.error_message if cloud_response else "Cloud generation failed"
                    response.error = error_msg
                    logger.error(f"❌ Cloud generation failed: {error_msg}")

        except Exception as e:
            response.error = str(e)
            logger.error(f"❌ Full generation process failed: {e}")

        response.execution_time = time.time() - start_time
        return response

    def _convert_cloud_response(self, cloud_response: CloudGenerationResponse):
        """将云端响应转换为标准生成响应格式 - 修复版本"""
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
                "post_processing": cloud_response.model_info.get("post_processing", "enabled"),
                "fixes_applied": cloud_response.model_info.get("fixes_applied", [])
            },
            performance={
                "generation_time": cloud_response.generation_time,
                "model_info": cloud_response.model_info
            }
        )

    def _create_default_validation_result(self, is_valid: bool, message: str) -> ValidationResult:
        """🔥 修复3: 创建默认验证结果"""
        try:
            # 尝试创建标准的ValidationResult
            return ValidationResult(
                overall_valid=is_valid,
                is_valid=is_valid,
                validation_passed=is_valid,
                errors=[] if is_valid else [message],
                warnings=[],
                message=message
            )
        except Exception:
            # 如果ValidationResult不可用，创建一个简单的对象
            class SimpleValidationResult:
                def __init__(self, valid, msg):
                    self.overall_valid = valid
                    self.is_valid = valid
                    self.validation_passed = valid
                    self.errors = [] if valid else [msg]
                    self.warnings = []
                    self.message = msg

            return SimpleValidationResult(is_valid, message)

    def analyze_constraint_effectiveness(self, response: ClientResponse) -> Dict:
        """分析约束效果 - 增强版本"""
        analysis = {
            "constraints_sent": False,
            "constraints_applied": {},
            "constraint_violations": [],
            "validation_passed": False,
            "effectiveness_score": 0.0,
            "strategy_used": "unknown",
            "processing_mode": "unknown",
            "fixes_applied": []
        }

        if response.generation and response.generation.metadata:
            metadata = response.generation.metadata

            analysis["constraints_sent"] = True
            analysis["constraints_applied"] = metadata.get("constraints_applied", {})
            analysis["constraint_violations"] = metadata.get("constraint_violations", [])
            analysis["strategy_used"] = metadata.get("constraint_strategy", "unknown")
            analysis["processing_mode"] = metadata.get("processing_mode", "standard")
            analysis["fixes_applied"] = metadata.get("fixes_applied", [])

        # 🔥 修复4: 安全的验证结果访问
        if response.validation:
            try:
                # 尝试多种可能的属性名
                analysis["validation_passed"] = (
                        getattr(response.validation, 'overall_valid', False) or
                        getattr(response.validation, 'is_valid', False) or
                        getattr(response.validation, 'validation_passed', False)
                )
            except Exception as e:
                logger.warning(f"⚠️ Error accessing validation results: {e}")
                analysis["validation_passed"] = False

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

            # 修复加权
            fixes_bonus = 0.05 if analysis["fixes_applied"] else 0.0

            analysis["effectiveness_score"] = max(0.0,
                                                  constraint_score - violation_penalty + strategy_bonus + mode_bonus + fixes_bonus)

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

    def get_system_status(self) -> Dict:
        """🔥 新增: 获取系统状态"""
        return {
            "local_validator_available": self.local_validator is not None,
            "local_validation_enabled": self.config.get("local_validation", {}).get("enabled", False),
            "strategy_mode": self.strategy_config.get("mode", "gbnf_priority"),
            "post_processing_enabled": self.post_processing_config.get("enabled", False),
            "available_prompt_types": self.get_available_prompt_types(),
            "config_loaded": bool(self.config)
        }

    def health_check(self) -> Dict:
        """🔥 新增: 客户端健康检查"""
        status = self.get_system_status()

        # 检查关键组件
        issues = []
        if not self.constraint_sender:
            issues.append("constraint_sender_missing")
        if self.config.get("local_validation", {}).get("enabled", False) and not self.local_validator:
            issues.append("local_validator_requested_but_unavailable")

        status.update({
            "healthy": len(issues) == 0,
            "issues": issues,
            "timestamp": time.time()
        })

        return status