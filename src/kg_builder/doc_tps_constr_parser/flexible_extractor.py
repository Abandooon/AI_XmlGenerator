import re
from typing import List

from models import ConstraintRaw
from logging_utils import StepLogger

__all__ = ["FlexibleConstraintExtractor"]


class FlexibleConstraintExtractor:
    """抽取遵循固定格式的约束块：[ID] 标题 (cid:100) 细则 (cid:99) (关联条目ID列表)"""

    # 行首 ID
    _ID_ANCHOR = re.compile(r"^\s*\[((?:constr|TPS(?:_SWCT)?|RS|req)_[^\]]+)\]", re.I)

    # 标记
    _CID_OPEN = "(cid:100)"
    _CID_CLOSE = "(cid:99)"

    # 引用ID - 使用新的模式匹配(cid:99)后的括号内容，允许跨行
    _REF_ID_PATTERN = re.compile(r"\(cid:99\)\s*\((.*?)\)", re.DOTALL)

    # 匹配其他位置的引用
    _REF_ELSEWHERE = re.compile(r"\[(?:constr|TPS(?:_SWCT)?|RS|req)_[^\]]+\]")

    def __init__(self, debug: bool = True, max_debug_length: int = 200, **_):
        self.debug = debug
        self.max_debug_len = max_debug_length
        self.logger = StepLogger(enable=True)

    def extract_constraints(self, text: str):
        self.logger.step("提取约束：开始")
        text = self._preprocess_text(text)  # 新增：修复被分割的单词
        purified = self._prefilter(text)
        blocks = list(self._iter_blocks(purified))
        cons = [self._build_constraint(b) for b in blocks]
        self.logger.finish()
        return cons

    def _preprocess_text(self, text: str) -> str:
        """预处理文本，修复被换行符分割的单词"""
        # 处理行尾连字符
        text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)

        # 处理无连字符但明显被分割的单词
        text = re.sub(r'(\w{3,})\s*\n\s*(\w{2,})',
                      lambda m: m.group(1) + m.group(2)
                      if m.group(1)[-1].islower() and m.group(2)[0].islower()
                      else m.group(0), text)

        return text

    def _iter_blocks(self, text: str):
        """迭代查找所有约束块，确保完整捕获关联ID部分"""
        lines = text.splitlines()
        n, i = len(lines), 0

        while i < n:
            # 查找约束开始（ID标记）
            if not self._ID_ANCHOR.match(lines[i]):
                i += 1
                continue

            # 找到约束开始
            start = i
            i += 1

            # 查找约束结束和关联ID
            found_cid_close = False
            found_ref_open = False
            ref_bracket_count = 0

            while i < n:
                line = lines[i]

                # 处理cid:99标记
                if not found_cid_close and self._CID_CLOSE in line:
                    found_cid_close = True

                    # 检查同一行中是否有左括号开始关联ID
                    if "(" in line[line.find(self._CID_CLOSE) + len(self._CID_CLOSE):]:
                        found_ref_open = True
                        # 计算此行中左括号出现次数
                        ref_part = line[line.find(self._CID_CLOSE) + len(self._CID_CLOSE):]
                        ref_bracket_count = ref_part.count("(") - ref_part.count(")")

                # 如果已找到cid:99和左括号，继续寻找右括号以完成关联ID捕获
                elif found_cid_close and found_ref_open:
                    ref_bracket_count += line.count("(") - line.count(")")

                    # 括号匹配完成，关联ID部分结束
                    if ref_bracket_count <= 0:
                        i += 1  # 包含当前行
                        break

                # 未找到结束但遇到新约束，作为容错处理
                elif self._ID_ANCHOR.match(line):
                    break

                i += 1

                # 已经找到结束标记但没有关联ID，或者搜索太多行
                if found_cid_close and not found_ref_open and i - start > 3:
                    break

                # 容错：搜索超过最大限制
                if i - start > 50:
                    break

            # 提取完整约束块
            yield "\n".join(lines[start:i])

    def _build_constraint(self, block: str):
        """从文本块构建ConstraintRaw对象，正确处理复杂关联ID并分离标题和正文"""
        # 提取ID
        id_match = self._ID_ANCHOR.match(block.split('\n')[0])
        cid = id_match.group(1) if id_match else "UNKNOWN"

        # 提取关联ID列表 - 使用正则表达式抓取(cid:99)后的括号内容
        reference_ids = []
        ref_id_match = self._REF_ID_PATTERN.search(block)

        if ref_id_match:
            # 提取括号内容并按逗号分割
            ref_content = ref_id_match.group(1)
            # 清理和分割引用ID
            ref_parts = [p.strip() for p in re.split(r',\s*', ref_content)]
            # 过滤空字符串
            reference_ids = [p for p in ref_parts if p]

        # 提取文本中其他位置的引用
        other_refs = [m.group(0).strip("[]") for m in self._REF_ELSEWHERE.finditer(block)]
        # 过滤掉当前ID
        other_refs = [ref for ref in other_refs if ref != cid]

        # 合并并去重所有引用
        all_refs = reference_ids + other_refs
        all_refs = list(dict.fromkeys(all_refs))  # 去重

        # 修改：分离标题和正文
        title = ""
        body = ""

        if self._CID_OPEN in block and self._CID_CLOSE in block:
            # 提取标题（在ID之后，cid:100之前）
            before_open = block.split(self._CID_OPEN, 1)[0]
            if id_match:
                title = before_open[id_match.end():].strip()

            # 提取详细内容（在cid:100和cid:99之间）
            middle_parts = block.split(self._CID_OPEN, 1)[1].split(self._CID_CLOSE, 1)
            body = middle_parts[0].strip() if middle_parts else ""
        else:
            # 非标准格式处理
            body = block
            if id_match:
                body = body[id_match.end():].strip()

            # 处理可能的标题 - 取第一行或首句为标题
            if "\n" in body:
                title, rest = body.split("\n", 1)
                body = rest.strip()
            elif "." in body:
                title, rest = body.split(".", 1)
                body = rest.strip()
                title = title + "."

            # 移除可能的尾部引用
            if ref_id_match:
                body = body.replace(ref_id_match.group(0), "").strip()

        return ConstraintRaw(
            id=cid,
            type=cid.split("_", 1)[0] if "_" in cid else "GENERIC",
            title=title,
            body=body,
            reference_ids=all_refs,
        )

    def _prefilter(self, text: str):
        """预处理文本，移除干扰内容"""
        patterns = [
            (r"\b\d+\s+of\s+\d+\b", ""),  # 页码
            (r"Document ID \d+:.*?(?=\n|$)", ""),  # 文档ID
            (r"note \d+:.*?(?=\n|$)", ""),  # note
            (r"— AUTOSAR CONFIDENTIAL —", ""),  # 保密标记
            (r"Software Component Template\s*\nAUTOSAR Release \d+\.\d+\.\d+", ""),  # 文档头
            (r"\n{3,}", "\n\n")  # 规范化空行
        ]

        for pattern, replacement in patterns:
            text = re.sub(pattern, replacement, text, flags=re.I)

        return text.strip()