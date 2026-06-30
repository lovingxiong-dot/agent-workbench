"""
Smoke test for v4 MainWindow startup and basic interactions.
Does not require a display; uses QCoreApplication event loop with timers.
"""
import sys
import os
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from PySide6.QtCore import QCoreApplication, QTimer
from PySide6.QtWidgets import QApplication

from v4.main_window import MainWindow
from v4.events import SessionCreateEvent


class TestV4GUISmoke:
    @classmethod
    def setup_class(cls):
        app = QApplication.instance() or QApplication(sys.argv)
        cls.app = app

    def test_window_starts_without_crash(self):
        window = MainWindow()
        self.app.processEvents()
        assert window is not None
        assert window._orchestrator is not None
        # 启动时进入草稿窗口，不自动创建会话
        assert window._orchestrator.current_session_id is None
        window.close()
        window.deleteLater()
        self.app.processEvents()

    def test_new_conversation_buttons_do_not_create_empty_sessions(self):
        window = MainWindow()
        initial_count = len(window._repo.list_sessions())

        # 反复点击新对话按钮，不应创建空会话
        window.conversation_list._btn_chat.click()
        self.app.processEvents()
        window.conversation_list._btn_work.click()
        self.app.processEvents()
        window.conversation_list._btn_chat.click()
        self.app.processEvents()

        final_count = len(window._repo.list_sessions())
        assert final_count == initial_count, (
            f"空点击不应创建会话，期望 {initial_count}，实际 {final_count}"
        )

        window.close()
        window.deleteLater()
        self.app.processEvents()
