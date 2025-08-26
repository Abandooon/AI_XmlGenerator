"""knowledge/constraint_engine.py - 约束规则引擎

从KG查询和管理AUTOSAR约束规则，移除验证逻辑，专注于约束信息提供
"""
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
from ..config import CONFIG

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False

class ConstraintType(Enum):
    """约束类型枚举"""
    MODEL_OCL = "ModelOCL"         # OCL模型约束
    DATA_TYPE = "DataType"         # 数据类型约束
    PRODUCTION = "Production"      # 生产约束
    DOCUMENTATION = "Documentation"  # 文档约束

@dataclass
class ConstraintInfo:
    """约束信息"""
    constraint_id: str
    constraint_type: ConstraintType
    expression: str
    title: str
    description: str
    target_elements: List[str]
    is_active: bool

class ConstraintEngine:
    """约束规则引擎"""

    def __init__(self):
        """初始化约束引擎"""
        self.config = CONFIG.knowledge_graph
        self.driver = None
        self.constraint_cache = {}

        # 初始化Neo4j连接
        if NEO4J_AVAILABLE:
            self._init_neo4j_connection()

    # constraint_engine.py 修正
    def _init_neo4j_connection(self):
        """初始化Neo4j连接 - 修复版本"""
        try:
            if CONFIG.debug_mode:
                print(f"[DEBUG] 约束引擎连接Neo4j: {self.config.neo4j_uri}")

            self.driver = GraphDatabase.driver(
                self.config.neo4j_uri,
                auth=(self.config.neo4j_user, self.config.neo4j_password),
                max_connection_lifetime=30 * 60,
                max_connection_pool_size=10,  # 约束引擎使用较小的连接池
                connection_acquisition_timeout=60,
                # 根据URI判断是否需要加密
                encrypted=False if any(
                    x in self.config.neo4j_uri for x in ["localhost", "127.0.0.1", "bolt://"]) else True
            )

            # 测试连接
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                if result.single()["test"] == 1:
                    print("[INFO] 约束引擎Neo4j连接成功")
                else:
                    raise Exception("连接测试失败")

        except Exception as e:
            print(f"[WARN] 约束引擎Neo4j连接失败: {e}，使用模拟约束")
            self.driver = None

    def query_constraints_for_elements(self, element_types: List[str]) -> List[ConstraintInfo]:
        """查询指定元素类型的约束"""

        if not element_types:
            return []

        # 检查缓存
        cache_key = f"constraints:{':'.join(sorted(element_types))}"
        if cache_key in self.constraint_cache:
            return self.constraint_cache[cache_key]

        try:
            if self.driver:
                constraints = self._query_constraints_from_kg(element_types)
            else:
                constraints = self._get_mock_constraints(element_types)

            # 缓存结果
            self.constraint_cache[cache_key] = constraints
            return constraints

        except Exception as e:
            if CONFIG.debug_mode:
                print(f"[DEBUG] 约束查询失败: {e}")
            return self._get_mock_constraints(element_types)

    def _query_constraints_from_kg(self, element_types: List[str]) -> List[ConstraintInfo]:
        """从KG查询约束"""

        constraints = []

        with self.driver.session() as session:
            for element_type in element_types:
                # 查询约束节点
                query = """
                MATCH (e:Class {xml_tag: $element_type})<-[:CONSTRAINS]-(c:Constraint)
                WHERE c.is_active = true OR c.is_active IS NULL
                RETURN c.cid as constraint_id,
                       c.constraint_type as constraint_type,
                       c.id_type as id_type,
                       c.expression as expression,
                       c.title as title,
                       c.scope_path as scope_path,
                       c.targets as targets,
                       c.is_active as is_active,
                       labels(c) as labels
                """

                results = session.run(query, element_type=element_type)

                for record in results:
                    # 解析约束类型
                    constraint_type = self._parse_constraint_type(
                        record.get("constraint_type", ""),
                        record.get("id_type", ""),
                        record.get("labels", [])
                    )

                    # 创建约束信息
                    constraint = ConstraintInfo(
                        constraint_id=record.get("constraint_id", ""),
                        constraint_type=constraint_type,
                        expression=record.get("expression", ""),
                        title=record.get("title", ""),
                        description=record.get("scope_path", ""),
                        target_elements=[element_type],
                        is_active=record.get("is_active", True)
                    )

                    constraints.append(constraint)

        return constraints

    def _parse_constraint_type(self, constraint_type: str, id_type: str, labels: List[str]) -> ConstraintType:
        """解析约束类型"""

        # 优先从labels解析
        for label in labels:
            if label in ["ModelOCL", "DataType", "Production", "Documentation"]:
                try:
                    return ConstraintType(label)
                except ValueError:
                    pass

        # 从constraint_type解析
        if constraint_type:
            if "ocl" in constraint_type.lower():
                return ConstraintType.MODEL_OCL
            elif "datatype" in constraint_type.lower():
                return ConstraintType.DATA_TYPE
            elif "production" in constraint_type.lower():
                return ConstraintType.PRODUCTION
            elif "doc" in constraint_type.lower():
                return ConstraintType.DOCUMENTATION

        # 从id_type解析
        if id_type:
            if "constraint" in id_type.lower():
                return ConstraintType.MODEL_OCL

        # 默认为MODEL_OCL
        return ConstraintType.MODEL_OCL

    def _get_mock_constraints(self, element_types: List[str]) -> List[ConstraintInfo]:
        """获取模拟约束（当KG不可用时）"""

        constraints = []

        for element_type in element_types:
            if element_type == "APPLICATION-SW-COMPONENT-TYPE":
                constraints.extend([
                    ConstraintInfo(
                        constraint_id="ASW_COMP_001",
                        constraint_type=ConstraintType.MODEL_OCL,
                        expression="self.shortName->notEmpty()",
                        title="组件必须有SHORT-NAME",
                        description="应用软件组件必须定义SHORT-NAME属性",
                        target_elements=[element_type],
                        is_active=True
                    ),
                    ConstraintInfo(
                        constraint_id="ASW_COMP_002",
                        constraint_type=ConstraintType.MODEL_OCL,
                        expression="self.ports->size() >= 1",
                        title="组件必须有端口",
                        description="应用软件组件必须至少包含一个端口",
                        target_elements=[element_type],
                        is_active=True
                    ),
                    ConstraintInfo(
                        constraint_id="ASW_COMP_003",
                        constraint_type=ConstraintType.DATA_TYPE,
                        expression="shortName matches '^[A-Za-z][A-Za-z0-9_]*$'",
                        title="命名规范",
                        description="SHORT-NAME必须以字母开头，只包含字母数字下划线",
                        target_elements=[element_type],
                        is_active=True
                    )
                ])

            elif element_type == "P-PORT-PROTOTYPE":
                constraints.extend([
                    ConstraintInfo(
                        constraint_id="PPORT_001",
                        constraint_type=ConstraintType.MODEL_OCL,
                        expression="self.providedInterface->notEmpty()",
                        title="P端口必须引用接口",
                        description="P-PORT-PROTOTYPE必须有PROVIDED-INTERFACE-TREF",
                        target_elements=[element_type],
                        is_active=True
                    )
                ])

            elif element_type == "R-PORT-PROTOTYPE":
                constraints.extend([
                    ConstraintInfo(
                        constraint_id="RPORT_001",
                        constraint_type=ConstraintType.MODEL_OCL,
                        expression="self.requiredInterface->notEmpty()",
                        title="R端口必须引用接口",
                        description="R-PORT-PROTOTYPE必须有REQUIRED-INTERFACE-TREF",
                        target_elements=[element_type],
                        is_active=True
                    )
                ])

            elif element_type == "SWC-INTERNAL-BEHAVIOR":
                constraints.extend([
                    ConstraintInfo(
                        constraint_id="SWC_IB_001",
                        constraint_type=ConstraintType.MODEL_OCL,
                        expression="self.runnable->notEmpty() implies self.events->notEmpty()",
                        title="有Runnable必须有事件",
                        description="如果定义了RUNNABLE-ENTITY，必须定义相应的事件",
                        target_elements=[element_type],
                        is_active=True
                    )
                ])

            elif element_type == "RUNNABLE-ENTITY":
                constraints.extend([
                    ConstraintInfo(
                        constraint_id="RUNNABLE_001",
                        constraint_type=ConstraintType.DATA_TYPE,
                        expression="symbol matches '^[A-Za-z][A-Za-z0-9_]*$'",
                        title="Runnable符号命名",
                        description="SYMBOL必须符合C语言标识符规范",
                        target_elements=[element_type],
                        is_active=True
                    )
                ])

        return constraints

    def generate_constraint_prompt(self, element_types: List[str]) -> str:
        """生成约束相关的提示词"""

        constraints = self.query_constraints_for_elements(element_types)

        if not constraints:
            return "## 约束要求\n遵循AUTOSAR标准规范和XML结构要求。"

        prompt_lines = ["## 约束要求"]
        prompt_lines.append("生成的ARXML必须遵循以下约束规则：")
        prompt_lines.append("")

        # 按约束类型分组
        ocl_constraints = [c for c in constraints if c.constraint_type == ConstraintType.MODEL_OCL]
        data_constraints = [c for c in constraints if c.constraint_type == ConstraintType.DATA_TYPE]

        if ocl_constraints:
            prompt_lines.append("### 🔴 模型约束 (必须满足)")
            for constraint in ocl_constraints:
                prompt_lines.append(f"- **{constraint.title}**: {constraint.description}")
                if constraint.expression:
                    prompt_lines.append(f"  - 约束表达式: `{constraint.expression}`")
            prompt_lines.append("")

        if data_constraints:
            prompt_lines.append("### 🟡 数据类型约束 (建议遵循)")
            for constraint in data_constraints:
                prompt_lines.append(f"- **{constraint.title}**: {constraint.description}")
                if constraint.expression:
                    prompt_lines.append(f"  - 约束表达式: `{constraint.expression}`")
            prompt_lines.append("")

        # 添加通用约束提醒
        prompt_lines.append("### 📋 通用要求")
        prompt_lines.append("- 所有UUID必须唯一且符合格式要求")
        prompt_lines.append("- 引用路径必须正确且一致")
        prompt_lines.append("- 遵循AUTOSAR命名约定")
        prompt_lines.append("- 确保XML结构的完整性")

        return "\n".join(prompt_lines)

    def get_constraint_summary(self, element_types: List[str]) -> Dict[str, Any]:
        """获取约束摘要信息"""

        constraints = self.query_constraints_for_elements(element_types)

        summary = {
            "total_constraints": len(constraints),
            "by_type": {},
            "critical_constraints": [],
            "elements_covered": list(set(element_types))
        }

        # 按类型统计
        for constraint in constraints:
            constraint_type = constraint.constraint_type.value
            summary["by_type"][constraint_type] = summary["by_type"].get(constraint_type, 0) + 1

            # 收集关键约束
            if constraint.constraint_type == ConstraintType.MODEL_OCL and constraint.is_active:
                summary["critical_constraints"].append({
                    "id": constraint.constraint_id,
                    "title": constraint.title,
                    "description": constraint.description
                })

        return summary

    def get_constraints_by_target(self, target_element: str) -> List[ConstraintInfo]:
        """获取特定目标元素的约束"""

        all_constraints = self.query_constraints_for_elements([target_element])
        return [c for c in all_constraints if target_element in c.target_elements]

    def clear_cache(self):
        """清除约束缓存"""
        self.constraint_cache.clear()

    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()

    def get_stats(self) -> Dict[str, Any]:
        """获取约束引擎统计信息"""

        cache_size = len(self.constraint_cache)
        total_constraints = sum(len(constraints) for constraints in self.constraint_cache.values())

        return {
            "cache_entries": cache_size,
            "total_cached_constraints": total_constraints,
            "kg_connected": self.driver is not None,
            "constraint_types": [ct.value for ct in ConstraintType]
        }

# 全局约束引擎实例
constraint_engine = ConstraintEngine()