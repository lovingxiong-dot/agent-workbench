"""tests/ui/test_streaming_chat_loop.py — Streaming UI 事件与对话闭环测试。

覆盖 Commit 3 核心要求：
- AI_CHUNK / AI_END / ENGINE_FAILED 事件正确映射到 UI 信号。
- 流式输出不重复生成完整 AI 消息。
- 非流式路径（CHAT 模式）仍能显示完整回复。
"""
from __future__ import annotations

import os
import sys
import threading
import time
from typing import Any

import pytest
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from v6.runtime.context import RuntimeContext
from v6.runtime.enums import RuntimeState
from v6.runtime.event_bus import RuntimeEvent, RuntimeEventType

from agent_workbench.ui.workbench_ui_controller import WorkbenchUIController


class _SignalCollector(QObject):
    """收集 Qt 信号发射内容。"""

    def __init__(self) -> None:
        super().__init__()
        self.chunks: list[str] = []
        self.ai_messages: list[tuple[str, str]] = []
        self.stream_ends = 0
        self.streaming_states: list[bool] = []

    def connect_to(self, controller: WorkbenchUIController) -> None:
        controller.sign_stream_chunk.connect(self._on_chunk)
        controller.sign_chat_ai.connect(self._on_ai)
        controller.sign_stream_end.connect(self._on_end)
        controller.sign_set_streaming.connect(self._on_streaming)

    def _on_chunk(self, text: str) -> None:
        self.chunks.append(text)

    def _on_ai(self, text: str, phase: str) -> None:
        self.ai_messages.append((text, phase))

    def _on_end(self) -> None:
        self.stream_ends += 1

    def _on_streaming(self, streaming: bool) -> None:
        self.streaming_states.append(streaming)


@pytest.fixture(scope="session")
def qt_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


class TestStreamingEventMapping:
    """直接测试事件回调 → UI 信号的映射。"""

    @pytest.fixture
    def controller(self, qt_app, tmp_path):
        ctrl = WorkbenchUIController(workbench_host=None, data_dir=str(tmp_path))
        ctrl._current_task_id = "task-123"
        ctrl._streaming = True
        yield ctrl
        ctrl.shutdown()

    def test_ai_chunk_emits_stream_chunk(self, controller):
        collector = _SignalCollector()
        collector.connect_to(controller)

        event = RuntimeEvent(
            type=RuntimeEventType.AI_CHUNK,
            payload={"text": "hello", "phase": ""},
            task_id="task-123",
        )
        controller._on_ai_chunk(event)

        assert collector.chunks == ["hello"]
        assert controller._ai_parts == ["hello"]

    def test_ai_chunk_ignores_other_task(self, controller):
        collector = _SignalCollector()
        collector.connect_to(controller)

        event = RuntimeEvent(
            type=RuntimeEventType.AI_CHUNK,
            payload={"text": "ignored"},
            task_id="other-task",
        )
        controller._on_ai_chunk(event)

        assert collector.chunks == []

    def test_ai_end_emits_stream_end(self, controller):
        collector = _SignalCollector()
        collector.connect_to(controller)

        event = RuntimeEvent(
            type=RuntimeEventType.AI_END,
            payload={"response": "full response"},
            task_id="task-123",
        )
        controller._on_ai_end(event)

        assert collector.stream_ends == 1
        assert collector.streaming_states == [False]
        assert controller._streaming is False
        assert controller._current_task_id is None

    def test_ai_end_ignores_when_not_streaming(self, controller):
        collector = _SignalCollector()
        collector.connect_to(controller)
        controller._streaming = False

        event = RuntimeEvent(
            type=RuntimeEventType.AI_END,
            payload={},
            task_id="task-123",
        )
        controller._on_ai_end(event)

        assert collector.stream_ends == 0

    def test_engine_failed_emits_error_and_stream_end(self, controller):
        collector = _SignalCollector()
        collector.connect_to(controller)

        event = RuntimeEvent(
            type=RuntimeEventType.ENGINE_FAILED,
            payload={"error": "mock failure"},
            task_id="task-123",
        )
        controller._on_engine_failed(event)

        assert collector.ai_messages == [("[错误: mock failure]", "error")]
        assert collector.stream_ends == 1
        assert collector.streaming_states == [False]
        assert controller._streaming is False


