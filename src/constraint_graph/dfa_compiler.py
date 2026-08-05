"""dfa_compiler.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Compile a GBNF grammar into a *prefix-closed* DFA and emit:

  • <name>.fsm               –  JSON  (FSM v2, possibly compressed)
  • autosar_allowed_tokens.py –  runtime helper for vLLM

Key features
------------
1)  Depth-limited subset-construction  (default MAX_DEPTH = 15)
2)  Hopcroft minimisation               –  |Q|min
3)  Path-compression (linear chains)    –  further shrinks |Q|
4)  Optional *on-demand* runtime: states that are not stored in the FSM
    are reconstructed lazily with an embedded Lark parser and cached
"""
from __future__ import annotations

import argparse
import functools
import json
import pathlib
import textwrap
from collections import defaultdict, deque
from typing import Dict, List, Set, Tuple

from lark import Lark

from cfg import BUILD_CFG
from utils import normalize

MAX_DEPTH              = BUILD_CFG.get("limits", {}).get("max_depth", 10)
CHAIN_COMPRESS_THRESHOLD = BUILD_CFG.get("limits", {}).get("compress_threshold", 1)
LRU_CACHE_SIZE         = BUILD_CFG.get("limits", {}).get("lru_cache", 10_000)
PROGRESS_STEP = BUILD_CFG.get("limits", {}).get("progress_step", 1000)


# ── DFA helpers ──────────────────────────────────────────────────────────────
State = str                          # use concatenated token string as key
EdgeTable = Dict[State, Dict[str, State]]


def _build_prefix_dfa(parser: Lark, all_terms: List[str], *, progress: bool = False, roots: set[str] | None = None,) -> Tuple[EdgeTable, Set[State]]:
    """
    BFS over token prefixes until MAX_DEPTH, asking Lark for follow-set.
    Returns:
        transitions :  state  -> {token -> next_state}
        accepting   :  set(state)
    """
    transitions: EdgeTable = {}
    accepting: Set[State] = set()

    start: State = ""
    q: deque[Tuple[State, List[str]]] = deque([(start, [])])
    processed = 0

    while q:
        state, toks = q.popleft()
        if len(toks) >= MAX_DEPTH:
            continue

        # follow-set
        next_terms = _follow_set(parser, tuple(toks))

        allowed_all = [_sym_name(t) for t in next_terms]
        # 如果在起始状态且给定 roots → 过滤
        if not toks and roots is not None:
            allowed = [a for a in allowed_all if normalize(a) in roots]
        else:
            allowed = allowed_all
        if not allowed:
            accepting.add(state)
            continue

        transitions[state] = {}
        for t in allowed:
            nxt_toks = toks + [t]
            nxt = " ".join(nxt_toks)
            transitions[state][t] = nxt
            # 仅在还 **没触顶** 时才继续 BFS，避免产生悬空节点

            if len(nxt_toks) < MAX_DEPTH and nxt not in transitions:
                q.append((nxt, nxt_toks))

        processed += 1
        if progress and processed % PROGRESS_STEP == 0:
            print(f"   … {processed:,} states explored (queue={len(q):,})")

    # ── Post-pass：补全深度触顶但被引用的叶节点 ───────────────────
    # 这样 Hopcroft/压缩阶段就永远不会遇到“悬空目标状态”

    for edges in list(transitions.values()):
        for nxt in edges.values():
            if nxt not in transitions:
                transitions[nxt] = {}  # dead-end
                accepting.add(nxt)  # 视作可终态

    return transitions, accepting


