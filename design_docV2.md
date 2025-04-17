### 更新后的顶层项目目录  

```text
autosar_generator_project/
├─ config/
│   ├─ config.yaml              # 新增 llm.backend、constraint_graph 段
│   └─ logging.yaml
├─ data/
│   ├─ schemas/                 # AUTOSAR XSD
│   ├─ rules/                   # 原始 Drools 规则
│   ├─ constraint_graph/        # ⇦ 新增：生成的 autosar.graphml 缓存
│   ├─ shacl/                   # ⇦ 新增：autosar_shapes.ttl（CG→SHACL）
│   └─ …                        # requirements/ metamodel/ 等原有子目录
├─ docker/
│   └─ vllm_openai.Dockerfile   # ⇦ 新增：自托管 vLLM 镜像
├─ src/
│   ├─ nlp/
│   ├─ kg_builder/
│   ├─ constraint_graph/        # ⇦ **整块新增**
│   │   ├─ builder.py           # XSD+Drools+KG → CG+SHACL
│   │   ├─ graph.py             # next_valid_tokens / is_valid
│   │   ├─ fsm.py               # FSM 压缩实现
│   │   └─ utils.py
│   ├─ kg_query/
│   ├─ llm_interaction/
│   │   ├─ base.py
│   │   ├─ openai_client.py
│   │   └─ selfhost_client.py   # ⇦ 新增：vLLM/TGI 封装
│   ├─ generation_pipeline/
│   │   ├─ cg_decoder.py        # ⇦ 新增：token‑level CGD
│   │   ├─ ilp_reranker.py      # ⇦ 新增：span‑level CGD
│   │   └─ generators.py        # 加入 CGDGenerator
│   ├─ validation/
│   │   ├─ xsd_validator.py
│   │   ├─ drools_validator.py
│   │   └─ shacl_validator.py   # ⇦ 新增：pySHACL 校验
│   ├─ utils/
│   │   ├─ llm_factory.py       # ⇦ 新增：热切换 LLM backend
│   │   └─ file_io.py …         # 其他原有工具
│   └─ tests/
│       ├─ test_constraint_graph.py   # ⇦ 新增单元测试
│       └─ test_cg_decoder.py         # ⇦ 新增单元测试
├─ experiments/
│   ├─ run_experiment.py
│   └─ metrics/
│       └─ info_bottleneck.py   # ⇦ 新增 ΔH 熵减评估
└─ README.md
```

