# AUTOSAR 设计与验证 Web 界面设计文档

*Release v1.0 / 2025-07-28*

---

## 1. 系统概述

### 1.1 设计目标

设计一个统一的Web界面，集成对话式设计系统、XML配置编辑器和验证模块，提供完整的AUTOSAR组件设计、配置、验证和管理工作流。

### 1.2 核心功能模块

| 功能模块 | 主要功能 | 技术实现 | 集成方式 |
|----------|----------|----------|----------|
| **策略选择中心** | 多种生成策略切换 | React组件 + API网关 | 统一API路由 |
| **对话式设计界面** | 两轮对话设计流程 | WebSocket + React | 集成LLM API + RAG |
| **XML配置编辑器** | 可视化配置编辑 | JSON Schema Form + Java JAXB | 模型解析API |
| **验证控制台** | 三段式验证管理 | React Dashboard | 集成验证系统 |
| **项目管理中心** | 文件版本管理 | Git集成 + 文件系统 | RESTful API |

---

## 2. 整体架构设计

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                    前端架构 (React SPA)                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│  │ 策略选择    │ │ 对话设计    │ │ 配置编辑    │ │ 验证控制台  │ │
│  │ 中心模块    │ │ 界面模块    │ │ 器模块      │ │ 模块        │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│                    状态管理层 (Redux + Context)                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│  │ 项目状态    │ │ 对话状态    │ │ 配置状态    │ │ 验证状态    │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│                    API网关层 (Express.js)                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│  │ 策略路由    │ │ 对话API     │ │ 配置API     │ │ 验证API     │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│                    后端服务层                                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│  │ LLM生成服务 │ │ vLLM服务    │ │ JAXB解析    │ │ 验证服务    │ │
│  │ (Python)    │ │ (Python)    │ │ 服务(Java)  │ │ (Python)    │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│                    数据存储层                                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│  │ Neo4j KG    │ │ Redis缓存   │ │ MongoDB会话 │ │ 文件系统    │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 技术栈选择

**前端技术栈**:
- **框架**: React 18 + TypeScript
- **UI组件**: Ant Design + React Flow
- **状态管理**: Redux Toolkit + React Context
- **通信**: Axios + Socket.io-client
- **构建工具**: Vite + ESLint + Prettier

**后端技术栈**:
- **API网关**: Express.js + TypeScript
- **LLM服务**: Python FastAPI
- **JAXB服务**: Spring Boot (Java)
- **验证服务**: Python FastAPI
- **实时通信**: Socket.io

**数据存储**:
- **知识图谱**: Neo4j
- **会话缓存**: Redis
- **文档存储**: MongoDB
- **文件存储**: 文件系统 + MinIO (可选)

---

## 3. 用户界面设计

### 3.1 整体布局架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        顶部导航栏                                 │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐      ┌─────┐ ┌─────┐   │
│  │Logo │ │项目 │ │设计 │ │配置 │ │验证 │ ... │帮助 │ │用户 │   │
│  └─────┘ └─────┘ └─────┘ └─────┘ └─────┘      └─────┘ └─────┘   │
├─────────────────────────────────────────────────────────────────┤
│ ┌─────────────────┐ ┌─────────────────────────────────────────┐ │
│ │                 │ │                                         │ │
│ │   左侧导航面板   │ │              主工作区域                  │ │
│ │                 │ │                                         │ │
│ │ • 项目文件树     │ │   ┌─────────────────────────────────┐   │ │
│ │ • 最近对话       │ │   │                                 │   │ │
│ │ • 快捷操作       │ │   │          页面内容区域            │   │ │
│ │ • 收藏配置       │ │   │                                 │   │ │
│ │                 │ │   │                                 │   │ │
│ │                 │ │   └─────────────────────────────────┘   │ │
│ │                 │ │                                         │ │
│ └─────────────────┘ └─────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│                        底部状态栏                                 │
│  状态信息 │ 进度条 │ 错误提示 │ 操作历史 │ 性能监控 │ 版本信息      │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 主要页面设计

#### 3.2.1 策略选择页面

**页面目标**: 提供多种生成策略的选择和配置

