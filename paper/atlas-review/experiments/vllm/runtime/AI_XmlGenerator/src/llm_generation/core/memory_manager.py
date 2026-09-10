"""core/memory_manager.py - 短期记忆管理

管理会话级别的短期记忆，支持对话上下文保持和用户偏好学习
"""
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from ..config import CONFIG
from ..utils.exceptions import MemoryError
from ..utils.serializers import SessionMemory, ConversationTurn, ArchitectureDesign, generate_uuid


class MemoryManager:
    """短期记忆管理器"""

    def __init__(self):
        """初始化记忆管理器"""
        self.config = CONFIG.memory
        self.sessions: Dict[str, SessionMemory] = {}
        self.user_preferences: Dict[str, Dict[str, Any]] = {}

        # 简化实现：使用内存存储，实际可接入Redis
        self.storage_backend = "memory"

    def create_session(self, user_id: str = None) -> str:
        """创建新会话"""
        session_id = generate_uuid()

        session = SessionMemory(
            session_id=session_id,
            start_time=datetime.now().isoformat(),
            current_round=0,
            conversation_history=[],
            accumulated_context=self._init_context(user_id)
        )

        self.sessions[session_id] = session

        if CONFIG.debug_mode:
            print(f"[DEBUG] 创建新会话: {session_id}")

        return session_id

    def _init_context(self, user_id: str = None) -> Dict[str, Any]:
        """初始化会话上下文"""
        context = {
            "user_id": user_id,
            "domain_preferences": {},
            "design_patterns_used": [],
            "rejected_options": [],
            "confirmed_decisions": [],
            "last_activity": datetime.now().isoformat()
        }

        # 如果有用户偏好，加载到上下文
        if user_id and user_id in self.user_preferences:
            context["domain_preferences"] = self.user_preferences[user_id].copy()

        return context

    def get_session(self, session_id: str) -> Optional[SessionMemory]:
        """获取会话信息"""
        if session_id not in self.sessions:
            return None

        session = self.sessions[session_id]

        # 检查会话是否过期
        if self._is_session_expired(session):
            self.delete_session(session_id)
            return None

        return session

    def _is_session_expired(self, session: SessionMemory) -> bool:
        """检查会话是否过期"""
        try:
            start_time = datetime.fromisoformat(session.start_time)
            expiry_time = start_time + timedelta(seconds=self.config.session_ttl)
            return datetime.now() > expiry_time
        except Exception:
            return True

    def add_conversation_turn(
            self,
            session_id: str,
            round_number: int,
            user_input: str,
            system_output: str,
            design_artifacts: Dict[str, Any] = None,
            user_feedback: str = None
    ) -> bool:
        """添加对话轮次"""
        session = self.get_session(session_id)
        if not session:
            raise MemoryError(f"会话不存在: {session_id}")

        turn = ConversationTurn(
            round_number=round_number,
            user_input=user_input,
            system_output=system_output,
            design_artifacts=design_artifacts or {},
            user_feedback=user_feedback
        )

        session.conversation_history.append(turn)
        session.current_round = round_number

        # 更新accumulated_context
        self._update_accumulated_context(session, turn)

        # 限制历史记录长度
        if len(session.conversation_history) > self.config.max_session_history:
            session.conversation_history = session.conversation_history[-self.config.max_session_history:]

        if CONFIG.debug_mode:
            print(f"[DEBUG] 添加对话轮次: 会话{session_id}, 轮次{round_number}")

        return True

    def _update_accumulated_context(self, session: SessionMemory, turn: ConversationTurn):
        """更新累积上下文"""
        context = session.accumulated_context

        # 更新最后活动时间
        context["last_activity"] = turn.timestamp

        # 分析设计偏好
        if turn.design_artifacts:
            self._analyze_design_preferences(context, turn.design_artifacts)

        # 分析用户反馈
        if turn.user_feedback:
            self._analyze_user_feedback(context, turn.user_feedback)

    def _analyze_design_preferences(self, context: Dict[str, Any], artifacts: Dict[str, Any]):
        """分析设计偏好"""
        # 组件类型偏好
        if "component_plan" in artifacts:
            for component in artifacts["component_plan"]:
                comp_type = component.get("type", "")
                if comp_type:
                    if "component_type_frequency" not in context:
                        context["component_type_frequency"] = {}
                    context["component_type_frequency"][comp_type] = \
                        context["component_type_frequency"].get(comp_type, 0) + 1

        # 接口类型偏好
        if "interface_plan" in artifacts:
            for interface in artifacts["interface_plan"]:
                intf_type = interface.get("type", "")
                if intf_type:
                    if "interface_type_frequency" not in context:
                        context["interface_type_frequency"] = {}
                    context["interface_type_frequency"][intf_type] = \
                        context["interface_type_frequency"].get(intf_type, 0) + 1

        # 命名模式
        if "component_plan" in artifacts:
            for component in artifacts["component_plan"]:
                name = component.get("name", "")
                if name:
                    if "naming_patterns" not in context:
                        context["naming_patterns"] = []
                    # 简单的命名模式分析
                    if "_" in name:
                        if "underscore_naming" not in context["naming_patterns"]:
                            context["naming_patterns"].append("underscore_naming")
                    if name.isupper():
                        if "uppercase_naming" not in context["naming_patterns"]:
                            context["naming_patterns"].append("uppercase_naming")

    def _analyze_user_feedback(self, context: Dict[str, Any], feedback: str):
        """分析用户反馈"""
        feedback_lower = feedback.lower()

        # 分析拒绝的选项
        if any(word in feedback_lower for word in ["不要", "不需要", "去掉", "删除"]):
            context["rejected_options"].append({
                "feedback": feedback,
                "timestamp": datetime.now().isoformat()
            })

        # 分析确认的决策
        if any(word in feedback_lower for word in ["好的", "确认", "同意", "可以"]):
            context["confirmed_decisions"].append({
                "feedback": feedback,
                "timestamp": datetime.now().isoformat()
            })

    def update_design_state(self, session_id: str, design: ArchitectureDesign) -> bool:
        """更新设计状态"""
        session = self.get_session(session_id)
        if not session:
            raise MemoryError(f"会话不存在: {session_id}")

        session.current_design_state = design

        if CONFIG.debug_mode:
            print(f"[DEBUG] 更新设计状态: 会话{session_id}")

        return True

    def get_context_summary(self, session_id: str) -> Dict[str, Any]:
        """获取上下文摘要"""
        session = self.get_session(session_id)
        if not session:
            return {}

        # 生成上下文摘要
        summary = {
            "session_info": {
                "session_id": session.session_id,
                "current_round": session.current_round,
                "conversation_count": len(session.conversation_history),
                "start_time": session.start_time
            },
            "user_preferences": self._extract_user_preferences(session),
            "design_history": self._extract_design_history(session),
            "recent_decisions": self._extract_recent_decisions(session)
        }

        return summary

    def _extract_user_preferences(self, session: SessionMemory) -> Dict[str, Any]:
        """提取用户偏好"""
        context = session.accumulated_context

        preferences = {}

        # 组件类型偏好
        if "component_type_frequency" in context:
            freq = context["component_type_frequency"]
            if freq:
                most_used = max(freq.items(), key=lambda x: x[1])
                preferences["preferred_component_type"] = most_used[0]

        # 接口类型偏好
        if "interface_type_frequency" in context:
            freq = context["interface_type_frequency"]
            if freq:
                most_used = max(freq.items(), key=lambda x: x[1])
                preferences["preferred_interface_type"] = most_used[0]

        # 命名模式偏好
        if "naming_patterns" in context:
            preferences["naming_patterns"] = context["naming_patterns"]

        return preferences

    def _extract_design_history(self, session: SessionMemory) -> List[Dict[str, Any]]:
        """提取设计历史"""
        history = []

        for turn in session.conversation_history:
            if turn.design_artifacts:
                history.append({
                    "round": turn.round_number,
                    "timestamp": turn.timestamp,
                    "artifacts": turn.design_artifacts,
                    "user_feedback": turn.user_feedback
                })

        return history

    def _extract_recent_decisions(self, session: SessionMemory, limit: int = 5) -> List[Dict[str, Any]]:
        """提取最近的决策"""
        decisions = []

        # 从确认的决策中提取
        confirmed = session.accumulated_context.get("confirmed_decisions", [])
        decisions.extend(confirmed[-limit:])

        # 从拒绝的选项中提取
        rejected = session.accumulated_context.get("rejected_options", [])
        decisions.extend(rejected[-limit:])

        # 按时间排序
        decisions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        return decisions[:limit]

    def generate_continuity_prompt(self, session_id: str) -> str:
        """生成连续性提示词"""
        session = self.get_session(session_id)
        if not session or not session.conversation_history:
            return ""

        summary = self.get_context_summary(session_id)

        prompt_lines = ["## 对话上下文"]

        # 会话信息
        prompt_lines.append(f"当前是第 {summary['session_info']['current_round']} 轮对话")

        # 用户偏好
        preferences = summary.get("user_preferences", {})
        if preferences:
            prompt_lines.append("\n### 用户偏好")
            if "preferred_component_type" in preferences:
                prompt_lines.append(f"- 偏好组件类型: {preferences['preferred_component_type']}")
            if "preferred_interface_type" in preferences:
                prompt_lines.append(f"- 偏好接口类型: {preferences['preferred_interface_type']}")
            if "naming_patterns" in preferences:
                prompt_lines.append(f"- 命名模式: {', '.join(preferences['naming_patterns'])}")

        # 最近决策
        recent_decisions = summary.get("recent_decisions", [])
        if recent_decisions:
            prompt_lines.append("\n### 最近决策")
            for decision in recent_decisions[:3]:  # 只显示最近3个
                prompt_lines.append(f"- {decision.get('feedback', '')}")

        # 当前设计状态
        if session.current_design_state:
            prompt_lines.append("\n### 当前设计状态")
            design = session.current_design_state
            if design.component_plan:
                prompt_lines.append(f"- 组件数量: {len(design.component_plan)}")
            if design.interface_plan:
                prompt_lines.append(f"- 接口数量: {len(design.interface_plan)}")

        prompt_lines.append("\n请基于以上上下文继续对话，保持设计的连续性和一致性。")

        return "\n".join(prompt_lines)

    def save_user_preferences(self, user_id: str, preferences: Dict[str, Any]):
        """保存用户偏好"""
        self.user_preferences[user_id] = preferences

        if CONFIG.debug_mode:
            print(f"[DEBUG] 保存用户偏好: {user_id}")

    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]

            if CONFIG.debug_mode:
                print(f"[DEBUG] 删除会话: {session_id}")

            return True
        return False

    def cleanup_expired_sessions(self):
        """清理过期会话"""
        expired_sessions = []

        for session_id, session in self.sessions.items():
            if self._is_session_expired(session):
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            self.delete_session(session_id)

        if expired_sessions and CONFIG.debug_mode:
            print(f"[DEBUG] 清理过期会话: {len(expired_sessions)}个")

    def get_stats(self) -> Dict[str, Any]:
        """获取记忆管理器统计信息"""
        active_sessions = len(self.sessions)
        total_conversations = sum(len(session.conversation_history) for session in self.sessions.values())

        return {
            "active_sessions": active_sessions,
            "total_conversations": total_conversations,
            "user_preferences_count": len(self.user_preferences),
            "storage_backend": self.storage_backend
        }


# 全局记忆管理器实例
memory_manager = MemoryManager()