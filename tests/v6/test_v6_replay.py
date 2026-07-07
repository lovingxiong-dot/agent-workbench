"""tests/v6/test_v6_replay.py — Runtime Trace Replay Foundation 测试。"""
from __future__ import annotations

import time

from v6.runtime.context import RuntimeContext
from v6.runtime.engine_manager import EngineManager
from v6.runtime.engines import LLMEngine
from v6.runtime.event_bus import EventBus, RuntimeEvent, RuntimeEventType
from v6.runtime.replay import ReplayLog, ReplayRecord, ReplayService
from v6.runtime.trace import RuntimeTrace


def test_replay_record_from_event() -> None:
    event = RuntimeEvent(
        type=RuntimeEventType.ENGINE_STARTED,
        payload={
            "input_snapshot": {"prompt": "hello"},
            "output_snapshot": {},
            "metadata": {"engine": "llm"},
        },
        task_id="t1",
        trace_id="trace-1",
        source="engine:llm",
        phase="inference",
    )
    record = ReplayRecord.from_event(event)
    assert record.trace_id == "trace-1"
    assert record.task_id == "t1"
    assert record.component == "engine:llm"
    assert record.component_type == "engine"
    assert record.event_type == RuntimeEventType.ENGINE_STARTED
    assert record.input_snapshot == {"prompt": "hello"}
    assert record.metadata == {"engine": "llm"}


def test_replay_log_timeline_sorted() -> None:
    log = ReplayLog()
    log.add(ReplayRecord(trace_id="a", task_id="t1", timestamp=2.0, component="engine:llm", component_type="engine", event_type="start"))
    log.add(ReplayRecord(trace_id="a", task_id="t1", timestamp=1.0, component="engine:tool", component_type="engine", event_type="start"))
    timeline = log.timeline()
    assert len(timeline) == 2
    assert timeline[0]["component"] == "engine:tool"
    assert timeline[1]["component"] == "engine:llm"


def test_replay_log_filter_by_task_id() -> None:
    log = ReplayLog()
    log.add(ReplayRecord(trace_id="a", task_id="t1", timestamp=1.0, component="engine:llm", component_type="engine", event_type="start"))
    log.add(ReplayRecord(trace_id="a", task_id="t2", timestamp=2.0, component="engine:tool", component_type="engine", event_type="start"))
    filtered = log.filter(task_id="t1")
    assert len(filtered) == 1
    assert filtered[0].task_id == "t1"


def test_replay_service_imports_from_trace() -> None:
    trace = RuntimeTrace()
    trace.add(
        node="engine:llm",
        action="engine_start",
        phase="inference",
        payload={"input_snapshot": {"prompt": "hi"}, "output_snapshot": {"text": "hello"}},
    )
    service = ReplayService()
    count = service.import_from_trace(trace, task_id="t1")
    assert count == 1
    timeline = service.timeline(task_id="t1")
    assert len(timeline) == 1
    assert timeline[0]["component"] == "engine:llm"
    assert timeline[0]["input_snapshot"] == {"prompt": "hi"}
    assert timeline[0]["output_snapshot"] == {"text": "hello"}


def test_replay_service_view_summary() -> None:
    trace = RuntimeTrace()
    trace.add(node="engine:llm", action="engine_start", phase="inference", payload={})
    trace.add(node="engine:tool", action="engine_start", phase="tool", payload={})
    service = ReplayService()
    service.import_from_trace(trace, task_id="t1")
    view = service.view(task_id="t1")
    assert view["record_count"] == 2
    assert view["components"] == {"engine:llm": 1, "engine:tool": 1}


def test_replay_service_subscribes_to_event_bus() -> None:
    bus = EventBus()
    bus.start()
    try:
        service = ReplayService()
        service.attach(bus)
        bus.publish(
            RuntimeEventType.ENGINE_STARTED,
            {"input_snapshot": {"x": 1}},
            task_id="t-sub",
            source="engine:llm",
        )
        time.sleep(0.1)
        records = service.log.filter(task_id="t-sub")
        assert len(records) == 1
        assert records[0].component == "engine:llm"
        assert records[0].input_snapshot == {"x": 1}
    finally:
        bus.stop()


def test_replay_service_export() -> None:
    service = ReplayService()
    service.log.add(
        ReplayRecord(
            trace_id="trace-1",
            task_id="t1",
            timestamp=1.0,
            component="runtime",
            component_type="runtime",
            event_type="task.started",
        )
    )
    exported = service.export()
    assert exported["record_count"] == 1
    assert exported["records"][0]["event_type"] == "task.started"


def test_replay_record_component_type_inference() -> None:
    assert ReplayRecord._infer_component_type("engine:llm") == "engine"
    assert ReplayRecord._infer_component_type("service:chat") == "service"
    assert ReplayRecord._infer_component_type("runtime") == "runtime"
    assert ReplayRecord._infer_component_type("tool:search") == "tool"


def test_replay_service_does_not_re_execute_engine() -> None:
    """第一版 ReplayService 只记录轨迹，不重新调用 Engine。"""
    ctx = RuntimeContext.new()
    manager = EngineManager(trace=ctx.trace)
    manager.register(LLMEngine())
    manager.initialize_all(ctx)

    ctx.request = {"prompt": "hello"}
    result = manager.execute("llm", ctx)
    assert len(ctx.trace.steps()) == 1

    service = ReplayService()
    service.import_from_trace(ctx.trace, task_id=ctx.task_id)
    timeline = service.timeline(task_id=ctx.task_id)
    assert len(timeline) == 1
    # 确认没有新的执行发生：result 不变，trace 步骤数不变
    assert result.status == "placeholder"
    assert len(ctx.trace.steps()) == 1