**布局设计**:
```
┌─────────────────────────────────────────────────────────────────┐
│                        策略选择中心                               │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐     │
│  │   API + RAG     │ │      vLLM       │ │   vLLM + RAG    │     │
│  │   ┌─────────┐   │ │   ┌─────────┐   │ │   ┌─────────┐   │     │
│  │   │  图标   │   │ │   │  图标   │   │ │   │  图标   │   │     │
│  │   └─────────┘   │ │   └─────────┘   │ │   └─────────┘   │     │
│  │                 │ │                 │ │                 │     │
│  │ • 云端LLM服务   │ │ • 本地部署      │ │ • 混合模式      │     │
│  │ • 实时知识查询  │ │ • 高性能推理    │ │ • 智能路由      │     │
│  │ • 低延迟响应    │ │ • 数据隐私      │ │ • 资源优化      │     │
│  │                 │ │                 │ │                 │     │
│  │ ┌─────────────┐ │ │ ┌─────────────┐ │ │ ┌─────────────┐ │     │
│  │ │    选择     │ │ │ │    选择     │ │ │ │    选择     │ │     │
│  │ └─────────────┘ │ │ └─────────────┘ │ │ └─────────────┘ │     │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘     │
├─────────────────────────────────────────────────────────────────┤
│                        配置参数区域                               │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ 模型配置:  [Gemini 2.5 Pro ▼] 温度: [0.7] Top-P: [0.9]    │ │
│  │ 知识库:   [√] 启用RAG  [√] 动态查询  [√] 约束检查          │ │
│  │ 性能:     最大Token: [60000]  超时: [300s]  并发: [4]      │ │
│  └─────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐                ┌─────────────────────────┐ │
│  │   开始新项目    │                │      加载现有项目        │ │
│  └─────────────────┘                └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

**组件功能**:
- **策略卡片**: 显示策略特点、优势、适用场景
- **配置面板**: 动态显示选中策略的配置选项
- **预设模板**: 提供常用配置的快速选择
- **性能预估**: 显示预估的响应时间和资源消耗

#### 3.2.2 对话式设计界面

**页面目标**: 实现两轮对话设计流程

**布局设计**:
```
┌─────────────────────────────────────────────────────────────────┐
│                      对话式设计工作台                             │
├─────────────────────────────────────────────────────────────────┤
│ ┌─────────────────┐ ┌─────────────────────────────────────────┐ │
│ │   对话历史面板   │ │              主对话区域                  │ │
│ │                 │ │                                         │ │
│ │ ┌─────────────┐ │ │  ┌─────────────────────────────────┐   │ │
│ │ │ Round 1     │ │ │  │                                 │   │ │
│ │ │ 架构设计    │ │ │  │        当前对话内容              │   │ │
│ │ │ ● 已完成    │ │ │  │                                 │   │ │
│ │ └─────────────┘ │ │  │  用户: 请设计一个传感器数据       │   │ │
│ │                 │ │  │        处理组件                  │   │ │
│ │ ┌─────────────┐ │ │  │                                 │   │ │
│ │ │ Round 2     │ │ │  │  系统: 基于您的需求，我建议...    │   │ │
│ │ │ 详细生成    │ │ │  │                                 │   │ │
│ │ │ ○ 进行中    │ │ │  │                                 │   │ │
│ │ └─────────────┘ │ │  └─────────────────────────────────┘   │ │
│ │                 │ │                                         │ │
│ │ • 上传PDF文档   │ │  ┌─────────────────────────────────┐   │ │
│ │ • 需求模板      │ │  │                                 │   │ │
│ │ • 对话记忆      │ │  │          输入区域                │   │ │
│ │ • 导出历史      │ │  │  [输入您的需求或反馈...]        │   │ │
│ │                 │ │  │                                 │   │ │
│ └─────────────────┘ │  │  [发送] [上传文档] [选择模板]   │   │ │
│                     │  └─────────────────────────────────┘   │ │
├─────────────────────┼─────────────────────────────────────────┤
│    文档分析面板      │              结果展示区域                │
│                     │                                         │
│ PDF: sensor_req.pdf │  ┌─────────────────────────────────┐   │ │
│ 状态: 已分析 ✓     │  │                                 │   │ │
│ 置信度: 85%        │  │        架构设计结果              │   │ │
│                    │  │                                 │   │ │
│ 提取信息:          │  │  • 组件: SensorDataProcessor     │   │ │
│ • 功能需求 (3)     │  │  • 接口: DataInterface          │   │ │
│ • 性能要求 (2)     │  │  • 连接: CAN总线                │   │ │
│ • 约束条件 (1)     │  │                                 │   │ │
│                    │  │  [确认设计] [修改] [重新生成]    │   │ │
│                    │  └─────────────────────────────────┘   │ │
└─────────────────────┴─────────────────────────────────────────┘
```

**关键组件**:
- **轮次状态指示器**: 清晰显示当前所处的对话阶段
- **对话气泡**: 区分用户输入和系统响应
- **实时打字效果**: 模拟真实对话体验
- **文档分析面板**: 显示PDF解析结果和置信度
- **结果可视化**: 架构图、组件关系图
- **记忆提示**: 基于历史对话的智能提示

#### 3.2.3 XML配置编辑器

**页面目标**: 基于JAXB注解的可视化XML配置编辑

**布局设计**:
```
┌─────────────────────────────────────────────────────────────────┐
│                       XML配置编辑器                              │
├─────────────────────────────────────────────────────────────────┤
│ ┌─────────────────┐ ┌─────────────────────────────────────────┐ │
│ │   结构导航树     │ │              配置表单区域                │ │
│ │                 │ │                                         │ │
│ │ ▼ APPLICATION-  │ │  ┌─────────────────────────────────┐   │ │
│ │   SW-COMPONENT  │ │  │          组件基础信息            │   │ │
│ │   ├─ SHORT-NAME │ │  │                                 │   │ │
│ │   ├─ ADMIN-DATA │ │  │ 名称: [SensorProcessor]         │   │ │
│ │   ├─▼ PORTS     │ │  │ 版本: [1.0.0]                  │   │ │
│ │   │  ├─ P-PORT  │ │  │ 描述: [传感器数据处理组件]       │   │ │
│ │   │  └─ R-PORT  │ │  │                                 │   │ │
│ │   ├─ INTERNAL-  │ │  │ UUID: [auto-generated] [生成]   │   │ │
│ │   │   BEHAVIORS │ │  └─────────────────────────────────┘   │ │
│ │   └─ ...        │ │                                         │ │
│ │                 │ │  ┌─────────────────────────────────┐   │ │
│ │ [展开全部]      │ │  │           端口配置              │   │ │
│ │ [折叠全部]      │ │  │                                 │   │ │
│ │ [搜索节点]      │ │  │ 提供端口 (P-PORT):              │   │ │
│ │                 │ │  │ ┌─────────────────────────────┐ │   │ │
│ └─────────────────┘ │  │ │ 端口名: [DataOutput]        │ │   │ │
│                     │  │ │ 接口: [SensorDataInterface] │ │   │ │
│                     │  │ │ [添加] [删除] [复制]        │ │   │ │
│                     │  │ └─────────────────────────────┘ │   │ │
│                     │  │                                 │   │ │
│                     │  │ 需求端口 (R-PORT):              │   │ │
│                     │  │ ┌─────────────────────────────┐ │   │ │
│                     │  │ │ 端口名: [ConfigInput]       │ │   │ │
│                     │  │ │ 接口: [ConfigInterface]     │ │   │ │
│                     │  │ │ 超时: [100ms]               │ │   │ │
│                     │  │ └─────────────────────────────┘ │   │ │
│                     │  └─────────────────────────────────┘   │ │
├─────────────────────┼─────────────────────────────────────────┤
│     工具栏区域       │              预览区域                    │
│                     │                                         │
│ [保存] [另存为]     │  ┌─────────────────────────────────┐   │ │
│ [验证] [格式化]     │  │                                 │   │ │
│ [撤销] [重做]       │  │           XML预览               │   │ │
│ [导入] [导出]       │  │                                 │   │ │
│                     │  │ <APPLICATION-SW-COMPONENT-TYPE> │   │ │
│ 模式: [表单 ▼]     │  │   <SHORT-NAME>SensorProcessor   │   │ │
│ 视图: [分割 ▼]     │  │   </SHORT-NAME>                 │   │ │
│                     │  │   <PORTS>                       │   │ │
│                     │  │     <P-PORT-PROTOTYPE>          │   │ │
│                     │  │       ...                       │   │ │
│                     │  │                                 │   │ │
│                     │  └─────────────────────────────────┘   │ │
└─────────────────────┴─────────────────────────────────────────┘
```

**核心功能**:
- **智能表单生成**: 基于JAXB注解自动生成表单字段
- **实时验证**: 输入时即时验证字段约束
- **模板应用**: 基于常用模式的配置模板
- **版本对比**: 显示配置变更的差异
- **批量操作**: 支持多个相似元素的批量编辑

#### 3.2.4 验证控制台

**页面目标**: 集成三段式验证系统的控制界面

**布局设计**:
```
┌─────────────────────────────────────────────────────────────────┐
│                        验证控制台                                 │
├─────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │                        执行控制面板                          │ │
│ │                                                             │ │
│ │ 验证模式: [完整模式 ▼]  文件: [sensor_component.arxml ▼]    │ │
│ │                                                             │ │
│ │ [开始验证] [停止] [重置]    进度: ████████░░ 80%             │ │
│ └─────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐     │
│ │   结构验证      │ │   语义验证      │ │   约束验证      │     │
│ │     (XSD)       │ │    (SHACL)      │ │     (SMT)       │     │
│ │                 │ │                 │ │                 │     │
│ │ 状态: ✓ 通过    │ │ 状态: ⚠ 警告   │ │ 状态: ⏸ 等待   │     │
│ │ 时间: 2.3s      │ │ 时间: 15.7s     │ │ 时间: --        │     │
│ │ 错误: 0         │ │ 错误: 0         │ │ 错误: --        │     │
│ │ 警告: 0         │ │ 警告: 3         │ │ 警告: --        │     │
│ │                 │ │                 │ │                 │     │
│ │ Schema:         │ │ RDF三元组:      │ │ 约束条件:       │     │
│ │ autosar_432.xsd │ │ 1,247个         │ │ 待分析...       │     │
│ │                 │ │ Shape: 23个     │ │                 │     │
│ │ [查看详情]      │ │ [查看详情]      │ │ [查看详情]      │     │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘     │
├─────────────────────────────────────────────────────────────────┤
│                          详情面板                                │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │                        语义验证详情                          │ │
│ │                                                             │ │
│ │ 警告 #1: [行125] 端口命名不符合约定                        │ │
│ │ ├─ 详情: Port "dataOut" 应使用PascalCase命名              │ │
│ │ ├─ 建议: 重命名为 "DataOut"                               │ │
│ │ └─ 影响: 轻微，不影响功能                                 │ │
│ │                                                             │ │
│ │ 警告 #2: [行203] 缺少可选的描述属性                        │ │
│ │ ├─ 详情: P-PORT-PROTOTYPE 缺少 DESC 元素                  │ │
│ │ ├─ 建议: 添加端口功能描述                                 │ │
│ │ └─ 影响: 文档完整性                                       │ │
│ │                                                             │ │
│ │ 警告 #3: [行445] 接口引用路径过深                          │ │
│ │ ├─ 详情: 接口引用路径长度超过推荐深度                      │ │
│ │ ├─ 建议: 简化包结构或使用相对路径                          │ │
│ │ └─ 影响: 可维护性                                         │ │
│ │                                                             │ │
│ │ [导出报告] [修复建议] [忽略警告] [应用修复]                │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

