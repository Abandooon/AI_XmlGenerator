"""cli.py — one‑click KG → XML pipeline
================================================
Right‑click / double‑click to run without any command‑line arguments.
Internal constants define the KG connection and output directory.

* Default KG (Bolt) : bolt://neo4j:mySecretPwd@localhost:7687
* Output artifacts  : ./artifacts/

You *can* still pass CLI args to override these defaults, e.g.
    python -m cli build --kg bolt://user:pwd@remote:7687 --out /tmp/out
"""
from __future__ import annotations

import argparse
import pathlib
import sys
from typing import Optional
import json
from argparse import BooleanOptionalAction

# ── Hard‑coded defaults ───────────────────────────────────────────────────────

DEFAULT_KG = "bolt://neo4j:autosar4.2.2@127.0.0.1:7687"
DEFAULT_OUT_DIR = "artifacts"

# ── Utility helpers ───────────────────────────────────────────────────────────

def _ensure_dir(p: pathlib.Path) -> pathlib.Path:
    p.mkdir(parents=True, exist_ok=True)
    return p


def _print_step(msg: str) -> None:
    print(f"\n🛠️  {msg} …", flush=True)

def _load_roots(explicit: str | None = None) -> list[str | int] | None:
    """
    * 若显式传入 `--roots <file>` 就读那个文件
    * 否则依次尝试：
        ① 与 cli.py 同目录的 roots.json
        ② 当前工作目录的 roots.json
    * 全部找不到则返回 ``None``（由 TokenExtractor 自动推断）
    """
    candidates = (
        [pathlib.Path(explicit)] if explicit else []
    ) + [
        pathlib.Path(__file__).with_name("roots.json"),
        pathlib.Path.cwd() / "roots.json",
    ]
    for fp in candidates:
        if fp.is_file():
            return json.loads(fp.read_text(encoding="utf-8"))
    return None


# ── Sub‑command implementations ───────────────────────────────────────────────


def _cmd_dump_raw(args: argparse.Namespace) -> None:
    """KG → raw_*.jsonl"""
    from token_extractor import TokenExtractor  # lazy import

    _print_step("Dumping raw tables from KG")
    roots = _load_roots(args.roots)
    TokenExtractor.from_kg(args.kg, roots=roots).dump(_ensure_dir(pathlib.Path(args.out)))
    print("✅  raw tables written to", args.out)


def _cmd_canonicalize(args: argparse.Namespace) -> None:
    from canonicalizer import Canonicalizer

    _print_step("Canonicalizing constraints")
    Canonicalizer.run(args.raw_constraints, args.out)
    print("✅  canonical_constraints.json →", args.out)


def _cmd_enrich(args: argparse.Namespace) -> None:
    from enricher import ConstraintEnricher

    _print_step("Enriching constraints with schema info")
    ConstraintEnricher.run(args.raw_attr, args.raw_enum,
                        args.canonical, args.out)
    print("✅  enriched_constraints.json →", args.out)


def _cmd_export_grammar(args: argparse.Namespace) -> None:
    from grammar_exporter import GrammarExporter
    _print_step("Exporting GBNF grammar & allowed‑tokens stub")
    roots = _load_roots(args.roots)  # ← 复用同一加载函数
    GrammarExporter.run(args.enriched,
                        args.out,
                        roots = roots)  # ← 传列表而非路径
    print("✅  Grammar artifacts →", args.out)


def _cmd_export_shacl(args: argparse.Namespace) -> None:
    from shacl_exporter import ShaclExporter

    _print_step("Exporting SHACL shapes")
    ShaclExporter(args.out).run(args.enriched)
    print("✅  SHACL shapes →", args.out)


def _cmd_compile_dfa(args: argparse.Namespace) -> None:
    from dfa_compiler import compile_gbnf

    _print_step("Compiling prefix DFA")
    roots = _load_roots(args.roots)
    compile_gbnf(
        args.gbnf,
        compress = args.compress,
        on_demand = args.on_demand,
        progress = args.progress,
        roots=roots,
    )
    print("✅  DFA compiled next to GBNF")

# ── One‑stop build ────────────────────────────────────────────────────────────


