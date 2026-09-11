# 附录

本附录按正文的实验顺序组织。附录 A 补充 AUTOSAR 的需求来源、ICM 与验证器、受控修复和工程案例；附录 B 给出 AUTOSAR-vLLM 解码对照的设置与代价；附录 C 补充铁路规则、对照与修复案例；附录 D 说明 PIL 的评分、专家意见及实际决策修订。附录 A.4、C.4 和 D.3 分别以实际 ARXML、XMI 和 JSON 片段展示任务、生成、诊断、修复与复验。主要比较的分析单位、重复汇总方式和重采样设置见 C.2 与 D.2；完整配对数据、统计脚本及敏感性分析保存在复现材料中。

## 附录 A AUTOSAR 工程生成与修复

### A.1 需求设计与生成设置

20 个需求依据 AUTOSAR Classic 4.2.2 的 Software Component Template 和 Specification of RTE 设计<sup style="color:#FF0000">[28]</sup><sup style="color:#FF0000">[29]</sup>。前者规定组件、端口、通信属性、内部行为及引用结构，后者用于解释周期触发与显式数据访问。ETAS 工具链下 RH850 工程中的接口与行为组合提供工程观察依据；作者进行去上下文化、命名规范化、分解重组和参数变化，形成表 A1 的三个层次。

表 A1 AUTOSAR 需求设计及来源

| 内容 | 来源依据 | 设计方式 |
| --- | --- | --- |
| 接口与端口 | 工程中的三个提供接口、三个需求接口及数据元素 | 重组接口组合，规范化命名 |
| 周期与接收超时 | 工程基线分别为 0.01 s、0.3 s | 设置周期和超时参数变体 |
| 初始值 | constr_1201 要求所选非队列接收通信属性具有初始值 | 作者统一取数值 0 |
| 最小层 6 案 | 单端口及接口 | 分别构造提供端口或需求端口 |
| 标准层 7 案 | 端口、周期执行与访问关系 | 组合 2–3 个端口、一个 Runnable 及周期事件 |
| 完整层 7 案 | 多接口与内部行为 | 组合六个端口、1–3 个 Runnable 及周期变化 |

所选初始值的规范依据见 Software Component Template 的 constr_1201，使用含义见 TPS_SWCT_01220<sup style="color:#FF0000">[28]</sup>；数值 0 是任务设计中的具体选择。20 个基础案例共要求 33 个提供端口、32 个需求端口、18 个 Runnable、18 个周期事件和 55 个变量访问。详细案例来源与设计说明随复现材料提供。

生成使用 gpt-5.6-luna、low 推理强度、温度 1.0、严格结构化输出和 128,000 词元最大输出预算，三个固定种子为 104729、130363、155921。任务输入包括英文需求描述、据需求确定的结构化规格及已有接口目录。正式包保留 20 份需求提示和 120 份第二阶段生成提示；它们与规范抽取时使用的提示分别保存。任务分析选定所需结构，再与 ICM 和图谱中的元模型信息共同组装生成约束。适配器绑定固定对象和值，装配结构化输出并序列化为 ARXML。生成评价与受控修复分开执行。

60 次生成形成 60 份组件文件和 195 份接口文件。单个组件文档含 11–115 个 XML 元素，接口文档各含 10 个元素，最大嵌套深度为 14，根 AUTOSAR 计为第 1 层。最大案例 ASW-FULL-06 的一次输出包含七份文档，共 175 个元素。上述元素数按 XML 元素节点计算，属性、文本及重复副本不另计。

### A.2 规范约束抽取、ICM 与验证器

规范约束抽取使用 Software Component Template 第 2–13 章的文本及其元模型信息<sup style="color:#FF0000">[28]</sup>。作者标注章节、相关类和枚举，系统从元模型转换所得的表示中补入相应属性和枚举字面量，按章节与段落形成带上下文的输入片段。LLM 据此提出结构化约束及其目标元素候选，后续整理结合规范原文形成约束记录与元素绑定。规范原文为英文，抽取实现中的控制提示使用中文；抽取与后续语义整理的实现、记录及身份分别提供。表 A2 概括领域准备流程，固定资源的实际复核状态见下文。

表 A2 AUTOSAR 规范约束抽取与整理规格

| 项目 | 内容 |
| --- | --- |
| 材料范围 | 所选规范章节中的带标识条款、规范性叙述及相关示例；保留条款标识和章节出处 |
| 术语上下文 | 片段及上级章节、相关元模型类及属性、枚举及字面量 |
| 结构化输出 | 约束标识、内容、类型、取值、关联条款，以及目标类、属性或枚举候选 |
| 关联与语义复核 | 检查目标元素及其成员归属；分别记录元素绑定、规则解释及待复核问题 |
| 后续使用 | 按已有映射与检查实现接入生成和验证；检索根据关联与相关性选择约束材料，并保留其复核状态 |

