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

from lark import Lark


# ── Parameters (could be CLI-tuned) ───────────────────────────────────────────
MAX_DEPTH = 10                      # stop BFS after this many tokens
CHAIN_COMPRESS_THRESHOLD = 1        # “linear” means ≤1 outgoing edge
LRU_CACHE_SIZE = 10_000             # on-demand runtime
PROGRESS_STEP = 10_000


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
        next_terms = parser.parse_interactive(" ".join(toks)).accepts()
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
            nxt = " ".join(toks + [t])
            transitions[state][t] = nxt
            if nxt not in transitions:
                q.append((nxt, toks + [t]))
        processed += 1
        if progress and processed % PROGRESS_STEP == 0:
            print(f"   … {processed:,} states explored (queue={len(q):,})")
    return transitions, accepting


def _hopcroft_minimise(trans: EdgeTable, accepting: Set[State]) -> Tuple[EdgeTable, Set[State]]:
    """
    Classic Hopcroft partition-refinement algorithm.
    Returns a *new* transitions dict whose keys are representative states.
    """
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

    for s in trans:
        if s in skip:
            continue
        cur = s
        chain: List[str] = []
        while (
            cur not in accepting
            and len(trans[cur]) == 1
            and list(trans[cur].values())[0] not in accepting
            and len(trans[list(trans[cur].values())[0]]) == 1
        ):
            tok, nxt = next(iter(trans[cur].items()))
            chain.append(tok)
            skip.add(cur)
            cur = nxt
        # store edge
        if chain:
            edge_key = "|".join(chain)
            out.setdefault(s, {})[edge_key] = cur
        # copy remaining edges
        for a, t in trans[cur].items():
            out.setdefault(cur, {})[a] = t

    # plus states that never appear as src
    for s, edges in trans.items():
        if s not in out:
            out[s] = edges
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

    roots_set = None
    if roots:
        # 统一成小写+下划线，便于匹配 Terminal 名
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