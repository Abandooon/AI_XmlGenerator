import re
from typing import List, Dict, Any, Optional

from models import ConstraintRaw
from utils import CONSTRAINT_BLOCK_PATTERN, extract_reference_id, clean_constraint_text


class ConstraintExtractor:
    def __init__(self):
        # 编译正则表达式以提高性能
        self.constraint_pattern = re.compile(CONSTRAINT_BLOCK_PATTERN, re.DOTALL)

    def extract_constraints(self, text: str) -> List[ConstraintRaw]:
        """从预处理后的文本中提取约束"""
        constraints = []

        # 查找所有约束块
        for match in self.constraint_pattern.finditer(text):
            constraint_type = match.group(1)  # constr 或 TPS
            constraint_id = f"{constraint_type}_{match.group(2)}"  # 完整ID，如 constr_1299
            title_part = match.group(3).strip()
            body_part = match.group(4).strip()
            reference_id = extract_reference_id(body_part) or match.group(5)

            # 清理约束文本
            body_part = clean_constraint_text(body_part)

            # 分离标题和解释部分(如果有)
            title, explanation = self._separate_title_and_explanation(title_part, body_part)

            constraint = ConstraintRaw(
                id=constraint_id,
                type=constraint_type,
                title=title,
                body=body_part,
                explanation=explanation,
                reference_id=reference_id
            )

            constraints.append(constraint)

        return constraints

    def _separate_title_and_explanation(self, title_text: str, body_text: str) -> Tuple[str, Optional[str]]:
        """
        分离标题和解释文本
        策略: 标题通常是第一句话，解释文本可能在正文中以"In other words"等短语开始
        """
        title = title_text.strip()
        explanation = None

        # 检查正文中是否有解释部分
        explanation_patterns = [
            r"In\s+other\s+words,\s+(.*)",
            r"This\s+means\s+that\s+(.*)",
            r"Note(?:\s+that)?:\s+(.*)"
        ]

        for pattern in explanation_patterns:
            match = re.search(pattern, body_text, re.IGNORECASE | re.DOTALL)
            if match:
                explanation = match.group(0)
                # 从正文中移除解释部分
                body_text = body_text.replace(explanation, "").strip()
                break

        return title, explanation