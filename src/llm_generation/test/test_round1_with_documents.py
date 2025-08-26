"""test_round1_with_documents.py - Round1文档处理测试

测试Round1的文档上传、处理和架构设计功能
包括单文档、多文档、多组件生成等场景
"""

import os
import sys
import json
import tempfile
import unittest
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, patch, MagicMock

# 添加项目路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.llm_generation.core.round1_designer import Round1Designer
from src.llm_generation.utils.document_processor import DocumentProcessor
from src.llm_generation.utils.exceptions import ArchitectureDesignError


class TestRound1WithDocuments(unittest.TestCase):
    """Round1文档处理测试类"""

    def setUp(self):
        """测试初始化"""
        self.round1_designer = Round1Designer()
        self.document_processor = DocumentProcessor()
        self.test_data_dir = Path(__file__).parent / "test_data"
        self.test_data_dir.mkdir(exist_ok=True)

    def tearDown(self):
        """测试清理"""
        # 清理上传的文档
        self.document_processor.cleanup_all_files()

    def create_test_pdf(self, filename: str, content: str) -> str:
        """创建测试PDF文件（模拟）"""
        # 由于创建真实PDF需要额外库，这里创建文本文件模拟
        file_path = self.test_data_dir / f"{filename}.txt"
        file_path.write_text(content)
        return str(file_path)

    def create_test_requirements(self) -> str:
        """创建测试需求文档"""
        content = """
        AUTOSAR Motor Control System Requirements

        1. System Overview
        The system shall control a motor with closed-loop feedback control.

        2. Components Required
        - Temperature Sensor Component: Read motor temperature
        - Speed Sensor Component: Read motor RPM
        - Controller Component: Implement PID control algorithm
        - Actuator Component: Send PWM signals to motor

        3. Interfaces
        - Sensor Data Interface: Transfer sensor readings
        - Control Command Interface: Transfer control signals

        4. Performance Requirements
        - Control loop: 10ms cycle time
        - Temperature monitoring: 100ms cycle
        - Response time: < 5ms

        5. Safety Requirements
        - Over-temperature protection
        - Emergency stop capability
        """
        return self.create_test_pdf("requirements", content)

    def create_test_architecture(self) -> str:
        """创建测试架构文档"""
        content = """
        System Architecture Design

        Layer 1: Sensor Layer
        - TemperatureSensor_Component
        - SpeedSensor_Component

        Layer 2: Control Layer  
        - MotorController_Component (main control logic)
        - SafetyMonitor_Component (safety checks)

        Layer 3: Actuator Layer
        - MotorActuator_Component

        Data Flow:
        Sensors -> Controller -> Actuator
        All components -> SafetyMonitor
        """
        return self.create_test_pdf("architecture", content)

    @patch('google.generativeai.upload_file')
    @patch('google.generativeai.GenerativeModel.generate_content')
    def test_single_document_upload(self, mock_generate, mock_upload):
        """测试单个文档上传和处理"""

        # 创建测试文档
        req_file = self.create_test_requirements()

        # 模拟文件上传
        mock_file = Mock()
        mock_file.name = "file_123"
        mock_file.display_name = "requirements.txt"
        mock_file.uri = "https://generativelanguage.googleapis.com/v1/files/file_123"
        mock_file.state.name = "ACTIVE"
        mock_file.mime_type = "text/plain"
        mock_upload.return_value = mock_file

        # 模拟内容提取
        mock_response = Mock()
        mock_response.text = "文档包含电机控制系统需求，需要4个组件和2个接口"
        mock_generate.return_value = mock_response

        # 上传文档
        uploaded_file = self.document_processor.upload_file(req_file)

        # 验证上传
        self.assertIsNotNone(uploaded_file)
        self.assertEqual(uploaded_file.display_name, "requirements.txt")
        mock_upload.assert_called_once()

        # 提取内容
        content = self.document_processor.extract_document_content(uploaded_file)
        self.assertIn("电机控制", content)

    @patch('google.generativeai.upload_file')
    @patch('src.llm_generation.llm.gemini_client.GeminiClient.generate_with_schema')
    def test_round1_with_documents(self, mock_generate_schema, mock_upload):
        """测试Round1使用文档进行架构设计"""

        # 创建测试文档
        req_file = self.create_test_requirements()
        arch_file = self.create_test_architecture()

        # 模拟文件上传
        mock_files = []
        for i, (path, name) in enumerate([(req_file, "requirements.txt"),
                                          (arch_file, "architecture.txt")]):
            mock_file = Mock()
            mock_file.name = f"file_{i}"
            mock_file.display_name = name
            mock_file.uri = f"https://generativelanguage.googleapis.com/v1/files/file_{i}"
            mock_file.state.name = "ACTIVE"
            mock_files.append(mock_file)

        mock_upload.side_effect = mock_files

        # 模拟LLM生成的架构设计（多组件）
        mock_architecture = {
            "system_analysis": {
                "functional_decomposition": "系统分为传感层、控制层和执行层",
                "data_flow_analysis": "传感器->控制器->执行器的数据流",
                "timing_requirements": "10ms控制周期",
                "document_based_requirements": "基于上传的需求文档和架构文档"
            },
            "component_plan": [
                {
                    "component_id": "comp_1",
                    "name": "TemperatureSensorComponent",
                    "type": "SENSOR-ACTUATOR-SW-COMPONENT-TYPE",
                    "purpose": "读取电机温度",
                    "estimated_complexity": "Simple",
                    "element_design": {
                        "ports": {
                            "needed": True,
                            "details": "需要一个输出端口发送温度数据"
                        }
                    }
                },
                {
                    "component_id": "comp_2",
                    "name": "SpeedSensorComponent",
                    "type": "SENSOR-ACTUATOR-SW-COMPONENT-TYPE",
                    "purpose": "读取电机转速",
                    "estimated_complexity": "Simple",
                    "element_design": {
                        "ports": {
                            "needed": True,
                            "details": "需要一个输出端口发送转速数据"
                        }
                    }
                },
                {
                    "component_id": "comp_3",
                    "name": "MotorControllerComponent",
                    "type": "APPLICATION-SW-COMPONENT-TYPE",
                    "purpose": "实现PID控制算法",
                    "estimated_complexity": "Complex",
                    "element_design": {
                        "ports": {
                            "needed": True,
                            "details": "需要输入端口接收传感器数据，输出端口发送控制命令"
                        },
                        "internal_behaviors": {
                            "needed": True,
                            "runnables": ["ControlAlgorithm"],
                            "events": ["10ms周期事件"]
                        }
                    }
                },
                {
                    "component_id": "comp_4",
                    "name": "MotorActuatorComponent",
                    "type": "SENSOR-ACTUATOR-SW-COMPONENT-TYPE",
                    "purpose": "执行电机控制命令",
                    "estimated_complexity": "Medium",
                    "element_design": {
                        "ports": {
                            "needed": True,
                            "details": "需要输入端口接收控制命令"
                        }
                    }
                }
            ],
            "interface_plan": [
                {
                    "interface_id": "intf_1",
                    "name": "SensorDataInterface",
                    "type": "SENDER-RECEIVER-INTERFACE",
                    "communication_pattern": "异步数据传输",
                    "connected_components": ["comp_1", "comp_2", "comp_3"]
                },
                {
                    "interface_id": "intf_2",
                    "name": "ControlCommandInterface",
                    "type": "SENDER-RECEIVER-INTERFACE",
                    "communication_pattern": "异步控制命令",
                    "connected_components": ["comp_3", "comp_4"]
                }
            ],
            "connection_topology": {
                "component_connections": "传感器组件->控制器组件->执行器组件",
                "data_flow_paths": "温度/转速数据->控制算法->PWM信号"
            },
            "architecture_rationale": {
                "design_decisions": "采用分层架构，符合AUTOSAR标准"
            }
        }

        mock_generate_schema.return_value = (
            mock_architecture,
            1000,  # input_tokens
            2000,  # output_tokens
            3000  # total_tokens
        )

        # 执行架构设计
        design, stats = self.round1_designer.design_architecture(
            user_requirements="设计一个电机控制系统",
            document_files=[req_file, arch_file]
        )

        # 验证设计结果
        self.assertIsNotNone(design)
        self.assertEqual(len(design.component_plan), 4)  # 4个组件
        self.assertEqual(len(design.interface_plan), 2)  # 2个接口

        # 验证组件类型
        component_names = [comp["name"] for comp in design.component_plan]
        self.assertIn("TemperatureSensorComponent", component_names)
        self.assertIn("MotorControllerComponent", component_names)

        # 验证统计信息
        self.assertEqual(stats["component_count"], 4)
        self.assertEqual(stats["interface_count"], 2)
        self.assertEqual(stats["documents_processed"], 2)

        # 验证element_design
        controller = next(c for c in design.component_plan
                          if c["name"] == "MotorControllerComponent")
        self.assertTrue(controller["element_design"]["ports"]["needed"])
        self.assertTrue(controller["element_design"]["internal_behaviors"]["needed"])

    def test_document_validation(self):
        """测试文档验证功能"""

        # 测试不存在的文件
        is_valid, error = self.document_processor.validate_file("/non/existent/file.pdf")
        self.assertFalse(is_valid)
        self.assertIn("不存在", error)

        # 测试不支持的格式
        invalid_file = self.test_data_dir / "test.xyz"
        invalid_file.write_text("test")
        is_valid, error = self.document_processor.validate_file(str(invalid_file))
        self.assertFalse(is_valid)
        self.assertIn("不支持", error)

        # 测试空文件
        empty_file = self.test_data_dir / "empty.txt"
        empty_file.write_text("")
        is_valid, error = self.document_processor.validate_file(str(empty_file))
        self.assertFalse(is_valid)
        self.assertIn("为空", error)

        # 测试有效文件
        valid_file = self.test_data_dir / "valid.txt"
        valid_file.write_text("valid content")
        is_valid, error = self.document_processor.validate_file(str(valid_file))
        self.assertTrue(is_valid)
        self.assertEqual(error, "")

    @patch('src.llm_generation.llm.gemini_client.GeminiClient.generate_with_schema')
    def test_round1_without_documents(self, mock_generate):
        """测试Round1不使用文档的情况"""

        # 模拟简单的单组件架构
        mock_architecture = {
            "system_analysis": {
                "functional_decomposition": "单一温度监控功能",
                "data_flow_analysis": "传感器->处理->输出"
            },
            "component_plan": [
                {
                    "component_id": "comp_1",
                    "name": "TemperatureMonitor",
                    "type": "APPLICATION-SW-COMPONENT-TYPE",
                    "purpose": "监控温度",
                    "element_design": {
                        "ports": {"needed": True}
                    }
                }
            ],
            "interface_plan": [
                {
                    "interface_id": "intf_1",
                    "name": "TempDataInterface",
                    "type": "SENDER-RECEIVER-INTERFACE",
                    "communication_pattern": "周期性数据"
                }
            ],
            "connection_topology": {
                "component_connections": "单组件系统",
                "data_flow_paths": "输入->处理->输出"
            },
            "architecture_rationale": {
                "design_decisions": "简单监控系统"
            }
        }

        mock_generate.return_value = (mock_architecture, 500, 1000, 1500)

        # 执行架构设计（无文档）
        design, stats = self.round1_designer.design_architecture(
            user_requirements="设计一个温度监控组件"
        )

        # 验证结果
        self.assertEqual(len(design.component_plan), 1)
        self.assertEqual(stats["documents_processed"], 0)

    @patch('google.generativeai.upload_file')
    def test_multiple_file_upload(self, mock_upload):
        """测试批量文档上传"""

        # 创建多个测试文件
        files = []
        for i in range(3):
            file_path = self.test_data_dir / f"doc_{i}.txt"
            file_path.write_text(f"Document {i} content")
            files.append(str(file_path))

        # 模拟上传
        mock_files = []
        for i, path in enumerate(files):
            mock_file = Mock()
            mock_file.name = f"file_{i}"
            mock_file.display_name = f"doc_{i}.txt"
            mock_file.state.name = "ACTIVE"
            mock_files.append(mock_file)

        mock_upload.side_effect = mock_files

        # 批量上传
        uploaded = self.document_processor.upload_multiple_files(files)

        # 验证
        self.assertEqual(len(uploaded), 3)
        self.assertEqual(mock_upload.call_count, 3)

        # 获取上传信息
        info = self.document_processor.get_uploaded_files_info()
        self.assertEqual(len(info), 3)


