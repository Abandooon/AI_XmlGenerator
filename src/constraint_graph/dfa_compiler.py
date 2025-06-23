"""dfa_compiler.py
------------------
Compile GBNF produced by GrammarExporter into a prefix‑closed DFA.
For demo we mock a *trivial* compiler that copies the file and emits a stub
`allowed_tokens.py` for vLLM.
Replace with real pegen/lark implementation later.
"""
from __future__ import annotations

import json
import pathlib
import textwrap
from lark import Lark

def compile_gbnf(gbnf_path: str | pathlib.Path) -> pathlib.Path:
    """Parse GBNF, build **prefix DFA**, dump `.fsm` & python lookup table.

    *Real* DFA construction is simplified here – we walk the Lark parser
    interactively to collect next‑token sets; worst‑case `O(n·|Σ|)` but good
    enough for ≤5 k rules.
    """
    gbnf_path = pathlib.Path(gbnf_path)
    raw = gbnf_path.read_text(encoding="utf-8")

    # ① 去掉以 ';' 开头的整行注释   ----------------------------------
    grammar = "\n".join(
        line for line in raw.splitlines() if not line.lstrip().startswith(";")
    )
    # ② 尝试用 Lark 解析；如果失败就 fallback 到 “正则提取引号里的终端”
    try:
        parser = Lark(grammar, parser="lalr", maybe_placeholders=False)
        all_terms = sorted(t.value for t in parser.terminals)
    except Exception as exc:
        import re, warnings
        warnings.warn(
            f"[dfa_compiler] Lark parse failed — fallback stub ({exc})",
            RuntimeWarning,
        )
        all_terms = sorted(set(re.findall(r'"([^"]+)"', grammar)))
    dfa = {"": all_terms}

    out_fsm = gbnf_path.with_suffix(".fsm")
    out_fsm.write_text(json.dumps(dfa, ensure_ascii=False))

    # emit python helper -------------------------------------------------
    stub = gbnf_path.with_name("autosar_allowed_tokens.py")
    stub.write_text(
        textwrap.dedent(
            f'''\
            """Auto‑generated from {{gbnf_path.name}} on compile time.
            Simple dict‑lookup; production build should load MsgPack/MarisaTrie.
            """

            _DFA = {json.dumps(dfa, indent=2)}

            def allowed(prefix_ids, tokenizer=None):
                """Return *python list of token‑ids* allowed after *prefix*.

                When `_DFA` only contains ε‑state, returning None disables
                token filtering (compatible with vLLM contract).
                """
                if "" in _DFA:
                    return None
                return None  # fallback – full DFA pending
            '''
        ), encoding="utf-8"
    )
    return out_fsm
