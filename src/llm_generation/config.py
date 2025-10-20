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
class ConstraintEngineConfig:
    """约束引擎配置"""
    enabled: bool
    max_constraints_per_type: int
    constraint_types: List[str]
    exclude_standard_constraints: bool


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


# 在其他dataclass定义之后，Round1SchemaConfig定义之前添加：

@dataclass
class PortType:
    """端口类型定义"""
    name: str
    description: str


@dataclass
class EventType:
    """事件类型定义"""
    name: str
    description: str


@dataclass
class Round1ElementDesignConfig:
    """Round1元素设计配置"""
    port_types: List[PortType] = field(default_factory=list)
    event_types: List[EventType] = field(default_factory=list)

@dataclass
class RunnableElementDef:
    key: str
    xml_tag: Optional[str] = None           # 子项标签（如 VARIABLE-ACCESS）
    xml_wrapper_tag: Optional[str] = None   # 容器标签（如 DATA-SEND-POINTS）
    type: str = ""                          # 子项类型（如 VariableAccess）
    min: int = 0
    max: int = -1

@dataclass
class RunnableEntityConfig:
    """RunnableEntity配置"""
    required_elements: List[str] = field(default_factory=list)
    optional_elements: List[str] = field(default_factory=list)
    elements: List[RunnableElementDef] = field(default_factory=list)  # ← 新增

@dataclass
class UnionBranch:
    name: str
    selectable_children: List[str] = field(default_factory=list)  # 可以从中选择的子键（用于 Round1 让 LLM 精确选择 include）
    default_children: List[str] = field(default_factory=list)     # （可选）建议默认选择
    required_children: List[str] = field(default_factory=list)    # （可选）必须包含

@dataclass
class UnionSpec:
    of: str                               # 作用位置（如 "ACCESSED-VARIABLE" / "MODE-GROUP-IREF" / "SERVER-CALL-POINTS"）
    variants: List[UnionBranch] = field(default_factory=list)     # 可选分支（3选1/2选1/可多选）
    min_select: int = 1                   # 至少选择多少分支（SERVER-CALL-POINTS 可设为 1..2）
    max_select: int = 1                   # 至多选择多少分支

@dataclass
class Round1PreselectConfig:
    unions: List[UnionSpec] = field(default_factory=list)

@dataclass
class Round1SchemaConfig:
    """Round1 Schema配置 - 完整的嵌套结构"""
    component_types: ComponentTypesConfig = field(default_factory=ComponentTypesConfig)
    interface_types: InterfaceTypesConfig = field(default_factory=InterfaceTypesConfig)
    mode_declaration_group: ModeDeclarationGroupConfig = field(default_factory=ModeDeclarationGroupConfig)
    output_schema: OutputSchemaConfig = field(default_factory=OutputSchemaConfig)
    round1_element_design: Round1ElementDesignConfig = field(default_factory=Round1ElementDesignConfig)
    runnable_entity_config: RunnableEntityConfig = field(default_factory=RunnableEntityConfig)
    preselect: Round1PreselectConfig = field(default_factory=Round1PreselectConfig)


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

    # 新增：分阶段温度
    stage_temperatures: Dict[str, float] = field(default_factory=dict)

    def get_temperature(self, stage: str = None) -> float:
        """获取指定阶段的温度"""
        if stage and stage in self.stage_temperatures:
            return self.stage_temperatures[stage]
        return self.temperature


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
    constraint_engine: ConstraintEngineConfig
    debug_mode: bool
    output_dir: Path