class TestOnSendMsgSignalBehavior:
    """测试 on_send_msg 在不同 Runtime 行为下的 UI 信号输出。"""

    @pytest.fixture
    def controller(self, qt_app, tmp_path):
        config_path = tmp_path / "config.yaml"
        ctrl = WorkbenchUIController(
            workbench_host=None,
            data_dir=str(tmp_path),
            config_path=str(config_path),
        )
        ctrl._active_sid = "session-1"
        ctrl.startup()
        yield ctrl
        ctrl.shutdown()

    def _wait_for_thread(self, controller: WorkbenchUIController) -> None:
        thread = getattr(controller, "_workbench_thread", None)
        if thread is not None and thread.is_alive():
            thread.join(timeout=5.0)
        assert thread is None or not thread.is_alive()

    def test_non_streaming_path_emits_full_ai_message(self, controller, qt_app):
        collector = _SignalCollector()
        collector.connect_to(controller)

        def _mock_chat(text: str, session_id: str | None = None, task_id: str | None = None):
            ctx = RuntimeContext.new(task_id=task_id, session_id=session_id)
            ctx.add_message("assistant", "完整回复")
            ctx.status = RuntimeState.COMPLETED
            ctx.metadata["skipped_runtime"] = True
            return ctx

        controller._workbench.chat = _mock_chat  # type: ignore[method-assign]

        controller.on_send_msg("你好")
        self._wait_for_thread(controller)
        qt_app.processEvents()

        assert collector.ai_messages == [("完整回复", "")]
        assert collector.stream_ends == 1
        assert collector.streaming_states == [True, False]

    def test_streaming_path_does_not_duplicate_ai_message(self, controller, qt_app):
        collector = _SignalCollector()
        collector.connect_to(controller)

        def _mock_chat(text: str, session_id: str | None = None, task_id: str | None = None):
            # 同步模拟 Runtime 流式事件，避免事件总线异步导致竞态
            for chunk in ["片段1", "片段2", "片段3"]:
                controller._on_ai_chunk(
                    RuntimeEvent(
                        type=RuntimeEventType.AI_CHUNK,
                        payload={"text": chunk, "phase": ""},
                        task_id=task_id or "",
                    )
                )
            controller._on_ai_end(
                RuntimeEvent(
                    type=RuntimeEventType.AI_END,
                    payload={"response": "片段1片段2片段3"},
                    task_id=task_id or "",
                )
            )

            ctx = RuntimeContext.new(task_id=task_id, session_id=session_id)
            ctx.add_message("assistant", "片段1片段2片段3")
            ctx.status = RuntimeState.COMPLETED
            return ctx

        controller._workbench.chat = _mock_chat  # type: ignore[method-assign]

        controller.on_send_msg("你好")
        self._wait_for_thread(controller)
        qt_app.processEvents()

        assert collector.chunks == ["片段1", "片段2", "片段3"]
        assert collector.ai_messages == []
        assert collector.stream_ends == 1

    def test_error_path_emits_error_once(self, controller, qt_app):
        collector = _SignalCollector()
        collector.connect_to(controller)

        def _mock_chat(text: str, session_id: str | None = None, task_id: str | None = None):
            controller._on_engine_failed(
                RuntimeEvent(
                    type=RuntimeEventType.ENGINE_FAILED,
                    payload={"error": "provider down"},
                    task_id=task_id or "",
                )
            )
            raise RuntimeError("provider down")

        controller._workbench.chat = _mock_chat  # type: ignore[method-assign]

        controller.on_send_msg("你好")
        self._wait_for_thread(controller)
        qt_app.processEvents()

        assert collector.ai_messages == [("[错误: provider down]", "error")]
        assert collector.stream_ends == 1
