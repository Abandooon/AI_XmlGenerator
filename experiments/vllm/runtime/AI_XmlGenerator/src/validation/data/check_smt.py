# -*- coding: utf-8 -*-

import sys
from collections import defaultdict
from typing import Optional

from src.validation.constraints.smt_validator import SMTValidator


def find_first_existing(candidates):
    """在候选路径列表中找到第一个存在的文件"""
    for c in candidates:
        if c.exists():
            return c
    return None


def sanitize_template_text(txt: str) -> str:
    """
    对 SMT 模板文本做基本清洗：
    对完全重复的声明 (declare-sort / declare-fun / declare-const)
       只保留第一次出现
       ✅ fun 用 (name, 参数列表, 返回类型) 作为签名去重，避免误删不同参数个数的声明
    """

    lines = txt.splitlines()
    new_lines = []

    seen_sorts = set()  # key: sort 名
    seen_funs = set()  # key: (name, arg_sorts_str, ret_sort)
    seen_consts = set()  # key: (name, sort)

    # 解析完整签名（只看代码部分，不看注释）
    sort_re = re.compile(r'\(declare-sort\s+([^\s\)]+)\s*(\d*)\s*\)')
    fun_re = re.compile(r'\(declare-fun\s+([^\s\)]+)\s*\(([^)]*)\)\s+([^\s\)]+)\s*\)')
    const_re = re.compile(r'\(declare-const\s+([^\s\)]+)\s+([^\s\)]+)\s*\)')

    for line in lines:
        code = line
        semi = code.find(';')
        if semi != -1:
            code = code[:semi]

        m_sort = sort_re.search(code)
        m_fun = fun_re.search(code)
        m_const = const_re.search(code)

        if m_sort:
            # sort：按名称去重（declare-sort X 只能出现一次）
            name = m_sort.group(1)
            if name in seen_sorts:
                print(f"   ℹ️ 跳过重复的 sort 声明: {name}")
                continue
            seen_sorts.add(name)

        elif m_fun:
            # fun：按完整签名去重
            name, args_str, ret_sort = m_fun.groups()
            sig = (name, args_str.strip(), ret_sort)
            if sig in seen_funs:
                print(f"   ℹ️ 跳过重复的函数声明: {name}({args_str}) -> {ret_sort}")
                continue
            seen_funs.add(sig)

        elif m_const:
            # const：按 (name, sort) 去重
            name, sort = m_const.groups()
            sig = (name, sort)
            if sig in seen_consts:
                print(f"   ℹ️ 跳过重复的常量声明: {name} : {sort}")
                continue
            seen_consts.add(sig)

        new_lines.append(line)

    return "\n".join(new_lines)


