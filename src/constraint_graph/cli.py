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
import json
import os
import pathlib
import sys
import tomllib
from argparse import BooleanOptionalAction
from typing import Optional, Any, Dict

from dotenv import load_dotenv

import cfg
from dfa_compiler import compile_raw

load_dotenv(pathlib.Path(__file__).resolve().parents[2] / ".env")

# ── Hard‑coded defaults ───────────────────────────────────────────────────────

DEFAULT_KG = os.getenv("NEO4J_URI", "neo4j://127.0.0.1:7687")
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
    """修复版：确保传入 raw_classes.jsonl"""
    from enricher import ConstraintEnricher

    _print_step("Enriching constraints with schema info")

    # 🔧 修复：添加 raw_classes 参数
    raw_classes_fp = getattr(args, 'raw_classes', None)
    if not raw_classes_fp:
        # 自动推断 raw_classes.jsonl 位置
        raw_attr_path = pathlib.Path(args.raw_attr)
        raw_classes_fp = raw_attr_path.parent / "raw_classes.jsonl"

    ConstraintEnricher.run(
        args.raw_attr,
        args.raw_enum,
        args.canonical,
        args.out,
        raw_classes_fp=raw_classes_fp  # 🔧 传入 raw_classes.jsonl
    )
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
    """End‑to‑end pipeline with CID validation and severity classification"""

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
    raw_attributes = raw_dir / "raw_attributes.jsonl"
    raw_enums = raw_dir / "raw_enums.jsonl"
    raw_classes = raw_dir / "raw_classes.jsonl"

    # 🔧 验证关键文件存在
    required_files = [raw_constraints, raw_attributes, raw_enums, raw_classes]
    for file_path in required_files:
        if not file_path.exists():
            raise FileNotFoundError(f"Required file missing: {file_path}")

    print(f"✅ 验证raw文件完整性: {len(required_files)} 个文件都存在")

    # 2) canonicalize + enrich
    from canonicalizer import Canonicalizer
    from enricher import ConstraintEnricher

    canonical_file = root / "canonical_constraints.json"
    enriched_file = root / "enriched_constraints.json"

    _print_step("Canonicalizing constraints")
    Canonicalizer.run(raw_constraints, canonical_file)

    _print_step("Enriching constraints with schema info and severity classification")
    ConstraintEnricher.run(
        raw_attributes,
        raw_enums,
        canonical_file,
        enriched_file,
        raw_classes_fp=raw_classes
    )

    # 🔧 新增：验证CID一致性
    _print_step("Validating CID consistency throughout pipeline")
    validation_result = validate_cid_pipeline(
        str(raw_constraints),
        str(canonical_file),
        str(enriched_file)
    )

    if validation_result["overall_consistency"] > 0.9:
        print("✅ CID一致性验证通过")
    else:
        print(f"⚠️  CID一致性较低 ({validation_result['overall_consistency']:.1%})，但继续处理")
        print("   建议检查KG提取和字段映射逻辑")

    # 3) exports
    from grammar_exporter import GrammarExporter
    from shacl_exporter import ShaclExporter
    from smt_exporter import SmtExporter

    gbnf_file = grammar_dir / "autosar.gbnf"

    _print_step("Exporting GBNF grammar & allowed-tokens stub")
    GrammarExporter.run(raw_dir=raw_dir,
                        out_path=grammar_dir,
                        roots=roots)

    _print_step("Exporting SHACL shapes with severity classification")
    ShaclExporter.run(enriched_file, shapes_dir)

    _print_step("Compiling prefix DFA")
    compile_raw(
        raw_dir,
        roots=roots,
        compress=True,
        on_demand=True,
        progress=True,
    )

    _print_step("Exporting SMT constraints with severity classification")
    SmtExporter.run(enriched_file, root / "smt")
    print("✅  SMT constraints →", root / "smt")

    print("\n🎉  Pipeline completed with CID traceability and severity classification →", root)


def _build_parser() -> argparse.ArgumentParser:
    """修复版：为 enrich 命令添加 raw_classes 参数"""
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
    enr.add_argument("--raw-attr", required=True, help="path to raw_attributes.jsonl")
    enr.add_argument("--raw-enum", required=True, help="path to raw_enums.jsonl")
    enr.add_argument("--raw-classes", help="path to raw_classes.jsonl (auto-detect if not provided)")  # 🔧 新增
    enr.add_argument("--out", default="enriched_constraints.json")
    enr.set_defaults(func=_cmd_enrich)

    # 其他命令保持不变...
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
    dfa.add_argument("--roots", help="path to roots.json (override auto-detect)")
    dfa.add_argument(
        "--compress",
        dest="compress",
        action=BooleanOptionalAction,
        default=True,
        help="Hopcroft+chain compression (default: ON)",
    )
    dfa.add_argument(
        "--on-demand",
        dest="on_demand",
        action=BooleanOptionalAction,
        default=True,
        help="emit lazy runtime helper (default: ON)",
    )
    dfa.add_argument("--progress", action="store_true",
                     help="periodically print DFA compile progress")
    dfa.set_defaults(func=_cmd_compile_dfa)

    # compile_fsm --------------------------------------------------------
    fsm = sub.add_parser("compile_fsm", help="raw → FSM (V4)")
    fsm.add_argument("--raw", required=True, help="raw_* 目录")
    fsm.add_argument("--roots", required=True,
                     help="roots.json 文件路径 或 逗号分隔的XML标签列表")
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


