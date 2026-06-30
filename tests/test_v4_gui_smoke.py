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
        assert window._orchestrator.current_session_id is not None
        window.close()
        window.deleteLater()
        self.app.processEvents()

    def test_new_conversation_buttons_create_sessions(self):
        window = MainWindow()
        initial_count = len(window._repo.list_sessions())

        # Click chat new conversation
        window.conversation_list._btn_chat.click()
        self.app.processEvents()

        # Click work new conversation
        window.conversation_list._btn_work.click()
        self.app.processEvents()

        final_count = len(window._repo.list_sessions())
        assert final_count == initial_count + 2, (
            f"Expected {initial_count + 2} sessions, got {final_count}"
        )

        window.close()
        window.deleteLater()
        self.app.processEvents()
