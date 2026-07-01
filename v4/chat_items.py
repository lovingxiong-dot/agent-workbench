"""
chat_items.py — QGraphicsItem 消息元素（像素级对齐 SVG 设计稿）

坐标系：以聊天区左上角为原点(0,0)，宽402px。
左留白=20px，内容宽=362px，右留白=20px。

每个 Item 的 paint() 直接对照 ui-chat-area.svg 中的 x/y/w/h/rx/fill/stroke 赋值。
"""
from __future__ import annotations

from PySide6.QtWidgets import QGraphicsItem, QGraphicsTextItem, QGraphicsSceneMouseEvent, QStyleOptionGraphicsItem, QWidget
from PySide6.QtCore import Qt, QRectF, QPointF, Signal, QObject
from PySide6.QtGui import QPainter, QPainterPath, QPen, QBrush, QColor, QFont, QFontMetrics

# ══════════════════════════════════════════════════════════════
# SVG 精确常量（来自 ui-chat-area.svg / ui-full-dark.svg）
# ══════════════════════════════════════════════════════════════

CHAT_WIDTH = 402
LEFT_MARGIN = 20
RIGHT_MARGIN = 20
CONTENT_WIDTH = CHAT_WIDTH - LEFT_MARGIN - RIGHT_MARGIN  # 362

# 颜色（精确匹配 SVG fill/stroke）
C_BG_PRIMARY      = QColor("#1a1a2e")
C_BG_SIDEBAR       = QColor("#16213e")
C_BG_RIGHT         = QColor("#0f1729")
C_BG_DARKER        = QColor("#1a1a2e")  # header bar 深色
C_ACCENT           = QColor("#007acc")
C_BORDER           = QColor("#2a2a4a")
C_TEXT_PRIMARY     = QColor("#e0e0e0")
C_TEXT_SECONDARY   = QColor("#a0a0b0")
C_TEXT_MUTED       = QColor("#6a6a8a")
C_TEXT_INVERSE     = QColor("#ffffff")
C_ACCENT_BLUE      = QColor("#569cd6")  # chevrons, analyze accent
C_GREEN            = QColor("#4ec9b0")  # checkmarks, archive
C_YELLOW           = QColor("#dcdcaa")  # execute accent
C_MONO_TEXT        = QColor("#d4d4d4")  # monospace code text
C_GRAY             = QColor("#858585")  # pending steps
C_TAG_BG           = QColor("#0f3460")  # tag/mode bg

# 字体
FONT_FAMILY = "Segoe UI"
MONO_FAMILY = "Cascadia Code"


def _font(size: int, bold: bool = False, family: str = FONT_FAMILY) -> QFont:
    f = QFont(family, size)
    f.setBold(bold)
    f.setStyleStrategy(QFont.PreferAntialias)
    return f


def _mono_font(size: int) -> QFont:
    f = QFont(MONO_FAMILY, size)
    f.setStyleHint(QFont.Monospace)
    f.setStyleStrategy(QFont.PreferAntialias)
    return f


def _text_width(fm: QFontMetrics, text: str) -> float:
    return fm.horizontalAdvance(text)


# ══════════════════════════════════════════════════════════════
# 基础消息 Item
# ══════════════════════════════════════════════════════════════

