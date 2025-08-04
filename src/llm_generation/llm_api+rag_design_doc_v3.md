# AUTOSAR ASW LLM生成器设计文档 v3

## 1. 设计理念与核心思想

### 1.1 总体设计理念

本项目采用**"架构优先、渐进细化、知识复用"**的设计理念，通过LLM驱动的两轮对话生成AUTOSAR ASW组件。核心创新在于：

- **分层抽象**：将AUTOSAR复杂度分解为架构层和实现层
- **知识积累**：建立可复用的标准类型库和模式库
- **智能引导**：LLM专注于架构决策，确定性内容通过模板和引用处理
- **交互优化**：通过用户确认机制确保生成结果符合需求

### 1.2 设计原则

1. **20-80原则**：20%的架构元素决定80%的系统行为
2. **关注点分离**：架构设计与实现细节分离
3. **积累-复用-扩展**：标准组件的持续积累和复用
4. **最小化LLM负担**：让LLM专注于创造性任务

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        用户接口层                             │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   主程序     │  │  交互管理器   │  │   结果展示器     │  │
│  │   (main)    │  │(interaction) │  │  (presenter)    │  │
│  └─────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      核心生成层                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                  生成流程控制器                        │  │
│  │  ┌──────────┐  ┌──────────┐  ┌─────────────────┐  │  │
│  │  │  Round1   │  │  Round2   │  │   结果组装器     │  │  │
│  │  │ Designer  │  │ Generator │  │   (assembler)   │  │  │
│  │  └──────────┘  └──────────┘  └─────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                       LLM接口层                             │
│  ┌──────────────┐  ┌────────────────┐  ┌──────────────┐  │
│  │ Gemini客户端  │  │   提示词模板    │  │  响应解析器  │  │
│  │   (client)   │  │  (templates)   │  │  (parser)   │  │
│  └──────────────┘  └────────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      知识库层                               │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐  │
│  │  标准类型库  │  │  元模型定义  │  │    设计模式库    │  │
│  │ (datatypes) │  │ (metamodel) │  │   (patterns)    │  │
│  └─────────────┘  └─────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 数据流设计

```
用户需求 
    ↓
[Round 1: 架构设计]
    ├── 需求分析（LLM）
    ├── 架构规划（LLM）
    └── 类型选择（从标准库）
    ↓
用户确认/修改
    ↓
[Round 2: 详细生成]
    ├── 组件生成（LLM+模板）
    ├── 接口生成（LLM+模板）
    └── 类型引用（标准库）
    ↓
ARXML输出
```

## 3. 模块设计

### 3.1 项目目录结构

```
project_root/
├── config.yaml                          # 全局配置文件
├── src/
│   └── llm_generation/
│       ├── __init__.py
│       ├── config.py                    # 配置解析器
│       ├── main.py                      # 主程序入口
│       │
│       ├── core/                        # 核心业务逻辑
│       │   ├── __init__.py
│       │   ├── round1_designer.py       # Round 1架构设计器
│       │   ├── round2_generator.py      # Round 2详细生成器
│       │   ├── user_interaction.py      # 用户交互管理
│       │   └── result_assembler.py      # 结果组装器
│       │
│       ├── llm/                         # LLM相关模块
│       │   ├── __init__.py
│       │   ├── gemini_client.py         # Gemini API客户端
│       │   ├── prompt_templates.py      # 提示词模板管理
│       │   └── response_parser.py       # 响应解析器
│       │
│       ├── knowledge/                   # 知识库模块
│       │   ├── __init__.py
│       │   ├── standard_types.py        # 标准类型管理器
│       │   ├── metamodel_loader.py      # 元模型加载器
│       │   └── pattern_library.py       # 设计模式库
│       │
│       ├── utils/                       # 工具模块
│       │   ├── __init__.py
│       │   ├── exceptions.py            # 自定义异常
│       │   ├── serializers.py           # 数据序列化
│       │   └── arxml_builder.py         # ARXML构建器
│       │
│       ├── data/                        # 数据目录
│       │   ├── standard_types/          # 标准类型库
│       │   │   ├── base_types.arxml     # 基础数据类型
│       │   │   ├── automotive_types.arxml # 汽车通用类型
│       │   │   └── domain/              # 领域特定类型
│       │   ├── metamodel/               # 元模型定义
│       │   │   └── metamodel.json       # AUTOSAR元模型
│       │   └── patterns/                # 设计模式
│       │       └── patterns.json        # 常用设计模式
│       │
│       └── output/                      # 输出目录
│           ├── round1/                  # Round 1输出
│           ├── round2/                  # Round 2输出
│           └── final/                   # 最终ARXML
```

