**设计文档 V4：基于多维人工标注与严格上下文约束的 AUTOSAR 规范与约束抽取系统**

**版本：** 4.0
**日期：** 2025-05-13

**1. 项目概述**

本项目旨在从 AUTOSAR 相关文档（Markdown/纯文本）中自动抽取结构化的规范 (TPS) 和约束 (constr) 信息，并将其链接到标准的 UML 元模型及枚举定义。V4.0 版本引入了包括层级关系在内的多维人工标注体系，并对上下文注入和 LLM 行为施加严格约束，以实现高精度、结构化的信息抽取。

**核心流程：**

1.  **人工预处理与多维标注：** 领域专家在文档中添加 `#@CLASS`, `#@ENUM`, `#@SECTION`, `#@Hierarchical` 等标注。
2.  **上下文注入预处理：** 系统根据 `#@CLASS` 和 `#@ENUM` 标注，从元数据中提取相关类的属性及枚举的字面量，注入到文档块中。
3.  **LLM 约束抽取：** LLM 在严格的上下文指导下处理增强文档块，抽取规范/约束的各个组成部分，并区分其类型（TPS/constr）。
4.  **Linker 与校验：** 对 LLM 的抽取结果进行验证，并确认层级关系。
5.  **输出：** 生成 `constraints_linked_v4.json` 文件。

**2. 人工预处理与标注指南 (V4)**

**目标：** 为自动化流程提供明确、无歧义的锚点和结构信息。

**标注类型：**

1.  **章节标注 (`#@SECTION`)：**
    *   **目的：** 提供约束的上下文范围。
    *   **样式：** `#@SECTION: [章节标题或编号]`
    *   **示例：** `#@SECTION: 3.3.1 Overview`

2.  **类名标注 (`#@CLASS`)：**
    *   **目的：** 明确规范/约束所涉及的主要 AUTOSAR 类。
    *   **样式：** `#@CLASS: [UML标准类名]`
    *   **示例：** `#@CLASS: CompositionSwComponentType`
    *   **注意：** `[UML标准类名]` 必须与 `unified_metadata.json` 中的类名一致。

3.  **枚举名标注 (`#@ENUM`)：**
    *   **目的：** 明确规范/约束所涉及的 AUTOSAR 枚举类型。
    *   **样式：** `#@ENUM: [UML标准枚举名]`
    *   **示例：** `#@ENUM: SwImplPolicyEnum`
    *   **注意：** `[UML标准枚举名]` 必须与元数据中的枚举名一致。

4.  **层级关系标注 (`#@Hierarchical`)：**
    *   **目的：** 标记紧随其后的文本块（通常是一个约束或规范）是其逻辑上上一个非层级元素的子项。用于表达文档或约束间的缩进/从属关系。
    *   **样式：** 单独一行 `#@Hierarchical`，置于子项文本之前。
    *   **示例：**
        ```markdown
        [TPS_SWCT_01000] A component must have a shortName. (cid:100)...(cid:99)
        #@Hierarchical
        [constr_SWCT_01001] The shortName must follow naming conventions. (cid:100)...(cid:99)
        ```
        此处 `constr_SWCT_01001` 是 `TPS_SWCT_01000` 的子约束。

**标注原则：** 准确性、最小化但必要、一致性。

**3. 系统流程详细设计 (V4)**

**3.1 阶段一：上下文注入预处理 (`context_injector_v4.py`)**

*   **输入：**
    *   经过人工标注的 Markdown/纯文本文档。
    *   `unified_metadata.json` (包含类及其属性，枚举及其字面量)。
*   **步骤：**
    1.  **文档分块与标注解析：**
        *   按适宜大小（如 300-500 tokens）分块，保持句子完整性。
        *   对于每个块，解析其中所有 `#@SECTION` 标注。
        *   **扫描并收集实体：** 扫描当前块及其小范围上下文（如前后块）内的所有 `#@CLASS: [ClassName]` 和 `#@ENUM: [EnumName]` 标注。
    2.  **元数据提取：**
        *   对于收集到的每个 `[ClassName]`，从 `unified_metadata.json` 查询并获取其所有属性 (elements) 列表。
        *   对于收集到的每个 `[EnumName]`，从 `unified_metadata.json` 查询并获取其所有字面量 (literals) 列表。
    3.  **上下文注入：**
        *   为每个文档块动态生成上下文描述文本。
        *   **示例注入文本：**
            ```
            --- CONTEXT START ---
            Document Section: 3.3.1 Overview (if #@SECTION available)
            Referenced Classes:
              - ClassName1: Attributes [attr1, attr2, ...]
              - ClassName2: Attributes [attrA, attrB, ...]
            Referenced Enums:
              - EnumName1: Literals [LITERAL_A, LITERAL_B, ...]
            --- CONTEXT END ---
            [原始文档块内容，其中包含规范/约束文本及 #@Hierarchical, #@CLASS, #@ENUM 标注]
            ```
