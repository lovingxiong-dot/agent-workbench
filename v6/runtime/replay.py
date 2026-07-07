"""v6/runtime/replay.py — Runtime Execution Replay Foundation。

设计来源：V6.5 Runtime Foundation Layer Step 5.3。

核心原则：
- Replay 不是业务能力，而是 Runtime Infrastructure；因此以 ReplayService 形式存在，不实现为 Engine。
- ReplayRecord 关注"如何重新发生"，与 TraceStep（关注"发生了什么"）职责不同。
- 第一版只做 Deterministic Trace Replay：记录、导出、查看执行轨迹，不重新调用 LLM/Tool/Memory。
- ReplayService 通过 EventBus 订阅事件，不直接耦合 Engine。
"""
from __future__ import annotations

import copy
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from v6.runtime.event_bus import RuntimeEvent
from v6.runtime.trace import RuntimeTrace


@dataclass
class ReplayRecord:
    """单次可回放记录。

    字段说明：
    - trace_id: Trace 标识，便于按 Trace 聚合。
    - task_id: Runtime Task 标识。
    - timestamp: 事件发生时间戳。
    - component: 组件全名，例如 "engine:llm" / "service:chat" / "runtime" / "tool:search"。
    - component_type: 组件类型，例如 "engine" / "service" / "runtime" / "tool" / "adapter" / "observer"。
    - event_type: 事件类型，例如 "engine.started" / "task.completed"。
    - input_snapshot: 输入快照，用于回放时还原上下文。
    - output_snapshot: 输出快照，用于回放时观察结果。
    - metadata: 额外元数据。
    """

    trace_id: str
    task_id: str
    timestamp: float
    component: str
    component_type: str
    event_type: str
    input_snapshot: Dict[str, Any] = field(default_factory=dict)
    output_snapshot: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典。"""
        return {
            "trace_id": self.trace_id,
            "task_id": self.task_id,
            "timestamp": self.timestamp,
            "component": self.component,
            "component_type": self.component_type,
            "event_type": self.event_type,
            "input_snapshot": copy.deepcopy(self.input_snapshot),
            "output_snapshot": copy.deepcopy(self.output_snapshot),
            "metadata": copy.deepcopy(self.metadata),
        }

    @classmethod
    def from_event(cls, event: RuntimeEvent) -> "ReplayRecord":
        """从 RuntimeEvent 构造 ReplayRecord。"""
        payload = event.payload or {}
        component = event.source or "event_bus"
        component_type = cls._infer_component_type(component)
        return cls(
            trace_id=event.trace_id or event.task_id or "",
            task_id=event.task_id or "",
            timestamp=event.timestamp or time.time(),
            component=component,
            component_type=component_type,
            event_type=event.type or "",
            input_snapshot=copy.deepcopy(payload.get("input_snapshot", {})),
            output_snapshot=copy.deepcopy(payload.get("output_snapshot", {})),
            metadata=copy.deepcopy(payload.get("metadata", {})),
        )

    @staticmethod
    def _infer_component_type(component: str) -> str:
        """根据 component 名称推断类型。"""
        if ":" in component:
            return component.split(":", 1)[0]
        if component in {"runtime", "event_bus"}:
            return "runtime"
        return component


class ReplayLog:
    """ReplayRecord 列表容器；线程安全。"""

    def __init__(self) -> None:
        self._records: List[ReplayRecord] = []
        self._lock = threading.Lock()

    def add(self, record: ReplayRecord) -> None:
        """追加一条记录。"""
        with self._lock:
            self._records.append(record)

    def records(self) -> List[ReplayRecord]:
        """返回记录列表深拷贝快照。"""
        with self._lock:
            return copy.deepcopy(self._records)

    def clear(self) -> None:
        """清空记录。"""
        with self._lock:
            self._records.clear()

    def filter(
        self,
        task_id: Optional[str] = None,
        component: Optional[str] = None,
        event_type: Optional[str] = None,
    ) -> List[ReplayRecord]:
        """按条件筛选记录。"""
        with self._lock:
            result = list(self._records)
        if task_id is not None:
            result = [r for r in result if r.task_id == task_id]
        if component is not None:
            result = [r for r in result if r.component == component]
        if event_type is not None:
            result = [r for r in result if r.event_type == event_type]
        return copy.deepcopy(result)

    def timeline(self, task_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """返回按时间排序的时间线字典列表。"""
        records = self.filter(task_id=task_id)
        return [r.to_dict() for r in sorted(records, key=lambda r: r.timestamp)]

    def export(self) -> Dict[str, Any]:
        """导出完整 ReplayLog。"""
        with self._lock:
            records = list(self._records)
        return {
            "exported_at": time.time(),
            "record_count": len(records),
            "records": [r.to_dict() for r in sorted(records, key=lambda r: r.timestamp)],
        }


class ReplayService:
    """Runtime Execution Replay 服务。

    职责：
    - 订阅 EventBus 事件并转换为 ReplayRecord。
    - 从 RuntimeTrace 批量导入历史记录。
    - 提供 timeline / export / filter / view 等只读接口。
    - 不重新执行任何 Engine / Service / Tool。
    """

    def __init__(self, event_bus: Optional[Any] = None) -> None:
        self._log = ReplayLog()
        self._event_bus: Optional[Any] = event_bus
        self._subscribed_types: List[str] = []

    @property
    def log(self) -> ReplayLog:
        return self._log

    def attach(self, event_bus: Any) -> None:
        """绑定 EventBus 并订阅所有 RuntimeEventType 事件。"""
        self._event_bus = event_bus
        self._subscribe()

    def _subscribe(self) -> None:
        """订阅事件；具体类型由 RuntimeEventType 枚举决定。"""
        if self._event_bus is None:
            return
        try:
            from v6.runtime.event_bus import RuntimeEventType

            for event_type in RuntimeEventType:
                self._event_bus.subscribe(event_type.value, self._on_event)
                self._subscribed_types.append(event_type.value)
        except Exception:  # pragma: no cover - defensive
            pass

    def _on_event(self, event: RuntimeEvent) -> None:
        """事件回调：将事件转为 ReplayRecord 并存入 ReplayLog。"""
        record = ReplayRecord.from_event(event)
        self._log.add(record)

    def import_from_trace(self, trace: RuntimeTrace, task_id: str = "") -> int:
        """从 RuntimeTrace 导入历史步骤为 ReplayRecord；返回导入数量。"""
        count = 0
        for step in trace.steps():
            payload = step.payload or {}
            component = step.node or "trace"
            record = ReplayRecord(
                trace_id=task_id,
                task_id=task_id,
                timestamp=step.timestamp,
                component=component,
                component_type=ReplayRecord._infer_component_type(component),
                event_type=step.action or "",
                input_snapshot=copy.deepcopy(payload.get("input_snapshot", {})),
                output_snapshot=copy.deepcopy(payload.get("output_snapshot", {})),
                metadata=copy.deepcopy({k: v for k, v in payload.items() if k not in {"input_snapshot", "output_snapshot"}}),
            )
            self._log.add(record)
            count += 1
        return count

    def timeline(self, task_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """返回时间线。"""
        return self._log.timeline(task_id=task_id)

    def export(self) -> Dict[str, Any]:
        """导出完整 ReplayLog。"""
        return self._log.export()

    def view(self, task_id: Optional[str] = None) -> Dict[str, Any]:
        """查看指定 task 的 replay 摘要。"""
        records = self._log.filter(task_id=task_id)
        components: Dict[str, int] = {}
        for r in records:
            components[r.component] = components.get(r.component, 0) + 1
        return {
            "task_id": task_id,
            "record_count": len(records),
            "components": components,
            "timeline": [r.to_dict() for r in sorted(records, key=lambda r: r.timestamp)],
        }
