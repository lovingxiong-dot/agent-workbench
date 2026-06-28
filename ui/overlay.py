"""
OverlayWidget — 全局半透明遮罩层

用于在长时间操作（如 Agent 分析、文件加载）期间覆盖整个主窗口，
显示 loading 提示，阻止用户误操作。
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QProgressBar,
    QSizePolicy,
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QColor, QPalette


class OverlayWidget(QWidget):
    """半透明遮罩层，支持显示文本与进度条。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("overlayWidget")
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 默认隐藏
        self.hide()

        # 背景半透明黑
        self._opacity = 0.0
        self._base_color = QColor("#0D1117")
        self._update_palette()

        # 动画
        self._fade_in = QPropertyAnimation(self, b"overlay_opacity")
        self._fade_in.setDuration(200)
        self._fade_in.setEasingCurve(QEasingCurve.OutQuad)
        self._fade_in.setStartValue(0.0)
        self._fade_in.setEndValue(0.65)

        self._fade_out = QPropertyAnimation(self, b"overlay_opacity")
        self._fade_out.setDuration(150)
        self._fade_out.setEasingCurve(QEasingCurve.InQuad)
        self._fade_out.setStartValue(0.65)
        self._fade_out.setEndValue(0.0)
        self._fade_out.finished.connect(self.hide)

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(16)

        self._label = QLabel("处理中...")
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setStyleSheet("color: #E6EDF3; font-size: 14px; font-weight: bold;")
        layout.addWidget(self._label)

        self._progress = QProgressBar()
        self._progress.setRange(0, 0)  # 无限循环模式
        self._progress.setTextVisible(False)
        self._progress.setFixedSize(160, 4)
        self._progress.setStyleSheet("""
            QProgressBar {
                background-color: #30363D;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background-color: #58A6FF;
                border-radius: 2px;
            }
        """)
        layout.addWidget(self._progress, alignment=Qt.AlignCenter)

    # ── 属性动画 ─────────────────────────────
    def get_overlay_opacity(self) -> float:
        return self._opacity

    def set_overlay_opacity(self, value: float):
        self._opacity = max(0.0, min(1.0, value))
        self._update_palette()

    overlay_opacity = Property(float, get_overlay_opacity, set_overlay_opacity)

    def _update_palette(self):
        color = QColor(self._base_color)
        color.setAlphaF(self._opacity)
        palette = self.palette()
        palette.setColor(QPalette.Window, color)
        self.setPalette(palette)
        self.setAutoFillBackground(True)

    # ── 公共接口 ─────────────────────────────
    def show_overlay(self, text: str = "处理中..."):
        """显示遮罩层并播放淡入动画。"""
        self._label.setText(text)
        self._progress.setRange(0, 0)
        self.raise_()
        self.show()
        self._fade_out.stop()
        self._fade_in.start()

    def hide_overlay(self):
        """播放淡出动画后隐藏。"""
        self._fade_in.stop()
        self._fade_out.start()

    def set_text(self, text: str):
        """更新提示文本（保持显示状态）。"""
        self._label.setText(text)

    def set_progress(self, value: int, maximum: int = 100):
        """切换到确定进度模式；value < 0 时恢复无限循环。"""
        if value < 0:
            self._progress.setRange(0, 0)
            return
        self._progress.setRange(0, maximum)
        self._progress.setValue(value)
