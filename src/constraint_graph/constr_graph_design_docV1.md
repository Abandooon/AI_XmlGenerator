## constraint\_graph 设计文档（v1.1）

> **适用范围**
> 从已构建的知识图（KG）中抽取 `(:Constraint)-[:CONSTRAINS]->(...)` 片段，
> 生成 **强 CGD** 与 **三层验证** 所需的全部产物：
> `autosar.gbnf → autosar.fsm & autosar_allowed_tokens.py → autosar_shapes.ttl → constraints.smt2`

---

### 1. 设计目标

| 需求         | 设计要点                                                                     |
| ---------- | ------------------------------------------------------------------------ |
| **输入灵活**   | 既支持离线 `kg_nodes.json / kg_edges.json`，也能直连 **Neo4j Desktop** (`bolt://`) |
| **增量导出**   | 约束改动无需重跑 KG；通过 `hash` 判断增量，未来易缓存                                         |
| **多产物一致性** | 一份 canonical JSON 同时渲染 GBNF / DFA / SHACL / SMT，避免分叉                     |
| **易集成**    | 暴露 **函数式 API** `export(kg_uri, out_dir)` 及 CLI 子命令                       |
| **零侵入**    | 不修改 `kg_builder`；仅「读」KG，不写回                                              |

---

### 2. 总体架构

```mermaid
graph TD
  A[KG (Neo4j 或 JSON)] -->|loader| B[raw constraints]
  B -->|canonicalizer| C[canonical_constraints.json (内存)]
  C --> D1[GrammarExporter]
  C --> D2[ShaclExporter]
  C --> D3[SmtExporter]
  D1 -->|GBNF| E[autostar.gbnf]
  E -->|dfa_compiler| F[autosar.fsm, autosar_allowed_tokens.py]
```

---

### 3. 模块说明

| 模块                       | 主要职责                                                                               | 关键实现点                                                   |
| ------------------------ | ---------------------------------------------------------------------------------- | ------------------------------------------------------- |
| **loader.py**            | 从 KG 读取约束<br>• `bolt` 分支: Cypher 查询<br>• `json` 分支: 读本地文件                          | 懒加载 `neo4j-driver`; synthesize 与 JSON 兼容的 `nodes/edges` |
| **canonicalizer.py**     | 自然语言 → 语义封闭 JSON<br>填 `type / targets / minOccurs / enum / hash`                   | 简易规则 + 正则；留 `unknown` 供人工回查                             |
| **grammar\_exporter.py** | 枚举≤1 → GBNF 规则                                                                     | 追加到 `autosar.gbnf`                                      |
| **dfa\_compiler.py**     | GBNF → DFA → stub                                                                  | 目前写占位；预留真实 pegen/lark                                   |
| **shacl\_exporter.py**   | `sh:in + sh:maxCount` TTL                                                          | 直接写 Turtle                                              |
| **smt\_exporter.py**     | `(assert (or ...))` + `(check-sat)`                                                | 支持多约束共用变量                                               |
| **cli.py**               | • CLI：`export --kg … --out …`<br>• 函数：`export(kg_uri, out_dir)`<br>• 无参数运行 → 读环境变量 | 便于 PyCharm *Run* 按钮                                     |

---

### 4. 数据格式

#### 4.1 Canonical Constraint 片段

```json
{
  "cid": "constr_1311",
  "type": "cardinality",
  "targets": ["MemorySection.option","SwAddrMethod.option"],
  "minOccurs": 0,
  "maxOccurs": 1,
  "enum": ["safetyQM","safetyAsilA","safetyAsilB","safetyAsilC","safetyAsilD"],
  "hash": "a3c4e9d1afce"
}
```

#### 4.2 产物文件

| 文件                          | 用途                              |
| --------------------------- | ------------------------------- |
| `autosar.gbnf`              | vLLM 强 CGD 语法                   |
| `autosar.fsm`               | 前缀闭包 DFA 状态表（占位可替换）             |
| `autosar_allowed_tokens.py` | `prefix_allowed_tokens_fn` Stub |
| `autosar_shapes.ttl`        | pySHACL 语义验证                    |
| `constraints.smt2`          | Z3/CVC5 逻辑验证                    |

---

### 5. 运行方式

#### 5.1 PyCharm

```
Script : src/constraint_graph/cli.py
Parameters : (空)
Env       : KG_URI=bolt://localhost:7687
            OUT_DIR=out/cg
            NEO4J_USER=neo4j
            NEO4J_PASS=****** 
```

#### 5.2 命令行

```bash
python -m constraint_graph.cli export --kg bolt://localhost:7687 --out out/cg
# 或
python -m constraint_graph.cli export --kg out/kg --out out/cg
```

---

### 6. 扩展点

| 方向         | 说明                                           |
| ---------- | -------------------------------------------- |
| **更多约束类型** | 在 `canonicalizer` + 各 exporter `_emit_*` 扩   |
| **真实 DFA** | 替换 `dfa_compiler.py` 中占位逻辑                   |
| **缓存/增量**  | 对 `hash` 建索引；若未变动跳过文件写入                      |
| **CI**     | `pytest` + GitHub Action：加载最小 KG dump，断言产物存在 |

---

### 7. 依赖与版本

| 依赖             | 最低版本 | 作用                        |
| -------------- | ---- | ------------------------- |
| `neo4j-driver` | 5.x  | Bolt 连接                   |
| 其余均为标准库        | —    | argparse / json / pathlib |

---

### 8. 性能估计

| KG 规模  | 约束条数 | 导出时长（Mac M2, 单核） |
| ------ | ---- | ---------------- |
| 5k 节点  | 600  | < 0.5 s          |
| 50k 节点 | 6k   | \~ 3 s           |

*占位 DFA 编译近乎 O(1)；替换真编译器后视规则复杂度增加。*

---

### 9. 已知局限

1. **DFA** 目前为空实现；强 CGD 仍未真正硬约束。
2. **抽取规则** 只覆盖 `cardinality + enum`，复杂 range/implication 需扩展。
3. **增量缓存** 尚未落盘；每次都会全量写文件。

---

### 10. 迭代计划（摘要）

| Sprint | 目标                 | 关键任务                              |
| ------ | ------------------ | --------------------------------- |
| S-1    | 真 DFA 集成           | lark → table + 状态优化               |
| S-2    | range / implies 支持 | Canonicalizer & SMT/SHACL 扩       |
| S-3    | 缓存 & CI            | `hash-index.json` + GitHub Action |

---

**约束图 (constraint\_graph) 框架至此完整成型**。
后续若对具体实现、性能优化或论文撰写需要进一步细节，随时沟通！
