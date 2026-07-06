"""v6/runtime/context.py — 单次任务运行时上下文。

设计来源：docs/v6/SPEC.md 第 4、8 节。

核心原则：
- RuntimeContext 是运行时唯一状态对象（Single Source of Truth）。
- RuntimeContext 保存 Runtime Facts，不拥有 Runtime Behavior / 业务能力。
- Engine/Service 产生 Facts，写入 RuntimeContext；Runtime 编排 Engine 执行顺序。
- Engine 之间零耦合，不直接彼此调用，只通过 RuntimeContext 共享状态。
- RuntimeContext 允许拥有数据管理能力（add_message / clone / snapshot / restore / freeze / reset / to_dict 等）。
- 禁止出现 ctx.call_llm() / ctx.execute_tool() / ctx.save_memory() / ctx.invoke_agent() / ctx.dispatch() 等业务方法。
- messages 元素为 ChatMessage，不再使用裸 dict。
"""
from __future__ import annotations

import copy
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from v6.runtime.trace import RuntimeTrace
from v6.runtime.types import ChatMessage


@dataclass
class RuntimeContext:
    """维护单次任务的运行时事实（Runtime Facts）。

    RuntimeContext 是 Runtime State Container（运行时状态容器），不是 Runtime Manager。
    字段可演进，Engine 不应假设字段集合固定。
    """

    task_id: str
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None
    group_user_id: Optional[str] = None

    # 执行状态
    phase: str = ""
    mode: str = ""
    model: str = ""
    provider: str = ""

    # 项目与记忆
    project_path: str = ""
    memory: Dict[str, Any] = field(default_factory=dict)

    # 消息、工具、指标、结果
    messages: List[ChatMessage] = field(default_factory=list)
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    result: Dict[str, Any] = field(default_factory=dict)

    # 执行历史（History），供调试、回放、审计
    trace: RuntimeTrace = field(default_factory=RuntimeTrace)

    # 通用元数据容器，Engine 可读写自己负责的字段
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    created_at: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        self._lock = threading.RLock()

    @classmethod
    def new(
        cls,
        session_id: Optional[str] = None,
        task_id: Optional[str] = None,
        **kwargs: Any,
    ) -> "RuntimeContext":
        """工厂方法：自动生成 task_id，保持 Runtime 生命周期可追踪性。

        业务代码应优先使用此方法，避免手动填写无意义的 task_id。
        """
        return cls(
            task_id=task_id or uuid.uuid4().hex,
            session_id=session_id,
            **kwargs,
        )

    # ─────────────────────────────────────────────────────────
    # 数据管理方法（允许）
    # ─────────────────────────────────────────────────────────

    def add_message(self, role: str, content: str) -> None:
        """追加一条 ChatMessage 到上下文。"""
        with self._lock:
            self.messages.append(ChatMessage(role=role, content=content))

    def set_status(self, status: str) -> None:
        """线程安全地更新任务状态。"""
        with self._lock:
            self.status = status

    def snapshot(self) -> Dict[str, Any]:
        """返回当前状态的深拷贝快照（用于 Checkpoint / Replay / Rollback）。"""
        with self._lock:
            return self._make_snapshot()

    freeze = snapshot  # 别名：强调不可变快照语义

    def restore(self, snapshot: Dict[str, Any]) -> None:
        """从快照恢复状态（Rollback / Replay 基础）。"""
        with self._lock:
            self.task_id = snapshot.get("task_id", self.task_id)
            self.session_id = snapshot.get("session_id", self.session_id)
            self.conversation_id = snapshot.get("conversation_id", self.conversation_id)
            self.group_user_id = snapshot.get("group_user_id", self.group_user_id)
            self.phase = snapshot.get("phase", "")
            self.mode = snapshot.get("mode", "")
            self.model = snapshot.get("model", "")
            self.provider = snapshot.get("provider", "")
            self.project_path = snapshot.get("project_path", "")
            self.memory = copy.deepcopy(snapshot.get("memory", {}))
            self.tool_calls = copy.deepcopy(snapshot.get("tool_calls", []))
            self.metrics = copy.deepcopy(snapshot.get("metrics", {}))
            self.result = copy.deepcopy(snapshot.get("result", {}))
            self.metadata = copy.deepcopy(snapshot.get("metadata", {}))
            self.status = snapshot.get("status", "pending")
            self.created_at = snapshot.get("created_at", time.time())
            # trace 恢复：若快照含 steps 则重建 RuntimeTrace，否则保留当前实例
            raw_trace = snapshot.get("trace")
            if isinstance(raw_trace, dict) and "steps" in raw_trace:
                self.trace = RuntimeTrace()
                for s in raw_trace["steps"]:
                    self.trace.add(
                        node=s.get("node", ""),
                        action=s.get("action", ""),
                        phase=s.get("phase", ""),
                        payload=s.get("payload", {}),
                    )
            raw_messages = snapshot.get("messages", [])
            self.messages = [
                ChatMessage(**copy.deepcopy(m)) if isinstance(m, dict) else copy.deepcopy(m)
                for m in raw_messages
            ]

    def reset(self) -> None:
        """重置为初始空状态（保留 task_id 等标识）。"""
        with self._lock:
            self.phase = ""
            self.mode = ""
            self.model = ""
            self.provider = ""
            self.project_path = ""
            self.memory.clear()
            self.messages.clear()
            self.tool_calls.clear()
            self.metrics.clear()
            self.result.clear()
            self.trace.clear()
            self.metadata.clear()
            self.status = "pending"

    def clone(self) -> "RuntimeContext":
        """深拷贝自身，生成独立副本。"""
        with self._lock:
            cloned = RuntimeContext(
                task_id=self.task_id,
                session_id=self.session_id,
                conversation_id=self.conversation_id,
                group_user_id=self.group_user_id,
                phase=self.phase,
                mode=self.mode,
                model=self.model,
                provider=self.provider,
                project_path=self.project_path,
                memory=copy.deepcopy(self.memory),
                messages=copy.deepcopy(self.messages),
                tool_calls=copy.deepcopy(self.tool_calls),
                metrics=copy.deepcopy(self.metrics),
                result=copy.deepcopy(self.result),
                metadata=copy.deepcopy(self.metadata),
                status=self.status,
                created_at=self.created_at,
            )
        # trace 是独立的可变对象，需要单独深拷贝步骤
        cloned.trace = RuntimeTrace()
        for step in self.trace.steps():
            cloned.trace.add(
                node=step.node,
                action=step.action,
                phase=step.phase,
                payload=step.payload,
            )
        return cloned

    def to_dict(self) -> Dict[str, Any]:
        """序列化上下文为字典（兼容旧接口，语义同 snapshot）。"""
        return self.snapshot()

    # ─────────────────────────────────────────────────────────
    # 内部辅助
    # ─────────────────────────────────────────────────────────

    def _make_snapshot(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "session_id": self.session_id,
            "conversation_id": self.conversation_id,
            "group_user_id": self.group_user_id,
            "phase": self.phase,
            "mode": self.mode,
            "model": self.model,
            "provider": self.provider,
            "project_path": self.project_path,
            "memory": copy.deepcopy(self.memory),
            "messages": [copy.deepcopy(m.__dict__) for m in self.messages],
            "tool_calls": copy.deepcopy(self.tool_calls),
            "metrics": copy.deepcopy(self.metrics),
            "result": copy.deepcopy(self.result),
            "trace": self.trace.snapshot(),
            "metadata": copy.deepcopy(self.metadata),
            "status": self.status,
            "created_at": self.created_at,
        }
