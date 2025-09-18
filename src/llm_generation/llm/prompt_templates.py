"""llm/prompt_templates.py - 优化的提示词模板管理

充分利用Gemini长上下文能力，减少分批，提供完整信息
"""
import json
from textwrap import dedent
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
        }

    def _get_enhanced_round1_template(self) -> Template:
        template_text = """
        你是一个AUTOSAR软件组件架构设计专家，精通AUTOSAR标准和最佳实践，按后面的json schema字段严格匹配进行设计输出，注意不要将你的思考和其他冗余信息输出，请简洁且清晰的填充各字段，不要在功能描述中过于详细。
        ==========================================
        本系统采用两阶段生成架构：
        - Round1（当前阶段）: 架构设计与元素预选 - 决定系统的整体结构和每个组件的内部元素
        - Round2（后续阶段任务）: 基于Round1设计，逐组件生成详细的ARXML内容

        Round1 架构设计师职责:
        ------------------------------------------
        你作为Round1架构设计师，需要完成以下关键决策并按后面的json schema字段严格匹配进行设计输出：

        1. system_analysis（系统分析）:
           - functional_decomposition: 明确每个组件的具体功能职责和分工边界
           - data_flow_analysis: 详细描述组件间的数据流向、数据类型和传输时序
           - 明确每个接口承载的数据类型和通信模式
           - 分析组件间的依赖关系和调用链路
        2. connection_topology
           - 描述系统中组件和接口的连接关系和数据流向
        3. architecture_rationale
           - 记录和说明架构设计的决策依据和思考过程

        4. component_plan（组件设计）:
           - behavioral_characteristics: 详细描述该组件的运行时行为特征
             * 主要处理逻辑和算法
             * 触发条件和执行周期
             * 状态管理和转换逻辑
             * 数据处理流程（输入→处理→输出）
           - element_design: 预先确定组件需要的所有内部元素
             * 精确指定需要的端口类型（P-PORT/R-PORT等）
             * 明确事件类型和触发机制
             * 详细设计每个Runnable的元素结构和数据访问点

        5. interface_plan（接口设计）:
           - communication_pattern: 详细说明该接口的通信模式
             * 同步/异步特性
             * 数据传输频率和时延要求
             * 缓冲策略（队列/最新值）
             * 错误处理机制
           - data_elements/operations: 明确接口包含的数据元素或操作
           - 连接拓扑: 指明哪些组件通过此接口连接

        6. element_design预选（关键）:
           你的预选决策将直接指导Round2的Schema生成：
           - 每个选择都会影响最终生成的XML结构
           - preselect中的include列表决定了哪些子元素会被包含
           - 联合类型的variant选择决定了数据访问的具体实现方式

        架构设计质量标准:
        ------------------------------------------
        - 完整性: 所有组件和接口都有明确的功能定义和实现策略
        - 一致性: 组件间的接口匹配，数据类型统一
        - 可追溯性: 每个设计决策都能追溯到用户需求
        - 可实现性: element_design提供足够的细节供Round2生成

        注意：你的设计输出将作为Round2的输入，Round2会严格按照你的element_design生成对应的Schema和实例。
        
        ## 用户需求
        $user_requirements
    
        ## 设计上下文
        $design_context

        ---

        ## 元素预选任务（由于round2需要根据round1输出来查询组件元素，所以在此阶段需要先预选组件的子元素，务必遵循schema结构化输出）
        对每个 runnable 的 `elements`，按如下对象结构产出（数组）：
        - `key`: 从配置列出的元素键中选择（如 VariableAccess / ServerCallPoints / ModeAccessPoint / ModeSwitchPoint / ParameterAccess ...）
        - `wrapper`: 若该元素位于某 wrapper，请写明（如 DATA-SEND-POINTS / SERVER-CALL-POINTS）
        - `preselect`: 针对该元素内部的“联合位置”执行 **确定性选择**：
          - `of`: 联合名称（如 ACCESSED-VARIABLE / MODE-GROUP-IREF / SERVER-CALL-POINTS）
          - `variant`: 选择的分支名（例如 AUTOSAR-VARIABLE-IREF / LOCAL-VARIABLE-REF / SYNCHRONOUS-SERVER-CALL-POINT 等）
          - `include`: **从该 variant 的可选子键（selectable_children）中，精确挑选这次要生成 Schema 的子键**（不要罗列未选子键，注意子键子键的含义，注意子健互斥）
          - `notes`: 可选说明

        ### 预选清单（参考）
        - VariableAccess:
          - of=ACCESSED-VARIABLE → 3选1：AUTOSAR-VARIABLE-IREF | AUTOSAR-VARIABLE-IN-IMPL-DATATYPE | LOCAL-VARIABLE-REF，
          - 注意AUTOSAR-VARIABLE-IREF和AUTOSAR-VARIABLE-IN-IMPL-DATATYPE中TARGET-DATA-PROTOTYPE-REF为必选项，其他三个子键为互斥选项
            > 例如：`AUTOSAR-VARIABLE-IREF` 只选择 `["PORT-PROTOTYPE-REF","TARGET-DATA-PROTOTYPE-REF"]` 两个子键，此为常见组合；不要输出与PORT-PROTOTYPE-REF互斥的 `CONTEXT-*`、`ROOT-*` 等（**从schema中精确挑选要生成的**）。
        - ModeAccessPoint / ModeSwitchPoint:
          - of=MODE-GROUP-IREF → 2选1：R-MODE-GROUP-IN-ATOMIC-SWC-INSTANCE-REF | P-MODE-GROUP-IN-ATOMIC-SWC-INSTANCE-REF
        - ParameterAccess:
          - of=ACCESSED-PARAMETER → 2选1：AUTOSAR-PARAMETER-IREF | LOCAL-PARAMETER-REF
        - ServerCallPoints:
          - of=SERVER-CALL-POINTS → 可多选：SYNCHRONOUS-SERVER-CALL-POINT（含 OPERATION-IREF/TIMEOUT/EXCLUSIVE-AREA 供选择）
                                     ASYNCHRONOUS-SERVER-CALL-POINT（含 OPERATION-IREF/TIMEOUT 供选择）
                                     
        element_design 输出示例（必须严格遵循）:
        ------------------------------------------
        ```json
        {
            "runnables": [
              {
                "name": "ProcessingRunnable",
                "elements": [
                  {
                    "key": "DATA-RECEIVE-POINT-BY-ARGUMENTS",
                    "wrapper": "DATA-RECEIVE-POINT-BY-ARGUMENTS",
                    "preselect": [
                      {
                        "of": "ACCESSED-VARIABLE",
                        "variant": "AUTOSAR-VARIABLE-IREF",
                        "include": ["PORT-PROTOTYPE-REF", "TARGET-DATA-PROTOTYPE-REF"],
                        "notes": "从输入端口读取数据"
                      }
                    ]
                  },
                  {
                    "key": "DATA-SEND-POINTS",
                    "wrapper": "DATA-SEND-POINTS",
                    "preselect": [
                      {
                        "of": "ACCESSED-VARIABLE",
                        "variant": "AUTOSAR-VARIABLE-IREF",
                        "include": ["PORT-PROTOTYPE-REF", "TARGET-DATA-PROTOTYPE-REF"],
                        "notes": "向输出端口发送处理后的数据"
                      }
                    ]
                  }
                ]
              }
            ]
          }
        }
        ## 输出 JSON Schema（**必须严格匹配此结构与键名**）
        【输出硬规则 / HARD RULES】
            - 仅输出 1 个 JSON 对象，严格匹配稍后给出的 JSON Schema。
            - 不要输出任何解释、注释、自然语言、或 ```markdown 栅栏```。
            - JSON 字符串内不要出现裸换行，请使用 \\n。
            - 不要出现尾随逗号。
        $round1_schema_json
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
          "DATA-RECEIVE-POINT-BY-ARGUMENTS": {
            "VARIABLE-ACCESS": [ { /* VariableAccess 展开，含 AUTOSAR-VARIABLE-IREF 等 */ } ]
          },
          "DATA-SEND-POINTS": {
            "VARIABLE-ACCESS": [ { /* ... */ } ]
          },
          "SERVER-CALL-POINTS": {
            /* 若该容器在KG中是集合，使用数组；否则对象 */
        }
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

    def get_round1_prompt(
            self,
            user_requirements: str,
            design_context: str = "",
            component_types_allowed: List[str] = None,  # ← 新增：来自 config 的枚举
            interface_types_allowed: List[str] = None,  # ← 新增：来自 config 的枚举
            architecture_schema: Dict[str, Any] = None  # ← 新增：Round1 JSON Schema
    ) -> str:
        """获取Round 1架构设计提示词（带 config 枚举与 JSON Schema）"""

    #     # 术语库详细说明（可选）
    #     component_types_text = ""
    #     if component_types:
    #         for comp_type in component_types:
    #             component_types_text += f"""
    # - **{comp_type.get('name', '')}**
    #   描述: {comp_type.get('description', '')}
    #   场景: {', '.join(comp_type.get('scenarios', []) or [])}
    #   复杂度: {comp_type.get('complexity', 'Medium')}
    # """
    #
    #     interface_types_text = ""
    #     if interface_types:
    #         for intf_type in interface_types:
    #             interface_types_text += f"""
    # - **{intf_type.get('name', '')}**
    #   描述: {intf_type.get('description', '')}
    #   通信模式: {intf_type.get('communication_mode', '')}
    #   场景: {', '.join(intf_type.get('scenarios', []) or [])}
    # """

        # config.allowed_types 的枚举展示（主信息源）
        def _fmt_allowed(title, items):
            if not items:
                return f"{title}: （未在 config 指定，使用标准 AUTOSAR 缺省集）"
            lines = [f"{title}:"]
            for s in items:
                lines.append(f"- {s}")
            return "\n".join(lines)

        component_types_allowed_text = _fmt_allowed("组件类型（允许枚举）", component_types_allowed or [])
        interface_types_allowed_text = _fmt_allowed("接口类型（允许枚举）", interface_types_allowed or [])

        # JSON Schema 文本（避免 None）
        schema_text = json.dumps(architecture_schema or {}, ensure_ascii=False, indent=2)

        template = self.get_template("round1_architecture") or self._get_enhanced_round1_template()
        return template.substitute(
            user_requirements=user_requirements,
            design_context=design_context or "无额外上下文",
            # 术语库说明（可选）
            # component_types=component_types_text.strip(),
            # interface_types=interface_types_text.strip(),
            # config 的 allowed 列表（主信息源）
            component_types_allowed=component_types_allowed_text,
            interface_types_allowed=interface_types_allowed_text,
            # JSON Schema
            round1_schema_json=schema_text
        )

    def get_round2_prompt_interfaces(
            self,
            interface_plans: List[Dict[str, Any]],
            interface_schema: Dict[str, Any],
            architecture_design: Optional[Dict[str, Any]] = None,
            memory_context: str = ""
    ) -> str:
        """
        接口实例专用 Prompt（整块文本）：
        - 只生成“接口对象集合”，严格匹配 interface_schema
        - Round1 的 system_analysis / connection_topology / interface_plan 作为只读上下文
        - 不生成组件
        """
        import json
        from textwrap import dedent

        sys_analysis = (architecture_design or {}).get("system_analysis") if architecture_design else None
        conn_topology = (architecture_design or {}).get("connection_topology") if architecture_design else None

        sys_analysis_json = json.dumps(sys_analysis or {}, ensure_ascii=False, indent=2)
        conn_topology_json = json.dumps(conn_topology or {}, ensure_ascii=False, indent=2)
        iface_plan_json = json.dumps(interface_plans or [], ensure_ascii=False, indent=2)
        iface_schema_json = json.dumps(interface_schema or {}, ensure_ascii=False, indent=2)

        prompt = f"""
            你是 AUTOSAR 接口建模专家。**仅生成接口对象集合**，并且必须严格遵守下方“接口 JSON Schema”。不要生成任何组件。
            
            ## Round1 系统分析（只读）
            ```json
            {sys_analysis_json} 
            ```
            Round1 连接拓扑（只读）
            ```json
            {conn_topology_json}
            ```
            
            Round1 接口计划（只读）
            ```json
            {iface_plan_json}
            ```
            
            接口 JSON Schema（严格匹配）
            ```json
            {iface_schema_json}
            ```
            
            生成规则:
            顶层结构、键名、嵌套层级必须严格匹配上述接口 JSON Schema。
            每个接口条目的 SHORT-NAME = Round1 interface_plan[].name。
            键名一律使用 AUTOSAR XML 标签（不要使用驼峰别名）。
            所有 *REF/*TREF/*IREF 字段必须是对象，包含 @DEST 与 #text。
            仅使用 Schema 中出现的字段；不要新增未定义字段。
            {"\n## 对话记忆\n" + memory_context if memory_context else ""}
            """.strip()

        return dedent(prompt)

    def get_round2_prompt_single(
            self,
            comp_plan: Dict[str, Any],
            interface_plans: List[Dict[str, Any]],
            constraints: Dict[str, Any],
            component_schema: Dict[str, Any],
            interface_schema: Dict[str, Any],
            memory_context: str = "",
            architecture_design: Optional[Dict[str, Any]] = None
    ) -> str:
        """单组件实例 Prompt（整块文本）：
        - 只生成一个组件实例，严格匹配 component_schema
        - 注入 Round1 的 system_analysis / connection_topology / interface_plan（只读）
        - 同时提供 interface_schema（只读参考）帮助命名/类型一致性
        """
        import json
        from textwrap import dedent

        comp_name = comp_plan.get("name")
        comp_type = comp_plan.get("type")

        sys_analysis_json = json.dumps((architecture_design or {}).get("system_analysis") or {}, ensure_ascii=False,
                                       indent=2)
        conn_topology_json = json.dumps((architecture_design or {}).get("connection_topology") or {},
                                        ensure_ascii=False, indent=2)
        iface_plan_json = json.dumps(interface_plans or [], ensure_ascii=False, indent=2)
        iface_schema_json = json.dumps(interface_schema or {}, ensure_ascii=False, indent=2)
        comp_schema_json = json.dumps(component_schema or {}, ensure_ascii=False, indent=2)

        prompt = f"""
            你是 AUTOSAR XML 生成专家。仅生成一个组件的 JSON 实例（严格遵守下方“组件 JSON Schema”）。不得输出接口对象。
        
            组件：{comp_name}（类型：{comp_type}）
        
            ## Round1 系统分析（只读）
            ```json
            {sys_analysis_json}
            ```
            Round1 连接拓扑（只读）
            ```json
            {conn_topology_json}
            ```
            Round1 接口计划（只读）
            ```json
            {iface_plan_json}
            ```
            接口 JSON Schema（只读参考，勿输出接口对象）
            ```json
            {iface_schema_json}
            ```
            组件 JSON Schema（严格匹配）
            ```json
            {comp_schema_json}
            ```
            生成规则
            顶层只包含 {comp_type}（组件类型名）。
        
            在该对象内部的 SHORT-NAME 写入组件实例名：{comp_name}。
        
            键名一律使用 AUTOSAR XML 标签（不要使用驼峰别名）。
        
            所有 *REF/*TREF/*IREF 字段为对象，包含 @DEST 与 #text。
        
            仅使用 Schema 中出现的字段；不要新增未定义字段。
        
            不要输出接口对象；接口仅用于命名/类型一致性参考。
            {"\n## 对话记忆\n" + memory_context if memory_context else ""}
            """.strip()

        return dedent(prompt)


    def _format_component_list_detail(self, component_plans: List[Dict[str, Any]]) -> str:
        """格式化组件列表的详细信息"""

        if not component_plans:
            return "无组件"

        lines = []
        for i, comp in enumerate(component_plans, 1):
            comp_name = comp.get("name", f"Component_{i}")
            comp_type = comp.get("type", "APPLICATION-SW-COMPONENT-TYPE")

            lines.append(f"{i}. {comp_name} ({comp_type})")

            # 添加目的描述
            if comp.get("purpose"):
                lines.append(f"   目的: {comp.get('purpose')}")

            # 添加元素设计信息（如果存在）
            element_design = comp.get("element_design", {})

            # 处理端口信息
            if element_design.get("ports", {}).get("needed"):
                port_details = element_design["ports"].get("details", "需要端口")
                lines.append(f"   端口: {port_details}")

            # 处理内部行为信息
            if element_design.get("internal_behaviors", {}).get("needed"):
                # 原来只处理 str/list —— 改成优先处理数组对象
                behavior = comp.get("element_design", {}).get("internal_behaviors", {})
                runnables = behavior.get("runnables", [])

                if isinstance(runnables, list) and runnables and isinstance(runnables[0], dict):
                    for r in runnables:
                        rname = r.get("name", "Runnable")
                        elems = r.get("elements", [])
                        if elems:
                            lines.append(f"   - Runnable: {rname} | elements: {', '.join(elems)}")
                        else:
                            lines.append(f"   - Runnable: {rname}")
                elif isinstance(runnables, list):
                    # 兼容旧格式：["R1","R2"]
                    lines.append(f"   - Runnables: {', '.join(str(r) for r in runnables)}")
                elif isinstance(runnables, str):
                    lines.append(f"   - Runnables: {runnables}")

                # 安全处理events - 可能是字符串或列表
                events = behavior.get("events", [])
                if isinstance(events, str):
                    lines.append(f"   - Events: {events}")
                elif isinstance(events, list) and events:
                    for ev in events:
                        if isinstance(ev, dict):
                            et = ev.get("type", "EVENT")
                            en = ev.get("name", "")
                            trig = ev.get("trigger", "")
                            lines.append(f"   - Event: {et} {en} {('[' + trig + ']') if trig else ''}".rstrip())
                        else:
                            lines.append(f"   - Event: {ev}")

            # 添加复杂度评估
            if comp.get("estimated_complexity"):
                lines.append(f"   复杂度: {comp.get('estimated_complexity')}")

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
            lines.append("- Level 6+: DATA-RECEIVE-POINT-BY-ARGUMENTS, DATA-SEND-POINTS, SERVER-CALL-POINTS, DATA-READ-ACCESSS, DATA-READ-ACCESSSetc.")

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

    def _metamodel_context_from_schema(self, schema: Dict[str, Any], depth: int) -> str:
        # 简明版上下文：列出顶层 keys、definitions 里每种类型的首层字段名
        lines = ["### 元模型结构（来自JSON Schema）"]
        defs = (schema or {}).get("definitions", {}) or {}
        if defs:
            for tname, tschema in defs.items():
                if isinstance(tschema, dict) and tschema.get("type") == "object":
                    keys = list((tschema.get("properties") or {}).keys())
                    lines.append(f"- {tname}: {', '.join(keys[:12])}" if keys else f"- {tname}: (no properties)")
        else:
            # 若没有 definitions，就输出顶层 properties 的概览
            keys = list((schema.get("properties") or {}).keys())
            lines.append(f"- Root: {', '.join(keys[:20])}" if keys else "- Root: (no properties)")
        return "\n".join(lines)



# 全局模板管理器实例
template_manager = PromptTemplateManager()