class BaseMessageItem(QGraphicsItem):
    """所有聊天消息的基类。存储相对于场景的 y 偏移。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._item_height: float = 0
        self.setZValue(0)

    def item_height(self) -> float:
        return self._item_height

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, CHAT_WIDTH, self._item_height)


# ══════════════════════════════════════════════════════════════
# 用户消息气泡
# SVG: <rect x="240" y="56" width="148" height="26" rx="8" fill="#007acc"/>
#      <text x="365" y="74" fill="#fff" font-size="11" text-anchor="end">
# ══════════════════════════════════════════════════════════════

class UserBubbleItem(BaseMessageItem):
    """用户消息：右对齐 #007acc 圆角色块。宽度按文本自适应，最小 60px，最大 CONTENT_WIDTH。"""

    # 精确锚点 = 右边缘 - 14px（SVG: 文本在 x=365，chat右边=402，402-365=37, 气泡右边缘=240+148=388, 402-388=14）
    RIGHT_PAD = 14

    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self._text = text

        # 使用 11px Segoe UI 计算文本宽度
        f = _font(11, bold=False)
        fm = QFontMetrics(f)
        self._text_width = fm.horizontalAdvance(text)

        # 气泡尺寸：SVG 中 padding 约 12px*2=24
        bubble_w = max(60.0, min(float(CONTENT_WIDTH), self._text_width + 24.0))
        bubble_h = 26.0  # SVG 精确高度
        bubble_x = CHAT_WIDTH - self.RIGHT_PAD - bubble_w

        self._bubble_rect = QRectF(bubble_x, 0, bubble_w, bubble_h)
        self._text_rect = QRectF(bubble_x + 12, 0, bubble_w - 24, bubble_h)

        self._item_height = bubble_h + 8  # 4px 上下间距
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget | None = None):
        painter.setRenderHint(QPainter.Antialiasing)

        # 气泡背景
        path = QPainterPath()
        path.addRoundedRect(self._bubble_rect, 8, 8)
        painter.fillPath(path, C_ACCENT)

        # 文本：右对齐，SVG: x=365 text-anchor=end
        painter.setFont(_font(11))
        painter.setPen(C_TEXT_INVERSE)
        painter.drawText(self._text_rect, Qt.AlignRight | Qt.AlignVCenter, self._text)


# ══════════════════════════════════════════════════════════════
# 折叠块（思考过程 / 工具执行 / 内部命令输出）
# SVG 收起: <rect x="20" y="96" w="362" h="22" rx="4" fill="#16213e"/>
# SVG 展开: <rect x="20" y="122" w="362" h="62" rx="4" fill="#16213e"/>
#           <rect x="20" y="122" w="362" h="20" rx="4" fill="#1a1a2e"/>  ← header bar
# ══════════════════════════════════════════════════════════════