**关键功能**:
- **阶段状态可视化**: 清晰显示验证进度和结果
- **实时进度监控**: 显示当前验证阶段的进度
- **分类错误显示**: 按严重程度分类显示问题
- **智能修复建议**: 基于错误类型提供具体修复方案
- **批量操作**: 支持批量应用修复建议

### 3.3 响应式设计

#### 3.3.1 断点设计

| 设备类型 | 屏幕宽度 | 布局调整 | 主要变化 |
|----------|----------|----------|----------|
| **移动设备** | < 768px | 单列布局 | 隐藏侧边栏，底部导航 |
| **平板** | 768px - 1024px | 两列布局 | 可折叠侧边栏 |
| **桌面** | 1024px - 1440px | 三列布局 | 完整功能显示 |
| **大屏** | > 1440px | 扩展布局 | 更多并排面板 |

#### 3.3.2 自适应策略

- **导航适配**: 大屏水平导航，小屏汉堡菜单
- **表单适配**: 复杂表单分步骤，移动端优化输入体验
- **图表适配**: 响应式图表尺寸，移动端简化显示
- **操作适配**: 触摸友好的按钮尺寸和间距

---

## 4. 功能模块详细设计

### 4.1 策略选择中心

#### 4.1.1 策略管理架构

```typescript
interface GenerationStrategy {
  id: string;
  name: string;
  description: string;
  type: 'api_rag' | 'vllm' | 'vllm_rag';
  config: StrategyConfig;
  capabilities: string[];
  requirements: SystemRequirement[];
  performance: PerformanceMetrics;
}

interface StrategyConfig {
  model: ModelConfig;
  knowledge: KnowledgeConfig;
  performance: PerformanceConfig;
  advanced: AdvancedConfig;
}
```

