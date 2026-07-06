"""v6/runtime/engine_state.py — Engine 生命周期状态枚举。

设计来源：V6.5 Runtime Foundation Layer Step 3。

核心原则：
- EngineState 与 RuntimeState 分离：前者管理 Engine 实例生命周期，后者管理 Task 生命周期。
- Engine 生命周期：CREATED → LOADING → LOADED → INITIALIZING → READY → RUNNING → STOPPING → STOPPED。
- DEGRADED / ERROR 为健康检查返回的非正常状态。
"""
from __future__ import annotations

from enum import Enum


class EngineState(str, Enum):
    """Engine 实例生命周期状态。"""

    CREATED = "created"
    LOADING = "loading"
    LOADED = "loaded"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    DEGRADED = "degraded"
    ERROR = "error"
    STOPPING = "stopping"
    STOPPED = "stopped"
