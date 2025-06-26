# src/main.py
import asyncio
from generation.services.cloud_generation_service import CloudGenerationService
from generation.services.local_proxy_service import LocalProxyService
from generation.models.request_models import GenerationRequest


async def main():
    """主启动函数"""

    # 配置
    model_config = {
        "model_name": "deepseek-ai/deepseek-coder-33b-instruct",
        "max_model_len": 8192,
        "tensor_parallel_size": 1,
        "gpu_memory_utilization": 0.9
    }

    constraint_config = {
        "fsm_file": "src/constraint_graph/artifacts/raw/autosar.fsm",
        "allowed_tokens_module": "src/constraint_graph/artifacts/raw/autosar_allowed_tokens.py",
        "gbnf_file": "src/constraint_graph/artifacts/grammar/autosar.gbnf"
    }

    validator_config = {
        "gbnf_grammar_file": "src/constraint_graph/artifacts/grammar/autosar.gbnf",
        "shacl_shapes_file": "src/constraint_graph/artifacts/shapes/autosar_shapes.ttl",
        "smt_template_file": "src/constraint_graph/artifacts/constraints.smt2"
    }

    # 启动云端服务
    cloud_service = CloudGenerationService(model_config, constraint_config)
    await cloud_service.initialize_service()

    # 启动本地代理服务
    proxy_service = LocalProxyService(
        cloud_endpoint="http://localhost:8000",
        cache_config={"max_size": 1000, "ttl": 3600},
        validator_config=validator_config
    )

    # 测试生成
    test_request = GenerationRequest(
        prompt="Generate AUTOSAR timing event with period 100ms",
        autosar_context={"domain": "timing", "complexity": "simple"},
        temperature=0.7,
        max_tokens=1024,
        validation_level="full"
    )

    result = await proxy_service.proxy_generate(test_request)

    print("Generated XML:")
    print(result["generation_response"].generated_xml)
    print("\nValidation Report:")
    print(proxy_service.validator.generate_validation_report(result["validation_results"]))


if __name__ == "__main__":
    asyncio.run(main())