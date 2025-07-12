import asyncio
import json

import yaml
from pathlib import Path
import sys
import time

sys.path.insert(0, './src')

from src.client.full_client import FullAutosarClient
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def main():
    """主函数 - 支持两种prompt来源模式"""

    # 创建目录
    Path("outputs").mkdir(exist_ok=True)

    # 加载配置
    config_path = Path("config/main_config.yaml")
    if not config_path.exists():
        print(f"❌ Configuration file not found: {config_path}")
        return

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    print(f"🚀 AUTOSAR Generation System")
    print(f"🎯 Strategy: {config['constraint_strategy']['mode']}")

    # 初始化客户端
    client = FullAutosarClient(config)

    # 🎯 检查两种prompt来源
    config_prompts = []
    yaml_prompts = []

    # 1. 从配置文件获取prompts
    prompts_config = config.get('prompts', {})
    component_level = prompts_config.get('component_level', [])
    if isinstance(component_level, list) and component_level:
        config_prompts = component_level
        print(f"📋 Found {len(config_prompts)} prompts in config file")
    elif isinstance(component_level, str) and component_level.strip():
        config_prompts = [component_level]
        print(f"📋 Found 1 prompt in config file")

    # 2. 从YAML文件获取prompts
    promote_files = [
        "promote_full.yaml",
        "promote_mid.yaml",
        "promote_min.yaml"
    ]

    for promote_file in promote_files:
        file_path = Path(promote_file)
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    promote_data = yaml.safe_load(f)
                    # 获取第一个键的值
                    if promote_data:
                        key = list(promote_data.keys())[0]
                        file_prompts = promote_data.get(key, [])
                        if file_prompts:
                            yaml_prompts.extend(file_prompts)
                            print(f"📂 Loaded {len(file_prompts)} prompts from {promote_file}")
            except Exception as e:
                print(f"⚠️ Error loading {promote_file}: {e}")

    # 🎯 检查是否有可用的prompts
    if not config_prompts and not yaml_prompts:
        print("❌ Error: No prompts found in either config file or YAML files!")
        print("   Please add prompts to config/main_config.yaml under prompts.component_level")
        print("   OR place YAML files (promote_full.yaml, promote_mid.yaml, promote_min.yaml) in current directory")
        return

    # 🎯 选择prompt来源
    print(f"\n📊 Available prompt sources:")
    if config_prompts:
        print(f"   1. Config file: {len(config_prompts)} prompts")
    else:
        print(f"   1. Config file: 0 prompts (unavailable)")

    if yaml_prompts:
        print(f"   2. YAML files: {len(yaml_prompts)} prompts")
    else:
        print(f"   2. YAML files: 0 prompts (unavailable)")

    # 选择来源
    while True:
        source_choice = input("\nChoose prompt source: [1] Config file [2] YAML files: ").strip()

        if source_choice == "1" and config_prompts:
            selected_prompts = config_prompts
            source_name = "Config file"
            break
        elif source_choice == "2" and yaml_prompts:
            selected_prompts = yaml_prompts
            source_name = "YAML files"
            break
        elif source_choice == "1" and not config_prompts:
            print("❌ Config file has no prompts available")
        elif source_choice == "2" and not yaml_prompts:
            print("❌ YAML files have no prompts available")
        else:
            print("❌ Invalid choice, please enter 1 or 2")

    print(f"✅ Using {source_name}: {len(selected_prompts)} prompts")

    # 🎯 选择处理数量
    print(f"\n📝 Processing options:")
    print(f"   1. Single prompt (first one)")
    print(f"   2. First 3 prompts")
    print(f"   3. First 5 prompts")
    print(f"   4. All {len(selected_prompts)} prompts")

    while True:
        count_choice = input("Choose processing count: [1] Single [2] First 3 [3] First 5 [4] All: ").strip()

        if count_choice == "1":
            final_prompts = selected_prompts[:1]
            break
        elif count_choice == "2":
            final_prompts = selected_prompts[:3]
            break
        elif count_choice == "3":
            final_prompts = selected_prompts[:5]
            break
        elif count_choice == "4":
            final_prompts = selected_prompts
            break
        else:
            print("❌ Invalid choice, please enter 1, 2, 3, or 4")

    print(f"🎯 Processing {len(final_prompts)} prompt(s) from {source_name}")
    print(f"{'=' * 80}")

    # 🎯 处理prompts - 记录总体统计
    total_start_time = time.time()
    success_count = 0
    error_count = 0
    total_chars = 0
    total_tokens = 0
    total_memory = 0.0
    all_stats = []  # 🔥 收集所有统计信息
    seeds_used = []  # 🔥 记录使用的种子

    for i, prompt in enumerate(final_prompts, 1):
        print(f"\n🎯 Prompt {i}/{len(final_prompts)}")
        print(f"📄 Source: {source_name}")
        print(f"📄 Content preview: {prompt[:100]}...")

        start_time = time.time()

        try:
            response = await client.generate_and_validate_full(
                prompt=prompt,
                autosar_context={"component_type": "APPLICATION-SW-COMPONENT-TYPE"},
                max_tokens=8000,
                temperature=0.7,
                top_p=0.9,
                constraint_level="mixed"
            )

            generation_time = time.time() - start_time

            if response.success:
                xml_content = response.generation.generated_xml
                metadata = response.generation.metadata or {}
                performance = response.generation.performance or {}

                # 🔥 新增：检查是否有seed_results
                seed_results = metadata.get("seed_results", [])
                multi_seed_stats = metadata.get("multi_seed_stats", {})

                if seed_results and len(seed_results) > 0:
                    # 🔥 新逻辑：处理多种子结果
                    print(f"🎲 Found {len(seed_results)} seed results")

                    # 记录使用的种子（只记录一次）
                    if not seeds_used:
                        seeds_used = [r["seed"] for r in seed_results]

                    prompt_total_chars = 0
                    prompt_total_tokens = 0
                    prompt_total_memory = 0.0
                    seed_stats_list = []

                    for j, seed_result in enumerate(seed_results):
                        seed = seed_result["seed"]
                        seed_xml = seed_result["xml"]
                        seed_resource_stats = seed_result["resource_stats"]

                        if seed_result["success"]:
                            seed_xml_length = len(seed_xml)
                            prompt_total_chars += seed_xml_length

                            # 提取种子特定的统计信息
                            seed_tokens = seed_resource_stats.get("token_usage", {}).get("total_tokens", 0)
                            seed_memory = seed_resource_stats.get("memory_usage_mb", {}).get("delta", 0)
                            seed_time = seed_resource_stats.get("generation_time_seconds", 0)

                            prompt_total_tokens += seed_tokens
                            prompt_total_memory += seed_memory

                            # 🔥 生成包含种子的文件名
                            output_file = Path(
                                "outputs") / f"generated_{i}_seed_{seed}_{source_name.lower().replace(' ', '_')}.xml"

                            # 保存XML文件
                            with open(output_file, 'w', encoding='utf-8') as f:
                                try:
                                    import xml.dom.minidom
                                    dom = xml.dom.minidom.parseString(seed_xml)
                                    formatted_xml = dom.toprettyxml(indent="  ", encoding=None)
                                    formatted_xml = '\n'.join(
                                        [line for line in formatted_xml.split('\n') if line.strip()])
                                    f.write(formatted_xml)
                                except:
                                    f.write(seed_xml)

                            print(f"💾 Saved seed {seed}: {output_file}")
                            print(
                                f"   📊 Length: {seed_xml_length}, Time: {seed_time:.3f}s, Tokens: {seed_tokens}, Memory: {seed_memory:.2f}MB")

                            # 🔥 保存该种子的统计信息
                            seed_stats = {
                                "prompt_index": i,
                                "seed": seed,
                                "seed_version": j + 1,
                                "prompt_preview": prompt[:100] + "..." if len(prompt) > 100 else prompt,
                                "source": source_name,
                                "xml_length": seed_xml_length,
                                "generation_time": seed_time,
                                "token_usage": seed_resource_stats.get("token_usage", {}),
                                "memory_usage": seed_resource_stats.get("memory_usage_mb", {}),
                                "generation_params": seed_resource_stats.get("generation_params", {}),
                                "success": True,
                                "output_file": str(output_file)
                            }

                            # 保存种子特定的统计文件
                            stats_file = Path(
                                "outputs") / f"stats_{i}_seed_{seed}_{source_name.lower().replace(' ', '_')}.json"
                            with open(stats_file, 'w', encoding='utf-8') as f:
                                json.dump(seed_stats, f, indent=2, ensure_ascii=False)

                            print(f"📊 Saved stats for seed {seed}: {stats_file}")
                            seed_stats_list.append(seed_stats)

                        else:
                            print(f"❌ Seed {seed} failed: {seed_result.get('error', 'Unknown error')}")
                            seed_stats = {
                                "prompt_index": i,
                                "seed": seed,
                                "seed_version": j + 1,
                                "success": False,
                                "error": seed_result.get('error', 'Unknown error')
                            }
                            seed_stats_list.append(seed_stats)

                    # 更新总计数器
                    total_chars += prompt_total_chars
                    total_tokens += prompt_total_tokens
                    total_memory += prompt_total_memory

                    # 🔥 记录整体prompt统计
                    prompt_stats = {
                        "prompt_index": i,
                        "prompt_preview": prompt[:100] + "..." if len(prompt) > 100 else prompt,
                        "source": source_name,
                        "total_processing_time": multi_seed_stats.get("total_processing_time", 0),
                        "seed_count": len(seed_results),
                        "successful_seeds": len([r for r in seed_results if r["success"]]),
                        "seeds_used": [r["seed"] for r in seed_results],
                        "total_xml_chars": prompt_total_chars,
                        "total_tokens": prompt_total_tokens,
                        "total_memory_mb": prompt_total_memory,
                        "seed_details": seed_stats_list,
                        "success": True
                    }
                    all_stats.append(prompt_stats)
                    success_count += 1

                    print(
                        f"✅ Multi-seed generation completed: {len([r for r in seed_results if r['success']])}/{len(seed_results)} successful")

                else:
                    # 🔥 单一结果处理（向后兼容或非多种子策略）
                    xml_length = len(xml_content)
                    total_chars += xml_length

                    print(f"✅ Generation successful in {generation_time:.3f}s")
                    print(f"📝 Generated XML: {xml_length} characters")

                    # 显示详细的资源统计信息
                    vllm_time = performance.get('vllm_generation_time', 0)
                    total_process_time = performance.get('total_processing_time', 0)
                    token_usage = performance.get('token_usage', {})
                    memory_usage = performance.get('memory_usage', {})

                    tokens = token_usage.get('total_tokens', 0)
                    memory_delta = memory_usage.get('delta', 0)

                    total_tokens += tokens
                    total_memory += memory_delta

                    print(f"⏱️  Total processing: {total_process_time:.3f}s")
                    print(f"⏱️  vLLM generation: {vllm_time:.3f}s")
                    print(
                        f"🔢 Tokens: prompt={token_usage.get('prompt_tokens', 0)}, completion={token_usage.get('completion_tokens', 0)}, total={tokens}")
                    print(
                        f"💾 Memory: before={memory_usage.get('before', 0):.2f}MB, after={memory_usage.get('after', 0):.2f}MB, delta={memory_delta:.2f}MB")

                    # 保存单一XML文件
                    output_file = Path("outputs") / f"generated_{i}_{source_name.lower().replace(' ', '_')}.xml"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        try:
                            import xml.dom.minidom
                            dom = xml.dom.minidom.parseString(xml_content)
                            formatted_xml = dom.toprettyxml(indent="  ", encoding=None)
                            formatted_xml = '\n'.join([line for line in formatted_xml.split('\n') if line.strip()])
                            f.write(formatted_xml)
                        except:
                            f.write(xml_content)

                    print(f"💾 Saved: {output_file}")

                    # 🔥 选择性显示内容
                    if len(final_prompts) == 1:
                        print("\n📄 Generated XML:")
                        print("─" * 60)
                        try:
                            import xml.dom.minidom
                            dom = xml.dom.minidom.parseString(xml_content)
                            formatted_xml = dom.toprettyxml(indent="  ", encoding=None)
                            formatted_xml = '\n'.join([line for line in formatted_xml.split('\n') if line.strip()])
                            print(formatted_xml)
                        except:
                            print(xml_content)
                        print("─" * 60)
                    else:
                        # 批量模式只显示摘要
                        print(f"📄 XML preview: {xml_content[:200]}...")

                    # 记录统计
                    prompt_stats = {
                        "prompt_index": i,
                        "prompt_preview": prompt[:100] + "..." if len(prompt) > 100 else prompt,
                        "source": source_name,
                        "total_processing_time": total_process_time,
                        "vllm_generation_time": vllm_time,
                        "xml_length": xml_length,
                        "token_usage": token_usage,
                        "memory_usage": memory_usage,
                        "success": True
                    }
                    all_stats.append(prompt_stats)
                    success_count += 1

            else:
                print(f"❌ Generation failed: {response.error}")
                error_count += 1

                # 记录失败统计
                error_stats = {
                    "prompt_index": i,
                    "prompt_preview": prompt[:100] + "..." if len(prompt) > 100 else prompt,
                    "source": source_name,
                    "error": response.error,
                    "success": False
                }
                all_stats.append(error_stats)

        except Exception as e:
            print(f"❌ Error processing prompt {i}: {e}")
            logger.error(f"Generation error for prompt {i}: {e}", exc_info=True)
            error_count += 1

            # 记录异常统计
            exception_stats = {
                "prompt_index": i,
                "prompt_preview": prompt[:100] + "..." if len(prompt) > 100 else prompt,
                "source": source_name,
                "exception": str(e),
                "success": False
            }
            all_stats.append(exception_stats)

        # 批量处理时添加延迟
        if len(final_prompts) > 1 and i < len(final_prompts):
            print("⏳ Waiting 2 seconds before next prompt...")
            await asyncio.sleep(2)

    # 🔥 修复：保存完整的统计信息到文件
    total_time = time.time() - total_start_time

    # 🔥 收集所有种子相关的文件
    seed_xml_files = list(Path("outputs").glob(f"generated_*_seed_*_{source_name.lower().replace(' ', '_')}.xml"))
    seed_stats_files = list(Path("outputs").glob(f"stats_*_seed_*_{source_name.lower().replace(' ', '_')}.json"))

    stats_summary = {
        "session_info": {
            "source": source_name,
            "total_prompts": len(final_prompts),
            "successful": success_count,
            "failed": error_count,
            "success_rate": f"{(success_count / len(final_prompts) * 100):.1f}%",
            "total_time": f"{total_time:.2f}s",
            "average_time_per_prompt": f"{total_time / len(final_prompts):.2f}s",
            "total_characters": total_chars,
            "total_tokens": total_tokens,
            "total_memory_mb": f"{total_memory:.2f}",
            "average_chars_per_prompt": total_chars // len(final_prompts) if len(final_prompts) > 0 else 0,
            "average_tokens_per_prompt": total_tokens // len(final_prompts) if len(final_prompts) > 0 else 0,
            "strategy": config['constraint_strategy']['mode'],
            # 🔥 新增：种子信息
            "seeds_used": seeds_used if seeds_used else [42, 1001, 20250701],  # 默认种子值
            "seed_generation_enabled": len(seed_xml_files) > 0
        },
        # 🔥 修改：使用正确的键名
        "prompts_details": all_stats,
        # 🔥 新增：种子文件列表
        "seed_files": {
            "xml_files": [str(f) for f in seed_xml_files],
            "stats_files": [str(f) for f in seed_stats_files],
            "total_seed_files": len(seed_xml_files)
        }
    }

    # 保存统计文件
    stats_file = Path("outputs") / f"generation_stats_{source_name.lower().replace(' ', '_')}.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats_summary, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 80}")
    print(f"📊 Overall Statistics:")
    print(f"   Source: {source_name}")
    print(f"   Total prompts processed: {len(final_prompts)}")
    print(f"   Successful: {success_count}")
    print(f"   Failed: {error_count}")
    print(f"   Success rate: {(success_count / len(final_prompts) * 100):.1f}%")
    print(f"   Total time: {total_time:.2f}s")
    print(f"   Average time per prompt: {total_time / len(final_prompts):.2f}s")
    print(f"   Total characters generated: {total_chars:,}")
    print(f"   Total tokens used: {total_tokens:,}")
    print(f"   Total memory used: {total_memory:.2f}MB")
    if seeds_used:
        print(f"   Seeds used: {seeds_used}")
        print(f"   Seed files generated: {len(seed_xml_files)}")
    if total_chars > 0:
        print(f"   Average chars per prompt: {total_chars // len(final_prompts):,}")
    if total_tokens > 0:
        print(f"   Average tokens per prompt: {total_tokens // len(final_prompts):,}")

    print(f"📊 Detailed statistics saved: {stats_file}")
    print(f"🎉 Processing completed!")


if __name__ == "__main__":
    asyncio.run(main())