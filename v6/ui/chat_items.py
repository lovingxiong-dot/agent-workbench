"""v6/ui/chat_items.py — 聊天图形项。
设计来源：experiments/ui_template.py（Git 标签 v0.6-alpha）。"""
from __future__ import annotations

import re
from html import escape

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QGraphicsWidget, QGraphicsTextItem, QGraphicsItem

from v6.ui.base import C, qcolor


def _highlight(text: str, keyword: str) -> str:
    """将关键词在转义后的文本中高亮。"""
    txt = escape(text)
    if not keyword:
        return txt
    pat = re.compile(re.escape(keyword), re.IGNORECASE)
    return pat.sub(
        lambda m: f'<span style="background-color:rgba(0,122,204,0.45);color:{C["text_inverse"]}">{m.group(0)}</span>',
        txt,
    )


class ChatItem(QGraphicsWidget):
    """聊天图形项基类。"""

    MARGIN = 10

    def __init__(self, width: int, theme: str = "dark", parent=None):
        super().__init__(parent)
        self._w = max(width, 120)
        self._theme = theme
        self._keyword = ""
        self._bg = C["bg_card"]
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)

    def set_width(self, width: int) -> None:
        self._w = max(width, 120)
        self._refresh()

    def set_keyword(self, keyword: str) -> None:
        self._keyword = keyword
        self._refresh()

    def refresh_theme(self) -> None:
        self._refresh()

    def text(self) -> str:
        return ""

    def _refresh(self) -> None:
        self._update_content()
        self.setGeometry(0, 0, self._w, self._height())
        self.update()

    def _update_content(self) -> None:
        pass

    def _height(self) -> int:
        return 0

    def paint(self, painter: QPainter, option, widget=None) -> None:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(qcolor(C["border"]), 0.5))
        painter.setBrush(qcolor(self._bg))
        painter.drawRoundedRect(self.rect(), 8, 8)


class _RichItem(ChatItem):
    """使用 QGraphicsTextItem 渲染富文本的基类。"""

    def __init__(self, width: int, theme: str = "dark", parent=None):
        super().__init__(width, theme, parent)
        self._text = QGraphicsTextItem(self)
        self._text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

    def _update_content(self) -> None:
        self._text.setTextWidth(self._w - self.MARGIN * 2)
        self._text.setHtml(self._html())
        self._text.setPos(self.MARGIN, self.MARGIN)

    def _html(self) -> str:
        return ""

    def _height(self) -> int:
        return int(self._text.document().size().height() + self.MARGIN * 2)


class UserBubble(_RichItem):
    def __init__(self, text: str, width: int, theme: str = "dark", parent=None):
        super().__init__(width, theme, parent)
        self._raw = text
        self._bg = C["accent"]
        self._refresh()

    def text(self) -> str:
        return self._raw

    def _html(self) -> str:
        return (
            f'<p align="right" style="color:{C["text_inverse"]};font-size:13px;line-height:120%">'
            f'{_highlight(self._raw, self._keyword)}</p>'
        )

    def paint(self, painter: QPainter, option, widget=None) -> None:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(qcolor(self._bg))
        painter.drawRoundedRect(self.rect(), 12, 12)


class TextItem(_RichItem):
    def __init__(self, text: str, width: int, theme: str = "dark", parent=None):
        super().__init__(width, theme, parent)
        self._raw = text
        self._refresh()

    def text(self) -> str:
        return self._raw

    def _html(self) -> str:
        return (
            f'<p style="color:{C["text_primary"]};font-size:13px;line-height:120%">'
            f'{_highlight(self._raw, self._keyword)}</p>'
        )


class BulletItem(_RichItem):
    def __init__(self, text: str, width: int, theme: str = "dark", parent=None):
        super().__init__(width, theme, parent)
        self._raw = text
        self._refresh()

    def text(self) -> str:
        return self._raw

    def _html(self) -> str:
        return (
            f'<table cellpadding="0" cellspacing="0"><tr>'
            f'<td valign="top" width="16" style="color:{C["accent"]};font-size:13px">•</td>'
            f'<td style="color:{C["text_primary"]};font-size:13px;line-height:120%">'
            f'{_highlight(self._raw, self._keyword)}</td></tr></table>'
        )


