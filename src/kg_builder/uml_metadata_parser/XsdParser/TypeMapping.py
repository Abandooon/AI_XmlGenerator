# -*- coding: utf-8 -*-
import re
#--------------------适用于autosar4.2.2------------------------
def mapXsdTypeToJava(xsdType, context='default'):
    xsdToJavaTypeMap = {
        'base_type': {
            # 'CSE-CODE-TYPE-STRING--SIMPLE': 'java.lang.Integer',
            # 'FLOAT--SIMPLE': 'java.lang.Double',
            # 'TIME-VALUE--SIMPLE': 'java.lang.Double',
            # 这里传的就是base="*",小写的，如果是enum应该是引到这个枚举类------->逻辑错误，应该是找到继承的这个simpleType，看里面有没有enumeration标签，有的话就是个类
            'string': 'java.lang.String',
            'unsignedInt': 'java.lang.Integer',
            'double': 'java.lang.Double',
            'NMTOKEN': 'java.lang.String',
            'NMTOKENS': 'java.lang.String',
        },
        'attribute_group': {
            # 只有不含enum的Simple没解析为类，所以要映射为基本类型，别的都解析为类了，默认驼峰类名即可引到
            'string': 'java.lang.String',
            "STRING--SIMPLE": "java.lang.String",
            "DATE--SIMPLE": "java.lang.String",
            "TABLE-SEPARATOR-STRING--SIMPLE": "java.lang.String",
            "PRIMITIVE-IDENTIFIER--SIMPLE": "java.lang.String",
            "NMTOKENS-STRING--SIMPLE": "java.lang.String",
            "VIEW-TOKENS--SIMPLE": "java.lang.String",
            "NMTOKEN-STRING--SIMPLE": "java.lang.String",
            "IDENTIFIER--SIMPLE": "java.lang.String",
            "POSITIVE-INTEGER--SIMPLE": "java.lang.String",
            "INTEGER--SIMPLE": "java.lang.String",
            "MIME-TYPE-STRING--SIMPLE": "java.lang.String",
        },
        'group': {

        },
        'mixed':{
            "FT": "LOverviewParagraph",
            #在外面判断所属类，不是则replace overview
            # "FT": "LParagraph",
            "TRACE-REF": "TraceRef",
            "IE": "IndexEntry",
            "STD": "Std",
            "XDOC": "Xdoc",
            "XFILE": "Xfile",
            "SUP": "Supscript",
            "SUB": "Supscript",
            "TT": "Tt",
            "E": "EmphasisText",
            "XREF": "Xref",
            "BR": "Br",
            "XREF-TARGET": "XrefTarget",
            "VERBATIM": "MultiLanguageVerbatim",
        }
    }

    mapping = xsdToJavaTypeMap.get(context, {})

    if not isinstance(xsdType, str):
        xsdType = str(xsdType)

    # if context == 'base_type':
    #     if 'ENUM' in xsdType:
    #         # 如果 xsdType 包含 'Enum'，则使用 PascalCase 转换
    #         return to_pascal_case(xsdType)
    #     elif 'SIMPLE' in xsdType:
    #         # 如果 xsdType 仅包含 'Simple'，则映射为 'java.lang.String'
    #         return 'java.lang.String'
    #     else:
    #         # 如果没有匹配，仍然使用 PascalCase 转换
    #         return to_pascal_case(xsdType)
    # else:
    #     # 其他上下文下，默认返回 PascalCase 类型
    return mapping.get(xsdType, to_pascal_case(xsdType))
def to_pascal_case(snake_str):
    if not isinstance(snake_str, str):
        snake_str = str(snake_str)  # 将非字符串类型转换为字符串
    if snake_str in special_pascal_mappings:
        return special_pascal_mappings[snake_str]

    components = re.split('[-_]', snake_str)
    return ''.join(x.capitalize() for x in components)

def to_camel_case(snake_str):
    if not isinstance(snake_str, str):
        return snake_str  # 如果输入不是字符串，直接返回原值或处理为默认值
    if snake_str in special_camel_mappings:
        return special_camel_mappings[snake_str]

    components = re.split('[-_]', snake_str)
    return components[0].lower() + ''.join(x.title() for x in components[1:])

