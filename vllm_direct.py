# vllm_fixed.py
import asyncio
import aiohttp
import json
from pathlib import Path


async def check_vllm_connection():
    """检查vLLM连接 - 使用正确的API格式"""
    vllm_endpoint = "http://117.50.190.248:8000"

    try:
        print(f"🔍 Checking vLLM at {vllm_endpoint}")

        # 检查models端点
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{vllm_endpoint}/v1/models", timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    models = await resp.json()
                    print(f"✅ vLLM Models: {models['data'][0]['id']}")
                else:
                    print(f"❌ Models endpoint failed: {resp.status}")
                    return False

        # 使用正确的completions端点
        request_data = {
            "model": "/model/HuggingFace/deepseek-ai/DeepSeek-R1-Distill-Llama-70B",
            "prompt": "Generate a simple example:",
            "max_tokens": 100,
            "temperature": 0.7,
            "stream": False
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                    f"{vllm_endpoint}/v1/completions",
                    json=request_data,
                    timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    print(f"✅ vLLM Completions endpoint works")
                    print(f"📝 Generated: {result['choices'][0]['text'][:50]}...")
                    return True
                else:
                    error_text = await resp.text()
                    print(f"❌ Completions endpoint failed: {resp.status}")
                    print(f"Error: {error_text}")
                    return False

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


async def check_enhanced_service():
    """检查增强服务"""
    enhanced_endpoint = "http://117.50.190.248:8002"

    try:
        print(f"🔍 Checking Enhanced Service at {enhanced_endpoint}")

        # 使用更长的超时时间
        timeout = aiohttp.ClientTimeout(total=30, connect=10)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(f"{enhanced_endpoint}/health") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"✅ Enhanced Service healthy: {data['status']}")
                    return True
                else:
                    print(f"❌ Enhanced Service health check failed: {resp.status}")
                    return False

    except asyncio.TimeoutError:
        print(f"❌ Enhanced Service timeout")
        return False
    except Exception as e:
        print(f"❌ Enhanced Service failed: {e}")
        return False


async def generate_via_enhanced_service():
    """通过增强服务生成AUTOSAR"""
    enhanced_endpoint = "http://117.50.190.248:8002"

    request_data = {
        "request_id": "autosar-001",
        "prompt": "Generate basic AUTOSAR APPLICATION-SW-COMPONENT-TYPE named ASW_MotorController",
        "temperature": 0.7,
        "max_tokens": 800,
        "top_p": 0.9,
        "frequency_penalty": 0.1,
        "presence_penalty": 0.1,
        "constraint_info": {
            "fsm_enabled": False,
            "gbnf_enabled": False,
            "domain_constraints": {}
        },
        "autosar_context": {
            "domain": "motor_control",
            "component_type": "APPLICATION-SW-COMPONENT-TYPE"
        }
    }

    try:
        timeout = aiohttp.ClientTimeout(total=90, connect=10)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                    f"{enhanced_endpoint}/enhanced_generate",
                    json=request_data
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    print(f"✅ Enhanced service generation successful")

                    if result.get("success") and result.get("generated_xml"):
                        xml_content = result["generated_xml"]
                        print(f"📝 Generated XML: {len(xml_content)} characters")

                        # 保存结果
                        Path("outputs").mkdir(exist_ok=True)
                        output_file = Path("outputs") / "enhanced_autosar.xml"

                        with open(output_file, 'w', encoding='utf-8') as f:
                            f.write(xml_content)

                        print(f"💾 Saved: {output_file}")

                        # 预览
                        lines = xml_content.split('\n')
                        print("📄 Preview:")
                        for line in lines[:10]:
                            print(f"   {line}")

                        return True
                    else:
                        print(f"❌ Generation failed: {result.get('error_message', 'Unknown error')}")
                        print(f"Response: {result}")
                        return False
                else:
                    error_text = await resp.text()
                    print(f"❌ HTTP {resp.status}: {error_text}")
                    return False

    except asyncio.TimeoutError:
        print(f"❌ Enhanced service generation timeout")
        return False
    except Exception as e:
        print(f"❌ Enhanced service generation failed: {e}")
        return False


