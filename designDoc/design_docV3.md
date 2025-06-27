# 项目设计文档 V3 （完整版）

> **Project Title:** High-Precision AUTOSAR Specification and Constraint Extraction with Multidimensional Annotation, Multimodal Input, and Human-Reviewed ARXML Generation
> **Revision:** 2025-05-20
> 本版在 V2 基础上，**重点重构了知识图谱构建模块 (`kg_builder`)**，采用基于多维人工标注和严格上下文约束的策略（源自 `design_docV4.md` 的思路）以实现高精度的规范与约束抽取，并整合了多模态信息提取。同时，保留并细化了**人工审核与修改模块**作为最终 ARXML 质量保障的关键环节。

---

## 目录
1.  项目概述
2.  核心技术栈
3.  顶层目录结构
4.  配置文件约定
5.  数据分区说明
6.  详细模块设计
    6.1 NLP (*辅助角色*)
    6.2 **知识图谱构建与规范抽取 (`kg_builder`)** (*核心重构*)
        6.2.1 人工预处理与多维标注指南
        6.2.2 上下文注入预处理 (`context_injector.py`)
        6.2.3 LLM 约束抽取 (`llm_extractor.py`)
        6.2.4 多模态信息提取 (`multimodal_processor.py`)
        6.2.5 Linker 与校验 (`linker_validator.py`)
        6.2.6 约束数据模型与 Schema
        6.2.7 处理层级约束 (`#@Hierarchical`)
        6.2.8 约束图谱导出器 (`constraint_graph_exporter.py`)
    6.3 统一约束层 (`constraint_graph`)
    6.4 KG 查询 (`kg_query`)
    6.5 LLM 交互层 (`llm_interaction` - *主要用于生成*)
    6.6 验证层 (`validation`)
    6.7 生成流程 (`generation_pipeline`)
    6.8 工具库 (`utils`)
    6.9 人工审核与修改模块 (`human_review/`, `web_reviewer/`)
7.  运行流程
8.  实验与评估设计 (含规范抽取质量指标)
9.  CI/CD & 部署
10. 里程碑
11. 附录

---

## 1 项目概述
本框架旨在实现两大核心目标：
1.  **高精度规范与约束抽取**：从 AUTOSAR 相关文档（Markdown/纯文本，辅以多模态信息）中自动抽取结构化的规范 (TPS) 和约束 (constr) 信息，并将其链接到标准的 UML 元模型及枚举定义。此过程引入多维人工标注体系，并对上下文注入和 LLM 行为施加严格约束。
2.  **约束感知的 ARXML 生成与审核**：基于抽取的知识和约束，根据自然语言需求生成符合 AUTOSAR 标准的 ARXML，并提供人工审核与修改界面，确保最终输出的最高质量。

**V3 核心特性：**
*   **`kg_builder` 重构**：采用 `design_docV4.md` 的精细化信息抽取流程。
*   **多维人工标注**：`#@CLASS`, `#@ENUM`, `#@SECTION`, `#@Hierarchical` 指导抽取。
*   **严格上下文注入**：LLM 操作基于从元数据注入的精确上下文。
*   **多模态信息提取**：补充文本信息，丰富知识源。
*   **人工审核闭环**：对生成的 ARXML 进行专家级复核与修正。

---

## 2 核心技术栈
| 层次         | 技术                                       | 说明                                                                 |
|--------------|--------------------------------------------|----------------------------------------------------------------------|
| **规范抽取** | **Python, LLM (GPT-4o-mini or stronger)**  | **(核心)** 文本处理，上下文管理，基于Schema的LLM调用                     |
| NLP          | spaCy、SciBERT                             | (可选) 辅助预处理或复杂文本理解                                        |
| 多模态处理   | OpenAI GPT-4V, Google Gemini (Vision)      | 图表、图片内容理解与信息提取                                             |
| KG 存储      | Neo4j（生产），rdflib+GraphML（开发）        | (下游) 存储抽取的规范/约束及生成的CG                                   |
| 统一约束     | networkx、pySHACL                          | CG 构建 & SHACL 验证 (基于 `kg_builder` 输出)                            |
| 规则引擎     | Drools 7.x                                 | REST KIE-Server (基于 `kg_builder` 输出)                               |
| LLM API (生成)| OpenAI GPT-4-o                             | Phase-A ARXML 生成                                                     |
| 自托管 LLM(生成)| vLLM + Llama-3-8B-Instruct                 | Phase-B ARXML 生成                                                     |
| 解码约束     | `prefix_allowed_tokens_fn`、pulp(ILP)      | token-level / span-level ARXML 生成约束                                |
| ARXML对象模型 | JAXB (Java)                                | ARXML 与 Java 对象双向绑定 (人工审核模块)                                |
| Web后端      | Spring Boot (Java) / Flask (Python)        | 为人工审核界面提供 API 服务                                                |
| Web前端      | React / Vue / Angular                      | 人工审核与修改的用户界面                                                 |
| DevOps       | Docker Compose、GitHub Actions、k8s HPA    | 一键部署                                                                 |

