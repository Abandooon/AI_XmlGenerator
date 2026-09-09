"""core/reference_resolver.py - 引用解析器

使用配置化的语义模式，避免硬编码关键词
"""
import re
from typing import Dict, List, Any, Optional

from ..config import CONFIG
from ..utils.exceptions import ValidationError


class ReferenceResolver:
    """引用解析器 - 配置化语义模式"""

    def __init__(self):
        """初始化解析器"""
        self.semantic_patterns = self._load_semantic_patterns_from_config()
        self.resolution_cache: Dict[str, str] = {}

    def _load_semantic_patterns_from_config(self) -> List[Dict[str, Any]]:
        """从配置加载语义模式"""
        try:
            return CONFIG.semantic_resolution.patterns
        except AttributeError:
            raise ValidationError("配置文件中缺少语义解析模式定义")

    def resolve_all_references(
        self,
        generated_components: Dict[str, Any],
        interface_registry: Dict[str, Any]
    ) -> Dict[str, Any]:
        """解析所有组件中的引用"""

        if CONFIG.debug_mode:
            print(f"[DEBUG] 开始解析引用，组件数量: {len(generated_components)}")

        resolved_components = {}

        for comp_name, comp_data in generated_components.items():
            try:
                resolved_comp = self._resolve_component_references(
                    comp_data,
                    generated_components,
                    interface_registry
                )
                resolved_components[comp_name] = resolved_comp

                if CONFIG.debug_mode:
                    print(f"[DEBUG] 完成{comp_name}的引用解析")

            except Exception as e:
                if CONFIG.debug_mode:
                    print(f"[ERROR] 解析{comp_name}引用失败: {e}")
                # 严格模式：引用解析失败时抛出异常
                raise ValidationError(f"组件 {comp_name} 的引用解析失败: {str(e)}")

        return resolved_components

    def _resolve_component_references(
        self,
        component_data: Dict[str, Any],
        all_components: Dict[str, Any],
        interface_registry: Dict[str, Any]
    ) -> Dict[str, Any]:
        """解析单个组件的引用"""

        def resolve_recursive(obj, path=""):
            if isinstance(obj, dict):
                resolved = {}
                for key, value in obj.items():
                    if isinstance(value, str) and self._is_semantic_reference(value):
                        # 解析语义引用
                        resolved_ref = self._resolve_semantic_reference(
                            value, all_components, interface_registry
                        )
                        if resolved_ref is None:
                            raise ValidationError(f"无法解析语义引用: {value} (路径: {path}.{key})")
                        resolved[key] = resolved_ref
                    else:
                        resolved[key] = resolve_recursive(value, f"{path}.{key}")
                return resolved
            elif isinstance(obj, list):
                return [resolve_recursive(item, f"{path}[{i}]") for i, item in enumerate(obj)]
            else:
                return obj

        return resolve_recursive(component_data)

    def _is_semantic_reference(self, text: str) -> bool:
        """判断是否为语义引用 - 基于配置的标识符"""

        # 排除已经是路径的情况
        if text.startswith('/'):
            return False

        # 检查配置的语义标识符
        semantic_identifiers = CONFIG.semantic_resolution.identifiers

        return any(identifier in text for identifier in semantic_identifiers)

    def _resolve_semantic_reference(
        self,
        semantic_text: str,
        all_components: Dict[str, Any],
        interface_registry: Dict[str, Any]
    ) -> Optional[str]:
        """解析语义引用 - 基于配置模式"""

        # 检查缓存
        if semantic_text in self.resolution_cache:
            return self.resolution_cache[semantic_text]

        # 尝试配置的模式匹配
        for pattern_info in self.semantic_patterns:
            match = re.search(pattern_info["pattern"], semantic_text)
            if match:
                resolved = self._apply_pattern_template(
                    pattern_info, match, all_components, interface_registry
                )
                if resolved:
                    self.resolution_cache[semantic_text] = resolved
                    return resolved

        if CONFIG.debug_mode:
            print(f"[WARN] 无法解析语义引用: {semantic_text}")

        return None

    def _apply_pattern_template(
        self,
        pattern_info: Dict[str, Any],
        match: re.Match,
        all_components: Dict[str, Any],
        interface_registry: Dict[str, Any]
    ) -> Optional[str]:
        """应用模式模板"""

        template = pattern_info["template"]
        groups = match.groups()

        if len(groups) >= 2:
            component_desc = groups[0].strip()
            target_desc = groups[1].strip()

            # 查找匹配的组件
            component_name = self._find_component_by_description(
                component_desc, all_components
            )

            if component_name:
                # 生成路径
                path = template.format(
                    component=component_name,
                    target=target_desc
                )
                return path

        return None

    def _find_component_by_description(
        self,
        description: str,
        all_components: Dict[str, Any]
    ) -> Optional[str]:
        """根据描述查找组件 - 使用配置的映射规则"""

        desc_lower = description.lower()

        # 直接名称匹配
        for comp_name in all_components.keys():
            if comp_name.lower() == desc_lower:
                return comp_name

        # 部分匹配
        for comp_name in all_components.keys():
            if desc_lower in comp_name.lower() or comp_name.lower() in desc_lower:
                return comp_name

        # 使用配置的功能映射
        function_mappings = CONFIG.semantic_resolution.function_mappings

        for pattern, candidates in function_mappings.items():
            if pattern in desc_lower:
                for comp_name in all_components.keys():
                    comp_lower = comp_name.lower()
                    if any(candidate in comp_lower for candidate in candidates):
                        return comp_name

        return None

    # 移除所有硬编码的关键词匹配方法
    # 移除 _extract_keywords, _calculate_match_score 等方法

    def get_resolution_statistics(self) -> Dict[str, Any]:
        """获取解析统计信息"""
        return {
            "cached_resolutions": len(self.resolution_cache),
            "patterns_loaded": len(self.semantic_patterns),
            "cache_entries": list(self.resolution_cache.keys())[:10]
        }

    def clear_cache(self):
        """清理缓存"""
        self.resolution_cache.clear()

# 全局引用解析器实例
reference_resolver = ReferenceResolver()