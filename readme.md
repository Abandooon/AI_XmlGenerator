# 项目设计文档：基于知识图谱增强的约束感知 AUTOSAR XML 生成器

## 1. 项目概述

本项目旨在设计并实现一个自动化工具，用于根据自然语言描述的需求，生成符合 AUTOSAR 标准的 XML (ARXML) 文件。核心思路是结合自然语言处理（NLP）技术理解需求，利用知识图谱（KG）提供 AUTOSAR 领域的结构化知识和约束上下文，借助大型语言模型（LLM）强大的文本生成能力，并通过 XSD Schema 语法验证和 Drools 规则引擎进行语义约束验证，最终生成高质量、符合规范的 ARXML 文件。项目包含清晰的模块划分、系统的实验设计（包括多种基线方法的对比）以及结果评估机制。

## 2. 核心技术栈

*   **自然语言处理 (NLP):** spaCy / NLTK / Transformers (用于需求文本解析、实体识别、意图理解)
*   **知识图谱 (KG):** RDFLib / SPARQLWrapper / Neo4j Driver (用于存储和查询 AUTOSAR 元模型、标准约束等领域知识)
*   **大型语言模型 (LLM):** OpenAI GPT系列 / Azure OpenAI / 其他 LLM API (用于根据 Prompt 生成 XML 文本)
*   **XML 处理与验证:** lxml (用于 XML 解析和 XSD Schema 验证)
*   **规则引擎:** Drools (通过 KIE Server REST API 或其他方式执行，用于语义约束验证)
*   **编程语言:** Python 3.x
*   **配置管理:** YAML
*   **数据处理与分析:** Pandas, Matplotlib, Seaborn
*   **测试框架:** Pytest

## 3. 项目结构 (高层)
autosar_generator_project/
├── config/ # 配置文件 (主配置, 日志配置)
├── data/ # 输入数据 (需求, 元模型, Schema, 规则, KG数据, 真值)
├── src/ # 项目核心源代码
│ ├── nlp/ # 自然语言处理模块
│ ├── kg_builder/ # 知识图谱构建模块 (可独立运行)
│ ├── kg_query/ # 知识图谱查询模块
│ ├── llm_interaction/# LLM 交互模块
│ ├── validation/ # 验证模块 (XSD, Drools)
│ ├── generation_pipeline/ # 核心生成流程与策略模块
│ └── utils/ # 通用工具函数模块
├── experiments/ # 实验运行、评估脚本
├── results/ # 实验结果输出 (生成的XML, 日志, 报告)
├── tests/ # 单元测试和集成测试
├── main.py # 主程序入口
├── requirements.txt # Python 依赖库
└── README.md # 项目说明文档
## 4. 模块详细设计

### 4.1 `config` - 配置模块

*   **主要功能:** 集中管理项目的所有配置信息，如文件路径、API 密钥、模型名称、KG 连接点、日志级别等，实现配置与代码分离。
*   **输入:** 无（由用户或开发者编辑）。
*   **输出:** 被其他模块加载和使用的配置字典。
*   **关键组件/文件:**
    *   `config.yaml`: 主要配置文件。
    *   `logging.yaml`: 日志格式化与级别配置。

### 4.2 `data` - 数据模块

*   **主要功能:** 存储项目运行所需的各类输入数据和可选的基准数据。
*   **输入:** 外部提供或由 `kg_builder` 生成（例如 KG 数据）。
*   **输出:** 供项目其他模块读取的数据文件。
*   **关键子目录:**
    *   `requirements/`: 自然语言需求文件 (.txt, .json)。
    *   `metamodel/`: AUTOSAR 元模型文件 (.arxml, .ecore)，用于 KG 构建。
    *   `standards/`: (可选) AUTOSAR 标准文档 (.pdf)，用于 KG 构建。
    *   `schemas/`: AUTOSAR XSD 模式文件 (.xsd)。
    *   `rules/`: Drools 语义约束规则文件 (.drl)。
    *   `knowledge_graph/`: KG 数据文件 (.rdf, .db) 或连接信息。
    *   `ground_truth/`: (可选) 与需求对应的“黄金标准”XML 文件 (.arxml)，用于评估。

### 4.3 `src/nlp` - 自然语言处理模块

