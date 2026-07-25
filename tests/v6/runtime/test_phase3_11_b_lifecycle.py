"""tests/v6/runtime/test_phase3_11_b_lifecycle.py — Phase 3.11-B Lifecycle Activation 测试。

验证目标：
    3.11-B.1 ExecutionMetadata 创建与挂载 — ctx.execution 正确初始化
    3.11-B.2 LifecycleState 生命周期 — CREATED→QUEUED→PLANNING→EXECUTING→COMPLETED/FAILED
    3.11-B.3 ActivityState 活动状态 — IDLE/RUNNING 切换
    3.11-B.4 向后兼容 — RuntimeState 同步
    3.11-B.5 Context 快照/恢复 — 新字段持久化
    3.11-B.6 ExecutionControl — CancellationToken 与 ExecutionControl 容器

约束：
    - 禁止修改 RuntimeEvent schema
    - 禁止修改 Task 模型
    - 禁止修改 Frozen Contracts
"""
from __future__ import annotations

import threading
import time
import pytest

from v6.runtime.context import RuntimeContext
from v6.runtime.enums import ActivityState, LifecycleState, RuntimeState, lifecycle_to_runtime
from v6.runtime.event_bus import EventBus, RuntimeEventType
from v6.runtime.execution_control import CancellationToken, ExecutionControl, TaskCancelledError
from v6.runtime.execution_metadata import ExecutionMetadata
from v6.runtime.orchestrator import Orchestrator
from v6.runtime.task import Task


# ═══════════════════════════════════════════════════════════════════
# 3.11-B.1 ExecutionMetadata 创建与挂载
# ═══════════════════════════════════════════════════════════════════

class TestExecutionMetadata:
    """验证 ExecutionMetadata 的创建、挂载与计算属性。"""

    def test_execution_metadata_default_creation(self):
        """ExecutionMetadata 默认创建时自动生成 execution_id。"""
        meta = ExecutionMetadata(task_id="task-001")
        assert meta.execution_id != ""
        assert len(meta.execution_id) == 32  # uuid4().hex
        assert meta.task_id == "task-001"
        assert meta.parent_execution_id is None
        assert meta.retry_count == 0
        assert meta.priority == 0
        assert meta.tags == []

    def test_execution_metadata_with_parent(self):
        """ExecutionMetadata 支持 parent_execution_id。"""
        meta = ExecutionMetadata(
            task_id="task-002",
            parent_execution_id="exec-parent-001",
        )
        assert meta.parent_execution_id == "exec-parent-001"
        assert not meta.is_root_execution

    def test_execution_metadata_is_root_execution(self):
        """is_root_execution 判断是否正确。"""
        root = ExecutionMetadata(task_id="t1")
        assert root.is_root_execution

        child = ExecutionMetadata(task_id="t2", parent_execution_id="e1")
        assert not child.is_root_execution

    def test_execution_metadata_is_retry(self):
        """is_retry 判断是否正确。"""
        fresh = ExecutionMetadata(task_id="t1")
        assert not fresh.is_retry

        retry = ExecutionMetadata(task_id="t1", retry_count=1)
        assert retry.is_retry

    def test_execution_metadata_duration_seconds(self):
        """duration_seconds 计算是否正确。"""
        meta = ExecutionMetadata(task_id="t1")
        # 未开始，无 duration
        assert meta.duration_seconds is None

        # 开始但未结束，返回当前 elapsed
        from datetime import datetime, timezone, timedelta
        meta.started_at = datetime.now(timezone.utc) - timedelta(seconds=5)
        duration = meta.duration_seconds
        assert duration is not None
        assert 4.0 <= duration <= 6.0  # 约 5 秒

        # 已结束
        meta.finished_at = meta.started_at + timedelta(seconds=10)
        assert 9.9 <= meta.duration_seconds <= 10.1

    def test_execution_metadata_timeout(self):
        """is_deadline_reached 判断是否正确。"""
        from datetime import datetime, timezone, timedelta

        # v0.3: timeout_seconds 已替换为 deadline_at
        now = datetime.now(timezone.utc)
        meta = ExecutionMetadata(task_id="t1", deadline_at=now + timedelta(seconds=5))
        # 未到 deadline
        assert not meta.is_deadline_reached

        # 已过期
        meta.deadline_at = now - timedelta(seconds=10)
        assert meta.is_deadline_reached

        # 刚刚到期
        meta.deadline_at = now + timedelta(milliseconds=100)
        assert not meta.is_deadline_reached

        # 未设置 deadline
        meta2 = ExecutionMetadata(task_id="t2")
        assert not meta2.is_deadline_reached

    def test_execution_metadata_unique_ids(self):
        """每次创建 ExecutionMetadata 生成唯一 execution_id。"""
        ids = {ExecutionMetadata().execution_id for _ in range(100)}
        assert len(ids) == 100