def _hopcroft_minimise(trans: EdgeTable, accepting: Set[State]) -> Tuple[EdgeTable, Set[State]]:
    """
    Classic Hopcroft partition-refinement algorithm.
    Returns a *new* transitions dict whose keys are representative states.
    """
    # Make sure every target state exists in `trans`
    for edges in list(trans.values()):
        for s2 in edges.values():
            trans.setdefault(s2, {})

    # Build Σ
    sigma: Set[str] = {tok for edges in trans.values() for tok in edges}

    # P  – partition starting with {A, N}
    P: List[Set[State]] = [set(accepting), set(trans) - set(accepting)]
    W: deque[Set[State]] = deque(P)

    # reverse-edge map for fast predecessor lookup
    pred: Dict[str, Dict[State, Set[State]]] = {a: defaultdict(set) for a in sigma}
    for s, edges in trans.items():
        for a, s2 in edges.items():
            pred[a][s2].add(s)

    while W:
        A = W.popleft()
        for a in sigma:
            X = set().union(*(pred[a].get(q, set()) for q in A))
            for Y in P[:]:
                inter, diff = Y & X, Y - X
                if inter and diff:
                    P.remove(Y)
                    P.extend((inter, diff))
                    if Y in W:
                        W.remove(Y)
                        W.extend((inter, diff))
                    else:
                        W.append(inter if len(inter) <= len(diff) else diff)

    # representative mapping
    rep = {s: next(iter(part)) for part in P for s in part}

    new_trans: EdgeTable = defaultdict(dict)
    for s, edges in trans.items():
        r = rep[s]
        for a, s2 in edges.items():
            new_trans[r][a] = rep[s2]
    new_accept = {rep[s] for s in accepting}
    return dict(new_trans), new_accept


def _path_compress(trans: EdgeTable, accepting: Set[State]) -> Tuple[EdgeTable, Set[State]]:
    """
    Collapse chains (degree ≤1) into single super-edges by encoding the sequence.
    Stored as `"tok1|tok2|tok3"` to distinguish from normal token keys.
    """
    out: EdgeTable = {}
    skip: Set[State] = set()

    for s in list(trans.keys()):
        if s in skip:
            continue
        cur = s
        chain: List[str] = []
        # 1) collect a maximal linear chain (degree ≤1)
        while (
                cur not in accepting
                and len(trans[cur]) == 1
                and len(chain) < MAX_DEPTH  # ← 防止极端深链
        ):
            tok, nxt = next(iter(trans[cur].items()))
            if len(trans[nxt]) > 1 or nxt in accepting:
                break  # nxt 已分叉 → 停
            chain.append(tok)
            skip.add(cur)
            cur = nxt

        # 2) 写 super-edge / copy 终端节点所有边
        if chain:
            out.setdefault(s, {})["|".join(chain)] = cur
        if cur not in out:
            out[cur] = dict(trans[cur])  # 深拷贝防止后续修改

        # 3) 补遗漏
    for s, edges in trans.items():
        out.setdefault(s, {}).update(edges)
    return out, accepting


