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
from PySide6.QtCore import QTimer
from services.app_context import AppContext
from services.session_orchestrator import SessionOrchestrator
from ui.main_window import MainWindow


def _create_app_context():
    """创建全局服务容器"""
    app_root = os.path.dirname(os.path.abspath(__file__))
    storage_dir = AppContext.resolve_storage_dir(app_root)
    config_path = os.path.join(
        getattr(sys, "_MEIPASS", app_root) if getattr(sys, "frozen", False) else app_root,
        "config.yaml",
    )
    writable_config_path = (
        os.path.join(os.path.dirname(sys.executable), "config.yaml")
        if getattr(sys, "frozen", False)
        else config_path
    )
    return AppContext(
        config_path=config_path,
        writable_config_path=writable_config_path,
        storage_dir=storage_dir,
        app_root=app_root,
    )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("AI Agent Workbench")

    try:
        app_ctx = _create_app_context()
        orchestrator = SessionOrchestrator(
            app_context=app_ctx,
            message_bus=app_ctx.message_bus,
            task_service=app_ctx.task_service,
        )
        window = MainWindow(app_context=app_ctx, session_orchestrator=orchestrator)
        window.show()
        exit_code = app.exec()
        sys.exit(exit_code)
    except Exception as e:
        traceback.print_exc()
        sys.stderr.flush()
        raise
