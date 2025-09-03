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
        self.request_cache = {} if cache_config.enable_request_cache else None

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
        """生成多组件Schema - 带性能监控版本"""

        if not self.driver:
            raise KGQueryError("Neo4j连接未建立，无法生成Schema")

        # 使用监控上下文
        with schema_monitor.monitor("multi_component_schema_generation") as metrics:
            schemas = {}
            type_schema_cache = {}  # 类型级别的缓存

            # 记录总组件数
            if metrics:
                metrics.total_components = len(component_plans)

            with self.driver.session() as session:
                for comp_plan in component_plans:
                    comp_start_time = time.time() if metrics else None

                    comp_type = comp_plan.get("type", "")
                    comp_name = comp_plan.get("name", "")

                    if not comp_type:
                        raise KGQueryError(f"组件{comp_name}缺少类型定义")

                    # 复用相同类型的Schema
                    if comp_type in type_schema_cache:
                        schemas[comp_name] = type_schema_cache[comp_type]

                        # 记录缓存命中
                        if metrics:
                            metrics.record_cache_hit("type")
                            metrics.record_component(comp_name, time.time() - comp_start_time)

                        if CONFIG.debug_mode:
                            print(f"  ♻️ Reusing schema for {comp_name} (type: {comp_type})")
                        continue

                    # 记录缓存未命中
                    if metrics:
                        metrics.record_cache_miss()

                    # 基于element_design生成新的Schema
                    element_design = comp_plan.get("element_design", {})

                    # 包装Schema生成以记录查询
                    comp_schema = self._build_component_schema_with_design_monitored(
                        session,
                        comp_type,
                        element_design,
                        metrics
                    )

                    if not comp_schema or not comp_schema.get("properties"):
                        raise KGQueryError(f"无法为组件类型{comp_type}生成有效Schema")

                    # 记录Schema统计
                    if metrics:
                        properties_count = self._count_properties(comp_schema)
                        metrics.record_schema_properties(properties_count)
                        metrics.record_component(comp_name, time.time() - comp_start_time)

                    # 缓存该类型的Schema
                    type_schema_cache[comp_type] = comp_schema
                    schemas[comp_name] = comp_schema

                    if CONFIG.debug_mode:
                        print(f"  ✅ Generated schema for {comp_name} (type: {comp_type})")

            if not schemas:
                raise KGQueryError("未能生成任何组件Schema")

            result = {
                "type": "object",
                "properties": schemas,
                "required": list(schemas.keys()),
                "description": f"包含{len(component_plans)}个组件的Schema定义"
            }

            # 记录最终统计
            if metrics:
                # 计算最大深度
                max_depth = 0
                for schema in schemas.values():
                    depth = self._calculate_depth(schema)
                    max_depth = max(max_depth, depth)
                metrics.max_schema_depth = max_depth

            return result

    def _build_component_schema_with_design_monitored(
            self,
            session,
            component_type: str,
            element_design: Dict[str, Any],
            metrics: Optional['SchemaGenerationMetrics'] = None
    ) -> Dict[str, Any]:
        """带监控的Schema生成"""

        query_start = time.time() if metrics else None

        try:
            # 调用原有方法
            schema = self._build_component_schema_with_design(
                session,
                component_type,
                element_design
            )

            # 记录查询成功
            if metrics and query_start:
                metrics.record_query(time.time() - query_start, success=True)

            return schema

        except Exception as e:
            # 记录查询失败
            if metrics and query_start:
                metrics.record_query(time.time() - query_start, success=False)
            raise

    def _build_component_schema_with_design(
            self,
            session,
            component_type: str,
            element_design: Dict[str, Any]
    ) -> Dict[str, Any]:
        """基于element_design构建组件Schema"""

        # 检查应用级缓存
        cache_key = f"{component_type}:{json.dumps(element_design, sort_keys=True)}"
        cached_schema = self.schema_cache.get(cache_key)
        if cached_schema:
            return cached_schema

        # 清空请求级缓存和重置深度管理器
        if self.request_cache is not None:
            self.request_cache.clear()
        self.depth_manager.reset()

        # 构建必需路径树
        required_paths = self._build_required_paths_tree(
            session,
            component_type,
            element_design
        )

        # 记录必需路径数
        metrics = schema_monitor.current_metrics
        if metrics:
            metrics.required_paths_count += len(required_paths.get("required", []))

        # 生成Schema
        schema = self._build_schema_from_paths(
            session,
            component_type,
            required_paths,
            element_design
        )

        # 缓存结果
        self.schema_cache.set(cache_key, schema)

        return schema

    def _build_required_paths_tree(
            self,
            session,
            component_type: str,
            element_design: Dict[str, Any]
    ) -> Dict[str, Any]:
        """构建必需元素路径树 - 修复版本：使用灵活查询"""

        query_start = time.time()
        metrics = schema_monitor.current_metrics

        # 【修复】：使用灵活查询，同时匹配name和xml_tag
        query = """
        // 获取组件及其所有父类 - 修复：使用灵活查询
        MATCH (c:Class)
        WHERE c.name = $component_type OR c.xml_tag = $component_type
        OPTIONAL MATCH (c)-[:SUBCLASS_OF*0..]->(parent:Class)
        WITH c, collect(DISTINCT parent) as parents

        // 获取所有相关属性
        UNWIND (parents + [c]) as cls
        OPTIONAL MATCH (cls)-[:HAS_ATTRIBUTE]->(attr:Attribute)
        WHERE attr.minOccurs >= 1 OR attr.xml_tag IN $design_elements

        // 获取属性的类型信息
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

        # 从element_design提取需要的元素
        design_elements = self._extract_design_elements(element_design)

        # 优化查询
        query, params = self.query_optimizer.optimize_query(
            query,
            {
                "component_type": component_type,
                "design_elements": design_elements
            }
        )

        result = session.run(query, **params)

        # 记录查询时间
        if metrics:
            metrics.record_query(time.time() - query_start, success=True)

        # 构建路径树
        paths_tree = self._organize_paths_tree(result, design_elements)

        return paths_tree

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
                if attr["minOccurs"] and attr["minOccurs"] >= 1:
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
        """查询类的结构信息 - 使用灵活的查询策略"""
        query = """
        MATCH (c:Class)
        WHERE c.name = $class_name OR c.xml_tag = $class_name

        // 获取直接属性
        OPTIONAL MATCH (c)-[:HAS_ATTRIBUTE]->(attr:Attribute)
        OPTIONAL MATCH (attr)-[:TYPE_OF]->(attrType)

        // 获取子元素
        OPTIONAL MATCH (c)-[:HAS_CHILD]->(child:Class)

        // 获取继承的属性
        OPTIONAL MATCH (c)-[:SUBCLASS_OF*]->(parent:Class)
        OPTIONAL MATCH (parent)-[:HAS_ATTRIBUTE]->(inheritedAttr:Attribute)
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
        """构建类的Schema"""

        properties = {}
        required = []

        # 处理所有属性
        all_attrs = structure["direct_attrs"] + structure["inherited_attrs"]
        for attr in all_attrs:
            if not attr.get("name"):
                continue

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
                if attr.get("minOccurs", 0) >= 1:
                    required.append(attr["xml_wrapper_tag"])
            else:
                properties[prop_key] = prop_schema
                if attr.get("minOccurs", 0) >= 1:
                    required.append(prop_key)

        # 处理子元素
        for child_tag in structure["child_elements"]:
            if child_tag and self._should_expand_child(child_tag, element_design):
                child_schema = self._build_schema_recursive(
                    session, child_tag, paths_tree, element_design
                )
                properties[child_tag] = child_schema

        # 注入设计要求的结构
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
        """判断是否应该展开属性"""

        # element_design明确需要的
        if attr.get("xml_tag") in paths_tree.get("design_required", []):
            return True

        # minOccurs >= 1的必需属性
        if attr.get("minOccurs", 0) >= 1:
            return True

        # 引用类型不展开
        attr_name = attr.get("name", "")
        for suffix in self.termination_patterns['ref_suffixes']:
            if attr_name.endswith(suffix):
                return False

        # 原始类型不展开
        if attr.get("isPrimitiveType"):
            return False

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
        """注入element_design要求的结构 - 修复版本"""

        # 如果是组件根节点，添加必需的顶级结构
        if current_xml_tag and current_xml_tag.endswith("-SW-COMPONENT-TYPE"):
            # SHORT-NAME始终必需（AUTOSAR标准）
            if "SHORT-NAME" not in properties:
                properties["SHORT-NAME"] = {"type": "string", "minLength": 1}
                if "SHORT-NAME" not in required:
                    required.append("SHORT-NAME")

            # UUID建议添加（AUTOSAR标准）
            if "@UUID" not in properties:
                properties["@UUID"] = {
                    "type": "string",
                    "pattern": "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
                }

            # PORTS结构 - 动态查询
            if element_design.get("ports", {}).get("needed") and "PORTS" not in properties:
                properties["PORTS"] = self._get_ports_schema()

            # INTERNAL-BEHAVIORS结构 - 动态查询
            if element_design.get("internal_behaviors", {}).get("needed") and "INTERNAL-BEHAVIORS" not in properties:
                properties["INTERNAL-BEHAVIORS"] = self._get_internal_behaviors_schema()

            # 查询并添加其他组件特定的必需元素
            self._add_component_specific_elements(properties, required, current_xml_tag)

    def _get_ports_schema(self) -> Dict[str, Any]:
        """获取端口Schema - 修复查询版本"""
        if not self.driver:
            raise KGQueryError("Neo4j连接未建立，无法生成端口Schema")

        with self.driver.session() as session:
            # 查询PORTS的子元素结构
            query = """
            MATCH (ports:Class {name: 'Ports'})
            OPTIONAL MATCH (ports)-[:HAS_CHILD]->(port_type:Class)
            WHERE port_type.xml_tag IN ['P-PORT-PROTOTYPE', 'R-PORT-PROTOTYPE', 
                                         'PR-PORT-PROTOTYPE', 'PORT-PROTOTYPE']
            OPTIONAL MATCH (port_type)-[:HAS_ATTRIBUTE]->(attr:Attribute)
            WHERE attr.minOccurs >= 1
            RETURN port_type.xml_tag as port_tag,
                   port_type.name as port_name,
                   port_type.annotation as description,
                   collect(DISTINCT {
                       tag: attr.xml_tag,
                       name: attr.name,
                       required: attr.minOccurs >= 1,
                       type: attr.type
                   }) as required_attrs
            """

            result = session.run(query)

            ports_schema = {
                "type": "object",
                "properties": {}
            }

            has_ports = False
            for record in result:
                port_tag = record["port_tag"]
                if not port_tag:
                    continue

                has_ports = True

                # 构建每个端口类型的Schema
                port_item_schema = {
                    "type": "object",
                    "properties": {
                        "SHORT-NAME": {"type": "string", "minLength": 1}
                    },
                    "required": ["SHORT-NAME"]
                }

                # 添加特定端口类型的属性
                if port_tag == "P-PORT-PROTOTYPE":
                    port_item_schema["properties"]["PROVIDED-INTERFACE-TREF"] = {
                        "type": "string",
                        "description": "提供接口的引用路径"
                    }
                elif port_tag == "R-PORT-PROTOTYPE":
                    port_item_schema["properties"]["REQUIRED-INTERFACE-TREF"] = {
                        "type": "string",
                        "description": "需求接口的引用路径"
                    }
                    port_item_schema["properties"]["REQUIRED-COM-SPECS"] = {
                        "type": "object"
                    }
                elif port_tag == "PR-PORT-PROTOTYPE":
                    port_item_schema["properties"]["PROVIDED-REQUIRED-INTERFACE-TREF"] = {
                        "type": "string",
                        "description": "双向端口接口引用"
                    }

                # 添加从KG查询到的其他必需属性
                for attr in record["required_attrs"]:
                    attr_tag = attr["tag"] or attr["name"]
                    if attr_tag and attr_tag not in port_item_schema["properties"]:
                        port_item_schema["properties"][attr_tag] = {
                            "type": "string"
                        }
                        if attr["required"] and attr_tag not in port_item_schema["required"]:
                            port_item_schema["required"].append(attr_tag)

                # 端口可以是数组
                ports_schema["properties"][port_tag] = {
                    "type": "array",
                    "items": port_item_schema
                }

            # 如果查询不到端口结构，提供默认的端口Schema
            if not has_ports:
                ports_schema["properties"]["P-PORT-PROTOTYPE"] = {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "SHORT-NAME": {"type": "string", "minLength": 1},
                            "PROVIDED-INTERFACE-TREF": {"type": "string"}
                        },
                        "required": ["SHORT-NAME"]
                    }
                }
                ports_schema["properties"]["R-PORT-PROTOTYPE"] = {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "SHORT-NAME": {"type": "string", "minLength": 1},
                            "REQUIRED-INTERFACE-TREF": {"type": "string"}
                        },
                        "required": ["SHORT-NAME"]
                    }
                }

            return ports_schema

    def _get_internal_behaviors_schema(self) -> Dict[str, Any]:
        """获取内部行为Schema - 修复查询版本"""
        if not self.driver:
            raise KGQueryError("Neo4j连接未建立，无法生成内部行为Schema")

        with self.driver.session() as session:
            # 查询SWC-INTERNAL-BEHAVIOR的结构
            query = """
            MATCH (ib:Class)
            WHERE ib.name = 'SwcInternalBehavior' OR ib.xml_tag = 'SWC-INTERNAL-BEHAVIOR'
            OPTIONAL MATCH (ib)-[:HAS_ATTRIBUTE]->(attr:Attribute)
            OPTIONAL MATCH (ib)-[:HAS_CHILD]->(child:Class)
            WHERE child.xml_tag IN ['EVENTS', 'RUNNABLES', 'EXCLUSIVE-AREAS', 
                                    'INTER-RUNNABLE-VARIABLES', 'EXPLICIT-INTER-RUNNABLE-VARIABLES',
                                    'PORT-API-OPTIONS', 'INCLUDED-DATA-TYPE-SETS']

            // 查询EVENTS的子类型
            OPTIONAL MATCH (events:Class)
            WHERE events.name = 'Events' OR events.xml_tag = 'EVENTS'
            OPTIONAL MATCH (events)-[:HAS_CHILD]->(event_type:Class)

            // 查询RUNNABLES的结构
            OPTIONAL MATCH (runnables:Class)
            WHERE runnables.name = 'Runnables' OR runnables.xml_tag = 'RUNNABLES'
            OPTIONAL MATCH (runnables)-[:HAS_CHILD]->(runnable:Class)

            RETURN collect(DISTINCT attr.xml_tag) as attributes,
                   collect(DISTINCT child.xml_tag) as child_elements,
                   collect(DISTINCT event_type.xml_tag) as event_types,
                   collect(DISTINCT runnable.xml_tag) as runnable_types
            """

            result = session.run(query)
            record = result.single()

            # 构建基础结构
            behavior_schema = {
                "type": "object",
                "properties": {
                    "SHORT-NAME": {"type": "string", "minLength": 1}
                },
                "required": ["SHORT-NAME"]
            }

            # 添加EVENTS结构
            if not record or "TIMING-EVENT" not in (record.get("event_types") or []):
                # 提供默认的EVENTS结构
                behavior_schema["properties"]["EVENTS"] = {
                    "type": "object",
                    "properties": {
                        "TIMING-EVENT": {
                            "type": "array",
                            "items": {"type": "object"}
                        }
                    }
                }
            else:
                events_properties = {}
                for event_type in record["event_types"]:
                    if event_type:
                        events_properties[event_type] = {
                            "type": "array",
                            "items": {"type": "object"}
                        }

                if events_properties:
                    behavior_schema["properties"]["EVENTS"] = {
                        "type": "object",
                        "properties": events_properties
                    }

            # 添加RUNNABLES结构
            if not record or "RUNNABLE-ENTITY" not in (record.get("runnable_types") or []):
                # 提供默认的RUNNABLES结构
                behavior_schema["properties"]["RUNNABLES"] = {
                    "type": "object",
                    "properties": {
                        "RUNNABLE-ENTITY": {
                            "type": "array",
                            "items": {"type": "object"}
                        }
                    }
                }
            else:
                runnable_types = record["runnable_types"]
                if runnable_types:
                    behavior_schema["properties"]["RUNNABLES"] = {
                        "type": "object",
                        "properties": {
                            runnable_type: {
                                "type": "array",
                                "items": {"type": "object"}
                            }
                            for runnable_type in runnable_types if runnable_type
                        }
                    }

            # 添加其他子元素
            if record:
                for child in record["child_elements"]:
                    if child and child not in ["EVENTS", "RUNNABLES"]:
                        behavior_schema["properties"][child] = {
                            "type": "object"
                        }

            # 包装在INTERNAL-BEHAVIORS中
            return {
                "type": "object",
                "properties": {
                    "SWC-INTERNAL-BEHAVIOR": behavior_schema
                }
            }

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
        """添加组件类型特定的必需元素 - 使用灵活查询"""

        if not self.driver:
            return  # 如果没有连接，跳过特定元素

        with self.driver.session() as session:
            # 查询特定组件类型的必需元素
            query = """
            MATCH (c:Class)
            WHERE c.name = $component_type OR c.xml_tag = $component_type
            OPTIONAL MATCH (c)-[:HAS_ATTRIBUTE]->(attr:Attribute)
            WHERE attr.minOccurs >= 1 
              AND attr.xml_tag NOT IN ['SHORT-NAME', 'UUID']
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
                        # 根据类型添加适当的Schema
                        if attr.get("type") == "boolean":
                            properties[attr_key] = {"type": "boolean"}
                        elif attr.get("type") in ["integer", "int"]:
                            properties[attr_key] = {"type": "integer"}
                        else:
                            properties[attr_key] = {"type": "string"}

                        if attr.get("description"):
                            properties[attr_key]["description"] = attr["description"]

                        # 添加到required列表
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