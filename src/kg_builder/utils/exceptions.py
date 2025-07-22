"""
kg_builder 自定义异常定义
====================================================
所有业务层异常均继承自 KgBuilderError，方便统一捕获
"""

from typing import Any


class KgBuilderError(Exception):
    """基础异常——其他异常的父类。"""

    def __init__(self, message: str, *, payload: Any | None = None) -> None:
        super().__init__(message)
        self.payload = payload


class SchemaValidationError(KgBuilderError):
    """JSON 输入不符合 Schema 规范。"""


class MissingTargetError(KgBuilderError):
    """构图过程中找不到约束对应的目标实体。"""


class VersionConflictError(KgBuilderError):
    """新导入版本与已存在版本冲突。"""


class ExportError(KgBuilderError):
    """图导出失败（Neo4j / RDF 等）。"""
