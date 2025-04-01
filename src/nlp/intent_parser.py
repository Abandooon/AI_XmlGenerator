def load_llm(model_name):
    pass


class IntentParser:
    dict = {}

    def __init__(self, model_name: str = "gpt-4"):
        self.llm = load_llm(model_name)

    def parse(self, text: str) -> dict:
        """输入: 自然语言文本 → 输出: 结构化指令"""
        prompt = f"将AUTOSAR需求转换为JSON: {text}"
        return self.llm.generate(prompt)