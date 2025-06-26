# src/generation/processors/prompt_enhancer.py
from typing import Dict, Optional


class PromptEnhancer:
    """提示词增强处理器"""

    def __init__(self):
        """初始化提示增强器"""
        self.autosar_context_template = """
You are an AUTOSAR XML generator. Generate valid AUTOSAR XML according to the following requirements:

1. Follow AUTOSAR 4.3.1 schema structure
2. Use proper XML formatting with correct tag nesting
3. Include required attributes and elements
4. Ensure all references are valid

Context: {context}

User Request: {prompt}

Generate the AUTOSAR XML:
"""

    def enhance_prompt(
            self,
            user_prompt: str,
            autosar_context: Dict,
            constraint_hints: Dict = None
    ) -> str:
        """增强用户提示"""

        # 构建上下文信息
        context_str = []

        if autosar_context.get("domain"):
            context_str.append(f"Domain: {autosar_context['domain']}")

        if autosar_context.get("complexity"):
            context_str.append(f"Complexity: {autosar_context['complexity']}")

        if autosar_context.get("elements"):
            context_str.append(f"Elements: {', '.join(autosar_context['elements'])}")

        context = " | ".join(context_str) if context_str else "General AUTOSAR XML generation"

        # 应用模板
        enhanced_prompt = self.autosar_context_template.format(
            context=context,
            prompt=user_prompt
        )

        return enhanced_prompt