---

## 3 顶层目录结构
### 更新后的顶层项目目录 (V3 概览)

autosar_generator_project/
├─ config/
│   ├─ config.yaml
│   └─ logging.yaml
├─ data/
│   ├─ input_docs/              # ⬅️ 新增：存放待处理的原始 AUTOSAR 文档 (md, txt)
│   ├─ preprocessed_docs/       # ⬅️ 新增：存放经过人工标注和上下文注入的文档块
│   ├─ schemas/                 # AUTOSAR XSD
│   ├─ rules/                   # 原始 Drools 规则
│   ├─ constraint_graph/        # 生成的 autosar.graphml 缓存
│   ├─ shacl/                   # autosar_shapes.ttl（CG→SHACL）
│   ├─ multimodal_inputs/       # 从文档中提取出的图表、图片等
│   ├─ unified_metadata.json    # 核心元数据文件 (类、属性、枚举、字面量)
│   └─ extraction_schemas/      # ⬅️ 新增：存放LLM抽取任务的JSON Schema (如 extraction_schema.json)
├─ docker/
│   └─ vllm_openai.Dockerfile
├─ src/
│   ├─ nlp/                     # (可能部分功能被kg_builder中的LLM替代或辅助)
│   ├─ kg_builder/              # 核心：文档解析、多维标注、上下文注入、LLM抽取、校验、多模态处理
│   │   ├─ annotator_guidelines.md # ⬅️ 新增：人工标注规范文档
│   │   ├─ context_injector.py  # 对应 V4 的 context_injector_v4.py
│   │   ├─ llm_extractor.py     # 对应 V4 的 llm_batch_extract_v4.py
│   │   ├─ linker_validator.py  # 对应 V4 的 linker_validator_v4.py
│   │   ├─ multimodal_processor.py # 多模态信息提取
│   │   └─ constraint_graph_exporter.py # (消费 linker_validator.py 的输出)
│   ├─ constraint_graph/
│   ├─ kg_query/
│   ├─ llm_interaction/         # (主要服务于生成流程，kg_builder中的LLM交互可能更专用)
│   ├─ generation_pipeline/
│   ├─ validation/              # (XSD, Drools, SHACL 验证器)
│   ├─ human_review/            # 人工审核核心后端逻辑
│   │   ├─ arxml_transformer.py
│   │   ├─ review_service.py
│   │   └─ change_tracker.py
│   ├─ utils/
│   │   ├─ llm_factory.py
│   │   ├─ jaxb_bridge.py
│   │   └─ file_io.py …
│   └─ tests/
│       ├─ test_kg_builder.py     # ⬅️ 新增：针对 kg_builder 各阶段的单元测试
│       ├─ test_human_review.py
│       └─ …
├─ web_reviewer/                # Web UI 前后端 (人工审核界面)
│   ├─ backend/
│   └─ frontend/
├─ experiments/
└─ README.md
---

## 4 配置文件约定
`config/config.yaml` 可能新增/修改片段：
```yaml
kg_builder:
  llm_model_extraction: "gpt-4o-mini" # 用于规范抽取的LLM
  llm_temperature_extraction: 0.0
  input_docs_path: "data/input_docs/"
  preprocessed_docs_path: "data/preprocessed_docs/"
  unified_metadata_path: "data/unified_metadata.json"
  extraction_schema_path: "data/extraction_schemas/extraction_schema.json"
  output_constraints_linked_path: "data/constraints_linked.json" # kg_builder的最终输出
  # ... multimodal_kg, human_review (同上一版V3草稿)
```

---

