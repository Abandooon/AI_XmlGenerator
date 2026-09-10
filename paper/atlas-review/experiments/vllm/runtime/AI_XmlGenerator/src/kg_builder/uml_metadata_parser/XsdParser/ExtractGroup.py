import xml.etree.ElementTree as ET

from src.kg_builder.uml_metadata_parser.XsdParser.ExtractChoiceGroup import process_choiceRef
from src.kg_builder.uml_metadata_parser.XsdParser.GroupInnerComplexType import process_group_inner_complex_type
from src.kg_builder.uml_metadata_parser.XsdParser.TypeMapping import mapXsdTypeToJava
from src.kg_builder.uml_metadata_parser.XsdParser.Utils import to_camel_case, to_pascal_case


def extractGroup(root, element_wrapper):
    groups = {}

    # 查找所有群组元素
    for group in root.findall("./{http://www.w3.org/2001/XMLSchema}group"):
        group_name = group.get('name')
        # 根据group_name查找同名的complexType
        matching_complex_type = None
        for ct in root.findall(".//{http://www.w3.org/2001/XMLSchema}complexType"):
            if ct.get('name') == group_name:
                matching_complex_type = ct
                break
        # 如果找到了对应的complexType则提取其下所有的attributegroup
        attribute_groups = []
        if matching_complex_type is not None:
            for attributeGroupRef in matching_complex_type.findall(".//{http://www.w3.org/2001/XMLSchema}attributeGroup"):
                refName = to_pascal_case(attributeGroupRef.get('ref').split(':')[-1])
                attribute_groups.append(refName)

        result = extract_annotation(group)
        description = result['description']
        stereotypes = result['stereotypes']
        pure_maxOccurs = result['pureMM_maxOccurs']
        pure_minOccurs = result['pureMM_minOccurs']
        qualifiedName = result['qualifiedName']
        qualifiedNameParts = result['qualifiedNameParts']
        latestBindingTime = result['latestBindingTime']
        splitkey = result['splitkey']  # 获取分割键

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

        # 读取input文件夹中的XsdIndex.arxml文件，匹配该文件group name和group_name,相同则提取其中的complexTypes并存到child中# 读取input文件夹中的XsdIndex.arxml文件，匹配该文件group name和group_name,相同则提取其中的complexTypes并存到child中
        xsd_index_path = "input/XsdIndex.arxml"
        tree = ET.parse(xsd_index_path)
        root_index = tree.getroot()
        for group in root_index.findall("./group"):
            if group.get("name") == group_name:
                complex_types = ",".join([to_pascal_case(ct.strip()) for ct in group.get("complexTypes").replace("//", ",").lstrip(",").split(",")])
                child = complex_types
                subTags = [to_pascal_case(ct.strip()) for ct in
                                 group.get("complexTypes").replace("//", ",").lstrip(",").split(",")]
                break

        groups[group_name] = {
            'name': to_pascal_case(group_name),
            'qualifiedName': qualifiedName,
            'annotation': group_name,
            'description': description,
            'stereotypes': stereotypes,
            'pure_minOccurs': pure_minOccurs,
            'pure_maxOccurs': pure_maxOccurs,
            'child':child,
            'subTags': subTags,
            'elements': accumulated_elements,
            'innerClasses': accumulated_inner_classes,
            'attributeGroups': attribute_groups,
            'latestBindingTime': latestBindingTime,
            'splitkey': splitkey  # 添加分割键
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

        result = extract_annotation(element)
        description = result['description']
        stereotypes = result['stereotypes']
        pure_maxOccurs = result['pureMM_maxOccurs']
        pure_minOccurs = result['pureMM_minOccurs']
        qualifiedName = result['qualifiedName']
        qualifiedNameParts = result['qualifiedNameParts']
        latestBindingTime = result['latestBindingTime']
        splitkey = result['splitkey']  # 获取最新绑定时间

        wrapperElement = False
        if element_type:
            if maxOccurs == '1':
                element_type = mapXsdTypeToJava(element_type.split(':')[-1], context='group')  # 将类型映射为Java类型
                elements.append({
                    'name': to_camel_case(element_name),
                    'qualifiedName' : qualifiedNameParts,
                    'document_name': qualifiedName,
                    'type': element_type,
                    'annotation': '@XmlElement(name="{}")'.format(element_name),
                    'xml_tag': element_name,
                    'xml_wrapper_tag': None,
                    'is_xml_attribute': False,
                    'minOccurs': minOccurs,
                    'maxOccurs': maxOccurs,
                    'description': description,
                    'stereotypes': stereotypes,
                    'pure_minOccurs': pure_minOccurs,
                    'pure_maxOccurs': pure_maxOccurs,
                    'latestBindingTime': latestBindingTime,
                    'splitkey': splitkey
                })
            else:
                element_type = mapXsdTypeToJava(element_type.split(':')[-1], context='group')  # 将类型映射为Java类型
                elements.append({
                    'name': to_camel_case(element_name),
                    'qualifiedName': qualifiedNameParts,
                    'document_name': qualifiedName,
                    'type': element_type,
                    'annotation': '@XmlElement(name="{}")'.format(element_name),
                    'xml_tag': element_name,
                    'xml_wrapper_tag': None,
                    'is_xml_attribute': False,
                    'minOccurs': minOccurs,
                    'maxOccurs': maxOccurs,
                    'description': description,
                    'stereotypes': stereotypes,
                    'pure_minOccurs': pure_minOccurs,
                    'pure_maxOccurs': pure_maxOccurs,
                    'latestBindingTime': latestBindingTime,
                    'splitkey': splitkey
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
                    if description == "" and qualifiedName == "" and pure_maxOccurs == 0:
                        ns = "{http://www.w3.org/2001/XMLSchema}"
                        path = f".//{ns}complexType/{ns}choice/{ns}element"
                        found_element = element.find(path)
                        if found_element is not None:
                            result = extract_annotation(found_element)
                            description = result['description']
                            stereotypes = result['stereotypes']
                            pure_maxOccurs = result['pureMM_maxOccurs']
                            pure_minOccurs = result['pureMM_minOccurs']
                            qualifiedName = result['qualifiedName']
                            qualifiedNameParts = result['qualifiedNameParts']
                            latestBindingTime = result['latestBindingTime']
                            splitkey = result['splitkey']  # 获取最新绑定时间
                    for inner_type in inner_complex_types:
                        for attr in inner_type.get('InnerClassAttributes'):
                            elements.append({
                                'name': to_camel_case(element_name),
                                'qualifiedName': qualifiedNameParts,
                                'document_name': qualifiedName,
                                'type': attr.get('type'),
                                'annotation': attr.get('annotation'),
                                'xml_tag': attr.get('xml_tag'),
                                'xml_wrapper_tag': attr.get('xml_wrapper_tag'),
                                'is_xml_attribute': attr.get('is_xml_attribute'),
                                'minOccurs': minOccurs,
                                'maxOccurs': attr.get('maxOccurs'),
                                'description': description,
                                'stereotypes': stereotypes,
                                'pure_minOccurs': pure_minOccurs,
                                'pure_maxOccurs': pure_maxOccurs,
                                'latestBindingTime': latestBindingTime,
                                'splitkey': splitkey
                            })
                        #---将嵌套内部类提取出来放到外层
                        for innerInnerClass in inner_type.get('innerInnerClass'):
                            inner_classes.append(innerInnerClass)
                    # print(inner_complex_types)
                else:
                    elements.append({
                        'name': to_camel_case(element_name),
                        'qualifiedName': qualifiedNameParts,
                        'document_name': qualifiedName,
                        'type': to_pascal_case(element_name),
                        'annotation': '@XmlElement(name="{}")'.format(element_name),
                        'xml_tag': element_name,
                        'xml_wrapper_tag': None,
                        'is_xml_attribute': False,
                        'minOccurs': minOccurs,
                        'maxOccurs': maxOccurs,
                        'description': description,
                        'stereotypes': stereotypes,
                        'pure_minOccurs': pure_minOccurs,
                        'pure_maxOccurs': pure_maxOccurs,
                        'latestBindingTime': latestBindingTime,
                        'splitkey': splitkey
                    })
                    # 处理内部的complexType并生成内部类
                    for inner_type in inner_complex_types:
                        inner_classes.append(inner_type)  # 将内部类信息单独存储
            else:
                elements.append({
                    'name': to_camel_case(element_name),
                    'qualifiedName': qualifiedNameParts,
                    'document_name': qualifiedName,
                    'type': to_pascal_case(element_name),
                    'annotation': '@XmlElement(name="{}")'.format(element_name),
                    'xml_tag': element_name,
                    'xml_wrapper_tag': None,
                    'is_xml_attribute': False,
                    'minOccurs': minOccurs,
                    'maxOccurs': maxOccurs,
                    'description': description,
                    'stereotypes': stereotypes,
                    'pure_minOccurs': pure_minOccurs,
                    'pure_maxOccurs': pure_maxOccurs,
                    'latestBindingTime': latestBindingTime,
                    'splitkey': splitkey
                })
                # 处理内部的complexType并生成内部类
                for inner_type in inner_complex_types:
                    inner_classes.append(inner_type)  # 将内部类信息单独存储

    return elements, inner_classes  # 返回元素列表

def extract_annotation(group_element):
    import re
    description = ""
    pure_maxOccurs = 0
    pure_minOccurs = 0
    qualifiedName = ""
    stereotypes = []
    latestBindingTime = ""
    splitkey = ""
    annotation = group_element.find("./{http://www.w3.org/2001/XMLSchema}annotation")
    if annotation is not None:
        documentation = annotation.find("./{http://www.w3.org/2001/XMLSchema}documentation")
        if documentation is not None and documentation.text:
            description += documentation.text.strip() + " "
        appinfos = annotation.findall("./{http://www.w3.org/2001/XMLSchema}appinfo")
        for appinfo in appinfos:
            source = appinfo.get("source")
            if source == "tags" and appinfo.text:
                tag_text = appinfo.text.strip()
                max_match = re.search(r'pureMM\.maxOccurs\s*=\s*"(-?\d+)"', tag_text)
                if max_match:
                    pure_maxOccurs = int(max_match.group(1))
                min_match = re.search(r'pureMM\.minOccurs\s*=\s*"(\d+)"', tag_text)
                if min_match:
                    pure_minOccurs = int(min_match.group(1))
                qn_match = re.search(r'mmt\.qualifiedName\s*=\s*"([^"]+)"', tag_text)
                if qn_match:
                    qn = qn_match.group(1)
                    qualifiedName = qn
                vh_binding_time_match = re.search(r'vh\.latestBindingTime\s*=\s*"([^"]+)"', tag_text)
                if vh_binding_time_match:
                    latestBindingTime = vh_binding_time_match.group(1)
                else:
                    latestBindingTime = ""
                atp_splitkey_match = re.search(r'atp\.Splitkey\s*=\s*"([^"]+)"', tag_text)
                if atp_splitkey_match:
                    splitkey = atp_splitkey_match.group(1)
                else:
                    splitkey = ""
            elif source == "stereotypes" and appinfo.text:
                stereotypes = appinfo.text.strip().split(',')  # 按逗号分割为列表
    description = description.strip()
    return {
        "description": description,
        "stereotypes" : stereotypes,
        "pureMM_maxOccurs": pure_maxOccurs,
        "pureMM_minOccurs": pure_minOccurs,
        "qualifiedName": qualifiedName,
        "qualifiedNameParts": qualifiedName.split('.', 1)[1] if '.' in qualifiedName else "",
        "latestBindingTime" : latestBindingTime,
        "splitkey": splitkey
    }