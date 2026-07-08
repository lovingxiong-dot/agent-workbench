"""tests/interaction/test_mapper.py — RuntimeEvent → InteractionEvent 映射测试。"""
from __future__ import annotations

import pytest

from agent_workbench.runtime.interaction import InteractionEventType, RuntimeEventMapper
from v6.runtime.event_bus import RuntimeEvent, RuntimeEventType


@pytest.fixture
def mapper() -> RuntimeEventMapper:
    return RuntimeEventMapper()


def _event(event_type: RuntimeEventType, payload: dict, task_id: str = "task-1") -> RuntimeEvent:
    return RuntimeEvent(
        type=event_type.value,
        payload=payload,
        task_id=task_id,
        source="orchestrator",
    )


def test_mapper_ignores_unknown_event(mapper: RuntimeEventMapper) -> None:
    event = _event(RuntimeEventType.MODEL_SELECTED, {"model": "gpt-4"})
    assert mapper.map(event) is None


def test_mapper_maps_task_started(mapper: RuntimeEventMapper) -> None:
    event = _event(RuntimeEventType.TASK_STARTED, {"task_type": "action"})
    mapped = mapper.map(event)
    assert mapped is not None
    assert mapped.type == InteractionEventType.TASK_STARTED
    assert mapped.task_id == "task-1"


def test_mapper_maps_capability_chain_step(mapper: RuntimeEventMapper) -> None:
    event = _event(
        RuntimeEventType.CAPABILITY_CHAIN_STEP_STARTED,
        {"step_index": 1, "capability_id": "coding.python.debugging", "total_steps": 3},
    )
    mapped = mapper.map(event)
    assert mapped is not None
    assert mapped.type == InteractionEventType.CAPABILITY_STEP
    assert mapped.payload["index"] == 1
    assert mapped.payload["capability_id"] == "coding.python.debugging"
    assert mapped.payload["total"] == 3


def test_mapper_maps_engine_selected_to_status(mapper: RuntimeEventMapper) -> None:
    event = _event(
        RuntimeEventType.ENGINE_SELECTED,
        {"engine": "workbench_llm", "capability": "text_generation"},
    )
    mapped = mapper.map(event)
    assert mapped is not None
    assert mapped.type == InteractionEventType.STATUS_UPDATE
    assert mapped.payload["title"] == "选择执行引擎"


def test_mapper_maps_tool_events(mapper: RuntimeEventMapper) -> None:
    started = _event(RuntimeEventType.TOOL_STARTED, {"tool": "python_formatter", "args": {"file": "a.py"}})
    mapped_started = mapper.map(started)
    assert mapped_started is not None
    assert mapped_started.type == InteractionEventType.TOOL_STARTED
    assert mapped_started.payload["name"] == "python_formatter"

    completed = _event(RuntimeEventType.TOOL_COMPLETED, {"tool": "python_formatter", "result": {"ok": True}})
    mapped_completed = mapper.map(completed)
    assert mapped_completed is not None
    assert mapped_completed.type == InteractionEventType.TOOL_COMPLETED
    assert mapped_completed.payload["name"] == "python_formatter"


def test_mapper_maps_error_events(mapper: RuntimeEventMapper) -> None:
    event = _event(RuntimeEventType.ENGINE_FAILED, {"error": "engine crashed"})
    mapped = mapper.map(event)
    assert mapped is not None
    assert mapped.type == InteractionEventType.ERROR
    assert mapped.payload["message"] == "engine crashed"


def test_mapper_handles_empty_payload(mapper: RuntimeEventMapper) -> None:
    event = RuntimeEvent(
        type=RuntimeEventType.TASK_STARTED.value,
        payload=None,  # type: ignore[arg-type]
        task_id="task-1",
        source="orchestrator",
    )
    mapped = mapper.map(event)
    assert mapped is not None
    assert mapped.type == InteractionEventType.TASK_STARTED
    # payload 为 None 时按空 dict 处理，字段回退为默认值（如 task_type=None）。
    assert mapped.payload == {"task_type": None}


def test_mapper_defaults_source_to_unknown(mapper: RuntimeEventMapper) -> None:
    event = RuntimeEvent(
        type=RuntimeEventType.TASK_STARTED.value,
        payload={"task_type": "action"},
        task_id="task-1",
        source="orchestrator",
    )
    mapped = mapper.map(event)
    assert mapped is not None
    assert mapped.source == "unknown"


def test_mapper_unknown_event_returns_none(mapper: RuntimeEventMapper) -> None:
    event = RuntimeEvent(
        type="unknown.custom.event",
        payload={},
        task_id="task-1",
        source="orchestrator",
    )
    assert mapper.map(event) is None
