import os
import sys

THEMES = {
    "dark_github": "resources/themes/dark_github.qss",
    "dark_vscode": "resources/themes/dark_vscode.qss",
    "light_minimal": "resources/themes/light_minimal.qss",
    "trae_dark": "resources/themes/trae_dark.qss",
}


class ThemeService:
    def __init__(self):
        self.current = "trae_dark"

    @staticmethod
    def _app_root() -> str:
        """exe 环境下用 _MEIPASS，源码环境下用项目根"""
        if getattr(sys, 'frozen', False):
            return sys._MEIPASS
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def get_qss(self, name=None) -> str:
        name = name or self.current
        relative = THEMES.get(name, THEMES["dark_github"])
        path = os.path.join(self._app_root(), relative)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        return ""

    def list_themes(self) -> list:
        return list(THEMES.keys())

    def set_theme(self, name):
        if name in THEMES:
            self.current = name
