#!/usr/bin/env python3
"""llm_rag_generator.py - LLM RAG AUTOSAR组件生成器主程序

基于对话式逐层深入设计系统的AUTOSAR组件生成器
支持两轮对话：Round1架构设计 + Round2详细生成
支持多组件生成，动态Schema生成，支持文档上传

使用方法:
1. 直接运行: python llm_rag_generator.py
2. PyCharm右键运行
3. 交互式对话生成AUTOSAR ARXML
4. 支持上传PDF/Word/图片文档作为需求输入
"""

import os
import sys
import json
import traceback
from pathlib import Path
from typing import Dict, Any, Optional, List

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from src.llm_generation.config import CONFIG, load_config
    from src.llm_generation.core.conversation_manager import conversation_manager
    from src.llm_generation.utils.exceptions import (
        LLMGenerationException, ConversationError,
        ArchitectureDesignError, ValidationError
    )
    from src.llm_generation.utils.serializers import save_json
    from src.llm_generation.utils.document_processor import document_processor
except ImportError as e:
    print(f"❌ 导入模块失败: {e}")
    print("请确保项目结构正确且所有依赖已安装")
    sys.exit(1)


class LLMRAGGenerator:
    """LLM RAG生成器主类"""

    def __init__(self):
        """初始化生成器"""
        self.conversation_manager = conversation_manager
        self.document_processor = document_processor
        self.current_session_id = None
        self.demo_mode = False
        self.uploaded_documents = []  # 当前会话上传的文档

        print("🚀 LLM RAG AUTOSAR组件生成器")
        print("=" * 50)
        print(f"📊 配置信息:")
        print(f"  - LLM模型: {CONFIG.llm.model_name}")
        print(f"  - 调试模式: {'开启' if CONFIG.debug_mode else '关闭'}")
        print(f"  - 输出目录: {CONFIG.output_dir}")
        print(f"  - KG连接: {'Neo4j' if CONFIG.knowledge_graph.neo4j_uri else '模拟数据'}")
        print("=" * 50)

    def run_interactive_session(self):
        """运行交互式会话"""

        print("\n🎯 欢迎使用AUTOSAR组件设计助手!")
        print("我将通过两轮对话帮您设计AUTOSAR软件组件：")
        print("  Round 1: 架构设计 - 确定组件类型、接口、连接关系")
        print("  Round 2: 详细生成 - 从KG查询详细信息并生成完整ARXML")
        print("\n✨ 新特性:")
        print("  - 支持上传PDF/Word/图片文档作为需求输入")
        print("  - 支持多组件设计和生成")
        print("  - 动态从KG查询XML结构生成Schema")
        print("  - 确保实例引用的唯一性和一致性")
        print("\n📁 支持的文档格式:")
        print("  PDF, Word(.doc/.docx), 文本(.txt/.md), 图片(.png/.jpg/.jpeg/.gif/.webp)")
        print("\n输入 'quit' 或 'exit' 可随时退出")
        print("输入 'demo' 可运行演示模式")
        print("输入 'help' 查看帮助信息")
        print("输入 'upload' 上传文档文件")

        while True:
            try:
                print("\n" + "-" * 50)
                user_input = input("\n💬 请描述您要设计的AUTOSAR组件需求 (或输入'upload'上传文档): ").strip()

                if not user_input:
                    continue

                # 处理特殊命令
                if user_input.lower() in ['quit', 'exit', 'q']:
                    self._handle_quit()
                    break
                elif user_input.lower() == 'demo':
                    self._run_demo_mode()
                    continue
                elif user_input.lower() == 'help':
                    self._show_help()
                    continue
                elif user_input.lower() == 'stats':
                    self._show_stats()
                    continue
                elif user_input.lower() == 'upload':
                    self._handle_document_upload()
                    continue
                elif user_input.lower() == 'clear':
                    self._clear_documents()
                    continue

                # 开始新的对话会话
                self._start_new_conversation(user_input)

            except KeyboardInterrupt:
                print("\n\n⚠️ 用户中断，正在退出...")
                self._handle_quit()
                break
            except Exception as e:
                print(f"\n❌ 发生错误: {e}")
                if CONFIG.debug_mode:
                    traceback.print_exc()

                # 询问是否继续
                if self._ask_continue():
                    continue
                else:
                    break

    def _handle_document_upload(self):
        """处理文档上传"""

        print("\n📁 文档上传")
        print("=" * 30)
        print("支持格式: PDF, Word, TXT, MD, PNG, JPG, JPEG, GIF, WEBP")
        print("最大文件大小: 20MB")
        print("输入文件路径（支持多个，用逗号分隔），或输入'cancel'取消：")

        file_input = input("📎 文件路径: ").strip()

        if file_input.lower() == 'cancel':
            print("❌ 已取消上传")
            return

        # 分割多个文件路径
        file_paths = [path.strip() for path in file_input.split(',')]

        uploaded_count = 0
        failed_files = []

        for file_path in file_paths:
            # 展开用户目录
            file_path = os.path.expanduser(file_path)
            file_path = os.path.abspath(file_path)

            # 验证文件
            is_valid, error_msg = self.document_processor.validate_file(file_path)

            if not is_valid:
                print(f"❌ {Path(file_path).name}: {error_msg}")
                failed_files.append(Path(file_path).name)
                continue

            try:
                # 上传文件
                print(f"⏳ 正在上传 {Path(file_path).name}...")
                file_obj = self.document_processor.upload_file(file_path)

                if file_obj:
                    self.uploaded_documents.append(file_path)
                    uploaded_count += 1
                    print(f"✅ 成功上传: {Path(file_path).name}")

                    # 提取并显示文档摘要
                    print(f"📄 正在分析文档内容...")
                    content_summary = self.document_processor.extract_document_content(file_obj)
                    print(f"\n📋 文档摘要:")
                    print("-" * 20)
                    # 限制显示长度
                    if len(content_summary) > 500:
                        print(content_summary[:500] + "...")
                    else:
                        print(content_summary)
                    print("-" * 20)

            except Exception as e:
                print(f"❌ 上传失败 {Path(file_path).name}: {e}")
                failed_files.append(Path(file_path).name)

        # 显示上传结果
        print(f"\n📊 上传结果:")
        print(f"  成功: {uploaded_count}")
        print(f"  失败: {len(failed_files)}")

        if self.uploaded_documents:
            print(f"\n📚 当前已上传文档 ({len(self.uploaded_documents)}个):")
            for doc_path in self.uploaded_documents:
                print(f"  - {Path(doc_path).name}")
            print("\n💡 提示: 输入'clear'可清除所有已上传的文档")
            print("现在您可以输入需求描述，系统将结合文档内容进行设计")

    def _clear_documents(self):
        """清除已上传的文档"""

        if not self.uploaded_documents:
            print("ℹ️ 没有已上传的文档")
            return

        print(f"\n🗑️ 清除 {len(self.uploaded_documents)} 个文档...")

        # 清理文档处理器中的文件
        self.document_processor.cleanup_all_files()
        self.uploaded_documents.clear()

        print("✅ 所有文档已清除")

    def _start_new_conversation(self, user_input: str):
        """开始新的对话，包含文档支持"""

        try:
            print(f"\n🔄 正在分析需求...")

            # 准备文档文件列表
            document_files = self.uploaded_documents if self.uploaded_documents else None

            if document_files:
                print(f"📚 将参考 {len(document_files)} 个上传的文档")

            # 启动对话（需要修改conversation_manager以支持文档）
            result = self.conversation_manager.start_conversation(
                user_input=user_input,
                user_id="interactive_user",
                document_files=document_files  # 传递文档文件
            )

            self.current_session_id = result["session_id"]
            print(f"✅ 会话已创建: {self.current_session_id[:8]}...")

            # 执行Round 1
            self._execute_round1()

        except Exception as e:
            print(f"❌ 启动对话失败: {e}")
            if CONFIG.debug_mode:
                traceback.print_exc()

    def _execute_round1(self):
        """执行Round 1架构设计"""

        try:
            print(f"\n🏗️ Round 1: 正在进行架构设计...")
            print("📋 使用静态高层术语库进行架构规划...")

            if self.uploaded_documents:
                print(f"📚 结合 {len(self.uploaded_documents)} 个文档进行设计...")

            # 执行架构设计
            result = self.conversation_manager.process_round1(self.current_session_id)

            print(f"\n✅ Round 1完成!")
            print(f"📊 Token使用: {result['stats']['total_tokens']}")

            # 显示组件和接口统计
            design = result.get('design', {})
            component_count = len(design.get('component_plan', []))
            interface_count = len(design.get('interface_plan', []))
            print(f"🔧 设计结果: {component_count}个组件, {interface_count}个接口")

            # 如果有文档处理统计
            if 'documents_processed' in result['stats']:
                print(f"📄 处理文档: {result['stats']['documents_processed']}个")

            # 展示设计结果
            print(f"\n{result['presentation']}")
            print(f"\n{result['confirmation_prompt']}")

            # 等待用户反馈
            self._handle_user_feedback_loop()

        except Exception as e:
            print(f"❌ Round 1执行失败: {e}")
            if CONFIG.debug_mode:
                traceback.print_exc()

    def _handle_user_feedback_loop(self):
        """处理用户反馈循环"""

        max_feedback_rounds = 5  # 最多5轮反馈
        feedback_count = 0

        while feedback_count < max_feedback_rounds:
            try:
                feedback = input("\n💭 您的反馈: ").strip()

                if not feedback:
                    continue

                feedback_count += 1

                # 处理反馈
                result = self.conversation_manager.handle_user_feedback(
                    session_id=self.current_session_id,
                    feedback=feedback
                )

                print(f"\n{result['response']}")

                if result['can_proceed']:
                    # 用户确认，进入Round 2
                    self._execute_round2()
                    break
                else:
                    # 需要继续反馈
                    if feedback_count >= max_feedback_rounds:
                        print(f"\n⚠️ 已达到最大反馈轮次({max_feedback_rounds})，将使用当前设计进入Round 2")
                        self._execute_round2()
                        break
                    else:
                        print(f"\n🔄 请继续提供反馈 ({feedback_count}/{max_feedback_rounds})")

            except Exception as e:
                print(f"❌ 处理反馈失败: {e}")
                if CONFIG.debug_mode:
                    traceback.print_exc()
                break

    def _execute_round2(self):
        """执行Round 2详细生成"""

        try:
            print(f"\n⚙️ Round 2: 正在生成详细ARXML...")
            print("🔍 动态查询KG获取XML结构信息...")
            print("📐 生成定制化JSON Schema...")
            print("🎯 确保实例引用唯一性...")

            # 执行详细生成
            result = self.conversation_manager.process_round2(self.current_session_id)

            print(f"\n🎉 Round 2完成!")
            print(f"📊 Token使用: {result['stats']['total_tokens']}")

            # 显示生成统计
            stats = result['stats']
            print(f"📈 生成统计:")
            print(f"  - 组件数量: {stats.get('component_count', 0)}")
            print(f"  - Schema属性: {stats.get('schema_properties', 0)}")
            print(f"  - 应用约束: {stats.get('constraints_applied', 0)}")

            # 显示输出文件
            output_files = result.get('output_files', [])
            print(f"\n📁 输出文件 ({len(output_files)}个):")
            for file_path in output_files:
                file_name = Path(file_path).name
                print(f"  - {file_name}")

            # 显示生成的ARXML摘要
            self._show_arxml_summary(result['arxml_data'])

            # 显示总体统计
            self._show_session_summary(result['total_stats'])

            print(f"\n✅ {result['message']}")

            # 清理会话文档
            if self.uploaded_documents:
                print("\n🧹 清理会话文档...")
                self._clear_documents()

        except Exception as e:
            print(f"❌ Round 2执行失败: {e}")
            if CONFIG.debug_mode:
                traceback.print_exc()

    def _show_arxml_summary(self, arxml_data: Dict[str, Any]):
        """显示ARXML摘要"""

        print(f"\n📋 生成的ARXML摘要:")
        print("-" * 30)

        component_count = 0
        total_ports = 0
        total_events = 0
        total_runnables = 0

        # 遍历所有顶级元素
        for key, value in arxml_data.items():
            if isinstance(value, dict):
                component_count += 1
                comp_name = value.get('SHORT-NAME', key)
                print(f"🔧 组件: {comp_name}")

                # 统计端口
                ports = value.get("PORTS", {})
                p_ports = len(ports.get("P-PORT-PROTOTYPE", []))
                r_ports = len(ports.get("R-PORT-PROTOTYPE", []))
                ports_count = p_ports + r_ports
                total_ports += ports_count
                print(f"  📌 端口: {ports_count} (P:{p_ports}, R:{r_ports})")

                # 统计内部行为
                behaviors = value.get("INTERNAL-BEHAVIORS", {})
                if "SWC-INTERNAL-BEHAVIOR" in behaviors:
                    swc_behavior = behaviors["SWC-INTERNAL-BEHAVIOR"]

                    events = swc_behavior.get("EVENTS", {})
                    timing_events = len(events.get("TIMING-EVENT", []))
                    total_events += timing_events

                    runnables = swc_behavior.get("RUNNABLES", {})
                    runnable_entities = len(runnables.get("RUNNABLE-ENTITY", []))
                    total_runnables += runnable_entities

                    print(f"  ⏰ 事件: {timing_events}")
                    print(f"  🏃 Runnable: {runnable_entities}")
                print()

        print(
            f"📊 总计: {component_count}个组件, {total_ports}个端口, {total_events}个事件, {total_runnables}个Runnable")

    def _show_session_summary(self, stats: Dict[str, Any]):
        """显示会话摘要"""

        print(f"\n📈 会话统计:")
        print("-" * 20)
        print(f"总Token使用: {stats['total_tokens']}")
        print(f"Round1 Token: {stats['round1_tokens']}")
        print(f"Round2 Token: {stats['round2_tokens']}")

        # 计算成本估算（基于Gemini定价）
        total_tokens = stats['total_tokens']
        estimated_cost = total_tokens * 0.000001  # 简化估算
        print(f"预估成本: ${estimated_cost:.6f}")

    def _run_demo_mode(self):
        """运行演示模式"""

        print("\n🎭 演示模式")
        print("=" * 30)

        demo_scenarios = [
            {
                "name": "单组件温度监控",
                "description": "设计一个温度监控AUTOSAR组件，能够从温度传感器读取数据，进行处理分析，并输出温度状态信息给其他组件使用。",
                "sample_docs": []
            },
            {
                "name": "多组件电机控制系统",
                "description": "设计一个多组件电机控制AUTOSAR系统，包括传感器数据采集组件、控制算法处理组件、执行器控制组件，实现完整的闭环控制。需要组件间的数据交互和协调。",
                "sample_docs": []
            },
            {
                "name": "基于文档的系统设计",
                "description": "基于上传的需求文档设计AUTOSAR系统",
                "sample_docs": ["requirements.pdf", "architecture.png"]
            },
            {
                "name": "复杂数据融合系统",
                "description": "设计一个复杂的多传感器数据融合AUTOSAR系统，包括多个传感器接口组件、数据预处理组件、融合算法组件、结果输出组件。需要处理多种数据类型和复杂的数据流。",
                "sample_docs": []
            },
            {
                "name": "车载通信网关",
                "description": "设计一个车载通信网关AUTOSAR系统，需要多个组件处理不同的通信协议(CAN, LIN, Ethernet)，包括协议转换、路由管理、安全检查等功能。",
                "sample_docs": []
            }
        ]

        print("请选择演示场景:")
        for i, scenario in enumerate(demo_scenarios, 1):
            docs_hint = f" (含示例文档)" if scenario['sample_docs'] else ""
            print(f"  {i}. {scenario['name']}{docs_hint}")

        try:
            choice = input(f"\n请选择 (1-{len(demo_scenarios)}): ").strip()
            choice_idx = int(choice) - 1

            if 0 <= choice_idx < len(demo_scenarios):
                selected = demo_scenarios[choice_idx]
                print(f"\n🎯 选择了: {selected['name']}")
                print(f"📝 需求描述: {selected['description']}")

                if selected['sample_docs']:
                    print(f"📁 示例文档: {', '.join(selected['sample_docs'])}")
                    print("⚠️ 注意: 请确保示例文档存在，或使用'upload'命令上传您自己的文档")

                self.demo_mode = True
                self._start_new_conversation(selected['description'])
            else:
                print("❌ 无效选择")

        except ValueError:
            print("❌ 请输入有效数字")
        except Exception as e:
            print(f"❌ 演示模式错误: {e}")

    def _show_help(self):
        """显示帮助信息"""

        help_text = """
🆘 AUTOSAR组件设计助手 - 帮助信息
========================================

📝 使用说明:
1. 输入您的组件设计需求，系统将进行两轮对话设计
2. 可以先上传文档（PDF/Word/图片），系统会参考文档内容
3. Round 1会生成架构设计，请确认或提供修改意见
4. Round 2会从KG查询详细信息并生成ARXML文档

📁 文档上传:
- 'upload': 上传需求文档、架构图等文件
- 'clear': 清除所有已上传的文档
- 支持格式: PDF, Word, TXT, MD, PNG, JPG等
- 最大20MB，支持批量上传（逗号分隔路径）

💡 需求描述示例:

🔹 单组件场景:
- "设计一个温度监控组件，读取传感器数据并输出状态"
- "创建一个电机控制组件，接收控制指令并调节转速"

🔹 多组件场景:
- "设计一个多组件数据融合系统，包括数据采集、处理、输出组件"
- "创建一个完整的控制系统，需要传感器组件、控制器组件、执行器组件"

🔹 基于文档:
- 先使用'upload'上传需求文档
- 然后输入："基于上传的文档设计AUTOSAR系统"

🎛️ 特殊命令:
- 'upload' : 上传文档文件
- 'clear'  : 清除已上传的文档
- 'demo'   : 运行演示模式
- 'help'   : 显示此帮助信息
- 'stats'  : 显示系统统计信息
- 'quit'   : 退出程序

📋 反馈指南:
- 确认设计: "确认"、"同意"、"可以"
- 修改设计: "修改组件名称为XXX"、"改变接口类型"、"增加一个组件"
- 添加元素: "添加一个传感器组件"、"增加一个服务接口"
- 删除元素: "删除第二个组件"、"去掉这个接口"

🚀 新特性 (本版本):
- ✅ 支持PDF/Word/图片文档上传作为需求输入
- ✅ 文档内容自动提取和分析
- ✅ 基于文档的架构设计优化
- ✅ 支持多组件架构设计和生成
- ✅ 动态从KG查询XML结构生成Schema
- ✅ 确保实例引用的唯一性和一致性

📁 输出文件:
- 单组件: arxml_xxxxxxxx_timestamp.json
- 多组件: 每个组件单独保存 + 会话摘要
- 所有文件保存在 output/ 目录

🔧 KG集成:
- 如果配置了Neo4j，系统会动态查询元模型信息
- 如果没有KG，系统会使用内置的模拟数据
- 约束规则也会从KG动态查询
"""
        print(help_text)

    def _show_stats(self):
        """显示系统统计"""

        try:
            stats = self.conversation_manager.get_system_stats()

            print("\n📊 系统统计信息:")
            print("=" * 30)

            # 对话管理器统计
            conv_stats = stats.get("conversation_manager", {})
            print(f"会话统计:")
            print(f"  总会话数: {conv_stats.get('total_sessions', 0)}")
            print(f"  成功会话: {conv_stats.get('successful_sessions', 0)}")
            print(f"  失败会话: {conv_stats.get('failed_sessions', 0)}")
            print(f"  活跃会话: {conv_stats.get('active_sessions', 0)}")
            print(f"  成功率: {conv_stats.get('success_rate', 0):.2%}")

            # 记忆管理器统计
            memory_stats = stats.get("memory_manager", {})
            if memory_stats:
                print(f"\n记忆统计:")
                print(f"  活跃会话: {memory_stats.get('active_sessions', 0)}")
                print(f"  对话轮次: {memory_stats.get('total_conversations', 0)}")

            # LLM客户端统计
            llm_stats = stats.get("llm_client", {})
            if llm_stats:
                print(f"\nLLM统计:")
                print(f"  API调用次数: {llm_stats.get('call_count', 0)}")
                print(f"  总Token使用: {llm_stats.get('total_tokens', 0)}")
                print(f"  错误次数: {llm_stats.get('error_count', 0)}")
                if llm_stats.get('call_count', 0) > 0:
                    avg_tokens = llm_stats.get('total_tokens', 0) / llm_stats.get('call_count', 1)
                    print(f"  平均Token/调用: {avg_tokens:.0f}")

            # 文档处理统计
            doc_info = self.document_processor.get_uploaded_files_info()
            if doc_info:
                print(f"\n文档统计:")
                print(f"  已上传文档: {len(doc_info)}")
                for doc in doc_info:
                    print(f"    - {doc['name']} ({doc['state']})")

            # 约束引擎统计
            constraint_stats = stats.get("constraint_engine", {})
            if constraint_stats:
                print(f"\n约束引擎统计:")
                print(f"  缓存条目: {constraint_stats.get('cache_entries', 0)}")
                print(f"  缓存约束: {constraint_stats.get('total_cached_constraints', 0)}")
                print(f"  KG连接: {'是' if constraint_stats.get('kg_connected', False) else '否'}")

        except Exception as e:
            print(f"❌ 获取统计信息失败: {e}")

    def _ask_continue(self) -> bool:
        """询问是否继续"""

        try:
            response = input("\n🤔 是否继续? (y/n): ").strip().lower()
            return response in ['y', 'yes', '是', '继续']
        except:
            return False

    def _handle_quit(self):
        """处理退出"""

        print("\n🧹 正在清理资源...")

        try:
            # 清理文档
            if self.uploaded_documents:
                print("📁 清理上传的文档...")
                self.document_processor.cleanup_all_files()

            # 清理当前会话
            if self.current_session_id:
                self.conversation_manager.cleanup_session(self.current_session_id)

            # 清理过期会话
            self.conversation_manager.cleanup_expired_sessions()

            # 显示最终统计
            stats = self.conversation_manager.get_system_stats()
            conv_stats = stats.get("conversation_manager", {})

            print(f"📊 本次运行统计:")
            print(f"  处理会话: {conv_stats.get('total_sessions', 0)}")
            print(f"  成功生成: {conv_stats.get('successful_sessions', 0)}")
            if conv_stats.get('total_sessions', 0) > 0:
                success_rate = conv_stats.get('successful_sessions', 0) / conv_stats.get('total_sessions', 1)
                print(f"  成功率: {success_rate:.1%}")

        except Exception as e:
            print(f"⚠️ 清理时发生错误: {e}")

        print("👋 感谢使用AUTOSAR组件设计助手!")
        print("🚀 新版本特性: 文档上传 + 多组件生成 + 动态KG查询 + 实例引用管理")