def _load_round1_schema_config(yaml_config: dict) -> Round1SchemaConfig:
    """从YAML配置加载Round1Schema配置（增强版：合并多来源、显式校验、兜底）"""
    round1_yaml = yaml_config.get("round1_schema", {}) or {}

    # ---------- 组件类型 ----------
    component_types_yaml = round1_yaml.get("component_types", {}) or {}
    component_types_config = ComponentTypesConfig(
        allowed_types=component_types_yaml.get("allowed_types", []) or [],
        required_attributes=component_types_yaml.get("required_attributes", []) or [],
        optional_attributes=component_types_yaml.get("optional_attributes", []) or [],
    )

    # ---------- 接口类型 ----------
    interface_types_yaml = round1_yaml.get("interface_types", {}) or {}
    interface_types_config = InterfaceTypesConfig(
        allowed_types=interface_types_yaml.get("allowed_types", []) or [],
        required_attributes=interface_types_yaml.get("required_attributes", []) or [],
        optional_attributes=interface_types_yaml.get("optional_attributes", []) or [],
    )

    # ---------- 模式声明组 ----------
    mode_group_yaml = round1_yaml.get("mode_declaration_group", {}) or {}
    mode_group_config = ModeDeclarationGroupConfig(
        required_attributes=mode_group_yaml.get("required_attributes", []) or [],
        optional_attributes=mode_group_yaml.get("optional_attributes", []) or [],
    )

    # ---------- 输出字段（Round1 顶层产物） ----------
    output_schema_yaml = round1_yaml.get("output_schema", {}) or {}

    def _field_cfg(sec: str) -> OutputSchemaFieldConfig:
        sec_yaml = output_schema_yaml.get(sec, {}) or {}
        return OutputSchemaFieldConfig(
            required_fields=sec_yaml.get("required_fields", []) or [],
            optional_fields=sec_yaml.get("optional_fields", []) or [],
        )

    system_analysis_config = _field_cfg("system_analysis")
    component_plan_config = _field_cfg("component_plan")
    interface_plan_config = _field_cfg("interface_plan")

    output_schema_config = OutputSchemaConfig(
        system_analysis=system_analysis_config,
        component_plan=component_plan_config,
        interface_plan=interface_plan_config,
    )

    # ---------- Runnable 元素目录（关键：合并多来源 + 兜底 + 校验） ----------
    runnable_cfg_yaml = round1_yaml.get("runnable_entity_config", {}) or {}

    # 来源 1：首选（推荐）
    elems_yaml_1 = runnable_cfg_yaml.get("elements", []) or []

    # 来源 2：历史备选（有的项目把它写在 round1_element_design 里）
    alt_yaml = round1_yaml.get("round1_element_design", {}) or {}
    elems_yaml_2 = alt_yaml.get("runnable_elements", []) or []

    # 旧字段：只给 key 兜底
    req_keys = runnable_cfg_yaml.get("required_elements", []) or []
    opt_keys = runnable_cfg_yaml.get("optional_elements", []) or []

    # 合并：1 优先；2 追加；最后把旧字段转为最小定义兜底
    elem_defs: List[RunnableElementDef] = []

    def _append_elem(defs: List[RunnableElementDef], e: dict):
        if not isinstance(e, dict):
            return
        key = e.get("key")
        if not key:
            return
        defs.append(RunnableElementDef(
            key=key,
            xml_tag=e.get("xml_tag"),
            xml_wrapper_tag=e.get("xml_wrapper_tag"),
            type=e.get("type", "") or "",
            min=int(e.get("min", 0) or 0),
            max=int(e.get("max", -1) or -1),
        ))

    # 先加来源 1（官方推荐位置）
    for e in elems_yaml_1:
        _append_elem(elem_defs, e)

    # 再加来源 2（历史位置），按 key 去重
    seen_keys = {d.key for d in elem_defs}
    for e in elems_yaml_2:
        if isinstance(e, dict) and e.get("key") and e.get("key") not in seen_keys:
            _append_elem(elem_defs, e)
            seen_keys.add(e.get("key"))

    # 兜底：旧字段 required/optional → 仅 key 的最小定义
    if not elem_defs:
        merged_keys = []
        for k in (req_keys + opt_keys):
            if k and k not in merged_keys:
                merged_keys.append(k)
        for k in merged_keys:
            elem_defs.append(RunnableElementDef(key=k))

    # 显式校验：仍然为空就报错（不要把空枚举悄悄传下去）
    if not elem_defs:
        raise ValueError(
            "round1_schema.runnable_entity_config.elements 为空，且未提供 "
            "round1_element_design.runnable_elements 或 required/optional 兜底。"
        )

    runnable_entity_config = RunnableEntityConfig(
        required_elements=req_keys,
        optional_elements=opt_keys,
        elements=elem_defs,
    )

    # ---------- Round1 内部元素类型（端口/事件清单） ----------
    port_types_list: List[PortType] = []
    for p in alt_yaml.get("port_types", []) or []:
        name = p.get("name", "")
        if not name:
            continue
        port_types_list.append(PortType(
            name=name,
            description=p.get("description", ""),
        ))

    event_types_list: List[EventType] = []
    for ev in alt_yaml.get("event_types", []) or []:
        name = ev.get("name", "")
        if not name:
            continue
        event_types_list.append(EventType(
            name=name,
            description=ev.get("description", ""),
        ))

    round1_element_design_config = Round1ElementDesignConfig(
        port_types=port_types_list,
        event_types=event_types_list,
    )

    # ---------- preselect（unions/variants） ----------
    preselect_yaml = round1_yaml.get("preselect", {}) or {}
    unions_cfg: List[UnionSpec] = []

    for u in preselect_yaml.get("unions", []) or []:
        of_name = u.get("of")
        if not of_name:
            continue  # 跳过无 of 的条目

        branches: List[UnionBranch] = []
        for b in (u.get("variants") or []):
            vname = b.get("name")
            if not vname:
                continue  # 跳过无 name 的分支
            branches.append(UnionBranch(
                name=vname,
                selectable_children=b.get("selectable_children", []) or [],
                default_children=b.get("default_children", []) or [],
                required_children=b.get("required_children", []) or [],
            ))

        unions_cfg.append(UnionSpec(
            of=of_name,
            variants=branches,
            min_select=int(u.get("min_select", 1) or 1),
            max_select=int(u.get("max_select", 1) or 1),
        ))

    preselect_config = Round1PreselectConfig(unions=unions_cfg)

    # ---------- 汇总 ----------
    return Round1SchemaConfig(
        component_types=component_types_config,
        interface_types=interface_types_config,
        mode_declaration_group=mode_group_config,
        output_schema=output_schema_config,
        round1_element_design=round1_element_design_config,
        runnable_entity_config=runnable_entity_config,
        preselect=preselect_config,
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

        # 约束引擎配置（新增）
        constraint_config = yaml_config.get("constraint_engine", {})

        # 加载分阶段温度
        stage_temps = yaml_config["llm"].get("stage_temperatures", {})

        # 构建配置对象
        config = SystemConfig(
            llm=LLMConfig(
                model_name=yaml_config["llm"]["model_name"],
                llm_api_url=yaml_config["llm"]["llm_api_url"],
                api_key=api_key,
                temperature=yaml_config["llm"]["temperature"],
                stage_temperatures=stage_temps,  # 新增
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
            constraint_engine=ConstraintEngineConfig(
            enabled=constraint_config.get("enabled"),
            max_constraints_per_type=constraint_config.get("max_constraints_per_type"),
            constraint_types=constraint_config.get("constraint_types", ["MODEL_OCL", "DATA_TYPE"]),
            exclude_standard_constraints=constraint_config.get("exclude_standard_constraints")
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