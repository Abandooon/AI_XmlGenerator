# src/utils/logger.py
import logging
import sys
from pathlib import Path


def get_logger(name: str) -> logging.Logger:
    """获取配置好的logger"""
    logger = logging.getLogger(name)

    if not logger.handlers:
        # 设置日志级别
        logger.setLevel(logging.INFO)

        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        # 文件处理器
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(log_dir / "system.log", encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)

        # 格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        # 添加处理器
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger