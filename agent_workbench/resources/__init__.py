"""agent_workbench/resources — 产品品牌资产。

包含应用图标（PNG/ICO）与 PyInstaller 打包所需的静态资源。
"""
from __future__ import annotations

import os

_RESOURCES_DIR = os.path.dirname(os.path.abspath(__file__))

APP_ICON_PNG = os.path.join(_RESOURCES_DIR, "app_icon.png")
APP_ICON_ICO = os.path.join(_RESOURCES_DIR, "app_icon.ico")
