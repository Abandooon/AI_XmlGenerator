# 铁路与 Terra 同步审查

审查日期：2026-09-10。只读检查当前桌面章节、冻结实验材料及 `E:/git projects/AI_XmlGenerator/ATLAS`；没有改仓库、桌面材料或付费运行。新增发布草案仅在本审查目录。

## 1. 当前结论

当前 `方法与实验章节/实验章节_v2.md` 和 `附录章节_v2.md` 的铁路规模、成功数、区间、Terra 配对检验、调用和预算披露与保存证据一致。没有发现需要重新运行模型或改写冻结结果的问题。两模型对比必须保持描述性，不能从不同失败子集推导“模型越强，修复越好”。

| 核对项 | 冻结值 |
|---|---|
| Luna 正式生成 | G0/GS/GF：23/29/51，各以 72 为分母 |
| Luna 固定损伤 R | S/V/F：129/140/141，各以 144 为分母 |
| Luna 任务义务故障 T | 67/69/72，各以 72 为分母；不是模型转换实验 |
| Luna 全部正式证据 | 747 actions、891 endpoints；1,074 响应、1,085 派发意图、11 未知 |
| Terra 完成情况 | 24 任务、72 已知终点；G0/GS/GF=18/22/22 |
| Terra G0—GF | 18 均成功、2 均失败、4 改善、0 退化；+16.67 pp；精确双侧 p=.125、Holm=.25 |
| Terra GS—GF | 21 均成功、1 均失败、各 1 单向不一致；p=1、Holm=1 |
| Terra 已知用量 | 60 响应；输入 301,834、完成 36,604（含推理） |
| Terra 传输 | 62 实际派发意图、2 历史未知；另 1 DENY 未派发，不是未知或质量失败 |
| Terra 已知费用分解估算 | $1.790614500；不是最终账单 |
| 未知占用及保守总额 | 两次 $2.187456000；最终客户端总占用 $3.978205500 |
| 预算修订 | 初始 $5；23 任务后发送前拒绝；用户授权 $6 后只补第 24 任务 |
| 最终独立审计 | PASS/COMPLETE；72 XMI、32 字节/身份/任务组；原生评分零差异 |

依据：`E:/54239/Documents/ATLAS_TERRA_SUPPLEMENT/continuation3/run/RESULTS.json`、`BUDGET.jsonl`、`delivery/CURRENT_RESULTS_SUMMARY.json`；`review/continuation3/check_001/terra_independent_audit.json`。最终结果 SHA 为 `a12ada6a49d90da411f371e3331cba0d18bea9308ffde07b7a143d0cfce40a30`，审计 SHA 为 `b72ef371491eb26714047035db0d5fe9024d475d209b9cbe8980769ad26db75c`。主实验表与现有仓库 railway README/重算结果相符。

## 2. 文字修改

### 必须同步的旧仓库说明

1. `ATLAS/docs/EVIDENCE_AND_CLAIMS.md:25` 的 **“Transformation is 67/69/72 of 72.”** 错误。改成：**“The separately reported task-obligation fault-injection cohort T has S/V/F successes of 67/69/72 out of 72 each. It reverses the task-required active state while retaining native-query validity; it is not a model-transformation evaluation.”** 当前附录 D 已正确写成任务义务故障，无需为此改实验。
2. 同处 “139 unique XMI byte sequences” 建议统一为保存验证器实际使用的 **“139 distinct XMI-and-identity byte pairs”**；不要把配对身份遗漏。仓库 railway README 已使用正确口径。
3. `ATLAS/README.md:3` 的 **“No model experiment was rerun to create this release.”** 必须限定为历史离线纠错，而不能覆盖新 Terra：**“Historical experiment outputs remain unchanged. The release additionally includes a completed, separately authorized Terra supplement on the same 24 railway tasks; only that supplement made new model requests.”** 顶部结果表、CHANGE_REGISTER、REVIEWER_EVIDENCE_MAP、verify_release 的轨道/报告映射应增加 Terra 入口，不能把 72 新终点混入原 891 分母。
4. `README.md:35` 关于“manuscript … not edited in this release”应按本次真实内容调整：原整篇论文文件未改与已新增/修订方法、实验、附录章节是不同事实。不要让新章节进入仓库后仍声称完全未写论文材料。
5. `verify_release.py` 当前只运行四个旧轨道。新增 `railway_terra` 后应在选项、Java 检查、统一调度、结果路径和 provenance 中明确该补充；未知 11 次属于历史主实验，Terra 另有 2 次，不能静默合并或覆盖。