### 3.2 核心模块详细设计

#### 3.2.1 配置管理模块 (config.py)

```python
class Config:
    """全局配置管理器"""
    
    功能:
    - 解析根目录的config.yaml
    - 提供配置访问接口
    - 支持环境变量覆盖
    
    配置结构:
    - llm:           # LLM相关配置
        - api_key
        - model_name
        - temperature
    - knowledge:     # 知识库配置
        - standard_types_path
        - metamodel_path
        - patterns_path
    - generation:    # 生成配置
        - round1_elements  # Round 1包含的元素
        - max_components   # 最大组件数
        - timeout
    - output:        # 输出配置
        - format
        - encoding
```

#### 3.2.2 Round 1 架构设计器 (round1_designer.py)

```python
class Round1Designer:
    """架构设计器 - 专注于高层设计决策"""
    
    核心职责:
    - 分析用户需求
    - 生成架构规划（组件、接口、连接）
    - 从标准库选择合适的数据类型
    - 生成可视化的架构描述
    
    关键方法:
    - analyze_requirements()     # 需求分析
    - design_architecture()      # 架构设计
    - suggest_standard_types()   # 推荐标准类型
    - generate_topology()        # 生成拓扑结构
    
    输出格式:
    {
        "system_analysis": {},
        "component_plan": [],
        "interface_plan": [],
        "type_references": [],    # 引用标准类型
        "connection_topology": {}
    }
```

#### 3.2.3 Round 2 详细生成器 (round2_generator.py)

```python
class Round2Generator:
    """详细生成器 - 基于架构生成完整ARXML"""
    
    核心职责:
    - 基于确认的架构生成详细ARXML
    - 填充组件内部行为
    - 解析标准类型引用
    - 生成完整的端口连接
    
    关键方法:
    - generate_components()      # 生成组件定义
    - generate_interfaces()      # 生成接口定义
    - resolve_type_references()  # 解析类型引用
    - generate_connectors()      # 生成连接器
    
    特色功能:
    - 支持多组件批量生成
    - 自动处理类型依赖
    - 智能命名和引用管理
```

#### 3.2.4 标准类型管理器 (standard_types.py)

```python
class StandardTypeManager:
    """标准类型库管理器 - 知识积累与复用"""
    
    核心职责:
    - 加载和管理标准ARXML类型定义
    - 提供类型查询和推荐
    - 支持类型扩展和自定义
    
    类型分类:
    1. 基础类型（uint8, float32等）
    2. 汽车通用类型（电压、电流、温度等）
    3. 领域特定类型（可扩展）
    
    关键方法:
    - load_standard_types()      # 加载标准类型
    - find_type_by_name()        # 按名称查找
    - recommend_types()          # 智能推荐
    - register_custom_type()     # 注册自定义类型
    
    设计模式:
    - 单例模式确保全局一致
    - 缓存机制提高性能
    - 支持懒加载
```

#### 3.2.5 元模型加载器 (metamodel_loader.py)

```python
class MetamodelLoader:
    """元模型加载器 - 提供AUTOSAR结构定义"""
    
    核心职责:
    - 加载AUTOSAR元模型定义
    - 过滤Round 1/2需要的元素
    - 生成JSON Schema
    
    关键方法:
    - load_metamodel()           # 加载完整元模型
    - filter_round1_elements()   # 过滤Round 1元素
    - generate_schema()          # 生成JSON Schema
    - validate_element()         # 验证元素定义
```

#### 3.2.6 用户交互管理器 (user_interaction.py)

```python
class UserInteractionManager:
    """用户交互管理 - 确认和修改流程"""
    
    核心职责:
    - 展示Round 1设计结果
    - 解析用户反馈
    - 执行设计修改
    - 管理确认流程
    
    交互模式:
    1. 结构化展示（表格、列表）
    2. 自然语言反馈解析
    3. 增量式修改
    4. 版本对比
```

### 3.3 数据模型设计

#### 3.3.1 架构设计数据模型

