from src.data_processing.uml_metadata_parser.XsdParser.ExtractExtensionBaseType import extractBaseType
from src.data_processing.uml_metadata_parser.XsdParser.Utils import to_pascal_case,to_camel_case


def process_complex_type(complexType, root, element_wrapper, groups, attributeGroups):
    name = complexType.get('name')  # 获取复杂类型的名称
    # --------------做成jaxb那样的----------------------
    mixed = complexType.get('mixed')  # 获取mixed属性
    if not name:
        return None  # 跳过没有名称的复杂类型-----内部类名定义在element
    attributes = []  # 初始化列表，用于存储复杂类型的属性
    extends = None
    inner_classes = []
    # 全局列表用于存储 Element 和 ComplexType 映射信息
    element_complex_type_mappings = []
    # **添加标记变量**，用于指示是否为primitive类型
    is_attribute = False

    # **处理 annotation 标签中的 appinfo 标签**
    annotation = complexType.find("./{http://www.w3.org/2001/XMLSchema}annotation")
    if annotation is not None:
        for appinfo in annotation.findall("./{http://www.w3.org/2001/XMLSchema}appinfo"):
            source = appinfo.get('source')
            if source == "stereotypes" and ("primitive" in appinfo.text or "enumeration" in appinfo.text):
                is_attribute = True  # 设置标记为 primitive 类型

    # 处理扩展simpleContent
    simpleContent = complexType.find("./{http://www.w3.org/2001/XMLSchema}simpleContent")
    if simpleContent is not None:
        base = simpleContent.find("./{http://www.w3.org/2001/XMLSchema}extension")
        if base is not None:
            baseTypeName = base.get('base').split(':')[-1]  # 提取基类名称
            baseTypeInfo = extractBaseType(root, baseTypeName)  # 获取基类信息
            if baseTypeInfo['extendsClass'] is not None:
                extends = baseTypeInfo['extendsClass']
            else:
                attributes.append({
                    'name': 'value',
                    'type': baseTypeInfo['type'],
                    'annotation': '@XmlValue',
                    'pattern': baseTypeInfo.get('pattern'),
                    'isPrimitiveType': baseTypeInfo.get('isPrimitiveType'),
                    'source':'complexType.simpleContent'
                })
        # 处理extension下的attributegroup
        for attributeGroupRef in base.findall("./{http://www.w3.org/2001/XMLSchema}attributeGroup"):
            refName = attributeGroupRef.get('ref').split(':')[-1]
            # attributeGroups = extractAttributeGroup(root)  # 获取引用的属性组
            if refName in attributeGroups:
                for attr in attributeGroups[refName]:
                    attributes.append({
                        'name': to_camel_case(attr['name']),
                        'type': attr['type'],
                        'annotation': '@XmlAttribute(name="{}")'.format(attr['name']),
                        'source':'attributeGroup:'+refName
                        # 属性组中的属性生成@XmlAttribute注解
                    })

    # 处理complex下第一级attributeGroup
    for attributeGroupRef in complexType.findall("./{http://www.w3.org/2001/XMLSchema}attributeGroup"):
        refName = attributeGroupRef.get('ref').split(':')[-1]
        # attributeGroups = extractAttributeGroup(root)  # 获取引用的属性组
        if refName in attributeGroups:
            for attr in attributeGroups[refName]:
                attributes.append({
                    'name': to_camel_case(attr['name']),
                    'type': attr['type'],
                    'annotation': '@XmlAttribute(name="{}")'.format(attr['name']),  # 属性组中的属性生成@XmlAttribute注解
                    'source': 'attributeGroup:' + refName
                })

    # 处理群组sequence下group
    sequence = complexType.find("./{http://www.w3.org/2001/XMLSchema}sequence")
    if sequence is not None:
        for groupRef in sequence.findall("./{http://www.w3.org/2001/XMLSchema}group"):
            refName = groupRef.get('ref').split(':')[-1]
            if refName in groups:
                for element in groups[refName]['elements']:
                    attributes.append({
                        'name': element['name'],
                        'type': element['type'],
                        'annotation': element['annotation'],
                        'maxOccurs': element['maxOccurs'],
                        'minOccurs': element.get('minOccurs'),
                        'source':'group:'+refName
                    })
                # 将群组中的内部类添加到 inner_classes 列表中
                inner_classes.extend([{**inner_class,'group':refName} for inner_class in groups[refName]['innerClasses']])

    # 处理choice下的group
    choice = complexType.find("./{http://www.w3.org/2001/XMLSchema}choice")
    if choice is not None:
        maxOccurs = choice.get('maxOccurs')
        for groupRef in choice.findall("./{http://www.w3.org/2001/XMLSchema}group"):
            refName = groupRef.get('ref').split(':')[-1]
            # groups = extractGroup(root, element_wrapper)  # 获取引用的群组
            if refName in groups:
                if maxOccurs == '1':
                    for element in groups[refName]['elements']:
                        attributes.append({
                            'name': element['name'],
                            'type': element['type'],
                            'annotation': element['annotation'],
                            'maxOccurs': maxOccurs,
                            'minOccurs': element.get('minOccurs'),
                            'source': 'group:' + refName
                        })
                    inner_classes.extend([{**inner_class,'group':refName} for inner_class in groups[refName]['innerClasses']])
                else:
                    for element in groups[refName]['elements']:
                        attributes.append({
                            'name': element['name'],
                            'type': element['type'] if element['type'].startswith('ArrayList') else 'ArrayList<{}>'.format(element['type']),
                            'annotation': element['annotation'],
                            'maxOccurs': maxOccurs,
                            'minOccurs': element.get('minOccurs'),
                            'source': 'group:' + refName
                        })
                    inner_classes.extend([{**inner_class,'group':refName} for inner_class in groups[refName]['innerClasses']])
        if mixed == 'true':
            element_refs = []
            source_groups=[]
            for attr in attributes:
                if '@XmlElement' in attr['annotation']:
                    element_name = attr['annotation'].split('name="')[1].split('"')[0]
                    #---------------------打印XmlElementRef(name="{}")内容和所属complexType，用于生成ObjectWrapper，后续改为收集起来传出去，也用模版生成---------------------
                    # 收集 Element 和 ComplexType 的映射信息
                    element_complex_type_mappings.append({
                        'element_name': element_name,
                        'element_type':'',
                        'complex_type': to_pascal_case(name),  # ComplexType 的名称
                        'element_name_pascal':to_pascal_case(element_name)
                    })

                    source_groups.append(attr['source'].replace('group:',''))

                    element_refs.append(
                        '@XmlElementRef(name="{}", namespace="http://autosar.org/schema/r4.0", type=JAXBElement.class, required=false)'.format(
                            element_name))
            attributes = [attr for attr in attributes if '@XmlElement' not in attr['annotation']]
            if element_refs:
                attributes.append({
                    'name': 'content',
                    'type': 'ArrayList<Serializable>',
                    'annotation': '@XmlElementRefs({\n        ' + ',\n        '.join(element_refs) + '\n    })\n    @XmlMixed',
                    'maxOccurs': 'unbounded',
                    'mixed_groups':source_groups
                })

    return {
        'name': name,
        'attributes': attributes,
        'innerClasses': inner_classes,  # 存储所有内部类信息
        'extends': extends,
        'objFactory': element_complex_type_mappings,  # Element 和 ComplexType 映射信息
        'isAttribute': is_attribute
    }
