"""tests/v6/runtime/test_orchestrator_chain.py — Orchestrator Capability Chain 测试。"""
from __future__ import annotations

import threading

from v6.runtime.enums import RuntimeState
from v6.runtime.task import Task
from v6.runtime.user_request import UserRequest

from agent_workbench.controller import WorkbenchController


def _controller() -> WorkbenchController:
    controller = WorkbenchController()
    controller.start()
    return controller


def test_orchestrator_executes_capability_chain_in_order():
    controller = _controller()
    try:
        request = UserRequest(text="analyze and fix this python code")
        task = controller._manager.resolve(request)

        assert "capability_chain" in task.metadata
        assert len(task.metadata["capability_chain"]) == 3

        ctx = controller.submit_task(task)

        assert ctx.status == RuntimeState.COMPLETED
        trace_nodes = [step["node"] for step in ctx.trace.snapshot().get("steps", [])]
        # 链式任务应触发多次 LLM Engine 执行。
        assert trace_nodes.count("engine:llm") >= 3
    finally:
        controller.stop()


def test_orchestrator_publishes_chain_step_events():
    controller = _controller()
    event_bus = controller._runtime.core_runtime.event_bus
    received = []
    done = threading.Event()

    def callback(event) -> None:
        if event.type == "capability.chain.step.started":
            received.append(event.payload)
            if len(received) >= 3:
                done.set()

    event_bus.subscribe("capability.chain.step.started", callback)

    try:
        request = UserRequest(text="analyze and fix this python code")
        task = controller._manager.resolve(request)
        controller.submit_task(task)

        done.wait(timeout=2.0)
        assert len(received) == 3
        assert [p["step_index"] for p in received] == [0, 1, 2]
        assert received[0]["capability_id"] == "coding.python.analysis"
        assert received[1]["capability_id"] == "coding.python.debugging"
        assert received[2]["capability_id"] == "coding.python.testing"
    finally:
        controller.stop()


def test_orchestrator_chain_stops_on_step_failure():
    controller = _controller()
    try:
        # 手动构建一个包含不存在 engine capability 的链，触发执行失败。
        task = Task(
            id="chain-fail",
            capability="chat",
            payload={"text": "chain failure test"},
            metadata={
                "capability_id": "custom",
                "capability_path": ["custom"],
                "capability_chain": [
                    {
                        "capability_id": "step.ok",
                        "engine_capability": "text_generation",
                        "payload_overrides": {},
                        "persona": {},
                    },
                    {
                        "capability_id": "step.bad",
                        "engine_capability": "nonexistent_capability",
                        "payload_overrides": {},
                        "persona": {},
                    },
                ],
            },
        )

        ctx = controller.submit_task(task)

        assert ctx.status == RuntimeState.FAILED
    finally:
        controller.stop()


def test_orchestrator_ignores_chain_for_legacy_chat_task():
    controller = _controller()
    try:
        request = UserRequest(text="hello")
        task = controller._manager.resolve(request)

        assert "capability_chain" not in task.metadata

        ctx = controller.submit_task(task)

        assert ctx.status == RuntimeState.COMPLETED
        trace_nodes = [step["node"] for step in ctx.trace.snapshot().get("steps", [])]
        # 旧任务只走一次 LLM Engine。
        assert trace_nodes.count("engine:llm") >= 1
    finally:
        controller.stop()
