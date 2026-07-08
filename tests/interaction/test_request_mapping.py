"""tests/interaction/test_request_mapping.py — RuntimeRequest → UserRequest 映射完整性测试。

验证所有外部请求字段都能无损透传到 Runtime 内部 UserRequest，
确保 Source Boundary 等环境上下文不丢失。
"""
from __future__ import annotations

from agent_workbench.runtime.interaction import RuntimeRequest, RuntimeRequestSource


def test_request_id_is_preserved() -> None:
    request = RuntimeRequest(text="hello")
    user_request = request.to_user_request()
    assert user_request.metadata["request_id"] == request.request_id
    assert user_request.task_id == request.request_id


def test_source_is_preserved() -> None:
    request = RuntimeRequest(
        source=RuntimeRequestSource.WORKSPACE_SESSION,
        text="analyze project",
    )
    user_request = request.to_user_request()
    assert user_request.metadata["source"] == "workspace_session"


def test_session_id_is_preserved() -> None:
    request = RuntimeRequest(
        source=RuntimeRequestSource.GLOBAL_CHAT,
        text="hello",
        session_id="session-42",
    )
    user_request = request.to_user_request()
    assert user_request.session_id == "session-42"


def test_text_is_preserved() -> None:
    request = RuntimeRequest(text="explain transformer")
    user_request = request.to_user_request()
    assert user_request.text == "explain transformer"


def test_attachments_are_preserved() -> None:
    attachments = [{"name": "doc.pdf", "url": "file:///tmp/doc.pdf"}]
    request = RuntimeRequest(
        text="summarize this",
        attachments=attachments,
    )
    user_request = request.to_user_request()
    assert user_request.attachments == attachments


def test_action_id_is_preserved() -> None:
    request = RuntimeRequest(
        source=RuntimeRequestSource.COMMAND_BAR,
        action_id="format_current_file",
    )
    user_request = request.to_user_request()
    assert user_request.metadata["action_id"] == "format_current_file"


def test_metadata_is_preserved_and_merged() -> None:
    request = RuntimeRequest(
        source=RuntimeRequestSource.WORKSPACE_SESSION,
        text="run test",
        metadata={
            "workspace_id": "ws-1",
            "git_branch": "dev",
        },
    )
    user_request = request.to_user_request()
    assert user_request.metadata["workspace_id"] == "ws-1"
    assert user_request.metadata["git_branch"] == "dev"
    assert user_request.metadata["source"] == "workspace_session"
    assert user_request.metadata["request_id"] == request.request_id


def test_explicit_task_id_overrides_request_id() -> None:
    request = RuntimeRequest(
        task_id="task-explicit",
        text="hello",
    )
    user_request = request.to_user_request()
    assert user_request.task_id == "task-explicit"
    assert user_request.metadata["request_id"] == request.request_id


def test_empty_request_has_defaults() -> None:
    request = RuntimeRequest()
    user_request = request.to_user_request()
    assert user_request.text is None
    assert user_request.attachments == []
    assert user_request.session_id is None
    assert user_request.metadata["source"] == "global_chat"
    assert user_request.metadata["request_id"] == request.request_id
