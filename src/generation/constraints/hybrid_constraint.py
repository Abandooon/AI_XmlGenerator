# src/generation/constraints/hybrid_constraint.py
from typing import Dict, Optional
from vllm import SamplingParams


class HybridConstraintHandler:
    """混合约束策略处理器"""

    def __init__(self, fsm_handler: FSMConstraintHandler, gbnf_handler: GBNFConstraintHandler):
        """
        初始化混合约束处理器

        Args:
            fsm_handler: FSM约束处理器
            gbnf_handler: GBNF约束处理器
        """
        self.fsm_handler = fsm_handler
        self.gbnf_handler = gbnf_handler

    def create_sampling_params(
            self,
            temperature: float = 0.7,
            max_tokens: int = 1024,
            constraint_level: str = "mixed"
    ) -> SamplingParams:
        """创建混合约束的采样配置"""

        params = SamplingParams(
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=0.9,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )

        if constraint_level == "fsm_only":
            # 仅使用FSM约束
            params.logits_processors = [self.fsm_handler.create_logits_processor()]

        elif constraint_level == "gbnf_only":
            # 仅使用GBNF约束
            guided_config = self.gbnf_handler.create_guided_config()
            params.guided_grammar = guided_config["guided_grammar"]

        elif constraint_level == "mixed":
            # 混合约束策略
            params.logits_processors = [self.fsm_handler.create_logits_processor()]
            guided_config = self.gbnf_handler.create_guided_config()
            params.guided_grammar = guided_config["guided_grammar"]

        return params

    def select_constraint_strategy(self, autosar_context: Dict, complexity_level: str) -> str:
        """基于上下文自动选择约束策略"""

        # 根据AUTOSAR上下文和复杂度选择策略
        if complexity_level == "simple" and len(autosar_context.get("elements", [])) < 10:
            return "gbnf_only"
        elif complexity_level == "complex" or "timing" in autosar_context:
            return "mixed"
        else:
            return "fsm_only"