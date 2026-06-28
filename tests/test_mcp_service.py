"""
MCP Service 单元测试

验证 MCPRegistry 的工具适配与定义生成。
当前不测试真实子进程通信，仅验证接口契约。
"""
import unittest
from unittest.mock import AsyncMock, MagicMock

from services.mcp_service import MCPRegistry, MCPToolDefinition


class TestMCPRegistry(unittest.TestCase):
    def test_list_tools_initially_empty(self):
        registry = MCPRegistry()
        self.assertEqual(registry.list_tools(), [])

    def test_adapt_to_workbench_tools(self):
        registry = MCPRegistry()
        registry._tools = {
            "server/foo": MCPToolDefinition(
                name="server/foo",
                description="foo tool",
                parameters={"type": "object"},
                server_name="server",
            )
        }
        arun_map = registry.adapt_to_workbench_tools()
        self.assertIn("server/foo", arun_map)

    def test_to_tool_definitions(self):
        registry = MCPRegistry()
        registry._tools = {
            "server/foo": MCPToolDefinition(
                name="server/foo",
                description="foo tool",
                parameters={"type": "object"},
                server_name="server",
            )
        }
        defs = registry.to_tool_definitions()
        self.assertEqual(len(defs), 1)
        self.assertEqual(defs[0]["function"]["name"], "server/foo")
