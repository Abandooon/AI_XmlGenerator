# LLM生成框架设计 - 实现方案

*基于对话式逐层深入设计系统 V1.0*

---

## 1. 系统架构设计

### 1.1 目录结构

```
src/
└── llm_generation/
    ├── __init__.py
    ├── config.py                    # 配置管理
    ├── core/
    │   ├── __init__.py
    │   ├── conversation_manager.py  # 对话管理核心
    │   ├── memory_manager.py        # 短期记忆管理
    │   ├── round1_designer.py       # Round 1 架构设计器
    │   ├── round2_generator.py      # Round 2 详细生成器
    │   └── user_interaction.py      # 用户交互管理
    ├── document/
    │   ├── __init__.py
    │   ├── pdf_analyzer.py          # PDF文档分析器
    │   ├── content_extractor.py     # 内容提取器
    │   └── requirement_parser.py    # 需求解析器
    ├── knowledge/
    │   ├── __init__.py
    │   ├── terminology_builder.py   # 高层术语库构建
    │   ├── dynamic_query_engine.py  # 动态KG查询引擎
    │   └── constraint_engine.py     # 约束规则引擎
    ├── llm/
    │   ├── __init__.py
    │   ├── gemini_client.py         # Gemini API客户端
    │   ├── prompt_templates.py      # 提示词模板管理
    │   └── response_parser.py       # 响应解析器
    ├── utils/
    │   ├── __init__.py
    │   ├── validators.py            # 验证工具
    │   ├── serializers.py           # 序列化工具
    │   └── exceptions.py            # 异常定义
    ├── api/
    │   ├── __init__.py
    │   ├── endpoints.py             # API端点定义
    │   └── models.py                # 数据模型
    └── tests/
        ├── __init__.py
        ├── test_document/
        ├── test_core/
        ├── test_knowledge/
        └── test_llm/
```

---

## 2. 核心模块设计

### 2.1 对话管理核心 (`core/conversation_manager.py`)

#### 2.1.1 主要功能
- 统一对话流程控制
- 协调各个子模块交互
- 管理对话状态转换
- 处理异常和错误恢复

#### 2.1.2 核心类设计

**ConversationManager**
```python
class ConversationManager:
    """对话管理器 - 系统核心调度器"""
    
    # 主要属性
    - session_id: str                    # 会话唯一标识
    - memory_manager: MemoryManager      # 记忆管理器
    - round1_designer: Round1Designer    # Round 1设计器
    - round2_generator: Round2Generator  # Round 2生成器
    - user_interaction: UserInteraction  # 用户交互管理器
    - current_state: ConversationState   # 当前对话状态
```

#### 2.1.3 输入输出

**输入**:
- 用户初始需求文本
- 上传的PDF文档（可选）
- 用户反馈和修改要求

**输出**:
- 对话状态信息
- Round 1架构设计结果
- Round 2详细ARXML内容
- 完整的对话历史记录

#### 2.1.4 主要方法

| 方法名 | 功能描述 | 输入参数 | 返回值 |
|--------|----------|----------|---------|
| `start_conversation()` | 启动新对话会话 | user_input, pdf_file | session_info |
| `process_round1()` | 执行Round 1架构设计 | requirements, context | architecture_design |
| `handle_user_feedback()` | 处理用户反馈 | feedback, modifications | updated_design |
| `process_round2()` | 执行Round 2详细生成 | confirmed_design | arxml_content |
| `get_conversation_state()` | 获取当前对话状态 | - | conversation_state |

### 2.2 短期记忆管理 (`core/memory_manager.py`)

#### 2.2.1 主要功能
- 会话级上下文记忆存储
- 设计决策历史追踪
- 用户偏好临时学习
- 记忆生命周期管理

#### 2.2.2 核心类设计

**MemoryManager**
```python
class MemoryManager:
    """短期记忆管理器"""
    
    # 主要属性
    - session_memory: SessionMemory      # 会话记忆
    - design_history: List[DesignStep]   # 设计历史
    - user_preferences: UserPreferences  # 用户偏好
    - context_accumulator: ContextAccumulator  # 上下文累积器
```

#### 2.2.3 数据结构设计

**SessionMemory**
```python
@dataclass
class SessionMemory:
    session_id: str
    start_time: datetime
    current_round: int
    conversation_history: List[ConversationTurn]
    accumulated_context: AccumulatedContext
    current_design_state: DesignState
```

