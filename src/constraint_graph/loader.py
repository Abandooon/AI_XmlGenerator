"""loader.py (v1.1)
===================
Load constraints either from:
1. **Offline JSON dump** (kg_nodes.json / kg_edges.json)
2. **Online Neo4j** via bolt URI, e.g. ``bolt://localhost:7687``

Environment variables ``NEO4J_USER`` / ``NEO4J_PASS`` supply credentials (default ``neo4j/neo4j``).
"""
from __future__ import annotations

import json
import os
import pathlib
from typing import Any, Dict, List

try:
    from neo4j import GraphDatabase  # type: ignore
except ModuleNotFoundError:  # lazy import – only required when bolt:// is used
    GraphDatabase = None  # type: ignore

__all__ = ["ConstraintLoader"]


class ConstraintLoader:
    """Extract (:Constraint)-[:CONSTRAINS]->(:Attribute|Class) triples."""

    # ------------------------------------------------------------
    def __init__(self, kg_uri: str | pathlib.Path):
        self.kg_uri = str(kg_uri)
        self.mode = "bolt" if self.kg_uri.startswith("bolt://") else "json"

        if self.mode == "json":
            kg_path = pathlib.Path(self.kg_uri)
            self.nodes_file = kg_path / "kg_nodes.json"
            self.edges_file = kg_path / "kg_edges.json"
            if not self.nodes_file.exists() or not self.edges_file.exists():
                raise FileNotFoundError("kg_nodes.json / kg_edges.json not found in " + str(kg_path))
        else:
            if GraphDatabase is None:
                raise ImportError("neo4j-driver missing – `pip install neo4j`.")

    # ------------------------------------------------------------
    def load(self) -> List[Dict[str, Any]]:
        if self.mode == "json":
            return self._load_from_json()
        return self._load_from_bolt()

    # ============================================================
    # JSON branch
    # ============================================================
    def _load_from_json(self) -> List[Dict[str, Any]]:
        with open(self.nodes_file, "r", encoding="utf-8") as f:
            nodes = {n["id"]: n for n in json.load(f)}
        with open(self.edges_file, "r", encoding="utf-8") as f:
            edges = [tuple(e) for e in json.load(f)]
        return self._collect(nodes, edges)

    # ============================================================
    # Neo4j branch
    # ============================================================
    def _load_from_bolt(self) -> List[Dict[str, Any]]:
        user = os.getenv("NEO4J_USER", "neo4j")
        pwd = os.getenv("NEO4J_PASS", "neo4j")
        driver = GraphDatabase.driver(self.kg_uri, auth=(user, pwd))

        query = (
            "MATCH (c:Constraint)-[:CONSTRAINS]->(t) "
            "RETURN c.id AS cid, c.constraint_type AS ctype, c.value AS val, "
            "c.expression AS expr, t.qualifiedName AS qname, t.name AS tname"
        )
        with driver.session() as sess:
            rows = sess.run(query).data()

        # ➜ synthesize nodes / edges dicts compatible with JSON branch
        nodes: Dict[str, Dict[str, Any]] = {}
        edges: List[tuple[str, str, str]] = []
        for row in rows:
            cid = row["cid"]
            cnode = nodes.setdefault(cid, {
                "id": cid,
                "constraint_type": row.get("ctype"),
                "value": row.get("val"),
                "expression": row.get("expr"),
            })
            tgt_name = row.get("qname") or row.get("tname")
            tgt_id = f"attr:{tgt_name}"
            nodes.setdefault(tgt_id, {
                "id": tgt_id,
                "qualifiedName": tgt_name,
                "name": tgt_name,
            })
            edges.append((cid, "CONSTRAINS", tgt_id))

        return self._collect(nodes, edges)

    # ============================================================
    # common collector
    # ============================================================
    def _collect(self, nodes: Dict[str, Dict[str, Any]], edges: List[tuple[str, str, str]]) -> List[Dict[str, Any]]:
        constraints: Dict[str, Dict[str, Any]] = {}
        for s, rel, e in edges:
            if rel != "CONSTRAINS":
                continue
            c_node = nodes[s]
            t_node = nodes[e]
            cid = c_node["id"]
            record = constraints.setdefault(cid, {**c_node, "targets": []})
            target_name = t_node.get("qualifiedName") or t_node.get("name")
            record["targets"].append(target_name)
        return list(constraints.values())
