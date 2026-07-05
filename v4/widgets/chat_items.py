"""v4 聊天区图形元素。"""
import html
import re
from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtCore import Qt, QRect, QRectF, QPointF
from PySide6.QtGui import (
    QPainter, QPainterPath, QColor, QFont, QFontMetrics, QPen, QTextOption,
)
from .base import theme, _THEMES, C, font, mono_font, qcolor
from .chat_scene import ChatScene

# ══════════════════════════════════════════════════════════════
# 聊天区 QGraphicsItem 元素（像素级对齐 SVG）
# ══════════════════════════════════════════════════════════════

class ChatItem(QGraphicsItem):
    """所有聊天元素的基类。"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._h = 0.0

    def height(self) -> float:
        return self._h

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, ChatScene.CHAT_W, self._h)


class UserBubble(ChatItem):
    """SVG: x=240 y=56 w=148 h=26 rx=8 fill=#007acc, text x=365 text-anchor=end"""
    PAD_X = 12.0
    PAD_Y = 8.0
    RIGHT_PAD = 14.0

    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self._text = text
        fnt = font(11)
        max_text_w = max(40.0, ChatScene.CONTENT_W - 2 * self.PAD_X)
        tw, th = _wrap_text_size(text, fnt, max_text_w)
        bw = max(60.0, min(float(ChatScene.CONTENT_W), tw + 2 * self.PAD_X))
        bh = th + 2 * self.PAD_Y
        bx = ChatScene.CHAT_W - self.RIGHT_PAD - bw
        self._brect = QRectF(bx, 0, bw, bh)
        self._trect = QRectF(bx + self.PAD_X, self.PAD_Y, bw - 2 * self.PAD_X, th)
        self._h = bh + 8
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(self._brect, 8, 8)
        painter.fillPath(path, qcolor(C["accent"]))
        painter.setFont(font(11))
        painter.setPen(qcolor(C["text_inverse"]))
        to = QTextOption()
        to.setWrapMode(QTextOption.WordWrap)
        to.setAlignment(Qt.AlignRight)
        painter.drawText(self._trect, self._text, to)


