# -*- coding: utf-8 -*-

import os
import time

from lxml import etree
from jinja2 import Environment, FileSystemLoader

from src.data_processing.uml_metadata_parser.XsdParser.Expansion.GenerateInterface import generate_interface
from src.data_processing.uml_metadata_parser.XsdParser.Utils import to_pascal_case
from src.data_processing.uml_metadata_parser.XsdParser.Expansion.GenerateWrapper import collect_wrapper_class_names, \
    generate_wrapper_classes
from src.data_processing.uml_metadata_parser.XsdParser.Expansion.InnerInnerExtractor import extract_internals_classes, \
    all_class_info_list
from src.data_processing.uml_metadata_parser.XsdParser.ExtractAttributeGroup import extractAttributeGroup
from src.data_processing.uml_metadata_parser.XsdParser.ExtractComplexType import extractComplexType
from src.data_processing.uml_metadata_parser.XsdParser.ExtractGroup import extractGroup
from src.data_processing.uml_metadata_parser.XsdParser.ExtractSimpleType import extractSimpleType
from src.data_processing.uml_metadata_parser.XsdParser.generateObjFactory import generate_object_factory
if __name__ == "__main__":

    input_dir = 'input'
    output_dir = 'output'
    package_name = 'stdgui.data.entity.schema'
    wrapper_package_name = 'stdgui.data.entity.schema.wrapper'
    interface_package_name = 'stdgui.data.entity.schema.interfaces'
    element_wrapper = 'true'
    extract_inner_class = 'true'
    generate_wrapper = 'true'
    generate_abstract_interface = 'true'

    # 解析XSD文件
    xsdFile = os.path.join(input_dir, 'AUTOSAR_4-2-2.xsd')  # 指定XSD文件路径
    tree = etree.parse(xsdFile)  # 解析XSD文件为树结构
    root = tree.getroot()  # 获取XML的根节点

    # 提取信息
    groups = extractGroup(root, element_wrapper)
    attributeGroups = extractAttributeGroup(root)
    simpleTypes = extractSimpleType(root)  # 提取简单类型信息
    complexTypes, element_complex_type_mappings = extractComplexType(root, element_wrapper, groups,
                                                                     attributeGroups)  # 提取复杂类型信息，传入提取好的group中的element

    # 生成接口名
    interfaces_name = []
    for group_name, group_info in groups.items():
        interfaces_name.append(to_pascal_case(group_name))

    for complexType in complexTypes:
        extract_internals_classes(complexType, output_dir, package_name, None, interfaces_name, groups,
                                  generate_abstract_interface, input_dir, interface_package_name)

        # 在生成内部类后，获取所有类的信息,全局列表
        all_classes_info = all_class_info_list

    # 生成objectfactory
    generate_object_factory(output_dir, package_name, element_complex_type_mappings, None)

    if generate_wrapper:
        # 第一次遍历：收集需要生成的 wrapper 类名
        wrapper_class_names = collect_wrapper_class_names(all_classes_info)

        # 第二次遍历：正式生成 wrapper 类
        generate_wrapper_classes(input_dir, all_classes_info, output_dir, wrapper_package_name, wrapper_class_names, package_name)

    # 将groups、attributeGroups、simpleTypes、complexTypes保存到metadata文件
    metadata_file_path = os.path.join(output_dir, 'metadata.json')


    def serialize_element(value):
        if isinstance(value, etree._Element):
            return etree.tostring(value, encoding='unicode')
        elif isinstance(value, dict):
            return {k: serialize_element(v) for k, v in value.items()}
        else:
            return str(value)


    metadata_content = {
        "groups": {key: serialize_element(value) for key, value in groups.items()},
        "attributeGroups": {key: serialize_element(value) for key, value in attributeGroups.items()},
        "simpleTypes": {index: serialize_element(value) for index, value in enumerate(simpleTypes)},
        "complexTypes": {index: serialize_element(value) for index, value in enumerate(complexTypes)}
    }
    with open(metadata_file_path, 'w', encoding='utf-8') as metadata_file:
        import json
        json.dump(metadata_content, metadata_file, ensure_ascii=False, indent=4)