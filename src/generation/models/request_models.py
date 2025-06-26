# src/generation/models/request_models.py
from pydantic import BaseModel
from typing import Dict, Optional, List
import uuid


class GenerationRequest(BaseModel):
    """生成请求模型"""
    request_id: str = None
    prompt: str
    autosar_context: Dict = {}
    temperature: float = 0.7
    max_tokens: int = 1024
    constraint_level: str = "mixed"  # fsm_only, gbnf_only, mixed
    validation_level: str = "full"  # structure, semantic, constraint, full

    def __init__(self, **data):
        if 'request_id' not in data or not data['request_id']:
            data['request_id'] = str(uuid.uuid4())
        super().__init__(**data)


class BatchGenerationRequest(BaseModel):
    """批量生成请求模型"""
    requests: List[GenerationRequest]
    parallel_count: int = 4
    timeout: int = 300