#### 4.1.2 动态配置界面

**配置表单生成**:
- 基于策略类型动态生成配置字段
- 实时验证配置参数的有效性
- 提供配置预设和自定义保存
- 显示配置对性能的预期影响

**策略对比**:
- 并排显示多个策略的特性对比
- 性能基准测试结果展示
- 成本效益分析 (时间、资源、质量)
- 适用场景推荐引擎

#### 4.1.3 集成接口设计

**统一API网关**:
```typescript
interface StrategyRouter {
  route(strategy: GenerationStrategy, request: DesignRequest): Promise<DesignResponse>;
  validateStrategy(strategy: GenerationStrategy): ValidationResult;
  getAvailableStrategies(): GenerationStrategy[];
  switchStrategy(fromId: string, toId: string): Promise<void>;
}
```

### 4.2 XML配置编辑器

#### 4.2.1 JAXB模型解析

**Java后端服务**:
```java
@RestController
@RequestMapping("/api/v1/jaxb")
public class JAXBModelController {
    
    @PostMapping("/parse")
    public ModelSchema parseJAXBModel(@RequestBody ParseRequest request) {
        // 解析JAXB注解，生成JSON Schema
    }
    
    @PostMapping("/validate")
    public ValidationResult validateXML(@RequestBody ValidationRequest request) {
        // 基于JAXB约束验证XML
    }
    
    @PostMapping("/generate")
    public String generateXML(@RequestBody GenerationRequest request) {
        // 基于表单数据生成XML
    }
}
```

