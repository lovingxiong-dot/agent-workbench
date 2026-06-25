from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QMenu, QInputDialog, QFrame,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QAction


class ConversationListWidget(QWidget):
    """分栏对话列表：当前项目对话 / 全局纯对话"""

    conversation_selected = Signal(str)
    new_conversation = Signal(str)      # 参数为 project_path，空字符串表示全局纯对话
    conversation_deleted = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # 标题
        header = QLabel("对话")
        header.setObjectName("panelHeader")
        layout.addWidget(header)

        # 新建按钮行
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        self.project_new_btn = QPushButton("+ 项目新对话")
        self.project_new_btn.setObjectName("newChatBtn")
        self.project_new_btn.setCursor(Qt.PointingHandCursor)
        self.project_new_btn.setToolTip("在当前项目目录下创建新对话")
        self.project_new_btn.clicked.connect(lambda: self.new_conversation.emit("<project>"))
        btn_row.addWidget(self.project_new_btn)

        self.global_new_btn = QPushButton("+ 纯对话")
        self.global_new_btn.setObjectName("newChatBtn")
        self.global_new_btn.setCursor(Qt.PointingHandCursor)
        self.global_new_btn.setToolTip("创建不绑定任何目录的纯对话")
        self.global_new_btn.setStyleSheet("""
            QPushButton {
                background-color: #21262D; color: #E6EDF3; border: 1px solid #30363D;
                border-radius: 6px; padding: 6px 10px; font-size: 12px; font-weight: 500;
            }
            QPushButton:hover { background-color: #30363D; border: 1px solid #58A6FF; }
        """)
        self.global_new_btn.clicked.connect(lambda: self.new_conversation.emit(""))
        btn_row.addWidget(self.global_new_btn)
        layout.addLayout(btn_row)

        # ── 当前项目对话 ─────────────────────────
        self.project_header = QLabel("当前项目")
        self.project_header.setObjectName("sectionHeader")
        self.project_header.setStyleSheet("color: #58A6FF; font-size: 11px; font-weight: bold; padding: 4px 8px;")
        layout.addWidget(self.project_header)

        self.project_list = QListWidget()
        self.project_list.setObjectName("conversationList")
        self.project_list.itemClicked.connect(self._on_project_item_clicked)
        self.project_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.project_list.customContextMenuRequested.connect(
            lambda pos: self._on_context_menu(self.project_list, pos)
        )
        layout.addWidget(self.project_list, 1)

        # 分隔线
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: #30363D;")
        layout.addWidget(sep)

        # ── 全局纯对话 ───────────────────────────
        global_header = QLabel("全局对话")
        global_header.setObjectName("sectionHeader")
        global_header.setStyleSheet("color: #8B949E; font-size: 11px; font-weight: bold; padding: 4px 8px;")
        layout.addWidget(global_header)

        self.global_list = QListWidget()
        self.global_list.setObjectName("conversationList")
        self.global_list.itemClicked.connect(self._on_global_item_clicked)
        self.global_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.global_list.customContextMenuRequested.connect(
            lambda pos: self._on_context_menu(self.global_list, pos)
        )
        layout.addWidget(self.global_list, 1)

    def set_project_label(self, path: str):
        """更新当前项目标题显示"""
        display = path if len(path) < 30 else "..." + path[-27:]
        self.project_header.setText(f"当前项目: {display}")
        self.project_header.setToolTip(path)

    def add_conversation(self, session_id, title, project_path=None, active=False):
        """添加对话；根据 project_path 决定放到哪一栏"""
        item = QListWidgetItem(title)
        item.setData(Qt.UserRole, session_id)
        item.setToolTip(title)
        if project_path:
            self.project_list.addItem(item)
            if active:
                self.project_list.setCurrentItem(item)
        else:
            self.global_list.addItem(item)
            if active:
                self.global_list.setCurrentItem(item)
        if active:
            self._style_active_item(item)

    def set_active(self, session_id):
        """高亮指定会话，并清除其他项的高亮样式"""
        for lst in (self.project_list, self.global_list):
            for i in range(lst.count()):
                item = lst.item(i)
                if item.data(Qt.UserRole) == session_id:
                    lst.setCurrentItem(item)
                    self._style_active_item(item)
                else:
                    item.setForeground(QColor("#E6EDF3"))

    def clear_conversations(self):
        """清空两栏"""
        self.project_list.clear()
        self.global_list.clear()

    def _style_active_item(self, item):
        item.setForeground(QColor("#58A6FF"))

    def _on_project_item_clicked(self, item):
        self.global_list.clearSelection()
        self.conversation_selected.emit(item.data(Qt.UserRole))

    def _on_global_item_clicked(self, item):
        self.project_list.clearSelection()
        self.conversation_selected.emit(item.data(Qt.UserRole))

    def _on_context_menu(self, list_widget, pos):
        item = list_widget.itemAt(pos)
        if not item:
            return
        menu = QMenu(self)
        rename = QAction("重命名", self)
        delete = QAction("删除", self)
        rename.triggered.connect(lambda: self._rename_item(item))
        delete.triggered.connect(lambda: self.conversation_deleted.emit(item.data(Qt.UserRole)))
        menu.addAction(rename)
        menu.addAction(delete)
        menu.exec(list_widget.mapToGlobal(pos))

    def _rename_item(self, item):
        text, ok = QInputDialog.getText(self, "重命名对话", "名称:", text=item.text())
        if ok and text.strip():
            item.setText(text.strip())
            item.setToolTip(text.strip())

    def remove_conversation(self, session_id):
        for lst in (self.project_list, self.global_list):
            for i in range(lst.count()):
                item = lst.item(i)
                if item.data(Qt.UserRole) == session_id:
                    lst.takeItem(i)
                    return
