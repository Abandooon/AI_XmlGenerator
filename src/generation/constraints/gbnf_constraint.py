# src/generation/constraints/gbnf_constraint.py
from typing import Dict, List, Optional
import re


class GBNFConstraintHandler:
    """GBNF语法约束处理器"""

    def __init__(self, grammar_file: str):
        """
        初始化GBNF约束处理器

        Args:
            grammar_file: autosar.gbnf文件路径
        """
        self.grammar_text = self._load_grammar(grammar_file)
        self.grammar_rules = self._parse_grammar(self.grammar_text)

    def create_guided_config(self) -> Dict:
        """创建vLLM的guided generation配置"""
        return {
            "guided_grammar": self.grammar_text,
            "guided_choice": None,
            "guided_json": None,
            "guided_regex": None,
            "guided_decoding_backend": "outlines"
        }

    def validate_partial_output(self, text: str) -> bool:
        """验证部分输出是否符合语法"""
        # 实现部分匹配逻辑
        return self._is_partial_match(text, self.grammar_rules)

    def get_next_valid_tokens(self, current_text: str) -> List[str]:
        """基于语法规则获取下一个有效token"""
        # 分析当前文本在语法中的位置
        current_rule = self._find_current_rule(current_text)

        # 返回该位置允许的下一个tokens
        return self._get_valid_continuations(current_rule, current_text)