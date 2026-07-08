"""agent_workbench/runtime/manager — Manager Runtime 实现层。

v6.9.3-alpha 引入 ManagerRuntime，作为 UserRequest → CapabilityMatch → Task 的默认路由层。
v6.9.4-alpha 引入 DecisionManager，作为 Runtime Decision Layer 的默认 Manager。
"""
from __future__ import annotations

from agent_workbench.runtime.manager.decision_manager import DecisionManager
from agent_workbench.runtime.manager.runtime import ManagerRuntime

__all__ = ["DecisionManager", "ManagerRuntime"]
