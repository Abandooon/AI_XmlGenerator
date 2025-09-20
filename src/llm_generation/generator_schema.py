# generator_schema.py — Test Harness to go beyond schema and capture Round2 prompts
from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List, Tuple
from types import SimpleNamespace
import json
import re
import time
from datetime import datetime

# === 项目内导入（与现有工程保持一致） ===
# 已有：动态查询引擎（用于生成接口/组件 schema）
from src.llm_generation.knowledge.dynamic_query_engine import query_engine
# 新增：Round2 生成器（用于实际组装 prompt 并产出实例与 ARXML）
from src.llm_generation.core.round2_generator import round2_generator
# 读取全局配置（拿到 output_dir / debug_mode 等）
from src.llm_generation.config import CONFIG


# =========================
# 工具函数
# =========================
def _ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _safe_name(name: str) -> str:
    """把组件名等规范化为文件名友好格式"""
    s = re.sub(r"[^\w\-]+", "_", (name or "").strip())
    return s.strip("_") or "unnamed"


def _read_json(p: Path) -> Dict[str, Any]:
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(p: Path, obj: Any) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def _latest_round1_json() -> Path | None:
    """在 CONFIG.output_dir/round1_data 下寻找最新的 round1_*.json"""
    p = Path("output/round1_data/round1_20250917_155551.json")
    return p if p.exists() else None

def load_round1_design(path: Path) -> Dict[str, Any]:
    """兼容不同保存格式：design / response_data"""
    js = _read_json(path)
    payload = js.get("design") or js.get("response_data") or {}
    return {
        "component_plan": payload.get("component_plan", []),
        "interface_plan": payload.get("interface_plan", []),
        "system_analysis": payload.get("system_analysis", {}),
        "connection_topology": payload.get("connection_topology", {}),
        "architecture_rationale": payload.get("architecture_rationale", {})
    }


def _schema_out_root() -> Path:
    """schema 预览输出根目录"""
    return Path(CONFIG.output_dir) / "schema_preview"


def _round2_out_root() -> Path:
    """Round2 调试输出根目录（本脚本额外保存 ARXML）"""
    return Path(CONFIG.output_dir) / "round2_debug"


def _snapshot_prompt_files() -> List[Path]:
    """
    基于 round2_generator 内部的默认命名约定抓取 prompt：
    - 接口：round2_prompt_*.txt
    - 组件：round2_prompt_<组件名>_*.txt
    为兼容不同实现，递归在 output_dir 下通配查找。
    """
    root = Path(CONFIG.output_dir)
    patterns = [
        "**/round2_prompt_*.txt",
        "**/debug/round2_prompt_*.txt",          # 部分实现会放在 debug 子目录
    ]
    seen = set()
    results: List[Path] = []
    for pat in patterns:
        for p in root.glob(pat):
            # 去重并仅保留文件
            try:
                if p.is_file() and p not in seen:
                    seen.add(p)
                    results.append(p)
            except Exception:
                pass
    return sorted(results, key=lambda x: x.stat().st_mtime)


def _diff_new_files(before: List[Path], after: List[Path]) -> List[Path]:
    bset = {p.resolve() for p in before}
    return [p for p in after if p.resolve() not in bset]


def _print_prompt_head(path: Path, max_lines: int = 40) -> None:
    """打印每个 prompt 的前若干行，方便快速预览"""
    try:
        txt = path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        print(f"    [WARN] 无法读取 {path}: {e}")
        return
    lines = txt.splitlines()
    head = "\n".join(lines[:max_lines])
    more = "" if len(lines) <= max_lines else f"\n    ... （共 {len(lines)} 行，已截断）"
    print(f"---- {path.name} (位于 {path.parent}) ----")
    print(head)
    if more:
        print(more)
    print("-" * 80)


# =========================
# 1) 生成接口/组件的 Schema（保持你现有逻辑）
# =========================
def build_and_dump_schemas(design: Dict[str, Any]) -> Tuple[Path, Path]:
    """
    生成接口与组件 Schema 并落盘。
    返回：(接口Schema文件, 组件Schema目录)
    """
    out_root = _schema_out_root() / _ts()
    out_root.mkdir(parents=True, exist_ok=True)
    out_comp_dir = out_root / "components"
    out_comp_dir.mkdir(parents=True, exist_ok=True)

    interfaces = design.get("interface_plan", []) or []
    comps = design.get("component_plan", []) or []

    # 1) 接口 Schema
    try:
        iface_schema = query_engine.generate_interfaces_schema(interfaces)
    except Exception as e:
        print(f"[WARN] 生成接口Schema失败：{e}")
        iface_schema = {"type": "object", "properties": {}, "definitions": {}}

    iface_file = out_root / "_interfaces.schema.json"
    _write_json(iface_file, iface_schema)
    print(f"[OK] 写入接口Schema: {iface_file}")

    # 2) 组件 Schema（逐组件）
    total = 0
    for idx, comp in enumerate(comps, start=1):
        comp_name = _safe_name(comp.get("name", f"Component_{idx}"))
        try:
            comp_schema = query_engine.generate_component_schema_fixed(comp)
        except Exception as e:
            print(f"[WARN] 生成组件Schema失败（{comp_name}）：{e}")
            comp_schema = {"type": "object", "properties": {}, "definitions": {}}

        out_file = out_comp_dir / f"{idx:02d}_{comp_name}.schema.json"
        _write_json(out_file, comp_schema)
        print(f"[OK] 写入组件Schema: {out_file}")
        total += 1

    print(f"[DONE] 已生成 接口Schema + {total} 个组件Schema；根目录：{out_root}")
    return iface_file, out_comp_dir


