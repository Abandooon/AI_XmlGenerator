import os
import subprocess
import sys
import time


def run_script(script_name, description):
    """运行指定的Python脚本并显示输出"""
    print(f"\n{'-' * 80}")
    print(f"执行: {description}")
    print(f"{'-' * 80}")

    start_time = time.time()
    result = subprocess.run([sys.executable, script_name], capture_output=True, text=True)

    if result.returncode == 0:
        print(result.stdout)
        print(f"✓ 成功完成! 耗时: {time.time() - start_time:.2f}秒")
        return True
    else:
        print(f"标准输出:\n{result.stdout}")
        print(f"错误输出:\n{result.stderr}")
        print(f"✗ 执行失败! 退出代码: {result.returncode}")
        return False


def check_files():
    """检查所需文件是否存在"""
    missing_files = []

    # 检查输入文件
    if not os.path.exists('input'):
        os.makedirs('input')
        missing_files.append("input/AUTOSAR_4-2-2.xsd")
        missing_files.append("input/AUTOSAR_XMI.xmi")
    else:
        if not os.path.exists('input/AUTOSAR_4-2-2.xsd'):
            missing_files.append("input/AUTOSAR_4-2-2.xsd")
        if not os.path.exists('input/AUTOSAR_XMI.xmi'):
            missing_files.append("input/AUTOSAR_XMI.xmi")

    # 确保输出目录存在
    if not os.path.exists('output'):
        os.makedirs('output')

    return missing_files


def main():
    print("AUTOSAR XSD和XMI处理流程")
    print("=" * 50)

    # 检查所需文件
    missing_files = check_files()
    if missing_files:
        print("错误: 缺少以下必要文件:")
        for file in missing_files:
            print(f"- {file}")
        print("\n请将缺失的文件放到正确位置后再运行此脚本")
        return

    print("所有必要的输入文件已找到，开始处理...")

    # 1. 运行XSD解析器
    if not run_script('xsd_parser.py', "解析XSD文件 (生成metadata.json)"):
        print("XSD解析失败，处理终止")
        return

    # 2. 运行XMI解析器
    if not run_script('xmi_parser.py', "解析XMI文件 (生成structure.json)"):
        print("XMI解析失败，处理终止")
        return

    # 3. 运行合并脚本
    if not run_script('merge_xmi_xsd.py', "合并数据 (生成merged.json)"):
        print("合并过程失败，处理终止")
        return

    print("\n整个处理流程已成功完成!")
    print("输出文件:")
    print("- uml_metadata_parser/output/metadata.json - XSD元数据")
    print("- uml_metadata_parser/output/structure.json - XMI结构信息")
    print("- uml_metadata_parser/output/merged.json - 合并后的完整数据")


if __name__ == "__main__":
    main()