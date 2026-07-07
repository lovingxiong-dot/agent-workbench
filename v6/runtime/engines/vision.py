"""v6/runtime/engines/vision.py — Vision Engine 空壳。

设计来源：V6.5 Runtime Foundation Layer Step 4。

当前阶段：Runtime 骨架验证，不接入任何视觉模型或图像处理库。
未来职责：图像理解、OCR、视觉问答、多模态输入。
"""
from __future__ import annotations

from v6.runtime.engines.base import BaseEngine


class VisionEngine(BaseEngine):
    """Vision Engine：负责视觉与多模态处理。"""

    name = "vision"
    capabilities = ["image_understanding"]
