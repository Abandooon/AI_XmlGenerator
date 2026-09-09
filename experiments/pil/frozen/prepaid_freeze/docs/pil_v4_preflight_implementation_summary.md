# PIL V4.1 付费运行前修改总结

日期：2026-09-04  
状态：`READY_FOR_PAID_AUTHORIZATION`；英文翻译/法源等价复核、零网络代码审计与预检均已通过，正式付费执行尚未授权，V4.1 外部/付费调用为 0/0

旧 V4 在执行到 132/720 单元时发现 P1/P2 接收的输出契约信息不等，已立即停止。其 136 次逻辑调用完整归档，但全部排除、禁止续跑和择取；V4.1 是修正处理隔离并全面英文化后的新实验身份。

## 1. 人工评审闭环

- C1 第二名独立国际私法评审完成 60/60 事实-only 问卷；
- 两名评审对 4 个分歧案例形成联合共识；
- 对 5 个受影响案例完成双人重确认，返回表哈希为 `5550e771ab515b43ed28dc38418d4b5018090c7f399d1d881a86db525e3f247c`；
- D1 验收为 PASS：4 个工作表、公式和保护内容与冻结空表一致，5/5 双人确认完整；
- gold 来源最终为 51 个一致案例、4 个共识案例、5 个重确认案例。

D1 接受两项本体修复：EUIPO 独立无效申请编码为行政机关权限；Article 30 相关诉讼从 Article 29 同诉因先受理中分离。另有三项事实表述按双人意见修订。V2 原始数据、540 个结果和冻结身份均未改动。

## 2. 新的 V4.1 英文输入

- `data/inference_dataset_v41_en.jsonl`：60 条英文推理专用事实，不含 gold/连接点；
- `data/consensus_gold_v4.jsonl`：60 条双人共识 gold；
- `kb/authoritative_provisions_v41_en.jsonl`：58 条英文、逐条款区分的 instrument-qualified 法规证据及 EUR-Lex 来源；
- `schema/decision_schema_v4.json`：四臂共同模型输出 Schema；
- `schema/consensus_gold_schema_v4.json`：扩展 gold/可接受集合 Schema；
- `rules/delivery_rules_v4.json`：共同交付规则；
- `PIL_V4_ADJUDICATION_RECORD.json` 与 `PIL_D1_ACCEPTANCE.json`：评审来源与重确认接受记录。

现有国际私法研究生评审另完成 60 条英文案例和 58 条英文证据的逐行输入等价复核。54 条案例与 55 条证据直接通过；6 条案例（8、16、47、48、49、50）及 3 条证据（Articles 24(4)、26(1)、31(2)）按意见修订后通过，未决项为 0。完成表 SHA-256 为 `8f10fcb88a5ceb5e696284282687e04ca8820b5d3a0fce6624327e5e8778b5da`，该表只验证翻译/法源等价，不重新决定 gold。

知识库明确区分 Brussels I bis Article 29、30、31，并用法规 ID 区分 Brussels I bis 与 EU Trade Mark Regulation 中同号条文。固定词汇检索采用 top-12，并忽略中英文明确排除子句中的否定关键词。预检对 60/60 案的 gold 必需证据达到至少一项召回；这是运行前资格检查，不是模型结果。

## 3. 实验与执行代码

