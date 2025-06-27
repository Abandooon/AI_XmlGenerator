# src/validation/local_validator.py
import xml.etree.ElementTree as ET
from typing import Dict, Any
from pathlib import Path
import time

from ..models.data_models import ValidationResult
from ..utils.logger import get_logger

logger = get_logger(__name__)


class LocalValidator:
    """本地验证器 - 简化实现"""

    def __init__(self, artifacts_dir: str):
        self.artifacts_dir = Path(artifacts_dir)

    def validate_xml(self, xml_content: str, validation_level: str = "basic") -> ValidationResult:
        """验证XML内容"""
        start_time = time.time()

        result = ValidationResult()
        stages = {}

        try:
            # 基础XML格式验证
            stages["wellformed"] = self._validate_wellformed(xml_content)

            # AUTOSAR结构验证
            if validation_level in ["full", "structure"]:
                stages["structure"] = self._validate_autosar_structure(xml_content)

            # 计算总体有效性
            all_valid = all(
                stage["result"]["valid"]
                for stage in stages.values()
                if stage["executed"]
            )

            result.overall_valid = all_valid
            result.stages = stages
            result.total_time = time.time() - start_time

            logger.info(f"Validation completed: valid={all_valid}, time={result.total_time:.2f}s")

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            result.overall_valid = False
            result.error = str(e)
            result.total_time = time.time() - start_time

        return result

    def _validate_wellformed(self, xml_content: str) -> Dict[str, Any]:
        """验证XML格式良好性"""
        stage_info = {
            "executed": True,
            "result": {"valid": False, "error_info": None}
        }

        try:
            ET.fromstring(xml_content)
            stage_info["result"]["valid"] = True
            logger.debug("XML wellformed validation passed")
        except ET.ParseError as e:
            stage_info["result"]["error_info"] = f"XML Parse Error: {str(e)}"
            logger.warning(f"XML wellformed validation failed: {e}")
        except Exception as e:
            stage_info["result"]["error_info"] = f"Unexpected error: {str(e)}"
            logger.error(f"Wellformed validation error: {e}")

        return stage_info

    def _validate_autosar_structure(self, xml_content: str) -> Dict[str, Any]:
        """验证AUTOSAR结构"""
        stage_info = {
            "executed": True,
            "result": {"valid": False, "error_info": None}
        }

        try:
            # 检查必需的AUTOSAR元素
            required_elements = [
                "AUTOSAR",
                "AR-PACKAGES",
                "APPLICATION-SW-COMPONENT-TYPE"
            ]

            missing_elements = []
            for element in required_elements:
                if element not in xml_content:
                    missing_elements.append(element)

            if missing_elements:
                stage_info["result"]["error_info"] = f"Missing elements: {missing_elements}"
            else:
                stage_info["result"]["valid"] = True
                logger.debug("AUTOSAR structure validation passed")

        except Exception as e:
            stage_info["result"]["error_info"] = f"Structure validation error: {str(e)}"
            logger.error(f"AUTOSAR structure validation error: {e}")

        return stage_info

    def validate_full(self, xml_content: str) -> Dict[str, Any]:
        """完整验证接口（兼容性）"""
        result = self.validate_xml(xml_content, "full")
        return result.dict()