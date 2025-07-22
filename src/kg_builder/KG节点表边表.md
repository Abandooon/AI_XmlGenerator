下面把 **KG 的“本体（节点）表”与“关系（边）表”** 按开发代码实际创建的内容汇总成两张一览表，便于直接对照到 Cypher schema 或 ORM model。每一行都注明来源（代码文件），如需核对可跳回相应实现。

---

## 1. 本体（节点）表

| 节点 Label        | 唯一键 / IRI 前缀              | 主要属性字段（必含★ / 常见）                                                                                                                                                                                                                         | 典型来源代码                                            |
| --------------- | ------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- |
| **Class**       | `cls:` *或*源码里直接给定 `iri`   | ★ `name` ‧ `annotation` ‧ `description` ‧ `isComplexType` ‧ `isInnerClassType` ‧ `isAttribute`                                                                                                                                           | `OntologyGraphBuilder._pass_class_nodes`          |
| **ClassStub**   | `stub:`                   | ★ `name`                                                                                                                                                                                                                                 | `OntologyGraphBuilder._get_or_create_stub_class`  |
| **Attribute**   | `attr:`                   | ★ `name` ‧ `qualifiedName` ‧ `type` ‧ `minOccurs` ‧ `maxOccurs` ‧ `xml_tag` ‧ `isXmlAttr` ‧ `parentClass` ‧ `ownerClass` ‧ `xml_wrapper_tag` / `latestBindingTime` / `description` / `stereotypes` / `annotation` / `isPrimitiveType` | `OntologyGraphBuilder._create_attribute`          |
| **AttrGroup**   | `attrgrp:`                | ★ `name`                                                                                                                                                                                                                                 | `OntologyGraphBuilder._get_or_create_attrgroup`   |
| **Package**     | `pkg:/…`                  | ★ `name` ‧ `level`                                                                                                                                                                                                                       | `OntologyGraphBuilder._attach_package`            |
| **Enum**        | `enum:` *或*从元数据给定         | ★ `name` ‧ `baseType` ‧ `isPrimitive` ‧ `pattern` ‧ `annotation`                                                                                                                                                                         | `OntologyGraphBuilder._handle_simple_types`       |
| **EnumLiteral** | `lit:`                    | ★ `value`                                                                                                                                                                                                                                | `OntologyGraphBuilder._handle_simple_types`       |
| **Constraint**  | `<domain>:<ver>/constr/…` | ★ `cid` ‧ `id_type` ‧ `constraint_type` ‧ `is_active` ‧ `expression` ‧ `value` ‧ `scope_path` ‧ `targets` ‧ `references` ‧ `title` <br>Label 形如 `"Constraint;ModelOCL"`（多层标签分号分隔）                                                        | `ConstraintGraphBuilder._create_constraint_node`  |
| **Section**     | `doc:sec/…`               | 当前仅由 IRI 隐式标识（尚无属性字段）                                                                                                                                                                                                                    | `EdgeAssembler._get_or_create_section`            |

> **说明**
>
> * 所有节点都含 Neo4j 默认的 `id`（全文中指 IRI）。
> * Constraint 节点额外拥有一个动态层标签：`ModelOCL` / `DataType` / `Documentation` / `Production`，由 `constraint_type` 或 `id_type` 判定。

---

## 2. 关系（边）表

| 关系类型                                  | 起点 Label → 终点 Label                        | 多重度†  | 语义 / 触发逻辑                 | 主要来源代码                                                       |
| ------------------------------------- | ------------------------------------------ | ----- | ------------------------- | ------------------------------------------------------------ |
| **SUBCLASS\_OF**                      | Class → Class                              | 多 → 1 | 继承 / generalization       | `_wire_group_relationships` / `_wire_complex_relationships`  |
| **HAS\_CHILD**                        | Class → Class<br>Package → Package         | 多 → 多 | 复合聚合 / 包含                 | `_wire_group_relationships`、`_attach_package`                |
| **HAS\_ATTR\_GROUP**                  | Class → AttrGroup                          | 多 → 多 | 引用 XML AttributeGroup     | `_pass_class_nodes`                                          |
| **HAS\_ATTRIBUTE**                    | Class → Attribute<br>AttrGroup → Attribute | 多 → 多 | 类或 AttrGroup 拥有属性         | `_create_attribute` (默认 edge\_type)                          |
| **TYPE\_OF**                          | Attribute → Enum ∣ Class                   | 1 → 1 | 属性的数据类型                   | `_create_attribute`                                          |
| **VARIANT\_OF**                       | Class (…Content) → Class                   | 1 → 1 | Content-Variant 关联        | `_pass_class_nodes`                                          |
| **INLINE\_EXPANDS**                   | Class → Class ∣ ClassStub                  | 多 → 多 | XSD `xsd:group` inline 展开 | `_wire_inline_expands`                                       |
| **ASSOCIATED\_FROM / ASSOCIATED\_TO** | Class ↔ Class                              | 多 ↔ 多 | UML Association (有向)      | `_wire_group_relationships`                                  |
| **IN\_PACKAGE**                       | Class → Package                            | 1 → 1 | 归属包路径                     | `_attach_package`                                            |
| **HAS\_LITERAL**                      | Enum → EnumLiteral                         | 1 → 多 | 枚举字面量                     | `_handle_simple_types`                                       |
| **CONSTRAINS**                        | Constraint → Attribute ∣ Class             | 多 → 多 | 约束直接作用目标                  | `EdgeAssembler._build_constrains_edges`                      |
| **APPLIES\_TO\_CLASS**                | Constraint → Class                         | 多 → 多 | 约束跨类应用（目标属性在祖先类时）         | 同上                                                           |
| **REFERS\_TO**                        | Constraint → Constraint                    | 多 → 多 | 约束内部引用                    | `EdgeAssembler.build_edges`                                  |
| **IN\_SECTION**                       | Constraint → Section                       | 多 → 1 | 约束出处文档章节                  | `EdgeAssembler.build_edges` + `_get_or_create_section`       |
| **PARENT\_OF**                        | Section → Section                          | 多 → 多 | 文档章节层级                    | *规划中*（docstring 中声明待实现）                                      |

† **多重度**：根据代码逻辑推断；Neo4j 未显式限制。

---

### 核心要点回顾

* **节点标签覆盖**：代码共创建 9 种主要 label；Constraint 节点会带 *双标签*（“Constraint;DataType”等）。
* **关系类型**：17 种；其中 `PARENT_OF` 仅在 EdgeAssembler 文档字符串中声明，实际边生成将在后续补完。
* **唯一键策略**：全部使用 IRI (`id`)；Class / Attribute / Enum 等子类由 builder 保证 IRI 不冲突。
* **索引/查询**：builder 维护 `class_index`、`attr_index`、`enum_index`、`literal_index`、`parent_index`，在建边阶段做 O(1) 反查。

至此，你可以直接把上表转成 Neo4j `CONSTRAINT`/`INDEX` 与 `CREATE` 语句，或映射到你的 ORM/DSL。在拿到实际 KG dump 时，跑简单的 `MATCH (n) RETURN DISTINCT labels(n)` / `MATCH ()-[r]->() RETURN DISTINCT type(r)` 即可校验实现与设计的一致性。
