**设计文档：基于人工预标注与上下文增强的 AUTOSAR 约束抽取与对齐系统**

**1. 项目概述**

本项目旨在从 AUTOSAR 相关文档（Markdown/纯文本）中自动抽取结构化的约束信息，并将其链接到标准的 UML 元模型。V3.0 版本引入了人工预标注和上下文增强机制，以显著提高抽取准确性和流程效率。

**核心流程：**

1.  **人工预处理与标注：** 由领域专家在原始文档中添加特定格式的标注，明确关键信息。
2.  **上下文注入预处理：** 系统根据人工标注识别焦点类，从元数据中提取相关属性，并将此上下文信息注入到文档块中。
3.  **LLM 约束抽取：** 使用大型语言模型（LLM）处理增强后的文档块，抽取约束的各个组成部分。
4.  **轻量级 Linker 与校验：** 对 LLM 的抽取结果进行验证，并处理少量需要进一步确认的情况。
5.  **输出：** 生成 `constraints_linked.json` 文件，供下游系统（Drools, KG, CG）使用。

**2. 人工预处理与标注指南**

**目标：** 为后续自动化流程提供明确、无歧义的锚点信息，减少系统的推断难度。

**建议的人工工作：**

1.  **文档清洗与结构化（可选但推荐）：**
    *   删除与约束描述无关的混乱信息、注释、非文本内容（如部分图表标记）。
    *   确保文档段落结构清晰，便于后续按章节或逻辑块处理。

2.  **核心标注：**
todo：-----可以编写脚本正则匹配来自动化处理-----编写正则匹配[TPS/constr]**(cid:100)**(cid:99),添加#@TPS/constr标注-----添加嵌套关系标注#@fatherID{***}---文中see chapter/in chapter等应该加上引到的那个类
    *   **类名标注 (`#@CLASS`)：**
        *   **目的：** 明确约束所涉及的主要 AUTOSAR 类。
        *   **样式：** 在描述某个特定类的约束之前或旁边，使用 `#@CLASS: [UML标准类名]`。
        *   **示例：**
            ```markdown
            #@CLASS: RunnableEntity
            约束 TPS_SWCT_01457 规定，对于一个可运行实体...
            ```
        *   **注意：** `[UML标准类名]` 必须与 `elements.json` 中的类名完全一致。

    *   **章节/Profile 标注 (`#@SECTION`, `#@PROFILE`) (可选)：**
        *   **目的：** 提供约束的上下文范围，有助于后续的范围界定或校验。
        *   **样式：**
            *   `#@SECTION: [章节标题或编号]`
            *   `#@PROFILE: [适用的Profile名称，如SWCT, RTE]`
        *   **示例：**
            ```markdown
            #@SECTION: 4.2.5 SwComponentType Constraints
            #@PROFILE: SWCT
            #@CLASS: SwComponentType
            一个软件组件类型必须有一个短名。
            ```

    *   **属性名精确标注 (`#@[UML标准类名].[UML标准属性名]`) (当文本描述模糊时推荐)：**
        *   **目的：** 当约束文本中对属性的描述可能产生歧义，或者使用了非标准别名时，直接提供标准属性路径。
        *   **样式：** 在约束文本中，紧跟在可能引起歧义的属性描述之后，或直接替换它，使用 `#@[UML标准类名].[UML标准属性名]`。
        *   **示例：**
            ```markdown
            ... 该实体的执行时间（#@RunnableEntity.length）不能超过...
            ```
            或者，如果文本中只说“长度”：
            ```markdown
            ... 其长度（#@RunnableEntity.length）不能超过...
            ```
        *   **注意：** 这个标注的优先级最高，如果存在，LLM 应直接使用它作为 `targetAttribute`。




**标注原则：**

*   **准确性优先：** 确保所有标注的名称和路径与 `elements.json` 中的定义严格一致。
*   **最小化但必要：** 只在可能产生歧义或自动化处理困难的地方进行标注。如果文本本身已经非常清晰且规范，则无需过度标注。
*   **一致性：** 在整个文档集或项目中保持标注样式的一致性。

**3. 系统流程详细设计**

**3.1 阶段一：上下文注入预处理 (`context_injector.py`)**

*   **输入：**
    *   经过人工标注的 Markdown/纯文本文档。
    *   `elements.json` (UML 元数据)。
*   **步骤：**
    1.  **文档分块与标注解析：**
        *   使用 `split_md.py` (或类似工具) 将文档按一定大小（如 300-500 tokens，可调整）分块，保持句子完整性。
        *   对于每个块，解析其中所有 `#@CLASS`, `#@SECTION`, 等元信息标注。优先识别当前块的“主要焦点类”（例如，块内第一个 `#@CLASS` 标注，或根据某种启发式规则）。
    2.  **属性上下文提取：**
        *   根据识别出的“主要焦点类”，查询 `elements.json`，获取该类的所有直接属性名称列表。
    3.  **上下文注入：**
        *   为每个文档块动态生成一段上下文描述文本。
        *   **示例注入文本：**
            ```
            --- CONTEXT START ---
            Focus Class: RunnableEntity
            Attributes for RunnableEntity: [symbol, length, exclusiveAreaNestingOrder, canBeInvokedConcurrently, ...]
            Document Section: 4.2.5 SwComponentType Constraints (if #@SECTION available)
            Constraint ID Hint: TPS_SWCT_01457 (if #@ID available in block)
            --- CONTEXT END ---
            [原始文档块内容，其中可能包含更细粒度的 #@CLASS.Attribute 或 #@PATH 标注]
            ```
        *   将此上下文描述文本添加到原始文档块的开头。