**模型结构**:
```typescript
interface JAXBModelSchema {
  rootElement: ElementSchema;
  namespaces: NamespaceDefinition[];
  types: TypeDefinition[];
  constraints: ConstraintDefinition[];
}

interface ElementSchema {
  name: string;
  type: string;
  required: boolean;
  attributes: AttributeSchema[];
  children: ElementSchema[];
  annotations: AnnotationInfo[];
}
```

#### 4.2.2 表单组件映射

**自动表单生成**:
- **基础类型**: String → Input, Number → InputNumber
- **枚举类型**: Enum → Select, Boolean → Switch
- **复合类型**: Object → Fieldset, Array → FormList
- **引用类型**: Reference → AutoComplete with search

**高级组件**:
- **UUID字段**: 自动生成按钮 + 格式验证
- **路径引用**: 智能提示可用路径
- **时间配置**: 专用时间选择器
- **约束表达式**: 代码编辑器 + 语法高亮

#### 4.2.3 实时预览与验证

**双向同步**:
```typescript
interface XMLEditorState {
  formData: FormData;
  xmlContent: string;
  validationErrors: ValidationError[];
  isDirty: boolean;
}

class XMLEditor {
  syncFormToXML(formData: FormData): string;
  syncXMLToForm(xmlContent: string): FormData;
  validateRealtime(data: FormData): ValidationError[];
}
```

### 4.3 验证系统集成

#### 4.3.1 验证流程控制

**状态机设计**:
```typescript
enum ValidationState {
  IDLE = 'idle',
  PREPARING = 'preparing',
  STRUCTURAL = 'structural',
  SEMANTIC = 'semantic',
  CONSTRAINT = 'constraint',
  COMPLETED = 'completed',
  FAILED = 'failed'
}

interface ValidationController {
  startValidation(files: string[], mode: ValidationMode): Promise<void>;
  pauseValidation(): void;
  resumeValidation(): void;
  stopValidation(): void;
  getProgress(): ValidationProgress;
}
```

#### 4.3.2 实时结果展示

**WebSocket通信**:
```typescript
interface ValidationEvent {
  type: 'progress' | 'stage_complete' | 'error' | 'warning';
  stage: ValidationStage;
  data: ValidationEventData;
  timestamp: number;
}

class ValidationSocket {
  onProgress(callback: (progress: ValidationProgress) => void): void;
  onStageComplete(callback: (stage: ValidationStage, result: StageResult) => void): void;
  onError(callback: (error: ValidationError) => void): void;
}
```

#### 4.3.3 交互式修复

**智能修复建议**:
- 基于错误类型提供具体修复方案
- 支持一键应用简单修复
- 提供修复预览和撤销功能
- 批量处理相似错误

**修复工作流**:
1. 错误检测 → 分类 → 优先级排序
2. 生成修复建议 → 用户确认 → 应用修复
3. 增量验证 → 确认修复效果
4. 记录修复历史 → 学习优化

---

## 5. 状态管理设计

### 5.1 全局状态架构

```typescript
interface GlobalState {
  app: AppState;
  project: ProjectState;
  conversation: ConversationState;
  configuration: ConfigurationState;
  validation: ValidationState;
  ui: UIState;
}

// Redux Store 设计
const store = configureStore({
  reducer: {
    app: appReducer,
    project: projectReducer,
    conversation: conversationReducer,
    configuration: configurationReducer,
    validation: validationReducer,
    ui: uiReducer,
  },
  middleware: [
    thunk,
    sagaMiddleware,
    socketMiddleware,
  ],
});
```

### 5.2 模块状态设计

#### 5.2.1 项目状态

```typescript
interface ProjectState {
  currentProject: Project | null;
  recentProjects: Project[];
  fileTree: FileTreeNode[];
  activeFiles: ActiveFile[];
  unsavedChanges: string[];
}

interface Project {
  id: string;
  name: string;
  path: string;
  strategy: GenerationStrategy;
  lastModified: Date;
  metadata: ProjectMetadata;
}
```

#### 5.2.2 对话状态

```typescript
interface ConversationState {
  activeSession: ConversationSession | null;
  sessions: ConversationSession[];
  currentRound: number;
  memoryContext: MemoryContext;
  uploadedDocuments: DocumentAnalysis[];
}

interface ConversationSession {
  id: string;
  projectId: string;
  rounds: ConversationRound[];
  state: SessionState;
  createdAt: Date;
  lastActivity: Date;
}
```

#### 5.2.3 配置状态

```typescript
interface ConfigurationState {
  currentConfig: XMLConfiguration | null;
  modelSchema: JAXBModelSchema | null;
  validationErrors: ValidationError[];
  editorMode: 'form' | 'xml' | 'split';
  isDirty: boolean;
  history: ConfigurationHistory[];
}
```

---

## 6. API接口设计

### 6.1 RESTful API规范

#### 6.1.1 项目管理API

