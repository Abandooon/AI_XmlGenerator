# token_extractor.py
"""Extract flattened JSONL tables containing everything needed to build the
terminal‑token map (structure labels, attribute names, enum literals, etc.).

Designed to work on top of :pymod:`loader.KGLoader`.
"""
from __future__ import annotations

import json
import pathlib
import re
from collections import deque, defaultdict
from typing import Dict, Iterable, List, Set

from loader import KGLoader

__all__ = ["TokenExtractor"]


class TokenExtractor:
    """Walk the KG once and spit out 3–4 JSONL files.

    Parameters
    ----------
    loader : KGLoader
        A fully initialised loader providing node / edge indices.
    roots : list[str | int]
        *Either* a list of class **xml_tag** strings *or* explicit class IDs.
    """
    @classmethod
    def from_connection(
        cls,
        host: str,
        user: str | None,
        password: str | None,
        *,
        roots: List[str | int] | None = None,
    ) -> "TokenExtractor":
        """根据明确的连接参数返回实例。"""
        kg = KGLoader(host, user, password)
        if roots is None:
            if roots is None:
                raise ValueError(
                    "roots must be provided (either --roots FILE or roots.json); "
                    "auto-discovery has been disabled by design."
                )
        return cls(kg, roots)

    @classmethod
    def from_kg(cls, kg_url: str, roots: List[str | int] | None = None) -> "TokenExtractor":
        """一行完成：连接 Neo4j → 构建 **KGLoader** → 创建 TokenExtractor。

        参数
        ----
        kg_url : str
            Neo4j Bolt/neo4j 协议连接串，例如：
            ``bolt://neo4j:autosar4.2.2@127.0.0.1:7687``
        roots : list[str | int] | None
            根类 xml_tag 或节点 ID；若为 ``None`` 表示自动发现所有
            **没有任何 SUBCLASS_OF 入边** 的类，作为 XML 顶层根。
        """
        # 1) 创建 KGLoader（你的 Loader 类名是 KGLoader）
        kg = KGLoader(kg_url)
        if roots is None:
            raise ValueError(
                "roots must be provided (either --roots FILE or roots.json); "
                "auto-discovery has been disabled by design."
            )
        return cls(kg, roots)

    # ------------------------------------------------------------------
    def __init__(self, loader: KGLoader, roots: List[str | int]):
        self._kg = loader
        self.root_ids: List[int] = self._normalise_roots(roots)

        # Memoised results
        self._serialisable: Set[int] | None = None
        self._attr_cache: Dict[int, List[int]] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def serialisable_classes(self) -> Set[int]:
        """Compute – lazily – the set of Classes that *will* appear as XML tags."""
        if self._serialisable is not None:
            return self._serialisable

        kg = self._kg
        reachable: Set[int] = set()
        q: deque[int] = deque(self.root_ids)
        while q:
            cid = q.popleft()
            if cid in reachable:
                continue
            reachable.add(cid)

            # -------- 用聚合函数 --------------
            for aid in self.aggregate_attributes(cid):
                meta = kg.attr_nodes[aid]
                if not meta["isXmlAttr"]:
                    tid = kg.attr_type.get(aid)
                    if (
                        tid
                        and tid in kg.cls_nodes
                        and not kg.cls_nodes[tid].get("isAttribute", False)
                    ):
                        q.append(tid)
        self._serialisable = reachable
        return reachable

    # ------------------------------------------------------------------
    def aggregate_attributes(self, cls_id: int) -> List[int]:
        """Return list of Attribute IDs visible on *cls_id* after considering
        inheritance & inline‑expands.
        """
        if cls_id in self._attr_cache:
            return self._attr_cache[cls_id]

        kg = self._kg
        seen: Dict[str, int] = {}  # xml_tag → attrId (pick-first wins)

        # 1) self + SUBCLASS_OF chain (child overrides parent)
        todo: List[int] = [cls_id]
        while todo:
            cur = todo.pop()
            for aid in kg.cls_attrs.get(cur, []):
                tag = kg.attr_nodes[aid]["xml_tag"]
                if tag not in seen:
                    seen[tag] = aid
            todo.extend(kg.subcls.get(cur, []))

        # 2) INLINE_EXPANDS (no override – only fill gaps)
        dq: deque[int] = deque(kg.inline.get(cls_id, []))
        while dq:
            ex = dq.popleft()
            for aid in kg.cls_attrs.get(ex, []):
                tag = kg.attr_nodes[aid]["xml_tag"]
                if tag not in seen:
                    seen[tag] = aid
            dq.extend(kg.inline.get(ex, []))

        out = list(seen.values())
        self._attr_cache[cls_id] = out
        return out

    # ------------------------------------------------------------------
    def dump(self, out_dir: pathlib.Path | str) -> None:
        """Write ``raw_classes.jsonl``, ``raw_attributes.jsonl``, ``raw_enums.jsonl``
        (and ``meta_roots.json``) into *out_dir*.
        """
        out_path = pathlib.Path(out_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        kg = self._kg
        serial = self.serialisable_classes()
        restrictions = self._collect_value_restrictions()

        # 1) classes ------------------------------------------------------
        cls_fp = out_path / "raw_classes.jsonl"
        with cls_fp.open("w", encoding="utf-8") as f:
            for cid in sorted(serial):
                meta = kg.cls_nodes[cid]
                f.write(json.dumps({
                    "classId": cid,
                    "className": meta["name"],
                    "xml_tag": meta["xml_tag"],
                    "xml_wrapper_tag": meta["wrapper"],
                }, ensure_ascii=False) + "\n")

        # 2) attributes ----------------------------------------------------
        attrs_fp = out_path / "raw_attributes.jsonl"
        with attrs_fp.open("w", encoding="utf-8") as f_attr:
            for cid in sorted(serial):
                for aid in self.aggregate_attributes(cid):
                    meta = kg.attr_nodes[aid]
                    type_id = kg.attr_type.get(aid)
                    is_attr_cls = (
                        type_id in kg.cls_nodes
                        and kg.cls_nodes[type_id].get("isAttribute", False)
                    )
                    allowed = restrictions.get(aid)
                    f_attr.write(json.dumps({
                        "classId": cid,
                        "attrId": aid,
                        "xml_tag": meta["xml_tag"],
                        "xml_wrapper_tag": meta["wrapper"],
                        "isXmlAttr": meta["isXmlAttr"],
                        "minOccurs": meta["minOccurs"],
                        "maxOccurs": meta["maxOccurs"],
                        "typeId": type_id,
                        "attributeClass": is_attr_cls,
                        "allowedValues": allowed or None
                    }, ensure_ascii=False) + "\n")

        # 3) enum literals -------------------------------------------------
        # Collect enums reachable via any attribute returned above
        referenced_enums: Set[int] = set()
        for aid, tid in kg.attr_type.items():
            if tid in kg.enum_idx:
                referenced_enums.add(tid)

        enum_fp = out_path / "raw_enums.jsonl"
        with enum_fp.open("w", encoding="utf-8") as f_enum:
            for eid in sorted(referenced_enums):
                f_enum.write(json.dumps({
                    "enumId": eid,
                    "values": kg.enum_idx[eid],
                }, ensure_ascii=False) + "\n")

        # 4) constraints snapshot -----------------------------------------
        con_fp = out_path / "raw_constraints.jsonl"
        with con_fp.open("w", encoding="utf-8") as f_con:
            for cid, node in kg.constraint_nodes.items():
                f_con.write(json.dumps({
                        "cid": cid,
                        "constraint_type": node.get("constraint_type"),
                        "value": node.get("value"),
                        "expression": node.get("expression"),
                        "targets": kg.constrains_attr.get(cid, []),
                }, ensure_ascii=False) + "\n")

        # 4) save roots for provenance ------------------------------------
        meta_fp = out_path / "meta_roots.json"
        meta_fp.write_text(json.dumps(self.root_ids, ensure_ascii=False, indent=2))

    # ------------------------------------------------------------------
    # Helper utilities
    # ------------------------------------------------------------------

    def _normalise_roots(self, roots: Iterable[str | int]) -> List[int]:
        """Translate *xml_tag* → node ID when needed."""
        if not roots:
            raise ValueError("root class list is empty")

        name2id = self._kg.class_name_index()
        out: List[int] = []
        for r in roots:
            if isinstance(r, int):
                out.append(r)
            else:
                try:
                    out.append(name2id[r])
                except KeyError as err:
                    raise KeyError(f"root class xml_tag '{r}' not found in KG") from err
        return out

    # 啦约束 ----------------------------------------------
    def _collect_value_restrictions(self) -> Dict[int, List[str]]:
        kg = self._kg
        out = defaultdict(set)
        for cid, cn in kg.constraint_nodes.items():
            if cn.get("constraint_type") != "value_restriction":
                continue
            val = cn.get("value")
            if not val:
                continue
            # 支持多枚举拆分（逗号 / 中文顿号 / 空格 / 分号）
            parts = [p.strip() for p in re.split(r"[，,、;；\s]+", val) if p.strip()]
            for aid in kg.constrains_attr.get(cid, []):
                tid = kg.attr_type.get(aid)
                if tid in kg.enum_idx or (
                    tid in kg.cls_nodes and kg.cls_nodes[tid].get("isAttribute", False)
                    and kg.cls_nodes[tid].get("name", "").endswith("Enum")
                ):
                    out[aid].update(parts)
        return {k: sorted(v) for k, v in out.items()}

