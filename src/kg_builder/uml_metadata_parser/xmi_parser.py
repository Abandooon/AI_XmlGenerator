import os
import json
from lxml import etree

# 定义命名空间
namespaces = {
    'uml': 'http://schema.omg.org/spec/UML/2.1',
    'xmi': 'http://schema.omg.org/spec/XMI/2.1'
}


class XmiProcessor:
    def __init__(self):
        self.id_to_class = {}
        self.classes_dict = {}

    def build_class_mapping(self, root):
        """构建全局类ID到类名的映射"""
        for cls in root.findall('.//packagedElement[@xmi:type="uml:Class"]', namespaces):
            cls_id = cls.get(f'{{{namespaces["xmi"]}}}id')
            if cls_id:
                cls_name = cls.get('name', '')
                self.id_to_class[cls_id] = cls_name

    def process_links(self, xml_element, class_info, root):
        """处理链接关系并将结果存入class_info字典"""
        class_name = xml_element.get('name')

        extension = root.find('.//xmi:Extension', namespaces)
        if extension is None:
            return

        elements = extension.findall('.//element[@xmi:type="uml:Class"]', namespaces)

        associated_from = []
        associated_to = []
        parents = set()
        childs = set()
        aggregations = []
        dependencies = []

        for element in elements:
            if element.get('name') == class_name:
                for link in element.findall('links', namespaces):
                    for rel_type in ['Aggregation', 'Generalization', 'Dependency', 'Association']:
                        for rel in link.findall(rel_type, namespaces):
                            start_id = rel.get('start')
                            end_id = rel.get('end')
                            start_name = self.id_to_class.get(start_id)
                            end_name = self.id_to_class.get(end_id)

                            if not start_name or not end_name:
                                continue

                            if rel_type == 'Generalization':
                                if start_name != class_name:
                                    childs.add(start_name)
                                if end_name != class_name:
                                    parents.add(end_name)
                            elif rel_type == 'Aggregation':
                                aggregations.append(f"start:{start_name},end:{end_name};")
                            elif rel_type == 'Dependency':
                                dependencies.append(f"start:{start_name},end:{end_name};")
                            elif rel_type == 'Association':
                                if start_name == class_name:
                                    associated_to.append(end_name)
                                elif end_name == class_name:
                                    associated_from.append(start_name)

        if parents:
            class_info['parents'] = ','.join(parents)
        if childs:
            class_info['childs'] = ','.join(childs)
        if aggregations:
            class_info['Aggregation'] = ''.join(aggregations)
        if dependencies:
            class_info['Dependency'] = ''.join(dependencies)
        if associated_to:
            class_info['ClassAssociatedTo'] = ','.join(associated_to)
        if associated_from:
            class_info['ClassAssociatedFrom'] = ','.join(associated_from)

    def process_generalizations(self, xml_class, class_info):
        """处理继承关系并存入class_info"""
        generalizations = []
        for gen in xml_class.findall('generalization'):
            general_id = gen.get('general')
            if general_id in self.id_to_class:
                generalizations.append(self.id_to_class[general_id])
        if generalizations:
            class_info['generalization'] = ','.join(generalizations)

    def process_element(self, xml_elem, root, package_path):
        """递归处理元素并收集类信息"""
        elem_type = xml_elem.get(f'{{{namespaces["xmi"]}}}type', '')
        elem_name = xml_elem.get('name', '')

        if elem_type == 'uml:Package':
            new_package = package_path + [elem_name]
            for child in xml_elem.iterchildren():
                self.process_element(child, root, new_package)
        elif elem_type == 'uml:Class':
            class_name = elem_name
            class_info = {
                'Package': ','.join(package_path),
                'abstract': xml_elem.get('isAbstract', 'false').lower()
            }
            self.process_links(xml_elem, class_info, root)
            self.process_generalizations(xml_elem, class_info)
            self.classes_dict[class_name] = class_info

    def process_model(self, model_root):
        """处理整个模型并构建数据字典"""
        xmi_root = model_root.getroottree().getroot()
        for elem in model_root.iterchildren():
            if elem.tag == 'packagedElement' and elem.get(f'{{{namespaces["xmi"]}}}type') == 'uml:Package':
                self.process_element(elem, xmi_root, [])


def main():
    processor = XmiProcessor()

    input_path = 'input/AUTOSAR_XMI.xmi'
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'structure.json')

    tree = etree.parse(input_path, etree.XMLParser(remove_blank_text=True))
    root = tree.getroot()

    processor.build_class_mapping(root)

    model = root.find('.//uml:Model', namespaces=namespaces)
    if model is None:
        raise ValueError("未找到UML模型根元素")

    processor.process_model(model)

    # 转换为JSON并保存
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(processor.classes_dict, f, indent=2, ensure_ascii=False)

    print(f"生成文件：{output_path}")


if __name__ == "__main__":
    main()