```typescript
// 项目CRUD操作
POST   /api/v1/projects                  // 创建项目
GET    /api/v1/projects                  // 获取项目列表
GET    /api/v1/projects/:id              // 获取项目详情
PUT    /api/v1/projects/:id              // 更新项目
DELETE /api/v1/projects/:id              // 删除项目

// 文件管理
GET    /api/v1/projects/:id/files        // 获取文件树
POST   /api/v1/projects/:id/files        // 上传文件
GET    /api/v1/projects/:id/files/:path  // 获取文件内容
PUT    /api/v1/projects/:id/files/:path  // 更新文件内容
DELETE /api/v1/projects/:id/files/:path  // 删除文件
```

#### 6.1.2 对话管理API

```typescript
// 对话会话管理
POST   /api/v1/conversations             // 启动新对话
GET    /api/v1/conversations/:id         // 获取对话详情
POST   /api/v1/conversations/:id/rounds  // 添加对话轮次
PUT    /api/v1/conversations/:id/memory  // 更新记忆状态

// 文档分析
POST   /api/v1/documents/analyze         // 分析上传文档
GET    /api/v1/documents/analysis/:id    // 获取分析结果

// 生成服务
POST   /api/v1/generate/round1           // Round 1架构设计
POST   /api/v1/generate/round2           // Round 2详细生成
POST   /api/v1/generate/feedback         // 处理用户反馈
```

#### 6.1.3 配置管理API

```typescript
// JAXB模型解析
POST   /api/v1/jaxb/parse               // 解析JAXB模型
POST   /api/v1/jaxb/validate            // 验证XML配置
POST   /api/v1/jaxb/generate            // 生成XML文档

// 配置CRUD
GET    /api/v1/configurations/:id       // 获取配置
PUT    /api/v1/configurations/:id       // 更新配置
POST   /api/v1/configurations/:id/save  // 保存配置
GET    /api/v1/configurations/:id/history // 获取历史版本
```

#### 6.1.4 验证管理API

```typescript
// 验证执行
POST   /api/v1/validation/start         // 开始验证
POST   /api/v1/validation/stop          // 停止验证
GET    /api/v1/validation/status        // 获取验证状态
GET    /api/v1/validation/results       // 获取验证结果

// 修复管理
POST   /api/v1/validation/fix           // 应用修复建议
GET    /api/v1/validation/suggestions   // 获取修复建议
POST   /api/v1/validation/batch-fix     // 批量修复
```

### 6.2 WebSocket事件设计

#### 6.2.1 实时通信事件

```typescript
// 对话实时事件
interface ConversationEvents {
  'conversation:start': ConversationStartData;
  'conversation:message': ConversationMessage;
  'conversation:typing': TypingIndicator;
  'conversation:complete': ConversationResult;
  'conversation:error': ConversationError;
}

// 验证实时事件
interface ValidationEvents {
  'validation:start': ValidationStartData;
  'validation:progress': ValidationProgress;
  'validation:stage_complete': StageCompleteData;
  'validation:complete': ValidationResult;
  'validation:error': ValidationError;
}

// 文件同步事件
interface FileEvents {
  'file:changed': FileChangeData;
  'file:saved': FileSaveData;
  'file:conflict': FileConflictData;
  'file:sync': FileSyncData;
}
```

---

## 7. 用户体验设计

### 7.1 交互设计原则

#### 7.1.1 一致性原则
- **视觉一致性**: 统一的颜色、字体、图标系统
- **操作一致性**: 相似功能使用相同的交互模式
- **信息一致性**: 统一的信息层次和表达方式

#### 7.1.2 反馈原则
- **即时反馈**: 用户操作立即给出视觉响应
- **进度反馈**: 长时间操作显示进度指示
- **结果反馈**: 操作完成后明确的成功/失败提示

#### 7.1.3 容错原则
- **操作确认**: 危险操作需要用户确认
- **撤销机制**: 支持操作撤销和恢复
- **智能保存**: 自动保存和意外恢复

### 7.2 可访问性设计

#### 7.2.1 键盘导航
- 全部功能支持键盘操作
- 清晰的焦点指示
- 逻辑的Tab顺序

#### 7.2.2 屏幕阅读器支持
- 语义化HTML结构
- 适当的ARIA标签
- 替代文本和标题

#### 7.2.3 视觉辅助
- 高对比度模式
- 字体大小调节
- 色盲友好的配色

### 7.3 性能优化

#### 7.3.1 前端优化
- **代码分割**: 按路由和功能模块分割代码
- **懒加载**: 组件和资源的按需加载
- **缓存策略**: 合理的浏览器缓存设置
- **虚拟滚动**: 大列表的性能优化

#### 7.3.2 后端优化
- **接口缓存**: Redis缓存热点数据
- **并发控制**: 限制并发请求数量
- **资源池**: 数据库连接池和线程池
- **异步处理**: 长时间任务的异步执行

