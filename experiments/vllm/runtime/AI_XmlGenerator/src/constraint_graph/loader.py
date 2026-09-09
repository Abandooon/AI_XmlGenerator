# loader.py (修复版)
"""Unified KG loader that now exposes all indices required by the token‑export
pipeline.

修复：更新所有Neo4j查询使用elementId()替代已弃用的id()函数

The class supports **two back‑ends**:
    1. Live Neo4j instance (bolt/neo4j/http URI)
    2. Local JSON dump consisting of ``nodes.json`` + ``edges.json``

It returns four public dictionaries that downstream components rely on:

    cls_nodes     : classId           -> {"xml_tag", "wrapper"}
    attr_nodes    : attrId            -> {meta on Attribute}
    cls_attrs     : classId           -> [attrId, ...]           # HAS_ATTRIBUTE
    attr_type     : attrId            -> typeId | None           # TYPE_OF
    subcls        : classId           -> set[parentId]           # SUBCLASS_OF
    inline        : classId           -> set[groupClsId]        # INLINE_EXPANDS
    enum_idx      : enumId            -> list[str]              # enum literals
    constraint_nodes : constraintId  -> {constraint metadata}   # Constraint info
    constrains_attr  : constraintId  -> [attrId, ...]          # CONSTRAINS

A minimal set of fields is fetched so that higher layers do *zero* further
queries.
"""
from __future__ import annotations

import json
import os
import pathlib
import urllib
from collections import defaultdict
from typing import Dict, List, Set

from dotenv import load_dotenv

load_dotenv(pathlib.Path(__file__).resolve().parents[2] / ".env")

# Neo4j driver is an optional dependency; import lazily so local‑json mode works
try:
    from neo4j import GraphDatabase, Driver
except ModuleNotFoundError:  # pragma: no cover – still allow json mode without neo4j
    Driver = object  # type: ignore

__all__ = [
    "KGLoader",
]


