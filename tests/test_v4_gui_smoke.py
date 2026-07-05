"""
Smoke test for v5 MainWindow (new UI) startup and basic interactions.
Does not require a display; uses QCoreApplication event loop with timers.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from PySide6.QtCore import QCoreApplication, QTimer
from PySide6.QtWidgets import QApplication

from v4.main_window import MainWindow
from v4.events import SessionCreateEvent


class TestV5GUISmoke:
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

    def test_three_column_layout_initial_state(self):
        """验证三栏布局初始尺寸与右栏标签页数量。"""
        window = MainWindow()
        window.show()
        self.app.processEvents()

        # 左栏固定 220px，右栏固定 400px；splitter 保证存在三栏
        assert window._left.width() == 220
        assert window._right.width() == 400
        sizes = window._splitter.sizes()
        assert len(sizes) == 3, "应存在三栏"

        # 右栏四个标签页
        assert len(window._right._tab_btns) == 4, "右栏应包含 4 个标签页"
        tab_texts = [btn.text().lower() for btn in window._right._tab_btns]
        assert "v4 架构" in tab_texts
        assert "终端" in tab_texts
        assert "文件编辑器" in tab_texts or "文件读取器" in tab_texts
        assert "浏览器" in tab_texts

        window.close()
        window.deleteLater()
        self.app.processEvents()

    def test_new_session_button_creates_session(self):
        """点击「+ 新会话」应创建新会话。"""
        window = MainWindow()
        initial_count = len(window._repo.list_sessions())

        window._left._new_btn.click()
        self.app.processEvents()
        window._left._new_btn.click()
        self.app.processEvents()
        window._left._new_btn.click()
        self.app.processEvents()

        final_count = len(window._repo.list_sessions())
        assert final_count == initial_count + 3, (
            f"每次点击应创建一个会话，期望 {initial_count + 3}，实际 {final_count}"
        )

        window.close()
        window.deleteLater()
        self.app.processEvents()

    def test_theme_toggle_button_switches_and_persists(self):
        """点击主题按钮可在 dark/light 间切换，并持久化到 config.yaml。"""
        from services.config_service import ConfigService
        original_theme = ConfigService(config_path="config/config.yaml").get("app.theme", "dark")

        window = MainWindow()
        self.app.processEvents()

        try:
            initial_theme = window._config.get("app.theme", "dark")
            expected_emoji = "🌙" if initial_theme == "dark" else "☀️"
            other_theme = "light" if initial_theme == "dark" else "dark"
            other_emoji = "☀️" if other_theme == "light" else "🌙"

            assert window._left._theme_btn.text() == expected_emoji

            sidebar_before = window._left.styleSheet()

            window._left._theme_btn.click()
            self.app.processEvents()

            # 按钮图标、配置、UI 样式均应变更为对应主题
            assert window._left._theme_btn.text() == other_emoji
            assert window._config.get("app.theme") == other_theme
            assert window._left.styleSheet() != sidebar_before
        finally:
            # 恢复原始主题，避免影响其他测试和真实配置文件
            window._config.set("app.theme", original_theme)
            window._config.save()
            window.close()
            window.deleteLater()
            self.app.processEvents()
