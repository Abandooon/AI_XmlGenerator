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

# v3补充
# AUTOSAR ASW LLM生成器设计文档 v3 - 补充内容

## 7. 分批生成架构设计

### 7.1 分批生成理念

为解决大规模组件生成时的LLM上下文限制和生成质量问题，系统引入了**智能分批生成策略**：

- **动态阈值策略**：根据组件数量自动选择单批或多批生成
- **依赖感知分批**：基于组件间依赖关系制定最优分批顺序
- **语义占位符机制**：用自然语言描述引用关系，后期智能解析
- **引用一致性保证**：确保跨批次的组件引用正确性

### 7.2 分批生成架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    分批生成控制层                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ 依赖分析器    │  │ 分批策略器    │  │ 生成协调器    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   组件注册与引用管理层                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ 组件注册表    │  │ 引用解析器    │  │ 语义映射器    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      批次生成执行层                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ 批次1生成器   │  │ 批次2生成器   │  │ 批次N生成器   │  │
│  │ (独立组件)    │  │ (应用组件)    │  │ (组合组件)    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 7.3 分批策略矩阵

| 组件数量 | 生成策略 | 批次划分 | 优势 | 适用场景 |
|---------|---------|----------|------|----------|
| 1-5个 | 单批生成 | 全部组件一次生成 | 引用关系紧密，生成效率高 | 简单系统、原型验证 |
| 6-15个 | 类型分批 | 按组件类型分2-3批 | 平衡质量与效率 | 中等复杂度系统 |
| 16+个 | 依赖分批 | 按依赖层次分批 | 最大化生成质量 | 复杂系统、产品级开发 |

## 8. 语义占位符机制

### 8.1 设计动机

传统的组件引用需要精确的路径信息，但在分批生成时：
- 后生成的组件无法获知先生成组件的具体路径
- LLM难以同时处理抽象设计和具体引用
- 引用错误会导致整个生成失败

语义占位符机制通过**"语义描述 + 后期解析"**的方式解决了这一问题。

### 8.2 语义占位符格式设计

#### 8.2.1 组件引用模式
```
- "引用{功能描述}组件的{端口类型}端口"
  示例: "引用温度传感器组件的数据输出端口"

- "连接到{组件角色}的{数据类型}接口"
  示例: "连接到电机控制器的转速控制接口"

- "订阅{系统功能}管理器的{事件类型}"
  示例: "订阅系统状态管理器的模式切换事件"
```

#### 8.2.2 解析映射规则
```
语义描述 → 实际路径映射:
"引用温度传感器的数据输出端口" 
  → "/TemperatureSensor/Ports/TempDataOut"

"连接到电机控制器的转速控制接口"
  → "/MotorController/Interfaces/SpeedControlInterface"
```

### 8.3 引用解析流程

```
1. 语义模式识别
   ├── 正则表达式匹配
   ├── 关键词提取
   └── 意图分类

2. 组件映射查询
   ├── 注册表查询
   ├── 模糊匹配
   └── 启发式推断

3. 路径生成
   ├── 路径模板应用
   ├── 命名规范化
   └── 引用验证

4. 引用替换
   ├── 原地替换
   ├── 一致性检查
   └── 错误回退
```

## 9. 新增核心模块设计

### 9.1 组件注册表 (ComponentRegistry)

#### 9.1.1 核心功能
- **接口信息管理**：记录已生成组件的端口和接口信息
- **语义映射维护**：建立语义描述到实际路径的映射关系
- **引用查询服务**：为后续批次提供组件引用信息

#### 9.1.2 数据结构设计
```python
ComponentRegistration:
    - component_id: str          # 组件唯一标识
    - name: str                  # 组件名称
    - type: str                  # 组件类型
    - interfaces: List[Interface] # 接口列表
    - generation_batch: int      # 生成批次
    - semantic_mappings: Dict    # 语义映射
```

#### 9.1.3 关键方法
- `register_generated_component()`: 注册新生成的组件
- `resolve_semantic_reference()`: 解析语义引用
- `get_component_summaries()`: 获取组件摘要信息
- `update_semantic_mapping()`: 更新语义映射关系

### 9.2 引用解析器 (ReferenceResolver)

#### 9.2.1 解析策略
```
三层解析策略:
1. 直接匹配：精确的语义模式匹配
2. 模糊匹配：基于关键词相似度的匹配
3. 启发式推断：基于组件类型和功能的智能推断
```

#### 9.2.2 解析模式库
```python
# 内置解析模式
SEMANTIC_PATTERNS = [
    {
        "pattern": r"引用(.+?)的(.+?)端口",
        "type": "port_reference",
        "template": "/{component}/Ports/{port}"
    },
    {
        "pattern": r"连接到(.+?)的(.+?)接口", 
        "type": "interface_reference",
        "template": "/{component}/Interfaces/{interface}"
    }
    # ... 更多模式
]
```

### 9.3 依赖分析器 (DependencyAnalyzer)

#### 9.3.1 依赖分析算法
```
1. 依赖图构建
   ├── 接口依赖分析
   ├── 数据流依赖分析
   └── 控制流依赖分析

2. 拓扑排序
   ├── 无依赖组件识别
   ├── 依赖层次划分
   └── 循环依赖检测

3. 分批策略制定
   ├── 组件类型优先级
   ├── 复杂度平衡
   └── 批次大小优化
```

#### 9.3.2 分批优先级规则
```python
COMPONENT_PRIORITY = {
    "SENSOR-ACTUATOR-SW-COMPONENT-TYPE": 1,  # 最高优先级
    "PARAMETER-SW-COMPONENT-TYPE": 2,
    "APPLICATION-SW-COMPONENT-TYPE": 3,
    "SERVICE-SW-COMPONENT-TYPE": 4,
    "COMPOSITION-SW-COMPONENT-TYPE": 5       # 最低优先级
}
```

