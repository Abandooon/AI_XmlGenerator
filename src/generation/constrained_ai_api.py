class ConstrainedGenerator:
    list = []
    def __init__(self, constraints: list[str]):
        self.validator = DroolsValidator(constraints)

    def generate(self, prompt: str) -> str:
        """输入: 结构化指令 → 输出: ARXML实例"""
        while retry_count < MAX_RETRY:
            xml = self.llm.generate(prompt)
            if self.validator.check(xml):
                return xml
            prompt += f"\n修复建议: {self.validator.get_errors()}"
        raise GenerationError