# scripts/test_client.py
# !/usr/bin/env python3
import asyncio
import aiohttp
import json
import sys


async def test_cloud_service():
    """测试云端生成服务"""

    base_url = "http://10.60.232.92:8000"  # 内网地址

    # 测试健康检查
    print("Testing health check...")
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{base_url}/health") as response:
            health_data = await response.json()
            print(f"Health check: {health_data}")

            if not health_data.get("initialized", False):
                print("Service not initialized, trying to initialize...")
                async with session.post(f"{base_url}/initialize") as init_response:
                    init_data = await init_response.json()
                    print(f"Initialization: {init_data}")

    # 测试生成请求
    print("\nTesting XML generation...")

    test_request = {
        "prompt": "Generate AUTOSAR timing event with period 100ms",
        "autosar_context": {
            "domain": "timing",
            "complexity": "simple",
            "elements": ["timing-event", "period"]
        },
        "temperature": 0.7,
        "max_tokens": 1024,
        "constraint_level": "simple",
        "validation_level": "structure"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
                f"{base_url}/generate",
                json=test_request,
                timeout=aiohttp.ClientTimeout(total=60)
        ) as response:

            if response.status == 200:
                result = await response.json()
                print(f"Generation successful!")
                print(f"Request ID: {result.get('request_id')}")
                print(f"Generated XML (first 500 chars):")
                print(result.get('generated_xml', '')[:500])
                print(f"Metadata: {result.get('metadata', {})}")
                print(f"Performance: {result.get('performance', {})}")
            else:
                error_text = await response.text()
                print(f"Generation failed: {response.status}")
                print(f"Error: {error_text}")


if __name__ == "__main__":
    asyncio.run(test_cloud_service())