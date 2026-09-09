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

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set

from ..config import CONFIG
from .element_selection import interface_design_index, selection_design_index
from .xsd_content_index import (
    XsdContentIndexError,
    content_occurrence_index,
    load_text_content_type_index,
)

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    print("[WARN] neo4j driver未安装")

# 三选一（exactly one）类：类名 → 需要互斥选择的键集合
# 来源：XSD <xsd:group name="AUTOSAR-VARIABLE-REF"> 三个 minOccurs=0 的子元素在 AUTOSAR 语义里是变体
CHOICE_ONE_OF = {
    "AUTOSARVARIABLEREF": {
        "AUTOSAR-VARIABLE-IREF",
        "AUTOSAR-VARIABLE-IN-IMPL-DATATYPE",
        "LOCAL-VARIABLE-REF",
    },
    # 参数访问引用（出现于 PARAMETER-ACCESS 等场景）
    "AUTOSARPARAMETERREF": {
        "AUTOSAR-PARAMETER-IREF",
        "LOCAL-PARAMETER-REF",
    },
}

# InstanceRef 的“必选 + 三选一”规则（支持同义键：tag / wrapper）
# mandatory: 这些键必须出现（即便 KG 的 minOccurs 标成 0 也强制）
# xor_groups: 三选一，每个元素是同义键集合（取其中存在于 props 的那个）
XOR_WITH_MANDATORY = {
    # AUTOSAR-VARIABLE-IREF 的目标类型
    "VARIABLEINATOMICSWCTYPEINSTANCEREF": {
        "mandatory": {"TARGET-DATA-PROTOTYPE-REF"},
        "xor_groups": [
            {"PORT-PROTOTYPE-REF"},
            {"ROOT-VARIABLE-DATA-PROTOTYPE-REF"},
            {"CONTEXT-DATA-PROTOTYPE-REFS", "CONTEXT-DATA-PROTOTYPE-REF"},  # tag / wrapper 兼容
        ],
    },
    # AUTOSAR-VARIABLE-IN-IMPL-DATATYPE 的目标类型
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
        project_root = Path(__file__).resolve().parents[3]
        xsd_path = Path(str(CONFIG.validation.xsd_path))
        manifest_path = Path(str(CONFIG.validation.xsd_serialization_manifest_path))
        if not xsd_path.is_absolute():
            xsd_path = project_root / xsd_path
        if not manifest_path.is_absolute():
            manifest_path = project_root / manifest_path
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        expected_xsd_sha256 = str((manifest.get("xsd") or {}).get("sha256") or "")
        if len(expected_xsd_sha256) != 64:
            raise KGQueryError("serialization manifest has no pinned XSD hash")
        self.xsd_text_content_types = load_text_content_type_index(
            xsd_path,
            expected_sha256=expected_xsd_sha256,
        )

        # ✅ 新增：特定类型名称的直接映射表（优先级最高）
        self.DIRECT_TYPE_MAPPINGS = {
            "BOOLEAN": {
                "type": "string",
                "enum": ["true", "false"]  # ⬅️ 限制只能填 "true" 或 "false"
            },
            "INTEGER": {"type": "integer"},
            "DOUBLE": {"type": "number"},
            "TIME-VALUE": {"type": "number"},
            "TIMEVALUE": {"type": "number"},
            "FLOAT": {"type": "number"},
        }

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

        # Generic Phase 1 selections cover optional AUTOSAR paths outside the
        # legacy runnable-only preselect contract (ports, ComSpecs, events,
        # internal-behavior fields, and future XSD-backed component elements).
        # Each adjacent pair becomes a Neo4j expansion whitelist edge.
        generic_index = selection_design_index(element_design)
        for parent, children in generic_index.items():
            idx.setdefault(parent, set()).update(children)

        selected_tags = set(generic_index)
        for children in generic_index.values():
            selected_tags.update(children)
        port_types = {"P-PORT-PROTOTYPE", "R-PORT-PROTOTYPE", "PR-PORT-PROTOTYPE"}
        if "PORTS" in selected_tags or selected_tags.intersection(port_types):
            idx["__TOP__"].add("PORTS")
            selected_port_types = selected_tags.intersection(port_types)
            if selected_port_types:
                idx.setdefault("PORTS", set()).update(selected_port_types)

        internal_tags = {"SWC-INTERNAL-BEHAVIOR", "RUNNABLE-ENTITY", "EVENTS"}
        if selected_tags.intersection(internal_tags):
            idx["__TOP__"].add("INTERNAL-BEHAVIORS")
            idx.setdefault("INTERNAL-BEHAVIORS", set()).update(
                {"RUNNABLE-ENTITY", "EVENTS"}
            )

        # ----- PORTS -----
        ports = (element_design.get("ports") or {})
        if ports.get("needed"):
            idx["__TOP__"].add("PORTS")
            types = ports.get("types") or []
            if types:
                idx.setdefault("PORTS", set()).update(U(t) for t in types)

        # ----- INTERNAL-BEHAVIORS -----
        ib = (element_design.get("internal_behaviors")
              or element_design.get("swc_internal_behavior")
              or {})
        if ib.get("needed"):
            idx["__TOP__"].add("INTERNAL-BEHAVIORS")
            idx.setdefault("INTERNAL-BEHAVIORS", set()).update(
                {"RUNNABLE-ENTITY", "EVENTS"}
            )

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
                idx.setdefault("RUNNABLE-ENTITY", set()).update(run_elems)

            # events
            ev_types: set[str] = set()
            for ev in ib.get("events") or []:
                t = ev.get("type")
                if t: ev_types.add(U(t))
            if ev_types:
                idx.setdefault("EVENTS", set()).update(ev_types)

        return idx

    # ------------------------ KG 结构查询（唯一口径） ------------------------

    @staticmethod
    def _decode_xsd_content_model(raw: object) -> dict | None:
        """Decode the optional canonical JSON content model stored on Class."""
        if isinstance(raw, dict):
            return raw
        if not isinstance(raw, str) or not raw.strip():
            return None
        try:
            value = json.loads(raw)
        except (TypeError, ValueError, json.JSONDecodeError):
            return None
        return value if isinstance(value, dict) else None

    @staticmethod
    def _decode_xsd_context_models(raw: object) -> list[dict]:
        """Decode all parent-specific models retained for a legacy Class."""
        if isinstance(raw, list):
            return [item for item in raw if isinstance(item, dict)]
        if not isinstance(raw, str) or not raw.strip():
            return []
        try:
            value = json.loads(raw)
        except (TypeError, ValueError, json.JSONDecodeError):
            return []
        return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []

    @staticmethod
    def _select_xsd_context_model(
            effective: dict | None,
            contexts: list[dict],
            *,
            parent_class_ident: str = "",
            parent_container_tag: str = "",
    ) -> dict | None:
        if effective:
            return effective

        def norm(value: object) -> str:
            return "".join(ch for ch in str(value or "").upper() if ch.isalnum())

        hints = {norm(parent_class_ident), norm(parent_container_tag)} - {""}
        if not hints:
            return None
        ranked: list[tuple[int, dict]] = []
        for item in contexts:
            score = 0
            for raw_segment in item.get("container_path") or []:
                segment = str(raw_segment)
                if segment.startswith("element:"):
                    segment = segment.split(":", 1)[1].split("@", 1)[0]
                elif "}" in segment:
                    segment = segment.rsplit("}", 1)[-1]
                elif ":" in segment:
                    segment = segment.rsplit(":", 1)[-1]
                normalized = norm(segment)
                if normalized in hints:
                    score += 100
            if score:
                ranked.append((score, item))
        if not ranked:
            return None
        best_score = max(score for score, _ in ranked)
        best = [item for score, item in ranked if score == best_score]
        if len(best) != 1:
            hashes = {item.get("effective_model_sha256") for item in best}
            if len(hashes) != 1:
                signatures = set()
                for item in best:
                    model = item.get("effective_model")
                    try:
                        index = content_occurrence_index(model)
                    except XsdContentIndexError:
                        return None
                    signatures.add(
                        tuple(
                            (tag, occurrence.min_occurs, occurrence.max_occurs)
                            for tag, occurrence in index.items()
                        )
                    )
                if len(signatures) != 1:
                    return None
        model = best[0].get("effective_model")
        return model if isinstance(model, dict) else None

    @staticmethod
    def _xsd_content_order(model: dict | None) -> dict[str, int]:
        """Return the first XSD occurrence rank for element/wrapper tags."""
        order: dict[str, int] = {}

        def walk(node: object) -> None:
            if not isinstance(node, dict):
                return
            if node.get("kind") == "element":
                name = node.get("element_name") or node.get("name")
                if name:
                    order.setdefault(str(name).strip().upper(), len(order))
                return
            base_model = node.get("base_model")
            if isinstance(base_model, dict):
                walk(base_model)
            for child in node.get("children") or []:
                walk(child)

        walk(model)
        return order

    def _query_class_attributes(self, session, class_ident: str) -> dict:
        """
        返回：{ class_name, class_tag, attributes: [ {...}, ... ] }
        每个 attribute 字段包含：
          - a.*: name/xml_tag/xml_wrapper_tag/minOccurs/maxOccurs/isXmlAttr/isPrimitiveType/type(声明)
          - t.*: name/xml_tag/iri/labels/isAttribute/baseType/pattern 以及枚举字面量 t_enum_values
          - target_dest_*: 直接通过 (a)-[:TYPE_OF]->(t)-[:HAS_ATTRIBUTE]->(:Attribute{xml_tag:'DEST'})-[:TYPE_OF]->(:Enum)-[:HAS_LITERAL] 拿到的 DEST 枚举
            → 这是修复 KG 中 inline 类同名歧义的关键路径，不再做按名字的二次查询
          - target_is_dest_only: t 是否为 DEST-only 类（仅一个 DEST XML 属性、无任何元素子）
        """
        q = """
        MATCH (c:Class)
        WHERE c.name = $id OR c.xml_tag = $id
        WITH c LIMIT 1
        OPTIONAL MATCH (c)-[:SUBCLASS_OF*0..]->(p:Class)
        WITH c, collect(DISTINCT p) AS allc
        UNWIND allc AS cls
        OPTIONAL MATCH (cls)-[:HAS_ATTRIBUTE]->(a:Attribute)
        OPTIONAL MATCH (a)-[:TYPE_OF]->(t)
        OPTIONAL MATCH (t:Enum)-[:HAS_LITERAL]->(ev:EnumLiteral)

        // 兼容 KG: 当 t.isAttribute=true 时查找配套 Simple 类拿其约束（保留原逻辑）
        OPTIONAL MATCH (simple:Enum)
        WHERE t.isAttribute = true AND (
            simple.name = t.name + 'Simple' OR
            simple.xml_tag = t.xml_tag + '--SIMPLE'
        )
        OPTIONAL MATCH (simple)-[:HAS_LITERAL]->(simpleEv:EnumLiteral)

        WITH c, a, t,
             collect(DISTINCT ev.value) AS enum_vals,
             collect(DISTINCT simpleEv.value) AS simple_enum_vals,
             properties(a) AS amap,
             labels(t) AS tlabs,
             properties(t) AS tmap,
             properties(simple) AS simplemap

        // ✅ 直接通过 (t)-[:HAS_ATTRIBUTE]->(DEST 属性)-[:TYPE_OF]->(枚举类) 走边拿 DEST 枚举
        //   每个 (a, t) 都拿到自己 t 上挂的 DEST，避免 inline 同名歧义
        //   - 用 CALL (t) { ... } 显式作用域（Neo4j 5.6+ 推荐写法，避免 deprecation 警告）
        //   - 仅访问 KG 中实际存在的属性名 isXmlAttr / baseType
        CALL (t) {
            OPTIONAL MATCH (t)-[:HAS_ATTRIBUTE]->(destAttr:Attribute)
            WHERE coalesce(destAttr.xml_tag, destAttr.name) = 'DEST'
              AND coalesce(destAttr.isXmlAttr, false) = true
            OPTIONAL MATCH (destAttr)-[:TYPE_OF]->(destType)
            OPTIONAL MATCH (destType)-[:HAS_LITERAL]->(destLit:EnumLiteral)
            RETURN
                collect(DISTINCT destLit.value) AS dest_enum_vals,
                head(collect(DISTINCT destType.pattern)) AS dest_pattern,
                head(collect(DISTINCT destType.baseType)) AS dest_base,
                count(DISTINCT destAttr) AS dest_attr_count
        }

        // 统计 t 的非-XML-属性子元素数量，用于精确判断 DEST-only 类
        CALL (t) {
            OPTIONAL MATCH (t)-[:HAS_ATTRIBUTE]->(elemAttr:Attribute)
            WHERE coalesce(elemAttr.isXmlAttr, false) = false
              AND (elemAttr.xml_tag IS NOT NULL OR elemAttr.name IS NOT NULL)
            RETURN count(DISTINCT elemAttr) AS element_child_count
        }

        RETURN
          c.name AS class_name,
          c.xml_tag AS class_tag,
          c.xsd_effective_model_json AS xsd_effective_model_json,
          c.xsd_content_models_json AS xsd_content_models_json,
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
            type_xml_tag:    tmap['xml_tag'],
            type_iri:        tmap['id'],
            type_labels:     tlabs,
            t_is_attribute:  tmap['isAttribute'],
            t_base:          coalesce(tmap['baseType'], tmap['base']),
            t_pattern:       tmap['pattern'],
            t_is_enum:       CASE WHEN 'Enum' IN tlabs THEN true ELSE false END,
            t_enum_values:   enum_vals,

            // ✅ 直接挂在每个 attribute 上、按边走出来的 DEST 元数据
            target_dest_enum:    dest_enum_vals,
            target_dest_pattern: dest_pattern,
            target_dest_base:    dest_base,
            target_is_dest_only: (dest_attr_count = 1) AND (element_child_count = 0),

            // Simple 类约束（保留原行为；map 索引访问不会触发未知属性警告）
            simple_base:         coalesce(simplemap['base'], simplemap['baseType']),
            simple_pattern:      simplemap['pattern'],
            simple_enum_values:  simple_enum_vals,
            simple_is_primitive: simplemap['isPrimitiveType']
          }) AS attrs
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
            de = a.get("target_dest_enum")
            if isinstance(de, str): a["target_dest_enum"] = [de]
            attrs.append(a)
        return {
            "class_name": data.get("class_name"),
            "class_tag": data.get("class_tag"),
            "attributes": attrs,
            "xsd_content_model": self._decode_xsd_content_model(data.get("xsd_effective_model_json")),
            "xsd_context_models": self._decode_xsd_context_models(data.get("xsd_content_models_json")),
        }

    def _query_class_attributes_by_iri(self, session, iri: str) -> dict:
        """
        与 _query_class_attributes 等价，但通过 Class.id（IRI）精确匹配，避免 inline 同名歧义。
        当 _query_class_attributes 已带回 type_iri 时优先使用本方法。
        """
        q = """
        MATCH (c:Class) WHERE c.id = $iri
        WITH c LIMIT 1
        OPTIONAL MATCH (c)-[:SUBCLASS_OF*0..]->(p:Class)
        WITH c, collect(DISTINCT p) AS allc
        UNWIND allc AS cls
        OPTIONAL MATCH (cls)-[:HAS_ATTRIBUTE]->(a:Attribute)
        OPTIONAL MATCH (a)-[:TYPE_OF]->(t)
        OPTIONAL MATCH (t:Enum)-[:HAS_LITERAL]->(ev:EnumLiteral)
        WITH c, a, t,
             collect(DISTINCT ev.value) AS enum_vals,
             properties(a) AS amap,
             labels(t) AS tlabs,
             properties(t) AS tmap

        CALL (t) {
            OPTIONAL MATCH (t)-[:HAS_ATTRIBUTE]->(destAttr:Attribute)
            WHERE coalesce(destAttr.xml_tag, destAttr.name) = 'DEST'
              AND coalesce(destAttr.isXmlAttr, false) = true
            OPTIONAL MATCH (destAttr)-[:TYPE_OF]->(destType)
            OPTIONAL MATCH (destType)-[:HAS_LITERAL]->(destLit:EnumLiteral)
            RETURN
                collect(DISTINCT destLit.value) AS dest_enum_vals,
                head(collect(DISTINCT destType.pattern)) AS dest_pattern,
                head(collect(DISTINCT destType.baseType)) AS dest_base,
                count(DISTINCT destAttr) AS dest_attr_count
        }
        CALL (t) {
            OPTIONAL MATCH (t)-[:HAS_ATTRIBUTE]->(elemAttr:Attribute)
            WHERE coalesce(elemAttr.isXmlAttr, false) = false
              AND (elemAttr.xml_tag IS NOT NULL OR elemAttr.name IS NOT NULL)
            RETURN count(DISTINCT elemAttr) AS element_child_count
        }

        RETURN
          c.name AS class_name,
          c.xml_tag AS class_tag,
          c.xsd_effective_model_json AS xsd_effective_model_json,
          c.xsd_content_models_json AS xsd_content_models_json,
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
            type_xml_tag:    tmap['xml_tag'],
            type_iri:        tmap['id'],
            type_labels:     tlabs,
            t_is_attribute:  tmap['isAttribute'],
            t_base:          coalesce(tmap['baseType'], tmap['base']),
            t_pattern:       tmap['pattern'],
            t_is_enum:       CASE WHEN 'Enum' IN tlabs THEN true ELSE false END,
            t_enum_values:   enum_vals,
            target_dest_enum:    dest_enum_vals,
            target_dest_pattern: dest_pattern,
            target_dest_base:    dest_base,
            target_is_dest_only: (dest_attr_count = 1) AND (element_child_count = 0)
          }) AS attrs
        """
        rec = session.run(q, iri=iri).single()
        if not rec:
            raise KGQueryError(f"KG 中找不到 IRI 对应的 Class: {iri}")
        data = rec.data()
        attrs = []
        for a in data.get("attrs") or []:
            if not any(a.get(k) for k in
                       ("name", "xml_tag", "xml_wrapper_tag", "type_name", "a_is_primitive", "a_declared_type")):
                continue
            evs = a.get("t_enum_values")
            if isinstance(evs, str): a["t_enum_values"] = [evs]
            de = a.get("target_dest_enum")
            if isinstance(de, str): a["target_dest_enum"] = [de]
            attrs.append(a)
        return {
            "class_name": data.get("class_name"),
            "class_tag": data.get("class_tag"),
            "attributes": attrs,
            "xsd_content_model": self._decode_xsd_content_model(data.get("xsd_effective_model_json")),
            "xsd_context_models": self._decode_xsd_context_models(data.get("xsd_content_models_json")),
        }

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
    def _is_ref_terminal(
        self,
        session,
        type_name: str | None,
        a_xml_tag: str | None,
        type_iri: str | None = None,
        target_is_dest_only: Optional[bool] = None,
    ) -> bool:
        """
        True: 终止为 {@DEST,#text}; False: 继续递归。
        优先级：
          1. 如果调用方已经从 KG 边走出 target_is_dest_only 的判断，直接采用（最可靠）
          2. 否则若有 type_iri，按 IRI 精确查 (避免 inline 同名歧义)
          3. 再否则按 type_name 退而求其次（可能受 inline 同名歧义影响）
          4. 最后 fallback：仅当 xml_tag 以 "-TREF" 结尾才视为终止
        """
        # 1) 直接采用从原查询带回的精确判断
        if target_is_dest_only is True:
            return True
        if target_is_dest_only is False and (type_iri or type_name):
            # KG 已说明不是 DEST-only，但仍要兜底 -TREF 命名规则
            tag = (a_xml_tag or "").strip().upper()
            return tag.endswith("-TREF")

        # 2) 按 IRI 精确查
        if type_iri:
            try:
                return self._is_dest_only_class_by_iri(session, type_iri)
            except Exception:
                pass

        # 3) 按名字查（容易在 inline 同名时拿错节点）
        tn = (type_name or "").strip()
        if tn:
            try:
                return self._is_dest_only_class(session, tn)
            except Exception:
                pass

        # 4) 兜底：按命名约定
        tag = (a_xml_tag or "").strip().upper()
        return tag.endswith("-TREF")

    def _is_dest_only_class_by_iri(self, session, iri: str) -> bool:
        """按 IRI 精确判断目标类是否为 DEST-only。"""
        q = """
        MATCH (c:Class) WHERE c.id = $iri
        WITH c LIMIT 1
        CALL (c) {
            OPTIONAL MATCH (c)-[:HAS_ATTRIBUTE]->(da:Attribute)
            WHERE coalesce(da.xml_tag, da.name) = 'DEST'
              AND coalesce(da.isXmlAttr, false) = true
            RETURN count(DISTINCT da) AS dest_count
        }
        CALL (c) {
            OPTIONAL MATCH (c)-[:HAS_ATTRIBUTE]->(ea:Attribute)
            WHERE coalesce(ea.isXmlAttr, false) = false
              AND (ea.xml_tag IS NOT NULL OR ea.name IS NOT NULL)
            RETURN count(DISTINCT ea) AS elem_count
        }
        RETURN dest_count = 1 AND elem_count = 0 AS is_dest_only
        """
        rec = session.run(q, iri=iri).single()
        return bool(rec and rec["is_dest_only"])

    def _apply_occurrence_to_array(
        self,
        val: Dict[str, Any],
        min_occ: int,
        max_occ_raw,
    ) -> Dict[str, Any]:
        """
        将 KG 的 minOccurs / maxOccurs 统一映射成 JSON Schema 的 minItems / maxItems。

        约定：
          - val 必须是 type=array 的节点（已生成 items）
          - minOccurs >= 1 → minItems = minOccurs（不覆盖已有更严格的值）
          - maxOccurs > 1（有限正整数）→ maxItems = maxOccurs
          - maxOccurs = -1 / "unbounded" / "inf" → 不设 maxItems（无界）
          - maxOccurs = 0 / 1 → 通常不会落在 array 分支（由 _is_array_occurs 决定），不处理
        """
        if not isinstance(val, dict) or val.get("type") != "array":
            return val

        # minItems
        try:
            mo = int(min_occ) if min_occ is not None else 0
        except (ValueError, TypeError):
            mo = 0
        if mo > 0:
            val.setdefault("minItems", mo)

        # maxItems
        if max_occ_raw is None:
            return val
        s = str(max_occ_raw).strip().lower()
        if s in {"unbounded", "inf", "infinite"}:
            return val
        try:
            mx = int(max_occ_raw)
            if mx > 0:  # 排除 0/-1
                val["maxItems"] = mx
        except (ValueError, TypeError):
            pass
        return val

    def _apply_terminal_string_constraints(
        self,
        scalar: Dict[str, Any],
        enum_vals: Optional[List[Any]],
        pattern_str: Optional[str],
    ) -> Dict[str, Any]:
        """
        将 KG 的枚举字面量 / pattern 统一应用到标量 schema 节点上。
          - enum：直接覆盖
          - pattern：清理 XSD 命名空间后写入
        """
        if enum_vals:
            cleaned = [e for e in enum_vals if e is not None and e != ""]
            if cleaned:
                scalar = {**scalar, "enum": cleaned}
        if pattern_str:
            clean_pat = self._clean_xsd_pattern(pattern_str)
            if clean_pat:
                scalar = {**scalar, "pattern": clean_pat}
        return scalar

    @staticmethod
    def _scalar_from_base_type(base: Optional[str], boolean_as_string: bool = True) -> Dict[str, Any]:
        """
        把 XSD/KG 的 baseType 字符串映射为 JSON Schema 标量节点。
          - BOOLEAN 默认按 AUTOSAR XML 序列化形式输出 string + enum=["true","false"]
            （AUTOSAR 把布尔写在 XML 里就是字面量字符串）；boolean_as_string=False 才返回 type=boolean
          - INT / INTEGER / 各种 INTn → integer
          - FLOAT / DOUBLE / DECIMAL / NUMBER → number
          - 其余落到 string
        """
        b = (base or "").strip().upper()
        if b == "BOOLEAN":
            if boolean_as_string:
                return {"type": "string", "enum": ["true", "false"]}
            return {"type": "boolean"}
        if b in {"INT", "INTEGER", "INT8", "INT16", "INT32", "INT64",
                 "UINT", "UINT8", "UINT16", "UINT32", "UINT64",
                 "SINT", "SINT8", "SINT16", "SINT32", "SINT64",
                 "LONG", "SHORT"}:
            return {"type": "integer"}
        if b in {"FLOAT", "DOUBLE", "DECIMAL", "NUMBER"}:
            return {"type": "number"}
        return {"type": "string"}

    def _resolve_scalar_attribute_schema(
        self,
        session,
        parent_class_ident: str,
        attr_xml_tag: str,
        description: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        在 KG 中精确查 parent_class_ident 类下 xml_tag=attr_xml_tag 的属性，按其
        类型链（含 Simple 旁路）解析为 JSON Schema 标量节点；找不到返回 None。

        用于 generate_component_schema_fixed 这类“手写骨架”里的标量字段，避免硬编码枚举。
        分支顺序与 _build_class_schema_recursive 内的终止逻辑对齐：
          1) 直接映射表 (DIRECT_TYPE_MAPPINGS)
          2) t.isAttribute=true → 走 Simple 类的 base/enum/pattern
          3) t 是 Enum 或有 base → 取 base，叠加 enum / pattern
          4) 兜底：依据 xml_tag 名做朴素猜测
        """
        if not parent_class_ident or not attr_xml_tag:
            return None

        target_tag = attr_xml_tag.strip().upper()
        try:
            info = self._query_class_attributes(session, parent_class_ident)
        except Exception as e:
            if CONFIG.debug_mode:
                print(f"[DEBUG] _resolve_scalar_attribute_schema: 查询父类 {parent_class_ident} 失败: {e}")
            return None

        attr = None
        for a in info.get("attributes", []) or []:
            for nm in (a.get("xml_tag"), a.get("xml_wrapper_tag"), a.get("name")):
                if nm and nm.strip().upper() == target_tag:
                    attr = a
                    break
            if attr is not None:
                break

        if attr is None:
            if CONFIG.debug_mode:
                print(f"[DEBUG] _resolve_scalar_attribute_schema: KG 中未找到 {parent_class_ident}.{attr_xml_tag}")
            return None

        tname = attr.get("type_name") or attr.get("a_declared_type")
        scalar: Optional[Dict[str, Any]] = None

        # 1) 直接映射表（与递归路径完全一致）
        if tname:
            tup = tname.strip().upper()
            if tup in self.DIRECT_TYPE_MAPPINGS:
                scalar = dict(self.DIRECT_TYPE_MAPPINGS[tup])
                # 同样允许 Simple 类覆盖 enum/pattern
                simple_enum_vals = attr.get("simple_enum_values") or []
                simple_pattern = attr.get("simple_pattern")
                if simple_enum_vals:
                    scalar["enum"] = simple_enum_vals
                if simple_pattern:
                    cp = self._clean_xsd_pattern(simple_pattern)
                    if cp:
                        scalar["pattern"] = cp

        # 2/3) Simple 旁路 / 普通枚举 / 有 base
        if scalar is None:
            t_is_attr = bool(attr.get("t_is_attribute"))
            t_is_enum = bool(attr.get("t_is_enum")) or bool(attr.get("t_enum_values"))
            t_base = attr.get("t_base")
            t_pattern = attr.get("t_pattern")
            simple_base = attr.get("simple_base")
            simple_pattern = attr.get("simple_pattern")
            simple_enum_vals = attr.get("simple_enum_values") or []
            t_enum_vals = attr.get("t_enum_values") or []

            if t_is_attr or t_is_enum or t_base or simple_base:
                base = simple_base or t_base or ("string" if (t_is_attr or t_is_enum) else None)
                scalar = self._scalar_from_base_type(base, boolean_as_string=True)
                # 优先 Simple 类的枚举/pattern
                enum_vals = simple_enum_vals or t_enum_vals
                scalar = self._apply_terminal_string_constraints(
                    scalar, enum_vals, simple_pattern or t_pattern
                )

        # 4) 兜底：按 xml_tag/类型名猜原子类型
        if scalar is None:
            scalar = self._guess_primitive_from_name(target_tag) \
                     or self._guess_primitive_from_name((tname or "").upper()) \
                     or {"type": "string"}

        if description and "description" not in scalar:
            scalar["description"] = description

        return scalar

    # --- 1) 新增：判断“是否 DEST-only 类”的工具函数 ---
    def _is_dest_only_class(self, session, class_ident: str) -> bool:
        """
        True: 该类只有一个 XML 属性且为 DEST，且无任何子元素（element）。
        这种类应终止为 {@DEST,#text}，不要继续递归。

        ⚠️ 注意：此方法按 name/xml_tag 匹配，对 inline 同名类会有歧义；
        新代码请优先使用 _is_dest_only_class_by_iri。
        """
        info = self._query_class_attributes(session, class_ident) or {}
        attrs = info.get("attributes") or []

        def _is_xml_attr(a: dict) -> bool:
            return bool(a.get("isXmlAttr")) or bool(a.get("is_xml_attribute"))

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
            parent_class_ident: str = "",
            force_children_array: bool = False  # 新增参数
    ) -> tuple[str, dict, dict]:
        """
        从 KG 递归构建 class_ident 的 JSON Schema 片段（内联版）：
          - 仅保留：KG 必选(minOccurs>=1) ∪ Round1 白名单（容器→子键；of→variant；variant→include）
          - CHOICE_ONE_OF：仅在“该容器没有任何【相关】Round1 白名单”时作为兜底放行
          - XOR_WITH_MANDATORY：只做约束（强制必选 + 三选一），不主动放行新键
          - 引用终止（*-TREF/IREF）→ {@DEST, #text}；原子/枚举直接落标量；其余继续递归（内联）
        """

        # 在函数开始处添加：判断是否需要约束 maxItems
        def should_constrain_max_items(parent_tag: str, is_terminal: bool) -> bool:
            """
            判断是否需要约束数组最大元素数
            - RUNNABLE-ENTITY 的子元素：需要
            - 终止类型（枚举、isAttribute=true）：不需要
            - 接口类型：不需要
            """
            parent_upper = (parent_tag or "").strip().upper()

            # RUNNABLE-ENTITY 的直接子元素需要约束
            if parent_upper == "RUNNABLE-ENTITY":
                return True

            # DATA-SEND-POINTS 等容器的子元素也需要约束
            if parent_upper in {
                "DATA-SEND-POINTS",
                "DATA-RECEIVE-POINT-BY-ARGUMENTS",
                "DATA-RECEIVE-POINT-BY-VALUES",
                "SERVER-CALL-POINTS",
                "READ-LOCAL-VARIABLES",
                "WRITTEN-LOCAL-VARIABLES",
                "MODE-ACCESS-POINTS",
                "PARAMETER-ACCESSS"
            }:
                return True

            if is_terminal:  # 终止类型不约束
                return False

            # 接口类型不约束
            if parent_upper in {
                "CLIENT-SERVER-INTERFACE",
                "SENDER-RECEIVER-INTERFACE",
                "NV-DATA-INTERFACE",
                "MODE-SWITCH-INTERFACE",
                "PARAMETER-INTERFACE",
                "TRIGGER-INTERFACE"
            }:
                return False

            return False


        info = self._query_class_attributes(session, class_ident)
        content_models = info.get("xsd_context_models") or []
        content_model = self._select_xsd_context_model(
            info.get("xsd_content_model"),
            content_models,
            parent_class_ident=parent_class_ident,
            parent_container_tag=parent_container_tag,
        )
        class_name = info.get("class_name") or class_ident
        if class_name in seen:
            return class_name, {"type": "object", "properties": {}, "additionalProperties": False}, {}
        seen.add(class_name)

        def _U(s: str | None) -> str:
            return (s or "").strip().upper()

        attrs = [dict(item) for item in (info.get("attributes") or [])]
        if content_model:
            try:
                xsd_occurrences = content_occurrence_index(content_model)
            except XsdContentIndexError as error:
                raise KGQueryError(
                    f"XSD content model for {class_name} is unsupported: {error}"
                ) from error
            for attribute in attrs:
                attribute["_atlas_kg_max_occurs"] = attribute.get("maxOccurs")
                occurrence = None
                for candidate in (
                    attribute.get("xml_wrapper_tag"),
                    attribute.get("xml_tag"),
                    attribute.get("name"),
                ):
                    occurrence = xsd_occurrences.get(_U(candidate))
                    if occurrence is not None:
                        break
                if occurrence is not None:
                    attribute["minOccurs"] = occurrence.min_occurs
                    attribute["maxOccurs"] = (
                        -1 if occurrence.max_occurs is None else occurrence.max_occurs
                    )

        # ---- 规则/表 ----
        choice_map = globals().get("CHOICE_ONE_OF", {})
        xor_map = globals().get("XOR_WITH_MANDATORY", {})
        always_map = globals().get("ALWAYS_INCLUDE_OPTIONALS", {})

        # ---- Round1 白名单：来自父容器（例如 ACCESSED-VARIABLE / RUNNABLE-ENTITY / AUTOSAR-VARIABLE-IREF 等）----
        allowed_from_design: set[str] = set()
        if parent_container_tag:
            allowed_from_design |= {_U(x) for x in (design_index.get(_U(parent_container_tag)) or set())}

        # ★ 额外：全局设计键集合（用于允许“锚点”属性如 ACCESSED-VARIABLE 先被保留）
        class_up = _U(class_ident)
        for class_key in {class_up, _U(class_name), _U(info.get("class_tag"))} - {""}:
            allowed_from_design |= {
                _U(item) for item in (design_index.get(class_key) or set())
            }

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
            # 4) 额外放行（事件引用、InstanceRef 的 mandatory 键等）
            if (w in extra_opt) or (t in extra_opt) or (n in extra_opt):
                return True

            return False

        # 基于上述规则过滤属性
        attrs = [a for a in attrs if _keep(a)]

        # --- 最终版排序逻辑 (含MINIMUM-START-INTERVAL特殊处理) ---
        def get_final_sort_key(attr_dict: dict) -> str:
            """
            根据 wrapper > tag > name 的优先级，获取用于排序的最终键名。
            """
            # 优先使用 wrapper_tag
            key = attr_dict.get("xml_wrapper_tag")
            if key:
                return str(key)
            # 其次使用 xml_tag
            key = attr_dict.get("xml_tag")
            if key:
                return str(key)
            # 最后使用 name
            return str(attr_dict.get("name") or "")

        content_order = self._xsd_content_order(content_model)
        attrs.sort(key=lambda a: (
            content_order.get(_U(get_final_sort_key(a)), len(content_order) + 1000),
            # 第一部分(优先级)：三级优先级系统
            0 if _U(get_final_sort_key(a)) == "SHORT-NAME" else
            1 if _U(get_final_sort_key(a)) == "START-ON-EVENT-REF" else
            2 if _U(get_final_sort_key(a)) == "IS-SERVICE" else
            3 if _U(get_final_sort_key(a)) == "MINIMUM-START-INTERVAL" else
            4 if _U(get_final_sort_key(a)) == "OPERATION-IREF" else
            5 if _U(get_final_sort_key(a)) == "TIMEOUT" else
            6 if _U(get_final_sort_key(a)) == "CONTEXT-PORT-REF" else
            7,
            # 第二部分(字母顺序)：仍然使用最终的键名进行排序
            _U(get_final_sort_key(a))
        ))

        props: dict[str, dict] = {}
        required: list[str] = []
        definitions: dict[str, dict] = {}
        wrapper_shapes: dict[str, tuple[str, str, object]] = {}

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
            if wrap and tag and _U(wrap) != _U(tag):
                wrapper_shapes[key] = (
                    str(wrap), str(tag), a.get("_atlas_kg_max_occurs")
                )
            min_occ = int(a.get("minOccurs") or a.get("pure_minOccurs") or 0)
            max_occ_raw = a.get("maxOccurs")
            default_is_array = _is_array_occurs(max_occ_raw)
            is_array = _override_container_shape(_U(key), default_is_array)

            tname = a.get("type_name") or a.get("type")

            max_occ_raw = a.get("maxOccurs")
            default_is_array = _is_array_occurs(max_occ_raw)
            # ========== 应用父层强制标记 ==========
            if force_children_array:
                # 父层是联合容器壳，当前元素强制为array
                is_array = True
                if CONFIG.debug_mode:
                    print(f"[DEBUG] {key} 因父层联合容器壳，强制为array")
            else:
                # 正常白名单覆盖逻辑
                is_array = _override_container_shape(_U(key), default_is_array)

            # ============================================================
            # ✅ 新增：优先检查直接映射表（在所有其他判断之前）
            # ============================================================
            if tname:
                tname_upper = _U(tname)
                if tname_upper in self.DIRECT_TYPE_MAPPINGS:
                    scalar = self.DIRECT_TYPE_MAPPINGS[tname_upper].copy()

                    # ✅ 新增：叠加Simple类的约束
                    simple_pattern = a.get("simple_pattern")
                    simple_enum_vals = a.get("simple_enum_values") or []

                    if simple_enum_vals:
                        # Simple类的enum覆盖默认值
                        scalar["enum"] = simple_enum_vals

                    if simple_pattern:
                        clean_pattern = self._clean_xsd_pattern(simple_pattern)
                        if clean_pattern:
                            scalar["pattern"] = clean_pattern

                    val = {"type": "array", "items": scalar} if is_array else scalar
                    if is_array:
                        self._apply_occurrence_to_array(val, min_occ, max_occ_raw)

                    props[key] = val
                    if min_occ >= 1:
                        required.append(key)
                    if tag:
                        props[key]["x-xml-tag"] = tag
                    if wrap and wrap not in COLLAPSED_WRAPPERS:
                        props[key]["x-xml-wrapper-tag"] = wrap

                    if CONFIG.debug_mode:
                        print(f"[DEBUG] 直接映射类型: {tname} → {scalar}")

                    continue  # ⚠️ 跳过后续所有判断

            # 引用终止（TREF/IREF 或 DEST-only 类）
            # ✅ 关键修复：DEST 枚举直接从原查询的 target_dest_enum 字段读取
            #   该字段是通过 (a)-[:TYPE_OF]->(t)-[:HAS_ATTRIBUTE]->(:DEST)-[:TYPE_OF]->(:Enum)-[:HAS_LITERAL]
            #   走边拿出来的，不会因为 inline 类同名而错配；同时把 target_is_dest_only 传给判定函数
            type_iri = a.get("type_iri")
            target_is_dest_only = a.get("target_is_dest_only")
            if self._is_ref_terminal(
                session, tname, tag,
                type_iri=type_iri,
                target_is_dest_only=target_is_dest_only,
            ):
                # 直接从 attribute 上挂的字段拿 DEST 枚举（一次性、无歧义）
                target_dest_enum = a.get("target_dest_enum") or []
                target_dest_pattern = a.get("target_dest_pattern")

                dest_enum = None
                if isinstance(target_dest_enum, list) and len(target_dest_enum) > 0:
                    dest_enum = sorted([e for e in target_dest_enum if e])
                else:
                    # 极端兜底：当 KG 中 t 没挂 DEST 子边时，按 IRI / 名字再查一次
                    try:
                        if type_iri:
                            ref_class_info = self._query_class_attributes_by_iri(session, type_iri)
                        else:
                            ref_class_info = self._query_class_attributes(session, tname or tag)
                        for ref_attr in ref_class_info.get("attributes", []):
                            attr_tag = (ref_attr.get("xml_tag") or ref_attr.get("name") or "").strip().upper()
                            is_xml_attr = bool(ref_attr.get("isXmlAttr")) or bool(ref_attr.get("is_xml_attribute"))
                            if is_xml_attr and attr_tag == "DEST":
                                enum_values = ref_attr.get("t_enum_values") or []
                                if enum_values:
                                    dest_enum = sorted([e for e in enum_values if e])
                                break
                    except Exception as e:
                        if CONFIG.debug_mode:
                            print(f"[DEBUG] DEST 兜底查询失败 ({tname or tag}): {e}")

                if dest_enum is None and CONFIG.debug_mode:
                    print(f"[DEBUG] 未能为引用 {tname or tag} 的 DEST 属性解析出枚举值。")

                val = _emit_ref_object_schema(is_array, dest_enum)
                # ✅ 若 KG 给了 DEST 类型的 pattern，叠加到 @DEST 上（更严格）
                if target_dest_pattern:
                    clean_pat = self._clean_xsd_pattern(target_dest_pattern)
                    if clean_pat:
                        if is_array:
                            val["items"]["properties"]["@DEST"]["pattern"] = clean_pat
                        else:
                            val["properties"]["@DEST"]["pattern"] = clean_pat

                # ✅ 统一应用 minOccurs / maxOccurs → minItems / maxItems
                if is_array:
                    self._apply_occurrence_to_array(val, min_occ, max_occ_raw)

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

                # ✅ 新增：获取 Simple 类的约束
                simple_base = a.get("simple_base")
                simple_pattern = a.get("simple_pattern")
                simple_enum_vals = a.get("simple_enum_values") or []

                # 1) 强制终止：isAttribute=true的类型
                if t_is_attr:
                    # 兜底：如果Simple类和原类都没提供base，默认为string
                    base_to_use = simple_base or t_base or "string"
                    scalar = _scalar_from_base(base_to_use)

                    # 应用Simple类的枚举约束
                    if simple_enum_vals:
                        scalar = {**scalar, "enum": simple_enum_vals}
                    elif t_is_enum:
                        enum_vals = a.get("t_enum_values") or []
                        if enum_vals:
                            scalar = {**scalar, "enum": enum_vals}

                    # 应用Simple类的pattern约束
                    pattern_to_use = simple_pattern or t_pattern
                    if pattern_to_use:
                        clean_pattern = self._clean_xsd_pattern(pattern_to_use)
                        if clean_pattern:
                            scalar = {**scalar, "pattern": clean_pattern}

                    val = {"type": "array", "items": scalar} if is_array else scalar
                    if is_array:
                        self._apply_occurrence_to_array(val, min_occ, max_occ_raw)

                    props[key] = val
                    if min_occ >= 1:
                        required.append(key)
                    if tag:
                        props[key]["x-xml-tag"] = tag
                    if wrap and wrap not in COLLAPSED_WRAPPERS:
                        props[key]["x-xml-wrapper-tag"] = wrap

                    continue  # 终止，不再递归

                # 2) 其他终止条件：枚举或有base
                elif t_is_enum or t_base:
                    # ✅ 优先使用 Simple 类的 base（更精确）
                    base_to_use = simple_base or t_base
                    scalar = _scalar_from_base(base_to_use)

                    # ✅ 枚举约束：优先 Simple 类的 enumerations
                    if simple_enum_vals:
                        scalar = {**scalar, "enum": simple_enum_vals}
                    elif t_is_enum:
                        enum_vals = a.get("t_enum_values") or []
                        if enum_vals:
                            scalar = {**scalar, "enum": enum_vals}

                    # ✅ Pattern 约束：优先 Simple 类的 pattern
                    pattern_to_use = simple_pattern or t_pattern
                    if pattern_to_use:
                        # 清理 XSD 命名空间前缀
                        clean_pattern = self._clean_xsd_pattern(pattern_to_use)
                        if clean_pattern:
                            scalar = {**scalar, "pattern": clean_pattern}

                    val = {"type": "array", "items": scalar} if is_array else scalar

                    if is_array:
                        self._apply_occurrence_to_array(val, min_occ, max_occ_raw)

                    props[key] = val
                    if min_occ >= 1:
                        required.append(key)
                    if tag:
                        props[key]["x-xml-tag"] = tag
                    if wrap and wrap not in COLLAPSED_WRAPPERS:
                        props[key]["x-xml-wrapper-tag"] = wrap

                    continue


                # ========== 新增：模式2判断 ==========
                # 2) 递归前预判断：是否为"联合容器壳"
                is_union_container = False
                if default_is_array and not wrap:  # 满足基本条件：maxOccurs=-1 且无wrapper
                    is_union_container = self._is_union_container_shell(session, tname)
                # 如果是联合容器壳，覆盖容器形态判断
                if is_union_container:
                    is_array = False  # 当前节点强制为object
                    if CONFIG.debug_mode:
                        print(f"[DEBUG] {key} 作为联合容器壳，强制为object，子元素将为array")
                # ====================================
                # 3) 递归（传递force_children_array标记）
                next_key = _U(a.get("xml_wrapper_tag") or a.get("xml_tag"))
                child_parent = next_key if design_index.get(next_key) else _U(parent_container_tag)
                sub_name, sub_schema, sub_defs = self._build_class_schema_recursive(
                    session=session,
                    class_ident=tname,
                    parent_container_tag=child_parent,
                    design_index=design_index,
                    seen=set(seen),
                    parent_class_ident=class_name,
                    force_children_array=is_union_container  # 传递标记
                )
                definitions.update(sub_defs)

                val = {"type": "array", "items": sub_schema} if is_array else sub_schema

                if is_array:
                    self._apply_occurrence_to_array(val, min_occ, max_occ_raw)
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
            if is_array:
                val = {"type": "array", "items": val}
                self._apply_occurrence_to_array(val, min_occ, max_occ_raw)

            if _U(key) == "SHORT-NAME":
                val = self._apply_short_name_constraint(val)

            props[key] = val
            if min_occ >= 1:
                required.append(key)
            if tag:
                props[key]["x-xml-tag"] = tag
            if wrap and wrap not in COLLAPSED_WRAPPERS:
                props[key]["x-xml-wrapper-tag"] = wrap

        # ---- 组装当前类的 schema ----
        # Restore canonical XML wrapper/item nesting.  The KG attribute view
        # flattens e.g. DATA-SEND-POINTS/VARIABLE-ACCESS into one property, but
        # both XSD particles must remain explicit in the provider schema.
        for key, (wrapper, item_tag, kg_max_occurs) in wrapper_shapes.items():
            value = props.get(key)
            if not isinstance(value, dict):
                continue
            if value.get("type") == "array":
                raise KGQueryError(
                    f"XSD wrapper {wrapper} has unsupported repeated outer containers"
                )
            item_schema = value
            item_schema.pop("x-xml-wrapper-tag", None)
            item_schema["x-xml-tag"] = item_tag
            selected_items = {
                _U(item) for item in (design_index.get(_U(wrapper)) or set())
            }
            if _is_array_occurs(kg_max_occurs) or _U(item_tag) in selected_items:
                item_value: dict[str, Any] = {"type": "array", "items": item_schema}
            else:
                item_value = item_schema
            props[key] = {
                "type": "object",
                "properties": {item_tag: item_value},
                "required": [item_tag],
                "additionalProperties": False,
                "x-xml-tag": wrapper,
            }

        text_design_keys = {
            _U(class_ident),
            _U(class_name),
            _U(info.get("class_tag")),
            _U(parent_container_tag),
        } - {""}
        text_selected = any(
            "#TEXT" in {_U(item) for item in (design_index.get(key) or set())}
            for key in text_design_keys
        )
        if _U(info.get("class_tag")) in self.xsd_text_content_types and text_selected:
            props["#text"] = {"type": "string"}
            if "#text" not in required:
                required.append("#text")

        schema: dict = {"type": "object", "properties": props, "additionalProperties": False}
        if content_model:
            schema["x-atlas-content-model"] = content_model
        elif content_models:
            schema["x-atlas-content-models"] = content_models
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
            # ``includes`` is a set.  Its process-salted iteration order used to
            # leak into the JSON Schema ``required`` array and therefore into
            # the hash-pinned typed-repair context, even though the rendered
            # ARXML was identical.  Keep this semantic set canonical on disk.
            for inc_tag in sorted(includes):
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
        root_short_name_schema = self._apply_short_name_constraint({
            "type": "string",
            "const": name,
            "examples": [name]
        })
        root_props: Dict[str, Any] = {
            "SHORT-NAME": root_short_name_schema
        }
        root_required: List[str] = ["SHORT-NAME"]

        if "PORTS" in design_index.get("__TOP__", set()) and ports_obj is not None:
            root_props["PORTS"] = ports_obj
            # 你是否强制 PORTS 必填取决于策略，这里保持“不强制”，如需严格可解开下一行
            # root_required.append("PORTS")

        # === 扁平化：SWC-INTERNAL-BEHAVIOR 直接挂 RUNNABLE-ENTITY 数组（不再套 RUNNABLES 壳） ===
        # 扁平 INTERNAL-BEHAVIORS 与 RUNNABLES：只保留 SWC-INTERNAL-BEHAVIOR 与其下的 RUNNABLE-ENTITY
        if "INTERNAL-BEHAVIORS" in design_index.get("__TOP__", set()):
            sib_short_name_schema = self._apply_short_name_constraint({
                "type": "string"
            })

            # ✅ 修复：从 KG 解析两个必选标量的真实类型，而不是硬编码 ["true","false"]
            #   - SUPPORTS-MULTIPLE-INSTANTIATION 在 XSD 里是 xsd:boolean，KG 解出会是 string + ["true","false"]
            #   - HANDLE-TERMINATION-AND-RESTART  在 XSD 里是 HANDLE-TERMINATION-AND-RESTART-ENUM
            #     正确值是 ["CAN-BE-TERMINATED", "CAN-BE-TERMINATED-AND-RESTARTED", "NO-SUPPORT"]
            with self.driver.session() as _ssn:
                supports_multi = self._resolve_scalar_attribute_schema(
                    _ssn, "SwcInternalBehavior", "SUPPORTS-MULTIPLE-INSTANTIATION",
                    description="Indicates whether the component supports multiple instantiation. "
                                "Required by AUTOSAR standard (TPS_SWCT_01361).",
                ) or {
                    # KG 兜底（找不到时也给一个安全默认）
                    "type": "string",
                    "enum": ["true", "false"],
                    "description": "Indicates whether the component supports multiple instantiation. "
                                   "Required by AUTOSAR standard (TPS_SWCT_01361).",
                }
                handle_term = self._resolve_scalar_attribute_schema(
                    _ssn, "SwcInternalBehavior", "HANDLE-TERMINATION-AND-RESTART",
                    description="Controls the behavior with respect to stopping and restarting the component.",
                ) or {
                    # KG 兜底（用 XSD 中正确的三个枚举值，至少不会跑出 boolean 那种错）
                    "type": "string",
                    "enum": ["CAN-BE-TERMINATED", "CAN-BE-TERMINATED-AND-RESTARTED", "NO-SUPPORT"],
                    "description": "Controls the behavior with respect to stopping and restarting the component.",
                }

                ib_info = self._query_class_attributes(_ssn, "SwcInternalBehavior")
                ib_model = self._select_xsd_context_model(
                    ib_info.get("xsd_content_model"),
                    ib_info.get("xsd_context_models") or [],
                    parent_class_ident=comp_type,
                    parent_container_tag="INTERNAL-BEHAVIORS",
                )
                if not ib_model:
                    raise KGQueryError("SwcInternalBehavior XSD content model is unavailable")
                ib_occurrences = content_occurrence_index(ib_model)
                selected_ib_children = set(
                    design_index.get("SWC-INTERNAL-BEHAVIOR") or set()
                )

                def include_ib(tag: str) -> bool:
                    occurrence = ib_occurrences.get(tag)
                    return bool(
                        (occurrence and occurrence.min_occurs >= 1)
                        or tag in selected_ib_children
                    )

                if not include_ib("SUPPORTS-MULTIPLE-INSTANTIATION"):
                    supports_multi = None
                if not include_ib("HANDLE-TERMINATION-AND-RESTART"):
                    handle_term = None

            sib_props = {
                "SHORT-NAME": sib_short_name_schema,
                **(
                    {"SUPPORTS-MULTIPLE-INSTANTIATION": supports_multi}
                    if supports_multi is not None else {}
                ),
                **(
                    {"HANDLE-TERMINATION-AND-RESTART": handle_term}
                    if handle_term is not None else {}
                ),
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
    def component_xml_projection_map(self, comp_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Return the deterministic inverse of the provider-facing flattening."""
        comp_type = (
            comp_plan.get("type") or "ECU-ABSTRACTION-SW-COMPONENT-TYPE"
        ).strip()
        design_index = self._build_design_index(comp_plan.get("element_design") or {})
        rules: List[Dict[str, List[str]]] = []
        if "INTERNAL-BEHAVIORS" in design_index.get("__TOP__", set()):
            rules.extend([
                {
                    "source": ["SWC-INTERNAL-BEHAVIOR"],
                    "target": ["INTERNAL-BEHAVIORS", "SWC-INTERNAL-BEHAVIOR"],
                },
                {
                    "source": [
                        "INTERNAL-BEHAVIORS",
                        "SWC-INTERNAL-BEHAVIOR",
                        "RUNNABLE-ENTITY",
                    ],
                    "target": [
                        "INTERNAL-BEHAVIORS",
                        "SWC-INTERNAL-BEHAVIOR",
                        "RUNNABLES",
                        "RUNNABLE-ENTITY",
                    ],
                },
            ])
        return {
            "schema_version": "1.0",
            "component_type": comp_type,
            "rules": rules,
        }
    def _is_union_container_shell(self, session, class_ident: str) -> bool:
        """
        识别"联合容器壳"(模式2)：外层Class仅作为多个内层元素的容器

        判断依据：
        1. 该类有多个非XML属性的子元素 (len > 1)
        2. 每个子元素的maxOccurs=0 (在choice/sequence中可选)
        3. 调用方会额外判断父层maxOccurs=-1

        Returns:
            True: 该类是联合容器壳，应生成为object，子元素强制为array
            False: 正常处理
        """
        try:
            info = self._query_class_attributes(session, class_ident)
            attrs = info.get("attributes", [])

            # 过滤出实际子元素(排除XML属性、SHORT-NAME等元数据)
            child_elements = [
                a for a in attrs
                if not (a.get("isXmlAttr") or a.get("is_xml_attribute"))  # 非XML属性
                   and (a.get("xml_tag") or a.get("name"))  # 有标签名
                   and (a.get("xml_tag") or "").upper() not in {"SHORT-NAME", "DESC", "CATEGORY"}  # 非元数据
            ]

            # 必须有多个子元素
            if len(child_elements) <= 1:
                return False

            # 检查子元素是否都是maxOccurs=0 (可选)
            all_optional = all(
                int(a.get("maxOccurs", 0)) == 0
                for a in child_elements
            )

            if CONFIG.debug_mode and all_optional:
                print(f"[DEBUG] 识别到联合容器壳: {class_ident}, "
                      f"子元素: {[a.get('xml_tag') for a in child_elements]}")

            return all_optional

        except Exception as e:
            if CONFIG.debug_mode:
                print(f"[DEBUG] 容器壳判断异常 {class_ident}: {e}")
            return False

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
                force_children_array=False
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
            force_children_array=False
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
                force_children_array=False
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

    def _apply_short_name_constraint(self, schema_node: dict) -> dict:
        """为SHORT-NAME的Schema节点统一添加pattern和description约束。"""
        pattern = r"^[a-zA-Z][a-zA-Z0-9_]*$"
        description = "Identifier must start with a letter, and can only contain letters, numbers, and underscores (_). Hyphens (-) are not allowed."

        # 检查节点是否为数组，约束应施加在 `items` 上
        if schema_node.get("type") == "array" and isinstance(schema_node.get("items"), dict):
            schema_node["items"]["pattern"] = pattern
            schema_node["items"]["description"] = description
        else:
            schema_node["pattern"] = pattern
            schema_node["description"] = description

        return schema_node

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
        - 依赖 KG：展开 (minOccurs>=1) 的元素以及 Round1 data_elements 选中的路径
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
                    design_index = interface_design_index(itype, items)
                    _nm, base_schema, defs = self._build_class_schema_recursive(
                        session=session,
                        class_ident=itype,
                        parent_container_tag=itype,
                        design_index=design_index,
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
                            sn["enum"] = examples

                    requested_data_elements = sorted({
                        str(name).strip()
                        for plan in items
                        for name in (plan.get("data_elements") or [])
                        if str(name).strip()
                    })
                    if requested_data_elements:
                        data_nodes: List[Dict[str, Any]] = []

                        def collect_data_nodes(node: Any) -> None:
                            if not isinstance(node, dict):
                                return
                            properties_node = node.get("properties")
                            if isinstance(properties_node, dict):
                                for key, child in properties_node.items():
                                    if _up(key) == "VARIABLE-DATA-PROTOTYPE" and isinstance(child, dict):
                                        data_nodes.append(child)
                                    collect_data_nodes(child)
                            items_node = node.get("items")
                            if isinstance(items_node, dict):
                                collect_data_nodes(items_node)

                        collect_data_nodes(base_schema)
                        if len(data_nodes) != 1:
                            raise KGQueryError(
                                f"expected one VARIABLE-DATA-PROTOTYPE schema for {itype}, "
                                f"found {len(data_nodes)}"
                            )
                        data_node = data_nodes[0]
                        data_item = data_node.get("items") if data_node.get("type") == "array" else data_node
                        data_name = (data_item.get("properties") or {}).get("SHORT-NAME")
                        if not isinstance(data_name, dict):
                            raise KGQueryError(
                                f"VARIABLE-DATA-PROTOTYPE for {itype} has no SHORT-NAME schema"
                            )
                        data_name["enum"] = requested_data_elements
                        if data_node.get("type") == "array":
                            counts = [len(plan.get("data_elements") or []) for plan in items]
                            data_node["minItems"] = min(counts)
                            data_node["maxItems"] = max(counts)

                    properties[itype] = {
                        "type": "array",
                        "items": base_schema,
                        "minItems": len(items),
                        "maxItems": len(items),
                    }
                    required.append(itype)
                except Exception as error:
                    raise KGQueryError(
                        f"failed to build requested interface schema for {itype}: {error}"
                    ) from error

        return {
            "type": "object",
            "additionalProperties": False,
            "properties": properties,
            "required": required,
            "definitions": definitions or {}
        }

    @staticmethod
    def _clean_xsd_pattern(pattern_str: str) -> Optional[str]:
        """
        清理 XSD pattern 字符串，提取纯正则表达式

        输入示例：
        '<xsd:pattern xmlns:xsd="..." value="[0-1]"/>'

        输出：
        '[0-1]'
        """
        import re
        if not pattern_str:
            return None

        # 尝试提取 value 属性
        match = re.search(r'value="([^"]+)"', pattern_str)
        if match:
            return match.group(1)

        # 如果没有 XML 标签，假设已经是纯正则
        if not pattern_str.strip().startswith('<'):
            return pattern_str.strip()

        return None

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
