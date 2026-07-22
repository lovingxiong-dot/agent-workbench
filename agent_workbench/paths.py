"""agent_workbench/paths.py — 统一路径解析。

支持三种运行模式：
1. PyInstaller 打包模式（sys.frozen）：以 sys.executable 所在目录为 App Root
2. AOS_HOME 环境变量：以 AOS_HOME 为数据根目录
3. 开发模式：以 __file__ 为基准解析

所有路径统一通过此模块获取，禁止在代码中直接使用 __file__ 计算路径。
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def _is_frozen() -> bool:
    """检测是否为 PyInstaller 打包环境。"""
    return getattr(sys, "frozen", False)


def _get_bundle_dir() -> Path | None:
    """返回 PyInstaller 临时解压目录（仅在打包模式下有效）。"""
    if _is_frozen():
        return Path(sys._MEIPASS)
    return None


def get_app_root() -> Path:
    """返回应用根目录。

    - 打包模式：sys.executable 所在目录
    - 开发模式：agent_workbench 包的父目录（即项目根目录）
    """
    if _is_frozen():
        return Path(sys.executable).resolve().parent
    # 开发模式：paths.py 在 agent_workbench/ 下，上一层是项目根目录
    return Path(__file__).resolve().parent.parent


def get_resource_dir() -> Path:
    """返回资源目录（打包模式下为 _MEIPASS，开发模式下为项目根目录）。

    用于读取 config/default.yaml、packages/ 等捆绑资源。
    """
    bundle = _get_bundle_dir()
    if bundle is not None:
        return bundle
    return get_app_root()


def get_config_dir() -> Path:
    """返回配置文件目录。"""
    return get_resource_dir() / "config"


def get_config_path() -> Path:
    """返回默认配置文件路径：config/default.yaml。"""
    return get_config_dir() / "default.yaml"


def get_packages_dir() -> Path:
    """返回 Agent Packages 目录。"""
    return get_resource_dir() / "packages"


def get_data_dir() -> Path:
    """返回用户数据根目录。

    优先级：
    1. AOS_HOME 环境变量
    2. %APPDATA%/AgentWorkbench（Windows）
    3. ~/.agent-workbench（Linux/macOS）
    """
    aos_home = os.environ.get("AOS_HOME")
    if aos_home:
        return Path(aos_home) / "data"

    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
        return Path(base) / "AgentWorkbench"
    xdg = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
    return Path(xdg) / "agent-workbench"


def get_sessions_dir() -> Path:
    """返回 Session 数据存储目录。"""
    return get_data_dir() / "sessions"


def get_env_path() -> Path | None:
    """返回 .env 文件路径（可能不存在）。"""
    path = get_app_root() / "config" / ".env"
    return path if path.exists() else None


def get_icon_path() -> Path:
    """返回应用图标路径（app_icon.ico）。"""
    return get_resource_dir() / "resources" / "app_icon.ico"


def ensure_dirs() -> None:
    """确保所有必要的数据目录存在。"""
    get_sessions_dir().mkdir(parents=True, exist_ok=True)