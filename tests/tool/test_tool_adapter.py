"""tests/tool/test_tool_adapter.py — ToolAdapter 测试。

v6.10.0-alpha Tool Runtime Product Layer。

边界：
  - 测试 Runtime Tool dict → ToolViewModel 转换
  - 不发起 Tool 执行
"""
from __future__ import annotations

import pytest

from agent_workbench.presentation.adapters.tool_adapter import ToolAdapter


class TestToolAdapterBasics:
    """ToolAdapter 基础转换测试。"""

    def test_to_view_model_basic(self) -> None:
        adapter = ToolAdapter()
        tool_dict = {
            "name": "echo_tool",
            "description": "回声工具",
            "enabled": True,
            "permission": "user",
            "schema": {"input": {"type": "string"}},
        }
        vm = adapter.to_view_model(tool_dict)
        assert vm.tool_id == "echo_tool"
        assert vm.name == "echo_tool"
        assert vm.description == "回声工具"
        assert vm.status == "enabled"
        assert vm.permission == "user"
        assert vm.schema == {"input": {"type": "string"}}

    def test_to_view_model_disabled(self) -> None:
        adapter = ToolAdapter()
        tool_dict = {"name": "t", "enabled": False}
        vm = adapter.to_view_model(tool_dict)
        assert vm.status == "disabled"

    def test_to_view_model_admin_permission(self) -> None:
        adapter = ToolAdapter()
        tool_dict = {"name": "admin_tool", "permission": "admin", "enabled": True}
        vm = adapter.to_view_model(tool_dict)
        assert vm.permission == "admin"

    def test_to_list_view_model(self) -> None:
        adapter = ToolAdapter()
        tools = [
            {"name": "t1", "enabled": True},
            {"name": "t2", "enabled": False},
            {"name": "t3", "enabled": True},
        ]
        list_vm = adapter.to_list_view_model(tools)
        assert list_vm.total_count == 3
        assert list_vm.enabled_count == 2
        assert len(list_vm.get_enabled()) == 2

    def test_to_view_model_empty_schema(self) -> None:
        adapter = ToolAdapter()
        vm = adapter.to_view_model({"name": "t"})
        assert vm.schema == {}

    def test_to_view_model_none_schema(self) -> None:
        adapter = ToolAdapter()
        vm = adapter.to_view_model({"name": "t", "schema": None})
        assert vm.schema == {}