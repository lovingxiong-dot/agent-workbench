"""
Tests for AgentOrchestrator Phase-aware tool binding and AgentSession state isolation.

验证 T2 收尾核心点：
1. set_phase -> bind_tools_for_phase 链路按 Phase 过滤工具集合
2. _call_tool 在运行时也校验 Phase 白名单
3. AgentSession 的 phase_messages 滑动窗口与 Execute 阶段隔离
"""
import asyncio
import unittest
from unittest.mock import MagicMock

from agent_engine.orchestrator import AgentOrchestrator
from agent_engine.agent_session import AgentSession
from langchain_core.messages import HumanMessage, AIMessage


class TestOrchestratorPhaseToolBinding(unittest.TestCase):
    """验证 Phase 切换后工具绑定集合正确"""

    def _make_orchestrator(self, llm=None, **kwargs):
        return AgentOrchestrator(
            llm=llm or MagicMock(),
            tool_map={
                "read_file": MagicMock(),
                "write_file": MagicMock(),
                "run_command": MagicMock(),
                "web_fetch": MagicMock(),
            },
            tool_definitions=[
                {"type": "function", "function": {"name": "read_file"}},
                {"type": "function", "function": {"name": "write_file"}},
                {"type": "function", "function": {"name": "run_command"}},
                {"type": "function", "function": {"name": "web_fetch"}},
            ],
            system_prompt="test",
            **kwargs,
        )

    def _extract_bound_tool_names(self, bound_llm):
        """从 mock LLM 的 bind_tools 调用中提取被绑定的工具名列表"""
        # bind_tools 被调用时会返回一个新的 MagicMock；这里直接返回调用时传入的 defs
        call_args = bound_llm.bind_tools.call_args
        if call_args is None:
            return None
        defs = call_args[0][0]
        return {d["function"]["name"] for d in defs}

    def test_analyze_phase_binds_read_only_tools(self):
        llm = MagicMock()
        orch = self._make_orchestrator(llm=llm)
        orch.set_phase("analyze")
        bound = orch.bind_tools_for_phase("analyze")

        # analyze 默认只绑定读/查类工具
        names = self._extract_bound_tool_names(llm)
        self.assertIsNotNone(names)
        self.assertIn("read_file", names)
        self.assertIn("web_fetch", names)
        self.assertNotIn("write_file", names)
        self.assertNotIn("run_command", names)

    def test_verify_phase_binds_read_only_tools(self):
        llm = MagicMock()
        orch = self._make_orchestrator(llm=llm)
        orch.set_phase("verify")
        bound = orch.bind_tools_for_phase("verify")

        names = self._extract_bound_tool_names(llm)
        self.assertIsNotNone(names)
        self.assertIn("read_file", names)
        self.assertIn("web_fetch", names)
        self.assertNotIn("write_file", names)
        self.assertNotIn("run_command", names)

    def test_execute_phase_binds_all_tools(self):
        llm = MagicMock()
        orch = self._make_orchestrator(llm=llm)
        orch.set_phase("execute")
        bound = orch.bind_tools_for_phase("execute")

        names = self._extract_bound_tool_names(llm)
        self.assertIsNotNone(names)
        self.assertEqual(names, {"read_file", "write_file", "run_command", "web_fetch"})

    def test_set_phase_changes_current_phase(self):
        orch = self._make_orchestrator()
        self.assertEqual(orch._current_phase, "execute")
        orch.set_phase("analyze")
        self.assertEqual(orch._current_phase, "analyze")
        orch.set_phase("execute")
        self.assertEqual(orch._current_phase, "execute")
        orch.set_phase("verify")
        self.assertEqual(orch._current_phase, "verify")

    def test_custom_phase_allowlist_overrides_default(self):
        llm = MagicMock()
        orch = self._make_orchestrator(
            llm=llm,
            phase_tool_allowlists={
                "analyze": {"write_file"},
                "execute": None,
            },
        )
        orch.set_phase("analyze")
        orch.bind_tools_for_phase("analyze")

        names = self._extract_bound_tool_names(llm)
        self.assertEqual(names, {"write_file"})

    def test_call_tool_rejects_disallowed_tool_in_phase(self):
        """即使 LLM 意外请求，运行时也拒绝执行非白名单工具"""
        orch = self._make_orchestrator()
        orch.set_phase("analyze")
        result = asyncio.run(orch._call_tool("write_file", {"path": "/tmp/x", "content": "x"}))
        self.assertIn("not allowed in analyze phase", result)

    def test_call_tool_allows_allowed_tool_in_phase(self):
        orch = self._make_orchestrator()
        orch.set_phase("analyze")
        # read_file 在 analyze 白名单中，但没有真实实现，也没有 arun_map，会走到同步 run
        # 这里只验证白名单检查通过；同步执行会因 mock 无 run 方法报错，说明白名单已放行
        with self.assertRaises(Exception):
            asyncio.run(orch._call_tool("read_file", {"path": "/tmp/x"}))


class TestAgentSessionStateIsolation(unittest.TestCase):
    """验证 AgentSession 跨 Phase 状态隔离"""

    def _make_session(self):
        return AgentSession(
            llm=MagicMock(),
            tool_map={},
            tool_definitions=[],
            mode="craft",
            project_root="",
            system_prompt="test",
        )

    def test_execute_uses_independent_chat_history(self):
        session = self._make_session()
        # 模拟 Analyze 阶段积累了 phase_messages
        session.phase_messages.append(HumanMessage(content="prev user"))
        session.phase_messages.append(AIMessage(content="prev analyze result"))

        # run_execute 内部使用 chat_history=[]，不应携带 phase_messages
        captured = {}

        async def _fake_arun(*args, **kwargs):
            captured.update(kwargs)
            return "execute done"

        session.orchestrator.arun = _fake_arun

        asyncio.run(session.run_execute([], "do it", "ctx"))
        self.assertEqual(captured.get("chat_history"), [], "Execute 阶段必须独立聊天历史")

    def test_phase_messages_sliding_window(self):
        session = self._make_session()
        for i in range(20):
            session.phase_messages.append(HumanMessage(content=f"user {i}"))
            session.phase_messages.append(AIMessage(content=f"ai {i}"))

        session._trim_phase_messages()
        self.assertLessEqual(len(session.phase_messages), 12)
        # 保留最近的消息
        self.assertEqual(session.phase_messages[-1].content, "ai 19")
        self.assertEqual(session.phase_messages[-2].content, "user 19")

    def test_analyze_appends_to_phase_messages(self):
        session = self._make_session()
        captured = {"args": None, "kwargs": None}

        async def _fake_arun(*args, **kwargs):
            captured["args"] = args
            captured["kwargs"] = kwargs
            return '[{"description": "task 1"}]'

        session.orchestrator.arun = _fake_arun

        asyncio.run(session.run_analyze("hello", "ctx"))

        # run_analyze 通过位置参数传入 chat_history 副本
        chat_history = captured["args"][1] if len(captured["args"]) > 1 else None
        self.assertEqual(chat_history, [])

        # 调用后 phase_messages 追加了当前轮摘要
        self.assertEqual(len(session.phase_messages), 2)
        self.assertEqual(session.phase_messages[0].content, "hello")
        self.assertEqual(session.phase_messages[1].content, '[{"description": "task 1"}]')


if __name__ == "__main__":
    unittest.main()
