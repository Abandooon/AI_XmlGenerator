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
    # 在 smt_validator.py 第53-94行的 __init__ 方法中添加

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
        # 格式: { "baseName": [(actual_name, arg_types, ret_type, suffix_number), ...] }
        # suffix_number: 0 表示原名, 2 表示 __2, 3 表示 __3, ...
        self.predicate_base_to_variants: Dict[str, List[Tuple[str, List[str], str, int]]] = {}

        # ✅ [新增] 精确谓词名到签名的映射，用于快速查找
        # 格式: { "actualName": (arg_types, ret_type) }
        self.predicate_signatures: Dict[str, Tuple[List[str], str]] = {}

        # ✅ [新增] 跳过的谓词记录
        self.skipped_predicates: List[Dict[str, Any]] = []

        # ✅ [新增] 谓词匹配缓存，避免重复匹配
        # 格式: { (mapping_pred_name, arity): matched_template_pred_name or None }
        self.predicate_match_cache: Dict[Tuple[str, int], Optional[str]] = {}

        # runtime generated
        self.smt_decls: List[str] = []
        self.smt_facts: List[str] = []
        self.declared_consts: Set[str] = set()

        # 🔧 新增：记录运行时自动声明过的 sort，避免重复 declare-sort
        self.auto_declared_sorts: Set[str] = set()

        # ✅ 新增：每个 SMT 断言对应的元信息（约束ID、属性角色、XML 元素等）
        self.fact_metadata: List[Dict[str, Any]] = []

        # mapping loaded from JSON
        self.mapping: List[Dict[str, Any]] = []

        # parent map cache for XML tree navigation
        self._parent_map = None
        self._last_root = None

        # load artifacts
        self._load_smt_template()
        self._load_mapping()
        self.cross_file_resolver = None  # 跨文件解析器
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
        """
        # 重置相关数据结构
        self.template_sorts = set()
        self.template_functions = {}
        self.template_constructors = {}
        self.predicate_base_to_variants = {}
        self.predicate_signatures = {}
        self.predicate_match_cache = {}  # 清空缓存

        # parse declare-sort
        for m in re.finditer(r'\(declare-sort\s+([A-Za-z0-9_\-]+)\s+\d+\)', txt):
            self.template_sorts.add(m.group(1))

        # parse declare-fun (name (args) RET)
        # 同时构建基础名到变体的映射
        for m in re.finditer(r'\(declare-fun\s+([A-Za-z0-9_\-]+)\s*\(([^\)]*)\)\s*([A-Za-z0-9_\-]+)\)', txt):
            fname = m.group(1)
            args_txt = m.group(2).strip()
            ret = m.group(3)
            arg_types = []
            if args_txt:
                arg_types = [tok for tok in re.split(r'\s+', args_txt) if tok]

            # 存储到 template_functions（按返回类型分组）
            key = ret
            self.template_functions.setdefault(key, []).append((fname, arg_types, ret))

            # ✅ 存储精确签名
            self.predicate_signatures[fname] = (arg_types, ret)

            # ✅ 解析基础名和后缀数字
            base_name, suffix_num = self._parse_predicate_name_suffix(fname)

            # ✅ 构建基础名到变体的映射
            variant_info = (fname, arg_types, ret, suffix_num)
            self.predicate_base_to_variants.setdefault(base_name, []).append(variant_info)

        # ✅ 对每个基础名的变体按后缀数字排序（0, 2, 3, 4, ...）
        for base_name in self.predicate_base_to_variants:
            self.predicate_base_to_variants[base_name].sort(key=lambda x: x[3])

        # naive parse of declare-datatypes for constructors
        for m in re.finditer(r'\(declare-datatypes\s*\([^)]*\)\s*\(\s*\(\s*([A-Za-z0-9_\-]+)\s+([^\)]+)\)\s*\)\)', txt,
                             re.S):
            dtype = m.group(1)
            body = m.group(2)
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

    def _match_predicate_in_template(self, mapping_pred_name: str, expected_arity: int = -1) -> Optional[str]:
        """
        在模板中查找与mapping谓词名匹配的实际谓词名

        匹配策略（按优先级）：
        1. 精确匹配：mapping中的名字直接存在于模板中
        2. 基础名匹配：mapping名去掉后缀后匹配模板中的基础名
        3. 按数字顺序优先匹配：__2, __3, ... 顺序
        4. 参数数量匹配：如果指定了expected_arity，优先匹配参数数量相同的

        Args:
            mapping_pred_name: mapping中的谓词名
            expected_arity: 期望的参数数量，-1表示不限制

        Returns:
            模板中匹配的实际谓词名，或None（未找到）
        """
        # 清洗输入的谓词名
        clean_pred_name = self._normalize_predicate_name(mapping_pred_name)

        # 检查缓存
        cache_key = (clean_pred_name, expected_arity)
        if cache_key in self.predicate_match_cache:
            return self.predicate_match_cache[cache_key]

        matched = None

        # 策略1: 精确匹配
        if clean_pred_name in self.predicate_signatures:
            if expected_arity == -1:
                matched = clean_pred_name
            else:
                sig = self.predicate_signatures[clean_pred_name]
                if len(sig[0]) == expected_arity:
                    matched = clean_pred_name

        # 策略2: 基础名匹配
        if matched is None:
            base_name, _ = self._parse_predicate_name_suffix(clean_pred_name)

            if base_name in self.predicate_base_to_variants:
                variants = self.predicate_base_to_variants[base_name]

                # 按后缀数字顺序遍历（已排序：0, 2, 3, 4, ...）
                for actual_name, arg_types, ret_type, suffix_num in variants:
                    if expected_arity == -1:
                        # 不限制参数数量，返回第一个匹配的
                        matched = actual_name
                        break
                    elif len(arg_types) == expected_arity:
                        # 参数数量匹配
                        matched = actual_name
                        break

                # 如果按参数数量没匹配到，放宽条件返回第一个
                if matched is None and variants:
                    matched = variants[0][0]  # 返回后缀数字最小的

        # 策略3: 大小写不敏感匹配（作为最后手段）
        if matched is None:
            lower_pred = clean_pred_name.lower()
            for actual_name, sig in self.predicate_signatures.items():
                if actual_name.lower() == lower_pred:
                    if expected_arity == -1 or len(sig[0]) == expected_arity:
                        matched = actual_name
                        break

        # 缓存结果
        self.predicate_match_cache[cache_key] = matched
        return matched

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
        声明一个常量，支持同一常量的多种Sort声明（取最通用的）
        """
        norm_sort = self._normalize_sort(sort)
        builtin_sorts = {"Int", "Bool", "Real", "String"}

        # 自动声明未知Sort
        if (
                norm_sort not in builtin_sorts
                and norm_sort not in self.template_sorts
                and norm_sort not in self.auto_declared_sorts
        ):
            self.smt_decls.append(f"(declare-sort {norm_sort} 0)")
            self.auto_declared_sorts.add(norm_sort)

        # ✅ [新增] 检查是否已经用不同的Sort声明过
        if name in self.declared_consts:
            # 检查之前声明的Sort是否相同
            if hasattr(self, '_const_sort_map'):
                prev_sort = self._const_sort_map.get(name)
                if prev_sort and prev_sort != norm_sort:
                    # ✅ 检查是否是子类型关系
                    if self._is_subtype_of(prev_sort, norm_sort):
                        # 之前的是子类型，当前的是父类型，使用父类型（更通用）
                        # 需要重新声明（但SMT不支持，所以只记录警告）
                        print(f"[DEBUG] 常量 {name} 类型升级: {prev_sort} → {norm_sort}")
                    elif self._is_subtype_of(norm_sort, prev_sort):
                        # 当前的是子类型，之前的是父类型，保持父类型
                        pass
                    else:
                        # 不兼容的类型
                        print(f"[WARN] 常量 {name} 类型冲突: 已声明为 {prev_sort}, 又被声明为 {norm_sort}")
            return

        self.declared_consts.add(name)

        # ✅ [新增] 记录常量的Sort
        if not hasattr(self, '_const_sort_map'):
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

                if tgt_sort:
                    self._declare_const(subj_name, tgt_sort)
                else:
                    self._declare_const(subj_name, "Int")

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

                        # 修改 _generate_from_mapping_for_root 方法中的谓词断言生成部分
                        # 替换 smt_validator.py 第644-724行

                        # optional: generate simple predicate assertions if mapping asks
                        smt_preds = p.get("smt_predicates") or {}
                        for pred_name, pred_info in smt_preds.items():
                            # ✅ [新增] 计算期望的参数数量
                            if isinstance(pred_info, dict):
                                args = pred_info.get("args", [])
                                expected_arity = len(args)
                            else:
                                expected_arity = 1

                            # ✅ 在模板中匹配谓词名
                            matched_pred_name = self._match_predicate_in_template(pred_name, expected_arity)

                            if matched_pred_name is None:
                                skip_info = {
                                    "constraint_id": cid,
                                    "mapping_predicate": pred_name,
                                    "expected_arity": expected_arity,
                                    "property_role": role,
                                    "reason": f"谓词 '{pred_name}' 在SMT模板中未找到匹配"
                                }
                                self.skipped_predicates.append(skip_info)
                                print(f"[WARN] 跳过谓词 '{pred_name}' (约束: {cid}, 属性: {role}): 模板中未找到匹配")
                                continue

                            if matched_pred_name != pred_name:
                                print(f"[INFO] 谓词映射: '{pred_name}' → '{matched_pred_name}' (约束: {cid})")

                            # ✅ [新增] 获取谓词签名，用于确定正确的参数类型
                            pred_signature = self.predicate_signatures.get(matched_pred_name)

                            if isinstance(pred_info, dict):
                                args_template = pred_info.get("args", [])
                                resolved_args = []
                                resolved_arg_sorts = []  # ✅ 记录参数的Sort

                                for arg_idx, a in enumerate(args_template):
                                    if a == "PROPERTY":
                                        resolved_args.append(prop_smt)
                                        resolved_arg_sorts.append(self._normalize_sort(p_sort))
                                    elif a == "SUBJECT":
                                        # ✅ [关键修复] 检查谓词期望的参数类型
                                        expected_sort = None
                                        if pred_signature and arg_idx < len(pred_signature[0]):
                                            expected_sort = pred_signature[0][arg_idx]

                                        actual_sort = self._normalize_sort(tgt_sort)

                                        # 如果类型不匹配，尝试使用谓词期望的类型重新声明
                                        if expected_sort and expected_sort != actual_sort:
                                            # 检查是否需要使用不同的Sort来声明SUBJECT
                                            if not self._is_subtype_of(actual_sort, expected_sort):
                                                print(f"[WARN] 类型不匹配: 谓词 {matched_pred_name} 参数{arg_idx + 1} "
                                                      f"期望 {expected_sort}, mapping提供 {actual_sort}")
                                                # ✅ 使用谓词期望的类型重新声明SUBJECT
                                                self._declare_const(subj_name, expected_sort)
                                                resolved_arg_sorts.append(expected_sort)
                                            else:
                                                resolved_arg_sorts.append(actual_sort)
                                        else:
                                            resolved_arg_sorts.append(actual_sort)

                                        resolved_args.append(subj_name)
                                    else:
                                        resolved_args.append(a)
                                        resolved_arg_sorts.append("Unknown")

                                # ✅ [新增] 验证参数类型
                                is_valid, error_msg = self._validate_predicate_args(matched_pred_name,
                                                                                    resolved_arg_sorts)
                                if not is_valid:
                                    print(f"[WARN] 谓词参数类型不匹配 ({cid}): {matched_pred_name} - {error_msg}")
                                    # 仍然尝试生成，让Z3报告具体错误

                                base_meta = {
                                    "constraint_id": cid,
                                    "target_sort": tgt_sort,
                                    "subject": subj_name,
                                    "subject_xml_tag": _xml_tag_local(node.tag),
                                    "property_role": role,
                                    "property_sort": p_sort,
                                    "property_xml_tag": _xml_tag_local(fe.tag),
                                    "property_index": idx,
                                    "pred_name": matched_pred_name,
                                    "original_pred_name": pred_name,
                                }

                                fact_str = f"(assert ({matched_pred_name} {' '.join(resolved_args)}))"
                                self.smt_facts.append(fact_str)
                                self.fact_metadata.append(base_meta)

                            else:
                                # simple string形式
                                pred_str = str(pred_info).strip()
                                matched_simple = self._match_predicate_in_template(pred_str, 1)
                                if matched_simple is None:
                                    self.skipped_predicates.append({
                                        "constraint_id": cid,
                                        "mapping_predicate": pred_str,
                                        "expected_arity": 1,
                                        "property_role": role,
                                        "reason": f"谓词 '{pred_str}' 在SMT模板中未找到匹配"
                                    })
                                    print(f"[WARN] 跳过谓词 '{pred_str}' (约束: {cid}): 模板中未找到匹配")
                                    continue

                                fact_str = f"(assert ({matched_simple} {prop_smt}))"
                                self.smt_facts.append(fact_str)
                                meta = dict(base_meta) if 'base_meta' in dir() else {
                                    "constraint_id": cid,
                                    "property_role": role,
                                }
                                meta["pred_name"] = matched_simple
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
                            # ✅ [新增] 计算期望的参数数量
                            if isinstance(pred_info, dict):
                                arg_list = pred_info.get("args", [])
                                expected_arity = len(arg_list)
                            else:
                                expected_arity = 1

                            # ✅ [新增] 在模板中匹配谓词名
                            matched_pred_name = self._match_predicate_in_template(pred_name, expected_arity)

                            if matched_pred_name is None:
                                # ✅ 匹配失败，记录并跳过
                                self.skipped_predicates.append({
                                    "constraint_id": cid,
                                    "mapping_predicate": pred_name,
                                    "expected_arity": expected_arity,
                                    "property_role": role,
                                    "source": "cross_file",
                                    "reason": f"谓词 '{pred_name}' 在SMT模板中未找到匹配"
                                })
                                print(
                                    f"[WARN] [跨文件] 跳过谓词 '{pred_name}' (约束: {cid}): 模板中未找到匹配")
                                continue

                            # ✅ 如果匹配到的名字与原名不同，打印提示
                            if matched_pred_name != pred_name:
                                print(
                                    f"[INFO] [跨文件] 谓词映射: '{pred_name}' → '{matched_pred_name}' (约束: {cid})")

                            args = []
                            if isinstance(pred_info, dict):
                                for arg in pred_info.get("args", []):
                                    if arg == "SUBJECT":
                                        args.append(subj_smt_name)
                                    elif arg == "PROPERTY":
                                        args.append(prop_smt_name)
                                    else:
                                        args.append(arg)
                            else:
                                args = [prop_smt_name]
                                # ✅ 对简单字符串形式也使用匹配后的名字
                                matched_pred_name = self._match_predicate_in_template(str(pred_info), 1)
                                if matched_pred_name is None:
                                    self.skipped_predicates.append({
                                        "constraint_id": cid,
                                        "mapping_predicate": str(pred_info),
                                        "expected_arity": 1,
                                        "property_role": role,
                                        "source": "cross_file",
                                        "reason": f"谓词 '{pred_info}' 在SMT模板中未找到匹配"
                                    })
                                    continue

                            # ✅ 使用匹配后的谓词名
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
                                "original_pred_name": pred_name
                            })

        return count

    def _get_children_tags(self, source_file: str, element_path: str) -> List[str]:
        """
        回溯源文件，获取指定元素的所有直接子元素标签列表。
        用于互斥约束检查 (_check_mutual_exclusion)。
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

            # 收集所有直接子元素的标签名（去除命名空间）
            children_tags = []
            for child in target_node:
                tag = _xml_tag_local(child.tag)
                if tag:
                    children_tags.append(tag)

            return children_tags
        except Exception as e:
            print(f"[WARN] 获取子元素标签失败 {source_file} :: {element_path}: {e}")
            return []

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

    def _validate_predicate_args(self, pred_name: str, arg_sorts: List[str]) -> Tuple[bool, Optional[str]]:
        """
        验证谓词参数类型是否与模板声明匹配

        Args:
            pred_name: 谓词名
            arg_sorts: 参数的Sort列表

        Returns:
            (is_valid, error_message)
        """
        if pred_name not in self.predicate_signatures:
            return True, None  # 谓词不在模板中，跳过验证

        declared_arg_types, ret_type = self.predicate_signatures[pred_name]

        if len(arg_sorts) != len(declared_arg_types):
            return False, f"参数数量不匹配: 期望 {len(declared_arg_types)}, 实际 {len(arg_sorts)}"

        # 检查每个参数类型
        mismatches = []
        for i, (actual, expected) in enumerate(zip(arg_sorts, declared_arg_types)):
            if actual != expected:
                # 检查是否是子类型关系（如 P-PORT-PROTOTYPE 是 PORTS 的子类型）
                if not self._is_subtype_of(actual, expected):
                    mismatches.append(f"参数{i + 1}: 期望 {expected}, 实际 {actual}")

        if mismatches:
            return False, "; ".join(mismatches)

        return True, None

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

    def _find_correct_sort_for_predicate_arg(self, pred_name: str, arg_index: int) -> Optional[str]:
        """
        根据谓词签名，找到指定参数位置期望的Sort

        Args:
            pred_name: 谓词名
            arg_index: 参数索引（0-based）

        Returns:
            期望的Sort名，或None
        """
        if pred_name not in self.predicate_signatures:
            return None

        declared_arg_types, _ = self.predicate_signatures[pred_name]

        if arg_index < len(declared_arg_types):
            return declared_arg_types[arg_index]

        return None

    # -------------------------
    # Top-level validate_constraints API
    # -------------------------
    def validate_constraints(self, xml_content: str) -> Dict[str, Any]:
        """
        Main entry. Returns a dict with solver status and output.
        Workflow:
          - parse xml_content
          - reset generated lists
          - generate SHACL (string)
          - generate SMT decls/facts using mapping
          - compose final SMT script: template + decls + facts + (check-sat)
          - run Z3 (CLI if available) and return results
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
        self.skipped_predicates = []  # ✅ [新增] 重置跳过记录
        self.predicate_match_cache = {}  # ✅ [新增] 重置匹配缓存
        self.auto_declared_sorts = set()  # ✅ 重置自动声明的Sort
        self._const_sort_map = {}  # ✅ [新增] 重置常量Sort映射

        # SMT generation from mapping
        if not self.mapping:
            # fallback: try to auto-generate simple declares for common tags found in template
            # (No mapping means no facts, will lead to 0 data points)
            pass
        # generate facts per mapping
        self._generate_from_mapping_for_root(root)
        # compose SMT text
        decls_text = "\n".join(self.smt_decls)
        facts_text = "\n".join(self.smt_facts)
        # ⬇️ 关键修改：捕获约束数量
        constraint_count = len(self.smt_facts)
        smt_parts = []
        if self.smt_template_text:
            smt_parts.append(self.smt_template_text.rstrip())
        else:
            # minimal header if no template
            smt_parts.append("; generated SMT script (no template provided)")
        smt_parts.append("\n; --- AUTO-GENERATED DECLS ---")
        if decls_text:
            smt_parts.append(decls_text)
        smt_parts.append("\n; --- AUTO-GENERATED FACTS ---")
        if facts_text:
            smt_parts.append(facts_text)
        # ⬇️ 关键修改：如果事实为0，则跳过 Z3 并返回通过
        if constraint_count == 0:
            print("[INFO] SMT Validator: No facts generated from mapping. Skipping solver.")
            return {
                "valid": True,  # 0 个约束 = 默认通过
                "constraint_count": 0,
                "satisfied_count": 0,
                "smt": "\n\n".join(smt_parts),
                "mapping_json": json.dumps(self.mapping, indent=2, ensure_ascii=False),
                "solver": {"status": "SKIPPED", "reason": "No SMT facts generated"}
            }
        # ensure check-sat at end
        smt_parts.append("\n(check-sat)\n")
        full_smt = "\n\n".join(smt_parts)
        # 在 full_smt = "\n\n".join(smt_parts) 之后，添加：
        # print("\n========== DEBUG: 生成的 SMT 脚本 ==========")
        # print(full_smt)
        # print("========== DEBUG END ==========\n")
        # 3) mapping JSON output (string)
        mapping_json_text = ""
        try:
            mapping_json_text = json.dumps(self.mapping, indent=2, ensure_ascii=False)
        except Exception:
            mapping_json_text = "{}"


        # 4) run z3 if available
        solver_result = None
        incremental_result = None
        if self.z3_cli_available:
            solver_result = self._run_z3_cli(full_smt)
            # ✅ 新增：CLI 模式下也执行增量诊断
            cli_stdout = solver_result.get("stdout", "")
            if "unsat" in cli_stdout:
                try:
                    import z3
                    incremental_result = self._incremental_validate_with_diagnosis(
                        self.smt_facts,
                        self.smt_template_text
                    )
                except ImportError:
                    incremental_result = {"error": "Z3 Python API not available for diagnosis"}
        else:
            # try python z3
            try:
                import z3
                solver_result = self._run_z3_python(full_smt)
                # 如果验证失败，执行增量验证以获取诊断信息
                py_status = solver_result.get("status", "")
                if "unsat" in py_status:
                    incremental_result = self._incremental_validate_with_diagnosis(
                        self.smt_facts,
                        self.smt_template_text
                    )
            except ImportError:
                solver_result = {"status": "SKIPPED", "reason": "Z3 not available"}
        # 结果判断
        is_valid = False
        satisfied_count = 0
        if solver_result:
            cli_stdout = solver_result.get("stdout", "")
            py_status = solver_result.get("status", "")
            print(f"[DEBUG] SMT solver_result: {solver_result}")
            if "unsat" in cli_stdout or "unsat" in py_status:
                is_valid = False
            elif "sat" in cli_stdout or "sat" in py_status:
                is_valid = True
                satisfied_count = constraint_count
            elif solver_result.get("status") == "SKIPPED":
                is_valid = True
                solver_result["warning"] = "Z3 not available, validation skipped"
            else:
                is_valid = False

        # ✅ 新增：打印诊断信息
        if incremental_result and not is_valid:
            print(f"[DEBUG] SMT incremental_result: {incremental_result}")
            diagnosis_text = incremental_result.get("diagnosis", "")
            if diagnosis_text:
                print("\n" + diagnosis_text)
            conflicts = incremental_result.get("conflicting_facts", [])
            if conflicts:
                print(f"\n🔍 发现 {len(conflicts)} 个约束冲突:")
                for conflict in conflicts[:5]:  # 最多显示 5 个
                    idx = conflict.get("index", -1)
                    cid = conflict.get("constraint_id", "UNKNOWN_CONSTRAINT")
                    role = conflict.get("property_role")
                    prefix = f"  - 约束 {cid}"
                    if role:
                        prefix += f" / 属性 {role}"
                    prefix += f" / 第 {idx + 1} 个断言: "
                    print(prefix + conflict.get("fact", "")[:100] + "...")

        # 5) return structure
        return {
            "valid": is_valid,
            "constraint_count": constraint_count,
            "satisfied_count": satisfied_count,
            "smt": full_smt,
            "mapping_json": mapping_json_text,
            "solver": solver_result,
            "diagnosis": incremental_result,
            "skipped_predicates": self.skipped_predicates,  # ✅ [新增]
            "predicate_match_stats": {  # ✅ [新增] 匹配统计
                "total_matched": len(self.predicate_match_cache),
                "skipped_count": len(self.skipped_predicates)
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
        try:
            import z3  # type: ignore
        except Exception as e:
            return {"method": "python_z3", "error": f"import failed: {e}"}
        try:
            # parse and check-sat using z3 API
            parsed = z3.parse_smt2_string(full_smt)
            s = z3.Solver()
            if isinstance(parsed, list):
                for f in parsed:
                    s.add(f)
            else:
                s.add(parsed)
            res = s.check()
            m = s.model() if res == z3.sat else None
            return {"method": "python_z3", "status": str(res), "model": str(m) if m else None, "assertions": len(s.assertions())}
        except Exception as e:
            return {"method": "python_z3", "error": f"parse/solve failed: {e}"}

    def _incremental_validate_with_diagnosis(self, facts_list: List[str], template_text: str) -> Dict[str, Any]:
        """
        增量验证：逐个断言验证，定位具体冲突
        返回详细的诊断信息
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
            # ✅ 修复：正确使用 push/pop
            # solver.push()  # 保存初始状态
            # 逐个添加 facts，找到导致 unsat 的断言
            conflicting_facts = []
            added_facts = []  # 记录已添加的事实
            for i, fact_str in enumerate(facts_list):
                try:
                    # ✅ 构造完整上下文：模板 + 声明 + 断言
                    full_script = template_text + "\n\n"
                    if self.smt_decls:
                        full_script += "\n".join(self.smt_decls) + "\n\n"
                    full_script += fact_str

                    # 解析整个脚本（Z3 会忽略重复的声明）
                    all_assertions = z3.parse_smt2_string(full_script)

                    # 计算新断言的数量（总数 - 模板中的断言数）
                    # 模板断言数已知（context_assertions）
                    template_assertion_count = len(context_assertions)
                    new_assertions = list(all_assertions)[template_assertion_count:]

                    if not new_assertions:
                        continue

                    # 只添加新断言
                    solver.push()
                    for fa in new_assertions:
                        solver.add(fa)

                    result = solver.check()
                    if result == z3.unsat:
                        # ✅ 取出对应的元信息
                        meta = self.fact_metadata[i] if i < len(self.fact_metadata) else {}
                        conflict = {
                            "index": i,
                            "fact": fact_str.strip(),
                            "message": f"第 {i + 1} 个断言导致约束冲突",
                            "context": added_facts[-3:] if len(added_facts) >= 3 else added_facts[:]
                        }
                        # ✅ 合并元信息（constraint_id 等）
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

    def validate_cross_file_constraints(self, arxml_files: List[str]) -> Dict[str, Any]:
        """
        执行跨文件SMT约束验证

        Args:
            arxml_files: ARXML文件路径列表

        Returns:
            验证结果字典
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

        # 生成跨文件SMT事实
        fact_count = self._generate_global_smt_facts()

        result["stats"]["fact_count"] = fact_count
        result["stats"]["skipped_count"] = len(self.skipped_predicates)
        result["skipped_predicates"] = self.skipped_predicates

        if fact_count == 0:
            print("[INFO] 跨文件验证: 未生成任何SMT事实")
            result["stats"]["reason"] = "No cross-file SMT facts generated"
            return result

        # 组合SMT脚本
        decls_text = "\n".join(self.smt_decls)
        facts_text = "\n".join(self.smt_facts)

        smt_parts = []
        if self.smt_template_text:
            smt_parts.append(self.smt_template_text.rstrip())
        smt_parts.append("\n; --- CROSS-FILE DECLS ---")
        if decls_text:
            smt_parts.append(decls_text)
        smt_parts.append("\n; --- CROSS-FILE FACTS ---")
        if facts_text:
            smt_parts.append(facts_text)
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
            elif "error" in solver_result:
                result["valid"] = False
                result["violations"].append({
                    "type": "SMT_SOLVER_ERROR",
                    "message": solver_result.get("error", "Unknown error")
                })

        result["solver"] = solver_result
        result["smt"] = full_smt

        return result

    def _validate_smt_constraints(self) -> List[Dict]:
        """执行SMT模板中定义的跨文件约束"""
        violations = []

        if not self.cross_file_resolver:
            return violations

        # 过滤出跨文件约束
        cross_file_mappings = [m for m in self.mapping if m.get('cross_file', False)]

        if not cross_file_mappings:
            print("[INFO] 未找到跨文件约束映射")
            return violations

        print(f"[INFO] 检查 {len(cross_file_mappings)} 个跨文件约束...")

        for mapping in cross_file_mappings:
            constraint_id = mapping.get('constraint_id', 'unknown')
            severity = mapping.get('severity', 'Violation')

            try:
                result = self._check_single_cross_file_constraint(mapping)
                if not result['satisfied']:
                    for detail in result.get('details', []):
                        violations.append({
                            'type': 'SMT_CROSS_FILE_VIOLATION',
                            'constraint_id': constraint_id,
                            'severity': severity,
                            'detail': detail,
                            'message': f"跨文件约束 {constraint_id} 不满足: {detail.get('reason', 'unknown')}"
                        })
            except Exception as e:
                print(f"[WARN] 约束 {constraint_id} 验证失败: {e}")
                violations.append({
                    'type': 'SMT_CONSTRAINT_ERROR',
                    'constraint_id': constraint_id,
                    'severity': 'Warning',
                    'error': str(e),
                    'message': f"约束 {constraint_id} 验证出错"
                })

        return violations

    def _check_single_cross_file_constraint(self, mapping: Dict) -> Dict:
        result = {'satisfied': True, 'details': []}

        target = mapping.get('target', {})
        target_sort = target.get('target_sort', '')
        target_xml_tag = target.get('target_xml', {}).get('xml_tag', '')

        # 🔧 修复：使用抽象类到具体类的映射
        concrete_tags = self._get_concrete_tags(target_xml_tag)

        # 获取所有目标类型的元素
        target_elements = []
        for tag in concrete_tags:
            elements = self.cross_file_resolver.get_elements_by_type(tag)
            if elements:
                target_elements.extend(elements)

        if not target_elements:
            return result

        properties = mapping.get('properties', [])
        ref_properties = [p for p in properties if p.get('is_cross_file_ref', False)]

        # 检查引用属性的约束
        for prop in ref_properties:
            xml_tag = prop.get('xml_tag', '')
            dest_attr = prop.get('dest_attr', 'DEST')
            resolution_strategy = prop.get('resolution_strategy', 'short-name-path')

            # 获取所有该类型的引用
            if xml_tag in self.cross_file_resolver.ref_registry:
                refs = self.cross_file_resolver.ref_registry[xml_tag]

                for ref in refs:
                    ref_path = ref.get('text', '')
                    if ref_path:
                        # 检查引用是否解析成功
                        resolved = self.cross_file_resolver.resolve_reference(ref_path)
                        if not resolved:
                            result['satisfied'] = False
                            result['details'].append({
                                'property': prop.get('role', xml_tag),
                                'ref_path': ref_path,
                                'source_file': ref.get('source_file', ''),
                                'reason': f'引用 {ref_path} 无法解析'
                            })
                        else:
                            # 检查类型匹配
                            expected_dest = ref.get('dest', '')
                            actual_type = resolved.get('tag', '')
                            if expected_dest and actual_type != expected_dest:
                                result['satisfied'] = False
                                result['details'].append({
                                    'property': prop.get('role', xml_tag),
                                    'ref_path': ref_path,
                                    'expected_type': expected_dest,
                                    'actual_type': actual_type,
                                    'reason': f'类型不匹配: 期望 {expected_dest}, 实际 {actual_type}'
                                })

        # 检查互斥/依赖约束
        logical_pattern = mapping.get('logical_pattern', {})
        if logical_pattern.get('type') == 'mutual_exclusion':
            # 互斥约束检查
            exclusion_result = self._check_mutual_exclusion(mapping, target_elements)
            if not exclusion_result['satisfied']:
                result['satisfied'] = False
                result['details'].extend(exclusion_result['details'])

        return result

    def _check_mutual_exclusion(self, mapping: Dict, target_elements: List[Dict]) -> Dict:
        """检查互斥约束"""
        result = {'satisfied': True, 'details': []}

        properties = mapping.get('properties', [])
        if len(properties) < 2:
            return result

        # 简化实现：检查是否存在同时具有互斥属性的元素
        prop_names = [p.get('xml_tag', '') for p in properties]

        for elem in target_elements:
            elem_path = elem.get('path', '')
            source_file = elem.get('source_file', '')

            # 🔧 如果没有 children_tags，回溯源文件获取
            children = elem.get('children_tags', None)
            if children is None:
                children = self._get_children_tags(source_file, elem_path)

            # 统计该元素具有哪些互斥属性
            present_props = [pn for pn in prop_names if pn in children]

            if len(present_props) > 1:
                result['satisfied'] = False
                result['details'].append({
                    'element_path': elem_path,
                    'conflicting_properties': present_props,
                    'reason': f'互斥属性同时存在: {", ".join(present_props)}'
                })

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

    # 在类的末尾添加诊断方法

    def get_template_predicate_summary(self) -> Dict[str, Any]:
        """
        获取模板中谓词的摘要信息，用于诊断
        """
        summary = {
            "total_sorts": len(self.template_sorts),
            "sorts": list(self.template_sorts),
            "total_predicates": len(self.predicate_signatures),
            "predicates": {},
            "base_name_groups": {}
        }

        # 按基础名分组
        for base_name, variants in self.predicate_base_to_variants.items():
            summary["base_name_groups"][base_name] = [
                {
                    "actual_name": v[0],
                    "arity": len(v[1]),
                    "arg_types": v[1],
                    "return_type": v[2],
                    "suffix_number": v[3]
                }
                for v in variants
            ]

        # 所有谓词签名
        for pred_name, (arg_types, ret_type) in self.predicate_signatures.items():
            summary["predicates"][pred_name] = {
                "arity": len(arg_types),
                "arg_types": arg_types,
                "return_type": ret_type
            }

        return summary

    def validate_mapping_predicates(self) -> Dict[str, Any]:
        """
        验证mapping中的所有谓词是否能在模板中找到匹配
        在实际验证前调用，用于诊断配置问题
        """
        report = {
            "all_matched": True,
            "matched": [],
            "unmatched": [],
            "warnings": []
        }

        for entry in self.mapping:
            cid = entry.get("constraint_id", "unknown")

            for prop in entry.get("properties", []):
                role = prop.get("role", "unknown")
                smt_preds = prop.get("smt_predicates", {})

                for pred_name, pred_info in smt_preds.items():
                    if isinstance(pred_info, dict):
                        expected_arity = len(pred_info.get("args", []))
                    else:
                        expected_arity = 1

                    matched = self._match_predicate_in_template(pred_name, expected_arity)

                    if matched:
                        match_info = {
                            "constraint_id": cid,
                            "property_role": role,
                            "mapping_predicate": pred_name,
                            "matched_predicate": matched,
                            "is_renamed": matched != pred_name
                        }
                        report["matched"].append(match_info)

                        if matched != pred_name:
                            report["warnings"].append(
                                f"谓词重命名: '{pred_name}' → '{matched}' (约束: {cid})"
                            )
                    else:
                        report["all_matched"] = False
                        report["unmatched"].append({
                            "constraint_id": cid,
                            "property_role": role,
                            "mapping_predicate": pred_name,
                            "expected_arity": expected_arity
                        })

        return report

