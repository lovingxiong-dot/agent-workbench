"""v4 主窗口 — 门面角色：初始化核心组件 + 组合 UI 子系统 + 信号桥接"""
import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QSplitter,
    QFileDialog, QInputDialog, QMessageBox,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPalette

from .repository import SessionRepository, _get_app_root
from .event_bus import MessageBus
from .orchestrator import SessionOrchestrator
from .ui_renderer import UIRenderer
from .worker_manager import WorkerManager
from services.config_service import ConfigService
from .events import (
    UserSendEvent, UserStopEvent, UserConfirmEvent,
    SessionSwitchEvent, SessionDeleteEvent, SessionPinEvent,
    SessionCreateEvent, SessionRenameEvent,
)
from .widgets import (
    ThemeManager, theme, _THEMES, C, qcolor, install_invisible_handles,
    EdgeResizeWidget, LeftPanel, ChatArea, RightPanel,
)


class MainWindow(QMainWindow):
    def __init__(self, worker_mgr=None):
        super().__init__(None, Qt.FramelessWindowHint)
        self.resize(1400, 900)
        self.setMinimumWidth(1200)
        self._right_visible = True
        self._drag_pos = None
        self._corner_radius = 8

        self._config = ConfigService(config_path="config/config.yaml")
        self.setWindowTitle(self._config.get("app.version", "Agent Workbench"))
        self._theme_name = self._config.get("app.theme", theme.name)
        if self._theme_name not in _THEMES:
            self._theme_name = theme.name
        theme.set_theme(self._theme_name)

        self._repo = SessionRepository()
        self._bus = MessageBus(trace=False)
        self._bus.connect_dispatch()

        self._engines = self._init_engines()
        self._worker_mgr = worker_mgr or WorkerManager(
            message_bus=self._bus,
            parent=self,
        )

        self._orchestrator = SessionOrchestrator(
            repository=self._repo,
            message_bus=self._bus,
            worker_manager=self._worker_mgr,
            parent=self,
        )

        self._setup_ui()

        self._ui_renderer = UIRenderer(
            message_bus=self._bus,
            chat_view=self._center,
            conversation_list=self._left,
            right_panel=self._right,
            current_session_provider=lambda: self._orchestrator.current_session_id or "",
            parent=self,
        )

        self._draft_session_type = "chat"
        self._draft_project_path = ""
        self._current_model_name = self._config.get("app.last_model", "tool-agent")
        self._current_mode = self._config.get("app.last_mode", "ask")

        self._connect_signals()
        self._init_default_session()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_rounded_mask()
        self._update_edge_positions()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        ml = QHBoxLayout(central)
        ml.setContentsMargins(0, 0, 0, 0)
        ml.setSpacing(0)

        self._splitter = QSplitter(Qt.Horizontal)
        self._splitter.setHandleWidth(1)
        install_invisible_handles(self._splitter)

        self._left = LeftPanel()
        self._left.setMinimumWidth(180)
        self._left.setMaximumWidth(220)
        self._splitter.addWidget(self._left)

        self._center = ChatArea()
        self._center.setMinimumWidth(280)
        self._splitter.addWidget(self._center)

        self._right = RightPanel()
        self._right.setMinimumWidth(200)
        self._right.set_window_buttons(self.showMinimized, self._toggle_maximize, self.close)
        self._splitter.addWidget(self._right)

        self._splitter.setSizes([220, 404, 400])
        self._splitter.setStretchFactor(0, 0)
        self._splitter.setStretchFactor(1, 1)
        self._splitter.setStretchFactor(2, 0)
        self._splitter.splitterMoved.connect(self._on_splitter_moved)
        ml.addWidget(self._splitter)

        theme.changed.connect(self._apply_theme_palette)
        self._apply_theme_palette()

        from PySide6.QtCore import Qt as QtEdge
        self._edge_widgets = [
            EdgeResizeWidget(QtEdge.TopEdge | QtEdge.LeftEdge, Qt.SizeFDiagCursor, central),
            EdgeResizeWidget(QtEdge.TopEdge, Qt.SizeVerCursor, central),
            EdgeResizeWidget(QtEdge.TopEdge | QtEdge.RightEdge, Qt.SizeBDiagCursor, central),
            EdgeResizeWidget(QtEdge.LeftEdge, Qt.SizeHorCursor, central),
            EdgeResizeWidget(QtEdge.RightEdge, Qt.SizeHorCursor, central),
            EdgeResizeWidget(QtEdge.BottomEdge | QtEdge.LeftEdge, Qt.SizeBDiagCursor, central),
            EdgeResizeWidget(QtEdge.BottomEdge, Qt.SizeVerCursor, central),
            EdgeResizeWidget(QtEdge.BottomEdge | QtEdge.RightEdge, Qt.SizeFDiagCursor, central),
        ]
        self._update_edge_positions()

    def _update_edge_positions(self):
        S = EdgeResizeWidget.SIZE
        W, H = self.width(), self.height()
        tl, t, tr, l, r, bl, b, br = self._edge_widgets
        tl.place(0, 0, S, S)
        t.place(S, 0, W - 2 * S, S)
        tr.place(W - S, 0, S, S)
        l.place(0, S, S, H - 2 * S)
        r.place(W - S, S, S, H - 2 * S)
        bl.place(0, H - S, S, S)
        b.place(S, H - S, W - 2 * S, S)
        br.place(W - S, H - S, S, S)

    def _on_splitter_moved(self, pos, index):
        QTimer.singleShot(0, self._center._rebuild_content)

    def _toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def _apply_rounded_mask(self):
        from PySide6.QtGui import QBitmap, QPainterPath, QPainter
        r = self._corner_radius
        path = QPainterPath()
        rect = self.rect()
        path.addRoundedRect(rect, r, r)
        mask = QBitmap(self.size())
        mask.fill(Qt.color0)
        p = QPainter(mask)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillPath(path, Qt.color1)
        p.end()
        self.setMask(mask)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() == Qt.LeftButton:
            delta = event.globalPosition().toPoint() - self._drag_pos
            self.move(self.pos() + delta)
            self._drag_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def _apply_theme_palette(self):
        app = QApplication.instance()
        from PySide6.QtWidgets import QStyleFactory
        app.setStyle(QStyleFactory.create("Fusion"))
        p = QPalette()
        p.setColor(QPalette.Window, qcolor(C["bg_primary"]))
        p.setColor(QPalette.WindowText, qcolor(C["text_primary"]))
        p.setColor(QPalette.Base, qcolor(C["bg_primary"]))
        p.setColor(QPalette.Button, qcolor(C["bg_sidebar"]))
        p.setColor(QPalette.Highlight, qcolor(C["accent"]))
        app.setPalette(p)

    def _init_engines(self) -> dict:
        from agent_engine.llm_registry import LLMRegistry
        from agent_engine.engines import (
            PromptEngine, InferenceEngine, ToolEngine,
            MemoryEngine, MetricsEngine, PolicyEngine,
        )
        config = self._config.config if self._config else {}
        registry = LLMRegistry("config/config.yaml", "config/config.yaml")
        policy = PolicyEngine(config.get("ai_engine", {}))
        metrics = MetricsEngine()
        engines = {
            "registry": registry, "policy": policy, "metrics": metrics,
            "prompt": PromptEngine(
                base_prompts={m: c.get("system_prompt", "") for m, c in config.get("manual_modes", {}).items()},
                user_rules=config.get("user_rules", []),
                app_version=config.get("app", {}).get("version", "v5.0"),
            ),
            "inference": InferenceEngine(policy_engine=policy, metrics_engine=metrics, llm_registry=registry),
            "tool": ToolEngine(),
            "memory": MemoryEngine(
                app_root=_get_app_root(),
                config=config.get("self_context", {}), policy_engine=policy,
            ),
        }
        return engines

    def _connect_signals(self):
        self._center._input.send_clicked.connect(self._on_send)
        self._center._input.mode_clicked.connect(self._on_mode_tag_clicked)
        self._center._input.model_clicked.connect(self._on_model_tag_clicked)

        self._left.new_session_requested.connect(self._on_new_session)
        self._left.session_action_requested.connect(self._on_session_action)
        self._left.session_selected.connect(self._on_session_selected)
        self._left.search_text_changed.connect(self._on_search_text_changed)
        self._left.theme_toggled.connect(self._on_theme_changed)

        self._center._header.left_expand_toggled.connect(self._toggle_left_panel)
        self._center._header.expand_toggled.connect(self._toggle_right_panel)
        self._center._header.double_clicked.connect(self._toggle_maximize)

    def _init_default_session(self):
        self._draft_session_type = "chat"
        self._draft_project_path = ""
        self._center._input.set_mode(self._current_mode)
        self._center._input.set_model(self._current_model_name)
        self._left._theme_btn.setText("☀️" if theme.name == "light" else "🌙")
        if hasattr(self._orchestrator, "clear_current"):
            self._orchestrator.clear_current()

    def _current_session_id(self) -> str:
        return self._orchestrator.current_session_id or ""

    def _on_send(self):
        text = self._center._input._text_edit.toPlainText().strip()
        if not text:
            return
        self._bus.emit(UserSendEvent(
            session_id=self._current_session_id(),
            user_text=text,
            mode=self._current_mode,
            session_type=self._draft_session_type,
            project_path=self._draft_project_path,
            model=self._current_model_name,
        ))
        self._center._input._text_edit.clear()

    def _on_new_session(self, session_type="chat"):
        self._draft_session_type = session_type
        if session_type == "work":
            self._draft_project_path = ""
        self._bus.emit(SessionCreateEvent(
            title="新对话",
            session_type=session_type,
            project_path=self._draft_project_path,
            mode=self._current_mode,
            model=self._current_model_name,
        ))

    def _on_session_selected(self, idx):
        sid = self._left._idx_to_sid.get(idx)
        if sid:
            self._bus.emit(SessionSwitchEvent(new_session_id=sid))

    def _on_session_action(self, action, idx):
        sid = self._left._idx_to_sid.get(idx)
        if not sid:
            return
        if action == "new":
            self._on_new_session("chat")
        elif action == "project":
            path = QFileDialog.getExistingDirectory(self, "选择项目路径")
            if path:
                self._draft_project_path = path
                self._bus.emit(SessionCreateEvent(
                    title="项目会话",
                    session_type="work",
                    project_path=path,
                    mode=self._current_mode,
                    model=self._current_model_name,
                ))
        elif action == "rename":
            meta = self._repo.get_session(sid)
            old = meta.title if meta else "未命名"
            new, ok = QInputDialog.getText(self, "重命名会话", "新名称：", text=old)
            if ok and new.strip():
                self._bus.emit(SessionRenameEvent(session_id=sid, new_title=new.strip()))
        elif action == "delete":
            ret = QMessageBox.question(self, "删除会话", "确定删除该会话？")
            if ret == QMessageBox.Yes:
                self._bus.emit(SessionDeleteEvent(session_id=sid))
        elif action == "pin":
            meta = self._repo.get_session(sid)
            if meta:
                self._bus.emit(SessionPinEvent(session_id=sid, pinned=not meta.pinned))

    def _on_search_text_changed(self, text):
        pass

    def _on_mode_tag_clicked(self):
        pass

    def _on_model_tag_clicked(self):
        pass

    def _on_theme_changed(self, theme_name):
        self._config.set("app.theme", theme_name)
        self._config.save()

    def _get_project_path(self):
        return ""

    def _toggle_left_panel(self):
        if self._left.isVisible():
            self._left.hide()
            total = self.width()
            rw = self._right.width() if self._right_visible else 0
            self._splitter.setSizes([0, total - rw, rw])
        else:
            self._left.show()
            rw = 400 if self._right_visible else 0
            self._splitter.setSizes([220, self.width() - 220 - rw, rw])
        QApplication.processEvents()
        self._center._rebuild_content()

    def _toggle_right_panel(self):
        if self._right_visible:
            self._right.hide()
            total = self.width()
            self._splitter.setSizes([220, total - 220, 0])
            self._right_visible = False
        else:
            self._right.show()
            self._splitter.setSizes([220, 404, 400])
            self._right_visible = True
        QApplication.processEvents()
        self._center._rebuild_content()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Agent Workbench")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
