from datetime import datetime
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QListWidget, QListWidgetItem
from PySide6.QtCore import Qt


class TaskListWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._tasks = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        header = QLabel("任务")
        header.setObjectName("panelHeader")
        layout.addWidget(header)
        top = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("添加新任务...")
        self.add_btn = QPushButton("+")
        self.add_btn.setFixedWidth(32)
        self.add_btn.clicked.connect(self._add_task_from_input)
        self.input.returnPressed.connect(self._add_task_from_input)
        top.addWidget(self.input)
        top.addWidget(self.add_btn)
        layout.addLayout(top)
        self.list = QListWidget()
        self.list.setObjectName("taskList")
        self.list.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self.list)
        self.clear_btn = QPushButton("清除已完成")
        self.clear_btn.clicked.connect(self._clear_completed)
        layout.addWidget(self.clear_btn)

    def _add_task_from_input(self):
        text = self.input.text().strip()
        if text:
            self.add_task(text)
            self.input.clear()

    def add_task(self, text, task_id=None, status="pending"):
        if task_id is None:
            task_id = f"task_{datetime.now().strftime('%H%M%S%f')[:-3]}"
        item = QListWidgetItem(text)
        item.setData(Qt.UserRole, task_id)
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        item.setCheckState(Qt.Checked if status == "done" else Qt.Unchecked)
        self.list.addItem(item)
        self._tasks[task_id] = item
        return task_id

    def finish_task(self, task_id, result=""):
        item = self._tasks.get(task_id)
        if item:
            item.setCheckState(Qt.Checked)
            if result:
                item.setText(f"{item.text()}  ✅ {result}")

    def _on_item_changed(self, item):
        task_id = item.data(Qt.UserRole)
        self._tasks[task_id] = item

    def _clear_completed(self):
        for i in range(self.list.count() - 1, -1, -1):
            item = self.list.item(i)
            if item.checkState() == Qt.Checked:
                task_id = item.data(Qt.UserRole)
                self._tasks.pop(task_id, None)
                self.list.takeItem(i)
