# 参考文献替换与引文复核

当前论文采用 33 项参考文献；26 项替换为实际取得的官方导出，包括出版社 13 项、IETF 1 项、作者机构 1 项以及 DOI 注册机构 11 项。另 7 项规范或法规未取得官方 BibTeX 导出，保留已核对的固定版本信息，并更换为明确的本地 key。

原始导出存放于 [official_exports](official_exports/)，逐项来源见 [BIBTEX_PROVENANCE.json](BIBTEX_PROVENANCE.json)。文件名前缀是替换前编号；下面同时列出新旧编号。DOI 注册机构导出和作者机构导出没有标成出版社直接导出。

## 引用内容复核

引言与相关工作审查覆盖 29 处引文，方法、实验、结论与附录覆盖 42 处；补入 XSD 规范引用后，当前稿共有 72 处文献引用。表格、实验结果、案例代码片段及 80 个稳定标签保持不变。

本轮主要修正了 Grammar-Aligned Decoding 的采样分布说明、PathOCL 的评价指标以及 RAG 中“模型生成”的歧义；补入 XSD 顺序要求的依据，调整结论中的引文位置，并补回 case19 已有题干前提。

## 官网导出的必要处理

- JOT 导出的作者字段夹有 HTML 标签，月份使用未定义宏；仅清除标签并修正月份表示。页码根据官方 PDF 由 3:99-112 规范为 99--112；原始导出保留。
- 两篇不同的 Ma 2025 论文收到相同的 DOI 导出 key，分别加 a、b 消除冲突。Di Rocco 的不可见空白和 Train Benchmark key 的重音做了可移植性规范，作者姓名保留导出形式。
- 个别 DOI 导出用 July、Sept 等未定义月份宏，转换为等价的字面量；没有改变日期。
- XGrammar 采用 MLSys 官网导出的作者顺序 Dong / Ruan / Cai / Xu / Zhao / Lai / Chen。官网 PDF 的顺序为 Dong / Ruan / Cai / Lai / Xu / Zhao / Chen，两种官方载体存在差异，供作者最终核准。
- Synchromesh 采用 Microsoft Research 的正式 ICLR 2022 导出，使用 Alex Polozov、Chris Meek 的姓名形式；原始 PDF 的显示名可能不同。
- JSON Schema 改用 IETF 的同一草案编号导出，日期为 2022-06-10；此前 json-schema.org 页面显示 2022-06-16。文中所指仍为 Draft 2020-12 的验证规范。
- 审阅用参考文献样式保留官网题名大小写，并去除仅 DOI 大小写不同导致的重复链接；官方模板文件原样保留。

## 按当前论文编号的来源和 key 对照

