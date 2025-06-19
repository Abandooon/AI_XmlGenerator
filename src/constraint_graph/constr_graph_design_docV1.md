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
### **allowed-tokens 子系统补充设计（聚焦“逐 step 可采样 token 集”硬约束）**


# “allowed-tokens”子系统设计文档
> 本节替换并细化 *§3 生成流程* 和 *§4 allowed() 运行协议*，确保 **XML 标签、属性名、有限字面量** 在 **每一步采样** 时都被硬性屏蔽到位。

---

## 1 核心思路

> **可采样 token ∶** 对于当前 **DFA 状态 S**，枚举所有 *能使 DFA 仍可达终态* 的 **终端 T**，计算 `BPE(T)`，取并集即 *Allowed(S)*。
>
> ```text
> Allowed(S) = ⋃_{T ∈ frontier(S)}   Tokenize(T)
> ```
>
> *frontier(S)* = DFA.transitions\[S]∩Terminals

---

## 2 信息提取 & 映射

| KG 字段                  | 描述                                      | 进入终端集的形式                |
| ---------------------- | --------------------------------------- | ----------------------- |
| `Class.xml_tag`        | `<SWC-INTERNAL-BEHAVIOR>`               | `<TAG>` `</TAG>`        |
| `Attribute.xml_tag`    | `<CYCLE-TIME>` → 属性名                    | `ATTRIBUTE="`、`"`（结束引号） |
| `EnumLiteral.value`    | `"DIAGNOSIS"`, `"SENSOR"`               | **直接字面量**               |
| `Constraint.value`     | `[ "ON", "OFF" ]`                       | 同上                      |
| `Constraint.range` ≤ N | `[1,100]` 且 *(100 ≤ MAX\_ENUM)*         | `"1"` … `"100"`         |
| `regex` → 等价有限集        | `^[0-3][0-9]$` → `00` … `39`            | 全枚举                     |
| `min/maxOccurs`        | 出现上限=0 时 **不放入**，=1 时 `<TAG>` only once | 由 DFA 状态计数实现            |

> **MAX\_ENUM**：配置阈值（默认 ≈ 1 000）；超过则由 SHACL/SMT 兜底。

---

## 3 运行时算法（伪码）

```python
def allowed(state_id: int, prefix: str) -> set[int] | None:
    """
    1. 查询 DFA 在 state_id 可接受的终端集合 F
    2. 映射到 token id 集合 U
    3. 若属性值正在展开 → 附加 regexFilter / rangeFilter
    """
    F = DFA.allowed_terminals(state_id)        # {'<CYCLE-TIME>', '23', '</CYCLE-TIME>'}
    U = set()
    for term in F:
        U |= TOKEN_MAP.get(term, set())

    # --- 可选后缀过滤 ---
    if inside_long_range(prefix):              # 如 1..65535
        U &= digit_tokens                     # 只允许 '0'..'9'

    return U or None
```

*`inside_long_range()`* 通过正则判断光标是否处在 `<LENGTH>` 等“大范围数值”区块；此时仅放行 `digit_tokens`，最后再交 SHACL 或 SMT 做范围检查。

---

## 4 Mermaid 流程图（Markdown 嵌入）

```mermaid
flowchart TD
    subgraph 构建期
        A1[KG\n(xml_tag, enum, range…)]
        A2[canonical_constraints.json]
        A1 -->|抽取映射| B(终端集)
        B --> C[GrammarExporter\n(gbnf)]
        C --> D[dfa_compiler\n(.fsm)]
        D --> E[tokenizer\nencode(term)]
        E --> F[AllowedTokensExporter\n→ autosar_allowed_tokens.py]
    end
    subgraph 运行期
        V[vLLM decoding\n(prompt, logits)]
        P[autosar_allowed_tokens.py\nallowed(state,prefix)]
        V -->|state_id,prefix| P
        P --|token set| V
        V -->|生成 XML| Out[ARXML]
    end
```

---

## 5 状态→终端→token 映射示例

| DFA 状态 S | 前缀                 | frontier(S)               | token IDs (GPT-2) |
| -------- | ------------------ | ------------------------- | ----------------- |
| `S₀`     | `""`               | `<SWC-INTERNAL-BEHAVIOR>` | `[13, 54717, 12]` |
| `S₁`     | `<SWC…>`           | `<SHORT-NAME>`            | `[13, 54708, 12]` |
| `S₂`     | …`<CYCLE-TIME>`    | `"1"` … `"100"`           | `[16]` … `[463]`  |
| `S₃`     | …`20</CYCLE-TIME>` | `<MODE-SWITCH-EVENT>`     | `[13, 54811, 12]` |
| `S₄`     | …`PRIORITY>`       | `"1"` … `"16"`            | `[16]` … `[31]`   |

*达到 `MODE-SWITCH-EVENT maxOccurs = 1` 后，`frontier(S)` 将 **不再包含** `<MODE-SWITCH-EVENT>`，DFA 换到 `S₅`。*

---

## 6 接口变更（摘录）

```bash
constraint_graph.cli export \
  --kg bolt://... \
  --out out/cg \
  --tokenizer meta-llama/Llama-3-8B
```

生成文件结构：

```
out/cg/
 ├ autosar.gbnf
 ├ autosar.fsm
 ├ tokens.json              # 终端→原文
 └ autosar_allowed_tokens.py
```

---

## 7 与 SHACL / SMT 的衔接

* **allowed-tokens** → 保证 **局部合法性**（标签、属性、有限枚举、简单 range）。
* **SHACL Shapes**  → 检查 **值域**、**出现次数**、**regex**。
* **SMT-LIB**     → 处理 **跨节点依赖**、**数学关系**、**引用一致性**。

这样形成 **“生成时硬护栏 → 生成后轻验 → 深验”** 三段防线，职责清晰、无重复计算。

---


