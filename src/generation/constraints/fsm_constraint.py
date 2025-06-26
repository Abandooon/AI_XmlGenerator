# src/generation/constraints/fsm_constraint.py
from typing import List, Dict, Set, Optional
import json
from transformers import PreTrainedTokenizer


class FSMConstraintHandler:
    """FSM状态机约束处理器"""

    def __init__(self, fsm_file: str, allowed_tokens_module: str, tokenizer: PreTrainedTokenizer):
        """
        初始化FSM约束处理器

        Args:
            fsm_file: autosar.fsm文件路径
            allowed_tokens_module: autosar_allowed_tokens.py模块路径
            tokenizer: 分词器实例
        """
        self.fsm_data = self._load_fsm(fsm_file)
        self.allowed_tokens_func = self._load_allowed_tokens(allowed_tokens_module)
        self.tokenizer = tokenizer
        self.state_cache = {}  # 缓存状态转换

    def create_logits_processor(self):
        """创建基于FSM的logits处理器"""

        def fsm_logits_processor(input_ids: List[int], scores):
            # 从token序列提取当前状态
            current_state = self.extract_current_state(input_ids)

            # 获取允许的下一个tokens
            allowed_tokens = self.get_allowed_transitions(current_state)

            # 创建token掩码
            token_mask = self.create_token_mask(allowed_tokens, len(scores))

            # 应用掩码到logits
            scores[~token_mask] = float('-inf')
            return scores

        return fsm_logits_processor

    def extract_current_state(self, input_ids: List[int]) -> str:
        """从token序列解析当前XML标签状态"""
        # 解码tokens为文本
        text = self.tokenizer.decode(input_ids, skip_special_tokens=True)

        # 提取XML标签序列
        xml_tags = self._extract_xml_tags(text)

        # 转换为FSM状态字符串
        state = " ".join(xml_tags) if xml_tags else ""
        return state

    def get_allowed_transitions(self, state: str) -> Set[str]:
        """查询FSM转换表获取允许的转换"""
        if state in self.state_cache:
            return self.state_cache[state]

        # 使用allowed_tokens函数查询
        prefix = state.split() if state else []
        allowed = self.allowed_tokens_func(prefix)

        self.state_cache[state] = allowed or set()
        return self.state_cache[state]