def disambiguate_overloaded_functions(template_text: str) -> str:
    """
    对模板中的重名函数做“按区域重命名”：
    - 只处理 (declare-fun ...) 的重名情况
    - 忽略以 ';' 开头的注释行中的声明
    - 对于同名函数 f：
        * 第一条声明保持为 f
        * 第二条声明起，依次改为 f__2, f__3, ...
        * 同时把“该声明行到下一条同名声明行之前”的所有调用 f(...) 改为新名字
    这样可以把 LLM 按块生成的重名谓词拆成互不冲突的全局符号。
    """

    lines = template_text.splitlines()
    fun_decl_re = re.compile(
        r'\(declare-fun\s+([^\s\)]+)\s*\(([^)]*)\)\s+([^\s\)]+)\s*\)'
    )

    # name -> list of (line_idx, args_str, ret_sort)
    decls_by_name: dict[str, list[tuple[int, str, str]]] = defaultdict(list)

    # 1) 收集所有非注释的 declare-fun
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith(";") or stripped == "":
            continue
        m = fun_decl_re.search(stripped)
        if m:
            name, args_str, ret_sort = m.groups()
            decls_by_name[name].append((i, args_str.strip(), ret_sort))

    # 2) 对每个出现多次的名字按区域重命名
    for name, decls in decls_by_name.items():
        if len(decls) <= 1:
            continue

        # 按行号排序，保证从上到下处理
        decls.sort(key=lambda x: x[0])
        print(
            f"   ⚠️ 检测到重名函数 '{name}' 有 {len(decls)} 个声明，"
            f"将对后 {len(decls) - 1} 个按区域重命名。"
        )

        for idx_in_group, (line_idx, args_str, ret_sort) in enumerate(decls):
            if idx_in_group == 0:
                # 第一条声明保持原名
                continue

            # 为第 2,3,... 条声明生成新名字：name__2, name__3, ...
            new_name = f"{name}__{idx_in_group + 1}"

            # ---------------------------
            # 2.1 修改声明行本身
            # ---------------------------
            orig_line = lines[line_idx]
            stripped = orig_line.lstrip()
            leading_ws_len = len(orig_line) - len(stripped)
            m2 = fun_decl_re.search(stripped)
            if not m2:
                continue
            s, e = m2.start(1), m2.end(1)
            new_stripped = stripped[:s] + new_name + stripped[e:]
            lines[line_idx] = " " * leading_ws_len + new_stripped

            # ---------------------------
            # 2.2 修改该声明到“下一条同名声明之前”的调用
            # ---------------------------
            seg_start = line_idx + 1
            if idx_in_group + 1 < len(decls):
                seg_end = decls[idx_in_group + 1][0] - 1
            else:
                seg_end = len(lines) - 1

            # 匹配“独立的符号 name”，防止把别的标识符的一部分改掉
            sym_pat = re.compile(
                r'(?<![A-Za-z0-9_\-])' + re.escape(name) + r'(?![A-Za-z0-9_\-])'
            )

            for k in range(seg_start, seg_end + 1):
                line_k = lines[k]
                stripped2 = line_k.lstrip()
                # 整行注释 / 空行跳过
                if stripped2.startswith(";") or stripped2 == "":
                    continue

                # 只改代码部分，不动注释
                semi = line_k.find(";")
                if semi == -1:
                    code_part = line_k
                    comment_part = ""
                else:
                    code_part = line_k[:semi]
                    comment_part = line_k[semi:]

                new_code = sym_pat.sub(new_name, code_part)
                if new_code != code_part:
                    lines[k] = new_code + comment_part

    return "\n".join(lines)


from pathlib import Path
import re