class TestRound1Output(unittest.TestCase):
    """Round1输出格式测试"""

    def test_architecture_design_structure(self):
        """测试架构设计输出结构"""

        # 期望的输出结构
        expected_structure = {
            "system_analysis": {
                "functional_decomposition": str,
                "data_flow_analysis": str,
                "timing_requirements": str,
                "scalability_considerations": str
            },
            "component_plan": [
                {
                    "component_id": str,
                    "name": str,
                    "type": str,
                    "purpose": str,
                    "element_design": {
                        "ports": {
                            "needed": bool,
                            "details": str
                        }
                    }
                }
            ],
            "interface_plan": [
                {
                    "interface_id": str,
                    "name": str,
                    "type": str,
                    "communication_pattern": str
                }
            ],
            "connection_topology": {
                "component_connections": str,
                "data_flow_paths": str
            },
            "architecture_rationale": {
                "design_decisions": str
            }
        }

        # 验证结构的函数
        def validate_structure(data: Dict, expected: Dict) -> bool:
            """递归验证数据结构"""
            for key, expected_type in expected.items():
                if key not in data:
                    print(f"Missing key: {key}")
                    return False

                if isinstance(expected_type, dict):
                    if not isinstance(data[key], dict):
                        print(f"Type mismatch for {key}: expected dict")
                        return False
                    if not validate_structure(data[key], expected_type):
                        return False

                elif isinstance(expected_type, list):
                    if not isinstance(data[key], list):
                        print(f"Type mismatch for {key}: expected list")
                        return False
                    # 验证列表中的元素结构
                    if len(expected_type) > 0 and len(data[key]) > 0:
                        for item in data[key]:
                            if not validate_structure(item, expected_type[0]):
                                return False

            return True

        # 创建测试数据
        test_output = {
            "system_analysis": {
                "functional_decomposition": "测试功能分解",
                "data_flow_analysis": "测试数据流",
                "timing_requirements": "10ms",
                "scalability_considerations": "可扩展"
            },
            "component_plan": [
                {
                    "component_id": "comp_1",
                    "name": "TestComponent",
                    "type": "APPLICATION-SW-COMPONENT-TYPE",
                    "purpose": "测试目的",
                    "element_design": {
                        "ports": {
                            "needed": True,
                            "details": "需要输入输出端口"
                        }
                    }
                }
            ],
            "interface_plan": [
                {
                    "interface_id": "intf_1",
                    "name": "TestInterface",
                    "type": "SENDER-RECEIVER-INTERFACE",
                    "communication_pattern": "异步"
                }
            ],
            "connection_topology": {
                "component_connections": "A->B",
                "data_flow_paths": "输入->处理->输出"
            },
            "architecture_rationale": {
                "design_decisions": "采用标准架构"
            }
        }

        # 验证
        self.assertTrue(validate_structure(test_output, expected_structure))


