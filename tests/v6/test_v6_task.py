"""tests/v6/test_v6_task.py — Task 数据模型测试。

验证 Foundation 长期接口：
- Task 包含 id / capability / payload / metadata / created_at。
- 旧代码使用的 task_id / type 别名仍可用。
- session_id 同步到 metadata。
- ChatTask / AnalyzeTask 正确设置 capability。
"""
from __future__ import annotations

from datetime import datetime, timezone

from v6.runtime.task import AnalyzeTask, ChatTask, Task


def test_task_foundation_fields() -> None:
    """Task 包含 Foundation 所需的五个核心字段。"""
    before = datetime.now(timezone.utc)
    task = Task(capability="chat", payload={"text": "hello"})
    after = datetime.now(timezone.utc)

    assert isinstance(task.id, str) and len(task.id) == 32
    assert task.capability == "chat"
    assert task.payload == {"text": "hello"}
    assert task.metadata == {}
    assert before <= task.created_at <= after


def test_task_backward_compatible_aliases() -> None:
    """旧代码使用的 task_id 与 type 别名映射到 id 与 capability。"""
    task = Task(task_id="t-1", type="tool", payload={})

    assert task.id == "t-1"
    assert task.task_id == "t-1"
    assert task.capability == "tool"
    assert task.type == "tool"


def test_task_session_id_syncs_to_metadata() -> None:
    """session_id 保留为顶层字段，同时写入 metadata。"""
    task = Task(capability="chat", session_id="sess-001")

    assert task.session_id == "sess-001"
    assert task.metadata.get("session_id") == "sess-001"


def test_chat_task_sets_capability() -> None:
    """ChatTask 自动设置 capability=chat 并将 text 写入 payload。"""
    task = ChatTask(text="hello", session_id="sess-002")

    assert task.capability == "chat"
    assert task.type == "chat"
    assert task.payload["text"] == "hello"
    assert task.metadata["session_id"] == "sess-002"


def test_analyze_task_sets_capability() -> None:
    """AnalyzeTask 自动设置 capability=analyze 并将 path 写入 payload。"""
    task = AnalyzeTask(target_path="/tmp/project")

    assert task.capability == "analyze"
    assert task.payload["path"] == "/tmp/project"


def test_task_default_capability_from_class_name() -> None:
    """未显式指定 capability 时，从类名推导默认值。"""

    class CustomTask(Task):
        pass

    task = CustomTask()
    assert task.capability == "custom"
