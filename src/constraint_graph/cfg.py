# cfg.py  ── 单一职责：提供全局 BUILD_CFG -------------------------------
import pathlib, tomllib, argparse, sys
from typing import Any

def _load_build_cfg(path: str | None = None) -> dict[str, Any]:
    """按优先级查找并解析 build.toml。"""
    candidates = (
        [pathlib.Path(path)] if path else []
    ) + [pathlib.Path.cwd() / "build.toml",
         pathlib.Path(__file__).with_name("build.toml")]
    for fp in candidates:
        if fp.is_file():
            with fp.open("rb") as f:
                return tomllib.load(f)
    return {}

BUILD_CFG: dict[str, Any] = _load_build_cfg()