### 当前章节的最小建议

当前正文 4.4.2 与附录 D.4 已明确不显著、不能普遍排名、单 seed、输出上限不同和方法策略未完全分离，主体无需重写。建议在附录 D.4 两模型表后补一条，以防读者把条件恢复率当作模型修复能力比较：

> 两模型的初始失败集合不同：Luna 有 18 个失败起点，Terra 有 6 个，仅 4 个任务重合；Luna 中另含一个未形成制品的赋值拒绝。因而，两模型各自失败子集的恢复比例不能用于比较独立修复能力。即使题目相同，各模型生成的初始候选仍不同，本实验没有控制共同损坏制品来检验模型能力与修复效果的关系。

附录 D.2 的“S 以最终合法修订评分”可改为“**S 以最后一个通过修改契约检查并被选中的候选评分，全部原生及任务验收另行执行**”。修改契约检查针对字段、类型、范围及允许编辑边界，不代表模型已满足全部约束。`BAL-1-01` 的 GS 第一轮成功、第二轮回归仍被计为失败，直接证明没有隐藏 best-of-k。其 `BUDGET_EXHAUSTED` 是两轮修改机会用尽，不是美元预算失败。

## 3. 为什么不能推出‘模型越强修复越好’

同 seed 的 Luna：GF 从 6/24 增至 13/24，增加 7 个；Terra：GF 从 18/24 增至 22/24，增加 4 个。Luna 的 7/18（若只讨论可修制品则需另区分那次赋值拒绝）与 Terra 的 4/6，分母来自各自生成过程筛出的不同失败，不能直接比较。成功率更高的初始模型算术上留给修复的增长空间较小，但这不证明其残余错误更难或更容易。

初始失败交集只有 `BAL-1-01`、`BAL-1-02`、`BAL-1-08`、`BAL-2-02`。这四项中两模型 GF 均成功两项；该观察仅用于检查任务身份，不构成新的预定统计或公平修复对照。Terra 的另外两个失败 `BAL-3-06`、`BAL-3-07` 在 Luna 的 G0 中已成功，说明失败集合也不是简单的包含关系。因此可以写“第二模型设置中仍观察到修复增加成功数”，不能写“模型能力增强导致修复更有效”“更强模型剩余失败必然更难”或“第二模型证明跨模型稳健优越性”。

证据：`continuation3/delivery/paired_tasks.csv` 的 24 行任务配对；补充设计只预定 Terra 内部 G0—GF、GS—GF 两个检验。模型间差异、4 项交集和按失败筛选的比例没有确立新的因果对照。

## 4. 现有仓库封装与完整 ZIP 的组成

旧 railway 轨道使用 `archives/railway_evidence_01.zip` 至 `_05.zip`、`PAYLOAD_MANIFEST.json` 与 `review.py`；五个 ZIP 大小分别为 16,810,505、18,894,357、19,896,896、20,070,756、30,136,094 字节。入口使用调用方 Python 与外部 Java 8，按归档及文件 SHA 安全解压，原始数据和 corrected 评分入口分离。顶层 `.gitattributes` 的 `* -text` 保持历史文件字节。

当前 Terra 完整 ZIP：157,646,776 字节、9,434 项；SHA `3382364e8c94a361a496987633c34b8733086d8e074e77bc46f5b069d5e11a7e`。

| 分类 | 文件数 | 未压缩字节 | ZIP 内压缩字节 |
|---|---:|---:|---:|
| 四段证据、源码及其余材料 | 7,984 | 63,775,371 | 16,418,821 |
| Windows Python | 960 | 49,151,046 | 18,796,797 |
| 原生 JAR | 44 | 19,467,522 | 17,506,643 |
| 原封存 JDK | 446 | 199,680,317 | 102,538,223 |

