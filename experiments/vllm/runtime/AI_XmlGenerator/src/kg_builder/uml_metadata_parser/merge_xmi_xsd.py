import json
import os
import re
from pathlib import Path


def load_json_file(file_path):
    """尝试加载JSON文件，如果格式有问题则尝试修复"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"JSON解析错误在文件 {file_path}:")
        print(f"错误信息: {str(e)}")

        # 读取文件内容进行修复
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 尝试修复常见的JSON问题
        fixed_content = fix_json(content)

        # 保存原始文件备份
        backup_path = str(file_path) + ".backup"
        os.rename(file_path, backup_path)
        print(f"原始文件已备份到 {backup_path}")

        # 保存修复后的内容
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        print(f"已尝试修复并保存到 {file_path}")

        # 重新加载修复后的文件
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)


def fix_json(content):
    """修复常见的JSON格式问题"""
    # 修复属性名没有双引号问题
    content = re.sub(r'([{,]\s*)([a-zA-Z0-9_]+)(\s*:)', r'\1"\2"\3', content)

    # 修复单引号问题
    content = re.sub(r"'([^']*)'", r'"\1"', content)

    # 移除尾部多余的逗号
    content = re.sub(r',(\s*[}\]])', r'\1', content)

    # 修复可能缺失的引号
    content = re.sub(r': *([a-zA-Z][a-zA-Z0-9_]+)([,}])', r': "\1"\2', content)

    return content


def save_json_file(data, file_path):
    """保存数据到JSON文件"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def remove_inner_classes_from_groups(metadata):
    """从metadata的groups中删除innerClasses字段"""
    groups = metadata.get("groups", {})
    removed_count = 0

    for group_name, group_data in groups.items():
        if "innerClasses" in group_data:
            del group_data["innerClasses"]
            removed_count += 1

    if removed_count > 0:
        print(f"\n已从 {removed_count} 个groups元素中删除innerClasses字段")
    else:
        print("\n未在groups中找到innerClasses字段")

    return metadata


def remove_fields_from_structure(structure):
    """从structure中删除Aggregation和parents字段"""
    aggregation_count = 0
    parents_count = 0

    for class_name, class_data in structure.items():
        if "Aggregation" in class_data:
            del class_data["Aggregation"]
            aggregation_count += 1

        if "parents" in class_data:
            del class_data["parents"]
            parents_count += 1

    if aggregation_count > 0 or parents_count > 0:
        print(f"\n已删除 {aggregation_count} 个Aggregation字段和 {parents_count} 个parents字段")
    else:
        print("\n未在structure中找到需要删除的字段")

    return structure


def remove_duplicate_complex_types(metadata):
    """从complexTypes中删除与groups重名的元素"""
    groups = metadata.get("groups", {})
    complex_types = metadata.get("complexTypes", {})

    # 查找groups和complexTypes中重名的元素
    duplicates = []
    for name in complex_types.keys():
        if name in groups:
            duplicates.append(name)

    # 从complexTypes中删除重名元素
    for name in duplicates:
        complex_types.pop(name)

    # 打印删除信息
    if duplicates:
        print(f"\n已从complexTypes中删除以下{len(duplicates)}个与groups重名的元素:")
        for elem in sorted(duplicates):
            print(f"- {elem}")
    else:
        print("\n未发现complexTypes中与groups重名的元素")

    # 更新metadata
    metadata["complexTypes"] = complex_types
    return metadata


def merge_elements(metadata_groups, structure):
    """合并来自metadata.json和structure.json的元素"""
    merged_result = {}
    merged_elements = set()  # 记录已合并的元素

    # 遍历metadata.json中的groups元素
    for group_name, group_data in metadata_groups.items():
        merged_result[group_name] = group_data.copy()  # 从metadata数据开始

        # 检查该元素是否也存在于structure.json中
        if group_name in structure:
            # 合并来自structure.json的数据
            structure_data = structure[group_name]
            for key, value in structure_data.items():
                # 添加来自structure.json的键值对
                merged_result[group_name][key] = value

            # 记录该元素已被合并
            merged_elements.add(group_name)

    # 找出未合并的元素
    all_structure_elements = set(structure.keys())
    unmerged_elements = all_structure_elements - merged_elements

    return merged_result, unmerged_elements


def main():
    # 定义输入和输出路径
    input_dir = Path("output")
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    metadata_path = input_dir / "metadata.json"
    structure_path = input_dir / "structure.json"
    output_path = output_dir / "unified_metadata.json"

    try:
        # 加载JSON文件
        print(f"正在加载 {metadata_path}...")
        metadata = load_json_file(metadata_path)

        # 从metadata的groups中删除innerClasses字段
        print("删除groups中的innerClasses字段...")
        metadata = remove_inner_classes_from_groups(metadata)

        # 移除complexTypes中与groups重名的元素
        print("检查并删除complexTypes中与groups重名的元素...")
        metadata = remove_duplicate_complex_types(metadata)

        print(f"正在加载 {structure_path}...")
        structure = load_json_file(structure_path)

        # 从structure中删除Aggregation和parents字段
        print("删除structure中的Aggregation和parents字段...")
        structure = remove_fields_from_structure(structure)

        # 提取metadata.json中的groups
        metadata_groups = metadata.get("groups", {})

        # 合并元素
        print("合并元素...")
        merged_data, unmerged_elements = merge_elements(metadata_groups, structure)

        # 打印未合并的元素
        if unmerged_elements:
            print(
                f"\n以下 {len(unmerged_elements)} 个元素在 structure.json 中存在但未被合并（因为在 metadata.json 的 groups 中未找到）:")
            for elem in sorted(unmerged_elements):
                print(f"- {elem}")
        else:
            print("\nstructure.json 中的所有元素都已合并")

        # 创建最终输出数据，保留metadata中的所有元素
        output_data = metadata.copy()
        # 用合并后的groups更新输出数据
        output_data["groups"] = merged_data

        # 保存合并结果
        save_json_file(output_data, output_path)
        print(f"\n合并数据已保存到 {output_path}")
    except Exception as e:
        print(f"处理过程中出错: {str(e)}")
        raise e


if __name__ == "__main__":
    main()