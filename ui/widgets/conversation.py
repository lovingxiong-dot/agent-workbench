from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QListWidget, QListWidgetItem, QMenu, QInputDialog
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QAction


class ConversationListWidget(QWidget):
    new_conversation = Signal()
    conversation_selected = Signal(str)
    conversation_deleted = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        header = QLabel("对话")
        header.setObjectName("panelHeader")
        layout.addWidget(header)
        self.new_btn = QPushButton("+ 新对话")
        self.new_btn.setObjectName("newChatBtn")
        self.new_btn.setCursor(Qt.PointingHandCursor)
        self.new_btn.clicked.connect(self.new_conversation.emit)
        layout.addWidget(self.new_btn)
        self.list = QListWidget()
        self.list.setObjectName("conversationList")
        self.list.itemClicked.connect(self._on_item_clicked)
        self.list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self._on_context_menu)
        layout.addWidget(self.list)

    def add_conversation(self, session_id, title, active=False):
        item = QListWidgetItem(title)
        item.setData(Qt.UserRole, session_id)
        item.setToolTip(title)
        self.list.addItem(item)
        if active:
            self.list.setCurrentItem(item)
            self._style_active_item(item)

    def set_active(self, session_id):
        for i in range(self.list.count()):
            item = self.list.item(i)
            if item.data(Qt.UserRole) == session_id:
                self.list.setCurrentItem(item)
                self._style_active_item(item)
                return

    def _style_active_item(self, item):
        item.setForeground(QColor("#58A6FF"))

    def _on_item_clicked(self, item):
        session_id = item.data(Qt.UserRole)
        self.conversation_selected.emit(session_id)

    def _on_context_menu(self, pos):
        item = self.list.itemAt(pos)
        if not item:
            return
        menu = QMenu(self)
        rename = QAction("重命名", self)
        delete = QAction("删除", self)
        rename.triggered.connect(lambda: self._rename_item(item))
        delete.triggered.connect(lambda: self.conversation_deleted.emit(item.data(Qt.UserRole)))
        menu.addAction(rename)
        menu.addAction(delete)
        menu.exec(self.list.mapToGlobal(pos))

    def _rename_item(self, item):
        text, ok = QInputDialog.getText(self, "重命名对话", "名称:", text=item.text())
        if ok and text.strip():
            item.setText(text.strip())

    def remove_conversation(self, session_id):
        for i in range(self.list.count()):
            item = self.list.item(i)
            if item.data(Qt.UserRole) == session_id:
                self.list.takeItem(i)
                return

    def clear_conversations(self):
        """清空对话列表（用于按项目目录切换时刷新）"""
        self.list.clear()
