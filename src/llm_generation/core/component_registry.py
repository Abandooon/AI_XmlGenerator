"""core/component_registry.py - 简化的组件注册表

优化为支持直接引用，移除语义占位符处理
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

from ..config import CONFIG
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
    absolute_path: str = ""  # 新增：绝对路径


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
    absolute_path: str = ""  # 新增：组件绝对路径


class ComponentRegistry:
    """简化的组件注册表管理器 - 优化版"""

    def __init__(self):
        """初始化注册表"""
        self.components: Dict[str, ComponentRegistration] = {}
        self.interfaces: Dict[str, ComponentInterface] = {}
        self.path_index: Dict[str, Any] = {}  # 新增：路径索引
        self.session_id: Optional[str] = None

    def initialize_session(
        self,
        component_plans: List[Dict[str, Any]],
        interface_plans: List[Dict[str, Any]]
    ):
        """初始化会话 - 简化版"""

        self.session_id = generate_uuid()
        self.components.clear()
        self.interfaces.clear()
        self.path_index.clear()

        # 预注册所有组件（用于直接引用）
        for comp_plan in component_plans:
            comp_name = comp_plan.get("name", "")
            if comp_name:
                comp_path = f"/Components/{comp_name}"
                self.path_index[comp_path] = {
                    "type": "component",
                    "name": comp_name,
                    "plan": comp_plan
                }

        # 预注册所有接口
        for intf_plan in interface_plans:
            intf_name = intf_plan.get("name", "")
            if intf_name:
                intf_path = f"/Interfaces/{intf_name}"
                self.path_index[intf_path] = {
                    "type": "interface",
                    "name": intf_name,
                    "plan": intf_plan
                }

                # 创建接口信息
                interface_info = ComponentInterface(
                    name=intf_name,
                    type="INTERFACE",
                    interface_type=intf_plan.get("type", ""),
                    description=intf_plan.get("communication_pattern", ""),
                    absolute_path=intf_path
                )
                self.interfaces[intf_name] = interface_info

        if CONFIG.debug_mode:
            print(f"[DEBUG] 初始化注册表: {len(component_plans)}个组件, {len(interface_plans)}个接口")

    def register_generated_component(self, component_data: Dict[str, Any]):
        """注册已生成的组件 - 简化版"""

        comp_name = self._extract_component_name(component_data)
        if not comp_name:
            return

        comp_type = self._extract_component_type(component_data)
        comp_path = f"/Components/{comp_name}"

        # 创建注册信息
        registration = ComponentRegistration(
            component_id=generate_uuid(),
            name=comp_name,
            type=comp_type,
            generated_data=component_data,
            timestamp=generate_uuid(),
            absolute_path=comp_path
        )

        # 提取并注册接口
        interfaces = self._extract_interfaces_direct(component_data, comp_name)
        registration.interfaces = interfaces

        # 注册组件
        self.components[comp_name] = registration

        # 更新路径索引
        self.path_index[comp_path] = {
            "type": "component",
            "name": comp_name,
            "registration": registration
        }

        # 注册端口路径
        for interface in interfaces:
            port_path = f"{comp_path}/Ports/{interface.name}"
            self.path_index[port_path] = {
                "type": "port",
                "component": comp_name,
                "port": interface.name,
                "interface": interface
            }

    def _extract_interfaces_direct(
        self,
        component_data: Dict[str, Any],
        comp_name: str
    ) -> List[ComponentInterface]:
        """提取接口信息 - 使用直接路径"""

        interfaces = []
        comp_path = f"/Components/{comp_name}"

        # 查找PORTS结构
        ports_data = self._find_ports_data(component_data)
        if not ports_data:
            return interfaces

        # 提取P-PORT
        if "P-PORT-PROTOTYPE" in ports_data:
            pports = ports_data["P-PORT-PROTOTYPE"]
            if not isinstance(pports, list):
                pports = [pports]

            for pport in pports:
                if isinstance(pport, dict):
                    port_name = pport.get("SHORT-NAME", "")
                    if port_name:
                        interface = ComponentInterface(
                            name=port_name,
                            type="P-PORT",
                            interface_type="SENDER-RECEIVER-INTERFACE",
                            component_name=comp_name,
                            absolute_path=f"{comp_path}/Ports/{port_name}"
                        )
                        interfaces.append(interface)

        # 提取R-PORT
        if "R-PORT-PROTOTYPE" in ports_data:
            rports = ports_data["R-PORT-PROTOTYPE"]
            if not isinstance(rports, list):
                rports = [rports]

            for rport in rports:
                if isinstance(rport, dict):
                    port_name = rport.get("SHORT-NAME", "")
                    if port_name:
                        interface = ComponentInterface(
                            name=port_name,
                            type="R-PORT",
                            interface_type="SENDER-RECEIVER-INTERFACE",
                            component_name=comp_name,
                            absolute_path=f"{comp_path}/Ports/{port_name}"
                        )
                        interfaces.append(interface)

        return interfaces

    def validate_reference_path(self, path: str) -> bool:
        """验证引用路径的有效性"""

        # 检查路径是否存在于索引中
        return path in self.path_index

    def get_element_by_path(self, path: str) -> Optional[Dict[str, Any]]:
        """通过路径获取元素"""

        return self.path_index.get(path)

    def get_all_valid_paths(self) -> List[str]:
        """获取所有有效路径"""

        return list(self.path_index.keys())

    def get_component_paths(self) -> List[str]:
        """获取所有组件路径"""

        return [
            path for path, info in self.path_index.items()
            if info.get("type") == "component"
        ]

    def get_interface_paths(self) -> List[str]:
        """获取所有接口路径"""

        return [
            path for path, info in self.path_index.items()
            if info.get("type") == "interface"
        ]

    def get_port_paths(self, component_name: str = None) -> List[str]:
        """获取端口路径"""

        port_paths = []
        for path, info in self.path_index.items():
            if info.get("type") == "port":
                if component_name is None or info.get("component") == component_name:
                    port_paths.append(path)
        return port_paths

    def generate_reference_map(self) -> Dict[str, List[str]]:
        """生成引用映射（用于验证）"""

        reference_map = {
            "components": self.get_component_paths(),
            "interfaces": self.get_interface_paths(),
            "ports": self.get_port_paths()
        }

        return reference_map

    def get_component_summaries(self) -> List[Dict[str, Any]]:
        """获取组件摘要 - 包含路径信息"""

        summaries = []
        for comp_name, registration in self.components.items():
            summary = {
                "name": comp_name,
                "type": registration.type,
                "path": registration.absolute_path,
                "interfaces": [
                    {
                        "type": intf.type,
                        "name": intf.name,
                        "path": intf.absolute_path
                    }
                    for intf in registration.interfaces
                ],
                "interface_count": len(registration.interfaces)
            }
            summaries.append(summary)

        return summaries

    def get_interface_summaries(self) -> List[Dict[str, Any]]:
        """获取接口摘要 - 包含路径信息"""

        summaries = []
        for intf_name, interface in self.interfaces.items():
            summary = {
                "name": intf_name,
                "type": interface.interface_type,
                "path": interface.absolute_path,
                "description": interface.description
            }
            summaries.append(summary)

        return summaries

    def validate_all_references(self, arxml_data: Dict[str, Any]) -> Dict[str, Any]:
        """验证所有引用的有效性"""

        validation_result = {
            "valid": True,
            "invalid_references": [],
            "warnings": []
        }

        def check_references(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if isinstance(value, str) and any(ref in key.upper() for ref in ["REF", "TREF"]):
                        # 检查引用格式
                        if value.startswith("/"):
                            if not self.validate_reference_path(value):
                                validation_result["valid"] = False
                                validation_result["invalid_references"].append({
                                    "path": path + "." + key,
                                    "reference": value,
                                    "reason": "路径不存在"
                                })
                        elif not value.startswith("#"):  # 内部引用
                            validation_result["warnings"].append({
                                "path": path + "." + key,
                                "reference": value,
                                "reason": "引用格式不标准"
                            })
                    elif isinstance(value, (dict, list)):
                        check_references(value, path + "." + key)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    check_references(item, path + f"[{i}]")

        check_references(arxml_data)

        return validation_result

    def _extract_component_name(self, component_data: Dict[str, Any]) -> str:
        """提取组件名称"""
        if "SHORT-NAME" in component_data:
            return component_data["SHORT-NAME"]

        for key in component_data.keys():
            if isinstance(component_data[key], dict) and "SHORT-NAME" in component_data[key]:
                return component_data[key]["SHORT-NAME"]

        return ""

    def _extract_component_type(self, component_data: Dict[str, Any]) -> str:
        """提取组件类型"""
        for key in component_data.keys():
            if "COMPONENT-TYPE" in key:
                return key
        return "APPLICATION-SW-COMPONENT-TYPE"

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

    def clear_session(self):
        """清理会话"""
        self.components.clear()
        self.interfaces.clear()
        self.path_index.clear()
        self.session_id = None

    def export_registry(self) -> Dict[str, Any]:
        """导出注册表数据"""

        return {
            "session_id": self.session_id,
            "components": {
                name: {
                    "type": reg.type,
                    "path": reg.absolute_path,
                    "interfaces": [
                        {
                            "name": intf.name,
                            "type": intf.type,
                            "path": intf.absolute_path
                        }
                        for intf in reg.interfaces
                    ]
                }
                for name, reg in self.components.items()
            },
            "interfaces": {
                name: {
                    "type": intf.interface_type,
                    "path": intf.absolute_path
                }
                for name, intf in self.interfaces.items()
            },
            "path_index_size": len(self.path_index)
        }


# 全局组件注册表实例
component_registry = ComponentRegistry()