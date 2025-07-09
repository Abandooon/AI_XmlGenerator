#!/usr/bin/env python3
"""
通用 JSON 转 AUTOSAR ARXML 转换器
自动处理任意 JSON 结构，无需硬编码标签
"""

import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
from pathlib import Path
from typing import Dict, Any, List, Union
import os
from collections import OrderedDict


class GenericJsonToArxmlConverter:
    """通用 JSON 转 ARXML 转换器"""

    def __init__(self):
        # AUTOSAR 命名空间
        self.namespaces = {
            '': 'http://autosar.org/schema/r4.0',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
        }

        # 注册命名空间
        for prefix, uri in self.namespaces.items():
            ET.register_namespace(prefix, uri)

        # AUTOSAR 元素顺序定义（根据标准）
        # 这里定义了一些常见元素的顺序，可以根据需要扩展
        self.element_order = {
            'APPLICATION-SW-COMPONENT-TYPE': [
                'SHORT-NAME',
                'LONG-NAME',
                'DESC',
                'CATEGORY',
                'ADMIN-DATA',
                'INTRODUCTION',
                'ANNOTATIONS',
                'VARIATION-POINT',
                'CONSTANT-MAPPING-REFS',
                'DATA-TYPE-MAPPING-REFS',
                'INSTANTIATION-DATA-DEF-PROPS',
                'PORTS',
                'PORT-GROUPS',
                'UNIT-GROUP-REFS',
                'INTERNAL-BEHAVIORS',
                'SYMBOL-PROPS'
            ],
            'PORTS': [
                'P-PORT-PROTOTYPE',
                'R-PORT-PROTOTYPE',
                'PR-PORT-PROTOTYPE'
            ],
            'P-PORT-PROTOTYPE': [
                'SHORT-NAME',
                'LONG-NAME',
                'DESC',
                'CATEGORY',
                'ADMIN-DATA',
                'INTRODUCTION',
                'ANNOTATIONS',
                'CLIENT-SERVER-ANNOTATIONS',
                'DELEGATED-PORT-ANNOTATION',
                'IO-HW-ABSTRACTION-SERVER-ANNOTATIONS',
                'MODE-PORT-ANNOTATIONS',
                'NV-DATA-PORT-ANNOTATIONS',
                'PARAMETER-PORT-ANNOTATIONS',
                'SENDER-RECEIVER-ANNOTATIONS',
                'TRIGGER-PORT-ANNOTATIONS',
                'VARIATION-POINT',
                'PROVIDED-COM-SPECS',
                'PROVIDED-INTERFACE-TREF'
            ],
            'R-PORT-PROTOTYPE': [
                'SHORT-NAME',
                'LONG-NAME',
                'DESC',
                'CATEGORY',
                'ADMIN-DATA',
                'INTRODUCTION',
                'ANNOTATIONS',
                'CLIENT-SERVER-ANNOTATIONS',
                'DELEGATED-PORT-ANNOTATION',
                'IO-HW-ABSTRACTION-SERVER-ANNOTATIONS',
                'MODE-PORT-ANNOTATIONS',
                'NV-DATA-PORT-ANNOTATIONS',
                'PARAMETER-PORT-ANNOTATIONS',
                'SENDER-RECEIVER-ANNOTATIONS',
                'TRIGGER-PORT-ANNOTATIONS',
                'VARIATION-POINT',
                'REQUIRED-COM-SPECS',
                'REQUIRED-INTERFACE-TREF'
            ],
            'SWC-INTERNAL-BEHAVIOR': [
                'SHORT-NAME',
                'LONG-NAME',
                'DESC',
                'CATEGORY',
                'ADMIN-DATA',
                'INTRODUCTION',
                'ANNOTATIONS',
                'VARIATION-POINT',
                'DATA-TYPE-MAPPING-REFS',
                'EXCLUSIVE-AREAS',
                'INTER-RUNNABLE-VARIABLES',
                'CALIBRATION-PARAMETER-VALUE-SETS',
                'CONSTANT-VALUE-MAPPING-REFS',
                'DATA-TYPE-MAPPING-REFS',
                'INSTANTIATION-DATA-DEF-PROPS',
                'STATIC-MEMORYS',
                'EVENTS',
                'EXPLICIT-INTER-RUNNABLE-VARIABLES',
                'HANDLE-TERMINATION-AND-RESTART',
                'IMPLICIT-INTER-RUNNABLE-VARIABLES',
                'INCLUDED-DATA-TYPE-SETS',
                'INCLUDED-MODE-DECLARATION-GROUP-SETS',
                'INSTANTIATION-DATA-DEF-PROPS',
                'PER-INSTANCE-MEMORYS',
                'PER-INSTANCE-PARAMETERS',
                'PORT-API-OPTIONS',
                'RUNNABLES',
                'SERVICE-DEPENDENCYS',
                'SHARED-PARAMETERS',
                'SUPPORTS-MULTIPLE-INSTANTIATION',
                'VARIATION-POINT-PROXYS'
            ],
            'TIMING-EVENT': [
                'SHORT-NAME',
                'START-ON-EVENT-REF',
                'PERIOD',
                'OFFSET'
            ],
            'RUNNABLE-ENTITY': [
                'SHORT-NAME',
                'LONG-NAME',
                'DESC',
                'CATEGORY',
                'ADMIN-DATA',
                'INTRODUCTION',
                'ANNOTATIONS',
                'ARGUMENTS',
                'CAN-BE-INVOKED-CONCURRENTLY',
                'DATA-READ-ACCESSS',
                'DATA-RECEIVE-POINT-BY-ARGUMENTS',
                'DATA-RECEIVE-POINT-BY-VALUES',
                'DATA-SEND-POINTS',
                'DATA-WRITE-ACCESSS',
                'EXCLUSIVE-AREA-REFS',
                'MINIMUM-START-INTERVAL',
                'MODE-ACCESS-POINTS',
                'MODE-SWITCH-POINTS',
                'PARAMETER-ACCESSS',
                'READ-LOCAL-VARIABLES',
                'SERVER-CALL-POINTS',
                'SYMBOL',
                'WAIT-POINTS',
                'WRITTEN-LOCAL-VARIABLES'
            ],
            'VARIABLE-ACCESS': [
                'SHORT-NAME',
                'LONG-NAME',
                'DESC',
                'CATEGORY',
                'ADMIN-DATA',
                'INTRODUCTION',
                'ANNOTATIONS',
                'VARIATION-POINT',
                'ACCESSED-VARIABLE',
                'SCOPE',
                'VARIABLE-IN-ATOMIC-SWC-TYPE-INSTANCE-REF'
            ]
        }

    def convert_folder(self, input_folder: str, output_folder: str):
        """
        批量转换文件夹中的所有 JSON 文件

        Args:
            input_folder: 输入文件夹路径
            output_folder: 输出文件夹路径
        """
        input_path = Path(input_folder)
        output_path = Path(output_folder)

        # 创建输出目录
        output_path.mkdir(parents=True, exist_ok=True)

        # 查找所有 JSON 文件
        json_files = list(input_path.rglob("*.json"))

        if not json_files:
            print(f"❌ 在 {input_folder} 中没有找到 JSON 文件")
            return

        print(f"📁 找到 {len(json_files)} 个 JSON 文件")

        # 转换每个文件
        for json_file in json_files:
            # 计算相对路径
            relative_path = json_file.relative_to(input_path)

            # 构建输出路径
            output_file = output_path / relative_path.with_suffix('.arxml')

            # 创建输出目录
            output_file.parent.mkdir(parents=True, exist_ok=True)

            try:
                print(f"\n📄 转换: {relative_path}")
                self.convert_file(json_file, output_file)
                print(f"   ✅ 成功 -> {output_file.relative_to(output_path)}")
            except Exception as e:
                print(f"   ❌ 失败: {str(e)}")

    def convert_file(self, json_path: Union[str, Path], output_path: Union[str, Path]):
        """
        转换单个 JSON 文件为 ARXML

        Args:
            json_path: JSON 文件路径
            output_path: 输出 ARXML 文件路径
        """
        json_path = Path(json_path)
        output_path = Path(output_path)

        # 读取 JSON，保持顺序
        with open(json_path, 'r', encoding='utf-8') as f:
            # 使用 object_pairs_hook 保持 JSON 中的顺序
            json_data = json.load(f, object_pairs_hook=OrderedDict)

        # 转换为 XML
        xml_str = self.convert_json_to_xml(json_data)

        # 保存文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(xml_str)

    def convert_json_to_xml(self, json_data: Dict[str, Any]) -> str:
        """
        将 JSON 数据转换为 ARXML 字符串

        Args:
            json_data: JSON 数据字典

        Returns:
            格式化的 XML 字符串
        """
        # 创建根元素
        root = ET.Element('AUTOSAR')
        root.set('xmlns', self.namespaces[''])
        root.set('{http://www.w3.org/2001/XMLSchema-instance}schemaLocation',
                 'http://autosar.org/schema/r4.0 AUTOSAR_4-2-2.xsd')

        # 创建基本结构
        ar_packages = ET.SubElement(root, 'AR-PACKAGES')
        ar_package = ET.SubElement(ar_packages, 'AR-PACKAGE')

        # 添加包名
        short_name = ET.SubElement(ar_package, 'SHORT-NAME')
        short_name.text = 'COM_SWC'

        # 创建 ELEMENTS
        elements = ET.SubElement(ar_package, 'ELEMENTS')

        # 递归转换 JSON 内容
        self._convert_json_to_element(elements, json_data)

        # 重新排序所有元素（根据 AUTOSAR 标准）
        self._reorder_element(root)

        # 格式化输出
        return self._prettify_xml(root)

    def _reorder_element(self, elem: ET.Element):
        """
        根据 AUTOSAR 标准重新排序元素的子元素

        Args:
            elem: 要重新排序的元素
        """
        tag_name = elem.tag

        # 检查是否有定义的顺序
        if tag_name not in self.element_order:
            # 如果没有定义顺序，递归处理子元素
            for child in elem:
                self._reorder_element(child)
            return

        # 获取定义的顺序
        order = self.element_order[tag_name]

        # 创建一个字典来存储子元素
        children_dict = {}
        for child in elem:
            child_tag = child.tag
            if child_tag not in children_dict:
                children_dict[child_tag] = []
            children_dict[child_tag].append(child)

        # 移除所有子元素
        for child in list(elem):
            elem.remove(child)

        # 按照定义的顺序重新添加子元素
        for tag in order:
            if tag in children_dict:
                for child in children_dict[tag]:
                    elem.append(child)
                    # 递归处理子元素
                    self._reorder_element(child)

        # 添加不在顺序列表中的元素（保持原有顺序）
        for tag, children in children_dict.items():
            if tag not in order:
                for child in children:
                    elem.append(child)
                    # 递归处理子元素
                    self._reorder_element(child)

    def _convert_json_to_element(self, parent: ET.Element, data: Any, tag_name: str = None):
        """
        递归转换 JSON 数据到 XML 元素

        这是核心方法，处理所有可能的 JSON 结构：
        - 字典 -> XML 元素
        - 列表 -> 多个相同标签的元素
        - 基本类型 -> 文本内容
        - @ 开头的键 -> XML 属性
        - #text 键 -> 元素文本内容
        """
        if isinstance(data, dict):
            # 如果是顶层字典且没有指定标签名，使用键作为标签
            if tag_name is None:
                for key, value in data.items():
                    if not key.startswith('@'):  # 跳过属性
                        self._convert_json_to_element(parent, value, key)
            else:
                # 检查是否是空字典
                if not data:
                    # 空字典：创建自闭合元素 <ELEMENT/>
                    elem = ET.SubElement(parent, tag_name)
                    return

                # 创建元素
                elem = ET.SubElement(parent, tag_name)

                # 处理属性和子元素
                text_content = None
                has_children = False

                for key, value in data.items():
                    if key.startswith('@'):
                        # XML 属性
                        attr_name = key[1:]  # 移除 @ 前缀
                        elem.set(attr_name, str(value))
                    elif key == '#text':
                        # 元素文本内容
                        text_content = str(value)
                    else:
                        # 子元素
                        has_children = True
                        self._convert_json_to_element(elem, value, key)

                # 设置文本内容（如果有）
                if text_content is not None:
                    elem.text = text_content

        elif isinstance(data, list):
            # 列表：为每个项创建相同标签的元素
            for item in data:
                self._convert_json_to_element(parent, item, tag_name)

        else:
            # 基本类型：创建带文本的元素
            if tag_name:
                elem = ET.SubElement(parent, tag_name)
                # 处理 None 值
                if data is not None:
                    elem.text = str(data)

    def _prettify_xml(self, elem: ET.Element) -> str:
        """
        格式化 XML 输出

        Args:
            elem: XML 根元素

        Returns:
            格式化的 XML 字符串
        """
        # 转换为字符串
        rough_string = ET.tostring(elem, encoding='unicode')

        # 使用 minidom 格式化
        reparsed = minidom.parseString(rough_string)

        # 获取格式化的 XML
        pretty_xml = reparsed.toprettyxml(indent="  ", encoding=None)

        # 清理输出
        lines = pretty_xml.split('\n')

        # 移除空行
        lines = [line.rstrip() for line in lines if line.strip()]

        # 确保 XML 声明正确
        if not lines[0].startswith('<?xml'):
            lines.insert(0, '<?xml version="1.0" encoding="UTF-8"?>')
        else:
            # 替换为标准声明
            lines[0] = '<?xml version="1.0" encoding="UTF-8"?>'

        return '\n'.join(lines)


