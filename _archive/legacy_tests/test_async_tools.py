"""
Async 工具冒烟测试
验证 T1 改造后：
1. ARUN_MAP 包含所有 I/O 工具
2. arun 可在事件循环中正常执行
3. 同步入口仍可在无事件循环线程中工作
4. Orchestrator._call_tool 优先命中 ARUN_MAP
"""
import asyncio
import os
import tempfile
import threading
import unittest
from unittest.mock import MagicMock

from tools import TOOL_MAP, ARUN_MAP
from tools.system import run_command, read_file, write_file, list_dir
from tools.external_apis import set_cpu_executor as set_external_cpu
from tools.quant import set_cpu_executor as set_quant_cpu
from agent_engine.orchestrator import AgentOrchestrator


class TestAsyncToolDiscovery(unittest.TestCase):
    """确认所有 I/O 工具都在 ARUN_MAP 中注册"""

    def test_io_tools_in_arun_map(self):
        io_tool_names = [
            "run_command", "read_file", "write_file", "list_dir", "web_fetch",
            "clipboard_read", "clipboard_write", "list_processes", "kill_process",
            "fetch_stock_data", "fetch_financial_news", "fetch_macro_data",
            "run_python", "run_powershell", "run_bash",
        ]
        for name in io_tool_names:
            self.assertIn(name, ARUN_MAP, f"{name} 未在 ARUN_MAP 中注册")
            self.assertTrue(callable(ARUN_MAP[name]), f"{name} 的 arun 不可调用")
            self.assertIn(name, TOOL_MAP, f"{name} 未在 TOOL_MAP 中注册")

    def test_sync_tools_not_in_arun_map(self):
        self.assertNotIn("send_notification", ARUN_MAP)
        self.assertNotIn("run_as_admin", ARUN_MAP)
        self.assertNotIn("run_backtest", ARUN_MAP)
        self.assertNotIn("mt5_get_price", ARUN_MAP)
        self.assertNotIn("mt5_place_order", ARUN_MAP)


class TestAsyncToolExecution(unittest.TestCase):
    """在独立事件循环中验证 arun 可执行"""

    def _run_async(self, coro):
        return asyncio.run(coro)

    def test_arun_read_write_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_path = os.path.join(tmpdir, "async_test.txt")
            content = "hello async tools"

            # write
            result = self._run_async(ARUN_MAP["write_file"]({"path": test_path, "content": content}))
            self.assertIn("已写入", result)

            # read
            result = self._run_async(ARUN_MAP["read_file"]({"path": test_path}))
            self.assertIn(content, result)

    def test_arun_list_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            open(os.path.join(tmpdir, "a.txt"), "w").close()
            result = self._run_async(ARUN_MAP["list_dir"]({"path": tmpdir}))
            self.assertIn("a.txt", result)

    def test_arun_run_python(self):
        result = self._run_async(ARUN_MAP["run_python"]({"code": "print(1+1)"}))
        self.assertIn("2", result)

    def test_arun_run_command_echo(self):
        result = self._run_async(ARUN_MAP["run_command"]({"command": "echo hello_async"}))
        self.assertIn("hello_async", result)


class TestSyncEntryPoint(unittest.TestCase):
    """验证同步入口可在无事件循环线程中工作"""

    def test_run_command_in_thread(self):
        results = {}

        def target():
            # LangChain @tool 装饰后生成 StructuredTool，需用 .invoke(dict) 调用
            results["output"] = run_command.invoke({"command": "echo sync_thread_test"})

        t = threading.Thread(target=target)
        t.start()
        t.join()
        self.assertIn("sync_thread_test", results.get("output", ""))


class TestOrchestratorCallTool(unittest.TestCase):
    """验证 Orchestrator._call_tool 调用链"""

    def test_call_tool_prefers_arun_map(self):
        fake_llm = MagicMock()
        fake_tool = MagicMock()
        arun_called = {"args": None}

        async def fake_arun(args):
            arun_called["args"] = args
            return "arun_result"

        orch = AgentOrchestrator(
            llm=fake_llm,
            tool_map={"fake_tool": fake_tool},
            tool_definitions=[],
            system_prompt="test",
            cpu_executor=MagicMock(),
            arun_map={"fake_tool": fake_arun},
        )

        result = asyncio.run(orch._call_tool("fake_tool", {"x": 1}))
        self.assertEqual(result, "arun_result")
        self.assertEqual(arun_called["args"], {"x": 1})
        fake_tool.run.assert_not_called()

    def test_call_tool_falls_back_to_run_in_executor(self):
        fake_llm = MagicMock()
        fake_tool = MagicMock()
        fake_tool.run.return_value = "sync_result"

        # 使用真实 ThreadPoolExecutor 验证 run_in_executor 路径
        from concurrent.futures import ThreadPoolExecutor
        executor = ThreadPoolExecutor(max_workers=1)

        orch = AgentOrchestrator(
            llm=fake_llm,
            tool_map={"fake_tool": fake_tool},
            tool_definitions=[],
            system_prompt="test",
            cpu_executor=executor,
            arun_map={},
        )

        result = asyncio.run(orch._call_tool("fake_tool", {"x": 1}))
        self.assertEqual(result, "sync_result")
        executor.shutdown(wait=False)


class TestCpuExecutorInjection(unittest.TestCase):
    """验证 external_apis / quant 的 set_cpu_executor 可被调用"""

    def test_set_cpu_executor_external(self):
        mock_ex = MagicMock()
        set_external_cpu(mock_ex)
        # 仅验证不抛错

    def test_set_cpu_executor_quant(self):
        mock_ex = MagicMock()
        set_quant_cpu(mock_ex)
        # 仅验证不抛错


if __name__ == "__main__":
    unittest.main()
