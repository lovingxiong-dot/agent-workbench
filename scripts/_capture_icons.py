"""截图验证：dark / light 双主题，覆盖四项目标修改。"""
import sys, os, time
sys.path.insert(0, r"f:\Agent\agent_workbench")
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from experiments.ui_template import MainWindow, theme

app = QApplication(sys.argv)
w = MainWindow()
w.show()

ts = str(int(time.time()))
screenshot_dir = r"f:\Agent\agent_workbench\_screenshots"
os.makedirs(screenshot_dir, exist_ok=True)

QTimer.singleShot(800, lambda: (
    w.grab().save(os.path.join(screenshot_dir, f"icon_dark_{ts}.png")),
    theme.set_theme("light"),
    QTimer.singleShot(600, lambda: (
        w.grab().save(os.path.join(screenshot_dir, f"icon_light_{ts}.png")),
        app.quit()
    ))
))

app.exec()