| 当前编号 | 原编号 | 文献 | 当前 key | 来源 |
| --- | --- | --- | --- | --- |
| [1] | [1] | [Survey and classification of model transformation tools](https://doi.org/10.1007/s10270-018-0665-6) | `Kahani2019` | [出版社官网导出](https://citation-needed.springer.com/v2/references/10.1007/s10270-018-0665-6?format=bibtex&flavour=citation) |
| [2] | [2] | [On the use of large language models in model-driven engineering](https://doi.org/10.1007/s10270-025-01263-8) | `DiRocco2025` | [出版社官网导出](https://citation-needed.springer.com/v2/references/10.1007/s10270-025-01263-8?format=bibtex&flavour=citation) |
| [3] | [27] | [XML Schema Part 1: Structures Second Edition](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/) | `W3C2004XMLSchemaStructures` | [官方规范信息整理；未取得 BibTeX 导出](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/) |
| [4] | [3] | [Synchromesh: Reliable code generation from pre-trained language models](https://www.microsoft.com/en-us/research/publication/synchromesh-reliable-code-generation-from-pre-trained-language-models/) | `poesia2022synchromesh` | [作者机构官网导出](https://www.microsoft.com/en-us/research/publication/synchromesh-reliable-code-generation-from-pre-trained-language-models/bibtex/) |
| [5] | [4] | [Accurate and Consistent Graph Model Generation from Text with Large Language Models](http://dx.doi.org/10.1109/MODELS67397.2025.00018) | `Chen_2025` | [DOI 注册机构官方导出](https://doi.org/10.1109/MODELS67397.2025.00018) |
| [6] | [5] | [EMF-Kaizen: an intelligent assistant for domain-specific modelling and meta-modelling](http://www.jot.fm/contents/issue_2026_03/a8.html) | `JOT:issue_2026_03/a8` | [出版社官网导出](https://www.jot.fm/contents/issue_2026_03/a8/bibtex.html) |
| [7] | [6] | [Object Constraint Language, Version 2.4](https://www.omg.org/spec/OCL/2.4/PDF) | `OMG2014OCL24` | [官方规范信息整理；未取得 BibTeX 导出](https://www.omg.org/spec/OCL/2.4/PDF) |
| [8] | [7] | [XML Metadata Interchange (XMI) Specification, Version 2.5.1](https://www.omg.org/spec/XMI/2.5.1/PDF) | `OMG2015XMI251` | [官方规范信息整理；未取得 BibTeX 导出](https://www.omg.org/spec/XMI/2.5.1/PDF) |
| [9] | [8] | [A Dual-Stage Framework for Behavior-Enhanced Automated Code Generation in Industrial-Scale Meta-Models](http://dx.doi.org/10.1109/ACCESS.2025.3614174) | `Ma_2025a` | [DOI 注册机构官方导出](https://doi.org/10.1109/ACCESS.2025.3614174) |
| [10] | [9] | [A graph solver for the automated generation of consistent domain-specific models](http://dx.doi.org/10.1145/3180155.3180186) | `Semer_th_2018` | [DOI 注册机构官方导出](https://api.crossref.org/works/10.1145/3180155.3180186/transform/application/x-bibtex) |
| [11] | [10] | [MDE in the Era of Generative AI](https://citation-needed.springer.com/v2/references/10.1007/978-3-031-85356-2_8?format=bibtex&flavour=citation) | `10.1007/978-3-031-85356-2_8` | [出版社官网导出](https://citation-needed.springer.com/v2/references/10.1007/978-3-031-85356-2_8?format=bibtex&flavour=citation) |
| [12] | [11] | [Synergy of Large Language Model and Model Driven Engineering for Automated Development of Centralized Vehicular Systems](https://arxiv.org/abs/2404.05508) | `https://doi.org/10.48550/arxiv.2404.05508` | [DOI 注册机构官方导出](https://data.crosscite.org/application/x-bibtex/10.48550/arXiv.2404.05508) |
| [13] | [12] | [AI-Enhanced AUTOSAR Configuration: Efficient Methods for Dataset Generation and Automated Code Production](http://dx.doi.org/10.1109/RTSI61910.2024.10761393) | `El_Gnainy_2024` | [DOI 注册机构官方导出](https://doi.org/10.1109/RTSI61910.2024.10761393) |
| [14] | [13] | [Automating AUTOSAR BSW Configuration Generation with Fine-Tuned LLMs and a Compact Intermediate Representation](http://dx.doi.org/10.3390/app16178443) | `Samy_2026` | [DOI 注册机构官方导出](https://api.crossref.org/works/10.3390/app16178443/transform/application/x-bibtex) |
| [15] | [14] | [PathOCL: Path-Based Prompt Augmentation for OCL Generation with GPT-4](http://dx.doi.org/10.1145/3650105.3652290) | `Abukhalaf_2024` | [DOI 注册机构官方导出](https://api.crossref.org/works/10.1145/3650105.3652290/transform/application/x-bibtex) |
| [16] | [15] | [A survey of traceability in requirements engineering and model-driven development](https://doi.org/10.1007/s10270-009-0145-0) | `Winkler2010` | [出版社官网导出](https://citation-needed.springer.com/v2/references/10.1007/s10270-009-0145-0?format=bibtex&flavour=citation) |
| [17] | [16] | [Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks](https://proceedings.neurips.cc/paper_files/paper/2020/file/6b493230205f780e1bc26945df7481e5-Paper.pdf) | `NEURIPS2020_6b493230` | [出版社官网导出](https://papers.nips.cc/paper_files/paper/10517-/bibtex) |
| [18] | [17] | [Grammar-Constrained Decoding for Structured NLP Tasks without Finetuning](https://aclanthology.org/2023.emnlp-main.674/) | `geng-etal-2023-grammar` | [出版社官网导出](https://aclanthology.org/2023.emnlp-main.674.bib) |
| [19] | [18] | [XGrammar: Flexible and Efficient Structured Generation Engine for Large Language Models](https://proceedings.mlsys.org/paper_files/paper/2025/file/5c20ca4b0b20b0bd2f1d839dc605e70f-Paper-Conference.pdf) | `MLSYS2025_5c20ca4b` | [出版社官网导出](https://proceedings.mlsys.org/paper_files/paper/619-/bibtex) |
| [20] | [19] | [XGrammar-2: Dynamic and Efficient Structured Generation Engine for Agentic LLMs](http://dx.doi.org/10.1145/3786335.3813124) | `Li_2026` | [DOI 注册机构官方导出](https://api.crossref.org/works/10.1145/3786335.3813124/transform/application/x-bibtex) |
| [21] | [20] | [Projectional Decoding: Towards Semantic-Aware LLM Generation](http://dx.doi.org/10.1145/3803437.3805571) | `Chen_2026` | [DOI 注册机构官方导出](https://api.crossref.org/works/10.1145/3803437.3805571/transform/application/x-bibtex) |
| [22] | [21] | [Grammar-Aligned Decoding](https://proceedings.neurips.cc/paper_files/paper/2024/file/2bdc2267c3d7d01523e2e17ac0a754f3-Paper-Conference.pdf) | `NEURIPS2024_2bdc2267` | [出版社官网导出](https://proceedings.neurips.cc/paper_files/paper/24012-/bibtex) |
| [23] | [22] | [Generating repairs for inconsistent models](https://doi.org/10.1007/s10270-022-00996-0) | `Marchezan2023` | [出版社官网导出](https://citation-needed.springer.com/v2/references/10.1007/s10270-022-00996-0?format=bibtex&flavour=citation) |
| [24] | [23] | [Self-Refine: Iterative Refinement with Self-Feedback](https://proceedings.neurips.cc/paper_files/paper/2023/file/91edff07232fb1b55a505a9e9f6c0ff3-Paper-Conference.pdf) | `NEURIPS2023_91edff07` | [出版社官网导出](https://proceedings.neurips.cc/paper_files/paper/20017-/bibtex) |
| [25] | [24] | [SpecGen: Automated Generation of Formal Program Specifications via Large Language Models](http://dx.doi.org/10.1109/ICSE55347.2025.00129) | `Ma_2025b` | [DOI 注册机构官方导出](https://api.crossref.org/works/10.1109/ICSE55347.2025.00129/transform/application/x-bibtex) |
| [26] | [25] | [JSON Schema Validation: A Vocabulary for Structural Validation of JSON](https://datatracker.ietf.org/doc/draft-bhutton-json-schema-validation/01/) | `bhutton-json-schema-validation-01` | [IETF 官网导出](https://datatracker.ietf.org/doc/draft-bhutton-json-schema-validation/bibtex/) |
| [27] | [26] | [A framework for evaluating tool support for co-evolution of modeling languages, tools and models](https://doi.org/10.1007/s10270-024-01218-5) | `Tolvanen2025` | [出版社官网导出](https://citation-needed.springer.com/v2/references/10.1007/s10270-024-01218-5?format=bibtex&flavour=citation) |
| [28] | [28] | [Software Component Template](https://www.autosar.org/fileadmin/standards/R4.2.2/CP/AUTOSAR_TPS_SoftwareComponentTemplate.pdf) | `AUTOSAR2015SoftwareComponentTemplate422` | [官方规范信息整理；未取得 BibTeX 导出](https://www.autosar.org/fileadmin/standards/R4.2.2/CP/AUTOSAR_TPS_SoftwareComponentTemplate.pdf) |
| [29] | [29] | [Specification of RTE](https://www.autosar.org/fileadmin/standards/R4.2.2/CP/AUTOSAR_SWS_RTE.pdf) | `AUTOSAR2015RTE422` | [官方规范信息整理；未取得 BibTeX 导出](https://www.autosar.org/fileadmin/standards/R4.2.2/CP/AUTOSAR_SWS_RTE.pdf) |
| [30] | [30] | [Efficient Memory Management for Large Language Model Serving with PagedAttention](http://dx.doi.org/10.1145/3600006.3613165) | `Kwon_2023` | [DOI 注册机构官方导出](https://api.crossref.org/works/10.1145/3600006.3613165/transform/application/x-bibtex) |
| [31] | [31] | [The Train Benchmark: cross-technology performance evaluation of continuous model queries](https://doi.org/10.1007/s10270-016-0571-8) | `Szarnyas2018` | [出版社官网导出](https://citation-needed.springer.com/v2/references/10.1007/s10270-016-0571-8?format=bibtex&flavour=citation) |
| [32] | [32] | [Regulation (EU) No 1215/2012 of the European Parliament and of the Council of 12 December 2012 on jurisdiction and the recognition and enforcement of judgments in civil and commercial matters (recast)](https://eur-lex.europa.eu/eli/reg/2012/1215/2015-02-26/eng) | `EU1215_2012_Consolidated20150226` | [官方规范信息整理；未取得 BibTeX 导出](https://eur-lex.europa.eu/eli/reg/2012/1215/2015-02-26/eng) |
| [33] | [33] | [Regulation (EU) 2017/1001 of the European Parliament and of the Council of 14 June 2017 on the European Union trade mark (codification) (Text with EEA relevance)](https://eur-lex.europa.eu/eli/reg/2017/1001/2025-12-01/eng) | `EU2017_1001_Consolidated20251201` | [官方规范信息整理；未取得 BibTeX 导出](https://eur-lex.europa.eu/eli/reg/2017/1001/2025-12-01/eng) |

## 改句与原文对照

以下只列文字和引用位置调整；所有 key 的替换详见上表和 [KEY_MAP.json](KEY_MAP.json)。新表述以红色标记。

### IR18（原稿第 149 行）

**原文：** PathOCL 以 UML 类模型和自然语言约束为输入，选取相关类及模型路径构造提示，再生成 OCL 表达式\paperref{abukhalafPathOCLPathBasedPrompt2024}。其结果显示，选择路径上下文可以减少提示规模并改善生成约束的有效性，而语义正确性的改善仍需单独考察。

**修改：** <span style="color:#c00000">PathOCL 以 UML 类模型和自然语言约束为输入，选取相关类及模型路径构造提示，再生成 OCL 表达式。该文分别评价约束的可编译性和语义正确性：路径提示缩短了单次输入，通过多条路径尝试提高了可编译约束的比例，语义正确率的改善较小\paperref{abukhalafPathOCLPathBasedPrompt2024}。</span>

**依据：** 有效性需明确所指。原句可能被理解为论文未评价语义；实际上分别评价且相对完整 UML 上下文正确率提升较小。并须避免暗示只缩短单个提示就带来了较高总体通过率，作者使用 top-k 路径尝试。

[来源 1](https://arxiv.org/html/2405.12450v1)

### IR20（原稿第 155 行）

**原文：** 检索增强生成通过外部材料为模型生成提供依据\paperref{Lewis2020RAG}。

**修改：** <span style="color:#c00000">检索增强生成将外部文档的检索结果与语言模型的文本生成过程结合\paperref{Lewis2020RAG}。</span>

**依据：** MDE 语境中的模型生成通常指实例模型构造；RAG 原论文这里支撑的是语言模型生成与外部知识检索的结合。

[来源 1](https://papers.nips.cc/paper/2020/hash/6b493230205f780e1bc26945df7481e5-Abstract.html)

### IR24（原稿第 163 行）

**原文：** Synchromesh 将示例检索与完成引擎结合，在部分输出上执行语法、作用域、类型和部分上下文逻辑\paperref{poesiaSynchromeshReliableCode2021}。

**修改：** <span style="color:#c00000">Synchromesh 将示例检索与补全引擎结合，在部分输出上执行语法、作用域、类型和部分上下文逻辑\paperref{poesiaSynchromeshReliableCode2021}。</span>

**依据：** completion engine 通常译为补全引擎；技术内容和引用位置正确。

[来源 1](https://www.microsoft.com/en-us/research/wp-content/uploads/2022/01/csd_arxiv.pdf)

### INTRO-XSD（原稿第 70 行）

**原文：** 例如，以对象属性表示模型特征时，属性书写顺序不能替代 XSD 中的元素顺序规则；后者需要由序列化映射和目标格式检查共同处理。

**修改：** <span style="color:#c00000">例如，以对象属性表示模型特征时，属性书写顺序不能替代 XSD 中的元素顺序规则\paperref{W3CXMLSchema2004}；后者需要由序列化映射和目标格式检查共同处理。</span>

**依据：** W3C XML Schema Part1 §3.8（Model Groups）定义 sequence、choice、all；sequence 保留颗粒顺序。此引文支撑 XSD 顺序规则，末半句是本文序列化设计。

[来源 1](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cModel_Group)

### M1（原稿第 390 行）

**原文：** 受约束解码会改变原模型的输出分布，其局部筛选不等同于在所有满足约束的完整结果中进行最优选择\paperref{parkGrammaralignedDecoding2025}。

**修改：** <span style="color:#c00000">受约束解码会改变原模型的输出分布；逐步筛选并重新归一化，通常不同于在完整输出满足约束的条件下从原模型分布采样\paperref{parkGrammaralignedDecoding2025}。</span>

**依据：** Grammar-Aligned Decoding 讨论条件采样分布，原句将其改写为最优化问题，论断对象发生了变化。

[来源 1](https://proceedings.neurips.cc/paper_files/paper/2024/hash/2bdc2267c3d7d01523e2e17ac0a754f3-Abstract-Conference.html)

### M2（原稿第 190 行）

**原文：** 在结构化生成中，JSON Schema 是一种广泛采用、具有成熟工具支持的约束表示，可描述字段类型、必需项、数量及允许值\paperref{JSONSchemaValidation202012}。

**修改：** <span style="color:#c00000">JSON Schema 通过验证关键字描述 JSON 实例的字段类型、必需项、数量及允许值，为结构化生成提供约束表示\paperref{JSONSchemaValidation202012}。</span>

**依据：** 该规范直接支持关键字和验证语义，不直接支持“广泛采用、成熟”的评价。保留其与结构化生成的关系，并让引文贴合可核查技术内容。

[来源 1](https://json-schema.org/draft/2020-12/json-schema-validation)

### M3（原稿第 714 行）

**原文：** 近期 LLM 与 MDE 研究已涉及模型与元模型构造、语义引导生成，以及形式化规格生成\paperref{Almonte2026EMFKaizen}\paperref{Chen2026ProjectionalDecoding}\paperref{maSpecGenAutomatedGeneration2025}。

**修改：** <span style="color:#c00000">近期 LLM 与 MDE 研究已涉及模型与元模型构造\paperref{Almonte2026EMFKaizen}、语义引导生成\paperref{Chen2026ProjectionalDecoding}，以及形式化规格生成\paperref{maSpecGenAutomatedGeneration2025}。</span>

**依据：** 三个不同研究对象分别对应三篇来源。移动现有引文，使对应关系直接可见，不增加参考文献或改变结论。

[来源 1](https://www.jot.fm/issues/issue_2026_03/a8.pdf)；[来源 2](https://conf.researchr.org/details/fse-2026/fse-2026-ideas-visions-and-reflections/20/Projectional-Decoding-Towards-Semantic-Aware-LLM-Generation)；[来源 3](https://conf.researchr.org/details/icse-2025/icse-2025-research-track/173/SpecGen-Automated-Generation-of-Formal-Program-Specifications-via-Large-Language-Mod)

### M4（原稿第 1281 行）

**原文：** case19 中，依据 Article 6(1) 转交德国国内法的结论明确，后续国内法是否赋予管辖权仍待判断\paperref{EU1215_2012}；

**修改：** <span style="color:#c00000">case19 的被告仅在中国有住所，题干已排除 Article 6(1) 所列例外，因此应由德国国内法判断管辖权；现有材料尚不能确定德国国内法是否赋予管辖权\paperref{EU1215_2012}。</span>

**依据：** 不重新裁判案例；仅补回已有题干事实，使国内法转介结论的适用前提可由读者看懂，避免把附例外的 Article6(1) 写成无条件规则。后续布尔标记说明与专家意见保持原样。

[来源 1](https://eur-lex.europa.eu/legal-content/EN/AUTO/?qid=1755638897268&uri=CELEX%3A02012R1215-20150226)

## 核验结果

当前 PDF 36 页；33 项文献、72 处引文、80 个稳定标签及 132 个 PDF 内部链接均通过检查。BibTeX 无警告，无未定义引用、缺字或版心溢出。附录 A—D 已整合在 main.tex 中。实验文件的逐文件校验在交付记录中保存。
