def extractSimpleType(root):
    simpleTypes = []  # 初始化一个列表，用于存储简单类型的信息


    # 查找所有的简单类型元素
    for simpleType in root.findall(".//{http://www.w3.org/2001/XMLSchema}simpleType"):
        isPrimitiveType = False  # 是否为基本类型
        pattern = None  # 正则表达式
        name = simpleType.get('name')  # 获取简单类型的名称
        restriction = simpleType.find(".//{http://www.w3.org/2001/XMLSchema}restriction")  # 获取限制基类型
        baseType = restriction.get('base').split(':')[
            -1] if restriction is not None else 'String'  # 获取限制的基本类型，默认为string

        # 获取restriction标签下的enumeration
        enumerations = []
        if restriction is not None:
            for enum in restriction.findall(".//{http://www.w3.org/2001/XMLSchema}enumeration"):
                enum_value = enum.get('value')  # 获取枚举值
                if enum_value:
                    enumerations.append(enum_value)

            pattern = restriction.find(".//{http://www.w3.org/2001/XMLSchema}pattern")
            if pattern is not None:
                isPrimitiveType = True


        # 判断枚举值数量，如果为0，则不添加到列表中
        # if len(enumerations) == 1:
        #     isOneEnumeration = True

        # 将简单类型的信息存储到字典中，并添加到列表中
        simpleTypes.append({
            'name': name,
            'base': baseType,
            'enumerations': enumerations,  # 添加枚举值列表
            'isPrimitiveType': isPrimitiveType,
            'pattern': pattern
        })

    return simpleTypes  # 返回解析后的简单类型列表
