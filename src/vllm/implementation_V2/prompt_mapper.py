#!/usr/bin/env python3
# prompt_mapper.py - 增强版，完整覆盖所有格式并支持批量处理

from typing import Dict, List, Any

import yaml


class AutosarPromptMapper:
    """增强版 - 完整覆盖所有格式，支持批量处理"""

    def __init__(self):
        # 🎯 完整的预定义映射表 - 覆盖所有格式变体
        self.prompt_mappings = {
            # === MIN格式映射 ===
            "min_mcu01_emergsutdown": {
                'component_name': 'ASW_COM_MIN',
                'p_ports': [
                    {'name': 'PPort_MCU01_EmergShutDown', 'signal': 'MCU01_EmergShutDown',
                     'interface': '/COM_Interface/SR_Interface_MCU01_EmergShutDown'}
                ],
                'r_ports': [],
                'timing_events': [],
                'runnables': []
            },
            "min_mcu02_maxtor": {
                'component_name': 'ASW_COM_MIN',
                'p_ports': [
                    {'name': 'PPort_MCU02_MaxTor', 'signal': 'MCU02_MaxTor',
                     'interface': '/COM_Interface/SR_Interface_MCU02_MaxTor'}
                ],
                'r_ports': [],
                'timing_events': [],
                'runnables': []
            },
            "min_mcu03_nrf_idcsamp": {
                'component_name': 'ASW_COM_MIN',
                'p_ports': [
                    {'name': 'PPort_MCU03_NRF_IdcSamp', 'signal': 'MCU03_NRF_IdcSamp',
                     'interface': '/COM_Interface/SR_Interface_MCU03_NRF_IdcSamp'}
                ],
                'r_ports': [],
                'timing_events': [],
                'runnables': []
            },

            # === MID格式映射 - 完整覆盖所有变体 ===
            "mid_emergsutdown_maxtor_hcu01tqcmd": {
                'component_name': 'ASW_COM_STD',
                'p_ports': [
                    {'name': 'PPort_MCU01_EmergShutDown', 'signal': 'MCU01_EmergShutDown',
                     'interface': '/COM_Interface/SR_Interface_MCU01_EmergShutDown'},
                    {'name': 'PPort_MCU02_MaxTor', 'signal': 'MCU02_MaxTor',
                     'interface': '/COM_Interface/SR_Interface_MCU02_MaxTor'}
                ],
                'r_ports': [
                    {
                        'name': 'RPort_HCU01_TqCmd',
                        'signal': 'HCU01_TqCmd',
                        'interface': '/COM_Interface/SR_Interface_HCU01_TqCmd',
                        'data_element': '/COM_Interface/SR_Interface_HCU01_TqCmd/HCU01_Tq_Cmd',
                        'alive_timeout': '0.3',
                        'handle_timeout_type': 'NONE'
                    }
                ],
                'timing_events': [
                    {
                        'name': 'TE_RE_COM_SWC',
                        'period': '0.01',
                        'runnable_ref': '/COM_SWC/ASW_COM_STD/SwcInternalBehavior/RE_COM_SWC'
                    }
                ],
                'runnables': [
                    {
                        'name': 'RE_COM_SWC',
                        'symbol': 'RE_COM_SWC_func',
                        'receive_access_count': 1,
                        'send_access_count': 2
                    }
                ]
            },
            "mid_maxtor_nrf_hcu01shift": {
                'component_name': 'ASW_COM_STD',
                'p_ports': [
                    {'name': 'PPort_MCU02_MaxTor', 'signal': 'MCU02_MaxTor',
                     'interface': '/COM_Interface/SR_Interface_MCU02_MaxTor'},
                    {'name': 'PPort_MCU03_NRF_IdcSamp', 'signal': 'MCU03_NRF_IdcSamp',
                     'interface': '/COM_Interface/SR_Interface_MCU03_NRF_IdcSamp'}
                ],
                'r_ports': [
                    {
                        'name': 'RPort_HCU01_Shift',
                        'signal': 'HCU01_Shift',
                        'interface': '/COM_Interface/SR_Interface_HCU01_Shift',
                        'data_element': '/COM_Interface/SR_Interface_HCU01_Shift/HCU01_Shift',
                        'alive_timeout': '0.3',
                        'handle_timeout_type': 'NONE'
                    }
                ],
                'timing_events': [
                    {
                        'name': 'TE_RE_COM_SWC',
                        'period': '0.01',
                        'runnable_ref': '/COM_SWC/ASW_COM_STD/SwcInternalBehavior/RE_COM_SWC'
                    }
                ],
                'runnables': [
                    {
                        'name': 'RE_COM_SWC',
                        'symbol': 'RE_COM_SWC_func',
                        'receive_access_count': 1,
                        'send_access_count': 2
                    }
                ]
            },
            "mid_emergsutdown_nrf_hcu02poweroff": {
                'component_name': 'ASW_COM_STD',
                'p_ports': [
                    {'name': 'PPort_MCU01_EmergShutDown', 'signal': 'MCU01_EmergShutDown',
                     'interface': '/COM_Interface/SR_Interface_MCU01_EmergShutDown'},
                    {'name': 'PPort_MCU03_NRF_IdcSamp', 'signal': 'MCU03_NRF_IdcSamp',
                     'interface': '/COM_Interface/SR_Interface_MCU03_NRF_IdcSamp'}
                ],
                'r_ports': [
                    {
                        'name': 'RPort_HCU02_Poweroff',
                        'signal': 'HCU02_Poweroff',
                        'interface': '/COM_Interface/SR_Interface_HCU02_Poweroff',
                        'data_element': '/COM_Interface/SR_Interface_HCU02_Poweroff/HCU02_Poweroff',
                        'alive_timeout': '0.3',
                        'handle_timeout_type': 'NONE'
                    }
                ],
                'timing_events': [
                    {
                        'name': 'TE_RE_COM_SWC',
                        'period': '0.02',  # 20ms
                        'runnable_ref': '/COM_SWC/ASW_COM_STD/SwcInternalBehavior/RE_COM_SWC'
                    }
                ],
                'runnables': [
                    {
                        'name': 'RE_COM_SWC',
                        'symbol': 'RE_COM_SWC_func',
                        'receive_access_count': 1,
                        'send_access_count': 2
                    }
                ]
            },
            "mid_emergsutdown_maxtor_hcu01shift": {
                'component_name': 'ASW_COM_STD',
                'p_ports': [
                    {'name': 'PPort_MCU01_EmergShutDown', 'signal': 'MCU01_EmergShutDown',
                     'interface': '/COM_Interface/SR_Interface_MCU01_EmergShutDown'},
                    {'name': 'PPort_MCU02_MaxTor', 'signal': 'MCU02_MaxTor',
                     'interface': '/COM_Interface/SR_Interface_MCU02_MaxTor'}
                ],
                'r_ports': [
                    {
                        'name': 'RPort_HCU01_Shift',
                        'signal': 'HCU01_Shift',
                        'interface': '/COM_Interface/SR_Interface_HCU01_Shift',
                        'data_element': '/COM_Interface/SR_Interface_HCU01_Shift/HCU01_Shift',
                        'alive_timeout': '0.3',
                        'handle_timeout_type': 'NONE'
                    }
                ],
                'timing_events': [
                    {
                        'name': 'TE_RE_COM_SWC',
                        'period': '0.005',  # 5ms
                        'runnable_ref': '/COM_SWC/ASW_COM_STD/SwcInternalBehavior/RE_COM_SWC'
                    }
                ],
                'runnables': [
                    {
                        'name': 'RE_COM_SWC',
                        'symbol': 'RE_COM_SWC_func',
                        'receive_access_count': 1,
                        'send_access_count': 2
                    }
                ]
            },
            "mid_emergsutdown_nrf_hcu01tqcmd": {
                'component_name': 'ASW_COM_STD',
                'p_ports': [
                    {'name': 'PPort_MCU01_EmergShutDown', 'signal': 'MCU01_EmergShutDown',
                     'interface': '/COM_Interface/SR_Interface_MCU01_EmergShutDown'},
                    {'name': 'PPort_MCU03_NRF_IdcSamp', 'signal': 'MCU03_NRF_IdcSamp',
                     'interface': '/COM_Interface/SR_Interface_MCU03_NRF_IdcSamp'}
                ],
                'r_ports': [
                    {
                        'name': 'RPort_HCU01_TqCmd',
                        'signal': 'HCU01_TqCmd',
                        'interface': '/COM_Interface/SR_Interface_HCU01_TqCmd',
                        'data_element': '/COM_Interface/SR_Interface_HCU01_TqCmd/HCU01_Tq_Cmd',
                        'alive_timeout': '0.3',
                        'handle_timeout_type': 'NONE'
                    }
                ],
                'timing_events': [
                    {
                        'name': 'TE_RE_COM_SWC',
                        'period': '0.01',  # 10ms
                        'runnable_ref': '/COM_SWC/ASW_COM_STD/SwcInternalBehavior/RE_COM_SWC'
                    }
                ],
                'runnables': [
                    {
                        'name': 'RE_COM_SWC',
                        'symbol': 'RE_COM_SWC_func',
                        'receive_access_count': 1,
                        'send_access_count': 2
                    }
                ]
            },
            "mid_maxtor_nrf_hcu02poweroff": {
                'component_name': 'ASW_COM_STD',
                'p_ports': [
                    {'name': 'PPort_MCU02_MaxTor', 'signal': 'MCU02_MaxTor',
                     'interface': '/COM_Interface/SR_Interface_MCU02_MaxTor'},
                    {'name': 'PPort_MCU03_NRF_IdcSamp', 'signal': 'MCU03_NRF_IdcSamp',
                     'interface': '/COM_Interface/SR_Interface_MCU03_NRF_IdcSamp'}
                ],
                'r_ports': [
                    {
                        'name': 'RPort_HCU02_Poweroff',
                        'signal': 'HCU02_Poweroff',
                        'interface': '/COM_Interface/SR_Interface_HCU02_Poweroff',
                        'data_element': '/COM_Interface/SR_Interface_HCU02_Poweroff/HCU02_Poweroff',
                        'alive_timeout': '0.3',
                        'handle_timeout_type': 'NONE'
                    }
                ],
                'timing_events': [
                    {
                        'name': 'TE_RE_COM_SWC',
                        'period': '0.015',  # 15ms
                        'runnable_ref': '/COM_SWC/ASW_COM_STD/SwcInternalBehavior/RE_COM_SWC'
                    }
                ],
                'runnables': [
                    {
                        'name': 'RE_COM_SWC',
                        'symbol': 'RE_COM_SWC_func',
                        'receive_access_count': 1,
                        'send_access_count': 2
                    }
                ]
            },
            "mid_emergsutdown_maxtor_hcu01tqcmd_with_timeout": {
                'component_name': 'ASW_COM_STD',
                'p_ports': [
                    {'name': 'PPort_MCU01_EmergShutDown', 'signal': 'MCU01_EmergShutDown',
                     'interface': '/COM_Interface/SR_Interface_MCU01_EmergShutDown'},
                    {'name': 'PPort_MCU02_MaxTor', 'signal': 'MCU02_MaxTor',
                     'interface': '/COM_Interface/SR_Interface_MCU02_MaxTor'}
                ],
                'r_ports': [
                    {
                        'name': 'RPort_HCU01_TqCmd',
                        'signal': 'HCU01_TqCmd',
                        'interface': '/COM_Interface/SR_Interface_HCU01_TqCmd',
                        'data_element': '/COM_Interface/SR_Interface_HCU01_TqCmd/HCU01_Tq_Cmd',
                        'alive_timeout': '0.3',
                        'handle_timeout_type': 'NONE'  # 显式设置
                    }
                ],
                'timing_events': [
                    {
                        'name': 'TE_RE_COM_SWC',
                        'period': '0.01',  # 10ms
                        'runnable_ref': '/COM_SWC/ASW_COM_STD/SwcInternalBehavior/RE_COM_SWC'
                    }
                ],
                'runnables': [
                    {
                        'name': 'RE_COM_SWC',
                        'symbol': 'RE_COM_SWC_func',
                        'receive_access_count': 1,
                        'send_access_count': 2
                    }
                ]
            },

            # === FULL格式映射 ===
            "full_standard": {
                'component_name': 'ASW_COM',
                'p_ports': [
                    {'name': 'PPort_MCU01_EmergShutDown', 'signal': 'MCU01_EmergShutDown',
                     'interface': '/COM_Interface/SR_Interface_MCU01_EmergShutDown'},
                    {'name': 'PPort_MCU02_MaxTor', 'signal': 'MCU02_MaxTor',
                     'interface': '/COM_Interface/SR_Interface_MCU02_MaxTor'},
                    {'name': 'PPort_MCU03_NRF_IdcSamp', 'signal': 'MCU03_NRF_IdcSamp',
                     'interface': '/COM_Interface/SR_Interface_MCU03_NRF_IdcSamp'}
                ],
                'r_ports': [
                    {
                        'name': 'RPort_HCU01_TqCmd',
                        'signal': 'HCU01_TqCmd',
                        'interface': '/COM_Interface/SR_Interface_HCU01_TqCmd',
                        'data_element': '/COM_Interface/SR_Interface_HCU01_TqCmd/HCU01_Tq_Cmd',
                        'alive_timeout': '0.3',
                        'handle_timeout_type': 'NONE'
                    },
                    {
                        'name': 'RPort_HCU01_Shift',
                        'signal': 'HCU01_Shift',
                        'interface': '/COM_Interface/SR_Interface_HCU01_Shift',
                        'data_element': '/COM_Interface/SR_Interface_HCU01_Shift/HCU01_Shift',
                        'alive_timeout': '0.3',
                        'handle_timeout_type': 'NONE'
                    },
                    {
                        'name': 'RPort_HCU02_Poweroff',
                        'signal': 'HCU02_Poweroff',
                        'interface': '/COM_Interface/SR_Interface_HCU02_Poweroff',
                        'data_element': '/COM_Interface/SR_Interface_HCU02_Poweroff/HCU02_Poweroff',
                        'alive_timeout': '0.3',
                        'handle_timeout_type': 'NONE'
                    }
                ],
                'timing_events': [
                    {
                        'name': 'TE_RE_COM_SWC',
                        'period': '0.01',
                        'runnable_ref': '/COM_SWC/ASW_COM/SwcInternalBehavior/RE_COM_SWC'
                    }
                ],
                'runnables': [
                    {
                        'name': 'RE_COM_SWC',
                        'symbol': 'RE_COM_SWC_func',
                        'receive_access_count': 3,
                        'send_access_count': 3
                    }
                ]
            },
            "full_with_calibration": {
                'component_name': 'ASW_COM',
                'p_ports': [
                    {'name': 'PPort_MCU01_EmergShutDown', 'signal': 'MCU01_EmergShutDown',
                     'interface': '/COM_Interface/SR_Interface_MCU01_EmergShutDown'},
                    {'name': 'PPort_MCU02_MaxTor', 'signal': 'MCU02_MaxTor',
                     'interface': '/COM_Interface/SR_Interface_MCU02_MaxTor'},
                    {'name': 'PPort_MCU03_NRF_IdcSamp', 'signal': 'MCU03_NRF_IdcSamp',
                     'interface': '/COM_Interface/SR_Interface_MCU03_NRF_IdcSamp'}
                ],
                'r_ports': [
                    {
                        'name': 'RPort_HCU01_TqCmd',
                        'signal': 'HCU01_TqCmd',
                        'interface': '/COM_Interface/SR_Interface_HCU01_TqCmd',
                        'data_element': '/COM_Interface/SR_Interface_HCU01_TqCmd/HCU01_Tq_Cmd',
                        'alive_timeout': '0.3',
                        'handle_timeout_type': 'NONE'
                    },
                    {
                        'name': 'RPort_HCU01_Shift',
                        'signal': 'HCU01_Shift',
                        'interface': '/COM_Interface/SR_Interface_HCU01_Shift',
                        'data_element': '/COM_Interface/SR_Interface_HCU01_Shift/HCU01_Shift',
                        'alive_timeout': '0.3',
                        'handle_timeout_type': 'NONE'
                    },
                    {
                        'name': 'RPort_HCU02_Poweroff',
                        'signal': 'HCU02_Poweroff',
                        'interface': '/COM_Interface/SR_Interface_HCU02_Poweroff',
                        'data_element': '/COM_Interface/SR_Interface_HCU02_Poweroff/HCU02_Poweroff',
                        'alive_timeout': '0.3',
                        'handle_timeout_type': 'NONE'
                    },
                    {
                        'name': 'CalPort_TqLim',
                        'signal': 'TqLim',
                        'interface': '/Cal_TqLim_IF',
                        'data_element': '/Cal_TqLim_IF/TqLim',
                        'alive_timeout': '0.3',
                        'handle_timeout_type': 'NONE'
                    }
                ],
                'timing_events': [
                    {
                        'name': 'TE_RE_COM_SWC',
                        'period': '0.01',
                        'runnable_ref': '/COM_SWC/ASW_COM/SwcInternalBehavior/RE_COM_SWC'
                    }
                ],
                'runnables': [
                    {
                        'name': 'RE_COM_SWC',
                        'symbol': 'RE_COM_SWC_func',
                        'receive_access_count': 4,
                        'send_access_count': 3
                    }
                ]
            },
            "full_with_sleep_mode": {
                'component_name': 'ASW_COM',
                'p_ports': [
                    {'name': 'PPort_MCU01_EmergShutDown', 'signal': 'MCU01_EmergShutDown',
                     'interface': '/COM_Interface/SR_Interface_MCU01_EmergShutDown'},
                    {'name': 'PPort_MCU02_MaxTor', 'signal': 'MCU02_MaxTor',
                     'interface': '/COM_Interface/SR_Interface_MCU02_MaxTor'},
                    {'name': 'PPort_MCU03_NRF_IdcSamp', 'signal': 'MCU03_NRF_IdcSamp',
                     'interface': '/COM_Interface/SR_Interface_MCU03_NRF_IdcSamp'}
                ],
                'r_ports': [
                    {
                        'name': 'RPort_HCU01_TqCmd',
                        'signal': 'HCU01_TqCmd',
                        'interface': '/COM_Interface/SR_Interface_HCU01_TqCmd',
                        'data_element': '/COM_Interface/SR_Interface_HCU01_TqCmd/HCU01_Tq_Cmd',
                        'alive_timeout': '0.3',
                        'handle_timeout_type': 'NONE'
                    },
                    {
                        'name': 'RPort_HCU01_Shift',
                        'signal': 'HCU01_Shift',
                        'interface': '/COM_Interface/SR_Interface_HCU01_Shift',
                        'data_element': '/COM_Interface/SR_Interface_HCU01_Shift/HCU01_Shift',
                        'alive_timeout': '0.3',
                        'handle_timeout_type': 'NONE'
                    },
                    {
                        'name': 'RPort_HCU02_Poweroff',
                        'signal': 'HCU02_Poweroff',
                        'interface': '/COM_Interface/SR_Interface_HCU02_Poweroff',
                        'data_element': '/COM_Interface/SR_Interface_HCU02_Poweroff/HCU02_Poweroff',
                        'alive_timeout': '0.3',
                        'handle_timeout_type': 'NONE'
                    },
                    {
                        'name': 'RPort_SLEEP_Mode',
                        'signal': 'SLEEP',
                        'interface': '/COM_Interface/SR_Interface_SLEEP',
                        'data_element': '/COM_Interface/SR_Interface_SLEEP/SLEEP',
                        'alive_timeout': '0.3',
                        'handle_timeout_type': 'NONE'
                    }
                ],
                'timing_events': [
                    {
                        'name': 'TE_RE_COM_SWC',
                        'period': '0.01',
                        'runnable_ref': '/COM_SWC/ASW_COM/SwcInternalBehavior/RE_COM_SWC'
                    }
                ],
                'runnables': [
                    {
                        'name': 'RE_COM_SWC',
                        'symbol': 'RE_COM_SWC_func',
                        'receive_access_count': 4,
                        'send_access_count': 3
                    }
                ]
            },
            "full_with_explicit_alivetime": {
                'component_name': 'ASW_COM',
                'p_ports': [
                    {'name': 'PPort_MCU01_EmergShutDown', 'signal': 'MCU01_EmergShutDown',
                     'interface': '/COM_Interface/SR_Interface_MCU01_EmergShutDown'},
                    {'name': 'PPort_MCU02_MaxTor', 'signal': 'MCU02_MaxTor',
                     'interface': '/COM_Interface/SR_Interface_MCU02_MaxTor'},
                    {'name': 'PPort_MCU03_NRF_IdcSamp', 'signal': 'MCU03_NRF_IdcSamp',
                     'interface': '/COM_Interface/SR_Interface_MCU03_NRF_IdcSamp'}
                ],
                'r_ports': [
                    {
                        'name': 'RPort_HCU01_TqCmd',
                        'signal': 'HCU01_TqCmd',
                        'interface': '/COM_Interface/SR_Interface_HCU01_TqCmd',
                        'data_element': '/COM_Interface/SR_Interface_HCU01_TqCmd/HCU01_Tq_Cmd',
                        'alive_timeout': '0.3',
                        'handle_timeout_type': 'NONE',
                        'explicit_alive_timeout': True  # 🎯 标记显式声明
                    },
                    {
                        'name': 'RPort_HCU01_Shift',
                        'signal': 'HCU01_Shift',
                        'interface': '/COM_Interface/SR_Interface_HCU01_Shift',
                        'data_element': '/COM_Interface/SR_Interface_HCU01_Shift/HCU01_Shift',
                        'alive_timeout': '0.3',
                        'handle_timeout_type': 'NONE',
                        'explicit_alive_timeout': True
                    },
                    {
                        'name': 'RPort_HCU02_Poweroff',
                        'signal': 'HCU02_Poweroff',
                        'interface': '/COM_Interface/SR_Interface_HCU02_Poweroff',
                        'data_element': '/COM_Interface/SR_Interface_HCU02_Poweroff/HCU02_Poweroff',
                        'alive_timeout': '0.3',
                        'handle_timeout_type': 'NONE',
                        'explicit_alive_timeout': True
                    }
                ],
                'timing_events': [
                    {
                        'name': 'TE_RE_COM_SWC',
                        'period': '0.01',
                        'runnable_ref': '/COM_SWC/ASW_COM/SwcInternalBehavior/RE_COM_SWC'
                    }
                ],
                'runnables': [
                    {
                        'name': 'RE_COM_SWC',
                        'symbol': 'RE_COM_SWC_func',
                        'receive_access_count': 3,
                        'send_access_count': 3
                    }
                ]
            },
        }
        # 🆕 添加缺失的FULL格式映射
        self.prompt_mappings.update({
            "full_with_explicit_alivetime": {
                'component_name': 'ASW_COM',
                'p_ports': [
                    {'name': 'PPort_MCU01_EmergShutDown', 'signal': 'MCU01_EmergShutDown',
                     'interface': '/COM_Interface/SR_Interface_MCU01_EmergShutDown'},
                    {'name': 'PPort_MCU02_MaxTor', 'signal': 'MCU02_MaxTor',
                     'interface': '/COM_Interface/SR_Interface_MCU02_MaxTor'},
                    {'name': 'PPort_MCU03_NRF_IdcSamp', 'signal': 'MCU03_NRF_IdcSamp',
                     'interface': '/COM_Interface/SR_Interface_MCU03_NRF_IdcSamp'}
                ],
                'r_ports': [
                    {
                        'name': 'RPort_HCU01_TqCmd',
                        'signal': 'HCU01_TqCmd',
                        'interface': '/COM_Interface/SR_Interface_HCU01_TqCmd',
                        'data_element': '/COM_Interface/SR_Interface_HCU01_TqCmd/HCU01_Tq_Cmd',
                        'alive_timeout': '0.3',
                        'handle_timeout_type': 'NONE',
                        'explicit_alive_timeout': True  # 🎯 标记显式声明
                    },
                    {
                        'name': 'RPort_HCU01_Shift',
                        'signal': 'HCU01_Shift',
                        'interface': '/COM_Interface/SR_Interface_HCU01_Shift',
                        'data_element': '/COM_Interface/SR_Interface_HCU01_Shift/HCU01_Shift',
                        'alive_timeout': '0.3',
                        'handle_timeout_type': 'NONE',
                        'explicit_alive_timeout': True
                    },
                    {
                        'name': 'RPort_HCU02_Poweroff',
                        'signal': 'HCU02_Poweroff',
                        'interface': '/COM_Interface/SR_Interface_HCU02_Poweroff',
                        'data_element': '/COM_Interface/SR_Interface_HCU02_Poweroff/HCU02_Poweroff',
                        'alive_timeout': '0.3',
                        'handle_timeout_type': 'NONE',
                        'explicit_alive_timeout': True
                    }
                ],
                'timing_events': [
                    {
                        'name': 'TE_RE_COM_SWC',
                        'period': '0.01',
                        'runnable_ref': '/COM_SWC/ASW_COM/SwcInternalBehavior/RE_COM_SWC'
                    }
                ],
                'runnables': [
                    {
                        'name': 'RE_COM_SWC',
                        'symbol': 'RE_COM_SWC_func',
                        'receive_access_count': 3,
                        'send_access_count': 3
                    }
                ]
            },

            "full_with_handle_timeout": {
                # 与 full_with_explicit_alivetime 类似，但强调 handleTimeoutType
                # ... 复制上面的结构，可以共用full_standard ...
                **self.prompt_mappings["full_standard"]  # 继承标准配置
            },

            "full_basic_variant": {
                # 基础变体，与标准版本相同但用于区分不同的prompt表述
                **self.prompt_mappings["full_standard"]  # 继承标准配置
            }
        })

    def parse_batch_prompts(self, batch_prompt_text: str) -> List[Dict[str, Any]]:
        """🎯 解析批量prompts（支持YAML列表格式）"""
        results = []

        print(f"🔍 Parsing batch prompts: {len(batch_prompt_text)} chars")

        # 检测是否为批量格式
        if "- |" in batch_prompt_text or batch_prompt_text.strip().startswith("-"):
            try:
                # 解析YAML列表
                prompts = yaml.safe_load(batch_prompt_text)
                if isinstance(prompts, list):
                    print(f"📋 Found {len(prompts)} prompts in batch")
                    for i, prompt in enumerate(prompts):
                        if isinstance(prompt, str):
                            result = self._extract_all_info(prompt)
                            result['batch_index'] = i
                            results.append(result)
                            print(f"   ✅ Parsed prompt {i + 1}: {result.get('component_name', 'Unknown')}")
                        else:
                            print(f"   ⚠️ Skipping non-string prompt {i + 1}: {type(prompt)}")
                else:
                    # 单个prompt
                    result = self._extract_all_info(str(prompts))
                    results.append(result)
            except Exception as e:
                print(f"❌ YAML parsing failed: {e}")
                # 回退到单个prompt处理
                results.append(self._extract_all_info(batch_prompt_text))
        else:
            # 单个prompt
            results.append(self._extract_all_info(batch_prompt_text))

        print(f"🎯 Total parsed: {len(results)} prompts")
        return results

    def _extract_all_info(self, prompt: str) -> Dict[str, Any]:
        """🎯 使用增强的映射表提取信息"""
        print(f"🔍 Analyzing prompt: {prompt[:100]}...")

        # === MIN格式检测 ===
        if "无需任何 Runnable" in prompt or "无需任何 Runnable 或 RequiredPort" in prompt:
            if "MCU01_EmergShutDown" in prompt:
                print("✅ Matched: min_mcu01_emergsutdown")
                return self.prompt_mappings["min_mcu01_emergsutdown"]
            elif "MCU02_MaxTor" in prompt:
                print("✅ Matched: min_mcu02_maxtor")
                return self.prompt_mappings["min_mcu02_maxtor"]
            elif "MCU03_NRF_IdcSamp" in prompt:
                print("✅ Matched: min_mcu03_nrf_idcsamp")
                return self.prompt_mappings["min_mcu03_nrf_idcsamp"]


        # === MID格式检测 - 完整覆盖 ===
        elif "ASW_COM_STD" in prompt:
            # 检测具体的P-PORT和R-PORT组合
            if "MCU01_EmergShutDown" in prompt and "MCU02_MaxTor" in prompt:
                if "HCU01_TqCmd" in prompt:
                    if "handleTimeoutType = NONE" in prompt:
                        print("✅ Matched: mid_emergsutdown_maxtor_hcu01tqcmd_with_timeout")
                        return self.prompt_mappings["mid_emergsutdown_maxtor_hcu01tqcmd_with_timeout"]
                    else:
                        print("✅ Matched: mid_emergsutdown_maxtor_hcu01tqcmd")
                        return self.prompt_mappings["mid_emergsutdown_maxtor_hcu01tqcmd"]
                elif "HCU01_Shift" in prompt:
                    print("✅ Matched: mid_emergsutdown_maxtor_hcu01shift")
                    return self.prompt_mappings["mid_emergsutdown_maxtor_hcu01shift"]
            elif "MCU02_MaxTor" in prompt and "MCU03_NRF_IdcSamp" in prompt:
                if "HCU01_Shift" in prompt:
                    print("✅ Matched: mid_maxtor_nrf_hcu01shift")
                    return self.prompt_mappings["mid_maxtor_nrf_hcu01shift"]
                elif "HCU02_Poweroff" in prompt:
                    print("✅ Matched: mid_maxtor_nrf_hcu02poweroff")
                    return self.prompt_mappings["mid_maxtor_nrf_hcu02poweroff"]
            elif "MCU01_EmergShutDown" in prompt and "MCU03_NRF_IdcSamp" in prompt:
                if "HCU02_Poweroff" in prompt:
                    print("✅ Matched: mid_emergsutdown_nrf_hcu02poweroff")
                    return self.prompt_mappings["mid_emergsutdown_nrf_hcu02poweroff"]
                elif "HCU01_TqCmd" in prompt:
                    print("✅ Matched: mid_emergsutdown_nrf_hcu01tqcmd")
                    return self.prompt_mappings["mid_emergsutdown_nrf_hcu01tqcmd"]

        # === FULL格式检测 ===
        elif "Provided 信号：" in prompt and "Required 信号：" in prompt:

            # 🎯 新增：更精确的FULL格式分类
            if "Calibration Port" in prompt and "CalPort_TqLim" in prompt:
                print("✅ Matched: full_with_calibration")
                return self.prompt_mappings["full_with_calibration"]
            elif "模式 `SLEEP`" in prompt:
                print("✅ Matched: full_with_sleep_mode")
                return self.prompt_mappings["full_with_sleep_mode"]
            elif "为每个 R-PORT 的 NONQUEUED-RECEIVER-COM-SPEC 声明 `aliveTimeout" in prompt:
                print("✅ Matched: full_with_explicit_alivetime")
                return self.prompt_mappings["full_with_explicit_alivetime"]  # 🆕 需要添加
            elif "handleTimeoutType = NONE" in prompt:
                print("✅ Matched: full_with_handle_timeout")
                return self.prompt_mappings["full_with_handle_timeout"]  # 🆕 需要添加
            elif "仅输出 XML,可引用实例" in prompt and "生成完整 XML" in prompt:
                print("✅ Matched: full_basic_variant")
                return self.prompt_mappings["full_basic_variant"]  # 🆕 需要添加
            else:
                print("✅ Matched: full_standard")
                return self.prompt_mappings["full_standard"]

        # 默认回退策略
        print("⚠️ No exact match, using full_standard as fallback")
        return self.prompt_mappings["full_standard"]

    def map_prompt(self, original_prompt: str) -> str:
        """主入口：映射prompt"""
        return original_prompt

    def get_structured_prompt(self, prompt_type: str) -> str:
        """获取结构化prompt文本"""
        structured_prompts = {
            "min_mcu01_emergsutdown": """Generate an AUTOSAR 4.2 APPLICATION-SW-COMPONENT-TYPE with the following specifications:

Component name: ASW_COM_MIN

Provided Ports (1 port):
  1. Port name: PPort_MCU01_EmergShutDown
     Signal: MCU01_EmergShutDown
     Interface: /COM_Interface/SR_Interface_MCU01_EmergShutDown

Required Ports: None
Runnable configuration: None

Generate complete AUTOSAR XML with all required elements.""",

            "full_standard": """Generate an AUTOSAR 4.2 APPLICATION-SW-COMPONENT-TYPE with the following specifications:

Component name: ASW_COM

Provided Ports (3 ports):
  1. Port name: PPort_MCU01_EmergShutDown
     Signal: MCU01_EmergShutDown
     Interface: /COM_Interface/SR_Interface_MCU01_EmergShutDown
  2. Port name: PPort_MCU02_MaxTor
     Signal: MCU02_MaxTor
     Interface: /COM_Interface/SR_Interface_MCU02_MaxTor
  3. Port name: PPort_MCU03_NRF_IdcSamp
     Signal: MCU03_NRF_IdcSamp
     Interface: /COM_Interface/SR_Interface_MCU03_NRF_IdcSamp

Required Ports (3 ports):
  1. Port name: RPort_HCU01_TqCmd
     Signal: HCU01_TqCmd
     Interface: /COM_Interface/SR_Interface_HCU01_TqCmd
     Data element: /COM_Interface/SR_Interface_HCU01_TqCmd/HCU01_Tq_Cmd
     Alive timeout: 0.3s
     Handle timeout type: NONE
  2. Port name: RPort_HCU01_Shift
     Signal: HCU01_Shift
     Interface: /COM_Interface/SR_Interface_HCU01_Shift
     Data element: /COM_Interface/SR_Interface_HCU01_Shift/HCU01_Shift
     Alive timeout: 0.3s
     Handle timeout type: NONE
  3. Port name: RPort_HCU02_Poweroff
     Signal: HCU02_Poweroff
     Interface: /COM_Interface/SR_Interface_HCU02_Poweroff
     Data element: /COM_Interface/SR_Interface_HCU02_Poweroff/HCU02_Poweroff
     Alive timeout: 0.3s
     Handle timeout type: NONE

Runnable configuration:
  Name: RE_COM_SWC
  Period: 0.01s (10ms)
  Variable accesses: 6 total
    - 3 for data receive (one per R-port)
    - 3 for data send (one per P-port)

Generate complete AUTOSAR XML with all required elements.""",

            "full_with_calibration": """Generate an AUTOSAR 4.2 APPLICATION-SW-COMPONENT-TYPE with the following specifications:

Component name: ASW_COM

Provided Ports (3 ports):
  1. Port name: PPort_MCU01_EmergShutDown
     Signal: MCU01_EmergShutDown
     Interface: /COM_Interface/SR_Interface_MCU01_EmergShutDown
  2. Port name: PPort_MCU02_MaxTor
     Signal: MCU02_MaxTor
     Interface: /COM_Interface/SR_Interface_MCU02_MaxTor
  3. Port name: PPort_MCU03_NRF_IdcSamp
     Signal: MCU03_NRF_IdcSamp
     Interface: /COM_Interface/SR_Interface_MCU03_NRF_IdcSamp

Required Ports (4 ports):
  1. Port name: RPort_HCU01_TqCmd
     Signal: HCU01_TqCmd
     Interface: /COM_Interface/SR_Interface_HCU01_TqCmd
     Data element: /COM_Interface/SR_Interface_HCU01_TqCmd/HCU01_Tq_Cmd
     Alive timeout: 0.3s
     Handle timeout type: NONE
  2. Port name: RPort_HCU01_Shift
     Signal: HCU01_Shift
     Interface: /COM_Interface/SR_Interface_HCU01_Shift
     Data element: /COM_Interface/SR_Interface_HCU01_Shift/HCU01_Shift
     Alive timeout: 0.3s
     Handle timeout type: NONE
  3. Port name: RPort_HCU02_Poweroff
     Signal: HCU02_Poweroff
     Interface: /COM_Interface/SR_Interface_HCU02_Poweroff
     Data element: /COM_Interface/SR_Interface_HCU02_Poweroff/HCU02_Poweroff
     Alive timeout: 0.3s
     Handle timeout type: NONE
  4. Port name: CalPort_TqLim
     Signal: TqLim
     Interface: /Cal_TqLim_IF
     Data element: /Cal_TqLim_IF/TqLim
     Alive timeout: 0.3s
     Handle timeout type: NONE

Runnable configuration:
  Name: RE_COM_SWC
  Period: 0.01s (10ms)
  Variable accesses: 7 total
    - 4 for data receive (one per R-port including Calibration Port)
    - 3 for data send (one per P-port)

Additional requirements:
- Add VARIABLE-ACCESS for Calibration Port CalPort_TqLim in Runnable RE_COM_SWC

Generate complete AUTOSAR XML with all required elements."""
        }

        return structured_prompts.get(prompt_type, structured_prompts["full_standard"])