"""llm_xml_generator.py

Batch-generate AUTOSAR ARXML (JSON via tool-calling) with Gemini
────────────────────────────────────────────────────────────────
* Prompts: promote.yaml  (min/mid/full ± rag)
* Seeds  : 42, 1001, 20250701   — library若不支持 seed 将自动忽略
* Outputs:
    ├── output/<group>/<idx>_seed<seed>.json   ← 模型 JSON (if USE_JSON_SCHEMA=True)
    ├── output/<group>/<idx>_seed<seed>.xml    ← 原始 XML (if USE_JSON_SCHEMA=False)
    └── output/metrics.csv                     ← 指标记录
"""
from __future__ import annotations

import csv
import json
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import google.generativeai as genai
import yaml

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
USE_JSON_SCHEMA: bool = False  # 设为True启用JSON Schema，False为纯文本模式
DEBUG_MODE: bool = True  # 启用详细调试输出
TEST_SIMPLE_PROMPT: bool = False  # 使用简化的测试提示词

SEEDS: List[int] = [42, 1001, 20250701]  # 随机种子列表
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


def convert_json_schema_to_gemini_schema(json_schema: dict) -> dict:
    """将 JSON Schema 转换为 Gemini 的 response_schema 格式"""

    def convert_type(json_type: str) -> str:
        """转换类型名称"""
        type_mapping = {
            "object": "OBJECT",
            "array": "ARRAY",
            "string": "STRING",
            "number": "NUMBER",
            "integer": "INTEGER",
            "boolean": "BOOLEAN"
        }
        return type_mapping.get(json_type, "STRING")

    def convert_schema_object(obj: dict) -> dict:
        """递归转换 schema 对象"""
        result = {}

        # 转换类型
        if "type" in obj:
            result["type"] = convert_type(obj["type"])

        # 转换描述
        if "description" in obj:
            result["description"] = obj["description"]

        # 处理对象属性
        if obj.get("type") == "object" and "properties" in obj:
            result["properties"] = {}
            for key, value in obj["properties"].items():
                result["properties"][key] = convert_schema_object(value)

            # 添加必需字段
            if "required" in obj:
                result["required"] = obj["required"]

        # 处理数组项
        if obj.get("type") == "array" and "items" in obj:
            result["items"] = convert_schema_object(obj["items"])

        # 处理枚举
        if "enum" in obj:
            result["enum"] = obj["enum"]

        return result

    # 从根对象开始转换
    return convert_schema_object(json_schema)


