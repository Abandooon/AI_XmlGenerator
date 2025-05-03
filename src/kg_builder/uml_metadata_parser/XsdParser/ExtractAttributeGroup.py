from src.kg_builder.uml_metadata_parser.XsdParser.ExtractGroup import extract_annotation
from src.kg_builder.uml_metadata_parser.XsdParser.TypeMapping import mapXsdTypeToJava
from src.kg_builder.uml_metadata_parser.XsdParser.Utils import to_pascal_case, to_camel_case


# 获取所有的attributeGroup和每个attributeGroup中的attribute（name和type），返回出去再遍历匹配引用的
def extractAttributeGroup(root):
    attributeGroups = {}  # 初始化一个字典，用于存储根节点下所有的attributeGroup

    # 查找所有的attributeGroup元素
    for attributeGroup in root.findall(".//{http://www.w3.org/2001/XMLSchema}attributeGroup"):
        name = to_pascal_case(attributeGroup.get('name')) # 获取attributeGroup的名称
        attributes = []

        # 查找attributeGroup中的所有attribute元素
        for attribute in attributeGroup.findall(".//{http://www.w3.org/2001/XMLSchema}attribute"):
            result = extract_annotation(attribute)
            description = result['description']
            stereotypes = result['stereotypes']
            pure_maxOccurs = result['pureMM_maxOccurs']
            pure_minOccurs = result['pureMM_minOccurs']
            qualifiedName = result['qualifiedName']
            qualifiedNameParts = result['qualifiedNameParts']

            attrName = attribute.get('name')  # 获取属性的名称
            attrType = attribute.get('type')  # 获取属性的类型
            if attrType:
                attrType = attrType.split(':')[-1]  # 如果属性类型存在，去除命名空间，保留实际类型名
            attributes.append({
                'name': to_camel_case(attrName),
                'qualifiedName': qualifiedNameParts,
                'document_name': qualifiedName,
                'type': mapXsdTypeToJava(attrType, context='attribute_group'),
                'annotation': attrName,
                'description': description,
                'stereotypes': stereotypes,
                'pure_minOccurs': pure_minOccurs,
                'pure_maxOccurs': pure_maxOccurs,
            })

        attributeGroups[name] = attributes  # 将属性组的名称和属性列表存储到字典中

    return attributeGroups  # 返回包含所有属性组的字典
