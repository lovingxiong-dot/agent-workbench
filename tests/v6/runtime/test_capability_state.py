"""tests/v6/runtime/test_capability_state.py — CapabilityState 生命周期契约测试。"""
from __future__ import annotations

from agent_workbench.runtime.capability import CapabilityExecutionState, CapabilityState


def test_capability_state_has_reserved_workflow_states() -> None:
    assert CapabilityState.PENDING.value == "pending"
    assert CapabilityState.RESOLVED.value == "resolved"
    assert CapabilityState.SCHEDULED.value == "scheduled"
    assert CapabilityState.RUNNING.value == "running"
    assert CapabilityState.COMPLETED.value == "completed"
    assert CapabilityState.FAILED.value == "failed"
    # 预留 Workflow 阶段状态
    assert CapabilityState.CANCELLED.value == "cancelled"
    assert CapabilityState.TIMEOUT.value == "timeout"
    assert CapabilityState.SKIPPED.value == "skipped"


def test_capability_execution_state_defaults() -> None:
    state = CapabilityExecutionState(
        capability_id="image_generation",
        state=CapabilityState.RUNNING,
    )
    assert state.capability_id == "image_generation"
    assert state.state == CapabilityState.RUNNING
    assert state.task_id is None
    assert state.started_at is None
    assert state.finished_at is None
    assert state.error is None
    assert state.metadata == {}


def test_capability_execution_state_full_fields() -> None:
    state = CapabilityExecutionState(
        capability_id="coding.python.analysis",
        state=CapabilityState.FAILED,
        task_id="task-1",
        started_at=1.0,
        finished_at=2.0,
        error="engine timeout",
        metadata={"attempt": 1},
    )
    assert state.task_id == "task-1"
    assert state.error == "engine timeout"
    assert state.metadata["attempt"] == 1
