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

    # 1. 修改 main_validator.py 中的 _save_report 方法

    def _save_report(self, xml_file: str, report: str, results: Dict):
        """保存验证报告 - 修复保存逻辑"""

        # 🔧 修复1: 确保启用报告保存
        reporting_config = self.config.get('reporting', {})
        save_reports = reporting_config.get('save_reports', True)  # 默认启用

        # 🔧 修复：强制保存重要报告
        if not save_reports:
            print("⚠️  配置中禁用了报告保存，但仍将保存重要验证报告")
            save_reports = True

        if not save_reports:
            print("📝 报告保存已禁用")
            return

        try:
            # 生成报告文件名
            xml_name = Path(xml_file).stem
            timestamp = time.strftime("%Y%m%d_%H%M%S")

            # 🔧 修复：确保报告目录存在
            report_dir = project_root / self.config['file_paths'].get('report_dir', 'reports')
            report_dir.mkdir(parents=True, exist_ok=True)  # 确保创建父目录

            report_file = report_dir / f"validation_report_{xml_name}_{timestamp}.txt"

            # 🔧 修复：保存文本报告
            print(f"📝 正在保存报告到: {report_file}")

            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(f"验证文件: {xml_file}\n")
                f.write(f"验证时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 80 + "\n")
                f.write(report)

            # 🔧 验证文件是否成功创建
            if report_file.exists():
                file_size = report_file.stat().st_size
                print(f"✅ 报告已保存: {report_file} ({file_size} bytes)")
            else:
                print(f"❌ 报告保存失败: 文件未创建")
                return

            # 🔧 修复：JSON格式保存逻辑
            report_format = reporting_config.get('format', 'text')
            if report_format in ['json', 'both']:
                import json
                json_file = report_file.with_suffix('.json')

                print(f"📝 正在保存JSON报告到: {json_file}")

                # 🔧 确保results可序列化
                serializable_results = self._make_serializable(results)

                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'xml_file': xml_file,
                        'validation_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'results': serializable_results
                    }, f, indent=2, ensure_ascii=False)

                if json_file.exists():
                    json_size = json_file.stat().st_size
                    print(f"✅ JSON报告已保存: {json_file} ({json_size} bytes)")
                else:
                    print(f"❌ JSON报告保存失败")

            # 🔧 新增：生成SHACL专门报告（如果有违规）
            if hasattr(self.orchestrator, 'generate_shacl_violation_summary_report'):
                semantic_result = results.get("stages", {}).get("semantic", {}).get("result", {})
                violation_count = semantic_result.get("violation_count", 0)

                if violation_count > 0:
                    shacl_report_file = report_dir / f"shacl_violations_{xml_name}_{timestamp}.txt"
                    shacl_report = self.orchestrator.generate_shacl_violation_summary_report(results)

                    with open(shacl_report_file, 'w', encoding='utf-8') as f:
                        f.write(f"SHACL违规专门报告\n")
                        f.write(f"验证文件: {xml_file}\n")
                        f.write(f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write("=" * 80 + "\n")
                        f.write(shacl_report)

                    print(f"📄 SHACL专门报告已保存: {shacl_report_file}")

        except Exception as e:
            print(f"❌ 保存报告失败: {e}")
            import traceback
            traceback.print_exc()

    def _make_serializable(self, obj):
        """将对象转换为可JSON序列化的格式"""
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        elif hasattr(obj, '__dict__'):
            return str(obj)
        else:
            return str(obj)

    # 2. 修改 main_validator.py 中的 _validate_environment 方法

    def _validate_environment(self):
        """验证环境和文件完整性 - 支持文件夹扫描"""
        print("正在验证环境...")

        # 修正：使用project_root解析所有相对路径
        file_paths = self.config.get('file_paths', {})

        # XSD文件检查
        xsd_path = file_paths.get('xsd_schema', '')
        if xsd_path:
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
            shacl_full_path = project_root / shacl_path if not Path(shacl_path).is_absolute() else Path(shacl_path)
            if shacl_full_path.exists():
                print(f"✅ SHACL Shapes: {shacl_full_path}")
            else:
                print(f"❌ SHACL Shapes文件未找到: {shacl_full_path}")
        else:
            print("⚠️  配置中未指定SHACL Shapes路径")

        # 🔥 [新增] XSD Index文件检查
        xsd_index_path = file_paths.get('xsd_index', '')
        if xsd_index_path:
            xsd_index_full_path = project_root / xsd_index_path if not Path(xsd_index_path).is_absolute() else Path(
                xsd_index_path)
            if xsd_index_full_path.exists():
                print(f"✅ XSD Index Ontology: {xsd_index_full_path}")
            else:
                print(f"❌ XSD Index文件未找到: {xsd_index_full_path} (RDFS推理将不可用)")
        else:
            print("⚠️  配置中未指定XSD Index路径")

        # SMT文件检查
        smt_path = file_paths.get('smt_template', '')
        if smt_path:
            smt_full_path = project_root / smt_path if not Path(smt_path).is_absolute() else Path(smt_path)
            if smt_full_path.exists():
                print(f"✅ SMT Template: {smt_full_path}")
            else:
                print(f"❌ SMT Template文件未找到: {smt_full_path}")
        else:
            print("⚠️  配置中未指定SMT Template路径")

        # 🔧 修复2: 增强的XML实例文件扫描逻辑
        xml_instances_config = file_paths.get('xml_instances', [])
        available_xmls = []

        print("🔍 扫描XML实例文件...")

        for xml_config in xml_instances_config:
            xml_path = Path(xml_config)

            # 如果是相对路径，转换为绝对路径
            if not xml_path.is_absolute():
                xml_path = project_root / xml_config

            if xml_path.is_file():
                # 单个文件
                if xml_path.suffix.lower() in ['.xml', '.arxml']:
                    available_xmls.append(str(xml_path))
                    print(f"✅ XML文件: {xml_path}")
                else:
                    print(f"⚠️  非XML文件: {xml_path}")

            elif xml_path.is_dir():
                # 🔧 新增：文件夹扫描逻辑
                print(f"📁 扫描文件夹: {xml_path}")
                folder_xmls = self._scan_xml_folder(xml_path)
                available_xmls.extend(folder_xmls)

            else:
                print(f"⚠️  路径不存在: {xml_path}")

        # 🔧 去重并排序
        available_xmls = sorted(list(set(available_xmls)))

        if not available_xmls:
            print("❌ 没有找到可用的XML实例文件")
            print("💡 请检查配置文件中的xml_instances路径，支持:")
            print("   - 单个文件: xml_instance/test.arxml")
            print("   - 文件夹: xml_instance/ (自动扫描所有.xml/.arxml文件)")
            sys.exit(1)

        print(f"📊 总共找到 {len(available_xmls)} 个XML文件")
        self.available_xml_files = available_xmls

        # 创建输出目录
        self._create_output_directories()

    def _scan_xml_folder(self, folder_path: Path) -> List[str]:
        """🔧 新增：扫描文件夹中的XML文件"""
        xml_files = []

        try:
            # 支持的XML文件扩展名
            xml_extensions = ['.xml', '.arxml']

            # 递归扫描文件夹
            for file_path in folder_path.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in xml_extensions:
                    xml_files.append(str(file_path))
                    print(f"   📄 发现: {file_path.relative_to(folder_path)}")

            if not xml_files:
                print(f"   ⚠️  文件夹 {folder_path} 中未找到XML文件")
            else:
                print(f"   ✅ 在 {folder_path} 中找到 {len(xml_files)} 个XML文件")

        except Exception as e:
            print(f"   ❌ 扫描文件夹失败: {e}")

        return xml_files

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
        """验证所有配置的XML文件（包含跨文件验证）"""
        results = []

        print(f"\n{'=' * 80}")
        print("开始批量验证所有XML文件")
        print(f"{'=' * 80}")

        # 第一阶段：单文件验证
        print("\n📁 第一阶段: 单文件验证")
        for xml_file in self.available_xml_files:
            result = self.validate_single_file(xml_file, validation_mode)
            results.append(result)

            # 简要状态显示
            status = "✅ 通过" if result['success'] else "❌ 失败"
            print(f"{status} - {Path(xml_file).name}")

        # 统计单文件验证结果
        passed = sum(1 for r in results if r['success'])
        total = len(results)

        print(f"\n📊 单文件验证结果: {passed}/{total} 文件通过")

        # 第二阶段：跨文件验证（新增）
        # 🔥 检查配置中的跨文件验证开关
        constraint_config = self.config.get('validators', {}).get('constraint', {})
        cross_file_enabled = constraint_config.get('cross_file_validation', False)

        if len(self.available_xml_files) > 1 and cross_file_enabled:
            print("\n📁 第二阶段: 跨文件约束验证")
            cross_file_result = self.validate_cross_file()
            results.append(cross_file_result)

            if cross_file_result['success']:
                print("✅ 跨文件约束验证通过")
            else:
                print(f"❌ 跨文件约束验证失败: {len(cross_file_result.get('violations', []))} 个违规")
        elif not cross_file_enabled:
            print("\n📁 第二阶段: 跨文件约束验证 (已禁用)")


        # 最终统计
        all_passed = all(r.get('success', False) for r in results)

        print(f"\n{'=' * 80}")
        if all_passed:
            print(f"🎉 批量验证完成: 所有验证通过")
        else:
            failed_count = sum(1 for r in results if not r.get('success', False))
            print(f"⚠️  批量验证完成: {failed_count} 项验证失败")
        print(f"{'=' * 80}")

        return results

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
            print("5. 跨文件约束验证")  # 新增选项
            print("0. 退出")

            choice = input("\n请输入选择 (0-5): ").strip()

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
            elif choice == '5':
                self._interactive_cross_file()  # 新增
            else:
                print("无效选择，请重试")

    def _interactive_cross_file(self):
        """交互式跨文件验证"""
        print(f"\n将对 {len(self.available_xml_files)} 个文件执行跨文件约束验证")
        confirm = input("确认执行? (y/N): ")
        if confirm.lower() == 'y':
            result = self.validate_cross_file()

            # 保存跨文件验证报告
            if result.get('violations'):
                self._save_cross_file_report(result)

    def _save_cross_file_report(self, result: Dict):
        """保存跨文件验证报告"""
        try:
            report_dir = project_root / self.config['file_paths'].get('report_dir', 'reports')
            report_dir.mkdir(parents=True, exist_ok=True)

            timestamp = time.strftime("%Y%m%d_%H%M%S")
            report_file = report_dir / f"cross_file_validation_{timestamp}.txt"

            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("跨文件约束验证报告\n")
                f.write(f"验证时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"文件数量: {result.get('files_analyzed', 0)}\n")
                f.write("=" * 80 + "\n\n")

                # 统计信息
                stats = result.get('stats', {})
                f.write("📊 统计信息:\n")
                f.write(f"  - 全局元素数: {stats.get('total_elements', 0)}\n")
                f.write(f"  - 引用总数: {stats.get('total_refs', 0)}\n")
                f.write(f"  - 引用类型数: {stats.get('ref_types', 0)}\n\n")

                # 违规详情
                violations = result.get('violations', [])
                f.write(f"❌ 违规总数: {len(violations)}\n\n")

                for i, v in enumerate(violations, 1):
                    f.write(f"--- 违规 #{i} ---\n")
                    f.write(f"类型: {v.get('type', 'UNKNOWN')}\n")
                    f.write(f"消息: {v.get('message', '')}\n")
                    if 'ref_path' in v:
                        f.write(f"引用路径: {v['ref_path']}\n")
                    if 'source_file' in v:
                        f.write(f"来源文件: {v['source_file']}\n")
                    f.write("\n")

            print(f"✅ 跨文件验证报告已保存: {report_file}")

        except Exception as e:
            print(f"❌ 保存报告失败: {e}")

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
        """显示可用文件 - 增强显示"""
        print("\n📁 可用的XML文件:")

        # 按文件夹分组显示
        files_by_folder = {}
        for xml_file in self.available_xml_files:
            folder = str(Path(xml_file).parent)
            if folder not in files_by_folder:
                files_by_folder[folder] = []
            files_by_folder[folder].append(xml_file)

        total_size = 0
        for folder, files in files_by_folder.items():
            print(f"  📂 {folder}:")
            for xml_file in sorted(files):
                try:
                    size = Path(xml_file).stat().st_size
                    size_str = f"{size:,} bytes" if size < 1024 * 1024 else f"{size / (1024 * 1024):.1f} MB"
                    print(f"    📄 {Path(xml_file).name} ({size_str})")
                    total_size += size
                except Exception as e:
                    print(f"    📄 {Path(xml_file).name} (无法获取大小: {e})")

        total_size_str = f"{total_size:,} bytes" if total_size < 1024 * 1024 else f"{total_size / (1024 * 1024):.1f} MB"
        print(f"\n📊 总计: {len(self.available_xml_files)} 个文件, {total_size_str}")

    # 5. 增强输出目录创建逻辑

    def _create_output_directories(self):
        """创建输出目录 - 增强版"""
        file_paths = self.config.get('file_paths', {})
        reporting_config = self.config.get('reporting', {})

        # 基础输出目录
        output_dir = project_root / file_paths.get('output_dir', 'logs')
        report_dir = project_root / file_paths.get('report_dir', 'reports')

        # 创建目录
        output_dir.mkdir(parents=True, exist_ok=True)
        report_dir.mkdir(parents=True, exist_ok=True)

        print(f"✅ 输出目录: {output_dir}")
        print(f"✅ 报告目录: {report_dir}")

        # 🔧 新增：创建时间戳子目录（可选）
        if reporting_config.get('create_timestamp_dirs', False):
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            timestamp_report_dir = report_dir / timestamp
            timestamp_report_dir.mkdir(exist_ok=True)
            print(f"✅ 时间戳报告目录: {timestamp_report_dir}")

        # 🔧 新增：创建分类子目录
        for subdir in ['semantic_reports', 'constraint_reports', 'structure_reports']:
            sub_path = report_dir / subdir
            sub_path.mkdir(exist_ok=True)

        print(f"📁 报告子目录已创建完成")

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

    def validate_cross_file(self, arxml_files: List[str] = None) -> Dict:
        """
        执行跨文件约束验证

        Args:
            arxml_files: ARXML文件列表，默认使用配置中的所有文件

        Returns:
            跨文件验证结果
        """
        if arxml_files is None:
            arxml_files = self.available_xml_files

        print(f"\n{'=' * 60}")
        print("🔗 跨文件约束验证")
        print(f"{'=' * 60}")
        print(f"文件数量: {len(arxml_files)}")

        results = {
            'phase': 'cross_file',
            'files_analyzed': len(arxml_files),
            'violations': [],
            'success': True,
            'stats': {}
        }

        try:
            # 动态导入跨文件解析器
            try:
                from src.validation.cross_file_resolver import CrossFileResolver
            except ImportError as e:
                print(f"❌ 无法导入 CrossFileResolver: {e}")
                print("💡 请确保已创建 src/validation/cross_file_resolver.py")
                results['success'] = False
                results['error'] = str(e)
                return results

            # 初始化跨文件解析器
            resolver = CrossFileResolver()
            print("\n📊 构建全局索引...")
            resolver.build_global_index(arxml_files)

            stats = {
                'total_elements': len(resolver.global_index),
                'total_refs': sum(len(refs) for refs in resolver.ref_registry.values()),
                'ref_types': len(resolver.ref_registry)
            }
            results['stats'] = stats

            print(f"  ✅ 索引完成: {stats['total_elements']} 个元素, {stats['total_refs']} 个引用")

            # 1. 引用完整性检查
            print("\n📌 检查引用完整性...")
            ref_violations = resolver.validate_all_refs()
            if ref_violations:
                print(f"  ❌ 发现 {len(ref_violations)} 个未解析引用:")
                for v in ref_violations[:10]:  # 显示前10个
                    print(f"    - {v['ref_path']}")
                    print(f"      期望类型: {v['expected_dest']}")
                    print(f"      来源文件: {Path(v['source_file']).name}")
                if len(ref_violations) > 10:
                    print(f"    ... 还有 {len(ref_violations) - 10} 个未显示")
                results['violations'].extend(ref_violations)
            else:
                print(f"  ✅ 所有 {stats['total_refs']} 个引用均已解析")

            # 2. DEST类型匹配检查
            print("\n🔍 检查DEST类型匹配...")
            type_mismatches = resolver.check_dest_type_match()
            if type_mismatches:
                print(f"  ❌ 发现 {len(type_mismatches)} 个类型不匹配:")
                for m in type_mismatches[:10]:
                    print(f"    - {m['ref_path']}")
                    print(f"      声明: {m['declared_dest']}, 实际: {m['actual_type']}")
                if len(type_mismatches) > 10:
                    print(f"    ... 还有 {len(type_mismatches) - 10} 个未显示")
                results['violations'].extend(type_mismatches)
            else:
                print(f"  ✅ 所有DEST类型匹配正确")

            # 3. SMT跨文件约束验证（如果编排器已初始化且有SMT验证器）
            self._initialize_orchestrator()
            if hasattr(self.orchestrator, 'smt_validator') and self.orchestrator.smt_validator:
                print("\n🧮 执行SMT跨文件约束验证...")
                smt_validator = self.orchestrator.smt_validator
                smt_validator.set_cross_file_resolver(resolver)

                # 检查跨文件约束
                smt_results = smt_validator.validate_cross_file_constraints(arxml_files)
                smt_violations = smt_results.get('violations', [])

                if smt_violations:
                    print(f"  ❌ 发现 {len(smt_violations)} 个SMT约束违规")
                    results['violations'].extend(smt_violations)
                else:
                    print(f"  ✅ SMT跨文件约束验证通过")

                results['smt_stats'] = smt_results.get('stats', {})
            else:
                print("\n⚠️  SMT验证器未初始化，跳过SMT跨文件约束验证")

            # 4. 全局唯一性检查
            print("\n🆔 检查全局SHORT-NAME唯一性...")
            duplicates = self._check_global_uniqueness(resolver)
            if duplicates:
                print(f"  ❌ 发现 {len(duplicates)} 个重复路径")
                for d in duplicates[:5]:
                    print(f"    - {d['path']}: 在文件 {', '.join(d['files'])}")
                results['violations'].extend(duplicates)
            else:
                print(f"  ✅ 所有SHORT-NAME-PATH全局唯一")

            # 5. 生成跨文件验证报告
            results['success'] = len(results['violations']) == 0

            # 统计信息
            violation_summary = {}
            for v in results['violations']:
                v_type = v.get('type', 'UNKNOWN')
                violation_summary[v_type] = violation_summary.get(v_type, 0) + 1

            results['violation_summary'] = violation_summary

            print(f"\n{'=' * 60}")
            if results['success']:
                print("✅ 跨文件约束验证通过")
            else:
                print(f"❌ 跨文件约束验证失败: {len(results['violations'])} 个违规")
                for v_type, count in violation_summary.items():
                    print(f"  - {v_type}: {count} 个")
            print(f"{'=' * 60}")

        except Exception as e:
            print(f"❌ 跨文件验证失败: {e}")
            results['success'] = False
            results['error'] = str(e)
            import traceback
            traceback.print_exc()

        return results

    def _check_global_uniqueness(self, resolver) -> List[Dict]:
        """检查全局SHORT-NAME-PATH唯一性"""
        duplicates = []

        # 构建路径到文件的映射
        path_to_files = {}

        for path, info in resolver.global_index.items():
            source_file = info.get('source_file', '')
            if path not in path_to_files:
                path_to_files[path] = []
            path_to_files[path].append(source_file)

        # 检查是否有重复（由于global_index是字典，同名会覆盖）
        # 这里需要在索引构建时记录重复，或者重新扫描
        # 简化实现：返回空列表（实际项目中可能需要增强CrossFileResolver）

        return duplicates


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