def call_gemini_with_response_schema(prompt: str, seed: int) -> Tuple[str, int, int, int]:
    """使用 Response Schema 方式调用 Gemini"""

    # 转换 JSON Schema 为 Gemini 格式
    gemini_schema = convert_json_schema_to_gemini_schema(SCHEMA)

    # 构建生成配置
    generation_config = genai.types.GenerationConfig(
        response_mime_type="application/json",
        response_schema=gemini_schema,
        temperature=TEMPERATURE,
        top_p=TOP_P,
        max_output_tokens=MAX_OUTPUT_TOKENS,
    )

    # 添加 seed（如果支持）
    try:
        generation_config.seed = seed
    except AttributeError:
        pass  # 老版本不支持seed

    # 增强提示词
    enhanced_prompt = f"""
You are an AUTOSAR ASW component assistant. Generate JSON content that strictly follows the provided schema.

{prompt}

Important requirements:
1. The response must be valid JSON
2. Follow the exact structure defined in the schema
3. Use correct AUTOSAR naming conventions
4. Include all required fields
"""

    try:
        # 调用 Gemini
        resp = MODEL.generate_content(
            contents=enhanced_prompt,
            generation_config=generation_config,
        )

        if not resp.text:
            raise RuntimeError("Empty response from Gemini")

        # 解析响应
        try:
            # Gemini 使用 response_schema 时直接返回 JSON 字符串
            json_obj = json.loads(resp.text)
        except json.JSONDecodeError:
            # 如果解析失败，尝试提取 JSON 部分
            import re
            json_match = re.search(r'\{[\s\S]*\}', resp.text)
            if json_match:
                json_str = json_match.group(0)
                json_obj = json.loads(json_str)
            else:
                raise ValueError(f"Invalid JSON in response: {resp.text[:500]}...")

        # 获取 token 使用情况
        input_tokens, output_tokens, total_tokens = extract_token_usage(resp)

        # 返回格式化的 JSON
        return json.dumps(json_obj, ensure_ascii=False, indent=2), input_tokens, output_tokens, total_tokens

    except Exception as e:
        if DEBUG_MODE:
            print(f"[DEBUG] Response schema generation failed: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
        raise


def call_gemini(prompt: str, seed: int) -> Tuple[str, int, int, int]:
    """根据USE_JSON_SCHEMA设置调用对应的函数"""
    if USE_JSON_SCHEMA:
        # 使用 Response Schema 方式而不是 Function Calling
        return call_gemini_with_response_schema(prompt, seed)
    else:
        return call_gemini_text_only(prompt, seed)


# 为了完整性，这里提供一个简化版的 Gemini Schema（如果自动转换有问题）
def get_simplified_gemini_schema() -> dict:
    """返回简化的 Gemini response_schema"""
    return {
        "type": "OBJECT",
        "properties": {
            "APPLICATION-SW-COMPONENT-TYPE": {
                "type": "OBJECT",
                "required": ["SHORT-NAME", "PORTS"],
                "properties": {
                    "SHORT-NAME": {
                        "type": "STRING",
                        "description": "Component name"
                    },
                    "ADMIN-DATA": {
                        "type": "OBJECT",
                        "properties": {
                            "SDGS": {
                                "type": "OBJECT",
                                "properties": {
                                    "SDG": {
                                        "type": "OBJECT",
                                        "properties": {
                                            "SD": {"type": "STRING"},
                                            "@GID": {"type": "STRING"}
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "PORTS": {
                        "type": "OBJECT",
                        "properties": {
                            "P-PORT-PROTOTYPE": {
                                "type": "ARRAY",
                                "items": {
                                    "type": "OBJECT",
                                    "required": ["SHORT-NAME", "PROVIDED-INTERFACE-TREF"],
                                    "properties": {
                                        "@UUID": {"type": "STRING"},
                                        "SHORT-NAME": {"type": "STRING"},
                                        "PROVIDED-INTERFACE-TREF": {
                                            "type": "OBJECT",
                                            "required": ["@DEST", "#text"],
                                            "properties": {
                                                "@DEST": {
                                                    "type": "STRING",
                                                    "enum": ["SENDER-RECEIVER-INTERFACE"]
                                                },
                                                "#text": {"type": "STRING"}
                                            }
                                        }
                                    }
                                }
                            },
                            "R-PORT-PROTOTYPE": {
                                "type": "ARRAY",
                                "items": {
                                    "type": "OBJECT",
                                    "required": ["SHORT-NAME", "REQUIRED-INTERFACE-TREF"],
                                    "properties": {
                                        "@UUID": {"type": "STRING"},
                                        "SHORT-NAME": {"type": "STRING"},
                                        "REQUIRED-INTERFACE-TREF": {
                                            "type": "OBJECT",
                                            "required": ["@DEST", "#text"],
                                            "properties": {
                                                "@DEST": {
                                                    "type": "STRING",
                                                    "enum": ["SENDER-RECEIVER-INTERFACE"]
                                                },
                                                "#text": {"type": "STRING"}
                                            }
                                        },
                                        "REQUIRED-COM-SPECS": {
                                            "type": "OBJECT",
                                            "properties": {
                                                "NONQUEUED-RECEIVER-COM-SPEC": {
                                                    "type": "OBJECT",
                                                    "properties": {
                                                        "DATA-ELEMENT-REF": {
                                                            "type": "OBJECT",
                                                            "properties": {
                                                                "@DEST": {"type": "STRING"},
                                                                "#text": {"type": "STRING"}
                                                            }
                                                        },
                                                        "ALIVE-TIMEOUT": {"type": "NUMBER"},
                                                        "HANDLE-TIMEOUT-TYPE": {"type": "STRING"}
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "INTERNAL-BEHAVIORS": {
                        "type": "OBJECT",
                        "properties": {
                            "SWC-INTERNAL-BEHAVIOR": {
                                "type": "OBJECT",
                                "properties": {
                                    "SHORT-NAME": {"type": "STRING"},
                                    "EVENTS": {
                                        "type": "OBJECT",
                                        "properties": {
                                            "TIMING-EVENT": {
                                                "type": "ARRAY",
                                                "items": {
                                                    "type": "OBJECT",
                                                    "properties": {
                                                        "@UUID": {"type": "STRING"},
                                                        "SHORT-NAME": {"type": "STRING"},
                                                        "START-ON-EVENT-REF": {
                                                            "type": "OBJECT",
                                                            "properties": {
                                                                "@DEST": {"type": "STRING"},
                                                                "#text": {"type": "STRING"}
                                                            }
                                                        },
                                                        "PERIOD": {"type": "NUMBER"}
                                                    }
                                                }
                                            }
                                        }
                                    },
                                    "RUNNABLES": {
                                        "type": "OBJECT",
                                        "properties": {
                                            "RUNNABLE-ENTITY": {
                                                "type": "ARRAY",
                                                "items": {
                                                    "type": "OBJECT",
                                                    "properties": {
                                                        "@UUID": {"type": "STRING"},
                                                        "SHORT-NAME": {"type": "STRING"},
                                                        "DATA-RECEIVE-POINT-BY-ARGUMENTS": {
                                                            "type": "OBJECT",
                                                            "properties": {
                                                                "VARIABLE-ACCESS": {
                                                                    "type": "ARRAY",
                                                                    "items": {
                                                                        "type": "OBJECT",
                                                                        "properties": {
                                                                            "@UUID": {"type": "STRING"},
                                                                            "SHORT-NAME": {"type": "STRING"},
                                                                            "ACCESSED-VARIABLE": {"type": "OBJECT"}
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        },
                                                        "DATA-SEND-POINTS": {
                                                            "type": "OBJECT",
                                                            "properties": {
                                                                "VARIABLE-ACCESS": {
                                                                    "type": "ARRAY",
                                                                    "items": {
                                                                        "type": "OBJECT",
                                                                        "properties": {
                                                                            "@UUID": {"type": "STRING"},
                                                                            "SHORT-NAME": {"type": "STRING"},
                                                                            "ACCESSED-VARIABLE": {"type": "OBJECT"}
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        },
                                                        "SYMBOL": {"type": "STRING"}
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }


# 简化的替代方案：如果上述方法仍有问题，可以使用这个更简单的版本
def call_gemini_with_schema_simple(prompt: str, seed: int) -> Tuple[str, int, int, int]:
    """简化版本：让模型直接生成JSON，不使用function calling"""

    # 修改提示词，要求直接输出JSON
    enhanced_prompt = f"""
{prompt}

请直接输出符合以下要求的JSON格式内容，不要包含任何其他说明文字：
1. 必须是有效的JSON格式
2. 必须包含 APPLICATION-SW-COMPONENT-TYPE 作为根对象
3. 必须符合AUTOSAR ASW组件的结构

输出示例格式：
{{
  "APPLICATION-SW-COMPONENT-TYPE": {{
    "SHORT-NAME": "...",
    "PORTS": {{
      ...
    }}
  }}
}}
"""

    gen_config = make_gen_config(seed)

    try:
        resp = MODEL.generate_content(
            contents=enhanced_prompt,
            generation_config=gen_config,
        )

        if not resp.text:
            raise RuntimeError("Empty response from Gemini")

        # 从响应中提取JSON
        text = resp.text.strip()

        # 尝试直接解析
        try:
            json_obj = json.loads(text)
        except json.JSONDecodeError:
            # 查找JSON部分
            import re
            json_match = re.search(r'\{[\s\S]*\}', text)
            if json_match:
                json_str = json_match.group(0)
                json_obj = json.loads(json_str)
            else:
                raise ValueError("No valid JSON found in response")

        input_tokens, output_tokens, total_tokens = extract_token_usage(resp)
        return json.dumps(json_obj, ensure_ascii=False, indent=2), input_tokens, output_tokens, total_tokens

    except Exception as e:
        if DEBUG_MODE:
            print(f"[DEBUG] Simple generation failed: {type(e).__name__}: {str(e)}")
        raise


def _convert_to_serializable(obj: Any, visited: Optional[set] = None, depth: int = 0) -> Any:
    """
    递归将任意对象转换为可JSON序列化的标准Python对象，防止无限递归。
    """
    # 防止无限递归
    if depth > 10:  # 限制递归深度
        return f"<MaxDepth: {type(obj).__name__}>"

    if visited is None:
        visited = set()

    # 检查对象ID避免循环引用
    obj_id = id(obj)
    if obj_id in visited:
        return f"<Circular: {type(obj).__name__}>"

    # 基本类型直接返回
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj

    # 添加到已访问集合
    visited.add(obj_id)

    try:
        # 标准容器类型
        if isinstance(obj, dict):
            result = {}
            for k, v in obj.items():
                if isinstance(k, (str, int, float)):
                    result[str(k)] = _convert_to_serializable(v, visited, depth + 1)
            return result

        if isinstance(obj, (list, tuple)):
            return [_convert_to_serializable(i, visited, depth + 1) for i in obj]

        # 处理Google AI的特殊对象
        obj_type_name = type(obj).__name__

        # 跳过问题类型
        if obj_type_name in ('MessageMeta', 'mappingproxy', 'MessageRule'):
            return f"<Skipped: {obj_type_name}>"

        # 处理protobuf消息
        if hasattr(obj, '_pb'):
            try:
                from google.protobuf.json_format import MessageToDict
                return MessageToDict(obj._pb)
            except Exception:
                pass

        # 尝试转换为字典（限制属性数量）
        if hasattr(obj, '__dict__'):
            obj_dict = obj.__dict__
            if len(obj_dict) < 50:  # 限制属性数量防止过大对象
                return _convert_to_serializable(obj_dict, visited, depth + 1)

        # 最终返回类型描述
        return f"<{obj_type_name}>"

    except Exception as e:
        return f"<Error: {type(e).__name__}>"
    finally:
        # 从已访问集合中移除，允许在其他路径中再次访问
        visited.discard(obj_id)


def call_gemini_text_only(prompt: str, seed: int, max_retries: int = 3, base_delay: float = 1.0) -> Tuple[
    str, int, int, int]:
    """纯文本模式调用Gemini，包含重试机制"""
    sys_msg = (
        "You are an AUTOSAR ASW component assistant. "
        "Generate the requested ARXML content directly as XML text. "
        "Output only the XML content without any additional explanation."
    )
    full_prompt = f"<sys>{sys_msg}</sys>\n{prompt}"
    gen_config = make_gen_config(seed)

    last_exception: Optional[Exception] = None

    for attempt in range(max_retries):
        try:
            if DEBUG_MODE and attempt > 0:
                print(f"[DEBUG] Retry attempt {attempt + 1}/{max_retries}")

            resp = MODEL.generate_content(
                contents=full_prompt,
                generation_config=gen_config,
            )

            if not resp.candidates or not resp.candidates[0].content.parts:
                raise RuntimeError("Empty response from Gemini")

            text_content = resp.text
            input_tokens, output_tokens, total_tokens = extract_token_usage(resp)

            if DEBUG_MODE and attempt > 0:
                print(f"[DEBUG] Retry successful on attempt {attempt + 1}")

            return text_content, input_tokens, output_tokens, total_tokens

        except Exception as e:
            last_exception = e
            error_type = type(e).__name__

            # 对于网络相关错误进行重试
            if error_type in ['ProxyError', 'SSLError', 'ConnectionError', 'Timeout']:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)  # 指数退避
                    if DEBUG_MODE:
                        print(f"[DEBUG] Network error {error_type}, retrying in {delay:.1f}s...")
                    time.sleep(delay)
                    continue

            # 非网络错误或重试次数用完，直接抛出
            break

    # 所有重试都失败
    print(
        f"[ERROR] Text generation failed after {max_retries} attempts: {type(last_exception).__name__}: {str(last_exception)}")
    raise last_exception

# ────────────────────────────────
# Main loop
# ────────────────────────────────
def test_basic_gemini_connection() -> bool:
    """测试基本的Gemini连接是否正常"""
    try:
        print("[TEST] Testing basic Gemini connection...")
        test_prompt = "Hello, please respond with 'OK' if you can see this message."
        resp = MODEL.generate_content(test_prompt)

        if resp and resp.text:
            print(f"[TEST] Basic connection successful. Response: {resp.text[:100]}")
            return True
        else:
            print("[TEST] Basic connection failed: No response text")
            return False
    except Exception as e:
        print(f"[TEST] Basic connection failed: {type(e).__name__}: {str(e)}")
        return False


def generate_all() -> None:
    init_metrics_file()

    # 首先测试基本连接
    if DEBUG_MODE and not test_basic_gemini_connection():
        print("[ERROR] Basic Gemini connection test failed. Please check your API key and network connection.")
        return

    prompts_by_group = load_prompts(PROMPT_YML)

    print(f"[INFO] JSON Schema mode: {'ENABLED' if USE_JSON_SCHEMA else 'DISABLED'}")
    print(f"[INFO] Output format: {'.json' if USE_JSON_SCHEMA else '.txt'}")
    print(f"[INFO] Model: {LLM_MODEL_NAME}")
    print(f"[INFO] Debug mode: {'ENABLED' if DEBUG_MODE else 'DISABLED'}")
    print(f"[INFO] Test simple prompt: {'ENABLED' if TEST_SIMPLE_PROMPT else 'DISABLED'}")
    print("-" * 60)

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
                    # 提供更详细的错误信息
                    err_msg = f"{type(e).__name__}: {str(e)}"
                    print(f"[ERROR] {err_msg}")

                    # 在调试模式下打印完整的堆栈跟踪
                    if hasattr(e, '__traceback__'):
                        print("[TRACEBACK]")
                        traceback.print_exc()

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
                    str(out_path.relative_to(BASE_DIR)) if content else "",
                    err_msg,
                ])

                # 错误时增加等待时间
                time.sleep(RATE_LIMIT_SLEEP * (3 if status == "error" else 1))

    print("-" * 60)
    print("[INFO] Generation complete!")

if __name__ == "__main__":
    generate_all()