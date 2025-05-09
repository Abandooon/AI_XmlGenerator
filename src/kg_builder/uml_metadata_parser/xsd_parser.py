# -*- coding: utf-8 -*-

import os

from lxml import etree
from src.kg_builder.uml_metadata_parser.XsdParser.Expansion.GenerateWrapper import collect_wrapper_class_names, \
    generate_wrapper_classes
from src.kg_builder.uml_metadata_parser.XsdParser.Expansion.InnerInnerExtractor import extract_internals_classes, \
    all_class_info_list, extract_inner_class_info_list
from src.kg_builder.uml_metadata_parser.XsdParser.ExtractAttributeGroup import extractAttributeGroup
from src.kg_builder.uml_metadata_parser.XsdParser.ExtractComplexType import extractComplexType
from src.kg_builder.uml_metadata_parser.XsdParser.ExtractGroup import extractGroup
from src.kg_builder.uml_metadata_parser.XsdParser.ExtractSimpleType import extractSimpleType
from src.kg_builder.uml_metadata_parser.XsdParser.Utils import to_pascal_case
from src.kg_builder.uml_metadata_parser.XsdParser.generateObjFactory import generate_object_factory

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
        extract_inner_class = extract_inner_class_info_list

    # 生成objectfactory
    generate_object_factory(output_dir, package_name, element_complex_type_mappings, None)

    if generate_wrapper:
        # 第一次遍历：收集需要生成的 wrapper 类名
        wrapper_class_names = collect_wrapper_class_names(all_classes_info)

        # 第二次遍历：正式生成 wrapper 类
        generate_wrapper_classes(input_dir, all_classes_info, output_dir, wrapper_package_name, wrapper_class_names,
                                 package_name)

    # 将groups、attributeGroups、simpleTypes、complexTypes保存到metadata文件
    metadata_file_path = os.path.join(output_dir, 'metadata.json')


    def improved_serialize_element(value):
        """更智能地序列化元素，保留JSON兼容的数据结构"""
        if isinstance(value, etree._Element):
            return etree.tostring(value, encoding='unicode')
        elif isinstance(value, dict):
            return {k: improved_serialize_element(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [improved_serialize_element(item) for item in value]
        elif isinstance(value, (int, float, bool, str, type(None))):
            # 这些类型直接兼容JSON，无需转换
            return value
        else:
            # 不兼容JSON的类型转为字符串
            return str(value)


    # 从对象获取特定字段值的函数
    def get_field_value(obj, field):
        """从对象尝试获取字段值"""
        if isinstance(obj, dict) and field in obj:
            return obj[field]
        elif hasattr(obj, field):
            return getattr(obj, field)
        elif hasattr(obj, 'get') and callable(obj.get):
            return obj.get(field)
        return None


    # 构建metadata内容
    metadata_content = {
        "groups": {},
        "attributeGroups": {key: improved_serialize_element(value) for key, value in attributeGroups.items()},
        "simpleTypes": {},
        "complexTypes": {},
        "extract_inner_class": {}
    }

    # 处理groups - 使用'name'作为键
    for key, value in groups.items():
        name = get_field_value(value, 'name') or key
        metadata_content["groups"][name] = improved_serialize_element(value)

    # 处理simpleTypes - 使用'id'作为键
    for index, value in enumerate(simpleTypes):
        id_value = get_field_value(value, 'id')
        if id_value:
            metadata_content["simpleTypes"][id_value] = improved_serialize_element(value)
        else:
            metadata_content["simpleTypes"][f"type_{index}"] = improved_serialize_element(value)

    # 处理complexTypes - 使用'document_name'作为键
    for index, value in enumerate(complexTypes):
        doc_name = get_field_value(value, 'document_name')
        if doc_name:
            metadata_content["complexTypes"][doc_name] = improved_serialize_element(value)
        else:
            metadata_content["complexTypes"][f"type_{index}"] = improved_serialize_element(value)

    # 处理extract_inner_class - 使用可能的标识符
    for index, value in enumerate(extract_inner_class):
        # 尝试使用多个可能的字段作为标识符
        identifier = (get_field_value(value, 'name') or
                      get_field_value(value, 'id') or
                      get_field_value(value, 'document_name'))
        if identifier:
            metadata_content["extract_inner_class"][identifier] = improved_serialize_element(value)
        else:
            metadata_content["extract_inner_class"][f"class_{index}"] = improved_serialize_element(value)

    # 保存为JSON
    with open(metadata_file_path, 'w', encoding='utf-8') as metadata_file:
        import json

        json.dump(metadata_content, metadata_file, ensure_ascii=False, indent=4)
