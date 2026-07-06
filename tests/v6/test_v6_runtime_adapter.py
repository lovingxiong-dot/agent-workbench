"""tests/v6/test_v6_runtime_adapter.py — RuntimeAdapter 契约与功能测试。"""
from __future__ import annotations

import time

import pytest

from v6.runtime.adapter import IRuntimeAdapter, LocalRuntimeAdapter
from v6.runtime.context import RuntimeContext
from v6.runtime.runtime import AgentRuntime


def test_adapter_submit_returns_task_id():
    """Adapter.submit(ctx) 返回 task_id。"""
    runtime = AgentRuntime()
    adapter = LocalRuntimeAdapter(runtime)
    adapter.start()
    try:
        ctx = RuntimeContext(task_id="t-1", session_id="s-1")
        task_id = adapter.submit(ctx)
        assert task_id == "t-1"
        adapter.runtime.scheduler.wait_all(timeout=2.0)
    finally:
        adapter.stop()


def test_adapter_cancel_task():
    """Adapter.cancel(task_id) 可取消尚未执行的任务。"""
    runtime = AgentRuntime()
    adapter = LocalRuntimeAdapter(runtime)
    adapter.start()
    try:
        ctx = RuntimeContext(task_id="t-cancel", session_id="s-1")
        task_id = adapter.submit(ctx)
        assert adapter.cancel(task_id) is True
    finally:
        adapter.stop()


def test_adapter_subscribe_event():
    """Adapter.subscribe 可订阅 Runtime 事件。"""
    runtime = AgentRuntime()
    adapter = LocalRuntimeAdapter(runtime)
    adapter.start()
    received = []
    try:
        adapter.subscribe("ai_end", lambda evt: received.append(evt))
        ctx = RuntimeContext(task_id="t-sub", session_id="s-1")
        adapter.submit(ctx)
        adapter.runtime.scheduler.wait_all(timeout=2.0)
        time.sleep(0.1)  # 等待事件总线分发完成
        assert any(e.type == "ai_end" for e in received)
    finally:
        adapter.stop()


def test_adapter_protocol_is_abstract():
    """IRuntimeAdapter 不能直接实例化。"""
    with pytest.raises(TypeError):
        IRuntimeAdapter()


def test_runtime_does_not_know_caller():
    """Runtime 不知道调用方是谁，只接收 Task。"""
    runtime = AgentRuntime()
    adapter = LocalRuntimeAdapter(runtime)
    # Runtime 只有 event_bus / scheduler / handlers 等内部成员，没有 caller/source 字段
    assert not hasattr(runtime, "caller")
    assert not hasattr(runtime, "source")


def test_adapter_submit_propagates_context():
    """Adapter.submit(ctx) 会把 ctx 传递给 Runtime，EchoHandler 读取 ctx.messages。"""
    import threading

    runtime = AgentRuntime()
    adapter = LocalRuntimeAdapter(runtime)
    adapter.start()
    done = threading.Event()
    try:
        adapter.subscribe("ai_end", lambda _evt: done.set())
        ctx = RuntimeContext.new(session_id="s-propagate")
        ctx.add_message("user", "来自 ctx 的消息")
        task_id = adapter.submit(ctx)
        assert done.wait(timeout=2.0)
        adapter.runtime.scheduler.wait_all(timeout=2.0)
        assert task_id == ctx.task_id
        assert len(ctx.messages) == 2
        assert ctx.messages[0].role == "user"
        assert ctx.messages[0].content == "来自 ctx 的消息"
        assert ctx.messages[1].role == "ai"
        assert ctx.messages[1].content == "收到：来自 ctx 的消息"
    finally:
        adapter.stop()
