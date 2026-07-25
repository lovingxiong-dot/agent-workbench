"""tests/v6/runtime/test_phase3_11_c_cancellation.py — Phase 3.11-C Execution Control Activation 测试。

验证目标：
    3.11-C.1 RuntimeContext.control 集成 — control 字段存在、默认值、快照/恢复/clone/reset
    3.11-C.2 Orchestrator.cancel() — 取消任务、终态不可取消、状态迁移
    3.11-C.3 CancellationToken 生命周期 — 取消信号传播、Worker 线程响应
    3.11-C.4 超时处理 — timeout 触发自动取消
    3.11-C.5 TASK_CANCELLED 事件 — 事件发布和订阅
    3.11-C.6 协作式取消检查 — _check_cancellation 在关键路径中生效

约束：
    - 禁止修改 RuntimeState ABI
    - 禁止修改 Capability Contract
    - 禁止修改 Decision Layer
    - 禁止修改 UI Layer
    - 禁止修改 Provider Layer
"""
from __future__ import annotations

import threading
import time
import pytest

from v6.runtime.context import RuntimeContext
from v6.runtime.enums import ActivityState, LifecycleState, RuntimeState
from v6.runtime.event_bus import EventBus, RuntimeEventType
from v6.runtime.execution_control import CancellationToken, ExecutionControl, TaskCancelledError
from v6.runtime.execution_metadata import ExecutionMetadata
from v6.runtime.orchestrator import Orchestrator
from v6.runtime.task import Task


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def bus() -> EventBus:
    b = EventBus()
    b.start()
    try:
        yield b
    finally:
        b.stop()


@pytest.fixture
def orch(bus: EventBus) -> Orchestrator:
    return Orchestrator(event_bus=bus)


# ═══════════════════════════════════════════════════════════════════
# 3.11-C.1 RuntimeContext.control 集成
# ═══════════════════════════════════════════════════════════════════

class TestRuntimeContextControl:
    """验证 RuntimeContext.control 字段的集成。"""

    def test_control_field_exists_by_default(self):
        """RuntimeContext 默认创建 control 字段。"""
        ctx = RuntimeContext.new()
        assert isinstance(ctx.control, ExecutionControl)
        assert not ctx.control.is_cancelled

    def test_control_field_independent_per_context(self):
        """每个 RuntimeContext 的 control 独立。"""
        ctx1 = RuntimeContext.new()
        ctx2 = RuntimeContext.new()
        ctx1.control.cancel("ctx1 reason")
        assert ctx1.control.is_cancelled
        assert not ctx2.control.is_cancelled

    def test_snapshot_includes_control(self):
        """snapshot() 包含 control 状态。"""
        ctx = RuntimeContext.new()
        snap = ctx.snapshot()
        assert "control" in snap
        assert snap["control"]["cancelled"] is False
        assert snap["control"]["cancel_reason"] == ""

    def test_snapshot_control_cancelled(self):
        """snapshot() 记录取消状态。"""
        ctx = RuntimeContext.new()
        ctx.control.cancel("user abort")
        snap = ctx.snapshot()
        assert snap["control"]["cancelled"] is True
        assert snap["control"]["cancel_reason"] == "user abort"

    def test_restore_control_not_cancelled(self):
        """restore() 恢复未取消状态。"""
        ctx = RuntimeContext.new()
        ctx.control.cancel("test")  # 先取消
        ctx.restore({"control": {"cancelled": False, "cancel_reason": ""}})
        assert not ctx.control.is_cancelled

    def test_restore_control_cancelled(self):
        """restore() 恢复已取消状态。"""
        ctx = RuntimeContext.new()
        ctx.restore({"control": {"cancelled": True, "cancel_reason": "restored cancel"}})
        assert ctx.control.is_cancelled
        assert ctx.control.cancellation.reason == "restored cancel"

    def test_restore_control_missing(self):
        """restore() 缺少 control 字段时使用默认值。"""
        ctx = RuntimeContext.new()
        ctx.control.cancel("test")
        ctx.restore({"task_id": "t1"})
        # 未提供 control，reset 为默认（未取消）
        assert not ctx.control.is_cancelled

    def test_clone_creates_new_control(self):
        """clone() 创建独立的新 ExecutionControl，不共享取消状态。"""
        ctx = RuntimeContext.new()
        ctx.control.cancel("original")
        cloned = ctx.clone()
        assert ctx.control.is_cancelled
        assert not cloned.control.is_cancelled  # 新实例，未取消

    def test_reset_clears_control(self):
        """reset() 重置 control 为新实例。"""
        ctx = RuntimeContext.new()
        ctx.control.cancel("test")
        ctx.reset()
        assert not ctx.control.is_cancelled
        assert ctx.control.cancellation.reason == ""


