"""agent_workbench/conversation — Conversation Domain。

职责：
- 管理 Conversation 生命周期与元数据（title、summary 等）。
- 提供 TitleGenerator / ConversationTitleService，自动生成会话标题。
- 通过 ConversationService 为 UI 提供统一入口，使 Qt / Web / CLI 只读取 conversation.title。

UI 层不直接调用 SessionService / ChatService，而是通过 ConversationService 与 Conversation Domain 交互。
"""
from __future__ import annotations

from agent_workbench.conversation.conversation_service import ConversationService
from agent_workbench.conversation.title_generator import (
    RuleTitleGenerator,
    TitleGenerator,
)
from agent_workbench.conversation.title_service import ConversationTitleService

__all__ = [
    "ConversationService",
    "ConversationTitleService",
    "TitleGenerator",
    "RuleTitleGenerator",
]
