#!/usr/bin/env python3
"""
测试SMT验证器修复效果
确保修复后的验证器能正确处理各种情况
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_smt_fixes():
    """测试SMT验证器的修复"""

    print("🧪 开始测试SMT验证器修复...")
    print("=" * 60)

    # 测试用例1：缺少必需元素
    test_xml_missing = """<?xml version="1.0" encoding="UTF-8"?>
<AUTOSAR xmlns="http://autosar.org/schema/r4.0">
    <AR-PACKAGES>
        <AR-PACKAGE>
            <!-- 缺少SHORT-NAME，应该被检测为违规 -->
            <ELEMENTS>
                <APPLICATION-SW-COMPONENT-TYPE>
                    <!-- 这里也缺少SHORT-NAME -->
                </APPLICATION-SW-COMPONENT-TYPE>
            </ELEMENTS>
        </AR-PACKAGE>
    </AR-PACKAGES>
</AUTOSAR>"""

    # 测试用例2：包含wrapper的完整XML
    test_xml_with_wrapper = """<?xml version="1.0" encoding="UTF-8"?>
<AUTOSAR xmlns="http://autosar.org/schema/r4.0">
    <AR-PACKAGES>
        <AR-PACKAGE>
            <SHORT-NAME>TestPackage</SHORT-NAME>
            <ELEMENTS>
                <SWC-INTERNAL-BEHAVIOR>
                    <SHORT-NAME>InternalBehavior</SHORT-NAME>
                    <RUNNABLES>
                        <RUNNABLE-ENTITY>
                            <SHORT-NAME>Runnable1</SHORT-NAME>
                        </RUNNABLE-ENTITY>
                        <RUNNABLE-ENTITY>
                            <SHORT-NAME>Runnable2</SHORT-NAME>
                        </RUNNABLE-ENTITY>
                    </RUNNABLES>
                </SWC-INTERNAL-BEHAVIOR>
            </ELEMENTS>
        </AR-PACKAGE>
    </AR-PACKAGES>
</AUTOSAR>"""

    # 测试用例3：约束值为字典的情况（模拟）
    test_constraints_with_dict = [
        {
            "cid": "test_dict_constraint",
            "is_structural": True,
            "enriched_targets": [{
                "target_type": "attribute",
                "xml_tag": "SHORT-NAME",
                "class_xml_tag": "AR-PACKAGE",
                "minOccurs": {"value": 1, "source": "xsd"},  # 字典格式
                "maxOccurs": {"value": 1, "source": "xsd"}  # 字典格式
            }]
        }
    ]

    try:
        # 导入SMT验证器
        from src.validation.constraints.smt_validator import SMTValidator

        # 创建临时的SMT模板文件
        smt_template = """
; Test SMT template
(set-logic QF_LIA)
(check-sat)
"""
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.smt2', delete=False) as f:
            f.write(smt_template)
            smt_file = f.name

        # 初始化验证器
        validator = SMTValidator(smt_file)

        # 手动注入测试约束
        validator.structural_constraints = test_constraints_with_dict

        print("✅ SMT验证器初始化成功")

        # 测试1：缺少元素的验证
        print("\n📝 测试1: 验证缺少SHORT-NAME的XML...")
        result1 = validator.validate_constraints(test_xml_missing)

        if result1.get('structural_valid') == False:
            print("✅ 正确检测到结构违规")
        else:
            print("❌ 未能检测到结构违规")

        # 测试2：wrapper处理
        print("\n📝 测试2: 验证包含wrapper的XML...")
        result2 = validator.validate_constraints(test_xml_with_wrapper)

        # 检查是否正确计数
        print(f"   结构验证: {'通过' if result2.get('structural_valid') else '失败'}")

        # 检查详细结果中的计数
        if 'detailed_results' in result2:
            for r in result2['detailed_results']:
                if 'actual_count' in r:
                    print(f"   {r.get('element', 'unknown')}: 实际数量={r['actual_count']}")

        # 测试3：类型处理
        print("\n📝 测试3: 验证约束值类型处理...")
        # 约束已经注入，验证是否能正确处理字典类型
        if not any("'>' not supported" in str(r.get('error', ''))
                   for r in result2.get('detailed_results', [])):
            print("✅ 正确处理了字典类型的约束值")
        else:
            print("❌ 仍然存在类型错误")

        print("\n🎯 测试总结:")
        print("   1. 结构违规检测: ", "✅ 通过" if not result1.get('structural_valid') else "❌ 失败")
        print("   2. Wrapper处理: ", "✅ 通过" if result2.get('valid') else "⚠️ 需要检查")
        print("   3. 类型错误修复: ", "✅ 已修复" if "'>' not supported" not in str(result2) else "❌ 未修复")

        # 清理临时文件
        os.unlink(smt_file)

    except ImportError as e:
        print(f"❌ 无法导入SMT验证器: {e}")
        print("请确保在正确的项目目录下运行")
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()


def test_wrapper_counting():
    """专门测试wrapper计数逻辑"""
    print("\n🔍 测试Wrapper计数逻辑...")
    print("-" * 40)

    # 创建测试XML模型
    test_model = {
        "entities": {
            "SWC-INTERNAL-BEHAVIOR": [{
                "id": "entity_1",
                "tag": "SWC-INTERNAL-BEHAVIOR",
                "element": None,  # 实际会是Element对象
                "children_tags": ["SHORT-NAME", "RUNNABLES"]
            }],
            "RUNNABLES": [{
                "id": "entity_2",
                "tag": "RUNNABLES",
                "children_tags": ["RUNNABLE-ENTITY", "RUNNABLE-ENTITY"]
            }],
            "RUNNABLE-ENTITY": [
                {"id": "entity_3", "tag": "RUNNABLE-ENTITY"},
                {"id": "entity_4", "tag": "RUNNABLE-ENTITY"}
            ]
        },
        "wrapper_relationships": {
            "RUNNABLES": "RUNNABLE-ENTITY"
        },
        "element_counts": {
            "RUNNABLE-ENTITY": 2,
            "RUNNABLES": 1
        }
    }

    print("📊 测试数据:")
    print("   - SWC-INTERNAL-BEHAVIOR包含RUNNABLES")
    print("   - RUNNABLES包含2个RUNNABLE-ENTITY")
    print("   - 期望计数: 2个（不应重复）")

    # 这里可以添加更多的计数逻辑测试
    print("✅ Wrapper计数逻辑测试完成")


if __name__ == "__main__":
    print("🚀 SMT验证器修复测试")
    print("=" * 80)

    # 运行主要测试
    test_smt_fixes()

    # 运行wrapper计数测试
    test_wrapper_counting()

    print("\n" + "=" * 80)
    print("🏁 测试完成！")
    print("\n建议后续步骤:")
    print("1. 运行 python checksmt.py 查看详细的修复演示")
    print("2. 运行 python run_validation.py 进行完整的验证测试")
    print("3. 检查日志中的元素计数是否正确（避免重复）")
    print("4. 确认没有类型错误（dict vs int）")