def _check_template_syntax_and_duplicates(
        template_text: str,
        smt_template_path: Path,
) -> str:
    """
    对 SMT 模板本身做一些快速检查，并在清洗后直接写回原文件：
    1. 如安装 python z3，则用 z3.parse_smt2_string 对“原始模板”和“清洗后模板”做语法检查
    2. 正则扫描模板中的 declare-sort / declare-fun / declare-const，检测重名声明
    3. 检测符号既被声明为 sort 又被声明为 fun/const 等“角色冲突”
    4. ✅ 无论 z3 是否解析成功，只要清洗后内容发生变化，就写回 smt_template_path
       （包括：去重 + 重名函数按区域重命名）
    """
    print("🔎 对 SMT 模板做语法与重复声明检查")

    # 1) 声明去重
    cleaned = sanitize_template_text(template_text)

    # 2) 对重名函数做“按区域重命名”
    cleaned = disambiguate_overloaded_functions(cleaned)

    # 3) 如有修改，写回文件
    if cleaned != template_text:
        try:
            smt_template_path.write_text(cleaned, encoding="utf-8")
            print(f"   💾 已用清洗 + 重名函数重命名后的模板覆盖原文件: {smt_template_path}")
        except Exception as io_err:
            print("   ⚠️ 写回清洗后模板到文件失败：")
            print(f"      {io_err}")
    else:
        print("   ℹ️ 清洗前后模板内容相同，无需写回文件。")

    # 4) 尝试做一下语法检查（仅提示用，不影响写回）
    try:
        import z3  # type: ignore
    except ImportError:
        print("   ℹ️ 未安装 python z3，跳过严格语法解析，仅做正则级别的检查。")
    else:
        # 原始模板
        try:
            import textwrap
            z3.parse_smt2_string(template_text)
            print("   ✅ Z3 语法解析通过（原始模板）。")
        except Exception as e:
            print("   ❌ Z3 解析原始模板失败：")
            print(f"      {e}")

        # 清洗后模板
        try:
            z3.parse_smt2_string(cleaned)
            print("   ✅ Z3 语法解析通过（清洗后模板）。")
        except Exception as e:
            print("   ❌ Z3 解析清洗后模板失败（但已写回，只做提示）：")
            print(f"      {e}")

    # 5) 正则扫描重复声明（这里用清洗后的内容做扫描，更符合当前文件状态）
    sort_pattern = re.compile(r"\(declare-sort\s+([^\s\)]+)")
    fun_pattern = re.compile(r"\(declare-fun\s+([^\s\)]+)\s+\(([^)]*)\)\s+([^\s\)]+)\)")
    const_pattern = re.compile(r"\(declare-const\s+([^\s\)]+)\s+([^\s\)]+)\)")

    from collections import defaultdict

    sort_counts = defaultdict(list)  # name -> [line1, line2, ...]
    fun_counts = defaultdict(list)
    const_counts = defaultdict(list)

    lines = cleaned.splitlines()
    for lineno, line in enumerate(lines, start=1):
        # 去掉前导空白，纯注释行直接跳过
        stripped = line.lstrip()
        if stripped.startswith(';') or stripped == "":
            continue

        # 只在“非注释部分”里查找声明
        for m in sort_pattern.finditer(stripped):
            name = m.group(1)
            sort_counts[name].append(lineno)
        for m in fun_pattern.finditer(stripped):
            name = m.group(1)
            fun_counts[name].append(lineno)
        for m in const_pattern.finditer(stripped):
            name = m.group(1)
            const_counts[name].append(lineno)

    has_dup = False
    for name, locs in sort_counts.items():
        if len(locs) > 1:
            has_dup = True
            print(f"   ⚠️ Sort '{name}' 在模板中重复声明 {len(locs)} 次，行号: {locs}")
    for name, locs in fun_counts.items():
        if len(locs) > 1:
            has_dup = True
            print(f"   ⚠️ 函数 '{name}' 在模板中重复声明 {len(locs)} 次，行号: {locs}")
    for name, locs in const_counts.items():
        if len(locs) > 1:
            has_dup = True
            print(f"   ⚠️ 常量 '{name}' 在模板中重复声明 {len(locs)} 次，行号: {locs}")

    if not has_dup:
        print("   ✅ 未检测到显式的重复声明（declare-sort/fun/const）。")

    # 6) 检测符号角色冲突（既是 sort 又是 fun/const 等）
    from collections import defaultdict as dd

    symbol_kinds = dd(set)
    for name in sort_counts:
        symbol_kinds[name].add("sort")
    for name in fun_counts:
        symbol_kinds[name].add("fun")
    for name in const_counts:
        symbol_kinds[name].add("const")

    conflict_found = False
    for name, kinds in symbol_kinds.items():
        if len(kinds) > 1:
            conflict_found = True
            kinds_str = ", ".join(sorted(kinds))
            print(f"   ⚠️ 符号 '{name}' 同时被用作 {kinds_str}，可能存在声明冲突。")

    if not conflict_found:
        print("   ✅ 未检测到显式的符号角色冲突。")

        # ✅ [新增] 6) 可满足性检查 - 这是关键！
        print("\n   🧮 检查模板逻辑可满足性...")
        try:
            import z3

            # 解析清洗后的模板
            assertions = z3.parse_smt2_string(cleaned)
            print(f"   ℹ️ 模板包含 {len(assertions)} 个断言/公理")

            # ✅ [新增] 分析公理复杂度
            _analyze_assertion_complexity(assertions, cleaned)

            # 创建求解器并添加所有断言
            solver = z3.Solver()
            solver.set("timeout", 60000)  # 1分钟初次检查

            for a in assertions:
                solver.add(a)

            # 检查可满足性
            print("\n   ⏳ 正在进行可满足性检查（最多1分钟）...")
            result = solver.check()

            if result == z3.sat:
                print("   ✅ 模板逻辑可满足性检查通过 (SAT)")
            elif result == z3.unsat:
                print("   ❌ 模板逻辑不可满足 (UNSAT) - 公理内部存在矛盾！")
                print("   ⚠️ 这将导致验证时立即失败，无论输入什么数据")

                # 尝试定位问题公理
                print("\n   🔍 尝试定位矛盾的公理...")
                _find_conflicting_axioms(assertions, cleaned)
            else:
                print(f"   ⚠️ 求解器返回 UNKNOWN")
                print("\n   🔍 开始深度诊断...")
                _diagnose_unknown_result(assertions, cleaned)

        except ImportError:
            print("   ℹ️ 未安装 z3，跳过可满足性检查")
        except Exception as e:
            print(f"   ⚠️ 可满足性检查失败: {e}")
            import traceback
            traceback.print_exc()

        # 返回清洗后的模板文本
        return cleaned

    # 返回（可能已清洗 + 重命名的）模板文本，方便调用方更新 validator 内部缓存

    return cleaned


