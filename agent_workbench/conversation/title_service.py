"""agent_workbench/conversation/title_service.py — 会话标题服务。

职责：
- 根据消息列表生成标题。
- 在 Assistant 第一轮回复完成后，若标题为空则自动更新会话标题。
- 不阻塞 UI；标题生成失败时静默回退到默认标题。
"""
from __future__ import annotations

from v6.runtime.types import ChatMessage
from v6.session_manager import SessionManager

from agent_workbench.conversation.title_generator import RuleTitleGenerator, TitleGenerator


class ConversationTitleService:
    """协调标题生成与会话持久化。"""

    DEFAULT_TITLE: str = "New Conversation"

    def __init__(self, title_generator: TitleGenerator | None = None) -> None:
        self._generator = title_generator or RuleTitleGenerator()

    def generate_title(self, messages: list[ChatMessage]) -> str:
        """根据消息列表生成标题。"""
        try:
            title = self._generator.generate(messages)
        except Exception:
            title = ""
        return title.strip() or self.DEFAULT_TITLE

    def maybe_update_title(
        self,
        sid: str,
        session_manager: SessionManager,
        messages: list[ChatMessage],
    ) -> str | None:
        """如果会话标题为空，则生成并保存新标题；否则返回 None。

        非空标题被视为用户手动设置或已自动生成过，不再覆盖。
        """
        session = session_manager.get(sid)
        if session is None:
            return None

        current_title = (session.get("title") or "").strip()
        if current_title:
            return None

        title = self.generate_title(messages)
        session_manager.rename(sid, title)
        return title
