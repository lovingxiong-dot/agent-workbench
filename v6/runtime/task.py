"""v6/runtime/task.py — Runtime 任务模型。

设计原则（Foundation 长期接口）：
- Runtime 只依赖 Task，不依赖 chat() 等专用入口。
- Router 只解析 capability，不解析 payload。
- 后续新增 Capability 不应修改 Task 接口。
- 本阶段不实现 Workflow 字段（parent_task_id / workflow_id / priority / timeout / retry_policy 等）。
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(init=False)
class Task:
    """Runtime 任务基类。

    核心字段：
    - id: Task 唯一标识，供 Trace / Replay / Workspace 使用。
    - capability: 唯一的能力路由依据（如 chat、image_generation、tool、code）。
    - payload: Capability 专属输入，Runtime 不解析其内部结构。
    - metadata: 保存来源、会话、优先级等非业务数据，避免污染 payload。
    - created_at: 创建时间，供 Trace 与后续统计使用。

    兼容字段：
    - session_id: Foundation 阶段仍保留为顶层字段，同时自动同步到 metadata。
    - task_id / type: 旧代码使用的别名，分别映射到 id / capability；构造参数也兼容。
    """

    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    capability: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    session_id: str | None = None

    def __init__(
        self,
        id: str | None = None,
        capability: str = "",
        payload: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        created_at: datetime | None = None,
        session_id: str | None = None,
        task_id: str | None = None,
        type: str | None = None,
    ) -> None:
        self.id = id or task_id or uuid.uuid4().hex
        self.capability = capability or type or ""
        self.payload = payload if payload is not None else {}
        self.metadata = metadata if metadata is not None else {}
        self.created_at = created_at if created_at is not None else datetime.now(timezone.utc)
        self.session_id = session_id
        if not self.capability:
            self.capability = self.__class__.__name__.lower().replace("task", "")
        if self.session_id is not None:
            self.metadata.setdefault("session_id", self.session_id)

    # Backward compatibility: old code uses task_id
    @property
    def task_id(self) -> str:
        return self.id

    @task_id.setter
    def task_id(self, value: str) -> None:
        self.id = value

    # Backward compatibility: old code uses task.type
    @property
    def type(self) -> str:
        return self.capability

    @type.setter
    def type(self, value: str) -> None:
        self.capability = value


@dataclass(init=False)
class ChatTask(Task):
    """用户聊天任务（兼容包装）。"""

    text: str = ""

    def __init__(
        self,
        text: str = "",
        session_id: str | None = None,
        id: str | None = None,
        task_id: str | None = None,
        capability: str = "",
        type: str | None = None,
        payload: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        created_at: datetime | None = None,
    ) -> None:
        super().__init__(
            id=id,
            capability=capability or type or "chat",
            payload=payload,
            metadata=metadata,
            created_at=created_at,
            session_id=session_id,
            task_id=task_id,
        )
        self.text = text
        self.payload.setdefault("text", text)


@dataclass(init=False)
class AnalyzeTask(Task):
    """项目分析任务。"""

    target_path: str = ""

    def __init__(
        self,
        target_path: str = "",
        session_id: str | None = None,
        id: str | None = None,
        task_id: str | None = None,
        capability: str = "",
        type: str | None = None,
        payload: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        created_at: datetime | None = None,
    ) -> None:
        super().__init__(
            id=id,
            capability=capability or type or "analyze",
            payload=payload,
            metadata=metadata,
            created_at=created_at,
            session_id=session_id,
            task_id=task_id,
        )
        self.target_path = target_path
        self.payload.setdefault("path", target_path)
