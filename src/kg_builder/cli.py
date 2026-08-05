"""
KG Builder 命令行入口
====================================================
零参数运行：python -m kg_builder.cli
如需切换配置文件：python -m kg_builder.cli --cfg my_cfg.yaml
"""

from __future__ import annotations

import argparse
import json
from typing import Any

from neo4j import GraphDatabase

from config import load_config
from constraint_parser import ConstraintGraphBuilder
from edge_builder import EdgeAssembler
from graph_exporter import Neo4jExporter, RdfExporter
from loader import MetadataLoader, ConstraintLoader
from normalizer import normalize_metadata
from ontology_builder import OntologyGraphBuilder
from utils.logger import get_logger

logger = get_logger(__name__)


# ----------------------------------------------------------------------
def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser("kg_builder", add_help=False)
    ap.add_argument("--cfg", default="config.yaml", help="配置 YAML 路径")
    return ap.parse_args()

# 定义清空Neo4j数据库的函数
def clear_neo4j_database(uri: str, user: str, password: str) -> None:
    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        # 清空所有节点及边
        session.run("MATCH (n) DETACH DELETE n")
    driver.close()


# ----------------------------------------------------------------------
def main() -> None:  # pragma: no cover
    args = _parse_args()
    cfg  = load_config(args.cfg)

    # ---------- 0. 清空 Neo4j 数据库 ----------
    if cfg["graph_backend"] == "neo4j":
        clear_neo4j_database(cfg["neo4j"]["uri"], cfg["neo4j"]["user"], cfg["neo4j"]["password"])

    # ---------- 1. 加载 & 规范化元数据 ----------
    mdata = MetadataLoader().load(cfg["metadata_path"])
    mdata = normalize_metadata(
        mdata,
        domain = cfg["domain"],
        version = cfg["version"],
    )

    constraints_raw = ConstraintLoader().load(cfg["constraints_path"])

    # ---------- 2. 构建 Ontology ----------
    onto_builder             = OntologyGraphBuilder()
    on_nodes, on_edges       = onto_builder.build(mdata)
    node_by_id               = {n["id"]: n for n in on_nodes}

    # ---------- 3. 构建 Constraint 节点 ----------
    con_nodes                = ConstraintGraphBuilder(cfg["domain"], cfg["version"]) \
                                .build(constraints_raw)



    # ---------- 5. 索引 ----------
    cls_idx  = {n["name"]: n["id"] for n in on_nodes if n["label"] == "Class"}

    attr_idx: dict[str, str] = {}
    for n in on_nodes:
        if n["label"] != "Attribute":
            continue

        cls_physical = n["parentClass"]
        local_attr   = n["name"]

        # 物理键  ContentClass/attr
        attr_idx[f"{cls_physical}/{local_attr}"] = n["id"]

        # 逻辑键  ownerClass/attr
        owner = n.get("ownerClass") or n.get("qualifiedName", "").split(".", 1)[0]
        if owner:
            attr_idx[f"{owner}/{local_attr}"] = n["id"]

    enum_idx = {n["name"]: n["id"] for n in on_nodes if n["label"] == "Enum"}
    lit_idx  = {
        n["id"].split("/", 1)[-1]: n["id"]
        for n in on_nodes if n["label"] == "EnumLiteral"
    }

    # ---------- 6. parent_index  (多继承) ----------
    parent_index: dict[str, list[str]] = {}
    for s, rel, e in on_edges:
        if rel == "SUBCLASS_OF":
            child  = node_by_id[s]["name"]
            parent = node_by_id[e]["name"]
            parent_index.setdefault(child, []).append(parent)

    # ---------- 7. EdgeAssembler ----------
    assembler   = EdgeAssembler(
        class_index   = cls_idx,
        attr_index    = attr_idx,
        enum_index    = enum_idx,
        literal_index = lit_idx,
        parent_index  = parent_index,
    )
    con_edges   = assembler.build_edges(con_nodes)

    # ---------- 4. 约束节点：序列化 targets ----------
    for n in con_nodes:
        if "targets" in n:
            n["targets_json"] = json.dumps(n.pop("targets"))

    # ---------- 8. 合并节点 & 边 ----------
    nodes: list[dict[str, Any]] = on_nodes + con_nodes
    edges                       = on_edges + con_edges

    # ---------- 9. 导出图 ----------
    if cfg["graph_backend"] == "neo4j":
        Neo4jExporter(
            uri      = cfg["neo4j"]["uri"],
            user     = cfg["neo4j"]["user"],
            password = cfg["neo4j"]["password"],
        ).export(nodes, edges)
    else:
        RdfExporter().export(nodes, edges, ttl_path="output/kg.ttl")

    # ---------- 10. 导出 SHACL / SMT / GBNF ----------
    # out_dir = Path(cfg["output_dir"]); out_dir.mkdir(exist_ok=True)
    # ShapeEmitter(cfg["domain"], cfg["version"]).build(con_nodes) \
    #     .serialize(cfg["export"]["shacl"])
    # Path(cfg["export"]["smt"]).write_text(
    #     SmtEmitter().build(con_nodes), encoding="utf-8"
    # )
    # Path(cfg["export"]["gbnf"]).write_text(
    #     GbnfMaker().build(con_nodes), encoding="utf-8"
    # )

    logger.info("KG 构建流程结束")


if __name__ == "__main__":  # pragma: no cover
    main()
