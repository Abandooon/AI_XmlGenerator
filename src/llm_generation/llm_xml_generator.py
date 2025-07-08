"""llm_xml_generator.py

Batch-generate AUTOSAR ARXML (JSON via tool-calling) with Gemini
────────────────────────────────────────────────────────────────
* Prompts: promote.yaml  (min/mid/full ± rag)
* Seeds  : 42, 1001, 20240704   — library若不支持 seed 将自动忽略
* Outputs:
    ├── output/<group>/<idx>_seed<seed>.json   ← 模型 JSON (if USE_JSON_SCHEMA=True)
    ├── output/<group>/<idx>_seed<seed>.txt    ← 原始文本 (if USE_JSON_SCHEMA=False)
    └── output/metrics.csv                     ← 指标记录
"""
from __future__ import annotations

import csv
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml
import google.generativeai as genai
from src.kg_builder.doc_constr_parser.config import (
    LLM_API_KEY,
    LLM_API_BASE,
    LLM_MODEL_NAME,
    MAX_OUTPUT_TOKENS,
)

# ────────────────────────────────
# Hyper-params & constants
# ────────────────────────────────
# 控制是否使用JSON Schema的开关
USE_JSON_SCHEMA: bool = True  # 设为True启用JSON Schema，False为纯文本模式

SEEDS: List[int] = [42, 1001, 20240704]
TEMPERATURE: float = 0.7
TOP_P: float = 0.9
RATE_LIMIT_SLEEP: float = 0.5  # seconds between calls

BASE_DIR   = Path(__file__).resolve().parent
PROMPT_YML = BASE_DIR / "promote.yaml"
SCHEMA_JSON = BASE_DIR / "schema.json"

OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
METRICS_CSV = OUTPUT_DIR / "metrics.csv"

# ────────────────────────────────
# Gemini init
# ────────────────────────────────
if not LLM_API_KEY:
    raise EnvironmentError("LLM_API_KEY 环境变量未设置！")

genai.configure(
    api_key=LLM_API_KEY,
    transport="rest",
    client_options={"api_endpoint": LLM_API_BASE or "https://generativelanguage.googleapis.com"},
)
MODEL = genai.GenerativeModel(LLM_MODEL_NAME)

# ────────────────────────────────
# I/O helpers
# ────────────────────────────────
def load_prompts(path: Path) -> Dict[str, List[str]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("promote.yaml must map lists by group name")
    return data


def load_schema(path: Path) -> dict:
    schema = json.loads(path.read_text(encoding="utf-8"))
    # 移除Google AI API不支持的字段
    unsupported_fields = ["$schema", "title"]
    for field in unsupported_fields:
        if field in schema:
            del schema[field]

    # 递归移除嵌套属性中的不支持字段
    def clean_schema(obj):
        if isinstance(obj, dict):
            for field in unsupported_fields:
                if field in obj:
                    del obj[field]
            for key, value in list(obj.items()):
                clean_schema(value)
        elif isinstance(obj, list):
            for item in obj:
                clean_schema(item)

    clean_schema(schema)
    return schema

def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def init_metrics_file() -> None:
    if not METRICS_CSV.exists():
        with METRICS_CSV.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["timestamp", "group", "idx", "seed", "use_json_schema", "status", "elapsed_s",
                 "input_tokens", "output_tokens", "total_tokens", "chars", "outfile", "error"]
            )

