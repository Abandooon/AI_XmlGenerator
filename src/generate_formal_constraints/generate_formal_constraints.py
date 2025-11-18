# -*- coding: utf-8 -*-

import os
import json
import re
import sys
import time
from pathlib import Path
from typing import Iterable, List, Tuple, Optional

# ---------------------------
# LLM 客户端
# ---------------------------
def _load_llm_client():
    try:
        from src.llm_generation.llm.openai_client import OpenAIClient
        class _Adapter:
            def __init__(self):
                self._cli = OpenAIClient()
            def generate_text(self, prompt: str, system_message: Optional[str] = None,
                              seed: Optional[int] = None, temperature: Optional[float] = None):
                text, in_tok, out_tok, ttl_tok = self._cli.generate_text(
                    prompt=prompt,
                    system_message=system_message,
                    seed=seed,
                    temperature=temperature
                )
                return text, in_tok, out_tok, ttl_tok

        return _Adapter()
    except Exception:
        print("[WARN] 未能加载项目内 OpenAIClient。")

# ---------------------------
# 工具函数
# ---------------------------

def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8")

def read_json(p: Path):
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)

def chunked(seq: List, n: int) -> Iterable[List]:
    for i in range(0, len(seq), n):
        yield seq[i:i+n]

_CODE_BLOCK_TURTLE = re.compile(r"```turtle\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)
_CODE_BLOCK_SMT2   = re.compile(r"```smt2\s*(.*?)\s*```",   re.DOTALL | re.IGNORECASE)
_CODE_BLOCK_JSON   = re.compile(r"```json\s*(.*?)\s*```",   re.DOTALL | re.IGNORECASE)

def extract_turtle_and_smt2_and_json(text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    从 LLM 返回文本中抽取 turtle、smt2 与 json 三个代码块的内容（去掉围栏）。
    若找不到，返回 (None, None, None) 或其中之一。
    """
    turtle_match = _CODE_BLOCK_TURTLE.search(text)
    smt2_match   = _CODE_BLOCK_SMT2.search(text)
    json_match   = _CODE_BLOCK_JSON.search(text)
    turtle = turtle_match.group(1).strip() if turtle_match else None
    smt2   = smt2_match.group(1).strip()   if smt2_match else None
    jtxt   = json_match.group(1).strip()   if json_match else None
    return turtle, smt2, jtxt

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def append_with_sep(p: Path, content: str):
    """向文件尾部追加一段内容，前后自动补换行分隔"""
    if not content:
        return
    with p.open("a", encoding="utf-8") as f:
        if p.exists() and p.stat().st_size > 0:
            f.write("\n\n")
        f.write(content.strip() + "\n")

def append_mapping_json(mapping_path: Path, mapping_block: str):
    """
    把 LLM 生成的 mapping JSON 块追加到 mapping_path（该文件为 JSON 数组）。
    - 如果 mapping_block 是 JSON 对象或数组，合并到文件中的数组里（append entries）。
    - 若文件不存在，创建新的数组文件。
    - 若解析失败，记录警告并写入 mapping_errors.log（append 原始文本，便于人工检查）。
    """
    if not mapping_block:
        return
    try:
        parsed = json.loads(mapping_block)
    except Exception as e:
        # try to salvage common issues: replace smart quotes, trailing commas
        try:
            cleaned = mapping_block.replace("“", "\"").replace("”", "\"").replace("’", "'")
            cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)  # remove trailing commas
            parsed = json.loads(cleaned)
        except Exception as e2:
            # give up and log
            logp = mapping_path.with_name("mapping_errors.log")
            with logp.open("a", encoding="utf-8") as lf:
                lf.write(f"\n\n# Failed to parse mapping JSON block at {time.asctime()}:\n")
                lf.write(mapping_block)
                lf.write("\n\n# parse error: " + str(e2) + "\n")
            print(f"[WARN] 无法解析 mapping JSON，已记录到 {logp}")
            return

    # load existing mappings (array)
    existing: List = []
    if mapping_path.exists():
        try:
            with mapping_path.open("r", encoding="utf-8") as mf:
                existing = json.load(mf)
                if not isinstance(existing, list):
                    # if it's a single object, wrap
                    existing = [existing]
        except Exception as e:
            # back up bad content and start anew
            bak = mapping_path.with_suffix(".bak.json")
            try:
                mapping_path.replace(bak)
                print(f"[WARN] 现有 mapping 文件无法解析，已备份为 {bak}")
            except Exception:
                pass
            existing = []

    # merge parsed into existing
    if isinstance(parsed, list):
        existing.extend(parsed)
    else:
        existing.append(parsed)

    # write back
    try:
        with mapping_path.open("w", encoding="utf-8") as mf:
            json.dump(existing, mf, ensure_ascii=False, indent=2)
        print(f"[OK] mapping 已追加到：{mapping_path}")
    except Exception as e:
        print(f"[ERROR] 写 mapping 文件失败：{e}")

# ---------------------------
# 主流程
# ---------------------------

def main():
    base_dir = Path(__file__).resolve().parent
    input_dir = base_dir / "input"
    output_dir = base_dir / "output"
    ensure_dir(output_dir)

    promote_path = input_dir / "promote.txt"
    constraints_path = input_dir / "constraints.json"
    shacl_out = output_dir / "shacl.ttl"
    smt_out   = output_dir / "constraints.smt2"
    mapping_out = output_dir / "mapping_smt.json"

    if not promote_path.exists():
        print(f"[ERROR] 未找到 promote 文件：{promote_path}")
        sys.exit(1)
    if not constraints_path.exists():
        print(f"[ERROR] 未找到 constraints.json 文件：{constraints_path}")
        sys.exit(1)

    promote = read_text(promote_path)
    constraints = read_json(constraints_path)

    if not isinstance(constraints, list) or not constraints:
        print("[WARN] constraints.json 不是数组或为空。不会调用 LLM。")
        sys.exit(0)

    client = _load_llm_client()
    print("[INFO] LLM 客户端已就绪。")

    total_batches = 0
    for batch in chunked(constraints, 7):
        total_batches += 1
        payload = json.dumps(batch, ensure_ascii=False, indent=2)
        prompt = (
            f"{promote.rstrip()}\n\n"
            f"{payload}\n\n"
            f"请输出：\n"
            f"1. ```turtle``` 块（SHACL）\n"
            f"2. ```smt2``` 块（SMT模板）\n"
            f"3. ```json``` 块（mapping数组）"
        )

        print(f"[INFO] 处理分组 {total_batches}（大小={len(batch)}）...")
        t0 = time.time()
        try:
            text, in_tok, out_tok, ttl_tok = client.generate_text(prompt=prompt)
        except Exception as e:
            print(f"[ERROR] LLM 调用失败：{e}")
            continue
        dt = time.time() - t0
        print(f"[INFO] LLM 返回，耗时 {dt:.2f}s")

        turtle, smt2, mapping_block = extract_turtle_and_smt2_and_json(text)
        if turtle is None and smt2 is None and mapping_block is None:
            print("[WARN] 未解析到 turtle/smt2/json 代码块，跳过本批。")
            continue

        if turtle:
            append_with_sep(shacl_out, turtle)
            print(f"[OK] 已追加 SHACL 到：{shacl_out}")
        else:
            print("[WARN] 本批未生成 SHACL。")

        if smt2:
            append_with_sep(smt_out, smt2)
            print(f"[OK] 已追加 SMT 到：{smt_out}")
        else:
            print("[WARN] 本批未生成 SMT。")

        if mapping_block:
            append_mapping_json(mapping_out, mapping_block)
        else:
            print("[WARN] 本批未生成 mapping JSON。")

    print(f"[DONE] 共处理分组：{total_batches}。输出位于 {output_dir}")

if __name__ == "__main__":
    main()
