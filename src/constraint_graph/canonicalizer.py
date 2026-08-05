"""canonicalizer.py (v1.4) - 进一步改进None值处理和字符清理
--------------------------------
新增功能：
1. 更强健的字符串清理
2. 改进的CID处理
3. 增强的错误处理
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
from typing import Any, Dict, List

import unicodedata

__all__ = ["Canonicalizer"]


_RANGE_RE = re.compile(r"(?P<min>-?\d+)\s*(?:<=|<)\s*([\w\.]+)\s*(?:<=|<)\s*(?P<max>-?\d+)")
_NUM_RE = re.compile(r"-?\d+")
_REGEX_HINT = re.compile(r"\^.*\$")
_MUTEX_HINT = re.compile(r"cannot|not\s+both|not\s+simultaneously", re.I)


class Canonicalizer:
    def canonicalize(self, raw: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """标准化约束 - 确保CID正确传递和溯源信息保持，强化字符串处理"""
        res: List[Dict[str, Any]] = []

        print("🔍 开始约束标准化...")

        for i, c in enumerate(raw):
            try:
                # 🔧 明确CID获取逻辑 - 按优先级顺序
                constraint_cid = c.get("cid")  # 优先使用cid字段
                autosar_id = c.get("autosar_id")  # AUTOSAR完整ID
                neo4j_node_id = c.get("neo4j_node_id")  # Neo4j节点ID

                # 🔧 确定最终CID
                if constraint_cid and str(constraint_cid).strip():
                    final_cid = str(constraint_cid).strip()
                    cid_source = "cid_field"
                elif autosar_id and "/" in str(autosar_id):
                    # 从AUTOSAR ID中提取CID
                    final_cid = str(autosar_id).split("/")[-1]
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

                    # 约束内容 - 🔧 强化字符串清理
                    "type": c.get("constraint_type") or self._infer_type(c),
                    "constraint_type": c.get("constraint_type"),  # 保持原始字段
                    "targets": c.get("targets", []),
                    "targets_data": c.get("targets_data", []),  # 保持完整目标数据
                    "expression": self._clean_string(c.get("expression")),
                    "title": self._clean_string(c.get("title")) or f"Constraint {final_cid}",
                    "value": self._clean_string(c.get("value")),
                    "is_active": c.get("is_active", True),
                    "references": c.get("references", []),
                    "scope_path": c.get("scope_path", []),
                    "id_type": c.get("id_type", ""),
                }

                # 🔧 原有的标准化处理逻辑 - 修复None值处理
                expr = rec["expression"]  # 现在保证不为None
                val = rec["value"]        # 现在保证不为None

                # range处理
                if rec["type"] == "range" or (expr and _RANGE_RE.search(expr)):
                    m = _RANGE_RE.search(expr) if expr else None
                    if m:
                        rec["rangeMin"] = int(m.group("min"))
                        rec["rangeMax"] = int(m.group("max"))
                        rec["inclusive"] = True

                # 🔧 修复：regex处理 - 确保val和expr不为None
                if rec["type"] == "format" or (val and _REGEX_HINT.search(val)) or (expr and _REGEX_HINT.search(expr)):
                    if val:
                        rec["regex"] = val
                    elif expr:
                        rec["regex"] = expr.strip()
                    rec["type"] = "format"

                # existence处理
                if rec["type"] == "existence":
                    low = expr.lower() if expr else ""
                    rec["mustNotExist"] = any(k in low for k in ["shall not exist", "must not be present", "禁止出现"])
                    rec["mustExist"] = not rec["mustNotExist"]

                # 🔧 修复：mutuallyExclusive处理 - 确保expr不为None
                if rec["type"] == "relationship" and expr and _MUTEX_HINT.search(expr):
                    attrs = re.findall(r"[A-Z][A-Za-z0-9_\.]+", expr)
                    rec["mutuallyExclusive"] = attrs

                # 🔧 修复：implies处理 - 确保expr不为None
                if rec["type"] == "behavioral" and expr and "if" in expr.lower() and "then" in expr.lower():
                    parts = expr.lower().split("then", 1)
                    if len(parts) == 2:
                        pre, post = parts
                        pre = pre.replace("if", "").strip()
                        rec["implies"] = {
                            "if": pre,
                            "then": post.strip(),
                        }

                # cardinality处理
                if rec["type"] == "cardinality":
                    nums = _NUM_RE.findall(expr) if expr else []
                    if nums:
                        # 🔧 修复：确保基数值始终是整数
                        try:
                            max_val = int(nums[-1])
                            rec["maxOccurs"] = max_val
                            rec["minOccurs"] = 0
                        except (ValueError, IndexError):
                            # 如果解析失败，使用默认值
                            rec["maxOccurs"] = -1  # 无限制
                            rec["minOccurs"] = 0
                    else:
                        # 没有找到数字，使用默认值
                        rec["maxOccurs"] = -1
                        rec["minOccurs"] = 0

                # 🔧 新增：统一处理所有可能的基数字段，确保类型安全
                for occurs_field in ["minOccurs", "maxOccurs", "rangeMin", "rangeMax"]:
                    if occurs_field in rec:
                        rec[occurs_field] = self._ensure_integer(rec[occurs_field])

                # 🔧 修复：value_restriction处理 - 确保val不为None
                if rec["type"] == "value_restriction":
                    if val:
                        splitter = re.compile(r"[，,、;；\s]+")
                        values = [v for v in splitter.split(val) if v]
                        # 🔧 清理枚举值
                        rec["enum"] = [self._clean_enum_value(v) for v in values if self._clean_enum_value(v)]
                    if not rec.get("enum") and expr:
                        rec["enum"] = self._parse_enum_from_expression(expr)

                # 🔧 基于原始CID生成一致的hash
                rec["hash"] = self._hash_from_original(final_cid, rec)
                res.append(rec)

            except Exception as e:
                print(f"⚠️  处理约束 {i} 时出错: {e}")
                # 创建最小的错误记录
                error_rec = {
                    "cid": f"ERROR_{i}",
                    "original_cid": f"ERROR_{i}",
                    "type": "error",
                    "expression": f"Processing error: {str(e)}",
                    "title": f"Error Constraint {i}",
                    "value": "",
                    "is_active": False,
                    "targets": [],
                    "hash": self._hash_from_original(f"ERROR_{i}", {"error": str(e)})
                }
                res.append(error_rec)
                continue

        print(f"📊 标准化完成: {len(res)} 个约束")

        # 🔧 验证CID唯一性
        cids = [r["cid"] for r in res]
        duplicate_cids = [cid for cid in set(cids) if cids.count(cid) > 1]
        if duplicate_cids:
            print(f"⚠️  发现重复CID: {duplicate_cids}")

        return res

    def _clean_string(self, text: Any) -> str:
        """🔧 新增：统一的字符串清理方法"""
        if text is None:
            return ""

        if isinstance(text, bytes):
            try:
                text = text.decode('utf-8', errors='replace')
            except Exception:
                text = str(text)

        text = str(text)

        # 移除控制字符
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)

        # 处理Unicode字符
        try:
            text = unicodedata.normalize('NFKD', text)
        except Exception:
            pass

        # 替换特殊字符
        replacements = {
            '•': 'bullet',
            '→': 'arrow',
            '←': 'left_arrow',
            '…': '...',
            '–': '-',
            '—': '-',
            '"': '"',
            '"': '"',
            ''': "'",
            ''': "'",
        }

        for old_char, new_char in replacements.items():
            text = text.replace(old_char, new_char)

        # 标准化空白字符
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def _clean_enum_value(self, value: str) -> str:
        """🔧 新增：清理枚举值"""
        if not value:
            return ""

        cleaned = self._clean_string(value)

        # 移除引号和多余的空白
        cleaned = cleaned.strip('"\'').strip()

        # 确保不为空且不只是特殊字符
        if not cleaned or len(cleaned.strip()) == 0:
            return ""

        # 限制长度
        if len(cleaned) > 50:
            cleaned = cleaned[:47] + "..."

        return cleaned

    def _hash_from_original(self, original_cid: str, record: Dict[str, Any]) -> str:
        """基于原始CID生成一致的hash，便于溯源"""
        if original_cid:
            # 使用原始CID作为基础，确保一致性
            base_string = f"{original_cid}_{record.get('type', 'unknown')}"
            return hashlib.md5(base_string.encode('utf-8')).hexdigest()[:12]
        else:
            # 后备：使用原有逻辑
            return self._hash(record)

    def _ensure_integer(self, value: Any) -> int:
        """确保值为整数类型"""
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0

    # ------------------------------------------------------------
    def _infer_type(self, c: Dict[str, Any]) -> str:
        """推断约束类型 - 修复None值处理"""
        t = c.get("constraint_type")
        if t:
            return t

        # 🔧 修复：确保expr不为None
        expr = self._clean_string(c.get("expression"))
        expr_lower = expr.lower()

        if _RANGE_RE.search(expr):
            return "range"
        if "shall be one of" in expr_lower or "single value" in expr_lower:
            return "value_restriction"
        if _REGEX_HINT.search(expr):
            return "format"
        if "shall exist" in expr_lower or "必须存在" in expr_lower:
            return "existence"
        if "cannot" in expr_lower and "simultaneously" in expr_lower:
            return "relationship"
        if "if" in expr_lower and "then" in expr_lower:
            return "behavioral"
        return "other"

    # ------------------------------------------------------------
    def _hash(self, record: Dict[str, Any]) -> str:
        """生成记录hash"""
        try:
            blob = json.dumps(record, sort_keys=True, default=str, ensure_ascii=True).encode('utf-8')
            return hashlib.md5(blob).hexdigest()[:12]
        except Exception as e:
            # 后备hash方法
            fallback_string = f"{record.get('cid', 'unknown')}_{record.get('type', 'unknown')}"
            return hashlib.md5(fallback_string.encode('utf-8')).hexdigest()[:12]

    @staticmethod
    def _parse_enum_from_expression(expr: str) -> List[str]:
        """从表达式中提取枚举值 - 改进版"""
        if not expr:  # 🔧 修复：处理None或空字符串
            return []

        # 清理表达式
        expr = Canonicalizer()._clean_string(expr)

        # 查找 "one of A|B|C" 或 "one of A, B, C" 模式
        patterns = [
            r"one of ([A-Za-z0-9_,\s|]+)",
            r"shall be one of ([A-Za-z0-9_,\s|]+)",
            r"must be one of ([A-Za-z0-9_,\s|]+)",
        ]

        for pattern in patterns:
            m = re.search(pattern, expr, re.IGNORECASE)
            if m:
                enum_str = m.group(1)
                # 分割枚举值（支持逗号、空格、竖线分隔）
                values = re.split(r'[,\s|]+', enum_str)
                cleaned_values = []
                for v in values:
                    cleaned = Canonicalizer()._clean_enum_value(v.strip())
                    if cleaned:
                        cleaned_values.append(cleaned)
                return cleaned_values

        return []

    @staticmethod
    def run(raw_path: str | pathlib.Path,
            out_path: str | pathlib.Path) -> pathlib.Path:
        """运行标准化"""
        raw_path, out_path = map(pathlib.Path, (raw_path, out_path))

        try:
            # 读取原始数据
            raw_text = raw_path.read_text(encoding="utf-8")
            raw = []

            for line_num, line in enumerate(raw_text.splitlines(), 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    raw.append(data)
                except json.JSONDecodeError as e:
                    print(f"⚠️  跳过第{line_num}行，JSON解析错误: {e}")
                    continue

            print(f"📋 成功读取 {len(raw)} 条原始约束")

            # 执行标准化
            canonical = Canonicalizer().canonicalize(raw)

            # 写入结果
            result_json = json.dumps(canonical, ensure_ascii=False, indent=2)
            out_path.write_text(result_json, encoding="utf-8")

            print(f"✅ 标准化结果已��存到: {out_path}")
            return out_path

        except Exception as e:
            print(f"❌ 标准化过程失败: {e}")
            raise

