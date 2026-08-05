#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SMT 文件诊断工具
用于检测 SMT-LIB 2 文件中的语法问题、括号匹配、重复声明等
"""
import os
import re
from collections import defaultdict


class SMTDiagnostics:
    """SMT 文件诊断类"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.content = ""
        self.lines = []
        self.errors = []
        self.warnings = []
        self.info = []

    def load_file(self) -> bool:
        """加载 SMT 文件"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.content = f.read()
                self.lines = self.content.split('\n')
            return True
        except Exception as e:
            self.errors.append(f"无法读取文件: {e}")
            return False

    def check_parentheses_balance(self):
        """检查括号匹配 - 逐行详细检查"""
        print("\n🔍 检查括号匹配...")

        stack = []
        line_opens = defaultdict(int)  # 每行的左括号数
        line_closes = defaultdict(int)  # 每行的右括号数

        for line_num, line in enumerate(self.lines, 1):
            # 移除注释
            clean_line = re.sub(r';.*', '', line)

            for col, char in enumerate(clean_line, 1):
                if char == '(':
                    stack.append((line_num, col))
                    line_opens[line_num] += 1
                elif char == ')':
                    line_closes[line_num] += 1
                    if stack:
                        stack.pop()
                    else:
                        self.errors.append(
                            f"第 {line_num} 行第 {col} 列: 多余的右括号 ')'"
                        )
                        print(f"  ❌ 第 {line_num} 行第 {col} 列: 多余的右括号")
                        print(f"     {clean_line}")
                        print(f"     {' ' * (col - 1)}^")

        # 检查未闭合的左括号
        if stack:
            print(f"\n  ❌ 发现 {len(stack)} 个未闭合的左括号:")
            for line_num, col in stack[:10]:  # 只显示前10个
                print(f"     第 {line_num} 行第 {col} 列")
                if line_num <= len(self.lines):
                    print(f"     {self.lines[line_num - 1]}")

            if len(stack) > 10:
                print(f"     ... 还有 {len(stack) - 10} 个")

        # 统计报告
        total_opens = sum(line_opens.values())
        total_closes = sum(line_closes.values())

        print(f"\n  📊 括号统计:")
        print(f"     左括号 '(' 总数: {total_opens}")
        print(f"     右括号 ')' 总数: {total_closes}")
        print(f"     差值: {total_opens - total_closes}")

        if total_opens == total_closes:
            print(f"  ✅ 括号数量匹配")
        else:
            self.errors.append(
                f"括号不匹配: {total_opens} 个 '(' vs {total_closes} 个 ')'"
            )
            print(f"  ❌ 括号数量不匹配!")

        # 显示每行的括号平衡
        print(f"\n  📋 每行括号详情 (仅显示不平衡的行):")
        for line_num in sorted(set(list(line_opens.keys()) + list(line_closes.keys()))):
            opens = line_opens[line_num]
            closes = line_closes[line_num]
            balance = opens - closes

            if balance != 0:
                status = "⚠️" if abs(balance) > 3 else "ℹ️"
                print(f"     {status} 第 {line_num:3d} 行: "
                      f"( {opens:2d} | ) {closes:2d} | 净差 {balance:+3d}")

    def check_declaration_syntax(self):
        """检查声明语句的语法"""
        print("\n🔍 检查声明语句语法...")

        # 匹配各种声明
        patterns = {
            'set-logic': r'\(\s*set-logic\s+\w+\s*\)',
            'declare-sort': r'\(\s*declare-sort\s+[\w\-]+\s+\d+\s*\)',
            'declare-fun': r'\(\s*declare-fun\s+[\w\-]+\s*\([^\)]*\)\s*\w+\s*\)',
            'declare-const': r'\(\s*declare-const\s+[\w\-]+\s+\w+\s*\)',
            'assert': r'\(\s*assert\s+',
            'check-sat': r'\(\s*check-sat\s*\)',
        }

        found_commands = defaultdict(list)

        for line_num, line in enumerate(self.lines, 1):
            clean_line = re.sub(r';.*', '', line).strip()
            if not clean_line:
                continue

            for cmd, pattern in patterns.items():
                if re.search(pattern, clean_line):
                    found_commands[cmd].append(line_num)

        print(f"  📊 发现的命令:")
        for cmd, line_nums in sorted(found_commands.items()):
            print(f"     {cmd:15s}: {len(line_nums):3d} 个")
            if cmd == 'set-logic' and len(line_nums) > 1:
                self.warnings.append(f"发现多个 set-logic 声明: {line_nums}")
                print(f"        ⚠️  多个 set-logic 声明")

    def check_assert_statements(self):
        """检查 assert 语句的结构"""
        print("\n🔍 检查 assert 语句...")

        in_assert = False
        assert_start_line = 0
        assert_depth = 0
        assert_count = 0

        for line_num, line in enumerate(self.lines, 1):
            clean_line = re.sub(r';.*', '', line)

            # 检测 assert 开始
            if '(assert' in clean_line and not in_assert:
                in_assert = True
                assert_start_line = line_num
                assert_depth = 0
                assert_count += 1

            if in_assert:
                # 计算这行的括号深度变化
                for char in clean_line:
                    if char == '(':
                        assert_depth += 1
                    elif char == ')':
                        assert_depth -= 1

                        # assert 结束
                        if assert_depth == 0:
                            in_assert = False
                            break

        if in_assert:
            self.errors.append(
                f"第 {assert_start_line} 行的 assert 语句未闭合"
            )
            print(f"  ❌ 第 {assert_start_line} 行的 assert 语句未闭合")
            print(f"     {self.lines[assert_start_line - 1]}")

        print(f"  ✅ 共发现 {assert_count} 个 assert 语句")

    def find_duplicate_declarations(self):
        """查找重复声明"""
        print("\n🔍 检查重复声明...")

        declarations = defaultdict(list)

        # 提取声明
        declare_pattern = r'\(\s*(declare-(?:sort|fun|const))\s+([\w\-]+)'

        for line_num, line in enumerate(self.lines, 1):
            clean_line = re.sub(r';.*', '', line)
            matches = re.finditer(declare_pattern, clean_line)

            for match in matches:
                decl_type = match.group(1)
                symbol = match.group(2)
                declarations[symbol].append((line_num, decl_type, clean_line.strip()))

        # 检查重复
        duplicates = {k: v for k, v in declarations.items() if len(v) > 1}

        if duplicates:
            print(f"  ⚠️  发现 {len(duplicates)} 个重复声明:")
            for symbol, decls in sorted(duplicates.items()):
                print(f"\n     符号: '{symbol}' (出现 {len(decls)} 次)")
                for line_num, decl_type, line_content in decls:
                    print(f"       第 {line_num:3d} 行: {decl_type}")
                    print(f"           {line_content[:80]}...")

            self.warnings.extend([f"重复声明: {k}" for k in duplicates.keys()])
        else:
            print(f"  ✅ 未发现重复声明")

    def check_logical_structure(self):
        """检查逻辑结构问题"""
        print("\n🔍 检查逻辑结构...")

        has_set_logic = False
        has_check_sat = False
        has_assertions = False

        for line in self.lines:
            clean_line = re.sub(r';.*', '', line)

            if '(set-logic' in clean_line:
                has_set_logic = True
            if '(check-sat)' in clean_line:
                has_check_sat = True
            if '(assert' in clean_line:
                has_assertions = True

        print(f"  📋 结构检查:")
        print(f"     set-logic:  {'✅' if has_set_logic else '❌'}")
        print(f"     assertions: {'✅' if has_assertions else '⚠️  (没有断言)'}")
        print(f"     check-sat:  {'✅' if has_check_sat else '⚠️  (没有求解命令)'}")

        if not has_set_logic:
            self.warnings.append("缺少 (set-logic ...) 声明")
        if not has_check_sat:
            self.info.append("缺少 (check-sat) 命令")

    def find_problematic_lines(self):
        """找出可能有问题的行"""
        print("\n🔍 查找可疑的行...")

        suspicious_patterns = [
            (r'\)\s*\)', '连续的右括号'),
            (r'\(\s*\(', '连续的左括号'),
            (r'\)\s*\(', '括号之间缺少空格或操作符'),
            (r'^\s*\)\s*$', '单独的右括号'),
            (r'[^\s]\(', '括号前缺少空格'),
            (r'\)[^\s\)]', '括号后缺少空格'),
        ]

        found_issues = []

        for line_num, line in enumerate(self.lines, 1):
            clean_line = re.sub(r';.*', '', line)
            if not clean_line.strip():
                continue

            for pattern, description in suspicious_patterns:
                if re.search(pattern, clean_line):
                    found_issues.append((line_num, description, clean_line.strip()))

        if found_issues:
            print(f"  ⚠️  发现 {len(found_issues)} 个可疑行:")
            for line_num, desc, line_content in found_issues[:20]:  # 只显示前20个
                print(f"\n     第 {line_num:3d} 行: {desc}")
                print(f"           {line_content[:100]}")

            if len(found_issues) > 20:
                print(f"\n     ... 还有 {len(found_issues) - 20} 个可疑行")
        else:
            print(f"  ✅ 未发现明显可疑的行")

    def try_z3_parse(self):
        """尝试用 Z3 解析文件"""
        print("\n🔍 尝试 Z3 解析...")

        try:
            import z3
            print(f"  ✅ Z3 已安装")

            try:
                z3.parse_smt2_string(self.content)
                print(f"  ✅ Z3 解析成功!")
                return True
            except Exception as e:
                error_msg = str(e)
                print(f"  ❌ Z3 解析失败:")
                print(f"     {error_msg}")

                # 尝试从错误消息中提取行号
                line_match = re.search(r'line\s+(\d+)', error_msg)
                col_match = re.search(r'column\s+(\d+)', error_msg)

                if line_match:
                    line_num = int(line_match.group(1))
                    print(f"\n     问题位置: 第 {line_num} 行")

                    # 显示问题行及其上下文
                    if 1 <= line_num <= len(self.lines):
                        start = max(1, line_num - 2)
                        end = min(len(self.lines), line_num + 2)

                        print(f"\n     上下文:")
                        for i in range(start, end + 1):
                            marker = " >>> " if i == line_num else "     "
                            print(f"{marker}{i:3d}: {self.lines[i - 1]}")

                self.errors.append(f"Z3 解析错误: {error_msg}")
                return False

        except ImportError:
            print(f"  ⚠️  Z3 未安装,跳过解析测试")
            self.info.append("建议安装 z3-solver 进行更详细的检查")
            return None

    def generate_report(self):
        """生成诊断报告"""
        print("\n" + "=" * 70)
        print("📊 诊断报告摘要")
        print("=" * 70)

        print(f"\n文件: {os.path.basename(self.file_path)}")
        print(f"大小: {len(self.content)} 字节")
        print(f"行数: {len(self.lines)}")

        if self.errors:
            print(f"\n❌ 错误 ({len(self.errors)} 个):")
            for i, error in enumerate(self.errors, 1):
                print(f"   {i}. {error}")
        else:
            print(f"\n✅ 没有发现严重错误")

        if self.warnings:
            print(f"\n⚠️  警告 ({len(self.warnings)} 个):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"   {i}. {warning}")

        if self.info:
            print(f"\nℹ️  信息:")
            for info in self.info:
                print(f"   • {info}")

        print("\n" + "=" * 70)

        if self.errors:
            print("❌ 文件存在严重问题,需要修复")
            return False
        elif self.warnings:
            print("⚠️  文件可能存在问题,建议检查")
            return True
        else:
            print("✅ 文件看起来没有明显问题")
            return True

    def run_all_checks(self):
        """运行所有诊断检查"""
        print("=" * 70)
        print(f"SMT 文件诊断工具")
        print(f"诊断文件: {os.path.basename(self.file_path)}")
        print("=" * 70)

        if not self.load_file():
            return False

        # 运行所有检查
        self.check_parentheses_balance()
        self.check_declaration_syntax()
        self.check_assert_statements()
        self.find_duplicate_declarations()
        self.check_logical_structure()
        self.find_problematic_lines()
        self.try_z3_parse()

        # 生成报告
        return self.generate_report()


def main():
    """主函数"""
    import sys

    # 默认检查路径
    default_paths = [
        "src/constraint_graph/artifacts/smt/constraints.smt2",
        "constraints.smt2",
        "input/constraints.smt2"
    ]

    # 如果提供了命令行参数
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        # 尝试找到文件
        file_path = None
        for path in default_paths:
            if os.path.exists(path):
                file_path = path
                break

        if not file_path:
            print("❌ 未找到 SMT 文件")
            print(f"\n已尝试以下路径:")
            for path in default_paths:
                print(f"  • {path}")
            print(f"\n使用方法: python {sys.argv[0]} <smt_file_path>")
            return

    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return

    # 运行诊断
    diagnostics = SMTDiagnostics(file_path)
    success = diagnostics.run_all_checks()

    # 退出码
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()