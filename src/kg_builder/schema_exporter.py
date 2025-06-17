"""
Guided Decoding Grammar 导出器
====================================================
• 将目标类相关约束集合导出为
  1) GBNF —— vLLM `guided_grammar`
  2) JSON-Schema —— GPT-4o JSON-mode
• 简化策略：仅导出 minOccurs/maxOccurs 与枚举值
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from utils.logger import get_logger

logger = get_logger(__name__)


class GbnfMaker:
    """生成 GBNF 字符串"""

    def build(self, constraints: List[Dict[str, Any]]) -> str:
        rules: List[str] = ["root ::= <ARXML>"]
        for c in constraints:
            if c.get("constraint_type") == "value_restriction" and c.get("targets"):
                t = c["targets"][0]
                if t["entityType"] == "enum":
                    enum_name = t["targetEntityName"]
                    literals = "|".join(t["targetAttributes"])
                    rules.append(f"<{enum_name}> ::= {literals}")
        gbnf = "\n".join(rules)
        logger.info("GBNF 生成完成，%d 条规则", len(rules))
        return gbnf


class JsonSchemaMaker:
    """生成 JSON-Schema 字符串（供 GPT-4o JSON-mode）"""

    def build(self, constraints: List[Dict[str, Any]]) -> str:
        schema: Dict[str, Any] = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {},
            "required": [],
        }

        for c in constraints:
            if not c["targets"]:
                continue
            t = c["targets"][0]
            attr_list = t["targetAttributes"]
            # 仅处理单属性场景
            if len(attr_list) != 1 or attr_list[0].startswith("_"):
                continue
            attr = attr_list[0]

            prop = schema["properties"].setdefault(attr, {"type": "string"})
            if c["constraint_type"] == "value_restriction":
                prop["enum"] = [c["value"]]
            if c["constraint_type"] == "format":
                prop["pattern"] = c["value"]
            if c["constraint_type"] == "cardinality" and c["value"] == "1":
                schema["required"].append(attr)

        import json

        js = json.dumps(schema, ensure_ascii=False, indent=2)
        logger.info("JSON-Schema 生成完成，字段 %d 个", len(schema["properties"]))
        return js
