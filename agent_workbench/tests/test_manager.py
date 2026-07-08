"""agent_workbench/tests/test_manager.py — Manager 层测试。

验证 UserRequest → Manager → Task → submit_task() 主链。
"""
from __future__ import annotations

import pytest

from v6.runtime.enums import RuntimeState
from v6.runtime.task import Task
from v6.runtime.user_request import UserRequest

from agent_workbench.controller import WorkbenchController
from agent_workbench.services.manager import AgentManager


@pytest.fixture
def controller() -> WorkbenchController:
    ctrl = WorkbenchController()
    ctrl.start()
    try:
        yield ctrl
    finally:
        ctrl.stop()


def test_agent_manager_resolves_chat_request() -> None:
    """AgentManager 将普通文本请求解析为 chat capability 任务。"""
    manager = AgentManager()
    request = UserRequest(text="hello", session_id="sess-chat")

    task = manager.resolve(request)

    assert task.capability == "chat"
    assert task.payload.get("text") == "hello"
    assert task.session_id == "sess-chat"


def test_agent_manager_resolves_tool_request() -> None:
    """AgentManager 根据 metadata 中的 task_type 解析为 tool capability 任务。"""
    manager = AgentManager()
    request = UserRequest(
        session_id="sess-tool",
        metadata={
            "task_type": "tool",
            "tool_request": {"tool": "echo", "args": {"text": "hi"}},
        },
    )

    task = manager.resolve(request)

    assert task.capability == "tool"
    assert task.metadata["task_type"] == "tool"
    assert task.metadata["tool_request"]["tool"] == "echo"


def test_controller_chat_uses_manager(controller: WorkbenchController) -> None:
    """验证 controller.chat() 通过 Manager 生成 Task 并提交到 Runtime。"""
    captured: list[Task] = []
    original_resolve = controller._manager.resolve

    def _spy(request: UserRequest) -> Task:
        task = original_resolve(request)
        captured.append(task)
        return task

    controller._manager.resolve = _spy
    try:
        ctx = controller.chat("hello manager", session_id="sess-mgr")
        assert ctx.status == RuntimeState.COMPLETED
        assert len(captured) == 1
        assert captured[0].capability == "chat"
        assert captured[0].metadata["capability_id"] == "chat"
        assert captured[0].payload.get("text") == "hello manager"
    finally:
        controller._manager.resolve = original_resolve


def test_user_request_to_engine_chain(controller: WorkbenchController) -> None:
    """验证完整主链：UserRequest → Manager → Task → CapabilityRouter → Engine。"""
    request = UserRequest(text="chain test", session_id="sess-chain")
    task = controller._manager.resolve(request)
    ctx = controller.submit_task(task)

    assert ctx.status == RuntimeState.COMPLETED
    assert any(m.role == "assistant" for m in ctx.messages)
