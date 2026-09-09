"""llm/gemini_client.py - Gemini API客户端

封装Gemini API调用，支持Response Schema、重试机制、文档处理和函数调用
支持配置化的文件上传功能（默认关闭）
基于llm_xml_generator.py的实现进行优化
"""
import json
import re
import time
from typing import Dict, Any, Tuple, Optional, List, Union, TYPE_CHECKING, Callable

import google.generativeai as genai

from ..config import CONFIG
from ..utils.exceptions import LLMAPIError

# 类型检查时的导入
if TYPE_CHECKING:
    try:
        from google.generativeai.types import File as GeminiFile
    except ImportError:
        GeminiFile = Any
else:
    GeminiFile = Any


class GeminiClient:
    """Gemini API客户端 - 支持纯对话、文件上传和函数调用"""

    def __init__(self):
        """初始化Gemini客户端"""
        self.config = CONFIG.llm

        # 从配置读取是否启用文件上传（默认False）
        self.enable_file_upload = getattr(self.config, 'enable_file_upload', False)

        # 配置Gemini
        api_endpoint = self._normalize_api_endpoint(self.config.llm_api_url)

        genai.configure(
            api_key=self.config.api_key,
            transport="rest",
            client_options={"api_endpoint": api_endpoint},
        )

        # 创建模型实例
        self.model = genai.GenerativeModel(self.config.model_name)

        # 性能监控
        self.call_count = 0
        self.total_tokens = 0
        self.error_count = 0
        self.success_count = 0
        self.function_call_count = 0

        # 调试模式
        self.debug_mode = CONFIG.debug_mode

        # 默认重试配置
        self.default_max_retries = 3
        self.default_base_delay = 1.0
        self.rate_limit_sleep = 0.5

        # 函数注册表
        self.registered_functions = {}
        self.function_implementations = {}

        # 检查文件上传支持
        self._check_file_upload_support()

    def _check_file_upload_support(self):
        """检查并报告文件上传功能状态"""
        if self.enable_file_upload:
            try:
                _ = genai.upload_file
                if self.debug_mode:
                    print("[DEBUG] File upload enabled and supported")
            except (AttributeError, ImportError):
                self.enable_file_upload = False
                if self.debug_mode:
                    print("[WARNING] File upload requested but not supported, falling back to dialogue mode")
        else:
            if self.debug_mode:
                print("[DEBUG] Running in dialogue-only mode (file upload disabled)")

    def _normalize_api_endpoint(self, api_url: str) -> str:
        """规范化API端点URL"""
        if not api_url:
            return "https://generativelanguage.googleapis.com"

        if not api_url.startswith(('http://', 'https://')):
            api_url = f"https://{api_url}"

        return api_url.rstrip('/')

    def register_function(self, name: str, parameters: Dict[str, Any],
                         implementation: Callable, description: str = ""):
        """注册函数供LLM调用

        Args:
            name: 函数名称
            parameters: 函数参数schema（JSON Schema格式）
            implementation: 函数实现
            description: 函数描述
        """
        # 转换为Gemini函数格式
        function_declaration = genai.types.FunctionDeclaration(
            name=name,
            description=description,
            parameters=parameters
        )

        self.registered_functions[name] = function_declaration
        self.function_implementations[name] = implementation

        if self.debug_mode:
            print(f"[DEBUG] Registered function: {name}")

    def clear_functions(self):
        """清空已注册的函数"""
        self.registered_functions.clear()
        self.function_implementations.clear()

    def _make_generation_config(
        self,
        seed: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_output_tokens: Optional[int] = None
    ) -> genai.types.GenerationConfig:
        """创建生成配置，兼容不同版本的 google-generativeai"""

        config_params = {
            "temperature": temperature or self.config.temperature,
            "max_output_tokens": max_output_tokens or self.config.max_output_tokens,
        }

        if hasattr(self.config, 'top_p'):
            config_params["top_p"] = top_p or self.config.top_p
        elif top_p is not None:
            config_params["top_p"] = top_p

        if seed is not None:
            try:
                test_config = genai.types.GenerationConfig(seed=seed, **config_params)
                return test_config
            except (TypeError, AttributeError):
                if self.debug_mode:
                    print(f"[DEBUG] Current version doesn't support seed parameter")
                pass

        return genai.types.GenerationConfig(**config_params)

    def generate_with_functions(
        self,
        prompt: str,
        functions: Optional[List[str]] = None,
        system_message: Optional[str] = None,
        temperature: Optional[float] = None,
        max_retries: Optional[int] = None
    ) -> Tuple[str, Dict[str, Any], int, int, int]:
        """使用函数调用生成内容

        Args:
            prompt: 提示词
            functions: 要启用的函数名称列表（None表示使用所有已注册函数）
            system_message: 系统消息
            temperature: 生成温度
            max_retries: 最大重试次数

        Returns:
            (最终响应文本, 函数调用记录, 输入tokens, 输出tokens, 总tokens)
        """
        max_retries = max_retries or self.default_max_retries

        # 准备函数工具
        if functions:
            active_functions = [self.registered_functions[name]
                              for name in functions if name in self.registered_functions]
        else:
            active_functions = list(self.registered_functions.values())

        if not active_functions:
            # 没有函数时降级到普通生成
            response_text, input_tokens, output_tokens, total_tokens = self.generate_text(
                prompt, system_message, temperature=temperature, max_retries=max_retries
            )
            return response_text, {}, input_tokens, output_tokens, total_tokens

        # 创建工具集
        tools = [genai.types.Tool(function_declarations=active_functions)]

        # 准备完整提示词
        if system_message:
            full_prompt = f"<sys>{system_message}</sys>\n{prompt}"
        else:
            full_prompt = prompt

        generation_config = self._make_generation_config(temperature=temperature)

        # 创建支持函数调用的模型
        model_with_tools = genai.GenerativeModel(
            model_name=self.config.model_name,
            tools=tools
        )

        function_call_history = {}
        chat = model_with_tools.start_chat(enable_automatic_function_calling=True)

        for attempt in range(max_retries):
            try:
                if self.debug_mode and attempt > 0:
                    print(f"[DEBUG] Function generation retry {attempt + 1}/{max_retries}")

                self.call_count += 1

                # 发送消息并处理函数调用
                response = chat.send_message(
                    full_prompt,
                    generation_config=generation_config
                )

                # 处理函数调用
                for part in response.parts:
                    if hasattr(part, 'function_call'):
                        fn_call = part.function_call
                        fn_name = fn_call.name
                        fn_args = dict(fn_call.args)

                        if self.debug_mode:
                            print(f"[DEBUG] Function called: {fn_name} with args: {fn_args}")

                        # 执行函数
                        if fn_name in self.function_implementations:
                            try:
                                result = self.function_implementations[fn_name](**fn_args)
                                function_call_history[fn_name] = {
                                    "args": fn_args,
                                    "result": result
                                }
                                self.function_call_count += 1

                                # 发送函数响应给模型
                                response = chat.send_message(
                                    genai.types.FunctionResponse(
                                        name=fn_name,
                                        response={"result": result}
                                    )
                                )
                            except Exception as e:
                                if self.debug_mode:
                                    print(f"[DEBUG] Function execution error: {e}")
                                # 发送错误响应
                                response = chat.send_message(
                                    genai.types.FunctionResponse(
                                        name=fn_name,
                                        response={"error": str(e)}
                                    )
                                )

                # 获取最终响应
                final_text = response.text
                input_tokens, output_tokens, total_tokens = self._extract_token_usage(response)

                self.total_tokens += total_tokens
                self.success_count += 1

                return final_text, function_call_history, input_tokens, output_tokens, total_tokens

            except Exception as e:
                self.error_count += 1
                if self.debug_mode:
                    print(f"[DEBUG] Attempt {attempt + 1} failed: {str(e)}")

                if attempt < max_retries - 1:
                    time.sleep(self.rate_limit_sleep)
                else:
                    raise LLMAPIError(f"Function generation failed: {str(e)}")

    def generate_with_schema_and_functions(
        self,
        prompt: str,
        schema: Dict[str, Any],
        functions: Optional[List[str]] = None,
        seed: Optional[int] = None,
        max_retries: Optional[int] = None,
        temperature: Optional[float] = None,
        document_files: Optional[Union[Any, List[Any]]] = None,
        document_text: Optional[str] = None,
        context_info: Optional[str] = None
    ) -> Tuple[Dict[str, Any], Dict[str, Any], int, int, int]:
        """结合Schema和函数调用的生成

        Returns:
            (JSON响应, 函数调用记录, 输入tokens, 输出tokens, 总tokens)
        """
        max_retries = max_retries or self.default_max_retries

        # 准备函数工具
        if functions:
            active_functions = [self.registered_functions[name]
                              for name in functions if name in self.registered_functions]
        else:
            active_functions = list(self.registered_functions.values())

        # 如果有函数，创建带工具的模型
        if active_functions:
            tools = [genai.types.Tool(function_declarations=active_functions)]
            model = genai.GenerativeModel(
                model_name=self.config.model_name,
                tools=tools
            )
        else:
            model = self.model

        # 增强提示词
        enhanced_prompt = self._enhance_prompt_for_json(prompt)

        if document_text:
            enhanced_prompt = f"""参考文档：
{document_text}

任务要求：
{enhanced_prompt}"""

        if context_info:
            enhanced_prompt = f"""上下文信息：
{context_info}

{enhanced_prompt}"""

        # 准备生成配置
        try:
            gemini_schema = self._convert_json_schema_to_gemini(schema)
            generation_config = genai.types.GenerationConfig(
                response_mime_type="application/json",
                response_schema=gemini_schema,
                temperature=temperature or self.config.temperature,
                max_output_tokens=self.config.max_output_tokens,
            )

            if seed is not None:
                try:
                    generation_config.seed = seed
                except AttributeError:
                    pass

        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] Response Schema not supported, using text mode")
            return self._generate_json_text_mode_simple(
                enhanced_prompt, schema, seed, max_retries, temperature
            )

        function_call_history = {}

        for attempt in range(max_retries):
            try:
                if self.debug_mode and attempt > 0:
                    print(f"[DEBUG] Retry attempt {attempt + 1}/{max_retries}")

                self.call_count += 1

                # 如果有函数，使用chat模式处理函数调用
                if active_functions:
                    chat = model.start_chat(enable_automatic_function_calling=True)
                    response = chat.send_message(
                        enhanced_prompt,
                        generation_config=generation_config
                    )

                    # 处理函数调用
                    for part in response.parts:
                        if hasattr(part, 'function_call'):
                            fn_call = part.function_call
                            fn_name = fn_call.name
                            fn_args = dict(fn_call.args)

                            if fn_name in self.function_implementations:
                                try:
                                    result = self.function_implementations[fn_name](**fn_args)
                                    function_call_history[fn_name] = {
                                        "args": fn_args,
                                        "result": result
                                    }
                                    self.function_call_count += 1

                                    response = chat.send_message(
                                        genai.types.FunctionResponse(
                                            name=fn_name,
                                            response={"result": result}
                                        )
                                    )
                                except Exception as e:
                                    if self.debug_mode:
                                        print(f"[DEBUG] Function error: {e}")
                else:
                    # 无函数的普通生成
                    response = model.generate_content(
                        contents=enhanced_prompt,
                        generation_config=generation_config
                    )

                if not response.text:
                    raise LLMAPIError("Empty response from Gemini")

                try:
                    json_data = json.loads(response.text)
                except json.JSONDecodeError:
                    json_data = self._extract_json_from_text(response.text)

                input_tokens, output_tokens, total_tokens = self._extract_token_usage(response)
                self.total_tokens += total_tokens
                self.success_count += 1

                return json_data, function_call_history, input_tokens, output_tokens, total_tokens

            except Exception as e:
                self.error_count += 1
                if attempt < max_retries - 1:
                    time.sleep(self.rate_limit_sleep)
                else:
                    raise LLMAPIError(f"Generation failed: {str(e)}")


    def _convert_json_schema_to_gemini(self, json_schema: Dict) -> Dict:
        """将JSON Schema转换为Gemini Response Schema格式"""

        def convert_type(json_type: str) -> str:
            """转换类型名称"""
            type_mapping = {
                "object": "OBJECT",
                "array": "ARRAY",
                "string": "STRING",
                "number": "NUMBER",
                "integer": "INTEGER",
                "boolean": "BOOLEAN",
                "null": "NULL"
            }
            return type_mapping.get(json_type, "STRING")

        def clean_schema(obj: Dict) -> Dict:
            """清理不支持的字段"""
            # 移除Gemini不支持的字段
            unsupported_fields = ["$schema", "title", "$ref", "additionalProperties"]
            for field in unsupported_fields:
                obj.pop(field, None)
            return obj

        def convert_schema_object(obj: Dict) -> Dict:
            """递归转换schema对象"""
            # 先清理
            obj = clean_schema(obj)
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

            # 处理默认值
            if "default" in obj:
                result["default"] = obj["default"]

            return result

        # 清理并转换
        cleaned_schema = clean_schema(json_schema.copy())
        return convert_schema_object(cleaned_schema)

    def _extract_token_usage(self, response) -> Tuple[int, int, int]:
        """从响应中提取token使用情况"""
        try:
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                input_tokens = getattr(usage, 'prompt_token_count', 0)
                output_tokens = getattr(usage, 'candidates_token_count', 0)
                total_tokens = getattr(usage, 'total_token_count', input_tokens + output_tokens)
                return input_tokens, output_tokens, total_tokens
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] Failed to extract token usage: {e}")
        return 0, 0, 0

    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """从文本中提取JSON内容"""

        # 尝试直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 尝试查找JSON代码块
        json_patterns = [
            r'```json\s*(.*?)\s*```',  # ```json ... ```
            r'```\s*(.*?)\s*```',       # ``` ... ```
            r'\{[\s\S]*\}',             # { ... }
        ]

        for pattern in json_patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                try:
                    # 清理匹配的文本
                    cleaned = match.strip()
                    return json.loads(cleaned)
                except json.JSONDecodeError:
                    continue

        raise ValueError(f"No valid JSON found in response: {text[:500]}...")

    def _enhance_prompt_for_json(self, prompt: str) -> str:
        """增强JSON生成的提示词"""
        return f"""
You are an AUTOSAR ASW component assistant. Generate JSON content that strictly follows the provided schema.

{prompt}

Important requirements:
1. The response must be valid JSON
2. Follow the exact structure defined in the schema
3. Use correct AUTOSAR naming conventions
4. Include all required fields
5. Generate realistic and meaningful values
6. Ensure all UUIDs are unique
7. Use PascalCase for component names
8. Follow AUTOSAR standards for all elements
"""

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
        """生成纯文本，支持文档输入"""

        max_retries = max_retries or self.default_max_retries

        # 构建完整提示词
        if system_message:
            full_prompt = f"<sys>{system_message}</sys>\n{prompt}"
        else:
            full_prompt = prompt

        # 纯对话模式：添加文档文本
        if not self.enable_file_upload or document_files is None:
            if document_text:
                full_prompt = f"""参考文档：
{document_text}

{full_prompt}"""

            generation_config = self._make_generation_config(seed, temperature)

            for attempt in range(max_retries):
                try:
                    if self.debug_mode and attempt > 0:
                        print(f"[DEBUG] Text generation retry {attempt + 1}/{max_retries}")

                    self.call_count += 1

                    response = self.model.generate_content(
                        contents=full_prompt,
                        generation_config=generation_config,
                    )

                    if not response.text:
                        raise LLMAPIError("Empty response from Gemini")

                    input_tokens, output_tokens, total_tokens = self._extract_token_usage(response)
                    self.total_tokens += total_tokens
                    self.success_count += 1

                    return response.text, input_tokens, output_tokens, total_tokens

                except Exception as e:
                    self.error_count += 1
                    if attempt < max_retries - 1:
                        if any(err in str(e) for err in ['ProxyError', 'SSLError', 'ConnectionError', 'Timeout']):
                            delay = self.default_base_delay * (2 ** attempt)
                            time.sleep(delay)
                        else:
                            time.sleep(self.rate_limit_sleep)
                    else:
                        raise LLMAPIError(f"Text generation failed: {str(e)}")
        else:
            # 文件上传模式实现（保持原有逻辑）
            pass

    def generate_with_schema(
        self,
        prompt: str,
        schema: Dict[str, Any],
        seed: Optional[int] = None,
        max_retries: Optional[int] = None,
        temperature: Optional[float] = None,
        document_files: Optional[Union[Any, List[Any]]] = None,
        document_text: Optional[str] = None,
        context_info: Optional[str] = None
    ) -> Tuple[Dict[str, Any], int, int, int]:
        """使用Response Schema生成结构化JSON（向后兼容）"""

        # 调用新的带函数支持的方法，但不启用任何函数
        json_data, _, input_tokens, output_tokens, total_tokens = \
            self.generate_with_schema_and_functions(
                prompt=prompt,
                schema=schema,
                functions=None,  # 不启用函数
                seed=seed,
                max_retries=max_retries,
                temperature=temperature,
                document_files=document_files,
                document_text=document_text,
                context_info=context_info
            )

        return json_data, input_tokens, output_tokens, total_tokens

    def get_stats(self) -> Dict[str, Any]:
        """获取客户端统计信息"""
        total_calls = max(self.call_count, 1)
        return {
            "mode": "file_upload" if self.enable_file_upload else "dialogue_only",
            "call_count": self.call_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "function_call_count": self.function_call_count,
            "total_tokens": self.total_tokens,
            "registered_functions": len(self.registered_functions),
            "success_rate": self.success_count / total_calls,
            "error_rate": self.error_count / total_calls,
            "avg_tokens_per_call": self.total_tokens / total_calls if total_calls > 0 else 0
        }