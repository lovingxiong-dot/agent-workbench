"""tests/v6/test_v6_user_request.py — UserRequest 协议对象测试。"""
from __future__ import annotations

from v6.runtime.user_request import UserRequest


def test_user_request_has_foundation_fields() -> None:
    """UserRequest 包含通用输入字段且 metadata / attachments 可扩展。"""
    req = UserRequest(
        text="hello",
        session_id="sess-001",
        task_id="t-1",
        metadata={"origin": "chat"},
        attachments=[{"type": "image", "url": "http://example.com/x.png"}],
    )

    assert req.text == "hello"
    assert req.session_id == "sess-001"
    assert req.task_id == "t-1"
    assert req.metadata == {"origin": "chat"}
    assert len(req.attachments) == 1


def test_user_request_defaults_are_safe() -> None:
    """默认字段为空列表 / 空字典，不会共享可变默认值。"""
    r1 = UserRequest()
    r2 = UserRequest()

    assert r1.attachments is not r2.attachments
    assert r1.metadata is not r2.metadata
    r1.metadata["x"] = 1
    assert "x" not in r2.metadata
