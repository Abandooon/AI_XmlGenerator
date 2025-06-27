# scripts/start_cloud_service.py
import os
import sys
import asyncio
import yaml
import uvicorn

sys.path.insert(0, '/opt/autosar_vllm_system/src')

from generation.services.enhanced_cloud_service import EnhancedCloudGenerationService


async def main():
    """主启动函数"""
    # 配置
    config = {
        "model": {
            "name": "deepseek-ai/deepseek-r1-distill-llama-8b",  # 使用当前部署的模型
            "max_model_len": 4096,
            "tensor_parallel_size": 1,
            "gpu_memory_utilization": 0.8,
            "trust_remote_code": True
        },
        "cloud_service": {
            "host": "0.0.0.0",
            "port": 8000
        }
    }

    # 创建服务
    service = EnhancedCloudGenerationService(config)

    # 初始化
    print("Initializing Enhanced AUTOSAR vLLM service...")
    success = await service.initialize_service()

    if success:
        print("✅ Service initialized successfully!")
        print(f"🚀 Starting server on {config['cloud_service']['host']}:{config['cloud_service']['port']}")

        # 运行服务器
        uvicorn.run(
            service.app,
            host=config["cloud_service"]["host"],
            port=config["cloud_service"]["port"],
            log_level="info"
        )
    else:
        print("❌ Failed to initialize service")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())