44/44 Terra JAR 的 SHA 已存在于旧 railway/PAYLOAD_MANIFEST，可按字节身份复用。但 **原 EXECUTION_SEAL 的 2,087 文件包含 446 个 JDK 文件及 44 个 JAR**。简单删除 JDK 后调用原审计会失败；也不能篡改旧封印后声称原始全量身份已验证。若采用去重/外部运行时，需要另写明确报告运行时排除的发布适配层，复杂度高于本轮最低风险方案。

## 5. 本轮采纳 root 的最小整合方案

同意将已验证的完整 ZIP 按 **40 MiB 原字节分成四块**，保留全 ZIP SHA，放在新 `experiments/railway_terra/archives/`。它们是字节块，不是四个可独立解压 ZIP；必须按 manifest 顺序重建后再解压。前三块各 41,943,040 字节，第四块 31,817,656 字节，均低于本轮规定的单文件限制。此方案保留全部四段原始证据、全部旧/新封印、两次未知占用、旧 DENY、三项修订及运行时身份，不改任何科学代码。

本轮不额外复制第二份 Python/JDK目录。Git 两分支引用相同分块内容可共享对象；分块本身仍包含既有 JAR 字节，不能声称跨压缩包去除了所有依赖重复。其优势是最小变化、完整保真和离线独立包一致，而不是体积最优。不要同时把原 157 MB ZIP 也加入 Git。

发布入口流程：校验每块大小/偏移/SHA → 顺序重建并核对原完整 ZIP SHA → 拒绝目录穿越、重复/大小写碰撞和符号链接 → 解压到新工作目录 → 用调用方 Python 执行包内 `continuation3/delivery/verify_package.py` → 用调用方 Python、显式外部 Java 8 执行包内 `review/continuation3/verify_final.py --package-root <root> --output <new-output> --java <java8>`。保留每步日志及发布级 REVIEW_RESULT。

**review3 的参数为 `--package-root`，不是 `--root`；也支持 `--java`。** 整条评分/审计链仅使用 Python 标准库和 subprocess Java，没有调用 Windows 专属 API；不需要执行包内 Windows Python/JDK。它们仍被提取用于历史 SHA 验证。可以提供调用方 Python + Java8 的可移植入口，但当前只在 Windows 实测过，不能把代码检查写成 Linux/macOS 已实际验证。

## 6. 草案与发布验收

新草案：`E:/54239/Documents/ATLAS_SYNC_REVIEW/railway_terra_release_draft/review.py`；分块清单草案 `PARTS_MANIFEST.draft.json` 已从原 ZIP 按字节范围只读计算 SHA，没有生成实际分块。root 若采用，复制为 `PARTS_MANIFEST.json`，按清单文件名生成四块，再执行一次完整发布入口检查。不需要再运行模型或改历史数据。

Git 网页可直接展示原字节的设计/协议、结果摘要、报告、配对 CSV、调用 CSV、最终独立审计及核心源码；另附 `SOURCE_VIEW_MANIFEST.json` 映射网页副本到包内位置及 SHA，避免出现两套不同代码。推荐显示 `DESIGN.json`、`run_supplement.py`、`supplement_runtime.py`、`raw_native_score.py`、三次续行入口、`workspace/railway_method_v5/{pipeline,policies,repair_loop,typed_patch}.py`、最终独立审计入口与辅助模块。原位置/开发标识可留在可复核源码和来源路径，章节标题继续使用无开发版本的名称。

发布完成需核对：四块还原 SHA 与上述完整包完全相同；八套证据封印和包清单通过；原生重验 72 XMI/32 组零差异；统计仍为 18/22/22、p=.125/1.0、Holm=.25/1；预算为 60 响应/62 派发/两未知/一 DENY/$3.9782055；源码网页副本 SHA 一致；无 `.env`、真实认证头或 API 配置进入发布。当前完整包的 PRIVATE_DATA_SCAN 两个匹配只是显式无网络测试的合成凭据，没有真实凭据。

root 独占仓库修改、提交及推送。本子任务不修改分支或重新封存原实验。