正式实验使用固定的 ICM 资源，分别保存规范来源、语义整理与元素绑定。该存量含 1,085 条结构化约束、6,533 条约束关联，以及 11,177 个结构节点和 14,106 条结构关系。结构节点包含多种表示对象。语义状态中，473 条标记为已整理（curated），612 条为暂定（provisional）；综合状态中，472 条标记为 approved，613 条为 needs_review。综合状态由发布程序依据整理、绑定及实现问题标记生成，不等同于独立人工签核。元素绑定另有 1,052 条完整、30 条不适用、2 条部分完成和 1 条未解决。

检索器将复核状态用于排序，但不排除待复核材料，因此检索到的卡片仍需按其状态解释。规则实现另行登记：检查计划接入 554 条规则，包括 400 条 Python 后端规则和 154 条声明式规则；这是配置规模，每次运行的实际检查由适用对象确定。图 6 的 TPS_SWCT_01519 卡片标记为暂定且待复核，元素绑定已完成，其检查计划中的形式化规格则标记为已审查。该例展示规则实现的实际检查，未将其视为整条约束解释或全部 ICM 存量已经完成语义确认。

自定义检查由 LLM 辅助人工编写。作者对照规范确定适用对象、判定条件和诊断位置，选择实现并用满足、违反及边界样例测试。声明式操作处理范围、枚举、基数、存在性和引用等要求；专用检查处理跨对象关系。运行时依据规则标识和本次对象绑定装配检查项，不为每个任务重新生成验证代码。

生成后先用 AUTOSAR XSD 检查实际 ARXML，再解析本地引用并执行适用领域规则。原任务验收器从案例规格读取组件名称、端口集合、接口引用、初始值、超时、Runnable、周期和读写关系，与实际制品逐项比较。制品与生成计划的一致性另行检查。例如，周期事件能够解析并不意味着周期正确；任务要求 10 ms 时，验收器还要核对实际值为 0.01 s。

### A.3 核心故障与替代故障

受控修复使用依据案例和 XSD 确定性构造、且已通过验收的参考制品。每个基础案例安排五个故障位置，对具有适用对象的位置执行固定核心操作，共 85 个；其余 15 个位置在运行前指定可执行的替代操作。修复最多允许两轮，实际各单元均在一轮内完成。

表 A3 核心故障修复结果

| 故障 | 单元数 | 检出数 | 恢复参考内容 |
| --- | ---: | ---: | ---: |
| 初始值为空 | 17 | 17 | 17 |
| 初始值错误 | 17 | 17 | 17 |
| 事件或内部行为路径缺失 | 14 | 14 | 14 |
| 接收通信属性缺失 | 17 | 17 | 17 |
| XSD 元素顺序错误 | 20 | 20 | 20 |
| 合计 | 85 | 85 | 85 |

替代操作的原因是目标结构不存在。例如，只有提供端口的案例没有接收初始值，因而不能清空它；没有 Runnable 和事件的案例也不能注入其路径故障。表 A4 列出实际执行的替代操作，每行对应三个案例。

表 A4 运行前声明的替代操作

| 案例 | 原核心操作 | 替代操作 | 数量与恢复结果 |
| --- | --- | --- | --- |
| MIN-01 至 MIN-03 | 初始值为空 | 清空提供接口引用 | 3/3 |
| MIN-01 至 MIN-03 | 初始值错误 | 将提供接口引用改为不存在的路径 | 3/3 |
| MIN-01 至 MIN-03 | 接收通信属性缺失 | 删除提供端口 | 3/3 |
| MIN-01 至 MIN-03 | 事件或内部行为路径缺失 | 删除组件名称 | 3/3 |
| MIN-04 至 MIN-06 | 事件或内部行为路径缺失 | 删除需求接口引用 | 3/3 |

核心与替代集合分别为 85/85 和 15/15 恢复参考文件集合及字节内容。核心集合使用 109 次模型响应、661,631 个词元；替代集合使用 21 次响应、54,993 个词元。部分插入类修复分阶段生成，因而一次修复轮次可以包含多个响应。

### A.4 贯穿案例 周期组件的构造与事件引用恢复