**ConversationTurn**
```python
@dataclass
class ConversationTurn:
    round_number: int
    user_input: str
    system_output: str
    design_artifacts: Dict[str, Any]
    user_feedback: Optional[str]
    modifications: List[str]
    timestamp: datetime
```

#### 2.2.4 输入输出

**输入**:
- 对话轮次数据
- 用户选择和反馈
- 设计决策记录
- 上下文更新信息

**输出**:
- 会话上下文摘要
- 用户偏好配置
- 历史决策参考
- 连续性提示信息

### 2.3 Round 1 架构设计器 (`core/round1_designer.py`)

#### 2.3.1 主要功能
- 高层架构设计生成
- 组件类型和数量确定
- 接口类型和连接设计
- 设计决策合理性分析

#### 2.3.2 核心类设计

**Round1Designer**
```python
class Round1Designer:
    """Round 1 架构设计器"""
    
    # 主要属性
    - terminology_builder: TerminologyBuilder  # 术语库构建器
    - gemini_client: GeminiClient             # Gemini客户端
    - design_validator: DesignValidator       # 设计验证器
    - template_manager: TemplateManager       # 模板管理器
```

#### 2.3.3 输入输出

**输入**:
- 结构化需求描述
- 领域上下文信息
- 用户偏好和历史
- 文档分析结果（如有）

**输出**:
- 架构设计方案JSON
- 组件规划详情
- 接口设计详情
- 连接拓扑描述
- 设计决策说明

#### 2.3.4 输出数据结构

**ArchitectureDesign**
```python
@dataclass
class ArchitectureDesign:
    system_analysis: SystemAnalysis
    component_plan: List[ComponentPlan]
    interface_plan: List[InterfacePlan]
    connection_topology: ConnectionTopology
    architecture_rationale: ArchitectureRationale
```

### 2.4 Round 2 详细生成器 (`core/round2_generator.py`)

#### 2.4.1 主要功能
- 详细ARXML文档生成
- 动态知识查询和应用
- 约束规则验证和应用
- 生成质量保证

#### 2.4.2 核心类设计

**Round2Generator**
```python
class Round2Generator:
    """Round 2 详细生成器"""
    
    # 主要属性
    - dynamic_query_engine: DynamicQueryEngine  # 动态查询引擎
    - constraint_engine: ConstraintEngine       # 约束引擎
    - gemini_client: GeminiClient              # Gemini客户端
    - arxml_validator: ARXMLValidator          # ARXML验证器
```

#### 2.4.3 输入输出

**输入**:
- 确认的架构设计
- 组件详细配置需求
- 相关约束和规则
- 用户自定义参数

**输出**:
- 完整ARXML文档
- 生成质量报告
- 约束验证结果
- 可追溯性映射

### 2.5 用户交互管理 (`core/user_interaction.py`)

#### 2.5.1 主要功能
- 设计结果可视化展示
- 用户反馈收集和处理
- 修改请求解析和应用
- 交互流程控制

#### 2.5.2 核心类设计

**UserInteraction**
```python
class UserInteraction:
    """用户交互管理器"""
    
    # 主要属性
    - visualization_engine: VisualizationEngine  # 可视化引擎
    - feedback_parser: FeedbackParser           # 反馈解析器
    - modification_handler: ModificationHandler  # 修改处理器
    - confirmation_manager: ConfirmationManager  # 确认管理器
```

#### 2.5.3 输入输出

**输入**:
- Round 1设计结果
- 用户反馈文本
- 修改指令
- 确认状态

**输出**:
- 可视化设计展示
- 反馈处理结果
- 修改后的设计方案
- 用户确认状态

---

## 3. 文档处理模块

### 3.1 PDF文档分析器 (`document/pdf_analyzer.py`)

#### 3.1.1 主要功能
- PDF文件读取和预处理
- 文本内容提取
- 结构化信息识别
- 多模态内容处理

#### 3.1.2 核心类设计

**PDFAnalyzer**
```python
class PDFAnalyzer:
    """PDF文档分析器"""
    
    # 主要属性
    - content_extractor: ContentExtractor    # 内容提取器
    - requirement_parser: RequirementParser  # 需求解析器
    - gemini_client: GeminiClient           # Gemini客户端（多模态）
```

#### 3.1.3 输入输出

**输入**:
- PDF文件路径或字节流
- 分析深度配置
- 用户偏好设置

**输出**:
- 提取的文本内容
- 结构化需求信息
- 图表和图像描述
- 分析置信度评分

