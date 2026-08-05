"""utils/monitoring.py - Schema生成性能监控"""
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List

from ..config import CONFIG


@dataclass
class SchemaGenerationMetrics:
    """Schema生成指标"""
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None

    # 组件指标
    total_components: int = 0
    components_processed: int = 0
    component_timings: Dict[str, float] = field(default_factory=dict)

    # 查询指标
    total_kg_queries: int = 0
    failed_queries: int = 0
    query_timings: List[float] = field(default_factory=list)

    # Schema指标
    max_schema_depth: int = 0
    total_properties: int = 0
    schemas_generated: int = 0
    required_paths_count: int = 0

    # 缓存指标
    cache_hits: int = 0
    cache_misses: int = 0
    type_reuses: int = 0

    # 终止指标
    termination_reasons: Dict[str, int] = field(default_factory=dict)

    def record_component(self, comp_name: str, duration: float):
        """记录组件处理"""
        self.components_processed += 1
        self.component_timings[comp_name] = duration

    def record_query(self, duration: float, success: bool = True):
        """记录查询"""
        self.total_kg_queries += 1
        self.query_timings.append(duration)
        if not success:
            self.failed_queries += 1

    def record_cache_hit(self, cache_type: str = "type"):
        """记录缓存命中"""
        self.cache_hits += 1
        if cache_type == "type":
            self.type_reuses += 1

    def record_cache_miss(self):
        """记录缓存未命中"""
        self.cache_misses += 1

    def record_schema_properties(self, properties_count: int):
        """记录Schema属性数"""
        self.total_properties += properties_count
        self.schemas_generated += 1

    def record_termination(self, reason: str):
        """记录终止原因"""
        self.termination_reasons[reason] = self.termination_reasons.get(reason, 0) + 1

    def record_cache_access(self, hit: bool):
        """记录缓存访问"""
        if hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1

    def finalize(self) -> Dict[str, Any]:
        """完成并返回指标"""
        self.end_time = time.time()
        duration = self.end_time - self.start_time

        # 计算平均值
        avg_query_time = sum(self.query_timings) / len(self.query_timings) if self.query_timings else 0
        avg_component_time = sum(self.component_timings.values()) / len(
            self.component_timings) if self.component_timings else 0
        cache_hit_rate = self.cache_hits / max(self.cache_hits + self.cache_misses, 1)

        return {
            "summary": {
                "total_duration_seconds": round(duration, 3),
                "components_processed": self.components_processed,
                "schemas_generated": self.schemas_generated,
                "type_reuse_count": self.type_reuses,
                "cache_hit_rate": f"{cache_hit_rate:.1%}"
            },
            "performance": {
                "avg_component_time": round(avg_component_time, 3),
                "avg_query_time": round(avg_query_time, 3),
                "total_queries": self.total_kg_queries,
                "failed_queries": self.failed_queries
            },
            "schema_stats": {
                "total_properties": self.total_properties,
                "avg_properties_per_schema": self.total_properties // max(self.schemas_generated, 1),
                "max_depth": self.max_schema_depth,
                "required_paths": self.required_paths_count
            },
            "cache_stats": {
                "hits": self.cache_hits,
                "misses": self.cache_misses,
                "hit_rate": f"{cache_hit_rate:.1%}",
                "type_reuses": self.type_reuses
            },
            "termination_distribution": self.termination_reasons,
            "component_details": self.component_timings
        }


class SchemaGenerationMonitor:
    """Schema生成监控器"""

    def __init__(self):
        self.current_metrics: Optional[SchemaGenerationMetrics] = None
        self.history: List[Dict[str, Any]] = []
        self.enabled = CONFIG.debug_mode  # 根据调试模式决定是否启用

    @contextmanager
    def monitor(self, operation_name: str = "schema_generation"):
        """监控上下文管理器"""
        if not self.enabled:
            yield None
            return

        metrics = SchemaGenerationMetrics()
        self.current_metrics = metrics

        try:
            if CONFIG.debug_mode:
                print(f"\n[Monitor] Starting {operation_name}...")
            yield metrics
        finally:
            results = metrics.finalize()
            self.history.append(results)

            if CONFIG.debug_mode:
                self._print_metrics(results)

            self.current_metrics = None

    def start_monitoring(self) -> Optional[SchemaGenerationMetrics]:
        """开始监控"""
        if not self.enabled:
            return None
        self.current_metrics = SchemaGenerationMetrics()
        return self.current_metrics

    def end_monitoring(self) -> Optional[Dict[str, Any]]:
        """结束监控"""
        if not self.current_metrics:
            return None

        metrics = self.current_metrics.finalize()
        self.history.append(metrics)

        if CONFIG.debug_mode:
            self._print_metrics(metrics)

        self.current_metrics = None
        return metrics

    def _print_metrics(self, metrics: Dict[str, Any]):
        """打印性能指标"""
        print("\n" + "=" * 60)
        print("📊 Schema Generation Performance Metrics")
        print("=" * 60)

        summary = metrics["summary"]
        print(f"\n📈 Summary:")
        print(f"  ⏱️  Total Duration: {summary['total_duration_seconds']}s")
        print(f"  📦 Components Processed: {summary['components_processed']}")
        print(f"  📋 Schemas Generated: {summary['schemas_generated']}")
        print(f"  ♻️  Type Reuses: {summary['type_reuse_count']}")
        print(f"  💾 Cache Hit Rate: {summary['cache_hit_rate']}")

        perf = metrics["performance"]
        print(f"\n⚡ Performance:")
        print(f"  🔍 Total Queries: {perf['total_queries']}")
        print(f"  ⏱️  Avg Query Time: {perf['avg_query_time']}s")
        print(f"  ⏱️  Avg Component Time: {perf['avg_component_time']}s")

        schema_stats = metrics["schema_stats"]
        print(f"\n📊 Schema Statistics:")
        print(f"  📝 Total Properties: {schema_stats['total_properties']}")
        print(f"  📏 Avg Properties/Schema: {schema_stats['avg_properties_per_schema']}")
        print(f"  🏔️  Max Depth: {schema_stats['max_depth']}")

        # 终止原因分布
        if metrics.get("termination_distribution"):
            print(f"\n🛑 Termination Reasons:")
            for reason, count in metrics["termination_distribution"].items():
                print(f"  - {reason}: {count}")

        # 组件详细时间（只显示最慢的3个）
        if metrics["component_details"]:
            sorted_components = sorted(
                metrics["component_details"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
            print(f"\n🐌 Slowest Components:")
            for comp_name, timing in sorted_components:
                print(f"  - {comp_name}: {timing:.3f}s")

        print("=" * 60 + "\n")

    def get_last_metrics(self) -> Optional[Dict[str, Any]]:
        """获取最后一次监控结果"""
        return self.history[-1] if self.history else None

    def clear_history(self):
        """清空历史记录"""
        self.history.clear()


# 全局监控器实例
schema_monitor = SchemaGenerationMonitor()