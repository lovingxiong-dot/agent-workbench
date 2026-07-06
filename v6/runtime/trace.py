"""v6/runtime/trace.py — Runtime Trace：记录 Task 执行历史，支持 Replay。

设计来源：docs/v6/SPEC.md 第 4、8 节及 Runtime Task 四对象演进方向。

核心原则：
- RuntimeTrace 只记录事实（History），不保存业务逻辑。
- 每个步骤包含：时间戳、阶段、节点（runtime/engine/service/tool）、动作、载荷摘要。
- Engine / Service / Tool / Runtime 均可向 ctx.trace.add(...) 写入自己负责的步骤。
- RuntimeTrace 与 RuntimeContext 生命周期绑定，随 Task 创建而创建。
- ReplayPlayer 按 trace 步骤重放事件，供调试、审计、可视化使用。
"""
from __future__ import annotations

import copy
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from v6.runtime.enums import TraceEvent
from v6.runtime.event_bus import EventBus


@dataclass
class TraceStep:
    """单次执行步骤。"""

    timestamp: float
    phase: str
    node: str
    action: str
    payload: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """统一把枚举转成字符串存储，保持序列化一致性。"""
        if isinstance(self.phase, Enum):
            self.phase = self.phase.value
        if isinstance(self.node, Enum):
            self.node = self.node.value
        if isinstance(self.action, Enum):
            self.action = self.action.value


class RuntimeTrace:
    """Runtime Task 的执行历史容器。

    线程安全；所有写操作受锁保护；读取返回深拷贝快照。
    """

    def __init__(self) -> None:
        self._steps: List[TraceStep] = []
        self._lock = threading.Lock()

    def add(
        self,
        node: Union[str, Enum],
        action: Union[str, TraceEvent],
        phase: Union[str, Enum] = "",
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        """追加一条执行步骤。

        Args:
            node: 记录主体，如 runtime / engine / service / tool / adapter。
            action: 具体动作，如 start / dispatch / finish / error / emit_chunk。
            phase: 当前阶段，如 inference / memory / tool / policy。
            payload: 附加结构化信息，建议只放摘要（避免过大对象）。
        """
        with self._lock:
            self._steps.append(
                TraceStep(
                    timestamp=time.time(),
                    phase=phase,
                    node=node,
                    action=action,
                    payload=copy.deepcopy(payload) if payload else {},
                )
            )

    def steps(self) -> List[TraceStep]:
        """返回步骤列表深拷贝快照。"""
        with self._lock:
            return copy.deepcopy(self._steps)

    def snapshot(self) -> Dict[str, Any]:
        """序列化为字典。"""
        with self._lock:
            return {
                "steps": [
                    {
                        "timestamp": s.timestamp,
                        "phase": s.phase,
                        "node": s.node,
                        "action": s.action,
                        "payload": copy.deepcopy(s.payload),
                    }
                    for s in self._steps
                ]
            }

    def last(self) -> Optional[TraceStep]:
        """返回最后一步（深拷贝）。"""
        with self._lock:
            if not self._steps:
                return None
            return copy.deepcopy(self._steps[-1])

    def filter(self, node: Optional[str] = None, action: Optional[str] = None) -> List[TraceStep]:
        """按 node 和/或 action 筛选步骤。"""
        with self._lock:
            result = list(self._steps)
        if node is not None:
            result = [s for s in result if s.node == node]
        if action is not None:
            result = [s for s in result if s.action == action]
        return copy.deepcopy(result)

    def clear(self) -> None:
        """清空历史（Replay 或重置时使用）。"""
        with self._lock:
            self._steps.clear()


class ReplayPlayer:
    """基于 RuntimeTrace 的事件回放器。

    当前只重放 node == "engine" 且 action 为 emit_* 的事件步骤，
    后续可扩展为按节点/动作/阶段重放任意步骤。
    """

    def __init__(self, trace: RuntimeTrace, event_bus: EventBus) -> None:
        self._trace = trace
        self._bus = event_bus

    def play(self, task_id: str = "replay") -> None:
        """按 trace 顺序重放事件。"""
        for step in self._trace.steps():
            if step.node != "engine":
                continue
            if step.action == "emit_start":
                self._bus.emit("ai_start", step.payload.get("data", {}), task_id)
            elif step.action == "emit_chunk":
                self._bus.emit("ai_chunk", step.payload.get("data", {}), task_id)
            elif step.action == "emit_end":
                self._bus.emit("ai_end", step.payload.get("data", {}), task_id)
            elif step.action == "emit_error":
                self._bus.emit("error", step.payload.get("data", {}), task_id)

    def to_dict(self) -> Dict[str, Any]:
        """返回当前 trace 快照，供外部序列化。"""
        return self._trace.snapshot()
