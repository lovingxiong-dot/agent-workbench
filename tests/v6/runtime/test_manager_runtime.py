"""tests/v6/runtime/test_manager.py — ManagerRuntime 单元测试。"""
from __future__ import annotations

import threading

from v6.runtime.event_bus import EventBus
from v6.runtime.user_request import UserRequest

from agent_workbench.runtime.capability.graph import CapabilityRegistry
from agent_workbench.runtime.manager.runtime import ManagerRuntime


def _make_registry() -> CapabilityRegistry:
    registry = CapabilityRegistry()
    registry.load_defaults()
    return registry


def test_manager_resolves_chat_request():
    registry = _make_registry()
    manager = ManagerRuntime(registry)
    request = UserRequest(text="hello")

    task = manager.resolve(request)

    # Commit 2 保持旧 capability 取值，真实 Context 在 metadata。
    assert task.capability == "chat"
    assert task.metadata["capability_id"] == "chat"
    assert task.payload["text"] == "hello"


def test_manager_resolves_tool_request():
    registry = _make_registry()
    manager = ManagerRuntime(registry)
    request = UserRequest(
        text="execute command",
        metadata={"task_type": "tool", "tool_request": {"name": "terminal"}},
    )

    task = manager.resolve(request)

    assert task.capability == "tool"
    assert task.metadata["capability_id"] == "tool"
    assert task.payload["tool_request"] == {"name": "terminal"}


def test_manager_resolves_coding_request():
    registry = _make_registry()
    manager = ManagerRuntime(registry)
    request = UserRequest(text="fix this bug")

    task = manager.resolve(request)

    # Commit 2 Task.capability 保持旧 "chat"，真实 Capability Context 在 metadata。
    assert task.capability == "chat"
    assert task.metadata["capability_id"] == "coding.python.debugging"
    assert task.metadata["capability_path"] == [
        "assistant",
        "coding",
        "coding.python",
        "coding.python.debugging",
    ]


def test_manager_sets_capability_metadata():
    registry = _make_registry()
    manager = ManagerRuntime(registry)
    request = UserRequest(text="review code")

    task = manager.resolve(request)

    assert task.metadata["capability_id"] == "analyze"
    assert task.metadata["capability_name"] == "Analyze"
    assert "capability_path" in task.metadata


def test_manager_fallback_to_chat_for_unknown_input():
    registry = _make_registry()
    manager = ManagerRuntime(registry)
    request = UserRequest(text="xyzabc unknown topic")

    task = manager.resolve(request)

    assert task.capability == "chat"
    assert task.metadata["capability_id"] == "chat"


def test_manager_preserves_session_and_task_id():
    registry = _make_registry()
    manager = ManagerRuntime(registry)
    request = UserRequest(
        text="hello",
        session_id="session-1",
        task_id="task-1",
    )

    task = manager.resolve(request)

    assert task.session_id == "session-1"
    assert task.id == "task-1"


def test_manager_publishes_events_when_bus_running():
    registry = _make_registry()
    event_bus = EventBus()
    event_bus.start()
    received = []
    done = threading.Event()

    def callback(event) -> None:
        received.append(event.type)
        if len(received) >= 2:
            done.set()

    event_bus.subscribe("manager.intent.classified", callback)
    event_bus.subscribe("manager.capability.selected", callback)

    try:
        manager = ManagerRuntime(registry, event_bus=event_bus)
        request = UserRequest(text="hello", metadata={"task_id": "t-manager"})
        manager.resolve(request)

        done.wait(timeout=2.0)
        assert "manager.intent.classified" in received
        assert "manager.capability.selected" in received
    finally:
        event_bus.stop()


def test_manager_silent_when_bus_not_running():
    registry = _make_registry()
    event_bus = EventBus()
    manager = ManagerRuntime(registry, event_bus=event_bus)
    request = UserRequest(text="hello")

    # 总线未启动不应抛错。
    task = manager.resolve(request)
    assert task.metadata["capability_id"] == "chat"


def test_manager_builds_capability_chain_for_coding_python():
    from agent_workbench.runtime.capability import CapabilityChain

    registry = _make_registry()
    manager = ManagerRuntime(registry)
    request = UserRequest(text="analyze and fix this python code")

    task = manager.resolve(request)

    chain_steps = CapabilityChain.from_metadata(task.metadata)
    assert chain_steps is not None
    assert [step.capability_id for step in chain_steps] == [
        "coding.python.analysis",
        "coding.python.debugging",
        "coding.python.testing",
    ]


def test_manager_builds_capability_chain_for_coding():
    from agent_workbench.runtime.capability import CapabilityChain

    registry = _make_registry()
    manager = ManagerRuntime(registry)
    request = UserRequest(text="structure code")

    task = manager.resolve(request)

    chain_steps = CapabilityChain.from_metadata(task.metadata)
    assert chain_steps is not None
    assert [step.capability_id for step in chain_steps] == [
        "coding.python.analysis",
        "coding.python.debugging",
        "coding.python.testing",
        "coding.code_editor",
    ]


def test_manager_no_chain_for_chat():
    from agent_workbench.runtime.capability import CapabilityChain

    registry = _make_registry()
    manager = ManagerRuntime(registry)
    request = UserRequest(text="hello")

    task = manager.resolve(request)

    assert "capability_chain" not in task.metadata
    assert CapabilityChain.from_metadata(task.metadata) is None