*   **主要功能:** 解析输入的自然语言需求文本，提取关键信息，如实体（如信号名称、端口类型）、意图（如创建、配置）、属性（如长度、数据类型）等。
*   **输入:** 单条自然语言需求文本 (字符串)。
*   **输出:** 包含解析结果的结构化数据（例如，字典），包含原始文本、识别出的实体列表、推断的意图等。
*   **关键组件/文件:**
    *   `processor.py`: 包含 `NLProcessor` 类，封装 NLP 模型加载和文本处理逻辑。

## 4.4 `src/kg_builder` - 知识图谱构建模块 (详细技术细节)

**主要目标:** 将分散在 AUTOSAR 元模型文件和（可选的）标准文档中的领域知识，转化为结构化的、机器可读的知识图谱格式（如 RDF 三元组），为后续的 KG 查询和 LLM 上下文增强提供数据基础。**此模块通常作为预处理步骤离线运行**。

**核心流程:**

1.  **解析 (Parsing):** 从不同来源（ARXML, Ecore, PDF）提取结构化或半结构化信息。
2.  **本体设计 (Ontology Design - 概念步骤):** 定义如何在图谱中表示 AUTOSAR 概念、属性和关系。
3.  **转换 (Transformation):** 将解析出的信息依据本体设计，映射为图谱元素（节点、边、属性）。
4.  **填充 (Population):** 将转换后的图谱元素写入目标知识图谱存储（如 RDF 文件、三元组数据库、图数据库）。

---

### 4.4.1 `metamodel_parser.py` - 元模型解析器

*   **功能职责:** 负责解析结构化的 AUTOSAR 元模型文件。
*   **输入:**
    *   AUTOSAR ARXML 文件 (`.arxml`): 一种基于 XML 的标准格式。
    *   (可选) Ecore 模型文件 (`.ecore`): 如果使用 Eclipse Modeling Framework (EMF) 相关的元模型。
*   **技术实现:**
    *   **ARXML 解析:**
        *   **库:** 使用强大的 XML 处理库，如 `lxml`。
        *   **方法:**
            *   利用 XPath 表达式精确导航和提取特定的 AUTOSAR 元素（如 `<AR-PACKAGE>`, `<ELEMENTS>`, `<SW-COMPONENT-TYPE>`, `<PORT-PROTOTYPE>`, `<COM-SIGNAL>` 等）及其属性（如 `UUID`）。
            *   提取元素的 `<SHORT-NAME>` 和其他关键子元素的值。
            *   识别和解析元素之间的关系，特别是：
                *   **包含关系 (Containment):** 通过 XML 的层级结构体现（父子节点）。
                *   **引用关系 (References):** 解析 `<*REF>` 元素（如 `<PORT-PROTOTYPE-REF>`, `<SIGNAL-REF>`），提取 `DEST` 属性（引用的类型）和引用路径（指向目标元素的 `SHORT-NAME` 路径或 `UUID`）。
            *   处理变体点 (Variation Points) 和条件编译（如果需要）。
    *   **Ecore 解析:**
        *   **库:** 使用 `pyecore` 库。
        *   **方法:** 加载 `.ecore` 文件，遍历模型中的 `EPackage`, `EClass`, `EAttribute`, `EReference` 等元元素。提取类名、属性名、属性类型、引用关系（包括引用的类型、上下界、是否为 containment 等）。
*   **输出:**
    *   一个标准化的中间数据结构，例如 Python 的字典或自定义对象列表。这个结构应清晰地表示从元模型中提取出的所有相关元素、它们的属性、以及它们之间的包含和引用关系。
    *   **示例 (简化):**
        ```python
        [
          {'id': 'uuid_swc_1', 'type': 'SwComponentType', 'short_name': 'MySWC', 'ports': ['uuid_port_a']},
          {'id': 'uuid_port_a', 'type': 'PortPrototype', 'short_name': 'DataPort', 'direction': 'IN', 'interface_ref': 'uuid_if_x'},
          # ...
        ]
        ```
*   **挑战:**
    *   ARXML 文件可能非常庞大，需要高效的解析策略（如 `iterparse`）。
    *   正确解析和表示复杂的引用关系（跨包引用、基于 UUID 的引用）。
    *   处理不同版本的 AUTOSAR Schema 差异。

