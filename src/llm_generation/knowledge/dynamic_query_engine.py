"""knowledge/dynamic_query_engine.py - 动态KG查询引擎

按需查询Neo4j知识图谱，获取组件和接口的详细信息，动态生成JSON Schema
"""
import json
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
from ..config import CONFIG
from ..utils.exceptions import KGQueryError

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


class DynamicQueryEngine:
    def __init__(self):
        """初始化查询引擎"""
        self.config = CONFIG.knowledge_graph
        self.driver = None
        self.query_cache = {}
        self.max_schema_depth = CONFIG.knowledge_graph.max_schema_depth  # 修正：正确访问配置
        self.visited_classes = set()

        if NEO4J_AVAILABLE:
            self._init_neo4j_connection()

    def _query_xml_structure_from_neo4j(self, component_types: List[str]) -> Dict[str, ComponentSchema]:
        """从Neo4j查询XML结构 - 基于节点表设计"""
        schemas = {}

        with self.driver.session() as session:
            for comp_type in component_types:
                try:
                    # 重置访问记录
                    self.visited_classes.clear()

                    # 递归构建完整的XML结构
                    xml_structure = self._build_recursive_xml_structure(
                        session, comp_type, depth=0
                    )

                    if xml_structure:
                        # 查询约束
                        constraints = self._query_constraints_for_class(session, comp_type)

                        # 分析必需和可选元素
                        required_elements, optional_elements = self._analyze_element_requirements(
                            session, comp_type
                        )

                        schemas[comp_type] = ComponentSchema(
                            component_type=comp_type,
                            xml_structure=xml_structure,
                            required_elements=required_elements,
                            optional_elements=optional_elements,
                            constraints=constraints
                        )

                except Exception as e:
                    print(f"[WARN] 查询{comp_type}结构失败: {e}")
                    continue

        return schemas

    def _build_recursive_xml_structure(
            self,
            session,
            class_xml_tag: str,
            depth: int = 0,
            parent_path: str = ""
    ) -> Dict[str, Any]:
        """递归构建XML结构，基于KG节点表"""

        # 深度限制
        if depth >= self.max_schema_depth:
            return {"type": "object", "description": f"深度限制({self.max_schema_depth})"}

        # 防止循环引用
        path_key = f"{parent_path}/{class_xml_tag}"
        if path_key in self.visited_classes:
            return {"type": "object", "description": "循环引用"}

        self.visited_classes.add(path_key)

        try:
            # 查询类及其属性和子元素
            query = """
            MATCH (c:Class)
            WHERE c.xml_tag = $xml_tag OR c.name = $xml_tag

            // 查询属性
            OPTIONAL MATCH (c)-[:HAS_ATTRIBUTE]->(a:Attribute)

            // 查询子类/子元素
            OPTIONAL MATCH (c)-[:HAS_CHILD]->(child:Class)

            // 查询类型引用
            OPTIONAL MATCH (a)-[:TYPE_OF]->(type:Class)
            OPTIONAL MATCH (a)-[:TYPE_OF]->(enum:Enum)

            RETURN c.xml_tag as class_tag,
                   c.xml_wrapper_tag as wrapper_tag,
                   c.annotation as class_annotation,

                   collect(DISTINCT {
                       name: a.name,
                       xml_tag: a.xml_tag,
                       xml_wrapper_tag: a.xml_wrapper_tag,
                       type: a.type,
                       min_occurs: a.minOccurs,
                       max_occurs: a.maxOccurs,
                       is_xml_attr: a.isXmlAttr,
                       description: a.description,
                       type_class: type.xml_tag,
                       type_enum: enum.name
                   }) as attributes,

                   collect(DISTINCT {
                       xml_tag: child.xml_tag,
                       wrapper_tag: child.xml_wrapper_tag,
                       annotation: child.annotation
                   }) as child_elements
            """

            result = session.run(query, xml_tag=class_xml_tag)
            record = result.single()

            if not record:
                return {"type": "object", "description": f"未找到类: {class_xml_tag}"}

            properties = {}
            required = []

            # 处理属性
            for attr in record["attributes"]:
                if not attr["name"]:
                    continue

                prop_schema = self._build_attribute_schema(
                    session, attr, depth + 1, path_key
                )

                # 确定属性键名
                prop_key = self._get_property_key(attr)
                properties[prop_key] = prop_schema

                # 判断是否必需
                if self._is_attribute_required(attr):
                    required.append(prop_key)

            # 处理子元素
            for child in record["child_elements"]:
                if not child["xml_tag"]:
                    continue

                child_schema = self._build_recursive_xml_structure(
                    session, child["xml_tag"], depth + 1, path_key
                )

                # 处理wrapper标签
                child_key = child["xml_tag"]
                if child["wrapper_tag"]:
                    # 有wrapper的情况，创建嵌套结构
                    wrapper_schema = {
                        "type": "object",
                        "properties": {
                            child["xml_tag"]: child_schema
                        }
                    }
                    properties[child["wrapper_tag"]] = wrapper_schema
                else:
                    properties[child_key] = child_schema

            schema = {
                "type": "object",
                "properties": properties
            }

            if required:
                schema["required"] = required

            if record["class_annotation"]:
                schema["description"] = record["class_annotation"]

            return schema

        except Exception as e:
            print(f"[WARN] 构建{class_xml_tag}结构失败: {e}")
            return {"type": "object", "description": f"构建失败: {str(e)}"}

        finally:
            # 移除访问记录
            self.visited_classes.discard(path_key)

    # dynamic_query_engine.py 修正
    def _init_neo4j_connection(self):
        """初始化Neo4j连接"""
        try:
            # 添加连接调试信息
            if CONFIG.debug_mode:
                print(f"[DEBUG] 连接Neo4j: {self.config.neo4j_uri}")
                print(f"[DEBUG] 用户名: {self.config.neo4j_user}")

            self.driver = GraphDatabase.driver(
                self.config.neo4j_uri,
                auth=(self.config.neo4j_user, self.config.neo4j_password),
                # 添加Neo4j Aura云服务的连接配置
                encrypted=True,  # 强制加密连接
                trust="TRUST_SYSTEM_CA_SIGNED_CERTIFICATES",  # 信任系统CA证书
                max_connection_lifetime=30 * 60,  # 30分钟连接生命周期
                max_connection_pool_size=50,  # 连接池大小
                connection_acquisition_timeout=60  # 连接获取超时60秒
            )

            # 测试连接 - 增强测试
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

    def _build_attribute_schema(
            self,
            session,
            attr: Dict[str, Any],
            depth: int,
            parent_path: str
    ) -> Dict[str, Any]:
        """构建属性Schema"""

        schema = {
            "description": attr.get("description", "")
        }

        # 处理类型
        if attr.get("type_class"):
            # 引用其他类类型，递归构建
            if depth < self.max_schema_depth:
                schema.update(self._build_recursive_xml_structure(
                    session, attr["type_class"], depth, parent_path
                ))
            else:
                schema["type"] = "object"
                schema["description"] += " (类型引用，深度限制)"

        elif attr.get("type_enum"):
            # 枚举类型
            enum_values = self._query_enum_values(session, attr["type_enum"])
            schema["type"] = "string"
            schema["enum"] = enum_values

        else:
            # 基础类型
            schema["type"] = self._map_primitive_type(attr.get("type", "string"))

        # 处理数组
        if attr.get("max_occurs") and (attr["max_occurs"] == -1 or attr["max_occurs"] > 1):
            schema = {
                "type": "array",
                "items": schema
            }

        return schema

    def _get_property_key(self, attr: Dict[str, Any]) -> str:
        """获取属性键名"""

        # XML属性用@前缀
        if attr.get("is_xml_attr"):
            return f"@{attr['xml_tag'] or attr['name']}"

        # 有xml_wrapper_tag的情况
        if attr.get("xml_wrapper_tag"):
            return attr["xml_wrapper_tag"]

        # 普通情况
        return attr.get("xml_tag") or attr["name"]

    def _is_attribute_required(self, attr: Dict[str, Any]) -> bool:
        """判断属性是否必需"""
        min_occurs = attr.get("min_occurs", 0)
        return min_occurs is not None and min_occurs > 0

    def _query_enum_values(self, session, enum_name: str) -> List[str]:
        """查询枚举值"""
        query = """
        MATCH (e:Enum {name: $enum_name})-[:HAS_LITERAL]->(l:EnumLiteral)
        RETURN collect(l.value) as values
        """

        result = session.run(query, enum_name=enum_name)
        record = result.single()

        return record["values"] if record else []

    def _map_primitive_type(self, kg_type: str) -> str:
        """映射基础类型"""
        type_mapping = {
            "string": "string",
            "integer": "integer",
            "int": "integer",
            "long": "integer",
            "float": "number",
            "double": "number",
            "decimal": "number",
            "boolean": "boolean",
            "bool": "boolean",
            "dateTime": "string",
            "date": "string",
            "time": "string"
        }
        return type_mapping.get(kg_type, "string")

    def _analyze_element_requirements(
            self,
            session,
            class_xml_tag: str
    ) -> Tuple[List[str], List[str]]:
        """分析必需和可选元素"""

        required_elements = []
        optional_elements = []

        query = """
        MATCH (c:Class {xml_tag: $xml_tag})-[:HAS_ATTRIBUTE]->(a:Attribute)
        WHERE a.minOccurs > 0
        RETURN collect(a.xml_tag) as required_attrs

        UNION

        MATCH (c:Class {xml_tag: $xml_tag})-[:HAS_ATTRIBUTE]->(a:Attribute)  
        WHERE a.minOccurs = 0 OR a.minOccurs IS NULL
        RETURN collect(a.xml_tag) as optional_attrs
        """

        # 简化查询，分别获取必需和可选
        req_query = """
        MATCH (c:Class {xml_tag: $xml_tag})-[:HAS_ATTRIBUTE]->(a:Attribute)
        WHERE a.minOccurs > 0
        RETURN collect(COALESCE(a.xml_tag, a.name)) as elements
        """

        opt_query = """
        MATCH (c:Class {xml_tag: $xml_tag})-[:HAS_ATTRIBUTE]->(a:Attribute)
        WHERE a.minOccurs = 0 OR a.minOccurs IS NULL  
        RETURN collect(COALESCE(a.xml_tag, a.name)) as elements
        """

        try:
            req_result = session.run(req_query, xml_tag=class_xml_tag)
            req_record = req_result.single()
            if req_record:
                required_elements = [e for e in req_record["elements"] if e]

            opt_result = session.run(opt_query, xml_tag=class_xml_tag)
            opt_record = opt_result.single()
            if opt_record:
                optional_elements = [e for e in opt_record["elements"] if e]

        except Exception as e:
            print(f"[WARN] 分析{class_xml_tag}元素需求失败: {e}")

        return required_elements, optional_elements

    def get_schema_depth_stats(self) -> Dict[str, Any]:
        """获取Schema深度统计信息"""
        return {
            "max_depth": self.max_schema_depth,
            "visited_classes_count": len(self.visited_classes),
            "cache_size": len(self.query_cache)
        }

# 全局查询引擎实例
query_engine = DynamicQueryEngine()