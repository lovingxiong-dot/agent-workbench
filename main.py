#!/usr/bin/env python3
"""
AI Agent Workbench v4 · 单轨架构入口
"""
import sys
import os
import traceback

# 确保项目根在 sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _diagnostic_hook(exc_type, exc_value, exc_tb):
    """全局异常钩子：把未捕获异常打印到 stderr 并刷新"""
    print("=" * 60, file=sys.stderr)
    print("UNCAUGHT PYTHON EXCEPTION", file=sys.stderr)
    traceback.print_exception(exc_type, exc_value, exc_tb)
    print("=" * 60, file=sys.stderr)
    sys.stderr.flush()


sys.excepthook = _diagnostic_hook

from PySide6.QtWidgets import QApplication
from v4.main_window import MainWindow


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("AI Agent Workbench")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
