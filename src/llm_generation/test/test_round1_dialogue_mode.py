#!/usr/bin/env python3
"""
test_round1_dialogue_mode.py - Round1纯对话模式测试

测试Round1设计器在纯对话模式下的功能
不依赖文件上传，直接在PyCharm中运行
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple
from unittest.mock import patch, Mock, MagicMock

# 添加项目路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.llm_generation.core.round1_designer import Round1Designer
from src.llm_generation.llm.gemini_client import GeminiClient
from src.llm_generation.utils.serializers import ArchitectureDesign


class Round1DialogueModeTester:
    """Round1纯对话模式测试器"""

    def __init__(self):
        self.test_output_dir = Path(__file__).parent / "test_output"
        self.test_output_dir.mkdir(exist_ok=True, parents=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.test_results = []

    def create_mock_response(self, component_count: int = 1) -> Dict[str, Any]:
        """创建模拟的架构设计响应"""

        # 基础响应结构
        response = {
            "system_analysis": {
                "functional_decomposition": f"系统包含{component_count}个核心组件",
                "data_flow_analysis": "输入->处理->输出的数据流",
                "timing_requirements": "10ms控制周期",
                "scalability_considerations": "支持模块化扩展",
                "architecture_patterns": ["分层架构", "模块化设计"]
            },
            "component_plan": [],
            "interface_plan": [],
            "connection_topology": {
                "component_connections": "",
                "data_flow_paths": "传感器->控制器->执行器",
                "control_flow_paths": "初始化->运行->关闭"
            },
            "architecture_rationale": {
                "design_decisions": "采用AUTOSAR标准架构",
                "tradeoff_analysis": "平衡性能与可维护性",
                "alternative_considerations": "考虑了多种架构方案",
                "risk_assessment": "低风险，成熟技术栈"
            }
        }

        # 根据数量生成组件
        for i in range(component_count):
            component = {
                "component_id": f"comp_{i + 1:03d}",
                "name": f"Component_{i + 1}",
                "type": "APPLICATION-SW-COMPONENT-TYPE",
                "purpose": f"功能组件{i + 1}",
                "estimated_complexity": ["Simple", "Medium", "Complex"][i % 3],
                "port_estimates": {
                    "input_ports": f"{i + 1}个输入端口",
                    "output_ports": f"{i + 1}个输出端口"
                },
                "behavioral_characteristics": f"执行功能{i + 1}的处理逻辑",
                "element_design": {
                    "ports": {
                        "needed": True,
                        "details": f"包含{i + 2}个端口定义"
                    },
                    "internal_behaviors": {
                        "needed": True,
                        "runnables": [f"Runnable_{j}" for j in range(i + 1)],
                        "events": ["TIMING-EVENT"]
                    }
                }
            }
            response["component_plan"].append(component)

            # 生成对应的接口
            interface = {
                "interface_id": f"intf_{i + 1:03d}",
                "name": f"Interface_{i + 1}",
                "type": "SENDER-RECEIVER-INTERFACE",
                "communication_pattern": "异步通信",
                "data_category": "控制数据",
                "connected_components": [f"comp_{i + 1:03d}"],
                "performance_requirements": "低延迟"
            }
            response["interface_plan"].append(interface)

        return response

    def test_simple_dialogue(self):
        """测试简单的纯对话场景"""

        print("\n" + "=" * 60)
        print("🔹 测试1：简单对话设计（单组件）")
        print("=" * 60)

        # 准备模拟响应
        mock_response = self.create_mock_response(component_count=1)

        with patch.object(GeminiClient, 'generate_with_schema') as mock_gen:
            mock_gen.return_value = (mock_response, 500, 1000, 1500)

            try:
                designer = Round1Designer()

                # 纯对话输入
                user_input = """
                设计一个简单的温度监控组件：
                - 读取温度传感器数据
                - 进行阈值判断
                - 输出控制信号
                """

                print(f"\n用户输入：{user_input[:100]}...")

                # 执行设计（纯对话模式，无文档）
                design, stats = designer.design_architecture(
                    user_requirements=user_input
                )

                print(f"\n✅ 设计结果：")
                print(f"  组件数：{stats['component_count']}")
                print(f"  接口数：{stats['interface_count']}")
                print(f"  Token：{stats['total_tokens']}")

                # 验证结果
                assert stats['component_count'] == 1
                assert stats['interface_count'] == 1
                assert len(design.component_plan) == 1

                self.test_results.append({
                    "test": "简单对话设计",
                    "status": "PASS",
                    "components": stats['component_count'],
                    "tokens": stats['total_tokens']
                })

                return design, stats

            except Exception as e:
                print(f"❌ 测试失败：{e}")
                self.test_results.append({
                    "test": "简单对话设计",
                    "status": "FAIL",
                    "error": str(e)
                })
                raise

    def test_complex_dialogue(self):
        """测试复杂的纯对话场景（多组件）"""

        print("\n" + "=" * 60)
        print("🔹 测试2：复杂对话设计（多组件系统）")
        print("=" * 60)

        # 准备复杂响应
        mock_response = self.create_mock_response(component_count=5)

        with patch.object(GeminiClient, 'generate_with_schema') as mock_gen:
            mock_gen.return_value = (mock_response, 1000, 2000, 3000)

            try:
                designer = Round1Designer()

                # 复杂需求描述
                user_input = """
                设计一个完整的电机控制系统，包括以下组件：

                1. 传感器组件：
                   - 温度传感器组件
                   - 速度传感器组件

                2. 控制组件：
                   - PID控制器组件
                   - 状态管理组件

                3. 执行器组件：
                   - PWM输出组件

                要求：
                - 所有组件通过AUTOSAR标准接口通信
                - 支持故障诊断
                - 满足功能安全要求
                """

                print(f"\n用户输入（复杂需求）：")
                print(user_input[:200] + "...")

                # 执行设计
                design, stats = designer.design_architecture(
                    user_requirements=user_input
                )

                print(f"\n✅ 设计结果：")
                print(f"  组件数：{stats['component_count']}")
                print(f"  接口数：{stats['interface_count']}")
                print(f"  Token：{stats['total_tokens']}")

                # 显示组件列表
                print("\n📦 生成的组件：")
                for comp in design.component_plan:
                    print(f"  • {comp['name']}: {comp['purpose']}")
                    print(f"    复杂度: {comp.get('estimated_complexity', 'N/A')}")

                # 验证结果
                assert stats['component_count'] == 5
                assert stats['interface_count'] == 5

                self.test_results.append({
                    "test": "复杂对话设计",
                    "status": "PASS",
                    "components": stats['component_count'],
                    "tokens": stats['total_tokens']
                })

                return design, stats

            except Exception as e:
                print(f"❌ 测试失败：{e}")
                self.test_results.append({
                    "test": "复杂对话设计",
                    "status": "FAIL",
                    "error": str(e)
                })
                raise

    def test_dialogue_with_context(self):
        """测试带上下文信息的对话"""

        print("\n" + "=" * 60)
        print("🔹 测试3：带上下文的对话设计")
        print("=" * 60)

        mock_response = self.create_mock_response(component_count=3)

        with patch.object(GeminiClient, 'generate_with_schema') as mock_gen:
            mock_gen.return_value = (mock_response, 800, 1600, 2400)

            try:
                designer = Round1Designer()

                # 主需求
                user_input = "设计一个电池管理系统BMS"

                # 设计上下文
                design_context = """
                这是一个电动汽车项目的一部分：
                - 需要监控48个电池单元
                - 支持CAN通信
                - 符合ISO 26262 ASIL-C要求
                """

                # 记忆上下文（之前的设计）
                memory_context = """
                之前已经设计了：
                - 电机控制器组件
                - 整车控制器接口
                需要与这些组件协同工作
                """

                print(f"\n用户输入：{user_input}")
                print(f"设计上下文：{design_context[:100]}...")
                print(f"记忆上下文：{memory_context[:100]}...")

                # 执行设计（带上下文）
                design, stats = designer.design_architecture(
                    user_requirements=user_input,
                    design_context=design_context,
                    memory_context=memory_context
                )

                print(f"\n✅ 设计结果：")
                print(f"  组件数：{stats['component_count']}")
                print(f"  接口数：{stats['interface_count']}")
                print(f"  Token：{stats['total_tokens']}")

                self.test_results.append({
                    "test": "带上下文对话",
                    "status": "PASS",
                    "components": stats['component_count'],
                    "tokens": stats['total_tokens']
                })

                return design, stats

            except Exception as e:
                print(f"❌ 测试失败：{e}")
                self.test_results.append({
                    "test": "带上下文对话",
                    "status": "FAIL",
                    "error": str(e)
                })
                raise

    def test_dialogue_with_text_document(self):
        """测试带文档文本的对话（不是文件上传）"""

        print("\n" + "=" * 60)
        print("🔹 测试4：带文档文本的对话设计")
        print("=" * 60)

        # 模拟从论文提取的文本
        document_text = """
        基于AUTOSAR的底盘域控制器设计要求：

        1. 应用层组件：
           - IOP Block: 输入处理组件，接收车辆消息
           - Estimate Block: 状态估计组件，包括质量估计、路面坡度估计
           - ABS Block: 防抱死制动系统
           - ASR Block: 驱动防滑系统
           - AYC Block: 主动横摆控制
           - RSC Block: 防侧翻稳定控制
           - Arbitration Block: 仲裁模块
           - OUP Block: 输出处理组件

        2. 接口要求：
           - 使用SENDER-RECEIVER接口进行数据传输
           - 使用CLIENT-SERVER接口进行服务调用

        3. 时序要求：
           - 控制周期: 10ms
           - 传感器采样: 1ms
        """

        mock_response = self.create_mock_response(component_count=8)

        with patch.object(GeminiClient, 'generate_with_schema') as mock_gen:
            # 模拟处理文档文本
            mock_gen.return_value = (mock_response, 2000, 4000, 6000)

            try:
                designer = Round1Designer()

                user_input = "基于提供的文档文本，设计底盘域控制器架构"

                print(f"\n用户输入：{user_input}")
                print(f"文档文本（摘要）：")
                print(document_text[:300] + "...")

                # 执行设计（使用文档文本而非文件）
                # 注意：这里需要修改Round1Designer以支持document_text参数
                with patch.object(GeminiClient, 'generate_with_schema') as mock_gen_inner:
                    # 设置mock返回，包含context_info参数
                    def mock_generate(*args, **kwargs):
                        # 检查是否传入了context_info（包含文档文本）
                        if 'context_info' in kwargs and document_text in str(kwargs.get('context_info', '')):
                            return (mock_response, 2000, 4000, 6000)
                        return (mock_response, 1000, 2000, 3000)

                    mock_gen_inner.side_effect = mock_generate

                    # 通过design_context传递文档文本
                    design, stats = designer.design_architecture(
                        user_requirements=user_input,
                        design_context=f"参考文档内容：\n{document_text}"
                    )

                print(f"\n✅ 设计结果：")
                print(f"  组件数：{stats['component_count']}")
                print(f"  接口数：{stats['interface_count']}")
                print(f"  Token：{stats['total_tokens']}")

                # 显示提取的组件
                print("\n📦 基于文档生成的组件：")
                for i, comp in enumerate(design.component_plan[:5], 1):
                    print(f"  {i}. {comp['name']}: {comp['purpose']}")

                self.test_results.append({
                    "test": "文档文本对话",
                    "status": "PASS",
                    "components": stats['component_count'],
                    "tokens": stats['total_tokens']
                })

                return design, stats

            except Exception as e:
                print(f"❌ 测试失败：{e}")
                self.test_results.append({
                    "test": "文档文本对话",
                    "status": "FAIL",
                    "error": str(e)
                })
                raise

    def test_real_api_call(self):
        """测试真实API调用（可选）"""

        print("\n" + "=" * 60)
        print("🔹 测试5：真实API调用测试")
        print("=" * 60)

        try:
            # 检查是否可以进行真实调用
            client = GeminiClient()

            if not client.test_connection():
                print("⚠️ 跳过真实API测试（连接失败）")
                self.test_results.append({
                    "test": "真实API调用",
                    "status": "SKIP",
                    "reason": "API连接失败"
                })
                return None, None

            print("✅ API连接成功，执行真实调用...")

            designer = Round1Designer()

            # 简单的测试需求
            user_input = "设计一个简单的LED控制组件，包含开关控制和亮度调节功能"

            print(f"\n用户输入：{user_input}")

            start_time = time.time()

            # 执行真实设计
            design, stats = designer.design_architecture(
                user_requirements=user_input
            )

            elapsed_time = time.time() - start_time

            print(f"\n✅ 真实API调用成功：")
            print(f"  响应时间：{elapsed_time:.2f}秒")
            print(f"  组件数：{stats['component_count']}")
            print(f"  接口数：{stats['interface_count']}")
            print(f"  输入Token：{stats.get('input_tokens', 0)}")
            print(f"  输出Token：{stats.get('output_tokens', 0)}")
            print(f"  总Token：{stats['total_tokens']}")

            # 保存真实响应
            output_file = self.test_output_dir / f"real_api_response_{self.timestamp}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "request": user_input,
                    "response": {
                        "system_analysis": design.system_analysis,
                        "component_plan": design.component_plan,
                        "interface_plan": design.interface_plan
                    },
                    "stats": stats,
                    "elapsed_time": elapsed_time
                }, f, indent=2, ensure_ascii=False)

            print(f"\n💾 响应已保存：{output_file.name}")

            self.test_results.append({
                "test": "真实API调用",
                "status": "PASS",
                "components": stats['component_count'],
                "tokens": stats['total_tokens'],
                "time": f"{elapsed_time:.2f}s"
            })

            return design, stats

        except Exception as e:
            print(f"❌ 真实API调用失败：{e}")
            self.test_results.append({
                "test": "真实API调用",
                "status": "FAIL",
                "error": str(e)
            })
            return None, None

    def generate_report(self):
        """生成测试报告"""

        print("\n" + "=" * 60)
        print("📊 测试报告")
        print("=" * 60)

        # 统计
        total_tests = len(self.test_results)
        passed = sum(1 for r in self.test_results if r['status'] == 'PASS')
        failed = sum(1 for r in self.test_results if r['status'] == 'FAIL')
        skipped = sum(1 for r in self.test_results if r['status'] == 'SKIP')

        print(f"\n测试统计：")
        print(f"  总计：{total_tests}")
        print(f"  通过：{passed} ✅")
        print(f"  失败：{failed} ❌")
        print(f"  跳过：{skipped} ⚠️")
        print(f"  通过率：{passed / total_tests * 100:.1f}%")

        print(f"\n详细结果：")
        for result in self.test_results:
            status_icon = {"PASS": "✅", "FAIL": "❌", "SKIP": "⚠️"}.get(result['status'], "❓")
            print(f"\n  {status_icon} {result['test']}:")
            print(f"     状态: {result['status']}")

            if 'components' in result:
                print(f"     组件数: {result['components']}")
            if 'tokens' in result:
                print(f"     Token: {result['tokens']}")
            if 'time' in result:
                print(f"     耗时: {result['time']}")
            if 'error' in result:
                print(f"     错误: {result['error']}")
            if 'reason' in result:
                print(f"     原因: {result['reason']}")

        # 保存报告
        report_file = self.test_output_dir / f"test_report_{self.timestamp}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": self.timestamp,
                "mode": "dialogue_only",
                "statistics": {
                    "total": total_tests,
                    "passed": passed,
                    "failed": failed,
                    "skipped": skipped,
                    "pass_rate": f"{passed / total_tests * 100:.1f}%"
                },
                "results": self.test_results
            }, f, indent=2, ensure_ascii=False)

        print(f"\n💾 报告已保存：{report_file.name}")

    def run_all_tests(self):
        """运行所有测试"""

        print("\n" + "🚀" * 20)
        print("     Round1 纯对话模式测试套件")
        print("       无需文件上传功能")
        print("🚀" * 20)

        # 检查配置
        try:
            from src.llm_generation.config import CONFIG
            file_upload = getattr(CONFIG.llm, 'enable_file_upload', False)
            print(f"\n当前配置：")
            print(f"  文件上传: {'启用' if file_upload else '禁用'}")
            print(f"  API端点: {CONFIG.llm.llm_api_url}")
            print(f"  模型: {CONFIG.llm.model_name}")
        except Exception as e:
            print(f"配置读取失败: {e}")

        print("\n开始测试...")
        time.sleep(1)

        # 运行测试
        tests = [
            ("简单对话", self.test_simple_dialogue),
            ("复杂对话", self.test_complex_dialogue),
            ("带上下文", self.test_dialogue_with_context),
            ("文档文本", self.test_dialogue_with_text_document),
            ("真实API", self.test_real_api_call)
        ]

        for test_name, test_func in tests:
            try:
                test_func()
            except Exception as e:
                print(f"\n测试 {test_name} 异常: {e}")

        # 生成报告
        self.generate_report()

        print("\n" + "=" * 60)
        print("✅ 测试完成！")
        print("=" * 60)


def main():
    """主函数 - PyCharm直接运行"""

    tester = Round1DialogueModeTester()
    tester.run_all_tests()

    return 0


if __name__ == "__main__":
    exit(main())