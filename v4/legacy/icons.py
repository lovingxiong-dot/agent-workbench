"""
icons.py — v4 UI 公共 SVG 图标库

提供基于 SVG path 的 QIcon 渲染，避免依赖系统字体 emoji，确保跨平台一致。
"""
from PySide6.QtCore import QByteArray, QSize
from PySide6.QtGui import QIcon, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import Qt


ICON_PATHS = {
    "search": "M 10 10 a 4 4 0 1 0 0 8 a 4 4 0 1 0 0 -8 M 14 17 L 17 20",
    "more": "M6 12a1.5 1.5 0 1 0 3 0a1.5 1.5 0 1 0 -3 0 M12 12a1.5 1.5 0 1 0 3 0a1.5 1.5 0 1 0 -3 0 M18 12a1.5 1.5 0 1 0 3 0a1.5 1.5 0 1 0 -3 0",
    "expand": "M10 10H4V4M14 4h6v6M4 14v6h6M14 20h6v-6",
    "collapse": "M4 10V4h6M20 4v6h-6M4 14h6v6M20 20h-6v-6",
    "chevron-up": "M18 15l-6-6-6 6",
    "chevron-down": "M6 9l6 6 6-6",
    "close": "M6 6l12 12M18 6L6 18",
    "arrow-up": "M12 19V5M5 12l7-7 7 7",
    "arrow-left": "M19 12H5M12 19l-7-7 7-7",
    "arrow-right": "M5 12h14M12 5l7 7-7 7",
    "refresh": "M23 4v6h-6M1 20v-6h6M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15",
    "home": "M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z M9 22V12h6v10",
    "lightning": "M13 2L3 14h9l-1 8 10-12h-9l1-8z",
    "send": "M12 19V5M5 12l7-7 7 7",
    "send-plane": "M 21 3 L 3 12 L 10 14 L 21 3 Z M 21 3 L 14 21 L 10 14 L 21 3 Z",
}


def _render_svg(name: str, color: str, size: int) -> QPixmap:
    """渲染 SVG 到 QPixmap。"""
    path_data = ICON_PATHS.get(name, "")
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.5" '
        f'stroke-linecap="round" stroke-linejoin="round">'
        f'<path d="{path_data}"/></svg>'
    )
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return pixmap


def svg_icon(name: str, color: str, size: int = 18) -> QIcon:
    """根据 SVG path 名称渲染矢量图标。"""
    return QIcon(_render_svg(name, color, size))


def svg_pixmap(name: str, color: str, size: int = 18) -> QPixmap:
    """根据 SVG path 名称渲染矢量 Pixmap。"""
    return _render_svg(name, color, size)
