"""constraint_graph/cli.py  (v1.3)
------------------------------------------------
High‑level CLI & importable export() function **with Enricher stage**.
"""
from __future__ import annotations

import argparse
import os
import pathlib
import sys
from typing import List, Optional

from loader import ConstraintLoader
from canonicalizer import Canonicalizer
from enricher import ConstraintEnricher  # NEW
from grammar_exporter import GrammarExporter
from dfa_compiler import compile_gbnf
from shacl_exporter import ShaclExporter
from smt_exporter import SmtExporter

__all__ = ["export"]

# ------------------------------------------------------------
# Public callable (PyCharm can call directly)
# ------------------------------------------------------------

def export(kg: str, out: str = "out/cg") -> None:
    ns = argparse.Namespace(kg=kg, out=out)
    _export_cmd(ns)


# ------------------------------------------------------------
# internal main logic
# ------------------------------------------------------------

def _export_cmd(ns: argparse.Namespace) -> None:
    kg_uri = str(ns.kg)
    out_dir = pathlib.Path(ns.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 0. load raw + canonicalize
    loader = ConstraintLoader(kg_uri)
    raw_constraints = loader.load()
    canonical = Canonicalizer().canonicalize(raw_constraints)

    # 1. enrich with Attribute/Enum meta
    enricher = ConstraintEnricher(loader.attr_idx, loader.enum_idx)
    constraints = enricher.enrich(canonical)

    # 2. Grammar & DFA
    g_path = GrammarExporter(out_dir).export(constraints)
    compile_gbnf(g_path)

    # 3. SHACL / SMT
    ShaclExporter(out_dir).export(constraints)
    SmtExporter(out_dir).export(constraints)

    print("✅ Constraint artefacts exported to", out_dir)


# ------------------------------------------------------------
# CLI wrapper
# ------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser("constraint_graph", add_help=True)
    sub = p.add_subparsers(dest="cmd", required=True)

    exp = sub.add_parser("export", help="export artefacts from KG (bolt URI or dir)")
    exp.add_argument("--kg", required=True)
    exp.add_argument("--out", default="out/cg")
    exp.set_defaults(func=_export_cmd)
    return p


def main(argv: Optional[List[str]] = None):
    if argv is None and len(sys.argv) == 1:  # called bare → env fallback
        kg_uri = os.getenv("KG_URI", "neo4j://127.0.0.1:7687")
        out_dir = os.getenv("OUT_DIR", "out/cg")
        export(kg_uri, out_dir)
        return
    parser = _build_parser()
    ns = parser.parse_args(argv)
    ns.func(ns)


if __name__ == "__main__":
    main()
