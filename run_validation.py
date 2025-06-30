# run_validation.py
"""
AUTOSAR XML验证系统 - 一键运行脚本
适用于PyCharm环境，不包含自动包安装
"""
import os
import sys
from pathlib import Path
import yaml


def check_project_structure():
    """检查项目结构完整性"""
    print("🔍 检查项目结构...")

    required_dirs = [
        "config",
        "src/validation",
        "src/constraint_graph/artifacts",
        "xml_instance"
    ]

    missing_dirs = []
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            missing_dirs.append(dir_path)
        else:
            print(f"✅ {dir_path}")

    if missing_dirs:
        print(f"❌ 缺少目录: {', '.join(missing_dirs)}")
        return False

    print("✅ 项目结构检查完成")
    return True


def check_dependencies():
    """检查Python依赖包"""
    print("\n📦 检查依赖包...")

    required_packages = [
        ('xmlschema', 'xmlschema'),
        ('rdflib', 'rdflib'),
        ('pyshacl', 'pyshacl'),
        ('pyyaml', 'yaml')
    ]

    optional_packages = [
        ('z3-solver', 'z3')
    ]

    missing_required = []
    missing_optional = []

    # 检查必需包
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"✅ {package_name}")
        except ImportError:
            missing_required.append(package_name)
            print(f"❌ {package_name} (必需)")

    # 检查可选包
    for package_name, import_name in optional_packages:
        try:
            __import__(import_name)
            print(f"✅ {package_name} (可选)")
        except ImportError:
            missing_optional.append(package_name)
            print(f"⚠️  {package_name} (可选 - SMT验证需要)")

    if missing_required:
        print(f"\n❌ 缺少必需包: {', '.join(missing_required)}")
        print("请在PyCharm中安装:")
        print("File -> Settings -> Project -> Python Interpreter -> '+' 添加包")
        return False

    if missing_optional:
        print(f"\n⚠️  缺少可选包: {', '.join(missing_optional)}")
        print("SMT约束验证将被禁用")

    print("✅ 依赖检查完成")
    return True


def create_default_validation_config():
    """创建默认的验证配置文件"""
    config_content = """validation:
  name: "AUTOSAR XML Validation System"
  version: "1.0.0"

file_paths:
  xml_instances:
    - "xml_instance/ASW_COM.arxml"

  xsd_schema: "src/constraint_graph/artifacts/schema/AUTOSAR_4-2-2.xsd"
  shacl_shapes: "src/constraint_graph/artifacts/shapes/autosar_shapes.ttl"
  smt_template: "src/constraint_graph/artifacts/smt/constraints.smt2"

  output_dir: "logs"
  report_dir: "reports"

validators:
  structure:
    enabled: true
    timeout: 30

  semantic:
    enabled: true
    timeout: 60

  constraint:
    enabled: true
    timeout: 120

validation_modes:
  quick: ["structure"]
  standard: ["structure", "semantic"] 
  full: ["structure", "semantic", "constraint"]

default_mode: "full"

reporting:
  format: "text"
  detailed_errors: true
  save_reports: true
  console_output: true
"""

    # 创建config目录
    Path("config").mkdir(exist_ok=True)

    # 写入配置文件
    config_file = Path("config/validation_config.yaml")
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(config_content)

    print(f"✅ 创建默认配置: {config_file}")


def check_config_files():
    """检查配置文件"""
    print("\n📝 检查配置文件...")

    # 检查主配置文件
    main_config = Path("config/main_config.yaml")
    validation_config = Path("config/validation_config.yaml")

    if not main_config.exists() and not validation_config.exists():
        print("❌ 未找到配置文件，创建默认配置...")
        create_default_validation_config()

    # 优先使用专门的验证配置
    if validation_config.exists():
        print(f"✅ 使用验证配置: {validation_config}")
        return str(validation_config)
    elif main_config.exists():
        print(f"✅ 使用主配置: {main_config}")
        return str(main_config)

    return None


def check_validation_files():
    """检查验证相关文件"""
    print("\n📋 检查验证文件...")

    # 从配置中读取文件路径
    config_file = check_config_files()
    if not config_file:
        return False

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ 配置文件读取失败: {e}")
        return False

    file_paths = config.get('file_paths', {})

    # 检查XML实例文件
    xml_instances = file_paths.get('xml_instances', [])
    available_xmls = 0
    for xml_file in xml_instances:
        if Path(xml_file).exists():
            available_xmls += 1
            print(f"✅ XML实例: {xml_file}")
        else:
            print(f"⚠️  XML实例未找到: {xml_file}")

    if available_xmls == 0:
        print("❌ 没有可用的XML实例文件")
        return False

    # 检查验证器文件
    validator_files = [
        ('XSD Schema', file_paths.get('xsd_schema')),
        ('SHACL Shapes', file_paths.get('shacl_shapes')),
        ('SMT Template', file_paths.get('smt_template'))
    ]

    missing_files = []
    for file_desc, file_path in validator_files:
        if file_path and Path(file_path).exists():
            print(f"✅ {file_desc}: {file_path}")
        else:
            missing_files.append(f"{file_desc}: {file_path}")
            print(f"❌ {file_desc}: {file_path}")

    if missing_files:
        print(f"❌ 缺少验证文件: {len(missing_files)} 个")
        return False

    print("✅ 验证文件检查完成")
    return True