def main():
    """主函数"""
    # ========== 配置参数 ==========
    # 修改这里的路径来指定输入输出文件夹
    INPUT_FOLDER = "output/min_promote_rag"  # 输入文件夹路径
    OUTPUT_FOLDER = "output/min_promote_rag/output"  # 输出文件夹路径
    # ==============================

    print("=" * 60)
    print("🔄 JSON to ARXML Converter")
    print("=" * 60)
    print(f"📂 输入文件夹: {os.path.abspath(INPUT_FOLDER)}")
    print(f"📂 输出文件夹: {os.path.abspath(OUTPUT_FOLDER)}")
    print("=" * 60)

    # 检查输入文件夹是否存在
    if not os.path.exists(INPUT_FOLDER):
        print(f"❌ 错误：输入文件夹 '{INPUT_FOLDER}' 不存在！")
        print("\n请执行以下操作：")
        print(f"1. 创建文件夹: {os.path.abspath(INPUT_FOLDER)}")
        print("2. 将要转换的 JSON 文件放入该文件夹")
        print("3. 重新运行此脚本")
        return

    # 创建转换器实例
    converter = GenericJsonToArxmlConverter()

    # 执行转换
    converter.convert_folder(INPUT_FOLDER, OUTPUT_FOLDER)

    print("\n" + "=" * 60)
    print("✅ 转换完成！")
    print(f"📂 输出文件保存在: {os.path.abspath(OUTPUT_FOLDER)}")


if __name__ == "__main__":
    main()

# ========== 使用说明 ==========
# 1. 修改 main() 函数中的 INPUT_FOLDER 和 OUTPUT_FOLDER 变量
# 2. 将 JSON 文件放入 INPUT_FOLDER 文件夹
# 3. 直接运行脚本（右键运行或 python script.py）
# 4. 转换后的 ARXML 文件将保存在 OUTPUT_FOLDER 文件夹中
#
# JSON 格式约定：
# - 普通键值对 -> XML 元素
# - @ 开头的键 -> XML 属性（如 "@UUID": "xxx"）
# - #text 键 -> 元素文本内容
# - 数组 -> 多个相同标签的元素
# ==============================