#### 新增/修改要点一览
| 位置 | 目的 |
|------|------|
| **constraint_graph/** | 统一存放 CG 构建与查询逻辑；输出 GraphML & SHACL。 |
| **docker/** | 提供 `vllm_openai.Dockerfile`，一键部署自托管 LLM 服务。 |
| **llm_interaction/selfhost_client.py** | 让代码可调用本地 vLLM/TGI，接口与 OpenAI 保持一致。 |
| **generation_pipeline/cg_decoder.py** | 在自托管模式下注入 `prefix_allowed_tokens_fn` 实现硬 CGD。 |
| **generation_pipeline/ilp_reranker.py** | 在 API 模式下对 n‑best 候选做约束可行性重排。 |
| **validation/shacl_validator.py** | 用 pySHACL 校验 CG→SHACL 形约，形成第三层验证。 |
| **utils/llm_factory.py** | 根据 `config.llm.backend` 返回 OpenAI 或 SelfHost 客户端，实现“热切换”。 |
| **data/constraint_graph/, data/shacl/** | 缓存 CG 结果与 SHACL shapes，避免重复建图。 |
| **experiments/metrics/info_bottleneck.py** | 统计检索‑增强前后 NLL，计算 ΔH 熵减。 |
| **tests/** | 新增针对 CG 与 CGD 的单元测试脚本。 |

> **总结**：在原目录基础上主要 **增了 7 个功能子目录/文件**，并扩充 `config` 与 `validation`，以支持 **统一约束层、强/弱 CGD 解码、自托管 LLM、SHACL 校验** 等新特性。其它原有结构与接口保持兼容。

# 项目设计文档 V2 （完整版）

> **Project Title:** Constraint‑Graph Enhanced, Knowledge‑Graph Driven AUTOSAR XML Generator  
> **Revision:** 2025‑04‑17  
> 本版在 V1 基础上融入 **统一约束层 (CG+SHACL)、约束引导解码 (CGD)、自托管 LLM 服务、热插拔 LLMClient 抽象、CI/CD** 等改动。新增内容处已消除 “➡️” 标识，形成最终定稿。

---

## 目录
1. 项目概述  
2. 核心技术栈  
3. 顶层目录结构  
4. 配置文件约定  
5. 数据分区说明  
6. 详细模块设计  
   6.1 NLP  
   6.2 知识图谱构建 (`kg_builder`)  
   6.3 统一约束层 (`constraint_graph`)  
   6.4 KG 查询 (`kg_query`)  
   6.5 LLM 交互层 (`llm_interaction`)  
   6.6 验证层 (`validation`)  
   6.7 生成流程 (`generation_pipeline`)  
   6.8 工具库 (`utils`)  
7. 运行流程  
8. 实验与评估设计  
9. CI/CD & 部署  
10. 里程碑  
11. 附录（SHACL 示例、Drools 模板、术语表）

---

## 1 项目概述
本框架根据自然语言需求生成符合 AUTOSAR 标准的 ARXML。  
**V2 新增特色：**

* **Constraint Graph (CG)**：将 XSD 基数、Drools 语义和 KG 规则统一成图形约束。  
* **CGD**：在解码时用 FSM/ILP 动态过滤非法 token，显著减少后置修复。  
* **SHACL 形约**：由 CG 自动导出，做轻量图态校验。  
* **双运行模式**：Phase‑A（OpenAI API + 弱 CGD）；Phase‑B（自托管 vLLM + 强 CGD）。

---

## 2 核心技术栈
| 层次 | 技术 | 说明 |
|------|------|------|
| NLP | spaCy、SciBERT | 需求解析、实体/关系抽取 |
| KG 存储 | Neo4j（生产），rdflib+GraphML（开发） | 双模式 |
| 统一约束 | networkx、pySHACL | CG 构建 & SHACL 验证 |
| 规则引擎 | Drools 7.x | REST KIE‑Server |
| LLM API | OpenAI GPT‑4‑o | Phase‑A |
| 自托管 LLM | vLLM + Llama‑3‑8B‑Instruct | Phase‑B，`--serve-openai` |
| 解码约束 | `prefix_allowed_tokens_fn`、pulp(ILP) | token‑level / span‑level |
| DevOps | Docker Compose、GitHub Actions、k8s HPA | 一键部署 |

---

## 3 顶层目录结构
```text
project_root/
├─ config/
│  ├─ config.yaml
│  └─ logging.yaml
├─ data/
│  ├─ schemas/               # XSD
│  ├─ rules/                 # Drools DRL
│  ├─ constraint_graph/      # autosar.graphml
│  ├─ shacl/                 # autosar_shapes.ttl
│  └─ …
├─ docker/
│  └─ vllm_openai.Dockerfile
├─ src/
│  ├─ nlp/
│  ├─ kg_builder/
│  ├─ constraint_graph/
│  ├─ kg_query/
│  ├─ llm_interaction/
│  ├─ generation_pipeline/
│  ├─ validation/
│  ├─ utils/
│  └─ …
└─ experiments/
```

---

## 4 配置文件约定
`config/config.yaml` 关键片段：
```yaml
llm:
  backend: openai        # openai | selfhost
  base_url: https://api.openai.com/v1
  api_key: ${OPENAI_KEY}
  decoder: cgd           # naive | xsd | full | cgd
constraint_graph:
  xsd_path: data/schemas/autosar.xsd
  drools_dir: data/rules/
  kg_endpoint: bolt://localhost:7687
  cache: data/constraint_graph/autosar.graphml
```

---

## 5 数据分区说明
| 目录 | 内容 | 生成方式 |
|------|------|----------|
| `constraint_graph/` | `autosar.graphml` | `CGBuilder.build()` |
| `shacl/` | `autosar_shapes.ttl` | 同步导出 |
| `rules/generated/` | *.drl | Jinja2 渲染模板 |

## 6 详细模块设计

### 6.1 NLP 模块 `src/nlp/`

| 组件 | 功能 | 关键实现 |
|------|------|----------|
| `processor.py` | `NLProcessor.parse(text)` → {intent, entities, attrs} | spaCy 流水线：Tokenizer → NER(微调 SciBERT) → 自定义意图分类 |
| `terminology.py` | AUTOSAR 术语词典、简称映射 | 从 KG 抽“label/altLabel” 构建 |
| `patterns/` | 规则抽取正则 | 维护 `yaml`，在 CI 做覆盖率测试 |

> **输出格式**  
> ```jsonc
> {
>   "intent": "create_swc",
>   "entities": [
>     {"text":"SpeedSensor","type":"SwcShortName"},
>     {"text":"uint16","type":"DataType"}
>   ],
>   "attrs": {"period_ms": 10}
> }
> ```

---

### 6.2 知识图谱构建 `src/kg_builder/`

#### 6.2.1 `uml_metadata_parser.py`
* 解析 `.xsd/.xmi` → `elements.json`
* 补充字段：`uri`, `relType`, `valueDomain`, `ocl`, `autosar_release`

#### 6.2.2 `doc_processor.py`
* 基于 LLM + 手工规则抽取约束：
  * **实体**：SwcInternalBehavior、RunnableEntity …
  * **关系**：`mustHave`, `prohibits`, `minCardinality`
  * **约束**：自然语句 → 结构化表达式

#### 6.2.3 `constraint_graph_exporter.py`
```python
class CGBuilder:
    def build(cfg):
        xsd_nodes = XSDParser(cfg.xsd_path).to_occurrence_shapes()
        drools = DroolsParser(cfg.drools_dir).lhs_to_graph()
        kg_sem = KGQuery(cfg.kg_endpoint).extract_semantic_rules()
        G = merge_graphs(xsd_nodes, drools, kg_sem)
        nx.write_graphml(G, cfg.cache)
        export_shacl(G, "data/shacl/autosar_shapes.ttl")
        return G
```

---

### 6.3 统一约束层 `src/constraint_graph/`

| 文件 | 责任 |
|------|------|
| `builder.py` | 读取 XSD/Drools/KG → 输出 `.graphml` + `.ttl` |
| `graph.py` | `next_valid_tokens`, `is_valid(xml)`, `report(xml)` |
| `fsm.py` | 图 → 有限状态机 (trie 压缩) |
| `utils.py` | `xml2rdf`, `rdf2xml`（验证转换） |

---

### 6.4 KG 查询模块 `src/kg_query/`

* 维持 `KGQuerier.query(cypher|sparql)`  
* 新增 `KGQuerier.value_domain(node_uri, prop)` — 供 CG 值域编码

---

### 6.5 LLM 交互层 `src/llm_interaction/`

| 类 | 说明 |
|----|------|
| `base.LLMClient` | 统一 `generate()` / `stream_generate()`；记录 metrics |
| `openai_client.py` | 调用 `/v1/chat/completions` |
| `selfhost_client.py` | 调用自托管 vLLM/TGI，同路径同参数 |
| `prompt_formatter.py` | 3 策略：plain, kg_enhanced, repair |
| `schemas/` | JSON‑schema 与 function‑calling 描述，服务骨架‑填充策略 |

---

### 6.6 验证层 `src/validation/`

| 组件 | 输入 | 输出 | 关键依赖 |
|------|------|------|----------|
| `xsd_validator.py` | xml, xsd | pass?, errors | lxml |
| `shacl_validator.py` | rdf, shapes.ttl | pass?, report | pyshacl |
| `drools_validator.py` | facts.json | pass?, violations | KIE‑Server REST |
| `validator_hub.py` | xml | 统一返回三层结果 | 组合前 3 者 |

---

### 6.7 生成流程 `src/generation_pipeline/`

```python
class CGDGenerator(BaseGenerator):
    def generate(self, nl_text):
        ctx = self.kgq.retrieve_context(nl_text)
        prompt = formatter.kg_enhanced(nl_text, ctx)
        if self.cfg.llm.backend == "selfhost":
            xml = self.llm.generate(prompt, temperature=0.4,
                                    prefix_allowed_tokens_fn=cg_decoder.allowed)
        else:                               # API 路径
            skel = self.llm.generate(prompt_skeleton(nl_text))[0]
            xmls = self.llm.generate(prompt_fill(nl_text, skel), n=20)
            xml = ilp_reranker.pick_valid(xmls)
        ok, errs = validator_hub.validate(xml)
        if not ok and self.cfg.allow_repair:
            xml = self.repair(xml, errs)
        return xml, errs
```

* **cg_decoder.py**：包装 `ConstraintGraph.next_valid_tokens`  
* **ilp_reranker.py**：MILP 目标 `max Σ_i logP_i x_i ` s.t. 约束可行

---

### 6.8 工具库 `src/utils/`

* `llm_factory.py` — 根据 `cfg.llm.backend` 返回正确 LLMClient  
* `file_io.py` — 同 V1  
* `logging_config.py` — 加流式 & 文件 handler；按 run‑id 分目录  
* `metrics.py` — 解析生成日志，输出 csv / Prometheus pushgateway


## 7 运行流程

> 对应 `main.py → run_experiment.py`

1. **启动 & 参数解析**  
   `python main.py --config config/config.yaml`

2. **日志初始化**  
   `utils.logging_config.setup()`

3. **加载配置**  
   `cfg = file_io.load_yaml()`

4. **组件初始化**  
   * `NLProcessor`  
   * `CG = CGBuilder.load_or_build(cfg.constraint_graph)`  
   * `ValidatorHub`(XSD, SHACL, Drools)  
   * `LLM = llm_factory.build_llm_client(cfg.llm)`  
   * `Generator = CGDGenerator(cfg, NLProcessor, LLM, CG, ValidatorHub)`

5. **数据集遍历**  
   对每条需求 `req.txt`：  
   1. `parse_result = nlp.parse(req)`  
   2. `xml, errs = Generator.generate(req)`  
   3. 记录 metrics（XSD pass?, Drools pass?, CG‑Violate, ΔH …）

6. **结果汇总 & 报告**  
   DataFrame → `results/reports/summary.csv`  
   生成图表 (Seaborn) 存 `reports/plots/`

---

## 8 实验与评估设计

| 类别 | 指标 | 描述 |
|------|------|------|
| 合规性 | **XSD_Pass%**, **Drools_Pass%**, **SHACL_Pass%**, **CG_Violate_Rate** | 四层约束 |
| 经济性 | AvgTokens, API_Cost (USD) | `LLMClient` 记录 |
| 效率 | Backtrack_Cnt, ILP_Time (ms) | 输出自 cg_decoder / ilp_reranker |
| 质量 | BLEU, Tree Edit Distance, Similarity_to_GT | 若有黄金真值 |
| 熵减 | **ΔH (k‑nat)** | `experiments/metrics/info_bottleneck.py` |

统计显著性：`scipy.stats.ttest_rel` 对比 Baseline vs CGD。

---

## 9 CI/CD & 部署

### 9.1 GitHub Actions

```yaml
name: CI
on: [push, pull_request]
jobs:
  unit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r requirements.txt
      - run: pytest -q
  e2e-openai:
    env: { LLM_BACKEND: openai, OPENAI_KEY: ${{secrets.OPENAI_KEY}} }
    steps:
      - run: python main.py --quick_test
  e2e-selfhost:
    services:
      vllm: { image: vllm/vllm-openai:latest, ports: [8000:8000] }
    env: { LLM_BACKEND: selfhost, LLM_BASE_URL: http://localhost:8000/v1, LLM_API_KEY: dummy }
    steps:
      - run: python main.py --quick_test
```

### 9.2 Docker Compose (自托管)

```yaml
services:
  llm:
    build: ./docker
    ports: [8000:8000]
    environment:
      - MODEL=/models/llama-3-8b
      - SERVE_OPENAI=1
    deploy:
      resources:
        reservations:
          devices: [{capabilities: [gpu]}]
    healthcheck: {test: curl -f http://llm:8000/v1/models, interval: 30s}

  generator:
    build: .
    depends_on: [llm]
    environment:
      - LLM_BACKEND=selfhost
      - LLM_BASE_URL=http://llm:8000/v1
      - LLM_API_KEY=dummy
```

k8s HPA：根据 GPU_util ≥ 70% 扩 1→N 副本。

---

## 10 里程碑

| 阶段 | 时间 (2025) | 交付物 |
|------|------------|---------|
| **M1** | 05 月 | API 弱 CGD、指标脚本、CI unit pass |
| **M2** | 06 月 | 完整 ConstraintGraph、SHACL 导出、自动 Drools 模板 |
| **M3** | 07 月 | vLLM 服务、强 CGD、k8s Helm Chart |
| **M4** | 08 月 | 论文提交、GitHub 发布 (MIT) |

---

## 11 附录

### 11.1 SHACL 片段

```turtle
ex:SwcInternalBehaviorShape a sh:NodeShape ;
  sh:targetClass autosar:SwcInternalBehavior ;
  sh:property [
      sh:path autosar:runnable ;
      sh:minCount 1 ;
  ] .
```

### 11.2 Drools 模板 `occurrence_rule.ftl`

```freemarker
rule "${id}"
when
  $x : ${class}( ${field}.size ${op} ${value} )
then
  insertLogical(new Violation("${severity}", "${message}", $x));
end
```

### 11.3 术语表 (节选)

| 缩写 | 解释 |
|------|------|
| CG | Constraint Graph |
| CGD | Constraint‑Guided Decoding |
| SHACL | Shapes Constraint Language |
| RAG | Retrieval‑Augmented Generation |
| TED | Tree Edit Distance |

