# src/generation/models/response_models.py
from pydantic import BaseModel
from typing import Dict, Optional, List, Any
import time


class GenerationResponse(BaseModel):
    """生成响应模型"""
    request_id: str
    generated_xml: str
    metadata: Dict[str, Any] = {}
    performance: Dict[str, float] = {}
    constraint_info: Dict[str, Any] = {}
    timestamp: float = None

    def __init__(self, **data):
        if 'timestamp' not in data:
            data['timestamp'] = time.time()
        super().__init__(**data)


class ErrorResponse(BaseModel):
    """错误响应模型"""
    request_id: str
    error_code: str
    error_message: str
    error_details: Dict = {}
    timestamp: float = None

    def __init__(self, **data):
        if 'timestamp' not in data:
            data['timestamp'] = time.time()
        super().__init__(**data)