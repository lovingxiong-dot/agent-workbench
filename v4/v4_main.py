"""v4 归档入口：保留旧 UI 完整版的可启动入口，用于独立打包 v4 版本。

注意：v4 已进入只读归档状态，本文件仅用于生成 dist/AgentWorkbenchV4/。
v5 主线请使用根目录 main.py。
"""
import sys

from PySide6.QtWidgets import QApplication

from v4.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Agent Workbench V4")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
