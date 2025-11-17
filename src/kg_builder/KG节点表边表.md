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


---

* **节点标签覆盖**：代码共创建 9 种主要 label；Constraint 节点会带 *双标签*（“Constraint;DataType”等）。
* **关系类型**：17 种；其中 `PARENT_OF` 仅在 EdgeAssembler 文档字符串中声明，实际边生成将在后续补完。
* **唯一键策略**：全部使用 IRI (`id`)；Class / Attribute / Enum 等子类由 builder 保证 IRI 不冲突。
* **索引/查询**：builder 维护 `class_index`、`attr_index`、`enum_index`、`literal_index`、`parent_index`，在建边阶段做 O(1) 反查。


下面把这套代码如何**从元模型数据构建节点与边**的完整逻辑，以及**最终知识图谱（KG）的数据结构/字段**讲清楚。为便于核对，我在关键结论处给出文件内联引用。

# 一、整体流程（从输入到KG）

1. **加载元数据与约束**

* `MetadataLoader.load()` 读取 `unified_metadata.json`，若存在 JSON Schema 则先校验；否则走“轻量解析”。它还会把 `groups / complexTypes / simpleTypes` 下的一层 `null` 值清洗为 `""`，减少后续空判断的分支。
* `ConstraintLoader.load()` 读取 `constraints_linked.json`，兼容“顶层就是数组”或顶层对象里装在 `extracted_constraints` 两种格式。

2. **构建本体层（Ontology）节点与边**
   `OntologyGraphBuilder.build(meta)` 走两遍：

* **Pass-1（只建节点）**：从 `groups / complexTypes / extract_inner_class / simpleTypes` 生成 Class / Attribute / Package / AttrGroup / Enum / EnumLiteral 等节点；并对属性做类型链接准备。
* **Pass-2（连边）**：为类之间的继承/组合/关联、类与包、类与属性组、属性与类型等补全关系边。

3. **融合约束层（Constraints）关系**
   `EdgeAssembler.build_edges(constraint_nodes)` 基于约束目标，把“规则约束到类/属性”的边、引用关系、章节定位等建立起来；必要时回溯祖先类定位属性。

---

# 二、本体层：节点与边的详细构建逻辑

## 2.1 Pass-1：创建节点

### A) Class 类节点

* 来源：`groups` / `complexTypes` / `extract_inner_class`
* 字段：

  * `id`=给定 `iri`，`label`="Class"
  * `name`、`xml_tag`、`description`
  * `isComplexType`（仅 complexTypes 为 True）、`isInnerClassType`（仅 inner 为 True）、`isAttribute`（透传）
* 索引：`_class_idx[name] = iri`。

### B) Package 包节点 + 归属边

* 若类含 `Package` 路径：沿路径逐级创建 `Package` 节点（`id`=`pkg:/seg1/seg2...`，字段 `name`、`level`），相邻包之间加 `HAS_CHILD`；类指向最末级包 `IN_PACKAGE`。

### C) Attribute / Element 属性节点

* 来源：类下的 `attributes` 与 `elements` 两组；等价处理。
* `id`：优先 `attr["iri"]`，否则 `attr:{slug(qualifiedName or name)}`；如已存在则跳过重复创建。
* 字段（重点）：

  * `name`（取 `qualifiedName` 的最后段或 `name`）
  * `qualifiedName`、`type`、`isXmlAttr`、`minOccurs`、`maxOccurs`、`xml_tag`、`xml_wrapper_tag`、`latestBindingTime`、`description`、`stereotypes`、`annotation`、`isPrimitiveType`
  * **`parentClass`**：父节点的类名（属性“物理所在”容器的名称）
  * **`ownerClass`**：优先 `attr["ownerClass"]`；否则取 `qualifiedName` 的类前缀；再否则回退为 `parentClass`
* 关系：从父类（或属性组）到属性连 `HAS_ATTRIBUTE`。

> **说明**：`parentClass / ownerClass` 字段在 v1.1 中被明确补全，解决了 CLI 某些 KeyError 问题。

### D) AttributeGroup 属性组

* 对类声明的 `attributeGroups`，若不存在则创建 `AttrGroup` 节点（`id`=`attrgrp:…`）；类指向组 `HAS_ATTR_GROUP`。
* 同时把该组在元数据里声明的“通用属性”实体化到组节点上（组→属性：`HAS_ATTRIBUTE`）。

### E) Enum & EnumLiteral

* simpleTypes 作为 **Enum** 节点：`name`、`baseType`、`isPrimitive`、`pattern`、`xml_tag`；并为每个枚举值建 **EnumLiteral**（字段 `value`），由枚举指向字面量 `HAS_LITERAL`。同时记录 `_enum_idx[name] = iri`。

### F) ClassStub 占位类

* 在需要“内联展开”但目标类不存在时，创建 `ClassStub`（`id`=`stub:…`，字段 `name`）。

## 2.2 Pass-2：连边

### A) 类关系（groups 与 complexTypes）

* **继承**：`groups.generalization` 与 `complexTypes.extends` → `SUBCLASS_OF`。
* **组合/聚合**：`groups.childs` → `HAS_CHILD`。
* **关联**：`ClassAssociatedFrom` → 源类 `ASSOCIATED_FROM` 到当前类；`ClassAssociatedTo` → 源类 `ASSOCIATED_TO` 到当前类。
* **内联展开**：`xsdInlines` → 当前类 `INLINE_EXPANDS` 目标类（必要时创建 `ClassStub`）。
* **内容变体**：类名以 `…Content` 结尾，则该类 `VARIANT_OF` 去掉 `Content` 的基类（若已存在）。
* 自环与重复边会被自动忽略。

