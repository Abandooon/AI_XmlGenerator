"""config.py - 系统配置管理

统一管理LLM API、知识图谱、对话系统等配置参数
完全基于YAML配置文件，无硬编码
"""
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
import yaml
from dataclasses import dataclass, field

# 基础路径配置 - 修正路径逻辑
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent.parent  # 项目根目录
CONFIG_DIR = ROOT_DIR / "config"   # 配置文件目录

# 在 config.py 中添加/修改以下数据类定义

@dataclass
class ComponentTypesConfig:
    """组件类型配置"""
    allowed_types: List[str] = field(default_factory=list)
    required_attributes: List[str] = field(default_factory=list)
    optional_attributes: List[str] = field(default_factory=list)


@dataclass
class InterfaceTypesConfig:
    """接口类型配置"""
    allowed_types: List[str] = field(default_factory=list)
    required_attributes: List[str] = field(default_factory=list)
    optional_attributes: List[str] = field(default_factory=list)


@dataclass
class ModeDeclarationGroupConfig:
    """模式声明组配置"""
    required_attributes: List[str] = field(default_factory=list)
    optional_attributes: List[str] = field(default_factory=list)


@dataclass
class OutputSchemaFieldConfig:
    """输出Schema字段配置"""
    required_fields: List[str] = field(default_factory=list)
    optional_fields: List[str] = field(default_factory=list)


@dataclass
class OutputSchemaConfig:
    """输出Schema配置"""
    system_analysis: OutputSchemaFieldConfig = field(default_factory=OutputSchemaFieldConfig)
    component_plan: OutputSchemaFieldConfig = field(default_factory=OutputSchemaFieldConfig)
    interface_plan: OutputSchemaFieldConfig = field(default_factory=OutputSchemaFieldConfig)


@dataclass
class Round1SchemaConfig:
    """Round1 Schema配置 - 完整的嵌套结构"""
    component_types: ComponentTypesConfig = field(default_factory=ComponentTypesConfig)
    interface_types: InterfaceTypesConfig = field(default_factory=InterfaceTypesConfig)
    mode_declaration_group: ModeDeclarationGroupConfig = field(default_factory=ModeDeclarationGroupConfig)
    output_schema: OutputSchemaConfig = field(default_factory=OutputSchemaConfig)

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
    enable_file_upload: bool


@dataclass
class ConversationConfig:
    """对话配置"""
    session_ttl: int
    enable_memory: bool

@dataclass
class MemoryConfig:
    """内存管理配置"""
    session_ttl: int
    max_session_history: int
    enable_user_preferences: bool
    storage_backend: str
    cache_size: int

@dataclass
class KnowledgeGraphConfig:
    """知识图谱配置"""
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    max_safety_depth: int


@dataclass
class TerminationRulesConfig:
    """终止条件规则配置"""
    ref_suffixes: List[str] = field(default_factory=lambda: ["-REF", "-TREF", "-IREF"])
    standard_prefixes: List[str] = field(default_factory=lambda: ["/AUTOSAR/", "/DataTypes/"])


@dataclass
class CacheConfig:
    """缓存配置"""
    enable_request_cache: bool
    enable_application_cache: bool
    application_cache_ttl: int
    max_cache_size: int

@dataclass
class SchemaPerformanceConfig:
    """Schema生成性能配置"""
    query_timeout: int
    max_properties_per_object: int
    parallel_query: bool


@dataclass
class SchemaGenerationConfig:
    """Schema生成配置"""
    termination_rules: TerminationRulesConfig = field(default_factory=TerminationRulesConfig)
    cache_config: CacheConfig = field(default_factory=CacheConfig)
    performance: SchemaPerformanceConfig = field(default_factory=SchemaPerformanceConfig)


@dataclass
class StandardTypesConfig:
    """标准数据类型配置"""
    standard_types_path: Optional[str] = None


@dataclass
class GenerationConfig:
    """生成配置"""
    single_batch_threshold: int
    max_batch_size: int
    enable_semantic_placeholders: bool
    reference_resolution_timeout: int
    max_schema_injection_depth: int


@dataclass
class SemanticPattern:
    """语义模式配置"""
    pattern: str
    type: str
    template: str


@dataclass
class SemanticResolutionConfig:
    """语义解析配置"""
    identifiers: List[str]
    patterns: List[SemanticPattern]
    function_mappings: Dict[str, List[str]]
    fuzzy_match_threshold: float
    enable_heuristic_resolution: bool
    resolution_cache_size: int


@dataclass
class MetamodelInjectionConfig:
    """元模型注入配置"""
    round1_depth: int
    round2_depth: int
    include_required_attributes: bool
    include_min_occurs: bool


