# src/models/constraint_models.py
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, ConfigDict


class ConstraintInfo(BaseModel):
    """约束信息模型"""
    model_config = ConfigDict(protected_namespaces=())

    fsm_enabled: bool = False
    gbnf_enabled: bool = False
    grammar_rules: Optional[str] = None
    allowed_tokens: Optional[List[str]] = None
    current_state: Optional[str] = None
    domain_constraints: Dict[str, Any] = {}


class EnhancedGenerationRequest(BaseModel):
    """增强生成请求模型"""
    model_config = ConfigDict(protected_namespaces=())

    request_id: str
    prompt: str
    temperature: float = 0.7
    max_tokens: int = 1024
    top_p: float = 0.9
    frequency_penalty: float = 0.1
    presence_penalty: float = 0.1
    constraint_info: ConstraintInfo
    autosar_context: Dict[str, Any] = {}


class CloudGenerationResponse(BaseModel):
    """云端生成响应模型"""
    model_config = ConfigDict(protected_namespaces=())

    request_id: str
    success: bool
    generated_xml: Optional[str] = None
    raw_output: Optional[str] = None
    constraints_applied: Dict[str, bool] = {}
    constraint_violations: List[str] = []
    generation_time: float = 0.0
    model_info: Dict[str, Any] = {}
    error_message: Optional[str] = None
    error_details: Dict[str, Any] = {}