# src/models/constraint_models.py - 更新版本
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any


class ConstraintInfo(BaseModel):
    """约束信息模型 - 支持引用和传统模式"""
    model_config = ConfigDict(protected_namespaces=())

    # 🔥 新增：引用模式（优先使用）
    fsm_ref: Optional[str] = None  # "autosar" - 引用预加载的FSM
    gbnf_ref: Optional[str] = None  # "autosar" - 引用预加载的GBNF

    # 传统模式（兼容性保留）
    fsm_enabled: bool = False
    current_state: Optional[str] = None
    allowed_tokens: Optional[List[str]] = None
    gbnf_enabled: bool = False
    grammar_rules: Optional[str] = None

    # 其他字段
    domain_constraints: Dict[str, Any] = {}
    constraint_version: Optional[str] = None
    constraint_source: Optional[str] = None


class EnhancedGenerationRequest(BaseModel):
    """增强生成请求模型"""
    model_config = ConfigDict(protected_namespaces=())

    request_id: str
    timestamp: Optional[float] = None
    prompt: str
    temperature: float = 0.7
    max_tokens: int = 1024
    top_p: float = 0.9
    frequency_penalty: float = 0.1
    presence_penalty: float = 0.1
    constraint_info: ConstraintInfo
    autosar_context: Dict[str, Any] = {}
    client_version: Optional[str] = None
    client_id: Optional[str] = None


class CloudGenerationResponse(BaseModel):
    """云端生成响应模型"""
    model_config = ConfigDict(protected_namespaces=())

    request_id: str
    success: bool
    timestamp: Optional[float] = None
    generated_xml: Optional[str] = None
    raw_output: Optional[str] = None
    constraints_applied: Dict[str, Any] = {}  # 🔥 支持复杂数据结构
    constraint_violations: List[str] = []
    generation_time: float = 0.0
    model_info: Dict[str, Any] = {}
    error_message: Optional[str] = None
    error_details: Dict[str, Any] = {}


# src/client/constraint_preparer.py - 更新版本
import json
from typing import Dict, List, Optional, Any
from pathlib import Path

