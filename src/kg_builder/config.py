"""
配置读取模块
====================================================
优先级（高 → 低）：
1. CLI --cfg 指定 YAML
2. YAML 中的键
3. 环境变量覆盖（NEO4J_PWD）
4. 内置 _DEFAULT_CFG
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from utils.logger import get_logger

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# 默认配置：所有运行所需关键路径都给出占位值，开箱即跑
# ----------------------------------------------------------------------
_DEFAULT_CFG: dict[str, Any] = {
    # 图后端
    "graph_backend": "neo4j",
    "neo4j": {
        "uri": "neo4j://127.0.0.1:7687",
        "user": "neo4j",
        "password": "autosar4.2.2"
    },
    # 输入数据
    # "metadata_path": "data/unified_metadata.json",
    "metadata_path": "data/unified_metadata_with_inlines.json",
    "constraints_path": "data/constraints_linked.json",
    # 域与版本
    "domain": "AUTOSAR",
    "version": "UNSPECIFIED",
    # 统一导出目录
    "output_dir": "output",
}

# ----------------------------------------------------------------------
class KgConfig(dict):
    """支持点号访问的 dict，如 cfg.neo4j"""

    def __getattr__(self, item: str):  # type: ignore[override]  # pragma: no cover
        try:
            return self[item]
        except KeyError as exc:
            raise AttributeError(item) from exc


def load_config(cfg_path: str | Path | None) -> KgConfig:
    """
    合并优先级：
        内置默认 < YAML 文件 < 环境变量
    并根据 output_dir 自动拼接 export 路径
    """
    cfg: dict[str, Any] = _DEFAULT_CFG.copy()

    # ---------- YAML ----------
    if cfg_path and Path(cfg_path).exists():
        path = Path(cfg_path)
        logger.info("加载配置文件: %s", path.resolve())
        cfg |= yaml.safe_load(path.read_text(encoding="utf-8"))

    # ---------- 环境变量 ----------
    neo_pwd = os.getenv("NEO4J_PWD")
    if neo_pwd:
        cfg.setdefault("neo4j", {})["password"] = neo_pwd

    # ---------- 导出路径拼接 ----------
    odir = Path(cfg["output_dir"])
    cfg["export"] = {
        "shacl": str(odir / "shapes.ttl"),
        "smt": str(odir / "constraints.smt2"),
        "gbnf": str(odir / "autosar.gbnf"),
    }

    logger.debug("最终配置合并结果: %s", cfg)
    return KgConfig(cfg)
