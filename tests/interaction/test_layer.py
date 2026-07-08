"""tests/interaction/test_layer.py — WorkbenchInteractionLayer 测试。"""
from __future__ import annotations

from unittest.mock import MagicMock

from agent_workbench.runtime.interaction import (
    InteractionEvent,
    InteractionEventType,
    RuntimeRequest,
    RuntimeRequestSource,
    UIEventRenderer,
    WorkbenchInteractionLayer,
)
from v6.runtime.enums import RuntimeState


class FakeRenderer(UIEventRenderer):
    def __init__(self) -> None:
        self.events: list[InteractionEvent] = []

    def render(self, event: InteractionEvent) -> None:
        self.events.append(event)


def _runtime(task_id: str = "task-1") -> MagicMock:
    runtime = MagicMock()
    runtime.core_runtime.event_bus = MagicMock()
    runtime.submit_request.return_value = task_id
    return runtime


def test_layer_subscribes_to_event_bus() -> None:
    runtime = _runtime()
    layer = WorkbenchInteractionLayer(runtime=runtime)
    runtime.core_runtime.event_bus.subscribe.assert_called_once()


def test_layer_submit_request_delegates_to_runtime() -> None:
    runtime = _runtime(task_id="task-1")
    layer = WorkbenchInteractionLayer(runtime=runtime)
    request = RuntimeRequest(text="hello")
    returned_id = layer.submit_request(request)
    # layer.submit_request 始终返回 request.request_id，而不是 runtime 返回的 task_id。
    assert returned_id == request.request_id
    runtime.submit_request.assert_called_once_with(request)


def test_layer_maps_event_to_renderer() -> None:
    runtime = _runtime(task_id="task-1")
    renderer = FakeRenderer()
    layer = WorkbenchInteractionLayer(runtime=runtime, renderer=renderer)

    # 先提交请求，建立 task_id -> request_id 映射。
    request = RuntimeRequest(text="hello")
    layer.submit_request(request)

    callback = runtime.core_runtime.event_bus.subscribe.call_args[0][1]
    from v6.runtime.event_bus import RuntimeEvent, RuntimeEventType

    event = RuntimeEvent(
        type=RuntimeEventType.TASK_STARTED.value,
        payload={"task_type": "action"},
        task_id="task-1",
        source="orchestrator",
    )
    callback(event)

    assert len(renderer.events) == 1
    assert renderer.events[0].type == InteractionEventType.TASK_STARTED
    assert renderer.events[0].request_id == request.request_id


def test_layer_renderer_errors_do_not_propagate() -> None:
    runtime = _runtime()

    class BrokenRenderer(UIEventRenderer):
        def render(self, event: InteractionEvent) -> None:
            raise RuntimeError("broken")

    layer = WorkbenchInteractionLayer(runtime=runtime, renderer=BrokenRenderer())
    callback = runtime.core_runtime.event_bus.subscribe.call_args[0][1]
    from v6.runtime.event_bus import RuntimeEvent, RuntimeEventType

    event = RuntimeEvent(
        type=RuntimeEventType.TASK_STARTED.value,
        payload={},
        task_id="task-1",
        source="orchestrator",
    )
    callback(event)  # 不应抛出异常


def test_layer_close_unsubscribes_from_event_bus() -> None:
    runtime = _runtime()
    layer = WorkbenchInteractionLayer(runtime=runtime)
    layer.close()

    callback = runtime.core_runtime.event_bus.subscribe.call_args[0][1]
    runtime.core_runtime.event_bus.unsubscribe.assert_called_once_with("*", callback)
    assert layer._renderer is None
    assert layer._subscribed is False


def test_layer_close_clears_task_mapping() -> None:
    runtime = _runtime(task_id="task-1")
    layer = WorkbenchInteractionLayer(runtime=runtime)
    request = RuntimeRequest(text="hello")
    layer.submit_request(request)

    layer.close()
    assert layer._task_to_request == {}


def test_layer_submit_request_failure_renders_error() -> None:
    runtime = _runtime()
    runtime.submit_request.side_effect = RuntimeError("runtime down")
    renderer = FakeRenderer()
    layer = WorkbenchInteractionLayer(runtime=runtime, renderer=renderer)

    request = RuntimeRequest(text="hello")
    returned_id = layer.submit_request(request)

    assert returned_id == request.request_id
    assert len(renderer.events) == 1
    assert renderer.events[0].type == InteractionEventType.ERROR
    assert renderer.events[0].request_id == request.request_id
    assert "runtime down" in renderer.events[0].payload["message"]
