"""
动态查询引擎 - 从知识图谱查询AUTOSAR元模型信息并生成JSON Schema
修复查询字段不匹配问题：统一使用灵活查询策略
"""
import json
import time
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
from functools import lru_cache
from ..config import CONFIG
from ..utils.exceptions import KGQueryError
from ..utils.monitoring import schema_monitor

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    print("[WARN] neo4j driver未安装，使用模拟数据")


@dataclass
class XMLElementInfo:
    """XML元素信息"""
    xml_tag: str
    attributes: List[Dict[str, Any]]
    child_elements: List[str]
    constraints: List[str]
    is_required: bool
    min_occurs: int
    max_occurs: int


@dataclass
class ComponentSchema:
    """组件Schema信息"""
    component_type: str
    xml_structure: Dict[str, Any]
    required_elements: List[str]
    optional_elements: List[str]
    constraints: List[str]


class DepthManager:
    """递归深度管理器"""

    def __init__(self, max_depth: int = 50):
        self.max_depth = max_depth
        self.current_depth = 0
        self.path_stack = []

    def can_go_deeper(self) -> bool:
        """检查是否可以继续深入"""
        return self.current_depth < self.max_depth

    def enter_level(self, tag: str) -> bool:
        """进入新的递归层级"""
        if tag in self.path_stack:  # 循环检测
            return False
        if not self.can_go_deeper():
            return False
        self.current_depth += 1
        self.path_stack.append(tag)
        return True

    def exit_level(self):
        """退出当前递归层级"""
        if self.path_stack:
            self.path_stack.pop()
            self.current_depth -= 1

    def get_depth(self) -> int:
        """获取当前深度"""
        return self.current_depth

    def reset(self):
        """重置深度管理器"""
        self.current_depth = 0
        self.path_stack.clear()