#---------------多线程，可能由于异步导致提取内部类名不同----------------------
# def extractComplexType(root, element_wrapper, groups, attributeGroups):
#     complexTypes = []  # 初始化一个列表，用于存储复杂类型的信息
#     element_complex_type_mappings=[]
#     # 使用 ThreadPoolExecutor 并行处理 complexType
#     with ThreadPoolExecutor(max_workers=8) as executor:
#         futures = [executor.submit(process_complex_type, complexType, root, element_wrapper, groups, attributeGroups)
#                    for complexType in root.findall(".//{http://www.w3.org/2001/XMLSchema}complexType")]
#
#         for future in as_completed(futures):
#             result = future.result()
#             if result:  # 仅当返回结果非空时添加
#                 complexTypes.append(result)
#                 element_complex_type_mappings.extend(result['objFactory'])
#
#     return complexTypes, element_complex_type_mappings  # 返回解析后的复杂类型列表

#--------------单线程遍历，每次生成相同------------------------
def extractComplexType(root, element_wrapper, groups, attributeGroups):
    complexTypes = []  # 初始化一个列表，用于存储复杂类型的信息
    element_complex_type_mappings = []  # 初始化一个列表，用于存储 Element 和 ComplexType 的映射信息

    # 遍历所有 complexType 节点
    for complexType in root.findall(".//{http://www.w3.org/2001/XMLSchema}complexType"):
        result = process_complex_type(complexType, root, element_wrapper, groups, attributeGroups)

        if result:  # 仅当返回结果非空时添加
            complexTypes.append(result)
            element_complex_type_mappings.extend(result['objFactory'])  # 收集 Element 和 ComplexType 的映射信息

    return complexTypes, element_complex_type_mappings  # 返回解析后的复杂类型和映射信息列表
