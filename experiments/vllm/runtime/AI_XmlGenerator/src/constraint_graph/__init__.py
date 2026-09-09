# constraint_graph package
"""Unified Constraint Graph – converts KG constraints to executable artefacts.

Exposes high‑level API:

    from constraint_graph.cli import main
    main(["export", "--kg", "./out/kg", "--out", "./out/cg"])

"""
__all__ = [
    "loader",
    "canonicalizer",
    "grammar_exporter",
    "dfa_compiler",
    "shacl_exporter",
    "smt_exporter",
    "cli",
]
