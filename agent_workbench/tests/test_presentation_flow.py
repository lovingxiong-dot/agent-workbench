"""test_presentation_flow.py — Phase 1-C Presentation Pipeline 全链路验证。

验证：
    Mock Runtime Data
    → ViewModel (dataclass)
    → Transformer
    → Shell Contract (NavigationGroup / WorkspaceState / InspectorState)

不依赖 Runtime、PySide6、v6/ui。
"""
from __future__ import annotations

import sys
import os

# 添加项目根目录到 Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from agent_workbench.presentation.shell.integration import PresentationPipeline
from agent_workbench.presentation.shell.protocol import (
    InspectorState,
    NavigationGroup,
    NavigationItem,
    WorkspaceState,
)


# ══════════════════════════════════════════════════════════════════
# 链路 1: Session → NavigationGroup
# ══════════════════════════════════════════════════════════════════

def test_sessions_to_navigation_groups() -> None:
    """Mock Runtime Session → NavigationGroup 全链路。"""
    raw_sessions = [
        {"sid": "s1", "title": "Chat 1", "group_id": "today", "is_active": True},
        {"sid": "s2", "title": "Chat 2", "group_id": "today"},
        {"sid": "s3", "title": "Yesterday Chat", "group_id": "yesterday"},
    ]
    pipeline = PresentationPipeline()
    groups = pipeline.sessions_to_navigation_groups(raw_sessions)

    assert len(groups) == 2
    assert isinstance(groups[0], NavigationGroup)
    assert groups[0].id == "today"
    assert len(groups[0].items) == 2
    assert groups[0].items[0].title == "Chat 1"
    assert groups[0].items[0].kind == "session"
    assert groups[0].items[0].is_active is True

    assert groups[1].id == "yesterday"
    assert len(groups[1].items) == 1
    assert isinstance(groups[1].items[0], NavigationItem)


def test_empty_sessions() -> None:
    """空 Session 列表 → 空 NavigationGroup 列表。"""
    groups = PresentationPipeline.sessions_to_navigation_groups([])
    assert groups == []


# ══════════════════════════════════════════════════════════════════
# 链路 2: Message → WorkspaceState
# ══════════════════════════════════════════════════════════════════

def test_messages_to_workspace_state() -> None:
    """Mock Runtime Message → WorkspaceState 全链路。"""
    raw_messages = [
        {"id": "m1", "role": "user", "content": "Hello"},
        {"id": "m2", "role": "assistant", "content": "Hi!", "tool_calls": [{"name": "search", "result": {}, "status": "ok"}]},
        {"id": "m3", "role": "tool", "content": "result", "tool_calls": [{"name": "exec", "result": {"ok": True}, "status": "ok"}]},
    ]
    ws = PresentationPipeline.messages_to_workspace_state(
        title="Test Session",
        subtitle="f:/project",
        raw_messages=raw_messages,
        models=["gpt-4o", "claude-3.5"],
    )

    assert isinstance(ws, WorkspaceState)
    assert ws.title == "Test Session"
    assert ws.subtitle == "f:/project"
    assert len(ws.messages) == 3
    assert ws.messages[0].role == "user"
    assert ws.messages[1].role == "assistant"
    assert ws.messages[1].tool_calls[0]["name"] == "search"
    assert ws.messages[2].role == "tool"
    assert ws.models == ["gpt-4o", "claude-3.5"]


def test_empty_messages() -> None:
    """空 Message 列表 → WorkspaceState。"""
    ws = PresentationPipeline.messages_to_workspace_state("Empty", "", [])
    assert ws.title == "Empty"
    assert ws.messages == []
    assert ws.models == []


# ══════════════════════════════════════════════════════════════════
# 链路 3: Capability → NavigationItem
# ══════════════════════════════════════════════════════════════════

def test_capabilities_to_navigation_items() -> None:
    """Mock Runtime Capability → NavigationItem 全链路。"""
    raw_caps = [
        {"id": "python", "name": "Python", "description": "exec", "category": "tool", "is_enabled": True},
        {"id": "filesystem", "name": "FS MCP", "description": "fs", "category": "mcp"},
        {"id": "refactor", "name": "Refactor", "description": "refactor code", "category": "skill"},
        {"id": "auto_commit", "name": "Auto Commit", "description": "auto", "category": "automation", "is_enabled": True},
    ]
    items = PresentationPipeline.capabilities_to_navigation_items(raw_caps)

    assert len(items) == 4
    assert isinstance(items[0], NavigationItem)
    assert items[0].kind == "tool"
    assert items[0].is_active is True
    assert items[1].kind == "mcp"
    assert items[1].is_active is False
    assert items[2].kind == "skill"
    assert items[3].kind == "automation"


# ══════════════════════════════════════════════════════════════════
# 链路 4: Metadata → InspectorState
# ══════════════════════════════════════════════════════════════════

def test_metadata_to_inspector_state() -> None:
    """Mock Runtime Metadata → InspectorState。"""
    raw_props = [
        {"name": "provider", "value": "openai", "type": "string"},
        {"name": "temperature", "value": 0.7, "type": "number"},
        {"name": "streaming", "value": True, "type": "boolean"},
    ]
    state = PresentationPipeline.metadata_to_inspector_state("model", raw_props)

    assert isinstance(state, InspectorState)
    assert state.object_id == "model"
    assert len(state.properties) == 3
    assert state.properties[0]["name"] == "provider"
    assert state.properties[1]["value"] == 0.7
    assert state.properties[2]["value"] is True


def test_empty_metadata() -> None:
    """空 Metadata → InspectorState。"""
    state = PresentationPipeline.metadata_to_inspector_state("empty", [])
    assert state.object_id == "empty"
    assert state.properties == []


# ══════════════════════════════════════════════════════════════════
# 综合：4 链路集成验证
# ══════════════════════════════════════════════════════════════════

def test_full_pipeline_integration() -> None:
    """Mock Runtime 全数据 → 三种 Shell Contract 同时验证。"""
    # 输入
    raw_sessions = [{"sid": "s1", "title": "Chat", "group_id": "today", "is_active": True}]
    raw_messages = [{"id": "m1", "role": "user", "content": "hi"}]
    raw_caps = [{"id": "python", "name": "Python", "category": "tool"}]
    raw_props = [{"name": "model", "value": "gpt-4o", "type": "string"}]

    # 输出
    nav = PresentationPipeline.sessions_to_navigation_groups(raw_sessions)
    ws = PresentationPipeline.messages_to_workspace_state("T", "S", raw_messages)
    items = PresentationPipeline.capabilities_to_navigation_items(raw_caps)
    ins = PresentationPipeline.metadata_to_inspector_state("m", raw_props)

    # 类型断言
    assert isinstance(nav[0], NavigationGroup)
    assert isinstance(ws, WorkspaceState)
    assert isinstance(items[0], NavigationItem)
    assert isinstance(ins, InspectorState)

    # 数据完整性
    assert nav[0].items[0].title == "Chat"
    assert ws.messages[0].content == "hi"
    assert items[0].title == "Python"  # Capability.name → NavigationItem.title
    assert ins.properties[0]["value"] == "gpt-4o"


if __name__ == "__main__":
    test_sessions_to_navigation_groups()
    test_empty_sessions()
    test_messages_to_workspace_state()
    test_empty_messages()
    test_capabilities_to_navigation_items()
    test_metadata_to_inspector_state()
    test_empty_metadata()
    test_full_pipeline_integration()
    print("ALL 8 TESTS PASSED")
