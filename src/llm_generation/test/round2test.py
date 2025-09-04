"""
生产级Round2 Schema生成测试
验证BMS系统的完整Schema生成
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.llm_generation.knowledge.dynamic_query_engine import query_engine
from src.llm_generation.config import CONFIG


def create_bms_component_plans() -> List[Dict[str, Any]]:
    """创建BMS系统的组件计划（模拟Round1输出）"""

    return [
        {
            "component_id": "comp_001",
            "name": "VoltageSensorHandler",
            "type": "SENSOR-ACTUATOR-SW-COMPONENT-TYPE",
            "element_design": {
                "ports": {"needed": True},
                "internal_behaviors": {"needed": True}
            }
        },
        {
            "component_id": "comp_002",
            "name": "CurrentSensorHandler",
            "type": "SENSOR-ACTUATOR-SW-COMPONENT-TYPE",
            "element_design": {
                "ports": {"needed": True},
                "internal_behaviors": {"needed": True}
            }
        },
        {
            "component_id": "comp_003",
            "name": "TemperatureSensorHandler",
            "type": "SENSOR-ACTUATOR-SW-COMPONENT-TYPE",
            "element_design": {
                "ports": {"needed": True},
                "internal_behaviors": {"needed": True}
            }
        },
        {
            "component_id": "comp_004",
            "name": "StateOfChargeEstimator",
            "type": "APPLICATION-SW-COMPONENT-TYPE",
            "element_design": {
                "ports": {"needed": True},
                "internal_behaviors": {"needed": True}
            }
        },
        {
            "component_id": "comp_005",
            "name": "FaultManager",
            "type": "APPLICATION-SW-COMPONENT-TYPE",
            "element_design": {
                "ports": {"needed": True},
                "internal_behaviors": {"needed": True}
            }
        },
        {
            "component_id": "comp_006",
            "name": "CellBalancingController",
            "type": "APPLICATION-SW-COMPONENT-TYPE",
            "element_design": {
                "ports": {"needed": True},
                "internal_behaviors": {"needed": True}
            }
        },
        {
            "component_id": "comp_007",
            "name": "BmsStateManager",
            "type": "COMPOSITION-SW-COMPONENT-TYPE",
            "element_design": {
                "ports": {"needed": True},
                "internal_behaviors": {"needed": False}
            }
        },
        {
            "component_id": "comp_008",
            "name": "BmsParameterManager",
            "type": "PARAMETER-SW-COMPONENT-TYPE",
            "element_design": {
                "ports": {"needed": True},
                "internal_behaviors": {"needed": False}
            }
        }
    ]


def test_bms_schema_generation():
    """测试完整BMS系统的Schema生成"""

    print("\n" + "=" * 60)
    print("BMS System Schema Generation Test")
    print("=" * 60)

    component_plans = create_bms_component_plans()

    print(f"\n📋 BMS组件架构:")
    print(f"  传感器组件: 3个")
    print(f"  应用组件: 3个")
    print(f"  组合组件: 1个")
    print(f"  参数组件: 1个")
    print(f"  总计: {len(component_plans)}个组件")

    try:
        print("\n🔄 生成完整BMS系统Schema...")

        # 生成Schema
        schema = query_engine.generate_multi_component_schema(component_plans)

        if schema and 'properties' in schema:
            print("\n✅ Schema生成成功!")

            # 统计分析
            type_stats = {}
            for comp in component_plans:
                comp_type = comp['type']
                if comp_type not in type_stats:
                    type_stats[comp_type] = []
                type_stats[comp_type].append(comp['name'])

            print("\n📊 组件类型分布:")
            for comp_type, comp_names in type_stats.items():
                print(f"  {comp_type}: {len(comp_names)}个")
                for name in comp_names:
                    if name in schema['properties']:
                        comp_schema = schema['properties'][name]
                        prop_count = len(comp_schema.get('properties', {}))
                        print(f"    - {name}: {prop_count}个属性")

            # 验证关键结构
            print("\n🔍 验证关键结构:")
            for comp_name in schema['properties']:
                comp_schema = schema['properties'][comp_name]
                if 'properties' in comp_schema:
                    props = comp_schema['properties']

                    # 检查必需元素
                    has_short_name = 'SHORT-NAME' in props
                    has_uuid = '@UUID' in props
                    has_ports = 'PORTS' in props
                    has_behaviors = 'INTERNAL-BEHAVIORS' in props

                    print(f"\n  {comp_name}:")
                    print(f"    ✓ SHORT-NAME: {'是' if has_short_name else '否'}")
                    print(f"    ✓ UUID: {'是' if has_uuid else '否'}")
                    print(f"    ✓ PORTS: {'是' if has_ports else '否'}")
                    print(f"    ✓ INTERNAL-BEHAVIORS: {'是' if has_behaviors else '否'}")

            # 保存结果
            output_file = Path("bms_schema_output.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(schema, f, indent=2, ensure_ascii=False)
            print(f"\n💾 完整Schema已保存到: {output_file}")

            return schema

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


def verify_schema_completeness(schema: Dict[str, Any]):
    """验证Schema的完整性"""

    print("\n" + "=" * 60)
    print("Schema Completeness Verification")
    print("=" * 60)

    issues = []
    warnings = []

    for comp_name, comp_schema in schema.get('properties', {}).items():
        if 'properties' not in comp_schema:
            issues.append(f"{comp_name}: 缺少properties字段")
            continue

        props = comp_schema['properties']

        # 必需检查
        if 'SHORT-NAME' not in props:
            issues.append(f"{comp_name}: 缺少SHORT-NAME")

        if '@UUID' not in props:
            warnings.append(f"{comp_name}: 缺少UUID属性")

        # 类型特定检查
        if 'PORTS' in props:
            ports_schema = props['PORTS']
            if 'properties' not in ports_schema:
                warnings.append(f"{comp_name}: PORTS结构不完整")

        if 'INTERNAL-BEHAVIORS' in props:
            behaviors_schema = props['INTERNAL-BEHAVIORS']
            if 'properties' not in behaviors_schema:
                warnings.append(f"{comp_name}: INTERNAL-BEHAVIORS结构不完整")

    # 输出结果
    if issues:
        print("\n❌ 严重问题:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\n✅ 无严重问题")

    if warnings:
        print("\n⚠️ 警告:")
        for warning in warnings:
            print(f"  - {warning}")
    else:
        print("\n✅ 无警告")

    return len(issues) == 0


if __name__ == "__main__":
    print("🚀 启动BMS系统Schema生成测试\n")

    # 启用调试模式
    CONFIG.debug_mode = False  # 减少输出噪音

    # 测试BMS系统Schema生成
    schema = test_bms_schema_generation()

    # 验证Schema完整性
    if schema:
        is_valid = verify_schema_completeness(schema)

        if is_valid:
            print("\n🎉 BMS系统Schema生成测试通过！")
        else:
            print("\n⚠️ Schema存在问题，需要进一步调试")

    print("\n✨ 测试完成!")