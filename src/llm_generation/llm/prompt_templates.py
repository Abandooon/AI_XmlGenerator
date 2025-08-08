"""llm/prompt_templates.py - 提示词模板管理

管理Round 1和Round 2的提示词模板，支持多组件生成
"""
from typing import Dict, Any, List, Optional
from string import Template

class PromptTemplateManager:
    """提示词模板管理器"""

    def __init__(self):
        """初始化模板管理器"""
        self.templates = {
            # Round 1 架构设计模板
            "round1_architecture": self._get_round1_template(),
            "round1_analysis": self._get_analysis_template(),

            # Round 2 详细生成模板
            "round2_generation": self._get_round2_template(),
            "round2_multi_component": self._get_multi_component_template(),
        }

    def _get_round1_template(self) -> Template:
        """Round 1 架构设计模板"""
        template_text = """
你是一个AUTOSAR架构设计专家。根据用户需求设计软件组件架构。

## 用户需求
$user_requirements

## 设计上下文
$design_context

## 可用组件类型
$component_types

## 可用接口类型  
$interface_types

## 设计任务
请设计一个符合AUTOSAR标准的软件组件架构，包括：

1. **系统分析**: 分析功能需求、数据流、时序要求
2. **组件规划**: 确定需要的组件类型、数量、职责
3. **接口规划**: 设计组件间的接口类型、通信模式
4. **连接拓扑**: 定义组件间的连接关系和数据流向
5. **架构决策**: 说明关键设计决策的理由

## 设计原则
- 遵循AUTOSAR分层架构
- 保持组件职责单一
- 最小化组件间耦合
- 考虑可扩展性和可维护性
- 满足实时性和安全性要求

## 多组件设计指导
如果需求复杂，可以设计多个组件：
- 每个组件应有明确的职责边界
- 组件间通过标准AUTOSAR接口通信
- 避免循环依赖
- 考虑组件的独立部署和测试

## 输出要求
输出JSON格式的架构设计，包含所有必需字段。确保：
- 组件ID和接口ID唯一
- 组件名称具有描述性
- 接口类型选择合理
- 连接关系清晰明确
"""
        return Template(template_text)

    def _get_analysis_template(self) -> Template:
        """系统分析模板"""
        template_text = """
作为AUTOSAR系统分析专家，请对以下需求进行深入分析：

## 需求描述
$requirements

## 分析维度
1. **功能分解**: 识别主要功能模块和子功能
2. **数据流分析**: 分析数据的产生、传递、消费路径
3. **时序分析**: 识别关键时序约束和周期性要求
4. **接口分析**: 确定对外接口和内部接口需求
5. **约束分析**: 识别性能、安全、资源约束
6. **复杂度评估**: 评估实现复杂度和组件数量需求

## 输出格式
提供结构化的分析结果，为架构设计提供依据。
"""
        return Template(template_text)

    def _get_round2_template(self) -> Template:
        """Round 2 详细生成模板"""
        template_text = """
你是AUTOSAR XML生成专家。根据确认的架构设计生成详细的ARXML内容。

## 架构设计
$architecture_design

## 约束规则
$constraints

## 生成任务
根据架构设计生成符合AUTOSAR标准的完整ARXML JSON结构。

## 生成要求
1. **结构完整**: 包含所有必需的XML元素
2. **命名规范**: 遵循AUTOSAR命名约定
3. **类型正确**: 使用正确的AUTOSAR数据类型
4. **引用一致**: 确保所有引用的完整性和唯一性
5. **UUID唯一**: 所有UUID必须唯一且格式正确

## 关键元素要求

### APPLICATION-SW-COMPONENT-TYPE
- SHORT-NAME: 使用架构设计中的组件名称
- @UUID: 生成唯一UUID
- PORTS: 根据接口计划生成端口
- INTERNAL-BEHAVIORS: 定义内部行为

### 端口定义 (PORTS)
- P-PORT-PROTOTYPE: 提供接口的端口
  - SHORT-NAME: 描述性端口名称
  - PROVIDED-INTERFACE-TREF: 正确的接口引用
- R-PORT-PROTOTYPE: 需要接口的端口
  - SHORT-NAME: 描述性端口名称
  - REQUIRED-INTERFACE-TREF: 正确的接口引用
  - REQUIRED-COM-SPECS: 通信规范

### 内部行为 (INTERNAL-BEHAVIORS)
- SWC-INTERNAL-BEHAVIOR:
  - SHORT-NAME: 内部行为名称
  - EVENTS: 至少一个TIMING-EVENT
  - RUNNABLES: 至少一个RUNNABLE-ENTITY

### 事件和Runnable关联
- TIMING-EVENT:
  - SHORT-NAME: 事件名称
  - START-ON-EVENT-REF: 正确引用RUNNABLE-ENTITY
  - PERIOD: 合理的周期值
- RUNNABLE-ENTITY:
  - SHORT-NAME: Runnable名称
  - SYMBOL: C函数名称
  - 数据访问点: 根据端口定义

## 命名约定
- 组件名称: PascalCase，如 TemperatureMonitor
- 端口名称: PascalCase + 方向，如 TempDataOut, ControlIn
- Runnable名称: PascalCase + Run，如 TempProcessRun
- 事件名称: PascalCase + Event，如 TempProcessEvent

## 输出格式
生成完整的JSON结构，严格遵循提供的schema定义。
"""
        return Template(template_text)

    def _get_multi_component_template(self) -> Template:
        """多组件生成模板"""
        template_text = """
你是AUTOSAR多组件XML生成专家。根据架构设计生成多个组件的ARXML内容。

## 架构设计 (包含多个组件)
$architecture_design

## 组件生成要求
需要生成 $component_count 个组件：
$component_list

## 多组件生成规则

### 1. 唯一性保证
- 每个组件的所有UUID必须全局唯一
- 组件名称不能重复
- 端口名称在组件内唯一
- Runnable名称在组件内唯一

### 2. 引用一致性
- 接口引用路径必须正确
- 组件间的端口连接要对应
- 事件和Runnable的引用关系正确

### 3. 命名策略
- 组件名称体现功能特性，如: TempSensor, DataProcessor, ControlManager
- 端口名称体现数据类型和方向，如: TempData_Out, ControlCmd_In
- 避免通用名称，使用具体描述性名称

### 4. 组件间协作
- 发送组件的P-PORT对应接收组件的R-PORT
- 接口类型必须匹配
- 数据流向符合架构设计

## 约束规则
$constraints

## 特殊要求
- 每个组件都应该是完整的、可独立部署的
- 组件的复杂度应该合理，避免过度复杂
- 保持组件间的松耦合

## 输出格式
生成包含所有组件的完整JSON结构，每个组件作为独立的顶级属性。
"""
        return Template(template_text)

    def get_template(self, template_name: str) -> Optional[Template]:
        """获取指定模板"""
        return self.templates.get(template_name)

    def render_template(
        self,
        template_name: str,
        **kwargs
    ) -> str:
        """渲染模板"""
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"模板不存在: {template_name}")

        try:
            return template.substitute(**kwargs)
        except KeyError as e:
            raise ValueError(f"模板参数缺失: {e}")

    def get_round1_prompt(
        self,
        user_requirements: str,
        design_context: str = "",
        component_types: List[Dict] = None,
        interface_types: List[Dict] = None
    ) -> str:
        """获取Round 1提示词"""

        # 格式化组件类型
        if component_types:
            comp_text = "\n".join([
                f"### {comp['name']}\n"
                f"- 描述: {comp.get('description', '')}\n"
                f"- 复杂度: {comp.get('complexity', '')}\n"
                f"- 典型场景: {', '.join(comp.get('scenarios', []))}\n"
                for comp in component_types
            ])
        else:
            comp_text = "APPLICATION-SW-COMPONENT-TYPE: 应用软件组件"

        # 格式化接口类型
        if interface_types:
            intf_text = "\n".join([
                f"### {intf['name']}\n"
                f"- 描述: {intf.get('description', '')}\n"
                f"- 通信模式: {intf.get('communication_mode', '')}\n"
                f"- 典型场景: {', '.join(intf.get('scenarios', []))}\n"
                for intf in interface_types
            ])
        else:
            intf_text = "SENDER-RECEIVER-INTERFACE: 发送接收接口"

        return self.render_template(
            "round1_architecture",
            user_requirements=user_requirements,
            design_context=design_context,
            component_types=comp_text,
            interface_types=intf_text
        )

    def get_round2_prompt(
        self,
        architecture_design: Dict[str, Any],
        component_details: List[Dict] = None,
        interface_details: List[Dict] = None,
        constraints: List[str] = None
    ) -> str:
        """获取Round 2提示词"""

        # 格式化架构设计
        arch_text = self._format_architecture_design(architecture_design)

        # 格式化约束
        constraints_text = "\n".join(constraints or ["遵循AUTOSAR标准规范"])

        # 判断是单组件还是多组件
        component_plan = architecture_design.get("component_plan", [])

        if len(component_plan) <= 1:
            # 单组件生成
            return self.render_template(
                "round2_generation",
                architecture_design=arch_text,
                constraints=constraints_text
            )
        else:
            # 多组件生成
            component_list = "\n".join([
                f"{i+1}. {comp.get('name', f'Component{i+1}')} - {comp.get('type', '')} - {comp.get('purpose', '')}"
                for i, comp in enumerate(component_plan)
            ])

            return self.render_template(
                "round2_multi_component",
                architecture_design=arch_text,
                component_count=len(component_plan),
                component_list=component_list,
                constraints=constraints_text
            )

    def _format_architecture_design(self, design: Dict[str, Any]) -> str:
        """格式化架构设计信息"""
        lines = []

        if 'system_analysis' in design:
            lines.append("### 系统分析")
            for key, value in design['system_analysis'].items():
                friendly_key = self._translate_analysis_key(key)
                lines.append(f"- {friendly_key}: {value}")

        if 'component_plan' in design:
            lines.append(f"\n### 组件规划 ({len(design['component_plan'])}个组件)")
            for i, comp in enumerate(design['component_plan'], 1):
                lines.append(f"{i}. **{comp.get('name', f'Component{i}')}**")
                lines.append(f"   - 类型: {comp.get('type', '')}")
                lines.append(f"   - 功能: {comp.get('purpose', '')}")
                lines.append(f"   - 复杂度: {comp.get('estimated_complexity', '')}")

                if 'port_estimates' in comp:
                    ports = comp['port_estimates']
                    if ports.get('input_ports'):
                        lines.append(f"   - 输入端口: {ports['input_ports']}")
                    if ports.get('output_ports'):
                        lines.append(f"   - 输出端口: {ports['output_ports']}")
                lines.append("")

        if 'interface_plan' in design:
            lines.append(f"### 接口规划 ({len(design['interface_plan'])}个接口)")
            for i, intf in enumerate(design['interface_plan'], 1):
                lines.append(f"{i}. **{intf.get('name', f'Interface{i}')}**")
                lines.append(f"   - 类型: {intf.get('type', '')}")
                lines.append(f"   - 通信模式: {intf.get('communication_pattern', '')}")
                lines.append(f"   - 数据类别: {intf.get('data_category', '')}")

                if 'connected_components' in intf:
                    components = intf['connected_components']
                    if components:
                        lines.append(f"   - 连接组件: {', '.join(components)}")
                lines.append("")

        if 'connection_topology' in design:
            lines.append("### 连接拓扑")
            topology = design['connection_topology']
            if topology.get('component_connections'):
                lines.append(f"- 组件连接: {topology['component_connections']}")
            if topology.get('data_flow_paths'):
                lines.append(f"- 数据流向: {topology['data_flow_paths']}")
            if topology.get('control_flow_paths'):
                lines.append(f"- 控制流向: {topology['control_flow_paths']}")

        if 'architecture_rationale' in design:
            lines.append("\n### 设计理由")
            rationale = design['architecture_rationale']
            if rationale.get('design_decisions'):
                lines.append(f"- 关键决策: {rationale['design_decisions']}")
            if rationale.get('tradeoff_analysis'):
                lines.append(f"- 权衡分析: {rationale['tradeoff_analysis']}")

        return "\n".join(lines)

    def get_batch_generation_prompt(
            self,
            batch_info: Dict[str, Any],
            architecture_design: Dict[str, Any],
            constraints: List[str],
            batch_context: str,
            registered_interfaces: List[Dict[str, Any]] = None
    ) -> str:
        """获取分批生成提示词"""

        batch_type = batch_info.get("batch_type", "unknown")
        component_list = batch_info.get("components", [])

        template_text = f"""
    你是AUTOSAR XML分批生成专家。当前正在生成第{batch_info.get('batch_idx', 0) + 1}批组件。

    {batch_context}

    ## 当前批次任务
    批次类型: {batch_type}
    组件数量: {len(component_list)}
    生成目标: {batch_info.get('description', '生成当前批次的组件')}

    ### 要生成的组件:
    """

        for i, comp in enumerate(component_list, 1):
            template_text += f"{i}. **{comp.get('name', f'Component{i}')}**\n"
            template_text += f"   - 类型: {comp.get('type', '')}\n"
            template_text += f"   - 功能: {comp.get('purpose', '')}\n"
            template_text += f"   - 复杂度: {comp.get('estimated_complexity', '')}\n\n"

        # 添加已注册接口信息
        if registered_interfaces:
            template_text += "## 可引用的已生成接口\n"
            for intf in registered_interfaces:
                template_text += f"- {intf['name']}: {intf['description']}\n"

        # 添加语义占位符指导
        template_text += """

    ## 语义占位符使用规范

    对于需要引用其他组件的地方，请使用语义占位符而非具体路径：

    ### 正确示例:
    - REQUIRED-INTERFACE-TREF: "引用温度传感器的数据输出接口"
    - PORT-PROTOTYPE-REF: "连接到电机控制器的转速端口"
    - START-ON-EVENT-REF: "绑定到数据处理器的周期事件"

    ### 错误示例（不要使用具体路径）:
    - REQUIRED-INTERFACE-TREF: "/Components/TempSensor/Ports/DataOut"

    ### 语义占位符规则:
    1. 使用自然语言描述引用意图
    2. 明确指出目标组件的功能特征
    3. 说明连接的数据类型或用途
    4. 保持描述的简洁和准确

    ## 约束规则
    """

        # 添加约束
        for constraint in constraints:
            template_text += f"- {constraint}\n"

        template_text += """

    ## 生成要求
    1. 严格按照提供的JSON Schema生成
    2. 每个组件必须有唯一的UUID
    3. 组件名称必须与架构设计中的名称一致
    4. 使用语义占位符处理所有外部引用
    5. 确保端口定义与接口规划匹配
    6. 内部行为定义要完整且合理

    请生成当前批次所有组件的完整JSON结构。
    """

        return template_text

    def get_semantic_placeholder_guidance(self) -> str:
        """获取语义占位符指导"""
        return """
    ## 语义占位符设计指导

    ### 组件引用模式
    - "引用{功能描述}组件的{端口类型}端口"
    - "连接到{组件角色}的{数据类型}接口"
    - "订阅{系统功能}管理器的{事件类型}"

    ### 接口引用模式
    - "使用{数据内容}传输接口"
    - "提供{服务功能}访问接口"
    - "管理{状态类型}切换接口"

    ### 内部引用模式
    - "绑定到{功能名称}的{事件类型}事件"
    - "执行{处理逻辑}的运行实体"
    - "访问{数据源}的数据访问点"
    """

    def _translate_analysis_key(self, key: str) -> str:
        """翻译系统分析的键"""
        translations = {
            "functional_decomposition": "功能分解",
            "data_flow_analysis": "数据流分析",
            "timing_requirements": "时序要求",
            "scalability_considerations": "可扩展性考虑"
        }
        return translations.get(key, key)

    def generate_component_specific_prompt(
        self,
        component_plan: Dict[str, Any],
        context: str = ""
    ) -> str:
        """为单个组件生成特定的提示词"""

        comp_name = component_plan.get('name', 'Component')
        comp_type = component_plan.get('type', 'APPLICATION-SW-COMPONENT-TYPE')
        comp_purpose = component_plan.get('purpose', '')

        prompt = f"""
## 组件特定生成要求

### 目标组件: {comp_name}
- 类型: {comp_type}
- 功能: {comp_purpose}

### 生成重点
1. 组件名称必须为: {comp_name}
2. 根据功能目的设计合适的端口
3. 内部行为要体现组件特性
4. Runnable和事件命名要与组件功能相关

### 上下文信息
{context}

请生成该组件的完整ARXML结构。
"""
        return prompt

# 全局模板管理器实例
template_manager = PromptTemplateManager()