"""loader.py (v1.2)
===================
Support JSON *and* Neo4j input **and** expose `attr_idx` / `enum_idx` for Enricher.
"""
from __future__ import annotations

import json
import os
import pathlib
from typing import Any, Dict, List

try:
    from neo4j import GraphDatabase  # type: ignore
except ModuleNotFoundError:
    GraphDatabase = None  # type: ignore

__all__ = ["ConstraintLoader"]


class ConstraintLoader:
    def __init__(self, kg_uri: str | pathlib.Path):
        self.kg_uri = str(kg_uri)
        self.mode = "bolt" if self.kg_uri.startswith("neo4j://") else "json"
        if self.mode == "json":
            kg_path = pathlib.Path(self.kg_uri)
            self.nodes_file = kg_path / "kg_nodes.json"
            self.edges_file = kg_path / "kg_edges.json"
            if not (self.nodes_file.exists() and self.edges_file.exists()):
                raise FileNotFoundError("kg_nodes.json / kg_edges.json missing in " + str(kg_path))
        else:
            if GraphDatabase is None:
                raise ImportError("neo4j-driver not installed – pip install neo4j")

        # public indexes for Enricher
        self.attr_idx: Dict[str, Dict[str, Any]] = {}
        self.enum_idx: Dict[str, List[Dict[str, Any]]] = {}

    # ------------------------------------------------------------
    def load(self) -> List[Dict[str, Any]]:
        if self.mode == "json":
            nodes, edges = self._load_json_nodes_edges()
        else:
            nodes, edges = self._load_bolt_nodes_edges()
        self._build_indexes(nodes, edges)
        return self._collect_constraints(nodes, edges)

    # ------------------------------------------------------------
    def _load_json_nodes_edges(self) -> tuple[Dict[str, Dict[str, Any]], List[tuple[str, str, str]]]:
        with open(self.nodes_file, "r", encoding="utf-8") as f:
            nodes = {n["id"]: n for n in json.load(f)}
        with open(self.edges_file, "r", encoding="utf-8") as f:
            edges = [tuple(e) for e in json.load(f)]
        return nodes, edges

    # ------------------------------------------------------------
    def _load_bolt_nodes_edges(self) -> tuple[Dict[str, Dict[str, Any]], List[tuple[str, str, str]]]:
        user = os.getenv("NEO4J_USER", "neo4j")
        pwd = os.getenv("NEO4J_PASS", "autosar4.2.2")
        driver = GraphDatabase.driver(self.kg_uri, auth=(user, pwd))
        nodes: Dict[str, Dict[str, Any]] = {}
        edges: List[tuple[str, str, str]] = []

        # 1) constraint triples
        q1 = (
            "MATCH (c:Constraint)-[:CONSTRAINS]->(t) "
            "RETURN c.id AS cid, c.constraint_type AS ctype, c.value AS val, "
            "c.expression AS expr, t.qualifiedName AS qname, t.name AS tname"
        )
        # 2) attribute meta
        q2 = (
            "MATCH (cls)-[:HAS_ATTRIBUTE]->(a:Attribute) "
            "RETURN cls.name AS cls, a.name AS attr, a.minOccurs AS minO, a.maxOccurs AS maxO, a.type AS typ"
        )
        # 3) enum literals
        q3 = (
            "MATCH (e:Enum)-[:HAS_LITERAL]->(l:EnumLiteral) "
            "RETURN e.name AS ename, l.value AS val"
        )
        with driver.session() as sess:
            for r in sess.run(q1):
                cid = r["cid"]
                nodes.setdefault(cid, {
                    "id": cid,
                    "constraint_type": r.get("ctype"),
                    "value": r.get("val"),
                    "expression": r.get("expr"),
                })
                tgt_name = r.get("qname") or r.get("tname")
                tid = f"attr:{tgt_name}"
                nodes.setdefault(tid, {"id": tid, "qualifiedName": tgt_name, "name": tgt_name})
                edges.append((cid, "CONSTRAINS", tid))
            for r in sess.run(q2):
                key = f"{r['cls']}.{r['attr']}"
                self.attr_idx[key] = {"minOccurs": r["minO"], "maxOccurs": r["maxO"], "type": r["typ"]}
            for r in sess.run(q3):
                self.enum_idx.setdefault(r["ename"], []).append({"value": r["val"]})
        return nodes, edges

    # ------------------------------------------------------------
    def _build_indexes(self, nodes: Dict[str, Dict[str, Any]], edges: List[tuple[str, str, str]]) -> None:
        if self.attr_idx:
            return  # already built (bolt branch)
        # build from JSON nodes
        for n in nodes.values():
            if n.get("label") == "Attribute":
                parent = self._find_parent_class(n["id"], edges, nodes)
                if not parent:
                    continue
                key = f"{parent}.{n['name']}"
                self.attr_idx[key] = {
                    "minOccurs": n.get("minOccurs"),
                    "maxOccurs": n.get("maxOccurs"),
                    "type": n.get("type"),
                }
            elif n.get("label") == "EnumLiteral":
                pass  # handled via edge
        # enum literals via edges
        for s, rel, e in edges:
            if rel == "HAS_LITERAL":
                en = nodes[s]["name"]
                lit_val = nodes[e].get("value")
                self.enum_idx.setdefault(en, []).append({"value": lit_val})

    def _find_parent_class(
            self,
            attr_id: str,
            edges: List[tuple[str, str, str]],
            nodes: Dict[str, Dict[str, Any]],  # 新参数
    ) -> str | None:
        for s, rel, e in edges:
            if rel == "HAS_ATTRIBUTE" and e == attr_id:
                return nodes[s]["name"]  # ← 用 nodes 查真正类名
        return None

    # ------------------------------------------------------------
    def _collect_constraints(self, nodes: Dict[str, Dict[str, Any]], edges: List[tuple[str, str, str]]) -> List[Dict[str, Any]]:
        constraints: Dict[str, Dict[str, Any]] = {}
        for s, rel, e in edges:
            if rel != "CONSTRAINS":
                continue
            c_node = nodes[s]
            t_node = nodes[e]
            cid = c_node["id"]
            record = constraints.setdefault(cid, {**c_node, "targets": []})
            target_name = (t_node.get("qualifiedName") or t_node.get("name") or "").replace("/", ".")
            record["targets"].append(target_name)
        return list(constraints.values())