---

### 4.4.2 `doc_processor.py` - 标准文档处理器 (可选)

*   **功能职责:** 从非结构化或半结构化的 AUTOSAR 标准文档（通常是 PDF 格式）中提取有价值的知识，如图谱中未明确包含的约束、规则或最佳实践。
*   **输入:** PDF 格式的 AUTOSAR 标准文档 (`.pdf`)。
*   **技术实现:**
    *   **PDF 文本提取:**
        *   **库:** `PyPDF2`, `pdfminer.six`。
        *   **方法:** 提取文档的纯文本内容。需要处理分页、页眉页脚、多栏布局、表格（可能需要特定库或技术将其转换为文本或结构化数据）、图片标题等。对于扫描版 PDF，可能需要 OCR (Optical Character Recognition) 工具（如 `pytesseract` 配合 Tesseract OCR 引擎）。
    *   **信息抽取 (Information Extraction - IE):** 这是核心难点。
        *   **命名实体识别 (NER):**
            *   **目标:** 识别文本中提及的 AUTOSAR 概念（如 "Runnable Entity", "Timing Constraint", "NvM Block"）。
            *   **方法:**
                *   **基于规则:** 使用正则表达式、词典（Gazetteers，包含已知 AUTOSAR 术语列表）进行匹配。
                *   **基于模型:** 使用预训练的 NLP 模型（如 spaCy, BERT），并可能需要**针对 AUTOSAR 领域进行微调 (fine-tuning)** 以提高识别特定术语的准确率。
        *   **关系抽取 (RE):**
            *   **目标:** 识别实体之间的关系（如 "Runnable Entity *triggers* Bsw Event", "NvM Block *has property* RAM Block Size"）。
            *   **方法:**
                *   **基于模式:** 定义词汇或句法模式（如 Dependency Parsing + 规则）来匹配关系短语。
                *   **基于模型:** 使用监督学习或远程监督方法训练关系抽取模型。
        *   **约束/规则抽取:**
            *   **目标:** 识别描述限制或条件的句子（如 "The short name *must not exceed* 128 characters", "A client-server port *shall only be connected* to a compatible server port"）。
            *   **方法:** 通常需要更复杂的 NLP 技术，如语义角色标注 (Semantic Role Labeling - SRL)、条件句识别，或结合关键词（"must", "shall", "should not", "if...then"）和句法分析。
*   **输出:**
    *   结构化的信息列表，例如：
        *   识别出的实体及其类型。
        *   提取出的关系三元组 (实体1, 关系类型, 实体2)。
        *   抽取的约束规则文本或结构化表示。
*   **挑战:**
    *   PDF 格式多样性导致文本提取困难且易出错。
    *   自然语言的歧义性和多样性给信息抽取带来巨大挑战。
    *   需要高质量的领域词典或标注数据来训练或优化 NLP 模型。
    *   将抽取的非结构化约束转化为可在如图谱或 Drools 中使用的形式。

---

### 4.4.3 本体设计 (Ontology Design - 概念步骤)

*   **功能职责:** 在实际编码 `graph_populator` 之前，需要设计知识图谱的模式（Schema/Ontology）。这决定了知识如何在图谱中表示。
*   **关键决策:**
    *   **节点类型 (Classes):** 如何表示 AUTOSAR 的核心概念（如 `SwComponentType`, `PortPrototype`, `ComSignal`）？通常映射为图谱中的类或节点标签。
    *   **属性 (Properties/Attributes):** 如何表示元素的属性（如 `short_name`, `length`, `direction`）？通常映射为节点的属性或特定的数据属性边。
    *   **关系 (Relationships/Edges):** 如何表示元素间的关系（如 `containsPort`, `hasInterface`, `sendsSignal`）？映射为图谱中的边（带有类型/标签）。
    *   **命名空间 (Namespaces):** 定义 URI 前缀以避免命名冲突，并标识知识来源（如 `autosar:`, `standard:`, `project:`）。
    *   **标识符 (Identifiers):** 如何唯一标识图谱中的每个节点？可以使用元模型中的 UUID（如果可用且稳定），或者基于 Short Name 路径生成唯一的 URI。
    *   **数据类型 (Datatypes):** 如何表示属性值的数据类型（字符串、整数、布尔值等）？在 RDF 中使用 XSD 数据类型（如 `xsd:string`, `xsd:integer`）。
    *   **链接文档知识:** 如何将从文档中提取的实体和关系链接回元模型定义的节点？可能需要基于名称匹配或引入额外的映射关系。

