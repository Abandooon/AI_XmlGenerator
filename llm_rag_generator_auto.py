#!/usr/bin/env python3
"""llm_rag_generator.py - LLM RAG AUTOSAR组件生成器主程序

基于对话式逐层深入设计系统的AUTOSAR组件生成器
支持两轮对话：Round1架构设计 + Round2详细生成
支持多组件生成，动态Schema生成，支持文档上传
✨ 新增：批量处理需求文件 + 指标记录功能
"""

import os
import sys
import json
import traceback
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from src.llm_generation.core.conversation_manager import ConversationState
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

        # 条件初始化文档处理器
        if CONFIG.llm.enable_file_upload:
            try:
                from src.llm_generation.utils.document_processor import document_processor
                self.document_processor = document_processor
                self.file_upload_enabled = True
            except ImportError:
                self.document_processor = None
                self.file_upload_enabled = False
                print("⚠️ 文档处理器不可用，文档上传功能已禁用")
        else:
            self.document_processor = None
            self.file_upload_enabled = False

        self.current_session_id = None
        self.demo_mode = False
        self.uploaded_documents = []

        # ✨ 新增：批量实验相关
        self.batch_mode = False
        self.current_metrics = {}

        # ✨ 新增：创建输出目录
        self.generated_arxml_dir = project_root / "generated_arxml"
        self.metrics_dir = project_root / "llm_rag_output" / "mark"
        self.generated_arxml_dir.mkdir(exist_ok=True, parents=True)
        self.metrics_dir.mkdir(exist_ok=True, parents=True)

        # 显示功能状态
        print("🚀 LLM RAG AUTOSAR组件生成器")
        print("=" * 50)
        print(f"📊 配置信息:")
        print(f"  - LLM模型: {CONFIG.llm.model_name}")
        print(f"  - 调试模式: {'开启' if CONFIG.debug_mode else '关闭'}")
        print(f"  - 文档上传: {'可用' if self.file_upload_enabled else '禁用（纯对话模式）'}")
        print(f"  - 输出目录: {CONFIG.output_dir}")
        print(f"  - ARXML目录: {self.generated_arxml_dir}")
        print(f"  - 指标目录: {self.metrics_dir}")
        print("=" * 50)

    # ✨ 新增：批量处理需求文件
    def run_batch_experiment(self):
        """运行批量实验模式"""
        print("\n🧪 批量实验模式")
        print("=" * 50)

        # 需求文件目录
        require_dir = project_root / "nlp_require"
        if not require_dir.exists():
            print(f"❌ 需求目录不存在: {require_dir}")
            return

        # 读取需求文件
        requirement_files = {
            # "simple": require_dir / "simple.json",
            # "middle": require_dir / "middle.json",
            "complex": require_dir / "complex.json"
        }

        # 检查文件是否存在
        for complexity, file_path in requirement_files.items():
            if not file_path.exists():
                print(f"⚠️  需求文件不存在: {file_path}")
                requirement_files.pop(complexity)

        if not requirement_files:
            print("❌ 没有可用的需求文件")
            return

        print(f"📁 找到 {len(requirement_files)} 个需求文件")

        # 询问是否继续
        response = input("\n是否开始批量生成? (y/n): ").strip().lower()
        if response not in ['y', 'yes', '是']:
            print("❌ 已取消")
            return

        # 批量处理
        self.batch_mode = True
        all_results = []

        for complexity, file_path in requirement_files.items():
            print(f"\n{'=' * 60}")
            print(f"📋 处理 {complexity.upper()} 复杂度需求")
            print(f"{'=' * 60}")

            try:
                # 读取需求文件
                with open(file_path, 'r', encoding='utf-8') as f:
                    requirements = json.load(f)

                if not isinstance(requirements, list):
                    requirements = [requirements]

                # 处理每个需求
                for idx, req in enumerate(requirements, 1):
                    print(f"\n{'─' * 60}")
                    print(f"🔹 需求 {idx}/{len(requirements)}: {req.get('system_name', 'Unknown')}")
                    print(f"{'─' * 60}")

                    result = self._process_single_requirement(
                        requirement=req,
                        complexity=complexity,
                        index=idx
                    )
                    all_results.append(result)

                    # 短暂延迟避免API限流
                    if idx < len(requirements):
                        time.sleep(2)

            except Exception as e:
                print(f"❌ 处理 {complexity} 失败: {e}")
                if CONFIG.debug_mode:
                    traceback.print_exc()

        # 保存汇总结果
        self._save_batch_summary(all_results)

        print(f"\n{'=' * 60}")
        print("✅ 批量实验完成！")
        print(f"📊 处理了 {len(all_results)} 个需求")
        print(f"📁 ARXML文件位于: {self.generated_arxml_dir}")
        print(f"📈 指标文件位于: {self.metrics_dir}")
        print(f"\n💡 提示: 输入 'analyze' 命令可手动计算详细指标")
        print(f"{'=' * 60}")

    # ✨ 新增：处理单个需求
    def _process_single_requirement(
            self,
            requirement: Dict[str, Any],
            complexity: str,
            index: int
    ) -> Dict[str, Any]:
        """处理单个需求并记录指标"""

        system_name = requirement.get("system_name", f"System_{index}")
        description = requirement.get("description", "")

        # 构建提示文本
        prompt = self._build_prompt_from_requirement(requirement)

        print(f"\n📝 系统名称: {system_name}")
        print(f"📄 描述: {description[:100]}...")

        # 初始化指标记录
        metrics = {
            "case_id": f"{complexity}_{index}",
            "system_name": system_name,
            "complexity": complexity,
            "requirement": requirement,
            "start_time": datetime.now().isoformat(),
            "phase1": {},
            "phase2": {},
            "final_status": "pending"
        }

        try:
            # Phase 1: Blueprint生成
            print(f"\n🏗️  Phase 1: 架构设计...")
            phase1_start = time.time()

            result = self.conversation_manager.start_conversation(
                user_input=prompt,
                user_id=f"batch_{complexity}_{index}"
            )
            self.current_session_id = result["session_id"]

            # Round1 设计
            result1 = self.conversation_manager.process_round1(self.current_session_id)
            phase1_end = time.time()

            # 记录Phase1指标
            metrics["phase1"] = {
                "duration": phase1_end - phase1_start,
                "api_calls": 1,
                "tokens": result1.get('stats', {}).get('total_tokens', 0),
                "component_count": len(result1.get('design', {}).get('component_plan', [])),
                "interface_count": len(result1.get('design', {}).get('interface_plan', [])),
                "blueprint": result1.get('design', {})
            }

            print(f"✅ Phase 1 完成 ({phase1_end - phase1_start:.2f}s)")
            print(f"   - Token使用: {metrics['phase1']['tokens']}")
            print(f"   - 组件数: {metrics['phase1']['component_count']}")
            print(f"   - 接口数: {metrics['phase1']['interface_count']}")

            # ✅ 批量模式：直接设置确认状态（绕过用户反馈）
            print(f"\n⚙️  批量模式：自动确认设计...")
            session_info = self.conversation_manager._get_session_info(self.current_session_id)

            if session_info:
                # 直接设置为已确认状态
                session_info["state"] = ConversationState.ROUND1_COMPLETED
                session_info["final_confirmation_time"] = time.time()

                # 记录确认操作到内存
                self.conversation_manager.memory_manager.add_conversation_turn(
                    session_id=self.current_session_id,
                    round_number=1,
                    user_input="[自动确认]",
                    system_output="批量模式自动确认设计",
                    design_artifacts={},
                    user_feedback="[Batch Mode Auto-Confirm]"
                )

                print(f"✅ 设计已自动确认")
            else:
                raise ConversationError(f"会话不存在: {self.current_session_id}")

            # Phase 2: 详细生成
            print(f"\n🔧 Phase 2: 详细生成...")
            phase2_start = time.time()

            result2 = self.conversation_manager.process_round2(self.current_session_id)

            phase2_end = time.time()

            # 记录Phase2指标
            metrics["phase2"] = {
                "duration": phase2_end - phase2_start,
                "tokens": result2.get('stats', {}).get('total_tokens', 0),
                "output_files": result2.get('output_files', [])
            }

            print(f"✅ Phase 2 完成 ({phase2_end - phase2_start:.2f}s)")
            print(f"   - Token使用: {metrics['phase2']['tokens']}")
            print(f"   - 输出文件: {len(metrics['phase2']['output_files'])}")

            # 移动生成的文件到指定目录
            self._move_generated_files(
                output_files=result2.get('output_files', []),
                system_name=system_name,
                complexity=complexity,
                index=index
            )

            metrics["final_status"] = "success"
            metrics["end_time"] = datetime.now().isoformat()

        except Exception as e:
            print(f"❌ 处理失败: {e}")
            if CONFIG.debug_mode:
                traceback.print_exc()

            metrics["final_status"] = "failure"
            metrics["error"] = str(e)
            metrics["end_time"] = datetime.now().isoformat()

        finally:
            # 保存单个需求的指标
            self._save_metrics(metrics, complexity, index)

        return metrics

    # ✨ 新增：从需求构建提示
    def _build_prompt_from_requirement(self, requirement: Dict[str, Any]) -> str:
        """从需求JSON构建提示文本"""

        prompt_parts = []

        # 系统名称
        if "system_name" in requirement:
            prompt_parts.append(f"系统名称: {requirement['system_name']}")

        # 描述
        if "description" in requirement:
            prompt_parts.append(f"系统描述: {requirement['description']}")

        # 组件数量
        if "components_count" in requirement:
            prompt_parts.append(f"组件数量: {requirement['components_count']}")

        # 组件类型
        if "component_types" in requirement:
            types_str = ", ".join(requirement["component_types"])
            prompt_parts.append(f"组件类型: {types_str}")

        # 关键需求
        if "key_requirements" in requirement:
            prompt_parts.append("关键需求:")
            for req in requirement["key_requirements"]:
                prompt_parts.append(f"  - {req}")

        return "\n".join(prompt_parts)

    # ✨ 新增：移动生成的文件
    def _move_generated_files(
            self,
            output_files: List[str],
            system_name: str,
            complexity: str,
            index: int
    ):
        """移动生成的ARXML文件到指定目录"""

        import shutil

        # 创建子目录
        target_dir = self.generated_arxml_dir / complexity
        target_dir.mkdir(exist_ok=True, parents=True)

        moved_files = []

        for file_path in output_files:
            if not os.path.exists(file_path):
                print(f"⚠️  文件不存在: {file_path}")
                continue

            # 构建新文件名
            file_name = Path(file_path).name
            # 添加序号前缀
            new_name = f"{complexity}_{index:02d}_{system_name}_{file_name}"
            target_path = target_dir / new_name

            try:
                shutil.copy2(file_path, target_path)
                moved_files.append(str(target_path))
                print(f"📁 已保存: {target_path.name}")
            except Exception as e:
                print(f"⚠️  移动文件失败 {file_name}: {e}")

        return moved_files

    # ✨ 新增：保存指标
    def _save_metrics(self, metrics: Dict[str, Any], complexity: str, index: int):
        """保存单个需求的指标"""

        # 创建复杂度子目录
        complexity_dir = self.metrics_dir / complexity
        complexity_dir.mkdir(exist_ok=True, parents=True)

        # 保存指标文件
        metrics_file = complexity_dir / f"{complexity}_{index:02d}_metrics.json"

        try:
            with open(metrics_file, 'w', encoding='utf-8') as f:
                json.dump(metrics, f, indent=2, ensure_ascii=False)
            print(f"📊 指标已保存: {metrics_file.name}")
        except Exception as e:
            print(f"⚠️  保存指标失败: {e}")

    # ✨ 新增：保存批量汇总
    def _save_batch_summary(self, all_results: List[Dict[str, Any]]):
        """保存批量实验汇总"""

        summary = {
            "experiment_time": datetime.now().isoformat(),
            "total_cases": len(all_results),
            "success_count": sum(1 for r in all_results if r["final_status"] == "success"),
            "failure_count": sum(1 for r in all_results if r["final_status"] == "failure"),
            "by_complexity": {},
            "results": all_results
        }

        # 按复杂度统计
        for result in all_results:
            complexity = result["complexity"]
            if complexity not in summary["by_complexity"]:
                summary["by_complexity"][complexity] = {
                    "total": 0,
                    "success": 0,
                    "failure": 0
                }

            summary["by_complexity"][complexity]["total"] += 1
            if result["final_status"] == "success":
                summary["by_complexity"][complexity]["success"] += 1
            else:
                summary["by_complexity"][complexity]["failure"] += 1

        # 保存汇总文件
        summary_file = self.metrics_dir / f"batch_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        try:
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            print(f"\n📊 汇总报告已保存: {summary_file}")
        except Exception as e:
            print(f"⚠️  保存汇总失败: {e}")

    # ✨ 新增：手动分析指标
    def analyze_metrics(self):
        """手动分析和计算详细指标"""

        print("\n📊 指标分析工具")
        print("=" * 50)

        # 读取所有指标文件
        all_metrics = []

        for complexity_dir in self.metrics_dir.iterdir():
            if not complexity_dir.is_dir():
                continue

            for metrics_file in complexity_dir.glob("*_metrics.json"):
                try:
                    with open(metrics_file, 'r', encoding='utf-8') as f:
                        metrics = json.load(f)
                        all_metrics.append(metrics)
                except Exception as e:
                    print(f"⚠️  读取失败 {metrics_file}: {e}")

        if not all_metrics:
            print("❌ 没有找到指标文件")
            return

        print(f"📁 找到 {len(all_metrics)} 个指标文件")

        # 计算统计信息
        self._calculate_statistics(all_metrics)

    # ✨ 新增：计算统计信息
    def _calculate_statistics(self, all_metrics: List[Dict[str, Any]]):
        """计算并显示统计信息"""

        print("\n" + "=" * 60)
        print("📈 统计分析结果")
        print("=" * 60)

        # 总体统计
        total = len(all_metrics)
        success = sum(1 for m in all_metrics if m["final_status"] == "success")
        failure = total - success

        print(f"\n【总体统计】")
        print(f"  总案例数: {total}")
        print(f"  成功: {success} ({success / total * 100:.1f}%)")
        print(f"  失败: {failure} ({failure / total * 100:.1f}%)")

        # 按复杂度统计
        by_complexity = {}
        for m in all_metrics:
            complexity = m["complexity"]
            if complexity not in by_complexity:
                by_complexity[complexity] = []
            by_complexity[complexity].append(m)

        print(f"\n【按复杂度统计】")
        for complexity in sorted(by_complexity.keys()):
            metrics = by_complexity[complexity]
            total_c = len(metrics)
            success_c = sum(1 for m in metrics if m["final_status"] == "success")

            print(f"\n  {complexity.upper()}:")
            print(f"    案例数: {total_c}")
            print(f"    成功率: {success_c / total_c * 100:.1f}%")

        # Token使用统计
        successful_metrics = [m for m in all_metrics if m["final_status"] == "success"]

        if successful_metrics:
            total_tokens = sum(
                m["phase1"].get("tokens", 0) + m["phase2"].get("tokens", 0)
                for m in successful_metrics
            )
            avg_tokens = total_tokens / len(successful_metrics)

            print(f"\n【Token使用统计】")
            print(f"  总Token: {total_tokens}")
            print(f"  平均Token/案例: {avg_tokens:.0f}")

        # 时间统计
        if successful_metrics:
            total_time = sum(
                m["phase1"].get("duration", 0) + m["phase2"].get("duration", 0)
                for m in successful_metrics
            )
            avg_time = total_time / len(successful_metrics)

            print(f"\n【时间统计】")
            print(f"  总耗时: {total_time:.1f}秒")
            print(f"  平均耗时/案例: {avg_time:.1f}秒")

        # 组件统计
        component_counts = [
            m["phase1"].get("component_count", 0)
            for m in successful_metrics
        ]

        if component_counts:
            print(f"\n【组件统计】")
            print(f"  平均组件数: {sum(component_counts) / len(component_counts):.1f}")
            print(f"  最小组件数: {min(component_counts)}")
            print(f"  最大组件数: {max(component_counts)}")

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
        print("\n📚 支持的文档格式:")
        print("  PDF, Word(.doc/.docx), 文本(.txt/.md), 图片(.png/.jpg/.jpeg/.gif/.webp)")
        print("\n输入 'quit' 或 'exit' 可随时退出")
        print("输入 'demo' 可运行演示模式")
        print("输入 'help' 查看帮助信息")
        print("输入 'upload' 上传文档文件")
        print("输入 'batch' 运行批量实验模式")  # ✨ 新增
        print("输入 'analyze' 分析已有指标")  # ✨ 新增

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
                elif user_input.lower() == 'batch':  # ✨ 新增
                    self.run_batch_experiment()
                    continue
                elif user_input.lower() == 'analyze':  # ✨ 新增
                    self.analyze_metrics()
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

    # ... 其他方法保持不变 ...

    def _handle_document_upload(self):
        """处理文档上传"""
        if not self.file_upload_enabled:
            print("❌ 文档上传功能未启用")
            print("提示: 请在配置文件中设置 enable_file_upload: true 来启用此功能")
            return

        print("\n📁 文档上传")
        print("=" * 30)
        print("支持格式: PDF, Word, TXT, MD, PNG, JPG, JPEG, GIF, WEBP")
        print("最大文件大小: 20MB")
        print("输入文件路径（支持多个，用逗号分隔），或输入'cancel'取消：")

        file_input = input("🔎 文件路径: ").strip()

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
        """开始新的对话，条件性支持文档"""
        try:
            print(f"\n📄 正在分析需求...")

            # 准备文档文件列表
            document_files = self.uploaded_documents if self.uploaded_documents else None

            if document_files:
                print(f"📚 将参考 {len(document_files)} 个上传的文档")

            # 根据文档上传配置调用不同的方法
            if self.file_upload_enabled and document_files:
                # 启用文档上传且有文档时
                result = self.conversation_manager.start_conversation(
                    user_input=user_input,
                    user_id="interactive_user",
                    document_files=document_files
                )
            else:
                # 纯对话模式，不传递document_files参数
                result = self.conversation_manager.start_conversation(
                    user_input=user_input,
                    user_id="interactive_user"
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
            print(f"\n🗃️ Round 1: 正在进行架构设计...")
            print("📋 使用限定高层术语库进行架构规划...")

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


            if not self.batch_mode:
                # 交互模式：需要人工反馈
                self._handle_user_feedback_loop()
            else:
                # ✅ 批量模式：直接确认（与 _process_single_requirement 中的逻辑一致）
                print(f"\n⚙️  批量模式：自动确认设计...")
                session_info = self.conversation_manager._get_session_info(self.current_session_id)

                if session_info:
                    session_info["state"] = ConversationState.ROUND1_COMPLETED
                    session_info["final_confirmation_time"] = time.time()

                    self.conversation_manager.memory_manager.add_conversation_turn(
                        session_id=self.current_session_id,
                        round_number=1,
                        user_input="[自动确认]",
                        system_output="批量模式自动确认设计",
                        design_artifacts={},
                        user_feedback="[Batch Mode Auto-Confirm]"
                    )
                    print(f"✅ 设计已自动确认")

                    # 直接进入 Round2
                    self._execute_round2()
                else:
                    raise ConversationError(f"会话不存在: {self.current_session_id}")

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
                        print(f"\n📄 请继续提供反馈 ({feedback_count}/{max_feedback_rounds})")

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
            print("📋 生成定制化JSON Schema...")
            print("🎯 确保实例引用唯一性...")

            # 执行详细生成
            result = self.conversation_manager.process_round2(self.current_session_id)

            print(f"\n🎉 Round 2完成!")
            print(f"📊 Token使用: {result['stats']['total_tokens']}")

            # 显示输出文件
            output_files = result.get('output_files', [])
            print(f"\n📁 输出文件 ({len(output_files)}个):")
            for file_path in output_files:
                file_name = Path(file_path).name
                print(f"  - {file_name}")

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
                    print(f"📚 示例文档: {', '.join(selected['sample_docs'])}")
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

🎛️ 特殊命令:
- 'upload' : 上传文档文件
- 'clear'  : 清除已上传的文档
- 'demo'   : 运行演示模式
- 'batch'  : 批量实验模式（RQ2）✨
- 'analyze': 分析已有指标 ✨
- 'help'   : 显示此帮助信息
- 'stats'  : 显示系统统计信息
- 'quit'   : 退出程序

📚 批量实验模式:
- 自动读取 nlp_require/ 目录下的需求文件
- 支持 simple.json, middle.json, complex.json
- 自动执行 Round1 + Round2
- 生成的ARXML保存到 generated_arxml/
- 指标保存到 output/mark/
- 使用 'analyze' 命令分析指标
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

            # LLM客户端统计
            llm_stats = stats.get("llm_client", {})
            if llm_stats:
                print(f"\nLLM统计:")
                print(f"  API调用次数: {llm_stats.get('call_count', 0)}")
                print(f"  总Token使用: {llm_stats.get('total_tokens', 0)}")
                print(f"  错误次数: {llm_stats.get('error_count', 0)}")

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
        print("🚀 新版本特性: 文档上传 + 多组件生成 + 动态KG查询 + 实例引用管理 + 批量实验")


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
        print("请设置API密钥:")
        print("  export LLM_API_KEY='your_api_key'")
        return False

    # 检查输出目录
    CONFIG.output_dir.mkdir(exist_ok=True, parents=True)

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