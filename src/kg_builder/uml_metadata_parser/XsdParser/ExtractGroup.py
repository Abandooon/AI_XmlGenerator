from src.data_processing.uml_metadata_parser.XsdParser.TypeMapping import mapXsdTypeToJava
from src.data_processing.uml_metadata_parser.XsdParser.GroupInnerComplexType import process_group_inner_complex_type
from src.data_processing.uml_metadata_parser.XsdParser.ExtractChoiceGroup import process_choiceRef
from src.data_processing.uml_metadata_parser.XsdParser.Utils import to_camel_case,to_pascal_case
import xml.etree.ElementTree as ET

def extractGroup(root, element_wrapper):
    groups = {}

    # ��������Ⱥ��Ԫ��
    for group in root.findall("./{http://www.w3.org/2001/XMLSchema}group"):
        group_name = group.get('name')

        description = extract_annotation(group)

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
                        # �������˵�һ��group refԪ��
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


            #1.ֱ����ȡelement������2.�ҵ����õ�group��ȡelement�ŵ�����
            elif child.tag.endswith('choice'):
                choice = child
                innerChoice = choice.find("./{http://www.w3.org/2001/XMLSchema}choice")
                element = innerChoice.findall("./{http://www.w3.org/2001/XMLSchema}element")
                #element�������ж���û�У�process_elements�������ϼ�innerChoice����������element���س���
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
                                # �������õ�group�������ظ�group�е�elements
                                elements, inner_classes = process_choiceRef(root, refName, innerMaxOccurs,
                                                                            element_wrapper)
                                accumulated_elements.extend(elements)
                                accumulated_inner_classes.extend(inner_classes)

        # ��ȡinput�ļ����е�XsdIndex.arxml�ļ���ƥ����ļ�group name��group_name,��ͬ����ȡ���е�complexTypes���浽child��# ��ȡinput�ļ����е�XsdIndex.arxml�ļ���ƥ����ļ�group name��group_name,��ͬ����ȡ���е�complexTypes���浽child��
        xsd_index_path = "input/XsdIndex.arxml"
        tree = ET.parse(xsd_index_path)
        root_index = tree.getroot()
        for group in root_index.findall("./group"):
            if group.get("name") == group_name:
                complex_types = ",".join([to_pascal_case(ct.strip()) for ct in group.get("complexTypes").replace("//", ",").lstrip(",").split(",")])
                child = complex_types
                break

        groups[group_name] = {
            'name': to_pascal_case(group_name),
            'annotation': group_name,
            'type': 'abstract',
            'association': '',
            'generalization': '',
            'description': description,
            'ocl': '',
            'child':child,
            'label':'',
            'elements': accumulated_elements,
            'innerClasses': accumulated_inner_classes,
            'DynamicMethods': [],
        }

    return groups