class FoldBlockItem(BaseMessageItem):
    """可折叠块：收起时 22px 薄条，展开时显示 body 内容。
    
    交互：点击 header 区域切换展开/收起。
    """

    toggled = Signal()

    FOLD_H = 22.0       # 收起高度
    HEADER_H = 20.0     # 展开时 header bar 高度
    CARD_RX = 4.0       # 圆角

    def __init__(self, title: str, status_text: str = "", parent=None):
        super().__init__(parent)
        self._title = title
        self._status = status_text
        self._expanded = False
        self._body_items: list[QGraphicsItem] = []
        self._body_height: float = 0

        self._item_height = self.FOLD_H + 4  # 4px 上下间距
        self.setAcceptHoverEvents(True)
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)

    def set_body(self, items: list[QGraphicsItem], body_height: float):
        """设置展开时的 body 内容。每个 item 会作为子项加入。"""
        self._body_items = items
        self._body_height = body_height
        for item in items:
            item.setParentItem(self)
            item.setVisible(False)

    def expand(self):
        if not self._expanded:
            self._expanded = True
            self._item_height = self.HEADER_H + self._body_height + 4
            for item in self._body_items:
                item.setVisible(True)
            self.prepareGeometryChange()
            self.toggled.emit()

    def collapse(self):
        if self._expanded:
            self._expanded = False
            self._item_height = self.FOLD_H + 4
            for item in self._body_items:
                item.setVisible(False)
            self.prepareGeometryChange()
            self.toggled.emit()

    def toggle(self):
        if self._expanded:
            self.collapse()
        else:
            self.expand()

    def is_expanded(self) -> bool:
        return self._expanded

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget | None = None):
        painter.setRenderHint(QPainter.Antialiasing)

        y_offset = 0.0  # 4px top margin handled by scene layout

        if self._expanded:
            # 外层卡片
            outer = QRectF(LEFT_MARGIN, y_offset, CONTENT_WIDTH, self.HEADER_H + self._body_height)
            path = QPainterPath()
            path.addRoundedRect(outer, self.CARD_RX, self.CARD_RX)
            painter.fillPath(path, C_BG_SIDEBAR)

            # Header bar（深色）
            header_rect = QRectF(LEFT_MARGIN, y_offset, CONTENT_WIDTH, self.HEADER_H)
            hpath = QPainterPath()
            hpath.addRoundedRect(header_rect, self.CARD_RX, self.CARD_RX)
            # 覆盖底部圆角让 header 无缝衔接 body
            hpath.addRect(LEFT_MARGIN, y_offset + self.HEADER_H - self.CARD_RX, CONTENT_WIDTH, self.CARD_RX)
            painter.fillPath(hpath, C_BG_DARKER)

            # Chevron ▼ (down = expanded)
            self._draw_chevron(painter, LEFT_MARGIN + 10, y_offset + 10, down=True)

            # 标题
            painter.setFont(_font(11, bold=False))
            painter.setPen(C_TEXT_SECONDARY)
            painter.drawText(QPointF(LEFT_MARGIN + 28, y_offset + 15), self._title)

            # 状态
            if self._status:
                painter.setFont(_font(10))
                painter.setPen(C_TEXT_MUTED)
                painter.drawText(QPointF(LEFT_MARGIN + 96, y_offset + 15), self._status)
        else:
            # 收起态：单条薄矩形
            fold_rect = QRectF(LEFT_MARGIN, y_offset, CONTENT_WIDTH, self.FOLD_H)
            path = QPainterPath()
            path.addRoundedRect(fold_rect, self.CARD_RX, self.CARD_RX)
            painter.fillPath(path, C_BG_SIDEBAR)

            # Chevron ▶ (right = collapsed)
            self._draw_chevron(painter, LEFT_MARGIN + 12, y_offset + 11, down=False)

            # 标题
            painter.setFont(_font(11, bold=False))
            painter.setPen(C_TEXT_SECONDARY)
            painter.drawText(QPointF(LEFT_MARGIN + 28, y_offset + 15), self._title)

            # 状态
            if self._status:
                painter.setFont(_font(10))
                painter.setPen(C_TEXT_MUTED)
                painter.drawText(QPointF(LEFT_MARGIN + 96, y_offset + 15), self._status)

    def _draw_chevron(self, painter: QPainter, cx: float, cy: float, down: bool):
        """绘制 4×6 小三角。"""
        pen = QPen(C_ACCENT_BLUE, 1.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        if down:
            # ▼: M cx-2 cy-1 L cx cy+2 L cx+2 cy-1
            path = QPainterPath()
            path.moveTo(cx - 2, cy - 1)
            path.lineTo(cx, cy + 2)
            path.lineTo(cx + 2, cy - 1)
            painter.drawPath(path)
        else:
            # ▶: M cx-1 cy-2 L cx+2 cy L cx-1 cy+2
            path = QPainterPath()
            path.moveTo(cx - 1, cy - 2)
            path.lineTo(cx + 2, cy)
            path.lineTo(cx - 1, cy + 2)
            painter.drawPath(path)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        if event.button() == Qt.LeftButton:
            # 检查是否点击在 header 区域
            header_rect = QRectF(LEFT_MARGIN, 0, CONTENT_WIDTH, self.FOLD_H if not self._expanded else self.HEADER_H)
            if header_rect.contains(event.pos()):
                self.toggle()
                event.accept()
                return
        super().mousePressEvent(event)

    def hoverMoveEvent(self, event):
        header_rect = QRectF(LEFT_MARGIN, 0, CONTENT_WIDTH, self.FOLD_H if not self._expanded else self.HEADER_H)
        if header_rect.contains(event.pos()):
            self.setCursor(Qt.PointingHandCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, CHAT_WIDTH, self._item_height)


# ══════════════════════════════════════════════════════════════
# 工具执行条目
# SVG: 4px 左 bar + ✓ 图标 + 工具名 + 耗时 + ▶ 参数
# ══════════════════════════════════════════════════════════════

class ToolEntryItem(BaseMessageItem):
    """单个工具执行条目。高度 14px + 2px 间距 = 16px。"""

    ENTRY_H = 14.0
    BAR_X = LEFT_MARGIN + 10      # SVG: x=30
    BAR_W = 4.0
    ICON_X = LEFT_MARGIN + 22     # SVG: x=42
    NAME_X = LEFT_MARGIN + 33     # SVG: x=53
    TIME_X = LEFT_MARGIN + 134    # SVG: x=154
    ARGS_X = LEFT_MARGIN + 189    # SVG: x=209

    def __init__(self, tool_name: str, elapsed_ms: int, success: bool, parent=None):
        super().__init__(parent)
        self._name = tool_name
        self._elapsed = f"{elapsed_ms / 1000:.1f}s" if elapsed_ms >= 100 else f"{elapsed_ms}ms"
        self._icon = "✓" if success else "✗"
        self._icon_color = C_GREEN if success else QColor("#f14c4c")
        self._item_height = self.ENTRY_H + 2  # 13px step + 2px gap
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget | None = None):
        painter.setRenderHint(QPainter.Antialiasing)
        y = 1.0

        # 4px 左 bar（rx=2）
        bar_rect = QRectF(self.BAR_X, y, self.BAR_W, self.ENTRY_H)
        bar_path = QPainterPath()
        bar_path.addRoundedRect(bar_rect, 2, 2)
        painter.fillPath(bar_path, C_BORDER)

        # ✓ / ✗
        painter.setFont(_mono_font(10))
        painter.setPen(self._icon_color)
        painter.drawText(QPointF(self.ICON_X, y + 11), self._icon)

        # 工具名
        painter.setPen(C_MONO_TEXT)
        painter.drawText(QPointF(self.NAME_X, y + 11), self._name)

        # 耗时
        painter.setFont(_mono_font(9))
        painter.setPen(C_TEXT_MUTED)
        painter.drawText(QPointF(self.TIME_X, y + 11), self._elapsed)

        # ▶ 参数（SVG: #569cd6, 9px）
        painter.setPen(C_ACCENT_BLUE)
        painter.drawText(QPointF(self.ARGS_X, y + 11), "▶ 参数")


