"""presentation/protocols/interaction/command.py — InteractionCommand 协议。

InteractionCommand 表达用户交互意图（UI 语言），
不表达 Runtime 行为（Capability / Tool / Engine / Provider）。

约束：
  ✓ 用户动作：CHAT_SUBMIT, SESSION_SELECT, GENERATION_CANCEL 等
  ✗ 禁止 Runtime 概念：TOOL_EXECUTE, CAPABILITY_RUN, ENGINE_SELECT 等

原则：
  UI 说"用户点击了运行按钮"
  ↓
  InteractionCommand(type=WORKSPACE_ACTION, payload={"action":"run"})
  ↓
  Runtime Decision Layer 判断调用什么 Capability

Phase 2-C.1：独立协议，从 RuntimeRequest 提取。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CommandType(str, Enum):
    """用户交互意图类型。

    只表达用户做了什么，不表达 Runtime 应该怎么执行。
    禁止添加 TOOL / CAPABILITY / ENGINE / PROVIDER 等 Runtime 概念。
    """

    # ── 聊天 ──
    CHAT_SUBMIT = "chat.submit"           # 用户发送聊天消息

    # ── 生成控制 ──
    GENERATION_CANCEL = "generation.cancel"  # 用户点击停止按钮

    # ── 会话操作 ──
    SESSION_SELECT = "session.select"     # 用户选中一个会话
    SESSION_CREATE = "session.create"     # 用户点击新建会话
    SESSION_DELETE = "session.delete"     # 用户删除一个会话

    # ── 工作区操作 ──
    WORKSPACE_ACTION = "workspace.action"  # 用户在工作区执行操作（打开文件、运行等）

    # ── 输入提交 ──
    INPUT_SUBMIT = "input.submit"          # 用户在输入区提交（终端命令、搜索等）

    # ── UI 动作 ──
    UI_ACTION = "ui.action"                # 通用 UI 动作（设置、导出、切换主题等）


@dataclass
class InteractionCommand:
    """UI 层用户意图。

    与 RuntimeRequest 的区别：
    - InteractionCommand 表达用户意图（UI 语言）
    - RuntimeRequest 表达执行请求（Runtime 语言）
    - Decision Layer 负责将 Command 翻译为 Request

    字段：
    - type: 命令类型（用户交互意图）。
    - payload: 命令载荷（具体数据）。
    - session_id: 关联的会话标识（可选）。
    """
    type: CommandType
    payload: dict[str, Any] = field(default_factory=dict)
    session_id: str | None = None

    def __post_init__(self) -> None:
        if self.payload is None:
            self.payload = {}