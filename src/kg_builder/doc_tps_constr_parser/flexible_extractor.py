import re
from typing import Optional

from models import ConstraintRaw
from logging_utils import StepLogger


class FlexibleConstraintExtractor:
    """灵活的约束提取器，能够处理多种格式"""

    def __init__(self, debug=True, max_debug_length=200):
        self.debug = debug
        self.max_debug_length = max_debug_length
        self.logger = StepLogger(enable=True)

    def extract_constraints(self, text: str) -> list[ConstraintRaw]:
        """主提取方法，尝试多种策略"""
        self.logger.step("开始提取约束")

        self.logger.log(f"输入文本长度: {len(text)} 字符")
        if self.debug:
            sample_text = text[:self.max_debug_length] + "..." if len(text) > self.max_debug_length else text
            self.logger.log(f"文本样本: {sample_text}")

        self.logger.step("预处理文本，过滤XML和代码示例")
        filtered_text = self._prefilter_text(text)
        self.logger.log(f"预处理后文本长度: {len(filtered_text)} 字符")

        self.logger.step("查找所有约束ID")
        constraint_ids = self._find_all_constraint_ids(filtered_text)

        if not constraint_ids:
            self.logger.log("未找到任何约束ID，提取结束")
            return []

        self.logger.log(f"找到 {len(constraint_ids)} 个约束ID")
        for i, (id_type, id_num, start_pos) in enumerate(constraint_ids[:5]):
            self.logger.log(f"ID {i + 1}: [{id_type}_{id_num}] 位置: {start_pos}")
        if len(constraint_ids) > 5:
            self.logger.log(f"...以及{len(constraint_ids) - 5}个更多约束ID")

        self.logger.step("解析每个约束的内容")
        constraints = []
        skipped_count = 0

        for i, (id_type, id_num, start_pos) in enumerate(constraint_ids):
            constraint_id = f"{id_type}_{id_num}"
            self.logger.log(f"处理约束 #{i + 1}: {constraint_id}")

            # 确定约束结束位置
            end_pos = len(filtered_text)
            if i < len(constraint_ids) - 1:
                end_pos = constraint_ids[i + 1][2]

            constraint_text = filtered_text[start_pos:end_pos].strip()
            self.logger.log(f"约束文本长度: {len(constraint_text)} 字符")

            self.logger.log(f"解析约束 {constraint_id} 的内容")
            _, body, explanation, reference_id = self._parse_constraint_content(constraint_text, id_type, id_num)

            # 检查是否是假阳性
            if self._is_likely_false_positive(body):
                self.logger.log(f"跳过可能的假阳性: [{constraint_id}]")
                skipped_count += 1
                continue

            constraint = ConstraintRaw(
                id=constraint_id,
                type=id_type,
                body=body,
                explanation=explanation,
                reference_id=reference_id
            )

            constraints.append(constraint)

            body_preview = body[:50] + "..." if len(body) > 50 else body
            self.logger.log(f"成功提取约束: {constraint_id} - {body_preview}")

        self.logger.step("约束提取完成")
        self.logger.log(f"共找到 {len(constraint_ids)} 个约束ID")
        self.logger.log(f"成功提取 {len(constraints)} 个约束")
        self.logger.log(f"跳过 {skipped_count} 个可能的假阳性")

        self.logger.finish()
        return constraints

    def _find_all_constraint_ids(self, text: str) -> list[tuple[str, str, int]]:
        """查找所有约束ID及其位置"""
        # 匹配 [constr_123], [TPS_456], [TPS_SWCT_789] 等格式
        id_pattern = r'\[(constr|TPS|TPS_SWCT|req)_([^\]]+)\]'
        matches = list(re.finditer(id_pattern, text))

        # 返回格式：[(id_type, id_number, start_position), ...]
        return [(m.group(1), m.group(2), m.start()) for m in matches]

    def _parse_constraint_content(self, text: str, id_type: str, id_num: str) -> tuple[
        None, str, Optional[str], Optional[str]]:
        """解析约束内容，将整个内容作为正文处理"""
        # 移除约束ID部分
        id_marker = f"[{id_type}_{id_num}]"
        body_text = text.replace(id_marker, "", 1).strip()

        # 寻找引用ID (通常在文本末尾括号内)
        reference_id = None
        ref_match = re.search(r'\(([A-Z0-9_]+)\)$', body_text)
        if ref_match:
            reference_id = ref_match.group(1)
            # 从正文中移除引用ID
            body_text = body_text[:ref_match.start()].strip()

        # 尝试从正文中分离出解释部分
        explanation = None
        explanation_markers = [
            "In other words", "Nevertheless", "Note that",
            "i.e.", "e.g.", "This means", "For example"
        ]

        # 尝试分离解释段落
        body_parts = re.split(r'\n\s*\n', body_text)  # 使用空行分隔段落
        if len(body_parts) > 1:
            for i, part in enumerate(body_parts[1:], 1):
                for marker in explanation_markers:
                    if marker in part:
                        explanation = '\n\n'.join(body_parts[i:])
                        body_text = body_parts[0]
                        break
                if explanation:
                    break

        # 如果没有通过段落分离找到解释，尝试直接在文本中查找标记
        if not explanation:
            for marker in explanation_markers:
                exp_start = body_text.find(marker)
                if exp_start > 20:  # 避免标记出现在太靠前的位置
                    explanation = body_text[exp_start:].strip()
                    body_text = body_text[:exp_start].strip()
                    break

        # 清理特殊格式标记，如 (cid:100) 和 (cid:99)
        body_text = re.sub(r'\(cid:\d+\)', '', body_text)
        if explanation:
            explanation = re.sub(r'\(cid:\d+\)', '', explanation)

        return None, body_text, explanation, reference_id

    def _prefilter_text(self, text: str) -> str:
        """预处理文本以过滤掉XML代码块和示例代码块"""
        original_length = len(text)

        # 过滤XML代码块
        filtered = re.sub(r'<[^>]+>.*?</[^>]+>', '', text, flags=re.DOTALL)
        xml_removed_length = len(filtered)
        self.logger.log(f"XML过滤: {original_length - xml_removed_length} 字符被移除")

        # 过滤代码示例块
        filtered = re.sub(r'Listing \d+\..*?\n\n', '\n\n', filtered)

        # 过滤图表引用
        filtered = re.sub(r'Figure \d+\..*?\n', '\n', filtered)

        # 过滤表格引用
        filtered = re.sub(r'Table \d+\..*?\n', '\n', filtered)

        final_length = len(filtered)
        self.logger.log(f"预处理总计移除: {original_length - final_length} 字符")

        return filtered

    def _is_likely_false_positive(self, body: str) -> bool:
        """检查是否可能是假阳性识别，主要基于正文内容和特殊标记"""
        # 首先检查特殊标记，若存在，判定为真约束
        if "(cid:100)" in body and "(cid:99)" in body:
            return False

        # 如果正文为空或极短
        if not body or len(body) < 10:
            return True

        # 如果正文包含明显的非约束内容标记
        non_constraint_markers = [
            "Listing", "Figure", "Table", "Example",
            "<", ">", "<?xml", "EXAMPLE", "OUTPUT"
        ]

        for marker in non_constraint_markers:
            if marker in body[:50]:
                return True

        # 检查格式特征
        if body.count('\n') < 1:  # 真正的约束通常是多行的
            return True

        # 检查内容是否包含明显的非约束内容
        if re.search(r'Figure \d+\.', body) or re.search(r'Table \d+\.', body):
            return True

        return False