def write_metrics(row: List) -> None:
    with METRICS_CSV.open("a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(row)

def extract_token_usage(response) -> Tuple[int, int, int]:
    """从响应中提取token使用情况"""
    try:
        if hasattr(response, 'usage_metadata'):
            usage = response.usage_metadata
            input_tokens = getattr(usage, 'prompt_token_count', 0)
            output_tokens = getattr(usage, 'candidates_token_count', 0)
            total_tokens = getattr(usage, 'total_token_count', input_tokens + output_tokens)
            return input_tokens, output_tokens, total_tokens
        else:
            return 0, 0, 0
    except Exception:
        return 0, 0, 0

# ────────────────────────────────
# Generation core
# ────────────────────────────────
# 只有在启用JSON Schema时才加载schema和工具定义
SCHEMA = load_schema(SCHEMA_JSON) if USE_JSON_SCHEMA else None
TOOLS_DEF = [{
    "function_declarations": [{
        "name": "generate_arxml_json",
        "description": "Generate AUTOSAR ASW component JSON conforming to schema",
        "parameters": SCHEMA,
    }]
}] if USE_JSON_SCHEMA else None

def make_gen_config(seed: int):
    """构造兼容不同版本 google-generativeai 的 GenerationConfig"""
    try:
        # 尝试新版本API（支持seed参数）
        return genai.types.GenerationConfig(
            temperature=TEMPERATURE,
            top_p=TOP_P,
            max_output_tokens=MAX_OUTPUT_TOKENS,
            seed=seed,
        )
    except (TypeError, AttributeError):
        # 老版本不支持seed参数
        return genai.types.GenerationConfig(
            temperature=TEMPERATURE,
            top_p=TOP_P,
            max_output_tokens=MAX_OUTPUT_TOKENS,
        )


def call_gemini_with_schema(prompt: str, seed: int) -> Tuple[str, int, int, int]:
    """使用JSON Schema调用Gemini，返回格式化的JSON字符串和token使用情况"""
    sys_msg = (
        "You are an AUTOSAR ASW component assistant. "
        "Return content strictly via the provided function so that it matches the JSON Schema."
    )
    full_prompt = f"<sys>{sys_msg}</sys>\n{prompt}"
    gen_config = make_gen_config(seed)

    # 尝试多种API格式以确保兼容性
    api_attempts = [
        # 新版API格式
        {
            "tools": TOOLS_DEF,
            "tool_config": {"function_calling_config": {"mode": "any", "allowed_function_names": ["generate_arxml_json"]}}
        },
        # 备用格式1
        {
            "tools": TOOLS_DEF,
            "tool_config": {"function_calling_config": {"mode": "any"}}
        },
        # 旧版API格式
        {
            "tools": [{
                "name": "generate_arxml_json",
                "description": "Generate AUTOSAR ASW component JSON conforming to schema",
                "parameters": SCHEMA,
            }]
        }
    ]

    last_error = None
    for attempt_idx, api_config in enumerate(api_attempts):
        try:
            resp = MODEL.generate_content(
                contents=full_prompt,
                generation_config=gen_config,
                **api_config
            )

            if not resp.candidates or not resp.candidates[0].content.parts:
                raise RuntimeError("Empty response from Gemini")

            part = resp.candidates[0].content.parts[0]
            if not hasattr(part, "function_call"):
                raise RuntimeError("Gemini did not return a function_call result")

            # 修复：统一调用增强的序列化函数
            json_args = _convert_to_serializable(part.function_call.args)

            input_tokens, output_tokens, total_tokens = extract_token_usage(resp)
            return json.dumps(json_args, ensure_ascii=False, indent=2), input_tokens, output_tokens, total_tokens

        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            # 如果是API格式相关错误，尝试下一种格式
            if any(keyword in error_str for keyword in [
                "tool_config", "function_declarations", "function_calling_config",
                "mode", "allowed_function_names", "unexpected", "argument"
            ]):
                continue
            else:
                # 如果不是API格式问题，直接抛出错误
                raise

    # 所有尝试都失败了
    raise RuntimeError(f"All API format attempts failed. Last error: {last_error}")

def _convert_to_serializable(obj):
    """
    递归将任意对象（包括Google AI的特殊对象）转换为可JSON序列化的标准Python对象。
    - 增强了对 MessageMapContainer 和 MapComposite 的处理。
    """
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    if isinstance(obj, dict):
        return {k: _convert_to_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_convert_to_serializable(i) for i in obj]

    # 专门处理 Google AI 的特殊对象类型
    obj_type_name = type(obj).__name__

    # 处理 MapComposite 和 MessageMapContainer 类型
    if 'MapComposite' in obj_type_name or 'MessageMapContainer' in obj_type_name:
        try:
            # 方法1: 尝试作为字典迭代
            if hasattr(obj, 'items') and callable(obj.items):
                result = {}
                for k, v in obj.items():
                    result[k] = _convert_to_serializable(v)
                return result

            # 方法2: 尝试通过keys()和[]访问
            if hasattr(obj, 'keys') and callable(obj.keys):
                result = {}
                for key in obj.keys():
                    try:
                        value = obj[key]
                        result[key] = _convert_to_serializable(value)
                    except (KeyError, TypeError):
                        continue
                return result

            # 方法3: 尝试通过dir()获取属性
            if hasattr(obj, '__dict__'):
                return _convert_to_serializable(obj.__dict__)

        except Exception as e:
            print(f"[DEBUG] Failed to serialize {obj_type_name}: {e}")

    # 处理其他可能的容器类型
    if hasattr(obj, '__iter__') and not isinstance(obj, str):
        try:
            # 尝试作为列表处理
            return [_convert_to_serializable(item) for item in obj]
        except (TypeError, AttributeError):
            pass

        try:
            # 尝试作为字典处理
            if hasattr(obj, 'items'):
                return {k: _convert_to_serializable(v) for k, v in obj.items()}
        except (AttributeError, TypeError):
            pass

    # 备用方法：检查常见的转换方法
    for method_name in ('to_dict', 'as_dict', '_asdict'):
        if hasattr(obj, method_name) and callable(getattr(obj, method_name)):
            try:
                return _convert_to_serializable(getattr(obj, method_name)())
            except Exception:
                continue

    # 最终回退：详细的对象分析
    print(f"[WARN] Unserializable object type: {obj_type_name}")
    print(f"[DEBUG] Object methods: {[m for m in dir(obj) if not m.startswith('_')]}")

    # 尝试获取对象的所有公共属性
    try:
        attrs = {}
        for attr_name in dir(obj):
            if not attr_name.startswith('_'):
                try:
                    attr_value = getattr(obj, attr_name)
                    if not callable(attr_value):
                        attrs[attr_name] = _convert_to_serializable(attr_value)
                except Exception:
                    continue
        if attrs:
            return attrs
    except Exception:
        pass

    # 最终回退：转换为字符串
    return str(obj)


def call_gemini_text_only(prompt: str, seed: int) -> Tuple[str, int, int, int]:
    """纯文本模式调用Gemini，返回原始文本和token使用情况"""
    sys_msg = (
        "You are an AUTOSAR ASW component assistant. "
        "Generate the requested ARXML content directly as text."
    )
    full_prompt = f"<sys>{sys_msg}</sys>\n{prompt}"
    gen_config = make_gen_config(seed)

    resp = MODEL.generate_content(
        contents=full_prompt,
        generation_config=gen_config,
    )

    if not resp.candidates or not resp.candidates[0].content.parts:
        raise RuntimeError("Empty response from Gemini")

    text_content = resp.text
    input_tokens, output_tokens, total_tokens = extract_token_usage(resp)
    return text_content, input_tokens, output_tokens, total_tokens


def call_gemini(prompt: str, seed: int) -> Tuple[str, int, int, int]:
    """根据USE_JSON_SCHEMA设置调用对应的函数"""
    if USE_JSON_SCHEMA:
        return call_gemini_with_schema(prompt, seed)
    else:
        return call_gemini_text_only(prompt, seed)

# ────────────────────────────────
# Main loop
# ────────────────────────────────
def generate_all() -> None:
    init_metrics_file()
    prompts_by_group = load_prompts(PROMPT_YML)

    print(f"[INFO] JSON Schema mode: {'ENABLED' if USE_JSON_SCHEMA else 'DISABLED'}")
    print(f"[INFO] Output format: {'.json' if USE_JSON_SCHEMA else '.txt'}")

    for group, prompts in prompts_by_group.items():
        if not isinstance(prompts, list):
            print(f"[WARN] Skip key '{group}' – expected list.")
            continue

        out_dir = OUTPUT_DIR / group
        ensure_dir(out_dir)

        for idx, prompt in enumerate(prompts, 1):
            for seed in SEEDS:
                # 根据模式选择文件扩展名
                file_ext = "json" if USE_JSON_SCHEMA else "txt"
                fname = f"{idx:02d}_seed{seed}.{file_ext}"
                out_path = out_dir / fname
                if out_path.exists():
                    print(f"[SKIP] {group}/{fname} exists")
                    continue

                print(f"[INFO] {group} › {idx} › seed {seed}")
                t0 = time.perf_counter()
                status = "success"
                err_msg = ""
                content = ""
                input_tokens = output_tokens = total_tokens = 0

                try:
                    content, input_tokens, output_tokens, total_tokens = call_gemini(prompt, seed)
                    out_path.write_text(content, encoding="utf-8")
                    print(f"[SAVED] → {out_path.relative_to(BASE_DIR)} (chars={len(content)}, tokens={total_tokens})")
                except Exception as e:
                    status = "error"
                    err_msg = str(e)
                    print(f"[ERROR] {err_msg}")
                elapsed = time.perf_counter() - t0

                write_metrics([
                    datetime.now().isoformat(timespec="seconds"),
                    group,
                    idx,
                    seed,
                    USE_JSON_SCHEMA,
                    status,
                    f"{elapsed:.3f}",
                    input_tokens,
                    output_tokens,
                    total_tokens,
                    len(content),
                    str(out_path.relative_to(BASE_DIR)),
                    err_msg,
                ])
                time.sleep(RATE_LIMIT_SLEEP * (3 if status == "error" else 1))

if __name__ == "__main__":
    generate_all()
