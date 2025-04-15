from src.data_processing.uml_metadata_parser.XsdParser.ExtractSimpleType import extractSimpleType
from src.data_processing.uml_metadata_parser.XsdParser.TypeMapping import mapXsdTypeToJava
from src.data_processing.uml_metadata_parser.XsdParser.TypeMapping import mapXsdTypeToJava
from src.data_processing.uml_metadata_parser.XsdParser.Utils import to_pascal_case


# 只处理扩展本身，不处理下面的标签
def extractBaseType(root, baseName):
    baseTypeInfo = {
        'type': None,  # 初始化字典，存储基类型信息
        'extendsClass': None,
        'annotation': None
    }

    # 提取XSD中的简单类型
    simpleTypes = extractSimpleType(root)
    for simpleType in simpleTypes:
        if baseName == simpleType['name']:  # 匹配基类型名称
            if simpleType['enumerations']:  # 检查是否存在枚举值
                baseTypeInfo['type'] = to_pascal_case(simpleType['name'])  # 如果有枚举值，使用simpleType的name作为Java类名
                baseTypeInfo['annotation'] = '@XmlElement(name="{}")'.format(baseName)
            elif simpleType['isPrimitiveType']:  # 检查是否为基本类型
                baseTypeInfo['type'] = mapXsdTypeToJava(simpleType['base'], context='base_type')  # 否则使用类型映射
                baseTypeInfo['annotation'] = '@XmlValue'
                baseTypeInfo['pattern'] = simpleType['pattern'].get('value')
                baseTypeInfo['isPrimitiveType'] = simpleType['isPrimitiveType']
            else:
                baseTypeInfo['type'] = mapXsdTypeToJava(simpleType['base'], context='base_type')  # 否则使用类型映射
                baseTypeInfo['annotation'] = '@XmlValue'
            return baseTypeInfo  # 返回基类型信息
        else:
            # 查找所有复杂类型，并匹配基类型名称----------->不是简单类型就是复杂类型----》ref----》后面可以改xsd来添加其他的
            for complexType in root.findall(".//{http://www.w3.org/2001/XMLSchema}complexType"):
                if complexType.get('name') == baseName:
                    baseTypeInfo['extendsClass'] = to_pascal_case(baseName)
                    return baseTypeInfo  # 返回基类型信息


    return baseTypeInfo  # 返回基类型信息


