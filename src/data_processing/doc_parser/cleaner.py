# doc_parser/cleaner.py
import re

def clean_text(text: str) -> str:
    """
    对文本进行清洗与标准化（去除多余空白和噪音）。
    输入:
        text (str): 原始文本
    输出:
        str: 清洗后的文本
    """
    return re.sub(r'\s+', ' ', text).strip()