# ══════════════════════════════════════════════════════════════
# 阶段面板
# SVG:
#   <rect w="362" h="72" rx="8" fill="#16213e" stroke="#2a2a4a"/>
#   <rect w="4"   h="72" rx="2" fill="#569cd6"/>          ← 左边 accent bar
#   <rect w="358" h="24" rx="6" fill="#1a1a2e"/>          ← header
#   <text ...>📋 分析结果</text>
#   <circle r="3" fill="#4ec9b0"/>  <text>项目采用...</text>
# ══════════════════════════════════════════════════════════════

# 阶段 → 颜色映射
PHASE_COLORS = {
    "analyze": C_ACCENT_BLUE,   # #569cd6
    "confirm": C_ACCENT_BLUE,
    "execute": C_YELLOW,        # #dcdcaa
    "verify":  QColor("#c586c0"),
    "archive": C_GREEN,         # #4ec9b0
}

PHASE_TITLES = {
    "analyze": "📋 分析结果",
    "confirm": "📋 分析结果",
    "execute": "📝 执行计划",
    "verify":  "🔍 验证结果",
    "archive": "✅ 完成报告",
}

STEP_ICONS = {"done": ("✓", C_GREEN), "running": ("⟳", C_YELLOW), "pending": ("○", C_TEXT_MUTED), "fail": ("✗", QColor("#f14c4c"))}