## 5 数据分区说明
| 目录                     | 内容                                                       | 生成方式/来源                                  |
|--------------------------|------------------------------------------------------------|----------------------------------------------|
| `input_docs/`            | 原始 AUTOSAR 文档 (md, txt)                                  | 人工提供                                       |
| `preprocessed_docs/`     | 经过人工标注和上下文注入的文档块                               | `kg_builder/context_injector.py`               |
| `unified_metadata.json`  | 类、属性、枚举、字面量的元数据定义                             | 外部提供/预处理生成                            |
| `extraction_schemas/`    | LLM 抽取任务的 JSON Schema                                   | 开发定义                                       |
| `constraints_linked.json`| `kg_builder` 最终输出的结构化规范/约束数据                   | `kg_builder/linker_validator.py`             |
| `multimodal_inputs/`     | 从文档中提取的图片/图表文件                                  | 手动或脚本从原始需求文档中分离                 |
| `constraint_graph/`      | `autosar.graphml` (基于 `constraints_linked.json` 构建)      | `kg_builder/constraint_graph_exporter.py`    |
| `shacl/`                 | `autosar_shapes.ttl`                                       | 同步导出自 CG                                  |
| ...                      | (其他同上一版V3草稿)                                         |                                              |

---

## 6 详细模块设计

### 6.1 NLP 模块 `src/nlp/`
*   **角色调整：** 在 V3 中，对于规范抽取任务，其核心功能（如实体识别、关系抽取）大部分被 `kg_builder` 中基于 LLM 和严格上下文的流程所取代或增强。
*   **可能用途：**
    *   对 `data/input_docs/` 进行初步的文本清洗、句子分割。
    *   辅助识别文档中可能需要人工添加 `#@CLASS` 或 `#@ENUM` 标注的区域。
    *   在 ARXML 生成流程中，解析用户输入的自然语言需求（此部分功能保留 V2 设计）。

### 6.2 知识图谱构建与规范抽取 (`src/kg_builder/`) (*核心重构*)
此模块负责从 AUTOSAR 文档中高精度地抽取结构化的规范和约束信息，并整合多模态内容。

#### 6.2.1 人工预处理与多维标注指南 (`src/kg_builder/annotator_guidelines.md`)
*   **内容：** 详细描述 `design_docV4.md` 中定义的标注类型 (`#@SECTION`, `#@CLASS`, `#@ENUM`, `#@Hierarchical`) 的目的、样式、示例和标注原则。
*   **目的：** 确保领域专家标注的一致性和准确性，为后续自动化流程提供高质量输入。
*   **存储：** 作为一个 Markdown 文件，供标注人员参考。

#### 6.2.2 上下文注入预处理 (`src/kg_builder/context_injector.py`)
*   **输入：**
    *   经过人工标注的 Markdown/纯文本文档 (来自 `data/input_docs/`)。
    *   `data/unified_metadata.json`。
*   **步骤：**
    1.  **文档分块与标注解析：** (同 `design_docV4.md` 3.1.1)
    2.  **元数据提取：** (同 `design_docV4.md` 3.1.2) 为块内及小范围上下文的 `#@CLASS` 和 `#@ENUM` 提取属性和字面量。
    3.  **上下文注入：** (同 `design_docV4.md` 3.1.3) 为每个文档块动态生成包含章节、相关类属性、相关枚举字面量的上下文描述文本。
*   **输出：** 增强后的文档块列表 (存入 `data/preprocessed_docs/`)。

#### 6.2.3 LLM 约束抽取 (`src/kg_builder/llm_extractor.py`)
*   **输入：** 增强后的文档块列表 (来自 `data/preprocessed_docs/`)。
*   **核心LLM Prompt指令：** (严格遵循 `design_docV4.md` 3.2 中的指令)
    *   强调从特定格式 `[ID_TYPE_ID_NUMBER] Title (cid:100) Details (cid:99)(References)` 抽取。
    *   ID与类型 (`id`, `id_type`) 的提取。
    *   标题 (`title`) 与细则 (`expression`) 的提取。
    *   引用 (`references`) 的提取。
    *   **严格的目标实体确定：** 基于紧邻的 `#@CLASS`/`#@ENUM` 标注。
    *   **严格的目标属性/字面量确定：** 必须在注入的上下文中存在，否则置为 `_classLevel` / `_enumLevel`。**禁止推测。**
    *   层级关系 (`parent_id`) 的初步识别（基于 `#@Hierarchical`）。
    *   其他字段 (`constraint_type`, `value`)。
