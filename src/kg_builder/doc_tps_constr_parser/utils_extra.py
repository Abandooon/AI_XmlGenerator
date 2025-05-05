import re
from typing import Optional


def find_pattern_matches(text: str, patterns: list[str], debug: bool = False) -> list[tuple[int, int, dict[str, str]]]:
    """使用多个模式查找匹配项"""
    all_matches = []

    for i, pattern in enumerate(patterns):
        try:
            regex = re.compile(pattern, re.DOTALL)
            matches = list(regex.finditer(text))

            if debug:
                print(f"模式 #{i + 1} 找到 {len(matches)} 个匹配项")

            for match in matches:
                start, end = match.span()
                groups = {f"group{j}": match.group(j) for j in range(1, len(match.groups()) + 1)}
                all_matches.append((start, end, groups))

        except re.error as e:
            if debug:
                print(f"模式 #{i + 1} 正则表达式错误: {e}")

    # 按开始位置排序
    all_matches.sort(key=lambda x: x[0])

    return all_matches


def extract_chunks_between_markers(text: str, start_markers: list[str], end_markers: list[str],
                                   include_markers: bool = False, debug: bool = False) -> list[tuple[str, int, int]]:
    """从文本中提取被标记的块"""
    chunks = []

    # 查找所有开始标记和结束标记的位置
    start_positions = []
    for marker in start_markers:
        for match in re.finditer(re.escape(marker), text):
            pos = match.start() if not include_markers else match.start()
            start_positions.append((pos, marker))

    end_positions = []
    for marker in end_markers:
        for match in re.finditer(re.escape(marker), text):
            pos = match.end() if not include_markers else match.end() + len(marker)
            end_positions.append((pos, marker))

    # 排序位置
    start_positions.sort()
    end_positions.sort()

    if debug:
        print(f"找到 {len(start_positions)} 个开始标记和 {len(end_positions)} 个结束标记")

    # 匹配开始和结束标记
    for s_pos, s_marker in start_positions:
        # 查找开始位置之后的第一个结束标记
        matching_end = None
        for e_pos, e_marker in end_positions:
            if e_pos > s_pos:
                matching_end = (e_pos, e_marker)
                break

        if matching_end:
            e_pos, e_marker = matching_end
            start = s_pos if include_markers else s_pos + len(s_marker)
            end = e_pos if include_markers else e_pos - len(e_marker)

            chunk_text = text[start:end].strip()
            chunks.append((chunk_text, start, end))

    return chunks