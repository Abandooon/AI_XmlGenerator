# llm/openai_client.py
"""
OpenAI-compatible GPT client via CloseAI proxy.
- Drop-in 替代 GeminiClient：方法签名一致 (generate_with_schema / generate_text)
- 支持 Structured Outputs（优先）→ 自动降级到 JSON mode → 纯文本 + 解析修复
- 兼容 token 统计字段差异
"""

import json
import re
import time
from typing import Dict, Any, Tuple, Optional, List, Union

from openai import OpenAI

from ..config import CONFIG
from ..utils.exceptions import LLMAPIError


class OpenAIClient:
    def __init__(self):
        self.config = CONFIG.llm
        self.debug_mode = getattr(CONFIG, "debug_mode", False)
        self.default_max_retries = 3
        self.rate_limit_sleep = 0.5

        base = self._normalize_base(self.config.llm_api_url)
        # CloseAI 文档：Base URL 要带 /v1
        # 例如 https://api.openai-proxy.org/v1
        self.client = OpenAI(base_url=base, api_key=self.config.api_key)

        self.call_count = 0
        self.total_tokens = 0
        self.success_count = 0
        self.error_count = 0

    # ---------- public APIs (与 GeminiClient 对齐) ----------

    def generate_with_schema(
        self,
        prompt: str,
        schema: Dict[str, Any],
        seed: Optional[int] = None,
        max_retries: Optional[int] = None,
        temperature: Optional[float] = None,
        document_files: Optional[Union[Any, List[Any]]] = None,  # 忽略，OpenAI 侧无需独立上传
        document_text: Optional[str] = None,
        context_info: Optional[str] = None
    ) -> Tuple[Dict[str, Any], int, int, int]:

        json_data, _, in_tok, out_tok, ttl = self._generate_with_schema_impl(
            prompt=prompt,
            schema=schema,
            seed=seed,
            max_retries=max_retries,
            temperature=temperature,
            document_text=document_text,
            context_info=context_info
        )
        return json_data, in_tok, out_tok, ttl

    def generate_text(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        seed: Optional[int] = None,
        max_retries: Optional[int] = None,
        temperature: Optional[float] = None,
        document_files: Optional[Union[Any, List[Any]]] = None,
        document_text: Optional[str] = None
    ) -> Tuple[str, int, int, int]:

        max_retries = max_retries or self.default_max_retries
        full_prompt = prompt
        if system_message:
            full_prompt = f"<sys>{system_message}</sys>\n{full_prompt}"
        if document_text:
            full_prompt = f"参考文档：\n{document_text}\n\n{full_prompt}"

        for attempt in range(max_retries):
            try:
                if self.debug_mode and attempt > 0:
                    print(f"[DEBUG] Text retry {attempt+1}/{max_retries}")

                self.call_count += 1
                resp = self.client.chat.completions.create(
                    model=self.config.model_name,
                    temperature=temperature or self.config.temperature,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": full_prompt},
                    ],
                )

                text = resp.choices[0].message.content or ""
                in_tok, out_tok, ttl_tok = self._extract_usage(resp)
                self.total_tokens += ttl_tok
                self.success_count += 1
                return text, in_tok, out_tok, ttl_tok

            except Exception as e:
                self.error_count += 1
                if attempt < max_retries - 1:
                    time.sleep(self.rate_limit_sleep)
                else:
                    raise LLMAPIError(f"Text generation failed: {e}")

    # ---------- core implementation ----------

    def _generate_with_schema_impl(
        self,
        prompt: str,
        schema: Dict[str, Any],
        seed: Optional[int],
        max_retries: Optional[int],
        temperature: Optional[float],
        document_text: Optional[str],
        context_info: Optional[str],
        functions: Optional[List[str]] = None,  # 预留，当前不走函数调用
    ) -> Tuple[Dict[str, Any], Dict[str, Any], int, int, int]:
        """
        先尝试 Structured Outputs (json_schema) → 失败降级 JSON mode → 失败再走解析修复
        返回：(json_data, function_history, in_tok, out_tok, total_tok)
        """
        max_retries = max_retries or self.default_max_retries

        enhanced_prompt = prompt
        if document_text:
            enhanced_prompt = f"参考文档：\n{document_text}\n\n任务要求：\n{enhanced_prompt}"
        if context_info:
            enhanced_prompt = f"上下文信息：\n{context_info}\n\n{enhanced_prompt}"

        # 1) Structured Outputs（模型需支持，如 gpt-4o/4o-mini 2024-08-06+）
        for attempt in range(max_retries):
            try:
                if self.debug_mode and attempt > 0:
                    print(f"[DEBUG] SO retry {attempt+1}/{max_retries}")

                self.call_count += 1
                resp = self.client.chat.completions.create(
                    model=self.config.model_name,
                    # temperature=temperature or self.config.temperature,
                    messages=[
                        {"role": "system", "content":
                         "You are an AUTOSAR assistant. Output ONLY JSON, strictly matching the schema."},
                        {"role": "user", "content": enhanced_prompt},
                    ],
                    response_format={
                        "type": "json_schema",
                        "json_schema": {
                            "name": "result",
                            "strict": True,
                            "schema": schema
                        }
                    },
                    seed=seed
                )

                text = resp.choices[0].message.content or ""
                try:
                    data = json.loads(text)
                except json.JSONDecodeError:
                    data = self._extract_json_from_text(text)

                in_tok, out_tok, ttl_tok = self._extract_usage(resp)
                self.total_tokens += ttl_tok
                self.success_count += 1
                return data, {}, in_tok, out_tok, ttl_tok

            except Exception as e:
                # 常见：不支持 json_schema → 降级到 JSON mode
                last_error = e
                if self.debug_mode:
                    print(f"[DEBUG] Structured Outputs failed: {e}")
                break  # 直接降级（不少代理会报 400/参数不支持）

        # 2) JSON mode：只保证“返回 JSON 对象”，不保证 schema 严格一致
        for attempt in range(max_retries):
            try:
                if self.debug_mode and attempt > 0:
                    print(f"[DEBUG] JSON mode retry {attempt+1}/{max_retries}")

                self.call_count += 1
                resp = self.client.chat.completions.create(
                    model=self.config.model_name,
                    # temperature=temperature or self.config.temperature,
                    messages=[
                        {"role": "system", "content":
                         "You are an AUTOSAR assistant. Output ONLY a valid JSON object."},
                        {"role": "user", "content": enhanced_prompt},
                    ],
                    response_format={"type": "json_object"},
                    seed=seed
                )
                text = resp.choices[0].message.content or ""

                try:
                    data = json.loads(text)
                except json.JSONDecodeError:
                    # 兜底修复 → 再解析
                    data = json.loads(self._repair_json_text(text))

                in_tok, out_tok, ttl_tok = self._extract_usage(resp)
                self.total_tokens += ttl_tok
                self.success_count += 1
                return data, {}, in_tok, out_tok, ttl_tok

            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    time.sleep(self.rate_limit_sleep)
                else:
                    # 最后再做一遍“全文修复”尝试
                    try:
                        data = json.loads(self._repair_json_text(text))
                        in_tok, out_tok, ttl_tok = self._extract_usage(resp)
                        self.total_tokens += ttl_tok
                        self.success_count += 1
                        return data, {}, in_tok, out_tok, ttl_tok
                    except Exception:
                        raise LLMAPIError(f"Generation failed: {last_error}")

    # ---------- helpers ----------

    def _normalize_base(self, url: str) -> str:
        if not url:
            return "https://api.openai-proxy.org/v1"
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        if not url.rstrip("/").endswith("/v1"):
            url = url.rstrip("/") + "/v1"
        return url


    def _extract_usage(self, resp) -> Tuple[int, int, int]:
        """
        兼容 chat.completions / responses 两种结构
        """
        try:
            # chat.completions
            if hasattr(resp, "usage") and resp.usage:
                pt = getattr(resp.usage, "prompt_tokens", 0) or getattr(resp.usage, "input_tokens", 0) or 0
                ct = getattr(resp.usage, "completion_tokens", 0) or getattr(resp.usage, "output_tokens", 0) or 0
                tt = getattr(resp.usage, "total_tokens", pt + ct)
                return pt, ct, tt
        except Exception:
            pass
        return 0, 0, 0

    def _enhance_prompt_for_json(self, prompt: str) -> str:
        return f"""
Return ONLY JSON matching the schema. 
No prose, no markdown. Escape quotes, use \\n for line breaks.
{prompt}
""".strip()

    # —— 以下是“宽松修复”以提高健壮性（解决 Unterminated string 等）
    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        try:
            return json.loads(text)
        except Exception:
            pass
        for pattern in [r'```json\s*(.*?)\s*```', r'```\s*(.*?)\s*```', r'\{[\s\S]*\}']:
            for m in re.findall(pattern, text, re.DOTALL):
                c = m.strip()
                for cand in (c, self._repair_json_text(c)):
                    try:
                        return json.loads(cand)
                    except Exception:
                        continue
        repaired = self._repair_json_text(text)
        return json.loads(repaired)

    def _repair_json_text(self, text: str) -> str:
        import re
        t = re.sub(r"```json\s*([\s\S]*?)\s*```", r"\1", text)
        t = re.sub(r"```\s*([\s\S]*?)\s*```", r"\1", t)
        if "{" in t and "}" in t:
            t = t[t.find("{"): t.rfind("}") + 1]
        t = t.replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'")
        t = re.sub(r",(\s*[}\]])", r"\1", t)  # 尾逗号
        out, in_str, esc = [], False, False
        for ch in t:
            if in_str:
                if esc:
                    out.append(ch); esc = False
                else:
                    if ch == "\\":
                        out.append(ch); esc = True
                    elif ch in ("\n", "\r"):
                        out.append("\\n")
                    else:
                        out.append(ch)
                if not esc and ch == '"':
                    in_str = False
            else:
                out.append(ch)
                if ch == '"':
                    in_str, esc = True, False
        return "".join(out)
