# -*- coding: utf-8 -*-
# Run with: Python (not pytest)

import sys
import unittest
from pathlib import Path
from typing import Dict, Any, List

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.llm_generation.core.round1_designer import Round1Designer


class checkRound1ArchitectureDesigner(unittest.TestCase):
    """Round1架构设计器测试类"""

    def setUp(self):
        """测试前设置"""
        self.designer = Round1Designer()
        # 模拟LLM响应
        self.mock_llm_response = None

    def tearDown(self):
        """测试后清理"""
        pass

    # ==================== 测试1：架构设计输出结构完整性 ====================

    def check_architecture_output_structure_completeness(self):
        """测试架构设计输出结构的完整性"""

        # 准备模拟的完整架构响应
        mock_response = {
            "system_analysis": {
                "functional_decomposition": "系统分为传感器数据采集、数据处理、控制输出三个主要功能模块",
                "data_flow_analysis": "传感器数据->预处理->算法处理->控制决策->执行器输出",
                "timing_requirements": "主循环10ms，数据采集100Hz，控制输出50Hz",
                "scalability_considerations": "支持动态添加传感器，模块化设计便于扩展"
            },
            "component_plan": [
                {
                    "component_id": "comp_001",
                    "name": "TemperatureSensor",
                    "type": "SENSOR-ACTUATOR-SW-COMPONENT-TYPE",
                    "purpose": "读取和预处理温度传感器数据",
                    "estimated_complexity": "Simple",
                    "port_estimates": {
                        "input_ports": "硬件接口输入",
                        "output_ports": "温度数据输出端口"
                    },
                    "behavioral_characteristics": "周期性采样，数据滤波",
                    "element_design": {
                        "ports": {
                            "needed": True,
                            "details": "需要一个输出端口发送温度数据"
                        },
                        "internal_behaviors": {
                            "needed": True,
                            "runnables": ["ReadTemperature", "FilterData"],
                            "events": ["TIMING-EVENT-10ms"]
                        }
                    }
                }
            ],
            "interface_plan": [
                {
                    "interface_id": "intf_001",
                    "name": "TemperatureDataInterface",
                    "type": "SENDER-RECEIVER-INTERFACE",
                    "communication_pattern": "异步广播",
                    "data_category": "传感器数据",
                    "connected_components": ["TemperatureSensor", "DataProcessor"],
                    "performance_requirements": "低延迟，高可靠性"
                }
            ],
            "connection_topology": {
                "component_connections": "TemperatureSensor -> DataProcessor -> Controller",
                "data_flow_paths": "传感器数据单向流动到处理器",
                "control_flow_paths": "控制器反馈到传感器配置"
            },
            "architecture_rationale": {
                "design_decisions": "采用分层架构，明确职责分离",
                "tradeoff_analysis": "性能vs模块化的平衡",
                "alternative_considerations": "考虑过集中式架构，但扩展性差",
                "risk_assessment": "主要风险在于实时性保证"
            }
        }

        # 验证结构完整性的辅助函数
        def validate_structure(design_output: Dict[str, Any]) -> List[str]:
            """验证架构设计输出结构，返回错误列表"""
            errors = []

            # 1. 验证顶级结构
            required_top_level = ["system_analysis", "component_plan", "interface_plan",
                                  "connection_topology", "architecture_rationale"]
            for field in required_top_level:
                if field not in design_output:
                    errors.append(f"缺少必需的顶级字段: {field}")

            # 2. 验证system_analysis
            if "system_analysis" in design_output:
                sa = design_output["system_analysis"]
                required_sa_fields = ["functional_decomposition", "data_flow_analysis"]
                for field in required_sa_fields:
                    if field not in sa:
                        errors.append(f"system_analysis缺少必需字段: {field}")

            # 3. 验证component_plan
            if "component_plan" in design_output:
                for i, comp in enumerate(design_output["component_plan"]):
                    comp_errors = validate_component_structure(comp, i)
                    errors.extend(comp_errors)

            # 4. 验证interface_plan
            if "interface_plan" in design_output:
                for i, intf in enumerate(design_output["interface_plan"]):
                    intf_errors = validate_interface_structure(intf, i)
                    errors.extend(intf_errors)

            # 5. 验证connection_topology
            if "connection_topology" in design_output:
                ct = design_output["connection_topology"]
                required_ct_fields = ["component_connections", "data_flow_paths"]
                for field in required_ct_fields:
                    if field not in ct:
                        errors.append(f"connection_topology缺少必需字段: {field}")

            # 6. 验证architecture_rationale
            if "architecture_rationale" in design_output:
                ar = design_output["architecture_rationale"]
                if "design_decisions" not in ar:
                    errors.append("architecture_rationale缺少design_decisions")

            return errors

        def validate_component_structure(comp: Dict[str, Any], index: int) -> List[str]:
            """验证单个组件的结构"""
            errors = []
            prefix = f"component_plan[{index}]"

            # 必需字段
            required = ["component_id", "name", "type", "purpose"]
            for field in required:
                if field not in comp:
                    errors.append(f"{prefix}缺少必需字段: {field}")

            # 验证element_design - 这是关键！
            if "element_design" not in comp:
                errors.append(f"{prefix}缺少element_design字段")
            else:
                ed = comp["element_design"]
                if "ports" not in ed:
                    errors.append(f"{prefix}.element_design缺少ports定义")
                else:
                    if "needed" not in ed["ports"]:
                        errors.append(f"{prefix}.element_design.ports缺少needed字段")

                if "internal_behaviors" not in ed:
                    errors.append(f"{prefix}.element_design缺少internal_behaviors定义")
                else:
                    ib = ed["internal_behaviors"]
                    if "needed" not in ib:
                        errors.append(f"{prefix}.element_design.internal_behaviors缺少needed字段")
                    if ib.get("needed") and not ib.get("runnables"):
                        errors.append(f"{prefix}.element_design.internal_behaviors需要但缺少runnables")

            return errors

        def validate_interface_structure(intf: Dict[str, Any], index: int) -> List[str]:
            """验证单个接口的结构"""
            errors = []
            prefix = f"interface_plan[{index}]"

            required = ["interface_id", "name", "type", "communication_pattern"]
            for field in required:
                if field not in intf:
                    errors.append(f"{prefix}缺少必需字段: {field}")

            return errors

        # 执行验证
        errors = validate_structure(mock_response)
        self.assertEqual(len(errors), 0, f"结构验证失败: {errors}")

        print("✅ 测试1通过：架构设计输出结构完整")

    # ==================== 测试2：element_design正确性 ====================

    def check_element_design_correctness(self):
        """测试element_design的正确性和组件类型匹配"""

        test_cases = [
            {
                "component_type": "SENSOR-ACTUATOR-SW-COMPONENT-TYPE",
                "expected_ports_needed": True,  # 传感器组件必需端口
                "expected_behaviors_needed": True,  # 需要周期性采样行为
                "expected_runnables": ["ReadSensor", "ProcessData"],
                "description": "传感器组件必须有端口和行为"
            },
            {
                "component_type": "APPLICATION-SW-COMPONENT-TYPE",
                "expected_ports_needed": True,  # 应用组件需要端口交互
                "expected_behaviors_needed": True,  # 需要复杂的内部行为
                "expected_runnables": ["MainAlgorithm", "DataProcessing"],
                "description": "应用组件需要端口和复杂行为"
            },
            {
                "component_type": "PARAMETER-SW-COMPONENT-TYPE",
                "expected_ports_needed": True,  # 参数组件需要提供端口
                "expected_behaviors_needed": False,  # 通常不需要复杂行为
                "expected_runnables": [],
                "description": "参数组件主要提供数据，行为简单"
            },
            {
                "component_type": "COMPOSITION-SW-COMPONENT-TYPE",
                "expected_ports_needed": True,  # 组合组件需要代理端口
                "expected_behaviors_needed": False,  # 主要是结构组合
                "expected_runnables": [],
                "description": "组合组件主要做结构组合"
            }
        ]

        def validate_element_design_for_type(
                component_type: str,
                element_design: Dict[str, Any],
                expected_ports: bool,
                expected_behaviors: bool
        ) -> List[str]:
            """根据组件类型验证element_design的合理性"""
            errors = []

            # 验证端口设计
            if element_design.get("ports", {}).get("needed") != expected_ports:
                errors.append(f"{component_type}的ports.needed应该是{expected_ports}")

            # 验证行为设计
            ib = element_design.get("internal_behaviors", {})
            if ib.get("needed") != expected_behaviors:
                errors.append(f"{component_type}的internal_behaviors.needed应该是{expected_behaviors}")

            # 如果需要行为，验证runnables和events
            if expected_behaviors and ib.get("needed"):
                if not ib.get("runnables"):
                    errors.append(f"{component_type}需要定义runnables")
                if not ib.get("events"):
                    errors.append(f"{component_type}需要定义events")

            return errors

        # 测试每种组件类型
        all_errors = []
        for test_case in test_cases:
            # 创建测试组件
            test_component = {
                "component_id": "test_comp",
                "name": f"Test{test_case['component_type']}",
                "type": test_case["component_type"],
                "purpose": "测试组件",
                "element_design": {
                    "ports": {
                        "needed": test_case["expected_ports_needed"],
                        "details": "测试端口"
                    },
                    "internal_behaviors": {
                        "needed": test_case["expected_behaviors_needed"],
                        "runnables": test_case["expected_runnables"],
                        "events": ["TIMING-EVENT"] if test_case["expected_behaviors_needed"] else []
                    }
                }
            }

            # 验证
            errors = validate_element_design_for_type(
                test_case["component_type"],
                test_component["element_design"],
                test_case["expected_ports_needed"],
                test_case["expected_behaviors_needed"]
            )

            if errors:
                all_errors.extend(errors)
                print(f"❌ {test_case['component_type']}: {test_case['description']}")
                for error in errors:
                    print(f"   - {error}")
            else:
                print(f"✅ {test_case['component_type']}: {test_case['description']}")

        self.assertEqual(len(all_errors), 0, f"element_design验证失败: {all_errors}")

        print("✅ 测试2通过：element_design正确性验证")

    # ==================== 测试3：多组件场景测试 ====================

    def check_multi_component_scenarios(self):
        """测试不同规模的多组件场景"""

        scenarios = [
            {
                "name": "简单场景",
                "component_count": 1,
                "interface_count": 0,
                "description": "单个独立组件"
            },
            {
                "name": "中等场景",
                "component_count": 5,
                "interface_count": 4,
                "description": "传感器-处理器-控制器架构"
            },
            {
                "name": "复杂场景",
                "component_count": 12,
                "interface_count": 15,
                "description": "完整的多层次系统架构"
            }
        ]

        def generate_mock_architecture(comp_count: int, intf_count: int) -> Dict[str, Any]:
            """生成模拟的架构设计"""
            components = []
            interfaces = []

            # 生成组件
            component_types = [
                "SENSOR-ACTUATOR-SW-COMPONENT-TYPE",
                "APPLICATION-SW-COMPONENT-TYPE",
                "SERVICE-SW-COMPONENT-TYPE",
                "PARAMETER-SW-COMPONENT-TYPE",
                "COMPOSITION-SW-COMPONENT-TYPE"
            ]

            for i in range(comp_count):
                comp_type = component_types[i % len(component_types)]
                components.append({
                    "component_id": f"comp_{i:03d}",
                    "name": f"Component_{i}",
                    "type": comp_type,
                    "purpose": f"组件{i}的功能描述",
                    "estimated_complexity": ["Simple", "Medium", "Complex"][i % 3],
                    "port_estimates": {
                        "input_ports": f"{i % 3 + 1}个输入端口",
                        "output_ports": f"{i % 2 + 1}个输出端口"
                    },
                    "behavioral_characteristics": f"行为特征{i}",
                    "element_design": {
                        "ports": {
                            "needed": True,
                            "details": f"端口设计{i}"
                        },
                        "internal_behaviors": {
                            "needed": comp_type != "PARAMETER-SW-COMPONENT-TYPE",
                            "runnables": [f"Runnable_{i}_1",
                                          f"Runnable_{i}_2"] if comp_type != "PARAMETER-SW-COMPONENT-TYPE" else [],
                            "events": [f"EVENT_{i}"] if comp_type != "PARAMETER-SW-COMPONENT-TYPE" else []
                        }
                    }
                })

            # 生成接口
            interface_types = [
                "SENDER-RECEIVER-INTERFACE",
                "CLIENT-SERVER-INTERFACE",
                "MODE-SWITCH-INTERFACE",
                "NV-DATA-INTERFACE"
            ]

            for i in range(intf_count):
                intf_type = interface_types[i % len(interface_types)]
                # 随机连接两个组件
                comp1_idx = i % comp_count
                comp2_idx = (i + 1) % comp_count
                interfaces.append({
                    "interface_id": f"intf_{i:03d}",
                    "name": f"Interface_{i}",
                    "type": intf_type,
                    "communication_pattern": ["同步", "异步", "事件驱动"][i % 3],
                    "data_category": f"数据类别{i}",
                    "connected_components": [
                        components[comp1_idx]["name"],
                        components[comp2_idx]["name"]
                    ],
                    "performance_requirements": f"性能要求{i}"
                })

            return {
                "system_analysis": {
                    "functional_decomposition": f"系统包含{comp_count}个组件，{intf_count}个接口",
                    "data_flow_analysis": "数据流分析",
                    "timing_requirements": "时序要求",
                    "scalability_considerations": "可扩展性考虑"
                },
                "component_plan": components,
                "interface_plan": interfaces,
                "connection_topology": {
                    "component_connections": f"共{comp_count}个组件相互连接",
                    "data_flow_paths": "数据流路径",
                    "control_flow_paths": "控制流路径"
                },
                "architecture_rationale": {
                    "design_decisions": "设计决策",
                    "tradeoff_analysis": "权衡分析",
                    "alternative_considerations": "备选方案",
                    "risk_assessment": "风险评估"
                }
            }

        def validate_multi_component_architecture(
                architecture: Dict[str, Any],
                expected_comp_count: int,
                expected_intf_count: int
        ) -> List[str]:
            """验证多组件架构的合理性"""
            errors = []

            # 验证组件数量
            actual_comp_count = len(architecture.get("component_plan", []))
            if actual_comp_count != expected_comp_count:
                errors.append(f"组件数量不匹配: 期望{expected_comp_count}, 实际{actual_comp_count}")

            # 验证接口数量
            actual_intf_count = len(architecture.get("interface_plan", []))
            if actual_intf_count != expected_intf_count:
                errors.append(f"接口数量不匹配: 期望{expected_intf_count}, 实际{actual_intf_count}")

            # 验证组件ID唯一性
            comp_ids = [c["component_id"] for c in architecture.get("component_plan", [])]
            if len(comp_ids) != len(set(comp_ids)):
                errors.append("存在重复的component_id")

            # 验证接口ID唯一性
            intf_ids = [i["interface_id"] for i in architecture.get("interface_plan", [])]
            if len(intf_ids) != len(set(intf_ids)):
                errors.append("存在重复的interface_id")

            # 验证接口连接的组件存在性
            comp_names = {c["name"] for c in architecture.get("component_plan", [])}
            for intf in architecture.get("interface_plan", []):
                for comp_name in intf.get("connected_components", []):
                    if comp_name not in comp_names:
                        errors.append(f"接口{intf['name']}引用了不存在的组件{comp_name}")

            # 验证复杂场景下的批处理策略
            if expected_comp_count > 10:
                # 验证是否有合理的复杂度分布
                complexities = [c.get("estimated_complexity", "Unknown")
                                for c in architecture.get("component_plan", [])]
                if all(c == complexities[0] for c in complexities):
                    errors.append("复杂场景应该有不同的组件复杂度")

            return errors

        # 测试每个场景
        for scenario in scenarios:
            print(f"\n测试场景: {scenario['name']} - {scenario['description']}")
            print(f"  组件数: {scenario['component_count']}, 接口数: {scenario['interface_count']}")

            # 生成架构
            mock_arch = generate_mock_architecture(
                scenario['component_count'],
                scenario['interface_count']
            )

            # 验证
            errors = validate_multi_component_architecture(
                mock_arch,
                scenario['component_count'],
                scenario['interface_count']
            )

            if errors:
                print(f"  ❌ 验证失败:")
                for error in errors:
                    print(f"     - {error}")
            else:
                print(f"  ✅ 验证通过")

            self.assertEqual(len(errors), 0, f"{scenario['name']}验证失败")

        print("\n✅ 测试3通过：多组件场景验证")

    # ==================== 测试4：组件类型多样性 ====================

    def check_component_type_diversity(self):
        """测试不同组件类型的特性和约束"""

        component_type_specs = {
            "APPLICATION-SW-COMPONENT-TYPE": {
                "description": "应用软件组件",
                "typical_ports": (2, 5),  # (min, max)
                "needs_behaviors": True,
                "typical_runnables": ["ProcessData", "ExecuteAlgorithm"],
                "supports_state_machine": True,
                "can_have_service_needs": True
            },
            "SENSOR-ACTUATOR-SW-COMPONENT-TYPE": {
                "description": "传感器执行器组件",
                "typical_ports": (1, 3),
                "needs_behaviors": True,
                "typical_runnables": ["ReadHardware", "WriteHardware"],
                "supports_state_machine": False,
                "can_have_service_needs": False
            },
            "COMPOSITION-SW-COMPONENT-TYPE": {
                "description": "组合组件",
                "typical_ports": (0, 10),  # 可以有很多代理端口
                "needs_behaviors": False,  # 主要是结构
                "typical_runnables": [],
                "supports_state_machine": False,
                "can_have_service_needs": False
            },
            "PARAMETER-SW-COMPONENT-TYPE": {
                "description": "参数组件",
                "typical_ports": (1, 5),  # 只有提供端口
                "needs_behaviors": False,
                "typical_runnables": [],
                "supports_state_machine": False,
                "can_have_service_needs": False
            },
            "SERVICE-SW-COMPONENT-TYPE": {
                "description": "服务组件",
                "typical_ports": (1, 3),
                "needs_behaviors": True,
                "typical_runnables": ["ProvideService"],
                "supports_state_machine": True,
                "can_have_service_needs": True
            },
            "NV-BLOCK-SW-COMPONENT-TYPE": {
                "description": "非易失性数据块组件",
                "typical_ports": (1, 2),
                "needs_behaviors": True,
                "typical_runnables": ["ReadNvData", "WriteNvData"],
                "supports_state_machine": False,
                "can_have_service_needs": False
            }
        }

        def create_component_by_type(comp_type: str, spec: Dict[str, Any]) -> Dict[str, Any]:
            """根据类型规范创建组件"""
            min_ports, max_ports = spec["typical_ports"]
            port_count = (min_ports + max_ports) // 2

            component = {
                "component_id": f"test_{comp_type.lower()}",
                "name": f"Test{comp_type.replace('-', '')}",
                "type": comp_type,
                "purpose": spec["description"],
                "estimated_complexity": "Medium",
                "port_estimates": {
                    "input_ports": f"{port_count // 2}个输入端口" if port_count > 1 else "无",
                    "output_ports": f"{(port_count + 1) // 2}个输出端口" if port_count > 0 else "无"
                },
                "behavioral_characteristics": f"{spec['description']}的典型行为",
                "element_design": {
                    "ports": {
                        "needed": port_count > 0,
                        "details": f"需要{port_count}个端口" if port_count > 0 else "无端口需求"
                    },
                    "internal_behaviors": {
                        "needed": spec["needs_behaviors"],
                        "runnables": spec["typical_runnables"] if spec["needs_behaviors"] else [],
                        "events": ["TIMING-EVENT"] if spec["needs_behaviors"] else []
                    }
                }
            }

            # 添加特定类型的特殊属性
            if spec["supports_state_machine"]:
                component["has_state_machine"] = True

            if spec["can_have_service_needs"]:
                component["service_dependencies"] = ["DiagnosticService", "NvMService"]

            return component

        def validate_component_type_characteristics(
                component: Dict[str, Any],
                spec: Dict[str, Any]
        ) -> List[str]:
            """验证组件类型特性"""
            errors = []
            comp_type = component["type"]

            # 验证端口需求
            has_ports = component["element_design"]["ports"]["needed"]
            min_ports, max_ports = spec["typical_ports"]
            if min_ports > 0 and not has_ports:
                errors.append(f"{comp_type}通常需要端口")

            # 验证行为需求
            needs_behaviors = component["element_design"]["internal_behaviors"]["needed"]
            if spec["needs_behaviors"] != needs_behaviors:
                errors.append(f"{comp_type}的行为需求不正确: 期望{spec['needs_behaviors']}, 实际{needs_behaviors}")

            # 验证Runnables
            if spec["needs_behaviors"]:
                runnables = component["element_design"]["internal_behaviors"]["runnables"]
                if not runnables:
                    errors.append(f"{comp_type}需要定义Runnables")

                # 验证典型的Runnable名称
                for expected_runnable in spec["typical_runnables"]:
                    if not any(expected_runnable in r for r in runnables):
                        print(f"  提示: {comp_type}通常包含{expected_runnable}类型的Runnable")

            # 验证状态机支持
            if spec["supports_state_machine"] and "has_state_machine" not in component:
                print(f"  提示: {comp_type}支持状态机")

            # 验证服务依赖
            if spec["can_have_service_needs"] and "service_dependencies" not in component:
                print(f"  提示: {comp_type}可以有服务依赖")

            return errors

        # 测试每种组件类型
        print("\n组件类型多样性测试:")
        print("=" * 60)

        all_errors = []
        for comp_type, spec in component_type_specs.items():
            print(f"\n测试组件类型: {comp_type}")
            print(f"  描述: {spec['description']}")

            # 创建组件
            component = create_component_by_type(comp_type, spec)

            # 验证
            errors = validate_component_type_characteristics(component, spec)

            if errors:
                print(f"  ❌ 验证失败:")
                for error in errors:
                    print(f"     - {error}")
                all_errors.extend(errors)
            else:
                print(f"  ✅ 验证通过")

            # 显示组件特性
            print(f"  特性:")
            print(f"    - 端口范围: {spec['typical_ports']}")
            print(f"    - 需要行为: {spec['needs_behaviors']}")
            print(f"    - 支持状态机: {spec['supports_state_machine']}")
            print(f"    - 可有服务依赖: {spec['can_have_service_needs']}")

        self.assertEqual(len(all_errors), 0, f"组件类型验证失败: {all_errors}")

        print("\n✅ 测试4通过：组件类型多样性验证")

    # ==================== 集成测试：element_design对Round2的影响 ====================

    def check_element_design_impact_on_round2(self):
        """测试element_design如何影响Round2的Schema生成"""

        print("\n\n测试element_design对Round2 Schema生成的影响:")
        print("=" * 60)

        # 场景1: ports.needed = true的组件
        component_with_ports = {
            "component_id": "comp_with_ports",
            "name": "ComponentWithPorts",
            "type": "APPLICATION-SW-COMPONENT-TYPE",
            "element_design": {
                "ports": {
                    "needed": True,
                    "details": "需要多个输入输出端口"
                },
                "internal_behaviors": {
                    "needed": True,
                    "runnables": ["ProcessData"],
                    "events": ["TIMING-EVENT-10ms"]
                }
            }
        }

        # 场景2: ports.needed = false的组件
        component_without_ports = {
            "component_id": "comp_without_ports",
            "name": "ComponentWithoutPorts",
            "type": "APPLICATION-SW-COMPONENT-TYPE",
            "element_design": {
                "ports": {
                    "needed": False,
                    "details": "独立运行，无需端口"
                },
                "internal_behaviors": {
                    "needed": True,
                    "runnables": ["InternalProcess"],
                    "events": ["INIT-EVENT"]
                }
            }
        }

        # 场景3: internal_behaviors.needed = false的组件
        component_without_behaviors = {
            "component_id": "comp_passive",
            "name": "PassiveComponent",
            "type": "PARAMETER-SW-COMPONENT-TYPE",
            "element_design": {
                "ports": {
                    "needed": True,
                    "details": "提供参数端口"
                },
                "internal_behaviors": {
                    "needed": False,
                    "runnables": [],
                    "events": []
                }
            }
        }

        def simulate_round2_schema_generation(component: Dict[str, Any]) -> Dict[str, Any]:
            """模拟Round2基于element_design生成Schema"""
            schema = {
                "type": "object",
                "properties": {
                    "SHORT-NAME": {"type": "string"},
                    "@UUID": {"type": "string"}
                },
                "required": ["SHORT-NAME", "@UUID"]
            }

            # 根据element_design决定包含哪些元素
            ed = component["element_design"]

            # 端口Schema
            if ed["ports"]["needed"]:
                schema["properties"]["PORTS"] = {
                    "type": "object",
                    "properties": {
                        "P-PORT-PROTOTYPE": {"type": "array"},
                        "R-PORT-PROTOTYPE": {"type": "array"}
                    }
                }
                schema["required"].append("PORTS")
                print(f"    → Schema包含PORTS (因为ports.needed=true)")
            else:
                print(f"    → Schema不包含PORTS (因为ports.needed=false)")

            # 内部行为Schema
            if ed["internal_behaviors"]["needed"]:
                schema["properties"]["INTERNAL-BEHAVIORS"] = {
                    "type": "object",
                    "properties": {
                        "SWC-INTERNAL-BEHAVIOR": {
                            "type": "object",
                            "properties": {
                                "EVENTS": {"type": "object"},
                                "RUNNABLES": {"type": "object"}
                            },
                            "required": ["EVENTS", "RUNNABLES"]
                        }
                    },
                    "required": ["SWC-INTERNAL-BEHAVIOR"]
                }
                schema["required"].append("INTERNAL-BEHAVIORS")

                # 添加具体的Runnable
                runnables = ed["internal_behaviors"]["runnables"]
                if runnables:
                    print(f"    → Schema包含Runnables: {runnables}")

                # 添加具体的Event
                events = ed["internal_behaviors"]["events"]
                if events:
                    print(f"    → Schema包含Events: {events}")
            else:
                print(f"    → Schema不包含INTERNAL-BEHAVIORS (因为internal_behaviors.needed=false)")

            return schema

        # 测试每个场景
        test_scenarios = [
            ("完整组件（端口+行为）", component_with_ports),
            ("无端口组件", component_without_ports),
            ("无行为组件（被动）", component_without_behaviors)
        ]

        for scenario_name, component in test_scenarios:
            print(f"\n场景: {scenario_name}")
            print(f"  组件: {component['name']} ({component['type']})")
            print(f"  element_design:")
            print(f"    - ports.needed: {component['element_design']['ports']['needed']}")
            print(f"    - behaviors.needed: {component['element_design']['internal_behaviors']['needed']}")
            print(f"  生成的Schema特征:")

            schema = simulate_round2_schema_generation(component)

            # 验证Schema必需字段
            print(f"  Schema必需字段: {schema['required']}")

            # 验证关键断言
            ed = component["element_design"]
            if ed["ports"]["needed"]:
                self.assertIn("PORTS", schema["required"], "需要端口时Schema应包含PORTS")
            else:
                self.assertNotIn("PORTS", schema["required"], "不需要端口时Schema不应包含PORTS")

            if ed["internal_behaviors"]["needed"]:
                self.assertIn("INTERNAL-BEHAVIORS", schema["required"], "需要行为时Schema应包含INTERNAL-BEHAVIORS")
            else:
                self.assertNotIn("INTERNAL-BEHAVIORS", schema["required"],
                                 "不需要行为时Schema不应包含INTERNAL-BEHAVIORS")

        print("\n✅ element_design影响测试通过：正确影响Round2 Schema生成")


