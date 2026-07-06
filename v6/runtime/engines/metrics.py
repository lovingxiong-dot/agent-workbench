"""v6/runtime/engines/metrics.py — MetricsEngine：指标采集、聚合、告警。

设计来源：V4 agent_engine/engines/metrics_engine.py（提取核心逻辑）。

职责：读取 ctx.metadata["metric_records"]，写入 ctx.metrics。
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional

from v6.runtime.engines.interfaces import Engine, IMetricsEngine


class MetricsEngine(IMetricsEngine):
    """指标引擎：内存存储，支持 avg/sum/max/min/latest 聚合与阈值订阅。"""

    def __init__(self) -> None:
        self._store: Dict[str, Dict[str, Dict]] = defaultdict(
            lambda: defaultdict(lambda: {"values": [], "tags": {}})
        )
        self._subscribers: Dict[str, list] = {}

    async def run(self, ctx: "RuntimeContext") -> "RuntimeContext":
        """从 ctx.metadata['metric_records'] 记录指标，结果写入 ctx.metrics。"""
        records = ctx.metadata.get("metric_records", [])
        if isinstance(records, list):
            for record in records:
                if isinstance(record, dict):
                    self.record(
                        namespace=record.get("namespace", "default"),
                        name=record.get("name", "unknown"),
                        value=record.get("value"),
                        tags=record.get("tags"),
                    )

        ctx.metrics = self.snapshot()
        return ctx

    def record(
        self,
        namespace: str,
        name: str,
        value: Any,
        tags: Optional[Dict[str, Any]] = None,
    ) -> None:
        """记录指标并触发阈值告警。"""
        entry = self._store[namespace][name]
        entry["values"].append(value)
        if tags:
            entry["tags"].update(tags)

        for threshold, callback in self._subscribers.get(f"{namespace}.{name}", []):
            try:
                if isinstance(value, (int, float)) and value > threshold:
                    callback(value, threshold)
            except Exception:
                pass

    def get(self, namespace: str, name: str, aggregation: str = "avg") -> Any:
        """查询聚合指标。"""
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

    def subscribe(
        self, metric_name: str, threshold: float, callback: Callable
    ) -> None:
        """订阅指标阈值告警。"""
        if metric_name not in self._subscribers:
            self._subscribers[metric_name] = []
        self._subscribers[metric_name].append((threshold, callback))

    def snapshot(self) -> Dict[str, Any]:
        """返回当前指标快照。"""
        result: Dict[str, Any] = {}
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
        """清空指标（测试隔离用）。"""
        self._store.clear()
        self._subscribers.clear()
