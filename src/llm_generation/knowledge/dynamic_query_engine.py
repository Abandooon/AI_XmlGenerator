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
    # "AUTOSARVARIABLEREF": {
    #     "AUTOSAR-VARIABLE-IREF",
    #     "LOCAL-VARIABLE-REF",
    #     "AUTOSAR-VARIABLE-IN-IMPL-DATATYPE",
    # },
}

# InstanceRef 的“必选 + 三选一”规则（支持同义键：tag / wrapper）
# mandatory: 这些键必须出现（即便 KG 的 minOccurs 标成 0 也强制）
# xor_groups: 三选一，每个元素是同义键集合（取其中存在于 props 的那个）
XOR_WITH_MANDATORY = {
    # "VARIABLEINATOMICSWCTYPEINSTANCEREF": {
    #     "mandatory": {"TARGET-DATA-PROTOTYPE-REF"},
    #     "xor_groups": [
    #         {"PORT-PROTOTYPE-REF"},
    #         {"ROOT-VARIABLE-DATA-PROTOTYPE-REF"},
    #         {"CONTEXT-DATA-PROTOTYPE-REFS", "CONTEXT-DATA-PROTOTYPE-REF"},  # tag / wrapper 兼容
    #     ],
    # },
    # "ARVARIABLEINIMPLEMENTATIONDATAINSTANCEREF": {
    #     "mandatory": {"TARGET-DATA-PROTOTYPE-REF"},
    #     "xor_groups": [
    #         {"PORT-PROTOTYPE-REF"},
    #         {"ROOT-VARIABLE-DATA-PROTOTYPE-REF"},
    #         {"CONTEXT-DATA-PROTOTYPE-REFS", "CONTEXT-DATA-PROTOTYPE-REF"},
    #     ],
    # },

}

# ==================== Optional 放行（精简后） ====================
# 只保留事件起点引用这类“便捷但不改变结构选择权”的可选放行；
# 删除会越权影响结构选择的条目：RUNNABLE-ENTITY / SERVERCALLPOINTS 相关。
ALWAYS_INCLUDE_OPTIONALS: dict[str, set[str]] = {
    # 事件：常见的“起点引用”在 KG 中多为 0..1，但工程上几乎总需要
    "SWC-MODE-SWITCH-EVENT": {"START-ON-EVENT-REF"},
    "DATA-WRITE-COMPLETED-EVENT": {"START-ON-EVENT-REF"},
    "OPERATION-INVOKED-EVENT": {"START-ON-EVENT-REF"},
    "TIMING-EVENT": {"START-ON-EVENT-REF"},
    "ASYNCHRONOUS-SERVER-CALL-RETURNS-EVENT": {"START-ON-EVENT-REF"},
    "EXTERNAL-TRIGGER-OCCURRED-EVENT": {"START-ON-EVENT-REF"},
    "DATA-RECEIVED-EVENT": {"START-ON-EVENT-REF"},
    "MODE-SWITCHED-ACK-EVENT": {"START-ON-EVENT-REF"},
    "SWC-MODE-MANAGER-ERROR-EVENT": {"START-ON-EVENT-REF"},
    "INTERNAL-TRIGGER-OCCURRED-EVENT": {"START-ON-EVENT-REF"},
    "BACKGROUND-EVENT": {"START-ON-EVENT-REF"},
    "DATA-SEND-COMPLETED-EVENT": {"START-ON-EVENT-REF"},
    "INIT-EVENT": {"START-ON-EVENT-REF"},
    "DATA-RECEIVE-ERROR-EVENT": {"START-ON-EVENT-REF"},
    "TRANSFORMER-HARD-ERROR-EVENT": {"START-ON-EVENT-REF"},
}

# 哪些 XML wrapper 在 Schema 阶段要折叠，生成完成后再补壳
COLLAPSED_WRAPPERS = {"INTERNAL-BEHAVIORS", "RUNNABLES"}

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