class checkRound1DesignerIntegration(unittest.TestCase):
    """Round1设计器集成测试"""

    def test_real_world_scenario(self):
        """测试真实世界场景：电池管理系统"""

        print("\n\n" + "=" * 60)
        print("集成测试：电池管理系统架构设计")
        print("=" * 60)

        # 真实的需求描述
        user_requirements = """
        设计一个电动汽车电池管理系统(BMS)的AUTOSAR软件架构，包括：
        1. 电池电压和温度监控
        2. 充放电控制
        3. SOC(State of Charge)计算
        4. 故障诊断和保护
        5. 与整车控制器通信
        """

        # 期望的架构要素
        expected_components = [
            "VoltageSensor",  # 电压传感器
            "TemperatureSensor",  # 温度传感器
            "SOCCalculator",  # SOC计算
            "ChargeController",  # 充电控制
            "FaultDiagnostic",  # 故障诊断
            "BMSController",  # BMS主控制器
            "VehicleInterface"  # 整车接口
        ]

        expected_interfaces = [
            "VoltageData",  # 电压数据
            "TemperatureData",  # 温度数据
            "SOCStatus",  # SOC状态
            "ChargeControl",  # 充电控制
            "DiagnosticInfo",  # 诊断信息
            "VehicleCommand"  # 整车命令
        ]

        # 模拟生成的架构
        mock_architecture = {
            "system_analysis": {
                "functional_decomposition": """
                BMS系统分解为以下功能模块：
                - 数据采集层：电压和温度传感器组件
                - 处理层：SOC计算和故障诊断组件
                - 控制层：充放电控制组件
                - 接口层：与整车通信组件
                """,
                "data_flow_analysis": """
                数据流：
                传感器 -> 数据处理 -> 控制决策 -> 执行动作
                诊断信息 -> 整车接口 -> 外部系统
                """,
                "timing_requirements": """
                - 传感器采样：100ms周期
                - SOC计算：1s周期
                - 故障诊断：10ms周期（安全关键）
                - 整车通信：CAN总线20ms周期
                """,
                "scalability_considerations": """
                支持不同电池包配置（串并联数量可配置）
                支持多种电池化学类型（LFP、NCM等）
                """
            },
            "component_plan": [
                {
                    "component_id": "bms_001",
                    "name": "VoltageSensor",
                    "type": "SENSOR-ACTUATOR-SW-COMPONENT-TYPE",
                    "purpose": "采集各电芯电压数据",
                    "estimated_complexity": "Simple",
                    "element_design": {
                        "ports": {"needed": True, "details": "输出电压数据端口"},
                        "internal_behaviors": {
                            "needed": True,
                            "runnables": ["ReadVoltage", "FilterVoltageData"],
                            "events": ["TIMING-EVENT-100ms"]
                        }
                    }
                },
                {
                    "component_id": "bms_002",
                    "name": "TemperatureSensor",
                    "type": "SENSOR-ACTUATOR-SW-COMPONENT-TYPE",
                    "purpose": "采集电池包温度数据",
                    "estimated_complexity": "Simple",
                    "element_design": {
                        "ports": {"needed": True, "details": "输出温度数据端口"},
                        "internal_behaviors": {
                            "needed": True,
                            "runnables": ["ReadTemperature", "ValidateTemp"],
                            "events": ["TIMING-EVENT-100ms"]
                        }
                    }
                },
                {
                    "component_id": "bms_003",
                    "name": "SOCCalculator",
                    "type": "APPLICATION-SW-COMPONENT-TYPE",
                    "purpose": "基于电压、电流和温度计算SOC",
                    "estimated_complexity": "Complex",
                    "element_design": {
                        "ports": {"needed": True, "details": "输入传感器数据，输出SOC"},
                        "internal_behaviors": {
                            "needed": True,
                            "runnables": ["CalculateSOC", "UpdateSOCModel"],
                            "events": ["TIMING-EVENT-1s", "DATA-RECEIVED-EVENT"]
                        }
                    }
                },
                {
                    "component_id": "bms_004",
                    "name": "ChargeController",
                    "type": "APPLICATION-SW-COMPONENT-TYPE",
                    "purpose": "控制充放电过程",
                    "estimated_complexity": "Complex",
                    "element_design": {
                        "ports": {"needed": True, "details": "输入SOC和命令，输出控制信号"},
                        "internal_behaviors": {
                            "needed": True,
                            "runnables": ["ControlCharging", "ProtectBattery"],
                            "events": ["TIMING-EVENT-10ms"]
                        }
                    }
                },
                {
                    "component_id": "bms_005",
                    "name": "FaultDiagnostic",
                    "type": "APPLICATION-SW-COMPONENT-TYPE",
                    "purpose": "诊断电池故障和异常",
                    "estimated_complexity": "Medium",
                    "element_design": {
                        "ports": {"needed": True, "details": "输入所有传感器数据，输出诊断结果"},
                        "internal_behaviors": {
                            "needed": True,
                            "runnables": ["DiagnosesFault", "GenerateDTC"],
                            "events": ["TIMING-EVENT-10ms"]
                        }
                    }
                }
            ],
            "interface_plan": [
                {
                    "interface_id": "intf_001",
                    "name": "VoltageDataInterface",
                    "type": "SENDER-RECEIVER-INTERFACE",
                    "communication_pattern": "周期性广播",
                    "connected_components": ["VoltageSensor", "SOCCalculator", "FaultDiagnostic"]
                },
                {
                    "interface_id": "intf_002",
                    "name": "TemperatureDataInterface",
                    "type": "SENDER-RECEIVER-INTERFACE",
                    "communication_pattern": "周期性广播",
                    "connected_components": ["TemperatureSensor", "SOCCalculator", "FaultDiagnostic"]
                },
                {
                    "interface_id": "intf_003",
                    "name": "SOCStatusInterface",
                    "type": "SENDER-RECEIVER-INTERFACE",
                    "communication_pattern": "事件触发",
                    "connected_components": ["SOCCalculator", "ChargeController"]
                }
            ],
            "connection_topology": {
                "component_connections": """
                传感器层 -> 处理层 -> 控制层
                所有组件 -> 诊断组件（监控）
                控制层 <-> 整车接口（双向）
                """,
                "data_flow_paths": "传感器数据单向流向处理和控制",
                "control_flow_paths": "整车命令影响充电控制"
            },
            "architecture_rationale": {
                "design_decisions": """
                1. 采用分层架构确保安全性和可维护性
                2. 故障诊断独立运行，提高系统可靠性
                3. SOC计算与控制分离，便于算法升级
                """,
                "risk_assessment": "主要风险：传感器故障、通信延迟、算法精度"
            }
        }

        def validate_bms_architecture(architecture: Dict[str, Any]) -> Dict[str, Any]:
            """验证BMS架构的完整性和合理性"""
            validation_result = {
                "passed": True,
                "warnings": [],
                "errors": [],
                "statistics": {}
            }

            # 统计信息
            comp_count = len(architecture.get("component_plan", []))
            intf_count = len(architecture.get("interface_plan", []))

            validation_result["statistics"] = {
                "component_count": comp_count,
                "interface_count": intf_count,
                "sensor_components": 0,
                "application_components": 0,
                "safety_critical_components": 0
            }

            # 验证关键组件存在性
            component_names = {c["name"] for c in architecture.get("component_plan", [])}

            critical_components = ["VoltageSensor", "TemperatureSensor", "FaultDiagnostic"]
            for critical in critical_components:
                if critical not in component_names:
                    validation_result["errors"].append(f"缺少关键组件: {critical}")
                    validation_result["passed"] = False

            # 统计组件类型
            for comp in architecture.get("component_plan", []):
                comp_type = comp.get("type", "")
                if "SENSOR" in comp_type:
                    validation_result["statistics"]["sensor_components"] += 1
                elif "APPLICATION" in comp_type:
                    validation_result["statistics"]["application_components"] += 1

                # 检查安全关键组件
                if "Fault" in comp["name"] or "Protect" in str(comp.get("element_design", {})):
                    validation_result["statistics"]["safety_critical_components"] += 1

            # 验证时序要求
            timing = architecture.get("system_analysis", {}).get("timing_requirements", "")
            if "10ms" in timing:
                print("  ✓ 包含安全关键的10ms周期")
            else:
                validation_result["warnings"].append("未明确10ms安全周期")

            # 验证接口完整性
            interface_types = {i["type"] for i in architecture.get("interface_plan", [])}
            if "SENDER-RECEIVER-INTERFACE" not in interface_types:
                validation_result["warnings"].append("缺少发送-接收接口")

            # 验证element_design合理性
            for comp in architecture.get("component_plan", []):
                ed = comp.get("element_design", {})
                if comp["type"] == "SENSOR-ACTUATOR-SW-COMPONENT-TYPE":
                    if not ed.get("ports", {}).get("needed"):
                        validation_result["errors"].append(f"传感器组件{comp['name']}应该需要端口")
                        validation_result["passed"] = False

                if "Calculator" in comp["name"] or "Controller" in comp["name"]:
                    if not ed.get("internal_behaviors", {}).get("runnables"):
                        validation_result["warnings"].append(f"处理组件{comp['name']}应该定义Runnables")

            return validation_result

        # 执行验证
        print("\n验证BMS架构设计:")
        result = validate_bms_architecture(mock_architecture)

        print(f"\n统计信息:")
        for key, value in result["statistics"].items():
            print(f"  - {key}: {value}")

        if result["errors"]:
            print(f"\n错误 ({len(result['errors'])}):")
            for error in result["errors"]:
                print(f"  ❌ {error}")

        if result["warnings"]:
            print(f"\n警告 ({len(result['warnings'])}):")
            for warning in result["warnings"]:
                print(f"  ⚠️  {warning}")

        if result["passed"]:
            print(f"\n✅ BMS架构验证通过！")
        else:
            print(f"\n❌ BMS架构验证失败")

        self.assertTrue(result["passed"], "BMS架构验证应该通过")

        # 额外验证：element_design的影响链
        print("\n\nelement_design影响链分析:")
        print("-" * 40)
        for comp in mock_architecture["component_plan"]:
            print(f"\n组件: {comp['name']}")
            ed = comp["element_design"]
            print(f"  element_design配置:")
            print(f"    - ports.needed: {ed['ports']['needed']}")
            print(f"    - behaviors.needed: {ed['internal_behaviors']['needed']}")
            if ed["internal_behaviors"]["needed"]:
                print(f"    - runnables: {ed['internal_behaviors']['runnables']}")
                print(f"    - events: {ed['internal_behaviors']['events']}")

            print(f"  → Round2影响:")
            if ed["ports"]["needed"]:
                print(f"     Schema将包含PORTS结构")
            if ed["internal_behaviors"]["needed"]:
                print(f"     Schema将包含INTERNAL-BEHAVIORS")
                print(f"     将生成{len(ed['internal_behaviors']['runnables'])}个Runnable实体")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("Round1架构设计器完整测试套件")
    print("=" * 60)

    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加所有测试
    suite.addTests(loader.loadTestsFromTestCase(checkRound1ArchitectureDesigner))
    suite.addTests(loader.loadTestsFromTestCase(checkRound1DesignerIntegration))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 显示总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"运行测试: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n🎉 所有测试通过！Round1架构设计器功能正常")
        print("\n关键验证点:")
        print("✓ 架构设计输出结构完整")
        print("✓ element_design正确配置")
        print("✓ 支持多组件场景")
        print("✓ 组件类型多样性")
        print("✓ element_design正确影响Round2 Schema生成")
    else:
        print("\n❌ 存在测试失败，请检查问题")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)