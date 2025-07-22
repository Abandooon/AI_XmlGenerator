# run_validation.py
"""
AUTOSAR XML验证系统 - 一键运行脚本 (修复版)
支持main_config.yaml配置文件
"""
import os
import sys
from pathlib import Path
import yaml


def check_project_structure():
    """检查项目结构完整性"""
    print("🔍 检查项目结构...")

    required_dirs = [
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
    config_file = Path("config/mainnn_config.yaml")
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(config_content)

    print(f"✅ 创建默认配置: {config_file}")


def check_config_files():
    """检查配置文件 - 修复版，正确支持main_config.yaml"""
    print("\n📝 检查配置文件...")

    # 修正：按正确优先级查找配置文件
    config_candidates = [
        "main_config.yaml",              # 1. 根目录下的main_config.yaml
        "config/main_config.yaml",       # 2. config目录下的main_config.yaml
        "validation_config.yaml",        # 3. 旧版配置文件（兼容性）
        "config/validation_config.yaml"  # 4. config目录下的旧版配置文件
    ]

    for config_file in config_candidates:
        config_path = Path(config_file)
        if config_path.exists():
            print(f"✅ 找到配置文件: {config_file}")

            # 验证配置文件格式
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)

                # 检查是否有file_paths配置
                if 'file_paths' in config:
                    print(f"✅ 配置文件格式正确")
                    return str(config_path)
                else:
                    print(f"⚠️  配置文件缺少file_paths部分，尝试下一个...")
                    continue

            except Exception as e:
                print(f"⚠️  配置文件格式错误: {e}，尝试下一个...")
                continue

    # 如果都没找到合适的配置文件，使用默认路径
    print("❌ 未找到合适的配置文件")
    return None


