"""autosar_allowed_tokens – AUTO-GENERATED
------------------------------------------------
• FSM file : autosar.fsm
• Compress : True
• On-demand: True
"""
from __future__ import annotations

import json
import pathlib
from typing import List, Optional

# 加载完整的 FSM
_FSM_PATH = pathlib.Path(__file__).parent / "autosar.fsm"
with _FSM_PATH.open(encoding="utf-8") as f:
    _FSM_DATA = json.load(f)

_TRANSITIONS = _FSM_DATA["edges"]
_ACCEPTING = set(_FSM_DATA["accept"])

def allowed(prefix_tokens: List[str]) -> Optional[List[str]]:
    """
    Args:
        prefix_tokens: 已生成的 token 序列
    Returns:
        允许的下一个 token 列表，或 None 表示不限制
    """
    state = " ".join(prefix_tokens)
    if state in _TRANSITIONS:
        return list(_TRANSITIONS[state].keys())
    return None

# vLLM 兼容接口
def allowed_token_ids(prefix_ids, tokenizer) -> Optional[List[int]]:
    """vLLM 兼容的接口"""
    if not prefix_ids or not tokenizer:
        return None

    # 将 token IDs 转换为文本
    prefix_text = tokenizer.decode(prefix_ids, skip_special_tokens=True).strip()
    tokens = prefix_text.split() if prefix_text else []

    # 获取允许的 tokens
    allowed_tokens = allowed(tokens)
    if allowed_tokens is None:
        return None

    # 转换为 token IDs
    token_ids = []
    for token in allowed_tokens:
        try:
            ids = tokenizer.encode(token, add_special_tokens=False)
            if ids:
                token_ids.append(ids[0])
        except:
            continue

    return token_ids if token_ids else None