class StepItem(_RichItem):
    def __init__(self, index: int, text: str, width: int, theme: str = "dark", parent=None):
        super().__init__(width, theme, parent)
        self._index = index
        self._raw = text
        self._refresh()

    def text(self) -> str:
        return self._raw

    def _html(self) -> str:
        return (
            f'<table cellpadding="0" cellspacing="0"><tr>'
            f'<td valign="top" width="22" style="color:{C["accent_blue"]};font-size:12px;font-weight:bold">'
            f'{self._index}.</td>'
            f'<td style="color:{C["text_primary"]};font-size:13px;line-height:120%">'
            f'{_highlight(self._raw, self._keyword)}</td></tr></table>'
        )


class FoldBlock(_RichItem):
    def __init__(self, title: str, body: str, width: int, theme: str = "dark", parent=None):
        super().__init__(width, theme, parent)
        self._title = title
        self._body = body
        self._refresh()

    def text(self) -> str:
        return f"{self._title} {self._body}"

    def _html(self) -> str:
        return (
            f'<p style="color:{C["text_primary"]};font-size:13px;font-weight:bold;margin-bottom:4px">'
            f'▼ {self._title}</p>'
            f'<p style="color:{C["text_secondary"]};font-size:13px;line-height:120%">'
            f'{_highlight(self._body, self._keyword)}</p>'
        )


class PhasePanel(_RichItem):
    def __init__(self, phase: str, body: str, width: int, theme: str = "dark", parent=None):
        super().__init__(width, theme, parent)
        self._phase = phase
        self._body = body
        self._refresh()

    def text(self) -> str:
        return f"{self._phase} {self._body}"

    def _html(self) -> str:
        return (
            f'<p style="color:{C["accent_blue"]};font-size:12px;font-weight:bold;margin-bottom:4px">'
            f'▶ {self._phase}</p>'
            f'<p style="color:{C["text_primary"]};font-size:13px;line-height:120%">'
            f'{_highlight(self._body, self._keyword)}</p>'
        )


class ToolEntry(_RichItem):
    def __init__(self, name: str, result: dict, status: str, width: int, theme: str = "dark", parent=None):
        super().__init__(width, theme, parent)
        self._name = name
        self._result = result
        self._status = status
        self._bg = C["bg_input"]
        self._refresh()

    def text(self) -> str:
        return f"{self._name} {self._result}"

    def _html(self) -> str:
        color = C["green"] if self._status == "ok" else C["yellow"]
        body = _highlight(str(self._result), self._keyword)
        return (
            f'<p style="color:{C["text_secondary"]};font-size:12px">'
            f'tool: <b style="color:{C["text_primary"]}">{self._name}</b> '
            f'<span style="color:{color}">[{self._status}]</span></p>'
            f'<pre style="color:{C["mono_text"]};font-family:Cascadia Code;font-size:12px;'
            f'margin:4px 0;white-space:pre-wrap">{body}</pre>'
        )


class SystemCard(_RichItem):
    def __init__(self, title: str, body: str, width: int, theme: str = "dark", parent=None):
        super().__init__(width, theme, parent)
        self._title = title
        self._body = body
        self._refresh()

    def text(self) -> str:
        return f"{self._title} {self._body}"

    def _html(self) -> str:
        return (
            f'<p align="center" style="color:{C["text_muted"]};font-size:12px;margin-bottom:4px">'
            f'{self._title}</p>'
            f'<p align="center" style="color:{C["text_secondary"]};font-size:13px;line-height:120%">'
            f'{_highlight(self._body, self._keyword)}</p>'
        )


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication, QGraphicsScene, QGraphicsView
    from PySide6.QtCore import QTimer

    app = QApplication(sys.argv)
    scene = QGraphicsScene()
    w = 560
    items = [
        UserBubble("你好，帮我分析这个项目。", w),
        PhasePanel("Reasoning", "我先查看项目结构，再给出建议。", w),
        ToolEntry("list_dir", {"files": ["main.py", "README.md"]}, "ok", w),
        BulletItem("项目结构清晰，主入口在 main.py。", w),
        StepItem(1, "运行依赖检查。", w),
        FoldBlock("详细日志", "这一步读取了目录下的所有文件。", w),
        SystemCard("系统消息", "已自动保存会话。", w),
        TextItem("如需继续，请输入下一步指令。", w),
    ]
    y = 10
    for it in items:
        scene.addItem(it)
        it.setPos(10, y)
        y += int(it.boundingRect().height()) + 8
    view = QGraphicsView(scene)
    view.resize(w + 40, 600)
    view.show()
    QTimer.singleShot(300, view.close)
    sys.exit(app.exec())