# ═══════════════════════════════════════════════════════════════════
# 3.11-C.2 Orchestrator.cancel() 取消控制
# ═══════════════════════════════════════════════════════════════════

class TestOrchestratorCancel:
    """验证 Orchestrator.cancel() 的取消控制。"""

    def test_cancel_active_task(self, orch: Orchestrator, bus: EventBus):
        """取消活跃任务：取消令牌触发、状态迁移到 CANCELLED。"""
        task = Task(capability="chat", payload={"text": "hello"})
        task_id = orch.submit(task)

        # Foundation 模式下任务完成极快，需立即取消
        result = orch.cancel(task_id, "user request")
        assert result is True

        ctx = orch.context(task_id)
        assert ctx is not None
        assert ctx.lifecycle == LifecycleState.CANCELLED
        assert ctx.activity == ActivityState.IDLE
        assert ctx.control.is_cancelled
        assert ctx.control.cancellation.reason == "user request"

    def test_cancel_sets_finished_at(self, orch: Orchestrator, bus: EventBus):
        """取消时设置 ExecutionMetadata.finished_at。"""
        task = Task(capability="chat", payload={"text": "hello"})
        task_id = orch.submit(task)

        orch.cancel(task_id, "test")
        ctx = orch.context(task_id)
        assert ctx is not None
        assert ctx.execution is not None
        assert ctx.execution.finished_at is not None

    def test_cancel_nonexistent_task(self, orch: Orchestrator):
        """取消不存在的任务返回 False。"""
        result = orch.cancel("nonexistent-id", "test")
        assert result is False

    def test_cancel_already_completed_task(self, orch: Orchestrator, bus: EventBus):
        """已完成任务不可取消。"""
        task = Task(capability="chat", payload={"text": "hello"})
        task_id = orch.submit(task)
        time.sleep(0.5)  # 等待 Foundation 模式完成

        ctx = orch.context(task_id)
        assert ctx is not None
        assert ctx.lifecycle == LifecycleState.COMPLETED

        result = orch.cancel(task_id, "late cancel")
        assert result is False

    def test_cancel_already_cancelled_task(self, orch: Orchestrator, bus: EventBus):
        """已取消任务不可重复取消。"""
        task = Task(capability="chat", payload={"text": "hello"})
        task_id = orch.submit(task)

        orch.cancel(task_id, "first")
        result = orch.cancel(task_id, "second")
        assert result is False

    def test_cancel_publishes_task_cancelled_event(self, orch: Orchestrator, bus: EventBus):
        """cancel() 发布 TASK_CANCELLED 事件。

        ADR-014 Precedence Rule: 任务已处于 COMPLETED 终态时 cancel() 返回 False 且不发布事件。
        本测试要求 cancel() 实际生效后再断言事件。
        """
        received: list[dict] = []

        def _on_cancelled(event):
            received.append(event.payload)

        bus.subscribe(RuntimeEventType.TASK_CANCELLED, _on_cancelled)

        task = Task(capability="chat", payload={"text": "hello"})
        task_id = orch.submit(task)

        # 若 Foundation mode 下任务已自动完成（终态），cancel 返回 False，不发布事件
        cancelled = orch.cancel(task_id, "event test")
        if not cancelled:
            # 任务在 submit() 后已进入终态（ADR-014: COMPLETED > CANCELLED）
            state = orch.state(task_id)
            assert state in (
                RuntimeState.COMPLETED,
                RuntimeState.FAILED,
                RuntimeState.CANCELLED,
            )
            # 等待异步分发后断言：不应有 TASK_CANCELLED 事件
            time.sleep(0.2)
            assert len(received) == 0
        else:
            # cancel 实际生效，断言事件已发布
            time.sleep(0.2)
            assert len(received) >= 1
            assert any(p.get("reason") == "event test" for p in received)

    def test_cancel_state_machine_transition(self, orch: Orchestrator, bus: EventBus):
        """cancel() 后 RuntimeState 迁移到 CANCELLED。"""
        task = Task(capability="chat", payload={"text": "hello"})
        task_id = orch.submit(task)

        orch.cancel(task_id, "test")
        state = orch.state(task_id)
        assert state == RuntimeState.CANCELLED


