#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SHACL形状图诊断脚本 - 独立版本 (增强诊断版)

功能：
1. 检查文件中是否有 b'...' 这类字节串残留污染 TTL。
2. 常规方式尝试一次性加载 RDF 图，给出错误行上下文。
3. 如果加载失败，启用“递增式按约束块加载”，
   按 autosar:XXX 约束块一个一个往图里加，定位第一个出问题的块。
4. 简单检查连续 sh:path 的结构问题。
"""

import rdflib
from pathlib import Path
import re
import sys


def diagnose_shacl_shapes(ttl_file_path: str):
    """诊断SHACL形状图中的常见问题"""
    print("=" * 80)
    print("🔍 SHACL形状图诊断工具 (增强版)")
    print("=" * 80)
    print()

    ttl_path = Path(ttl_file_path)

    if not ttl_path.exists():
        print(f"❌ 文件不存在: {ttl_path}")
        return

    print(f"📂 目标文件: {ttl_path.name}")
    print(f"📍 完整路径: {ttl_path.absolute()}")
    print()

    # 先把文件全部读入内存，后面多处复用
    try:
        with open(ttl_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        print("❌ 文件编码错误: 无法用UTF-8读取，文件可能包含二进制数据或使用了错误的编码。")
        return
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return

    # 步骤0: 检查字节串污染
    print("步骤0: 检查文件损坏/污染")
    print("-" * 80)
    check_byte_artifacts(lines)

    print("\n" + "=" * 80)

    # 步骤1: 一次性加载 RDF 图
    print("步骤1: RDF图加载测试")
    print("-" * 80)
    loaded_ok = check_rdf_graph(ttl_path, lines)

    # 只有在加载失败时，才启用递增式诊断
    if not loaded_ok:
        print("\n" + "=" * 80)
        print("步骤1.5: 递增式按约束块加载诊断")
        print("-" * 80)
        incremental_load_by_blocks(ttl_path, lines)

    print("\n" + "=" * 80)

    # 步骤2: 简单文本结构检查
    print("步骤2: sh:path 结构分析")
    print("-" * 80)
    check_ttl_structure(lines)


# ---------------------------------------------------------------------------
# 步骤0：检查字节串残留
# ---------------------------------------------------------------------------

def check_byte_artifacts(lines):
    """检查文件中是否残留了Python字节串表示 (如 b'...')"""
    print("🔍 正在扫描 Python 字节串残留 (b'...') ...")

    pattern = re.compile(r"(b'[^']*')|(b\"[^\"]*\")")

    found_count = 0
    for i, line in enumerate(lines):
        matches = pattern.findall(line)
        if matches:
            found_count += 1
            if found_count <= 5:  # 只显示前5个
                print(f"❌ [第 {i + 1} 行] 发现疑似字节串残留:")
                print(f"   原文: {line.strip()}")
                for match in matches:
                    m = match[0] if match[0] else match[1]
                    print(f"   可疑片段: {m}")

    if found_count > 0:
        print(f"\n📊 总结: 共发现 {found_count} 行包含疑似字节串残留 (b'...')。")
        print("💡 建议: 这通常是因为在生成文件时，使用了 str(bytes_data) 而不是 bytes_data.decode('utf-8')。")
        print("   这些字符破坏了Turtle语法，导致rdflib解析失败。")
    else:
        print("✅ 未发现明显的字节串残留。")


# ---------------------------------------------------------------------------
# 步骤1：常规 RDF 图加载
# ---------------------------------------------------------------------------

def check_rdf_graph(ttl_path: Path, lines):
    """方法1: 通过加载RDF图来检查，返回是否加载成功"""
    try:
        print("🔧 尝试使用 rdflib 一次性加载 TTL 文件...")

        g = rdflib.Graph()
        g.parse(str(ttl_path), format='turtle')

        print(f"✅ RDF图加载成功: {len(g)} 个三元组")
        # 如果加载成功，继续检查 path 重复问题
        check_shacl_paths_in_graph(g, ttl_path)
        return True

    except Exception as e:
        print(f"\n❌ RDF图加载失败!")
        error_msg = str(e)
        print(f"   错误信息: {error_msg}")

        # 尝试提取行号
        line_match = re.search(r'line (\d+)', error_msg)
        if line_match:
            line_num = int(line_match.group(1))
            print(f"\n🔍 定位到错误行: 第 {line_num} 行")
            print_file_context(ttl_path, line_num)
        else:
            print("   (无法从错误信息中提取具体行号)")

        return False


def print_file_context(file_path: Path, target_line: int, context=3):
    """打印文件指定行周围的内容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        start = max(0, target_line - 1 - context)
        end = min(len(lines), target_line + context)

        print(f"📄 文件内容上下文 (第 {start + 1} - {end} 行):")
        print("-" * 40)
        for i in range(start, end):
            current_line_num = i + 1
            marker = "👉" if current_line_num == target_line else "  "
            content = lines[i].rstrip()
            print(f"{marker} {current_line_num:5d} | {content}")
        print("-" * 40)
        print("💡 提示: 仔细观察上面标记为 👉 的行及其上一行结尾。")

    except Exception as e:
        print(f"无法读取文件上下文: {e}")


