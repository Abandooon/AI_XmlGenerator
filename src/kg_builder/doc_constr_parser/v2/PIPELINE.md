# 文档约束 V2 链路

V2 保留旧链路并行运行，所有语义判断均来自人工/助手逐条审阅，不调用项目中的 LLM API。

## 数据分层

1. `work/source_manifest.jsonl`：不可变的原文证据、章节路径、行号、原文哈希和解析状态。
2. `work/semantic_curation.jsonl`：规范性、重要性、核心性、用途、规则类型、可观测性、验证策略和目标提示。
3. `work/binding_decisions.jsonl`：目标到元模型声明、XML 标签、wrapper 和路径的确定性绑定。
4. `constraints_v2.json`：面向检索、验证和修复的发布结构；每条记录保留完整溯源。
5. `generate_formal_constraints/v2/validation_plan.json`：所有 `must_validate=true` 规则的失败闭合执行计划。
6. `llm_generation/knowledge/v2/retrieval_cards.jsonl`：用于 Round2/promote 的紧凑检索卡片。

关键字段：

- `normativity`：mandatory / recommended / optional / informational。
- `importance`：core / major / supporting。
- `is_core`：是否属于生成与验证的核心不变量。
- `usages`：generation_context / automatic_validation / repair_guidance / human_review / documentation。
- `rule_family`：类型兼容、基数、引用完整性、互斥、条件存在等。
- `observability`：full / partial / none。
- `policy`：must / should / optional / manual / not_applicable。
- `must_validate`：是否必须进入验证计划；该字段与“是否已有执行器”分离。

## 失败闭合语义

- `PASS`：规则适用且检查完成，未发现违反；或当前输入中没有该规则的适用对象。
- `FAIL`：发现可复现的违反。
- `NOT_EVALUATED`：规则适用，但执行器、引用范围或外部能力不完整。
- `ERROR`：解析器或执行器异常。

只要任一 `must` 规则适用但为 `NOT_EVALUATED`，总结果就是 `INCOMPLETE`，不会被当作通过。

## 全量重建

在项目根目录执行：

```powershell
.\.venv\Scripts\python.exe -B src\generate_formal_constraints\v2\run_pipeline.py
.\.venv\Scripts\python.exe -B -m unittest discover -s tests_v2 -v
```

重建程序依次执行原文抽取与校验、语义批次展开、目标净化与绑定、验证计划编译、结构化发布、检索卡生成和全链路一致性审计。最终审计见 `src/generate_formal_constraints/v2/pipeline_audit.json`。

## Round2/promote 检索

V2 检索不再按“某个类链接的前 N 条”截断。它先对全体候选按以下证据评分，再应用总量和规则族配额：

1. 精确 XML 路径；
2. 属性标签；
3. 类标签；
4. 当前用途；
5. must/core/major 权重；
6. Round1 需求文本词项。

Round2 对接口和每个组件分别查询，默认注入 20/24 条约束，并在提示词中携带约束 ID、策略、重要性、规则族、摘要和目标。未命中的可选结构不会仅为满足约束而被生成。

## 当前基线

- 原文与发布记录：1085 / 1085。
- `must_validate`：554。
- 已实现 Python 语义规则：400。
- 已审查并实现的 typed DSL 规则：154。
- 计划中规则：0。
- 依赖运行时、部署、外部证据或生成意图的人工审查项：51。
- 核心目标绑定缺口：0。

缺少生成意图、精确目标、参数、完整引用范围或外部证据时，规则必须返回
`NOT_EVALUATED` 并使结果保持 `INCOMPLETE`，不得静默通过。