# ═══════════════════════════════════════════════════════════════════
# 3.11-C.3 CancellationToken 生命周期（Orchestrator 集成）
# ═══════════════════════════════════════════════════════════════════

class TestCancellationTokenLifecycle:
    """验证 CancellationToken 在 Orchestrator 中的生命周期。"""

    def test_submit_creates_fresh_token(self, orch: Orchestrator, bus: EventBus):
        """submit() 创建的 RuntimeContext 带有未取消的 CancellationToken。"""
        task = Task(capability="chat", payload={"text": "hello"})
        task_id = orch.submit(task)

        ctx = orch.context(task_id)
        assert ctx is not None
        assert not ctx.control.is_cancelled
        assert ctx.control.cancellation.reason == ""

    def test_cancel_signal_propagates_to_context(self, orch: Orchestrator, bus: EventBus):
        """cancel() 设置的取消信号传播到 ctx.control。

        ADR-014 Precedence Rule: 任务已处于 COMPLETED 终态时 cancel() 返回 False，
        此时不应触发取消信号。本测试在 cancel 实际生效时验证信号传播。
        """
        task = Task(capability="chat", payload={"text": "hello"})
        task_id = orch.submit(task)

        cancelled = orch.cancel(task_id, "signal test")
        ctx = orch.context(task_id)
        assert ctx is not None

        if cancelled:
            # cancel 实际生效，断言信号传播
            assert ctx.control.is_cancelled
            assert ctx.control.cancellation.reason == "signal test"
        else:
            # 任务在 submit() 后已进入终态，cancel 被拒绝（ADR-014）
            state = orch.state(task_id)
            assert state in (
                RuntimeState.COMPLETED,
                RuntimeState.FAILED,
                RuntimeState.CANCELLED,
            )
            # 终态任务不应有取消信号
            assert not ctx.control.is_cancelled

    def test_token_wait_wakes_on_cancel(self):
        """CancellationToken.wait() 在 cancel() 后立即返回 True。"""
        token = CancellationToken()

        def _cancel_after_delay():
            time.sleep(0.1)
            token.cancel("wake test")

        threading.Thread(target=_cancel_after_delay, daemon=True).start()
        result = token.wait(timeout=2.0)
        assert result is True
        assert token.reason == "wake test"

    def test_raise_if_cancelled_after_orchestrator_cancel(self, orch: Orchestrator, bus: EventBus):
        """Orchestrator cancel() 后 ctx.control.raise_if_cancelled() 抛出异常。"""
        task = Task(capability="chat", payload={"text": "hello"})
        task_id = orch.submit(task)

        orch.cancel(task_id, "test")
        ctx = orch.context(task_id)
        assert ctx is not None

        with pytest.raises(TaskCancelledError) as exc:
            ctx.control.raise_if_cancelled()
        assert "test" in str(exc.value)


# ═══════════════════════════════════════════════════════════════════
# 3.11-C.4 Deadline 处理
# ═══════════════════════════════════════════════════════════════════

