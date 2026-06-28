"""
AgentSession Session-as-Room 生命周期测试

验证每个 Session 独立持有 chat_history，enter/leave 边界清晰。
"""
import unittest
from unittest.mock import MagicMock

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from agent_engine.agent_session import AgentSession


class TestAgentSessionRoom(unittest.TestCase):
    """测试 Session-as-Room 接口"""

    def _make_session(self):
        return AgentSession(
            llm=MagicMock(),
            tool_map={},
            tool_definitions=[],
            mode="ask",
            project_root="",
            system_prompt="test",
        )

    def test_enter_loads_chat_history(self):
        """enter() 应按角色重建 chat_history"""
        session = self._make_session()
        messages = [
            {"role": "user", "content": "你好"},
            {"role": "ai", "content": "你好，有什么可以帮你的？"},
            {"role": "system", "content": "系统提示"},
        ]
        session.enter("session-A", messages)

        self.assertEqual(session.current_session_id, "session-A")
        history = session.get_chat_history()
        self.assertEqual(len(history), 3)
        self.assertIsInstance(history[0], HumanMessage)
        self.assertEqual(history[0].content, "你好")
        self.assertIsInstance(history[1], AIMessage)
        self.assertEqual(history[1].content, "你好，有什么可以帮你的？")
        self.assertIsInstance(history[2], SystemMessage)
        self.assertEqual(history[2].content, "系统提示")

    def test_enter_is_idempotent(self):
        """多次进入同一房间不会重复累积消息"""
        session = self._make_session()
        messages = [{"role": "user", "content": "问题"}]
        session.enter("session-A", messages)
        session.enter("session-A", messages)

        self.assertEqual(len(session.get_chat_history()), 1)

    def test_leave_clears_room_state(self):
        """leave() 应清空当前房间所有状态"""
        session = self._make_session()
        session.enter("session-A", [{"role": "user", "content": "问题"}])
        session.add_user_message("追加")
        session.add_assistant_message("回答")
        session.leave()

        self.assertEqual(session.current_session_id, "")
        self.assertEqual(len(session.get_chat_history()), 0)
        self.assertEqual(len(session.phase_messages), 0)

    def test_add_messages_append_to_history(self):
        """add_user_message / add_assistant_message 追加到当前房间"""
        session = self._make_session()
        session.enter("session-A", [])
        session.add_user_message("用户输入")
        session.add_assistant_message("AI 回复")

        history = session.get_chat_history()
        self.assertEqual(len(history), 2)
        self.assertIsInstance(history[0], HumanMessage)
        self.assertIsInstance(history[1], AIMessage)

    def test_different_sessions_do_not_share_history(self):
        """不同房间的 chat_history 互相独立"""
        session = self._make_session()
        session.enter("session-A", [{"role": "user", "content": "A 的问题"}])
        session.leave()
        session.enter("session-B", [{"role": "user", "content": "B 的问题"}])

        history = session.get_chat_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].content, "B 的问题")


if __name__ == "__main__":
    unittest.main()
