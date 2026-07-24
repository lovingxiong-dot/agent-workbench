"""tests/tool/test_tool_service.py — WorkbenchToolServiceController 测试。

v6.10.0-alpha Tool Runtime Product Layer。

边界：
  - 测试 v6-agent 层聚合逻辑
  - 使用 Mock RuntimeToolBackend
  - 不修改 Runtime ToolModule
"""
from __future__ import annotations

from typing import Any, Dict, List

import pytest

from agent_workbench.presentation.services.tool_service import (
    RuntimeToolBackend,
    ToolConfigUpdate,
    WorkbenchToolServiceController,
)


class MockRuntimeToolBackend:
    """Mock Runtime Tool Backend。"""

    def __init__(self, tools: List[Dict[str, Any]] | None = None) -> None:
        self._tools = {t["name"]: dict(t) for t in (tools or [])}

    def list_tool_dicts(self) -> List[Dict[str, Any]]:
        return [dict(t) for t in self._tools.values()]

    def set_tool_enabled(self, tool_id: str, enabled: bool) -> bool:
        if tool_id not in self._tools:
            return False
        self._tools[tool_id]["enabled"] = enabled
        return True

    def set_tool_config(self, tool_id: str, config: Dict[str, Any]) -> bool:
        if tool_id not in self._tools:
            return False
        self._tools[tool_id].update(config)
        return True

    def get(self, tool_id: str) -> Dict[str, Any]:
        return self._tools.get(tool_id, {})


def make_controller(tools: List[Dict[str, Any]] | None = None) -> WorkbenchToolServiceController:
    """工厂：构造 ToolServiceController。"""
    backend = MockRuntimeToolBackend(tools)
    return WorkbenchToolServiceController(backend)


class TestToolServiceList:
    """Tool list 操作测试。"""

    def test_empty_list(self) -> None:
        controller = make_controller()
        vm = controller.list_view_model()
        assert vm.total_count == 0
        assert vm.enabled_count == 0

    def test_list_with_tools(self) -> None:
        controller = make_controller([
            {"name": "echo", "description": "回声", "enabled": True, "permission": "user"},
            {"name": "search", "description": "搜索", "enabled": False, "permission": "admin"},
        ])
        vm = controller.list_view_model()
        assert vm.total_count == 2
        assert vm.enabled_count == 1

    def test_get_view_model_existing(self) -> None:
        controller = make_controller([
            {"name": "echo", "enabled": True},
        ])
        vm = controller.get_view_model("echo")
        assert vm is not None
        assert vm.tool_id == "echo"

    def test_get_view_model_missing(self) -> None:
        controller = make_controller()
        assert controller.get_view_model("nonexistent") is None


class TestToolServiceLifecycle:
    """Tool enable/disable/update 操作测试。"""

    def test_enable_tool(self) -> None:
        controller = make_controller([
            {"name": "echo", "enabled": False},
        ])
        result = controller.enable_tool("echo")
        assert result.success is True
        assert controller.get_view_model("echo").status == "enabled"

    def test_disable_tool(self) -> None:
        controller = make_controller([
            {"name": "echo", "enabled": True},
        ])
        result = controller.disable_tool("echo")
        assert result.success is True
        assert controller.get_view_model("echo").status == "disabled"

    def test_enable_missing_tool(self) -> None:
        controller = make_controller()
        result = controller.enable_tool("nonexistent")
        assert result.success is False

    def test_disable_missing_tool(self) -> None:
        controller = make_controller()
        result = controller.disable_tool("nonexistent")
        assert result.success is False

    def test_update_tool_config(self) -> None:
        controller = make_controller([
            {"name": "echo", "permission": "user", "enabled": True},
        ])
        result = controller.update_tool_config("echo", {"permission": "admin"})
        assert result.success is True
        assert controller.get_view_model("echo").permission == "admin"

    def test_update_missing_tool(self) -> None:
        controller = make_controller()
        result = controller.update_tool_config("nonexistent", {"permission": "admin"})
        assert result.success is False


class TestToolModuleBackend:
    """ToolModuleBackend 测试（适配 Runtime ToolModule）。"""

    def test_list_tool_dicts(self) -> None:
        class MockToolModule:
            def list_tools(self):
                return [{"name": "echo", "enabled": True}]

        from agent_workbench.presentation.services.tool_module_backend import (
            ToolModuleBackend,
        )
        backend = ToolModuleBackend(MockToolModule())
        assert backend.list_tool_dicts() == [{"name": "echo", "enabled": True}]

    def test_set_tool_enabled_via_registry(self) -> None:
        class MockTool:
            def __init__(self):
                self.enabled = True

        class MockRegistry:
            def __init__(self):
                self._tools = {"echo": MockTool()}

            def get(self, name):
                return self._tools.get(name)

            def set_enabled(self, name, enabled):
                if name not in self._tools:
                    return False
                self._tools[name].enabled = enabled
                return True

        class MockToolModule:
            @property
            def registry(self):
                return MockRegistry()

        from agent_workbench.presentation.services.tool_module_backend import (
            ToolModuleBackend,
        )
        backend = ToolModuleBackend(MockToolModule())
        ok = backend.set_tool_enabled("echo", False)
        assert ok is True
        ok = backend.set_tool_enabled("nonexistent", False)
        assert ok is False

    def test_set_tool_config_updates_fields(self) -> None:
        class MockTool:
            def __init__(self):
                self.permission = "user"
                self.enabled = True
                self.description = "old"

        shared_registry = type("R", (), {
            "_tools": {"echo": MockTool()},
            "get": lambda self, name: self._tools.get(name),
        })()

        class MockToolModule:
            @property
            def registry(self):
                return shared_registry

        from agent_workbench.presentation.services.tool_module_backend import (
            ToolModuleBackend,
        )
        backend = ToolModuleBackend(MockToolModule())
        ok = backend.set_tool_config(
            "echo",
            {"permission": "admin", "description": "new"},
        )
        assert ok is True
        tool = shared_registry.get("echo")
        assert tool.permission == "admin"
        assert tool.description == "new"