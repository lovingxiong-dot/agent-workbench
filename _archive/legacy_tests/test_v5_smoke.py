"""V5 MainWindow 冒烟测试。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from PySide6.QtWidgets import QApplication

from v5.main import bootstrap


class TestV5MainWindowSmoke:
    @classmethod
    def setup_class(cls):
        app = QApplication.instance() or QApplication(sys.argv)
        cls.app = app

    def test_bootstrap_creates_window(self):
        window = bootstrap()
        assert window is not None
        assert hasattr(window, "_left")
        assert hasattr(window, "_center")
        assert hasattr(window, "_right")
        window.close()
        window.deleteLater()
        self.app.processEvents()

    def test_three_column_layout(self):
        window = bootstrap()
        window.show()
        self.app.processEvents()

        sizes = window._splitter.sizes()
        assert len(sizes) == 3, "应存在三栏"
        assert all(s > 0 for s in sizes), "三栏均应有正宽度"

        assert window._left.isVisible()
        assert window._center.isVisible()
        assert window._right.isVisible()

        window.close()
        window.deleteLater()
        self.app.processEvents()

    def test_window_title_from_config(self):
        window = bootstrap()
        title = window.windowTitle()
        assert title and isinstance(title, str)
        window.close()
        window.deleteLater()
        self.app.processEvents()

    def test_new_chat_signal_connected(self):
        window = bootstrap()
        # 点击左栏新建会话按钮应触发 controller 处理
        initial_count = len(window._ctrl._session_service.list_sessions())
        window._left.sign_new_chat.emit("chat")
        self.app.processEvents()

        assert len(window._ctrl._session_service.list_sessions()) == initial_count + 1

        window.close()
        window.deleteLater()
        self.app.processEvents()

    def test_send_message_signal(self):
        window = bootstrap()
        # 创建一个会话后再发送消息
        window._left.sign_new_chat.emit("chat")
        self.app.processEvents()

        chunks = []
        window._center.sign_send_msg.connect(lambda text: chunks.append(text))
        window._center.sign_send_msg.emit("hello")
        self.app.processEvents()

        assert chunks == ["hello"]

        window.close()
        window.deleteLater()
        self.app.processEvents()
