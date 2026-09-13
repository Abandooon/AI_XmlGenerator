> Historical audit record. Current supported commands and output locations are in [COMMANDS.md](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md).

# PIL 与方法主张独立复核

复核日期：2026-09-10。对象为桌面当前中文方法、实验正文、附录和根目录回复矩阵，以及已封存的 PIL 原始、勘误和专家补充材料。本报告不修改 Desktop 或仓库，不执行付费调用，不声称外部第三方专家认证，也不替代 Git 两分支同步验收。

**结论：本次范围内未发现必须修改的新增事实、统计或方法主张错误。** 当前 PIL 可以作为有明确评分边界的结构化决策补充证据；不能据此称完整 ICM 迁移、工程模型符合性或全量法律正确性已经验证。上述限制已写入现稿。31 个回复矩阵编号完整、唯一；整稿英文合并及正式逐条回复仍未完成，现有矩阵也明确保留这一状态。

## 1. 本轮实际执行的检查

- 通读当前方法正文，核对实验正文 4.5–4.6、附录 E、回复矩阵全部 31 项，并对照原编辑信及三位审稿人意见。
- 依据 PIL `PACKAGE_MANIFEST.json` 对 76 项载荷重新核对文件长度和 SHA-256：76/76 一致，缺失或差异为 0。复用此前对这些未变证据完成的全量离线重评分、请求重构、边界测试及移动目录验证，不无条件重跑同一套流程。
- 从勘误分析的 720 条 `scored_units` 重新聚合各组结果、修复事件和 60 案的配对差值；以二项分布精确求和独立计算双侧符号检验，再对四项比较作 Holm 校正。结果与现稿一致。
- 将原分析和勘误分析按 `unit_id` 对齐、逐字段比较：仅 case19 的 12 个 `evidence_requirement_met` 从 false 改为 true，其余逐条评分字段未变。
- 核对专家补充记录、未来字段协议和 720 条意见关联层：3 条 reviewed、717 条 not_reviewed；完整法律正确率为 null。核对三条具体答案的自动终点分别为 false、true、true。
- 以正则提取当前矩阵行首编号：31 项、31 个唯一编号，结构为 E-01–04、R1-01–13、R2-01–08、R3-01–06。

本轮使用本地 Python 3.12 的标准库 `json/hashlib/collections/math/re`，以 `python -I -B -c <只读核对程序>` 执行；不导入生成器，不访问网络或 API 凭据。bootstrap 数值复用此前完整重算后、且本轮哈希未变的分析文件；本轮未声称重新执行 bootstrap 或重新进行法律实体裁决。

## 2. PIL 事实与当前表述