**任务及领域依据。** ASW-FULL-01 要求构造组件 ASW_Com_Full_Baseline，含三个提供端口、三个需求端口及六个接口；一个 Runnable 每隔 10 ms 执行三项读取和三项写入。需求还指定接收初始值为 0、超时为 0.3 s。元模型提供内部行为、Runnable、TimingEvent 及其包含和引用关系；ICM 中的 TPS_SWCT_01519 为声明为周期执行的 Runnable 提供事件检查依据<sup style="color:#FF0000">[28]</sup>。

**任务绑定、L1 与装配。** 任务分析将内部行为、Runnable 和事件分别绑定为 IB_Com_Full_Baseline、RE_Com_Full_Baseline 和 TE_Com_Full_Baseline，并确定接口、变量访问及引用目标。L1 根据元模型与这些选择组装生成 schema，约束所需对象和包含层次。结构化结果由适配器装配，补入已绑定的固定值，再按 XSD 元素顺序序列化，形成一份组件和六份接口 ARXML。

以下摘自第一次正式生成的组件，展示事件引用和实际 Runnable 声明。省略组件及其以上父层级，并用注释标明省略的读写访问；仅调整缩排和引用文本前后的换行，引用内部未截断。

片段 A1 正式生成的周期事件及 Runnable

```xml
<SWC-INTERNAL-BEHAVIOR>
  <SHORT-NAME>IB_Com_Full_Baseline</SHORT-NAME>
  <EVENTS>
    <TIMING-EVENT>
      <SHORT-NAME>TE_Com_Full_Baseline</SHORT-NAME>
      <START-ON-EVENT-REF DEST="RUNNABLE-ENTITY">
        /Components/ASW_Com_Full_Baseline/IB_Com_Full_Baseline/RE_Com_Full_Baseline
      </START-ON-EVENT-REF>
      <PERIOD>0.01</PERIOD>
    </TIMING-EVENT>
  </EVENTS>
  <RUNNABLES>
    <RUNNABLE-ENTITY>
      <SHORT-NAME>RE_Com_Full_Baseline</SHORT-NAME>
      <!-- 省略三项读取和三项写入的 VARIABLE-ACCESS -->
    </RUNNABLE-ENTITY>
  </RUNNABLES>
</SWC-INTERNAL-BEHAVIOR>
```

**L2 与原任务验收。** 此次正式生成一次通过七份文档的 XSD 检查、22 个本地引用检查和 61 项案例结构义务。周期规则对一个适用 Runnable 完成检查并通过；任务验收另将实际周期 0.01 s 与要求的 10 ms 比较，并核对端口集合和读写关系。因此，事件存在、引用可解析与具体任务参数正确分别得到检查。

**独立受控损坏。** 同一需求另从已通过验收的确定性参考组件注入故障：删除事件引用中的内部行为路径段，保留的局部内容如下。

片段 A2 独立受控故障中的事件引用

```xml
<START-ON-EVENT-REF DEST="RUNNABLE-ENTITY">
  /Components/ASW_Com_Full_Baseline/RE_Com_Full_Baseline
</START-ON-EVENT-REF>
```

损坏后 XSD 仍通过，但本地引用找不到目标；周期检查报告该 Runnable 缺少关联的 TimingEvent，任务验收也未通过。修复定位到事件的引用文本，依据已绑定的目标恢复完整路径，即补回 IB_Com_Full_Baseline。重新序列化后一轮复验通过，组件及六份接口的文件集合和字节内容恢复为参考制品。这一单元展示独立受控修复，正式生成本身已在首次尝试中通过。

## 附录 B AUTOSAR-vLLM 解码干预

### B.1 比较条件与执行设置

实验使用 Qwen3.5-9B、vLLM<sup style="color:#FF0000">[30]</sup> 和 XGrammar<sup style="color:#FF0000">[18]</sup>，在两张 RTX 4090 上执行，张量并行度为 2。温度为 0，top_p 为 1，关闭 thinking、推测解码和前缀缓存，最大输出为 16,384 词元。20 个案例各使用三个固定种子，形成 60 个区组；提示约束 U、受约束解码 G、解码与审计 A 的六种执行排列各用于十个区组。

三组提示都给出相同需求、输出说明及完整 JSON Schema。U 仅通过提示提供约束；G 进一步将约束交给后端执行；A 进一步记录逐步干预。生成约束来自固定案例结构，包含字段、数组、嵌套和取值要求。本实验固定这些输入，以观察执行解码约束本身的作用。

### B.2 分层结果与运行代价

表 B1 各案例层次的结构验收结果

| 案例层级 | U：提示约束 | G：解码约束 | A：解码与审计 |
| --- | ---: | ---: | ---: |
| 最小，6 案×3 次 | 9/18 | 18/18 | 18/18 |
| 标准，7 案×3 次 | 18/21 | 21/21 | 21/21 |
| 完整，7 案×3 次 | 18/21 | 21/21 | 21/21 |
| 合计，20 案×3 次 | 45/60 | 60/60 | 60/60 |