- P0/P1/P2/P3 采用统一 JSON 语义，分别估计检索、L1、L2+一次修复和整体流水线效应；
- `pil_v4_contract.py` 实现 schema、instrument-qualified 引用、共同审计和 gold 兼容；
- `pil_v4_arms.py` 实现四臂与冻结检索；
- `pil_v4_provider.py` 独立固定 V4 的模型和 AUTOSAR V20 对齐参数：非流式 Chat Completions、`low`、`temperature=1.0`、128000 completion token、180 秒、三组固定 seed、SDK 隐式重试 0 和最多 8 次有记录的瞬时传输继续；不再传递依赖 V2 执行器；
- `pil_v4_schedule.py` 固定 720 单元交错顺序并校验数据和关键实现哈希；
- `pil_v4_run.py` 提供追加式 ledger、基础设施尝试日志、单实例锁和显式付费 token，并在第一次请求前核验冻结的 provider、运行时与端点哈希；
- 运行清单分别累计成功单元与基础设施失败尝试的 input/output/total token、逻辑请求和传输请求；失败单元默认不得隐式重试；
- `pil_v4_rescore.py` 以案例为推断单位给出预定对比及依赖簇敏感性；
- `pil_v4_preflight.py` 生成零调用预检；
- `pil_v4_authorize.py` 只在显式确认后新建独立正式授权，不修改预检；
- `pil_v41_render_prompts.py` 固化 240 份不同的完整英文提示词；
- `pil_v41_prepaid_audit.py` 使用内存 provider 做零网络处理臂/请求载荷故障注入，且代码审计报告进入预检哈希门；
- `pil_v4_retained_diagnostic.py` 只对 55 个事实未变案例做事后连续性诊断，不替代 V4。

## 4. 自检结果

- V4.1 专项：27/27 通过；Workbench：38/38 通过；
- 60 个推理案例、60 个 gold、58 条证据、31 个依赖簇、720 个计划单元全部一致；
- gold Schema 与共同契约：60/60 PASS；
- 必需证据检索缺失：0；
- 推理字段泄漏：0；
- Article 29/30/31 与 EUIPO 标签测试：PASS；
- V4.1 provider/paid 调用：0/0；零网络代码审计：PASS；
- 英文输入一致性复核：60/60 案例、58/58 证据通过，完成表实际哈希与验收记录一致；
- 历史 V2 扩展测试在当前 Python 环境触发冻结运行时指纹漂移并失败关闭；没有为消除该失败而修改 V2 指纹。

## 5. 旧输出的限定诊断

对 55 个事实未变案例，使用锁定的 baseline/RAG 人工文本转录和旧 prism 结构化输出，对 V4 共识 gold 重新计算“结论 + 管辖类型”：

| 臂 | 严格 | 集合兼容 | 单元 |
|---|---:|---:|---:|
| baseline | 57.6% | 75.8% | 165 |
| RAG | 60.6% | 72.1% | 165 |
| old prism | 70.9% | 70.9% | 165 |

严格口径下 old prism 相对 baseline 为 +13.3 pp，案例 bootstrap 95% CI 为 [-5.5, 32.1] pp；集合兼容口径为 -4.8 pp，95% CI 为 [-21.2, 11.5] pp。该结果仍依赖事后口径，且不评价 V4 的统一交付与引用终点，因此只用于解释测量威胁，不能预测或替代 V4 四臂结果。

## 6. 前端与当前硬门

Workbench 只读页面已切换到 `PIL V4.1 preflight`，展示案例数、评审链、英文输入资格、知识库、检索覆盖、代码审计、720 单元、检查通过数和调用数。它只读取并验证预检内容哈希，不能生成授权、schedule 或 provider client。

英文输入等价复核已经完成并通过；零网络代码审计和 65 项相关测试也已通过。当前唯一硬门是新建一个绑定冻结预检、运行时和端点哈希的独立显式付费授权。授权前不生成正式 schedule、不创建正式 ledger、不读取凭证、不发起调用。

## 7. 与当前论文方法边界的对应

PIL V4 只复制 ATLAS 的“统一语义契约 → 解码期结构约束 → 独立后验审计 → 一次有界修复/失败关闭”责任链。它没有复制 AUTOSAR 的确定性 XML 骨架、跨文件引用材料化和深层工件构造，因此论文中应称为“shallow structured-decision replication of the layered constraint/validation sub-contract”，不能称为完整 ATLAS pipeline 的法律域验证。完成 720 单元后，PIL 最多支持本案例集内四个预定组件比较的有效性；不单独支持机制不变性、领域总体外推或普遍跨域泛化。