def _analyze_assertion_complexity(assertions, template_text: str):
    """分析公理的复杂度，帮助理解为什么求解器可能返回UNKNOWN"""

    print("\n   📊 公理复杂度分析:")
    print("   " + "-" * 60)

    stats = {
        'total': len(assertions),
        'with_forall': 0,
        'with_exists': 0,
        'with_nested_quantifiers': 0,
        'with_string_ops': 0,
        'with_implications': 0,
        'simple': 0,
    }

    complex_assertions = []  # 记录复杂公理的索引

    for i, a in enumerate(assertions):
        a_str = str(a)

        has_forall = 'ForAll' in a_str or 'forall' in a_str.lower()
        has_exists = 'Exists' in a_str or 'exists' in a_str.lower()

        if has_forall:
            stats['with_forall'] += 1
        if has_exists:
            stats['with_exists'] += 1
        if has_forall and has_exists:
            stats['with_nested_quantifiers'] += 1
            complex_assertions.append(i)

        # 检查字符串操作
        if any(op in a_str for op in ['String', 'str.', 'Str', '\"']):
            stats['with_string_ops'] += 1

        # 检查蕴含
        if 'Implies' in a_str or '=>' in a_str:
            stats['with_implications'] += 1

        # 简单公理（无量词）
        if not has_forall and not has_exists:
            stats['simple'] += 1

    print(f"   总断言数:           {stats['total']}")
    print(f"   含 ForAll:          {stats['with_forall']} ({100 * stats['with_forall'] // max(1, stats['total'])}%)")
    print(f"   含 Exists:          {stats['with_exists']} ({100 * stats['with_exists'] // max(1, stats['total'])}%)")
    print(f"   嵌套量词 (复杂):    {stats['with_nested_quantifiers']}")
    print(f"   含字符串操作:       {stats['with_string_ops']}")
    print(f"   含蕴含 (=>):        {stats['with_implications']}")
    print(f"   简单断言 (无量词):  {stats['simple']}")
    print("   " + "-" * 60)

    # 警告
    if stats['with_nested_quantifiers'] > 0:
        print(f"   ⚠️ 发现 {stats['with_nested_quantifiers']} 个嵌套量词公理，这是导致 UNKNOWN 的主要原因")

    if stats['with_string_ops'] > 50:
        print(f"   ⚠️ 大量字符串操作 ({stats['with_string_ops']})，可能导致求解困难")

    if stats['with_forall'] > 100:
        print(f"   ⚠️ 大量全称量词 ({stats['with_forall']})，求解复杂度指数级增长")

    return stats, complex_assertions


