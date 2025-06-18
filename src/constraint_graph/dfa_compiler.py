"""dfa_compiler.py
------------------
Compile GBNF produced by GrammarExporter into a prefix‑closed DFA.
For demo we mock a *trivial* compiler that copies the file and emits a stub
`allowed_tokens.py` for vLLM.
Replace with real pegen/lark implementation later.
"""
from __future__ import annotations

import pathlib
import textwrap


def compile_gbnf(gbnf_path: str | pathlib.Path) -> pathlib.Path:
    gbnf_path = pathlib.Path(gbnf_path)
    out_fsm = gbnf_path.with_suffix(".fsm")
    out_fsm.write_text("<fsm>placeholder</fsm>")

    # emit python stub
    stub = gbnf_path.with_name("autosar_allowed_tokens.py")
    stub.write_text(
        textwrap.dedent(
            '''\
            """prefix_allowed_tokens_fn stub – ALWAYS allow all tokens.
            Replace with DFA transition table lookup generated from .fsm file."""
            def allowed(*_):
                return None  # returning None means "no restriction" in vLLM
            '''
        )
    )
    return out_fsm
