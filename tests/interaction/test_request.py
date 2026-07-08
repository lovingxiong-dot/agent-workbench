"""tests/interaction/test_request.py — RuntimeRequest 协议测试。"""
from __future__ import annotations

from agent_workbench.runtime.interaction import RuntimeRequest, RuntimeRequestSource


def test_runtime_request_defaults_to_global_chat() -> None:
    request = RuntimeRequest(text="hello")
    assert request.source == RuntimeRequestSource.GLOBAL_CHAT
    assert request.text == "hello"
    assert request.request_id is not None


def test_runtime_request_preserves_workspace_session_source() -> None:
    request = RuntimeRequest(
        source=RuntimeRequestSource.WORKSPACE_SESSION,
        text="analyze this file",
        session_id="sid-1",
    )
    assert request.source == RuntimeRequestSource.WORKSPACE_SESSION
    user_request = request.to_user_request()
    assert user_request.session_id == "sid-1"
    assert user_request.metadata["source"] == "workspace_session"


def test_runtime_request_action_id_is_not_capability() -> None:
    request = RuntimeRequest(
        source=RuntimeRequestSource.COMMAND_BAR,
        action_id="format_current_file",
    )
    assert request.action_id == "format_current_file"
    user_request = request.to_user_request()
    assert user_request.metadata["action_id"] == "format_current_file"


def test_runtime_request_does_not_have_capability_hint() -> None:
    assert not hasattr(RuntimeRequest, "capability_hint")


def test_runtime_request_to_user_request_carries_request_id() -> None:
    request = RuntimeRequest(text="hello")
    user_request = request.to_user_request()
    assert user_request.task_id == request.request_id
    assert user_request.metadata["request_id"] == request.request_id
