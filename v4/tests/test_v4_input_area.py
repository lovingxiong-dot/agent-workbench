"""
test_v4_input_area.py — v4 输入区组件测试

覆盖：
- Enter 发送、Shift+Enter 换行
- mode/model 切换信号
- 停止按钮在 streaming 时显示
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest

from v4.legacy.input_area import InputAreaWidget
from v4.widgets.base import _THEMES


@pytest.fixture(scope="session")
def qt_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


class TestV4InputArea:
    @pytest.fixture(autouse=True)
    def setup(self, qt_app):
        self.app = qt_app
        self.theme = _THEMES["dark"]
        self.widget = InputAreaWidget(self.theme)
        self.widget.show()
        yield
        self.widget.deleteLater()
        self.app.processEvents()

    def test_enter_sends_message(self):
        received = []
        self.widget.send_requested.connect(lambda: received.append("send"))
        self.widget.text_edit.setPlainText("hello")

        QTest.keyClick(self.widget.text_edit, Qt.Key_Return)
        self.app.processEvents()

        assert len(received) == 1, "Enter 应触发 send_requested"

    def test_shift_enter_inserts_newline(self):
        self.widget.text_edit.setPlainText("line1")
        self.widget.text_edit.moveCursor(QTextCursor.End)

        QTest.keyClick(self.widget.text_edit, Qt.Key_Return, Qt.ShiftModifier)
        self.app.processEvents()

        text = self.widget.text_edit.toPlainText()
        assert "\n" in text, "Shift+Enter 应插入换行"
        assert text.startswith("line1\n"), f"实际文本：{text!r}"

    def test_mode_changed_signal(self):
        modes = ["ask", "plan", "craft"]
        self.widget.set_modes(modes, "ask")
        captured = []
        self.widget.mode_changed.connect(captured.append)

        # 通过标签按钮模拟选择 plan
        self.widget.mode_tag.set_value("plan")
        self.widget._on_mode_changed("plan")
        self.app.processEvents()

        assert captured == ["plan"], f"mode_changed 应发射 plan，实际 {captured}"

    def test_model_changed_signal(self):
        providers = {"tool-agent": {"model": "qwen"}, "flash": {"model": "gemini"}}
        self.widget.set_models(providers, "tool-agent")
        captured = []
        self.widget.model_changed.connect(captured.append)

        # 通过标签按钮模拟选择 flash
        self.widget.model_tag.set_value("flash")
        self.widget._on_model_changed("flash")
        self.app.processEvents()

        assert captured == ["flash"], f"model_changed 应发射 flash，实际 {captured}"

    def test_streaming_toggles_stop_button(self):
        assert not self.widget.stop_btn.isVisible()
        assert self.widget.send_btn.isVisible()

        self.widget.set_streaming(True)
        self.app.processEvents()

        assert self.widget.stop_btn.isVisible(), "streaming 时应显示停止按钮"
        assert not self.widget.send_btn.isVisible(), "streaming 时应隐藏发送按钮"

        self.widget.set_streaming(False)
        self.app.processEvents()

        assert not self.widget.stop_btn.isVisible()
        assert self.widget.send_btn.isVisible()
