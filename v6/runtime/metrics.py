"""v6/runtime/metrics.py — RuntimeMetrics：运行时统计信息容器。

设计来源：Runtime Kernel 演进方向及 docs/v6/SPEC.md 第 8 节。

核心原则：
- RuntimeMetrics 保存 Statistics（token/latency/tool_time/cost/retry 等），不属于 Facts。
- 当前挂载在 RuntimeContext.metrics 上，未来可平滑迁移到 RuntimeTask.metrics。
- 线程安全；所有写操作受锁保护；读取返回深拷贝快照。
"""
from __future__ import annotations

import copy
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class RuntimeMetrics:
    """Runtime Task 的统计信息容器。

    字段覆盖 LLM 推理、工具执行、记忆检索、队列等待等常见指标。
    非预定义指标可通过 custom 字典扩展，不影响序列化。
    """

    tokens: int = 0
    latency_ms: float = 0.0
    tool_time_ms: float = 0.0
    memory_hits: int = 0
    cache_hits: int = 0
    cost: float = 0.0
    retry: int = 0
    queue_time_ms: float = 0.0

    # 自定义指标扩展容器
    custom: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._lock = threading.Lock()

    def record(self, **kwargs: Any) -> None:
        """原子地记录一组指标；预定义字段直接覆盖，其余落入 custom。"""
        with self._lock:
            for key, value in kwargs.items():
                if key == "custom":
                    self.custom.update(value)
                elif hasattr(self, key) and not key.startswith("_"):
                    setattr(self, key, value)
                else:
                    self.custom[key] = value

    def accumulate(self, **kwargs: Any) -> None:
        """原子地累加数值型指标；非数值型落入 custom。"""
        with self._lock:
            for key, value in kwargs.items():
                if key == "custom":
                    self.custom.update(value)
                    continue
                current = getattr(self, key, 0)
                try:
                    setattr(self, key, current + value)
                except TypeError:
                    self.custom[key] = value

    def mark_queue_time(self, start: float) -> None:
        """根据起始时间戳计算并记录排队耗时（秒 → 毫秒）。"""
        with self._lock:
            self.queue_time_ms = (time.time() - start) * 1000

    def snapshot(self) -> Dict[str, Any]:
        """返回深拷贝快照，用于 Checkpoint / Replay / 上报。"""
        with self._lock:
            return self._make_snapshot()

    def to_dict(self) -> Dict[str, Any]:
        """语义同 snapshot，兼容旧 dict 接口。"""
        return self.snapshot()

    def reset(self) -> None:
        """清空所有统计。"""
        with self._lock:
            self.tokens = 0
            self.latency_ms = 0.0
            self.tool_time_ms = 0.0
            self.memory_hits = 0
            self.cache_hits = 0
            self.cost = 0.0
            self.retry = 0
            self.queue_time_ms = 0.0
            self.custom.clear()

    def _make_snapshot(self) -> Dict[str, Any]:
        return {
            "tokens": self.tokens,
            "latency_ms": self.latency_ms,
            "tool_time_ms": self.tool_time_ms,
            "memory_hits": self.memory_hits,
            "cache_hits": self.cache_hits,
            "cost": self.cost,
            "retry": self.retry,
            "queue_time_ms": self.queue_time_ms,
            "custom": copy.deepcopy(self.custom),
        }