提示约束组中，三个最小案例将接收通信属性数组写成对象，一个标准案例和一个完整案例出现访问引用嵌套错误。五个案例的三次重复均失败；其余案例通过结构检查和后续制品验收。执行解码约束后，各层次均通过。按基础案例观察，五案改善、十五案持平。

全部 60 次审计生成均出现无约束最高分词元被语法排除的步骤，每次 7–10 步，合计 516/54,942 步。审计组与普通受约束解码组的 60 对输出字节相同。表 B2 比较输出量和请求时间。

表 B2 词元与请求时间

| 指标 | U | G | A |
| --- | ---: | ---: | ---: |
| 输出词元总量 | 73,644 | 54,942 | 54,942 |
| 每请求平均输出词元 | 1,227.4 | 915.7 | 915.7 |
| 请求时间合计/s | 811.519 | 621.901 | 795.092 |
| 每请求平均时间/s | 13.525 | 10.365 | 13.252 |

审计增加的平均请求时间为 2.887 s，中位数为 2.634 s；累计请求时间增加 27.85%。这里的时间按模型请求统计，与正文 AUTOSAR 完整流程时间分别计量。

## 附录 C 铁路模型生成与修复

### C.1 模型来源与检查

实验复用 Train Benchmark 的元模型和六条 VIATRA 查询<sup style="color:#FF0000">[31]</sup>，作者设计服务衔接、维护预备和冗余监测三类任务，并应用于链式、分支汇合、环、自环、共享道岔、分离线路、多区域和分支环八种布局。任务规格规定对象、固定物理连接、允许赋值字段以及必须保持的服务状态和监测关系。作者将这些任务要求明确写入结构化规格，系统据此形成任务相关的约束表示和结构计划；实现中该任务产物命名为 ICM，用于绑定本次对象与要求，与方法中的可复用领域约束资源分别说明。领域检查沿用上述原生查询。

表 C1 六条原生查询

| 查询 | 本实验执行的性质 |
| --- | --- |
| PosLength | 区段长度为正 |
| SwitchMonitored | 每个道岔应被传感器监测 |
| SwitchSet | 对启用且入口信号为 GO 的路径，计划道岔设置与实际位置一致 |
| RouteSensor | 路径包含对其计划道岔实施监测的传感器要求 |
| ConnectedSegments | 同一传感器不监测形成六区段有向游走的所有区段；顶点不要求互异 |
| SemaphoreNeighbor | 不同路径要求的传感器所监测的相邻轨道满足原查询规定的公共边界信号机关联 |

生成输出经字段域和引用范围检查后装配为 XMI。验证直接加载该 XMI，执行 EMF 模型诊断和 VIATRA 查询，并与独立编写的关系查询交叉核对匹配集合。原任务验收另行检查指定状态、关系及受保护内容。

### C.2 条件与补充集合

主实验使用 gpt-5.6-luna、low 推理强度、温度 1.0、128,000 词元最大输出预算及三个固定种子。初始生成 G0 的两个分支分别为自修复 GS 和验证反馈修复 GF。受控集合中，自修复 S 获得公共规则、当前模型及允许字段，采用与 Self-Refine 相关的自我检查思路<sup style="color:#FF0000">[23]</sup>；V 增加验证反馈与非回归接纳，F 进一步提供违规位置、局部候选和依赖信息。每个分支最多两轮，每轮最多修改六个显式字段，拒绝或无进展时可以提前停止。

表 C2 实验集合与严格成功

| 集合 | 输入规模 | 比较条件 | 严格成功 |
| --- | --- | --- | --- |
| 生成 | 24 任务各三次，共 72 起点 | G0／GS／GF | 23／29／51，分母均为 72 |
| 固定损坏 | 每任务一项单故障及一项复合故障；复合模型含 12 个耦合、12 个并发，各三次 | S／V／F | 129／140／141，分母均为 144 |
| 任务义务故障 | 24 输入各三次 | S／V／F | 67／69／72，分母均为 72 |
| 正确性保持 | 3 正确输入各三次 | S／V／F | 各 9/9 |

任务义务故障将任务要求的路径启用状态反转，包括 16 个误停用和 8 个误启用案例；这些输入仍通过原生领域查询，却不满足本次任务。这一对照使任务验收的作用单独可见。正确性保持集合则检查修复流程能否保留已经满足要求的结果。

