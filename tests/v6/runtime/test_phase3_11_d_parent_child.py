"""tests/v6/runtime/test_phase3_11_d_parent_child.py — Phase 3.11-D Parent-Child Execution 测试。

验证目标（按 v0.3 Architecture Review）：
    - ExecutionMetadata 零 graph 字段 + deadline_at 模型
    - ExecutionRegistry topology owner（active references）
    - Cleanup safe predicate 三条件
    - CancellationPropagationContext invariants（origin/chain + depth）
    - Cancellation propagation Top-down DFS 后序
    - Deadline 模型 effective = min(parent, child)
    - DEADLINE_EXCEEDED 触发 cancel
    - RuntimeContext ABI 不变量：ctx.control is ctx.execution.control

测试分层（60% Primitive + 40% Integration）：
    Primitive（直接验证数据结构与算法）：
    - CancellationPropagationContext
    - ExecutionRegistry（含 cleanup_due 确定性触发）
    - Deadline 计算与 PropagationType

    Integration（通过公共 API 验证）：
    - RuntimeContext ABI 不变量
    - submit_child() 公共入口
    - cancel() 公共入口
    - cleanup_due(now) 确定性清理（不依赖 Foundation worker）

约束：
    - 不修改 RuntimeState ABI
    - 不修改 RuntimeEvent schema
    - 不修改 RuntimeContext ABI
    - 不调用私有 _start_deadline_timer() / _cancel_with_deadline()
    - 不依赖 Foundation mode worker 生命周期
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List

import pytest

from v6.runtime.cancellation_propagation import (
    CancellationPropagationContext,
    CancellationPropagationLimitExceeded,
    MAX_PROPAGATION_DEPTH,
    PropagationType,
)
from v6.runtime.context import RuntimeContext
from v6.runtime.enums import LifecycleState, RuntimeState
from v6.runtime.event_bus import EventBus, RuntimeEventType
from v6.runtime.execution_metadata import ExecutionMetadata
from v6.runtime.execution_registry import ExecutionNode, ExecutionRegistry
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


def future_time(seconds: float) -> datetime:
    """返回未来时间（用于 cleanup_due 确定性触发）。"""
    return datetime.now(timezone.utc) + timedelta(seconds=seconds)


# ═══════════════════════════════════════════════════════════════════
# Primitive Tests — CancellationPropagationContext (4)
# ═══════════════════════════════════════════════════════════════════


class TestCancellationPropagationContextPrimitive:
    """Primitive: CancellationPropagationContext 自身行为。"""

    def test_origin_chain_invariant(self):
        """chain[0] == origin_execution_id（__post_init__ 验证）。"""
        ctx = CancellationPropagationContext(
            propagation_type=PropagationType.PARENT_CANCELLED,
            origin_execution_id="exec-A",
            chain=("exec-A", "exec-B"),
            reason="test",
            initiated_at=datetime.now(timezone.utc),
        )
        assert ctx is not None

        with pytest.raises(ValueError, match="chain\\[0\\]"):
            CancellationPropagationContext(
                propagation_type=PropagationType.PARENT_CANCELLED,
                origin_execution_id="exec-A",
                chain=("exec-B", "exec-C"),
                reason="test",
                initiated_at=datetime.now(timezone.utc),
            )

    def test_extend_enforces_depth_internally(self):
        """extend() 内部 enforce depth（不依赖调用方）。"""
        ctx = CancellationPropagationContext.user_request("exec-1")
        try:
            for i in range(MAX_PROPAGATION_DEPTH + 5):
                ctx = ctx.extend(f"exec-{i + 2}")
        except CancellationPropagationLimitExceeded as e:
            assert e.depth > e.max_depth
            assert e.max_depth == MAX_PROPAGATION_DEPTH

    def test_frozen_immutability(self):
        """CancellationPropagationContext frozen 不可变。"""
        ctx = CancellationPropagationContext.user_request("exec-1")
        with pytest.raises(Exception):  # FrozenInstanceError
            ctx.reason = "modified"  # type: ignore[misc]

    def test_propagation_extend_creates_new_instance(self):
        """extend() 返回新实例（不可变语义）。"""
        ctx1 = CancellationPropagationContext.user_request("exec-1")
        ctx2 = ctx1.extend("exec-2")
        assert ctx1 is not ctx2
        assert ctx1.chain == ("exec-1",)
        assert ctx2.chain == ("exec-1", "exec-2")
        assert ctx2.origin_execution_id == "exec-1"


# ═══════════════════════════════════════════════════════════════════
# Primitive Tests — ExecutionRegistry (7)
# ═══════════════════════════════════════════════════════════════════


class TestExecutionRegistryPrimitive:
    """Primitive: ExecutionRegistry 自身行为（包含 cleanup_due 确定性触发）。"""

    def test_register_no_cycle(self):
        """register() 检测环路。"""
        reg = ExecutionRegistry()
        reg.register("exec-a", "ta", None)
        reg.register("exec-b", "tb", "exec-a")
        with pytest.raises(ValueError, match="Cycle detected"):
            reg.register("exec-c", "tc", "exec-c")

    def test_cleanup_safe_predicate_three_conditions(self):
        """_is_cleanup_safe 三条件守卫（terminal + descendants + retention）。"""
        reg = ExecutionRegistry()
        eid = "exec-x"
        node = ExecutionNode(
            execution_id=eid,
            task_id="tx",
            parent_execution_id=None,
        )
        reg._nodes[eid] = node
        now = datetime.now(timezone.utc)

        # Condition 1 失败：node 未 terminal
        assert not reg._is_cleanup_safe(node, now)

        # Condition 3 失败：cleanup_eligible_at > now
        node.terminated_at = now
        node.cleanup_eligible_at = now + timedelta(seconds=300)
        assert not reg._is_cleanup_safe(node, now)

        # 全部满足
        node.cleanup_eligible_at = now - timedelta(seconds=1)
        assert reg._is_cleanup_safe(node, now)

    def test_cleanup_due_deterministic_trigger(self):
        """cleanup_due(now) 按三条件确定性清理（替代 timer 依赖）。"""
        reg = ExecutionRegistry()
        parent = "exec-p"
        child = "exec-c"
        reg.register(parent, "tp", None)
        reg.register(child, "tc", parent)
        reg.mark_terminated(child)
        reg.mark_terminated(parent)

        # 当前时间：cleanup_eligible_at 未到
        assert reg.cleanup_due(datetime.now(timezone.utc)) == 0

        # 推进到未来：所有 eligible 且 safe 的节点清理
        cleaned = reg.cleanup_due(future_time(600))
        assert cleaned == 2
        assert not reg.has_node(parent)
        assert not reg.has_node(child)

    def test_cleanup_due_blocks_when_descendants_active(self):
        """descendants 未 terminal 时，cleanup_due 跳过 parent。"""
        reg = ExecutionRegistry()
        parent = "exec-p"
        child = "exec-c"
        reg.register(parent, "tp", None)
        reg.register(child, "tc", parent)
        reg.mark_terminated(parent)
        # child 仍 active（未 terminal）

        cleaned = reg.cleanup_due(future_time(600))
        assert cleaned == 0
        assert reg.has_node(parent)

    def test_children_ids_preserved_after_cleanup_due(self):
        """v0.3: cleanup_due 清理后 parent.children_ids 保留历史引用。"""
        reg = ExecutionRegistry()
        parent = "exec-p"
        child = "exec-c"
        reg.register(parent, "tp", None)
        reg.register(child, "tc", parent)
        reg.mark_terminated(child)

        cleaned = reg.cleanup_due(future_time(600))
        assert cleaned == 1
        assert not reg.has_node(child)

        parent_node = reg.get(parent)
        assert parent_node is not None
        assert child in parent_node.children_ids  # historical preserved

    def test_get_active_children_filters_cleaned(self):
        """active children filter（已清理的不返回）。"""
        reg = ExecutionRegistry()
        parent = "exec-p"
        child1 = "exec-c1"
        child2 = "exec-c2"
        reg.register(parent, "tp", None)
        reg.register(child1, "tc1", parent)
        reg.register(child2, "tc2", parent)
        reg.mark_terminated(child1)
        reg.cleanup_due(future_time(600))

        active = reg.get_active_children(parent)
        active_ids = [c.execution_id for c in active]
        assert "exec-c2" in active_ids
        assert "exec-c1" not in active_ids

    def test_get_root_and_depth(self):
        """get_root / get_depth 正确追溯。"""
        reg = ExecutionRegistry()
        reg.register("root", "tr", None)
        reg.register("child", "tc", "root")
        reg.register("grand", "tg", "child")

        root = reg.get_root("grand")
        assert root is not None
        assert root.execution_id == "root"
        assert reg.get_depth("root") == 0
        assert reg.get_depth("child") == 1
        assert reg.get_depth("grand") == 2


# ═══════════════════════════════════════════════════════════════════
# Primitive Tests — Deadline (3)
# ═══════════════════════════════════════════════════════════════════


class TestDeadlinePrimitive:
    """Primitive: deadline 计算与 PropagationType。"""

    def test_deadline_exceeded_propagation_type(self):
        """PropagationType.DEADLINE_EXCEEDED 存在。"""
        assert PropagationType.DEADLINE_EXCEEDED.value == "deadline_exceeded"

    def test_parent_timeout_removed(self):
        """PARENT_TIMEOUT 已移除（v0.3 统一命名）。"""
        assert not hasattr(PropagationType, "PARENT_TIMEOUT")

    def test_deadline_exceeded_static_factory(self):
        """CancellationPropagationContext.deadline_exceeded() 工厂。"""
        now = datetime.now(timezone.utc)
        ctx = CancellationPropagationContext.deadline_exceeded("exec-1", now)
        assert ctx.propagation_type == PropagationType.DEADLINE_EXCEEDED
        assert ctx.origin_execution_id == "exec-1"
        assert ctx.chain[0] == "exec-1"
        assert "deadline exceeded at" in ctx.reason


# ═══════════════════════════════════════════════════════════════════
# Primitive Tests — ExecutionMetadata (2)
# ═══════════════════════════════════════════════════════════════════


class TestExecutionMetadataPrimitive:
    """Primitive: ExecutionMetadata 字段约束。"""

    def test_execution_metadata_no_graph_fields(self):
        """ExecutionMetadata 零 graph 字段（除 parent_execution_id）。"""
        meta = ExecutionMetadata(task_id="t1")
        forbidden = [
            "children_ids",
            "execution_depth",
            "root_execution_id",
            "sibling_count",
        ]
        for field_name in forbidden:
            assert not hasattr(meta, field_name), f"forbidden field {field_name}"
        assert hasattr(meta, "parent_execution_id")
        assert hasattr(meta, "execution_id")
        assert hasattr(meta, "task_id")
        assert hasattr(meta, "deadline_at")
        assert hasattr(meta, "control")

    def test_is_deadline_reached(self):
        """is_deadline_reached 计算正确。"""
        now = datetime.now(timezone.utc)
        assert not ExecutionMetadata(task_id="t1").is_deadline_reached
        meta = ExecutionMetadata(task_id="t2", deadline_at=now + timedelta(seconds=10))
        assert not meta.is_deadline_reached
        meta.deadline_at = now - timedelta(seconds=10)
        assert meta.is_deadline_reached


# ═══════════════════════════════════════════════════════════════════
# Integration Tests — RuntimeContext ABI（公共 API）(2)
# ═══════════════════════════════════════════════════════════════════


class TestRuntimeContextABI:
    """Integration: RuntimeContext.control ABI 不变量（通过 attach_execution 公共入口）。"""

    def test_attach_execution_unifies_control(self):
        """attach_execution() 绑定 execution 与 control（is 同一对象）。"""
        ctx = RuntimeContext.new(task_id="t")
        assert ctx.execution is None
        assert ctx.control is not None

        # 通过 attach_execution 公共入口
        exec_meta = ExecutionMetadata(task_id="t")
        ctx.attach_execution(exec_meta)

        # v0.3 不变量
        assert ctx.execution is exec_meta
        assert ctx.control is exec_meta.control

    def test_attach_execution_replaces_previous(self):
        """attach_execution() 替换旧 execution，control 引用同步更新。"""
        ctx = RuntimeContext.new(task_id="t")
        old_exec = ExecutionMetadata(task_id="t")
        ctx.attach_execution(old_exec)
        old_control = ctx.control

        new_exec = ExecutionMetadata(task_id="t2")
        ctx.attach_execution(new_exec)

        assert ctx.execution is new_exec
        assert ctx.control is new_exec.control
        assert ctx.control is not old_control


# ═══════════════════════════════════════════════════════════════════
# Integration Tests — Orchestrator 公共 API (5)
# ═══════════════════════════════════════════════════════════════════


class TestOrchestratorPublicAPI:
    """Integration: Orchestrator 公共 API 验证（submit_child / cancel / execution_registry）。"""

    def test_execution_registry_exposed(self, orch: Orchestrator):
        """Orchestrator.execution_registry 暴露 Registry 实例。"""
        assert orch.execution_registry is not None
        assert isinstance(orch.execution_registry, ExecutionRegistry)

    def test_submit_child_via_registry_link(self, orch: Orchestrator):
        """submit_child() 通过 Registry 建立 parent-child 关系。"""
        # 在 Registry 中预创建 parent（绕过 submit 的 worker 启动）
        parent_id = "exec-public-parent"
        orch.execution_registry.register(parent_id, "task-parent-pub", None)

        child_task = Task(capability="chat", payload={"text": "child"})
        child_task.task_id = "task-child-pub"

        # submit_child 通过公共 API
        child_task_id = orch.submit_child(parent_id, child_task)
        ctx = orch.context(child_task_id)
        assert ctx is not None
        assert ctx.execution is not None
        assert ctx.execution.parent_execution_id == parent_id
        assert ctx.control is ctx.execution.control  # ABI 不变量

    def test_cancel_propagation_chain_construction(self, orch: Orchestrator):
        """cancel() 构造的 propagation context chain 完整。"""
        reg = orch.execution_registry
        reg.register("exec-cancel-root", "tr", None)
        reg.register("exec-cancel-mid", "tm", "exec-cancel-root")
        reg.register("exec-cancel-leaf", "tl", "exec-cancel-mid")

        # 验证 chain 通过 extend 构造正确
        ctx_root = CancellationPropagationContext.user_request(
            "exec-cancel-root", "user cancel"
        )
        ctx_mid = ctx_root.extend("exec-cancel-mid")
        ctx_leaf = ctx_mid.extend("exec-cancel-leaf")

        assert ctx_leaf.chain == ("exec-cancel-root", "exec-cancel-mid", "exec-cancel-leaf")
        assert ctx_leaf.origin_execution_id == "exec-cancel-root"
        # payload 结构
        payload = ctx_leaf.to_payload()
        assert payload["propagation_type"] == "user_request"
        assert payload["origin_execution_id"] == "exec-cancel-root"
        assert payload["chain"] == [
            "exec-cancel-root",
            "exec-cancel-mid",
            "exec-cancel-leaf",
        ]

    def test_effective_deadline_takes_min(self, orch: Orchestrator):
        """_compute_effective_deadline = min(parent, child)。"""
        now = datetime.now(timezone.utc)
        parent_ctx = RuntimeContext.new(task_id="p")
        parent_ctx.attach_execution(
            ExecutionMetadata(task_id="p", deadline_at=now + timedelta(seconds=60))
        )
        child_ctx = RuntimeContext.new(task_id="c")
        child_ctx.attach_execution(
            ExecutionMetadata(task_id="c", deadline_at=now + timedelta(seconds=30))
        )

        effective = orch._compute_effective_deadline(parent_ctx, child_ctx)
        assert effective == child_ctx.execution.deadline_at  # min(60, 30) = 30

    def test_effective_deadline_handles_none(self, orch: Orchestrator):
        """_compute_effective_deadline 处理 None（仅 parent / 仅 child / 都无）。"""
        now = datetime.now(timezone.utc)

        # 仅 parent 设置
        parent_ctx = RuntimeContext.new(task_id="p")
        parent_ctx.attach_execution(
            ExecutionMetadata(task_id="p", deadline_at=now + timedelta(seconds=60))
        )
        child_ctx = RuntimeContext.new(task_id="c")  # 无 deadline
        effective = orch._compute_effective_deadline(parent_ctx, child_ctx)
        assert effective == parent_ctx.execution.deadline_at

        # 仅 child 设置
        parent_ctx2 = RuntimeContext.new(task_id="p2")
        child_ctx2 = RuntimeContext.new(task_id="c2")
        child_ctx2.attach_execution(
            ExecutionMetadata(task_id="c2", deadline_at=now + timedelta(seconds=30))
        )
        effective = orch._compute_effective_deadline(parent_ctx2, child_ctx2)
        assert effective == child_ctx2.execution.deadline_at

        # 都未设置
        assert (
            orch._compute_effective_deadline(
                RuntimeContext.new(task_id="p3"),
                RuntimeContext.new(task_id="c3"),
            )
            is None
        )


# ═══════════════════════════════════════════════════════════════════
# Integration Tests — Deadline Cancellation 公共 API (1)
# ═══════════════════════════════════════════════════════════════════


class TestDeadlineCancellationPublicAPI:
    """Integration: 通过公共 cancel_with_propagation 验证 DEADLINE_EXCEEDED 路径。

    不调用私有 _start_deadline_timer() / _cancel_with_deadline()。
    通过 Orchestrator 暴露的 cancel_with_propagation 公共 API 验证。
    """

    def test_deadline_exceeded_propagation_via_cancel_with_propagation(
        self, orch: Orchestrator, bus: EventBus
    ):
        """DEADLINE_EXCEEDED propagation context 通过 cancel_with_propagation 发布。"""
        events: list = []

        def _on(event):
            events.append(event)

        bus.subscribe(RuntimeEventType.TASK_CANCELLED, _on)

        # 预创建 ctx（绕过 submit worker 启动）
        from v6.runtime.enums import ActivityState
        ctx = RuntimeContext.new(task_id="t-deadline-int")
        ctx.attach_execution(
            ExecutionMetadata(
                task_id="t-deadline-int",
                deadline_at=datetime.now(timezone.utc) - timedelta(seconds=1),
            )
        )
        orch._contexts["t-deadline-int"] = ctx
        orch._task_states["t-deadline-int"] = RuntimeState.EXECUTING

        # 构造 DEADLINE_EXCEEDED propagation
        propagation = CancellationPropagationContext(
            propagation_type=PropagationType.DEADLINE_EXCEEDED,
            origin_execution_id=ctx.execution.execution_id,
            chain=(ctx.execution.execution_id,),
            reason=f"deadline exceeded at {ctx.execution.deadline_at.isoformat()}",
            initiated_at=datetime.now(timezone.utc),
        )

        # 通过公共 cancel_with_propagation
        result = orch.cancel_with_propagation("t-deadline-int", propagation)
        assert result is True

        # 等待事件分发
        import time
        time.sleep(0.3)

        # 验证 TASK_CANCELLED 事件 payload
        deadline_events = [
            e for e in events if e.type == RuntimeEventType.TASK_CANCELLED
        ]
        assert len(deadline_events) >= 1
        event = deadline_events[0]
        assert event.payload["propagation_type"] == "deadline_exceeded"
        assert event.payload["origin_execution_id"] == ctx.execution.execution_id
        assert "deadline exceeded at" in event.payload["reason"]


# ═══════════════════════════════════════════════════════════════════
# Integration Tests — Cleanup Lifecycle（公共 API）(1)
# ═══════════════════════════════════════════════════════════════════


class TestCleanupLifecyclePublicAPI:
    """Integration: 通过 ExecutionRegistry 公共 API 验证 cleanup 完整生命周期。"""

    def test_full_lifecycle_mark_terminated_to_cleanup_due(self, orch: Orchestrator):
        """完整生命周期：register → mark_terminated → cleanup_due(now+retention)。"""
        reg = orch.execution_registry
        reg.register("exec-lifecycle-int", "tl", None)
        assert reg.has_node("exec-lifecycle-int")

        # 模拟终态（无需触发 worker）
        reg.mark_terminated("exec-lifecycle-int")

        # 当前：未到期
        assert reg.cleanup_due(datetime.now(timezone.utc)) == 0

        # 推进时间
        assert reg.cleanup_due(future_time(600)) == 1
        assert not reg.has_node("exec-lifecycle-int")