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
from typing import Dict, List, MutableMapping, Set, Tuple
from utils import normalize
from cfg import BUILD_CFG

from lark import Lark


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
    root_edges: EdgeTable,
    grammar: str,
) -> str:
    root_json = json.dumps(root_edges, ensure_ascii=False, indent=2)
    grammar_repr = textwrap.indent(json.dumps(grammar), " " * 4) if on_demand else "    ''"
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
        import functools
        from typing import List, Optional

        _ROOT_DFA = {root_json}
        _GRAMMAR = (
{grammar_repr}
        )

        {"from lark import Lark" if on_demand else ""}
        {"_PARSER = Lark(_GRAMMAR, parser='lalr', maybe_placeholders=False)" if on_demand else ""}

        _CACHE_SIZE = {lru_size}

        def _calc_follow(prefix_tokens: List[str]) -> List[str]:
            """Lazy follow-set using Lark when not in _ROOT_DFA."""
            {"return []  # disabled" if not on_demand else "return [t.value for t in _PARSER.parse_interactive(' '.join(prefix_tokens)).accepts()]"}
        
        @functools.lru_cache(maxsize=_CACHE_SIZE)
        def _allowed(prefix: str) -> Optional[List[int]]:
            toks = prefix.split() if prefix else []
            state = ' '.join(toks)
            if state in _ROOT_DFA:
                # stored subset
                return _ROOT_DFA[state]
            follow = _calc_follow(toks)
            return follow

        # vLLM entry point -------------------------------------------------
        def allowed(prefix_ids, tokenizer) -> Optional[List[int]]:
            """
            Args:
                prefix_ids : list[int] – already emitted *token ids*
                tokenizer  : tokenizer with decode()
            Returns:
                *list[int]* of *token ids* allowed next, or None to disable
            """
            if not prefix_ids or not tokenizer:
                return None  # disable filter for degenerate cases
            prefix_txt = tokenizer.decode(prefix_ids, skip_special_tokens=True).strip()
            follow_terms = _allowed(prefix_txt)
            if follow_terms is None:
                return None
            return [tokenizer.encode(t, add_special_tokens=False)[0] for t in follow_terms]
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

# ── 新增：直接从 raw 快照编译 FSM ─────────────────────────────────
def compile_raw(
    raw_dir: str | pathlib.Path,
    *,
    roots: list[str],
    compress: bool = False,
    on_demand: bool = False,
    progress: bool = False,
) -> pathlib.Path:
    """
    V4 版：raw_classes / raw_attributes → FSM。
    输出 <raw_dir>/autosar.fsm；返回其路径。
    """
    import collections, json, pathlib, utils

    raw_dir = pathlib.Path(raw_dir)
    c_path, a_path = raw_dir / "raw_classes.jsonl", raw_dir / "raw_attributes.jsonl"
    if not (c_path.is_file() and a_path.is_file()):
        raise FileNotFoundError("raw_dir 必须包含 raw_classes.jsonl 与 raw_attributes.jsonl")

    # --- ① 预索引 -------------------------------------------------------
    tag2cid, id2tag, wrappers = {}, {}, {}  # ← 新增 id2tag
    children: dict[int, list[int]] = collections.defaultdict(list)

    # ----- classes -------------------------------------------------------
    with c_path.open(encoding="utf-8") as fp:
        for ln in fp:
            row = json.loads(ln)
            cid = row["classId"]
            norm_tag = utils.normalize(row["xml_tag"])  # ← snake_case
            tag2cid[norm_tag] = cid
            id2tag[cid] = norm_tag

    # ----- attributes ----------------------------------------------------
    with a_path.open(encoding="utf-8") as fp:
        for ln in fp:
            row = json.loads(ln)
            pid = row["classId"]  # ← parent = classId
            if w := row.get("xml_wrapper_tag"):  # ← snake_case
                wrappers[pid] = utils.normalize(w)
            child_cid = row.get("typeId")  # ← 下钻目标
            if child_cid and child_cid in id2tag:  # ← 只保存在 cls 表里的
                children[pid].append(child_cid)

    # --- ② BFS 构建迁移表 ----------------------------------------------
    start = [utils.normalize(r) for r in roots]
    trans, accepting = {}, set()
    q = collections.deque([(t, 0) for t in start])  # ← tuple(tag, depth)

    while q:
        tag, depth = q.popleft()  # ← 正常解包
        if depth >= MAX_DEPTH:
            continue
        cid = tag2cid[tag]
        trans.setdefault(tag, {})

        # wrapper → item
        if cid in wrappers:
            w_tag = wrappers[cid]
            trans[tag][w_tag] = w_tag
            trans.setdefault(w_tag, {})[tag] = tag
            tag = w_tag  # 子元素挂在 wrapper 下

        # children
        for child_cid in children.get(cid, []):
            child_tag = id2tag[child_cid]
            trans[tag][child_tag] = child_tag
            if child_tag not in trans:
                q.append((child_tag, depth + 1))  # ← 深度 +1

    accepting = set(trans)

    # --- ③ 可选压缩 / 最小化 --------------------------------------------
    if compress:
        trans, accepting = _path_compress(trans, accepting)
    if on_demand:
        trans, accepting = _hopcroft_minimise(trans, accepting)

    # --- ④ 输出 ---------------------------------------------------------
    out = raw_dir / "autosar.fsm"
    out.write_text(json.dumps({"trans": trans, "accepting": list(accepting)}, indent=2))
    return out
