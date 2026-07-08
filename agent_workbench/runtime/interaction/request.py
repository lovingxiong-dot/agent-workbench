"""agent_workbench/runtime/interaction/request.py — 外部输入协议。

RuntimeRequest 是 Workbench 与所有外部入口（UI / MCP / Local Agent / Remote Agent）
之间的统一输入契约。它不是 UserRequest、RuntimeDecision 或 UI Model。

约束：
- 不允许表达 Capability 路由意图（禁止 capability_hint）。
- action_id 表示用户动作，不是 Runtime capability。
  正确："format_current_file"
  错误："python_formatter"
- Capability 选择只能由 Runtime 内部的 Decision Layer 完成。
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from v6.runtime.user_request import UserRequest


class RuntimeRequestSource(str, Enum):
    """RuntimeRequest 的来源。

    注意：source 是环境上下文边界（Global Chat vs Workspace Session），
    不是 capability 路由指令。Decision Layer 可以参考 source 作为上下文，
    但 capability 选择仍由 Runtime Resolver 独立完成。
    """

    GLOBAL_CHAT = "global_chat"
    WORKSPACE_SESSION = "workspace_session"
    COMMAND_BAR = "command_bar"
    WORKSPACE_ACTION = "workspace_action"
    MCP = "mcp"
    LOCAL_AGENT = "local_agent"


@dataclass
class RuntimeRequest:
    """外部请求对象。

    字段：
    - request_id: 请求唯一标识，默认自动生成。
    - source: 请求来源。
    - session_id: 所属会话标识。
    - task_id: 外部指定的任务标识；缺省使用 request_id。
    - text: 文本输入。
    - attachments: 附件列表。
    - action_id: 用户动作标识（如 "format_current_file"），不是 capability_id。
    - payload: 执行层附加数据。
    - metadata: 扩展元数据。
    """

    request_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    source: RuntimeRequestSource = RuntimeRequestSource.GLOBAL_CHAT
    session_id: str | None = None
    task_id: str | None = None
    text: str | None = None
    attachments: list[Any] = field(default_factory=list)
    action_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.attachments is None:
            self.attachments = []
        if self.payload is None:
            self.payload = {}
        if self.metadata is None:
            self.metadata = {}

    def to_user_request(self) -> UserRequest:
        """转换为 Runtime 内部的 UserRequest。"""
        metadata = dict(self.metadata)
        metadata["source"] = self.source.value
        if self.action_id is not None:
            metadata["action_id"] = self.action_id
        if self.request_id is not None:
            metadata["request_id"] = self.request_id

        return UserRequest(
            text=self.text,
            attachments=list(self.attachments),
            session_id=self.session_id,
            task_id=self.task_id or self.request_id,
            metadata=metadata,
        )
