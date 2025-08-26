"""core/conversation_manager.py - 优化的对话管理核心

简化流程，充分利用长上下文能力
"""
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from ..config import CONFIG
from ..utils.serializers import ArchitectureDesign, generate_uuid, save_json
from ..utils.exceptions import ConversationError, ArchitectureDesignError, ValidationError
from .memory_manager import memory_manager
from .round1_designer import round1_designer
from .round2_generator import round2_generator
from .user_interaction import user_interaction
from .dependency_analyzer import dependency_analyzer


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
        self.single_batch_sessions = 0  # 新增：单批生成的会话数
        self.multi_batch_sessions = 0   # 新增：多批生成的会话数

    def start_conversation(
        self,
        user_input: str,
        user_id: str = None,
        session_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """启动新对话会话"""

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
                "results": {},
                "stats": {
                    "total_tokens": 0,
                    "round1_tokens": 0,
                    "round2_tokens": 0
                },
                "optimization_info": {}  # 新增：优化信息
            }

            self.active_sessions[session_id] = session_info

            # 预分析系统规模
            self._analyze_system_scale(session_info, user_input)

            if CONFIG.debug_mode:
                print(f"[DEBUG] 启动新对话: {session_id}")
                print(f"[DEBUG] 预估系统规模: {session_info['optimization_info']}")

            return {
                "session_id": session_id,
                "status": "success",
                "state": session_info["state"].value,
                "optimization_hint": session_info.get("optimization_info", {}),
                "message": "对话会话已创建，准备开始架构设计..."
            }

        except Exception as e:
            self.failed_sessions += 1
            raise ConversationError(f"启动对话失败: {str(e)}")

    def process_round1(self, session_id: str) -> Dict[str, Any]:
        """执行Round 1架构设计 - 增强版"""

        session_info = self._get_session_info(session_id)
        if not session_info:
            raise ConversationError(f"会话不存在: {session_id}")

        try:
            session_info["state"] = ConversationState.ROUND1_PROCESSING
            session_info["current_round"] = 1

            memory_context = self.memory_manager.generate_continuity_prompt(session_id)

            # 分析需求 - 增强版
            requirements_analysis = self.round1_designer.analyze_requirements(
                session_info["user_input"]
            )

            # 根据预分析结果提供设计指导
            design_guidance = self._generate_design_guidance(session_info, requirements_analysis)

            # 执行架构设计
            design, stats = self.round1_designer.design_architecture(
                user_requirements=session_info["user_input"],
                design_context=json.dumps({
                    **session_info.get("context", {}),
                    "optimization_info": session_info.get("optimization_info", {}),
                    "design_guidance": design_guidance
                }),
                memory_context=memory_context,
                suggested_patterns=requirements_analysis.get("suggested_patterns", [])
            )

            # 分析生成策略
            generation_strategy = self._analyze_generation_strategy(design)
            session_info["optimization_info"]["generation_strategy"] = generation_strategy

            # 展示设计结果
            presentation = self.user_interaction.present_architecture_design(design)

            # 添加优化建议
            if generation_strategy.get("recommended_strategy") == "single_batch":
                presentation += "\n\n✨ 优化提示：系统规模适合一次性生成，将获得最佳一致性。"

            confirmation_prompt = self.user_interaction.generate_confirmation_prompt(design)

            session_info["state"] = ConversationState.ROUND1_COMPLETED
            session_info["results"]["round1"] = {
                "design": design,
                "requirements_analysis": requirements_analysis,
                "presentation": presentation,
                "generation_strategy": generation_strategy
            }
            session_info["stats"]["round1_tokens"] = stats["total_tokens"]
            session_info["stats"]["total_tokens"] += stats["total_tokens"]

            self.memory_manager.add_conversation_turn(
                session_id=session_id,
                round_number=1,
                user_input=session_info["user_input"],
                system_output=presentation,
                design_artifacts=design.__dict__
            )

            self.memory_manager.update_design_state(session_id, design)

            if CONFIG.debug_mode:
                print(f"[DEBUG] Round1完成: {len(design.component_plan)}个组件")
                print(f"[DEBUG] 建议策略: {generation_strategy.get('recommended_strategy')}")

            return {
                "session_id": session_id,
                "status": "success",
                "state": session_info["state"].value,
                "round": 1,
                "design": design.__dict__,
                "presentation": presentation,
                "confirmation_prompt": confirmation_prompt,
                "generation_strategy": generation_strategy,  # 新增
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
        """执行Round 2详细生成 - 优化版"""

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
            generation_strategy = session_info["results"]["round1"].get("generation_strategy", {})

            component_count = len(confirmed_design.component_plan)

            # 记录生成模式统计
            if component_count <= CONFIG.generation.single_batch_threshold:
                self.single_batch_sessions += 1
                generation_mode = "unified_batch"
            else:
                self.multi_batch_sessions += 1
                generation_mode = "intelligent_batch"

            if CONFIG.debug_mode:
                print(f"[DEBUG] Round2生成模式: {generation_mode}")
                print(f"[DEBUG] 组件数量: {component_count}")
                print(f"[DEBUG] 建议策略: {generation_strategy.get('recommended_strategy')}")
                print(f"[DEBUG] 预估Token: {generation_strategy.get('estimated_tokens', 'N/A')}")

            memory_context = self.memory_manager.generate_continuity_prompt(session_id)

            # 添加优化要求
            if custom_requirements is None:
                custom_requirements = {}
            custom_requirements["optimization_mode"] = generation_mode
            custom_requirements["enable_direct_references"] = True
            custom_requirements["schema_depth"] = CONFIG.generation.max_schema_injection_depth

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
                "optimization_metrics": stats.get("performance_metrics", {})
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
            self.successful_sessions += 1

            # 性能报告
            performance_report = self._generate_performance_report(session_info, stats)

            if CONFIG.debug_mode:
                print(f"[DEBUG] Round2完成: {len(output_files)}个文件")
                print(f"[DEBUG] Token效率: {stats.get('tokens_per_component', 'N/A')} tokens/组件")
                print(f"[DEBUG] 生成时间: {stats.get('generation_time', 'N/A')}秒")

            return {
                "session_id": session_id,
                "status": "success",
                "state": session_info["state"].value,
                "round": 2,
                "arxml_data": arxml_data,
                "output_files": [str(f) for f in output_files],
                "stats": stats,
                "total_stats": session_info["stats"],
                "generation_mode": generation_mode,
                "performance_report": performance_report,  # 新增
                "message": f"ARXML文档已成功生成！共{len(output_files)}个文件，使用{generation_mode}模式。"
            }

        except Exception as e:
            session_info["state"] = ConversationState.ERROR
            self.failed_sessions += 1
            raise ValidationError(f"Round2执行失败: {str(e)}")

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

    def _generate_design_guidance(
        self,
        session_info: Dict[str, Any],
        requirements_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成设计指导"""

        optimization_info = session_info.get("optimization_info", {})

        guidance = {
            "target_component_count": optimization_info.get("estimated_components", 8),
            "prefer_simple_architecture": optimization_info.get("estimated_scale") == "small",
            "enable_direct_references": True,
            "use_standard_patterns": True,
            "optimization_focus": "consistency" if optimization_info.get("estimated_scale") != "large" else "scalability"
        }

        return guidance

    def _analyze_generation_strategy(self, design: ArchitectureDesign) -> Dict[str, Any]:
        """分析最佳生成策略"""

        return self.dependency_analyzer.get_optimization_suggestions(design.component_plan)

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
        arxml_content: str,
        design: ArchitectureDesign
    ) -> List[str]:
        """保存优化的结果"""

        output_files = []
        timestamp = int(time.time())

        # 保存ARXML文件
        component_count = len(design.component_plan)
        if component_count <= 5:
            filename = f"arxml_{design.component_plan[0].get('name', 'System')}_{session_id[:8]}_{timestamp}.xml"
        else:
            filename = f"arxml_system_{component_count}comps_{session_id[:8]}_{timestamp}.xml"

        output_path = CONFIG.output_dir / filename

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(arxml_content)
        output_files.append(output_path)

        # 保存性能报告
        session_info = self._get_session_info(session_id)
        if session_info and "results" in session_info and "round2" in session_info["results"]:
            report_filename = f"performance_{session_id[:8]}_{timestamp}.json"
            report_path = CONFIG.output_dir / report_filename

            performance_data = {
                "session_id": session_id,
                "generation_mode": session_info["results"]["round2"]["generation_mode"],
                "component_count": component_count,
                "optimization_metrics": session_info["results"]["round2"].get("optimization_metrics", {}),
                "total_stats": session_info["stats"],
                "timestamp": timestamp
            }

            save_json(performance_data, report_path)
            output_files.append(report_path)

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

    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息 - 增强版"""

        stats = {
            "conversation_manager": {
                "total_sessions": self.total_sessions,
                "successful_sessions": self.successful_sessions,
                "failed_sessions": self.failed_sessions,
                "active_sessions": len(self.active_sessions),
                "success_rate": self.successful_sessions / max(self.total_sessions, 1),
                "single_batch_sessions": self.single_batch_sessions,  # 新增
                "multi_batch_sessions": self.multi_batch_sessions,    # 新增
                "single_batch_ratio": self.single_batch_sessions / max(self.total_sessions, 1)  # 新增
            },
            "optimization_metrics": {
                "average_single_batch_threshold": CONFIG.generation.single_batch_threshold,
                "max_batch_size": CONFIG.generation.max_batch_size,
                "schema_injection_depth": CONFIG.generation.max_schema_injection_depth,
                "long_context_utilization": self._calculate_context_utilization()
            },
            "memory_manager": self.memory_manager.get_stats()
        }

        return stats

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