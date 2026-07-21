"""
MCP Service — 模型上下文协议（Model Context Protocol）接入基座

当前版本为接口预留与轻量实现：
- 支持 MCP Server 配置、连接、工具发现
- 提供将 MCP tool 注册到工作台 TOOL_MAP / ARUN_MAP 的适配器
- 为后续逐步接入外部 MCP Server 预留扩展点

设计原则：
- 不依赖 PySide6，可在后台任务、测试代码中独立使用
- 所有 I/O 均为 async，避免阻塞事件循环
- transport 层可插拔（stdio / sse / websocket），当前仅预留 stdio 骨架
"""
import asyncio
import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class MCPServerConfig:
    """MCP Server 配置"""
    name: str
    transport: str  # "stdio" | "sse" | "websocket"
    command: Optional[str] = None  # for stdio
    args: List[str] = field(default_factory=list)
    url: Optional[str] = None  # for sse / websocket
    env: Dict[str, str] = field(default_factory=dict)


@dataclass
class MCPToolDefinition:
    """MCP Tool 元数据"""
    name: str
    description: str
    parameters: Dict[str, Any]
    server_name: str


class MCPTransport(ABC):
    """MCP 传输层抽象"""

    @abstractmethod
    async def connect(self, config: MCPServerConfig) -> bool:
        ...

    @abstractmethod
    async def call(self, method: str, params: Optional[Dict] = None) -> Any:
        ...

    @abstractmethod
    async def close(self) -> None:
        ...


class MCPStdioTransport(MCPTransport):
    """通过子进程 stdio 与 MCP Server 通信"""

    def __init__(self):
        self._process: Optional[asyncio.subprocess.Process] = None

    async def connect(self, config: MCPServerConfig) -> bool:
        if not config.command:
            return False
        try:
            env = os.environ.copy()
            env.update(config.env)
            self._process = await asyncio.create_subprocess_exec(
                config.command,
                *config.args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            # 简单等待进程启动
            await asyncio.sleep(0.05)
            return self._process.returncode is None
        except Exception:
            return False

    async def call(self, method: str, params: Optional[Dict] = None) -> Any:
        if not self._process:
            raise RuntimeError("MCP transport not connected")
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": 1,
        }
        data = json.dumps(request, ensure_ascii=False).encode("utf-8") + b"\n"
        self._process.stdin.write(data)
        await self._process.stdin.drain()
        line = await self._process.stdout.readline()
        if not line:
            raise RuntimeError("MCP server closed stdout")
        return json.loads(line.decode("utf-8"))

    async def close(self) -> None:
        if self._process:
            try:
                self._process.terminate()
                await asyncio.wait_for(self._process.wait(), timeout=2.0)
            except Exception:
                try:
                    self._process.kill()
                except Exception:
                    pass


class MCPClient:
    """单个 MCP Server 的客户端"""

    def __init__(self, config: MCPServerConfig):
        self.config = config
        self._transport: Optional[MCPTransport] = None

    @property
    def is_connected(self) -> bool:
        return self._transport is not None

    async def connect(self) -> bool:
        if self.config.transport == "stdio":
            self._transport = MCPStdioTransport()
        else:
            # TODO: SSE / WebSocket transport 待实现
            return False
        ok = await self._transport.connect(self.config)
        if not ok:
            self._transport = None
        return ok

    async def list_tools(self) -> List[MCPToolDefinition]:
        result = await self._transport.call("tools/list")
        tools = []
        for t in result.get("tools", []):
            tools.append(
                MCPToolDefinition(
                    name=f"{self.config.name}/{t['name']}",
                    description=t.get("description", ""),
                    parameters=t.get("parameters", {}),
                    server_name=self.config.name,
                )
            )
        return tools

    async def call_tool(self, tool_name: str, args: Dict[str, Any]) -> str:
        result = await self._transport.call(
            "tools/call", {"name": tool_name, "arguments": args}
        )
        return json.dumps(result, ensure_ascii=False)

    async def close(self):
        if self._transport:
            await self._transport.close()
            self._transport = None


class MCPRegistry:
    """管理多个 MCP Server 连接，并提供工具适配"""

    def __init__(self):
        self._clients: Dict[str, MCPClient] = {}
        self._tools: Dict[str, MCPToolDefinition] = {}

    async def add_server(self, config: MCPServerConfig) -> bool:
        """添加并连接一个 MCP Server"""
        client = MCPClient(config)
        if not await client.connect():
            return False
        self._clients[config.name] = client
        try:
            tools = await client.list_tools()
            for tool in tools:
                self._tools[tool.name] = tool
        except Exception:
            # 连接成功但工具列表获取失败，保持连接可用
            pass
        return True

    def list_tools(self) -> List[MCPToolDefinition]:
        return list(self._tools.values())

    async def call_tool(self, full_name: str, args: Dict[str, Any]) -> str:
        client_name, _, tool_name = full_name.partition("/")
        client = self._clients.get(client_name)
        if not client:
            raise RuntimeError(f"MCP server '{client_name}' not connected")
        return await client.call_tool(tool_name, args)

    def adapt_to_workbench_tools(self) -> Dict[str, Callable]:
        """把 MCP tools 转换为工作台可识别的 async callable（arun 形式）"""
        arun_map: Dict[str, Callable] = {}
        for name in self._tools:
            async def _arun(args, _name=name):
                return await self.call_tool(_name, args)

            arun_map[name] = _arun
        return arun_map

    def to_tool_definitions(self) -> List[Dict[str, Any]]:
        """生成 LangChain bind_tools 可用的 tool definitions"""
        defs = []
        for tool in self._tools.values():
            defs.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters,
                    },
                }
            )
        return defs

    async def close_all(self):
        for client in self._clients.values():
            await client.close()
        self._clients.clear()
        self._tools.clear()