@dataclass
class SystemConfig:
    """系统总配置"""
    llm: LLMConfig
    conversation: ConversationConfig
    memory: MemoryConfig
    knowledge_graph: KnowledgeGraphConfig
    standard_types: StandardTypesConfig
    terminology: TerminologyConfig
    generation: GenerationConfig
    semantic_resolution: SemanticResolutionConfig
    schema_generation: SchemaGenerationConfig  # 新增
    round1_schema: Round1SchemaConfig  # 新增
    metamodel_injection: MetamodelInjectionConfig  # 新增
    debug_mode: bool
    output_dir: Path


def _load_round1_schema_config(yaml_config: dict) -> Round1SchemaConfig:
    """从YAML配置加载Round1Schema配置"""
    round1_yaml = yaml_config.get("round1_schema", {})


    # 加载组件类型配置
    component_types_yaml = round1_yaml.get("component_types", {})
    component_types_config = ComponentTypesConfig(
        allowed_types=component_types_yaml.get("allowed_types", []),
        required_attributes=component_types_yaml.get("required_attributes", []),
        optional_attributes=component_types_yaml.get("optional_attributes", [])
    )

    # 加载接口类型配置
    interface_types_yaml = round1_yaml.get("interface_types", {})
    interface_types_config = InterfaceTypesConfig(
        allowed_types=interface_types_yaml.get("allowed_types", []),
        required_attributes=interface_types_yaml.get("required_attributes", []),
        optional_attributes=interface_types_yaml.get("optional_attributes", [])
    )



    # 加载模式声明组配置
    mode_group_yaml = round1_yaml.get("mode_declaration_group", {})
    mode_group_config = ModeDeclarationGroupConfig(
        required_attributes=mode_group_yaml.get("required_attributes", []),
        optional_attributes=mode_group_yaml.get("optional_attributes", [])
    )

    # 加载输出Schema配置
    output_schema_yaml = round1_yaml.get("output_schema", {})

    system_analysis_yaml = output_schema_yaml.get("system_analysis", {})
    system_analysis_config = OutputSchemaFieldConfig(
        required_fields=system_analysis_yaml.get("required_fields", []),
        optional_fields=system_analysis_yaml.get("optional_fields", [])
    )

    component_plan_yaml = output_schema_yaml.get("component_plan", {})
    component_plan_config = OutputSchemaFieldConfig(
        required_fields=component_plan_yaml.get("required_fields", []),
        optional_fields=component_plan_yaml.get("optional_fields", [])
    )

    interface_plan_yaml = output_schema_yaml.get("interface_plan", {})
    interface_plan_config = OutputSchemaFieldConfig(
        required_fields=interface_plan_yaml.get("required_fields", []),
        optional_fields=interface_plan_yaml.get("optional_fields", [])
    )

    output_schema_config = OutputSchemaConfig(
        system_analysis=system_analysis_config,
        component_plan=component_plan_config,
        interface_plan=interface_plan_config
    )

    return Round1SchemaConfig(
        component_types=component_types_config,
        interface_types=interface_types_config,
        mode_declaration_group=mode_group_config,
        output_schema=output_schema_config
    )

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

        # Neo4j配置处理
        kg_config = yaml_config.get("knowledge_graph", {})
        neo4j_password = kg_config.get("neo4j_password", "")
        neo4j_user = kg_config.get("neo4j_user", "neo4j")

        # 兼容性处理：如果配置中还是max_schema_depth，转换为max_safety_depth
        max_safety_depth = kg_config.get("max_safety_depth",
                                         kg_config.get("max_schema_depth", 50))

        # 标准数据类型配置
        standard_types = yaml_config.get("standard_types", {})

        # 生成配置
        generation_config = yaml_config.get("generation", {})

        # 语义解析配置
        semantic_config = yaml_config.get("semantic_resolution", {})
        patterns = []
        for pattern_data in semantic_config.get("patterns", []):
            patterns.append(SemanticPattern(
                pattern=pattern_data["pattern"],
                type=pattern_data["type"],
                template=pattern_data["template"]
            ))

        # Schema生成配置
        schema_gen_config = yaml_config.get("schema_generation", {})
        termination_config = schema_gen_config.get("termination_rules", {})
        cache_config = schema_gen_config.get("cache_config", {})
        perf_config = schema_gen_config.get("performance", {})

        # Round1 Schema配置
        round1_schema_config = yaml_config.get("round1_schema", {})

        # 元模型注入配置
        metamodel_config = yaml_config.get("metamodel_injection", {})

        memory_config = yaml_config.get("memory", {})

        # 构建配置对象
        config = SystemConfig(
            llm=LLMConfig(
                model_name=yaml_config["llm"]["model_name"],
                llm_api_url=yaml_config["llm"]["llm_api_url"],
                api_key=api_key,
                temperature=yaml_config["llm"]["temperature"],
                max_output_tokens=yaml_config["llm"]["max_output_tokens"],
                max_context_tokens=yaml_config["llm"]["max_context_tokens"],
                enable_file_upload=yaml_config["llm"].get("enable_file_upload")
            ),
            conversation=ConversationConfig(
                session_ttl=yaml_config["conversation"]["session_ttl"],
                enable_memory=yaml_config["conversation"]["enable_memory"]
            ),
            memory=MemoryConfig(  # 新增
                session_ttl=memory_config.get("session_ttl", 86400),
                max_session_history=memory_config.get("max_session_history", 20),
                enable_user_preferences=memory_config.get("enable_user_preferences", True),
                storage_backend=memory_config.get("storage_backend", "memory"),
                cache_size=memory_config.get("cache_size", 100)
            ),
            knowledge_graph=KnowledgeGraphConfig(
                neo4j_uri=kg_config["neo4j_uri"],
                neo4j_user=neo4j_user,
                neo4j_password=neo4j_password,
                max_safety_depth=max_safety_depth  # 使用新字段
            ),
            generation=GenerationConfig(
                single_batch_threshold=generation_config.get("single_batch_threshold", 5),
                max_batch_size=generation_config.get("max_batch_size", 8),
                enable_semantic_placeholders=generation_config.get("enable_semantic_placeholders", True),
                reference_resolution_timeout=generation_config.get("reference_resolution_timeout", 300),
                max_schema_injection_depth=generation_config.get("max_schema_injection_depth",15),
            ),
            semantic_resolution=SemanticResolutionConfig(
                identifiers=semantic_config.get("identifiers", []),
                patterns=patterns,
                function_mappings=semantic_config.get("function_mappings", {}),
                fuzzy_match_threshold=semantic_config.get("fuzzy_match_threshold", 0.6),
                enable_heuristic_resolution=semantic_config.get("enable_heuristic_resolution", True),
                resolution_cache_size=semantic_config.get("resolution_cache_size", 1000)
            ),
            schema_generation=SchemaGenerationConfig(
                termination_rules=TerminationRulesConfig(
                    ref_suffixes=termination_config.get("ref_suffixes", ["-REF", "-TREF", "-IREF"]),
                    standard_prefixes=termination_config.get("standard_prefixes", ["/AUTOSAR/", "/DataTypes/"])
                ),
                cache_config=CacheConfig(
                    enable_request_cache=cache_config.get("enable_request_cache", True),
                    enable_application_cache=cache_config.get("enable_application_cache", True),
                    application_cache_ttl=cache_config.get("application_cache_ttl", 3600),
                    max_cache_size=cache_config.get("max_cache_size", 100)
                ),
                performance=SchemaPerformanceConfig(
                    query_timeout=perf_config.get("query_timeout", 30),
                    max_properties_per_object=perf_config.get("max_properties_per_object", 1000),
                    parallel_query=perf_config.get("parallel_query", False)
                )
            ),
            round1_schema=_load_round1_schema_config(yaml_config),
            metamodel_injection=MetamodelInjectionConfig(
                round1_depth=metamodel_config.get("round1_depth", 1),
                round2_depth=metamodel_config.get("round2_depth", 8),
                include_required_attributes=metamodel_config.get("include_required_attributes", True),
                include_min_occurs=metamodel_config.get("include_min_occurs", True)
            ),
            standard_types=StandardTypesConfig(
                standard_types_path=standard_types.get("standard_types_path")
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

    # 验证安全深度配置
    if config.knowledge_graph.max_safety_depth < 10 or config.knowledge_graph.max_safety_depth > 100:
        raise ValueError("max_safety_depth应该在10-100之间")

    # 验证术语库配置
    if not config.terminology.component_types:
        raise ValueError("至少需要配置一个组件类型")

    if not config.terminology.interface_types:
        raise ValueError("至少需要配置一个接口类型")

    # 验证输出目录
    if not config.output_dir.is_absolute():
        raise ValueError("输出目录必须是绝对路径")

    # 验证Schema生成配置
    if config.schema_generation.performance.query_timeout <= 0:
        raise ValueError("查询超时时间必须大于0")

    if config.schema_generation.cache_config.max_cache_size <= 0:
        raise ValueError("缓存大小必须大于0")


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