def _cmd_build(args: argparse.Namespace) -> None:
    """End‑to‑end pipeline: KG → all artifacts"""

    root = pathlib.Path(args.out)
    raw_dir = _ensure_dir(root / "raw")
    grammar_dir = _ensure_dir(root / "grammar")
    shapes_dir = _ensure_dir(root / "shapes")

    # 1) KG → raw
    from token_extractor import TokenExtractor

    _print_step("Dumping raw tables from KG")
    roots = _load_roots(getattr(args, "roots", None))
    TokenExtractor.from_kg(args.kg, roots=roots).dump(raw_dir)

    raw_constraints = raw_dir / "raw_constraints.jsonl"

    # 2) canonicalize + enrich
    from canonicalizer import Canonicalizer
    from enricher import ConstraintEnricher

    canonical_file = root / "canonical_constraints.json"
    enriched_file = root / "enriched_constraints.json"

    _print_step("Canonicalizing constraints")
    Canonicalizer.run(raw_constraints, canonical_file)

    _print_step("Enriching constraints with schema info")
    ConstraintEnricher.run(raw_dir / "raw_attributes.jsonl",
                           raw_dir / "raw_enums.jsonl",
                           canonical_file,
                           enriched_file)

    # 3) exports
    from grammar_exporter import GrammarExporter
    from shacl_exporter import ShaclExporter
    from dfa_compiler import compile_gbnf
    from smt_exporter import SmtExporter

    gbnf_file = grammar_dir / "autosar.gbnf"

    _print_step("Exporting GBNF grammar & allowed-tokens stub")
    GrammarExporter.run(enriched_file,
                        grammar_dir,
                        roots = roots)  # ← 把前面读到的 roots 列表传进来

    _print_step("Exporting SHACL shapes")
    ShaclExporter.run(enriched_file, shapes_dir)  # ② 同上

    _print_step("Compiling prefix DFA")
    compile_gbnf(
        gbnf_file,
        compress=True,  # 开启 Hopcroft + path-compression
        on_demand=True,  # 只写根≤3层，其余运行时懒解析
        progress=True,  # 定期打印编译进度
        roots=roots
    )
    SmtExporter.run(enriched_file, root / "smt")
    print("✅  SMT constraints →", root / "smt")

    print("\n🎉  Pipeline completed →", root)

# ── CLI parser wiring ─────────────────────────────────────────────────────────


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser("constraint‑graph toolkit")
    sub = p.add_subparsers(dest="cmd", required=True)

    # dump_raw -----------------------------------------------------------
    dump = sub.add_parser("dump_raw", help="KG → raw_*.jsonl")
    dump.add_argument("--kg", default=DEFAULT_KG, help="Neo4j bolt URL")
    dump.add_argument("--out", default="data/raw", help="output dir")
    dump.add_argument("--roots", help="path to roots.json")
    dump.set_defaults(func=_cmd_dump_raw)

    # canonicalize -------------------------------------------------------
    canon = sub.add_parser("canonicalize", help="raw_constraints → canonical_constraints.json")
    canon.add_argument("raw_constraints")
    canon.add_argument("--out", default="canonical_constraints.json")
    canon.set_defaults(func=_cmd_canonicalize)

    # enrich -------------------------------------------------------------
    enr = sub.add_parser("enrich", help="canonical_constraints → enriched_constraints.json")
    enr.add_argument("canonical")
    enr.add_argument("--out", default="enriched_constraints.json")
    enr.set_defaults(func=_cmd_enrich)

    # grammar ------------------------------------------------------------
    gexp = sub.add_parser("export_grammar", help="enriched → Grammar artifacts")
    gexp.add_argument("enriched")
    gexp.add_argument("--out", default="grammar")
    gexp.set_defaults(func=_cmd_export_grammar)

    # shacl --------------------------------------------------------------
    sexp = sub.add_parser("export_shacl", help="enriched → SHACL TTL")
    sexp.add_argument("enriched")
    sexp.add_argument("--out", default="shapes")
    sexp.set_defaults(func=_cmd_export_shacl)

    # dfa ----------------------------------------------------------------
    dfa = sub.add_parser("compile_dfa", help="GBNF → DFA")
    dfa.add_argument("gbnf")

    # 特定roottag开关
    dfa.add_argument("--roots", help="path to roots.json (override auto-detect)")

    # ① 压缩开关：默认 ON，可 --no-compress 关闭
    dfa.add_argument(
    "--compress",
        dest = "compress",
        action = BooleanOptionalAction,
        default = True,
        help = "Hopcroft+chain compression (default: ON)",
    )

    # ② 懒加载开关：默认 ON，可 --no-on-demand 关闭
    dfa.add_argument(
    "--on-demand",
        dest = "on_demand",
        action = BooleanOptionalAction,
        default = True,
        help = "emit lazy runtime helper (default: ON)",
    )
    dfa.add_argument("--progress", action="store_true",
                    help = "periodically print DFA compile progress")
    dfa.set_defaults(func=_cmd_compile_dfa)

    # build --------------------------------------------------------------
    build = sub.add_parser("build", help="End‑to‑end pipeline (KG → all artifacts)")
    build.add_argument("--kg", default=DEFAULT_KG, help="Neo4j bolt URL")
    build.add_argument("--out", default=DEFAULT_OUT_DIR, help="output root directory")
    build.add_argument("--roots", help="path to roots.json (override auto-detect)")

    build.set_defaults(func=_cmd_build)

    return p

# ── main entry ───────────────────────────────────────────────────────────────


def main(argv: Optional[list[str]] = None) -> None:
    """If no CLI args are supplied, run full pipeline with built‑in defaults."""
    if argv is None:
        argv = sys.argv[1:]

    if not argv:  # double‑click / right‑click run
        print("(no arguments) → running full build with embedded defaults")
        _cmd_build(argparse.Namespace(kg=DEFAULT_KG, out=DEFAULT_OUT_DIR))
        return

    parser = _build_parser()
    ns = parser.parse_args(argv)
    ns.func(ns)  # type: ignore[attr-defined]


if __name__ == "__main__":  # pragma: no cover
    main()
