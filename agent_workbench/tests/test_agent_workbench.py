"""agent_workbench/tests/test_agent_workbench.py — Agent Workbench V6 端到端测试。

验证范围：
- WorkbenchController 装配 AgentWorkbenchRuntime + Workbench Engine。
- 用户消息经 WorkbenchController → Core Runtime → Orchestrator → Engine。
- Task Lifecycle：CREATED → PLANNING → EXECUTING → COMPLETED。
- Trace 记录 Engine 链路。
- Tool Engine 调用链路。
- ConfigStore 配置热更新。
- 默认 YAML 加载。
- CLI 入口可正常退出。
"""
from __future__ import annotations

import pytest

from v6.runtime.enums import RuntimeState

from agent_workbench.controller import WorkbenchController


@pytest.fixture
def controller() -> WorkbenchController:
    ctrl = WorkbenchController()
    ctrl.start()
    try:
        yield ctrl
    finally:
        ctrl.stop()


def test_agent_lifecycle_chat(controller: WorkbenchController) -> None:
    """验证单 Agent 聊天生命周期完整闭环。"""
    ctx = controller.chat("hello", session_id="sess-001")

    assert ctx.status == RuntimeState.COMPLETED
    assert any(m.role == "assistant" for m in ctx.messages)
    assistant_msg = [m for m in ctx.messages if m.role == "assistant"][-1]
    assert "V6 Agent Workbench" in assistant_msg.content

    timeline = controller.trace_timeline(ctx.task_id)
    nodes = {step["node"] for step in timeline}
    assert "engine:llm" in nodes


def test_agent_lifecycle_tool(controller: WorkbenchController) -> None:
    """验证 Tool Engine 调用链路。"""
    ctx = controller.chat_with_tool("get_time", {})

    assert ctx.status == RuntimeState.COMPLETED
    assert "tool_result" in ctx.result.extra
    assert "time" in ctx.result.extra["tool_result"]

    timeline = controller.trace_timeline(ctx.task_id)
    nodes = {step["node"] for step in timeline}
    assert "engine:tool" in nodes


def test_planner_loop_selects_llm_for_chat(controller: WorkbenchController) -> None:
    """验证 PlannerLoop 对 chat 任务选择 llm engine。"""
    ctx = controller.chat("analyze this text")

    assert ctx.status == RuntimeState.COMPLETED
    timeline = controller.trace_timeline(ctx.task_id)
    engine_steps = [s for s in timeline if s["node"] == "engine:llm"]
    assert len(engine_steps) >= 1


def test_planner_loop_selects_tool_for_tool_task(controller: WorkbenchController) -> None:
    """验证 PlannerLoop 对 tool 任务选择 tool engine。"""
    ctx = controller.chat_with_tool("echo", {"text": "hi"})

    assert ctx.status == RuntimeState.COMPLETED
    timeline = controller.trace_timeline(ctx.task_id)
    engine_steps = [s for s in timeline if s["node"] == "engine:tool"]
    assert len(engine_steps) >= 1


def test_config_store_read_write(controller: WorkbenchController) -> None:
    """验证 ConfigStore 支持点分路径读写。"""
    store = controller._runtime.config
    store.set("model.sampling.temperature", 0.5)
    assert store.get("model.sampling.temperature") == 0.5
    assert store.get("model.default_provider") == "echo"


def test_config_loader_reads_default_yaml() -> None:
    """验证配置加载器能读取默认 YAML。"""
    from agent_workbench.config.loader import ConfigLoader

    loader = ConfigLoader()
    loader.load()
    assert loader.get("agent.name") == "Agent Workbench V6"
    assert loader.get("runtime.use_orchestrator") is True


def test_app_cli_mode_exits_cleanly() -> None:
    """验证 app.py CLI 入口可正常退出。"""
    from agent_workbench.app import main

    result = main([
        "--mode", "cli",
        "--config", "agent_workbench/config/default.yaml",
        "--test-input", "hello",
    ])
    assert result == 0