主实验的 49 个失败起点中，48 个已形成模型。GF 恢复其中 28 个；余下 20 个均仍有 SemaphoreNeighbor 违反。停止原因包括 16 个提案因使已有检查退化而被拒绝、3 个弃权和 1 个提案未消除违反；另有 1 个起点在初始赋值阶段未获接纳。当前流程能够阻止退化修改，但没有为所有关系组合找到可接纳修复。

同一基础任务上的结果按条件配对，先汇总该任务的重复运行及相应故障，再对 24 个任务等权计算成功率差。表 C3 的差值为前一条件减去后一条件，单位为百分点；区间通过对基础任务进行 9,999 次配对重采样估计。四项比较按 0.05 的名义误差水平分配，每项报告 1 − 0.05/4 = 98.75% 的名义边际百分位区间；三次重复保留在各自任务内，基础任务数为 24。

表 C3 铁路主实验的成功率差及区间

| 比较条件 | 成功率差／百分点 | 98.75% 重采样区间／百分点 |
| --- | ---: | --- |
| 自然生成 验证反馈修复 − 初始生成 | +38.89 | [22.22, 56.94] |
| 自然生成 验证反馈修复 − 自修复 | +30.56 | [15.28, 47.22] |
| 受控损坏 验证反馈与定位修复 − 自修复 | +8.33 | [0.00, 19.44] |
| 受控损坏 验证反馈与定位修复 − 验证反馈修复 | +0.69 | [−3.47, 5.91] |

例如，验证反馈修复与自修复分别成功 51/72 和 29/72，相差 30.56 个百分点。受控损坏中，增加定位信息相对已有验证反馈净增一个成功，其差值区间包含零，尚不足以明确该额外收益。按八种线路布局重采样的敏感性分析、完整配对记录与计算脚本见复现材料的统计说明。

生成 G0 的 72 份响应使用 371,575 词元，响应时间合计 812.54 s；GS 追加 81 份响应、464,875 词元与 799.19 s；GF 追加 48 份响应、335,937 词元与 635.40 s。完整修复路径的成本包含其共享生成成本和相应追加成本。铁路主实验各集合保存响应的总量为 1,074 份、6,118,127 词元、8,840.70 s。

### C.3 第二模型及运行代价

第二模型使用 gpt-5.6-terra、low 推理强度和固定种子 104729，沿用同一 24 个任务、检查、允许字段与修复轮数。Luna 的同任务同种子结果用于比较。

表 C4 两模型的同任务结果

| 条件 | Luna 严格成功 | Terra 严格成功 |
| --- | ---: | ---: |
| G0，不修复 | 6/24（25.0%） | 18/24（75.0%） |
| GS，自修复 | 8/24（33.3%） | 22/24（91.7%） |
| GF，完整修复 | 13/24（54.2%） | 22/24（91.7%） |

Terra 的 18 个初始成功全部保留，六个失败起点在 GS 和 GF 下各恢复四个。两分支共同成功 21 个，共同失败一个，另外各有一个仅该分支成功。补充运行最大完成预算为 4,096 词元；本批保存响应均在上限内完成。Luna 与 Terra 的输出预算不同，因此该补充按实际配置描述初始生成及修复结果。

Terra 保存的 60 份响应共用 338,438 词元，其中输入 301,834、输出 36,604。

### C.4 贯穿案例 两条服务路径的关系修复

BAL-1-01 要求在固定的六区段链式布局上配置两条启用路径 r1、r2，保持物理连接、计划道岔位置和指定监测：n1 覆盖 w1、t1，n2 覆盖 w2、t2，n3 覆盖 t3；每条路径至少要求两个不同的传感器。结构化任务规格固定对象及连接，程序据此组装生成约束，将传感器需求限定在 n1–n6 等已声明的可选对象内。种子 155921 的初始模型取 r1.requires=[n1,n3]、r2.requires=[n2,n3]，经装配形成以下 XMI。

片段保留原始引用，仅调整换行并省略外围及其他节点。XMI 标识须按身份映射读取：n12、n13 分别对应路径 r1、r2；n4、n5、n6 对应业务传感器 n1、n2、n3；n15、n16 对应 t2、t3；n1、n2、n3 对应信号机 m_boundary、m_in、m_out。因此，原始 requires="n4 n6" 表示业务层的 [n1,n3]。

片段 C1 初始 XMI 及修复后的路径字段

