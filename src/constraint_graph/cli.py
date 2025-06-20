"""cli.py – run token‑extraction either via hard‑coded defaults (so you can
just **right‑click → Run** in PyCharm) *or* via command‑line arguments if you
prefer flexibility.

If **no CLI arguments** are supplied, the script falls back to the constants
in the section *"Default configuration (PyCharm friendly)"* below.

Typical usage patterns
----------------------

* **PyCharm** – right‑click this file → *Run 'cli'* → it will connect to the
  KG specified by the constants and dump tables to the output directory.
* **Terminal** – `python cli.py --kg bolt://... --roots roots.json` etc. to
  override those defaults without editing the file.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
from typing import List, Union

from loader import KGLoader
from token_extractor import TokenExtractor

__all__ = ["main"]

# ---------------------------------------------------------------------------
# Default configuration (PyCharm friendly)
# ---------------------------------------------------------------------------
KG_SOURCE: str | pathlib.Path = "neo4j://127.0.0.1:7687"  # or path to KG dump dir
KG_USER: str | None = "neo4j"
KG_PASSWORD: str | None = "autosar4.2.2"
ROOTS_PATH: str | pathlib.Path = "roots.json"            # list of xml_tag / id
OUT_DIR: pathlib.Path = pathlib.Path("out/token-src")


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _read_roots(path: str | os.PathLike) -> List[Union[str, int]]:
    with open(os.fspath(path), "r", encoding="utf-8") as f:
        roots = json.load(f)
    if not isinstance(roots, list):
        raise ValueError("roots json must be a list")
    return roots


# ---------------------------------------------------------------------------
# Core execution
# ---------------------------------------------------------------------------

def run(kg: Union[str, pathlib.Path], roots_file: Union[str, pathlib.Path], out: pathlib.Path,
        user: str | None = None, password: str | None = None) -> None:
    """Shared logic – used by both *main()* and argparse entry."""
    loader = KGLoader(kg, user=user, password=password)
    roots = _read_roots(roots_file)

    extractor = TokenExtractor(loader, roots)
    extractor.dump(out)

    print("✅ Token source tables written to", out)


# ---------------------------------------------------------------------------
# Command‑line interface (optional)
# ---------------------------------------------------------------------------

def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser("constraint‑graph utils")
    p.add_argument("--kg", help="bolt:// uri or directory with nodes.json")
    p.add_argument("--user", help="neo4j user")
    p.add_argument("--password", help="neo4j password")
    p.add_argument("--roots", help="JSON file listing root class xml_tag or ids")
    p.add_argument("--out", type=pathlib.Path, help="output directory for raw tables")
    return p


def main() -> None:  # noqa: D401 – imperative mood
    parser = _build_arg_parser()
    ns, unknown = parser.parse_known_args()

    if len(sys.argv) == 1:  # === No CLI arguments – use defaults ============
        run(
            kg=KG_SOURCE,
            roots_file=ROOTS_PATH,
            out=OUT_DIR,
            user=KG_USER,
            password=KG_PASSWORD,
        )
    else:  # === CLI path =====================================================
        if unknown:
            parser.error("unrecognised arguments: " + " ".join(unknown))
        run(
            kg=ns.kg or KG_SOURCE,
            roots_file=ns.roots or ROOTS_PATH,
            out=ns.out or OUT_DIR,
            user=ns.user or KG_USER,
            password=ns.password or KG_PASSWORD,
        )


# ---------------------------------------------------------------------------
# Backward‑compat: alias for older imports expecting ConstraintLoader
# ---------------------------------------------------------------------------
class ConstraintLoader(KGLoader):
    """Alias so that existing `from loader import ConstraintLoader` keeps working.
    Only `.attr_idx` / `.enum_idx` are used downstream; `.load()` remains to be
    implemented if your old pipeline needs it.
    """

    def load(self):  # pylint: disable=method-hidden
        raise NotImplementedError(
            "Constraint loading is not implemented in the rewritten KGLoader."
        )


if __name__ == "__main__":
    main()
