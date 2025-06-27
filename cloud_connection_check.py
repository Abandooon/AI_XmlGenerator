# cloud_connection_check.py
import asyncio
import aiohttp
import json


async def multiple_endpoints():
    """测试多个端点"""
    endpoints = [
        "http://10.60.232.92:8000",  # 内网地址
        "http://117.50.189.102:8000",  # 外网地址（从配置文件看到的）
    ]

    for endpoint in endpoints:
        print(f"\n🔍 Testing endpoint: {endpoint}")

        try:
            async with aiohttp.ClientSession() as session:
                # 设置更长的超时时间
                timeout = aiohttp.ClientTimeout(total=30, connect=10)

                async with session.get(f"{endpoint}/health", timeout=timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ SUCCESS on {endpoint}")
                        print(f"   Response: {data}")
                        return endpoint, True
                    else:
                        print(f"❌ HTTP Error {response.status} on {endpoint}")

        except aiohttp.ClientConnectorError as e:
            print(f"❌ Connection Error on {endpoint}: {e}")
        except asyncio.TimeoutError:
            print(f"❌ Timeout on {endpoint}")
        except Exception as e:
            print(f"❌ Unexpected Error on {endpoint}: {e}")

    return None, False


async def main():
    print("🚀 Testing multiple cloud endpoints...")
    endpoint, success = await multiple_endpoints()

    if success:
        print(f"\n🎉 Found working endpoint: {endpoint}")
    else:
        print(f"\n💥 All endpoints failed. Cloud service may be down.")


if __name__ == "__main__":
    asyncio.run(main())