def run_validation_system():
    """运行验证系统"""
    print("\n🚀 启动验证系统...")

    # 添加项目根目录到Python路径
    project_root = Path.cwd()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    try:
        # 检查主验证器文件是否存在
        main_validator_path = Path("src/validation/main_validator.py")
        if not main_validator_path.exists():
            print(f"❌ 主验证器文件不存在: {main_validator_path}")
            print("请确保已经从重构方案中复制了新的验证器文件")
            return False

        # 导入主验证器
        from src.validation.main_validator import AutosarValidator

        # 使用验证配置文件
        config_path = "config/validation_config.yaml"
        if not Path(config_path).exists():
            config_path = "config/main_config.yaml"

        # 创建验证器实例
        validator = AutosarValidator(config_path)

        print("\n" + "=" * 80)
        print("🎯 AUTOSAR XML验证系统已启动")
        print("=" * 80)

        # 询问用户运行模式
        print("\n请选择运行模式:")
        print("1. 验证所有XML文件 (推荐)")
        print("2. 交互模式")
        print("3. 验证单个文件")

        choice = input("\n请输入选择 (1-3, 默认1): ").strip() or "1"

        if choice == "1":
            # 验证所有文件
            print("\n开始验证所有XML文件...")
            results = validator.validate_all_files()

            # 显示最终结果
            passed = sum(1 for r in results if r['success'])
            total = len(results)

            if passed == total:
                print(f"\n🎉 验证完成! 所有 {total} 个文件都通过了验证")
                return True
            else:
                print(f"\n⚠️  验证完成! {passed}/{total} 个文件通过验证")
                return False

        elif choice == "2":
            # 交互模式
            validator.run_interactive()
            return True

        elif choice == "3":
            # 单文件验证
            print("\n可用的XML文件:")
            for i, xml_file in enumerate(validator.available_xml_files, 1):
                print(f"{i}. {Path(xml_file).name}")

            try:
                file_choice = int(input("\n请选择文件序号: ")) - 1
                if 0 <= file_choice < len(validator.available_xml_files):
                    xml_file = validator.available_xml_files[file_choice]
                    result = validator.validate_single_file(xml_file)
                    return result['success']
                else:
                    print("无效的文件序号")
                    return False
            except ValueError:
                print("请输入有效的数字")
                return False
        else:
            print("无效选择")
            return False

    except ImportError as e:
        print(f"❌ 导入验证模块失败: {e}")
        print("请检查项目结构和Python路径设置")
        print("确保已经从重构方案中复制了以下文件:")
        print("  - src/validation/main_validator.py")
        print("  - src/validation/orchestrator/config_driven_orchestrator.py")
        return False
    except Exception as e:
        print(f"❌ 验证系统运行失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("=" * 80)
    print("🔧 AUTOSAR XML验证系统 - 一键启动")
    print("=" * 80)
    print("适用于PyCharm环境，请确保已手动安装所需依赖包")
    print()

    # 1. 检查项目结构
    if not check_project_structure():
        print("\n❌ 项目结构不完整，请检查文件和目录")
        input("按Enter键退出...")
        return False

    # 2. 检查依赖包
    if not check_dependencies():
        print("\n❌ 依赖包不完整，请在PyCharm中安装缺少的包")
        print("\n安装步骤:")
        print("1. File -> Settings")
        print("2. Project -> Python Interpreter")
        print("3. 点击 '+' 按钮")
        print("4. 搜索并安装: xmlschema, rdflib, pyshacl, pyyaml")
        print("5. 可选安装: z3-solver (用于SMT约束验证)")
        input("\n按Enter键退出...")
        return False

    # 3. 检查验证文件
    if not check_validation_files():
        print("\n❌ 验证文件不完整，请检查配置文件中的路径设置")
        input("按Enter键退出...")
        return False

    # 4. 运行验证系统
    success = run_validation_system()

    if success:
        print("\n✅ 验证系统运行完成")
    else:
        print("\n❌ 验证系统运行出现问题")

    input("\n按Enter键退出...")
    return success


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断了程序运行")
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")
        import traceback
        traceback.print_exc()
        input("按Enter键退出...")