class TestRound1Integration(unittest.TestCase):
    """Round1集成测试"""

    @patch('src.llm_generation.llm.gemini_client.GeminiClient.generate_with_schema')
    def test_complete_flow_with_feedback(self, mock_generate):
        """测试完整流程包括用户反馈"""

        # 第一次生成
        first_design = {
            "system_analysis": {
                "functional_decomposition": "初始设计",
                "data_flow_analysis": "简单数据流"
            },
            "component_plan": [
                {
                    "component_id": "comp_1",
                    "name": "InitialComponent",
                    "type": "APPLICATION-SW-COMPONENT-TYPE",
                    "purpose": "初始目的",
                    "element_design": {"ports": {"needed": True}}
                }
            ],
            "interface_plan": [],
            "connection_topology": {
                "component_connections": "无",
                "data_flow_paths": "无"
            },
            "architecture_rationale": {
                "design_decisions": "初始决策"
            }
        }

        # 修改后的设计
        revised_design = {
            **first_design,
            "component_plan": [
                {
                    "component_id": "comp_1",
                    "name": "ImprovedComponent",
                    "type": "APPLICATION-SW-COMPONENT-TYPE",
                    "purpose": "改进的目的",
                    "element_design": {
                        "ports": {"needed": True},
                        "internal_behaviors": {"needed": True}
                    }
                },
                {
                    "component_id": "comp_2",
                    "name": "AdditionalComponent",
                    "type": "SENSOR-ACTUATOR-SW-COMPONENT-TYPE",
                    "purpose": "新增组件",
                    "element_design": {"ports": {"needed": True}}
                }
            ]
        }

        # 模拟两次调用
        mock_generate.side_effect = [
            (first_design, 500, 1000, 1500),
            (revised_design, 600, 1200, 1800)
        ]

        designer = Round1Designer()

        # 第一次设计
        design1, stats1 = designer.design_architecture("初始需求")
        self.assertEqual(len(design1.component_plan), 1)

        # 模拟用户反馈后的第二次设计
        design2, stats2 = designer.design_architecture(
            "初始需求",
            design_context="用户要求添加一个传感器组件"
        )
        self.assertEqual(len(design2.component_plan), 2)
        self.assertEqual(mock_generate.call_count, 2)


if __name__ == '__main__':
    # 创建测试套件
    suite = unittest.TestSuite()

    # 添加测试
    suite.addTest(unittest.makeSuite(TestRound1WithDocuments))
    suite.addTest(unittest.makeSuite(TestRound1Output))
    suite.addTest(unittest.makeSuite(TestRound1Integration))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 输出测试报告
    print("\n" + "=" * 50)
    print("测试报告汇总")
    print("=" * 50)
    print(f"运行测试: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")

    # 如果有失败或错误，显示详情
    if result.failures:
        print("\n失败的测试:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback[:100]}...")

    if result.errors:
        print("\n错误的测试:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback[:100]}...")