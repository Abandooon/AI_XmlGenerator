class ConstraintMiner:
    list = []
    def extract(self, doc_path: str) -> list[str]:
        """输入: 标准文档.pdf → 输出: 约束规则列表"""
        # 使用NLP规则提取（如正则匹配"必须满足...")
        return ["周期≤10ms", "端口数量≥1"]