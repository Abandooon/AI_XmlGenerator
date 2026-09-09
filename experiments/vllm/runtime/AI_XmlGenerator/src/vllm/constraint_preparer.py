# src/client/constraint_preparer.py
import json
from importlib.machinery import SourceFileLoader
from pathlib import Path
from typing import Dict, List, Any

from src.client.constraint_models import ConstraintInfo

from ..utils.logger import get_logger

logger = get_logger(__name__)


class ConstraintPreparer:
    """本地约束准备器 - 准备约束信息发送到云端"""

    def __init__(self, artifacts_dir: str):
        self.artifacts_dir = Path(artifacts_dir)

        # 预加载约束制品
        self.gbnf_grammar = self._load_gbnf_grammar()
        self.fsm_data = self._load_fsm_data()
        self.allowed_tokens_list = self._load_allowed_tokens()

    def _load_gbnf_grammar(self) -> str:
        """加载GBNF语法文件"""
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

    def _load_fsm_data(self) -> Dict:
        """加载FSM数据"""
        fsm_file = self.artifacts_dir / "raw" / "autosar.fsm"
        try:
            if fsm_file.exists():
                with open(fsm_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"Loaded FSM data with {len(data.get('states', []))} states")
                    return data
            else:
                logger.warning(f"FSM file not found: {fsm_file}")
                return {}
        except Exception as e:
            logger.error(f"Failed to load FSM data: {e}")
            return {}



    def _load_allowed_tokens(self) -> List[str]:
        """加载 autosar_allowed_tokens.py 里的 ALLOWED_TOKENS 列表"""
        tokens_file = self.artifacts_dir / "raw" / "autosar_allowed_tokens.py"

        if not tokens_file.exists():
            logger.warning(f"Allowed-tokens file not found: {tokens_file}, using default set")
            return self._get_default_autosar_tokens()

        try:
            # 动态加载模块而不污染 sys.modules
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

    def prepare_constraint_info(self, constraint_level: str = "mixed",
                                current_state: str = "START",
                                use_references: bool = True) -> ConstraintInfo:
        """准备约束信息 - 支持引用和传统模式"""

        constraint_info = ConstraintInfo()

        if use_references:
            # 🔥 新模式：使用预加载引用（优先）
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
            # 🔄 传统模式：直接传输（兼容性保留）
            logger.info("Using traditional transmission mode")

            # 修正：只有mixed和full级别才启用GBNF
            if constraint_level in ["mixed", "full"]:
                constraint_info.gbnf_enabled = True
                constraint_info.grammar_rules = self.gbnf_grammar
            else:
                # simple级别不使用约束
                constraint_info.gbnf_enabled = False
                constraint_info.grammar_rules = ""

            if constraint_level in ["mixed", "full"]:
                constraint_info.fsm_enabled = True
                constraint_info.allowed_tokens = self.allowed_tokens_list
                constraint_info.current_state = current_state
            else:
                # simple级别不使用FSM
                constraint_info.fsm_enabled = False
                constraint_info.allowed_tokens = []
                constraint_info.current_state = None

        # 添加域特定约束（不变）
        if constraint_level == "full":
            constraint_info.domain_constraints = {
                "required_elements": [
                    "AUTOSAR", "AR-PACKAGES", "APPLICATION-SW-COMPONENT-TYPE"
                ],
                "value_ranges": {
                    "period": (0.001, 1.0),  # 1ms到1s
                    "timeout": (0.0, 10.0)  # 0到10秒
                }
            }

        # 添加版本信息
        constraint_info.constraint_version = "4.0.0"
        constraint_info.constraint_source = "reference" if use_references else "transmission"

        logger.info(
            f"Prepared constraint info: level={constraint_level}, mode={'reference' if use_references else 'transmission'}")
        return constraint_info

    def get_constraint_summary(self) -> Dict[str, Any]:
        """获取约束制品摘要"""
        return {
            "gbnf_loaded": len(self.gbnf_grammar) > 0,
            "gbnf_size": len(self.gbnf_grammar),
            "fsm_loaded": len(self.fsm_data) > 0,
            "fsm_states": len(self.fsm_data.get('states', [])),
            "allowed_tokens_count": len(self.allowed_tokens_list),
            "artifacts_dir": str(self.artifacts_dir)
        }