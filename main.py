# main.py - 修复版本
import asyncio
import yaml
from pathlib import Path
import sys
import uuid
import time
import json

sys.path.insert(0, './src')

from src.client.full_client import FullAutosarClient
from src.utils.logger import get_logger

logger = get_logger(__name__)

# 简化的用例
AUTOSAR_CASES = [
    {
        "prompt": "Generate battery temperature monitor component",
        "autosar_context": {
            "domain": "battery_monitoring",
            "component_type": "APPLICATION-SW-COMPONENT-TYPE"
        }
    },
    {
        "prompt": "Generate motor controller component",
        "autosar_context": {
            "domain": "motor_control",
            "component_type": "APPLICATION-SW-COMPONENT-TYPE"
        }
    }
]


async def main():
    """主函数 - 修复版本"""

    # 创建目录
    for dir_name in ["logs", "outputs", "cache"]:
        Path(dir_name).mkdir(exist_ok=True)

    # 加载配置
    config_path = Path("config/main_config.yaml")
    if not config_path.exists():
        print(f"❌ Configuration file not found: {config_path}")
        return

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    print(f"🚀 AUTOSAR Detailed Generation System")
    print(f"📋 Project: {config['project']['name']}")
    print(f"🌐 Endpoint: {config['cloud_service']['internal_endpoint']}")
    print(f"🤖 Model: {config['cloud_service']['model_name']}")
    print(f"🔧 API Type: {config['cloud_service']['api_type']}")
    print(f"⏱️ Configured timeout: {config['cloud_service']['timeout']}s")
    print(f"⏱️ Request timeout: {config['performance']['request_timeout']}s")

    # 初始化完整客户端
    client = FullAutosarClient(config)

    # 执行生成任务
    successful_generations = 0

    for i, case in enumerate(AUTOSAR_CASES, 1):
        print(f"\n{'=' * 80}")
        print(f"🧪 Generation {i}: {case['autosar_context']['domain']}")
        print(f"{'=' * 80}")

        try:
            print(f"🔄 Generating detailed AUTOSAR XML...")
            print(f"💡 Using detailed prompt from cloud_client...")

            start_time = time.time()

            # 在main.py的生成调用中添加constraint_level参数
            response = await client.generate_and_validate_full(
                prompt=case["prompt"],
                autosar_context=case["autosar_context"],
                max_tokens=8000,
                temperature=0.3,
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1,
                constraint_level="mixed"  # 添加这一行
            )

            generation_time = time.time() - start_time

            if response.success:
                xml_content = response.generation.generated_xml

                print(f"✅ Generation successful in {generation_time:.2f}s")
                print(f"📝 Generated XML: {len(xml_content)} characters")

                # 详细内容验证
                has_autosar = "AUTOSAR" in xml_content
                has_xml_declaration = xml_content.strip().startswith('<?xml')
                has_component_type = "APPLICATION-SW-COMPONENT-TYPE" in xml_content
                has_rport = "R-PORT-PROTOTYPE" in xml_content
                has_pport = "P-PORT-PROTOTYPE" in xml_content
                has_runnable = "RUNNABLE-ENTITY" in xml_content
                has_timing_event = "TIMING-EVENT" in xml_content
                has_internal_behavior = "INTERNAL-BEHAVIOR" in xml_content
                has_uuid = "uuid=" in xml_content or "UUID>" in xml_content

                print("🔍 Detailed Content Validation:")
                print(f"   XML Declaration: {'✅' if has_xml_declaration else '❌'}")
                print(f"   AUTOSAR root: {'✅' if has_autosar else '❌'}")
                print(f"   APPLICATION-SW-COMPONENT-TYPE: {'✅' if has_component_type else '❌'}")
                print(f"   R-PORT-PROTOTYPE: {'✅' if has_rport else '❌'}")
                print(f"   P-PORT-PROTOTYPE: {'✅' if has_pport else '❌'}")
                print(f"   RUNNABLE-ENTITY: {'✅' if has_runnable else '❌'}")
                print(f"   TIMING-EVENT: {'✅' if has_timing_event else '❌'}")
                print(f"   INTERNAL-BEHAVIOR: {'✅' if has_internal_behavior else '❌'}")
                print(f"   UUID attributes: {'✅' if has_uuid else '❌'}")

                # 计算验证分数
                checks = [has_xml_declaration, has_autosar, has_component_type,
                          has_rport, has_pport, has_runnable, has_timing_event,
                          has_internal_behavior, has_uuid]
                validation_score = sum(checks) / len(checks) * 100
                print(f"   Overall Score: {validation_score:.1f}%")

                # 保存原始XML（用于调试）
                domain = case['autosar_context']['domain']
                output_file = Path("outputs") / f"autosar_{i}_{domain}.xml"

                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(xml_content)

                print(f"💾 Saved: {output_file}")

                # 预览所有行（因为内容很短）
                lines = xml_content.split('\n')
                print("📄 Complete XML Content:")
                print("─" * 60)
                for line_num, line in enumerate(lines, 1):
                    print(f"{line_num:2d}: {line}")
                print("─" * 60)

                # 保存元数据（修复ValidationResult属性访问）
                metadata = {
                    "request_id": str(uuid.uuid4()),
                    "generation_time": generation_time,
                    "prompt_used": "detailed_prompt_from_cloud_client",
                    "output_length": len(xml_content),
                    "autosar_context": case["autosar_context"],
                    "validation_score": validation_score,
                    "detailed_validation": {
                        "has_xml_declaration": has_xml_declaration,
                        "has_autosar": has_autosar,
                        "has_component_type": has_component_type,
                        "has_rport": has_rport,
                        "has_pport": has_pport,
                        "has_runnable": has_runnable,
                        "has_timing_event": has_timing_event,
                        "has_internal_behavior": has_internal_behavior,
                        "has_uuid": has_uuid
                    }
                }

                # 安全地访问验证结果
                if response.validation:
                    # 检查ValidationResult对象有哪些属性
                    validation_attrs = {
                        "overall_valid": getattr(response.validation, 'overall_valid', False),
                        "is_valid": getattr(response.validation, 'is_valid', False),
                        "validation_passed": getattr(response.validation, 'validation_passed', False)
                    }

                    # 尝试获取错误信息
                    error_count = 0
                    warning_count = 0

                    if hasattr(response.validation, 'errors'):
                        error_count = len(response.validation.errors)
                    elif hasattr(response.validation, 'error_list'):
                        error_count = len(response.validation.error_list)
                    elif hasattr(response.validation, 'validation_errors'):
                        error_count = len(response.validation.validation_errors)

                    if hasattr(response.validation, 'warnings'):
                        warning_count = len(response.validation.warnings)
                    elif hasattr(response.validation, 'warning_list'):
                        warning_count = len(response.validation.warning_list)

                    metadata["local_validation"] = {
                        **validation_attrs,
                        "error_count": error_count,
                        "warning_count": warning_count,
                        "available_attributes": [attr for attr in dir(response.validation) if not attr.startswith('_')]
                    }

                    print(f"🔍 Local Validation:")
                    print(
                        f"   Valid: {'✅' if validation_attrs.get('overall_valid') or validation_attrs.get('is_valid') else '❌'}")
                    print(f"   Errors: {error_count}")
                    print(f"   Warnings: {warning_count}")

                metadata_file = Path("outputs") / f"autosar_{i}_{domain}_metadata.json"
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2)

                successful_generations += 1

            else:
                print(f"❌ Generation failed: {response.error}")
                logger.error(f"Generation {i} failed: {response.error}")

        except Exception as e:
            print(f"❌ Generation {i} failed with exception: {e}")
            logger.error(f"Generation {i} exception: {e}", exc_info=True)

            # 保存调试信息
            if 'response' in locals() and response.generation:
                debug_file = Path("outputs") / f"debug_{i}_raw_output.txt"
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(response.generation.generated_xml)
                print(f"🐛 Debug output saved: {debug_file}")

    print(f"\n🏁 Generation Completed!")
    print(
        f"📊 Success Rate: {successful_generations}/{len(AUTOSAR_CASES)} ({successful_generations / len(AUTOSAR_CASES) * 100:.1f}%)")

    if successful_generations > 0:
        print(f"📁 Check ./outputs/ for generated XML files")
    else:
        print(f"❌ All generations failed")
        print(f"💡 The generated content appears to be incomplete XML fragments")
        print(f"💡 Check if the detailed prompt in cloud_client.py is being used correctly")


if __name__ == "__main__":
    asyncio.run(main())