def _diagnose_unknown_result(assertions, template_text: str):
    """当求解器返回UNKNOWN时，进行深度诊断"""
    import z3

    print("\n   " + "=" * 70)
    print("   🔬 深度诊断: 分析为什么求解器返回 UNKNOWN")
    print("   " + "=" * 70)

    # 1. 分批检查
    print("\n   📦 阶段1: 分批检查（找出问题区域）")
    print("   " + "-" * 60)

    batch_size = 100
    problem_batch_start = -1
    last_sat_batch = -1

    for batch_start in range(0, len(assertions), batch_size):
        batch_end = min(batch_start + batch_size, len(assertions))

        solver = z3.Solver()
        solver.set("timeout", 15000)  # 每批15秒

        # 添加从头到当前批次的所有断言
        for a in assertions[:batch_end]:
            solver.add(a)

        result = solver.check()
        status_icon = "✅" if result == z3.sat else ("❌" if result == z3.unsat else "❓")
        print(f"   {status_icon} 断言 1-{batch_end}: {result}")

        if result == z3.sat:
            last_sat_batch = batch_end
        elif result == z3.unsat:
            print(f"   ❌ 发现矛盾！问题在断言 {last_sat_batch + 1}-{batch_end} 中")
            problem_batch_start = last_sat_batch
            break
        elif result == z3.unknown:
            print(f"   ❓ 从断言 {last_sat_batch + 1}-{batch_end} 开始变成 unknown")
            problem_batch_start = last_sat_batch
            break

    # 2. 如果找到问题区域，进一步缩小范围
    if problem_batch_start >= 0:
        print(
            f"\n   🔍 阶段2: 在断言 {problem_batch_start + 1}-{min(problem_batch_start + batch_size + 50, len(assertions))} 中精确定位")
        print("   " + "-" * 60)

        # 获取assert位置信息
        assert_positions = _scan_assert_positions(template_text)

        solver = z3.Solver()
        solver.set("timeout", 5000)

        # 添加问题区域之前的断言
        for a in assertions[:problem_batch_start]:
            solver.add(a)

        found_problems = []

        # 逐个添加问题区域的断言
        for i in range(problem_batch_start, min(problem_batch_start + batch_size + 50, len(assertions))):
            solver.push()
            solver.add(assertions[i])

            result = solver.check()

            if result != z3.sat:
                found_problems.append((i, result))

                if len(found_problems) <= 5:  # 只显示前5个
                    print(f"\n   {'❌' if result == z3.unsat else '❓'} 第 {i + 1} 个断言导致 {result}")

                    # 显示行号和上下文
                    if i < len(assert_positions):
                        pos = assert_positions[i]
                        print(f"      📍 文件位置: 第 {pos['start_line']} 行")
                        _print_context_around_line(template_text, pos['start_line'], 2, 3)

                    print(f"      Z3 表示: {str(assertions[i])[:150]}...")

                solver.pop()
                # 不添加这个有问题的断言，继续检查其他的
            else:
                solver.pop()
                solver.add(assertions[i])

        if len(found_problems) > 5:
            print(f"\n   ... 还有 {len(found_problems) - 5} 个问题断言未显示")

        if found_problems:
            print(f"\n   📋 问题断言汇总 (共 {len(found_problems)} 个):")
            for i, (idx, res) in enumerate(found_problems[:10]):
                if idx < len(assert_positions):
                    line = assert_positions[idx]['start_line']
                    print(f"      - 第 {idx + 1} 个断言 (第 {line} 行): {res}")
                else:
                    print(f"      - 第 {idx + 1} 个断言: {res}")

    # 3. 尝试不同的求解策略
    print(f"\n   🎯 阶段3: 尝试不同的求解策略")
    print("   " + "-" * 60)

    strategies = [
        ("默认策略", {}),
        ("MBQI (量词实例化)", {"smt.mbqi": True, "smt.auto_config": False}),
        ("无MBQI", {"smt.mbqi": False}),
        ("激进量词", {"smt.qi.eager_threshold": 10}),
        ("简化模式", {"smt.auto_config": False, "smt.mbqi": False}),
    ]

    for name, settings in strategies:
        solver = z3.Solver()
        solver.set("timeout", 20000)  # 20秒
        for k, v in settings.items():
            try:
                solver.set(k, v)
            except:
                pass

        for a in assertions:
            solver.add(a)

        result = solver.check()
        status_icon = "✅" if result == z3.sat else ("❌" if result == z3.unsat else "❓")
        print(f"   {status_icon} {name}: {result}")

        if result == z3.sat:
            print(f"   🎉 策略 '{name}' 成功！建议在代码中使用此策略")
            break
        elif result == z3.unsat:
            print(f"   ❌ 策略 '{name}' 发现矛盾！模板确实有问题")
            break

    # 4. 给出建议
    print(f"\n   💡 诊断建议:")
    print("   " + "-" * 60)
    print("   1. 检查上述定位到的问题公理")
    print("   2. 简化复杂的量词公式，特别是嵌套的 ForAll + Exists")
    print("   3. 考虑将某些复杂约束注释掉进行测试")
    print("   4. 字符串比较约束可能导致求解困难，考虑使用枚举类型替代")
    print("   5. 如果所有策略都是 unknown，可能模板本身没问题，只是太复杂")
    print("   " + "=" * 70)


def _scan_assert_positions(template_text: str):
    """
    扫描模板文本，找出所有 (assert ...) 语句的位置信息

    Returns:
        List of {
            'index': int,           # 第几个assert (0-based)
            'start_line': int,      # 起始行号 (1-based)
            'end_line': int,        # 结束行号 (1-based)
            'content': str,         # assert 内容（可能跨多行）
        }
    """
    lines = template_text.splitlines()
    asserts = []

    i = 0
    assert_index = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()

        # 跳过注释和空行
        if stripped.startswith(';') or stripped == '':
            i += 1
            continue

        # 检查是否是 assert 开始
        if '(assert' in stripped or stripped.startswith('(assert'):
            start_line = i + 1  # 1-based

            # 收集完整的 assert（可能跨多行）
            content_lines = [line]
            paren_count = line.count('(') - line.count(')')

            j = i + 1
            while paren_count > 0 and j < len(lines):
                next_line = lines[j]
                content_lines.append(next_line)
                paren_count += next_line.count('(') - next_line.count(')')
                j += 1

            end_line = j  # 1-based
            content = '\n'.join(content_lines)

            asserts.append({
                'index': assert_index,
                'start_line': start_line,
                'end_line': end_line,
                'content': content,
            })

            assert_index += 1
            i = j
        else:
            i += 1

    return asserts


