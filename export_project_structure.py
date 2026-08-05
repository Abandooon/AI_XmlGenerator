# export_project_structure.py
"""
自动导出PyCharm项目结构
"""
from datetime import datetime
from pathlib import Path


def should_ignore(path: Path, ignore_patterns: list) -> bool:
    """检查是否应该忽略某个路径"""
    path_str = str(path)
    for pattern in ignore_patterns:
        if pattern in path_str:
            return True
    return False


def get_project_structure(root_path: Path, ignore_patterns: list = None) -> list:
    """获取项目结构"""
    if ignore_patterns is None:
        ignore_patterns = [
            '__pycache__',
            '.git',
            '.idea',
            'venv',
            'env',
            '.pytest_cache',
            'node_modules',
            '.DS_Store',
            'Thumbs.db'
        ]

    structure = []

    def add_directory(current_path: Path, prefix: str = ""):
        """递归添加目录结构"""
        try:
            # 获取当前目录下的所有项目
            items = sorted(current_path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))

            for i, item in enumerate(items):
                if should_ignore(item, ignore_patterns):
                    continue

                # 判断是否是最后一个项目
                is_last = i == len([x for x in items if not should_ignore(x, ignore_patterns)]) - 1

                # 选择合适的符号
                if is_last:
                    symbol = "└── "
                    next_prefix = prefix + "    "
                else:
                    symbol = "├── "
                    next_prefix = prefix + "│   "

                # 添加到结构中
                if item.is_dir():
                    structure.append(f"{prefix}{symbol}{item.name}/")
                    add_directory(item, next_prefix)
                else:
                    file_size = item.stat().st_size
                    if file_size > 1024:
                        size_str = f" ({file_size // 1024}KB)"
                    else:
                        size_str = f" ({file_size}B)"
                    structure.append(f"{prefix}{symbol}{item.name}{size_str}")

        except PermissionError:
            structure.append(f"{prefix}[Permission Denied]")

    structure.append(f"{root_path.name}/")
    add_directory(root_path)

    return structure


def export_detailed_structure(root_path: Path) -> str:
    """导出详细的项目结构信息"""

    # 基本统计信息
    python_files = list(root_path.rglob("*.py"))
    yaml_files = list(root_path.rglob("*.yaml")) + list(root_path.rglob("*.yml"))
    txt_files = list(root_path.rglob("*.txt"))
    json_files = list(root_path.rglob("*.json"))

    total_files = len(list(root_path.rglob("*")))
    total_dirs = len([p for p in root_path.rglob("*") if p.is_dir()])

    # 计算总代码行数
    total_lines = 0
    for py_file in python_files:
        try:
            with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                total_lines += len(f.readlines())
        except:
            pass

    report = []
    report.append("=" * 80)
    report.append(f"项目结构导出报告")
    report.append(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"项目路径: {root_path.absolute()}")
    report.append("=" * 80)
    report.append("")

    # 统计信息
    report.append("📊 统计信息:")
    report.append(f"  总文件数: {total_files}")
    report.append(f"  总目录数: {total_dirs}")
    report.append(f"  Python文件: {len(python_files)} 个")
    report.append(f"  配置文件: {len(yaml_files)} 个")
    report.append(f"  文档文件: {len(txt_files)} 个")
    report.append(f"  JSON文件: {len(json_files)} 个")
    report.append(f"  总代码行数: {total_lines} 行")
    report.append("")

    # 项目结构树
    report.append("🌳 项目结构树:")
    structure = get_project_structure(root_path)
    report.extend(structure)
    report.append("")

    # 关键文件列表
    report.append("📁 关键文件列表:")

    # Python模块文件
    if python_files:
        report.append("  🐍 Python文件:")
        for py_file in sorted(python_files):
            rel_path = py_file.relative_to(root_path)
            try:
                lines = len(open(py_file, 'r', encoding='utf-8', errors='ignore').readlines())
                report.append(f"    {rel_path} ({lines} 行)")
            except:
                report.append(f"    {rel_path}")

    # 配置文件
    if yaml_files:
        report.append("  ⚙️ 配置文件:")
        for yaml_file in sorted(yaml_files):
            rel_path = yaml_file.relative_to(root_path)
            report.append(f"    {rel_path}")

    # 文档文件
    if txt_files:
        report.append("  📄 文档文件:")
        for txt_file in sorted(txt_files):
            rel_path = txt_file.relative_to(root_path)
            report.append(f"    {rel_path}")

    report.append("")

    # 依赖分析
    requirements_file = root_path / "requirements.txt"
    if requirements_file.exists():
        report.append("📦 项目依赖:")
        try:
            with open(requirements_file, 'r', encoding='utf-8') as f:
                deps = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                for dep in deps:
                    report.append(f"  - {dep}")
        except:
            report.append("  (无法读取requirements.txt)")
        report.append("")

    return "\n".join(report)


