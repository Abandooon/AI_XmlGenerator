"""llm/gemini_client.py - Gemini API客户端

封装Gemini API调用，支持Response Schema、重试机制和文档处理
支持配置化的文件上传功能（默认关闭）
基于llm_xml_generator.py的实现进行优化
"""
import json
import time
import re
import traceback
from typing import Dict, Any, Tuple, Optional, List, Union, TYPE_CHECKING
import google.generativeai as genai
from ..config import CONFIG
from ..utils.exceptions import LLMAPIError

# 类型检查时的导入
if TYPE_CHECKING:
    # 仅在类型检查时尝试导入，运行时不会执行
    try:
        from google.generativeai.types import File as GeminiFile
    except ImportError:
        GeminiFile = Any
else:
    # 运行时使用Any类型，避免导入错误
    GeminiFile = Any


class GeminiClient:
    """Gemini API客户端 - 支持纯对话和文件上传两种模式"""

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

        # 调试模式
        self.debug_mode = CONFIG.debug_mode

        # 默认重试配置
        self.default_max_retries = 3
        self.default_base_delay = 1.0
        self.rate_limit_sleep = 0.5

        # 检查文件上传支持
        self._check_file_upload_support()

    def _check_file_upload_support(self):
        """检查并报告文件上传功能状态"""
        if self.enable_file_upload:
            try:
                # 尝试访问upload_file函数
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

        # 确保URL有正确的协议
        if not api_url.startswith(('http://', 'https://')):
            api_url = f"https://{api_url}"

        # 移除末尾的斜杠
        return api_url.rstrip('/')

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

        # 添加top_p（如果配置中存在）
        if hasattr(self.config, 'top_p'):
            config_params["top_p"] = top_p or self.config.top_p
        elif top_p is not None:
            config_params["top_p"] = top_p

        # 尝试添加seed（如果支持）
        if seed is not None:
            try:
                # 测试是否支持seed参数
                test_config = genai.types.GenerationConfig(seed=seed, **config_params)
                return test_config
            except (TypeError, AttributeError):
                # 不支持seed，忽略该参数
                if self.debug_mode:
                    print(f"[DEBUG] Current version doesn't support seed parameter")
                pass

        return genai.types.GenerationConfig(**config_params)

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

    def process_document(
        self,
        prompt: str,
        document_files: Optional[Union[Any, List[Any]]] = None,  # 使用Any避免类型错误
        document_text: Optional[str] = None,  # 新增：支持直接传入文档文本
        extract_content: bool = True
    ) -> Tuple[str, int, int, int]:
        """处理包含文档的请求（支持文件或文本两种方式）

        Args:
            prompt: 提示词
            document_files: 已上传的文档文件对象（仅在enable_file_upload=True时使用）
            document_text: 文档文本内容（纯对话模式使用）
            extract_content: 是否自动提取文档内容

        Returns:
            (响应文本, 输入tokens, 输出tokens, 总tokens)
        """

        # 纯对话模式：使用文档文本
        if not self.enable_file_upload or document_files is None:
            if document_text:
                # 构建带文档内容的提示词
                if extract_content:
                    full_prompt = f"""请先分析以下文档内容：

{document_text}

提取以下信息：
1. 文档中的功能需求和系统要求
2. 架构设计相关信息（如有）
3. 组件和接口描述（如有）
4. 性能和约束条件

基于以上信息以及下面的要求：
{prompt}"""
                else:
                    full_prompt = f"""参考文档：
{document_text}

要求：
{prompt}"""
            else:
                full_prompt = prompt

            # 使用纯文本生成
            generation_config = self._make_generation_config()

            for attempt in range(self.default_max_retries):
                try:
                    if self.debug_mode and attempt > 0:
                        print(f"[DEBUG] Document processing retry {attempt + 1}/{self.default_max_retries}")

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
                    if attempt < self.default_max_retries - 1:
                        time.sleep(self.rate_limit_sleep)
                    else:
                        raise LLMAPIError(f"Document processing failed: {str(e)}")

        # 文件上传模式（仅在明确启用且支持时使用）
        else:
            # 确保document_files是列表
            if document_files is not None and not isinstance(document_files, list):
                document_files = [document_files]

            # 构建内容列表
            content_parts = []

            # 如果需要提取文档内容，添加提取指令
            if extract_content and document_files:
                extract_prompt = """请先分析上传的文档，提取以下信息：
1. 文档中的功能需求和系统要求
2. 架构设计相关信息（如有）
3. 组件和接口描述（如有）
4. 性能和约束条件

然后基于这些信息以及下面的要求：
"""
                content_parts.append(extract_prompt + prompt)
            else:
                content_parts.append(prompt)

            # 添加文档文件
            if document_files:
                content_parts.extend(document_files)

            generation_config = self._make_generation_config()

            last_exception = None

            for attempt in range(self.default_max_retries):
                try:
                    if self.debug_mode and attempt > 0:
                        print(f"[DEBUG] Document processing retry {attempt + 1}/{self.default_max_retries}")

                    self.call_count += 1

                    # 调用Gemini处理文档
                    response = self.model.generate_content(
                        contents=content_parts,
                        generation_config=generation_config,
                    )

                    if not response.text:
                        raise LLMAPIError("Empty response from Gemini")

                    # 获取token使用情况
                    input_tokens, output_tokens, total_tokens = self._extract_token_usage(response)
                    self.total_tokens += total_tokens
                    self.success_count += 1

                    return response.text, input_tokens, output_tokens, total_tokens

                except Exception as e:
                    last_exception = e
                    self.error_count += 1

                    if attempt < self.default_max_retries - 1:
                        time.sleep(self.rate_limit_sleep)

            # 所有重试失败
            raise LLMAPIError(f"Document processing failed after {self.default_max_retries} attempts: {str(last_exception)}")

    def generate_with_schema(
        self,
        prompt: str,
        schema: Dict[str, Any],
        seed: Optional[int] = None,
        max_retries: Optional[int] = None,
        temperature: Optional[float] = None,
        document_files: Optional[Union[Any, List[Any]]] = None,  # 文件模式
        document_text: Optional[str] = None,  # 文本模式
        context_info: Optional[str] = None  # 额外上下文
    ) -> Tuple[Dict[str, Any], int, int, int]:
        """使用Response Schema生成结构化JSON，支持文档输入"""

        max_retries = max_retries or self.default_max_retries

        # 纯对话模式或无文件时的处理
        if not self.enable_file_upload or (document_files is None and document_text):
            # 构建增强的提示词
            enhanced_prompt = self._enhance_prompt_for_json(prompt)

            # 添加文档文本（如果有）
            if document_text:
                enhanced_prompt = f"""参考文档：
{document_text}

任务要求：
{enhanced_prompt}"""

            # 添加额外上下文（如果有）
            if context_info:
                enhanced_prompt = f"""上下文信息：
{context_info}

{enhanced_prompt}"""

            # 尝试使用Response Schema
            try:
                gemini_schema = self._convert_json_schema_to_gemini(schema)
                generation_config = genai.types.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=gemini_schema,
                    temperature=temperature or self.config.temperature,
                    max_output_tokens=self.config.max_output_tokens,
                )

                # 尝试添加seed
                if seed is not None:
                    try:
                        generation_config.seed = seed
                    except AttributeError:
                        pass

            except Exception as e:
                if self.debug_mode:
                    print(f"[DEBUG] Response Schema not supported, using text mode")
                # 降级到纯文本JSON生成
                return self._generate_json_text_mode_simple(
                    enhanced_prompt, schema, seed, max_retries, temperature
                )

            # 执行生成
            for attempt in range(max_retries):
                try:
                    if self.debug_mode and attempt > 0:
                        print(f"[DEBUG] Retry attempt {attempt + 1}/{max_retries}")

                    self.call_count += 1

                    response = self.model.generate_content(
                        contents=enhanced_prompt,
                        generation_config=generation_config,
                    )

                    if not response.text:
                        raise LLMAPIError("Empty response from Gemini")

                    # 解析JSON
                    try:
                        json_data = json.loads(response.text)
                    except json.JSONDecodeError:
                        json_data = self._extract_json_from_text(response.text)

                    input_tokens, output_tokens, total_tokens = self._extract_token_usage(response)
                    self.total_tokens += total_tokens
                    self.success_count += 1

                    return json_data, input_tokens, output_tokens, total_tokens

                except Exception as e:
                    self.error_count += 1
                    if self.debug_mode:
                        print(f"[DEBUG] Attempt {attempt + 1} failed: {str(e)}")

                    if attempt < max_retries - 1:
                        if any(err in str(e) for err in ['ProxyError', 'SSLError', 'ConnectionError', 'Timeout']):
                            delay = self.default_base_delay * (2 ** attempt)
                            time.sleep(delay)
                        else:
                            time.sleep(self.rate_limit_sleep)
                    else:
                        raise LLMAPIError(f"Generation failed: {str(e)}")

        # 文件上传模式（向后兼容）
        else:
            return self._generate_with_schema_file_mode(
                prompt, schema, seed, max_retries, temperature, document_files
            )

    def _generate_json_text_mode_simple(
        self,
        prompt: str,
        schema: Dict[str, Any],
        seed: Optional[int] = None,
        max_retries: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> Tuple[Dict[str, Any], int, int, int]:
        """简化的文本模式JSON生成（用于纯对话模式）"""

        max_retries = max_retries or self.default_max_retries

        # 构建要求直接输出JSON的提示词
        enhanced_prompt = f"""{prompt}

Please output valid JSON that conforms to this structure:
{json.dumps(schema, indent=2)[:2000]}...

Requirements:
1. Output ONLY valid JSON, no explanations
2. Follow the exact schema structure
3. Include all required fields
4. Use meaningful values

Begin JSON output:
"""

        generation_config = self._make_generation_config(seed, temperature)

        for attempt in range(max_retries):
            try:
                self.call_count += 1

                response = self.model.generate_content(
                    contents=enhanced_prompt,
                    generation_config=generation_config,
                )

                if not response.text:
                    raise LLMAPIError("Empty response from Gemini")

                # 提取JSON
                json_data = self._extract_json_from_text(response.text)

                # 获取token使用情况
                input_tokens, output_tokens, total_tokens = self._extract_token_usage(response)
                self.total_tokens += total_tokens
                self.success_count += 1

                return json_data, input_tokens, output_tokens, total_tokens

            except Exception as e:
                if attempt == max_retries - 1:
                    self.error_count += 1
                    raise LLMAPIError(f"Text mode generation failed: {str(e)}")

                time.sleep(self.rate_limit_sleep)

    def _generate_with_schema_file_mode(
        self,
        prompt: str,
        schema: Dict[str, Any],
        seed: Optional[int] = None,
        max_retries: Optional[int] = None,
        temperature: Optional[float] = None,
        document_files: Optional[Union[Any, List[Any]]] = None
    ) -> Tuple[Dict[str, Any], int, int, int]:
        """文件模式的schema生成（向后兼容）"""

        max_retries = max_retries or self.default_max_retries

        # 转换schema格式
        gemini_schema = self._convert_json_schema_to_gemini(schema)

        # 构建内容列表
        content_parts = []

        # 如果有文档，添加文档分析指令
        if document_files:
            if not isinstance(document_files, list):
                document_files = [document_files]

            doc_prompt = """请分析上传的文档，并结合文档内容和以下要求生成结构化输出：

"""
            content_parts.append(doc_prompt + self._enhance_prompt_for_json(prompt))
            content_parts.extend(document_files)
        else:
            content_parts.append(self._enhance_prompt_for_json(prompt))

        # 构建生成配置
        try:
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
                print(f"[DEBUG] Response Schema not supported in file mode")
            # 降级到文本模式
            return self._generate_json_text_mode(prompt, schema, seed, max_retries, temperature, document_files)

        last_exception = None

        for attempt in range(max_retries):
            try:
                if self.debug_mode and attempt > 0:
                    print(f"[DEBUG] Retry attempt {attempt + 1}/{max_retries}")

                self.call_count += 1

                response = self.model.generate_content(
                    contents=content_parts,
                    generation_config=generation_config,
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

                return json_data, input_tokens, output_tokens, total_tokens

            except Exception as e:
                last_exception = e
                self.error_count += 1

                if attempt < max_retries - 1:
                    if any(err in str(e) for err in ['ProxyError', 'SSLError', 'ConnectionError', 'Timeout']):
                        delay = self.default_base_delay * (2 ** attempt)
                        time.sleep(delay)
                    else:
                        time.sleep(self.rate_limit_sleep)

        raise LLMAPIError(f"All attempts failed: {str(last_exception)}")

    def _generate_json_text_mode(
        self,
        prompt: str,
        schema: Dict[str, Any],
        seed: Optional[int] = None,
        max_retries: Optional[int] = None,
        temperature: Optional[float] = None,
        document_files: Optional[Union[Any, List[Any]]] = None
    ) -> Tuple[Dict[str, Any], int, int, int]:
        """文本模式生成JSON（降级方案），支持文档输入"""

        max_retries = max_retries or self.default_max_retries

        # 构建要求直接输出JSON的提示词
        enhanced_prompt = f"""
{prompt}

Please output valid JSON that conforms to this structure:
{json.dumps(schema, indent=2)[:1000]}...

Requirements:
1. Output ONLY valid JSON, no explanations
2. Follow the exact schema structure
3. Include all required fields
4. Use meaningful values

Begin JSON output:
"""

        # 构建内容列表
        content_parts = []
        if document_files:
            if not isinstance(document_files, list):
                document_files = [document_files]
            content_parts.append("请分析文档并生成JSON输出：\n" + enhanced_prompt)
            content_parts.extend(document_files)
        else:
            content_parts.append(enhanced_prompt)

        generation_config = self._make_generation_config(seed, temperature)

        for attempt in range(max_retries):
            try:
                self.call_count += 1

                response = self.model.generate_content(
                    contents=content_parts,
                    generation_config=generation_config,
                )

                if not response.text:
                    raise LLMAPIError("Empty response from Gemini")

                # 提取JSON
                json_data = self._extract_json_from_text(response.text)

                # 获取token使用情况
                input_tokens, output_tokens, total_tokens = self._extract_token_usage(response)
                self.total_tokens += total_tokens
                self.success_count += 1

                return json_data, input_tokens, output_tokens, total_tokens

            except Exception as e:
                if attempt == max_retries - 1:
                    self.error_count += 1
                    raise LLMAPIError(f"Text mode generation failed: {str(e)}")

                time.sleep(self.rate_limit_sleep)

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

        # 文件上传模式
        else:
            # 构建内容列表
            content_parts = [full_prompt]
            if document_files:
                if not isinstance(document_files, list):
                    document_files = [document_files]
                content_parts.extend(document_files)

            generation_config = self._make_generation_config(seed, temperature)

            last_exception = None

            for attempt in range(max_retries):
                try:
                    if self.debug_mode and attempt > 0:
                        print(f"[DEBUG] Text generation retry {attempt + 1}/{max_retries}")

                    self.call_count += 1

                    response = self.model.generate_content(
                        contents=content_parts,
                        generation_config=generation_config,
                    )

                    if not response.text:
                        raise LLMAPIError("Empty response from Gemini")

                    input_tokens, output_tokens, total_tokens = self._extract_token_usage(response)
                    self.total_tokens += total_tokens
                    self.success_count += 1

                    return response.text, input_tokens, output_tokens, total_tokens

                except Exception as e:
                    last_exception = e
                    self.error_count += 1

                    if attempt < max_retries - 1:
                        if any(err in str(e) for err in ['ProxyError', 'SSLError', 'ConnectionError', 'Timeout']):
                            delay = self.default_base_delay * (2 ** attempt)
                            time.sleep(delay)
                        else:
                            time.sleep(self.rate_limit_sleep)

            raise LLMAPIError(f"Text generation failed after {max_retries} attempts: {str(last_exception)}")

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

    def test_connection(self) -> bool:
        """测试API连接"""
        try:
            if self.debug_mode:
                print("[TEST] Testing Gemini connection...")

            test_prompt = "Hello, please respond with 'OK' if you can see this message."
            response = self.model.generate_content(test_prompt)

            if response and response.text:
                if self.debug_mode:
                    print(f"[TEST] Connection successful. Response: {response.text[:100]}")
                return True
            else:
                if self.debug_mode:
                    print("[TEST] Connection failed: No response text")
                return False

        except Exception as e:
            if self.debug_mode:
                print(f"[TEST] Connection failed: {type(e).__name__}: {str(e)}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """获取客户端统计信息"""
        total_calls = max(self.call_count, 1)
        return {
            "mode": "file_upload" if self.enable_file_upload else "dialogue_only",
            "call_count": self.call_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "total_tokens": self.total_tokens,
            "success_rate": self.success_count / total_calls,
            "error_rate": self.error_count / total_calls,
            "avg_tokens_per_call": self.total_tokens / total_calls if total_calls > 0 else 0
        }

    def reset_stats(self):
        """重置统计信息"""
        self.call_count = 0
        self.success_count = 0
        self.error_count = 0
        self.total_tokens = 0