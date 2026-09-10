#!/usr/bin/env python3
# dynamic_gbnf_strategy.py - 动态GBNF生成策略

from typing import Dict, Any, Tuple

import aiohttp

from prompt_mapper import AutosarPromptMapper


class DynamicGBNFStrategy:
    def __init__(self, template_path: str = "autosar_template.gbnf"):
        self.template_path = template_path
        self.template = self._load_template()
        # 初始化prompt映射器
        self.prompt_mapper = AutosarPromptMapper()

    def _validate_and_normalize_requirements(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """验证和规范化需求 - 修复data_element字段"""
        # 确保所有必要字段存在
        normalized = {
            "component_name": requirements.get("component_name", "ASW_COM"),
            "p_ports": requirements.get("p_ports", []),
            "r_ports": requirements.get("r_ports", []),
            "timing_events": requirements.get("timing_events", []),
            "runnables": requirements.get("runnables", [])
        }

        # 🔥 修复R-PORT的data_element字段
        for r_port in normalized["r_ports"]:
            # 确保必需字段存在
            if "alive_timeout" not in r_port:
                r_port["alive_timeout"] = "0.3"
            if "handle_timeout_type" not in r_port:
                r_port["handle_timeout_type"] = "NONE"

            # 🔥 关键修复：确保data_element字段存在
            if "data_element" not in r_port:
                signal = r_port.get('signal', r_port['name'].replace('RPort_', '').replace('CalPort_', ''))
                interface = r_port.get('interface', f'/COM_Interface/SR_Interface_{signal}')

                # 信号名映射（处理特殊情况）
                signal_mapping = {
                    'HCU01_TqCmd': 'HCU01_Tq_Cmd',  # 注意这个特殊映射
                    'HCU01_Shift': 'HCU01_Shift',
                    'HCU02_Poweroff': 'HCU02_Poweroff',
                    'MCU01_EmergShutDown': 'MCU01_EmergShutDown',
                    'MCU02_MaxTor': 'MCU02_MaxTor',
                    'MCU03_NRF_IdcSamp': 'MCU03_NRF_IdcSamp'
                }

                data_element_name = signal_mapping.get(signal, signal)
                r_port["data_element"] = f'{interface}/{data_element_name}'

        # 如果没有runnable，至少创建一个
        if not normalized["runnables"]:
            normalized["runnables"] = [{
                "name": "RE_COM_SWC",
                "symbol": "RE_COM_SWC_func",
                "receive_access_count": len(normalized["r_ports"]),
                "send_access_count": len(normalized["p_ports"])
            }]

        # 如果没有timing event，为每个runnable创建一个
        if not normalized["timing_events"]:
            normalized["timing_events"] = [{
                "name": f"TE_{runnable['name']}",
                "period": "0.01",
                "runnable_ref": f"/COM_SWC/{normalized['component_name']}/SwcInternalBehavior/{runnable['name']}"
            } for runnable in normalized["runnables"]]

        return normalized

    def _get_default_requirements(self) -> Dict[str, Any]:
        """获取默认需求配置 - 确保包含data_element字段"""
        return {
            "component_name": "ASW_COM",
            "p_ports": [
                {"name": "PPort_MCU01_EmergShutDown", "interface": "/COM_Interface/SR_Interface_MCU01_EmergShutDown"},
                {"name": "PPort_MCU02_MaxTor", "interface": "/COM_Interface/SR_Interface_MCU02_MaxTor"},
                {"name": "PPort_MCU03_NRF_IdcSamp", "interface": "/COM_Interface/SR_Interface_MCU03_NRF_IdcSamp"}
            ],
            "r_ports": [
                {
                    "name": "RPort_HCU01_TqCmd",
                    "interface": "/COM_Interface/SR_Interface_HCU01_TqCmd",
                    "data_element": "/COM_Interface/SR_Interface_HCU01_TqCmd/HCU01_Tq_Cmd",  # 🔥 包含data_element
                    "alive_timeout": "0.3",
                    "handle_timeout_type": "NONE"
                },
                {
                    "name": "RPort_HCU01_Shift",
                    "interface": "/COM_Interface/SR_Interface_HCU01_Shift",
                    "data_element": "/COM_Interface/SR_Interface_HCU01_Shift/HCU01_Shift",  # 🔥 包含data_element
                    "alive_timeout": "0.3",
                    "handle_timeout_type": "NONE"
                },
                {
                    "name": "RPort_HCU02_Poweroff",
                    "interface": "/COM_Interface/SR_Interface_HCU02_Poweroff",
                    "data_element": "/COM_Interface/SR_Interface_HCU02_Poweroff/HCU02_Poweroff",  # 🔥 包含data_element
                    "alive_timeout": "0.3",
                    "handle_timeout_type": "NONE"
                }
            ],
            "timing_events": [
                {
                    "name": "TE_COM_SWC",
                    "period": "0.01",
                    "runnable_ref": "/COM_SWC/ASW_COM/SwcInternalBehavior/RE_COM_SWC"
                }
            ],
            "runnables": [
                {
                    "name": "RE_COM_SWC",
                    "symbol": "RE_COM_SWC_func",
                    "receive_access_count": 3,
                    "send_access_count": 3
                }
            ]
        }

    def _load_template(self) -> str:
        """加载GBNF模板"""
        # 这里简化为直接返回模板字符串
        # 实际使用时应从文件加载
        return '''start: autosar_component

autosar_component: "<APPLICATION-SW-COMPONENT-TYPE>" component_content "</APPLICATION-SW-COMPONENT-TYPE>"

component_content: short_name ports internal_behaviors

short_name: "<SHORT-NAME>" name_value "</SHORT-NAME>"
name_value: /[A-Za-z][A-Za-z0-9_]*/

ports: "<PORTS>" {p_ports_rule} {r_ports_rule} "</PORTS>"

{p_port_definitions}

{r_port_definitions}

internal_behaviors: "<INTERNAL-BEHAVIORS>" swc_internal_behavior "</INTERNAL-BEHAVIORS>"
swc_internal_behavior: "<SWC-INTERNAL-BEHAVIOR>" behavior_content "</SWC-INTERNAL-BEHAVIOR>"
behavior_content: short_name events runnables

events: "<EVENTS>" {timing_events_rule} "</EVENTS>"
{timing_event_definitions}

runnables: "<RUNNABLES>" {runnable_entities_rule} "</RUNNABLES>"
{runnable_definitions}

{variable_access_definitions}

uuid_attr: "UUID=\\\"" uuid_value "\\\""
uuid_value: /[a-f0-9]{{8}}-[a-f0-9]{{4}}-[a-f0-9]{{4}}-[a-f0-9]{{4}}-[a-f0-9]{{12}}/

symbol: "<SYMBOL>" symbol_name "</SYMBOL>"
symbol_name: /[A-Za-z_][A-Za-z0-9_]*/

{path_definitions}'''

    # !/usr/bin/env python3
    # 修复后的GBNF生成方法 - 解决vLLM Internal Server Error

    def generate_gbnf_from_requirements(self, requirements: Dict[str, Any]) -> str:
        """根据需求生成GBNF规则 - 修复语法错误和转义问题"""
        print(f"🔧 Generating GBNF for: {len(requirements['p_ports'])} P-ports, {len(requirements['r_ports'])} R-ports")

        # 使用简化的GBNF模板，避免复杂的字符串转义
        base_template = '''start: autosar_component

    autosar_component: "<APPLICATION-SW-COMPONENT-TYPE>" component_content "</APPLICATION-SW-COMPONENT-TYPE>"

    component_content: short_name ports internal_behaviors

    short_name: "<SHORT-NAME>" component_name "</SHORT-NAME>"
    component_name: "ASW_COM"

    ports: "<PORTS>" port_list "</PORTS>"
    port_list: {port_rules}

    {port_definitions}

    internal_behaviors: "<INTERNAL-BEHAVIORS>" swc_internal_behavior "</INTERNAL-BEHAVIORS>"
    swc_internal_behavior: "<SWC-INTERNAL-BEHAVIOR>" behavior_content "</SWC-INTERNAL-BEHAVIOR>"
    behavior_content: short_name events runnables

    events: "<EVENTS>" timing_event "</EVENTS>"
    timing_event: "<TIMING-EVENT" " " uuid_attr ">" timing_event_content "</TIMING-EVENT>"
    timing_event_content: short_name start_on_event_ref period
    start_on_event_ref: "<START-ON-EVENT-REF" " " dest_attr ">" runnable_path "</START-ON-EVENT-REF>"
    dest_attr: "DEST=" quote "RUNNABLE-ENTITY" quote
    runnable_path: "/COM_SWC/ASW_COM/SwcInternalBehavior/RE_COM_SWC"
    period: "<PERIOD>0.01</PERIOD>"

    runnables: "<RUNNABLES>" runnable_entity "</RUNNABLES>"
    runnable_entity: "<RUNNABLE-ENTITY" " " uuid_attr ">" runnable_content "</RUNNABLE-ENTITY>"
    runnable_content: short_name data_receive_points data_send_points symbol
    data_receive_points: "<DATA-RECEIVE-POINT-BY-ARGUMENTS>" {receive_access_rules} "</DATA-RECEIVE-POINT-BY-ARGUMENTS>"
    data_send_points: "<DATA-SEND-POINTS>" {send_access_rules} "</DATA-SEND-POINTS>"
    symbol: "<SYMBOL>RE_COM_SWC_func</SYMBOL>"

    {variable_access_definitions}

    uuid_attr: "UUID=" quote uuid_value quote
    uuid_value: /[a-f0-9]{{8}}-[a-f0-9]{{4}}-[a-f0-9]{{4}}-[a-f0-9]{{4}}-[a-f0-9]{{12}}/
    quote: "\\""'''

        # 构建端口规则列表
        port_rules = []
        port_definitions = []

        # 处理P-PORT
        p_port_count = len(requirements["p_ports"])
        for i in range(p_port_count):
            port_rules.append(f"p_port_{i + 1}")

            p_port = requirements["p_ports"][i]
            interface_path = p_port['interface'].replace('/', '\\/')  # 转义斜杠

            port_def = f'''p_port_{i + 1}: "<P-PORT-PROTOTYPE" " " uuid_attr ">" p_port_content_{i + 1} "</P-PORT-PROTOTYPE>"
    p_port_content_{i + 1}: short_name provided_interface_tref_{i + 1}
    provided_interface_tref_{i + 1}: "<PROVIDED-INTERFACE-TREF" " " p_dest_attr ">" p_interface_path_{i + 1} "</PROVIDED-INTERFACE-TREF>"
    p_dest_attr: "DEST=" quote "SENDER-RECEIVER-INTERFACE" quote
    p_interface_path_{i + 1}: "{interface_path}"'''

            port_definitions.append(port_def)

        # 处理R-PORT
        r_port_count = len(requirements["r_ports"])
        for i in range(r_port_count):
            port_rules.append(f"r_port_{i + 1}")

            r_port = requirements["r_ports"][i]
            interface_path = r_port['interface'].replace('/', '\\/')
            data_element_path = r_port['data_element'].replace('/', '\\/')
            alive_timeout = r_port['alive_timeout']
            handle_timeout_type = r_port['handle_timeout_type']

            port_def = f'''r_port_{i + 1}: "<R-PORT-PROTOTYPE" " " uuid_attr ">" r_port_content_{i + 1} "</R-PORT-PROTOTYPE>"
    r_port_content_{i + 1}: short_name required_com_specs_{i + 1} required_interface_tref_{i + 1}
    required_com_specs_{i + 1}: "<REQUIRED-COM-SPECS>" nonqueued_receiver_com_spec_{i + 1} "</REQUIRED-COM-SPECS>"
    nonqueued_receiver_com_spec_{i + 1}: "<NONQUEUED-RECEIVER-COM-SPEC>" com_spec_content_{i + 1} "</NONQUEUED-RECEIVER-COM-SPEC>"
    com_spec_content_{i + 1}: data_element_ref_{i + 1} alive_timeout_{i + 1} handle_timeout_type_{i + 1}
    data_element_ref_{i + 1}: "<DATA-ELEMENT-REF" " " r_dest_attr ">" data_element_path_{i + 1} "</DATA-ELEMENT-REF>"
    r_dest_attr: "DEST=" quote "VARIABLE-DATA-PROTOTYPE" quote
    data_element_path_{i + 1}: "{data_element_path}"
    alive_timeout_{i + 1}: "<ALIVE-TIMEOUT>{alive_timeout}</ALIVE-TIMEOUT>"
    handle_timeout_type_{i + 1}: "<HANDLE-TIMEOUT-TYPE>{handle_timeout_type}</HANDLE-TIMEOUT-TYPE>"
    required_interface_tref_{i + 1}: "<REQUIRED-INTERFACE-TREF" " " r_dest_attr ">" r_interface_path_{i + 1} "</REQUIRED-INTERFACE-TREF>"
    r_interface_path_{i + 1}: "{interface_path}"'''

            port_definitions.append(port_def)

        # 组合端口规则
        all_port_rules = " ".join(port_rules) if port_rules else ""

        # 生成变量访问规则
        receive_access_rules = []
        send_access_rules = []
        variable_access_definitions = []

        # 接收访问（R-PORT对应）
        for i in range(r_port_count):
            receive_access_rules.append(f"variable_access_r_{i + 1}")

            r_port = requirements["r_ports"][i]
            port_path = f"/COM_SWC/ASW_COM/{r_port['name']}"
            data_element_path = r_port['data_element'].replace('/', '\\/')

            var_access_def = f'''variable_access_r_{i + 1}: "<VARIABLE-ACCESS" " " uuid_attr ">" variable_access_content_r_{i + 1} "</VARIABLE-ACCESS>"
    variable_access_content_r_{i + 1}: short_name accessed_variable_r_{i + 1}
    accessed_variable_r_{i + 1}: "<ACCESSED-VARIABLE>" autosar_variable_iref_r_{i + 1} "</ACCESSED-VARIABLE>"
    autosar_variable_iref_r_{i + 1}: "<AUTOSAR-VARIABLE-IREF>" port_prototype_ref_r_{i + 1} target_data_prototype_ref_r_{i + 1} "</AUTOSAR-VARIABLE-IREF>"
    port_prototype_ref_r_{i + 1}: "<PORT-PROTOTYPE-REF" " " r_port_dest_attr ">" r_port_path_{i + 1} "</PORT-PROTOTYPE-REF>"
    r_port_dest_attr: "DEST=" quote "R-PORT-PROTOTYPE" quote
    r_port_path_{i + 1}: "{port_path}"
    target_data_prototype_ref_r_{i + 1}: "<TARGET-DATA-PROTOTYPE-REF" " " target_dest_attr ">" target_data_path_r_{i + 1} "</TARGET-DATA-PROTOTYPE-REF>"
    target_dest_attr: "DEST=" quote "VARIABLE-DATA-PROTOTYPE" quote
    target_data_path_r_{i + 1}: "{data_element_path}"'''

            variable_access_definitions.append(var_access_def)

        # 发送访问（P-PORT对应）
        for i in range(p_port_count):
            send_access_rules.append(f"variable_access_s_{i + 1}")

            p_port = requirements["p_ports"][i]
            port_path = f"/COM_SWC/ASW_COM/{p_port['name']}"
            # 为P-PORT生成data element路径
            data_element_path = f"{p_port['interface']}/{p_port['signal']}".replace('/', '\\/')

            var_access_def = f'''variable_access_s_{i + 1}: "<VARIABLE-ACCESS" " " uuid_attr ">" variable_access_content_s_{i + 1} "</VARIABLE-ACCESS>"
    variable_access_content_s_{i + 1}: short_name accessed_variable_s_{i + 1}
    accessed_variable_s_{i + 1}: "<ACCESSED-VARIABLE>" autosar_variable_iref_s_{i + 1} "</ACCESSED-VARIABLE>"
    autosar_variable_iref_s_{i + 1}: "<AUTOSAR-VARIABLE-IREF>" port_prototype_ref_s_{i + 1} target_data_prototype_ref_s_{i + 1} "</AUTOSAR-VARIABLE-IREF>"
    port_prototype_ref_s_{i + 1}: "<PORT-PROTOTYPE-REF" " " p_port_dest_attr ">" p_port_path_{i + 1} "</PORT-PROTOTYPE-REF>"
    p_port_dest_attr: "DEST=" quote "P-PORT-PROTOTYPE" quote
    p_port_path_{i + 1}: "{port_path}"
    target_data_prototype_ref_s_{i + 1}: "<TARGET-DATA-PROTOTYPE-REF" " " target_dest_attr ">" target_data_path_s_{i + 1} "</TARGET-DATA-PROTOTYPE-REF>"
    target_data_path_s_{i + 1}: "{data_element_path}"'''

            variable_access_definitions.append(var_access_def)

        # 应用所有替换
        gbnf = base_template.format(
            port_rules=all_port_rules,
            receive_access_rules=" ".join(receive_access_rules) if receive_access_rules else "",
            send_access_rules=" ".join(send_access_rules) if send_access_rules else ""
        )

        # 添加端口定义和变量访问定义
        gbnf = gbnf.replace("{port_definitions}", "\n\n".join(port_definitions))
        gbnf = gbnf.replace("{variable_access_definitions}", "\n\n".join(variable_access_definitions))

        print(f"✅ Generated GBNF: {len(gbnf)} characters")

        # 基础验证
        if len(gbnf) < 100:
            raise Exception("Generated GBNF too short")

        if "start:" not in gbnf:
            raise Exception("Generated GBNF missing start rule")

        # 检查是否有未替换的占位符
        if "{" in gbnf or "}" in gbnf:
            print("⚠️ Warning: GBNF contains unreplaced placeholders")

        return gbnf

    async def generate(self, vllm_endpoint: str, request: Any) -> Tuple[str, Dict[str, Any]]:
        """主生成方法 - 添加更多调试信息"""
        print("🎯 Using Dynamic GBNF Strategy")

        # 步骤1: 使用prompt_mapper解析需求
        print("📋 Parsing requirements from prompt...")
        try:
            requirements = self.prompt_mapper._extract_all_info(request.prompt)
            print(
                f"🔍 Raw parsing result: {len(requirements.get('p_ports', []))} P-ports, {len(requirements.get('r_ports', []))} R-ports")

            # 调试输出
            for i, r_port in enumerate(requirements.get('r_ports', [])):
                print(
                    f"   R-port {i + 1}: {r_port.get('name', 'Unknown')} -> data_element: {r_port.get('data_element', 'MISSING')}")

        except Exception as e:
            print(f"❌ Parsing failed: {e}, using fallback")
            requirements = self._get_default_requirements()

        # 步骤2: 规范化需求
        try:
            requirements = self._validate_and_normalize_requirements(requirements)
            print(
                f"✅ Normalized requirements: {len(requirements['p_ports'])} P-ports, {len(requirements['r_ports'])} R-ports")

            # 再次检查data_element字段
            for i, r_port in enumerate(requirements['r_ports']):
                if 'data_element' not in r_port:
                    print(f"❌ R-port {i + 1} still missing data_element!")
                    raise KeyError(f"data_element missing for R-port {r_port['name']}")
                else:
                    print(f"✅ R-port {i + 1}: {r_port['name']} -> {r_port['data_element']}")

        except Exception as e:
            print(f"❌ Normalization failed: {e}")
            raise

        # 步骤3: 生成定制GBNF
        print("🔧 Generating customized GBNF...")
        try:
            customized_gbnf = self.generate_gbnf_from_requirements(requirements)
        except Exception as e:
            print(f"❌ GBNF generation failed: {e}")
            raise

        # 步骤4: 使用定制GBNF生成XML
        print("🚀 Generating XML with customized GBNF...")
        vllm_request = {
            "model": "/model/HuggingFace/deepseek-ai/DeepSeek-R1-Distill-Qwen-14B",
            "prompt": request.prompt,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "frequency_penalty": request.frequency_penalty,
            "presence_penalty": request.presence_penalty,
            "stream": False,
            "guided_grammar": customized_gbnf,
            "stop": ["</APPLICATION-SW-COMPONENT-TYPE>", "</COMPONENT>", "</ROOT>"]
        }

        constraints_applied = {
            "gbnf": True,
            "fsm": False,
            "strategy": "dynamic_gbnf",
            "requirements_extracted": requirements,
            "gbnf_customized": True
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                        f"{vllm_endpoint}/v1/completions",
                        json=vllm_request,
                        timeout=aiohttp.ClientTimeout(total=600)
                ) as resp:
                    if resp.status == 200:
                        response = await resp.json()
                        raw_output = response["choices"][0]["text"]
                        print(f"✅ Dynamic GBNF generation successful: {len(raw_output)} chars")
                        return raw_output, constraints_applied
                    else:
                        error_text = await resp.text()
                        raise Exception(f"vLLM error: {error_text}")
            except Exception as e:
                print(f"❌ Request failed: {e}")
                raise