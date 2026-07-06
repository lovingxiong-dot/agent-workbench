"""tests/v6/test_runtime_state_machine.py — RuntimeState 状态机测试。"""
from __future__ import annotations

import pytest

from v6.runtime.enums import RuntimeState
from v6.runtime.state_machine import RuntimeStateMachine, RuntimeStateTransitionError


@pytest.fixture
def sm() -> RuntimeStateMachine:
    return RuntimeStateMachine()


def test_created_to_queued_and_cancelled(sm: RuntimeStateMachine) -> None:
    assert sm.can_transition(RuntimeState.CREATED, RuntimeState.QUEUED)
    assert sm.can_transition(RuntimeState.CREATED, RuntimeState.CANCELLED)
    assert not sm.can_transition(RuntimeState.CREATED, RuntimeState.RUNNING)
    assert not sm.can_transition(RuntimeState.CREATED, RuntimeState.COMPLETED)


def test_queued_to_running_and_cancelled(sm: RuntimeStateMachine) -> None:
    assert sm.transition(RuntimeState.QUEUED, RuntimeState.RUNNING) == RuntimeState.RUNNING
    assert sm.can_transition(RuntimeState.QUEUED, RuntimeState.CANCELLED)
    assert not sm.can_transition(RuntimeState.QUEUED, RuntimeState.COMPLETED)


def test_running_to_all_expected_targets(sm: RuntimeStateMachine) -> None:
    expected = {
        RuntimeState.WAITING,
        RuntimeState.PAUSED,
        RuntimeState.CANCELLED,
        RuntimeState.COMPLETED,
        RuntimeState.FAILED,
    }
    assert set(sm.valid_targets(RuntimeState.RUNNING)) == expected


def test_waiting_to_running_cancelled_failed(sm: RuntimeStateMachine) -> None:
    assert sm.transition(RuntimeState.WAITING, RuntimeState.RUNNING) == RuntimeState.RUNNING
    assert sm.can_transition(RuntimeState.WAITING, RuntimeState.CANCELLED)
    assert sm.can_transition(RuntimeState.WAITING, RuntimeState.FAILED)
    assert not sm.can_transition(RuntimeState.WAITING, RuntimeState.COMPLETED)


def test_paused_to_running_or_cancelled(sm: RuntimeStateMachine) -> None:
    assert sm.can_transition(RuntimeState.PAUSED, RuntimeState.RUNNING)
    assert sm.can_transition(RuntimeState.PAUSED, RuntimeState.CANCELLED)
    assert not sm.can_transition(RuntimeState.PAUSED, RuntimeState.COMPLETED)


def test_failed_to_queued_for_retry(sm: RuntimeStateMachine) -> None:
    assert sm.transition(RuntimeState.FAILED, RuntimeState.QUEUED) == RuntimeState.QUEUED
    assert not sm.can_transition(RuntimeState.FAILED, RuntimeState.RUNNING)


def test_terminal_states_have_no_outgoing_transitions(sm: RuntimeStateMachine) -> None:
    assert sm.valid_targets(RuntimeState.COMPLETED) == []
    assert sm.valid_targets(RuntimeState.CANCELLED) == []
    assert sm.is_terminal(RuntimeState.COMPLETED)
    assert sm.is_terminal(RuntimeState.CANCELLED)


def test_invalid_transition_raises(sm: RuntimeStateMachine) -> None:
    with pytest.raises(RuntimeStateTransitionError):
        sm.transition(RuntimeState.CREATED, RuntimeState.RUNNING)

    with pytest.raises(RuntimeStateTransitionError):
        sm.transition(RuntimeState.COMPLETED, RuntimeState.RUNNING)


def test_error_message_contains_state_names(sm: RuntimeStateMachine) -> None:
    with pytest.raises(RuntimeStateTransitionError) as exc_info:
        sm.transition(RuntimeState.COMPLETED, RuntimeState.RUNNING)
    message = str(exc_info.value)
    assert "completed" in message
    assert "running" in message
    assert "Invalid RuntimeState transition" in message


def test_non_enum_arguments_are_rejected(sm: RuntimeStateMachine) -> None:
    assert not sm.can_transition("created", RuntimeState.RUNNING)  # type: ignore[arg-type]
    assert not sm.can_transition(RuntimeState.CREATED, "running")  # type: ignore[arg-type]
