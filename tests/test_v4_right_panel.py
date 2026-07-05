"""
test_v4_right_panel.py — v4 右栏面板测试

覆盖：
- TerminalWidget 输出追加与清空
- FileReaderWidget 打开不存在文件给出提示
- BrowserWidget / RightPanelWidget 标签切换
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from PySide6.QtWidgets import QApplication

from v4.legacy.right_panel import TerminalWidget, FileReaderWidget, RightPanelWidget
from v4.widgets.base import _THEMES


@pytest.fixture(scope="session")
def qt_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


class TestV4RightPanel:
    @pytest.fixture(autouse=True)
    def setup(self, qt_app):
        self.app = qt_app
        self.theme = _THEMES["dark"]
        yield

    def test_terminal_widget_append_and_clear(self):
        widget = TerminalWidget(self.theme)
        widget.append_output("hello")
        widget.append_output("world")
        self.app.processEvents()

        text = widget.output_edit.toPlainText()
        assert "hello" in text
        assert "world" in text

        widget.clear()
        self.app.processEvents()
        assert widget.output_edit.toPlainText() == ""

        widget.deleteLater()
        self.app.processEvents()

    def test_file_reader_shows_error_for_missing_file(self):
        widget = FileReaderWidget(self.theme)
        widget.open_file("/nonexistent/path/file.txt")
        self.app.processEvents()

        text = widget.editor.toPlainText()
        assert "[文件不存在]" in text

        widget.deleteLater()
        self.app.processEvents()

    def test_file_reader_displays_content(self, tmp_path):
        widget = FileReaderWidget(self.theme)
        test_file = tmp_path / "sample.txt"
        test_file.write_text("Hello, v4 UI!", encoding="utf-8")

        widget.open_file(str(test_file))
        self.app.processEvents()

        assert "Hello, v4 UI!" in widget.editor.toPlainText()
        assert str(test_file) in widget.path_label.text()

        widget.deleteLater()
        self.app.processEvents()

    def test_right_panel_switch_tab(self):
        widget = RightPanelWidget(self.theme)
        self.app.processEvents()

        assert widget.tabs.count() == 4
        widget.switch_tab("终端")
        self.app.processEvents()
        assert widget.tabs.currentIndex() == 1

        widget.switch_tab("浏览器")
        self.app.processEvents()
        assert widget.tabs.currentIndex() == 3

        widget.switch_tab("文件编辑器")
        self.app.processEvents()
        assert widget.tabs.currentIndex() == 2

        widget.deleteLater()
        self.app.processEvents()

    def test_right_panel_open_file_switches_to_file_reader(self, tmp_path):
        widget = RightPanelWidget(self.theme)
        test_file = tmp_path / "code.py"
        test_file.write_text("print('ok')", encoding="utf-8")

        widget.open_file(str(test_file))
        self.app.processEvents()

        assert widget.tabs.currentIndex() == 2  # 文件编辑器
        assert "print('ok')" in widget.file_reader.editor.toPlainText()

        widget.deleteLater()
        self.app.processEvents()