class SchemaCache:
    """Schema缓存管理器"""

    def __init__(self, max_size: int = 100, ttl: int = 3600):
        self.cache = {}
        self.timestamps = {}
        self.max_size = max_size
        self.ttl = ttl
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """获取缓存项"""
        if key in self.cache:
            # 检查是否过期
            if time.time() - self.timestamps[key] < self.ttl:
                self.hits += 1
                return self.cache[key]
            else:
                # 过期则删除
                del self.cache[key]
                del self.timestamps[key]
        self.misses += 1
        return None

    def set(self, key: str, value: Dict[str, Any]):
        """设置缓存项"""
        # 如果缓存已满，删除最旧的项
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.timestamps, key=self.timestamps.get)
            del self.cache[oldest_key]
            del self.timestamps[oldest_key]

        self.cache[key] = value
        self.timestamps[key] = time.time()

    def clear(self):
        """清空缓存"""
        self.cache.clear()
        self.timestamps.clear()
        self.hits = 0
        self.misses = 0

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0
        return {
            "size": len(self.cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
            "max_size": self.max_size,
            "ttl": self.ttl
        }


class QueryOptimizer:
    """查询优化器"""

    def __init__(self):
        self.query_cache = {}

    def optimize_query(self, query: str, params: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """优化查询语句"""
        # 添加查询提示
        optimized_query = query

        # 如果查询大量数据，添加LIMIT提示
        if "MATCH" in query and "LIMIT" not in query:
            # 为安全起见，对没有LIMIT的查询添加默认限制
            optimized_query = query + " LIMIT 1000"

        return optimized_query, params

    @lru_cache(maxsize=128)
    def get_cached_query_plan(self, query_hash: str):
        """获取缓存的查询计划"""
        return self.query_cache.get(query_hash)


class DynamicQueryEngine:
    """动态查询引擎"""

    def __init__(self):
        """初始化查询引擎"""
        self.config = CONFIG.knowledge_graph
        self.driver = None

        # 使用配置中的值
        self.max_safety_depth = self.config.max_safety_depth

        # 深度管理器
        self.depth_manager = DepthManager(self.max_safety_depth)

        # 缓存管理器
        cache_config = CONFIG.schema_generation.cache_config
        self.schema_cache = SchemaCache(
            max_size=cache_config.max_cache_size,
            ttl=cache_config.application_cache_ttl
        )

        # 初始化请求级缓存
        self.request_cache = {} if cache_config.enable_request_cache else None

        # 类型级schema缓存（真正的复用）
        self.type_schema_cache = {}

        # 查询优化器
        self.query_optimizer = QueryOptimizer()

        # 终止条件配置
        self.termination_patterns = {
            'ref_suffixes': CONFIG.schema_generation.termination_rules.ref_suffixes,
            'standard_prefixes': CONFIG.schema_generation.termination_rules.standard_prefixes
        }

        # 性能配置
        self.performance_config = CONFIG.schema_generation.performance

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

    def generate_multi_component_schema(self, component_plans: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成多组件Schema - 修复版，实现真正的类型复用"""

        if not self.driver:
            raise KGQueryError("Neo4j连接未建立，无法生成Schema")

        # 按类型分组组件
        components_by_type = {}
        for comp_plan in component_plans:
            comp_type = comp_plan.get("type", "")
            comp_name = comp_plan.get("name", "")

            if not comp_type:
                raise KGQueryError(f"组件{comp_name}缺少类型定义")

            if comp_type not in components_by_type:
                components_by_type[comp_type] = []
            components_by_type[comp_type].append(comp_plan)

        if CONFIG.debug_mode:
            print(f"\n[SCHEMA] 组件类型分组:")
            for comp_type, comps in components_by_type.items():
                comp_names = [c['name'] for c in comps]
                print(f"  {comp_type}: {comp_names}")

        # 为每个类型生成一次schema，然后为该类型的所有组件使用引用
        schemas = {}
        type_definitions = {}  # 存储类型定义

        with self.driver.session() as session:
            for comp_type, comp_plans_of_type in components_by_type.items():
                # 只为该类型生成一次schema
                if comp_type not in self.type_schema_cache:
                    if CONFIG.debug_mode:
                        print(f"\n[SCHEMA] 生成类型schema: {comp_type}")

                    # 合并该类型所有组件的element_design
                    merged_element_design = self._merge_element_designs(comp_plans_of_type)

                    # 生成类型schema
                    type_schema = self._build_component_schema_with_design_filtered(
                        session,
                        comp_type,
                        merged_element_design
                    )

                    self.type_schema_cache[comp_type] = type_schema
                    type_definitions[comp_type] = type_schema
                else:
                    if CONFIG.debug_mode:
                        print(f"[SCHEMA] 复用已有类型schema: {comp_type}")
                    type_definitions[comp_type] = self.type_schema_cache[comp_type]

                # 为该类型的每个组件创建引用
                for comp_plan in comp_plans_of_type:
                    comp_name = comp_plan.get("name", "")
                    # 使用$ref引用类型定义
                    schemas[comp_name] = {"$ref": f"#/definitions/{comp_type}"}

        # 构建最终schema
        result = {
            "type": "object",
            "properties": schemas,
            "required": list(schemas.keys()),
            "definitions": type_definitions,  # 添加类型定义
            "description": f"包含{len(component_plans)}个组件的Schema定义（{len(type_definitions)}个类型）"
        }

        if CONFIG.debug_mode:
            print(f"\n[SCHEMA] 生成完成:")
            print(f"  - 组件数: {len(component_plans)}")
            print(f"  - 类型数: {len(type_definitions)}")
            print(f"  - Schema大小减少: {(1 - len(type_definitions) / len(component_plans)) * 100:.1f}%")

        return result

    def _merge_element_designs(self, comp_plans: List[Dict[str, Any]]) -> Dict[str, Any]:
        """合并同类型组件的element_design"""
        merged = {
            "ports": {"needed": False, "types": []},
            "internal_behaviors": {"needed": False, "runnables": {}, "events": []}
        }

        for comp_plan in comp_plans:
            element_design = comp_plan.get("element_design", {})

            # 合并ports需求
            if element_design.get("ports", {}).get("needed"):
                merged["ports"]["needed"] = True
                port_types = element_design.get("ports", {}).get("types", [])
                merged["ports"]["types"].extend(port_types)

            # 合并internal_behaviors需求
            ib = element_design.get("internal_behaviors", {})
            if ib.get("needed"):
                merged["internal_behaviors"]["needed"] = True

                # 合并runnables（现在是对象结构）
                runnables = ib.get("runnables", {})
                if runnables:
                    if not merged["internal_behaviors"]["runnables"]:
                        merged["internal_behaviors"]["runnables"] = {
                            "names": [],
                            "required_elements": [],
                            "optional_elements": []
                        }

                    # 合并runnable名称
                    merged["internal_behaviors"]["runnables"]["names"].extend(
                        runnables.get("names", [])
                    )

                    # 合并required_elements（取并集）
                    merged["internal_behaviors"]["runnables"]["required_elements"] = list(set(
                        merged["internal_behaviors"]["runnables"]["required_elements"] +
                        runnables.get("required_elements", [])
                    ))

                    # 合并optional_elements（取并集）
                    merged["internal_behaviors"]["runnables"]["optional_elements"] = list(set(
                        merged["internal_behaviors"]["runnables"]["optional_elements"] +
                        runnables.get("optional_elements", [])
                    ))

                # 合并events
                merged["internal_behaviors"]["events"].extend(ib.get("events", []))

        # 去重处理
        merged["ports"]["types"] = list(set(merged["ports"]["types"]))

        # Events去重（保持原有逻辑）
        seen_events = []
        unique_events = []
        for event in merged["internal_behaviors"]["events"]:
            if isinstance(event, dict):
                event_key = (event.get("type", ""), event.get("name", ""))
                if event_key not in seen_events:
                    seen_events.append(event_key)
                    unique_events.append(event)

        merged["internal_behaviors"]["events"] = unique_events

        # Runnable names去重
        if merged["internal_behaviors"]["runnables"]:
            merged["internal_behaviors"]["runnables"]["names"] = list(set(
                merged["internal_behaviors"]["runnables"]["names"]
            ))

        return merged

    def _build_component_schema_with_design_filtered(
            self,
            session,
            component_type: str,
            element_design: Dict[str, Any]
    ) -> Dict[str, Any]:
        """构建组件Schema - 过滤版本，只包含必要元素"""

        # 清空请求级缓存和重置深度管理器
        if self.request_cache is not None:
            self.request_cache.clear()
        self.depth_manager.reset()

        # 构建必需路径树（只包含必需元素）
        required_paths = self._build_required_paths_tree_filtered(
            session,
            component_type,
            element_design
        )

        # 生成Schema
        schema = self._build_schema_from_paths(
            session,
            component_type,
            required_paths,
            element_design
        )

        return schema

    def _build_required_paths_tree_filtered(
            self,
            session,
            component_type: str,
            element_design: Dict[str, Any]
    ) -> Dict[str, Any]:
        """构建必需元素路径树 - 严格过滤版本"""

        # 提取element_design中明确指定的元素
        design_elements = []

        # 处理端口设计
        if element_design.get("ports", {}).get("needed"):
            design_elements.append("PORTS")
            port_types = element_design.get("ports", {}).get("types", [])
            design_elements.extend(port_types)

        # 处理事件设计
        if element_design.get("internal_behaviors", {}).get("needed"):
            design_elements.append("INTERNAL-BEHAVIORS")
            design_elements.append("SWC-INTERNAL-BEHAVIOR")
            design_elements.append("EVENTS")
            design_elements.append("RUNNABLES")
            design_elements.append("RUNNABLE-ENTITY")

            # 添加具体的事件类型
            events = element_design.get("internal_behaviors", {}).get("events", [])
            for event in events:
                if isinstance(event, dict) and "type" in event:
                    design_elements.append(event["type"])

        # KG查询 - 只获取minOccurs>=1或设计指定的元素
        query = """
        MATCH (c:Class)
        WHERE c.name = $component_type OR c.xml_tag = $component_type
        OPTIONAL MATCH (c)-[:SUBCLASS_OF*0..]->(parent:Class)
        WITH c, collect(DISTINCT parent) as parents

        UNWIND (parents + [c]) as cls
        OPTIONAL MATCH (cls)-[:HAS_ATTRIBUTE]->(attr:Attribute)
        WHERE (attr.minOccurs >= 1) OR (attr.xml_tag IN $design_elements)

        // 不要硬编码过滤列表！让Round1设计和minOccurs决定
        OPTIONAL MATCH (attr)-[:TYPE_OF]->(type)

        RETURN cls.name as class_name,
               cls.xml_tag as class_xml_tag,
               collect(DISTINCT {
                   name: attr.name,
                   xml_tag: attr.xml_tag,
                   minOccurs: attr.minOccurs,
                   maxOccurs: attr.maxOccurs,
                   xml_wrapper_tag: attr.xml_wrapper_tag,
                   isXmlAttr: attr.isXmlAttr,
                   type_xml_tag: type.xml_tag,
                   type_name: type.name,
                   type_labels: labels(type)
               }) as attributes
        """

        result = session.run(query,
                             component_type=component_type,
                             design_elements=design_elements)

        paths_tree = {
            "required": [],
            "design_required": design_elements
        }

        for record in result:
            for attr in record["attributes"]:
                # 严格筛选：只要minOccurs>=1或在design_elements中的
                minOccurs = attr.get("minOccurs") or 0
                if minOccurs >= 1 or attr.get("xml_tag") in design_elements:
                    paths_tree["required"].append(attr)

        return paths_tree

    def generate_multi_interface_schema(self, interface_plans: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成多接口Schema - 类似组件的类型复用机制"""

        if not self.driver:
            raise KGQueryError("Neo4j连接未建立，无法生成Schema")

        # 按类型分组接口
        interfaces_by_type = {}
        for intf_plan in interface_plans:
            intf_type = intf_plan.get("type", "")
            intf_name = intf_plan.get("name", "")

            if not intf_type:
                raise KGQueryError(f"接口{intf_name}缺少类型定义")

            if intf_type not in interfaces_by_type:
                interfaces_by_type[intf_type] = []
            interfaces_by_type[intf_type].append(intf_plan)

        if CONFIG.debug_mode:
            print(f"\n[SCHEMA] 接口类型分组:")
            for intf_type, intfs in interfaces_by_type.items():
                intf_names = [i['name'] for i in intfs]
                print(f"  {intf_type}: {intf_names}")

        # 为每个类型生成一次schema，然后复用
        schemas = {}
        type_definitions = {}

        with self.driver.session() as session:
            for intf_type, intf_plans_of_type in interfaces_by_type.items():
                # 检查缓存
                cache_key = f"interface_{intf_type}"
                if cache_key not in self.type_schema_cache:
                    if CONFIG.debug_mode:
                        print(f"\n[SCHEMA] 生成接口类型schema: {intf_type}")

                    # 生成接口类型schema
                    type_schema = self._build_interface_schema_from_kg(
                        session,
                        intf_type
                    )

                    self.type_schema_cache[cache_key] = type_schema
                    type_definitions[intf_type] = type_schema
                else:
                    if CONFIG.debug_mode:
                        print(f"[SCHEMA] 复用已有接口类型schema: {intf_type}")
                    type_definitions[intf_type] = self.type_schema_cache[cache_key]

                # 为该类型的每个接口创建引用
                for intf_plan in intf_plans_of_type:
                    intf_name = intf_plan.get("name", "")
                    schemas[intf_name] = {"$ref": f"#/definitions/{intf_type}"}

        return {
            "type": "object",
            "properties": schemas,
            "definitions": type_definitions,
            "description": f"包含{len(interface_plans)}个接口的Schema定义（{len(type_definitions)}个类型）"
        }

    def _build_interface_schema_from_kg(self, session, interface_type: str) -> Dict[str, Any]:
        """从KG构建接口Schema - 完全KG驱动"""

        # 重置深度管理器
        self.depth_manager.reset()

        # 查询接口结构
        query = """
        MATCH (i:Class)
        WHERE i.name = $interface_type OR i.xml_tag = $interface_type

        // 获取所有属性（包括继承的）
        OPTIONAL MATCH (i)-[:SUBCLASS_OF*0..]->(parent:Class)
        WITH i, collect(DISTINCT parent) as parents

        UNWIND (parents + [i]) as cls
        OPTIONAL MATCH (cls)-[:HAS_ATTRIBUTE]->(attr:Attribute)
        OPTIONAL MATCH (attr)-[:TYPE_OF]->(attrType)

        // 获取子元素
        OPTIONAL MATCH (i)-[:HAS_CHILD]->(child:Class)

        RETURN i.xml_tag as interface_tag,
               i.name as interface_name,
               collect(DISTINCT {
                   name: attr.name,
                   xml_tag: attr.xml_tag,
                   minOccurs: attr.minOccurs,
                   maxOccurs: attr.maxOccurs,
                   type_name: attrType.name,
                   type_xml_tag: attrType.xml_tag
               }) as attributes,
               collect(DISTINCT child.xml_tag) as child_elements
        """

        result = session.run(query, interface_type=interface_type)
        record = result.single()

        if not record:
            return {"type": "object", "description": f"Unknown interface type: {interface_type}"}

        # 构建Schema
        schema = {
            "type": "object",
            "properties": {},
            "required": []
        }

        # 处理必需属性
        for attr in record["attributes"]:
            minOccurs = attr.get("minOccurs") or 0
            if minOccurs >= 1:
                attr_key = attr.get("xml_tag") or attr.get("name")
                if attr_key:
                    schema["properties"][attr_key] = {"type": "string"}
                    schema["required"].append(attr_key)

        # 处理子元素（如DATA-ELEMENTS, OPERATIONS等）
        for child_tag in record["child_elements"]:
            if child_tag:
                child_schema = self._query_interface_child_structure(session, child_tag, interface_type)
                if child_schema:
                    schema["properties"][child_tag] = child_schema

        return schema

    def _query_interface_child_structure(self, session, child_tag: str, interface_type: str) -> Dict[str, Any]:
        """查询接口子元素结构 - 完全KG驱动"""

        # 特殊处理DATA-ELEMENTS
        if child_tag == "DATA-ELEMENTS":
            return self._query_data_elements_structure(session, interface_type)
        elif child_tag == "OPERATIONS":
            return self._query_operations_structure(session, interface_type)
        else:
            # 通用子元素查询
            return self._query_generic_child_structure(session, child_tag)

    def _query_data_elements_structure(self, session, interface_type: str) -> Dict[str, Any]:
        """查询DATA-ELEMENTS结构 - 完全从KG"""

        query = """
        MATCH (de:Class)
        WHERE de.name = 'VariableDataPrototype' OR de.xml_tag = 'VARIABLE-DATA-PROTOTYPE'

        OPTIONAL MATCH (de)-[:HAS_ATTRIBUTE]->(attr:Attribute)
        WHERE attr.minOccurs >= 1

        RETURN collect(DISTINCT {
            xml_tag: attr.xml_tag,
            name: attr.name,
            minOccurs: attr.minOccurs
        }) as required_attrs
        """

        result = session.run(query)
        record = result.single()

        if record:
            item_schema = {
                "type": "object",
                "properties": {
                    "SHORT-NAME": {"type": "string"},
                    "TYPE-TREF": {
                        "type": "string",
                        "description": "引用IMPLEMENTATION-DATA-TYPE"
                    }
                },
                "required": ["SHORT-NAME", "TYPE-TREF"]
            }

            # 添加其他必需属性
            for attr in record["required_attrs"]:
                if attr["xml_tag"] not in ["SHORT-NAME", "TYPE-TREF"]:
                    item_schema["properties"][attr["xml_tag"]] = {"type": "string"}
                    minOccurs = attr.get("minOccurs") or 0
                    if minOccurs >= 1:
                        item_schema["required"].append(attr["xml_tag"])

            return {
                "type": "array",
                "items": item_schema
            }

        return {"type": "array", "items": {"type": "object"}}

    def _query_ports_structure(self, session, port_types: List[str]) -> Dict[str, Any]:
        """动态查询端口结构 - 基于element_design指定的类型"""

        ports_schema = {
            "type": "object",
            "properties": {}
        }

        # 只查询element_design指定的端口类型
        for port_type in port_types:
            query = """
            MATCH (port:Class)
            WHERE port.xml_tag = $port_type
            OPTIONAL MATCH (port)-[:SUBCLASS_OF*0..]->(parent:Class)
            WITH port, collect(DISTINCT parent) as parents

            UNWIND (parents + [port]) as cls
            OPTIONAL MATCH (cls)-[:HAS_ATTRIBUTE]->(attr:Attribute)
            WHERE attr.minOccurs >= 1  // 只要必需属性
            OPTIONAL MATCH (attr)-[:TYPE_OF]->(attrType)

            RETURN port.xml_tag as port_xml_tag,
                   collect(DISTINCT {
                       name: attr.name,
                       xml_tag: attr.xml_tag,
                       minOccurs: attr.minOccurs,
                       isXmlAttr: attr.isXmlAttr,
                       type_name: attrType.name
                   }) as required_attributes
            """

            result = session.run(query, port_type=port_type)
            record = result.single()

            if record:
                port_item_schema = {
                    "type": "object",
                    "properties": {},
                    "required": []
                }

                for attr in record['required_attributes']:
                    if attr['name']:
                        attr_key = f"@{attr['xml_tag']}" if attr.get('isXmlAttr') else attr['xml_tag']
                        port_item_schema["properties"][attr_key] = {"type": "string"}
                        if attr.get('minOccurs', 0) >= 1:
                            port_item_schema["required"].append(attr_key)

                ports_schema["properties"][port_type] = {
                    "type": "array",
                    "items": port_item_schema
                }

        return ports_schema

    def _query_event_type_from_kg(self, session, event_type: str) -> Dict[str, Any]:
        """从KG查询特定事件类型的Schema - 完全KG驱动版本"""

        query = """
        MATCH (event:Class)
        WHERE event.xml_tag = $event_type OR event.name = $event_type

        // 获取所有属性（包括继承的）- 只要必需的
        OPTIONAL MATCH (event)-[:SUBCLASS_OF*0..]->(parent:Class)
        WITH event, collect(DISTINCT parent) as parents

        UNWIND (parents + [event]) as cls
        OPTIONAL MATCH (cls)-[:HAS_ATTRIBUTE]->(attr:Attribute)
        WHERE attr.minOccurs >= 1  // 只查询必需属性
        OPTIONAL MATCH (attr)-[:TYPE_OF]->(attrType)

        RETURN event.xml_tag as event_tag,
               collect(DISTINCT {
                   name: attr.name,
                   xml_tag: attr.xml_tag,
                   minOccurs: attr.minOccurs,
                   maxOccurs: attr.maxOccurs,
                   type_name: attrType.name,
                   type_xml_tag: attrType.xml_tag,
                   isPrimitiveType: attrType.isPrimitiveType,
                   isComplexType: attrType.isComplexType,
                   isXmlAttr: attr.isXmlAttr
               }) as attributes
        """

        result = session.run(query, event_type=event_type)
        record = result.single()

        if not record:
            # 如果KG中没有，返回空schema而不是硬编码的默认值
            return None

        # 构建事件Schema - 完全基于KG查询结果
        event_schema = {
            "type": "object",
            "properties": {},
            "required": []
        }

        # 处理所有必需属性
        for attr in record["attributes"]:
            if not attr.get("name"):
                continue

            attr_key = attr.get("xml_tag") or attr.get("name")
            if attr.get("isXmlAttr"):
                attr_key = f"@{attr_key}"

            # 根据KG中的类型信息决定schema类型
            if attr.get("isPrimitiveType"):
                type_name = attr.get("type_name", "string")
                attr_schema = self._map_primitive_type(type_name)
            elif attr.get("isComplexType") and self.depth_manager.can_go_deeper():
                # 复杂类型需要递归查询
                attr_schema = self._build_schema_recursive(
                    session,
                    attr.get("type_name"),
                    {"design_required": []},  # 事件属性不需要额外的design过滤
                    {}
                )
            else:
                attr_schema = {"type": "string"}

            event_schema["properties"][attr_key] = attr_schema

            # minOccurs >= 1的属性加入required
            if attr.get("minOccurs", 0) >= 1:
                event_schema["required"].append(attr_key)

        return event_schema

    def _query_runnable_entity_deep(self, session, runnable_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """深度查询RUNNABLE-ENTITY结构 - 完全KG驱动并递归展开"""

        # 获取配置的元素
        if not runnable_config:
            runnable_config = CONFIG.round1_schema.runnable_entity_config

        if isinstance(runnable_config, dict):
            required_elements = runnable_config.get("required_elements", [])
            optional_elements = runnable_config.get("optional_elements", [])
        else:
            required_elements = getattr(runnable_config, "required_elements", []) or []
            optional_elements = getattr(runnable_config, "optional_elements", []) or []

        all_elements = required_elements + optional_elements

        # 查询RunnableEntity的完整结构
        query = """
        MATCH (re:Class)
        WHERE re.name = 'RunnableEntity' OR re.xml_tag = 'RUNNABLE-ENTITY'

        // 获取所有属性（包括继承的）
        OPTIONAL MATCH (re)-[:SUBCLASS_OF*0..]->(parent:Class)
        WITH re, collect(DISTINCT parent) as parents

        UNWIND (parents + [re]) as cls
        OPTIONAL MATCH (cls)-[:HAS_ATTRIBUTE]->(attr:Attribute)
        WHERE (attr.minOccurs >= 1) OR 
              (attr.xml_tag IN $all_elements) OR 
              (attr.name IN $all_elements)
        OPTIONAL MATCH (attr)-[:TYPE_OF]->(attrType)

        RETURN re.xml_tag as runnable_tag,
               collect(DISTINCT {
                   name: attr.name,
                   xml_tag: attr.xml_tag,
                   minOccurs: attr.minOccurs,
                   maxOccurs: attr.maxOccurs,
                   type_name: attrType.name,
                   type_xml_tag: attrType.xml_tag,
                   isComplexType: attrType.isComplexType,
                   isPrimitiveType: attrType.isPrimitiveType,
                   isXmlAttr: attr.isXmlAttr,
                   isRequired: (attr.minOccurs >= 1) OR 
                              (attr.xml_tag IN $required_elements) OR 
                              (attr.name IN $required_elements)
               }) as attributes
        """

        result = session.run(query,
                             all_elements=all_elements,
                             required_elements=required_elements)
        record = result.single()

        if not record:
            return None

        # 构建详细的RunnableEntity Schema
        runnable_schema = {
            "type": "object",
            "properties": {},
            "required": []
        }

        # 处理所有配置的属性
        for attr in record["attributes"]:
            attr_key = attr.get("xml_tag") or attr.get("name")
            if not attr_key:
                continue

            if attr.get("isXmlAttr"):
                attr_key = f"@{attr_key}"

            # 根据属性类型构建schema
            if attr.get("isPrimitiveType"):
                type_name = attr.get("type_name", "string")
                attr_schema = self._map_primitive_type(type_name)
            elif attr.get("isComplexType") and self.depth_manager.can_go_deeper():
                # 复杂类型递归展开
                self.depth_manager.enter_level("RUNNABLE-ENTITY-ATTR")
                try:
                    attr_schema = self._build_schema_recursive(
                        session,
                        attr.get("type_name"),
                        {"design_required": []},
                        {}
                    )
                finally:
                    self.depth_manager.exit_level()
            else:
                # 根据属性名推断类型（从KG查询）
                type_query = """
                MATCH (attr:Attribute {xml_tag: $attr_tag})-[:TYPE_OF]->(type)
                RETURN type.name as type_name, 
                       type.isPrimitiveType as is_primitive,
                       type.baseType as base_type
                LIMIT 1
                """
                type_result = session.run(type_query, attr_tag=attr_key.lstrip("@"))
                type_record = type_result.single()

                if type_record and type_record["is_primitive"]:
                    attr_schema = self._map_primitive_type(type_record.get("base_type", "string"))
                else:
                    attr_schema = {"type": "string"}

            runnable_schema["properties"][attr_key] = attr_schema

            # 处理必需属性
            if attr.get("isRequired"):
                runnable_schema["required"].append(attr_key)

        return {
            "type": "array",
            "items": runnable_schema
        }

    def _query_behaviors_structure(self, session, behavior_design: Dict[str, Any]) -> Dict[str, Any]:
        """动态查询内部行为结构 - 完全基于element_design和KG，无硬编码"""

        behavior_schema = {
            "type": "object",
            "properties": {
                "SWC-INTERNAL-BEHAVIOR": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }

        swc_behavior = behavior_schema["properties"]["SWC-INTERNAL-BEHAVIOR"]

        # 查询SWC-INTERNAL-BEHAVIOR的必需属性
        behavior_query = """
        MATCH (b:Class)
        WHERE b.name = 'SwcInternalBehavior' OR b.xml_tag = 'SWC-INTERNAL-BEHAVIOR'
        OPTIONAL MATCH (b)-[:HAS_ATTRIBUTE]->(attr:Attribute)
        WHERE attr.minOccurs >= 1
        RETURN collect(DISTINCT {
            xml_tag: attr.xml_tag,
            name: attr.name,
            isXmlAttr: attr.isXmlAttr
        }) as required_attrs
        """

        behavior_result = session.run(behavior_query)
        behavior_record = behavior_result.single()

        if behavior_record:
            for attr in behavior_record["required_attrs"]:
                if attr["xml_tag"]:
                    attr_key = f"@{attr['xml_tag']}" if attr.get("isXmlAttr") else attr["xml_tag"]
                    swc_behavior["properties"][attr_key] = {"type": "string"}
                    swc_behavior["required"].append(attr_key)

        # 处理EVENTS - 基于element_design中指定的事件类型
        events = behavior_design.get("events", [])
        if events:
            events_schema = {
                "type": "object",
                "properties": {}
            }

            # 获取所有事件类型并查询其结构
            event_types = set()
            for event in events:
                if isinstance(event, dict) and "type" in event:
                    event_types.add(event["type"])

            # 为每个事件类型从KG查询完整结构
            for event_type in event_types:
                event_schema = self._query_event_type_from_kg(session, event_type)
                if event_schema:
                    events_schema["properties"][event_type] = {
                        "type": "array",
                        "items": event_schema
                    }

            if events_schema["properties"]:
                swc_behavior["properties"]["EVENTS"] = events_schema

        # 处理RUNNABLES - 使用深度查询
        runnables_info = behavior_design.get("runnables", {})
        if runnables_info:
            runnable_config = {
                "required_elements": runnables_info.get("required_elements", []),
                "optional_elements": runnables_info.get("optional_elements", [])
            }

            # 使用深度查询获取完整的RunnableEntity schema
            runnables_array_schema = self._query_runnable_entity_deep(session, runnable_config)
            if runnables_array_schema:
                swc_behavior["properties"]["RUNNABLES"] = {
                    "type": "object",
                    "properties": {
                        "RUNNABLE-ENTITY": runnables_array_schema
                    }
                }

        return behavior_schema

    def _get_ports_schema(self) -> Dict[str, Any]:
        """获取端口Schema - 深度展开版"""
        if not self.driver:
            raise KGQueryError("Neo4j连接未建立，无法生成端口Schema")

        with self.driver.session() as session:
            if CONFIG.debug_mode:
                print("\n[SCHEMA] 深度查询PORTS结构...")

            ports_schema = {
                "type": "object",
                "properties": {}
            }

            # 查询P-PORT-PROTOTYPE的详细结构
            p_port_schema = self._query_port_type_deep(session, "PPortPrototype", "P-PORT-PROTOTYPE")
            if p_port_schema:
                ports_schema["properties"]["P-PORT-PROTOTYPE"] = {
                    "type": "array",
                    "items": p_port_schema
                }

            # 查询R-PORT-PROTOTYPE的详细结构
            r_port_schema = self._query_port_type_deep(session, "RPortPrototype", "R-PORT-PROTOTYPE")
            if r_port_schema:
                ports_schema["properties"]["R-PORT-PROTOTYPE"] = {
                    "type": "array",
                    "items": r_port_schema
                }

            if CONFIG.debug_mode:
                print(f"[SCHEMA] PORTS Schema生成完成，包含{len(ports_schema['properties'])}种端口类型")

            return ports_schema

    def _query_port_type_deep(self, session, port_name: str, port_xml_tag: str) -> Dict[str, Any]:
        """深度查询端口类型结构"""

        query = """
        MATCH (port:Class)
        WHERE port.name = $port_name OR port.xml_tag = $port_xml_tag

        // 获取所有父类（包括自己）
        OPTIONAL MATCH (port)-[:SUBCLASS_OF*0..]->(parent:Class)
        WITH port, collect(DISTINCT parent) as parents

        // 获取所有必需属性
        UNWIND (parents + [port]) as cls
        OPTIONAL MATCH (cls)-[:HAS_ATTRIBUTE]->(attr:Attribute)
        WHERE attr.minOccurs >= 1  // 只要必需属性
        OPTIONAL MATCH (attr)-[:TYPE_OF]->(attrType)

        RETURN port.xml_tag as port_xml_tag,
               collect(DISTINCT {
                   name: attr.name,
                   xml_tag: attr.xml_tag,
                   type: attr.type,
                   type_name: attrType.name,
                   minOccurs: attr.minOccurs,
                   maxOccurs: attr.maxOccurs,
                   isXmlAttr: attr.isXmlAttr,
                   isPrimitiveType: attrType.isPrimitiveType
               }) as required_attributes
        """

        result = session.run(query, port_name=port_name, port_xml_tag=port_xml_tag)
        record = result.single()

        if not record:
            return None

        port_schema = {
            "type": "object",
            "properties": {},
            "required": []
        }

        # 只添加必需属性
        for attr in record['required_attributes']:
            if not attr['name']:
                continue

            attr_key = attr['xml_tag'] or attr['name']
            if attr.get('isXmlAttr'):
                attr_key = f"@{attr_key}"

            # 基础类型
            if attr.get('isPrimitiveType'):
                attr_schema = self._map_primitive_type(attr.get('type_name', 'string'))
            else:
                attr_schema = {"type": "string"}

            port_schema["properties"][attr_key] = attr_schema
            port_schema["required"].append(attr_key)

        # 添加必需的引用
        port_schema["properties"]["PROVIDED-INTERFACE-TREF"] = {
            "type": "string",
            "description": "接口引用"
        }

        return port_schema


    def _extract_design_elements(self, element_design: Dict[str, Any]) -> List[str]:
        """从element_design提取需要的元素 - 修复版本：处理null xml_tag"""
        design_elements = []

        if not self.driver:
            raise KGQueryError("Neo4j连接未建立，无法查询设计元素")

        with self.driver.session() as session:
            # 查询PORTS相关的所有子元素
            if element_design.get("ports", {}).get("needed"):
                # 先添加PORTS本身
                design_elements.append("PORTS")

                # 查询Ports的子元素
                ports_query = """
                MATCH (p:Class {name: 'Ports'})
                OPTIONAL MATCH (p)-[:HAS_CHILD*1..2]->(child:Class)
                WHERE child.xml_tag IS NOT NULL
                RETURN collect(DISTINCT child.xml_tag) as child_tags
                """
                result = session.run(ports_query)
                record = result.single()
                if record and record["child_tags"]:
                    design_elements.extend([tag for tag in record["child_tags"] if tag])

                # 如果没有找到子元素，添加标准的端口类型
                if len(design_elements) == 1:  # 只有PORTS
                    design_elements.extend(["P-PORT-PROTOTYPE", "R-PORT-PROTOTYPE"])

            # 查询INTERNAL-BEHAVIORS相关的所有子元素
            if element_design.get("internal_behaviors", {}).get("needed"):
                # 先添加基本元素
                design_elements.extend([
                    "INTERNAL-BEHAVIORS",
                    "SWC-INTERNAL-BEHAVIOR"
                ])

                # 查询InternalBehaviors的子元素
                behaviors_query = """
                MATCH (b:Class)
                WHERE b.name IN ['InternalBehaviors', 'SwcInternalBehavior']
                OPTIONAL MATCH (b)-[:HAS_CHILD*1..2]->(child:Class)
                WHERE child.xml_tag IN ['EVENTS', 'RUNNABLES', 'EXCLUSIVE-AREAS', 
                                        'INTER-RUNNABLE-VARIABLES', 'EXPLICIT-INTER-RUNNABLE-VARIABLES']
                RETURN collect(DISTINCT child.xml_tag) as child_tags
                """
                result = session.run(behaviors_query)
                record = result.single()
                if record and record["child_tags"]:
                    design_elements.extend([tag for tag in record["child_tags"] if tag])

        return design_elements

    def _organize_paths_tree(self, query_result, design_elements: List[str]) -> Dict[str, Any]:
        """组织路径树结构"""
        paths_tree = {
            "required": [],
            "optional": [],
            "design_required": design_elements
        }

        for record in query_result:
            for attr in record["attributes"]:
                min_occurs = attr.get("minOccurs")
                # 修复：处理None值
                if min_occurs is not None and min_occurs >= 1:
                    paths_tree["required"].append(attr)
                elif attr["xml_tag"] in design_elements:
                    paths_tree["required"].append(attr)  # 设计要求的也作为必需
                else:
                    paths_tree["optional"].append(attr)

        return paths_tree

    def _build_schema_from_paths(
            self,
            session,
            component_type: str,
            paths_tree: Dict[str, Any],
            element_design: Dict[str, Any]
    ) -> Dict[str, Any]:
        """从路径树构建Schema"""

        # 初始化根Schema
        schema = {
            "type": "object",
            "properties": {},
            "required": []
        }

        # 递归构建Schema
        schema = self._build_schema_recursive(
            session,
            component_type,
            paths_tree,
            element_design
        )

        return schema

    def _build_schema_recursive(
            self,
            session,
            current_class_name: str,
            paths_tree: Dict[str, Any],
            element_design: Dict[str, Any]
    ) -> Dict[str, Any]:
        """递归构建Schema - 修复版本"""

        # 检查缓存
        cache_key = f"{current_class_name}:{self.depth_manager.get_depth()}"
        if self.request_cache and cache_key in self.request_cache:
            return {"$ref": f"#/definitions/{current_class_name}"}

        # 特殊处理：顶级组件类型不检查终止条件
        if not (current_class_name.endswith("-SW-COMPONENT-TYPE") or
                current_class_name.endswith("SwComponentType")):
            # 检查终止条件
            termination_result = self._check_termination(session, current_class_name)
            if termination_result:
                return termination_result

        # 尝试进入新层级
        if not self.depth_manager.enter_level(current_class_name):
            return {"$ref": f"#/definitions/{current_class_name}"}

        try:
            # 查询当前类的结构
            structure = self._query_class_structure(session, current_class_name)
            if not structure:
                return {"type": "object", "description": f"Unknown type: {current_class_name}"}

            # 构建Schema
            schema = self._build_class_schema(
                session,
                structure,
                paths_tree,
                element_design
            )

            # 缓存结果
            if self.request_cache is not None:
                self.request_cache[cache_key] = schema

            return schema

        finally:
            # 退出当前层级
            self.depth_manager.exit_level()

    def _query_class_structure(self, session, class_name: str) -> Optional[Dict[str, Any]]:
        """查询类的结构信息 - 只查询必需属性"""
        query = """
        MATCH (c:Class)
        WHERE c.name = $class_name OR c.xml_tag = $class_name

        // 只获取必需的直接属性（minOccurs >= 1）
        OPTIONAL MATCH (c)-[:HAS_ATTRIBUTE]->(attr:Attribute)
        WHERE attr.minOccurs >= 1
        OPTIONAL MATCH (attr)-[:TYPE_OF]->(attrType)

        // 只获取必需的子元素
        OPTIONAL MATCH (c)-[:HAS_CHILD]->(child:Class)
        WHERE EXISTS((child)-[:HAS_ATTRIBUTE]->(:Attribute {minOccurs: 1}))

        // 只获取必需的继承属性
        OPTIONAL MATCH (c)-[:SUBCLASS_OF*]->(parent:Class)
        OPTIONAL MATCH (parent)-[:HAS_ATTRIBUTE]->(inheritedAttr:Attribute)
        WHERE inheritedAttr.minOccurs >= 1
        OPTIONAL MATCH (inheritedAttr)-[:TYPE_OF]->(inheritedType)

        RETURN c.xml_tag as class_tag,
               c.name as class_name,
               c.annotation as description,
               c.isComplexType as is_complex,
               c.isInnerClassType as is_inner,
               collect(DISTINCT {
                   name: attr.name,
                   xml_tag: attr.xml_tag,
                   xml_wrapper_tag: attr.xml_wrapper_tag,
                   minOccurs: attr.minOccurs,
                   maxOccurs: attr.maxOccurs,
                   isXmlAttr: attr.isXmlAttr,
                   type_xml_tag: attrType.xml_tag,
                   type_name: attrType.name,
                   type_labels: labels(attrType),
                   isPrimitiveType: attrType.isPrimitiveType
               }) as direct_attrs,
               collect(DISTINCT child.xml_tag) as child_elements,
               collect(DISTINCT {
                   name: inheritedAttr.name,
                   xml_tag: inheritedAttr.xml_tag,
                   minOccurs: inheritedAttr.minOccurs
               }) as inherited_attrs
        LIMIT 1
        """

        result = session.run(query, class_name=class_name)
        return result.single()

    def _build_class_schema(
            self,
            session,
            structure: Dict[str, Any],
            paths_tree: Dict[str, Any],
            element_design: Dict[str, Any]
    ) -> Dict[str, Any]:
        """构建类的Schema - 严格筛选版本"""

        properties = {}
        required = []

        # 获取design_elements用于额外筛选
        design_elements = paths_tree.get("design_required", [])

        # 处理所有属性 - 但要严格筛选
        all_attrs = structure["direct_attrs"] + structure["inherited_attrs"]
        for attr in all_attrs:
            if not attr.get("name"):
                continue

            # 严格筛选条件
            min_occurs = attr.get("minOccurs", 0)
            xml_tag = attr.get("xml_tag", "")

            # 只包含：minOccurs>=1 或 在design_elements中
            if min_occurs < 1 and xml_tag not in design_elements:
                continue  # 跳过不必要的属性

            # 构建属性Schema
            prop_schema = self._build_attribute_schema(session, attr, paths_tree, element_design)

            # 确定属性键名
            prop_key = self._get_property_key(attr)

            # 处理xml_wrapper_tag
            if attr.get("xml_wrapper_tag"):
                wrapper_schema = {
                    "type": "object",
                    "properties": {
                        attr["xml_tag"] or attr["name"]: prop_schema
                    }
                }
                properties[attr["xml_wrapper_tag"]] = wrapper_schema
                if min_occurs >= 1:
                    required.append(attr["xml_wrapper_tag"])
            else:
                properties[prop_key] = prop_schema
                if min_occurs >= 1:
                    required.append(prop_key)

        # 处理子元素 - 同样要严格筛选
        for child_tag in structure["child_elements"]:
            if child_tag and (self._should_expand_child(child_tag, element_design) or
                              self._is_required_child(session, child_tag)):
                child_schema = self._build_schema_recursive(
                    session, child_tag, paths_tree, element_design
                )
                properties[child_tag] = child_schema

        # 注入设计要求的结构（保持不变）
        current_tag = structure["class_tag"] or structure["class_name"]
        self._inject_design_structures(
            properties, required, element_design, current_tag
        )

        # 构建最终Schema
        schema = {"type": "object", "properties": properties}

        if required:
            schema["required"] = required

        if structure["description"]:
            schema["description"] = structure["description"]

        return schema

    def _is_required_child(self, session, child_tag: str) -> bool:
        """检查子元素是否是必需的"""
        query = """
        MATCH (parent:Class)-[:HAS_CHILD]->(child:Class)
        WHERE child.xml_tag = $child_tag
        RETURN child.minOccurs as min_occurs
        LIMIT 1
        """

        result = session.run(query, child_tag=child_tag)
        record = result.single()

        if record and record.get("min_occurs", 0) >= 1:
            return True
        return False

    def _build_attribute_schema(
            self,
            session,
            attr: Dict[str, Any],
            paths_tree: Dict[str, Any],
            element_design: Dict[str, Any]
    ) -> Dict[str, Any]:
        """构建属性Schema"""

        # 检查是否应该展开
        if not self._should_expand_attribute(attr, paths_tree, element_design):
            return {"type": "string", "description": "Simplified"}

        # XML属性
        if attr.get("isXmlAttr"):
            return {"type": "string"}

        # 原始类型
        if attr.get("isPrimitiveType"):
            return self._map_primitive_type(attr.get("type_name", "string"))

        # 枚举类型
        type_labels = attr.get("type_labels", [])
        if "Enum" in type_labels:
            enum_values = self._query_enum_values(session, attr.get("type_name"))
            return {
                "type": "string",
                "enum": enum_values if enum_values else ["UNKNOWN"]
            }

        # 复杂类型 - 使用type_name而非type_xml_tag
        type_name = attr.get("type_name")
        if type_name and self.depth_manager.can_go_deeper():
            return self._build_schema_recursive(
                session, type_name, paths_tree, element_design
            )

        # 默认string类型
        return {"type": "string"}

    def _check_termination(self, session, class_name: str) -> Optional[Dict[str, Any]]:
        """检查终止条件 - 修复版本"""

        metrics = schema_monitor.current_metrics

        # 1. 安全深度保护
        if not self.depth_manager.can_go_deeper():
            if metrics:
                metrics.record_termination("max_depth")
            return {"type": "object", "description": f"Max depth reached for {class_name}"}

        # 2. 引用类型终止
        for suffix in self.termination_patterns['ref_suffixes']:
            if class_name.endswith(suffix):
                if metrics:
                    metrics.record_termination("reference_type")
                return {"type": "string", "description": f"Reference to {class_name}"}

        # 3. 标准类型引用
        for prefix in self.termination_patterns['standard_prefixes']:
            if class_name.startswith(prefix):
                if metrics:
                    metrics.record_termination("standard_type")
                return {"type": "string", "description": f"Standard type: {class_name}"}

        # 4. 查询节点类型判断
        node_info = self._query_node_type(session, class_name)
        if not node_info:
            if metrics:
                metrics.record_termination("unknown_type")
            return {"type": "string", "description": f"Unknown type: {class_name}"}

        return self._check_node_termination(node_info, class_name, metrics)

    def _query_node_type(self, session, class_name: str) -> Optional[Dict[str, Any]]:
        """查询节点类型信息 - 使用灵活查询"""
        query = """
        MATCH (n)
        WHERE n.name = $class_name OR n.xml_tag = $class_name
        RETURN labels(n) as labels,
               n.isPrimitiveType as is_primitive,
               n.isComplexType as is_complex,
               n.baseType as base_type,
               exists((n)-[:HAS_CHILD]->()) as has_children,
               exists((n)-[:HAS_ATTRIBUTE]->()) as has_attributes
        LIMIT 1
        """

        result = session.run(query, class_name=class_name)
        return result.single()

    def _check_node_termination(
            self,
            node_info: Dict[str, Any],
            class_name: str,
            metrics
    ) -> Optional[Dict[str, Any]]:
        """检查节点是否应该终止"""

        # 特殊处理：组件类型不应被终止
        if class_name.endswith("-SW-COMPONENT-TYPE") or class_name.endswith("SwComponentType"):
            return None  # 不终止，继续展开

        # 原子类型
        if node_info["is_primitive"]:
            if metrics:
                metrics.record_termination("primitive_type")
            return self._map_primitive_type(node_info.get("base_type", "string"))

        # 枚举类型
        if "Enum" in node_info["labels"]:
            if metrics:
                metrics.record_termination("enum_type")
            # 这里简化处理，实际枚举值需要另外查询
            return {"type": "string", "enum": ["UNKNOWN"]}

        # 简单类型（无子结构）
        if not node_info["has_children"] and not node_info["has_attributes"]:
            if metrics:
                metrics.record_termination("simple_type")
            if node_info.get("base_type"):
                return self._map_primitive_type(node_info["base_type"])
            return {"type": "string"}

        # 不终止，继续展开
        return None

    def _should_expand_attribute(
            self,
            attr: Dict[str, Any],
            paths_tree: Dict[str, Any],
            element_design: Dict[str, Any]
    ) -> bool:
        """判断是否应该展开属性 - 严格版本"""

        # 1. element_design明确需要的
        if attr.get("xml_tag") in paths_tree.get("design_required", []):
            return True

        # 2. minOccurs >= 1的必需属性
        min_occurs = attr.get("minOccurs")
        if min_occurs is not None and min_occurs >= 1:
            return True

        # 3. 其他都不展开
        return False



    def _should_expand_child(
            self,
            child_tag: str,
            element_design: Dict[str, Any]
    ) -> bool:
        """判断是否应该展开子元素"""

        # PORTS相关
        if element_design.get("ports", {}).get("needed"):
            if child_tag in ["PORTS", "P-PORT-PROTOTYPE", "R-PORT-PROTOTYPE"]:
                return True

        # INTERNAL-BEHAVIORS相关
        if element_design.get("internal_behaviors", {}).get("needed"):
            if child_tag in ["INTERNAL-BEHAVIORS", "SWC-INTERNAL-BEHAVIOR",
                             "EVENTS", "RUNNABLES"]:
                return True

        # 默认不展开子元素，除非是必需的
        return False

    def _inject_design_structures(
            self,
            properties: Dict[str, Any],
            required: List[str],
            element_design: Dict[str, Any],
            current_xml_tag: str
    ) -> None:
        """注入element_design要求的结构 - 完全KG驱动版本"""

        # 只在组件根节点注入
        if not (current_xml_tag and current_xml_tag.endswith("-SW-COMPONENT-TYPE")):
            return

        # 必需的基础元素
        if "SHORT-NAME" not in properties:
            properties["SHORT-NAME"] = {"type": "string", "minLength": 1}
            if "SHORT-NAME" not in required:
                required.append("SHORT-NAME")

        if "@UUID" not in properties:
            properties["@UUID"] = {
                "type": "string",
                "pattern": "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
            }

        # 基于element_design动态注入PORTS
        if element_design.get("ports", {}).get("needed"):
            with self.driver.session() as session:
                properties["PORTS"] = self._query_ports_structure(
                    session,
                    element_design.get("ports", {}).get("types", [])
                )

        # 基于element_design动态注入INTERNAL-BEHAVIORS
        if element_design.get("internal_behaviors", {}).get("needed"):
            with self.driver.session() as session:
                properties["INTERNAL-BEHAVIORS"] = self._query_behaviors_structure(
                    session,
                    element_design.get("internal_behaviors", {})
                )

    def _query_runnable_entity_direct(self, session) -> Dict[str, Any]:
        """直接查询RUNNABLE-ENTITY结构"""

        runnable_query = """
        MATCH (runnable:Class)
        WHERE runnable.name = 'RunnableEntity' 
           OR runnable.xml_tag = 'RUNNABLE-ENTITY'

        // 获取所有属性
        OPTIONAL MATCH (runnable)-[:SUBCLASS_OF*0..]->(parent:Class)
        WITH runnable, collect(DISTINCT parent) as parents

        UNWIND (parents + [runnable]) as cls
        OPTIONAL MATCH (cls)-[:HAS_ATTRIBUTE]->(attr:Attribute)

        RETURN runnable.xml_tag as xml_tag,
               collect(DISTINCT {
                   name: attr.name,
                   xml_tag: attr.xml_tag,
                   minOccurs: attr.minOccurs,
                   isXmlAttr: attr.isXmlAttr
               }) as attributes
        """

        result = session.run(runnable_query)
        record = result.single()

        if not record or not record['attributes']:
            return None

        runnable_schema = {
            "type": "object",
            "properties": {},
            "required": []
        }

        for attr in record['attributes']:
            if not attr['name']:
                continue

            attr_key = attr['xml_tag'] or attr['name']
            if attr.get('isXmlAttr'):
                attr_key = f"@{attr_key}"

            runnable_schema["properties"][attr_key] = {"type": "string"}

            if attr.get('minOccurs', 0) >= 1:
                runnable_schema["required"].append(attr_key)

        # 返回包装后的Schema
        return {
            "type": "object",
            "properties": {
                record['xml_tag']: {
                    "type": "array",
                    "items": runnable_schema
                }
            }
        }

    def _query_class_attributes(self, session, class_name: str) -> Dict[str, Any]:
        """通用的类属性查询方法"""

        query = """
        MATCH (c:Class)
        WHERE c.name = $class_name

        // 获取所有属性（包括继承的）
        OPTIONAL MATCH (c)-[:SUBCLASS_OF*0..]->(parent:Class)
        WITH c, collect(DISTINCT parent) as parents

        UNWIND (parents + [c]) as cls
        OPTIONAL MATCH (cls)-[:HAS_ATTRIBUTE]->(attr:Attribute)

        RETURN c.xml_tag as xml_tag,
               collect(DISTINCT {
                   name: attr.name,
                   xml_tag: attr.xml_tag,
                   minOccurs: attr.minOccurs,
                   isXmlAttr: attr.isXmlAttr
               }) as attributes
        """

        result = session.run(query, class_name=class_name)
        record = result.single()

        if not record or not record['attributes']:
            return None

        schema = {
            "type": "object",
            "properties": {},
            "required": []
        }

        for attr in record['attributes']:
            if not attr['name']:
                continue

            attr_key = attr['xml_tag'] or attr['name']
            if attr.get('isXmlAttr'):
                attr_key = f"@{attr_key}"

            schema["properties"][attr_key] = {"type": "string"}

            if attr.get('minOccurs', 0) >= 1:
                schema["required"].append(attr_key)

        return schema if schema["properties"] else None

    def _get_property_key(self, attr: Dict[str, Any]) -> str:
        """获取属性键名 - 处理xml_tag为null的情况"""

        # XML属性用@前缀
        if attr.get("isXmlAttr"):
            xml_tag = attr.get("xml_tag") or attr.get("name", "")
            return f"@{xml_tag}"

        # 普通属性 - 优先使用xml_tag，如果为null则使用name
        return attr.get("xml_tag") or attr.get("name", "")

    def _query_enum_values(self, session, enum_name: str) -> List[str]:
        """查询枚举值"""

        query_start = time.time()
        metrics = schema_monitor.current_metrics

        query = """
        MATCH (e:Enum {name: $enum_name})-[:HAS_LITERAL]->(l:EnumLiteral)
        RETURN collect(l.value) as values
        """

        result = session.run(query, enum_name=enum_name)
        record = result.single()

        if metrics:
            metrics.record_query(time.time() - query_start, success=True)

        return record["values"] if record else []

    def _map_primitive_type(self, kg_type: str) -> Dict[str, Any]:
        """映射基础类型 - 返回Schema而非仅类型字符串"""

        type_mapping = {
            "string": {"type": "string"},
            "integer": {"type": "integer"},
            "int": {"type": "integer"},
            "long": {"type": "integer"},
            "float": {"type": "number"},
            "double": {"type": "number"},
            "decimal": {"type": "number"},
            "boolean": {"type": "boolean"},
            "bool": {"type": "boolean"},
            "dateTime": {"type": "string", "format": "date-time"},
            "date": {"type": "string", "format": "date"},
            "time": {"type": "string", "format": "time"}
        }

        return type_mapping.get(kg_type, {"type": "string"})

    def _count_properties(self, schema: Dict[str, Any]) -> int:
        """递归计算Schema中的属性总数"""
        count = 0

        if isinstance(schema, dict):
            if "properties" in schema:
                count += len(schema["properties"])
                for prop in schema["properties"].values():
                    count += self._count_properties(prop)
            elif "items" in schema:
                count += self._count_properties(schema["items"])

        return count

    def _calculate_depth(self, schema: Dict[str, Any], current_depth: int = 0) -> int:
        """计算Schema的最大深度"""
        if not isinstance(schema, dict):
            return current_depth

        max_depth = current_depth

        if "properties" in schema:
            for prop in schema["properties"].values():
                depth = self._calculate_depth(prop, current_depth + 1)
                max_depth = max(max_depth, depth)
        elif "items" in schema:
            depth = self._calculate_depth(schema["items"], current_depth + 1)
            max_depth = max(max_depth, depth)

        return max_depth

    def generate_batch_schema(self, component_plans: List[Dict[str, Any]]) -> Dict[str, Any]:
        """为组件批次生成Schema - 复用generate_multi_component_schema"""

        # 直接调用多组件生成方法，自动处理相同类型的Schema
        return self.generate_multi_component_schema(component_plans)

    def query_constraints_for_elements(self, element_types: List[str]) -> List[str]:
        """查询元素约束规则 - 使用灵活查询"""

        if not self.driver:
            raise KGQueryError("Neo4j连接未建立，无法查询约束规则")

        try:
            with self.driver.session() as session:
                constraints = []

                for element_type in element_types:
                    # 使用灵活查询
                    query = """
                    MATCH (c:Class)-[:HAS_CONSTRAINT]->(constraint:Constraint)
                    WHERE c.name = $element_type OR c.xml_tag = $element_type
                    RETURN constraint.description as description
                    """

                    result = session.run(query, element_type=element_type)
                    for record in result:
                        if record["description"]:
                            constraints.append(record["description"])

                # 添加基础约束
                constraints.extend([
                    "所有UUID必须符合标准格式",
                    "SHORT-NAME必须符合AUTOSAR命名规范",
                    "引用路径必须正确且可解析"
                ])

                return list(set(constraints))  # 去重

        except Exception as e:
            if CONFIG.debug_mode:
                print(f"[DEBUG] 约束查询失败: {e}")
            raise KGQueryError(f"约束规则查询失败: {str(e)}")

    def _add_component_specific_elements(
            self,
            properties: Dict[str, Any],
            required: List[str],
            component_type: str
    ) -> None:
        """添加组件类型特定的必需元素 - 修复Neo4j语法"""

        if not self.driver:
            return

        with self.driver.session() as session:
            # 修复后的查询：使用正确的Neo4j语法
            query = """
            MATCH (c:Class)
            WHERE c.name = $component_type OR c.xml_tag = $component_type
            OPTIONAL MATCH (c)-[:SUBCLASS_OF*0..]->(parent:Class)
            WITH c, collect(DISTINCT parent) as parents

            // 获取所有类（包括自身和父类）的属性
            UNWIND (parents + [c]) as cls
            OPTIONAL MATCH (cls)-[:HAS_ATTRIBUTE]->(attr:Attribute)
            WHERE attr.minOccurs >= 1 
              AND NOT attr.xml_tag IN ['SHORT-NAME', 'UUID']
              AND NOT attr.xml_tag IN $existing_props

            RETURN collect(DISTINCT {
                tag: attr.xml_tag,
                name: attr.name,
                type: attr.type,
                description: attr.annotation,
                isXmlAttr: attr.isXmlAttr
            }) as required_attrs
            """

            existing_props = list(properties.keys())
            result = session.run(query,
                                 component_type=component_type,
                                 existing_props=existing_props)
            record = result.single()

            if record and record["required_attrs"]:
                for attr in record["required_attrs"]:
                    attr_tag = attr["tag"] or attr["name"]
                    if not attr_tag:
                        continue

                    attr_key = f"@{attr_tag}" if attr.get("isXmlAttr") else attr_tag

                    if attr_key not in properties:
                        if attr.get("type") == "boolean":
                            properties[attr_key] = {"type": "boolean"}
                        elif attr.get("type") in ["integer", "int"]:
                            properties[attr_key] = {"type": "integer"}
                        else:
                            properties[attr_key] = {"type": "string"}

                        if attr.get("description"):
                            properties[attr_key]["description"] = attr["description"]

                        if attr_key not in required:
                            required.append(attr_key)

    def clear_cache(self, cache_level: str = "all"):
        """清理缓存"""

        if cache_level in ["request", "all"]:
            if self.request_cache is not None:
                self.request_cache.clear()
            self.depth_manager.reset()

        if cache_level in ["application", "all"]:
            self.schema_cache.clear()

        if CONFIG.debug_mode:
            print(f"[DEBUG] 清理了 {cache_level} 级别的缓存")

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""

        return {
            "request_cache_size": len(self.request_cache) if self.request_cache else 0,
            "schema_cache": self.schema_cache.get_stats(),
            "current_depth": self.depth_manager.get_depth(),
            "max_safety_depth": self.max_safety_depth
        }

    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()


# 全局查询引擎实例
query_engine = DynamicQueryEngine()