### B) 属性类型边

* 在创建属性时若 `type` 命中 `_enum_idx` 或 `_class_idx`，就加 `TYPE_OF`；
* 结束前 `_wire_attr_type_edges()` 再全表校正一次，确保遗漏被补全。

---

# 三、约束层：根据 constraints 生成的边

`EdgeAssembler.build_edges()` 对每个“约束节点”（已在外部构造成 `{"id": ..., "targets": ..., "references": ..., "scope_path": ...}` 的字典）产出以下关系：

### 3.1 `CONSTRAINS` / `APPLIES_TO_CLASS`

* 对每个 target（仅处理 `entityType == "class"`）：

  * 若 `targetAttributes == ["_classLevel"]` → 直接：约束节点 `CONSTRAINS` → 目标**类**。
  * 否则逐个属性名 `a`：

    * 若本类就声明了属性 `a` → `CONSTRAINS` → 本类的**属性**。
    * 若本类未声明 → **回溯祖先**（利用 `parent_index` 拓扑）寻找首次声明该属性的祖先类，命中后：

      * 约束 `CONSTRAINS` → 祖先类的**属性**；
      * 额外加一条 `APPLIES_TO_CLASS` 指向**原目标类**，表达“此约束适用于该类，但落在其继承来的属性上”。
  * 若找不到目标类或属性会抛 `MissingTargetError`（以早暴露数据问题）。

### 3.2 `REFERS_TO`

* 对 `references`（字符串数组），把每个引用转成“同文档下的兄弟 IRI”：`<当前约束IRI的父路径>/<ref>`，然后连 `REFERS_TO`。

### 3.3 `IN_SECTION`（以及关于 `PARENT_OF`）

* 若含 `scope_path`（如 `["Chapter 1", "Section 1.1"]`），则把它 slug 化为 `doc:sec/Chapter_1/Section_1_1`，并连：约束 `IN_SECTION` → 该 section IRI。
* 代码里**未**创建 `Section` 节点本身、也**未**真的产出 `PARENT_OF`（虽然文件头注释写了“目标包含 PARENT\_OF”）——当前实现仅返回 `IN_SECTION` 边和 section IRI 字符串缓存；如需章节树，还要在别处落地 section 节点并连上下级。

---

# 四、最终 KG 的数据结构（节点/边模式）

## 4.1 节点（Node）

所有节点共有字段：`id`（IRI）、`label`（类型标识）。各类型的补充字段如下：

* **Class**

  * `name`, `xml_tag`, `description`
  * `isComplexType`, `isInnerClassType`, `isAttribute`（布尔）
* **ClassStub**

  * `name`（占位）
* **Package**

  * `name`, `level`（从1开始的层级）
* **AttrGroup**

  * `name`
* **Attribute**

  * `name`, `qualifiedName`, `type`, `isXmlAttr`
  * `minOccurs`, `maxOccurs`, `xml_tag`, `xml_wrapper_tag`
  * `latestBindingTime`, `description`, `stereotypes`, `annotation`
  * `isPrimitiveType`
  * **`parentClass`**, **`ownerClass`**（v1.1 新增、已自动推断）
* **Enum**

  * `name`, `baseType`, `isPrimitive`, `pattern`, `xml_tag`
* **EnumLiteral**

  * `value`
* **（Section）**

  * 本代码不创建节点；仅在 `IN_SECTION` 边里出现形如 `doc:sec/...` 的 IRI。若你需要章节成为一等节点，需在装载/合并阶段按这些 IRI 另外建 `Section` 节点。

> **IRI 规则**：
> Class/Enum/EnumLiteral 直接使用输入里的 `iri`；Package 用 `pkg:/...`；AttrGroup 用 `attrgrp:...`；Attribute 默认 `attr:...`（除非输入提供 `iri`）；ClassStub 用 `stub:...`；Section 用 `doc:sec/...`。

## 4.2 边（Edge）

统一三元组：`(startIRI, relType, endIRI)`。已实现的关系与语义：

* **类/结构**

  * `SUBCLASS_OF`：继承（groups.generalization / complexTypes.extends）
  * `HAS_CHILD`：组合/聚合（groups.childs，包层级也用此）
  * `ASSOCIATED_FROM` / `ASSOCIATED_TO`：类间关联
  * `INLINE_EXPANDS`：内联展开（缺失时以 `ClassStub` 占位）
  * `VARIANT_OF`：`…Content` 变体与基类的对应关系
  * `IN_PACKAGE`：类归属包（类→末级包）
* **属性/类型**

  * `HAS_ATTRIBUTE`：类或属性组 → 属性
  * `TYPE_OF`：属性 → 其类型（Class 或 Enum）
  * `HAS_ATTR_GROUP`：类 → 属性组
  * `HAS_LITERAL`：枚举 → 字面量
* **约束/文档**

  * `CONSTRAINS`：约束 → 类（\_classLevel）或属性
  * `APPLIES_TO_CLASS`：当约束落在**继承来的属性**时，额外指向原目标类
  * `REFERS_TO`：约束内部“引用”关系
  * `IN_SECTION`：约束位于哪一文档章节（section IRI）
  * **（`PARENT_OF` 未实现）**：当前代码未生成章节层级边。

> **去重/自环**：添加边时会跳过自环与重复三元组。

注：group中的类额外添加字段：abstract、isAbstract