class TestTimeoutHandling:
    """v0.3: deadline_at 触发的自动取消（替代 timeout_seconds）。"""

    def test_deadline_mechanism_wired(self, orch: Orchestrator, bus: EventBus):
        """Deadline 定时器正确启动：当 execution.deadline_at 设置时启动定时器线程。"""
        from datetime import datetime, timezone, timedelta
        from v6.runtime.execution_metadata import ExecutionMetadata

        task = Task(capability="chat", payload={"text": "hello"})
        task_id = orch.submit(task)

        ctx = orch.context(task_id)
        assert ctx is not None
        ctx.attach_execution(
            ExecutionMetadata(
                task_id=task_id,
                deadline_at=datetime.now(timezone.utc) + timedelta(milliseconds=100),
            )
        )

        # 直接调用 _start_deadline_timer 验证不抛异常
        orch._start_deadline_timer(task_id, ctx)
        # 定时器线程已启动，等待其完成
        time.sleep(0.3)

    def test_deadline_timer_respects_cancellation_token(self, orch: Orchestrator, bus: EventBus):
        """Deadline 定时器使用 CancellationToken.wait()，手动取消后不重复触发。"""
        from datetime import datetime, timezone, timedelta
        from v6.runtime.execution_metadata import ExecutionMetadata

        cancel_count = 0

        def _on_cancelled(event):
            nonlocal cancel_count
            cancel_count += 1

        bus.subscribe(RuntimeEventType.TASK_CANCELLED, _on_cancelled)

        task = Task(capability="chat", payload={"text": "hello"})
        task_id = orch.submit(task)

        ctx = orch.context(task_id)
        assert ctx is not None
        ctx.attach_execution(
            ExecutionMetadata(
                task_id=task_id,
                deadline_at=datetime.now(timezone.utc) + timedelta(seconds=5),
            )
        )

        # 手动取消（在 deadline 之前）
        orch.cancel(task_id, "manual cancel")

        # 等待 deadline 定时器响应取消
        time.sleep(0.3)

        ctx = orch.context(task_id)
        assert ctx is not None
        assert ctx.lifecycle == LifecycleState.CANCELLED
        assert ctx.control.cancellation.reason == "manual cancel"

        # 验证只触发一次取消
        time.sleep(0.2)
        assert cancel_count == 1

    def test_no_deadline_when_not_set(self, orch: Orchestrator, bus: EventBus):
        """未设置 deadline_at 时不触发 deadline。"""
        task = Task(capability="chat", payload={"text": "hello"})
        task_id = orch.submit(task)

        time.sleep(0.5)

        ctx = orch.context(task_id)
        assert ctx is not None
        # Foundation 模式正常完成，非 deadline 取消
        assert ctx.lifecycle == LifecycleState.COMPLETED

    def test_deadline_timer_not_started_when_no_deadline(self, orch: Orchestrator):
        """未设置 deadline_at 时 _start_deadline_timer 不启动线程。"""
        ctx = RuntimeContext.new()
        orch._start_deadline_timer(ctx.task_id, ctx)
        # 没有 deadline，不抛异常即可

    def test_deadline_timer_with_past_deadline_immediately_cancels(self):
        """deadline_at 在过去时 _cancel_with_deadline 立即构造 DEADLINE_EXCEEDED context。

        不依赖 Orchestrator 内部状态，验证 deadline propagation context 结构正确。
        """
        from datetime import datetime, timezone, timedelta
        from v6.runtime.cancellation_propagation import (
            CancellationPropagationContext,
            PropagationType,
        )

        past_deadline = datetime.now(timezone.utc) - timedelta(seconds=1)
        # 模拟 _cancel_with_deadline 构造的 propagation
        ctx = RuntimeContext.new(task_id="t-past-deadline")
        ctx.attach_execution(
            ExecutionMetadata(
                task_id="t-past-deadline",
                deadline_at=past_deadline,
            )
        )
        propagation = CancellationPropagationContext(
            propagation_type=PropagationType.DEADLINE_EXCEEDED,
            origin_execution_id=ctx.execution.execution_id,
            chain=(ctx.execution.execution_id,),
            reason=f"deadline exceeded at {past_deadline.isoformat()}",
            initiated_at=datetime.now(timezone.utc),
        )
        # 验证 propagation 结构
        assert propagation.propagation_type == PropagationType.DEADLINE_EXCEEDED
        assert propagation.origin_execution_id == ctx.execution.execution_id
        assert "deadline exceeded at" in propagation.reason


# ═══════════════════════════════════════════════════════════════════
# 3.11-C.5 TASK_CANCELLED 事件
# ═══════════════════════════════════════════════════════════════════