*   **输出：** 增强后的文档块列表。

**3.2 阶段二：LLM 约束抽取 (`llm_batch_extract_v4.py`)**

*   **输入：** 增强后的文档块列表。
*   **核心LLM Prompt指令：**
    *   "针对文档中每个格式为 `[ID_TYPE_ID_NUMBER] Title (cid:100) Details (cid:99)(References)` 的规范或约束进行抽取。"
    *   "**ID与类型：** 从 `[ID_TYPE_ID_NUMBER]` 中提取 `id` (完整ID字符串) 和 `id_type` ('TPS_SWCT' 或 'constr')。"
    *   "**标题：** 提取 `Title` 部分。"
    *   "**细则：** 提取 `Details` 部分作为 `expression`。"
    *   "**引用：** 提取 `(References)` 中的所有ID作为 `references` 列表。"
    *   "**目标实体确定：**
        *   查看紧邻当前规范/约束文本之前的 `#@CLASS: ClassName` 或 `#@ENUM: EnumName` 标注。以此确定 `targetClass` 或 `targetEnum`。
        *   如果两者都存在，优先考虑更近的或根据启发式规则（例如，如果文本内容更倾向于描述类属性则选Class，如果描述枚举值则选Enum）。"
    *   "**目标属性/字面量确定 (严格规则)：**
        *   如果目标是类 (`targetClass`)：查看注入的 `---CONTEXT START---` 中 `Referenced Classes` 下对应 `ClassName` 的 `Attributes` 列表。当前规范/约束文本中提及的属性**必须**在该列表中。如果找到，则设为 `targetAttribute`。
        *   如果目标是枚举 (`targetEnum`)：查看注入的 `---CONTEXT START---` 中 `Referenced Enums` 下对应 `EnumName` 的 `Literals` 列表。当前规范/约束文本中提及的字面量**必须**在该列表中。如果找到，则设为 `targetAttribute` (或 `targetLiteral`，schema中统一为 `targetAttribute`)。
        *   **禁止推测：** 如果文本中提及的属性/字面量**不在**对应实体（类/枚举）的上下文注入的属性/字面量列表中，**绝不能自行推测或创造**。
        *   **类/枚举级别默认：** 在上述“禁止推测”的情况下，或规范/约束本身明确是针对整个类/枚举的，则将 `targetAttribute` 设置为特殊值 `_classLevel` (对于类) 或 `_enumLevel` (对于枚举)。"
    *   "**层级关系：** 如果当前规范/约束之前紧邻 `#@Hierarchical` 标注，尝试将前一个抽取的非层级规范/约束的 `id` 作为本条记录的 `parent_id`。"
    *   "抽取其他相关字段如 `type` (约束类型，如cardinality, range等), `value`。"
*   **Function Schema (`schema_v4.json`)：** 见第4节。
*   **API 调用：** 模型 `gpt-4o-mini` 或更强，`temperature=0.0`。
*   **输出：** `constraints_raw_v4.jsonl`。

**3.3 阶段三：Linker 与校验 (`linker_validator_v4.py`)**

*   **输入：** `constraints_raw_v4.jsonl`, `unified_metadata.json`。
*   **步骤：**
    1.  **解析与组合 `targetRef`：**
        *   如果 `targetAttribute` 是 `_classLevel`，则 `targetRef` 为 `[targetClass]._classLevel`。
        *   如果 `targetAttribute` 是 `_enumLevel`，则 `targetRef` 为 `[targetEnum]._enumLevel`。
        *   否则，`targetRef` 为 `[targetClass].[targetAttribute]` 或 `[targetEnum].[targetAttribute]`。
    2.  **UML元数据校验：**
        *   **实体存在性：** 校验 `targetClass` 或 `targetEnum` 是否在 `unified_metadata.json` 中。
        *   **属性/字面量存在性 (LLM遵循性校验)：** 如果 `targetAttribute` 不是 `_classLevel` 或 `_enumLevel`，校验其是否是对应类/枚举的合法属性/字面量。
        *   **类型兼容性校验：** (同V3) 检查约束 `type` 和 `value` 与元数据定义是否兼容。
    3.  **ID类型与格式校验：** 验证 `id_type` 是否为 "TPS_SWCT" 或 "constr"，验证 `id` 格式。
    4.  **层级关系校验：** 如果存在 `parent_id`，校验具有该 `id` 的父约束是否存在于已处理的集合中。
    5.  **置信度调整。**
*   **输出：** `constraints_linked_v4.json`, `review_queue_v4.csv`。

**4. 约束数据模型与Schema (`schema_v4.json` 示例)**

