# src/generation/services/cloud_generation_service.py
import asyncio
import time
from typing import Dict, List, Optional
from vllm import AsyncLLMEngine, AsyncEngineArgs
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from ..constraints.simple_constraint import SimpleConstraintHandler
from ..processors.prompt_enhancer import PromptEnhancer
from ..processors.xml_postprocessor import XMLPostProcessor
from ..models.request_models import GenerationRequest, BatchGenerationRequest
from ..models.response_models import GenerationResponse, ErrorResponse


class CloudGenerationService:
    """云端生成服务"""

    def __init__(self, config: Dict):
        """初始化云端生成服务"""
        self.config = config
        self.engine: Optional[AsyncLLMEngine] = None
        self.constraint_handler: Optional[SimpleConstraintHandler] = None
        self.prompt_enhancer = PromptEnhancer()
        self.xml_postprocessor = XMLPostProcessor()
        self.is_initialized = False

        # 创建FastAPI应用
        self.app = FastAPI(title="AUTOSAR vLLM Generation Service", version="1.0.0")
        self._setup_routes()
        self._setup_cors()

    def _setup_cors(self):
        """设置CORS"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _setup_routes(self):
        """设置API路由"""

        @self.app.get("/health")
        async def health_check():
            """健康检查"""
            return {
                "status": "healthy" if self.is_initialized else "initializing",
                "model": self.config["model"]["name"],
                "initialized": self.is_initialized
            }

        @self.app.post("/generate", response_model=GenerationResponse)
        async def generate_xml(request: GenerationRequest):
            """单个XML生成请求"""
            if not self.is_initialized:
                raise HTTPException(status_code=503, detail="Service not initialized")

            try:
                response = await self.generate_xml(request)
                return response
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/batch_generate")
        async def batch_generate_xml(batch_request: BatchGenerationRequest):
            """批量XML生成请求"""
            if not self.is_initialized:
                raise HTTPException(status_code=503, detail="Service not initialized")

            try:
                responses = await self.batch_generate(batch_request.requests)
                return {"responses": responses}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/initialize")
        async def initialize_service():
            """手动初始化服务"""
            success = await self.initialize_service()
            return {"success": success, "initialized": self.is_initialized}

    async def initialize_service(self) -> bool:
        """异步初始化模型和约束加载"""
        if self.is_initialized:
            return True

        try:
            print("Initializing vLLM engine...")

            # 初始化vLLM引擎
            engine_args = AsyncEngineArgs(
                model=self.config["model"]["name"],
                max_model_len=self.config["model"]["max_model_len"],
                tensor_parallel_size=self.config["model"]["tensor_parallel_size"],
                gpu_memory_utilization=self.config["model"]["gpu_memory_utilization"],
                trust_remote_code=self.config["model"].get("trust_remote_code", True),
                enforce_eager=True  # 避免图编译问题
            )

            self.engine = AsyncLLMEngine.from_engine_args(engine_args)
            print("vLLM engine initialized successfully")

            # 初始化约束处理器
            print("Initializing constraint handler...")
            self.constraint_handler = SimpleConstraintHandler(
                fsm_file=self.config["constraints"]["fsm_file"],
                gbnf_file=self.config["constraints"]["gbnf_file"]
            )
            print("Constraint handler initialized successfully")

            self.is_initialized = True
            return True

        except Exception as e:
            print(f"Service initialization failed: {e}")
            self.is_initialized = False
            return False

    async def generate_xml(self, request: GenerationRequest) -> GenerationResponse:
        """执行约束XML生成"""

        start_time = time.time()

        try:
            # 1. 提示增强
            enhanced_prompt = self.prompt_enhancer.enhance_prompt(
                request.prompt,
                request.autosar_context
            )

            # 2. 创建采样参数
            sampling_params = self.constraint_handler.create_sampling_params(
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                constraint_level=request.constraint_level
            )

            # 3. vLLM生成
            print(f"Generating for request {request.request_id}")
            generation_start = time.time()

            results = []
            async for request_output in self.engine.generate(
                    enhanced_prompt,
                    sampling_params,
                    request_id=request.request_id
            ):
                results.append(request_output)

            generation_time = time.time() - generation_start

            if not results:
                raise Exception("No generation results")

            # 4. 后处理
            raw_xml = results[-1].outputs[0].text
            cleaned_xml = self.xml_postprocessor.clean_generated_xml(raw_xml)

            total_time = time.time() - start_time

            return GenerationResponse(
                request_id=request.request_id,
                generated_xml=cleaned_xml,
                metadata={
                    "constraint_level": request.constraint_level,
                    "prompt_length": len(enhanced_prompt),
                    "raw_output_length": len(raw_xml),
                    "cleaned_output_length": len(cleaned_xml)
                },
                performance={
                    "total_time": total_time,
                    "generation_time": generation_time,
                    "processing_time": total_time - generation_time
                },
                constraint_info={
                    "fsm_states": len(self.constraint_handler.fsm_data.get("states", [])),
                    "gbnf_applied": bool(
                        self.constraint_handler.gbnf_grammar and request.constraint_level in ["gbnf", "mixed"])
                }
            )

        except Exception as e:
            print(f"Generation failed for request {request.request_id}: {e}")
            return ErrorResponse(
                request_id=request.request_id,
                error_code="GENERATION_FAILED",
                error_message=str(e),
                error_details={"constraint_level": request.constraint_level}
            )

    async def batch_generate(self, request_list: List[GenerationRequest]) -> List[GenerationResponse]:
        """批量处理生成请求"""

        # 简单的顺序处理，后续可以优化为并行
        results = []
        for request in request_list:
            result = await self.generate_xml(request)
            results.append(result)

        return results

    def run_server(self, host: str = "0.0.0.0", port: int = 8000):
        """运行服务器"""
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            log_level="info",
            access_log=True
        )


# 启动脚本
async def main():
    """主启动函数"""

    # 配置
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
        }
    }

    # 创建服务
    service = CloudGenerationService(config)

    # 初始化服务
    print("Initializing service...")
    success = await service.initialize_service()

    if success:
        print("Service initialized successfully, starting server...")
        service.run_server(host="0.0.0.0", port=8000)
    else:
        print("Failed to initialize service")


if __name__ == "__main__":
    asyncio.run(main())