class KGLoader:
    """Load just enough of the KG to support token extraction and constraint
    canonicalisation.  The *entire* graph is **not** pulled – only the handful of
    labels + edge types required.
    """

    # --- Construction -----------------------------------------------------

    def __init__(
            self,
            source: str | pathlib.Path,
            user: str | None = None,
            password: str | None = None,
    ) -> None:
        """``source`` may be either
            * a *str* ``bolt://`` / ``neo4j://`` / ``http://`` URI or
            * a directory containing ``nodes.json`` + ``edges.json``.
        """
        self._is_neo4j = isinstance(source, str) and source.startswith(("bolt://", "neo4j://", "http://", "https://"))
        self._driver: Driver | None = None
        self._json_dir: pathlib.Path | None = None

        if self._is_neo4j:
            # Neo4j back‑end -------------------------------------------------
            parsed = urllib.parse.urlparse(source)
            uri_user = parsed.username
            uri_pwd = parsed.password

            # 重组 **不含凭证** 的 URI
            clean_netloc = parsed.hostname or ""

            if parsed.port:
                clean_netloc += f":{parsed.port}"
            clean_uri = urllib.parse.urlunparse(
                (parsed.scheme, clean_netloc, parsed.path, "", "", "")
            )

            # ❷ 取优先级：CLI 显式参数 > URI 内嵌 > None
            auth_user = user or uri_user or os.getenv("NEO4J_USER") or "neo4j"
            auth_pwd = (
                password
                or uri_pwd
                or os.getenv("NEO4J_PASSWORD")
                or os.getenv("NEO4J_PWD")
            )
            if not auth_pwd:
                raise ValueError(
                    "Neo4j password is not configured. Set NEO4J_PASSWORD in .env."
                )

            self._driver = GraphDatabase.driver(clean_uri,
                                                auth=(auth_user, auth_pwd))
        else:
            # Local JSON back‑end -------------------------------------------
            self._json_dir = pathlib.Path(source)
            if not (self._json_dir / "nodes.json").exists():
                raise FileNotFoundError("nodes.json not found in " + str(source))

        # Public indices (filled by `load()`)
        self.cls_nodes: Dict[int, Dict[str, str | None]] = {}
        self.attr_nodes: Dict[int, Dict[str, str | int | bool | None]] = {}
        self.cls_attrs: Dict[int, List[int]] = defaultdict(list)
        self.attr_type: Dict[int, int] = {}
        self.subcls: Dict[int, Set[int]] = defaultdict(set)
        self.inline: Dict[int, Set[int]] = defaultdict(set)
        self.enum_idx: Dict[int, List[str]] = {}
        self.constraint_nodes: Dict[int, Dict[str, str | None]] = {}
        self.constrains_attr: Dict[int, List[int]] = defaultdict(list)

        # Kick off data load -------------------------------------------------
        self._load()

    # ---------------------------------------------------------------------
    # Internal helpers (Neo4j)
    # ---------------------------------------------------------------------

    def _load(self) -> None:
        if self._is_neo4j:
            self._load_neo4j()
        else:
            self._load_json()

    # ---------------- Neo4j branch ---------------------------------------

    def _load_neo4j(self) -> None:  # noqa: C901 – a bit long but linear
        assert self._driver is not None, "driver not initialised"

        with self._driver.session() as sess:
            # 🔧 修复：检查Neo4j版本并选择合适的ID函数
            id_function = self._get_id_function(sess)
            print(f"📋 使用Neo4j ID函数: {id_function}")

            # 1) Class nodes ------------------------------------------------
            cy_cls = f"""
            MATCH (c:Class)
            RETURN {id_function}(c) AS cid,
                   c.xml_tag         AS tag,
                   c.name            AS name,
                   c.xml_wrapper_tag AS wrapper,
                   coalesce(c.isAttribute,false) AS isAttr
            """
            for rec in sess.run(cy_cls):
                # 🔧 修复：确保ID为整数类型
                cid = self._normalize_id(rec["cid"])
                self.cls_nodes[cid] = {
                    "xml_tag": rec["tag"],
                    "name": rec["name"],
                    "wrapper": rec["wrapper"],
                    "isAttribute": bool(rec["isAttr"]),
                }

            # 2) Attribute nodes + HAS_ATTRIBUTE ---------------------------
            cy_attr = f"""
            MATCH (c:Class)-[:HAS_ATTRIBUTE]->(a:Attribute)
            RETURN {id_function}(a) AS aid,
                   {id_function}(c) AS cid,
                   a.xml_tag   AS tag,
                   a.xml_wrapper_tag AS wrapper,
                   a.isXmlAttr AS isAttr,
                   a.minOccurs AS lo,
                   a.maxOccurs AS hi
            """
            for rec in sess.run(cy_attr):
                # 🔧 修复：确保ID为整数类型
                aid = self._normalize_id(rec["aid"])
                cid = self._normalize_id(rec["cid"])

                raw = rec["isAttr"]
                is_attr = False  # 默认
                if isinstance(raw, bool):
                    is_attr = raw
                elif isinstance(raw, (int, float)):
                    is_attr = bool(raw)
                elif isinstance(raw, str):
                    is_attr = raw.lower() not in {"false", "0", ""}

                self.attr_nodes[aid] = {
                    "xml_tag": rec["tag"],
                    "wrapper": rec["wrapper"],
                    "isXmlAttr": is_attr,  # ← 用转换后的值
                    "minOccurs": int(rec["lo"]) if rec["lo"] is not None else None,
                    "maxOccurs": int(rec["hi"]) if rec["hi"] is not None else None,
                }

                self.cls_attrs[cid].append(aid)

            # 3) TYPE_OF ----------------------------------------------------
            cy_type = f"""
            MATCH (a:Attribute)-[:TYPE_OF]->(t)
            RETURN {id_function}(a) AS aid, {id_function}(t) AS tid
            """
            for rec in sess.run(cy_type):
                aid = self._normalize_id(rec["aid"])
                tid = self._normalize_id(rec["tid"])
                self.attr_type[aid] = tid

            # 4) SUBCLASS_OF ----------------------------------------------
            cy_sub = f"""
            MATCH (c:Class)-[:SUBCLASS_OF]->(p:Class)
            RETURN {id_function}(c) AS cid, {id_function}(p) AS pid
            """
            for rec in sess.run(cy_sub):
                cid = self._normalize_id(rec["cid"])
                pid = self._normalize_id(rec["pid"])
                self.subcls[cid].add(pid)

            # 5) INLINE_EXPANDS -------------------------------------------
            cy_inline = f"""
            MATCH (c:Class)-[:INLINE_EXPANDS]->(g:Class)
            RETURN {id_function}(c) AS cid, {id_function}(g) AS gid
            """
            for rec in sess.run(cy_inline):
                cid = self._normalize_id(rec["cid"])
                gid = self._normalize_id(rec["gid"])
                self.inline[cid].add(gid)

            # 6) Enum literals --------------------------------------------
            cy_enum = f"""
            MATCH (e:Enum)-[:HAS_LITERAL]->(lit:EnumLiteral)
            WITH {id_function}(e) AS eid, collect(lit.value) AS vals
            RETURN eid, vals
            """
            for rec in sess.run(cy_enum):
                eid = self._normalize_id(rec["eid"])
                self.enum_idx[eid] = rec["vals"]

            # 7) 🔧 修复：约束节点 - 提取完整的约束信息 ---------------------------
            cy_constraints = f"""
            MATCH (c:Constraint)
            RETURN {id_function}(c) AS cid,
                   c.constraint_type AS ctype,
                   c.value           AS val,
                   c.expression      AS expression,
                   c.title           AS title,
                   c.cid             AS constraint_cid,
                   c.id              AS autosar_id,
                   c.id_type         AS id_type,
                   c.is_active       AS is_active,
                   c.references      AS references,
                   c.scope_path      AS scope_path,
                   c.targets_json    AS targets_json
            """
            for rec in sess.run(cy_constraints):
                cid = self._normalize_id(rec["cid"])
                self.constraint_nodes[cid] = {
                    "constraint_type": rec["ctype"],
                    "value": rec["val"],
                    "expression": rec["expression"] or "",
                    "title": rec["title"] or "",
                    "cid": rec["constraint_cid"],  # 约束的实际CID
                    "id": rec["autosar_id"],  # AUTOSAR ID
                    "id_type": rec["id_type"] or "",
                    "is_active": rec["is_active"] if rec["is_active"] is not None else True,
                    "references": rec["references"] or [],
                    "scope_path": rec["scope_path"] or [],
                    "targets_json": rec["targets_json"],
                }

            # 8) 🔧 修复：约束关系 CONSTRAINS ----------------------------------
            cy_constrains = f"""
            MATCH (c:Constraint)-[:CONSTRAINS]->(a:Attribute)
            RETURN {id_function}(c) AS cid, {id_function}(a) AS aid
            """
            for rec in sess.run(cy_constrains):
                cid = self._normalize_id(rec["cid"])
                aid = self._normalize_id(rec["aid"])
                self.constrains_attr[cid].append(aid)

    def _get_id_function(self, session) -> str:
        """🔧 检测Neo4j版本并返回合适的ID函数"""
        try:
            # 尝试使用elementId()函数（Neo4j 5.0+）
            test_query = "MATCH (n) RETURN elementId(n) AS id LIMIT 1"
            result = session.run(test_query)
            result.single()  # 如果成功，说明支持elementId()
            return "elementId"
        except Exception:
            # 如果失败，回退到id()函数（Neo4j 4.x及以下）
            print("⚠️  Neo4j版本不支持elementId()，使用传统id()函数")
            return "id"

    def _normalize_id(self, node_id) -> int:
        """🔧 标准化节点ID为整数"""
        if isinstance(node_id, int):
            return node_id
        elif isinstance(node_id, str):
            # elementId()返回字符串，尝试转换为整数
            if node_id.isdigit():
                return int(node_id)
            else:
                # 对于字符串ID，使用hash生成稳定的整数ID
                return abs(hash(node_id)) % (2 ** 31)
        else:
            # 其他类型，转换为字符串再处理
            return abs(hash(str(node_id))) % (2 ** 31)

    # ---------------- JSON branch ---------------------------------------

    def _load_json(self) -> None:  # noqa: C901 – similar linear loader
        assert self._json_dir is not None
        nodes_fp = self._json_dir / "nodes.json"
        edges_fp = self._json_dir / "edges.json"

        with open(nodes_fp, "r", encoding="utf-8") as f:
            nodes = json.load(f)
        with open(edges_fp, "r", encoding="utf-8") as f:
            edges = json.load(f)

        # Build node index: id → node
        node_map = {n["id"]: n for n in nodes}

        # --- Node payloads ----------------------------------------------
        for n in nodes:
            raw = n["properties"].get("isXmlAttr")
            if isinstance(raw, bool):
                is_attr = raw
            elif isinstance(raw, (int, float)):
                is_attr = bool(raw)
            elif isinstance(raw, str):
                is_attr = raw.lower() not in {"false", "0", ""}
            else:
                is_attr = False

            labels = set(n["labels"] if isinstance(n["labels"], list) else [n["labels"]])
            if "Class" in labels:
                self.cls_nodes[n["id"]] = {
                    "xml_tag": n["properties"].get("xml_tag"),
                    "name": n["properties"].get("name"),
                    "wrapper": n["properties"].get("xml_wrapper_tag"),
                    "isAttribute": n["properties"].get("isAttribute", False),
                }
            elif "Attribute" in labels:
                self.attr_nodes[n["id"]] = {
                    "xml_tag": n["properties"].get("xml_tag"),
                    "wrapper": n["properties"].get("xml_wrapper_tag"),
                    "isXmlAttr": is_attr,
                    "minOccurs": n["properties"].get("minOccurs"),
                    "maxOccurs": n["properties"].get("maxOccurs"),
                }
            elif "EnumLiteral" in labels:
                # handled when reading edges HAS_LITERAL
                pass
            elif "Constraint" in labels:
                # 🔧 修复：提取完整的约束信息
                props = n["properties"]
                self.constraint_nodes[n["id"]] = {
                    "constraint_type": props.get("constraint_type"),
                    "value": props.get("value"),
                    "expression": props.get("expression", ""),
                    "title": props.get("title", ""),
                    "cid": props.get("cid"),
                    "id": props.get("id"),
                    "id_type": props.get("id_type", ""),
                    "is_active": props.get("is_active", True),
                    "references": props.get("references", []),
                    "scope_path": props.get("scope_path", []),
                    "targets_json": props.get("targets_json"),
                }

        # --- Edge payloads ----------------------------------------------
        for e in edges:
            typ = e["type"]
            if typ == "HAS_ATTRIBUTE":
                self.cls_attrs[e["start"]].append(e["end"])
            elif typ == "TYPE_OF":
                self.attr_type[e["start"]] = e["end"]
            elif typ == "SUBCLASS_OF":
                self.subcls[e["start"]].add(e["end"])
            elif typ == "INLINE_EXPANDS":
                self.inline[e["start"]].add(e["end"])
            elif typ == "HAS_LITERAL":
                enum_id = e["start"]
                lit_node = node_map[e["end"]]
                self.enum_idx.setdefault(enum_id, []).append(lit_node["properties"]["value"])
            elif typ == "CONSTRAINS":
                self.constrains_attr[e["start"]].append(e["end"])

        # Deduplicate enum literal order deterministically
        for k, v in self.enum_idx.items():
            self.enum_idx[k] = sorted(set(v))

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def class_name_index(self) -> Dict[str, int]:
        """Return mapping *xml_tag → classId* (for root name resolution)."""
        return {v["xml_tag"]: cid for cid, v in self.cls_nodes.items() if v["xml_tag"]}

    # ----------------------------------------------
    # Context‑manager sugar for session lifecycle
    # ----------------------------------------------
    def close(self):
        if self._driver is not None:
            self._driver.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()