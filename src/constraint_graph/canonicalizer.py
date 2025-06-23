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
        res: List[Dict[str, Any]] = []
        for c in raw:
            rec: Dict[str, Any] = {
                "cid": c.get("id") or c.get("cid"),
                "type": c.get("constraint_type") or self._infer_type(c),
                "targets": c.get("targets", []),
            }

            expr = c.get("expression", "")
            val = (c.get("value") or "").strip()

            # ---------------- range ----------------
            if rec["type"] == "range" or _RANGE_RE.search(expr):
                m = _RANGE_RE.search(expr)
                if m:
                    rec["rangeMin"] = int(m.group("min"))
                    rec["rangeMax"] = int(m.group("max"))
                    rec["inclusive"] = True
            # ---------------- regex ----------------
            if rec["type"] == "format" or _REGEX_HINT.search(val) or _REGEX_HINT.search(expr):
                rec["regex"] = val or expr.strip()
                rec["type"] = "format"
            # ---------------- existence ----------------
            if rec["type"] == "existence":
                low = expr.lower()
                rec["mustNotExist"] = any(k in low for k in ["shall not exist", "must not be present", "禁止出现"])
                rec["mustExist"] = not rec["mustNotExist"]
            # ---------------- mutuallyExclusive ----------------
            if rec["type"] == "relationship" and _MUTEX_HINT.search(expr):
                attrs = re.findall(r"[A-Z][A-Za-z0-9_\.]+", expr)
                rec["mutuallyExclusive"] = attrs
            # ---------------- implies ----------------
            if rec["type"] == "behavioral" and "if" in expr.lower() and "then" in expr.lower():
                # naive split
                pre, post = expr.lower().split("then", 1)
                pre = pre.replace("if", "").strip()
                rec["implies"] = {
                    "if": pre,
                    "then": post.strip(),
                }
            # ---------------- cardinality / enum existing ----------------
            if rec["type"] == "cardinality":
                nums = _NUM_RE.findall(expr)
                if nums:
                    rec["maxOccurs"] = int(nums[-1])
                    rec["minOccurs"] = 0
            if rec["type"] == "value_restriction":
                if val:
                    splitter = re.compile(r"[，,、;；\s]+")
                    rec["enum"] = [v for v in splitter.split(val) if v]
                # 如果仍为空，再尝试从 expression 推断
                if not rec.get("enum") and expr:
                    rec["enum"] = self._parse_enum_from_expression(expr)

            rec["hash"] = self._hash(rec)
            res.append(rec)
        return res

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