def export_code_summary(root_path: Path) -> str:
    """导出代码摘要"""

    summary = []
    summary.append("=" * 80)
    summary.append("代码文件摘要")
    summary.append("=" * 80)
    summary.append("")

    python_files = list(root_path.rglob("*.py"))

    for py_file in sorted(python_files):
        rel_path = py_file.relative_to(root_path)
        summary.append(f"📄 {rel_path}")
        summary.append("-" * 60)

        try:
            with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

            # 提取文档字符串和关键信息
            in_docstring = False
            docstring_lines = []
            classes = []
            functions = []

            for i, line in enumerate(lines):
                stripped = line.strip()

                # 检测文档字符串
                if '"""' in stripped or "'''" in stripped:
                    if not in_docstring:
                        in_docstring = True
                        if stripped.count('"""') == 2 or stripped.count("'''") == 2:
                            docstring_lines.append(stripped)
                            in_docstring = False
                        else:
                            docstring_lines.append(stripped)
                    else:
                        docstring_lines.append(stripped)
                        in_docstring = False
                elif in_docstring:
                    docstring_lines.append(stripped)

                # 检测类和函数
                if stripped.startswith('class '):
                    classes.append(stripped)
                elif stripped.startswith('def '):
                    functions.append(stripped)
                elif stripped.startswith('async def '):
                    functions.append(stripped)

            # 显示文档字符串
            if docstring_lines:
                summary.append("📝 文档:")
                for doc_line in docstring_lines[:5]:  # 只显示前5行
                    summary.append(f"  {doc_line}")
                if len(docstring_lines) > 5:
                    summary.append(f"  ... (还有 {len(docstring_lines) - 5} 行)")
                summary.append("")

            # 显示类
            if classes:
                summary.append("🏗️ 类:")
                for cls in classes:
                    summary.append(f"  {cls}")
                summary.append("")

            # 显示函数
            if functions:
                summary.append("⚙️ 函数:")
                for func in functions[:10]:  # 只显示前10个函数
                    summary.append(f"  {func}")
                if len(functions) > 10:
                    summary.append(f"  ... (还有 {len(functions) - 10} 个函数)")
                summary.append("")

            summary.append(f"📊 统计: {len(lines)} 行, {len(classes)} 个类, {len(functions)} 个函数")

        except Exception as e:
            summary.append(f"❌ 无法读取文件: {e}")

        summary.append("")
        summary.append("")

    return "\n".join(summary)


def main():
    """主函数"""
    root_path = Path.cwd()

    print("🚀 开始导出项目结构...")

    # 创建输出目录
    output_dir = root_path / "project_exports"
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 导出详细结构
    print("📋 导出详细结构...")
    detailed_structure = export_detailed_structure(root_path)
    detail_file = output_dir / f"project_structure_detailed_{timestamp}.txt"
    detail_file.write_text(detailed_structure, encoding='utf-8')

    # 导出简单结构
    print("🌳 导出简单结构...")
    simple_structure = get_project_structure(root_path)
    simple_file = output_dir / f"project_structure_simple_{timestamp}.txt"
    simple_file.write_text("\n".join(simple_structure), encoding='utf-8')

    # 导出代码摘要
    print("📝 导出代码摘要...")
    code_summary = export_code_summary(root_path)
    summary_file = output_dir / f"code_summary_{timestamp}.txt"
    summary_file.write_text(code_summary, encoding='utf-8')

    print("✅ 导出完成!")
    print(f"📁 输出目录: {output_dir}")
    print(f"📄 详细结构: {detail_file.name}")
    print(f"🌳 简单结构: {simple_file.name}")
    print(f"📝 代码摘要: {summary_file.name}")


if __name__ == "__main__":
    main()