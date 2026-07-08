"""v6/runtime/user_request.py — 用户请求协议对象。

设计边界：
- UserRequest 是 Runtime 的输入协议，封装一切来自外部（UI / API / CLI / Workflow / System）的请求。
- Manager 负责将 UserRequest 转换为 Task；Runtime 只接收 Task，不解析 UserRequest。
- 本阶段仅包含最通用的字段，后续扩展通过 metadata 完成，不修改主结构。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class UserRequest:
    """用户请求对象。

    字段：
    - text: 文本输入（可选）。
    - attachments: 附件列表，如图片、文件、音频等（可选）。
    - metadata: 来源、策略、调度等扩展信息，避免污染主结构。
    - session_id: 所属会话标识（可选）。
    - task_id: 外部指定的任务标识（可选）。
    """

    text: str | None = None
    attachments: list[Any] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    session_id: str | None = None
    task_id: str | None = None

    def __post_init__(self) -> None:
        if self.attachments is None:
            self.attachments = []
        if self.metadata is None:
            self.metadata = {}
