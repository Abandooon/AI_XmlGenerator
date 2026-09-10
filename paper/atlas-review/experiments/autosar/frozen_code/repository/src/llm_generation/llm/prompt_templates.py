"""Provider-visible prompt templates for the two-stage AUTOSAR pipeline."""
import json
from string import Template
from typing import Dict, Any, List, Optional


class PromptTemplateManager:
    """Manage the provider-visible prompts used by generation."""

    def __init__(self):
        """Initialize the template registry."""
        self.templates = {
            # Round 1 架构设计模板（增强）
            "round1_architecture": self._get_enhanced_round1_template(),
            # Round2（接口与单组件）
            "round2_interfaces": self.get_round2_prompt_interfaces,
            "round2_component": self.get_round2_prompt_single,
        }

    def _get_enhanced_round1_template(self) -> Template:
        template_text = """
        You are an AUTOSAR software-component architecture specialist. Return a
        concise design that strictly matches the JSON Schema supplied below. Do
        not expose chain-of-thought, commentary, or fields outside that schema.
        ==========================================
        This pipeline has two stages:
        - Round 1 (this task): architecture design and deterministic element
          selection for the system, interfaces, and each component.
        - Round 2: generate detailed structured values for each interface and
          component under schemas compiled from the Round 1 design.

        Round 1 responsibilities:
        ------------------------------------------
        1. system_analysis:
           - functional_decomposition: define each component's responsibility
             and boundary.
           - data_flow_analysis: describe direction, data type, and timing of
             every inter-component flow.
           - identify each interface's payload and communication pattern.
           - identify dependencies and invocation chains.
        2. connection_topology
           - describe component/interface connections and flow direction.
        3. architecture_rationale
           - give concise, output-facing reasons for the architecture choices.

        4. component_plan:
           - behavioral_characteristics: state processing logic, triggers,
             periods, state transitions, and input-to-output flow.
           - element_design: select every required internal element, including
             exact port types, event types, runnable structure, and data-access
             points.

        5. interface_plan:
           - communication_pattern: state synchronous/asynchronous behavior,
             frequency, latency, buffering, and error handling.
           - data_elements/operations: list the required payload elements or
             operations.
           - identify the components connected through each interface.

        6. element_design preselection (critical):
            Round 2 compiles its provider schema from these decisions:
            - every selection changes the generated XML structure;
            - each preselect.include list is the exact set of child elements to
              include;
            - each union variant fixes the concrete data-access representation.
            
            AUTOSAR encapsulation is mandatory:
            - an event may start only a runnable owned by the same component;
            - component data access must use that component's own ports;
            - cross-component communication is mediated by RTE port connections,
              never by a direct reference to another component's port.

        Architecture quality criteria:
        ------------------------------------------
        - Completeness: every component and interface has a defined role.
        - Consistency: connected ports use matching interfaces and data types.
        - Traceability: every design decision follows from the requirement.
        - Realizability: element_design is detailed enough for Round 2.

        Round 2 will compile schemas and instances strictly from this output.
        
        ## User requirement
        $user_requirements
    
        ## Design context
        $design_context

        ---

        ## Deterministic AUTOSAR element selections
        Populate `component_plan[].element_design.selections` for every structure or value
        explicitly required by the user, including optional XSD elements under ports,
        ComSpecs, events, internal behaviors, and runnable substructures.
        - `path` is the XML-tag path relative to the component payload. Use exact AUTOSAR
          tags, e.g. `["PORTS", "R-PORT-PROTOTYPE", "REQUIRED-COM-SPECS",
          "NONQUEUED-RECEIVER-COM-SPEC", "ALIVE-TIMEOUT"]`.
        - Every `path` entry must be an uppercase AUTOSAR XML tag, or the final
          `@DEST`/`#TEXT` entry. Never put an instance name or lexical value in `path`;
          instance names belong only in `anchors` or `value`.
        - Use final `#TEXT` only to select an XML element's direct text value. Phase2
          resolves whether that text is represented as a scalar or a `#text` property;
          do not guess the provider JSON representation.
        - Do not select the component root `SHORT-NAME`; Round2 already constrains it to
          the component plan name.
        - Use a separate selection for every exact leaf value (`SHORT-NAME`, `#TEXT`,
          `@DEST`, timeout, period, enum, and reference value).
        - `min_occurs` and `max_occurs` express the requirement, not an XSD guess.
        - For values under repeated structures, add `anchors`, e.g.
          `{"path_index": 1, "short_name": "Rp_HCU01_TqCmd"}` anchors the
          R-PORT-PROTOTYPE segment. Use an empty array when no anchor is needed.
        - Set `value_present=true` only for an exact lexical value; otherwise set it to
          false and set `value` to the empty string.
        - An exact value must target a scalar XSD leaf: a final `#TEXT`, `@ATTRIBUTE`,
          or primitive element. Never attach an exact value to a complex container such
          as `INIT-VALUE`; select its concrete value-specification branch and scalar leaf.
        - Do not invent paths. If the requirement cannot be expressed using known AUTOSAR
          tags, leave no substitute and append an object with the original requirement and
          reason to `component_plan[].element_design.unsupported`.
        - Always emit `unsupported`; use an empty array only when every requested component
          element has a supported selection path.

        ## Runnable element-preselection task
        For each runnable, emit `elements` as an array of objects:
        - `key`: choose a configured element key such as VariableAccess,
          ServerCallPoints, ModeAccessPoint, ModeSwitchPoint, or ParameterAccess.
        - `wrapper`: name the containing XML wrapper when one exists, such as
          DATA-SEND-POINTS or SERVER-CALL-POINTS.
        - `preselect`: make deterministic choices for every union inside it:
          - `of`: union name, such as ACCESSED-VARIABLE or MODE-GROUP-IREF.
          - `variant`: selected branch name.
          - `include`: choose exactly the required child keys from that variant's
            selectable_children. Do not list unselected or mutually exclusive keys.
          - `notes`: optional concise rationale.

        ### Preselection reference
        - VariableAccess:
          - ACCESSED-VARIABLE selects exactly one of AUTOSAR-VARIABLE-IREF,
            AUTOSAR-VARIABLE-IN-IMPL-DATATYPE, or LOCAL-VARIABLE-REF.
          - TARGET-DATA-PROTOTYPE-REF is required in the first two branches.
            A common AUTOSAR-VARIABLE-IREF selection is exactly
            `["PORT-PROTOTYPE-REF", "TARGET-DATA-PROTOTYPE-REF"]`; do not also
            select mutually exclusive CONTEXT-* or ROOT-* children.
        - ModeAccessPoint / ModeSwitchPoint:
          - MODE-GROUP-IREF selects exactly one of
            R-MODE-GROUP-IN-ATOMIC-SWC-INSTANCE-REF or
            P-MODE-GROUP-IN-ATOMIC-SWC-INSTANCE-REF.
        - ParameterAccess:
          - ACCESSED-PARAMETER selects exactly one of AUTOSAR-PARAMETER-IREF
            or LOCAL-PARAMETER-REF.
        - ServerCallPoints:
          - SERVER-CALL-POINTS may include SYNCHRONOUS-SERVER-CALL-POINT
            (OPERATION-IREF/TIMEOUT/EXCLUSIVE-AREA) and/or
            ASYNCHRONOUS-SERVER-CALL-POINT (OPERATION-IREF/TIMEOUT).
                                     
        element_design example:
        ------------------------------------------
        ```json
        {
            "runnables": [
              {
                "name": "Processing_Runnable",
                "elements": [
                  {
                    "key": "DATA-RECEIVE-POINT-BY-ARGUMENTS",
                    "wrapper": "DATA-RECEIVE-POINT-BY-ARGUMENTS",
                    "preselect": [
                      {
                        "of": "ACCESSED-VARIABLE",
                        "variant": "AUTOSAR-VARIABLE-IREF",
                        "include": ["PORT-PROTOTYPE-REF", "TARGET-DATA-PROTOTYPE-REF"],
                        "notes": "Read data through the input port"
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
                        "notes": "Send processed data through the output port"
                      }
                    ]
                  }
                ]
              }
            ]
          }
        }
        ## Output JSON Schema
        HARD RULES:
            - Return exactly one JSON object matching the supplied JSON Schema.
            - Return no explanation, comments, prose, or Markdown fences.
            - Escape newlines inside JSON strings as \\n.
            - Do not use trailing commas.
            - Use underscores, not hyphens, in generated `name` values.
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
        """Build the Round 1 prompt with configured enums and JSON Schema."""
        # config.allowed_types 的枚举展示（主信息源）
        def _fmt_allowed(title, items):
            if not items:
                return f"{title}: not restricted by configuration; use the standard AUTOSAR set"
            lines = [f"{title}:"]
            for s in items:
                lines.append(f"- {s}")
            return "\n".join(lines)

        component_types_allowed_text = _fmt_allowed("Allowed component types", component_types_allowed or [])
        interface_types_allowed_text = _fmt_allowed("Allowed interface types", interface_types_allowed or [])

        # JSON Schema 文本（避免 None）
        schema_text = json.dumps(architecture_schema or {}, ensure_ascii=False, indent=2)

        template = self.get_template("round1_architecture") or self._get_enhanced_round1_template()
        return template.substitute(
            user_requirements=user_requirements,
            design_context=design_context or "No additional design context.",
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
        """Build the interface-only Round 2 prompt."""
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
            You are an AUTOSAR interface-modeling specialist. Generate only the
            interface object collection and match the Interface JSON Schema
            exactly. Do not generate component objects.

            ## Round 1 system analysis (read only)
            ```json
            {sys_analysis_json} 
            ```
            ## Round 1 connection topology (read only)
            ```json
            {conn_topology_json}
            ```
            ## Round 1 interface plan (read only)
            ```json
            {iface_plan_json}
            ```
            ## Standard types available to TYPE-TREF
            Example: <TYPE-TREF DEST="IMPLEMENTATION-DATA-TYPE">/AUTOSAR_Platform/ImplementationDataTypes/sint16</TYPE-TREF>
            ```json
            {standard_types_json}
            ```
            ## Interface JSON Schema (exact contract)
            ```json
            {iface_schema_json}
            ```

            Generation rules:
            - The top-level shape, keys, and nesting must match the schema exactly.
            - Each interface SHORT-NAME equals its Round 1 interface_plan[].name;
              generated SHORT-NAME values use underscores, not hyphens.
            - Keys are exact AUTOSAR XML tags, never camelCase aliases.
            - Every *REF value is an object containing @DEST (target AUTOSAR type)
              and #text (absolute instance path). Example:
              <TARGET-DATA-PROTOTYPE-REF DEST="VARIABLE-DATA-PROTOTYPE">/COM_Interface/SR_Interface_MCU02_MaxTor/MCU02_MaxTor</TARGET-DATA-PROTOTYPE-REF>.
            - Use only fields present in the schema; add no undeclared fields.
        """.strip()

        return dedent(prompt)

    # 替换 PromptTemplateManager.get_round2_prompt_single（整段）
    def get_round2_prompt_single(
            self,
            comp_plan: Dict[str, Any],
            interface_plans: List[Dict[str, Any]],
            component_schema: Dict[str, Any],
            interface_index: List[Dict[str, Any]],
            r1_component_design: Dict[str, Any],
            memory_context: str = "",
            architecture_design: Optional[Dict[str, Any]] = None,
            known_paths: Optional[Dict[str, List[str]]] = None
    ) -> str:
        """Build the single-component Round 2 prompt."""
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

        # ****** 新增逻辑: 格式化已知路径为文本 ******
        known_paths_text = "None; this is the first generated component."
        if known_paths:
            lines = []
            for path_type, path_list in known_paths.items():
                lines.append(f"  # Type: {path_type}")
                for path in path_list:
                    lines.append(f"  - {path}")
            known_paths_text = "\n".join(lines)

            # ****** 新增：AUTOSAR组件封装原则说明 ******
        autosar_encapsulation_rules = f"""

            ## AUTOSAR component encapsulation (mandatory)

            Component behavior may reference runtime elements owned by this
            component only.

            1. Event-start references:
               - Every START-ON-EVENT-REF must reference a RUNNABLE-ENTITY owned
                 by component {comp_name}.
               - Required path: /Components/{comp_name}/{{InternalBehaviorName}}/{{RunnableName}}
               - Valid examples:
                 * /Components/{comp_name}/IB_Main/Init_Runnable
                 * /Components/{comp_name}/IB_Main/Control_Process_Runnable
                 * /Components/{comp_name}/IB_Main/Periodic_Task_100ms
               - Invalid examples:
                 * /Components/OtherComponent/SomeRunnable (other component)
                 * /Components/{comp_name}/Internal/Extra/SubRunnable (wrong depth)

            2. Port-access references:
               - PORT-PROTOTYPE-REF in DATA-SEND-POINTS,
                 DATA-RECEIVE-POINT-BY-ARGUMENTS, or DATA-READ-ACCESSS must
                 reference a port owned by component {comp_name}.
               - Required path: /Components/{comp_name}/{{PortName}}
               - Valid examples:
                 * /Components/{comp_name}/P_Port_Status
                 * /Components/{comp_name}/R_Port_TempSensor
                 * /Components/{comp_name}/PR_Port_ServiceInterface
               - Invalid examples:
                 * /Components/OtherComponent/SomePort (other component)
                 * /Components/{comp_name}/Ports/P_Port_Status (extra container)

            3. Service-call references:
               - CONTEXT-R-PORT-REF and CONTEXT-P-PORT-REF under
                 SERVER-CALL-POINTS must use a port owned by {comp_name} and the
                 same port path format above.

            4. Interface data-element references:
               - TARGET-DATA-PROTOTYPE-REF may reference an element in any
                 generated interface.
               - Select its path from the schema enum when an enum is present.
               - Required path: /COM_Interface/{{InterfaceName}}/{{DataElementName}}
               - Examples:
                 * /COM_Interface/TempSR_Interface/SeatLeft_Sensor1_Temp
                 * /COM_Interface/CAN_Setting_Interface/Requested_Level_Left

            Important:
            - The schema intentionally has no enum for this component's own
              port and runnable references because those instances are being
              created now. Construct them from the Round 1 names.
            - Port paths are exactly /Components/{comp_name}/{{PortName}}.
            - Runnable paths are exactly
              /Components/{comp_name}/{{InternalBehaviorName}}/{{RunnableName}}.
            - Cross-component communication and triggering must be mediated by
              RTE port connections. A component never directly references a
              runtime element owned by another component.
            """

        prompt = f"""
            You are an AUTOSAR structured-value generation specialist. Generate
            exactly one component JSON instance matching the Component JSON
            Schema below. Do not emit interface objects or fields outside the schema.

            Component: {comp_name} (type: {comp_type})
        
            {autosar_encapsulation_rules}
            
            ## Round 1 system analysis (read only)
            ```json
            {sys_analysis_json}
            ```
            ## Round 1 connection topology (read only)
            ```json
            {conn_topology_json}
            ```
            ## Round 1 interface plan (read only)
            ```json
            {iface_plan_json}
            ```
            ## Interface instance index
            Read-only candidates for *-INTERFACE-TREF; do not create interface objects.
            ```json
            {iface_index_json}
            ```
            
            ## Previously generated instance paths for *-REF fields
            Prefer these paths when a valid reference target is listed.
            ```
            {known_paths_text}
            ```
            
            ## Complete Round 1 component_plan entry (read only)
            ```json
            {r1_design_json}
            ```
            ## Component JSON Schema (exact contract)
            ```json
            {comp_schema_json}
            ```
            Generation rules:
            - The top-level object contains only {comp_type}.
            - Its SHORT-NAME is exactly {comp_name}.
            - Keys are exact AUTOSAR XML tags, never camelCase aliases.
            
            Reference rules:
            Every *REF value is an object with:
            - @DEST: target AUTOSAR type, selected from the schema enum.
            - #text: absolute AUTOSAR instance path.
            
            Path strategy:
            1. If #text has an enum, select one enumerated path.
            2. Otherwise construct only a same-component path using Round 1 names:
               - Port: /Components/{comp_name}/{{PortName}}
               - Runnable: /Components/{comp_name}/{{InternalBehaviorName}}/{{RunnableName}}
            
            Valid example:
            ```json
            {{
              "START-ON-EVENT-REF": {{
                "@DEST": "RUNNABLE-ENTITY",
                "#text": "/Components/{comp_name}/IB_Main/Control_Process_Runnable"
              }},
              "PORT-PROTOTYPE-REF": {{
                "@DEST": "R-PORT-PROTOTYPE",
                "#text": "/Components/{comp_name}/R_Port_TempSR"
              }},
              "TARGET-DATA-PROTOTYPE-REF": {{
                "@DEST": "VARIABLE-DATA-PROTOTYPE",
                "#text": "/COM_Interface/TempSR_Interface/SeatLeft_Sensor1_Temp"
              }}
            }}
            ```
            
            Numeric values do not include an `ms` suffix. JSON booleans are
            lowercase `true` and `false`. Use only schema-declared fields.
        """.strip()

        return dedent(prompt)

    def _translate_analysis_key(self, key: str) -> str:
        """Return a provider-facing label for a system-analysis key."""
        translations = {
            "functional_decomposition": "Functional decomposition",
            "data_flow_analysis": "Data-flow analysis",
            "timing_requirements": "Timing requirements",
            "scalability_considerations": "Scalability considerations",
        }
        return translations.get(key, key)

    def get_template(self, template_name: str) -> Optional[Template]:
        """Return a named prompt template, if registered."""
        return self.templates.get(template_name)


# 全局模板管理器实例
template_manager = PromptTemplateManager()
