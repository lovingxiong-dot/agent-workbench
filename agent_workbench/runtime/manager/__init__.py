"""agent_workbench/runtime/manager — Manager Runtime 实现层。

v6.9.3-alpha 引入 ManagerRuntime，作为 UserRequest → CapabilityMatch → Task 的默认路由层。
"""
from __future__ import annotations

from agent_workbench.runtime.manager.runtime import ManagerRuntime

__all__ = ["ManagerRuntime"]