---

### 4.4.4 `graph_populator.py` - 图谱填充器

*   **功能职责:** 连接到目标知识图谱存储，并将 `metamodel_parser` 和 `doc_processor` 输出的中间数据，按照预定义的本体设计，转换为图谱数据并写入。
*   **输入:**
    *   来自 `metamodel_parser` 的结构化元模型数据。
    *   来自 `doc_processor` 的提取实体、关系和约束。
    *   KG 连接配置 (来自 `config.yaml`)。
*   **技术实现:**
    *   **连接 KG 后端:**
        *   **RDF 三元组存储 (如 Apache Jena Fuseki, GraphDB):** 使用 `SPARQLWrapper` 库连接到 SPARQL 端点。
        *   **本地 RDF 文件:** 使用 `rdflib` 库在内存中构建图，然后序列化为文件 (如 Turtle `.ttl`, RDF/XML `.rdf`)。
        *   **图数据库 (如 Neo4j):** 使用官方的 `neo4j` Python 驱动程序连接到数据库实例。
    *   **数据转换与映射:**
        *   **核心逻辑:** 遍历输入的中间数据结构。
        *   **节点创建:** 为每个 AUTOSAR 元素（如 SWC, Port）创建一个节点。根据本体设计分配类型（RDF Class 或 Neo4j Label）。生成或获取唯一标识符 (URI 或 Node ID)。
        *   **属性添加:** 将元素的属性（如 Short Name, UUID）添加为节点的属性或数据属性边。确保数据类型正确（使用 RDF Literals 或 Neo4j 属性类型）。
        *   **关系创建:** 根据元模型中的包含关系和引用关系，或文档中提取的关系，创建图谱中的边。为边分配类型（RDF Predicate 或 Neo4j Relationship Type）。
        *   **链接:** 确保引用关系正确链接到目标节点（通过 URI 或 ID 查找）。
    *   **写入图谱:**
        *   **RDF:** 构建 SPARQL `INSERT DATA` 或 `UPDATE` 查询，并通过 `SPARQLWrapper` 发送。对于 `rdflib`，直接调用 `graph.add((subject, predicate, object))`。
        *   **Neo4j:** 构建 Cypher `CREATE` 或 `MERGE` 语句，并通过驱动程序执行。`MERGE` 通常更好，可以避免重复创建已存在的节点或关系（幂等性）。
    *   **性能优化:** 对于大量数据，使用批量插入（SPARQL `INSERT DATA` 支持多三元组，Cypher `UNWIND ... CREATE/MERGE`）和事务管理。
*   **输出:**
    *   填充了 AUTOSAR 知识的目标知识图谱（数据库状态被修改或生成 RDF 文件）。
    *   记录填充过程的日志信息（成功、失败、跳过等）。
*   **挑战:**
    *   确保生成的标识符全局唯一且一致。
    *   高效地处理大规模元模型数据，避免性能瓶颈。
    *   实现幂等性操作，使得重复运行填充脚本不会产生冗余数据或错误。
    *   错误处理和事务管理，确保数据一致性。

---

**总结:**

知识图谱构建模块 (`kg_builder`) 是一个关键的预处理步骤，它通过解析结构化和非结构化的 AUTOSAR 资源，结合精心设计的本体，将领域知识编码到知识图谱中。这个过程涉及 XML/Ecore 解析、复杂的 NLP 信息抽取、数据转换和映射，以及与特定 KG 后端的交互。构建出的知识图谱是后续实现知识图谱增强的约束感知生成的基础。

### 4.5 `src/kg_query` - 知识图谱查询模块

*   **主要功能:** 提供查询知识图谱的能力。根据 NLP 解析结果或其他上下文信息，生成查询语句（如 SPARQL），从 KG 中检索相关的 AUTOSAR 结构、约束、关系或实例信息，为 LLM 生成提供上下文。
*   **输入:** 查询语句 (字符串) 或需要查询的概念/实体信息 (来自 NLP 结果)。
*   **输出:** 从 KG 返回的查询结果 (通常是结构化数据，如字典列表)。
*   **关键组件/文件:**
    *   `querier.py`: 包含 `KGQuerier` 类，封装 KG 连接和查询执行逻辑。

