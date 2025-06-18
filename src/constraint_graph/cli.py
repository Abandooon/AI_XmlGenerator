"""constraint_graph.cli (v1.1)
--------------------------------
High‑level API & CLI to export constraint artefacts.
可作为模块 `constraint_graph.export(kg_uri, out_dir)` 直接调用，
也可在命令行使用 `python -m constraint_graph.cli export ...`。
"""
from __future__ import annotations

import argparse
import os
import pathlib
import sys
from typing import List, Optional

from loader import ConstraintLoader
from canonicalizer import Canonicalizer
from grammar_exporter import GrammarExporter
from dfa_compiler import compile_gbnf
from shacl_exporter import ShaclExporter
from smt_exporter import SmtExporter

__all__ = ["export"]

# ------------------------------------------------------------
# Public callable (for PyCharm Run without params)
# ------------------------------------------------------------

def export(kg: str, out: str = "out/cg") -> None:
    """Programmatic entrypoint; wraps internal export_cmd logic."""
    ns = argparse.Namespace(kg=kg, out=out)
    _export_cmd(ns)


# ------------------------------------------------------------
# internal
# ------------------------------------------------------------

def _export_cmd(ns: argparse.Namespace) -> None:
    kg_uri = ns.kg
    out_dir = pathlib.Path(ns.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 0. load & canonicalize
    canon = Canonicalizer()
    loader = ConstraintLoader(kg_uri)
    canonical_constraints = canon.canonicalize(loader.load())

    # 1. grammar
    g_path = GrammarExporter(out_dir).export(canonical_constraints)

    # 2. dfa
    compile_gbnf(g_path)

    # 3. shacl
    ShaclExporter(out_dir).export(canonical_constraints)

    # 4. smt
    SmtExporter(out_dir).export(canonical_constraints)

    print("✅ Constraint artefacts exported to", out_dir)


# ------------------------------------------------------------
# CLI
# ------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser("constraint_graph", add_help=True)
    sub = p.add_subparsers(dest="cmd", required=True)

    exp = sub.add_parser("export", help="export artefacts from existing KG")
    exp.add_argument("--kg", required=True, help="KG directory or bolt URI")
    exp.add_argument("--out", default="out/cg", help="output directory")
    exp.set_defaults(func=_export_cmd)
    return p


def main(argv: Optional[List[str]] = None):
    if argv is None and len(sys.argv) == 1:
        # Called without CLI params (e.g. PyCharm "Run" button) → try env vars
        kg_uri = os.getenv("KG_URI", "bolt://localhost:7687")
        out_dir = os.getenv("OUT_DIR", "out/cg")
        export(kg_uri, out_dir)
        return

    parser = _build_parser()
    ns = parser.parse_args(argv)
    ns.func(ns)


if __name__ == "__main__":  # pragma: no cover
    main()
