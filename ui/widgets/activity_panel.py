"""
ActivityWidget — 结构化活动面板

- 以中文标题 + 类别 + 时间展示关键事件
- 分栏：当前项目活动 / 全局活动
- 点击活动条目在下方详情区显示完整内容
"""
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QTextEdit, QFrame,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor


# 类别 -> 显示颜色
CATEGORY_COLORS = {
    "文件": "#58A6FF",
    "项目": "#3FB950",
    "对话": "#D2A8FF",
    "工具": "#F0883E",
    "系统": "#8B949E",
}


def _format_time(iso_ts: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_ts)
        return dt.strftime("%m-%d %H:%M:%S")
    except Exception:
        return iso_ts


class ActivityWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._project_path = ""
        self._activities = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # ── 工具栏 ──────────────────────────────
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(8, 0, 8, 0)
        header = QLabel("活动")
        header.setObjectName("panelHeader")
        toolbar.addWidget(header)
        toolbar.addStretch()
        self.clear_btn = QPushButton("清除")
        self.clear_btn.setObjectName("fileTreeToolBtn")
        self.clear_btn.setFixedSize(40, 24)
        self.clear_btn.clicked.connect(self.clear)
        toolbar.addWidget(self.clear_btn)
        layout.addLayout(toolbar)

        # ── 当前项目活动 ─────────────────────────
        project_header = QLabel("当前项目")
        project_header.setObjectName("sectionHeader")
        project_header.setStyleSheet("color: #58A6FF; font-size: 11px; font-weight: bold; padding: 4px 8px;")
        layout.addWidget(project_header)

        self.project_list = QListWidget()
        self.project_list.setObjectName("activityList")
        self.project_list.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.project_list, 1)

        # 分隔线
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: #30363D;")
        layout.addWidget(sep)

        # ── 全局活动 ─────────────────────────────
        global_header = QLabel("全局")
        global_header.setObjectName("sectionHeader")
        global_header.setStyleSheet("color: #8B949E; font-size: 11px; font-weight: bold; padding: 4px 8px;")
        layout.addWidget(global_header)

        self.global_list = QListWidget()
        self.global_list.setObjectName("activityList")
        self.global_list.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.global_list, 1)

        # ── 详情区 ───────────────────────────────
        detail_label = QLabel("详情")
        detail_label.setObjectName("sectionHeader")
        detail_label.setStyleSheet("color: #E6EDF3; font-size: 11px; font-weight: bold; padding: 4px 8px;")
        layout.addWidget(detail_label)

        self.detail_edit = QTextEdit()
        self.detail_edit.setReadOnly(True)
        self.detail_edit.setFont(QFont("Cascadia Code", 10))
        self.detail_edit.setObjectName("activityDetail")
        self.detail_edit.setPlaceholderText("点击上方活动查看详细内容")
        layout.addWidget(self.detail_edit, 1)

    def set_project_path(self, path: str):
        self._project_path = path or ""
        self.refresh()

    def set_activities(self, activities: list):
        """外部传入完整活动列表，组件内部按 project_path 过滤"""
        self._activities = list(activities)
        self.refresh()

    def refresh(self):
        self.project_list.clear()
        self.global_list.clear()

        for act in self._activities:
            item = self._make_item(act)
            path = act.get("project_path", "")
            if path and path == self._project_path:
                self.project_list.addItem(item)
            elif path == "":
                self.global_list.addItem(item)

    def _make_item(self, activity: dict) -> QListWidgetItem:
        title = activity.get("title", "未命名")
        category = activity.get("category", "系统")
        ts = _format_time(activity.get("timestamp", ""))
        summary = activity.get("summary", "")

        display = f"[{category}] {title}\n{ts}  {summary[:40]}"
        item = QListWidgetItem(display)
        item.setData(Qt.UserRole, activity)
        item.setToolTip(summary)
        color = CATEGORY_COLORS.get(category, "#8B949E")
        item.setForeground(QColor(color))
        return item

    def _on_item_clicked(self, item: QListWidgetItem):
        activity = item.data(Qt.UserRole)
        if not activity:
            return
        detail = activity.get("detail", "")
        title = activity.get("title", "")
        category = activity.get("category", "")
        ts = activity.get("timestamp", "")
        self.detail_edit.setPlainText(
            f"标题: {title}\n"
            f"类别: {category}\n"
            f"时间: {ts}\n"
            f"{'='*40}\n"
            f"{detail}"
        )

    def clear(self):
        self._activities = []
        self.project_list.clear()
        self.global_list.clear()
        self.detail_edit.clear()
