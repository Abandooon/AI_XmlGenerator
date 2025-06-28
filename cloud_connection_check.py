import asyncio
import aiohttp
import json


async def enhanced_service(base_url: str):
    """测试增强服务的专用端点"""
    print(f"🎯 Testing Enhanced Service at {base_url}")

    try:
        async with aiohttp.ClientSession() as session:
            # 测试根端点
            async with session.get(f"{base_url}/") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   Root: ✅ {data.get('service', 'Unknown')}")
                else:
                    print(f"   Root: ❌ {response.status}")

            # 测试健康端点
            async with session.get(f"{base_url}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    status = health_data.get('status', 'unknown')
                    print(f"   Health: ✅ {status}")
                    print(f"   vLLM Available: {health_data.get('vllm_available', False)}")
                    print(f"   Guided Generation: {health_data.get('guided_generation_supported', False)}")
                else:
                    print(f"   Health: ❌ {response.status}")

            # 测试增强生成端点
            test_request = {
                "request_id": "test-001",
                "prompt": "Generate a simple AUTOSAR component",
                "temperature": 0.7,
                "max_tokens": 100,
                "constraint_info": {
                    "fsm_enabled": False,
                    "gbnf_enabled": False,
                    "domain_constraints": {}
                },
                "autosar_context": {
                    "domain": "test",
                    "component_type": "APPLICATION-SW-COMPONENT-TYPE"
                }
            }

            async with session.post(f"{base_url}/enhanced_generate",
                                    json=test_request) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"   Enhanced Generate: ✅ Success: {result.get('success', False)}")
                elif response.status == 503:
                    print(f"   Enhanced Generate: ⚠️ Service unavailable (vLLM not ready)")
                else:
                    error_text = await response.text()
                    print(f"   Enhanced Generate: ❌ {response.status} - {error_text}")

    except Exception as e:
        print(f"❌ Enhanced service test failed: {e}")


async def main():
    # 只测试增强服务
    await enhanced_service("http://117.50.173.128:8000")


if __name__ == "__main__":
    asyncio.run(main())