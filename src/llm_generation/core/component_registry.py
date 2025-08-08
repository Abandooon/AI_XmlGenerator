"""
管理已生成组件的接口信息，支持语义占位符解析
"""
import json
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from ..utils.serializers import generate_uuid


@dataclass
class ComponentInterface:
    """组件接口信息"""
    name: str
    type: str  # P-PORT或R-PORT
    interface_type: str  # SENDER-RECEIVER-INTERFACE等
    data_elements: List[str] = field(default_factory=list)
    description: str = ""
    component_name: str = ""


@dataclass
class ComponentRegistration:
    """组件注册信息"""
    component_id: str
    name: str
    type: str
    interfaces: List[ComponentInterface] = field(default_factory=list)
    generated_data: Dict[str, Any] = field(default_factory=dict)
    generation_batch: int = 0
    timestamp: str = ""


class ComponentRegistry:
    """组件注册表管理器"""

    def __init__(self):
        """初始化注册表"""
        self.components: Dict[str, ComponentRegistration] = {}
        self.interfaces: Dict[str, ComponentInterface] = {}
        self.semantic_map: Dict[str, str] = {}  # 语义描述 -> 实际路径
        self.session_id: Optional[str] = None

    def initialize_session(
            self,
            component_plans: List[Dict[str, Any]],
            interface_plans: List[Dict[str, Any]]
    ):
        """初始化会话"""
        self.session_id = generate_uuid()
        self.components.clear()
        self.interfaces.clear()
        self.semantic_map.clear()

        # 预注册接口计划
        for intf_plan in interface_plans:
            interface_info = ComponentInterface(
                name=intf_plan.get("name", ""),
                type="INTERFACE",
                interface_type=intf_plan.get("type", ""),
                description=intf_plan.get("communication_pattern", "")
            )
            self.interfaces[interface_info.name] = interface_info

    def register_generated_component(self, component_data: Dict[str, Any]):
        """注册已生成的组件"""

        # 提取组件信息
        comp_name = self._extract_component_name(component_data)
        comp_type = self._extract_component_type(component_data)

        if not comp_name:
            return

        # 创建注册信息
        registration = ComponentRegistration(
            component_id=generate_uuid(),
            name=comp_name,
            type=comp_type,
            generated_data=component_data,
            timestamp=generate_uuid()  # 临时使用UUID作为时间戳
        )

        # 提取接口信息
        interfaces = self._extract_interfaces(component_data, comp_name)
        registration.interfaces = interfaces

        # 注册组件
        self.components[comp_name] = registration

        # 更新语义映射
        self._update_semantic_mapping(comp_name, interfaces)

    def _extract_component_name(self, component_data: Dict[str, Any]) -> str:
        """提取组件名称"""
        if "SHORT-NAME" in component_data:
            return component_data["SHORT-NAME"]

        # 从顶级键提取
        for key in component_data.keys():
            if isinstance(component_data[key], dict) and "SHORT-NAME" in component_data[key]:
                return component_data[key]["SHORT-NAME"]

        return ""

    def _extract_component_type(self, component_data: Dict[str, Any]) -> str:
        """提取组件类型"""
        # 从键名推断
        for key in component_data.keys():
            if "COMPONENT-TYPE" in key:
                return key

        return "APPLICATION-SW-COMPONENT-TYPE"

    def _extract_interfaces(
            self,
            component_data: Dict[str, Any],
            comp_name: str
    ) -> List[ComponentInterface]:
        """提取组件接口信息"""

        interfaces = []

        # 查找PORTS结构
        ports_data = self._find_ports_data(component_data)
        if not ports_data:
            return interfaces

        # 提取P-PORT-PROTOTYPE
        if "P-PORT-PROTOTYPE" in ports_data:
            pports = ports_data["P-PORT-PROTOTYPE"]
            if isinstance(pports, list):
                for pport in pports:
                    interface = self._create_interface_from_port(pport, "P-PORT", comp_name)
                    if interface:
                        interfaces.append(interface)
            elif isinstance(pports, dict):
                interface = self._create_interface_from_port(pports, "P-PORT", comp_name)
                if interface:
                    interfaces.append(interface)

        # 提取R-PORT-PROTOTYPE
        if "R-PORT-PROTOTYPE" in ports_data:
            rports = ports_data["R-PORT-PROTOTYPE"]
            if isinstance(rports, list):
                for rport in rports:
                    interface = self._create_interface_from_port(rport, "R-PORT", comp_name)
                    if interface:
                        interfaces.append(interface)
            elif isinstance(rports, dict):
                interface = self._create_interface_from_port(rports, "R-PORT", comp_name)
                if interface:
                    interfaces.append(interface)

        return interfaces

    def _find_ports_data(self, component_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """查找PORTS数据"""

        def search_ports(data):
            if isinstance(data, dict):
                if "PORTS" in data:
                    return data["PORTS"]
                for value in data.values():
                    result = search_ports(value)
                    if result:
                        return result
            return None

        return search_ports(component_data)

    def _create_interface_from_port(
            self,
            port_data: Dict[str, Any],
            port_type: str,
            comp_name: str
    ) -> Optional[ComponentInterface]:
        """从端口数据创建接口信息"""

        port_name = port_data.get("SHORT-NAME", "")
        if not port_name:
            return None

        # 确定接口类型
        interface_ref_key = "PROVIDED-INTERFACE-TREF" if port_type == "P-PORT" else "REQUIRED-INTERFACE-TREF"
        interface_ref = port_data.get(interface_ref_key, "")

        # 推断接口类型
        interface_type = self._infer_interface_type(interface_ref, port_data)

        return ComponentInterface(
            name=port_name,
            type=port_type,
            interface_type=interface_type,
            description=f"{comp_name}的{port_name}端口",
            component_name=comp_name
        )

    def _infer_interface_type(self, interface_ref: str, port_data: Dict[str, Any]) -> str:
        """推断接口类型"""

        # 从引用路径推断
        if "SENDER-RECEIVER" in interface_ref.upper():
            return "SENDER-RECEIVER-INTERFACE"
        elif "CLIENT-SERVER" in interface_ref.upper():
            return "CLIENT-SERVER-INTERFACE"
        elif "MODE-SWITCH" in interface_ref.upper():
            return "MODE-SWITCH-INTERFACE"

        # 默认类型
        return "SENDER-RECEIVER-INTERFACE"

    def _update_semantic_mapping(self, comp_name: str, interfaces: List[ComponentInterface]):
        """更新语义映射"""

        for interface in interfaces:
            # 生成语义描述模式
            semantic_patterns = [
                f"引用{comp_name}的{interface.name}端口",
                f"连接到{comp_name}的{interface.name}",
                f"{comp_name}的{interface.name}接口",
                f"使用{comp_name}提供的{interface.name}"
            ]

            # 生成实际路径
            actual_path = f"/{comp_name}/Ports/{interface.name}"

            # 添加映射
            for pattern in semantic_patterns:
                self.semantic_map[pattern] = actual_path

    def resolve_semantic_reference(self, semantic_description: str) -> Optional[str]:
        """解析语义引用"""

        # 直接匹配
        if semantic_description in self.semantic_map:
            return self.semantic_map[semantic_description]

        # 模糊匹配
        for pattern, path in self.semantic_map.items():
            if self._semantic_match(semantic_description, pattern):
                return path

        return None

    def _semantic_match(self, description: str, pattern: str) -> bool:
        """语义匹配"""

        # 简单的关键词匹配
        desc_words = set(description.lower().split())
        pattern_words = set(pattern.lower().split())

        # 计算交集比例
        intersection = desc_words & pattern_words
        union = desc_words | pattern_words

        if len(union) == 0:
            return False

        similarity = len(intersection) / len(union)
        return similarity > 0.6  # 相似度阈值

    def get_component_summaries(self) -> List[Dict[str, Any]]:
        """获取组件摘要"""

        summaries = []
        for comp_name, registration in self.components.items():
            summary = {
                "name": comp_name,
                "type": registration.type,
                "interfaces": [
                    f"{intf.type}:{intf.name}" for intf in registration.interfaces
                ],
                "interface_count": len(registration.interfaces)
            }
            summaries.append(summary)

        return summaries

    def get_interface_summaries(self) -> List[Dict[str, Any]]:
        """获取接口摘要"""

        summaries = []
        for intf_name, interface in self.interfaces.items():
            summary = {
                "name": intf_name,
                "type": interface.interface_type,
                "description": interface.description
            }
            summaries.append(summary)

        return summaries

    def get_interface_registry(self) -> Dict[str, ComponentInterface]:
        """获取接口注册表"""
        return self.interfaces.copy()

    def get_semantic_mappings(self) -> Dict[str, str]:
        """获取语义映射"""
        return self.semantic_map.copy()

    def clear_session(self):
        """清理会话"""
        self.components.clear()
        self.interfaces.clear()
        self.semantic_map.clear()
        self.session_id = None


# 全局组件注册表实例
component_registry = ComponentRegistry()