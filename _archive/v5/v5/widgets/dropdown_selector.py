"""V5 通用内嵌下拉选择器。"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QPainter, QColor, QPen
from .base import theme, C, font


class DropdownSelector(QWidget):
    """内嵌下拉列表：定位到触发标签正下方，点击项后发射 item_selected。"""
    item_selected = Signal(str)

    CORNER = 8

    def __init__(self, items: list[str], parent=None):
        super().__init__(parent)
        self._items = items
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.Popup if not parent else Qt.WindowType.Widget)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)

        self._labels: list[QLabel] = []
        for text in items:
            lbl = QLabel(text)
            lbl.setFont(font(10))
            lbl.setCursor(Qt.PointingHandCursor)
            lbl.setStyleSheet(
                f"color: {C['text_secondary']}; background: transparent; "
                f"padding: 6px 10px; border-radius: 4px;"
            )
            lbl.mousePressEvent = lambda e, t=text: self._on_item_clicked(t)
            lbl.enterEvent = lambda e, l=lbl: l.setStyleSheet(
                f"color: {C['text_primary']}; background-color: {C['bg_hover']}; "
                f"padding: 6px 10px; border-radius: 4px;"
            )
            lbl.leaveEvent = lambda e, l=lbl: l.setStyleSheet(
                f"color: {C['text_secondary']}; background: transparent; "
                f"padding: 6px 10px; border-radius: 4px;"
            )
            layout.addWidget(lbl)
            self._labels.append(lbl)

        self.setFixedWidth(120)
        self.setFixedHeight(len(items) * 26 + 4)
        self.hide()
        theme.changed.connect(self._refresh_theme)
        self._refresh_theme()

    def _refresh_theme(self):
        self.setStyleSheet(f"background-color: transparent;")
        for lbl in self._labels:
            lbl.setStyleSheet(
                f"color: {C['text_secondary']}; background: transparent; "
                f"padding: 6px 10px; border-radius: 4px;"
            )

    def _on_item_clicked(self, text: str):
        self.item_selected.emit(text)
        self.hide()

    def position_under(self, widget: QWidget):
        """定位到给定控件正下方、左对齐（在父控件坐标系内）。"""
        parent = self.parentWidget()
        if parent:
            pos = widget.mapTo(parent, QPoint(0, widget.height() + 2))
            self.move(pos.x(), pos.y())
        else:
            pos = widget.mapToGlobal(QPoint(0, widget.height() + 2))
            self.move(pos.x(), pos.y())

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QColor(C["bg_card"]))
        p.setPen(QPen(QColor(C["border"]), 0.5))
        p.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), self.CORNER, self.CORNER)
        p.end()