# =========================
# 2) 继续下钻：调用 Round2 并捕获本次生成的所有 prompt
# =========================
def run_round2_and_capture_prompts(design: Dict[str, Any]) -> Path:
    """
    构造 ArchitectureDesign（用 SimpleNamespace 即可），
    调用 round2_generator.generate_arxml(...)，
    返回保存的 ARXML 路径；同时在控制台打印新生成的接口/组件 prompt。
    """
    # 1) 运行前快照（已有 prompt）
    before = _snapshot_prompt_files()

    # 2) 组装 ArchitectureDesign（Round2 只用到 .component_plan / .interface_plan 等属性）
    arch = SimpleNamespace(
        component_plan=design.get("component_plan", []),
        interface_plan=design.get("interface_plan", []),
        system_analysis=design.get("system_analysis", {}),
        connection_topology=design.get("connection_topology", {}),
        architecture_rationale=design.get("architecture_rationale", {})
    )

    # 3) 调用 Round2（不改生成器）
    print("[INFO] 调用 Round2 生成器（generate_arxml）...")
    t0 = time.time()
    arxml_content, stats = round2_generator.generate_arxml(
        architecture_design=arch,
        memory_context="(TEST) generator_schema.py"
    )
    dt = time.time() - t0
    print(f"[OK] Round2 完成，耗时 {dt:.2f}s；统计: { {k: stats.get(k) for k in ['input_tokens','output_tokens','total_tokens','generation_time'] if k in stats} }")

    # 4) 保存合并 ARXML
    out_root = _round2_out_root()
    out_root.mkdir(parents=True, exist_ok=True)
    arxml_path = out_root / f"combined_{_ts()}.arxml"
    arxml_path.write_text(arxml_content or "", encoding="utf-8")
    print(f"[OK] ARXML 写入：{arxml_path}")

    # 5) 运行后快照，找出“本次新生成”的所有 prompt
    after = _snapshot_prompt_files()
    new_prompts = _diff_new_files(before, after)

    if not new_prompts:
        print("[WARN] 未检测到新的 prompt 文件。可能是：")
        print("  - Round2 未落盘 prompt；或")
        print("  - prompt 文件名/目录与你的实现不一致。")
    else:
        print(f"[INFO] 本次新生成 {len(new_prompts)} 个 prompt 文件：")
        for p in new_prompts:
            print(f"  - {p}")

        print("\n[PREVIEW] Prompt 内容（截取前若干行）")
        print("=" * 80)
        for p in new_prompts:
            _print_prompt_head(p, max_lines=40)

    return arxml_path


# =========================
# 统一入口（右键运行）
# =========================
def run() -> None:
    """
    右键直接运行的入口：
      1) 自动寻找最近的 Round1 JSON
      2) 生成接口/组件 Schema
      3) 下钻到 Round2，抓取并预览接口与各组件的 prompt
    如需固定 Round1 文件，可把 round1_path 赋值为具体路径。
    """
    # 手动指定路径（若你希望固定一个 round1.json，取消下一行注释并填写路径）
    # round1_path = Path("src/llm_generation/output/round1_data/round1_20250917_155551.json")

    round1_path = _latest_round1_json()
    if not round1_path:
        raise FileNotFoundError("未找到 Round1 产物（CONFIG.output_dir/round1_data/round1_*.json）。请先运行 Round1，或手动在本文件中指定 round1_path。")

    print(f"[INFO] 使用 Round1 数据：{round1_path}")
    design = load_round1_design(round1_path)

    # 先生成 Schema（保持你原来的测试行为）
    build_and_dump_schemas(design)

    # 再继续调用 Round2，抓取接口/组件 prompt
    run_round2_and_capture_prompts(design)

    print("\n[ALL DONE] 已完成：Schema 落盘 + Round2 运行 + Prompt 抓取/预览。")


# PyCharm 右键运行入口
if __name__ == "__main__":
    run()
