#!/usr/bin/env python
# coding: utf-8
"""
additional_xsd_parser.py ____ 目的是将由于属性“内联其值类型”而引用的 group ref="XXX"提取到元数据中
-------------------------------------------------
• 仅扫描 XSD 第一层 <complexType> → 采集 group ref
• 只补 groups 节点，不动 complexTypes
• 过滤逻辑：inline_ref − {当前类所有 UML 祖先}
"""

import argparse
import json
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

from lxml import etree

from uml_metadata_parser.XsdParser.TypeMapping import to_pascal_case

# ---- 默认路径（可在 PyCharm Run/Debug 中覆盖） ----
DEFAULT_XSD  = Path("data/AUTOSAR_4-2-2.xsd")
DEFAULT_JSON = Path("data/unified_metadata.json")
DEFAULT_OUT  = Path("output/unified_metadata_with_inlines.json")
# --------------------------------------------------


def collect_inline_map(xsd_path: Path) -> dict[str, set[str]]:
    """收集 entity → {ref_class, …} 映射"""
    ns = {"xsd": "http://www.w3.org/2001/XMLSchema"}
    tree = etree.parse(str(xsd_path))
    inline_map: dict[str, set[str]] = defaultdict(set)

    for ct in tree.xpath("/xsd:schema/xsd:complexType", namespaces=ns):
        raw_name = ct.get("name")
        if not raw_name:
            continue
        entity = to_pascal_case(raw_name)

        for grp in ct.xpath("./xsd:sequence/xsd:group | ./xsd:choice/xsd:group", namespaces=ns):
            ref_raw = grp.get("ref")
            if not ref_raw:
                continue
            ref_cls = to_pascal_case(ref_raw.split(":")[-1])
            if ref_cls != entity:
                inline_map[entity].add(ref_cls)
    return inline_map


def patch_json(in_json: Path, out_json: Path, inline_map: dict[str, set[str]]) -> None:
    data   = json.loads(in_json.read_text(encoding="utf-8"))
    groups = data.get("groups", {})

    # ---------- 构建 UML 继承索引 ----------
    parent_map: dict[str, list[str]] = {
        g["name"]: g.get("generalization", []) for g in groups.values()
    }

    @lru_cache(maxsize=None)
    def ancestors(cls: str) -> set[str]:
        """递归收集所有祖先类名（不含自身）"""
        parents = parent_map.get(cls, [])
        acc = set(parents)
        for p in parents:
            acc |= ancestors(p)
        return acc

    # ---------- 更新 xsdInlines ----------
    changed = 0
    for g in groups.values():
        cls = g["name"]
        if cls not in inline_map:
            continue

        missing = inline_map[cls] - ancestors(cls)
        if not missing:
            continue

        cur = set(g.get("xsdInlines", []))
        cur.update(missing)
        g["xsdInlines"] = sorted(cur)
        changed += 1

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✅ 已更新 {changed} 个类；结果写入 {out_json.resolve()}")


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--xsd",  type=Path, default=DEFAULT_XSD)
    ap.add_argument("--json", type=Path, default=DEFAULT_JSON)
    ap.add_argument("--out",  type=Path, default=DEFAULT_OUT)
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    if not args.xsd.exists():
        raise FileNotFoundError(f"XSD 文件不存在: {args.xsd}")
    if not args.json.exists():
        raise FileNotFoundError(f"JSON 文件不存在: {args.json}")

    inline_map = collect_inline_map(args.xsd)
    patch_json(args.json, args.out, inline_map)


if __name__ == "__main__":
    main()
