import re
from typing import Optional

from models import ConstraintRaw
from utils import CONSTRAINT_BLOCK_PATTERN, extract_reference_id, clean_constraint_text


class ConstraintExtractor:
    def __init__(self):
        # 编译正则表达式以提高性能
        self.constraint_pattern = re.compile(CONSTRAINT_BLOCK_PATTERN, re.DOTALL)

    def extract_constraints(self, text: str) -> list[ConstraintRaw]:
        """从预处理后的文本中提取约束"""
        constraints = []

        # 查找所有约束块
        for match in self.constraint_pattern.finditer(text):
            constraint_type = match.group(1)  # constr 或 TPS 或 TPS_SWCT
            constraint_id = f"{constraint_type}_{match.group(2)}"  # 完整ID
            title_part = match.group(3).strip()
            body_part = match.group(4).strip()
            reference_id = extract_reference_id(body_part) or match.group(5)

            # 清理约束文本
            body_part = clean_constraint_text(body_part)

            # 寻找"In other words"或相似短语开始的解释段落
            explanation = None
            explanation_start = body_part.find("In other words")
            if explanation_start == -1:
                explanation_start = body_part.find("Nevertheless")

            if explanation_start != -1:
                explanation = body_part[explanation_start:].strip()
                body_part = body_part[:explanation_start].strip()

            constraint = ConstraintRaw(
                id=constraint_id,
                type=constraint_type,
                title=title_part,
                body=body_part,
                explanation=explanation,
                reference_id=reference_id
            )

            constraints.append(constraint)

        if not constraints:
            # 添加更灵活的回退方法
            constraints = self._extract_with_fallback_method(text)

        return constraints

    def _extract_with_fallback_method(self, text: str) -> list[ConstraintRaw]:
        """备用的约束提取方法，更灵活地处理不同格式"""
        constraints = []

        # 找出所有可能的约束ID
        id_pattern = r"\[(constr|TPS|TPS_SWCT)_([^\]]+)\]"
        id_matches = re.finditer(id_pattern, text)

        for id_match in id_matches:
            start_pos = id_match.start()
            constraint_type = id_match.group(1)
            constraint_number = id_match.group(2)
            constraint_id = f"{constraint_type}_{constraint_number}"

            # 查找该ID后的内容，直到下一个约束ID或文档结束
            next_id_match = re.search(id_pattern, text[start_pos + 1:])
            end_pos = start_pos + 1 + (next_id_match.start() if next_id_match else len(text) - start_pos - 1)

            constraint_text = text[start_pos:end_pos].strip()

            # 尝试分离标题、正文和解释
            lines = constraint_text.split('\n')
            title_line = lines[0].replace(f"[{constraint_type}_{constraint_number}]", "").strip()

            # 假设正文从第二行开始
            body_text = '\n'.join(lines[1:]).strip()

            # 尝试提取引用ID
            reference_id = None
            ref_match = re.search(r"\(([A-Z0-9_]+)\)$", body_text)
            if ref_match:
                reference_id = ref_match.group(1)

            # 查找解释部分
            explanation = None
            for exp_starter in ["In other words", "Nevertheless", "Note that"]:
                exp_start = body_text.find(exp_starter)
                if exp_start != -1:
                    explanation = body_text[exp_start:].strip()
                    body_text = body_text[:exp_start].strip()
                    break

            constraint = ConstraintRaw(
                id=constraint_id,
                type=constraint_type,
                title=title_line,
                body=body_text,
                explanation=explanation,
                reference_id=reference_id
            )

            constraints.append(constraint)

        return constraints