*   **输出：** 增强后的文档块列表，每个块都带有上下文信息。

**3.2 阶段二：LLM 约束抽取 (`llm_batch_extract_v3.py`)**

*   **输入：** 增强后的文档块列表。
*   **步骤：**
    1.  **Prompt 组装：**
        *   Prompt 应指导 LLM：
            *   优先使用注入的上下文信息（特别是焦点类及其属性列表）来确定 `targetClass` 和 `targetAttribute`。
            *   如果文本中存在 `#@[ClassName].[AttributeName]` 或 `#@PATH` 这样的精确标注，应直接采纳这些标注作为 `targetRef` (或其一部分)。
            *   抽取约束的 `id` (可参考上下文中的 Constraint ID Hint), `type`, `value`, `expression`, `scope`, 和 `confidence`。
        *   Few-shot 示例应包含带有注入上下文和精确标注的例子。
    2.  **Function Schema (`schema.json`)：**
        *   保持与 V2 类似，但 `targetClass` 和 `targetAttribute` (或合并为 `targetRef`) 的说明应强调优先采纳上下文和精确标注。
        *   可以考虑增加一个 `rawTargetText` 字段，用于存储 LLM 从原文中识别出的、未经对齐的类/属性文本，以备调试或辅助校验。
    3.  **API 调用：**
        *   模型：`gpt-4o-mini` 或更强模型。
        *   参数：`temperature=0.0` (或非常低的值)，`function_call="auto"`。
        *   异步并发调用。
*   **输出：** `constraints_raw_v3.jsonl`。由于上下文增强和精确标注的存在，此文件中的 `targetClass` 和 `targetAttribute` (或 `targetRef`) 字段的准确性预期会非常高。

**3.3 阶段三：轻量级 Linker 与校验 (`linker_validator_v3.py`)**

*   **输入：**
    *   `constraints_raw_v3.jsonl`。
    *   `elements.json`。
*   **目标：** 主要进行验证，而非复杂的歧义消除。
*   **步骤：**
    1.  **解析 `targetRef`：**
        *   如果 LLM 直接输出了 `targetRef` (基于 `#@PATH` 或 `#@[ClassName].[AttributeName]` 标注)，则直接使用。
        *   如果 LLM 输出的是 `targetClass` 和 `targetAttribute`，则组合成 `targetRef`。
    2.  **UML 元数据校验：**
        *   **存在性校验：** 验证 `targetRef` 中的类名和属性名 (以及路径中的中间步骤) 是否真实存在于 `elements.json` 中。
        *   **类型兼容性校验 (可选但推荐)：** 检查抽取的约束 `type` (如 `maxCardinality`) 和 `value` 是否与 `elements.json` 中对应属性的元数据 (如 `maxOccurs`, 数据类型) 相兼容。例如，不能对一个 `maxOccurs="1"` 的属性设置 `maxCardinality = 5`。
    3.  **处理少量模糊情况 (如果 LLM 未能基于上下文完全确定)：**
        *   如果 LLM 抽取的 `targetAttribute` 仍然存在模糊性（尽管概率已大大降低），可以启用一个非常简化的打分机制（可能只基于词形相似度和上下文提供的属性列表）或直接标记为人工复核。
        *   **不再需要复杂的 `alias_dict.pkl` 和多特征语义打分作为主要流程。**
    4.  **置信度调整：** 根据校验结果和 LLM 的原始置信度，调整最终的置信度评分。校验通过的可以保持或提高置信度。
*   **输出：**
    *   `constraints_linked_v3.json` (高质量的结构化约束数据)。
    *   `review_queue_v3.csv` (需要人工复核的极少数约束)。

**3.4 阶段四：约束数据模型与 Drools 映射**

*   与 `design_docV2.md` 中的定义基本保持一致。
*   `targetRef` 字段的质量将是最高的。

**4. 质量指标 (预期)**

| 指标                 | 期望 (V3) | V2 期望 | 说明                                   |
| -------------------- | --------- | ------- | -------------------------------------- |
| 块级召回率             | ≥ 0.97    | ≥ 0.95  | 上下文增强有助于 LLM 更好理解         |
| 字段完整率             | ≥ 0.98    | ≥ 0.95  | 目标更明确                               |
| **`targetRef` 准确率** | **≥ 0.98**| (N/A)   | 核心提升，基于人工标注和上下文          |
| Linker 自动对齐率    | (N/A)     | ≥ 0.85  | Linker 角色转为验证为主，此指标意义减弱 |
| **整体自动通过率**     | **≥ 0.95**| (N/A)   | LLM抽取+轻量校验后无需人工复核的比例 |
| 人工复核率             | ≤ 0.05    | ≤ 0.15  | 大幅降低                               |

**5. 关键技术栈调整**

*   增加：文档预处理器 (`context_injector.py`)，用于解析人工标注和注入上下文。
*   简化：Linker 模块 (`linker_validator_v3.py`) 的逻辑，减少对复杂相似度计算和别名词典的依赖。
*   LLM Prompt Engineering：需要针对新的上下文注入格式进行调整。

**6. 总结与优势**

V3.0 流程通过引入可控的人工预标注和智能的上下文注入，旨在：

*   **大幅提升核心信息 (`targetRef`) 的抽取准确性。**
*   **显著降低对复杂 Linker 算法和人工后期复核的依赖。**
*   **使 LLM 的行为更可预测和可控。**
*   **整体上提高约束抽取流程的效率和最终产出质量。**

虽然增加了前期的人工标注成本，但预期通过后端自动化效率和准确性的提升，能够获得更高的整体投资回报率，尤其是在处理大量或复杂 AUTOSAR 文档时。