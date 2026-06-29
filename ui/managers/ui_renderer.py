"""
UIRenderer — UI 渲染指令统一处理器（v3）

订阅 MessageBus 的 ui.* 事件，统一更新：
- ChatView（当前会话的消息、流式、Phase UI）
- 状态栏 / capacity 指示器
- ConversationList（会话状态徽章）

原则：只处理 UI 表现，不持有业务状态。
"""
import logging
from typing import Callable, Optional

from PySide6.QtCore import QObject

from core.event_bus import MessageBus
from core.events import (
    UIAppendUserEvent,
    UIAppendAIEvent,
    UIAppendSystemEvent,
    UIStreamChunkEvent,
    UIFinalizeStreamEvent,
    UISetStreamingEvent,
    UISetPhaseIndicatorEvent,
    UIClearPhaseUIEvent,
    UIShowConfirmationEvent,
    UIHideConfirmationEvent,
    UIShowSkipVerifyEvent,
    UIHideSkipVerifyEvent,
    UIUpdateStatusBarEvent,
    UIUpdateSessionStatusEvent,
    UISetSendEnabledEvent,
    UIUpdateQueueBarEvent,
)

logger = logging.getLogger(__name__)


class UIRenderer(QObject):
    """v3 UI 事件渲染器"""

    def __init__(
        self,
        message_bus: MessageBus,
        chat_view,
        status_indicator=None,
        conversation_list=None,
        capacity_label=None,
        queue_bar=None,
        current_session_provider: Callable[[], Optional[str]] = None,
        parent=None,
    ):
        super().__init__(parent)
        self._bus = message_bus
        self._chat_view = chat_view
        self._status_indicator = status_indicator
        self._conversation_list = conversation_list
        self._capacity_label = capacity_label
        self._queue_bar = queue_bar
        self._current_session_provider = current_session_provider

        self._subscribe_events()

    def _current_session_id(self) -> Optional[str]:
        if self._current_session_provider:
            return self._current_session_provider()
        return None

    def _is_current(self, session_id: str) -> bool:
        return session_id == self._current_session_id()

    def _subscribe_events(self):
        self._bus.subscribe_namespace("ui", self._on_ui_event)

    def _on_ui_event(self, event):
        """统一事件分发"""
        try:
            handler = getattr(self, f"_handle_{event.name}", None)
            if handler:
                handler(event)
        except Exception as e:
            logger.warning("UIRenderer handle %s error: %s", event.event_type(), e)

    def _handle_append_user(self, event: UIAppendUserEvent):
        if not self._is_current(event.session_id):
            return
        self._chat_view.append_user(event.text)

    def _handle_append_ai(self, event: UIAppendAIEvent):
        if not self._is_current(event.session_id):
            return
        self._chat_view.append_ai(event.text)

    def _handle_append_system(self, event: UIAppendSystemEvent):
        if not self._is_current(event.session_id):
            return
        self._chat_view.append_system(event.text)

    def _handle_stream_chunk(self, event: UIStreamChunkEvent):
        if not self._is_current(event.session_id):
            return
        self._chat_view.append_chunk(event.chunk)

    def _handle_finalize_stream(self, event: UIFinalizeStreamEvent):
        if not self._is_current(event.session_id):
            return
        self._chat_view.finalize_stream()

    def _handle_set_streaming(self, event: UISetStreamingEvent):
        if not self._is_current(event.session_id):
            return
        self._chat_view.set_streaming(event.active)

    def _handle_set_phase_indicator(self, event: UISetPhaseIndicatorEvent):
        if not self._is_current(event.session_id):
            return
        self._chat_view.set_phase_indicator(
            event.phase,
            event.task_count,
        )

    def _handle_clear_phase_ui(self, event: UIClearPhaseUIEvent):
        if not self._is_current(event.session_id):
            return
        self._chat_view.clear_phase_ui()

    def _handle_show_confirmation(self, event: UIShowConfirmationEvent):
        if not self._is_current(event.session_id):
            return
        self._chat_view.show_confirmation(event.task_list)

    def _handle_hide_confirmation(self, event: UIHideConfirmationEvent):
        if not self._is_current(event.session_id):
            return
        self._chat_view.hide_confirmation()

    def _handle_show_skip_verify(self, event: UIShowSkipVerifyEvent):
        if not self._is_current(event.session_id):
            return
        self._chat_view.show_skip_verify()

    def _handle_hide_skip_verify(self, event: UIHideSkipVerifyEvent):
        if not self._is_current(event.session_id):
            return
        self._chat_view.hide_skip_verify()

    def _handle_update_status_bar(self, event: UIUpdateStatusBarEvent):
        if self._status_indicator is None:
            return
        self._status_indicator.setText(event.capacity_text)

    def _handle_update_session_status(self, event: UIUpdateSessionStatusEvent):
        if self._conversation_list is None:
            return
        try:
            self._conversation_list.update_session_status(
                event.session_id,
                event.status,
            )
        except Exception as e:
            logger.debug("update_session_status not supported: %s", e)

    def _handle_set_send_enabled(self, event: UISetSendEnabledEvent):
        if not self._is_current(event.session_id):
            return
        if hasattr(self._chat_view, "set_send_enabled"):
            self._chat_view.set_send_enabled(event.enabled)

    def _handle_update_queue_bar(self, event: UIUpdateQueueBarEvent):
        if not self._is_current(event.session_id):
            return
        if self._queue_bar is None:
            return
        self._queue_bar.setVisible(event.is_visible)
        if event.is_visible:
            self._queue_bar.setText(event.bar_text)
