"""agent_workbench/conversation/conversation_service.py — Conversation 业务服务。

这是 UI 与底层 SessionService / ChatService 之间的统一入口：
- 管理 Conversation 生命周期（创建、删除、重命名、置顶、激活）。
- 保存用户 / Assistant 消息。
- 在第一轮 Assistant 回复完成后自动触发标题生成。

UI 层（Qt / Web / CLI）只与本服务交互，不直接依赖 SessionService / ChatService。
"""
from __future__ import annotations

from v6.runtime.context import RuntimeContext
from v6.runtime.types import ChatMessage
from v6.services.chat_service import ChatService
from v6.services.session_service import SessionService

from agent_workbench.conversation.title_service import ConversationTitleService


class ConversationService:
    """Conversation Domain 的统一服务入口。"""

    DEFAULT_TITLE: str = "New Conversation"

    def __init__(
        self,
        session_service: SessionService,
        chat_service: ChatService,
        title_service: ConversationTitleService | None = None,
    ) -> None:
        self._session = session_service
        self._chat = chat_service
        self._title = title_service or ConversationTitleService()

    def create_conversation(self, title: str = "") -> str:
        """创建新会话；若 title 为空，则 Navigator 会显示默认占位标题。"""
        ctx = RuntimeContext.new()
        ctx.metadata["session_title"] = title
        self._session.create(ctx)
        return ctx.session_id

    def store_user_message(self, sid: str, text: str) -> None:
        """持久化一条用户消息。"""
        ctx = RuntimeContext.new(session_id=sid)
        ctx.add_message("user", text)
        self._chat.store(ctx)

    def store_assistant_message(self, sid: str, text: str) -> str | None:
        """持久化一条 Assistant 消息，并在标题为空时自动生成标题。

        返回生成后的标题；若未生成则返回 None。
        """
        ctx = RuntimeContext.new(session_id=sid)
        ctx.add_message("assistant", text)
        self._chat.store(ctx)

        load_ctx = RuntimeContext.new(session_id=sid)
        self._chat.load(load_ctx)
        return self._title.maybe_update_title(sid, self._session.manager, load_ctx.messages)

    def load_messages(self, sid: str) -> list[ChatMessage]:
        """加载指定会话的全部消息。"""
        ctx = RuntimeContext.new(session_id=sid)
        self._chat.load(ctx)
        return list(ctx.messages)

    def rename_conversation(self, sid: str, title: str) -> None:
        """重命名会话；手动重命名后自动标题不会再覆盖。"""
        ctx = RuntimeContext.new(session_id=sid)
        ctx.metadata["session_title"] = title
        self._session.rename(ctx)

    def delete_conversation(self, sid: str) -> None:
        """删除会话。"""
        ctx = RuntimeContext.new(session_id=sid)
        self._session.delete(ctx)

    def pin_conversation(self, sid: str) -> bool:
        """切换会话置顶状态。"""
        ctx = RuntimeContext.new(session_id=sid)
        return self._session.pin(ctx)

    def list_groups(self) -> list[tuple[str, str, list[dict]]]:
        """返回按时间分组的会话列表，供 Navigator 渲染。"""
        ctx = RuntimeContext.new()
        self._session.load(ctx)
        return ctx.metadata.get("session_groups", [])

    def get_active(self) -> str | None:
        """返回当前激活会话 ID。"""
        ctx = RuntimeContext.new()
        self._session.get_active(ctx)
        return ctx.session_id

    def set_active(self, sid: str) -> None:
        """设置当前激活会话。"""
        ctx = RuntimeContext.new(session_id=sid)
        self._session.set_active(ctx)

    def get_conversation(self, sid: str) -> dict | None:
        """返回单个会话的元数据。"""
        return self._session.manager.get(sid)