```xml
<!-- G0：传感器、相邻区段及两条路径的局部摘录 -->
<sensors xmi:id="n5" id="5" monitors="n15 n21" />
<sensors xmi:id="n6" id="6" monitors="n16" />
<elements xmi:id="n15" id="15" xsi:type="railway:Segment"
  connectsTo="n16" monitoredBy="n5" length="40">
  <semaphores xmi:id="n1" id="1" signal="GO" />
</elements>
<routes xmi:id="n12" id="12" active="true" entry="n2" exit="n1" requires="n4 n6">
  <follows xmi:id="n10" id="10" position="DIVERGING" target="n20" route="n12" />
</routes>
<routes xmi:id="n13" id="13" active="true" entry="n1" exit="n3" requires="n5 n6">
  <follows xmi:id="n11" id="11" position="DIVERGING" target="n21" route="n13" />
</routes>
<!-- GF：仅 r1.requires 改变，r2 及上述监测和连接保持不变 -->
<routes xmi:id="n12" id="12" active="true" entry="n2" exit="n1" requires="n4 n5">
  <follows xmi:id="n10" id="10" position="DIVERGING" target="n20" route="n12" />
</routes>
```

L2 成功加载初始 XMI，EMF 诊断无结构错误，其余五条原生查询均通过；SemaphoreNeighbor 返回下列违反，参数按信号机、两条路径、两个传感器和两个轨道元素排列。

片段 C2 初始模型的关系检查诊断

```text
SemaphoreNeighbor: FAIL
tuple = [m_out, r2, r1, n2, n3, t2, t3]
```

这里 t2→t3 分别由 r2 所需的 n2 和 r1 所需的 n3 监测，触发 r2 出口与 r1 入口应为同一信号机的要求；实际二者为 m_out 与 m_in。GF 依据诊断及局部候选，仅将 r1.requires 改为 [n1,n2]，如片段后半所示。复验记录中六条查询均为空匹配，两条路径仍启用，七项任务义务及受保护内容检查全部通过；提案通过修复接纳，一轮后达到严格成功。L1 限定可选引用，L2 检查跨对象关系，修复接纳同时保持服务任务。

## 附录 D 国际私法决策

### D.1 案例与比较条件

PIL 实验采用由两名国际私法研究生构建的 60 个英文合成管辖情景。两人分别复核初轮参考标签，初轮未查看对方判断，再共同讨论分歧。案例依据 Brussels I bis 的 2015 年 2 月 26 日合并文本<sup style="color:#FF0000">[32]</sup>及欧盟商标条例的 2025 年 12 月 1 日合并文本<sup style="color:#FF0000">[33]</sup>。依据条文含义整理决策字段、管辖类型和跨字段检查，并将 58 条条款转述组织为支持库。条文以法律文书和条款的联合身份引用，固定词汇检索最多返回 12 条。

表 D1 生成条件

| 条件 | 输入依据 | 结构执行 | 生成后处理 |
| --- | --- | --- | --- |
| P0 基础提示 | 案情及共同输出要求 | 提示要求 | 解析并检查结构 |
| P1 检索增强 | 增加检索法律依据 | 提示要求 | 解析并检查结构 |
| P2 结构约束 | 与 P1 相同 | 严格 schema | 检查结构后发布 |
| P3 完整检查 | 与 P1 相同 | 严格 schema | 审计、一次修复、复验与发布控制 |

各组使用 gpt-5.6-luna、low、温度 1.0、128,000 词元最大输出预算和三个固定种子，每组 180 个结果。运行时模型和审计器不读取参考答案。案例先固定参考判断，模型输出随后按共同指标评价。

### D.2 审计与结果

审计器由 LLM 辅助人工编写，检查字段类型、枚举、主要与备选管辖类型、结论与部分条款之间的约定，以及引用是否位于允许证据中。P3 将原事实、相同证据、原答案和诊断交给模型，允许一次修订；复验仍失败时保存关闭记录。

主要复合终点要求结构有效、共同交付规则通过、四项参考义务兼容且实际发布。参考义务分别检查所选结论、主要管辖类型、必需证据和条件标记；证据义务要求与非空必需集合至少有一项交集。自由文本法律理由不由这四项字段比较完整判定。

表 D2 四组结果 每组 180 个结果

| 组别 | 结构有效 | 交付有效 | 实际发布 | 参考兼容 | 主要复合终点 |
| --- | ---: | ---: | ---: | ---: | ---: |
| P0 | 180（100.0） | 91（50.6） | 180（100.0） | 74（41.1） | 73（40.6） |
| P1 | 178（98.9） | 117（65.0） | 178（98.9） | 102（56.7） | 96（53.3） |
| P2 | 180（100.0） | 118（65.6） | 180（100.0） | 105（58.3） | 101（56.1） |
| P3 | 180（100.0） | 180（100.0） | 176（97.8） | 144（80.0） | 143（79.4） |

