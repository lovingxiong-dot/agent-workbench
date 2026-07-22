"""v6/ui/chat_area.py — 中区组合组件。
设计来源：experiments/ui_template.py（Git 标签 v0.6-alpha）。"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGraphicsView,
    QLineEdit, QPushButton, QLabel, QSizePolicy,
)

from v6.ui.base import C, theme
from v6.ui.header_bar import HeaderBar
from v6.ui.input_area import InputArea
from v6.ui.chat_scene import ChatScene
from v6.ui.more_dropdown import MoreDropdown


class SearchBar(QWidget):
    """聊天搜索条：关键词输入、上一个/下一个、关闭。"""

    keyword_changed = Signal(str)
    navigate = Signal(int)
    closed = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedHeight(36)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        self._edit = QLineEdit()
        self._edit.setPlaceholderText("搜索...")
        self._edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._edit.textChanged.connect(self.keyword_changed.emit)
        layout.addWidget(self._edit)

        self._count = QLabel("0/0")
        layout.addWidget(self._count)

        for text, delta in (("◀", -1), ("▶", 1)):
            btn = QPushButton(text)
            btn.setFixedSize(26, 24)
            btn.clicked.connect(lambda _c, d=delta: self.navigate.emit(d))
            layout.addWidget(btn)

        close_btn = QPushButton("×")
        close_btn.setFixedSize(26, 24)
        close_btn.clicked.connect(self.closed.emit)
        layout.addWidget(close_btn)

    def set_count(self, current: int, total: int) -> None:
        self._count.setText(f"{current}/{total}")


class ChatArea(QWidget):
    """中区组合：标题栏 + 聊天场景 + 搜索条 + 输入区。"""

    send_msg = Signal(str)
    stop_msg = Signal()
    mode_changed = Signal(str)
    model_changed = Signal(str)
    export_requested = Signal()
    settings_requested = Signal()
    search_toggled = Signal()
    more_clicked = Signal(QPoint)
    toggle_right_panel = Signal()
    left_expand_toggled = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._modes = ["Agent", "Chat", "Coder"]
        self._mode_i = 0
        self._models = ["gpt-4o", "gpt-4o-mini", "claude-3.5"]
        self._model_i = 0
        self._matches: list = []
        self._match_idx = -1
        self._stream_item = None
        self._build()
        self._load_demo()
        self.refresh_theme()
        theme.changed.connect(self.refresh_theme)

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._header = HeaderBar(self)
        self._header.left_expand_toggled.connect(self.left_expand_toggled.emit)
        self._header.expand_toggled.connect(self.toggle_right_panel.emit)
        self._header.search_clicked.connect(self._toggle_search)
        self._header.more_clicked.connect(self._show_more)
        self._header.double_clicked.connect(self._on_header_dblclick)
        layout.addWidget(self._header)

        self._search = SearchBar(self)
        self._search.hide()
        self._search.keyword_changed.connect(self._on_search)
        self._search.navigate.connect(self._on_navigate)
        self._search.closed.connect(self._toggle_search)
        layout.addWidget(self._search)

        self._scene = ChatScene(self)
        self._view = QGraphicsView(self._scene, self)
        self._view.setFrameShape(QGraphicsView.Shape.NoFrame)
        self._view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._view.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        layout.addWidget(self._view, 1)

        self._analyze_bar = QWidget(self)
        ab_layout = QHBoxLayout(self._analyze_bar)
        ab_layout.setContentsMargins(0, 8, 0, 8)
        self._analyze_btn = QPushButton("帮我分析当前项目")
        self._analyze_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._analyze_btn.setFixedHeight(32)
        self._analyze_btn.clicked.connect(lambda: self.send_msg.emit("帮我分析当前项目"))
        ab_layout.addStretch(1)
        ab_layout.addWidget(self._analyze_btn)
        ab_layout.addStretch(1)
        layout.addWidget(self._analyze_bar)

        self._input = InputArea(self)
        self._input.set_mode(self._modes[self._mode_i])
        self._input.set_model(self._models[self._model_i])
        self._input.send_clicked.connect(self._on_send)
        self._input.stop_clicked.connect(self.stop_msg.emit)
        self._input.mode_tag_clicked.connect(self._cycle_mode)
        self._input.model_tag_clicked.connect(self._cycle_model)
        layout.addWidget(self._input)

        self._more = MoreDropdown(self)
        self._more.export_requested.connect(self.export_requested.emit)
        self._more.copy_link_requested.connect(lambda: None)
        self._more.settings_requested.connect(self.settings_requested.emit)
        self._more.devtools_requested.connect(lambda: None)

    def _load_demo(self) -> None:
        self._header.set_title("项目分析助手", "f:\\Agent\\agent_workbench")
        self.append_user("帮我分析当前项目，给出优化建议。")
        self.append_ai("已进入分析流程，我会按以下步骤进行：", "Analyze")
        self._scene.add_step(1, "扫描目录结构与关键文件。")
        self._scene.add_step(2, "识别潜在的性能与安全问题。")
        self._scene.add_bullet("主入口 main.py 逻辑清晰，建议增加类型注解。")
        self._scene.add_bullet("测试覆盖率不足，建议补充边界用例。")
        self._scene.add_tool("list_dir", {"files": ["main.py", "README.md", "tests"]}, "ok")
        self._scene.add_fold_block("详细日志", "已读取 3 个文件，共 240 行代码。")
        self._scene.add_system_card("系统消息", "分析完成，结果已自动保存。")
        self.append_ai("需要我帮你生成改进后的代码吗？")

    # ── Data Injection Methods（Presentation Contract → UI Shell）──

    def load_messages(self, messages: list) -> None:
        """从 MessageViewModel 列表注入消息数据。
        
        清除 demo 数据，替换为真实消息流。
        不修改任何视觉属性。
        """
        self._scene.clear()
        for msg in messages:
            if msg.role == "user":
                self._scene.add_user_message(msg.content)
            elif msg.role == "assistant":
                self._scene.add_ai_message(msg.content)
            elif msg.role == "tool":
                for tc in msg.tool_calls or []:
                    self._scene.add_tool(
                        tc.get("name", ""),
                        tc.get("result", {}),
                        tc.get("status", "ok"),
                    )
        self._view.verticalScrollBar().setValue(
            self._view.verticalScrollBar().maximum()
        )

    def load_models(self, models: list[str]) -> None:
        """从 ViewModel 列表注入模型选项。
        
        替换硬编码的模型列表。
        不修改任何视觉属性。
        """
        if models:
            self._models = models
            self._model_i = 0
            self._input.set_model(self._models[0])

    def set_title(self, title: str, subtitle: str) -> None:
        self._header.set_title(title, subtitle)

    def append_user(self, text: str) -> None:
        self._scene.add_user_message(text)
        self._view.verticalScrollBar().setValue(self._view.verticalScrollBar().maximum())

    def append_ai(self, text: str, phase: str = "") -> None:
        self._stream_item = self._scene.add_ai_message(text, phase)
        self._view.verticalScrollBar().setValue(self._view.verticalScrollBar().maximum())

    def stream_chunk(self, text: str) -> None:
        if self._stream_item is None:
            self._stream_item = self._scene.add_ai_message("")
        if hasattr(self._stream_item, "_raw"):
            self._stream_item._raw += text
            self._stream_item.refresh_theme()
        self._view.verticalScrollBar().setValue(self._view.verticalScrollBar().maximum())

    def stream_end(self) -> None:
        self._stream_item = None
        self.set_streaming(False)

    def set_streaming(self, streaming: bool) -> None:
        self._input.set_running(streaming)

    def set_analyze_button_visible(self, visible: bool) -> None:
        self._analyze_bar.setVisible(visible)

    def tool_executed(self, name: str, result: dict, status: str = "ok", elapsed_ms: int = 0) -> None:
        self._scene.add_tool(name, result, status)

    def confirm_required(self, tool: str, command: str) -> None:
        self._scene.add_system_card("确认请求", f"{tool}: {command}")

    def _on_send(self) -> None:
        text = self._input.text().strip()
        if text:
            self.append_user(text)
            self.send_msg.emit(text)
            self._input.clear_text()

    def _cycle_mode(self) -> None:
        self._mode_i = (self._mode_i + 1) % len(self._modes)
        mode = self._modes[self._mode_i]
        self._input.set_mode(mode)
        self.mode_changed.emit(mode)

    def _cycle_model(self) -> None:
        self._model_i = (self._model_i + 1) % len(self._models)
        model = self._models[self._model_i]
        self._input.set_model(model)
        self.model_changed.emit(model)

    def _toggle_search(self) -> None:
        visible = not self._search.isVisible()
        self._search.setVisible(visible)
        if visible:
            self._search._edit.setFocus()
        else:
            self._search._edit.clear()
        self.search_toggled.emit()

    def _on_search(self, keyword: str) -> None:
        self._scene.set_keyword(keyword)
        self._matches = self._scene.match_items()
        self._match_idx = 0 if self._matches else -1
        self._search.set_count(self._match_idx + 1 if self._matches else 0, len(self._matches))
        if self._matches:
            self._view.ensureVisible(self._matches[0])

    def _on_navigate(self, delta: int) -> None:
        if not self._matches:
            return
        self._match_idx = (self._match_idx + delta) % len(self._matches)
        self._search.set_count(self._match_idx + 1, len(self._matches))
        self._view.ensureVisible(self._matches[self._match_idx])

    def _show_more(self, pos: QPoint) -> None:
        self.more_clicked.emit(pos)
        self._more.show_at(pos)

    def _on_header_dblclick(self) -> None:
        win = self.window()
        if win.isMaximized():
            win.showNormal()
        else:
            win.showMaximized()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_F and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self._toggle_search()
            event.accept()
            return
        super().keyPressEvent(event)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._scene.set_width(max(self._view.viewport().width(), 200))

    def refresh_theme(self) -> None:
        self.setStyleSheet(f"background-color: {C['bg_primary']};")
        self._view.setStyleSheet(f"background-color: {C['bg_primary']}; border: none;")
        self._analyze_btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['btn_bg']}; color: {C['text_primary']}; "
            f"border: 1px solid {C['border']}; border-radius: 16px; padding: 0 16px; "
            f"font-size: 13px; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; }}"
        )
        self._search.setStyleSheet(
            f"SearchBar {{ background-color: {C['bg_card']}; border-bottom: 1px solid {C['border']}; }}"
            f"QLineEdit {{ background-color: {C['bg_input']}; color: {C['text_primary']}; "
            f"border: 1px solid {C['border']}; border-radius: 4px; padding: 2px 6px; }}"
            f"QLabel {{ color: {C['text_secondary']}; }}"
            f"QPushButton {{ background-color: {C['btn_bg']}; color: {C['text_primary']}; "
            f"border: 1px solid {C['border']}; border-radius: 4px; }}"
            f"QPushButton:hover {{ background-color: {C['btn_hover']}; }}"
        )


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication, QMainWindow
    from PySide6.QtCore import QTimer

    app = QApplication(sys.argv)
    win = QMainWindow()
    win.setWindowFlags(Qt.WindowType.FramelessWindowHint)
    win.resize(800, 700)
    area = ChatArea()
    win.setCentralWidget(area)
    win.show()
    QTimer.singleShot(500, win.close)
    sys.exit(app.exec())