| 核对对象 | 证据与现稿定位 | 判断 |
| --- | --- | --- |
| 案例与专家身份 | [HUMAN_REVIEW_CLARIFICATION.json](/E:/Desktop/ATLAS论文修改版/12_审稿复现包_2026-09-09/reviewer_release/experiments/pil/expert_supplement/HUMAN_REVIEW_CLARIFICATION.json:4)；[附录 E.1](/E:/Desktop/ATLAS论文修改版/方法与实验章节/附录章节_v2.md:239) | 设计者 Xinyue Yang；Xinyue Yang、Yirui Wang 初轮分别判断、未看对方初轮结果，之后讨论分歧；Codex 辅助填写。接受用户确认，不再将 AI 辅助误记为无人评审，不虚构历史签署日期。 |
| 设计与四组 | [契约定义](/E:/Desktop/ATLAS论文修改版/12_审稿复现包_2026-09-09/reviewer_release/experiments/pil/frozen/prepaid_freeze/pil_v4_contract.py:369)；[正式执行](/E:/Desktop/ATLAS论文修改版/12_审稿复现包_2026-09-09/reviewer_release/experiments/pil/frozen/prepaid_freeze/pil_v4_arms.py:252)；[附录 E1](/E:/Desktop/ATLAS论文修改版/方法与实验章节/附录章节_v2.md:243) | 60 案×4 组×3 次=720 单元，各组 180。P0 无检索，P1 加检索，P2 加提供方严格 schema，P3 再加审计、至多一次 LLM 修复及关闭发布策略。没有将审计程序误称为修复 LLM。 |
| 共同评分与独立性 | [评分器](/E:/Desktop/ATLAS论文修改版/12_审稿复现包_2026-09-09/reviewer_release/experiments/pil/frozen/prepaid_freeze/pil_v4_rescore.py:117)；[四字段判断](/E:/Desktop/ATLAS论文修改版/12_审稿复现包_2026-09-09/reviewer_release/experiments/pil/frozen/prepaid_freeze/pil_v4_contract.py:354)；[附录 E.2](/E:/Desktop/ATLAS论文修改版/方法与实验章节/附录章节_v2.md:258) | 运行时不读取 gold；离线交付判定复用运行时审计实现，不能称实现上独立的法律验证。主要终点同时要求结构、共同交付、四字段参考兼容和实际发布。现稿区分准确。 |
| case19 勘误 | [修正分析](/E:/Desktop/ATLAS论文修改版/12_审稿复现包_2026-09-09/reviewer_release/experiments/pil/corrections/expected/PIL_V41_ERRATUM1_ANALYSIS.json:1)；[附录 E.4](/E:/Desktop/ATLAS论文修改版/方法与实验章节/附录章节_v2.md:300) | 必需证据 Article 62(1)→6(1)，影响 12 个证据标记，不改变主要终点或配对统计，不重新生成答案。不能把这项输入勘误当作对全部法律判断重新标注。 |
| 三条事后意见 | [EXPERT_ADJUDICATIONS.json](/E:/Desktop/ATLAS论文修改版/12_审稿复现包_2026-09-09/reviewer_release/experiments/pil/expert_supplement/data/EXPERT_ADJUDICATIONS.json:3)；[表 E4](/E:/Desktop/ATLAS论文修改版/方法与实验章节/附录章节_v2.md:304) | 19/P3/1 实体解释可接受但条件标记层次歧义，规范 false，保留原 true 及原终点失败；42/P1/1 的 Amsterdam 推论不可接受但机器通过；42/P3/1 因全文条件限定而有条件可接受，不能说具体法院或排他效力已确定。 |
| 后续字段解释 | [FIELD_SEMANTICS_CLARIFICATION.json](/E:/Desktop/ATLAS论文修改版/12_审稿复现包_2026-09-09/reviewer_release/experiments/pil/expert_supplement/protocol/FIELD_SEMANTICS_CLARIFICATION.json:3)；[附录说明](/E:/Desktop/ATLAS论文修改版/方法与实验章节/附录章节_v2.md:312) | conditional 评价所选结论本身，不放宽为任意 bool；没有倒填旧提示。case42 的 Articles 19、25(4) 内容按用户已确认意见报告，本轮不作新的独立法律结论。 |
| 人审范围与跨域主张 | [意见关联层](/E:/Desktop/ATLAS论文修改版/12_审稿复现包_2026-09-09/reviewer_release/experiments/pil/expert_supplement/expected/EXPERT_REVIEW_JOIN_720.json:1)；[正文 4.5](/E:/Desktop/ATLAS论文修改版/方法与实验章节/实验章节_v2.md:92)；[附录 E.1](/E:/Desktop/ATLAS论文修改版/方法与实验章节/附录章节_v2.md:237) | 3 条事后意见不等于新增 720 条实体审评；没有独立因素抽取、元模型转换和完整 ICM 构建。PIL 被限定为浅层结构化决策补充，没有用于冒充工程模型迁移。 |

## 3. 数值复核

下列每组分母均为 180；现稿表 E2 与本轮重聚合完全一致。

| 组 | 结构有效 | 交付有效 | 实际发布 | 参考兼容 | 主要终点 |
| --- | ---: | ---: | ---: | ---: | ---: |
| P0 | 180 | 91 | 180 | 74 | 73 |
| P1 | 178 | 117 | 178 | 102 | 96 |
| P2 | 180 | 118 | 180 | 105 | 101 |
| P3 | 180 | 180 | 176 | 144 | 143 |

P3 交付有效包括 4 个关闭记录，不能当作成功发布。62 个修复单元中 58 个发布，40 个恢复参考兼容且发布，42 个最终达到复合终点，3 个诱发参考不兼容。正文、附录与复现包没有混用这些事件。

| 案例配对比较 | 正/负/平案例数 | 差值/百分点 | 本轮精确双侧 p | 本轮 Holm p |
| --- | --- | ---: | ---: | ---: |
| P1−P0 | 25/13/22 | +12.7778 | 0.0729513885 | 0.1459027770 |
| P2−P1 | 15/11/34 | +2.7778 | 0.5571970940 | 0.5571970940 |
| P3−P2 | 24/4/32 | +23.3333 | 0.0001799911 | 0.0005399734 |
| P3−P0 | 35/5/20 | +38.8889 | 0.0000013826 | 0.0000055304 |

现稿 [统计说明与表 E3](/E:/Desktop/ATLAS论文修改版/方法与实验章节/附录章节_v2.md:279) 保留了 60 案 bootstrap、31 依赖簇敏感性、各 20,000 次，以及区间未作同时校正的边界。P1−P0 区间虽正但 Holm 检验不显著，P2−P1 无可靠单独增益；P3−P2 是审计、修复与发布策略的联合效应。引用 F1 的 P3=0.692 低于 P1=0.720、P2=0.712，也没有删去这一不利结果。

原始账本及请求完整性的全量验证复用 [移动目录验证报告](/E:/Desktop/ATLAS论文修改版/12_审稿复现包_2026-09-09/reviewer_release/experiments/pil/verification/relocation/verification_report.json:1)：720 最终单元、784 传输记录、782 唯一响应。132 单元先导批次整体排除的依据保留于原冻结包；附录明确先导设计影响和不混合计数，复现包 [README](/E:/Desktop/ATLAS论文修改版/12_审稿复现包_2026-09-09/reviewer_release/experiments/pil/README.md:75) 给出精确排除规模。不能因正式 720 单元完整就称所有传输均成功，或推断上游模型身份已被独立认证。

