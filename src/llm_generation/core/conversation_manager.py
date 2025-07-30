"""core/conversation_manager.py - 对话管理核心

统一管理两轮对话流程，协调各个子模块的交互
移除验证打分逻辑，专注于流程控制和结果输出
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

class ConversationState(Enum):
    """对话状态枚举"""
    INITIALIZED = "initialized"          # 已初始化
    ROUND1_PROCESSING = "round1_processing"  # Round1处理中
    ROUND1_COMPLETED = "round1_completed"    # Round1完成
    USER_FEEDBACK = "user_feedback"      # 等待用户反馈
    ROUND2_PROCESSING = "round2_processing"  # Round2处理中
    ROUND2_COMPLETED = "round2_completed"    # Round2完成
    COMPLETED = "completed"              # 对话完成
    ERROR = "error"                      # 错误状态

class ConversationManager:
    """对话管理核心"""

    def __init__(self):
        """初始化对话管理器"""
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.memory_manager = memory_manager
        self.round1_designer = round1_designer
        self.round2_generator = round2_generator
        self.user_interaction = user_interaction

        # 统计信息
        self.total_sessions = 0
        self.successful_sessions = 0
        self.failed_sessions = 0

    def start_conversation(
        self,
        user_input: str,
        user_id: str = None,
        session_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """启动新对话会话"""

        try:
            # 创建会话
            session_id = self.memory_manager.create_session(user_id)
            self.total_sessions += 1

            # 初始化会话状态
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
                }
            }

            self.active_sessions[session_id] = session_info

            if CONFIG.debug_mode:
                print(f"[DEBUG] 启动新对话: {session_id}")

            return {
                "session_id": session_id,
                "status": "success",
                "state": session_info["state"].value,
                "message": "对话会话已创建，准备开始架构设计..."
            }

        except Exception as e:
            self.failed_sessions += 1
            raise ConversationError(f"启动对话失败: {str(e)}")

    def process_round1(self, session_id: str) -> Dict[str, Any]:
        """执行Round 1架构设计"""

        session_info = self._get_session_info(session_id)
        if not session_info:
            raise ConversationError(f"会话不存在: {session_id}")

        try:
            # 更新状态
            session_info["state"] = ConversationState.ROUND1_PROCESSING
            session_info["current_round"] = 1

            # 获取记忆上下文
            memory_context = self.memory_manager.generate_continuity_prompt(session_id)

            # 分析用户需求
            requirements_analysis = self.round1_designer.analyze_requirements(
                session_info["user_input"]
            )

            # 执行架构设计
            design, stats = self.round1_designer.design_architecture(
                user_requirements=session_info["user_input"],
                design_context=json.dumps(session_info.get("context", {})),
                memory_context=memory_context,
                suggested_patterns=requirements_analysis.get("suggested_patterns", [])
            )

            # 展示设计结果
            presentation = self.user_interaction.present_architecture_design(design)
            confirmation_prompt = self.user_interaction.generate_confirmation_prompt(design)

            # 更新会话状态
            session_info["state"] = ConversationState.ROUND1_COMPLETED
            session_info["results"]["round1"] = {
                "design": design,
                "requirements_analysis": requirements_analysis,
                "presentation": presentation
            }
            session_info["stats"]["round1_tokens"] = stats["total_tokens"]
            session_info["stats"]["total_tokens"] += stats["total_tokens"]

            # 保存到记忆
            self.memory_manager.add_conversation_turn(
                session_id=session_id,
                round_number=1,
                user_input=session_info["user_input"],
                system_output=presentation,
                design_artifacts=design.__dict__
            )

            # 更新设计状态
            self.memory_manager.update_design_state(session_id, design)

            if CONFIG.debug_mode:
                print(f"[DEBUG] Round1完成: {len(design.component_plan)}个组件")

            return {
                "session_id": session_id,
                "status": "success",
                "state": session_info["state"].value,
                "round": 1,
                "design": design.__dict__,
                "presentation": presentation,
                "confirmation_prompt": confirmation_prompt,
                "stats": stats,
                "message": "架构设计已完成，请确认或提供修改意见"
            }

        except Exception as e:
            session_info["state"] = ConversationState.ERROR
            raise ArchitectureDesignError(f"Round1执行失败: {str(e)}")

    def handle_user_feedback(
        self,
        session_id: str,
        feedback: str
    ) -> Dict[str, Any]:
        """处理用户反馈"""

        session_info = self._get_session_info(session_id)
        if not session_info:
            raise ConversationError(f"会话不存在: {session_id}")

        try:
            # 检查当前状态
            if session_info["state"] != ConversationState.ROUND1_COMPLETED:
                raise ConversationError("当前状态不允许接收用户反馈")

            # 更新状态
            session_info["state"] = ConversationState.USER_FEEDBACK

            # 获取当前设计
            current_design = session_info["results"]["round1"]["design"]

            # 处理反馈
            response, modified_design, can_proceed = self.user_interaction.handle_user_feedback(
                feedback, current_design
            )

            # 更新设计（如果有修改）
            if modified_design != current_design:
                session_info["results"]["round1"]["design"] = modified_design
                self.memory_manager.update_design_state(session_id, modified_design)

            # 保存反馈到记忆
            self.memory_manager.add_conversation_turn(
                session_id=session_id,
                round_number=1,
                user_input=feedback,
                system_output=response,
                design_artifacts=modified_design.__dict__ if isinstance(modified_design, ArchitectureDesign) else modified_design,
                user_feedback=feedback
            )

            if can_proceed:
                # 用户确认，准备进入Round2
                session_info["state"] = ConversationState.ROUND1_COMPLETED
                return {
                    "session_id": session_id,
                    "status": "confirmed",
                    "state": session_info["state"].value,
                    "response": response,
                    "can_proceed": True,
                    "message": "设计已确认，准备生成详细ARXML"
                }
            else:
                # 需要继续修改
                session_info["state"] = ConversationState.ROUND1_COMPLETED
                return {
                    "session_id": session_id,
                    "status": "modified",
                    "state": session_info["state"].value,
                    "response": response,
                    "modified_design": modified_design.__dict__ if isinstance(modified_design, ArchitectureDesign) else modified_design,
                    "can_proceed": False,
                    "message": "设计已修改，请继续确认"
                }

        except Exception as e:
            session_info["state"] = ConversationState.ERROR
            raise ConversationError(f"处理用户反馈失败: {str(e)}")

    def process_round2(
        self,
        session_id: str,
        custom_requirements: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """执行Round 2详细生成"""

        session_info = self._get_session_info(session_id)
        if not session_info:
            raise ConversationError(f"会话不存在: {session_id}")

        try:
            # 检查状态
            if session_info["state"] != ConversationState.ROUND1_COMPLETED:
                raise ConversationError("必须先完成Round1并确认设计")

            # 更新状态
            session_info["state"] = ConversationState.ROUND2_PROCESSING
            session_info["current_round"] = 2

            # 获取确认的设计
            confirmed_design = session_info["results"]["round1"]["design"]

            # 获取记忆上下文
            memory_context = self.memory_manager.generate_continuity_prompt(session_id)

            # 执行详细生成
            arxml_data, stats = self.round2_generator.generate_arxml(
                architecture_design=confirmed_design,
                memory_context=memory_context,
                custom_requirements=custom_requirements
            )

            # 更新会话状态
            session_info["state"] = ConversationState.ROUND2_COMPLETED
            session_info["results"]["round2"] = {
                "arxml_data": arxml_data
            }
            session_info["stats"]["round2_tokens"] = stats["total_tokens"]
            session_info["stats"]["total_tokens"] += stats["total_tokens"]

            # 保存结果
            output_files = self._save_results(session_id, arxml_data, confirmed_design)

            # 保存到记忆
            self.memory_manager.add_conversation_turn(
                session_id=session_id,
                round_number=2,
                user_input="生成详细ARXML",
                system_output="ARXML已生成",
                design_artifacts={"arxml_files": [str(f) for f in output_files]}
            )

            # 标记对话完成
            session_info["state"] = ConversationState.COMPLETED
            self.successful_sessions += 1

            if CONFIG.debug_mode:
                print(f"[DEBUG] Round2完成: 生成{len(output_files)}个文件")

            return {
                "session_id": session_id,
                "status": "success",
                "state": session_info["state"].value,
                "round": 2,
                "arxml_data": arxml_data,
                "output_files": [str(f) for f in output_files],
                "stats": stats,
                "total_stats": session_info["stats"],
                "message": f"ARXML文档已成功生成！共{len(output_files)}个文件。"
            }

        except Exception as e:
            session_info["state"] = ConversationState.ERROR
            self.failed_sessions += 1
            raise ValidationError(f"Round2执行失败: {str(e)}")

    def get_conversation_state(self, session_id: str) -> Dict[str, Any]:
        """获取对话状态"""

        session_info = self._get_session_info(session_id)
        if not session_info:
            return {"error": "会话不存在"}

        # 获取记忆摘要
        memory_summary = self.memory_manager.get_context_summary(session_id)

        state_info = {
            "session_id": session_id,
            "state": session_info["state"].value,
            "current_round": session_info["current_round"],
            "start_time": session_info["start_time"],
            "elapsed_time": time.time() - session_info["start_time"],
            "user_id": session_info.get("user_id"),
            "stats": session_info["stats"],
            "memory_summary": memory_summary
        }

        # 添加各轮次结果
        if "round1" in session_info["results"]:
            state_info["round1_completed"] = True
            r1_design = session_info["results"]["round1"]["design"]
            state_info["round1_components"] = len(r1_design.component_plan) if hasattr(r1_design, 'component_plan') else 0

        if "round2" in session_info["results"]:
            state_info["round2_completed"] = True
            r2_data = session_info["results"]["round2"]["arxml_data"]
            state_info["round2_output_size"] = len(str(r2_data)) if r2_data else 0

        return state_info

    def _get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话信息"""
        return self.active_sessions.get(session_id)

    # conversation_manager.py 修正
    def _save_results(self, session_id: str, arxml_content: str, design: ArchitectureDesign) -> List[str]:
        """保存生成结果 - 修正：arxml_content现在是XML字符串"""

        output_files = []
        timestamp = int(time.time())

        # 保存XML文件
        if len(design.component_plan) == 1:
            # 单组件：保存为XML文件
            comp_name = design.component_plan[0].get('name', 'Component')
            filename = f"arxml_{comp_name}_{session_id[:8]}_{timestamp}.xml"
            output_path = CONFIG.output_dir / filename

            # 直接保存XML字符串
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(arxml_content)
            output_files.append(output_path)
        else:
            # 多组件：保存为单个XML文件
            filename = f"arxml_multi_{session_id[:8]}_{timestamp}.xml"
            output_path = CONFIG.output_dir / filename

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(arxml_content)
            output_files.append(output_path)

        # 保存会话摘要JSON
        summary_filename = f"session_{session_id[:8]}_{timestamp}.json"
        summary_path = CONFIG.output_dir / summary_filename

        session_info = self._get_session_info(session_id)
        if session_info:
            summary_data = {
                "session_id": session_id,
                "user_input": session_info["user_input"],
                "state": session_info["state"].value,
                "stats": session_info["stats"],
                "component_count": len(design.component_plan),
                "interface_count": len(design.interface_plan),
                "round1_design": design.__dict__,
                "arxml_files": [f.name for f in output_files]
            }

            save_json(summary_data, summary_path)

        return output_files

    def _extract_component_name(self, key: str, value: Any) -> str:
        """从组件数据中提取组件名称"""

        if isinstance(value, dict) and "SHORT-NAME" in value:
            return value["SHORT-NAME"]

        # 从key中提取
        if "_" in key:
            parts = key.split("_")
            if len(parts) > 1:
                return parts[-1]  # 取最后一部分作为名称

        return "Component"

    def cleanup_session(self, session_id: str) -> bool:
        """清理会话"""

        # 清理记忆
        self.memory_manager.delete_session(session_id)

        # 清理活跃会话
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            return True

        return False

    def cleanup_expired_sessions(self):
        """清理过期会话"""

        current_time = time.time()
        expired_sessions = []

        for session_id, session_info in self.active_sessions.items():
            # 检查会话是否超时（24小时）
            if current_time - session_info["start_time"] > CONFIG.conversation.session_ttl:
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            self.cleanup_session(session_id)

        # 清理记忆管理器中的过期会话
        self.memory_manager.cleanup_expired_sessions()

        if expired_sessions and CONFIG.debug_mode:
            print(f"[DEBUG] 清理过期会话: {len(expired_sessions)}个")

    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""

        # 汇总各组件统计
        stats = {
            "conversation_manager": {
                "total_sessions": self.total_sessions,
                "successful_sessions": self.successful_sessions,
                "failed_sessions": self.failed_sessions,
                "active_sessions": len(self.active_sessions),
                "success_rate": self.successful_sessions / max(self.total_sessions, 1)
            },
            "memory_manager": self.memory_manager.get_stats(),
            "llm_client": self.round1_designer.gemini_client.get_stats() if hasattr(self.round1_designer.gemini_client, 'get_stats') else {},
            "constraint_engine": self.round2_generator.constraint_engine.get_stats()
        }

        return stats

    def export_session_data(self, session_id: str) -> Dict[str, Any]:
        """导出会话数据"""

        session_info = self._get_session_info(session_id)
        if not session_info:
            raise ConversationError(f"会话不存在: {session_id}")

        # 获取完整的会话数据
        session_data = session_info.copy()

        # 获取记忆数据
        memory_data = self.memory_manager.get_context_summary(session_id)
        session_data["memory_context"] = memory_data

        # 序列化状态枚举
        session_data["state"] = session_data["state"].value

        return session_data

    def list_active_sessions(self) -> List[Dict[str, Any]]:
        """列出活跃会话"""

        sessions = []
        for session_id, session_info in self.active_sessions.items():
            session_summary = {
                "session_id": session_id,
                "state": session_info["state"].value,
                "current_round": session_info["current_round"],
                "start_time": session_info["start_time"],
                "user_id": session_info.get("user_id"),
                "elapsed_time": time.time() - session_info["start_time"],
                "component_count": 0
            }

            # 添加组件数量信息
            if "round1" in session_info.get("results", {}):
                design = session_info["results"]["round1"].get("design")
                if hasattr(design, 'component_plan'):
                    session_summary["component_count"] = len(design.component_plan)

            sessions.append(session_summary)

        return sessions

# 全局对话管理器实例
conversation_manager = ConversationManager()