def _print_context_around_line(template_text: str, line_no: int, context_before: int = 3, context_after: int = 5):
    """打印指定行号周围的上下文"""
    lines = template_text.splitlines()

    start = max(0, line_no - 1 - context_before)
    end = min(len(lines), line_no + context_after)

    print(f"\n      📄 上下文 (第 {start + 1} - {end} 行):")
    print("      " + "-" * 70)

    for i in range(start, end):
        line_num = i + 1
        prefix = "  →→ " if line_num == line_no else "     "
        # 截断过长的行
        line_content = lines[i][:120]
        if len(lines[i]) > 120:
            line_content += "..."
        print(f"      {prefix}{line_num:5d}: {line_content}")

    print("      " + "-" * 70)


def _find_conflicting_axioms(assertions, template_text: str = None):
    """
    增量添加公理，找出导致UNSAT的那个
    新增：显示行号和上下文
    """
    import z3

    # 扫描所有 assert 的位置
    assert_positions = []
    if template_text:
        assert_positions = _scan_assert_positions(template_text)
        print(f"   ℹ️ 模板中共有 {len(assert_positions)} 个 assert 语句")

        if len(assert_positions) != len(assertions):
            print(f"   ⚠️ 注意: 扫描到的 assert 数量 ({len(assert_positions)}) "
                  f"与 Z3 解析的断言数量 ({len(assertions)}) 不一致")
            print(f"   ⚠️ 行号定位可能有偏差（某些声明也被计入断言）")

    solver = z3.Solver()
    solver.set("timeout", 5000)  # 每个公理5秒超时

    conflicts = []

    for i, a in enumerate(assertions):
        solver.push()
        solver.add(a)

        result = solver.check()
        if result == z3.unsat:
            print(f"\n   {'=' * 70}")
            print(f"   ❌ 第 {i + 1} 个公理导致矛盾:")

            # 尝试找到对应的行号
            if i < len(assert_positions):
                pos = assert_positions[i]
                start_line = pos['start_line']
                end_line = pos['end_line']

                if start_line == end_line:
                    print(f"      📍 文件位置: 第 {start_line} 行")
                else:
                    print(f"      📍 文件位置: 第 {start_line} - {end_line} 行")

                # 打印上下文
                if template_text:
                    _print_context_around_line(template_text, start_line)

                conflicts.append({
                    'assertion_index': i,
                    'start_line': start_line,
                    'end_line': end_line,
                })
            else:
                print(f"      ⚠️ 无法定位行号（断言索引超出范围）")

            print(f"      Z3 表示: {str(a)[:200]}...")
            print(f"   {'=' * 70}")

            # 不回滚，继续检查是否有更多冲突
            solver.pop()
        else:
            solver.pop()
            solver.add(a)  # 保留这个公理

    # 打印汇总和修复建议
    print(f"\n   {'#' * 70}")
    print(f"   # 冲突汇总: 发现 {len(conflicts)} 个矛盾公理")
    print(f"   {'#' * 70}")

    if conflicts:
        print("\n   📋 矛盾公理位置列表（方便复制）:")
        for c in conflicts:
            print(f"      - 第 {c['start_line']} 行 (断言 #{c['assertion_index'] + 1})")

        print("\n   💡 修复建议:")
        print("   " + "-" * 70)
        print("   1. 打开 SMT 模板文件，定位到上述行号")
        print("   2. 如果是枚举值约束（如 roleValue == 'X'），合并为 OR 形式:")
        print("      ")
        print("      ❌ 错误写法（每个值一个公理，互相矛盾）:")
        print("         (assert (forall (r) (=> cond (= (f r) \"A\"))))")
        print("         (assert (forall (r) (=> cond (= (f r) \"B\"))))")
        print("      ")
        print("      ✅ 正确写法（合并为 OR）:")
        print("         (assert (forall (r) (=> cond (or (= (f r) \"A\")")
        print("                                         (= (f r) \"B\")))))")
        print("      ")
        print("   3. 或者临时注释掉冲突的公理进行测试:")
        print("      ; (assert ...冲突的公理...)")
        print("   " + "-" * 70)
    else:
        print("\n   ✅ 未检测到具体的单个矛盾公理")
        print("   💡 可能是多个公理组合导致矛盾，需要人工分析")