def create_missing_validation_files():
    """创建缺失的验证文件"""
    print("\n🔧 检查并创建缺失的验证文件...")

    # 创建必要的目录结构
    directories = [
        "src/constraint_graph/artifacts/shapes",
        "src/constraint_graph/artifacts/schema",
        "src/constraint_graph/artifacts/smt",
        "logs",
        "reports"
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ 目录: {directory}")

    # 创建基础的SHACL shapes文件
    shapes_file = Path("src/constraint_graph/artifacts/shapes/autosar_shapes.ttl")
    if not shapes_file.exists():
        shapes_content = """@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix autosar: <http://autosar.org/schema/> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

# 基础的AUTOSAR组件形状定义
autosar:ApplicationSwComponentTypeShape
    a sh:NodeShape ;
    sh:targetClass autosar:APPLICATION-SW-COMPONENT-TYPE ;
    sh:property [
        sh:path autosar:SHORT-NAME ;
        sh:datatype xsd:string ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:message "APPLICATION-SW-COMPONENT-TYPE must have exactly one SHORT-NAME" ;
    ] .

# 端口原型形状定义
autosar:PortPrototypeShape
    a sh:NodeShape ;
    sh:targetClass autosar:P-PORT-PROTOTYPE, autosar:R-PORT-PROTOTYPE ;
    sh:property [
        sh:path autosar:SHORT-NAME ;
        sh:datatype xsd:string ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:message "Port prototype must have exactly one SHORT-NAME" ;
    ] .
"""
        with open(shapes_file, 'w', encoding='utf-8') as f:
            f.write(shapes_content)
        print(f"✅ 创建SHACL shapes: {shapes_file}")

    # 创建基础的SMT模板文件
    smt_file = Path("src/constraint_graph/artifacts/smt/constraints.smt2")
    if not smt_file.exists():
        smt_content = """; Basic AUTOSAR SMT constraint template

(set-logic QF_LRA)

; Basic timing constraints
(declare-const period Real)
(declare-const deadline Real)

; Constraints
(assert (> period 0.0))
(assert (> deadline 0.0))
(assert (<= deadline period))

(check-sat)
"""
        with open(smt_file, 'w', encoding='utf-8') as f:
            f.write(smt_content)
        print(f"✅ 创建SMT模板: {smt_file}")

    # 创建基础的XSD文件（如果不存在）
    xsd_file = Path("src/constraint_graph/artifacts/schema/AUTOSAR_4-2-2.xsd")
    if not xsd_file.exists():
        xsd_content = """<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
           targetNamespace="http://autosar.org/schema/r4.0"
           xmlns:autosar="http://autosar.org/schema/r4.0"
           elementFormDefault="qualified">

    <!-- Basic AUTOSAR component definition -->
    <xs:element name="APPLICATION-SW-COMPONENT-TYPE">
        <xs:complexType>
            <xs:sequence>
                <xs:element name="SHORT-NAME" type="xs:string"/>
                <xs:element name="PORTS" minOccurs="0">
                    <xs:complexType>
                        <xs:choice maxOccurs="unbounded">
                            <xs:element name="P-PORT-PROTOTYPE" type="autosar:PortPrototypeType"/>
                            <xs:element name="R-PORT-PROTOTYPE" type="autosar:PortPrototypeType"/>
                        </xs:choice>
                    </xs:complexType>
                </xs:element>
            </xs:sequence>
        </xs:complexType>
    </xs:element>

    <!-- Port prototype type definition -->
    <xs:complexType name="PortPrototypeType">
        <xs:sequence>
            <xs:element name="SHORT-NAME" type="xs:string"/>
        </xs:sequence>
    </xs:complexType>

</xs:schema>
"""
        with open(xsd_file, 'w', encoding='utf-8') as f:
            f.write(xsd_content)
        print(f"✅ 创建XSD schema: {xsd_file}")


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
        # 创建示例XML文件
        create_sample_xml()

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
        print(f"⚠️  发现 {len(missing_files)} 个缺失文件，尝试创建...")
        create_missing_validation_files()

    print("✅ 验证文件检查完成")
    return True


def create_sample_xml():
    """创建示例XML文件"""
    xml_dir = Path("xml_instance")
    xml_dir.mkdir(exist_ok=True)

    xml_file = xml_dir / "ASW_COM.arxml"
    if not xml_file.exists():
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<AUTOSAR xmlns="http://autosar.org/schema/r4.0" 
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <AR-PACKAGES>
        <AR-PACKAGE>
            <SHORT-NAME>ComponentTypes</SHORT-NAME>
            <ELEMENTS>
                <APPLICATION-SW-COMPONENT-TYPE>
                    <SHORT-NAME>ExampleComponent</SHORT-NAME>
                    <PORTS>
                        <P-PORT-PROTOTYPE>
                            <SHORT-NAME>ProvidePort</SHORT-NAME>
                        </P-PORT-PROTOTYPE>
                        <R-PORT-PROTOTYPE>
                            <SHORT-NAME>RequirePort</SHORT-NAME>
                        </R-PORT-PROTOTYPE>
                    </PORTS>
                </APPLICATION-SW-COMPONENT-TYPE>
            </ELEMENTS>
        </AR-PACKAGE>
    </AR-PACKAGES>
</AUTOSAR>
"""
        with open(xml_file, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        print(f"✅ 创建示例XML: {xml_file}")


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

        # 查找配置文件
        config_path = check_config_files()

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


def validate_constraint_files():
    """验证生成的约束文件质量"""
    print("\n🔍 检查约束文件质量...")

    # 检查SHACL文件
    shacl_file = Path("src/constraint_graph/artifacts/shapes/autosar_shapes.ttl")
    if shacl_file.exists():
        try:
            import rdflib
            g = rdflib.Graph()
            g.parse(str(shacl_file), format="turtle")
            print(f"✅ SHACL文件语法正确: {len(g)} 个三元组")
        except Exception as e:
            print(f"❌ SHACL文件语法错误: {e}")
            return False

    # 检查SMT文件
    smt_file = Path("src/constraint_graph/artifacts/smt/constraints.smt2")
    if smt_file.exists():
        try:
            content = smt_file.read_text(encoding='utf-8')
            if "(check-sat)" in content and "(set-logic" in content:
                print(f"✅ SMT文件格式正确")
            else:
                print(f"⚠️  SMT文件可能不完整")
        except Exception as e:
            print(f"❌ SMT文件读取错误: {e}")

    return True


def main():
    """主函数"""
    print("=" * 80)
    print("🔧 AUTOSAR XML验证系统 - 一键启动 (修复版)")
    print("=" * 80)
    print("支持main_config.yaml配置文件，自动创建缺失文件")
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
        print("\n❌ 验证文件设置失败")
        input("按Enter键退出...")
        return False

    # 3.1 验证约束文件质量
    validate_constraint_files()

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