class PhasePanelItem(BaseMessageItem):
    """阶段面板：outer card + 4px accent bar + header + body 内容。"""

    HEADER_H = 24.0
    CARD_RX = 8.0

    def __init__(self, phase: str, parent=None):
        super().__init__(parent)
        self._phase = phase
        self._accent_color = PHASE_COLORS.get(phase, C_ACCENT_BLUE)
        self._title = PHASE_TITLES.get(phase, "📋 结果")
        self._body_items: list[QGraphicsItem] = []
        self._body_h: float = 0
        self._item_height = self.HEADER_H + 4  # minimum: header + margin
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)

    def set_body(self, items: list[QGraphicsItem], body_height: float):
        self._body_items = items
        self._body_h = body_height
        self._item_height = self.HEADER_H + body_height + 16  # header + body + padding
        for item in items:
            item.setParentItem(self)

    def phase_header_h(self) -> float:
        return self.HEADER_H

    def accent_color(self) -> QColor:
        return self._accent_color

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget | None = None):
        painter.setRenderHint(QPainter.Antialiasing)
        y = 4.0
        card_h = self.HEADER_H + self._body_h + 8

        # 外层卡片 rx=8
        card_rect = QRectF(LEFT_MARGIN, y, CONTENT_WIDTH, card_h)
        card_path = QPainterPath()
        card_path.addRoundedRect(card_rect, self.CARD_RX, self.CARD_RX)
        painter.fillPath(card_path, C_BG_SIDEBAR)
        # stroke 0.5px
        pen = QPen(C_BORDER, 0.5)
        painter.setPen(pen)
        painter.drawPath(card_path)

        # 4px 左边 accent bar（rx=2，叠加在卡片左边）
        accent_rect = QRectF(LEFT_MARGIN, y, 4, card_h)
        apath = QPainterPath()
        apath.addRoundedRect(accent_rect, 2, 2)
        painter.fillPath(apath, self._accent_color)

        # Header（深色，从 accent bar 右侧开始）
        header_rect = QRectF(LEFT_MARGIN + 4, y, CONTENT_WIDTH - 4, self.HEADER_H)
        hpath = QPainterPath()
        hpath.addRoundedRect(header_rect, 6, 6)
        hpath.addRect(LEFT_MARGIN + 4, y + self.HEADER_H - 6, CONTENT_WIDTH - 4, 6)
        painter.fillPath(hpath, C_BG_DARKER)

        # Header 文本
        painter.setPen(Qt.NoPen)
        painter.setFont(_font(12, bold=True))
        painter.setPen(C_TEXT_PRIMARY)
        painter.drawText(QPointF(LEFT_MARGIN + 14, y + 17), self._title)


# ══════════════════════════════════════════════════════════════
# Phase 面板 body 中的步骤条 / 文本项
# ══════════════════════════════════════════════════════════════

class PhaseStepItem(BaseMessageItem):
    """执行计划中的一个步骤条目。"""
    ITEM_H = 20.0

    def __init__(self, status: str, name: str, detail: str = "", parent=None):
        super().__init__(parent)
        self._icon, self._icon_color = STEP_ICONS.get(status, ("○", C_TEXT_MUTED))
        self._name = name
        self._detail = detail
        self._item_height = self.ITEM_H
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget | None = None):
        painter.setRenderHint(QPainter.Antialiasing)
        # 定位在 panel body 内（由父级 PhasePanelItem 的 body area 偏移）
        y = 4

        # 步骤图标
        painter.setFont(_mono_font(10))
        painter.setPen(self._icon_color)
        painter.drawText(QPointF(LEFT_MARGIN + 14, y + 12), self._icon)

        # 步骤名
        painter.setFont(_font(10))
        painter.setPen(C_TEXT_PRIMARY)
        painter.drawText(QPointF(LEFT_MARGIN + 29, y + 12), self._name)

        # 详情
        if self._detail:
            painter.setFont(_font(9))
            painter.setPen(C_TEXT_MUTED)
            # 估算详情起始 x
            fm = QFontMetrics(_font(10))
            name_w = fm.horizontalAdvance(self._name)
            painter.drawText(QPointF(LEFT_MARGIN + 29 + name_w + 8, y + 12), self._detail)