def check_shacl_paths_in_graph(g, ttl_path):
    """在已加载的图上检查 sh:path 重复"""
    SH = rdflib.Namespace("http://www.w3.org/ns/shacl#")
    property_shapes = list(g.subjects(rdflib.RDF.type, SH.PropertyShape))
    print(f"📊 找到 {len(property_shapes)} 个PropertyShape")

    problem_count = 0
    for shape in property_shapes:
        paths = list(g.objects(shape, SH.path))
        if len(paths) > 1:
            problem_count += 1
            print(f"\n❌ 发现逻辑问题 #{problem_count}:")
            print(f"   📍 Shape URI: {shape}")
            print(f"   🔢 sh:path数量: {len(paths)}")
            find_in_file(ttl_path, str(shape))

    if problem_count == 0:
        print("\n✅ 未在RDF图中发现重复sh:path")
    else:
        print(f"\n📊 总结: 发现 {problem_count} 个PropertyShape有重复的sh:path")


# ---------------------------------------------------------------------------
# 步骤1.5：递增式按“约束块”加载
# ---------------------------------------------------------------------------

def incremental_load_by_blocks(ttl_path: Path, lines):
    """
    按“约束块”（以 autosar:XXX 开头的块）递增加载，
    找出第一个导致 rdflib.parse 失败的块。
    """

    # 先拆分成 header + 若干块
    header_lines, blocks = split_into_blocks(lines)

    print(f"📄 header 行数: {len(header_lines)}")
    print(f"📦 检测到约束/形状块数量: {len(blocks)}")
    if not blocks:
        print("⚠️ 未检测到以 'autosar:' 开头的约束块，无法做块级诊断。")
        return

    header_text = "".join(header_lines)

    # 先只解析 header，确保前缀等没问题
    try:
        g = rdflib.Graph()
        g.parse(data=header_text, format='turtle')
        print("✅ header 部分解析成功。")
    except Exception as e:
        print("❌ 仅 header 部分解析就失败，说明出问题的内容在文件最前面。")
        print(f"   错误: {e}")
        return

    # 逐块追加
    accumulated_text = header_text
    for idx, (start_line, block_lines) in enumerate(blocks, start=1):
        block_text = "".join(block_lines)
        test_text = accumulated_text + block_text

        try:
            g = rdflib.Graph()
            g.parse(data=test_text, format='turtle')
            print(f"✅ 块 #{idx} (起始行 {start_line}) 解析成功，累计三元组: {len(g)}")
            accumulated_text = test_text  # 更新累计内容
        except Exception as e:
            print(f"\n❌ 在追加第 {idx} 个约束块时解析失败！")
            print(f"   起始行号: {start_line}")
            first_line = block_lines[0].lstrip()
            shape_head = first_line.strip() or "<空行>"
            print(f"   该块开头内容: {shape_head}")
            print(f"   rdflib 错误信息: {e}")

            # 打印该块的若干行，便于人工查看
            print("\n📄 疑似有问题的约束块内容（前 40 行）:")
            print("-" * 60)
            for offset, line in enumerate(block_lines[:40]):
                lineno = start_line + offset
                print(f"{lineno:5d} | {line.rstrip()}")
            print("-" * 60)
            print("💡 建议: 重点检查这个块内部的 sh:sparql / 字符串引号 / 末尾的 ';' 或 '.'。")

            # 再尝试用 rdflib 报错信息中给的行号打印上下文
            error_msg = str(e)
            line_match = re.search(r'line (\d+)', error_msg)
            if line_match:
                err_line = int(line_match.group(1))
                print("\n🔍 rdflib 报错行的上下文（基于整文件行号）:")
                print_file_context(ttl_path, err_line)

            break
    else:
        print("\n✅ 所有块递增解析都成功 —— 说明问题可能是别的原因（例如编码、隐藏字符等）。")