def _emit_ref_object_schema(is_array: bool, dest_enum: list[str] | None = None) -> dict:
    base = {
        "type": "object",
        "properties": {
            "@DEST": {"type": "string"},
            "#text": {"type": "string"}
        },
        "required": ["@DEST", "#text"]
    }
    if dest_enum:
        base["properties"]["@DEST"]["enum"] = sorted({str(x) for x in dest_enum if x})
    return {"type": "array", "items": base, "minItems": 1} if is_array else base


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
          - 还会消费 elements[].preselect[]，将：
              of -> variant 加入白名单（保证分支被展开）
              variant -> include 子键加入白名单（保证只展开所选子键）
              ✅ 新增：wrapper -> of（确保在该 wrapper 下放行该锚点分支）
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

                        # ✅ 同步到 wrapper：确保本 wrapper 下放行该 of（例如 DATA-SEND-POINTS → ACCESSED-VARIABLE）
                        if run_key and of:
                            idx.setdefault(run_key, set()).add(of)

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
          - CHOICE_ONE_OF：仅在“该容器没有任何【相关】Round1 白名单”时作为兜底放行
          - XOR_WITH_MANDATORY：只做约束（强制必选 + 三选一），不主动放行新键
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
        choice_map = globals().get("CHOICE_ONE_OF", {})
        xor_map = globals().get("XOR_WITH_MANDATORY", {})
        always_map = globals().get("ALWAYS_INCLUDE_OPTIONALS", {})

        # ---- Round1 白名单：来自父容器（例如 ACCESSED-VARIABLE / RUNNABLE-ENTITY / AUTOSAR-VARIABLE-IREF 等）----
        allowed_from_design: set[str] = set()
        if parent_container_tag:
            allowed_from_design |= {_U(x) for x in (design_index.get(_U(parent_container_tag)) or set())}

        # ★ 额外：全局设计键集合（用于允许“锚点”属性如 ACCESSED-VARIABLE 先被保留）
        design_global_keys: set[str] = {_U(k) for k in (design_index.keys() or [])}
        design_all_selected_values: set[str] = set()
        for v in (design_index.values() or []):
            design_all_selected_values |= {_U(x) for x in (v or set())}

        class_up = _U(class_ident)

        # ---- 计算“本层候选名集合”，用于判定 Round1 白名单是否与本层相关 ----
        candidate_names: set[str] = set()
        for a in attrs:
            for nm in (a.get("xml_wrapper_tag"), a.get("xml_tag"), a.get("name")):
                if nm:
                    candidate_names.add(_U(nm))

        # ---- CHOICE_ONE_OF 只在“无【相关】Round1 白名单”时兜底放行 ----
        choice_set = set(choice_map.get(class_up, set()))
        has_related_design = bool(allowed_from_design & (candidate_names | choice_set))
        if choice_set and not has_related_design:
            # 兜底：放入所有候选（例如 AUTOSARVARIABLEREF 的各个变体），避免无路可走
            allowed_from_design |= {_U(x) for x in choice_set}

        # ---- 可选放行：事件引用等（来自 ALWAYS_INCLUDE_OPTIONALS）----
        extra_opt: set[str] = set(always_map.get(class_up, set()))

        # ---- InstanceRef 类的放行策略（关键点）----
        if class_up.endswith("INSTANCEREF"):
            rule = xor_map.get(class_up, {})
            mandatory = {_U(x) for x in (rule.get("mandatory") or set())}
            if has_related_design or allowed_from_design:
                # 只放行必选；其余由 allowed_from_design（来自 variant 的 include）决定
                extra_opt |= mandatory
            else:
                # 兜底（没有设计约束）：放行本类所有键，避免剪空
                for a in attrs:
                    if a.get("xml_tag"):
                        extra_opt.add(_U(a.get("xml_tag")))
                    if a.get("xml_wrapper_tag"):
                        extra_opt.add(_U(a.get("xml_wrapper_tag")))

        def _keep(a: dict) -> bool:
            # 1) KG 必选
            try:
                min_occ = int(a.get("minOccurs") or a.get("pure_minOccurs") or 0)
            except Exception:
                min_occ = 0
            if min_occ >= 1:
                return True

            w = _U(a.get("xml_wrapper_tag"))
            t = _U(a.get("xml_tag"))
            n = _U(a.get("name"))

            # 2) 命中“本层相关”的 Round1 白名单
            if (w in allowed_from_design) or (t in allowed_from_design) or (n in allowed_from_design):
                return True

            # 3) 设计锚点 / 选中值（跨层允许）
            if (w in design_global_keys) or (t in design_global_keys) or (n in design_global_keys):
                return True
            if (w in design_all_selected_values) or (t in design_all_selected_values) or (
                    n in design_all_selected_values):
                return True

            # 4) 额外放行（事件引用、InstanceRef 的 mandatory 键等）
            if (w in extra_opt) or (t in extra_opt) or (n in extra_opt):
                return True

            return False

        # 基于上述规则过滤属性
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

        for a in attrs:
            key = a.get("name") or a.get("xml_tag") or a.get("xml_wrapper_tag") or "FIELD"
            key = key.strip()
            tag = a.get("xml_tag")
            wrap = a.get("xml_wrapper_tag")
            min_occ = int(a.get("minOccurs") or a.get("pure_minOccurs") or 0)
            max_occ_raw = a.get("maxOccurs")
            default_is_array = _is_array_occurs(max_occ_raw)
            is_array = _override_container_shape(_U(key), default_is_array)

            tname = a.get("type_name") or a.get("type")

            # 引用终止（TREF/IREF 或 DEST-only 类）
            if self._is_ref_terminal(session, tname, tag):
                dest_enum = None
                try:
                    # 以 xml_tag 优先，其次用 type_name 去查“包含 DEST 的类”
                    tref_ident = (tag or tname)
                    info = self._query_class_attributes(session, tref_ident) or {}
                    for _a in (info.get("attributes") or []):
                        # 找到 XML 属性 DEST
                        _is_attr = bool(_a.get("isXmlAttr")) or bool(_a.get("is_xml_attribute"))
                        _tag = (_a.get("xml_tag") or _a.get("name") or "").strip().upper()
                        if _is_attr and _tag == "DEST":
                            evs = _a.get("t_enum_values") or []
                            dest_enum = [e for e in evs if e] or None
                            break
                except Exception:
                    pass

                val = _emit_ref_object_schema(is_array, dest_enum)
                if is_array and min_occ > 0:
                    val.setdefault("minItems", min_occ)
                    try:
                        if max_occ_raw and str(max_occ_raw).lower() != "unbounded":
                            val["maxItems"] = int(max_occ_raw)
                    except Exception:
                        pass
                props[key] = val
                if min_occ >= 1:
                    required.append(key)
                if tag:
                    props[key]["x-xml-tag"] = tag
                if wrap and wrap not in COLLAPSED_WRAPPERS:
                    props[key]["x-xml-wrapper-tag"] = wrap

                continue

            # ---- 有 TYPE_OF：原子/枚举 终止 或 继续递归（直接内联子 schema）----
            if tname:
                t_is_attr = bool(a.get("t_is_attribute"))
                t_is_enum = bool(a.get("t_is_enum")) or bool(a.get("t_enum_values"))
                t_base = a.get("t_base")
                t_pattern = a.get("t_pattern")

                # 1) 终止：原子/枚举
                if t_is_attr or t_is_enum or t_base:
                    scalar = _scalar_from_base(t_base)
                    if t_is_enum:
                        enum_vals = a.get("t_enum_values") or []
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
                    if tag:
                        props[key]["x-xml-tag"] = tag
                    if wrap and wrap not in COLLAPSED_WRAPPERS:
                        props[key]["x-xml-wrapper-tag"] = wrap

                    continue

                # 2) 递归（若下层在 design_index 有专属白名单，则切 parent；否则沿用父容器）
                next_key = _U(a.get("xml_wrapper_tag") or a.get("xml_tag"))
                child_parent = next_key if design_index.get(next_key) else _U(parent_container_tag)

                sub_name, sub_schema, sub_defs = self._build_class_schema_recursive(
                    session=session,
                    class_ident=tname,
                    parent_container_tag=child_parent,
                    design_index=design_index,
                    seen=set(seen)
                )
                definitions.update(sub_defs)

                val = {"type": "array", "items": sub_schema} if is_array else sub_schema
                if is_array and min_occ > 0:
                    val.setdefault("minItems", min_occ)
                props[key] = val
                if min_occ >= 1:
                    required.append(key)
                if tag:
                    props[key]["x-xml-tag"] = tag
                if wrap and wrap not in COLLAPSED_WRAPPERS:
                    props[key]["x-xml-wrapper-tag"] = wrap

                continue

            # ---- 无 TYPE_OF：按 a.isEnum/a.baseType/命名启发落标量 ----
            base_type = a.get("a_baseType") or a.get("baseType")
            is_enum = bool(a.get("a_isEnum"))
            if is_enum:
                val = {"type": "string", "enum": a.get("enum_values") or []}
            else:
                prim = self._guess_primitive_from_name(_U(base_type) or _U(tag) or _U(key))
                val = prim or {"type": "string"}
            if is_array and min_occ > 0:
                val = {"type": "array", "items": val}
                val.setdefault("minItems", min_occ)
            props[key] = val
            if min_occ >= 1:
                required.append(key)
            if tag:
                props[key]["x-xml-tag"] = tag
            if wrap and wrap not in COLLAPSED_WRAPPERS:
                props[key]["x-xml-wrapper-tag"] = wrap

        # ---- 组装当前类的 schema ----
        schema: dict = {"type": "object", "properties": props, "additionalProperties": False}
        if required:
            schema["required"] = required

        # ✅ Round1 include → required：若 Round1 在当前类（如 AUTOSAR-VARIABLE-IREF）声明了 include 子键，
        #    则把这些子键提升为 required（按 x-xml-tag 对齐 JSON 键名）
        includes = {_U(x) for x in (design_index.get(class_up) or set())}
        if includes:
            # 建立 xmlTag → jsonKey 的映射
            tag_to_json_key = {}
            for _k, _v in props.items():
                if isinstance(_v, dict):
                    xt = _v.get("x-xml-tag")
                    if xt:
                        tag_to_json_key[_U(xt)] = _k
            req = schema.setdefault("required", [])
            for inc_tag in includes:
                jk = tag_to_json_key.get(inc_tag)
                if jk and jk not in req:
                    req.append(jk)

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

        # B) XOR_WITH_MANDATORY：例如 *INSTANCE-REF 的 TARGET 必选 + 定位三选一
        rule = xor_map.get(class_up)
        if rule:
            mandatory = [x for x in (rule.get("mandatory") or []) if x in props]
            reps = [list(g)[0] for g in (rule.get("xor_groups") or []) if any(x in props for x in g)]
            if mandatory:
                schema.setdefault("required", [])
                for m in mandatory:
                    if m not in schema["required"]:
                        schema["required"].append(m)
            if len(reps) >= 2:
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

    # ======================== 固定骨架 + 局部递归 入口 ========================
    def _xmlize_schema_properties(self, schema_fragment: dict) -> dict:
        """
        将递归阶段产生的“驼峰键 + x-xml-wrapper-tag/x-xml-tag 标注”的 schema 片段，
        在最终输出阶段重写为 AUTOSAR 风格键名：
          - 同时存在 wrapper/tag：外层用 wrapper，当容器键；容器内部以 tag 作为元素键
            * 若原节点为 array：W -> { T: array(items=原items) }
            * 若原节点为 object/scalar：仅将键重命名为 W
          - wrapper 为空/不存在：仅使用 tag；若 tag 也无，则保留原键
          - 递归处理 object.properties / array.items，并同步 required 键名映射
        注意：仅在最终组装 schema 前调用；不要在 KG 递归阶段调用。
        """
        from copy import deepcopy
        node = deepcopy(schema_fragment)

        def _walk(n: dict) -> dict:
            if not isinstance(n, dict):
                return n

            # 先递归 array.items（这样 items 已经完成内部重命名）
            if n.get("type") == "array" and isinstance(n.get("items"), dict):
                n["items"] = _walk(n["items"])

            # 再处理对象 properties
            if n.get("type") == "object" and isinstance(n.get("properties"), dict):
                old_props = n["properties"]
                new_props = {}
                # 旧键 → 新键 的映射，用于同步 required
                key_map = {}

                for old_key, sub in list(old_props.items()):
                    sub2 = _walk(sub)  # 先对子树进行重命名/规范化

                    wrapper = sub2.get("x-xml-wrapper-tag")
                    tag = sub2.get("x-xml-tag")

                    # 默认值
                    new_key = old_key
                    new_val = sub2

                    if wrapper:
                        # 有 wrapper，优先作为外层容器键
                        new_key = wrapper
                        if isinstance(sub2, dict) and sub2.get("type") == "array" and tag:
                            # 规则：W -> { T: 原 array }
                            arr = {"type": "array"}
                            # 继承原 array 的 items/min/maxItems
                            if "items" in sub2:
                                arr["items"] = sub2["items"]
                            if "minItems" in sub2:
                                arr["minItems"] = sub2["minItems"]
                            if "maxItems" in sub2:
                                arr["maxItems"] = sub2["maxItems"]
                            new_val = {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {tag: arr},
                                "required": [tag]
                            }
                        else:
                            # 非 array：仅改键为 wrapper，值保持
                            new_val = sub2
                            if isinstance(new_val, dict) and new_val.get("type") == "object" \
                                    and isinstance(new_val.get("properties"), dict):
                                new_val.setdefault("additionalProperties", False)
                                new_val["required"] = sorted(list(new_val["properties"].keys()))
                    else:
                        # 无 wrapper：若有 xml tag，用 xml tag 改键；否则保留旧键
                        if tag:
                            new_key = tag
                            new_val = sub2
                            if isinstance(new_val, dict) and new_val.get("type") == "object" \
                                    and isinstance(new_val.get("properties"), dict):
                                new_val.setdefault("additionalProperties", False)
                                new_val["required"] = sorted(list(new_val["properties"].keys()))

                    new_props[new_key] = new_val
                    key_map[old_key] = new_key

                # 应用 properties 替换
                n["properties"] = new_props

                # 同步 required 键名
                if isinstance(n.get("required"), list):
                    n["required"] = [key_map.get(k, k) for k in n["required"]]

                # 本层兜底：若本层未显式 or 未写全 required，按 strict 规则补成“全部子键”
                if isinstance(n.get("properties"), dict):
                    all_keys = sorted(list(n["properties"].keys()))
                    if not isinstance(n.get("required"), list) or set(n["required"]) != set(all_keys):
                        n["required"] = all_keys

            return n

        return _walk(node)

    def generate_component_schema_fixed(self, comp_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        固定上层骨架（PORTS / INTERNAL-BEHAVIORS / RUNNABLES / EVENTS），
        三处“内层区域”做类型驱动递归（端口条目、runnable 子容器、事件类型）。
        —— 保持递归阶段用驼峰键以兼容 KG 查询；最终打包时统一替换为 AUTOSAR 标签键。
        返回：JSON Schema（顶层键 = 组件类型名；内联根；仍保留 definitions 以备后续扩展）
        """
        name = (comp_plan.get("name") or "SWC").strip()
        comp_type = (comp_plan.get("type") or "ECU-ABSTRACTION-SW-COMPONENT-TYPE").strip()
        element_design = comp_plan.get("element_design") or {}

        # Round1 → 设计索引
        design_index = self._build_design_index(element_design)

        definitions: Dict[str, Any] = {}
        with self.driver.session() as session:
            # 1) PORTS
            ports_obj, defs_ports = self._build_ports_section(session, design_index)
            definitions.update(defs_ports)

            # 2) RUNNABLES / EVENTS（在 INTERNAL-BEHAVIORS 下）
            runnables_obj, defs_runs = self._build_runnables_section(session, design_index)
            definitions.update(defs_runs)

            events_obj, defs_events = self._build_events_section(session, design_index)
            definitions.update(defs_events)

        # 3) 组件根骨架（模板化，不从 KG 根类递归）
        root_props: Dict[str, Any] = {
            "SHORT-NAME": {
                "type": "string",
                # 给 LLM 友好的示例，但不强约束（避免把 name 锁死为 const）
                "examples": [name],
            }
        }
        root_required: List[str] = ["SHORT-NAME"]

        if "PORTS" in design_index.get("__TOP__", set()) and ports_obj is not None:
            root_props["PORTS"] = ports_obj
            # 你是否强制 PORTS 必填取决于策略，这里保持“不强制”，如需严格可解开下一行
            # root_required.append("PORTS")

        # 先构建 runnables 的 “条目” schema（def_schema），保持你原本的递归/definitions 逻辑
        def_schema, definitions_runnables = self._build_runnable_entity_definition(session, design_index)
        definitions.update(definitions_runnables or {})

        # 事件 EVENT 区域（如有），保持你原有的构建逻辑
        events_obj, definitions_events = self._build_events_section(session, design_index)
        definitions.update(definitions_events or {})

        # === 扁平化：SWC-INTERNAL-BEHAVIOR 直接挂 RUNNABLE-ENTITY 数组（不再套 RUNNABLES 壳） ===
        # 扁平 INTERNAL-BEHAVIORS 与 RUNNABLES：只保留 SWC-INTERNAL-BEHAVIOR 与其下的 RUNNABLE-ENTITY
        if "INTERNAL-BEHAVIORS" in design_index.get("__TOP__", set()):
            sib_props = {
                "SHORT-NAME": {"type": "string"},
                # 折叠 RUNNABLES：把 RUNNABLES 容器里的 RUNNABLE-ENTITY 直接暴露出来
                **(
                    {"RUNNABLE-ENTITY": (runnables_obj.get("properties") or {}).get("RUNNABLE-ENTITY")}
                    if isinstance(runnables_obj, dict) else {}
                ),
                # 事件仍使用原来的 EVENTS 结构（本次仅折叠 RUNNABLES，EVENTS 保持不变）
                **({"EVENTS": events_obj} if events_obj is not None else {}),
            }
            # required 要覆盖当前 properties 的所有键，避免 Structured Outputs 校验缺键
            sib_required = sorted([k for k, v in (sib_props or {}).items() if v is not None])

            root_props["SWC-INTERNAL-BEHAVIOR"] = {
                "type": "object",
                "additionalProperties": False,
                "properties": sib_props,
                "required": sib_required,
            }

        # 根对象 strict：required = 当前 properties 的全部键
        swc_root = {
            "type": "object",
            "additionalProperties": False,
            "properties": root_props,
            "required": sorted(list(root_props.keys())),
        }

        # ✅ 关键收尾：把根片段统一替换为 AUTOSAR 标签键（wrapper/tag），仅在最终输出前执行
        swc_root_xml = self._xmlize_schema_properties(swc_root)

        # ✅ 顶层：用“组件类型名”作为根键，且直接内联（不再 $ref）
        schema: Dict[str, Any] = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                comp_type: swc_root_xml
            },
            "required": [comp_type],
        }
        # 如后续子类型真的需要，可保留 definitions（当前生成通常用不到 $ref）
        if definitions:
            schema["definitions"] = definitions

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
            "x-xml-tag": "PORTS",
            "required": sorted(list(props.keys()))
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
            "x-xml-tag": "EVENTS",
            "required": sorted(list(props.keys()))
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
        接口 Schema（精简版）：
        - 顶层以接口类型名分组（AUTOSAR 标签）
        - 每类接口 -> array(items = 该类型的内联 Schema）
        - 仅依赖 KG：展开 (minOccurs>=1) 的元素；不做任何额外放行/手工骨架
        """
        from collections import defaultdict

        # 1) 按类型分组
        grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for itf in interface_plans or []:
            t = self._canon_iface_type(itf.get("type", ""))
            if not t:
                continue
            grouped[t].append(itf)

        properties: Dict[str, Any] = {}
        required: List[str] = []
        definitions: Dict[str, Any] = {}

        if not self.driver:
            # 没 KG 时，降级为最小可用形状（仅 SHORT-NAME），仍保持分组
            for itype, items in grouped.items():
                item_schema = {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "SHORT-NAME": {
                            "type": "string",
                            "examples": [it.get("name") for it in items if it.get("name")]
                        }
                    },
                    "required": ["SHORT-NAME"]
                }
                properties[itype] = {"type": "array", "items": item_schema, "minItems": 1}
                required.append(itype)
            return {
                "type": "object",
                "additionalProperties": False,
                "properties": properties,
                "required": required
            }

        # 2) 走 KG 递归：class_ident=类型名，parent_container_tag=类型名，design_index={}
        with self.driver.session() as session:
            for itype, items in grouped.items():
                try:
                    _nm, base_schema, defs = self._build_class_schema_recursive(
                        session=session,
                        class_ident=itype,
                        parent_container_tag=itype,
                        design_index={},  # 接口不依赖 Round1 设计白名单
                        seen=set()
                    )
                    # 转为 AUTOSAR 标签键（wrapper/tag 处理）
                    if hasattr(self, "_xmlize_schema_properties"):
                        base_schema = self._xmlize_schema_properties(base_schema)
                    definitions.update(defs)

                    # 给 SHORT-NAME 打 examples（不改变结构/必填，仅利于命名）
                    sn = base_schema.get("properties", {}).get("SHORT-NAME")
                    if isinstance(sn, dict):
                        examples = [it.get("name") for it in items if it.get("name")]
                        if examples:
                            sn["examples"] = examples

                    properties[itype] = {"type": "array", "items": base_schema, "minItems": 1}
                    required.append(itype)
                except Exception:
                    # 查询失败时保底为最小形状
                    item_schema = {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "SHORT-NAME": {
                                "type": "string",
                                "examples": [it.get("name") for it in items if it.get("name")]
                            }
                        },
                        "required": ["SHORT-NAME"]
                    }
                    properties[itype] = {"type": "array", "items": item_schema, "minItems": 1}
                    required.append(itype)

        return {
            "type": "object",
            "additionalProperties": False,
            "properties": properties,
            "required": required,
            "definitions": definitions or {}
        }

    def _canon_iface_type(self, t: str) -> str:
        """将多种写法统一成 AUTOSAR 标签写法"""
        U = (t or "").strip().upper().replace(" ", "").replace("_", "")
        mapping = {
            "CLIENTSERVERINTERFACE": "CLIENT-SERVER-INTERFACE",
            "CLIENT-SERVER-INTERFACE": "CLIENT-SERVER-INTERFACE",
            "SENDERRECEIVERINTERFACE": "SENDER-RECEIVER-INTERFACE",
            "SENDER-RECEIVER-INTERFACE": "SENDER-RECEIVER-INTERFACE",
            "NVDATAINTERFACE": "NV-DATA-INTERFACE",
            "NV-DATA-INTERFACE": "NV-DATA-INTERFACE",
            "MODESWITCHINTERFACE": "MODE-SWITCH-INTERFACE",
            "MODE-SWITCH-INTERFACE": "MODE-SWITCH-INTERFACE",
            "PARAMETERINTERFACE": "PARAMETER-INTERFACE",
            "PARAMETER-INTERFACE": "PARAMETER-INTERFACE",
            "TRIGGERINTERFACE": "TRIGGER-INTERFACE",
            "TRIGGER-INTERFACE": "TRIGGER-INTERFACE",
        }
        return mapping.get(U, (t or "").strip().upper())



query_engine = DynamicQueryEngine()