# ═══════════════════════════════════════════════════════════════════
# 3.11-B.2 LifecycleState 生命周期
# ═══════════════════════════════════════════════════════════════════

class TestLifecycleState:
    """验证 LifecycleState 枚举与向后兼容映射。"""

    def test_lifecycle_state_values(self):
        """LifecycleState 枚举值完整。"""
        values = {s.value for s in LifecycleState}
        expected = {"created", "queued", "planning", "executing", "completed", "failed", "cancelled"}
        assert values == expected

    def test_lifecycle_to_runtime_mapping(self):
        """LifecycleState → RuntimeState 映射正确。"""
        assert lifecycle_to_runtime(LifecycleState.CREATED) == RuntimeState.CREATED
        assert lifecycle_to_runtime(LifecycleState.QUEUED) == RuntimeState.QUEUED
        assert lifecycle_to_runtime(LifecycleState.PLANNING) == RuntimeState.PLANNING
        assert lifecycle_to_runtime(LifecycleState.EXECUTING) == RuntimeState.EXECUTING
        assert lifecycle_to_runtime(LifecycleState.COMPLETED) == RuntimeState.COMPLETED
        assert lifecycle_to_runtime(LifecycleState.FAILED) == RuntimeState.FAILED
        assert lifecycle_to_runtime(LifecycleState.CANCELLED) == RuntimeState.CANCELLED

    def test_activity_state_values(self):
        """ActivityState 枚举值完整。"""
        values = {s.value for s in ActivityState}
        expected = {"idle", "running", "streaming", "waiting", "paused"}
        assert values == expected

    def test_context_set_lifecycle(self):
        """RuntimeContext.set_lifecycle 正确更新双状态。"""
        ctx = RuntimeContext.new()
        assert ctx.lifecycle == LifecycleState.CREATED
        assert ctx.activity == ActivityState.IDLE

        ctx.set_lifecycle(LifecycleState.QUEUED)
        assert ctx.lifecycle == LifecycleState.QUEUED
        assert ctx.activity == ActivityState.IDLE  # activity 不变
        assert ctx.status == RuntimeState.QUEUED  # 向后兼容同步

        ctx.set_lifecycle(LifecycleState.EXECUTING, ActivityState.RUNNING)
        assert ctx.lifecycle == LifecycleState.EXECUTING
        assert ctx.activity == ActivityState.RUNNING
        assert ctx.status == RuntimeState.EXECUTING

    def test_context_set_lifecycle_to_terminal(self):
        """终态时 activity 自动变为 IDLE。"""
        ctx = RuntimeContext.new()
        ctx.set_lifecycle(LifecycleState.EXECUTING, ActivityState.RUNNING)

        ctx.set_lifecycle(LifecycleState.COMPLETED, ActivityState.IDLE)
        assert ctx.lifecycle == LifecycleState.COMPLETED
        assert ctx.activity == ActivityState.IDLE
        assert ctx.status == RuntimeState.COMPLETED

    def test_context_set_status_backward_compat(self):
        """旧 set_status 方法仍可用，且同步 lifecycle。"""
        ctx = RuntimeContext.new()
        ctx.set_status(RuntimeState.EXECUTING)
        assert ctx.status == RuntimeState.EXECUTING
        assert ctx.lifecycle == LifecycleState.EXECUTING

    def test_context_set_status_with_string(self):
        """set_status 接受字符串参数。"""
        ctx = RuntimeContext.new()
        ctx.set_status("completed")
        assert ctx.status == RuntimeState.COMPLETED
        assert ctx.lifecycle == LifecycleState.COMPLETED


# ═══════════════════════════════════════════════════════════════════
# 3.11-B.3 Orchestrator 双状态模型集成
# ═══════════════════════════════════════════════════════════════════