def split_into_blocks(lines):
    """
    将 TTL 文本拆分为：
    - header_lines: 第一段（通常是 @prefix、全局注释等）
    - blocks: 之后每个以 'autosar:' 开头的约束/形状块

    这里采用简单启发式：检测到以 'autosar:' 开头且不是注释/@prefix 的行，
    视为一个新块的起始。
    """
    header_lines = []
    blocks = []

    in_blocks = False
    current_block = []
    current_start_line = 0

    for idx, line in enumerate(lines):
        stripped = line.lstrip()

        # 判断是否是新的块起始：行以 autosar: 开头，且不是注释、不是@prefix
        is_block_start = (
            stripped.startswith("autosar:")
            and not stripped.startswith("@prefix")
            and not stripped.startswith("#")
        )

        if not in_blocks:
            if is_block_start:
                in_blocks = True
                current_block = [line]
                current_start_line = idx + 1  # 1-based
            else:
                header_lines.append(line)
        else:
            if is_block_start:
                # 结束上一块，开始新块
                blocks.append((current_start_line, current_block))
                current_block = [line]
                current_start_line = idx + 1
            else:
                current_block.append(line)

    # 收尾
    if in_blocks and current_block:
        blocks.append((current_start_line, current_block))

    return header_lines, blocks


# ---------------------------------------------------------------------------
# 步骤2：简单文本结构检查
# ---------------------------------------------------------------------------

def check_ttl_structure(lines):
    """检查连续的 sh:path 等简单结构问题"""
    print("🔍 检查连续出现的sh:path...")
    consecutive_found = []
    for i in range(len(lines) - 1):
        line1 = lines[i].strip()
        line2 = lines[i + 1].strip()
        if 'sh:path' in line1 and 'sh:path' in line2:
            if line1.endswith(';') or line1.endswith(','):
                consecutive_found.append((i + 1, i + 2, line1, line2))

    if consecutive_found:
        print(f"⚠️  找到 {len(consecutive_found)} 处连续的sh:path (可能是合并错误):")
        for item in consecutive_found[:5]:
            print(f"   行 {item[0]}-{item[1]}: {item[2]} <--> {item[3]}")
    else:
        print("   ✅ 未发现连续的sh:path")


def find_in_file(ttl_path: Path, search_text: str):
    """在文件中查找特定文本的位置 (保留原功能)"""
    try:
        local_name = search_text.split('#')[-1].split('/')[-1]
        with open(ttl_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        for i, line in enumerate(lines, 1):
            if local_name in line:
                print(f"   📂 位于第 {i} 行: {line.strip()}")
                break
    except Exception:
        pass


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    """主函数"""
    script_dir = Path(__file__).parent

    # 自动寻找文件
    ttl_candidates = [
        script_dir / "autosar_shapes.ttl",
        Path("autosar_shapes.ttl"),
        Path("src/validation/data/autosar_shapes.ttl"),
        Path("../src/validation/data/autosar_shapes.ttl"),
        # 你本地项目里的绝对路径（可根据需要修改）
        Path(r"C:\Users\54239\PycharmProjects\AI_XmlGenerator\src\validation\data\autosar_shapes.ttl"),
    ]

    ttl_file = None
    for candidate in ttl_candidates:
        if candidate.exists():
            ttl_file = candidate
            break

    if not ttl_file and len(sys.argv) > 1:
        ttl_file = Path(sys.argv[1])

    if not ttl_file:
        print("❌ 未找到autosar_shapes.ttl文件")
        print(f"搜索路径: {[str(p) for p in ttl_candidates]}")
        sys.exit(1)

    diagnose_shacl_shapes(str(ttl_file))


if __name__ == "__main__":
    main()
