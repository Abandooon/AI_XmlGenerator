# build_schema_per_component.py
from pathlib import Path
import json
import re
import sys

# ★ 根据你的工程包名修改下面导入
from src.llm_generation.knowledge.dynamic_query_engine import query_engine

def load_round1_design(path: str):
    with open(path, "r", encoding="utf-8") as f:
        js = json.load(f)
    payload = js.get("design") or js.get("response_data") or {}
    return {
        "component_plan": payload.get("component_plan", []),
        "interface_plan": payload.get("interface_plan", []),
        "system_analysis": payload.get("system_analysis", {}),
        "connection_topology": payload.get("connection_topology", {}),
        "architecture_rationale": payload.get("architecture_rationale", {}),
    }

def _safe_name(s: str) -> str:
    s = s.strip() or "Component"
    # 只保留字母数字/._-，其余转为_
    return re.sub(r"[^A-Za-z0-9._-]+", "_", s)

def main():
    # 允许通过命令行传入 Round1 路径；否则用默认示例路径
    round1_path = sys.argv[1] if len(sys.argv) > 1 else "output/round1_data/round1_20250917_155551.json"
    d = load_round1_design(round1_path)

    comps = d.get("component_plan") or []
    intfs = d.get("interface_plan") or []

    out_dir = Path("output/round2_schema_fixed")
    out_comp_dir = out_dir / "components"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_comp_dir.mkdir(parents=True, exist_ok=True)

    # 1) 可选：输出接口只读Schema（一次）
    try:
        interface_schema = query_engine.generate_multi_interface_schema(intfs)
    except Exception as e:
        print(f"[WARN] 生成接口Schema失败：{e}")
        interface_schema = {"type": "object", "properties": {}, "definitions": {}}

    (out_dir / "_interfaces.schema.json").write_text(
        json.dumps(interface_schema, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # 2) 逐组件：调用“固定骨架 + 局部递归”引擎生成单组件Schema并落盘
    total = 0
    for idx, comp in enumerate(comps, start=1):
        comp_name = _safe_name(comp.get("name", f"Component_{idx}"))
        comp_schema = query_engine.generate_component_schema_fixed(comp)

        out_file = out_comp_dir / f"{idx:02d}_{comp_name}.schema.json"
        out_file.write_text(json.dumps(comp_schema, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[OK] 写入组件Schema: {out_file}")
        total += 1

    print(f"[DONE] 共生成 {total} 个组件Schema；接口Schema见 {out_dir / '_interfaces.schema.json'}")

if __name__ == "__main__":
    main()