def _print_error_context_from_smt_script(
        smt_script: str,
        error_msg: str,
        context_lines: int = 3,
) -> None:
    """
    从 Z3 的错误信息中提取 "line N"，
    然后在 SMT 脚本中打印该行附近若干行，方便快速定位问题。
    """
    if not smt_script or not error_msg:
        return

    m = re.search(r"line\s+(\d+)", error_msg)
    if not m:
        return

    try:
        line_no = int(m.group(1))
    except ValueError:
        return

    lines = smt_script.splitlines()
    if not (1 <= line_no <= len(lines)):
        return

    start = max(1, line_no - context_lines)
    end = min(len(lines), line_no + context_lines)

    print(f"   🔍 错误附近 SMT 行（约第 {line_no} 行）：")
    for i in range(start, end + 1):
        prefix = "->" if i == line_no else "  "
        print(f"   {prefix} {i:5d}: {lines[i - 1]}")


def diagnose_smt(
        smt_template_file: Path,
        mapping_file: Optional[Path],
        arxml_file: Optional[Path],
):
    print("=" * 80)
    print("🔍 SMT 模板 & 映射诊断工具")
    print("=" * 80)
    print()

    print(f"📂 SMT 模板文件: {smt_template_file}")
    print(f"📂 SMT 映射文件: {mapping_file if mapping_file else '(未指定 / 未找到)'}")
    if arxml_file:
        print(f"📂 测试用 ARXML: {arxml_file}")
    print()

    # 1) 尝试构造 SMTValidator
    try:
        validator = SMTValidator(
            smt_template_file=str(smt_template_file),
            mapping_file=str(mapping_file) if mapping_file else None,
        )
    except Exception as e:
        print("❌ SMTValidator 初始化失败：")
        print(f"   {e}")
        return

    # 2) 打印模板 / mapping 的加载情况
    print("-" * 80)
    print("步骤1：检查 SMT 模板与 mapping 基本信息")
    print("-" * 80)

    # 这些属性名需要与 smt_validator.py 中保持一致
    template_text = getattr(validator, "smt_template_text", "")
    template_sorts = getattr(validator, "template_sorts", set())
    template_functions = getattr(validator, "template_functions", {})
    template_ctors = getattr(validator, "template_constructors", {})

    mapping = getattr(validator, "mapping", [])

    print(f"📝 模板字符总数: {len(template_text)}")
    print(f"🔤 模板中解析出的 sort 数量: {len(template_sorts)}")
    print(f"🔧 模板中解析出的函数声明数量: {len(template_functions)}")
    print(f"🏗️  模板中解析出的构造器数量: {len(template_ctors)}")
    print(f"🗺️  mapping 条目数量: {len(mapping) if mapping else 0}")
    if not template_text:
        print("⚠️ 警告：smt_template_text 为空，模板似乎没有正确加载。")
    if mapping is None:
        print("⚠️ 警告：mapping 为 None，可能未传入 mapping 文件。")
    elif len(mapping) == 0:
        print("⚠️ 提示：mapping 已加载，但内容为空（或结构不符合预期）。")

    # 2.1 对模板做语法 & 重复声明检查
    print("\n" + "-" * 80)
    print("步骤1-补充：SMT 模板语法与重复声明检查")
    print("-" * 80)
    if template_text:
        # ✅ 传入模板路径，并接收清洗后的文本
        template_text = _check_template_syntax_and_duplicates(
            template_text,
            smt_template_file,
        )
        # 让当前 validator 使用清洗后的模板文本
        validator.smt_template_text = template_text
        # 如需依赖解析出的 sorts / functions，可以选择性重新解析
        try:
            validator._parse_template(template_text)
        except Exception as e:
            print(f"⚠️ 重新解析清洗后的模板失败：{e}")
    else:
        print("⚠️ 模板内容为空，无法做语法和重复声明检查。")

    # 3) 如有 ARXML，做一次约束生成 + 求解器测试
    print("\n" + "-" * 80)
    print("步骤2：使用 ARXML 进行 SMT 约束生成与求解测试（如有）")
    print("-" * 80)

    if not arxml_file:
        print("💡 未指定 ARXML 文件，跳过约束生成测试。")
        print("   使用方法示例：")
        print("     python check_smt.py path/to/constraints.smt2 path/to/mapping_smt.json path/to/example.arxml")
        return

    if not arxml_file.exists():
        print(f"❌ ARXML 文件不存在: {arxml_file}")
        return

    try:
        xml_text = arxml_file.read_text(encoding="utf-8")
    except Exception as e:
        print(f"❌ 读取 ARXML 失败: {e}")
        return

    try:
        result = validator.validate_constraints(xml_text)
    except Exception as e:
        print("❌ 调用 validate_constraints 失败：")
        print(f"   {e}")
        return

    # 与 smt_validator.validate_constraints 的返回结构对齐
    valid = result.get("valid", None)
    constraint_count = result.get("constraint_count", None)
    solver_info = result.get("solver", {}) or {}
    diagnosis = result.get("diagnosis", {})

    print(f"📊 生成的 SMT 约束条数: {constraint_count}")
    print(f"✅ valid 标记: {valid}")
    print(f"🧠 求解器原始返回: {solver_info}")

    # 解析求解器返回，给出“报错种类”的友好描述
    if "error" in solver_info:
        print("❌ 求解器报错（parse/solve failed）：")
        print(f"   {solver_info['error']}")
    else:
        status = solver_info.get("status", "")
        if status:
            print(f"   ℹ️ 求解器 status: {status}")
            if "unsat" in status:
                print("   ➤ 约束整体为 UNSAT（存在冲突）。")
            elif "sat" in status:
                print("   ➤ 约束整体为 SAT（当前无冲突）。")
            elif "unknown" in status.lower():
                print("   ➤ Z3 返回 unknown，可能是超时或使用了不支持的特性。")

    # 如果诊断中也带有 error 信息，一并打印
    if isinstance(diagnosis, dict) and diagnosis.get("error"):
        print("❌ 增量诊断模块错误信息：")
        print(f"   {diagnosis['error']}")

    # 可选打印部分 SMT 文本做人工核查
    smt_script = result.get("smt", "")
    print("\n--- SMT 脚本前 40 行预览 ---")
    if smt_script:
        lines = smt_script.splitlines()
        for i, line in enumerate(lines[:40], start=1):
            print(f"{i:4d}: {line}")
        if len(lines) > 40:
            print("... (后续行已省略)")
    else:
        print("⚠️ 未在结果中找到 'smt' 字段，无法预览脚本。")

    # ✅ 如果有 parse/solve failed，尝试根据 error 中的行号，在 SMT 文本中打印上下文
    if "error" in solver_info and smt_script:
        _print_error_context_from_smt_script(smt_script, solver_info["error"])


