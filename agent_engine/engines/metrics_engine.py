"""
Metrics Engine — 指标采集、聚合、查询

从 MetricsCollector 提取。内存存储，支持 avg/sum/max/min/latest 聚合。
闭环：InferenceEngine/ContextEngine 上报 → MetricsEngine 聚合 → PolicyEngine 决策
"""
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional
from .interfaces import IMetricsEngine


class MetricsEngine(IMetricsEngine):
    """指标引擎：采集、聚合、订阅"""

    def __init__(self):
        self._store: Dict[str, Dict[str, Dict]] = defaultdict(
            lambda: defaultdict(lambda: {"values": [], "tags": {}})
        )
        self._subscribers: Dict[str, List[tuple]] = {}

    def record(
        self,
        namespace: str,
        name: str,
        value: Any,
        tags: Optional[Dict[str, Any]] = None,
    ) -> None:
        entry = self._store[namespace][name]
        entry["values"].append(value)
        if tags:
            entry["tags"].update(tags)

        # 检查告警订阅
        for threshold, callback in self._subscribers.get(f"{namespace}.{name}", []):
            try:
                if isinstance(value, (int, float)) and value > threshold:
                    callback(value, threshold)
            except Exception:
                pass

    def get(self, namespace: str, name: str, aggregation: str = "avg") -> Any:
        values = self._store[namespace][name]["values"]
        if not values:
            return 0 if aggregation in ("avg", "sum", "max", "min") else None

        nums = [v for v in values if isinstance(v, (int, float))]
        if not nums:
            return values[-1] if values else None

        if aggregation == "avg":
            return sum(nums) / len(nums)
        elif aggregation == "sum":
            return sum(nums)
        elif aggregation == "max":
            return max(nums)
        elif aggregation == "min":
            return min(nums)
        elif aggregation == "latest":
            return values[-1]
        return values[-1]

    def subscribe(self, metric_name: str, threshold: float, callback: Callable) -> None:
        if metric_name not in self._subscribers:
            self._subscribers[metric_name] = []
        self._subscribers[metric_name].append((threshold, callback))

    def snapshot(self) -> Dict[str, Any]:
        """返回当前指标快照"""
        result = {}
        for ns, names in self._store.items():
            result[ns] = {}
            for name, entry in names.items():
                result[ns][name] = {
                    "count": len(entry["values"]),
                    "latest": entry["values"][-1] if entry["values"] else None,
                    "tags": dict(entry["tags"]),
                }
        return result

    def clear(self) -> None:
        self._store.clear()
