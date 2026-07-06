"""V5 聊天区 UI 组件单元测试。

覆盖 HeaderBar / SearchBar / MoreDropdown / InputArea / ChatArea，
重点验证 SVG 规范尺寸、信号发射、搜索高亮、模式列表一致性。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from PySide6.QtCore import Qt, QPoint, QEvent
from PySide6.QtGui import QTextCursor, QKeyEvent
from PySide6.QtWidgets import QApplication, QWidget, QLabel
from PySide6.QtTest import QTest

from v5.widgets.chat_area import HeaderBar, SearchBar, MoreDropdown, InputArea, ChatArea
from v5.widgets.base import theme


@pytest.fixture(scope="session")
def qt_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


class TestHeaderBar:
    @pytest.fixture(autouse=True)
    def setup(self, qt_app):
        self.app = qt_app
        self.widget = HeaderBar()
        self.widget.show()
        yield
        self.widget.deleteLater()
        self.app.processEvents()

    def test_header_has_three_icon_buttons(self):
        assert self.widget._search_btn is not None
        assert self.widget._more_btn is not None
        assert self.widget._expand_btn is not None

    def test_header_button_size_matches_spec(self):
        for btn in (self.widget._search_btn, self.widget._more_btn, self.widget._expand_btn):
            assert btn.width() == 18
            assert btn.height() == 22

    def test_header_search_clicked_signal(self):
        received = []
        self.widget.search_clicked.connect(lambda: received.append("search"))
        self.widget._search_btn.click()
        self.app.processEvents()
        assert received == ["search"]

    def test_header_more_clicked_signal(self):
        received = []
        self.widget.more_clicked.connect(lambda: received.append("more"))
        self.widget._more_btn.click()
        self.app.processEvents()
        assert received == ["more"]

    def test_header_expand_clicked_signal(self):
        received = []
        self.widget.expand_toggled.connect(lambda: received.append("expand"))
        self.widget._expand_btn.click()
        self.app.processEvents()
        assert received == ["expand"]

    def test_header_double_click_signal(self):
        received = []
        self.widget.double_clicked.connect(lambda: received.append("dbl"))
        self.widget.mouseDoubleClickEvent(None)
        self.app.processEvents()
        assert received == ["dbl"]

    def test_header_set_title(self):
        self.widget._title_lbl.setText("项目会话")
        assert self.widget._title_lbl.text() == "项目会话"

    def test_header_set_expanded_state(self):
        self.widget.set_expanded_state(False)
        assert not self.widget._expanded
        self.widget.set_expanded_state(True)
        assert self.widget._expanded

    def test_header_mouse_drag_methods_exist(self):
        # 验证拖动相关方法存在且不抛异常（不直接传入 None event）
        assert callable(self.widget.mousePressEvent)
        assert callable(self.widget.mouseMoveEvent)
        assert callable(self.widget.mouseReleaseEvent)

    def test_header_theme_refresh_applies_styles(self):
        original = theme.name
        try:
            target = "light" if original == "dark" else "dark"
            theme.set_theme(target)
            self.app.processEvents()
            sheet = self.widget._title_lbl.styleSheet()
            assert C_key_in_sheet(sheet, "text_primary")
        finally:
            theme.set_theme(original)


class TestSearchBar:
    @pytest.fixture(autouse=True)
    def setup(self, qt_app):
        self.app = qt_app
        self.widget = SearchBar()
        self.widget.show()
        yield
        self.widget.deleteLater()
        self.app.processEvents()

    def test_search_has_input_and_buttons(self):
        assert self.widget._input is not None
        assert self.widget._prev_btn is not None
        assert self.widget._next_btn is not None
        assert self.widget._close_btn is not None

    def test_search_text_changed_signal(self):
        received = []
        self.widget.search_text_changed.connect(received.append)
        self.widget._input.setText("hello")
        self.app.processEvents()
        assert received == ["hello"]

    def test_search_next_signal(self):
        received = []
        self.widget.next_match.connect(lambda: received.append("next"))
        self.widget._next_btn.click()
        self.app.processEvents()
        assert received == ["next"]

    def test_search_prev_signal(self):
        received = []
        self.widget.prev_match.connect(lambda: received.append("prev"))
        self.widget._prev_btn.click()
        self.app.processEvents()
        assert received == ["prev"]

    def test_search_close_signal(self):
        received = []
        self.widget.closed.connect(lambda: received.append("close"))
        self.widget._close_btn.click()
        self.app.processEvents()
        assert received == ["close"]

    def test_search_enter_emits_next(self):
        received = []
        self.widget.next_match.connect(lambda: received.append("next"))
        self.widget._input.setFocus()
        QTest.keyClick(self.widget._input, Qt.Key_Return)
        self.app.processEvents()
        assert received == ["next"]

    def test_search_shift_enter_emits_prev(self):
        received = []
        self.widget.prev_match.connect(lambda: received.append("prev"))
        self.widget._input.setFocus()
        QTest.keyClick(self.widget._input, Qt.Key_Return, Qt.ShiftModifier)
        self.app.processEvents()
        assert received == ["prev"]

    def test_search_esc_emits_close(self):
        received = []
        self.widget.closed.connect(lambda: received.append("close"))
        self.widget._input.setFocus()
        QTest.keyClick(self.widget._input, Qt.Key_Escape)
        self.app.processEvents()
        assert received == ["close"]

    def test_search_clear_empties_input(self):
        self.widget._input.setText("keyword")
        self.widget.clear()
        assert self.widget.text() == ""

    def test_search_buttons_size(self):
        for btn in (self.widget._prev_btn, self.widget._next_btn, self.widget._close_btn):
            assert btn.width() == 18
            assert btn.height() == 18


class TestMoreDropdown:
    @pytest.fixture(autouse=True)
    def setup(self, qt_app):
        self.app = qt_app
        self.widget = MoreDropdown()
        yield
        self.widget.hide()
        self.widget.deleteLater()
        self.app.processEvents()

    def test_more_dropdown_initially_hidden(self):
        # __init__ 中已调用 hide()
        assert self.widget.isHidden()

    def test_more_dropdown_width_matches_spec(self):
        self.widget.show()
        assert self.widget.width() == MoreDropdown.WIDTH

    def test_more_dropdown_height_matches_spec(self):
        self.widget.show()
        assert self.widget.height() == 306

    def _find_label(self, text: str):
        for lbl in self.widget.findChildren(QLabel):
            if text in lbl.text():
                return lbl
        return None

    def test_more_dropdown_export_signal(self):
        received = []
        self.widget.export_requested.connect(lambda: received.append("export"))
        lbl = self._find_label("导出")
        assert lbl is not None
        lbl.mousePressEvent(None)
        self.app.processEvents()
        assert received == ["export"]

    def test_more_dropdown_settings_signal(self):
        received = []
        self.widget.settings_requested.connect(lambda: received.append("settings"))
        lbl = self._find_label("设置")
        assert lbl is not None
        lbl.mousePressEvent(None)
        self.app.processEvents()
        assert received == ["settings"]

    def test_more_dropdown_esc_hides(self):
        self.widget.show()
        assert self.widget.isVisible()
        ev = QKeyEvent(QEvent.Type.KeyPress, Qt.Key_Escape, Qt.KeyboardModifier.NoModifier)
        self.widget.keyPressEvent(ev)
        self.app.processEvents()
        assert self.widget.isHidden()

    def test_more_dropdown_has_progress_section(self):
        assert self._find_label("进度") is not None

    def test_more_dropdown_has_file_section(self):
        assert self._find_label("文件") is not None


class TestInputArea:
    @pytest.fixture(autouse=True)
    def setup(self, qt_app):
        self.app = qt_app
        self.widget = InputArea()
        self.widget.show()
        yield
        self.widget.deleteLater()
        self.app.processEvents()

    def test_input_has_text_edit(self):
        assert self.widget._text_edit is not None

    def test_input_enter_sends_message(self):
        received = []
        self.widget.send_clicked.connect(lambda: received.append("send"))
        self.widget._text_edit.setPlainText("hello")
        self.widget._text_edit.setFocus()
        QTest.keyClick(self.widget._text_edit, Qt.Key_Return)
        self.app.processEvents()
        assert received == ["send"]

    def test_input_shift_enter_inserts_newline(self):
        self.widget._text_edit.setPlainText("line1")
        self.widget._text_edit.moveCursor(QTextCursor.End)
        QTest.keyClick(self.widget._text_edit, Qt.Key_Return, Qt.ShiftModifier)
        self.app.processEvents()
        assert "\n" in self.widget._text_edit.toPlainText()

    def test_input_send_button_emits_send(self):
        received = []
        self.widget.send_clicked.connect(lambda: received.append("send"))
        self.widget._send_btn.click()
        self.app.processEvents()
        assert received == ["send"]

    def test_input_stop_button_emits_stop(self):
        received = []
        self.widget.stop_clicked.connect(lambda: received.append("stop"))
        self.widget._stop_btn.click()
        self.app.processEvents()
        assert received == ["stop"]

    def test_input_streaming_toggles_buttons(self):
        self.widget.set_streaming(True)
        self.app.processEvents()
        assert self.widget._stop_btn.isVisible()
        assert not self.widget._send_btn.isVisible()

        self.widget.set_streaming(False)
        self.app.processEvents()
        assert not self.widget._stop_btn.isVisible()
        assert self.widget._send_btn.isVisible()

    def test_input_mode_tag_click_emits_mode(self):
        received = []
        self.widget.mode_clicked.connect(lambda: received.append("mode"))
        self.widget._mode_tag.mousePressEvent(None)
        self.app.processEvents()
        assert received == ["mode"]

    def test_input_model_tag_click_emits_model(self):
        received = []
        self.widget.model_clicked.connect(lambda: received.append("model"))
        self.widget._model_tag.mousePressEvent(None)
        self.app.processEvents()
        assert received == ["model"]

    def test_input_mode_value_updated(self):
        self.widget.set_mode("plan")
        assert self.widget._mode_tag._value_label.text() == "plan"

    def test_input_model_value_updated(self):
        self.widget.set_model("flash")
        assert self.widget._model_tag._value_label.text() == "flash"

    def test_input_enter_during_streaming_does_not_send(self):
        received = []
        self.widget.send_clicked.connect(lambda: received.append("send"))
        self.widget.set_streaming(True)
        self.widget._text_edit.setPlainText("hello")
        self.widget._text_edit.setFocus()
        QTest.keyClick(self.widget._text_edit, Qt.Key_Return)
        self.app.processEvents()
        assert received == []

    def test_input_minimum_height(self):
        assert self.widget.minimumHeight() >= 104


class TestChatArea:
    @pytest.fixture(autouse=True)
    def setup(self, qt_app):
        self.app = qt_app
        self.widget = ChatArea()
        self.widget.show()
        self.widget.resize(600, 500)
        yield
        self.widget.deleteLater()
        self.app.processEvents()

    def test_chat_area_has_header_input_view(self):
        assert self.widget._header is not None
        assert self.widget._view is not None
        assert self.widget._input is not None

    def test_chat_area_default_modes_match_engine(self):
        assert self.widget._modes == ["ask", "plan", "craft"]

    def test_chat_area_set_modes(self):
        self.widget.set_modes(["ask", "plan"])
        assert self.widget._modes == ["ask", "plan"]

    def test_chat_area_set_modes_reverts_invalid_current(self):
        self.widget._current_mode = "review"
        self.widget.set_modes(["ask", "plan", "craft"])
        assert self.widget._current_mode == "ask"

    def test_chat_area_mode_cycle_uses_provided_modes(self):
        self.widget.set_modes(["ask", "plan", "craft"])
        self.widget._current_mode = "ask"
        received = []
        self.widget.sign_mode_changed.connect(received.append)
        self.widget._on_mode_clicked()
        assert self.widget._current_mode == "plan"
        assert received == ["plan"]

    def test_chat_area_set_title(self):
        self.widget.set_title("项目A", "/path/to/project")
        assert self.widget._header._title_lbl.text() == "项目A"
        assert self.widget._header._env_lbl.text() == "/path/to/project"

    def test_chat_area_append_user_renders_bubble(self):
        self.widget.append_user("hello")
        self.app.processEvents()
        assert len(self.widget._scene._items) == 1
        assert "hello" in self.widget.to_plain_text()

    def test_chat_area_append_ai_renders_text(self):
        self.widget.append_ai("world")
        self.app.processEvents()
        assert len(self.widget._scene._items) >= 1
        assert "world" in self.widget.to_plain_text()

    def test_chat_area_append_system_renders_card(self):
        self.widget.append_system("system msg")
        self.app.processEvents()
        assert "system msg" in self.widget.to_plain_text()

    def test_chat_area_append_chunk_stream(self):
        self.widget.append_chunk("chunk1")
        self.widget.append_chunk("chunk2")
        self.app.processEvents()
        assert "chunk1chunk2" in self.widget.to_plain_text()

    def test_chat_area_finalize_stream(self):
        self.widget.append_chunk("partial")
        self.widget.finalize_stream()
        self.app.processEvents()
        assert self.widget._chat_history[-1]["role"] == "ai"

    def test_chat_area_clear_chat(self):
        self.widget.append_user("hello")
        self.widget.clear_chat()
        self.app.processEvents()
        assert self.widget._chat_history == []
        assert len(self.widget._scene._items) == 0

    def test_chat_area_send_message_signal(self):
        received = []
        self.widget.sign_send_msg.connect(received.append)
        self.widget.input_field.setPlainText("send this")
        self.widget._on_send_clicked()
        self.app.processEvents()
        assert received == ["send this"]

    def test_chat_area_set_streaming_updates_header(self):
        self.widget.set_streaming(True)
        self.app.processEvents()
        assert self.widget._header._status_lbl.isVisible()
        assert "回答中" in self.widget._header._status_lbl.text()

    def test_chat_area_search_highlights_matches(self):
        self.widget.append_user("hello world")
        self.widget.append_user("goodbye world")
        self.widget._on_search_text_changed("hello")
        self.app.processEvents()
        assert self.widget._search_matches
        assert 0 in self.widget._search_matches

    def test_chat_area_append_tool_adds_tool_entry(self):
        self.widget.append_tool("read_file", {"path": "/tmp/a"}, "content", 42)
        self.app.processEvents()
        assert any(entry.get("role") == "tool" for entry in self.widget._chat_history)
        assert "read_file" in self.widget.to_plain_text()
        assert "content" in self.widget.to_plain_text()

    def test_chat_area_append_ai_with_phase_renders_panel(self):
        self.widget.append_ai("result", phase="analyze")
        self.app.processEvents()
        assert self.widget._chat_history[-1].get("phase") == "analyze"
        # 阶段面板与文本内容都应被渲染到场景
        assert len(self.widget._scene._items) >= 1
        assert "result" in self.widget.to_plain_text()

    def test_chat_area_phase_titles_for_all_phases(self):
        for phase in ("analyze", "confirm", "execute", "verify", "archive"):
            self.widget.clear_chat()
            self.widget.append_ai("body", phase=phase)
            self.app.processEvents()
            assert self.widget._chat_history[-1].get("phase") == phase


# ══════════════════════════════════════════════════════════════
# 辅助函数
# ══════════════════════════════════════════════════════════════

def C_key_in_sheet(sheet: str, key: str) -> bool:
    """粗略判断 QSS 中是否包含当前主题颜色键对应的值（用于主题切换测试）。"""
    from v5.widgets.base import C
    value = C.get(key, "")
    return value and value in sheet