def main():
    script_dir = Path(__file__).parent

    # 参考 check_shacl.py 的风格，准备一些候选路径
    smt_template_candidates = [
        script_dir / "autosar_constraints.smt2",
        script_dir / "constraints.smt2",
        Path("autosar_constraints.smt2"),
        Path("constraints.smt2"),
        Path("src/validation/data/autosar_constraints.smt2"),
        Path("../src/validation/data/autosar_constraints.smt2"),
        Path(r"C:\Users\54239\PycharmProjects\AI_XmlGenerator\src\validation\data\autosar_constraints.smt2"),
    ]

    mapping_candidates = [
        script_dir / "mapping_smt.json",
        script_dir / "autosar_smt_mapping.json",
        Path("mapping_smt.json"),
        Path("autosar_smt_mapping.json"),
        Path("src/validation/data/mapping_smt.json"),
        Path("../src/validation/data/mapping_smt.json"),
        Path(r"C:\Users\54239\PycharmProjects\AI_XmlGenerator\src\validation\data\mapping_smt.json"),
    ]

    smt_template_file = find_first_existing(smt_template_candidates)
    mapping_file = find_first_existing(mapping_candidates)

    # 命令行优先：允许手动指定路径
    # 用法:
    #   python check_smt.py <smt_template> [mapping_json] [test.arxml]
    args = sys.argv[1:]
    arxml_file = None

    if len(args) >= 1:
        smt_template_file = Path(args[0])
    if len(args) >= 2:
        mapping_file = Path(args[1])
    if len(args) >= 3:
        arxml_file = Path(args[2])

    if not smt_template_file or not smt_template_file.exists():
        print("❌ 未找到 SMT 模板文件 (*.smt2)")
        print("   请检查 smt_template_candidates 列表或通过命令行显式指定。")
        sys.exit(1)

    if mapping_file and not mapping_file.exists():
        print(f"⚠️ 映射文件不存在: {mapping_file}，将以无 mapping 模式运行。")
        mapping_file = None

    diagnose_smt(smt_template_file, mapping_file, arxml_file)


if __name__ == "__main__":
    main()