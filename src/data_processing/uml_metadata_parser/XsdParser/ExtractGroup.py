from src.data_processing.uml_metadata_parser.XsdParser.TypeMapping import mapXsdTypeToJava
from src.data_processing.uml_metadata_parser.XsdParser.GroupInnerComplexType import process_group_inner_complex_type
from src.data_processing.uml_metadata_parser.XsdParser.ExtractChoiceGroup import process_choiceRef
from src.data_processing.uml_metadata_parser.XsdParser.Utils import to_camel_case,to_pascal_case


def extractGroup(root, element_wrapper):
    groups = {}

    # 查找所有群组元素
    for group in root.findall("./{http://www.w3.org/2001/XMLSchema}group"):
        group_name = group.get('name')
        accumulated_elements = []
        accumulated_inner_classes = []

        for child in group:
            if child.tag.endswith('sequence'):
                sequence = child
                element = sequence.findall("./{http://www.w3.org/2001/XMLSchema}element")
                if element is not None:
                    elements, inner_classes = process_elements(root, sequence, element_wrapper)
                    accumulated_elements.extend(elements)
                    accumulated_inner_classes.extend(inner_classes)

                choices = sequence.findall("./{http://www.w3.org/2001/XMLSchema}choice")
                if choices is not None:
                    for choice in choices:
                        innerMaxOccurs = choice.get('maxOccurs')
                        innerMinOccurs = choice.get('minOccurs')
                        # 仅返回了第一个group ref元素
                        # group = choice.find("./{http://www.w3.org/2001/XMLSchema}group")
                        # if group is not None:
                        #     refName = group.get('ref').split(':')[-1]
                        #     elements, inner_classes = process_choiceRef(root, refName, innerMaxOccurs, element_wrapper)
                        #     accumulated_elements.extend(elements)
                        #     accumulated_inner_classes.extend(inner_classes)
                        groups_in_choice = choice.findall("./{http://www.w3.org/2001/XMLSchema}group")
                        if groups_in_choice is not None:
                            for group_in_choice in groups_in_choice:
                                refName = group_in_choice.get('ref').split(':')[-1]
                                elements, inner_classes = process_choiceRef(root, refName, innerMaxOccurs, element_wrapper)
                                accumulated_elements.extend(elements)
                                accumulated_inner_classes.extend(inner_classes)


            #1.直接提取element出来；2.找到引用的group提取element放到这里
            elif child.tag.endswith('choice'):
                choice = child
                innerChoice = choice.find("./{http://www.w3.org/2001/XMLSchema}choice")
                element = innerChoice.findall("./{http://www.w3.org/2001/XMLSchema}element")
                #element仅用于判断有没有，process_elements传的是上级innerChoice，遍历所有element返回出来
                if element is not None:
                    elements, inner_classes = process_elements(root, innerChoice,element_wrapper)
                    accumulated_elements.extend(elements)
                    accumulated_inner_classes.extend(inner_classes)

                innerInnerChoices = innerChoice.findall("./{http://www.w3.org/2001/XMLSchema}choice")
                if innerInnerChoices is not None:
                    for innerInnerChoice in innerInnerChoices:
                        innerMaxOccurs = innerInnerChoice.get('maxOccurs')
                        groups_in_choice = innerInnerChoice.findall("./{http://www.w3.org/2001/XMLSchema}group")
                        if groups_in_choice is not None:
                            for group_in_choice in groups_in_choice:
                                refName = group_in_choice.get('ref').split(':')[-1]
                                # 传入引用的group名，返回该group中的elements
                                elements, inner_classes = process_choiceRef(root, refName, innerMaxOccurs,
                                                                            element_wrapper)
                                accumulated_elements.extend(elements)
                                accumulated_inner_classes.extend(inner_classes)

        groups[group_name] = {
            'name': to_pascal_case(group_name),
            'annotation': group_name,
            'type': 'abstract',
            'association': '',
            'generalization': '',
            'description': '',
            'ocl': '',
            'child':'',
            'label':'',
            'elements': accumulated_elements,
            'innerClasses': accumulated_inner_classes
        }

    return groups

