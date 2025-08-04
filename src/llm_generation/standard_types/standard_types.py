"""knowledge/standard_types.py - 标准类型管理器

从ARXML文件中提取AUTOSAR标准类型信息，供LLM使用
"""
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import xml.etree.ElementTree as ET
from ..config import CONFIG
from ..utils.exceptions import ConfigurationError


@dataclass
class BaseType:
    """SW-BASE-TYPE定义"""
    name: str
    size: int  # bits
    encoding: str
    category: str
    description: str = ""


@dataclass
class ImplementationType:
    """IMPLEMENTATION-DATA-TYPE定义"""
    name: str
    category: str
    base_type_ref: Optional[str] = None
    compu_method_ref: Optional[str] = None
    type_reference_ref: Optional[str] = None
    description: str = ""
    sub_elements: List[Dict[str, Any]] = None


@dataclass
class CompuMethod:
    """COMPU-METHOD定义"""
    name: str
    category: str
    unit_ref: Optional[str] = None
    compu_scales: List[Dict[str, Any]] = None


@dataclass
class Unit:
    """UNIT定义"""
    name: str
    display_name: str
    factor_si_to_unit: float
    offset_si_to_unit: float
    physical_dimension_ref: Optional[str] = None


class StandardTypeManager:
    """标准类型库管理器"""

    def __init__(self, standard_types_path: Optional[Path] = None):
        """初始化标准类型管理器"""
        # 确定标准类型目录路径
        if standard_types_path is None:
            # 默认路径：src/llm_generation/data/standard_types/
            self.types_dir = Path(__file__).parent.parent / "data" / "standard_types"
        else:
            self.types_dir = Path(standard_types_path)

        # 类型存储
        self.base_types: Dict[str, BaseType] = {}
        self.implementation_types: Dict[str, ImplementationType] = {}
        self.compu_methods: Dict[str, CompuMethod] = {}
        self.units: Dict[str, Unit] = {}

        # AUTOSAR命名空间
        self.ns = {'ar': 'http://autosar.org/schema/r4.0'}

        # 加载标准类型
        self._load_all_types()

    def _load_all_types(self):
        """加载所有标准类型文件"""
        if not self.types_dir.exists():
            raise ConfigurationError(f"标准类型目录不存在: {self.types_dir}")

        # 定义要加载的文件及其处理方法
        type_files = {
            "PlatformBase_Types.arxml": self._load_base_types,
            "Platform_Types.arxml": self._load_implementation_types,
            "Standard_Types.arxml": self._load_implementation_types,
            "rba_CUCELCompuMethods_BSWMD.arxml": self._load_compu_methods_and_units
        }

        for filename, loader_func in type_files.items():
            filepath = self.types_dir / filename
            if filepath.exists():
                loader_func(filepath)
                if CONFIG.debug_mode:
                    print(f"[DEBUG] 加载类型文件: {filename}")
            else:
                if CONFIG.debug_mode:
                    print(f"[DEBUG] 类型文件不存在: {filename}")

    def _load_base_types(self, filepath: Path):
        """加载SW-BASE-TYPE定义"""
        tree = ET.parse(filepath)
        root = tree.getroot()

        # 查找所有SW-BASE-TYPE元素
        for base_type in root.findall(".//ar:SW-BASE-TYPE", self.ns):
            name = self._get_text(base_type, "ar:SHORT-NAME")
            if not name:
                continue

            # 提取属性
            size = int(self._get_text(base_type, "ar:BASE-TYPE-SIZE", "0"))
            encoding = self._get_text(base_type, "ar:BASE-TYPE-ENCODING", "NONE")
            category = self._get_text(base_type, "ar:CATEGORY", "FIXED_LENGTH")

            # 提取描述
            desc = self._get_text(base_type, ".//ar:L-4[@L='EN']", "")
            if not desc:
                desc = self._get_text(base_type, ".//ar:L-1[@L='EN']", "")

            self.base_types[name] = BaseType(
                name=name,
                size=size,
                encoding=encoding,
                category=category,
                description=desc
            )

    def _load_implementation_types(self, filepath: Path):
        """加载IMPLEMENTATION-DATA-TYPE定义"""
        tree = ET.parse(filepath)
        root = tree.getroot()

        # 查找所有IMPLEMENTATION-DATA-TYPE元素
        for impl_type in root.findall(".//ar:IMPLEMENTATION-DATA-TYPE", self.ns):
            name = self._get_text(impl_type, "ar:SHORT-NAME")
            if not name:
                continue

            # 提取属性
            category = self._get_text(impl_type, "ar:CATEGORY", "VALUE")

            # 提取描述
            desc = self._get_text(impl_type, ".//ar:L-4[@L='EN']", "")
            if not desc:
                desc = self._get_text(impl_type, ".//ar:L-1[@L='EN']", "")

            # 提取引用
            base_type_ref = self._get_ref(impl_type, ".//ar:BASE-TYPE-REF")
            compu_method_ref = self._get_ref(impl_type, ".//ar:COMPU-METHOD-REF")
            type_ref_ref = self._get_ref(impl_type, ".//ar:IMPLEMENTATION-DATA-TYPE-REF")

            # 处理结构体子元素
            sub_elements = []
            if category == "STRUCTURE":
                for sub_elem in impl_type.findall(".//ar:IMPLEMENTATION-DATA-TYPE-ELEMENT", self.ns):
                    elem_name = self._get_text(sub_elem, "ar:SHORT-NAME")
                    elem_type_ref = self._get_ref(sub_elem, ".//ar:IMPLEMENTATION-DATA-TYPE-REF")
                    if elem_name and elem_type_ref:
                        sub_elements.append({
                            "name": elem_name,
                            "type_ref": elem_type_ref
                        })

            self.implementation_types[name] = ImplementationType(
                name=name,
                category=category,
                base_type_ref=base_type_ref,
                compu_method_ref=compu_method_ref,
                type_reference_ref=type_ref_ref,
                description=desc,
                sub_elements=sub_elements if sub_elements else None
            )

    def _load_compu_methods_and_units(self, filepath: Path):
        """加载COMPU-METHOD和UNIT定义"""
        tree = ET.parse(filepath)
        root = tree.getroot()

        # 加载COMPU-METHOD
        for compu in root.findall(".//ar:COMPU-METHOD", self.ns):
            name = self._get_text(compu, "ar:SHORT-NAME")
            if not name:
                continue

            category = self._get_text(compu, "ar:CATEGORY", "IDENTICAL")
            unit_ref = self._get_ref(compu, "ar:UNIT-REF")

            # 提取COMPU-SCALES
            scales = []
            for scale in compu.findall(".//ar:COMPU-SCALE", self.ns):
                scale_data = {
                    "lower_limit": self._get_text(scale, ".//ar:LOWER-LIMIT", ""),
                    "upper_limit": self._get_text(scale, ".//ar:UPPER-LIMIT", ""),
                    "compu_const": self._get_text(scale, ".//ar:VT", "")
                }
                scales.append(scale_data)

            self.compu_methods[name] = CompuMethod(
                name=name,
                category=category,
                unit_ref=unit_ref,
                compu_scales=scales if scales else None
            )

        # 加载UNIT
        for unit in root.findall(".//ar:UNIT", self.ns):
            name = self._get_text(unit, "ar:SHORT-NAME")
            if not name:
                continue

            self.units[name] = Unit(
                name=name,
                display_name=self._get_text(unit, "ar:DISPLAY-NAME", name),
                factor_si_to_unit=float(self._get_text(unit, "ar:FACTOR-SI-TO-UNIT", "1.0")),
                offset_si_to_unit=float(self._get_text(unit, "ar:OFFSET-SI-TO-UNIT", "0.0")),
                physical_dimension_ref=self._get_ref(unit, "ar:PHYSICAL-DIMENSION-REF")
            )

    def _get_text(self, element, path: str, default: str = "") -> str:
        """获取元素文本内容"""
        elem = element.find(path, self.ns)
        return elem.text if elem is not None and elem.text else default

    def _get_ref(self, element, path: str) -> Optional[str]:
        """获取引用路径"""
        elem = element.find(path, self.ns)
        return elem.text if elem is not None and elem.text else None

    def get_type_context_for_llm(self, filter_categories: List[str] = None) -> str:
        """生成供LLM使用的类型上下文信息"""
        context_lines = ["## AUTOSAR标准类型信息\n"]

        # 基础类型信息
        context_lines.append("### 基础类型 (SW-BASE-TYPE)")
        context_lines.append("这些是AUTOSAR最底层的类型定义：\n")

        for base_type in sorted(self.base_types.values(), key=lambda x: x.name):
            context_lines.append(f"- **{base_type.name}**: {base_type.size}位, 编码={base_type.encoding}")
            if base_type.description:
                context_lines.append(f"  描述: {base_type.description}")

        # 实现类型信息
        context_lines.append("\n### 实现类型 (IMPLEMENTATION-DATA-TYPE)")
        context_lines.append("这些是可以在接口中使用的数据类型：\n")

        # 按类别分组
        by_category = {}
        for impl_type in self.implementation_types.values():
            if filter_categories and impl_type.category not in filter_categories:
                continue
            category = impl_type.category
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(impl_type)

        for category, types in sorted(by_category.items()):
            context_lines.append(f"\n#### {category}类型:")
            for impl_type in sorted(types, key=lambda x: x.name):
                context_lines.append(f"- **{impl_type.name}**")
                if impl_type.description:
                    context_lines.append(f"  描述: {impl_type.description}")
                if impl_type.base_type_ref:
                    base_name = impl_type.base_type_ref.split('/')[-1]
                    context_lines.append(f"  基础类型: {base_name}")
                if impl_type.sub_elements:
                    context_lines.append(f"  包含元素: {len(impl_type.sub_elements)}个")

        # 计算方法信息
        if self.compu_methods:
            context_lines.append("\n### 计算方法 (COMPU-METHOD)")
            context_lines.append("定义了值的转换和枚举：\n")

            for compu in sorted(self.compu_methods.values(), key=lambda x: x.name):
                context_lines.append(f"- **{compu.name}** ({compu.category})")
                if compu.compu_scales:
                    context_lines.append(f"  包含{len(compu.compu_scales)}个转换规则")

        return "\n".join(context_lines)

    def get_type_by_name(self, type_name: str) -> Optional[Dict[str, Any]]:
        """根据名称获取类型信息"""
        # 先查找实现类型
        if type_name in self.implementation_types:
            impl_type = self.implementation_types[type_name]
            return {
                "type": "IMPLEMENTATION-DATA-TYPE",
                "name": impl_type.name,
                "category": impl_type.category,
                "base_type_ref": impl_type.base_type_ref,
                "compu_method_ref": impl_type.compu_method_ref,
                "description": impl_type.description,
                "sub_elements": impl_type.sub_elements
            }

        # 再查找基础类型
        if type_name in self.base_types:
            base_type = self.base_types[type_name]
            return {
                "type": "SW-BASE-TYPE",
                "name": base_type.name,
                "size": base_type.size,
                "encoding": base_type.encoding,
                "category": base_type.category,
                "description": base_type.description
            }

        return None

    def list_available_types(self, category: str = None) -> List[str]:
        """列出可用的类型名称"""
        types = []

        for impl_type in self.implementation_types.values():
            if category is None or impl_type.category == category:
                types.append(impl_type.name)

        return sorted(types)

    def get_stats(self) -> Dict[str, int]:
        """获取类型统计信息"""
        return {
            "base_types": len(self.base_types),
            "implementation_types": len(self.implementation_types),
            "compu_methods": len(self.compu_methods),
            "units": len(self.units)
        }


# 全局标准类型管理器实例
standard_type_manager = StandardTypeManager()