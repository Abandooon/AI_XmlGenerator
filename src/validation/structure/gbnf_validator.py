# src/validation/structure/gbnf_validator.py
import subprocess
from typing import Dict, List, Tuple
import xml.etree.ElementTree as ET


class GBNFValidator:
    """GBNF语法结构验证器"""

    def __init__(self, grammar_file: str):
        """
        初始化GBNF验证器

        Args:
            grammar_file: GBNF语法文件路径
        """
        self.grammar_file = grammar_file
        self.grammar_content = self._load_grammar(grammar_file)

    def validate_structure(self, xml_content: str) -> Dict:
        """验证XML结构是否符合GBNF语法"""

        try:
            # 1. 提取token序列
            token_sequence = self.extract_token_sequence(xml_content)

            # 2. 语法解析验证
            is_valid, error_info = self._parse_with_grammar(token_sequence)

            # 3. 错误定位
            error_location = None
            if not is_valid:
                error_location = self.get_error_location(xml_content, error_info)

            return {
                "valid": is_valid,
                "error_info": error_info,
                "error_location": error_location,
                "token_count": len(token_sequence)
            }

        except Exception as e:
            return {
                "valid": False,
                "error_info": f"Validation error: {str(e)}",
                "error_location": None,
                "token_count": 0
            }

    def extract_token_sequence(self, xml_content: str) -> List[str]:
        """从XML提取token序列进行语法检查"""

        tokens = []
        try:
            # 解析XML获取标签序列
            root = ET.fromstring(xml_content)

            def extract_tags(element, prefix=""):
                current_state = f"{prefix} {element.tag}".strip()
                tokens.append(element.tag)

                for child in element:
                    extract_tags(child, current_state)

            extract_tags(root)

        except ET.ParseError as e:
            # XML格式错误，返回部分解析的tokens
            tokens = self._partial_parse_tokens(xml_content)

        return tokens

    def get_error_location(self, xml_content: str, error_info: str) -> Dict:
        """定位语法错误的具体位置"""

        lines = xml_content.split('\n')

        # 简单的错误定位逻辑
        for i, line in enumerate(lines):
            if any(keyword in line for keyword in ['<', '>', '=']):
                # 找到可能的错误行
                return {
                    "line": i + 1,
                    "column": 0,
                    "context": line.strip()
                }

        return {"line": 1, "column": 0, "context": "Unknown"}