P3 的交付有效记录中包含四个关闭记录，实际发布为 176 个，达到主要终点为 143 个。62 个单元触发修复，其中 40 个从参考不兼容转为兼容并发布，42 个修复单元最终达到主要终点；另有 3 个从兼容转为不兼容。字段兼容与交付通过因而分别统计。

相同案例在四种条件下的主要复合终点差异见表 D3。先在每个案例内汇总三次运行，再计算条件间的差值；以 60 个案例为单位进行 20,000 次配对重采样，报告 95% 百分位区间；每次抽取保留该案例在各条件下的对应结果。

表 D3 PIL 主要复合终点的成功率差及区间

| 比较条件 | 成功率差／百分点 | 95% 重采样区间／百分点 |
| --- | ---: | --- |
| 检索增强 − 基础提示 | +12.8 | [2.2, 23.3] |
| 结构约束 − 检索增强 | +2.8 | [−3.3, 9.4] |
| 完整检查 − 结构约束 | +23.3 | [13.3, 33.9] |
| 完整检查 − 基础提示 | +38.9 | [27.8, 50.0] |

完整检查相对结构约束增加 42 个主要终点成功结果，对应 23.3 个百分点。单独增加结构约束的差值为 2.8 个百分点，区间包含零。按 31 个设计来源组的敏感性分析及四项比较的校正检验保存在复现材料中。表中区间估计平均差值；另存的符号检验评价改善与退化方向并进行多重比较校正，不能将两种分析视为同一个判定。

P0–P3 的引用 F1 均值分别为 0.449、0.720、0.712、0.692；每个预定单元的平均词元用量分别为 1,177.39、1,465.77、1,746.33、2,392.31，P3 包含追加修复。完整检查的主要终点更高，引用重合度与成本则呈现不同变化。

### D.3 贯穿案例 选法院协议的类型修订

**事实与结构化生成。** case8 中，双方均住意大利，约定瑞典法院管辖，一方仍在意大利起诉。第 1 次 P3 运行检索到 Brussels I bis 的 Article 25、25(1) 等条款，以相同事实和证据生成决策记录。严格输出结构控制字段与枚举；初始 JSON 结构通过检查，结论为让位于约定法院。

**实际诊断。** 审计指出结论与主要管辖类型不一致：该结论要求主要类型为 `agreement`，而已填写的 `exclusive` 还缺少其编码规则要求的条款依据。修订输入包含原事实、相同检索证据、初始答案和两条诊断，最多允许一次尝试。下面摘录该次初始答案和修订答案的相关字段，保留原键名、取值与依据顺序。

片段 D1 初始决策记录的相关字段

```json
{
  "conclusion": "Decline_in_favor_of_chosen_court",
  "forum": "Swedish courts",
  "forum_type": "exclusive",
  "alternative_forum_types": ["agreement"],
  "legal_basis": [
    {"instrument": "BRUSSELS_I_BIS", "provision": "Art.25"},
    {"instrument": "BRUSSELS_I_BIS", "provision": "Art.25(1)"}
  ]
}
```

片段 D2 一次修订后的相关字段

```json
{
  "conclusion": "Decline_in_favor_of_chosen_court",
  "forum": "Swedish courts",
  "forum_type": "agreement",
  "alternative_forum_types": ["exclusive"],
  "legal_basis": [
    {"instrument": "BRUSSELS_I_BIS", "provision": "Art.25"},
    {"instrument": "BRUSSELS_I_BIS", "provision": "Art.25(1)"}
  ]
}
```

**复验与发布。** 修订交换主要与备选类型，保留法院、结论及上述依据。复验的结构和审计均通过，记录实际发布，并由参考不兼容转为兼容，达到主要复合终点。本文以 `agreement` 表示协议管辖依据，`exclusive` 的主要类型对应预先编码的法定专属管辖类别；该修订不否定 Article 25(1) 下选法院协议可能具有的排他效力<sup style="color:#FF0000">[32]</sup>。此例展示结构有效之后的跨字段检查与修订，不能据此认定全部法律条件均已得到证明。

### D.4 定向专家复核

在自动评分之外，专家还对 case19 和 case42 的三份具体回答作了定向复核。case19 中，依据 Article 6(1) 转交德国国内法的结论明确，后续国内法是否赋予管辖权仍待判断<sup style="color:#FF0000">[32]</sup>；条件标记应评价所选结论本身，规范编码为 false。原模型 true 反映了对后一层问题的解释，实体解释可接受，但不据此改写其原自动终点。

