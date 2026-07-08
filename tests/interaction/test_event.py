"""tests/interaction/test_event.py — InteractionEvent 协议测试。"""
from __future__ import annotations

from agent_workbench.runtime.interaction import InteractionEvent, InteractionEventType


def test_interaction_event_carries_source() -> None:
    event = InteractionEvent(
        type=InteractionEventType.TASK_STARTED,
        request_id="req-1",
        source="command_bar",
        task_id="task-1",
        payload={"task_type": "tool"},
    )
    assert event.source == "command_bar"
    assert event.task_id == "task-1"
    assert event.payload["task_type"] == "tool"
