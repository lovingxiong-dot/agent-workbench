"""agent_workbench/ui/workbench/inspector.py — 右侧属性检查器。

根据 ModulePresentation + ViewSchema 动态生成编辑器：
- 无 Schema 时：平铺 Properties / Statistics / Actions。
- 有 Schema 时：按 InspectorTabSchema 渲染为 Tab，支持 category 过滤。

UI 只发 Signal：
- property_changed(object_id, property_name, new_value)
- action_triggered(object_id, action_name)
"""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from v6.ui.base import C, font
from agent_workbench.ui.workbench.presentation import (
    ActionPresentation,
    ModulePresentation,
    PropertyPresentation,
    StatisticPresentation,
)
from agent_workbench.ui.workbench.view_schema import InspectorSchema, InspectorTabSchema


_READONLY_STYLE = (
    f"background-color: {C['bg_input']}; color: {C['text_muted']}; "
    f"border: 1px solid {C['border']}; border-radius: 4px; padding: 4px;"
)

_EDITABLE_STYLE = (
    f"background-color: {C['bg_input']}; color: {C['text_primary']}; "
    f"border: 1px solid {C['border']}; border-radius: 4px; padding: 4px;"
)


class Inspector(QWidget):
    """Workbench 属性检查器。"""

    property_changed = Signal(str, str, object)  # object_id, property_name, new_value
    action_triggered = Signal(str, str)  # object_id, action_name

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._object_id = ""
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(12, 12, 12, 12)
        self._layout.setSpacing(12)

        self._title = QLabel("Inspector", self)
        self._title.setFont(font(14, bold=True))
        self._layout.addWidget(self._title)

        # 模式 A：无 Schema，单滚动区
        self._scroll = QScrollArea(self)
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet("border: none;")
        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(12)
        self._content_layout.addStretch()
        self._scroll.setWidget(self._content)
        self._layout.addWidget(self._scroll)

        # 模式 B：有 Schema，Tab 容器（懒加载）
        self._tabs: QTabWidget | None = None
        self._schema: InspectorSchema | None = None

        self._style()

    def _style(self) -> None:
        self.setStyleSheet(
            f"background-color: {C['bg_right']}; color: {C['text_primary']}; border-left: 1px solid {C['border']};"
        )

    def set_schema(self, schema: InspectorSchema | None) -> None:
        """设置 Inspector 布局协议；None 表示回退到传统平铺模式。"""
        self._schema = schema
        self._ensure_mode()

    def _ensure_mode(self) -> None:
        """根据是否有 Schema 切换 Tab 模式或传统滚动模式。"""
        has_tabs = self._schema is not None and self._schema.tabs
        if has_tabs:
            if self._tabs is None:
                self._scroll.hide()
                self._tabs = QTabWidget(self)
                self._tabs.setStyleSheet("border: none;")
                self._layout.addWidget(self._tabs)
            self._tabs.show()
        else:
            if self._tabs is not None:
                self._tabs.hide()
            self._scroll.show()

    def set_object(self, presentation: ModulePresentation) -> None:
        """根据 PresentationModel 渲染 Inspector。"""
        self._object_id = presentation.id
        self._title.setText(presentation.name)
        self._ensure_mode()

        if self._tabs is not None and self._tabs.isVisible():
            self._render_tab_mode(presentation)
        else:
            self._render_legacy_mode(presentation)

    def _render_legacy_mode(self, presentation: ModulePresentation) -> None:
        """传统模式：平铺所有 Properties / Statistics / Actions。"""
        self._clear_content(self._content_layout)
        self._add_property_sections(presentation.properties, self._content_layout)
        self._add_section(self._content_layout, "Statistics", presentation.statistics, self._create_statistic)
        self._add_section(self._content_layout, "Actions", presentation.actions, self._create_action)

    def _render_tab_mode(self, presentation: ModulePresentation) -> None:
        """Schema 模式：每个 Tab 按 source 渲染对应内容。"""
        assert self._tabs is not None
        # 清空旧 Tab
        while self._tabs.count() > 0:
            self._tabs.removeTab(0)

        for tab_schema in self._schema.tabs:  # type: ignore[union-attr]
            tab_widget, tab_layout = self._create_tab_container()
            if tab_schema.source == "properties":
                props = self._filter_properties(presentation.properties, tab_schema)
                self._add_property_sections(props, tab_layout)
            elif tab_schema.source == "statistics":
                self._add_section(tab_layout, tab_schema.title, presentation.statistics, self._create_statistic)
            elif tab_schema.source == "actions":
                self._add_section(tab_layout, tab_schema.title, presentation.actions, self._create_action)
            self._tabs.addTab(tab_widget, tab_schema.title)

    def _create_tab_container(self) -> tuple[QWidget, QVBoxLayout]:
        """创建一个带滚动区的 Tab 容器。"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        layout.addStretch()
        scroll.setWidget(content)

        wrapper = QWidget()
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.setSpacing(0)
        wrapper_layout.addWidget(scroll)
        return wrapper, layout

    def _clear_content(self, layout: QVBoxLayout) -> None:
        """清空 layout 中除最后 stretch 外的所有内容。"""
        while layout.count() > 1:
            item = layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

    def _filter_properties(
        self, properties: list[PropertyPresentation], tab_schema: InspectorTabSchema
    ) -> list[PropertyPresentation]:
        """按 TabSchema.categories 过滤 Properties；空列表表示不过滤。"""
        if not tab_schema.categories:
            return properties
        categories = {c.strip().lower() for c in tab_schema.categories}
        return [p for p in properties if (p.category or "").strip().lower() in categories]

    def _add_section(self, layout: QVBoxLayout, title: str, items, factory) -> None:
        if not items:
            return
        lbl = QLabel(title)
        lbl.setFont(font(12, bold=True))
        lbl.setStyleSheet(f"color: {C['text_secondary']}; margin-top: 8px;")
        layout.insertWidget(layout.count() - 1, lbl)
        for item in items:
            widget = factory(item)
            layout.insertWidget(layout.count() - 1, widget)

    def _add_property_sections(
        self, properties: list[PropertyPresentation], layout: QVBoxLayout
    ) -> None:
        """按 category 分组渲染 Properties；空 category 归入 General。"""
        if not properties:
            return
        groups: dict[str, list[PropertyPresentation]] = {}
        for prop in properties:
            category = (prop.category or "").strip() or "General"
            groups.setdefault(category, []).append(prop)

        for category in sorted(groups.keys()):
            self._add_section(layout, category, groups[category], self._create_property)

    def _create_property(self, prop: PropertyPresentation) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        label = QLabel(prop.label)
        label.setFont(font(10))
        label.setStyleSheet(f"color: {C['text_muted']};")
        layout.addWidget(label)

        editor = self._create_property_editor(prop)
        layout.addWidget(editor)
        return container

    def _create_property_editor(self, prop: PropertyPresentation) -> QWidget:
        """根据 PropertyPresentation 创建合适的编辑器，并统一处理 editable / sensitive。"""
        if prop.sensitive:
            return self._create_password_editor(prop)
        if prop.type == "boolean":
            return self._create_boolean_editor(prop)
        if prop.type == "select":
            return self._create_select_editor(prop)
        if prop.type in ("textarea", "json"):
            return self._create_textarea_editor(prop)
        return self._create_string_editor(prop)

    def _create_password_editor(self, prop: PropertyPresentation) -> QLineEdit:
        """敏感字段统一使用密码输入框，只读时禁用编辑。"""
        ln = QLineEdit(str(prop.value), self)
        ln.setEchoMode(QLineEdit.EchoMode.Password)
        ln.setReadOnly(not prop.editable)
        ln.setEnabled(prop.editable)
        ln.setStyleSheet(_EDITABLE_STYLE if prop.editable else _READONLY_STYLE)
        if prop.editable:
            ln.editingFinished.connect(
                lambda name=prop.name, widget=ln: self.property_changed.emit(self._object_id, name, widget.text())
            )
        return ln

    def _create_boolean_editor(self, prop: PropertyPresentation) -> QCheckBox:
        chk = QCheckBox(self)
        chk.setChecked(bool(prop.value))
        chk.setEnabled(prop.editable)
        if prop.editable:
            chk.stateChanged.connect(lambda state, name=prop.name: self.property_changed.emit(self._object_id, name, bool(state)))
        return chk

    def _create_select_editor(self, prop: PropertyPresentation) -> QComboBox:
        cmb = QComboBox(self)
        cmb.addItems(prop.options)
        idx = cmb.findText(str(prop.value))
        if idx >= 0:
            cmb.setCurrentIndex(idx)
        cmb.setEnabled(prop.editable)
        if prop.editable:
            cmb.currentTextChanged.connect(lambda text, name=prop.name: self.property_changed.emit(self._object_id, name, text))
        return cmb

    def _create_textarea_editor(self, prop: PropertyPresentation) -> QTextEdit:
        txt = QTextEdit(self)
        txt.setPlainText(str(prop.value))
        txt.setReadOnly(not prop.editable)
        txt.setEnabled(prop.editable)
        txt.setMaximumHeight(200)
        txt.setStyleSheet(_EDITABLE_STYLE if prop.editable else _READONLY_STYLE)
        if prop.editable:
            txt.textChanged.connect(lambda name=prop.name, widget=txt: self.property_changed.emit(self._object_id, name, widget.toPlainText()))
        return txt

    def _create_string_editor(self, prop: PropertyPresentation) -> QLineEdit:
        ln = QLineEdit(str(prop.value), self)
        ln.setReadOnly(not prop.editable)
        ln.setEnabled(prop.editable)
        ln.setStyleSheet(_EDITABLE_STYLE if prop.editable else _READONLY_STYLE)
        if prop.editable:
            ln.editingFinished.connect(
                lambda name=prop.name, widget=ln: self.property_changed.emit(self._object_id, name, widget.text())
            )
        return ln

    def _create_statistic(self, stat: StatisticPresentation) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        label = QLabel(f"{stat.label}:")
        label.setFont(font(10))
        label.setStyleSheet(f"color: {C['text_muted']};")
        layout.addWidget(label)

        value_text = str(stat.value)
        if stat.format == "json":
            import json
            value_text = json.dumps(stat.value, ensure_ascii=False, indent=2)
        value = QLabel(value_text)
        value.setFont(font(10, bold=True))
        value.setStyleSheet(f"color: {C['text_primary']};")
        value.setWordWrap(True)
        layout.addWidget(value, 1)
        return container

    def _create_action(self, action: ActionPresentation) -> QWidget:
        btn = QPushButton(f"{action.icon} {action.label}")
        btn.setFont(font(10))
        btn.setToolTip(action.description)
        btn.setEnabled(action.enabled)
        if action.enabled:
            btn.clicked.connect(lambda _checked, name=action.name: self.action_triggered.emit(self._object_id, name))
        btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['btn_bg']}; color: {C['text_primary']}; border: 1px solid {C['border']}; border-radius: 4px; padding: 6px 12px; }}"
            f"QPushButton:hover {{ background-color: {C['btn_hover']}; }}"
            f"QPushButton:disabled {{ background-color: {C['bg_input']}; color: {C['text_muted']}; border: 1px solid {C['border']}; }}"
        )
        return btn