# ── Public API ───────────────────────────────────────────────────────────────
def compile_gbnf(
    gbnf_path: str | pathlib.Path,
    *,
    compress: bool = False,
    on_demand: bool = False,
    progress: bool = False,
    roots: list[str] | None = None,
    ) -> pathlib.Path:
    """
    Compile a GBNF file into a prefix-closed DFA (.fsm) and an
    `autosar_allowed_tokens.py` helper.

    Args:
        gbnf_path : Path to *.gbnf*
        compress  : Hopcroft + path compression
        on_demand : emit lazy runtime helper
        progress  : print BFS progress every PROGRESS_STEP states
        roots     : list of **original XML tags** to keep as DFA roots
                    (e.g. "APPLICATION-SW-COMPONENT-TYPE")
    """
    # ------------------------------------------------------------------ fix ↓
    roots_set: set[str] | None = None
    if roots:
        # keep exactly the same form produced by normalize(a) in _build_prefix_dfa
        #   "APPLICATION-SW-COMPONENT-TYPE" → "application_sw_component_type"
        roots_set = {normalize(r) for r in roots}

    """Main entry: build DFA, write .fsm & runtime helper; return .fsm Path."""
    gbnf_path = pathlib.Path(gbnf_path)
    grammar_raw = gbnf_path.read_text(encoding="utf-8")

    # ---- Step 0: GBNF ➜ Lark-compatible EBNF --------------------
    grammar = grammar_raw

    # 0.1 去掉分号注释
    grammar = "\n".join(
        ln for ln in grammar.splitlines() if not ln.lstrip().startswith(";")
    )
    import re
    # 0.2 去掉 C-style注释 /* … */
    grammar = re.sub(r"/\*.*?\*/", "", grammar, flags=re.S)

    # 0.3 把  <NAME>  ⇒  name   （全小写、无尖括）
    grammar = re.sub(r"<([A-Za-z0-9_]+)>", lambda m: m.group(1).lower(), grammar)

    # 0.4  把 “::=” 换成 “:”
    grammar = grammar.replace("::=", ":")
    # ---------- 0.5  补 start 规则 -----------------------------
    if not re.search(r"^\s*start\s*:", grammar, flags=re.M):
        # 取首个非终结符作为入口
        m = re.search(r"^\s*([a-zA-Z_][\w]*)\s*:", grammar, flags=re.M)
        if not m:
            raise ValueError("Cannot infer start rule from grammar")
        root = m.group(1)
        grammar = f"start: {root}\n\n" + grammar

    # Lark parse (fallback to regex if totally broken)
    try:
        parser = Lark(grammar, parser="lalr", maybe_placeholders=False)
        all_terms = sorted(_sym_name(t) for t in parser.terminals)
    except Exception as exc:  # pragma: no cover
        import re, warnings

        warnings.warn(f"Lark failed – stub DFA ({exc})", RuntimeWarning)
        all_terms = sorted(set(re.findall(r'"([^"]+)"', grammar)))
        parser = None

    # ε-state only?
    if not all_terms or parser is None:
        dfa = {"": all_terms}
        accepting: Set[State] = set()
    else:
        trans, accepting = _build_prefix_dfa(
                parser,
                all_terms,
                progress = progress,
                roots=roots_set,
        )
        if compress:
            trans, accepting = _hopcroft_minimise(trans, accepting)
            trans, accepting = _path_compress(trans, accepting)
        dfa = trans

    # ── write FSM (JSON) ──────────────────────────────────────────────────
    fsm_obj = {
        "version": 2,
        "compressed": compress,
        "states": list(dfa.keys()),
        "edges": dfa,
        "accept": list(accepting),
    }
    out_fsm = gbnf_path.with_suffix(".fsm")
    out_fsm.write_text(json.dumps(fsm_obj, ensure_ascii=False))

    # ── write runtime helper ──────────────────────────────────────────────
    stub_path = gbnf_path.with_name("autosar_allowed_tokens.py")
    stub_code = _render_runtime_stub(
        fsm_name=out_fsm.name,
        compress=compress,
        on_demand=on_demand,
        root_edges={k: v for k, v in dfa.items() if k.count(" ") < 3},  # ≤3-layer
        grammar=grammar if on_demand else "",
    )
    stub_path.write_text(stub_code, encoding="utf-8")
    return out_fsm


# ── helper for runtime stub generation ───────────────────────────────────────
def _render_runtime_stub(
    *,
    fsm_name: str,
    compress: bool,
    on_demand: bool,
    root_edges: Dict[str, Dict[str, str]],  # 改回原来的类型
    grammar: str,
    ) -> str:
    root_json = json.dumps(root_edges, ensure_ascii=False, indent=2)
    lru_size = LRU_CACHE_SIZE
    return textwrap.dedent(
        f'''\
        """autosar_allowed_tokens – AUTO-GENERATED
        ------------------------------------------------
        • FSM file : {fsm_name}
        • Compress : {compress}
        • On-demand: {on_demand}
        """
        from __future__ import annotations
        import json
        import pathlib
        from typing import List, Optional

        # 加载完整的 FSM
        _FSM_PATH = pathlib.Path(__file__).parent / "{fsm_name}"
        with _FSM_PATH.open(encoding="utf-8") as f:
            _FSM_DATA = json.load(f)

        _TRANSITIONS = _FSM_DATA["edges"]
        _ACCEPTING = set(_FSM_DATA["accept"])

        def allowed(prefix_tokens: List[str]) -> Optional[List[str]]:
            """
            Args:
                prefix_tokens: 已生成的 token 序列
            Returns:
                允许的下一个 token 列表，或 None 表示不限制
            """
            state = " ".join(prefix_tokens)
            if state in _TRANSITIONS:
                return list(_TRANSITIONS[state].keys())
            return None

        # vLLM 兼容接口
        def allowed_token_ids(prefix_ids, tokenizer) -> Optional[List[int]]:
            """vLLM 兼容的接口"""
            if not prefix_ids or not tokenizer:
                return None

            # 将 token IDs 转换为文本
            prefix_text = tokenizer.decode(prefix_ids, skip_special_tokens=True).strip()
            tokens = prefix_text.split() if prefix_text else []

            # 获取允许的 tokens
            allowed_tokens = allowed(tokens)
            if allowed_tokens is None:
                return None

            # 转换为 token IDs
            token_ids = []
            for token in allowed_tokens:
                try:
                    ids = tokenizer.encode(token, add_special_tokens=False)
                    if ids:
                        token_ids.append(ids[0])
                except:
                    continue

            return token_ids if token_ids else None
        '''
    )


