from lxml import etree
import os


def extract_generalizations(input_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'generalizations.xml')

    try:
        # 命名空间定义
        namespaces = {
            'uml': 'http://schema.omg.org/spec/UML/2.1',
            'xmi': 'http://schema.omg.org/spec/XMI/2.1'
        }
        tree = etree.parse(input_path)
        root = tree.getroot()
        print(f"√ 成功解析文件: {os.path.basename(input_path)}")
    except Exception as e:
        print(f"× 文件解析失败: {str(e)}")
        return

    # 建立xmi:id到元素的完整映射
    id_to_element_map = {}
    for elem in root.xpath('//uml:Model//packagedElement', namespaces=namespaces):
        elem_id = elem.get('{http://schema.omg.org/spec/XMI/2.1}id')
        id_to_element_map[elem_id] = {
            'xmi_id': elem_id,
            'name': elem.get('name', 'unnamed'),
            'isAbstract': elem.get('isAbstract', 'false'),
            'type': elem.get('{http://schema.omg.org/spec/XMI/2.1}type')
        }
    print(f"建立 {len(id_to_element_map)} 个元素的完整映射")

    # 查找需要处理的父元素
    valid_parents = root.xpath('//uml:Model//packagedElement[./generalization]', namespaces=namespaces)
    print(f"找到 {len(valid_parents)} 个包含generalization的父元素")

    # 创建XML根节点
    new_root = etree.Element('GeneralizationSystem',
                             nsmap={'xmi': namespaces['xmi'],
                                    'uml': namespaces['uml']})

    # 处理每个父元素
    for parent_elem in valid_parents:
        parent_id = parent_elem.get('{http://schema.omg.org/spec/XMI/2.1}id')
        parent_info = id_to_element_map.get(parent_id, {
            'xmi_id': parent_id,
            'name': 'unknown',
            'isAbstract': 'false',
            'type': 'unknown'
        })

        # 创建唯一标识符（xmi_id + name）
        element_uid = f"{parent_info['xmi_id']}::{parent_info['name']}"
        print(f"\n处理元素: {element_uid}")

        # 创建Element节点，使用合法属性名
        element_node = etree.SubElement(new_root, 'Element', {
            'xmi_id': parent_info['xmi_id'],  # 使用xmi_id代替xmi:id
            'name': parent_info['name'],
            'isAbstract': parent_info['isAbstract'],
            'xmi_type': parent_info['type']  # 使用xmi_type代替xmi:type
        })

        # 处理generalization
        gen_count = 0
        for gen in parent_elem.iterchildren('generalization'):
            general_id = gen.get('general')
            father_info = id_to_element_map.get(general_id)

            if not father_info:
                print(f"  警告: 未找到general对应的元素 {general_id}")
                continue

            # 创建Generalization节点，使用合法属性名
            gen_node = etree.SubElement(element_node, 'Generalization', {
                'xmi_id': gen.get('{http://schema.omg.org/spec/XMI/2.1}id'),  # 使用xmi_id
                'general': general_id,
                'fatherXmiId': father_info['xmi_id'],
                'fatherName': father_info['name'],
                'fatherIsAbstract': father_info['isAbstract']
            })
            gen_count += 1
            print(f"  添加继承关系: {father_info['name']} ({father_info['xmi_id']})")

        print(f"共添加 {gen_count} 个继承关系")

    # 生成最终文件
    try:
        etree.register_namespace('xmi', namespaces['xmi'])
        etree.register_namespace('uml', namespaces['uml'])

        tree = etree.ElementTree(new_root)
        tree.write(output_path,
                   encoding='windows-1252',
                   xml_declaration=True,
                   pretty_print=True)
        print(f"\n√ 结果已保存至: {output_path}")
    except Exception as e:
        print(f"× 文件写入失败: {str(e)}")


if __name__ == "__main__":
    extract_generalizations('input/AUTOSAR_XMI_21.xmi', 'output')