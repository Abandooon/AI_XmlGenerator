# 统一术语表

本表沿用已确认的图文术语约定，并补充全文涉及的领域与实验用语。英文采用美式拼写。结构约束与结构化约束、模型实例与序列化制品、验证与任务验收分别使用对应术语。

| 中文 | 统一英文 | 用法 |
|---|---|---|
| 模型驱动工程 | model-driven engineering (MDE) | 首次出现给出全称及缩写；正文通常使用 MDE。 |
| 领域元模型 | domain metamodel | 定义领域模型的类型、特征和关系；metamodel 拼写为一个词。 |
| 元模型元素 | metamodel element | 与当前正文一致，统称类、属性、关系等元模型组成部分；不统一替换为 metamodel entity。 |
| 实例模型／模型实例 | model instance | 指依据元模型组织的具体对象、属性值与关系构成的模型；全文统一使用 model instance。 |
| 候选模型 | candidate model | 指已构造且等待验证和任务验收的模型实例。 |
| 序列化制品 | serialized artifact | 指模型在 ARXML、XMI 等目标表示中的制品；全文采用美式拼写 artifact。 |
| 元模型符合性 | metamodel conformance | 说明模型与其元模型的符合关系。 |
| 模型一致性 | model consistency | 说明模型满足适用的领域关系和一致性要求；与元模型符合性分别使用。 |
| 需求满足 | requirements satisfaction | 说明输出满足原始任务要求，采用 requirements 复数。 |
| 良构约束 | well-formedness constraint | MDE 中描述合法模型应满足条件的常用表述；复数为 well-formedness constraints。 |
| 基数（元模型关系的取值范围） | multiplicity | 用于 0..1、1..* 等上下界及属性或关系的数量约束；这是图中“基数”的默认译法。 |
| 基数（集合的元素数量） | cardinality | 用于某个集合实际含有的元素数量；描述 JSON 数组数量时也可写 array size 或 number of items。 |
| 模型转换 | model transformation | 用于模型表示间的转换；序列化过程另用 serialization。 |
| 已有模型上下文 | existing model context | 指本次生成可使用的已有模型元素、属性及关系，例如既有 Runnable 与其引用路径。 |
| 集成约束模型 | Integrated Constraint Model (ICM) | 保留的核心名称；首次出现给出全称，后续使用 ICM。 |
| 结构约束／结构性约束 | structural constraint | 描述类型、必需特征、嵌套、关系和数量等结构要求。 |
| 结构化约束 | structured constraint | 强调约束被整理为具有目标、条件、要求等字段的记录；与 structural constraint 区分。 |
| 规则／约束 | rule / constraint | rule 用于领域规范规定的要求或检查规则；constraint 用于限制模型或生成内容的条件。按语义选择，不机械互换。 |
| 约束记录 | constraint record | ICM 中保存约束内容、目标元素、来源及用途等信息的记录。 |
| 结构化约束抽取 | constraint extraction | 展开描述可用 extract structured constraints from natural-language specifications。 |
| 元模型引导的 | metamodel-guided | 用于方法、抽取与生成等修饰语；术语注入的具体动作可写 provide metamodel terminology as context。 |
| 元素关联 | element association | 用于 ICM 中约束记录与元模型元素间的关联；形式化集合 A 使用 associations。 |
| 自动链接 | automatic linking | 用于建立约束记录到元模型元素链接的动作；动词用 link constraints to metamodel elements。 |
| 任务绑定 | task binding | 指将适用约束落实到本次对象、取值和引用；动作写 bind constraints to task-specific objects and values。 |
| 可追溯性 | traceability | 指需求、规范来源、约束、模型、检查及修复之间对应关系的可回查性。 |
| 追溯链接 | trace link | 指具体的跨制品对应关系；约束与类型的静态关联及本次对象绑定仍分别使用 association 和 binding。 |
| 来源信息 | provenance | 用于规范、元模型文件、版本及位置等来源信息；图中 P 保留。具体对应边使用 source link。 |
| 生成时约束 | generation-time constraint | 强调约束在生成期间执行；复数为 generation-time constraints。 |
| 生成约束 | generation constraints | 指为当前任务组装的结构、取值和引用限制；只有具体表示确实为模式时才使用 schema。 |
| 生成映射 | generation mapping | 指将元模型信息及适用约束转换为生成限制的已有映射。 |
| 生成时约束层 | generation-time constraint layer (L1) | 保持 L1 的统一名称；强调执行时可写 constraint enforcement during generation。 |
| 受约束生成 | constrained generation | 指在约束下生成内容的过程；范围比逐词元的 constrained decoding 更广。 |
| 受约束解码 | constrained decoding | 指解码时依据约束筛选允许的词元并更新匹配状态的技术。 |
| JSON Schema | JSON Schema | 保留标准名称和大小写；在本方法中表示可编译供解码后端执行的生成限制。 |
| 生成后验证层 | post-generation validation layer (L2) | 描述验证过程时使用 post-generation validation；与 formal verification 分别使用。 |
| 任务验收 | task acceptance | 指依据原始任务要求接纳结果；具体检查用 task acceptance checks。 |
| 检查器 | checker | 指执行某项检查的组件或函数，例如 reference checker；检查动作和单个检查项使用 check。 |
| 验证器 | validator | 用于组织验证能力的组件或现有工具，例如 XSD validator；同一组件在全文保持同一称谓。 |
| 验证反馈 | validation feedback | 指检查返回的违反项、对象位置和诊断信息，用于后续修复。 |
| 修复 | repair | 验证反馈修复写 repair with validation feedback，自修复写 self-repair，修复后复验写 revalidation。 |