# ── CLI entry (optional tooling) ─────────────────────────────────────────────
def _cli() -> None:  # pragma: no cover
    p = argparse.ArgumentParser("compile GBNF → DFA")
    p.add_argument("gbnf")
    p.add_argument("--compress", action="store_true", help="Hopcroft + path compression")
    p.add_argument("--on-demand", action="store_true", help="emit lazy runtime helper")
    ns = p.parse_args()
    compile_gbnf(ns.gbnf, compress=ns.compress, on_demand=ns.on_demand)


if __name__ == "__main__":  # pragma: no cover
    _cli()

# -------- helper: make token/terminal name robust -----------
def _sym_name(sym) -> str:
    """Return the textual name of a terminal, whatever Lark gives us."""
    return sym.name if hasattr(sym, "name") else str(sym)

# --- 优化 _build_prefix_dfa() ------------------------------------------------
# 缓存 follow-set：同一前缀别反复调 Lark
@functools.lru_cache(maxsize=50_000)
def _follow_set(parser: Lark, toks: Tuple[str, ...]) -> List[str]:
    return [_sym_name(t) for t in parser.parse_interactive(" ".join(toks)).accepts()]


def compile_raw(
        raw_dir: str | pathlib.Path,
        *,
        roots: list[str],
        compress: bool = False,
        on_demand: bool = False,
        progress: bool = False,
) -> pathlib.Path:
    import collections, json, pathlib, utils, re

    raw_dir = pathlib.Path(raw_dir)
    c_path, a_path = raw_dir / "raw_classes.jsonl", raw_dir / "raw_attributes.jsonl"
    if not (c_path.is_file() and a_path.is_file()):
        raise FileNotFoundError("raw_dir 必须包含 raw_classes.jsonl 与 raw_attributes.jsonl")

    # 从配置文件读取限制
    MAX_STATES = BUILD_CFG.get("limits", {}).get("max_states", 50_000)
    MAX_QUEUE = BUILD_CFG.get("limits", {}).get("max_queue", 10_000)
    MAX_ENUM = BUILD_CFG.get("limits", {}).get("max_enum", 64)
    PROGRESS_STEP = BUILD_CFG.get("limits", {}).get("progress_step", 1000)

    # --- ① 预索引 -------------------------------------------------------
    tag2cid, id2tag = {}, {}
    cid2classname = {}
    children: dict[int, list[dict]] = collections.defaultdict(list)

    # **新增：上下文相关映射**
    contextual_tag2cid = {}  # "parent_cid:xml_tag" -> child_cid

    # 全局标签映射（无上下文冲突的）
    global_tag2cid = {}

    # ----- classes -------------------------------------------------------
    with c_path.open(encoding="utf-8") as fp:
        for ln in fp:
            if not ln.strip():
                continue
            row = json.loads(ln)
            cid = row["classId"]

            # 记录类名
            class_name = row.get("className", f"class_{cid}")
            cid2classname[cid] = class_name

            xml_tag = row.get("xml_tag")
            if xml_tag:
                norm_tag = utils.normalize(xml_tag)
                global_tag2cid[norm_tag] = cid
                id2tag[cid] = norm_tag

    # ----- 枚举映射 -------------------------------------------------------
    enum_map = {}
    enum_path = raw_dir / "raw_enums.jsonl"
    if enum_path.exists():
        with enum_path.open(encoding="utf-8") as fp:
            for ln in fp:
                if not ln.strip():
                    continue
                row = json.loads(ln)
                enum_id = row.get("enumId") or row.get("enum_id")
                values = row.get("values", [])
                if enum_id and values and len(values) <= MAX_ENUM:
                    try:
                        enum_map[int(enum_id)] = values
                    except (TypeError, ValueError):
                        continue

    # ----- attributes（构建上下文相关映射和children关系）-------------------------------------------------------
    if progress:
        print("🔍 构建上下文相关映射和children关系...")

    with a_path.open(encoding="utf-8") as fp:
        for ln in fp:
            if not ln.strip():
                continue
            row = json.loads(ln)
            pid = row["classId"]

            # -- 新逻辑：除 DEST 以外的属性继续跳过 -------------------
            is_dest_attr = bool(row.get("isXmlAttr")) and row["xml_tag"] == "DEST"
            if row.get("isXmlAttr", False) and not is_dest_attr:
                continue

            xml_tag = row.get("xml_tag")
            type_id = row.get("typeId")
            attribute_class = row.get("attributeClass", False)

            if not xml_tag or not type_id:
                continue

            norm_tag = utils.normalize(xml_tag)

            # **上下文相关映射**
            context_key = f"{pid}:{norm_tag}"
            contextual_tag2cid[context_key] = type_id

            # **检查全局映射冲突**
            if norm_tag in global_tag2cid:
                if global_tag2cid[norm_tag] != type_id:
                    if progress:
                        print(f"   上下文冲突：标签 '{norm_tag}' 在不同上下文中映射到不同类")
                        print(f"     全局: {global_tag2cid[norm_tag]}")
                        print(f"     上下文 {pid}: {type_id}")
            else:
                # 无冲突，可以作为全局映射
                global_tag2cid[norm_tag] = type_id
                if type_id not in id2tag:
                    id2tag[type_id] = norm_tag

            # **处理枚举值**
            allowed_values = row.get("allowedValues", [])
            if is_dest_attr and not allowed_values:
                # DEST 枚举来自 typeId → raw_enums
                allowed_values = enum_map.get(type_id, [])
            elif not is_dest_attr and not allowed_values and type_id in enum_map:
                # 普通文本节点可选值（用于 GBNF 约束）
                allowed_values = enum_map[type_id]

            child_info = {
                'child_cid': type_id,
                'xml_tag': norm_tag,
                'xml_wrapper_tag': utils.normalize(row.get("xml_wrapper_tag", "")) if row.get(
                    "xml_wrapper_tag") else None,
                'max_occurs': row.get("maxOccurs", 1),
                'min_occurs': row.get("minOccurs", 1),
                'attribute_class': attribute_class,
                'is_dest_attr': is_dest_attr,     # ← ★ 新增
                'allowed_values': allowed_values if allowed_values and 0 < len(allowed_values) <= MAX_ENUM else None
            }
            children[pid].append(child_info)

    # **构建最终的tag2cid映射表**
    tag2cid = global_tag2cid.copy()

    if progress:
        print(f"✓ 映射统计:")
        print(f"   全局tag映射: {len(global_tag2cid)}")
        print(f"   上下文映射: {len(contextual_tag2cid)}")

    # --- ② BFS 构建迁移表 ----------------------------------------------
    if not roots:
        raise ValueError("必须指定 roots 参数")

    start_tags = []
    for r in roots:
        norm_tag = utils.normalize(r)
        if norm_tag not in tag2cid:
            print(f"警告：根节点 '{r}' (normalized: '{norm_tag}') 不存在于 tag2cid 中")
            continue
        start_tags.append(norm_tag)

    if not start_tags:
        raise ValueError("没有有效的根节点")

    # 初始化状态机
    trans = {}
    accepting = set()
    q = collections.deque()
    visited = set()
    state_depth = {}

    # 添加空起始状态
    trans[""] = {tag: tag for tag in start_tags}
    accepting.add("")

    # 初始化队列
    for tag in start_tags:
        q.append((tag, 1))
        state_depth[tag] = 1

    processed = 0
    if progress:
        print(f"🔍 开始构建DFA，起始标签: {start_tags}")
        print(f"   MAX_DEPTH={MAX_DEPTH}, MAX_STATES={MAX_STATES}")

    def is_autosar_type_constraint(values: list[str]) -> bool:
        """判断枚举值是否为AUTOSAR类型约束"""
        if not values:
            return False
        # AUTOSAR类型名通常是大写+连字符的格式
        type_pattern = re.compile(r'^[A-Z][A-Z0-9-]*[A-Z0-9]$')
        return all(type_pattern.match(v) for v in values)

    def resolve_child_cid(parent_cid: int, child_tag: str) -> int:
        """解析子元素的类ID，优先使用上下文映射"""
        context_key = f"{parent_cid}:{child_tag}"
        if context_key in contextual_tag2cid:
            return contextual_tag2cid[context_key]
        return tag2cid.get(child_tag, -1)

    while q:
        # 安全检查
        if len(trans) > MAX_STATES:
            print(f"⚠️  状态数超过限制 {MAX_STATES:,}，停止扩展")
            break
        if len(q) > MAX_QUEUE:
            print(f"⚠️  队列过长 {len(q):,}，截断队列")
            q = collections.deque(sorted(q, key=lambda x: x[1])[:MAX_QUEUE // 2])

        state, depth = q.popleft()
        processed += 1

        if progress and processed % PROGRESS_STEP == 0:
            print(f"   … 已处理 {processed:,} 个状态，队列剩余 {len(q):,} 个，"
                  f"当前深度 {depth}，总状态数 {len(trans):,}")

        # 检查深度限制
        if depth > MAX_DEPTH:
            continue

        if state in visited:
            continue
        visited.add(state)

        # 获取当前状态对应的类
        parts = state.split() if state else []
        current_tag = parts[-1] if parts else ""

        if not current_tag or current_tag not in tag2cid:
            accepting.add(state)
            continue

        cid = tag2cid[current_tag]
        trans.setdefault(state, {})

        # 获取该类的所有子元素
        child_list = children.get(cid, [])
        if not child_list:
            accepting.add(state)
            continue

        state_has_children = False

        for child_info in child_list:
            wrapper = child_info['xml_wrapper_tag']
            child_tag = child_info['xml_tag']
            max_occurs = child_info['max_occurs']
            allowed_values = child_info.get('allowed_values')

            # **使用上下文相关映射解析子类ID**
            resolved_child_cid = resolve_child_cid(cid, child_tag)

            # 检查子元素是否可以继续展开
            can_expand = (
                    resolved_child_cid in children or
                    child_tag in tag2cid
            )

            if wrapper:
                # 有wrapper的情况
                wrapper_state = f"{state} {wrapper}" if state else wrapper

                if wrapper not in trans[state]:
                    trans[state][wrapper] = wrapper_state
                    state_depth[wrapper_state] = depth + 1
                    state_has_children = True

                trans.setdefault(wrapper_state, {})

                is_dest_attr = child_info.get('is_dest_attr', False)
                if allowed_values:
                    if is_dest_attr:                 # ← 只对 DEST 枚举建 edge
                        # **类型约束枚举：在FSM中处理**
                        for literal in allowed_values:
                            norm_type = utils.normalize(literal)
                            type_state = f"{wrapper_state} {norm_type}"
                            if norm_type not in trans[wrapper_state]:
                                trans[wrapper_state][norm_type] = type_state
                                state_depth[type_state] = depth + 2
                                # **关键修复：确保状态存在于trans中**
                                trans.setdefault(type_state, {})
                                accepting.add(type_state)

                                # 检查类型约束指向的类是否还能展开
                                type_cid = tag2cid.get(norm_type)
                                if type_cid and type_cid in children and depth + 2 < MAX_DEPTH:
                                    q.append((type_state, depth + 2))
                    else:
                        # 普通文本枚举：交给 GBNF，FSM 不扩展
                        accepting.add(wrapper_state)
                        continue
                else:
                    # 普通子元素
                    child_state = f"{wrapper_state} {child_tag}"
                    if child_tag not in trans[wrapper_state]:
                        trans[wrapper_state][child_tag] = child_state
                        state_depth[child_state] = depth + 2
                        trans.setdefault(child_state, {})

                        # 自环处理
                        if max_occurs != 1:
                            trans.setdefault(child_state, {})[child_tag] = child_state

                        # 继续展开条件
                        if can_expand and depth + 2 < MAX_DEPTH and child_state not in visited:
                            q.append((child_state, depth + 2))
            else:
                # 没有wrapper的直接连接
                is_dest_attr = child_info.get('is_dest_attr', False)
                if allowed_values:
                    if is_dest_attr:
                        # **类型约束枚举：在FSM中处理**
                        for literal  in allowed_values:
                            norm_type = utils.normalize(literal)
                            type_state = f"{state} {norm_type}" if state else norm_type
                            if norm_type not in trans[state]:
                                trans[state][norm_type] = type_state
                                state_depth[type_state] = depth + 1
                                # **关键修复：确保状态存在于trans中**
                                trans.setdefault(type_state, {})
                                accepting.add(type_state)
                                state_has_children = True

                                # 检查类型约束指向的类是否还能展开
                                type_cid = tag2cid.get(norm_type)
                                if type_cid and type_cid in children and depth + 1 < MAX_DEPTH:
                                    q.append((type_state, depth + 1))
                    else:
                        # **值约束枚举：交给GBNF处理**
                        accepting.add(state)
                        state_has_children = True
                        continue
                else:
                    # 普通子元素
                    child_state = f"{state} {child_tag}" if state else child_tag
                    if child_tag not in trans[state]:
                        trans[state][child_tag] = child_state
                        state_depth[child_state] = depth + 1
                        state_has_children = True
                        trans.setdefault(child_state, {})

                        # 自环处理
                        if max_occurs != 1:
                            trans.setdefault(child_state, {})[child_tag] = child_state

                        # 继续展开条件
                        if can_expand and depth + 1 < MAX_DEPTH and child_state not in visited:
                            q.append((child_state, depth + 1))

        # 如果状态有子元素，也将其标记为接受态（前缀闭包）
        if state_has_children:
            accepting.add(state)

    # 确保所有状态都是接受态
    accepting.update(trans.keys())

    if progress:
        print(f"✓ BFS完成: 共生成 {len(trans):,} 个状态")
        depth_dist = collections.Counter(state_depth.values())
        print(f"   深度分布: {dict(sorted(depth_dist.items()))}")

    # 验证修复效果
    if BUILD_CFG.get("debug", {}).get("enable_validation", False):
        print("🔍 验证状态一致性...")
        validate_state_consistency(trans, progress)

    # --- ③ 可选压缩 / 最小化 --------------------------------------------
    if compress:
        original_size = len(trans)
        if progress:
            print(f"🔬 开始Hopcroft最小化...")
        trans, accepting = _hopcroft_minimise(trans, accepting)
        if progress:
            print(f"   最小化后: {original_size:,} → {len(trans):,} 个状态")

        if progress:
            print(f"🗜️  开始路径压缩...")
        trans, accepting = _path_compress(trans, accepting)
        if progress:
            print(f"   路径压缩后: {len(trans):,} 个状态")

    # --- ④ 输出 FSM 和 runtime stub ----------------------------------------
    fsm_obj = {
        "version": 2,
        "compressed": compress,
        "states": list(trans.keys()),
        "edges": trans,
        "accept": list(accepting),
    }

    out_fsm = raw_dir / "autosar.fsm"
    out_fsm.write_text(json.dumps(fsm_obj, ensure_ascii=False, indent=2))

    stub_path = raw_dir / "autosar_allowed_tokens.py"
    stub_code = _render_runtime_stub(
        fsm_name=out_fsm.name,
        compress=compress,
        on_demand=on_demand,
        root_edges=trans,
        grammar=""
    )
    stub_path.write_text(stub_code, encoding="utf-8")

    print(f"✅ FSM 输出到: {out_fsm}")
    print(f"✅ Runtime stub 输出到: {stub_path}")

    return out_fsm

def find_concrete_children(abstract_class_id: int, attributes_path: pathlib.Path) -> list[dict]:
    """查找抽象类的所有具体实现"""
    concrete_children = []

    with attributes_path.open(encoding="utf-8") as fp:
        for ln in fp:
            if not ln.strip():
                continue
            row = json.loads(ln)

            # 查找以该抽象类为父类的所有属性
            if (row.get("classId") == abstract_class_id and
                    not row.get("isXmlAttr", False) and
                    row.get("xml_tag") and
                    row.get("typeId")):
                concrete_children.append({
                    'xml_tag': row['xml_tag'],
                    'typeId': row['typeId'],
                    'maxOccurs': row.get("maxOccurs", 1),
                    'minOccurs': row.get("minOccurs", 1)
                })

    return concrete_children


def validate_state_consistency(trans, progress=True):
    """验证状态一致性"""
    from collections import defaultdict

    issues = []

    # 检查目标状态是否存在
    for source, edges in trans.items():
        for token, target in edges.items():
            if target not in trans and target not in [""]:  # 空字符串状态可能不在trans中
                issues.append(f"状态 '{source}' 通过 '{token}' 到达不存在的状态 '{target}'")

    # 检查是否有过度共享的状态
    target_to_sources = defaultdict(list)
    for source, edges in trans.items():
        for token, target in edges.items():
            target_to_sources[target].append((source, token))

    suspicious_states = []
    for target, sources in target_to_sources.items():
        if len(sources) > 10:  # 如果一个状态被超过10个不同路径到达，可能有问题
            unique_tokens = set(token for _, token in sources)
            if len(unique_tokens) > 5:  # 且通过超过5个不同token到达
                suspicious_states.append((target, len(sources), len(unique_tokens)))

    if progress:
        if issues:
            print("❌ 发现状态引用问题:")
            for issue in issues[:5]:
                print(f"   {issue}")

        if suspicious_states:
            print("⚠️ 发现可疑的状态共享:")
            for state, source_count, token_count in suspicious_states[:3]:
                print(f"   状态 '{state}' 被 {source_count} 个路径到达，通过 {token_count} 个不同token")

    return len(issues) == 0 and len(suspicious_states) == 0


def visualize_fsm_structure_dict(trans, max_depth=5):
    """可视化FSM结构"""
    from collections import defaultdict, Counter

    print("🔍 FSM结构分析:")
    print(f"   总状态数: {len(trans)}")

    # 按深度分组
    depth_groups = defaultdict(list)
    for state in trans.keys():
        depth = state.count(" ") if state else 0
        if depth <= max_depth:
            depth_groups[depth].append(state)

    for depth in sorted(depth_groups.keys()):
        states = depth_groups[depth]
        print(f"   深度 {depth}: {len(states)} 个状态")

        # 显示该深度的token分布
        if depth > 0 and states:
            tokens_at_depth = []
            for state in states:
                if state:
                    last_token = state.split()[-1]
                    tokens_at_depth.append(last_token)

            token_freq = Counter(tokens_at_depth)
            common_tokens = token_freq.most_common(5)
            print(f"     常见token: {common_tokens}")

        # 显示示例状态
        for state in states[:3]:
            out_degree = len(trans.get(state, {}))
            print(f"     - '{state}' (出度: {out_degree})")
        if len(states) > 3:
            print(f"     ... 还有 {len(states) - 3} 个")


def debug_unresolved_paths(children, tag2cid, cid2classname, progress=True):
    """分析无法展开的路径"""
    if not progress:
        return

    print("🔍 分析展开阻塞点...")

    blocked_classes = []
    for cid, child_list in children.items():
        class_name = cid2classname.get(cid, f"unknown_{cid}")
        has_expandable_children = False

        for child_info in child_list:
            child_cid = child_info['child_cid']
            if child_cid in children or child_cid in tag2cid.values():
                has_expandable_children = True
                break

        if not has_expandable_children and child_list:
            blocked_classes.append({
                'cid': cid,
                'class_name': class_name,
                'child_count': len(child_list),
                'children': [
                    {
                        'xml_tag': child['xml_tag'],
                        'child_cid': child['child_cid'],
                        'child_class': cid2classname.get(child['child_cid'], f"unknown_{child['child_cid']}")
                    }
                    for child in child_list[:3]  # 只显示前3个
                ]
            })

    if blocked_classes:
        print(f"   发现 {len(blocked_classes)} 个可能的阻塞类:")
        for blocked in blocked_classes[:5]:  # 只显示前5个
            print(f"   - {blocked['class_name']} (CID: {blocked['cid']}, {blocked['child_count']} 个子元素)")
            for child in blocked['children']:
                print(f"     └─ {child['xml_tag']} -> {child['child_class']}")