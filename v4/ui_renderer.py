"""
ui_renderer.py — v4 UI 渲染器

订阅 MessageBus 的 ui.* 事件，统一更新：
- ChatView（当前会话的消息、流式、Phase UI）
- 状态栏 / capacity 指示器
- ConversationList（会话状态徽章）

原则：只处理 UI 表现，不持有业务状态。
事件过滤：只处理当前会话的事件，其余丢弃。
"""
from typing import Callable, Optional
from PySide6.QtCore import QObject

from .event_bus import MessageBus
from .events import *


class UIRenderer(QObject):
    def __init__(self, message_bus, chat_view, status_indicator=None, conversation_list=None, capacity_label=None, queue_bar=None, current_session_provider=None, parent=None):
        super().__init__(parent)
        self._bus = message_bus
        self._chat_view = chat_view
        self._status_indicator = status_indicator
        self._conversation_list = conversation_list
        self._capacity_label = capacity_label
        self._queue_bar = queue_bar
        self._current_session_provider = current_session_provider
        self._bus.subscribe_namespace("ui", self._on_ui_event)

    def _current_session_id(self):
        return self._current_session_provider() if self._current_session_provider else None

    def _is_current(self, event):
        return event.session_id == self._current_session_id()

    def _on_ui_event(self, event):
        handler = getattr(self, f"_handle_{event.name}", None)
        if handler:
            try:
                handler(event)
            except Exception as e:
                print(f"UIRenderer error: {e}", flush=True)

    def _handle_append_user(self, event):
        if self._is_current(event): self._chat_view.append_user(event.text)

    def _handle_append_ai(self, event):
        if self._is_current(event): self._chat_view.append_ai(event.text)

    def _handle_append_system(self, event):
        if self._is_current(event): self._chat_view.append_system(event.text)

    def _handle_stream_chunk(self, event):
        if self._is_current(event): self._chat_view.append_chunk(event.chunk)

    def _handle_finalize_stream(self, event):
        if self._is_current(event): self._chat_view.finalize_stream()

    def _handle_set_streaming(self, event):
        if self._is_current(event): self._chat_view.set_streaming(event.active)

    def _handle_set_phase(self, event):
        if self._is_current(event): self._chat_view.set_phase_indicator(event.phase, event.task_count)

    def _handle_clear_phase(self, event):
        if self._is_current(event): self._chat_view.clear_phase_ui()

    def _handle_clear_chat(self, event):
        if self._is_current(event): self._chat_view.clear_chat()

    def _handle_show_confirm(self, event):
        if self._is_current(event): self._chat_view.show_confirmation(event.task_list)

    def _handle_hide_confirm(self, event):
        if self._is_current(event): self._chat_view.hide_confirmation()

    def _handle_set_send_enabled(self, event):
        if self._is_current(event) and hasattr(self._chat_view, "set_send_enabled"):
            self._chat_view.set_send_enabled(event.enabled)

    def _handle_update_queue_bar(self, event):
        if self._is_current(event) and self._queue_bar:
            self._queue_bar.setVisible(event.visible)
            if event.visible: self._queue_bar.setText(event.bar_text)

    def _handle_focus_input(self, event):
        if self._is_current(event) and hasattr(self._chat_view, "input_field"):
            self._chat_view.input_field.setFocus()

    def _handle_set_active_session(self, event):
        if self._conversation_list:
            try:
                self._conversation_list.set_active_session(event.active_session_id)
            except Exception as e:
                print(f"UIRenderer set_active_session error: {e}", flush=True)

    def _handle_update_session_list(self, event):
        if self._conversation_list:
            try: self._conversation_list.refresh(event.sessions)
            except: pass

    def _handle_update_session_badge(self, event):
        if self._conversation_list:
            try: self._conversation_list.update_badge(event.session_id, event.phase)
            except: pass