*   **Function Calling Schema：** 使用 `data/extraction_schemas/extraction_schema.json` (见 6.2.6)。
*   **API 调用：** 模型 `gpt-4o-mini` (或配置中指定)，`temperature=0.0`。
*   **输出：** 原始 LLM 抽取结果列表 (JSON Lines格式，例如 `constraints_raw.jsonl`)。

#### 6.2.4 多模态信息提取 (`src/kg_builder/multimodal_processor.py`)
*   **目的：** 从文档中的图片、图表（存储在 `data/multimodal_inputs/`）提取结构化信息，对齐到 AUTOSAR 元模型，作为对文本信息的补充。
*   **输入：**
    *   图片/图表文件路径 (可能由 `context_injector.py` 在处理文档时识别并传递)。
    *   相关的文本上下文（如图表标题、引用该图表的段落）。
    *   `data/unified_metadata.json`。
*   **流程：**
    1.  调用多模态 LLM (如 GPT-4V API) 或专用视觉模型分析图片/图表。
    2.  提取关键视觉元素、元素间的连接关系、图内文本标签等。
    3.  尝试将提取的视觉信息映射到 AUTOSAR 元模型概念（如组件、端口、连接器、状态、转换等）。此步骤可能需要复杂的逻辑，结合文本上下文和元数据进行。
    4.  输出结构化数据，其格式应尽量与 `llm_extractor.py` 的输出兼容或可合并，包含 `id` (可自生成或与引用文本关联), `title` (图表标题), `targetClass`/`targetEnum`, `expression` (对图表内容的描述或提取的规则), `references` 等。
*   **输出：** 结构化的多模态信息列表，供 `linker_validator.py` 合并处理。

#### 6.2.5 Linker 与校验 (`src/kg_builder/linker_validator.py`)
*   **输入：**
    *   `llm_extractor.py` 输出的原始文本抽取结果 (`constraints_raw.jsonl`)。
    *   `multimodal_processor.py` 输出的结构化多模态信息列表。
    *   `data/unified_metadata.json`。
*   **步骤：**
    1.  **合并输入：** 将文本抽取结果和多模态抽取结果合并为一个待处理列表。
    2.  **解析与组合 `targetRef`：** (同 `design_docV4.md` 3.3.1)
    3.  **UML元数据校验：** (同 `design_docV4.md` 3.3.2) 包括实体存在性、属性/字面量存在性 (LLM遵循性校验)、类型兼容性。
    4.  **ID类型与格式校验：** (同 `design_docV4.md` 3.3.3)
    5.  **层级关系校验：** (同 `design_docV4.md` 3.3.4)
    6.  **引用校验：** 校验 `references` 列表中的 ID 是否存在于已处理的集合中或已知的规范ID库中。
    7.  **数据清洗与规范化：** 例如，统一日期格式、去除不必要的空白等。
    8.  **置信度评估/调整。**
*   **输出：**
    *   最终链接和校验后的结构化规范/约束列表 (`data/constraints_linked.json`)。
    *   需要人工复核的条目队列 (`data/review_queue_kg.csv`)，例如校验失败或低置信度的条目。

#### 6.2.5.1 人工复核结构化约束

#### 6.2.6 约束数据模型与 Schema (`data/extraction_schemas/extraction_schema.json`)
*   **内容：** (采用 `design_docV4.md` 第4节中的 `schema_v4.json` 定义)
    *   包含 `id`, `id_type`, `title`, `targetClass`, `targetEnum`, `targetAttribute`, `targetRef`, `expression`, `references`, `constraint_type`, `value`, `scope` (内含 `section`, `parent_id`), `rawSourceText`, `confidence` 等字段。
*   **作用：** 作为 LLM Function Calling 的 Schema，确保 LLM 输出的结构化。

#### 6.2.7 处理层级约束 (`#@Hierarchical`)
*   **标注：** 由人工在 `data/input_docs/` 中添加。
*   **LLM 抽取 (`llm_extractor.py`)：** 当遇到 `#@Hierarchical`，尝试将当前约束的 `parent_id` 设为前一个抽取的非层级约束的 `id`。
*   **Linker/Validator (`linker_validator.py`)：** 验证 `parent_id` 指向的父约束确实存在于当前批次或已知的库中。
*   **意义：** 允许在 `data/constraints_linked.json` 中显式表达约束间的父子从属关系。

