#!/usr/bin/env python3
# 增强版安全动态GBNF策略 - 支持批量处理和参数配置

import time
from typing import Dict, List, Any, Tuple

import aiohttp
import psutil

from prompt_mapper import AutosarPromptMapper


class SafeDynamicGBNFStrategy:
    """增强版安全GBNF策略 - 支持批量处理、参数配置和多样性生成"""

    # 🎯 生成参数配置
    SEEDS: List[int] = [42, 1001, 20250701]  # 随机种子列表
    TEMPERATURE: float = 0.7  # 默认温度
    TOP_P: float = 0.9  # 默认top_p

    def __init__(self, template_path: str = "autosar_template.gbnf"):
        self.template_path = template_path
        # 初始化prompt映射器
        self.prompt_mapper = AutosarPromptMapper()

        # 预定义的安全GBNF模板 - 扩展覆盖更多格式
        self.safe_gbnf_templates = {
            "min_format": self._get_min_gbnf_template(),
            "mid_format": self._get_mid_gbnf_template(),  # 🆕 新增MID格式
            "standard_format": self._get_standard_gbnf_template(),
            "full_format": self._get_full_gbnf_template(),
            "full_with_special": self._get_full_with_special_template()  # 🆕 特殊full格式
        }

        # 批量处理统计
        self.batch_stats = {
            'total_batches': 0,
            'total_prompts': 0,
            'successful_generations': 0,
            'failed_generations': 0,
            'template_usage': {}
        }

    def _get_min_gbnf_template(self) -> str:
        """最小格式的GBNF模板（只有P-PORT）"""
        return '''start: autosar_component

autosar_component: "<APPLICATION-SW-COMPONENT-TYPE>" component_content "</APPLICATION-SW-COMPONENT-TYPE>"

component_content: short_name ports

short_name: "<SHORT-NAME>ASW_COM_MIN</SHORT-NAME>"

ports: "<PORTS>" p_port "</PORTS>"

p_port: "<P-PORT-PROTOTYPE" " " uuid_attr ">" p_port_content "</P-PORT-PROTOTYPE>"
p_port_content: short_name provided_interface_tref
provided_interface_tref: "<PROVIDED-INTERFACE-TREF" " " "DEST=\\"SENDER-RECEIVER-INTERFACE\\">/COM_Interface/SR_Interface_MCU01_EmergShutDown</PROVIDED-INTERFACE-TREF>"

uuid_attr: "UUID=\\"" uuid_value "\\""
uuid_value: /[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}/'''

    def _get_mid_gbnf_template(self) -> str:
        """🆕 中等格式的GBNF模板（2个P-PORT + 1个R-PORT + Runnable）"""
        return '''start: autosar_component

autosar_component: "<APPLICATION-SW-COMPONENT-TYPE>" component_content "</APPLICATION-SW-COMPONENT-TYPE>"

component_content: short_name ports internal_behaviors

short_name: "<SHORT-NAME>ASW_COM_STD</SHORT-NAME>"

ports: "<PORTS>" p_ports r_ports "</PORTS>"

p_ports: p_port_1 p_port_2
p_port_1: "<P-PORT-PROTOTYPE" " " uuid_attr ">" p_port_content_1 "</P-PORT-PROTOTYPE>"
p_port_content_1: short_name_p1 provided_interface_tref_1
short_name_p1: "<SHORT-NAME>PPort_MCU01_EmergShutDown</SHORT-NAME>"
provided_interface_tref_1: "<PROVIDED-INTERFACE-TREF" " " "DEST=\\"SENDER-RECEIVER-INTERFACE\\">/COM_Interface/SR_Interface_MCU01_EmergShutDown</PROVIDED-INTERFACE-TREF>"

p_port_2: "<P-PORT-PROTOTYPE" " " uuid_attr ">" p_port_content_2 "</P-PORT-PROTOTYPE>"
p_port_content_2: short_name_p2 provided_interface_tref_2
short_name_p2: "<SHORT-NAME>PPort_MCU02_MaxTor</SHORT-NAME>"
provided_interface_tref_2: "<PROVIDED-INTERFACE-TREF" " " "DEST=\\"SENDER-RECEIVER-INTERFACE\\">/COM_Interface/SR_Interface_MCU02_MaxTor</PROVIDED-INTERFACE-TREF>"

r_ports: r_port_1
r_port_1: "<R-PORT-PROTOTYPE" " " uuid_attr ">" r_port_content_1 "</R-PORT-PROTOTYPE>"
r_port_content_1: short_name_r1 required_com_specs_1 required_interface_tref_1
short_name_r1: "<SHORT-NAME>RPort_HCU01_TqCmd</SHORT-NAME>"
required_com_specs_1: "<REQUIRED-COM-SPECS>" nonqueued_receiver_com_spec_1 "</REQUIRED-COM-SPECS>"
nonqueued_receiver_com_spec_1: "<NONQUEUED-RECEIVER-COM-SPEC>" com_spec_content_1 "</NONQUEUED-RECEIVER-COM-SPEC>"
com_spec_content_1: data_element_ref_1 alive_timeout handle_timeout_type
data_element_ref_1: "<DATA-ELEMENT-REF" " " "DEST=\\"VARIABLE-DATA-PROTOTYPE\\">/COM_Interface/SR_Interface_HCU01_TqCmd/HCU01_Tq_Cmd</DATA-ELEMENT-REF>"
alive_timeout: "<ALIVE-TIMEOUT>0.3</ALIVE-TIMEOUT>"
handle_timeout_type: "<HANDLE-TIMEOUT-TYPE>NONE</HANDLE-TIMEOUT-TYPE>"
required_interface_tref_1: "<REQUIRED-INTERFACE-TREF" " " "DEST=\\"SENDER-RECEIVER-INTERFACE\\">/COM_Interface/SR_Interface_HCU01_TqCmd</REQUIRED-INTERFACE-TREF>"

internal_behaviors: "<INTERNAL-BEHAVIORS>" swc_internal_behavior "</INTERNAL-BEHAVIORS>"
swc_internal_behavior: "<SWC-INTERNAL-BEHAVIOR>" behavior_content "</SWC-INTERNAL-BEHAVIOR>"
behavior_content: short_name_ib events runnables
short_name_ib: "<SHORT-NAME>SwcInternalBehavior</SHORT-NAME>"

events: "<EVENTS>" timing_event "</EVENTS>"
timing_event: "<TIMING-EVENT" " " uuid_attr ">" timing_event_content "</TIMING-EVENT>"
timing_event_content: short_name_te start_on_event_ref period
short_name_te: "<SHORT-NAME>TE_RE_COM_SWC</SHORT-NAME>"
start_on_event_ref: "<START-ON-EVENT-REF" " " "DEST=\\"RUNNABLE-ENTITY\\">/COM_SWC/ASW_COM_STD/SwcInternalBehavior/RE_COM_SWC</START-ON-EVENT-REF>"
period: "<PERIOD>0.01</PERIOD>"

runnables: "<RUNNABLES>" runnable_entity "</RUNNABLES>"
runnable_entity: "<RUNNABLE-ENTITY" " " uuid_attr ">" runnable_content "</RUNNABLE-ENTITY>"
runnable_content: short_name_re data_receive_points data_send_points symbol
short_name_re: "<SHORT-NAME>RE_COM_SWC</SHORT-NAME>"
data_receive_points: "<DATA-RECEIVE-POINT-BY-ARGUMENTS>" variable_access_r1 "</DATA-RECEIVE-POINT-BY-ARGUMENTS>"
data_send_points: "<DATA-SEND-POINTS>" variable_access_s1 variable_access_s2 "</DATA-SEND-POINTS>"
symbol: "<SYMBOL>RE_COM_SWC_func</SYMBOL>"

variable_access_r1: "<VARIABLE-ACCESS" " " uuid_attr ">" variable_access_content_r1 "</VARIABLE-ACCESS>"
variable_access_content_r1: short_name_var_r1 accessed_variable_r1
short_name_var_r1: "<SHORT-NAME>DRPA_HCU01_TqCmd</SHORT-NAME>"
accessed_variable_r1: "<ACCESSED-VARIABLE>" autosar_variable_iref_r1 "</ACCESSED-VARIABLE>"
autosar_variable_iref_r1: "<AUTOSAR-VARIABLE-IREF>" port_prototype_ref_r1 target_data_prototype_ref_r1 "</AUTOSAR-VARIABLE-IREF>"
port_prototype_ref_r1: "<PORT-PROTOTYPE-REF" " " "DEST=\\"R-PORT-PROTOTYPE\\">/COM_SWC/ASW_COM_STD/RPort_HCU01_TqCmd</PORT-PROTOTYPE-REF>"
target_data_prototype_ref_r1: "<TARGET-DATA-PROTOTYPE-REF" " " "DEST=\\"VARIABLE-DATA-PROTOTYPE\\">/COM_Interface/SR_Interface_HCU01_TqCmd/HCU01_Tq_Cmd</TARGET-DATA-PROTOTYPE-REF>"

variable_access_s1: "<VARIABLE-ACCESS" " " uuid_attr ">" variable_access_content_s1 "</VARIABLE-ACCESS>"
variable_access_content_s1: short_name_var_s1 accessed_variable_s1
short_name_var_s1: "<SHORT-NAME>DSP_MCU01_EmergShutDown</SHORT-NAME>"
accessed_variable_s1: "<ACCESSED-VARIABLE>" autosar_variable_iref_s1 "</ACCESSED-VARIABLE>"
autosar_variable_iref_s1: "<AUTOSAR-VARIABLE-IREF>" port_prototype_ref_s1 target_data_prototype_ref_s1 "</AUTOSAR-VARIABLE-IREF>"
port_prototype_ref_s1: "<PORT-PROTOTYPE-REF" " " "DEST=\\"P-PORT-PROTOTYPE\\">/COM_SWC/ASW_COM_STD/PPort_MCU01_EmergShutDown</PORT-PROTOTYPE-REF>"
target_data_prototype_ref_s1: "<TARGET-DATA-PROTOTYPE-REF" " " "DEST=\\"VARIABLE-DATA-PROTOTYPE\\">/COM_Interface/SR_Interface_MCU01_EmergShutDown/MCU01_EmergShutDown</TARGET-DATA-PROTOTYPE-REF>"

variable_access_s2: "<VARIABLE-ACCESS" " " uuid_attr ">" variable_access_content_s2 "</VARIABLE-ACCESS>"
variable_access_content_s2: short_name_var_s2 accessed_variable_s2
short_name_var_s2: "<SHORT-NAME>DSP_MCU02_MaxTor</SHORT-NAME>"
accessed_variable_s2: "<ACCESSED-VARIABLE>" autosar_variable_iref_s2 "</ACCESSED-VARIABLE>"
autosar_variable_iref_s2: "<AUTOSAR-VARIABLE-IREF>" port_prototype_ref_s2 target_data_prototype_ref_s2 "</AUTOSAR-VARIABLE-IREF>"
port_prototype_ref_s2: "<PORT-PROTOTYPE-REF" " " "DEST=\\"P-PORT-PROTOTYPE\\">/COM_SWC/ASW_COM_STD/PPort_MCU02_MaxTor</PORT-PROTOTYPE-REF>"
target_data_prototype_ref_s2: "<TARGET-DATA-PROTOTYPE-REF" " " "DEST=\\"VARIABLE-DATA-PROTOTYPE\\">/COM_Interface/SR_Interface_MCU02_MaxTor/MCU02_MaxTor</TARGET-DATA-PROTOTYPE-REF>"

uuid_attr: "UUID=\\"" uuid_value "\\""
uuid_value: /[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}/'''

    def _get_standard_gbnf_template(self) -> str:
        """标准格式的GBNF模板（3P+3R）- 保持原有实现"""
        return '''start: autosar_component

autosar_component: "<APPLICATION-SW-COMPONENT-TYPE>" component_content "</APPLICATION-SW-COMPONENT-TYPE>"

component_content: short_name ports internal_behaviors

short_name: "<SHORT-NAME>ASW_COM</SHORT-NAME>"

ports: "<PORTS>" p_ports r_ports "</PORTS>"

p_ports: p_port_1 p_port_2 p_port_3
p_port_1: "<P-PORT-PROTOTYPE" " " uuid_attr ">" p_port_content_1 "</P-PORT-PROTOTYPE>"
p_port_content_1: short_name_p1 provided_interface_tref_1
short_name_p1: "<SHORT-NAME>PPort_MCU01_EmergShutDown</SHORT-NAME>"
provided_interface_tref_1: "<PROVIDED-INTERFACE-TREF" " " "DEST=\\"SENDER-RECEIVER-INTERFACE\\">/COM_Interface/SR_Interface_MCU01_EmergShutDown</PROVIDED-INTERFACE-TREF>"

p_port_2: "<P-PORT-PROTOTYPE" " " uuid_attr ">" p_port_content_2 "</P-PORT-PROTOTYPE>"
p_port_content_2: short_name_p2 provided_interface_tref_2
short_name_p2: "<SHORT-NAME>PPort_MCU02_MaxTor</SHORT-NAME>"
provided_interface_tref_2: "<PROVIDED-INTERFACE-TREF" " " "DEST=\\"SENDER-RECEIVER-INTERFACE\\">/COM_Interface/SR_Interface_MCU02_MaxTor</PROVIDED-INTERFACE-TREF>"

p_port_3: "<P-PORT-PROTOTYPE" " " uuid_attr ">" p_port_content_3 "</P-PORT-PROTOTYPE>"
p_port_content_3: short_name_p3 provided_interface_tref_3
short_name_p3: "<SHORT-NAME>PPort_MCU03_NRF_IdcSamp</SHORT-NAME>"
provided_interface_tref_3: "<PROVIDED-INTERFACE-TREF" " " "DEST=\\"SENDER-RECEIVER-INTERFACE\\">/COM_Interface/SR_Interface_MCU03_NRF_IdcSamp</PROVIDED-INTERFACE-TREF>"

r_ports: r_port_1 r_port_2 r_port_3
r_port_1: "<R-PORT-PROTOTYPE" " " uuid_attr ">" r_port_content_1 "</R-PORT-PROTOTYPE>"
r_port_content_1: short_name_r1 required_com_specs_1 required_interface_tref_1
short_name_r1: "<SHORT-NAME>RPort_HCU01_TqCmd</SHORT-NAME>"
required_com_specs_1: "<REQUIRED-COM-SPECS>" nonqueued_receiver_com_spec_1 "</REQUIRED-COM-SPECS>"
nonqueued_receiver_com_spec_1: "<NONQUEUED-RECEIVER-COM-SPEC>" com_spec_content_1 "</NONQUEUED-RECEIVER-COM-SPEC>"
com_spec_content_1: data_element_ref_1 alive_timeout handle_timeout_type
data_element_ref_1: "<DATA-ELEMENT-REF" " " "DEST=\\"VARIABLE-DATA-PROTOTYPE\\">/COM_Interface/SR_Interface_HCU01_TqCmd/HCU01_Tq_Cmd</DATA-ELEMENT-REF>"
alive_timeout: "<ALIVE-TIMEOUT>0.3</ALIVE-TIMEOUT>"
handle_timeout_type: "<HANDLE-TIMEOUT-TYPE>NONE</HANDLE-TIMEOUT-TYPE>"
required_interface_tref_1: "<REQUIRED-INTERFACE-TREF" " " "DEST=\\"SENDER-RECEIVER-INTERFACE\\">/COM_Interface/SR_Interface_HCU01_TqCmd</REQUIRED-INTERFACE-TREF>"

r_port_2: "<R-PORT-PROTOTYPE" " " uuid_attr ">" r_port_content_2 "</R-PORT-PROTOTYPE>"
r_port_content_2: short_name_r2 required_com_specs_2 required_interface_tref_2
short_name_r2: "<SHORT-NAME>RPort_HCU01_Shift</SHORT-NAME>"
required_com_specs_2: "<REQUIRED-COM-SPECS>" nonqueued_receiver_com_spec_2 "</REQUIRED-COM-SPECS>"
nonqueued_receiver_com_spec_2: "<NONQUEUED-RECEIVER-COM-SPEC>" com_spec_content_2 "</NONQUEUED-RECEIVER-COM-SPEC>"
com_spec_content_2: data_element_ref_2 alive_timeout handle_timeout_type
data_element_ref_2: "<DATA-ELEMENT-REF" " " "DEST=\\"VARIABLE-DATA-PROTOTYPE\\">/COM_Interface/SR_Interface_HCU01_Shift/HCU01_Shift</DATA-ELEMENT-REF>"
required_interface_tref_2: "<REQUIRED-INTERFACE-TREF" " " "DEST=\\"SENDER-RECEIVER-INTERFACE\\">/COM_Interface/SR_Interface_HCU01_Shift</REQUIRED-INTERFACE-TREF>"

r_port_3: "<R-PORT-PROTOTYPE" " " uuid_attr ">" r_port_content_3 "</R-PORT-PROTOTYPE>"
r_port_content_3: short_name_r3 required_com_specs_3 required_interface_tref_3
short_name_r3: "<SHORT-NAME>RPort_HCU02_Poweroff</SHORT-NAME>"
required_com_specs_3: "<REQUIRED-COM-SPECS>" nonqueued_receiver_com_spec_3 "</REQUIRED-COM-SPECS>"
nonqueued_receiver_com_spec_3: "<NONQUEUED-RECEIVER-COM-SPEC>" com_spec_content_3 "</NONQUEUED-RECEIVER-COM-SPEC>"
com_spec_content_3: data_element_ref_3 alive_timeout handle_timeout_type
data_element_ref_3: "<DATA-ELEMENT-REF" " " "DEST=\\"VARIABLE-DATA-PROTOTYPE\\">/COM_Interface/SR_Interface_HCU02_Poweroff/HCU02_Poweroff</DATA-ELEMENT-REF>"
required_interface_tref_3: "<REQUIRED-INTERFACE-TREF" " " "DEST=\\"SENDER-RECEIVER-INTERFACE\\">/COM_Interface/SR_Interface_HCU02_Poweroff</REQUIRED-INTERFACE-TREF>"

internal_behaviors: "<INTERNAL-BEHAVIORS>" swc_internal_behavior "</INTERNAL-BEHAVIORS>"
swc_internal_behavior: "<SWC-INTERNAL-BEHAVIOR>" behavior_content "</SWC-INTERNAL-BEHAVIOR>"
behavior_content: short_name_ib events runnables
short_name_ib: "<SHORT-NAME>SwcInternalBehavior</SHORT-NAME>"

events: "<EVENTS>" timing_event "</EVENTS>"
timing_event: "<TIMING-EVENT" " " uuid_attr ">" timing_event_content "</TIMING-EVENT>"
timing_event_content: short_name_te start_on_event_ref period
short_name_te: "<SHORT-NAME>TE_RE_COM_SWC</SHORT-NAME>"
start_on_event_ref: "<START-ON-EVENT-REF" " " "DEST=\\"RUNNABLE-ENTITY\\">/COM_SWC/ASW_COM/SwcInternalBehavior/RE_COM_SWC</START-ON-EVENT-REF>"
period: "<PERIOD>0.01</PERIOD>"

runnables: "<RUNNABLES>" runnable_entity "</RUNNABLES>"
runnable_entity: "<RUNNABLE-ENTITY" " " uuid_attr ">" runnable_content "</RUNNABLE-ENTITY>"
runnable_content: short_name_re data_receive_points data_send_points symbol
short_name_re: "<SHORT-NAME>RE_COM_SWC</SHORT-NAME>"
data_receive_points: "<DATA-RECEIVE-POINT-BY-ARGUMENTS>" variable_access_r1 variable_access_r2 variable_access_r3 "</DATA-RECEIVE-POINT-BY-ARGUMENTS>"
data_send_points: "<DATA-SEND-POINTS>" variable_access_s1 variable_access_s2 variable_access_s3 "</DATA-SEND-POINTS>"
symbol: "<SYMBOL>RE_COM_SWC_func</SYMBOL>"

variable_access_r1: "<VARIABLE-ACCESS" " " uuid_attr ">" variable_access_content_r1 "</VARIABLE-ACCESS>"
variable_access_content_r1: short_name_var_r1 accessed_variable_r1
short_name_var_r1: "<SHORT-NAME>DRPA_HCU01_TqCmd</SHORT-NAME>"
accessed_variable_r1: "<ACCESSED-VARIABLE>" autosar_variable_iref_r1 "</ACCESSED-VARIABLE>"
autosar_variable_iref_r1: "<AUTOSAR-VARIABLE-IREF>" port_prototype_ref_r1 target_data_prototype_ref_r1 "</AUTOSAR-VARIABLE-IREF>"
port_prototype_ref_r1: "<PORT-PROTOTYPE-REF" " " "DEST=\\"R-PORT-PROTOTYPE\\">/COM_SWC/ASW_COM/RPort_HCU01_TqCmd</PORT-PROTOTYPE-REF>"
target_data_prototype_ref_r1: "<TARGET-DATA-PROTOTYPE-REF" " " "DEST=\\"VARIABLE-DATA-PROTOTYPE\\">/COM_Interface/SR_Interface_HCU01_TqCmd/HCU01_Tq_Cmd</TARGET-DATA-PROTOTYPE-REF>"

variable_access_r2: "<VARIABLE-ACCESS" " " uuid_attr ">" variable_access_content_r2 "</VARIABLE-ACCESS>"
variable_access_content_r2: short_name_var_r2 accessed_variable_r2
short_name_var_r2: "<SHORT-NAME>DRPA_HCU01_Shift</SHORT-NAME>"
accessed_variable_r2: "<ACCESSED-VARIABLE>" autosar_variable_iref_r2 "</ACCESSED-VARIABLE>"
autosar_variable_iref_r2: "<AUTOSAR-VARIABLE-IREF>" port_prototype_ref_r2 target_data_prototype_ref_r2 "</AUTOSAR-VARIABLE-IREF>"
port_prototype_ref_r2: "<PORT-PROTOTYPE-REF" " " "DEST=\\"R-PORT-PROTOTYPE\\">/COM_SWC/ASW_COM/RPort_HCU01_Shift</PORT-PROTOTYPE-REF>"
target_data_prototype_ref_r2: "<TARGET-DATA-PROTOTYPE-REF" " " "DEST=\\"VARIABLE-DATA-PROTOTYPE\\">/COM_Interface/SR_Interface_HCU01_Shift/HCU01_Shift</TARGET-DATA-PROTOTYPE-REF>"

variable_access_r3: "<VARIABLE-ACCESS" " " uuid_attr ">" variable_access_content_r3 "</VARIABLE-ACCESS>"
variable_access_content_r3: short_name_var_r3 accessed_variable_r3
short_name_var_r3: "<SHORT-NAME>DRPA_HCU02_Poweroff</SHORT-NAME>"
accessed_variable_r3: "<ACCESSED-VARIABLE>" autosar_variable_iref_r3 "</ACCESSED-VARIABLE>"
autosar_variable_iref_r3: "<AUTOSAR-VARIABLE-IREF>" port_prototype_ref_r3 target_data_prototype_ref_r3 "</AUTOSAR-VARIABLE-IREF>"
port_prototype_ref_r3: "<PORT-PROTOTYPE-REF" " " "DEST=\\"R-PORT-PROTOTYPE\\">/COM_SWC/ASW_COM/RPort_HCU02_Poweroff</PORT-PROTOTYPE-REF>"
target_data_prototype_ref_r3: "<TARGET-DATA-PROTOTYPE-REF" " " "DEST=\\"VARIABLE-DATA-PROTOTYPE\\">/COM_Interface/SR_Interface_HCU02_Poweroff/HCU02_Poweroff</TARGET-DATA-PROTOTYPE-REF>"

variable_access_s1: "<VARIABLE-ACCESS" " " uuid_attr ">" variable_access_content_s1 "</VARIABLE-ACCESS>"
variable_access_content_s1: short_name_var_s1 accessed_variable_s1
short_name_var_s1: "<SHORT-NAME>DSP_MCU01_EmergShutDown</SHORT-NAME>"
accessed_variable_s1: "<ACCESSED-VARIABLE>" autosar_variable_iref_s1 "</ACCESSED-VARIABLE>"
autosar_variable_iref_s1: "<AUTOSAR-VARIABLE-IREF>" port_prototype_ref_s1 target_data_prototype_ref_s1 "</AUTOSAR-VARIABLE-IREF>"
port_prototype_ref_s1: "<PORT-PROTOTYPE-REF" " " "DEST=\\"P-PORT-PROTOTYPE\\">/COM_SWC/ASW_COM/PPort_MCU01_EmergShutDown</PORT-PROTOTYPE-REF>"
target_data_prototype_ref_s1: "<TARGET-DATA-PROTOTYPE-REF" " " "DEST=\\"VARIABLE-DATA-PROTOTYPE\\">/COM_Interface/SR_Interface_MCU01_EmergShutDown/MCU01_EmergShutDown</TARGET-DATA-PROTOTYPE-REF>"

variable_access_s2: "<VARIABLE-ACCESS" " " uuid_attr ">" variable_access_content_s2 "</VARIABLE-ACCESS>"
variable_access_content_s2: short_name_var_s2 accessed_variable_s2
short_name_var_s2: "<SHORT-NAME>DSP_MCU02_MaxTor</SHORT-NAME>"
accessed_variable_s2: "<ACCESSED-VARIABLE>" autosar_variable_iref_s2 "</ACCESSED-VARIABLE>"
autosar_variable_iref_s2: "<AUTOSAR-VARIABLE-IREF>" port_prototype_ref_s2 target_data_prototype_ref_s2 "</AUTOSAR-VARIABLE-IREF>"
port_prototype_ref_s2: "<PORT-PROTOTYPE-REF" " " "DEST=\\"P-PORT-PROTOTYPE\\">/COM_SWC/ASW_COM/PPort_MCU02_MaxTor</PORT-PROTOTYPE-REF>"
target_data_prototype_ref_s2: "<TARGET-DATA-PROTOTYPE-REF" " " "DEST=\\"VARIABLE-DATA-PROTOTYPE\\">/COM_Interface/SR_Interface_MCU02_MaxTor/MCU02_MaxTor</TARGET-DATA-PROTOTYPE-REF>"

variable_access_s3: "<VARIABLE-ACCESS" " " uuid_attr ">" variable_access_content_s3 "</VARIABLE-ACCESS>"
variable_access_content_s3: short_name_var_s3 accessed_variable_s3
short_name_var_s3: "<SHORT-NAME>DSP_MCU03_NRF_IdcSamp</SHORT-NAME>"
accessed_variable_s3: "<ACCESSED-VARIABLE>" autosar_variable_iref_s3 "</ACCESSED-VARIABLE>"
autosar_variable_iref_s3: "<AUTOSAR-VARIABLE-IREF>" port_prototype_ref_s3 target_data_prototype_ref_s3 "</AUTOSAR-VARIABLE-IREF>"
port_prototype_ref_s3: "<PORT-PROTOTYPE-REF" " " "DEST=\\"P-PORT-PROTOTYPE\\">/COM_SWC/ASW_COM/PPort_MCU03_NRF_IdcSamp</PORT-PROTOTYPE-REF>"
target_data_prototype_ref_s3: "<TARGET-DATA-PROTOTYPE-REF" " " "DEST=\\"VARIABLE-DATA-PROTOTYPE\\">/COM_Interface/SR_Interface_MCU03_NRF_IdcSamp/MCU03_NRF_IdcSamp</TARGET-DATA-PROTOTYPE-REF>"

uuid_attr: "UUID=\\"" uuid_value "\\""
uuid_value: /[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}/'''

    def _get_full_gbnf_template(self) -> str:
        """完整格式的GBNF模板（包含Calibration Port）"""
        # 基于标准模板，添加第四个R-PORT
        standard = self._get_standard_gbnf_template()

        # 修改r_ports规则
        full_template = standard.replace(
            "r_ports: r_port_1 r_port_2 r_port_3",
            "r_ports: r_port_1 r_port_2 r_port_3 r_port_4"
        )

        # 添加第四个R-PORT定义
        cal_port_def = '''
r_port_4: "<R-PORT-PROTOTYPE" " " uuid_attr ">" r_port_content_4 "</R-PORT-PROTOTYPE>"
r_port_content_4: short_name_r4 required_com_specs_4 required_interface_tref_4
short_name_r4: "<SHORT-NAME>CalPort_TqLim</SHORT-NAME>"
required_com_specs_4: "<REQUIRED-COM-SPECS>" nonqueued_receiver_com_spec_4 "</REQUIRED-COM-SPECS>"
nonqueued_receiver_com_spec_4: "<NONQUEUED-RECEIVER-COM-SPEC>" com_spec_content_4 "</NONQUEUED-RECEIVER-COM-SPEC>"
com_spec_content_4: data_element_ref_4 alive_timeout handle_timeout_type
data_element_ref_4: "<DATA-ELEMENT-REF" " " "DEST=\\"VARIABLE-DATA-PROTOTYPE\\">/Cal_TqLim_IF/TqLim</DATA-ELEMENT-REF>"
required_interface_tref_4: "<REQUIRED-INTERFACE-TREF" " " "DEST=\\"SENDER-RECEIVER-INTERFACE\\">/Cal_TqLim_IF</REQUIRED-INTERFACE-TREF>"'''

        # 添加第四个变量访问
        cal_var_access = '''
variable_access_r4: "<VARIABLE-ACCESS" " " uuid_attr ">" variable_access_content_r4 "</VARIABLE-ACCESS>"
variable_access_content_r4: short_name_var_r4 accessed_variable_r4
short_name_var_r4: "<SHORT-NAME>DRPA_CalPort_TqLim</SHORT-NAME>"
accessed_variable_r4: "<ACCESSED-VARIABLE>" autosar_variable_iref_r4 "</ACCESSED-VARIABLE>"
autosar_variable_iref_r4: "<AUTOSAR-VARIABLE-IREF>" port_prototype_ref_r4 target_data_prototype_ref_r4 "</AUTOSAR-VARIABLE-IREF>"
port_prototype_ref_r4: "<PORT-PROTOTYPE-REF" " " "DEST=\\"R-PORT-PROTOTYPE\\">/COM_SWC/ASW_COM/CalPort_TqLim</PORT-PROTOTYPE-REF>"
target_data_prototype_ref_r4: "<TARGET-DATA-PROTOTYPE-REF" " " "DEST=\\"VARIABLE-DATA-PROTOTYPE\\">/Cal_TqLim_IF/TqLim</TARGET-DATA-PROTOTYPE-REF>"'''

        # 修改data_receive_points
        full_template = full_template.replace(
            'data_receive_points: "<DATA-RECEIVE-POINT-BY-ARGUMENTS>" variable_access_r1 variable_access_r2 variable_access_r3 "</DATA-RECEIVE-POINT-BY-ARGUMENTS>"',
            'data_receive_points: "<DATA-RECEIVE-POINT-BY-ARGUMENTS>" variable_access_r1 variable_access_r2 variable_access_r3 variable_access_r4 "</DATA-RECEIVE-POINT-BY-ARGUMENTS>"'
        )

        # 在末尾添加定义
        full_template += cal_port_def + cal_var_access

        return full_template

    def _get_full_with_special_template(self) -> str:
        """🆕 特殊full格式（包含SLEEP模式等）"""
        # 类似于full_format，但添加特殊的R-PORT
        standard = self._get_standard_gbnf_template()

        # 修改r_ports规则
        special_template = standard.replace(
            "r_ports: r_port_1 r_port_2 r_port_3",
            "r_ports: r_port_1 r_port_2 r_port_3 r_port_special"
        )

        # 添加特殊R-PORT定义
        special_port_def = '''
r_port_special: "<R-PORT-PROTOTYPE" " " uuid_attr ">" r_port_content_special "</R-PORT-PROTOTYPE>"
r_port_content_special: short_name_special required_com_specs_special required_interface_tref_special
short_name_special: "<SHORT-NAME>RPort_SLEEP_Mode</SHORT-NAME>"
required_com_specs_special: "<REQUIRED-COM-SPECS>" nonqueued_receiver_com_spec_special "</REQUIRED-COM-SPECS>"
nonqueued_receiver_com_spec_special: "<NONQUEUED-RECEIVER-COM-SPEC>" com_spec_content_special "</NONQUEUED-RECEIVER-COM-SPEC>"
com_spec_content_special: data_element_ref_special alive_timeout handle_timeout_type
data_element_ref_special: "<DATA-ELEMENT-REF" " " "DEST=\\"VARIABLE-DATA-PROTOTYPE\\">/COM_Interface/SR_Interface_SLEEP/SLEEP</DATA-ELEMENT-REF>"
required_interface_tref_special: "<REQUIRED-INTERFACE-TREF" " " "DEST=\\"SENDER-RECEIVER-INTERFACE\\">/COM_Interface/SR_Interface_SLEEP</REQUIRED-INTERFACE-TREF>"'''

        # 添加特殊变量访问
        special_var_access = '''
variable_access_special: "<VARIABLE-ACCESS" " " uuid_attr ">" variable_access_content_special "</VARIABLE-ACCESS>"
variable_access_content_special: short_name_var_special accessed_variable_special
short_name_var_special: "<SHORT-NAME>DRPA_SLEEP_Mode</SHORT-NAME>"
accessed_variable_special: "<ACCESSED-VARIABLE>" autosar_variable_iref_special "</ACCESSED-VARIABLE>"
autosar_variable_iref_special: "<AUTOSAR-VARIABLE-IREF>" port_prototype_ref_special target_data_prototype_ref_special "</AUTOSAR-VARIABLE-IREF>"
port_prototype_ref_special: "<PORT-PROTOTYPE-REF" " " "DEST=\\"R-PORT-PROTOTYPE\\">/COM_SWC/ASW_COM/RPort_SLEEP_Mode</PORT-PROTOTYPE-REF>"
target_data_prototype_ref_special: "<TARGET-DATA-PROTOTYPE-REF" " " "DEST=\\"VARIABLE-DATA-PROTOTYPE\\">/COM_Interface/SR_Interface_SLEEP/SLEEP</TARGET-DATA-PROTOTYPE-REF>"'''

        # 修改data_receive_points
        special_template = special_template.replace(
            'data_receive_points: "<DATA-RECEIVE-POINT-BY-ARGUMENTS>" variable_access_r1 variable_access_r2 variable_access_r3 "</DATA-RECEIVE-POINT-BY-ARGUMENTS>"',
            'data_receive_points: "<DATA-RECEIVE-POINT-BY-ARGUMENTS>" variable_access_r1 variable_access_r2 variable_access_r3 variable_access_special "</DATA-RECEIVE-POINT-BY-ARGUMENTS>"'
        )

        # 在末尾添加定义
        special_template += special_port_def + special_var_access

        return special_template

    def _validate_and_normalize_requirements(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """验证和规范化需求"""
        normalized = {
            "component_name": requirements.get("component_name", "ASW_COM"),
            "p_ports": requirements.get("p_ports", []),
            "r_ports": requirements.get("r_ports", []),
            "timing_events": requirements.get("timing_events", []),
            "runnables": requirements.get("runnables", [])
        }

        print(
            f"✅ Using static template for: {len(normalized['p_ports'])} P-ports, {len(normalized['r_ports'])} R-ports")
        return normalized

    def generate_gbnf_from_requirements(self, requirements: Dict[str, Any]) -> str:
        """🎯 根据需求选择合适的静态GBNF模板 - 支持完整7种FULL格式"""
        p_port_count = len(requirements["p_ports"])
        r_port_count = len(requirements["r_ports"])
        component_name = requirements.get("component_name", "ASW_COM")

        print(
            f"🔧 Selecting GBNF template for: {p_port_count} P-ports, {r_port_count} R-ports, component: {component_name}")

        # 模板选择逻辑
        if p_port_count == 1 and r_port_count == 0:
            template_key = "min_format"
        elif component_name == "ASW_COM_STD" and p_port_count == 2 and r_port_count == 1:
            template_key = "mid_format"
        elif r_port_count == 4:
            # 检查特殊格式
            has_calibration = any("CalPort" in port.get("name", "") for port in requirements["r_ports"])
            has_sleep = any("SLEEP" in port.get("signal", "") for port in requirements["r_ports"])

            if has_calibration:
                template_key = "full_format"  # Calibration Port版本
            elif has_sleep:
                template_key = "full_with_special"  # SLEEP模式版本
            else:
                template_key = "full_format"  # 通用4R版本
        elif r_port_count == 3 and component_name == "ASW_COM":
            # 🎯 所有3R的FULL格式变体都使用standard_format模板
            # full_standard, full_with_explicit_alivetime, full_with_handle_timeout, full_basic_variant
            template_key = "standard_format"
        else:
            template_key = "standard_format"

        selected_template = self.safe_gbnf_templates[template_key]

        # 统计模板使用情况
        self.batch_stats["template_usage"][template_key] = self.batch_stats["template_usage"].get(template_key, 0) + 1

        print(f"✅ Selected template: {template_key} ({len(selected_template)} chars)")
        return selected_template

    def _get_generation_params(self, index: int, total: int) -> Dict[str, Any]:
        """🔥 修改：生成参数配置，不进行微调"""
        seed = self.SEEDS[index % len(self.SEEDS)]

        # 🔥 修改：直接使用原始参数，不添加随机变化
        params = {
            "seed": seed,
            "temperature": self.TEMPERATURE,  # 保持原始参数
            "top_p": self.TOP_P,  # 保持原始参数
            "index": index,
            "total": total
        }

        return params

    def _get_template_type(self, requirements: Dict[str, Any]) -> str:
        """获取模板类型（用于统计）"""
        p_count = len(requirements["p_ports"])
        r_count = len(requirements["r_ports"])
        component_name = requirements.get("component_name", "ASW_COM")

        if p_count == 1 and r_count == 0:
            return "min_format"
        elif component_name == "ASW_COM_STD" and p_count == 2 and r_count == 1:
            return "mid_format"
        elif r_count == 4:
            return "full_format"
        else:
            return "standard_format"

    async def _generate_single_xml(self, vllm_endpoint: str, request: Any, gbnf: str, params: Dict[str, Any] = None) -> \
    Tuple[str, Dict[str, Any]]:
        """🔥 修改：生成单个XML - 增加GPU资源监控"""
        if params is None:
            params = {
                "temperature": self.TEMPERATURE,
                "top_p": self.TOP_P,
                "seed": self.SEEDS[0]
            }

        # 🔥 开始监控 - 包含GPU
        start_time = time.time()
        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB

        # 🔥 新增：GPU监控
        gpu_memory_before = 0
        gpu_peak_memory = 0
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu_memory_before = gpus[0].memoryUsed  # MB
                gpu_peak_memory = gpu_memory_before
        except ImportError:
            print("⚠️ GPUtil not available, skipping GPU monitoring")
        except Exception as e:
            print(f"⚠️ GPU monitoring error: {e}")

        vllm_request = {
            "model": "/model/HuggingFace/deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
            "prompt": request.prompt,  # 🔥 修改：使用原始prompt而不是固定文本
            "max_tokens": request.max_tokens,
            "temperature": params["temperature"],
            "top_p": params["top_p"],
            "frequency_penalty": request.frequency_penalty,
            "presence_penalty": request.presence_penalty,
            "stream": False,
            "guided_grammar": gbnf,
            "stop": ["</APPLICATION-SW-COMPONENT-TYPE>"],
            "seed": params.get("seed")
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                    f"{vllm_endpoint}/v1/completions",
                    json=vllm_request,
                    timeout=aiohttp.ClientTimeout(total=300)
            ) as resp:
                if resp.status == 200:
                    response = await resp.json()

                    # 🔥 结束监控
                    end_time = time.time()
                    memory_after = process.memory_info().rss / 1024 / 1024  # MB
                    generation_time = end_time - start_time

                    # 🔥 新增：GPU监控结束
                    gpu_memory_after = 0
                    try:
                        if 'GPUtil' in globals():
                            gpus = GPUtil.getGPUs()
                            if gpus:
                                gpu_memory_after = gpus[0].memoryUsed
                                gpu_peak_memory = max(gpu_peak_memory, gpu_memory_after)
                    except:
                        pass

                    # 🔥 提取token信息
                    usage_info = response.get("usage", {})
                    prompt_tokens = usage_info.get("prompt_tokens", 0)
                    completion_tokens = usage_info.get("completion_tokens", 0)
                    total_tokens = usage_info.get("total_tokens", 0)

                    xml_output = response["choices"][0]["text"]

                    # 🔥 资源统计 - 包含GPU
                    resource_stats = {
                        "generation_time_seconds": round(generation_time, 3),
                        "memory_usage_mb": {
                            "before": round(memory_before, 2),
                            "after": round(memory_after, 2),
                            "delta": round(memory_after - memory_before, 2)
                        },
                        # 🔥 新增：GPU资源统计
                        "gpu_usage_mb": {
                            "before": round(gpu_memory_before, 2),
                            "after": round(gpu_memory_after, 2),
                            "peak": round(gpu_peak_memory, 2),
                            "delta": round(gpu_memory_after - gpu_memory_before, 2)
                        },
                        "token_usage": {
                            "prompt_tokens": prompt_tokens,
                            "completion_tokens": completion_tokens,
                            "total_tokens": total_tokens
                        },
                        "generation_params": params
                    }

                    return xml_output, resource_stats
                else:
                    error_text = await resp.text()
                    raise Exception(f"vLLM error: {error_text}")


    async def generate_batch(self, vllm_endpoint: str, request: Any) -> Tuple[List[str], Dict[str, Any]]:
        """🎯 批量生成方法 - 增加详细资源统计"""
        print("🎯 Using Enhanced Safe Dynamic GBNF Strategy (Batch Mode)")

        # 🎯 批量开始时间
        batch_start_time = time.time()
        process = psutil.Process()
        batch_memory_before = process.memory_info().rss / 1024 / 1024  # MB

        # 更新批量统计
        self.batch_stats['total_batches'] += 1

        # 解析批量prompts
        batch_results = self.prompt_mapper.parse_batch_prompts(request.prompt)
        self.batch_stats['total_prompts'] += len(batch_results)

        xml_outputs = []
        detailed_stats = []  # 🎯 详细统计列表
        batch_stats = {
            "total_prompts": len(batch_results),
            "successful": 0,
            "failed": 0,
            "templates_used": {},
            "detailed_prompt_stats": []  # 🎯 每个prompt的详细统计
        }

        for i, requirements in enumerate(batch_results):
            print(f"📝 Processing prompt {i + 1}/{len(batch_results)}")

            prompt_start_time = time.time()

            try:
                # 规范化需求
                requirements = self._validate_and_normalize_requirements(requirements)

                # 选择GBNF模板
                safe_gbnf = self.generate_gbnf_from_requirements(requirements)
                template_type = self._get_template_type(requirements)

                # 统计模板使用
                batch_stats["templates_used"][template_type] = batch_stats["templates_used"].get(template_type, 0) + 1

                # 🎯 为每个prompt使用不同的生成参数
                gen_params = self._get_generation_params(i, len(batch_results))

                # 🎯 生成XML并获取资源统计
                xml_output, resource_stats = await self._generate_single_xml(vllm_endpoint, request, safe_gbnf,
                                                                             gen_params)
                xml_outputs.append(xml_output)

                prompt_end_time = time.time()

                # 🎯 详细的prompt统计
                prompt_stats = {
                    "prompt_index": i + 1,
                    "component_name": requirements.get("component_name", "Unknown"),
                    "p_ports_count": len(requirements.get("p_ports", [])),
                    "r_ports_count": len(requirements.get("r_ports", [])),
                    "template_used": template_type,
                    "total_prompt_time": round(prompt_end_time - prompt_start_time, 3),
                    "xml_length": len(xml_output),
                    **resource_stats  # 包含generation_time, memory_usage, token_usage等
                }

                batch_stats["detailed_prompt_stats"].append(prompt_stats)
                detailed_stats.append(prompt_stats)

                batch_stats["successful"] += 1
                self.batch_stats['successful_generations'] += 1

                print(f"✅ Prompt {i + 1} successful: {len(xml_output)} chars, "
                      f"time: {resource_stats['generation_time_seconds']}s, "
                      f"tokens: {resource_stats['token_usage']['total_tokens']}, "
                      f"memory: {resource_stats['memory_usage_mb']['delta']}MB")

            except Exception as e:
                print(f"❌ Prompt {i + 1} failed: {e}")
                xml_outputs.append(f"<!-- ERROR: {e} -->")

                prompt_end_time = time.time()

                # 🎯 失败的prompt也记录统计
                error_stats = {
                    "prompt_index": i + 1,
                    "component_name": "ERROR",
                    "p_ports_count": 0,
                    "r_ports_count": 0,
                    "template_used": "none",
                    "total_prompt_time": round(prompt_end_time - prompt_start_time, 3),
                    "xml_length": 0,
                    "generation_time_seconds": 0,
                    "memory_usage_mb": {"before": 0, "after": 0, "delta": 0},
                    "token_usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                    "error": str(e)
                }

                batch_stats["detailed_prompt_stats"].append(error_stats)
                detailed_stats.append(error_stats)

                batch_stats["failed"] += 1
                self.batch_stats['failed_generations'] += 1

        # 🎯 批量结束统计
        batch_end_time = time.time()
        batch_memory_after = process.memory_info().rss / 1024 / 1024  # MB
        total_batch_time = batch_end_time - batch_start_time

        # 🎯 聚合统计
        total_tokens = sum(stat.get("token_usage", {}).get("total_tokens", 0) for stat in detailed_stats)
        total_memory_delta = sum(stat.get("memory_usage_mb", {}).get("delta", 0) for stat in detailed_stats)
        avg_time_per_prompt = total_batch_time / len(batch_results) if batch_results else 0

        constraints_applied = {
            "gbnf": True,
            "fsm": False,
            "strategy": "enhanced_safe_dynamic_gbnf_batch",
            "batch_stats": batch_stats,
            "batch_mode": True,
            "global_batch_stats": self.batch_stats,
            # 🎯 新增批量资源统计
            "batch_resource_summary": {
                "total_batch_time_seconds": round(total_batch_time, 3),
                "avg_time_per_prompt": round(avg_time_per_prompt, 3),
                "total_tokens_used": total_tokens,
                "avg_tokens_per_prompt": round(total_tokens / len(batch_results), 1) if batch_results else 0,
                "total_memory_delta_mb": round(total_memory_delta, 2),
                "batch_memory_usage": {
                    "before": round(batch_memory_before, 2),
                    "after": round(batch_memory_after, 2),
                    "delta": round(batch_memory_after - batch_memory_before, 2)
                },
                "prompts_processed": len(batch_results),
                "success_rate": round((batch_stats["successful"] / len(batch_results)) * 100, 1) if batch_results else 0
            }
        }

        return xml_outputs, constraints_applied

    async def generate(self, vllm_endpoint: str, request: Any) -> Tuple[str, Dict[str, Any]]:
        """主生成方法 - 修改：返回每个种子的独立结果"""
        print("🎯 Using Enhanced Safe Dynamic GBNF Strategy")

        # 🔥 修改：更精确的批量检测，避免误判 min_promote
        is_batch = False

        # 检查是否真的是 YAML 列表格式
        if ("- |" in request.prompt and request.prompt.count("- |") >= 2) or \
                (request.prompt.strip().startswith("- ") and request.prompt.count('\n-') >= 1):
            is_batch = True

        # 额外检查：如果包含 min_promote、mid_promote、full_promote 等关键词，视为批量
        if any(keyword in request.prompt for keyword in ["min_promote:", "mid_promote:", "full_promote:"]):
            is_batch = True

        if is_batch:
            # 批量模式保持不变
            print("🔄 Detected batch mode, using batch processor")
            xml_outputs, constraints_applied = await self.generate_batch(vllm_endpoint, request)
            combined_xml = "\n\n<!-- === BATCH SEPARATOR === -->\n\n".join(xml_outputs)
            return combined_xml, constraints_applied
        else:
            # 单个prompt模式 - 确保生成多种子结果
            print(f"📋 Single prompt mode - generating {len(self.SEEDS)} versions with different seeds")

            single_start_time = time.time()

            # 步骤1-3：需求解析和GBNF生成
            try:
                requirements = self.prompt_mapper._extract_all_info(request.prompt)
                print(
                    f"🔍 Parsed: {len(requirements.get('p_ports', []))} P-ports, {len(requirements.get('r_ports', []))} R-ports")
            except Exception as e:
                print(f"❌ Parsing failed: {e}, using fallback")
                requirements = self.prompt_mapper.prompt_mappings["full_standard"]

            requirements = self._validate_and_normalize_requirements(requirements)

            try:
                safe_gbnf = self.generate_gbnf_from_requirements(requirements)
                print(f"✅ Selected GBNF template: {len(safe_gbnf)} characters")
            except Exception as e:
                print(f"❌ Template selection failed: {e}")
                safe_gbnf = self.safe_gbnf_templates["standard_format"]

            # 🔥 修改：收集每个种子的独立结果，确保都生成
            seed_results = []

            for i, seed in enumerate(self.SEEDS):
                print(f"🎲 Generating version {i + 1}/{len(self.SEEDS)} with seed {seed}")

                # 🔥 修改：使用固定参数，不微调
                params = {
                    "seed": seed,
                    "temperature": self.TEMPERATURE,  # 直接使用原始参数
                    "top_p": self.TOP_P,  # 直接使用原始参数
                    "index": i,
                    "total": len(self.SEEDS)
                }

                try:
                    xml_output, resource_stats = await self._generate_single_xml(vllm_endpoint, request, safe_gbnf,
                                                                                 params)

                    seed_result = {
                        "seed": seed,
                        "xml": xml_output,
                        "resource_stats": resource_stats,
                        "success": True
                    }
                    seed_results.append(seed_result)

                    print(f"✅ Version {i + 1} successful: {len(xml_output)} chars, "
                          f"seed={seed}, time: {resource_stats['generation_time_seconds']}s, "
                          f"tokens: {resource_stats['token_usage']['total_tokens']}")

                except Exception as e:
                    print(f"❌ Version {i + 1} failed with seed {seed}: {e}")

                    seed_result = {
                        "seed": seed,
                        "xml": f"<!-- ERROR with seed {seed}: {e} -->",
                        "resource_stats": {
                            "generation_time_seconds": 0,
                            "memory_usage_mb": {"before": 0, "after": 0, "delta": 0},
                            "gpu_usage_mb": {"before": 0, "after": 0, "peak": 0, "delta": 0},
                            "token_usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
                        },
                        "success": False,
                        "error": str(e)
                    }
                    seed_results.append(seed_result)

            single_end_time = time.time()
            total_single_time = single_end_time - single_start_time

            # 计算汇总统计
            successful_versions = len([r for r in seed_results if r["success"]])

            # 返回第一个成功的XML作为主要输出（保持向后兼容）
            primary_xml = next((r["xml"] for r in seed_results if r["success"]), seed_results[0]["xml"])

            constraints_applied = {
                "gbnf": True,
                "fsm": False,
                "strategy": "enhanced_safe_dynamic_gbnf_multi_seed",
                "requirements_extracted": requirements,
                "gbnf_customized": True,
                "template_used": "static_safe",
                # 🔥 确保包含种子结果
                "seed_results": seed_results,
                "multi_seed_stats": {
                    "total_versions": len(self.SEEDS),
                    "successful_versions": successful_versions,
                    "failed_versions": len(self.SEEDS) - successful_versions,
                    "seeds_used": self.SEEDS,
                    "total_processing_time": round(total_single_time, 3),
                },
                "single_resource_stats": {
                    "total_processing_time": round(total_single_time, 3),
                    "component_name": requirements.get("component_name", "Unknown"),
                    "p_ports_count": len(requirements.get("p_ports", [])),
                    "r_ports_count": len(requirements.get("r_ports", [])),
                    "generation_mode": "multi_seed",
                    "versions_generated": len(seed_results)
                }
            }

            return primary_xml, constraints_applied

    def get_batch_statistics(self) -> Dict[str, Any]:
        """获取批量处理统计信息"""
        return {
            "batch_stats": self.batch_stats,
            "success_rate": (
                                    self.batch_stats['successful_generations'] /
                                    max(1, self.batch_stats['total_prompts'])
                            ) * 100,
            "template_distribution": self.batch_stats['template_usage']
        }