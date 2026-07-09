"""agent_workbench/ui/workbench/welcome_workspace.py — Welcome / Home Workspace。

职责：
- 作为 Workbench OS 的 Home 页面。
- 展示产品定位、已安装 Agents、快捷入口、最近项目、文档链接。
- 不持有业务对象，只通过信号向 WorkbenchUIController 报告用户意图。
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from v6.ui.base import C, font


class WelcomeWorkspaceItem(QWidget):
    """Welcome / Home Workspace。"""

    new_agent_requested = Signal()
    install_agent_requested = Signal()
    documentation_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        scroll = QScrollArea(self)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._layout.addWidget(scroll)

        container = QWidget(scroll)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(64, 48, 64, 32)
        container_layout.setSpacing(32)
        scroll.setWidget(container)

        # 标题区
        title = QLabel("Workbench OS 1.0", container)
        title.setFont(font(28, bold=True))
        title.setStyleSheet(f"color: {C['text_primary']};")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(title)

        subtitle = QLabel("Install · Manage · Run Agents", container)
        subtitle.setFont(font(14))
        subtitle.setStyleSheet(f"color: {C['text_secondary']};")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(subtitle)

        tagline = QLabel("An operating system for AI Agents.", container)
        tagline.setFont(font(11))
        tagline.setStyleSheet(f"color: {C['text_muted']};")
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(tagline)

        container_layout.addSpacing(24)

        # 快捷入口
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(16)
        actions_layout.addStretch()

        self._new_agent_btn = QPushButton("+ New Agent", container)
        self._new_agent_btn.setFont(font(11))
        self._new_agent_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._new_agent_btn.setStyleSheet(self._button_style())
        self._new_agent_btn.clicked.connect(self.new_agent_requested.emit)
        actions_layout.addWidget(self._new_agent_btn)

        self._install_agent_btn = QPushButton("+ Install Agent", container)
        self._install_agent_btn.setFont(font(11))
        self._install_agent_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._install_agent_btn.setStyleSheet(self._button_style())
        self._install_agent_btn.clicked.connect(self.install_agent_requested.emit)
        actions_layout.addWidget(self._install_agent_btn)

        actions_layout.addStretch()
        container_layout.addLayout(actions_layout)

        # 内容区：Recent + Documentation
        content_layout = QHBoxLayout()
        content_layout.setSpacing(32)

        recent_group = self._create_group("Recent", container)
        self._recent_list = QLabel("No recent projects.", recent_group)
        self._recent_list.setFont(font(11))
        self._recent_list.setStyleSheet(f"color: {C['text_secondary']};")
        self._recent_list.setWordWrap(True)
        recent_group.layout().addWidget(self._recent_list)
        content_layout.addWidget(recent_group, 1)

        docs_group = self._create_group("Documentation", container)
        docs = [
            ("Getting Started", "getting-started"),
            ("Create your first Agent", "create-first-agent"),
            ("Package Development Guide", "package-dev-guide"),
            ("GitHub", "github"),
        ]
        docs_layout = QVBoxLayout()
        docs_layout.setSpacing(8)
        for label, key in docs:
            link = QLabel(f"<a href='{key}' style='color: {C['accent_blue']}; text-decoration: none;'>{label}</a>", docs_group)
            link.setFont(font(11))
            link.setTextFormat(Qt.TextFormat.RichText)
            link.setOpenExternalLinks(False)
            link.linkActivated.connect(lambda k=key: self.documentation_requested.emit(k))
            docs_layout.addWidget(link)
        docs_group.layout().addLayout(docs_layout)
        content_layout.addWidget(docs_group, 1)

        container_layout.addLayout(content_layout)

        # Installed Agents
        agents_group = self._create_group("Installed Agents", container)
        self._agents_list = QLabel("No agents installed.", agents_group)
        self._agents_list.setFont(font(11))
        self._agents_list.setStyleSheet(f"color: {C['text_secondary']};")
        self._agents_list.setWordWrap(True)
        agents_group.layout().addWidget(self._agents_list)
        container_layout.addWidget(agents_group)

        container_layout.addStretch()

        # 底部状态
        footer_layout = QHBoxLayout()
        self._version_label = QLabel("Version 1.0", container)
        self._version_label.setFont(font(10))
        self._version_label.setStyleSheet(f"color: {C['text_muted']};")
        footer_layout.addWidget(self._version_label)

        footer_layout.addStretch()

        self._project_label = QLabel("Current Project\n—", container)
        self._project_label.setFont(font(10))
        self._project_label.setStyleSheet(f"color: {C['text_muted']};")
        self._project_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._project_label.setWordWrap(True)
        footer_layout.addWidget(self._project_label)
        container_layout.addLayout(footer_layout)

        self.setStyleSheet(f"background-color: {C['bg_primary']}; border: none;")

    def _create_group(self, title: str, parent: QWidget) -> QFrame:
        group = QFrame(parent)
        group.setStyleSheet(
            f"QFrame {{ background-color: {C['bg_card']}; border: 1px solid {C['border']}; border-radius: 8px; }}"
        )
        layout = QVBoxLayout(group)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        label = QLabel(title, group)
        label.setFont(font(12, bold=True))
        label.setStyleSheet(f"color: {C['text_primary']};")
        layout.addWidget(label)
        return group

    def _button_style(self) -> str:
        return (
            f"QPushButton {{"
            f"  background-color: {C['btn_bg']};"
            f"  color: {C['text_primary']};"
            f"  border: 1px solid {C['border']};"
            f"  border-radius: 6px;"
            f"  padding: 10px 20px;"
            f"}}"
            f"QPushButton:hover {{ background-color: {C['btn_hover']}; }}"
        )

    def set_installed_agents(self, agents: list[tuple[str, str]]) -> None:
        """设置已安装 Agent 列表。"""
        if not agents:
            self._agents_list.setText("No agents installed.")
            return
        lines = [f"  • {name}" for _, name in agents]
        self._agents_list.setText("\n".join(lines))
        self._agents_list.setStyleSheet(f"color: {C['text_primary']};")

    def set_recent_projects(self, projects: list[str]) -> None:
        """设置最近项目列表。"""
        if not projects:
            self._recent_list.setText("No recent projects.")
            return
        lines = [f"  • {name}" for name in projects]
        self._recent_list.setText("\n".join(lines))
        self._recent_list.setStyleSheet(f"color: {C['text_primary']};")

    def set_project(self, project_name: str, parent_dir: str) -> None:
        """设置当前项目信息。

        参数：
            project_name: 项目目录名（如 agent_workbench）。
            parent_dir: 项目所在父目录（如 ``F:\\Agent\\``）。
        """
        self._project_label.setText(f"Current Project\n{project_name}\n{parent_dir}")

    def set_version(self, version: str) -> None:
        """设置版本号。"""
        self._version_label.setText(f"Version {version}")
