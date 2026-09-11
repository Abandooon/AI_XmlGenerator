# AUTOSAR requirement provenance and source navigation

This English entry identifies the sources used by Section 4.2.1 and Appendix A.1 of the [current manuscript](../current/README.md). The original Chinese design explanation is retained below as historical source context. Its dated statements and earlier publication recommendations are not current manuscript instructions.

The 20 cases are author-curated component-level requirements: six minimal, seven standard and seven full cases. AUTOSAR Classic 4.2.2 defines the modeled elements and relations; an ETAS/RH850 engineering example informed recurring modeling patterns; the authors simplified, recombined and parameterized those patterns. The set is not an official AUTOSAR test suite or a statistical sample of customer projects.

| Inspect | Current package location |
| --- | --- |
| Structured case definitions | [asw_cases_v3.yaml](../../experiments/vllm/runtime/atlas_autosar_requirements_v3/asw_cases_v3.yaml) |
| Prompt renderer | [render_cases.py](../../experiments/vllm/runtime/atlas_autosar_requirements_v3/render_cases.py) |
| Original rendered prompts and run identities | [AUTOSAR archive](../../experiments/autosar/frozen/AUTOSAR_V20_FORMAL_EVIDENCE_FINAL_2026-09-02.zip); members under `AUTOSAR_V20_FORMAL_EVIDENCE_FINAL_2026-09-02/requirements/` |
| Worked example, actual ARXML and checks | [Evidence map](../../docs/REVIEWER_EVIDENCE_MAP.md#autosar-periodic-component-example) |
| Constraint preparation and language roles | [ICM evidence](../../docs/ICM_EVIDENCE.md) |
| Current statistical methods | [Statistical analysis](../../docs/STATISTICAL_ANALYSIS.md) |

The saved `requirements/rendered/prompts/ASW-FULL-01.txt` and that run's retained component-generation prompt are in English. This observation identifies those particular inputs; it does not make the normative source, extraction instructions, all control messages or comments one language. See the ICM guide for the separate preparation workflow. The historical engineering-workspace locator below is not a distributable package link.

---
## Historical Chinese design note

## 1. 文档目的

本文档说明 ATLAS AUTOSAR Classic ASW 需求集的来源、设计原则、规范依据、工程依据、工具依据、实验裁剪方式和可审计证据，用于：

- 回应“20 条需求从何而来、是否符合 AUTOSAR 与实际工程”的审稿意见；
- 区分规范性来源、工具实现参考、工程观察和作者实验设计；
- 为论文中的需求构造方法、数据集说明和局限性提供可复用文字；
- 防止将作者构建的组件片段基准误称为 AUTOSAR 官方测试集或完整工业需求集。

本文档是冻结需求集的伴随说明，不改变 [`asw_cases_v3.yaml`](../../experiments/vllm/runtime/atlas_autosar_requirements_v3/asw_cases_v3.yaml)、已渲染提示词、运行清单或任何实验哈希。

## 2. 结论摘要

这 20 条需求是**作者构建并审查的、面向 AUTOSAR Classic 4.2.2 应用软件组件片段的受控基准**。它们不是 AUTOSAR 官方需求，不是 AUTOSAR 官方一致性测试，也不是从客户需求文档逐条复制得到的工业需求。

其来源关系应准确表述为：

1. 使用 AUTOSAR Classic 4.2.2 Software Component Template、VFB、RTE、Methodology 和 4.2.2 XSD 约束允许出现的模型元素、引用关系、枚举和值域；
2. 从一个 ETAS 工具链下的 AUTOSAR 4.2.2 工程中观察反复出现的 ASW 建模模式，包括 P/R Port、Sender-Receiver Interface、NonqueuedReceiverComSpec、Runnable、TimingEvent 和显式数据访问；
3. 使用 Vector DaVinci Developer 和 ETAS ISOLAR-A 的公开资料解释这些规范元素如何在主流工具中配置和检查；
4. 由作者对工程模式进行去上下文化、规范化、裁剪、组合和难度分层，形成 6 条 minimal、7 条 standard 和 7 条 full 需求；
5. 将每条结构化需求确定性渲染成提示词和验证义务，并在固定 AUTOSAR 4.2.2 XSD 与哈希固定的接口上下文中预检。

因此，可以声称这些需求**符合所选 AUTOSAR 4.2.2 组件建模子集，并具有明确工程模式依据**；不能声称它们是“官方 AUTOSAR benchmark”“完整 AUTOSAR 系统需求”或“具有统计代表性的工业需求样本”。

## 3. 证据层级与来源职责

| 层级 | 来源 | 在本文中的职责 | 不能承担的职责 |
|---|---|---|---|
| L1 规范性来源 | AUTOSAR 4.2.2 Software Component Template、XSD | 定义模型元素、关系、约束、枚举、值域和 XML 结构 | 不能证明 20 条实验需求具有工业代表性 |
| L2 概念与流程来源 | SW-C and System Modeling Guide、VFB、Methodology、RTE | 解释组件、端口、接口、Runnable、Event、RTE 与开发流程的关系 | 不能替代目标版本的 XSD 和模板约束 |
| L3 工具实现来源 | Vector DaVinci Developer、ETAS ISOLAR-A | 说明规范元素如何在工具中配置、显示、分析和生成 | 不是 AUTOSAR 元模型的规范制定者 |
| L4 工程观察来源 | ETAS RH850 AUTOSAR 4.2.2 工程 ARXML | 证明所选模式和部分参数确实出现在工程实践中 | 不能被公开宣称为 AUTOSAR 官方示例或生产车型统计样本 |
| L5 作者设计 | `asw_cases_v3.yaml` 与确定性渲染器 | 负责去上下文化、简化、参数变体、难度分层、评分义务和重复实验 | 不能被包装成外部独立 benchmark |

审稿回复中推荐使用“author-curated from recurring engineering patterns and checked against AUTOSAR 4.2.2”，不推荐使用“extracted from official AUTOSAR requirements”。

## 4. 版本选择原则

### 4.1 规范目标版本

需求源明确固定 `autosar_release: "4.2.2"`。因此，实验合规性的主要证据必须来自：

- AUTOSAR Software Component Template, Release 4.2.2, Document ID 062；
- AUTOSAR 4.2.2 XML Schema `AUTOSAR_4-2-2.xsd`；
- 同版本或包含清晰 4.2.2 变更历史的 VFB、RTE 和 Methodology 文档。

截至 2026 年 8 月，R25-11 是 AUTOSAR Classic 最新正式发布版本，但它在本研究中只适合用于说明当前概念与术语延续，不用于替代 4.2.2 的版本合规证明。论文应避免用 R25-11 文档直接证明一个 4.2.2 ARXML 产物满足同版本约束。

### 4.2 XSD 合规与语义合规的区别

- **XSD 合规**：证明 XML 元素、顺序、类型、出现次数和基本值域符合固定 4.2.2 Schema。
- **模板语义合规**：证明端口与接口、Runnable 与 Event、VariableAccess 与端口方向等关系满足 Software Component Template 的语义约束。
- **组件片段合规**：证明当前组件及其外部接口上下文自洽。
- **系统级合规**：还需要 Composition、Connector、System/ECU Mapping、Deployment、RTE/BSW 配置和更多跨工件证据；本需求集不评价这一层。

本文的“符合 AUTOSAR”限定为前三项中的已评价部分，不扩张成系统级保证。

## 5. AUTOSAR 原文与需求构造的对应关系

### 5.1 软件组件、Port 与 PortInterface

AUTOSAR VFB 的规范性标题包括：

> “Components interact only through ports.”

> “Each port typed by exactly one interface.”

Software Component Template 4.2.2 的 `[TPS_SWCT_01025]` 将 PortPrototype 描述为组件连接点，并由 PortInterface 定义实际交换的信息。需求集据此采用：

- `APPLICATION-SW-COMPONENT-TYPE`；
- `P-PORT-PROTOTYPE` 表示提供方；
- `R-PORT-PROTOTYPE` 表示需求方；
- `PROVIDED-INTERFACE-TREF` 与 `REQUIRED-INTERFACE-TREF`；
- `DEST="SENDER-RECEIVER-INTERFACE"`；
- 指向哈希固定接口目录的绝对 AUTOSAR 引用路径。

这部分构造不是任意 XML 拼装，而是直接对应 AUTOSAR 的组件边界和接口契约模型。

### 5.2 Sender-Receiver 通信子集

VFB 将 Sender-Receiver 定义为标准 PortInterface 类型：发送方可以向一个或多个接收方分发信息。Software Component Template 4.2.2 的 Table 4.59 规定 SenderReceiverInterface 与 SenderComSpec/ReceiverComSpec 的组合关系。

主基准只选用 Sender-Receiver，原因是：

- 它是 AUTOSAR ASW 中最常见、最基础的通信模式之一；
- 工程样例中的六个目标接口均使用该模式；
- 它能同时覆盖 Port、Interface、ComSpec、Runnable 数据访问和 RTE 读写关系；
- 限定一个通信范式有利于将实验失败定位为结构生成问题，而不是不同通信范式之间的混杂。

Client-Server、ModeSwitch 和 Parameter Interface 被放入边界挑战而未进入主评分，不代表这些构造不重要，只表示它们不属于本次受控主实验范围。

### 5.3 SwcInternalBehavior、RunnableEntity 与 TimingEvent

Software Component Template 4.2.2 第 7.2.3 节和 `[TPS_SWCT_01519]` 规定：若 AtomicSwComponentType 中的 RunnableEntity 需要周期执行，应定义带目标周期的 TimingEvent，并由该 Event 引用需要启动的 Runnable。

需求集据此构造：

```text
SWC-INTERNAL-BEHAVIOR
├── EVENTS
│   └── TIMING-EVENT
│       ├── START-ON-EVENT-REF -> RUNNABLE-ENTITY
│       └── PERIOD
└── RUNNABLES
    └── RUNNABLE-ENTITY
```

`TimingEvent.period` 的物理单位为秒且必须大于零。需求集使用 0.005、0.01、0.015 和 0.02 秒，分别对应 5、10、15 和 20 ms，全部处于规范允许的正值范围。

minimal 案例不要求内部行为，用于单独测量 Port/Interface/ComSpec 的生成能力；standard 和 full 案例才引入 Runnable、TimingEvent 和 VariableAccess。这是一种实验分解设计，不是对完整工业 SWC 形态的统计描述。

### 5.4 Runnable 的显式读写访问

Software Component Template 4.2.2 对 RunnableEntity 的访问角色给出明确语义：

- `dataReceivePointByArgument` 聚合 `VariableAccess`，表示对 Sender-Receiver RPort 数据元素的显式读取；
- `dataSendPoint` 聚合 `VariableAccess`，表示对 Sender-Receiver PPort 数据元素的显式写入；
- `[constr_2004]` 将 `dataSendPoint` 的目标约束到 PPort/PRPort；
- `[constr_2005]` 将 `dataReceivePointByArgument` 的目标约束到 RPort/PRPort；
- 访问目标通过 `AUTOSAR-VARIABLE-IREF` 同时引用 PortPrototype 和目标 VariableDataPrototype。

这与需求集中的 `reads`、`writes` 结构和最终 ARXML 义务一一对应，也与 Vector DaVinci Developer 中 Runnable 的 **Access Points**、**Read Data** 和显式写入配置一致。

### 5.5 NonqueuedReceiverComSpec、AliveTimeout 与 HandleTimeoutType

Software Component Template 4.2.2 Table 4.61 将 `NonqueuedReceiverComSpec` 定义为非队列接收通信的属性集合，其中：

- `aliveTimeout` 是以秒表示的接收存活超时；值为 0 时不执行超时监控；
- `handleTimeoutType` 控制超时后的处理策略；
- `none` 表示不使用替换值；
- `replace` 表示以通信初始值作为替换值。

工程样例中三个 RPort 均使用 `ALIVE-TIMEOUT=0.3` 和 `HANDLE-TIMEOUT-TYPE=NONE`。需求集保留该工程基线，并增加其他合法正值，用来测试模型能否精确保持不同数值，而不是把 0.3 当成固定模板常量。

### 5.6 InitValue 的规范来源与作者选择

Software Component Template 4.2.2 的 `[constr_1201]` 规定：当 `NonqueuedReceiverComSpec` 由 `RPortPrototype` 拥有时，`initValue` 应存在；`[TPS_SWCT_01220]` 说明在数据尚未接收而应用尝试读取时使用该初始值。

据此，主基准对每个 RPort 的 NonqueuedReceiverComSpec 要求数值 InitValue。需要区分两层来源：

- **要求存在 InitValue**：来自 AUTOSAR 4.2.2 模板语义；
- **统一选择数值 0**：是作者为无 Composition/System 上下文的组件片段确定的控制策略。

ETAS 工程样例中没有出现 `INIT-VALUE`，因此不能声称数值 0 是从该工程原样提取。更准确的说法是：作者以规范约束补足工程模式，并使用固定零值减少不必要变量。

“无 Connector”也不等价于现实系统中永远不连接。需求源的含义是：在本实验提供的验证上下文中没有 Composition/System Connector，因此评分时将这些 RPort 作为无外部发送方上下文的组件片段处理。

## 6. Vector 与 ETAS 资料的正确使用方式

### 6.1 Vector DaVinci Developer

Vector 的 Runnable 文档将编辑界面划分为 **Properties、Triggers、Access Points**，并明确列出：

- `Periodically`：周期触发 Runnable，可配置周期值和单位；
- `Read Data`：从非队列 Receiver Port 读取数据；
- 显式写入：对应 `Rte_Write`；
- `Invoke Operations`：对应 `Rte_Call`，但不在本主基准范围内。

Vector Data Exchange Analysis Editor 又从 Atomic SWC、Runnable 和 Port 层级分析：

- assembly/delegation connector；
- Runnable port access；
- triggers；
- data mapping。

这些资料证明本基准选择的 Runnable/Event/Access 模型能够在主流工具中直接配置和检查。论文中应把 Vector 放在“tool realization”或“industrial tool workflow”位置，不能用它替代 AUTOSAR Software Component Template 的规范定义。

### 6.2 ETAS ISOLAR-A

ETAS 公开资料将 ISOLAR-A 描述为用于设计 AUTOSAR Classic architecture、system 和 application software 的工具，并支持 AUTOSAR 交换格式。它可作为以下事实的公开工具依据：

- SWC/System 设计可由 authoring tool 生成和修改 ARXML；
- 应用软件设计与后续 ECU/BSW 配置属于不同但衔接的工具阶段；
- 当前需求集所覆盖的是 ISOLAR-A 风格的应用组件建模子集，而不是完整 ISOLAR-B/BSW 配置。

本研究的工程证据来自 ETAS 工具链项目 ARXML；ETAS 公共网页只用于说明工具职责，不用于声称 ETAS 官方认可本 benchmark。

## 7. 工程文档与工程实践证据

### 7.1 工程上下文

本地工程证据位于：

```text
E:/博士材料/AUTOSAR/ETAS_RH850_AR422_OnSiteSupport_Multicore
```

其中 `ASW_COM.arxml`（历史工程观察文件；作者本机定位不作为公开包链接） 的根元素声明：

```xml
xsi:schemaLocation="http://autosar.org/schema/r4.0 AUTOSAR_4-2-2.xsd"
```

因此它是一个明确指向 AUTOSAR 4.2.2 Schema 的工程 ARXML 片段。该材料应描述为“ETAS-based AUTOSAR 4.2.2 engineering project artifact”或“工程样例”，除非另有项目证明，不应升级为“量产车型需求”或“客户原始需求”。

### 7.2 工程目录中的构造统计

对工程 `ASW` 目录中的 ARXML 进行只读检索，得到：

| 构造 | 出现次数 | 涉及文件数 |
|---|---:|---:|
| `APPLICATION-SW-COMPONENT-TYPE` | 10 | 10 |
| `P-PORT-PROTOTYPE` | 18 | 6 |
| `R-PORT-PROTOTYPE` | 23 | 8 |
| `SENDER-RECEIVER-INTERFACE` | 8 | 2 |
| `SWC-INTERNAL-BEHAVIOR` | 10 | 10 |
| `RUNNABLE-ENTITY` | 27 | 10 |
| `TIMING-EVENT` | 16 | 10 |
| `DATA-SEND-POINTS` | 6 | 5 |
| `DATA-RECEIVE-POINT-BY-ARGUMENTS` | 2 | 2 |
| `NONQUEUED-RECEIVER-COM-SPEC` | 3 | 1 |
| `ALIVE-TIMEOUT` | 3 | 1 |
| `HANDLE-TIMEOUT-TYPE` | 3 | 1 |
| `INIT-VALUE` | 0 | 0 |

这些统计证明所选构造组合并非仅从抽象规范想象出来，而是出现在实际可导入的 AUTOSAR 工程 ARXML 中。它同时解释了为何 InitValue 要被标为规范驱动补充，而不是工程直接观察项。

### 7.3 六个接口的工程映射

| 需求目录 ID | 方向 | 工程接口路径 | 工程与基准的关系 |
|---|---|---|---|
| `MCU01_EmergShutDown` | provided | `/COM_Interface/SR_Interface_MCU01_EmergShutDown` | 接口名与数据元素名直接保留 |
| `MCU02_MaxTor` | provided | `/COM_Interface/SR_Interface_MCU02_MaxTor` | 接口名与数据元素名直接保留 |
| `MCU03_NRF_IdcSamp` | provided | `/COM_Interface/SR_Interface_MCU03_NRF_IdcSamp` | 接口名与数据元素名直接保留 |
| `HCU01_TqCmd` | required | `/COM_Interface/SR_Interface_HCU01_TqCmd` | 接口名保留；工程数据元素 `HCU01_Tq_Cmd` 规范化为 `HCU01_TqCmd` |
| `HCU01_Shift` | required | `/COM_Interface/SR_Interface_HCU01_Shift` | 接口名与数据元素名直接保留 |
| `HCU02_Poweroff` | required | `/COM_Interface/SR_Interface_HCU02_Poweroff` | 接口名与数据元素名直接保留 |

`ASW_COM.arxml` 还直接给出：

- 三个 PPort 和三个 RPort；
- 三个 RPort 的 `ALIVE-TIMEOUT=0.3` 与 `HANDLE-TIMEOUT-TYPE=NONE`；
- 一个 `PERIOD=0.01` 的 TimingEvent；
- 一个读取三个 RPort、写入三个 PPort 的 Runnable；
- 通过 `AUTOSAR-VARIABLE-IREF` 绑定 PortPrototype 与 VariableDataPrototype。

因此，`ASW-FULL-01` 可视为最接近该工程结构模式的去上下文化基线；其余案例是围绕该基线进行的受控分解和组合。

### 7.4 工程材料的保密边界

- 论文可以报告去上下文化后的构造、统计、来源类型和哈希；
- 未经许可不应公开完整 ETAS 工程、客户标识、供应商专有配置或原始项目目录；
- 本地 AUTOSAR 4.2.2 PDF 副本带有版权/保密标记，不应作为论文补充材料重新分发；
- 正式参考文献应链接 AUTOSAR、Vector 和 ETAS 的公开页面；
- 如审稿人要求复核工程来源，可提供去标识化的元素清单、片段哈希或作者声明，而不是直接上传工程包。

## 8. 20 条需求的设计思路

### 8.1 设计目标

需求集不是为了复刻完整 ECU，而是为了测量模型在受控 AUTOSAR 组件子集上的结构生成能力：

- 能否建立正确数量和方向的 Port；
- 能否引用固定 SenderReceiverInterface 和数据元素；
- 能否生成正确的 RPort ComSpec；
- 能否建立 Runnable 与 TimingEvent 的引用；
- 能否把每个 read/write 绑定到正确的端口和数据元素；
- 能否保持数值、枚举、引用、出现次数和 XSD 顺序；
- 难度增加时是否仍能保持组件整体一致性。

### 8.2 受控构造流程

```text
AUTOSAR 4.2.2 允许的组件建模子集
             +
ETAS 工程中重复出现的六接口通信模式
             ↓
去除工程外围上下文并进行命名规范化
             ↓
分解为 Port、ComSpec、Runnable、Event、Access 义务
             ↓
按结构规模与关系数量分为 minimal / standard / full
             ↓
加入有限周期和 alive-timeout 变体
             ↓
结构化 YAML 权威源
             ↓
确定性提示词、运行定义和哈希清单
             ↓
4.2.2 XSD、结构义务与引用完整性预检
```

### 8.3 难度分层

| 层级 | 数量 | 主要目的 | 结构特征 |
|---|---:|---|---|
| minimal | 6 | 隔离 Port、Interface 与 RPort ComSpec | 单 PPort 或单 RPort，不要求 InternalBehavior |
| standard | 7 | 建立完整的单 Runnable 周期读写链 | 2-3 个 Port、1 个 Runnable、1 个 TimingEvent、2-3 个访问 |
| full | 7 | 测量多端口、多 Runnable、多周期和参数变体 | 固定 3P+3R，1-3 个 Runnable/Event，4-6 个访问 |

难度不是按算法复杂度定义，因为本实验不生成或评价应用算法；难度由模型元素数量、交叉引用数量、重复结构数量和数值保持义务决定。

### 8.4 参数选择

| 参数 | 选择 | 来源与作用 |
|---|---|---|
| provided interfaces | 3 个 MCU 接口 | 直接来自工程模式 |
| required interfaces | 3 个 HCU 接口 | 直接来自工程模式，1 个数据元素名做规范化 |
| baseline period | 0.01 s | 工程直接观察的 10 ms 周期 |
| period variants | 0.005/0.015/0.02 s | 作者设计的合法正值，用于多周期和精确数值测试 |
| baseline aliveTimeout | 0.3 s | 工程直接观察 |
| timeout variants | 0.05/0.1/0.2/0.4/0.5 s | 作者设计的合法正值变化 |
| handleTimeoutType | `NONE` | 工程直接观察且为规范合法枚举；避免引入 replacement value 的额外语义 |
| InitValue | 数值 0 | 规范要求其存在；作者固定值以控制变量 |
| repetitions | 3 个固定 seed | 用于稳定性观察，不作为独立组件样本 |

### 8.5 全集结构统计

| 指标 | 总数/分布 |
|---|---:|
| 用例 | 20 |
| PPort | 33 |
| RPort | 32 |
| Runnable | 18 |
| TimingEvent | 18 |
| VariableAccess | 55 |
| 周期 | 5 ms × 3；10 ms × 10；15 ms × 1；20 ms × 4 |
| aliveTimeout | 0.05 × 1；0.1 × 4；0.2 × 3；0.3 × 21；0.4 × 2；0.5 × 1 |
| handleTimeoutType | `NONE` × 32 |

六个接口在案例中的出现次数接近均衡：三个 provided 接口各 11 次，`HCU01_TqCmd` 与 `HCU01_Shift` 各 11 次，`HCU02_Poweroff` 10 次。这种平衡降低了单一信号名称主导结果的风险。

## 9. 20 个案例的覆盖说明

| 案例 | 核心设计 | P/R | Runnable 与周期 | Access | 来源分类 |
|---|---|---:|---|---:|---|
| ASW-MIN-01 | 单 emergency-shutdown PPort | 1/0 | 无 | 0 | 工程接口的最小化分解 |
| ASW-MIN-02 | 单 maximum-torque PPort | 1/0 | 无 | 0 | 工程接口的最小化分解 |
| ASW-MIN-03 | 单 current-sample PPort | 1/0 | 无 | 0 | 工程接口的最小化分解 |
| ASW-MIN-04 | 单 torque-command RPort | 0/1 | 无 | 0 | 工程 RPort/0.3/NONE + 规范 InitValue |
| ASW-MIN-05 | 单 shift RPort | 0/1 | 无 | 0 | 工程 RPort/0.3/NONE + 规范 InitValue |
| ASW-MIN-06 | 单 power-off RPort | 0/1 | 无 | 0 | 工程 RPort/0.3/NONE + 规范 InitValue |
| ASW-STD-01 | torque 输入到 max-torque 输出 | 1/1 | 1 × 10 ms | 2 | 工程周期读写链的缩减 |
| ASW-STD-02 | shift 输入到 shutdown 输出 | 1/1 | 1 × 5 ms | 2 | 工程模式 + 作者周期变体 |
| ASW-STD-03 | power-off 输入到 current 输出 | 1/1 | 1 × 20 ms | 2 | 工程模式 + 作者周期变体 |
| ASW-STD-04 | 一输入两输出 | 2/1 | 1 × 10 ms | 3 | 作者组合设计 |
| ASW-STD-05 | 两输入一输出 | 1/2 | 1 × 15 ms | 3 | 作者组合与周期变体 |
| ASW-STD-06 | 一输入两输出 | 2/1 | 1 × 10 ms | 3 | 作者组合设计 |
| ASW-STD-07 | 显式 0.1 s timeout | 1/1 | 1 × 10 ms | 2 | 规范合法的数值保持挑战 |
| ASW-FULL-01 | 3 输入、3 输出、单 Runnable | 3/3 | 1 × 10 ms | 6 | 最接近工程 `ASW_COM` 基线 |
| ASW-FULL-02 | 快慢两个独立 Runnable | 3/3 | 5/20 ms | 6 | 工程模式的多速率拆分 |
| ASW-FULL-03 | 控制/安全双速率职责 | 3/3 | 10/20 ms | 6 | 作者职责分组设计 |
| ASW-FULL-04 | 一输入驱动全部输出，保留其余 RPort | 3/3 | 1 × 10 ms | 4 | 区分端口存在与访问覆盖 |
| ASW-FULL-05 | 全部输入驱动一个输出，保留其余 PPort | 3/3 | 1 × 10 ms | 4 | 区分端口存在与访问覆盖 |
| ASW-FULL-06 | 三个互不共享访问的周期链 | 3/3 | 5/10/20 ms | 6 | 最大重复结构与引用压力 |
| ASW-FULL-07 | 三个不同 aliveTimeout | 3/3 | 1 × 10 ms | 6 | 数值差异保持压力 |

## 10. 直接来源、规范化和作者设计的边界

| 内容 | 直接工程观察 | AUTOSAR 规范要求/允许 | 作者设计 |
|---|---:|---:|---:|
| 六个 Sender-Receiver 接口路径 | 是 | 是 | 接口名基本保留；1 个数据元素名规范化 |
| PPort/RPort 方向 | 是 | 是 | 案例中重新组合 |
| 3P+3R 基线结构 | 是 | 是 | 分解成不同规模 |
| Runnable + 10 ms TimingEvent | 是 | 是 | 扩展出 5/15/20 ms |
| read RPort / write PPort | 是 | 是 | 分配给 1-3 个 Runnable |
| aliveTimeout=0.3 | 是 | 是 | 扩展出其他正值 |
| handleTimeoutType=NONE | 是 | 是 | 全集固定以控制变量 |
| InitValue 必须存在 | 工程片段未出现 | 是，`constr_1201` | 固定为数值 0 |
| 6/7/7 难度分层 | 否 | 不规定 | 是 |
| 20 条数量与 3 次重复 | 否 | 不规定 | 是 |
| 评分规则和结构义务 | 否 | 以规范结构为依据 | 是 |

这张表是回答“需求从哪来”的核心：**模型语言来自规范，工程模式和部分参数来自工程，案例边界与实验变化来自作者。**

## 11. 范围与排除项

### 11.1 主基准覆盖

- ApplicationSwComponentType；
- PPortPrototype、RPortPrototype；
- SenderReceiverInterface 引用；
- SwcInternalBehavior；
- RunnableEntity；
- TimingEvent；
- dataSendPoint 与 dataReceivePointByArgument；
- NonqueuedReceiverComSpec；
- InitValue、AliveTimeout、HandleTimeoutType。

### 11.2 主基准不覆盖

- CompositionSwComponentType、SwComponentPrototype 与 Connector；
- ECU/System Description、网络、通信集群和 Data Mapping；
- ECU Mapping、Deployment、OS Task Mapping；
- RTE 生成结果与 BSW 配置；
- 完整 ApplicationDataType/ImplementationDataType 目录；
- Client-Server、ModeSwitch 和 Parameter 主评分；
- 应用算法及其功能正确性；
- 运行时行为、时序分析、安全分析或法规合规。

论文中的 ASW 总体树可以用于背景说明，但必须高亮“evaluated subset”，不能让读者误以为 Composition、DataType、Client-Server、Mode 或完整 RTE 链都已被这 20 条需求覆盖。

## 12. 验证与可审计证据

### 12.1 离线预检

固定预检清单记录：

- 20/20 个案例完成结构义务编译和确定性物化；
- 20 个组件 ARXML；
- 按案例提供 65 个接口 ARXML；
- 合计 85/85 个 ARXML 通过固定 AUTOSAR 4.2.2 XSD；
- 225/225 个同上下文引用可解析；
- 70/70 个受控错误注入被 XSD、结构义务或引用完整性门检测；
- 总体预检决策为 `PASS`。

这些结果证明 20 条结构化要求均存在可实现且可验证的 4.2.2 ARXML 参考结构。它们不证明模型运行结果一定通过，也不证明完整系统级 AUTOSAR 合规。

### 12.2 冻结工件与哈希

| 工件 | SHA-256 |
|---|---|
| `asw_cases_v3.yaml` | `3b61eb5926b5646a12f8767524192cd7ed65a39e27a37aa9672277058489e024` |
| `README.md` | `10d658ee362a627ed5fddd1a5a7d19b04f6f8ed909777f5679eb9cc2eeb23456` |
| `rendered/run_manifest.json` | `0af861da7b10dfe80261080b58dba1c3758378d0a2a1bfe55b5084d90bc202b4` |
| `render_cases.py` | `e3045e1131abd9cbaf7ec16b233c924cf1c7f30f684d454d77a407d98b18f6d5` |
| `AUTOSAR_4-2-2.xsd` | `3c89b2f16d1981eb04e12c7fbe035e7cd6fbd79965a47ff6cf6d6b878feb71ad` |
| 工程 `ASW_COM.arxml` | `1eaac065e23179a8f8ec5ed08501ef43ff189048f26a507d6be96dc61ebb70e3` |

由于正式运行依赖这些哈希，来源说明应作为新增伴随文档维护，不应为了增加引用而回改冻结 YAML 或重新渲染正式提示词。

## 13. 推荐的论文方法表述

### 13.1 中文版本

> 本研究构建了 20 条面向 AUTOSAR Classic 4.2.2 应用软件组件片段的受控需求。该需求集由作者基于 AUTOSAR 4.2.2 Software Component Template、VFB、RTE、Methodology 和固定 XML Schema 设计，并参考一个 ETAS 工具链下的 AUTOSAR 4.2.2 工程中反复出现的组件建模模式。工程模式包括 Sender-Receiver P/R Port、NonqueuedReceiverComSpec、周期 Runnable/TimingEvent 及显式数据读写访问。Vector DaVinci Developer 与 ETAS ISOLAR-A 文档仅用于验证这些规范元素在主流工具中的可配置性，不作为元模型的规范来源。作者对工程模式进行了去上下文化、规范化、裁剪、组合和难度分层，形成 6 条 minimal、7 条 standard 和 7 条 full 案例；因此该数据集属于作者构建的组件级基准，而不是 AUTOSAR 官方一致性测试或完整工业系统需求集。

### 13.2 English version

> We constructed 20 controlled requirements for AUTOSAR Classic 4.2.2 application-software-component fragments. The cases were authored with reference to the AUTOSAR 4.2.2 Software Component Template, VFB, RTE, Methodology, and a pinned AUTOSAR 4.2.2 XML Schema. Their engineering patterns were informed by recurring component-modeling structures observed in an ETAS-based AUTOSAR 4.2.2 project, including sender-receiver P/R ports, nonqueued receiver communication specifications, periodically triggered runnable entities, and explicit data accesses. Vector DaVinci Developer and ETAS ISOLAR-A documentation were used only to corroborate tool-level realizability, not as normative definitions. The authors de-contextualized, normalized, decomposed, recombined, and stratified these patterns into 6 minimal, 7 standard, and 7 full cases. Accordingly, the resulting dataset is an author-curated component-fragment benchmark rather than an official AUTOSAR conformance suite or a statistically representative sample of complete industrial requirements.

## 14. 推荐的审稿回复

> Thank you for raising this important point. We agree that the provenance of the 20 requirements should be stated explicitly. These requirements are not taken from an official AUTOSAR benchmark and are not verbatim copies of customer requirements. They are author-curated, simplified component-level modeling cases derived from recurring patterns observed in an ETAS-based AUTOSAR Classic 4.2.2 engineering project. The selected constructs and their semantics were checked against the AUTOSAR 4.2.2 Software Component Template and the pinned AUTOSAR 4.2.2 XML Schema. Vector DaVinci Developer and ETAS ISOLAR-A documentation were used only to corroborate tool-level realizability rather than as normative definitions.
>
> The evaluated subset covers application software component types, sender-receiver P/R ports, nonqueued receiver communication specifications, internal behaviors, runnable entities, timing events, and explicit data accesses. It deliberately excludes composition/system design, connectors, ECU deployment, RTE/BSW configuration, complete data-type modeling, and application-algorithm correctness. The engineering patterns were de-contextualized and recombined into three controlled structural-complexity tiers. We therefore describe the dataset as an author-curated component-fragment benchmark rather than an official or fully representative industrial AUTOSAR benchmark.
>
> For additional auditability, deterministic reference materialization produced 20 component ARXML files and 65 interface ARXML files. All 85 files passed the pinned AUTOSAR 4.2.2 XSD, and all 225 expected cross-references were resolved in the same hash-pinned validation context. We have added a provenance-and-scope table, clarified the distinction between normative, tool-level, engineering, and author-designed sources, and expanded the limitations section accordingly.

## 15. 推荐的论文修改位置

1. **Dataset/Requirements 小节**：加入第 13 节的来源和构造说明。
2. **表格**：加入第 10 节的“直接工程观察/规范/作者设计”矩阵。
3. **Experimental Scope 小节**：明确第 11 节的覆盖与排除项。
4. **Validation 小节**：报告 85/85 XSD 和 225/225 引用预检，但注明它们不是系统级一致性结论。
5. **Limitations 小节**：明确作者构建、单一 Sender-Receiver 子集、结构化提示、工程来源数量有限以及缺少独立外部需求样本。
6. **Supplementary Material**：可发布本文件的去敏版本、结构化需求、渲染器、清单与哈希；不发布带保密标记的 PDF 或完整 ETAS 工程。

## 16. 局限性和应避免的表述

### 16.1 必须披露的局限性

- 案例由系统作者/工具链开发组构建，不能视为独立第三方测试集；
- 精确 ARXML 标签、路径和计数被显式写入提示，实验主要评价受控结构综合，不等同于自由自然语言需求理解；
- 六个接口主要来自一个工程上下文，不能推断为整个汽车行业的接口分布；
- full 表示本需求集内部的最高结构复杂度，不表示完整 AUTOSAR 系统；
- 统一使用 Sender-Receiver 和 `NONE` 减少了通信范式与超时策略的多样性；
- XSD PASS 是必要条件，不是完整 AUTOSAR 语义、系统集成或运行时正确性的充分条件。

### 16.2 推荐与不推荐措辞

| 不推荐 | 推荐 |
|---|---|
| “20 official AUTOSAR requirements” | “20 author-curated AUTOSAR 4.2.2 component-fragment requirements” |
| “requirements extracted from AUTOSAR” | “constructs checked against AUTOSAR 4.2.2 specifications” |
| “real production requirements” | “patterns informed by an ETAS-based AUTOSAR 4.2.2 engineering project” |
| “AUTOSAR-compliant system” | “XSD-valid and structurally conforming component fragments in the evaluated scope” |
| “full AUTOSAR cases” | “full-tier cases within the benchmark” |
| “Vector/ETAS defines the model” | “Vector/ETAS documents corroborate tool-level realization” |

## 17. 正式参考文献建议

论文正文以 4-5 份 AUTOSAR 文档为主，Vector/ETAS 资料作为工具实现参考：

1. AUTOSAR. *Software Component Template*. AUTOSAR Release 4.2.2, Document ID 062, 2015. 规范元素和语义约束的首要来源。  
   <https://www.autosar.org/fileadmin/standards/R4.2.2/CP/AUTOSAR_TPS_SoftwareComponentTemplate.pdf>
2. AUTOSAR. *SW-C and System Modeling Guide*. AUTOSAR Release 4.2.2, Document ID 207, 2015. 组件与系统建模方法。  
   <https://www.autosar.org/fileadmin/standards/R4.2.2/CP/AUTOSAR_TR_SWCModelingGuide.pdf>
3. AUTOSAR. *Virtual Functional Bus*. AUTOSAR Release 4.2.2, Document ID 056. Port、Interface 与通信原理。  
   <https://www.autosar.org/fileadmin/standards/R4.2.2/CP/AUTOSAR_TR_VFB.pdf>
4. AUTOSAR. *Methodology for Classic Platform*. AUTOSAR Release 4.2.2, Document ID 068. ASW 设计、实现和集成流程。  
   <https://www.autosar.org/fileadmin/standards/R4.2.2/CP/AUTOSAR_TR_Methodology.pdf>
5. AUTOSAR. *Specification of RTE Software*. AUTOSAR Release 4.2.2, Document ID 084. Runnable/Event/Port 到 RTE 执行和 API 的机制。  
   <https://www.autosar.org/fileadmin/standards/R4.2.2/CP/AUTOSAR_SWS_RTE.pdf>
6. AUTOSAR. *Classic Platform*. 当前版本、应用层、VFB 和 RTE 的官方概览。  
   <https://www.autosar.org/standards/classic-platform/>
7. Vector Informatik. *Defining Runnable Entities - DaVinci Developer Classic*. Runnable 的 Properties、Triggers 和 Access Points。  
   <https://help.vector.com/davinci-developer-classic/current/en/help/html/defining_runnable_entities.html>
8. Vector Informatik. *Data Exchange Analysis Editor - DaVinci Developer Classic*. Component、Runnable、Port 和 Data Exchange 检查。  
   <https://help.vector.com/davinci-developer-classic/current/en/help/html/data_exchange_analysis_editor.html>
9. ETAS. *RTA-CAR Details & Integration - ISOLAR-A*. AUTOSAR Classic architecture、system 和 application-software 设计工具职责。  
   <https://www.etas.com/ww/en/products-services/vehicle-software-platform/autosar-classic-profile-rta-car/rta-car-details-integration/>

如果出版格式允许，建议对 [3]-[5] 进一步替换为 AUTOSAR 官方文档检索页中明确标记的 4.2.2 版本；较新版本可保留为概念延续的补充引用，但不承担目标版本合规证明。

## 18. Current package locations

The following links replace the historical author's-directory navigation. They do not change the frozen requirement definitions.

1. [Case specification](../../experiments/vllm/runtime/atlas_autosar_requirements_v3/asw_cases_v3.yaml): the 20 structured cases and declared task obligations.
2. [Deterministic renderer](../../experiments/vllm/runtime/atlas_autosar_requirements_v3/render_cases.py): converts case specifications into requirement prompts and run definitions.
3. [Original AUTOSAR archive](../../experiments/autosar/frozen/AUTOSAR_V20_FORMAL_EVIDENCE_FINAL_2026-09-02.zip): under `AUTOSAR_V20_FORMAL_EVIDENCE_FINAL_2026-09-02/`, inspect `requirements/README.md`, `requirements/rendered/run_manifest.json` and `requirements/rendered/prompts/`.
4. The same archive retains `code_snapshot/experiment/ALL_REQUIREMENTS_OFFLINE_PRECHECK_MANIFEST.json`. This is a historical preparation check; use the [current package entry](../../experiments/autosar/README.md) for the documented offline review of the formal experiment.
5. [Paper-to-evidence map](../../docs/REVIEWER_EVIDENCE_MAP.md): exact prompt, schema, ARXML and validation member paths for the current worked example.
6. [Statistical analysis](../../docs/STATISTICAL_ANALYSIS.md) and [ICM evidence](../../docs/ICM_EVIDENCE.md): current explanations and source-status distinctions.

The case specification defines the requirement; rendered artifacts express it deterministically; the schedule assigns executions and seeds. The schedule is not the origin of the requirement.
## 19. V20 正式证据的使用边界（2026-09-02）

本需求来源说明与 V20 正式数据配套使用。V20 不改变上述 20 条需求的来源、语言、裁剪方式或代表性边界；它只是在通用 IR 编译与验证路径修复并重新冻结后，统一执行了完整正式设计。

- 生成分母为 20 个案例 × 3 个固定 seed = 60 个观察；60/60 形成工件束并通过 XSD、artifact profile、任务义务、本地引用与独立复核；20/20 个案例三次均通过。
- 所有 60 个 full-corpus 判定仍为 `INCOMPLETE`，因为任务没有生成 system/deployment 证据。这不属于工件 XSD 或任务义务失败。
- 正常预物化路径共应用 1,734 个需求义务，并在 49 个运行中执行 527 次确定性 IR 归一化/恢复。这些操作发生在模型结构化响应之后、ARXML 物化之前，不是对实验结束后工件的人工修改。
- 受控修复必须分层报告：core fixed-operator 为 85/85，预声明 substitution 为 15/15；两层均达到严格恢复与原始工件精确恢复，但不能合并为一个“方法修复率”。
- 自然生成失败为 0，因此自然失败修复效果不可估计，不能写成 100%。
- AUTOSAR provider 实验使用 strict JSON Schema 约束语义 IR，但没有可观测 token mask；token-level grammar intervention 的证据只来自单独的本地 vLLM 实验。

V20 的关键内容身份为：generation `5da533af826edcabca4c08632ffdc684ef31de31a868046be96f70f851ec9ef6`，repair `15b0cd2f2f65756ca6373e9abb7fcfdf68ca108e67bccb77bf329e89d111412c`，Neo4j 上下文 `2ad8bfd31daae20c624bea39d955543ae0ab2544b61c6f06e481291011ba055b`。旧 V17/V18/V19 开发和诊断结果不得与 V20 拼接或进入论文分母。