def check_environment():
    """检查运行环境"""

    print("🔍 检查运行环境...")

    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ Python版本过低，需要3.8+")
        return False

    # 检查API密钥
    if not CONFIG.llm.api_key:
        print("❌ LLM_API_KEY环境变量未设置")
        print("请设置Gemini API密钥:")
        print("  export LLM_API_KEY='your_api_key'")
        return False

    # 检查输出目录
    CONFIG.output_dir.mkdir(exist_ok=True, parents=True)

    # 测试LLM连接
    try:
        from src.llm_generation.llm.gemini_client import GeminiClient
        client = GeminiClient()
        if not client.test_connection():
            print("⚠️ LLM API连接测试失败，但程序将继续运行")
        else:
            print("✅ LLM API连接正常")
    except Exception as e:
        print(f"⚠️ LLM连接测试异常: {e}")

    # 测试KG连接（可选）
    try:
        from src.llm_generation.knowledge.dynamic_query_engine import query_engine
        if query_engine.driver:
            print("✅ Neo4j KG连接正常")
        else:
            print("ℹ️ 使用模拟KG数据（未配置Neo4j）")
    except Exception as e:
        print(f"ℹ️ KG连接检查异常: {e}")

    print("✅ 环境检查完成")
    return True


def main():
    """主函数"""

    try:
        # 检查环境
        if not check_environment():
            sys.exit(1)

        # 创建生成器实例
        generator = LLMRAGGenerator()

        # 运行交互式会话
        generator.run_interactive_session()

    except KeyboardInterrupt:
        print("\n\n⚠️ 程序被用户中断")
    except Exception as e:
        print(f"\n❌ 程序运行失败: {e}")
        if CONFIG.debug_mode:
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()