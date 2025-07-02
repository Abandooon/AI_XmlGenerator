# **Constraint-Graph “三段护栏” 重构设计文档（v 3.2 Draft）**

> 本设计文档用 **Markdown** 编写，既给出原理性解释，也落到可直接编码的模块职责。
> 目标：依据 **raw\_\*\*.jsonl → DFA** 的新链路，重构 `dfa_compiler.py / cli.py`，同时保留现有 **GBNF + SHACL + SMT** 产物。

---

## 1. 总览与核心理念

| 层级         | 护栏方式                           | 关键产物                                       | 目的                          |
| ---------- | ------------------------------ | ------------------------------------------ | --------------------------- |
| **生成时硬护栏** | **Prefix-DFA**（allowed-tokens） | `autosar.fsm`, `autosar_allowed_tokens.py` | *实时* 约束 *XML 标签顺序/嵌套*，走错即硬拦 |
| **生成后轻验**  | **Lark + SHACL**               | `autosar.gbnf`, `autosar_shapes.ttl`       | 解析 token → 文本；检查基数、枚举、正则    |
| **深度验**    | **SMT**                        | `constraints.smt2`                         | 跨实体关系、区间、蕴含、不变式             |

> **关键取舍**
>
> * 词法/枚举由 **GBNF** 持有；
> * 结构由 **DFA** 持有；
> * 语义由 **SHACL / SMT** 持有。
>   三者互不重叠、互不依赖，可独立增量。

---

## 2. 数据链路与产物

```mermaid
flowchart LR
    subgraph Extraction
        KG[(Neo4j / Parquet / RDF)]
        KG --> TE[token_extractor.py]
    end
    TE --> RC[raw_classes.jsonl]
    TE --> RA[raw_attributes.jsonl]
    TE --> RE[raw_enums.jsonl]
    TE --> RCON[raw_constraints.jsonl]
    
    subgraph Generation
        RC & RA & RE --> GE[grammar_exporter.py]
        GE --> GBNF[autosar.gbnf] ---\
        RC & RA --> DFA[dfa_compiler.py] --> FSM[autosar.fsm]
        RE -. tokens .-> GBNF
    end
    
    RCON --> SHACL[autosar_shapes.ttl]
    RCON --> SMT[constraints.smt2]
    
    FSM -->|allowed()| LLM[XML LLM Model]
    GBNF --> LLM
```

* **raw\_classes.jsonl** — 可达类元素；含 `xml_tag`, `xml_wrapper_tag`.
* **raw\_attributes.jsonl** — 父-子边；已展开继承 & inline；`xml_tag`, `xml_wrapper_tag`, `attributeClass`, `typeId`.
* **raw\_enums.jsonl** — `enumId → ≤64 values`。
* **raw\_constraints.jsonl** — regex, 区间, cross-entity；仅供 SHACL/SMT。

---

## 3. 模块职责

### 3.1 token\_extractor.py (保持现状)

| 任务                       | 细节                                  |
| ------------------------ | ----------------------------------- |
| `serialisable_classes()` | BFS *composition/aggregation*；剥离循环  |
| `aggregate_attributes()` | 继承下沉、inline class 拉平、`isXmlAttr` 过滤 |
| 落盘 raw\_\*               | 行级哈希，供增量编译                          |

### 3.2 grammar\_exporter.py （**词法表**）

1. **TOKEN 行**

   ```bnf
   EXCLUSIVE_AREA:        "EXCLUSIVE-AREA"
   ```
2. **一元规则**

   ```bnf
   <exclusive_area> ::= EXCLUSIVE_AREA
   ```
3. **单值枚举** (allowedValues ≤ 64 或 enum.values ≤ 64)

   ```bnf
   <sw_impl_policy_value> ::= "QUEUED" | "STANDARD"
   ```

> **不写层级产生式**；由 DFA 负责结构。

### 3.3 dfa\_compiler.py （**结构护栏**）✱ *重构重点*

