# AUTOSAR规范约束提取系统

### 1. 项目概述

AUTOSAR规范约束提取系统是一个自然语言处理工具，旨在从AUTOSAR技术规范文档中自动提取结构化的约束和规范条目。系统结合了spaCy的NLP能力与AUTOSAR元数据知识库，实现了高效的约束识别和语义解析。

### 2. 文件功能说明

#### 2.1 主要模块

| 文件名 | 主要功能 |
|-------|--------|
| `main.py` | 主程序入口，协调各模块工作流程，处理命令行参数 |
| `document_processor.py` | 文档加载与预处理，处理特殊字符和重建段落 |
| `constraint_extractor.py` | 约束块识别与提取，使用正则表达式匹配约束模式 |
| `entity_recognizer.py` | 实体识别，基于元数据构建术语表并识别文本中的AUTOSAR实体 |
| `logic_analyzer.py` | 约束逻辑分析，解析条件、禁止、范围等语义结构 |
| `constraint_mapper.py` | 约束结构化映射，将分析结果转换为标准JSON结构 |
| `models.py` | 数据模型定义，包含各种约束和实体的数据类 |
| `utils.py` | 通用工具函数，包含正则模式、文件操作等辅助功能 |

#### 2.2 核心数据模型 (`models.py`)

- `Entity`: 表示识别出的AUTOSAR实体（类、属性、枚举值）
- `ConstraintRaw`: 从文档中提取的原始约束信息
- `ConstraintStructured`: 最终结构化的约束输出
- 各种表达式类：如`ConditionExpression`、`ProhibitionExpression`等

#### 2.3 辅助功能 (`utils.py`)

- 预定义的正则表达式模式
- JSON文件操作函数
- 文本标准化和清理函数

### 3. 处理流程

#### 3.1 整体流程

```
文档加载 → 预处理 → 约束提取 → 实体识别 → 逻辑分析 → 结构化映射 → 保存结果
```

#### 3.2 详细流程

1. **初始化阶段**
   - 加载命令行参数
   - 初始化各处理模块
   - 验证输入文件和目录

2. **文档处理** (`document_processor.py`)
   - 加载规范文档
   - 标准化特殊字符
   - 重建可能被错误分割的段落

3. **约束提取** (`constraint_extractor.py`)
   - 使用正则表达式查找约束块
   - 分离约束ID、标题、正文和引用ID
   - 提取额外的解释文本

4. **实体识别** (`entity_recognizer.py`)
   - 从元数据构建术语表和匹配器
   - 识别文本中的类名、属性名和枚举值
   - 处理属性路径和特殊模式

5. **逻辑分析** (`logic_analyzer.py`)
   - 确定约束类型
   - 提取条件表达式
   - 识别禁止性语句
   - 分析不重叠约束
   - 提取许可表达式和作用范围

6. **结构映射** (`constraint_mapper.py`)
   - 根据约束类型选择合适的映射逻辑
   - 构建标准化的JSON结构
   - 填充条件、禁止、范围等信息

7. **结果保存**
   - 将结构化约束转换为JSON格式
   - 保存到输出目录

### 4. 输入/输出规格

#### 4.1 输入

- **规范文档** (`input/autosar_spec.md`): AUTOSAR规范的文本内容
- **元数据文件** (`input/unified_metadata.json`): 融合的XMI和XSD元数据

#### 4.2 输出

- **结构化约束** (`output/structured_constraints.json`): 以JSON格式保存的结构化约束

### 5. 使用方法

#### 5.1 安装依赖

```bash
pip install spacy
python -m spacy download en_core_web_sm
```

#### 5.2 基本用法

```bash
python main.py
```

#### 5.3 高级用法

```bash
python main.py --input-dir custom_input --output-dir custom_output --spec-file other_spec.md --metadata-file other_metadata.json
```

### 6. 系统优势

- **基于知识库的实体识别**: 使用AUTOSAR元数据作为术语库，提高实体识别准确性
- **多层次约束解析**: 通过结合正则模式和依存句法分析，处理复杂约束表达
- **模块化设计**: 各组件可独立优化和升级
- **可扩展性**: 易于扩展以支持新的约束类型和模式

该系统提供了一个端到端的解决方案，能够将非结构化的AUTOSAR规范转换为结构化的约束定义，便于在知识图谱构建、一致性验证和规则引擎中使用。