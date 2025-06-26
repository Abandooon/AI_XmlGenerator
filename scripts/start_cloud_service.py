# scripts/start_cloud_service.py
# !/usr/bin/env python3
import os
import sys
import asyncio
import yaml

# 添加项目路径
sys.path.insert(0, '/opt/autosar_vllm_system/src')

from generation.services.cloud_generation_service import CloudGenerationService


def load_config(config_path: str) -> dict:
    """加载配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


async def main():
    """主启动函数"""

    # 加载配置
    config_path = "/opt/autosar_vllm_system/config/system_config.yaml"
    if os.path.exists(config_path):
        config = load_config(config_path)
    else:
        # 默认配置
        config = {
            "model": {
                "name": "deepseek-ai/deepseek-coder-33b-instruct",
                "max_model_len": 4096,
                "tensor_parallel_size": 1,
                "gpu_memory_utilization": 0.8,
                "trust_remote_code": True
            },
            "constraints": {
                "fsm_file": "/opt/autosar_vllm_system/artifacts/autosar.fsm",
                "gbnf_file": "/opt/autosar_vllm_system/artifacts/autosar.gbnf"
            },
            "cloud_service": {
                "host": "0.0.0.0",
                "port": 8000
            }
        }

    # 创建服务
    service = CloudGenerationService(config)

    # 初始化服务
    print("Initializing AUTOSAR vLLM service...")
    success = await service.initialize_service()

    if success:
        print(f"Service initialized successfully!")
        print(f"Starting server on {config['cloud_service']['host']}:{config['cloud_service']['port']}")
        service.run_server(
            host=config["cloud_service"]["host"],
            port=config["cloud_service"]["port"]
        )
    else:
        print("Failed to initialize service")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())