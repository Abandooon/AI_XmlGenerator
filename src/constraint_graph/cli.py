import argparse
import pathlib

from loader import KGLoader
from token_extractor import TokenExtractor

__all__ = ["build_arg_parser"]


def _export_tokens(ns: argparse.Namespace) -> None:
    """CLI entry: `export-tokens`"""
    kg = KGLoader(ns.kg, user=ns.user, password=ns.password)
    roots = _read_roots(ns.roots)

    extractor = TokenExtractor(kg, roots)
    extractor.dump(ns.out)

    print("✅ Token source tables written to", ns.out)


def _read_roots(path: str | None) -> list[str | int]:
    if path is None:
        raise SystemExit("--roots JSON file is required")
    import json, os

    with open(os.fspath(path), "r", encoding="utf-8") as f:
        roots = json.load(f)
    if not isinstance(roots, list):
        raise ValueError("roots json must be a list")
    return roots


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser("constraint-graph utils")
    sub = p.add_subparsers(dest="cmd", required=True)

    # -------------------------------------------------------------
    t = sub.add_parser("export-tokens", help="dump raw tables for token build")
    t.add_argument("--kg", required=True, help="bolt:// or directory with nodes.json")
    t.add_argument("--user", help="neo4j user")
    t.add_argument("--password", help="neo4j password")
    t.add_argument("--roots", required=True, help="JSON file listing root class xml_tag or ids")
    t.add_argument("--out", type=pathlib.Path, default=pathlib.Path("out/token-src"))
    t.set_defaults(func=_export_tokens)

    return p


if __name__ == "__main__":
    ns = build_arg_parser().parse_args()
    ns.func(ns)
