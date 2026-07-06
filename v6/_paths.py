"""v6/_paths.py — 跨模块共享的数据目录路径。

数据目录规则：
- 测试/开发可通过环境变量 V6_DATA_DIR 覆盖
- 开发/源码运行时：项目根目录下的 storage/
- PyInstaller 打包后：exe 同级目录下的 storage/
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def data_dir() -> Path:
    """返回 V6 数据目录（默认 storage/，可被 V6_DATA_DIR 覆盖）。"""
    env = os.environ.get("V6_DATA_DIR")
    if env:
        return Path(env)
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).resolve().parent
    else:
        base = Path(__file__).resolve().parents[1]
    return base / "storage"
