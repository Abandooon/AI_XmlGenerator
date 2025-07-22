import os
from pathlib import Path
import xml.etree.ElementTree as ET
import re


def process_arxml_files(input_dir="."):
    """
    处理arxml文件：1.补全未闭合标签 2.包装 3.格式化

    Args:
        input_dir: 输入目录，默认为当前目录
    """
    input_path = Path(input_dir)

    # 查找所有arxml文件
    arxml_files = list(input_path.glob("*.xml"))
    if not arxml_files:
        print(f"在目录 {input_path} 中未找到arxml文件")
        return

    print(f"找到 {len(arxml_files)} 个arxml文件")

    processed_count = 0

    for arxml_file in arxml_files:
        try:
            print(f"\n处理文件: {arxml_file.name}")

            # 读取原始文件内容
            with open(arxml_file, 'r', encoding='utf-8') as f:
                original_content = f.read().strip()

            if not original_content:
                print(f"跳过空文件: {arxml_file.name}")
                continue

            # 步骤1: 补全未闭合的标签
            print("  步骤1: 补全未闭合标签...")
            completed_content = complete_unclosed_tags(original_content)

            # 步骤2: 包装为完整的AUTOSAR结构
            print("  步骤2: 添加AUTOSAR包装...")
            wrapped_xml = wrap_with_autosar_simple(completed_content)

            # 步骤3: 格式化XML
            print("  步骤3: 格式化XML...")
            try:
                root = ET.fromstring(wrapped_xml)
                formatted_xml = format_xml_simple(root)

                # 写入文件
                with open(arxml_file, 'w', encoding='utf-8') as f:
                    f.write(formatted_xml)

                print(f"  ✅ 处理完成: {arxml_file.name}")
                processed_count += 1

            except ET.ParseError as e:
                print(f"  ❌ XML解析失败: {e}")
                # 保存未格式化但补全的版本
                with open(arxml_file, 'w', encoding='utf-8') as f:
                    f.write(wrapped_xml)
                print(f"  ⚠️  保存为未格式化版本: {arxml_file.name}")
                processed_count += 1

        except Exception as e:
            print(f"❌ 处理失败 {arxml_file.name}: {e}")

    print(f"\n处理完成！成功处理 {processed_count} 个文件")


def wrap_with_autosar_simple(content):
    """简单包装：直接添加AUTOSAR外包装"""
    wrapped_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<AUTOSAR xmlns="http://autosar.org/schema/r4.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://autosar.org/schema/r4.0 AUTOSAR_4-2-2.xsd">
  <AR-PACKAGES>
    <AR-PACKAGE>
      <SHORT-NAME>COM_SWC</SHORT-NAME>
      <ELEMENTS>
{indent_content(content, 8)}
      </ELEMENTS>
    </AR-PACKAGE>
  </AR-PACKAGES>
</AUTOSAR>"""

    return wrapped_xml


def format_xml_simple(root):
    """简单格式化XML，不添加命名空间前缀"""
    # 注册默认命名空间，避免ns0前缀
    ET.register_namespace('', 'http://autosar.org/schema/r4.0')
    ET.register_namespace('xsi', 'http://www.w3.org/2001/XMLSchema-instance')

    # 添加缩进
    indent_xml(root)

    # 转换为字符串
    xml_str = ET.tostring(root, encoding='unicode')

    # 添加XML声明
    formatted_xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str

    return formatted_xml


# 移除不需要的extract_core_content和wrap_with_autosar函数

def complete_unclosed_tags(content):
    """补全未闭合的标签"""
    if not content.strip():
        return content

    # 分析标签栈
    tag_stack = []
    lines = content.split('\n')

    for line in lines:
        # 查找所有开始标签
        open_tags = re.findall(r'<([^/][^>\s]*)[^>]*(?<!/)>', line)
        for tag in open_tags:
            # 清理标签名，移除属性
            clean_tag = tag.split()[0] if ' ' in tag else tag
            tag_stack.append(clean_tag)

        # 查找所有结束标签
        close_tags = re.findall(r'</([^>\s]+)>', line)
        for tag in close_tags:
            # 从栈中移除匹配的开始标签
            if tag_stack and tag_stack[-1] == tag:
                tag_stack.pop()
            elif tag in tag_stack:
                # 如果不在栈顶，移除第一个匹配的标签
                tag_stack.remove(tag)

    # 补全未闭合的标签
    completed_content = content

    if tag_stack:
        print(f"    发现未闭合标签: {tag_stack}")
        # 按相反顺序添加结束标签
        for tag in reversed(tag_stack):
            completed_content += f'\n</{tag}>'
        print(f"    已补全 {len(tag_stack)} 个结束标签")

    return completed_content


def indent_content(content, spaces):
    """为内容添加指定的缩进"""
    if not content.strip():
        return content

    indent = ' ' * spaces
    lines = content.split('\n')
    indented_lines = []

    for line in lines:
        if line.strip():  # 只为非空行添加缩进
            indented_lines.append(indent + line)
        else:
            indented_lines.append(line)

    return '\n'.join(indented_lines)

def indent_xml(elem, level=0):
    """递归添加XML缩进"""
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for child in elem:
            indent_xml(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


if __name__ == "__main__":
    process_arxml_files()