```json
{
  "type": "object",
  "properties": {
    "id": { "type": "string", "description": "完整的规范/约束ID，如 TPS_SWCT_01032 或 constr_XYZ_001" },
    "id_type": { "type": "string", "enum": ["TPS_SWCT", "constr"], "description": "ID的类型" },
    "title": { "type": "string", "description": "规范/约束的标题文本" },
    "targetClass": { "type": ["string", "null"], "description": "约束目标AUTOSAR类名 (如果目标是类)" },
    "targetEnum": { "type": ["string", "null"], "description": "约束目标AUTOSAR枚举名 (如果目标是枚举)" },
    "targetAttribute": { "type": "string", "description": "约束目标的具体属性/字面量名，或特殊值 '_classLevel', '_enumLevel'" },
    "targetRef": { "type": "string", "description": "组合后的目标引用路径，如 ClassName.AttrName, EnumName.LiteralName, ClassName._classLevel" },
    "expression": { "type": "string", "description": "约束的详细文本描述 (cid:100) 和 (cid:99) 之间的内容" },
    "references": {
      "type": "array",
      "items": { "type": "string" },
      "description": "约束末尾括号中引用的其他ID列表"
    },
    "constraint_type": { "type": "string", "description": "约束的语义类型 (如 cardinality, value_restriction, definition, etc.)" }, // Renamed from "type" to avoid conflict
    "value": { "type": ["string", "number", "boolean", "null"], "description": "约束的具体值" },
    "scope": {
      "type": "object",
      "properties": {
        "section": { "type": ["string", "null"] },
        "parent_id": { "type": ["string", "null"], "description": "如果通过 #@Hierarchical 标注识别，则为父约束的ID" }
      }
    },
    "rawSourceText": { "type": "string", "description": "LLM处理的原始约束文本块"},
    "confidence": { "type": "number", "minimum": 0, "maximum": 1 }
  },
  "required": ["id", "id_type", "title", "expression", "targetRef"]
}
```

**5. 处理层级约束 (`#@Hierarchical`)**

`#@Hierarchical` 标注用于显式声明文档结构中的从属关系。

*   **LLM 抽取：** 当 LLM遇到此标注时，它会尝试将紧随其后的约束的 `parent_id` 字段设置为前一个成功抽取的、非 `#@Hierarchical` 标记的约束的 `id`。
*   **Linker/Validator：** 可以验证 `parent_id` 指向的约束确实存在。
*   **下游应用：** `parent_id` 字段允许下游系统（如知识图谱构建、规则引擎）重建约束间的层级结构，这对于理解复杂规范非常重要。

**6. 质量指标 (预期 V4)**

| 指标                   | 期望 (V4) | 说明                                                                 |
| ---------------------- | --------- | -------------------------------------------------------------------- |
| 块级召回率             | ≥ 0.98    | 上下文和标注更明确                                                       |
| 字段完整率             | ≥ 0.99    | 结构更清晰                                                             |
| **`targetRef` 准确率** | **≥ 0.99**| 严格基于上下文，LLM不推测，大幅提升                                        |
| **`id_type` 准确率**   | **≥ 0.99**| 基于明确的ID格式                                                        |
| **层级关系捕获率**     | ≥ 0.95    | 基于 `#@Hierarchical` 标注，主要取决于标注质量                         |
| 整体自动通过率         | ≥ 0.97    | 由于LLM行为受严格约束，后续校验通过率高                                    |
| 人工复核率             | ≤ 0.03    | 显著降低，主要处理标注错误或极复杂边缘情况                               |

**7. 关键技术栈调整**

*   **`context_injector_v4.py`:** 逻辑增强，以处理 `#@CLASS` 和 `#@ENUM` 并从元数据提取相应信息。
*   **`llm_batch_extract_v4.py`:** Prompt Engineering 是核心，需严格指导 LLM 遵循上下文、区分ID类型、处理层级。
*   **`linker_validator_v4.py`:** 校验逻辑调整，以匹配新的 schema 和 LLM 行为。
*   **`unified_metadata.json`:** 需要确保包含类、属性、枚举、字面量的完整信息。

**8. 总结与优势 (V4)**

V4.0 通过引入更丰富的标注体系（特别是 `#@Hierarchical` 和 `#@ENUM`）和对 LLM 行为的严格上下文限定，旨在：

*   **空前提升 `targetRef` 的准确性：** LLM 被禁止在上下文之外推测属性/字面量。
*   **准确区分规范 (TPS) 与约束 (constr)。**
*   **捕获约束间的层级关系，** 提供更丰富的结构化信息。
*   **进一步降低人工复核的需求，** 提高整体流程效率和产出质量。
*   使 LLM 的输出更加可预测、可控且符合预定义的元数据结构。

虽然对人工标注的精细度要求更高，但通过后端自动化流程的极高准确性和结构化输出的丰富性，预计将为知识图谱构建和规则系统集成带来显著的价值提升。
