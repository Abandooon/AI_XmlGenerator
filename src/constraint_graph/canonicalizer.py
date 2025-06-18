"""canonicalizer.py
------------------
Transform raw constraint dicts into canonical JSON records used by all exporters.
Fills default fields and computes stable hash so downstream can detect changes.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Dict, List


class Canonicalizer:
    _NUM_RE = re.compile(r"(?P<num>\d+)")

    def canonicalize(self, raw: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        res = []
        for c in raw:
            typ = c.get("constraint_type") or self._infer_type(c.get("title", ""))
            targets = c.get("targets", [])
            value = c.get("value", "")
            min_oc, max_oc = self._infer_occurs(c)
            record: Dict[str, Any] = {
                "cid": c.get("id"),
                "type": typ,
                "targets": targets,
                "minOccurs": min_oc,
                "maxOccurs": max_oc,
                "enum": [v.strip() for v in value.split(",") if v.strip()],
            }
            record["hash"] = self._hash(record)
            res.append(record)
        return res

    # ------------------------------------------------------------
    def _infer_type(self, text: str) -> str:
        text_l = text.lower()
        if "at most" in text_l or "max" in text_l:
            return "cardinality"
        if "shall be one of" in text_l or "include a single value" in text_l:
            return "value_restriction"
        return "unknown"

    def _infer_occurs(self, c: Dict[str, Any]) -> tuple[int | None, int | None]:
        if c.get("constraint_type") == "cardinality":
            # simple heuristic: look for numbers in expression
            nums = self._NUM_RE.findall(c.get("expression", ""))
            if nums:
                return (0, int(nums[-1]))
            if "single" in c.get("expression", "").lower():
                return (0, 1)
        return (None, None)

    def _hash(self, record: Dict[str, Any]) -> str:
        blob = json.dumps(record, sort_keys=True).encode()
        return hashlib.md5(blob).hexdigest()[:12]
