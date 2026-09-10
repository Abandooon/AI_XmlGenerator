"""core/conversation_manager.py - 优化的对话管理核心

简化流程，充分利用长上下文能力
"""
import json
import time
from enum import Enum
from typing import Dict, List, Any, Optional

from .dependency_analyzer import dependency_analyzer
from .memory_manager import memory_manager
from .round1_designer import round1_designer
from .round2_generator import round2_generator
from .user_interaction import user_interaction
from ..config import CONFIG
from ..utils.exceptions import ConversationError, ArchitectureDesignError, ValidationError
from ..utils.serializers import ArchitectureDesign
from src.validation.v2.selection_obligations import generation_status_from_validation


class ConversationState(Enum):
    """对话状态枚举"""
    INITIALIZED = "initialized"
    ROUND1_PROCESSING = "round1_processing"
    ROUND1_COMPLETED = "round1_completed"
    USER_FEEDBACK = "user_feedback"
    ROUND2_PROCESSING = "round2_processing"
    ROUND2_COMPLETED = "round2_completed"
    COMPLETED = "completed"
    ERROR = "error"


class ConversationManager:
    """优化的对话管理核心"""

    MAX_MODIFICATIONS = 10

    def __init__(self):
        """初始化对话管理器"""
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.memory_manager = memory_manager
        self.round1_designer = round1_designer
        self.round2_generator = round2_generator
        self.user_interaction = user_interaction
        self.dependency_analyzer = dependency_analyzer

        # 统计信息
        self.total_sessions = 0
        self.successful_sessions = 0
        self.failed_sessions = 0
        self.incomplete_sessions = 0
        self.single_batch_sessions = 0  # 新增：单批生成的会话数
        self.multi_batch_sessions = 0   # 新增：多批生成的会话数

    def start_conversation(
            self,
            user_input: str,
            user_id: str = None,
            session_context: Dict[str, Any] = None,
            document_files: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """启动新对话会话 - 支持文档输入"""

        try:
            session_id = self.memory_manager.create_session(user_id)
            self.total_sessions += 1

            session_info = {
                "session_id": session_id,
                "state": ConversationState.INITIALIZED,
                "user_id": user_id,
                "start_time": time.time(),
                "current_round": 0,
                "user_input": user_input,
                "context": session_context or {},
                "document_files": document_files,  # 保存文档文件列表
                "document_context": "",  # 文档内容摘要
                "results": {},
                "stats": {
                    "total_tokens": 0,
                    "round1_tokens": 0,
                    "round2_tokens": 0
                },
                "optimization_info": {}
            }

            self.active_sessions[session_id] = session_info

            # 预分析系统规模
            self._analyze_system_scale(session_info, user_input)

            # 如果有文档，提取文档上下文
            if document_files:
                session_info["document_context"] = f"基于{len(document_files)}个文档的需求设计"

            if CONFIG.debug_mode:
                print(f"[DEBUG] 启动新对话: {session_id}")
                print(f"[DEBUG] 预估系统规模: {session_info['optimization_info']}")
                if document_files:
                    print(f"[DEBUG] 包含文档: {len(document_files)}个")

            return {
                "session_id": session_id,
                "status": "success",
                "state": session_info["state"].value,
                "optimization_hint": session_info.get("optimization_info", {}),
                "has_documents": bool(document_files),
                "message": "对话会话已创建，准备开始架构设计..."
            }

        except Exception as e:
            self.failed_sessions += 1
            raise ConversationError(f"启动对话失败: {str(e)}")

    def process_round1(self, session_id: str) -> Dict[str, Any]:
        """执行Round 1架构设计 - 修正版"""

        session_info = self._get_session_info(session_id)
        if not session_info:
            raise ConversationError(f"会话不存在: {session_id}")

        try:
            session_info["state"] = ConversationState.ROUND1_PROCESSING
            session_info["current_round"] = 1

            # 获取记忆上下文
            memory_context = self.memory_manager.generate_continuity_prompt(session_id)

            # 准备设计上下文
            design_context = json.dumps({
                **session_info.get("context", {}),
                "optimization_info": session_info.get("optimization_info", {}),
                "document_context": session_info.get("document_context", "")
            })

            # 执行架构设计（Round1不需要函数调用）
            design, stats = self.round1_designer.design_architecture(
                user_requirements=session_info["user_input"],
                design_context=design_context,
                memory_context=memory_context,
                suggested_patterns=[],
                document_files=session_info.get("document_files"),
                use_functions=False,
                generation_seed=session_info.get("context", {}).get("generation_seed"),
                generation_value_obligations=session_info.get("context", {}).get(
                    "generation_value_obligations", []
                ),
                generation_requirement_contracts=session_info.get("context", {}).get(
                    "generation_requirement_contracts", []
                ),
            )

            # 【移除】不在Round1分析生成策略
            # generation_strategy = self._analyze_generation_strategy(design)

            # 展示设计结果
            presentation = self.user_interaction.present_architecture_design(design)

            # 基于复杂度添加简单提示（不涉及生成策略）
            complexity = design.system_analysis.get("complexity_assessment", "Medium")
            component_count = len(design.component_plan)

            if component_count <= 5:
                presentation += "\n\n✨ 系统规模适中，设计简洁清晰。"
            elif component_count <= 15:
                presentation += "\n\n📊 系统包含多个组件，架构设计合理。"
            else:
                presentation += "\n\n🏗️ 大型系统架构，组件职责明确。"

            confirmation_prompt = self.user_interaction.generate_confirmation_prompt(design)

            session_info["state"] = ConversationState.ROUND1_COMPLETED
            session_info["results"]["round1"] = {
                "design": design,
                "presentation": presentation,
                # 移除 generation_strategy
            }
            session_info["stats"]["round1_tokens"] = stats["total_tokens"]
            session_info["stats"]["total_tokens"] += stats["total_tokens"]

            # 更新记忆
            self.memory_manager.add_conversation_turn(
                session_id=session_id,
                round_number=1,
                user_input=session_info["user_input"],
                system_output=presentation,
                design_artifacts=design.__dict__
            )

            self.memory_manager.update_design_state(session_id, design)

            if CONFIG.debug_mode:
                print(f"[DEBUG] Round1完成: {stats['component_count']}个组件, "
                      f"{stats['interface_count']}个接口")
                print(f"[DEBUG] 复杂度评估: {complexity}")

            return {
                "session_id": session_id,
                "status": "success",
                "state": session_info["state"].value,
                "round": 1,
                "design": design.__dict__,
                "presentation": presentation,
                "confirmation_prompt": confirmation_prompt,
                # 移除 generation_strategy
                "stats": stats,
                "message": "架构设计已完成，请确认或提供修改意见"
            }

        except Exception as e:
            session_info["state"] = ConversationState.ERROR
            raise ArchitectureDesignError(f"Round1执行失败: {str(e)}")

    def process_round2(
            self,
            session_id: str,
            custom_requirements: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """执行Round 2详细生成 - 修正版"""

        session_info = self._get_session_info(session_id)
        if not session_info:
            raise ConversationError(f"会话不存在: {session_id}")

        try:
            if session_info["state"] != ConversationState.ROUND1_COMPLETED:
                raise ConversationError("必须先完成Round1并确认设计")

            if "final_confirmation_time" not in session_info:
                raise ConversationError("设计尚未最终确认")

            session_info["state"] = ConversationState.ROUND2_PROCESSING
            session_info["current_round"] = 2

            confirmed_design = session_info["results"]["round1"]["design"]
            component_count = len(confirmed_design.component_plan)

            # 在Round2决定生成模式（基于配置的阈值）
            single_batch_threshold = getattr(CONFIG.generation, 'single_batch_threshold', 25)

            if component_count <= single_batch_threshold:
                generation_mode = "unified_batch"
                if CONFIG.debug_mode:
                    print(f"[DEBUG] 使用单批生成模式（{component_count}个组件 <= 阈值{single_batch_threshold}）")
            else:
                # 只有在超过阈值时才考虑分批
                generation_mode = "intelligent_batch"
                if CONFIG.debug_mode:
                    print(f"[DEBUG] 使用分批生成模式（{component_count}个组件 > 阈值{single_batch_threshold}）")

            # 记录生成模式统计
            if generation_mode == "unified_batch":
                self.single_batch_sessions += 1
            else:
                self.multi_batch_sessions += 1

            memory_context = self.memory_manager.generate_continuity_prompt(session_id)

            # 添加优化要求
            if custom_requirements is None:
                custom_requirements = {}
            custom_requirements["optimization_mode"] = generation_mode
            custom_requirements["enable_direct_references"] = True

            # 设置schema深度
            schema_depth = getattr(CONFIG.generation, 'max_schema_injection_depth',
                                   getattr(CONFIG.metamodel_injection, 'round2_depth', 15))
            custom_requirements["schema_depth"] = schema_depth

            # 执行详细生成
            arxml_data, stats = self.round2_generator.generate_arxml(
                architecture_design=confirmed_design,
                memory_context=memory_context,
                custom_requirements=custom_requirements
            )

            session_info["state"] = ConversationState.ROUND2_COMPLETED
            session_info["results"]["round2"] = {
                "arxml_data": arxml_data,
                "generation_mode": generation_mode,
                "component_count": component_count,
                "optimization_metrics": stats.get("performance_metrics", {}),
                "validation": stats.get("validation"),
                "validation_context": stats.get("validation_context"),
                "auto_repair": stats.get("auto_repair"),
            }
            session_info["stats"]["round2_tokens"] = stats["total_tokens"]
            session_info["stats"]["total_tokens"] += stats["total_tokens"]

            # 保存结果
            output_files = self._save_optimized_results(session_id, arxml_data, confirmed_design)

            self.memory_manager.add_conversation_turn(
                session_id=session_id,
                round_number=2,
                user_input="生成详细ARXML",
                system_output=f"ARXML已生成（{generation_mode}）",
                design_artifacts={"arxml_files": [str(f) for f in output_files]}
            )

            session_info["state"] = ConversationState.COMPLETED
            validation = stats.get("validation") or {}
            validation_decision = validation.get("decision", "DISABLED")
            result_status = generation_status_from_validation(validation_decision)
            if result_status == "success":
                self.successful_sessions += 1
            elif result_status == "generated_with_validation_errors":
                self.failed_sessions += 1
            else:
                self.incomplete_sessions += 1

            # 性能报告
            performance_report = self._generate_performance_report(session_info, stats)

            if CONFIG.debug_mode:
                print(f"[DEBUG] Round2完成: {len(output_files)}个文件")

            return {
                "session_id": session_id,
                "status": result_status,
                "state": session_info["state"].value,
                "round": 2,
                "arxml_data": arxml_data,
                "output_files": [str(f) for f in output_files],
                "stats": stats,
                "total_stats": session_info["stats"],
                "generation_mode": generation_mode,
                "performance_report": performance_report,
                "validation": validation,
                "message": f"ARXML文档已生成，共{len(output_files)}个输出文件，"
                           f"验证结果为 {validation_decision}，使用{generation_mode}模式。"
            }

        except Exception as e:
            session_info["state"] = ConversationState.ERROR
            self.failed_sessions += 1
            raise ValidationError(f"Round2执行失败: {str(e)}")

    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息 - 修复版"""

        stats = {
            "conversation_manager": {
                "total_sessions": self.total_sessions,
                "successful_sessions": self.successful_sessions,
                "failed_sessions": self.failed_sessions,
                "incomplete_sessions": self.incomplete_sessions,
                "active_sessions": len(self.active_sessions),
                "success_rate": self.successful_sessions / max(self.total_sessions, 1),
                "single_batch_sessions": self.single_batch_sessions,
                "multi_batch_sessions": self.multi_batch_sessions,
                "single_batch_ratio": self.single_batch_sessions / max(self.total_sessions, 1)
            },
            "optimization_metrics": {
                "average_single_batch_threshold": CONFIG.generation.single_batch_threshold,
                "max_batch_size": CONFIG.generation.max_batch_size,
                # 修复配置属性访问
                "schema_injection_depth": CONFIG.generation.max_schema_injection_depth,
                "long_context_utilization": self._calculate_context_utilization()
            },
            "memory_manager": self.memory_manager.get_stats()
        }

        return stats


    def _analyze_system_scale(self, session_info: Dict[str, Any], user_input: str):
        """预分析系统规模"""

        # 简单的关键词分析
        keywords = {
            "small": ["简单", "单一", "基础", "simple", "basic", "single"],
            "medium": ["中等", "标准", "常规", "standard", "normal", "typical"],
            "large": ["复杂", "大型", "多个", "系统", "complex", "large", "multiple", "system"]
        }

        input_lower = user_input.lower()
        scale = "medium"  # 默认中等规模

        for size, words in keywords.items():
            if any(word in input_lower for word in words):
                scale = size
                break

        # 估算组件数量
        estimated_components = {
            "small": 3,
            "medium": 8,
            "large": 20
        }

        session_info["optimization_info"] = {
            "estimated_scale": scale,
            "estimated_components": estimated_components.get(scale, 8),
            "recommended_mode": "unified_batch" if scale != "large" else "intelligent_batch"
        }


    def _generate_performance_report(
        self,
        session_info: Dict[str, Any],
        round2_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成性能报告"""

        report = {
            "session_duration": time.time() - session_info["start_time"],
            "total_tokens": session_info["stats"]["total_tokens"],
            "round1_tokens": session_info["stats"]["round1_tokens"],
            "round2_tokens": session_info["stats"]["round2_tokens"],
            "generation_mode": session_info["results"]["round2"]["generation_mode"],
            "component_count": session_info["results"]["round2"]["component_count"],
            "tokens_per_component": round2_stats.get("tokens_per_component", 0),
            "generation_time": round2_stats.get("generation_time", 0),
            "optimization_metrics": round2_stats.get("performance_metrics", {}),
            "efficiency_score": self._calculate_efficiency_score(session_info, round2_stats)
        }

        return report

    def _calculate_efficiency_score(
        self,
        session_info: Dict[str, Any],
        round2_stats: Dict[str, Any]
    ) -> float:
        """计算效率得分"""

        # 基于多个因素计算效率得分
        tokens_per_comp = round2_stats.get("tokens_per_component", 5000)
        time_per_comp = round2_stats.get("performance_metrics", {}).get("time_per_component", 10)

        # 理想值
        ideal_tokens = 3000
        ideal_time = 5

        # 计算得分（0-100）
        token_score = max(0, 100 - abs(tokens_per_comp - ideal_tokens) / 50)
        time_score = max(0, 100 - abs(time_per_comp - ideal_time) * 5)

        # 单批生成加分
        if session_info["results"]["round2"]["generation_mode"] == "unified_batch":
            batch_bonus = 10
        else:
            batch_bonus = 0

        return min(100, (token_score + time_score) / 2 + batch_bonus)

    def _save_optimized_results(
            self,
            session_id: str,
            arxml_content,  # 兼容老签名：可能是 str，也可能是 dict
            design: ArchitectureDesign
    ) -> List[str]:
        """保存Round2结果：兼容单文件与多文件两种返回"""
        output_files: List[str] = []
        timestamp = int(time.time())

        # ---- 新：多文件模式（dict）----
        if isinstance(arxml_content, dict):
            # 组件
            comp_map = arxml_content.get("components", {}) or {}
            outdir = CONFIG.output_dir / "ARXML" / "Components"
            outdir.mkdir(parents=True, exist_ok=True)
            for name, xml_text in comp_map.items():
                fp = outdir / f"{name}_{session_id[:8]}_{timestamp}.arxml"
                with open(fp, "w", encoding="utf-8") as f:
                    f.write(xml_text)
                output_files.append(str(fp))

            # 接口
            intf_map = arxml_content.get("interfaces", {}) or {}
            outdir = CONFIG.output_dir / "ARXML" / "Interfaces"
            outdir.mkdir(parents=True, exist_ok=True)
            for name, xml_text in intf_map.items():
                fp = outdir / f"{name}_{session_id[:8]}_{timestamp}.arxml"
                with open(fp, "w", encoding="utf-8") as f:
                    f.write(xml_text)
                output_files.append(str(fp))

        # ---- 旧：单文件回退（保持兼容）----
        else:
            component_count = len(design.component_plan)
            if component_count <= 5 and component_count > 0:
                first = design.component_plan[0].get("name", "System")
                filename = f"arxml_{first}_{session_id[:8]}_{timestamp}.xml"
            else:
                filename = f"arxml_system_{component_count}comps_{session_id[:8]}_{timestamp}.xml"

            output_path = CONFIG.output_dir / filename
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(arxml_content)
            output_files.append(str(output_path))

        # 验证报告与 ARXML 使用同一会话和时间戳，不隐藏 FAIL/INCOMPLETE。
        session_info = self._get_session_info(session_id)
        validation = (
            session_info.get("results", {}).get("round2", {}).get("validation")
            if session_info else None
        )
        validation_dir = CONFIG.output_dir / "ARXML"
        if validation:
            validation_dir.mkdir(parents=True, exist_ok=True)
            validation_path = validation_dir / f"validation_{session_id[:8]}_{timestamp}.json"
            from ..utils.serializers import save_json
            save_json(validation, validation_path)
            output_files.append(str(validation_path))

        # Persist the hash-pinned retrieval/validation manifest independently.
        round2_result = session_info.get("results", {}).get("round2", {}) if session_info else {}
        validation_context = round2_result.get("validation_context")
        if validation_context:
            validation_dir.mkdir(parents=True, exist_ok=True)
            context_path = validation_dir / f"validation_context_{session_id[:8]}_{timestamp}.json"
            from ..utils.serializers import save_json
            save_json(validation_context, context_path)
            output_files.append(str(context_path))

        # Keep every repair attempt and acceptance decision for audit/replay.
        repair_audit = round2_result.get("auto_repair")
        if repair_audit and repair_audit.get("enabled"):
            validation_dir.mkdir(parents=True, exist_ok=True)
            repair_path = validation_dir / f"repair_audit_{session_id[:8]}_{timestamp}.json"
            from ..utils.serializers import save_json
            save_json(repair_audit, repair_path)
            output_files.append(str(repair_path))

        # 统一写性能报告
        session_info = self._get_session_info(session_id)
        if session_info and "results" in session_info and "round2" in session_info["results"]:
            report_filename = f"performance_{session_id[:8]}_{timestamp}.json"
            report_path = CONFIG.output_dir / report_filename
            performance_data = {
                "session_id": session_id,
                "generation_mode": session_info["results"]["round2"]["generation_mode"],
                "component_count": len(design.component_plan),
                "optimization_metrics": session_info["results"]["round2"].get("optimization_metrics", {}),
                "total_stats": session_info["stats"],
                "timestamp": timestamp
            }
            from ..utils.serializers import save_json
            save_json(performance_data, report_path)
            output_files.append(str(report_path))

        return output_files

    def handle_user_feedback(
        self,
        session_id: str,
        feedback: str
    ) -> Dict[str, Any]:
        """处理用户反馈 - 保持原有实现"""

        # 保持原有的用户反馈处理逻辑
        session_info = self._get_session_info(session_id)

        if not session_info:
            raise ConversationError(f"会话不存在: {session_id}")

        try:
            # 检查修改次数限制
            modification_history = session_info.get("modification_history", [])
            if len(modification_history) >= self.MAX_MODIFICATIONS:
                return {
                    "session_id": session_id,
                    "status": "max_modifications_reached",
                    "state": session_info["state"].value,
                    "response": f"已达到最大修改次数限制({self.MAX_MODIFICATIONS}次)。\n请回复'最终确认'接受当前设计。",
                    "can_proceed": False
                }

            if session_info["state"] not in [ConversationState.ROUND1_COMPLETED, ConversationState.USER_FEEDBACK]:
                raise ConversationError(f"当前状态{session_info['state'].value}不允许接收用户反馈")

            session_info["state"] = ConversationState.USER_FEEDBACK
            current_design = session_info["results"]["round1"]["design"]

            if "modification_history" not in session_info:
                session_info["modification_history"] = []

            response, modified_design, can_proceed = self.user_interaction.handle_user_feedback(
                feedback, current_design
            )

            if modified_design != current_design:
                session_info["modification_history"].append({
                    "feedback": feedback,
                    "timestamp": time.time()
                })
                session_info["results"]["round1"]["design"] = modified_design
                self.memory_manager.update_design_state(session_id, modified_design)

            self.memory_manager.add_conversation_turn(
                session_id=session_id,
                round_number=1,
                user_input=feedback,
                system_output=response,
                design_artifacts=modified_design.__dict__ if isinstance(modified_design, ArchitectureDesign) else modified_design,
                user_feedback=feedback
            )

            if can_proceed:
                session_info["state"] = ConversationState.ROUND1_COMPLETED
                session_info["final_confirmation_time"] = time.time()

                return {
                    "session_id": session_id,
                    "status": "confirmed",
                    "state": session_info["state"].value,
                    "response": response,
                    "can_proceed": True,
                    "message": "设计已最终确认，准备生成详细ARXML"
                }
            else:
                session_info["state"] = ConversationState.USER_FEEDBACK

                return {
                    "session_id": session_id,
                    "status": "modified",
                    "state": session_info["state"].value,
                    "response": response,
                    "can_proceed": False,
                    "message": "设计已修改，请继续确认或提出新的修改要求"
                }

        except Exception as e:
            session_info["state"] = ConversationState.ERROR
            raise ConversationError(f"处理用户反馈失败: {str(e)}")


    def _calculate_context_utilization(self) -> float:
        """计算上下文利用率"""

        # 基于会话统计估算
        if self.total_sessions == 0:
            return 0.0

        # 单批会话表示更好的上下文利用
        return (self.single_batch_sessions / self.total_sessions) * 100

    def _get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话信息"""
        return self.active_sessions.get(session_id)

    def cleanup_session(self, session_id: str) -> bool:
        """清理会话"""
        self.memory_manager.delete_session(session_id)
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            return True
        return False

    def cleanup_expired_sessions(self):
        """清理过期会话"""
        current_time = time.time()
        expired_sessions = []

        for session_id, session_info in self.active_sessions.items():
            if current_time - session_info["start_time"] > CONFIG.conversation.session_ttl:
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            self.cleanup_session(session_id)

        self.memory_manager.cleanup_expired_sessions()

        if expired_sessions and CONFIG.debug_mode:
            print(f"[DEBUG] 清理过期会话: {len(expired_sessions)}个")


# 全局对话管理器实例
conversation_manager = ConversationManager()