#处理group里面的element
#如果开启了wrapper，应该从内部类中提取出内部类的element放到这里，相当于直接type=
def process_elements(root, sequenceOrChoice, element_wrapper):
    elements = []
    inner_classes = []
    for element in sequenceOrChoice.findall("./{http://www.w3.org/2001/XMLSchema}element"):
        # --------element可能没有maxOccurs，这时候就要看外面的choice-------
        maxOccurs = element.get('maxOccurs') or '1'
        minOccurs = element.get('minOccurs') or '0'
        element_name = element.get('name')
        element_type = element.get('type')  # 获取元素类型-----没有就是内部类，走到else里面
        wrapperElement = False
        if element_type:
            if maxOccurs == '1':
                element_type = mapXsdTypeToJava(element_type.split(':')[-1], context='group')  # 将类型映射为Java类型
                elements.append({
                    'name': to_camel_case(element_name),
                    'type': element_type,
                    'annotation': '@XmlElement(name="{}")'.format(element_name),
                    'minOccurs': minOccurs,
                    'maxOccurs': maxOccurs
                })
            else:
                element_type = mapXsdTypeToJava(element_type.split(':')[-1], context='group')  # 将类型映射为Java类型
                elements.append({
                    'name': to_camel_case(element_name),
                    'type': 'ArrayList<{}>'.format(element_type),
                    'annotation': '@XmlElement(name="{}")'.format(element_name),
                    'minOccurs': minOccurs,
                    'maxOccurs': maxOccurs
                })
        else:
            # 这里就是生成内部类对应的字段------嵌套内部类也要考虑list
            # 由于这里是choice下引用的group中的element，所以不需要wrapper
            inner_complex_types, wrapperElement = process_group_inner_complex_type(root, element,
                                                                                   element_wrapper)  # 处理群组中的复杂类型，生成内部类
            #这里是内部类上层的element，为1才生成wrapper，不然他本身就是list
            if maxOccurs == '1':
                #-------如果wrapperElement为True，说明生成了wrapper，将内部类属性放到上层element中，将嵌套内部类提到上层内部类,属性变量名用上层element的-----
                if wrapperElement:
                    for inner_type in inner_complex_types:
                        for attr in inner_type.get('InnerClassAttributes'):
                            elements.append({
                                'name': to_camel_case(element_name),
                                'type': attr.get('type'),
                                'annotation': attr.get('annotation'),
                                'minOccurs': minOccurs,
                                'maxOccurs': attr.get('maxOccurs')
                            })
                        #---将嵌套内部类提取出来放到外层
                        for innerInnerClass in inner_type.get('innerInnerClass'):
                            inner_classes.append(innerInnerClass)
                    # print(inner_complex_types)
                else:
                    elements.append({
                        'name': to_camel_case(element_name),
                        'type': to_pascal_case(element_name),
                        'annotation': '@XmlElement(name="{}")'.format(element_name),
                        'minOccurs': minOccurs,
                        'maxOccurs': maxOccurs
                    })
                    # 处理内部的complexType并生成内部类
                    for inner_type in inner_complex_types:
                        inner_classes.append(inner_type)  # 将内部类信息单独存储
            else:
                elements.append({
                    'name': to_camel_case(element_name) + 's',
                    'type': 'ArrayList<{}>'.format(to_pascal_case(element_name)),
                    'annotation': '@XmlElement(name="{}")'.format(element_name),
                    'minOccurs': minOccurs,
                    'maxOccurs': maxOccurs
                })
                # 处理内部的complexType并生成内部类
                for inner_type in inner_complex_types:
                    inner_classes.append(inner_type)  # 将内部类信息单独存储

    return elements, inner_classes  # 返回元素列表