class TestOrchestratorLifecycle:
    """验证 Orchestrator 中 LifecycleState + ActivityState 的完整生命周期。"""

    @pytest.fixture
    def bus(self) -> EventBus:
        b = EventBus()
        b.start()
        try:
            yield b
        finally:
            b.stop()

    @pytest.fixture
    def orch(self, bus: EventBus) -> Orchestrator:
        return Orchestrator(event_bus=bus)

    def test_submit_creates_execution_metadata(self, orch: Orchestrator):
        """submit() 创建 ExecutionMetadata 并挂载到 ctx.execution。"""
        task = Task(capability="chat", payload={"text": "hello"})
        task_id = orch.submit(task)

        ctx = orch.context(task_id)
        assert ctx is not None
        assert ctx.execution is not None
        assert ctx.execution.task_id == task_id
        assert ctx.execution.execution_id != ""

    def test_submit_sets_queued_lifecycle(self, orch: Orchestrator):
        """submit() 后 lifecycle 为 QUEUED（EventBus 异步分发可能已推进到 PLANNING）。"""
        task = Task(capability="chat", payload={"text": "hello"})
        task_id = orch.submit(task)

        ctx = orch.context(task_id)
        assert ctx is not None
        # submit() 内部设置 QUEUED，但 EventBus 异步分发可能已将状态推进到 PLANNING
        assert ctx.lifecycle in (LifecycleState.QUEUED, LifecycleState.PLANNING)
        assert ctx.activity == ActivityState.IDLE

    def test_full_lifecycle_created_to_completed(self, orch: Orchestrator, bus: EventBus):
        """完整生命周期：CREATED→QUEUED→PLANNING→EXECUTING→COMPLETED。

        submit() 内部已发布 TASK_STARTED，EventBus 异步分发后自动触发完整流程。
        无需手动发布事件。
        """
        task = Task(capability="chat", payload={"text": "hello"})
        task_id = orch.submit(task)

        ctx = orch.context(task_id)
        assert ctx is not None
        # submit() 内部设置 QUEUED，但 EventBus 异步分发可能已推进到后续状态
        assert ctx.lifecycle in (LifecycleState.QUEUED, LifecycleState.PLANNING, LifecycleState.EXECUTING, LifecycleState.COMPLETED)

        # 等待异步 EventBus 分发 + 执行线程完成
        time.sleep(0.5)

        ctx = orch.context(task_id)
        assert ctx is not None
        # Foundation 模式无 EngineManager，直接完成
        assert ctx.lifecycle == LifecycleState.COMPLETED
        assert ctx.activity == ActivityState.IDLE
        assert ctx.status == RuntimeState.COMPLETED

    def test_full_lifecycle_sets_started_at(self, orch: Orchestrator, bus: EventBus):
        """ExecutionMetadata.started_at 在执行开始时设置。"""
        task = Task(capability="chat", payload={"text": "hello"})
        task_id = orch.submit(task)

        time.sleep(0.5)

        ctx = orch.context(task_id)
        assert ctx is not None
        assert ctx.execution is not None
        assert ctx.execution.started_at is not None

    def test_full_lifecycle_sets_finished_at(self, orch: Orchestrator, bus: EventBus):
        """ExecutionMetadata.finished_at 在完成时设置。"""
        task = Task(capability="chat", payload={"text": "hello"})
        task_id = orch.submit(task)

        time.sleep(0.5)

        ctx = orch.context(task_id)
        assert ctx is not None
        assert ctx.execution is not None
        assert ctx.execution.finished_at is not None
        assert ctx.execution.duration_seconds is not None

    def test_submit_then_state_tracking(self, orch: Orchestrator):
        """submit() 后 _task_states 跟踪正常（EventBus 已异步处理到 PLANNING）。"""
        task = Task(capability="chat", payload={"text": "hello"})
        task_id = orch.submit(task)

        # EventBus 异步分发，可能已推进到 PLANNING 或更远
        state = orch.state(task_id)
        assert state is not None
        assert state in {RuntimeState.CREATED, RuntimeState.PLANNING, RuntimeState.EXECUTING, RuntimeState.COMPLETED}

    def test_multiple_tasks_independent_lifecycle(self, orch: Orchestrator):
        """多个任务的 lifecycle 独立。"""
        t1 = Task(capability="chat", payload={"text": "a"})
        t2 = Task(capability="chat", payload={"text": "b"})

        id1 = orch.submit(t1)
        id2 = orch.submit(t2)

        ctx1 = orch.context(id1)
        ctx2 = orch.context(id2)

        assert ctx1 is not None
        assert ctx2 is not None
        # submit() 内部设置 QUEUED，但 EventBus 异步分发可能已推进到后续状态
        assert ctx1.lifecycle in (LifecycleState.QUEUED, LifecycleState.PLANNING, LifecycleState.EXECUTING, LifecycleState.COMPLETED)
        assert ctx2.lifecycle in (LifecycleState.QUEUED, LifecycleState.PLANNING, LifecycleState.EXECUTING, LifecycleState.COMPLETED)
        assert ctx1.execution is not None
        assert ctx2.execution is not None
        assert ctx1.execution.execution_id != ctx2.execution.execution_id


