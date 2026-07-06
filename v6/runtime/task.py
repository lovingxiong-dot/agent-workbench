"""v6/runtime/task.py — 任务基类与具体任务类型。

设计来源：docs/v6/SPEC.md 第 4 节。
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Task:
    """Runtime 任务基类。"""

    type: str = ""
    task_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    session_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.type:
            self.type = self.__class__.__name__.lower().replace("task", "")


@dataclass
class ChatTask(Task):
    """用户聊天任务。"""

    text: str = ""

    def __post_init__(self) -> None:
        super().__post_init__()
        self.type = "chat"
        self.payload.setdefault("text", self.text)


@dataclass
class AnalyzeTask(Task):
    """项目分析任务。"""

    target_path: str = ""

    def __post_init__(self) -> None:
        super().__post_init__()
        self.type = "analyze"
        self.payload.setdefault("path", self.target_path)