class FoldBlock(ChatItem):
    """可折叠块。SVG收起: rx=4 h=22 fill=#16213e；展开: header h=20 fill=#1a1a2e + body。"""
    FOLD_H = 22.0
    HEADER_H = 20.0
    RX = 4.0

    def __init__(self, title: str, status: str = "", parent=None):
        super().__init__(parent)
        self._title = title
        self._status = status
        self._expanded = False
        self._body_h = 0.0
        self._body_items: list[QGraphicsItem] = []
        self._h = self.FOLD_H + 4
        self.setAcceptHoverEvents(True)

    def set_body(self, items: list[QGraphicsItem], h: float):
        self._body_items = items
        self._body_h = h
        for item in items:
            item.setParentItem(self)
            item.setVisible(False)

    def toggle(self):
        if self._expanded:
            self._expanded = False
            self._h = self.FOLD_H + 4
            for item in self._body_items:
                item.setVisible(False)
        else:
            self._expanded = True
            self._h = self.HEADER_H + self._body_h + 4
            for item in self._body_items:
                item.setVisible(True)
        self.prepareGeometryChange()

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        y0 = 0.0

        if self._expanded:
            # 外层卡片（dark bg_card #16213e; light bg_card #ffffff）
            outer = QRectF(ChatScene.LEFT_MARGIN, y0, ChatScene.CONTENT_W, self.HEADER_H + self._body_h)
            p = QPainterPath()
            p.addRoundedRect(outer, self.RX, self.RX)
            painter.fillPath(p, qcolor(C["bg_card"]))

            # Header bar
            hr = QRectF(ChatScene.LEFT_MARGIN, y0, ChatScene.CONTENT_W, self.HEADER_H)
            hp = QPainterPath()
            hp.addRoundedRect(hr, self.RX, self.RX)
            hp.addRect(ChatScene.LEFT_MARGIN, y0 + self.HEADER_H - self.RX, ChatScene.CONTENT_W, self.RX)
            painter.fillPath(hp, qcolor(C["bg_darker"]))

            self._draw_chevron(painter, ChatScene.LEFT_MARGIN + 10, y0 + 10, down=True)
            painter.setFont(font(11))
            painter.setPen(qcolor(C["text_secondary"]))
            painter.drawText(QPointF(ChatScene.LEFT_MARGIN + 28, y0 + 15), self._title)
            if self._status:
                painter.setFont(font(10))
                painter.setPen(qcolor(C["text_muted"]))
                painter.drawText(QPointF(ChatScene.LEFT_MARGIN + 96, y0 + 15), self._status)
        else:
            fr = QRectF(ChatScene.LEFT_MARGIN, y0, ChatScene.CONTENT_W, self.FOLD_H)
            p = QPainterPath()
            p.addRoundedRect(fr, self.RX, self.RX)
            painter.fillPath(p, qcolor(C["bg_card"]))
            self._draw_chevron(painter, ChatScene.LEFT_MARGIN + 12, y0 + 11, down=False)
            painter.setFont(font(11))
            painter.setPen(qcolor(C["text_secondary"]))
            painter.drawText(QPointF(ChatScene.LEFT_MARGIN + 28, y0 + 15), self._title)
            if self._status:
                painter.setFont(font(10))
                painter.setPen(qcolor(C["text_muted"]))
                painter.drawText(QPointF(ChatScene.LEFT_MARGIN + 96, y0 + 15), self._status)

    def _draw_chevron(self, painter, cx, cy, down):
        pen = QPen(qcolor(C["accent_blue"]), 1.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        path = QPainterPath()
        if down:
            path.moveTo(cx - 2, cy - 1); path.lineTo(cx, cy + 2); path.lineTo(cx + 2, cy - 1)
        else:
            path.moveTo(cx - 1, cy - 2); path.lineTo(cx + 2, cy); path.lineTo(cx - 1, cy + 2)
        painter.drawPath(path)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            hr = QRectF(ChatScene.LEFT_MARGIN, 0, ChatScene.CONTENT_W, self.FOLD_H if not self._expanded else self.HEADER_H)
            if hr.contains(event.pos()):
                self.toggle()
                event.accept()
                return
        super().mousePressEvent(event)

    def hoverMoveEvent(self, event):
        hr = QRectF(ChatScene.LEFT_MARGIN, 0, ChatScene.CONTENT_W, self.FOLD_H if not self._expanded else self.HEADER_H)
        self.setCursor(Qt.PointingHandCursor if hr.contains(event.pos()) else Qt.ArrowCursor)

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, ChatScene.CHAT_W, self._h)


class ToolEntry(ChatItem):
    """SVG: 4px左bar + ✓ + 工具名 + 耗时 + ▶参数"""
    def __init__(self, name: str, elapsed: str, success: bool = True, parent=None):
        super().__init__(parent)
        self._name = name
        self._elapsed = elapsed
        self._icon = "✓" if success else "✗"
        self._success = success
        self._h = 16
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        y = 1.0
        # 4px bar（SVG dark #2a2a4a=border; light #e9ecef=bg_sidebar）
        bar_color = C["border"] if theme.name == "dark" else C["bg_sidebar"]
        br = QRectF(ChatScene.LEFT_MARGIN + 10, y, 4, 14)
        bp = QPainterPath()
        bp.addRoundedRect(br, 2, 2)
        painter.fillPath(bp, qcolor(bar_color))
        # icon：运行时读取当前主题色，避免实例化时固定深色
        icon_color = C["green"] if self._success else "#f14c4c"
        painter.setFont(mono_font(10))
        painter.setPen(qcolor(icon_color))
        painter.drawText(QPointF(ChatScene.LEFT_MARGIN + 22, y + 11), self._icon)
        # name
        painter.setPen(qcolor(C["mono_text"]))
        painter.drawText(QPointF(ChatScene.LEFT_MARGIN + 33, y + 11), self._name)
        # elapsed
        painter.setFont(mono_font(9))
        painter.setPen(qcolor(C["text_muted"]))
        painter.drawText(QPointF(ChatScene.LEFT_MARGIN + 134, y + 11), self._elapsed)
        # args chevron
        painter.setPen(qcolor(C["accent_blue"]))
        painter.drawText(QPointF(ChatScene.LEFT_MARGIN + 189, y + 11), "▶ 参数")


