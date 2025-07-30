"""knowledge/terminology_builder.py - 高层术语库构建

从KG提取核心概念，构建Round 1使用的高层术语库
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class ComponentType:
    """组件类型定义"""
    name: str
    description: str
    typical_scenarios: List[str]
    complexity_level: str  # Simple/Medium/Complex
    connection_patterns: List[str]
    usage_conditions: List[str]


@dataclass
class InterfaceType:
    """接口类型定义"""
    name: str
    description: str
    communication_mode: str  # 同步/异步、单向/双向
    data_characteristics: str
    performance_characteristics: str
    typical_data_types: List[str]
    usage_scenarios: List[str]


@dataclass
class DesignPattern:
    """设计模式定义"""
    name: str
    description: str
    component_combination: List[str]
    interface_combination: List[str]
    data_flow_direction: str
    usage_scenarios: List[str]
    variation_points: List[str]


class TerminologyBuilder:
    """高层术语库构建器"""

    def __init__(self):
        """初始化术语库构建器"""
        self.component_types = self._build_component_types()
        self.interface_types = self._build_interface_types()
        self.design_patterns = self._build_design_patterns()

    def _build_component_types(self) -> List[ComponentType]:
        """构建组件类型库（静态定义）"""
        return [
            ComponentType(
                name="APPLICATION-SW-COMPONENT-TYPE",
                description="应用软件组件，实现应用层业务逻辑",
                typical_scenarios=[
                    "数据处理和计算",
                    "业务逻辑控制",
                    "传感器数据融合",
                    "执行器控制",
                    "状态机管理"
                ],
                complexity_level="Medium",
                connection_patterns=[
                    "通过P-PORT提供服务",
                    "通过R-PORT请求服务",
                    "支持多个端口连接"
                ],
                usage_conditions=[
                    "需要实现复杂业务逻辑",
                    "需要与多个组件交互",
                    "需要周期性或事件驱动执行"
                ]
            ),
            ComponentType(
                name="SENSOR-ACTUATOR-SW-COMPONENT-TYPE",
                description="传感器执行器软件组件，处理硬件接口",
                typical_scenarios=[
                    "传感器数据采集",
                    "执行器控制信号输出",
                    "硬件抽象层接口",
                    "诊断数据处理"
                ],
                complexity_level="Simple",
                connection_patterns=[
                    "P-PORT提供传感器数据",
                    "R-PORT接收控制命令",
                    "通常单一数据流向"
                ],
                usage_conditions=[
                    "需要与硬件直接交互",
                    "数据格式相对固定",
                    "实时性要求较高"
                ]
            ),
            ComponentType(
                name="COMPOSITION-SW-COMPONENT-TYPE",
                description="组合软件组件，包含和组织其他组件",
                typical_scenarios=[
                    "系统级组件组合",
                    "子系统封装",
                    "复杂功能模块化",
                    "层次化架构设计"
                ],
                complexity_level="Complex",
                connection_patterns=[
                    "包含多个子组件",
                    "代理内部组件接口",
                    "支持委托连接器"
                ],
                usage_conditions=[
                    "需要组织多个相关组件",
                    "需要隐藏内部复杂性",
                    "需要提供统一外部接口"
                ]
            ),
            ComponentType(
                name="PARAMETER-SW-COMPONENT-TYPE",
                description="参数软件组件，管理配置参数",
                typical_scenarios=[
                    "系统配置管理",
                    "标定参数存储",
                    "运行时参数调整",
                    "工厂设置管理"
                ],
                complexity_level="Simple",
                connection_patterns=[
                    "P-PORT提供参数值",
                    "支持参数变更通知",
                    "通常为数据提供者"
                ],
                usage_conditions=[
                    "需要管理可配置参数",
                    "需要参数持久化",
                    "需要运行时参数访问"
                ]
            )
        ]

    def _build_interface_types(self) -> List[InterfaceType]:
        """构建接口类型库（静态定义）"""
        return [
            InterfaceType(
                name="SENDER-RECEIVER-INTERFACE",
                description="发送接收接口，用于异步数据通信",
                communication_mode="异步、单向或双向",
                data_characteristics="数据驱动，支持周期性和事件驱动传输",
                performance_characteristics="高吞吐量，低延迟，支持数据丢失检测",
                typical_data_types=[
                    "传感器数值（温度、压力、速度）",
                    "状态信息（开关状态、模式）",
                    "控制指令（目标值、使能信号）",
                    "诊断数据（错误代码、状态标志）"
                ],
                usage_scenarios=[
                    "传感器数据传输",
                    "控制信号发送",
                    "状态信息广播",
                    "诊断数据报告",
                    "周期性数据更新"
                ]
            ),
            InterfaceType(
                name="CLIENT-SERVER-INTERFACE",
                description="客户端服务端接口，用于同步服务调用",
                communication_mode="同步、双向请求响应",
                data_characteristics="操作驱动，支持复杂数据结构和返回值",
                performance_characteristics="确定性响应时间，支持错误处理",
                typical_data_types=[
                    "配置参数（读写操作）",
                    "计算服务（输入参数和计算结果）",
                    "诊断服务（测试请求和结果）",
                    "标定数据（读写访问）"
                ],
                usage_scenarios=[
                    "参数配置服务",
                    "复杂计算请求",
                    "诊断测试调用",
                    "数据库访问",
                    "文件操作服务"
                ]
            ),
            InterfaceType(
                name="MODE-SWITCH-INTERFACE",
                description="模式切换接口，用于系统模式管理",
                communication_mode="异步、事件驱动",
                data_characteristics="模式状态驱动，支持模式切换通知",
                performance_characteristics="低延迟模式切换，支持模式依赖管理",
                typical_data_types=[
                    "运行模式（初始化、正常、降级）",
                    "功能模式（激活、非激活）",
                    "诊断模式（正常、测试、维护）",
                    "安全模式（安全、故障安全）"
                ],
                usage_scenarios=[
                    "系统启动关闭管理",
                    "功能激活控制",
                    "故障安全处理",
                    "诊断模式切换",
                    "节能模式管理"
                ]
            ),
            InterfaceType(
                name="NV-DATA-INTERFACE",
                description="非易失性数据接口，用于持久化数据存储",
                communication_mode="同步、读写操作",
                data_characteristics="持久化数据，支持数据完整性保护",
                performance_characteristics="相对较慢，支持数据验证和恢复",
                typical_data_types=[
                    "配置参数（用户设置）",
                    "标定数据（工厂标定值）",
                    "学习数据（自适应参数）",
                    "历史数据（事件记录）"
                ],
                usage_scenarios=[
                    "用户配置存储",
                    "标定参数保存",
                    "自学习数据持久化",
                    "故障记录存储",
                    "统计数据保存"
                ]
            )
        ]

    def _build_design_patterns(self) -> List[DesignPattern]:
        """构建设计模式库（静态定义）"""
        return [
            DesignPattern(
                name="传感器数据采集模式",
                description="从传感器采集数据并提供给应用组件处理",
                component_combination=["SENSOR-ACTUATOR-SW-COMPONENT-TYPE", "APPLICATION-SW-COMPONENT-TYPE"],
                interface_combination=["SENDER-RECEIVER-INTERFACE"],
                data_flow_direction="传感器组件 → 应用组件",
                usage_scenarios=[
                    "温度监控系统",
                    "速度检测应用",
                    "压力监测系统",
                    "位置感知应用"
                ],
                variation_points=[
                    "传感器数据类型",
                    "采集频率",
                    "数据预处理方式",
                    "故障检测策略"
                ]
            ),
            DesignPattern(
                name="控制指令执行模式",
                description="应用组件生成控制指令，执行器组件执行",
                component_combination=["APPLICATION-SW-COMPONENT-TYPE", "SENSOR-ACTUATOR-SW-COMPONENT-TYPE"],
                interface_combination=["SENDER-RECEIVER-INTERFACE"],
                data_flow_direction="应用组件 → 执行器组件",
                usage_scenarios=[
                    "电机控制系统",
                    "阀门控制应用",
                    "加热器控制",
                    "照明控制系统"
                ],
                variation_points=[
                    "控制算法类型",
                    "执行器类型",
                    "反馈机制",
                    "安全保护策略"
                ]
            ),
            DesignPattern(
                name="参数配置服务模式",
                description="通过客户端服务端接口进行参数配置",
                component_combination=["APPLICATION-SW-COMPONENT-TYPE", "PARAMETER-SW-COMPONENT-TYPE"],
                interface_combination=["CLIENT-SERVER-INTERFACE"],
                data_flow_direction="双向：参数读写操作",
                usage_scenarios=[
                    "系统配置管理",
                    "用户偏好设置",
                    "标定参数调整",
                    "诊断参数配置"
                ],
                variation_points=[
                    "参数类型和范围",
                    "访问权限控制",
                    "参数验证规则",
                    "默认值设置"
                ]
            ),
            DesignPattern(
                name="模式管理模式",
                description="通过模式切换接口管理系统运行模式",
                component_combination=["APPLICATION-SW-COMPONENT-TYPE", "APPLICATION-SW-COMPONENT-TYPE"],
                interface_combination=["MODE-SWITCH-INTERFACE"],
                data_flow_direction="模式管理器 → 功能组件",
                usage_scenarios=[
                    "系统启动关闭管理",
                    "功能激活控制",
                    "安全模式切换",
                    "节能模式管理"
                ],
                variation_points=[
                    "模式类型定义",
                    "切换条件",
                    "模式依赖关系",
                    "切换延迟时间"
                ]
            ),
            DesignPattern(
                name="数据融合处理模式",
                description="多个传感器数据融合处理，提供综合信息",
                component_combination=["SENSOR-ACTUATOR-SW-COMPONENT-TYPE", "APPLICATION-SW-COMPONENT-TYPE"],
                interface_combination=["SENDER-RECEIVER-INTERFACE"],
                data_flow_direction="多个传感器 → 融合处理组件",
                usage_scenarios=[
                    "多传感器定位",
                    "环境感知融合",
                    "故障检测诊断",
                    "性能监控分析"
                ],
                variation_points=[
                    "融合算法选择",
                    "传感器权重",
                    "异常数据处理",
                    "输出数据格式"
                ]
            ),
            DesignPattern(
                name="分层控制模式",
                description="多层次控制架构，上层策略下层执行",
                component_combination=["APPLICATION-SW-COMPONENT-TYPE", "APPLICATION-SW-COMPONENT-TYPE",
                                       "SENSOR-ACTUATOR-SW-COMPONENT-TYPE"],
                interface_combination=["SENDER-RECEIVER-INTERFACE", "CLIENT-SERVER-INTERFACE"],
                data_flow_direction="策略层 → 控制层 → 执行层",
                usage_scenarios=[
                    "复杂控制系统",
                    "智能决策应用",
                    "自适应控制",
                    "多目标优化控制"
                ],
                variation_points=[
                    "控制层级数量",
                    "层间通信方式",
                    "决策算法",
                    "反馈路径设计"
                ]
            )
        ]

    def get_component_types(self) -> List[ComponentType]:
        """获取组件类型列表"""
        return self.component_types

    def get_interface_types(self) -> List[InterfaceType]:
        """获取接口类型列表"""
        return self.interface_types

    def get_design_patterns(self) -> List[DesignPattern]:
        """获取设计模式列表"""
        return self.design_patterns

    def get_component_type_by_name(self, name: str) -> Optional[ComponentType]:
        """根据名称获取组件类型"""
        for comp_type in self.component_types:
            if comp_type.name == name:
                return comp_type
        return None

    def get_interface_type_by_name(self, name: str) -> Optional[InterfaceType]:
        """根据名称获取接口类型"""
        for intf_type in self.interface_types:
            if intf_type.name == name:
                return intf_type
        return None

    def suggest_patterns_for_scenario(self, scenario: str) -> List[DesignPattern]:
        """根据场景建议设计模式"""
        suggestions = []
        scenario_lower = scenario.lower()

        for pattern in self.design_patterns:
            # 检查使用场景匹配
            for usage_scenario in pattern.usage_scenarios:
                if any(keyword in scenario_lower for keyword in usage_scenario.lower().split()):
                    suggestions.append(pattern)
                    break

        return suggestions

    def get_terminology_summary(self) -> Dict[str, Any]:
        """获取术语库摘要"""
        return {
            "component_types": [
                {
                    "name": ct.name,
                    "description": ct.description,
                    "complexity": ct.complexity_level
                }
                for ct in self.component_types
            ],
            "interface_types": [
                {
                    "name": it.name,
                    "description": it.description,
                    "communication_mode": it.communication_mode
                }
                for it in self.interface_types
            ],
            "design_patterns": [
                {
                    "name": dp.name,
                    "description": dp.description,
                    "components": dp.component_combination
                }
                for dp in self.design_patterns
            ]
        }


# 全局术语库实例
terminology_builder = TerminologyBuilder()