import os
from src.data_processing.uml_metadata_parser.XsdParser.Expansion.GenerateInterface import generate_interface
from src.data_processing.uml_metadata_parser.XsdParser.Utils import to_pascal_case

# 维护一个全局的内部类信息列表
inner_class_info_list = []
# 新增一个全局的所有类信息列表
all_class_info_list = []
rename_element=[]
def extract_internals_classes(complexType, output_dir, package_name, class_template, interfaces_name,groups,generate_abstract_interface,input_dir,interface_package_name):
    parent_class_name = None
    if not complexType.get('innerClasses'):
        all_class_info_list.append({
            'name': to_pascal_case(complexType['name']),
            'attributes': complexType['attributes'],
            'isAttribute': complexType['isAttribute']
        })
        return

    main_class_name = to_pascal_case(complexType['name']) if parent_class_name is None else parent_class_name
    for inner_class in complexType['innerClasses']:
        xmlType = inner_class['xmlType']
        rootElementName = inner_class['xmlType']
        inner_class_name = inner_class['InnerClassName']
        inner_class_attributes = inner_class['InnerClassAttributes']
        #记录内部类所属group，提取修改
        source_group = inner_class['group']

        # 初始化标记变量
        is_duplicate = False
        rename_flag = False
        other_main_name = None

        # 收集所有匹配的内部类信息
        matching_infos = [info for info in inner_class_info_list if info['inner_class_name'] == inner_class_name]

        # 处理匹配的内部类信息
        for info in matching_infos:
            if info['inner_class_attributes'] == inner_class_attributes:
                # 属性相等，存在重复，不生成文件
                is_duplicate = True
                rename_flag = info['rename_flag']
                if rename_flag:
                    other_main_name = info['main_class_name']
                # 已经找到属性相等的情况，可以退出循环
                break
            else:
                # 属性不等，需要重命名
                rename_flag = True
                # 不要break，继续检查是否有属性相等的情况

        if not is_duplicate:
            if rename_flag:
                # 名字相同但属性不匹配，需要重命名并生成类文件
                new_inner_class_name = f"{inner_class_name}_{main_class_name}"
                xmlType = f"{xmlType}_{main_class_name}"
                inner_class_info_list.append({
                    'inner_class_name': inner_class_name,
                    'main_class_name': main_class_name,
                    'rename_flag': True,
                    'inner_class_attributes': inner_class_attributes
                })

                # 更新父级类中的成员类型
                update_parent_attributes(complexType, inner_class_name, new_inner_class_name)
                update_group_attributes(groups, inner_class_name, new_inner_class_name,source_group)
                # 将内部类信息添加到全局列表
                all_class_info_list.append({
                    'name': new_inner_class_name,
                    'attributes': inner_class_attributes,
                    'isAttribute': complexType['isAttribute']
                })
            else:
                # 首次出现，生成类文件
                inner_class_info_list.append({
                    'inner_class_name': inner_class_name,
                    'main_class_name': main_class_name,
                    'rename_flag': False,
                    'inner_class_attributes': inner_class_attributes
                })
                # 将内部类信息添加到全局列表
                all_class_info_list.append({
                    'name': inner_class_name,
                    'attributes': inner_class_attributes,
                    'isAttribute': complexType['isAttribute']
                })
        else:
            if rename_flag:
                # 不生成内部类文件，需要修改父级类的成员类型
                new_inner_class_name = f"{inner_class_name}_{other_main_name}"
                update_parent_attributes(complexType, inner_class_name, new_inner_class_name)
                update_group_attributes(groups, inner_class_name, new_inner_class_name,source_group)
                # 不需要break，继续处理
            else:
                # 不生成内部类文件，父级类成员类型不变
                pass

        # **递归处理嵌套的内部类**
        if inner_class.get('innerInnerClass'):
            inner_inner_classes = inner_class.get('innerInnerClass')
            for inner_inner_class in inner_inner_classes:
                # 将嵌套内部类信息添加到全局列表
                all_class_info_list.append({
                    'name': inner_inner_class['InnerClassName'],
                    'attributes': inner_inner_class['InnerClassAttributes'],
                    'isAttribute': complexType['isAttribute']
                })

    # 如果当前处理的是主类，生成主类的Java代码
    if parent_class_name is None:
        all_class_info_list.append({
            'name': main_class_name,
            'attributes': complexType['attributes'],
            'isAttribute': complexType['isAttribute']
        })

    for attr in complexType['attributes']:
        if 'mixed_groups' in attr:
            if attr['mixed_groups'] is not None:
                for mix_group in attr['mixed_groups']:
                    group = groups[mix_group]
                    group['elements'].clear()
                    group['is_mixed'] = 'True'

    # 生成接口，提取内部类。需修改接口元素名
    generate_interface(input_dir, output_dir, groups, interface_package_name, package_name)

def update_parent_attributes(parent_class, old_inner_class_name, new_inner_class_name):
    for attribute in parent_class['attributes']:
        attr_type = attribute['type']
        if attr_type.startswith('List<') or attr_type.startswith('ArrayList<'):
            inner_type = attr_type[attr_type.find('<') + 1:attr_type.rfind('>')]
            if inner_type == old_inner_class_name:
                attribute['type'] = f"{attr_type[:attr_type.find('<') + 1]}{new_inner_class_name}{attr_type[attr_type.rfind('>'):]}"
        elif attr_type == old_inner_class_name:
            attribute['type'] = new_inner_class_name

def update_group_attributes(groups, old_inner_class_name, new_inner_class_name,source_group):
    for attribute in groups[source_group]['elements']:
        attr_type = attribute['type']
        if attr_type.startswith('List<') or attr_type.startswith('ArrayList<'):
            inner_type = attr_type[attr_type.find('<') + 1:attr_type.rfind('>')]
            if inner_type == old_inner_class_name:
                attribute['type'] = f"{attr_type[:attr_type.find('<') + 1]}{new_inner_class_name}{attr_type[attr_type.rfind('>'):]}"
        elif attr_type == old_inner_class_name:
            attribute['type'] = new_inner_class_name


