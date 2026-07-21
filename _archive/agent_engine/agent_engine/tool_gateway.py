"""
ToolGateway — 外部工具统一接入网关

职责：
- 统合本地 TOOL_MAP/ARUN_MAP、MCP tools、MT5 signals 等外部能力
- 为 Orchestrator 提供统一的工具发现与调用接口
- 支持动态热插拔外部工具，便于后期接入 MCP Server、MT5 信号源等

设计原则：
- 不依赖 PySide6 / UI，只通过标准 Python callable 暴露接口
- 本地工具与外部工具解耦，外部工具未连接时不影响本地工具
- 所有外部调用优先走 async 路径
"""
from typing import Any, Callable, Dict, List, Optional


class ToolGateway:
    """工具统一接入网关"""

    def __init__(self):
        self._tool_map: Dict[str, Callable] = {}
        self._arun_map: Dict[str, Callable] = {}
        self._definitions: List[Dict[str, Any]] = []
        self._mcp_registry: Optional[Any] = None

    # ═══════════════════════════════════════════════════════
    # 本地工具注册
    # ═══════════════════════════════════════════════════════
    def register_local_tools(
        self,
        tool_map: Dict[str, Callable],
        arun_map: Dict[str, Callable],
        definitions: List[Dict[str, Any]],
    ):
        """注册工作台内置工具"""
        self._tool_map.update(tool_map)
        self._arun_map.update(arun_map)
        self._definitions.extend(definitions)

    # ═══════════════════════════════════════════════════════
    # MCP 工具注册
    # ═══════════════════════════════════════════════════════
    def register_mcp_registry(self, mcp_registry: Any):
        """注册 MCP Registry；工具在需要时动态转换"""
        self._mcp_registry = mcp_registry

    def refresh_mcp_tools(self) -> List[Dict[str, Any]]:
        """刷新 MCP tools 到本地缓存；返回新增/更新的 tool definitions"""
        if not self._mcp_registry:
            return []
        arun_map = self._mcp_registry.adapt_to_workbench_tools()
        self._arun_map.update(arun_map)
        defs = self._mcp_registry.to_tool_definitions()
        # 去重：同名工具以最新为准
        existing = {d["function"]["name"]: d for d in self._definitions}
        for d in defs:
            existing[d["function"]["name"]] = d
        self._definitions = list(existing.values())
        return defs

    # ═══════════════════════════════════════════════════════
    # 统一查询接口
    # ═══════════════════════════════════════════════════════
    def get_tool_map(self) -> Dict[str, Callable]:
        """获取同步工具映射（主要用于 bind_tools 兼容）"""
        return dict(self._tool_map)

    def get_arun_map(self) -> Dict[str, Callable]:
        """获取 async 工具映射（供 Orchestrator._call_tool 优先调用）"""
        return dict(self._arun_map)

    def get_definitions(self) -> List[Dict[str, Any]]:
        """获取所有工具定义（本地 + MCP）"""
        return list(self._definitions)

    def has_tool(self, name: str) -> bool:
        return name in self._tool_map or name in self._arun_map

    # ═══════════════════════════════════════════════════════
    # 统一调用接口
    # ═══════════════════════════════════════════════════════
    async def call_tool(self, name: str, args: Any) -> str:
        """统一调用工具：优先 async，其次同步 run"""
        import asyncio
        import inspect

        if name in self._arun_map:
            return await self._arun_map[name](args)
        if name in self._tool_map:
            tool = self._tool_map[name]
            if inspect.iscoroutinefunction(tool):
                return await tool(args)
            # 同步工具：在默认 executor 中运行，避免阻塞事件循环
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, tool.run, args)
        raise RuntimeError(f"Tool '{name}' not registered")
