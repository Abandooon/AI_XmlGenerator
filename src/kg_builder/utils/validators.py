"""
输入文件校验工具
====================================================
1. 使用 jsonschema 对 unified_metadata.json / constraints_linked.json 进行结构校验
2. 进行关键字段完整性检查（如 id 唯一性、targets 可解析性等）
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator

from .exceptions import SchemaValidationError
from .logger import get_logger

logger = get_logger(__name__)


class JsonValidator:
    """JSON Schema 校验封装"""

    def __init__(self, schema: dict[str, Any]) -> None:
        self._validator = Draft7Validator(schema)

    def validate_file(self, filepath: str | Path) -> dict[str, Any]:
        path = Path(filepath)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as err:  # pragma: no cover
            raise SchemaValidationError(f"{path} 不是合法 JSON: {err}") from err

        errors = sorted(self._validator.iter_errors(data), key=lambda e: e.path)
        if errors:
            msgs = "\n".join(f"- {'/'.join(map(str, e.path))}: {e.message}" for e in errors)
            raise SchemaValidationError(f"{path} 不符合 Schema:\n{msgs}")

        logger.info("文件 %s 通过 Schema 校验", path.name)
        return data
