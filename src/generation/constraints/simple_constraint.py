# src/generation/constraints/simple_constraint.py
import json
import sys
import os
from typing import List, Dict, Set, Optional
from vllm import SamplingParams


class SimpleConstraintHandler:
    """简化的约束处理器 - 先实现基本功能"""

    def __init__(self, fsm_file: str, gbnf_file: str):
        """
        初始化约束处理器

        Args:
            fsm_file: FSM文件路径
            gbnf_file: GBNF语法文件路径
        """
        self.fsm_data = self._load_fsm_data(fsm_file)
        self.gbnf_grammar = self._load_gbnf_grammar(gbnf_file)

        print(f"Loaded FSM with {len(self.fsm_data.get('states', []))} states")
        print(f"Loaded GBNF grammar: {len(self.gbnf_grammar)} characters")

    def _load_fsm_data(self, fsm_file: str) -> Dict:
        """加载FSM数据"""
        try:
            if os.path.exists(fsm_file):
                with open(fsm_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                print(f"Warning: FSM file not found: {fsm_file}")
                return {"states": [], "edges": {}, "accept": []}
        except Exception as e:
            print(f"Error loading FSM: {e}")
            return {"states": [], "edges": {}, "accept": []}

    def _load_gbnf_grammar(self, gbnf_file: str) -> str:
        """加载GBNF语法"""
        try:
            if os.path.exists(gbnf_file):
                with open(gbnf_file, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                print(f"Warning: GBNF file not found: {gbnf_file}")
                return ""
        except Exception as e:
            print(f"Error loading GBNF: {e}")
            return ""

    def create_sampling_params(
            self,
            temperature: float = 0.7,
            max_tokens: int = 1024,
            constraint_level: str = "simple"
    ) -> SamplingParams:
        """创建采样参数"""

        params = SamplingParams(
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=0.9,
            frequency_penalty=0.1,
            presence_penalty=0.1
        )

        # 如果有GBNF语法，应用语法约束
        if self.gbnf_grammar and constraint_level in ["gbnf", "mixed"]:
            try:
                params.guided_grammar = self.gbnf_grammar
                print("Applied GBNF grammar constraint")
            except Exception as e:
                print(f"Failed to apply GBNF constraint: {e}")

        return params