def validate_cid_pipeline(raw_constraints_file: str,
                          canonical_constraints_file: str,
                          enriched_constraints_file: str) -> Dict[str, Any]:
    """验证整个pipeline的CID一致性"""
    import json

    print("🔍 开始CID pipeline验证...")

    # 1. 读取raw约束
    with open(raw_constraints_file, 'r', encoding='utf-8') as f:
        raw_constraints = [json.loads(line) for line in f if line.strip()]

    # 2. 读取canonical约束
    with open(canonical_constraints_file, 'r', encoding='utf-8') as f:
        canonical_constraints = json.load(f)

    # 3. 读取enriched约束
    with open(enriched_constraints_file, 'r', encoding='utf-8') as f:
        enriched_constraints = json.load(f)

    # 4. 提取各阶段的CID
    raw_cids = set()
    for c in raw_constraints:
        cid = c.get("cid")
        if cid and not cid.startswith("NEO4J_") and not cid.startswith("UNKNOWN_"):
            raw_cids.add(cid)

    canonical_cids = set()
    for c in canonical_constraints:
        cid = c.get("cid") or c.get("original_cid")
        if cid and not cid.startswith("NEO4J_") and not cid.startswith("UNKNOWN_"):
            canonical_cids.add(cid)

    enriched_semantic_cids = set()
    for c in enriched_constraints:
        if c.get("is_semantic", False):
            cid = c.get("cid") or c.get("original_cid")
            if cid and not cid.startswith("NEO4J_") and not cid.startswith("UNKNOWN_"):
                enriched_semantic_cids.add(cid)

    # 5. 验证一致性
    raw_to_canonical = len(raw_cids.intersection(canonical_cids))
    canonical_to_enriched = len(canonical_cids.intersection(enriched_semantic_cids))
    raw_to_enriched = len(raw_cids.intersection(enriched_semantic_cids))

    # 6. 统计结果
    validation_result = {
        "raw_constraints_count": len(raw_constraints),
        "canonical_constraints_count": len(canonical_constraints),
        "enriched_semantic_count": len([c for c in enriched_constraints if c.get("is_semantic")]),
        "enriched_structural_count": len([c for c in enriched_constraints if c.get("is_structural")]),

        "raw_cids_count": len(raw_cids),
        "canonical_cids_count": len(canonical_cids),
        "enriched_semantic_cids_count": len(enriched_semantic_cids),

        "raw_to_canonical_match": raw_to_canonical,
        "canonical_to_enriched_match": canonical_to_enriched,
        "raw_to_enriched_match": raw_to_enriched,

        "raw_to_canonical_rate": raw_to_canonical / len(raw_cids) if raw_cids else 0,
        "canonical_to_enriched_rate": canonical_to_enriched / len(canonical_cids) if canonical_cids else 0,
        "raw_to_enriched_rate": raw_to_enriched / len(raw_cids) if raw_cids else 0,

        "missing_in_canonical": raw_cids - canonical_cids,
        "missing_in_enriched": canonical_cids - enriched_semantic_cids,
        "overall_consistency": raw_to_enriched / len(raw_cids) if raw_cids else 0
    }

    # 7. 输出报告
    print(f"📊 CID一致性验证报告:")
    print(f"   Raw → Canonical: {raw_to_canonical}/{len(raw_cids)} ({validation_result['raw_to_canonical_rate']:.1%})")
    print(
        f"   Canonical → Enriched: {canonical_to_enriched}/{len(canonical_cids)} ({validation_result['canonical_to_enriched_rate']:.1%})")
    print(f"   Raw → Enriched: {raw_to_enriched}/{len(raw_cids)} ({validation_result['raw_to_enriched_rate']:.1%})")
    print(f"   整体一致性: {validation_result['overall_consistency']:.1%}")

    if validation_result["missing_in_canonical"]:
        missing_list = list(validation_result['missing_in_canonical'])[:5]
        print(f"   Canonical中缺失: {missing_list}...")

    if validation_result["missing_in_enriched"]:
        missing_list = list(validation_result['missing_in_enriched'])[:5]
        print(f"   Enriched中缺失: {missing_list}...")

    return validation_result


def debug_constraint_cid(constraint_file: str, target_cid: str):
    """调试特定CID的约束在pipeline中的状态"""
    import json

    print(f"🔍 调试约束CID: {target_cid}")

    with open(constraint_file, 'r', encoding='utf-8') as f:
        if constraint_file.endswith('.jsonl'):
            constraints = [json.loads(line) for line in f if line.strip()]
        else:
            constraints = json.load(f)

    found_constraints = []
    for c in constraints:
        cid = c.get("cid") or c.get("original_cid")
        if cid == target_cid:
            found_constraints.append(c)

    if found_constraints:
        print(f"✅ 找到 {len(found_constraints)} 个匹配的约束:")
        for i, c in enumerate(found_constraints, 1):
            print(f"   {i}. CID: {c.get('cid')}")
            print(f"      原始CID: {c.get('original_cid')}")
            print(f"      类型: {c.get('type') or c.get('constraint_type')}")
            print(f"      标题: {c.get('title', 'N/A')[:50]}")
            print(f"      表达式: {c.get('expression', 'N/A')[:50]}")
            print(f"      来源: {c.get('constraint_source', 'unknown')}")
            print(f"      严重性: {c.get('severity', 'unknown')}")
            print(f"      是否结构约束: {c.get('is_structural', False)}")
            print(f"      是否语义约束: {c.get('is_semantic', False)}")
            print()
    else:
        print(f"❌ 未找到CID为 {target_cid} 的约束")


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
    ns.func(ns)


if __name__ == "__main__":  # pragma: no cover
    main()
