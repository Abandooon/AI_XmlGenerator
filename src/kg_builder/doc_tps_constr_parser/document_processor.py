import os
import re
from typing import List, Tuple, Dict, Any, Optional

from utils import normalize_text


class DocumentProcessor:
    def __init__(self, input_dir: str):
        self.input_dir = input_dir

    def load_document(self, file_name: str) -> str:
        """加载文档文件，支持.md格式"""
        file_path = os.path.join(self.input_dir, file_name)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return content

    def preprocess_document(self, content: str) -> str:
        """预处理文档内容"""
        # 标准化文本
        normalized = normalize_text(content)

        # 重建段落 - 尝试识别被错误分割的段落
        normalized = self._rebuild_paragraphs(normalized)

        return normalized

    def _rebuild_paragraphs(self, text: str) -> str:
        """
        重建可能被错误分割的段落
        策略: 如果一行不以句号结束且下一行不以大写字母开始，则将它们合并
        """
        lines = text.split('\n')
        result_lines = []

        i = 0
        while i < len(lines):
            current_line = lines[i].rstrip()

            # 检查是否需要与下一行合并
            if (i < len(lines) - 1 and
                    not current_line.endswith(('.', '!', '?', ':', ';')) and
                    not lines[i + 1].strip().startswith(('[', '#', '*', '>', '-')) and
                    (not lines[i + 1].strip() or not lines[i + 1].strip()[0].isupper())):
                # 合并当前行和下一行
                result_lines.append(current_line + ' ' + lines[i + 1].lstrip())
                i += 2
            else:
                result_lines.append(current_line)
                i += 1

        return '\n'.join(result_lines)

    def process(self, file_name: str) -> str:
        """加载并预处理文档"""
        content = self.load_document(file_name)
        return self.preprocess_document(content)