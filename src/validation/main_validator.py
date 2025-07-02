# src/validation/main_validator.py
"""
AUTOSAR XML验证系统主入口
支持从配置文件读取所有路径，避免硬编码
"""
import os
import sys
from pathlib import Path
import yaml
from typing import Dict, List, Optional
import time

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class AutosarValidator:
    """AUTOSAR XML验证系统主类"""

    def __init__(self, config_path: str = "config/main_config.yaml"):
        """初始化验证系统"""
        self.config_path = config_path
        self.config = self._load_config()
        self.orchestrator = None

        # 验证配置和环境
        self._validate_environment()

    def _load_config(self) -> Dict:
        """加载配置文件"""
        try:
            config_file = project_root / self.config_path
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            print(f"✅ 配置文件加载成功: {config_file}")
            return config
        except FileNotFoundError:
            print(f"❌ 配置文件未找到: {self.config_path}")
            print("请确保配置文件存在或运行 setup_validation.py 创建默认配置")
            sys.exit(1)
        except Exception as e:
            print(f"❌ 配置文件加载失败: {e}")
            sys.exit(1)

    def _validate_environment(self):
        """验证环境和文件完整性"""
        print("正在验证环境...")

        # 修正：使用project_root解析所有相对路径
        file_paths = self.config.get('file_paths', {})

        # XSD文件检查
        xsd_path = file_paths.get('xsd_schema', '')
        if xsd_path:
            # 修正：正确处理相对路径
            xsd_full_path = project_root / xsd_path if not Path(xsd_path).is_absolute() else Path(xsd_path)
            if xsd_full_path.exists():
                print(f"✅ XSD Schema: {xsd_full_path}")
            else:
                print(f"❌ XSD Schema文件未找到: {xsd_full_path}")
        else:
            print("⚠️  配置中未指定XSD Schema路径")

        # SHACL文件检查
        shacl_path = file_paths.get('shacl_shapes', '')
        if shacl_path:
            # 修正：正确处理相对路径
            shacl_full_path = project_root / shacl_path if not Path(shacl_path).is_absolute() else Path(shacl_path)
            if shacl_full_path.exists():
                print(f"✅ SHACL Shapes: {shacl_full_path}")
            else:
                print(f"❌ SHACL Shapes文件未找到: {shacl_full_path}")
        else:
            print("⚠️  配置中未指定SHACL Shapes路径")

        # SMT文件检查
        smt_path = file_paths.get('smt_template', '')
        if smt_path:
            # 修正：正确处理相对路径
            smt_full_path = project_root / smt_path if not Path(smt_path).is_absolute() else Path(smt_path)
            if smt_full_path.exists():
                print(f"✅ SMT Template: {smt_full_path}")
            else:
                print(f"❌ SMT Template文件未找到: {smt_full_path}")
        else:
            print("⚠️  配置中未指定SMT Template路径")

        # 检查XML实例文件
        xml_instances = file_paths.get('xml_instances', [])
        available_xmls = []
        for xml_file in xml_instances:
            # 修正：正确处理相对路径
            xml_full_path = project_root / xml_file if not Path(xml_file).is_absolute() else Path(xml_file)
            if xml_full_path.exists():
                available_xmls.append(str(xml_full_path))
                print(f"✅ XML实例: {xml_full_path}")
            else:
                print(f"⚠️  XML实例未找到: {xml_full_path}")

        if not available_xmls:
            print("❌ 没有找到可用的XML实例文件")
            sys.exit(1)

        self.available_xml_files = available_xmls
        # 创建输出目录
        self._create_output_directories()

    def _create_output_directories(self):
        """创建输出目录"""
        file_paths = self.config.get('file_paths', {})

        output_dir = project_root / file_paths.get('output_dir', 'logs')
        report_dir = project_root / file_paths.get('report_dir', 'reports')

        output_dir.mkdir(exist_ok=True)
        report_dir.mkdir(exist_ok=True)

        print(f"✅ 输出目录: {output_dir}")
        print(f"✅ 报告目录: {report_dir}")

    def _initialize_orchestrator(self):
        """初始化验证编排器"""
        if self.orchestrator is None:
            try:
                from .orchestrator.config_driven_orchestrator import ConfigDrivenOrchestrator

                # 修正：直接传递完整配置，让编排器自己处理路径解析
                orchestrator_config = {
                    'validators': self.config.get('validators', {}),
                    'file_paths': self.config.get('file_paths', {}),  # 传递完整file_paths配置
                    'project_root': str(project_root)  # 传递项目根目录
                }

                self.orchestrator = ConfigDrivenOrchestrator(orchestrator_config)
                print("✅ 验证编排器初始化成功")

            except Exception as e:
                print(f"❌ 验证编排器初始化失败: {e}")
                raise

    def validate_single_file(self, xml_file: str, validation_mode: str = None) -> Dict:
        """验证单个XML文件 - 增强错误处理"""
        if validation_mode is None:
            validation_mode = self.config.get('default_mode', 'full')

        print(f"\n{'=' * 60}")
        print(f"验证文件: {xml_file}")
        print(f"验证模式: {validation_mode}")
        print(f"{'=' * 60}")

        # 读取XML内容
        try:
            with open(xml_file, 'r', encoding='utf-8') as f:
                xml_content = f.read()
        except Exception as e:
            return {
                'file': xml_file,
                'success': False,
                'error': f"读取文件失败: {e}"
            }

        # 初始化编排器
        try:
            self._initialize_orchestrator()
        except Exception as e:
            return {
                'file': xml_file,
                'success': False,
                'error': f"初始化编排器失败: {e}"
            }

        # 执行验证
        try:
            # 根据验证模式确定验证级别
            validation_modes = self.config.get('validation_modes', {})
            validation_stages = validation_modes.get(validation_mode, ['structure', 'semantic', 'constraint'])

            # 修复：使用正确的方法名
            if hasattr(self.orchestrator, 'execute_full_validation'):
                validation_level = validation_mode if validation_mode in ['structure', 'semantic',
                                                                          'constraint'] else "full"
                results = self.orchestrator.execute_full_validation(xml_content, validation_level=validation_level)
            else:
                # 使用新的方法
                results = self.orchestrator.execute_validation(xml_content, validation_stages)

            # 修复：确保results有正确的结构
            if not isinstance(results, dict):
                results = {'overall_valid': False, 'error': 'Invalid validation results'}

            # 生成报告
            if hasattr(self.orchestrator, 'generate_validation_report'):
                report = self.orchestrator.generate_validation_report(results)
            else:
                report = f"Validation completed. Overall valid: {results.get('overall_valid', False)}"

            # 保存报告
            self._save_report(xml_file, report, results)

            # 显示结果
            if self.config.get('reporting', {}).get('console_output', True):
                print(report)

            return {
                'file': xml_file,
                'success': results.get('overall_valid', False),
                'results': results,
                'report': report
            }

        except Exception as e:
            error_msg = f"验证过程出错: {e}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            return {
                'file': xml_file,
                'success': False,
                'error': error_msg
            }

    def validate_all_files(self, validation_mode: str = None) -> List[Dict]:
        """验证所有配置的XML文件"""
        results = []

        print(f"\n{'=' * 80}")
        print("开始批量验证所有XML文件")
        print(f"{'=' * 80}")

        for xml_file in self.available_xml_files:
            result = self.validate_single_file(xml_file, validation_mode)
            results.append(result)

            # 简要状态显示
            status = "✅ 通过" if result['success'] else "❌ 失败"
            print(f"{status} - {Path(xml_file).name}")

        # 统计结果
        passed = sum(1 for r in results if r['success'])
        total = len(results)

        print(f"\n{'=' * 80}")
        print(f"批量验证完成: {passed}/{total} 文件通过验证")
        print(f"{'=' * 80}")

        return results

    def _save_report(self, xml_file: str, report: str, results: Dict):
        """保存验证报告"""
        if not self.config.get('reporting', {}).get('save_reports', True):
            return

        try:
            # 生成报告文件名
            xml_name = Path(xml_file).stem
            timestamp = time.strftime("%Y%m%d_%H%M%S")

            report_dir = project_root / self.config['file_paths'].get('report_dir', 'reports')
            report_file = report_dir / f"validation_report_{xml_name}_{timestamp}.txt"

            # 保存文本报告
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(f"验证文件: {xml_file}\n")
                f.write(f"验证时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 80 + "\n")
                f.write(report)

            print(f"📄 报告已保存: {report_file}")

            # 如果配置了JSON格式，也保存JSON
            if self.config.get('reporting', {}).get('format') == 'json':
                import json
                json_file = report_file.with_suffix('.json')
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)
                print(f"📄 JSON报告已保存: {json_file}")

        except Exception as e:
            print(f"⚠️  保存报告失败: {e}")

    def run_interactive(self):
        """交互式运行模式"""
        print("\n" + "=" * 80)
        print("AUTOSAR XML验证系统 - 交互模式")
        print("=" * 80)

        while True:
            print("\n请选择操作:")
            print("1. 验证单个文件")
            print("2. 验证所有文件")
            print("3. 查看可用文件")
            print("4. 更改验证模式")
            print("0. 退出")

            choice = input("\n请输入选择 (0-4): ").strip()

            if choice == '0':
                print("退出验证系统")
                break
            elif choice == '1':
                self._interactive_single_file()
            elif choice == '2':
                self._interactive_all_files()
            elif choice == '3':
                self._show_available_files()
            elif choice == '4':
                self._change_validation_mode()
            else:
                print("无效选择，请重试")

    def _interactive_single_file(self):
        """交互式单文件验证"""
        print("\n可用的XML文件:")
        for i, xml_file in enumerate(self.available_xml_files, 1):
            print(f"{i}. {Path(xml_file).name}")

        try:
            choice = int(input("\n请选择文件序号: ")) - 1
            if 0 <= choice < len(self.available_xml_files):
                xml_file = self.available_xml_files[choice]
                self.validate_single_file(xml_file)
            else:
                print("无效的文件序号")
        except ValueError:
            print("请输入有效的数字")

    def _interactive_all_files(self):
        """交互式全文件验证"""
        confirm = input(f"\n确认验证所有 {len(self.available_xml_files)} 个文件? (y/N): ")
        if confirm.lower() == 'y':
            self.validate_all_files()

    def _show_available_files(self):
        """显示可用文件"""
        print("\n可用的XML文件:")
        for xml_file in self.available_xml_files:
            size = Path(xml_file).stat().st_size
            print(f"  📄 {xml_file} ({size} bytes)")

    def _change_validation_mode(self):
        """更改验证模式"""
        modes = self.config.get('validation_modes', {})
        current_mode = self.config.get('default_mode', 'full')

        print(f"\n当前验证模式: {current_mode}")
        print("可用的验证模式:")
        for mode, stages in modes.items():
            print(f"  {mode}: {', '.join(stages)}")

        new_mode = input("\n请输入新的验证模式: ").strip()
        if new_mode in modes:
            self.config['default_mode'] = new_mode
            print(f"✅ 验证模式已更改为: {new_mode}")
        else:
            print("无效的验证模式")


