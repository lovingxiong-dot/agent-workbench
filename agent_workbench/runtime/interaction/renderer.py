"""agent_workbench/runtime/interaction/renderer.py — 向后兼容 re-export。

Phase 2-C.1：UIEventRenderer 已迁移至 presentation/protocols/interaction/renderer.py。
本文件保留为 re-export 别名，确保旧 import 路径不中断。
"""
from __future__ import annotations

from agent_workbench.presentation.protocols.interaction.renderer import UIEventRenderer

__all__ = ["UIEventRenderer"]