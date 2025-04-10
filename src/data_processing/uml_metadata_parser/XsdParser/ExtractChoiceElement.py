from src.data_processing.uml_metadata_parser.XsdParser.ExtractExtensionBaseType import extractBaseType
from src.data_processing.uml_metadata_parser.XsdParser.TypeMapping import mapXsdTypeToJava
from src.data_processing.uml_metadata_parser.XsdParser.Utils import to_pascal_case,to_camel_case


def process_choice_elements(root, choice, maxOccurs, fatherElementName, element_wrapper):
    #这里是用来生成@xmlelementWrapper注解的，
    elements = []
    inner_classes = []
    #设置wrapperelement记录当前内部类是否生成wrapper，若是则要改主类element且不生成内部类
    wrapperElement = False
    #判断有几个element,如果只有一个，且choice为unbounded且开启了wrapper，不生成内部类，直接把list<>放到主类中，注解加wrapper
    if len(choice.findall(
            "./{http://www.w3.org/2001/XMLSchema}element")) == 1 and maxOccurs != '1' and element_wrapper:
        single_element = choice.find("./{http://www.w3.org/2001/XMLSchema}element")
        # 如果single_element没有complextype
        innerComplextype = single_element.find("./{http://www.w3.org/2001/XMLSchema}complexType")
        wrapperElement = True
        if innerComplextype is None:
            element_name = single_element.get('name')  # 获取元素名称
            element_type = single_element.get('type')
            element_type = mapXsdTypeToJava(element_type.split(':')[-1], context='group')  # 将类型映射为Java类型
            elements.append({
                'name': to_camel_case(element_name),
                'type': 'ArrayList<{}>'.format(element_type), #现在还是存在内部类中的，应该在外层提取到主类中
                # 'annotation': '@XmlElement(name="{}")'.format(element_name)
                'annotation': '@XmlElementWrapper(name="{}")\n@XmlElement(name="{}")'.format(fatherElementName, element_name),
                'maxOccurs': maxOccurs
            })
        #wrapper，有嵌套内部类，只生成最内层类做为内部类
        else:
            element_name = single_element.get('name')
            complex_type = single_element.find("./{http://www.w3.org/2001/XMLSchema}complexType")
            elements.append({
                'name': to_camel_case(element_name),
                'type': 'ArrayList<{}>'.format(to_pascal_case(element_name)),
                # 'annotation': '@XmlElement(name="{}")'.format(element_name)
                'annotation': '@XmlElementWrapper(name="{}")\n@XmlElement(name="{}")'.format(fatherElementName,
                                                                                             element_name),
                'maxOccurs': maxOccurs
            })
            inner_class_name = to_pascal_case(element_name)  # 将元素名称转换为PascalCase，用作内部类的名称
            inner_complex_types = []  # 初始化列表，用于存储内部复杂类型信息
            attributes = []  # 初始化列表，用于存储属性信息
            innerInnerClass = []
            extendsClass = None
            # 处理simpleContent
            simple_content = complex_type.find("./{http://www.w3.org/2001/XMLSchema}simpleContent")
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
                            # 'annotationName': baseTypeInfo['annotationName']
                        })
            for attr in extension.findall("./{http://www.w3.org/2001/XMLSchema}attribute"):
                attr_name = attr.get('name')  # 获取属性名称
                attr_type = mapXsdTypeToJava(attr.get('type').split(':')[-1],
                                             context='attribute_group')  # 将属性类型映射为Java类型
                attributes.append({
                    'name': to_camel_case(attr_name),
                    'type': attr_type,
                    'annotation': '@XmlAttribute(name="{}")'.format(attr_name)  # 为属性生成@XmlAttribute注解
                })
            inner_complex_types.append({
                'InnerClassName': inner_class_name,
                # 'annotation' : element_name,
                'InnerClassAttributes': attributes,
                'extendsClass': extendsClass,
                'innerInnerClass': innerInnerClass,
                'xmlType':element_name
            })

            for inner_type in inner_complex_types:
                inner_classes.append(inner_type)  # 将内部类信息单独存储
        return elements, inner_classes, wrapperElement  # 返回元素列表

    else:
        for element in choice.findall("./{http://www.w3.org/2001/XMLSchema}element"):
            element_name = element.get('name')  # 获取元素名称
            element_type = element.get('type')  # 获取元素类型-----》没有就是内部类
            if element_type:
                if maxOccurs == '1':
                    element_type = mapXsdTypeToJava(element_type.split(':')[-1], context='group')  # 将类型映射为Java类型
                    elements.append({
                        'name': to_camel_case(element_name),
                        'type': element_type,
                        'annotation': '@XmlElement(name="{}")'.format(element_name),
                        'maxOccurs': maxOccurs
                    })
                else:
                    element_type = mapXsdTypeToJava(element_type.split(':')[-1], context='group')  # 将类型映射为Java类型
                    elements.append({
                        'name': to_camel_case(element_name),
                        'type': 'ArrayList<{}>'.format(element_type),
                        'annotation': '@XmlElement(name="{}")'.format(element_name),
                        'maxOccurs': maxOccurs
                        # 'annotation': '@XmlElementWrapper(name="{}")\n@XmlElement(name="{}")'.format(fatherElementName, element_name)
                    })
            else:
                # 这里就是生成内部类对应的字段------》嵌套内部类也要考虑list
                if maxOccurs == '1':
                    elements.append({
                        'name': to_camel_case(element_name),
                        'type': to_pascal_case(element_name),
                        'annotation': '@XmlElement(name="{}")'.format(element_name),
                        'maxOccurs': maxOccurs
                    })
                else:
                    elements.append({
                        'name': to_camel_case(element_name),
                        'type': 'ArrayList<{}>'.format(to_pascal_case(element_name)),
                        'annotation': '@XmlElement(name="{}")'.format(element_name),
                        'maxOccurs': maxOccurs
                        # 'annotation': '@XmlElementWrapper(name="{}")\n@XmlElement(name="{}")'.format(fatherElementName, element_name)
                    })
                # 处理内部的 complexType 并生成内部类

                complex_type = element.find("./{http://www.w3.org/2001/XMLSchema}complexType")
                element_name = element.get('name')  # 获取元素名称----->父element
                inner_class_name = to_pascal_case(element_name)  # 将元素名称转换为PascalCase，用作内部类的名称
                inner_complex_types = []  # 初始化列表，用于存储内部复杂类型信息
                attributes = []  # 初始化列表，用于存储属性信息
                innerInnerClass = []
                extendsClass = None
                # 处理simpleContent
                simple_content = complex_type.find("./{http://www.w3.org/2001/XMLSchema}simpleContent")
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
                                # 'annotationName': baseTypeInfo['annotationName']
                            })
                for attr in extension.findall("./{http://www.w3.org/2001/XMLSchema}attribute"):
                    attr_name = attr.get('name')  # 获取属性名称
                    attr_type = mapXsdTypeToJava(attr.get('type').split(':')[-1],
                                                 context='attribute_group')  # 将属性类型映射为Java类型
                    attributes.append({
                        'name': to_camel_case(attr_name),
                        'type': attr_type,
                        'annotation': '@XmlAttribute(name="{}")'.format(attr_name)  # 为属性生成@XmlAttribute注解
                    })
                inner_complex_types.append({
                    'InnerClassName': inner_class_name,
                    # 'annotation' : element_name,
                    'InnerClassAttributes': attributes,
                    'extendsClass': extendsClass,
                    'innerInnerClass': innerInnerClass,
                    'xmlType': element_name
                })

                for inner_type in inner_complex_types:
                    inner_classes.append(inner_type)  # 将内部类信息单独存储
        return elements, inner_classes, wrapperElement # 返回元素列表



