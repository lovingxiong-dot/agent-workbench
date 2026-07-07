"""agent_workbench/runtime — Agent Workbench V6 内部 Runtime 封装层。

该层属于 Application Layer，不是 v6-core / v6-service 的一部分。
职责：
- 组合 ConfigStore、ProfileManager、EventBus、ModuleRegistry。
- 为 WorkbenchController 提供单一入口。
"""
from __future__ import annotations
