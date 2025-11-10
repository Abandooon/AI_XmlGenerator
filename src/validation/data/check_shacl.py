#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SHACL形状图诊断脚本 - 独立版本
专门诊断 "more than one 'sh:path'" 错误
直接在PyCharm中右键运行
"""

import rdflib
from pathlib import Path
import re
import sys


def diagnose_shacl_shapes(ttl_file_path: str):
    """诊断SHACL形状图中的重复sh:path问题"""

    print("=" * 80)
    print("🔍 SHACL形状图诊断工具")
    print("=" * 80)
    print()

    ttl_path = Path(ttl_file_path)

    if not ttl_path.exists():
        print(f"❌ 文件不存在: {ttl_path}")
        return

    print(f"📂 目标文件: {ttl_path.name}")
    print(f"📍 完整路径: {ttl_path.absolute()}")
    print()

    # 方法1: 尝试加载RDF图并检查
    print("方法1: RDF图分析")
    print("-" * 80)
    check_rdf_graph(ttl_path)

    print("\n" + "=" * 80)

    # 方法2: 直接分析TTL文件文本
    print("方法2: TTL文本分析")
    print("-" * 80)
    check_ttl_text(ttl_path)


def check_rdf_graph(ttl_path: Path):
    """方法1: 通过加载RDF图来检查"""
    try:
        print("🔧 尝试加载SHACL形状图...")

        g = rdflib.Graph()
        g.parse(str(ttl_path), format='turtle')

        print(f"✅ RDF图加载成功: {len(g)} 个三元组")

        SH = rdflib.Namespace("http://www.w3.org/ns/shacl#")

        # 查找所有PropertyShape
        property_shapes = list(g.subjects(rdflib.RDF.type, SH.PropertyShape))
        print(f"📊 找到 {len(property_shapes)} 个PropertyShape")

        # 检查每个PropertyShape的sh:path数量
        problem_count = 0
        for shape in property_shapes:
            paths = list(g.objects(shape, SH.path))

            if len(paths) > 1:
                problem_count += 1
                print(f"\n❌ 发现问题 #{problem_count}:")
                print(f"   📍 Shape URI: {shape}")
                print(f"   🔢 sh:path数量: {len(paths)} (应该只有1个)")
                print(f"   📋 路径列表:")
                for i, path in enumerate(paths, 1):
                    print(f"      {i}. {path}")

                # 查找所属的NodeShape
                print(f"   🔍 查找上下文...")
                for node_shape in g.subjects(SH.property, shape):
                    print(f"   🏷️  所属NodeShape: {node_shape}")

                    # 获取targetClass
                    target_classes = list(g.objects(node_shape, SH.targetClass))
                    if target_classes:
                        print(f"   🎯 targetClass: {target_classes[0]}")

                    # 获取message
                    messages = list(g.objects(node_shape, SH.message))
                    if messages:
                        msg = str(messages[0])
                        if len(msg) > 100:
                            msg = msg[:100] + "..."
                        print(f"   💬 message: {msg}")

                # 在文件中查找位置
                find_in_file(ttl_path, str(shape))

        if problem_count == 0:
            print("\n✅ 未在RDF图中发现重复sh:path")
            print("💡 但pyshacl可能在验证阶段检测到问题...")
        else:
            print(f"\n📊 总结: 发现 {problem_count} 个PropertyShape有重复的sh:path")

    except Exception as e:
        print(f"❌ RDF图加载失败: {e}")
        print("💡 错误可能在TTL文件的语法中，继续用方法2分析...")


def check_ttl_text(ttl_path: Path):
    """方法2: 直接分析TTL文本"""
    try:
        with open(ttl_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        print(f"📄 文件总行数: {len(lines)}")
        print()

        # 策略1: 查找连续的sh:path行
        print("🔍 策略1: 查找连续的sh:path...")
        check_consecutive_paths(lines)

        print("\n" + "-" * 80)

        # 策略2: 分析PropertyShape块
        print("🔍 策略2: 分析PropertyShape块...")
        check_property_shape_blocks(lines)

        print("\n" + "-" * 80)

        # 策略3: 正则表达式搜索
        print("🔍 策略3: 正则表达式搜索...")
        check_with_regex(lines)

    except Exception as e:
        print(f"❌ 文本分析失败: {e}")
        import traceback
        traceback.print_exc()


def check_consecutive_paths(lines):
    """检查连续出现的sh:path"""
    consecutive_found = []

    for i in range(len(lines) - 1):
        line1 = lines[i].strip()
        line2 = lines[i + 1].strip()

        if 'sh:path' in line1 and 'sh:path' in line2:
            # 检查是否在同一个PropertyShape块中
            # 简单判断: 如果第一行以分号结尾，可能有问题
            if line1.endswith(';') or line1.endswith(','):
                consecutive_found.append({
                    'line1_num': i + 1,
                    'line2_num': i + 2,
                    'line1': line1,
                    'line2': line2
                })

    if consecutive_found:
        print(f"⚠️  找到 {len(consecutive_found)} 处连续的sh:path:")

        for j, item in enumerate(consecutive_found, 1):
            print(f"\n   {j}. 第 {item['line1_num']}-{item['line2_num']} 行:")
            print(f"      {item['line1_num']:4d}: {item['line1']}")
            print(f"      {item['line2_num']:4d}: {item['line2']}")
    else:
        print("   ✅ 未发现连续的sh:path")


def check_property_shape_blocks(lines):
    """分析PropertyShape块"""
    problems = []

    i = 0
    while i < len(lines):
        line = lines[i]

        # 查找PropertyShape块的开始
        if 'sh:property' in line and '[' in line:
            block_start = i
            block_lines = []
            bracket_count = line.count('[') - line.count(']')

            # 收集整个块
            while i < len(lines) and bracket_count > 0:
                block_lines.append(lines[i])
                i += 1
                if i < len(lines):
                    bracket_count += lines[i].count('[')
                    bracket_count -= lines[i].count(']')

            # 分析这个块
            block_text = ''.join(block_lines)

            # 简单分割: 用逗号分隔的独立PropertyShape
            sub_shapes = re.split(r'\]\s*,\s*\[', block_text)

            for sub_shape in sub_shapes:
                path_count = sub_shape.count('sh:path')
                if path_count > 1:
                    problems.append({
                        'start_line': block_start + 1,
                        'path_count': path_count,
                        'preview': sub_shape[:200]
                    })
        else:
            i += 1

    if problems:
        print(f"❌ 找到 {len(problems)} 个有问题的PropertyShape块:")

        for j, prob in enumerate(problems, 1):
            print(f"\n   {j}. 大约在第 {prob['start_line']} 行:")
            print(f"      sh:path数量: {prob['path_count']}")
            print(f"      内容预览:")
            for line in prob['preview'].split('\n')[:5]:
                if 'sh:path' in line:
                    print(f"         >>> {line.strip()}")
                else:
                    print(f"             {line.strip()}")
    else:
        print("   ✅ 未发现明显的问题块")


def check_with_regex(lines):
    """使用正则表达式搜索"""
    content = ''.join(lines)

    # 模式: 在方括号内有多个sh:path
    pattern = r'\[[^\[\]]*?sh:path[^\[\];]*;[^\[\]]*?sh:path[^\[\]]*?\]'

    matches = list(re.finditer(pattern, content, re.DOTALL))

    if matches:
        print(f"❌ 正则表达式找到 {len(matches)} 个可疑块:")

        for i, match in enumerate(matches[:5], 1):  # 只显示前5个
            line_num = content[:match.start()].count('\n') + 1
            matched_text = match.group(0)

            print(f"\n   {i}. 大约在第 {line_num} 行:")

            # 提取sh:path行
            path_lines = [line for line in matched_text.split('\n') if 'sh:path' in line]
            print(f"      发现 {len(path_lines)} 个sh:path:")
            for path_line in path_lines[:3]:
                print(f"         >>> {path_line.strip()}")

            if len(path_lines) > 3:
                print(f"         ... 还有 {len(path_lines) - 3} 个")

        if len(matches) > 5:
            print(f"\n   ... 还有 {len(matches) - 5} 个匹配")
    else:
        print("   ✅ 正则表达式未找到明显问题")


def find_in_file(ttl_path: Path, search_text: str):
    """在文件中查找特定文本的位置"""
    try:
        # 提取URI的本地名称
        local_name = search_text.split('#')[-1].split('/')[-1]

        with open(ttl_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for i, line in enumerate(lines, 1):
            if local_name in line:
                print(f"   📂 TTL文件中的位置:")
                print(f"      第 {i} 行: {line.strip()}")

                # 显示上下文
                start = max(0, i - 2)
                end = min(len(lines), i + 2)
                print(f"      上下文 (第 {start + 1}-{end} 行):")
                for j in range(start, end):
                    marker = "   >>> " if j == i - 1 else "       "
                    print(f"{marker}{j + 1:4d}: {lines[j].rstrip()}")
                break

    except Exception as e:
        print(f"   ⚠️  无法定位: {e}")


def main():
    """主函数"""
    # 获取脚本所在目录
    script_dir = Path(__file__).parent

    # 查找TTL文件
    ttl_candidates = [
        script_dir / "autosar_shapes.ttl",
        Path("autosar_shapes.ttl"),
        Path("src/validation/data/autosar_shapes.ttl"),
        Path("../src/validation/data/autosar_shapes.ttl"),
    ]

    ttl_file = None
    for candidate in ttl_candidates:
        if candidate.exists():
            ttl_file = candidate
            break

    if not ttl_file:
        print("❌ 未找到autosar_shapes.ttl文件")
        print("\n请将此脚本放在以下任一位置:")
        for path in ttl_candidates:
            print(f"  • {path}")
        print("\n或者手动指定文件路径:")
        print(f"  python {Path(__file__).name} <ttl_file_path>")
        sys.exit(1)

    # 如果命令行提供了参数，使用参数
    if len(sys.argv) > 1:
        ttl_file = Path(sys.argv[1])

    diagnose_shacl_shapes(str(ttl_file))


if __name__ == "__main__":
    main()