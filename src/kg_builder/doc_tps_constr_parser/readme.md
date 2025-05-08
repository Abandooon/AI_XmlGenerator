```markdown
# 文档约束处理流水线

## 1. 项目目的

本项目旨在处理文本文档（`.txt` 或 `.md` 格式），以提取、分析和结构化约束。该流水线包括几个阶段：文档预处理、原始约束提取、约束内实体识别、约束逻辑分析，最后将它们映射为结构化格式。

## 2. 目录结构

项目预期并创建以下目录结构：

```
.
├── input/                     # 输入文件目录
│   ├── unified_metadata.json  # 用于实体识别的元数据（可选，但推荐）
│   └── *.txt                  # 输入文档文件
│   └── *.md                   # 输入文档文件
├── output/                    # 最终输出文件目录
│   ├── debug/                 # 用于存储中间处理结果和日志的目录
│   │   ├── {文档基础名}_preprocessed.txt
│   │   ├── {文档基础名}_raw_constraints.json
│   │   ├── {文档基础名}_raw_constraints.txt
│   │   ├── {文档基础名}_entities.json
│   │   ├── {文档基础名}_entities.txt
│   │   ├── {文档基础名}_logic_analyses.json
│   │   ├── {文档基础名}_logic_analyses.txt
│   │   ├── {文档基础名}_structured_constraints.json
│   │   └── {文档基础名}_structured_constraints.txt
│   ├── extracted_constraints.txt
│   ├── structured_constraints.json
│   └── processing_stats.json
├── src/                       # 源代码目录 (示例)
│   ├── main.py                # 流水线主脚本
│   ├── document_processor.py  # 文档处理器
│   ├── flexible_extractor.py  # 约束提取器
│   ├── entity_recognizer.py   # 实体识别器
│   ├── logic_analyzer.py      # 逻辑分析器
│   ├── constraint_mapper.py   # 约束映射器
│   ├── models.py              # 数据模型
│   ├── logging_utils.py       # 日志工具
│   └── utils.py               # 通用工具
└── README.md                  # 本文件 (中文版为 README_zh.md)
```

*   **`input/`**: 将您的输入文档（`.txt`, `.md`）和 `unified_metadata.json` 文件放在此处。如果 `input/` 目录不存在，脚本将尝试创建它。
*   **`output/`**: 如果此目录不存在，将会被创建。它存储最终处理结果。
*   **`output/debug/`**: 如果此子目录不存在，将会被创建。它存储每个文档在处理的每个步骤中生成的中间文件，这对于调试非常有用。

## 3. 所需文件

*   **输入文档**: 包含待处理约束的文本文件（`.txt`）或 Markdown 文件（`.md`）。这些文件应放置在 `input/` 目录中。
*   **`input/unified_metadata.json`**: 此 JSON 文件供 `EntityRecognizer` 使用。它应包含有关实体组和简单类型的元数据。
    *   如果未找到此文件，将记录一条警告，并创建一个空的模板（`{"groups": {}, "simpleTypes": {}}`）。没有正确的元数据，实体识别功能将受限或被禁用。

## 4. 工作流程 / 流水线步骤

`main.py` 脚本执行以下工作流程：

1.  **初始化**:
    *   设置一个日志记录器，用于详细的步骤日志。
    *   定义并创建 `input`、`output` 和 `output/debug` 目录（如果它们不存在）。
    *   检查 `input` 目录中是否存在 `unified_metadata.json`。如果未找到，则创建一个空文件。
    *   扫描 `input` 目录以查找 `.txt` 和 `.md` 文档文件。

2.  **组件设置**:
    *   初始化以下处理组件：
        *   `DocumentProcessor`: 用于清理和准备文档文本。
        *   `FlexibleConstraintExtractor`: 用于识别和提取原始约束文本。
        *   `EntityRecognizer`: 用于在提取的约束中识别和标记实体（使用 `unified_metadata.json`）。如果初始化失败（例如，元数据问题），则跳过实体识别。
        *   `LogicAnalyzer`: 用于分析约束的逻辑结构（例如，条件、禁止）。
        *   `ConstraintMapper`: 用于将分析后的约束转换为最终的结构化格式。

3.  **文档处理循环**: 对找到的每个文档执行：
    *   **a. 预处理**:
        *   `DocumentProcessor` 读取并预处理文档内容。
        *   预处理后的内容保存到 `output/debug/{文档基础名}_preprocessed.txt`。
    *   **b. 原始约束提取**:
        *   `FlexibleConstraintExtractor` 处理预处理后的内容以提取原始约束。
        *   提取的原始约束以 JSON 格式保存到 `output/debug/{文档基础名}_raw_constraints.json`，并以人类可读的文本格式保存到 `output/debug/{文档基础名}_raw_constraints.txt`。
        *   收集这些原始约束以供进一步处理。
    *   **c. 实体识别**:
        *   如果启用了实体识别并且已提取原始约束：
            *   `EntityRecognizer` 处理每个原始约束以识别实体。
            *   当前文档中识别出的实体以 JSON 格式保存到 `output/debug/{文档基础名}_entities.json`，并以人类可读的文本格式保存到 `output/debug/{文档基础名}_entities.txt`。
            *   约束会用实体信息进行更新。
            *   累积在所有文档中找到的所有实体，用于最终统计。
    *   **d. 逻辑分析**:
        *   `LogicAnalyzer` 处理每个约束（现在可能已富含实体信息）以确定其逻辑结构（例如，类型、条件、范围）。
        *   当前文档的分析结果以 JSON 格式保存到 `output/debug/{文档基础名}_logic_analyses.json`，并以人类可读的文本格式保存到 `output/debug/{文档基础名}_logic_analyses.txt`。
    *   **e. 结构化映射**:
        *   `ConstraintMapper` 获取（富含实体的）约束及其逻辑分析结果，将它们映射为最终的 `ConstraintStructured` 对象。
        *   当前文档的结构化约束以 JSON 格式保存到 `output/debug/{文档基础名}_structured_constraints.json`，并以人类可读的文本格式保存到 `output/debug/{文档基础名}_structured_constraints.txt`。

4.  **最终输出生成**:
    *   **原始约束**: 从所有文档中提取的所有原始约束被汇总，并以人类可读的格式保存到 `output/extracted_constraints.txt`。
    *   **结构化约束**: 来自所有文档的所有结构化约束被汇总，并以 JSON 格式保存到 `output/structured_constraints.json`。最终的 JSON 对象会过滤掉 null 值。
    *   **处理统计**: 处理运行的摘要（时间戳、文档数量、文档名称列表、原始和结构化约束的数量、实体识别状态以及找到的实体总数）保存到 `output/processing_stats.json`。

## 5. 输出文件

### 调试文件 (位于 `output/debug/`)

对于每个输入文档（例如 `mydoc.txt`），会生成以下中间文件：

*   **`mydoc_preprocessed.txt`**: 文档经过初始清理和预处理后的内容。
*   **`mydoc_raw_constraints.json`**: 从文档中提取的原始约束，JSON 格式。
*   **`mydoc_raw_constraints.txt`**: 原始约束，人类可读的文本格式。
*   **`mydoc_entities.json`**: 在文档约束中识别出的实体，JSON 格式。
*   **`mydoc_entities.txt`**: 识别出的实体，人类可读的文本格式，按约束分组。
*   **`mydoc_logic_analyses.json`**: 每个约束的逻辑分析结果，JSON 格式。
*   **`mydoc_logic_analyses.txt`**: 逻辑分析结果，人类可读的文本格式。
*   **`mydoc_structured_constraints.json`**: 映射到最终结构化格式的约束，JSON 格式。
*   **`mydoc_structured_constraints.txt`**: 结构化约束，人类可读的文本格式。

### 最终输出文件 (位于 `output/`)

*   **`extracted_constraints.txt`**: 从所有已处理文档中提取的所有原始约束的汇编，人类可读格式。
*   **`structured_constraints.json`**: 一个 JSON 数组，包含来自所有已处理文档的所有结构化约束。
*   **`processing_stats.json`**: 包含有关已完成处理运行统计信息的 JSON 文件。

## 6. 如何运行

1.  **先决条件**:
    *   确保已安装 Python 3.x。
    *   安装所有必需的依赖项（例如，如果导入的模块如 `entity_recognizer` 中使用了特定的 NLP 库）。通常，您会有一个 `requirements.txt` 文件。如果没有，请检查 Python 文件中的 import 语句以了解外部库。

2.  **准备输入**:
    *   在与 `src` 目录相同的位置（或 `main.py` 将运行的位置）创建一个 `input` 目录。
    *   将您的 `.txt` 或 `.md` 文档文件放入 `input` 目录。
    *   如果使用实体识别，请将格式正确的 `unified_metadata.json` 文件放入 `input` 目录。

3.  **执行脚本**:
    导航到包含 `main.py` 的目录（例如 `src/`）或其父目录（如果作为模块运行），然后运行：
    ```bash
    python main.py
    ```
    （如果 `main.py` 在 `src` 文件夹内，而您在项目根目录，则可以运行 `python src/main.py`）

4.  **检查输出**:
    *   执行后，检查 `output/` 目录以获取最终结果，并检查 `output/debug/` 目录以获取中间文件和日志。
    *   控制台输出也将提供该过程的逐步日志记录。

```