import os
import re
from collections import defaultdict

# --- 配置 ---
INPUT_DIR = "input"
OUTPUT_DIR = "output"
# 我们只对这些关键字进行符号冲突检查
SIMPLE_DECL_KEYWORDS = ("declare-sort", "declare-fun", "declare-const")
# 用于从 (declare-fun myFunc ...) 中提取 'myFunc' 的 Regex
RE_SIMPLE_SYMBOL = re.compile(
    # 匹配 (declare-sort/fun/const
    r'\(\s*(declare-sort|declare-fun|declare-const)\s+'
    # 捕获第一个不带括号或空格的词（即符号）
    r'([^\s\(\)]+)'
)


def remove_comments(content):
    """从 SMT 内容中删除所有 ; 注释。"""
    return re.sub(r";.*", "", content)


def parse_sexprs(content):
    """
    一个简单的 S-表达式解析器，用于提取所有顶层 (...) 块。
    """
    paren_level = 0
    expr_start = -1
    for i, char in enumerate(content):
        if char == '(':
            if paren_level == 0:
                expr_start = i
            paren_level += 1
        elif char == ')':
            if paren_level > 0:
                paren_level -= 1
                if paren_level == 0 and expr_start != -1:
                    yield content[expr_start: i + 1]
                    expr_start = -1


def normalize_expr(s_expr):
    """将 S-表达式规范化为单行，用单个空格分隔。"""
    return re.sub(r'\s+', ' ', s_expr).strip()


def process_smt_file(input_path, output_path):
    """
    处理单个 SMT 文件：
    1. 提取所有声明。
    2. 删除完全相同的重复。
    3. 识别符号冲突。
    4. 写入清理后的文件。
    返回一个冲突报告列表。
    """
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"  [错误] 无法读取文件: {input_path} ({e})")
        return []

    content_no_comments = remove_comments(content)

    set_logic_stmt = None
    other_statements = []

    # 注册表
    # Key: 符号 (e.g., "myFunc"), Value: set(规范化的完整声明)
    simple_decls_registry = defaultdict(set)
    # Value: set(规范化的完整声明)
    datatype_decls_registry = set()

    # 1. 解析和分类
    for s_expr in parse_sexprs(content_no_comments):
        norm_expr = normalize_expr(s_expr)
        if not norm_expr:
            continue

        if norm_expr.startswith('(set-logic'):
            set_logic_stmt = norm_expr
            continue

        match = RE_SIMPLE_SYMBOL.match(norm_expr)

        if match:
            # 这是一个 simple-decl (sort, fun, const)
            keyword, symbol = match.groups()
            simple_decls_registry[symbol].add(norm_expr)

        elif norm_expr.startswith('(declare-datatypes'):
            # 这是一个 datatype-decl
            datatype_decls_registry.add(norm_expr)

        else:
            # 这是一个 'assert', 'check-sat', etc.
            other_statements.append(s_expr)  # 保留原始格式

    # 2. 分析冲突并准备最终的声明列表
    file_conflicts = []
    final_simple_decls = []

    for symbol, definitions in simple_decls_registry.items():
        if len(definitions) > 1:
            # 找到符号冲突！
            report = f"  - 符号冲突 '{symbol}':\n"
            def_list = sorted(list(definitions))
            for i, defn in enumerate(def_list):
                report += f"    {i + 1}: {defn}\n"
            file_conflicts.append(report)

            # 为输出文件选择第一个（按字母顺序）
            final_simple_decls.append(def_list[0])
        else:
            # 没有冲突，只有一个定义
            final_simple_decls.append(list(definitions)[0])

    # 3. 写入清理后的文件
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            if set_logic_stmt:
                f.write(set_logic_stmt)
                f.write("\n\n")

            f.write(";; --- 唯一的简单声明 (Sorts, Funs, Consts) --- ;;\n")
            if final_simple_decls:
                f.write("\n".join(sorted(final_simple_decls)))
                f.write("\n\n")

            f.write(";; --- 唯一的数据类型声明 (Datatypes) --- ;;\n")
            if datatype_decls_registry:
                f.write("\n".join(sorted(list(datatype_decls_registry))))
                f.write("\n\n")

            f.write(";; --- 其他语句 (Assertions, etc.) --- ;;\n")
            if other_statements:
                f.write("\n\n".join(other_statements))
                f.write("\n")

        print(f"  [成功] 已处理: {os.path.basename(input_path)} -> {output_path}")

    except Exception as e:
        print(f"  [错误] 无法写入输出文件: {output_path} ({e})")

    return file_conflicts


def main():
    """
    主函数：遍历 input 目录并打印最终报告。
    """
    print("SMT-LIB 声明冲突检查器")
    print("=" * 40)

    if not os.path.exists(INPUT_DIR):
        print(f"[错误] 输入文件夹 '{INPUT_DIR}' 未找到。")
        print("请在脚本同级目录下创建一个 'input' 文件夹并放入 .smt2 文件。")
        return

    total_conflicts = {}
    file_count = 0

    print(f"正在扫描 '{INPUT_DIR}' 文件夹...")

    for filename in os.listdir(INPUT_DIR):
        if filename.endswith(".smt") or filename.endswith(".smt2"):
            file_count += 1
            input_path = os.path.join(INPUT_DIR, filename)
            output_path = os.path.join(OUTPUT_DIR, filename)

            conflicts = process_smt_file(input_path, output_path)
            if conflicts:
                total_conflicts[filename] = conflicts

    print("=" * 40)
    print("处理完成。")
    print("\n" + "=" * 40)
    print("       SMT 符号冲突报告")
    print("=" * 40)

    if not total_conflicts:
        if file_count > 0:
            print(f"\n检查了 {file_count} 个文件。未发现符号冲突。")
        else:
            print(f"\n在 '{INPUT_DIR}' 中未找到 .smt 或 .smt2 文件。")
    else:
        for filename, conflicts in total_conflicts.items():
            print(f"\n[ 文件: {filename} ]")
            for report in conflicts:
                print(report, end='')  # 报告已经包含了换行符

    print("\n" + "=" * 40)
    print(f"清理后的文件已保存在 '{OUTPUT_DIR}' 文件夹中。")


if __name__ == "__main__":
    main()