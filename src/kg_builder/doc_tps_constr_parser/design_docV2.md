# LLM 约束抽取 & Linker 对齐——操作说明

> **目标**：将 Markdown/纯文本片段中的 AUTOSAR 约束句转为统一 `constraints_linked.json`，供 Drools / KG / CG 后续使用。
>
> **覆盖范围**：
>
> 1. *llm\_batch\_extract.py* —— 调用 GPT‑4o function‑calling 批量抽取
> 2. *linker.py* —— 把抽取结果映射到唯一的 UML `Class.Attribute`

---

## 1  LLM 抽取流程

| 步骤                      | 说明                                                                                                | 关键参数                        |
| ----------------------- | ------------------------------------------------------------------------------------------------- | --------------------------- |
| **1.1 分块**              | `split_md.py`：按 **300 tokens + 30 tokens overlap** 切 `docs_md/*.md`，保持句子不被截断                      | `MAX_TOK=300`, `OVERLAP=30` |
| **1.2 Prompt 组装**       | 每块 prepend 标识头：`<DOC=42 CHUNK=03/17>`；拼接 FEW‑SHOT（3–5 条多样示例）                                      | Few‑shot 文档：`few_shot.md`   |
| **1.3 Function Schema** | 统一 `extract_constraint` schema：`id, type, targetClass, targetAttribute, value, scope, confidence` | 见 `schema.json`             |
| **1.4 API 调用**          | `gpt-4o-mini`, `temperature=0.0`, `function_call="auto"`, **异步并发** (≤ 100 rps)                    | `openai.AsyncOpenAI`        |
| **1.5 原始输出**            | 写入 `constraints_raw.jsonl` —— 每行一个 JSON object                                                    | 典型字段见 §1.6                  |

### 1.6 例子

```jsonc
{
  "id": "TPS_SWCT_01457",
  "type": "mustHave",
  "targetClass": "RunnableEntity",
  "targetAttribute": "exclusiveAreaNestingOrder",
  "value": null,
  "scope": {"profile": "SWCT"},
  "confidence": 0.91
}
```

> *Tip*：抽取时不强行要求“官方 UML 名称”，保留文本别名；交由 Linker 对齐。

---

## 2  Linker 对齐流程

### 2.1 输入

* `constraints_raw.jsonl`
* `elements.json` & `alias_dict.pkl`（由 `parse_uml.py` 生成）

### 2.2 候选召回

```python
cands = alias_dict.get(attr_name)  # "runnable" → 多个 class.attr 列表
```

### 2.3 多特征打分

| 特征                  | 权重  | 计算方式                               |
| ------------------- | --- | ---------------------------------- |
| 词形相似 (Jaro‑Winkler) | 0.4 | `jellyfish.jaro_winkler()`         |
| 语义相似 (MiniLM)       | 0.3 | `cos(embed(m), embed(cand))`       |
| Profile/章节先验        | 0.1 | 同章节 / same profile +0.1            |
| 类焦点 (最近引用)          | 0.1 | 若 `cand.class == focus_class` +0.1 |
| Occurs/Datatype 兼容  | 0.1 | 约束类型与 UML 元属性匹配 +0.1               |

```python
score = sum(w*f for w,f in zip(weights, features))
```

*阈值*：`score ≥ 0.80` → 自动接受；`0.50–0.80` → `review_queue.csv`；`<0.50` 丢弃。

### 2.4 校验 & 补全

* 若约束类型为 `maxCardinality` 但候选属性 `maxOccurs="1"` → 降分。
* 检查导航属性 (`resolvedType` 等) 是否存在；不存在则进入人工复核。

### 2.5 输出格式

```jsonc
{
  "id": "TPS_SWCT_01457",
  "type": "mustHave",
  "targetClass": "RunnableEntity",
  "targetAttribute": "exclusiveAreaNestingOrder",
  "value": null,
  "scope": {"profile": "SWCT"},
  "confidence": 0.87
}
```

写入 `constraints_linked.json`，供 Drools / KG / CG 使用。

---

## 3  质量指标

| 指标           | 期望     |
| ------------ | ------ |
| 块级召回率        | ≥ 0.95 |
| 字段完整率        | ≥ 0.95 |
| Linker 自动对齐率 | ≥ 0.85 |
| 人工复核率        | ≤ 0.15 |

> **建议**：对低置信度样本构建 hard‑negative，再微调 cross‑encoder 以逐步提高自动对齐比例。



## 4  约束数据模型

> **说明**：以下模型假设元数据（`elements.json`）已提供所有类/属性的详细信息，因此约束对象只存**最小必要信息**：
>
> * `id` – 规范唯一编号；
> * `type` – 约束类别（决定 Drools 模板）；
> * `targetRef` – **完全限定路径** `Class.Attribute`（或仅 `Class`）；
> * `value` / `expression` – 数值或逻辑表达式；
> * 可选 `scope` / `confidence`。

```jsonc
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "AutosarConstraintMinimal",
  "type": "object",
  "required": ["id", "type", "targetRef"],
  "properties": {
    "id": {[todo_list](../../../todo_list)
      "type": "string",
      "description": "约束 ID，例如 TPS_SWCT_01457"
    },

    "type": {
      "type": "string",
      "enum": [
        "mustHave",           // 存在性
        "maxCardinality",     // 基数上限
        "minCardinality",     // 基数下限
        "upperBound",         // 数值 ≤ value
        "lowerBound",         // 数值 ≥ value
        "equivalence",        // A == B
        "conditionalExistence"// 条件存在性
      ]
    },

    "targetRef": {
      "type": "string",
      "description": "完全限定引用：<Class>[.<Attribute>]，如 SwcInternalBehavior.runnables"
    },

    "value": {
      "description": "上/下限或枚举值；不适用则省略",
      "type": ["number", "string", "null"],
      "default": null
    },

    "expression": {
      "description": "复杂条件或等价表达式，使用 targetRef 引用。示例： 'resolvedType.category == VALUE'",
      "type": ["string", "null"],
      "default": null
    },

    "scope": {
      "description": "可选作用域，如 profile",
      "type": "object",
      "properties": {
        "profile": {"type": "string"}
      },
      "additionalProperties": true,
      "default": {}
    },

    "confidence": {
      "type": "number",
      "minimum": 0,
      "maximum": 1,
      "default": 1.0,
      "description": "抽取+对齐置信度"
    }
  },
  "additionalProperties": false
}
```

### Drools 映射策略

| 字段           | 作用                       | 例子                                      |
| ------------ | ------------------------ | --------------------------------------- |
| `id`         | 规则名                      | `rule "TPS_SWCT_01457"`                 |
| `type`       | 选模板                      | `mustHave.ftl`, `maxCard.ftl` …         |
| `targetRef`  | 直接拆为 `class`、`attribute` | `SwcInternalBehavior` / `runnables`     |
| `value`      | 比较值                      | 上/下限、枚举                                 |
| `expression` | 生成额外 `when` 条件           | 解析 `${leftRef} ${op} ${rightRef/value}` |

> **注**：模板渲染阶段根据 `targetRef` 在 `elements.json` 内查找 `minOccurs/maxOccurs/xml_tag` 等详细元数据，无需在约束对象中重复存储。
