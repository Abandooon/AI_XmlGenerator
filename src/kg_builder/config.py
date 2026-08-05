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
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

from utils.logger import get_logger

logger = get_logger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

# ----------------------------------------------------------------------
# 默认配置：所有运行所需关键路径都给出占位值，开箱即跑
# ----------------------------------------------------------------------
_DEFAULT_CFG: dict[str, Any] = {
    # 图后端
    "graph_backend": "neo4j",
    "neo4j": {
        "uri": "neo4j://127.0.0.1:7687",
        "user": "neo4j",
        "password": "",
    },
    # 输入数据
    # "metadata_path": "data/unified_metadata.json",
    "metadata_path": "data/unified_metadata_with_inlines.json",
    "constraints_path": "data/constraints_linked.json",
    # 域与版本
    "domain": "AUTOSAR",
    "version": "4-2-2",
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
    cfg: dict[str, Any] = deepcopy(_DEFAULT_CFG)

    # ---------- YAML ----------
    if cfg_path and Path(cfg_path).exists():
        path = Path(cfg_path)
        logger.info("加载配置文件: %s", path.resolve())
        cfg |= yaml.safe_load(path.read_text(encoding="utf-8"))

    # ---------- 环境变量 ----------
    neo4j_cfg = cfg.setdefault("neo4j", {})
    env_uri = os.getenv("NEO4J_URI")
    env_user = os.getenv("NEO4J_USER")
    env_password = os.getenv("NEO4J_PASSWORD") or os.getenv("NEO4J_PWD")
    if env_uri:
        neo4j_cfg["uri"] = env_uri
    if env_user:
        neo4j_cfg["user"] = env_user
    if env_password:
        neo4j_cfg["password"] = env_password

    if cfg.get("graph_backend") == "neo4j" and not neo4j_cfg.get("password"):
        raise ValueError(
            "Neo4j password is not configured. Set NEO4J_PASSWORD in the project .env file."
        )

    # ---------- 导出路径拼接 ----------
    odir = Path(cfg["output_dir"])
    cfg["export"] = {
        "shacl": str(odir / "shapes.ttl"),
        "smt": str(odir / "constraints.smt2"),
        "gbnf": str(odir / "autosar.gbnf"),
    }

    safe_cfg = deepcopy(cfg)
    if safe_cfg.get("neo4j", {}).get("password"):
        safe_cfg["neo4j"]["password"] = "<redacted>"
    logger.debug("Loaded configuration: %s", safe_cfg)
    return KgConfig(cfg)