### 4.6 `src/llm_interaction` - LLM 交互模块

*   **主要功能:** 负责与配置的大型语言模型进行交互。包括格式化输入（构建 Prompt），发送请求到 LLM API，并接收返回的生成文本。
*   **输入:** Prompt 字符串 (由 `generation_pipeline` 或 `prompt_formatter` 构建)。
*   **输出:** LLM API 返回的生成文本 (期望是 XML 字符串)，或在出错时返回 None。
*   **关键组件/文件:**
    *   `prompt_formatter.py`: 提供函数来根据不同策略（基础、KG 增强、修复）构建不同的 Prompt。
    *   `llm_client.py`: 包含 `LLMClient` 类，处理与特定 LLM 提供商 API 的通信（如 OpenAI API 调用）。

### 4.7 `src/validation` - 验证模块

*   **主要功能:** 对 LLM 生成的 XML 进行验证，确保其符合 AUTOSAR 规范。
*   **输入:**
    *   待验证的 XML 文本 (字符串)。
    *   XSD Schema 对象 (由 `load_xsd_schema` 加载)。
    *   Drools Validator 实例 (用于调用 Drools 规则)。
    *   (Drools) 转换后用于规则引擎的数据 (如 JSON facts)。
*   **输出:**
    *   一个布尔值，指示验证是否通过。
    *   一个字符串列表，包含具体的验证错误信息 (如果验证失败)。
*   **关键组件/文件:**
    *   `xsd_validator.py`: 提供 `validate_xsd` 函数，使用 lxml 执行 XSD 语法验证。
    *   `drools_validator.py`: 包含 `DroolsValidator` 类，负责与 Drools 引擎（如 KIE Server）交互，执行语义规则验证。

### 4.8 `src/generation_pipeline` - 核心生成流程与策略模块

*   **主要功能:** 编排整个 XML 生成的核心流程。根据选择的生成策略（基线1、基线2、基线3、提出方法），协调调用 NLP、KG 查询、LLM 交互和验证模块。实现可能包含验证失败后的修复逻辑。
*   **输入:**
    *   原始需求文本 (字符串)。
    *   NLP 解析结果 (字典)。
    *   配置信息 (决定使用哪个策略和组件)。
    *   其他模块的实例 (LLM Client, KG Querier, Validators)。
*   **输出:**
    *   最终生成的（可能经过修复和验证的）XML 文本 (字符串)，或在失败时返回 None。
    *   最终的验证错误列表 (如果最终结果无效)。
*   **关键组件/文件:**
    *   `base_generator.py`: (可选) 定义生成器的抽象基类。
    *   `generators.py`: 包含不同生成策略的具体实现类 (`NaiveGenerator`, `XsdConstrainedGenerator`, `FullConstrainedGenerator`, `KgEnhancedGenerator`)。
    *   `repair.py`: (可选) 包含或被 `BaseGenerator` 调用，实现基于错误信息的 XML 修复逻辑（通常是构建修复 Prompt 并再次调用 LLM）。

### 4.9 `src/utils` - 通用工具函数模块

*   **主要功能:** 提供项目中多个模块可能共用的辅助函数，如文件读写（YAML, JSON, TXT）、日志配置初始化等。
*   **输入:** 取决于具体函数 (如文件路径、数据对象)。
*   **输出:** 取决于具体函数 (如读取的数据、文件写入状态、日志记录)。
*   **关键组件/文件:**
    *   `file_io.py`: 封装文件加载和保存操作。
    *   `logging_config.py`: 提供 `setup_logging` 函数，根据配置文件初始化日志系统。

### 4.10 `experiments` - 实验运行与评估模块

*   **主要功能:** 负责执行整个实验流程，包括加载数据集、按配置运行不同的生成方法、收集结果、计算评估指标以及（可选地）生成分析报告和图表。
*   **输入:**
    *   主配置文件路径。
    *   需求数据集 (`data/requirements/`)。
    *   (可选) Ground Truth 数据 (`data/ground_truth/`)。
