"""tools/observation/derived/ — Derived Metrics Pure Functions。

Pure Function discipline:
- 输入: Frozen 数据结构
- 输出: 数值（metric）或 Snapshot
- 无副作用、无 I/O、无 Runtime 状态修改
- 不 import Runtime 写模块
"""
from tools.observation.derived.latency import execution_latency_ms
from tools.observation.derived.cancellation_propagation import (
    cancellation_propagation_ms,
)
from tools.observation.derived.deadline_accuracy import deadline_error_ms
from tools.observation.derived.event_throughput import event_throughput
from tools.observation.derived.registry_footprint import registry_footprint

__all__ = [
    "execution_latency_ms",
    "cancellation_propagation_ms",
    "deadline_error_ms",
    "event_throughput",
    "registry_footprint",
]
