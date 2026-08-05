from pathlib import Path
from typing import Optional, Dict, Any

import aiohttp
from src.client.constraint_models import EnhancedGenerationRequest, CloudGenerationResponse

from ..utils.logger import get_logger

logger = get_logger(__name__)


class CloudServiceClient:
    """简化的云端服务客户端"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.cloud_config = config["cloud_service"]
        self.endpoint = self.cloud_config["internal_endpoint"]
        self.timeout = self.cloud_config["timeout"]
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def connect(self):
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)

    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None

    async def enhanced_generate(self, request: EnhancedGenerationRequest) -> CloudGenerationResponse:
        """发送生成请求"""
        logger.info(f"Sending request to {self.endpoint}/enhanced_generate")

        try:
            request_dict = request.dict()

            async with self.session.post(
                    f"{self.endpoint}/enhanced_generate",
                    json=request_dict,
                    headers={"Content-Type": "application/json"}
            ) as response:

                if response.status == 200:
                    response_data = await response.json()

                    # 简单保存原始输出
                    if response_data.get("raw_output"):
                        output_file = Path("outputs") / f"raw_output_{request.request_id[:8]}.txt"
                        output_file.parent.mkdir(exist_ok=True)
                        with open(output_file, 'w', encoding='utf-8') as f:
                            f.write(response_data["raw_output"])

                    return CloudGenerationResponse(**response_data)
                else:
                    error_text = await response.text()
                    return CloudGenerationResponse(
                        request_id=request.request_id,
                        success=False,
                        error_message=f"HTTP {response.status}: {error_text}"
                    )

        except Exception as e:
            logger.error(f"Request failed: {e}")
            return CloudGenerationResponse(
                request_id=request.request_id,
                success=False,
                error_message=f"Client Error: {str(e)}"
            )