### 3.2 内容提取器 (`document/content_extractor.py`)

#### 3.2.1 主要功能
- 多格式文档内容提取
- OCR图像文字识别
- 表格和列表结构化
- 元数据信息提取

#### 3.2.2 技术实现策略

**文档处理流水线**:
1. 文件格式识别和预处理
2. 文本内容提取（PyPDF2/pdfplumber）
3. 图像内容识别（Gemini Vision API）
4. 结构化元素解析
5. 内容质量评估和清洗

#### 3.2.3 输入输出

**输入**:
- 原始文档文件
- 提取配置参数
- 质量要求设置

**输出**:
- 结构化文本内容
- 提取的图像和图表
- 文档结构信息
- 提取质量报告

### 3.3 需求解析器 (`document/requirement_parser.py`)

#### 3.3.1 主要功能
- 需求文本智能分析
- 设计意图推理
- 技术要求提取
- 约束条件识别

#### 3.3.2 核心类设计

**RequirementParser**
```python
class RequirementParser:
    """需求解析器"""
    
    # 主要属性
    - llm_analyzer: LLMAnalyzer        # LLM分析器
    - intent_extractor: IntentExtractor # 意图提取器
    - constraint_detector: ConstraintDetector # 约束检测器
```

#### 3.3.3 输入输出

**输入**:
- 提取的文档内容
- 分析上下文信息
- 领域知识背景

**输出**:
- 结构化需求描述
- 推理的设计意图
- 提取的约束条件
- 技术背景信息

---

## 4. 知识管理模块

### 4.1 高层术语库构建 (`knowledge/terminology_builder.py`)

#### 4.1.1 主要功能
- 从KG提取核心概念
- 构建高层术语库
- 场景导向知识组织
- 术语库压缩和优化

#### 4.1.2 核心类设计

**TerminologyBuilder**
```python
class TerminologyBuilder:
    """高层术语库构建器"""
    
    # 主要属性
    - kg_client: KGClient                    # KG查询客户端
    - concept_extractor: ConceptExtractor    # 概念提取器
    - terminology_cache: TerminologyCache    # 术语库缓存
```

#### 4.1.3 输入输出

**输入**:
- 统一知识图谱数据
- 领域配置参数
- 使用频率统计

**输出**:
- 压缩的术语库
- 概念层次结构
- 使用场景映射
- 术语关联关系

### 4.2 动态KG查询引擎 (`knowledge/dynamic_query_engine.py`)

#### 4.2.1 主要功能
- 按需查询详细信息
- 批量查询优化
- 查询结果缓存
- 关联查询扩展

#### 4.2.2 核心类设计

**DynamicQueryEngine**
```python
class DynamicQueryEngine:
    """动态KG查询引擎"""
    
    # 主要属性
    - neo4j_client: Neo4jClient          # Neo4j客户端
    - query_optimizer: QueryOptimizer    # 查询优化器
    - result_cache: ResultCache          # 结果缓存
    - batch_processor: BatchProcessor    # 批处理器
```

#### 4.2.3 查询策略设计

**查询类型分类**:
- 组件详细信息查询：属性、子元素、约束规则
- 接口详细信息查询：数据元素、操作定义、通信规范
- 依赖关系查询：元素间依赖和引用关系
- 约束传播查询：相关约束的关联查询

#### 4.2.4 输入输出

**输入**:
- 组件/接口类型列表
- 查询深度配置
- 缓存策略参数

**输出**:
- 详细元素信息
- 关联关系数据
- 约束规则集合
- 查询性能报告

### 4.3 约束规则引擎 (`knowledge/constraint_engine.py`)

#### 4.3.1 主要功能
- 约束规则分类管理
- 上下文相关约束筛选
- 约束冲突检测
- 约束验证和应用

#### 4.3.2 核心类设计

**ConstraintEngine**
```python
class ConstraintEngine:
    """约束规则引擎"""
    
    # 主要属性
    - constraint_classifier: ConstraintClassifier  # 约束分类器
    - conflict_detector: ConflictDetector          # 冲突检测器
    - validator: ConstraintValidator               # 约束验证器
```

#### 4.3.3 约束分类体系

**语法约束**:
- XML Schema结构约束
- 数据类型和格式约束
- 基数约束(minOccurs/maxOccurs)

**语义约束**:
- ModelOCL业务规则
- 跨元素一致性约束
- 领域特定语义规则

