# -*- coding: utf-8 -*-
"""
Dynamic Query Engine — Clean Single-Path Implementation (patched)

变更要点（2025-09-10）
- 终止型类型支持：当 Attribute 的 TYPE_OF 指向的 Class 为 “原子/别名/枚举” 时，直接落基元/enum，不再递归；
  支持字段：t.isPrimitiveType、t.isAttribute、t.base、t.enumerations、t.pattern。
- 无 TYPE_OF 的 Attribute：不再给空对象，优先用 a.isEnum/a.baseType 映射到基元；再用名称启发式；最后兜底 string。
- 查询返回字段扩充：带回 a.isEnum/a.baseType 以及 t.isAttribute/t.base/t.enumerations/t.pattern。
- 小优化：去掉 SUBCLASS_OF*0.. 后再 + c 的重复合并。

设计要点：
1) 仅使用 KG 的 Class/Attribute/TYPE_OF/SUBCLASS_OF 关系；不使用 (:Element)/HAS_ELEMENT/HAS_CHILD。
2) 每一层筛选“要展开的属性”：(minOccurs >= 1) OR (被 Round1 设计声明)。
   - Round1 设计通过 _build_design_index 编译为：父容器 xml_tag -> 需要的子元素 tag(wrapper/tag) 集合。
   - 匹配同时支持 xml_tag 和 xml_wrapper_tag（兼容 runnableentity 等 wrapper!=tag 的场景）。
3) 递归永远用 Attribute 的 type_name（Class.name）向下，而不是用 xml_tag（避免 tag 重复的歧义）。
4) 容器/数组判断：maxOccurs 为 unbounded/负数/大于1 -> array；否则单对象/原子。
5) 终止规则：primitive/enum/simple（根据 KG 字段）映射到 JSON 原子类型；不硬编码 AUTOSAR 键名。
6) 产出 Schema：所有对象 additionalProperties=False；必选字段来自 minOccurs>=1。

注意：
- 该实现不写死 *-TREF/*-IREF 的对象形式，完全按 KG 递归；如需“@DEST/#text”之类形状，请在 KG 中为其 Class 建模。
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from neo4j import GraphDatabase
from ..config import CONFIG

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    print("[WARN] neo4j driver未安装")

# 三选一（exactly one）类：类名 → 需要互斥选择的键集合
CHOICE_ONE_OF = {
    "AUTOSARVARIABLEREF": {
        "AUTOSAR-VARIABLE-IREF",
        "LOCAL-VARIABLE-REF",
        "AUTOSAR-VARIABLE-IN-IMPL-DATATYPE",
    },
}

# InstanceRef 的“必选 + 三选一”规则（支持同义键：tag / wrapper）
# mandatory: 这些键必须出现（即便 KG 的 minOccurs 标成 0 也强制）
# xor_groups: 三选一，每个元素是同义键集合（取其中存在于 props 的那个）
XOR_WITH_MANDATORY = {
    "VARIABLEINATOMICSWCTYPEINSTANCEREF": {
        "mandatory": {"TARGET-DATA-PROTOTYPE-REF"},
        "xor_groups": [
            {"PORT-PROTOTYPE-REF"},
            {"ROOT-VARIABLE-DATA-PROTOTYPE-REF"},
            {"CONTEXT-DATA-PROTOTYPE-REFS", "CONTEXT-DATA-PROTOTYPE-REF"},  # tag / wrapper 兼容
        ],
    },
    "ARVARIABLEINIMPLEMENTATIONDATAINSTANCEREF": {
        "mandatory": {"TARGET-DATA-PROTOTYPE-REF"},
        "xor_groups": [
            {"PORT-PROTOTYPE-REF"},
            {"ROOT-VARIABLE-DATA-PROTOTYPE-REF"},
            {"CONTEXT-DATA-PROTOTYPE-REFS", "CONTEXT-DATA-PROTOTYPE-REF"},
        ],
    },

}

# ==================== Optional 放行（精简后） ====================
# 只保留事件起点引用这类“便捷但不改变结构选择权”的可选放行；
# 删除会越权影响结构选择的条目：RUNNABLE-ENTITY / SERVERCALLPOINTS 相关。
ALWAYS_INCLUDE_OPTIONALS: dict[str, set[str]] = {
    # 事件：常见的“起点引用”在 KG 中多为 0..1，但工程上几乎总需要
    "TIMINGEVENT": {"START-ON-EVENT-REF"},
    "RTEEVENT": {"START-ON-EVENT-REF"},
    "MODESWITCHEVENT": {"START-ON-EVENT-REF"},
    "DATARECEIVEDEVENT": {"START-ON-EVENT-REF"},
}



# ---------------------------- 工具 & 异常 ----------------------------

class KGQueryError(RuntimeError):
    pass


def _norm(s: Optional[str]) -> str:
    return (s or "").strip()


def _up(s: Optional[str]) -> str:
    return _norm(s).upper()


def _is_array_occurs(max_occurs) -> bool:
    """-1 或 >1 为数组；兼容历史 'unbounded' 字符串。"""
    if max_occurs is None: return False
    try:
        v = int(max_occurs)
        return (v == -1) or (v > 1)
    except Exception:
        s = str(max_occurs).strip().lower()
        return s in {"unbounded","inf","infinite"}

def _emit_ref_object_schema(is_array: bool) -> dict:
    obj = {
        "type": "object",
        "properties": {
            "@DEST": {"type": "string"},
            "#text": {"type": "string"}
        },
        "required": ["@DEST","#text"],
        "additionalProperties": False
    }
    return {"type":"array","items":obj} if is_array else obj

def _override_container_shape(prop_key_upper: str, default_is_array: bool) -> bool:
    """
    容器白名单覆盖（优先于 maxOccurs）：
      - 壳=object（非数组）：PORTS, INTERNAL-BEHAVIORS, COMPONENTS, CONNECTORS
      - 条目=数组：R-PORT-PROTOTYPE, P-PORT-PROTOTYPE, RUNNABLE-ENTITY, EVENTS
    其他保持默认。
    """
    U = prop_key_upper
    # 壳：强制非数组
    if U in {"PORTS","INTERNAL-BEHAVIORS","COMPONENTS","CONNECTORS"}:
        return False
    # 条目：强制数组
    if U in {"R-PORT-PROTOTYPE","P-PORT-PROTOTYPE","RUNNABLE-ENTITY","EVENTS"}:
        return True
    return default_is_array





# ---------------------------- 引擎主体 ----------------------------

@dataclass
class Neo4jConfig:
    uri: str
    user: str
    password: str


class DynamicQueryEngine:
    """
    Clean 版：唯一实现路径（含终止型类型判断 & 无 TYPE_OF 兜底）
    """

    def __init__(self):
        """初始化查询引擎"""
        self.config = CONFIG.knowledge_graph
        self.driver = None

        if NEO4J_AVAILABLE:
            self._init_neo4j_connection()

    def _init_neo4j_connection(self):
        """初始化Neo4j连接"""
        try:
            if CONFIG.debug_mode:
                print(f"[DEBUG] 连接Neo4j: {self.config.neo4j_uri}")
                print(f"[DEBUG] 用户名: {self.config.neo4j_user}")

            self.driver = GraphDatabase.driver(
                self.config.neo4j_uri,
                auth=(self.config.neo4j_user, self.config.neo4j_password)
            )

            # 测试连接
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                test_value = result.single()["test"]
                if test_value == 1:
                    print("[INFO] Neo4j连接成功")
                else:
                    raise Exception("连接测试失败")

        except Exception as e:
            print(f"[WARN] Neo4j连接失败: {e}")
            if CONFIG.debug_mode:
                import traceback
                traceback.print_exc()
            self.driver = None

    # ------------------------ Round1 设计索引 ------------------------

    def _build_design_index(self, element_design: dict) -> dict[str, set[str]]:
        """
        Round1 → 设计索引：
          - 顶层 '__TOP__' 决定是否展开 PORTS / INTERNAL-BEHAVIORS
          - 'PORTS'：端口原型类型白名单
          - 'INTERNAL-BEHAVIORS'：固定允许 {'RUNNABLE-ENTITY','EVENTS'}
          - 'RUNNABLE-ENTITY'：runnables[*].elements 的 wrapper/key 合并（如 DATA-SEND-POINTS、SERVER-CALL-POINTS…）
          - 'EVENTS'：events[*].type 合并（如 TIMING-EVENT、DATA-RECEIVED-EVENT…）
          - **新增**：消费 elements[].preselect[]，将
              of -> variant 加入白名单（保证分支被展开）
              variant -> include 子键加入白名单（保证只展开所选子键）
        """

        def U(x):
            return (x or "").strip().upper()

        idx: dict[str, set[str]] = {"__TOP__": set()}
        if not element_design:
            return idx

        # ----- PORTS -----
        ports = (element_design.get("ports") or {})
        if ports.get("needed"):
            idx["__TOP__"].add("PORTS")
            types = ports.get("types") or []
            if types:
                idx["PORTS"] = {U(t) for t in types}

        # ----- INTERNAL-BEHAVIORS -----
        ib = (element_design.get("internal_behaviors")
              or element_design.get("swc_internal_behavior")
              or {})
        if ib.get("needed"):
            idx["__TOP__"].add("INTERNAL-BEHAVIORS")
            idx["INTERNAL-BEHAVIORS"] = {"RUNNABLE-ENTITY", "EVENTS"}

            # runnables: 收集 wrapper/key；同时编译 preselect（of→variant，variant→include）
            run_elems: set[str] = set()
            for r in ib.get("runnables") or []:
                for elem in r.get("elements") or []:
                    if isinstance(elem, str):
                        run_elems.add(U(elem))
                        continue
                    if not isinstance(elem, dict):
                        continue

                    run_key = U(elem.get("wrapper") or elem.get("key"))
                    if run_key:
                        run_elems.add(run_key)

                    for ps in elem.get("preselect") or []:
                        of = U(ps.get("of"))
                        variant = U(ps.get("variant"))
                        include = [U(x) for x in (ps.get("include") or [])]

                        # of -> variant：白名单该分支（避免分支是 0..1 时被过滤）
                        if of and variant:
                            idx.setdefault(of, set()).add(variant)

                        # variant -> include：只展开被选择的子键
                        if variant and include:
                            s = idx.setdefault(variant, set())
                            s.update(include)

            if run_elems:
                idx["RUNNABLE-ENTITY"] = run_elems

            # events
            ev_types: set[str] = set()
            for ev in ib.get("events") or []:
                t = ev.get("type")
                if t: ev_types.add(U(t))
            if ev_types:
                idx["EVENTS"] = ev_types

        return idx

    # ------------------------ KG 结构查询（唯一口径） ------------------------

    def _query_class_attributes(self, session, class_ident: str) -> dict:
        """
        返回：{ class_name, class_tag, attributes: [ {...}, ... ] }
        每个 attribute 字段包含：
          - a.*: name/xml_tag/xml_wrapper_tag/minOccurs/maxOccurs/isXmlAttr/isPrimitiveType/type(声明)
          - t.*: name/labels/isAttribute/baseType/pattern 以及枚举字面量 t_enum_values
        """
        q = """
        MATCH (c:Class)
        WHERE (c.name) = $id OR (c.xml_tag) = $id OR (c.xml_wrapper_tag) = $id
        OPTIONAL MATCH path=(c)-[:SUBCLASS_OF*0..]->(p:Class)
        WITH c, collect(DISTINCT p) AS allc
        UNWIND allc AS cls
        OPTIONAL MATCH (cls)-[:HAS_ATTRIBUTE]->(a:Attribute)
        OPTIONAL MATCH (a)-[:TYPE_OF]->(t)
        OPTIONAL MATCH (t:Enum)-[:HAS_LITERAL]->(ev:EnumLiteral)
        WITH c, a, t, collect(DISTINCT ev.value) AS enum_vals, properties(a) AS amap, labels(t) AS tlabs, properties(t) AS tmap
        RETURN
          c.name AS class_name,
          c.xml_tag AS class_tag,
          collect(DISTINCT {
            name:            coalesce(amap['name'], a.name),
            xml_tag:         coalesce(amap['xml_tag'], a.xml_tag),
            xml_wrapper_tag: coalesce(amap['xml_wrapper_tag'], a.xml_wrapper_tag),
            minOccurs:       coalesce(amap['minOccurs'], a.minOccurs),
            maxOccurs:       coalesce(amap['maxOccurs'], a.maxOccurs),
            isXmlAttr:       coalesce(amap['isXmlAttr'], amap['is_xml_attribute']),
            a_is_primitive:  coalesce(amap['isPrimitiveType'], false),
            a_declared_type: amap['type'],
            type_name:       tmap['name'],
            type_labels:     tlabs,
            t_is_attribute:  tmap['isAttribute'],
            t_base:          coalesce(tmap['baseType'], tmap['base']),
            t_pattern:       tmap['pattern'],
            t_is_enum:       CASE WHEN 'Enum' IN tlabs THEN true ELSE false END,
            t_enum_values:   enum_vals
          }) AS attrs
        LIMIT 1
        """
        rec = session.run(q, id=class_ident).single()
        if not rec:
            raise KGQueryError(f"KG 中找不到 Class: {class_ident}")
        data = rec.data()
        attrs = []
        for a in data.get("attrs") or []:
            if not any(a.get(k) for k in
                       ("name", "xml_tag", "xml_wrapper_tag", "type_name", "a_is_primitive", "a_declared_type")):
                continue
            # 规范化：t_enum_values 统一为 list
            evs = a.get("t_enum_values")
            if isinstance(evs, str): a["t_enum_values"] = [evs]
            attrs.append(a)
        return {"class_name": data.get("class_name"), "class_tag": data.get("class_tag"), "attributes": attrs}




    # ------------------------ 终止与基元映射 ------------------------

    @staticmethod
    def _guess_primitive_from_name(tn: str) -> Optional[Dict[str, Any]]:
        if not tn:
            return None
        # 朴素猜测（不依赖固定域模型）
        if any(x in tn for x in ("INT", "UINT", "SINT", "INTEGER", "LONG", "SHORT")):
            return {"type": "integer"}
        if any(x in tn for x in ("FLOAT", "DOUBLE", "DECIMAL")):
            return {"type": "number"}
        if "BOOL" in tn or "BOOLEAN" in tn:
            return {"type": "boolean"}
        if any(x in tn for x in ("STRING", "CHAR", "TEXT", "IDENTIFIER", "ID")):
            return {"type": "string"}
        return None  # 交给递归

    @staticmethod
    def _scalar_from_base(base: Optional[str]) -> Dict[str, Any]:
        b = _up(base)
        if b in {"BOOLEAN"}: return {"type": "boolean"}
        if b in {"INT","INTEGER","INT8","INT16","INT32","INT64"}: return {"type": "integer"}
        if b in {"FLOAT","DOUBLE","DECIMAL","NUMBER"}: return {"type": "number"}
        return {"type": "string"}

    @staticmethod
    def _map_primitive_json(type_name: Optional[str], type_labels: Optional[List[str]], is_primitive: Optional[bool]) -> Optional[Dict[str, Any]]:
        """
        兼容旧的判断方式：根据 t.isPrimitiveType / labels / 命名猜测
        返回 None 表示“不是终止类型，需要递归”。
        """
        labels = set((type_labels or []))
        tn = _up(type_name)

        # 明确的原子类型标记（KG 字段）
        if is_primitive:
            return DynamicQueryEngine._guess_primitive_from_name(tn)

        # Enum 类：按 string 处理（不硬编码枚举值列表）
        if "Enum" in labels or "ENUM" in labels:
            return {"type": "string"}

        # 某些 KG 未标注 isPrimitiveType，可根据命名猜测
        return DynamicQueryEngine._guess_primitive_from_name(tn)

    # --- 2) 新增：统一的“是否当作引用终止”的判断 ---
    def _is_ref_terminal(self, session, type_name: str | None, a_xml_tag: str | None) -> bool:
        """
        True: 终止为 {@DEST,#text}; False: 继续递归。
        规则：
          - 优先：如有 type_name，则看该类是否为 DEST-only
          - 兜底：若没有 type_name，仅当 xml_tag 以 "-TREF" 结尾才视为终止
        """
        tn = (type_name or "").strip()
        if tn:
            try:
                return self._is_dest_only_class(session, tn)
            except Exception:
                # 查询失败走兜底
                pass

        tag = (a_xml_tag or "").strip().upper()
        return tag.endswith("-TREF")

    # --- 1) 新增：判断“是否 DEST-only 类”的工具函数 ---
    def _is_dest_only_class(self, session, class_ident: str) -> bool:
        """
        True: 该类只有一个 XML 属性且为 DEST，且无任何子元素（element）。
        这种类应终止为 {@DEST,#text}，不要继续递归。
        """
        info = self._query_class_attributes(session, class_ident) or {}
        attrs = info.get("attributes") or []

        def _is_xml_attr(a: dict) -> bool:
            # 兼容 isXmlAttr / is_xml_attribute 两种键
            return bool(a.get("isXmlAttr")) or bool(a.get("is_xml_attribute"))

        # 有任何子元素就不是 DEST-only
        has_element = any((not _is_xml_attr(a)) and (a.get("xml_tag") or a.get("name")) for a in attrs)
        if has_element:
            return False

        xml_attrs = [a for a in attrs if _is_xml_attr(a)]
        if len(xml_attrs) != 1:
            return False

        tag = (xml_attrs[0].get("xml_tag") or xml_attrs[0].get("name") or "").strip().upper()
        return tag == "DEST"

    # ------------------------ 递归构建（唯一实现） ------------------------

    def _build_class_schema_recursive(
            self,
            session,
            class_ident: str,
            parent_container_tag: str,
            design_index: dict[str, set[str]],
            seen: set[str],
    ) -> tuple[str, dict, dict]:
        """
        从 KG 递归构建 class_ident 的 JSON Schema 片段（内联版）：
          - 仅保留：KG 必选(minOccurs>=1) ∪ Round1 白名单（容器→子键；of→variant；variant→include）
          - CHOICE_ONE_OF：仅在“该容器没有任何 Round1 白名单”时作为兜底放行
          - XOR_WITH_MANDATORY：仍保留（对 InstanceRef 类的强约束）
          - 引用终止（*-TREF/IREF）→ {@DEST, #text}；原子/枚举直接落标量；其余继续递归（内联）
        """
        info = self._query_class_attributes(session, class_ident)
        class_name = info.get("class_name") or class_ident
        if class_name in seen:
            return class_name, {"type": "object", "properties": {}, "additionalProperties": False}, {}
        seen.add(class_name)

        def _U(s: str | None) -> str:
            return (s or "").strip().upper()

        attrs = info.get("attributes") or []

        # ---- 规则/表 ----
        choice_map = globals().get("CHOICE_ONE_OF",
                                   {})  # e.g. AUTOSARVARIABLEREF → {"AUTOSAR-VARIABLE-IREF","LOCAL-VARIABLE-REF",...}
        xor_map = globals().get("XOR_WITH_MANDATORY", {})  # e.g. *INSTANCE-REF 的必选 + 三组选一分组
        always_map = globals().get("ALWAYS_INCLUDE_OPTIONALS", {})

        # ---- Round1 白名单：来自父容器（例如 ACCESSED-VARIABLE / SERVER-CALL-POINTS / RUNNABLE-ENTITY 等）----
        allowed_from_design: set[str] = set()
        if parent_container_tag:
            allowed_from_design |= {_U(x) for x in (design_index.get(_U(parent_container_tag)) or set())}

        class_up = _U(class_ident)

        # ---- CHOICE_ONE_OF 只在“无 Round1 白名单”时兜底放行 ----
        # 例如：在 ACCESSED-VARIABLE 容器下，Round1 若已选择了 AUTOSAR-VARIABLE-IREF，
        # 则 allowed_from_design 已非空，此时不要把其它候选也放进去。
        choice_set = set(choice_map.get(class_up, set()))
        if choice_set and not allowed_from_design:
            allowed_from_design |= {_U(x) for x in choice_set}

        # ---- 可选放行表（精简后）：仅事件起点引用。InstanceRef 仍然自动放行本类拥有的 tag/wrapper 键 ----
        extra_opt: set[str] = set(always_map.get(class_up, set()))
        if class_up.endswith("INSTANCEREF"):
            for a in attrs:
                if a.get("xml_tag"):
                    extra_opt.add(_U(a.get("xml_tag")))
                if a.get("xml_wrapper_tag"):
                    extra_opt.add(_U(a.get("xml_wrapper_tag")))

        def _keep(a: dict) -> bool:
            # 选择：KG必选(minOccurs>=1) ∪ Round1白名单 ∪ 额外可选（事件引用等）
            try:
                min_occ = int(a.get("minOccurs") or a.get("pure_minOccurs") or 0)
            except Exception:
                min_occ = 0
            if min_occ >= 1:
                return True
            w = _U(a.get("xml_wrapper_tag"))
            t = _U(a.get("xml_tag"))
            n = _U(a.get("name"))
            if (w in allowed_from_design) or (t in allowed_from_design) or (n in allowed_from_design):
                return True
            if (w in extra_opt) or (t in extra_opt) or (n in extra_opt):
                return True
            return False

        attrs = [a for a in attrs if _keep(a)]

        props: dict[str, dict] = {}
        required: list[str] = []
        definitions: dict[str, dict] = {}

        # ---- 标量映射 ----
        def _scalar_from_base(base: str | None) -> dict:
            b = _U(base)
            if b in {"BOOLEAN"}: return {"type": "boolean"}
            if b in {"INT", "INTEGER", "INT8", "INT16", "INT32", "INT64"}: return {"type": "integer"}
            if b in {"FLOAT", "DOUBLE", "DECIMAL", "NUMBER"}: return {"type": "number"}
            return {"type": "string"}

        def _scalar_from_name_hint(key: str) -> dict:
            u = _U(key)
            if any(tok in u for tok in ("NAME", "ID", "REF", "TAG")): return {"type": "string"}
            if any(tok in u for tok in ("COUNT", "NUM", "RATE", "RATIO", "LENGTH")): return {"type": "number"}
            return {"type": "string"}

        for a in attrs:
            tag = _U(a.get("xml_tag"))
            wrap = _U(a.get("xml_wrapper_tag"))
            key = wrap or tag or _U(a.get("name"))
            if not key:
                continue

            # occurs / array 判定
            try:
                min_occ = int(a.get("minOccurs") or a.get("pure_minOccurs") or 0)
            except Exception:
                min_occ = 0
            max_occ_raw = a.get("maxOccurs", a.get("pure_maxOccurs"))

            default_is_array = _is_array_occurs(max_occ_raw)
            is_array = _override_container_shape(_U(key), default_is_array)

            # KG 的类型名有时在 "type_name"，有时在 "type"
            tname = a.get("type_name") or a.get("type")

            # ---- 引用终止：由结构判定（DEST-only）或明显 TREF 标签 ----
            if self._is_ref_terminal(session, tname, tag):
                val = _emit_ref_object_schema(is_array)
                if is_array:
                    if min_occ > 0:
                        val.setdefault("minItems", min_occ)
                    try:
                        if max_occ_raw and str(max_occ_raw).lower() != "unbounded":
                            val["maxItems"] = int(max_occ_raw)
                    except Exception:
                        pass
                props[key] = val
                if min_occ >= 1:
                    required.append(key)
                props[key]["x-xml-tag"] = tag
                props[key]["x-xml-wrapper-tag"] = wrap
                continue

            # ---- 有 TYPE_OF：原子/枚举 终止 或 继续递归（直接内联子 schema）----
            if tname:
                t_is_attr = bool(a.get("t_is_attribute"))
                t_is_enum = bool(a.get("t_is_enum")) or bool(a.get("t_enum_values"))
                t_base = a.get("t_base")
                t_pattern = a.get("t_pattern")
                enum_vals = a.get("t_enum_values") or []

                # 原子/枚举：直接落标量
                if t_is_attr or t_is_enum:
                    scalar = _scalar_from_base(t_base)
                    if enum_vals:
                        scalar = {**scalar, "enum": enum_vals}
                    if t_pattern:
                        scalar = {**scalar, "pattern": t_pattern}
                    val = {"type": "array", "items": scalar} if is_array else scalar
                    if is_array and min_occ > 0:
                        val.setdefault("minItems", min_occ)
                    props[key] = val
                    if min_occ >= 1:
                        required.append(key)
                    props[key]["x-xml-tag"] = tag
                    props[key]["x-xml-wrapper-tag"] = wrap
                    continue

                # 递归（若下层在 design_index 有专属白名单，则切 parent；否则沿用父容器）
                next_key = _U(a.get("xml_wrapper_tag") or a.get("xml_tag"))
                child_parent = next_key if design_index.get(next_key) else _U(parent_container_tag)

                sub_name, sub_schema, sub_defs = self._build_class_schema_recursive(
                    session=session,
                    class_ident=tname,
                    parent_container_tag=child_parent,
                    design_index=design_index,
                    seen=seen
                )
                definitions.update(sub_defs)

                val = {"type": "array", "items": sub_schema} if is_array else sub_schema
                if is_array:
                    if min_occ > 0:
                        val["minItems"] = min_occ
                    try:
                        if max_occ_raw and str(max_occ_raw).lower() != "unbounded":
                            val["maxItems"] = int(max_occ_raw)
                    except Exception:
                        pass
                props[key] = val
                if min_occ >= 1:
                    required.append(key)
                props[key]["x-xml-tag"] = tag
                props[key]["x-xml-wrapper-tag"] = wrap
                continue

            # ---- 无 TYPE_OF：叶子兜底（名称/声明类型启发）----
            if self._is_ref_terminal(session, None, tag):
                val = _emit_ref_object_schema(is_array)
            else:
                if a.get("a_is_primitive"):
                    scalar = {"type": "string"}
                elif a.get("a_declared_type"):
                    scalar = _scalar_from_base(a.get("a_declared_type"))
                else:
                    scalar = _scalar_from_name_hint(key)
                val = {"type": "array", "items": scalar} if is_array else scalar

            if is_array and min_occ > 0:
                val.setdefault("minItems", min_occ)
            props[key] = val
            if min_occ >= 1:
                required.append(key)
            props[key]["x-xml-tag"] = tag
            props[key]["x-xml-wrapper-tag"] = wrap

        # ---- 组装当前类的 schema ----
        schema: dict = {"type": "object", "properties": props, "additionalProperties": False}
        if required:
            schema["required"] = required

        # ================= 判别式“三选一”兜底（仅基于“当前 props 中实际存在的候选”） =================
        # A) CHOICE_ONE_OF：例如 AUTOSARVARIABLEREF 的多个子分支
        if class_up in choice_map:
            options = [k for k in choice_map[class_up] if k in props]
            if len(options) >= 2:
                schema["properties"]["variant"] = {"type": "string", "enum": options}
                schema.setdefault("required", [])
                if "variant" not in schema["required"]:
                    schema["required"].append("variant")
                conditions = []
                for opt in options:
                    forbid = [x for x in options if x != opt]
                    conditions.append({
                        "if": {"properties": {"variant": {"const": opt}}},
                        "then": {
                            "required": [opt],
                            "not": {"anyOf": [{"required": [f]} for f in forbid]}
                        }
                    })
                schema.setdefault("allOf", []).extend(conditions)
            elif len(options) == 1:
                schema.setdefault("required", [])
                if options[0] not in schema["required"]:
                    schema["required"].append(options[0])

        # B) XOR_WITH_MANDATORY：必选 + 互斥组（按“当前 props 中存在的键”裁剪）
        if class_up in xor_map:
            rule = xor_map[class_up]
            # must
            must = list(rule.get("mandatory", set()) or [])
            if must:
                schema.setdefault("required", [])
                for k in must:
                    if k in props and k not in schema["required"]:
                        schema["required"].append(k)
            # xor groups
            groups = list(rule.get("xor_groups", []) or [])
            reps: list[str] = []
            for g in groups:
                rep = next((k for k in g if k in props), None)
                if rep:
                    reps.append(rep)
            if len(reps) >= 2:
                if "variant" in schema["properties"]:
                    old_enum = set(schema["properties"]["variant"].get("enum", []))
                    schema["properties"]["variant"]["enum"] = sorted(old_enum.union(reps))
                else:
                    schema["properties"]["variant"] = {"type": "string", "enum": reps}
                    schema.setdefault("required", [])
                    if "variant" not in schema["required"]:
                        schema["required"].append("variant")
                conditions = []
                for opt in reps:
                    forbid = [x for x in reps if x != opt]
                    conditions.append({
                        "if": {"properties": {"variant": {"const": opt}}},
                        "then": {
                            "required": [opt],
                            "not": {"anyOf": [{"required": [f]} for f in forbid]}
                        }
                    })
                schema.setdefault("allOf", []).extend(conditions)
            elif len(reps) == 1:
                schema.setdefault("required", [])
                if reps[0] not in schema["required"]:
                    schema["required"].append(reps[0])

        return class_name, schema, definitions

    # ------------------------分块构建----------------------------------------
    # ======================== 固定骨架 + 局部递归 入口 ========================

    def generate_component_schema_fixed(self, comp_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        固定上层骨架（PORTS / INTERNAL-BEHAVIORS / RUNNABLES / EVENTS），
        仅在三处“内层区域”做类型驱动的递归：
          - PORTS 下的条目对象（P-PORT-PROTOTYPE / R-PORT-PROTOTYPE / …）
          - RUNNABLE-ENTITY 下各 elements wrapper（如 DATA-SEND-POINTS 等）
          - EVENTS 下各事件类型（如 TIMING-EVENT、DATA-RECEIVED-EVENT …）

        参数:
          comp_plan: Round1 的单组件计划（含 element_design）

        返回:
          JSON Schema（definitions里含局部递归生成的类型；顶层仅包含 { "<comp_name>": { ... } }）
        """
        name = (comp_plan.get("name") or "SWC").strip()
        element_design = comp_plan.get("element_design") or {}

        # Round1 → 设计索引
        design_index = self._build_design_index(element_design)

        definitions: Dict[str, Any] = {}
        with self.driver.session() as session:
            # --- 1) PORTS 区 ---
            ports_obj, defs_ports = self._build_ports_section(session, design_index)
            definitions.update(defs_ports)

            # --- 2) RUNNABLES 与 EVENTS（都在 INTERNAL-BEHAVIORS / SWC-INTERNAL-BEHAVIOR 之下） ---
            runnables_obj, defs_runs = self._build_runnables_section(session, design_index)
            definitions.update(defs_runs)

            events_obj, defs_events = self._build_events_section(session, design_index)
            definitions.update(defs_events)

        # ----- 3) 组件根骨架（不从 KG 根类递归，直接模板化） -----
        root_props: Dict[str, Any] = {
            "SHORT-NAME": {"type": "string"}
        }
        root_required: List[str] = ["SHORT-NAME"]

        # 是否需要 PORTS
        if "PORTS" in design_index.get("__TOP__", set()):
            if ports_obj is not None:
                root_props["PORTS"] = ports_obj
                # 端口不是强必填：由实例是否需要决定；如需强制必填可取消下行注释
                # root_required.append("PORTS")

        # 是否需要 INTERNAL-BEHAVIORS
        if "INTERNAL-BEHAVIORS" in design_index.get("__TOP__", set()):
            # 固定两级壳：INTERNAL-BEHAVIORS/SWC-INTERNAL-BEHAVIOR
            ib_props = {
                "SWC-INTERNAL-BEHAVIOR": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "SHORT-NAME": {"type": "string"},
                        # RUNNABLES / EVENTS 两块：按需放入（为空则不放）
                        **({"RUNNABLES": runnables_obj} if runnables_obj is not None else {}),
                        **({"EVENTS": events_obj} if events_obj is not None else {}),
                    },
                    "required": ["SHORT-NAME"],
                }
            }
            root_props["INTERNAL-BEHAVIORS"] = {
                "type": "object",
                "additionalProperties": False,
                "properties": ib_props,
                "x-xml-tag": "INTERNAL-BEHAVIORS"
            }
            # 同上，不强制 required，按需打开
            # root_required.append("INTERNAL-BEHAVIORS")

        swc_root = {
            "type": "object",
            "additionalProperties": False,
            "properties": root_props,
            "required": root_required,
        }

        # 顶层包装：<comp_name> : $ref SWC-ROOT
        schema = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                name: {"$ref": "#/definitions/SWC-ROOT"}
            },
            "required": [name],
            "definitions": {
                **definitions,
                "SWC-ROOT": swc_root
            }
        }
        return schema

    # ======================== 三个内层构建器 ========================

    def _build_ports_section(
            self, session, design_index: Dict[str, set]
    ) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        """
        固定生成 PORTS 壳；条目级（P-PORT-PROTOTYPE/R-PORT-PROTOTYPE/…）用递归生成 item schema

        返回:
          (ports_object_schema or None, definitions)
        """
        if "PORTS" not in design_index.get("__TOP__", set()):
            return None, {}

        requested_types = set(design_index.get("PORTS") or [])
        # 若 Round1 未指明具体类型，给出常用默认
        if not requested_types:
            requested_types = {"P-PORT-PROTOTYPE", "R-PORT-PROTOTYPE"}

        props: Dict[str, Any] = {}
        required: List[str] = []
        definitions: Dict[str, Any] = {}

        for pt in sorted(requested_types):
            # 从条目类开始递归，父容器传 PORTS；向下层仅展开 minOccurs>=1 的属性
            def_name, def_schema, defs = self._build_class_schema_recursive(
                session=session,
                class_ident=pt,  # 可命中 c.name / c.xml_tag / c.xml_wrapper_tag
                parent_container_tag="PORTS",
                design_index=design_index,
                seen=set(),
            )
            # 直接内联，不再引用 definitions
            definitions.update(defs)

            props[pt] = {
                "type": "array",
                "items": def_schema,  # ← inline
                "x-xml-tag": pt
            }
            # 注意：是否 required 取决于 Round1/规则；默认不强制
            # required.append(pt)

        ports_obj = {
            "type": "object",
            "additionalProperties": False,
            "properties": props,
            "x-xml-tag": "PORTS"
        }
        if required:
            ports_obj["required"] = required
        return ports_obj, definitions

    def _build_runnables_section(
            self, session, design_index: Dict[str, set]
    ) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        """
        固定生成 RUNNABLES 壳；不再把 DATA-SEND-POINTS 等 wrapper 当“类”去查，
        而是先从 RUNNABLE-ENTITY 类起跳递归，递归器会依据 design_index['RUNNABLE-ENTITY']
        只展开被 Round1 选中的 wrapper/子块。
        """
        # 顶层是否要求 INTERNAL-BEHAVIORS
        if "INTERNAL-BEHAVIORS" not in design_index.get("__TOP__", set()):
            return None, {}

        allowed = design_index.get("INTERNAL-BEHAVIORS")
        if "RUNNABLE-ENTITY" not in allowed:
            return None, {}

        # Round1 选择的 runnable 子块（wrapper keys）
        selected_keys = set(design_index.get("RUNNABLE-ENTITY") or [])

        definitions: Dict[str, Any] = {}

        # 若 KG 用的是类名 "RunnableEntity"（不是 xml_tag），做一次兜底
        def_name, def_schema, defs = self._build_class_schema_recursive(
            session=session,
            class_ident="RunnableEntity",
            parent_container_tag="RUNNABLE-ENTITY",
            design_index=design_index,
            seen=set(),
        )

        # 直接内联，不再引用 definitions
        definitions.update(defs)

        # RUNNABLES 壳：数组 items 直接内联 RUNNABLE-ENTITY 的 schema
        runnables_obj = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "RUNNABLE-ENTITY": {
                    "type": "array",
                    "items": def_schema,  # ← inline
                }
            },
            "x-xml-tag": "RUNNABLES",
            "required": ["RUNNABLE-ENTITY"] if selected_keys else []
        }
        return runnables_obj, definitions

    def _build_events_section(
            self, session, design_index: Dict[str, set]
    ) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        """
        固定生成 EVENTS 壳；每种事件类型（如 TIMING-EVENT）是一个数组，
        item schema 由对应事件类作为起点的**局部递归**获得。
        - 与原实现的区别：数组 items 直接内联子 schema（不再通过 $ref/definitions）
        - 返回: (events_object_schema or None, definitions)
        """
        # 顶层必须允许 INTERNAL-BEHAVIORS
        if "INTERNAL-BEHAVIORS" not in design_index.get("__TOP__", set()):
            return None, {}

        allowed = design_index.get("INTERNAL-BEHAVIORS") or set()
        if "EVENTS" not in allowed:
            return None, {}

        # Round1 声明的事件类型列表（如 {"TIMING-EVENT", "DATA-RECEIVED-EVENT"}）
        event_types = sorted(design_index.get("EVENTS") or [])
        if not event_types:
            # 未在 Round1 指定事件类型，则不给 EVENTS（也可选择给出空壳）
            return None, {}

        props: Dict[str, Any] = {}
        definitions: Dict[str, Any] = {}

        for et in event_types:
            # 以事件类型（xml_tag）为起点做局部递归，parent_container_tag 固定为 "EVENTS"
            def_name, def_schema, defs = self._build_class_schema_recursive(
                session=session,
                class_ident=et,  # 命中 xml_tag，如 TIMING-EVENT
                parent_container_tag="EVENTS",
                design_index=design_index,
                seen=set(),
            )
            # 仅合并子递归带回的 definitions（通常很小/为空）；不再把本类型挂到 definitions
            definitions.update(defs)

            # 直接内联 items（不使用 $ref）
            props[et] = {
                "type": "array",
                "items": def_schema,  # ← inline 子 schema
                "x-xml-tag": et
            }

        events_obj = {
            "type": "object",
            "additionalProperties": False,
            "properties": props,
            "x-xml-tag": "EVENTS"
            # 如需强制至少出现某类事件，可按需添加 "required": sorted(event_types)
        }
        return events_obj, definitions

    # ------------------------ 顶层构建 API ------------------------

    def generate_single_component_schema(self, comp_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        基于 Round1 单组件计划：{"name","type","element_design"} 生成 JSON Schema。
        只包含：Round1 设计声明的元素 + KG 中 minOccurs≥1 的元素；并按 type 递归。
        """
        comp_name = comp_plan["name"]
        comp_type = comp_plan["type"]
        element_design = comp_plan.get("element_design") or {}

        if not comp_type:
            raise KGQueryError(f"组件 {comp_name} 缺少 type")

        design_index = self._build_design_index(element_design)
        seen: Set[str] = set()

        with self.driver.session() as session:
            top_name, top_schema, definitions = self._build_class_schema_recursive(
                session=session,
                class_ident=comp_type,
                parent_container_tag="__TOP__",
                design_index=design_index,
                seen=seen
            )

        # 产出：顶层以组件名作为唯一属性；definitions 存放顶层类型与子类型
        out = {
            "type": "object",
            "properties": {comp_name: {"$ref": f"#/definitions/{top_name}"}},
            "required": [comp_name],
            "additionalProperties": False,
            "definitions": {**definitions, top_name: top_schema}
        }
        return out

    def generate_multi_component_schema(self, comp_plans: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        多组件场景：每个组件一个顶层键，definitions 中存入每个组件的根类型 Schema。
        """
        if not comp_plans:
            return {"type": "object", "properties": {}, "additionalProperties": False}

        definitions: Dict[str, Any] = {}
        props: Dict[str, Any] = {}
        req: List[str] = []

        for comp in comp_plans:
            name = comp["name"]
            single = self.generate_single_component_schema(comp)
            # 直接引用组件自身根定义
            root_ref = list(single["definitions"].keys())[-1]  # 顶层类型名（最后合入的）
            props[name] = {"$ref": f"#/definitions/{root_ref}"}
            definitions.update(single["definitions"])
            req.append(name)

        return {
            "type": "object",
            "properties": props,
            "required": req,
            "additionalProperties": False,
            "definitions": definitions
        }

    # ------------------------ interface ------------------------
    def generate_multi_interface_schema(self, interface_plans: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        生成多接口Schema - 作为只读参考供组件引用
        按类型分组，同类型接口复用Schema定义
        """
        if not interface_plans:
            return {"type": "object", "properties": {}, "additionalProperties": False}

        # 按类型分组
        interfaces_by_type = {}
        for intf in interface_plans:
            intf_type = intf.get("type", "")
            intf_name = intf.get("name", "")

            if not intf_type:
                raise KGQueryError(f"接口{intf_name}缺少类型定义")

            if intf_type not in interfaces_by_type:
                interfaces_by_type[intf_type] = []
            interfaces_by_type[intf_type].append(intf)

        # 为每个类型生成一次schema，然后复用
        type_definitions = {}
        schemas = {}

        with self.driver.session() as session:
            for intf_type, intfs in interfaces_by_type.items():
                # 检查缓存或生成新Schema
                if intf_type not in type_definitions:
                    # 生成接口类型Schema
                    type_schema = self._build_interface_schema(session, intf_type)
                    type_definitions[intf_type] = type_schema

                # 为该类型的每个接口创建引用
                for intf in intfs:
                    schemas[intf["name"]] = {"$ref": f"#/definitions/{intf_type}"}

        return {
            "type": "object",
            "properties": schemas,
            "definitions": type_definitions,
            "additionalProperties": False
        }

    def _build_interface_schema(self, session, interface_type: str) -> Dict[str, Any]:
        """构建接口类型Schema"""
        # 查询接口类型结构
        info = self._query_class_attributes(session, interface_type)

        props = {}
        req = []

        # 处理必需属性
        for attr in info["attributes"]:
            min_occ = int(attr.get("minOccurs", 0))
            if min_occ >= 1:
                key = attr.get("xml_tag") or attr.get("name")
                if key:
                    # 简化处理：接口主要包含标量属性和数据元素
                    if key == "DATA-ELEMENTS":
                        props[key] = self._build_data_elements_schema()
                    elif key == "OPERATIONS":
                        props[key] = self._build_operations_schema()
                    else:
                        props[key] = {"type": "string"}
                    req.append(key)

        schema = {"type": "object", "properties": props, "additionalProperties": False}
        if req:
            schema["required"] = req

        return schema

    def _build_data_elements_schema(self) -> Dict[str, Any]:
        """构建DATA-ELEMENTS结构"""
        return {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "SHORT-NAME": {"type": "string"},
                    "TYPE-TREF": {
                        "type": "object",
                        "properties": {
                            "@DEST": {"type": "string", "const": "IMPLEMENTATION-DATA-TYPE"},
                            "#text": {"type": "string"}
                        },
                        "required": ["@DEST", "#text"]
                    }
                },
                "required": ["SHORT-NAME", "TYPE-TREF"]
            }
        }

    def _build_operations_schema(self) -> Dict[str, Any]:
        """构建OPERATIONS结构"""
        return {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "SHORT-NAME": {"type": "string"},
                    "ARGUMENTS": {"type": "object"}
                },
                "required": ["SHORT-NAME"]
            }
        }
    # ------------------------ 资源管理 ------------------------

    def close(self):
        try:
            self.driver.close()
        except Exception:
            pass

query_engine = DynamicQueryEngine()