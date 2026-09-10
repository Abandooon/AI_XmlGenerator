#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hook pyshacl 内部 VALUES 检测逻辑，精确定位问题约束
"""

import re
import sys
from pathlib import Path

import pyshacl
import rdflib
from rdflib import Namespace

print(f"✅ pyshacl 版本: {pyshacl.__version__}")

SH = Namespace("http://www.w3.org/ns/shacl#")
AUTOSAR = Namespace("http://autosar.org/")


def find_values_in_sparql_queries(shapes_file: str):
    """
    直接用 pyshacl 相同的逻辑检测 VALUES 子句
    pyshacl 源码中的检测在: pyshacl/constraints/sparql/sparql_based_constraint_components.py
    """

    print("=" * 80)
    print("🔬 使用 pyshacl 相同的 VALUES 检测逻辑")
    print("=" * 80)

    # 加载 shapes
    shapes_graph = rdflib.Graph()
    shapes_graph.parse(shapes_file, format='turtle')
    print(f"✅ Shapes: {len(shapes_graph)} 三元组")

    # pyshacl 0.30.1 中检测 VALUES 的正则模式
    # 参考: https://github.com/RDFLib/pySHACL/blob/master/pyshacl/constraints/sparql/sparql_based_constraint_components.py
    # 在 SPARQLConstraintBase._validate 方法中

    # pyshacl 使用的模式（根据版本可能略有不同）
    # 它检测 SPARQL 查询字符串中是否包含 VALUES 关键字
    values_patterns = [
        # 标准 SPARQL VALUES 子句: VALUES ?var { ... }
        r'\bVALUES\s+\?',
        r'\bVALUES\s*\(',
        # 也可能是简单的包含检测
        r'\bVALUES\b',
    ]

    print("\n📋 扫描所有 sh:sparql 约束...")
    print("-" * 60)

    sparql_constraints = list(shapes_graph.subject_objects(SH.sparql))
    print(f"发现 {len(sparql_constraints)} 个 SPARQL 约束\n")

    found_issues = []

    for shape_uri, sparql_node in sparql_constraints:
        # 获取查询
        select_query = shapes_graph.value(sparql_node, SH.select)
        ask_query = shapes_graph.value(sparql_node, SH.ask)
        query = str(select_query) if select_query else (str(ask_query) if ask_query else None)

        if not query:
            continue

        # 用所有模式检测
        for pattern in values_patterns:
            matches = list(re.finditer(pattern, query, re.IGNORECASE))
            if matches:
                message = shapes_graph.value(sparql_node, SH.message)
                found_issues.append({
                    'shape_uri': str(shape_uri),
                    'message': str(message) if message else None,
                    'query': query,
                    'pattern': pattern,
                    'matches': [(m.start(), m.group()) for m in matches]
                })
                break  # 找到一个模式匹配就够了

    # 输出结果
    print("=" * 80)
    print("📋 检测结果")
    print("=" * 80)

    if found_issues:
        print(f"\n❌ 发现 {len(found_issues)} 个包含 'VALUES' 的约束:\n")

        for i, issue in enumerate(found_issues, 1):
            print(f"\n{'=' * 70}")
            print(f"❌ 问题 #{i}")
            print(f"{'=' * 70}")
            print(f"   Shape URI: {issue['shape_uri']}")
            if issue['message']:
                print(f"   消息: {issue['message']}")
            print(f"   匹配模式: {issue['pattern']}")
            print(f"   匹配位置: {issue['matches']}")

            print(f"\n   SPARQL 查询:")
            print("   " + "-" * 60)
            for line in issue['query'].split('\n'):
                # 高亮包含 VALUES 的行
                if re.search(r'\bVALUES\b', line, re.IGNORECASE):
                    print(f"   >>> {line}  ⚠️ <-- VALUES 在这里")
                else:
                    print(f"       {line}")
            print("   " + "-" * 60)
    else:
        print("\n✅ 未发现包含 VALUES 的约束")

    # 额外：检查 pyshacl 源码中的实际检测逻辑
    print("\n" + "=" * 80)
    print("🔍 检查 pyshacl 源码中的 VALUES 检测位置")
    print("=" * 80)

    try:
        import pyshacl.constraints.sparql.sparql_based_constraint_components as sparql_module
        source_file = sparql_module.__file__
        print(f"📂 源文件: {source_file}")

        with open(source_file, 'r', encoding='utf-8') as f:
            source_code = f.read()

        # 搜索 VALUES 相关的代码
        values_code_lines = []
        for i, line in enumerate(source_code.split('\n'), 1):
            if 'VALUES' in line:
                values_code_lines.append((i, line.strip()))

        if values_code_lines:
            print(f"\n找到 {len(values_code_lines)} 行包含 'VALUES' 的代码:")
            for line_num, line_content in values_code_lines:
                print(f"   行 {line_num}: {line_content[:100]}")

    except Exception as e:
        print(f"⚠️ 无法检查源码: {e}")

    return found_issues


def check_with_pyshacl_internal(shapes_file: str):
    """
    尝试使用 pyshacl 内部的 SPARQL 约束类来检测
    """
    print("\n" + "=" * 80)
    print("🔬 使用 pyshacl 内部类进行检测")
    print("=" * 80)

    try:
        from pyshacl.shape import Shape
        from pyshacl.shapes_graph import ShapesGraph

        # 加载 shapes
        shapes_graph = rdflib.Graph()
        shapes_graph.parse(shapes_file, format='turtle')

        # 创建 ShapesGraph 对象
        sg = ShapesGraph(shapes_graph, None)

        print(f"✅ ShapesGraph 创建成功")
        print(f"   shapes 数量: {len(list(sg.shapes))}")

        # 遍历所有 shapes，找出有 SPARQL 约束的
        for shape in sg.shapes:
            # 检查是否有 sparql 约束
            sparql_nodes = list(shapes_graph.objects(shape.node, SH.sparql))
            if sparql_nodes:
                print(f"\n   Shape: {shape.node}")
                print(f"   has {len(sparql_nodes)} SPARQL constraint(s)")

                for sn in sparql_nodes:
                    query = shapes_graph.value(sn, SH.select)
                    if query and 'VALUES' in str(query).upper():
                        print(f"   ⚠️ 包含 VALUES!")
                        print(f"   查询: {str(query)[:200]}...")

    except Exception as e:
        print(f"❌ 检测失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    # ========== 直接配置文件路径 ==========
    shapes_file = Path(r"C:\Users\54239\PycharmProjects\AI_XmlGenerator\src\validation\data\autosar_shapes.ttl")
    # ======================================

    if not shapes_file.exists():
        print(f"❌ shapes 文件不存在: {shapes_file}")
        sys.exit(1)

    print(f"📂 Shapes: {shapes_file}")

    # 方法1: 直接正则扫描
    issues = find_values_in_sparql_queries(str(shapes_file))

    # 方法2: 使用 pyshacl 内部类
    check_with_pyshacl_internal(str(shapes_file))

    # 总结
    print("\n" + "=" * 80)
    print("💡 诊断总结")
    print("=" * 80)

    if issues:
        print(f"\n发现 {len(issues)} 个约束包含 'VALUES' 关键字")
        print("pyshacl 可能误将属性名中的 VALUES（如 DATA-RECEIVE-POINT-BY-VALUES）")
        print("识别为 SPARQL VALUES 子句。")
        print("\n🔧 修复建议:")
        print("   在 SPARQL 查询中，将包含 'VALUES' 的属性名改为别名")
        print("   例如: autosar:DATA-RECEIVE-POINT-BY-VALUES → autosar:DRPBV")
    else:
        print("\n未发现问题，可能是 pyshacl 内部处理逻辑的问题")
        print("建议尝试降级 pyshacl: pip install pyshacl==0.20.0")


if __name__ == "__main__":
    main()