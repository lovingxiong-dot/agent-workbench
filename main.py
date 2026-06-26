#!/usr/bin/env python3
"""
AI Agent 工作台 v2 · 手动模式专业版 (PySide6)
模式：Ask（问答） / Plan（规划） / Craft（执行）
所有模式均拥有完整工具权限，敏感操作二次确认。

v2 特性:
- 模块化架构 (ui/widgets · workers · services)
- 流式输出 · 模型下拉选择
- 对话持久化 (SQLite)
- .env 密钥管理 · Token 追踪
- 外部 QSS 主题系统
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
from ui.main_window import MainWindow


if __name__ == "__main__":
    print("[DIAG] main.py start", flush=True)
    app = QApplication(sys.argv)
    app.setApplicationName("AI Agent Workbench")
    print("[DIAG] QApplication created", flush=True)

    try:
        window = MainWindow()
        print("[DIAG] MainWindow created", flush=True)
        window.show()
        print("[DIAG] MainWindow shown", flush=True)
        exit_code = app.exec()
        print(f"[DIAG] app.exec() returned {exit_code}", flush=True)
        sys.exit(exit_code)
    except Exception as e:
        print(f"[DIAG] Exception during startup: {e}", flush=True)
        traceback.print_exc()
        sys.stderr.flush()
        raise