special_pascal_mappings = {
"AR-ELEMENT":"ARElement",
"AR-OBJECT":"ARObject",
"AR-PACKAGE":"ARPackage",
"AUTOSAR":"AUTOSAR",
"DIAGNOSTIC-CONTROL-DTC-SETTING":"DiagnosticControlDTCSetting",
"DIAGNOSTIC-CONTROL-DTC-SETTING-CLASS":"DiagnosticControlDTCSettingClass",
"DIAGNOSTIC-IO-CONTROL":"DiagnosticIOControl",
"DIAGNOSTIC-READ-DTC-INFORMATION":"DiagnosticReadDTCInformation",
"DIAGNOSTIC-READ-DTC-INFORMATION-CLASS":"DiagnosticReadDTCInformationClass",
"DIAGNOSTIC-READ-DATA-BY-PERIODIC-ID":"DiagnosticReadDataByPeriodicID",
"DIAGNOSTIC-READ-DATA-BY-PERIODIC-ID-CLASS":"DiagnosticReadDataByPeriodicIDClass",
"ECU-MAPPING":"ECUMapping",
"EOC-EVENT-REF":"EOCEventRef",
"EOC-EXECUTABLE-ENTITY-REF":"EOCExecutableEntityRef",
"EOC-EXECUTABLE-ENTITY-REF-ABSTRACT":"EOCExecutableEntityRefAbstract",
"EOC-EXECUTABLE-ENTITY-REF-GROUP":"EOCExecutableEntityRefGroup",
"FM-ATTRIBUTE-DEF":"FMAttributeDef",
"FM-ATTRIBUTE-VALUE":"FMAttributeValue",
"FM-CONDITION-BY-FEATURES-AND-ATTRIBUTES":"FMConditionByFeaturesAndAttributes",
"FM-CONDITION-BY-FEATURES-AND-SW-SYSTEMCONSTS":"FMConditionByFeaturesAndSwSystemconsts",
"FM-FEATURE":"FMFeature",
"FM-FEATURE-DECOMPOSITION":"FMFeatureDecomposition",
"FM-FEATURE-MAP":"FMFeatureMap",
"FM-FEATURE-MAP-ASSERTION":"FMFeatureMapAssertion",
"FM-FEATURE-MAP-CONDITION":"FMFeatureMapCondition",
"FM-FEATURE-MAP-ELEMENT":"FMFeatureMapElement",
"FM-FEATURE-MODEL":"FMFeatureModel",
"FM-FEATURE-RELATION":"FMFeatureRelation",
"FM-FEATURE-RESTRICTION":"FMFeatureRestriction",
"FM-FEATURE-SELECTION":"FMFeatureSelection",
"FM-FEATURE-SELECTION-SET":"FMFeatureSelectionSet",
"FM-FORMULA-BY-FEATURES-AND-ATTRIBUTES":"FMFormulaByFeaturesAndAttributes",
"FM-FORMULA-BY-FEATURES-AND-SW-SYSTEMCONSTS":"FMFormulaByFeaturesAndSwSystemconsts",
"INSTANTIATION-RTE-EVENT-PROPS":"InstantiationRTEEventProps",
"PR-PORT-PROTOTYPE":"PRPortPrototype",
"PARAMETER-IN-ATOMIC-SWC-TYPE-INSTANCE-REF":"ParameterInAtomicSWCTypeInstanceRef",
"PORT-API-OPTION":"PortAPIOption",
"R-MODE-GROUP-IN-ATOMIC-SWC-INSTANCE-REF":"RModeGroupInAtomicSWCInstanceRef",
"RTE-EVENT":"RTEEvent",
"SOMEIP-TRANSFORMATION-DESCRIPTION":"SOMEIPTransformationDescription",
"SOMEIP-TRANSFORMATION-I-SIGNAL-PROPS":"SOMEIPTransformationISignalProps",
"SOMEIP-TRANSFORMATION-I-SIGNAL-PROPS-CONDITIONAL":"SOMEIPTransformationISignalPropsConditional",
"SOMEIP-TRANSFORMATION-I-SIGNAL-PROPS-CONTENT":"SOMEIPTransformationISignalPropsContent",
"TD-EVENT-BSW":"TDEventBsw",
"TD-EVENT-BSW-INTERNAL-BEHAVIOR":"TDEventBswInternalBehavior",
"TD-EVENT-BSW-MODE-DECLARATION":"TDEventBswModeDeclaration",
"TD-EVENT-BSW-MODULE":"TDEventBswModule",
"TD-EVENT-COM":"TDEventCom",
"TD-EVENT-COMPLEX":"TDEventComplex",
"TD-EVENT-CYCLE-START":"TDEventCycleStart",
"TD-EVENT-FR-CLUSTER-CYCLE-START":"TDEventFrClusterCycleStart",
"TD-EVENT-FRAME":"TDEventFrame",
"TD-EVENT-I-PDU":"TDEventIPdu",
"TD-EVENT-I-SIGNAL":"TDEventISignal",
"TD-EVENT-MODE-DECLARATION":"TDEventModeDeclaration",
"TD-EVENT-OCCURRENCE-EXPRESSION":"TDEventOccurrenceExpression",
"TD-EVENT-OCCURRENCE-EXPRESSION-FORMULA":"TDEventOccurrenceExpressionFormula",
"TD-EVENT-OPERATION":"TDEventOperation",
"TD-EVENT-SWC":"TDEventSwc",
"TD-EVENT-SWC-INTERNAL-BEHAVIOR":"TDEventSwcInternalBehavior",
"TD-EVENT-SWC-INTERNAL-BEHAVIOR-REFERENCE":"TDEventSwcInternalBehaviorReference",
"TD-EVENT-TT-CAN-CYCLE-START":"TDEventTTCanCycleStart",
"TD-EVENT-TRIGGER":"TDEventTrigger",
"TD-EVENT-VARIABLE-DATA-PROTOTYPE":"TDEventVariableDataPrototype",
"TD-EVENT-VFB":"TDEventVfb",
"TD-EVENT-VFB-PORT":"TDEventVfbPort",
"TD-EVENT-VFB-REFERENCE":"TDEventVfbReference",
"VARIABLE-IN-ATOMIC-SWC-TYPE-INSTANCE-REF":"VariableInAtomicSWCTypeInstanceRef"
}
special_camel_mappings = {
"AR-ELEMENT":"aRElement",
"AR-OBJECT":"aRObject",
"AR-PACKAGE":"aRPackage",
"AUTOSAR":"aUTOSAR",
"DIAGNOSTIC-CONTROL-DTC-SETTING":"diagnosticControlDTCSetting",
"DIAGNOSTIC-CONTROL-DTC-SETTING-CLASS":"diagnosticControlDTCSettingClass",
"DIAGNOSTIC-IO-CONTROL":"diagnosticIOControl",
"DIAGNOSTIC-READ-DTC-INFORMATION":"diagnosticReadDTCInformation",
"DIAGNOSTIC-READ-DTC-INFORMATION-CLASS":"diagnosticReadDTCInformationClass",
"DIAGNOSTIC-READ-DATA-BY-PERIODIC-ID":"diagnosticReadDataByPeriodicID",
"DIAGNOSTIC-READ-DATA-BY-PERIODIC-ID-CLASS":"diagnosticReadDataByPeriodicIDClass",
"ECU-MAPPING":"eCUMapping",
"EOC-EVENT-REF":"eOCEventRef",
"EOC-EXECUTABLE-ENTITY-REF":"eOCExecutableEntityRef",
"EOC-EXECUTABLE-ENTITY-REF-ABSTRACT":"eOCExecutableEntityRefAbstract",
"EOC-EXECUTABLE-ENTITY-REF-GROUP":"eOCExecutableEntityRefGroup",
"FM-ATTRIBUTE-DEF":"fMAttributeDef",
"FM-ATTRIBUTE-VALUE":"fMAttributeValue",
"FM-CONDITION-BY-FEATURES-AND-ATTRIBUTES":"fMConditionByFeaturesAndAttributes",
"FM-CONDITION-BY-FEATURES-AND-SW-SYSTEMCONSTS":"fMConditionByFeaturesAndSwSystemconsts",
"FM-FEATURE":"fMFeature",
"FM-FEATURE-DECOMPOSITION":"fMFeatureDecomposition",
"FM-FEATURE-MAP":"fMFeatureMap",
"FM-FEATURE-MAP-ASSERTION":"fMFeatureMapAssertion",
"FM-FEATURE-MAP-CONDITION":"fMFeatureMapCondition",
"FM-FEATURE-MAP-ELEMENT":"fMFeatureMapElement",
"FM-FEATURE-MODEL":"fMFeatureModel",
"FM-FEATURE-RELATION":"fMFeatureRelation",
"FM-FEATURE-RESTRICTION":"fMFeatureRestriction",
"FM-FEATURE-SELECTION":"fMFeatureSelection",
"FM-FEATURE-SELECTION-SET":"fMFeatureSelectionSet",
"FM-FORMULA-BY-FEATURES-AND-ATTRIBUTES":"fMFormulaByFeaturesAndAttributes",
"FM-FORMULA-BY-FEATURES-AND-SW-SYSTEMCONSTS":"fMFormulaByFeaturesAndSwSystemconsts",
"INSTANTIATION-RTE-EVENT-PROPS":"instantiationRTEEventProps",
"PR-PORT-PROTOTYPE":"pRPortPrototype",
"PARAMETER-IN-ATOMIC-SWC-TYPE-INSTANCE-REF":"parameterInAtomicSWCTypeInstanceRef",
"PORT-API-OPTION":"portAPIOption",
"R-MODE-GROUP-IN-ATOMIC-SWC-INSTANCE-REF":"rModeGroupInAtomicSWCInstanceRef",
"RTE-EVENT":"rTEEvent",
"SOMEIP-TRANSFORMATION-DESCRIPTION":"sOMEIPTransformationDescription",
"SOMEIP-TRANSFORMATION-I-SIGNAL-PROPS":"sOMEIPTransformationISignalProps",
"SOMEIP-TRANSFORMATION-I-SIGNAL-PROPS-CONDITIONAL":"sOMEIPTransformationISignalPropsConditional",
"SOMEIP-TRANSFORMATION-I-SIGNAL-PROPS-CONTENT":"sOMEIPTransformationISignalPropsContent",
"TD-EVENT-BSW":"tDEventBsw",
"TD-EVENT-BSW-INTERNAL-BEHAVIOR":"tDEventBswInternalBehavior",
"TD-EVENT-BSW-MODE-DECLARATION":"tDEventBswModeDeclaration",
"TD-EVENT-BSW-MODULE":"tDEventBswModule",
"TD-EVENT-COM":"tDEventCom",
"TD-EVENT-COMPLEX":"tDEventComplex",
"TD-EVENT-CYCLE-START":"tDEventCycleStart",
"TD-EVENT-FR-CLUSTER-CYCLE-START":"tDEventFrClusterCycleStart",
"TD-EVENT-FRAME":"tDEventFrame",
"TD-EVENT-I-PDU":"tDEventIPdu",
"TD-EVENT-I-SIGNAL":"tDEventISignal",
"TD-EVENT-MODE-DECLARATION":"tDEventModeDeclaration",
"TD-EVENT-OCCURRENCE-EXPRESSION":"tDEventOccurrenceExpression",
"TD-EVENT-OCCURRENCE-EXPRESSION-FORMULA":"tDEventOccurrenceExpressionFormula",
"TD-EVENT-OPERATION":"tDEventOperation",
"TD-EVENT-SWC":"tDEventSwc",
"TD-EVENT-SWC-INTERNAL-BEHAVIOR":"tDEventSwcInternalBehavior",
"TD-EVENT-SWC-INTERNAL-BEHAVIOR-REFERENCE":"tDEventSwcInternalBehaviorReference",
"TD-EVENT-TT-CAN-CYCLE-START":"tDEventTTCanCycleStart",
"TD-EVENT-TRIGGER":"tDEventTrigger",
"TD-EVENT-VARIABLE-DATA-PROTOTYPE":"tDEventVariableDataPrototype",
"TD-EVENT-VFB":"tDEventVfb",
"TD-EVENT-VFB-PORT":"tDEventVfbPort",
"TD-EVENT-VFB-REFERENCE":"tDEventVfbReference",
"VARIABLE-IN-ATOMIC-SWC-TYPE-INSTANCE-REF":"variableInAtomicSWCTypeInstanceRef"
}



