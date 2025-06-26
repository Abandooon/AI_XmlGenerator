# src/generation/processors/xml_postprocessor.py
import re
import xml.etree.ElementTree as ET
from typing import Tuple


class XMLPostProcessor:
    """XML后处理器"""

    def __init__(self):
        """初始化XML后处理器"""
        pass

    def clean_generated_xml(self, raw_xml: str) -> str:
        """清理生成的XML"""

        # 1. 移除多余的文本
        xml_content = self._extract_xml_content(raw_xml)

        # 2. 修复常见格式问题
        xml_content = self._fix_common_issues(xml_content)

        # 3. 验证格式
        is_valid, cleaned_xml = self._validate_and_clean(xml_content)

        return cleaned_xml if is_valid else xml_content

    def _extract_xml_content(self, text: str) -> str:
        """提取XML内容"""

        # 查找XML开始和结束标签
        xml_start = text.find('<?xml')
        if xml_start == -1:
            xml_start = text.find('<')

        if xml_start == -1:
            return text

        # 从XML开始位置截取
        xml_content = text[xml_start:]

        # 移除XML后的多余文本
        lines = xml_content.split('\n')
        clean_lines = []

        for line in lines:
            clean_lines.append(line)
            # 如果遇到根元素结束标签，停止
            if re.search(r'</[^>]*>$', line.strip()) and len(clean_lines) > 5:
                break

        return '\n'.join(clean_lines)

    def _fix_common_issues(self, xml_content: str) -> str:
        """修复常见XML问题"""

        # 移除重复的XML声明
        xml_decl_count = xml_content.count('<?xml')
        if xml_decl_count > 1:
            first_decl = xml_content.find('<?xml')
            first_decl_end = xml_content.find('?>', first_decl) + 2
            xml_without_first = xml_content[first_decl_end:]
            xml_without_duplicates = xml_without_first.replace('<?xml', '<!--xml')
            xml_content = xml_content[:first_decl_end] + xml_without_duplicates

        # 修复未闭合的标签（简单处理）
        xml_content = re.sub(r'<([^/>]+)>([^<]*?)(?=<[^/]|$)', r'<\1>\2</\1>', xml_content)

        return xml_content

    def _validate_and_clean(self, xml_content: str) -> Tuple[bool, str]:
        """验证和清理XML"""

        try:
            # 尝试解析XML
            ET.fromstring(xml_content)
            return True, xml_content
        except ET.ParseError as e:
            print(f"XML parsing error: {e}")
            return False, xml_content