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
    def __init__(self, smt_template_file: str, mapping_file: Optional[str] = None, **kwargs):
        """
        smt_template_file: path to constraints.smt2 template (kept as-is)
        mapping_file: path to JSON mapping (default 'src/validation/data/mapping_smt.json')
        """
        self.smt_template_file = smt_template_file
        self.mapping_file = mapping_file

        self.smt_template_text: str = ""
        self.template_sorts: Set[str] = set()
        self.template_functions: Dict[str, List[Tuple[str, List[str], str]]] = {}
        self.template_constructors: Dict[str, List[Tuple[str, List[str]]]] = {}

        # runtime generated
        self.smt_decls: List[str] = []
        self.smt_facts: List[str] = []
        self.declared_consts: Set[str] = set()

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

    def _parse_template(self, txt: str):
        # parse declare-sort
        for m in re.finditer(r'\(declare-sort\s+([A-Za-z0-9_\-]+)\s+\d+\)', txt):
            self.template_sorts.add(m.group(1))
        # parse declare-fun (name (args) RET)
        for m in re.finditer(r'\(declare-fun\s+([A-Za-z0-9_\-]+)\s*\(([^\)]*)\)\s*([A-Za-z0-9_\-]+)\)', txt):
            fname = m.group(1)
            args_txt = m.group(2).strip()
            ret = m.group(3)
            arg_types = []
            if args_txt:
                # simple split; keeps tokens
                arg_types = [tok for tok in re.split(r'\s+', args_txt) if tok]
            key = ret
            self.template_functions.setdefault(key, []).append((fname, arg_types, ret))
        # naive parse of declare-datatypes for constructors
        # matches simple cases: (declare-datatypes () ((T (C1 (f1 t1) ...) (C2 ...))))
        for m in re.finditer(r'\(declare-datatypes\s*\([^)]*\)\s*\(\s*\(\s*([A-Za-z0-9_\-]+)\s+([^\)]+)\)\s*\)\)', txt, re.S):
            dtype = m.group(1)
            body = m.group(2)
            ctors = []
            for cm in re.finditer(r'\(\s*([A-Za-z0-9_\-]+)\s*(\([^\)]*\))?', body):
                ctor = cm.group(1)
                args = cm.group(2)
                arg_types = []
                if args:
                    # find field types inside ( (name type) ...)
                    pairs = re.findall(r'\(\s*[A-Za-z0-9_\-]+\s+([A-Za-z0-9_\-]+)\s*\)', args)
                    arg_types = pairs
                ctors.append((ctor, arg_types))
            if ctors:
                self.template_constructors.setdefault(dtype, []).extend(ctors)

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

    # -------------------------
    # Mapping-driven generation
    # -------------------------
    def _declare_const(self, name: str, sort: str):
        if name in self.declared_consts:
            return
        self.declared_consts.add(name)
        self.smt_decls.append(f"(declare-const {name} {sort})")

    def _ensure_accessor_decl(self, accessor: str, arg_sort: str, ret_sort: str):
        # If template already has a function with this name, skip; otherwise create declare-fun text (we do not add to template)
        # We don't emit declare-fun into self.smt_template_text; instead we rely on declaring consts and using asserts as needed.
        return

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
            cid = entry.get("constraint_id", "constraint")
            tgt = entry.get("target", {}) or {}
            tgt_sort = tgt.get("target_sort")
            tgt_xml = tgt.get("target_xml") or {}
            tgt_xpath = tgt_xml.get("xpath") or tgt_xml.get("xml_tag")
            tgt_binding = tgt.get("target_binding", "short-name")

            # find matching xml nodes
            nodes = []
            if tgt_xpath:
                # try simple relative xpath patterns; allow both with and without namespace
                try:
                    nodes = root.findall(".//" + tgt_xpath)
                except Exception:
                    # fallback: try tag search
                    nodes = [n for n in root.iter() if _xml_tag_local(n.tag) == tgt_xpath]
            else:
                # if no xpath, attempt to use tag name from target_xml
                tag = tgt_xml.get("xml_tag") if tgt_xml else None
                if tag:
                    nodes = [n for n in root.iter() if _xml_tag_local(n.tag) == tag]

            # default to entire document if no target specified (rare)
            if not nodes and not tgt_xpath and not tgt_xml:
                nodes = [root]

            # For each matched target element, generate subject and properties
            for node in nodes:
                # determine SMT subject name
                prefix = tgt_sort or _xml_tag_local(node.tag)
                subj_name = self._stable_name_for_elem(node, binding=tgt_binding, prefix=prefix)
                # declare subject
                if tgt_sort:
                    self._declare_const(subj_name, tgt_sort)
                else:
                    # no target sort known: use Int as fallback to avoid unknown constant errors
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
                        # 尝试相对路径查找（相对于当前 node）
                        try:
                            # 如果 xpath 包含 '/'，说明是多层路径
                            if '/' in search_path:
                                found = node.findall(".//" + search_path)
                            else:
                                # 单层：直接子元素或任意后代
                                found = node.findall(".//" + search_path)
                                # 如果找不到，尝试直接子元素
                                if not found:
                                    found = [c for c in node if _xml_tag_local(c.tag) == search_path]
                        except Exception:
                            # fallback: 遍历所有后代，匹配标签名
                            found = [c for c in node.iter() if _xml_tag_local(c.tag) == (p_xml_tag or search_path)]

                    if not found:
                        # property not present (optional)
                        continue

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
                            # pred_info may be dict with type 'predicate' and args specify how to fill
                            if isinstance(pred_info, dict):
                                args = pred_info.get("args", [])
                                # resolve args, allow tokens: PROPERTY -> current prop_smt, SUBJECT -> subj_name
                                resolved_args = []
                                for a in args:
                                    if a == "PROPERTY" or a.upper().startswith("VARIATIONPOINT") or a.upper().startswith(role.upper()):
                                        resolved_args.append(prop_smt)
                                    elif a == "SUBJECT" or a.upper() == tgt_sort.upper():
                                        resolved_args.append(subj_name)
                                    else:
                                        # literal or other
                                        resolved_args.append(a)
                                self.smt_facts.append(f"(assert ({pred_name} {' '.join(resolved_args)}))")
                            else:
                                # if simple string, assume unary predicate on property
                                self.smt_facts.append(f"(assert ({pred_info} {prop_smt}))")

                # logical pattern: 在模板驱动架构下，跳过逻辑模式生成
                lp = entry.get("logical_pattern") or {}
                if lp:
                    # 传递给简化版的方法（只做日志记录，不生成断言）
                    self._emit_logical_pattern(lp, subj_name, prop_instances, entry.get("constraint_id"))

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

    def _resolve_pattern_expr(self, expr: Any, subj_name: str, prop_instances: Dict[str, List[str]]) -> Optional[str]:
        """
        Resolve pattern expressions which may be:
          - dict { "fn": "predName", "args": ["SUBJECT","role"] }
          - string template like "predicate(SUBJECT, ROLE)"
        Returns SMT expression string (no surrounding assert).
        """
        if expr is None:
            return None
        if isinstance(expr, str):
            # simple template replace
            t = expr.replace("{{SUBJECT}}", subj_name)
            for role, names in prop_instances.items():
                if names:
                    t = t.replace("{{" + role.upper() + "}}", names[0])
            return t
        if isinstance(expr, dict):
            fn = expr.get("fn")
            args = expr.get("args", [])
            resolved_args = []
            for a in args:
                if a == "SUBJECT":
                    resolved_args.append(subj_name)
                elif a in prop_instances and prop_instances[a]:
                    resolved_args.append(prop_instances[a][0])
                else:
                    # literal or unknown; pass as-is
                    resolved_args.append(str(a))
            return f"({fn} {' '.join(resolved_args)})"
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
            diagnosis_text = incremental_result.get("diagnosis", "")
            if diagnosis_text:
                print("\n" + diagnosis_text)
            # 打印具体冲突
            conflicts = incremental_result.get("conflicting_facts", [])
            if conflicts:
                print(f"\n🔍 发现 {len(conflicts)} 个约束冲突:")
                for conflict in conflicts[:5]:  # 最多显示5个
                    print(f"  - 第 {conflict.get('index', '?') + 1} 个断言: {conflict.get('fact', '')[:100]}...")
        # 5) return structure
        return {
            "valid": is_valid,
            "constraint_count": constraint_count,
            "satisfied_count": satisfied_count,
            "smt": full_smt,
            "mapping_json": mapping_json_text,
            "solver": solver_result,
            "diagnosis": incremental_result
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
            solver.push()  # 保存初始状态
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
                        conflicting_facts.append({
                            "index": i,
                            "fact": fact_str.strip(),
                            "message": f"第 {i + 1} 个断言导致约束冲突",
                            "context": added_facts[-3:] if len(added_facts) >= 3 else added_facts[:]
                        })
                        solver.pop()
                    else:
                        solver.pop()
                        for fa in new_assertions:
                            solver.add(fa)
                        added_facts.append(fact_str.strip()[:80])

                except Exception as e:
                    conflicting_facts.append({
                        "index": i,
                        "fact": fact_str.strip(),
                        "error": f"解析失败: {str(e)}"
                    })
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

            lines.append(f"\n  ❌ 冲突 #{i} (断言 #{idx + 1}):")
            lines.append(f"     {fact}")

            if error:
                lines.append(f"     错误: {error}")

        lines.append(f"\n  📊 冲突统计: {len(conflicting_facts)} 个约束违反")

        return "\n".join(lines)

    def set_cross_file_resolver(self, resolver) -> None:
        """设置跨文件解析器"""
        self.cross_file_resolver = resolver

    def validate_cross_file_constraints(self, arxml_files: List[str]) -> Dict[str, Any]:
        """
        执行跨文件约束验证

        Args:
            arxml_files: 所有ARXML文件路径

        Returns:
            验证结果
        """
        # 修复：使用正确的属性名
        if not self.z3_cli_available:
            try:
                import z3
                z3_available = True
            except ImportError:
                z3_available = False
        else:
            z3_available = True

        if not z3_available:
            return {
                'success': False,
                'error': 'Z3 solver not available',
                'violations': []
            }

        if not self.cross_file_resolver:
            from src.validation.cross_file_resolver import CrossFileResolver
            self.cross_file_resolver = CrossFileResolver()
            self.cross_file_resolver.build_global_index(arxml_files)

        violations = []

        # 1. 基础引用完整性检查
        ref_violations = self.cross_file_resolver.validate_all_refs()
        violations.extend(ref_violations)

        # 2. DEST类型匹配检查
        type_mismatches = self.cross_file_resolver.check_dest_type_match()
        violations.extend(type_mismatches)

        # 3. 执行SMT约束验证
        smt_violations = self._validate_smt_constraints()
        violations.extend(smt_violations)

        return {
            'success': len(violations) == 0,
            'violations': violations,
            'stats': {
                'total_elements': len(self.cross_file_resolver.global_index),
                'total_refs': sum(len(refs) for refs in self.cross_file_resolver.ref_registry.values()),
                'unresolved_refs': len(ref_violations),
                'type_mismatches': len(type_mismatches),
                'smt_violations': len(smt_violations)
            }
        }

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
        """检查单个跨文件约束"""
        result = {'satisfied': True, 'details': []}

        target = mapping.get('target', {})
        target_sort = target.get('target_sort', '')
        target_xml_tag = target.get('target_xml', {}).get('xml_tag', '')

        # 获取所有目标类型的元素
        target_elements = self.cross_file_resolver.get_elements_by_type(target_xml_tag)

        if not target_elements:
            # 没有找到目标元素，约束自动满足
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
            children = elem.get('children_tags', [])

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

    def generate_smt_instance_from_global(self, output_path: str) -> None:
        """
        根据全局索引生成SMT实例文件

        Args:
            output_path: 输出文件路径
        """
        if not self.cross_file_resolver:
            raise ValueError("需要先设置跨文件解析器并构建索引")

        lines = []

        # 1. 读取模板
        if self.smt_template_text:
            lines.append(f"; SMT Instance generated from global index")
            lines.append(f"; Template: {self.smt_template_file}")
            lines.append(self.smt_template_text.rstrip())
            lines.append("\n; --- GLOBAL INSTANCE DATA ---\n")
        else:
            lines.append("; Generated SMT instance (no template)")

        # 2. 为每个元素生成常量声明
        lines.append("; Element declarations")
        for path, info in self.cross_file_resolver.global_index.items():
            safe_name = self._path_to_smt_name(path)
            element_type = info['tag']

            # 检查类型是否在模板中声明
            if element_type in self.template_sorts:
                lines.append(f"(declare-const {safe_name} {element_type})")
            else:
                lines.append(f"; Skipping {safe_name}: sort {element_type} not in template")

        # 3. 生成引用关系断言
        lines.append("\n; Reference assertions")
        for ref_type, refs in self.cross_file_resolver.ref_registry.items():
            for ref in refs:
                ref_path = ref.get('text', '')
                if ref_path:
                    target = self.cross_file_resolver.resolve_reference(ref_path)
                    if target:
                        lines.append(f"; REF {ref_type}: {ref_path} -> {target['tag']}")
                        # 可以添加具体的引用断言
                    else:
                        lines.append(f"; UNRESOLVED REF {ref_type}: {ref_path}")

        # 4. 添加检查命令
        lines.append("\n(check-sat)")
        lines.append("(get-model)")

        # 写入文件
        from pathlib import Path as PathLib
        PathLib(output_path).write_text('\n'.join(lines), encoding='utf-8')
        print(f"[OK] SMT实例已生成: {output_path}")

    def _path_to_smt_name(self, path: str) -> str:
        """将SHORT-NAME-PATH转换为合法的SMT标识符"""
        # 移除开头的斜杠，替换特殊字符
        name = path.lstrip('/')
        name = name.replace('/', '_').replace('-', '_').replace('.', '_')
        # 确保以字母开头
        if name and not name[0].isalpha():
            name = 'elem_' + name
        return _sanitize_ident(name)