#### 6.2.8 约束图谱导出器 (`src/kg_builder/constraint_graph_exporter.py`)
*   **输入：** `data/constraints_linked.json`。
*   **功能：** 将 `linker_validator.py` 输出的高度结构化的规范/约束列表转换为 Constraint Graph (CG)。
    *   每个规范/约束可以是一个节点或一组关系。
    *   `targetRef` 指向图中的特定元素（类节点、属性边、枚举节点）。
    *   `constraint_type` 和 `value` 定义了约束的具体内容。
    *   `parent_id` 用于在CG中建立层级依赖。
*   **输出：** `data/constraint_graph/autosar.graphml` 和 `data/shacl/autosar_shapes.ttl` (如果适用)。
*   **注意：** 此模块的设计与 V2 中的 `CGBuilder` 类似，但其输入源现在是经过严格抽取和校验的结构化数据，而非直接解析 XSD/Drools/KG。CG 的构建逻辑可能需要调整以适应这种更细致的输入。

---

### 6.3 统一约束层 (`src/constraint_graph/`)
*(功能同 V2，但其构建现在依赖于 `kg_builder` 输出的 `autosar.graphml`)*
*   `graph.py`: 提供 `next_valid_tokens`, `is_valid(xml)` 等接口，供 `generation_pipeline` 使用。
*   `fsm.py`: 图 → 有限状态机 (用于强 CGD)。

---

### 6.4 KG 查询 (`src/kg_query/`)
*(功能同 V2，查询的知识图谱现在可能更侧重于由 `kg_builder` 精密抽取的规范/约束知识，而不仅仅是元模型本体)*

---

### 6.5 LLM 交互层 (`src/llm_interaction/` - 主要用于 ARXML 生成)
*(功能同 V2，负责 ARXML 生成时的 LLM 调用，与 `kg_builder` 中的 `llm_extractor.py` 分离，后者专注于规范抽取任务)*

---

### 6.6 验证层 (`src/validation/`)
*(功能同 V2 - XSD, SHACL, Drools 验证器。这些验证器现在也用于验证人工审核后的 ARXML)*

---

### 6.7 生成流程 (`src/generation_pipeline/`)
*(功能同 V2 - `CGDGenerator` 等，但其依赖的 CG 来自新的 `kg_builder` 流程)*

---

### 6.8 工具库 (`src/utils/`)
*(同上一版V3草稿，包含 `llm_factory.py`, `file_io.py`, `jaxb_bridge.py` 等)*

---

### 6.9 人工审核与修改模块 (`src/human_review/`, `web_reviewer/`)
目标： 为领域专家提供一个用户友好的 Web 界面，对 LLM 生成并通过自动验证的 ARXML 文件进行最终的符合性检查和细粒度修改。修改操作基于从 AUTOSAR 元模型生成的 JAXB 注解 Java 类，确保修改的结构合法性。

核心流程：

LLM 生成的 ARXML 经过自动验证后，可被提交到人工审核系统。
后端 (ARXML → Java 对象 → JSON):
接收 ARXML 文件。
JAXB 反序列化: 使用预先根据 AUTOSAR 元模型（XSD）生成的、带有 JAXB 注解的 Java 类，将 ARXML 文件反序列化为 Java 对象树。这步确保了导入的 XML 结构上是有效的。
对象树转 JSON: 将复杂的 Java 对象树转换为一种适合前端 UI（如树形控件、表单）渲染的 JSON 结构。此 JSON 需要保留原始结构、数据类型、元素名称、属性等信息。
前端 (UI 展示与编辑):
从后端获取 ARXML 的 JSON 表示。
以可交互的树形视图展示 ARXML 结构。
用户可以选择节点，在表单中查看和编辑其属性值、文本内容。
支持（受约束的）添加、删除符合 AUTOSAR 规范的子元素（基于元模型信息，例如可选元素的列表）。
编辑时可提供基于元模型的简单校验（如数据类型、必填项）。
后端 (JSON → Java 对象 → ARXML):
接收前端提交的修改（通常是更新后的 JSON 结构或变更集）。
JSON 更新 Java 对象: 将 JSON 中的修改应用回服务器端的 Java 对象树。
JAXB 序列化: 使用 JAXB 将修改后的 Java 对象树序列化回 ARXML 字符串/文件。
用户确认后，保存修改后的 ARXML。
组件设计：

