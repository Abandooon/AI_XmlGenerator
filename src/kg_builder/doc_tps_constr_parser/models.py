from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Union

@dataclass
class Entity:
    """识别出的实体信息"""
    text: str
    type: str  # CLASS, ATTRIBUTE, ENUM_VALUE等
    start: int
    end: int
    parent: Optional[str] = None  # 父类或所属类
    metadata: Dict[str, Any] = field(default_factory=dict)  # 来自元数据的附加信息

@dataclass
class ConstraintRaw:
    """从文档中提取的原始约束信息"""
    id: str  # 约束ID如constr_1299
    type: str  # 约束类型如constr或TPS
    title: str  # 约束标题
    body: str  # 约束主体文本
    explanation: Optional[str] = None  # 附加解释文本
    reference_id: Optional[str] = None  # 引用的标识符如RS_SWCT_03200

@dataclass
class ConditionExpression:
    """条件表达式"""
    class_name: str
    attribute: str
    operation: str  # ==, !=, >, <, etc.
    value: Any
    scope: Optional[str] = None  # 作用范围，如"any", "all"

@dataclass
class ProhibitionExpression:
    """禁止性表达式"""
    class_name: str
    attribute: str
    operation: str  # shall_not_be_set, shall_not_equal, etc.
    scope: Optional[str] = None  # 作用范围，如"any", "all"

@dataclass
class NonOverlapExpression:
    """不重叠表达式"""
    attributes: List[Dict[str, str]]  # 不应重叠的属性列表，每项包含class和attribute
    scope: str  # 作用范围，如"within_one_ModeDeclarationGroup"

@dataclass
class PermissionExpression:
    """许可表达式"""
    attributes: List[Dict[str, str]]  # 允许的属性列表，每项包含class和attribute
    permission: str  # 许可类型，如"arbitrary_values"
    conditions: List[str] = field(default_factory=list)  # 前提条件，如其他约束ID

@dataclass
class ConstraintStructured:
    """结构化后的约束信息"""
    id: str  # 约束ID
    type: str  # 约束类型，如ConditionalProhibition
    title: str  # 约束标题
    body: str  # 约束原文
    source_id: str  # 源约束ID
    explanation: Optional[str] = None  # 附加解释
    reference_id: Optional[str] = None  # 引用ID
    condition: Optional[Union[ConditionExpression, List[ConditionExpression]]] = None
    prohibition: Optional[List[ProhibitionExpression]] = None
    non_overlapping: Optional[NonOverlapExpression] = None
    permission: Optional[PermissionExpression] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)  # 额外数据