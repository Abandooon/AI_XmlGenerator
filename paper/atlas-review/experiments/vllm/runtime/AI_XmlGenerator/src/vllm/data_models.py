# src/models/data_models.py
from typing import Dict, List, Optional, Any

from pydantic import BaseModel


class GenerationResponse(BaseModel):
    """生成响应模型"""
    request_id: str
    generated_xml: str
    metadata: Dict[str, Any] = {}
    performance: Dict[str, Any] = {}

class ValidationResult(BaseModel):
    """验证结果模型"""
    overall_valid: bool = False
    stages: Dict[str, Any] = {}
    violations: List[str] = []
    total_time: float = 0.0

class ClientResponse(BaseModel):
    """客户端完整响应模型"""
    request: Any = None  # EnhancedGenerationRequest
    success: bool = False
    generation: Optional[GenerationResponse] = None
    validation: Optional[ValidationResult] = None
    execution_time: float = 0.0
    error: Optional[str] = None