**架构约束**:
- 组件间连接规则
- 接口兼容性规则
- 系统级约束规则

#### 4.3.4 输入输出

**输入**:
- 设计决策上下文
- 目标元素类型
- 约束应用范围

**输出**:
- 相关约束集合
- 约束优先级排序
- 冲突检测结果
- 验证建议

---

## 5. LLM接口模块

### 5.1 Gemini API客户端 (`llm/gemini_client.py`)

#### 5.1.1 主要功能
- Gemini API调用封装
- 请求重试和错误处理
- 响应解析和验证
- 性能监控和优化

#### 5.1.2 核心类设计

**GeminiClient**
```python
class GeminiClient:
    """Gemini API客户端"""
    
    # 主要属性
    - api_config: APIConfig              # API配置
    - retry_handler: RetryHandler        # 重试处理器
    - response_parser: ResponseParser    # 响应解析器
    - performance_monitor: PerformanceMonitor  # 性能监控器
```

#### 5.1.3 调用模式支持

**文本生成模式**:
- 纯文本输出
- 适用于Round 1架构设计
- 支持流式输出

**JSON模式**:
- 结构化JSON输出
- Response Schema约束
- 适用于Round 2详细生成

**多模态模式**:
- 文本+图像输入
- 适用于PDF文档分析
- 支持OCR和图像理解

#### 5.1.4 输入输出

**输入**:
- 提示词文本
- 生成配置参数
- 多模态内容（可选）

**输出**:
- 生成的文本内容
- Token使用统计
- 响应时间指标
- 质量评估结果

### 5.2 提示词模板管理 (`llm/prompt_templates.py`)

#### 5.2.1 主要功能
- 提示词模板定义和管理
- 动态参数替换
- 上下文注入策略
- 模板版本控制

#### 5.2.2 模板类型设计

**Round 1架构设计模板**:
- 系统分析提示词
- 组件规划提示词
- 接口设计提示词
- 架构合理性分析提示词

**Round 2详细生成模板**:
- ARXML生成提示词
- 约束应用提示词
- 质量验证提示词

**文档分析模板**:
- 需求理解提示词
- 设计意图推理提示词
- 约束提取提示词

#### 5.2.3 输入输出

**输入**:
- 模板标识符
- 动态参数字典
- 上下文信息

**输出**:
- 完整的提示词文本
- 参数替换日志
- 模板使用统计

### 5.3 响应解析器 (`llm/response_parser.py`)

#### 5.2.1 主要功能
- LLM响应格式解析
- 结构化数据提取
- 错误检测和修复
- 质量评估和过滤

#### 5.3.2 核心类设计

**ResponseParser**
```python
class ResponseParser:
    """响应解析器"""
    
    # 主要属性
    - json_parser: JSONParser            # JSON解析器
    - xml_parser: XMLParser              # XML解析器
    - quality_assessor: QualityAssessor  # 质量评估器
    - error_corrector: ErrorCorrector    # 错误修正器
```

#### 5.3.3 输入输出

**输入**:
- LLM原始响应
- 期望的输出格式
- 验证规则配置

**输出**:
- 解析后的结构化数据
- 质量评估报告
- 错误检测结果
- 修正建议

---

## 6. 工具模块

### 6.1 验证工具 (`utils/validators.py`)

#### 6.1.1 主要功能
- 数据格式验证
- JSON Schema验证
- ARXML语法验证
- 业务规则验证

#### 6.1.2 验证器类型

**SchemaValidator**:
- JSON Schema验证
- 数据结构完整性检查
- 类型约束验证

**ARXMLValidator**:
- XML语法验证
- AUTOSAR规范符合性
- 引用完整性检查

**BusinessRuleValidator**:
- 领域特定规则验证
- 约束条件检查
- 逻辑一致性验证

### 6.2 序列化工具 (`utils/serializers.py`)

#### 6.2.1 主要功能
- 对象序列化和反序列化
- 格式转换
- 数据压缩和解压
- 版本兼容性处理

### 6.3 异常定义 (`utils/exceptions.py`)

#### 6.3.1 异常层次设计

**系统级异常**:
- `LLMGenerationException`: 顶层异常基类
- `ConfigurationError`: 配置错误
- `ResourceNotFoundError`: 资源未找到

**业务级异常**:
- `DocumentAnalysisError`: 文档分析失败
- `ArchitectureDesignError`: 架构设计失败
- `ValidationError`: 验证失败

