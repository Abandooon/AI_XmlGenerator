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
from typing import Optional, Any
import json
from argparse import BooleanOptionalAction
import tomllib

import cfg
from dfa_compiler import compile_raw

# ── Hard‑coded defaults ───────────────────────────────────────────────────────

DEFAULT_KG = "bolt://neo4j:autosar4.2.2@127.0.0.1:7687"
DEFAULT_OUT_DIR = "artifacts"

# ── Utility helpers ───────────────────────────────────────────────────────────

# 单例缓存，任何模块可 from cli import BUILD_CFG 引用
def _load_build_cfg(path: str | pathlib.Path | None = None) -> dict[str, Any]:
    """
    查找并解析 build.toml：
        ① --config 指定
        ② CWD 下
        ③ 与 cli.py 同目录
    """
    candidates = (
        [pathlib.Path(path)] if path else []
    ) + [pathlib.Path.cwd() / "build.toml",
         pathlib.Path(__file__).with_name("build.toml")]
    for fp in candidates:
        if fp.is_file():
            with fp.open("rb") as f:
                return tomllib.load(f)
    return {}     # 没找到：落回空 dict

# 保持 module-level 全局
BUILD_CFG: dict[str, Any] = _load_build_cfg()

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
    GrammarExporter.run(raw_dir=args.raw,
                        out_path=args.out,
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

# ── 新增命令处理函数 --------------------------------------------------
def _cmd_compile_fsm(ns):
    from dfa_compiler import compile_raw
    # 修改 roots 处理逻辑
    if isinstance(ns.roots, str):
        # 如果是文件路径
        if ns.roots.endswith('.json'):
            roots = _load_roots(ns.roots)
        else:
            # 如果是逗号分隔的字符串
            roots = [r.strip() for r in ns.roots.split(',')]
    else:
        roots = ns.roots or []

    if not roots:
        raise ValueError("必须指定 roots 参数")

    compile_raw(
        ns.raw,
        roots=roots,
        compress=False,
        on_demand=False,
        progress=True,
    )


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
    GrammarExporter.run(raw_dir=raw_dir,
                        out_path=grammar_dir,
                        roots = roots)  # ← 把前面读到的 roots 列表传进来

    _print_step("Exporting SHACL shapes")
    ShaclExporter.run(enriched_file, shapes_dir)  # ② 同上

    _print_step("Compiling prefix DFA")
    compile_raw(
        raw_dir,
        roots=roots,
        compress=True,
        on_demand=True,
        progress=True,
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
    gexp.add_argument("--raw", required=True, help="directory containing raw_*.jsonl")
    gexp.add_argument("--out", default="grammar")
    gexp.add_argument("--roots", required=True, help="path to roots.json")

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

    # ── _build_parser()：新增 compile_fsm 子命令 ───────────────────────
    # 修改 compile_fsm 子命令的参数定义
    fsm = sub.add_parser("compile_fsm", help="raw → FSM (V4)")
    fsm.add_argument("--raw", required=True, help="raw_* 目录")
    # 修改 roots 参数：可以是文件路径或逗号分隔的标签列表
    fsm.add_argument("--roots", required=True,
                     help="roots.json 文件路径 或 逗号分隔的XML标签列表 (如 'APPLICATION-SW-COMPONENT-TYPE,FIBEX-ELEMENT')")
    fsm.add_argument("--compress", action=argparse.BooleanOptionalAction, default=True)
    fsm.add_argument("--on-demand", action=argparse.BooleanOptionalAction, default=True)
    fsm.add_argument("--progress", action=argparse.BooleanOptionalAction, default=False)
    fsm.set_defaults(func=_cmd_compile_fsm)

    # build --------------------------------------------------------------
    build = sub.add_parser("build", help="End-to-end pipeline (KG → all artifacts)")
    build.add_argument("--kg", default=DEFAULT_KG, help="Neo4j bolt URL")
    build.add_argument("--out", default=DEFAULT_OUT_DIR, help="output root directory")
    build.add_argument("--roots", help="path to roots.json (override auto-detect)")
    build.add_argument("--config", help="override build.toml path")

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

    # 若 --config 重新加载 build.toml
    if getattr(ns, "config", None):
        cfg.BUILD_CFG.clear()
        cfg.BUILD_CFG.update(cfg._load_build_cfg(ns.config))
    # 延迟导入，避免循环
    from dfa_compiler import compile_raw
    ns.func(ns)


if __name__ == "__main__":  # pragma: no cover
    main()