from ..models.constraint_models import ConstraintInfo
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ConstraintPreparer:
    """约束准备器 - 支持引用和传统模式"""

    def __init__(self, artifacts_dir: str):
        self.artifacts_dir = Path(artifacts_dir)

        # 检查本地文件存在性（用于决定模式）
        self.local_fsm_available = self._check_local_fsm()
        self.local_gbnf_available = self._check_local_gbnf()

        # 如果需要传统模式，预加载文件
        if self.local_fsm_available or self.local_gbnf_available:
            self.gbnf_grammar = self._load_gbnf_grammar()
            self.allowed_tokens_list = self._load_allowed_tokens()
        else:
            self.gbnf_grammar = ""
            self.allowed_tokens_list = []

    def _check_local_fsm(self) -> bool:
        """检查本地FSM文件是否存在"""
        fsm_file = self.artifacts_dir / "raw" / "autosar.fsm"
        tokens_file = self.artifacts_dir / "raw" / "autosar_allowed_tokens.py"
        return fsm_file.exists() or tokens_file.exists()

    def _check_local_gbnf(self) -> bool:
        """检查本地GBNF文件是否存在"""
        gbnf_file = self.artifacts_dir / "grammar" / "autosar.gbnf"
        return gbnf_file.exists()

    def prepare_constraint_info(self, constraint_level: str = "mixed",
                                current_state: str = "START",
                                use_references: bool = True) -> ConstraintInfo:
        """准备约束信息 - 支持引用和传统模式"""

        constraint_info = ConstraintInfo()

        if use_references:
            # 🔥 新模式：使用预加载引用（推荐）
            logger.info("Using constraint reference mode (zero transmission)")

            if constraint_level in ["mixed", "full"]:
                # FSM优先策略
                constraint_info.fsm_ref = "autosar"  # 引用云端预加载的autosar.fsm
                constraint_info.gbnf_ref = None  # FSM优先，不使用GBNF
                logger.info("Applied FSM reference constraint: autosar")

            elif constraint_level == "gbnf_only":
                # 仅GBNF模式（用于对比测试）
                constraint_info.fsm_ref = None
                constraint_info.gbnf_ref = "autosar"  # 引用云端预加载的autosar.gbnf
                logger.info("Applied GBNF reference constraint: autosar")

            else:
                # simple级别 - 无约束
                constraint_info.fsm_ref = None
                constraint_info.gbnf_ref = None
                logger.info("No constraints applied (simple level)")

        else:
            # 🔄 传统模式：直接传输（兼容性/本地测试）
            logger.info("Using traditional transmission mode")

            if constraint_level in ["mixed", "full"] and self.local_fsm_available:
                constraint_info.fsm_enabled = True
                constraint_info.allowed_tokens = self.allowed_tokens_list
                constraint_info.current_state = current_state
                logger.info(f"Applied traditional FSM constraint: {len(self.allowed_tokens_list)} tokens")

            elif constraint_level == "gbnf_only" and self.local_gbnf_available:
                constraint_info.gbnf_enabled = True
                constraint_info.grammar_rules = self.gbnf_grammar
                logger.info(f"Applied traditional GBNF constraint: {len(self.gbnf_grammar)} chars")

            else:
                logger.info("No local constraint files available or simple level")

        # 添加域特定约束（不变）
        if constraint_level == "full":
            constraint_info.domain_constraints = {
                "required_elements": [
                    "AUTOSAR", "AR-PACKAGES", "APPLICATION-SW-COMPONENT-TYPE"
                ],
                "value_ranges": {
                    "period": (0.001, 1.0),
                    "timeout": (0.0, 10.0)
                }
            }

        constraint_info.constraint_version = "4.0.0"
        constraint_info.constraint_source = "reference" if use_references else "transmission"

        logger.info(
            f"Prepared constraint info: level={constraint_level}, mode={'reference' if use_references else 'transmission'}")
        return constraint_info

    def _load_gbnf_grammar(self) -> str:
        """加载GBNF语法文件（传统模式）"""
        gbnf_file = self.artifacts_dir / "grammar" / "autosar.gbnf"
        try:
            if gbnf_file.exists():
                with open(gbnf_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    logger.info(f"Loaded GBNF grammar: {len(content)} characters")
                    return content
            else:
                logger.warning(f"GBNF file not found: {gbnf_file}")
                return ""
        except Exception as e:
            logger.error(f"Failed to load GBNF grammar: {e}")
            return ""

    def _load_allowed_tokens(self) -> List[str]:
        """加载允许的tokens（传统模式）"""
        tokens_file = self.artifacts_dir / "raw" / "autosar_allowed_tokens.py"

        if not tokens_file.exists():
            logger.warning(f"Allowed-tokens file not found: {tokens_file}, using default set")
            return self._get_default_autosar_tokens()

        try:
            from importlib.machinery import SourceFileLoader
            mod = SourceFileLoader("autosar_tokens_stub", str(tokens_file)).load_module()
            if hasattr(mod, "ALLOWED_TOKENS") and isinstance(mod.ALLOWED_TOKENS, list):
                logger.info(f"Loaded {len(mod.ALLOWED_TOKENS)} allowed tokens from stub")
                return mod.ALLOWED_TOKENS
            else:
                logger.warning("ALLOWED_TOKENS not found in stub, falling back to default")
                return self._get_default_autosar_tokens()
        except Exception as e:
            logger.error(f"Failed to import allowed tokens: {e}")
            return self._get_default_autosar_tokens()

    def _get_default_autosar_tokens(self) -> List[str]:
        """获取默认AUTOSAR tokens"""
        return [
            # XML基础
            "<", ">", "/", "=", '"',
            "<?xml", "version", "encoding", "UTF-8",

            # AUTOSAR结构
            "AUTOSAR", "AR-PACKAGES", "AR-PACKAGE", "ELEMENTS",
            "APPLICATION-SW-COMPONENT-TYPE", "SHORT-NAME",

            # 端口
            "PORTS", "P-PORT-PROTOTYPE", "R-PORT-PROTOTYPE",

            # 行为
            "INTERNAL-BEHAVIOR", "RUNNABLES", "RUNNABLE-ENTITY",
            "EVENTS", "TIMING-EVENT", "PERIOD",

            # 常见组件名
            "BatteryTempMonitor", "MotorController", "SensorComponent",
            "MainRunnable", "StatusOutput", "SensorInput"
        ]

    def get_constraint_summary(self) -> Dict[str, Any]:
        """获取约束制品摘要"""
        return {
            "local_fsm_available": self.local_fsm_available,
            "local_gbnf_available": self.local_gbnf_available,
            "gbnf_loaded": len(self.gbnf_grammar) > 0,
            "gbnf_size": len(self.gbnf_grammar),
            "allowed_tokens_count": len(self.allowed_tokens_list),
            "artifacts_dir": str(self.artifacts_dir),
            "recommended_mode": "reference" if not (
                        self.local_fsm_available or self.local_gbnf_available) else "both_available"
        }


# src/client/full_client.py - 核心修改部分
# 在 FullAutosarClient 类中的 generate_and_validate_full 方法中修改：

"""
async def generate_and_validate_full(
    self,
    prompt: str,
    autosar_context: Dict[str, Any] = None,
    max_tokens: int = 1500,
    temperature: float = 0.3,
    top_p: float = 0.9,
    frequency_penalty: float = 0.1,
    presence_penalty: float = 0.1,
    constraint_level: str = "mixed"  # "simple", "mixed", "full", "gbnf_only"
) -> FullGenerationResponse:
    # 现有代码...

    # 🔥 关键修改：优先使用引用模式
    try:
        # 尝试引用模式（推荐）
        constraint_info = self.constraint_preparer.prepare_constraint_info(
            constraint_level=constraint_level,
            use_references=True  # 优先使用引用
        )

        request = EnhancedGenerationRequest(
            request_id=str(uuid.uuid4()),
            timestamp=time.time(),
            prompt=prompt,
            constraint_info=constraint_info,
            autosar_context=autosar_context or {},
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            client_version="4.0.0"
        )

        logger.info(f"Using constraint mode: {constraint_info.constraint_source}")
        logger.info(f"FSM ref: {constraint_info.fsm_ref}, GBNF ref: {constraint_info.gbnf_ref}")

        # 发送请求...
        # 其余代码保持不变

    except Exception as e:
        logger.error(f"Reference mode failed, falling back to transmission mode: {e}")

        # Fallback到传统模式
        constraint_info = self.constraint_preparer.prepare_constraint_info(
            constraint_level=constraint_level,
            use_references=False  # 使用传统传输
        )
        # ... 重新构建请求并发送
"""