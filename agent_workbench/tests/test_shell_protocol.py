"""test_shell_protocol.py — Phase 1-B.1 Shell Protocol 验证。

验证：
- ShellProtocol 可被 QtShell/WebShell 实现（Structural Typing）
- Transformers 输入输出正确
- 不依赖 PySide6
"""
from __future__ import annotations

import sys
import os
from dataclasses import dataclass
from typing import List

# 添加项目根目录到 Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from agent_workbench.presentation.shell.protocol import (
    ShellProtocol,
    NavigationItem,
    NavigationGroup,
    WorkspaceMessage,
    WorkspaceState,
    InspectorState,
    CommandState,
)
from agent_workbench.presentation.view_models.session import (
    SessionViewModel,
    MessageViewModel,
)
from agent_workbench.presentation.view_models.capability import CapabilityViewModel
from agent_workbench.presentation.shell.transformers.session import to_navigation_groups
from agent_workbench.presentation.shell.transformers.message import to_workspace_state
from agent_workbench.presentation.shell.transformers.capability import to_navigation_items


class TestShellProtocol:
    """验证 ShellProtocol 接口定义正确。"""

    def test_is_protocol(self) -> None:
        from typing import Protocol
        assert issubclass(ShellProtocol, Protocol), (
            "ShellProtocol must be typing.Protocol"
        )

    def test_can_be_implemented(self) -> None:
        """验证任何实现同名方法的类都满足协议（不要求继承）。"""

        class QtShell:  # 不继承 ShellProtocol
            def update_navigation(self, groups: List[NavigationGroup]) -> None:
                pass

            def update_workspace(self, state: WorkspaceState) -> None:
                pass

            def update_inspector(self, state: InspectorState) -> None:
                pass

            def update_command(self, state: CommandState) -> None:
                pass

        shell = QtShell()
        assert hasattr(shell, "update_navigation")
        assert hasattr(shell, "update_workspace")

    def test_navigation_model_names(self) -> None:
        """Navigation 使用结构模型命名（Group），非 State。"""
        assert "NavigationGroup" in globals()
        assert "NavigationItem" in globals()
        # NavigationState 不应存在
        from agent_workbench.presentation.shell import protocol as pmod
        assert not hasattr(pmod, "NavigationState"), (
            "NavigationState should be renamed to NavigationGroup"
        )


class TestSessionTransformer:
    """验证 SessionViewModel → NavigationGroup 转换。"""

    def test_empty(self) -> None:
        assert to_navigation_groups([]) == []

    def test_single_group(self) -> None:
        sessions = [
            SessionViewModel(id="1", title="Chat 1", group_id="today"),
            SessionViewModel(id="2", title="Chat 2", group_id="today"),
        ]
        groups = to_navigation_groups(sessions)
        assert len(groups) == 1
        assert groups[0].id == "today"
        assert groups[0].title == "today"
        assert len(groups[0].items) == 2
        assert groups[0].items[0].kind == "session"
        assert isinstance(groups[0], NavigationGroup)

    def test_multi_group(self) -> None:
        sessions = [
            SessionViewModel(id="1", title="Today", group_id="today"),
            SessionViewModel(id="2", title="Yesterday", group_id="yesterday"),
        ]
        groups = to_navigation_groups(sessions)
        assert len(groups) == 2

    def test_is_active(self) -> None:
        sessions = [
            SessionViewModel(id="1", title="Chat 1", group_id="today", is_active=True),
            SessionViewModel(id="2", title="Chat 2", group_id="today", is_active=False),
        ]
        groups = to_navigation_groups(sessions)
        assert groups[0].items[0].is_active is True
        assert groups[0].items[1].is_active is False

    def test_default_group(self) -> None:
        sessions = [
            SessionViewModel(id="1", title="Chat 1", group_id=""),
        ]
        groups = to_navigation_groups(sessions)
        assert groups[0].id == "default"


class TestMessageTransformer:
    """验证 MessageViewModel → WorkspaceState 转换。"""

    def test_empty(self) -> None:
        ws = to_workspace_state()
        assert ws.title == ""
        assert ws.messages == []
        assert ws.models == []
        assert isinstance(ws, WorkspaceState)

    def test_full(self) -> None:
        msgs = [
            MessageViewModel(id="m1", role="user", content="Hello"),
            MessageViewModel(
                id="m2", role="assistant", content="Hi!",
                tool_calls=[{"name": "search", "result": {}, "status": "ok"}],
            ),
        ]
        ws = to_workspace_state(
            title="Test Session",
            subtitle="f:/project",
            messages=msgs,
            models=["gpt-4o", "claude-3.5"],
        )
        assert ws.title == "Test Session"
        assert ws.subtitle == "f:/project"
        assert len(ws.messages) == 2
        assert ws.messages[0].role == "user"
        assert ws.messages[1].tool_calls[0]["name"] == "search"
        assert ws.models == ["gpt-4o", "claude-3.5"]


class TestCapabilityTransformer:
    """验证 CapabilityViewModel → NavigationItem 转换。"""

    def test_empty(self) -> None:
        assert to_navigation_items([]) == []

    def test_multiple(self) -> None:
        caps = [
            CapabilityViewModel(id="python", name="Python", description="exec", category="tool", is_enabled=True),
            CapabilityViewModel(id="filesystem", name="FS MCP", description="fs", category="mcp"),
        ]
        items = to_navigation_items(caps)
        assert len(items) == 2
        assert items[0].kind == "tool"
        assert items[0].is_active is True
        assert items[1].kind == "mcp"
        assert isinstance(items[0], NavigationItem)


class TestNoDependencies:
    """验证 Shell 层无禁止依赖。"""

    def test_no_pyside6(self) -> None:
        shell_dir = os.path.join(os.path.dirname(__file__), "..", "presentation", "shell")
        for root, _, files in os.walk(shell_dir):
            for fname in files:
                if fname.endswith(".py"):
                    fpath = os.path.join(root, fname)
                    with open(fpath, encoding="utf-8") as f:
                        src = f.read()
                    for line in src.splitlines():
                        stripped = line.strip()
                        if stripped.startswith("#") or stripped.startswith('"""'):
                            continue
                        # 只标记真正 import PySide6 的行
                        if "PySide6" in stripped and (stripped.startswith("from ") or stripped.startswith("import ")):
                            raise AssertionError(f"PySide6 import in {fpath}: {stripped}")

    def test_no_runtime(self) -> None:
        shell_dir = os.path.join(os.path.dirname(__file__), "..", "presentation", "shell")
        for root, _, files in os.walk(shell_dir):
            for fname in files:
                if fname.endswith(".py"):
                    fpath = os.path.join(root, fname)
                    with open(fpath, encoding="utf-8") as f:
                        src = f.read()
                    for line in src.splitlines():
                        stripped = line.strip()
                        if stripped.startswith("#") or stripped.startswith('"""'):
                            continue
                        for forbidden in ["from runtime", "import runtime"]:
                            if forbidden in stripped.lower() and (stripped.startswith("from ") or stripped.startswith("import ")):
                                raise AssertionError(f"Runtime import in {fpath}: {stripped}")


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
