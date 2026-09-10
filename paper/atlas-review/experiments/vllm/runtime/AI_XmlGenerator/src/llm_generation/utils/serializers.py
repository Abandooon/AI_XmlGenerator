"""utils/serializers.py - 序列化工具

提供对象序列化和反序列化功能
"""
import json
import uuid
from dataclasses import dataclass, asdict, fields
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


def generate_uuid() -> str:
    """生成UUID字符串"""
    return str(uuid.uuid4())


def current_timestamp() -> str:
    """获取当前时间戳"""
    return datetime.now().isoformat()


@dataclass
class ArchitectureDesign:
    """架构设计数据结构"""
    system_analysis: Dict[str, str]
    component_plan: List[Dict[str, Any]]
    interface_plan: List[Dict[str, Any]]
    component_generation_order: List[str]
    connection_topology: Dict[str, Any]
    architecture_rationale: Dict[str, str]
    session_id: str = ""
    timestamp: str = ""

    def __post_init__(self):
        if not self.session_id:
            self.session_id = generate_uuid()
        if not self.timestamp:
            self.timestamp = current_timestamp()


@dataclass
class ConversationTurn:
    """对话轮次数据结构"""
    round_number: int
    user_input: str
    system_output: str
    design_artifacts: Dict[str, Any]
    user_feedback: Optional[str] = None
    modifications: List[str] = None
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = current_timestamp()
        if self.modifications is None:
            self.modifications = []


@dataclass
class SessionMemory:
    """会话记忆数据结构"""
    session_id: str
    start_time: str
    current_round: int
    conversation_history: List[ConversationTurn]
    accumulated_context: Dict[str, Any]
    current_design_state: Optional[ArchitectureDesign] = None

    def __post_init__(self):
        if not self.start_time:
            self.start_time = current_timestamp()


class EnhancedJSONEncoder(json.JSONEncoder):
    """增强的JSON编码器"""

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Path):
            return str(obj)
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        return super().default(obj)


def to_json(obj: Any, indent: int = 2) -> str:
    """将对象转换为JSON字符串"""
    if hasattr(obj, '__dict__'):
        # 如果是dataclass或其他对象，转换为字典
        if hasattr(obj, '__dataclass_fields__'):
            data = asdict(obj)
        else:
            data = obj.__dict__
    else:
        data = obj

    return json.dumps(data, cls=EnhancedJSONEncoder, ensure_ascii=False, indent=indent)


def from_json(json_str: str, target_class: type = None) -> Any:
    """从JSON字符串恢复对象"""
    data = json.loads(json_str)

    if target_class is None:
        return data

    # 如果目标类是dataclass，使用字段初始化
    if hasattr(target_class, '__dataclass_fields__'):
        field_names = {f.name for f in fields(target_class)}
        filtered_data = {k: v for k, v in data.items() if k in field_names}
        return target_class(**filtered_data)

    return data


def save_json(obj: Any, file_path: Union[str, Path]) -> None:
    """保存对象为JSON文件"""
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(to_json(obj))


def load_json(file_path: Union[str, Path], target_class: type = None) -> Any:
    """从JSON文件加载对象"""
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        json_str = f.read()

    return from_json(json_str, target_class)


def deep_merge(dict1: Dict, dict2: Dict) -> Dict:
    """深度合并两个字典"""
    result = dict1.copy()

    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value

    return result