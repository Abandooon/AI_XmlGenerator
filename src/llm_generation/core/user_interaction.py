"""core/user_interaction.py - 用户交互管理

处理Round 1结果的用户确认、反馈和修改
"""
import json
from typing import Dict, List, Any, Optional, Tuple
from ..config import CONFIG
from ..utils.serializers import ArchitectureDesign
from ..utils.exceptions import ConversationError


class UserInteraction:
    """用户交互管理器"""

    def __init__(self):
        """初始化用户交互管理器"""
        self.feedback_patterns = self._build_feedback_patterns()

    def _build_feedback_patterns(self) -> Dict[str, List[str]]:
        """构建反馈模式识别"""
        return {
            "confirm": [
                "确认", "同意", "可以", "好的", "是的", "对的", "正确",
                "confirm", "yes", "ok", "agree", "correct"
            ],
            "modify": [
                "修改", "改变", "调整", "更改", "不对", "错误", "需要",
                "modify", "change", "adjust", "wrong", "need", "should"
            ],
            "reject": [
                "不要", "删除", "去掉", "拒绝", "不需要", "不对",
                "reject", "remove", "delete", "no", "don't"
            ],
            "add": [
                "添加", "增加", "新增", "加上", "还需要",
                "add", "include", "also need", "plus"
            ]
        }

    def present_architecture_design(self, design: ArchitectureDesign) -> str:
        """以用户友好的方式展示架构设计"""

        presentation = []

        # 标题
        presentation.append("🏗️ AUTOSAR组件架构设计")
        presentation.append("=" * 50)

        # 系统分析摘要
        if design.system_analysis:
            presentation.append("\n📋 系统分析")
            presentation.append("-" * 20)

            for key, value in design.system_analysis.items():
                friendly_key = self._translate_key(key)
                presentation.append(f"• {friendly_key}: {value}")

        # 组件规划
        if design.component_plan:
            presentation.append(f"\n🔧 组件规划 ({len(design.component_plan)}个组件)")
            presentation.append("-" * 20)

            for i, component in enumerate(design.component_plan, 1):
                name = component.get('name', f'Component{i}')
                comp_type = component.get('type', 'Unknown')
                purpose = component.get('purpose', '未定义')
                complexity = component.get('estimated_complexity', '未知')

                presentation.append(f"{i}. {name}")
                presentation.append(f"   类型: {self._translate_component_type(comp_type)}")
                presentation.append(f"   功能: {purpose}")
                presentation.append(f"   复杂度: {complexity}")

                if 'port_estimates' in component:
                    ports = component['port_estimates']
                    if 'input_ports' in ports:
                        presentation.append(f"   输入端口: {ports['input_ports']}")
                    if 'output_ports' in ports:
                        presentation.append(f"   输出端口: {ports['output_ports']}")
                presentation.append("")

        # 接口规划
        if design.interface_plan:
            presentation.append(f"\n🔌 接口规划 ({len(design.interface_plan)}个接口)")
            presentation.append("-" * 20)

            for i, interface in enumerate(design.interface_plan, 1):
                name = interface.get('name', f'Interface{i}')
                intf_type = interface.get('type', 'Unknown')
                pattern = interface.get('communication_pattern', '未定义')

                presentation.append(f"{i}. {name}")
                presentation.append(f"   类型: {self._translate_interface_type(intf_type)}")
                presentation.append(f"   通信模式: {pattern}")

                if 'connected_components' in interface:
                    components = interface['connected_components']
                    if components:
                        presentation.append(f"   连接组件: {', '.join(components)}")
                presentation.append("")

        # 连接拓扑
        if design.connection_topology:
            presentation.append("\n🔗 连接拓扑")
            presentation.append("-" * 20)

            topology = design.connection_topology
            if 'component_connections' in topology:
                presentation.append(f"组件连接: {topology['component_connections']}")
            if 'data_flow_paths' in topology:
                presentation.append(f"数据流向: {topology['data_flow_paths']}")
            if 'control_flow_paths' in topology:
                presentation.append(f"控制流向: {topology['control_flow_paths']}")

        # 设计理由
        if design.architecture_rationale:
            presentation.append("\n💡 设计决策")
            presentation.append("-" * 20)

            rationale = design.architecture_rationale
            if 'design_decisions' in rationale:
                presentation.append(f"关键决策: {rationale['design_decisions']}")
            if 'tradeoff_analysis' in rationale:
                presentation.append(f"权衡分析: {rationale['tradeoff_analysis']}")

        # 用户操作提示
        presentation.append("\n" + "=" * 50)
        presentation.append("📝 请审查以上设计并提供反馈:")
        presentation.append("• 如果满意，请回复 '确认' 或 '同意'")
        presentation.append("• 如果需要修改，请具体说明需要调整的地方")
        presentation.append("• 如果需要添加组件或接口，请说明要添加什么")
        presentation.append("• 如果要删除某些部分，请明确指出")

        return "\n".join(presentation)

    def _translate_key(self, key: str) -> str:
        """翻译系统分析的键"""
        translations = {
            "functional_decomposition": "功能分解",
            "data_flow_analysis": "数据流分析",
            "timing_requirements": "时序要求",
            "scalability_considerations": "可扩展性考虑"
        }
        return translations.get(key, key)

    def _translate_component_type(self, comp_type: str) -> str:
        """翻译组件类型"""
        translations = {
            "APPLICATION-SW-COMPONENT-TYPE": "应用软件组件",
            "SENSOR-ACTUATOR-SW-COMPONENT-TYPE": "传感器执行器组件",
            "COMPOSITION-SW-COMPONENT-TYPE": "组合软件组件",
            "PARAMETER-SW-COMPONENT-TYPE": "参数组件"
        }
        return translations.get(comp_type, comp_type)

    def _translate_interface_type(self, intf_type: str) -> str:
        """翻译接口类型"""
        translations = {
            "SENDER-RECEIVER-INTERFACE": "发送接收接口",
            "CLIENT-SERVER-INTERFACE": "客户端服务端接口",
            "MODE-SWITCH-INTERFACE": "模式切换接口",
            "NV-DATA-INTERFACE": "非易失性数据接口"
        }
        return translations.get(intf_type, intf_type)

    def analyze_user_feedback(self, feedback: str) -> Dict[str, Any]:
        """分析用户反馈"""

        feedback_lower = feedback.lower()
        analysis = {
            "intent": "unknown",
            "confidence": 0.0,
            "specific_requests": [],
            "target_elements": [],
            "action_type": "none"
        }

        # 意图识别
        intents = {}
        for intent, patterns in self.feedback_patterns.items():
            matches = sum(1 for pattern in patterns if pattern.lower() in feedback_lower)
            if matches > 0:
                intents[intent] = matches

        if intents:
            # 选择匹配最多的意图
            primary_intent = max(intents.items(), key=lambda x: x[1])
            analysis["intent"] = primary_intent[0]
            analysis["confidence"] = min(primary_intent[1] * 0.3, 1.0)

        # 具体请求分析
        analysis["specific_requests"] = self._extract_specific_requests(feedback)

        # 目标元素分析
        analysis["target_elements"] = self._identify_target_elements(feedback)

        # 动作类型分析
        analysis["action_type"] = self._determine_action_type(analysis["intent"], feedback)

        return analysis

    def _extract_specific_requests(self, feedback: str) -> List[str]:
        """提取具体请求"""
        requests = []

        # 简单的关键词匹配
        if "组件" in feedback:
            requests.append("组件相关")
        if "接口" in feedback:
            requests.append("接口相关")
        if "端口" in feedback:
            requests.append("端口相关")
        if "名称" in feedback or "命名" in feedback:
            requests.append("命名相关")
        if "类型" in feedback:
            requests.append("类型相关")
        if "连接" in feedback:
            requests.append("连接相关")

        return requests

    def _identify_target_elements(self, feedback: str) -> List[str]:
        """识别目标元素"""
        elements = []

        # 组件名称识别（简化实现）
        words = feedback.split()
        for word in words:
            if any(suffix in word.lower() for suffix in ["component", "组件", "comp"]):
                elements.append(word)

        return elements

    def _determine_action_type(self, intent: str, feedback: str) -> str:
        """确定动作类型"""
        if intent == "confirm":
            return "proceed"
        elif intent == "modify":
            return "modify"
        elif intent == "reject":
            return "remove"
        elif intent == "add":
            return "add"
        else:
            return "clarify"

    def handle_user_feedback(
            self,
            feedback: str,
            current_design: ArchitectureDesign
    ) -> Tuple[str, ArchitectureDesign, bool]:
        """处理用户反馈"""

        # 分析反馈
        analysis = self.analyze_user_feedback(feedback)

        if CONFIG.debug_mode:
            print(f"[DEBUG] 反馈分析: {analysis}")

        # 根据分析结果处理
        if analysis["action_type"] == "proceed":
            return self._handle_confirmation(current_design)

        elif analysis["action_type"] == "modify":
            return self._handle_modification(feedback, current_design, analysis)

        elif analysis["action_type"] == "add":
            return self._handle_addition(feedback, current_design, analysis)

        elif analysis["action_type"] == "remove":
            return self._handle_removal(feedback, current_design, analysis)

        else:
            return self._handle_clarification(feedback, current_design)

    def _handle_confirmation(self, design: ArchitectureDesign) -> Tuple[str, ArchitectureDesign, bool]:
        """处理确认反馈"""
        response = "✅ 架构设计已确认！正在生成详细的ARXML内容..."
        return response, design, True  # True表示可以进入Round 2

    def _handle_modification(
            self,
            feedback: str,
            design: ArchitectureDesign,
            analysis: Dict[str, Any]
    ) -> Tuple[str, ArchitectureDesign, bool]:
        """处理修改反馈"""

        modified_design = design
        modifications = []

        # 简化的修改处理逻辑
        if "组件" in feedback and "名称" in feedback:
            # 修改组件名称
            if design.component_plan:
                old_name = design.component_plan[0].get('name', '')
                # 尝试从反馈中提取新名称
                new_name = self._extract_new_name(feedback)
                if new_name:
                    design.component_plan[0]['name'] = new_name
                    modifications.append(f"组件名称从 '{old_name}' 修改为 '{new_name}'")

        if "接口" in feedback and "类型" in feedback:
            # 修改接口类型
            new_type = self._extract_interface_type(feedback)
            if new_type and design.interface_plan:
                design.interface_plan[0]['type'] = new_type
                modifications.append(f"接口类型修改为 '{new_type}'")

        if modifications:
            response = f"🔧 已应用以下修改:\n" + "\n".join([f"• {mod}" for mod in modifications])
            response += "\n\n" + self.present_architecture_design(modified_design)
        else:
            response = "🤔 未能理解具体的修改要求，请更详细地说明需要修改什么。"

        return response, modified_design, False  # False表示需要继续确认

    def _handle_addition(
            self,
            feedback: str,
            design: ArchitectureDesign,
            analysis: Dict[str, Any]
    ) -> Tuple[str, ArchitectureDesign, bool]:
        """处理添加反馈"""

        additions = []

        if "组件" in feedback:
            # 添加新组件
            new_component = {
                "component_id": f"comp_new_{len(design.component_plan) + 1}",
                "name": f"NewComponent{len(design.component_plan) + 1}",
                "type": "APPLICATION-SW-COMPONENT-TYPE",
                "purpose": "根据用户要求添加的组件"
            }
            design.component_plan.append(new_component)
            additions.append("新增一个应用组件")

        if "接口" in feedback:
            # 添加新接口
            new_interface = {
                "interface_id": f"intf_new_{len(design.interface_plan) + 1}",
                "name": f"NewInterface{len(design.interface_plan) + 1}",
                "type": "SENDER-RECEIVER-INTERFACE",
                "communication_pattern": "异步数据传输"
            }
            design.interface_plan.append(new_interface)
            additions.append("新增一个发送接收接口")

        if additions:
            response = f"➕ 已添加以下元素:\n" + "\n".join([f"• {add}" for add in additions])
            response += "\n\n" + self.present_architecture_design(design)
        else:
            response = "🤔 未能理解具体的添加要求，请更详细地说明需要添加什么。"

        return response, design, False

    def _handle_removal(
            self,
            feedback: str,
            design: ArchitectureDesign,
            analysis: Dict[str, Any]
    ) -> Tuple[str, ArchitectureDesign, bool]:
        """处理删除反馈"""

        removals = []

        # 简化的删除逻辑
        if "组件" in feedback and len(design.component_plan) > 1:
            removed_component = design.component_plan.pop()
            removals.append(f"删除组件: {removed_component.get('name', '')}")

        if "接口" in feedback and len(design.interface_plan) > 1:
            removed_interface = design.interface_plan.pop()
            removals.append(f"删除接口: {removed_interface.get('name', '')}")

        if removals:
            response = f"➖ 已删除以下元素:\n" + "\n".join([f"• {rem}" for rem in removals])
            response += "\n\n" + self.present_architecture_design(design)
        else:
            response = "🤔 未能理解具体的删除要求，或者无法删除（需要保留最少的元素）。"

        return response, design, False

    def _handle_clarification(
            self,
            feedback: str,
            design: ArchitectureDesign
    ) -> Tuple[str, ArchitectureDesign, bool]:
        """处理需要澄清的反馈"""

        response = """🤔 我没有完全理解您的反馈，请您更具体地说明:

• 如果要修改某个组件或接口，请说明要修改哪个以及如何修改
• 如果要添加新的元素，请说明要添加什么类型的组件或接口
• 如果要删除某些元素，请明确指出要删除哪个
• 如果对当前设计满意，请直接回复 '确认'

当前设计概要:"""

        response += f"""
• 组件数量: {len(design.component_plan)}
• 接口数量: {len(design.interface_plan)}

您也可以重新查看完整设计或提出新的需求。"""

        return response, design, False

    def _extract_new_name(self, feedback: str) -> Optional[str]:
        """从反馈中提取新名称"""
        # 简单的名称提取逻辑
        words = feedback.split()

        # 查找 "改为" "叫做" "命名为" 等关键词后面的词
        keywords = ["改为", "叫做", "命名为", "改成", "换成"]
        for i, word in enumerate(words):
            if word in keywords and i + 1 < len(words):
                return words[i + 1]

        return None

    def _extract_interface_type(self, feedback: str) -> Optional[str]:
        """从反馈中提取接口类型"""
        feedback_lower = feedback.lower()

        type_mapping = {
            "客户端": "CLIENT-SERVER-INTERFACE",
            "服务端": "CLIENT-SERVER-INTERFACE",
            "服务": "CLIENT-SERVER-INTERFACE",
            "模式": "MODE-SWITCH-INTERFACE",
            "切换": "MODE-SWITCH-INTERFACE",
            "数据": "SENDER-RECEIVER-INTERFACE",
            "发送": "SENDER-RECEIVER-INTERFACE",
            "接收": "SENDER-RECEIVER-INTERFACE"
        }

        for keyword, interface_type in type_mapping.items():
            if keyword in feedback_lower:
                return interface_type

        return None

    def generate_confirmation_prompt(self, design: ArchitectureDesign) -> str:
        """生成确认提示"""
        prompt = "请确认以上架构设计是否符合您的需求。\n\n"
        prompt += "✅ 回复 '确认' 或 '同意' - 如果设计满足需求\n"
        prompt += "🔧 回复具体修改要求 - 如果需要调整\n"
        prompt += "➕ 说明要添加的内容 - 如果需要增加组件或接口\n"
        prompt += "➖ 说明要删除的内容 - 如果需要移除某些部分\n"

        return prompt


# 全局用户交互管理器实例
user_interaction = UserInteraction()