from src.utils.logger import get_logger
logger = get_logger(__name__)

class PromptEnhancer:
    def enhance_prompt(self, prompt: str, autosar_context: dict | None = None) -> str:
        """当前占位实现：仅拼接上下文信息，后续可替换为模板系统"""
        if autosar_context:
            ctx = " | ".join(f"{k}:{v}" for k, v in autosar_context.items())
            return f"{prompt}\n\n<!-- CONTEXT:{ctx} -->"
        return prompt