## 摘要与引言用语

| 中文 | 英文 | 用法 |
| --- | --- | --- |
| 元模型引导的分层约束模型生成 | metamodel-guided model generation with layered constraints | 作为方法描述使用，不赋予方法新的英文专名。 |
| 运行实体 | runnable entity | 沿用英文图稿，AUTOSAR 类型标识 RunnableEntity 保持原拼写。 |
| 周期事件（本例） | timing event | 本例对应 AUTOSAR TimingEvent；周期触发要求在句中用 every 10 ms 表达。 |
| 内部行为 | internal behavior | 指 AUTOSAR 模型中包含运行实体的内部行为。 |
| 生成时约束执行 | generation-time constraint enforcement | 执行动作使用 enforcement，层名称仍用 generation-time constraint layer。 |
| 生成后检查 | post-generation checks | 具体检查可用 check，验证过程使用 validation。 |
| 完整流程运行 | end-to-end run | 20 个需求、每需求三次运行与 255 份 ARXML 文件分别计数。 |
| 受控故障注入实验 | controlled fault-injection experiment | 其中的 core units 和 substitute units 是实验单元。 |
| 结构验收 | structural acceptance | 沿用图 7；不替换为整体正确率。 |
| 严格成功判定 | strict success criterion | 计数使用 number of successful runs，比例使用 strict success rate。 |
| 验证反馈修复 | repair with validation feedback | 与英文图稿及原术语约定一致。 |
| 国际私法结构化决策 | structured decision-making in private international law | PIL 为 private international law；与工程模型实例构造分别表述。 |

## 全文补充用语

| 中文 | 英文 | 用法 |
| --- | --- | --- |
| 领域适配者 | domain integrator | 指负责接入领域映射和检查能力的人员。 |
| 领域适配组件 | domain adapter | 指模型构造、序列化等适配组件。 |
| 主要复合终点 | primary composite endpoint | 对应 PIL 中结构、交付规则、参考判断及实际发布的复合条件。 |
| 参考兼容 | compatibility with the reference judgments | 表头可用 reference compatibility。 |
| 参考判断义务 | requirements derived from the reference judgments | 指源稿定义的四项要求。 |
| 发布控制 | release control | 对应 PIL 输出是否实际发布。 |
| 复现材料 | replication package | 指论文链接的配套代码和实验材料。 |
| 形式化验证制品 | formal verification artifacts | 结论中的未来方向，涵盖验证模型、证明义务及相应检查实现。 |
| 重采样区间 | resampling interval | 保留原文的重采样方式、置信水平与区间端点。 |
| 百分点 | percentage points | 表达成功率之差，与百分比区别。 |

PIL 四个条件统一为 Basic prompting (P0)、Retrieval augmentation (P1)、Structural constraints (P2) 和 Full checks (P3)。铁路条件缩写 G0/GS/GF 与 S/V/F 保持原样。实际元模型类型、模型标识、代码字段及证据字面量保留原拼写。
