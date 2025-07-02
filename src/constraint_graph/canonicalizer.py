"""canonicalizer.py (v1.2)
--------------------------------
Support extra constraint families: range / regex / existence / mutuallyExclusive / implies.
标准字段：
- rangeMin / rangeMax / inclusive
- regex
- mustExist (bool) / mustNotExist (bool)
- mutuallyExclusive (list[str])
- implies: {ifTarget, ifValue, thenTarget, thenValue}
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Dict, List
import pathlib

__all__ = ["Canonicalizer"]


_RANGE_RE = re.compile(r"(?P<min>-?\d+)\s*(?:<=|<)\s*([\w\.]+)\s*(?:<=|<)\s*(?P<max>-?\d+)")
_NUM_RE = re.compile(r"-?\d+")
_REGEX_HINT = re.compile(r"\^.*\$")
_MUTEX_HINT = re.compile(r"cannot|not\s+both|not\s+simultaneously", re.I)


class Canonicalizer:
    def canonicalize(self, raw: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """标准化约束 - 确保CID正确传递和溯源信息保持"""
        res: List[Dict[str, Any]] = []

        print("🔍 开始约束标准化...")

        for i, c in enumerate(raw):
            # 🔧 明确CID获取逻辑 - 按优先级顺序
            constraint_cid = c.get("cid")  # 优先使用cid字段
            autosar_id = c.get("autosar_id")  # AUTOSAR完整ID
            neo4j_node_id = c.get("neo4j_node_id")  # Neo4j节点ID

            # 🔧 确定最终CID
            if constraint_cid and constraint_cid.strip():
                final_cid = constraint_cid.strip()
                cid_source = "cid_field"
            elif autosar_id and "/" in autosar_id:
                # 从AUTOSAR ID中提取CID
                final_cid = autosar_id.split("/")[-1]
                cid_source = "extracted_from_autosar_id"
                print(f"📋 从AUTOSAR ID提取CID: {autosar_id} → {final_cid}")
            elif neo4j_node_id:
                # 使用Neo4j节点ID作为后备
                final_cid = f"NEO4J_{neo4j_node_id}"
                cid_source = "neo4j_fallback"
                print(f"⚠️  使用Neo4j节点ID作为CID: {final_cid}")
            else:
                # 最后后备：使用索引
                final_cid = f"UNKNOWN_{i}"
                cid_source = "index_fallback"
                print(f"❌ 无法确定CID，使用索引: {final_cid}")

            # 🔧 构建标准化记录，保持溯源信息
            rec: Dict[str, Any] = {
                # CID相关字段
                "cid": final_cid,
                "original_cid": final_cid,
                "cid_source": cid_source,

                # 溯源字段
                "autosar_id": autosar_id,
                "neo4j_node_id": neo4j_node_id,
                "kg_source": c.get("kg_source", False),

                # 约束内容
                "type": c.get("constraint_type") or self._infer_type(c),
                "constraint_type": c.get("constraint_type"),  # 保持原始字段
                "targets": c.get("targets", []),
                "targets_data": c.get("targets_data", []),  # 保持完整目标数据
                "expression": c.get("expression", ""),
                "title": c.get("title", f"Constraint {final_cid}"),
                "value": c.get("value", ""),
                "is_active": c.get("is_active", True),
                "references": c.get("references", []),
                "scope_path": c.get("scope_path", []),
                "id_type": c.get("id_type", ""),
            }

            # 🔧 原有的标准化处理逻辑
            expr = rec["expression"]
            val = rec["value"]

            # range处理
            if rec["type"] == "range" or _RANGE_RE.search(expr):
                m = _RANGE_RE.search(expr)
                if m:
                    rec["rangeMin"] = int(m.group("min"))
                    rec["rangeMax"] = int(m.group("max"))
                    rec["inclusive"] = True

            # regex处理
            if rec["type"] == "format" or _REGEX_HINT.search(val) or _REGEX_HINT.search(expr):
                rec["regex"] = val or expr.strip()
                rec["type"] = "format"

            # existence处理
            if rec["type"] == "existence":
                low = expr.lower()
                rec["mustNotExist"] = any(k in low for k in ["shall not exist", "must not be present", "禁止出现"])
                rec["mustExist"] = not rec["mustNotExist"]

            # mutuallyExclusive处理
            if rec["type"] == "relationship" and _MUTEX_HINT.search(expr):
                attrs = re.findall(r"[A-Z][A-Za-z0-9_\.]+", expr)
                rec["mutuallyExclusive"] = attrs

            # implies处理
            if rec["type"] == "behavioral" and "if" in expr.lower() and "then" in expr.lower():
                pre, post = expr.lower().split("then", 1)
                pre = pre.replace("if", "").strip()
                rec["implies"] = {
                    "if": pre,
                    "then": post.strip(),
                }

            # cardinality处理
            if rec["type"] == "cardinality":
                nums = _NUM_RE.findall(expr)
                if nums:
                    rec["maxOccurs"] = int(nums[-1])
                    rec["minOccurs"] = 0

            # value_restriction处理
            if rec["type"] == "value_restriction":
                if val:
                    splitter = re.compile(r"[，,、;；\s]+")
                    rec["enum"] = [v for v in splitter.split(val) if v]
                if not rec.get("enum") and expr:
                    rec["enum"] = self._parse_enum_from_expression(expr)

            # 🔧 基于原始CID生成一致的hash
            rec["hash"] = self._hash_from_original(final_cid, rec)
            res.append(rec)

        print(f"📊 标准化完成: {len(res)} 个约束")

        # 🔧 验证CID唯一性
        cids = [r["cid"] for r in res]
        duplicate_cids = [cid for cid in set(cids) if cids.count(cid) > 1]
        if duplicate_cids:
            print(f"⚠️  发现重复CID: {duplicate_cids}")

        return res

    def _hash_from_original(self, original_cid: str, record: Dict[str, Any]) -> str:
        """基于原始CID生成一致的hash，便于溯源"""
        if original_cid:
            # 使用原始CID作为基础，确保一致性
            import hashlib
            base_string = f"{original_cid}_{record.get('type', 'unknown')}"
            return hashlib.md5(base_string.encode()).hexdigest()[:12]
        else:
            # 后备：使用原有逻辑
            return self._hash(record)

    # ------------------------------------------------------------
    def _infer_type(self, c: Dict[str, Any]) -> str:
        t = c.get("constraint_type")
        if t:
            return t
        expr = c.get("expression", "").lower()
        if _RANGE_RE.search(expr):
            return "range"
        if "shall be one of" in expr or "single value" in expr:
            return "value_restriction"
        if _REGEX_HINT.search(expr):
            return "format"
        if "shall exist" in expr or "必须存在" in expr:
            return "existence"
        if "cannot" in expr and "simultaneously" in expr:
            return "relationship"
        if "if" in expr and "then" in expr:
            return "behavioral"
        return "other"

    # ------------------------------------------------------------
    def _hash(self, record: Dict[str, Any]) -> str:
        blob = json.dumps(record, sort_keys=True, default=str).encode()
        return hashlib.md5(blob).hexdigest()[:12]

    @ staticmethod
    def _parse_enum_from_expression(expr: str) -> List[str]:
        """Very naïve extraction of 'one of A|B|C' style lists."""
        m = re.search(r"one of ([A-Za-z0-9_,\s]+)", expr)
        if m:
            return [x.strip() for x in re.split(r"[,\s]+", m.group(1)) if x.strip()]
        return []

    @staticmethod
    def run(raw_path: str | pathlib.Path,
            out_path: str | pathlib.Path) -> pathlib.Path:
        raw_path, out_path = map(pathlib.Path, (raw_path, out_path))
        raw = [json.loads(l) for l in raw_path.read_text(encoding="utf-8").splitlines() if l.strip()]
        canonical = Canonicalizer().canonicalize(raw)
        out_path.write_text(json.dumps(canonical, ensure_ascii=False, indent=2), encoding="utf-8")
        return out_path
