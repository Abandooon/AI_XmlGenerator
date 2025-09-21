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
            # Round2（接口与单组件）
            "round2_interfaces": self.get_round2_prompt_interfaces,
            "round2_component": self.get_round2_prompt_single,
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

    # （建议同步）替换 PromptTemplateManager.get_round2_prompt_interfaces（整段）以去掉 memory_context 注入
    def get_round2_prompt_interfaces(
            self,
            interface_plans: List[Dict[str, Any]],
            interface_schema: Dict[str, Any],
            architecture_design: Optional[Dict[str, Any]] = None,
            memory_context: str = "",
            standard_types: dict | None = None,
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
        standard_types_json = json.dumps(standard_types or {}, ensure_ascii=False, indent=2)

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
            标准类型库（供 TYPE-TREF 引用，例如：<TYPE-TREF DEST="IMPLEMENTATION-DATA-TYPE">/AUTOSAR_Platform/ImplementationDataTypes/sint16</TYPE-TREF>）
            ```json
            {standard_types_json}
            ```
            接口 JSON Schema（严格匹配）
            ```json
            {iface_schema_json}
            ```

            生成规则:
            顶层结构、键名、嵌套层级必须严格匹配上述接口 JSON Schema。
            每个接口条目的 SHORT-NAME = Round1 interface_plan[].name。
            键名一律使用 AUTOSAR XML 标签（不要使用驼峰别名）。
            所有 *REF 字段必须是对象，包含 @DEST(引向的实例类型) 与 #text(引向的实例路径)。
            仅使用 Schema 中出现的字段；不要新增未定义字段。
        """.strip()

        return dedent(prompt)

    # 替换 PromptTemplateManager.get_round2_prompt_single（整段）
    def get_round2_prompt_single(
            self,
            comp_plan: Dict[str, Any],
            interface_plans: List[Dict[str, Any]],
            constraints: Dict[str, Any],
            component_schema: Dict[str, Any],
            interface_index: List[Dict[str, Any]],
            r1_component_design: Dict[str, Any],
            memory_context: str = "",
            architecture_design: Optional[Dict[str, Any]] = None
    ) -> str:
        """单组件实例 Prompt（整块文本）：
        - 只生成一个组件实例，严格匹配 component_schema
        - 注入 Round1 的 system_analysis / connection_topology / interface_plan（只读）
        - 同时提供 interface_index（只读引用清单），避免模型回写接口对象
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

        # 关键：接口实例索引 + 组件schema + round1 的“组件完整设计计划”
        iface_index_json = json.dumps(interface_index or [], ensure_ascii=False, indent=2)
        comp_schema_json = json.dumps(component_schema or {}, ensure_ascii=False, indent=2)
        r1_design_json = json.dumps(r1_component_design or {}, ensure_ascii=False, indent=2)

        prompt = f"""
            你是 AUTOSAR XML 生成专家。仅生成一个组件的 JSON 实例（严格遵守下方“组件 JSON Schema”）。不得输出接口对象。
            当前是 Round2 的软件组件实例生成任务，你应该根据下面的 Round1 设计上下文，生成当前软件组件的完整定义，并且生成内容和格式要严格匹配“组件 JSON Schema”。

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
            接口实例索引（只读，用于端口的 *-INTERFACE-TREF 引用；不要新增接口对象）
            ```json
            {iface_index_json}
            ```
            Round1 组件设计Schema（完整的 component_plan 条目）
            ```json
            {r1_design_json}
            ```
            组件 JSON Schema（严格匹配）
            ```json
            {comp_schema_json}
            ```
            生成规则
            顶层只包含 {comp_type}（组件类型名）。
            在该对象内部的 SHORT-NAME 写入组件实例名：{comp_name}。
            键名一律使用 AUTOSAR XML 标签（不要使用驼峰别名）。
            所有 *REF 字段为对象，包含 @DEST(引向的实例类型) 与 #text(引向的实例路径)。
            仅使用 Schema 中出现的字段；不要新增未定义字段。
        """.strip()

        return dedent(prompt)

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


# 全局模板管理器实例
template_manager = PromptTemplateManager()