*   **输出:**
    *   生成的 XML 文件 (存入 `results/generated_xml/`)。
    *   运行日志 (存入 `results/logs/`)。
    *   包含评估指标的汇总报告 (如 CSV 文件，存入 `results/reports/`)。
    *   (可选) 分析图表 (存入 `results/reports/`)。
*   **关键组件/文件:**
    *   `run_experiment.py`: 实验主脚本，协调整个流程。
    *   `dataset_loader.py`: 加载需求和 Ground Truth 数据。
    *   `metrics_calculator.py`: 计算评估指标 (如成功率、验证通过率、与真值的相似度等)。
    *   `analysis.py`: (可选) 对汇总结果进行统计分析并生成图表。

### 4.11 `results` - 结果存储模块

*   **主要功能:** 存储实验过程中产生的所有输出文件。
*   **输入:** 由 `experiments` 模块或其他运行过程产生的文件和数据。
*   **输出:** 持久化存储的实验结果。
*   **关键子目录:**
    *   `generated_xml/`: 按方法分类存储生成的 XML 文件。
    *   `logs/`: 存储运行日志文件。
    *   `reports/`: 存储指标汇总报告 (CSV) 和分析图表 (PNG)。

### 4.12 `tests` - 测试模块

*   **主要功能:** 包含对 `src` 目录下各模块功能的单元测试和集成测试，确保代码质量和功能的正确性。
*   **输入:** `src` 目录下的源代码。
*   **输出:** 测试执行结果 (通过/失败)。
*   **关键组件/文件:**
    *   `test_*.py`: 针对特定模块或功能的测试文件 (如 `test_nlp.py`, `test_validation.py`)。

## 5. 核心程序运行流程 (`main.py` -> `run_experiment.py`)

1.  **启动:** 执行 `python main.py`。
2.  **参数解析 (`main.py`):** 解析命令行参数，主要是获取主配置文件路径 (`config/config.yaml`)。
3.  **日志初始化 (`main.py` -> `utils.logging_config`):** 根据 `config/logging.yaml` 设置日志记录器。
4.  **调用实验主函数 (`main.py` -> `experiments.run_experiment.main`):** 将配置文件路径传递给实验运行主函数。
5.  **加载配置 (`run_experiment.py`):** 使用 `utils.file_io.load_yaml` 加载主配置文件。
6.  **初始化组件 (`run_experiment.py`):**
    *   创建 `NLProcessor` 实例。
    *   创建 `LLMClient` 实例 (传入 LLM 配置和 API 密钥)。
    *   如果需要 (如运行 `proposed` 方法)，创建 `KGQuerier` 实例 (传入 KG 配置)。
    *   如果需要 (如运行 `baseline2` 及以上方法)，加载 XSD Schema (`validation.xsd_validator.load_xsd_schema`)。
    *   如果需要 (如运行 `baseline3` 及以上方法)，创建 `DroolsValidator` 实例 (传入 Drools 配置)。
7.  **加载数据集 (`run_experiment.py` -> `experiments.dataset_loader`):** 从 `data/requirements/` 加载需求文本，并可选地从 `data/ground_truth/` 加载对应的黄金标准 XML。
8.  **遍历生成方法 (`run_experiment.py`):** 对于配置文件中 `experiments.methods_to_run` 指定的每种方法 (如 `baseline1`, `proposed`):
    a.  **获取生成器实例:** 根据方法名称，实例化对应的生成器类 (如 `NaiveGenerator`, `KgEnhancedGenerator`)，并传入所需的组件实例 (LLM Client, KG Querier 等)。
    b.  **遍历需求 (`run_experiment.py`):** 对于数据集中的每一条需求:
        i.  **NLP 处理:** 调用 `NLProcessor` 解析需求文本，获取意图、实体等。
        ii. **调用生成 (`run_experiment.py` -> `generator.generate`):** 执行选定生成器的 `generate` 方法，传入原始需求文本和 NLP 解析结果。
            *   **生成器内部流程 (以 `KgEnhancedGenerator` 为例):**
                1.  **KG 查询:** (`KgEnhancedGenerator._query_kg_for_context`) 调用 `KGQuerier` 获取与需求相关的上下文信息。
                2.  **构建 Prompt:** (`llm_interaction.prompt_formatter.format_kg_enhanced_prompt`) 结合需求文本和 KG 上下文创建 Prompt。
                3.  **LLM 生成:** (`LLMClient.generate_text`) 调用 LLM API 获取初步的 XML 文本。
                4.  **验证:** (`BaseGenerator._validate_xml`) 调用 `validation` 模块进行 XSD 和/或 Drools 验证。
                5.  **修复 (如果需要):** 如果验证失败且允许修复，调用 `BaseGenerator._repair_xml` 构建修复 Prompt，再次调用 LLM 生成修复后的 XML，然后重新验证。此过程可能重复，直到验证通过或达到最大尝试次数。
        iii. **保存结果:** (`run_experiment.py` -> `utils.file_io`) 将最终生成的 XML (如果成功) 或错误信息保存到 `results/generated_xml/{method_name}/` 目录下。
        iv. **计算指标:** (`run_experiment.py` -> `experiments.metrics_calculator`) 计算本次生成的评估指标 (如是否成功、验证是否通过、错误数量、与 Ground Truth 的相似度等)。
        v.  **记录结果:** 将本次运行的配置、路径、耗时、指标等信息添加到结果列表中。