---

## 8. 技术实现方案

### 8.1 前端架构

#### 8.1.1 项目结构

```
frontend/
├── public/
│   ├── index.html
│   └── assets/
├── src/
│   ├── components/           # 通用组件
│   │   ├── common/          # 基础组件
│   │   ├── forms/           # 表单组件
│   │   └── charts/          # 图表组件
│   ├── pages/               # 页面组件
│   │   ├── strategy/        # 策略选择
│   │   ├── conversation/    # 对话设计
│   │   ├── configuration/   # 配置编辑
│   │   └── validation/      # 验证控制台
│   ├── hooks/               # 自定义Hooks
│   ├── store/               # 状态管理
│   ├── services/            # API服务
│   ├── utils/               # 工具函数
│   ├── styles/              # 样式文件
│   └── types/               # TypeScript类型定义
├── package.json
└── vite.config.ts
```

#### 8.1.2 核心技术选型

**UI框架**: React 18 + TypeScript
- 函数组件 + Hooks
- 严格模式和并发特性
- Error Boundary错误处理

**UI组件库**: Ant Design 5.x
- 企业级UI设计语言
- 丰富的组件生态
- TypeScript支持

**状态管理**: Redux Toolkit + Context
- Redux用于全局复杂状态
- Context用于局部简单状态
- RTK Query用于数据获取

**路由管理**: React Router 6
- 嵌套路由支持
- 动态路由加载
- 路由级代码分割

### 8.2 后端架构

#### 8.2.1 微服务设计

```
backend/
├── api-gateway/             # API网关 (Node.js)
│   ├── routes/
│   ├── middleware/
│   └── config/
├── llm-service/             # LLM生成服务 (Python)
│   ├── src/llm_generation/
│   ├── requirements.txt
│   └── Dockerfile
├── jaxb-service/            # JAXB解析服务 (Java)
│   ├── src/main/java/
│   ├── pom.xml
│   └── Dockerfile
├── validation-service/      # 验证服务 (Python)
│   ├── src/validation/
│   ├── requirements.txt
│   └── Dockerfile
└── shared/                  # 共享资源
    ├── schemas/
    ├── configs/
    └── docs/
```

#### 8.2.2 技术栈选择

**API网关**: Express.js + TypeScript
- 统一路由和认证
- 请求代理和负载均衡
- 跨域和安全中间件

**LLM服务**: FastAPI + Python
- 异步请求处理
- 自动API文档生成
- Pydantic数据验证

**JAXB服务**: Spring Boot + Java
- 成熟的JAXB生态
- 自动配置和依赖注入
- RESTful API支持

**验证服务**: FastAPI + Python
- 集成现有验证系统
- 异步验证执行
- WebSocket实时通信

### 8.3 数据存储方案

#### 8.3.1 数据存储分层

**关系型数据**: PostgreSQL
- 项目元数据和用户信息
- 事务性数据处理
- 复杂查询支持

**图数据库**: Neo4j
- AUTOSAR知识图谱
- 复杂关系查询
- 路径分析和推理

**缓存层**: Redis
- 会话数据缓存
- 查询结果缓存
- 实时数据存储

**文档存储**: MongoDB
- 对话历史记录
- 配置版本管理
- 非结构化数据

**文件存储**: MinIO/S3
- XML文件存储
- 文档上传管理
- 版本文件备份

---

## 9. 部署与运维

### 9.1 容器化部署

#### 9.1.1 Docker Compose配置

```yaml
version: '3.8'
services:
  # 前端服务
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:8000

  # API网关
  api-gateway:
    build: ./backend/api-gateway
    ports:
      - "8000:8000"
    depends_on:
      - llm-service
      - jaxb-service
      - validation-service

  # LLM生成服务
  llm-service:
    build: ./backend/llm-service
    environment:
      - LLM_API_KEY=${LLM_API_KEY}
      - NEO4J_URI=bolt://neo4j:7687
    depends_on:
      - neo4j
      - redis

  # JAXB解析服务
  jaxb-service:
    build: ./backend/jaxb-service
    environment:
      - SPRING_PROFILES_ACTIVE=docker

  # 验证服务
  validation-service:
    build: ./backend/validation-service
    volumes:
      - ./validation-data:/app/data

  # 数据库服务
  neo4j:
    image: neo4j:5.x
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/password

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  mongodb:
    image: mongo:6
    ports:
      - "27017:27017"
    environment:
      - MONGO_INITDB_ROOT_USERNAME=admin
      - MONGO_INITDB_ROOT_PASSWORD=password
```

### 9.2 监控与日志

#### 9.2.1 应用监控

**性能指标**:
- API响应时间和吞吐量
- 前端页面加载时间
- 数据库查询性能
- 内存和CPU使用率