```python
ArchitectureDesign:
    system_analysis:
        functional_decomposition: str
        data_flow_analysis: str
        timing_requirements: str
        scalability_considerations: str
    
    component_plan: List[ComponentPlan]
        - component_id: str
        - name: str
        - type: ComponentType
        - purpose: str
        - complexity: ComplexityLevel
        - port_estimates: PortEstimates
    
    interface_plan: List[InterfacePlan]
        - interface_id: str
        - name: str
        - type: InterfaceType
        - communication_pattern: str
        - data_elements: List[DataElementRef]
        - connected_components: List[str]
    
    type_references: List[TypeReference]
        - local_name: str
        - standard_type_path: str
        - category: TypeCategory
    
    connection_topology:
        component_connections: List[Connection]
        data_flow_paths: List[DataPath]
        control_flow_paths: List[ControlPath]
```

#### 3.3.2 标准类型引用模型

```python
StandardTypeReference:
    category: Enum[BASE, AUTOMOTIVE, DOMAIN_SPECIFIC]
    package_path: str  # /AUTOSAR/DataTypes/BaseTypes
    type_name: str     # Std_Float32
    includes_compu_method: bool
    includes_unit: bool
    physical_dimension: Optional[str]
```

### 3.4 关键流程设计

#### 3.4.1 Round 1 流程

```
1. 需求输入
   ↓
2. LLM需求分析
   ├── 功能识别
   ├── 复杂度评估
   └── 模式匹配
   ↓
3. 架构生成
   ├── 组件规划（数量、类型、职责）
   ├── 接口设计（类型、数据流向）
   └── 类型选择（从标准库推荐）
   ↓
4. 用户确认
   ├── 可视化展示
   ├── 修改建议
   └── 迭代优化
```

#### 3.4.2 Round 2 流程

```
1. 架构输入（已确认）
   ↓
2. 详细生成准备
   ├── 加载标准类型定义
   ├── 准备组件模板
   └── 构建生成上下文
   ↓
3. LLM详细生成
   ├── 组件内部行为
   ├── 端口详细定义
   ├── Runnable设计
   └── 事件配置
   ↓
4. 后处理
   ├── 类型引用解析
   ├── 路径补全
   ├── UUID生成
   └── 格式化输出
```

### 3.5 扩展性设计

#### 3.5.1 标准类型库扩展

```
扩展机制:
1. 领域特定类型添加
   - 在data/standard_types/domain/下添加新的arxml
   - 系统自动发现和加载

2. 类型继承和组合
   - 基于已有类型创建新类型
   - 支持类型别名和包装

3. 项目特定类型
   - 项目级别的类型定义
   - 优先级高于标准库
```

#### 3.5.2 LLM提供商扩展

```
抽象接口设计:
- BaseLLMClient
  - generate_with_schema()
  - generate_text()
  
具体实现:
- GeminiClient
- GPTClient (future)
- ClaudeClient (future)
```

## 4. 创新特性

### 4.1 智能类型推荐系统

基于需求分析自动推荐合适的标准类型，减少用户选择负担。

### 4.2 增量式架构优化

支持多轮迭代优化，每次修改都基于上一版本的增量改进。

### 4.3 领域知识积累

生成的优秀设计可以被提取为新的模式，持续丰富知识库。

### 4.4 混合生成策略

- 确定性内容：使用模板和标准库
- 创造性内容：使用LLM生成
- 验证性内容：使用规则引擎

## 5. 部署和使用

### 5.1 环境要求

- Python 3.8+
- Gemini API访问权限
- 4GB+ RAM

### 5.2 配置步骤

1. 在项目根目录创建config.yaml
2. 配置LLM API密钥
3. 确认标准类型库路径
4. 运行主程序

### 5.3 使用流程

```bash
# 启动生成器
python -m src.llm_generation.main

# 输入需求
> 请生成一个电池管理系统的温度监控组件

# Round 1: 查看架构设计
# Round 2: 确认后生成详细ARXML
# 输出: output/final/TemperatureMonitor.arxml
```

## 6. 未来规划

1. **Web界面**：提供图形化的设计和确认界面
2. **协作功能**：支持团队协作和设计评审
3. **CI/CD集成**：与开发流程无缝集成
4. **性能优化**：缓存、并行生成等优化措施
5. **更多LLM支持**：接入GPT-4、Claude等模型