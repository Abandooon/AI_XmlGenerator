
---

## 1. 只看“本类直接声明”的属性

```cypher
// 按 xml_tag 精确定位
MATCH (c:Class {xml_tag: 'SWC-INTERNAL-BEHAVIOR'})-[:HAS_ATTRIBUTE]->(a:Attribute)
RETURN a.xml_tag        AS attr_tag,
       a.isXmlAttr      AS is_attr,
       a.minOccurs      AS min_occurs,
       a.maxOccurs      AS max_occurs
ORDER BY attr_tag;
```

> 如果你手头只有节点 ID（例如 `12345`），把 `WHERE id(c)=12345`
> （Neo4j 4.x）或 `WHERE elementId(c)='12345'`（Neo4j 5.x）替换掉上面的 `{xml_tag:…}` 即可。

---

## 2. 查看“本类属性 → 其 type 指向的类/枚举/原始类型”

```cypher
MATCH (c:Class {xml_tag: 'SWC-INTERNAL-BEHAVIOR'})-[:HAS_ATTRIBUTE]->(a:Attribute)
OPTIONAL MATCH (a)-[:TYPE_OF]->(t)
RETURN a.xml_tag                 AS attr_tag,
       labels(t)[0]              AS target_label,   // Class / Enum / Primitive …
       t.xml_tag                 AS target_xml_tag, // 目标是 Class 时
       t.name                    AS enum_name,      // 目标是 Enum 时
       t.baseType                AS primitive_name  // 目标是 Primitive 时
ORDER BY attr_tag;
```

* `labels(t)[0]` 能告诉你目标节点属于哪种概念。
* `t.xml_tag` 仅对 `Class` 节点有意义；如果是 `Enum` 或原始数据类型则为 `null`。

---

## 3. **连同父类继承**的属性一并列出

```cypher
MATCH (c:Class {xml_tag:'SWC-INTERNAL-BEHAVIOR'})-[:SUBCLASS_OF*0..]->(sup:Class)
MATCH (sup)-[:HAS_ATTRIBUTE]->(a:Attribute)
RETURN DISTINCT
       sup.xml_tag               AS declared_in,   // 哪个父（或本）类声明
       a.xml_tag                 AS attr_tag,
       a.isXmlAttr               AS is_attr,
       a.minOccurs               AS min_occurs,
       a.maxOccurs               AS max_occurs
ORDER BY declared_in, attr_tag;
```

> `*0..` 让当前类 `c` 自己也被包含（长度 0）。

---

## 4. 再加上 **INLINE\_EXPANDS** 引入的属性

```cypher
MATCH (c:Class {xml_tag:'SWC-INTERNAL-BEHAVIOR'})
OPTIONAL MATCH path = (c)-[:INLINE_EXPANDS*0..]->(g:Class)
WITH DISTINCT g AS grp          // g 包括自身与所有展开 group
MATCH (grp)-[:HAS_ATTRIBUTE]->(a:Attribute)
RETURN grp.xml_tag  AS from_group,
       a.xml_tag    AS attr_tag,
       a.isXmlAttr  AS is_attr
ORDER BY from_group, attr_tag;
```

---

