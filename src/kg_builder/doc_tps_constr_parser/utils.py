import re
import os
import json
from typing import Dict, List, Any, Optional

# 约束ID模式
CONSTRAINT_ID_PATTERN = r"\[(constr|TPS)_(\d+)\]"

# 约束块模式 (匹配整个约束块)
CONSTRAINT_BLOCK_PATTERN = r"\[(constr|TPS)_(\d+)\](.*?)(?:\(cid:100\)(.*?)(?:\(cid:99\)(?:\(\)|\(([A-Z0-9_]+)\))))"

# 条件模式
CONDITIONAL_PATTERNS = [
    r"if\s+(.*?)\s+(?:is|are)\s+(?:set|equal)\s+to\s+(.*?)(?:,|\.|;)",
    r"when\s+(.*?)\s+(?:is|are)\s+(.*?)(?:,|\.|;)",
    r"for\s+(?:any|all)\s+(.*?)(?:,|\.|;)",
]

# 禁止模式
PROHIBITION_PATTERNS = [
    r"(.*?)\s+shall\s+not\s+be\s+set(?:,|\.|;)",
    r"(.*?)\s+(?:shall|must)\s+not\s+(.*?)(?:,|\.|;)",
]

# 范围模式
SCOPE_PATTERNS = [
    r"within\s+(?:one|a|the)\s+(.*?)(?:,|\.|;)",
    r"for\s+(?:any|each|all)\s+(.*?)(?:,|\.|;)",
]

# 重叠模式
OVERLAP_PATTERNS = [
    r"(.*?)\s+(?:shall|must)\s+not\s+overlap(?:,|\.|;)",
    r"(.*?)\s+(?:shall|must)\s+be\s+unique(?:,|\.|;)",
]


def load_json(file_path: str) -> Dict[str, Any]:
    """加载JSON文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data: Any, file_path: str) -> None:
    """保存数据到JSON文件"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def normalize_text(text: str) -> str:
    """标准化文本，处理特殊字符和空白"""
    # 替换特殊的cid标记为更易理解的标记
    text = text.replace("(cid:100)", " <START_RULE> ")
    text = text.replace("(cid:99)()", " <END_RULE> ")

    # 处理可能的参考ID格式
    text = re.sub(r"\(cid:99\)\(([A-Z0-9_]+)\)", r" <END_RULE> <REF_ID>\1</REF_ID>", text)

    # 标准化空白字符
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\s*\n\s*', '\n', text)

    return text.strip()


def extract_reference_id(text: str) -> Optional[str]:
    """从文本中提取参考ID"""
    match = re.search(r"<REF_ID>([A-Z0-9_]+)</REF_ID>", text)
    if match:
        return match.group(1)
    return None


def clean_constraint_text(text: str) -> str:
    """清理约束文本，移除标记等"""
    text = re.sub(r"<START_RULE>|<END_RULE>|<REF_ID>.*?</REF_ID>", "", text)
    return text.strip()