9.  **汇总与保存 (`run_experiment.py`):** 将所有运行结果整理成 Pandas DataFrame，并保存为 CSV 文件到 `results/reports/`。
10. **(可选) 分析与绘图 (`run_experiment.py` -> `experiments.analysis`):** 加载结果 CSV 文件，使用 Matplotlib/Seaborn 生成分析图表（如各方法成功率对比、生成时间对比等），保存到 `results/reports/analysis_plots/`。
11. **结束。**

## 6. 实验设计与对比

项目通过配置 `experiments.methods_to_run` 来运行和比较不同的生成策略：

*   **基线1 (`NaiveGenerator`):** 仅使用 LLM 根据基本 Prompt 生成 XML，不进行任何验证或修复。评估 LLM 的基础生成能力。
*   **基线2 (`XsdConstrainedGenerator`):** LLM 生成后，进行 XSD 语法验证。如果验证失败，尝试使用 LLM 进行修复，并再次验证。评估 XSD 约束和修复的效果。
*   **基线3 (`FullConstrainedGenerator`):** LLM 生成后，依次进行 XSD 语法验证和 Drools 语义验证。如果任一验证失败，尝试使用 LLM 进行修复，并重新完整验证。评估 XSD+Drools 约束和修复的效果。
*   **提出方法 (`KgEnhancedGenerator`):** 在生成前，先查询知识图谱获取上下文信息，构建增强型 Prompt 指导 LLM 生成。生成后同样进行完整的 XSD 和 Drools 验证与修复。评估知识图谱增强对生成质量和合规性的提升效果。

通过对比这些方法在各项评估指标（生成成功率、验证通过率、与真值相似度、生成时间等）上的表现，可以量化评估知识图谱增强和不同约束组合的价值。

## 7. 关键挑战与未来工作

*   **知识图谱构建:** 从多样化的 AUTOSAR 文档（元模型、标准 PDF 等）准确、全面地构建高质量知识图谱是核心挑战。
*   **KG 查询与 Prompt 工程:** 如何将 NLP 解析结果有效映射为 KG 查询？如何将 KG 返回的结构化信息有效融入 LLM Prompt 以精确指导生成？这是发挥 KG 价值的关键。
*   **Drools 规则编写与维护:** 定义全面且正确的 AUTOSAR 语义约束规则需要深厚的领域知识，且规则库的维护成本较高。
*   **评估指标:** 除了基本的验证通过率，如何设计更精细的指标来衡量生成 XML 的语义准确性、完整性和简洁性？
*   **修复机制:** 如何设计更智能、更有效的修复策略，准确诊断错误并生成高质量的修复指令给 LLM？
*   **性能与扩展性:** 处理大规模需求或复杂配置时，LLM 调用、KG 查询和验证过程的效率可能成为瓶颈。
*   **LLM 幻觉与稳定性:** LLM 可能生成不符合要求或与上下文矛盾的内容，需要通过约束和修复来缓解。

未来的工作可以围绕优化 KG 构建流程、改进 Prompt 设计、增强修复逻辑、探索更有效的评估方法以及提升系统整体性能和鲁棒性等方面展开。