class PhaseBulletItem(BaseMessageItem):
    """分析结果中的 bullet 条目：● + 文本。"""
    ITEM_H = 20.0

    def __init__(self, text: str, color: QColor = C_GREEN, parent=None):
        super().__init__(parent)
        self._text = text
        self._color = color
        self._item_height = self.ITEM_H
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget | None = None):
        painter.setRenderHint(QPainter.Antialiasing)
        y = 4

        # Bullet 圆点（r=3, fill=green）
        painter.setPen(Qt.NoPen)
        painter.setBrush(self._color)
        painter.drawEllipse(QPointF(LEFT_MARGIN + 13, y + 10), 3, 3)

        # 文本
        painter.setFont(_font(10))
        painter.setPen(self._color)
        painter.drawText(QPointF(LEFT_MARGIN + 23, y + 13), self._text)


class PhaseTextItem(BaseMessageItem):
    """阶段面板中的纯文本行（例如「v4.0.5-alpha 存档完成」）。"""
    ITEM_H = 22.0

    def __init__(self, text: str, color: QColor = C_GREEN, parent=None):
        super().__init__(parent)
        self._text = text
        self._color = color
        self._item_height = self.ITEM_H
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget | None = None):
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setFont(_font(10))
        painter.setPen(self._color)
        painter.drawText(QPointF(LEFT_MARGIN + 14, 15), self._text)


# ══════════════════════════════════════════════════════════════
# 系统通知卡片
# ══════════════════════════════════════════════════════════════

class SystemCardItem(BaseMessageItem):
    """居中系统通知卡片。"""

    CARD_PAD_X = 14
    CARD_PAD_Y = 10

    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self._text = text

        f = _font(11)
        fm = QFontMetrics(f)
        max_w = CONTENT_WIDTH - self.CARD_PAD_X * 2
        self._text_lines = self._wrap_text(fm, text, max_w)
        self._line_h = fm.height() + 2

        card_w = min(CONTENT_WIDTH, max(fm.horizontalAdvance(line) for line in self._text_lines) + self.CARD_PAD_X * 2 + 4)
        card_h = len(self._text_lines) * self._line_h + self.CARD_PAD_Y * 2
        self._card_rect = QRectF((CHAT_WIDTH - card_w) / 2, 4, card_w, card_h)
        self._item_height = card_h + 8
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)

    @staticmethod
    def _wrap_text(fm: QFontMetrics, text: str, max_w: float) -> list[str]:
        lines = []
        for line in text.split("\n"):
            if fm.horizontalAdvance(line) <= max_w:
                lines.append(line)
            else:
                current = ""
                for ch in line:
                    test = current + ch
                    if fm.horizontalAdvance(test) > max_w and current:
                        lines.append(current)
                        current = ch
                    else:
                        current = test
                if current:
                    lines.append(current)
        return lines

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget | None = None):
        painter.setRenderHint(QPainter.Antialiasing)

        # 卡片背景
        path = QPainterPath()
        path.addRoundedRect(self._card_rect, 8, 8)
        painter.fillPath(path, C_BG_SIDEBAR)
        pen = QPen(C_BORDER, 0.5)
        painter.setPen(pen)
        painter.drawPath(path)

        # 文本
        painter.setFont(_font(11))
        painter.setPen(C_TEXT_PRIMARY)
        y = self._card_rect.top() + self.CARD_PAD_Y
        for line in self._text_lines:
            painter.drawText(QPointF(self._card_rect.left() + self.CARD_PAD_X, y + self._line_h - 3), line)
            y += self._line_h
