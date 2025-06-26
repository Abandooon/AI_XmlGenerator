# src/generation/services/local_proxy_service.py
import asyncio
import aiohttp
from typing import Dict, Optional
import hashlib
import json
from ..models.request_models import GenerationRequest
from ..models.response_models import GenerationResponse
from ...validation.orchestrator.validation_orchestrator import ValidationOrchestrator
from ...core.cache.generation_cache import GenerationCache


class LocalProxyService:
    """本地代理服务"""

    def __init__(self, cloud_endpoint: str, cache_config: Dict, validator_config: Dict):
        """
        初始化本地代理服务

        Args:
            cloud_endpoint: 云端服务地址
            cache_config: 缓存配置
            validator_config: 验证器配置
        """
        self.cloud_endpoint = cloud_endpoint
        self.cache = GenerationCache(cache_config)
        self.validator = ValidationOrchestrator(validator_config)

    async def proxy_generate(self, request: GenerationRequest) -> Dict:
        """代理云端生成并执行本地验证"""

        # 1. 检查缓存
        request_hash = self._compute_request_hash(request)
        cached_result = self.cache.get_cached_result(request_hash)

        if cached_result:
            return {
                "generation_response": cached_result["generation_response"],
                "validation_results": cached_result["validation_results"],
                "cache_hit": True
            }

        # 2. 调用云端生成
        generation_response = await self._call_cloud_generation(request)

        if not generation_response:
            return {
                "error": "Cloud generation failed",
                "cache_hit": False
            }

        # 3. 执行本地验证
        validation_results = self.validator.execute_full_validation(
            generation_response.generated_xml,
            request.validation_level
        )

        # 4. 缓存结果
        result = {
            "generation_response": generation_response,
            "validation_results": validation_results,
            "cache_hit": False
        }

        self.cache.store_result(request_hash, result, ttl=3600)  # 1小时TTL

        return result

    async def _call_cloud_generation(self, request: GenerationRequest) -> Optional[GenerationResponse]:
        """调用云端生成服务"""

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                        f"{self.cloud_endpoint}/generate",
                        json=request.dict(),
                        timeout=aiohttp.ClientTimeout(total=30)
                ) as response:

                    if response.status == 200:
                        response_data = await response.json()
                        return GenerationResponse.parse_obj(response_data)
                    else:
                        print(f"Cloud service error: {response.status}")
                        return None

        except Exception as e:
            print(f"Cloud service call failed: {e}")
            return None

    def _compute_request_hash(self, request: GenerationRequest) -> str:
        """计算请求哈希用于缓存键"""

        # 序列化请求的关键字段
        key_data = {
            "prompt": request.prompt,
            "autosar_context": request.autosar_context,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "constraint_level": getattr(request, 'constraint_level', 'mixed')
        }

        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()