## 4. 原审稿要求、31 项矩阵及方法边界

原意见批评的是当时以 AUTOSAR 为主的投稿稿，不能把后来新增的 PIL 或铁路实验说成原审稿人已审核的结果。当前矩阵明确其意见为归一化摘要，并要求最终回复引用原文，没有作这种混淆。

| 原意见位置 | 当前覆盖与剩余边界 |
| --- | --- |
| [编辑信 46–52 行](/E:/Desktop/ATLAS论文修改版/SOSYM-26-00005681_DECISION_LETTER_2026-06-18.txt:46)：可读性、通用/实例边界、来源语言、修复和人工投入 | E-01–04 均在；方法先整体再细节，实验分领域计量。人工耗时与效率没有被伪造为已测。 |
| [Reviewer 1，80–94 行](/E:/Desktop/ATLAS论文修改版/SOSYM-26-00005681_DECISION_LETTER_2026-06-18.txt:80)：术语、局部/托管解码、日志效益、跨模型比较及内部题集偏差 | R1 系列保留这些限制，未用 PIL 浅层结果证明完整迁移；跨模型差异仍为描述。 |
| [Reviewer 2，118–125 行](/E:/Desktop/ATLAS论文修改版/SOSYM-26-00005681_DECISION_LETTER_2026-06-18.txt:118)：未评价的 NL 元模型路径、ICM 到检查器示例、适配实现和修复证据 | R2 系列保留；[方法 3.1](/E:/Desktop/ATLAS论文修改版/21_方法论中文稿_v5_2026-09-10/ATLAS_方法论_中文稿_v5.md:11) 排除从 NL 新建元模型，[3.3](/E:/Desktop/ATLAS论文修改版/21_方法论中文稿_v5_2026-09-10/ATLAS_方法论_中文稿_v5.md:53) 区分抽取/链接/复核/执行，[3.6](/E:/Desktop/ATLAS论文修改版/21_方法论中文稿_v5_2026-09-10/ATLAS_方法论_中文稿_v5.md:132) 明确已有工具、模板或人工实现，不新增验证器自动综合能力。 |
| [Reviewer 3，178–183 行](/E:/Desktop/ATLAS论文修改版/SOSYM-26-00005681_DECISION_LETTER_2026-06-18.txt:178)：泛化、语义限制、修复和人工角色、ICM 例子 | R3 系列保留；[方法 3.6–3.8](/E:/Desktop/ATLAS论文修改版/21_方法论中文稿_v5_2026-09-10/ATLAS_方法论_中文稿_v5.md:138) 不将 L1/L2 视为理论语法/语义分界，不把运行记录或检查通过当完整正确性证明。 |

当前 [矩阵第 5、41 行](/E:/Desktop/ATLAS论文修改版/REVIEW_RESPONSE_MATRIX.md:5) 已明确：全篇英文稿、摘要、贡献、相关工作、结论和正式回复仍待合并，最终页码行号待整稿编译；编辑信提及的可能附加审稿文件尚须在投稿系统确认。**这些是已有并需保留的投稿待办，不是本轮发现的新实验失败；Git 同步完成也不能将其改称已经关闭。** 在现有窄指标和限制下，本轮没有发现必须重跑模型、补做全 720 条法律人审才能同步材料的问题。只有今后提高到完整法律准确率或完整跨域 ICM 迁移主张时，才需要对应的新证据。

## 5. 本轮审阅版本绑定

| 当前文件 | SHA-256 |
| --- | --- |
| `方法与实验章节/实验章节_v2.md` | `2821735bafe0c0121f37f48024e02819b3b9f9b7b404077c7fa6657a48c16445` |
| `方法与实验章节/附录章节_v2.md` | `c13d9c220e2487a393fa25b1e313e9246d20d6709d0ff8880f4cd7b7beb9cd16` |
| `REVIEW_RESPONSE_MATRIX.md` | `b0814113281d92b71c09969bdfd4a5922bde75d726048725323fa81942527b26` |
| `21_方法论中文稿_v5_2026-09-10/ATLAS_方法论_中文稿_v5.md` | `7da6744d6c9d518f7b1edbb8773f049c51590870d239355df5e2a62fb6a2d22a` |
| PIL 勘误分析 | `df9f876945cdef37e83a4aa1e14004669a440a43fc8942fdd47546085576d01f` |
| PIL 专家补充 | `34dc5058b001189ce973b4661335fc90ac37f235a2cfddec6d12f420ee1225d8` |
| PIL 人工角色确认 | `86058539007a25e5ac60025fd01c17cf3f5a4423fbd0ae16adb3e6463613c157` |

正文、矩阵或证据若在同步前发生实质改动，应以改动部分重新核对；本报告不涵盖未读取的 Git 分支文件、访问权限、远端同步结果或最终投稿稿。
