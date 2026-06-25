import os

THEMES = {
    "dark_github": "resources/themes/dark_github.qss",
    "dark_vscode": "resources/themes/dark_vscode.qss",
    "light_minimal": "resources/themes/light_minimal.qss",
}


class ThemeService:
    def __init__(self):
        self.current = "dark_github"

    def get_qss(self, name=None) -> str:
        name = name or self.current
        path = THEMES.get(name, THEMES["dark_github"])
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        return ""

    def list_themes(self) -> list:
        return list(THEMES.keys())

    def set_theme(self, name):
        if name in THEMES:
            self.current = name
