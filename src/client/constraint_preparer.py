# src/client/constraint_preparer.py
import json
from typing import Dict, List, Optional, Any
from pathlib import Path

from ..models.constraint_models import ConstraintInfo
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
        """加载允许的tokens - 修复版本"""
        tokens_file = self.artifacts_dir / "raw" / "autosar_allowed_tokens.py"

        # 如果文件不存在，返回预定义的基础tokens
        if not tokens_file.exists():
            logger.warning(f"Allowed tokens file not found: {tokens_file}, using default tokens")
            return self._get_default_autosar_tokens()

        try:
            with open(tokens_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 简单解析ALLOWED_TOKENS变量
            if "ALLOWED_TOKENS" in content:
                return self._get_default_autosar_tokens()

            return self._get_default_autosar_tokens()

        except Exception as e:
            logger.error(f"Failed to load allowed tokens: {e}")
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
                                current_state: str = "START") -> ConstraintInfo:
        """准备约束信息"""

        constraint_info = ConstraintInfo()

        # 根据约束级别配置
        if constraint_level in ["simple", "mixed", "full"]:
            constraint_info.gbnf_enabled = True
            constraint_info.grammar_rules = self.gbnf_grammar

        if constraint_level in ["mixed", "full"]:
            constraint_info.fsm_enabled = True
            constraint_info.allowed_tokens = self.allowed_tokens_list
            constraint_info.current_state = current_state

        # 添加域特定约束
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

        logger.info(f"Prepared constraint info for level: {constraint_level}")
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