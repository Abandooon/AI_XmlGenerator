import os
from pathlib import Path


def convert_txt_to_arxml(input_dir="."):
    """
    遍历指定目录下的所有txt文件，去除markdown代码块标记，转换为arxml文件

    Args:
        input_dir: 输入目录，默认为当前目录
    """
    input_path = Path(input_dir)

    # 查找所有txt文件
    txt_files = list(input_path.glob("*.txt"))

    if not txt_files:
        print(f"在目录 {input_path} 中未找到txt文件")
        return

    print(f"找到 {len(txt_files)} 个txt文件")

    converted_count = 0

    for txt_file in txt_files:
        try:
            # 读取txt文件内容
            with open(txt_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            if not lines:
                print(f"跳过空文件: {txt_file.name}")
                continue

            # 去除第一行的```xml和最后一行的```
            if lines and lines[0].strip() == "```xml":
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            # 生成输出文件路径
            output_file = txt_file.with_suffix('.arxml')

            # 写入arxml文件
            with open(output_file, 'w', encoding='utf-8') as f:
                f.writelines(lines)

            print(f"✅ 转换完成: {txt_file.name} -> {output_file.name}")
            converted_count += 1

        except Exception as e:
            print(f"❌ 转换失败 {txt_file.name}: {e}")

    print(f"\n转换完成！成功转换 {converted_count} 个文件")


if __name__ == "__main__":
    convert_txt_to_arxml()