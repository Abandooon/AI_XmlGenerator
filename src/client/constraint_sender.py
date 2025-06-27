# src/client/constraint_sender.py
import json
import uuid
from typing import Dict, List, Optional
from pathlib import Path

from src.client.constraint_preparer import ConstraintPreparer  # 使用已有的ConstraintPreparer
from src.models.constraint_models import ConstraintInfo, EnhancedGenerationRequest
from src.utils.logger import get_logger

logger = get_logger(__name__)

class ConstraintSender:
    """约束信息发送器 - 简化版本"""

    def __init__(self, artifacts_dir: str):
        # 使用ConstraintPreparer来加载约束制品
        self.constraint_preparer = ConstraintPreparer(artifacts_dir)

    def build_enhanced_request(
            self,
            prompt: str,
            autosar_context: Dict = None,
            xml_context: List[str] = None,
            constraint_level: str = "mixed",
            **generation_params
    ) -> EnhancedGenerationRequest:
        """构建增强的生成请求"""
        request_id = str(uuid.uuid4())

        # 使用ConstraintPreparer准备约束信息
        current_state = self._extract_current_state(xml_context)
        constraint_info = self.constraint_preparer.prepare_constraint_info(
            constraint_level, current_state
        )

        request = EnhancedGenerationRequest(
            request_id=request_id,
            prompt=prompt,
            constraint_info=constraint_info,
            autosar_context=autosar_context or {},
            **generation_params
        )

        logger.info(f"Built enhanced request {request_id} with constraint level: {constraint_level}")
        return request

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
        return self.constraint_preparer.get_constraint_summary()