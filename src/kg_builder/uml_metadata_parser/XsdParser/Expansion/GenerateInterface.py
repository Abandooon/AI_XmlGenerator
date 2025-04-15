# -*- coding: utf-8 -*-
import os

from jinja2 import Environment, FileSystemLoader
from lxml import etree

from src.data_processing.uml_metadata_parser.XsdParser.Utils import to_pascal_case


def generate_interface(input_dir, output_dir, groups, interface_package_name,package_name):

    interfaces_name=[]

    # 读取继承信息
    xml_file_path = os.path.join(input_dir, 'generalizations.xml')
    # 解析 XML 文件
    tree = etree.parse(xml_file_path)
    root = tree.getroot()

    # 查找所有 <Element> 标签
    elements = root.xpath('//Element', namespaces={'xmi': 'http://www.omg.org/spec/XMI/20131001'})

    element_inheritance = {}
    for element in elements:
        element_name = element.get('name')
        generalizations = element.xpath('Generalization', namespaces={'xmi': 'http://www.omg.org/spec/XMI/20131001'})

        # 如果有继承关系，拼接所有父类的名称
        father_names = [gen.get('fatherName') for gen in generalizations]
        if father_names:
            element_inheritance[element_name] = ', '.join(father_names)  # 用逗号拼接父类名称

    # 遍历 group 匹配继承关系
    for group_name, group_info in groups.items():
        extends_interface = False
        # 获取与 group 相关的继承关系
        if to_pascal_case(group_name) in element_inheritance:
            # 如果 element 与 group_name 匹配，则添加继承信息
            extends_interface = True
            father_name = element_inheritance[to_pascal_case(group_name)]


