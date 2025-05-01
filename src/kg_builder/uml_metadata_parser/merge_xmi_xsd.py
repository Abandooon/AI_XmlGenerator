import json
import os
from pathlib import Path
import re


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
    input_dir = Path("input")
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    metadata_path = input_dir / "metadata.json"
    structure_path = input_dir / "structure.json"
    output_path = output_dir / "merged.json"

    try:
        # 加载JSON文件
        print(f"正在加载 {metadata_path}...")
        metadata = load_json_file(metadata_path)

        print(f"正在加载 {structure_path}...")
        structure = load_json_file(structure_path)

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

        # 保存合并结果
        output_data = {"groups": merged_data}
        save_json_file(output_data, output_path)

        print(f"\n合并数据已保存到 {output_path}")
    except Exception as e:
        print(f"处理过程中出错: {str(e)}")
        raise e


if __name__ == "__main__":
    main()