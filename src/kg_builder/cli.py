"""
KG Builder 命令行入口
====================================================
零参数运行：python -m kg_builder.cli
如需切换配置文件：python -m kg_builder.cli --cfg my_cfg.yaml
"""

from __future__ import annotations

import argparse
from pathlib import Path

from config import load_config
from loader import MetadataLoader, ConstraintLoader
from normalizer import normalize_metadata
from ontology_builder import OntologyGraphBuilder
from constraint_parser import ConstraintGraphBuilder
from edge_builder import EdgeAssembler
from graph_exporter import Neo4jExporter, RdfExporter
from shacl_generator import ShapeEmitter
from smt_exporter import SmtEmitter
from schema_exporter import GbnfMaker
from utils.logger import get_logger

logger = get_logger(__name__)


# ----------------------------------------------------------------------
# CLI 解析 —— 仅保留 --cfg，可零参数运行
# ----------------------------------------------------------------------
def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser("kg_builder", add_help=False)
    ap.add_argument("--cfg", default="config.yaml", help="配置 YAML 路径")
    return ap.parse_args()


# ----------------------------------------------------------------------
def main() -> None:  # pragma: no cover
    args = _parse_args()
    cfg = load_config(args.cfg)

    # ---------- 1. 加载 & 规范化元数据 ----------
    meta_path = cfg["metadata_path"]
    cons_path = cfg["constraints_path"]
    if not (meta_path and cons_path):
        raise SystemExit("请在 config.yaml 配置 metadata_path 与 constraints_path")
    # 解析 json文件
    mdata = MetadataLoader().load(meta_path)
    # 加载 metadata 的 groups-elements, complexTypes-attributes, simpleTypes-enumerations，原地写入iri ------ 其他元素呢？
    mdata = normalize_metadata(mdata, domain=cfg["domain"], version=cfg["version"])

    constraints = ConstraintLoader().load(cons_path)

    # ---------- 2. 构建 Ontology ----------
    onto_builder = OntologyGraphBuilder()
    on_nodes, on_edges = onto_builder.build(mdata)

    # 索引供连边解析
    cls_idx = {n["name"]: n["id"] for n in on_nodes if "Class" in n["label"]}
    attr_idx = {f"{n['id'].split('/')[-2]}/{n['name']}": n["id"] for n in on_nodes if n["label"] == "Attribute"}
    enum_idx = {n["name"]: n["id"] for n in on_nodes if n["label"] == "Enum"}
    lit_idx = {n["id"].split("/", 1)[-1]: n["id"] for n in on_nodes if n["label"] == "EnumLiteral"}

    # ---------- 3. 约束节点 ----------
    con_nodes = ConstraintGraphBuilder(cfg["domain"], cfg["version"]).build(constraints)

    # ---------- 4. 连边 ----------
    assembler = EdgeAssembler(
        class_index=cls_idx,
        attr_index=attr_idx,
        enum_index=enum_idx,
        literal_index=lit_idx,
    )
    con_edges = assembler.build_edges(con_nodes)

    # 合并
    nodes = on_nodes + con_nodes
    edges = on_edges + con_edges

    # ---------- 5. 导出图 ----------
    if cfg["graph_backend"] == "neo4j":
        Neo4jExporter(
            uri = cfg["neo4j"]["uri"],
            user = cfg["neo4j"]["user"],
            password = cfg["neo4j"]["password"],
        ).export(nodes, edges)
    else:
        RdfExporter().export(nodes, edges, ttl_path="output/kg.ttl")

    # ---------- 6. 导出 SHACL / SMT / GBNF ----------
    out_dir = Path(cfg["output_dir"])
    out_dir.mkdir(exist_ok=True)

    ShapeEmitter(cfg["domain"], cfg["version"]).build(con_nodes) \
        .serialize(cfg["export"]["shacl"])
    Path(cfg["export"]["smt"]).write_text(SmtEmitter().build(con_nodes), encoding="utf-8")
    Path(cfg["export"]["gbnf"]).write_text(GbnfMaker().build(con_nodes), encoding="utf-8")

    logger.info("KG 构建流程结束；产物已输出至 %s", out_dir.resolve())


if __name__ == "__main__":  # pragma: no cover
    main()


# 根据需要，以下代码可以取消注释以导出 SHACL、SMT 和 GBNF 格式
# from .shacl_generator import ShapeEmitter
# from .smt_exporter import SmtEmitter
# from .schema_exporter import GbnfMaker, JsonSchemaMaker
#
# # 在导出 Neo4j / RDF 之后
# ShapeEmitter(cfg["domain"], cfg["version"]).build(con_nodes).serialize(cfg["export"]["shacl"])
# Path(cfg["export"]["smt"]).write_text(SmtEmitter().build(con_nodes), encoding="utf-8")
# Path(cfg["export"]["gbnf"]).write_text(GbnfMaker().build(con_nodes), encoding="utf-8")
