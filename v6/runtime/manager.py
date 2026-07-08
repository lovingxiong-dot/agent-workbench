"""v6/runtime/manager.py — Manager 协议。

设计边界：
- Manager 位于 UserRequest 与 Task 之间，是 Runtime 任务生成策略的抽象。
- Runtime 不依赖具体 Manager 实现，只依赖此协议。
- 未来可实现 RuleManager / LLMManager / PolicyManager / HumanApprovalManager 等。
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from v6.runtime.task import Task
from v6.runtime.user_request import UserRequest


@runtime_checkable
class Manager(Protocol):
    """任务管理器协议。

    Manager 接收用户请求，决定如何将其转换为一个可提交的 Task。
    """

    def resolve(self, request: UserRequest) -> Task:
        """将 UserRequest 解析为 Task。

        Args:
            request: 用户请求，可能来自 UI、API、CLI、Workflow 或 System。

        Returns:
            一个已设置 capability 的 Task，可直接提交给 Runtime。
        """
        ...
