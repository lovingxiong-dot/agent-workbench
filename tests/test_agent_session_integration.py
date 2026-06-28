"""
AgentSession + Orchestrator 协作集成测试

验证 Analyze → Execute → Verify 全链路在状态、Phase、上下文隔离上的正确性。
使用 Mocked Orchestrator.arun，不依赖真实 LLM 和 UI。
"""
import asyncio
import unittest
from unittest.mock import MagicMock

from agent_engine.agent_session import AgentSession
from agent_engine.orchestrator import AgentOrchestrator
from agent_engine.phase_manager import TaskItem
from langchain_core.messages import HumanMessage, AIMessage


class TestAgentSessionPhaseFlow(unittest.TestCase):
    """模拟 Craft 模式 Analyze → Execute → Verify 的完整状态流转"""

    def _make_session(self):
        return AgentSession(
            llm=MagicMock(),
            tool_map={},
            tool_definitions=[],
            mode="craft",
            project_root="",
            system_prompt="test",
        )

    def test_full_phase_sequence(self):
        session = self._make_session()
        calls = []

        async def fake_arun(user_text, chat_history=None, callbacks=None, **kwargs):
            calls.append({
                "phase": session.orchestrator._current_phase,
                "user_text": user_text,
                "chat_history_len": len(chat_history) if chat_history else 0,
            })
            phase = session.orchestrator._current_phase
            if phase == "analyze":
                return '[{"description": "列出当前目录"}]'
            elif phase == "execute":
                return "已执行：列出目录，结果包含 file1.txt"
            elif phase == "verify":
                return "验证通过"
            return ""

        session.orchestrator.arun = fake_arun

        # ── Analyze ─────────────────────────────────────────────
        tasks, full_text = asyncio.run(session.run_analyze("帮我列目录", "workspace ctx"))

        self.assertEqual(session.orchestrator._current_phase, "analyze")
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].description, "列出当前目录")
        # Analyze 后 phase_messages 应追加当前轮摘要（Human + AI）
        self.assertEqual(len(session.phase_messages), 2)
        self.assertEqual(session.phase_messages[0].content, "帮我列目录")
        self.assertEqual(session.phase_messages[1].content, '[{"description": "列出当前目录"}]')

        # ── Execute ─────────────────────────────────────────────
        result = asyncio.run(session.run_execute(tasks, "帮我列目录", "execute ctx"))

        self.assertEqual(session.orchestrator._current_phase, "execute")
        # Execute 必须传入空 chat_history，不携带 Analyze 阶段上下文
        self.assertEqual(calls[-1]["chat_history_len"], 0)
        self.assertIn("file1.txt", result)
        # Execute 不应污染 phase_messages
        self.assertEqual(len(session.phase_messages), 2)

        # ── Verify ──────────────────────────────────────────────
        verify_result = asyncio.run(session.run_verify(
            [{"task": "列出当前目录", "result": "file1.txt"}],
            "本地验证通过",
            "verify ctx"
        ))

        self.assertEqual(session.orchestrator._current_phase, "verify")
        self.assertEqual(verify_result, "验证通过")
        # Verify 可以读取 Analyze 阶段累积的 phase_messages
        self.assertGreaterEqual(len(session.phase_messages), 2)

        # ── 阶段顺序与 workspace_context 隔离断言 ─────────────────
        self.assertEqual(calls[0]["phase"], "analyze")
        self.assertEqual(calls[1]["phase"], "execute")
        self.assertEqual(calls[2]["phase"], "verify")
        # set_phase 应把对应 context 写入 orchestrator.workspace_context
        self.assertEqual(session.orchestrator.workspace_context, "verify ctx")

    def test_phase_messages_sliding_window_across_turns(self):
        """多轮 Analyze 后，phase_messages 应被截断，Verify 不会拿到超长历史"""
        session = self._make_session()

        async def fake_arun(user_text, chat_history=None, callbacks=None, **kwargs):
            return '[{"description": "task"}]'

        session.orchestrator.arun = fake_arun

        for i in range(10):
            asyncio.run(session.run_analyze(f"request {i}", "ctx"))

        # 每轮追加 2 条，滑动窗口上限 12 条
        self.assertEqual(len(session.phase_messages), 12)
        self.assertEqual(session.phase_messages[-1].content, '[{"description": "task"}]')
        self.assertEqual(session.phase_messages[-2].content, "request 9")


class TestOrchestratorPhaseToolRestrictionInSequence(unittest.TestCase):
    """验证 Phase 切换后，同一工具在不同 Phase 下的执行权限变化"""

    def _make_orchestrator(self, phase="execute"):
        tool = MagicMock()
        tool.run.return_value = "write ok"

        orch = AgentOrchestrator(
            llm=MagicMock(),
            tool_map={"write_file": tool},
            tool_definitions=[{"type": "function", "function": {"name": "write_file"}}],
            system_prompt="test",
            cpu_executor=MagicMock(),
        )
        orch.set_phase(phase)
        return orch, tool

    def test_write_file_blocked_in_analyze_then_allowed_in_execute(self):
        orch, tool = self._make_orchestrator("analyze")

        # Analyze 阶段 write_file 被拦截
        result = asyncio.run(orch._call_tool("write_file", {"path": "/tmp/x", "content": "x"}))
        self.assertIn("not allowed in analyze phase", result)
        tool.run.assert_not_called()

        # 切换到 Execute 阶段并重新绑定工具，write_file 应被包含
        orch.set_phase("execute")
        orch.bind_tools_for_phase("execute")
        bound_defs = orch.llm.bind_tools.call_args[0][0]
        bound_names = {d["function"]["name"] for d in bound_defs}
        self.assertIn("write_file", bound_names)


if __name__ == "__main__":
    unittest.main()