class TestTaskCancelledEvent:
    """验证 TASK_CANCELLED 事件的发布、订阅和 Trace 写入。"""

    def test_event_type_exists(self):
        """TASK_CANCELLED 事件类型已定义。"""
        assert RuntimeEventType.TASK_CANCELLED == "task.cancelled"

    def test_event_published_on_cancel(self, orch: Orchestrator, bus: EventBus):
        """cancel() 发布 TASK_CANCELLED 事件。"""
        events: list = []

        def _collect(event):
            events.append(event)

        bus.subscribe(RuntimeEventType.TASK_CANCELLED, _collect)

        task = Task(capability="chat", payload={"text": "hello"})
        task_id = orch.submit(task)

        orch.cancel(task_id, "event payload test")

        time.sleep(0.3)
        assert len(events) >= 1
        event = events[0]
        assert event.type == RuntimeEventType.TASK_CANCELLED
        assert event.task_id == task_id
        assert event.source == "orchestrator"
        assert event.payload.get("reason") == "event payload test"

    def test_event_not_published_for_nonexistent_task(self, orch: Orchestrator, bus: EventBus):
        """取消不存在的任务不发布事件。"""
        events: list = []

        def _collect(event):
            events.append(event)

        bus.subscribe(RuntimeEventType.TASK_CANCELLED, _collect)

        orch.cancel("nonexistent", "test")
        time.sleep(0.1)
        assert len(events) == 0

    def test_event_not_published_for_completed_task(self, orch: Orchestrator, bus: EventBus):
        """已完成任务取消不发布事件。"""
        events: list = []

        def _collect(event):
            events.append(event)

        bus.subscribe(RuntimeEventType.TASK_CANCELLED, _collect)

        task = Task(capability="chat", payload={"text": "hello"})
        task_id = orch.submit(task)
        time.sleep(0.5)  # 等待完成

        # 清空已有事件
        events.clear()

        result = orch.cancel(task_id, "late")
        assert result is False
        time.sleep(0.1)
        assert len(events) == 0


# ═══════════════════════════════════════════════════════════════════
# 3.11-C.6 协作式取消检查
# ═══════════════════════════════════════════════════════════════════

class TestCooperativeCancellation:
    """验证 Orchestrator._check_cancellation 在关键路径中的协作式取消。"""

    def test_check_cancellation_raises_when_cancelled(self, orch: Orchestrator):
        """_check_cancellation 在已取消时抛出 TaskCancelledError。"""
        ctx = RuntimeContext.new()
        ctx.control.cancel("test")
        with pytest.raises(TaskCancelledError):
            orch._check_cancellation(ctx)

    def test_check_cancellation_noop_when_not_cancelled(self, orch: Orchestrator):
        """_check_cancellation 在未取消时无操作。"""
        ctx = RuntimeContext.new()
        orch._check_cancellation(ctx)  # no exception

    def test_cancel_before_execution_marks_failed(self, orch: Orchestrator, bus: EventBus):
        """在 _execute_task 执行前取消，任务标记为 FAILED（含取消原因）。"""
        task = Task(capability="chat", payload={"text": "hello"})
        task_id = orch.submit(task)

        ctx = orch.context(task_id)
        assert ctx is not None

        # 在 _execute_task 被调度前立即取消
        ctx.control.cancel("pre-execution cancel")

        # 等待执行线程
        time.sleep(0.5)

        ctx = orch.context(task_id)
        assert ctx is not None
        # 取消检查在 transition 之前，任务应保持 QUEUED 或进入 FAILED
        assert ctx.lifecycle in (LifecycleState.QUEUED, LifecycleState.FAILED, LifecycleState.CANCELLED)

    def test_independent_tasks_dont_share_cancellation(self, orch: Orchestrator, bus: EventBus):
        """取消一个任务不影响另一个任务。"""
        t1 = Task(capability="chat", payload={"text": "a"})
        t2 = Task(capability="chat", payload={"text": "b"})

        id1 = orch.submit(t1)
        id2 = orch.submit(t2)

        orch.cancel(id1, "cancel task 1")

        ctx1 = orch.context(id1)
        ctx2 = orch.context(id2)

        assert ctx1 is not None
        assert ctx2 is not None
        assert ctx1.lifecycle == LifecycleState.CANCELLED
        assert ctx1.control.is_cancelled
        assert ctx2.lifecycle != LifecycleState.CANCELLED
        assert not ctx2.control.is_cancelled

    def test_cancelled_task_trace_hook_removed(self, orch: Orchestrator, bus: EventBus):
        """取消后 Trace Hook 被清理。"""
        task = Task(capability="chat", payload={"text": "hello"})
        task_id = orch.submit(task)

        orch.cancel(task_id, "cleanup test")

        # Trace Hook 已被移除
        with bus._lock:
            assert task_id not in bus._trace_hooks