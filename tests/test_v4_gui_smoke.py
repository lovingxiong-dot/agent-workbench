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

    def test_three_column_layout_initial_state(self):
        """验证三栏布局初始尺寸与右栏标签页数量。"""
        window = MainWindow()
        self.app.processEvents()

        # 左栏固定 220px，右栏固定 400px；splitter 保证存在三栏
        assert window._left_panel.width() == 220
        assert window._right_panel.width() == 400
        sizes = window.splitter.sizes()
        assert len(sizes) == 3, "应存在三栏"

        # 右栏四个标签页
        assert window.right_panel.tabs.count() == 4, "右栏应包含 4 个标签页"
        tab_texts = [window.right_panel.tabs.tabText(i).lower() for i in range(window.right_panel.tabs.count())]
        assert "v4 架构" in tab_texts
        assert "终端" in tab_texts
        assert "文件编辑器" in tab_texts or "文件读取器" in tab_texts
        assert "浏览器" in tab_texts

        window.close()
        window.deleteLater()
        self.app.processEvents()

    def test_new_task_button_does_not_create_empty_session(self):
        window = MainWindow()
        initial_count = len(window._repo.list_sessions())

        # 反复点击「+ 新任务」按钮，不应创建空会话
        window.conversation_list.new_task_btn.click()
        self.app.processEvents()
        window.conversation_list.new_task_btn.click()
        self.app.processEvents()
        window.conversation_list.new_task_btn.click()
        self.app.processEvents()

        final_count = len(window._repo.list_sessions())
        assert final_count == initial_count, (
            f"空点击不应创建会话，期望 {initial_count}，实际 {final_count}"
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

            assert window.conversation_list.theme_btn.text() == expected_emoji

            # 记录切换前的样式，用于验证切换后确实变化
            chat_area_before = window.chat_area.chat_area.styleSheet()
            sidebar_before = window.conversation_list.styleSheet()

            window.conversation_list.theme_btn.click()
            self.app.processEvents()

            # 按钮图标、配置、UI 样式均应变更为对应主题
            assert window.conversation_list.theme_btn.text() == other_emoji
            assert window._config.get("app.theme") == other_theme
            assert window.chat_area.chat_area.styleSheet() != chat_area_before
            assert window.conversation_list.styleSheet() != sidebar_before
        finally:
            # 恢复原始主题，避免影响其他测试和真实配置文件
            window._config.set("app.theme", original_theme)
            window._config.save()
            window.close()
            window.deleteLater()
            self.app.processEvents()
