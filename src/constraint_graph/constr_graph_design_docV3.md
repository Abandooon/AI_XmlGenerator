## constraint\_graph 设计文档（v3.1 — 2025‑06‑23）

> **关键词：** 单源真相 / 扁平快照 / 真 DFA / 逐步硬约束 / 三段防线 / *跨实体关系*
>
> v3.1 在 v3.0 的基础上 **补全“关系型约束”**（cross‑entity / implies），实现从 KG → SMT 的自动转换，并更新约束‑产物映射。

---

### 1 变更概览（v3.0 → v3.1）

| 主题                      | v3.0                          | **v3.1 改动**                                           |
| ----------------------- | ----------------------------- | ----------------------------------------------------- |
| **Relation Constraint** | 仅识别 `implies` 字段              | + 支持 JSON DSL：`{"if": A, "then": B}`<br>+ 跨类存在性、跨属性依赖 |
| **smt\_exporter.py**    | `_existence / _range / _enum` | + `_relation()`  → 生成 `=>` 子句、实例化函数                   |
| **文档**                  | 无专节                           | + §10 “关系型约束示例与转换”                                    |

---

### 2 总体架构（v3.1）

```mermaid
graph TD
  subgraph Extraction
      KG[(Neo4j / JSON)] --> L[loader]
      L --> RA[raw_attributes.jsonl]
      L --> RC[raw_constraints.jsonl]
      L --> RCL[raw_classes.jsonl]
      L --> RE[raw_enums.jsonl]
  end
  subgraph Canonical
      RA & RC & RE --> C[canonicalizer]
      C --> EC[canonical_constraints.json]
      C -->|enrich| EN[enriched_constraints.json]
  end
  subgraph Export
      EN --> G[GrammarExporter] --> GB[autosar.gbnf]
      GB --> D[dfa_compiler] --> FSM[autosar.fsm]
      D --> PY[autosar_allowed_tokens.py]
      EN --> S[ShaclExporter] --> TTL[autosar_shapes.ttl]
      EN --> M[SmtExporter]   --> SMT[constraints.smt2]
  end
```

---

### 3 文件与约束类型映射

| 产物文件                            | **约束字段**                                    | 转换链路 & 用途                                                  |
| ------------------------------- | ------------------------------------------- | ---------------------------------------------------------- |
| **autosar.gbnf**                | `enum`, `(maxOccurs==1 ∧ enum=None)`        | GrammarExporter → LLM 解析器强语法                               |
| **autosar.fsm**                 | GBNF 全量终端                                   | dfa\_compiler → 前缀 DFA 状态机                                 |
| **autosar\_allowed\_tokens.py** | 同上                                          | dfa\_compiler → 推理期 `allowed(prefix)`                      |
| **autosar\_shapes.ttl**         | `range`, `regex`, `min/maxOccurs`           | ShaclExporter → 生成后轻量验证 (pySHACL)                          |
| **constraints.smt2**            | `range`, `relation`, `implies`, `cross‑ref` | SmtExporter → Z3/CVC5 深度验证；关系型约束以 `=>`, `and`, `exists` 编译 |
| **raw\_\*.jsonl**               | KG 原生属性                                     | 所有下游导出基线；支持行级哈希增量                                          |

> **关系型约束**（relation）示例：
>
> ```json
> { "if": "BswM.Mode==OFF", "then": "Swc.Category in {APPLICATION}" }
> ```
>
> 由 SmtExporter 编译为：
>
> ```smt2
> (assert (forall ((pkg Pkg))
>   (=> (= (BswM_Mode pkg) OFF)
>       (= (Swc_Category pkg) APPLICATION))))
> ```

---

### 4 dfa\_compiler 关键算法（摘要）

```python
# 1. GBNF → EBNF 预处理
ebnf = gbnf_to_ebnf(gbnf_txt)
parser = Lark(ebnf, parser="lalr", start="ROOT")

# 2. 遍历 Lark 状态 → DFA
dfa = {}
frontier = [()]
while frontier:
    prefix = frontier.pop()
    allow  = allowed_terms(parser, prefix)
    dfa[prefix] = allow
    if len(prefix) < MAX_DEPTH:
        frontier.extend(prefix+(t,) for t in allow)

# 3. dump FSM + allowed_tokens.py
```

---

### 5 关系型约束转换逻辑

| DSL 字段                 | 例子                                           | SMT 片段                                              | 备注      |
| ---------------------- | -------------------------------------------- | --------------------------------------------------- | ------- |
| `{"if": A, "then": B}` | `if: ClassA.flag==1`<br>`then: ClassB.exist` | `(=> (= Flag 1) (exists ((b B)) (ClassB_exist b)))` | 跨类存在性   |
| `requires`             | `Swc.port requires OsApplication`            | `(=> (PortExist p) (OsApplicationExist app))`       | 支持多对多   |
| `mutex`                | `AttrX mutex AttrY`                          | `(not (and X Y))`                                   | 编译成互斥断言 |

---

### 6 运行时接口

同 v3.0，不变。

---

### 7 测试清单（新增）

| 测试                      | 断言                                  |
| ----------------------- | ----------------------------------- |
| `test_relation_implies` | `if/then` SMT 模型可被求解；反例模型返回 `unsat` |
| `test_mutex`            | 两互斥属性同为真时模型 `unsat`                 |
| `test_dfa_closed`       | `allowed(prefix)` 集合闭合              |

---

### 8 后续路线图

1. **range‑to‑enum 自动化**：对 `range:size≤256` 内的区间直接列枚举 → GBNF → DFA。
2. **unsat‑core 反馈**：把 Z3 反例回写 Neo4j，驱动数据修复循环。
3. **IDE LSP 插件**：在 XML 编辑器中实时调用 `allowed_prefix` 完成上下文检查。

---

*v3.1 完*
