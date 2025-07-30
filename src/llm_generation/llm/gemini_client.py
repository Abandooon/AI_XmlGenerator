"""llm/gemini_client.py - Gemini API客户端

封装Gemini API调用，支持JSON Schema和重试机制
"""
import json
import time
from typing import Dict, Any, Tuple, Optional
import google.generativeai as genai
from ..config import CONFIG
from ..utils.exceptions import LLMAPIError
from ..utils.validators import validate_json_schema


class GeminiClient:
    """Gemini API客户端"""

    def __init__(self):
        """初始化Gemini客户端"""
        self.config = CONFIG.llm

        # 配置Gemini
        genai.configure(
            api_key=self.config.api_key,
            transport="rest",
            client_options={"api_endpoint": self.config.api_base},
        )

        # 创建模型实例
        self.model = genai.GenerativeModel(self.config.model_name)

        # 性能监控
        self.call_count = 0
        self.total_tokens = 0
        self.error_count = 0

    def _make_generation_config(self, seed: Optional[int] = None) -> genai.types.GenerationConfig:
        """创建生成配置"""
        config_params = {
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "max_output_tokens": self.config.max_output_tokens,
        }

        # 添加seed（如果支持）
        if seed is not None:
            try:
                config_params["seed"] = seed
            except (TypeError, AttributeError):
                # 老版本不支持seed参数
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
                "boolean": "BOOLEAN"
            }
            return type_mapping.get(json_type, "STRING")

        def convert_schema_object(obj: Dict) -> Dict:
            """递归转换schema对象"""
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

        return convert_schema_object(json_schema)

    def _extract_token_usage(self, response) -> Tuple[int, int, int]:
        """从响应中提取token使用情况"""
        try:
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                input_tokens = getattr(usage, 'prompt_token_count', 0)
                output_tokens = getattr(usage, 'candidates_token_count', 0)
                total_tokens = getattr(usage, 'total_token_count', input_tokens + output_tokens)
                return input_tokens, output_tokens, total_tokens
        except Exception:
            pass
        return 0, 0, 0

    def generate_with_schema(
            self,
            prompt: str,
            schema: Dict[str, Any],
            seed: Optional[int] = None,
            max_retries: int = 3
    ) -> Tuple[Dict[str, Any], int, int, int]:
        """使用Response Schema生成结构化JSON"""

        # 转换schema格式
        gemini_schema = self._convert_json_schema_to_gemini(schema)

        # 构建生成配置
        generation_config = genai.types.GenerationConfig(
            response_mime_type="application/json",
            response_schema=gemini_schema,
            temperature=self.config.temperature,
            top_p=self.config.top_p,
            max_output_tokens=self.config.max_output_tokens,
        )

        # 添加seed
        if seed is not None:
            try:
                generation_config.seed = seed
            except AttributeError:
                pass

        # 增强提示词
        enhanced_prompt = f"""
You are an AUTOSAR ASW component assistant. Generate JSON content that strictly follows the provided schema.

{prompt}

Important requirements:
1. The response must be valid JSON
2. Follow the exact structure defined in the schema  
3. Use correct AUTOSAR naming conventions
4. Include all required fields
5. Generate realistic and meaningful values
"""

        for attempt in range(max_retries):
            try:
                self.call_count += 1

                # 调用Gemini
                response = self.model.generate_content(
                    contents=enhanced_prompt,
                    generation_config=generation_config,
                )

                if not response.text:
                    raise LLMAPIError("Gemini返回空响应")

                # 解析JSON
                try:
                    json_data = json.loads(response.text)
                except json.JSONDecodeError as e:
                    # 尝试提取JSON部分
                    import re
                    json_match = re.search(r'\{[\s\S]*\}', response.text)
                    if json_match:
                        json_data = json.loads(json_match.group(0))
                    else:
                        raise LLMAPIError(f"响应中没有有效的JSON: {response.text[:500]}")

                # 验证schema
                is_valid, errors = validate_json_schema(json_data, schema)
                if not is_valid and attempt < max_retries - 1:
                    if CONFIG.debug_mode:
                        print(f"[DEBUG] Schema验证失败，重试 {attempt + 1}/{max_retries}: {errors[:3]}")
                    continue

                # 获取token使用情况
                input_tokens, output_tokens, total_tokens = self._extract_token_usage(response)
                self.total_tokens += total_tokens

                return json_data, input_tokens, output_tokens, total_tokens

            except Exception as e:
                if attempt == max_retries - 1:
                    self.error_count += 1
                    raise LLMAPIError(f"Gemini调用失败: {str(e)}")

                # 指数退避
                wait_time = (2 ** attempt) * 1.0
                if CONFIG.debug_mode:
                    print(f"[DEBUG] API调用失败，{wait_time:.1f}s后重试: {str(e)}")
                time.sleep(wait_time)

        raise LLMAPIError("超过最大重试次数")

    def generate_text(
            self,
            prompt: str,
            system_message: Optional[str] = None,
            seed: Optional[int] = None,
            max_retries: int = 3
    ) -> Tuple[str, int, int, int]:
        """生成纯文本"""

        # 构建完整提示词
        if system_message:
            full_prompt = f"<sys>{system_message}</sys>\n{prompt}"
        else:
            full_prompt = prompt

        generation_config = self._make_generation_config(seed)

        for attempt in range(max_retries):
            try:
                self.call_count += 1

                response = self.model.generate_content(
                    contents=full_prompt,
                    generation_config=generation_config,
                )

                if not response.text:
                    raise LLMAPIError("Gemini返回空响应")

                # 获取token使用情况
                input_tokens, output_tokens, total_tokens = self._extract_token_usage(response)
                self.total_tokens += total_tokens

                return response.text, input_tokens, output_tokens, total_tokens

            except Exception as e:
                if attempt == max_retries - 1:
                    self.error_count += 1
                    raise LLMAPIError(f"Gemini调用失败: {str(e)}")

                wait_time = (2 ** attempt) * 1.0
                time.sleep(wait_time)

        raise LLMAPIError("超过最大重试次数")

    def test_connection(self) -> bool:
        """测试API连接"""
        try:
            response = self.model.generate_content("Hello, please respond with 'OK'.")
            return response.text and "OK" in response.text
        except Exception as e:
            if CONFIG.debug_mode:
                print(f"[DEBUG] API连接测试失败: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """获取客户端统计信息"""
        return {
            "call_count": self.call_count,
            "total_tokens": self.total_tokens,
            "error_count": self.error_count,
            "error_rate": self.error_count / max(self.call_count, 1)
        }