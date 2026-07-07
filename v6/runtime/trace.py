"""v6/runtime/trace.py — Runtime Trace：记录 Task 执行历史，支持 Replay。

设计来源：docs/v6/SPEC.md 第 4、8 节及 Runtime Task 四对象演进方向。

核心原则：
- RuntimeTrace 只记录事实（History），不保存业务逻辑。
- 每个步骤包含：时间戳、阶段、节点（runtime/engine/service/tool）、动作、载荷摘要，
  并可联动 RuntimeMetrics 记录 duration_ms / tokens / cost / tool_time_ms。
- Engine / Service / Tool / Runtime 均可向 ctx.trace.add(...) 写入自己负责的步骤。
- RuntimeTrace 与 RuntimeContext 生命周期绑定，随 Task 创建而创建。
- ReplayPlayer 按 trace 步骤重放事件，供调试、审计、可视化使用。
"""
from __future__ import annotations

import copy
import threading
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Generator, List, Optional, Union

from v6.runtime.enums import TraceEvent
from v6.runtime.event_bus import EventBus
from v6.runtime.metrics import RuntimeMetrics


@dataclass
class TraceStep:
    """单次执行步骤。

    Metrics 字段（duration_ms / tokens / cost / tool_time_ms）可与 RuntimeMetrics 联动，
    形成 Task Execution Timeline。

    parent_id / step_id 支持将 Timeline 展开为 Tree，
    为 Replay、Metrics、Tree UI 提供结构基础。
    """

    timestamp: float
    phase: str
    node: str
    action: str
    payload: Dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0
    tokens: int = 0
    cost: float = 0.0
    tool_time_ms: float = 0.0
    step_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    parent_id: str = ""
    status: str = "success"  # pending / running / success / failed

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
        duration_ms: float = 0.0,
        tokens: int = 0,
        cost: float = 0.0,
        tool_time_ms: float = 0.0,
        metrics: Optional[RuntimeMetrics] = None,
        parent_id: str = "",
        status: str = "success",
    ) -> TraceStep:
        """追加一条执行步骤。

        Args:
            node: 记录主体，如 runtime / engine / service / tool / adapter。
            action: 具体动作，如 start / dispatch / finish / error / emit_chunk。
            phase: 当前阶段，如 inference / memory / tool / policy。
            payload: 附加结构化信息，建议只放摘要（避免过大对象）。
            duration_ms: 步骤耗时（毫秒）。
            tokens: 步骤消耗 token 数。
            cost: 步骤估算成本。
            tool_time_ms: 步骤中工具执行耗时（毫秒）。
            metrics: RuntimeMetrics 实例；若提供且未显式传入指标，
                     自动提取 tokens / cost / tool_time_ms。
            parent_id: 父步骤 ID，支持 Tree 结构。
            status: 步骤状态：pending / running / success / failed。

        Returns:
            刚添加的 TraceStep（深拷贝），方便调用方获取 step_id。
        """
        if metrics is not None:
            snap = metrics.snapshot()
            tokens = tokens or snap.get("tokens", 0)
            cost = cost or snap.get("cost", 0.0)
            tool_time_ms = tool_time_ms or snap.get("tool_time_ms", 0.0)

        step = TraceStep(
            timestamp=time.time(),
            phase=phase,
            node=node,
            action=action,
            payload=copy.deepcopy(payload) if payload else {},
            duration_ms=duration_ms,
            tokens=tokens,
            cost=cost,
            tool_time_ms=tool_time_ms,
            parent_id=parent_id,
            status=status,
        )
        with self._lock:
            self._steps.append(step)
        return copy.deepcopy(step)

    @contextmanager
    def timed_step(
        self,
        node: Union[str, Enum],
        action: Union[str, TraceEvent],
        phase: Union[str, Enum] = "",
        payload: Optional[Dict[str, Any]] = None,
        metrics: Optional[RuntimeMetrics] = None,
        parent_id: str = "",
        status: str = "success",
    ) -> Generator[TraceStep, None, None]:
        """自动计时并在退出时抓取 metrics 的上下文管理器。

        使用示例：
            with ctx.trace.timed_step("engine", TraceEvent.MODEL_INVOKE, metrics=ctx.metrics):
                response = llm.call(...)
        """
        start = time.time()
        step = TraceStep(
            timestamp=start,
            phase=phase,
            node=node,
            action=action,
            payload=copy.deepcopy(payload) if payload else {},
            parent_id=parent_id,
            status=status,
        )
        with self._lock:
            self._steps.append(step)
        try:
            yield step
        finally:
            step.duration_ms = (time.time() - start) * 1000
            if metrics is not None:
                snap = metrics.snapshot()
                step.tokens = snap.get("tokens", 0)
                step.cost = snap.get("cost", 0.0)
                step.tool_time_ms = snap.get("tool_time_ms", 0.0)

    @contextmanager
    def scope(
        self,
        node: Union[str, Enum],
        action: Union[str, TraceEvent],
        phase: Union[str, Enum] = "",
        payload: Optional[Dict[str, Any]] = None,
        parent_id: str = "",
        status: str = "success",
    ) -> Generator[TraceStep, None, None]:
        """上下文作用域：预留接口，供 Workflow Runtime 维护嵌套 parent_id 栈。

        Foundation 阶段 Chat Runtime 的执行链（Task -> Engine -> Stream）足够扁平，
        由 EventBus 根据 ``TRACE_EVENT_LEVEL`` / ``TRACE_EVENT_PARENT_LEVEL``
        自动推断 parent_id，因此不推荐在 Foundation 中广泛使用 ``scope()``。

        未来 Workflow Runtime 引入 Planner / Router / Multi-Tool 等嵌套链路时，
        可通过 ``with ctx.trace.scope(...)`` 显式管理父子层级。
        """
        step = TraceStep(
            timestamp=time.time(),
            phase=phase,
            node=node,
            action=action,
            payload=copy.deepcopy(payload) if payload else {},
            parent_id=parent_id,
            status="running",
        )
        with self._lock:
            self._steps.append(step)
        try:
            yield step
        finally:
            step.status = status

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
                        "duration_ms": s.duration_ms,
                        "tokens": s.tokens,
                        "cost": s.cost,
                        "tool_time_ms": s.tool_time_ms,
                        "step_id": s.step_id,
                        "parent_id": s.parent_id,
                        "status": s.status,
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
