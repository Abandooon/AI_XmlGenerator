# 审稿意见与当前修改对应

本表保留原矩阵中的31项归一化意见及编号，处理内容按当前方法论、实验和附录更新。意见摘要不替代编辑信中的原文；正式回复应逐条引用原意见并绑定最终页码和行号。

当前中文章节已经形成，但全篇英文稿、摘要、贡献、相关工作、结论和正式回复信仍待合并。本表的章节覆盖不表示投稿稿已完成。原始意见见 [编辑与审稿意见](sources/SOSYM-26-00005681_DECISION_LETTER_2026-06-18.txt)，当前文件见 [总导航](README.md)，实际证据定位见 [自审与材料说明](../docs/SELF_REVIEW.md)。

| 编号 | 来源 | 原矩阵保留的意见摘要 | 当前对应 | 处理内容及未完成范围 |
| --- | --- | --- | --- | --- |
| E-01 | Editor | The paper is difficult to read; terms and abstractions drift. | 方法全章；实验4.1、4.2、4.5 | 方法正文使用通用 MDE 术语，保留 ICM、L1、L2；简化形式化。摘要、引言及结论仍待统一。 |
| E-02 | Editor | The boundary between general ATLAS and its AUTOSAR realization is unclear. | 方法3.5、3.6；实验4.2、4.3；附录B、C | ATLAS 限于已有显式元模型及可实现约束。AUTOSAR 和铁路分别说明工程实现；PIL 仅补充结构化决策证据。 |
| E-03 | Editor | Dataset source, language, repository state, and model inconsistency undermine the evaluation. | 实验4.1、4.6；附录A、C–F | 报告内部设计来源、语言、实际请求模型、全部预定分母及证据留存范围。铁路另有同24任务、固定种子的Luna–Terra描述性比较，模型内部修复对照分别解释。 |
| E-04 | Editor | AGR lacks execution, stability, cost, and human-involvement evidence. | 实验4.4；附录A、D、E | 报告实际修复、失败、响应和用量。AUTOSAR 核心85与替代15分别计量；铁路提供自然失败及重复运行证据。人工耗时和人效未测量。 |
| R1-01 | Reviewer 1 | RAG, constrained decoding, schema enforcement, and LLM repair are known techniques; novelty is overstated. | 方法ICM构建与L1/L2；实验4.2、4.5 | 组成技术属于既有工作；贡献定位为元模型锚定的 ICM 构建及约束与生成、检查、修复的组织。相关工作及全篇贡献表述待同步，不把流水线通过率当作每个组件的新颖性证明。 |
| R1-02 | Reviewer 1 | AUTOSAR may be poorly represented in pretraining; the paper does not establish what the model knows. | 实验4.4.1、4.6 | 只报告当前60个整体流程结果，不推断训练语料覆盖、基础模型知识或未经处理的原始生成能力。 |
| R1-03 | Reviewer 1 | Results obtained with different models cannot be compared as if they isolate a mechanism. | 实验4.1、4.3、4.6；附录D.4、E | 本地U/G/A和PIL四组各自控制模型；工程实验分开解释。铁路补充同24任务、固定种子的两模型对照，各自GS/GF共享自身G0；模型间差异仅描述，Terra内部检验不代表模型间检验。服务报告身份不等于独立模型认证。 |
| R1-04 | Reviewer 1 | The repository exposes Chinese/mixed-language requirements, casting doubt on the reported language condition. | 实验4.1；附录A、D、E | AUTOSAR 正式需求为作者设计英文任务；铁路为作者任务规格；PIL 为人工复核英文情景。开发历史不混入正式样本。 |
| R1-05 | Reviewer 1 | The 20-system/284-file experiment lacks a trustworthy, reproducible provenance chain. | 当前实验4及附录全部结果 | 旧20系统／284文件实验不计入任何当前分母，也不更名复用其结果。全篇旧表及依赖主张须在合稿时删除。 |
| R1-06 | Reviewer 1 | The paper conflates token-level constrained decoding with hosted structured output. | 方法3.5；实验4.1、4.3；附录C | 托管结构化输出的可见证据与本地逐步解码审计区分；不由API调用声称观察了托管服务内部掩码。 |
| R1-07 | Reviewer 1 | The reported “156 allowed tokens” statistic is not a defensible diagnostic measure. | 实验4.3；图7；附录C | 不用旧允许token均数；保留516/54,942绑定标记及其定义。缺历史logits与掩码，不能独立重算全部布尔判定，也不是token改写率。 |
| R1-08 | Reviewer 1 | The utility of audit logs relative to IDEs or ordinary validators is not demonstrated. | 实验4.3、4.6；附录C、F | 报告审计留存能力和27.85%累计时间开销；没有IDE或工程师效率对照，不作效益推断。 |
| R1-09 | Reviewer 1 | Section 4 contains no quantitative execution data for AGR. | 实验4.4；附录A、D、E | AUTOSAR受控恢复、铁路自然与受控失败、PIL一次修复分开计量，报告失败及用量。 |
| R1-10 | Reviewer 1 | Repair “stability” is asserted without repeated repair attempts. | 实验4.4、4.6；附录A、D | AUTOSAR每设计单元只执行一次，不称修复重复性；铁路三seed结果及稳定性按基础任务报告，不能推广到所有修复任务。 |
| R1-11 | Reviewer 1 | Human effort, repair cost, or productivity gains are unsupported. | 实验4.4.3、4.6；附录C–E | 承认案例、适配、检查器和专家准备中的人工参与；已知token与响应耗时不等于完整成本，无人效主张；第二模型费用仅为渠道用量估算，未知费用保留预留。 |
| R1-12 | Reviewer 1 | Cross-domain generalization is not empirically established. | 实验4.5、4.6；附录D、E | 铁路提供第二工程模型实例的有限证据；PIL仅提供浅层结构化决策证据。模板共享、开发可见和适配工作均披露，不声称任意领域迁移。 |
| R1-13 | Reviewer 1 | Dataset provenance, representativeness, language, and selection bias are unclear. | 实验4.1.2、4.6；附录A | 依据规范、工程观察、工具资料及作者重组说明20案例的形成；明确结构化精确规格与接口目录也为输入，不评价精确要求的独立自然语言提取；不称官方测试集或独立客户需求样本。 |
| R2-01 | Reviewer 2 | Readers need concise AUTOSAR and ARXML background. | 实验4.1.2 | 补入AUTOSAR组件、接口及ARXML多文件表达的简要背景，并区分XSD与任务验收。 |
| R2-02 | Reviewer 2 | The method needs a concrete running example rather than only abstract layers. | 实验4.2、图6；附录B；方法图2、4、5 | 采用TPS_SWCT_01519实际规则链，区分周期事件存在、计划取值一致和原任务周期满足；结合受控修复说明检查对象和复验。 |
| R2-03 | Reviewer 2 | Implementation details do not distinguish implemented, prototype, evaluated, and unevaluated parts. | 实验4.1.2、4.2、4.5；附录B | 分别说明已有功能、当前记录来源、实际评价及未评价部分；ICM存量与待确认状态不合并为全体已专家验证。 |
| R2-04 | Reviewer 2 | Path S2 / natural-language metamodel induction is described as core despite not being evaluated. | 方法适用范围及3.6；实验4.1、4.2 | 自然语言到领域元模型的构建不在ATLAS方法范围；铁路使用作者结构化任务规格，不能作为自动抽取实验。 |
| R2-05 | Reviewer 2 | Domain-general interfaces and AUTOSAR-specific mechanisms are mixed together. | 方法全章；实验4.1.2、4.5 | 方法表述保持领域通用；工程特有元模型、序列化、检查器和允许编辑在实验实例化中说明。 |
| R2-06 | Reviewer 2 | The paper does not clearly distinguish a single ARXML file, a component bundle, and a multi-file system. | 实验4.1.2、4.4.1；附录A | 60个工件束包含255文件；文件数不作为独立任务数。声明范围内通过与完整规范语料未完成同时报告，不主张系统部署合规。 |
| R2-07 | Reviewer 2 | The formal presentation is dense and insufficiently connected to the executable workflow. | 方法形式化、3.6及图1–5；实验4.2 | 沿用简化形式化，说明各元素并连接执行流程；3.6用具体职责和条件说明检查器，不增添多余数学体系。 |
| R2-08 | Reviewer 2 | The paper overstates system-scale semantic correctness and the role of SHACL/SMT. | 方法3.6；实验4.1.2、4.4.1、4.6；附录B | 据实际XSD、声明式规则、Python插件、EMF和VIATRA报告；不沿用未获证据支持的SHACL/SMT或完整语义正确性主张。 |
| R3-01 | Reviewer 3 | A clearer end-to-end figure and running example are needed. | 方法图1、2、4、5；实验4.2及图6 | 当前中文图统一黑白灰、形状和线型；来源到检查的实际周期规则实例连接方法流程。 |
| R3-02 | Reviewer 3 | The origin and scope of experimental cases need clarification. | 实验4.1.2；附录A、D、E | 分别披露AUTOSAR、铁路和PIL设计者、来源、共享模板及内部开发关系。 |
| R3-03 | Reviewer 3 | AGR needs quantitative evidence and clearer failure analysis. | 实验4.4；附录A、D、E | AUTOSAR核心/替代分开；铁路报告修复后仍失败以及F/V配对差异；PIL报告3个诱发不兼容及机器通过反例。 |
| R3-04 | Reviewer 3 | Low or confusing SHACL/SMT results need defensible interpretation. | 实验4.1.2、4.4.1、4.6 | 不继续使用旧SHACL/SMT结果解释方法。当前结果按实际执行器和声明覆盖报告；全篇旧表与引用待同步移除。 |
| R3-05 | Reviewer 3 | The ICM/layering idea is promising but terminology and presentation should be simplified. | 方法ICM构建及L1/L2；实验4.2 | ICM明确包含元模型表示、来源、结构化约束及实体/用途/实现关联，保留构建贡献；不再仅将其缩减为责任接口或内部存储表。 |
| R3-06 | Reviewer 3 | Conclusions should reflect semi-automatic support and limitations rather than full automation. | 方法3.6；实验4.4.3、4.6；附录B、E、F | 明确LLM辅助人工开发检查器，人工审核与自动检查不同。结论应限定当前可支持范围；完整论文结论尚待合并改写。 |

所有条目的最终图表号、页码和行号均在整稿编译后填入，不以独立章节页码代替。原意见所提可能另附的审稿文件，如未包含在现有编辑信和材料中，仍应在投稿系统中核对；本轮没有读取投稿系统中的未知附件。

第二模型补充已完成全部24任务、72终点，Terra为18/22/22，同任务Luna为6/8/13。正文4.4.2及图8提供概要，附录D.4保留配对检验、单种子及输出上限差异；未发现GF相对GS的新增成功总数，不能扩展为普遍模型优越性。最终投稿页码与行号仍待整稿更新。
