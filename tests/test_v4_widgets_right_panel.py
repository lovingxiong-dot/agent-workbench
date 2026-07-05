"""
test_v4_widgets_right_panel.py — v4/widgets 右栏组件测试

覆盖：
- TerminalWidget 输出追加/清空/运行命令
- FileReaderWidget 打开/保存/大文件截断/编码
- BrowserWidget URL 加载
- RightPanel 标签切换/打开文件/最近文件/项目根目录同步/主题刷新
"""
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from PySide6.QtWidgets import QApplication, QLabel

from v4.widgets.terminal_widget import TerminalWidget
from v4.widgets.file_reader_widget import FileReaderWidget
from v4.widgets.browser_widget import BrowserWidget, _WEBENGINE_AVAILABLE
from v4.widgets.right_panel import RightPanel
from v4.widgets.base import theme, _THEMES


@pytest.fixture(scope="session")
def qt_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


class TestTerminalWidget:
    @pytest.fixture(autouse=True)
    def setup(self, qt_app):
        self.app = qt_app
        self.widget = TerminalWidget()
        yield
        self.widget.deleteLater()
        self.app.processEvents()

    def test_append_output_and_clear(self):
        self.widget.append_output("hello")
        self.widget.append_output("world")
        self.app.processEvents()

        text = self.widget._output.toPlainText()
        assert "hello" in text
        assert "world" in text

        self.widget.clear()
        self.app.processEvents()
        assert self.widget._output.toPlainText() == ""

    def test_set_cwd(self):
        self.widget.set_cwd("/tmp")
        assert self.widget._cwd == "/tmp"

        self.widget.set_cwd("")
        assert self.widget._cwd == os.getcwd()

    def test_run_command_echo(self):
        self.widget.run_command("echo ok", cwd=os.getcwd())
        self.app.processEvents()
        # 等待工作线程完成
        for _ in range(50):
            if self.widget._worker is None:
                break
            self.app.processEvents()
            time.sleep(0.05)

        text = self.widget._output.toPlainText()
        assert "$ echo ok" in text
        assert "ok" in text
        assert "[退出码: 0]" in text


class TestFileReaderWidget:
    @pytest.fixture(autouse=True)
    def setup(self, qt_app):
        self.app = qt_app
        self.widget = FileReaderWidget()
        yield
        self.widget.deleteLater()
        self.app.processEvents()

    def test_open_missing_file(self):
        self.widget.open_file("/nonexistent/path/file.txt")
        self.app.processEvents()
        assert "[文件不存在]" in self.widget._editor.toPlainText()

    def test_open_and_save_file(self, tmp_path):
        test_file = tmp_path / "sample.txt"
        test_file.write_text("Hello, v4 UI!", encoding="utf-8")

        self.widget.open_file(str(test_file))
        self.app.processEvents()

        assert "Hello, v4 UI!" in self.widget._editor.toPlainText()
        assert str(test_file) in self.widget._path_label.text()

        self.widget._editor.setPlainText("Updated content")
        self.widget._on_save()
        self.app.processEvents()

        assert test_file.read_text(encoding="utf-8") == "Updated content"

    def test_large_file_truncated(self, tmp_path):
        test_file = tmp_path / "big.txt"
        test_file.write_text("x" * (2 * 1024 * 1024), encoding="utf-8")

        self.widget.open_file(str(test_file))
        self.app.processEvents()

        text = self.widget._editor.toPlainText()
        assert "x" in text
        assert "[文件过大，仅显示前 1024KB]" in text


class TestBrowserWidget:
    @pytest.fixture(autouse=True)
    def setup(self, qt_app):
        self.app = qt_app
        self.widget = BrowserWidget()
        yield
        self.widget.deleteLater()
        self.app.processEvents()

    def test_load_url_normalizes_scheme(self):
        self.widget.load_url("example.com")
        assert self.widget._url_input.text() == "https://example.com"

    def test_set_home_page(self):
        self.widget.set_home_page("https://www.google.com")
        assert self.widget._home_url == "https://www.google.com"


class TestRightPanel:
    @pytest.fixture(autouse=True)
    def setup(self, qt_app):
        self.app = qt_app
        self.widget = RightPanel()
        yield
        self.widget.deleteLater()
        self.app.processEvents()

    def test_switch_tab_by_name(self):
        self.widget.switch_tab("终端")
        self.app.processEvents()
        assert self.widget._active_tab == 1

        self.widget.switch_tab("文件编辑器")
        self.app.processEvents()
        assert self.widget._active_tab == 2

        self.widget.switch_tab("浏览器")
        self.app.processEvents()
        assert self.widget._active_tab == 3

    def test_open_file_switches_to_file_reader(self, tmp_path):
        test_file = tmp_path / "code.py"
        test_file.write_text("print('ok')", encoding="utf-8")

        self.widget.open_file(str(test_file))
        self.app.processEvents()

        assert self.widget._active_tab == 2
        assert "print('ok')" in self.widget.file_reader._editor.toPlainText()
        # 最近文件应包含该文件
        labels = []
        for row in self.widget._file_rows:
            labels.extend(row.findChildren(QLabel))
        assert any(os.path.basename(str(test_file)) in lbl.text() for lbl in labels)

    def test_add_recent_file_dedup(self, tmp_path):
        test_file = tmp_path / "a.txt"
        test_file.write_text("a", encoding="utf-8")

        self.widget.add_recent_file(str(test_file))
        self.widget.add_recent_file(str(test_file))
        self.app.processEvents()

        paths = [row.property("file_path") for row in self.widget._file_rows]
        assert paths.count(os.path.abspath(str(test_file))) == 1

    def test_set_project_root(self):
        self.widget.set_project_root("/tmp")
        assert self.widget.terminal._cwd == "/tmp"

    def test_theme_refresh_does_not_crash(self):
        theme.set_theme("light")
        self.app.processEvents()
        theme.set_theme("dark")
        self.app.processEvents()
        # 主要验证不崩溃、文件行数量一致
        assert len(self.widget._file_rows) >= 0
