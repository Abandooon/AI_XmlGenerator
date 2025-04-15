# -*- coding: utf-8 -*-
import os
import re

from jinja2 import Environment, FileSystemLoader

from src.data_processing.uml_metadata_parser.XsdParser.Expansion.GenerateRefObj import get_different_tag_elements, \
    get_complex_ref, get_subtypes
from src.data_processing.uml_metadata_parser.XsdParser.Utils import to_pascal_case


def collect_wrapper_class_names(complexTypeClassesInfo):
    wrapper_class_names = set()
    for class_info in complexTypeClassesInfo:
        class_name = class_info['name']
        wrapper_class_name = class_name + 'Wrapper'
        wrapper_class_names.add(wrapper_class_name)
    return wrapper_class_names

def generate_wrapper_classes(input_dir, complexTypeClassesInfo, output_dir, wrapper_package_name, wrapper_class_names, package_name):


    # 正则表达式匹配 ArrayList<SomeType> 的类型
    list_type_pattern = re.compile(r'ArrayList<(.+)>')


    for class_info in complexTypeClassesInfo:
        original_class_name = class_info['name']
        original_variable_name = class_info['name'][0].lower() + class_info['name'][1:] if original_class_name not in ['String', 'Boolean', 'Float', 'Integer'] else class_info['name'][0].lower() + class_info['name'][1:] + '1'
        wrapper_class_name = original_class_name + 'Wrapper'
        attributes = []
        additional_api_methods = []  # 保存需要生成的 API 方法信息
        additional_api_refs = []  # 保存需要生成的主类中的ref方法信息

        has_arraylist_serializable = False  # 标记是否存在 ArrayList<Serializable> 类型
        has_ref_object = False  # 标记是否存在 refObject 类型
        has_ref_attr = False
        isAttribute = class_info['isAttribute']
        isList = False

        has_different_tag=False
        differentTag=None
        #保存被引用的name与type不同的Element信息
        differentTagsElements = get_different_tag_elements(input_dir)

        # todo：遍历类中的属性------------------------------------------------------------
        # 1. Ref类且属性有dest，则搜索所有子类确定返回值类型，在模板中构建get方法
        # 2. 类中属性有ref，将这个ref中的查找方法放到该类中，（list？）
        # 3. 类中有ArrayList<Serializable>，查找引用的元素类，模板中提供方法
        for attribute in class_info['attributes']:
            attr_type = attribute.get('type')  # 获取属性的类型
            anno = attribute.get('annotation')  # 获取注解信息
            attr_name = attribute.get('name')  # 获取属性的 name
            has_different_tag_attr = False
            differentTagAttr = None
            #针对ref类添加查找方法
            if attr_name is None:
                continue
            #第一种情况针对引用类：本身为Ref类且属性有dest，则搜索所有子类确定返回值类型，在模板中构建get方法，与其他if条件互不相关，对返回值类型无影响
            if original_class_name.split('_')[0].endswith(('Ref', 'Iref', 'Tref')) and attr_name == 'dest':
                #遍历DifferentTagsWithElements.xml中的elementClass并转为驼峰，如果其中有与类名匹配的，并且simpleTypeName（转驼峰）与attr_type匹配，则标记并传递name标签到查找方法模板
                for elementClass in differentTagsElements:
                    if original_class_name.split('_')[0] == elementClass['elementClass'] and attr_type==elementClass['simpleTypeName']:
                        has_different_tag = True
                        differentTag=elementClass['refDestName']

                # 标记为有引用对象
                has_ref_object = True

                # 提取 enumType 并转换为大写字母，以便在 get_subtypes 中查找
                enumType = '-'.join(re.findall(r'[A-Z][^A-Z]*', attr_type.replace('SubtypesEnum', ''))).upper()

                # 调用 get_subtypes 函数，获取 RefObjs[]（即 complexTypes 列表）
                refObjNames = get_subtypes(input_dir, enumType)

                # 遍历每个 refObjName，生成 getter 方法
                for refObjName in refObjNames:
                    # 预先检查是否有 Wrapper 类
                    has_wrapper = refObjName + 'Wrapper' in wrapper_class_names
                    return_type = refObjName + 'Wrapper' if has_wrapper else refObjName

                    # 构建 method_info，减少重复代码
                    method_info = {
                        'annotation_pascal_case': return_type,  # PascalCase 类名或 Wrapper 类名
                        # 'original_variable_name': refObjName.lower(),  # 小写形式的变量名
                        'has_wrapper': has_wrapper  # 是否有 Wrapper 类
                    }

                    # 将 method_info 添加到 additional_api_methods 列表
                    additional_api_methods.append(method_info)

            #第二种情况针对非引用类中的属性：分为三种，1.区分是否为list、普通属性、ref、混合元素，是否有wrapper，2.非list，普通属性、ref，是否有wrapper
            #针对主类中的引用属性，将查找方法提到主类中，主类中没法根据dest枚举查找子类

            # 获取所有引用复杂类型，即不用生成查找方法的属性类型
            complex_ref_list = get_complex_ref(input_dir)

            #如果正则匹配匹配到属性为list--------要对Serializable和ref做额外处理
            list_match = list_type_pattern.match(attr_type)
            # has_wrapper = False  # 标记是否有 Wrapper--------没用到吧
            if list_match:
                inner_type = list_match.group(1)
                # 处理 ArrayList<Serializable> 类型
                if inner_type == 'Serializable':
                    return_type = attr_type # ArrayList<Serializable>不用包装wrapper
                    has_arraylist_serializable = True  # 标记存在 ArrayList<Serializable>
                    # 从注解中获取所有 'name' 并转换为 PascalCase
                    if anno and 'name=' in anno:
                        names = re.findall(r'name="([^"]+)"', anno)  # 匹配所有 'name' 值
                        for annotation_name in names:
                            #将注解name转为QNAME通过工厂类实例化
                            annotation_pascal_case = to_pascal_case(annotation_name)
                            method_info = {
                                'annotation_pascal_case': annotation_pascal_case,
                            }
                            additional_api_methods.append(method_info)
                # 处理 ArrayList<Ref>类型
                elif inner_type.split('_')[0].endswith(('Ref', 'Iref', 'Tref')) and inner_type.split('_')[0] not in complex_ref_list:

                    inner_type_class = inner_type.split('_')[0]
                    # 如果 List 中的类型有对应的 Wrapper，则返回 ArrayList<SomeTypeWrapper>
                    if inner_type + 'Wrapper' in wrapper_class_names:
                        return_type = f'ArrayList<{inner_type}Wrapper>'
                    else:
                        return_type = f'ArrayList<{inner_type}>'
                    # 标记为有引用对象
                    has_ref_attr = True
                    isList = True
                    # 构建 method_info，减少重复代码
                    ref_info = {
                        'isList':isList,
                        'refMetfodName': to_pascal_case(attr_name.replace('Ref', '').replace('Iref', '').replace('Tref', '')), # PascalCase 类名或 Wrapper 类名
                        'attrType': inner_type,
                        'attrName': attr_name
                    }
                    additional_api_refs.append(ref_info)
                # 如果是其他 ArrayList<SomeType>
                elif inner_type + 'Wrapper' in wrapper_class_names:
                    # 如果 List 中的类型有对应的 Wrapper，则返回 ArrayList<SomeTypeWrapper>
                    return_type = f'ArrayList<{inner_type}Wrapper>'
                    has_wrapper = True
                else:
                    return_type = attr_type

            # 如果是普通类类型，如果是ref类，将查找方法提到主类中
            elif attr_type.split('_')[0].endswith(('Ref', 'Iref', 'Tref')) and attr_type.split('_')[0] not in complex_ref_list:
                for elementClass in differentTagsElements:
                    if attr_type.split('_')[0] == elementClass['elementClass']:
                        has_different_tag_attr = True
                        differentTagAttr=elementClass['refDestName']

                # 标记为有引用对象
                if attr_type + 'Wrapper' in wrapper_class_names:
                    return_type = attr_type + 'Wrapper'
                else:
                    return_type = attr_type
                has_ref_attr = True
                isList = False
                # 构建 method_info，减少重复代码
                ref_info = {
                    'isList':isList,
                    'refMetfodName': attr_name,  #用作get方法名
                    'attrType':attr_type,#填充对象类型
                    'attrName': attr_name,#当前类中的get ref方法
                    'hasDifferentTag':has_different_tag_attr,
                    'differentTagAttr':differentTagAttr
                }
                # 将 method_info 添加到 additional_api_methods 列表
                additional_api_refs.append(ref_info)
            # 如果是普通类型并且有 Wrapper
            elif attr_type + 'Wrapper' in wrapper_class_names:
                return_type = attr_type + 'Wrapper'
                # has_wrapper = True
            # 普通类型，无需包装
            else:
                return_type = attr_type

            # 将确定好的属性信息添加到 attributes 列表
            attribute['type'] = return_type
            # attribute['hasWrapper'] = has_wrapper
            attributes.append(attribute)

