"""agent_workbench/ui/workbench/agent_profile_workspace.py — Agent Profile 详情页。

展示选中 Agent 的完整信息：名称、描述、System Prompt、Provider、模型、Skills、Tools。

v6.10.0-alpha Agent Configuration Layer：
  - 保留原有 _setup_ui / 详情展示
  - 追加 set_view_model(profile) — AgentProfile ViewModel 入口
  - 追加 signals：edit_requested / activate_requested / delete_requested
"""
from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from v6.ui.base import C, font


class AgentProfileWorkspaceItem(QWidget):
    """Agent Profile 详情页。

    v6.10.0-alpha:
      - 保留原有 _setup_ui / 详情展示
      - 新增 ViewModel 入口 set_view_model(profile)
      - 新增 signals: edit_requested / activate_requested / delete_requested
    """

    # ──────────────────────────────────────────────────────────
    # v6.10.0-alpha: Agent 操作 signals
    # ──────────────────────────────────────────────────────────

    edit_requested = Signal(str)  # agent_id
    activate_requested = Signal(str)  # agent_id
    delete_requested = Signal(str)  # agent_id

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._current_profile: Any = None  # AgentProfile | None
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

        self._container = QWidget(scroll)
        self._container_layout = QVBoxLayout(self._container)
        self._container_layout.setContentsMargins(32, 28, 32, 28)
        self._container_layout.setSpacing(20)
        scroll.setWidget(self._container)

        self.setStyleSheet(f"background-color: {C['bg_primary']}; border: none;")

    def set_agent(self, info: dict[str, Any]) -> None:
        """设置当前显示的 Agent 信息。"""
        # 清除旧内容
        while self._container_layout.count():
            item = self._container_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        name = info.get("name", info.get("id", "Unknown Agent"))
        agent_id = info.get("id", "")

        # 标题：Agent 名称
        title = QLabel(name, self._container)
        title.setFont(font(22, bold=True))
        title.setStyleSheet(f"color: {C['text_primary']}; border: none;")
        self._container_layout.addWidget(title)

        # ID badge
        if agent_id:
            id_label = QLabel(f"ID: {agent_id}", self._container)
            id_label.setFont(font(11))
            id_label.setStyleSheet(f"color: {C['text_muted']}; border: none;")
            self._container_layout.addWidget(id_label)

        # 版本
        version = info.get("version", "")
        if version:
            ver_label = QLabel(f"Version {version}", self._container)
            ver_label.setFont(font(11))
            ver_label.setStyleSheet(f"color: {C['text_muted']}; border: none;")
            self._container_layout.addWidget(ver_label)

        # 描述
        description = info.get("description", "")
        if description:
            self._container_layout.addSpacing(8)
            desc_group = self._create_section("Description", self._container)
            desc_text = QLabel(description, desc_group)
            desc_text.setFont(font(12))
            desc_text.setStyleSheet(f"color: {C['text_secondary']}; border: none;")
            desc_text.setWordWrap(True)
            desc_group.layout().addWidget(desc_text)
            self._container_layout.addWidget(desc_group)

        # System Prompt
        system_prompt = info.get("system_prompt", "")
        if system_prompt:
            self._container_layout.addSpacing(4)
            prompt_group = self._create_section("System Prompt", self._container)
            prompt_text = QLabel(system_prompt, prompt_group)
            prompt_text.setFont(font(11))
            prompt_text.setStyleSheet(
                f"color: {C['text_secondary']}; background-color: {C['bg_card']}; "
                f"border: 1px solid {C['border']}; border-radius: 4px; padding: 12px;"
            )
            prompt_text.setWordWrap(True)
            prompt_text.setTextFormat(Qt.TextFormat.PlainText)
            prompt_group.layout().addWidget(prompt_text)
            self._container_layout.addWidget(prompt_group)

        # Provider & Model
        provider = info.get("provider", "—")
        model = info.get("model", "—")
        self._container_layout.addSpacing(4)
        config_group = self._create_section("Configuration", self._container)
        config_layout = config_group.layout()

        provider_row = QLabel(f"Provider:  {provider}", config_group)
        provider_row.setFont(font(12))
        provider_row.setStyleSheet(f"color: {C['text_primary']}; border: none;")
        config_layout.addWidget(provider_row)

        model_row = QLabel(f"Model:  {model}", config_group)
        model_row.setFont(font(12))
        model_row.setStyleSheet(f"color: {C['text_primary']}; border: none;")
        config_layout.addWidget(model_row)
        self._container_layout.addWidget(config_group)

        # Skills
        skills = info.get("skills", [])
        if skills:
            self._container_layout.addSpacing(4)
            skills_group = self._create_section("Skills", self._container)
            skills_layout = skills_group.layout()
            for skill in skills:
                if isinstance(skill, dict):
                    skill_name = skill.get("name", "Unknown")
                else:
                    skill_name = str(skill)
                skill_label = QLabel(f"  ▸ {skill_name}", skills_group)
                skill_label.setFont(font(12))
                skill_label.setStyleSheet(f"color: {C['text_secondary']}; border: none;")
                skills_layout.addWidget(skill_label)
            self._container_layout.addWidget(skills_group)

        # Tools
        tools = info.get("tools", [])
        if tools:
            self._container_layout.addSpacing(4)
            tools_group = self._create_section("Tools", self._container)
            tools_layout = tools_group.layout()
            for tool in tools:
                if isinstance(tool, dict):
                    tool_name = tool.get("name", "Unknown")
                else:
                    tool_name = str(tool)
                tool_label = QLabel(f"  ▸ {tool_name}", tools_group)
                tool_label.setFont(font(12))
                tool_label.setStyleSheet(f"color: {C['text_secondary']}; border: none;")
                tools_layout.addWidget(tool_label)
            self._container_layout.addWidget(tools_group)

        # Runtime Capabilities (Capability Tree)
        capabilities = info.get("capabilities", [])
        if capabilities:
            self._container_layout.addSpacing(4)
            cap_group = self._create_section("Runtime Capabilities", self._container)
            cap_layout = cap_group.layout()
            for cap in capabilities:
                ns = cap.get("namespace", "unknown")
                cap_name = cap.get("name", ns)
                cap_icon = cap.get("icon", "")
                stats = cap.get("stats", [])
                stats_text = "  |  ".join(f"{s['key']}: {s['value']}" for s in stats) if stats else ""
                cap_label = QLabel(f"  {cap_icon}  {cap_name}  —  {stats_text}" if stats_text else f"  {cap_icon}  {cap_name}", cap_group)
                cap_label.setFont(font(12))
                cap_label.setStyleSheet(f"color: {C['text_secondary']}; border: none;")
                cap_label.setWordWrap(True)
                cap_layout.addWidget(cap_label)
            self._container_layout.addWidget(cap_group)

        self._container_layout.addStretch()

    def _create_section(self, title: str, parent: QWidget) -> QFrame:
        """创建带标题的分组区域。"""
        group = QFrame(parent)
        group.setStyleSheet(
            f"QFrame {{ background-color: {C['bg_card']}; border: 1px solid {C['border']}; border-radius: 8px; }}"
        )
        layout = QVBoxLayout(group)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        label = QLabel(title, group)
        label.setFont(font(12, bold=True))
        label.setStyleSheet(f"color: {C['text_primary']}; border: none;")
        layout.addWidget(label)
        return group

    # ──────────────────────────────────────────────────────────
    # v6.10.0-alpha: ViewModel 接入
    # ──────────────────────────────────────────────────────────

    def set_view_model(self, profile: Any) -> None:
        """通过 AgentProfile ViewModel 刷新详情页（v6.10 推荐入口）。

        Args:
            profile: view_models.agent_profile.AgentProfile。
        """
        self._current_profile = profile
        info = self._profile_to_legacy_info(profile)
        self.set_agent(info)

    def get_current_profile(self) -> Any:
        """获取当前 ViewModel。"""
        return self._current_profile

    @staticmethod
    def _profile_to_legacy_info(profile: Any) -> dict[str, Any]:
        """AgentProfile -> legacy agent info dict（保留旧 _render_info 入口）。"""
        return {
            "agent_id": profile.identity.agent_id,
            "name": profile.identity.name,
            "description": profile.identity.description,
            "avatar": profile.identity.avatar,
            "system_prompt": "",
            "provider": profile.provider_id,
            "model": "",
            "skills": [{"name": s} for s in profile.skills],
            "tools": [{"name": t} for t in profile.tools],
            "capabilities": [],
        }

    def request_edit(self, agent_id: str) -> None:
        """UI 请求编辑 Agent（emit signal）。"""
        self.edit_requested.emit(agent_id)

    def request_activate(self, agent_id: str) -> None:
        """UI 请求激活 Agent（emit signal）。"""
        self.activate_requested.emit(agent_id)

    def request_delete(self, agent_id: str) -> None:
        """UI 请求删除 Agent（emit signal）。"""
        self.delete_requested.emit(agent_id)