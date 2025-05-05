import os
import re
from typing import Optional

from utils import normalize_text


class DocumentProcessor:
    def __init__(self, input_dir: str):
        self.input_dir = input_dir

    # 方法保持不变，只修改类型注解

    def load_document(self, file_name: str) -> str:
        """加载文档文件，支持.md格式"""
        file_path = os.path.join(self.input_dir, file_name)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return content

    def preprocess_document(self, file_path: str) -> str:
        """预处理文档，保留特殊格式标记"""
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            text = f.read()

        # 保留 (cid:xxx) 格式标记以用于提取
        preserved_text = text

        # 规范化但保留关键格式
        preserved_text = re.sub(r'\r\n', '\n', preserved_text)  # 统一换行符

        # 保留空行以区分段落
        preserved_text = re.sub(r'\n{3,}', '\n\n', preserved_text)  # 将3个以上换行符替换为2个

        return preserved_text

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