#����group�����element
#���������wrapper��Ӧ�ô��ڲ�������ȡ���ڲ����element�ŵ�����൱��ֱ��type=
def process_elements(root, sequenceOrChoice, element_wrapper):
    elements = []
    inner_classes = []
    for element in sequenceOrChoice.findall("./{http://www.w3.org/2001/XMLSchema}element"):
        # --------element����û��maxOccurs����ʱ���Ҫ�������choice-------
        maxOccurs = element.get('maxOccurs') or '1'
        minOccurs = element.get('minOccurs') or '0'
        element_name = element.get('name')
        element_type = element.get('type')  # ��ȡԪ������-----û�о����ڲ��࣬�ߵ�else����

        description = extract_annotation(element)

        wrapperElement = False
        if element_type:
            if maxOccurs == '1':
                element_type = mapXsdTypeToJava(element_type.split(':')[-1], context='group')  # ������ӳ��ΪJava����
                elements.append({
                    'name': to_camel_case(element_name),
                    'type': element_type,
                    'annotation': '@XmlElement(name="{}")'.format(element_name),
                    'minOccurs': minOccurs,
                    'maxOccurs': maxOccurs,
                    'description': description,
                    'ocl':"minOccurs: {}, maxOccurs: {}".format(minOccurs, maxOccurs)
                })
            else:
                element_type = mapXsdTypeToJava(element_type.split(':')[-1], context='group')  # ������ӳ��ΪJava����
                elements.append({
                    'name': to_camel_case(element_name),
                    'type': 'ArrayList<{}>'.format(element_type),
                    'annotation': '@XmlElement(name="{}")'.format(element_name),
                    'minOccurs': minOccurs,
                    'maxOccurs': maxOccurs,
                    'description': description,
                    'ocl': "minOccurs: {}, maxOccurs: {}".format(minOccurs, maxOccurs)
                })
        else:
            # ������������ڲ����Ӧ���ֶ�------Ƕ���ڲ���ҲҪ����list
            # ����������choice�����õ�group�е�element�����Բ���Ҫwrapper
            inner_complex_types, wrapperElement = process_group_inner_complex_type(root, element,
                                                                                   element_wrapper)  # ����Ⱥ���еĸ������ͣ������ڲ���
            #�������ڲ����ϲ��element��Ϊ1������wrapper����Ȼ���������list
            if maxOccurs == '1':
                #-------���wrapperElementΪTrue��˵��������wrapper�����ڲ������Էŵ��ϲ�element�У���Ƕ���ڲ����ᵽ�ϲ��ڲ���,���Ա��������ϲ�element��-----
                if wrapperElement:
                    for inner_type in inner_complex_types:
                        for attr in inner_type.get('InnerClassAttributes'):
                            elements.append({
                                'name': to_camel_case(element_name),
                                'type': attr.get('type'),
                                'annotation': attr.get('annotation'),
                                'minOccurs': minOccurs,
                                'maxOccurs': attr.get('maxOccurs'),
                                'description': description,
                                'ocl': "minOccurs: {}, maxOccurs: {}".format(minOccurs, maxOccurs)
                            })
                        #---��Ƕ���ڲ�����ȡ�����ŵ����
                        for innerInnerClass in inner_type.get('innerInnerClass'):
                            inner_classes.append(innerInnerClass)
                    # print(inner_complex_types)
                else:
                    elements.append({
                        'name': to_camel_case(element_name),
                        'type': to_pascal_case(element_name),
                        'annotation': '@XmlElement(name="{}")'.format(element_name),
                        'minOccurs': minOccurs,
                        'maxOccurs': maxOccurs,
                        'description': description,
                        'ocl': "minOccurs: {}, maxOccurs: {}".format(minOccurs, maxOccurs)
                    })
                    # �����ڲ���complexType�������ڲ���
                    for inner_type in inner_complex_types:
                        inner_classes.append(inner_type)  # ���ڲ�����Ϣ�����洢
            else:
                elements.append({
                    'name': to_camel_case(element_name) + 's',
                    'type': 'ArrayList<{}>'.format(to_pascal_case(element_name)),
                    'annotation': '@XmlElement(name="{}")'.format(element_name),
                    'minOccurs': minOccurs,
                    'maxOccurs': maxOccurs,
                    'description': description,
                    'ocl': "minOccurs: {}, maxOccurs: {}".format(minOccurs, maxOccurs)
                })
                # �����ڲ���complexType�������ڲ���
                for inner_type in inner_complex_types:
                    inner_classes.append(inner_type)  # ���ڲ�����Ϣ�����洢

    return elements, inner_classes  # ����Ԫ���б�

def extract_annotation(group_element):
    # ��ȡgroup��ǩ�е�xsd:annotation�е�xsd:documentation��xsd:appinfo source="tags"��xsd:appinfo source="stereotypes"�����ݣ����浽description��
    description = ""
    annotation = group_element.find("./{http://www.w3.org/2001/XMLSchema}annotation")
    if annotation is not None:
        documentation = annotation.find("./{http://www.w3.org/2001/XMLSchema}documentation")
        if documentation is not None and documentation.text:
            description += "note:" + documentation.text.strip() + " "

        appinfos = annotation.findall("./{http://www.w3.org/2001/XMLSchema}appinfo")
        for appinfo in appinfos:
            source = appinfo.get("source")
            if source == "tags" and appinfo.text:
                description += "tag:" + appinfo.text.strip() + " "
            elif source == "stereotypes" and appinfo.text:
                description += "stereotype:" + appinfo.text.strip() + " "
    description = description.strip()
    return description