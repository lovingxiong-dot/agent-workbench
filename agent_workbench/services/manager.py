"""agent_workbench/services/manager.py — AgentManager 实现。

职责：
- 将 UserRequest 转换为 Task。
- Foundation 阶段使用规则判断 capability；后续可替换为 LLM、策略或人工审批实现。
- 不直接调用 Runtime，只输出 Task。
"""
from __future__ import annotations

from typing import Any

from v6.runtime.manager import Manager
from v6.runtime.task import ChatTask, Task
from v6.runtime.user_request import UserRequest


class AgentManager:
    """默认 Agent 任务管理器。

    当前规则：
    - 若 request.metadata["task_type"] == "tool"，生成 tool capability 任务。
    - 否则生成 chat capability 任务（ChatTask）。
    """

    def resolve(self, request: UserRequest) -> Task:
        """将用户请求解析为 Task。"""
        metadata = dict(request.metadata or {})
        session_id = request.session_id
        task_id = request.task_id

        if metadata.get("task_type") == "tool":
            return Task(
                id=task_id,
                session_id=session_id,
                capability="tool",
                payload={
                    "text": request.text or "",
                    "tool_request": metadata.get("tool_request"),
                },
                metadata=metadata,
            )

        return ChatTask(
            text=request.text or "",
            session_id=session_id,
            id=task_id,
            metadata=metadata,
        )
