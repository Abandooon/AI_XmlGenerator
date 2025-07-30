"""llm/response_parser.py - 响应解析器

解析LLM响应，移除验证打分逻辑，专注于数据解析和基础修复
"""
import json
import re
from typing import Dict, Any, List, Tuple, Optional, Union
from ..utils.exceptions import ValidationError
from ..utils.serializers import ArchitectureDesign

class ResponseParser:
    """LLM响应解析器"""

    def __init__(self):
        """初始化解析器"""
        pass

    def parse_architecture_response(self, response_text: str) -> ArchitectureDesign:
        """只解析，不修复"""
        json_data = self._extract_json(response_text)  # 只提取JSON
        # 直接创建对象，不做任何修复
        return ArchitectureDesign(**json_data)

    def parse_arxml_response(self, response_data: Union[str, Dict]) -> Dict[str, Any]:
        """只解析，不修复"""
        if isinstance(response_data, str):
            return self._extract_json(response_data)
        return response_data

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """从文本中提取JSON内容"""
        # 清理文本
        text = text.strip()

        # 尝试直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 查找JSON代码块
        json_blocks = re.findall(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        for block in json_blocks:
            try:
                return json.loads(block.strip())
            except json.JSONDecodeError:
                continue

        # 查找大括号包围的内容
        brace_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(brace_pattern, text, re.DOTALL)

        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue

        raise ValidationError("无法从响应中提取有效的JSON内容")


# 全局响应解析器实例（如果需要）
response_parser = ResponseParser()