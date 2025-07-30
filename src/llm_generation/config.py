"""config.py - 系统配置管理

统一管理LLM API、知识图谱、对话系统等配置参数
完全基于YAML配置文件，无硬编码
"""
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
import yaml
from dataclasses import dataclass

# 基础路径配置 - 修正路径逻辑
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent.parent  # 项目根目录
CONFIG_DIR = ROOT_DIR / "config"   # 配置文件目录


@dataclass
class ComponentType:
    """组件类型配置"""
    name: str
    description: str
    scenarios: List[str]
    complexity: str


@dataclass
class InterfaceType:
    """接口类型配置"""
    name: str
    description: str
    communication_mode: str
    scenarios: List[str]


@dataclass
class DesignPattern:
    """设计模式配置"""
    name: str
    components: List[str]
    interfaces: List[str]
    scenarios: List[str]


@dataclass
class TerminologyConfig:
    """术语库配置"""
    component_types: List[ComponentType]
    interface_types: List[InterfaceType]
    design_patterns: List[DesignPattern]


@dataclass
class LLMConfig:
    """LLM配置"""
    model_name: str
    llm_api_url: str
    api_key: str
    temperature: float
    max_output_tokens: int
    max_context_tokens: int


@dataclass
class ConversationConfig:
    """对话配置"""
    session_ttl: int
    enable_memory: bool


@dataclass
class KnowledgeGraphConfig:
    """知识图谱配置"""
    neo4j_uri: str
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""
    max_schema_depth: int = 7


@dataclass
class SystemConfig:
    """系统总配置"""
    llm: LLMConfig
    conversation: ConversationConfig
    knowledge_graph: KnowledgeGraphConfig
    terminology: TerminologyConfig
    debug_mode: bool
    output_dir: Path


def _create_component_types(data: List[Dict]) -> List[ComponentType]:
    """创建组件类型列表"""
    return [
        ComponentType(
            name=item["name"],
            description=item["description"],
            scenarios=item["scenarios"],
            complexity=item["complexity"]
        )
        for item in data
    ]


def _create_interface_types(data: List[Dict]) -> List[InterfaceType]:
    """创建接口类型列表"""
    return [
        InterfaceType(
            name=item["name"],
            description=item["description"],
            communication_mode=item["communication_mode"],
            scenarios=item["scenarios"]
        )
        for item in data
    ]


def _create_design_patterns(data: List[Dict]) -> List[DesignPattern]:
    """创建设计模式列表"""
    return [
        DesignPattern(
            name=item["name"],
            components=item["components"],
            interfaces=item["interfaces"],
            scenarios=item["scenarios"]
        )
        for item in data
    ]


# config.py 修正版本
def load_config(config_path: Optional[Path] = None) -> SystemConfig:
    """加载系统配置"""

    # 确定配置文件路径
    if config_path is None:
        config_path = CONFIG_DIR / "llm_api_config.yaml"

    # 检查配置文件是否存在
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    try:
        # 读取YAML配置
        with open(config_path, 'r', encoding='utf-8') as f:
            yaml_config = yaml.safe_load(f)

        # 从环境变量读取敏感信息，如果yaml中没有配置的话
        api_key = yaml_config.get("llm", {}).get("api_key", "")
        if not api_key:
            api_key = os.getenv("LLM_API_KEY", "")
            if not api_key:
                raise ValueError("LLM API Key未配置：请在yaml文件中配置api_key或设置LLM_API_KEY环境变量")

        # Neo4j配置处理 - 支持多种字段名
        kg_config = yaml_config.get("knowledge_graph", {})
        neo4j_password = kg_config.get("neo4j_password", "")
        if not neo4j_password:
            neo4j_password = os.getenv("NEO4J_PASSWORD", "")

        # 兼容user和neo4j_user两种字段名
        neo4j_user = kg_config.get("neo4j_user") or kg_config.get("user", "neo4j")

        # 构建配置对象
        config = SystemConfig(
            llm=LLMConfig(
                model_name=yaml_config["llm"]["model_name"],
                llm_api_url=yaml_config["llm"]["llm_api_url"],
                api_key=api_key,
                temperature=yaml_config["llm"]["temperature"],
                max_output_tokens=yaml_config["llm"]["max_output_tokens"],
                max_context_tokens=yaml_config["llm"]["max_context_tokens"]
            ),
            conversation=ConversationConfig(
                session_ttl=yaml_config["conversation"]["session_ttl"],
                enable_memory=yaml_config["conversation"]["enable_memory"]
            ),
            knowledge_graph=KnowledgeGraphConfig(
                neo4j_uri=kg_config["neo4j_uri"],
                neo4j_user=neo4j_user,  # 修正：兼容两种字段名
                neo4j_password=neo4j_password,
                max_schema_depth=kg_config["max_schema_depth"]
            ),
            terminology=TerminologyConfig(
                component_types=_create_component_types(yaml_config["terminology"]["component_types"]),
                interface_types=_create_interface_types(yaml_config["terminology"]["interface_types"]),
                design_patterns=_create_design_patterns(yaml_config["terminology"]["design_patterns"])
            ),
            debug_mode=yaml_config["debug_mode"],
            output_dir=Path(yaml_config["output_dir"]).resolve()
        )

        # 创建输出目录
        config.output_dir.mkdir(exist_ok=True, parents=True)

        # 验证配置
        _validate_config(config)

        return config

    except yaml.YAMLError as e:
        raise ValueError(f"YAML配置文件格式错误: {e}")
    except KeyError as e:
        raise ValueError(f"配置文件缺少必需字段: {e}")
    except Exception as e:
        raise ValueError(f"加载配置失败: {e}")


def _validate_config(config: SystemConfig):
    """验证配置有效性"""

    # 验证LLM配置
    if not config.llm.api_key:
        raise ValueError("LLM API Key不能为空")

    if not config.llm.model_name:
        raise ValueError("LLM模型名称不能为空")

    # 验证Neo4j配置
    if config.knowledge_graph.neo4j_uri:
        if not config.knowledge_graph.neo4j_uri.startswith(('bolt://', 'neo4j://', 'neo4j+s://', 'neo4j+ssc://')):
            raise ValueError("Neo4j URI格式不正确")

    # 验证术语库配置
    if not config.terminology.component_types:
        raise ValueError("至少需要配置一个组件类型")

    if not config.terminology.interface_types:
        raise ValueError("至少需要配置一个接口类型")

    # 验证输出目录
    if not config.output_dir.is_absolute():
        raise ValueError("输出目录必须是绝对路径")


def get_config_info() -> Dict[str, Any]:
    """获取配置信息概览"""
    return {
        "config_dir": str(CONFIG_DIR),
        "config_file": str(CONFIG_DIR / "llm_api_config.yaml"),
        "config_exists": (CONFIG_DIR / "llm_api_config.yaml").exists(),
        "base_dir": str(BASE_DIR),
        "root_dir": str(ROOT_DIR)
    }


# 全局配置实例
try:
    CONFIG = load_config()
    print(f"✅ 配置加载成功: {CONFIG_DIR / 'llm_api_config.yaml'}")
except Exception as e:
    print(f"❌ 配置加载失败: {e}")
    print(f"📁 配置文件位置: {CONFIG_DIR / 'llm_api_config.yaml'}")
    print(f"📋 配置信息: {get_config_info()}")
    sys.exit(1)