**技术级异常**:
- `LLMAPIError`: LLM API调用失败
- `KGQueryError`: 知识图谱查询失败
- `MemoryError`: 记忆管理失败

---

## 7. API接口设计

### 7.1 REST API端点 (`api/endpoints.py`)

#### 7.1.1 核心端点设计

**会话管理端点**:
- `POST /api/v1/conversation/start`: 启动新对话
- `GET /api/v1/conversation/{session_id}`: 获取会话状态
- `DELETE /api/v1/conversation/{session_id}`: 结束会话

**文档处理端点**:
- `POST /api/v1/document/analyze`: 上传并分析PDF文档
- `GET /api/v1/document/analysis/{analysis_id}`: 获取分析结果

**设计生成端点**:
- `POST /api/v1/design/round1`: 执行Round 1架构设计
- `POST /api/v1/design/round2`: 执行Round 2详细生成
- `POST /api/v1/design/feedback`: 处理用户反馈

**记忆管理端点**:
- `GET /api/v1/memory/session/{session_id}`: 获取会话记忆
- `PUT /api/v1/memory/session/{session_id}`: 更新会话记忆

### 7.2 数据模型 (`api/models.py`)

#### 7.2.1 请求/响应模型

**ConversationStartRequest**:
- user_input: 用户需求描述
- pdf_file: 上传的PDF文件（可选）
- preferences: 用户偏好设置

**ArchitectureDesignResponse**:
- session_id: 会话标识
- design_result: 架构设计结果
- confidence_score: 置信度评分
- next_steps: 后续步骤建议

---

## 8. 配置管理

### 8.1 配置文件结构 (`config.py`)

```yaml
# LLM配置
llm:
  provider: "gemini"
  model_name: "gemini-2.5-pro-preview-06-05"
  api_key_env: "LLM_API_KEY"
  api_base: "https://api.openai-proxy.org/google"
  max_context_tokens: 200000
  max_output_tokens: 60000
  temperature: 0.7
  top_p: 0.9

# 对话配置
conversation:
  session_ttl: 86400  # 24小时
  max_rounds: 10
  auto_save_interval: 300  # 5分钟

# 文档分析配置
document_analysis:
  max_file_size: 100MB
  supported_formats: ["pdf"]
  ocr_enabled: true
  analysis_timeout: 600

# 知识图谱配置
knowledge_graph:
  neo4j_uri: "bolt://localhost:7687"
  cache_ttl: 3600
  batch_query_size: 50

# 记忆管理配置
memory:
  storage_backend: "redis"
  redis_url: "redis://localhost:6379/1"
  max_session_history: 100
```

---

## 9. 部署和运维

### 9.1 容器化部署

**Docker配置**:
- 应用容器：Python + FastAPI
- 缓存容器：Redis
- 图数据库：Neo4j（可选，如果独立部署）

### 9.2 监控和日志

**关键指标监控**:
- API响应时间
- LLM调用成功率
- 文档分析成功率
- 用户会话活跃度

**日志级别设计**:
- DEBUG: 详细调试信息
- INFO: 关键操作记录
- WARN: 异常但可恢复的情况
- ERROR: 系统错误和失败

---

## 10. 测试策略

### 10.1 单元测试
- 每个模块独立测试
- Mock外部依赖
- 覆盖率目标：85%

### 10.2 集成测试
- 端到端流程测试
- 真实PDF文档测试
- 多轮对话场景测试

### 10.3 性能测试
- LLM API调用性能
- 并发用户支持能力
- 记忆存储性能

这个框架设计为实现对话式逐层深入设计系统提供了完整的技术架构，重点简化为PDF上传、短期记忆和Gemini 2.5 Pro单一模型，确保系统的可实现性和可维护性。


---------------------------------------------
# 集成web_ui设计
# 在config.py中新增API服务配置
api_service:
  host: "0.0.0.0"
  port: 8001
  cors_origins: ["http://localhost:3000"]
  
# 新增API接口定义
endpoints:
  - "/api/v1/conversation/start"
  - "/api/v1/conversation/round1" 
  - "/api/v1/conversation/round2"
  - "/api/v1/document/analyze"
  - 
src/llm_generation/
├── api/                    # 新增API层
│   ├── __init__.py
│   ├── main.py            # FastAPI应用入口
│   ├── routes/            # API路由定义
│   │   ├── conversation.py
│   │   ├── document.py
│   │   └── strategy.py
│   └── middleware/        # 中间件
└── (其他模块保持不变)