# ═══════════════════════════════════════════════════════════════════
# 3.11-B.4 Context 快照/恢复
# ═══════════════════════════════════════════════════════════════════

class TestContextSnapshotWithLifecycle:
    """验证 RuntimeContext 快照/恢复包含新字段。"""

    def test_snapshot_includes_lifecycle_fields(self):
        """snapshot() 包含 lifecycle、activity、execution。"""
        ctx = RuntimeContext.new()
        ctx.set_lifecycle(LifecycleState.EXECUTING, ActivityState.RUNNING)
        ctx.execution = ExecutionMetadata(task_id=ctx.task_id)

        snap = ctx.snapshot()
        assert snap["lifecycle"] == "executing"
        assert snap["activity"] == "running"
        assert snap["execution"] is not None
        assert "execution_id" in snap["execution"]

    def test_snapshot_lifecycle_none_execution(self):
        """snapshot() 中 execution 为 None 时正确处理。"""
        ctx = RuntimeContext.new()
        snap = ctx.snapshot()
        assert snap["lifecycle"] == "created"
        assert snap["activity"] == "idle"
        assert snap["execution"] is None

    def test_restore_lifecycle_fields(self):
        """restore() 恢复 lifecycle、activity、execution。"""
        ctx = RuntimeContext.new()
        ctx.set_lifecycle(LifecycleState.EXECUTING, ActivityState.RUNNING)
        ctx.execution = ExecutionMetadata(task_id="task-001", execution_id="exec-abc")

        snap = ctx.snapshot()

        restored = RuntimeContext.new(task_id="task-001")
        restored.restore(snap)

        assert restored.lifecycle == LifecycleState.EXECUTING
        assert restored.activity == ActivityState.RUNNING
        assert restored.execution is not None
        assert restored.execution.execution_id == "exec-abc"
        assert restored.execution.task_id == "task-001"

    def test_restore_handles_string_lifecycle(self):
        """restore() 接受字符串形式的 lifecycle。"""
        ctx = RuntimeContext.new()
        ctx.restore({"lifecycle": "executing", "activity": "running"})
        assert ctx.lifecycle == LifecycleState.EXECUTING
        assert ctx.activity == ActivityState.RUNNING

    def test_restore_handles_missing_lifecycle(self):
        """restore() 缺少 lifecycle 字段时使用默认值。"""
        ctx = RuntimeContext.new()
        ctx.set_lifecycle(LifecycleState.EXECUTING)
        ctx.restore({"task_id": "t1"})
        assert ctx.lifecycle == LifecycleState.CREATED  # 默认
        assert ctx.activity == ActivityState.IDLE

    def test_clone_preserves_lifecycle(self):
        """clone() 保留 lifecycle 字段。"""
        ctx = RuntimeContext.new()
        ctx.set_lifecycle(LifecycleState.EXECUTING, ActivityState.RUNNING)
        ctx.execution = ExecutionMetadata(task_id=ctx.task_id)

        cloned = ctx.clone()
        assert cloned.lifecycle == LifecycleState.EXECUTING
        assert cloned.activity == ActivityState.RUNNING
        assert cloned.execution is not None
        assert cloned.execution.execution_id == ctx.execution.execution_id

    def test_reset_clears_lifecycle(self):
        """reset() 重置 lifecycle 为 CREATED/IDLE。"""
        ctx = RuntimeContext.new()
        ctx.set_lifecycle(LifecycleState.EXECUTING, ActivityState.RUNNING)
        ctx.execution = ExecutionMetadata(task_id=ctx.task_id)

        ctx.reset()
        assert ctx.lifecycle == LifecycleState.CREATED
        assert ctx.activity == ActivityState.IDLE
        assert ctx.execution is None


