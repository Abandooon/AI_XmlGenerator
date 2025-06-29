# src/client/cloud_client.py - 简化版本，移除重复请求和后处理
import aiohttp
import asyncio
import time
import json
import os
from typing import Optional, Dict, Any, List
from pathlib import Path

from ..models.constraint_models import EnhancedGenerationRequest, CloudGenerationResponse
from ..utils.logger import get_logger

logger = get_logger(__name__)


class CloudServiceClient:
    """云端服务客户端 - 简化版本，只保留单次请求"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.cloud_config = config["cloud_service"]
        self.endpoint = self.cloud_config["internal_endpoint"]
        self.timeout = self.cloud_config["timeout"]
        self.api_type = self.cloud_config.get("api_type", "enhanced")
        self.model_name = self.cloud_config.get("model_name", "")
        self.session: Optional[aiohttp.ClientSession] = None

        # 🔥 输出配置
        self.output_config = config.get("output", {})
        self.outputs_dir = Path(self.output_config.get("outputs_dir", "./outputs"))
        self.save_raw_outputs = self.output_config.get("save_raw_outputs", True)

        # 确保输出目录存在
        if self.save_raw_outputs:
            self.outputs_dir.mkdir(parents=True, exist_ok=True)

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def connect(self):
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
            logger.info(f"Connected to cloud service at {self.endpoint} (API: {self.api_type})")

    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None

    async def enhanced_generate(self, request: EnhancedGenerationRequest) -> CloudGenerationResponse:
        """调用生成接口 - 统一的单次请求"""

        logger.info(f"🚀 Sending single request to {self.endpoint}/enhanced_generate")

        try:
            # 转换为字典
            request_dict = request.dict()

            # 发送请求
            async with self.session.post(
                    f"{self.endpoint}/enhanced_generate",
                    json=request_dict,
                    headers={"Content-Type": "application/json"}
            ) as response:

                logger.info(f"📡 HTTP response status: {response.status}")

                if response.status == 200:
                    response_data = await response.json()
                    logger.info(f"✅ Response received successfully")

                    # 🔥 保存原始输出到文件
                    if self.save_raw_outputs and response_data.get("raw_output"):
                        await self._save_raw_output(
                            request.request_id,
                            response_data["raw_output"],
                            response_data.get("generated_xml", "")
                        )

                    return CloudGenerationResponse(**response_data)
                else:
                    error_text = await response.text()
                    logger.error(f"❌ HTTP error response: {error_text}")
                    return CloudGenerationResponse(
                        request_id=request.request_id,
                        success=False,
                        error_message=f"HTTP {response.status}: {error_text}"
                    )

        except Exception as e:
            logger.error(f"❌ Exception in enhanced_generate: {e}")
            import traceback
            traceback.print_exc()
            return CloudGenerationResponse(
                request_id=request.request_id,
                success=False,
                error_message=f"Client Error: {str(e)}"
            )

    async def _save_raw_output(self, request_id: str, raw_output: str, generated_xml: str):
        """保存原始输出到文件"""
        try:
            # 创建时间戳目录
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            if self.output_config.get("create_timestamp_dirs", True):
                output_dir = self.outputs_dir / f"{timestamp}_{request_id[:8]}"
            else:
                output_dir = self.outputs_dir

            output_dir.mkdir(parents=True, exist_ok=True)

            # 保存原始输出
            raw_file = output_dir / f"raw_output_{request_id[:8]}.txt"
            with open(raw_file, 'w', encoding='utf-8') as f:
                f.write(raw_output)

            # 保存处理后的XML（如果有）
            if generated_xml and generated_xml != raw_output:
                xml_file = output_dir / f"generated_xml_{request_id[:8]}.xml"
                with open(xml_file, 'w', encoding='utf-8') as f:
                    f.write(generated_xml)

            logger.info(f"📁 Raw output saved to: {raw_file}")

        except Exception as e:
            logger.error(f"❌ Failed to save raw output: {e}")

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            if self.api_type == "vllm_native":
                # vLLM健康检查
                async with self.session.get(f"{self.endpoint}/v1/models") as response:
                    if response.status == 200:
                        models = await response.json()
                        return {
                            "status": "healthy",
                            "api_type": "vllm_native",
                            "models": models.get("data", [])
                        }
                    else:
                        return {"status": "unhealthy", "http_status": response.status}
            else:
                # 增强服务健康检查
                async with self.session.get(f"{self.endpoint}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        data["api_type"] = "enhanced"
                        return data
                    else:
                        return {"status": "unhealthy", "http_status": response.status}
        except Exception as e:
            return {"status": "error", "error": str(e), "api_type": self.api_type}