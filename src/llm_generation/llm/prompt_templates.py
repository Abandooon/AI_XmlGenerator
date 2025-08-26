"""llm/prompt_templates.py - 优化的提示词模板管理

充分利用Gemini长上下文能力，减少分批，提供完整信息
"""
from typing import Dict, Any, List, Optional
from string import Template

class PromptTemplateManager:
    """提示词模板管理器 - 优化版"""

    def __init__(self):
        """初始化模板管理器"""
        self.templates = {
            # Round 1 架构设计模板（增强）
            "round1_architecture": self._get_enhanced_round1_template(),

            # Round 2 详细生成模板（长上下文优化）
            "round2_unified": self._get_unified_round2_template(),

            # 备用：大规模批次模板
            "round2_large_batch": self._get_large_batch_template(),
        }

    def _get_enhanced_round1_template(self) -> Template:
        """增强的Round 1架构设计模板"""
        template_text = """
你是一个AUTOSAR架构设计专家。根据用户需求设计软件组件架构。

## 用户需求
$user_requirements

## 设计上下文
$design_context

## 可用组件类型（完整列表）
$component_types

## 可用接口类型（完整列表）
$interface_types

## 设计任务
请设计一个符合AUTOSAR标准的完整软件组件架构，包括：

1. **系统分析**: 深入分析功能需求、数据流、时序要求
2. **组件规划**: 确定所有需要的组件类型、数量、职责、内部结构
3. **接口规划**: 设计所有组件间的接口类型、通信模式、数据元素
4. **连接拓扑**: 完整定义所有组件间的连接关系和数据流向
5. **引用路径**: 明确指定所有引用的完整路径（无需语义占位符）

## 增强设计原则
- **完整性优先**: 一次性设计所有需要的元素
- **明确引用**: 使用完整的引用路径，如 /Components/TempSensor/Ports/DataOut
- **详细规格**: 为每个组件提供详细的端口和行为规格
- **减少歧义**: 避免模糊描述，使用精确的技术规范

## 组件规划要求
对于每个组件，请提供：
- component_id: 唯一标识符
- name: 描述性名称
- type: AUTOSAR组件类型
- purpose: 详细功能描述
- port_estimates: 
  - input_ports: 输入端口详细列表
  - output_ports: 输出端口详细列表
- behavioral_characteristics:
  - runnables: 运行实体列表
  - events: 事件列表
  - timing: 时序要求
- direct_references: 直接引用的其他组件/接口的完整路径

## 接口规划要求
对于每个接口，请提供：
- interface_id: 唯一标识符
- name: 描述性名称
- type: AUTOSAR接口类型
- communication_pattern: 通信模式详情
- data_elements: 详细的数据元素定义
- connected_components: 连接的组件对
- direct_paths: 接口在系统中的完整路径

## 输出要求
输出完整、详细的JSON格式架构设计。确保：
- 所有ID全局唯一
- 引用路径完整准确
- 组件间关系明确
- 数据流向清晰
- 可直接用于Round 2生成
"""
        return Template(template_text)

    def _get_unified_round2_template(self) -> Template:
        """统一的Round 2生成模板 - 利用长上下文"""
        template_text = """
你是AUTOSAR XML生成专家。基于架构设计一次性生成所有组件的完整ARXML内容。

## 完整架构设计
$architecture_design

## 详细元模型信息（深度=$schema_depth）
$metamodel_context

## 完整约束规则
$constraints

## 标准类型库
$standard_types

## 生成任务
一次性生成所有 $component_count 个组件的完整ARXML JSON结构。

## 关键生成要求

### 1. 完整性要求
- 生成所有组件的完整定义
- 包含所有必需的XML元素和属性
- 完整的内部行为定义（INTERNAL-BEHAVIORS）
- 所有端口定义（PORTS）
- 完整的事件和Runnable关联

### 2. 引用一致性
- 使用完整的引用路径，无需语义占位符
- 组件间引用直接使用绝对路径
- 示例：/Components/TemperatureMonitor/Ports/TempDataOut

### 3. 结构规范
对于每个APPLICATION-SW-COMPONENT-TYPE：
```
{
  "SHORT-NAME": "ComponentName",
  "@UUID": "unique-uuid-here",
  "PORTS": {
    "P-PORT-PROTOTYPE": [{
      "SHORT-NAME": "OutputPortName",
      "PROVIDED-INTERFACE-TREF": "/Interfaces/InterfaceName"
    }],
    "R-PORT-PROTOTYPE": [{
      "SHORT-NAME": "InputPortName", 
      "REQUIRED-INTERFACE-TREF": "/Interfaces/InterfaceName",
      "REQUIRED-COM-SPECS": {...}
    }]
  },
  "INTERNAL-BEHAVIORS": {
    "SWC-INTERNAL-BEHAVIOR": {
      "SHORT-NAME": "InternalBehaviorName",
      "EVENTS": {
        "TIMING-EVENT": [{
          "SHORT-NAME": "Event10ms",
          "START-ON-EVENT-REF": "/Components/ComponentName/InternalBehavior/Runnables/RunnableName",
          "PERIOD": 0.01
        }]
      },
      "RUNNABLES": {
        "RUNNABLE-ENTITY": [{
          "SHORT-NAME": "RunnableName",
          "SYMBOL": "RunnableName_func",
          "DATA-READ-ACCESSES": {...},
          "DATA-WRITE-ACCESSES": {...}
        }]
      }
    }
  }
}
```

### 4. 深层元素要求（基于元模型深度$schema_depth）
包含以下所有层级的元素：
$required_elements_detail

### 5. 数据类型使用
- 所有数据元素使用标准类型库中的类型
- TYPE-TREF格式：/AUTOSAR_Platform/ImplementationDataTypes/typename
- 避免自定义类型，优先使用标准类型

## 组件列表（需要生成的所有组件）
$component_list_detail

## 接口定义（预定义的所有接口）
$interface_definitions

## 质量要求
1. **原子性**: 所有组件在一个响应中完整生成
2. **可追溯性**: 每个元素都能追溯到架构设计
3. **一致性**: 组件间的交互完全一致
4. **完整性**: 不遗漏任何必需元素
5. **正确性**: 严格遵循AUTOSAR标准

## 输出格式
生成包含所有组件的单一JSON结构，每个组件作为顶级属性：
```json
{
  "TemperatureMonitor": { /* 完整组件定义 */ },
  "DataProcessor": { /* 完整组件定义 */ },
  "ControlManager": { /* 完整组件定义 */ },
  // ... 所有其他组件
}
```

请确保输出的JSON可以直接转换为有效的ARXML文件。
"""
        return Template(template_text)

    def _get_large_batch_template(self) -> Template:
        """大规模批次模板 - 备用"""
        template_text = """
你是AUTOSAR大规模系统生成专家。利用长上下文能力一次性处理大量组件。

## 系统规模
- 组件总数: $total_components
- 接口总数: $total_interfaces  
- 连接总数: $total_connections

## 完整系统架构
$full_architecture

## 扩展元模型（深度=$extended_depth）
$extended_metamodel

## 生成策略
采用"全系统一次性生成"策略：
1. 先生成所有接口定义
2. 再生成所有组件定义
3. 最后建立所有连接关系

## 优化指导
- 利用组件模板减少重复
- 使用命名规范保持一致性
- 批量处理相似组件
- 保持引用的绝对路径

## 大规模生成规范
$large_scale_specifications

## 输出要求
生成完整的系统ARXML，包含所有组件、接口和连接。
"""
        return Template(template_text)

    def get_round2_prompt(
        self,
        architecture_design: Dict[str, Any],
        constraints: List[str] = None,
        schema_depth: int = 15
    ) -> str:
        """获取优化的Round 2提示词 - 统一生成版本"""

        component_plans = architecture_design.get("component_plan", [])
        interface_plans = architecture_design.get("interface_plan", [])

        # 格式化组件列表详情
        component_list_detail = self._format_component_list_detail(component_plans)

        # 格式化接口定义
        interface_definitions = self._format_interface_definitions(interface_plans)

        # 获取深层元模型上下文
        metamodel_context = self._get_deep_metamodel_context(component_plans, schema_depth)

        # 获取必需元素详情
        required_elements_detail = self._get_required_elements_detail(component_plans, schema_depth)

        # 获取标准类型上下文
        from ..standard_types.standard_types import standard_type_manager
        standard_types = standard_type_manager.get_type_context_for_llm(
            filter_categories=["VALUE", "TYPE_REFERENCE", "PRIMITIVE"]
        )

        return self.render_template(
            "round2_unified",
            architecture_design=self._format_architecture_design(architecture_design),
            component_count=len(component_plans),
            schema_depth=schema_depth,
            metamodel_context=metamodel_context,
            constraints="\n".join(constraints or ["遵循AUTOSAR标准规范"]),
            standard_types=standard_types,
            component_list_detail=component_list_detail,
            interface_definitions=interface_definitions,
            required_elements_detail=required_elements_detail
        )

    def _format_component_list_detail(self, component_plans: List[Dict]) -> str:
        """格式化详细的组件列表"""
        lines = []
        for i, comp in enumerate(component_plans, 1):
            lines.append(f"{i}. **{comp.get('name', f'Component{i}')}**")
            lines.append(f"   - 类型: {comp.get('type', '')}")
            lines.append(f"   - 功能: {comp.get('purpose', '')}")
            lines.append(f"   - 复杂度: {comp.get('estimated_complexity', 'Medium')}")

            # 端口估计
            if 'port_estimates' in comp:
                ports = comp['port_estimates']
                lines.append(f"   - 输入端口: {ports.get('input_ports', 'N/A')}")
                lines.append(f"   - 输出端口: {ports.get('output_ports', 'N/A')}")

            # 行为特征
            if 'behavioral_characteristics' in comp:
                behavior = comp['behavioral_characteristics']
                if 'runnables' in behavior:
                    lines.append(f"   - Runnables: {', '.join(behavior['runnables'])}")
                if 'events' in behavior:
                    lines.append(f"   - Events: {', '.join(behavior['events'])}")

            # 直接引用
            if 'direct_references' in comp:
                lines.append(f"   - 引用: {', '.join(comp['direct_references'])}")

            lines.append("")

        return "\n".join(lines)

    def _format_interface_definitions(self, interface_plans: List[Dict]) -> str:
        """格式化接口定义"""
        lines = []
        for i, intf in enumerate(interface_plans, 1):
            lines.append(f"{i}. **{intf.get('name', f'Interface{i}')}**")
            lines.append(f"   - 类型: {intf.get('type', '')}")
            lines.append(f"   - 通信模式: {intf.get('communication_pattern', '')}")

            if 'data_elements' in intf and intf['data_elements']:
                lines.append(f"   - 数据元素: {', '.join(intf['data_elements'])}")

            if 'connected_components' in intf:
                lines.append(f"   - 连接组件: {' <-> '.join(intf['connected_components'])}")

            if 'direct_paths' in intf:
                lines.append(f"   - 路径: {intf['direct_paths']}")

            lines.append("")

        return "\n".join(lines)

    def _get_deep_metamodel_context(self, component_plans: List[Dict], depth: int) -> str:
        """获取深层元模型上下文"""
        lines = ["### 元模型结构（深度扩展）"]

        # 获取所有涉及的组件类型
        component_types = set(comp.get("type", "APPLICATION-SW-COMPONENT-TYPE")
                            for comp in component_plans)

        for comp_type in component_types:
            lines.append(f"\n#### {comp_type}")
            lines.append(f"继承深度: {depth}")
            lines.append("必需元素层级:")

            # 这里应该从knowledge graph获取实际的元模型信息
            # 简化示例
            lines.append("- Level 1: SHORT-NAME, @UUID")
            lines.append("- Level 2: PORTS (P-PORT-PROTOTYPE, R-PORT-PROTOTYPE)")
            lines.append("- Level 3: INTERNAL-BEHAVIORS (SWC-INTERNAL-BEHAVIOR)")
            lines.append("- Level 4: EVENTS (TIMING-EVENT, DATA-RECEIVED-EVENT)")
            lines.append("- Level 5: RUNNABLES (RUNNABLE-ENTITY)")
            lines.append("- Level 6+: DATA-ACCESS, SERVER-CALL-POINTS, etc.")

        return "\n".join(lines)

    def _get_required_elements_detail(self, component_plans: List[Dict], depth: int) -> str:
        """获取必需元素的详细说明"""
        lines = ["### 必需元素详细规格"]

        lines.append("\n#### 通用必需元素（所有组件）")
        lines.append("- SHORT-NAME: 组件短名称，PascalCase格式")
        lines.append("- @UUID: 全局唯一标识符，标准UUID格式")

        lines.append("\n#### PORTS结构（深度展开）")
        lines.append("```")
        lines.append("PORTS:")
        lines.append("  P-PORT-PROTOTYPE: (minOccurs=0, maxOccurs=unbounded)")
        lines.append("    - SHORT-NAME: 端口名称")
        lines.append("    - PROVIDED-INTERFACE-TREF: 接口引用")
        lines.append("    - PROVIDED-COM-SPECS: (可选)")
        lines.append("      - QUEUED-SENDER-COM-SPEC")
        lines.append("      - NONQUEUED-SENDER-COM-SPEC")
        lines.append("  R-PORT-PROTOTYPE: (minOccurs=0, maxOccurs=unbounded)")
        lines.append("    - SHORT-NAME: 端口名称")
        lines.append("    - REQUIRED-INTERFACE-TREF: 接口引用")
        lines.append("    - REQUIRED-COM-SPECS: (推荐)")
        lines.append("```")

        lines.append("\n#### INTERNAL-BEHAVIORS结构（深度展开）")
        lines.append("```")
        lines.append("INTERNAL-BEHAVIORS:")
        lines.append("  SWC-INTERNAL-BEHAVIOR:")
        lines.append("    - SHORT-NAME: 行为名称")
        lines.append("    - EVENTS: (minOccurs=1)")
        lines.append("      - TIMING-EVENT")
        lines.append("      - DATA-RECEIVED-EVENT")
        lines.append("      - OPERATION-INVOKED-EVENT")
        lines.append("    - RUNNABLES: (minOccurs=1)")
        lines.append("      - RUNNABLE-ENTITY")
        lines.append("    - PER-INSTANCE-MEMORYS: (可选)")
        lines.append("    - SERVICE-DEPENDENCYS: (可选)")
        lines.append("```")

        return "\n".join(lines)

    def _format_architecture_design(self, design: Dict[str, Any]) -> str:
        """格式化架构设计 - 增强版"""
        lines = []

        # 系统分析
        if 'system_analysis' in design:
            lines.append("### 系统分析")
            for key, value in design['system_analysis'].items():
                lines.append(f"- {self._translate_analysis_key(key)}: {value}")

        # 组件统计
        comp_count = len(design.get('component_plan', []))
        intf_count = len(design.get('interface_plan', []))

        lines.append(f"\n### 系统规模")
        lines.append(f"- 组件总数: {comp_count}")
        lines.append(f"- 接口总数: {intf_count}")
        lines.append(f"- 预估连接数: {comp_count * 2}")  # 简单估算

        # 组件摘要
        lines.append(f"\n### 组件架构摘要")
        comp_types = {}
        for comp in design.get('component_plan', []):
            comp_type = comp.get('type', 'Unknown')
            comp_types[comp_type] = comp_types.get(comp_type, 0) + 1

        for comp_type, count in comp_types.items():
            lines.append(f"- {comp_type}: {count}个")

        # 接口摘要
        lines.append(f"\n### 接口架构摘要")
        intf_types = {}
        for intf in design.get('interface_plan', []):
            intf_type = intf.get('type', 'Unknown')
            intf_types[intf_type] = intf_types.get(intf_type, 0) + 1

        for intf_type, count in intf_types.items():
            lines.append(f"- {intf_type}: {count}个")

        # 连接拓扑
        if 'connection_topology' in design:
            lines.append("\n### 连接拓扑")
            topology = design['connection_topology']
            if topology.get('component_connections'):
                lines.append(f"- 组件连接: {topology['component_connections']}")
            if topology.get('data_flow_paths'):
                lines.append(f"- 数据流: {topology['data_flow_paths']}")

        return "\n".join(lines)

    def _translate_analysis_key(self, key: str) -> str:
        """翻译分析键"""
        translations = {
            "functional_decomposition": "功能分解",
            "data_flow_analysis": "数据流分析",
            "timing_requirements": "时序要求",
            "scalability_considerations": "可扩展性"
        }
        return translations.get(key, key)

    def get_template(self, template_name: str) -> Optional[Template]:
        """获取模板"""
        return self.templates.get(template_name)

    def render_template(self, template_name: str, **kwargs) -> str:
        """渲染模板"""
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"模板不存在: {template_name}")

        try:
            return template.substitute(**kwargs)
        except KeyError as e:
            raise ValueError(f"模板参数缺失: {e}")

# 全局模板管理器实例
template_manager = PromptTemplateManager()