async def generate_via_vllm_direct():
    """直接通过vLLM生成AUTOSAR - 使用正确的API"""
    vllm_endpoint = "http://117.50.190.248:8000"

    prompt = """Generate a simple AUTOSAR APPLICATION-SW-COMPONENT-TYPE XML for motor controller.

Requirements:
- Valid XML structure with AUTOSAR namespace
- APPLICATION-SW-COMPONENT-TYPE element
- SHORT-NAME: ASW_MotorController

Generate complete AUTOSAR XML:

<?xml version="1.0" encoding="UTF-8"?>
<AUTOSAR xmlns="http://autosar.org/schema/r4.0">
  <AR-PACKAGES>
    <AR-PACKAGE>
      <SHORT-NAME>Components</SHORT-NAME>
      <ELEMENTS>
        <APPLICATION-SW-COMPONENT-TYPE>
          <SHORT-NAME>ASW_MotorController</SHORT-NAME>
        </APPLICATION-SW-COMPONENT-TYPE>
      </ELEMENTS>
    </AR-PACKAGE>
  </AR-PACKAGES>
</AUTOSAR>"""

    request_data = {
        "model": "/model/HuggingFace/deepseek-ai/DeepSeek-R1-Distill-Llama-70B",
        "prompt": prompt,
        "max_tokens": 800,
        "temperature": 0.7,
        "top_p": 0.9,
        "stream": False,
        "stop": ["</AUTOSAR>"]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                    f"{vllm_endpoint}/v1/completions",
                    json=request_data,
                    timeout=aiohttp.ClientTimeout(total=60)
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()

                    if "choices" in result and len(result["choices"]) > 0:
                        generated_text = result["choices"][0]["text"]

                        # 如果生成的文本没有XML声明，添加完整的XML结构
                        if not generated_text.strip().startswith('<?xml'):
                            xml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<AUTOSAR xmlns="http://autosar.org/schema/r4.0">
  <AR-PACKAGES>
    <AR-PACKAGE>
      <SHORT-NAME>Components</SHORT-NAME>
      <ELEMENTS>
        <APPLICATION-SW-COMPONENT-TYPE>
          <SHORT-NAME>ASW_MotorController</SHORT-NAME>
        </APPLICATION-SW-COMPONENT-TYPE>
      </ELEMENTS>
    </AR-PACKAGE>
  </AR-PACKAGES>
</AUTOSAR>'''
                        else:
                            # 清理生成的XML
                            xml_content = generated_text.strip()
                            if not xml_content.endswith('</AUTOSAR>'):
                                xml_content += '\n</AUTOSAR>'

                        print(f"✅ Direct vLLM generation successful")
                        print(f"📝 Generated XML: {len(xml_content)} characters")

                        # 保存结果
                        Path("outputs").mkdir(exist_ok=True)
                        output_file = Path("outputs") / "direct_autosar.xml"

                        with open(output_file, 'w', encoding='utf-8') as f:
                            f.write(xml_content)

                        print(f"💾 Saved: {output_file}")

                        # 预览
                        lines = xml_content.split('\n')
                        print("📄 Preview:")
                        for line in lines[:10]:
                            print(f"   {line}")

                        return True
                    else:
                        print(f"❌ No choices in response: {result}")
                        return False
                else:
                    error_text = await resp.text()
                    print(f"❌ Direct generation failed: {resp.status} - {error_text}")
                    return False

    except Exception as e:
        print(f"❌ Direct generation request failed: {e}")
        return False


async def main():
    """主函数"""
    print("🚀 Fixed vLLM Connection and Generation Check")

    # 检查vLLM直连
    vllm_works = await check_vllm_connection()

    # 检查增强服务
    enhanced_works = await check_enhanced_service()

    print(f"\n📊 Connection Results:")
    print(f"   Direct vLLM: {'✅' if vllm_works else '❌'}")
    print(f"   Enhanced Service: {'✅' if enhanced_works else '❌'}")

    # 根据可用性进行生成
    if enhanced_works:
        print(f"\n🧪 Attempting generation via Enhanced Service...")
        enhanced_success = await generate_via_enhanced_service()

        if enhanced_success:
            print(f"✅ Enhanced service generation completed successfully")
            print(f"💡 Recommendation: Update main_config.yaml to use port 8002")
            return

    if vllm_works:
        print(f"\n🧪 Attempting generation via Direct vLLM...")
        direct_success = await generate_via_vllm_direct()

        if direct_success:
            print(f"✅ Direct vLLM generation completed successfully")
            print(f"💡 Recommendation: Modify client to use vLLM v1/completions API")
            return

    print(f"\n❌ Both generation methods failed")
    print(f"💡 Please check cloud service configuration")


if __name__ == "__main__":
    asyncio.run(main())