"""utils/exceptions.py - 系统异常定义

定义系统中使用的各种异常类型
"""

class LLMGenerationException(Exception):
    """LLM生成系统顶层异常基类"""
    pass

# 系统级异常
class ConfigurationError(LLMGenerationException):
    """配置错误"""
    pass

class ResourceNotFoundError(LLMGenerationException):
    """资源未找到错误"""
    pass

# 业务级异常
class ArchitectureDesignError(LLMGenerationException):
    """架构设计失败"""
    pass

class ValidationError(LLMGenerationException):
    """验证失败"""
    pass

class ConversationError(LLMGenerationException):
    """对话流程错误"""
    pass

# 技术级异常
class LLMAPIError(LLMGenerationException):
    """LLM API调用失败"""
    def __init__(self, message: str, status_code: int = None, response_text: str = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text

class KGQueryError(LLMGenerationException):
    """知识图谱查询失败"""
    pass

class MemoryError(LLMGenerationException):
    """记忆管理失败"""
    pass

class SchemaGenerationError(LLMGenerationException):
    """Schema生成失败"""
    pass

class PromptTemplateError(LLMGenerationException):
    """提示词模板错误"""
    pass