"""agent_workbench/ui/workbench/inspector.py — 右侧属性检查器。

根据 ModulePresentation 动态生成编辑器：
- Properties：可编辑字段
- Statistics：只读状态
- Actions：操作按钮
- Diagnostics：预留的诊断信息区

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
        self._style()

    def _style(self) -> None:
        self.setStyleSheet(
            f"background-color: {C['bg_right']}; color: {C['text_primary']}; border-left: 1px solid {C['border']};"
        )

    def set_object(self, presentation: ModulePresentation) -> None:
        """根据 PresentationModel 渲染 Inspector。"""
        self._object_id = presentation.id
        self._title.setText(presentation.name)

        # 清空现有内容（保留最后的 stretch）
        while self._content_layout.count() > 1:
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        self._add_section("Properties", presentation.properties, self._create_property)
        self._add_section("Statistics", presentation.statistics, self._create_statistic)
        self._add_section("Actions", presentation.actions, self._create_action)

    def _add_section(self, title: str, items, factory) -> None:
        if not items:
            return
        lbl = QLabel(title)
        lbl.setFont(font(12, bold=True))
        lbl.setStyleSheet(f"color: {C['text_secondary']}; margin-top: 8px;")
        self._content_layout.insertWidget(self._content_layout.count() - 1, lbl)
        for item in items:
            widget = factory(item)
            self._content_layout.insertWidget(self._content_layout.count() - 1, widget)

    def _create_property(self, prop: PropertyPresentation) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        label = QLabel(prop.label)
        label.setFont(font(10))
        label.setStyleSheet(f"color: {C['text_muted']};")
        layout.addWidget(label)

        editor: QWidget
        if prop.type == "boolean":
            chk = QCheckBox(self)
            chk.setChecked(bool(prop.value))
            chk.setEnabled(prop.editable)
            chk.stateChanged.connect(lambda state, name=prop.name: self.property_changed.emit(self._object_id, name, bool(state)))
            editor = chk
        elif prop.type == "select":
            cmb = QComboBox(self)
            cmb.addItems(prop.options)
            idx = cmb.findText(str(prop.value))
            if idx >= 0:
                cmb.setCurrentIndex(idx)
            cmb.setEnabled(prop.editable)
            cmb.currentTextChanged.connect(lambda text, name=prop.name: self.property_changed.emit(self._object_id, name, text))
            editor = cmb
        elif prop.type in ("textarea", "json"):
            txt = QTextEdit(self)
            txt.setPlainText(str(prop.value))
            txt.setReadOnly(not prop.editable)
            txt.setMaximumHeight(200)
            txt.textChanged.connect(lambda name=prop.name, widget=txt: self.property_changed.emit(self._object_id, name, widget.toPlainText()))
            editor = txt
        else:
            ln = QLineEdit(str(prop.value), self)
            ln.setReadOnly(not prop.editable)
            if prop.editable:
                ln.editingFinished.connect(
                    lambda name=prop.name, widget=ln: self.property_changed.emit(self._object_id, name, widget.text())
                )
            editor = ln

        editor.setStyleSheet(
            f"background-color: {C['bg_input']}; color: {C['text_primary']}; border: 1px solid {C['border']}; border-radius: 4px; padding: 4px;"
        )
        layout.addWidget(editor)
        return container

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
        btn.clicked.connect(lambda _checked, name=action.name: self.action_triggered.emit(self._object_id, name))
        btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['btn_bg']}; color: {C['text_primary']}; border: 1px solid {C['border']}; border-radius: 4px; padding: 6px 12px; }}"
            f"QPushButton:hover {{ background-color: {C['btn_hover']}; }}"
        )
        return btn