def main():
    """主函数 - 支持命令行参数"""
    import argparse

    parser = argparse.ArgumentParser(description='AUTOSAR XML验证系统')
    parser.add_argument('--config', default='config/main_config.yaml',
                        help='配置文件路径')
    parser.add_argument('--mode', choices=['quick', 'standard', 'full'],
                        help='验证模式')
    parser.add_argument('--file', help='指定要验证的XML文件')
    parser.add_argument('--all', action='store_true',
                        help='验证所有配置的文件')
    parser.add_argument('--interactive', action='store_true',
                        help='进入交互模式')

    args = parser.parse_args()

    try:
        # 初始化验证器
        validator = AutosarValidator(args.config)

        if args.interactive:
            validator.run_interactive()
        elif args.file:
            # 验证指定文件
            if Path(args.file).exists():
                result = validator.validate_single_file(args.file, args.mode)
                sys.exit(0 if result['success'] else 1)
            else:
                print(f"❌ 文件不存在: {args.file}")
                sys.exit(1)
        elif args.all:
            # 验证所有文件
            results = validator.validate_all_files(args.mode)
            success_count = sum(1 for r in results if r['success'])
            sys.exit(0 if success_count == len(results) else 1)
        else:
            # 默认交互模式
            validator.run_interactive()

    except KeyboardInterrupt:
        print("\n\n验证被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 验证系统错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()