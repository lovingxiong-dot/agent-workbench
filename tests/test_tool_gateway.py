"""
ToolGateway 单元测试

验证工具网关的注册、查询、调用和 MCP 集成能力。
"""
import asyncio
import unittest
from unittest.mock import MagicMock

from agent_engine.tool_gateway import ToolGateway


async def _async_result(value):
    return value


class FakeAsyncTool:
    """模拟异步工具"""

    async def arun(self, args):
        return f"async: {args}"


class FakeSyncTool:
    """模拟同步工具"""

    def run(self, args):
        return f"sync: {args}"


class TestToolGateway(unittest.TestCase):
    def test_register_local_tools(self):
        gateway = ToolGateway()
        tool_map = {"sync_tool": FakeSyncTool()}
        async def _async_tool(args):
            return f"arun: {args}"

        arun_map = {"async_tool": _async_tool}
        defs = [
            {"type": "function", "function": {"name": "sync_tool"}},
            {"type": "function", "function": {"name": "async_tool"}},
        ]
        gateway.register_local_tools(tool_map, arun_map, defs)

        self.assertIn("sync_tool", gateway.get_tool_map())
        self.assertIn("async_tool", gateway.get_arun_map())
        self.assertEqual(len(gateway.get_definitions()), 2)
        self.assertTrue(gateway.has_tool("async_tool"))

    def test_call_tool_prefers_arun(self):
        gateway = ToolGateway()
        gateway.register_local_tools(
            {},
            {"tool_a": lambda args: _async_result("arun_result")},
            [{"type": "function", "function": {"name": "tool_a"}}],
        )
        result = asyncio.run(gateway.call_tool("tool_a", {}))
        self.assertEqual(result, "arun_result")

    def test_register_mcp_registry(self):
        gateway = ToolGateway()
        mcp_registry = MagicMock()
        mcp_registry.adapt_to_workbench_tools.return_value = {
            "mcp/foo": lambda args: _async_result("mcp_result")
        }
        mcp_registry.to_tool_definitions.return_value = [
            {"type": "function", "function": {"name": "mcp/foo"}}
        ]

        gateway.register_mcp_registry(mcp_registry)
        gateway.refresh_mcp_tools()

        self.assertTrue(gateway.has_tool("mcp/foo"))
        self.assertEqual(len(gateway.get_definitions()), 1)

    def test_call_mcp_tool(self):
        gateway = ToolGateway()
        mcp_registry = MagicMock()
        mcp_registry.adapt_to_workbench_tools.return_value = {
            "mcp/bar": lambda args: _async_result("bar_result")
        }
        mcp_registry.to_tool_definitions.return_value = []
        gateway.register_mcp_registry(mcp_registry)
        gateway.refresh_mcp_tools()

        result = asyncio.run(gateway.call_tool("mcp/bar", {}))
        self.assertEqual(result, "bar_result")
