"""
统一日志封装
====================================================
• 控制台输出 INFO+
• 文件输出 DEBUG+
"""

import logging
import os
from pathlib import Path


def _build_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # ---- 控制台 Handler ----
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(
        logging.Formatter(
            fmt="[%(levelname)s] %(asctime)s | %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logger.addHandler(ch)

    # ---- 文件 Handler ----
    log_dir = Path(os.getenv("KGBUILDER_LOG_DIR", "logs"))
    log_dir.mkdir(exist_ok=True)
    fh = logging.FileHandler(log_dir / "kg_builder_debug.log", encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logger.addHandler(fh)

    logger.debug("Logger 初始化完成")
    return logger


# 外部统一使用 get_logger 获取，避免重复配置
_log_cache: dict[str, logging.Logger] = {}


def get_logger(module_name: str) -> logging.Logger:
    if module_name not in _log_cache:
        _log_cache[module_name] = _build_logger(module_name)
    return _log_cache[module_name]