6.9.1 web_reviewer/backend/ (示例：基于Java Spring Boot)
JAXB Annotated Java Classes: (用户已提供) 根据 AUTOSAR XSD 生成的核心模型类。
Controllers (ReviewController.java):
REST API 端点：
POST /upload_arxml: 上传待审核的 ARXML。
GET /arxml_json/{id}: 获取指定 ARXML 的 JSON 表示。
POST /update_arxml/{id}: 提交修改后的 JSON。
GET /download_arxml/{id}: 下载审核后的 ARXML。
Services (ArxmlReviewService.java):
封装 JAXB 的序列化/反序列化逻辑。
处理 Java 对象与 JSON 之间的转换。
管理审核会话、状态、版本（可选）。
pom.xml / build.gradle: 包含 JAXB, Spring Web, JSON处理库 (Jackson) 等依赖。
6.9.2 web_reviewer/frontend/ (示例：基于React)
Components:
ArxmlTreeView.tsx: 显示 ARXML 结构的树形组件 (可使用 react-arborist, rc-tree 等库)。
NodeEditorForm.tsx: 根据选定节点的元数据动态生成编辑表单。
Toolbar.tsx: 提供加载、保存、验证(可选)等操作按钮。
Services/API Calls (apiService.ts): 封装与后端 API 的交互。
State Management (Redux, Zustand, Context API): 管理 ARXML 数据、编辑状态、用户信息。
UI 考虑:
清晰展示层级关系、元素类型、属性名、属性值。
对于引用 (REF)，应能显示目标路径，甚至提供跳转。
对于枚举值，应提供下拉选择。
对于基数约束（minOccurs, maxOccurs），界面应有所体现（如是否可删除，是否可添加多个）。
长列表分页或虚拟滚动。
变更高亮或对比功能 (高级)。
6.9.3 src/human_review/ (Python 侧，与主流程集成)
review_initiator.py (或集成在 generation_pipeline):
负责将通过自动验证的 ARXML 文件（或其引用）发送给 web_reviewer 后端服务。
可以轮询或通过回调机制等待审核完成。
arxml_transformer.py (若部分转换逻辑在Python端):
辅助进行 ARXML 与审核系统所需格式（如特定JSON）的转换，如果Java后端不直接处理原始ARXML。
与 utils/jaxb_bridge.py 交互（如果Java部分是独立工具）。
---

## 7 运行流程
1.  **阶段一：知识获取与CG构建 (主要由 `kg_builder` 完成)**
    a.  **人工标注：** 领域专家在 `data/input_docs/` 中添加 `#@SECTION`, `#@CLASS`, `#@ENUM`, `#@Hierarchical` 标注。
    b.  **上下文注入 (`context_injector.py`)：** 处理标注文档，注入元数据上下文，生成增强文档块到 `data/preprocessed_docs/`。
    c.  **LLM抽取 (`llm_extractor.py`)：** LLM 根据严格 Prompt 和 Schema 从增强文档块中抽取规范/约束信息。
    d.  **多模态处理 (`multimodal_processor.py`)：** (并行或串行) 从关联的图片/图表中提取信息。
    e.  **链接与校验 (`linker_validator.py`)：** 合并文本和多模态抽取结果，进行校验、链接，输出 `data/constraints_linked.json`。
    f.  **CG导出 (`constraint_graph_exporter.py`)：** 将 `constraints_linked.json` 转换为 `autosar.graphml`。
2.  **阶段二：ARXML 生成与审核 (主流程)**
    a.  **启动 & 参数解析 (`main.py`)**
    b.  **日志初始化 & 加载配置**
    c.  **组件初始化：**
        *   NLProcessor (用于解析用户需求)
        *   ConstraintGraph (从 `autosar.graphml` 加载)
        *   ValidatorHub (XSD, SHACL, Drools)
        *   LLMClient (用于ARXML生成)
        *   CGDGenerator
        *   HumanReviewServiceConnector
    d.  **遍历用户需求 (如 `run_experiment.py`)：**
        i.  NLP 解析用户自然语言需求。
        ii. `CGDGenerator` 使用 ConstraintGraph 和 LLM 生成 ARXML。
        iii. `ValidatorHub` 对生成的 ARXML 进行自动验证。
        iv. **人工审核：** 若启用且满足条件，将 ARXML 提交至 `human_review` 模块，由专家在 `web_reviewer` 界面审核修改。
        v.  (可选) 审核后的 ARXML 再次通过 `ValidatorHub` 验证。
        vi. 记录 metrics。
    e.  **结果汇总 & 报告。**

