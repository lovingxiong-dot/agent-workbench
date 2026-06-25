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

# 确保项目根在 sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("AI Agent Workbench")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
