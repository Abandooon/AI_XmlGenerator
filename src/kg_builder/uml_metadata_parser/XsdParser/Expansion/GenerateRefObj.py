# -*- coding: utf-8 -*-
import os

from lxml import etree

from src.data_processing.uml_metadata_parser.XsdParser.Utils import to_pascal_case


def get_subtypes(input_dir, enumType):
    # XsdIndex.arxml 文件路径
    arxml_file_path = os.path.join(input_dir, 'XsdIndex.arxml')

    # 解析 XsdIndex.arxml 文件
    tree = etree.parse(arxml_file_path)
    root = tree.getroot()

    # # 定义 XML 命名空间
    # ns = {'': 'http://autosar.org/schema/r4.0'}  # 默认命名空间

    # 查找 <group> 元素，其中 @name 等于 enumType
    xpath_query = f'//group[@name="{enumType}"]/@complexTypes'
    complex_types_str = root.xpath(xpath_query)

    # 如果找不到，返回空列表
    if not complex_types_str:
        return []

    # 获取 complexTypes 字符串，并按 '//' 分割
    complex_types_str = complex_types_str[0]
    ref_objs = [to_pascal_case(ref_obj.strip()) for ref_obj in complex_types_str.split('//') if ref_obj.strip()]

    # 返回 RefObjs[]
    return [ref_obj.strip() for ref_obj in ref_objs if ref_obj.strip()]
#编写方法，主类中ref属性是否要生成get方法匹配这里的返回值，如果匹配到则不要
def get_complex_ref(input_dir):
    """
    从 ComplexRef.arxml 文件中提取所有 <xsd:complexType> 的 name 属性值，并将其转换为 PascalCase。

    :param input_dir: 包含 ComplexRef.arxml 文件的目录路径
    :return: 一个包含 PascalCase 格式的 complexType name 的列表
    """
    # XsdIndex.arxml 文件路径
    arxml_file_path = os.path.join(input_dir, 'ComplexRef.arxml')

    # 解析 ComplexRef.arxml 文件
    tree = etree.parse(arxml_file_path)
    root = tree.getroot()

    # 定义命名空间映射
    namespaces = {'xsd': "http://www.w3.org/2001/XMLSchema"}

    # 查找所有 <xsd:complexType> 的 name 属性
    xpath_query = '//xsd:complexType/@name'
    complex_types = root.xpath(xpath_query, namespaces=namespaces)

    # 转换为 PascalCase 格式
    complex_types_list = [to_pascal_case(name) for name in complex_types]
    return complex_types_list


def get_different_tag_elements(input_dir):
    """
    从 DifferentTagsWithElements.xml 文件中提取 simpleTypeName 和 elementClass，并将其转换为驼峰命名格式。

    :param input_dir: 包含 DifferentTagsWithElements.xml 文件的目录路径
    :return: 一个包含字典的列表，每个字典有 simpleTypeName 和 elementClass，均为驼峰命名格式
    """
    # DifferentTagsWithElements.xml 文件路径
    xml_file_path = os.path.join(input_dir, 'DifferentTagsWithElements.xml')

    # 解析 XML 文件
    tree = etree.parse(xml_file_path)
    root = tree.getroot()

    # 查找所有 <element> 标签
    elements = root.xpath('//element', namespaces={'xsd': 'http://www.w3.org/2001/XMLSchema'})

    # 提取 simpleTypeName 和 elementClass，并转换为驼峰命名格式
    differentTagsElements = []
    for element in elements:
        simple_type_name = element.attrib.get('simpleTypeName', '')
        element_class = element.attrib.get('elementClass', '')
        ref_dest_name = element.attrib.get('name', '')
        ref_dest_type=element.attrib.get('type','')

        # 转换为驼峰命名格式
        simple_type_name_camel = to_pascal_case(simple_type_name)
        element_class_camel = to_pascal_case(element_class)

        differentTagsElements.append({
            'simpleTypeName': simple_type_name_camel,
            'elementClass': element_class_camel,
            'refDestName':ref_dest_name,
            'refDestType':ref_dest_type
        })

    return differentTagsElements