**业务指标**:
- 用户活跃度和留存率
- 对话成功率和满意度
- 验证通过率和错误分布
- 文档处理成功率

#### 9.2.2 日志管理

**日志分级**:
- ERROR: 系统错误和异常
- WARN: 警告信息和降级处理
- INFO: 关键业务操作
- DEBUG: 详细调试信息

**日志收集**:
- 集中式日志收集 (ELK Stack)
- 结构化日志格式 (JSON)
- 日志轮转和归档
- 敏感信息脱敏

### 9.3 安全设计

#### 9.3.1 认证授权

**用户认证**:
- JWT Token认证
- OAuth2.0集成
- 多因素认证支持

**权限控制**:
- 基于角色的访问控制 (RBAC)
- 细粒度权限设计
- API级别权限验证

#### 9.3.2 数据安全

**传输安全**:
- HTTPS强制加密
- API请求签名验证
- 跨域安全策略

**存储安全**:
- 敏感数据加密存储
- 数据库访问控制
- 备份数据加密

---

## 10. 测试策略

### 10.1 测试分层

#### 10.1.1 前端测试

**单元测试**:
- React组件测试 (React Testing Library)
- Hook逻辑测试
- 工具函数测试
- 覆盖率目标: 80%+

**集成测试**:
- 页面流程测试
- API集成测试
- 状态管理测试

**端到端测试**:
- 用户场景测试 (Playwright)
- 跨浏览器兼容性测试
- 性能测试

#### 10.1.2 后端测试

**单元测试**:
- 服务层逻辑测试
- 数据层操作测试
- 工具函数测试

**集成测试**:
- API接口测试
- 数据库集成测试
- 外部服务集成测试

**性能测试**:
- API性能基准测试
- 并发压力测试
- 资源消耗测试

### 10.2 自动化测试

#### 10.2.1 CI/CD流水线

```yaml
# GitHub Actions 示例
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18
      
      # 前端测试
      - name: Frontend Tests
        run: |
          cd frontend
          npm ci
          npm run test:coverage
          npm run build
      
      # 后端测试
      - name: Backend Tests
        run: |
          cd backend
          docker-compose -f docker-compose.test.yml up --abort-on-container-exit
      
      # 部署
      - name: Deploy
        if: github.ref == 'refs/heads/main'
        run: |
          docker-compose up -d
```

---

## 11. 项目管理

### 11.1 开发里程碑

| 阶段 | 时间 | 主要交付物 | 验收标准 |
|------|------|------------|----------|
| **Phase 1** | 4周 | 基础架构 + 策略选择 | 多策略切换正常工作 |
| **Phase 2** | 6周 | 对话设计界面 | 两轮对话流程完整 |
| **Phase 3** | 4周 | XML配置编辑器 | JAXB模型解析正确 |
| **Phase 4** | 3周 | 验证系统集成 | 三段式验证完整 |
| **Phase 5** | 2周 | 系统集成测试 | 端到端流程通过 |
| **Phase 6** | 1周 | 部署上线 | 生产环境稳定运行 |

### 11.2 团队分工

**前端团队** (3人):
- 1名架构师: 负责整体前端架构设计
- 2名开发工程师: 负责页面组件开发

**后端团队** (4人):
- 1名架构师: 负责微服务架构设计
- 1名Python开发: LLM和验证服务
- 1名Java开发: JAXB解析服务
- 1名DevOps: 部署运维和监控

**UI/UX设计师** (1人):
- 界面设计和用户体验优化

### 11.3 质量保证

**代码质量**:
- 强制代码审查机制
- 统一编码规范和工具
- 自动化质量检查

**项目管理**:
- 敏捷开发流程
- 每日站会和周报告
- 风险识别和应对

---

## 12. 总结

这个Web界面设计文档提供了一个完整的AUTOSAR设计与验证系统的用户界面解决方案，主要特点包括：

### 12.1 技术亮点

1. **统一的多策略支持**: 无缝切换API+RAG、vLLM、vLLM+RAG三种生成策略
2. **智能的配置编辑**: 基于JAXB注解的自动表单生成和实时验证
3. **集成的验证流程**: 三段式验证系统的可视化控制和反馈
4. **现代化的架构**: 微服务后端 + React前端的可扩展架构

### 12.2 用户价值

1. **降低使用门槛**: 可视化界面替代复杂的命令行操作
2. **提升工作效率**: 集成的工作流减少工具切换成本
3. **保证质量**: 实时验证和智能修复提升输出质量
4. **增强协作**: 项目管理和版本控制支持团队协作

### 12.3 扩展性设计

系统架构支持功能扩展和技术演进：
- 插件化的验证器扩展机制
- 可配置的生成策略框架
- 标准化的API接口设计
- 模块化的前端组件体系

这个设计为AUTOSAR设计工具链提供了现代化的用户界面解决方案，将复杂的技术能力包装为用户友好的操作体验。