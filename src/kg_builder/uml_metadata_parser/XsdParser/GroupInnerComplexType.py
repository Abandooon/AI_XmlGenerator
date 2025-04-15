import re

from src.data_processing.uml_metadata_parser.XsdParser.ExtractChoiceElement import process_choice_elements
from src.data_processing.uml_metadata_parser.XsdParser.ExtractExtensionBaseType import extractBaseType
from src.data_processing.uml_metadata_parser.XsdParser.TypeMapping import mapXsdTypeToJava
from src.data_processing.uml_metadata_parser.XsdParser.ExtractChoiceGroup import process_choiceRef
from src.data_processing.uml_metadata_parser.XsdParser.Utils import to_camel_case,to_pascal_case


def process_group_inner_complex_type(root, element, element_wrapper):
    inner_complex_types = []  # 初始化列表，用于存储内部复杂类型信息

    # 查找element中的complexType标签
    complex_type = element.find("./{http://www.w3.org/2001/XMLSchema}complexType")
    # 可能有内部类的内部类，最多嵌套两层
    if complex_type is not None:
        element_name = element.get('name')  # 获取元素名称----->父element
        inner_class_name = to_pascal_case(element_name)  # 将元素名称转换为PascalCase，用作内部类的名称

        attributes = []  # 初始化列表，用于存储属性信息
        innerInnerClass = []
        extendsClass = None
        wrapperElement = False

        for child in complex_type:
            if child.tag.endswith('choice'):
                # 处理 complexType 中的 choice 标签------->嵌套内部类要继续返回出去，要根据maxoccurs处理element
                choice = child
                #传入element_name，用于生成wrapper注解
                #返回的是当前内部类的成员和内部类，应该进一步提取，先调试一步步往外提，还没处理嵌套内部类
                choice_elements, innerInnerClass, wrapperElement = process_choice(root, choice, element_name, element_wrapper)
                attributes.extend(choice_elements)
            elif child.tag.endswith('simpleContent'):
                # 处理simpleContent
                simple_content = child
                extension = simple_content.find("./{http://www.w3.org/2001/XMLSchema}extension")
                if extension is not None:
                    baseName = extension.get('base').split(':')[-1]
                    baseTypeInfo = extractBaseType(root, baseName)
                    if baseTypeInfo is not None:
                        if baseTypeInfo['extendsClass'] is not None:
                            extendsClass = baseTypeInfo['extendsClass']
                        else:
                            # 如果继承的是simpleType就要加属性字段，如果是继承枚举类，需要@xmlElement；否则@XmlValue
                            attributes.append({
                                'type': baseTypeInfo['type'],
                                'annotation': baseTypeInfo['annotation'],
                            })
                for attr in extension.findall("./{http://www.w3.org/2001/XMLSchema}attribute"):
                    attr_name = attr.get('name')  # 获取属性名称
                    attr_type = mapXsdTypeToJava(attr.get('type').split(':')[-1], context='attribute_group')  # 将属性类型映射为Java类型
                    attributes.append({
                        'name': to_camel_case(attr_name),
                        'type': attr_type,
                        'annotation': '@XmlAttribute(name="{}")'.format(attr_name)  # 为属性生成@XmlAttribute注解
                    })

        inner_complex_types.append({
            'InnerClassName': inner_class_name,
            'InnerClassAttributes': attributes,
            'extendsClass': extendsClass,
            'innerInnerClass': innerInnerClass,
            'xmlType':element_name
        })

    return inner_complex_types, wrapperElement  # 返回内部复杂类型信息列表

#处理group中内部类的choice，传入上一级的element_name用于生成wrapper注解
def process_choice(root, choice, element_name, element_wrapper):
    elements = []  # 初始化列表，用于存储choice中的元素
    innerClass = []
    maxOccurs = choice.get('maxOccurs')
    wrapperElement = False

    for child in choice:
        if child.tag.endswith('element'):
            # 处理choice中的元素，传入当前choice的maxoccurs和父element的name（wrapper注解名）
            elements, innerClass, wrapperElement = (process_choice_elements(root, choice, maxOccurs, element_name, element_wrapper))
        elif child.tag.endswith('group'):  # element和group没有同时存在，choice下为group的只有两个
            refName = child.get('ref').split(':')[-1]
            elements, innerClass = process_choiceRef(root, refName, maxOccurs,element_wrapper)

    return elements, innerClass, wrapperElement  # 返回元素列表




