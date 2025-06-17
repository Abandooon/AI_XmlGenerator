"""
导出图到 Neo4j 或 RDF
====================================================
• 默认使用 neo4j-driver 批量 `UNWIND`
• 若 cfg.graph_backend = rdf_hdt，则序列化 Turtle
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import neo4j

from utils.logger import get_logger
from utils.exceptions import ExportError

logger = get_logger(__name__)

Node = Dict[str, Any]
Edge = Tuple[str, str, str]


class Neo4jExporter:
    """批量写入 Neo4j"""

    def __init__(self, uri: str, user: str, password: str) -> None:
        self.driver = neo4j.GraphDatabase.driver(uri, auth=(user, password))

    # ----------- Public -----------
    def export(self, nodes: list[Node], edges: list[Edge]) -> None:
        with self.driver.session() as sess:
            self._create_constraints(sess)
            self._batch_nodes(sess, nodes)
            self._batch_edges(sess, edges)
            logger.info("Neo4j 导入完成: nodes=%d edges=%d", len(nodes), len(edges))

    # ----------- Private -----------
    @staticmethod
    def _create_constraints(sess: neo4j.Session) -> None:
        sess.run("""
            CREATE CONSTRAINT id_is_unique IF NOT EXISTS
            FOR (n:Entity)                 // ★ 指定 Entity 标签
            REQUIRE n.id IS UNIQUE
        """)


    def _batch_nodes(
            self,
            sess: neo4j.Session,
            nodes: list[Node],
            batch_size: int = 1_000,
    ) -> None:
        """
        批量写节点（依赖 APOC 5.x）

        ❶ 预处理：把 label 拆成列表；props 过滤 id/label/空值
        ❷ Cypher：apoc.merge.node → 保证唯一 + 加 :Entity
                  apoc.create.addLabels → 批量附加其余标签
                  apoc.map.clean       → 写入属性（去除 null/''）
        """
        # ---------- ❶ Python 侧预处理 ----------
        rows = []
        for n in nodes:
            labels = n["label"].split(";") if n["label"] else []
            props = {k: v for k, v in n.items()
                     if k not in ("id", "label") and v not in (None, "", [])}
            rows.append({"id": n["id"], "labels": labels, "props": props})

        # ---------- ❷ 带 APOC 的批量语句 ----------
        cypher = """
        UNWIND $batch AS row

        // Merge 节点，保证 (id) 唯一，同时加基础标签
        CALL apoc.merge.node(
            ['Entity'],                   // 基础标签
            {id: row.id}
        ) YIELD node

        // 动态添加额外标签
        CALL apoc.create.addLabels(node, row.labels) YIELD node AS n

        // 清理并写入属性：
        //   · 第二参 keysToRemove 为空列表 -> 不删键
        //   · 第三参 valuesToRemove 过滤 NULL 和 ''，避免 NPE
        WITH apoc.map.clean(row.props, [], [NULL,'']) AS cleanProps, n
        SET  n += cleanProps
        """

        # 批量执行
        for i in range(0, len(rows), batch_size):
            sess.run(cypher, batch=rows[i: i + batch_size])

    def _batch_edges(self, sess: neo4j.Session, edges: list[Edge]) -> None:
        query = """
        UNWIND $batch AS e
        MATCH (s {id: e[0]}),(t {id: e[2]})
        MERGE (s)-[r:`%s`]->(t)
        """ % (
            "%s"
        )  # edge type 占位

        # 分类型批插，减少动态语句
        buckets: dict[str, list[Edge]] = {}
        for s, rel, t in edges:
            buckets.setdefault(rel, []).append((s, rel, t))

        for rel, sub in buckets.items():
            q = query % rel
            self._batch_exec(sess, q, sub)

    @staticmethod
    def _batch_exec(sess: neo4j.Session, cypher: str, data: list[Any], batch_size: int = 1000) -> None:
        for i in range(0, len(data), batch_size):
            sess.run(cypher, batch=data[i : i + batch_size])


# ----------- 简易 RDF 导出 (可选) -----------

class RdfExporter:
    """
    简化实现：把 Node/Edge 转 Turtle 字符串
    """

    def export(self, nodes: list[Node], edges: list[Edge], ttl_path: str) -> None:
        try:
            from rdflib import Graph, URIRef, Literal, RDF
        except ImportError as exc:  # pragma: no cover
            raise ExportError("请安装 rdflib 以启用 RDF 导出") from exc

        g = Graph()
        for n in nodes:
            subj = URIRef(n["id"])
            for label in n["label"].split(";"):
                g.add((subj, RDF.type, URIRef(f"kg:{label}")))
            for k, v in n.items():
                if k in ("id", "label") or v is None:
                    continue
                g.add((subj, URIRef(f"kg:{k}"), Literal(v)))

        for s, rel, t in edges:
            g.add((URIRef(s), URIRef(f"kg:{rel}"), URIRef(t)))

        g.serialize(ttl_path, format="turtle")
        logger.info("RDF 已导出到 %s", ttl_path)