| 步骤              | 行为                                                                        |
| --------------- | ------------------------------------------------------------------------- |
| **预索引**         | `tag2cid`,  `children[cid] → List[AttrRec]`                               |
| **BFS**         | 队列元素 = `(state_str, cid)`；<br>生成 `transitions[state][token] = next_state` |
| **Wrapper 处理**  | 若 `xml_wrapper_tag` 存在，先连 wrapper → 再连 item                               |
| **继续下钻条件**      | `attributeClass == true` **OR** `typeId∈classIds`                         |
| **深度限**         | `MAX_DEPTH` (=10)；触顶不再 enqueue                                            |
| **Hopcroft 压缩** | 保留，减少状态                                                                   |
| **生成 stub**     | `allowed(history)` 查询 `dict[state]`                                       |

### 3.4 allowed\_tokens runtime stub

```python
def allowed(prefix: list[str]) -> set[str] | None:
    state = " ".join(prefix)
    return TRANS.get(state)          # None = 不再限制，交 SHACL
```

---

## 4. 原理要点

| 主题                   | 说明                                                                              |
| -------------------- | ------------------------------------------------------------------------------- |
| **为何 FSM 不依赖 GBNF？** | GBNF 的 follow-set 在无层级产生式时会退化，导致解析器只能返回自身 token。直接用 raw BFS 可避免解析负担、信息丢失。       |
| **GBNF 仍不可删**        | 提供 TOKEN ↔ 字面串映射；IDE 高亮、闭标签写回、`MAX_DEPTH` 触顶 fallback、LLM prompt 都要用。           |
| **枚举拦截 vs. 深验**      | ≤64 单值枚举前置到 GBNF → 生成时硬限制；大枚举或多值属性留给 SHACL。                                     |
| **Wrapper Tag**      | 在 raw\_attribute 行内给出 `xml_wrapper_tag`；BFS 先生成 wrapper 状态，再按 `maxOccurs` 创建自环。 |

---

## 5. 核心数据结构（示意）

```python
# transitions: Dict[str, Dict[str, str]]
"" : {
  "APPLICATION_SW_COMPONENT_TYPE": "APPLICATION_SW_COMPONENT_TYPE"
},
"APPLICATION_SW_COMPONENT_TYPE": {
  "PORT_INTERFACE": "APPLICATION_SW_COMPONENT_TYPE PORT_INTERFACE",
  "SW_IMPL_POLICY": "APPLICATION_SW_COMPONENT_TYPE SW_IMPL_POLICY",
  ...
},
"APPLICATION_SW_COMPONENT_TYPE PORT_INTERFACE": {
  "PORT_INTERFACE":  ...  # 自环 (maxOccurs=-1)
}
```

*任一状态默认认为是接受态。
带枚举值的节点（如 `SW_IMPL_POLICY`) 在 GBNF 层面已被硬约束为字面量，不再下钻。*

---

## 6. 编译/CLI 流程（新）

```bash
# 步骤 1  抽取 KG → raw 表
python token_extractor.py dump --kg bolt://… --out artifacts/raw

# 步骤 2  GBNF（词法表）
python grammar_exporter.py --raw artifacts/raw --out artifacts/grammar --roots roots.json

# 步骤 3  FSM（结构护栏）
python dfa_compiler.py   --raw artifacts/raw --out artifacts/fsm   --roots roots.json
```

`build` 子命令自动串联 1-3 步；`--no-compress` 参数可跳过 Hopcroft 用于调试。

---

## 7. 后续可扩展点

| 优先级 | 方向                 | 说明                                                   |
| --- | ------------------ | ---------------------------------------------------- |
| 🔴  | **On-the-fly DFA** | 运行期按需展开，彻底解决状态爆炸                                     |
| 🟠  | **MAX\_DEPTH 自适应** | 统计真实路径分布，动态调深度                                       |
| 🟠  | **IDE LSP 插件**     | 利用 FSM 做即时补全、高亮                                      |
| 🟡  | **性能基准**           | 固定 5 k / 50 k 节点 KG dump，持续跟踪 FSM 规模与 `allowed()` 延迟 |

---

## 8. 结论

* 将 **KG 元模型 → raw → DFA** 直接串接，能最精确、最低耦合地表达嵌套结构；
* **GBNF** 留做词法层，满足解析与可读性；
* **SHACL/SMT** 继续处理深层语义。

> 以上设计既保留“三段护栏”架构精神，又消除了 “follow-set 退化” 带来的信息损失，为后续代码重构提供了清晰且可落地的蓝图。
