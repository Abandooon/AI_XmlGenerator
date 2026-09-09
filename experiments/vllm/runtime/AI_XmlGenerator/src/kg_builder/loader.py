"""
JSON 输入加载器
====================================================
• 负责把 unified_metadata.json 与 constraints_linked.json
  解析为 Python dict，并做基础字段预处理
• 依赖 utils.validators.JsonValidator 进行 Schema 校验-------没有校验依然正常解析json文件
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from utils.exceptions import SchemaValidationError
from utils.logger import get_logger
from utils.validators import JsonValidator

logger = get_logger(__name__)


class MetadataLoader:
    """加载 unified_metadata.json"""

    # Schema 通常存放在 `schemas/` 目录；这里简化写死
    _SCHEMA_PATH = Path(__file__).with_suffix("").parent.parent / "schemas" / "unified_metadata.schema.json"

    def __init__(self) -> None:
        if self._SCHEMA_PATH.exists():
            self._validator = JsonValidator(
                schema=self._SCHEMA_PATH.read_text(encoding="utf-8")  # type: ignore[arg-type]
            )
        else:  # pragma: no cover
            # 若未提供 schema 文件，仅做浅检查
            self._validator = None

    def load(self, json_path: str | Path) -> dict[str, Any]:
        logger.info("加载元模型文件: %s", json_path)
        if self._validator:  # 完整 Schema 校验
            try:
                data = self._validator.validate_file(json_path)
            except SchemaValidationError:
                logger.warning("未通过完整 Schema，尝试轻量解析")
                data = self._light_load(json_path)
        else:
            data = self._light_load(json_path)

        # 轻量预处理：把 None → 空字符串，方便后续判断
        self._clean_nulls(data)
        return data

    @staticmethod
    def _light_load(json_path: str | Path) -> dict[str, Any]:
        import json

        return json.loads(Path(json_path).read_text(encoding="utf-8"))

    @staticmethod
    def _clean_nulls(data: dict[str, Any]) -> None:
        """原地把 null 字段替换成 '' (仅一层)"""
        for topk in ("groups", "complexTypes", "simpleTypes"):
            sub = data.get(topk)
            if not isinstance(sub, dict):
                continue
            for val in sub.values():
                for k, v in list(val.items()):
                    if v is None:
                        val[k] = ""


class ConstraintLoader:
    """加载 constraints_linked.json"""

    _SCHEMA_PATH = Path(__file__).with_suffix("").parent.parent / "schemas" / "constraints_linked.schema.json"

    def __init__(self) -> None:
        if self._SCHEMA_PATH.exists():
            self._validator = JsonValidator(
                schema=self._SCHEMA_PATH.read_text(encoding="utf-8")  # type: ignore[arg-type]
            )
        else:
            self._validator = None

    def load(self, json_path: str | Path) -> list[dict[str, Any]]:
        logger.info("加载约束文件: %s", json_path)
        if self._validator:
            data = self._validator.validate_file(json_path)
        else:
            data = MetadataLoader._light_load(json_path)

        # ★ 兼容两种格式：对象 or 直接数组
        if isinstance(data, list):
            return data
        if "extracted_constraints" in data:
            return data["extracted_constraints"]

        raise SchemaValidationError(
            f"{json_path} 格式错误：既不是数组，也不含 'extracted_constraints' 键"
        )

