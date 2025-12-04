# smt_validator.py
# Template-driven, mapping-driven SMT validator for AUTOSAR ARXML.
# Loads SMT template, mapping JSON (default: src/validation/data/mapping_smt.json),
# parses ARXML content, generates SMT (decls + facts) according to mapping,
# and invokes Z3 (CLI if available, else python z3).
#
# External API preserved:
#   v = SMTValidator(smt_template_file, mapping_file=None)
#   result = v.validate_constraints(xml_content: str) -> dict
#
# Minimal-intrusion design: mapping_file defaults to "src/validation/data/mapping_smt.json".
# If mapping not found, validator will attempt best-effort template-driven mapping and warn.

import os
import re
import json
import tempfile
import subprocess
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple
import xml.etree.ElementTree as ET

# -------------------------
# Utility helpers
# -------------------------
def _sanitize_ident(s: str) -> str:
    s = str(s)
    s = re.sub(r'[^A-Za-z0-9_\-]', '_', s)
    s = re.sub(r'__+', '_', s).strip('_')
    if not s:
        return "id"
    if not re.match(r'^[A-Za-z_]', s):
        s = "_" + s
    return s

def _xml_tag_local(tag: str) -> str:
    if tag is None:
        return ""
    if '}' in tag:
        return tag.split('}', 1)[1]
    return tag

def _first_text(elem: Optional[ET.Element], child_tag: str) -> Optional[str]:
    if elem is None:
        return None
    c = elem.find(child_tag)
    if c is not None and c.text:
        return c.text.strip()
    return None

# -------------------------
# SMT Validator class
# -------------------------
class SMTValidator:
    def __init__(self, smt_template_file: str, mapping_file: Optional[str] = None, xsd_index_file: Optional[str] = None,
                 **kwargs):
        """
        smt_template_file: path to constraints.smt2 template (kept as-is)
        mapping_file: path to JSON mapping (default 'src/validation/data/mapping_smt.json')
        """
        self.smt_template_file = smt_template_file
        self.mapping_file = mapping_file

        # 🔥 [新增] 继承关系表 { "ParentTag": {"ChildTag1", "ChildTag2"} }
        self.inheritance_map = {}
        if xsd_index_file:
            self._load_inheritance_map(xsd_index_file)

        self.smt_template_text: str = ""
        self.template_sorts: Set[str] = set()
        self.template_functions: Dict[str, List[Tuple[str, List[str], str]]] = {}
        self.template_constructors: Dict[str, List[Tuple[str, List[str]]]] = {}

        # ✅ [新增] 谓词基础名到变体的映射，用于处理重命名后的谓词匹配
        self.predicate_base_to_variants: Dict[str, List[Tuple[str, List[str], str, int]]] = {}

        # ✅ [新增] 精确谓词名到签名的映射，用于快速查找
        self.predicate_signatures: Dict[str, Tuple[List[str], str]] = {}

        # ✅ [新增] 跳过的谓词记录
        self.skipped_predicates: List[Dict[str, Any]] = []
        # 新增：已经打印过的 "跳过谓词" 键，避免重复噪音
        self._skip_warned_keys: Set[Tuple[Any, ...]] = set()

        # ✅ [新增] 谓词匹配缓存，避免重复匹配
        self.predicate_match_cache: Dict[Tuple[str, int], Optional[str]] = {}

        # ========== 🔥 [新增] 选择性加载SMT的数据结构 ==========
        # 模板声明部分（declare-sort, declare-fun, declare-datatype等）
        self.template_declarations: str = ""
        # 模板断言部分：{ assert_id -> { "text": str, "predicates": Set[str] } }
        self.template_assertions: Dict[int, Dict[str, Any]] = {}
        # 谓词到断言ID的映射：{ predicate_name -> Set[assert_id] }
        self.predicate_to_assertions: Dict[str, Set[int]] = {}
        # ========== END ==========

        # runtime generated
        self.smt_decls: List[str] = []
        self.smt_facts: List[str] = []
        self.declared_consts: Set[str] = set()

        # 🔧 新增：记录运行时自动声明过的 sort，避免重复 declare-sort
        self.auto_declared_sorts: Set[str] = set()

        # ✅ 新增：每个 SMT 断言对应的元信息
        self.fact_metadata: List[Dict[str, Any]] = []

        # mapping loaded from JSON
        self.mapping: List[Dict[str, Any]] = []

        # parent map cache for XML tree navigation
        self._parent_map = None
        self._last_root = None

        # load artifacts
        self._load_smt_template()
        self._load_mapping()

        self.wiring_report: Optional[Dict[str, Any]] = None
        try:
            self.wiring_report = self.analyze_constraint_wiring()
        except Exception as e:
            print(f"[WARN] analyze_constraint_wiring 执行失败: {e}")
            self.wiring_report = None

        self.verbosity = kwargs.get("verbosity", 1)  # 0=quiet,1=info,2=diag,3=debug
        self.enable_runtime_wiring_diag = kwargs.get("enable_runtime_wiring_diag", False)

        self.cross_file_resolver = None
        self.z3_cli_available = self._z3_cli_available()
    # -------------------------
    # Loading and parsing SMT template
    # -------------------------
    def _load_smt_template(self):
        try:
            with open(self.smt_template_file, 'r', encoding='utf-8') as f:
                txt = f.read()
            self.smt_template_text = txt
            self._parse_template(txt)
        except Exception as e:
            # absent template is critical, but keep going with empty template
            self.smt_template_text = ""
            self.template_sorts = set()
            self.template_functions = {}
            self.template_constructors = {}
            print(f"[WARN] Could not load SMT template '{self.smt_template_file}': {e}")

    def _load_inheritance_map(self, index_file: str):
        """从 XsdIndex.arxml 加载继承关系"""
        try:
            tree = ET.parse(index_file)
            root = tree.getroot()
            count = 0

            # 清空旧的映射
            self.inheritance_map = {}

            for group in root.findall("group"):
                parent = group.get("name")
                complex_types = group.get("complexTypes", "")

                if not parent or not complex_types:
                    continue

                # 🔥 [优化] 直接解析所有类型，不做排除
                # 如果 XsdIndex 写的是 //A//B，那么 valid_tags 就是 {A, B}
                # 如果 XsdIndex 写的是 //Parent，那么 valid_tags 就是 {Parent}
                valid_tags = set(t for t in complex_types.split('//') if t)

                if valid_tags:
                    self.inheritance_map[parent] = valid_tags
                    count += 1

            print(f"[INFO] SMT Validator loaded {count} inheritance groups from XsdIndex")
        except Exception as e:
            print(f"[WARN] Failed to load XsdIndex: {e}")

    def _parse_template(self, txt: str):
        """
        解析SMT模板，提取sorts、functions、constructors
        并构建谓词基础名到变体的映射（处理check_smt.py的重命名）

        🔥 [新增] 分离声明部分和断言部分，支持选择性加载
        🔥 [新增] 标记使用不完备理论的断言
        """
        # 重置相关数据结构
        self.template_sorts = set()
        self.template_functions = {}
        self.template_constructors = {}
        self.predicate_base_to_variants = {}
        self.predicate_signatures = {}
        self.predicate_match_cache = {}

        # 🔥 [新增] 重置选择性加载的数据结构
        self.template_declarations = ""
        self.template_assertions = {}
        self.predicate_to_assertions = {}

        # ========== 1. 先解析声明以提取sorts和functions ==========
        # 这必须在解析断言之前完成，否则 _extract_predicates_from_sexp 无法正确识别谓词

        # parse declare-sort
        for m in re.finditer(r'\(declare-sort\s+([A-Za-z0-9_\-]+)\s+\d+\)', txt):
            self.template_sorts.add(m.group(1))

        # parse declare-fun (name (args) RET)
        fun_pattern = r'\(declare-fun\s+([A-Za-z0-9_\-]+)\s*\(([^\)]*)\)\s*([A-Za-z0-9_\-]+)\)'
        for m in re.finditer(fun_pattern, txt, re.DOTALL):
            fname = m.group(1)
            args_txt = m.group(2).strip()
            ret = m.group(3)
            arg_types = []
            if args_txt:
                arg_types = [tok for tok in re.split(r'\s+', args_txt) if tok]

            key = ret
            self.template_functions.setdefault(key, []).append((fname, arg_types, ret))

            # ✅ 存储精确签名
            self.predicate_signatures[fname] = (arg_types, ret)

            # ✅ 解析基础名和后缀数字
            base_name, suffix_num = self._parse_predicate_name_suffix(fname)

            # ✅ 构建基础名到变体的映射
            variant_info = (fname, arg_types, ret, suffix_num)
            self.predicate_base_to_variants.setdefault(base_name, []).append(variant_info)

        # ✅ 对每个基础名的变体按后缀数字排序
        for base_name in self.predicate_base_to_variants:
            self.predicate_base_to_variants[base_name].sort(key=lambda x: x[3])

        # parse declare-datatypes for constructors
        # parse declare-datatypes for constructors
        for m in re.finditer(
                r'\(declare-datatypes\s*\([^)]*\)\s*\(\s*\(\s*([A-Za-z0-9_\-]+)\s+([^\)]+)\)\s*\)\)',
                txt,
                re.S,
        ):
            dtype = m.group(1)
            body = m.group(2)

            # ✅ 新增：datatype 名本身也是一个已声明的 sort
            # 避免后面 _declare_const 再对它做 (declare-sort dtype 0)，导致 "sort already declared/defined"
            self.template_sorts.add(dtype)

            ctors = []
            for cm in re.finditer(r'\(\s*([A-Za-z0-9_\-]+)\s*(\([^\)]*\))?', body):
                ctor = cm.group(1)
                args = cm.group(2)
                arg_types = []
                if args:
                    pairs = re.findall(r'\(\s*[A-Za-z0-9_\-]+\s+([A-Za-z0-9_\-]+)\s*\)', args)
                    arg_types = pairs
                ctors.append((ctor, arg_types))
            if ctors:
                self.template_constructors.setdefault(dtype, []).extend(ctors)

        # ========== 2. 分离声明和断言 ==========
        declaration_lines = []
        assertion_id = 0

        # 🔥 [新增] 不完备理论关键字
        incomplete_theory_keywords = [
            'Array', 'select', 'store', 'const-array',  # Array 理论
            'Seq', 'seq.', 'seq.len', 'seq.++', 'seq.nth', 'seq.extract',  # Sequence 理论
            'String', 'str.', 'str.len', 'str.++', 'str.contains', 'str.substr',  # String 理论
            'str.at', 'str.indexof', 'str.replace', 'str.prefixof', 'str.suffixof',
            're.', 're.++', 're.union', 're.inter',  # 正则表达式
        ]

        def _uses_incomplete_theory(sexp_text: str) -> bool:
            """检查S表达式是否使用了不完备理论"""
            for kw in incomplete_theory_keywords:
                if kw in sexp_text:
                    return True
            return False

        def _count_quantifier_depth(sexp_text: str) -> int:
            """估算量词嵌套深度"""
            # 简化实现：计算forall和exists的总数作为复杂度指标
            forall_count = sexp_text.count('forall')
            exists_count = sexp_text.count('exists')
            return forall_count + exists_count

        # 使用正则匹配顶层S表达式
        def extract_top_level_sexps(text: str) -> List[Tuple[int, int, str]]:
            """提取所有顶层S表达式，返回 [(start, end, content), ...]"""
            results = []
            i = 0
            while i < len(text):
                # 跳过空白和注释
                while i < len(text):
                    if text[i] in ' \t\n\r':
                        i += 1
                    elif text[i] == ';':
                        # 跳过整行注释
                        while i < len(text) and text[i] != '\n':
                            i += 1
                        if i < len(text):
                            i += 1
                    else:
                        break

                if i >= len(text):
                    break

                if text[i] == '(':
                    start = i
                    depth = 1
                    i += 1
                    while i < len(text) and depth > 0:
                        if text[i] == '(':
                            depth += 1
                        elif text[i] == ')':
                            depth -= 1
                        elif text[i] == ';':
                            # 跳过行内注释
                            while i < len(text) and text[i] != '\n':
                                i += 1
                            continue
                        elif text[i] == '"':
                            # 跳过字符串
                            i += 1
                            while i < len(text) and text[i] != '"':
                                if text[i] == '\\':
                                    i += 1
                                i += 1
                            # 跳过闭合引号
                        i += 1
                    end = i
                    content = text[start:end]
                    results.append((start, end, content))
                else:
                    i += 1
            return results

        sexps = extract_top_level_sexps(txt)

        # 🔥 [新增] 统计不完备理论断言
        incomplete_theory_count = 0
        high_complexity_count = 0

        for start, end, sexp in sexps:
            sexp_stripped = sexp.strip()

            # 判断是否是assert语句
            if sexp_stripped.startswith('(assert'):
                # 🔥 现在 predicate_signatures 已经填充完毕，可以正确识别谓词
                predicates_in_assert = self._extract_predicates_from_sexp(sexp_stripped)

                # 🔥 [新增] 检查是否使用不完备理论
                uses_incomplete = _uses_incomplete_theory(sexp_stripped)
                quantifier_depth = _count_quantifier_depth(sexp_stripped)

                if uses_incomplete:
                    incomplete_theory_count += 1
                if quantifier_depth >= 2:
                    high_complexity_count += 1

                self.template_assertions[assertion_id] = {
                    "text": sexp_stripped,
                    "predicates": predicates_in_assert,
                    "uses_incomplete_theory": uses_incomplete,  # 🔥 [新增]
                    "quantifier_depth": quantifier_depth,  # 🔥 [新增]
                }

                # 建立谓词到断言ID的反向映射
                for pred in predicates_in_assert:
                    self.predicate_to_assertions.setdefault(pred, set()).add(assertion_id)

                assertion_id += 1
            else:
                # 声明语句，保留
                declaration_lines.append(sexp_stripped)

        # 合并声明部分
        self.template_declarations = "\n".join(declaration_lines)

        print(f"[INFO] SMT模板解析完成: {len(declaration_lines)} 个声明, {len(self.template_assertions)} 个断言, "
              f"{len(self.predicate_signatures)} 个谓词签名")
        print(f"[INFO] 不完备理论断言: {incomplete_theory_count}, 高复杂度断言(量词>=2): {high_complexity_count}")

    def _extract_predicates_from_sexp(self, sexp: str) -> Set[str]:
        """
        从S表达式中提取所有使用的谓词名称

        示例输入: (assert (forall ((x T)) (=> (pred1 x) (pred2 x y))))
        返回: {"pred1", "pred2"}
        """
        predicates = set()

        # 排除SMT关键字
        smt_keywords = {
            'assert', 'forall', 'exists', 'let', 'and', 'or', 'not', 'implies', '=>',
            'ite', 'true', 'false', '+', '-', '*', '/', '=', '<', '>', '<=', '>=',
            'distinct', 'xor', 'iff', 'if', 'then', 'else',
            'declare-sort', 'declare-fun', 'declare-const', 'define-fun',
            'check-sat', 'get-model', 'push', 'pop', 'set-logic', 'set-option',
            'Int', 'Bool', 'Real', 'String', 'Array', 'BitVec',
        }

        # 匹配函数调用模式: (func_name arg1 arg2 ...)
        pattern = r'\(\s*([A-Za-z_][A-Za-z0-9_\-]*)'

        for m in re.finditer(pattern, sexp):
            name = m.group(1)
            # 排除关键字
            if name.lower() in smt_keywords or name in smt_keywords:
                continue

            # 检查是否在predicate_signatures中（即是否是声明的函数）
            if name in self.predicate_signatures:
                predicates.add(name)
            else:
                # 也可能是重命名后的谓词，检查基础名
                base_name, _ = self._parse_predicate_name_suffix(name)
                if base_name in self.predicate_base_to_variants:
                    predicates.add(name)
                # 🔥 [新增] 也检查基础名本身是否匹配
                elif base_name in self.predicate_signatures:
                    predicates.add(name)

        return predicates

    def _get_relevant_assertions(self, used_predicates: Set[str],
                                 filter_incomplete_theory: bool = True,
                                 max_propagation_rounds: int = 1) -> str:
        """
        根据使用的谓词集合，选择性加载相关的断言

        Args:
            used_predicates: 数据事实中实际使用的谓词集合
            filter_incomplete_theory: 是否过滤使用不完备理论的断言
            max_propagation_rounds: 依赖传播最大轮次 (0=禁用传播, 1=只传播一轮)

        Returns:
            选择性加载的断言文本
        """
        if not used_predicates:
            print("[INFO] 无使用的谓词，跳过所有模板断言")
            return ""

        # 收集相关的断言ID
        relevant_assertion_ids = set()
        direct_assertion_ids = set()  # 🔥 记录直接关联的断言（用于诊断）

        # 直接相关：断言中使用了这些谓词
        for pred in used_predicates:
            if pred in self.predicate_to_assertions:
                relevant_assertion_ids.update(self.predicate_to_assertions[pred])
                direct_assertion_ids.update(self.predicate_to_assertions[pred])

            # 也检查基础名（处理重命名情况）
            base_name, _ = self._parse_predicate_name_suffix(pred)
            # 查找所有使用该基础名变体的断言
            if base_name in self.predicate_base_to_variants:
                for actual_name, _, _, _ in self.predicate_base_to_variants[base_name]:
                    if actual_name in self.predicate_to_assertions:
                        relevant_assertion_ids.update(self.predicate_to_assertions[actual_name])
                        direct_assertion_ids.update(self.predicate_to_assertions[actual_name])

        # 🔥 [修改] 限制依赖传播轮次
        iteration = 0
        if max_propagation_rounds > 0:
            expanded = True
            while expanded and iteration < max_propagation_rounds:
                expanded = False
                iteration += 1

                current_ids = set(relevant_assertion_ids)
                for aid in current_ids:
                    if aid in self.template_assertions:
                        assertion_info = self.template_assertions[aid]
                        for dep_pred in assertion_info.get("predicates", set()):
                            if dep_pred in self.predicate_to_assertions:
                                new_ids = self.predicate_to_assertions[dep_pred] - relevant_assertion_ids
                                if new_ids:
                                    relevant_assertion_ids.update(new_ids)
                                    expanded = True

        # 🔥 [新增] 过滤使用不完备理论的断言
        filtered_assertion_ids = set()
        skipped_incomplete = 0
        skipped_high_complexity = 0

        for aid in relevant_assertion_ids:
            if aid not in self.template_assertions:
                continue

            assertion_info = self.template_assertions[aid]

            # 检查是否使用不完备理论
            if filter_incomplete_theory and assertion_info.get("uses_incomplete_theory", False):
                skipped_incomplete += 1
                continue

            # 🔥 [可选] 跳过高复杂度断言 (量词嵌套深度 >= 3)
            # if assertion_info.get("quantifier_depth", 0) >= 3:
            #     skipped_high_complexity += 1
            #     continue

            filtered_assertion_ids.add(aid)

        # 生成断言文本（按原始顺序）
        assertion_texts = []
        sorted_ids = sorted(filtered_assertion_ids)

        for aid in sorted_ids:
            if aid in self.template_assertions:
                assertion_texts.append(self.template_assertions[aid]["text"])

        total_assertions = len(self.template_assertions)
        direct_count = len(direct_assertion_ids)
        propagated_count = len(relevant_assertion_ids)
        final_count = len(filtered_assertion_ids)

        # 🔥 详细诊断信息
        print(f"[INFO] 选择性加载断言: {final_count}/{total_assertions} "
              f"({100 * final_count / total_assertions if total_assertions > 0 else 0:.1f}%)")
        print(f"[INFO] 相关谓词: {sorted(used_predicates)[:10]}{'...' if len(used_predicates) > 10 else ''}")
        print(f"[DIAG] 直接关联断言: {direct_count}")
        print(f"[DIAG] 传播后断言数: {propagated_count} (传播轮次: {iteration})")
        print(f"[DIAG] 过滤后断言数: {final_count}")
        if skipped_incomplete > 0:
            print(f"[DIAG] 跳过不完备理论断言: {skipped_incomplete}")
        if skipped_high_complexity > 0:
            print(f"[DIAG] 跳过高复杂度断言: {skipped_high_complexity}")

        # 统计高扇出谓词
        high_fanout = [(p, len(self.predicate_to_assertions.get(p, set())))
                       for p in used_predicates]
        high_fanout.sort(key=lambda x: -x[1])
        print(f"[DIAG] 高扇出谓词TOP5: {high_fanout[:5]}")

        # 统计最终加载断言的量词复杂度
        forall_count = sum(1 for aid in filtered_assertion_ids
                           if 'forall' in self.template_assertions.get(aid, {}).get('text', ''))
        exists_count = sum(1 for aid in filtered_assertion_ids
                           if 'exists' in self.template_assertions.get(aid, {}).get('text', ''))
        print(f"[DIAG] 最终加载 - 包含forall: {forall_count}, 包含exists: {exists_count}")

        return "\n".join(assertion_texts)

    def _collect_used_predicates(self) -> Set[str]:
        """
        从已生成的SMT事实中收集所有使用的谓词/函数名称
        """
        used_predicates: Set[str] = set()

        for meta in self.fact_metadata:
            # 谓词
            pred_name = meta.get("pred_name")
            if pred_name:
                used_predicates.add(pred_name)

            # ✅ 函数名也算进来
            func_name = meta.get("function_name")
            if func_name:
                used_predicates.add(func_name)

        # 兜底：从 smt_facts 里用正则扫一遍
        if not used_predicates and self.smt_facts:
            for fact in self.smt_facts:
                m = re.search(r'\(assert\s+\(\s*([A-Za-z_][A-Za-z0-9_\-]*)', fact)
                if m:
                    used_predicates.add(m.group(1))

        return used_predicates

    def _parse_predicate_name_suffix(self, pred_name: str) -> Tuple[str, int]:
        """
        解析谓词名中的后缀数字（check_smt.py的重命名格式）

        支持的格式：
        - "hasPeriod" → ("hasPeriod", 0)      # 原名，后缀为0
        - "hasPeriod__2" → ("hasPeriod", 2)   # 双下划线+数字
        - "hasPeriod_2" → ("hasPeriod", 2)    # 单下划线+数字（兼容）
        - "hasPeriod2" → ("hasPeriod", 2)     # 直接数字后缀（兼容）

        Returns:
            (base_name, suffix_number)
        """
        # 模式1: name__N (check_smt.py的标准格式)
        match = re.match(r'^(.+)__(\d+)$', pred_name)
        if match:
            return (match.group(1), int(match.group(2)))

        # 模式2: name_N (单下划线，兼容)
        match = re.match(r'^(.+)_(\d+)$', pred_name)
        if match:
            base = match.group(1)
            num = int(match.group(2))
            # 排除像 "has_period_ref" 这种本身就有下划线的名字
            # 只有当数字是1位或2位时才认为是后缀
            if num >= 2 and num <= 99:
                return (base, num)

        # 模式3: nameN (直接数字后缀，如hasPeriod2)
        match = re.match(r'^(.+[A-Za-z_\-])(\d{1,2})$', pred_name)
        if match:
            base = match.group(1)
            num = int(match.group(2))
            if num >= 2 and num <= 99:
                return (base, num)

        # 无后缀，返回原名和0
        return (pred_name, 0)

    def _match_predicate_in_template(
            self,
            mapping_pred_name: str,
            expected_arity: int = -1,
            expected_arg_sorts: List[str] = None,
            is_function: bool = False,  # ✅ 新增：标记是否为函数
            expected_return_sort: str = None  # ✅ 新增：函数的期望返回类型
    ) -> Optional[str]:
        """
        在模板中查找与mapping谓词名匹配的实际谓词名。

        对于谓词 (Bool返回)：匹配参数类型
        对于函数 (非Bool返回)：匹配返回类型 + 参数数量，放宽参数类型检查
        """
        clean_pred_name = self._normalize_predicate_name(mapping_pred_name)

        # 🔧 修改缓存键，包含函数标记
        cache_key = (clean_pred_name, expected_arity,
                     tuple(expected_arg_sorts) if expected_arg_sorts else None,
                     is_function, expected_return_sort)
        if cache_key in self.predicate_match_cache:
            return self.predicate_match_cache[cache_key]

        matched = None
        base_name, _ = self._parse_predicate_name_suffix(clean_pred_name)

        # ✅ [新增] 函数匹配策略：优先匹配返回类型
        if is_function and expected_return_sort:
            # 策略F1: 精确名称 + 返回类型匹配
            if clean_pred_name in self.predicate_signatures:
                sig = self.predicate_signatures[clean_pred_name]
                ret_type = sig[1]
                if self._sort_compatible(ret_type, expected_return_sort):
                    if expected_arity == -1 or len(sig[0]) == expected_arity:
                        matched = clean_pred_name

            # 策略F2: 基础名变体 + 返回类型匹配
            if matched is None and base_name in self.predicate_base_to_variants:
                variants = self.predicate_base_to_variants[base_name]
                for actual_name, arg_types, ret_type, suffix_num in variants:
                    # 检查返回类型兼容性
                    if self._sort_compatible(ret_type, expected_return_sort):
                        # 检查参数数量
                        if expected_arity == -1 or len(arg_types) == expected_arity:
                            matched = actual_name
                            break

            # 策略F3: 大小写不敏感 + 返回类型匹配
            if matched is None:
                lower_pred = clean_pred_name.lower()
                for actual_name, sig in self.predicate_signatures.items():
                    if actual_name.lower() == lower_pred:
                        ret_type = sig[1]
                        if self._sort_compatible(ret_type, expected_return_sort):
                            if expected_arity == -1 or len(sig[0]) == expected_arity:
                                matched = actual_name
                                break

            self.predicate_match_cache[cache_key] = matched
            return matched

        # ========== 原有的谓词匹配逻辑 (Bool返回) ==========
        strict_type_check = expected_arg_sorts and "Unknown" not in expected_arg_sorts

        # [策略1] 精确名称匹配 + 类型检查
        if clean_pred_name in self.predicate_signatures:
            sig = self.predicate_signatures[clean_pred_name]
            if expected_arity == -1 or len(sig[0]) == expected_arity:
                if not strict_type_check or self._arg_types_match(sig[0], expected_arg_sorts):
                    matched = clean_pred_name

        # [策略2] 基础名匹配(变体) + 类型匹配
        if matched is None and base_name in self.predicate_base_to_variants:
            variants = self.predicate_base_to_variants[base_name]
            for actual_name, arg_types, ret_type, suffix_num in variants:
                if expected_arity != -1 and len(arg_types) != expected_arity:
                    continue
                if strict_type_check:
                    if self._arg_types_match(arg_types, expected_arg_sorts):
                        matched = actual_name
                        break
                else:
                    matched = actual_name
                    break

        # [策略4] 大小写不敏感匹配
        if matched is None:
            lower_pred = clean_pred_name.lower()
            for actual_name, sig in self.predicate_signatures.items():
                if actual_name.lower() == lower_pred:
                    if expected_arity == -1 or len(sig[0]) == expected_arity:
                        if not strict_type_check or self._arg_types_match(sig[0], expected_arg_sorts):
                            matched = actual_name
                            break

        self.predicate_match_cache[cache_key] = matched
        return matched

    def _sort_compatible(self, declared_sort: str, expected_sort: str) -> bool:
        """检查两个Sort是否兼容（相等或存在继承关系）"""
        if declared_sort == expected_sort:
            return True
        if self._is_subtype_of(declared_sort, expected_sort):
            return True
        if self._is_subtype_of(expected_sort, declared_sort):
            return True
        return False

    def _arg_types_match(self, declared_types: List[str], actual_types: List[str]) -> bool:
        """
        检查参数类型是否匹配（支持继承层次：父类/子类都可以匹配）

        declared_types: 来自 SMT 模板中 declare-fun 的参数类型
        actual_types  : 来自 mapping（SUBJECT/PROPERTY 对应的 smt_sort 或 target_sort）
        """
        if len(declared_types) != len(actual_types):
            return False

        for declared, actual in zip(declared_types, actual_types):
            # 防御：实际类型未知直接不匹配
            if not actual or actual == "Unknown":
                return False

            # 完全相同，直接通过
            if declared == actual:
                continue

            # 情况 1：mapping 用子类，模板用父类
            #   e.g.: declared = ATOMIC-SW-COMPONENT-TYPE,
            #         actual   = APPLICATION-SW-COMPONENT-TYPE
            if self._is_subtype_of(actual, declared):
                continue

            # 情况 2：mapping 用父类，模板用子类
            #   e.g.: declared = APPLICATION-SW-COMPONENT-TYPE,
            #         actual   = ATOMIC-SW-COMPONENT-TYPE
            if self._is_subtype_of(declared, actual):
                continue

            # 其它情况视为不兼容
            return False

        return True

    def _normalize_predicate_name(self, pred_name: str) -> str:
        """
        清洗谓词名：
        - 去除首尾空白
        - 去除非法字符（只保留 [A-Za-z0-9_-]）
        """
        if pred_name is None:
            return ""
        s = str(pred_name).strip()
        # 去除非法字符
        s = re.sub(r'[^A-Za-z0-9_\-]', '', s)
        return s

    # -------------------------
    # Load mapping JSON
    # -------------------------
    def _load_mapping(self):
        if not self.mapping_file:
            self.mapping = []
            print("[INFO] No mapping file provided to SMTValidator; proceeding without mapping.")
            return
        try:
            with open(self.mapping_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # mapping could be dict or list; normalize to list
            if isinstance(data, dict):
                # maybe top-level object with entries keyed by constraint_id
                # convert to list of value objects
                if all(isinstance(v, dict) for v in data.values()):
                    self.mapping = list(data.values())
                else:
                    # fallback: wrap
                    self.mapping = [data]
            elif isinstance(data, list):
                self.mapping = data
            else:
                self.mapping = []
            # basic validation: ensure each has constraint_id
            for entry in self.mapping:
                if 'constraint_id' not in entry:
                    entry['constraint_id'] = entry.get('id') or ("constraint_" + str(hash(json.dumps(entry)))[1:8])
        except FileNotFoundError:
            self.mapping = []
            print(f"[ERROR] Mapping file '{self.mapping_file}' not found; proceeding without mapping.")
            print(f"[ERROR] 这将导致 '0 data points' 错误。请检查您的 main_config.yaml 中 'smt_mapping' 的路径。")
        except Exception as e:
            self.mapping = []
            print(f"[WARN] Failed to load mapping file '{self.mapping_file}': {e}")

    # -------------------------
    # z3 availability
    # -------------------------
    def _z3_cli_available(self) -> bool:
        try:
            res = subprocess.run(['z3', '-version'], capture_output=True, text=True, timeout=3)
            return res.returncode == 0
        except Exception:
            return False

    # -------------------------
    # XML helpers
    # -------------------------
    def _parse_xml_root(self, xml_content: str) -> Optional[ET.Element]:
        try:
            root = ET.fromstring(xml_content)
            # cache root and parent map
            self._last_root = root
            self._build_parent_map(root)
            return root
        except Exception as e:
            print(f"[ERROR] Failed to parse XML content: {e}")
            return None

    def _build_parent_map(self, root: ET.Element):
        self._parent_map = {}
        for parent in root.iter():
            for child in list(parent):
                self._parent_map[child] = parent

    def _find_parent(self, elem: ET.Element) -> Optional[ET.Element]:
        if self._parent_map is None:
            return None
        return self._parent_map.get(elem)

    def _stable_name_for_elem(self, elem: ET.Element, binding: str = "short-name", prefix: Optional[str] = None) -> str:
        """
        binding: "short-name" | "path" | "id"
        prefix: optional prefix string for SMT ident
        """
        # try short-name
        sn = _first_text(elem, "SHORT-NAME")
        if binding == "short-name" and sn:
            base = sn
        elif binding == "id":
            # fallback to element's xml tag + index under parent
            tag = _xml_tag_local(elem.tag)
            idx = self._index_in_parent(elem)
            base = f"{tag}_{idx}"
        else:
            # path binding: construct path from root -> elem using short-names if present
            path_parts = []
            cur = elem
            while cur is not None:
                tag = _xml_tag_local(cur.tag)
                snc = _first_text(cur, "SHORT-NAME") or None
                if snc:
                    path_parts.append(f"{tag}.{snc}")
                else:
                    path_parts.append(tag)
                cur = self._find_parent(cur)
            path_parts.reverse()
            base = "_".join(path_parts)
        if prefix:
            name = f"{prefix}_{base}"
        else:
            name = base
        return _sanitize_ident(name)

    def _index_in_parent(self, elem: ET.Element) -> int:
        parent = self._find_parent(elem)
        if parent is None:
            return 0
        same = [c for c in list(parent) if _xml_tag_local(c.tag) == _xml_tag_local(elem.tag)]
        for i, c in enumerate(same):
            if c is elem:
                return i
        return 0

    def _declare_const(self, name: str, sort: str):
        """
        声明一个常量。

        注意：同一个常量如果被多次以不同 Sort 声明（例如 mapping 写的是父类，
        而谓词签名要求子类），我们会在类型兼容的前提下，以“后声明的 Sort 为准”，
        并回写已有的 (declare-const ...) 语句中，保证和 SMT 模板保持一致。
        """
        norm_sort = self._normalize_sort(sort)
        builtin_sorts = {"Int", "Bool", "Real", "String"}

        # 自动声明未知 Sort
        if (
                norm_sort not in builtin_sorts
                and norm_sort not in self.template_sorts
                and norm_sort not in self.auto_declared_sorts
        ):
            self.smt_decls.append(f"(declare-sort {norm_sort} 0)")
            self.auto_declared_sorts.add(norm_sort)

        # 处理重复声明
        if name in self.declared_consts:
            prev_sort = getattr(self, "_const_sort_map", {}).get(name)
            if prev_sort and prev_sort != norm_sort:
                # 只要两个 Sort 在继承关系上是兼容的，就允许“升级/降级”，
                # 直接以**新的** Sort 为准，并回写已有的声明。
                if self._sort_compatible(prev_sort, norm_sort):
                    if self.verbosity >= 2:
                        print(f"[DEBUG] 常量 {name} 类型统一: {prev_sort} → {norm_sort}")
                    # 回写已有的 (declare-const name prev_sort ...)
                    prefix = f"(declare-const {name} "
                    replacement = f"(declare-const {name} {norm_sort})"
                    for i, decl in enumerate(self.smt_decls):
                        if decl.startswith(prefix):
                            self.smt_decls[i] = replacement
                            break
                    # 更新记录
                    self._const_sort_map[name] = norm_sort
                else:
                    # 真的不兼容就只给出告警，不自动修正
                    print(
                        f"[WARN] 常量 {name} 类型冲突: 已声明为 {prev_sort}, 又被声明为 {norm_sort}"
                    )
            return

        # 首次声明
        self.declared_consts.add(name)
        if not hasattr(self, "_const_sort_map"):
            self._const_sort_map = {}
        self._const_sort_map[name] = norm_sort
        self.smt_decls.append(f"(declare-const {name} {norm_sort})")

    def _generate_from_mapping_for_root(self, root: ET.Element):
        """
        Core loop: iterate mapping entries, locate XML elements per mapping, and emit SMT declares+asserts.
        Mapping schema (per entry) expected fields (best-effort):
          - constraint_id
          - target: { target_sort, target_xml: { xml_tag, xpath? }, target_binding }
          - properties: list of props with xml_tag, xpath?, smt_sort, smt_accessor?, smt_predicates?
          - logical_pattern: template to generate SMT assertions (see README of mapping)
          - shacl: optional shacl guidance (not used here; SHACL generation handled separately)
        """
        # 🔥 [诊断] 打印mapping信息
        print(f"[DIAG] _generate_from_mapping_for_root 开始")
        print(f"[DIAG] mapping条目数: {len(self.mapping)}")
        for entry in self.mapping:
            # ✅ 显式过滤跨文件约束
            if entry.get('cross_file', False):
                continue  # 跳过跨文件约束
            cid = entry.get("constraint_id", "constraint")
            tgt = entry.get("target", {}) or {}
            tgt_sort = tgt.get("target_sort")
            tgt_xml = tgt.get("target_xml") or {}
            base_tag = tgt_xml.get("xml_tag")
            tgt_xpath = tgt_xml.get("xpath")
            tgt_binding = tgt.get("target_binding", "short-name")

            # 🔥 [核心修改开始] 构建搜索标签列表
            tags_to_search = set()

            # 1. 优先检查继承表 (XsdIndex)
            if base_tag and base_tag in self.inheritance_map:
                # 如果是抽象类 (如 ATOMIC-...), inheritance_map[base_tag] 仅包含子类
                # 如果是具体类 (如 APPLICATION-...), inheritance_map[base_tag] 包含它自己
                # 所以我们可以盲目地信任这个列表
                tags_to_search.update(self.inheritance_map[base_tag])
                # print(f"[DEBUG] Mapping {base_tag} -> {tags_to_search}")
            elif base_tag:
                # 如果不在继承表中，说明它是一个没有子类的普通具体标签，搜它自己
                tags_to_search.add(base_tag)

            # 开始搜索
            nodes = []

            # 策略 A: 如果有 XPath，优先 XPath (通常 XPath 是特定路径)
            if tgt_xpath:
                tag = tgt_xpath
                # 注意：如果 xpath 包含具体标签名，不需要扩展；如果是通配符才需要考虑
                # 这里简化处理，假设 xpath 是精确的
                nodes = [n for n in root.iter() if _xml_tag_local(n.tag) == tag]

            # 策略 B: 使用智能构建的 tags_to_search
            elif tags_to_search:
                # 高效搜索：只遍历一次 XML
                nodes = [n for n in root.iter() if _xml_tag_local(n.tag) in tags_to_search]
            else:
                # if no xpath, attempt to use tag name from target_xml
                tag = tgt_xml.get("xml_tag") if tgt_xml else None
                if tag:
                    # 🔥 确保使用去除命名空间的标签进行匹配
                    nodes = [n for n in root.iter() if _xml_tag_local(n.tag) == tag]

            # default to entire document if no target specified (rare)
            if not nodes and not tgt_xpath and not tgt_xml:
                nodes = [root]

            # For each matched target element, generate subject and properties
            for node in nodes:
                # SMT 声明依然使用 tgt_sort (抽象类型)
                # 例如: (declare-const MySwc ATOMIC-SW-COMPONENT-TYPE)
                prefix = tgt_sort or _xml_tag_local(node.tag)
                subj_name = self._stable_name_for_elem(node, binding=tgt_binding, prefix=prefix)
                #
                # if tgt_sort:
                #     self._declare_const(subj_name, tgt_sort)
                # else:
                #     self._declare_const(subj_name, "Int")

                # process properties
                props = entry.get("properties", []) or []
                prop_instances = {}  # role -> smt_name
                for p in props:
                    role = p.get("role") or p.get("name") or p.get("xml_tag")
                    p_xpath = p.get("xpath")  # 可选的相对路径
                    p_xml_tag = p.get("xml_tag")  # 元素标签名
                    p_binding = p.get("binding") or "short-name"
                    p_sort = p.get("smt_sort") or p.get("smtType") or None

                    found = []

                    # 优先使用 xpath，如果为空则使用 xml_tag
                    search_path = p_xpath if p_xpath else p_xml_tag

                    if search_path:
                        # 命名空间感知的路径查找
                        if '/' in search_path:
                            # 多层路径：逐层匹配（去除命名空间）
                            path_parts = search_path.split('/')
                            current_nodes = [node]

                            # 兼容写法：如果第一段等于当前节点标签，认为是重复写了自身标签，自动跳过
                            first = path_parts[0]
                            cur_tag = _xml_tag_local(node.tag)
                            if first == cur_tag:
                                path_parts = path_parts[1:]

                            for part in path_parts:
                                next_nodes = []
                                for n in current_nodes:
                                    # 使用去命名空间的标签匹配
                                    matches = [c for c in n if _xml_tag_local(c.tag) == part]
                                    next_nodes.extend(matches)
                                current_nodes = next_nodes

                            found = current_nodes
                        else:
                            # 单层路径：先找直接子元素，再找后代
                            found = [c for c in node if _xml_tag_local(c.tag) == search_path]
                            if not found:
                                # 查找所有后代（兼容性保留）
                                found = [c for c in node.iter() if _xml_tag_local(c.tag) == search_path]

                    if not found:
                        # property 不存在：可选地只在需要时打印未命中日志
                        # print(f"[DEBUG] [{cid}] 属性 '{role}' 在节点 {_xml_tag_local(node.tag)} 上未找到路径 '{search_path}'")
                        continue

                    # 到这里说明找到了，打印“正确映射的节点”
                    debug_names = []
                    for fe in found[:3]:  # 只展示前 3 个，防止日志太长
                        debug_names.append(self._stable_name_for_elem(fe, binding=p_binding, prefix=role))

                    # print(
                    #     f"[DEBUG] [{cid}] 属性 '{role}'：在节点 "
                    #     f"{_xml_tag_local(node.tag)} 上通过路径 '{search_path}' "
                    #     f"命中 {len(found)} 个元素，示例: {', '.join(debug_names)}"
                    # )

                    # for each found, create an smt name and declare
                    for idx, fe in enumerate(found):
                        prop_smt = self._stable_name_for_elem(fe, binding=p_binding, prefix=role)
                        # declare according to p_sort
                        if p_sort:
                            self._declare_const(prop_smt, p_sort)
                        else:
                            # try to infer sort from mapping target sorts or template sorts
                            inferred_sort = p.get("smt_infer_from") or None
                            if inferred_sort and inferred_sort in self.template_sorts:
                                self._declare_const(prop_smt, inferred_sort)
                            else:
                                self._declare_const(prop_smt, "Int")
                        # record
                        prop_instances.setdefault(role, []).append(prop_smt)

                        # optional: generate simple predicate assertions if mapping asks
                        smt_preds = p.get("smt_predicates") or {}
                        for pred_name, pred_info in smt_preds.items():
                            if isinstance(pred_info, dict):
                                args_template = pred_info.get("args", [])
                                expected_arity = len(args_template)
                                pred_type = pred_info.get("type", "predicate")  # ✅ 获取类型标记

                                if pred_type == "function":
                                    # ========== 函数处理（通用） ==========
                                    # mapping 里给的是返回类型
                                    expected_return_sort = self._normalize_sort(p_sort) if p_sort else None

                                    # 若 mapping 里的 sort 既不是模板已知 sort，也不是基础类型，就不要用它来过滤
                                    if expected_return_sort and expected_return_sort not in self.template_sorts \
                                            and expected_return_sort not in ("Int", "Real", "Bool"):
                                        expected_return_sort = None

                                    # 按名字 + 元数（+可选返回类型）在模板中找函数
                                    matched_name = self._match_predicate_in_template(
                                        pred_name,
                                        expected_arity=expected_arity,
                                        expected_arg_sorts=None,  # 不检查参数类型
                                        is_function=True,
                                        expected_return_sort=expected_return_sort
                                    )

                                    if not matched_name:
                                        skip_info = {
                                            "constraint_id": cid,
                                            "mapping_predicate": pred_name,
                                            "reason": "no_matching_function",
                                            "expected_return_sort": expected_return_sort,
                                            "expected_arity": expected_arity,
                                        }
                                        self.skipped_predicates.append(skip_info)
                                        self._log_skip_predicate_once(skip_info)
                                        continue

                                    # 获取匹配函数的签名
                                    matched_signature = self.predicate_signatures.get(matched_name)
                                    arg_sorts = matched_signature[0] if matched_signature else []
                                    ret_type = matched_signature[1] if matched_signature else (
                                            expected_return_sort or "Int")

                                    # 先声明函数的“输出常量”，保持原有逻辑
                                    self._declare_const(prop_smt, ret_type)

                                    # 生成函数调用实参
                                    resolved_args: List[str] = []

                                    # 先复制一份，后面可能会改
                                    effective_args_template = list(args_template)

                                    # 🔥 如果 mapping 把函数参数写成了 "PROPERTY"，但模板里的签名其实是主体类型，
                                    #    则自动把它纠正成用 SUBJECT 作为参数，把 PROPERTY 仅作为数值来源。
                                    if matched_signature and len(args_template) == 1 and args_template[0] == "PROPERTY":
                                        sig_arg_sorts = matched_signature[0]
                                        sig_arg_sort = sig_arg_sorts[0] if sig_arg_sorts else None

                                        norm_tgt_sort = self._normalize_sort(tgt_sort) if tgt_sort else None
                                        norm_p_sort = self._normalize_sort(p_sort) if p_sort else None

                                        # 条件：
                                        # 1) 函数签名的参数类型和目标 sort（主体类型）兼容
                                        # 2) 且和属性的 sort 不兼容
                                        #    ——典型案例：minimumStartInterval 的参数是 RUNNABLE-ENTITY，
                                        #      mapping 写 PROPERTY，但 PROPERTY 的 sort 是 Int
                                        if (
                                                sig_arg_sort
                                                and norm_tgt_sort
                                                and self._sort_compatible(norm_tgt_sort, sig_arg_sort)
                                                and (
                                                not norm_p_sort or not self._sort_compatible(norm_p_sort, sig_arg_sort))
                                        ):
                                            # 把参数模板从 ["PROPERTY"] 改成 ["SUBJECT"]
                                            effective_args_template = ["SUBJECT"]

                                    # 根据 effective_args_template 声明参数常量并收集实参
                                    if matched_signature:
                                        for arg_idx, a in enumerate(effective_args_template):
                                            sig_sort = matched_signature[0][arg_idx] if arg_idx < len(
                                                matched_signature[0]) else None

                                            if a == "SUBJECT":
                                                self._declare_const(subj_name, sig_sort or tgt_sort or "Int")
                                                resolved_args.append(subj_name)
                                            elif a == "PROPERTY":
                                                self._declare_const(prop_smt, sig_sort or p_sort or "Int")
                                                resolved_args.append(prop_smt)
                                            else:
                                                resolved_args.append(a)
                                    else:
                                        for a in effective_args_template:
                                            if a == "SUBJECT":
                                                self._declare_const(subj_name, tgt_sort or "Int")
                                                resolved_args.append(subj_name)
                                            elif a == "PROPERTY":
                                                self._declare_const(prop_smt, p_sort or "Int")
                                                resolved_args.append(prop_smt)
                                            else:
                                                resolved_args.append(a)

                                    # ✅ 新增：最后再做一次“参数个数 vs 模板签名”的严格检查
                                    if matched_signature and len(resolved_args) != len(matched_signature[0]):
                                        print(
                                            f"[WARN] 跳过函数 '{matched_name}' (约束: {cid}): "
                                            f"模板要求 {len(matched_signature[0])} 个参数, "
                                            f"但 mapping 提供了 {len(resolved_args)} 个"
                                        )
                                        continue

                                    if resolved_args:
                                        func_app = f"({matched_name} {' '.join(resolved_args)})"
                                    else:
                                        # 仅在真正 0 元函数时才会走到这里
                                        func_app = f"({matched_name})"

                                    # 从当前属性元素中抽取标量字面量（Int / Real / Bool）
                                    value_lit = self._extract_scalar_literal_from_element(fe, p_sort)

                                    if value_lit is not None:
                                        # ✅ 真正绑定函数值： (= (f args...) literal)
                                        fact_str = f"(assert (= {func_app} {value_lit}))"
                                        self.smt_facts.append(fact_str)
                                        meta_kind = "function_value"
                                    else:
                                        # 没有可解析标量值（比如 TIME-VALUE），那就只保留输出常量 + 元信息
                                        meta_kind = "function_output"

                                    func_meta = {
                                        "constraint_id": cid,
                                        "type": "function",
                                        "function_name": matched_name,
                                        "pred_name": matched_name,  # ✅ 让 _collect_used_predicates 能看到
                                        "output_const": prop_smt,
                                        "output_sort": ret_type,
                                        "property_role": role,
                                        "kind": meta_kind,
                                    }
                                    self.fact_metadata.append(func_meta)

                                    if matched_name != pred_name:
                                        print(f"[INFO] 函数映射: '{pred_name}' → '{matched_name}' (约束: {cid})")

                                    # 完成函数处理，继续下一个 smt_predicate
                                    continue

                                else:
                                    # ========== 谓词处理 (保持原逻辑) ==========
                                    actual_arg_sorts = []
                                    for a in args_template:
                                        if a == "SUBJECT":
                                            actual_arg_sorts.append(self._normalize_sort(tgt_sort))
                                        elif a == "PROPERTY":
                                            actual_arg_sorts.append(self._normalize_sort(p_sort))
                                        else:
                                            actual_arg_sorts.append("Unknown")

                                    matched_name = self._match_predicate_in_template(
                                        pred_name,
                                        expected_arity=expected_arity,
                                        expected_arg_sorts=actual_arg_sorts,
                                        is_function=False
                                    )

                                    if not matched_name:
                                        skip_info = {
                                            "constraint_id": cid,
                                            "mapping_predicate": pred_name,
                                            "reason": "no_matching_predicate",
                                            "expected_arity": expected_arity,
                                            "actual_arg_sorts": actual_arg_sorts,
                                        }
                                        self.skipped_predicates.append(skip_info)
                                        self._log_skip_predicate_once(skip_info)
                                        continue

                                    matched_signature = self.predicate_signatures.get(matched_name)

                                    # ✅ 只对谓词检查Bool返回类型
                                    if matched_signature:
                                        ret_type = matched_signature[1]
                                        if ret_type != "Bool":
                                            skip_info = {
                                                "constraint_id": cid,
                                                "mapping_predicate": pred_name,
                                                "reason": "non_boolean_predicate",
                                                "return_type": ret_type,
                                            }
                                            self.skipped_predicates.append(skip_info)
                                            self._log_skip_predicate_once(skip_info)
                                            continue

                                    # ============== 🔥 类型兼容性检查与类型确定 ==============
                                    # actual_xml_sort = self._normalize_sort(_xml_tag_local(node.tag))
                                    # actual_prop_sort = self._normalize_sort(_xml_tag_local(fe.tag))

                                    actual_xml_sort = self._normalize_sort(tgt_sort) if tgt_sort else "Int"
                                    actual_prop_sort = self._normalize_sort(p_sort) if p_sort else "Int"
                                    should_skip_due_to_type = False

                                    # 预先计算每个参数应使用的类型（始终以模板签名为准）
                                    arg_sorts_to_use = {}
                                    if matched_signature:
                                        for arg_idx_chk, arg_type_chk in enumerate(args_template):
                                            if arg_idx_chk >= len(matched_signature[0]):
                                                continue
                                            expected_sort = matched_signature[0][arg_idx_chk]

                                            if arg_type_chk == "SUBJECT":
                                                # SUBJECT：检查 mapping 的主体 sort 和模板签名是否兼容
                                                if not self._sort_compatible(actual_xml_sort, expected_sort):
                                                    should_skip_due_to_type = True
                                                    break
                                                # 统一使用谓词签名中的 Sort
                                                arg_sorts_to_use["SUBJECT"] = expected_sort

                                            elif arg_type_chk == "PROPERTY":
                                                # PROPERTY：检查属性 sort 和模板签名是否兼容
                                                if not self._sort_compatible(actual_prop_sort, expected_sort):
                                                    should_skip_due_to_type = True
                                                    break
                                                arg_sorts_to_use["PROPERTY"] = expected_sort

                                    if should_skip_due_to_type:
                                        continue
                                    # ============== 类型兼容性检查结束 ==============

                                    # 生成谓词断言
                                    resolved_args = []
                                    for arg_idx, a in enumerate(args_template):
                                        if a == "PROPERTY":
                                            sort_to_use = arg_sorts_to_use.get("PROPERTY")
                                            if sort_to_use:
                                                self._declare_const(prop_smt, sort_to_use)
                                            elif matched_signature and arg_idx < len(matched_signature[0]):
                                                self._declare_const(prop_smt, matched_signature[0][arg_idx])
                                            else:
                                                self._declare_const(prop_smt, p_sort)
                                            resolved_args.append(prop_smt)
                                        elif a == "SUBJECT":
                                            sort_to_use = arg_sorts_to_use.get("SUBJECT")
                                            if sort_to_use:
                                                self._declare_const(subj_name, sort_to_use)
                                            elif matched_signature and arg_idx < len(matched_signature[0]):
                                                self._declare_const(subj_name, matched_signature[0][arg_idx])
                                            else:
                                                self._declare_const(subj_name, tgt_sort)
                                            resolved_args.append(subj_name)
                                        else:
                                            resolved_args.append(a)

                                    base_meta = {
                                        "constraint_id": cid,
                                        "type": "predicate",
                                        "target_sort": tgt_sort,
                                        "subject": subj_name,
                                        "property_role": role,
                                        "pred_name": matched_name,
                                    }

                                    fact_str = f"(assert ({matched_name} {' '.join(resolved_args)}))"
                                    self.smt_facts.append(fact_str)
                                    self.fact_metadata.append(base_meta)

                                    if matched_name != pred_name:
                                        print(f"[INFO] 谓词映射: '{pred_name}' → '{matched_name}' (约束: {cid})")


                            else:
                                # simple string形式
                                pred_str = str(pred_info).strip()
                                actual_arg_sorts_simple = [self._normalize_sort(p_sort)]
                                matched_simple = self._match_predicate_in_template(pred_str, 1, actual_arg_sorts_simple)

                                if matched_simple is None:
                                    self.skipped_predicates.append({
                                        "constraint_id": cid,
                                        "mapping_predicate": pred_str,
                                        "expected_arity": 1,
                                        "actual_arg_sorts": actual_arg_sorts_simple,
                                        "property_role": role,
                                        "reason": f"谓词 '{pred_str}' 在SMT模板中未找到匹配"
                                    })
                                    print(f"[WARN] 跳过谓词 '{pred_str}' (约束: {cid}): 模板中未找到匹配")
                                    continue

                                # 🔥 [CRITICAL FIX] 简单形式也要检查返回类型
                                simple_sig = self.predicate_signatures.get(matched_simple)
                                if simple_sig:
                                    if simple_sig[1] != 'Bool':
                                        print(
                                            f"[WARN] 跳过非布尔谓词 '{matched_simple}' (约束: {cid}): 返回类型 {simple_sig[1]}")
                                        continue
                                    if len(simple_sig[0]) > 0:
                                        self._declare_const(prop_smt, simple_sig[0][0])
                                    else:
                                        self._declare_const(prop_smt, p_sort)

                                fact_str = f"(assert ({matched_simple} {prop_smt}))"
                                self.smt_facts.append(fact_str)
                                meta = {
                                    "constraint_id": cid,
                                    "property_role": role,
                                    "pred_name": matched_simple,
                                }
                                self.fact_metadata.append(meta)

                # logical pattern: 在模板驱动架构下，跳过逻辑模式生成
                lp = entry.get("logical_pattern") or {}
                if lp:
                    # 传递给简化版的方法（只做日志记录，不生成断言）
                    self._emit_logical_pattern(lp, subj_name, prop_instances, entry.get("constraint_id"))

    def _generate_global_smt_facts(self) -> int:
        """
        根据 Mapping 和 全局索引，生成 SMT 数据事实 (Data Facts)。

        注意：
        1. 这里生成的 `(assert ...)` 仅用于录入数据（例如 "A 拥有 B"）。
        2. 这里的 `declare-const` 会将 XML 中的具体子类映射为 SMT 中的抽象父类。
        3. 绝不生成逻辑规则（逻辑规则由 SMT 模板提供）。
        """
        resolver = self.cross_file_resolver
        global_index = resolver.global_index

        # 1. 筛选跨文件 Mapping
        cross_mappings = [m for m in self.mapping if m.get('cross_file', False)]

        count = 0

        for entry in cross_mappings:
            cid = entry.get("constraint_id")
            tgt = entry.get("target", {})

            # 目标 XML 标签 (可能是抽象类，如 ATOMIC-SW-COMPONENT-TYPE)
            abstract_tag = tgt.get("target_xml", {}).get("xml_tag")

            # SMT 中对应的类型 (必须与 SMT Template 中的 declare-sort 一致)
            # 例如：(declare-sort ATOMIC-SW-COMPONENT-TYPE 0)
            tgt_sort = tgt.get("target_sort", "Int")

            # 🔥 [Fix] 抽象类处理：获取该抽象类对应的所有具体子类标签
            # 例如：ATOMIC-SW... -> {APPLICATION-SW..., COMPLEX-DEVICE..., ...}
            concrete_tags = self._get_concrete_tags(abstract_tag)

            # 在全局索引中查找这些具体标签的所有实例
            target_instances = [
                (path, info) for path, info in global_index.items()
                if info['tag'] in concrete_tags
            ]

            for path, info in target_instances:
                # 1. 声明主体对象 (Declare Subject)
                # 关键点：虽然 path 指向的是具体类，但在 SMT 里我们将其声明为抽象类类型 (tgt_sort)
                # 这样它才能被 SMT 模板中的 (forall ((c ATOMIC-SW...)) ...) 捕获
                subj_smt_name = self._path_to_smt_name(path)
                self._declare_const(subj_smt_name, tgt_sort)

                # 2. 录入属性/关系数据 (Populate Predicates)
                for prop in entry.get("properties", []):
                    role = prop.get("role")
                    p_xml_tag = prop.get("xml_tag")  # 子元素标签，如 RUNNABLE-ENTITY
                    p_xpath = prop.get("xpath")
                    p_sort = prop.get("smt_sort", "Int")
                    predicates = prop.get("smt_predicates", {})  # 定义了如何录入数据，如 (ownsRunnable SUB PROP)
                    is_ref = prop.get("is_cross_file_ref", False)

                    # 回溯源文件，提取该属性的具体值
                    # - 如果是包含关系，val 是子元素的 ShortName
                    # - 如果是引用关系，val 是目标元素的 DEST 路径
                    extracted_values = self._extract_element_property_value(
                        info['source_file'], path, p_xml_tag, p_xpath,
                        is_ref=is_ref  # ✅ 传递 is_ref 参数
                    )

                    for val in extracted_values:
                        prop_smt_name = ""

                        if is_ref:
                            # 情况 A: 引用 (Ref)
                            ref_path = val
                            # 确保引用目标在全局索引中存在
                            if ref_path in global_index:
                                prop_smt_name = self._path_to_smt_name(ref_path)
                                # 声明引用目标对象
                                self._declare_const(prop_smt_name, p_sort)
                            else:
                                # 引用目标未解析，无法生成关系事实，跳过
                                continue
                        else:
                            # 情况 B: 子元素 (Child)
                            # 构造子元素的完整路径
                            child_path = f"{path}/{val}"
                            if child_path in global_index:
                                prop_smt_name = self._path_to_smt_name(child_path)
                                # 声明子元素对象
                                self._declare_const(prop_smt_name, p_sort)
                            else:
                                # 情况 C: 普通数据值 (如 String 类型)
                                if p_sort == "String":
                                    # 简单的字符串转义
                                    safe_val = val.replace('"', '\\"')
                                    prop_smt_name = f'"{safe_val}"'
                                else:
                                    continue

                        # 生成谓词事实 (Fact Assertion)
                        for pred_name, pred_info in predicates.items():
                            if isinstance(pred_info, dict):
                                arg_list = pred_info.get("args", [])
                                expected_arity = len(arg_list)

                                # ✅ [新增] 计算实际参数类型
                                actual_arg_sorts = []
                                for a in arg_list:
                                    if a == "SUBJECT":
                                        actual_arg_sorts.append(self._normalize_sort(tgt_sort))
                                    elif a == "PROPERTY":
                                        actual_arg_sorts.append(self._normalize_sort(p_sort))
                                    else:
                                        actual_arg_sorts.append("Unknown")
                            else:
                                expected_arity = 1
                                actual_arg_sorts = [self._normalize_sort(p_sort)]

                            # ✅ [修改] 传入参数类型进行匹配
                            matched_pred_name = self._match_predicate_in_template(
                                pred_name,
                                expected_arity,
                                actual_arg_sorts
                            )

                            if matched_pred_name is None:
                                self.skipped_predicates.append({
                                    "constraint_id": cid,
                                    "mapping_predicate": pred_name,
                                    "expected_arity": expected_arity,
                                    "actual_arg_sorts": actual_arg_sorts,
                                    "property_role": role,
                                    "source": "cross_file",
                                    "reason": f"谓词 '{pred_name}' 在SMT模板中未找到参数类型匹配的声明"
                                })
                                print(
                                    f"[WARN] [跨文件] 跳过谓词 '{pred_name}' (约束: {cid}): 参数类型 {actual_arg_sorts} 不匹配")
                                continue

                            # 🔥 [CRITICAL FIX] 跨文件事实生成也要检查返回类型
                            matched_signature = self.predicate_signatures.get(matched_pred_name)
                            if matched_signature:
                                ret_type = matched_signature[1]
                                if ret_type != 'Bool':
                                    print(
                                        f"[WARN] [跨文件] 跳过非布尔谓词 '{matched_pred_name}' (约束: {cid}): 返回类型 {ret_type}")
                                    continue

                            if matched_pred_name != pred_name:
                                print(
                                    f"[INFO] [跨文件] 谓词映射: '{pred_name}' → '{matched_pred_name}' (约束: {cid})")

                            args = []
                            if isinstance(pred_info, dict):
                                for arg_idx, arg in enumerate(pred_info.get("args", [])):
                                    if arg == "SUBJECT":
                                        # 使用谓词签名中的类型
                                        if matched_signature and arg_idx < len(matched_signature[0]):
                                            self._declare_const(subj_smt_name,
                                                                matched_signature[0][arg_idx])
                                        args.append(subj_smt_name)
                                    elif arg == "PROPERTY":
                                        if matched_signature and arg_idx < len(matched_signature[0]):
                                            self._declare_const(prop_smt_name,
                                                                matched_signature[0][arg_idx])
                                        args.append(prop_smt_name)
                                    else:
                                        args.append(arg)
                            else:
                                if matched_signature and len(matched_signature[0]) > 0:
                                    self._declare_const(prop_smt_name, matched_signature[0][0])
                                args = [prop_smt_name]

                            fact = f"(assert ({matched_pred_name} {' '.join(args)}))"
                            self.smt_facts.append(fact)
                            count += 1

                            self.fact_metadata.append({
                                "constraint_id": cid,
                                "fact": fact,
                                "subject": path,
                                "property_role": role,
                                "value": val,
                                "pred_name": matched_pred_name,
                                "original_pred_name": pred_name,
                                "matched_signature": matched_signature
                            })

        return count

    # -------------------------
    # Logical pattern emitter
    # -------------------------
    def _emit_logical_pattern(self, lp: Dict[str, Any], subj_name: str, prop_instances: Dict[str, List[str]],
                              cid: Optional[str]):
        """
        在模板驱动架构下，logical_pattern 仅用于文档说明。
        验证器不再根据它生成逻辑公理（公理已在 SMT 模板中）。

        此方法保留为空操作，以保持向后兼容性。
        """
        ptype = lp.get("type", "none")

        if ptype in ["none", "documentation", ""]:
            # 模板驱动模式：不生成任何逻辑断言
            # 所有逻辑公理应该已经在 SMT 模板中定义
            return

        # 兼容旧版本：如果仍然使用旧格式，发出警告
        if ptype in ["forall_implication", "not_both", "exists_unique", "simple_assert"]:
            print(f"[WARN] 约束 {cid} 使用旧版 logical_pattern 格式。")
            print(f"       在模板驱动架构下，逻辑公理应在 SMT 模板中定义，而非通过 mapping 生成。")
            # 不再生成断言，避免重复
            return

    def _normalize_sort(self, sort: Optional[str]) -> str:
        """
        清洗从 mapping 里拿到的 sort 字符串：
          - 去掉首尾空白
          - 处理 xsd: 前缀（xsd:string → String, xsd:integer → Int）
          - 如果包含空格，只取第一个 token
          - 去掉非法字符
          - 尝试在模板中匹配相似的Sort名
        """
        if sort is None:
            sort = ""
        s = str(sort).strip()
        if not s:
            return "Int"

        # ✅ [新增] 处理 xsd: 前缀的常见类型映射
        xsd_mapping = {
            "xsd:string": "String",
            "xsd_string": "String",
            "xsd:integer": "Int",
            "xsd_integer": "Int",
            "xsd:int": "Int",
            "xsd_int": "Int",
            "xsd:boolean": "Bool",
            "xsd_boolean": "Bool",
            "xsd:bool": "Bool",
            "xsd_bool": "Bool",
            "xsd:decimal": "Real",
            "xsd_decimal": "Real",
            "xsd:float": "Real",
            "xsd_float": "Real",
            "xsd:double": "Real",
            "xsd_double": "Real",
            "string": "String",
            "integer": "Int",
            "boolean": "Bool",
            "float": "Real",
            "double": "Real",
        }

        s_lower = s.lower()
        if s_lower in xsd_mapping:
            return xsd_mapping[s_lower]

        # 如果有人错误地写了 "PORTS P-PORT-PROTOTYPE" 这种，只取第一个 token
        tokens = s.split()
        s = tokens[0]

        # 去掉非法字符（包括冒号）
        s = re.sub(r'[^A-Za-z0-9_\-]', '_', s)
        s = s.strip("_")
        if not s:
            return "Int"

        # sort 名必须是合法 SMT 标识符，首字符不能是数字
        if not re.match(r'^[A-Za-z_]', s):
            s = "_" + s

        # ✅ 如果清洗后的Sort不在模板中，尝试相似匹配
        builtin_sorts = {"Int", "Bool", "Real", "String"}
        if s not in self.template_sorts and s not in builtin_sorts:
            matched_sort = self._match_sort_in_template(s)
            if matched_sort:
                return matched_sort
            # ✅ [新增] 如果仍然找不到，打印警告
            # Sort会被自动声明，但可能导致谓词参数类型不匹配
            print(f"[WARN] Sort '{s}' 不在模板中，将自动声明（可能导致类型不匹配）")

        return s

    def _match_sort_in_template(self, sort_name: str) -> Optional[str]:
        """
        在模板中查找相似的Sort名

        匹配策略：
        1. 精确匹配
        2. 大小写不敏感匹配
        3. 去除连字符/下划线后匹配
        """
        # 精确匹配
        if sort_name in self.template_sorts:
            return sort_name

        # 大小写不敏感匹配
        lower_sort = sort_name.lower().replace('-', '').replace('_', '')
        for ts in self.template_sorts:
            if ts.lower().replace('-', '').replace('_', '') == lower_sort:
                return ts

        return None

    def _is_subtype_of(self, child_sort: str, parent_sort: str) -> bool:
        """
        检查child_sort是否是parent_sort的子类型
        基于inheritance_map进行判断
        """
        if child_sort == parent_sort:
            return True

        # 检查inheritance_map
        if parent_sort in self.inheritance_map:
            return child_sort in self.inheritance_map[parent_sort]

        return False

    def validate_constraints(self, xml_content: str) -> Dict[str, Any]:
        """
        Main entry. Returns a dict with solver status and output.

        🔥 [修改] 选择性加载SMT断言，避免全量加载导致unknown
        """
        # parse xml
        root = self._parse_xml_root(xml_content)
        if root is None:
            return {"valid": False, "status": "ERROR", "error": "Invalid XML content"}

        # reset
        self.smt_decls = []
        self.smt_facts = []
        self.declared_consts = set()
        self.fact_metadata = []
        self.skipped_predicates = []
        self.predicate_match_cache = {}
        self.auto_declared_sorts = set()
        self._const_sort_map = {}

        # SMT generation from mapping
        if not self.mapping:
            print("[WARN] SMT Validator: mapping为空，无法生成数据事实")

        # generate facts per mapping
        self._generate_from_mapping_for_root(root)

        # 🔥 [新增] 详细诊断输出
        print(f"[DIAG] ========== SMT验证诊断 ==========")
        print(f"[DIAG] mapping条目数: {len(self.mapping)}")
        print(f"[DIAG] 生成的常量声明数: {len(self.smt_decls)}")
        print(f"[DIAG] 生成的数据事实数: {len(self.smt_facts)}")
        print(f"[DIAG] 跳过的谓词数: {len(self.skipped_predicates)}")

        # 🔥 在此处添加完整事实打印：
        print(f"\n[DIAG] ========== 完整SMT数据事实 ({len(self.smt_facts)}条) ==========")
        for i, fact in enumerate(self.smt_facts):
            print(f"[FACT {i + 1:3d}] {fact}")
        print(f"[DIAG] =====================================================\n")

        # 收集使用的谓词
        used_predicates = self._collect_used_predicates()
        if self.verbosity >= 1:
            print(f"[DIAG] 使用的谓词数: {len(used_predicates)}")
            print(f"[DIAG] 使用的谓词: {sorted(used_predicates)[:10]}{'...' if len(used_predicates) > 10 else ''}")

        # 🔥 新增：运行时接线分析（基于当前这一个 ARXML）
        runtime_wiring = None
        if self.enable_runtime_wiring_diag:
            runtime_wiring = self.analyze_runtime_wiring()  # 利用 self.fact_metadata + self.mapping

            stats = runtime_wiring.get("stats", {})
            if self.verbosity >= 1:
                print(
                    "[DIAG] 运行时接线统计: "
                    f"全接线={stats.get('full', 0)}, "
                    f"半接线={stats.get('partial', 0)}, "
                    f"未接线={stats.get('unused', 0)}"
                )
            # 也可以打印 top N 约束看谁“真正参与了”本次验证
            top = runtime_wiring.get("top_constraints", [])[:5]
            if self.verbosity >= 2 and top:
                ids = [c["constraint_id"] for c in top]
                print(f"[DIAG] 本次ARXML触发最多的约束TOP: {ids}")

        # compose SMT text
        decls_text = "\n".join(self.smt_decls)
        facts_text = "\n".join(self.smt_facts)
        constraint_count = len(self.smt_facts)

        smt_parts = []

        # 🔥 [修改] 使用声明部分而非完整模板
        if self.template_declarations:
            smt_parts.append("; --- SMT TEMPLATE DECLARATIONS ---")
            smt_parts.append(self.template_declarations)
        else:
            smt_parts.append("; generated SMT script (no template provided)")

        smt_parts.append("\n; --- AUTO-GENERATED DECLS ---")
        if decls_text:
            smt_parts.append(decls_text)

        smt_parts.append("\n; --- AUTO-GENERATED FACTS ---")
        if facts_text:
            smt_parts.append(facts_text)

        # 如果事实为0，跳过Z3
        if constraint_count == 0:
            print("[INFO] SMT Validator: No facts generated from mapping. Skipping solver.")
            return {
                "valid": True,
                "constraint_count": 0,
                "satisfied_count": 0,
                "smt": "\n\n".join(smt_parts),
                "mapping_json": json.dumps(self.mapping, indent=2, ensure_ascii=False),
                "solver": {"status": "SKIPPED", "reason": "No SMT facts generated"}
            }

        # 🔥 [修改] 选择性加载相关断言，启用不完备理论过滤，限制传播轮次
        relevant_assertions = self._get_relevant_assertions(
            used_predicates,
            filter_incomplete_theory=True,  # 过滤使用Array/String/Seq的断言
            max_propagation_rounds=1  # 限制传播为1轮，避免过度膨胀
        )
        if relevant_assertions:
            smt_parts.append("\n; --- RELEVANT TEMPLATE ASSERTIONS ---")
            smt_parts.append(relevant_assertions)

        # ensure check-sat at end
        smt_parts.append("\n(check-sat)\n")
        full_smt = "\n\n".join(smt_parts)

        # mapping JSON output
        mapping_json_text = ""
        try:
            mapping_json_text = json.dumps(self.mapping, indent=2, ensure_ascii=False)
        except Exception:
            mapping_json_text = "{}"

        # run z3
        solver_result = None
        incremental_result = None

        if self.z3_cli_available:
            solver_result = self._run_z3_cli(full_smt)
            cli_stdout = solver_result.get("stdout", "")
            if "unsat" in cli_stdout:
                try:
                    import z3
                    incremental_result = self._incremental_validate_with_diagnosis(
                        self.smt_facts,
                        self.template_declarations + "\n" + relevant_assertions  # 🔥 使用选择性加载的断言
                    )
                except ImportError:
                    incremental_result = {"error": "Z3 Python API not available for diagnosis"}
        else:
            try:
                import z3
                solver_result = self._run_z3_python(full_smt)
                py_status = solver_result.get("status", "")
                if "unsat" in py_status:
                    incremental_result = self._incremental_validate_with_diagnosis(
                        self.smt_facts,
                        self.template_declarations + "\n" + relevant_assertions  # 🔥 使用选择性加载的断言
                    )
            except ImportError:
                solver_result = {"status": "SKIPPED", "reason": "Z3 not available"}

        # 结果判断
        is_valid = False
        satisfied_count = 0

        if solver_result:
            cli_stdout = solver_result.get("stdout", "")
            py_status = solver_result.get("status", "")
            # print(f"[DEBUG] SMT solver_result: {solver_result}")

            if "unsat" in cli_stdout or "unsat" in py_status:
                print(f"\n❌ SMT验证结果: UNSAT (约束不可满足)")
                is_valid = False
            elif "sat" in cli_stdout or "sat" in py_status:
                print(f" SMT验证结果: SAT (约束满足)")
                is_valid = True
                satisfied_count = constraint_count
            elif "unknown" in cli_stdout or "unknown" in py_status:
                # 🔥 [新增] 处理unknown情况
                print("[WARN] Z3 returned 'unknown' - 约束过于复杂或超时")
                is_valid = False
                solver_result["warning"] = "Z3 returned unknown (timeout or complexity)"
            elif solver_result.get("status") == "SKIPPED":
                is_valid = True
                solver_result["warning"] = "Z3 not available, validation skipped"
            else:
                is_valid = False
                # 🔥 [修复] 打印详细错误信息
                print(f"\n❌ SMT验证结果: 未知状态")
                if solver_result.get("error"):
                    print(f"   错误信息: {solver_result['error']}")
                if solver_result.get("traceback"):
                    print(f"   堆栈追踪:\n{solver_result['traceback'][:500]}...")
                if solver_result.get("stderr"):
                    print(f"   标准错误: {solver_result['stderr']}")
                # 打印完整的 solver_result 用于调试
                print(f"   solver_result: {solver_result}")

        # 打印诊断信息
        if incremental_result and not is_valid:
            print(f"[DEBUG] SMT incremental_result: {incremental_result}")
            diagnosis_text = incremental_result.get("diagnosis", "")
            if diagnosis_text:
                print("\n" + diagnosis_text)
            conflicts = incremental_result.get("conflicting_facts", [])
            if conflicts:
                print(f"\n🔍 发现 {len(conflicts)} 个约束冲突:")
                for conflict in conflicts[:5]:
                    idx = conflict.get("index", -1)
                    cid = conflict.get("constraint_id", "UNKNOWN_CONSTRAINT")
                    role = conflict.get("property_role")
                    prefix = f"  - 约束 {cid}"
                    if role:
                        prefix += f" / 属性 {role}"
                    prefix += f" / 第 {idx + 1} 个断言: "
                    print(prefix + conflict.get("fact", "")[:100] + "...")

        # 🔥 [新增] 验证有效性检查
        validation_effective = len(self.smt_facts) > 0 and len(used_predicates) > 0

        # 🔥 [新增] 详细诊断输出，用于验证系统正确性
        if self.smt_facts and used_predicates:
            print("\n" + "=" * 60)
            print("🔍 SMT验证详细诊断报告")
            print("=" * 60)

            # 1. 显示谓词到断言的映射关系
            print("\n📋 谓词-断言关联:")
            for pred in sorted(used_predicates)[:10]:
                assertion_ids = self.predicate_to_assertions.get(pred, set())
                # 也检查变体
                base_name, _ = self._parse_predicate_name_suffix(pred)
                if base_name in self.predicate_base_to_variants:
                    for actual_name, _, _, _ in self.predicate_base_to_variants[base_name]:
                        assertion_ids = assertion_ids.union(
                            self.predicate_to_assertions.get(actual_name, set())
                        )
                print(f"   {pred}: 关联 {len(assertion_ids)} 个断言")

            # 2. 显示加载的断言示例（前3个）
            # 📝 加载的断言示例 (前3个):
            if relevant_assertions:
                print("\n📝 加载的断言示例 (前3个):")
                # 🔥 [修复] 使用正则表达式直接匹配完整的assert语句
                import re
                # 匹配从 (assert 开始到对应的闭括号
                assertion_pattern = re.compile(r'\(assert\s+[^)]*(?:\([^)]*\)[^)]*)*\)', re.DOTALL)
                assertion_matches = assertion_pattern.findall(relevant_assertions)

                # 如果正则匹配不到，尝试简单按行匹配
                if not assertion_matches:
                    assertion_matches = [line.strip() for line in relevant_assertions.split('\n')
                                         if line.strip().startswith('(assert')]

                for i, assertion in enumerate(assertion_matches[:3]):
                    # 清理多余空白
                    clean_assertion = ' '.join(assertion.split())
                    display = clean_assertion[:200] + "..." if len(clean_assertion) > 200 else clean_assertion
                    print(f"   {i + 1}. {display}")

                if len(assertion_matches) > 3:
                    print(f"   ... 还有 {len(assertion_matches) - 3} 个断言")

            # 3. 显示数据事实与断言的交集谓词
            fact_predicates = set()
            for fact in self.smt_facts:
                match = re.search(r'\(assert\s+\(\s*([A-Za-z_][A-Za-z0-9_\-]*)', fact)
                if match:
                    fact_predicates.add(match.group(1))

            assertion_predicates = set()
            if relevant_assertions:
                for match in re.finditer(r'\(\s*([A-Za-z_][A-Za-z0-9_\-]+)\s+', relevant_assertions):
                    name = match.group(1)
                    if name in self.predicate_signatures:
                        assertion_predicates.add(name)

            shared_predicates = fact_predicates.intersection(assertion_predicates)
            print(f"\n🔗 数据-断言共享谓词: {len(shared_predicates)} 个")
            if shared_predicates:
                print(f"   {sorted(shared_predicates)[:10]}")

            # 4. 验证有效性指标
            effectiveness_score = len(shared_predicates) / max(len(fact_predicates), 1) * 100
            print(f"\n📊 验证有效性评分: {effectiveness_score:.1f}%")
            if effectiveness_score < 50:
                print("   ⚠️ 警告: 数据事实与加载断言的关联度较低，验证可能不完整")
            elif effectiveness_score >= 80:
                print("   ✅ 良好: 数据事实与断言高度关联")

            print("=" * 60 + "\n")

        return {
            "valid": is_valid,
            "validation_effective": validation_effective,  # 🔥 新增：验证是否真正有效
            "constraint_count": constraint_count,
            "satisfied_count": satisfied_count,
            "satisfaction_rate": (satisfied_count / constraint_count * 100) if constraint_count > 0 else 0,  # 🔥 新增
            "facts_generated": len(self.smt_facts),  # 🔥 新增
            "predicates_used": len(used_predicates),  # 🔥 新增
            "runtime_wiring": runtime_wiring,  # 🔥 新增
            "assertions_loaded": len(relevant_assertions.split('\n')) if relevant_assertions else 0,  # 🔥 新增
            "smt": full_smt,
            "mapping_json": mapping_json_text,
            "solver": solver_result,
            "diagnosis": incremental_result,
            "skipped_predicates": self.skipped_predicates,
            "predicate_match_stats": {
                "total_matched": len(self.predicate_match_cache),
                "skipped_count": len(self.skipped_predicates),
                "used_predicates": list(used_predicates),  # 🔥 [新增]
                "loaded_assertions": len(self.template_assertions) if hasattr(self, 'template_assertions') else 0
            }
        }
    # -------------------------
    # Solver invocations
    # -------------------------
    def _run_z3_cli(self, full_smt: str) -> Dict[str, Any]:
        try:
            with tempfile.NamedTemporaryFile('w', suffix='.smt2', delete=False, encoding='utf-8') as tf:
                tf.write(full_smt)
                tf.flush()
                fname = tf.name
            proc = subprocess.run(['z3', fname], capture_output=True, text=True, timeout=30)
            stdout = proc.stdout.strip()
            stderr = proc.stderr.strip()
            # remove temp file
            try:
                os.remove(fname)
            except Exception:
                pass
            return {"method": "z3_cli", "stdout": stdout, "stderr": stderr, "returncode": proc.returncode}
        except Exception as e:
            return {"method": "z3_cli", "error": str(e)}

    def _run_z3_python(self, full_smt: str) -> Dict[str, Any]:
        """
        使用Z3 Python API执行SMT求解

        🔥 [修改] 添加参数调优和更详细的诊断信息
        """
        try:
            import z3
        except ImportError as e:
            return {"method": "python_z3", "error": f"import failed: {e}"}

        try:
            parsed = z3.parse_smt2_string(full_smt)
            s = z3.Solver()

            # 🔥 Z3参数调优
            s.set("timeout", 60000)  # 60秒超时
            s.set("smt.mbqi", True)  # 启用基于模型的量词实例化
            s.set("smt.qi.eager_threshold", 100.0)  # 🔥 修复：使用浮点数

            for f in parsed:
                s.add(f)

            res = s.check()

            result = {
                "method": "python_z3",
                "status": str(res),
                "assertions": len(s.assertions())
            }

            if res == z3.sat:
                result["model"] = str(s.model())
            elif res == z3.unknown:
                # 获取unknown的详细原因
                reason = s.reason_unknown()
                result["reason_unknown"] = reason
                result["statistics"] = str(s.statistics())

                # 分析unknown原因并给出建议
                if "incomplete" in reason:
                    if "array" in reason.lower():
                        result["suggestion"] = "约束使用了Array理论，Z3无法完全判定。建议：过滤使用Array的断言。"
                    elif "seq" in reason.lower() or "string" in reason.lower():
                        result["suggestion"] = "约束使用了Sequence/String理论，Z3无法完全判定。"
                    else:
                        result["suggestion"] = f"不完备理论导致unknown: {reason}"
                elif "timeout" in reason.lower():
                    result["suggestion"] = "求解超时。建议：减少加载的断言数量。"
                elif "canceled" in reason.lower():
                    result["suggestion"] = "求解被取消（资源限制）。"

            return result
        except Exception as e:
            import traceback
            error_result = {
                "method": "python_z3",
                "status": "error",  # 🔥 添加明确的错误状态
                "error": f"parse/solve failed: {e}",
                "traceback": traceback.format_exc()
            }
            print(f"[ERROR] Z3 Python API 执行失败: {e}")  # 🔥 立即打印
            return error_result
    def _incremental_validate_with_diagnosis(self, facts_list: List[str], template_text: str) -> Dict[str, Any]:
        """
        增量验证：逐个断言验证，定位具体冲突

        🔥 [修改] template_text参数现在是选择性加载后的模板（声明+相关断言）
        """
        try:
            import z3
        except ImportError:
            return {"method": "incremental", "error": "z3 not available"}

        try:
            full_context = template_text
            if self.smt_decls:
                decls_text = "\n".join(self.smt_decls)
                full_context = template_text + "\n\n; --- DECLARATIONS ---\n" + decls_text

            # 解析包含声明的完整上下文
            context_assertions = z3.parse_smt2_string(full_context)

            solver = z3.Solver()
            for assertion in context_assertions:
                solver.add(assertion)

            # 检查上下文是否可满足
            if solver.check() == z3.unsat:
                return {
                    "method": "incremental",
                    "valid": False,
                    "error": "SMT template + declarations is unsatisfiable",
                    "failed_at": "context"
                }

            # 逐个添加facts，找到导致unsat的断言
            conflicting_facts = []
            added_facts = []

            for i, fact_str in enumerate(facts_list):
                try:
                    full_script = template_text + "\n\n"
                    if self.smt_decls:
                        full_script += "\n".join(self.smt_decls) + "\n\n"
                    full_script += fact_str

                    all_assertions = z3.parse_smt2_string(full_script)
                    template_assertion_count = len(context_assertions)
                    new_assertions = list(all_assertions)[template_assertion_count:]

                    if not new_assertions:
                        continue

                    solver.push()
                    for fa in new_assertions:
                        solver.add(fa)

                    result = solver.check()
                    if result == z3.unsat:
                        meta = self.fact_metadata[i] if i < len(self.fact_metadata) else {}
                        conflict = {
                            "index": i,
                            "fact": fact_str.strip(),
                            "message": f"第 {i + 1} 个断言导致约束冲突",
                            "context": added_facts[-3:] if len(added_facts) >= 3 else added_facts[:]
                        }
                        conflict.update(meta)
                        conflicting_facts.append(conflict)
                        solver.pop()
                    else:
                        solver.pop()
                        for fa in new_assertions:
                            solver.add(fa)
                        added_facts.append(fact_str.strip()[:80])

                except Exception as e:
                    meta = self.fact_metadata[i] if i < len(self.fact_metadata) else {}
                    conflict = {
                        "index": i,
                        "fact": fact_str.strip(),
                        "error": f"解析失败: {str(e)}"
                    }
                    conflict.update(meta)
                    conflicting_facts.append(conflict)

            if conflicting_facts:
                return {
                    "method": "incremental",
                    "valid": False,
                    "conflicting_facts": conflicting_facts,
                    "total_conflicts": len(conflicting_facts),
                    "total_facts": len(facts_list),
                    "diagnosis": self._generate_conflict_diagnosis(conflicting_facts)
                }

            return {
                "method": "incremental",
                "valid": True,
                "message": "所有断言一致性检查通过"
            }

        except Exception as e:
            import traceback
            return {
                "method": "incremental",
                "error": f"增量验证失败: {str(e)}",
                "traceback": traceback.format_exc()
            }

    def _generate_conflict_diagnosis(self, conflicting_facts: List[Dict]) -> str:
        """生成人类可读的冲突诊断信息"""
        lines = ["🔍 约束冲突诊断报告:"]

        for i, conflict in enumerate(conflicting_facts, 1):
            idx = conflict.get("index", -1)
            fact = conflict.get("fact", "")
            error = conflict.get("error", "")

            cid = conflict.get("constraint_id")
            role = conflict.get("property_role")
            subject = conflict.get("subject")
            pred = conflict.get("pred_name")

            lines.append(f"\n  ❌ 冲突 #{i} (断言 #{idx + 1}):")
            if cid:
                lines.append(f"     约束 ID    : {cid}")
            if subject:
                lines.append(f"     目标元素    : {subject}")
            if role:
                lines.append(f"     属性角色    : {role}")
            if pred:
                lines.append(f"     谓词        : {pred}")

            lines.append(f"     SMT 断言    : {fact}")

            if error:
                lines.append(f"     错误        : {error}")

        lines.append(f"\n  📊 冲突统计: {len(conflicting_facts)} 个约束违反")

        return "\n".join(lines)

    def set_cross_file_resolver(self, resolver):
        """设置跨文件解析器"""
        self.cross_file_resolver = resolver

    def validate_cross_file_constraints(self) -> Dict[str, Any]:
        """
        执行跨文件SMT约束验证

        🔥 [修改] 选择性加载SMT断言
        """
        result = {
            "valid": True,
            "violations": [],
            "stats": {},
            "skipped_predicates": []
        }

        if not self.cross_file_resolver:
            result["error"] = "CrossFileResolver未设置"
            result["valid"] = False
            return result

        # 重置状态
        self.smt_decls = []
        self.smt_facts = []
        self.declared_consts = set()
        self.fact_metadata = []
        self.skipped_predicates = []
        self.predicate_match_cache = {}
        self.auto_declared_sorts = set()  # 🔥 [新增] 重置自动声明的Sort
        self._const_sort_map = {}  # 🔥 [新增] 重置常量Sort映射

        # 生成跨文件SMT事实
        fact_count = self._generate_global_smt_facts()

        result["stats"]["fact_count"] = fact_count
        result["stats"]["skipped_count"] = len(self.skipped_predicates)
        result["skipped_predicates"] = self.skipped_predicates

        if fact_count == 0:
            print("[INFO] 跨文件验证: 未生成任何SMT事实")
            result["stats"]["reason"] = "No cross-file SMT facts generated"
            return result

        # 🔥 [新增] 收集使用的谓词
        used_predicates = self._collect_used_predicates()

        # 组合SMT脚本
        decls_text = "\n".join(self.smt_decls)
        facts_text = "\n".join(self.smt_facts)

        smt_parts = []

        # 🔥 [修改] 使用声明部分
        if self.template_declarations:
            smt_parts.append("; --- SMT TEMPLATE DECLARATIONS ---")
            smt_parts.append(self.template_declarations)

        smt_parts.append("\n; --- CROSS-FILE DECLS ---")
        if decls_text:
            smt_parts.append(decls_text)
        smt_parts.append("\n; --- CROSS-FILE FACTS ---")
        if facts_text:
            smt_parts.append(facts_text)

        # 🔥 [修改] 选择性加载相关断言
        relevant_assertions = self._get_relevant_assertions(
            used_predicates,
            filter_incomplete_theory=True,
            max_propagation_rounds=1
        )
        if relevant_assertions:
            smt_parts.append("\n; --- RELEVANT TEMPLATE ASSERTIONS ---")
            smt_parts.append(relevant_assertions)

        smt_parts.append("\n(check-sat)\n")

        full_smt = "\n\n".join(smt_parts)

        # 执行Z3验证
        solver_result = None
        if self.z3_cli_available:
            solver_result = self._run_z3_cli(full_smt)
        else:
            try:
                import z3
                solver_result = self._run_z3_python(full_smt)
            except ImportError:
                solver_result = {"status": "SKIPPED", "reason": "Z3 not available"}

        # 解析结果
        if solver_result:
            cli_stdout = solver_result.get("stdout", "")
            py_status = solver_result.get("status", "")

            if "unsat" in cli_stdout or "unsat" in py_status:
                result["valid"] = False
                result["violations"].append({
                    "type": "SMT_CONSTRAINT_VIOLATION",
                    "message": "跨文件SMT约束验证失败（UNSAT）"
                })
            elif "unknown" in cli_stdout or "unknown" in py_status:
                # 🔥 [新增] 处理unknown
                result["valid"] = False
                result["violations"].append({
                    "type": "SMT_SOLVER_UNKNOWN",
                    "message": "Z3返回unknown（约束过于复杂或超时）"
                })
            elif "error" in solver_result:
                result["valid"] = False
                result["violations"].append({
                    "type": "SMT_SOLVER_ERROR",
                    "message": solver_result.get("error", "Unknown error")
                })

        result["solver"] = solver_result
        result["stats"]["used_predicates"] = list(used_predicates)

        return result

    def _get_concrete_tags(self, abstract_tag: str) -> Set[str]:
        """
        获取抽象标签对应的所有具体标签。
        解决 SMT Template 使用抽象类 (ATOMIC-SW-...) 而 XML 使用具体类的问题。
        """
        if not abstract_tag:
            return set()
        # 如果在 XsdIndex 加载的继承表中，返回所有子类
        if abstract_tag in self.inheritance_map:
            # print(f"[DEBUG] Mapping Abstract {abstract_tag} -> Concrete {self.inheritance_map[abstract_tag]}")
            return self.inheritance_map[abstract_tag]
        # 否则假设它是具体类，返回自身
        return {abstract_tag}

    def _extract_element_property_value(self, source_file: str, element_path: str,
                                        prop_xml_tag: str, prop_xpath: str = None,
                                        is_ref: bool = False) -> List[str]:
        """
        [跨文件] 回溯源文件，提取指定元素的具体属性值或引用目标路径。

        Args:
            is_ref: True 时提取文本内容（引用路径），False 时优先提取 SHORT-NAME
        """
        try:
            if not hasattr(self, '_file_tree_cache'):
                self._file_tree_cache = {}
            if source_file not in self._file_tree_cache:
                try:
                    self._file_tree_cache[source_file] = ET.parse(source_file)
                except Exception as e:
                    print(f"[WARN] 无法解析文件 {source_file}: {e}")
                    return []

            tree = self._file_tree_cache[source_file]
            root = tree.getroot()
            target_node = self._find_node_by_path(root, element_path)
            if target_node is None:
                return []

            results = []
            search_path = prop_xpath if prop_xpath else prop_xml_tag

            if search_path:
                parts = search_path.split('/')
                nodes = [target_node]
                for part in parts:
                    next_nodes = []
                    for n in nodes:
                        next_nodes.extend([c for c in n if _xml_tag_local(c.tag) == part])
                    nodes = next_nodes

                for n in nodes:
                    if is_ref:
                        # 引用类型：提取文本内容（路径）
                        if n.text and n.text.strip():
                            results.append(n.text.strip())
                    else:
                        # 子元素类型：优先提取 SHORT-NAME
                        sn = _first_text(n, "SHORT-NAME")
                        if sn:
                            results.append(sn)
                        elif n.text and n.text.strip():
                            results.append(n.text.strip())

            return results
        except Exception as e:
            print(f"[WARN] 提取属性值失败 {source_file} :: {element_path}: {e}")
            return []

    def _find_node_by_path(self, root: ET.Element, path: str) -> Optional[ET.Element]:
        """
        根据 SHORT-NAME 路径在 ET.Element 树中查找对应节点。
        用于从 CrossFileResolver 的索引回溯到具体 XML 节点。
        """
        # 移除开头的 /
        clean_path = path.strip('/')
        parts = [p for p in clean_path.split('/') if p]
        def recursive_find(node, remaining_parts):
            if not remaining_parts:
                return node
            target_name = remaining_parts[0]
            # 1. 在直接子节点中查找 SHORT-NAME 匹配
            for child in node:
                sn = _first_text(child, "SHORT-NAME")
                if sn == target_name:
                    res = recursive_find(child, remaining_parts[1:])
                    if res is not None:
                        return res
            # 2. 如果没找到，尝试穿透非命名容器（如 ELEMENTS, COMPONENTS 等 wrapper）
            for child in node:
                if _first_text(child, "SHORT-NAME") is None:
                    # 路径部分不减少，继续在 wrapper 内部找当前 target_name
                    res = recursive_find(child, remaining_parts)
                    if res is not None:
                        return res
            return None
        return recursive_find(root, parts)

    def _path_to_smt_name(self, path: str) -> str:
        """将SHORT-NAME-PATH转换为合法的SMT标识符"""
        # 移除开头的斜杠，替换特殊字符
        name = path.lstrip('/')
        name = name.replace('/', '_').replace('-', '_').replace('.', '_')
        # 确保以字母开头
        if name and not name[0].isalpha():
            name = 'elem_' + name
        return _sanitize_ident(name)

    def _log_skip_predicate_once(self, skip_info: Dict[str, Any]):
        """去重打印跳过信息"""
        cid = skip_info.get("constraint_id")
        mp = skip_info.get("mapping_predicate")
        reason = skip_info.get("reason", "")

        # 构建去重键
        key = (cid, mp, reason)
        if key in self._skip_warned_keys:
            return
        self._skip_warned_keys.add(key)

        if reason == "no_matching_predicate":
            arg_sorts = skip_info.get("actual_arg_sorts", [])
            print(f"[WARN] 跳过谓词 '{mp}' (约束: {cid}): 模板中未找到参数类型匹配的声明")
            if arg_sorts:
                print(f"       期望参数类型: {list(arg_sorts)}")
        elif reason == "no_matching_function":
            ret_sort = skip_info.get("expected_return_sort", "Unknown")
            print(f"[WARN] 跳过函数 '{mp}' (约束: {cid}): 模板中未找到返回类型匹配的声明")
            print(f"       期望返回类型: {ret_sort}")
        elif reason == "non_boolean_predicate":
            ret_type = skip_info.get("return_type")
            print(f"[WARN] 跳过非布尔谓词 '{mp}' (约束: {cid}): 返回类型为 {ret_type}")
        else:
            print(f"[WARN] 跳过 '{mp}' (约束: {cid}): {reason}")

    def analyze_constraint_wiring(self) -> Dict[str, Any]:
        """
        静态分析 mapping_smt.json + SMT 模板 的“接线情况”。

        维度：
        - data_wired: 至少有一个 property/target 有 xml_tag/xpath，可以从 ARXML 实际抽数据
        - symbol_wired: 至少有一个 smt_predicate 能在模板里找到匹配的 declare-fun（签名对得上）
        - logic_wired: 至少有一个映射到的谓词实际出现在模板断言里（predicate_to_assertions 非空）

        返回结构示例:
        {
          "total_constraints": 123,
          "fully_wired": 45,
          "half_wired": 60,
          "unwired": 18,
          "by_constraint": {
            "TPS_SWCT_01080": {
              "class": "half_wired",
              "data_wired": True,
              "symbol_wired": True,
              "logic_wired": False,
              "missing_predicates": ["hasDelegationPort"],
              "unused_predicates": ["has_port__2"],
              "details": [...]
            },
            ...
          }
        }
        """
        report: Dict[str, Any] = {
            "total_constraints": 0,
            "fully_wired": 0,
            "half_wired": 0,
            "unwired": 0,
            "by_constraint": {}
        }

        if not self.mapping:
            print("[WARN] analyze_constraint_wiring: mapping 为空，无法分析接线")
            return report

        # 方便判断“谓词是否被任何断言使用”
        predicate_to_assertions = self.predicate_to_assertions or {}
        predicate_base_to_variants = self.predicate_base_to_variants or {}

        for entry in self.mapping:
            cid = entry.get("constraint_id", "<unknown>")
            props = entry.get("properties") or []
            target = entry.get("target") or {}

            report["total_constraints"] += 1

            tgt_sort_raw = target.get("target_sort")
            tgt_sort = self._normalize_sort(tgt_sort_raw) if tgt_sort_raw else None

            data_wired = False
            symbol_wired = False
            logic_wired = False

            missing_preds: List[str] = []
            unused_preds: List[str] = []
            prop_details: List[Dict[str, Any]] = []

            # 1) 只要 target_xml 或者任意 property 有 xml_tag/xpath，就认为在数据侧“有线”
            if (target.get("target_xml") and target["target_xml"].get("xml_tag")):
                data_wired = True

            for p in props:
                role = p.get("role")
                xml_tag = p.get("xml_tag")
                xpath = p.get("xpath")
                p_sort_raw = p.get("smt_sort") or tgt_sort
                p_sort = self._normalize_sort(p_sort_raw) if p_sort_raw else None

                if xml_tag or xpath:
                    data_wired = True

                smt_preds = p.get("smt_predicates") or {}
                if not smt_preds:
                    # 这个 property 只是纯数据，没有连到 SMT，也记一下
                    prop_details.append({
                        "role": role,
                        "xml_tag": xml_tag,
                        "xpath": xpath,
                        "smt_predicates": [],
                        "symbol_wired": False,
                        "logic_wired": False,
                    })
                    continue

                for mapping_name, pred_info in smt_preds.items():
                    # 兼容两种形式：mapping里是 object + args / 简单字符串
                    if isinstance(pred_info, dict):
                        args_template = pred_info.get("args", [])
                    else:
                        args_template = ["PROPERTY"]  # 简单形式默认一元谓词

                    # 根据 args_template 生成期望的参数 sort （尽量贴合 _generate_from_mapping_for_root 的逻辑）:contentReference[oaicite:1]{index=1}
                    expected_sorts: List[str] = []
                    for a in args_template:
                        if a == "SUBJECT":
                            expected_sorts.append(tgt_sort or "Unknown")
                        elif a == "PROPERTY":
                            expected_sorts.append(p_sort or "Unknown")
                        else:
                            expected_sorts.append("Unknown")

                    expected_arity = len(expected_sorts) if expected_sorts else -1

                    matched_name = self._match_predicate_in_template(
                        mapping_name,
                        expected_arity,
                        expected_sorts
                    )

                    this_symbol_wired = False
                    this_logic_wired = False

                    if matched_name is None:
                        missing_preds.append(mapping_name)
                    else:
                        this_symbol_wired = True

                        # 看这个谓词（含变体）是否真的被某条断言使用
                        used_asserts: Set[int] = set()
                        if matched_name in predicate_to_assertions:
                            used_asserts |= predicate_to_assertions[matched_name]

                        base_name, _ = self._parse_predicate_name_suffix(matched_name)
                        if base_name in predicate_base_to_variants:
                            for actual_name, _, _, _ in predicate_base_to_variants[base_name]:
                                if actual_name in predicate_to_assertions:
                                    used_asserts |= predicate_to_assertions[actual_name]

                        if used_asserts:
                            this_logic_wired = True
                        else:
                            unused_preds.append(matched_name)

                    symbol_wired = symbol_wired or this_symbol_wired
                    logic_wired = logic_wired or this_logic_wired

                    prop_details.append({
                        "role": role,
                        "xml_tag": xml_tag,
                        "xpath": xpath,
                        "mapping_predicate": mapping_name,
                        "matched_predicate": matched_name,
                        "expected_sorts": expected_sorts,
                        "symbol_wired": this_symbol_wired,
                        "logic_wired": this_logic_wired,
                    })

            # 约束级别分类
            if data_wired and logic_wired:
                klass = "fully_wired"
                report["fully_wired"] += 1
            elif data_wired or symbol_wired or logic_wired:
                # 有一边接上了（能从ARXML抽到数据，或者能找到SMT谓词），但是没形成完整闭环
                klass = "half_wired"
                report["half_wired"] += 1
            else:
                klass = "unwired"
                report["unwired"] += 1

            report["by_constraint"][cid] = {
                "class": klass,
                "data_wired": data_wired,
                "symbol_wired": symbol_wired,
                "logic_wired": logic_wired,
                "missing_predicates": sorted(set(missing_preds)),
                "unused_predicates": sorted(set(unused_preds)),
                "details": prop_details,
            }

        # 打一点摘要日志，帮助你定位“全接线”约束
        print("========== 约束接线总览 ==========")
        print(f"  总约束数: {report['total_constraints']}")
        print(f"  全接线:   {report['fully_wired']}")
        print(f"  半接线:   {report['half_wired']}")
        print(f"  未接线:   {report['unwired']}")

        fully_ids = [
            cid for cid, info in report["by_constraint"].items()
            if info["class"] == "fully_wired"
        ]
        print(f"  部分全接线约束ID: {fully_ids[:10]}{' ...' if len(fully_ids) > 10 else ''}")
        print("==================================")

        return report

    def analyze_runtime_wiring(self):
        """
        基于当前这次验证 run 的 fact_metadata，分析每个 constraint_id 的“运行时接线情况”。

        返回一个 list，每个元素:
        {
          "constraint_id": str,
          "declared_predicates": [...],   # mapping 中声明要用的谓词(基础名)
          "grounded_predicates": [...],   # 本次事实中真的出现过的谓词(基础名)
          "missing_predicates": [...],    # 声明了但这次一个 fact 都没生成的谓词
          "wiring_ratio": 0.0~1.0,        # grounded/declared
          "fact_count": int,              # 本次 run 中生成的 fact 数
        }
        """
        # 1. 从 mapping 收集“声明要用的谓词”(基础名)
        cid_to_declared = defaultdict(set)
        for entry in self.mapping:
            cid = entry.get("constraint_id") or entry.get("id")
            if not cid:
                continue
            for prop in entry.get("properties", []):
                smt_preds = prop.get("smt_predicates", {})
                for mp_name, info in smt_preds.items():
                    base, _ = self._parse_predicate_name_suffix(mp_name)
                    cid_to_declared[cid].add(base)

        # 2. 从 fact_metadata 收集“本次 run 真正用到的谓词”(基础名) + fact 数
        cid_to_grounded = defaultdict(set)
        cid_to_fact_count = defaultdict(int)

        for meta in self.fact_metadata:
            cid = meta.get("constraint_id")
            if not cid:
                continue

            cid_to_fact_count[cid] += 1

            if meta.get("type") == "predicate":
                name = meta.get("pred_name")
            elif meta.get("type") == "function":
                name = meta.get("function_name")
            else:
                name = None

            if name:
                base, _ = self._parse_predicate_name_suffix(name)
                cid_to_grounded[cid].add(base)

        # 3. 汇总 wiring 指标
        report = []
        for cid, declared in cid_to_declared.items():
            if not declared:
                continue
            grounded = cid_to_grounded.get(cid, set())
            intersect = declared & grounded
            missing = declared - grounded

            wiring_ratio = len(intersect) / len(declared) if declared else 0.0

            report.append({
                "constraint_id": cid,
                "declared_predicates": sorted(declared),
                "grounded_predicates": sorted(grounded),
                "missing_predicates": sorted(missing),
                "wiring_ratio": wiring_ratio,
                "fact_count": cid_to_fact_count.get(cid, 0),
            })

        # 按“接线程度 + fact 数”排序
        report.sort(key=lambda r: (-(r["wiring_ratio"]), -r["fact_count"]))
        return report

    def _extract_scalar_literal_from_element(self, elem: ET.Element, p_sort: Optional[str]) -> Optional[str]:
        """
        从属性对应的 XML 元素里，抽取一个可以直接用于 SMT 的标量字面量：
        - Int / Real / Bool

        p_sort 为 mapping 中配置的 smt_sort / smtType，用于决定解析方式。
        """
        if elem is None:
            return None

        norm_sort = self._normalize_sort(p_sort or "Int")

        # 1. 优先用元素自身 text
        text = (elem.text or "").strip() if elem.text else ""

        # 2. AUTOSAR 里很多数值写在 <VALUE> 子元素里
        if not text:
            v = elem.find("VALUE")
            if v is not None and v.text:
                text = v.text.strip()

        if not text:
            return None

        # Int
        if norm_sort == "Int":
            try:
                int(text)
            except ValueError:
                print(f"[WARN] 属性值 '{text}' 不是合法的 Int，忽略该值")
                return None
            return text

        # Real
        if norm_sort == "Real":
            try:
                float(text)
            except ValueError:
                print(f"[WARN] 属性值 '{text}' 不是合法的 Real，忽略该值")
                return None
            return text

        # Bool
        if norm_sort == "Bool":
            low = text.lower()
            if low in ("true", "1"):
                return "true"
            if low in ("false", "0"):
                return "false"
            print(f"[WARN] 属性值 '{text}' 不是合法的 Bool，忽略该值")
            return None

        # 其它复杂 Sort（TIME-VALUE 之类）暂时不做通用解析
        return None






