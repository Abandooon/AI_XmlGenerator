#!/usr/bin/env python3
"""
测试 Round1 Designer 实际调用 Gemini API 的输出
"""
import json
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.llm_generation.core.round1_designer import round1_designer
from src.llm_generation.config import CONFIG


def test_round1_gemini_api():
    """测试 Round1 实际调用 Gemini API"""

    print("=" * 60)
    print("Round1 Designer - Gemini API 实际调用测试")
    print("=" * 60)

    # 测试用例1：简单的温度监控系统
    print("\n📋 测试用例：温度监控系统")
    print("-" * 40)

    user_requirements = """
    设计一个温度监控系统的AUTOSAR软件架构，包含以下功能：
    1. 从温度传感器读取数据
    2. 处理和分析温度数据
    3. 当温度超过阈值时触发告警
    4. 将温度数据发送给其他组件
    """

    try:
        print("\n🚀 正在调用 Gemini API 进行架构设计...")
        print(f"📡 API URL: {CONFIG.llm.llm_api_url}")
        print(f"🤖 Model: {CONFIG.llm.model_name}")
        print(f"🔧 Functions enabled: True")

        # 调用 Round1 Designer
        design, stats = round1_designer.design_architecture(
            user_requirements=user_requirements,
            design_context="这是一个车载温度监控系统",
            use_functions=True  # 启用函数调用
        )

        print("\n✅ Gemini API 调用成功！")
        print("\n📊 Token 使用统计:")
        print(f"  - 输入 Tokens: {stats['input_tokens']}")
        print(f"  - 输出 Tokens: {stats['output_tokens']}")
        print(f"  - 总计 Tokens: {stats['total_tokens']}")
        print(f"  - 函数调用次数: {stats['functions_called']}")

        # 显示架构设计结果
        print("\n🏗️ 架构设计结果:")
        print("=" * 60)

        # 1. 系统分析
        print("\n📌 系统分析:")
        print("-" * 40)
        system_analysis = design.system_analysis
        for key, value in system_analysis.items():
            print(f"\n【{key}】")
            print(f"  {value}")

        # 2. 组件规划
        print("\n\n📦 组件规划:")
        print("-" * 40)
        print(f"共设计 {len(design.component_plan)} 个组件：\n")

        for i, comp in enumerate(design.component_plan, 1):
            print(f"{i}. {comp.get('name', 'Unknown')}")
            print(f"   类型: {comp.get('type', 'Unknown')}")
            print(f"   用途: {comp.get('purpose', 'Unknown')}")
            print(f"   复杂度: {comp.get('estimated_complexity', 'Unknown')}")

            # 显示 element_design
            element_design = comp.get('element_design', {})
            if element_design:
                print(f"   元素设计:")
                ports = element_design.get('ports', {})
                print(f"     - 需要端口: {ports.get('needed', False)}")
                if ports.get('details'):
                    print(f"       {ports['details']}")

                behaviors = element_design.get('internal_behaviors', {})
                print(f"     - 需要行为: {behaviors.get('needed', False)}")
                if behaviors.get('runnables'):
                    print(f"       Runnables: {behaviors['runnables']}")
                if behaviors.get('events'):
                    print(f"       Events: {behaviors['events']}")
            print()

        # 3. 接口规划
        print("\n🔌 接口规划:")
        print("-" * 40)
        print(f"共设计 {len(design.interface_plan)} 个接口：\n")

        for i, intf in enumerate(design.interface_plan, 1):
            print(f"{i}. {intf.get('name', 'Unknown')}")
            print(f"   类型: {intf.get('type', 'Unknown')}")
            print(f"   通信模式: {intf.get('communication_pattern', 'Unknown')}")
            connected = intf.get('connected_components', [])
            if connected:
                print(f"   连接组件: {' <-> '.join(connected)}")
            print()

        # 4. 连接拓扑
        print("\n🔗 连接拓扑:")
        print("-" * 40)
        topology = design.connection_topology
        if topology.get('component_connections'):
            print(f"组件连接: {topology['component_connections']}")
        if topology.get('data_flow_paths'):
            print(f"数据流: {topology['data_flow_paths']}")

        # 5. 架构理由
        print("\n\n💡 架构设计理由:")
        print("-" * 40)
        rationale = design.architecture_rationale
        if rationale.get('design_decisions'):
            print(f"设计决策: {rationale['design_decisions']}")

        # 6. 函数调用详情（如果有）
        if stats.get('function_details'):
            print("\n\n🔧 函数调用详情:")
            print("-" * 40)
            for func_name, details in stats['function_details'].items():
                print(f"\n函数: {func_name}")
                print(f"  参数: {details.get('args', {})}")
                print(f"  结果: {details.get('result', {})}")

        # 保存完整输出到文件
        output_file = CONFIG.output_dir / "round1_gemini_output.json"
        output_data = {
            "requirements": user_requirements,
            "design": {
                "system_analysis": design.system_analysis,
                "component_plan": design.component_plan,
                "interface_plan": design.interface_plan,
                "connection_topology": design.connection_topology,
                "architecture_rationale": design.architecture_rationale
            },
            "stats": stats
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        print(f"\n\n💾 完整输出已保存到: {output_file}")

        return design, stats

    except Exception as e:
        print(f"\n❌ 调用 Gemini API 失败: {e}")
        if CONFIG.debug_mode:
            import traceback
            traceback.print_exc()
        return None, None


def test_with_functions():
    """测试函数调用功能"""

    print("\n\n" + "=" * 60)
    print("测试函数调用功能")
    print("=" * 60)

    user_requirements = """
    设计一个复杂的汽车电池管理系统(BMS)，需要：
    1. 监控多个电池单元的电压和温度
    2. 计算电池状态(SOC/SOH)
    3. 控制充放电过程
    4. 与车辆其他系统通信
    5. 故障诊断和保护
    """

    try:
        print("\n🚀 调用 Gemini API（启用函数）...")

        design, stats = round1_designer.design_architecture(
            user_requirements=user_requirements,
            design_context="这是一个电动汽车的电池管理系统",
            use_functions=True
        )

        if design:
            print(f"\n✅ 设计完成!")
            print(f"📊 生成了 {len(design.component_plan)} 个组件")
            print(f"🔌 生成了 {len(design.interface_plan)} 个接口")
            print(f"🔧 调用了 {stats.get('functions_called', 0)} 个函数")

            # 显示组件列表
            print("\n组件列表:")
            for comp in design.component_plan:
                print(f"  - {comp['name']} ({comp['type']})")

    except Exception as e:
        print(f"❌ 测试失败: {e}")


if __name__ == "__main__":
    # 确保输出目录存在
    CONFIG.output_dir.mkdir(exist_ok=True, parents=True)

    # 运行测试
    design, stats = test_round1_gemini_api()

    if design:
        print("\n\n🎉 测试完成！")

        # 可选：测试函数调用
        # test_with_functions()
    else:
        print("\n\n❌ 测试失败，请检查 API 配置和网络连接")