class PhasePanel(ChatItem):
    """阶段面板：rx=8卡片 + 4px accent bar + header + body（body 自动垂直堆叠）。"""
    HEADER_H = 24.0
    RX = 8.0
    BODY_TOP = 8.0
    # 颜色键（避免类定义时捕获固定颜色）
    PHASE_COLORS = {
        "analyze": "accent_blue", "execute": "yellow",
        "archive": "green", "verify": "purple",
    }

    def __init__(self, title: str, accent_key: str, body_items: list = None, parent=None):
        super().__init__(parent)
        self._title = title
        self._accent_key = accent_key
        self._body_items = body_items or []
        # 自动布局 body items 并计算总高度
        y = self.HEADER_H + self.BODY_TOP
        for item in self._body_items:
            item.setParentItem(self)
            item.setPos(ChatScene.LEFT_MARGIN, y)
            y += item.height() + 6
        self._body_h = max(0.0, y - self.HEADER_H - self.BODY_TOP)
        self._h = self.HEADER_H + self._body_h + 16

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        y = 4.0
        card_h = self.HEADER_H + self._body_h + 8

        # 卡片（dark bg_sidebar #16213e; light bg_card #ffffff）
        cr = QRectF(ChatScene.LEFT_MARGIN, y, ChatScene.CONTENT_W, card_h)
        cp = QPainterPath()
        cp.addRoundedRect(cr, self.RX, self.RX)
        painter.fillPath(cp, qcolor(C["bg_card"]))
        pen = QPen(qcolor(C["border"]), 0.5)
        painter.setPen(pen)
        painter.drawPath(cp)

        # accent bar：运行时读取当前主题色
        accent = C.get(self._accent_key, C["accent_blue"])
        ar = QRectF(ChatScene.LEFT_MARGIN, y, 4, card_h)
        ap = QPainterPath()
        ap.addRoundedRect(ar, 2, 2)
        painter.fillPath(ap, qcolor(accent))

        # header
        hr = QRectF(ChatScene.LEFT_MARGIN + 4, y, ChatScene.CONTENT_W - 4, self.HEADER_H)
        hp = QPainterPath()
        hp.addRoundedRect(hr, 6, 6)
        hp.addRect(ChatScene.LEFT_MARGIN + 4, y + self.HEADER_H - 6, ChatScene.CONTENT_W - 4, 6)
        painter.fillPath(hp, qcolor(C["bg_darker"]))
        painter.setPen(qcolor(C["text_primary"]))
        painter.setFont(font(12, bold=True))
        painter.drawText(QPointF(ChatScene.LEFT_MARGIN + 14, y + 17), self._title)


class BulletItem(ChatItem):
    """● + 文本（自动换行）"""
    INDENT = 23.0
    TOP = 14.0

    def __init__(self, text: str, color_key: str = "green", parent=None):
        super().__init__(parent)
        self._text = text
        self._color_key = color_key
        fnt = font(10)
        max_w = max(40.0, ChatScene.CONTENT_W - self.INDENT - 10)
        _, th = _wrap_text_size(text, fnt, max_w)
        self._h = max(20.0, th + 10)
        self._text_rect = QRectF(ChatScene.LEFT_MARGIN + self.INDENT, 4, max_w, th)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        color = qcolor(C[self._color_key])
        painter.setPen(Qt.NoPen)
        painter.setBrush(color)
        painter.drawEllipse(QPointF(ChatScene.LEFT_MARGIN + 13, self.TOP), 3, 3)
        painter.setFont(font(10))
        painter.setPen(color)
        to = QTextOption()
        to.setWrapMode(QTextOption.WordWrap)
        painter.drawText(self._text_rect, self._text, to)