case42 中，法国消费者向荷兰商家网购家具，并另行确认阿姆斯特丹法院条款。P1 第一次回答从荷兰住所直接推出阿姆斯特丹具体法院具有管辖权，专家认为后文未纠正这一错误，判为不可接受；该回答的自动终点通过。P3 第一次回答在后文明确给整个结论加上消费者规则和选法院条件限制，专家判为有条件可接受。消费者另行确认条款并不自动满足 Articles 19 和 25(4) 的要求<sup style="color:#FF0000">[32]</sup>。这一对照说明结构化终点与全文实体判断应分别解释。

上述意见关联具体案例和原回答，用于解释评分所覆盖的内容。完整案例、任务配置、模型制品、评价结果和分析入口按四组实验保存在随文复现材料中。

# 参考文献

[18] Dong, Yixin; Ruan, Charlie F.; Cai, Yaxing; Lai, Ruihang; Xu, Ziyi; Zhao, Yilong; Chen, Tianqi (2025). XGrammar: Flexible and Efficient Structured Generation Engine for Large Language Models. Proceedings of Machine Learning and Systems, 7. [https://proceedings.mlsys.org/paper_files/paper/2025/hash/5c20ca4b0b20b0bd2f1d839dc605e70f-Abstract-Conference.html](https://proceedings.mlsys.org/paper_files/paper/2025/hash/5c20ca4b0b20b0bd2f1d839dc605e70f-Abstract-Conference.html)

[23] Madaan, Aman; Tandon, Niket; Gupta, Prakhar; Hallinan, Skyler; Gao, Luyu; Wiegreffe, Sarah; Alon, Uri; Dziri, Nouha; Prabhumoye, Shrimai; Yang, Yiming; Gupta, Shashank; Majumder, Bodhisattwa Prasad; Hermann, Katherine; Welleck, Sean; Yazdanbakhsh, Amir; Clark, Peter (2023). Self-Refine: Iterative Refinement with Self-Feedback. Advances in Neural Information Processing Systems, 36, 46534–46594. [https://doi.org/10.52202/075280-2019](https://doi.org/10.52202/075280-2019)

[28] AUTOSAR (2015). Software Component Template. AUTOSAR; Document ID 062; Classic Platform Release 4.2.2; 31 July 2015. [https://www.autosar.org/fileadmin/standards/R4.2.2/CP/AUTOSAR_TPS_SoftwareComponentTemplate.pdf](https://www.autosar.org/fileadmin/standards/R4.2.2/CP/AUTOSAR_TPS_SoftwareComponentTemplate.pdf)

[29] AUTOSAR (2015). Specification of RTE. AUTOSAR; Document ID 084; Release 4.2.2; 31 July 2015. [https://www.autosar.org/fileadmin/standards/R4.2.2/CP/AUTOSAR_SWS_RTE.pdf](https://www.autosar.org/fileadmin/standards/R4.2.2/CP/AUTOSAR_SWS_RTE.pdf)

[30] Kwon, Woosuk; Li, Zhuohan; Zhuang, Siyuan; Sheng, Ying; Zheng, Lianmin; Yu, Cody Hao; Gonzalez, Joseph E.; Zhang, Hao; Stoica, Ion (2023). Efficient Memory Management for Large Language Model Serving with PagedAttention. Proceedings of the ACM SIGOPS 29th Symposium on Operating Systems Principles. [https://doi.org/10.1145/3600006.3613165](https://doi.org/10.1145/3600006.3613165)

[31] Szárnyas, Gábor; Izsó, Benedek; Ráth, István; Varró, Dániel (2018). The Train Benchmark: cross-technology performance evaluation of continuous model queries. Software and Systems Modeling, 17, 1365–1393. [https://doi.org/10.1007/s10270-016-0571-8](https://doi.org/10.1007/s10270-016-0571-8)

[32] European Parliament; Council of the European Union (2012). Regulation (EU) No 1215/2012 of the European Parliament and of the Council of 12 December 2012 on jurisdiction and the recognition and enforcement of judgments in civil and commercial matters (recast). Official Journal of the European Union, L 351, 20 December 2012, pp. 1–32; Consolidated text of 26 February 2015. [https://eur-lex.europa.eu/eli/reg/2012/1215/2015-02-26/eng](https://eur-lex.europa.eu/eli/reg/2012/1215/2015-02-26/eng)

[33] European Parliament; Council of the European Union (2017). Regulation (EU) 2017/1001 of the European Parliament and of the Council of 14 June 2017 on the European Union trade mark (codification) (Text with EEA relevance). Official Journal of the European Union, L 154, 16 June 2017, pp. 1–99; Consolidated text of 1 December 2025. [https://eur-lex.europa.eu/eli/reg/2017/1001/2025-12-01/eng](https://eur-lex.europa.eu/eli/reg/2017/1001/2025-12-01/eng)
