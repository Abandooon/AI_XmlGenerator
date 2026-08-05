"""core/dependency_analyzer.py - 简化的依赖分析器

优化为支持大规模单批生成，仅在必要时提供分批建议
"""
from dataclasses import dataclass
from typing import Dict, List, Any, Set

from ..config import CONFIG


@dataclass
class ComponentDependency:
    """组件依赖信息"""
    component_id: str
    component_name: str
    depends_on: Set[str]
    depended_by: Set[str]
    complexity: str
    component_type: str


class DependencyAnalyzer:
    """简化的依赖分析器 - 优化版"""

    def __init__(self):
        """初始化分析器"""
        # 简化的组件类型优先级（仅用于超大规模分批）
        self.component_type_priority = {
            "COMPLEX-DEVICE-DRIVER-SW-COMPONENT-TYPE": 1,
            "ECU-ABSTRACTION-SW-COMPONENT-TYPE": 2,
            "SENSOR-ACTUATOR-SW-COMPONENT-TYPE": 3,
            "PARAMETER-SW-COMPONENT-TYPE": 4,
            "NV-BLOCK-SW-COMPONENT-TYPE": 5,
            "SERVICE-SW-COMPONENT-TYPE": 6,
            "SERVICE-PROXY-SW-COMPONENT-TYPE": 7,
            "APPLICATION-SW-COMPONENT-TYPE": 8,
            "COMPOSITION-SW-COMPONENT-TYPE": 9,
        }

    def should_use_batch_generation(
        self,
        component_plans: List[Dict[str, Any]]
    ) -> bool:
        """判断是否需要分批生成"""

        component_count = len(component_plans)

        # 基于配置的阈值判断
        if component_count <= CONFIG.generation.single_batch_threshold:
            return False

        # 计算总复杂度
        if CONFIG.batch_optimization.enable_intelligent_grouping:
            total_complexity = self._calculate_total_complexity(component_plans)
            max_complexity = CONFIG.batch_optimization.max_complexity_per_batch

            # 如果总复杂度在单批容量内，仍使用单批
            if total_complexity <= max_complexity * 1.5:  # 给予50%的容差
                if CONFIG.debug_mode:
                    print(f"[DEBUG] 总复杂度{total_complexity}在容量内，使用单批生成")
                return False

        return True

    def analyze_and_batch(
        self,
        component_plans: List[Dict[str, Any]],
        interface_plans: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """分析并创建批次 - 简化版"""

        component_count = len(component_plans)

        if CONFIG.debug_mode:
            print(f"[DEBUG] 分析{component_count}个组件")

        # 优先返回单批
        if not self.should_use_batch_generation(component_plans):
            return [{
                "batch_idx": 0,
                "batch_type": "unified",
                "description": f"统一生成所有{component_count}个组件",
                "components": component_plans,
                "dependencies": [],
                "optimization_hint": "single_batch_optimal"
            }]

        # 仅在超大规模时进行智能分批
        return self._create_optimized_batches(component_plans, interface_plans)

    def _calculate_total_complexity(
        self,
        component_plans: List[Dict[str, Any]]
    ) -> int:
        """计算总复杂度"""

        weights = CONFIG.batch_optimization.component_complexity_weights
        total = 0

        for comp in component_plans:
            complexity = comp.get("estimated_complexity", "Medium")
            weight = weights.get(complexity.upper(), weights.get("MEDIUM", 3))
            total += weight

        return total

    def _create_optimized_batches(
        self,
        component_plans: List[Dict[str, Any]],
        interface_plans: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """创建优化的批次 - 最小化批次数量"""

        batches = []
        max_batch_size = CONFIG.generation.max_batch_size
        max_complexity = CONFIG.batch_optimization.max_complexity_per_batch

        # 基于复杂度和大小的智能分组
        current_batch = []
        current_complexity = 0

        # 按类型优先级排序（保持一定的逻辑顺序）
        sorted_components = sorted(
            component_plans,
            key=lambda c: (
                self.component_type_priority.get(c.get("type", ""), 99),
                c.get("estimated_complexity", "Medium")
            )
        )

        for comp in sorted_components:
            comp_complexity = self._get_component_complexity(comp)

            # 检查是否需要新批次
            needs_new_batch = (
                len(current_batch) >= max_batch_size or
                current_complexity + comp_complexity > max_complexity
            )

            if needs_new_batch and current_batch:
                # 保存当前批次
                batches.append(self._create_batch_info(
                    current_batch,
                    len(batches),
                    self._determine_batch_type(current_batch)
                ))
                current_batch = []
                current_complexity = 0

            current_batch.append(comp)
            current_complexity += comp_complexity

        # 添加最后一个批次
        if current_batch:
            batches.append(self._create_batch_info(
                current_batch,
                len(batches),
                self._determine_batch_type(current_batch)
            ))

        if CONFIG.debug_mode:
            print(f"[DEBUG] 创建了{len(batches)}个批次")
            for batch in batches:
                print(f"[DEBUG] 批次{batch['batch_idx']}: {len(batch['components'])}个组件")

        return batches

    def _get_component_complexity(self, component: Dict[str, Any]) -> int:
        """获取组件复杂度权重"""

        complexity = component.get("estimated_complexity", "Medium")
        weights = CONFIG.batch_optimization.component_complexity_weights

        return weights.get(complexity.upper(), weights.get("MEDIUM", 3))

    def _create_batch_info(
        self,
        components: List[Dict[str, Any]],
        batch_idx: int,
        batch_type: str
    ) -> Dict[str, Any]:
        """创建批次信息"""

        return {
            "batch_idx": batch_idx,
            "batch_type": batch_type,
            "description": f"批次{batch_idx + 1}: {len(components)}个{batch_type}组件",
            "components": components,
            "dependencies": list(range(batch_idx)),  # 依赖前面所有批次
            "complexity_score": sum(self._get_component_complexity(c) for c in components),
            "optimization_hint": "batch_required_for_scale"
        }

    def _determine_batch_type(self, components: List[Dict[str, Any]]) -> str:
        """确定批次类型"""

        # 统计组件类型
        type_counts = {}
        for comp in components:
            comp_type = comp.get("type", "APPLICATION-SW-COMPONENT-TYPE")
            type_counts[comp_type] = type_counts.get(comp_type, 0) + 1

        # 找出主要类型
        if type_counts:
            main_type = max(type_counts.items(), key=lambda x: x[1])[0]

            # 简化的类型映射
            if "SENSOR" in main_type or "ACTUATOR" in main_type:
                return "hardware"
            elif "PARAMETER" in main_type or "NV-BLOCK" in main_type:
                return "data"
            elif "SERVICE" in main_type:
                return "service"
            elif "COMPOSITION" in main_type:
                return "composition"
            else:
                return "application"

        return "mixed"

    def get_optimization_suggestions(
        self,
        component_plans: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """获取优化建议"""

        component_count = len(component_plans)
        total_complexity = self._calculate_total_complexity(component_plans)

        suggestions = {
            "component_count": component_count,
            "total_complexity": total_complexity,
            "recommended_strategy": "",
            "estimated_tokens": 0,
            "optimization_tips": []
        }

        # 推荐策略
        if component_count <= 10:
            suggestions["recommended_strategy"] = "single_batch"
            suggestions["optimization_tips"].append("组件数量适中，建议单批生成")
        elif component_count <= CONFIG.generation.single_batch_threshold:
            suggestions["recommended_strategy"] = "single_batch_extended"
            suggestions["optimization_tips"].append(f"利用长上下文，可一次生成{component_count}个组件")
        else:
            suggestions["recommended_strategy"] = "intelligent_batch"
            suggestions["optimization_tips"].append("超大规模系统，建议智能分批")

            # 计算建议的批次数
            batch_count = (total_complexity // CONFIG.batch_optimization.max_complexity_per_batch) + 1
            suggestions["optimization_tips"].append(f"建议分为{batch_count}个批次")

        # 估算Token使用
        suggestions["estimated_tokens"] = self._estimate_token_usage(component_plans)

        return suggestions

    def _estimate_token_usage(self, component_plans: List[Dict[str, Any]]) -> int:
        """估算Token使用量"""

        # 简单估算：每个组件约2000-5000 tokens
        base_tokens_per_component = 3500

        # 根据复杂度调整
        total_tokens = 0
        for comp in component_plans:
            complexity = comp.get("estimated_complexity", "Medium")
            multiplier = {"Simple": 0.7, "Medium": 1.0, "Complex": 1.5}.get(complexity, 1.0)
            total_tokens += int(base_tokens_per_component * multiplier)

        # 添加prompt和schema的开销
        overhead = len(component_plans) * 500 + 5000  # 基础开销

        return total_tokens + overhead


# 全局依赖分析器实例
dependency_analyzer = DependencyAnalyzer()