# ═══════════════════════════════════════════════════════════════════
# 3.11-B.5 ExecutionControl + CancellationToken
# ═══════════════════════════════════════════════════════════════════

class TestCancellationToken:
    """验证 CancellationToken 协作式取消。"""

    def test_initial_state_not_cancelled(self):
        """初始状态未取消。"""
        token = CancellationToken()
        assert not token.is_cancelled()
        assert token.reason == ""

    def test_cancel_sets_signal(self):
        """cancel() 设置取消信号。"""
        token = CancellationToken()
        token.cancel("user requested")
        assert token.is_cancelled()
        assert token.reason == "user requested"

    def test_cancel_preserves_first_reason(self):
        """多次 cancel 保留首次原因。"""
        token = CancellationToken()
        token.cancel("first")
        token.cancel("second")
        assert token.reason == "first"

    def test_raise_if_cancelled(self):
        """raise_if_cancelled 抛出 TaskCancelledError。"""
        token = CancellationToken()
        token.cancel("test")
        with pytest.raises(TaskCancelledError) as exc:
            token.raise_if_cancelled()
        assert "test" in str(exc.value)

    def test_raise_if_cancelled_noop_when_not_cancelled(self):
        """未取消时 raise_if_cancelled 不抛异常。"""
        token = CancellationToken()
        token.raise_if_cancelled()  # no exception

    def test_wait_timeout(self):
        """wait() 超时返回 False。"""
        token = CancellationToken()
        assert not token.wait(timeout=0.1)

    def test_wait_cancelled(self):
        """wait() 被取消后返回 True。"""
        token = CancellationToken()

        def _cancel_after_delay():
            time.sleep(0.1)
            token.cancel("test")

        threading.Thread(target=_cancel_after_delay, daemon=True).start()
        assert token.wait(timeout=1.0)

    def test_task_cancelled_error(self):
        """TaskCancelledError 包含 task_id 和 reason。"""
        exc = TaskCancelledError(task_id="t-001", reason="timeout")
        assert exc.task_id == "t-001"
        assert exc.reason == "timeout"
        assert "t-001" in str(exc)
        assert "timeout" in str(exc)


class TestExecutionControl:
    """验证 ExecutionControl 容器。"""

    def test_execution_control_default(self):
        """ExecutionControl 默认创建 CancellationToken。"""
        control = ExecutionControl()
        assert control.cancellation is not None
        assert not control.is_cancelled

    def test_execution_control_cancel_delegates(self):
        """ExecutionControl.cancel() 委托给 CancellationToken。"""
        control = ExecutionControl()
        control.cancel("test")
        assert control.is_cancelled
        assert control.cancellation.reason == "test"

    def test_execution_control_raise_if_cancelled(self):
        """ExecutionControl.raise_if_cancelled() 委托给 CancellationToken。"""
        control = ExecutionControl()
        control.cancel("test")
        with pytest.raises(TaskCancelledError):
            control.raise_if_cancelled()


# ═══════════════════════════════════════════════════════════════════
# 3.11-B.6 TASK_CANCELLED 事件类型
# ═══════════════════════════════════════════════════════════════════

class TestTaskCancelledEvent:
    """验证 TASK_CANCELLED 事件类型（ADR-013）。"""

    def test_task_cancelled_event_type_exists(self):
        """TASK_CANCELLED 事件类型已注册。"""
        assert RuntimeEventType.TASK_CANCELLED == "task.cancelled"

    def test_task_cancelled_event_published(self):
        """发布 TASK_CANCELLED 事件能被订阅者接收。"""
        bus = EventBus()
        bus.start()
        received: list[dict] = []

        def on_cancelled(event):
            received.append(event.payload)

        bus.subscribe(RuntimeEventType.TASK_CANCELLED, on_cancelled)
        try:
            bus.publish(
                event_type=RuntimeEventType.TASK_CANCELLED,
                payload={"reason": "user cancelled"},
                task_id="task-001",
                source="orchestrator",
            )
            time.sleep(0.1)
        finally:
            bus.stop()

        assert len(received) == 1
        assert received[0]["reason"] == "user cancelled"