"""knowledge/terminology_builder.py - 高层术语库构建

从元模型定义中提取核心概念，为Round 1提供纯粹的元模型信息
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class AttributeDefinition:
    """属性定义"""
    tag: str
    description: str
    min_occurs: int
    max_occurs: int  # -1表示无限制


@dataclass
class ComponentTypeDefinition:
    """组件类型定义"""
    name: str
    description: str
    is_abstract: bool
    parent_type: Optional[str] = None
    attributes: List[AttributeDefinition] = field(default_factory=list)
    sub_types: List['ComponentTypeDefinition'] = field(default_factory=list)


@dataclass
class InterfaceTypeDefinition:
    """接口类型定义"""
    name: str
    description: str
    is_abstract: bool
    parent_type: Optional[str] = None
    attributes: List[AttributeDefinition] = field(default_factory=list)
    sub_types: List['InterfaceTypeDefinition'] = field(default_factory=list)


@dataclass
class ModeDeclarationGroupDefinition:
    """模式声明组定义"""
    name: str = "MODE-DECLARATION-GROUP"
    description: str = "Mode declaration group for mode management"
    attributes: List[AttributeDefinition] = field(default_factory=list)


class TerminologyBuilder:
    """高层术语库构建器 - 基于元模型信息"""

    def __init__(self):
        """初始化术语库构建器"""
        self.component_types = self._load_component_types()
        self.interface_types = self._load_interface_types()
        self.mode_declaration_group = self._load_mode_declaration_group()

    def _load_component_types(self) -> Dict[str, ComponentTypeDefinition]:
        """加载组件类型定义（从round1.json提取）"""

        # 基础SW-COMPONENT-TYPE定义
        sw_component_type = ComponentTypeDefinition(
            name="SW-COMPONENT-TYPE",
            description="Base abstract class for all software component types",
            is_abstract=True,
            attributes=[
                AttributeDefinition("SHORT-NAME", "This specifies an identifying shortName for the object. It needs to be unique within its context and is intended for humans but even more for technical reference.", 1, 1),
                AttributeDefinition("PORTS", "The ports through which this component can communicate.\nThe aggregation of PortPrototype is subject to variability with the purpose to support the conditional existence of PortPrototypes.\nThe upper multiplicity of this role has been increased to * due to resolving an atpVariation stereotype. The previous value was -1.", 0, -1),
                AttributeDefinition("SW-COMPONENT-DOCUMENTATION", "This adds a documentation to the SwComponentType.\nThe upper multiplicity of this role has been increased to * due to resolving an atpVariation stereotype. The previous value was 1.", 0, -1),
                AttributeDefinition("CONSISTENCY-NEEDS", "This represents the colelction of ConsistencyNeeds owned by the enclosing SwComponentType.\nThe upper multiplicity of this role has been increased to * due to resolving an atpVariation stereotype. The previous value was -1.", 0, -1),
                AttributeDefinition("DESC", "This represents a general but brief (one paragraph) description what the object in question is about. It is only one paragraph! Desc is intended to be collected into overview tables. This property helps a human reader to identify the object in question.\n\nMore elaborate documentation, (in particular how the object is built or used) should go to \"introduction\".", 0, 1),
            ]
        )

        # ATOMIC-SW-COMPONENT-TYPE定义
        atomic_sw_component = ComponentTypeDefinition(
            name="ATOMIC-SW-COMPONENT-TYPE",
            description="An atomic software component is atomic in the sense that it cannot be further decomposed and distributed across multiple ECUs.",
            is_abstract=True,
            parent_type="SW-COMPONENT-TYPE"
        )

        # 具体的原子组件类型
        application_sw = ComponentTypeDefinition(
            name="APPLICATION-SW-COMPONENT-TYPE",
            description="The ApplicationSwComponentType is used to represent the application software.",
            is_abstract=False,
            parent_type="ATOMIC-SW-COMPONENT-TYPE"
        )

        sensor_actuator_sw = ComponentTypeDefinition(
            name="SENSOR-ACTUATOR-SW-COMPONENT-TYPE",
            description="The SensorActuatorSwComponentType introduces the possibility to link from the software representation of a sensor/actuator to its hardware description provided by the ECU Resource Template.",
            is_abstract=False,
            parent_type="ATOMIC-SW-COMPONENT-TYPE"
        )

        complex_driver_sw = ComponentTypeDefinition(
            name="COMPLEX-DEVICE-DRIVER-SW-COMPONENT-TYPE",
            description="The ComplexDeviceDriverSwComponentType is a special AtomicSwComponentType that has direct access to hardware on an ECU and which is therefore linked to a specific ECU or specific hardware. The ComplexDeviceDriverSwComponentType introduces the possibility to link from the software representation to its hardware description provided by the ECU Resource Template.",
            is_abstract=False,
            parent_type="ATOMIC-SW-COMPONENT-TYPE"
        )

        ecu_abstraction_sw = ComponentTypeDefinition(
            name="ECU-ABSTRACTION-SW-COMPONENT-TYPE",
            description="The ECUAbstraction is a special AtomicSwComponentType that resides between a software-component that wants to access ECU periphery and the Microcontroller Abstraction. The EcuAbstractionSwComponentType introduces the possibility to link from the software representation to its hardware description provided by the ECU Resource Template.",
            is_abstract=False,
            parent_type="ATOMIC-SW-COMPONENT-TYPE"
        )

        nv_block_sw = ComponentTypeDefinition(
            name="NV-BLOCK-SW-COMPONENT-TYPE",
            description="The NvBlockSwComponentType defines non volatile data which data can be shared between SwComponentPrototypes. The non volatile data of the NvBlockSwComponentType are accessible via provided and required ports.",
            is_abstract=False,
            parent_type="ATOMIC-SW-COMPONENT-TYPE"
        )

        service_proxy_sw = ComponentTypeDefinition(
            name="SERVICE-PROXY-SW-COMPONENT-TYPE",
            description="This class provides the ability to express a software-component which provides access to an internal service for remote ECUs. It acts as a proxy for the service providing access to the service.\n\nAn important use case is the request of vehicle mode switches: Such requests can be communicated via sender-receiver interfaces across ECU boundaries, but the mode manager being responsible to perform the mode switches is an AUTOSAR Service which is located in the Basic Software and is not visible in the VFB view. To handle this situation, a ServiceProxySwComponentType will act as proxy for the mode manager. It will have R-Ports to be connected with the mode requestors on VFB level and Service-Ports to be connected with the local mode manager at ECU integration time.\n\nApart from the semantics, a ServiceProxySwComponentType has these specific properties:\n* A prototype of it can be mapped to more than one ECUs in the system description.\n* Exactly one additional instance of it will be created in the ECU-Extract per ECU to which the prototype has been mapped.\n* For remote communication, it can have only R-Ports with sender-receiver interfaces and 1:n semantics.\n* There shall be no connectors between two prototypes of any ServiceProxySwComponentType.",
            is_abstract=False,
            parent_type="ATOMIC-SW-COMPONENT-TYPE"
        )

        service_sw = ComponentTypeDefinition(
            name="SERVICE-SW-COMPONENT-TYPE",
            description="ServiceSwComponentType is used for configuring services for a given ECU. Instances of this class are only to be created in ECU Configuration phase for the specific purpose of the service configuration.",
            is_abstract=False,
            parent_type="ATOMIC-SW-COMPONENT-TYPE"
        )

        # 组合组件类型
        composition_sw = ComponentTypeDefinition(
            name="COMPOSITION-SW-COMPONENT-TYPE",
            description="A CompositionSwComponentType aggregates SwComponentPrototypes (that in turn are typed by SwComponentTypes) as well as SwConnectors for primarily connecting SwComponentPrototypes among each others and towards the surface of the CompositionSwComponentType. By this means hierarchical structures of software-components can be created.",
            is_abstract=False,
            parent_type="SW-COMPONENT-TYPE"
        )

        # 参数组件类型
        parameter_sw = ComponentTypeDefinition(
            name="PARAMETER-SW-COMPONENT-TYPE",
            description="The ParameterSwComponentType defines parameters and characteristic values accessible via provided Ports. The provided values are the same for all connected SwComponentPrototypes",
            is_abstract=False,
            parent_type="SW-COMPONENT-TYPE"
        )

        # 构建层次结构
        atomic_sw_component.sub_types = [
            application_sw,
            sensor_actuator_sw,
            complex_driver_sw,
            ecu_abstraction_sw,
            nv_block_sw,
            service_proxy_sw,
            service_sw
        ]

        sw_component_type.sub_types = [
            atomic_sw_component,
            composition_sw,
            parameter_sw
        ]

        # 返回字典形式
        types_dict = {
            "SW-COMPONENT-TYPE": sw_component_type,
            "ATOMIC-SW-COMPONENT-TYPE": atomic_sw_component,
            "APPLICATION-SW-COMPONENT-TYPE": application_sw,
            "SENSOR-ACTUATOR-SW-COMPONENT-TYPE": sensor_actuator_sw,
            "COMPLEX-DEVICE-DRIVER-SW-COMPONENT-TYPE": complex_driver_sw,
            "ECU-ABSTRACTION-SW-COMPONENT-TYPE": ecu_abstraction_sw,
            "NV-BLOCK-SW-COMPONENT-TYPE": nv_block_sw,
            "SERVICE-PROXY-SW-COMPONENT-TYPE": service_proxy_sw,
            "SERVICE-SW-COMPONENT-TYPE": service_sw,
            "COMPOSITION-SW-COMPONENT-TYPE": composition_sw,
            "PARAMETER-SW-COMPONENT-TYPE": parameter_sw
        }

        return types_dict

    def _load_interface_types(self) -> Dict[str, InterfaceTypeDefinition]:
        """加载接口类型定义（从round1.json提取）"""

        # 基础PORT-INTERFACE定义
        port_interface = InterfaceTypeDefinition(
            name="PORT-INTERFACE",
            description="Abstract base class for all port interfaces",
            is_abstract=True,
            attributes=[
                AttributeDefinition("SHORT-NAME", "This specifies an identifying shortName for the object. It needs to be unique within its context and is intended for humans but even more for technical reference.", 1, 1),
                AttributeDefinition("IS-SERVICE", "This flag is set if the PortInterface is to be used for\ncommunication between an\n* ApplicationSwComponentType or\n* ServiceProxySwComponentType or\n* SensorActuatorSwComponentType or\n* ComplexDeviceDriverSwComponentType\n* ServiceSwComponentType\n* EcuAbstractionSwComponentType\n\nand a ServiceSwComponentType (namely an\nAUTOSAR Service) located on the same ECU.\nOtherwise the flag is not set.", 1, 1),
                AttributeDefinition("SERVICE-KIND", "This attribute provides further details about the nature of the applied service.", 0, 1),
                AttributeDefinition("DESC", "This represents a general but brief (one paragraph) description what the object in question is about. It is only one paragraph! Desc is intended to be collected into overview tables. This property helps a human reader to identify the object in question.\n\nMore elaborate documentation, (in particular how the object is built or used) should go to \"introduction\".", 0, 1),
            ]
        )

        # CLIENT-SERVER-INTERFACE定义
        client_server = InterfaceTypeDefinition(
            name="CLIENT-SERVER-INTERFACE",
            description="A client/server interface declares a number of operations that can be invoked on a server by a client.",
            is_abstract=False,
            parent_type="PORT-INTERFACE"
        )

        # DATA-INTERFACE定义（抽象）
        data_interface = InterfaceTypeDefinition(
            name="DATA-INTERFACE",
            description="The purpose of this meta-class is to act as an abstract base class for subclasses that share the semantics of being concerned about data (as opposed to e.g. operations).",
            is_abstract=True,
            parent_type="PORT-INTERFACE"
        )

        # DATA-INTERFACE的子类
        nv_data = InterfaceTypeDefinition(
            name="NV-DATA-INTERFACE",
            description="A non volatile data interface declares a number of VariableDataPrototypes to be exchanged between non volatile block components and atomic software components.",
            is_abstract=False,
            parent_type="DATA-INTERFACE"
        )

        parameter = InterfaceTypeDefinition(
            name="PARAMETER-INTERFACE",
            description="A parameter interface declares a number of parameter and characteristic values to be exchanged between parameter components and software components.",
            is_abstract=False,
            parent_type="DATA-INTERFACE"
        )

        sender_receiver = InterfaceTypeDefinition(
            name="SENDER-RECEIVER-INTERFACE",
            description="A sender/receiver interface declares a number of data elements to be sent and received.",
            is_abstract=False,
            parent_type="DATA-INTERFACE"
        )

        # MODE-SWITCH-INTERFACE定义
        mode_switch = InterfaceTypeDefinition(
            name="MODE-SWITCH-INTERFACE",
            description="A mode switch interface declares a ModeDeclarationGroupPrototype to be sent and received.",
            is_abstract=False,
            parent_type="PORT-INTERFACE"
        )

        # TRIGGER-INTERFACE定义
        trigger = InterfaceTypeDefinition(
            name="TRIGGER-INTERFACE",
            description="A trigger interface declares a number of triggers that can be sent by an trigger source.",
            is_abstract=False,
            parent_type="PORT-INTERFACE"
        )

        # 构建层次结构
        data_interface.sub_types = [nv_data, parameter, sender_receiver]
        port_interface.sub_types = [client_server, data_interface, mode_switch, trigger]

        # 返回字典形式
        types_dict = {
            "PORT-INTERFACE": port_interface,
            "CLIENT-SERVER-INTERFACE": client_server,
            "DATA-INTERFACE": data_interface,
            "NV-DATA-INTERFACE": nv_data,
            "PARAMETER-INTERFACE": parameter,
            "SENDER-RECEIVER-INTERFACE": sender_receiver,
            "MODE-SWITCH-INTERFACE": mode_switch,
            "TRIGGER-INTERFACE": trigger
        }

        return types_dict

    def _load_mode_declaration_group(self) -> ModeDeclarationGroupDefinition:
        """加载模式声明组定义（从round1.json提取）"""

        mode_group = ModeDeclarationGroupDefinition(
            attributes=[
                AttributeDefinition("SHORT-NAME", "This specifies an identifying shortName for the object. It needs to be unique within its context and is intended for humans but even more for technical reference.", 1, 1),
                AttributeDefinition("INITIAL-MODE-REF", "The initial mode of the ModeDeclarationGroup. This mode is active before any mode switches occurred.", 1, 1),
                AttributeDefinition("MODE-DECLARATION", "The ModeDeclarations collected in this ModeDeclarationGroup.\nThe upper multiplicity of this role has been increased to * due to resolving an atpVariation stereotype. The previous value was -1.", 1, -1),
                AttributeDefinition("MODE-TRANSITION", "This represents the avaliable ModeTransitions of the ModeDeclarationGroup", 0, -1),
                AttributeDefinition("MODE-MANAGER-ERROR-BEHAVIOR", "This represents the ability to define the error behavior expected by the mode manager in case of errors on the mode user side (e.g. terminated mode user).", 0, 1),
                AttributeDefinition("MODE-USER-ERROR-BEHAVIOR", "This represents the definition of the error behavior expected by the mode user in case of errors on the mode manager side (e.g. terminated mode manager).", 0, 1),
                AttributeDefinition("ON-TRANSITION-VALUE", "The value of this attribute shall be taken into account by the RTE generator for programmatically representing a value used for the transition between two statuses.", 0, 1),
                AttributeDefinition("DESC", "This represents a general but brief (one paragraph) description what the object in question is about. It is only one paragraph! Desc is intended to be collected into overview tables. This property helps a human reader to identify the object in question.\n\nMore elaborate documentation, (in particular how the object is built or used) should go to \"introduction\".", 0, 1),
            ]
        )

        return mode_group

    def get_component_types(self) -> Dict[str, ComponentTypeDefinition]:
        """获取组件类型字典"""
        return self.component_types

    def get_interface_types(self) -> Dict[str, InterfaceTypeDefinition]:
        """获取接口类型字典"""
        return self.interface_types

    def get_concrete_component_types(self) -> List[ComponentTypeDefinition]:
        """获取具体（非抽象）的组件类型"""
        concrete_types = []
        for type_def in self.component_types.values():
            if not type_def.is_abstract:
                concrete_types.append(type_def)
        return concrete_types

    def get_concrete_interface_types(self) -> List[InterfaceTypeDefinition]:
        """获取具体（非抽象）的接口类型"""
        concrete_types = []
        for type_def in self.interface_types.values():
            if not type_def.is_abstract:
                concrete_types.append(type_def)
        return concrete_types

    def get_component_type_by_name(self, name: str) -> Optional[ComponentTypeDefinition]:
        """根据名称获取组件类型"""
        return self.component_types.get(name)

    def get_interface_type_by_name(self, name: str) -> Optional[InterfaceTypeDefinition]:
        """根据名称获取接口类型"""
        return self.interface_types.get(name)

    def get_metamodel_summary(self) -> Dict[str, Any]:
        """获取元模型摘要信息"""

        # 获取具体组件类型
        concrete_components = self.get_concrete_component_types()

        # 获取具体接口类型
        concrete_interfaces = self.get_concrete_interface_types()

        return {
            "component_types": {
                "total_count": len(self.component_types),
                "abstract_count": sum(1 for t in self.component_types.values() if t.is_abstract),
                "concrete_types": [
                    {
                        "name": ct.name,
                        "description": ct.description,
                        "parent": ct.parent_type
                    }
                    for ct in concrete_components
                ]
            },
            "interface_types": {
                "total_count": len(self.interface_types),
                "abstract_count": sum(1 for t in self.interface_types.values() if t.is_abstract),
                "concrete_types": [
                    {
                        "name": it.name,
                        "description": it.description,
                        "parent": it.parent_type
                    }
                    for it in concrete_interfaces
                ]
            },
            "mode_declaration_group": {
                "name": self.mode_declaration_group.name,
                "required_attributes": [
                    attr.tag for attr in self.mode_declaration_group.attributes
                    if attr.min_occurs >= 1
                ],
                "optional_attributes": [
                    attr.tag for attr in self.mode_declaration_group.attributes
                    if attr.min_occurs == 0
                ]
            }
        }

    def get_type_hierarchy(self) -> Dict[str, Any]:
        """获取类型层次结构"""

        def build_hierarchy(type_def, is_component=True):
            """递归构建层次结构"""
            result = {
                "name": type_def.name,
                "is_abstract": type_def.is_abstract,
                "description": type_def.description[:100] + "..." if len(type_def.description) > 100 else type_def.description
            }

            if type_def.sub_types:
                result["children"] = [
                    build_hierarchy(sub_type, is_component)
                    for sub_type in type_def.sub_types
                ]

            return result

        return {
            "component_hierarchy": build_hierarchy(self.component_types["SW-COMPONENT-TYPE"]),
            "interface_hierarchy": build_hierarchy(self.interface_types["PORT-INTERFACE"], False)
        }


# 全局术语库实例
terminology_builder = TerminologyBuilder()