class StepItem(ChatItem):
    """执行步骤：✓/⟳/○ + 名称 + 详情（自动换行）"""
    ICONS = {"done": ("✓", "green"), "running": ("⟳", "yellow"),
             "pending": ("○", "text_muted"), "fail": ("✗", "#f14c4c")}
    ICON_X = 14.0
    TEXT_X = 29.0

    def __init__(self, status: str, name: str, detail: str = "", parent=None):
        super().__init__(parent)
        self._icon, self._ic_key = self.ICONS.get(status, ("○", "text_muted"))
        self._name = name
        self._detail = detail
        name_fnt = font(10)
        detail_fnt = font(9)
        max_w = max(40.0, ChatScene.CONTENT_W - self.TEXT_X - 10)
        _, name_h = _wrap_text_size(name, name_fnt, max_w)
        self._name_rect = QRectF(ChatScene.LEFT_MARGIN + self.TEXT_X, 4, max_w, name_h)
        if detail:
            _, detail_h = _wrap_text_size(detail, detail_fnt, max_w)
            self._detail_rect = QRectF(ChatScene.LEFT_MARGIN + self.TEXT_X, 6 + name_h, max_w, detail_h)
            self._h = max(20.0, 6 + name_h + detail_h + 6)
        else:
            self._detail_rect = None
            self._h = max(20.0, name_h + 10)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        # 图标颜色运行时解析
        ic = C.get(self._ic_key, C["text_muted"]) if self._ic_key.startswith("#") is False else self._ic_key
        painter.setFont(mono_font(10))
        painter.setPen(qcolor(ic))
        painter.drawText(QPointF(ChatScene.LEFT_MARGIN + self.ICON_X, 16), self._icon)
        painter.setFont(font(10))
        painter.setPen(qcolor(C["text_primary"]))
        to = QTextOption()
        to.setWrapMode(QTextOption.WordWrap)
        painter.drawText(self._name_rect, self._name, to)
        if self._detail_rect:
            painter.setFont(font(9))
            painter.setPen(qcolor(C["text_muted"]))
            painter.drawText(self._detail_rect, self._detail, to)


class TextItem(ChatItem):
    """纯文本块（自动换行）。"""
    TEXT_X = 14.0

    def __init__(self, text: str, color_key: str = "green", parent=None):
        super().__init__(parent)
        self._text = text
        self._color_key = color_key
        fnt = font(10)
        max_w = max(40.0, ChatScene.CONTENT_W - self.TEXT_X - 10)
        _, th = _wrap_text_size(text, fnt, max_w)
        self._h = max(22.0, th + 10)
        self._text_rect = QRectF(ChatScene.LEFT_MARGIN + self.TEXT_X, 4, max_w, th)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setFont(font(10))
        painter.setPen(qcolor(C[self._color_key]))
        to = QTextOption()
        to.setWrapMode(QTextOption.WordWrap)
        painter.drawText(self._text_rect, self._text, to)


class SystemCard(ChatItem):
    """居中系统卡片（支持自动换行）。"""
    PAD_X = 14.0
    PAD_Y = 10.0

    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self._text = text
        fnt = font(11)
        max_text_w = max(40.0, ChatScene.CONTENT_W - 2 * self.PAD_X)
        tw, th = _wrap_text_size(text, fnt, max_text_w)
        cw = min(ChatScene.CONTENT_W, tw + 2 * self.PAD_X)
        ch = th + 2 * self.PAD_Y
        self._crect = QRectF((ChatScene.CHAT_W - cw) / 2, 4, cw, ch)
        self._text_rect = QRectF(self._crect.left() + self.PAD_X, self._crect.top() + self.PAD_Y,
                                 cw - 2 * self.PAD_X, th)
        self._h = ch + 8

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        cp = QPainterPath()
        cp.addRoundedRect(self._crect, 8, 8)
        painter.fillPath(cp, qcolor(C["bg_card"]))
        painter.setPen(QPen(qcolor(C["border"]), 0.5))
        painter.drawPath(cp)
        painter.setFont(font(11))
        painter.setPen(qcolor(C["text_primary"]))
        to = QTextOption()
        to.setWrapMode(QTextOption.WordWrap)
        to.setAlignment(Qt.AlignCenter)
        painter.drawText(self._text_rect, self._text, to)


# ══════════════════════════════════════════════════════════════
# 聊天场景
# ══════════════════════════════════════════════════════════════

def _strip_html(raw: str) -> str:
    """将 HTML 片段转为纯文本，用于 QGraphicsItem 渲染。"""
    if not raw:
        return ""
    text = re.sub(r'<[^>]+>', '', raw)
    return html.unescape(text).strip()


def _wrap_text_size(text: str, fnt: QFont, max_w: float, line_spacing: int = 2) -> tuple[float, float]:
    """计算文本在指定最大宽度下自动换行后的包围盒尺寸。"""
    fm = QFontMetrics(fnt)
    rect = fm.boundingRect(QRect(0, 0, max(1, int(max_w)), 1000000), Qt.TextWordWrap, text)
    # boundingRect 返回的是 tight rect，实际行高用 fm.height()
    lines = max(1, int(rect.height() / fm.height() + 0.5))
    h = lines * fm.height() + (lines - 1) * line_spacing
    return rect.width(), h
