# src/client/vllm_adapter.py
import time
from typing import Dict, Any

import aiohttp


class VLLMAdapter:
    """vLLM API适配器"""

    def __init__(self, config: Dict[str, Any]):
        self.endpoint = config['cloud_service']['internal_endpoint']
        self.model_name = config['cloud_service']['model_name']
        self.timeout = config['cloud_service']['timeout']
        self.max_retries = config['cloud_service']['max_retries']

    async def check_health(self) -> Dict[str, Any]:
        """检查vLLM服务健康状态"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                        f"{self.endpoint}/v1/models",
                        timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        models = await resp.json()
                        return {
                            "available": True,
                            "models": models.get("data", []),
                            "status": "healthy"
                        }
                    else:
                        return {"available": False, "error": f"HTTP {resp.status}"}
        except Exception as e:
            return {"available": False, "error": str(e)}

    async def generate(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行生成请求"""

        # 构建vLLM请求
        vllm_request = {
            "model": self.model_name,
            "prompt": request_data["prompt"],
            "max_tokens": min(request_data.get("max_tokens", 800), 1000),
            "temperature": request_data.get("temperature", 0.7),
            "top_p": request_data.get("top_p", 0.9),
            "frequency_penalty": request_data.get("frequency_penalty", 0.1),
            "presence_penalty": request_data.get("presence_penalty", 0.1),
            "stream": False,
            "stop": ["</AUTOSAR>", "\n\n---", "```"]
        }

        start_time = time.time()

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                        f"{self.endpoint}/v1/completions",
                        json=vllm_request,
                        timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()

                        # 提取生成的文本
                        if "choices" in result and len(result["choices"]) > 0:
                            generated_text = result["choices"][0]["text"]

                            return {
                                "success": True,
                                "generated_text": generated_text,
                                "raw_response": result,
                                "generation_time": time.time() - start_time,
                                "model_info": {
                                    "model_name": self.model_name,
                                    "usage": result.get("usage", {})
                                }
                            }
                        else:
                            return {
                                "success": False,
                                "error": "No choices in vLLM response",
                                "raw_response": result
                            }
                    else:
                        error_text = await resp.text()
                        return {
                            "success": False,
                            "error": f"HTTP {resp.status}: {error_text}",
                            "generation_time": time.time() - start_time
                        }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "generation_time": time.time() - start_time
            }

    def clean_xml_output(self, raw_text: str) -> str:
        """清理XML输出"""
        if not raw_text:
            return ""

        lines = raw_text.strip().split('\n')
        xml_lines = []
        xml_started = False

        for line in lines:
            line = line.strip()

            if not xml_started:
                if line.startswith('<?xml') or (line.startswith('<') and 'AUTOSAR' in line):
                    xml_started = True
                    xml_lines.append(line)
            else:
                xml_lines.append(line)
                if line.strip() == '</AUTOSAR>':
                    break

        xml_content = '\n'.join(xml_lines)

        # 如果没有XML声明，添加
        if xml_content and not xml_content.startswith('<?xml'):
            xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_content

        # 确保有结束标签
        if xml_content and not xml_content.strip().endswith('</AUTOSAR>'):
            xml_content += '\n</AUTOSAR>'

        return xml_content

    def enhance_autosar_prompt(self, prompt: str, autosar_context: Dict[str, Any] = None) -> str:
        """增强AUTOSAR提示词"""

        context_parts = []
        if autosar_context:
            if "domain" in autosar_context:
                context_parts.append(f"Domain: {autosar_context['domain']}")
            if "component_type" in autosar_context:
                context_parts.append(f"Component Type: {autosar_context['component_type']}")

        context_str = "\n".join(context_parts) if context_parts else "Standard AUTOSAR component"

        enhanced_prompt = f"""You are an expert AUTOSAR XML generator. Generate a valid APPLICATION-SW-COMPONENT-TYPE following AUTOSAR R4.0 specification.

Context Information:
{context_str}

Task: {prompt}

Requirements:
1. Generate ONLY valid AUTOSAR XML following R4.0 schema
2. Create APPLICATION-SW-COMPONENT-TYPE structure:
   - Proper XML declaration and AUTOSAR namespace
   - AR-PACKAGES container structure
   - APPLICATION-SW-COMPONENT-TYPE element with SHORT-NAME
   - Use realistic component names
3. Generate clean, well-formatted XML without explanations
4. Keep structure simple but valid

Start with XML declaration and generate complete structure:

<?xml version="1.0" encoding="UTF-8"?>
<AUTOSAR xmlns="http://autosar.org/schema/r4.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://autosar.org/schema/r4.0 AUTOSAR_4-2-2.xsd">"""

        return enhanced_prompt