---

## 8 实验与评估设计
包含两大部分的指标：

**A. 规范抽取质量 (`kg_builder` 产出评估)** (基于 `design_docV4.md` 的预期)
| 指标                   | 期望 (V3) | 说明                                                       |
| ---------------------- | --------- | ---------------------------------------------------------- |
| 块级召回率             | ≥ 0.98    | 抽取出规范/约束文本块的比例                                    |
| 字段完整率             | ≥ 0.99    | Schema中所有必填字段都被LLM正确填充的比例                        |
| **`targetRef` 准确率** | **≥ 0.99**| `targetClass.targetAttribute` 或 `targetEnum.targetLiteral` 与人工标注/元数据一致的比例 |
| **`id_type` 准确率**   | **≥ 0.99**| 正确识别 'TPS_SWCT' 或 'constr' 的比例                       |
| **层级关系捕获率**     | ≥ 0.95    | 正确识别并链接 `parent_id` 的比例 (依赖标注质量)               |
| `linker_validator`通过率| ≥ 0.97    | LLM原始输出通过后续自动校验的比例                              |
| 人工复核率 (规范抽取)  | ≤ 0.03    | `review_queue_kg.csv` 中的条目比例                           |

**B. ARXML 生成质量与人工审核** (同上一版V3草稿)
| 类别         | 指标                                     | 描述                                   |
|--------------|------------------------------------------|----------------------------------------|
| 合规性       | XSD_Pass%, Drools_Pass%, SHACL_Pass%     | 自动验证通过率                           |
| ...          | (其他经济性、效率、质量指标同V2)           | ...                                    |
| 人工审核     | Review_Rate                              | 需要人工审核的ARXML比例                  |
|              | Avg_Correction_Severity                  | 人工修改的平均严重程度/数量                |
|              | Time_To_Review                           | 平均人工审核耗时                         |

---

## 9 CI/CD & 部署
*(同上一版V3草稿，确保 `kg_builder` 的脚本和依赖也被包含在CI流程和部署包中)*

---

## 10 里程碑
*(调整以反映 `kg_builder` 的核心地位和人工审核的并行开发)*
| 阶段 | 时间 (2025) | 交付物                                                                 |
|------|------------|------------------------------------------------------------------------|
| **M1** | 06 月      | **`kg_builder`核心流程PoC (标注->注入->LLM抽取->Linker)，`unified_metadata`准备** |
| **M2** | 07 月      | **`kg_builder`集成多模态处理，初步 `constraints_linked.json` 输出，CG导出器适配** |
| M2.5 | 08 月      | API 弱 CGD (基于新CG)、指标脚本、CI unit pass (含 `kg_builder` 测试)      |
| M3   | 09 月      | vLLM 服务、强 CGD (基于新CG)                                               |
| M3.5 | 10 月      | 人工审核模块后端(JAXB集成, API)与前端(基本ARXML树展示与编辑)原型             |
| M4   | 11 月      | 完整人工审核流程集成, k8s Helm Chart, 论文提交、GitHub 发布 (MIT)          |

---

## 11 附录
*   人工标注规范 (`src/kg_builder/annotator_guidelines.md` 的详细内容)
*   `extraction_schema.json` 的完整定义
*   (其他同 V2)

---

**V3 核心优势总结：**

通过对 `kg_builder` 模块的彻底革新，V3 版本旨在从源头上保证输入知识的结构化质量和与元模型的一致性。严格的上下文约束和多维人工标注最大限度地减少了 LLM 在规范抽取阶段的“幻觉”和不确定性。这使得后续的 Constraint Graph 构建更加可靠，进而提升了 ARXML 自动生成的准确性。最后，人工审核模块作为质量保障的最后一道关卡，确保了系统在面对复杂和关键需求时的最终可靠性。这种“前端严控抽取 + 后端人工校验”的双重保障机制是 V3 相较于前序版本在质量和可信度上的主要飞跃。
```