## 10. 增强的生成流程

### 10.1 Round 2 增强流程

```
1. 组件数量判断
   ├── <= 5个：单批生成
   ├── 6-15个：类型分批
   └── 16+个：依赖分批

2. 依赖关系分析
   ├── 构建依赖图
   ├── 拓扑排序
   └── 制定分批策略

3. 批次逐一生成
   ├── 第一批：独立组件（传感器、参数）
   ├── 第二批：应用组件（业务逻辑）
   └── 第三批：组合组件（系统集成）

4. 语义引用解析
   ├── 模式匹配
   ├── 组件查询
   └── 路径替换

5. 最终组装
   ├── 组件合并
   ├── 引用验证
   └── ARXML生成
```

### 10.2 质量保证机制

#### 10.2.1 分层验证
```
批次级验证:
- 组件结构完整性
- 语义占位符格式
- 批次内一致性

系统级验证:
- 跨批次引用正确性
- 全局命名唯一性
- 接口兼容性

语义级验证:
- 引用解析成功率
- 路径可达性
- 业务逻辑一致性
```

#### 10.2.2 错误恢复策略
```
引用解析失败:
1. 记录失败的语义描述
2. 提供最相似的替代引用
3. 标记需要人工确认的引用

批次生成失败:
1. 保留已成功的批次
2. 重试失败的批次
3. 提供降级生成选项

系统级错误:
1. 回退到单批生成模式
2. 提供部分结果
3. 生成详细的错误报告
```

## 11. 配置增强

### 11.1 新增配置项

```yaml
# 分批生成配置
generation:
  single_batch_threshold: 5              # 单批生成阈值
  max_batch_size: 8                      # 最大批次大小
  enable_semantic_placeholders: true     # 启用语义占位符
  reference_resolution_timeout: 300      # 引用解析超时

# 依赖分析配置
dependency_analysis:
  enable_dependency_detection: true      # 启用依赖检测
  max_dependency_depth: 5               # 最大依赖深度
  circular_dependency_handling: "warning" # 循环依赖处理方式

# 语义解析配置
semantic_resolution:
  fuzzy_match_threshold: 0.6            # 模糊匹配阈值
  enable_heuristic_resolution: true     # 启用启发式解析
  resolution_cache_size: 1000           # 解析缓存大小
```

## 12. 性能优化与扩展性

### 12.1 性能优化策略

#### 12.1.1 并行处理
```
批次内并行:
- 独立组件可以并行生成
- Schema生成并行化
- 类型查询并行化

批次间流水线:
- 当前批次生成时，预处理下一批次
- 引用解析与生成并行
- 结果验证异步化
```

#### 12.1.2 缓存机制
```
多级缓存策略:
1. Schema缓存：缓存动态生成的Schema
2. 类型缓存：缓存标准类型查询结果
3. 引用缓存：缓存语义引用解析结果
4. 组件缓存：缓存已生成组件的摘要信息
```

### 12.2 扩展性设计

#### 12.2.1 插件化架构
```python
# 分批策略插件接口
class BatchingStrategy:
    def analyze_dependencies(self, components) -> DependencyGraph
    def create_batches(self, dependency_graph) -> List[Batch]

# 引用解析插件接口  
class ReferenceResolver:
    def register_pattern(self, pattern: SemanticPattern)
    def resolve_reference(self, semantic_text: str) -> Optional[str]
```

#### 12.2.2 领域扩展机制
```
领域特定扩展:
1. 自定义语义模式
2. 领域特定的分批策略
3. 专用的组件类型优先级
4. 定制化的引用解析规则
```

## 13. 监控与调试

### 13.1 分批生成监控

```python
# 生成统计信息
BatchGenerationStats:
    - total_batches: int
    - successful_batches: int
    - failed_batches: int
    - average_batch_time: float
    - reference_resolution_rate: float
    - semantic_cache_hit_rate: float
```

### 13.2 调试支持

#### 13.2.1 可视化分批策略
```
依赖关系图:
- 显示组件间依赖关系
- 标识分批边界
- 高亮循环依赖

批次执行流程:
- 实时显示当前执行的批次
- 展示每个批次的生成进度
- 标记引用解析状态
```

#### 13.2.2 引用解析调试
```
解析跟踪:
- 记录每个语义引用的解析过程
- 显示模式匹配的中间结果
- 提供解析失败的详细原因

性能分析:
- 各个解析策略的成功率
- 解析时间分布
- 缓存命中率统计
```

## 14. 最佳实践与使用建议

### 14.1 分批生成最佳实践

```
组件设计建议:
1. 优先设计独立性强的组件
2. 明确定义组件间的接口契约
3. 避免过度复杂的依赖关系
4. 使用描述性的组件和端口命名

语义占位符建议:
1. 使用清晰、具体的功能描述
2. 避免歧义的表达方式
3. 保持一致的命名风格
4. 提供足够的上下文信息
```

### 14.2 系统规模建议

| 系统规模 | 推荐策略 | 预期效果 | 注意事项 |
|---------|---------|----------|----------|
| 小型(1-5组件) | 单批生成 | 快速原型验证 | 关注接口设计的完整性 |
| 中型(6-15组件) | 类型分批 | 平衡质量与效率 | 注意组件间依赖关系 |
| 大型(16+组件) | 依赖分批 | 最优生成质量 | 重视架构设计的合理性 |
